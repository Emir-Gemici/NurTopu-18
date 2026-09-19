"""Askı eğimi ölçer (D-505 ek 3): ThO>0,25 dönemlerinde DesRoll/DesPitch ortalaması,
dünya çerçevesine çevrilmiş eğim vektörü, RCOU yayılımı, yerde okunan roll/pitch."""
import sys, math, statistics as st
from pymavlink import mavutil
def calis(yol):
    m=mavutil.mavlink_connection(yol); t0=None; att=[]; ctun=[]; rcou=[]; p={}
    while True:
        x=m.recv_match(blocking=False)
        if x is None: break
        t=x.get_type()
        if t=='PARM': p[x.Name]=x.Value; continue
        ts=getattr(x,'TimeUS',None)
        if ts is None: continue
        t0=ts if t0 is None else t0; s=(ts-t0)/1e6
        if t=='ATT': att.append((s,x.Roll,x.Pitch,x.Yaw,x.DesRoll,x.DesPitch))
        elif t=='CTUN': ctun.append((s,x.ThO,x.Alt))
        elif t=='RCOU': rcou.append((s,x.C1,x.C2,x.C3,x.C4))
    hucre = "4S" if p.get('BATT_ARM_VOLT',0)>13 or p.get('MOT_BAT_VOLT_MAX',0)>15 else "3S/?"
    print(f"## {yol.split('/')[-1]}  süre {ctun[-1][0]:.0f} s  {hucre}  AHRS_TRIM {math.degrees(p.get('AHRS_TRIM_X',0)):+.2f}/{math.degrees(p.get('AHRS_TRIM_Y',0)):+.2f}°  ThH {p.get('MOT_THST_HOVER',0):.3f}")
    hi=[q for q in ctun if q[1]>0.25]; seg=[]
    if hi:
        a0=hi[0][0]; prev=a0
        for q in hi[1:]:
            if q[0]-prev>2: seg.append((a0,prev)); a0=q[0]
            prev=q[0]
        seg.append((a0,prev))
    for a,b in seg:
        if b-a<8: continue
        w=[q for q in att if a+3<=q[0]<=b-1]; c=[q for q in ctun if a<=q[0]<=b]
        if len(w)<30: continue
        dr=st.mean(q[4] for q in w); dp=st.mean(q[5] for q in w); yaw=st.mean(q[3] for q in w); yr=math.radians(yaw)
        fwd=-dp; right=dr; n=fwd*math.cos(yr)-right*math.sin(yr); e=fwd*math.sin(yr)+right*math.cos(yr)
        rc=[q for q in rcou if a<=q[0]<=b]; mm=[round(st.mean(col)) for col in zip(*[q[1:] for q in rc])] if rc else []
        print(f"   {a:6.1f}-{b:6.1f} s ({b-a:3.0f} s) alt ort {st.mean(q[2] for q in c):4.2f} maks {max(q[2] for q in c):4.2f} · DesRoll {dr:+5.2f}° DesPitch {dp:+5.2f}° yaw {yaw:4.0f}° → dünya |{math.hypot(n,e):.2f}°| yön {math.degrees(math.atan2(e,n))%360:3.0f}° · RCOU {mm} yayılım {max(mm)-min(mm) if mm else '-'}")
    gnd=[q for q in att if q[0]<8]
    if gnd: print(f"   yerde (ilk 8 s) roll {st.mean(q[1] for q in gnd):+.2f}° pitch {st.mean(q[2] for q in gnd):+.2f}°")
for yol in sys.argv[1:]: 
    try: calis(yol)
    except Exception as ex: print("HATA", yol, ex)
