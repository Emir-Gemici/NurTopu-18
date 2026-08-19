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

# ── T54 · SINIF ESLEME — TEK KAYNAKTAN (madde 16 · REVIEW_LOG D-195/D-199) ──
# ESKI KUSUR (D-67): yalniz road-clear(7)->0 ve road-blocked(8)->1 aliniyordu;
# bina/agac/su/havuz ETIKETSIZ ARKA PLANA dusuyordu. Etiketsiz arka plan
# denetim almaz -> modele hicbir yerde "cati zemin DEGILDIR" denmedi ->
# "genis duz yuzey = zemin" genellemesi (otopark %80,6 kaplama bundan).
#
# ⚠ IKI SEMA VARDIR ve KARISTIRILMISTI (D-195): HAM RescueNet id'leri
# (Note.txt: 0=Background..10=Pool) ile 11-sinif ara kumenin YOLO indeksleri
# AYNI DEGILDIR. Bu dosya HAM maskeyi okur -> HAM id kullanir. Tek kaynak
# `scripts/olcum/41_cok_sinifli_veri.py::SINIF_ESLEME`dir; buradan AST ile
# okunur, IKINCI BIR KOPYA YAZILMAZ (projenin 4x tekrar eden kusuru).
# 41 IMPORT EDILMEZ: modul `ayarlar` ithal eder ve makineye baglidir;
# `ast.literal_eval` yan etkisiz okur.
_ESLEME_AYNASI = Path(__file__).resolve().parent.parent / "scripts" / "olcum" / "41_cok_sinifli_veri.py"


def _sinif_esleme():
    import ast
    agac = ast.parse(_ESLEME_AYNASI.read_text(encoding="utf-8"))
    for dugum in ast.walk(agac):
        if isinstance(dugum, ast.Assign):
            for hedef in dugum.targets:
                if getattr(hedef, "id", None) == "SINIF_ESLEME":
                    return ast.literal_eval(dugum.value)
    raise RuntimeError(f"SINIF_ESLEME bulunamadi: {_ESLEME_AYNASI}")


SINIF_ESLEME = _sinif_esleme()
#: HAM id kumeleri ADLARDAN turetilir — ciplak id yazilmaz (madde 16).
TRAVERSABLE_HAM = {h for h, (_i, ad) in SINIF_ESLEME.items() if ad == "traversable"}
VEHICLE_HAM = {h for h, (_i, ad) in SINIF_ESLEME.items() if ad == "vehicle"}
# T54 ARAC KARARI — OLCULDU (D-199): DOTA OBB katmani RescueNet arac
# piksellerinin %0,0'ini yakaliyor (n=40 kare, 4.469.436 arac px, kesisim 0;
# urettigi maskelerin %100'u arac DISINA dustu — plane/harbor yanlis sinifi).
# Yani "cift sayim" endisesi BU VERIDE BOSTUR: egitim etiketi bu araclari
# kapsayan TEK seydir. ARAC ENGELDIR. (Uretimde egitilen kume
# `rescuenet_2sinif_engelli` de araci enge sayar — 57_t54_engel_eslemesi.)
BLOCKED_HAM = set(SINIF_ESLEME) - TRAVERSABLE_HAM
assert TRAVERSABLE_HAM and BLOCKED_HAM and VEHICLE_HAM <= BLOCKED_HAM


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

        # T54 (D-199): HAM id kumeleri TEK KAYNAKTAN turetildi (yukarida).
        # Eski satirlar yalniz 7/8 aliyordu; simdi zemin-olmayan HER etiketli
        # sinif ENGELDIR ("bilinmeyen -> engel", madde 15 ile ayni yon).
        road_mask = np.isin(lbl_np, sorted(TRAVERSABLE_HAM)).astype(np.uint8)
        blocked_mask = np.isin(lbl_np, sorted(BLOCKED_HAM)).astype(np.uint8)

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
    # T54 KORUMASI: `rescuenet_yolo` TARIHSEL egitim verisidir
    # (karisim_arena*.yaml v21-v27 donemi onu okur). Yeni eslemeyle SESSIZCE
    # uzerine yazmak, eski kosumlarin verisini geriye donuk DEGISTIRIR ve
    # yeniden uretilebilirligi kirar. Var olan cikti ancak ACIK bayrakla ezilir.
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--temizle", action="store_true",
                    help="cikti dizini VARSA sil ve yeniden uret (aksi halde durur)")
    args = ap.parse_args()
    if OUTPUT_DIR.exists() and not args.temizle:
        sys.exit(f"DUR: {OUTPUT_DIR} zaten var. Bu kume TARIHSEL karisimlarin "
                 "girdisidir; yeni eslemeyle ezmek icin --temizle verin. "
                 "(Uretimin 2 sinifli kumesi zaten `rescuenet_2sinif_engelli`dir "
                 "— 41 + 57 zinciri.)")
    if OUTPUT_DIR.exists():
        import shutil
        shutil.rmtree(OUTPUT_DIR)

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
