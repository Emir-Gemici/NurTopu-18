# Navitas — Model Güçlendirme (v3): Plan · Durum · Devir Notu

> **Bu dosya kalıcı hafızadır.** Amaç: token/oturum biterse başka bir AI (codex,
> başka Claude Code hesabı) buradan devam edip işi yarıda bırakmasın. Her önemli
> adımdan sonra bu dosyayı güncelle. Son güncelleme: **2026-07-12**.

---

## 0. TEK CÜMLE
Segmentasyon modelinin genel mask mAP50'sini **0,60 takım hedefinin üstüne**
(hedef ≥ 0,65) çıkarmak için YOLOv8**s**-seg tabanlı güçlendirilmiş bir eğitim
(v3) hazırlandı; kullanıcı Colab'da eğitip test edecek, sonuç DDR'a işlenecek.

---

## 1. BAŞARI KRİTERİ
- **Zorunlu:** v3 mask mAP50 (genel, 294 görüntülük RescueNet val setinde) ≥ **0,60**.
- **Hedef:** ≥ **0,65** ("şaşırt beni" — kullanıcı bunu istedi).
- **Kritik alt-metrik:** blocked mask mAP50'yi 0,322'den **≥ 0,45**'e çıkarmak
  (genel mAP'i çeken TEK sebep bu; aşağıya bak).

---

## 2. MEVCUT DURUM ANALİZİ (neden buradayız)

Ölçülen değerler (11.07.2026 bağımsız Colab val, `results/v2_val_20260711/`):

| Model | genel mask mAP50 | traversable | blocked |
|---|---|---|---|
| v1 (rescuenet_seg_v1) | **0,619** ✅ | 0,874 | 0,363 |
| v2 (navitas_seg_v2, SAHADA) | **0,595** ❌ | 0,868 | 0,322 |

**KİLİT MATEMATİK:** genel mAP50 = iki sınıfın ORTALAMASI.
- v2: (0,868 + 0,322) / 2 = 0,595 ✓
- Yani traversable zaten mükemmel (0,87); **tüm sorun blocked'ta.**
- 0,60'ı geçmek için blocked'ın sadece **> 0,33** olması yeter (traversable sabitken).
  v1 zaten 0,363 ile geçiyor. Yani hedef fazlasıyla ulaşılabilir.

**Neden v2, v1'den KÖTÜ (blocked 0,363 → 0,322):** v2 daha ağır augmentasyonla
eğitildi (`degrees=45`, `copy_paste=0.15`, `patience=40`). Aşırı döndürme (val
doğal yönde, train 45° döner) azınlık sınıfı en çok vurur. FloodNet katkısı
BEKLENİYORDU ama gelmedi (aşağıya bak) → v2 fiilen RescueNet-only + fazla-aug =
gerileme.

---

## 3. 🔴 KRİTİK BULGU — FloodNet hiç eğitime girmedi
`dataset/download_floodnet.py` iki hatalı:
1. **Yanlış track:** `takara-ai/FloodNet_2021-Track_2_Dataset_HF` çekiyor. Track 2
   = **VQA** (görsel-soru-cevap); `description/tags/size/objects` döndürür, GÖRÜNTÜ/
   MASKE YOK. Semantik segmentasyon **Track 1**'dedir.
2. **Yanlış sınıf indeksi:** gerçek FloodNet etiketleri `road-flooded=4,
   road-non-flooded=5`; script `3` ve `4` varsayıyor (bir kayma). Ek olarak Track 1
   yalnız ~400 etiketli maske içerir (kalanı yarı-denetimli/etiketsiz).

**Sonuç:** v1 ve v2, "RescueNet+FloodNet" DENDİĞİ HALDE fiilen **RescueNet-only**
eğitildi (kanıt: v2'nin gömülü metrikleri 294'lük RescueNet val ile birebir örtüşüyor).
DDR v4.2'de bu dürüstçe düzeltildi.

**Karar:** v3'te FloodNet'e GÜVENME. RescueNet + dengeleme + kapasite ile hedefi
geç. FloodNet düzeltmesi ayrı, opsiyonel, RİSKLİ bir görev (TODO-7).

---

## 4. STRATEJİ — v3 reçetesi ve gerekçeleri (kanıta dayalı)

| # | Değişiklik | v2 | v3 | Gerekçe |
|---|---|---|---|---|
| 1 | Model boyutu | yolov8**n** (3,4M) | yolov8**s** (11M) | Azınlık sınıf için kapasite. Jetson Orin NX'te TensorRT ile 512px >30 FPS → drone için sorun yok (algı Jetson'da). **En yüksek kaldıraç.** |
| 2 | `degrees` | 45 | **15** | v1→v2 blocked gerilemesini geri al (aşırı döndürme dağılım uyuşmazlığı). |
| 3 | `copy_paste` | 0.15 | **0.30** | Instance kopyala-yapıştır = azınlık sınıf boost (Ultralytics yerleşik). |
| 4 | blocked oversampling | yok | **+2 kopya** | `dataset/oversample_blocked.py`; blocked görselleri fiziksel çoğaltır (1:3,5 → ~1:2). |
| 5 | epochs / patience | 150 / 40 | **200 / 60** | Büyük model daha uzun yakınsar. |

