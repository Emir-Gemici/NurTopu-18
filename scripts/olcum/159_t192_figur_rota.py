"""159 — T192 BIRINCIL OLCUT: sartname figurunde ROTA URETILIYOR MU?

ON KAYIT: REVIEW_LOG D-340 (egitimden ONCE yazildi).
  BIRINCIL OLCUT ikilidir: `analyze_path` bu karede rota URETMELIDIR
  (None donmemeli, en az 2 waypoint). ESIK UYDURULMAZ.
  IKINCIL (bilgi, KAPI DEGIL): zemin kaplamasi. Taban %4,4.
  D-186 bu figur uzerinde model TAVANI koymayi zaten reddetmisti; burada
  tavan YOK, yalniz "rota cikiyor mu" sorusu var.

⚠ NE IDDIA ETMEZ: figur, sartnamenin kendi ifadesiyle "tamamen yapay zeka
ile olusturulmustur, gercek alani dogrudan yansitmamaktadir" (D-99). n = 1.
Bu kapi "sahada calisir" DEMEZ; "kaptanin tanidigi resimde rota cikiyor" der.

Kullanim:
  <venv> 159_t192_figur_rota.py --agirlik models/navitas_seg_v36_best.pt
  <venv> 159_t192_figur_rota.py --agirlik A.pt --agirlik B.pt --json cikti.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(KOK / "codes"))

import cv2                                                          # noqa: E402
import numpy as np                                                  # noqa: E402

from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp,     # noqa: E402
                           _preprocess, analyze_path, get_masks)

KARE = KOK / "data" / "arena_referans" / "sartname_s9_arena.png"
TABAN_ZEMIN = 0.044        # v36'nin OLCULEN degeri (D-342) — kiyas icin


def olc(agirlik: Path) -> dict:
    if not KARE.is_file():
        return {"durum": "OLCULEMEDI", "sebep": f"kare yok: {KARE}"}
    im = cv2.imread(str(KARE))
    if im is None:
        return {"durum": "OLCULEMEDI", "sebep": "kare okunamadi"}
    if not Path(agirlik).is_file():
        return {"durum": "OLCULEMEDI", "sebep": f"agirlik yok: {agirlik}"}

    from ultralytics import YOLO
    model = YOLO(str(agirlik), task="segment")
    sq, small, icerik = _preprocess(im)
    res = model.predict(small, imgsz=INFER_SIZE, conf=0.30, verbose=False)
    mk = _maskeleri_icerige_kirp(get_masks(res, sq.shape[0], sq.shape[1]), icerik)
    zemin = mk[0]

    yol, guven, wps, red = analyze_path(
        zemin, icerik=icerik, engel_mask=mk.get(1),
        mpp=50.0 / im.shape[1], return_reason=True)
    kod = (red[0] if isinstance(red, (tuple, list)) else red)

    x0, y0, cw, ch = icerik
    z = zemin[y0:y0 + ch, x0:x0 + cw] > 0
    e = mk.get(1)
    e = (e[y0:y0 + ch, x0:x0 + cw] > 0) if e is not None else np.zeros_like(z)

    rota_var = bool(red is None and wps is not None and len(wps) >= 2)
    return {
        "durum": "GECTI" if rota_var else "DUSTU",
        "agirlik": Path(agirlik).name,
        "rota_uretildi": rota_var,
        "waypoint": int(len(wps)) if wps is not None else 0,
        "guven": round(float(guven), 3) if guven is not None else None,
        "ret_sebebi": kod,
        "zemin_kaplamasi": round(float(z.mean()), 4),
        "engel_kaplamasi": round(float(e.mean()), 4),
        "cekimser": round(float((~(z | e)).mean()), 4),
        "_taban_zemin_v36": TABAN_ZEMIN,
        "_olcut": ("BIRINCIL: rota URETILMELI (ikili, esik yok). "
                   "Zemin kaplamasi BILGIDIR, kapi DEGIL (D-186)."),
        "_n": 1,
        "_uyari": ("figur YAPAY ZEKA urunudur (D-99); bu olcum 'sahada "
                   "calisir' DEMEZ."),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--agirlik", type=Path, action="append", required=True)
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args()

    hepsi = []
    for w in a.agirlik:
        d = olc(w)
        hepsi.append(d)
        if d["durum"] == "OLCULEMEDI":
            print(f"  {w.name:32s} OLCULEMEDI — {d['sebep']}")
            continue
        print(f"  {d['agirlik']:32s} {d['durum']:6s} "
              f"rota={'VAR' if d['rota_uretildi'] else 'YOK'} "
              f"wp={d['waypoint']:3d} · zemin %{100*d['zemin_kaplamasi']:.1f} "
              f"· cekimser %{100*d['cekimser']:.1f} · ret={d['ret_sebebi']}")
    if a.json:
        a.json.parent.mkdir(parents=True, exist_ok=True)
        a.json.write_text(json.dumps(hepsi, indent=1, ensure_ascii=False),
                          encoding="utf-8")
        print(f"json -> {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
