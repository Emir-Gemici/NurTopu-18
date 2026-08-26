"""150 — T159: CIKARIM GEOMETRISI (ON_KAYIT §20). TANISAL — uretim kodu DEGISMEZ.

Soru: kompozit 9 karede tavan 8/9 rota verirken v36 0/9 veriyor. Sebep modelin
gercek domende zayifligi mi, yoksa CIKARIM GEOMETRISI mi (1024x576 kare
1024x1024 tuvale letterbox edilip 512'ye kuculunce yol yari olcege iniyor)?

Dort kip, ayni model, ayni `analyze_path`:
  A taban : letterbox (_preprocess) -> imgsz 512      [BUGUNKU URETIM]
  B       : letterbox               -> imgsz 1024
  D       : letterbox               -> imgsz 768
  C       : letterbox YOK, ozgun kare dogrudan imgsz 512

Her kip: sinif 0 IoU (kume etiketine karsi), ust/alt uc bant temasi, rota sonucu.

Kullanim:
  python scripts/olcum/150_cikarim_geometrisi.py
  python scripts/olcum/150_cikarim_geometrisi.py --kume dji --kare-sayisi 20
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

KOMPOZIT = KOK / "data" / "arena_kompozit"


def _kod(red, yol_no):
    if yol_no is not None:
        return "ROTA"
    if red is None:
        return "RET(sebepsiz)"
    return red[0] if isinstance(red, (tuple, list)) else str(red)


def _etiket_maskeleri(lbl_yolu: Path, w: int, h: int):
    m0 = np.zeros((h, w), np.uint8)
    m1 = np.zeros((h, w), np.uint8)
    for satir in lbl_yolu.read_text(encoding="utf-8").splitlines():
        p = satir.split()
        if len(p) < 7:
            continue
        sinif = int(float(p[0]))
        k = np.array([float(x) for x in p[1:]], np.float32).reshape(-1, 2)
        k[:, 0] *= w
        k[:, 1] *= h
        cv2.fillPoly(m0 if sinif == 0 else m1, [k.astype(np.int32)], 255)
    return m0, m1


def _iou(a, b):
    a = a > 0
    b = b > 0
    birlesim = np.count_nonzero(a | b)
    return (np.count_nonzero(a & b) / birlesim) if birlesim else None


def _bant_temasi(maske, icerik, bant_px=None):
    """Icerik dikdortgeninin en alt/en ust satirinda kac piksel dolu."""
    x0, y0, w, h = icerik
    alt = int(np.count_nonzero(maske[y0 + h - 1, x0:x0 + w]))
    ust = int(np.count_nonzero(maske[y0, x0:x0 + w]))
    return alt, ust, w


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="models/navitas_seg_v36_best.pt")
    ap.add_argument("--cikti", default="results/gece_20260826/cikarim_geometrisi.json")
    a = ap.parse_args()

    from rpi_inference import (_maskeleri_icerige_kirp, _preprocess,
                               _rota_kararini_esikle, analyze_path, get_masks)
    import yks_gui
    from ultralytics import YOLO

    CONF = yks_gui.YksArayuz.ALGI_PREDICT_CONF
    o = object.__new__(yks_gui.YksArayuz)
    o.algi_kaynak = "kompozit"
    olcekler = o._kompozit_olcekleri()
    gorseller = sorted(p for p in (KOMPOZIT / "images").rglob("*")
                       if p.suffix.lower() in (".jpg", ".png", ".jpeg"))
    assert gorseller, "kompozit gorsel yok"

    myol = Path(a.model)
    if not myol.is_absolute():
        myol = KOK / a.model
    model = YOLO(str(myol))
    print(f"model: {myol.name} · conf {CONF} · {len(gorseller)} kare", flush=True)

    KIPLER = [("A_taban_lb512", True, 512), ("B_lb1024", True, 1024),
              ("D_lb768", True, 768), ("C_lbyok_512", False, 512)]
    rapor = {"model": myol.name, "conf": CONF, "kare": len(gorseller), "kipler": {}}

    for ad, letterbox, imgsz in KIPLER:
        kareler = []
        for yol in gorseller:
            img = cv2.imread(str(yol))
            h0, w0 = img.shape[:2]
            sq, small, icerik = _preprocess(img)
            lbl = KOMPOZIT / "labels" / yol.parent.name / (yol.stem + ".txt")
            g0, g1 = _etiket_maskeleri(lbl, w0, h0)
            yan = sq.shape[0]
            x0, y0, w, h = icerik
            tavan0 = np.zeros((yan, yan), np.uint8)
            tavan0[y0:y0 + h, x0:x0 + w] = g0

            if letterbox:
                girdi = cv2.resize(sq, (imgsz, imgsz))
                sonuc = model.predict(girdi, imgsz=imgsz, conf=CONF, verbose=False)
                mk = _maskeleri_icerige_kirp(get_masks(sonuc, yan, yan), icerik)
                trav, blok = mk[0], mk[1]
            else:
                # letterbox YOK: ozgun kare dogrudan; maske ozgun boyutta uretilip
                # AYNI tuvale ayni yere yerlestirilir (karar zinciri degismesin).
                sonuc = model.predict(img, imgsz=imgsz, conf=CONF, verbose=False)
                mk0 = get_masks(sonuc, h0, w0)
                trav = np.zeros((yan, yan), np.uint8)
                blok = np.zeros((yan, yan), np.uint8)
                trav[y0:y0 + h, x0:x0 + w] = mk0[0]
                blok[y0:y0 + h, x0:x0 + w] = mk0[1]

            mpp = olcekler.get(yol.name)
            (hy, gv, hw, kor, red, olc) = analyze_path(
                trav, icerik=icerik, engel_mask=blok, mpp=mpp,
                return_clean=True, return_reason=True, return_olcum=True)
            yol_no, gv, wps, red = _rota_kararini_esikle(hy, gv, hw, red)
            alt, ust, gen = _bant_temasi(trav, icerik)
            t_alt, t_ust, _ = _bant_temasi(tavan0, icerik)
            kareler.append({
                "kare": yol.name, "kod": _kod(red, yol_no), "yol_no": yol_no,
                "iou_sinif0": _iou(trav, tavan0),
                "zemin_px": int(np.count_nonzero(trav)),
                "tavan_px": int(np.count_nonzero(tavan0)),
                "bant_alt": alt, "bant_ust": ust, "bant_genislik": gen,
                "tavan_bant_alt": t_alt, "tavan_bant_ust": t_ust,
            })
        say = {}
        for k in kareler:
            say[k["kod"]] = say.get(k["kod"], 0) + 1
        iou = [k["iou_sinif0"] for k in kareler if k["iou_sinif0"] is not None]
        med = float(np.median(iou)) if iou else None
        rapor["kipler"][ad] = {"imgsz": imgsz, "letterbox": letterbox,
                               "dagilim": say, "iou_medyan": med, "kareler": kareler}
        print(f"{ad:14s} imgsz={imgsz:4d} lb={int(letterbox)} "
              f"ROTA={say.get('ROTA', 0)}/{len(kareler)} IoU_med="
              f"{med if med is None else round(med, 4)} {say}", flush=True)

    taban = rapor["kipler"]["A_taban_lb512"]
    t_rota = taban["dagilim"].get("ROTA", 0)
    t_iou = taban["iou_medyan"] or 0.0
    hukum = {}
    for ad, k in rapor["kipler"].items():
        if ad == "A_taban_lb512":
            continue
        d_rota = k["dagilim"].get("ROTA", 0) - t_rota
        d_iou = (k["iou_medyan"] or 0.0) - t_iou
        hukum[ad] = {"d_rota": d_rota, "d_iou": round(d_iou, 4),
                     "olcut_saglandi": bool(d_rota >= 4 and d_iou >= 0.05)}
    rapor["hukum"] = hukum
    rapor["hukum_metni"] = ("GEOMETRI" if any(v["olcut_saglandi"] for v in hukum.values())
                            else "GEOMETRI DEGIL — model/veri")
    print("\nHUKUM:", json.dumps(hukum, ensure_ascii=False), rapor["hukum_metni"])

    cikti = KOK / a.cikti
    cikti.parent.mkdir(parents=True, exist_ok=True)
    cikti.write_text(json.dumps(rapor, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"yazildi: {cikti}")


if __name__ == "__main__":
    main()
