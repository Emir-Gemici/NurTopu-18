"""T58 KAPI 2 — B1'i BAGIMSIZ tekrarla: gercek drone karelerinde bos maske.

NEDEN BAGIMSIZ: mimar "v24 0/30 bos maske %78,4" olctu. Anayasa madde 7 geregi
o sayi denetlenmeden uretim modeli cevrilmez. Bu betik olcumu SIFIRDAN kurar:
kare secimi, zincir ve esik burada acikca yazilidir.

ZINCIR URETIMDEN: `_preprocess` -> `predict(imgsz=INFER_SIZE, conf=...)` ->
`get_masks` -> `_maskeleri_icerige_kirp`. GUI'nin `_algi_kos` yolu ile ayni
(T36 hizalamasi). Kaplama `karar_sozlesmesi.zemin_kaplamasi` ile ICERIK
kutusundan olculur — letterbox dolgusu paydaya girmez.

KONTROL (D-15/K-04: "sifir olcum basari sayilmaz"): v17 NEGATIF kontroldur.
Olcut gercekten DUSEBILIYOR mu? v17 B1'de kordu; bu betik onu tekrar
dusurmelidir. Dusmezse olcut bozuktur, model iyi degildir.

Kullanim:
  venv\\Scripts\\python.exe 58_b1_bagimsiz.py [-n 30] [--conf 0.30]
"""
import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

from ayarlar import REPO

sys.path.insert(0, str(REPO / "codes"))
from karar_sozlesmesi import zemin_kaplamasi                      # noqa: E402
from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp,   # noqa: E402
                           _preprocess, get_masks)

CIK = Path(__file__).parent / "results" / "t58_b1"
MODELLER = ["navitas_seg_v24_best.pt", "navitas_seg_v21_best.pt",
            "navitas_seg_v17_best.pt"]


def kareler(n):
    """Gercek drone kareleri — ESIT ARALIKLI sec.

    Bas 30 kare tek videonun ilk saniyeleridir; esit aralikli secim tum
    videolari ve tum irtifalari kapsar. Secim TOHUMSUZ ve tekrarlanabilir.
    """
    hepsi = sorted((REPO / "data" / "raw_frames").rglob("*.jpg"))
    if n >= len(hepsi):
        return hepsi
    adim = len(hepsi) / float(n)
    return [hepsi[min(len(hepsi) - 1, int(i * adim))] for i in range(n)]


def olc(model, yollar, conf):
    bos = 0
    oranlar = []
    for p in yollar:
        img = cv2.imread(str(p))
        if img is None:
            continue
        sq, small, icerik = _preprocess(img)
        h, w = sq.shape[:2]
        r = model.predict(small, imgsz=INFER_SIZE, conf=conf, verbose=False)
        m = _maskeleri_icerige_kirp(get_masks(r, h, w), icerik)
        zemin = m[0]
        if int(np.count_nonzero(zemin)) == 0:
            bos += 1
        oranlar.append(float(zemin_kaplamasi(zemin, icerik)))
    return {"n": len(oranlar), "bos": bos,
            "ort": float(np.mean(oranlar)) if oranlar else 0.0,
            "min": float(min(oranlar)) if oranlar else 0.0,
            "maks": float(max(oranlar)) if oranlar else 0.0}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=30)
    ap.add_argument("--conf", type=float, nargs="*", default=[0.30, 0.25])
    a = ap.parse_args()

    from ultralytics import YOLO
    yollar = kareler(a.n)
    CIK.mkdir(parents=True, exist_ok=True)
    print(f"B1 BAGIMSIZ · kare {len(yollar)}/{a.n} · kaynak data/raw_frames "
          f"(esit aralikli) · zincir URETIM")
    print(f"ilk kare: {yollar[0].name}   son kare: {yollar[-1].name}")
    print("=" * 76)
    print(f"{'model':<26}{'conf':>6}{'BOS maske':>11}{'ort kaplama':>13}"
          f"{'min':>8}{'maks':>8}")
    kayit = []
    for ad in MODELLER:
        yol = REPO / "models" / ad
        if not yol.exists():
            print(f"{ad:<26}  (dosya yok)")
            continue
        mdl = YOLO(str(yol), task="segment")
        for conf in a.conf:
            s = olc(mdl, yollar, conf)
            kayit.append({"model": ad, "conf": conf, **s})
            print(f"{ad:<26}{conf:>6.2f}{s['bos']:>7}/{s['n']:<3}"
                  f"{100*s['ort']:>12.1f}%{100*s['min']:>7.1f}%"
                  f"{100*s['maks']:>7.1f}%")
        del mdl
    (CIK / "t58_b1.json").write_text(
        json.dumps({"kareler": [p.name for p in yollar], "olcumler": kayit},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    print("=" * 76)

    def bul(ad, conf):
        for k in kayit:
            if k["model"] == ad and abs(k["conf"] - conf) < 1e-9:
                return k
        return None

    v24 = bul("navitas_seg_v24_best.pt", 0.30)
    v17 = bul("navitas_seg_v17_best.pt", 0.30)
    if v24:
        print(f"KAPI 2   v24 bos maske {v24['bos']}/{v24['n']}   "
              f"{'GECTI' if v24['bos'] == 0 else 'DUSTU'}")
    if v17:
        print(f"KONTROL  v17 bos maske {v17['bos']}/{v17['n']}   "
              f"{'olcut DUSEBILIYOR (gecerli)' if v17['bos'] > 0 else 'OLCUT BOZUK — v17 de gecti'}")
    print(f"JSON -> {CIK / 't58_b1.json'}")


if __name__ == "__main__":
    main()
