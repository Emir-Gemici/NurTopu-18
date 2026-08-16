"""KARARSIZLIGIN MEKANIZMASI — seritler birbirine ne kadar yakin?

NEDEN (REVIEW_LOG D-142, acik madde). Doz egrisi tek yonlu cikti: gercek veri
arttikca `drone` yetenegi artiyor, koridor kararliligi bozuluyor.

    doz          karar cevrilmesi
    v28  0 kat     3/260 (%1,15)
    v32  2 kat     6/260 (%2,31)
    v30  4 kat     8/260 (%3,08)

AMA MEKANIZMA OLCULMEDI. "Gercek veri kararsizlik yapiyor" bir GOZLEMDIR,
aciklama degil. Aciklama olmadan T79 (beraberlik bozma + histerezis) GENEL
bir kural olarak yazilir ve asil sebebi vurmayabilir.

HIPOTEZ (mimar · OLCULMEDI, bu betigin sinayacagi sey):
    Gercek doku, maskeyi koridor KENARLARINDA daha gurultulu yapiyor.
    Seritlerin darboğaz degerleri birbirine YAKLASIYOR. Secim iki neredeyse
    esit aday arasinda yapildiginda, binde-4'luk bir gurultu tercihi cevirir.

    Olculebilir sonuc: v30/v32'nin SERIT PAYI (en iyi serit ile ikincisi
    arasindaki darbogaz farki) v28'inkinden KUCUK olmali.

BU BIR IDDIA DEGILDIR. Yanlis da olabilir: paylar ayni cikarsa kararsizlik
serit yakinligindan DEGIL baska bir seyden gelir (or. maskenin kendi
kararsizligi) ve T79 ona gore tasarlanmalidir.

Yer gercegi KULLANILMAZ. Sorulan "hangi serit dogru" degil, "seritler ne
kadar ayirt edilebilir".
"""
import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

from ayarlar import REPO

sys.path.insert(0, str(REPO / "codes"))

from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp,  # noqa: E402
                           _preprocess, analyze_path, get_masks)

KUME = Path(r"O:\navitas-local-train\calisma\sentetik_arena_kadraj_t66")
CONF = 0.30

MODELLER = {
    "v28 (0 kat)": Path(r"O:\navitas-local-train\calisma\v28_epoch200_last.pt"),
    "v32 (2 kat)": Path(r"O:\navitas-local-train\calisma\v32_best.pt"),
    "v30 (4 kat)": Path(r"O:\navitas-local-train\calisma\v30_best.pt"),
}


def serit_paylari(olcum):
    """(en_iyi, ikinci, pay) — None seritler elenir. Iki'den az serit varsa None."""
    sm = (olcum or {}).get("serit_min_px")
    if not sm:
        return None
    d = sorted((float(v) for v in sm if v is not None), reverse=True)
    if len(d) < 2:
        return None
    return d[0], d[1], d[0] - d[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kume", type=Path, default=KUME)
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    man = json.loads((args.kume / "manifest.json").read_text(encoding="utf-8"))
    from ultralytics import YOLO

    ozet = {}
    print(f"\n{'=' * 78}\nSERIT PAYI — seritler birbirinden ne kadar ayirt edilebilir?"
          f"\n{'=' * 78}")
    print(f"{'model':<14}{'n':>5}{'pay medyan':>12}{'pay %25':>10}"
          f"{'pay<2px':>10}{'pay<1px':>10}{'cok seritli':>13}")

    for ad, yol in MODELLER.items():
        if not yol.is_file():
            print(f"{ad:<14}  AGIRLIK YOK: {yol}")
            continue
        m = YOLO(str(yol), task="segment")
        paylar, cok_seritli, n = [], 0, 0
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
            sq, small, ic = _preprocess(img)
            r = m.predict(small, imgsz=INFER_SIZE, conf=CONF, verbose=False)
            mk = _maskeleri_icerige_kirp(get_masks(r, *sq.shape[:2]), ic)
            _y, _g, _w, _k, _red, olcum = analyze_path(
                mk[0], icerik=ic, engel_mask=mk[1], mpp=mpp,
                return_clean=True, return_reason=True, return_olcum=True)
            sp = serit_paylari(olcum)
            if sp is None:
                continue
            cok_seritli += 1
            paylar.append(sp[2])
        if not paylar:
            print(f"{ad:<14}{n:>5}   iki seritli kare YOK")
            continue
        a = np.array(paylar)
        print(f"{ad:<14}{n:>5}{np.median(a):>12.2f}{np.percentile(a, 25):>10.2f}"
              f"{int((a < 2).sum()):>10}{int((a < 1).sum()):>10}"
              f"{cok_seritli:>13}")
        ozet[ad] = {"n": n, "cok_seritli": cok_seritli,
                    "pay_medyan": float(np.median(a)),
                    "pay_p25": float(np.percentile(a, 25)),
                    "pay_alt2": int((a < 2).sum()),
                    "pay_alt1": int((a < 1).sum())}

    print(f"\n{'=' * 78}")
    print("OKUMA: `pay` = en iyi seridin darbogazi eksi IKINCI seridinki.")
    print("  Pay KUCULDUKCE iki aday esite yaklasir ve gurultu tercihi cevirir.")
    print("  Hipotez: v30/v32'nin payi v28'inkinden KUCUK olmali.")
    print("  Paylar AYNI cikarsa hipotez CURUR ve kararsizlik baska yerdendir.")
    print(f"{'=' * 78}")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(ozet, ensure_ascii=False, indent=1),
                             encoding="utf-8")
        print(f"json -> {args.json}")


if __name__ == "__main__":
    main()
