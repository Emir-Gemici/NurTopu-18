"""ARENA YER GERÇEĞİ — 2 AI arena görüntüsü için geçilebilir-yol maskesi üret.

NEDEN: şimdiye kadarki arena sondası (46_arena_esik.py) "3 koridordan hangisi"
sorusuna bakıyordu; bu 1 bitlik bir ölçüm ve %84 alanı boyayan bir model bile
tesadüfen doğru çıkabiliyor (v13 tam olarak böyle yaptı). Gerçek ölçüt IoU'dur:
model AÇIK YOLU mu buluyor, yoksa her yeri mi boyuyor?

YÖNTEM: görüntüler yapay zekâ üretimi olduğu için renkler temiz ve ayrık —
yol belirgin bir gri/asfalt bant, zemin yeşil çim, enkaz gri-kahve dokulu.
Yol maskesi HSV eşiği + en büyük bağlı bileşen + morfoloji ile çıkarılır,
sonra GÖRSEL OLARAK DOĞRULANIR (overlay yazılır). Otomatik ama denetimli.

Bu yer gerçeği KUSURSUZ DEĞİLDİR (n=2, yarı otomatik) — mutlak skor değil,
modeller arası KARŞILAŞTIRMA için kullanılmalıdır.

Kullanım:
  venv\\Scripts\\python.exe 47_arena_yer_gercegi.py
"""
from pathlib import Path

import cv2
import numpy as np

from ayarlar import REPO

KAYNAK = REPO / "test_images" / "ai"
CIK = Path(__file__).parent / "arena_yer_gercegi"


def yol_maskesi(im):
    """Açık (geçilebilir) yolu ayıkla: düşük doygunluklu ORTA parlaklıkta asfalt."""
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    s, v = hsv[..., 1], hsv[..., 2]

    # asfalt: renksiz (düşük doygunluk) + orta-koyu ton
    m = ((s < 60) & (v > 35) & (v < 165)).astype(np.uint8)

    # enkaz da renksiz+gri; onu DOKUdan ayır — asfalt PÜRÜZSÜZ, enkaz pürüzlü
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    puruz = cv2.Laplacian(g, cv2.CV_32F, ksize=3)
    puruz = cv2.blur(np.abs(puruz), (21, 21))
    m[puruz > np.percentile(puruz, 62)] = 0

    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))

    # en büyük bağlı bileşen = ana koridor (kopuk parçaları at)
    n, etiket, ist, _ = cv2.connectedComponentsWithStats(m, 8)
    if n <= 1:
        return m
    en = 1 + int(np.argmax(ist[1:, cv2.CC_STAT_AREA]))
    ana = (etiket == en).astype(np.uint8)
    # ana bileşene DEĞEN diğer parçaları da al (yolun kopuk uzantıları)
    genis = cv2.dilate(ana, np.ones((45, 45), np.uint8))
    for k in range(1, n):
        if k == en:
            continue
        if ist[k, cv2.CC_STAT_AREA] > 1500 and ((etiket == k) & (genis > 0)).any():
            ana[etiket == k] = 1
    return cv2.morphologyEx(ana, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))


def moloz_maskesi(im):
    """Molozu ayıkla: YÜKSEK dokulu (pürüzlü) bölgeler.

    NEDEN AYRI BİR MASKE: "geçilebilir"in arenada iki savunulabilir tanımı var —
    (A) işaretli patika, (B) engelsiz her zemin. Hangi tanımın doğru olduğu
    tartışmalı ve modelleri buna göre sıralamak keyfi olur. Ama İKİ TANIM DA
    şunda hemfikir: MOLOZ geçilebilir DEĞİLDİR. Molozun ne kadarının
    "traversable" işaretlendiği bu yüzden tartışmasız ve güvenlik açısından
    asıl önemli ölçüttür (moloza sürmek görevi bitirir).
    """
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    puruz = cv2.blur(np.abs(cv2.Laplacian(g, cv2.CV_32F, ksize=3)), (21, 21))
    m = (puruz > np.percentile(puruz, 72)).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((31, 31), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((15, 15), np.uint8))
    # küçük gürültü adacıklarını at
    n, etiket, ist, _ = cv2.connectedComponentsWithStats(m, 8)
    temiz = np.zeros_like(m)
    for k in range(1, n):
        if ist[k, cv2.CC_STAT_AREA] > 4000:
            temiz[etiket == k] = 1
    return temiz


def main():
    CIK.mkdir(parents=True, exist_ok=True)
    for p in sorted(KAYNAK.iterdir()):
        if p.suffix.lower() not in (".jpg", ".jpeg", ".png"):
            continue
        im = cv2.imread(str(p))
        if im is None:
            continue
        m = yol_maskesi(im)
        h, w = im.shape[:2]
        yuzde = 100 * int(m.sum()) / (h * w)
        cv2.imwrite(str(CIK / f"{p.stem}_gt.png"), m * 255)

        # moloz (kesinlikle geçilemez) maskesi + görsel doğrulama
        mz = moloz_maskesi(im)
        mz[m > 0] = 0                       # yol molozla çakışmasın
        cv2.imwrite(str(CIK / f"{p.stem}_moloz.png"), mz * 255)
        ovm = im.copy()
        ovm[mz > 0] = (0, 0, 220)
        vm = cv2.addWeighted(im, 0.55, ovm, 0.45, 0)
        cv2.putText(vm, f"MOLOZ (gecilemez)  %{100 * mz.mean():.1f}", (15, 45),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 255), 3)
        kk = max(1, w // 1000)
        cv2.imwrite(str(CIK / f"{p.stem}_moloz_overlay.jpg"),
                    cv2.resize(vm, (w // kk, h // kk)))

        ov = im.copy()
        ov[m > 0] = (0, 220, 0)
        vis = cv2.addWeighted(im, 0.55, ov, 0.45, 0)
        cv2.putText(vis, f"YER GERCEGI  %{yuzde:.1f}", (15, 45),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 255), 3)
        k = max(1, w // 1000)
        cv2.imwrite(str(CIK / f"{p.stem}_gt_overlay.jpg"), cv2.resize(vis, (w // k, h // k)))
        print(f"{p.name:10} yol alanı %{yuzde:5.2f}  → {CIK / (p.stem + '_gt.png')}")

    print(f"\nGÖRSEL DOĞRULAMA ŞART: {CIK}\\*_gt_overlay.jpg dosyalarına bakın.")
    print("Maske yalnız AÇIK KORİDORU kaplamalı; molozu/çimi kaplamamalı.")


if __name__ == "__main__":
    main()
