"""ARENA IoU — modelleri arena görüntülerinde SAYIYLA kıyasla.

46_arena_esik.py "3 koridordan hangisi" diye soruyordu: 1 bitlik ölçüm, ve
görüntünün %85'ini boyayan model bile tesadüfen doğru çıkabiliyordu (v13).
Bu betik 47_arena_yer_gercegi.py'nin ürettiği maskeyle IoU/kesinlik/duyarlılık
hesaplar — "yolu buldu mu" ile "her yeri boyadı mı" artık ayrışır.

  kesinlik (precision) = tahminin ne kadarı GERÇEKTEN yol  → her yeri boyayan çöker
  duyarlılık (recall)  = gerçek yolun ne kadarı bulundu    → kör model çöker
  IoU                  = ikisinin birleşik ölçüsü          → ASIL ÖLÇÜT

SINIR: n=2 ve yer gerçeği yarı otomatik (2.png'de dar kalıyor). Mutlak skor
değil, MODELLER ARASI KIYAS için. Görüntüler de arenanın YZ üretimi temsilleri.

Kullanım:
  venv\\Scripts\\python.exe 48_arena_iou.py
  venv\\Scripts\\python.exe 48_arena_iou.py --modeller v15 v16_arena
"""
import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

from ayarlar import REPO, uretim_pt

sys.path.insert(0, str(REPO / "codes"))
from rpi_inference import analyze_path

GT = Path(__file__).parent / "arena_yer_gercegi"
RUNS = REPO / "codes" / "runs" / "segment"
ESIKLER = [0.05, 0.10, 0.15, 0.25, 0.40]

