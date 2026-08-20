"""T122 — KAHIN KIYASI: aday kahinler AYNI yer gercegi uzerinde, AYNI olcutle.

YER GERCEGI: T121'de elle cizilip UC gorsel turda dogrulanan cati maskeleri
(`results/t121/cati_maskeleri/`, 55 kare cati iceriyor).
OLCUT: kahin bu cati alaninin ne kadarina ZEMIN diyor (KACAK; kucuk iyi) ve
kare genelinde ne kadar zemin uretiyor (KAPSAMA; cok dusukse korluk riski).

NEDEN. Yeni DJI verisi geldiginde etiket hattinin OTOMATIK bir cati kahinine
ihtiyaci var (elle 56 kare cizildi; yuzlerce kare icin surdurulemez). Aday
kahinler:
  · `71_gercek_kare_etiketleyici` ciktisi (klasik CV, modelden BAGIMSIZ)
    -> 107_t122_71_capraz_denetimi.py ile olculdu: kacak ort %49,4
  · model kahinleri (aday_v5c: uretecin bugunku kahini; v30; v34; t121_ft)
⚠ DAIRESELLIK: v34/t121_ft duzeltilmeye calisilan zincirin urunudur; kahin
olarak SECILMELERI dairesel olur. Olcume "hangi model ne goruyor" sorusu icin
girerler, kahin adayi olarak DEGIL — bu ayrim raporda korunur.

CIKTI: results/t122/kahin_kiyasi.json
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

from copy_paste_augmentation import zemin_ve_mevcut_engel  # noqa: E402
from ultralytics import YOLO  # noqa: E402

CATI_KOK = KOK / "results" / "t121" / "cati_maskeleri"
KARE_KOK = KOK / "data" / "raw_frames"
CIKTI = KOK / "results" / "t122" / "kahin_kiyasi.json"

# (etiket, yol, conf, dairesel_mi)
ADAYLAR = [
    ("aday_v5c@0.05", KOK / "models" / "aday_v5c_m640.pt", 0.05, False),
    ("aday_v5c@0.30", KOK / "models" / "aday_v5c_m640.pt", 0.30, False),
    ("v30@0.30", KOK / "models" / "navitas_seg_v30_best.pt", 0.30, True),
    ("v34@0.30", KOK / "models" / "navitas_seg_v34_best.pt", 0.30, True),
]


def main() -> int:
    catili = []
    for cp in sorted(CATI_KOK.glob("*.png")):
        ham = cv2.imread(str(cp), 0)
        m = (ham[:, :, 0] if ham.ndim == 3 else ham) > 127
        if m.any():
            video, kare = cp.stem.split("__")
            catili.append((f"{video}/{kare}.jpg", m))
    print(f"cati iceren kare: {len(catili)}", flush=True)

    kareler = {ad: cv2.imread(str(KARE_KOK / ad)) for ad, _ in catili}
    sonuc = {"n_kare": len(catili),
             "yer_gercegi": "T121 elle+homografi cati maskeleri (uc gorsel tur)",
             "olcut": "kacak = cati alaninda ZEMIN diyen piksel orani (kucuk iyi)",
             "adaylar": {}}
    for etiket, yol, conf, dairesel in ADAYLAR:
        model = YOLO(str(yol), task="segment")
        kacaklar, kapsamalar = [], []
        for ad, cati in catili:
            zemin, _ = zemin_ve_mevcut_engel(model, kareler[ad], conf)
            z = zemin.astype(bool)
            kacaklar.append(float((z & cati).sum() / max(1, cati.sum())))
            kapsamalar.append(float(z.mean()))
        del model
        sonuc["adaylar"][etiket] = {
            "yol": str(yol), "conf": conf, "dairesel_aday": dairesel,
            "kacak_ort": round(float(np.mean(kacaklar)), 4),
            "kacak_medyan": round(float(np.median(kacaklar)), 4),
            "kacak_maks": round(float(np.max(kacaklar)), 4),
            "kacak_yuksek_kare_0_20": int(sum(1 for k in kacaklar if k > 0.20)),
            "zemin_kapsama_ort": round(float(np.mean(kapsamalar)), 4),
        }
        print(etiket, json.dumps(sonuc["adaylar"][etiket], ensure_ascii=False),
              flush=True)

    CIKTI.parent.mkdir(parents=True, exist_ok=True)
    io.open(CIKTI, "w", encoding="utf-8").write(
        json.dumps(sonuc, ensure_ascii=False, indent=1))
    print(f"yazildi: {CIKTI}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
