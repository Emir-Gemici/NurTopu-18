# BÖLÜM 2 — Organizasyonel Yapı ve Proje Takvimi (5 puan)

> **Takım:** Navitas Autonomous Systems · **Takım ID:** 997827 · **Başvuru no:** 5329027
> *(Kaynak: `navitas-teknofest/references/ddr_requirements.md` — DDR döneminde yazıldı.
> **DOĞRULANACAK:** KYS kaydıyla teyit edilmeden bu üç alan rapora nihai sayılmaz.)*
>
> **Bu bölümün yazım kuralı.** Aşağıdaki her tarih ve her sayı bir artefakttan gelir;
> satırın sonunda hangi dosyadan ve hangi komutla çıkarıldığı yazılıdır (§7 Kanıt dizini).
> Ölçülmemiş bir şey "ölçülemedi" diye yazılır, tahmin edilmez. Geçmeyen bir kapı
> "geçmedi" diye yazılır (§4.4). Henüz atanmamış insan görevleri **BEYAN GEREKLİ (insan)**
> etiketiyle boş bırakılmıştır; doldurulmadan bu bölüm tamamlanmış sayılmaz.

---

## 1. İki ayrı sistem — organizasyon ve takvim bu ayrım üzerine kurulur

Şartname bu yarışmada takımdan **iki farklı fiziksel araçla** iş ister ve bunlar aynı araç değildir.
Rapordaki her takvim satırı hangi araca ait olduğu belirtilerek yazılmıştır.

| | **FDA görev test uçuşu aracı** | **Yarışma (final) aracı** |
|---|---|---|
| Şartname dayanağı | §5.3.2 — *"çoklu rotorlu ve dikey iniş-kalkış yapabilen bir insansız hava aracı (Drone)"* | §6 — *"sabit kanatlı insansız hava aracı (İHA) konfigürasyonunda olması zorunludur"* |
| Konfigürasyon | Quadcopter, 3B baskı gövde | Sabit kanat + mancınık fırlatma + paraşütle iniş + İKA |
| Görev | 20×20 m simüle alanda ≥ 30 m irtifadan açık güzergâh tespiti, YKS'ye canlı aktarım, ≤ 10 dk | Tam görev zinciri (fırlatma → tespit → aktarım → paraşüt → İKA → hedef bölge) |
| Bu raporda durumu | Gövde basıldı ve monte edildi; aviyonik montajı **5 Eylül 2026**'da yapılacak | **Üretilmedi.** Tasarım DDR'de sunuldu; üretim dalgası 21 Eylül sonrası (bkz. Bölüm 5 §11) |
| Ağırlık limiti | — (§5.3.2 limit koymuyor) | İHA ≤ 25 kg (yükler dâhil), İKA ≤ 10 kg (yük hariç) — §6 |

⚠ **Bu ayrım raporun her yerinde korunur.** FDA uçuşunda paraşüt ve İKA **yoktur**; yer kontrol
istasyonu yazılımı bunun için ayrı bir görev kipiyle (`--fda`) çalıştırılır ve o kipte paraşüt
ile İKA düğmeleri fiilen kapalıdır (sözleşme: `CONTRACTS.md` §6.7, karar kaydı `REVIEW_LOG.md`
D-408, 2026-09-02).

---

## 2. Organizasyonel yapı

### 2.1 Rol tanımları ve sorumluluk sınırları

Şartname §4, takımın **kaptan dâhil en az 6, en fazla 10 kişiden** oluşmasını zorunlu kılar.
Aşağıdaki yapı **rol** üzerinden tanımlıdır; bir kişi birden çok rolü üstlenebilir, ancak
**kanıt üreten rol ile o kanıtı onaylayan rol aynı kişi olamaz** (bağımsızlık kuralı, §2.3).

| # | Rol | Sorumluluk | Yetkisi olan kararlar | Ürettiği kanıt |
|---|---|---|---|---|
| R1 | **Takım Kaptanı** | Görev günü tutanağı, saha kararları, kişi ataması, alışveriş/tedarik onayı | "Takım Hazır" ilanı; uçuş/uçmama kararı; koordinat girişi onayı | Saha tutanağı, karar kaydı |
| R2 | **Pilot** | RC kumanda, arm/disarm ön kontrolü, manuel kurtarma (yalnız emniyet) | Uçuşu kesme; mod anahtarı kullanımı | Uçuş logu (`.bin`), hover/loiter kayıtları |
| R3 | **Aviyonik sorumlusu** | Pixhawk 6C + güç dağıtımı + kablolama + kalibrasyon; failsafe/geofence | Parametre yükleme; kablo hattı kabulü | `config/pixhawk/arducopter_fda_20260905.param` (sahada alınacak döküm) |
| R4 | **Görev bilgisayarı / kamera** | Jetson Nano 4GB kurulumu, kamera köprüsü, FPS kapısı, model yükleme | Sürüm/paket kurulumu; kamera kaynağı seçimi | `jetson_fps.py` çıktısı, `jetson_baslat.sh --kapi` çıktısı |
| R5 | **YKS operatörü** | Yer kontrol istasyonu, hakem ekranı, aktarım/ACK, kronometreler | Ekran düzeni; ACK'siz onayı reddetme | `hakem_log`, YKS ekran kaydı |
| R6 | **İKA sorumlusu** | İKA hattı (final dalgası); sürücü entegrasyonu, yük ve temas | İKA sürücü seçimi (donanım kararı) | `scripts/ika_surucu_kabul.py` kabul turu çıktısı |
| R7 | **Yazılım / görüntü işleme** | Algı zinciri, rota kararı, sözleşmeler, testler | Kod değişikliği (mühre kadar); eşik **değiştirme yetkisi YOKTUR** | `tests/` suit çıktısı, `REVIEW_LOG.md` D-kayıtları |
| R8 | **Kanıt-kalite (denetim)** | Bağımsız çürütme turu; ön kayıt tutma; kapı denetimi | Bulguyu deftere yazma; kapıyı geçersiz sayma | `REVIEW_LOG.md` çürütücü kayıtları |