Beklenen sonuç: traversable ~0,86–0,90, blocked ~0,42–0,52 → **genel ~0,64–0,70.**

**GÜVENLİK AĞI:** v1 (0,619) zaten sahaya alınabilir ve 0,60'ı geçiyor. v3
başarısız olsa bile taban v1'dir → operasyon tamamen YUKARI YÖNLÜ risk.

---

## 5. DOSYA ENVANTERİ (ne nerede)

Eğitim/güçlendirme:
- `codes/train_seg_v3.py` — güçlendirilmiş eğitim scripti (yukarıdaki reçete gömülü;
  `--smoke` ile yerel doğrulandı). Sınıf bazlı rapor basar.
- `dataset/oversample_blocked.py` — blocked dengeleme (idempotent; `--clean` ile geri al;
  yerel sentetik veri ile TEST EDİLDİ, 1:4 → 1:2).
- `navitas-model-guclendirme.ipynb` — **2 bölümlü Colab notebook** (kullanıcı bunu koşacak):
  BÖLÜM 1 eğitim+güçlendirme, BÖLÜM 2 test+kıyas+zip. Tüm kod hücreleri derlendi.

Kanıt/sonuç:
- `results/v2_val_20260711/` — v2 bağımsız ölçüm kanıtı (log, json, confusion, PR).
- (gelecek) `results/v3_test_<tarih>/` — kullanıcının v3 zip'i buraya açılacak.

DDR:
- `doc/ddr/word/v4.2/` — GÜNCEL DDR (v2 sınıf bazlı + FloodNet dürüstlük notu).
- (gelecek) `doc/ddr/word/v4.3/` — v3 sonuçları işlenince.

Referans/kaynak scriptler:
- `dataset/download_and_convert.py` — RescueNet indirici (ÇALIŞIYOR).
- `dataset/download_floodnet.py` — BOZUK (Bölüm 3); düzeltilecek (TODO-7).
- `codes/train_seg.py` — eski v2 scripti (dokunma, referans).

---

## 6. ✅ TODO LİSTESİ (durumlarıyla)

