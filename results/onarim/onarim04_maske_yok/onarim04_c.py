"""ONARIM-04 deney C: bilinen iyi karelere kontrollu bozulma (bulaniklik) + gercek IMX477 kareleri."""
import glob, json, sys
from pathlib import Path
sys.path.insert(0, str(Path.home() / "navitas" / "codes"))
import cv2, numpy as np
import rpi_inference as ri
model, _, _ = ri.load_model(None, kayit_zorunlu=True, ayrinti=True)

def olc(frame):
    sq, small, icerik = ri._preprocess(frame)
    h, w = sq.shape[:2]
    r = model.predict(small, imgsz=ri.INFER_SIZE, conf=0.30, verbose=False)
    m = ri._maskeleri_icerige_kirp(ri.get_masks(r, h, w), icerik)
    ic = frame.shape[0] * frame.shape[1] * (w / frame.shape[1]) ** 2
    return 100 * np.count_nonzero(m[0]) / ic, 100 * np.count_nonzero(m[1]) / ic

dji = sorted(glob.glob(str(Path.home() / "navitas/data/dji_gunduz_1280/*.jpg")))
sonuc = {}
for sigma in (0, 2, 5, 10, 20, 40):
    z = e = n0 = 0
    for f in dji:
        img = cv2.imread(f)
        if sigma:
            img = cv2.GaussianBlur(img, (0, 0), sigma)
        zp, ep = olc(img); z += zp; e += ep; n0 += zp > 0
    sonuc[f"dji_blur_sigma{sigma}"] = {"kare": len(dji), "zemin>0": n0, "zemin_ort%": round(z / len(dji), 1), "engel_ort%": round(e / len(dji), 1)}
for f in sorted(glob.glob("/tmp/onarim04_imx477/*")):
    img = cv2.imread(f)
    if img is None:
        continue
    zp, ep = olc(img)
    sonuc["imx477_" + Path(f).name] = {"hw": list(img.shape[:2]), "zemin%": round(zp, 1), "engel%": round(ep, 1)}
print(json.dumps(sonuc, indent=1))
