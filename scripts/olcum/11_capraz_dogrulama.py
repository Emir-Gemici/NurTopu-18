"""ÇAPRAZ DOĞRULAMA — herhangi bir modeli val VE bakir test split'inde ölç.

Neden: v1'den v5'e kadar 8 model/reçete kıyaslamasının TAMAMI aynı 294 görüntülük
val kümesinde yapıldı. data.yaml'da tanımlı 305 görüntülük test split'i (308
traversable + 85 blocked instance) bugüne dek hiçbir betikte kullanılmadı. Aynı
kümede tekrar tekrar model seçmek dolaylı aşırı uyum riski taşır: v4'ün v5'ten
gerçekten iyi olduğundan emin değiliz.

Bu betik Sıra 2'deki her deneyin standart raporlama aracıdır — her sonuç HEM
val294 HEM test305 üzerinde verilir ve deney defterine yazılır.

Kullanım:
  venv\\Scripts\\python.exe 11_capraz_dogrulama.py                      # v4, her iki split
  venv\\Scripts\\python.exe 11_capraz_dogrulama.py --split test         # yalnız test
  venv\\Scripts\\python.exe 11_capraz_dogrulama.py --model models/navitas_seg_v3_best.pt
  venv\\Scripts\\python.exe 11_capraz_dogrulama.py --ad v6_clspw05 --not "cls_pw=0.5 pilotu"

NOT: Windows DataLoader kuralı — tüm mantık main() içinde, __main__ korumalı.
"""
import argparse
import datetime
import hashlib
import json
import logging
from pathlib import Path

from ayarlar import DATA_YAML, REPO
import defter

VARSAYILAN_MODEL = REPO / "models" / "navitas_seg_v4_best.pt"
HEDEF = 0.60


