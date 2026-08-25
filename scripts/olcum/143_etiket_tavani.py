"""143 — ELLE ETIKET TAVANI: bir kare klasorunun YOLO etiketlerini (uc durumlu maskeden
turetilmis poligonlar) URETIM YOLUNDAN (analyze_path, 126 ile AYNI cagri) gecirir.
Sonuc: her kare icin "etiket rota uretir mi" -> model icin TAVAN ve yanlis-pozitif referansi.

  python 143_etiket_tavani.py --kareler dataset/dji_kirsal_0038_bolum/images/test --cikti results/gece_20260826/test29_etiket_tavani.json
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
sys.path.insert(0, str(KOK / "codes"))
from rpi_inference import analyze_path  # noqa: E402


def etiket_maskeleri(lbl: Path, h: int, w: int):
    """YOLO poligon satirlari -> (trav, engel) (h,w) uint8."""
    trav = np.zeros((h, w), np.uint8)
    engel = np.zeros((h, w), np.uint8)
    if not lbl.is_file():
        return trav, engel
    for satir in lbl.read_text(encoding="utf-8").splitlines():
        v = satir.split()
        if len(v) < 7:
            continue
        c = int(v[0])
        pts = (np.array([float(x) for x in v[1:]], np.float32).reshape(-1, 2) * [w, h]).astype(np.int32)
        cv2.fillPoly(trav if c == 0 else engel, [pts], 1)
    return trav, engel


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kareler", type=Path, required=True)
    ap.add_argument("--cikti", type=Path, required=True)
    a = ap.parse_args()
    kareler = sorted(a.kareler.glob("*.jpg"))
    satirlar = []
    for p in kareler:
        img = cv2.imread(str(p))
        h, w = img.shape[:2]
        yan = max(h, w)
        x0, y0 = (yan - w) // 2, (yan - h) // 2
        icerik = (x0, y0, w, h)
        lbl = p.parent.parent.parent / "labels" / p.parent.name / (p.stem + ".txt")
        t, e = etiket_maskeleri(lbl, h, w)
        trav = np.zeros((yan, yan), np.uint8); trav[y0:y0 + h, x0:x0 + w] = t
        engel = np.zeros((yan, yan), np.uint8); engel[y0:y0 + h, x0:x0 + w] = e
        y = analyze_path(trav, icerik=icerik, engel_mask=engel, mpp=None,
                         return_clean=True, return_reason=True, return_olcum=True)
        yol, _g, wps, _c, red, _o = y
        sebep = red[0] if isinstance(red, tuple) else red
        satirlar.append({"kare": p.name, "etiket_var": bool(t.any()), "sinif0_oran": round(float(t.mean()), 4),
                         "sebep": sebep, "wp": len(wps) if wps else 0, "rota": yol is not None})
        print(p.name, "rota" if yol is not None else sebep, flush=True)
    n_rota = sum(1 for s in satirlar if s["rota"])
    ozet = {"_ne": "ELLE ETIKET TAVANI — uretim yolu (analyze_path, mpp=None) elle etiket maskesiyle",
            "n": len(satirlar), "rota": n_rota, "sebepler": {},
            "kareler": satirlar}
    for s in satirlar:
        k = "ROTA" if s["rota"] else str(s["sebep"])
        ozet["sebepler"][k] = ozet["sebepler"].get(k, 0) + 1
    a.cikti.parent.mkdir(parents=True, exist_ok=True)
    a.cikti.write_text(json.dumps(ozet, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in ozet.items() if k != "kareler"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
