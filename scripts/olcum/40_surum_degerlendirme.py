"""SÜRÜM DEĞERLENDİRME — v4'ten bugüne tüm modellerin toplu karnesi.

Deney defterinden (bakir test) + karar doğruluğu ölçümlerinden + hız ölçümlerinden
tek tabloda birleştirir. v13/v14 gibi yeni koşular bitince tekrar çalıştırılabilir.

Kullanım:
  venv\\Scripts\\python.exe 40_surum_degerlendirme.py
"""
import csv
import json
from pathlib import Path

import defter
from ayarlar import REPO

RUNS = REPO / "codes" / "runs" / "segment"

# ad -> (mimari/çözünürlük, ne değişti, masaüstü FPS, Jetson tahmini)
KUNYE = {
    "v3":              ("yolov8s @512→640", "taban (v2'den güçlendirme)", 117, "40-50"),
    "v4":              ("yolov8s @512→640", "v3'ten ft, imgsz 512→640", 117, "40-50"),
    "v5a":             ("yolov8s @640", "sıfırdan pretrained, ovs×2", 117, "40-50"),
    "v5b":             ("yolov8s @640", "v3'ten ft, ovs×3", 117, "40-50"),
    "v5c":             ("yolov8m @640", "yolov8m, COCO'dan 200 epoch", 88, "18-22"),
    "v6_1024s":        ("yolov8s @1024", "native 1024 veri (ayrı test kümesi!)", 66, "15-20"),
    "v7_1024m":        ("yolov8m @1024", "native 1024 + m (ayrı test kümesi!)", 47, "10-15"),
    "v8_clspw05":      ("yolov8m @640", "v5c'den 100ep ft + cls_pw=0.5 [ADİL DEĞİL]", 88, "18-22"),
    "v8_mixup":        ("yolov8m @640", "v5c'den 100ep ft + mixup [ADİL DEĞİL]", 88, "18-22"),
    "v8_clspw03":      ("yolov8m @640", "v5c'den 100ep ft + cls_pw=0.3 [ADİL DEĞİL]", 88, "18-22"),
    "v9_mixup_full":   ("yolov8m @640", "v5c reçetesi + copy_paste_mode=mixup", 88, "18-22"),
    "v12_mixup_wblr0": ("yolov8m @640", "v9 + warmup_bias_lr=0.0", 88, "18-22"),
    "v13_mixup_box10": ("yolov8m @640", "v9 + box=10 (maske kaybı ağırlığı)", 88, "18-22"),
    "v15_ft2sinif":    ("yolov8m @640", "10-sınıf ön eğitim → 2 sınıf ft", 88, "18-22"),
    "v16_arena_pilot": ("yolov8m @640", "v15 + sentetik arena karışımı (v1 üreteç)", 88, "18-22"),
    "v17_arena_tam":   ("yolov8m @640", "v15 + sentetik arena (şerit modeli)", 88, "18-22"),
}

# ARENA ÖLÇÜMÜ (48_arena_iou.py, n=2, @eşik 0,25) — ad -> (moloza basma %, not)
# DİKKAT: görüntüler arenanın YAPAY ZEKÂ ÜRETİMİ temsilleridir (gerçek saha
# fotoğrafı değil) → domain transferi sondası, arena performansı KANITI değil.
#
# ASIL ÖLÇÜT MOLOZA BASMA — "geçilebilir"in arenada iki savunulabilir tanımı var
# (işaretli patika / engelsiz her zemin) ve IoU hangisini seçtiğinize göre değişiyor.
# Ama İKİ TANIM DA moloza basmayı hata sayar. DÜŞÜK olan iyi. Bkz. BULGULAR §13d.
# UYARI: kör bir model %0 alır (bedava) — kaplama yüzdesiyle birlikte okuyun.
ARENA = {
    "v4":              (0.0, "kör @0,25 — %0 bedava geliyor"),
    "v5c":             (0.0, "kör @0,25 (IoU 0,077 yalnız 0,10 eşiğinde)"),
    "v9_mixup_full":   (0.0, "tam kör, hiçbir eşikte çıktı yok"),
    "v13_mixup_box10": (37.7, "EN KÖTÜ — görüntünün %84,7'sini boyuyor"),
    "v15_ft2sinif":    (2.7, "EN İYİ — karar üreten VE moloza girmeyen tek model"),
    "v16_arena_pilot": (31.6, "sentetik v1 GERİLETTİ (v15'in 11 katı); "
                              "etiketsiz moloz + alan oranı hatası"),
    "v17_arena_tam":   (0.0, "★ SIÇRAMA — 1.jpg'de IoU 0,861 (yolu birebir izliyor, "
                             "kesinlik 0,863, kaplama %4,2); AMA 2.png'de hâlâ kör "
                             "→ havuz IoU 0,615. %0 moloz gerçek, körlükten değil"),
}

