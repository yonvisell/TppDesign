// OSC 1.0 messages and immediate bundles. Only the application grammar is accepted.
#pragma once
#include "control.h"
#include <cstdio>
namespace tpp {
inline uint32_t word(const uint8_t* p){return (uint32_t(p[0])<<24)|(uint32_t(p[1])<<16)|(uint32_t(p[2])<<8)|p[3];}
inline void putWord(uint8_t* p,uint32_t v){p[0]=v>>24;p[1]=v>>16;p[2]=v>>8;p[3]=v;}
struct Cursor {
    const uint8_t* p;unsigned n;
    const char* string(){
        unsigned end=0;while(end<n&&p[end])end++;
        unsigned padded=(end+4)&~3U;
        if(end>=n||padded>n)return nullptr;
        for(unsigned i=end;i<padded;i++)if(p[i])return nullptr;
        auto text=reinterpret_cast<const char*>(p);p+=padded;n-=padded;return text;
    }
    uint32_t integer(){auto v=word(p);p+=4;n-=4;return v;}
    float real(){auto u=integer();float f;memcpy(&f,&u,4);return f;}
};
enum class Setting { None, All, Wires, Limit, Mode, Guard, Age };
constexpr const char* ModeNames[]={"simultaneous","rotate-single","rotate-group","temperature-priority","staggered"};
struct Request {
    bool guarded=false,status=false,weighted=false,available=false,train=false;
    int pulses=0;unsigned periodUs=0;Setting setting=Setting::None;int statusVersion=1,wires=0,mode=0,guard=0,age=0;float limit=0;int epoch=0,seq=0;uint32_t deadline=0;unsigned mask=0;float level=0,ms=0,levels[9]{};
};
inline Outcome parseMessage(Cursor c,const char* addr,Request& req){
    const char* a=c.string(),*t=c.string();if(!a||!t)return Bad;
    const size_t base=strlen(addr);
    if(strncmp(a,addr,base)||(a[base]&&a[base]!='/'))return WrongUnit;
    const char* suffix=a+base;
    if(!strcmp(suffix,"/status")){
        req.status=true;
        if(!strcmp(t,",")&&!c.n)return Done;
        if(strcmp(t,",i")||c.n!=4)return Bad;
        req.statusVersion=int(c.integer());
        return (req.statusVersion==2||req.statusVersion==3)?Done:Bad;
    }
    if(!strcmp(suffix,"/config")){
        if(strcmp(t,",ifi")||c.n!=12)return Bad;
        req.setting=Setting::All;req.wires=int(c.integer());req.limit=c.real();req.mode=int(c.integer());
        return req.wires>=2&&req.wires<=4&&std::isfinite(req.limit)&&req.limit>=100&&req.limit<=750&&req.mode>=0&&req.mode<=4?Done:Bad;
    }
    if(!strcmp(suffix,"/config/mode")){
        if(strcmp(t,",s"))return Bad;
        const char* name=c.string();if(!name||c.n)return Bad;
        for(int k=0;k<=4;k++)if(!strcmp(name,ModeNames[k])){req.setting=Setting::Mode;req.mode=k;return Done;}
        return Bad;
    }
    if(!strcmp(suffix,"/config/limit")){
        if(strcmp(t,",f")||c.n!=4)return Bad;
        req.setting=Setting::Limit;req.limit=c.real();
        return std::isfinite(req.limit)&&req.limit>=100&&req.limit<=750?Done:Bad;
    }
    if(!strncmp(suffix,"/config/",8)){
        if(strcmp(t,",i")||c.n!=4)return Bad;
        int value=int(c.integer());
        if(!strcmp(suffix,"/config/wires")){req.setting=Setting::Wires;req.wires=value;return value>=2&&value<=4?Done:Bad;}
        if(!strcmp(suffix,"/config/guard")){req.setting=Setting::Guard;req.guard=value;return value==0||value==1?Done:Bad;}
        if(!strcmp(suffix,"/config/max_age_ms")){req.setting=Setting::Age;req.age=value;return value>=1&&value<=1000?Done:Bad;}
        return Bad;
    }
    req.train=!strcmp(suffix,"/train");
    req.available=!strcmp(suffix,"/actuate");
    req.weighted=req.train||!strcmp(suffix,"/pattern");
    if(!req.weighted&&!req.available&&*suffix)return Bad;
    const char* prefix=req.train?",iff":(req.weighted||req.available)?",f":",ff";
    unsigned prefixLen=strlen(prefix);
    if(strncmp(t,prefix,prefixLen)||c.n!=4*(strlen(t)-1))return Bad;
    const char* siteTags=t+prefixLen;
    unsigned sites=0;
    while(*siteTags){
        if(*siteTags++!='i'||(req.weighted&&*siteTags++!='f')||++sites>9)return Bad;
    }
    if(!sites)return Bad;
    if(req.train)req.pulses=int(c.integer());
    if(req.available)req.level=1.f;
    else if(!req.weighted)req.level=c.real();
    req.ms=c.real();
    if(!std::isfinite(req.ms)||req.ms<1||req.ms>100)return Bad;
    if(req.train){
        float duty=c.real();
        if(req.pulses<1||req.pulses>32||!std::isfinite(duty)||duty<.05f||duty>1)return Bad;
        unsigned onUs=unsigned(std::lround(double(req.ms)*1000));
        req.periodUs=unsigned(std::lround(double(onUs)/duty));
        if(uint64_t(req.pulses-1)*req.periodUs+onUs>2000000)return Bad;
    }
    while(c.n){
        int id=int(c.integer()),row=id/10,col=id%10;
        if(row<1||row>3||col<1||col>3)return Bad;
        unsigned bit=1U<<((row-1)*3+col-1);if(req.mask&bit)return Bad;req.mask|=bit;
        float l=req.weighted?c.real():req.level;
        if(!std::isfinite(l)||l<0||l>1)return Bad;
        req.levels[(row-1)*3+col-1]=l;
    }
    if(!std::isfinite(req.level)||!std::isfinite(req.ms)||req.level<0||req.level>1||req.ms<1||req.ms>100)return Bad;
    return Done;
}
inline Outcome decode(const uint8_t* data,unsigned len,const char* addr,Request& req){
    if(len>256||len%4)return Bad;
    if(len<8||memcmp(data,"#bundle\0",8))return parseMessage({data,len},addr,req);
    if(len<24||word(data+8)||word(data+12)!=1)return Bad;
    unsigned n=word(data+16);if(n>len-24||n%4)return Bad;
    Cursor guard{data+20,n};const char* a=guard.string(),*t=guard.string();
    char path[48];snprintf(path,sizeof(path),"%s/guard",addr);
    if(!a||!t||strcmp(a,path)||strcmp(t,",iii")||guard.n!=12)return Bad;
    req.guarded=true;req.epoch=int(guard.integer());req.seq=int(guard.integer());req.deadline=guard.integer();
    unsigned m=word(data+20+n);if(m!=len-24-n)return Bad;
    auto result=parseMessage({data+24+n,m},addr,req);
    return req.status?Bad:result;
}
struct Writer {
    char tags[64]={','};uint8_t values[370]{};unsigned count=1,size=0;
    void integer(int32_t x){tags[count++]='i';putWord(values+size,uint32_t(x));size+=4;}
    void real(float f){tags[count++]='f';uint32_t u;memcpy(&u,&f,4);putWord(values+size,u);size+=4;}
    void string(const char* s){tags[count++]='s';unsigned n=strlen(s);memcpy(values+size,s,n);size+=(n+4)&~3U;}
    unsigned finish(const char* addr,const char* suffix,uint8_t* out)const{
        char path[50];snprintf(path,sizeof(path),"%s%s",addr,suffix);
        unsigned n=(strlen(path)+4)&~3U,m=(count+4)&~3U;
        memset(out,0,n+m);memcpy(out,path,strlen(path));memcpy(out+n,tags,count);memcpy(out+n+m,values,size);return n+m+size;
    }
};
template<class Hardware> Receipt runTrain(State& st,Hardware& hw,const Request& r,uint64_t firstDeadline,int& completed){
    Receipt total;
    total.mask=r.mask;
    uint64_t start=hw.now();
    for(int j=0;j<r.pulses;j++){
        uint64_t onset=start+uint64_t(j)*r.periodUs;
        if(j){
            total.status=waitRunning(hw,onset);
            if(total.status!=Done)break;
            if(!hw.readIdle()){total.status=Sensor;break;}
        }
        Receipt part=run(st,hw,r.mask,0,r.ms,r.levels,j?UINT64_MAX:firstDeadline,false,onset);
        total.status=part.status;
        total.probes+=part.probes;total.groups+=part.groups;total.currentSamples+=part.currentSamples;
        total.peakT=std::max(total.peakT,part.peakT);total.peakI=std::max(total.peakI,part.peakI);
        for(int i=0;i<9;i++){
            total.dose[i]+=part.dose[i];total.probeEnergy[i]+=part.probeEnergy[i];
            total.unknownUpper[i]+=part.unknownUpper[i];total.timedUpper[i]+=part.timedUpper[i];
        }
        if(part.status!=Done)break;
        completed++;
    }
    if(total.status==Fault||total.status==Sensor){st.armed=false;st.fault=true;st.cold=false;}
    total.elapsedUs=unsigned(hw.now()-start);
    return total;
}
struct Server {
    char addr[32]="/tpp/ta/1";int epoch=1,last=0;bool simulated=false,guardRequired=true;int maxAgeMs=100;
    struct Seen{bool available=false;unsigned mask=0;float ms=0,levels[9]{};uint32_t tick=0;};Seen recent[16]{};unsigned next=0;
    void reset(int id,int serial){snprintf(addr,sizeof(addr),"/tpp/ta/%d",id);epoch=std::max(1,serial&0x7fffffff);last=0;guardRequired=true;maxAgeMs=100;next=0;for(auto& s:recent)s=Seen{};}
    template<class Hardware> unsigned handle(const uint8_t* pkt,unsigned n,uint8_t* reply,State& st,Hardware& hw){
        Request r;Receipt ans;int completed=0;uint32_t now=uint32_t(hw.now()/1000);
        ans.status=decode(pkt,n,addr,r);Writer w;
        if(ans.status==Done&&r.status){
            w.integer(epoch);w.integer(last);w.integer(now);
            w.integer(int(st.armed)|(int(st.calibrated)<<1)|(int(st.cold)<<2)|(int(st.fault)<<3));
            w.integer(simulated);w.real(hw.voltage());
            if(r.statusVersion>=2){w.integer(st.wires);w.real(st.ceiling);w.integer(st.mode);}
            if(r.statusVersion==3){w.integer(guardRequired);w.integer(maxAgeMs);}
            return w.finish(addr,"/status",reply);
        }
        if(ans.status==Done&&r.guarded){
            if(r.epoch!=epoch)ans.status=Epoch;
            else if(r.seq<=0||r.seq<=last)ans.status=Sequence;
            else if(int32_t(r.deadline-now)<=0||int32_t(r.deadline-now)>(r.setting==Setting::None?maxAgeMs:100))ans.status=Stale;
            else last=r.seq;
        }
        if(ans.status==Done&&!r.guarded&&(r.setting!=Setting::None||r.train||(r.available&&guardRequired)))ans.status=GuardRequired;
        if(ans.status==Done&&r.setting!=Setting::None){
            bool changed=false;
            if(r.setting==Setting::All||r.setting==Setting::Wires){
                changed=st.wires!=r.wires;
                if(changed){
                    st.calibrated=false;st.cold=false;st.armed=false;
                    if(!hw.changeWires(r.wires))ans.status=StorageFault;
                    else st.wires=r.wires;
                }
            }
            if(ans.status==Done){
                if(r.setting==Setting::All||r.setting==Setting::Mode)st.mode=Mode(r.mode);
                if(r.setting==Setting::All||r.setting==Setting::Limit)st.ceiling=r.limit;
                if(r.setting==Setting::Guard)guardRequired=r.guard!=0;
                if(r.setting==Setting::Age)maxAgeMs=r.age;
                ans.status=changed?NeedsEnrollment:ConfigSaved;
            }
        }
        if(ans.status==Done&&!r.guarded){
            for(const auto& k:recent)if(k.available==r.available&&k.mask==r.mask&&!memcmp(k.levels,r.levels,sizeof(k.levels))&&k.ms==r.ms&&uint32_t(now-k.tick)<100){ans.status=Duplicate;break;}
            if(ans.status==Done){auto& k=recent[next++%16];k.available=r.available;k.mask=r.mask;k.ms=r.ms;k.tick=now;memcpy(k.levels,r.levels,sizeof(k.levels));}
        }
        if(ans.status==Done){
            uint64_t firstDeadline=UINT64_MAX;
            if(r.guarded){
                uint64_t us=hw.now();int32_t left=int32_t(r.deadline-uint32_t(us/1000));
                firstDeadline=left<=0?us:(us/1000+unsigned(left))*1000;
            }
            if(r.train)ans=runTrain(st,hw,r,firstDeadline,completed);
            else ans=run(st,hw,r.mask,r.level,r.ms,r.levels,firstDeadline,r.available);
        }
        w.integer(epoch);w.integer(r.guarded?r.seq:0);w.string(label(ans.status));w.integer(simulated);
        w.integer(ans.mask);w.integer(ans.probes);w.integer(ans.groups);w.integer(ans.currentSamples);w.integer(ans.elapsedUs);
        w.real(ans.peakT);w.real(ans.peakI);
        for(float x:ans.dose)w.real(x);
        for(float x:ans.probeEnergy)w.real(x);
        for(float x:ans.unknownUpper)w.real(x);
        for(float x:ans.timedUpper)w.real(x);
        if(r.train){w.integer(r.pulses);w.integer(completed);return w.finish(addr,"/train/receipt",reply);}
        return w.finish(addr,"/receipt",reply);
    }
};
}
