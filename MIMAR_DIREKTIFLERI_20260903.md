# MİMAR DİREKTİFLERİ — 3 Eylül (Fable 5 → Opus 5 devri)

> **Yazan: Claude 2 — Fable 5, mimar.** Amelelik Opus 5'te yürür; bu dosya
> günün işlerinin bağlayıcı çerçevesidir. Her iş: ölçüm → ham çıktı → defter;
> eşik/sözleşme kararı gerekirse DUR ve "Fable 5'e al" de.
> Kapsam değişikliği (kullanıcı, 2026-09-03 sabah): TEKNOFEST soruları
> İLETİLMEYECEK → plan v2 §0 fail-safe yorumları KALICI bağlayıcıdır.
> Cuma DroidCam/DJI çekimi YOK → P6 iptal; kamera doğrulaması cumartesi
> GERÇEK kamerayla (kamera_dogrula zaten parametrik). Model döngüsü (T153/
> T47/T197) VERİ-BLOKLU: yeni veri gelmedikçe v36 son modeldir ve Faz C
> "model döngüsü" satırı düşer — dondurma kararı öne çekilebilir.

## İş 1 — T99: 89/90/91'i ÜRETİM imzasıyla yeniden koştur (GPU, sıralı)

- İmza farkı ölçülecek şey: `engel_sinif_idler=(1,2)` (araçlar engel) +
  ankorlu `baslangic/hedef` + `yol_sinif_idler=(0,)`. Üç betiği bu imzayla
  koştur; kayıp · pay · süre · kararlılık aynı tabloda ESKİ sayılarla yan
  yana raporla.
- **KAPI (görevden, aynen):** ölçüm koşulmadan HİÇBİR kod değişmez. Fark
  çıkarsa bulgu deftere, karar mimara. D-398 yan bulgusu beklentiyi
  bilgilendirir (v36 araçları engel görüyor → reddetme oranı artabilir);
  bu bir TAHMİNDİR, eşik değildir.
- Çıktı: `results/t99_uretim_imzasi/` + D-kaydı.

## İş 2 — T101: ÖNCE ÖLÇ (gerçek kadrajda koridor sayısı / sınır aşımı)

- Soru: gerçek karelerde (arena_kompozit + drone kaynaklı kareler) kadrajda
  kaç koridor görünüyor ve açık koridor `serit_no` üçte-bir sınırını ne
  sıklıkta aşıyor? (t66 sentetiğinde %29,6 idi — D-205.)
- Şerit kutusu etiketi yok (T111 duvarı): koridorlar ÜRETİMİN
  `koridor_adaylari` çıktısından alınır (model çıkarımı, üretim imzası).
  Bu bir VEKİL ölçümdür ve raporda öyle anılır.
- **KAPI (görevden, aynen):** `serit_no` DEĞİŞMEZ — sözleşme alanı
  (CONTRACTS §8). Bu tur yalnız ölçüm + rapor; "kapı bir açıklıktır"
  tanım değişikliği ancak bu sayılarla, ayrı ön kayıtla, mimarda.
- Çıktı: `results/t101_gercek_kadraj/` + D-kaydı.

## İş 3 — T61: iç-tutarlılık adayları — YALNIZ KEŞİF ölçümü

- Mimar aday tanımları (bu turda sabit; yenisi eklenecekse Fable 5'e sor):
  - **B1** maske-içi HSV kanal varyansı (zemin maskesi altında).
  - **B2** bileşen-bazlı ortalama renk sapması (bileşenler arası uzaklık).
  - **B3** maske-içi Laplacian enerji dağılımı (doku karışıklığı).
- Kümeler: kabul kümesi (meşru) + GT'li gerçek kareler
  (`gercek_kare_etiket_v1` etiketleri; model-GT IoU'su düşük kareler çökme
  VEKİLİ — vekilliği raporda açıkça yaz).
- **EŞİK YAZILMAZ:** bu tur dağılımları çıkarır; eşik ancak ikinci bir ön
  kayıtla (D-86 dersi: alt kümede "tam ayrık" görünen eşik tümde ayırmaz —
  süpürme TÜM kümede). Madde 15: gelecek ölçüt yalnız REDDEDEBİLİR.
- Çıktı: `results/t61_ic_tutarlilik/` + D-kaydı.

## Sıra ve kurallar

1→2→3 (hepsi GPU'lu; SIRALI koş, paralel GPU işi yok — BSOD örüntüsü).
Her işten sonra: genel kapı 15/15 + tam suit + commit/push (yeni imza
kuralıyla). Kod değişikliği bu üç işte YOK (yalnız ölçüm betikleri eklenir);
üretim koduna dokunan her şey Fable 5 kararı ister.
