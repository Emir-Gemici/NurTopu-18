"""T122 — 71 ETIKETLEYICISININ CAPRAZ DENETIMI: elle dogrulanmis catiyi goruyor mu?

NEDEN. `71_gercek_kare_etiketleyici.py` 67 gercek kareyi ZATEN etiketlemis
(`gercek_kare_etiket_v1/`, uc gorsel duzeltme turundan gecmis, D-127/D-128) ve
kurali DOGRU yondedir: "notr gri asfalt DEGILSE ENGELDIR" (fail-safe). Bu,
`copy_paste_augmentation.yolo_etiketi()`'nin tam-kare-zemin kuralinin TERSIDIR
(D-210). Yani depoda BIRBIRINE ZIT iki etiketleme felsefesi var ve egitim
verisini uretmis olan YANLIS olandir.

BU BETIK 71'i BAGIMSIZ BIR YER GERCEGIYLE SINAR: T121'de elle cizilip UC
gorsel turda dogrulanan cati maskeleri (`results/t121/cati_maskeleri/`, 56
kaynak). Olculen: 71 bu catilarin ne kadarini ZEMIN sayiyor (kacak), ne
kadarini ENGEL sayiyor (dogru). Onizlemede binanin GOLGELI yamaci yesil
gorundu — o gozlem burada SAYIYA cevrilir (D-80: gorsel isaret eder,
olcum karara baglar).

CIKTI: results/t122/capraz_71.json + gorsel sayfa.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import cv2
import numpy as np

KOK = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(KOK / "scripts"))

from copy_paste_augmentation import yolo_sinif_maskesi  # noqa: E402

ETIKET_KOK = Path(r"O:\navitas-local-train\calisma\gercek_kare_etiket_v1")
CATI_KOK = KOK / "results" / "t121" / "cati_maskeleri"
KARE_KOK = KOK / "data" / "raw_frames"
CIKTI = KOK / "results" / "t122"
ZEMIN = 0


def etiket_adi(kaynak: str) -> str:
    """`whatsapp_video_2026_07_30_at_11_44_03/frame_000008_...jpg`
    -> `11_44_03_frame_000008_...`"""
    video, kare = kaynak.split("/")
    return f"{video[-8:]}_{kare.replace('.jpg', '')}"


def main() -> int:
    catili = sorted(CATI_KOK.glob("*.png"))
    kayitlar, hucreler = [], []
    for cp in catili:
        anahtar = cp.stem                       # video__frame_...
        video, kare = anahtar.split("__")
        kaynak = f"{video}/{kare}.jpg"
        etiket = ETIKET_KOK / "labels" / f"{etiket_adi(kaynak)}.txt"
        if not etiket.is_file():
            kayitlar.append({"kaynak": kaynak, "hata": "71 etiketi YOK"})
            continue
        ham = cv2.imread(str(cp), 0)
        cati = ((ham[:, :, 0] if ham.ndim == 3 else ham) > 127)
        if not cati.any():
            continue                            # cati kadraj disi (T121: 1 kare)
        h, w = cati.shape
        metin = io.open(etiket, encoding="utf-8").read()
        zemin = yolo_sinif_maskesi(metin, (h, w), ZEMIN).astype(bool)
        kacak = float((zemin & cati).sum() / max(1, cati.sum()))
        kayitlar.append({
            "kaynak": kaynak, "cati_px": int(cati.sum()),
            "71_zemin_diyor_orani": round(kacak, 4),
            "71_engel_diyor_orani": round(1 - kacak, 4),
            "71_zemin_payi": round(float(zemin.mean()), 4),
        })
        if len(hucreler) < 6:
            bgr = cv2.imread(str(KARE_KOK / kaynak))
            g = bgr.copy()
            g[zemin] = (g[zemin] * 0.55 + np.array([0, 255, 0]) * 0.45).astype(np.uint8)
            kesisim = zemin & cati
            g[kesisim] = (0, 0, 255)            # KACAK: cati ama 71 zemin diyor
            cv2.putText(g, f"{kare[6:12]} kacak={kacak:.2f}", (8, 28),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.85, (255, 255, 0), 2)
            hucreler.append(cv2.resize(g, (640, 360)))

    olculen = [k for k in kayitlar if "71_zemin_diyor_orani" in k]
    oranlar = [k["71_zemin_diyor_orani"] for k in olculen]
    ozet = {
        "n_cati_kare": len(olculen),
        "kacak_ort": round(float(np.mean(oranlar)), 4),
        "kacak_medyan": round(float(np.median(oranlar)), 4),
        "kacak_maks": round(float(np.max(oranlar)), 4),
        "kacak_min": round(float(np.min(oranlar)), 4),
        "kacak_yuksek_kare_sayisi_0_20": sum(1 for o in oranlar if o > 0.20),
        "71_ort_zemin_payi": round(float(np.mean(
            [k["71_zemin_payi"] for k in olculen])), 4),
        "yer_gercegi": "T121 elle+homografi cati maskeleri (uc gorsel tur)",
        "kayitlar": kayitlar,
    }
    CIKTI.mkdir(parents=True, exist_ok=True)
    io.open(CIKTI / "capraz_71.json", "w", encoding="utf-8").write(
        json.dumps(ozet, ensure_ascii=False, indent=1))
    if hucreler:
        while len(hucreler) % 2:
            hucreler.append(np.zeros_like(hucreler[0]))
        satir = [np.hstack(hucreler[i:i + 2]) for i in range(0, len(hucreler), 2)]
        cv2.imwrite(str(CIKTI / "capraz_71.png"), np.vstack(satir))
    print(json.dumps({k: v for k, v in ozet.items() if k != "kayitlar"},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
