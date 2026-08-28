"""158 — T199 ARENA PROFILI EGITIMI · ON_KAYIT REVIEW_LOG D-340.

NEDEN. Sartname figurunde v36 rota URETEMIYOR (T192). Teshis D-342:
renk ve olcek suclu DEGIL; zeminin INCE YAPI YOGUNLUGU yarisi kadar.
Arena profili (D-343) kuruldu: izgara 0,30->0,52 · zemine ince kirinti
(kara-sapka 7,82 -> 13,16; hedef 16,83) · mavi IHA-IB ortusu CIZILMIYOR.

BU BETIK 152'NIN AYNISIDIR; TEK FARK karisima
`sentetik_arena_PROFIL_t199` EKLENMESIDIR. Recete, augmentasyon, tohum,
val kumesi — hicbiri degismedi. Boylece sonuc TEK degiskene baglanabilir.

⚠ ON KAYIT (D-340) BAGLAYICI:
  · BIRINCIL OLCUT: figurde ROTA URETILIYOR mu (ikili).
  · GERILEME KAPISI: 10 kapinin tamami MEVCUT esiklerle gecilmeli.
  · Figur EGITIME GIRMEZ (asagida denetlenir).
  · Uc denemede olmazsa T199 BASARISIZ kapanir, v36 korunur.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import time
from pathlib import Path

KOK = Path(__file__).resolve().parents[2]
DS = KOK / "dataset"
YAML = DS / "karisim_arena_profil_t199.yaml"
CIKTI = KOK / "results" / "gece_20260828"
KOSUM_ADI = "bariyer_v8_v36taban"
KOSUM_DIZINI = KOK / "codes" / "runs" / "segment" / KOSUM_ADI
TABAN = KOK / "models" / "navitas_seg_v36_best.pt"
T127_ARGS = KOK / "codes" / "runs" / "segment" / "t127_temiz" / "args.yaml"

# Egitim karisimi: v7a'nin TAMAMI + acili bariyer kumesi. Eskisi ATILMAZ —
# gerileme riski olmasin diye eski dagilim korunur, yenisi EKLENIR.
TRAIN_DIZINLERI = [
    DS / "rescuenet_2sinif_engelli" / "images" / "train",
    DS / "sentetik_arena" / "images" / "train",
    DS / "copy_paste_t127" / "images" / "train",
    DS / "dji_v7_x5" / "images" / "train",
    DS / "sentetik_arena_bariyer_acili" / "images" / "train",   # T185
    DS / "sentetik_arena_PROFIL_t199" / "images" / "train",     # T199, TEK YENI
]
VAL_DIZINLERI = [DS / "dji_v7" / "images" / "val"]

# Recetede BULUNMASI ZORUNLU alanlar. Biri eksikse egitim BASLAMAZ —
# v36'daki sessiz dusme bir daha olmaz.
ZORUNLU_ALANLAR = (
    "data", "epochs", "imgsz", "batch", "workers", "seed", "deterministic",
    "patience", "optimizer", "lr0", "lrf", "momentum", "weight_decay",
    "warmup_epochs", "cos_lr", "close_mosaic",
    "hsv_h", "hsv_s", "hsv_v", "degrees", "translate", "scale", "shear",
    "perspective", "flipud", "fliplr", "bgr", "mosaic", "mixup", "copy_paste",
    "erasing", "save_period", "project", "name", "exist_ok",
)


def _recete_tam_mi(recete: dict) -> None:
    eksik = [a for a in ZORUNLU_ALANLAR if a not in recete]
    if eksik:
        raise SystemExit(
            "RECETE EKSIK — egitim baslatilmadi. Eksik alanlar: "
            + ", ".join(eksik)
            + "\n(v36 tam bu sekilde degrees/flipud/copy_paste/cos_lr/optimizer "
              "alanlarini kaybetti ve kayit defteri 't127 birebir' dedi.)")


def yaml_yaz() -> dict:
    eksik = [str(d) for d in TRAIN_DIZINLERI + VAL_DIZINLERI if not d.is_dir()]
    if eksik:
        raise SystemExit("veri dizini YOK:\n  " + "\n  ".join(eksik))
    sayim = {}
    for d in TRAIN_DIZINLERI + VAL_DIZINLERI:
        sayim[str(d)] = len(list(d.glob("*.jpg"))) + len(list(d.glob("*.png")))
    # 🔴 ON_KAYIT D-340 §1: sinav kagidi egitime SIZAMAZ. Sadece belge degil,
    # KOSUMDAN ONCE denetlenen bir kapidir.
    yasak = "sartname_s9_arena"
    sizinti = []
    for d in TRAIN_DIZINLERI + VAL_DIZINLERI:
        sizinti += [str(p) for p in d.rglob("*") if yasak in p.name.lower()]
    if sizinti:
        ayrac = chr(10) + "  "
        raise SystemExit("🔴 SINAV KAGIDI EGITIM KUMESINDE (D-340 §1):"
                         + ayrac + ayrac.join(sizinti))

    bos = [k for k, v in sayim.items() if v == 0]
    if bos:
        raise SystemExit("BOS veri dizini:\n  " + "\n  ".join(bos))

    satirlar = [
        "# T199 ARENA PROFILI (ON_KAYIT REVIEW_LOG D-340).",
        "# v8 karisiminin TAMAMI + `sentetik_arena_PROFIL_t199`.",
        "# TEK DEGISKEN: arena profili (izgara + ince kirinti, mavi ortu YOK).",
        "# Eski kumelerin HICBIRI atilmadi (D-340 SS2: cesitlilik KALDIRILMAZ).",
        "# val = dji_v7 val (gercek GUNDUZ DJI kareleri) — degismedi.",
        f"path: {DS}",
        "train:",
    ]
    satirlar += [f"  - {d}" for d in TRAIN_DIZINLERI]
    satirlar.append("val:")
    satirlar += [f"  - {d}" for d in VAL_DIZINLERI]
    satirlar += ["", "nc: 2", "names:", "  0: traversable", "  1: blocked", ""]
    YAML.write_text("\n".join(satirlar), encoding="utf-8")

    ozet = {"yaml": str(YAML), "sayim": sayim,
            "train_toplam": sum(sayim[str(d)] for d in TRAIN_DIZINLERI),
            "val_toplam": sum(sayim[str(d)] for d in VAL_DIZINLERI)}
    CIKTI.mkdir(parents=True, exist_ok=True)
    (CIKTI / "karisim_v8.json").write_text(
        json.dumps(ozet, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(ozet, indent=1, ensure_ascii=False))
    return ozet


def _yedek_callback_ekle(model, yedek_dizin: Path):
    """Her epoch sonunda `last.pt`yi DONUSUMLU iki yedege ATOMIK kopyala.

    Ultralytics `last.pt`yi `write_bytes` ile yazar — atomik DEGILDIR. BSOD
    tam o sirada gelirse dosya yarim kalir. Iki yedek donusumlu yazildigi
    icin biri bozulsa digeri saglam olur; kopyalama `os.replace` ile atomik.
    """
    yedek_dizin.mkdir(parents=True, exist_ok=True)

    def _kopyala(egitici):
        try:
            son = Path(egitici.last)
            if not son.is_file():
                return
            ep = int(getattr(egitici, "epoch", 0))
            hedef = yedek_dizin / f"last_{ep % 2}.pt"
            gecici = yedek_dizin / f".gecici_{ep % 2}.pt"
            shutil.copy2(son, gecici)
            os.replace(gecici, hedef)          # ATOMIK
            (yedek_dizin / "durum.json").write_text(
                json.dumps({"epoch": ep, "yedek": hedef.name,
                            "zaman": time.strftime("%Y-%m-%d %H:%M:%S")}),
                encoding="utf-8")
        except Exception as exc:               # yedekleme egitimi ASLA durdurmaz
            print(f"[YEDEK UYARI] {type(exc).__name__}: {exc}", flush=True)

    model.add_callback("on_fit_epoch_end", _kopyala)


def egit(saat: float, devam: bool, epochs: int, patience: int) -> None:
    import yaml as _y
    from ultralytics import YOLO

    if not YAML.is_file():
        raise SystemExit(f"once `yaml` komutunu kos: {YAML} yok")
    ref = _y.safe_load(open(T127_ARGS, encoding="utf-8"))

    son = KOSUM_DIZINI / "weights" / "last.pt"
    if devam:
        if not son.is_file():
            raise SystemExit(f"devam edilecek checkpoint yok: {son}")
        model = YOLO(str(son))
        recete = {"resume": True}
        print(f"DEVAM: {son}", flush=True)
    else:
        if not TABAN.is_file():
            raise SystemExit(f"taban model yok: {TABAN}")
        model = YOLO(str(TABAN))
        recete = dict(
            data=str(YAML),
            epochs=epochs,
            time=float(saat),              # SAAT tavani — 15 saatlik butce
            imgsz=ref["imgsz"], batch=ref["batch"], workers=ref["workers"],
            seed=ref["seed"], deterministic=ref["deterministic"],
            patience=patience,
            # 🔴 optimizer ACIKCA verilir: 'auto' kalirsa ultralytics lr0'i
            # SESSIZCE ezer (v36'da 0,001 -> 0,001667 oldu, logda yazili).
            optimizer=ref["optimizer"],
            lr0=ref["lr0"], lrf=ref["lrf"], momentum=ref["momentum"],
            weight_decay=ref["weight_decay"],
            warmup_epochs=ref["warmup_epochs"],
            cos_lr=ref["cos_lr"], close_mosaic=ref["close_mosaic"],
            hsv_h=ref["hsv_h"], hsv_s=ref["hsv_s"], hsv_v=ref["hsv_v"],
            # 🔴 ASIL DEGISIKLIK: t127 degrees=15 diyordu, v36 0 aldi.
            # Nadir goruntude yonelim KEYFIDIR -> tam donme.
            degrees=180.0,
            translate=ref["translate"], scale=ref["scale"], shear=ref["shear"],
            perspective=ref["perspective"],
            flipud=ref["flipud"], fliplr=ref["fliplr"], bgr=ref["bgr"],
            mosaic=ref["mosaic"], mixup=ref["mixup"],
            copy_paste=ref["copy_paste"], erasing=ref["erasing"],
            # cokme dayanikliligi
            save_period=5,
            project=str(KOK / "codes" / "runs" / "segment"),
            name=KOSUM_ADI, exist_ok=True,
        )
        _recete_tam_mi(recete)
        CIKTI.mkdir(parents=True, exist_ok=True)
        (CIKTI / f"{KOSUM_ADI}_recete.json").write_text(
            json.dumps({"taban": str(TABAN),
                        "degrees_gerekce": "v36 degrees=0 ile egitildi; model "
                                           "bariyeri 60/120/135 derecede %0,0 "
                                           "goruyordu (D-324)",
                        **recete}, indent=1, ensure_ascii=False),
            encoding="utf-8")
        print("RECETE " + json.dumps(recete, ensure_ascii=False), flush=True)

    _yedek_callback_ekle(model, KOSUM_DIZINI / "yedek")

    t0 = time.time()
    model.train(**recete)
    sn = time.time() - t0
    best = KOSUM_DIZINI / "weights" / "best.pt"
    (CIKTI / f"{KOSUM_ADI}_bitti.json").write_text(
        json.dumps({"saniye": round(sn), "saat": round(sn / 3600.0, 2),
                    "best": str(best), "var": best.is_file()},
                   indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"EGITIM BITTI {sn/3600.0:.2f} saat -> {best} var={best.is_file()}",
          flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("komut", choices=["yaml", "egit"])
    ap.add_argument("--saat", type=float, default=14.0,
                    help="egitim SAAT tavani (ultralytics `time`)")
    ap.add_argument("--epochs", type=int, default=600,
                    help="ust sinir; `--saat` genelde once dolar")
    ap.add_argument("--patience", type=int, default=120,
                    help="v36 patience=15 ile 17. epoch'ta durdu — 15 saatlik "
                         "butce o ayarla ANLAMSIZ olurdu")
    ap.add_argument("--devam", action="store_true",
                    help="cokme sonrasi last.pt'den devam et")
    a = ap.parse_args()
    if a.komut == "yaml":
        yaml_yaz()
    else:
        egit(a.saat, a.devam, a.epochs, a.patience)


if __name__ == "__main__":
    main()
