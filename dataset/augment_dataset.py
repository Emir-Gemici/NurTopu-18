"""
Veri Seti Augmentasyonu — Mevcut YOLO dataset'ini genişlet

Mevcut 2964 görsel → ~15.000+ görsel

Augmentasyonlar (YOLO polygon etiketleri de dönüştürülür):
  - Yatay ayna (flip_h)
  - Dikey ayna (flip_v)
  - 90° döndürme (rot90)
  - 180° döndürme (rot180)
  - 270° döndürme (rot270)
  - Parlaklık/kontrast ±30% (brightness)
  - Gaussian bulanıklık (blur — sis simülasyonu)
  - Gamma düzeltme (gamma)

Kullanım:
  python3 augment_dataset.py                     # rescuenet_yolo → augment eder
  python3 augment_dataset.py --src floodnet_yolo  # farklı kaynak
  python3 augment_dataset.py --factor 4           # her görsel için 4 augment (varsayılan: 4)
  python3 augment_dataset.py --splits train       # sadece train split'i

Çıktı: dataset/rescuenet_yolo_aug/ (veya --out ile belirt)
"""

import argparse
import random
import sys
import numpy as np
import cv2
from pathlib import Path
from tqdm import tqdm
import shutil

_here = Path(__file__).parent

# Her görsel için kaç farklı augmentasyon versiyonu
DEFAULT_FACTOR = 4

# Geometric augmentasyonlar — (isim, flip_h, flip_v, rotate_k)
GEOM_AUGS = [
    ("fh",    True,  False, 0),   # yatay ayna
    ("fv",    False, True,  0),   # dikey ayna
    ("r90",   False, False, 1),   # 90° saat yönü
    ("r180",  False, False, 2),   # 180°
    ("r270",  False, False, 3),   # 270° saat yönü
    ("fhr90", True,  False, 1),   # yatay + 90°
]

# Color/blur augmentasyonlar
COLOR_AUGS = [
    "brightness_up",
    "brightness_down",
    "contrast_up",
    "contrast_down",
    "blur",
    "gamma_up",
    "gamma_down",
    "noise",
]


def transform_polygon_geom(pts_norm: np.ndarray, flip_h: bool, flip_v: bool, rotate_k: int) -> np.ndarray:
    """
    YOLO normalized [x, y] polygon noktalarını geometric dönüşüme göre dönüştür.
    pts_norm: (N, 2) array, değerler [0, 1] aralığında
    """
    pts = pts_norm.copy()

    if flip_h:
        pts[:, 0] = 1.0 - pts[:, 0]

    if flip_v:
        pts[:, 1] = 1.0 - pts[:, 1]

    for _ in range(rotate_k % 4):
        # 90° saat yönü: (x, y) → (1-y, x)
        pts = np.stack([1.0 - pts[:, 1], pts[:, 0]], axis=1)

    return np.clip(pts, 0.0, 1.0)


def apply_geom_to_image(img: np.ndarray, flip_h: bool, flip_v: bool, rotate_k: int) -> np.ndarray:
    if flip_h:
        img = cv2.flip(img, 1)
    if flip_v:
        img = cv2.flip(img, 0)
    for _ in range(rotate_k % 4):
        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    return img


def apply_color_aug(img: np.ndarray, aug_name: str) -> np.ndarray:
    img = img.astype(np.float32)
    if aug_name == "brightness_up":
        img = img * random.uniform(1.15, 1.40)
    elif aug_name == "brightness_down":
        img = img * random.uniform(0.60, 0.85)
    elif aug_name == "contrast_up":
        mean = img.mean()
        img = (img - mean) * random.uniform(1.2, 1.5) + mean
    elif aug_name == "contrast_down":
        mean = img.mean()
        img = (img - mean) * random.uniform(0.6, 0.85) + mean
    elif aug_name == "gamma_up":
        gamma = random.uniform(1.3, 2.0)
        img = np.power(img / 255.0, 1.0 / gamma) * 255.0
    elif aug_name == "gamma_down":
        gamma = random.uniform(0.4, 0.7)
        img = np.power(img / 255.0, 1.0 / gamma) * 255.0
    elif aug_name == "blur":
        img = img.astype(np.uint8)
        ksize = random.choice([3, 5, 7])
        img = cv2.GaussianBlur(img, (ksize, ksize), 0).astype(np.float32)
    elif aug_name == "noise":
        noise = np.random.normal(0, random.uniform(5, 15), img.shape)
        img = img + noise

    img = np.clip(img, 0, 255).astype(np.uint8)
    return img


