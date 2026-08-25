"""139 — GECE EGITIM KOSUMU (on kayit: results/gece_20260826/ON_KAYIT.md).

135 zincirinin IKI kusuru burada duzeltilir:
  1. recete `lr0` ve `warmup_epochs` GECIRILMIYORDU (kosum lr0 0,01 oldu, t127 0,001).
     Burada t127 args.yaml'dan ACIKCA okunup gecirilir.
  2. dji payi %0,8 idi ve val'de dji yoktu -> erken durdurma kirsali gormedi.
     Burada dji_kirsal train x20 cogaltilir (sabit baglanti), 0038 val/test'e bolunur.

Kullanim:
  python 139_gece_egitim.py hazirla            # kume + yaml + taban sayilari (egitim YOK)
  python 139_gece_egitim.py egit --taban v35   # kosum adi gece_v2_v35taban
  python 139_gece_egitim.py egit --taban v34
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

KOK = Path(__file__).resolve().parents[2]
DS = KOK / "dataset"
KAYNAK = DS / "dji_kirsal"
X20 = DS / "dji_kirsal_x20"
BOLUM = DS / "dji_kirsal_0038_bolum"          # val (cift) / test (tek)
YAML = DS / "karisim_gece_v2.yaml"
CIKTI = KOK / "results" / "gece_20260826"
KAT = 20
TABANLAR = {"v35": KOK / "models" / "navitas_seg_v35_best.pt",
            "v34": KOK / "models" / "navitas_seg_v34_best.pt"}


def _baglanti(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        return
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def hazirla():
    # 1) x20 cogaltma (train)
    imgs = sorted((KAYNAK / "images" / "train").glob("*.jpg"))
    assert imgs, "dji_kirsal train bos"
    for p in imgs:
        lbl = KAYNAK / "labels" / "train" / (p.stem + ".txt")
        assert lbl.exists(), f"etiket yok: {lbl}"
        for k in range(KAT):
            _baglanti(p, X20 / "images" / "train" / f"{p.stem}__x{k:02d}.jpg")
            _baglanti(lbl, X20 / "labels" / "train" / f"{p.stem}__x{k:02d}.txt")
    n_x20 = len(list((X20 / "images" / "train").glob("*.jpg")))
    # 2) 0038 bolumu: SIRALI ad listesinde cift konum -> val, tek -> test
    vals = sorted((KAYNAK / "images" / "val").glob("*.jpg"))
    assert len(vals) == 59, len(vals)
    bolum = {"val": [], "test": []}
    for i, p in enumerate(vals):
        hedef = "val" if i % 2 == 0 else "test"
        bolum[hedef].append(p.name)
        lbl = KAYNAK / "labels" / "val" / (p.stem + ".txt")
        _baglanti(p, BOLUM / "images" / hedef / p.name)
        _baglanti(lbl, BOLUM / "labels" / hedef / lbl.name)
    # 3) yaml
    yaml_metin = f"""# GECE v2 (on kayit: results/gece_20260826/ON_KAYIT.md)
# Mevcut karisim AYNEN + dji_kirsal_x20 (train x{KAT}) + 0038 CIFT konum val.
# 0038 TEK konum = TEST, hicbir egitim/durdurma kararinda YOK.
path: {DS}
train:
  - {DS / 'rescuenet_2sinif_engelli' / 'images' / 'train'}
  - {DS / 'sentetik_arena' / 'images' / 'train'}
  - {DS / 'copy_paste_t127' / 'images' / 'train'}
  - {X20 / 'images' / 'train'}
val:
  - {DS / 'rescuenet_2sinif_engelli' / 'images' / 'val'}
  - {DS / 'sentetik_arena' / 'images' / 'val'}
  - {DS / 'copy_paste_t127' / 'images' / 'val'}
  - {BOLUM / 'images' / 'val'}

nc: 2
names:
  0: traversable
  1: blocked
"""
    YAML.write_text(yaml_metin, encoding="utf-8")
    # 4) taban sayilari: ayni 29 test karesinde v35 ve v1 (mevcut olcumden)
    def sebepler(dosya, secici):
        d = json.load(open(KOK / dosya, encoding="utf-8"))
        cikti = {}
        for m, v in d["modeller"].items():
            if secici(m):
                say = {}
                for k in v["kareler"]:
                    if k["kare"] in bolum["test"]:
                        s = k["olceksiz_sebep"] or "ROTA"
                        say[s] = say.get(s, 0) + 1
                cikti[os.path.basename(m) if "runs" not in m else m.split(os.sep)[-3]] = say
        return cikti
    taban = {}
    taban.update(sebepler("results/dji_kirsal/bakir_0038_taban.json", lambda m: True))
    taban.update(sebepler("results/dji_kirsal/bakir_0038.json", lambda m: True))
    CIKTI.mkdir(parents=True, exist_ok=True)
    ozet = {"x20_train": n_x20, "val_0038": len(bolum["val"]), "test_0038": len(bolum["test"]),
            "bolum": bolum, "yaml": str(YAML), "taban_test29_olceksiz_sebep": taban}
    (CIKTI / "hazirlik.json").write_text(json.dumps(ozet, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in ozet.items() if k != "bolum"}, indent=1, ensure_ascii=False))


def egit(taban: str):
    import yaml as _y
    ref = _y.safe_load(open(KOK / "codes" / "runs" / "segment" / "t127_temiz" / "args.yaml", encoding="utf-8"))
    from ultralytics import YOLO
    ad = f"gece_v2_{taban}taban"
    model = YOLO(str(TABANLAR[taban]))
    recete = dict(data=str(YAML), epochs=ref["epochs"], imgsz=ref["imgsz"], batch=ref["batch"],
                  seed=ref["seed"], deterministic=ref["deterministic"], patience=ref["patience"],
                  lr0=ref["lr0"], warmup_epochs=ref["warmup_epochs"], workers=ref.get("workers", 8),
                  project=str(KOK / "codes" / "runs" / "segment"), name=ad, exist_ok=True)
    CIKTI.mkdir(parents=True, exist_ok=True)
    (CIKTI / f"{ad}_recete.json").write_text(json.dumps({"taban": str(TABANLAR[taban]), **recete}, indent=1), encoding="utf-8")
    print("RECETE", json.dumps(recete), flush=True)
    t0 = time.time()
    model.train(**recete)
    sn = time.time() - t0
    best = KOK / "codes" / "runs" / "segment" / ad / "weights" / "best.pt"
    (CIKTI / f"{ad}_bitti.json").write_text(json.dumps({"saniye": round(sn), "best": str(best), "var": best.exists()}), encoding="utf-8")
    print(f"EGITIM BITTI {sn:.0f} sn -> {best} var={best.exists()}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("komut", choices=["hazirla", "egit"])
    ap.add_argument("--taban", choices=list(TABANLAR), default="v35")
    a = ap.parse_args()
    if a.komut == "hazirla":
        hazirla()
    else:
        assert YAML.exists(), "once hazirla"
        egit(a.taban)


if __name__ == "__main__":
    main()
