"""Recompute gas retention, interface loads and local port impedance using issued cut and pressure records."""
import math
import json
from pathlib import Path
import numpy as np
from scipy.integrate import solve_ivp
from scipy.interpolate import PchipInterpolator
from scipy.optimize import brentq
from scipy.special import jve
from geometry_check import run as read_geometry, ROOT

PA, MU, RHO, GAMMA = 101325., 1.85e-5, 1.184, 1.4
OUT = Path(__file__).resolve().parent
T0 = 298.15

def gap_conductance(n, width_um, h_um, length_mm):
    return n*width_um*1e-6*(h_um*1e-6)**3/(12*MU*length_mm*1e-3)

def decay(g, c, pg, t):
    x = math.exp(-t*g/c)
    return x/(1+pg/(2*PA)*(1-x))

def neighbor(g, c, pg, t):
    return -0.5*math.expm1(-2*t*g*(1+pg/(2*PA))/c)

def leaks(v, short_land_mm, shared_land_mm):
    # Reference volume flow at 1 atm, 25 °C. Temperature multiplies pressure change per lost mass.
    t=.055
    iso=v/PA
    hot_isochore_temperature = T0*(1+60000/PA)
    hot=iso/(GAMMA*hot_isochore_temperature/T0)
    criteria=[]
    for label,c in (("isothermal 25 C",iso),("adiabatic tangent at 25 C",iso/GAMMA),("hot adiabatic tangent",hot)):
        for pg in (5000.,20000.,40000.,60000.):
            b=pg/(2*PA); f=.95
            limit=-math.log(f*(1+b)/(1+f*b))*c/t
            criteria.append(dict(case=label,pg_kPa=pg/1000,loss_limit_percent=5,ms=t*1000,
                        G_m3_Pa_s=limit,ambient_Q_uL_s=limit*pg*(1+b)*1e9,
                        equiv_16flank_h_um=(limit/gap_conductance(16,40,1.,short_land_mm))**(1/3),
                        slip_h_um=brentq(lambda h:gap_conductance(16,40,h,short_land_mm)*(1+.6/h)-limit,.01,20)))
    scenarios=[]
    for typ,n,b,l in (("four strands; all exits, shortest land",16,40,short_land_mm),
                      ("interpixel; eight wire flanks, shared land",8,40,shared_land_mm),
                      ("single broad dry interface channel",1,500,short_land_mm)):
        for h in (1,2,3,5,10,20,32):
            g=gap_conductance(n,b,h,l)
            data=[]
            for pg in (5000.,20000.,40000.,60000.):
                for ms in (1,20,55):
                    data.append(dict(pg_kPa=pg/1000,ms=ms,ambient_loss_percent=100*(1-decay(g,hot,pg,ms/1000)),
                            equal_neighbor_fraction_percent=100*neighbor(g,hot,pg,ms/1000),
                            ambient_loss_percent_slip=100*(1-decay(g*(1+.6/h),hot,pg,ms/1000)),
                            equal_neighbor_percent_slip=100*neighbor(g*(1+.6/h),hot,pg,ms/1000)))
            scenarios.append(dict(path=typ,count=n,width_um=b,h_um=h,length_mm=l,G_m3_Pa_s=g,scenarios=data))
    return dict(volume_m3=v,reference_C_m3_Pa=iso,hot_tangent_C_m3_Pa=hot,
        temperature_of_60kPa_isochoric_charge_K=hot_isochore_temperature,practical_decay=criteria,gaps=scenarios)

def ports(geom, v, traces):
    vl=geom["lower_volume_4w_mm3"]*1e-9
    vu=v-vl
    assert min(vl,vu)>0
    rows=[]
    for name,d1,d2,e,cd in (("nominal",.425,.600,.85,.70),("low impedance",.435,.610,.60,.80),("high impedance",.415,.590,1.70,.55),("oscillatory wall sensitivity",.415,.590,1.70,.55)):
        r=np.array([d1,d2])*0.5e-3; A=np.pi*r*r; l=np.array([geom["liner_thickness_mm"],geom["roof_thickness_mm"]])*1e-3
        # Effective length interval includes short-duct end effects and uncertain stepped transition.
        m=RHO*np.sum((l+e*r)/A)
        R=8*MU/np.pi*np.sum(l/r**4)+3*MU/r[0]**3
        B=RHO/(2*cd**2*min(A)**2)
        cl,cu=vl/(GAMMA*PA),vu/(GAMMA*PA)
        cdiff=cl*cu/(cl+cu)
        f=1/(2*np.pi*np.sqrt(m*cdiff))
        steady_R = R
        if name=="oscillatory wall sensitivity":
            # Womersley tube resistance evaluated at the acoustic frequency and held constant as a drag sensitivity.
            omega=2*np.pi*f
            z=r*np.sqrt(-1j*omega*RHO/MU)
            ztube=1j*omega*RHO*l/A/(1-2*jve(1,z)/(z*jve(0,z)))
            R=float(np.real(ztube).sum())+3*MU/r[0]**3
        def evaluate(pfun,deriv,tend,maxstep,scale):
            def eq(t,y):
                delta,q=y
                return [(1+vu/vl)*deriv(t)-q/cdiff,(delta-R*q-B*q*abs(q))/m]
            sol=solve_ivp(eq,(0,tend),[0.,0.],method="LSODA",dense_output=True,max_step=maxstep,rtol=2e-6,atol=[2e-5,1e-13])
            assert sol.success
            t=np.arange(0,tend+1.e-12,min(maxstep,4e-6))
            dif,q=sol.sol(t)
            avg=pfun(t); up=avg-vl/v*dif
            # Low-Mach nonlinear resistance is only indicative for deliberately fast stress input.
            return dict(max_lower_upper_diff_kPa=float(max(abs(dif))/1e3),max_upper_deviation_kPa=float(max(abs(up-avg))/1e3),
                max_upper_deviation_pct_of_source_peak=float(100*max(abs(up-avg))/scale),
                upper_peak_kPa=float(max(up)/1000),driven_mean_peak_kPa=float(max(avg)/1000),
                peak_Mach=float(max(abs(q))/min(A)/343))
        test={}
        for case in traces:
            z=case["trace"]; ts=np.array([q["ms"] for q in z])*.001
            src=PchipInterpolator(ts,[q["gas_gauge_kPa"]*1000 for q in z])
            test[case.get("label","thermal_"+str(case["strands"])+"w")]=evaluate(src,src.derivative(),.055,8e-6,case["peak_gauge_kPa"]*1000)
        for ms,pk in ((1.,60000.),(5.,60000.),(15.,60000.),(.08,5000.)):
            duration=ms/1000
            def mean(t):
                return pk*.5*(1-np.cos(np.pi*np.minimum(t/duration,1)))
            def rate(t):
                return .5*pk*np.pi/duration*math.sin(math.pi*t/duration) if 0<t<duration else 0.
            test[f"{ms:g}ms_{pk/1000:g}kPa_halfcos"]=evaluate(mean,rate,duration+.0008,min(duration/80,5e-6),pk)
        rows.append(dict(case=name,throat_diameter_mm=d1,copper_bore_mm=d2,end_length_factor=e,Cd=cd,
            air_inertance_Pa_s2_m3=m,linear_resistance_Pa_s_m3=R,steady_resistance_Pa_s_m3=steady_R,quadratic_Pa_s2_m6=B,
            Helmholtz_frequency_kHz=f/1000,quarter_period_us=1e6/(4*f),small_signal_amplitude_tau_ms=2*m/R*1000,
            response=test))
    return dict(lower_volume_mm3=vl*1e9,upper_volume_mm3=vu*1e9,records=rows)

