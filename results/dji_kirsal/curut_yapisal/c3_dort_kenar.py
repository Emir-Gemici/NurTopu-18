"""CURUTME 3 — (a) letterbox/bant aritmetigi dogru mu, (b) zemin YOK mu yoksa
YANLIS YONDE mi?

(a) `_preprocess` + `_maskeleri_icerige_kirp` gercekten kosulur; icerik kutusu
    ve bant satirlari URETIM fonksiyonlariyla yazdirilir.
(b) Ayni %2 esigi DORT kenara birden uygulanir (ust/alt/sol/sag). Ustabasinin
    hukmu "zemin kareyi kat etmiyor". Eger sol-sag kat ediliyorsa zemin VAR,
    yalnizca bant ekseniyle DIK duruyordur -> sebep 'zemin yok' degil
    'kadraj/rota ekseni'dir.
Ek: 90 derece dondurulmus kare ayni testi geciyor mu?
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
from rpi_inference import _maskeleri_icerige_kirp, _preprocess  # noqa: E402

KARE_DIZIN = KOK / "dataset" / "dji_kirsal" / "images" / "val"
ETIKET_KOK = KOK / "results" / "dji_20260822" / "f5_olcek"
CIK = KOK / "results" / "dji_kirsal" / "curut_yapisal"


def etiket_bul(stem):
    for alt in ("A", "B", "C", "D"):
        p = ETIKET_KOK / alt / (stem + "_uc.png")
        if p.exists():
            return p
    return None


def kenar_temaslari(maske, icerik):
    """(ust, alt, sol, sag) benzersiz sutun/satir temasi."""
    x0, y0, w, h = icerik
    bh = hedef_bant_yuksekligi(h)
    bw = hedef_bant_yuksekligi(w)  # ayni %8 orani, yatay karsiligi
    ic = maske[y0:y0 + h, x0:x0 + w]
    return {
        "ust": int(np.count_nonzero(ic[:bh, :].any(axis=0))),
        "alt": int(np.count_nonzero(ic[h - bh:, :].any(axis=0))),
        "sol": int(np.count_nonzero(ic[:, :bw].any(axis=1))),
        "sag": int(np.count_nonzero(ic[:, w - bw:].any(axis=1))),
    }


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    kareler = sorted(KARE_DIZIN.glob("*.jpg"))
    ilk = True
    satir = []
    for p in kareler:
        img = cv2.imread(str(p))
        H, W = img.shape[:2]
        tuval, small, icerik = _preprocess(img)
        x0, y0, w, h = icerik
        if ilk:
            print("URETIM ARITMETIGI (%s)" % p.name)
            print("  goruntu %dx%d -> tuval %s · icerik=(x0=%d,y0=%d,w=%d,h=%d)"
                  % (W, H, tuval.shape[:2], x0, y0, w, h))
            print("  bant_h=%d  (%.4f · h)  gereken_temas=%d px (%.4f · w)"
                  % (hedef_bant_yuksekligi(h), hedef_bant_yuksekligi(h) / h,
                     bant_temasi_gereken_px(w), bant_temasi_gereken_px(w) / w))
            print("  UST bant tuval satirlari [%d,%d) = ORIJINAL satir [%d,%d)"
                  % (y0, y0 + hedef_bant_yuksekligi(h), 0,
                     hedef_bant_yuksekligi(h)))
            print("  ALT bant tuval satirlari [%d,%d) = ORIJINAL satir [%d,%d)"
                  % (y0 + h - hedef_bant_yuksekligi(h), y0 + h,
                     h - hedef_bant_yuksekligi(h), h))
            # kaydirma sinamasi: bilinen desen tuvale konup geri okunur
            sonda = np.zeros((H, W), np.uint8)
            sonda[:hedef_bant_yuksekligi(h), :] = 1     # orijinalin en ustu
            sonda[H - hedef_bant_yuksekligi(h):, :] = 1  # ve en alti
            tv = np.zeros(tuval.shape[:2], np.uint8)
            tv[y0:y0 + h, x0:x0 + w] = sonda
            tv = _maskeleri_icerige_kirp({0: tv}, icerik)[0]
            kt = kenar_temaslari(tv, icerik)
            print("  SONDA (orijinalin ust+alt %d satiri): ust=%d alt=%d "
                  "-> kaydirma %s" % (hedef_bant_yuksekligi(h), kt["ust"],
                                      kt["alt"],
                                      "YOK" if kt["ust"] == w and kt["alt"] == w
                                      else "VAR!"))
            print()
            ilk = False
        lp = etiket_bul(p.stem)
        if lp is None:
            continue
        lab = cv2.imread(str(lp), cv2.IMREAD_UNCHANGED)
        if lab.ndim == 3:
            lab = lab[:, :, 0]
        büyük = cv2.resize(lab, (w, h), interpolation=cv2.INTER_NEAREST)
        s0 = np.zeros(tuval.shape[:2], np.uint8)
        s0[y0:y0 + h, x0:x0 + w] = (büyük == 1).astype(np.uint8)
        s0 = _maskeleri_icerige_kirp({0: s0}, icerik)[0]
        gereken = bant_temasi_gereken_px(w)
        kt = kenar_temaslari(s0, icerik)
        # 90 derece dondurulmus hal (sol/sag -> ust/alt olur)
        satir.append({"kare": p.name, "gereken": gereken, **kt,
                      "dikey_ok": kt["ust"] >= gereken and kt["alt"] >= gereken,
                      "yatay_ok": kt["sol"] >= gereken and kt["sag"] >= gereken})
    (CIK / "c3_dort_kenar.json").write_text(
        json.dumps({"_ne": "elle cizilen SINIF0 icin dort kenar temasi",
                    "kareler": satir}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print("yazildi c3_dort_kenar.json (%d kare)" % len(satir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
