from c_ort import *
import numpy as np, sys
v=yukle(); a,b,st=float(sys.argv[1]),float(sys.argv[2]),float(sys.argv[3])
N={round(d['t'],1):d for d in v['PSCN']}; E={round(d['t'],1):d for d in v['PSCE']}
RC={round(d['t'],1):d for d in v['RCIN']}; AT={round(d['t'],1):d for d in v['ATT']}; C={round(d['t'],1):d for d in v['CTUN']}
print("t | C1 C2 C3 C4 | DesR R DesP P Yaw | PN PE VN VE | hiz_govde_ileri hiz_govde_sag | Alt")
t=a
while t<=b+1e-9:
    k=round(t,1); n=N.get(k); e=E.get(k); r=RC.get(k); at=AT.get(k); c=C.get(k)
    if n and e and at and r:
        psi=math.radians(at['Yaw']); vf=n['VN']*math.cos(psi)+e['VE']*math.sin(psi); vr=-n['VN']*math.sin(psi)+e['VE']*math.cos(psi)
        print(f"{t:.1f} | {r['C1']} {r['C2']} {r['C3']} {r['C4']} | {at['DesRoll']:5.1f} {at['Roll']:5.1f} {at['DesPitch']:5.1f} {at['Pitch']:5.1f} {at['Yaw']:5.1f} | {n['PN']:6.2f} {e['PE']:6.2f} {n['VN']:5.2f} {e['VE']:5.2f} | {vf:5.2f} {vr:5.2f} | {c['Alt'] if c else float('nan'):.2f}")
    t+=st
n0=[d for d in v['PSCN'] if abs(d['t']-188.3)<0.06]; e0=[d for d in v['PSCE'] if abs(d['t']-188.3)<0.06]
n1=[d for d in v['PSCN'] if abs(d['t']-202.37)<0.02]; e1=[d for d in v['PSCE'] if abs(d['t']-202.37)<0.02]
print("kalkis konumu", n0[0]['PN'] if n0 else None, e0[0]['PE'] if e0 else None, "olay oncesi", n1[0]['PN'], e1[0]['PE'])
