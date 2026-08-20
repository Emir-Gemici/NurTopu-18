"""T121 adim 4 hazirlik — CATI ADAY MASKELERI (56 kaynak) + gorsel dogrulama sayfalari.

YONTEM (on kayit: results/t121_on_kayit.md):
  aday = v30_engel(conf 0.05) MINUS DOTA_arac(conf 0.25) -> close/open(15) ->
         alan >= ESIK blob'lari
  Sonra HER kare bindirme sayfasinda GOZLE dogrulanir (D-80); kirmizi kiremit
  ve v30'un kacirdigi bolgeler ELLE eklenir (ayri duzeltme dosyasi,
  results/t121/cati_duzeltmeleri.json). NIHAI OTORITE GOZDUR, v30 degil —
  dairesellik notu: v30 yalniz BASLANGIC cizimidir, kabul/ret insan(Fable 5)
  gozuyle verilir ve duzeltmeler elle poligondur.

ESIK GEREKCESI (ciplak degil): tekil arac ~28x56 px ~1.6k px (D-124: 27,8 px
= 1,8 m olcegi); en kucuk catı ornegi (kiremit, uzak kadraj) ~15k px
(results/t121/diskler.json sondalarindan). 5000 px araci eler, catiyi tutar.

CIKTI:
  results/t121/cati_aday/<kaynak>.png       (0/255 maske, kaynak cozunurlugu)
  results/t121/dogrulama_sayfa_<n>.png      (bindirmeli, 6 kare/sayfa)
  results/t121/cati_aday_ozet.json          (kare basina blob/alan dokumleri)
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import cv2
import numpy as np

KOK = Path(__file__).resolve().parents[2]
for p in (KOK / "scripts", KOK / "codes"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from copy_paste_augmentation import (  # noqa: E402
    arac_maskesi, eliptik_cekirdek, zemin_ve_mevcut_engel)
from ultralytics import YOLO  # noqa: E402

VERI = KOK / "dataset" / "copy_paste_gercek"
KARE_KOKU = KOK / "data" / "raw_frames"
CIKTI = KOK / "results" / "t121"
ALAN_ESIGI = 5000            # gerekce docstring'de (D-124 arac olcegi + sonda)
MORF = 15


def main() -> int:
    manifest = json.load(io.open(VERI / "manifest.json", encoding="utf-8"))
    kaynaklar = sorted({o["kaynak"] for o in manifest["ornekler"] if o.get("cikti")})
    v30 = YOLO(str(KOK / "models" / "navitas_seg_v30_best.pt"), task="segment")
    obb = YOLO(str(KOK / "yolov8m-obb.pt"))
    (CIKTI / "cati_aday").mkdir(parents=True, exist_ok=True)

    ozet = []
    hucreler = []
    for ad in kaynaklar:
        bgr = cv2.imread(str(KARE_KOKU / ad))
        _, engel = zemin_ve_mevcut_engel(v30, bgr, 0.05)
        arac = arac_maskesi(obb, bgr, 0.25, max(bgr.shape[:2]))
        aday = ((engel > 0) & ~(arac > 0)).astype(np.uint8)
        cek = eliptik_cekirdek(MORF)
        aday = cv2.morphologyEx(aday, cv2.MORPH_CLOSE, cek)
        aday = cv2.morphologyEx(aday, cv2.MORPH_OPEN, cek)
        konturlar, _ = cv2.findContours(aday, cv2.RETR_EXTERNAL,
                                        cv2.CHAIN_APPROX_SIMPLE)
        son = np.zeros_like(aday)
        alanlar = []
        for k in konturlar:
            a = cv2.contourArea(k)
            if a >= ALAN_ESIGI:
                cv2.drawContours(son, [k], -1, 1, -1)
                alanlar.append(int(a))
        anahtar = ad.replace("/", "__").replace(".jpg", "")
        cv2.imwrite(str(CIKTI / "cati_aday" / (anahtar + ".png")), son * 255)
        ozet.append({"kaynak": ad, "blob": len(alanlar), "alanlar": sorted(alanlar, reverse=True),
                     "pay": round(float(son.mean()), 4)})
        gorsel = bgr.copy()
        gorsel[son > 0] = (gorsel[son > 0] * 0.45 + np.array([0, 0, 255]) * 0.55).astype(np.uint8)
        cv2.putText(gorsel, ad.split("/")[-2][-8:] + "/" + ad.split("/")[-1][6:12],
                    (8, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 255, 255), 2)
        hucreler.append(cv2.resize(gorsel, (640, 360)))

    for s in range((len(hucreler) + 5) // 6):
        grup = hucreler[s * 6:(s + 1) * 6]
        while len(grup) % 2:
            grup.append(np.zeros_like(grup[0]))
        satirlar = [np.hstack(grup[i:i + 2]) for i in range(0, len(grup), 2)]
        cv2.imwrite(str(CIKTI / f"dogrulama_sayfa_{s}.png"), np.vstack(satirlar))

    io.open(CIKTI / "cati_aday_ozet.json", "w", encoding="utf-8").write(
        json.dumps({"alan_esigi": ALAN_ESIGI, "morf": MORF, "kareler": ozet},
                   ensure_ascii=False, indent=1))
    print(f"kaynak: {len(kaynaklar)} · sayfa: {(len(hucreler)+5)//6}")
    print("ortalama aday payi:", round(float(np.mean([o['pay'] for o in ozet])), 4))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
