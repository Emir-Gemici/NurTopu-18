"""T127 — TEMIZ BOLUM ZINCIRI: kume kur -> egit -> olc. ELLE ADIM YOK.

ON KAYIT: results/t127_on_kayit.md (D-107; egitim baslamadan yazildi).
Mimarin sarti: "Zinciri TEK betikle kur, adim adim elle baslatma — uyuyan bir
insan araya giremez."

ADIMLAR (her biri oncekinin ciktisina bagli; biri duserse zincir DURUR):
 1. KUME: `copy_paste_t122ac` goruntuleri TEMIZ bolumle yeniden dagitilir
    (`bolum_sec` D-233'te kaynak duzeyine indirildi). GORUNTU YENIDEN
    URETILMEZ — yalniz hangi varyantin hangi bolume gittigi degisir.
    KAPI: yeni manifestte "kaynagi egitimde de olan val" = 0 olmali; degilse
    zincir DURUR (fail-closed).
 2. YAML: `karisim_t127.yaml` (diger iki bilesen AYNEN).
 3. EGITIM: recete t122ac ile BIREBIR (56 RECETE + epochs 40, patience 15,
    taban v34). Ad: `t127_temiz`.
 4. OLCUM: kabul zinciri (65) · kiyas (109) · bakir kare kiyasi (115).
    Ciktilar results/t127_temiz/ altina yazilir.
"""
from __future__ import annotations

import collections
import importlib
import io
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[2]
OLCUM = KOK / "scripts" / "olcum"
sys.path.insert(0, str(OLCUM))
sys.path.insert(0, str(KOK / "scripts"))

from copy_paste_augmentation import bolum_sec  # noqa: E402

KAYNAK_KUME = KOK / "dataset" / "copy_paste_t122ac"
YENI_KUME = KOK / "dataset" / "copy_paste_t127"
ESKI_MANIFEST = KOK / "dataset" / "copy_paste_gercek" / "manifest.json"
YAML = KOK / "dataset" / "karisim_t127.yaml"
CIKTI = KOK / "results" / "t127_temiz"
AD = "t127_temiz"
RUNS = KOK / "codes" / "runs" / "segment"
PY = sys.executable


def adim1_kume() -> dict:
    man = json.load(io.open(ESKI_MANIFEST, encoding="utf-8"))
    tohum = man["parametreler"]["tohum"]
    uret = [o for o in man["ornekler"] if o.get("cikti")]

    if YENI_KUME.exists():
        shutil.rmtree(YENI_KUME)
    for bolum in ("train", "val"):
        (YENI_KUME / "images" / bolum).mkdir(parents=True)
        (YENI_KUME / "labels" / bolum).mkdir(parents=True)

    kayit, kaynak_bolum = [], collections.defaultdict(set)
    for o in uret:
        yeni_bolum = bolum_sec(Path(o["kaynak"]), 0, tohum, 0.15)
        ad = Path(o["cikti"]).name
        # Kaynak kume t122ac; goruntu ve ETIKET oradan KOPYALANIR (yeniden
        # uretim YOK). Eski bolum bilinmedigi icin iki yerde de aranir.
        for eski in ("train", "val"):
            img = KAYNAK_KUME / "images" / eski / ad
            if img.is_file():
                break
        else:
            continue                       # t122ac'de ihlalle yazilmamis dosya
        lbl = KAYNAK_KUME / "labels" / eski / ad.replace(".jpg", ".txt")
        shutil.copy2(img, YENI_KUME / "images" / yeni_bolum / ad)
        shutil.copy2(lbl, YENI_KUME / "labels" / yeni_bolum / lbl.name)
        kaynak_bolum[o["kaynak"]].add(yeni_bolum)
        kayit.append({"cikti": f"images/{yeni_bolum}/{ad}",
                      "kaynak": o["kaynak"], "bolum": yeni_bolum,
                      "durum": "YAZILDI"})

    train_kaynak = {k for k, v in kaynak_bolum.items() if "train" in v}
    val_ornek = [k for k in kayit if k["bolum"] == "val"]
    kirli = [k for k in val_ornek if k["kaynak"] in train_kaynak]
    sayim = collections.Counter(k["bolum"] for k in kayit)
    ozet = {"train": sayim["train"], "val": sayim["val"],
            "val_ornegi": len(val_ornek), "KIRLI_val": len(kirli),
            "ikiye_bolunen_kaynak": sum(1 for v in kaynak_bolum.values()
                                        if len(v) > 1),
            "tohum": tohum, "val_oran": 0.15}
    shutil.copy2(KAYNAK_KUME / "data.yaml", YENI_KUME / "data.yaml")
    io.open(YENI_KUME / "manifest.json", "w", encoding="utf-8").write(
        json.dumps({"parametreler": {**man["parametreler"],
                                     "_t127": "TEMIZ BOLUM (kaynak duzeyi)"},
                    "ozet": ozet, "ornekler": kayit},
                   ensure_ascii=False, indent=1))
    print("[1] KUME:", json.dumps(ozet, ensure_ascii=False), flush=True)
    if ozet["KIRLI_val"] != 0 or ozet["ikiye_bolunen_kaynak"] != 0:
        raise SystemExit("ZINCIR DURDU: bolum TEMIZ DEGIL (fail-closed)")
    return ozet