def read_label(lbl_path: Path):
    """YOLO polygon etiket dosyasını oku. [(class_id, pts_norm), ...] döner."""
    if not lbl_path.exists():
        return []
    lines = lbl_path.read_text().strip().splitlines()
    result = []
    for line in lines:
        if not line.strip():
            continue
        parts = line.split()
        cls = int(parts[0])
        coords = list(map(float, parts[1:]))
        if len(coords) < 6:  # min 3 nokta = 6 float
            continue
        pts = np.array(coords).reshape(-1, 2)
        result.append((cls, pts))
    return result


def write_label(lbl_path: Path, instances):
    """[(class_id, pts_norm), ...] → YOLO polygon formatında yaz."""
    lines = []
    for cls, pts in instances:
        coords = " ".join(f"{x:.6f} {y:.6f}" for x, y in pts)
        lines.append(f"{cls} {coords}")
    lbl_path.write_text("\n".join(lines))


def augment_split(src_img_dir: Path, src_lbl_dir: Path,
                  dst_img_dir: Path, dst_lbl_dir: Path,
                  factor: int, split_name: str):
    dst_img_dir.mkdir(parents=True, exist_ok=True)
    dst_lbl_dir.mkdir(parents=True, exist_ok=True)

    img_files = sorted(src_img_dir.glob("*.jpg")) + sorted(src_img_dir.glob("*.png"))
    if not img_files:
        print(f"  UYARI: {src_img_dir} — görsel yok")
        return 0

    # Orijinal görselleri önce kopyala
    print(f"  {split_name} orijinal kopyalanıyor...")
    for img_path in tqdm(img_files, desc=f"    copy"):
        dst_img = dst_img_dir / img_path.name
        dst_lbl = dst_lbl_dir / (img_path.stem + ".txt")
        shutil.copy2(img_path, dst_img)
        src_lbl = src_lbl_dir / (img_path.stem + ".txt")
        if src_lbl.exists():
            shutil.copy2(src_lbl, dst_lbl)
        else:
            dst_lbl.write_text("")

    # Augmentasyon
    print(f"  {split_name} augmentasyon ({factor}x)...")
    aug_count = 0

    # factor kadar augmentasyon grubu seç
    all_augs = []
    # Geometric augmentasyonlar (etiket dönüştürme gerekli)
    geom_names = [(name, flip_h, flip_v, rot) for name, flip_h, flip_v, rot in GEOM_AUGS]
    # Color augmentasyonlar (etiket değişmez)
    color_names = COLOR_AUGS.copy()

    # factor'a göre aug listesi oluştur
    used_augs = []
    if factor >= 1:
        used_augs.extend([("geom", *g) for g in geom_names[:min(factor, len(geom_names))]])
    if factor >= 4:
        used_augs.extend([("color", c, None, None, None) for c in color_names[:factor - len(geom_names)]])
    if len(used_augs) < factor:
        # Eksik kalan: renk augmentasyonu ekle
        for c in color_names:
            if len(used_augs) >= factor:
                break
            if ("color", c, None, None, None) not in used_augs:
                used_augs.append(("color", c, None, None, None))

    for img_path in tqdm(img_files, desc=f"    aug"):
        img = cv2.imread(str(img_path))
        if img is None:
            continue

        lbl_path = src_lbl_dir / (img_path.stem + ".txt")
        instances = read_label(lbl_path)

        for aug in used_augs[:factor]:
            aug_type = aug[0]

            if aug_type == "geom":
                _, aug_name, flip_h, flip_v, rot_k = aug
                aug_img = apply_geom_to_image(img.copy(), flip_h, flip_v, rot_k)
                aug_instances = [
                    (cls, transform_polygon_geom(pts, flip_h, flip_v, rot_k))
                    for cls, pts in instances
                ]
            else:  # color
                _, color_name = aug[0], aug[1]
                aug_img = apply_color_aug(img.copy(), color_name)
                aug_instances = instances  # etiket değişmez
                aug_name = color_name

            out_stem = f"{img_path.stem}_aug_{aug_name}"
            cv2.imwrite(str(dst_img_dir / f"{out_stem}.jpg"), aug_img,
                        [cv2.IMWRITE_JPEG_QUALITY, 90])
            write_label(dst_lbl_dir / f"{out_stem}.txt", aug_instances)
            aug_count += 1

    return len(img_files) + aug_count


