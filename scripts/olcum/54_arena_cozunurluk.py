"""ARENA ÇÖZÜNÜRLÜK SONDASI — `2.png` neden hiçbir modelde çözülmüyor?

HİPOTEZ: sorun anlamsal değil, ÖLÇEKSEL. `2.png`'de yol görüntünün %1,13'ü ve
1672 px genişlikteki kare 640'a küçültülünce ~15 px kalıyor. YOLOv8-seg'in maske
başı stride 8'de çalışır ve prototip maskeleri 160×160'tır; 15 px'lik bir yapı
o ölçekte 1-2 piksele iner. Yani model "göremiyor" olabilir, "anlamıyor" değil.

Bu ayrım önemli: anlamsalsa daha çok/başka veri gerekir (pahalı, günler).
Ölçekselse yalnız çıkarım çözünürlüğü değişir (bedava, ama FPS'e mal olur).

Eğitim GEREKTİRMEZ — yalnız çıkarım imgsz'i taranır.

Kullanım:
  venv\\Scripts\\python.exe 54_arena_cozunurluk.py
  venv\\Scripts\\python.exe 54_arena_cozunurluk.py --modeller v17 v19
"""
import argparse
import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np

from ayarlar import REPO, uretim_pt

sys.path.insert(0, str(REPO / "codes"))
from rpi_inference import analyze_path

GT = Path(__file__).parent / "arena_yer_gercegi"
RUNS = REPO / "codes" / "runs" / "segment"
OLCEKLER = [640, 960, 1280, 1600]
ESIK = 0.25

KISAYOL = {
    "v5c": REPO / "models" / "aday_v5c_m640.pt",
    "v15": RUNS / "v15_ft2sinif" / "weights" / "best.pt",
    "v17": RUNS / "v17_arena_tam" / "weights" / "best.pt",
    "v18": RUNS / "v18_arena_dar" / "weights" / "best.pt",
    "v19": RUNS / "v19_dar_kontrastli" / "weights" / "best.pt",
    "v20": RUNS / "v20_cok_olcekli" / "weights" / "best.pt",
}
# ⚠ URETIM MODELI CIPLAK SABIT DEGILDIR (madde 16) — kayit defterinden cozulur.
KISAYOL["uretim"] = uretim_pt()


