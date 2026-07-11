"""
Navitas — YOLOv8-seg Eğitim Scripti v3 (GÜÇLENDİRME)

AMAÇ: mask mAP50'yi 0,60 takım hedefinin ÜSTÜNE çıkarmak (hedef ≥ 0,65).

v2 → v3 DEĞİŞİKLİKLERİ ve GEREKÇELERİ (kanıta dayalı):
  1. Model n → s : YOLOv8n-seg (3,4M) azınlık 'blocked' sınıfı için kapasite-kısıtlı.
     YOLOv8s-seg (11M) kapasiteyi 3× artırır. Jetson Orin NX'te TensorRT ile
     512px'de rahat >30 FPS → drone tarafı için sorun yok (algı Jetson'da, İKA
     değil). Tek en yüksek kaldıraç.
  2. degrees 45 → 15 : v2, v1'e göre blocked'ta GERİLEDİ (0,363 → 0,322). En olası
     sebep aşırı döndürme: val doğal yönde, train 45° döner → dağılım uyuşmazlığı,
     azınlık sınıf en çok zarar görür. 15° robustluğu korur, uyuşmazlığı azaltır.
  3. copy_paste 0.15 → 0.30 : instance kopyala-yapıştır AZINLIK sınıfı doğrudan
     çoğaltır (Ultralytics'in yerleşik dengeleme aracı).
  4. epochs 150 → 200, patience 40 → 60 : daha büyük model daha uzun yakınsar.
  5. (opsiyonel) dataset/oversample_blocked.py ile blocked görselleri fiziksel
     çoğaltılır → dataloader-bağımsız dengeleme.

GÜVENLİK AĞI: v1 (0,619) zaten 0,60'ı geçiyor. v3 başarısız olsa bile taban v1.
Bu yüzden v3 tamamen YUKARI YÖNLÜ risk.

Kullanım (Colab GPU):
  python3 train_seg_v3.py --device 0 --model yolov8s-seg.pt --epochs 200
  python3 train_seg_v3.py --device 0 --model yolov8m-seg.pt   # s yetmezse
  python3 train_seg_v3.py --device cpu --epochs 1 --smoke      # yerel duman testi
"""
import argparse
from pathlib import Path
from ultralytics import YOLO

_here = Path(__file__).parent
_root = _here.parent

DEFAULT_DATA   = _root / "dataset" / "combined_data.yaml"
DEFAULT_MODEL  = "yolov8s-seg.pt"    # v3: nano DEĞİL small
DEFAULT_EPOCHS = 200
RUN_NAME       = "navitas_seg_v3"


def train(data, model_name, epochs, run_name, device, batch, imgsz, smoke=False):
    model = YOLO(model_name)
    results = model.train(
        data=str(data),
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        device=device,
        workers=(2 if smoke else 8),
        name=run_name,
        project=str(_here / "runs/segment"),
        exist_ok=True,

        # ── Optimizer ──
        optimizer="AdamW",
        lr0=0.001,
        lrf=0.01,               # 200 epoch cosine için biraz daha yüksek bitiş
        momentum=0.937,
        weight_decay=0.0005,
        warmup_epochs=(0 if smoke else 5),
        warmup_momentum=0.8,
        cos_lr=True,

        # ── Erken durdurma ──
        patience=(0 if smoke else 60),

        # ── Geometrik augmentasyon (v3: degrees düşürüldü) ──
        degrees=15.0,           # v2: 45 → 15 (blocked gerilemesini geri al)
        flipud=0.5,
        fliplr=0.5,
        scale=0.5,
        translate=0.1,
        shear=2.0,
        perspective=0.0,
        mosaic=1.0,
        close_mosaic=(0 if smoke else 20),

        # ── Renk/parlaklık (gölge/loş ışık robustluğu) ──
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.5,
        auto_augment=None,

        # ── Segmentasyon özel (v3: copy_paste artırıldı) ──
        copy_paste=0.30,        # v2: 0.15 → 0.30 (azınlık sınıf boost)
        erasing=0.2,
        mixup=0.0,

        # ── Kayıp ağırlıkları ──
        box=7.5,
        cls=0.5,
        dfl=1.5,
        overlap_mask=True,
        mask_ratio=4,

        # ── Kaydetme ──
        save=True,
        save_period=(0 if smoke else 25),
        val=True,
        plots=(not smoke),
        verbose=True,
    )
    return results


def per_class_report(run_name, data, imgsz, device):
    """Eğitim sonrası best.pt'yi val edip SINIF BAZLI mAP döndür (dict)."""
    best = _here / f"runs/segment/{run_name}/weights/best.pt"
    if not best.exists():
        print(f"UYARI: best.pt yok: {best}")
        return None
    m = YOLO(str(best))
    r = m.val(data=str(data), imgsz=imgsz, split="val", device=device, plots=False)
    rapor = {
        "genel": {
            "mask_mAP50": round(r.seg.map50, 4),
            "mask_mAP50_95": round(r.seg.map, 4),
            "box_mAP50": round(r.box.map50, 4),
        },
        "sinif": {},
    }
    for i, ci in enumerate(r.ap_class_index):
        rapor["sinif"][r.names[int(ci)]] = round(float(r.seg.ap50[i]), 4)
    return rapor


def main():
    ap = argparse.ArgumentParser(description="Navitas YOLOv8-seg v3 güçlendirme")
    ap.add_argument("--data",   default=str(DEFAULT_DATA))
    ap.add_argument("--model",  default=DEFAULT_MODEL)
    ap.add_argument("--epochs", type=int, default=DEFAULT_EPOCHS)
    ap.add_argument("--name",   default=RUN_NAME)
    ap.add_argument("--device", default="0", help="'0' GPU, 'cpu' CPU")
    ap.add_argument("--batch",  type=int, default=16)
    ap.add_argument("--imgsz",  type=int, default=512)
    ap.add_argument("--smoke",  action="store_true", help="hızlı kod-yolu doğrulama")
    args = ap.parse_args()

    data = Path(args.data)
    if not data.exists():
        raise SystemExit(f"HATA: data.yaml yok: {data}")

    print("=" * 60)
    print(f"NAVITAS v3 GÜÇLENDİRME  ·  model={args.model}  epochs={args.epochs}")
    print(f"data={data}  device={args.device}  batch={args.batch}  imgsz={args.imgsz}")
    print("=" * 60)

    train(data, args.model, args.epochs, args.name,
          args.device, args.batch, args.imgsz, smoke=args.smoke)

    rapor = per_class_report(args.name, data, args.imgsz, args.device)
    if rapor:
        print("\n=== SINIF BAZLI SONUÇ ===")
        print(rapor)
        m = rapor["genel"]["mask_mAP50"]
        print(f"\nHedef mask mAP50 ≥ 0,60 → {m} →",
              "GEÇTİ ✓" if m >= 0.60 else "geçmedi ✗")


if __name__ == "__main__":
    main()
