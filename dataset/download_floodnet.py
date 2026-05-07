"""
FloodNet → YOLOv8-seg format dönüştürücü

Dataset: takara-ai/FloodNet_2021-Track_2_Dataset_HF (HuggingFace)
  ~2343 görsel, yüksek çözünürlük, aerial UAV (Hurricane Harvey sonrası)

FloodNet sınıf eşlemesi → bizim 2 sınıf:
  4 (road-non-flooded) → 0: traversable
  3 (road-flooded)     → 1: blocked
  Diğer sınıflar ignore edilir.

Çıktı: dataset/floodnet_yolo/
  images/train|val|test  + labels/train|val|test  + data.yaml

Kullanım:
  pip install datasets pillow tqdm
  python3 download_floodnet.py
"""

import sys
import json
import numpy as np
import cv2
from pathlib import Path
from tqdm import tqdm

OUTPUT_DIR   = Path(__file__).parent / "floodnet_yolo"
MIN_AREA     = 300
MAX_POLYGONS = 30
EPSILON_RATIO = 0.003
IMG_SIZE     = 512

# FloodNet piksel etiket değerleri
FLOODNET_TRAVERSABLE = {4}   # road-non-flooded
FLOODNET_BLOCKED     = {3}   # road-flooded
# 1=background 2=building-flooded 3=road-flooded 4=road-non-flooded
# 5=water 6=tree 7=vehicle 8=pool 9=grass


def mask_to_yolo_polygons(mask: np.ndarray, class_id: int, min_area: int = MIN_AREA):
    binary = (mask == 1).astype(np.uint8)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    lines = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_area:
            continue
        eps   = EPSILON_RATIO * cv2.arcLength(cnt, True)
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


