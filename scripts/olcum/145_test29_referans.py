"""145 — TEST29 REFERANS TAMAMLAMA (ON_KAYIT §10).

  hazirla : mevcut test etiketlerinden (dataset/dji_kirsal_0038_bolum/labels/test) uc durumlu TABAN
            maskeleri + izgarali gosterimler uretir -> results/gece_20260826/test29_referans/taban/
  kur     : amelelerin yeni maskelerinden (test29_referans/<grup>/*_uc.png) YENI kumeyi kurar ->
            dataset/dji_kirsal_0038_bolum_v2/{images,labels}/test (eski kume DOKUNULMAZ), fark ozeti yazar.
"""
from __future__ import annotations
import argparse, importlib.util, json, os, shutil
from pathlib import Path
import cv2, numpy as np

KOK = Path(__file__).resolve().parents[2]
ESKI = KOK / "dataset" / "dji_kirsal_0038_bolum"
YENI = KOK / "dataset" / "dji_kirsal_0038_bolum_v2"
REF = KOK / "results" / "gece_20260826" / "test29_referans"
KARE_KOK = KOK / "results" / "dji_20260822" / "kareler_1fps"
W, H = 960, 540


def _modul(ad):
    spec = importlib.util.spec_from_file_location(ad, KOK / "scripts" / "olcum" / f"{ad}.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def hazirla():
    (REF / "taban").mkdir(parents=True, exist_ok=True)
    kareler = sorted((ESKI / "images" / "test").glob("*.jpg"))
    assert len(kareler) == 29, len(kareler)
    liste = []
    for p in kareler:
        m = np.zeros((H, W), np.uint8)
        for satir in (ESKI / "labels" / "test" / (p.stem + ".txt")).read_text(encoding="utf-8").splitlines():
            v = satir.split()
            if len(v) < 7: continue
            pts = (np.array([float(x) for x in v[1:]], np.float32).reshape(-1, 2) * [W, H]).astype(np.int32)
            cv2.fillPoly(m, [pts], 1 if int(v[0]) == 0 else 2)
        cv2.imwrite(str(REF / "taban" / (p.stem + "_uc.png")), m)
        kaynak, stem = p.stem.split("__", 1)
        liste.append({"govde": p.stem, "kare": f"{kaynak}/{stem}.jpg", "taban": f"results/gece_20260826/test29_referans/taban/{p.stem}_uc.png",
                      "sinif0": round(float((m == 1).mean()), 4), "sinif1": round(float((m == 2).mean()), 4), "etiketsiz": round(float((m == 0).mean()), 4)})
    gruplar = {chr(65 + g): liste[g::6] for g in range(6)}
    (REF / "atama.json").write_text(json.dumps({"_ne": "TEST29 referans tamamlama — 29 kare, 6 amele, MODEL CIKTISI GOSTERILMEZ", "gruplar": gruplar}, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"kare": len(liste), "grup": {k: len(v) for k, v in gruplar.items()}}))


def kur():
    z = _modul("135_dji_kirsal_zincir")
    if YENI.exists(): shutil.rmtree(YENI)
    (YENI / "images" / "test").mkdir(parents=True); (YENI / "labels" / "test").mkdir(parents=True)
    fark = []
    for p in sorted((ESKI / "images" / "test").glob("*.jpg")):
        yeni = sorted(REF.glob(f"[A-F]/{p.stem}_uc.png"))
        assert len(yeni) == 1, (p.stem, yeni)
        m = cv2.imread(str(yeni[0]), cv2.IMREAD_GRAYSCALE)
        assert m is not None and m.shape == (H, W) and set(np.unique(m).tolist()) <= {0, 1, 2}, yeni[0]
        tb = cv2.imread(str(REF / "taban" / (p.stem + "_uc.png")), cv2.IMREAD_GRAYSCALE)
        # KURAL: yeni maske tabanin sinif 1'ini SILEMEZ (guvenli yon) — ihlal varsa geri koy
        geri = int(((tb == 2) & (m != 2)).sum())
        if geri: m[tb == 2] = 2
        satir = z.maske_to_yolo(m)
        os.link(p, YENI / "images" / "test" / p.name) if not (YENI / "images" / "test" / p.name).exists() else None
        (YENI / "labels" / "test" / (p.stem + ".txt")).write_text("\n".join(satir) + ("\n" if satir else ""), encoding="utf-8")
        fark.append({"govde": p.stem, "sinif0_once": round(float((tb == 1).mean()), 4), "sinif0_sonra": round(float((m == 1).mean()), 4),
                     "sinif1_once": round(float((tb == 2).mean()), 4), "sinif1_sonra": round(float((m == 2).mean()), 4), "sinif1_geri_konan_px": geri})
    (REF / "fark.json").write_text(json.dumps(fark, indent=1, ensure_ascii=False), encoding="utf-8")
    d0 = sum(f["sinif0_sonra"] - f["sinif0_once"] for f in fark) / len(fark)
    print(json.dumps({"kare": len(fark), "sinif0_ort_degisim": round(d0, 4), "sinif1_geri_konan_kare": sum(1 for f in fark if f["sinif1_geri_konan_px"])}))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("komut", choices=["hazirla", "kur"]); a = ap.parse_args()
    hazirla() if a.komut == "hazirla" else kur()
