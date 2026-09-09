"""KAMERA YATAY GORUS ACISI (FOV) — kaydedilmis kareden OLCUM ile hesap.

NEDEN (T219 · FDR/ACIK_KALEMLER kalem 2): `--fov` bugun bir lens HESABIDIR (55-63°),
olcum degil. `codes/kamera_dogrula.py --kaydet kare.jpg` kareyi yazar ama FOV'u
hesaplamaz; bu betik o kareden alinan iki sayiyi (isaretler arasi piksel, gercek
mesafe) geometriye cevirir. jetson_baslat.sh FOV=<derece> YA DA ODAK=<piksel> ister
(rpi_inference: karsilikli dislar); ikisi de burada cikar.

Yordam (saha): kamera duvara DIK, mesafe d (metre, lens onunden duvara) olculur;
duvara birbirinden s metre uzak iki isaret (bant) konur, ikisi de kareye girer;
`kamera_dogrula.py --kaydet` ile kare alinir; bir resim goruntuleyicide iki isaretin
piksel x'leri okunur, farki p'dir; W kare genisligi (piksel).
    odak_px = p * d / s          FOV_yatay = 2 * atan(W / (2 * odak_px))
Isaretler kare kenarina yakin secilirse lens bozulmasi hesabi bozar: isaretleri
merkezin iki yanina, genisligin ortadaki ~%50'sine koy (kural, olcum degil).

Cikis: 0 hesaplandi · 2 gecersiz girdi. Sonuc satiri: `ODAK=<px>  FOV_yatay=<derece>`.

Kullanim:
  kamera_fov_hesapla.py --genislik-px 1280 --isaret-px 640 --isaret-m 1.00 --mesafe-m 2.00
  (ornek: odak 1280 px, FOV 53,13°)
"""
from __future__ import annotations

import argparse
import json
import math
import sys

CIKIS_TAMAM, CIKIS_GECERSIZ = 0, 2


def odak_px(isaret_px, isaret_m, mesafe_m):
    """Iki isaretin piksel farkindan odak uzakligi (piksel). Pozitif ve sonlu girdi ister."""
    for ad, d in (("isaret_px", isaret_px), ("isaret_m", isaret_m), ("mesafe_m", mesafe_m)):
        if not (isinstance(d, (int, float)) and math.isfinite(d) and d > 0):
            raise ValueError(f"{ad} pozitif ve sonlu olmali: {d!r}")
    return isaret_px * mesafe_m / isaret_m


def fov_derece(genislik_px, odak):
    """Kare genisligi ve odak (piksel) -> yatay gorus acisi (derece)."""
    if not (genislik_px > 0 and odak > 0):
        raise ValueError("genislik ve odak pozitif olmali")
    return math.degrees(2.0 * math.atan(genislik_px / (2.0 * odak)))


def hesapla(genislik_px, isaret_px, isaret_m, mesafe_m, yukseklik_px=None):
    o = odak_px(isaret_px, isaret_m, mesafe_m)
    sonuc = {"odak_px": o, "fov_yatay_derece": fov_derece(genislik_px, o),
             "genislik_px": genislik_px, "isaret_px": isaret_px,
             "isaret_m": isaret_m, "mesafe_m": mesafe_m}
    if yukseklik_px:
        sonuc["fov_dusey_derece"] = fov_derece(yukseklik_px, o)
    return sonuc


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--genislik-px", type=float, required=True, help="kare genisligi W (piksel)")
    ap.add_argument("--isaret-px", type=float, required=True,
                    help="iki isaretin karedeki x farki p (piksel)")
    ap.add_argument("--isaret-m", type=float, required=True,
                    help="iki isaretin gercek araligi s (metre)")
    ap.add_argument("--mesafe-m", type=float, required=True,
                    help="lens -> duvar mesafesi d (metre)")
    ap.add_argument("--yukseklik-px", type=float, default=None,
                    help="kare yuksekligi (piksel) — verilirse dusey FOV da yazilir")
    ap.add_argument("--json", action="store_true", help="sonucu JSON bas")
    a = ap.parse_args(argv)
    try:
        s = hesapla(a.genislik_px, a.isaret_px, a.isaret_m, a.mesafe_m, a.yukseklik_px)
    except ValueError as exc:
        print(f"GECERSIZ: {exc}", file=sys.stderr)
        return CIKIS_GECERSIZ
    if a.json:
        print(json.dumps(s, ensure_ascii=False))
    else:
        satir = f"ODAK={s['odak_px']:.1f} px  FOV_yatay={s['fov_yatay_derece']:.2f} derece"
        if "fov_dusey_derece" in s:
            satir += f"  FOV_dusey={s['fov_dusey_derece']:.2f} derece"
        print(satir)
        print(f"jetson_baslat.sh icin: FOV={s['fov_yatay_derece']:.1f}  (ya da ODAK={s['odak_px']:.0f}; ikisi birlikte verilmez)")
    return CIKIS_TAMAM


if __name__ == "__main__":
    sys.exit(main())
