"""Send guarded OSC/UDP commands to a thermopneumatic pixel display."""
import argparse
import json
import math
import socket
import struct
import time


FULL_SCALE_W=4.36
MODES=("simultaneous","rotate-single","rotate-group","temperature-priority","staggered")


def string(value):
    raw=value.encode("ascii")+b"\0"
    return raw+b"\0"*((-len(raw))%4)


def message(path,tags,*values):
    if len(tags)!=len(values):
        raise ValueError("OSC type count")
    data=string(path)+string(","+tags)
    for typ,value in zip(tags,values):
        data+=string(value) if typ=="s" else struct.pack(">"+typ,value)
    return data


def unpack(data):
    def take_string(offset):
        end=data.index(0,offset)
        following=(end+4)&~3
        if following>len(data) or any(data[end:following]):
            raise ValueError("OSC string padding")
        return data[offset:end].decode("ascii"),following
    path,k=take_string(0)
    tags,k=take_string(k)
    if not tags.startswith(","):
        raise ValueError("OSC type tags")
    result=[]
    for typ in tags[1:]:
        if typ=="s":
            value,k=take_string(k)
        elif typ in ("i","f"):
            value,=struct.unpack_from(">"+typ,data,k)
            k+=4
        else:
            raise ValueError("OSC type")
        result.append(value)
    if k!=len(data):
        raise ValueError("trailing OSC data")
    return path,tags,result


def pixel_code(cell):
    if isinstance(cell,int) and not isinstance(cell,bool):
        row,col=divmod(cell,10)
    elif isinstance(cell,(tuple,list)) and len(cell)==2:
        row,col=cell
    else:
        raise ValueError("use (row,column) or decimal 11..33")
    if type(row) is not int or type(col) is not int or row not in (1,2,3) or col not in (1,2,3):
        raise ValueError("pixel outside 3 by 3 array")
    return 10*row+col


def pulse(path,level,ms,pixels):
    ids=[pixel_code(k) for k in pixels]
    if not 1<=len(ids)<=9 or len(set(ids))!=len(ids):
        raise ValueError("select one to nine distinct pixels")
    if not(math.isfinite(level) and math.isfinite(ms) and 0<=level<=1 and 1<=ms<=100):
        raise ValueError("level 0..1; duration 1..100 ms")
    return message(path,"ff"+"i"*len(ids),level,ms,*ids)


def pattern(path,ms,levels):
    if not 1<=len(levels)<=9 or not math.isfinite(ms) or not 1<=ms<=100:
        raise ValueError("select one to nine pixels and 1..100 ms")
    values=[ms];ids=set()
    for pixel,level in levels.items():
        code=pixel_code(pixel)
        if code in ids or not math.isfinite(level) or not 0<=level<=1:
            raise ValueError("duplicate pixel or invalid level")
        ids.add(code);values.extend((code,level))
    return message(path+"/pattern","f"+"if"*len(ids),*values)


def train(path,count,on_ms,duty,levels):
    if type(count) is not int or not 1<=count<=32 or not math.isfinite(duty) or not .05<=duty<=1:
        raise ValueError("use 1–32 windows and duty fraction 0.05–1")
    # Let the same validated mapping and float32 wire values determine the schedule.
    _,_,args=unpack(pattern(path,on_ms,levels))
    duty=struct.unpack(">f",struct.pack(">f",duty))[0]
    on_us=math.floor(args[0]*1000+.5)
    period_us=math.floor(on_us/duty+.5)
    elapsed=(count-1)*period_us+on_us
    if elapsed>2_000_000:raise ValueError("train schedule exceeds two seconds")
    return message(path+"/train","iff"+"if"*len(levels),count,args[0],duty,*args[1:])


def configuration(path,wires,limit_C,mode):
    if type(wires) is not int or wires not in (2,3,4) or mode not in MODES or not math.isfinite(limit_C) or not 100<=limit_C<=750:
        raise ValueError("use 2–4 wires, 100–750 degrees C and a named mode")
    return message(path+"/config","ifi",wires,limit_C,MODES.index(mode))


def actuation(path,ms,pixels):
    ids=[pixel_code(p) for p in pixels]
    if not 1<=len(ids)<=9 or len(set(ids))!=len(ids) or not math.isfinite(ms) or not 1<=ms<=100:
        raise ValueError("use 1–9 distinct pixels and 1–100 ms")
    return message(path+"/actuate","f"+"i"*len(ids),ms,*ids)


def signed(u):
    return ((u+2**31)%2**32)-2**31


def guarded(path,cmd,epoch,seq,deadline_ms):
    guard=message(path+"/guard","iii",epoch,seq,signed(deadline_ms))
    return b"#bundle\0"+struct.pack(">Q",1)+b"".join(struct.pack(">I",len(x))+x for x in (guard,cmd))


