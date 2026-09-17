import glob, json
from pathlib import Path
import cv2, numpy as np
def keskinlik(img):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    s = 640.0 / max(g.shape)
    g = cv2.resize(g, (round(g.shape[1] * s), round(g.shape[0] * s)), interpolation=cv2.INTER_AREA)
    return float(cv2.Laplacian(g, cv2.CV_64F).var())
dji = sorted(glob.glob(str(Path.home() / "navitas/data/dji_gunduz_1280/*.jpg")))
wa = sorted(glob.glob(str(Path.home() / "navitas/data/raw_frames/*/*.jpg")))
out = {}
for ad, liste in (("dji", dji), ("whatsapp", wa)):
    for sigma in (0, 1, 2, 3, 5, 10):
        v = []
        for f in liste:
            img = cv2.imread(f)
            if sigma: img = cv2.GaussianBlur(img, (0, 0), sigma)
            v.append(keskinlik(img))
        out[f"{ad}_s{sigma}"] = {"n": len(v), "min": round(min(v), 1), "medyan": round(float(np.median(v)), 1), "max": round(max(v), 1)}
for f in sorted(glob.glob("/tmp/onarim04_imx477/*")):
    img = cv2.imread(f)
    if img is not None: out[Path(f).name] = round(keskinlik(img), 1)
print(json.dumps(out, indent=0))
