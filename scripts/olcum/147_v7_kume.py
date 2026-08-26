"""147 — v7 KUMESI (ON_KAYIT §14, CONTRACTS §12): 0037/0039'un TUM etiketli kareleri -> train/val,
0038 HIC girmez (DOGRULAMA).

Kaynaklar (uc durumlu maske ya da YOLO):
  dataset/dji_kirsal/labels/train (F5 donemi, 101 kare YOLO)  [0037/0039]
  results/gece_20260826/etiket_dalga{2,3,4}/*/<govde>_uc.png   [yalniz 0037/0039]
Bolum: rastgele %15 val (tohum 0) — yalniz erken durdurma icin.
Cikti: dataset/dji_v7/{images,labels}/{train,val}, dataset/dji_v7_x5 (train x5 sabit baglanti),
       dataset/karisim_gece_v7a.yaml (tam karisim + dji_v7_x5), karisim_gece_v7b.yaml (rescuenet YOK)
"""
from __future__ import annotations
import importlib.util, json, os, random, shutil
from pathlib import Path
import cv2, numpy as np

KOK = Path(__file__).resolve().parents[2]
DS = KOK / "dataset"
R = KOK / "results" / "gece_20260826"
KARE_KOK = KOK / "results" / "dji_20260822" / "kareler_1fps"
KUME = DS / "dji_v7"; X5 = DS / "dji_v7_x5"; KAT = 5
DOGRULAMA = "dji_20260822172613_0038_d"


def _modul(ad):
    spec = importlib.util.spec_from_file_location(ad, KOK / "scripts" / "olcum" / f"{ad}.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def _bag(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists(): return
    try: os.link(src, dst)
    except OSError: shutil.copy2(src, dst)


def main():
    z = _modul("135_dji_kirsal_zincir")
    kareler = {}  # govde -> (kare_yolu, yolo_satirlari, kaynak_etiketi)
    # 1) F5 donemi YOLO etiketleri (dji_kirsal train)
    for lbl in sorted((DS / "dji_kirsal" / "labels" / "train").glob("*.txt")):
        govde = lbl.stem
        if DOGRULAMA in govde: continue
        img = DS / "dji_kirsal" / "images" / "train" / (govde + ".jpg")
        assert img.is_file(), img
        kareler[govde] = (img, lbl.read_text(encoding="utf-8").splitlines(), "f5")
    # 2) dalga 2/3/4 uc durumlu maskeler
    for dalga in ("etiket_dalga2", "etiket_dalga3", "etiket_dalga4"):
        for p in sorted((R / dalga).glob("*/*_uc.png")):
            govde = p.name[:-len("_uc.png")]
            if DOGRULAMA in govde: continue
            kaynak, stem = govde.split("__", 1)
            img = KARE_KOK / kaynak / (stem + ".jpg"); assert img.is_file(), img
            m = cv2.imread(str(p), cv2.IMREAD_GRAYSCALE)
            assert m is not None and set(np.unique(m).tolist()) <= {0, 1, 2}, p
            if govde in kareler:
                raise SystemExit(f"[DUR] ayni kare iki kaynakta: {govde} ({kareler[govde][2]} ve {dalga})")
            kareler[govde] = (img, z.maske_to_yolo(m), dalga)
    govdeler = sorted(kareler)
    assert not any(DOGRULAMA in g for g in govdeler)
    rnd = random.Random(0); rnd.shuffle(govdeler)
    n_val = round(len(govdeler) * 0.15)
    val, train = set(govdeler[:n_val]), govdeler[n_val:]
    for d in (KUME, X5):
        if d.exists(): shutil.rmtree(d)
    say = {"train": 0, "val": 0, "bos": 0, "kaynak": {}}
    for g in sorted(kareler):
        img, satir, kay = kareler[g]
        bp = "val" if g in val else "train"
        (KUME / "images" / bp).mkdir(parents=True, exist_ok=True); (KUME / "labels" / bp).mkdir(parents=True, exist_ok=True)
        _bag(img, KUME / "images" / bp / (g + ".jpg"))
        (KUME / "labels" / bp / (g + ".txt")).write_text("\n".join(satir) + ("\n" if satir else ""), encoding="utf-8")
        say[bp] += 1; say["bos"] += (not satir); say["kaynak"][kay] = say["kaynak"].get(kay, 0) + 1
        if bp == "train":
            for k in range(KAT):
                _bag(KUME / "images" / bp / (g + ".jpg"), X5 / "images" / "train" / f"{g}__x{k:02d}.jpg")
                _bag(KUME / "labels" / bp / (g + ".txt"), X5 / "labels" / "train" / f"{g}__x{k:02d}.txt")
    say["x5_train"] = len(list((X5 / "images" / "train").glob("*.jpg")))
    ortak = "\nnc: 2\nnames:\n  0: traversable\n  1: blocked\n"
    tam = f"""# GECE v7a (ON_KAYIT §14): tam karisim + dji_v7_x5 (0037/0039 tum etiketler, x{KAT}); val = dji_v7 val (%15, tohum 0). 0038 YOK (CONTRACTS §12).
path: {DS}
train:
  - {DS / 'rescuenet_2sinif_engelli' / 'images' / 'train'}
  - {DS / 'sentetik_arena' / 'images' / 'train'}
  - {DS / 'copy_paste_t127' / 'images' / 'train'}
  - {X5 / 'images' / 'train'}
val:
  - {KUME / 'images' / 'val'}
""" + ortak
    (DS / "karisim_gece_v7a.yaml").write_text(tam, encoding="utf-8")
    (DS / "karisim_gece_v7b.yaml").write_text(tam.replace("# GECE v7a", "# GECE v7b (rescuenet YOK)").replace(f"  - {DS / 'rescuenet_2sinif_engelli' / 'images' / 'train'}\n", ""), encoding="utf-8")
    (R / "v7_kume.json").write_text(json.dumps({**say, "val_listesi": sorted(val)}, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(say, ensure_ascii=False))


if __name__ == "__main__":
    main()
