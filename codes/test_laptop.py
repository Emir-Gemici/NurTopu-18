"""
Laptop testi — görsel veya kamera
Kullanım:
  python3 codes/test_laptop.py --image test.jpg
  python3 codes/test_laptop.py --camera
"""

import argparse
from pathlib import Path
from ultralytics import YOLO

MODEL = Path(__file__).parent.parent / "models" / "rescuenet_seg_v1_best.pt"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=str, help="Görsel dosya yolu")
    parser.add_argument("--camera", action="store_true", help="Canlı kamera")
    parser.add_argument("--conf", type=float, default=0.25)
    args = parser.parse_args()

    if not args.image and not args.camera:
        parser.print_help()
        return

    model = YOLO(str(MODEL))

    if args.image:
        results = model.predict(
            args.image,
            imgsz=512,
            conf=args.conf,
            save=True,
            project="runs/test",
            name="predict",
        )
        print(f"Sonuç: runs/test/predict/{Path(args.image).name}")

    elif args.camera:
        import os
        os.environ["QT_QPA_PLATFORM"] = "xcb"
        model.predict(
            source=0,
            imgsz=512,
            conf=args.conf,
            show=True,
            stream=True,
        )


if __name__ == "__main__":
    main()