**BEYAN GEREKLİ (insan): rol → isim ataması.** Bu tablo bilerek isimsizdir. Kaptan, sekiz rolü
takım üyelerine atayacak; atama tablosu (ad-soyad, öğrenim düzeyi, rol, yedek rol) rapora
buradan eklenecektir.
**BEYAN GEREKLİ (insan): şartname §4 kontenjan ve oran kontrolü** — toplam üye sayısının 6–10
aralığında olduğu ve lisansüstü üye oranının şartname sınırını aşmadığı beyan edilecektir.
**BEYAN GEREKLİ (insan): danışman öğretim üyesi bilgisi.**

Bugün itibarıyla atanmış tek rol kullanıcı beyanıyla **R2 Pilot**'tur
(`SAHA_HAZIRLIK_PLANI_20260903.md` §3: *"pilot: kullanıcı"*).

### 2.2 Saha günü rol dağılımı (5 Eylül montaj günü ve 21 Eylül uçuş günü)

| an | R1 Kaptan | R2 Pilot | R3 Aviyonik | R4 Jetson/kamera | R5 YKS |
|---|---|---|---|---|---|
| Kutu/envanter | tutanak, eksik listesi | — | tartı + fotoğraf | — | — |
| Mekanik + kablolama | denetim | yapılandırmada | **yürütür** | kamera/Jetson yerleşimi | — |
| Pixhawk yapılandırma | tutanak | radyo kalibrasyonu | **yürütür** | — | HEARTBEAT teyidi |
| Jetson kurulumu | — | — | UART hattı | **yürütür** | — |
| Yer zinciri | kronometre | — | — | uçlar | **yürütür** |
| Uçuş | "Takım Hazır" | kumanda | pil/CG | canlı izleme | hakem ekranı |

Kaynak: `SAHA_HAZIRLIK_PLANI_20260903.md` §2 (montaj günü tablosu) ve §6 (21 Eylül akışı).

### 2.3 Karar ve kanıt yordamı (organizasyonun asıl omurgası)

Bu projenin organizasyonu, kim ne yapar tablosundan ibaret değildir; **bir işin bittiğine kimin,
neye bakarak karar verdiğini** de tanımlar. Dört kural bağlayıcıdır:

1. **Ön kayıt.** Bir ölçümün eşiği, sonuç görülmeden yazılır ve sonradan gevşetilmez
   (`REVIEW_LOG.md` D-107). Bu kural somut iş görmüştür: 2026-09-01'de umut verici bir ara
   sonuç, önceden yazılmış bir RED kuralıyla karşılaşıp reddedilmiştir (D-377).
2. **ÖLÇÜLEMEDİ ≠ GEÇTİ.** Ölçülemeyen şey geçmiş sayılmaz; paydası olmayan oran rapora girmez.
3. **Bağımsızlık.** Bir iş, onu yapanın onayıyla kapanmaz. Kod yazan rol kendi kodunun kapısını
   onaylayamaz; ayrı bir çürütme turu koşulur (`AGENTS.md` §8; uygulanmış örnekler: D-405, D-407).
4. **Kanıt silinmez.** Yanlış çıkan iddia defterden çıkarılmaz; üstü çizilip düzeltmesine işaret
   verilir (D-373). Bu bölümdeki §4.4 bu kuralın uygulanmasıdır.

Kanıt defteri: `REVIEW_LOG.md` — bugün itibarıyla **414 kayıt başlığı / 408 benzersiz kayıt no**
(ölçüm: `grep -cE "^### D-[0-9]+" REVIEW_LOG.md` → 414; `... | sort -u | wc -l` → 408; 2026-09-03).

---

## 3. Gerçekleşen proje takvimi (depo geçmişinden ölçüldü)

