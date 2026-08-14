"""K5 POPULASYON — IKA GOVDESI bariyer koluna degiyor mu? (n=1 degil, ~160 kare)

NEDEN (REVIEW_LOG D-114 + D-115): `63_bariyer_kesisimi.py` K5'i IKI yerde
yanlis olcuyordu:

  1. TEK KARE. Kesisim yalniz sartname figuru uzerinde olculuyordu. O kare
     D-99'da YAPAY ZEKA URETIMI oldugu tespit edilen karedir ve v27 orada rota
     uretmiyor — kesisim TANIMSIZ kaliyor, kapi ise "olcemedigini" DUSTU diye
     raporluyordu. Modelin degil, denetcinin kusuruydu.

  2. NOKTASAL ROTA. Kesisim, rotanin `cv2.line(..., 3)` ile cizilmis 3 piksel
     kalin izinden hesaplaniyordu. O 3 piksel IKA govdesini temsil etmez; ne
     eksik ne fazladir — KEYFIDIR. Olculen sey "cizgi bariyere degdi mi"ydi,
     "arac bariyere carpar mi" degil. sa_000131'de tam bu fark ortaya cikti:
     iz 3 px iken kesisim 8 px, iz 1 px iken 0 px.

BU BETIK ikisini de duzeltir ve K5'i K2 ILE AYNI TANIMA baglar (`61`):
rota, C-uzayiyla ayni yaricapla — `r_gerekli_px = R_GEREKLI_M / mpp` —
kalinlastirilir ve bariyer koluyla kesistirilir. Olcek her kare icin
manifest'ten okunur; ölçeksiz kare olcume GIRMEZ (olceksizken C-uzayi kapisi
kosamaz ve rota 1 piksellik bogazlardan siyrilir — sa_000131'de goruldu).

    kesisim = (r_gerekli_px ile kalin rota) ∩ (bariyer kolu)

K5 GECME OLCUTU (D-107): kesisim = 0 px. Populasyonda: kesen kare sayisi = 0.

Bariyer dedektoru MODELDEN BAGIMSIZDIR (LAB a* > 25, uzun-ince yatay bilesen)
ve `63`ten ITHAL edilir — iki yerde iki farkli bariyer tanimi olmasin.
"""
import argparse
import json
import sys
from importlib import import_module
from pathlib import Path

import cv2
import numpy as np

from ayarlar import REPO

BURASI = Path(__file__).parent
sys.path.insert(0, str(REPO / "codes"))
sys.path.insert(0, str(BURASI))

from costmap_path_finder import R_GEREKLI_M  # noqa: E402
from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp,  # noqa: E402
                           _preprocess, analyze_path, get_masks)

bariyer_maskesi = import_module("63_bariyer_kesisimi").bariyer_maskesi

