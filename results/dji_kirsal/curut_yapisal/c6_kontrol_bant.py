"""CURUTME 6 — KENDI CURUTMEMI CURUT: 90 derece dondurme testi HILELI mi?

Dondurulmus kadrajda icerik 2160x3840 olur; bu YALNIZ ekseni degil PARAMETRELERI
de degistirir:
    bant_h   : 0.08*2160 = 172 px  ->  0.08*3840 = 307 px  (bant 1.8x KALIN)
    gereken  : 0.02*3840 =  77 px  ->  0.02*2160 =  43 px  (bar 1.8x DUSUK)
Yani dondurulmus test iki yonden de DAHA KOLAY. Eger ORIJINAL kadraj bu gevsek
parametrelerle de gecmiyorsa, dondurmenin kazandirdigi sey EKSENDIR.
Gecerse, kazandiran sey PARAMETRE GEVSEMESIDIR ve curutmem coker.

Ayrica: bant kalinligini tarayip 'bant COK INCE' hipotezini olcerim.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import numpy as np

KOK = Path(r"O:\navitas")
sys.path.insert(0, str(KOK / "codes"))
from rpi_inference import _preprocess  # noqa: E402

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
    hedefler = [r["kare"] for r in e["kareler"] if r["durum"] == "YAPISAL"]
    BANTLAR = [172, 307, 432, 648, 1080]   # %8, %14.2, %20, %30, %50
    BARLAR = [77, 43, 20, 1]
    say = {(b, g): 0 for b in BANTLAR for g in BARLAR}
    satir = []
    for ad in hedefler:
        p = KARE_DIZIN / ad
        img = cv2.imread(str(p))
        lp = etiket_bul(p.stem)
        lab = cv2.imread(str(lp), cv2.IMREAD_UNCHANGED)
        if lab.ndim == 3:
            lab = lab[:, :, 0]
        _, _, icerik = _preprocess(img)
        x0, y0, w, h = icerik
        big = cv2.resize(lab, (w, h), interpolation=cv2.INTER_NEAREST)
        s0 = (big == 1).astype(np.uint8)
        # URETIMLE AYNI: yalniz en buyuk bilesen
        n, etk, st, _ = cv2.connectedComponentsWithStats(s0, 8)
        d = {"kare": ad}
        if n > 1:
            enb = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
            enbm = (etk == enb).astype(np.uint8)
        else:
            enbm = s0
        for bh in BANTLAR:
            ust = int(np.count_nonzero(enbm[:bh, :].any(axis=0)))
            alt = int(np.count_nonzero(enbm[h - bh:, :].any(axis=0)))
            tust = int(np.count_nonzero(s0[:bh, :].any(axis=0)))
            talt = int(np.count_nonzero(s0[h - bh:, :].any(axis=0)))
            d["bh%d" % bh] = {"enb_ust": ust, "enb_alt": alt,
                              "tam_ust": tust, "tam_alt": talt}
            for g in BARLAR:
                if tust >= g and talt >= g:
                    say[(bh, g)] += 1
        satir.append(d)
    print("ORIJINAL kadrajda, elle cizilen SINIF0 (TAM maske), 18 YAPISAL kare:")
    print("bant_h \\ gereken  " + "".join("%8d" % g for g in BARLAR))
    for bh in BANTLAR:
        print("%5d px (%%%4.1f)   " % (bh, 100.0 * bh / 2160)
              + "".join("%8d" % say[(bh, g)] for g in BARLAR))
    print("\n(hucre = 18 karenin kacinda ALT ve UST bandin IKISINE birden temas)")
    print("URETIM hucresi = bant_h 172, gereken 77")
    print("DONDURULMUS testin kullandigi gevsek parametre = 307 / 43")
    (CIK / "c6_kontrol_bant.json").write_text(
        json.dumps({"_ne": "bant kalinligi x temas bari duyarlilik taramasi "
                           "(orijinal kadraj, 18 YAPISAL kare)",
                    "izgara": {"%d/%d" % k: v for k, v in say.items()},
                    "kareler": satir}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
