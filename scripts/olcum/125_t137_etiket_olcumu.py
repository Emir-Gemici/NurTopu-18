"""T137 — ETIKETLEME KAPASITESI ve KALITESI icin OLCUM ALETI.

Bu betik ETIKET URETMEZ; etiketleme turunu OLCULEBILIR kilar:
  · `izgara`  : D-80 yordami — 100px izgarali TAM BOY gorunum uretir
                (T121'de anahtar poligonlar boyle yerlestirilmisti).
  · `maske`   : poligon listesini ikili maskeye rasterlestirir.
  · `iou`     : iki etiket kumesi arasinda kare kare IoU olcer.

🔴 OLCUM ZEMINI GUNDUZ KARELERIDIR. Gece karesinde etiketleme HIZLI cikar ama
YANLIS SEBEPTEN: bos kareyi etiketlemek kolaydir (D-271 §1). Bu yuzden zemin
`data/raw_frames` (67 kare, medyan L ~129) ve onun kaynaklaridir.

⚠ ENVANTER SINIRI (olculdu): depoda **67 AYRI gunduz karesi** vardir.
`dataset/copy_paste_gercek` 536 kayit tasir ama **AYRI KAYNAK sayisi yine 67**;
gerisi ayni karelerin varyantidir. Yani "200+ karelik buyuk parti" AYRI ICERIK
olarak MEVCUT DEGILDIR ve varyantla sisirmek yakin-kopya verimini olcerdi.

KIYAS ZEMINI: `results/t121/cati_anahtar_poligonlari.json` — 23 anahtar kare
Fable 5 tarafindan GOZLE yerlestirilmis ve UC gorsel turda dogrulanmistir
(D-80). Yer gercegi DEGILDIR, ama elde en iyi REFERANSTIR ve oyle anilir.
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

import cv2
import numpy as np

KOK = Path(__file__).resolve().parents[2]
T121_POLIGON = KOK / "results" / "t121" / "cati_anahtar_poligonlari.json"


def izgarali_gorunum(kare: Path, cikti: Path, adim: int = 100) -> Path:
    """D-80 yordami: 100px izgara + eksen etiketleri, TAM BOY (kucultme YOK).

    Kucultulmus gorunumde poligon yerlesimi sistematik kayar; T121'de bu
    yuzden tam boy kullanildi.
    """
    im = cv2.imread(str(kare))
    if im is None:
        raise SystemExit(f"kare okunamadi: {kare}")
    h, w = im.shape[:2]
    g = im.copy()
    for x in range(0, w, adim):
        cv2.line(g, (x, 0), (x, h), (0, 255, 255), 1)
        cv2.putText(g, str(x), (x + 2, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.4,
                    (0, 255, 255), 1)
    for y in range(0, h, adim):
        cv2.line(g, (0, y), (w, y), (0, 255, 255), 1)
        cv2.putText(g, str(y), (2, y + 14), cv2.FONT_HERSHEY_SIMPLEX, 0.4,
                    (0, 255, 255), 1)
    cikti.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(cikti), g, [cv2.IMWRITE_JPEG_QUALITY, 92])
    return cikti


def maske_kur(poligonlar, sekil) -> np.ndarray:
    """[[ [x,y], ... ], ...] -> ikili maske. Bos liste -> bos maske (GECERLI)."""
    h, w = sekil
    m = np.zeros((h, w), np.uint8)
    for p in poligonlar or []:
        if len(p) < 3:
            continue
        cv2.fillPoly(m, [np.asarray(p, dtype=np.int32)], 1)
    return m


def iou(a: np.ndarray, b: np.ndarray):
    """-> (iou|None, kesisim, birlesim). IKISI DE BOSSA None (tanimsiz).

    🔴 Bos-bos durumunu 1,0 saymak UYUMU SISIRIR: iki ajan da 'cati yok'
    dediginde bu bir ANLASMA gibi gorunur ama hicbir sey olculmemistir.
    Ayri raporlanir.
    """
    kes = int(np.count_nonzero(a & b))
    bir = int(np.count_nonzero(a | b))
    return (None if bir == 0 else kes / bir), kes, bir


def t121_referansi() -> dict:
    d = json.loads(T121_POLIGON.read_text(encoding="utf-8"))
    return {k: v.get("cati", []) for k, v in d["kareler"].items()}


def kume_yukle(yol: Path) -> dict:
    """{kare_anahtari: [poligon, ...]} bicimli etiket kumesi."""
    d = json.loads(Path(yol).read_text(encoding="utf-8"))
    if "kareler" in d:
        return {k: (v.get("cati", []) if isinstance(v, dict) else v)
                for k, v in d["kareler"].items()}
    return {k: (v.get("cati", []) if isinstance(v, dict) else v)
            for k, v in d.items() if not k.startswith("_")}


def kume_kiyasla(a: dict, b: dict, kare_koku: Path) -> dict:
    """Iki etiket kumesini ORTAK karelerde kiyasla."""
    ortak = sorted(set(a) & set(b))
    satir = []
    for anahtar in ortak:
        p = kare_koku / anahtar
        im = cv2.imread(str(p), cv2.IMREAD_GRAYSCALE)
        if im is None:
            satir.append({"kare": anahtar, "iou": None, "not": "kare okunamadi"})
            continue
        ma, mb = maske_kur(a[anahtar], im.shape), maske_kur(b[anahtar], im.shape)
        deger, kes, bir = iou(ma, mb)
        satir.append({"kare": anahtar, "iou": deger, "kesisim": kes,
                      "birlesim": bir,
                      "a_px": int(ma.sum()), "b_px": int(mb.sum())})
    olculen = [s["iou"] for s in satir if s.get("iou") is not None]
    return {"ortak_kare": len(ortak), "olculen": len(olculen),
            "ikisi_de_bos": len(satir) - len(olculen),
            "iou_medyan": float(np.median(olculen)) if olculen else None,
            "iou_ort": float(np.mean(olculen)) if olculen else None,
            "iou_min": float(min(olculen)) if olculen else None,
            "kareler": satir}


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError, OSError):
        pass
    ap = argparse.ArgumentParser()
    alt = ap.add_subparsers(dest="kip", required=True)

    g = alt.add_parser("izgara", help="D-80 izgarali gorunum uret")
    g.add_argument("--kare-koku", type=Path, default=KOK / "data" / "raw_frames")
    g.add_argument("--cikti", type=Path, required=True)
    g.add_argument("--liste", type=Path, help="JSON kare listesi; yoksa TUMU")

    k = alt.add_parser("iou", help="iki etiket kumesini kiyasla")
    k.add_argument("--a", type=Path, required=True)
    k.add_argument("--b", type=Path, required=True)
    k.add_argument("--kare-koku", type=Path, default=KOK / "data" / "raw_frames")
    k.add_argument("--cikti", type=Path)

    r = alt.add_parser("referans", help="T121 referans kumesini yaz")
    r.add_argument("--cikti", type=Path, required=True)

    args = ap.parse_args()

    if args.kip == "izgara":
        if args.liste:
            adlar = json.loads(args.liste.read_text(encoding="utf-8"))
        else:
            adlar = [str(p.relative_to(args.kare_koku)).replace("\\", "/")
                     for p in sorted(args.kare_koku.rglob("*.jpg"))]
        for ad in adlar:
            hedef = args.cikti / (ad.replace("/", "__").rsplit(".", 1)[0] + ".jpg")
            izgarali_gorunum(args.kare_koku / ad, hedef)
        print(f"izgarali gorunum: {len(adlar)} -> {args.cikti}")
        return 0

    if args.kip == "referans":
        ref = t121_referansi()
        args.cikti.parent.mkdir(parents=True, exist_ok=True)
        io.open(args.cikti, "w", encoding="utf-8").write(
            json.dumps({"_ne": "T121 REFERANS (gozle, uc gorsel tur — D-80). "
                               "Yer gercegi DEGIL.", "kareler": ref},
                       ensure_ascii=False, indent=1))
        print(f"referans: {len(ref)} kare -> {args.cikti}")
        return 0

    a, b = kume_yukle(args.a), kume_yukle(args.b)
    sonuc = kume_kiyasla(a, b, args.kare_koku)
    print(f"ortak kare {sonuc['ortak_kare']} · olculen {sonuc['olculen']} · "
          f"ikisi de bos {sonuc['ikisi_de_bos']}")
    print(f"IoU medyan {sonuc['iou_medyan']} · ort {sonuc['iou_ort']} · "
          f"min {sonuc['iou_min']}")
    if args.cikti:
        args.cikti.parent.mkdir(parents=True, exist_ok=True)
        io.open(args.cikti, "w", encoding="utf-8").write(
            json.dumps(sonuc, ensure_ascii=False, indent=1))
        print(f"yazildi: {args.cikti}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
