"""T53 — KOSULMAMIS HUCRE: 11-sinif on-egitim + GERCEK DOKU karisimi.

NEDEN (TASK_QUEUE T53, REVIEW_LOG D-61..D-65 · olculmus):

    model          K0 duyar  K0 kare>%1  K1 IoU  K1 kesin  K2 otopark  egitim
    v15_ft2sinif      0.134         2/9   0.425     0.804      24.1%   on-egitim VAR, gercek doku YOK
    v17               0.010         1/9   0.315     0.807       0.9%   v15 + sentetik fine-tune
    v21 (uretim)      0.890         9/9   0.311     0.813      81.0%   gercek doku VAR, on-egitim YOK

11-sinif on-egitim alan-ici dogrulugu ve asiri-tespit frenini veriyor; gercek
doku karisimi korlugu aciyor. IKISI HIC AYNI KOSUDA BIRLESTIRILMEDI.
`42_cok_sinifli_onegitim.py` asama 2'yi `ayarlar.DATA_YAML` ile — yani YALNIZ
rescuenet_yolo ile — kosuyor; sentetik arena ve gercek doku o adima hic girmiyor.

BU BETIK: mevcut on-egitimden (v15_on10sinif/weights/best.pt) devam eder ve
fine-tune'u `dataset/karisim_arena_gercek.yaml` ile kosar. ON-EGITIM YENIDEN
EGITILMEZ.

Recete `v15_ft2sinif/args.yaml`'dan BIREBIR alindi (uydurulmadi).

UYARI: uzun kosu. `FOR_DISABLE_CONSOLE_CTRL_HANDLER=1` olmadan baslatma —
konsol kapaninca egitim izsiz oluyor.
"""
import argparse
import os
import sys
from pathlib import Path

BURASI = Path(__file__).parent
sys.path.insert(0, str(BURASI))
from ayarlar import REPO  # noqa: E402

RUNS = REPO / "codes" / "runs" / "segment"
ON_BEST = RUNS / "v15_on10sinif" / "weights" / "best.pt"
FT_YAML = REPO / "dataset" / "karisim_arena_gercek.yaml"
AD = "v22_on10_gercek"

