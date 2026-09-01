# YAZILIM BİTİRME PLANI — 1 → 5 Eylül 2026

> **Emir (kullanıcı, 2026-09-01):** aviyonikler cumartesi (5 Eylül) geliyor;
> aviyonik olmadan yapılamayan kısımlar HARİÇ **tüm yazılım** cumartesiye
> biter. **Yazan: Claude 2 — bu plan için mimar yetkisiyle.**
> Dayanak: `results/sartname_bosluk/rapor.md` (26 Ağustos boşluk denetimi) +
> bugünkü envanter taraması. Her iş kapılıdır; kapısız iş "bitti" sayılmaz.

## 0. Görev akışı ↔ yazılım durumu (mimar haritası)

| adım | bileşen | durum |
|---|---|---|
| İHA kalkış→tarama→iniş uçuşu | Pixhawk görev planı | **AVİYONİK** (yazılımımız pasif) |
| Telemetri (irtifa→mpp, karar_yas) | `inis_kaniti.BagilIrtifaOkuyucu`, `rpi_inference` | kod+test var, **canlı akışla HİÇ koşmadı** (pymavlink kurulu değil) → **P1** |
| Algı→karar→telsiz | v36 + `analyze_path` + `KararYayinci` | ✅ kapılı (bugün: HB hedefli, p95 113 ms) |
| HB hedefi | ölçek+şekil kapılı `hb_konumu` | ✅ bugün bağlandı (zincir koşumu kapanıyor) |
| YKS hakem ekranı | `yks_gui` | ✅ kapılı (A2, K1, tatbikat F1–F6) |
| İHA iniş kanıtı → İKA kilidi | `iha_inis_yayinci`, §2.2.5 latch | kod+test ✅ · **Jetson başlatma yordamı yazılı değil** → **P4** |
| İKA_GO → İKA intikal → HB | `ika_receiver`, `ika_nav` | protokol ✅ · **gerçek sürücü katmanı YOK (T149)** → **P3** |
| SiK telsiz | `SerialLink` | kod var, **framing hiç sınanmadı** (pyserial yok) → **P2** |
| Saha video (H3) | DroidCam / `rpi_yayin` | kılavuz ✅ · algı hattına bağlama **T18** → **P6** (telefon yeter, aviyonik değil) |

## 1. İş paketleri (hepsi aviyonik-siz, hepsi kapılı)

**P1 · MAVLink katmanını CANLI koştur** — pymavlink kur (mimar kararı,
gerekçe kayıtlı); `sahte_pixhawk.py`: UDP'ye gerçek MAVLink çerçeveleri
(HEARTBEAT + GLOBAL_POSITION_INT + EXTENDED_SYS_STATE) basan üreteç.
Uçtan uca sınanır: irtifa→`mpp_irtifadan`→rota ölçeği · `karar_yas`
heartbeat'e · iniş kanıtı latch'i. Mock DEĞİL — gerçek pymavlink çözücüsü.
**Kapı:** yeni nöbetçi + kuru koşu `hedef_konumu/olcek` halkaları sahte
akışla GEÇTİ; saat-atlaması ve kaynak-kimliği senaryoları dahil.

**P2 · SerialLink'i radiosuz sına** — pyserial kur; `loop://` ile framing/
parçalanma/ACK turu. RF ölçümü CUMARTESİ (yazılım yolu bu hafta kapanır).
**Kapı:** SerialLink üzerinde mutlu_yol eşdeğeri mesaj turu + bozuk-bayt
enjeksiyonunda çerçeve kurtarma testi.

**P3 · T149 — İKA sürücü soyutlaması (KRİTİK)** — mimar tasarımı:
`ika_surucu.py` arayüzü (`hiz_ver(v,w)`, `konum_al()`, `durdur()`,
fail-closed: donanım cevap vermezse İKA DURUR); üç uygulama: `GazeboSurucu`
(mevcut `gz` yolu), `SahteSurucu` (test), `GercekSurucu` iskeleti (seri/PWM
— cumartesi doldurulur, o güne kadar `NotImplementedError` DEĞİL,
açık `DONANIM_YOK` reddi). `ika_nav` arayüzden konuşur.
**Kapı:** mevcut T141 zinciri Gazebo sürücüsüyle bayt-eş; SahteSurucu ile
şartname kilidi (§2.2.5) uçtan uca; "donanım sustu → İKA durdu" testi.

