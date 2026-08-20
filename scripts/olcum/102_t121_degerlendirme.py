"""T121 BELIRLEYICI KOSUM DEGERLENDIRMESI — on kayit olcutlerini oldugu gibi olcer.

ON KAYIT: results/t121_on_kayit.md (D-107). Bu betik esik YORUMLAMAZ; sayilari
uretir ve on kayit esikleriyle mekanik kiyasi yazar. K0/K1 icin ayrica
65_kabul_denetcisi CLI'si kosulur (ayni zincir, tek kaynak) — bu betik yalniz
T121'e ozgu olcumleri yapar:

  1. SONDA DISKLERI (6 kare, results/t121/diskler.json REV1):
     cati disklerinde ort. ENGEL ve ZEMIN orani — uretim conf 0,30 zinciri
     (`zemin_ve_mevcut_engel`, rpi_inference _preprocess/get_masks uzerinden).
     Basari kurali (on kayit): engel >= 0,50 VE zemin <= 0,30.
  2. 67 KARE KAPLAMA — IKI PAYDAYLA (D-207/T118 uyarisi):
     ICERIK paydasi: `karar_sozlesmesi.zemin_kaplamasi(trav, icerik)` (:426)
     LETTERBOX paydasi: maske ortalamasi TUM KARE tuval uzerinden (65'in tanimi)
     + `zemin_maskesi_reddi(trav, icerik)` tetik sayisi (:552).
  3. Ayni olcumler TABAN v34 icin de AYNI KOSUDA (esli kiyas).

CIKTI: results/t121/degerlendirme.json
"""
from __future__ import annotations

import argparse
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

DISKLER = KOK / "results" / "t121" / "diskler.json"
KARE_KOKU = KOK / "data" / "raw_frames"
CIKTI = KOK / "results" / "t121" / "degerlendirme.json"
CONF = 0.30                     # uretim zinciri (65/D-139)


def disk_maskesi(sekil, x, y, r):
    m = np.zeros(sekil, np.uint8)
    cv2.circle(m, (int(x), int(y)), int(r), 1, -1)
    return m.astype(bool)


def disk_olcumu(model) -> dict:
    cfg = json.load(io.open(DISKLER, encoding="utf-8"))["kareler"]
    cati_e, cati_z, zemin_z = [], [], []
    for ad, k in cfg.items():
        bgr = cv2.imread(str(KARE_KOKU / ad))
        zemin, engel = zemin_ve_mevcut_engel(model, bgr, CONF)
        for x, y, r in k["cati"]:
            dm = disk_maskesi(zemin.shape, x, y, r)
            cati_e.append(float(engel[dm].mean()))
            cati_z.append(float(zemin[dm].mean()))
        for x, y, r in k["zemin"]:
            dm = disk_maskesi(zemin.shape, x, y, r)
            zemin_z.append(float(zemin[dm].mean()))
    return {"cati_engel_ort": round(float(np.mean(cati_e)), 4),
            "cati_zemin_ort": round(float(np.mean(cati_z)), 4),
            "zemin_zemin_ort": round(float(np.mean(zemin_z)), 4),
            "n_cati_disk": len(cati_e), "n_zemin_disk": len(zemin_z)}


def kaplama_67(model) -> dict:
    kareler = sorted(KARE_KOKU.rglob("*.jpg"))
    icerik_p, tuval_p, red = [], [], 0
    red_sebepleri = {}
    for p in kareler:
        bgr = cv2.imread(str(p))
        sq, small, icerik = _preprocess(bgr)
        h, w = sq.shape[:2]
        sonuc = model.predict(small, imgsz=INFER_SIZE, conf=CONF, verbose=False)
        mk = _maskeleri_icerige_kirp(get_masks(sonuc, h, w), icerik)
        trav = (mk[0] > 0).astype(np.uint8)
        icerik_p.append(float(zemin_kaplamasi(trav, icerik)))
        tuval_p.append(float(trav.mean()))
        ret = zemin_maskesi_reddi(trav, icerik)
        if ret is not None:
            red += 1
            sebep = ret[0] if isinstance(ret, tuple) else str(ret)
            red_sebepleri[str(sebep)] = red_sebepleri.get(str(sebep), 0) + 1
    return {"n": len(kareler),
            "icerik_medyan": round(float(np.median(icerik_p)), 4),
            "icerik_ort": round(float(np.mean(icerik_p)), 4),
            "tuval_medyan": round(float(np.median(tuval_p)), 4),
            "tuval_ort": round(float(np.mean(tuval_p)), 4),
            "zemin_maskesi_reddi": red, "red_sebepleri": red_sebepleri}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ft", type=Path,
                    default=KOK / "codes" / "runs" / "segment" / "t121_etiket_ft"
                    / "weights" / "best.pt")
    ap.add_argument("--taban", type=Path,
                    default=KOK / "models" / "navitas_seg_v34_best.pt")
    args = ap.parse_args()
    if not args.ft.is_file():
        raise SystemExit(f"ft agirligi yok: {args.ft}")

    # D-222 §3: kiyas UC model uzerinden — v30 (cati gucul/arena zayif),
    # v34 (arena guclu/cati kor), t121_ft (etiket duzeltilmis aday).
    v30 = KOK / "models" / "navitas_seg_v30_best.pt"
    sonuc = {"conf": CONF, "ft": str(args.ft), "taban": str(args.taban),
             "v30": str(v30)}
    for etiket, yol in (("v30", v30), ("taban_v34", args.taban),
                        ("t121_ft", args.ft)):
        model = YOLO(str(yol), task="segment")
        sonuc[etiket] = {"disk": disk_olcumu(model), "kaplama67": kaplama_67(model)}
        del model

    d = sonuc["t121_ft"]["disk"]
    sonuc["on_kayit_kiyasi"] = {
        "cati_dondu": bool(d["cati_engel_ort"] >= 0.50 and d["cati_zemin_ort"] <= 0.30),
        "kural": "cati disklerinde engel>=0,50 VE zemin<=0,30 (results/t121_on_kayit.md)",
    }
    CIKTI.write_text(json.dumps(sonuc, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(sonuc, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
