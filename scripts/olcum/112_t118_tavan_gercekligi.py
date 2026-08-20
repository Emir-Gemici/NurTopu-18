"""T118/T116'ya VERİ: gercek otoparkin SURULEBILIR orani 0,67 tavanini asiyor mu?

🔴 ESIK DEGISTIRMEZ, ESIK ONERMEZ (AGENTS SS9.2). Yalnizca su olculur:
"tavan, DOGRU calisan bir modeli de reddeder mi?"

NEDEN (D-239): (c) secenegi catiyi engel yaptiktan SONRA bile icerik-paydali
kaplama 0,734 olcuyor ve `ZEMIN_KAPLAMA_TAVANI` (0,67) yuzunden 67/67 kare
reddediliyor. (a)+(c) tavani asmiyor ama bunu catı-disi zeminin %39,7'sini
KAYBEDEREK yapiyor (D-238). Soru: gercekte o kareler ne kadar surulebilir?

MODELDEN BAGIMSIZ TAHMIN — IKI SINIR:
  IYIMSER (ust sinir) : zemin = TUM KARE − (71 engel ∪ ELLE cati)
      71'in kacirdigi engeller zemin sayilir -> gercek degerden BUYUK
  MUHAFAZAKAR (alt sinir) : zemin = TUM KARE − (71 engel ∪ ELLE cati
      ∪ v34 engel ∪ t122ac engel)
      HER kaynagin engel dedigi her piksel disarida -> gercek degerden KUCUK
Iki sinir da 0,67'nin USTUNDEYSE, tavan gercegin altindadir ve DOGRU bir model
de reddedilir. Alt sinir altta kaliyorsa soru aciktir.

Payda: `karar_sozlesmesi.zemin_kaplamasi` ile AYNI (ICERIK kutusu) — T118/D-214
uyarisi geregi payda ACIKCA yazilir; LETTERBOX degeri de ayrica basilir.

CIKTI: results/t118/tavan_gercekligi.json
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

from copy_paste_augmentation import (yolo_sinif_maskesi,  # noqa: E402
                                     zemin_ve_mevcut_engel)
from karar_sozlesmesi import ZEMIN_KAPLAMA_TAVANI  # noqa: E402
from ultralytics import YOLO  # noqa: E402

ETIKET71 = Path(r"O:\navitas-local-train\calisma\gercek_kare_etiket_v1\labels")
CATI_KOK = KOK / "results" / "t121" / "cati_maskeleri"
KARE_KOK = KOK / "data" / "raw_frames"
CIKTI = KOK / "results" / "t118" / "tavan_gercekligi.json"
CONF = 0.30
MODELLER = {
    "v34": KOK / "models" / "navitas_seg_v34_best.pt",
    "t122ac": KOK / "codes" / "runs" / "segment" / "t122ac_daralt_cati" / "weights" / "best.pt",
}


def etiket_adi(video: str, kare: str) -> str:
    return f"{video[-8:]}_{kare}"


def main() -> int:
    kareler = []
    for cp in sorted(CATI_KOK.glob("*.png")):
        ham = cv2.imread(str(cp), 0)
        cati = ((ham[:, :, 0] if ham.ndim == 3 else ham) > 127)
        video, kare = cp.stem.split("__")
        et = ETIKET71 / f"{etiket_adi(video, kare)}.txt"
        img = cv2.imread(str(KARE_KOK / f"{video}/{kare}.jpg"))
        if img is None or not et.is_file():
            continue
        kareler.append((f"{video}/{kare}", img, cati, et))
    print(f"olculebilir kare: {len(kareler)}", flush=True)

    engel_modeller = {}
    for ad, yol in MODELLER.items():
        m = YOLO(str(yol), task="segment")
        engel_modeller[ad] = [zemin_ve_mevcut_engel(m, img, CONF)[1].astype(bool)
                              for _ad, img, _c, _e in kareler]
        del m

    kayitlar = []
    for i, (ad, img, cati, et) in enumerate(kareler):
        h, w = img.shape[:2]
        metin = io.open(et, encoding="utf-8").read()
        engel71 = yolo_sinif_maskesi(metin, (h, w), 1).astype(bool)
        # 71'in "zemin" demedigi her sey engel kabul edilir (fail-safe okuma)
        zemin71 = yolo_sinif_maskesi(metin, (h, w), 0).astype(bool)
        engel71 = engel71 | ~zemin71

        iyimser = ~(engel71 | cati)
        muhafazakar = iyimser.copy()
        for ad_m in MODELLER:
            muhafazakar &= ~engel_modeller[ad_m][i]
        kayitlar.append({
            "kare": ad,
            "iyimser_zemin": round(float(iyimser.mean()), 4),
            "muhafazakar_zemin": round(float(muhafazakar.mean()), 4),
        })

    iy = [k["iyimser_zemin"] for k in kayitlar]
    mu = [k["muhafazakar_zemin"] for k in kayitlar]
    ozet = {
        "n": len(kayitlar), "tavan": ZEMIN_KAPLAMA_TAVANI,
        "payda": "TAM KARE (gercek kareler letterbox DEGIL: 1024x576 ham)",
        "iyimser_medyan": round(float(np.median(iy)), 4),
        "iyimser_ort": round(float(np.mean(iy)), 4),
        "muhafazakar_medyan": round(float(np.median(mu)), 4),
        "muhafazakar_ort": round(float(np.mean(mu)), 4),
        "iyimser_tavani_asan_kare": int(sum(1 for v in iy if v > ZEMIN_KAPLAMA_TAVANI)),
        "muhafazakar_tavani_asan_kare": int(sum(1 for v in mu if v > ZEMIN_KAPLAMA_TAVANI)),
        "yorum_kurali": ("IKI sinir da tavanin USTUNDEYSE tavan gercegin "
                          "altindadir ve DOGRU bir model de reddedilir; "
                          "alt sinir altta kaliyorsa soru ACIKTIR."),
        "kayitlar": kayitlar,
    }
    CIKTI.parent.mkdir(parents=True, exist_ok=True)
    io.open(CIKTI, "w", encoding="utf-8").write(
        json.dumps(ozet, ensure_ascii=False, indent=1))
    print(json.dumps({k: v for k, v in ozet.items() if k != "kayitlar"},
                     ensure_ascii=False, indent=1))
    print("⚠ ESIK DEGISTIRILMEDI, ONERILMEDI — bu bir OLCUMDUR (SS9.2).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
