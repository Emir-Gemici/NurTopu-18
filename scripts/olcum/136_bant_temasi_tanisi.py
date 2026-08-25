"""UC_BANT_TEMAS_YOK — PARCALILIK mi YAPISAL mi? Ayirt edici olcum.

🔴 NEDEN (D-280 §2): DJI kirsal egitimi `MASKE_YOK`'u 35->29 dusurdu ama
rota uretimi 11->10'a indi; kazanilan kareler `UC_BANT_TEMAS_YOK`'a kaydi
(13->20). Yani model DAHA COK GORUYOR ama gordugu zemin BANTLARA ULASMIYOR.
Iki acikama mumkun ve ikisi TAMAMEN FARKLI ISLER gerektirir:
  (a) PARCALILIK — maske kopuk; `rpi_inference` YALNIZ EN BUYUK bileseni
      tutuyor (satir ~1200) ve o parca bantlara yetismiyor. Cozum: ETIKET
      kalitesi / model egitimi.
  (b) YAPISAL   — zemin 30 m irtifada kareyi alttan uste KAT ETMIYOR (yol
      capraz geciyor, kadraja sigmiyor). Cozum: ETIKET DEGIL, HAT/UCUS
      parametresi (irtifa, kadraj, bant tanimi).

AYIRT EDICI SINAMA (tek olcum, yoruma gerek yok):
    tam maske (TUM bilesenler) bantlara yetiyor  &&  en buyuk bilesen YETMIYOR
        -> PARCALILIK
    tam maske de YETMIYOR
        -> YAPISAL
Esik: BANT_TEMAS_MIN_ORANI = 0.02 (icerik genisliginin %2'si) — cok dusuk bir
bar; bunu gecemeyen bir koridor gercekten kenara ULASMIYOR demektir.

CIKTI: results/dji_kirsal/bant_tanisi.json + ekrana ozet
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import numpy as np

KOK = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(KOK / "codes"))

from karar_sozlesmesi import bant_temasi_gereken_px  # noqa: E402
from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp,  # noqa: E402
                           _preprocess, get_masks, hedef_bant_yuksekligi)
from ultralytics import YOLO  # noqa: E402

KARE_DIZIN = KOK / "dataset" / "dji_kirsal" / "images" / "val"
CIKTI = KOK / "results" / "dji_kirsal" / "bant_tanisi.json"

MODELLER = [
    ("v35", KOK / "models" / "navitas_seg_v35_best.pt"),
    ("dji_kirsal_v1", KOK / "codes" / "runs" / "segment" / "dji_kirsal_v1" /
     "weights" / "best.pt"),
]


def temas_genisligi(maske, icerik, taraf):
    """Bant icinde temas edilen BENZERSIZ x sutunu sayisi (uretimle ayni)."""
    x0, y0, w, h = icerik
    bant_h = hedef_bant_yuksekligi(h)
    if taraf == "ust":
        bant = maske[y0:y0 + bant_h, x0:x0 + w]
    else:
        bant = maske[y0 + h - bant_h:y0 + h, x0:x0 + w]
    if bant.size == 0:
        return 0
    return int((bant.any(axis=0)).sum())


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    kareler = sorted(KARE_DIZIN.glob("*.jpg"))
    print("kare: %d · esik BANT_TEMAS_MIN_ORANI = 0.02" % len(kareler))
    tum = {}
    for ad, yol in MODELLER:
        if not yol.exists():
            print("  %s: AGIRLIK YOK -> atlandi" % ad)
            continue
        model = YOLO(str(yol), task="segment")
        satirlar = []
        for p in kareler:
            img = cv2.imread(str(p))
            if img is None:
                continue
            sq, small, icerik = _preprocess(img)
            h, w = sq.shape[:2]
            sonuc = model.predict(small, imgsz=INFER_SIZE, conf=0.30, verbose=False)
            mk = _maskeleri_icerige_kirp(get_masks(sonuc, h, w), icerik)
            zemin = (np.asarray(mk[0]) > 0).astype(np.uint8)
            ix, iy, iw, ih = icerik
            gereken = bant_temasi_gereken_px(iw)
            n, lab, stats, _ = cv2.connectedComponentsWithStats(zemin, 8)
            if n <= 1:
                satirlar.append({"kare": p.name, "durum": "MASKE_YOK",
                                 "gereken": gereken})
                continue
            en_buyuk_i = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
            enb = (lab == en_buyuk_i).astype(np.uint8)
            toplam_px = int(zemin.sum())
            enb_px = int(enb.sum())
            olcum = {
                "kare": p.name, "bilesen": n - 1,
                "toplam_px": toplam_px, "enbuyuk_px": enb_px,
                "enbuyuk_pay": round(enb_px / max(toplam_px, 1), 4),
                "gereken": gereken, "icerik_w": iw,
            }
            for etiket, msk in (("enb", enb), ("tam", zemin)):
                for taraf in ("alt", "ust"):
                    olcum["%s_%s" % (etiket, taraf)] = temas_genisligi(
                        msk, icerik, taraf)
            enb_ok = (olcum["enb_alt"] >= gereken and olcum["enb_ust"] >= gereken)
            tam_ok = (olcum["tam_alt"] >= gereken and olcum["tam_ust"] >= gereken)
            olcum["enb_yeterli"] = enb_ok
            olcum["tam_yeterli"] = tam_ok
            if enb_ok:
                olcum["durum"] = "GECER"
            elif tam_ok:
                olcum["durum"] = "PARCALILIK"
            else:
                olcum["durum"] = "YAPISAL"
            satirlar.append(olcum)
        tum[ad] = satirlar

        say = {}
        for s in satirlar:
            say[s["durum"]] = say.get(s["durum"], 0) + 1
        print("\n== %s" % ad)
        for d in ("GECER", "PARCALILIK", "YAPISAL", "MASKE_YOK"):
            if d in say:
                print("   %-11s %3d" % (d, say[d]))
        red = [s for s in satirlar if s.get("durum") in ("PARCALILIK", "YAPISAL")]
        if red:
            pay = sorted(s["enbuyuk_pay"] for s in red)
            print("   reddedilenlerde en buyuk bilesenin payi: "
                  "medyan %.3f · min %.3f · maks %.3f"
                  % (pay[len(pay) // 2], pay[0], pay[-1]))
            for taraf in ("alt", "ust"):
                eksik = [s for s in red if s["tam_%s" % taraf] < s["gereken"]]
                print("   TAM maske %s bandina yetmeyen: %d/%d"
                      % (taraf, len(eksik), len(red)))

    CIKTI.parent.mkdir(parents=True, exist_ok=True)
    CIKTI.write_text(json.dumps(
        {"_ne": "UC_BANT_TEMAS_YOK tanisi — PARCALILIK mi YAPISAL mi",
         "_ayirt_edici": "tam maske yetiyor ama en buyuk bilesen yetmiyorsa "
                         "PARCALILIK; tam maske de yetmiyorsa YAPISAL",
         "_esik": "BANT_TEMAS_MIN_ORANI = 0.02",
         "modeller": tum}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\nyazildi: %s" % CIKTI)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