Aşağıdaki tablo tahmin değildir: `O:\navitas` git deposunun tamamı taranarak
`git log --date=short --pretty=format:"%ad|%h|%s"` ile çıkarılmıştır. Depoda **545 commit**
vardır; ilk commit **2026-05-06** (`17258f8`, "start project").

### 3.1 Faaliyet yoğunluğu — gün başına commit (ölçüm, 2026-09-03)

| ay | commit'li gün | toplam commit | en yoğun gün |
|---|---|---|---|
| Mayıs 2026 | 3 | 4 | 07.05 (2) |
| Haziran 2026 | 2 | 4 | 24.06 (3) |
| Temmuz 2026 | 5 | 27 | 11.07 (16) |
| Ağustos 2026 | 22 | 396 | 26.08 (**89**) |
| Eylül 2026 (1–2) | 2 | 93 | 02.09 (**72**) |

Ölçüm komutu: `git log --date=short --pretty=format:"%ad|%s" | awk -F'|' '{print $1}' | sort | uniq -c`.
Yorum: proje ağırlığı Ağustos'ta yoğunlaşmıştır; bu, DDR sonrası (29.07) açılan doğrulama
borçlarının kapatıldığı dönemdir ve §4'teki revizyonların çoğu bu pencerede alınmıştır.

### 3.2 Kilometre taşları

| tarih | kilometre taşı | kanıt |
|---|---|---|
| 2026-05-06 | Depo açıldı | `17258f8` "start project" |
| 2026-06-24 | **Model v2** — RescueNet + FloodNet, 100 epoch (Colab) | `594e1b0` |
| 2026-07-11 | Haberleşme çekirdeği: İHA→İKA/YKS açık yol aktarımı (UDP/seri, ACK+seq, heartbeat failsafe) | `d2227ef` |
| 2026-07-11 | Dürüst simülasyon zinciri (tarama → ortomozaik → model → rota → İKA) + hakem logu | `516041b` |
| 2026-07-12 | **Model v3** (yolov8s-seg): mask mAP50 **0,627**; `blocked` 0,322 → 0,403 | `4b386ce`, `results/v3_test_20260712` |
| **2026-07-15** | **DDR son teslim tarihi (şartname)** | şartname s.11 takvim tablosu |
| 2026-07-15 | Model v4 (imgsz 512 → 640; v3 reçetesi birebir) | git log 15.07 |
| **2026-07-29** | **DDR sonuçlarının açıklanması (şartname)** | şartname s.11 |
| 2026-08-05 | Jetson saha paketi ilk hâli; v17 / v20 paket modelleri | `jetson_paket/models/` dosya damgaları |
| 2026-08-13 → 08-19 | v24 → v27 → v30 → v34 model dizisi; kabul kapıları K0–K6 kuruldu | `jetson_paket/models/`, `REVIEW_LOG.md` |
| 2026-08-16 | 🔴 **Kusur ölçüldü:** `seed` eğitimi hiç etkilemiyor — v31, v30'un bit-bit aynısı (D-138); **6,4 saat GPU** karşılıksız harcandı | `REVIEW_LOG.md` D-138, D-252 |
| 2026-08-19 | Saha paketi kayıt defterini taşıyor — kılavuza göre kurulan Jetson model yükleyebiliyor (D-178/D-179) | `results/`, T103 |
| 2026-08-21 | **Model v35** üretime alındı | `jetson_paket/models/navitas_seg_v35_best.pt` |
| **2026-08-26** | **Model v36 üretime alındı — ön kayıtlı iki eşik GEÇİLMEDEN** (§4.4) | D-293, D-294, `results/fdr/GORUNTU_ISLEME_KANIT.md` §3 |
| 2026-08-26 | Üretim karar yolu ilan edildi: `analyze_path` **üretim**, `rota_bul` **tanısal** (D-295, `CONTRACTS.md` §11.2-EK) | D-295 |
| 2026-08-27 | K7 (yayınlanan şerit doğruluğu) kabul zincirine bağlandı; v36 bozulmadan geçti | D-316 |
| 2026-08-28 | **v37 denendi ve GERİ ALINDI**: kabul zinciri geçti, gerçek arena karesi reddetti | D-332 |
| 2026-08-28 | v8 adayı: 124 epoch / **6,19 saat** eğitim → kabul zinciri **RED**; v36 üretimde kaldı | D-331 |
| 2026-09-01 | FDR görüntü işleme kanıt paketi artefakttan üretilir hâle geldi (elle sayı yazımı kaldırıldı) | `scripts/olcum/167_fdr_kanit_paketi.py` |
| 2026-09-01 | Uçtan uca kare gecikmesi ölçüldü: p95 **0,113 s** (D-382/D-383) | `results/fdr/GORUNTU_ISLEME_KANIT.md` §4.1b |
| 2026-09-02 | Faz B araç seti: `iha_komut_alici`, `mavlink_dogrula`, `sik_rf_olc`, `ika_surucu_kabul` | D-403 |
| 2026-09-02 | **MAVLink çoğullayıcı zorunlu kılındı** — seri port tek sahipli, üç tüketici (`CONTRACTS.md` §7.4) | D-403, `FAZ_B_GUN_PLANI.md` §1 |
| 2026-09-02 | Jetson tek komutla kalkar (`jetson_baslat.sh` + 6 systemd birimi); sürüm dondurma mührü | D-404, D-405 |
| 2026-09-02 | Tam test suiti **1827 test** ile kapandı | D-407 §3, `REVIEW_LOG.md`:28298 |
| 2026-09-03 | Cuma öncesi kapı koşumu: genel kapı **15/15 · 15/15**, tam suit **1875 test OK** (skipped 3), kuru koşu **9 GEÇTİ / 1 SAHİPSİZ** (yalnız `motor`) | `results/faz_b_oncesi/cuma_kontrol/cuma_kontrol.txt` |
| 2026-09-03 | Saha belleği üretildi: **404 dosya · 1,27 GB** (`MANIFEST.txt` sha256 + git HEAD) | `scripts/bellek_hazirla.py`, `results/faz_b_oncesi/CUMA_KONTROL_KARTI.md` §A |
| 2026-09-02 | **YKS FDA görev kipi** (`--fda`) — 21 Eylül'de hakem onayını imkânsız kılan kilit kaldırıldı | D-408, `CONTRACTS.md` §6.7 |
| 2026-09-03 | Jetson **Nano 4GB** yığını (14/14 aarch64 çevrimdışı tekerlek), kamera köprüsü, ArduCopter parametre + görev şablonu | D-406, D-407 |

