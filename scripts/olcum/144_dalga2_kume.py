"""144 — ETIKET DALGA 2 -> YOLO kumesi (dataset/dji_kirsal_dalga2) + x20 cogaltma.

Bolum kurali (D-233, ON_KAYIT §2): 0038 kaynagi TEST kaynagidir -> dalga 2'deki 0038 kareleri
TRAIN'e GIRMEZ, val'e gider (erken durdurma). 0037/0039 -> train (x20 sabit baglanti).
Maske -> YOLO donusumu 135 zincirinin maske_to_yolo'su (ayni fonksiyon, ice aktarilir).
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
from pathlib import Path

import cv2

KOK = Path(__file__).resolve().parents[2]
KAYNAK = KOK / "results" / "gece_20260826" / "etiket_dalga2"
KARE_KOK = KOK / "results" / "dji_20260822" / "kareler_1fps"
KUME = KOK / "dataset" / "dji_kirsal_dalga2"
X20 = KOK / "dataset" / "dji_kirsal_dalga2_x20"
KAT = 20
TEST_KAYNAK = "dji_20260822172613_0038_d"


def _modul(ad):
    spec = importlib.util.spec_from_file_location(ad, KOK / "scripts" / "olcum" / f"{ad}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _bag(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        return
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def main():
    z = _modul("135_dji_kirsal_zincir")
    if KUME.exists():
        shutil.rmtree(KUME)
    if X20.exists():
        shutil.rmtree(X20)
    say = {"train": 0, "val": 0, "bos": []}
    for p in sorted(KAYNAK.glob("*/*_uc.png")):
        govde = p.name[:-len("_uc.png")]
        kaynak, stem = govde.split("__", 1)
        kare = KARE_KOK / kaynak / (stem + ".jpg")
        assert kare.is_file(), kare
        m = cv2.imread(str(p), cv2.IMREAD_GRAYSCALE)
        assert m is not None and set(map(int, set(m.ravel()))) <= {0, 1, 2}, p
        bp = "val" if kaynak == TEST_KAYNAK else "train"
        satir = z.maske_to_yolo(m)
        if not satir:
            say["bos"].append(govde)
        (KUME / "images" / bp).mkdir(parents=True, exist_ok=True)
        (KUME / "labels" / bp).mkdir(parents=True, exist_ok=True)
        shutil.copy2(kare, KUME / "images" / bp / (govde + ".jpg"))
        (KUME / "labels" / bp / (govde + ".txt")).write_text("\n".join(satir) + ("\n" if satir else ""), encoding="utf-8")
        say[bp] += 1
        if bp == "train":
            for k in range(KAT):
                _bag(KUME / "images" / bp / (govde + ".jpg"), X20 / "images" / "train" / f"{govde}__x{k:02d}.jpg")
                _bag(KUME / "labels" / bp / (govde + ".txt"), X20 / "labels" / "train" / f"{govde}__x{k:02d}.txt")
    # test29 ile kesisim SIFIR olmali
    test = {p.name for p in (KOK / "dataset" / "dji_kirsal_0038_bolum" / "images" / "test").glob("*.jpg")}
    kesisim = test & {p.name for p in (KUME / "images" / "val").glob("*.jpg")}
    assert not kesisim, kesisim
    say["x20_train"] = len(list((X20 / "images" / "train").glob("*.jpg")))
    say["test29_kesisim"] = 0
    print(json.dumps(say, ensure_ascii=False))
    (KOK / "results" / "gece_20260826" / "dalga2_kume.json").write_text(json.dumps(say, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
