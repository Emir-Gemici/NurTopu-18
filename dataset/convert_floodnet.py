"""
FloodNet Supervised v1.0 → YOLOv8-seg dönüştürücü

Kaynak yapısı (indirilen haliyle):
  FloodNet-Supervised_v1.0/
    train/
      train-org-img/   {id}.jpg        (4000×3000 px)
      train-label-img/ {id}_lab.png    (4000×3000, grayscale, 0-9)
    val/
      val-org-img/     {id}.jpg
      val-label-img/   {id}_lab.png
    test/
      test-org-img/    {id}.jpg
      test-label-img/  {id}_lab.png

Sınıf eşlemesi:
  4 (road-nonflooded) → 0: traversable
  3 (road-flooded)    → 1: blocked
  Diğerleri ignore

Kullanım:
  python3 convert_floodnet.py --src ~/Downloads/FloodNet/FloodNet-Supervised_v1.0
  python3 convert_floodnet.py --src ~/Downloads/FloodNet/FloodNet-Supervised_v1.0 --size 640
"""

import argparse
import json
import sys
import numpy as np
import cv2
from pathlib import Path
from tqdm import tqdm

_here     = Path(__file__).parent
OUTPUT    = _here / "floodnet_yolo"
MIN_AREA  = 500        # büyük görseller için daha yüksek minimum
MAX_POLYS = 30
EPS_RATIO = 0.002
OUT_SIZE  = 1024       # resize hedefi (kare)

TRAVERSABLE = 4        # road-nonflooded
BLOCKED     = 3        # road-flooded


def mask_to_yolo(mask: np.ndarray, cls: int) -> list[str]:
    binary = (mask == 1).astype(np.uint8)
    cnts, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    lines = []
    h, w = mask.shape
    for cnt in cnts:
        if cv2.contourArea(cnt) < MIN_AREA:
            continue
        eps    = EPS_RATIO * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, eps, True)
        if len(approx) < 3:
            continue
        pts = approx.reshape(-1, 2).astype(float)
        pts[:, 0] /= w
        pts[:, 1] /= h
        pts = np.clip(pts, 0.0, 1.0)
        coords = " ".join(f"{x:.6f} {y:.6f}" for x, y in pts)
        lines.append(f"{cls} {coords}")
    return lines


def process_split(floodnet_root: Path, split: str, out_size: int) -> dict:
    # Klasör isimlendirme: train → train-org-img / train-label-img
    img_src = floodnet_root / split / f"{split}-org-img"
    lbl_src = floodnet_root / split / f"{split}-label-img"

    if not img_src.exists():
        print(f"  UYARI: {img_src} bulunamadı")
        return {"total": 0, "traversable": 0, "blocked": 0, "skipped": 0, "empty": 0}

    out_img = OUTPUT / "images" / split
    out_lbl = OUTPUT / "labels" / split
    out_img.mkdir(parents=True, exist_ok=True)
    out_lbl.mkdir(parents=True, exist_ok=True)

    img_files = sorted(img_src.glob("*.jpg")) + sorted(img_src.glob("*.JPG")) + sorted(img_src.glob("*.png"))
    stats = {"total": 0, "traversable": 0, "blocked": 0, "skipped": 0, "empty": 0}

    for img_path in tqdm(img_files, desc=f"  {split}"):
        stem     = img_path.stem               # "10165"
        lbl_path = lbl_src / f"{stem}_lab.png"

        if not lbl_path.exists():
            stats["skipped"] += 1
            continue

        img = cv2.imread(str(img_path))
        lbl = cv2.imread(str(lbl_path), cv2.IMREAD_GRAYSCALE)

        if img is None or lbl is None:
            stats["skipped"] += 1
            continue

        # Kare crop + resize (4000x3000 → merkezi 3000x3000 → out_size×out_size)
        oh, ow = img.shape[:2]
        side = min(oh, ow)
        y0 = (oh - side) // 2
        x0 = (ow - side) // 2
        img_sq = img[y0:y0+side, x0:x0+side]
        lbl_sq = lbl[y0:y0+side, x0:x0+side]

        img_rs = cv2.resize(img_sq, (out_size, out_size), interpolation=cv2.INTER_AREA)
        lbl_rs = cv2.resize(lbl_sq, (out_size, out_size), interpolation=cv2.INTER_NEAREST)

        trav_mask    = (lbl_rs == TRAVERSABLE).astype(np.uint8)
        blocked_mask = (lbl_rs == BLOCKED).astype(np.uint8)

        trav_lines    = sorted(mask_to_yolo(trav_mask,    0), key=len, reverse=True)[:MAX_POLYS]
        blocked_lines = sorted(mask_to_yolo(blocked_mask, 1), key=len, reverse=True)[:MAX_POLYS // 2]
        all_lines     = trav_lines + blocked_lines

        fname = f"floodnet_{split}_{stats['total']:05d}"
        cv2.imwrite(str(out_img / f"{fname}.jpg"), img_rs, [cv2.IMWRITE_JPEG_QUALITY, 92])
        with open(out_lbl / f"{fname}.txt", "w") as f:
            f.write("\n".join(all_lines))

        stats["total"]       += 1
        stats["traversable"] += len(trav_lines)
        stats["blocked"]     += len(blocked_lines)
        if not all_lines:
            stats["empty"] += 1

    return stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--src",  required=True,       help="FloodNet-Supervised_v1.0 klasörü")
    parser.add_argument("--size", type=int, default=OUT_SIZE, help=f"Çıktı boyutu (varsayılan: {OUT_SIZE})")
    args = parser.parse_args()

    root = Path(args.src).expanduser().resolve()
    if not root.exists():
        print(f"HATA: {root} bulunamadı")
        sys.exit(1)

    # Boyutu global'e uygula (basit yöntem)
    global MIN_AREA
    if args.size <= 512:
        MIN_AREA = 200

    print(f"Kaynak  : {root}")
    print(f"Çıktı   : {OUTPUT}")
    print(f"Boyut   : {args.size}×{args.size}")
    print()

    OUTPUT.mkdir(parents=True, exist_ok=True)
    all_stats = {}

    for split in ["train", "val", "test"]:
        print(f"=== {split} ===")
        all_stats[split] = process_split(root, split, args.size)
        s = all_stats[split]
        print(f"  → {s['total']} görsel | traversable={s['traversable']} | "
              f"blocked={s['blocked']} | boş={s['empty']} | atlanan={s['skipped']}\n")

    # data.yaml
    (OUTPUT / "data.yaml").write_text(f"""# FloodNet Supervised v1.0 — YOLOv8-seg
path: {OUTPUT.resolve()}
train: images/train
val:   images/val
test:  images/test

nc: 2
names:
  0: traversable
  1: blocked
""")

    with open(OUTPUT / "conversion_stats.json", "w") as f:
        json.dump(all_stats, f, indent=2)

    total = sum(s["total"] for s in all_stats.values())
    print("=" * 50)
    print(f"TAMAMLANDI: {total} görsel → {OUTPUT}")
    print(f"Merge için : python3 dataset/merge_datasets.py")


if __name__ == "__main__":
    main()