### 3.3 Model sürüm soyağacı (üretim hattı)

| sürüm | paket dosyası damgası | durum | not |
|---|---|---|---|
| v2 | 2026-06-24 (git) | tarihsel | ilk Colab eğitimi |
| v3 / v4 | 2026-07-12 / 07-15 (git) | tarihsel | mask mAP50 0,627 (v3) |
| v17, v20 | 2026-08-05 | tarihsel | saha paketinin ilk modelleri |
| v21 | 2026-08-05 | tarihsel | — |
| v24 | 2026-08-13 | tarihsel | zemin kapısı eşiklerinin kalibre edildiği sürüm (D-283) |
| v27, v30 | 2026-08-14 / 08-15 | tarihsel | v31, v30'un bit-bit kopyası çıktı (D-138) |
| v34 | 2026-08-19 | **yedek aday** | tam sha `config/model_registry.json` `_yedek_surumler` |
| v35 | 2026-08-21 | **yedek aday** | v36'dan farklı hata yapar: arena K3/K4/K6'da daha iyi |
| **v36** | **2026-08-26** | **ÜRETİM** | `navitas-seg-v36-512`, sha256 `1d1caca6…c46911` |
| v37 | 2026-08-28 | **geri alındı** | gerçek arena karesi reddetti (D-332) |
| v8 (gece_v8) | 2026-08-28 | **reddedildi** | kabul zinciri RED (D-331) |

⚠ **DOĞRULANACAK:** v17–v36 satırlarındaki damgalar `jetson_paket/models/` içindeki dosya
değiştirme zamanlarıdır; bunlar **saha paketine kopyalanma** anıdır, eğitimin bittiği an değildir.
Eğitim bitiş zamanları eğitim koşum klasörlerinden ayrıca çıkarılmalıdır.

---

## 4. Revizyonlar — ÖDR → DDR → FDR

Şartname §5.3.1: *"Süreç boyunca meydana gelen bütün revizyonlar FDR kapsamında sunulmalıdır."*
Bu bölüm o hükmün karşılığıdır. Revizyonlar gizlenmemiş, gerekçeleriyle listelenmiştir.

### 4.1 Donanım revizyonları — DDR BOM'u ile bugünkü gerçek künye

DDR aviyonik BOM'u `navitas-teknofest/references/ddr_requirements.md` içindedir (27 kalem,
beyan edilen toplam **2293 g**). Bugünkü gerçek künye kullanıcı beyanıdır
(`SAHA_HAZIRLIK_PLANI_20260903.md` §0.2, 3 Eylül 2026).