def adim2_yaml() -> None:
    kaynak = io.open(KOK / "dataset" / "karisim_t122ac.yaml",
                     encoding="utf-8").read()
    io.open(YAML, "w", encoding="utf-8", newline="\n").write(
        "# T127 TEMIZ BOLUM — goruntuler t122ac ile AYNI, yalniz train/val\n"
        "# dagilimi kaynak duzeyinde (D-233 duzeltmesi). Diger bilesenler AYNEN.\n"
        + kaynak.replace("copy_paste_t122ac", "copy_paste_t127"))
    print(f"[2] YAML: {YAML.name}", flush=True)


def adim3_egitim() -> Path:
    m56 = importlib.import_module("56_t53_gercek_karisim")
    kw = dict(m56.RECETE)
    kw.update(epochs=40, patience=15)
    from ultralytics import YOLO
    taban = KOK / "models" / "navitas_seg_v34_best.pt"
    print(f"[3] EGITIM baslıyor: {AD} · taban={taban.name} · data={YAML.name}",
          flush=True)
    YOLO(str(taban)).train(data=str(YAML), project=str(RUNS), name=AD,
                           exist_ok=True, resume=False, **kw)
    agirlik = RUNS / AD / "weights" / "best.pt"
    print(f"[3] EGITIM BITTI -> {agirlik}", flush=True)
    return agirlik


def kos(betik: str, ek: list[str]) -> int:
    p = subprocess.run([PY, "-B", str(OLCUM / betik)] + ek,
                       cwd=str(KOK), text=True, encoding="utf-8",
                       errors="replace")
    print(f"    {betik} exit={p.returncode}", flush=True)
    return p.returncode


def adim4_olcum(agirlik: Path) -> None:
    CIKTI.mkdir(parents=True, exist_ok=True)
    print("[4] OLCUM", flush=True)
    kos("65_kabul_denetcisi.py", ["--model", str(agirlik), "--ad", AD])
    kos("109_t122_kiyas.py", ["--atla-eksik"])
    kos("115_t127_bakir_kiyas.py", [])
    for ad_dosya in ("kiyas.json", "kiyas.md"):
        kaynak = KOK / "results" / "t122" / ad_dosya
        if kaynak.is_file():
            shutil.copy2(kaynak, CIKTI / f"t122_{ad_dosya}")
    print("[4] OLCUM BITTI", flush=True)


def main() -> int:
    if os.environ.get("FOR_DISABLE_CONSOLE_CTRL_HANDLER") != "1":
        print("!! FOR_DISABLE_CONSOLE_CTRL_HANDLER=1 DEGIL — durduruluyor",
              file=sys.stderr)
        return 2
    ozet = adim1_kume()
    adim2_yaml()
    agirlik = adim3_egitim()
    adim4_olcum(agirlik)
    CIKTI.mkdir(parents=True, exist_ok=True)
    io.open(CIKTI / "zincir_ozeti.json", "w", encoding="utf-8").write(
        json.dumps({"kume": ozet, "agirlik": str(agirlik),
                    "on_kayit": "results/t127_on_kayit.md"},
                   ensure_ascii=False, indent=1))
    print("ZINCIR TAMAMLANDI", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
