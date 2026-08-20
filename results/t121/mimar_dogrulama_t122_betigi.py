# -*- coding: utf-8 -*-
"""T121 belirleyici kosum SONUCU — mimar dogrulamasi.

Betik `95_t121_kahin_sondasi.py` ile AYNI zinciri ve AYNI diskleri kullanir
(zemin_ve_mevcut_engel + results/t121/diskler.json), cunku on kayittaki BASARI
esigi (>=0,50 engel / <=0,30 zemin) v30'un O ZINCIRDE olculen 0,776/0,286
degerinden turetildi. Karsilastirma ayni zincirde olmali.

TABAN AYNI KOSUMDA olculur (v34 + v30) — bayat taban bu projede SEKIZ kez
kusur uretti (D-146/157/159/163/181/194/200/201).
"""
import io
import json
import sys
from pathlib import Path

import cv2
import numpy as np

KOK = Path("O:/navitas")
for p in (KOK / "scripts", KOK / "codes"):
    sys.path.insert(0, str(p))

from copy_paste_augmentation import zemin_ve_mevcut_engel  # noqa: E402
from ultralytics import YOLO  # noqa: E402

DISKLER = KOK / "results" / "t121" / "diskler.json"
KARE_KOKU = KOK / "data" / "raw_frames"
CONFLAR = (0.05, 0.30)

ADAYLAR = [
    ("t122ac_KAZANAN", KOK / "codes/runs/segment/t122ac_daralt_cati/weights/best.pt"),
    ("t122a", KOK / "codes/runs/segment/t122a_daralt/weights/best.pt"),
    ("v34_TABAN", KOK / "models/navitas_seg_v34_best.pt"),
    ("v30_ESIK_KAYNAGI", KOK / "models/navitas_seg_v30_best.pt"),
]


def disk_maskesi(sekil, x, y, r):
    m = np.zeros(sekil, np.uint8)
    cv2.circle(m, (int(x), int(y)), int(r), 1, -1)
    return m


cfg = json.load(io.open(DISKLER, encoding="utf-8"))
kareler = {ad: cv2.imread(str(KARE_KOKU / ad)) for ad in cfg["kareler"]}
for ad, img in kareler.items():
    if img is None:
        sys.exit("KARE OKUNAMADI: %s" % ad)

ozet = {}
tur_kirilim = {}
for etiket, yol in ADAYLAR:
    if not yol.is_file():
        sys.exit("AGIRLIK YOK: %s" % yol)
    model = YOLO(str(yol), task="segment")
    for conf in CONFLAR:
        a = ozet.setdefault("%s@%.2f" % (etiket, conf),
                            {"cz": [], "ce": [], "zz": []})
        for ad, k in cfg["kareler"].items():
            bgr = kareler[ad]
            zemin, engel = zemin_ve_mevcut_engel(model, bgr, conf)
            for x, y, r in k["cati"]:
                dm = disk_maskesi(zemin.shape, x, y, r).astype(bool)
                a["cz"].append(float(zemin[dm].mean()))
                a["ce"].append(float(engel[dm].mean()))
                if conf == 0.30:
                    t = tur_kirilim.setdefault(k["cati_turu"], {})
                    t.setdefault(etiket, []).append(float(engel[dm].mean()))
            for x, y, r in k["zemin"]:
                dm = disk_maskesi(zemin.shape, x, y, r).astype(bool)
                a["zz"].append(float(zemin[dm].mean()))
    del model

print("%-26s %11s %11s %12s" % ("model@conf", "cati->zemin", "cati->engel", "zemin->zemin"))
for k, v in ozet.items():
    print("%-26s %11.3f %11.3f %12.3f"
          % (k, np.mean(v["cz"]), np.mean(v["ce"]), np.mean(v["zz"])))

print("\nCATI TURUNE GORE cati->engel (conf 0,30):")
basliklar = [e for e, _ in ADAYLAR]
print("%-22s %s" % ("tur", " ".join("%16s" % b for b in basliklar)))
for tur, d in tur_kirilim.items():
    print("%-22s %s" % (tur, " ".join("%16.3f" % np.mean(d.get(b, [float('nan')])) for b in basliklar)))

# ON KAYIT OLCUTU (conf 0,30 uretim guveni)
a = ozet["t122ac_KAZANAN@0.30"]
ce, cz = float(np.mean(a["ce"])), float(np.mean(a["cz"]))
print("\nON KAYIT OLCUTU (results/t121_on_kayit.md):")
print("  BASARI = cati ENGEL >= 0,50  VE  cati ZEMIN <= 0,30")
print("  olculen: ENGEL %.3f (%s) · ZEMIN %.3f (%s)"
      % (ce, "TUTTU" if ce >= 0.50 else "TUTMADI",
         cz, "TUTTU" if cz <= 0.30 else "TUTMADI"))
print("  VERDIKT:", "BASARI" if (ce >= 0.50 and cz <= 0.30) else
      ("KISMEN" if (ce >= 0.50 or cz <= 0.30) else "TUTMADI"))

Path("O:/navitas/results/t121/mimar_dogrulama_t122.json").write_text(
    json.dumps({k: {kk: round(float(np.mean(vv)), 4) for kk, vv in v.items()}
                for k, v in ozet.items()}, ensure_ascii=False, indent=1),
    encoding="utf-8")
print("\nyazildi: results/t121/mimar_dogrulama_t122.json")