def receipt(data,path,epoch=None,seq=None,train_reply=False):
    address,tags,args=unpack(data)
    tail="ii" if train_reply else ""
    expected=path+("/train/receipt" if train_reply else "/receipt")
    if address!=expected or tags!=",iisiiiiiiff"+"f"*36+tail:
        raise ValueError("receipt identity or type mismatch")
    e,n,reason,sim,mask,probes,slots,samples,elapsed,t,i,*vectors=args
    if (epoch is not None and e!=epoch) or (seq is not None and n!=seq):
        raise ValueError("receipt epoch or sequence mismatch")
    details=dict(pulses_requested=vectors[-2],pulses_completed=vectors[-1]) if train_reply else {}
    fields=("energy_uJ","probe_uJ","unknown_upper_uJ","selected_timed_upper_uJ")
    arrays={key:vectors[9*j:9*j+9] for j,key in enumerate(fields)}
    return dict(epoch=e,sequence=n,outcome=reason,simulated=bool(sim),mask=mask,probe_count=probes,
                group_slots=slots,current_samples=samples,elapsed_us=elapsed,peak_estimated_C=t,peak_sampled_A=i,**arrays,**details)


class Client:
    def __init__(self,host,unit=1,port=5054,timeout=.30):
        if type(unit) is not int or not 1<=unit<=999:
            raise ValueError("unit 1..999")
        self.path=f"/tpp/ta/{unit}"
        self._last_age_ms=100
        self.socket=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.socket.settimeout(timeout)
        self.socket.connect((host,port))

    def close(self):
        self.socket.close()

    def status(self):
        self.socket.send(message(self.path+"/status","i",3))
        end=time.monotonic()+self.socket.gettimeout()
        while time.monotonic()<end:
            try:a,t,v=unpack(self.socket.recv(512))
            except (ValueError,UnicodeError,struct.error):continue
            if a==self.path+"/status" and t==",iiiiififiii":
                e,n,ms,flags,sim,rail,wires,limit_C,mode,guard,age=v
                self._last_age_ms=age
                return dict(epoch=e,last_sequence=n,receiver_ms=ms&0xffffffff,flags=flags,simulated=bool(sim),rail_V=rail,wires=wires,limit_C=limit_C,mode=MODES[mode],
                            guard_enabled=bool(guard),max_age_ms=age,armed=bool(flags&1),calibrated=bool(flags&2),
                            cold_initialized=bool(flags&4),fault=bool(flags&8))
        raise TimeoutError("status timeout")

    def configure(self,wires,limit_C,mode):
        return self._send(configuration(self.path,wires,limit_C,mode),None,False,setting=True)

    def set_wires(self,wires):
        if type(wires) is not int or wires not in (2,3,4):raise ValueError("wires must be 2, 3 or 4")
        return self._setting("wires","i",wires)

    def set_limit(self,limit_C):
        if not math.isfinite(limit_C) or not 100<=limit_C<=750:raise ValueError("limit must be 100–750 °C")
        return self._setting("limit","f",limit_C)

    def set_mode(self,mode):
        if mode not in MODES:raise ValueError("unknown drive mode")
        return self._setting("mode","s",mode)

    def set_guard(self,enabled):
        if type(enabled) is not bool:raise ValueError("guard setting must be True or False")
        return self._setting("guard","i",int(enabled))

    def set_max_age_ms(self,ms):
        if type(ms) is not int or not 1<=ms<=1000:raise ValueError("age must be 1–1000 integer milliseconds")
        return self._setting("max_age_ms","i",ms)

    def _setting(self,name,tag,value):
        return self._send(message(self.path+"/config/"+name,tag,value),None,False,setting=True)

    def actuate(self,ms,pixels,observed=None,raw=False):
        return self._send(actuation(self.path,ms,pixels),observed,raw)

    def command(self,level,ms,pixels,observed=None,raw=False):
        cmd=pulse(self.path,level,ms,pixels)
        return self._send(cmd,observed,raw)

    def dose(self,watts,ms,pixels,observed=None):
        """Request a calibrated mean NiCr power in watts per selected site."""
        return self.command(watts/FULL_SCALE_W,ms,pixels,observed=observed)

    def pattern(self,ms,levels,observed=None):
        return self._send(pattern(self.path,ms,levels),observed,False)

    def train(self,count,on_ms,duty,levels,observed=None):
        cmd=train(self.path,count,on_ms,duty,levels)
        # Include the maximum scheduled span in the response timeout only.
        span_s=((count-1)*on_ms/duty+on_ms)/1000
        return self._send(cmd,observed,False,train_seconds=span_s)

    def _send(self,cmd,observed,raw,setting=False,train_seconds=0.):
        t=time.monotonic()
        if observed is None:observed=t
        if not math.isfinite(observed) or observed>t:
            raise ValueError("observation must use local monotonic acquisition time")
        if t-observed>=(self._last_age_ms/1000 if raw else 1.0):
            return dict(outcome="observation_expired")
        epoch=None;seq=0
        if not raw:
            try:status=self.status()
            except (TimeoutError,ConnectionError,OSError):return dict(outcome="status_unavailable")
            # Charge outbound STATUS transit, reply transit and host processing to the
            # original observation before converting to receiver-relative time.
            age_ms=100 if setting else status["max_age_ms"]
            remaining=math.floor(age_ms-(time.monotonic()-observed)*1000)
            if remaining<=0:return dict(outcome="observation_expired")
            epoch=status["epoch"];seq=status["last_sequence"]+1
            if seq>=2**31:return dict(outcome="sequence_exhausted")
            cmd=guarded(self.path,cmd,epoch,seq,status["receiver_ms"]+remaining)
        if not raw:return self._exchange(self.socket,cmd,epoch,seq,train_seconds)
        # Compact replies all carry sequence zero. Use a separate UDP endpoint so
        # a late reply to an earlier exchange on the main connection cannot match.
        with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as transport:
            transport.settimeout(self.socket.gettimeout());transport.connect(self.socket.getpeername())
            return self._exchange(transport,cmd,None,0)

    def _exchange(self,transport,cmd,epoch,seq,train_seconds=0.):
        try:transport.send(cmd)
        except OSError:return dict(outcome="no_confirmed_receipt",sequence=seq)
        # An unconfirmed pulse is never resent. Delayed earlier receipts are discarded.
        timeout=transport.gettimeout()
        deadline=time.monotonic()+timeout+train_seconds
        try:
            while True:
                remaining=deadline-time.monotonic()
                if remaining<=0:break
                transport.settimeout(remaining)
                try:return receipt(transport.recv(512),self.path,epoch,seq,train_reply=train_seconds>0)
                except OSError:break
                except (ValueError,struct.error,UnicodeError):continue
        finally:
            transport.settimeout(timeout)
        return dict(outcome="no_confirmed_receipt",sequence=seq)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("host");p.add_argument("--unit",type=int,default=1);p.add_argument("--port",type=int,default=5054)
    action=p.add_mutually_exclusive_group()
    action.add_argument("--status",action="store_true");action.add_argument("--configure",action="store_true")
    action.add_argument("--actuate",action="store_true");action.add_argument("--dose",action="store_true")
    action.add_argument("--train",type=int,metavar="COUNT")
    p.add_argument("--duty",type=float)
    p.add_argument("--levels",type=float,nargs="+",help="one normalized power per --pixels entry")
    p.add_argument("--wires",type=int,choices=(2,3,4));p.add_argument("--limit",type=float)
    p.add_argument("--guard",choices=("on","off"));p.add_argument("--max-age-ms",type=int)
    p.add_argument("--mode",choices=MODES);scale=p.add_mutually_exclusive_group();scale.add_argument("--level",type=float);scale.add_argument("--watts",type=float)
    p.add_argument("--ms",type=float,default=20);p.add_argument("--pixels",type=int,nargs="+",default=[21,22])
    p.add_argument("--raw",action="store_true",help="send a plain OSC message; full-power actuation requires guard off")
    a=p.parse_args()
    changes={key:value for key,value in (("wires",a.wires),("limit",a.limit),("mode",a.mode),("guard",a.guard),("max_age_ms",a.max_age_ms)) if value is not None}
    if a.configure and len(changes)!=1 and set(changes)!={"wires","limit","mode"}:
        p.error("--configure accepts one setting or the complete --wires --limit --mode group")
    if not a.configure and changes:p.error("use --configure to change settings")
    if (a.watts is not None or a.level is not None) and (a.configure or a.actuate or a.status):p.error("power applies only to a calibrated dose")
    if a.raw and (a.configure or a.status):p.error("--raw applies to actuation and calibrated doses")
    if a.train is not None:
        if a.duty is None or a.raw or a.watts is not None:p.error("--train requires --duty and guarded normalized levels")
    elif a.duty is not None:p.error("--duty requires --train")
    if a.levels is not None and (a.raw or a.actuate or a.status or a.configure or a.level is not None or a.watts is not None or len(a.levels)!=len(a.pixels) or len(set(a.pixels))!=len(a.pixels)):
        p.error("--levels requires one value per distinct pixel and a calibrated command")
    r=Client(a.host,a.unit,a.port)
    try:
        if a.status:result=r.status()
        elif a.configure:
            if len(changes)==3:result=r.configure(a.wires,a.limit,a.mode)
            else:
                name,value=next(iter(changes.items()))
                result=getattr(r,"set_"+name)(value=="on" if name=="guard" else value)
        elif a.train is not None or a.levels is not None:
            if len(set(a.pixels))!=len(a.pixels):p.error("duplicate pixel")
            levels=dict(zip(a.pixels,a.levels if a.levels is not None else [a.level if a.level is not None else .5]*len(a.pixels)))
            result=r.train(a.train,a.ms,a.duty,levels) if a.train is not None else r.pattern(a.ms,levels)
        elif a.actuate:result=r.actuate(a.ms,a.pixels,raw=a.raw)
        else:
            level=a.watts/FULL_SCALE_W if a.watts is not None else (.5 if a.level is None else a.level)
            result=r.command(level,a.ms,a.pixels,raw=a.raw)
        print(json.dumps(result,indent=2))
    finally:r.close()
