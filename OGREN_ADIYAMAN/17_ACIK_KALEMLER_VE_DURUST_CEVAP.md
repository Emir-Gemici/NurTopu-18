# 17 · AÇIK KALEMLER VE DÜRÜST CEVAP — "bilmiyoruz / ölçmedik" nasıl söylenir

> Bu dosya en kısa ama en önemli olanıdır. Projenin kültürü **ÖLÇÜLEMEDİ ≠ GEÇTİ**; jüri önünde de öyle. Bir soruya "evet çalışıyor" demek kolaydır; FDR'nin ve
> defterin **aksini yazdığı** bir şeyi "evet" demek, raporla çelişip güveni bitirir. Aşağıda (1) dürüst cevap kalıbı, (2) açık kalemlerin tam listesi, (3) "tuzak" sorular.
> Kaynaklar: `FDR/ACIK_KALEMLER.md`, `FDR/BOLUM_6` §6.5.1 (A1–A13), `BOLUM_4` §4.13, `TASK_QUEUE.md` açık `[ ]`, `JETSON_OTURUM_DURUMU_20260909.md`, D-431 K1–K11.

---

## 1. Dürüst cevap kalıbı (ezberle)

```
1. Ne ÖLÇTÜK  → sayı + çerçeve + tarih         ("sentetik kabul kümesinde, n=260, 1 Eylül: …")
2. Ne ÖLÇMEDİK → açıkça, gerekçesiyle           ("gerçek arena karesi yok; maket çekimi yapmadık")
3. Ne YAPTIK bu boşluğa karşı → tasarım kararı  ("fail-closed: emin değilsek rota yayınlamıyoruz, sebebini yazıyoruz")
4. Ne ZAMAN kapanacak → tarih varsa tarih, yoksa "tarih vermiyoruz" ("21 Eylül provasında; A2/A5… için tarih yazmadık")
```
Yasak kelimeler: "muhtemelen çalışır", "sorun olmaz", "test ettik" (koşulmadıysa), "sahada denedik" (uçuş yoksa). Doğru kelimeler: **ölçüldü / beyan / ölçülemedi / doğrulanamadı**.
Sayı verirken **tarih** söyle (süit 1896 → 2138 → 2204 gibi sayılar günden güne değişti). "Kanıtlanmamış olan tek şey en önemlisidir: gerçek arenada, gerçek Jetson'da,
gerçek telsizle çalıştığı" (FDR §4.15) — bunu jüri sormadan sen söyle.

## 2. Açık kalemler — tam liste (10 Eylül 2026)

### 2.1 FDR Bölüm 6 açık gereksinimleri (A1–A13)
| # | ne | durum | kapanma |
|---|---|---|---|
| A1 | gerçek İKA motor sürücüsü | donanım tedarik edilmedi; `GercekSurucu` arka uçsuz | final dalgası |
| A2 | gerçek SiK 433 hattı (RTT, kayıp, menzil) | hiç ölçülmedi; DDR ">%98, 300 m" kanıtsız | `sik_rf_olc.py --n 50`; tarih yok |
| A3 | gerçek otonom uçuş | hiç koşmadı; 6 Eyl uçuş reddedildi | ilk hover → Loiter/Auto → prova |
| A4 | gerçek arena karesi | yok; maket yapılmayacak | 21 Eyl provasında; **rapor tarihinde kapatılamaz** |
| A5 | 45–51 s kör aralıklar (model) | ölçüldü, kapanmadı; hız değil model sorunu | tarih yok |
| A6 | üç-güzergâh adayı + K2/K3 ihlal denetimi üretim yolunda yok | yazılım borcu | tarih yok |
| A7 | `mod` alanı üretim telemetrisinde (manuel moda alma tespiti) | yazılım borcu | tarih yok |
| A8 | tekrar fırlatma doğrudan testi | tek testlik iş | tarih yok |
| A9 | Gazebo fiziksel temas | gz yok | tarih yok |
| ~~A10~~ | ~~Jetson FPS~~ | **KAPANDI 6 Eyl** (D-431) | — |
| A11 | `--fda` kipinin bağımsız denetimi | aynı el yazdı ve onayladı | 21 Eyl öncesi provada hakem rolü |
| A12 | otonom paraşüt tetiği | ölçülmedi (FDA aracında paraşüt yok) | final |
| A13 | Pixhawk failsafe/döküm; RC failsafe **DÜŞTÜ** | üçüncü döküm bekleniyor | tarih yok |

### 2.2 Bölüm 4 kalan test borcu (18; 3'ü kapandı)
gerçek arena karesi · ~~Jetson FPS~~ · SiK menzil/kayıp · uçuş testleri 3.1–3.6 · ~~engine↔pt~~ (ölçüldü, DÜŞTÜ) · gerçek Pixhawk'ta `mavlink_dogrula` 3/3 · `jetson_baslat.sh --kapi` ·
gerçek İKA sürücü · geofence/döküm · K5 figür bilgi px · ~~Nano belgesi~~ · RC failsafe · ESC kalibrasyonu (6 Eyl beyan) · pusula (6 Eyl ×2) · accel teyidi · parametre dökümü ·
pil gerilimi ±0,1 V (6 Eyl ölçüldü) · motor sırası/yönü videosu. **Denetim borcu:** D-407, `jetson_baslat`, T207, `_kanit_yaz` — "yazan ile onaylayan aynı taraf".

