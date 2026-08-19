"""ALAN DIŞI GENELLEME TESTİ — RescueNet dışı gerçek görüntülerde model kıyası.

NEDEN: bakir test (RescueNet) modelleri ayırt edemiyor (v9 vs v5c = 24/40, gürültü).
Ama yarışma sahası RescueNet DEĞİL. Alan dışı görüntülerde hangi model daha iyi
genelliyor — bu, bakir test mAP'inden daha anlamlı bir sinyal olabilir.

Ölçüt: tespit edilen traversable alanı + karar üretilebilmesi + waypoint sayısı.
Yer gerçeği yok (etiketsiz görüntüler), bu yüzden NİTELİKSEL kıyas — ama modeller
aynı görüntülerde karşılaştırıldığı için görecelidir ve bilgi taşır.

Kullanım:
  venv\\Scripts\\python.exe 45_alan_disi_test.py
"""
import sys
from pathlib import Path

import cv2
import numpy as np

from ayarlar import REPO

sys.path.insert(0, str(REPO / "codes"))
from rpi_inference import analyze_path  # üretim karar fonksiyonu

CIK = REPO / "results" / "alan_disi_test"

MODELLER = [
    ("v5c", REPO / "models" / "aday_v5c_m640.pt"),
    ("v9_mixup", REPO / "models" / "aday_v9_mixup_m640.pt"),
    ("v4", REPO / "models" / "navitas_seg_v4_best.pt"),
]


def gorseller():
    """RescueNet DIŞI görüntüler (road_* RescueNet örnekleridir, hariç tutulur)."""
    g = []
    for d in [REPO / "test_images" / "ai", REPO / "test_images" / "gemini"]:
        if not d.exists():
            continue
        for p in sorted(d.iterdir()):
            if p.suffix.lower() in (".jpg", ".jpeg", ".png") and not p.name.startswith("road_"):
                g.append(p)
    return g


def maskele(r, h, w):
    m = {0: np.zeros((h, w), np.uint8), 1: np.zeros((h, w), np.uint8)}
    if r.masks is None or r.boxes is None:
        return m
    for poly, cls in zip(r.masks.xy, r.boxes.cls):
        c = int(cls)
        if c in m and len(poly) >= 3:
            cv2.fillPoly(m[c], [poly.astype(np.int32)], 1)
    return m


def main():
    from ultralytics import YOLO

    gs = gorseller()
    if not gs:
        raise SystemExit("alan dışı görüntü bulunamadı")
    CIK.mkdir(parents=True, exist_ok=True)
    print(f"{len(gs)} alan dışı görüntü · {len(MODELLER)} model\n")

    ozet = {ad: {"trav_yuzde": [], "karar_var": 0, "wp": []} for ad, _ in MODELLER}

    for ad, yol in MODELLER:
        if not yol.exists():
            print(f"  {ad}: ağırlık yok, atlanıyor")
            continue
        model = YOLO(str(yol))
        for p in gs:
            im = cv2.imread(str(p))
            if im is None:
                continue
            h, w = im.shape[:2]
            r = model.predict(im, imgsz=640, conf=0.25, verbose=False)[0]
            m = maskele(r, h, w)
            karar, guven, wp = analyze_path(m[0])[:3]
            yuzde = 100 * int(m[0].sum()) / (h * w)
            ozet[ad]["trav_yuzde"].append(yuzde)
            ozet[ad]["karar_var"] += int(karar is not None)
            ozet[ad]["wp"].append(len(wp))
            print(f"  {ad:10} {p.name:14} trav %{yuzde:5.2f} · "
                  f"karar {({1:'SOL',2:'ORTA',3:'SAG'}).get(karar, 'YOK'):5} · wp {len(wp)}")

            ov = im.copy()
            ov[m[0] > 0] = (0, 200, 0)
            ov[m[1] > 0] = (0, 0, 220)
            vis = cv2.addWeighted(im, 0.55, ov, 0.45, 0)
            k = max(1, w // 1400)
            cv2.imwrite(str(CIK / f"{p.stem}_{ad}.jpg"), cv2.resize(vis, (w // k, h // k)))

    print("\n" + "=" * 60)
    print("ALAN DIŞI GENELLEME ÖZETİ")
    print("=" * 60)
    print(f"{'model':12} {'ort trav%':>10} {'karar üretti':>13} {'ort wp':>8}")
    for ad, d in ozet.items():
        if not d["trav_yuzde"]:
            continue
        print(f"{ad:12} {np.mean(d['trav_yuzde']):10.2f} "
              f"{d['karar_var']}/{len(d['trav_yuzde']):<12} {np.mean(d['wp']):8.1f}")
    print(f"\nGörseller: {CIK}")
    print("NOT: yer gerçeği yok — bu NİTELİKSEL bir kıyas. Yüksek trav% ve waypoint,")
    print("modelin alan dışında yol yapısını görebildiğini gösterir; düşük değer")
    print("aşırı-uyum/genelleme zayıflığı işaretidir.")


if __name__ == "__main__":
    main()
