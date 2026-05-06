"""
YOLOv8-seg eğitim scripti — RescueNet-Roads aerial segmentasyon

Hedef: mAP50 > 0.60, traversable/blocked tespiti
Export: NCNN (RPi 5 için)
"""

from ultralytics import YOLO
from pathlib import Path

DATASET_YAML = Path(__file__).parent.parent / "dataset" / "rescuenet_yolo" / "data.yaml"
RUN_NAME = "rescuenet_seg_v1"


def train():
    model = YOLO("yolov8n-seg.pt")

    results = model.train(
        data=str(DATASET_YAML),
        epochs=100,
        imgsz=512,
        batch=16,
        name=RUN_NAME,
        project="runs/segment",
        device="cpu",          # GPU varsa: device=0
        workers=4,
        patience=20,           # early stopping
        optimizer="AdamW",
        lr0=0.001,
        lrf=0.01,
        mosaic=1.0,
        degrees=15.0,          # aerial görüntü için rotasyon önemli
        flipud=0.5,
        fliplr=0.5,
        scale=0.3,
        translate=0.1,
        save=True,
        save_period=10,
        val=True,
        plots=True,
    )
    return results


def export_ncnn(run_name: str = RUN_NAME):
    # YOLO project="runs/segment" + name nested path
    candidates = [
        Path(f"runs/segment/{run_name}/weights/best.pt"),
        Path(f"runs/segment/runs/segment/{run_name}/weights/best.pt"),
    ]
    best_pt = next((p for p in candidates if p.exists()), None)
    if best_pt is None:
        print(f"ERROR: best.pt bulunamadı, kontrol et: {[str(c) for c in candidates]}")
        return
    model = YOLO(str(best_pt))
    model.export(format="ncnn", imgsz=512)
    print(f"NCNN export tamamlandı: {best_pt.parent}")


if __name__ == "__main__":
    if not DATASET_YAML.exists():
        print(f"ERROR: Dataset bulunamadı: {DATASET_YAML}")
        print("Önce çalıştır: python dataset/download_and_convert.py")
    else:
        print(f"Dataset: {DATASET_YAML}")
        results = train()
        print("\nEğitim bitti. NCNN export...")
        export_ncnn()
