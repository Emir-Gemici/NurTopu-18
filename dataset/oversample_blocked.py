"""
Navitas — 'blocked' sınıfı dengeleme (oversampling)

SORUN: RescueNet'te blocked (moloz/kapalı) örnekleri traversable'a göre ~3,5×
az (train: 2327 road vs 660 blocked instance). Model azınlık sınıfı yeterince
göremediğinden blocked mAP düşük (v2: 0,322). Bu, genel mAP50'yi 0,60 hedefinin
altına çeken TEK sebep (traversable zaten 0,868).

ÇÖZÜM: blocked içeren görsel+etiket çiftlerini FİZİKSEL olarak çoğalt (kopya
dosyalar). Ultralytics dataloader'ın kopya-yolu tekilleştirme davranışından
BAĞIMSIZ çalışır (garanti oversampling). Idempotent: önceki `_ovs*` kopyaları
silip yeniden üretir, tekrar tekrar çalıştırılabilir.

Kullanım:
  python3 oversample_blocked.py --dir rescuenet_yolo --split train --copies 2
     → her blocked görselinden 2 EK kopya (toplam 3×). Sadece train'e uygula;
       val/test'e ASLA (ölçüm bozulur).

  python3 oversample_blocked.py --dir rescuenet_yolo --split train --clean
     → sadece eski kopyaları temizle (oversampling'i geri al).
"""
import argparse
import shutil
from pathlib import Path

OVS_SUFFIX = "_ovs"          # kopya dosyaları bu ekle işaretlenir


def find_pairs(img_dir: Path, lbl_dir: Path):
    """(image_path, label_path) çiftleri — etiketi olan görseller."""
    pairs = []
    for img in sorted(img_dir.iterdir()):
        if img.suffix.lower() not in (".jpg", ".jpeg", ".png"):
            continue
        if OVS_SUFFIX in img.stem:            # zaten kopya — atla
            continue
        lbl = lbl_dir / f"{img.stem}.txt"
        if lbl.exists():
            pairs.append((img, lbl))
    return pairs


def label_has_class(lbl_path: Path, class_id: int) -> bool:
    """Etiket dosyasında verilen sınıf var mı?"""
    try:
        for line in lbl_path.read_text().splitlines():
            line = line.strip()
            if line and line.split()[0] == str(class_id):
                return True
    except Exception:
        pass
    return False


def count_instances(pairs):
    """(road_instances, blocked_instances) — tüm çiftlerde toplam satır sayısı."""
    road = blocked = 0
    for _, lbl in pairs:
        for line in lbl.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            cid = line.split()[0]
            if cid == "0":
                road += 1
            elif cid == "1":
                blocked += 1
    return road, blocked


def clean_copies(img_dir: Path, lbl_dir: Path) -> int:
    """Önceki tüm `_ovs*` kopyalarını sil. Silinen dosya sayısını döner."""
    n = 0
    for d in (img_dir, lbl_dir):
        for f in d.glob(f"*{OVS_SUFFIX}*"):
            f.unlink()
            n += 1
    return n


def main():
    ap = argparse.ArgumentParser(description="blocked sınıfı oversampling")
    ap.add_argument("--dir", default="rescuenet_yolo",
                    help="dataset kök klasörü (images/ ve labels/ içerir)")
    ap.add_argument("--split", default="train", help="split (SADECE train önerilir)")
    ap.add_argument("--copies", type=int, default=2,
                    help="blocked görseli başına EK kopya sayısı (2 → toplam 3×)")
    ap.add_argument("--clean", action="store_true",
                    help="sadece eski kopyaları temizle, yeni üretme")
    args = ap.parse_args()

    base = Path(__file__).parent / args.dir
    img_dir = base / "images" / args.split
    lbl_dir = base / "labels" / args.split
    if not img_dir.is_dir() or not lbl_dir.is_dir():
        raise SystemExit(f"HATA: bulunamadı: {img_dir} veya {lbl_dir}")

    if args.split != "train":
        print(f"⚠ UYARI: '{args.split}' split'ine oversampling ÖLÇÜMÜ BOZAR. "
              "Yalnız train'e uygula.")

    # Her koşuda önce temizle (idempotent)
    silinen = clean_copies(img_dir, lbl_dir)
    if silinen:
        print(f"Eski kopyalar temizlendi: {silinen} dosya")
    if args.clean:
        pairs = find_pairs(img_dir, lbl_dir)
        r, b = count_instances(pairs)
        print(f"Temizlendi. Şu anki instance: road={r} blocked={b}")
        return

    pairs = find_pairs(img_dir, lbl_dir)
    r0, b0 = count_instances(pairs)
    blocked_pairs = [(i, l) for (i, l) in pairs if label_has_class(l, 1)]
    print(f"Başlangıç: {len(pairs)} görsel · road={r0} blocked={b0} instance "
          f"(oran 1:{r0/max(b0,1):.1f})")
    print(f"blocked içeren görsel: {len(blocked_pairs)} · her birine +{args.copies} kopya")

    uretilen = 0
    for img, lbl in blocked_pairs:
        for k in range(1, args.copies + 1):
            new_stem = f"{img.stem}{OVS_SUFFIX}{k}"
            shutil.copy2(img, img_dir / f"{new_stem}{img.suffix}")
            shutil.copy2(lbl, lbl_dir / f"{new_stem}.txt")
            uretilen += 1

    pairs2 = find_pairs_including_copies(img_dir, lbl_dir)
    r1, b1 = count_instances(pairs2)
    print(f"Üretilen kopya: {uretilen} çift")
    print(f"Sonuç: {len(pairs2)} görsel · road={r1} blocked={b1} instance "
          f"(oran 1:{r1/max(b1,1):.1f})")
    print("✓ Oversampling tamam — eğitim bu klasörü kullanınca blocked dengelenir.")


def find_pairs_including_copies(img_dir: Path, lbl_dir: Path):
    """Kopyalar dahil TÜM çiftler (sonuç sayımı için)."""
    pairs = []
    for img in sorted(img_dir.iterdir()):
        if img.suffix.lower() not in (".jpg", ".jpeg", ".png"):
            continue
        lbl = lbl_dir / f"{img.stem}.txt"
        if lbl.exists():
            pairs.append((img, lbl))
    return pairs


if __name__ == "__main__":
    main()
