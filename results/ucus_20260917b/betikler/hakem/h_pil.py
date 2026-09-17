from h_ortak import *
import numpy as np, sys
for ad,pp in (("00:20","ha.pkl"),("02:50","hb.pkl")):
    v=yukle(pp); P=parm(v)
    print("==",ad, {k:P.get(k) for k in ("MOT_HOVER_LEARN","BATT_MONITOR","BATT_CAPACITY","MOT_THST_HOVER","PSC_ACCZ_P","PSC_ACCZ_I")})
    B=v["BAT"]; print(" BAT alanlari", list(B[0].keys()))
    # arm pencereleri
    for d in v["ARM"]: print("  ARM", round(d["t"],2), d["ArmState"], d["Method"])
    for t in [x["t"] for x in B][::max(1,len(B)//12)]:
        d=min(B,key=lambda z:abs(z["t"]-t))
        print(f"  t {d['t']:7.1f} V {d['Volt']:.2f} VR {d['VoltR']:.2f} I {d['Curr']:.1f} CurrTot {d['CurrTot']:.0f} mAh Res {d.get('Res',float('nan')):.4f} Rem {d.get('RemPct')}")
