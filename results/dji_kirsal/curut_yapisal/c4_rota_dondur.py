"""CURUTME 4 — 18 YAPISAL karede URETIM `analyze_path` gercekten kosulur.

Iki kosum, ayni elle cizilen etiketler, ayni uretim fonksiyonu:
  (1) ORIJINAL kadraj
  (2) kare 90 derece DONDURULMUS (iha yalpasi yol eksenine cevrilmis gibi)

Eger (1) YAPISAL deyip (2) ROTA URETIYORSA: arazide gecilebilir koridor VARDIR;
red sebebi 'zemin yok' degil 'koridor bant EKSENINE DIK' demektir.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np

KOK = Path(r"O:\navitas")
sys.path.insert(0, str(KOK / "codes"))
from rpi_inference import _preprocess, analyze_path  # noqa: E402

KARE_DIZIN = KOK / "dataset" / "dji_kirsal" / "images" / "val"
ETIKET_KOK = KOK / "results" / "dji_20260822" / "f5_olcek"
CIK = KOK / "results" / "dji_kirsal" / "curut_yapisal"


def etiket_bul(stem):
    for alt in ("A", "B", "C", "D"):
        p = ETIKET_KOK / alt / (stem + "_uc.png")
        if p.exists():
            return p
    return None


def kosum(img, lab):
    H, W = img.shape[:2]
    tuval, _, icerik = _preprocess(img)
    x0, y0, w, h = icerik
    büyük = cv2.resize(lab, (w, h), interpolation=cv2.INTER_NEAREST)
    zemin = np.zeros(tuval.shape[:2], np.uint8)
    engel = np.zeros(tuval.shape[:2], np.uint8)
    zemin[y0:y0 + h, x0:x0 + w] = (büyük == 1).astype(np.uint8)
    engel[y0:y0 + h, x0:x0 + w] = (büyük == 2).astype(np.uint8)
    t0 = time.perf_counter()
    serit, guven, wps, temiz, sebep = analyze_path(
        zemin, return_clean=True, return_reason=True,
        icerik=icerik, engel_mask=engel)
    return {"serit": serit, "guven": round(float(guven), 4),
            "wp": len(wps), "sebep": None if sebep is None else sebep[0],
            "detay": None if sebep is None else sebep[1],
            "sn": round(time.perf_counter() - t0, 1)}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    e = json.loads((KOK / "results" / "dji_kirsal" /
                    "bant_tanisi_etiket.json").read_text(encoding="utf-8"))
    hedefler = [r["kare"] for r in e["kareler"] if r["durum"] == "YAPISAL"]
    sonuc = []
    print("%-30s | %-28s | %-28s" % ("kare", "ORIJINAL", "90 DERECE DONDURULMUS"))
    for ad in hedefler:
        p = KARE_DIZIN / ad
        img = cv2.imread(str(p))
        lp = etiket_bul(p.stem)
        lab = cv2.imread(str(lp), cv2.IMREAD_UNCHANGED)
        if lab.ndim == 3:
            lab = lab[:, :, 0]
        a = kosum(img, lab)
        b = kosum(cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE),
                  cv2.rotate(lab, cv2.ROTATE_90_CLOCKWISE))
        sonuc.append({"kare": ad, "orijinal": a, "dondurulmus": b})

        def özet(d):
            if d["serit"] is None:
                return "RED %s" % (d["sebep"] or "?")
            return "ROTA serit=%d guven=%.3f wp=%d" % (d["serit"], d["guven"],
                                                       d["wp"])
        print("%-30s | %-28s | %-28s" % (ad[-26:], özet(a), özet(b)))
        sys.stdout.flush()
    n_o = sum(1 for s in sonuc if s["orijinal"]["serit"] is not None)
    n_d = sum(1 for s in sonuc if s["dondurulmus"]["serit"] is not None)
    print("\nORIJINAL rota ureten: %d/%d · DONDURULMUS rota ureten: %d/%d"
          % (n_o, len(sonuc), n_d, len(sonuc)))
    (CIK / "c4_rota_dondur.json").write_text(
        json.dumps({"_ne": "18 YAPISAL karede uretim analyze_path — orijinal vs "
                           "90 derece dondurulmus kadraj (elle cizilen etiket)",
                    "orijinal_rota": n_o, "dondurulmus_rota": n_d,
                    "kareler": sonuc}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
