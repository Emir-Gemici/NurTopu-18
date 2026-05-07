"""
Ek Aerial Dataset İndirici — YOLOv8-seg formatına dönüştürür

Desteklenen dataset'ler:
  1. Dubai Aerial Segmentation (gymprathap/Semantic-Segmentation-Aerial-Imagery-Dataset)
     6 sınıf: building, land, road, vegetation, water, unlabeled
     road → traversable (0), building+land+su+other → blocked değil, ignore
     NOT: Bu dataset yol/moloz ayrımı değil genel aerial segmentation.

  2. MANUEL: FloodNet (BinaLab)
     https://github.com/BinaLab/FloodNet-Supervised_v1.0
     Google Drive'dan indir, aşağıdaki manual_floodnet_convert() fonksiyonunu kullan.

Kullanım:
  python3 download_extra_datasets.py --dubai          # Dubai otomatik
  python3 download_extra_datasets.py --floodnet /path/to/FloodNet-v1  # Manuel FloodNet

FloodNet manuel indirme:
  1. https://github.com/BinaLab/FloodNet-Supervised_v1.0 adresine git
  2. Google Drive linkinden zip'i indir
  3. Aç: FloodNet-Supervised_v1.0/ klasörünü edinin
  4. python3 download_extra_datasets.py --floodnet /path/to/FloodNet-Supervised_v1.0
"""

import argparse
import sys
import json
import numpy as np
import cv2
from pathlib import Path
from tqdm import tqdm

_here = Path(__file__).parent
MIN_AREA      = 200
MAX_POLYGONS  = 30
EPSILON_RATIO = 0.003


# ─── Ortak Yardımcı ─────────────────────────────────────────────────────────

def mask_to_yolo_polygons(mask: np.ndarray, class_id: int, min_area: int = MIN_AREA):
    binary = (mask == 1).astype(np.uint8)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    lines = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area:
            continue
        eps    = EPSILON_RATIO * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, eps, True)
        if len(approx) < 3:
            continue
        pts = approx.reshape(-1, 2).astype(float)
        h, w = mask.shape
        pts[:, 0] /= w
        pts[:, 1] /= h
        pts = np.clip(pts, 0.0, 1.0)
        coords = " ".join(f"{x:.6f} {y:.6f}" for x, y in pts)
        lines.append(f"{class_id} {coords}")
    return lines


def write_yaml(out_dir: Path, note: str = ""):
    (out_dir / "data.yaml").write_text(f"""# {note} — YOLOv8-seg
path: {out_dir.resolve()}
train: images/train
val:   images/val
test:  images/test

nc: 2
names:
  0: traversable
  1: blocked
""")


# ─── 1. Dubai Aerial Segmentation ───────────────────────────────────────────
# HuggingFace: gymprathap/Semantic-Segmentation-Aerial-Imagery-Dataset
# Sınıflar (RGB renk bazlı): Building(107,142,35) Land(102,102,156) Road(0,255,0)
# Vegetation(34,139,34) Water(0,0,255) Unlabeled(0,0,0)

DUBAI_CLASSES = {
    "road":        ((0, 255, 0),    0),   # traversable
    "building":    ((107, 142, 35), None),
    "land":        ((102, 102, 156),None),
    "vegetation":  ((34, 139, 34),  None),
    "water":       ((0, 0, 255),    None),
    "unlabeled":   ((0, 0, 0),      None),
}

DUBAI_OUT = _here / "dubai_yolo"


def decode_dubai_mask(mask_img: np.ndarray):
    """Dubai RGB mask → (trav_mask, blocked_mask) binary arrays."""
    if mask_img.ndim == 2:
        # Grayscale — class ID bazlı (0=background,1=building,2=land,3=road,4=veg,5=water,6=unlabeled)
        trav_mask    = (mask_img == 3).astype(np.uint8)
        # blocked: aslında burada bloklayan sınıf yok, sadece not-road
        # Bu dataset disaster değil, genel aerial — blocked sınıfı yok
        blocked_mask = np.zeros_like(trav_mask)
    else:
        # RGB mask
        rgb = cv2.cvtColor(mask_img, cv2.COLOR_BGR2RGB)
        trav_mask    = np.all(rgb == [0, 255, 0], axis=-1).astype(np.uint8)
        blocked_mask = np.zeros(mask_img.shape[:2], dtype=np.uint8)
    return trav_mask, blocked_mask


