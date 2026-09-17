import pickle, bisect, sys
v = pickle.load(open("tum.pkl","rb"))
def filt(tip, I=None, C=None):
    L = v[tip]
    if I is not None: L = [(t,d) for t,d in L if d.get("I",0)==I]
    if C is not None: L = [(t,d) for t,d in L if d.get("C",0)==C]
    return L
S = {k: filt(k) for k in ["CTUN","PSCN","PSCE","PSCD","RCIN","ATT","RCOU","POS","GPS","RATE"]}
S["XKF1"] = filt("XKF1", C=0); S["BARO"]=filt("BARO", I=0)
T = {k: [t for t,_ in L] for k,L in S.items()}
def al(k, t, f):
    i = bisect.bisect_right(T[k], t)-1
    if i<0: return None
    return S[k][i][1].get(f)
a, b, st = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3])
t = a
print("t     | Alt  BAlt DAlt | K1PN  K1PE  K1PD  K1VN K1VE K1VD | TPN   PN    TPE   PE   TPD  PD  | VN   VE  TVN  TVE | C1   C2   C3   C4 | DR   R    DP   P   DY  Y | M4  M2  M1  M3 | GPSspd")
def g(x,n=2):
    return "  -" if x is None else f"{x:.{n}f}"
while t <= b+1e-9:
    print(f"{t:6.2f}| {g(al('CTUN',t,'Alt'))} {g(al('CTUN',t,'BAlt'))} {g(al('CTUN',t,'DAlt'))} | {g(al('XKF1',t,'PN'))} {g(al('XKF1',t,'PE'))} {g(al('XKF1',t,'PD'))} {g(al('XKF1',t,'VN'))} {g(al('XKF1',t,'VE'))} {g(al('XKF1',t,'VD'))} | "
          f"{g(al('PSCN',t,'TPN'))} {g(al('PSCN',t,'PN'))} {g(al('PSCE',t,'TPE'))} {g(al('PSCE',t,'PE'))} {g(al('PSCD',t,'TPD'))} {g(al('PSCD',t,'PD'))} | {g(al('PSCN',t,'VN'))} {g(al('PSCE',t,'VE'))} {g(al('PSCN',t,'TVN'))} {g(al('PSCE',t,'TVE'))} | "
          f"{al('RCIN',t,'C1')} {al('RCIN',t,'C2')} {al('RCIN',t,'C3')} {al('RCIN',t,'C4')} | {g(al('ATT',t,'DesRoll'),1)} {g(al('ATT',t,'Roll'),1)} {g(al('ATT',t,'DesPitch'),1)} {g(al('ATT',t,'Pitch'),1)} {g(al('ATT',t,'DesYaw'),0)} {g(al('ATT',t,'Yaw'),0)} | "
          f"{al('RCOU',t,'C9')} {al('RCOU',t,'C10')} {al('RCOU',t,'C11')} {al('RCOU',t,'C12')} | {g(al('GPS',t,'Spd'))}")
    t = round(t+st, 6)
