# NAVITAS — 19 Eylül 2026 akşamı bilgilendirme (Halil & Emir için)

> Dal: `bilgilendirme-he`. Taban: `tunel-saha-20260918` (eb6a0c20) — sahada YKİ'nin çalıştığı kod.
> Yazan: mimar oturumu, 19 Eyl ~21:30. Kanıtların hepsi repoda; her maddenin yanında dosyası var.
> Kanıt defteri: `REVIEW_LOG.md` içinde **D-505 … D-516** (bugünün kayıtları, dosyanın sonu).

## Tek paragrafta durum

Telsiz uçtan uca **çalışıyor**. İHA'nın kararları, GPS koordinatı ve rotası telsizle YKİ'ye
geliyor. Hakemin onayı (ACK) telsizle Jetson'a geri gidiyor. Hepsi ethernetsiz ölçüldü.
K8 hız kapısı (p95 < 200 ms) **geçmedi**: 212 ms ve 278 ms ölçüldü. Sistem çalışıyor ama
kapı sayısı tutmuyor; eşik gevşetilmedi. Bu akşam YKİ'de hakem onayının kendiliğinden
silinmesine yol açan ciddi bir hata bulundu ve düzeltildi. Düzeltme yalnız bu dalda var;
YKİ'yi bu dalın kodundan açın. Jetson tarafındaki telemetri düzeltmesi hazır ve denetlendi.
Jetson kapalı olduğu için henüz **kurulmadı**; tek komutla kurulur (bkz. 03).

## Ne tamam, ne eksik (sade)

| Konu | Durum | Nerede |
|---|---|---|
| Telsiz: Jetson → YKİ veri akışı | ✅ çalışıyor (ethernetsiz) | 01 |
| Telsiz: YKİ → Jetson onay (ACK) | ✅ 0,22 s'de ulaştı | 01, 02 |
| GPS koordinatı telsizden YKİ'ye | ✅ dış mekânda görüldü | 01 |
| Gerçek boyda rota (4 parça) telsizle | ✅ ilk gönderimde, 0,40 s | 01 |
| Telsiz USB'si çıkıp takılınca | ✅ 8 s'de kendiliğinden geri bağlanıyor (yeni kod) | 01 |
| K8 hız kapısı (p95 < 200 ms) | ❌ 212 / 278 ms — DÜŞTÜ | 01 |
| Video telemetri (uçuşta) | ❌ yok — telsiz taşıyamaz, Jetson'da Wi-Fi yok | 01 |
| Hakem onayı yeni seq'le silinmesi | ✅ düzeltildi (YKİ, bu dal) — canlı telsiz testi YAPILMADI | 02 |
| Tek NO_ROUTE karesi onayı silmesi | ✅ düzeltildi ("ONAY ASKIDA") | 02 |
| Saçma telemetri (0/0 konum, 890 m irtifa) | ✅ YKİ'de gizleniyor; Jetson düzeltmesi kurulmayı bekliyor | 02, 03 |
| Kamera kablosu ters pin | ✅ düzeltildi; kamera kopunca servis artık çökmüyor | 03 |
| Jetson kendiliğinden kapanma | ⚠ 2 kez, güç kesintisi imzası (yazılım değil) — konnektör şüphesi | 03 |
| Harici pusula (M9N) | ⚠ aralıklı — kablo; uçuş öncesi "MAG0" kontrolü şart | 04 |
| 14:18 düşüşü | ✅ sebep sol ön pervane somunu (beyan), giderildi | 06 |
| Kamera 90° dönük montaj | ⚠ kod değişmeden çözülür: uçuşta burun yönü / montaj açısı | 05 |
| Uçuş öncesi kontrol listesi | 📋 | 08 |

## Yarın sabah sıra (özet — ayrıntı 08'de)

1. Jetson'ı aç, ethernet tak, c9ee27f0 kurulumunu koş (03 §Kurulum). 2 dk.
2. Kamera yönü ok testi (05). Montaj açısını (+90 / −90) belirle, görev/pilot kuralına yaz.
3. Pixhawk açılışında Mesajlar'da **"MAG0 initial yaw alignment complete"** gör (04).
4. YKİ'yi **bu daldan** aç (02 §Açılış). Eski açık YKİ penceresi eski kodu taşır.
5. Canlı onay testi: Jetson her saniye yeni seq yollarken hakem iki adımı basar, onay kalıcı mı (02 §Açık test).
6. Pervane somunları (dört köşe) elle kontrol (06).

## Dosya haritası

| Dosya | İçerik |
|---|---|
| `01_TELSIZ_VE_K8.md` | telsiz zinciri, ölçümler, K8 hükmü, arıza okuma |
| `02_YKI_VE_HAKEM_ONAYI.md` | YKİ açılışı, iki adımlı onay, bu akşamki düzeltmeler |
| `03_JETSON.md` | servisler, kurulu dosyalar, bekleyen kurulum, kara kutu, kapanmalar |
| `04_PIXHAWK_PUSULA_PARAMETRE.md` | 3115 parametre dosyası, yazılan ayarlar, pusula, GCS failsafe |
| `05_KAMERA_YONU.md` | 90° montajın yazılıma etkisi, ok testi, montaj açısı kuralı |
| `06_UCUS_LOGLARI_19EYL.md` | 12:59 kayma ve 14:18 düşüş analizi |
| `07_ACIK_ISLER_RISKLER_DALLAR.md` | açık işler, riskler, git dal haritası |
| `08_UCUS_ONCESI_KONTROL.md` | sahada adım adım kontrol listesi |

## Bu dala giren dosyalar

- Bugünün ölçüm klasörleri: `results/telsiz_20260919/` (telsiz, K8, provalar, betikler),
  `results/jetson_20260919/` (manifest, kara kutu, kurulum dosyaları),
  `results/ucus_20260919/` (iki .bin log + analiz), `results/ucus_20260917*/`, `results/ucus_20260918/`
  (eksik kalan .bin/.tlog'lar), `results/saha_20260918/` (parametre dökümü).
- `config/pixhawk/3115_baslangic_20260919.param` (3115 motor başlangıç ayarı).
- `tools/yki_paket/` (YKİ .exe paketleyici).
- `scripts/tezgah/sik_ayar.py`, `telsiz_rtt_param.py` — Halil'in origin/master'daki dosyalarıyla **bire bir aynı** (birleştirmede çakışmaz).
- `REVIEW_LOG.md` → D-505 … D-516 eklendi.
- `tests/test_yks_gui_uretim_hizasi.py` → tek satır: görünüm listesine "rota" eklendi
  (YKİ'de "rota" görünümü 14 Eyl'den beri var, test beklentisi geride kalmıştı).

**Bilerek GİRMEYENLER:** ana klasördeki FDR/sunum/CAD dosyaları (14 Eyl işleri, ~30 000 dosya),
`.docx/.pptx/.zip`, Gemini görselleri, `dronesolid/`. Hepsi diskte duruyor, hiçbiri silinmedi.
Parola hiçbir dosyada yok (tarandı); Jetson betikleri parolayı `NAVITAS_SIFRE` ortam değişkeninden okur.
