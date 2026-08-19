"""SENTETİK VERİ DENETİMİ — eğitime sokmadan önce doğrula.

Sentetik veri sessizce bozuk olabilir (dönüşüm etiketi kaydırmış, poligon
sınır dışına taşmış, sınıf dengesi çökmüş). Bunlar eğitimi patlatmaz —
sadece modeli sessizce bozar. Bu yüzden ayrı bir denetim adımı var.

Denetlenenler:
  1. görüntü/etiket birebir eşleşiyor mu
  2. poligon koordinatları [0,1] aralığında mı, nokta sayısı yeterli mi
  3. sınıf dağılımı ve "en az bir traversable" garantisi tutuyor mu
  4. maske alanı makul mü (dejenere/nokta poligon var mı)
  5. rastgele örneklerde etiket-görüntü hizası (görsel kontak sayfası)

Kullanım:
  venv\\Scripts\\python.exe 52_sentetik_denetim.py
"""
import random
from collections import Counter
from pathlib import Path

import cv2
import numpy as np

KOK = Path(r"O:\navitas\dataset\sentetik_arena")
CIK = Path(__file__).parent / "calisma"


def main():
    rng = random.Random(0)
    toplam_hata = 0
    for bolum in ("train", "val"):
        gd, ld = KOK / "images" / bolum, KOK / "labels" / bolum
        if not gd.exists():
            print(f"{bolum}: yok, atlanıyor")
            continue
        gorseller = sorted(gd.glob("*.jpg"))
        etiketler = {p.stem for p in ld.glob("*.txt")}
        eksik = [p.name for p in gorseller if p.stem not in etiketler]
        fazla = etiketler - {p.stem for p in gorseller}

        sinif = Counter()
        trav_yok = 0
        kotu_koord = kucuk_poly = 0
        alanlar = {0: [], 1: []}
        nokta_sayilari = []

        for p in gorseller:
            satirlar = (ld / f"{p.stem}.txt").read_text(encoding="utf-8").splitlines()
            var0 = False
            for s in satirlar:
                q = s.split()
                if len(q) < 7:
                    kucuk_poly += 1
                    continue
                c = int(q[0])
                v = np.asarray(q[1:], np.float32)
                if v.min() < -1e-6 or v.max() > 1 + 1e-6:
                    kotu_koord += 1
                pts = v.reshape(-1, 2)
                nokta_sayilari.append(len(pts))
                sinif[c] += 1
                var0 |= (c == 0)
                # kapalı poligon alanı (ayakkabı bağı formülü, normalize)
                x, y = pts[:, 0], pts[:, 1]
                alanlar[c].append(abs(np.dot(x, np.roll(y, 1)) -
                                      np.dot(y, np.roll(x, 1))) / 2)
            if not var0:
                trav_yok += 1

        hata = len(eksik) + len(fazla) + kotu_koord
        toplam_hata += hata
        print(f"\n=== {bolum} ===")
        print(f"  görüntü {len(gorseller)} · etiket {len(etiketler)} · "
              f"eksik {len(eksik)} · fazla {len(fazla)}")
        print(f"  poligon: traversable {sinif[0]} · blocked {sinif[1]} · "
              f"başka sınıf {sum(v for k, v in sinif.items() if k > 1)}")
        print(f"  traversable İÇERMEYEN görüntü: {trav_yok} "
              f"(%{100 * trav_yok / max(1, len(gorseller)):.1f})")
        print(f"  aralık dışı koordinat: {kotu_koord} · kısa poligon: {kucuk_poly}")
        if nokta_sayilari:
            print(f"  poligon nokta sayısı: ort {np.mean(nokta_sayilari):.1f} · "
                  f"maks {max(nokta_sayilari)}")
        for c, ad in ((0, "traversable"), (1, "blocked")):
            if alanlar[c]:
                a = np.array(alanlar[c])
                print(f"  {ad:12} alan oranı: ort %{100 * a.mean():.2f} · "
                      f"min %{100 * a.min():.3f} · maks %{100 * a.max():.2f}")
        print(f"  {'✓ TEMİZ' if hata == 0 else f'✗ {hata} HATA'}")

    # görsel hiza kontrolü — rastgele 6 örnek
    gd = KOK / "images" / "train"
    ornek = rng.sample(sorted(gd.glob("*.jpg")), min(6, len(list(gd.glob('*.jpg')))))
    kareler = []
    for p in ornek:
        im = cv2.imread(str(p))
        h, w = im.shape[:2]
        ov = im.copy()
        for s in (KOK / "labels" / "train" / f"{p.stem}.txt").read_text().splitlines():
            q = s.split()
            if len(q) < 7:
                continue
            pts = (np.asarray(q[1:], np.float32).reshape(-1, 2) * (w, h)).astype(np.int32)
            cv2.fillPoly(ov, [pts], (0, 200, 0) if q[0] == "0" else (0, 0, 220))
        kareler.append(cv2.resize(cv2.addWeighted(im, 0.6, ov, 0.4, 0), (300, 300)))
    if kareler:
        CIK.mkdir(exist_ok=True)
        yol = CIK / "sentetik_denetim.jpg"
        cv2.imwrite(str(yol), np.vstack([np.hstack(kareler[:3]), np.hstack(kareler[3:6])]))
        print(f"\nGörsel hiza kontrolü: {yol}")

    print(f"\n{'✓ DENETİM GEÇTİ' if toplam_hata == 0 else f'✗ {toplam_hata} HATA — eğitime sokma'}")


if __name__ == "__main__":
    main()