KUME = BURASI / "calisma" / "sentetik_arena_kadraj_t66"
CONF = 0.30


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", type=Path, required=True)
    ap.add_argument("--kume", type=Path, default=KUME)
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    man = json.loads((args.kume / "manifest.json").read_text(encoding="utf-8"))

    from ultralytics import YOLO
    model = YOLO(str(args.model), task="segment")

    tarandi = bariyerli = olcekli = rota_var = kesen = 0
    kesisim_top = 0
    duyar, bogazlar, kesenler = [], [], []

    for ornek in man["ornekler"]:
        if ornek.get("durum") != "YAZILDI" or not ornek.get("arena"):
            continue
        p = args.kume / ornek["cikti"]
        if not p.is_file():
            continue
        tarandi += 1
        img = cv2.imread(str(p))
        if img is None:
            continue

        kol, kutular = bariyer_maskesi(img)
        if not kutular:
            continue                       # bariyersiz kare K5'e girmez
        bariyerli += 1
        mpp = ornek["arena"].get("mpp")
        if not mpp:
            continue                       # olceksiz kare OLCUME GIRMEZ
        olcekli += 1

        sq, small, icerik = _preprocess(img)
        h, w = sq.shape[:2]
        sonuc = model.predict(small, imgsz=INFER_SIZE, conf=CONF, verbose=False)
        # `get_masks` SOZLUK dondurur (anahtar = sinif id); ikili acilim
        # anahtarlari verir, maskeleri degil.
        mk = _maskeleri_icerige_kirp(get_masks(sonuc, h, w), icerik)
        trav, blok = mk[0], mk[1]

        # Bariyeri TUVAL cercevesine tasi. `_preprocess` icerigi OLCEKLEMEDEN
        # yerlestirir, bu yuzden tuval = ozgun + kaydirma; r_px ayni kalir.
        x0, y0, cw, ch = icerik
        kol_t = np.zeros((h, w), np.uint8)
        kol_t[y0:y0 + ch, x0:x0 + cw] = cv2.resize(
            kol, (cw, ch), interpolation=cv2.INTER_NEAREST)
        ust = kol_t > 0
        if not ust.any():
            continue
        duyar.append(float((blok[ust] > 0).mean()))

        _y, guven, wps, _k, red, olcum = analyze_path(
            trav, icerik=icerik, engel_mask=blok, mpp=mpp,
            return_clean=True, return_reason=True, return_olcum=True)
        if red is not None or not wps:
            continue                       # rota yok -> kesisim TANIMSIZ
        rota_var += 1
        bogazlar.append(olcum.get("darbogaz_px"))

        r_px = max(1, int(round(R_GEREKLI_M / mpp)))
        iz = np.zeros((h, w), np.uint8)
        pts = [(int(round(x)), int(round(y))) for x, y in wps]
        for a, b in zip(pts, pts[1:]):
            cv2.line(iz, a, b, 1, 2)
        iz = cv2.dilate(iz, cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (2 * r_px + 1, 2 * r_px + 1)))

        px = int(((iz > 0) & ust).sum())
        if px:
            kesen += 1
            kesisim_top += px
            kesenler.append({"kare": p.name, "px": px, "r_px": r_px,
                             "guven": guven,
                             "darbogaz_px": olcum.get("darbogaz_px")})

    bg = [b for b in bogazlar if b is not None]
    print(f"\n{'=' * 64}\nK5 POPULASYON · {args.model.name}")
    print(f"  olcut: (r_gerekli_px ile kalin rota) ∩ bariyer = 0 px  [D-107]")
    print("=" * 64)
    print(f"  taranan kare              : {tarandi}")
    print(f"  BARIYER iceren kare       : {bariyerli}")
    print(f"  bunlardan OLCEKLI         : {olcekli}")
    print(f"  bunlardan rota uretilen   : {rota_var}")
    print(f"  bariyer duyarliligi       : %{100 * float(np.mean(duyar)):.1f}"
          f"  (en dusuk %{100 * float(np.min(duyar)):.1f})")
    if bg:
        print(f"  darbogaz_px  ort/min      : {np.mean(bg):.1f} / {np.min(bg):.1f}")
    print("-" * 64)
    print(f"  GOVDE x BARIYER kesen kare: {kesen}/{rota_var}")
    print(f"  toplam kesisim            : {kesisim_top} px")
    print(f"  K5                        : "
          f"{'GECTI' if kesen == 0 else 'DUSTU'}")
    print("=" * 64)
    for k in kesenler[:10]:
        print(f"    {k['kare']}  {k['px']} px  r={k['r_px']}  "
              f"guven={k['guven']}  darbogaz={k['darbogaz_px']}")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(
            {"model": str(args.model), "tarandi": tarandi,
             "bariyerli": bariyerli, "olcekli": olcekli, "rota_var": rota_var,
             "duyar_ort": float(np.mean(duyar)),
             "duyar_min": float(np.min(duyar)),
             "kesen": kesen, "kesisim_px": kesisim_top, "kesenler": kesenler},
            ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\njson -> {args.json}")


if __name__ == "__main__":
    main()
