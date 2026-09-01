# ÖN KAYIT — P1: MAVLink katmanını CANLI koştur (plan v2)

**Tarih:** 2026-09-02 · **Yazan:** Claude 2 (Opus 5, amele) · **Ön kayıt D-107
gereği SONUÇ GÖRÜLMEDEN yazıldı.**

## 0. Neden

`comms/inis_kaniti.py` (BagilIrtifaOkuyucu + `yerde_mi`) ve `rpi_inference`
irtifa→mpp sağlayıcısı bugüne kadar **yalnız sahte nesnelerle** sınandı:
venv'de `pymavlink` kurulu bile değildi (2026-09-02 öncesi `find_spec` = None).
Bu, kabul zincirimizin sınıflandırmasıyla **`KOD_VAR != KOSUYOR`**: birim
testleri gerçek MAVLink çerçeve çözücüsünü hiç çalıştırmadı. Sahada Pixhawk'tan
gelen ilk paket, hiç koşmamış bir yolun ilk koşusu olurdu.

## 1. Bu ölçümün sorusu

> Üretim sınıfları (`BagilIrtifaOkuyucu`, `yerde_mi`, `IrtifadanMppSaglayici`)
> **gerçek pymavlink çerçevelerini** UDP üzerinden okuduğunda, birim
> testlerindeki sözleşmenin aynısını üretiyor mu?

Sahte nesne değil: gerçek `mavutil.mavlink_connection`, gerçek serileştirme,
gerçek CRC, gerçek `recv_match`.

## 2. Kapı ölçütleri (sonuç görülmeden yazıldı)

| # | senaryo | GEÇTİ ölçütü |
|---|---|---|
| G1 | Uçuş akışı (30 m sabit, sysid 1) | `irtifa_m()` 30,0 ± 0,05 m; `konum_derece()` gönderilen lat/lon'a 1e-6 derece içinde |
| G2 | irtifa→mpp | `IrtifadanMppSaglayici.kare_mpp()` canlı akıştan pozitif ve sonlu mpp; `mpp_irtifadan` ile birebir aynı |
| G3 | İniş kanıtı | Alçalan profil + ON_GROUND'da `yerde_mi(ardisik=3)` **True** |
| G4 | Havadayken iniş yok | IN_AIR akışında `yerde_mi` **False** (fail-closed) |
| G5 | Yabancı kaynak | Aynı porta sysid=99'dan gelen GLOBAL_POSITION_INT **kabul edilmez**: beklenen sysid'in değeri okunmaya devam eder, yabancının irtifası **asla** dönmez |
| G6 | Donuk saat (replay) | `time_boot_ms` ilerlemeyen tekrar paketleri **yaşı yenilemez**: tazelik penceresi dolunca `irtifa_m()` None |
| G7 | Bayatlık | Yayın durunca `tazelik_s` sonrası `irtifa_m()` None (kanıt: pencere içinde değer VAR, sonra None) |
| G8 | Genel kapı | `codes/test_rota_sentetik.py` 15/15 **ve** tam suit OK — pymavlink/pyserial kurulumu mevcut hiçbir kapıyı düşürmedi |

**Reddetme kuralı:** G1–G8'den herhangi biri düşerse P1 "bitti" sayılmaz;
sebep `REVIEW_LOG.md`'ye yazılır. Eşikler burada yazılıdır, sonuca göre
gevşetilmez.

## 3. Ortam değişikliği (mimar kararı #1)

`pymavlink 2.4.49`, `pyserial 3.5`, `fastcrc 0.3.6` kuruldu (2026-09-02).
Kurulum öncesi `pip freeze` yedeği: `results/ortam/pip_freeze_20260902_oncesi.txt`
(80 satır). Kuru koşu: hiçbir mevcut paket sürümü değişmedi (dry-run çıktısı
"Would install fastcrc-0.3.6 pymavlink-2.4.49 pyserial-3.5"); `cv2 5.0.0`,
`numpy 2.3.5`, `torch 2.11.0+cu128` dokunulmadı.

## 4. Not — bu ölçüm neyi KANITLAMAZ

Sahte Pixhawk gerçek uçuş kontrolcüsü **değildir**: gerçek Pixhawk'ın zamanlama
düzensizliği, paket kaybı, USB/telem kopması ve ArduPilot'un alan doldurma
alışkanlıkları burada yoktur. P1 "çerçeve çözme + sözleşme" katmanını kapatır;
**gerçek akış Faz B'de (5 Eylül) ölçülür.** `OLCULEMEDI != GECTI`.

---

## 5. SONUÇ (2026-09-02, ölçüm sonrası yazıldı)

| # | sonuç | kanıt |
|---|---|---|
| G1 | **GEÇTİ** | canlı akıştan irtifa 30,0 m (±0,05); konum (39.925533, 32.866287) 1e-6 içinde |
| G2 | **GEÇTİ** | `CanliOlcekSaglayici` canlı akıştan pozitif/sonlu mpp; `mpp_irtifadan` ile uyumlu |
| G3 | 🔴 **DÜŞTÜ** | Alçalan profilde `yerde_mi` **10 s son tarihe rağmen 0,002 s'de False** → **BULGU A** |
| G4 | **GEÇTİ** | IN_AIR akışında `yerde_mi` False (fail-closed doğru) |
| G5 (1) sızıntı yok | **GEÇTİ** | yabancı sysid'in 130 m'si **hiç** dönmedi |
| G5 (2) erişilebilirlik | 🔴 **DÜŞTÜ** | yabancı trafik altında **0/193 okuma** değer döndü (trafik yokken 193/193) → **BULGU B** |
| G6 | **GEÇTİ** | donuk `time_boot_ms` yaşı yenilemedi; pencere dolunca None |
| G7 | **GEÇTİ** | yayın durunca pencere sonrası None (önce değer VARdı) |
| G8 | **GEÇTİ** | genel kapı 15/15 · tam suit OK (aşağıda) |

**⚠ Ön kayıt gevşetilmedi.** G3 ve G5(2) yazıldığı haliyle **düştü** ve öyle
kaydedildi. Yerlerine gate koymadım: pozitif yol için ayrı bir ölçüt eklendi
(**G3b — ON_GROUND akışında `yerde_mi` True**, GEÇTİ, gerçek çerçevelerin
gerçek kanıt ürettiğini gösterir) ve iki düşüş `tests/test_p1_canli_mavlink.py`
içinde **karakterizasyon testi** olarak kilitlendi (`AcikBulgular`) — bunlar
"doğru davranış" iddiası değil, ölçülen davranışın sessizce değişmemesi içindir.

**P1 KAPANMADI.** İki bulgu mimar kararına bağlanmadan paket "bitti" sayılmaz
(plan v2: kapısız iş bitti sayılmaz). Ayrıntı ve seçenekler: `REVIEW_LOG.md`
**D-387**.
