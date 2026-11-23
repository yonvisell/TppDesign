"""Independent nodal analysis of ten EB terminals, twelve TA electrodes and individual continuous wires."""
from pathlib import Path
from itertools import combinations
import csv, json, math
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'analysis'
ORDER=(0,1,2,5,4,3,6,7,8)
TAPS=(0,1,2,3,6,5,4,3,6,7,8,9)
D=0.000127*92**((36-48)/39)
R20=1.08e-6*.0042/(math.pi*D**2/4)
def masks():
    for n in (1,2,3):yield from combinations(range(9),n)
def selection(selected):
    levels=[0]
    for pixel in ORDER:levels.append(levels[-1]^(pixel in selected))
    return levels
def isolated(pixel):
    j=ORDER.index(pixel)+1
    s=[-1]*10;s[0]=s[j-1]=0;s[j]=1
    return s
def solve(n,states,data,R,rail=6.,hot=False,contact_fault=None):
    # Nodes 0..9 are accessible J2 terminals, then remote cable ends, bars,
    # the wire at each contact, and the post-shunt power rail.
    bus=32+12*n;g=np.zeros((bus+1,bus+1));b=np.zeros(bus+1);edges=[]
    def edge(i,j,r,kind):
        g[i,i]+=1/r
        if j>=0:
            g[j,j]+=1/r;g[i,j]-=1/r;g[j,i]-=1/r
        edges.append((i,j,r,kind))
    for j,state in enumerate(states):
        edge(j,10+j,data['wire_lead'], 'cable')
        if state==1:edge(j,bus,data['switch'][j],'switch')
        if state==0:edge(j,-1,data['switch'][j],'switch')
        edge(j,-1,data['divider_ohm'],'divider')
    for bar,j in enumerate(TAPS):
        edge(10+j,20+bar,data['bar_cu'][bar],'carrier')
        for k in range(n):
            node=32+n*bar+k
            rc=data['pickup']
            if contact_fault and (bar,k)==tuple(contact_fault[:2]):rc=contact_fault[2]
            edge(20+bar,node,rc,'contact')
            if bar%4:
                idx=3*(bar//4)+bar%4-1
                edge(node-n,node,R[idx],idx)
    g[bus,bus]+=1/data['common'];b[bus]=rail/data['common']
    v=np.linalg.solve(g,b)
    ibus=(rail-v[bus])/data['common'];p=np.zeros(9);loss=ibus**2*data['common']
    contact_w=0.
    for i,j,r,kind in edges:
        w=(v[i]-(v[j] if j>=0 else 0.0))**2/r
        if isinstance(kind,int):p[kind]+=w
        else:loss+=w
        if contact_fault and i==20+contact_fault[0] and j==32+n*contact_fault[0]+contact_fault[1]:contact_w=w
    assert abs(rail*ibus-sum(p)-loss)<2e-7
    currents=np.array([(v[bus]*s-v[j])/data['switch'][j] if s>=0 else 0. for j,s in enumerate(states)])
    return p,ibus,currents,v[:10],contact_w
def main():
    data=json.loads((OUT/'input/electrical.json').read_text());ref=R20*np.interp(25,[20,100],[1.,1.006]);result={}
    records=[]
    for n in (2,3,4):
        runs={}
        for name,rail,hot,material in [('nominal',6.,False,ref),('high',6.3,False,ref),('hot',5.7,True,R20*1.068)]:
            d=data['hot' if hot else 'nominal'];limits=[0,0,0];weak=1000.;amps=pin=idle=0
            for sites in masks():
                w,a,j,_,_=solve(n,selection(sites),d,[material]*9,rail)
                power=min(w[list(sites)]);weak=min(weak,power);amps=max(amps,a);pin=max(pin,max(abs(j)))
                idle=max(idle,max(w[i] for i in range(9) if i not in sites))
                limits[len(sites)-1]+=int(a<=8 and max(abs(j))<=5)
                if n==2:records.append([name,' '.join(f'P{i//3+1}{i%3+1}' for i in sites),power,a,max(abs(j))])
            runs[name]=dict(min_W=weak,max_bus_A=amps,max_leg_A=pin,max_idle_W=idle,within_8A_5A_by_size=limits)
        w,a,j,_,_=solve(n,selection((4,)),data['nominal'],[ref]*9)
        runs['P22']=dict(on_W=w[4],on_A=a,duty_at_4p2=4.2/w[4])
        result[str(n)]=runs
    probes=[]
    for site in range(9):
        j=ORDER.index(site)+1
        R=np.full(9,ref)
        def reading(temps,st,defect=None):
            p,a,i,v,c=solve(2,st,data['nominal'],temps,contact_fault=defect)
            wire_a=math.sqrt(p[site]/(temps[site]/2))
            return abs(v[j]-v[j-1])/a,a,wire_a,c
        cold,ii,ia,_=reading(R,isolated(site))
        R[site]=R20*1.065
        warm,_,_,_=reading(R,isolated(site))
        groups=[]
        for group in masks():
            if site not in group or len(group)==1:continue
            _,_,_,v,_=solve(2,selection(group),data['nominal'],R)
            p=solve(2,selection(group),data['nominal'],R)[0][site];branch=math.sqrt(p/(R[site]/2))
            groups.append(abs((abs(v[j]-v[j-1])/branch-(cold-ref/2))-R[site]/2))
        probes.append(dict(site=f'P{site//3+1}{site%3+1}',cold_offset_ohm=cold-ref/2,raw_current_bias_percent=(ii/ia-1)*100,
          isolated_R_error_after_subtraction_mohm=1000*(warm-cold+ref/2-R[site]/2),group_worst_R_error_with_true_branch_I_mohm=1000*max(groups)))
    contact=[]
    for rc in (.010,.1,1.,4.,10.,10000.):
        p,a,_,v,c=solve(2,isolated(0),data['nominal'],np.full(9,ref),contact_fault=(1,0,rc))
        contact.append(dict(pickup_ohm=rc,loss_W=c,shunt_A=a,terminal_V=abs(v[1]-v[0]),observed_ohm=abs(v[1]-v[0])/a))
    with (OUT/'mask-power.csv').open('w') as f:
        cw=csv.writer(f);cw.writerow(['corner','selected','lowest_NiCr_W','source_A','largest_tap_A']);cw.writerows(records)
    with (OUT/'array-results.json').open('w') as f:json.dump(dict(diameter_um=D*1e6,strand_R20_ohm=R20,conductor_counts=result,probes=probes,first_contact=contact),f,indent=2)
if __name__=='__main__':main()