def maske(r, h, w, esik, sinif=0):
    m = np.zeros((h, w), np.uint8)
    if r.masks is None or r.boxes is None:
        return m
    for poly, cls, guv in zip(r.masks.xy, r.boxes.cls, r.boxes.conf):
        if int(cls) == sinif and float(guv) >= esik and len(poly) >= 3:
            cv2.fillPoly(m, [poly.astype(np.int32)], 1)
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modeller", nargs="+", default=["v17", "v19"])
    ap.add_argument("--esik", type=float, default=ESIK)
    ap.add_argument("--out", type=Path, default=None,
                    help="dizin; `ozet.json` buraya yazilir (S7). print ciktisi "
                         "AYNEN korunur — JSON EK'tir, ikame degil.")
    args = ap.parse_args()
    # S7: GORUNTU BAZINDA kayit; havuz ortalamasi ALINMAZ (44_karar_kurali.md).
    kayit = {"betik": Path(__file__).name, "esik": args.esik,
             "olcekler": OLCEKLER, "modeller": {}}

    from ultralytics import YOLO

    sahne = []
    for gp in sorted(GT.glob("*_gt.png")):
        ad = gp.name[:-7]
        kaynak = next((p for p in (REPO / "test_images" / "ai").iterdir()
                       if p.stem == ad), None)
        if kaynak is None:
            continue
        im = cv2.imread(str(kaynak))
        gi = cv2.imread(str(gp), cv2.IMREAD_GRAYSCALE)
        if gi.ndim > 2:
            gi = gi[..., 0]
        g = (gi > 127).astype(np.uint8)
        # S7: `moloza_basma_orani` ASIL OLCUTTUR (BULGULAR_20260720.md 13d),
        # bu betik onu hic tasimiyordu. Maske 48'deki kalibin AYNISIYLA okunur.
        mp = GT / f"{ad}_moloz.png"
        mi = cv2.imread(str(mp), cv2.IMREAD_GRAYSCALE) if mp.exists() else None
        if mi is not None and mi.ndim > 2:
            mi = mi[..., 0]
        mz = (mi > 127).astype(np.uint8) if mi is not None else np.zeros_like(g)
        sahne.append((kaynak.name, im, g, mz))

    # 🔴 JSON KENDI SINIRINI TASIR (S7 C maddesi) — alanlar KODDAN turetilir.
    kayit["kume"] = {
        "n": len(sahne),
        "kaynak": (REPO / "test_images" / "ai").relative_to(REPO).as_posix(),
        "gercek_arena": False,
        "not": "YZ uretimi iki gorsel; gercek 30 m arena karesi YOK",
        "goruntuler": [n for n, _, _, _ in sahne],
        "yer_gercegi": "47_arena_yer_gercegi.py (yari otomatik, 2.png'de DAR)",
    }
    print(f"eşik {args.esik} · ölçekler {OLCEKLER}")
    for gad, im, g, _mz in sahne:
        h, w = im.shape[:2]
        # yer gerçeğindeki yolun yaklaşık genişliği (alan / uzunluk)
        cs, _ = cv2.findContours(g, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        uzun = max((cv2.arcLength(c, True) / 2 for c in cs), default=1)
        kalinlik = int(g.sum()) / max(1.0, uzun)
        print(f"\n{gad}: {w}×{h} · yol alanı %{100 * g.mean():.2f} · "
              f"yaklaşık yol kalınlığı {kalinlik:.0f} px "
              f"(640'a küçültünce ~{kalinlik * 640 / max(h, w):.1f} px)")

    for ad in args.modeller:
        yol = KISAYOL.get(ad, Path(ad))
        if not Path(yol).exists():
            print(f"\n{ad}: ağırlık yok, atlanıyor")
            continue
        model = YOLO(str(yol))
        goruntu_kayitlari = []
        print(f"\n{'=' * 78}\n{ad}\n{'=' * 78}")
        print(f"{'imgsz':>6} " + " ".join(f"{g:>26}" for g, _, _, _ in sahne) + f"{'ms':>7}")
        for oc in OLCEKLER:
            hucre, sure = [], []
            for gad, im, g, mz in sahne:
                h, w = im.shape[:2]
                t0 = time.perf_counter()
                r = model.predict(im, imgsz=oc, conf=0.01, verbose=False)[0]
                sure.append((time.perf_counter() - t0) * 1000)
                p = maske(r, h, w, args.esik)
                b = int((p | g).sum())
                iou = int((p & g).sum()) / b if b else 0.0
                k = analyze_path(p)[0]
                hucre.append(f"IoU {iou:5.3f} %{100 * p.mean():5.2f} "
                             f"{({1: 'SOL', 2: 'ORTA', 3: 'SAG'}).get(k, 'YOK'):>4}")
                # GORUNTU BAZINDA kayit — havuza karismadan (S7 A maddesi).
                kes = int((p & g).sum())
                tah, ger = int(p.sum()), int(g.sum())
                mzk, mzt = int((p & mz).sum()), int(mz.sum())
                goruntu_kayitlari.append({
                    "goruntu_adi": gad, "model": ad, "imgsz": oc,
                    "esik": args.esik, "iou": iou,
                    "moloza_basma_orani": (mzk / mzt) if mzt else 0.0,
                    "kaplama": float(p.mean()),
                    "yer_gercegi_kaplamasi": float(g.mean()),
                    "kesinlik": (kes / tah) if tah else 0.0,
                    "duyarlilik": (kes / ger) if ger else 0.0,
                    "karar": ({1: "SOL", 2: "ORTA", 3: "SAG"}).get(k, "YOK"),
                    "sure_ms": round(sure[-1], 1),
                })
            print(f"{oc:>6} " + " ".join(f"{c:>26}" for c in hucre) +
                  f"{np.mean(sure):7.0f}")
        kayit["modeller"][ad] = {"agirlik": str(yol),
                                 "goruntu": goruntu_kayitlari}

    print("""
YORUM:
  IoU çözünürlükle YÜKSELİYORSA sorun ÖLÇEKSEL — model anlıyor ama göremiyordu.
    Çözüm çıkarım çözünürlüğü; bedeli FPS (ms sütunu masaüstü, Jetson değil).
  DEĞİŞMİYORSA sorun ANLAMSAL — o sahneyi hiç öğrenmemiş; veri gerekir.""")

    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        hedef = args.out / "ozet.json"
        hedef.write_text(json.dumps(kayit, ensure_ascii=False, indent=1),
                         encoding="utf-8")
        print(f"\njson -> {hedef}")


if __name__ == "__main__":
    main()
