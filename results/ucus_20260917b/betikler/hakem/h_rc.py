from h_ortak import *
v=yukle("ha.pkl")
import numpy as np
R=pen(v,"RCIN",624,631.9); print("00:20 624-631.9 C1..C4 min/max", [(min(d[c] for d in R),max(d[c] for d in R)) for c in ("C1","C2","C3","C4")])
C=pen(v,"CTUN",624,631.9); print(" Alt", round(min(d['Alt'] for d in C),2), round(max(d['Alt'] for d in C),2), "ThO ort", round(np.mean([d['ThO'] for d in C]),3))
w=yukle("hb.pkl"); C=pen(w,"CTUN",143.9,146.9); R=pen(w,"RCIN",143.9,146.9)
print("02:50 143.9-146.9 C1..C4", [(min(d[c] for d in R),max(d[c] for d in R)) for c in ("C1","C2","C3","C4")], "Alt", round(min(d['Alt'] for d in C),2), round(max(d['Alt'] for d in C),2), "ThO", round(np.mean([d['ThO'] for d in C]),3), "CRt ort", round(np.mean([d['CRt'] for d in C]),1))
C=pen(w,"CTUN",192.5,202.37); print("02:50 192.5-202.37 Alt", round(min(d['Alt'] for d in C),2), round(max(d['Alt'] for d in C),2), "ThO ilk/son 1s", round(np.mean([d['ThO'] for d in C if d['t']<193.5]),3), round(np.mean([d['ThO'] for d in C if d['t']>201.37]),3))
