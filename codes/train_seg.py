"""
Navitas — YOLOv8-seg Eğitim Scripti
CPU (AMD Ryzen 7 5700U, 16 çekirdek, 18.7GB RAM) için optimize edildi.

Dataset : RescueNet (2365) + FloodNet filtered (798) = 3163 train görsel
Model   : yolov8n-seg (RPi'de NCNN ile ≥10 FPS)
Hedef   : mAP50 > 0.65, traversable/blocked aerial tespiti

Kullanım:
  python3 train_seg.py                         # varsayılan ayarlar
  python3 train_seg.py --model yolov8s-seg.pt  # daha büyük model (yavaş)
  python3 train_seg.py --data dataset/rescuenet_yolo/data.yaml  # tek dataset
  python3 train_seg.py --epochs 200 --no-export
"""

import argparse
from pathlib import Path
from ultralytics import YOLO

_here = Path(__file__).parent
_root = _here.parent

# ─── Varsayılanlar ──────────────────────────────────────────────────────────

DEFAULT_DATA   = _root / "dataset" / "combined_data.yaml"
DEFAULT_MODEL  = "yolov8n-seg.pt"
DEFAULT_EPOCHS = 150
RUN_NAME       = "navitas_seg_v2"


# ─── Eğitim ─────────────────────────────────────────────────────────────────

def train(data: Path, model_name: str, epochs: int, run_name: str):
    model = YOLO(model_name)

    results = model.train(
        data=str(data),
        epochs=epochs,
        imgsz=512,
        batch=8,                # CPU için optimum
        workers=10,             # 16 çekirdeğin 10'unu data loading'e ver
        device="cpu",

        name=run_name,
        project="runs/segment",

        # ── Optimizer ───────────────────────────────────────────────────────
        optimizer="AdamW",
        lr0=0.001,              # başlangıç öğrenme hızı
        lrf=0.005,              # bitiş öğrenme hızı (lr0 × lrf)
        momentum=0.937,
        weight_decay=0.0005,
        warmup_epochs=5,        # ilk 5 epoch LR yavaş yükselir
        warmup_momentum=0.8,
        cos_lr=True,            # cosine LR schedule — son dönemlerde daha iyi

        # ── Erken durdurma ──────────────────────────────────────────────────
        patience=40,            # 40 epoch iyileşme olmazsa dur

        # ── Geometrik augmentasyon (CPU'da on-the-fly, disk kaplaması yok) ─
        degrees=45.0,           # hava fotoğrafı her açıdan gelebilir
        flipud=0.5,             # dikey ayna
        fliplr=0.5,             # yatay ayna
        scale=0.5,              # zoom ±%50 (farklı irtifayı simüle eder)
        translate=0.1,          # kaydırma ±%10
        shear=2.0,              # hafif perspektif bozukluğu
        perspective=0.0,        # sıfır (nadir bakış perspektif değişmez)
        mosaic=1.0,             # 4 görsel birleştirme (küçük nesneler için iyi)
        close_mosaic=25,        # son 25 epoch mosaic kapat (fine-tune için)

        # ── Renk/parlaklık augmentasyon (gölge challengeine karşı) ─────────
        hsv_h=0.015,            # hue ±%1.5
        hsv_s=0.7,              # saturation ±%70
        hsv_v=0.5,              # value/brightness ±%50 ← gölge için kritik
        auto_augment=None,      # kendi ayarlarımızı kullan

        # ── Segmentasyon özel ───────────────────────────────────────────────
        copy_paste=0.15,        # instance copy-paste (nadir sınıf için iyi)
        erasing=0.2,            # random erasing (partial occlusion simülasyonu)
        mixup=0.0,              # segmentation'da zararlı, kapalı

        # ── Kaydetme ────────────────────────────────────────────────────────
        save=True,
        save_period=20,         # her 20 epoch checkpoint
        val=True,
        plots=True,
        verbose=True,

        # ── Kayıp ağırlıkları ───────────────────────────────────────────────
        box=7.5,
        cls=0.5,
        dfl=1.5,
        overlap_mask=True,
        mask_ratio=4,
    )
    return results


# ─── Export ─────────────────────────────────────────────────────────────────

def find_best_pt(run_name: str) -> Path | None:
    candidates = [
        _here / f"runs/segment/{run_name}/weights/best.pt",
        _here / f"runs/segment/runs/segment/{run_name}/weights/best.pt",
        Path(f"runs/segment/{run_name}/weights/best.pt"),
        Path(f"runs/segment/runs/segment/{run_name}/weights/best.pt"),
    ]
    return next((p for p in candidates if p.exists()), None)


def export_ncnn(run_name: str):
    best_pt = find_best_pt(run_name)
    if best_pt is None:
        print(f"HATA: best.pt bulunamadı. El ile şunu çalıştır:")
        print(f"  model = YOLO('runs/segment/{run_name}/weights/best.pt')")
        print(f"  model.export(format='ncnn', imgsz=512)")
        return

    print(f"\nNCNN export: {best_pt}")
    model = YOLO(str(best_pt))
    export_path = model.export(format="ncnn", imgsz=512)
    print(f"Export tamamlandı: {export_path}")

    # models/ klasörüne kopyala
    import shutil
    dst = _root / "models" / f"{run_name}_ncnn_model"
    if Path(str(export_path)).exists():
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(str(export_path), str(dst))
        print(f"models/ altına kopyalandı: {dst}")


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Navitas YOLOv8-seg Eğitimi")
    parser.add_argument("--data",      default=str(DEFAULT_DATA),  help="data.yaml yolu")
    parser.add_argument("--model",     default=DEFAULT_MODEL,      help="Model ağırlığı")
    parser.add_argument("--epochs",    type=int, default=DEFAULT_EPOCHS)
    parser.add_argument("--name",      default=RUN_NAME,           help="Run ismi")
    parser.add_argument("--no-export", action="store_true",        help="Eğitim sonrası export yapma")
    args = parser.parse_args()

    data = Path(args.data)
    if not data.exists():
        print(f"HATA: data.yaml bulunamadı: {data}")
        print("Seçenekler:")
        for f in (_root / "dataset").glob("*.yaml"):
            print(f"  {f}")
        return

    print("=" * 60)
    print(f"Model   : {args.model}")
    print(f"Dataset : {data}")
    print(f"Epochs  : {args.epochs}  (patience=40)")
    print(f"Run     : {args.name}")
    print(f"Device  : CPU (AMD Ryzen 7 5700U, 16 çekirdek)")
    print("=" * 60)

    results = train(data, args.model, args.epochs, args.name)

    print("\n=== Sonuçlar ===")
    try:
        print(f"mAP50      : {results.results_dict.get('metrics/mAP50(M)', 'N/A'):.4f}")
        print(f"mAP50-95   : {results.results_dict.get('metrics/mAP50-95(M)', 'N/A'):.4f}")
        print(f"Precision  : {results.results_dict.get('metrics/precision(M)', 'N/A'):.4f}")
        print(f"Recall     : {results.results_dict.get('metrics/recall(M)', 'N/A'):.4f}")
    except Exception:
        pass

    if not args.no_export:
        export_ncnn(args.name)


if __name__ == "__main__":
    main()