| kalem | DDR BOM (15.07.2026) | **FDR — gerçek (03.09.2026)** | revizyon gerekçesi |
|---|---|---|---|
| Uçuş kontrolcüsü | Pixhawk 6C (BOM) / **Pixhawk 6X** (DDR mimari şeması) | **Pixhawk 6C** + PM02 güç modülü | DDR'nin iki belgesi çelişiyordu (BOM 6C, `avionics_software.md` şeması 6X); gerçek donanım **6C**'dir, çelişki bu raporla kapanır |
| Görev bilgisayarı | Jetson **Orin NX** + carrier + soğutucu (180 g) | **Jetson Nano 4GB** (JetPack 4.6.x, sistem Python 3.6) | Tedarik. Sonucu ağırdır: `ultralytics` Py ≥ 3.8 ister → Nano'da ayrı Python 3.8 venv + çevrimdışı tekerlek zinciri kuruldu (Bölüm 5 §7) |
| GNSS | Holybro **M10** GPS + pusula (32 g) | **Holybro M9N** | Tedarik |
| Kamera | **Arducam** IMX477 12MP (50 g) | **Raspberry Pi HQ** (IMX477, CSI) + standart lens | Aynı sensör (IMX477), farklı kart. Lens FOV'u **ÖLÇÜLMEDİ** — 5 Eylül'de `kamera_dogrula` ile ölçülecek |
| Güç dağıtımı / sensör | **Mauch PL-100** + Mauch PL 4-6S BEC + ayrı PDB | **Matek XCLASS FCHUB-12S V2** (PDB + akım sensörü) + **PM02** | Tedarik + sadeleştirme; akım ölçümü PM02'ye taşındı (`BATT_MONITOR=4`) |
| RC alıcı | TBS **Crossfire** Nano RX | **FlySky FS-i6** + FS-iA6B (**iBUS**) | Tedarik. Yazılım etkisi: `RC_PROTOCOLS` iBUS'a alındı (parametre dosyası, TEYİT listesinde) |
| Motor | SunnySky X2216 V3 1100KV ×2 (sabit kanat) | **5008 340KV ×4** + 12×10 pervane (çoklu rotor) | **Araç sınıfı farkı** — FDA aracı çoklu rotordur (§1) |
| ESC | Hobbywing FlyFun 40A V5 ×2 | **80 A DShot destekli ×4** (ilk uçuşlarda PWM 400 Hz) | Araç sınıfı farkı |
| Pil | 4S 14000–15000 mAh Li-ion (1000 g) | **1× 4S 10 Ah 25C**, şarj iMAX B6 (~3 saat dolum) | Tedarik. Operasyonel sonucu: **günde en fazla 2 uçuş** (takvim kısıtı, §5) |
| Paraşüt zinciri (kalem 12–16) | Opale Rescue 2,5 m² + pod + servo + mekanizma + tether | **FDA aracında YOK** | §5.3.2 çoklu rotor uçuşunda paraşüt zorunlu değil; final aracında kalır |
| Servolar (kanat/kuyruk) | EMAX ES08MA II ×4 | **FDA aracında YOK** | Araç sınıfı farkı |
| Pitot + airspeed | Pitot + Holybro MS5525DSO | **FDA aracında YOK** | Çoklu rotorda hava hızı sensörü kullanılmaz |
| Telemetri | Holybro SiK 433 MHz ×2 (uçak + YKS) | **2× SiK 433 MHz** — değişmedi | — |
| Acil güç kesme | Anahtarlı stop + röle | **Anahtar yok — pil fişi çekilir (XT60/XT90)** | 🔴 Şartname REQ-25…31 (çift acil güç kesme) FDA aracında **karşılanmıyor**; final aracı için **açık madde** (Bölüm 6'ya taşınır) |
| Gövde | (DDR: sabit kanat yapısal malzeme dağılımı) | **3B baskı quadcopter** (ABS + ABS-CF) | Araç sınıfı farkı; ayrıntı Bölüm 5 |

### 4.2 Yazılım ve mimari revizyonları

| konu | DDR'de beyan / plan | **FDR — bugünkü gerçek** | kanıt |
|---|---|---|---|
| Model | YOLOv8-seg **nano**, NCNN, conf > 0,40 (DDR akış şeması) | **YOLOv8m-seg**, `navitas-seg-v36-512`, PyTorch; conf 0,30 | `config/model_registry.json`, `navitas-teknofest/references/avionics_software.md` |
| Hızlandırma | TensorRT `.engine` (Jetson'da derlenir) | **Nano'da ÖLÇÜLEMEDİ** — venv38'de `tensorrt` modülü yok (JetPack 4.6 bağı Py3.6). PT/ONNX ile uçulur | `jetson_paket/JETSON_NANO_KURULUM.md` §0 |
| Rota karar yolu | tek yol varsayımı | **İki yol ayrıldı:** `analyze_path` üretim, `rota_bul` tanısal | D-295, `CONTRACTS.md` §11.2-EK |
| Pixhawk erişimi | doğrudan seri | 🔴 **Çoğullayıcı zorunlu** — seri port tek sahipli, üç tüketici ayrı UDP ucundan okur | D-403, `CONTRACTS.md` §7.4 |
| Kamera yolu | doğrudan `VideoCapture` | **Kamera köprüsü** (sistem Python 3.6 + GStreamer `nvarguscamerasrc` → MJPEG/HTTP) | D-406, `scripts/kamera_koprusu.py` |
| Hedef Bölge (HB) dedektörü | üretime bağlanacak | **BAĞLANMADI** — gerçek iniş pedinde isabet %0, kırmızı arabada %100 yanlış pozitif | D-295 §2, K3 |
| YKS görev kipi | tek kip | **`--fda` kipi eklendi** — paraşüt/İKA kapalı, bütçe tek 10 dk | D-408, `CONTRACTS.md` §6.7 |
| Süre limitleri | belgede | **Sözleşme sabiti**: İHA 900 s, İKA 600 s, FDA operasyon 600 s | `codes/karar_sozlesmesi.py`, D-318 |

### 4.3 Takvim revizyonu — şartname takvimi ile takım takvimi

| olay | şartname resmî tarihi | takım planı |
|---|---|---|
| FDR son teslim | **21.09.2026 – 17.00** | rapor bu tarihe yetiştirilir |
| FDA (FDS + Drone ile Görev Test Uçuşu) | **30.09 – 03.10.2026** | **tek atış** — `SAHA_RUNBOOK.md` başlık satırı |
| FDR sonuçları | 04.10.2026 | — |
| SGGS son teslim | 05.02.2027 | Bölüm 7'deki BOM bu sunumun temelidir |
| UHDR son teslim | 16.04.2027 | — |
| Uçuş testleri | 21.05.2027 | — |
| Yarışma | Ağustos–Eylül 2027 | — |

🔴 **Düzeltilen iç tutarsızlık.** `SAHA_HAZIRLIK_PLANI_20260903.md` §0.1, 21 Eylül Adıyaman
uçuşunu *"şartname §5.3.2"* diye etiketler. Bu **yanlıştır ve burada düzeltilir**: şartnamenin
resmî FDA penceresi 30.09–03.10.2026'dır (şartname s.11 takvim tablosu); 21 Eylül'deki Adıyaman
uçuşu takımın **kendi genel provasıdır** ve aynı zamanda FDR teslim günüdür. `SAHA_RUNBOOK.md`
başlık satırı bu doğru okumayı zaten taşır (*"kesin hazır 21 Eylül, tek atış 30 Eylül"*).
Plan belgesindeki etiket kaynağında düzeltilmemiştir (belge kaydı bozulmasın diye); rapor için
geçerli olan bu paragraftır.

### 4.4 🔴 Geçmeyen kapı — gizlenmez

Üretim modeli **v36**, kendi **ön kayıtlı iki eşiğini geçmeden** terfi etmiştir. Ham kayıt:

```text
ON KAYITLI ESIKLER GECILMEDI: ROTA >= 10 istendi, olculen 8;
MASKE_YOK <= 10 istendi, olculen 16.
GECILEN: FP <= 1 (1) ve YANLIS GUZERGAH = 0 (0).
Terfi bu esikleri GECEREK degil, KULLANICI KARARIYLA yapildi.
ESIKLER DEGISMEDI ve sonraki terfileri baglar.
```

- **Terfi tarihi:** 2026-08-26 · **Karar mercii:** kullanıcı (takım kararı), mimar değil.
- **Gerekçe:** gerçek karede yanlış güzergâh 15/21 → 7/38; engel üstü waypoint 79 → 3.
- **Bedeli açık yazıldı:** K3 0→1, K4 1→4, K6 5→7 (kapı içinde kaldı); kaplama67 0,51→0,42.
- **Eşikler gevşetilmedi** ve sonraki terfileri bağlamaya devam ediyor (`CONTRACTS.md` §12).
- Ayrıca aynı dönemde ölçülen bir karşı kalem: `karar_cevrilmesi` ekseninde v36, v35'ten
  **kötüdür** (14/260 vs 9/260, eşli koşum). Terfi geri alınmamış, ölçüm kayda geçmiştir (D-295 §3).

Bu satır, projenin kanıt yordamının kendi aleyhine de işlediğinin göstergesidir ve raporda
bilerek öne alınmıştır.

---

## 5. Planlanan takvim — 3 → 30 Eylül 2026

Kaynak: `SAHA_HAZIRLIK_PLANI_20260903.md` §4. Her satırın bir **kapısı** vardır; kapı geçilmeden
sonraki güne geçilmiş sayılmaz.

| gün | ne yapılır | rol | kapı |
|---|---|---|---|
| Per 3 Eyl | Jetson Nano yığını, kamera köprüsü, ArduCopter parametre + görev şablonu, çürütücü turu | R7, R8 | suit yeşil; dosyalar depoda ✅ |
| Cum 4 Eyl | microSD'ye JetPack 4.6.x yazımı; tekerlek + paket belleğe; YKS PC; alışveriş; **kargo teslim** | R1, R4, R5 | `results/faz_b_oncesi/` dolu; bellek hazır |
| **Cmt 5 Eyl** | **MONTAJ GÜNÜ** — kutu → mekanik → kablolama → Pixhawk → Nano kurulumu → yer zinciri (pervanesiz) | herkes | `mavlink_dogrula` 3/3; YKS'de HEARTBEAT; FPS ölçüldü |
| Paz 6 Eyl | Pusula kalibrasyonu (dışarıda); **ilk hover**; Loiter/Auto + iniş kanıtı — 2 uçuş | R2, R3, R5 | uçuş logu + `IHA_LANDED` |
| Pzt 7 – Cum 11 | Canlı algı (30 m'de OPEN_ROUTE); ilk tam prova | R2, R4, R5 | 1 tam prova ≤ 10 dk |
| Cmt 12 – Paz 13 | Tam prova ×2 | herkes | toplam 3 temiz prova |
| Pzt 14 – Çar 16 | Sıkı prova: kapalı kutudan başla, kronometre, sıfır müdahale | herkes | 0 müdahale |
| Per 17 Eyl | **Sürüm dondurma (mühür)** — bundan sonra kod değişmez | R7, R1 | künye depoda, `--dogrula` 0 |
| Cum 18 Eyl | "KESİN HAZIR" listesi baştan sona; yedek parça; taşıma kutusu | herkes | tutanak |
| Cmt 19 Eyl | Yedek gün; pil tam şarj | R2, R1 | — |
| Paz 20 Eyl | Adıyaman'a yolculuk; otelde kuru koşu | herkes | — |
| **Pzt 21 Eyl** | **Genel prova uçuşu — Adıyaman** · aynı gün **FDR son teslim (17.00)** | herkes | `results/gorev_20260921/` |
| 22–29 Eyl | Tutanak, düzeltmeler (mühür kapsamı dışında değişiklik yok) | — | — |
| **30.09–03.10** | **FDA — FDS + Drone ile Görev Test Uçuşu (şartname §5.3.2)** | herkes | **tek atış** |

**Takvimin ölçülmüş kısıtı:** tek pil ve iMAX B6 (~50 W → ~3 A → ~3 saat dolum) uçuş gününü
**en fazla 2 uçuşa** kilitler. İkinci pil + ≥150 W şarj cihazı prova sayısını ikiye katlar;
karar kaptandadır (`SAHA_HAZIRLIK_PLANI_20260903.md` §4 "Pil kuralı").

---

## 6. Takvim riskleri ve karşı önlemler (ölçülmüş olanlar)

| risk | neden gerçek | önlem | durumu |
|---|---|---|---|
| **Nano yığını kurulamaz** | v36 YOLOv8m-seg'dir; Nano **CPU**'da 512'de FPS kapısı (**0,61**) düşebilir — ölçülmedi | Çevrimdışı 14/14 aarch64 tekerlek hazır; sıra: CUDA topluluk wheel → ONNX Runtime → CPU torch | açık; 5 Eylül'de ölçülecek. **Eşik gevşetilmez** |
| **Yanlış güzergâh = 0 puan** | Şartname §5.3.2 mutlak | Histerezis, tek pas tarama, hakem ekranında güven + sebep | kod hazır (D-396) |
| **10 dk aşımı** | Şartname §5.3.2 mutlak | Görev planı kötü-durum bütçesi ~3–3,5 dk (hesaplandı, `config/pixhawk/README.md`) | test ile kilitli |
| **Tek pil** | Ölçülü (10 Ah, iMAX B6) | Günde 2 uçuş planı; 2. pil kararı kaptanda | açık |
| **Gerçek arena görüntüsü yok** | Ölçüm: arena benzeri saha kanıtı **yoktur** (T111/D-198) | Sentetik + gerçek kırsal iki ayrı çerçeve olarak raporlanır; arası tahmin edilmez | **kapanmadı** |
| **Acil güç kesme anahtarı yok** | Kullanıcı beyanı §0.2 | FDA aracında pil fişi; final aracı için tasarım borcu | **açık madde** |

---

## 7. Kanıt dizini

| # | sayı / iddia | dosya yolu | üreten betik / komut | ölçüm tarihi |
|---|---|---|---|---|
| 1 | 545 commit, ilk commit 2026-05-06 `17258f8` | `O:\navitas\.git` | `git log --date=short --pretty=format:"%ad\|%h\|%s"` | 2026-09-03 |
| 2 | Gün başına commit dağılımı (26.08 → 89, 02.09 → 72) | `O:\navitas\.git` | `git log … \| awk -F'\|' '{print $1}' \| sort \| uniq -c` | 2026-09-03 |
| 3 | Model dosyası damgaları v17…v36 | `jetson_paket/models/` | `ls -la jetson_paket/models/` | 2026-09-03 |
| 4 | Üretim modeli künyesi (`navitas-seg-v36-512`, imgsz 512, sha256 `1d1caca6…`) | `config/model_registry.json` → `profiles.competition` | `scripts/olcum/167_fdr_kanit_paketi.py` | 2026-09-01 |
| 5 | v36 ön kayıtlı eşiklerin geçilmediği ham metin (ROTA 8 < 10; MASKE_YOK 16 > 10) | `results/fdr/GORUNTU_ISLEME_KANIT.md` §3 | `scripts/olcum/167_fdr_kanit_paketi.py`; dayanak D-293/D-294 | 2026-08-26 (karar) / 2026-09-01 (paket) |
| 6 | `karar_cevrilmesi` v36 14/260 vs v35 9/260 | `REVIEW_LOG.md` D-295 §3 | eşli koşum, ON_KAYIT §16 | 2026-08-26 |
| 7 | v37 geri alındı; v8 adayı RED (124 epoch / 6,19 saat) | `REVIEW_LOG.md` D-332, D-331 | kabul zinciri `scripts/olcum/65_kabul_denetcisi.py` | 2026-08-28 |
| 8 | v31 = v30 bit-bit aynısı; 6,4 saat GPU karşılıksız | `REVIEW_LOG.md` D-138 (alıntı D-252:19148) | eğitim koşumu kıyası | 2026-08-16 |
| 9 | Uçtan uca kare gecikmesi p95 0,113 s | `results/fdr/GORUNTU_ISLEME_KANIT.md` §4.1b | D-382/D-383 ölçümü, 36 gerçek kare | 2026-09-01 |
| 10 | Tam suit 1827 test | `REVIEW_LOG.md`:28298 (D-407 §3) | `python -B -m unittest discover -s tests -q` | 2026-09-02 |
| 10b | Genel kapı 15/15 · 15/15; tam suit 1875 OK (skipped 3); kuru koşu 9 GEÇTİ / 1 SAHİPSİZ | `results/faz_b_oncesi/cuma_kontrol/cuma_kontrol.txt` | `codes/test_rota_sentetik.py`, `unittest discover`, `scripts/saha_kuru_kosu.py` | 2026-09-03 |
| 11 | Kanıt defteri 414 başlık / 408 benzersiz kayıt | `REVIEW_LOG.md` | `grep -cE "^### D-[0-9]+"` ve `\| sort -u \| wc -l` | 2026-09-03 |
| 12 | Şartname resmî takvimi (ÖDR/DDR/FDR/FDA/SGGS/UHDR tarihleri) | `results/sartname_bosluk/sartname_metin.txt` s.11 | PyMuPDF metin çıkarımı (`rapor_uret.py`) | 2026-08-26 |
| 13 | FDR puan tablosu (Tablo 4) ve FDA formülü (FDR×0,85 + uçuş×0,15) | `results/sartname_bosluk/sartname_metin.txt` §5.3.1–5.3.2 | aynı çıkarım | 2026-08-26 |
| 14 | DDR aviyonik BOM'u (27 kalem, 2293 g) | `navitas-teknofest/references/ddr_requirements.md` | DDR dönemi Excel aktarımı — **DOĞRULANACAK** | 2026-07 (tarih damgası yok) |
| 15 | DDR mimari şemasında "Pixhawk 6X" / "Jetson Orin NX" / "M10" | `navitas-teknofest/references/avionics_software.md` | — | 2026-07 |
| 16 | Gerçek donanım künyesi (Pixhawk 6C, M9N, Nano 4GB, FCHUB-12S, 5008 340KV, RPi HQ, 4S 10 Ah) | `SAHA_HAZIRLIK_PLANI_20260903.md` §0.2 | **kullanıcı beyanı**, 3 Eylül 2026 — kutu 5 Eylül'de açılıp teyit edilecek | 2026-09-03 |
| 17 | Planlanan 3–21 Eylül takvimi | `SAHA_HAZIRLIK_PLANI_20260903.md` §4 | — | 2026-09-03 |
| 18 | FDA görev kipi sözleşmesi (`--fda`) | `CONTRACTS.md` §6.7 · `REVIEW_LOG.md` D-408 | `tests/test_faz_b_yks_fda_kipi.py` (9 test, 4/4 mutant) | 2026-09-02 |
| 19 | MAVLink çoğullayıcı zorunluluğu | `CONTRACTS.md` §7.4 · `FAZ_B_GUN_PLANI.md` §1 | `scripts/mavlink_dogrula.py` | 2026-09-02 |
| 20 | Süre sözleşme sabitleri (900 / 600 / 600 s) | `codes/karar_sozlesmesi.py` · `CONTRACTS.md` §7.1 | `REVIEW_LOG.md` D-318 | 2026-08-27 |

### BEYAN GEREKLİ (insan) — bu bölümde kapatılacak boşluklar

1. **BEYAN GEREKLİ (insan): rol → isim ataması** (8 rol; ad-soyad, öğrenim düzeyi, yedek rol).
2. **BEYAN GEREKLİ (insan): takım üye sayısı ve şartname §4 oran kontrolü** (6–10 kişi; lisansüstü oranı).
3. **BEYAN GEREKLİ (insan): danışman öğretim üyesi** bilgisi.
4. **BEYAN GEREKLİ (insan): takım künyesinin KYS teyidi** (ID 997827 / başvuru 5329027).
5. **BEYAN GEREKLİ (insan): 5 Eylül kutu açılış teyidi** — §4.1'deki gerçek künye satırlarının
   her biri fiziksel parça ile karşılaştırılıp imzalanacaktır.
6. **BEYAN GEREKLİ (insan): 21 Eylül Adıyaman uçuş alanı izni** ve alan koordinatları.
