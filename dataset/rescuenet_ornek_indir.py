"""
RescueNet (asolodin/rescuenet-roads) veri setinden BİRKAÇ örnek görüntü indirir —
Roboflow test ekranına sürükleyip modeli denemek için.

2GB'ın TAMAMINI indirmez: streaming ile yalnız ilk N görüntüyü çeker, jpg kaydeder.

ÖN KOŞUL:  pip install datasets pillow
KULLANIM:  python3 rescuenet_ornek_indir.py            # 10 val görüntüsü
           python3 rescuenet_ornek_indir.py --n 20     # daha fazla
           python3 rescuenet_ornek_indir.py --split test

Çıktı:  test_images/rescuenet_ornek/  → içindeki .jpg'leri Roboflow'a sürükle.
"""
import argparse
from pathlib import Path

_ROOT = Path(__file__).parent.parent
OUT = _ROOT / "test_images" / "rescuenet_ornek"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=10, help="indirilecek görüntü sayısı")
    ap.add_argument("--split", default="val", help="val / train / test")
    args = ap.parse_args()

    try:
        from datasets import load_dataset
    except ImportError:
        raise SystemExit("Önce: pip install datasets pillow")

    OUT.mkdir(parents=True, exist_ok=True)
    print("RescueNet streaming ile açılıyor (2GB indirmeden)...")
    ds = load_dataset("asolodin/rescuenet-roads", streaming=True)
    mevcut = list(ds.keys())
    print("Mevcut split'ler:", mevcut)

    # istenen split'e en yakın adı bul (val ↔ validation vb.)
    hedef = next((s for s in mevcut if args.split.lower() in s.lower()), None) \
        or next((s for s in mevcut if "val" in s.lower()), mevcut[0])
    print(f"Kullanılan split: {hedef}")

    n = 0
    for sample in ds[hedef]:
        img = sample["image"]                 # PIL.Image RGB
        if img.mode != "RGB":
            img = img.convert("RGB")
        p = OUT / f"rescuenet_{hedef}_{n:02d}.jpg"
        img.save(p, quality=92)
        n += 1
        print(f"  kaydedildi: {p.name}")
        if n >= args.n:
            break

    print(f"\n✓ {n} görüntü indirildi → {OUT}")
    print("Şimdi bu klasördeki .jpg'leri Roboflow test ekranına sürükle "
          "(Select Files ile çoklu seçebilirsin).")


if __name__ == "__main__":
    main()
