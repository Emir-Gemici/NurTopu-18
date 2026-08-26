"""T36b kapanma olcumu (ON_KAYIT §25): ORACLE ve MODEL kollari ayri ayri.

Kompozit kumenin 9 karesinde:
  ORACLE : kumenin kendi YOLO etiketinden maske -> analyze_path -> yayinlanan `road`
  MODEL  : v36 maskesi -> ayni zincir
Ikisi de manifestteki `acik_serit` ile kiyaslanir.
"""
import json
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[2]
for y in (KOK / "comms", KOK / "codes"):
    sys.path.insert(0, str(y))

import cv2  # noqa: E402
import numpy as np  # noqa: E402
import rpi_inference as ri  # noqa: E402
import yks_gui  # noqa: E402

KUME = KOK / "data" / "arena_kompozit"


def etiket_maskeleri(lbl, w, h):
    m0 = np.zeros((h, w), np.uint8)
    m1 = np.zeros((h, w), np.uint8)
    for satir in lbl.read_text(encoding="utf-8").splitlines():
        p = satir.split()
        if len(p) < 7:
            continue
        c = int(float(p[0]))
        k = np.array([float(x) for x in p[1:]], np.float32).reshape(-1, 2)
        k[:, 0] *= w
        k[:, 1] *= h
        cv2.fillPoly(m0 if c == 0 else m1, [k.astype(np.int32)], 255)
    return m0, m1


def main():
    o = object.__new__(yks_gui.YksArayuz)
    o.algi_kaynak = "kompozit"
    gercek = o._kompozit_yer_gercegi()          # {dosya: beklenen_acik_serit}
    olcekler = o._kompozit_olcekleri()
    model = None
    gorseller = sorted(p for p in (KUME / "images").rglob("*")
                       if p.suffix.lower() in (".jpg", ".png"))
    rapor = {"kare": len(gorseller), "kollar": {}}

    for kol in ("ORACLE", "MODEL"):
        if kol == "MODEL" and model is None:
            from ultralytics import YOLO
            model = YOLO(str(KOK / "models" / yks_gui.YksArayuz.ALGI_MODEL_DOSYA))
        satirlar = []
        for yol in gorseller:
            img = cv2.imread(str(yol))
            sq, small, icerik = ri._preprocess(img)
            yan = sq.shape[0]
            x0, y0, w, h = icerik
            if kol == "ORACLE":
                lbl = KUME / "labels" / yol.parent.name / (yol.stem + ".txt")
                g0, g1 = etiket_maskeleri(lbl, img.shape[1], img.shape[0])
                trav = np.zeros((yan, yan), np.uint8)
                blok = np.zeros((yan, yan), np.uint8)
                trav[y0:y0 + h, x0:x0 + w] = g0
                blok[y0:y0 + h, x0:x0 + w] = g1
            else:
                sonuc = model.predict(small, imgsz=ri.INFER_SIZE,
                                      conf=yks_gui.YksArayuz.ALGI_PREDICT_CONF,
                                      verbose=False)
                mk = ri._maskeleri_icerige_kirp(ri.get_masks(sonuc, yan, yan), icerik)
                trav, blok = mk[0], mk[1]
            mpp = olcekler.get(yol.name)
            hy, gv, hw, red = ri.analyze_path(trav, icerik=icerik, engel_mask=blok,
                                              mpp=mpp, return_reason=True)
            yol_no, gv, wps, red = ri._rota_kararini_esikle(hy, gv, hw, red)
            beklenen = gercek.get(yol.name)
            satirlar.append({
                "kare": yol.name, "beklenen_serit": beklenen,
                "yayinlanan_road": yol_no, "guven": round(float(gv), 3),
                "ret": (red[0] if isinstance(red, tuple) else red),
                "dogru": bool(yol_no is not None and yol_no == beklenen),
                "ret_mi": bool(yol_no is None),
            })
        dogru = sum(1 for s in satirlar if s["dogru"])
        ret = sum(1 for s in satirlar if s["ret_mi"])
        rapor["kollar"][kol] = {"dogru": dogru, "ret": ret,
                                "n": len(satirlar), "kareler": satirlar}
        print(f"{kol:7s} DOGRU {dogru}/{len(satirlar)} · RET {ret}", flush=True)
        for s in satirlar:
            print(f"   {s['kare'][:44]:44s} beklenen={s['beklenen_serit']} "
                  f"yayin={s['yayinlanan_road']} guven={s['guven']} {s['ret'] or ''}")

    p = KOK / "results" / "t36b" / "olcum.json"
    p.write_text(json.dumps(rapor, indent=1, ensure_ascii=False), encoding="utf-8")
    print("yazildi:", p)


if __name__ == "__main__":
    main()