# Ölçülmüş karar doğruluğu (500 sahne, bakir test) — (kaba fonksiyon, üretim fonksiyonu)
KARAR = {
    "v3": (70.2, None), "v4": (71.8, None), "v5a": (71.6, None),
    "v5c": (74.6, 74.4), "v6_1024s": (74.4, 77.0), "v7_1024m": (71.6, None),
}

SIRA = ["v3", "v4", "v5a", "v5b", "v5c", "v6_1024s", "v7_1024m",
        "v8_clspw05", "v8_mixup", "v8_clspw03",
        "v9_mixup_full", "v12_mixup_wblr0", "v13_mixup_box10", "v15_ft2sinif",
        "v16_arena_pilot", "v17_arena_tam"]


def defter_test():
    d = {}
    for k in defter.oku():
        if k["split"] == "test" and k.get("mask_mAP50"):
            d[k["ad"]] = k          # son kayıt kazanır
    return d


def egitim_durumu(ad):
    p = RUNS / ad / "results.csv"
    if not p.exists():
        return None
    try:
        r = list(csv.DictReader(open(p, encoding="utf-8")))
        return len(r)
    except Exception:
        return None


def main():
    t = defter_test()
    print("=" * 96)
    print("SÜRÜM KARNESİ — v3'ten bugüne (bakir test, aynı 305 görüntülük küme)")
    print("=" * 96)
    print(f"{'sürüm':17} {'mimari':17} {'mAP50':>7} {'trav':>7} {'blocked':>8} "
          f"{'karar%':>7} {'MOLOZ↓':>7}  durum")
    print("-" * 96)

    en_iyi_map, en_iyi_ad = 0, None
    en_iyi_trav, en_iyi_trav_ad = 0, None
    for ad in SIRA:
        kun = KUNYE.get(ad, ("?", "?", 0, "?"))
        k = t.get(ad)
        if k:
            m = float(k["mask_mAP50"])
            tr = float(k["traversable_AP50"])
            b = float(k["blocked_AP50"])
            kd = KARAR.get(ad)
            kds = (f"{kd[1]:.1f}*" if kd and kd[1] else (f"{kd[0]:.1f}" if kd else ""))
            ar = ARENA.get(ad)
            ars = f"%{ar[0]:.1f}" if ar else "—"
            uyari = " ⚠küme" if ad in ("v6_1024s", "v7_1024m") else ""
            print(f"{ad:17} {kun[0]:17} {m:7.4f} {tr:7.4f} {b:8.4f} {kds:>7} {ars:>7}  "
                  f"{kun[1][:30]}{uyari}")
            if m > en_iyi_map and ad not in ("v6_1024s", "v7_1024m"):
                en_iyi_map, en_iyi_ad = m, ad
            if tr > en_iyi_trav and ad not in ("v6_1024s", "v7_1024m"):
                en_iyi_trav, en_iyi_trav_ad = tr, ad
        else:
            n = egitim_durumu(ad)
            durum = f"eğitiliyor ({n} epoch)" if n else "koşulmadı"
            print(f"{ad:17} {kun[0]:17} {'—':>7} {'—':>7} {'—':>8} {'—':>7} {'—':>7}  {durum}")

    print("-" * 96)
    print(f"EN İYİ mAP        : {en_iyi_ad} — {en_iyi_map:.4f}")
    print(f"EN İYİ traversable: {en_iyi_trav_ad} — {en_iyi_trav:.4f}  "
          "(kararı SÜREN sınıf — analyze_path yalnız bunu kullanıyor)")
    print("\n* = üretim karar fonksiyonu (rpi_inference); diğerleri kaba fonksiyon")
    print("⚠küme = native-1024 test kümesinde ölçüldü, diğerleriyle kıyaslanamaz")
    print("MOLOZ↓ = molozun yüzde kaçına 'geçilebilir' dendi @0,25 (48_arena_iou.py,")
    print("         n=2, YZ üretimi arena görselleri). DÜŞÜK İYİ — ama kör model de")
    print("         %0 alır; notlara bakmadan okumayın.")
    print("\nARENA NOTLARI (asıl ölçüt — RescueNet mAP arenaya transfer OLMUYOR):")
    for ad, (skor, not_) in sorted(ARENA.items(), key=lambda t: t[1][0]):
        print(f"  {ad:17} %{skor:4.1f} · {not_}")

    print("\n" + "=" * 96)
    print("ÖZET DEĞERLENDİRME")
    print("=" * 96)
    print("""
⛔ ÖNCE BUNU OKUYUN: RescueNet mAP SIRALAMASI ARENAYA TRANSFER OLMUYOR.
  mAP lideri v13, arenada EN KÖTÜ (molozun %37,7'sine "geçilebilir" diyor).
  mAP'te ortalarda olan v15, arenada tek çalışan model (%2,7).
  Yani aşağıdaki mAP sütunu yarışma başarısını ÖLÇMÜYOR. Bkz. BULGULAR §12-13.

RescueNet İÇİNDE kazanan: v9_mixup_full (mAP50 0,6787 · blocked 0,5371)
  → v5c reçetesinin aynısı, tek fark copy_paste_mode=mixup. FPS değişmedi.
  → AMA arenada TAM KÖR. Üretim adayı olarak savunulamaz.

ARENA'da kazanan: v17_arena_tam ★
  → 1.jpg'de IoU 0,077 (önceki en iyi) → 0,861. Yolu birebir izliyor, moloza
    hiç girmiyor (%0), kaplama %4,2 (yer gerçeği %3,6). Sızıntı kontrolü yapıldı:
    6452 eğitim görüntüsünün hiçbiri arena görselleriyle eşleşmiyor.
  → AMA 2.png'de hâlâ TAM KÖR (%0 çıktı) — n=2'nin biri çözüldü, biri çözülmedi.
  → Bedeli: bakir test mAP 0,6550 → 0,635 (−0,020, gürültüde) ·
    traversable 0,8402 → 0,801 (−0,039, gürültü sınırında — izlenmeli).

ÇALIŞAN KALDIRAÇLAR (bakir testte doğrulanmış):
  • yolov8m kapasitesi (v4→v5c): mAP +0,043 · blocked +0,076
  • copy_paste_mode=mixup (v5c→v9): mAP +0,008 · blocked +0,028
  • 10 sınıflı yardımcı görev ön eğitimi (v15): mAP'te değil ARENADA kazandırdı

ÇALIŞMAYAN / REDDEDİLEN:
  • native 1024 çözünürlük (v6/v7): mAP artmadı, FPS düştü
  • warmup_bias_lr=0.0 (v12): val +0,013 ama TEST −0,013 (val'e aşırı uyum)
  • cls_pw (v8 serisi): geriledi · v8 pilotları: metodoloji hatası
  • sentetik arena v1 (v16): mAP'i bozmadı ama arenayı 11× KÖTÜLEŞTİRDİ
    (etiketsiz moloz + alan oranı iki katı) → üreteç düzeltildi

YENİ VE EN BÜYÜK KALDIRAÇ: sentetik arena v2 — şerit modeli (v17)
  Arena duvarlarla ayrılmış ŞERİTLERdir, şeritlerin TAMAMI etiketlidir ve moloz
  her zaman blocked şeridin içine KIRPILIR → etiketsiz moloz kalmaz. Arena ölçeği
  kare içinde geniş aralıkta rastgele → sabit ölçek önyargısı kurulamaz.
  Sonuç: arena IoU 0,077 → 0,861 (bir görüntüde). RescueNet mAP bedeli gürültüde.
  ⚠ n=2'nin diğer görüntüsü hâlâ çözülmedi; gerçek arena fotoğrafıyla doğrulanmalı.

FPS KISITI NEYİ ELİYOR:
  yolov8l@640 ~11-14 FPS · m@1024 ~10-15 FPS → ikisi de 15 altı, aday değil.
  Bu yüzden mimari/çözünürlük ekseni KİLİTLİ; yalnız FPS-nötr kaldıraçlar kaldı.
  (Tüm sentetik veri çalışması da FPS-nötr: mimari/çözünürlük değişmiyor.)
""")


if __name__ == "__main__":
    main()
