"""ÇOK SINIFLI ÖN EĞİTİM → 2 SINIFA FINE-TUNE (sıçrama denemesi).

HİPOTEZ: RescueNet'in 10 sınıfından 8'ini atıyoruz. Oysa Building_Total_Destruction(6)
ve Tree(8) MOLOZU tarif ediyor — 'blocked' sınıfının tanımı tam da bu. Görsel doğrulama
(scratch_11dogrula.py) bunu teyit etti: molozla kaplı yol (blocked) etrafı yıkılmış bina
ve devrilmiş ağaçlarla çevrili. Model bu bağlamı öğrenirse yol/moloz ayrımı güçlenebilir.

İKİ AŞAMA:
  1) ÖN EĞİTİM: yolov8m-seg (COCO) → 10 sınıflı RescueNet, imgsz 640
  2) FINE-TUNE : aşama-1 ağırlığı → 2 sınıflı veri (rescuenet_yolo), v9 reçetesi (mixup)
     => SON MODEL nc=2, yolov8m@640. Çıkarım maliyeti değişmez → FPS KORUNUR.

ÖLÇEK TUTARLILIĞI: 10 sınıflı veri 1024x768 ama imgsz=640 ile eğitiliyor → yol ~32 px.
2 sınıflı veri 512 kaynak, imgsz=640 → yol ~32 px. İKİ AŞAMA AYNI NESNE ÖLÇEĞİNDE.

KIYAS TABANI: v9_mixup_full (bakir test mask mAP50 0,6787 · blocked 0,5371).
Aşama 2, v9 ile BİREBİR aynı reçete — tek fark başlangıç ağırlığı (COCO yerine
10-sınıf ön eğitimli). Yani temiz A/B.

Kesintiye dayanıklı: her aşama 32_dayanikli_egitim.py ile koşar, tamamlanan atlanır.

Kullanım:
  venv\\Scripts\\python.exe 42_cok_sinifli_onegitim.py
  venv\\Scripts\\python.exe 42_cok_sinifli_onegitim.py --on-epoch 150 --ft-epoch 200
"""
import argparse
import subprocess
import sys
from pathlib import Path

from ayarlar import REPO, DATA_YAML

PYTHON = Path(sys.executable)
BURASI = Path(__file__).parent
RUNS = REPO / "codes" / "runs" / "segment"
DURUM_KOK = BURASI / "calisma" / "egitim_durumu"
COK_YAML = REPO / "dataset" / "rescuenet_11sinif" / "data.yaml"

ON_AD = "v15_on10sinif"      # aşama 1
FT_AD = "v15_ft2sinif"       # aşama 2 (nihai aday)


def son_epoch(ad):
    p = RUNS / ad / "results.csv"
    if not p.exists():
        return 0
    try:
        return max(0, sum(1 for _ in p.open(encoding="utf-8")) - 1)
    except Exception:
        return 0


def bitti_mi(ad, epochs):
    if son_epoch(ad) >= epochs:
        return True
    log = DURUM_KOK / f"{ad}.log"
    if log.exists():
        try:
            return "EĞİTİM TAMAMLANDI" in log.read_text(encoding="utf-8", errors="replace")
        except Exception:
            pass
    return False


