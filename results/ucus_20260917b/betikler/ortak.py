import pickle, numpy as np, math
EXPO = 0.65
def yukle(p):
    return pickle.load(open(p, "rb"))
def dizi(v, tip, alanlar, filt=None):
    L = [d for d in v.get(tip, []) if (filt is None or filt(d))]
    t = np.array([d["t"] for d in L])
    return t, {a: np.array([d[a] for d in L], dtype=float) for a in alanlar}
def itki(pwm):
    a = np.clip((np.asarray(pwm, float) - 1150.0) / 800.0, 0, 1)
    return (1 - EXPO) * a + EXPO * a * a
def ornek(t_kaynak, x_kaynak, t_hedef):
    # sample-and-hold: son deger
    i = np.searchsorted(t_kaynak, t_hedef, side="right") - 1
    i = np.clip(i, 0, len(t_kaynak) - 1)
    return x_kaynak[i]
def yawfark(a, b):
    return (a - b + 180.0) % 360.0 - 180.0
