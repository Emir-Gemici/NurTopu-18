"""
Dataset Birleştirici — Birden fazla YOLO formatı dataset'i tek data.yaml'a bağlar.

Görsel/etiket KOPYALANMAZ. YOLO'ya birden fazla path veriliyor.
Yani disk alanı iki katına çıkmaz.

Kullanım:
  python3 merge_datasets.py               # otomatik tarar
  python3 merge_datasets.py --check       # kaç görsel var, kontrol et
  python3 merge_datasets.py --out merged_data.yaml   # özel çıktı adı

Mevcut dataset klasörleri otomatik taranır:
  dataset/rescuenet_yolo/
  dataset/floodnet_yolo/
  dataset/semantic_drone_yolo/
  dataset/<herhangi>_yolo/
"""

import argparse
import sys
from pathlib import Path

_here = Path(__file__).parent


def find_datasets():
    """dataset/ altındaki tüm *_yolo klasörlerini bul."""
    found = []
    for d in sorted(_here.glob("*_yolo")):
        yaml = d / "data.yaml"
        if yaml.exists() and (d / "images" / "train").exists():
            found.append(d)
    return found


def count_images(ds_dir: Path) -> dict:
    counts = {}
    for split in ["train", "val", "test"]:
        img_dir = ds_dir / "images" / split
        if img_dir.exists():
            n = len(list(img_dir.glob("*.jpg"))) + len(list(img_dir.glob("*.png")))
            counts[split] = n
        else:
            counts[split] = 0
    return counts


def build_merged_yaml(datasets: list, out_path: Path):
    """Çoklu train/val/test path'li data.yaml yaz."""
    train_paths = []
    val_paths   = []
    test_paths  = []

    for ds in datasets:
        train_dir = ds / "images" / "train"
        val_dir   = ds / "images" / "val"
        test_dir  = ds / "images" / "test"
        if train_dir.exists():
            train_paths.append(str(train_dir.resolve()))
        if val_dir.exists():
            val_paths.append(str(val_dir.resolve()))
        if test_dir.exists():
            test_paths.append(str(test_dir.resolve()))

    def fmt_paths(paths):
        if len(paths) == 1:
            return paths[0]
        return "\n" + "\n".join(f"  - {p}" for p in paths)

    yaml = f"""# Birleşik Dataset — YOLOv8-seg
# Otomatik üretildi: merge_datasets.py
# Dataset sayısı: {len(datasets)}

train: {fmt_paths(train_paths)}
val:   {fmt_paths(val_paths)}
test:  {fmt_paths(test_paths)}

nc: 2
names:
  0: traversable
  1: blocked
"""
    out_path.write_text(yaml)
    return train_paths, val_paths, test_paths


def main():
    parser = argparse.ArgumentParser(description="Dataset birleştirici")
    parser.add_argument("--check", action="store_true", help="Sadece istatistik göster")
    parser.add_argument("--out", default="merged_data.yaml", help="Çıktı YAML dosyası")
    args = parser.parse_args()

    datasets = find_datasets()

    if not datasets:
        print("HATA: Hiç dataset bulunamadı.")
        print("Önce indirme scriptlerini çalıştır:")
        print("  python3 download_and_convert.py   (RescueNet)")
        print("  python3 download_floodnet.py      (FloodNet)")
        sys.exit(1)

    print(f"Bulunan dataset'ler ({len(datasets)}):")
    print("-" * 55)

    grand_total = {"train": 0, "val": 0, "test": 0}
    for ds in datasets:
        counts = count_images(ds)
        print(f"  {ds.name:30s}  "
              f"train={counts['train']:5d}  val={counts['val']:4d}  test={counts['test']:4d}")
        for k in grand_total:
            grand_total[k] += counts[k]

    print("-" * 55)
    print(f"  {'TOPLAM':30s}  "
          f"train={grand_total['train']:5d}  val={grand_total['val']:4d}  test={grand_total['test']:4d}")

    if args.check:
        return

    out_path = _here / args.out
    train_paths, val_paths, test_paths = build_merged_yaml(datasets, out_path)

    print(f"\nYAML yazıldı: {out_path}")
    print("\nEğitim için kullan:")
    print(f"  python3 codes/train_seg.py --data {out_path.resolve()}")
    print("\nYa da train_seg.py içinde DATA_YAML'ı güncelle:")
    print(f"  DATA_YAML = \"{out_path.resolve()}\"")


if __name__ == "__main__":
    main()
