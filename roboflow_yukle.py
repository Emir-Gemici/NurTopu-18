"""
Roboflow'a v3 segmentasyon modelini (navitas_seg_v3_best.pt) yükleme.

ÖN KOŞULLAR:
  1. Roboflow'da bir **Instance Segmentation** projesi (workspace: halils-workspace-wm5dh).
     - Roboflow → Create New Project → Project Type: **Instance Segmentation** → sınıflar: traversable, blocked.
  2. API key: Roboflow → Settings → API → "Private API Key".
  3. Proje ID: proje URL'sindeki kısa ad (ör. .../halils-workspace-wm5dh/<PROJE_ID>/...).

⚠️ UYARI (bilinen risk): Roboflow YOLOv8 için resmî olarak `ultralytics==8.0.196` bekler;
   bizim v3 modeli 8.4.92 ile eğitildi. Bu yüzden yükleme veya sunucu-tarafı çıkarım
   HATA verebilir. Verirse tek çözüm: modeli 8.0.196 ile yeniden eğitmek.

KULLANIM:
  export ROBOFLOW_API_KEY=xxx           # ya da script sorunca yapıştır
  python3 roboflow_yukle.py --project <PROJE_ID>
"""
import argparse
import os
import shutil
import sys
from pathlib import Path

_ROOT = Path(__file__).parent
MODEL = _ROOT / "models" / "navitas_seg_v3_best.pt"


def main():
    ap = argparse.ArgumentParser(description="v3 modelini Roboflow'a yükle")
    ap.add_argument("--project", required=True,
                    help="Roboflow Instance Segmentation proje ID'si")
    ap.add_argument("--workspace", default="halils-workspace-wm5dh")
    ap.add_argument("--model-type", default="yolov8-seg",
                    help="segmentasyon için yolov8-seg (uymazsa hata mesajı doğrusunu söyler)")
    ap.add_argument("--model-name", default="navitas-seg-v3")
    args = ap.parse_args()

    if not MODEL.exists():
        sys.exit(f"HATA: model bulunamadı: {MODEL}")

    key = os.environ.get("ROBOFLOW_API_KEY") or input("Roboflow Private API key: ").strip()
    if not key:
        sys.exit("HATA: API key gerekli.")

    # Roboflow, weights/best.pt yapısında bir klasör ister
    run = _ROOT / "roboflow_v3_run"
    (run / "weights").mkdir(parents=True, exist_ok=True)
    shutil.copy2(MODEL, run / "weights" / "best.pt")
    print(f"Model hazırlandı: {run}/weights/best.pt")

    try:
        from roboflow import Roboflow
    except ImportError:
        sys.exit("HATA: pip install roboflow")

    rf = Roboflow(api_key=key)
    ws = rf.workspace(args.workspace)
    print(f"Yükleniyor → workspace={args.workspace} · project={args.project} · "
          f"type={args.model_type} ...")
    try:
        ws.deploy_model(
            model_type=args.model_type,
            model_path=str(run),
            project_ids=[args.project],
            model_name=args.model_name,
            filename="weights/best.pt",
        )
    except Exception as e:
        print("\n❌ YÜKLEME HATASI:", e)
        print("Muhtemel sebep: ultralytics sürüm uyuşmazlığı (8.4.92 vs 8.0.196) veya "
              "proje tipi 'Instance Segmentation' değil.")
        print("→ Çözüm: modeli 8.0.196 ile yeniden eğit, ya da projeyi seg tipiyle yeniden aç.")
        sys.exit(1)

    print("\n✅ YÜKLENDİ. Sıradaki adım:")
    print("  Roboflow → projen → 'Models' (veya 'Deploy') sekmesi → test görüntüsü yükle")
    print("  → tahmini gör → EKRAN GÖRÜNTÜSÜ al.")
    print("  Test için RescueNet görüntüleri: dataset/rescuenet_yolo/images/val/ "
          "(Colab'da indiriliyordu) ya da elindeki herhangi bir hava görüntüsü.")


if __name__ == "__main__":
    main()
