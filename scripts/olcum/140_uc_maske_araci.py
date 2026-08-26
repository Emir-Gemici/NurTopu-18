"""140 — UC DURUMLU MASKE ARACI (etiketleme amelesi icin TEK deterministik arac).

Biçim (SU_ETIKETLEME_PLANI.md §4b-EK-2 B): 960x540 PNG, deger 0 ETIKETSIZ · 1 SINIF 0 · 2 SINIF 1.
Islemler 960x540 koordinatinda yazilir (ops.json). Sira onemlidir: sonraki islem oncekini ezer.

  ops.json:  {"islemler": [
      {"tip": "poligon",   "deger": 1, "nokta": [[x,y],...]},
      {"tip": "dikdortgen","deger": 2, "kutu": [x0,y0,x1,y1]},
      {"tip": "daire",     "deger": 2, "merkez": [x,y], "yaricap": r} ]}

Komutlar:
  izgara   --kare <jpg> --cikti <jpg>              : 960x540 kucultulmus + 60 px izgara + koordinat etiketleri (amele bunu GORUR)
  buyut    --kare <jpg> --kutu x0 y0 x1 y1 --cikti <jpg> : 960 koordinatinda bir bolgeyi ham (4K) cozunurlukten buyutur, izgarali
  uret     --kare <jpg> --ops <json> --cikti <png> [--bindirme <jpg>] : maskeyi yazar, sayim basar, bindirme cizer
  sayim    --maske <png>
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

W, H = 960, 540
ADIM = 60


def _oku_960(kare: Path) -> np.ndarray:
    im = cv2.imread(str(kare), cv2.IMREAD_COLOR)
    if im is None:
        raise SystemExit(f"[DUR] kare okunamadi: {kare}")
    return cv2.resize(im, (W, H), interpolation=cv2.INTER_AREA)


def _izgara_ciz(im: np.ndarray, x_ofs=0, y_ofs=0, olcek=1.0, adim=ADIM) -> np.ndarray:
    im = im.copy()
    h, w = im.shape[:2]
    # 960-koordinatinda adim'in katlarina cizgi
    x = 0
    while (x - x_ofs) * olcek <= w:
        px = int(round((x - x_ofs) * olcek))
        if 0 <= px < w:
            cv2.line(im, (px, 0), (px, h - 1), (0, 255, 255), 1)
            cv2.putText(im, str(x), (px + 2, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 255, 255), 1)
        x += adim
        if x > 4000:
            break
    y = 0
    while (y - y_ofs) * olcek <= h:
        py = int(round((y - y_ofs) * olcek))
        if 0 <= py < h:
            cv2.line(im, (0, py), (w - 1, py), (0, 255, 255), 1)
            cv2.putText(im, str(y), (2, py + 12), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 255, 255), 1)
        y += adim
        if y > 4000:
            break
    return im


def izgara(kare: Path, cikti: Path):
    im = _izgara_ciz(_oku_960(kare))
    cikti.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(cikti), im, [cv2.IMWRITE_JPEG_QUALITY, 92])
    print("izgara ->", cikti)


def buyut(kare: Path, kutu, cikti: Path):
    ham = cv2.imread(str(kare), cv2.IMREAD_COLOR)
    if ham is None:
        raise SystemExit(f"[DUR] kare okunamadi: {kare}")
    hh, hw = ham.shape[:2]
    sx, sy = hw / W, hh / H
    x0, y0, x1, y1 = [int(v) for v in kutu]
    x0, x1 = max(0, min(x0, x1)), min(W, max(x0, x1))
    y0, y1 = max(0, min(y0, y1)), min(H, max(y0, y1))
    parca = ham[int(y0 * sy):int(y1 * sy), int(x0 * sx):int(x1 * sx)]
    # 960 koordinat sistemine gore olcek: parca genisligi (x1-x0) 960-birim
    hedef_w = 960
    olcek = hedef_w / max(1, (x1 - x0))
    parca = cv2.resize(parca, (hedef_w, int((y1 - y0) * olcek)), interpolation=cv2.INTER_AREA)
    parca = _izgara_ciz(parca, x_ofs=x0, y_ofs=y0, olcek=olcek, adim=20)
    cikti.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(cikti), parca, [cv2.IMWRITE_JPEG_QUALITY, 92])
    print("buyut ->", cikti, "olcek", round(olcek, 2))


def uret(kare: Path, ops: Path, cikti: Path, bindirme: Path | None, taban: Path | None = None):
    d = json.loads(Path(ops).read_text(encoding="utf-8"))
    m = np.zeros((H, W), np.uint8)
    if taban is not None:
        tm = cv2.imread(str(taban), cv2.IMREAD_GRAYSCALE)
        if tm is None or tm.shape != (H, W) or not set(np.unique(tm).tolist()) <= {0, 1, 2}:
            raise SystemExit(f"[DUR] taban maske gecersiz: {taban}")
        m = tm.copy()
    for i, op in enumerate(d["islemler"]):
        deger = int(op["deger"])
        if deger not in (0, 1, 2):
            raise SystemExit(f"[DUR] islem {i}: deger {deger} gecersiz (0/1/2)")
        t = op["tip"]
        if t == "poligon":
            pts = np.array(op["nokta"], np.int32)
            if len(pts) < 3:
                raise SystemExit(f"[DUR] islem {i}: poligon <3 nokta")
            cv2.fillPoly(m, [pts], deger)
        elif t == "dikdortgen":
            x0, y0, x1, y1 = [int(v) for v in op["kutu"]]
            m[max(0, y0):max(0, y1), max(0, x0):max(0, x1)] = deger
        elif t == "daire":
            cx, cy = [int(v) for v in op["merkez"]]
            cv2.circle(m, (cx, cy), int(op["yaricap"]), deger, -1)
        else:
            raise SystemExit(f"[DUR] islem {i}: tip {t} bilinmiyor")
    cikti.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(cikti), m)
    geri = cv2.imread(str(cikti), cv2.IMREAD_GRAYSCALE)
    assert geri is not None and set(np.unique(geri).tolist()) <= {0, 1, 2}
    say = sayim_hesapla(m)
    print(json.dumps({"maske": str(cikti), **say}, ensure_ascii=False))
    if bindirme is not None:
        im = _oku_960(kare)
        ov = im.copy()
        ov[m == 1] = (0.45 * ov[m == 1] + 0.55 * np.array([0, 200, 0])).astype(np.uint8)
        ov[m == 2] = (0.45 * ov[m == 2] + 0.55 * np.array([0, 0, 220])).astype(np.uint8)
        ov = _izgara_ciz(ov)
        cv2.putText(ov, "YESIL=sinif0 (surulebilir)  KIRMIZI=sinif1 (gecilemez)  RENKSIZ=ETIKETSIZ",
                    (8, H - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        yan = np.concatenate([im, ov], axis=1)
        bindirme.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(bindirme), yan, [cv2.IMWRITE_JPEG_QUALITY, 90])
        print("bindirme ->", bindirme)


def sayim_hesapla(m: np.ndarray) -> dict:
    n = m.size
    return {"etiketsiz": round(float((m == 0).mean()), 4), "sinif0": round(float((m == 1).mean()), 4),
            "sinif1": round(float((m == 2).mean()), 4), "px": int(n)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("komut", choices=["izgara", "buyut", "uret", "sayim", "goster"])
    ap.add_argument("--taban", type=Path, default=None, help="uret: islemler bu maskenin USTUNE uygulanir")
    ap.add_argument("--kare", type=Path)
    ap.add_argument("--ops", type=Path)
    ap.add_argument("--cikti", type=Path)
    ap.add_argument("--bindirme", type=Path, default=None)
    ap.add_argument("--maske", type=Path)
    ap.add_argument("--kutu", type=int, nargs=4)
    a = ap.parse_args()
    if a.komut == "izgara":
        izgara(a.kare, a.cikti)
    elif a.komut == "buyut":
        buyut(a.kare, a.kutu, a.cikti)
    elif a.komut == "uret":
        uret(a.kare, a.ops, a.cikti, a.bindirme, a.taban)
    elif a.komut == "goster":
        m = cv2.imread(str(a.maske), cv2.IMREAD_GRAYSCALE)
        im = _oku_960(a.kare); ov = im.copy()
        ov[m == 1] = (0.45 * ov[m == 1] + 0.55 * np.array([0, 200, 0])).astype(np.uint8)
        ov[m == 2] = (0.45 * ov[m == 2] + 0.55 * np.array([0, 0, 220])).astype(np.uint8)
        ov = _izgara_ciz(ov)
        a.cikti.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(a.cikti), np.concatenate([im, ov], axis=1), [cv2.IMWRITE_JPEG_QUALITY, 90])
        print("goster ->", a.cikti, json.dumps(sayim_hesapla(m)))
    else:
        m = cv2.imread(str(a.maske), cv2.IMREAD_GRAYSCALE)
        print(json.dumps(sayim_hesapla(m)))


if __name__ == "__main__":
    main()
