# -*- coding: utf-8 -*-
"""T150 (2) — arena figurundeki HB neden bulunamiyor: RENK mi SEKIL mi?"""
import os, sys, json
import numpy as np, cv2
KOK = r"O:\navitas"; sys.path.insert(0, os.path.join(KOK, "codes"))
from karar_sozlesmesi import BARIYER_KROMA_ESIGI, HB_ASGARI_ALAN_ORANI
p = os.path.join(KOK, "data", "arena_referans", "sartname_s9_arena.png")
im = cv2.imread(p, cv2.IMREAD_COLOR); h, w = im.shape[:2]
lab = cv2.cvtColor(im, cv2.COLOR_BGR2LAB)
a = lab[:, :, 1].astype(np.int16) - 128
# H pedi kabaca (gozle okundu, bindirmeden): x 325..400, y 118..178
x0, y0, x1, y1 = 325, 118, 400, 178
ped = a[y0:y1, x0:x1]
kirmizi_tum = int((a > BARIYER_KROMA_ESIGI).sum())
bgr = im[y0:y1, x0:x1].reshape(-1, 3)
d = {"figur_boyut": [h, w], "BARIYER_KROMA_ESIGI": BARIYER_KROMA_ESIGI,
     "ped_penceresi": [x0, y0, x1-x0, y1-y0],
     "ped_a_yildiz": {"min": int(ped.min()), "medyan": float(np.median(ped)),
                      "maks": int(ped.max()), "ort": round(float(ped.mean()), 2)},
     "ped_esigi_gecen_px": int((ped > BARIYER_KROMA_ESIGI).sum()),
     "ped_px_toplam": int(ped.size),
     "ped_BGR_ortalama": [round(float(v), 1) for v in bgr.mean(axis=0)],
     "karede_esigi_gecen_toplam_kirmizi_px": kirmizi_tum,
     "asgari_alan_px": round(HB_ASGARI_ALAN_ORANI * w * h, 1)}
# bariyer (kirmizi-beyaz) referans olarak: figurun bariyer bandi y 200..230
bx0, by0, bx1, by1 = 470, 200, 900, 232
bar = a[by0:by1, bx0:bx1]
d["bariyer_penceresi_a_yildiz_maks"] = int(bar.max())
d["bariyer_penceresi_esigi_gecen_px"] = int((bar > BARIYER_KROMA_ESIGI).sum())
print(json.dumps(d, ensure_ascii=False, indent=1))
json.dump(d, open(os.path.join(KOK, "results", "t150", "tani_arena_figuru.json"),
                  "w", encoding="utf-8"), ensure_ascii=False, indent=1)
im2 = im.copy()
cv2.rectangle(im2, (x0, y0), (x1, y1), (0, 255, 0), 2)
cv2.rectangle(im2, (bx0, by0), (bx1, by1), (0, 200, 255), 2)
kir = ((a > BARIYER_KROMA_ESIGI).astype(np.uint8))
im2[kir > 0] = (0.4*im2[kir > 0] + 0.6*np.array([255, 0, 255])).astype(np.uint8)
cv2.imwrite(os.path.join(KOK, "results", "t150", "bindirme",
                         "arena_figuru_kroma_tani.jpg"), im2)