def download_dubai():
    try:
        from datasets import load_dataset
    except ImportError:
        print("HATA: pip install datasets")
        sys.exit(1)

    print("Dubai Aerial Segmentation indiriliyor...")
    print("gymprathap/Semantic-Segmentation-Aerial-Imagery-Dataset")
    try:
        ds = load_dataset("gymprathap/Semantic-Segmentation-Aerial-Imagery-Dataset")
    except Exception as e:
        print(f"HATA: {e}")
        sys.exit(1)

    print(f"Splits: {list(ds.keys())}")

    # Split map
    split_map = {}
    for k in ds.keys():
        kl = k.lower()
        if "train" in kl:
            split_map["train"] = k
        elif "val" in kl or "valid" in kl:
            split_map["val"] = k
        elif "test" in kl:
            split_map["test"] = k

    # Tek split varsa train/val/test'e böl
    if len(split_map) < 2:
        only_split = list(ds.keys())[0]
        n = len(ds[only_split])
        indices = list(range(n))
        np.random.seed(42)
        np.random.shuffle(indices)
        n_val  = max(1, int(n * 0.15))
        n_test = max(1, int(n * 0.10))
        split_map = {
            "train": (only_split, indices[:n - n_val - n_test]),
            "val":   (only_split, indices[n - n_val - n_test:n - n_test]),
            "test":  (only_split, indices[n - n_test:]),
        }
        manual_split = True
    else:
        manual_split = False

    DUBAI_OUT.mkdir(parents=True, exist_ok=True)
    all_stats = {}

    for our_split, split_info in split_map.items():
        img_dir = DUBAI_OUT / "images" / our_split
        lbl_dir = DUBAI_OUT / "labels" / our_split
        img_dir.mkdir(parents=True, exist_ok=True)
        lbl_dir.mkdir(parents=True, exist_ok=True)

        stats = {"total": 0, "traversable": 0, "empty": 0}

        if manual_split:
            ds_split_name, idx_list = split_info
            samples = [ds[ds_split_name][i] for i in tqdm(idx_list, desc=f"  {our_split}")]
        else:
            samples = tqdm(ds[split_info], desc=f"  {our_split}")

        for i, sample in enumerate(samples):
            try:
                img_key = next(k for k in sample if k in ("image", "img", "pixel_values"))
                msk_key = next(k for k in sample if k in ("label", "mask", "annotation", "segmentation_mask"))
            except StopIteration:
                print(f"  UYARI: {our_split}_{i:05d} — beklenen anahtarlar yok: {list(sample.keys())}")
                continue

            img_raw = sample[img_key]
            msk_raw = sample[msk_key]

            try:
                img_np = np.array(img_raw.convert("RGB")) if hasattr(img_raw, "convert") else np.array(img_raw)
                msk_np = np.array(msk_raw.convert("L")) if hasattr(msk_raw, "convert") else np.array(msk_raw)
            except Exception as e:
                print(f"  UYARI: decode: {e}")
                continue

            h, w = msk_np.shape[:2] if msk_np.ndim >= 2 else img_np.shape[:2]
            trav_mask, blocked_mask = decode_dubai_mask(msk_np)

            trav_lines    = mask_to_yolo_polygons(trav_mask,    0)
            blocked_lines = mask_to_yolo_polygons(blocked_mask, 1)
            trav_lines    = sorted(trav_lines,    key=len, reverse=True)[:MAX_POLYGONS]
            blocked_lines = sorted(blocked_lines, key=len, reverse=True)[:MAX_POLYGONS // 2]
            all_lines     = trav_lines + blocked_lines

            fname = f"dubai_{our_split}_{i:05d}"
            cv2.imwrite(str(img_dir / f"{fname}.jpg"),
                        cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR),
                        [cv2.IMWRITE_JPEG_QUALITY, 92])
            with open(lbl_dir / f"{fname}.txt", "w") as f:
                f.write("\n".join(all_lines))

            stats["total"] += 1
            stats["traversable"] += len(trav_lines)
            if not all_lines:
                stats["empty"] += 1

        all_stats[our_split] = stats
        print(f"  {our_split}: {stats}")

    write_yaml(DUBAI_OUT, "Dubai Aerial Segmentation")
    with open(DUBAI_OUT / "conversion_stats.json", "w") as f:
        json.dump(all_stats, f, indent=2)

    total = sum(s["total"] for s in all_stats.values())
    print(f"\nToplam: {total} görsel → {DUBAI_OUT}")
    print("NOT: Bu dataset disaster değil — sadece 'road' sınıfı traversable olarak etiketlendi.")
    print("     Blocked sınıfı yok. RescueNet ile birleştirmek için merge_datasets.py kullan.")


# ─── 2. Manuel FloodNet (BinaLab) ───────────────────────────────────────────
# FloodNet sınıf eşlemesi (piksel değerleri):
#   0=Background  1=Building-Flooded  2=Building-NonFlooded
#   3=Road-Flooded(→blocked)  4=Road-NonFlooded(→traversable)
#   5=Water  6=Tree  7=Vehicle  8=Pool  9=Grass

FLOODNET_OUT = _here / "floodnet_yolo"
FLOODNET_TRAV    = {4}   # road-non-flooded
FLOODNET_BLOCKED = {3}   # road-flooded


