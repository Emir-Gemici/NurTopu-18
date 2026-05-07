"""
Semantic Drone Dataset → YOLOv8-seg format dönüştürücü

Dataset: Kaggle'dan indirilmesi gerekiyor (ücretsiz, kayıt şart)
  https://www.kaggle.com/datasets/bulentsiyah/semantic-drone-dataset
  veya: https://www.kaggle.com/datasets/awsaf49/semantic-drone-dataset

400 UAV görsel, 23 sınıf, 6000x4000px yüksek çözünürlük

Sınıf eşlemesi → 2 sınıf:
  traversable (0): paved-area(1), gravel(13), dirt(8), path(23)
  blocked (1)    : fence(9), wall(11), obstacle(22), tree(6), car(14), bicycle(15)
  ignore         : building, grass, vegetation, roof, sky, human, dog, etc.

Kullanım:
  1. Kaggle'dan dataset'i indir:
       https://www.kaggle.com/datasets/bulentsiyah/semantic-drone-dataset
     ZIP'i aç:
       semantic-drone-dataset/
         original_images/    ← RGB görüntüler (.jpg)
         label_images_semantic/  ← RGB etiketler (.png, sınıf renkleri)

  2. Bu scripti çalıştır:
       python3 download_semantic_drone.py --input /path/to/semantic-drone-dataset

Çıktı: dataset/semantic_drone_yolo/
"""

import argparse
import sys
import json
import numpy as np
import cv2
from pathlib import Path
from tqdm import tqdm

OUTPUT_DIR    = Path(__file__).parent / "semantic_drone_yolo"
MIN_AREA      = 500
MAX_POLYGONS  = 20
EPSILON_RATIO = 0.003
VAL_RATIO     = 0.15
TEST_RATIO    = 0.10

# Sınıf ID → (R, G, B) renk eşlemesi (SemanticDrone label görsellerindeki renkler)
# Kaynak: https://www.tugraz.at/index.php?id=22387
CLASS_COLORS = {
    "unlabeled"    : (0,   0,   0),
    "paved-area"   : (128, 64, 128),   # → traversable
    "dirt"         : (130, 76,  0),    # → traversable
    "grass"        : (0,  102,  0),    # → ignore
    "gravel"       : (112, 103, 87),   # → traversable
    "water"        : (28,  42, 168),   # → ignore
    "rocks"        : (48,  41, 30),    # → ignore
    "pool"         : (0,  50, 89),     # → ignore
    "vegetation"   : (107, 142, 35),   # → ignore
    "roof"         : (70,  70, 70),    # → ignore
    "wall"         : (102, 102, 156),  # → blocked
    "window"       : (254, 228, 12),   # → ignore
    "door"         : (254, 148,  12),  # → ignore
    "fence"        : (190, 153, 153),  # → blocked
    "fence-pole"   : (153, 153, 153),  # → blocked
    "person"       : (255,  22,  96),  # → blocked
    "dog"          : (102,  51,  0),   # → ignore
    "car"          : (9,   143, 150),  # → blocked
    "bicycle"      : (119,  11,  32),  # → blocked
    "tree"         : (51,   51,   0),  # → ignore
    "bald-tree"    : (190, 250, 190),  # → ignore
    "ar-marker"    : (112, 150, 146),  # → ignore
    "obstacle"     : (2,  135, 115),   # → blocked
    "conflicting"  : (255,   0,   0),  # → ignore
}

TRAVERSABLE_COLORS = {
    "paved-area", "dirt", "gravel"
}
BLOCKED_COLORS = {
    "wall", "fence", "fence-pole", "person", "car", "bicycle", "obstacle"
}


def rgb_to_class_mask(label_bgr: np.ndarray) -> tuple:
    """Label görselinden traversable ve blocked mask çıkar."""
    label_rgb = cv2.cvtColor(label_bgr, cv2.COLOR_BGR2RGB)
    trav_mask    = np.zeros(label_bgr.shape[:2], dtype=np.uint8)
    blocked_mask = np.zeros(label_bgr.shape[:2], dtype=np.uint8)

    for name, (r, g, b) in CLASS_COLORS.items():
        match = np.all(label_rgb == [r, g, b], axis=-1)
        if name in TRAVERSABLE_COLORS:
            trav_mask[match] = 1
        elif name in BLOCKED_COLORS:
            blocked_mask[match] = 1

    return trav_mask, blocked_mask


def mask_to_yolo_polygons(mask: np.ndarray, class_id: int, img_h: int, img_w: int):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    lines = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < MIN_AREA:
            continue
        eps    = EPSILON_RATIO * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, eps, True)
        if len(approx) < 3:
            continue
        pts = approx.reshape(-1, 2).astype(float)
        pts[:, 0] /= img_w
        pts[:, 1] /= img_h
        pts = np.clip(pts, 0.0, 1.0)
        coords = " ".join(f"{x:.6f} {y:.6f}" for x, y in pts)
        lines.append(f"{class_id} {coords}")
    return lines


