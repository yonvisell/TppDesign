"""Run the target OSC receiver against a numerical electrical / thermal plant on loopback."""
import argparse
import ctypes as C
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time

import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"analysis"))
from array_circuit import solve,isolated,ORDER


class Reading(C.Structure):
    _fields_=[(field,C.c_bool) for field in ("started","ok","hwfault","expired","stale")]+[
        ("v",C.c_float),("i",C.c_float),("sample",C.c_uint),("on",C.c_uint),("end",C.c_uint64)]+[(k,C.c_float) for k in ("before_observation","after_observation","ratio")]

Fire=C.CFUNCTYPE(None,C.c_uint,C.c_uint,C.c_uint,C.c_int,C.c_uint64,C.c_uint64,C.c_uint,C.POINTER(Reading))
Clock=C.CFUNCTYPE(C.c_uint64)
Wait=C.CFUNCTYPE(None,C.c_uint64)
PFloat=C.POINTER(C.c_float)


Note=C.CFUNCTYPE(None,C.c_uint,C.c_uint,C.c_int,C.c_uint,C.c_float,C.c_float,C.c_float,PFloat,PFloat,PFloat,PFloat)


def load_native():
    files=[ROOT/"software/native.cpp",*sorted((ROOT/"firmware/src").glob("*.h"))]
    tag=hashlib.sha256(b"".join(f.read_bytes() for f in files)).hexdigest()[:16]
    target=Path(tempfile.gettempdir())/f"tpp-r2k-{tag}.so"
    if not target.exists():
        temp=target.with_suffix(f".{os.getpid()}.so")
        subprocess.run([os.environ.get("CXX","c++"),"-std=c++17","-O2","-fPIC","-shared",str(files[0]),"-o",str(temp)],check=True)
        temp.replace(target)
    lib=C.CDLL(str(target))
    lib.make_fixture.argtypes=[C.c_int,PFloat,C.c_float,C.c_int,Fire,Clock,Wait,Note];lib.make_fixture.restype=C.c_void_p
    lib.switch_ohm.argtypes=[C.c_void_p];lib.switch_ohm.restype=C.c_float;lib.set_switch.argtypes=[C.c_void_p,C.c_float]
    lib.commission.argtypes=[C.c_void_p,C.c_uint64,C.c_uint32,C.c_float,C.c_float]
    lib.restore.argtypes=[C.c_void_p,C.c_uint64,C.c_uint32];lib.get_series.argtypes=[C.c_void_p,PFloat]
    lib.set_record_version.argtypes=[C.c_void_p,C.c_uint32]
    lib.cold_arm.argtypes=[C.c_void_p];lib.corrupt.argtypes=[C.c_void_p];lib.fail_write.argtypes=[C.c_void_p,C.c_int]
    lib.exchange.argtypes=[C.c_void_p,C.c_char_p,C.c_uint,C.POINTER(C.c_uint8)];lib.exchange.restype=C.c_uint
    lib.close_fixture.argtypes=[C.c_void_p]
    for name in ("cal_flag","arm_flag"):
        getattr(lib,name).argtypes=[C.c_void_p,C.c_int]
    lib.set_rail.argtypes=[C.c_void_p,C.c_float]
    lib.idle_state.argtypes=[C.c_void_p,PFloat]
    lib.observe.argtypes=[C.c_float,C.c_float,C.c_float,PFloat];lib.observe.restype=C.c_int
    lib.temperature.argtypes=[C.c_void_p,C.c_uint];lib.temperature.restype=C.c_float
    return lib

