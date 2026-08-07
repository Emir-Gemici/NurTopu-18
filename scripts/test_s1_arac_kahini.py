"""S1 KAPISI: arac kahini degisiminin ETIKET UZERINDEKI etkisini olc.

Kapi olcutu (TASK_QUEUE S1): ayni ham fotografta uretilen `engel` maskesindeki
arac piksel sayisi COCO'ya gore EN AZ 10x artmali.

NEDEN piksel sayiyoruz, tespit degil: `yolo_etiketi()` sinif 0'i (zemin) daima
TAM KARE dikdortgen yazar ve engel poligonlari ustune biner. Yani engel
maskesine girmeyen her arac pikseli ZEMIN etiketi alir. Olculmesi gereken sey
"kac arac bulundu" degil, "kac piksel dogru etiketlendi"dir.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

KOK = Path(__file__).resolve().parents[1]
for _yol in (KOK / "codes", KOK / "scripts"):
    if str(_yol) not in sys.path:
        sys.path.insert(0, str(_yol))

from arac_maskesi import coco_arac_maskesi, obb_arac_maskesi, obb_modeli_mi
from rpi_inference import get_masks


def kareler(kok: Path, n: int) -> list[Path]:
    hepsi = sorted(p for p in kok.rglob("*") if p.suffix.lower() in (".jpg", ".jpeg", ".png"))
    if not hepsi:
        raise SystemExit(f"HATA: goruntu yok: {kok}")
    adim = max(1, len(hepsi) // n)
    return hepsi[::adim][:n]


def main() -> int:
    a = argparse.ArgumentParser(description="S1 kapisi: COCO seg vs DOTA OBB arac kahini")
    a.add_argument("--girdi", type=Path, default=KOK / "data" / "raw_frames")
    a.add_argument("--coco", type=Path, default=KOK / "yolov8m-seg.pt")
    a.add_argument("--obb", type=Path, default=KOK / "yolov8m-obb.pt")
    a.add_argument("--kare", type=int, default=10)
    a.add_argument("--conf", type=float, default=0.25)
    a.add_argument("--imgsz", type=int, default=640)
    a.add_argument("--esik", type=float, default=10.0, help="gecmek icin gereken kat")
    a.add_argument("--cikti", type=Path)
    args = a.parse_args()

    for yol in (args.coco, args.obb):
        if not yol.is_file():
            print(f"HATA: model yok: {yol}", file=sys.stderr)
            return 2

    gorseller = kareler(args.girdi, args.kare)
    m_coco = YOLO(str(args.coco))
    m_obb = YOLO(str(args.obb))

    if not obb_modeli_mi(m_obb):
        print(f"HATA: {args.obb.name} OBB modeli degil — kapi gecersiz", file=sys.stderr)
        return 2
    if obb_modeli_mi(m_coco):
        print(f"HATA: {args.coco.name} OBB gorunuyor — karsilastirma gecersiz", file=sys.stderr)
        return 2

    kayitlar = []
    print(f"{'kare':40s} {'COCO px':>10s} {'OBB px':>10s} {'kat':>8s}")
    print("-" * 72)
    for yol in gorseller:
        bgr = cv2.imread(str(yol))
        if bgr is None:
            continue
        px_toplam = bgr.shape[0] * bgr.shape[1]
        c = coco_arac_maskesi(bgr, m_coco, args.conf, args.imgsz, get_masks)
        o = obb_arac_maskesi(bgr, m_obb, conf=args.conf, imgsz=max(bgr.shape[:2]))
        c_px, o_px = int((c > 0).sum()), int((o > 0).sum())
        kat = (o_px / c_px) if c_px else (float("inf") if o_px else 0.0)
        kayitlar.append({"kare": yol.name, "coco_px": c_px, "obb_px": o_px,
                         "kat": None if kat == float("inf") else round(kat, 2),
                         "coco_oran": round(c_px / px_toplam * 100, 3),
                         "obb_oran": round(o_px / px_toplam * 100, 3)})
        print(f"{yol.name[:40]:40s} {c_px:10d} {o_px:10d} "
              f"{'inf' if kat == float('inf') else f'{kat:8.2f}'}")

    if not kayitlar:
        print("HATA: hicbir kare islenemedi", file=sys.stderr)
        return 1

    toplam_c = sum(k["coco_px"] for k in kayitlar)
    toplam_o = sum(k["obb_px"] for k in kayitlar)
    havuz_kat = (toplam_o / toplam_c) if toplam_c else float("inf")

    print("\n" + "=" * 72)
    print(f"TOPLAM  COCO {toplam_c} px   OBB {toplam_o} px")
    print(f"HAVUZ KATI: {'sonsuz (COCO sifir buldu)' if toplam_c == 0 else f'{havuz_kat:.2f}x'}")
    print(f"KAPI ESIGI: >= {args.esik:.0f}x")

    gecti = (toplam_c == 0 and toplam_o > 0) or (havuz_kat >= args.esik)
    print("KAPI:", "GECTI" if gecti else "DUSTU")
    print("=" * 72)

    if args.cikti:
        args.cikti.parent.mkdir(parents=True, exist_ok=True)
        args.cikti.write_text(json.dumps(
            {"esik_kat": args.esik, "toplam_coco_px": toplam_c, "toplam_obb_px": toplam_o,
             "havuz_kat": None if toplam_c == 0 else round(havuz_kat, 3),
             "kapi_gecti": bool(gecti), "kareler": kayitlar},
            ensure_ascii=False, indent=2), encoding="utf-8")
        print("JSON:", args.cikti)
    return 0 if gecti else 1


if __name__ == "__main__":
    raise SystemExit(main())
