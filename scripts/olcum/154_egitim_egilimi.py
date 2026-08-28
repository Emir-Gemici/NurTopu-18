"""154 — EGITIM EGILIMI IZLEYICISI (gece 2026-08-28).

Egitim surerken belirli araliklarla `last.pt`yi ANLIK KOPYALAR ve ucuz iki
olcumu kosar:

  G4  · bariyer aci taramasi (12 aci) — asil hedef, val mAP bunu OLCMEZ
  KOMPOZIT · rota sayisi (88 kare) — gercek kirsal goruntude kalibrasyon

Sonuc `results/gece_20260828/egilim.jsonl` dosyasina EKLENIR (satir basina bir
olcum). Boylece sabah tek bir noktaya degil GIDISATA bakilabilir.

NEDEN GEREKLI: `best.pt` val mAP'e gore secilir ama val kumesi 73 gercek DJI
karesidir ve bariyer acisini/kompoziti OLCMEZ (D-328 §4). Model secimi on
kayitli kapilara gore yapilacak; bu betik o kapilarin epoch'a gore nasil
degistigini kaydeder.

⚠ Egitimi YAVASLATMAMAK icin olcum araligi genis tutulur ve her turda yalniz
12 + 88 = 100 cikarim yapilir.

Kullanim:
  <venv> 154_egitim_egilimi.py --aralik-dk 90 --tur 12
"""
from __future__ import annotations

import argparse
import glob
import json
import shutil
import sys
import time
from pathlib import Path

KOK = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(KOK / "codes"))

import cv2                                                        # noqa: E402
import numpy as np                                                # noqa: E402

from karar_sozlesmesi import ince_bariyer_maskesi                 # noqa: E402
from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp,   # noqa: E402
                           _preprocess, analyze_path, get_masks)

KOSUM = KOK / "codes" / "runs" / "segment" / "bariyer_v8_v36taban"
SON = KOSUM / "weights" / "last.pt"
SONUCLAR = KOK / "results" / "gece_20260828"
EGILIM = SONUCLAR / "egilim.jsonl"
SARTNAME = KOK / "data" / "arena_referans" / "sartname_s9_arena.png"
KOMPOZIT = KOK / "data" / "arena_kompozit"
GECICI = SONUCLAR / "_egilim_anlik.pt"


def _dondur(g, aci):
    h, w = g.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2.0, h / 2.0), aci, 1.0)
    kos, sin = abs(M[0, 0]), abs(M[0, 1])
    nw, nh = int(h * sin + w * kos), int(h * kos + w * sin)
    M[0, 2] += nw / 2.0 - w / 2.0
    M[1, 2] += nh / 2.0 - h / 2.0
    return cv2.warpAffine(g, M, (nw, nh), flags=cv2.INTER_LINEAR,
                          borderMode=cv2.BORDER_REPLICATE)


def _epoch():
    csv = KOSUM / "results.csv"
    if not csv.is_file():
        return None
    satirlar = [s for s in csv.read_text(encoding="utf-8").splitlines() if s.strip()]
    if len(satirlar) < 2:
        return None
    try:
        return int(satirlar[-1].split(",")[0])
    except (ValueError, IndexError):
        return None


def _olc(model):
    im = cv2.imread(str(SARTNAME))
    bar0 = ince_bariyer_maskesi(im)
    gecen, oranlar = 0, []
    for aci in range(0, 180, 15):
        g = _dondur(im, aci)
        b = _dondur(bar0 * 255, aci) > 127
        r = model.predict(g, imgsz=INFER_SIZE, conf=0.30, verbose=False)[0]
        h, w = g.shape[:2]
        e = np.zeros((h, w), np.uint8)
        if r.masks is not None:
            for msk, c in zip(r.masks.data.cpu().numpy(),
                              r.boxes.cls.cpu().numpy().astype(int)):
                if int(c) == 1:
                    e = np.maximum(e, cv2.resize(
                        msk.astype(np.uint8), (w, h),
                        interpolation=cv2.INTER_NEAREST))
        o = 100.0 * int((b & (e > 0)).sum()) / max(1, int(b.sum()))
        oranlar.append(round(o))
        gecen += o >= 60.0

    rota, maske_yok = 0, 0
    for p in sorted(glob.glob(str(KOMPOZIT / "images" / "*" / "*.jpg"))):
        img = cv2.imread(p)
        if img is None:
            continue
        sq, small, icerik = _preprocess(img)
        res = model.predict(small, imgsz=INFER_SIZE, conf=0.30, verbose=False)
        m = _maskeleri_icerige_kirp(get_masks(res, sq.shape[0], sq.shape[1]),
                                    icerik)
        yol, _g, _w, red = analyze_path(m[0], icerik=icerik,
                                        engel_mask=m.get(1),
                                        mpp=50.0 / img.shape[1],
                                        return_reason=True)
        if yol:
            rota += 1
        else:
            kod = red[0] if isinstance(red, (tuple, list)) else str(red)
            if kod == "MASKE_YOK":
                maske_yok += 1
    return {"G4_gecen": gecen, "G4_oranlar": oranlar,
            "kompozit_rota": rota, "kompozit_maske_yok": maske_yok}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--aralik-dk", type=float, default=90.0)
    ap.add_argument("--tur", type=int, default=12)
    a = ap.parse_args()
    SONUCLAR.mkdir(parents=True, exist_ok=True)
    from ultralytics import YOLO

    for tur in range(a.tur):
        if not SON.is_file():
            print(f"[{tur}] checkpoint yok, bekleniyor", flush=True)
        else:
            try:
                shutil.copy2(SON, GECICI)      # egitim yazarken kilitlenmesin
                ep = _epoch()
                model = YOLO(str(GECICI), task="segment")
                olcum = _olc(model)
                kayit = {"zaman": time.strftime("%Y-%m-%d %H:%M:%S"),
                         "epoch": ep, **olcum}
                with open(EGILIM, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(kayit, ensure_ascii=False) + "\n")
                print(f"[{tur}] epoch {ep} · G4 {olcum['G4_gecen']}/12 · "
                      f"kompozit {olcum['kompozit_rota']}/88 "
                      f"(MASKE_YOK {olcum['kompozit_maske_yok']})", flush=True)
                del model
            except Exception as exc:           # olcum egitimi ASLA durdurmaz
                print(f"[{tur}] OLCUM HATASI {type(exc).__name__}: {exc}",
                      flush=True)
        if tur < a.tur - 1:
            time.sleep(a.aralik_dk * 60.0)
    print("egilim izleyicisi bitti", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
