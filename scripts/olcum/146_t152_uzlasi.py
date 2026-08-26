"""146 — T152 UZLASI (ON_KAYIT §11): iki bagimsiz etiket gecisi -> uzlasi maskesi + uyusmazlik haritasi
+ dataset/dji_kirsal_0038_bolum_v3/{test,val}.

Kural (deterministik, guvenli yon):  sinif 0 <=> A==1 and B==1 ;  sinif 1 <=> A==2 or B==2 ;  aksi 0.
Gecis A (mevcut referans): test -> results/gece_20260826/test29_referans/{A..F}/<govde>_uc.png (v2);
                           val30 -> dataset/dji_kirsal_0038_bolum/labels/val (YOLO -> maske);
                           val52 -> results/gece_20260826/etiket_dalga{2,3}/*/<govde>_uc.png
Gecis B (yeni, kor):       results/gece_20260826/t152_gecis2/G*/<govde>_uc.png
"""
from __future__ import annotations
import importlib.util, json, os, shutil
from pathlib import Path
import cv2, numpy as np

KOK = Path(__file__).resolve().parents[2]
R = KOK / "results" / "gece_20260826"
ESKI = KOK / "dataset" / "dji_kirsal_0038_bolum"
DALGA2 = KOK / "dataset" / "dji_kirsal_dalga2"
YENI = KOK / "dataset" / "dji_kirsal_0038_bolum_v3"
KARE_KOK = KOK / "results" / "dji_20260822" / "kareler_1fps"
W, H = 960, 540


def _modul(ad):
    spec = importlib.util.spec_from_file_location(ad, KOK / "scripts" / "olcum" / f"{ad}.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def yolo_to_maske(lbl: Path) -> np.ndarray:
    m = np.zeros((H, W), np.uint8)
    if lbl.is_file():
        for satir in lbl.read_text(encoding="utf-8").splitlines():
            v = satir.split()
            if len(v) < 7: continue
            pts = (np.array([float(x) for x in v[1:]], np.float32).reshape(-1, 2) * [W, H]).astype(np.int32)
            cv2.fillPoly(m, [pts], 1 if int(v[0]) == 0 else 2)
    return m


def gecis_a(govde: str, bolum: str, kaynak_dizin: str) -> np.ndarray:
    if bolum == "test":
        y = sorted((R / "test29_referans").glob(f"[A-F]/{govde}_uc.png")); assert len(y) == 1, (govde, y)
        return cv2.imread(str(y[0]), cv2.IMREAD_GRAYSCALE)
    if kaynak_dizin == "bolum":
        return yolo_to_maske(ESKI / "labels" / "val" / (govde + ".txt"))
    y = sorted(list((R / "etiket_dalga2").glob(f"*/{govde}_uc.png")) + list((R / "etiket_dalga3").glob(f"*/{govde}_uc.png")))
    assert len(y) == 1, (govde, y)
    return cv2.imread(str(y[0]), cv2.IMREAD_GRAYSCALE)


def iou(a, b):
    u = int((a | b).sum()); return round(int((a & b).sum()) / u, 4) if u else None


def main():
    z = _modul("135_dji_kirsal_zincir")
    if YENI.exists(): shutil.rmtree(YENI)
    kareler = [(p, "test", "bolum") for p in sorted((ESKI / "images" / "test").glob("*.jpg"))] + \
              [(p, "val", "bolum") for p in sorted((ESKI / "images" / "val").glob("*.jpg"))] + \
              [(p, "val", "dalga2") for p in sorted((DALGA2 / "images" / "val").glob("*.jpg"))]
    assert len(kareler) == 111, len(kareler)
    (R / "t152_uzlasi").mkdir(parents=True, exist_ok=True)
    harita = []
    for p, bolum, kd in kareler:
        govde = p.stem
        a = gecis_a(govde, bolum, kd)
        yb = sorted((R / "t152_gecis2").glob(f"G*/{govde}_uc.png")); assert len(yb) == 1, (govde, yb)
        b = cv2.imread(str(yb[0]), cv2.IMREAD_GRAYSCALE)
        assert a.shape == b.shape == (H, W) and set(np.unique(a).tolist()) <= {0, 1, 2} and set(np.unique(b).tolist()) <= {0, 1, 2}
        u = np.zeros((H, W), np.uint8)
        u[(a == 1) & (b == 1)] = 1
        u[(a == 2) | (b == 2)] = 2
        cv2.imwrite(str(R / "t152_uzlasi" / (govde + "_uc.png")), u)
        for bl in ("images", "labels"):
            (YENI / bl / bolum).mkdir(parents=True, exist_ok=True)
        os.link(p, YENI / "images" / bolum / p.name)
        satir = z.maske_to_yolo(u)
        (YENI / "labels" / bolum / (govde + ".txt")).write_text("\n".join(satir) + ("\n" if satir else ""), encoding="utf-8")
        harita.append({"govde": govde, "bolum": bolum,
                       "A_sinif0": round(float((a == 1).mean()), 4), "B_sinif0": round(float((b == 1).mean()), 4), "U_sinif0": round(float((u == 1).mean()), 4),
                       "A_sinif1": round(float((a == 2).mean()), 4), "B_sinif1": round(float((b == 2).mean()), 4), "U_sinif1": round(float((u == 2).mean()), 4),
                       "iou_sinif0": iou(a == 1, b == 1), "iou_sinif1": iou(a == 2, b == 2),
                       "uyusmayan_pay": round(float((a != b).mean()), 4),
                       "A_yol_B_yol_degil": round(float(((a == 1) & (b != 1)).mean()), 4), "B_yol_A_yol_degil": round(float(((b == 1) & (a != 1)).mean()), 4)})
    ozet = {"_ne": "T152 uzlasi (ON_KAYIT §11): sinif0 = A∧B, sinif1 = A∨B", "n": len(harita),
            "iou_sinif0_medyan": float(np.median([h["iou_sinif0"] for h in harita if h["iou_sinif0"] is not None])),
            "uyusmayan_pay_medyan": float(np.median([h["uyusmayan_pay"] for h in harita])),
            "en_uyumsuz_10": sorted(harita, key=lambda h: -h["uyusmayan_pay"])[:10], "kareler": harita}
    (R / "t152_uzlasi" / "uyusmazlik_haritasi.json").write_text(json.dumps(ozet, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in ozet.items() if k not in ("kareler", "en_uyumsuz_10")}, ensure_ascii=False))
    print("en uyumsuz:", [(h["govde"][-25:], h["uyusmayan_pay"]) for h in ozet["en_uyumsuz_10"][:5]])


if __name__ == "__main__":
    main()