def convert_floodnet_folder(folder: Path, split_name: str):
    """
    FloodNet klasör yapısı:
      folder/
        train/      or      folder/
          image/              image/
          mask/               mask/
    """
    # Klasör yapısını bul
    for img_dir_candidate in [
        folder / split_name / "image",
        folder / split_name / "img",
        folder / f"{split_name}_image",
        folder / "image" / split_name,
    ]:
        if img_dir_candidate.exists():
            img_src = img_dir_candidate
            break
    else:
        print(f"  UYARI: {split_name} için image klasörü bulunamadı: {folder}")
        return {"total": 0, "traversable": 0, "blocked": 0, "empty": 0}

    for msk_dir_candidate in [
        folder / split_name / "mask",
        folder / split_name / "annotation",
        folder / f"{split_name}_mask",
        folder / "mask" / split_name,
        img_src.parent / "mask",
        img_src.parent / "annotation",
    ]:
        if msk_dir_candidate.exists():
            msk_src = msk_dir_candidate
            break
    else:
        print(f"  UYARI: {split_name} için mask klasörü bulunamadı")
        return {"total": 0, "traversable": 0, "blocked": 0, "empty": 0}

    print(f"  image: {img_src}")
    print(f"  mask : {msk_src}")

    img_files = sorted(img_src.glob("*.jpg")) + sorted(img_src.glob("*.JPG")) + sorted(img_src.glob("*.png"))
    if not img_files:
        print(f"  UYARI: Görsel bulunamadı: {img_src}")
        return {"total": 0, "traversable": 0, "blocked": 0, "empty": 0}

    out_img = FLOODNET_OUT / "images" / split_name
    out_lbl = FLOODNET_OUT / "labels" / split_name
    out_img.mkdir(parents=True, exist_ok=True)
    out_lbl.mkdir(parents=True, exist_ok=True)

    stats = {"total": 0, "traversable": 0, "blocked": 0, "empty": 0}

    for img_path in tqdm(img_files, desc=f"  {split_name}"):
        stem = img_path.stem
        msk_path = None
        for ext in [".png", ".jpg", ".JPG", ".tif"]:
            candidate = msk_src / (stem + ext)
            if candidate.exists():
                msk_path = candidate
                break

        if msk_path is None:
            continue

        img = cv2.imread(str(img_path))
        msk = cv2.imread(str(msk_path), cv2.IMREAD_GRAYSCALE)
        if img is None or msk is None:
            continue

        h, w = msk.shape
        trav_mask    = np.isin(msk, list(FLOODNET_TRAV)).astype(np.uint8)
        blocked_mask = np.isin(msk, list(FLOODNET_BLOCKED)).astype(np.uint8)

        trav_lines    = sorted(mask_to_yolo_polygons(trav_mask,    0), key=len, reverse=True)[:MAX_POLYGONS]
        blocked_lines = sorted(mask_to_yolo_polygons(blocked_mask, 1), key=len, reverse=True)[:MAX_POLYGONS // 2]
        all_lines = trav_lines + blocked_lines

        fname = f"floodnet_{split_name}_{stats['total']:05d}"
        cv2.imwrite(str(out_img / f"{fname}.jpg"), img, [cv2.IMWRITE_JPEG_QUALITY, 92])
        with open(out_lbl / f"{fname}.txt", "w") as f:
            f.write("\n".join(all_lines))

        stats["total"] += 1
        stats["traversable"] += len(trav_lines)
        stats["blocked"] += len(blocked_lines)
        if not all_lines:
            stats["empty"] += 1

    return stats


def manual_floodnet_convert(root: Path):
    print(f"FloodNet manuel dönüşümü: {root}")
    print(f"Çıktı: {FLOODNET_OUT}\n")

    FLOODNET_OUT.mkdir(parents=True, exist_ok=True)
    all_stats = {}

    for split in ["train", "val", "test"]:
        print(f"\n{split}:")
        stats = convert_floodnet_folder(root, split)
        all_stats[split] = stats
        print(f"  → {stats}")

    write_yaml(FLOODNET_OUT, "FloodNet Supervised v1.0")
    with open(FLOODNET_OUT / "conversion_stats.json", "w") as f:
        json.dump(all_stats, f, indent=2)

    total = sum(s["total"] for s in all_stats.values())
    print(f"\nToplam: {total} görsel → {FLOODNET_OUT}")


# ─── Main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dubai",    action="store_true",
                        help="Dubai Aerial Segmentation indir (HuggingFace)")
    parser.add_argument("--floodnet", type=str, metavar="KLASOR",
                        help="FloodNet Supervised v1.0 klasörünü YOLO formatına çevir")
    args = parser.parse_args()

    if not args.dubai and not args.floodnet:
        parser.print_help()
        print("\nÖrnek:")
        print("  python3 download_extra_datasets.py --dubai")
        print("  python3 download_extra_datasets.py --floodnet ~/Downloads/FloodNet-Supervised_v1.0")
        sys.exit(1)

    if args.dubai:
        download_dubai()

    if args.floodnet:
        manual_floodnet_convert(Path(args.floodnet))


if __name__ == "__main__":
    main()
