import pickle, math
def yukle(p="c.pkl"):
    with open(p,"rb") as f: return pickle.load(f)
def P(v): return {d["Name"]:d["Value"] for d in v["PARM"]}
def pen(v,tip,a,b,**kw):
    return [d for d in v.get(tip,[]) if d["t"] is not None and a<=d["t"]<=b and all(d.get(k)==x for k,x in kw.items())]
