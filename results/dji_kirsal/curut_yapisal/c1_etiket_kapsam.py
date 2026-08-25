"""CURUTME 1 — YAPISAL hukmu ETIKET KAPSAMI artifakti mi?

Iddia (I): 18 kare YAPISAL cunku zemin kareyi alttan uste kat etmiyor.
Sinama: etiket PNG'lerinde 0 = ETIKETSIZ. Eger bos ucta 0 (ETIKETSIZ)
hakimse, "zemin yok" degil "insan cizmemis" demektir -> hukum artifakt.
Karsi olasilik: bos ucta 2 (SINIF1 ENGEL) veya gercek arazi hakimse
ustabasi haklidir.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import numpy as np

KOK = Path(r"O:\navitas")
sys.path.insert(0, str(KOK / "codes"))
from karar_sozlesmesi import (bant_temasi_gereken_px,  # noqa: E402
                              hedef_bant_yuksekligi)

KARE_DIZIN = KOK / "dataset" / "dji_kirsal" / "images" / "val"
ETIKET_KOK = KOK / "results" / "dji_20260822" / "f5_olcek"
CIK = KOK / "results" / "dji_kirsal" / "curut_yapisal"


def etiket_haritasi():
    h = {}
    for alt in ("A", "B", "C", "D"):
        for p in (ETIKET_KOK / alt).glob("*_uc.png"):
            h.setdefault(p.name[:-len("_uc.png")], []).append(p)
    return h


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    hm = etiket_haritasi()
    kareler = sorted(KARE_DIZIN.glob("*.jpg"))
    satir = []
    boyutlar = set()
    cift = 0
    for p in kareler:
        stem = p.stem
        yollar = hm.get(stem)
        img = cv2.imread(str(p))
        boyutlar.add(img.shape[:2])
        if not yollar:
            satir.append({"kare": p.name, "etiket": None})
            continue
        if len(yollar) > 1:
            cift += 1
        lp = sorted(yollar)[0]
        lab = cv2.imread(str(lp), cv2.IMREAD_UNCHANGED)
        if lab.ndim == 3:
            lab = lab[:, :, 0]
        H, W = img.shape[:2]
        # etiket 960x540 -> icerik olcegine NEAREST buyut (deger korunur)
        büyük = cv2.resize(lab, (W, H), interpolation=cv2.INTER_NEAREST)
        bant_h = hedef_bant_yuksekligi(H)
        gereken = bant_temasi_gereken_px(W)
        ust = büyük[:bant_h, :]
        alt = büyük[H - bant_h:, :]
        d = {"kare": p.name, "etiket_dosya": str(lp), "etiket_sekli": list(lab.shape),
             "H": H, "W": W, "bant_h": bant_h, "gereken": gereken}
        for ad, b in (("ust", ust), ("alt", alt)):
            top = b.size
            d[f"{ad}_etiketsiz_oran"] = round(float((b == 0).sum()) / top, 4)
            d[f"{ad}_sinif0_oran"] = round(float((b == 1).sum()) / top, 4)
            d[f"{ad}_sinif1_oran"] = round(float((b == 2).sum()) / top, 4)
            d[f"{ad}_sinif0_sutun"] = int(np.count_nonzero((b == 1).any(axis=0)))
            d[f"{ad}_etiketli_sutun"] = int(np.count_nonzero((b > 0).any(axis=0)))
        d["kare_etiketsiz_oran"] = round(float((büyük == 0).sum()) / büyük.size, 4)
        d["kare_sinif0_oran"] = round(float((büyük == 1).sum()) / büyük.size, 4)
        d["kare_sinif1_oran"] = round(float((büyük == 2).sum()) / büyük.size, 4)
        # sinif0'in dikey yayilimi: en ust ve en alt satir
        s0 = (büyük == 1)
        satirlar_var = np.nonzero(s0.any(axis=1))[0]
        if satirlar_var.size:
            d["s0_ust_satir"] = int(satirlar_var[0])
            d["s0_alt_satir"] = int(satirlar_var[-1])
            d["s0_dikey_kapsam"] = round(
                float(satirlar_var[-1] - satirlar_var[0] + 1) / H, 4)
        else:
            d["s0_ust_satir"] = d["s0_alt_satir"] = -1
            d["s0_dikey_kapsam"] = 0.0
        # etiketli (0 disi) bolgenin dikey yayilimi
        et = (büyük > 0)
        er = np.nonzero(et.any(axis=1))[0]
        if er.size:
            d["et_ust_satir"] = int(er[0])
            d["et_alt_satir"] = int(er[-1])
            d["et_dikey_kapsam"] = round(float(er[-1] - er[0] + 1) / H, 4)
        else:
            d["et_ust_satir"] = d["et_alt_satir"] = -1
            d["et_dikey_kapsam"] = 0.0
        satir.append(d)
    CIK.mkdir(parents=True, exist_ok=True)
    (CIK / "c1_etiket_kapsam.json").write_text(
        json.dumps({"_ne": "etiket kapsami — YAPISAL artifakt sinamasi",
                    "kare_boyutlari": [list(b) for b in boyutlar],
                    "cift_etiketli_kare": cift,
                    "kareler": satir}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    var = [s for s in satir if s.get("etiket")is not None or "H" in s]
    print("kare %d · etiketli %d · cift etiket %d · boyutlar %s"
          % (len(satir), len([s for s in satir if "H" in s]), cift, boyutlar))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
