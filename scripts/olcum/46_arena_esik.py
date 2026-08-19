"""ARENA EŞİK TARAMASI — modeller arena benzeri sahnede kör değil, GÜVENSİZ.

DİKKAT — GÖRÜNTÜLERİN NİTELİĞİ: test_images/ai/{1.jpg,2.png} arenanın YAPAY ZEKÂ
ile ÜRETİLMİŞ temsilleridir (commit 73b02ca "ai arena gorselleri"), gerçek saha
fotoğrafı DEĞİLDİR. Yani bu sonda "model RescueNet dışı, tepeden bakışlı, moloz+
koridor içeren bir sahneye transfer oluyor mu" sorusunu ölçer; gerçek arena
performansını KANITLAMAZ. Kendi domain boşluğu vardır.

Sahne: 3 koridor, ortada açık kıvrımlı asfalt yol, yanlarda bariyer+moloz, H hedef
bölgesi. İşletme eşiği conf=0.25'te modeller neredeyse hiçbir şey bulmuyor; ama
conf=0.01'de v5c 75 traversable tespiti üretiyor (en yüksek güven 0,666) →
sinyal VAR, eşiğin altında.

Bu betik eşiği tarayıp hangi eşiğin doğru koridoru bulduğunu ölçer.
Yer gerçeği: her iki görüntüde de AÇIK KORİDOR ORTADA (gözle doğrulandı).

>> "doğru/2" SAYISINI TEK BAŞINA OKUMAYIN. Yanındaki KAPLAMA YÜZDESİNE bakın:
   %80+ boyayan bir model her şeyi yol sanıyordur ve "ORTA" cevabı tesadüftür
   (v13 böyle: %84,7). Ayrım gücü = molozu boyamadan yolu bulmak.

Kullanım:
  venv\\Scripts\\python.exe 46_arena_esik.py
"""
import sys
from pathlib import Path

import cv2
import numpy as np

from ayarlar import REPO

sys.path.insert(0, str(REPO / "codes"))
from rpi_inference import analyze_path

CIK = REPO / "results" / "arena_esik"
ESIKLER = [0.02, 0.05, 0.08, 0.10, 0.15, 0.20, 0.25]
# (görüntü, doğru koridor) — gözle doğrulandı: ikisinde de ORTA açık
ARENA = [("1.jpg", 2), ("2.png", 2)]
RUNS = REPO / "codes" / "runs" / "segment"
MODELLER = [("v5c", REPO / "models" / "aday_v5c_m640.pt"),
            ("v9", REPO / "models" / "aday_v9_mixup_m640.pt"),
            ("v4", REPO / "models" / "navitas_seg_v4_best.pt"),
            ("v12", RUNS / "v12_mixup_wblr0" / "weights" / "best.pt"),
            ("v13", RUNS / "v13_mixup_box10" / "weights" / "best.pt"),
            ("v15_10sinif", RUNS / "v15_ft2sinif" / "weights" / "best.pt")]


def maske_esikli(r, h, w, esik, sinif=0):
    m = np.zeros((h, w), np.uint8)
    if r.masks is None or r.boxes is None:
        return m
    for poly, cls, guv in zip(r.masks.xy, r.boxes.cls, r.boxes.conf):
        if int(cls) == sinif and float(guv) >= esik and len(poly) >= 3:
            cv2.fillPoly(m, [poly.astype(np.int32)], 1)
    return m


def main():
    from ultralytics import YOLO
    CIK.mkdir(parents=True, exist_ok=True)
    yon = {1: "SOL", 2: "ORTA", 3: "SAG", None: "YOK"}

    for ad, yol in MODELLER:
        if not yol.exists():
            continue
        model = YOLO(str(yol))
        print(f"\n{'=' * 62}\n{ad}\n{'=' * 62}")
        print(f"{'eşik':>6} " + " ".join(f"{g:>12}" for g, _ in ARENA) + "   doğru")
        for e in ESIKLER:
            satir, dogru = [], 0
            for g, gt in ARENA:
                im = cv2.imread(str(REPO / "test_images" / "ai" / g))
                h, w = im.shape[:2]
                # tek çıkarım, düşük eşik; süzme çevrimdışı
                r = model.predict(im, imgsz=640, conf=0.01, verbose=False)[0]
                m = maske_esikli(r, h, w, e)
                karar, guven, _ = analyze_path(m)[:3]
                dogru += int(karar == gt)
                yuzde = 100 * int(m.sum()) / (h * w)
                satir.append(f"{yon[karar]:>5}/%{yuzde:4.1f}")
                if abs(e - 0.05) < 1e-9:   # örnek görsel: eşik 0,05
                    ov = im.copy()
                    ov[m > 0] = (0, 220, 0)
                    vis = cv2.addWeighted(im, 0.55, ov, 0.45, 0)
                    cv2.putText(vis, f"{ad} esik{e} karar={yon[karar]}",
                                (15, 45), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 255), 3)
                    cv2.imwrite(str(CIK / f"{Path(g).stem}_{ad}_e005.jpg"), vis)
            print(f"{e:>6.2f} " + " ".join(f"{s:>12}" for s in satir) + f"   {dogru}/2")

    print(f"\nGörseller: {CIK}")
    print("\nNOT: n=2, yer gerçeği gözle belirlendi (ikisinde de ORTA açık).")
    print("Bu KESİN bir ölçüm değil, arena alanında sinyalin var olup olmadığını")
    print("gösteren bir SONDA. Gerçek karar için arenadan etiketli veri gerekir.")


if __name__ == "__main__":
    main()
