"""T144 OLCUM (salt okuma): rescuenet_ham TAM kume — len(l) vs ALAN sirali kirpma.
Maske 512x512'ye NEAREST ile kucultulur (betigin HF girdisiyle ayni cozunurluk).
Cikti: results/t144/olcum_kirpma.json"""
import glob
import json
import os
import sys
import time

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from dataset import download_and_convert as D  # noqa: E402

KOK = r"O:\navitas\dataset\rescuenet_ham"
BOLUM = {"train": "segmentation-trainset/train-label-img",
         "val": "segmentation-validationset/val-label-img",
         "test": "segmentation-testset/test-label-img"}
TAVAN = {"road": D.MAX_POLYGONS, "blocked": D.MAX_POLYGONS // 2}
sonuc = {}
t0 = time.time()
for bolum, alt in BOLUM.items():
    fs = sorted(glob.glob(os.path.join(KOK, alt, "*.png")))
    s = {"maske": len(fs)}
    for k in TAVAN:
        s[k] = {"asan": 0, "toplam_alan_asan": 0.0, "atilan_len": 0.0, "atilan_alan": 0.0,
                "etiket_degisen": 0, "en_kotu": None, "asanlar": []}
    for f in fs:
        lbl = cv2.imread(f, 0)
        lbl = cv2.resize(lbl, (D.IMG_SIZE, D.IMG_SIZE), interpolation=cv2.INTER_NEAREST)
        for k, ham in (("road", D.TRAVERSABLE_HAM), ("blocked", D.BLOCKED_HAM)):
            m = np.isin(lbl, sorted(ham)).astype(np.uint8)
            lines = D.mask_to_yolo_polygons(m, 0 if k == "road" else 1)
            tv = TAVAN[k]
            if len(lines) <= tv:
                continue
            alan = {l: D.poligon_alani(l) for l in lines}
            top = sum(alan.values())
            eski = sorted(lines, key=len, reverse=True)[:tv]
            yeni, kayit = D.alana_gore_kirp(lines, tv)
            at_e = top - sum(alan[l] for l in eski)
            at_y = kayit["atilan_alan"]
            r = s[k]
            r["asan"] += 1
            r["toplam_alan_asan"] += top
            r["atilan_len"] += at_e
            r["atilan_alan"] += at_y
            if set(eski) != set(yeni):
                r["etiket_degisen"] += 1
            r["asanlar"].append({
                "dosya": os.path.basename(f), "n": len(lines), "toplam": top,
                "atilan_len": at_e, "atilan_alan": at_y,
                "atilan_en_buyuk_len": max((alan[l] for l in lines if l not in eski), default=0),
                "tutulan_en_kucuk_len": min(alan[l] for l in eski)})
            if r["en_kotu"] is None or at_e / top > r["en_kotu"]["oran"]:
                r["en_kotu"] = {"dosya": os.path.basename(f), "oran": at_e / top,
                                "toplam": top, "atilan_len": at_e, "atilan_alan": at_y}
    for k in TAVAN:
        r = s[k]
        T = r["toplam_alan_asan"]
        r["atilan_len_oran"] = r["atilan_len"] / T if T else 0.0
        r["atilan_alan_oran"] = r["atilan_alan"] / T if T else 0.0
        r["ters_sira_sayisi"] = sum(1 for a in r["asanlar"]
                                    if a["atilan_en_buyuk_len"] > a["tutulan_en_kucuk_len"])
    sonuc[bolum] = s
    print(bolum, {k: (s[k]["asan"], s[k]["etiket_degisen"], round(s[k]["atilan_len_oran"], 4),
                      round(s[k]["atilan_alan_oran"], 4), s[k]["en_kotu"]) for k in TAVAN}, flush=True)
sonuc["_sure_sn"] = time.time() - t0
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "olcum_kirpma.json"), "w",
          encoding="utf-8") as fh:
    json.dump(sonuc, fh, indent=1, ensure_ascii=False)
