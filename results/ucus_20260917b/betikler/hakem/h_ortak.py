import pickle
def yukle(p):
    with open(p,"rb") as f: return pickle.load(f)
def parm(v):
    P={}
    for d in v["PARM"]: P[d["Name"]]=d["Value"]
    return P
def pen(v,tip,t0,t1,I=None):
    return [d for d in v.get(tip,[]) if t0<=d["t"]<=t1 and (I is None or d.get("I")==I)]