def egit(ad, model, data, epochs, batch, ekstra):
    if bitti_mi(ad, epochs):
        print(f"[{ad}] zaten tamamlanmış ({son_epoch(ad)} epoch), atlanıyor", flush=True)
        return True
    print(f"\n{'#' * 64}\n[{ad}] model={model}\n  data={data}\n"
          f"  {epochs} epoch · batch {batch} · {' '.join(ekstra)}\n{'#' * 64}", flush=True)
    subprocess.run([
        str(PYTHON), str(BURASI / "32_dayanikli_egitim.py"),
        "--ad", ad, "--data", str(data), "--model", str(model),
        "--imgsz", "640", "--epochs", str(epochs), "--batch", str(batch),
        "--tekrar", "8", *ekstra,
    ])
    return (RUNS / ad / "weights" / "best.pt").exists()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--on-epoch", type=int, default=150)
    ap.add_argument("--ft-epoch", type=int, default=200)
    ap.add_argument("--batch", type=int, default=12)   # v5c/v9 ile aynı
    args = ap.parse_args()

    if not COK_YAML.exists():
        raise SystemExit(f"10 sınıflı veri yok: {COK_YAML}\nÖnce: 41_cok_sinifli_veri.py")

    print("ÇOK SINIFLI ÖN EĞİTİM DENEYİ")
    print(f"  aşama 1: COCO → 10 sınıf ({args.on_epoch} epoch)")
    print(f"  aşama 2: → 2 sınıf, v9 reçetesi/mixup ({args.ft_epoch} epoch)")
    print(f"  kıyas tabanı: v9_mixup_full = 0,6787 / blocked 0,5371\n")

    # ── AŞAMA 1: çok sınıflı ön eğitim ──
    # mixup YOK: ön eğitimin amacı zengin temsil, augment karmaşası değil.
    if not egit(ON_AD, "yolov8m-seg.pt", COK_YAML, args.on_epoch, args.batch, []):
        raise SystemExit("aşama 1 tamamlanamadı")

    on_best = RUNS / ON_AD / "weights" / "best.pt"
    print(f"\n✓ Aşama 1 bitti: {on_best}")

    # ── AŞAMA 2: 2 sınıfa fine-tune, v9 reçetesi birebir ──
    if not egit(FT_AD, on_best, DATA_YAML, args.ft_epoch, args.batch,
                ["--copy_paste_mode", "mixup"]):
        raise SystemExit("aşama 2 tamamlanamadı")

    # ── Değerlendirme: bakir test ──
    print(f"\n[{FT_AD}] BAKIR TEST DEĞERLENDİRMESİ", flush=True)
    subprocess.run([
        str(PYTHON), str(BURASI / "11_capraz_dogrulama.py"),
        "--model", str(RUNS / FT_AD / "weights" / "best.pt"), "--ad", FT_AD,
        "--not", "10-sinif on egitim -> 2 sinif ft (v9 recetesi)",
    ])

    import defter
    print(f"\n{'=' * 66}\nSONUÇ\n{'=' * 66}")
    # NOT: sistem kararı YALNIZ traversable maskesini kullanıyor (6 analyze_path
    # çağrısının hepsi masks[0]) → traversable birincil metrik. blocked yalnız
    # rapor/mAP için. Bkz. 44_karar_kurali.md
    print(f"{'model':22} {'mAP50':>8} {'traversable':>12} {'blocked':>9}")
    print(f"{'v9_mixup (TABAN)':22} {0.6787:>8.4f} {0.8204:>12.4f} {0.5371:>9.4f}")
    print(f"{'v13_box10':22} {0.6794:>8.4f} {0.8485:>12.4f} {0.5102:>9.4f}")
    for k in defter.oku():
        if k["ad"] == FT_AD and k["split"] == "test" and k.get("mask_mAP50"):
            m = float(k["mask_mAP50"])
            t = float(k["traversable_AP50"])
            b = float(k["blocked_AP50"])
            print(f"{FT_AD:22} {m:>8.4f} {t:>12.4f} {b:>9.4f}")
            print(f"\n  v9'a göre: mAP {m - 0.6787:+.4f} · "
                  f"traversable {t - 0.8204:+.4f} · blocked {b - 0.5371:+.4f}")
            print("\n  UYARI: bakir testte gürültü sd≈0,03 (mask) / 0,05 (blocked).")
            print("  Bu farklar ANCAK eşleştirilmiş testle doğrulanırsa gerçektir:")
            print(f"    python 13_altkume_kararlilik.py --modeller "
                  f"{RUNS / FT_AD / 'weights' / 'best.pt'} v9 --n 40")
            print("    → galibiyet >= 35/40 değilse FARK YOKTUR.")
            if m - 0.6787 > 0.04 or t - 0.8204 > 0.04:
                print("\n  → Fark gürültü bandının ÜSTÜNDE; eşleştirilmiş testle teyit et.")
            else:
                print("\n  → Fark gürültü bandının içinde; yardımcı görev hipotezi "
                      "bu ölçümle DOĞRULANMADI.")


if __name__ == "__main__":
    main()
