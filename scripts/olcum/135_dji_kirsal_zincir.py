"""DJI KIRSAL EGITIM ZINCIRI — tek betik, elle adim YOK.

On kayit: `results/dji_20260822/egitim_on_kayit.md` (egitim BASLAMADAN yazildi)
Yetki   : kullanici, "isin bitince otomatik karar ver ve onay beklemeden ...
          model egitmeye basla". SINIRLAR KORUNUR: PUSH YOK · TERFI YOK ·
          registry'ye DOKUNULMAZ · esik/CONTRACTS DEGISMEZ.

ADIMLAR
  1+2 kume+bolum : 160 uc durumlu maske -> YOLO segment etiketi
        🔴 ETIKETSIZ (0) HICBIR poligon uretmez (tests/test_uc_durumlu_maske)
        BOLUM KAYNAK duzeyinde. GPS olcumu (SU_ETIKETLEME_PLANI §1d):
          0037 ∩ 0039 = 0037'nin %100'u -> AYNI ALAN
          0037 ∩ 0038 = 0 m²            -> HIC ORTUSMUYOR
        => EGITIM 0037+0039 · BAKIR OLCUM 0038
        FAIL-CLOSED: "kaynagi egitimde de olan val" = 0 olmali.
  3 yaml  : mevcut karisima EK bilesen (arena+RescueNet+copy_paste DEGISMEZ)
  4 egit  : t127_temiz recetesi AYNEN (D-276: farkli recete degil)
  5 olcum : kabul zinciri + bakir 0038

⚠ Bakir 0038 bir ALAN ayrimidir, OTURUM ayrimi DEGILDIR (ayni gun/kamera/
  operator). Ayri dogrulama ucusunun yerini TUTMAZ (D-256 §5).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import cv2
import numpy as np

KOK = Path(__file__).resolve().parents[2]
PY = r"O:\navitas-local-train\venv\Scripts\python.exe"
KARE_KOK = KOK / "results" / "dji_20260822" / "kareler_1fps"
MASKE_KOK = KOK / "results" / "dji_20260822" / "f5_olcek"
KUME = KOK / "dataset" / "dji_kirsal"
YAML = KOK / "dataset" / "karisim_dji_kirsal.yaml"
CIKTI = KOK / "results" / "dji_kirsal"
AD = "dji_kirsal_v1"
BAKIR_KAYNAK = "0038"

ETIKETSIZ, SINIF0, SINIF1 = 0, 1, 2


def maske_to_yolo(m, min_alan: int = 40):
    """UC DURUMLU maske -> YOLO satirlari. ETIKETSIZ icin HICBIR satir."""
    h, w = m.shape
    satir = []
    for deger, sid in ((SINIF0, 0), (SINIF1, 1)):
        ikili = (m == deger).astype(np.uint8)
        if not ikili.any():
            continue
        kont, _ = cv2.findContours(ikili, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for k in kont:
            if cv2.contourArea(k) < min_alan:
                continue
            yak = cv2.approxPolyDP(k, 0.002 * cv2.arcLength(k, True), True)
            if len(yak) < 3:
                continue
            nk = " ".join("%.6f %.6f" % (x / w, y / h) for x, y in yak.reshape(-1, 2))
            satir.append("%d %s" % (sid, nk))
    return satir


def adim1_2_kume():
    print("[1+2] KUME + BOLUM (kaynak duzeyinde)", flush=True)
    if KUME.exists():
        shutil.rmtree(KUME)
    for bl in ("images", "labels"):
        for bp in ("train", "val"):
            (KUME / bl / bp).mkdir(parents=True, exist_ok=True)

    maskeler = sorted(p for g in "ABCD" for p in (MASKE_KOK / g).glob("*_uc.png"))
    sayim = {"train": 0, "val": 0}
    bos_etiket = []
    kaynaklar = {"train": set(), "val": set()}
    for p in maskeler:
        govde = p.name[:-len("_uc.png")]
        kaynak_dizin, stem = govde.split("__", 1)
        kare = KARE_KOK / kaynak_dizin / (stem + ".jpg")
        if not kare.is_file():
            raise SystemExit("[DUR] kare DISKTE YOK: %s" % kare)
        m = cv2.imread(str(p), cv2.IMREAD_GRAYSCALE)
        if m is None or not set(np.unique(m).tolist()) <= {0, 1, 2}:
            raise SystemExit("[DUR] maske GECERSIZ: %s" % p)
        bp = "val" if BAKIR_KAYNAK in kaynak_dizin else "train"
        satir = maske_to_yolo(m)
        if not satir:
            bos_etiket.append(govde)
        shutil.copy2(kare, KUME / "images" / bp / (govde + ".jpg"))
        (KUME / "labels" / bp / (govde + ".txt")).write_text(
            "\n".join(satir) + ("\n" if satir else ""), encoding="utf-8")
        sayim[bp] += 1
        kaynaklar[bp].add(kaynak_dizin)

    ortak = kaynaklar["train"] & kaynaklar["val"]
    print("  train %d · val(BAKIR) %d" % (sayim["train"], sayim["val"]))
    print("  train kaynaklari: %s" % sorted(kaynaklar["train"]))
    print("  val   kaynaklari: %s" % sorted(kaynaklar["val"]))
    print("  kaynagi egitimde de olan val kaynagi: %d" % len(ortak))
    if ortak:
        raise SystemExit("\n[DUR] ZINCIR DURDU — BOLUM KIRLI: %s" % ortak)
    if bos_etiket:
        print("  [!] BOS etiket (%d): tamami etiketsiz kare — anotasyon "
              "uretmedi, YOLO bunlari arka plan sayar" % len(bos_etiket))
    return {"train": sayim["train"], "val": sayim["val"],
            "bos_etiket": len(bos_etiket),
            "train_kaynak": sorted(kaynaklar["train"]),
            "val_kaynak": sorted(kaynaklar["val"])}


def adim3_yaml():
    print("[3] YAML", flush=True)
    ds = KOK / "dataset"
    metin = (
        "# DJI KIRSAL — mevcut karisima EK bilesen.\n"
        "# arena + RescueNet + copy_paste_t127 AYNEN korunur; degisen tek sey\n"
        "# `dji_kirsal` eklenmesidir. Boylece 'kirsal veri arenayi bozdu mu'\n"
        "# sorusu TEK degiskenle olculur.\n"
        "# BOLUM: kaynak duzeyinde, GPS ile ayrik (0037+0039 egitim · 0038 BAKIR).\n"
        "# val'e dji_kirsal KONMADI: bakir 0038 AYRI olculur, egitimin erken\n"
        "# durdurmasi kirsal veriye gore yapilmasin diye.\n"
        "path: %s\n"
        "train:\n  - %s\n  - %s\n  - %s\n  - %s\n"
        "val:\n  - %s\n  - %s\n  - %s\n"
        "\nnc: 2\nnames:\n  0: traversable\n  1: blocked\n" % (
            ds,
            ds / "rescuenet_2sinif_engelli" / "images" / "train",
            ds / "sentetik_arena" / "images" / "train",
            ds / "copy_paste_t127" / "images" / "train",
            ds / "dji_kirsal" / "images" / "train",
            ds / "rescuenet_2sinif_engelli" / "images" / "val",
            ds / "sentetik_arena" / "images" / "val",
            ds / "copy_paste_t127" / "images" / "val"))
    YAML.write_text(metin, encoding="utf-8")
    print("  yazildi: %s" % YAML)


def adim4_egit():
    print("[4] EGITIM (t127_temiz recetesi AYNEN)", flush=True)
    import yaml as _y
    ref = _y.safe_load(open(KOK / "codes" / "runs" / "segment" / "t127_temiz" /
                            "args.yaml", encoding="utf-8"))
    from ultralytics import YOLO
    model = YOLO(ref["model"])
    t0 = time.time()
    model.train(data=str(YAML), epochs=ref["epochs"], imgsz=ref["imgsz"],
                batch=ref["batch"], seed=ref["seed"],
                deterministic=ref["deterministic"], patience=ref["patience"],
                project=str(KOK / "codes" / "runs" / "segment"), name=AD,
                exist_ok=True, workers=ref.get("workers", 8))
    print("  egitim %.0f sn" % (time.time() - t0))
    return KOK / "codes" / "runs" / "segment" / AD / "weights" / "best.pt"


def kos(betik, arg):
    r = subprocess.run([PY, str(KOK / "scripts" / "olcum" / betik)] + arg,
                       cwd=str(KOK), text=True, encoding="utf-8", errors="replace")
    return r.returncode


def adim5_olcum(agirlik):
    print("[5] OLCUM", flush=True)
    CIKTI.mkdir(parents=True, exist_ok=True)
    kos("65_kabul_denetcisi.py", ["--model", str(agirlik), "--ad", AD])
    kos("126_t138_gece_kumesi.py",
        ["--kareler", str(KUME / "images" / "val"),
         "--modeller", str(agirlik),
         "--cikti", str(CIKTI), "--dosya", "bakir_0038.json",
         "--etiket", "DJI kirsal BAKIR 0038 (alan-ayrimli, oturum-ayrimli DEGIL)"])


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if os.environ.get("FOR_DISABLE_CONSOLE_CTRL_HANDLER") != "1":
        print("!! FOR_DISABLE_CONSOLE_CTRL_HANDLER=1 DEGIL — durduruluyor",
              file=sys.stderr)
        return 2
    son = sys.argv[1] if len(sys.argv) > 1 else "5"
    ozet = adim1_2_kume()
    if son == "2":
        print(json.dumps(ozet, ensure_ascii=False, indent=1))
        return 0
    adim3_yaml()
    if son == "3":
        return 0
    agirlik = adim4_egit()
    ozet["agirlik"] = str(agirlik)
    adim5_olcum(agirlik)
    CIKTI.mkdir(parents=True, exist_ok=True)
    (CIKTI / "zincir_ozeti.json").write_text(
        json.dumps(dict(ozet, _on_kayit="results/dji_20260822/egitim_on_kayit.md"),
                   ensure_ascii=False, indent=1), encoding="utf-8")
    print("ZINCIR TAMAMLANDI", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
