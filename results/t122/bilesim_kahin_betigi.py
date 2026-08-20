"""v5c ile 71+watershed'in BILESIMI: zemin = v5c-zemin ∩ 71ws-zemin (fail-safe)."""
import importlib.util, io, json, sys
from pathlib import Path
import cv2, numpy as np
KOK = Path(r"O:\navitas")
for p in (KOK/"scripts", KOK/"codes"):
    sys.path.insert(0, str(p))
from copy_paste_augmentation import zemin_ve_mevcut_engel
from ultralytics import YOLO
def yukle(ad, dosya):
    s = importlib.util.spec_from_file_location(ad, KOK/"scripts"/"olcum"/dosya)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
D110 = yukle("d110", "110_t122_golge_kurali_denemesi.py")
D111 = yukle("d111", "111_t122_cati_buyutme_denemesi.py")
CATI = KOK/"results/t121/cati_maskeleri"; KARE = KOK/"data/raw_frames"
model = YOLO(str(KOK/"models/aday_v5c_m640.pt"), task="segment")
satirlar = []
for cp in sorted(CATI.glob("*.png")):
    ham = cv2.imread(str(cp), 0); cati = ((ham[:,:,0] if ham.ndim==3 else ham) > 127)
    if not cati.any(): continue
    v, k = cp.stem.split("__"); img = cv2.imread(str(KARE/f"{v}/{k}.jpg"))
    z5c, _ = zemin_ve_mevcut_engel(model, img, 0.30)
    z5c = z5c.astype(bool)
    bitki, yapi, _ = D110.bitki_ve_yapi(img)
    ws = D111.watershed_buyut(img, yapi)
    engel71 = ((bitki | yapi) > 0) | (ws > 0)
    z71 = ~engel71
    bilesim = z5c & z71
    dis = ~cati
    satirlar.append({
        "kare": f"{v}/{k}",
        "v5c_kacak": float((z5c & cati).sum()/cati.sum()),
        "71ws_kacak": float((z71 & cati).sum()/cati.sum()),
        "BILESIM_kacak": float((bilesim & cati).sum()/cati.sum()),
        "v5c_disi_engel": float((~z5c & dis).sum()/dis.sum()),
        "71ws_disi_engel": float((~z71 & dis).sum()/dis.sum()),
        "BILESIM_disi_engel": float((~bilesim & dis).sum()/dis.sum()),
    })
def o(k): return round(float(np.mean([s[k] for s in satirlar])), 4)
ozet = {"n": len(satirlar),
        "KACAK": {"v5c": o("v5c_kacak"), "71+ws": o("71ws_kacak"), "BILESIM": o("BILESIM_kacak")},
        "CATI_DISI_ENGEL": {"v5c": o("v5c_disi_engel"), "71+ws": o("71ws_disi_engel"), "BILESIM": o("BILESIM_disi_engel")}}
io.open(KOK/"results/t122/bilesim_kahin.json","w",encoding="utf-8").write(json.dumps({**ozet,"kayitlar":satirlar}, ensure_ascii=False, indent=1))
print(json.dumps(ozet, ensure_ascii=False, indent=1))