def process_sample(sample, fname: str, img_dir: Path, lbl_dir: Path):
    """Tek örnek işle. (traversable_count, blocked_count) döner."""
    import io
    from PIL import Image as PILImage

    # Farklı anahtar isimlerini dene
    img_raw = (sample.get("image") or sample.get("img") or
               sample.get("pixel_values") or sample.get("photo"))
    lbl_raw = (sample.get("label") or sample.get("mask") or
               sample.get("annotation") or sample.get("segmentation_mask") or
               sample.get("semantic_segmentation"))

    if img_raw is None or lbl_raw is None:
        print(f"  UYARI: {fname} — image/label yok, atlanıyor. Anahtarlar: {list(sample.keys())}")
        return 0, 0

    def decode_image(raw, mode="RGB"):
        """PIL veya numpy veya bytes'tan array döndür."""
        if hasattr(raw, 'convert'):           # PIL Image
            return np.array(raw.convert(mode))
        if isinstance(raw, np.ndarray):
            return raw
        # bytes → cv2
        buf = np.frombuffer(bytes(raw) if not isinstance(raw, (bytes, bytearray)) else raw, np.uint8)
        arr = cv2.imdecode(buf, cv2.IMREAD_COLOR if mode == "RGB" else cv2.IMREAD_GRAYSCALE)
        if arr is None:
            # cv2 de başarısız → PIL ile dene
            arr = np.array(PILImage.open(io.BytesIO(bytes(raw))).convert(mode))
        if mode == "RGB" and arr.ndim == 3 and arr.shape[2] == 3:
            arr = cv2.cvtColor(arr, cv2.COLOR_BGR2RGB)
        return arr

    try:
        img_np = decode_image(img_raw, "RGB")
    except Exception as e:
        print(f"  UYARI: {fname} — görsel decode hatası: {e}")
        return 0, 0

    try:
        lbl_np = decode_image(lbl_raw, "L")
    except Exception as e:
        print(f"  UYARI: {fname} — etiket decode hatası: {e}")
        return 0, 0

    # Orijinal boyuta göre normalize et
    oh, ow = lbl_np.shape[:2]

    trav_mask    = np.isin(lbl_np, list(FLOODNET_TRAVERSABLE)).astype(np.uint8)
    blocked_mask = np.isin(lbl_np, list(FLOODNET_BLOCKED)).astype(np.uint8)

    trav_lines    = mask_to_yolo_polygons(trav_mask,    class_id=0)
    blocked_lines = mask_to_yolo_polygons(blocked_mask, class_id=1)

    trav_lines    = sorted(trav_lines,    key=len, reverse=True)[:MAX_POLYGONS]
    blocked_lines = sorted(blocked_lines, key=len, reverse=True)[:MAX_POLYGONS // 2]
    all_lines     = trav_lines + blocked_lines

    # Görsel kaydet (orijinal boyut, sıkıştırma uygula)
    img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
    cv2.imwrite(str(img_dir / f"{fname}.jpg"), img_bgr, [cv2.IMWRITE_JPEG_QUALITY, 92])

    with open(lbl_dir / f"{fname}.txt", "w") as f:
        f.write("\n".join(all_lines))

    return len(trav_lines), len(blocked_lines)


def process_split(ds_split, split_name: str):
    img_dir = OUTPUT_DIR / "images" / split_name
    lbl_dir = OUTPUT_DIR / "labels" / split_name
    img_dir.mkdir(parents=True, exist_ok=True)
    lbl_dir.mkdir(parents=True, exist_ok=True)

    stats = {"total": 0, "traversable": 0, "blocked": 0, "empty": 0}

    for i, sample in enumerate(tqdm(ds_split, desc=f"  {split_name}")):
        fname = f"floodnet_{split_name}_{i:05d}"
        t, b  = process_sample(sample, fname, img_dir, lbl_dir)
        stats["total"] += 1
        stats["traversable"] += t
        stats["blocked"] += b
        if t == 0 and b == 0:
            stats["empty"] += 1

    return stats


def write_yaml():
    (OUTPUT_DIR / "data.yaml").write_text(f"""# FloodNet 2021 — YOLOv8-seg
path: {OUTPUT_DIR.resolve()}
train: images/train
val:   images/val
test:  images/test

nc: 2
names:
  0: traversable
  1: blocked
""")


CANDIDATE_DATASETS = [
    ("takara-ai/FloodNet_2021-Track_2_Dataset_HF", {"verification_mode": "no_checks"}),
    ("torchgeo/floodnet", {}),
    ("PumeTu/FloodNet", {}),
]


def try_load_dataset(name: str, kwargs: dict):
    from datasets import load_dataset
    try:
        ds = load_dataset(name, **kwargs)
        splits = list(ds.keys())
        print(f"  splits: {splits}")
        return ds
    except Exception as e:
        print(f"  HATA: {e}")
        return None


def main():
    try:
        from datasets import load_dataset
    except ImportError:
        print("HATA: pip install datasets")
        sys.exit(1)

    print("FloodNet HuggingFace versiyonları deneniyor...\n")
    ds = None
    used_name = None
    for name, kwargs in CANDIDATE_DATASETS:
        print(f"Deneniyor: {name}")
        ds = try_load_dataset(name, kwargs)
        if ds is not None:
            used_name = name
            break

    if ds is None:
        print("\nTüm HuggingFace versiyonları başarısız.")
        print("Manuel indirme için: https://github.com/BinaLab/FloodNet-Supervised_v1.0")
        sys.exit(1)

    print(f"\nKullanılan: {used_name}")
    # Örnek anahtarları decode hatası olmadan göster (raw format)
    first_split = list(ds.keys())[0]
    try:
        sample = ds[first_split][0]
        print(f"Örnek anahtarlar: {list(sample.keys())}\n")
    except Exception as e:
        print(f"İlk örnek decode edilemedi: {e}")
        print("Script yine de devam ediyor...\n")

    # Split isimlerini normalize et
    split_map = {}
    for k in ds.keys():
        k_lower = k.lower()
        if "train" in k_lower:
            split_map["train"] = k
        elif "val" in k_lower:
            split_map["val"] = k
        elif "test" in k_lower:
            split_map["test"] = k

    if not split_map:
        print(f"HATA: Beklenen split bulunamadı. Mevcut: {list(ds.keys())}")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    all_stats = {}

    for our_name, ds_name in split_map.items():
        print(f"\n{our_name} ({ds_name}, {len(ds[ds_name])} örnek):")
        all_stats[our_name] = process_split(ds[ds_name], our_name)

    write_yaml()

    print("\n=== ÖZET ===")
    total_images = 0
    for split, s in all_stats.items():
        print(f"{split:6s}: {s['total']} görsel | "
              f"traversable={s['traversable']} | blocked={s['blocked']} | boş={s['empty']}")
        total_images += s["total"]
    print(f"\nToplam: {total_images} görsel")
    print(f"Klasör: {OUTPUT_DIR}")

    with open(OUTPUT_DIR / "conversion_stats.json", "w") as f:
        json.dump(all_stats, f, indent=2)


if __name__ == "__main__":
    main()
