// Shared implementation for the XIAO and deterministic fixture. Times are microseconds;
// power (W) x time (us) gives energy in microjoules.
#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>

namespace tpp {
constexpr float R20=2.8935470f, C20=25.137826f, Free=2.9f/4.2f;
constexpr float Pmax=16.f, FullScaleW=4.36f, ErrorQ=.008f, WindowK=65.f, MarginK=25.f, BlindLimitUJ=3000.f;
constexpr int ProbeUs=80, ColdProbeUs=96, MinSlot=8, MaxSlot=256;
constexpr int Order[]={0,1,2,5,4,3,6,7,8};
constexpr float Qt[]={20,100,200,300,400,500,600,700,800,900,1000,1100,1200};
constexpr float Qr[]={1,1.006,1.015,1.028,1.045,1.065,1.068,1.057,1.051,1.052,1.062,1.071,1.080};
constexpr float Cp[]={460,460,480,500,520,540,560,600,630,650,670,700};
inline float interpolate(float t,const float* y,int n){
    for(int k=1;k<n;k++) if(t<=Qt[k])
        return y[k-1]+std::max(0.f,(t-Qt[k-1])/(Qt[k]-Qt[k-1]))*(y[k]-y[k-1]);
    return y[n-1];
}
inline float q(float t){return interpolate(t,Qr,13);}
inline float capacity(float t){return C20*Free*interpolate(t,Cp,12)/460.f;}
inline int edge(int pixel){return Order[pixel]+1;} // This permutation is its own inverse.
struct Pins { unsigned hi,en; };
inline Pins isolated(int site){unsigned high=1U<<(edge(site)-1); return {high,high|(high>>1)};}
inline Pins group(unsigned mask){
    unsigned high=0;bool level=false;
    for(int i=0;i<9;i++){level^=bool(mask&(1U<<Order[i]));high|=unsigned(level)<<i;}
    return {high,511};
}
inline uint32_t shiftWord(Pins p){return (p.hi&255)|((p.en&511)<<8);}
inline float wireRef(int count){return R20*2.f/count;}
inline float massScale(int count){return .5f*count;}
enum Mode {Simultaneous, RotateSingle, RotateGroup, TemperaturePriority, Staggered};
struct Calibration {float ambient=25, r20=R20,switchOhm=.068f,series[9]{};};
struct Pixel {float t=25,s=25,upper=25; uint64_t stamp=0,lastProbe=0;float sinceProbe=0;};
struct State {
    struct Tuning{float g_W_K=.00020f,beta=2.f,gamma=6.f;};
    Tuning tuning;unsigned nextSite=0;int wires=2;Mode mode=Simultaneous;Calibration cal; Pixel cell[9]; float ceiling=450;
    bool armed=false,calibrated=false,cold=false,fault=false;
    void coldStart(uint64_t now){
        for(auto& p:cell)p={cal.ambient,cal.ambient,cal.ambient,now,now,0};
        cold=true;armed=false;fault=false;
    }
};
enum Outcome {Done,Idle,Bad,Unarmed,MissingCal,Small,Temperature,Ambiguous,Mismatch,Sensor,Current,Timing,Fault,Duplicate,Stale,Epoch,Sequence,WrongUnit,ProbeDue,Duration,ConfigSaved,NeedsEnrollment,StorageFault,GuardRequired};
inline const char* label(Outcome s){
    const char* names[]={"complete","idle","invalid","disarmed","calibration_required","below_resolution","temperature_limit","ambiguous_R","inconsistent_R","invalid_sample","current_limit","timing_limit","hardware_fault","duplicate","stale","epoch","sequence","wrong_unit","probe_required","duration_limit","configured","recalibration_required","storage_error","guard_required"};
    return names[s];
}
struct Reading { bool started=false,ok=false,hwfault=false,expired=false,stale=false; float v=0,i=0; unsigned sampleUs=0,onUs=0;uint64_t end=0;float beforeObservation=0,afterObservation=0,measuredRatio=0; };
struct Receipt {
    Outcome status=Done;unsigned mask=0,probes=0,groups=0,currentSamples=0;
    float dose[9]{},probeEnergy[9]{},peakT=0,peakI=0,unknownUpper[9]{},timedUpper[9]{};unsigned elapsedUs=0;
};
// Exact frozen-coefficient evolution of C(T)*Tdot = P-G(T-S), Sdot=b(T-S)-g(S-A).
// The resistance-derived upper endpoint is propagated conservatively during each pulse.
inline void advance(Pixel& x,float ambient,uint64_t to,float p,State::Tuning fit,int wires=2){
    if(to<=x.stamp)return;
    float dt=float(to-x.stamp)*1.e-6f;
    fit.g_W_K*=massScale(wires);fit.beta*=massScale(wires);
    float c=capacity(x.t)*massScale(wires)*1.e-6f, a=fit.g_W_K/c,b=fit.beta,g=fit.gamma;
    float src=p*Free*q(x.t)/((1-Free)*q(x.s)+Free*q(x.t));
    if(dt<.002f){
        // Midpoint step during short slots; avoids transcendental calls in the hot loop.
        float tMid=x.t+.5f*dt*(src/c-a*(x.t-x.s));
        float sMid=x.s+.5f*dt*(b*(x.t-x.s)-g*(x.s-ambient));
        float delta=dt*(src/c-a*(tMid-sMid));
        x.t+=delta;x.s+=dt*(b*(tMid-sMid)-g*(sMid-ambient));
        x.upper=std::max(x.t,x.upper+delta);x.stamp=to;return;
    }
    float d=std::sqrt((a+b+g)*(a+b+g)-4*a*g);
    float slow=-2*a*g/(a+b+g+d),fast=-(a+b+g+d)/2.f;
    float ss=ambient+b*src/(g*fit.g_W_K),tt=ss+src/fit.g_W_K;
    float t0=x.t-tt,s0=x.s-ss;
    // Use expm1 to avoid cancellation of large source equilibria on short powered steps.
    auto inc=[&](float z,float dz){
        float coef=(dz-fast*z)/d;
        return coef*std::expm1(slow*dt)+(z-coef)*std::expm1(fast*dt);
    };
    float old=x.t;
    x.t+=inc(t0,-a*(t0-s0));x.s+=inc(s0,b*t0-(b+g)*s0);
    x.upper=std::max(x.t,x.upper+(x.t-old));x.stamp=to;
}
inline float ratio(float wire,float surroundings){return Free*q(wire)+(1-Free)*q(surroundings);}
inline Outcome correct(Pixel& x,float ambient,float measured){
    // Intersect each exact piecewise-linear segment with both the measurement band
    // and reachable temperature range. Count connected components across table knots.
    float lo=std::max(ambient,x.t-WindowK),hi=std::min(800.f,x.t+WindowK);
    int components=0;float last=-1e5f,best=x.t,cost=1e20f;
    for(int k=1;k<13;k++){
        float a=std::max(lo,Qt[k-1]),b=std::min(hi,Qt[k]);if(b<a)continue;
        float slope=Free*(Qr[k]-Qr[k-1])/(Qt[k]-Qt[k-1]);
        float base=ratio(a,x.s),t1=a+(measured-ErrorQ-base)/slope,t2=a+(measured+ErrorQ-base)/slope;
        float l=std::max(a,std::min(t1,t2)),h=std::min(b,std::max(t1,t2));
        if(l>h)continue;
        if(l>last+.001f)components++;
        last=h;
        float w=WindowK*WindowK/(ErrorQ*ErrorQ);
        float x0=std::clamp((x.t+w*slope*(measured-base+slope*a))/(1+w*slope*slope),l,h);
        float pr=(x0-x.t)/WindowK,rr=(ratio(x0,x.s)-measured)/ErrorQ, score=pr*pr+rr*rr;
        if(score<cost){cost=score;best=x0;}
    }
    if(components!=1)return components?Ambiguous:Mismatch;
    x.t=best;x.upper=last;
    return Done;
}
// Solve the chain at driven or floating nodes using a tridiagonal passive conductance
// matrix. Fit cold residual after a 40 mOhm cable allocation at each tap. Approximate
// bilateral leg R includes switch and EB copper; T0 is permanently grounded.
struct Power {float site[9]{},bus=0,pin=0;};
inline Power predict(const State& st,Pins pins,float vm){
    float diag[10]{},rhs[10]{},off[9]{},conductance[10]{},drive[10]{},v[10]{};
    for(int n=0;n<10;n++){
        if(n && !(pins.en&(1U<<(n-1))))continue;
        conductance[n]=1.f/(n?.044f+st.cal.switchOhm:.044f);
        drive[n]=(n&&(pins.hi&(1U<<(n-1))))?vm:0.f;
        diag[n]+=conductance[n];rhs[n]+=drive[n]*conductance[n];
    }
    for(int e=0;e<9;e++){
        int k=Order[e];float rn=st.cal.r20*ratio(st.cell[k].t,st.cell[k].s);
        off[e]=-1.f/(rn+std::max(0.f,st.cal.series[k]-.088f));diag[e]-=off[e];diag[e+1]-=off[e];
    }
    for(int n=1;n<10;n++){float w=off[n-1]/diag[n-1];diag[n]-=w*off[n-1];rhs[n]-=w*rhs[n-1];}
    for(int n=9;n>=0;n--)v[n]=(rhs[n]-(n==9?0.f:off[n]*v[n+1]))/diag[n];
    Power p;
    for(int n=0;n<10;n++){
        float i=conductance[n]*(drive[n]-v[n]);p.bus+=std::max(0.f,i);p.pin=std::max(p.pin,std::abs(i));
        if(n){int k=Order[n-1];float wireI=(v[n]-v[n-1])*off[n-1];p.site[k]=wireI*wireI*st.cal.r20*ratio(st.cell[k].t,st.cell[k].s);}
    }
    float busScale=vm/(vm+.021f*p.bus);
    p.bus*=busScale;p.pin*=busScale;for(float& w:p.site)w*=busScale*busScale;
    return p;
}
inline bool calibratedSeries(float x){return std::isfinite(x)&&x>=0.f&&x<=.75f;}
inline bool coldReading(float ambient,float r20,const Reading& r,float& series,int wires=2){
    if(!r.ok||!(r.i>.25f&&r.i<5.f&&r.v>3&&r.sampleUs>0&&r.sampleUs<ColdProbeUs))return false;
    float t=ambient+r20*q(ambient)*r.i*r.i*r.sampleUs*Free/(capacity(ambient)*massScale(wires));
    series=r.v/r.i-r20*ratio(t,ambient);
    return calibratedSeries(series);
}
inline float powerBound(const State& st){return std::max(Pmax,1.08f*6.3f*6.3f/st.cal.r20);}
inline bool headroom(const State& st,int i,unsigned us){
    return st.cell[i].upper+MarginK+powerBound(st)*(us+5)/(C20*massScale(st.wires))<st.ceiling;
}
// Wait only with the outputs blank. Between waits, service local disarm and driver faults.
template<class Hardware> Outcome waitRunning(Hardware& hw,uint64_t until){
    while(true){
        Outcome event=hw.service();
        if(event!=Done)return event;
        uint64_t now=hw.now();
        if(now>=until)return Done;
        hw.waitUntil(std::min(until,now+1000));
    }
}
inline unsigned admissibleGroup(const State& st,unsigned due,unsigned first,float rail){
    unsigned selected=0;
    for(unsigned off=0;off<9&&__builtin_popcount(selected)<3;off++){
        unsigned bit=1U<<((first+off)%9);
        if(!(due&bit))continue;
        Power next=predict(st,group(selected|bit),rail);
        if(next.bus<=8&&next.pin<=5)selected|=bit;
    }
    return selected;
}
template<class Hardware> Receipt run(State& st,Hardware& hw,unsigned mask,float level,float ms,const float* levels=nullptr,uint64_t firstDeadline=UINT64_MAX,bool available=false,uint64_t scheduled=UINT64_MAX){
    Receipt out;out.mask=mask;
    if(!mask||mask>511||(st.mode!=Staggered&&(!available||st.mode==Simultaneous)&&__builtin_popcount(mask)>3)||!std::isfinite(level)||!std::isfinite(ms)||level<0||level>1||ms<1||ms>100){out.status=Bad;return out;}
    const float bound=powerBound(st);
    const unsigned span=unsigned(std::lround(double(ms)*1000));
    float targets[9]{},largest=0;unsigned activeMask=0,shortMask=0,frames=1,tranches[9]{};
    for(int i=0;i<9;i++)if(mask>>i&1){
        float l=levels?levels[i]:level;
        if(!std::isfinite(l)||l<0||l>1){out.status=Bad;return out;}
        targets[i]=FullScaleW*l*span;largest=std::max(largest,targets[i]);
        if(l>0)activeMask|=1U<<i;
    }
    if(!activeMask){out.status=Idle;return out;}
    if(!st.calibrated){out.status=MissingCal;return out;}
    if(!st.armed||!st.cold||st.fault){out.status=Unarmed;return out;}
    frames=std::max(1U,std::min((span+999)/1000,unsigned(largest/(bound*(ProbeUs+MinSlot)))));
    const float railAtStart=hw.voltage();
    const float probeReservation=std::min(bound,1.08f*railAtStart*railAtStart/st.cal.r20)*ProbeUs;
    for(int i=0;i<9;i++)if(activeMask>>i&1){
        float e=targets[i];if(!available&&e<bound*MinSlot*.5f){out.status=Small;return out;}
        tranches[i]=std::max(1U,std::min(frames,unsigned(e/(bound*(ProbeUs+MinSlot)))));
        if(!available&&e<probeReservation){
            shortMask|=1U<<i;
            const auto& c=st.cell[i];
            if(c.sinceProbe>0&&(c.sinceProbe+e>BlindLimitUJ||hw.now()-c.lastProbe>100000)){out.status=ProbeDue;return out;}
        }
    }
    // Shared-current corrections are retained within this command for short continuations
    // of the same parity pattern, which have no ADC aperture of their own.
    float currentScale[512]{};
    bool started=false;
    const uint64_t start=scheduled==UINT64_MAX?hw.now():scheduled,deadline=start+span;
    const bool staggered=!available&&st.mode==Staggered;
    unsigned cursor=staggered?st.nextSite:0;
    if(staggered){
        while(!(activeMask&(1U<<cursor)))cursor=(cursor+1)%9;
        st.nextSite=(cursor+1)%9;
    }
    auto attempt=[&](unsigned active,Pins pins,unsigned us,int site)->Outcome{
        Outcome event=hw.service();
        if(event!=Done)return event;
        uint64_t now=hw.now();
        if(now+us+20>deadline){
            if(available||site>=0||now+MinSlot+20>deadline)return Timing;
            us=unsigned(deadline-now-20);
        }
        for(int i=0;i<9;i++){advance(st.cell[i],st.cal.ambient,now,0,st.tuning,st.wires);if((active>>i&1)&&!headroom(st,i,us))return Temperature;}
        if(staggered){
            float c=Free*C20*massScale(st.wires);
            for(int i=0;i<9;i++)if((active>>i&1)&&st.cell[i].upper+MarginK+bound*(us+5)/c>=st.ceiling)return Temperature;
        }
        const float rail=hw.voltage();if(!(rail>=5.7f&&rail<=6.3f))return Sensor;
        Power p=predict(st,pins,rail);
        float priorScale=currentScale[active]>0?currentScale[active]:1.f;
        if(!(p.bus>0&&p.bus*std::max(1.f,priorScale)<=8&&p.pin*std::max(1.f,priorScale)<=5))return Current;
        if(!started&&now>=firstDeadline)return Stale;
        for(int k=0;k<9;k++)if((shortMask&active)>>k&1)
            if(st.cell[k].sinceProbe+(us+5)*bound>BlindLimitUJ)return ProbeDue;
        auto r=hw.fire(pins,us,site,deadline,started?UINT64_MAX:firstDeadline,available?ProbeUs:MinSlot);
        if(r.expired)return r.stale?Stale:Timing;
        if(r.onUs>0)us=r.onUs;
        started|=r.started;
        if(r.started)for(int k=0;k<9;k++)if(active>>k&1)out.timedUpper[k]+=bound*(us+5);
        auto unknown=[&](Outcome reason){
            if(r.started)for(int k=0;k<9;k++)if(active>>k&1)out.unknownUpper[k]+=(us+5)*bound;
            return reason;
        };
        if(r.hwfault)return unknown(Fault);
        if(available&&r.started&&(!(r.i>0)||us<ProbeUs))return unknown(Sensor);
        if(!r.ok||r.end<us)return unknown(Sensor);
        const auto began=r.end-us;
        for(auto& c:st.cell)advance(c,st.cal.ambient,began,0,st.tuning,st.wires);
        if(r.i>0){
            if(!(r.i<=8 && (site<0||r.i<=5) && p.pin*(r.i/p.bus)<=5 && std::abs(p.bus-r.i)<std::max(.25f,.22f*p.bus)))return unknown(Current);
            out.peakI=std::max(out.peakI,r.i);out.currentSamples++;
            priorScale=r.i/p.bus;
            currentScale[active]=priorScale;
        }
        for(float& w:p.site)w*=priorScale*priorScale;
        if(site>=0){
            if(!(r.i>.25f&&r.v>1.f&&r.sampleUs>0&&r.sampleUs<us))return unknown(Sensor);
            float rn=r.v/r.i-st.cal.series[site],w=r.i*r.i*rn;
            if(!(rn>0&&std::isfinite(w)&&w<bound))return unknown(Sensor);
            p.site[site]=w;
            Pixel& c=st.cell[site];
            advance(c,st.cal.ambient,began+r.sampleUs,w,st.tuning,st.wires);
            r.measuredRatio=rn/st.cal.r20;r.beforeObservation=c.t;
            Outcome obs=correct(c,st.cal.ambient,r.measuredRatio);r.afterObservation=c.t;
            out.probes++;out.probeEnergy[site]+=us*w;
            if(obs==Done){c.sinceProbe=0;c.lastProbe=began+r.sampleUs;}
            // Even a rejected observation follows an actual timed pulse.
            for(int k=0;k<9;k++){advance(st.cell[k],st.cal.ambient,r.end,p.site[k],st.tuning,st.wires);out.dose[k]+=us*p.site[k];}
            if(obs!=Done)return obs;
        }else{
            out.groups++;
            for(int k=0;k<9;k++)if(active>>k&1)st.cell[k].sinceProbe+=bound*(us+5);
            for(int k=0;k<9;k++){advance(st.cell[k],st.cal.ambient,r.end,p.site[k],st.tuning,st.wires);out.dose[k]+=us*p.site[k];}
        }
        hw.note(st,active,us,site,r,p);
        for(const auto& c:st.cell)out.peakT=std::max(out.peakT,c.t);
        for(const auto& c:st.cell)if(c.upper+MarginK>=st.ceiling)return Temperature;
        return Done;
    };
    if(available){
        // Each group receives isolated, current-and-voltage sampled exposures, then
        // one joint shunt-sampled exposure. A singleton uses one longer measured slot.
        // Replan only the temperature-priority partition at each complete rotation.
        unsigned fixed[9]{},count=0;
        auto partition=[&](bool byTemperature){
            count=0;unsigned remaining=activeMask;
            while(remaining){
                int first=-1;
                for(int i=0;i<9;i++)if(remaining&(1U<<i)){
                    if(first<0||(byTemperature&&st.cell[i].t<st.cell[first].t))first=i;
                }
                unsigned selected=1U<<first;remaining^=selected;
                if(st.mode!=RotateSingle){
                    unsigned candidates=remaining;
                    while(candidates&&__builtin_popcount(selected)<3){
                        int pick=-1;
                        for(int i=0;i<9;i++)if(candidates&(1U<<i))
                            if(pick<0||(byTemperature&&st.cell[i].t<st.cell[pick].t))pick=i;
                        unsigned bit=1U<<pick;candidates^=bit;
                        Power candidate=predict(st,group(selected|bit),hw.voltage());
                        if(candidate.bus<=8&&candidate.pin<=5){selected|=bit;remaining^=bit;}
                    }
                }
                fixed[count++]=selected;
            }
        };
        auto drive=[&](unsigned bits,Pins pins,int site,unsigned desired){
            uint64_t now=hw.now();
            for(auto& c:st.cell)advance(c,st.cal.ambient,now,0,st.tuning,st.wires);
            for(const auto& c:st.cell)if(c.upper+MarginK>=st.ceiling)return Temperature;
            // An available-power pulse requires a usable shunt aperture on every edge.
            // Bound all prospective heat as if deposited in the free wire mass.
            float permissible=desired;
            for(int i=0;i<9;i++)if(bits&(1U<<i)){
                float room=st.ceiling-st.cell[i].upper-MarginK;
                permissible=std::min(permissible,room*C20*Free*massScale(st.wires)/bound-6.f);
            }
            if(permissible<ProbeUs)return Temperature;
            if(now>=deadline||deadline-now<ProbeUs+40)return Duration;
            unsigned dwell=std::min(unsigned(permissible),unsigned(deadline-now-40));
            return attempt(bits,pins,dwell,site);
        };
        for(auto& c:st.cell)advance(c,st.cal.ambient,start,0,st.tuning,st.wires);
        if(!(railAtStart>=5.7f&&railAtStart<=6.3f))out.status=Sensor;
        if(st.mode==Simultaneous){
            fixed[count++]=activeMask;
            auto p=predict(st,group(activeMask),railAtStart);
            if(p.bus>8||p.pin>5)out.status=Current; // decline before the first probe
        }else partition(st.mode==TemperaturePriority);
        while(out.status==Done){
            for(unsigned g=0;g<count&&out.status==Done;g++){
                unsigned bits=fixed[g];bool multiple=(bits&(bits-1))!=0;
                for(int k=0;k<9&&out.status==Done;k++)if(bits&(1U<<k))
                    out.status=drive(1U<<k,isolated(k),k,multiple?ProbeUs:MaxSlot);
                if(multiple&&out.status==Done)out.status=drive(bits,group(bits),-1,MaxSlot);
            }
            if(out.status==Done&&st.mode==TemperaturePriority)partition(true);
        }
    }
    for(unsigned f=0;!available&&f<frames&&out.status==Done;f++){
        out.status=waitRunning(hw,start+uint64_t(f)*span/frames);
        if(out.status!=Done)break;
        uint64_t frameStart=hw.now();
        for(auto& pixel:st.cell)advance(pixel,st.cal.ambient,frameStart,0,st.tuning,st.wires);
        float aim[9]{};unsigned probeMask=0;
        for(int i=0;i<9;i++)if(activeMask>>i&1){
            unsigned index=f*tranches[i]/frames;
            bool next=f==0||index!=(f-1)*tranches[i]/frames;
            aim[i]=targets[i]*float(index+1)/tranches[i];
            if(next&&!(shortMask>>i&1))probeMask|=1U<<i;
        }
        unsigned dwell[9]={};
        for(int i=0;i<9;i++)dwell[i]=ProbeUs;
        if(!staggered&&__builtin_popcount(probeMask)>1){
            // Shared taps make some selected branches cooler at the same group duty.
            // Deposit part of their extra demand during their already required probe,
            // eliminating otherwise separate trailing enable/latch transitions.
            auto pg=predict(st,group(probeMask),hw.voltage());
            float pSingle[9]{},sharedUs=1.e8f;
            for(int i=0;i<9;i++)if(probeMask>>i&1){
                auto ps=predict(st,isolated(i),hw.voltage());pSingle[i]=ps.site[i];
                sharedUs=std::min(sharedUs,std::max(0.f,aim[i]-out.dose[i]-ProbeUs*pSingle[i])/pg.site[i]);
            }
            for(int i=0;i<9;i++)if(probeMask>>i&1){
                float need=aim[i]-out.dose[i];
                float want=(need-sharedUs*pg.site[i])/pSingle[i];
                float permitted=std::min({160.f,need/bound,C20*massScale(st.wires)*(st.ceiling-MarginK-st.cell[i].upper)/bound-6.f});
                dwell[i]=unsigned(std::max(float(ProbeUs),std::min(std::round(want),std::floor(permitted))));
            }
        }
        for(unsigned step=0;step<9&&out.status==Done;step++){
            unsigned i=(cursor+step)%9;
            if(probeMask>>i&1)out.status=attempt(1U<<i,isolated(i),dwell[i],i);
        }
        unsigned unvisited=activeMask;
        for(int iter=0;iter<100&&out.status==Done;iter++){
            unsigned active=0;
            for(int i=0;i<9;i++)if((activeMask>>i&1)&&aim[i]-out.dose[i]>=bound*MinSlot*.5f)active|=1U<<i;
            if(!active)break;
            if(staggered){
                // Give each site with a remaining budget one visit per pass. Keep
                // the original synchronized wall window and its per-site targets.
                unvisited&=active;
                if(!unvisited)unvisited=active;
                active=admissibleGroup(st,unvisited,cursor,hw.voltage());
                if(!active){out.status=Current;break;}
                unvisited&=~active;
            }
            auto pins=group(active);auto p=predict(st,pins,hw.voltage());
            float scale=currentScale[active]>0?currentScale[active]:1.f;
            for(float& w:p.site)w*=scale*scale;
            float duration=staggered?128:MaxSlot,weakestNeed=0,maxWithinTolerance=duration;
            for(int i=0;i<9;i++)if(active>>i&1){
                float available=C20*massScale(st.wires)*(st.ceiling-MarginK-st.cell[i].upper)/bound-6.f;
                float w=std::max(.01f,p.site[i]),need=aim[i]-out.dose[i];
                duration=std::min(duration,std::min(available,need/w));
                weakestNeed=std::max(weakestNeed,need/w);
                maxWithinTolerance=std::min(maxWithinTolerance,std::min(available,(need+bound*MinSlot*.5f)/w));
            }
            // When another setup may not fit, spend the last joint dwell on the
            // neediest branch while all other branches remain within one half-slot
            // energy allowance. No thermal, current or wall-time limit changes.
            uint64_t current=hw.now();
            if(!staggered&&__builtin_popcount(active)>1 && (current>=deadline||deadline-current<unsigned(std::max(0.f,duration)+85)))
                duration=std::min(weakestNeed,maxWithinTolerance);
            if(duration<0){out.status=Temperature;break;}
            unsigned us=std::clamp(unsigned(std::lround(duration)),unsigned(MinSlot),unsigned(MaxSlot));
            out.status=attempt(active,pins,us,-1);
            if(iter==99&&out.status==Done)out.status=Timing;
        }
    }
    if(out.status==Done)out.status=waitRunning(hw,deadline);
    out.elapsedUs=unsigned(hw.now()-start);
    if(out.status!=Done&&out.status!=Duration&&out.status!=Unarmed&&!(out.status==Current&&!started)&&out.status!=Temperature&&out.status!=Timing&&out.status!=ProbeDue&&out.status!=Stale){
        st.armed=false;st.fault=true;st.cold=false;
    }
    return out;
}
} // namespace tpp
