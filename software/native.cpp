// C ABI exposing precisely the target parser, thermal observer and scheduler to a plant.
#include "../firmware/src/osc.h"
#include "../firmware/src/calibration.h"
using namespace tpp;
extern "C" {
typedef void (*Fire)(unsigned,unsigned,unsigned,int,uint64_t,uint64_t,unsigned,Reading*);
typedef void (*Note)(unsigned,unsigned,int,unsigned,float,float,float,const float*,const float*,const float*,const float*);
typedef uint64_t (*Clock)();
typedef void (*Wait)(uint64_t);
struct Storage{
    Record saved{};bool has=false,fail=false;
    bool read(Record& r){if(!has)return false;r=saved;return true;}
    bool write(const Record& r){if(fail)return false;saved=r;has=true;return true;}
    bool erase(){has=false;return true;}
};
struct Fixture {
    State st;Server server;Fire fireFn;Clock clock;Wait wait;Note onNote;float rail;int unit,persistedWires=2;Storage store;uint64_t lastHeat=0;
    Reading fire(Pins p,unsigned us,int site,uint64_t deadline,uint64_t startBy=UINT64_MAX,unsigned minimum=MinSlot){Reading r;fireFn(p.hi,p.en,us,site,deadline,startBy,minimum,&r);if(r.started)lastHeat=r.end;return r;}
    void note(const State& state,unsigned active,unsigned us,int site,const Reading& r,const Power& p){
        float wire[9],surround[9],upper[9];
        for(int k=0;k<9;k++){wire[k]=state.cell[k].t;surround[k]=state.cell[k].s;upper[k]=state.cell[k].upper;}
        onNote(active,us,site,r.sampleUs,r.beforeObservation,r.afterObservation,r.measuredRatio,wire,surround,upper,p.site);
    }
    bool changeWires(int n){if(store.fail||!store.erase())return false;persistedWires=n;return true;}
    bool quiet(){return now()>=lastHeat+2000000;}bool readIdle(){return rail>=5.7f&&rail<=6.3f;}bool prepareCal(){return readIdle();}
    float voltage(){return rail;}uint64_t now(){return clock();}void waitUntil(uint64_t t){wait(t);}
};
Fixture* make_fixture(int unit,const float* cal,float ceiling,int wires,Fire fire,Clock clock,Wait wait,Note note){
    auto* b=new Fixture{};b->fireFn=fire;b->clock=clock;b->wait=wait;b->rail=6;b->onNote=note;b->unit=unit;
    b->persistedWires=wires;b->st.wires=wires;b->st.cal.r20=wireRef(wires);
    b->server.reset(unit,881122);b->server.simulated=true;
    std::copy(cal,cal+9,b->st.cal.series);b->st.calibrated=true;b->st.ceiling=ceiling;
    b->st.coldStart(clock());b->st.armed=true;return b;
}
int commission(Fixture* b,uint64_t board,uint32_t head,float ambient,float r20){return enroll(b->st,*b,b->store,board,head,ambient,r20);}
int restore(Fixture* b,uint64_t board,uint32_t head){b->st=State{};b->st.wires=b->persistedWires;b->server.reset(b->unit,b->server.epoch+1);return restoreCalibration(b->st,b->store,board,head);}
void cold_arm(Fixture* b){if(b->st.calibrated&&b->quiet()){b->st.coldStart(b->now());b->st.armed=true;}}
void set_record_version(Fixture* b,uint32_t version){
    b->store.saved.version=version;
    b->store.saved.checksum=checkRecord(b->store.saved);
}
void corrupt(Fixture* b){b->store.saved.checksum^=1;}
void fail_write(Fixture* b,int v){b->store.fail=v;}
float switch_ohm(Fixture* b){return b->st.cal.switchOhm;}
void set_switch(Fixture* b,float x){b->st.cal.switchOhm=x;}
void get_series(Fixture* b,float* out){std::copy(b->st.cal.series,b->st.cal.series+9,out);}
unsigned exchange(Fixture* b,const uint8_t* p,unsigned n,uint8_t* out){return b->server.handle(p,n,out,b->st,*b);}
void close_fixture(Fixture* b){delete b;}
float temperature(Fixture* b,unsigned i){return b->st.cell[i].t;}
void arm_flag(Fixture* b,int val){b->st.armed=val;}
void cal_flag(Fixture* b,int val){b->st.calibrated=val;}
void set_rail(Fixture* b,float v){b->rail=v;}
void idle_state(Fixture* b,float* out){
    for(int k=0;k<9;k++){auto& p=b->st.cell[k];advance(p,b->st.cal.ambient,b->now(),0,b->st.tuning,b->st.wires);out[k]=p.t;out[9+k]=p.s;out[18+k]=p.upper;}
}
int observe(float t,float s,float measured,float* out){
    Pixel x{};x.t=t;x.s=s;auto code=correct(x,25,measured);out[0]=x.t;out[1]=x.upper;return int(code);
}
float cold_offset(float ambient,float r20,float v,float i,unsigned sample){
    Reading r;r.ok=true;r.i=i;r.v=v;r.sampleUs=sample;float series;
    return coldReading(ambient,r20,r,series)?series:-1;
}
unsigned probe_word(int k){return shiftWord(isolated(k));}
unsigned group_word(unsigned mask){return shiftWord(group(mask));}
}