### 2.3 Jetson tarafı (D-431 K1–K11; 9 Eyl durumu)
✅ K1 künye bantları (KILAVUZ başlığı hâlâ "Orin NX") · ⏳ **K2 T66 kabul kümesi Jetson'a getirilmeden nihai engine kararı yok** (uçuş `.pt`) · ✅ K3 · ✅ K4 · ✅ K5 · ❌ K6 post-process
darboğazı (mimar) · ◐ K7 · ❌ K8 onnxruntime-gpu sm_87 · ◐ K9 `wheels/` silme kararı Halil'in · ❌ **K10 süit Windows yolları** (Jetson'da 32 kırmızı) · ❌ **K11 ArduPlane parametre seti
ve provası yok** (final sabit kanat). Ek: **Gün-1 §4 doğruluk kapısı** (test_goruntuleri engine ↔ PC referans kararı) hiç ölçülemedi — PC'de v36 referans kararı dosyası yok.
Donanım: IMX477 CSI + ayna testi · Pixhawk `--kapi` · SiK `KIP=sik` ÖLÇÜLEMEDİ.

### 2.4 TASK_QUEUE açık kritikler
**T79** koridor seçimi binde-4 gürültüye kararsız (histerezis belirtiyi kapattı, kök Faz C) · **T199** üretece arena profili (yeni gerçek veri gerek) · **T47** v21 "geçilebilir" bu
alanda anlamsız (veri-bloklu) · **T149** İKA sürücüsü (insan+mimar) · **T211** motor künyesi + itki bütçesi (insan: etiket, veri sayfası, tartı) · T14 FDA 20×20 parametrizasyonu ·
S6 hedef sınıfı tohum olarak bağlı değil · T88 arena sınırı · T91/T92 kararsızlık · T204/T205/T208 küçük borçlar.

### 2.5 Saha / donanım (5–7 Eyl)
RC failsafe düzeltmesi ve tekrar testi · `RC6_OPTION` (kumandadan arm) · `FLTMODE6` Land ↔ FDR "RTL" beyanı · mimar kararı RTL/Land · `BATT_CAPACITY` 3300 ↔ 10 Ah · bilinçsiz değişen
`FS_THR_ENABLE`/`BATT_FS_LOW_ACT` · motor M1 hasarlı · devrilme kök nedeni (itki asimetrisi / CG-geometri) · kütle/CG tartısı · hover akımı · kamera FOV · ESC BEC telleri · 3 kırmızı tel ·
üçüncü parametre dökümü · mühür (17 Eyl) · Adıyaman koordinatları/alan izni · R2/R5 için ikinci kişi.

### 2.6 FDR belge boşlukları
3.1 uçuş bilimleri (7 YOK) · 3.2 yapısal (48 YOK; İKA/mancınık BOM yok; FEM sonucu okunamıyor) · 3.3.2 kablaj/güç hesabı · 3.3.3 3B simülasyon + video · Bölüm 5 hata prosedürleri
ve **kol reçete farkı gerekçesi** · Bölüm 7 fiyatlar · KYS künye teyidi · ÖDR/DDR REQ eşlemesi · Bölüm 1 yeniden üretimi · 7 bayat paragraf (6 Eyl sonrası).

## 3. Tuzak sorular ve dürüst cevaplar

**"Sisteminiz sahada çalışıyor mu?"** — "Yazılım zinciri yerde bütünleşik koşuyor ve kapılardan geçiyor; Jetson'da gerçek kare hızını ölçtük. Ama gerçek arenada, gerçek
telsizle, uçuşta henüz ölçmedik; ilk otonom uçuş provası önümüzdeki hafta. Raporumuz bunu 'ölçülemedi' olarak yazar, 'çalışır' demez."

**"Doğruluğunuz yüzde kaç?"** — "Hangi çerçevede? Sentetik kabul kümesinde yayınlanan şerit doğruluğu yüzde 98,8; gerçek kırsal doğrulama karelerinde rota üretimi 29 karede 8,
yanlış güzergâh sıfır. Bu iki sayı aynı şey değil ve arası tahmin edilmez. Gerçek arena karemiz yok."

**"Üretim modeliniz kendi kapınızı geçmedi mi?"** — "Evet, iki eşiği geçmedi. Onu yine de seçtik çünkü yanlış güzergâh oranını yüzde 71'den 18'e düşürdü ve şartnamede
yanlış güzergâh sıfır puan. Kararı insan verdi, istisnayı sözleşmeye adıyla yazdık, eşikleri değiştirmedik, önceki modeli yedek tuttuk."