KISAYOL = {
    "v4":  REPO / "models" / "navitas_seg_v4_best.pt",
    "v5c": REPO / "models" / "aday_v5c_m640.pt",
    "v9":  REPO / "models" / "aday_v9_mixup_m640.pt",
    "v13": RUNS / "v13_mixup_box10" / "weights" / "best.pt",
    "v15": RUNS / "v15_ft2sinif" / "weights" / "best.pt",
    "v16": RUNS / "v16_arena_pilot" / "weights" / "best.pt",
    "v16son": RUNS / "v16_arena_pilot" / "weights" / "last.pt",
    "v17": RUNS / "v17_arena_tam" / "weights" / "best.pt",
    "v18": RUNS / "v18_arena_dar" / "weights" / "best.pt",
    "v18son": RUNS / "v18_arena_dar" / "weights" / "last.pt",
    "v19": RUNS / "v19_dar_kontrastli" / "weights" / "best.pt",
    "v19son": RUNS / "v19_dar_kontrastli" / "weights" / "last.pt",
    "v20": RUNS / "v20_cok_olcekli" / "weights" / "best.pt",
    "v20son": RUNS / "v20_cok_olcekli" / "weights" / "last.pt",
    "v17son": RUNS / "v17_arena_tam" / "weights" / "last.pt",
}
# ⚠ URETIM MODELI CIPLAK SABIT DEGILDIR (madde 16): kayit defterinden cozulur.
# Yukaridaki KISAYOL tarihsel surumlerin sabit haritasidir ve oyle kalir; bu
# giris ise defter degistikce KENDILIGINDEN takip eder.
KISAYOL["uretim"] = uretim_pt()
VARSAYILAN = ["v4", "v5c", "v9", "v13", "v15", "v16"]


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
    ap.add_argument("--modeller", nargs="+", default=VARSAYILAN)
    ap.add_argument("--out", type=Path, default=None,
                    help="dizin; `ozet.json` buraya yazilir (S7). print ciktisi "
                         "AYNEN korunur — JSON EK'tir, ikame degil.")
    args = ap.parse_args()
    # S7: makine-okunur kayit. GORUNTU BAZINDA tutulur; havuz ozeti AYRI ve
    # `havuz_` onekli. Gerekce 44_karar_kurali.md: "v17'nin 0,615'i aslinda
    # 0,861 + 0,000'di" — iki goruntunun ortalamasi ikisini de temsil etmiyor.
    kayit = {"betik": Path(__file__).name, "imgsz": 640, "esikler": ESIKLER,
             "modeller": {}}

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
        if gi.ndim > 2:                      # bazı PNG'ler tek kanallı 3B dönüyor
            gi = gi[..., 0]
        g = (gi > 127).astype(np.uint8)
        mp = GT / f"{ad}_moloz.png"
        mi = cv2.imread(str(mp), cv2.IMREAD_GRAYSCALE) if mp.exists() else None
        if mi is not None and mi.ndim > 2:
            mi = mi[..., 0]
        mz = (mi > 127).astype(np.uint8) if mi is not None else np.zeros_like(g)
        sahne.append((kaynak.name, im, g, mz))
    if not sahne:
        raise SystemExit("yer gerçeği yok — önce 47_arena_yer_gercegi.py")
    # 🔴 JSON KENDI SINIRINI TASIR (S7 C maddesi). Alanlar KODDAN turetilir:
    # dosyalar gercekten sayilir, `gercek_arena` elle yazilmis bir bayrak
    # degil, kaynak dizinin ne oldugundan gelir. Biri alti ay sonra bu
    # dosyayi acip gercek arena olcumu SANMAMALI.
    kayit["kume"] = {
        "n": len(sahne),
        "kaynak": (REPO / "test_images" / "ai").relative_to(REPO).as_posix(),
        "gercek_arena": False,
        "not": "YZ uretimi iki gorsel; gercek 30 m arena karesi YOK",
        "goruntuler": [n for n, _, _, _ in sahne],
        "yer_gercegi": "47_arena_yer_gercegi.py (yari otomatik, 2.png'de DAR)",
    }
    print(f"{len(sahne)} arena sahnesi · yol alanı: " +
          ", ".join(f"{n} %{100 * g.mean():.2f}" for n, _, g, _ in sahne))
    print("  moloz alanı: " +
          ", ".join(f"{n} %{100 * m.mean():.2f}" for n, _, _, m in sahne))

    tablo = []
    for ad in args.modeller:
        yol = KISAYOL.get(ad, Path(ad))
        if not Path(yol).exists():
            print(f"\n{ad}: ağırlık yok ({yol}) — atlanıyor")
            continue
        model = YOLO(str(yol))
        print(f"\n{'=' * 74}\n{ad}\n{'=' * 74}")
        print(f"{'eşik':>6} {'IoU':>7} {'kesinlik':>9} {'duyarlılık':>11} "
              f"{'kaplama%':>9} {'MOLOZA BASMA':>13}  karar")
        en_iyi = (0.0, None)
        moloz_025 = None
        gor_iou_025 = {}
        goruntu_kayitlari, havuz_kayitlari = [], []
        for e in ESIKLER:
            kes = birl = kesin_p = kesin_t = duy_p = duy_t = 0
            mz_kes = mz_top = 0
            kaplama, kararlar = [], []
            for gad, im, g, mz in sahne:
                h, w = im.shape[:2]
                r = model.predict(im, imgsz=640, conf=0.01, verbose=False)[0]
                p = maske(r, h, w, e)
                kes += int((p & g).sum())
                birl += int((p | g).sum())
                kesin_p += int((p & g).sum()); kesin_t += int(p.sum())
                duy_p += int((p & g).sum()); duy_t += int(g.sum())
                mz_kes += int((p & mz).sum()); mz_top += int(mz.sum())
                kaplama.append(100 * p.mean())
                k = analyze_path(p)[0]
                kararlar.append({1: "SOL", 2: "ORTA", 3: "SAG"}.get(k, "YOK"))
                # GORUNTU BAZINDA kayit — havuza KARISMADAN.
                g_kes, g_bir = int((p & g).sum()), int((p | g).sum())
                g_tah, g_ger = int(p.sum()), int(g.sum())
                g_mz, g_mzt = int((p & mz).sum()), int(mz.sum())
                goruntu_kayitlari.append({
                    "goruntu_adi": gad, "model": ad, "imgsz": 640, "esik": e,
                    "iou": (g_kes / g_bir) if g_bir else 0.0,
                    # ⚠ ASIL OLCUT BUDUR, IoU DEGIL (BULGULAR_20260720.md 13d):
                    # IoU "gecilebilir = isaretli patika" varsayimini tasir;
                    # moloza basmak HER tanimda hatadir.
                    "moloza_basma_orani": (g_mz / g_mzt) if g_mzt else 0.0,
                    "kaplama": float(p.mean()),
                    "yer_gercegi_kaplamasi": float(g.mean()),
                    "kesinlik": (g_kes / g_tah) if g_tah else 0.0,
                    "duyarlilik": (g_kes / g_ger) if g_ger else 0.0,
                    "karar": kararlar[-1],
                })
                if abs(e - 0.25) < 1e-9:
                    gb = int((p | g).sum())
                    gor_iou_025[gad] = (int((p & g).sum()) / gb if gb else 0.0,
                                        100 * p.mean())
            iou = kes / birl if birl else 0.0
            kesinlik = kesin_p / kesin_t if kesin_t else 0.0
            duyarlilik = duy_p / duy_t if duy_t else 0.0
            moloz = mz_kes / mz_top if mz_top else 0.0
            print(f"{e:>6.2f} {iou:7.3f} {kesinlik:9.3f} {duyarlilik:11.3f} "
                  f"{np.mean(kaplama):9.2f} {100 * moloz:12.1f}%  {' '.join(kararlar)}")
            havuz_kayitlari.append({
                "esik": e, "havuz_iou": iou, "havuz_kesinlik": kesinlik,
                "havuz_duyarlilik": duyarlilik,
                "havuz_moloza_basma_orani": moloz,
                "havuz_kaplama_ortalamasi": float(np.mean(kaplama)) / 100.0,
                "kararlar": list(kararlar),
            })
            if iou > en_iyi[0]:
                en_iyi = (iou, e)
            if abs(e - 0.25) < 1e-9:
                moloz_025 = moloz
        # HAVUZ IoU İKİ GÖRÜNTÜYÜ GİZLİYOR: v17'de 0,615 havuz değeri aslında
        # 0,861 + 0,000'dan geliyordu. Görüntü bazında ayrı yazdır.
        print("  görüntü bazında @0,25: " + " · ".join(
            f"{g} IoU {i:.3f} (kaplama %{k:.1f})" for g, (i, k) in gor_iou_025.items()))
        tablo.append((ad, en_iyi[0], en_iyi[1], moloz_025, dict(gor_iou_025)))
        kayit["modeller"][ad] = {
            "agirlik": str(yol),
            "goruntu": goruntu_kayitlari,
            "havuz": havuz_kayitlari,
            # ⚠ BULGULAR_20260720.md 13a tablosu bu iki sayiyi yaziyor.
            "havuz_en_iyi_iou": en_iyi[0],
            "havuz_en_iyi_esik": en_iyi[1],
            "havuz_moloza_basma_orani_0_25": moloz_025,
        }

    print("\n" + "=" * 74)
    print("ÖZET (arena, n=2)")
    print("=" * 74)
    gorseller = [n for n, _, _, _ in sahne]
    print(f"  {'model':12} {'havuz IoU':>10} {'MOLOZ@0,25':>11} " +
          " ".join(f"{g:>14}" for g in gorseller))
    for ad, iou, e, mz, gi in sorted(tablo, key=lambda t: (t[3] if t[3] is not None else 9)):
        satir = " ".join(f"{gi.get(g, (0, 0))[0]:14.3f}" for g in gorseller)
        print(f"  {ad:12} {iou:10.3f} "
              f"{('%.1f%%' % (100 * mz)) if mz is not None else '—':>11} {satir}")
    print("""
İKİ ÖLÇÜT, İKİ FARKLI SORU:
  IoU          → "işaretli patikayı buldu mu". Ama arenada 'geçilebilir'in ikinci
                 savunulabilir tanımı var (engelsiz HER zemin), o yüzden düşük IoU
                 tek başına başarısızlık kanıtı DEĞİL.
  MOLOZA BASMA → "molozun yüzde kaçına 'geçilebilir' dedi". Her iki tanımda da
                 HATA; güvenlik açısından asıl ölçüt (moloza sürmek görevi bitirir).
                 SIRALAMA BUNA GÖRE — düşük olan iyi.
SINIR: n=2, yarı otomatik maskeler, YZ üretimi görüntüler.""")

    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        hedef = args.out / "ozet.json"
        hedef.write_text(json.dumps(kayit, ensure_ascii=False, indent=1),
                         encoding="utf-8")
        print(f"\njson -> {hedef}")


if __name__ == "__main__":
    main()