def process_files(pairs, split_name: str):
    """pairs = [(img_path, lbl_path), ...]"""
    img_dir = OUTPUT_DIR / "images" / split_name
    lbl_dir = OUTPUT_DIR / "labels" / split_name
    img_dir.mkdir(parents=True, exist_ok=True)
    lbl_dir.mkdir(parents=True, exist_ok=True)

    stats = {"total": 0, "traversable": 0, "blocked": 0, "empty": 0}

    for i, (img_p, lbl_p) in enumerate(tqdm(pairs, desc=f"  {split_name}")):
        img = cv2.imread(str(img_p))
        lbl = cv2.imread(str(lbl_p))
        if img is None or lbl is None:
            print(f"  UYARI: okunamadı — {img_p.name}")
            continue

        h, w = lbl.shape[:2]
        trav_mask, blocked_mask = rgb_to_class_mask(lbl)

        trav_lines    = mask_to_yolo_polygons(trav_mask,    0, h, w)
        blocked_lines = mask_to_yolo_polygons(blocked_mask, 1, h, w)
        trav_lines    = sorted(trav_lines,    key=len, reverse=True)[:MAX_POLYGONS]
        blocked_lines = sorted(blocked_lines, key=len, reverse=True)[:MAX_POLYGONS // 2]
        all_lines     = trav_lines + blocked_lines

        fname = f"drone_{split_name}_{i:04d}"
        cv2.imwrite(str(img_dir / f"{fname}.jpg"), img, [cv2.IMWRITE_JPEG_QUALITY, 92])
        with open(lbl_dir / f"{fname}.txt", "w") as f:
            f.write("\n".join(all_lines))

        stats["total"] += 1
        stats["traversable"] += len(trav_lines)
        stats["blocked"] += len(blocked_lines)
        if not all_lines:
            stats["empty"] += 1

    return stats


def write_yaml():
    (OUTPUT_DIR / "data.yaml").write_text(f"""# Semantic Drone Dataset — YOLOv8-seg
path: {OUTPUT_DIR.resolve()}
train: images/train
val:   images/val
test:  images/test

nc: 2
names:
  0: traversable
  1: blocked
""")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True,
                        help="Kaggle'dan indirilen semantic-drone-dataset klasörü")
    args = parser.parse_args()

    root = Path(args.input)
    img_dir = root / "original_images"
    lbl_dir = root / "label_images_semantic"

    if not img_dir.exists():
        # Alternatif isim dene
        img_dir = root / "dataset" / "original_images"
        lbl_dir = root / "dataset" / "label_images_semantic"

    if not img_dir.exists():
        print(f"HATA: original_images klasörü bulunamadı: {root}")
        print("Beklenen yapı:")
        print("  <input>/original_images/*.jpg")
        print("  <input>/label_images_semantic/*.png")
        sys.exit(1)

    images = sorted(img_dir.glob("*.jpg")) + sorted(img_dir.glob("*.JPG"))
    labels = sorted(lbl_dir.glob("*.png"))
    print(f"Bulunan: {len(images)} görsel, {len(labels)} etiket")

    if len(images) != len(labels):
        print(f"UYARI: görsel/etiket sayısı eşleşmiyor ({len(images)} vs {len(labels)})")

    pairs = list(zip(images, labels))

    n      = len(pairs)
    n_val  = max(1, int(n * VAL_RATIO))
    n_test = max(1, int(n * TEST_RATIO))
    n_train = n - n_val - n_test

    np.random.seed(42)
    idx = np.random.permutation(n)
    train_pairs = [pairs[i] for i in idx[:n_train]]
    val_pairs   = [pairs[i] for i in idx[n_train:n_train + n_val]]
    test_pairs  = [pairs[i] for i in idx[n_train + n_val:]]

    print(f"Bölme: train={len(train_pairs)}  val={len(val_pairs)}  test={len(test_pairs)}\n")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stats = {}
    stats["train"] = process_files(train_pairs, "train")
    stats["val"]   = process_files(val_pairs,   "val")
    stats["test"]  = process_files(test_pairs,  "test")

    write_yaml()

    print("\n=== ÖZET ===")
    total = 0
    for split, s in stats.items():
        print(f"{split:6s}: {s['total']} görsel | "
              f"traversable={s['traversable']} | blocked={s['blocked']} | boş={s['empty']}")
        total += s["total"]
    print(f"Toplam: {total} görsel -> {OUTPUT_DIR}")

    with open(OUTPUT_DIR / "conversion_stats.json", "w") as f:
        json.dump(stats, f, indent=2)


if __name__ == "__main__":
    main()
