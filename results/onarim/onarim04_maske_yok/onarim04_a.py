"""ONARIM-04 deney A: ayni kareler dogrudan (dosyadan) run_camera ile ayni on-isleme/maske yoluyla."""
import glob, json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path.home() / "navitas" / "codes"))
import cv2, numpy as np
import rpi_inference as ri
dizin = sys.argv[1]; cikti = sys.argv[2]
model, yol, _ = ri.load_model(None, kayit_zorunlu=True, ayrinti=True)
satirlar = []
for f in sorted(glob.glob(dizin + "/*.jpg")):
    frame = cv2.imread(f)
    sq, small, icerik = ri._preprocess(frame)
    h, w = sq.shape[:2]
    r = model.predict(small, imgsz=ri.INFER_SIZE, conf=0.30, verbose=False)
    m = ri._maskeleri_icerige_kirp(ri.get_masks(r, h, w), icerik)
    n_kutu = 0 if r[0].boxes is None else len(r[0].boxes)
    siniflar = [] if r[0].boxes is None else [int(c) for c in r[0].boxes.cls]
    satirlar.append({"dosya": Path(f).name, "kare_hw": list(frame.shape[:2]), "maske_hw": [h, w],
                     "zemin_px": int(np.count_nonzero(m[0])), "engel_px": int(np.count_nonzero(m[1])),
                     "n_tespit": n_kutu, "siniflar": siniflar})
Path(cikti).write_text("\n".join(json.dumps(s) for s in satirlar) + "\n")
print("model", yol.name, "kare", len(satirlar))
