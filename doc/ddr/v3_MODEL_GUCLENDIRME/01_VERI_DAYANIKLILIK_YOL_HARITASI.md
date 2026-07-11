# Navitas — Veri & Dayanıklılık Yol Haritası (DİNAMİK / yaşayan belge)

> **Bu YAŞAYAN bir belgedir.** Her test → açık bulma → kapatma turunda güncellenir
> (Bölüm 7 tablosu büyür). Amaç: modeli gerçek arena koşullarında (karanlık/gölge/
> labirent) dayanıklı yapmak — RescueNet val metriğini değil.
> Son güncelleme: **2026-07-11** · Durum: **Faz 0 (DDR önceliği, uygulama beklemede)**

---

## 0. BAĞLAM ve ZAMANLAMA
- ⏰ **Bu iş DDR SONRASI başlar.** DDR teslim: 15 Temmuz 2026. Önce o bitecek.
- 🔔 Kullanıcı 15 Temmuz **ve sonrası** için hatırlatma istedi → kuruldu.
- Kullanıcı: "ileride tekrar test ederim, planda açıkları bulup kapatır, üstüne
  güçlendirmeler ve eklemeler yaparız" → bu belge tam da o döngü için tasarlandı.

---

## 1. GERÇEK PROBLEM (metrik değil, VERİ/DOMAIN)
Kullanıcının asıl derdi RescueNet val mAP'i değil:
- **Karanlık/gölgeli yolları bilemiyor.**
- **Gerçek test videosunda araçların geçtiği yolu fark etmedi.**
- **Yarış günü LABİRENT** olacak; orada iyi olmak şart.
- "Daha zeki yaparsam daha iyi" — yani genel dayanıklılık.

**Kritik ayrım:** genel mAP50'yi 0,595→0,66 çıkarmak bu sorunları ÇÖZMEZ. O sayı
aynı güneşli kasırga fotoğraflarında biraz daha iyi olmak demek; karanlık/labirent
yolu öğretmez. Bu bir **veri/domain** problemi.

Kullanıcının kendi tespiti (2026-07-11): "modeli güçlendirmek = eğitirken kullanılan
VERİ SETLERİNİ güçlendirmek. İnternette yeterli veri yok; AI ile görsel üreterek
yapabilirim — ama önce DDR."

---

## 2. KÖK TEŞHİS (kanıtlı)
1. **Model karanlığı öğrenmedi** çünkü eğitim verisi (RescueNet) güneşli, gündüz,
   kasırga hava görüntüsü. Karanlık/gölge yol örneği yok denecek kadar az.
2. **Çıkışta yama var ama kırılgan:** `codes/rpi_inference.py` → `is_dark()` +
   `normalize_light()` (gamma + CLAHE), hatta "ham vs normalize" yarışı. Kendi kod
   yorumu: *"normalizasyon bazı görüntülerde tespiti BOZAR."* → Model karanlığı
   doğuştan bilmediği için çıkış yamasına muhtaç; yama da güvenilmez.
3. **Domain gap:** RescueNet = kasırga hasarı; arena = temiz labirent. Farklı dünya.
4. **Labirent = duvar gölgeleri** (yüksek kontrast gölge yamaları), muhtemelen "gece
   karanlığı" değil. Bu ayrım augmentasyon seçimini belirler (RandomShadow ↔ düşük ışık).

---

## 3. STRATEJİ — 3 KALDIRAÇ
- **A. Işık/gölge augmentasyonu (eğitimde):** Albumentations Ultralytics'e takılır
  → `RandomShadow`, `RandomGamma`, `RandomBrightnessContrast`, `CLAHE`. Güneşli
  veriden yapay karanlık/gölge üretir; model karanlığı DOĞUŞTAN öğrenir. Ucuz, yüksek etki.
- **B. Eğitim–çıkış ön işleme eşitliği:** Şu an eğitim ham, çıkış bazen normalize →
  uyuşmazlık. İkisini aynı yap (ya ikisi de CLAHE-normalize, ya augmentasyon eğitimi
  yeterince kapsar da çıkış yaması gereksizleşir).
