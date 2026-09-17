from c_ort import *
import numpy as np
v=yukle()
def ozet(a,b,ad):
    C=pen(v,"CTUN",a,b); B=pen(v,"BARO",a,b); G=pen(v,"GPS",a,b); X=pen(v,"XKF1",a,b,C=0)
    f=lambda L,k: (round(float(np.mean([d[k] for d in L])),2), round(min(d[k] for d in L),2), round(max(d[k] for d in L),2), len(L)) if L else None
    print(ad, a, b, "CTUN.Alt", f(C,"Alt"), "CTUN.BAlt", f(C,"BAlt"), "BARO.Alt", f(B,"Alt"), "GPS.Alt", f(G,"Alt"), "XKF1.PD", f(X,"PD"))
ozet(49.5,54.3,"yer1(arm, NOT_LANDED 54.3 once)")
ozet(66.0,75.5,"yer2 (NOT_LANDED 75.53 once)")
ozet(79.95,80.17,"W2 inis sonu")
ozet(113.3,118.1,"yer3")
ozet(120.5,124.2,"yer4")
ozet(134.2,140.8,"yer5 (NOT_LANDED 140.87 once)")
ozet(143.9,146.9,"W5 aski")
ozet(150.2,150.6,"W5 inis sonrasi yerde")
ozet(181.7,188.2,"yer6 son ucus oncesi (NOT_LANDED 188.3)")
ozet(196.0,202.37,"son ucus aski")
ozet(203.3,203.95,"cakilma sonrasi yerde (pervane akisi)")
# son ucus oncesi takeoff aninin detayi
for d in pen(v,"CTUN",186.5,190.5): print(f"CTUN {d['t']:.2f} ThO {d['ThO']:.3f} Alt {d['Alt']:.2f} BAlt {d['BAlt']:.2f} DAlt {d['DAlt']:.2f} CRt {d['CRt']:.0f}")