- [x] **T1** v2'yi bağımsız ölç, sınıf bazlı kök neden — TAMAM (blocked 0,322).
- [x] **T2** FloodNet bug teşhisi — TAMAM (Track 2/VQA + sınıf kayması).
- [x] **T3** v3 eğitim scripti + oversampling — TAMAM (yerel smoke test geçti).
- [x] **T4** 2 bölümlü Colab notebook — TAMAM (derlendi).
- [x] **T5** Bu handoff dokümanı — TAMAM.
- [x] **T6** TAMAM (12.07) — PLANDAN FARKLI: Colab değil YEREL GPU (yeni üye
      Yunus'un RTX 5080 Laptop'ı; akış `O:\navitas-local-train\` — notebook'un
      birebir yerel karşılığı, aynı kanıt formatı). SONUÇ: genel mask mAP50
      **0,6273** ✅ (0,60 hedefi GEÇİLDİ), traversable 0,852 / blocked **0,403**
      (0,322'den). Model: `models/navitas_seg_v3_best.pt` (SHA 8e8d46a6…,
      23,9 MB). Kanıt: `results/v3_test_20260712/` + repo kökünde test zip.
- [ ] **T7** AI: v3 sonuçlarını DDR v4.3'e işle (Bölüm 8 prosedürü). **← ŞU AN
      BURADAYIZ** — kaynak md'ler 12.07'de güncellendi: bolum4/bolum5 v3
      sonuçları, MoC dağılımı 6/5/1, tüm "şartname uyarınca 915 MHz" ifadeleri
      433'e düzeltildi (resmî şartname bant BELİRTMİYOR — takım kararı 433).
      Kalan: v4.3 HTML→ODT→PDF üretimi (LibreOffice gerekli).
- [ ] **T8** AI: v3 modelini sahaya al (models/ + NCNN/TensorRT export, DDR "sahadaki model" güncelle).
- [ ] **T9** (opsiyonel/stretch) FloodNet Track 1 seg kaynağını düzelt → blocked veri genişletme → v4 eğitimi.
- [x] **T10a** (12.07) Resmî şartname V2 repoya geldi; PDF'te REQ numarası YOK
      (numaralar T3KYS'teki ayrı gereksinim setinden). 4 boş hücre şartname madde
      referanslarıyla dolduruldu (bolum5); numaralı resmî set gelince son eşleme.
- [ ] **T10b** RPi FPS ölçümü (donanım gerektirir).

---

## 7. KULLANICI İÇİN ÇALIŞTIRMA TALİMATI (kısa)
1. `navitas-model-guclendirme.ipynb` → Colab'a yükle → `Çalışma zamanı → T4 GPU`.
2. **BÖLÜM 1** hücrelerini sırayla çalıştır (token iste; ~1–2 saat eğitim).
   Biterse `navitas_v3_weights_*.zip` iner.
3. **BÖLÜM 2** hücrelerini çalıştır → kıyas tablosu + `navitas_v3_test_*.zip` iner.
4. İki zip'i repo köküne koy, Claude'a haber ver.

---

## 8. SONUÇ INGESTION PROSEDÜRÜ (herhangi bir AI uygulayabilir → DDR v4.3)
Kullanıcı `navitas_v3_test_*.zip` verince:
1. Zip'i aç; `v3_val_sonuclari.json` + `kiyas.json` + `konsol.log` + `v3_val/` oku.
   Kanıtları `results/v3_test_<tarih>/` altına kopyala (video/ağır dosya yoksa hepsi commit'lenebilir).
2. **Doğrula:** `00_OZET.md`'deki genel mAP, `v3_val_sonuclari.json` ile tutuyor mu;
   model SHA `v3_model_kimlik.json`'da mı; val seti 294 mü (`dataset_ozet` yoksa logdan).
3. `doc/ddr/word/v4.1/` (veya en güncel vX) HTML'ini `v4.3/` klasörüne kopyala,
   kapağı "Sürüm 4.3" yap. Değişecek yerler:
   - "Başarı oranları" v2 tablosunun ALTINA v3 sütunu/tablosu ekle (genel + traversable + blocked).
   - v1/v2/v3 **kıyas tablosu** ekle; "0,60 hedefi GEÇİLDİ" cümlesi.
   - Eğitim tablosuna v3 sütunu (yolov8s, degrees 15, copy_paste 0.30, oversampling, 200 ep).
   - MoC (Bölüm 5) "Segmentasyon başarımı" satırı: durum **Karşılandı**, kanıt `results/v3_test_*`.
   - Bölüm 4 model doğrulama satırı: v3 sonucunu ekle.
   - Şekil 7 pasta grafiği: segmentasyon "Karşılandı" olunca dağılım güncellenir (Karşılandı +1).
4. HTML → ODT → PDF (LibreOffice headless, bkz. geçmiş sürümler); TOC sayfa no'larını doğrula;
   PDF sayfalarını görsel kontrol et.
5. `git add` (yeni model dosyası için `git add -f models/navitas_seg_v3_best.pt`), commit
   **trs-1342 kimliğiyle, Claude izi OLMADAN** ([[git-kimlik-tercihi]]), push.

---

## 9. KARAR GÜNLÜĞÜ (neden böyle)
- **FloodNet'i v3'e katmadık:** Track 1 temiz HF'de yok, ~400 maske, sınıf-index düzeltmesi
  gerek → doğrulanamayan dış veri "cerrahi" operasyona risk katar. RescueNet + dengeleme yeterli.
- **yolov8s (m değil):** m (27M) Jetson'da ~15 FPS sınırda; s güvenli + kapasite ye터li.
  s hedefi geçmezse notebook m'ye geçmeyi öneriyor.
- **Fiziksel oversampling (list-file değil):** Ultralytics dataloader'ın kopya-yolu
  tekilleştirmesinden bağımsız garanti çalışsın diye.
- **degrees 15 (0 değil):** biraz döndürme robustluğu gerçek drone yaw değişimi için gerekli;
  ama 45 fazlaydı.
- **Eğitim Colab'da, yerel değil:** yerel makine CPU + GPU yok; 200 epoch infeasible.
  Yerelde sadece kod-yolu smoke testi yapıldı.

---

## 10. RİSKLER + AZALTMA
- **Risk:** v3 yine < 0,60. **Azaltma:** m-model / oversampling +3 / güvenlik ağı v1 (0,619).
- **Risk:** Colab token yazma izni yok → push olmaz. **Azaltma:** notebook zip'i HER ZAMAN
  indirir; push best-effort. Kullanıcı zip'i elle koyar (kanıtlı akış).
- **Risk:** oversampling overfit. **Azaltma:** copies=2 (ılımlı) + ağır aug her kopyaya farklı.
- **Risk:** RescueNet indirici bozulursa. **Azaltma:** notebook 1.4'te boş-veri assert'i.

---

## 11. SONRAKİ AI İÇİN DEVİR NOTU
Buraya kadar HER ŞEY hazır ve repoda (pushlanmış). Tek beklenen: **kullanıcının Colab
koşusu (T6)**. Kullanıcı zip'i verdiğinde → Bölüm 8'i uygula → v4.3 üret → T7/T8 kapat.
Kullanıcı temposu: yavaş/açıklayıcı ister, "mala anlatır gibi" ([[kullanici-ogrenme-tempo]]),
teknik terimleri `doc/teknik_sozluk.md`'ye ekle. Git kuralları: [[git-kimlik-tercihi]].
DDR ana durum: [[ddr-raporu-15-temmuz]] hafızası + `doc/ddr/README_DDR.md`.
