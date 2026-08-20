"""T121 adim 4 hazirlik-2 — CATI POLIGONLARININ HOMOGRAFI YAYILIMI + dogrulama sayfalari.

YONTEM (on kayit): 21 anahtar karede elle poligon (results/t121/
cati_anahtar_poligonlari.json, D-80 ile yerlestirildi). Kalan 35 produced
kaynak icin AYNI videodaki EN YAKIN anahtar kareden ORB+RANSAC homografisiyle
tasinir (kare araligi <=3; sahne dokusu zengin, duzlemsel-uzak sahne —
homografi gecerli). Her kare bindirme sayfasinda GOZLE dogrulanir; kotu
tasinanlar elle duzeltilir (cati_duzeltmeleri.json, sonraki asama).

CIKTI:
  results/t121/cati_maskeleri/<anahtar>.png   (56 kaynak, 0/255)
  results/t121/yayilim_sayfa_<n>.png          (bindirmeli 6'li sayfalar)
  results/t121/yayilim_ozet.json              (H bulunamayan/az-eslesen kareler)
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import cv2
import numpy as np

KOK = Path(__file__).resolve().parents[2]
VERI = KOK / "dataset" / "copy_paste_gercek"
KARE_KOKU = KOK / "data" / "raw_frames"
CIKTI = KOK / "results" / "t121"
POLIGONLAR = CIKTI / "cati_anahtar_poligonlari.json"
EN_AZ_ESLESME = 40           # RANSAC inlier alt siniri; alti "supheli" isaretlenir


def maske_yap(poligonlar, sekil) -> np.ndarray:
    m = np.zeros(sekil, np.uint8)
    for p in poligonlar:
        cv2.fillPoly(m, [np.asarray(p, np.int32)], 1)
    return m


def homografi(kaynak_gri, hedef_gri):
    orb = cv2.ORB_create(4000)
    k1, d1 = orb.detectAndCompute(kaynak_gri, None)
    k2, d2 = orb.detectAndCompute(hedef_gri, None)
    if d1 is None or d2 is None:
        return None, 0
    es = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True).match(d1, d2)
    es = sorted(es, key=lambda m: m.distance)[:800]
    if len(es) < 12:
        return None, 0
    p1 = np.float32([k1[m.queryIdx].pt for m in es]).reshape(-1, 1, 2)
    p2 = np.float32([k2[m.trainIdx].pt for m in es]).reshape(-1, 1, 2)
    H, ic = cv2.findHomography(p1, p2, cv2.RANSAC, 3.0)
    return H, int(ic.sum()) if ic is not None else 0


def main() -> int:
    cfg = json.load(io.open(POLIGONLAR, encoding="utf-8"))["kareler"]
    manifest = json.load(io.open(VERI / "manifest.json", encoding="utf-8"))
    kaynaklar = sorted({o["kaynak"] for o in manifest["ornekler"] if o.get("cikti")})
    (CIKTI / "cati_maskeleri").mkdir(parents=True, exist_ok=True)

    ozet = []
    hucreler = []
    for ad in kaynaklar:
        bgr = cv2.imread(str(KARE_KOKU / ad))
        sekil = bgr.shape[:2]
        video = ad.split("/")[0]
        no = int(ad.split("/")[1].split("_")[1])
        if ad in cfg:
            maske = maske_yap(cfg[ad]["cati"], sekil)
            kayit = {"kaynak": ad, "yontem": "ANAHTAR", "inlier": None}
        else:
            adaylar = [(abs(int(k.split("/")[1].split("_")[1]) - no), k)
                       for k in cfg if k.split("/")[0] == video]
            adaylar.sort()
            mesafe, anahtar = adaylar[0]
            a_bgr = cv2.imread(str(KARE_KOKU / anahtar))
            H, inlier = homografi(cv2.cvtColor(a_bgr, cv2.COLOR_BGR2GRAY),
                                  cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY))
            if H is None or inlier < EN_AZ_ESLESME:
                maske = np.zeros(sekil, np.uint8)
                kayit = {"kaynak": ad, "yontem": "BASARISIZ", "anahtar": anahtar,
                         "mesafe": mesafe, "inlier": inlier}
            else:
                a_maske = maske_yap(cfg[anahtar]["cati"], sekil)
                maske = cv2.warpPerspective(a_maske, H, (sekil[1], sekil[0]),
                                            flags=cv2.INTER_NEAREST)
                kayit = {"kaynak": ad, "yontem": "HOMOGRAFI", "anahtar": anahtar,
                         "mesafe": mesafe, "inlier": inlier}
        anahtar_ad = ad.replace("/", "__").replace(".jpg", "")
        cv2.imwrite(str(CIKTI / "cati_maskeleri" / (anahtar_ad + ".png")), maske * 255)
        kayit["pay"] = round(float(maske.mean()), 4)
        ozet.append(kayit)
        gorsel = bgr.copy()
        gorsel[maske > 0] = (gorsel[maske > 0] * 0.45 + np.array([0, 0, 255]) * 0.55).astype(np.uint8)
        cv2.putText(gorsel, f"{video[-8:]}/{no:02d} {kayit['yontem'][:4]}",
                    (8, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 255, 255), 2)
        hucreler.append(cv2.resize(gorsel, (640, 360)))

    for s in range((len(hucreler) + 5) // 6):
        grup = hucreler[s * 6:(s + 1) * 6]
        while len(grup) % 2:
            grup.append(np.zeros_like(grup[0]))
        satirlar = [np.hstack(grup[i:i + 2]) for i in range(0, len(grup), 2)]
        cv2.imwrite(str(CIKTI / f"yayilim_sayfa_{s}.png"), np.vstack(satirlar))

    io.open(CIKTI / "yayilim_ozet.json", "w", encoding="utf-8").write(
        json.dumps({"en_az_eslesme": EN_AZ_ESLESME, "kareler": ozet},
                   ensure_ascii=False, indent=1))
    basarisiz = [o for o in ozet if o["yontem"] == "BASARISIZ"]
    print(f"kaynak: {len(kaynaklar)} · anahtar: {sum(1 for o in ozet if o['yontem']=='ANAHTAR')}"
          f" · homografi: {sum(1 for o in ozet if o['yontem']=='HOMOGRAFI')}"
          f" · BASARISIZ: {len(basarisiz)}")
    for o in basarisiz:
        print("  BASARISIZ:", o["kaynak"], "inlier=", o["inlier"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