- **C. Domain verisi (ASIL büyük kaldıraç):** arenaya benzeyen görüntü. Kaynaklar:
  1. **Simülasyon render'ı (bedava ETİKETLİ veri!):** sim zaten 5 kıvrımlı labirent
     üretiyor ve maskeyi (yol/engel) BİLİYOR → görüntü + otomatik maske çıkarılabilir.
     Elle etiketleme gerekmez. En verimli domain-veri kaynağı.
  2. **AI ile görsel üretimi:** labirent yol + moloz + değişken ışık/gölge/açı
     (kullanıcı yapacak; model AI-üretimi arena görsellerini zaten tanıyor — kanıtlı).
  3. **Gerçek arena/maket fotoğrafı:** varsa birkaç düzine bile ince ayarda çok işe yarar.
  4. **FloodNet Track 1 (opsiyonel, en zayıf/en zahmetli):** flooded-road = tıkalı yol,
     blocked'a YENİ örnek katar (oversampling'in tekrarından iyi). AMA 2026-07-11 canlı
     kontrol: Colab'da tek satırla çekilebilecek çalışan kaynak YOK — takara=Track2/VQA
     (maskesiz), torchgeo=imagefolder (sınıflandırma, maske değil), PumeTu=gated (giriş
     ister). Gerçek ~400 maske BinaLab GitHub/Google Drive'da, elle indirme + dönüştürme
     gerektirir. Ayrıca kasırga-sel domaini, temiz labirent DEĞİL → sim/AI'den daha az
     uyumlu. Sıralama: **sim render > AI arena > FloodNet.** `download_floodnet.py`'nin
     sınıf indeksleri + sessiz-hata guardı DÜZELTİLDİ; kalan iş: gerçek Track 1 kaynağı
     bulup ÜRETİLEN GÖRÜNTÜYÜ DOĞRULAMAK (hayalet FloodNet hatasını tekrarlama).

---

## 4. FAZLI PLAN
- **Faz 0 (şimdi–15 Tem):** SADECE DDR. Bu belge + hatırlatma hazır. Uygulama YOK.
- **Faz 1 (15 Tem sonrası): VERİ.** Sim render pipeline'ı (görüntü+maske) + AI görsel
  üretimi + augmentasyon reçetesi (albumentations). Domain + karanlık/gölge çeşitliliği.
- **Faz 2: EĞİTİM (v4).** yolov8s + ağır ışık/gölge aug + domain veri (RescueNet + sim
  + AI). [[00_PLAN_DURUM_DEVIR]]'deki v3 reçetesi taban; üstüne bu belgenin verisi.
- **Faz 3: GERÇEK KOŞUL TESTİ + DÖNGÜ.** Karanlık/labirent/gerçek-video testi →
  açık bul → kapat → tekrar (Bölüm 7).

---

## 5. TEST PROTOKOLÜ (gerçek metrik — RescueNet val DEĞİL)
- **Ölçüt:** karanlık/gölge/labirent/gerçek-video koşulunda YOL KARARI doğru mu?
- **Test seti:** kullanıcının test videoları + arena görselleri + bunların sentetik
  karanlık/gölge varyantları (gamma/RandomShadow ile üretilir).
- **Nasıl:** `simulation/scripts/iha_perceive.py` ile koştur; overlay + yol kararı +
  güven; gözle doğrula + skor. Ayrıca traversable'ın DÜŞMEDİĞİNİ kontrol et (görev-kritik).

---

## 6. AÇIK SLOTLAR (bilgi gelince doldur — kullanıcıya soruldu 2026-07-11)
- [ ] **Arena görüntüsü var mı?** (fine-tune verisi için) — cevap bekleniyor.
- [ ] **"Karanlık" tanımı:** duvar gölgesi mi, düşük ışık mı? (aug seçimi) — bekleniyor.
- [ ] **Başarısız test videosunun domaini:** kapalı mekân/yandan çekim mi (alan-dışı,
      temsili değil) yoksa hava/dik mi? — bekleniyor.
- [ ] **Donanım kesin mi:** algı Jetson'da mı (yolov8s güvenli) yoksa RPi riski var mı?

---

## 7. DİNAMİK DÖNGÜ (yaşayan tablo — her turda BÜYÜT)
Her "test et → açık bul → kapat" turunu buraya yaz. İlk tur DDR SONRASI doldurulacak.

| Tur | Tarih | Test koşulu | Bulunan açık | Kapatma aksiyonu | Sonuç/kanıt |
|---|---|---|---|---|---|
| — | (DDR sonrası ilk tur burada başlayacak) | — | — | — | — |

---

## 8. HATIRLATMA
🔔 15 Temmuz 2026 ve sonrası için hatırlatma **kuruldu** (kullanıcı istedi). DDR teslim
edilince bu yol haritasına dönülecek. Hatırlatma tetiklenince: DDR durumu sor → teslim
edildiyse Faz 1'e geç (veri) → değilse önce DDR.

---

## 9. BAĞLANTILAR
- Metrik-odaklı v3 planı (0,60 geçme, hazır+push'lu): `00_PLAN_DURUM_DEVIR.md`.
- DDR ana durum: `doc/ddr/README_DDR.md` + [[ddr-raporu-15-temmuz]] hafızası.
- Bu operasyonun hafıza kaydı: [[model-guclendirme-v3]].
- Git kuralı (trs-1342, izsiz): [[git-kimlik-tercihi]].
- Kullanıcı temposu (yavaş/açıklayıcı, terimleri sözlüğe ekle): [[kullanici-ogrenme-tempo]].
