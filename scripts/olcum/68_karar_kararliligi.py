"""KARAR KARARLILIGI — ayni sahne, gercekci algilayici gurultusu: secim ceviriliyor mu?

NEDEN (REVIEW_LOG D-119 + D-120). `.pt` ile FP16 `.onnx` 260 karenin 2'sinde
FARKLI koridor sectiler (rota 28 m ayrildi) — oysa zemin maskeleri IoU 0,9968
ile ortusuyordu. O olcumu "iki artefakt ayrisiyor" diye cerceveledim; saha
topolojisi denetlenince rotayi TEK yerin hesapladigi cikti (D-120), yani o
cerceve gecersiz.

Ama bulgunun OZU ayakta: iki artefakt, AYNI SAHNENIN binde-4 gurultuyle iki
ORNEGIDIR. Ayni kararsizlik tek bir IHA'da KAREDEN KAREYE de olusur — isik
oynar, algilayici gurultusu biner, JPEG yeniden sikistirir. Rota koridor
degistirip duruyorsa IKA'nin izleyecegi hedef zikzak yapar.

BU BETIK bunu olcer: her kareye GERCEKCI algilayici gurultusu bindirip ayni
modelle yeniden karar urettirir ve KARARIN CEVRILME oranini sayar.

  gurultu = Gauss(sigma) piksel gurultusu — varsayilan sigma=2/255 (%0,8),
  ucuz bir kameranin bile altinda kaldigi bir seviye. Yani bu olcum
  GERCEGIN ALT SINIRIDIR: saha gurultusu bundan buyuktur.

Yer gercegi KULLANILMAZ. Sorulan "karar dogru mu" degil, "karar AYNI MI".
"""
import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

from ayarlar import REPO, uretim_pt

BURASI = Path(__file__).parent
sys.path.insert(0, str(REPO / "codes"))

from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp,  # noqa: E402
                           _preprocess, analyze_path, get_masks)

KUME = BURASI / "calisma" / "sentetik_arena_kadraj_t66"
# T85: surum adi CIPLAK SABIT degildir (madde 16) — kayit defteri tek kaynak.
# Argumansiz kosan bir kararlilik olcumu ESKI modeli olcup sonucu uretim
# modelinin sayisi diye kaydediyordu; bu D-58/D-60/D-116 kusur sinifidir.
MODEL = uretim_pt()
CONF = 0.30


def karar(model, img, mpp):
    sq, small, icerik = _preprocess(img)
    r = model.predict(small, imgsz=INFER_SIZE, conf=CONF, verbose=False)
    mk = _maskeleri_icerige_kirp(get_masks(r, *sq.shape[:2]), icerik)
    yol, guven, wps, _k, red, olcum = analyze_path(
        mk[0], icerik=icerik, engel_mask=mk[1], mpp=mpp,
        return_clean=True, return_reason=True, return_olcum=True)
    # `analyze_path` rota reddedilince `olcum`u None dondurur — bos sozluge
    # dusmek, red halinde de karari (serit+sebep) kiyaslayabilmek icin sart.
    olcum = olcum or {}
    return (yol, red[0] if isinstance(red, tuple) else red, guven,
            olcum.get("darbogaz_px"), olcum.get("r_gerekli_px"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", type=Path, default=MODEL)
    ap.add_argument("--kume", type=Path, default=KUME)
    ap.add_argument("--sigma", type=float, default=2.0,
                    help="Gauss gurultu sigmasi, 0-255 olceginde (varsayilan 2)")
    ap.add_argument("--tekrar", type=int, default=3)
    ap.add_argument("--tohum", type=int, default=7)
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    man = json.loads((args.kume / "manifest.json").read_text(encoding="utf-8"))
    from ultralytics import YOLO
    model = YOLO(str(args.model), task="segment")
    rng = np.random.default_rng(args.tohum)

    n = kararsiz = 0
    paylar, cevrilenler = [], []

    for ornek in man["ornekler"]:
        if ornek.get("durum") != "YAZILDI" or not ornek.get("arena"):
            continue
        p = args.kume / ornek["cikti"]
        mpp = ornek["arena"].get("mpp")
        if not p.is_file() or not mpp:
            continue
        img = cv2.imread(str(p))
        if img is None:
            continue
        n += 1

        temiz = karar(model, img, mpp)
        if temiz[3] is not None and temiz[4]:
            paylar.append(temiz[3] - temiz[4])

        gorulen = {temiz[:2]}
        ornekler = [temiz]
        for _ in range(args.tekrar):
            g = rng.normal(0.0, args.sigma, img.shape).astype(np.float32)
            gurultulu = np.clip(img.astype(np.float32) + g, 0, 255).astype(np.uint8)
            k = karar(model, gurultulu, mpp)
            gorulen.add(k[:2])
            ornekler.append(k)

        if len(gorulen) > 1:
            kararsiz += 1
            cevrilenler.append({
                "kare": p.name,
                "kararlar": [{"serit": k[0], "red": k[1], "guven": k[2],
                              "darbogaz_px": k[3]} for k in ornekler],
                "pay_px": (temiz[3] - temiz[4]) if temiz[3] and temiz[4] else None})

    print(f"\n{'=' * 68}\nKARAR KARARLILIGI · {args.model.name}")
    print(f"  gurultu: Gauss sigma={args.sigma}/255 (%{100*args.sigma/255:.1f}) · "
          f"kare basina {args.tekrar} tekrar\n{'=' * 68}")
    print(f"  olculen kare        : {n}")
    print(f"  KARARI CEVRILEN     : {kararsiz}/{n}  "
          f"(%{100 * kararsiz / max(1, n):.2f})")
    if paylar:
        pa = np.array(paylar)
        print(f"  darbogaz PAYI (darbogaz - r_gerekli), tum kareler:")
        print(f"    medyan {np.median(pa):.1f} px · en dusuk {pa.min():.1f} px · "
              f"pay < 3 px olan kare: {int((pa < 3).sum())}/{len(pa)}")
    print("=" * 68)
    for c in cevrilenler[:12]:
        d = " | ".join(f"{k['serit']}/{k['red']}" for k in c["kararlar"])
        print(f"    {c['kare']}  pay={c['pay_px']}  ->  {d}")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(
            {"model": str(args.model), "sigma": args.sigma,
             "tekrar": args.tekrar, "n": n, "kararsiz": kararsiz,
             "cevrilenler": cevrilenler}, ensure_ascii=False, indent=1),
            encoding="utf-8")
        print(f"\njson -> {args.json}")


if __name__ == "__main__":
    main()
