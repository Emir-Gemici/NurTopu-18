from h_ortak import *
import numpy as np
v=yukle("hb.pkl")
P=pen(v,"POWR",188.4,202.37); print("POWR Vcc", round(min(d['Vcc'] for d in P),3), round(max(d['Vcc'] for d in P),3), "VServo", round(min(d['VServo'] for d in P),3), round(max(d['VServo'] for d in P),3), "Flags", sorted(set(d['Flags'] for d in P)), "AccFlags", sorted(set(d['AccFlags'] for d in P)))
B=pen(v,"BAT",188.4,202.37); print("BAT V", round(min(d['Volt'] for d in B),2), round(max(d['Volt'] for d in B),2), "I", round(min(d['Curr'] for d in B),1), round(max(d['Curr'] for d in B),1))
R=pen(v,"RCIN",181.7,204.0); dt=np.diff([d['t'] for d in R]); print("RCIN dt max", round(dt.max(),3), "C3 min", min(d['C3'] for d in R), "C4 min/max", min(d['C4'] for d in R), max(d['C4'] for d in R))
R=pen(v,"RCOU",188.4,202.37); print("RCOU 188.4-202.37 min/max her motor", {k:(min(d[c] for d in R),max(d[c] for d in R)) for k,c in (("M1","C11"),("M2","C10"),("M3","C12"),("M4","C9"))})
I=[d for d in pen(v,"IMU",190,202.30) if d['I']==0]; import math
gz=[math.degrees(d['GyrZ']) for d in I]; print("GyrZ 190-202.30 min/max/std", round(min(gz),1), round(max(gz),1), round(float(np.std(gz)),1))
