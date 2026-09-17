from h_ortak import *
import math
v=yukle("hb.pkl")
print("-- 203.1-204.3 RCOU/BAT/RCIN C5 C6")
B={round(d['t'],1):d for d in pen(v,"BAT",203.1,204.3)}; RC={round(d['t'],1):d for d in pen(v,"RCIN",203.1,204.3)}
for d in pen(v,"RCOU",203.1,204.3):
    k=round(d['t'],1); b=B.get(k); r=RC.get(k)
    print(f"{d['t']:.2f} M1 {d['C11']} M2 {d['C10']} M3 {d['C12']} M4 {d['C9']} | I {b['Curr'] if b else '-'} V {b['Volt'] if b else '-'} | C5 {r['C5'] if r else '-'} C6 {r['C6'] if r else '-'}")
print("-- 79.2-79.7 IMU |a| ve VIBE")
for d in pen(v,"IMU",79.3,79.6):
    a=math.sqrt(d['AccX']**2+d['AccY']**2+d['AccZ']**2); print(f"{d['t']:.3f} I{d['I']} |a| {a:.1f}")
for d in pen(v,"VIBE",79.2,79.7): print(f"{d['t']:.2f} IMU{d['IMU']} VZ {d['VibeZ']:.1f} Clip {d['Clip']}")
C=pen(v,"CTUN",75.5,80.2); print("W2 ThO min/max", round(min(d['ThO'] for d in C),3), round(max(d['ThO'] for d in C),3), "Alt min/max", round(min(d['Alt'] for d in C),2), round(max(d['Alt'] for d in C),2))
import numpy as np
x=[(d['t'],d['VibeZ'],d['Clip']) for d in v['VIBE'] if d['IMU']==0 and 188.3<=d['t']<=202.37]; print("W6 VibeZ max", max(x,key=lambda z:z[1]))
print("Clip IMU0 degisimleri tum log:", [(round(b['t'],2),a['Clip'],b['Clip']) for a,b in zip([d for d in v['VIBE'] if d['IMU']==0][:-1],[d for d in v['VIBE'] if d['IMU']==0][1:]) if b['Clip']!=a['Clip']][:8])
