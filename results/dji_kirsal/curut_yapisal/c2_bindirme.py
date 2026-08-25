"""CURUTME 2 — D-80 bindirmesi: YAPISAL karelerde BOS UCTA gercekten ne var?

Yesil = SINIF0 (surulebilir) · Kirmizi = SINIF1 (engel) · Bindirmesiz = ETIKETSIZ
Sari cizgiler = ust/alt uc bantlarinin sinirlari (icerik yuksekliginin %8'i).
"""
from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np

KOK = Path(r"O:\navitas")
sys.path.insert(0, str(KOK / "codes"))
from karar_sozlesmesi import hedef_bant_yuksekligi  # noqa: E402

KARE_DIZIN = KOK / "dataset" / "dji_kirsal" / "images" / "val"
ETIKET_KOK = KOK / "results" / "dji_20260822" / "f5_olcek"
CIK = KOK / "results" / "dji_kirsal" / "curut_yapisal" / "bindirme"

HEDEFLER = sys.argv[1:]


def etiket_bul(stem):
    for alt in ("A", "B", "C", "D"):
        p = ETIKET_KOK / alt / (stem + "_uc.png")
        if p.exists():
            return p
    return None


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    CIK.mkdir(parents=True, exist_ok=True)
    for hedef in HEDEFLER:
        eslesen = sorted(KARE_DIZIN.glob("*%s*.jpg" % hedef))
        if not eslesen:
            print("bulunamadi: %s" % hedef)
            continue
        p = eslesen[0]
        img = cv2.imread(str(p))
        H, W = img.shape[:2]
        lp = etiket_bul(p.stem)
        lab = cv2.imread(str(lp), cv2.IMREAD_UNCHANGED)
        if lab.ndim == 3:
            lab = lab[:, :, 0]
        büyük = cv2.resize(lab, (W, H), interpolation=cv2.INTER_NEAREST)
        vis = img.copy()
        renk = np.zeros_like(img)
        renk[büyük == 1] = (0, 255, 0)
        renk[büyük == 2] = (0, 0, 255)
        m = (büyük > 0)
        vis[m] = cv2.addWeighted(img, 0.55, renk, 0.45, 0)[m]
        bh = hedef_bant_yuksekligi(H)
        cv2.line(vis, (0, bh), (W, bh), (0, 255, 255), 6)
        cv2.line(vis, (0, H - bh), (W, H - bh), (0, 255, 255), 6)
        cv2.putText(vis, "UST BANT", (30, bh - 20), cv2.FONT_HERSHEY_SIMPLEX,
                    2.2, (0, 255, 255), 5)
        cv2.putText(vis, "ALT BANT", (30, H - bh + 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 2.2, (0, 255, 255), 5)
        kucuk = cv2.resize(vis, (1152, 648))
        out = CIK / ("%s_bindirme.png" % hedef)
        cv2.imwrite(str(out), kucuk)
        # yan yana: bindirmesiz kucuk kopya
        ham = cv2.resize(img, (1152, 648))
        cv2.imwrite(str(CIK / ("%s_ham.png" % hedef)), ham)
        print("yazildi %s  (%s)" % (out.name, p.name))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
