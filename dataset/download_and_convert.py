"""
RescueNet-Roads → YOLOv8-seg format dönüştürücü

Dataset: asolodin/rescuenet-roads (HuggingFace)
  train: 2370 | val: 294 | test: 305
  512×512 aerial images, binary mask (0=non-road, 1=road)

YOLO çıktı yapısı:
  dataset/
    images/train/  images/val/  images/test/
    labels/train/  labels/val/  labels/test/
    data.yaml

Sınıflar:
  0: traversable  (road)
  1: blocked      (non-road / debris)
"""

import os
import sys
import json
import numpy as np
import cv2
from pathlib import Path
from tqdm import tqdm

OUTPUT_DIR = Path(__file__).parent / "rescuenet_yolo"
MIN_AREA = 200          # piksel — küçük gürültüyü at
MAX_POLYGONS = 30       # görüntü başına max instance (hafıza)
EPSILON_RATIO = 0.003   # contour basitleştirme oranı (×perimeter)
IMG_SIZE = 512


def mask_to_yolo_polygons(mask: np.ndarray, class_id: int, min_area: int = MIN_AREA):
    """
    Binary mask → YOLO seg satırları listesi
    Her connected component ayrı instance.
    """
    binary = (mask == 1).astype(np.uint8)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    lines = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area:
            continue
        eps = EPSILON_RATIO * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, eps, True)
        if len(approx) < 3:
            continue
        pts = approx.reshape(-1, 2).astype(float)
        pts[:, 0] /= IMG_SIZE
        pts[:, 1] /= IMG_SIZE
        pts = np.clip(pts, 0.0, 1.0)
        coords = " ".join(f"{x:.6f} {y:.6f}" for x, y in pts)
        lines.append(f"{class_id} {coords}")
    return lines


def process_split(dataset_split, split_name: str, img_dir: Path, lbl_dir: Path):
    img_dir.mkdir(parents=True, exist_ok=True)
    lbl_dir.mkdir(parents=True, exist_ok=True)

    stats = {"total": 0, "skipped": 0, "road_instances": 0, "blocked_instances": 0}

    for i, sample in enumerate(tqdm(dataset_split, desc=split_name)):
        img = sample["image"]         # PIL.Image RGB
        lbl = sample["label"]         # PIL.Image grayscale mask

        img_np = np.array(img.convert("RGB"))
        lbl_np = np.array(lbl)

        # RescueNet class IDs: 7=road-clear, 8=road-blocked, 0=background
        road_mask = (lbl_np == 7).astype(np.uint8)
        blocked_mask = (lbl_np == 8).astype(np.uint8)

        road_lines = mask_to_yolo_polygons(road_mask, class_id=0)
        blocked_lines = mask_to_yolo_polygons(blocked_mask, class_id=1)

        # Çok fazla instance varsa en büyükleri al
        road_lines = sorted(road_lines, key=lambda l: len(l), reverse=True)[:MAX_POLYGONS]
        blocked_lines = sorted(blocked_lines, key=lambda l: len(l), reverse=True)[:MAX_POLYGONS // 2]

        all_lines = road_lines + blocked_lines

        fname = f"{split_name}_{i:05d}"
        img_path = img_dir / f"{fname}.jpg"
        lbl_path = lbl_dir / f"{fname}.txt"

        cv2.imwrite(str(img_path), cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR),
                    [cv2.IMWRITE_JPEG_QUALITY, 95])

        with open(lbl_path, "w") as f:
            f.write("\n".join(all_lines))

        stats["total"] += 1
        stats["road_instances"] += len(road_lines)
        stats["blocked_instances"] += len(blocked_lines)
        if not all_lines:
            stats["skipped"] += 1

    return stats


def write_yaml(output_dir: Path):
    yaml_content = f"""# RescueNet-Roads — YOLOv8-seg
path: {output_dir.resolve()}
train: images/train
val: images/val
test: images/test

nc: 2
names:
  0: traversable
  1: blocked
"""
    (output_dir / "data.yaml").write_text(yaml_content)
    print(f"data.yaml yazıldı: {output_dir / 'data.yaml'}")


def main():
    print("HuggingFace datasets yükleniyor...")
    try:
        from datasets import load_dataset
    except ImportError:
        print("ERROR: pip install datasets")
        sys.exit(1)

    print("Dataset indiriliyor: asolodin/rescuenet-roads")
    print("(İlk indirmede ~1-2 GB, cache'den hızlı)")
    ds = load_dataset("asolodin/rescuenet-roads")

    splits = {
        "train": ds["train"],
        "val":   ds["validation"],
        "test":  ds["test"],
    }

    total_stats = {}
    for split_name, split_data in splits.items():
        img_dir = OUTPUT_DIR / "images" / split_name
        lbl_dir = OUTPUT_DIR / "labels" / split_name
        stats = process_split(split_data, split_name, img_dir, lbl_dir)
        total_stats[split_name] = stats
        print(f"\n{split_name}: {stats}")

    write_yaml(OUTPUT_DIR)

    print("\n=== ÖZET ===")
    for split, s in total_stats.items():
        print(f"{split:5s}: {s['total']} görüntü | "
              f"road={s['road_instances']} | blocked={s['blocked_instances']} | "
              f"boş={s['skipped']}")
    print(f"\nDataset hazır: {OUTPUT_DIR}")
    print(f"YAML: {OUTPUT_DIR / 'data.yaml'}")

    # Stats kaydet
    with open(OUTPUT_DIR / "conversion_stats.json", "w") as f:
        json.dump(total_stats, f, indent=2)


if __name__ == "__main__":
    main()
