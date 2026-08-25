"""CURUTME 9 — MEKANIZMA: YAPISAL kareler 'zemin yok' kareleri mi, yoksa
'koridor bant eksenine DIK' kareleri mi?

Olcum: elle cizilen SINIF0'in EN BUYUK bileseninin ikinci derece momentlerinden
ana eksen acisi (0 = YATAY, 90 = DIKEY). Saf OpenCV/NumPy.
Ek olcum: zemin kutlesi (alan orani) — 'zemin yok' hipotezi bunun DUSUK
olmasini gerektirir.
"""
from __future__ import annotations

import json
import math
import statistics as st
import sys
from pathlib import Path

import cv2
import numpy as np

KOK = Path(r"O:\navitas")
KARE_DIZIN = KOK / "dataset" / "dji_kirsal" / "images" / "val"
ETIKET_KOK = KOK / "results" / "dji_20260822" / "f5_olcek"
CIK = KOK / "results" / "dji_kirsal" / "curut_yapisal"


def etiket_bul(stem):
    for alt in ("A", "B", "C", "D"):
        p = ETIKET_KOK / alt / (stem + "_uc.png")
        if p.exists():
            return p
    return None


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    e = json.loads((KOK / "results" / "dji_kirsal" /
                    "bant_tanisi_etiket.json").read_text(encoding="utf-8"))
    dur = {r["kare"]: r["durum"] for r in e["kareler"]}
    grup = {}
    satir = []
    for p in sorted(KARE_DIZIN.glob("*.jpg")):
        lp = etiket_bul(p.stem)
        if lp is None:
            continue
        lab = cv2.imread(str(lp), cv2.IMREAD_UNCHANGED)
        if lab.ndim == 3:
            lab = lab[:, :, 0]
        # etiket kendi cozunurlugunde olculur (aci ve oran olcek-degismez;
        # 960x540 ile 3840x2160 ayni en-boy orani)
        s0 = (lab == 1).astype(np.uint8)
        H, W = s0.shape
        if s0.sum() == 0:
            continue
        n, etk, stt, _ = cv2.connectedComponentsWithStats(s0, 8)
        enb = 1 + int(np.argmax(stt[1:, cv2.CC_STAT_AREA]))
        m = (etk == enb).astype(np.uint8)
        mo = cv2.moments(m, binaryImage=True)
        mu20 = mo["mu20"] / mo["m00"]
        mu02 = mo["mu02"] / mo["m00"]
        mu11 = mo["mu11"] / mo["m00"]
        # goruntu koordinatlarinda y asagi; aciyi 0=YATAY, 90=DIKEY olarak ver
        aci = 0.5 * math.atan2(2 * mu11, mu20 - mu02)
        aci_d = abs(math.degrees(aci))
        if aci_d > 90:
            aci_d = 180 - aci_d
        x, y, w_, h_, alan = stt[enb]
        d = {"kare": p.name, "durum": dur.get(p.name, "SINIF0_YOK"),
             "eksen_aci_derece": round(aci_d, 1),
             "enb_alan_orani": round(float(alan) / (H * W), 4),
             "s0_alan_orani": round(float(s0.sum()) / (H * W), 4),
             "enb_dikey_yayilim": round(h_ / H, 3),
             "enb_yatay_yayilim": round(w_ / W, 3)}
        satir.append(d)
        grup.setdefault(d["durum"], []).append(d)
    print("%-11s %3s | %-24s | %-22s | %-22s"
          % ("durum", "n", "ana eksen acisi (0=yatay)", "SINIF0 alan orani",
             "enb dikey/yatay yayilim"))
    for g in ("GECER", "PARCALILIK", "YAPISAL"):
        v = grup.get(g, [])
        if not v:
            continue
        a = sorted(x["eksen_aci_derece"] for x in v)
        al = sorted(x["s0_alan_orani"] for x in v)
        dy = sorted(x["enb_dikey_yayilim"] for x in v)
        yy = sorted(x["enb_yatay_yayilim"] for x in v)
        print("%-11s %3d | p50 %5.1f  (min %4.1f maks %4.1f) | p50 %.3f "
              "(min %.3f) | %.2f / %.2f"
              % (g, len(v), a[len(a) // 2], a[0], a[-1],
                 al[len(al) // 2], al[0], dy[len(dy) // 2], yy[len(yy) // 2]))
    print("\nYATAYA YAKIN koridor (aci < 30 derece) orani:")
    for g in ("GECER", "PARCALILIK", "YAPISAL"):
        v = grup.get(g, [])
        if v:
            print("  %-11s %2d/%2d" % (g, sum(1 for x in v
                                              if x["eksen_aci_derece"] < 30),
                                       len(v)))
    (CIK / "c9_koridor_ekseni.json").write_text(
        json.dumps({"_ne": "elle cizilen SINIF0 en buyuk bileseninin ana eksen "
                           "acisi ve kutlesi", "kareler": satir},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