def loads(geom, seats):
    aperture=geom["cap_area_mm2"]
    rows=json.loads((ROOT/"supplement/controlled-gas.json").read_text())["cases"]
    r=max(rows,key=lambda o:o["sum_Fe_mN"])
    entries=[("controller_replay",r["sum_Fe_mN"]/aperture,[r["wires"],r["ceiling"],r["mode"],r["ids"]])]
    family=[]
    for path in sorted((ROOT/"supplement/envelope").glob("*-*.json")):
        rec=json.loads(path.read_text())
        if "interleave" in path.name:
            m=max(rec,key=lambda r:r["sum_Fe_mN"])
            family.append((path.stem,m["sum_Fe_mN"]/aperture,[m["n"],m["k"],m["schedule"]]))
        else:
            m=max(rec,key=lambda r:r["best"]["peak_sum_pressure_kPa"])
            family.append((path.stem,m["best"]["peak_sum_pressure_kPa"],[m["strands"],m["pixels"]]))
    entries += family+[("9_uniform_60kPa",9*60,[]),("one_60kPa",60,[])]
    records=[]
    for name,sump,ref in entries:
        face=sump*geom["diaphragm_pressure_area_mm2"]*.001
        records.append(dict(case=name,reference=ref,sum_gauge_kPa=sump,face_opening_N=face,
            gasket_opening_N=sump*geom["gasket_opening_mm2"]*.001,
            floor_opening_N=sump*geom["floor_opening_mm2"]*.001,
            face_load_if_lift_reaches_grid_aperture_N=sump*seats["grid_opening_mm2"]*.001,
            floor_plane_squeeze_and_pressure_per_screw_N_at_q0p2=(geom["floor_gasket_area_mm2"]*.20+sump*geom["floor_opening_mm2"]*.001)/geom["fastener_count"],
            face_plane_squeeze_and_pressure_per_screw_N_at_q0p2=(seats["diaphragm_to_grid_contact_area_mm2"]*.20+face)/geom["fastener_count"],
            equal_share_face_opening_N=face/geom["fastener_count"],
            equal_share_clamp_N_by_assumed_gasket_mean_MPa={str(q):(geom["gasket_land_area_mm2"]*q+face)/geom["fastener_count"] for q in (.05,.20,.50)}))
    return records

def main():
    geom=read_geometry()
    volume=geom["net_volume_mm3"]["4"]*1e-9
    traces=json.loads((ROOT/"supplement/equal-power.json").read_text())
    assert "R2L" in traces["geometry"]["basis"]
    assert abs(traces["geometry"]["gas_volumes_by_strand_count_mm3"]["4"]-volume*1e9)<.0001
    short_land=geom["gasket_outer_land_min_mm"]-.08
    shared_land=geom["gasket_adjacent_horizontal_mm"]-.08
    thermal=list(traces["cases"])
    controlled=json.loads((ROOT/"supplement/controlled-gas.json").read_text())
    for case in controlled["cases"]:
        tr=case.get("trace_ms_midpoint_C_gas_C_pressure_kPa")
        if tr:
            thermal.append(dict(strands=case["wires"],label=f'production_P22_{case["ceiling"]}C',
                peak_gauge_kPa=case["weak_kPa"],trace=[dict(ms=row[0],gas_gauge_kPa=row[3]) for row in tr]))
    seat_check=json.loads((OUT/"step-readback.json").read_text())["fasteners_and_clearance"]
    data=dict(geometry=geom,mechanical_loads=loads(geom,seat_check),leak=leaks(volume,short_land,shared_land),
              port=ports(geom,volume,thermal))
    (OUT/"seal-results.json").write_text(json.dumps(data,indent=2)+"\n")
if __name__=="__main__":
    main()
