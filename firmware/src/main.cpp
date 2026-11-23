#include <Arduino.h>
#include <SPI.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include <Preferences.h>
#include <driver/gpio.h>
#include <esp_timer.h>
#include "esp32-hal-rmt.h"
#include "osc.h"
#include "calibration.h"

SET_LOOP_TASK_STACK_SIZE(16384);
using namespace tpp;
constexpr int RUN=D1, MISO_ADC=D2,ARM_PIN=D3,LATCH=D4,DIR9=D5,CS=D6,FAULT=D7,SCLK_PIN=D8,Q_ARM=D9,MOSI_PIN=D10;
WiFiUDP udp;Preferences nv;State control;tpp::Server server;
char ap[32],pass[20];int unitID=1;uint32_t headID=1;bool timerReady=false,udpReady=false;
uint64_t usNow(){return uint64_t(esp_timer_get_time());}
bool healthy(){return digitalRead(FAULT)&&digitalRead(Q_ARM);}
bool runHigh(){return gpio_get_level(static_cast<gpio_num_t>(RUN));}
void latch(Pins p){
    uint32_t w=shiftWord(p);digitalWrite(DIR9,(p.hi>>8)&1);digitalWrite(LATCH,LOW);
    SPI.transfer(w>>16);SPI.transfer(w>>8);SPI.transfer(w);
    digitalWrite(LATCH,HIGH);digitalWrite(LATCH,LOW);
}
void newEpoch(){
    server.reset(unitID,int(esp_random()));
    if(udpReady){udp.stop();udpReady=udp.begin(5054)!=0;}
}
void disarm(){latch({0,0});control.armed=false;newEpoch();}
bool armHardware();
struct Hardware {
    float blankA=0,rail=0;uint64_t lastHeat=0;
    uint64_t now(){return usNow();}
    bool quiet(){return now()>=lastHeat+2000000;}
    bool prepareCal(){return armHardware();}
    bool changeWires(int n){
        latch({0,0});
        if(nv.isKey("cal")&&(!nv.remove("cal")||nv.isKey("cal")))return false;
        return nv.putUInt("wires",n)==4&&nv.getUInt("wires",0)==unsigned(n);
    }
    float voltage(){return rail;}
    void note(const State&,unsigned,unsigned,int,const Reading&,const Power&){}
    void waitUntil(uint64_t when){
        while(now()+1500<when)delay(1);
        while(now()<when)delayMicroseconds(2);
    }
    uint16_t frame(int ch){
        digitalWrite(CS,LOW);
        uint16_t result=SPI.transfer16(0x1800|(ch<<7));
        digitalWrite(CS,HIGH);delayMicroseconds(3);return result;
    }
    bool readIdle(){
        frame(11);frame(10);auto i=frame(11),v=frame(10);
        if((i>>12)!=11||(v>>12)!=10||(i&4095)>65||(v&4095)==4095){rail=0;return false;}
        rail=(v&4095)*(7.5f/4096);blankA=(i&4095)*(12.5f/4096);
        return rail>=5.7f&&rail<=6.3f;
    }
    Reading fire(Pins pins,unsigned us,int site,uint64_t deadline=UINT64_MAX,uint64_t startBy=UINT64_MAX,unsigned minimum=MinSlot){
        Reading r;if(!timerReady||!healthy()){r.hwfault=true;return r;}
        // CS is high when shifting. Each ADC transaction also shifts the unlatched
        // 595 registers; always replace all 24 bits before the next RCLK edge.
        latch(pins);delayMicroseconds(5);
        uint64_t command=now();
        if(command>=startBy){r.expired=true;r.stale=true;latch({0,0});return r;}
        if(command+us+20>deadline){
            if(site>=0||command+minimum+20>deadline){r.expired=true;latch({0,0});return r;}
            us=unsigned(deadline-command-20);
        }
        r.onUs=us;
        rmt_data_t symbol{};symbol.level0=1;symbol.duration0=us;symbol.level1=0;symbol.duration1=5;
        if(!rmtWriteAsync(RUN,&symbol,1))return r;
        r.started=true;lastHeat=command;
        uint64_t first=0;do{if(runHigh()){first=now();break;}}while(now()-command<20);
        // Very short edges may finish before software observes RUN. Their RMT duration
        // is still finite; full-duration accounting is conservative for a missed edge.
        bool sample=site>=0||us>=64;
        bool ok=!sample;
        if(first&&sample){
            delayMicroseconds(8);int j=site<0?1:edge(site);
            int channels[]={11,j,j-1,11};uint16_t codes[4]{};unsigned times[4]{};bool plateau=runHigh();
            for(int k=0;k<(site<0?3:6);k++){
                unsigned ts=unsigned(now()-first);
                auto res=frame(site<0?11:channels[std::min(k,3)]);
                if(k>=2){int idx=k-2;codes[idx]=res&4095;times[idx]=ts;plateau&=(res>>12)==(site<0?11:channels[idx])&&codes[idx]<4095;}
            }
            ok=plateau&&runHigh()&&healthy();
            if(ok){
                float current=codes[0]*(12.5f/4096)-blankA;
                if(site>=0){
                    float vh=codes[1]*(7.5f/4096),vl=codes[2]*(7.5f/4096);
                    float i2=codes[3]*(12.5f/4096)-blankA;
                    ok=std::abs(i2-current)<.05f;current=.5f*(current+i2)-(10-j)*vh/30000.f;
                    r.v=vh-vl;r.sampleUs=(times[1]+times[2])/2;
                }
                r.i=current;ok=ok&&std::isfinite(current)&&current>.10f;
            }
        }
        while(!rmtTransmitCompleted(RUN)&&now()-command<us+300){}
        bool done=rmtTransmitCompleted(RUN)&&!runHigh();r.hwfault=!healthy();
        // A time overrun stops all subsequent slots. Blank without reversing IN9 live.
        if(!done){latch({pins.hi,0});delayMicroseconds(5);}
        latch({0,0});
        r.end=(first?first:command)+us;lastHeat=r.end;r.ok=ok&&done&&!r.hwfault;
        return r;
    }
} hw;

