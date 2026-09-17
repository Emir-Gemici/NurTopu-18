from c_ort import *
import numpy as np
v=yukle()
for d in pen(v,"IMU",79.25,79.65):
    ac=[d[k] for k in ("AccX","AccY","AccZ")]; print(f"IMU {d['t']:.3f} I{d['I']} |a| {math.sqrt(sum(x*x for x in ac)):.1f}")
for d in pen(v,"VIBE",79.2,79.7): print(f"VIBE {d['t']:.2f} IMU{d['IMU']} VZ {d['VibeZ']:.1f} Clip {d['Clip']}")
for d in pen(v,"CTUN",79.0,79.9): print(f"CTUN {d['t']:.2f} ThO {d['ThO']:.3f} Alt {d['Alt']:.2f}")
V0=[d for d in v['VIBE'] if d['IMU']==0]
print("IMU0 Clip degisimleri:", [(round(b['t'],2),a['Clip'],b['Clip']) for a,b in zip(V0[:-1],V0[1:]) if b['Clip']!=a['Clip']][:6])
V1=[d for d in v['VIBE'] if d['IMU']==1]
print("IMU1 Clip degisimleri:", [(round(b['t'],2),a['Clip'],b['Clip']) for a,b in zip(V1[:-1],V1[1:]) if b['Clip']!=a['Clip']][:6])
