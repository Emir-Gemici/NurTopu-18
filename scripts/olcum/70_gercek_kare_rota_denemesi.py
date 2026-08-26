"""GERCEK KARELERDE ROTA: olcegi ARACTAN verirsek ne oluyor?

NEDEN. Otopark karelerinde rota HIC uretilmiyor. Iki ayri tikac olculdu:
  1. OLCEK YOK — WhatsApp videosundan cikarilmis kareler, EXIF alan sayisi 0.
     C-uzayi kosamaz, cunku govde acikligi piksele cevrilemez.
  2. ZEMIN KAPISI — kaplama %78 > tavan %67; model bina catisini zemin
     sayiyor (D-118, gorselle dogrulandi).

`69_arac_referans_olcegi.py` 1. tikaci cozdu: DOTA OBB araclarindan
mpp = 1,80 m / kisa_kenar_px cikiyor, kareler arasi bagil aralik 0,23,
r_gerekli 14,2-15,9 px (arac genisligi 1,70-1,90 m belirsizliginin TAMAMI icin).

BU BETIK ikisini AYIRIR: her gercek karede, olcegi ARACTAN vererek karari
yeniden urettirir ve sonucu uc kovaya ayirir:

    ROTA VAR                 -> olcek TEK tikacti, cozuldu
    ZEMIN_MASKESI_SUPHELI    -> zemin kapisi hala tikiyor (catinin sorunu)
    BASKA RED                -> ucuncu bir sebep var, adiyla raporlanir

Boylece "gercek goruntude hicbir sey yapamiyoruz" ifadesi SAYIYA cevrilir.

⚠ Bu bir URETIM YOLU DEGILDIR. Arenada arac yoktur; orada olcek TELEMETRIDEN
gelir (D-98/T69). Burasi yalniz OLCUMDUR: gercek goruntude neyin tikadigini
ayirt etmek icin.
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import cv2
import numpy as np

from ayarlar import uretim_pt                                 # noqa: E402

# T161: kok `ayarlar`dan gelir — ciplak yol yazilmaz; kopya
# agacta (worktree) KENDI deposunu gosterir (ON_KAYIT SS22).
from ayarlar import REPO  # noqa: E402
BURASI = Path(__file__).parent
sys.path.insert(0, str(REPO / "codes"))

from arac_maskesi import ARAC_SINIFLERI                       # noqa: E402
from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp,  # noqa: E402
                           _preprocess, analyze_path, get_masks)

ARAC_GENISLIGI_M = 1.80
CONF = 0.30


def arac_mpp(obb_model, yol):
    """Sahnedeki araclardan metre/piksel. Arac yoksa None."""
    r = obb_model.predict(str(yol), conf=0.25, verbose=False)[0]
    if r.obb is None or len(r.obb) == 0:
        return None
    adlar = r.names
    sinif = r.obb.cls.cpu().numpy().astype(int)
    wh = r.obb.xywhr.cpu().numpy()[:, 2:4]
    sec = np.array([adlar.get(int(s), str(s)) in ARAC_SINIFLERI for s in sinif])
    if not sec.any():
        return None
    kisa = np.minimum(wh[sec][:, 0], wh[sec][:, 1])
    med = float(np.median(kisa))
    return (ARAC_GENISLIGI_M / med) if med > 0 else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kok", type=Path, default=REPO / "data" / "raw_frames")
    # T85: surum adi CIPLAK SABIT degildir (madde 16) — kayit defteri tek kaynak.
    ap.add_argument("--model", type=Path, default=uretim_pt())
    ap.add_argument("--obb", type=Path, default=REPO / "yolov8m-obb.pt")
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    from ultralytics import YOLO
    seg = YOLO(str(args.model), task="segment")
    obb = YOLO(str(args.obb), task="obb")

    kareler = sorted(args.kok.rglob("*.jpg"))
    kayit, sebepler = [], Counter()
    rota_var = olceksiz = 0

    for p in kareler:
        img = cv2.imread(str(p))
        if img is None:
            continue
        mpp = arac_mpp(obb, p)
        if mpp is None:
            olceksiz += 1
            sebepler["ARAC_YOK_OLCEK_CIKARILAMADI"] += 1
            kayit.append({"kare": p.name, "mpp": None, "red": "ARAC_YOK"})
            continue

        sq, small, icerik = _preprocess(img)
        r = seg.predict(small, imgsz=INFER_SIZE, conf=CONF, verbose=False)
        mk = _maskeleri_icerige_kirp(get_masks(r, *sq.shape[:2]), icerik)
        yol, guven, wps, _k, red, olcum = analyze_path(
            mk[0], icerik=icerik, engel_mask=mk[1], mpp=mpp,
            return_clean=True, return_reason=True, return_olcum=True)
        sebep = red[0] if isinstance(red, tuple) else red
        olcum = olcum or {}
        if red is None and wps:
            rota_var += 1
            sebepler["ROTA_VAR"] += 1
        else:
            sebepler[sebep or "SEBEPSIZ_ROTA_YOK"] += 1
        # ⚠ Kaplama ICERIGE bagil olcülür, tuvale DEGIL. `_preprocess` kareyi
        # kare tuvale doldurur (1024x576 -> 1024x1024); tuval uzerinden alinan
        # ortalama dolguyla sulanir ve kapinin kendi sayisindan KUCUK cikar
        # (olculdu: tuvalde %45,3 iken kapi %78 goruyordu). Kapi icerige bakar.
        x0, y0, cw, ch = icerik
        kaplama = float((mk[0][y0:y0 + ch, x0:x0 + cw] > 0).mean())
        kayit.append({"kare": p.name, "mpp": round(mpp, 5), "serit": yol,
                      "guven": guven, "red": sebep,
                      "kaplama": kaplama,
                      "darbogaz_px": olcum.get("darbogaz_px"),
                      "r_gerekli_px": olcum.get("r_gerekli_px")})

    print(f"\n{'=' * 70}\nGERCEK KARELERDE ROTA · olcek ARACTAN")
    print(f"  kok   : {args.kok}")
    print(f"  model : {args.model.name}\n{'=' * 70}")
    print(f"  taranan kare : {len(kayit)}")
    print(f"  ROTA URETILEN: {rota_var}/{len(kayit)}")
    print("-" * 70)
    for s, n in sebepler.most_common():
        print(f"    {n:4d}  {s}")
    print("-" * 70)
    kap = [k["kaplama"] for k in kayit if k.get("kaplama") is not None]
    if kap:
        print(f"  zemin kaplamasi  medyan %{100*np.median(kap):.1f} · "
              f"en dusuk %{100*min(kap):.1f} · en yuksek %{100*max(kap):.1f}"
              f"   (tavan %67)")
    mp = [k["mpp"] for k in kayit if k.get("mpp")]
    if mp:
        print(f"  arac mpp         medyan {np.median(mp):.5f} m/px  "
              f"({min(mp):.5f} - {max(mp):.5f})")
    print("=" * 70)

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(
            {"kok": str(args.kok), "model": str(args.model),
             "kare": len(kayit), "rota_var": rota_var,
             "sebepler": dict(sebepler), "kayitlar": kayit},
            ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\njson -> {args.json}")


if __name__ == "__main__":
    main()
