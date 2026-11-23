// Commissioning, persisted representation and identity checks shared by the XIAO and fixture.
#pragma once
#include "control.h"
#include "path_limits.h"
#include <cstddef>
namespace tpp {
// The mechanical stack changed in Revision K; preserve setup but require a new cold acquisition.
constexpr uint32_t CalibrationVersion=0x4b3031U;
struct Record {
    uint32_t version=CalibrationVersion,boardLow=0,boardHigh=0,head=0,wireCount=0;
    Calibration cal;uint32_t checksum=0;
};
inline bool validWireRef(int wires,float r20){
    return wires>=2&&wires<=4&&std::isfinite(r20)&&r20>=.90f*wireRef(wires)&&r20<=1.10f*wireRef(wires)&&6.3f/r20<=5.f;
}
inline uint32_t checkRecord(const Record& rec){
    uint32_t h=2166136261U;auto* p=reinterpret_cast<const uint8_t*>(&rec);
    for(unsigned i=0;i<offsetof(Record,checksum);i++)h=(h^p[i])*16777619U;
    return h;
}
template<class Store> bool restoreCalibration(State& st,Store& store,uint64_t board,uint32_t head){
    st.calibrated=false;Record r;
    if(!store.read(r)||r.version!=CalibrationVersion||r.boardLow!=uint32_t(board)||
       r.boardHigh!=uint32_t(board>>32)||r.head!=head||r.wireCount!=unsigned(st.wires)||r.checksum!=checkRecord(r))return false;
    if(!std::isfinite(r.cal.ambient)||r.cal.ambient<20||r.cal.ambient>40||
       !validWireRef(st.wires,r.cal.r20))return false;
    if(!std::isfinite(r.cal.switchOhm)||r.cal.switchOhm<0||r.cal.switchOhm>.35f)return false;
    for(int i=0;i<9;i++){
        float x=r.cal.series[i];if(!std::isfinite(x)||x<SeriesLo[i]||x>SeriesHi[i])return false;
    }
    st.cal=r.cal;st.calibrated=true;return true;
}
template<class Hardware,class Store> bool enroll(State& st,Hardware& hw,Store& store,
                                                uint64_t board,uint32_t head,float ambient,float r20){
    st.armed=false;st.cold=false;st.calibrated=false;
    if(!std::isfinite(ambient)||ambient<20||ambient>40||!validWireRef(st.wires,r20)||
       6.3f/r20>5.f||!head||!hw.quiet())return false;
    if(!store.erase()||!hw.prepareCal())return false;
    Record rec;rec.boardLow=uint32_t(board);rec.boardHigh=uint32_t(board>>32);rec.head=head;rec.wireCount=st.wires;
    rec.cal.ambient=ambient;rec.cal.r20=r20;float previous[9]{};float switchSum=0;int legs=0;
    for(int repeat=0;repeat<2;repeat++)for(int i=0;i<9;i++){
        hw.waitUntil(hw.now()+250000);
        if(!hw.readIdle())return false;
        const auto r=hw.fire(isolated(i),ColdProbeUs,i,UINT64_MAX);
        float series;
        if(!coldReading(ambient,r20,r,series,st.wires)||series<SeriesLo[i]||series>SeriesHi[i]||
           (repeat&&std::abs(series-previous[i])>.035f))return false;
        if(edge(i)>1){
            // Two conducting FETs. Idle rail minus driven J2 differential includes the
            // two local switch paths and the shared feed; average independent observations.
            switchSum+=(hw.voltage()-r.v)/r.i-.021f;legs+=2;
        }
        rec.cal.series[i]+=.5f*series;previous[i]=series;
    }
    rec.cal.switchOhm=switchSum/legs;
    if(!std::isfinite(rec.cal.switchOhm)||rec.cal.switchOhm<0||rec.cal.switchOhm>.35f)return false;
    rec.checksum=checkRecord(rec);
    if(!store.write(rec)||!restoreCalibration(st,store,board,head))return false;
    if(memcmp(&rec.cal,&st.cal,sizeof(Calibration))!=0){st.calibrated=false;return false;}
    return true;
}
}