**P4 · Saha runbook'ları tazele** — `saha_gunu_kontrol_listesi.md` (bayat:
v35/v34 → v36), `iha_inis_yayinci` Jetson başlatma yordamı (boşluk raporu
madde 6), `saha_kuru_kosu` çıktısının bugünkü halkalarla hizası.
**Kapı:** T154-kalıbı belge kapısı — runbook'taki sürüm/komut satırları
registry'den doğrulanır.

**P5 · T79/T91/T92 — karar kararlılığı (mimar kararı: histerezis)** —
ön kayıt ÖNCE: N-kare histerezis (yayınlanan şerit ancak K ardışık karede
aynıysa değişir; NO_ROUTE fail-closed anında). `68_karar_kararliligi`
altyapısıyla ölçülür: çevrilme 14/260'ın kaça indiği + gecikme maliyeti
(tazelik penceresi 5 s'nin içinde kalmalı). Eşik sonuçtan önce yazılır.
**Kapı:** çevrilme ↓, p95 karar gecikmesi ≤ mevcut + K·kare-süresi belgeli;
tüm mevcut kapılar yeşil.

**P6 · T18 — DroidCam'i algı hattına bağla (H3)** — telefon yeter.
`--camera` kaynağı olarak DroidCam URL'i; `kamera_dogrula` + ayna testi
(D-349) telefonla koşulur. **Kapı:** canlı telefon görüntüsünde uçtan uca
karar + YKS'de görünüm; 10 dk kesintisiz akış.

**P7 · Kapanışlar** — T150 zincir verdikti (koşuyor) → D-386; T14/K9
TEKNOFEST cevabı gelirse kapı profili; FDR sayfası tazeleme.

## 2. Gün planı

| gün | işler |
|---|---|
| **Salı akşam** (bugün) | P7 (T150 kapanışı) · pymavlink/pyserial kurulum + duman testi · P1 başlangıç |
| **Çarşamba** | P1 tamam · P2 tamam · P4 |
| **Perşembe** | P3 (T149 sürücü katmanı) — günün tamamı |
| **Cuma** | P5 (karar kararlılığı) · P6 (DroidCam, seninle) · TAM PROVA: kuru koşu + mutlu_yol + bütün kapılar + Gün-1 son kontrol |
| **Cumartesi** | DONANIM: Gün-1 listesi (Jetson) + aviyonik entegrasyonu (gerçek MAVLink, SiK RF, İKA sürücüsü doldurma, uçuş kontrolcüsü görev planı) |

## 3. Cumartesiye BİLEREK bırakılanlar (aviyonik-bloklu)

Gerçek MAVLink/Pixhawk akışı · SiK 433 MHz RF ölçümü · `.engine` + Jetson
FPS (T16/T17) · İKA gerçek sürüş · uçuş kontrolcüsü görev planı/geofence/
failsafe (repo dışı, Pixhawk yapılandırması — **cumartesi insan+mimar**).

## 4. İnsan görevleri (senden)

- K3+K9 sorusunu TEKNOFEST'e ilet (metin hazır, dünkü mesajda).
- Cuma: telefon + DroidCam kurulumu (P6, yarım saat, benimle).
- DJI Neo çekim görevi (kuyruk R-görevi) — hâlâ açık, eğitim verisi için.
- Cumartesi: donanım günü (Gün-1 + aviyonik).

## 5. Mimar kararları (bu planla verildi, gerekçeli)

1. **pymavlink + pyserial kurulur** — saf-Python, cv2'ye dokunmaz; bu
   katman bunlarsız sınanamaz. Kurulum öncesi `pip freeze` yedeği alınır.
2. **İKA sürücü arayüzü** P3'teki imzayla sözleşmeye girer (fail-closed:
   cevap yoksa DUR).
3. **T79 histerezisle ele alınır** — ön kayıt şartıyla; eşik sonuç
   görülmeden yazılır.
4. Koridor kararlılığının T91/T92 alt soruları P5'in ölçümünden sonra
   yeniden değerlendirilir (ölçümsüz kural eklenmez).