struct NvsCalibration {
    bool read(Record& r){return nv.getBytesLength("cal")==sizeof(r)&&nv.getBytes("cal",&r,sizeof(r))==sizeof(r);}
    bool write(const Record& r){return nv.putBytes("cal",&r,sizeof(r))==sizeof(r);}
    bool erase(){return !nv.isKey("cal")||(nv.remove("cal")&&!nv.isKey("cal"));}
} storage;
bool armHardware(){
    if(!timerReady||!digitalRead(FAULT)||!hw.readIdle())return false;
    digitalWrite(ARM_PIN,HIGH);delayMicroseconds(3);digitalWrite(ARM_PIN,LOW);return healthy();
}
bool calibrate(float ambient,float r20){
    disarm();return enroll(control,hw,storage,ESP.getEfuseMac(),headID,ambient,r20);
}
void info(){
    Serial.printf("TPP-R2J %s array_label=%lu port=5054 AP=%s key=%s station=%s rail=%.3f Ablank=%.4f cal=%d cold=%d armed=%d fault=%d Tmax=%.1f wires=%d mode=%d\n",
        server.addr,(unsigned long)headID,ap,pass,WiFi.localIP().toString().c_str(),hw.rail,hw.blankA,control.calibrated,control.cold,control.armed,control.fault,control.ceiling,control.wires,int(control.mode));
    if(control.calibrated){Serial.printf("A=%.2f R20=%.5f G=%.5f beta=%.3f gamma=%.3f Rseries ohm row-major",control.cal.ambient,control.cal.r20,control.tuning.g_W_K,control.tuning.beta,control.tuning.gamma);for(float r:control.cal.series)Serial.printf(" %.5f",r);Serial.println();}
}
void usb(){
    static char line[110];static unsigned n=0;static bool overflow=false;
    while(Serial.available()){
        int c=Serial.read();if(c=='\r')continue;
        if(c!='\n'){if(n+1<sizeof(line))line[n++]=c;else overflow=true;continue;}
        if(overflow){overflow=false;n=0;continue;}line[n]=0;n=0;
        float value,value2,value3;int id;char end;
        if(!strcmp(line,"ID")){hw.readIdle();info();}
        else if(!strcmp(line,"OFF")){disarm();info();}
        else if(sscanf(line,"UNIT %d %c",&id,&end)==1&&id>=1&&id<=999){
            disarm();if(nv.putUInt("unit",id)==4)unitID=id;newEpoch();info();
        }else if(sscanf(line,"ARRAY %d %c",&id,&end)==1&&id>0){
            disarm();control.cold=false;control.calibrated=false;
            if(nv.putUInt("array",id)==4){headID=id;restoreCalibration(control,storage,ESP.getEfuseMac(),headID);}
            info();
        }else if(sscanf(line,"WIRES %d %c",&id,&end)==1&&id>=2&&id<=4){
            if(id!=control.wires){
                disarm();control.cold=false;control.calibrated=false;
                if(hw.changeWires(id))control.wires=id;
                else Serial.println("Wire count write failed. Check NVS before use.");
            }info();
        }else if(sscanf(line,"LIMIT %f %c",&value,&end)==1&&std::isfinite(value)&&value>=100&&value<=750){
            disarm();control.ceiling=value;info();
        }else if(sscanf(line,"MODEL %f %f %f %c",&value,&value2,&value3,&end)==3
                 &&value>=.03f&&value<=1.f&&value2>=.2f&&value2<=20.f&&value3>=.2f&&value3<=40.f){
            disarm();control.tuning={value*.001f,value2,value3};control.cold=false;info();
        }else if(!strncmp(line,"CAL COLD ",9)){
            value2=wireRef(control.wires);int fields=sscanf(line+9,"%f %f %c",&value,&value2,&end);
            char tail;bool valid=fields==2||(fields==1&&sscanf(line+9,"%f %c",&value,&tail)==1);
            if(valid&&calibrate(value,fields==2?value2/q(value):wireRef(control.wires)))Serial.println("Calibration saved. Confirm cold before ARM.");
            else Serial.println("Calibration failed or cooling interval incomplete.");
        }else if(!strcmp(line,"COLD")){
            disarm();if(control.calibrated&&usNow()>=hw.lastHeat+2000000)control.coldStart(usNow());info();
        }else if(!strcmp(line,"ARM")){
            disarm();control.armed=control.calibrated&&control.cold&&!control.fault&&armHardware();info();
        }else if(!strncmp(line,"WIFI ",5)){
            char* sep=strchr(line+5,'\t');if(sep&&sep>line+5&&sep-line-5<=32&&strlen(sep+1)<=63){*sep=0;WiFi.begin(line+5,sep+1);}
        }else Serial.println("ID | UNIT n | ARRAY label | WIRES n | OFF | CAL COLD degC [bundle_ohm_at_ambient] | MODEL G_mW/K beta gamma | COLD | ARM | LIMIT degC | WIFI ssid<TAB>password");
        memset(line,0,sizeof(line));
    }
}
void setup(){
    for(int p:{RUN,LATCH,DIR9,ARM_PIN,SCLK_PIN,MOSI_PIN}){pinMode(p,OUTPUT);digitalWrite(p,LOW);}
    pinMode(CS,OUTPUT);digitalWrite(CS,HIGH);pinMode(FAULT,INPUT);pinMode(Q_ARM,INPUT);
    SPI.begin(SCLK_PIN,MISO_ADC,MOSI_PIN,-1);SPI.beginTransaction(SPISettings(4000000,MSBFIRST,SPI_MODE0));latch({0,0});
    timerReady=rmtInit(RUN,RMT_TX_MODE,RMT_MEM_NUM_BLOCKS_1,1000000)&&rmtSetEOT(RUN,0)&&gpio_input_enable(static_cast<gpio_num_t>(RUN))==ESP_OK;
    Serial.begin(115200);nv.begin("tpp-r2i",false) /* compatible calibration storage */;unitID=std::clamp(int(nv.getUInt("unit",1)),1,999);
    control.wires=int(nv.getUInt("wires",2));
    headID=nv.getUInt("array",1);restoreCalibration(control,storage,ESP.getEfuseMac(),headID);newEpoch();
    snprintf(ap,sizeof(ap),"TPP-R2J-%06x",unsigned(ESP.getEfuseMac()&0xffffff));
    snprintf(pass,sizeof(pass),"%08x%08x",unsigned(esp_random()),unsigned(esp_random()));
    WiFi.persistent(false);WiFi.mode(WIFI_AP_STA);WiFi.softAP(ap,pass);udpReady=udp.begin(5054)!=0;
}
void loop(){
    usb();if(control.armed&&!healthy()){disarm();control.fault=true;control.cold=false;}
    int n=udp.parsePacket();if(!n){delay(1);return;}
    uint8_t data[256],reply[512];
    if(n>256||udp.read(data,n)!=n){while(udp.available())udp.read();return;}
    hw.readIdle();
    unsigned len=server.handle(data,n,reply,control,hw);
    udp.beginPacket(udp.remoteIP(),udp.remotePort());udp.write(reply,len);udp.endPacket();
}