# v15_ft2sinif/args.yaml'dan birebir — recete degistirilmedi.
RECETE = dict(
    # D-112: imgsz 640 -> 512. Olculdu (v24, INFER_SIZE gercekten degistirilerek,
    # T66 kadraj n=50): IoU yayilimi 384..768 arasinda 0,027 — projenin gurultu
    # tabani 0,04'un ALTINDA, yani cozunurluk secimi DOGRULUK acisindan ayirt
    # edilemez. 640'in olculebilir bir ustunlugu YOK ama maliyeti VAR:
    # Jetson'da 1,56 kat hesap (orada hic olcumumuz yok) ve egitimde ~1,56 kat
    # sure. Uretim ZATEN 512'de kosuyor (`rpi_inference.INFER_SIZE`); bu degisiklik
    # egitimi ona hizalar ve olculmemis bir uyusmazligi kaldirir.
    # ⚠ v27 640 ile kosuldu; v27<->v28 kiyasi bu degiskeni de tasir.
    epochs=200, patience=60, batch=12, imgsz=512,
    optimizer="AdamW", seed=0, deterministic=True, cos_lr=True,
    close_mosaic=20, overlap_mask=True, mask_ratio=4,
    lr0=0.001, lrf=0.01, weight_decay=0.0005, warmup_epochs=5,
    degrees=15.0, scale=0.5, flipud=0.5, fliplr=0.5,
    mosaic=1.0, mixup=0.0, copy_paste=0.3,
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ad", default=AD)
    # T54: veri yolu SABIT birakilirsa `--ad` degistirip yanlis karisimla
    # egitmek cok kolay — bir kez oldu, kosum durdurulup duzeltildi.
    ap.add_argument("--data", type=Path, default=FT_YAML,
                    help="fine-tune karisim yaml'i (varsayilan: karisim_arena_gercek)")
    ap.add_argument("--epoch", type=int, default=RECETE["epochs"])
    ap.add_argument("--batch", type=int, default=RECETE["batch"])
    ap.add_argument("--devam", action="store_true",
                    help="Kesinti sonrasi ayni kosuya devam et")
    # D-108: egitim GPU'ya DEGIL VERI HATTINA bagli — GPU %42 bosta bekliyor ve
    # SM saati tavanina (3090 MHz) hic dayanmiyor. Bu yuzden overclock olculebilir
    # hizlanma vermedi. Kaldirac veri tarafindadir.
    # Ikisi de Ultralytics'in `resume` sirasinda GUNCELLENMESINE IZIN VERDIGI
    # anahtarlar arasindadir (`BaseTrainer.check_resume`), yani yarim kalan bir
    # kosuya da uygulanabilir.
    ap.add_argument("--workers", type=int, default=None,
                    help="Veri yukleyici isci sayisi (varsayilan Ultralytics 8)")
    ap.add_argument("--cache", default=None,
                    help="Goruntu onbellegi: ram | disk (varsayilan yok)")
    args = ap.parse_args()

    if os.environ.get("FOR_DISABLE_CONSOLE_CTRL_HANDLER") != "1":
        print("!! FOR_DISABLE_CONSOLE_CTRL_HANDLER=1 AYARLI DEGIL — konsol "
              "kapaninca egitim izsiz olur. Yine de devam ediliyor.", flush=True)
    if not ON_BEST.is_file():
        raise SystemExit(f"on-egitim agirligi yok: {ON_BEST}")
    if not args.data.is_file():
        raise SystemExit(f"karisim yaml yok: {args.data}")

    hedef = RUNS / args.ad
    if hedef.exists() and not args.devam:
        print(f"[{args.ad}] dizin zaten var: {hedef}\n"
              f"  Devam icin --devam ver, yeniden baslatmak icin --ad degistir.",
              flush=True)

    from ultralytics import YOLO
    print(f"[{args.ad}] baslangic\n  model = {ON_BEST}\n  data  = {args.data}\n"
          f"  epoch = {args.epoch}  batch = {args.batch}", flush=True)

    kw = dict(RECETE)
    kw.update(epochs=args.epoch, batch=args.batch)
    if args.workers is not None:
        kw["workers"] = args.workers
    if args.cache is not None:
        kw["cache"] = args.cache
    # 🔴 DEVAM KUSURU (2026-08-14, 44 epoch kaybedildi): `--devam` verilse bile
    # model ON_EGITIMDEN kuruluyordu. Ultralytics `resume=True`yi ancak modelin
    # KENDISI bir kontrol noktasiysa cozer; on-egitimden kurulunca `resume`
    # sessizce False'a duser (args satirinda `resume=False` gorulur), kosu
    # BASTAN baslar ve `exist_ok=True` yuzunden `results.csv` SILINIR.
    # Devam icin model kosunun kendi `last.pt`'sinden kurulur ve resume'a
    # o dosyanin YOLU verilir.
    son = RUNS / args.ad / "weights" / "last.pt"
    if args.devam:
        if not son.is_file():
            raise SystemExit(f"--devam istendi ama kontrol noktasi yok: {son}")
        model = YOLO(str(son))
        model.train(data=str(args.data), project=str(RUNS), name=args.ad,
                    exist_ok=True, resume=str(son), **kw)
    else:
        model = YOLO(str(ON_BEST))
        model.train(data=str(args.data), project=str(RUNS), name=args.ad,
                    exist_ok=True, resume=False, **kw)
    print(f"[{args.ad}] EGITIM TAMAMLANDI -> "
          f"{RUNS / args.ad / 'weights' / 'best.pt'}", flush=True)


if __name__ == "__main__":
    main()
