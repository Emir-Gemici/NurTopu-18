"""149 — KOMPOZIT KUMEDE TAVAN vs MODEL (ON_KAYIT §19 devami).

148 olcumu: `kompozit` kaynagindaki 9 karenin 9'unda rota YOK
(GORUS_HATTI_KOPUK 4, UC_BANT_TEMAS_YOK 5) — ve sebep OLCEK DEGIL (manifest mpp var).
Soru: kusur MODELDE mi (maske kotu) yoksa ROTA ALGORITMASINDA mi (yer gercegi
maskesiyle bile rota cikmiyor)?

Tavan = kumenin KENDI YOLO etiketlerinden (sinif 0 = gecilebilir, sinif 1 = engel)
rasterlenen maske. Model ile TAM AYNI `analyze_path` cagrisi kosulur.

Kullanim:
  python scripts/olcum/149_kompozit_tavan.py
  python scripts/olcum/149_kompozit_tavan.py --modeller models/navitas_seg_v36_best.pt models/navitas_seg_v35_best.pt
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(KOK / "comms"))
sys.path.insert(0, str(KOK / "codes"))

import cv2  # noqa: E402
import numpy as np  # noqa: E402

KUME = KOK / "data" / "arena_kompozit"


def _kod(red):
    if red is None:
        return "ROTA"
    return red[0] if isinstance(red, (tuple, list)) else str(red)


def _metin(red):
    if red is None:
        return None
    return " | ".join(str(x) for x in red) if isinstance(red, (tuple, list)) else str(red)


def _etiket_maskeleri(lbl_yolu: Path, w: int, h: int):
    """YOLO poligon etiketlerinden (sinif0, sinif1) ikili maske."""
    m0 = np.zeros((h, w), np.uint8)
    m1 = np.zeros((h, w), np.uint8)
    for satir in lbl_yolu.read_text(encoding="utf-8").splitlines():
        p = satir.split()
        if len(p) < 7:
            continue
        sinif = int(float(p[0]))
        koord = np.array([float(x) for x in p[1:]], np.float32).reshape(-1, 2)
        koord[:, 0] *= w
        koord[:, 1] *= h
        cv2.fillPoly(m0 if sinif == 0 else m1, [koord.astype(np.int32)], 255)
    return m0, m1


def _tuvale_koy(maske, icerik, yan):
    x0, y0, w, h = icerik
    tuval = np.zeros((yan, yan), np.uint8)
    tuval[y0:y0 + h, x0:x0 + w] = maske
    return tuval


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modeller", nargs="*", default=["models/navitas_seg_v36_best.pt",
                                                     "models/navitas_seg_v35_best.pt",
                                                     "models/navitas_seg_v34_best.pt"])
    ap.add_argument("--cikti", default="results/gece_20260826/kompozit_tavan.json")
    a = ap.parse_args()

    from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp, _preprocess,
                               _rota_kararini_esikle, analyze_path, get_masks)
    import yks_gui

    o = object.__new__(yks_gui.YksArayuz)
    o.algi_kaynak = "kompozit"
    olcekler = o._kompozit_olcekleri()

    gorseller = sorted(p for p in (KUME / "images").rglob("*")
                       if p.suffix.lower() in (".jpg", ".png", ".jpeg"))
    assert gorseller, "kompozit gorsel yok"

    rapor = {"kume": str(KUME), "kare": len(gorseller), "kosumlar": {}}

    def kos(ad, maske_uret):
        kareler = []
        for yol in gorseller:
            img = cv2.imread(str(yol))
            sq, small, icerik = _preprocess(img)
            trav, blok = maske_uret(img, sq, small, icerik, yol)
            mpp = olcekler.get(yol.name)
            (hy, gv, hw, kor, red, olc) = analyze_path(
                trav, icerik=icerik, engel_mask=blok, mpp=mpp,
                return_clean=True, return_reason=True, return_olcum=True)
            yol_no, gv, wps, red = _rota_kararini_esikle(hy, gv, hw, red)
            # uc bant temasi: koridorun alt/ust bant piksel sayisi ret metninde
            kareler.append({"kare": yol.name, "mpp": mpp, "yol_no": yol_no,
                            "kod": _kod(red) if yol_no is None else "ROTA",
                            "sebep": _metin(red),
                            "zemin_px": int(np.count_nonzero(trav)),
                            "engel_px": int(np.count_nonzero(blok)),
                            "wp": len(wps or [])})
        say = {}
        for k in kareler:
            say[k["kod"]] = say.get(k["kod"], 0) + 1
        rapor["kosumlar"][ad] = {"dagilim": say, "kareler": kareler}
        print(f"{ad}: {say}", flush=True)

    # 1) TAVAN — kumenin kendi etiketleri
    def tavan(img, sq, small, icerik, yol):
        lbl = KUME / "labels" / yol.parent.name / (yol.stem + ".txt")
        assert lbl.is_file(), lbl
        h, w = img.shape[:2]
        m0, m1 = _etiket_maskeleri(lbl, w, h)
        yan = sq.shape[0]
        trav = _tuvale_koy(m0, icerik, yan)
        blok = _tuvale_koy(m1, icerik, yan)
        return trav, blok
    kos("TAVAN(etiket)", tavan)

    # 2) modeller
    from ultralytics import YOLO
    for m in a.modeller:
        yolm = Path(m)
        if not yolm.is_absolute():
            yolm = KOK / m
        if not yolm.is_file():
            print(f"{m}: AGIRLIK YOK — atlandi", flush=True)
            continue
        model = YOLO(str(yolm))

        def modelli(img, sq, small, icerik, yol, _model=model):
            h, w = sq.shape[:2]
            sonuc = _model.predict(small, imgsz=INFER_SIZE,
                                   conf=yks_gui.YksArayuz.ALGI_PREDICT_CONF,
                                   verbose=False)
            mk = _maskeleri_icerige_kirp(get_masks(sonuc, h, w), icerik)
            return mk[0], mk[1]
        kos(yolm.stem, modelli)

    cikti = KOK / a.cikti
    cikti.parent.mkdir(parents=True, exist_ok=True)
    cikti.write_text(json.dumps(rapor, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"yazildi: {cikti}")


if __name__ == "__main__":
    main()
