from c_ort import *
import sys
v=yukle(sys.argv[1]); a,b=float(sys.argv[2]),float(sys.argv[3])
B={round(d['t'],1):d for d in pen(v,"BAT",a,b)}
RC={round(d['t'],1):d for d in pen(v,"RCIN",a,b)}
AT={round(d['t'],1):d for d in pen(v,"ATT",a,b)}
def T(p): x=max(0.0,(p-1150)/800.0); return 0.35*x+0.65*x*x
for d in pen(v,"RCOU",a,b):
    k=round(d['t'],1); bb=B.get(k); r=RC.get(k); at=AT.get(k)
    M=(d['C11'],d['C10'],d['C12'],d['C9'])
    p3=sum(max(0,(m-1150)/800)**3 for m in M)
    print(f"{d['t']:.2f} M1 {M[0]} M2 {M[1]} M3 {M[2]} M4 {M[3]} sum_a3 {p3:.2f} | I {bb['Curr'] if bb else '-'} V {bb['Volt'] if bb else '-'} | C5 {r['C5'] if r else '-'} C6 {r['C6'] if r else '-'} | R {at['Roll'] if at else '-'} P {at['Pitch'] if at else '-'}")
