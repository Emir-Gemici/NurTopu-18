"""CURUTME 7 — dondurmenin kazandirdigi EKSEN mi PARAMETRE mi?

Dondurulmus kadrajda icerik 2160x3840 oldugu icin uretim sabitleri farkli
piksele cevriliyor: bant_h 307 (172 yerine), gereken 43 (77 yerine).
Adil kontrol: ORIJINAL kadraji AYNI PIKSEL parametreleriyle kosmak.
    HEDEF_BANT_ORANI    307/2160 = 0.142130
    BANT_TEMAS_MIN_ORANI 43/3840 = 0.011198
Uc kosum, hepsinde URETIM `analyze_path`, hepsinde ELLE CIZILEN etiket:
  A) ORIJINAL kadraj · URETIM parametresi          (172 / 77)
  B) ORIJINAL kadraj · DONDURULMUSUN parametresi   (307 / 43)
  C) DONDURULMUS kadraj · URETIM parametresi       (fiilen 307 / 43)
B ~= C ise kazanan PARAMETREDIR. B << C ise kazanan EKSENDIR.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import numpy as np

KOK = Path(r"O:\navitas")
sys.path.insert(0, str(KOK / "codes"))
import karar_sozlesmesi as ks  # noqa: E402
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
    tuval, _, icerik = _preprocess(img)
    x0, y0, w, h = icerik
    big = cv2.resize(lab, (w, h), interpolation=cv2.INTER_NEAREST)
    zemin = np.zeros(tuval.shape[:2], np.uint8)
    engel = np.zeros(tuval.shape[:2], np.uint8)
    zemin[y0:y0 + h, x0:x0 + w] = (big == 1).astype(np.uint8)
    engel[y0:y0 + h, x0:x0 + w] = (big == 2).astype(np.uint8)
    s, g, wp, _t, r = analyze_path(zemin, return_clean=True, return_reason=True,
                                   icerik=icerik, engel_mask=engel)
    return {"serit": s, "guven": round(float(g), 4),
            "sebep": None if r is None else r[0],
            "bant_h": ks.hedef_bant_yuksekligi(h),
            "gereken": ks.bant_temasi_gereken_px(w),
            "kb_gecer": bool(s is not None and g >= ks.ROTA_GUVEN_ESIGI)}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    e = json.loads((KOK / "results" / "dji_kirsal" /
                    "bant_tanisi_etiket.json").read_text(encoding="utf-8"))
    hedefler = [r["kare"] for r in e["kareler"] if r["durum"] == "YAPISAL"]
    ORAN0, BAR0 = ks.HEDEF_BANT_ORANI, ks.BANT_TEMAS_MIN_ORANI
    sonuc = []
    print("K-B esigi = %.2f" % ks.ROTA_GUVEN_ESIGI)
    print("%-28s | %-22s | %-22s | %-22s"
          % ("kare", "A orij 172/77", "B orij 307/43", "C dondur (307/43)"))
    for ad in hedefler:
        img = cv2.imread(str(KARE_DIZIN / ad))
        lp = etiket_bul(Path(ad).stem)
        lab = cv2.imread(str(lp), cv2.IMREAD_UNCHANGED)
        if lab.ndim == 3:
            lab = lab[:, :, 0]
        ks.HEDEF_BANT_ORANI, ks.BANT_TEMAS_MIN_ORANI = ORAN0, BAR0
        A = kosum(img, lab)
        ks.HEDEF_BANT_ORANI, ks.BANT_TEMAS_MIN_ORANI = 307 / 2160, 43 / 3840
        B = kosum(img, lab)
        ks.HEDEF_BANT_ORANI, ks.BANT_TEMAS_MIN_ORANI = ORAN0, BAR0
        C = kosum(cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE),
                  cv2.rotate(lab, cv2.ROTATE_90_CLOCKWISE))

        def o(d):
            if d["serit"] is None:
                return "RED %s" % (d["sebep"] or "?")[:17]
            return "ROTA g=%.3f %s" % (d["guven"],
                                       "KB+" if d["kb_gecer"] else "KB-")
        print("%-28s | %-22s | %-22s | %-22s"
              % (ad[-24:], o(A), o(B), o(C)))
        sys.stdout.flush()
        sonuc.append({"kare": ad, "A_orij_uretim": A, "B_orij_gevsek": B,
                      "C_dondurulmus": C})
    for k, ad in (("A_orij_uretim", "A orij 172/77"),
                  ("B_orij_gevsek", "B orij 307/43"),
                  ("C_dondurulmus", "C dondur 307/43")):
        print("%-18s rota: %2d/18 · K-B GECEN: %2d/18"
              % (ad, sum(1 for s in sonuc if s[k]["serit"] is not None),
                 sum(1 for s in sonuc if s[k]["kb_gecer"])))
    (CIK / "c7_eksen_mi_parametre_mi.json").write_text(
        json.dumps({"_ne": "dondurme kazanci EKSEN mi PARAMETRE mi — "
                           "uretim analyze_path, elle cizilen etiket",
                    "kareler": sonuc}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