LIB=load_native()
MATERIAL=json.loads((ROOT/"firmware/material.json").read_text())
ELECTRIC=json.loads((ROOT/"analysis/input/electrical.json").read_text())["nominal"]
QT=MATERIAL["q_temperature_C"];QR=MATERIAL["q_values"]
FREE=MATERIAL["free_mm"]/MATERIAL["pitch_mm"]
C_FREE=FREE*MATERIAL["whole_C20_uJ_K"]
R20=MATERIAL["pair_R20_ohm"]
CALS={};DRIVE={}
def default_cal(wires=2,rail=6.):
    key=(wires,rail)
    if key not in CALS:
        # Single deterministic commissioning run is reused as the NVS cold record for
        # independent cold-start sweep cases. No ideal per-pixel offsets are injected.
        plant=Plant(offsets=[0]*9,wires=wires,rail=rail)
        try:
            plant.wait(2000001)
            if not LIB.commission(plant.ctx,401,1,25,2*R20/wires):raise RuntimeError("synthetic commissioning failed")
            values=(C.c_float*9)();LIB.get_series(plant.ctx,values);CALS[key]=list(values);DRIVE[key]=LIB.switch_ohm(plant.ctx)
        finally:plant.close()
    return CALS[key]


class Plant:
    """Separate (33 + 12 N)-node electrical solve with N physical wires. ADC readings are rounded to converter codes. A separate integrator evolves wire temperature."""
    def __init__(self,unit=1,ceiling=450,slow_us=0,offsets=None,driver_ohm=None,wires=2,rail=6.):
        self.t=np.full(9,25.);self.s=self.t.copy();self.clk=1000000
        self.joules_uJ=np.zeros(9);self.peak_true_C=25.;self.events=[];self.fault="";self.resistance_bias=0.;self.slow=slow_us
        self.fire_fn=Fire(self.fire);self.clock_fn=Clock(lambda:self.clk);self.wait_fn=Wait(self.wait)
        self.note_fn=Note(self.note);self.wires=wires;self.rail=rail;self.wireR20=2*R20/wires;self.electric=ELECTRIC;self.fail_at=None;cal=(C.c_float*9)(*(default_cal(wires,rail) if offsets is None else offsets))
        self.ctx=LIB.make_fixture(unit,cal,ceiling,wires,self.fire_fn,self.clock_fn,self.wait_fn,self.note_fn)
        LIB.set_rail(self.ctx,rail)
        if driver_ohm is not None:LIB.set_switch(self.ctx,driver_ohm)
        elif offsets is None:LIB.set_switch(self.ctx,DRIVE[(wires,rail)])

    def note(self,active,us,site,sample,prior,posterior,ratio,t,s,upper,p):
        self.events[-1].update(predicted_at_sample_C=prior if site>=0 else None,corrected_at_sample_C=posterior if site>=0 else None,measured_ratio=ratio if site>=0 else None,active_mask=active,sample_us=sample if site>=0 or us>=64 else None,
            observer_wire_C=list(t[:9]),observer_surroundings_C=list(s[:9]),observer_upper_C=list(upper[:9]),estimated_W=list(p[:9]))

    def idle_state(self):
        out=(C.c_float*27)();LIB.idle_state(self.ctx,out)
        return dict(wire_C=list(out[:9]),surroundings_C=list(out[9:18]),upper_C=list(out[18:]))

    def close(self):
        if self.ctx:LIB.close_fixture(self.ctx);self.ctx=None

    def advance(self,dt,power):
        if dt<=0:return
        # Independent explicit midpoint on <2ms intervals. Long idle interval uses
        # 1ms substeps, followed by room equilibrium after 15 seconds.
        if dt>15e6:
            self.t[:]=25;self.s[:]=25;return
        n=max(1,int(np.ceil(dt/1000)));h=dt*1e-6/n
        def rates(t,s):
            qf=np.interp(t,QT,QR);qs=np.interp(s,QT,QR)
            part=FREE*qf/(FREE*qf+(1-FREE)*qs)
            cp=np.interp(t,MATERIAL["cp_temperature_C"],MATERIAL["cp_J_per_kgK"])
            return ((part*power-.00020*(self.wires/2)*(t-s))/(C_FREE*(self.wires/2)*1e-6*cp/460.),self.wires*(t-s)-6*(s-25))
        for _ in range(n):
            a,b=rates(self.t,self.s);a,b=rates(self.t+.5*h*a,self.s+.5*h*b)
            self.t+=h*a;self.s+=h*b
        self.peak_true_C=max(self.peak_true_C,float(self.t.max()))

    def wait(self,target):
        if target>self.clk:
            self.advance(target-self.clk,0.);self.clk=target

    def exchange(self,data):
        buf=(C.c_uint8*512)();n=LIB.exchange(self.ctx,data,len(data),buf)
        return bytes(buf[:n])

    def electrical(self,states):
        resistance=self.wires*self.wireR20*(FREE*np.interp(self.t,QT,QR)+(1-FREE)*np.interp(self.s,QT,QR))
        return solve(self.wires,states,self.electric,resistance,self.rail)

    def fire(self,hi,en,us,site,deadline,start_by,minimum,result):
        r=result.contents
        self.wait(self.clk+18+self.slow) # explicit slot setup + software overhead scenario
        if self.clk>=start_by:r.expired=True;r.stale=True;return
        if self.clk+us+20>deadline:
            if site>=0 or self.clk+minimum+20>deadline:r.expired=True;return
            us=deadline-self.clk-20
        r.on=us
        r.started=True;began=self.clk
        states=[0]+[(1 if hi>>(n-1)&1 else 0) if en>>(n-1)&1 else -1 for n in range(1,10)]
        p0,a0,legs0,_,_=self.electrical(states);pins0=max(abs(legs0))
        sample=min(45,us//2);self.advance(sample,p0);self.clk+=sample
        p,a,ipin,v,_=self.electrical(states)
        self.advance(us-sample,p);self.clk+=us-sample;self.joules_uJ+=p0*sample+p*(us-sample)
        r.end=self.clk;r.ok=True;r.sample=sample;f_v=7.5/4096;f_i=12.5/4096
        if site>=0 or us>=64:r.i=round(a/f_i)*f_i
        if site>=0:
            j=ORDER.index(site)+1
            upper=round(v[j]/f_v)*f_v;r.v=upper-round(v[j-1]/f_v)*f_v
            r.i-=(10-j)*upper/30000
        if site>=0:r.v*=1+self.resistance_bias
        if self.fault=="sample" or self.fail_at==len(self.events):r.ok=False
        if self.fault=="hardware":r.hwfault=True;r.ok=False
        if self.fault=="current":r.i=10.1
        if self.fault=="resistance" and site>=0:r.v*=1.10
        self.events.append(dict(began_us=began,on_us=us,site=site,high=hi,enables=en,bus_A=float(max(a,a0)),pin_A=float(max(pins0,max(abs(ipin)))),sample_current_A=float(r.i),sample_voltage_V=float(r.v),oracle_wire_C=list(self.t),oracle_W=list((p0*sample+p*(us-sample))/us)))
        self.wait(self.clk+8)


def serve(bind="127.0.0.1",unit=1,port=5054,stop=None,wires=2,rail=6.,limit=450):
    plant=Plant(unit,wires=wires,rail=rail,ceiling=limit);origin=time.monotonic_ns()//1000-plant.clk
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sock:
        sock.bind((bind,port));sock.settimeout(.05)
        try:
            while stop is None or not stop.is_set():
                try:data,addr=sock.recvfrom(1024)
                except socket.timeout:continue
                plant.wait(max(plant.clk,time.monotonic_ns()//1000-origin))
                sock.sendto(plant.exchange(data),addr)
        finally:plant.close()


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--unit",type=int,default=1);p.add_argument("--port",type=int,default=5054)
    p.add_argument("--wires",type=int,choices=(2,3,4),default=2);p.add_argument("--rail",type=float,default=6.);p.add_argument("--limit",type=float,default=450)
    a=p.parse_args();serve(unit=a.unit,port=a.port,wires=a.wires,rail=a.rail,limit=a.limit)