def kur_log(dosya: Path):
    def logla(*p):
        s = " ".join(str(x) for x in p)
        print(s)
        with open(dosya, "a", encoding="utf-8") as f:
            f.write(s + "\n")
    fh = logging.FileHandler(str(dosya), encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(message)s"))
    logging.getLogger("ultralytics").addHandler(fh)
    return logla


def sha256(yol: Path) -> str:
    return hashlib.sha256(yol.read_bytes()).hexdigest()


def olc(model, split: str, imgsz: int, cikti: Path, logla):
    """Tek split ölçümü → metrik sözlüğü."""
    logla(f"\n{'=' * 64}\nSPLIT: {split}  |  imgsz: {imgsz}\n{'=' * 64}")
    sonuc = model.val(data=str(DATA_YAML), imgsz=imgsz, split=split,
                      plots=True, project=str(cikti), name=f"{split}{imgsz}",
                      exist_ok=True, verbose=True)
    m = {
        "split": split,
        "imgsz": imgsz,
        "box_mAP50": round(sonuc.box.map50, 4),
        "box_mAP50_95": round(sonuc.box.map, 4),
        "mask_mAP50": round(sonuc.seg.map50, 4),
        "mask_mAP50_95": round(sonuc.seg.map, 4),
        "mask_precision": round(sonuc.seg.mp, 4),
        "mask_recall": round(sonuc.seg.mr, 4),
        "sinif_bazli": {},
        "hiz_ms": {k: round(float(v), 3) for k, v in sonuc.speed.items()},
    }
    for sira, idx in enumerate(sonuc.ap_class_index):
        ad = sonuc.names[int(idx)]
        m["sinif_bazli"][ad] = {
            "box_mAP50": round(float(sonuc.box.ap50[sira]), 4),
            "mask_mAP50": round(float(sonuc.seg.ap50[sira]), 4),
            "mask_mAP50_95": round(float(sonuc.seg.ap[sira]), 4),
        }
    return m


def main():
    ap = argparse.ArgumentParser(description="val + bakir test split çapraz doğrulama")
    ap.add_argument("--model", default=str(VARSAYILAN_MODEL), help="ölçülecek .pt")
    ap.add_argument("--split", default="ikisi", choices=["val", "test", "ikisi"])
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--ad", default=None, help="deney defterindeki ad (vars: dosya adı)")
    ap.add_argument("--not", dest="notlar", default="", help="deftere düşülecek not")
    args = ap.parse_args()

    from ultralytics import YOLO

    model_pt = Path(args.model)
    if not model_pt.is_absolute():
        model_pt = REPO / model_pt
    if not model_pt.exists():
        raise SystemExit(f"HATA: ağırlık yok: {model_pt}")

    ad = args.ad or model_pt.stem
    tarih = datetime.datetime.now()
    cikti = REPO / "results" / f"capraz_dogrulama_{ad}_{tarih:%Y%m%d}"
    cikti.mkdir(parents=True, exist_ok=True)
    logla = kur_log(cikti / "konsol.log")

    canli = sha256(model_pt)
    logla("=" * 64)
    logla(f"ÇAPRAZ DOĞRULAMA — {tarih.isoformat(timespec='seconds')}")
    logla(f"model : {model_pt}")
    logla(f"SHA256: {canli}")
    logla(f"veri  : {DATA_YAML}")
    logla("=" * 64)

    yolo = YOLO(str(model_pt))
    splitler = ["val", "test"] if args.split == "ikisi" else [args.split]
    olcumler = {s: olc(yolo, s, args.imgsz, cikti, logla) for s in splitler}

    rapor = {
        "olcum": {"tarih": tarih.isoformat(timespec="seconds"), "ad": ad,
                  "imgsz": args.imgsz, "veri": str(DATA_YAML)},
        "agirlik": {"yol": str(model_pt), "sha256": canli,
                    "boyut_mb": round(model_pt.stat().st_size / 1e6, 1)},
        "splitler": olcumler,
    }

    # ── Split'ler arası tutarlılık: val'e aşırı uyum var mı? ──
    if len(olcumler) == 2:
        v, t = olcumler["val"], olcumler["test"]
        fark = round(v["mask_mAP50"] - t["mask_mAP50"], 4)
        bf = round(v["sinif_bazli"]["blocked"]["mask_mAP50"]
                   - t["sinif_bazli"]["blocked"]["mask_mAP50"], 4)
        rapor["val_test_farki"] = {"mask_mAP50": fark, "blocked_mask_mAP50": bf}
        logla("\n" + "=" * 64)
        logla("VAL ↔ TEST KARŞILAŞTIRMASI")
        logla(f"  mask mAP50 : val {v['mask_mAP50']}  ·  test {t['mask_mAP50']}"
              f"  ·  fark {fark:+.4f}")
        logla(f"  blocked    : val {v['sinif_bazli']['blocked']['mask_mAP50']}"
              f"  ·  test {t['sinif_bazli']['blocked']['mask_mAP50']}  ·  fark {bf:+.4f}")
        logla("  NOT: Tek modelin split farkı, model SIRALAMASININ korunduğunu göstermez —"
              "\n       aşırı uyum ancak birkaç model aynı iki split'te kıyaslanınca görünür."
              "\n       Sıralama kontrolü için: python 12_model_kiyas.py")

    json.dump(rapor, open(cikti / "capraz_dogrulama.json", "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)

    # ── Deney defterine yaz ──
    for s, m in olcumler.items():
        defter.ekle({
            "ad": ad, "model": model_pt.name, "model_sha8": canli[:8],
            "imgsz": args.imgsz, "split": s,
            "goruntu": {"val": 294, "test": 305}.get(s, ""),
            "mask_mAP50": m["mask_mAP50"], "mask_mAP50_95": m["mask_mAP50_95"],
            "box_mAP50": m["box_mAP50"],
            "precision": m["mask_precision"], "recall": m["mask_recall"],
            "traversable_AP50": m["sinif_bazli"].get("traversable", {}).get("mask_mAP50"),
            "blocked_AP50": m["sinif_bazli"].get("blocked", {}).get("mask_mAP50"),
            "git": defter.git_hash(REPO), "notlar": args.notlar,
        })

    logla("\n" + "=" * 64)
    logla("SONUÇLAR")
    logla(json.dumps(rapor, indent=2, ensure_ascii=False))
    for s, m in olcumler.items():
        logla(f"\n[{s}] hedef mask mAP50 ≥ {HEDEF:.2f}  ·  ölçülen {m['mask_mAP50']}  →  "
              + ("KARŞILANDI ✓" if m["mask_mAP50"] >= HEDEF else "KARŞILANMADI ✗"))
    logla(f"\nDeney defteri: {defter.DEFTER}")
    logla(f"Kanıt klasörü: {cikti}")
    logla("✓ ÇAPRAZ DOĞRULAMA TAMAM")


if __name__ == "__main__":
    main()
