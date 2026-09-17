from c_ort import *
import numpy as np, sys
def veri(pp, pencereler):
    v=yukle(pp); X=[]
    B={round(d['t'],2):d for d in v['BAT']}
    for a,b in pencereler:
        for d in pen(v,"RCOU",a,b):
            bb=B.get(round(d['t'],2))
            if not bb: continue
            M=(d['C11'],d['C10'],d['C12'],d['C9'])
            X.append((d['t'], sum(max(0,(m-1150)/800)**3 for m in M), bb['Curr'], bb['Volt'], max(M), sorted(M)[2]))
    return np.array(X)
# ucus penceresi: NOT_LANDED sonrasi, olay oncesi
A=veri("c.pkl",[(54.4,61.4),(75.6,79.9),(140.9,147.5),(188.4,202.37)])
B=veri("c0020.pkl",[(617.5,648.2)])
for ad,X in (("02:50 normal ucus",A),("00:20 u3 carpma oncesi",B)):
    s=X[:,1]; I=X[:,2]
    k=np.sum(s*I)/np.sum(s*s)
    print(ad, "n",len(X), "sum_a3 aralik %.2f-%.2f"%(s.min(),s.max()), "I aralik %.1f-%.1f"%(I.min(),I.max()), "k(A/birim a3, orijinden) %.1f"%k)
    for lo,hi in ((0,0.5),(0.5,0.7),(0.7,0.9),(0.9,1.1),(1.1,1.5),(1.5,3)):
        m=(s>=lo)&(s<hi)
        if m.sum(): print("   sum_a3 [%.1f,%.1f) n %d I ort %.1f min %.1f max %.1f | maxPWM ort %.0f"%(lo,hi,m.sum(),I[m].mean(),I[m].min(),I[m].max(),X[m,4].mean()))