**"Failsafe'leri test ettiniz mi?"** — "Parametreler yazılı ve testle kilitli. Sahada RC failsafe'i denedik ve **düştü**: alıcı son değerleri tutuyor. Düzeltme kumandada;
test geçmeden pervane takmıyoruz. RTL, geofence, pil failsafe henüz uçuşta tetiklenmedi."

**"İKA nerede?"** — "Yazılımı hazır ve kilitli; donanımı henüz alınmadı. Görev test uçuşunda İKA yok; final için açık kalem. Sürücü arayüzü arka uç olmadan kurulmayı reddeder,
'hazır' numarası yapmaz."

**"Haberleşme menziliniz?"** — "Gerçek 433 MHz hattı hiç ölçülmedi; ölçüm aracı yazıldı, iki telsiz kutudan çıktı ama RTT/kayıp henüz koşulmadı. Loopback'te uçtan uca p95 113 ms."

**"Neden TensorRT değil PyTorch?"** — "Engine'i derledik, hızlı, ama karar denkliği eşiğimizi geçemedi; aynı karede farklı şerit söyleme riskini hıza tercih etmeyiz. Nihai karar
kabul kümesiyle yapılacak, o küme henüz Jetson'da değil."

**"Simülasyon videonuz?"** — "Yok. Gazebo iskeleti var, CAD yok, koşum yok. Rapora 'ölçülemedi' yazdık."

**"Bütçe?"** — "Depoda parasal kayıt yok; BOM'da kalem ve tedarik durumu var, fiyat sütunları beyan bekliyor."

**"Kol baskı reçeteleri neden farklı?"** — "Fark var, gerekçesi kayıtta yok; bunu SGGS riski olarak kendimiz işaretledik."

**"6 Eylül'de neden uçmadınız?"** — "Kapılar geçmedi: RC failsafe düştü, ESC kalibrasyonu ve pusula gündüz tamamlanmamıştı, alacakaranlıktı. Üç kez istendi, reddedildi. Sonra
pervaneli üç devrilme oldu; uçuş logundan analiz ettik: kontrolcü doğru tepki vermiş, ön itki yetmemiş, bir motor hasarlı."

**"Yapay zekâ mı yazdı bu kodu?"** — "Büyük ölçüde evet, yazılı bir düzen altında: mimar kod yazmaz, denetler; yazan onaylayamaz; her kapı gerçekten koşulur; bağımsız çürütücü
turları. Aynı modelin iki örneğinin anlaşmasını kanıt saymıyoruz; hakem ölçüm."

---

## Jüriye 30 saniyede

> "Neyi bilmediğimizi biliyoruz ve yazdık: gerçek arena karesi yok, gerçek telsiz ölçülmedi, otonom uçuş henüz yapılmadı, İKA donanımı alınmadı,
> RC failsafe testte düştü. Bunların hiçbirini 'sorun çıkmadı' diye kapatmadık. Tasarımımız bu belirsizliğe karşı fail-closed: emin değilsek
> rota yayınlamayız ve sebebini hakem ekranına yazarız."

## Kendini sına
1. Dürüst cevabın dört adımı? 2. Yasak üç kelime, doğru dört kelime? 3. A1–A13'ten üçünü sebebiyle say. 4. K2 ve K10 nedir? 5. "Doğruluk yüzde kaç" sorusuna nasıl başlarsın?
6. RC failsafe sorusuna cevap? 7. Bölüm 5'teki riski jüri sormadan söyler misin? 8. Süit sayısı verirken neye dikkat? 9. "Sahada çalışıyor mu" cevabının ilk cümlesi? 10. FDR §4.15'in cümlesi?

<details><summary>Cevaplar</summary>
1. Ne ölçtük (sayı+çerçeve+tarih) · ne ölçmedik · ne yaptık · ne zaman. 2. "muhtemelen çalışır / sorun olmaz / test ettik (koşulmadıysa)"; ölçüldü / beyan / ölçülemedi / doğrulanamadı. 3. Örn. A1 İKA sürücüsü (donanım yok), A2 SiK (hiç ölçülmedi), A4 gerçek arena karesi (maket yok). 4. K2: T66 kabul kümesi Jetson'a gelmeden engine kararı yok; K10: testlerdeki Windows yolları Jetson'da 32 kırmızı. 5. "Hangi çerçevede?" — sentetik %98,8 vs gerçek kırsal 8/29, arası tahmin edilmez. 6. Parametre kilitli; sahada RC failsafe denendi ve düştü; düzeltme kumandada; test geçmeden pervane yok. 7. Evet: kol reçete farkı gerekçesiz, SGGS riski, kendimiz işaretledik. 8. Tarih söyle (1896 → 2138 → 2204). 9. "Yazılım zinciri yerde bütünleşik koşuyor ve kapılardan geçiyor; ama gerçek arenada/telsizle/uçuşta henüz ölçmedik." 10. "Kanıtlanmamış olan tek şey en önemlisidir: gerçek arenada, gerçek Jetson üzerinde, gerçek telsizle çalıştığı."
</details>
