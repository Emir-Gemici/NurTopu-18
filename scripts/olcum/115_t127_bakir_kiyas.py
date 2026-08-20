"""T127 — BAKIR karelerde dort aday kiyasi (D-242 SS3'un ekseni).

Kume: `114_t127_bakir_kare_kumesi.py`nin urettigi 11 EGITIM-DISI gercek kare
ve onlarin cati maskeleri. Olcut ve zincir T122 kiyasiyla (109) AYNI —
tek fark KUME. Boylece "ayni model, egitim-ici vs egitim-disi" kiyasi
YAPILABILIR.

⚠ SINIRLAR (114'te yazili, burada TEKRAR EDILIR cunku sonuc bunlarla okunur):
  · YANLI ORNEKLEM: kareler ureteci tarafindan "yeterli guvenli zemin yok"
    diye ELENDI — sistematik olarak DAHA ZOR.
  · ALAN-DISI DEGIL, EGITIM-DISI: ayni saha, ayni oturum, komsu kareler
    (pHash medyan 0,281; biri 0,094 = neredeyse ayni, AYRICA isaretlenir).
  · Cati maskeleri T121 capalarindan homografiyle tasindi; capalarin kendi
    kucuk tasmasi (alt kenarda araclara birkac piksel) TUM modellere AYNI
    sekilde biner — kiyasi bozmaz, mutlak degeri hafif sisirir.

CIKTI: results/t127/kiyas.json + kiyas.md
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
from karar_sozlesmesi import zemin_kaplamasi, zemin_maskesi_reddi  # noqa: E402
from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp,  # noqa: E402
                           _preprocess, get_masks)
from ultralytics import YOLO  # noqa: E402

MASKE_KOK = KOK / "results" / "t127" / "bakir_cati_maskeleri"
KARE_KOK = KOK / "data" / "raw_frames"
CIKTI = KOK / "results" / "t127"
CONF = 0.30
RUNS = KOK / "codes" / "runs" / "segment"
IKIZ = "whatsapp_video_2026_07_30_at_11_44_03/frame_000003_000000720.jpg"

MODELLER = [
    ("v30", KOK / "models" / "navitas_seg_v30_best.pt"),
    ("v34_URETIM", KOK / "models" / "navitas_seg_v34_best.pt"),
    ("t121_ft_(c)", RUNS / "t121_etiket_ft" / "weights" / "best.pt"),
    ("t122ac_(a+c)", RUNS / "t122ac_daralt_cati" / "weights" / "best.pt"),
]


def main() -> int:
    kareler = []
    for mp in sorted(MASKE_KOK.glob("*.png")):
        ham = cv2.imread(str(mp), 0)
        cati = ((ham[:, :, 0] if ham.ndim == 3 else ham) > 127)
        video, kare = mp.stem.split("__")
        ad = f"{video}/{kare}.jpg"
        img = cv2.imread(str(KARE_KOK / ad))
        if img is None or not cati.any():
            continue
        kareler.append((ad, img, cati))
    print(f"bakir kare (catili): {len(kareler)}", flush=True)

    sonuc = {}
    for etiket, yol in MODELLER:
        if not yol.is_file():
            print(f"ATLANDI: {etiket}", file=sys.stderr)
            continue
        model = YOLO(str(yol), task="segment")
        kacak, icerik_p, red, kacak_ikizsiz = [], [], 0, []
        for ad, img, cati in kareler:
            z, _e = zemin_ve_mevcut_engel(model, img, CONF)
            k = float((z.astype(bool) & cati).sum() / max(1, cati.sum()))
            kacak.append(k)
            if ad != IKIZ:
                kacak_ikizsiz.append(k)
            sq, small, icerik = _preprocess(img)
            h, w = sq.shape[:2]
            s = model.predict(small, imgsz=INFER_SIZE, conf=CONF, verbose=False)
            mk = _maskeleri_icerige_kirp(get_masks(s, h, w), icerik)
            trav = (mk[0] > 0).astype(np.uint8)
            icerik_p.append(float(zemin_kaplamasi(trav, icerik)))
            red += zemin_maskesi_reddi(trav, icerik) is not None
        del model
        sonuc[etiket] = {
            "cati_kacak_ort": round(float(np.mean(kacak)), 4),
            "cati_kacak_medyan": round(float(np.median(kacak)), 4),
            "cati_kacak_ort_IKIZSIZ": round(float(np.mean(kacak_ikizsiz)), 4),
            "kaplama_icerik_medyan": round(float(np.median(icerik_p)), 4),
            "red": int(red), "n": len(kareler),
        }
        print(etiket, json.dumps(sonuc[etiket], ensure_ascii=False), flush=True)

    CIKTI.mkdir(parents=True, exist_ok=True)
    io.open(CIKTI / "kiyas.json", "w", encoding="utf-8").write(
        json.dumps({"kume": "BAKIR (egitim disi) 11 gercek kare",
                    "conf": CONF, "modeller": sonuc}, ensure_ascii=False, indent=1))
    basliklar = [("cati_kacak_ort", "çatı kaçağı (bakir)"),
                 ("cati_kacak_ort_IKIZSIZ", "çatı kaçağı (ikiz kare hariç)"),
                 ("kaplama_icerik_medyan", "kaplama İÇERİK"),
                 ("red", "red / n")]
    satir = ["| ölçüt | " + " | ".join(sonuc) + " |",
             "|---|" + "---|" * len(sonuc)]
    for anahtar, baslik in basliklar:
        satir.append(f"| {baslik} | " + " | ".join(
            str(sonuc[m][anahtar]) for m in sonuc) + " |")
    io.open(CIKTI / "kiyas.md", "w", encoding="utf-8").write(
        "# T127 · BAKIR (eğitim dışı) karelerde kıyas\n\n" + "\n".join(satir) + "\n")
    print("\n".join(satir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