def main():
    parser = argparse.ArgumentParser(description="YOLO Dataset Augmentasyonu")
    parser.add_argument("--src",    default="rescuenet_yolo", help="Kaynak dataset klasörü (varsayılan: rescuenet_yolo)")
    parser.add_argument("--out",    default=None,             help="Çıktı klasörü (varsayılan: <src>_aug)")
    parser.add_argument("--factor", type=int, default=4,      help="Her görsel için kaç augmentasyon (varsayılan: 4)")
    parser.add_argument("--splits", nargs="+", default=["train"], help="İşlenecek split'ler (varsayılan: train)")
    args = parser.parse_args()

    src_dir = _here / args.src
    out_dir = _here / (args.out or (args.src + "_aug"))

    if not src_dir.exists():
        print(f"HATA: Kaynak bulunamadı: {src_dir}")
        sys.exit(1)

    print(f"Kaynak   : {src_dir}")
    print(f"Çıktı    : {out_dir}")
    print(f"Factor   : {args.factor}x (orijinal + {args.factor} augmentasyon)")
    print(f"Splits   : {args.splits}\n")

    out_dir.mkdir(parents=True, exist_ok=True)
    total_counts = {}

    for split in args.splits:
        src_img = src_dir / "images" / split
        src_lbl = src_dir / "labels" / split
        dst_img = out_dir / "images" / split
        dst_lbl = out_dir / "labels" / split

        if not src_img.exists():
            print(f"UYARI: {split} split'i yok: {src_img}")
            continue

        print(f"=== {split} ===")
        total = augment_split(src_img, src_lbl, dst_img, dst_lbl, args.factor, split)
        total_counts[split] = total
        print(f"  {split}: {total} görsel\n")

    # Val ve test için sadece kopyala (augmentasyon yapma)
    for split in ["val", "test"]:
        if split in args.splits:
            continue
        src_img = src_dir / "images" / split
        src_lbl = src_dir / "labels" / split
        if not src_img.exists():
            continue
        dst_img = out_dir / "images" / split
        dst_lbl = out_dir / "labels" / split
        print(f"=== {split} (kopyalanıyor, augmentasyon yok) ===")
        dst_img.mkdir(parents=True, exist_ok=True)
        dst_lbl.mkdir(parents=True, exist_ok=True)
        img_files = list(src_img.glob("*.jpg")) + list(src_img.glob("*.png"))
        for f in img_files:
            shutil.copy2(f, dst_img / f.name)
        lbl_files = list(src_lbl.glob("*.txt"))
        for f in lbl_files:
            shutil.copy2(f, dst_lbl / f.name)
        total_counts[split] = len(img_files)
        print(f"  {split}: {len(img_files)} görsel\n")

    # data.yaml yaz
    src_yaml = src_dir / "data.yaml"
    if src_yaml.exists():
        content = src_yaml.read_text()
        # path'i güncelle
        import re
        content = re.sub(r'^path:.*$', f'path: {out_dir.resolve()}', content, flags=re.MULTILINE)
        (out_dir / "data.yaml").write_text(content)
    else:
        (out_dir / "data.yaml").write_text(f"""path: {out_dir.resolve()}
train: images/train
val:   images/val
test:  images/test

nc: 2
names:
  0: traversable
  1: blocked
""")

    print("=" * 50)
    print("ÖZET:")
    grand = 0
    for split, count in total_counts.items():
        print(f"  {split:6s}: {count:6d} görsel")
        grand += count
    print(f"  {'TOPLAM':6s}: {grand:6d} görsel")
    print(f"\nÇıktı: {out_dir}")
    print(f"Eğitim için: python3 codes/train_seg.py --data {out_dir / 'data.yaml'}")


if __name__ == "__main__":
    main()
