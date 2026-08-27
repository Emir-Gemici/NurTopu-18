"""T163 olcumu (ON_KAYIT SS29): CONTRACTS SS8 cozunurluk sozlesmesi bugun ne diyor?

SS8'in tablosu v17 ile TEK arena karesinde olculmustu ve "imgsz = 640, degistirmek
guvenli DEGIL" diyor. Uretim ise 512'de kosuyor. Bu betik ayni ekseni BUGUNKU
uretim modeliyle ve kabul kumesinden 12 kareyle yeniden olcer.

Her cozunurluk icin: sinif 0 IoU (kumenin kendi YOLO etiketine karsi), icerik
kaplama orani, ve URETIM zincirinin karari (ROTA/ret + serit dogrulugu).
Olcek her kosumda manifestten (kare basina) gelir — uydurulmaz.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[2]
for _y in (KOK / "codes", KOK / "comms"):
    sys.path.insert(0, str(_y))

import cv2  # noqa: E402
import numpy as np  # noqa: E402
import rpi_inference as ri  # noqa: E402

COZUNURLUKLER = (512, 640, 768, 960, 1280)
CONF = 0.30


def _etiket_maskesi(lbl: Path, w: int, h: int):
    m0 = np.zeros((h, w), np.uint8)
    if not lbl.is_file():
        return m0
    for satir in lbl.read_text(encoding="utf-8").splitlines():
        p = satir.split()
        if len(p) < 7 or int(float(p[0])) != 0:
            continue
        k = np.array([float(x) for x in p[1:]], np.float32).reshape(-1, 2)
        k[:, 0] *= w
        k[:, 1] *= h
        cv2.fillPoly(m0, [k.astype(np.int32)], 255)
    return m0


def _iou(a, b):
    a, b = a > 0, b > 0
    birlesim = int(np.count_nonzero(a | b))
    return (int(np.count_nonzero(a & b)) / birlesim) if birlesim else None


def main():
    from ultralytics import YOLO

    defter = json.loads((KOK / "config" / "model_registry.json")
                        .read_text(encoding="utf-8"))
    kume = Path(defter["profiles"]["competition"]["kabul_kumesi"])
    uretim_imgsz = int(defter["profiles"]["competition"]["imgsz"])
    mf = json.loads((kume / "manifest.json").read_text(encoding="utf-8"))
    mpp_harita = {Path(o["cikti"]).name: o["arena"]["mpp"] for o in mf["ornekler"]
                  if isinstance(o.get("arena"), dict) and o["arena"].get("mpp")}
    serit_harita = {Path(o["cikti"]).name: o["arena"].get("acik_serit")
                    for o in mf["ornekler"] if isinstance(o.get("arena"), dict)}

    gorseller = sorted((kume / "images" / "val").glob("*.jpg"))
    adim = max(1, len(gorseller) // 12)
    secilen = gorseller[::adim][:12]
    assert secilen, "kabul kumesi val bos"

    model = YOLO(str(KOK / "models" / "navitas_seg_v36_best.pt"))
    print(f"model v36 · conf {CONF} · {len(secilen)} kare · "
          f"uretim imgsz {uretim_imgsz}", flush=True)

    rapor = {"_ne": "T163 · ON_KAYIT SS29 · CONTRACTS SS8 tazelemesi",
             "uretim_imgsz": uretim_imgsz, "kare": len(secilen),
             "conf": CONF, "cozunurlukler": {}}

    for imgsz in COZUNURLUKLER:
        satirlar = []
        for yol in secilen:
            img = cv2.imread(str(yol))
            sq, small, icerik = ri._preprocess(img)
            yan = sq.shape[0]
            x0, y0, w, h = icerik
            girdi = cv2.resize(sq, (imgsz, imgsz))
            son = model.predict(girdi, imgsz=imgsz, conf=CONF, verbose=False)
            mk = ri._maskeleri_icerige_kirp(ri.get_masks(son, yan, yan), icerik)
            trav, blok = mk[0], mk[1]

            lbl = kume / "labels" / "val" / (yol.stem + ".txt")
            g0 = _etiket_maskesi(lbl, img.shape[1], img.shape[0])
            tavan = np.zeros((yan, yan), np.uint8)
            tavan[y0:y0 + h, x0:x0 + w] = g0

            mpp = mpp_harita.get(yol.name)
            hy, gv, hw, red = ri.analyze_path(trav, icerik=icerik,
                                              engel_mask=blok, mpp=mpp,
                                              return_reason=True)
            yol_no, gv, wps, red = ri._rota_kararini_esikle(hy, gv, hw, red)
            beklenen = serit_harita.get(yol.name)
            icerik_px = w * h
            satirlar.append({
                "kare": yol.name,
                "iou_sinif0": _iou(trav, tavan),
                "kaplama": float(np.count_nonzero(trav[y0:y0 + h, x0:x0 + w])) / icerik_px,
                "yol_no": yol_no, "beklenen_serit": beklenen,
                "serit_dogru": bool(yol_no is not None and yol_no == beklenen),
                "kod": "ROTA" if yol_no is not None else (
                    red[0] if isinstance(red, (tuple, list)) else red),
            })
        iou = [s["iou_sinif0"] for s in satirlar if s["iou_sinif0"] is not None]
        kap = [s["kaplama"] for s in satirlar]
        ozet = {
            "iou_medyan": round(float(np.median(iou)), 4) if iou else None,
            "kaplama_medyan": round(float(np.median(kap)), 4),
            "kaplama_azami": round(float(np.max(kap)), 4),
            "rota": sum(1 for s in satirlar if s["yol_no"] is not None),
            "serit_dogru": sum(1 for s in satirlar if s["serit_dogru"]),
            "n": len(satirlar),
        }
        rapor["cozunurlukler"][str(imgsz)] = {**ozet, "kareler": satirlar}
        yildiz = " <- URETIM" if imgsz == uretim_imgsz else ""
        print(f"imgsz {imgsz:4d}: IoU med {ozet['iou_medyan']} · kaplama med "
              f"{ozet['kaplama_medyan']} (azami {ozet['kaplama_azami']}) · "
              f"ROTA {ozet['rota']}/{ozet['n']} · serit {ozet['serit_dogru']}"
              f"/{ozet['n']}{yildiz}", flush=True)

    cikti = KOK / "results" / "t163" / "olcum.json"
    cikti.parent.mkdir(parents=True, exist_ok=True)
    cikti.write_text(json.dumps(rapor, indent=1, ensure_ascii=False),
                     encoding="utf-8")
    print("yazildi:", cikti)


if __name__ == "__main__":
    main()
