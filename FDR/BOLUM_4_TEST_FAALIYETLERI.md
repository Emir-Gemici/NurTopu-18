# Bölüm 4. Test Faaliyetleri (15 PUAN)

> **Bu bölümün iddiası.** NAVITAS'ın en olgun tarafı bir model ya da bir kart
> değil, **ölçüm yordamıdır**. Aşağıda önce yordam (bir sayının bu projede nasıl
> "kanıt" sayıldığı), sonra otomatik kapı envanteri, sonra kabul kapılarının
> sonuçları, sonra **geçilmeyen kapılar**, sonra donanım gelmeden koşulan
> entegrasyon testleri ve en sonda **kapanmamış test borcu** yer alır.
>
> **Bu bölümün iddia ETMEDİĞİ.** Hiçbir sayı "sahada çalışır" demez. Arena
> ölçümlerinin tamamı sentetiktir; elimizde **gerçek arena/HTAB karesi yoktur**
> ve maket çekimi yapılmayacaktır. Uçuş testleri 6–19 Eylül planlıdır ve bu
> rapor yazılırken **hiçbiri koşulmamıştır**. Jetson üzerinde gerçek FPS ~~**ölçülmemiştir**~~
> → **6 Eylül'de ÖLÇÜLDÜ** (kart Orin Nano Developer Kit 4 GB; pt 1,35/1,06 · engine 1,58/1,33 FPS,
> eşik 0,61 — D-431, §4.4); SiK 433 MHz RF menzili **ölçülmemiştir**.
>
> **İki araç ayrımı.** Şartname §5.3.2 görev test uçuşu (prova: 21 Eylül Adıyaman · resmî uçuş: 30 Eylül–3 Ekim)
> **çoklu rotorlu** bir araçla yapılır: 3B baskı quadcopter, Pixhawk 6C + PM02,
> Jetson Orin Nano Developer Kit 4 GB (3 Eylül beyanı 'Nano 4GB' 6 Eylül'de kartla yanlışlandı, D-431),
> Raspberry Pi HQ (IMX477). Yarışma görevinin (§2.2) aracı
> **sabit kanat + mancınık + paraşüt + İKA**'dır ve ayrı sistemdir. Aşağıdaki
> testlerin **tamamı** algı–karar–haberleşme–yer istasyonu katmanına aittir; bu
> katman iki araçta da aynıdır. Uçuş kontrolcüsü yapılandırması ayrışır ve
> ayrıştığı yerde ayrıca yazılmıştır.

---

## 4.0 Bu bölümün yönergeye göre kapsaması

Yönerge Bölüm 4 tek paragraf hâlinde **on iki** gereksinim sayar. Aşağıdaki
tablo her birini bu bölümdeki karşılığına bağlar; alt başlık numaraları
gereksinim kimlikleriyle (`Y-4-M01` … `Y-4-M12`) aynı sırayı izler.

| kimlik | yönergenin istediği | bu bölümde | durum |
|---|---|---|---|
| `Y-4-M01` | planlanan yer testleri, fonksiyonel testler, entegrasyon testleri ile tasarımın gereksinimlere uygunluğunun doğrulanması | §4.1 | KISMEN |
| `Y-4-M02` | testlerin uygulama yöntemleri ve test altyapısı gereksinimlerinin nihai hâli | §4.2 | VAR |
| `Y-4-M03` | sensör gereksinimleri, sensör yerleşimleri, test takvimi, detaylı test zaman bütçe planlaması | §4.3 | KISMEN |
| `Y-4-M04` | ekipman kabul testleri — İHA ve İKA'daki **tüm** ekipmanlar | §4.4 | YOK |
| `Y-4-M05` | kumanda ve telemetri **menzil** testleri (sahada) | §4.5 | YOK |
| `Y-4-M06` | IMU, pusula ve pitot tüpü kalibrasyon kanıtları | §4.6 | YOK |
| `Y-4-M07` | görev icra simülasyonu + başarı oranları + grafikler + video linki | §4.7 (sahibi **Bölüm 3.3.3**) | YOK |
| `Y-4-M08` | görüntü işleme performansı, benzer koşullarda test sonuçları, doğruluk matrisleri | §4.8 | KISMEN |
| `Y-4-M09` | haberleşme: paket yapısı, veri hızı, iletişim gecikmesi | §4.9 | KISMEN |
| `Y-4-M10` | sistem üzerinde gerçekleştirilen **tüm** yer testleri | §4.10 | KISMEN |
| `Y-4-M11` | entegrasyon öncesi alt sistemlerin bir arada ve yerde bütünleşik çalıştığı kanıtlar | §4.11 | KISMEN |
| `Y-4-M12` | arıza emniyet doğrulaması (eve dönüş, motor kesme) — **sahada test edilmiş veri** | §4.12 | YOK |

**Karşılanamayan ve kısmen karşılanan gereksinimlerin nedenleri** §4.13'te kalem
kalem yazılıdır; yönergenin Bölüm 6 beklentisi (`Y-6-M05`) oradan beslenir.
Kanıt yolları §4.14'tedir.

---

## 4.1 Planlanan yer testleri, fonksiyonel testler ve entegrasyon testleri · `Y-4-M01`

> *Yönerge: "planlanan yer testleri, fonksiyonel testler ve entegrasyon testleri
> aracılığıyla tasarımın belirlenen gereksinimlere uygunluğu doğrulanmalıdır."*

Bu gereksinimin bugün karşılanan kısmı **algı–karar–haberleşme katmanının
otomatik kapı envanteri**dir; koşulmuş ve ham çıktısı buradadır. Araç yerde
bütünleşik çalıştırılmadığı için gereksinim KISMEN karşılanmıştır — eksik kalan
kısım §4.11 ve §4.13'tedir.

Aşağıdaki iki kapı **bu bölüm yazılırken koşuldu** (3 Eylül 2026); çıktılar ham
olarak konmuştur.

### 4.1.1 Genel kapı — `codes/test_rota_sentetik.py`

Anayasa madde 14: her görevden sonra bu kapı koşulur; düşerse görev geri alınır.
Kapı **iki kollu**dur: tanısal yol (`costmap_path_finder.rota_bul`) ve **üretim
yolu** (`rpi_inference.analyze_path`). İkinci kol, R1/T156'da ölçülen "genel
kapı yalnız `rota_bul`u zorluyor" boşluğunu kapatmak için eklendi.

**Koşum çıktısı (ham, 3 Eylül 2026):**

```text
==============================================================================
KORIDOR SECIMI - 15 DETERMINISTIK SENTETIK SAHNE (kusursuz maske)
==============================================================================
KOL 1 - TANISAL YOL (costmap_path_finder.rota_bul) - sart: TAM PUAN
harita  senaryo  gercek  tahmin  guven              durum   wp  sonuc
     1    kolay       1       1  1.000               ACIK   43  OK
     1     orta       2       2  1.000               ACIK   43  OK
     1      zor       3       3  0.797               ACIK   67  OK
     ...
SONUC: 15/15 dogru
[OK] TUM DETERMINISTIK SAHNELER GECTI

==============================================================================
KOL 2 - URETIM YOLU (rpi_inference.analyze_path) - AYNI 15 SAHNE
==============================================================================
harita  senaryo  gercek   yayin  guven   wp              ret  darbogaz  sonuc
     1    kolay       1       1  0.822    8             None         2  OK
     ...
URETIM YOLU: rota uretimi 15/15 - yayinlanan serit 15/15 (esik >= 14/15, ON_KAYIT SS18-B)
[OK] URETIM YOLU KOLU GECTI
------------------------------------------------------------------------------
GENEL KAPI (madde 14): GECTI - kol1 15/15 - kol2 serit 15/15
```

⚠ Kapsam: 15 sahne **kusursuz maskeyle** üretilmiş sentetik sahnelerdir. Bu kapı
karar geometrisinin (koridor seçimi, C-uzayı, darboğaz) doğruluğunu kilitler;
**algının** doğruluğunu ölçmez. Algı K0–K8'de ve gerçek-kare kapısındadır.

### 4.1.2 Tam test paketi — `python -m unittest discover -s tests`

**Koşum çıktısı (ham, 3 Eylül 2026, yorumlayıcı
`O:\navitas-local-train\venv\Scripts\python.exe`):**

```text
----------------------------------------------------------------------
Ran 1896 tests in 390.534s

OK (skipped=3)
```

**Suit büyümesi (kayıt defterinden, günü gününe):**

| tarih | test | kayıt |
|---:|---:|---|
| 2 Eyl | 1489 | D-388 §5 |
| 3 Eyl (D-403) | 1617 | D-403 §6 |
| 3 Eyl (D-404) | 1685 | D-404 §5 |
| 3 Eyl (D-406) | 1826 | D-406 |
| 3 Eyl (D-407) | 1827 | D-407 §4 |
| **3 Eyl (bu bölüm)** | **1896** | bu koşum. Ölçülen ara adımlar: 1875 (D-408 anı) → 1882 (saha belleği kapıları) → 1890 (takvim kapısı ve çürütücü turu kapıları) → **1896** (hakem kanıt yolu, +6 · D-412). 1890'lık koşum **6 hata** verdi; bkz. §4.13.3.1 |

`tests/` altında **153** adet `test_*.py` dosyası vardır (`ls tests/ | grep -c "^test_"`, 3 Eylül 2026). Aynı komut 5 Eylül 2026'da **180** verir.

**Faz B'de eklenen kapı dosyaları (test metodu sayısı, `grep -c "def test_"`):**

| dosya | test | neyi kilitler |
|---|---:|---|
| `tests/test_faz_b_surum_dondurma.py` | 49 | §6.1 sürüm mührü: kirli ağaç reddi, künye git bağı, kapsam (paket + kaynak + model + saha yapılandırma + YKS/İKA) |
| `tests/test_faz_b_jetson_baslat.py` | 42 | Jetson tek komut açılış; kuru çıktı == systemd `ExecStart` |
| `tests/test_faz_b_seri_hub.py` | 31 | SiK hub: uçtan uca YKS-seri → hub → gerçek `IhaKomutAlici` → ACK → seri |
| `tests/test_faz_b_nano_kurulum.py` | 20 | Nano kurulum belgesi ile birim dosyalarının dizin haritası uyumu |
| `tests/test_faz_b_akis_istegi.py` | 17 | T207: `SET_MESSAGE_INTERVAL` periyodik yenileme + sessizlik alarmı |
| `tests/test_faz_b_ack_ref_tip.py` | 14 | T206: ACK `ref_tip` eşleşmesi (çapraz eşleşme yasağı) |
| `tests/test_faz_b_pixhawk_sablon.py` | 12 | ArduCopter parametre + FDA görev şablonu metin kilidi |
| `tests/test_faz_b_rpi_ekransiz.py` | 9 | Ekransız kip: karar yolu bayt-eş, görsel üretilmez |
| `tests/test_faz_b_kamera_koprusu.py` | 7 | Kamera köprüsü (Python 3.6 uyumu, MJPEG, fail-visible) |
| `tests/test_k7_serit_dogrulugu.py` | 27 | K7 yayınlanan şerit doğruluğu + alt küme kanonik özeti |
| `tests/test_inis_kaniti.py` | 26 | `yerde_mi` sözleşmesi (ON_GROUND + irtifa + aynı sysid + ardışık 3) |

### 4.1.3 Bu envanterin kapsamadığı şey

| kapı kipi | neden koşulamadı |
|---|---|
| `jetson_baslat.sh --kur` / `--kapi` / `--dogrudan` (systemd) | Windows'ta koşulamaz; **Jetson'daki ilk koşum ilk kanıt olacak** (5 Eylül). **5 Eylül güncellemesi:** Jetson o gün araca takılmadı (D-426 §4: *"Jetson takili DEGIL"*); ilk koşum hâlâ **ÖLÇÜLEMEDİ** |
| TensorRT `.engine` derleme ve karar kıyası | `tensorrt` çalışma zamanı PC'de yok (venv'e bilerek kurulmadı); ORT CPU'ya geri düştü ve betik geri düşmeyi **"dönüştü" saymadı** (fail-closed çalıştı) |
| Gerçek MAVProxy | PC'de `[YOK] mavproxy.py (PATH)`; kuru koşu bunu **gizlemez, raporlar** |
| Tam suit, **YKS canlıyken** | D-427 (5 Eylül): `comms/test_comms.py:35-36` loopback'i üretim YKS/İKA portları **5005/5006**'ya bind eder; `comms/link.py` tek-sahipli uçta `SO_EXCLUSIVEADDRUSE` kurduğu için `yks_gui.py` açıkken `test_p8_sim_katmani.test_comms_loopback_gecer` **kesin düşer** (`WinError 10013`). 5 Eylül'de 3 koşumdan 2'si böyle düştü; kod değişmedi. Kuyruk: **T209** (geçici port ya da sebep söyleyen `skipTest`), henüz yapılmadı |

---

## 4.2 Testlerin uygulama yöntemleri ve test altyapısı gereksinimlerinin nihai hâli · `Y-4-M02`

> *Yönerge: "…ön tasarım ve detay değerlendirme raporlarında tanımlanan
> testlerin uygulama yöntemleri ile test altyapısı gereksinimlerinin nihai
> hâlinin ayrıntılı biçimde açıklanması beklenmektedir."*

**Uygulama yöntemi bu projede dört mekanizmadır**; nihai hâli aşağıdadır. Dört
mekanizma birlikte tek bir soruyu yanıtlar: **bir sayı bu projede nasıl kanıt
olur.** Test altyapısının nihai hâli (koşum ortamı ve fikstürler) §4.2.6'dadır.

Dört mekanizma birlikte çalışır. Hiçbiri sonradan icat edilmiş bir rapor süsü
değildir; her biri **bu projede bir kez gerçek zarar önlediği için** kuraldır ve
zararın kaydı `REVIEW_LOG.md`'de durur (**432 başlık · 426 benzersiz kayıt**, son kayıt D-427;
`grep -cE "^### D-[0-9]+"` · `grep -oE "^### D-[0-9]+" | sort -u | wc -l`, 5 Eylül 2026; 3 Eylül'de 414 · 408).

### 4.2.1 Ön kayıt — eşik, sonuç görülmeden yazılır (D-107)

**Kural.** Bir kapının eşiği ve **karar sırası**, ölçüm koşulmadan önce bir
`ON_KAYIT` dosyasına yazılır ve sonuç görüldükten sonra **değiştirilmez**.

**Kuralın doğuşu (D-107, 2026-08-14).** Kayıt kendi gerekçesini şöyle yazar:

```
NEDEN ONCEDEN. Bu projede tekrarlanan hata olcutu SAYIYI GORDUKTEN SONRA
yorumlamak oldu: D-85'te alt kumenin azamisine esik oturttum (D-86 curuttu),
D-90'da tanima bagli bir olcutle %92,7 rapor etmek uzereydim, D-104'te kapiyi
yanlis modelle olcturdum. Olcut sonuctan SONRA secilirse rasyonalize edilir.
Bu yuzden esikler BURAYA, sonuc gelmeden yaziliyor ve sabah DEGISTIRILMEYECEK.
```

**Depodaki hacim:** `results/` altında **36 ön kayıt artefaktı** (35 Markdown +
1 JSON), `find results -iname "*on_kayit*"` (3 Eylül 2026; 5 Eylül 2026'da yeniden sayıldı: 36, değişmedi).

**Ön kaydın somut olarak iş gördüğü dört olay:**

| olay | ön kayıtta ne yazılıydı | ölçüm ne çıktı | sonuç |
|---|---|---|---|
| **Çözünürlük 640** (D-377, `results/b4_fps/ON_KAYIT_INFER_SIZE.md` §5) | *"I2 düşerse → RED. I1 ne olursa olsun."* | I1 = **%21,6** (umut verici), I2 = **−0,204** (tavan −0,02) | **RED.** Karar sırası önceden yazılı olduğu için "kırsalda kazandırıyor, arenada biraz kaybettiriyor" tartışması hiç açılmadı |
| **P2 tampon tavanı** (D-388, `results/p2_seri/ON_KAYIT.md` S5) | tampon **≤ 64 KiB** kalmalı; gerekçe: en uzun meşru çerçevenin 16 katı | ölçülen **1.048.576 bayt** (sınırsız) | **DÜŞTÜ** → kod düzeltildi, **aynı eşikle** yeniden koşuldu; eşik gevşetilmedi |
| **P5 yayın histerezisi** (D-396, `results/p5_histerezis/ON_KAYIT.md`) | H1: toplam çevrilme ≤ %40 | H1 **düştü ve düşük kaldı** | Eşik **gevşetilmedi**; yerine EK-1 ölçütleri (H1a/H1b) *bileşim görülmeden* yazıldı, ölçüm sonra koşuldu |
| **T61 iç tutarlılık** (D-401, `results/t61_ic_tutarlilik/ON_KAYIT.md`) | tur **eşiksizdir**; eşik ancak ikinci bir ön kayıtla, tüm kümede süpürülerek yazılır | dört aday **DOĞRULANAMADI** | Keşif turu eşik **üretmedi**; "alt kümede ayrık görünen eşik tümde ayırmaz" dersi (D-86) korundu |

⚠ Ön kayıt **her zaman** kurtarmadı: `results/gece_20260826/ON_KAYIT.md` §15'te
kullanıcı *"izin veriyorum kurala rağmen"* diye yazdı ve v36 kendi eşiklerini
geçmeden terfi etti. Bu olay §4.8.2.1'de tam olarak yazılıdır — ön kaydın rolü
burada da **olayı görünür kılmak** oldu; sessiz bir gevşetme mümkün olmadı.

### 4.2.2 Mutasyon kontrolü — kapı kaldırılınca DÜŞMELİ

**Kural.** Bir test "geçti" demek yetmez; korumak iddia ettiği davranış **koda
uygulanmış** bir bozma (mutant) ile kaldırıldığında testin **düşmesi** gerekir.
Uygulanmayan mutasyon başarı sayılmaz (D-370).

**Depodan gerçek örnekler:**

| mutant | nereye uygulandı | suit tepkisi | kayıt |
|---|---|---|---|
| `if ekransiz:` korumaları → `if False:` | `codes/rpi_inference.py` | **3 test ERROR** (`cv2.error` yükseldi); dosya sonra `cmp` ile bayt-eş geri yüklendi | D-404 §2 |
| bağımsız denetçinin 7 mutantı (ekransız + kayıtlı video yolu) | `codes/rpi_inference.py` | ilk turda **4'ü kaçtı** (b, c, e, g) → test 8 ve 9 eklendi → **7/7 YAKALANDI** | D-404 §8 · `results/faz_b_oncesi/ekransiz_denetim/mutant_sonuc_9test.txt` |
| MUT-1 periyodik akış isteği kaldırıldı · MUT-2 sessizlik alarmı kaldırıldı | `comms/iha_inis_yayinci.py` (T207) | her biri **3 FAIL**; diğer 14 kapı ikisinde de geçti (hedefe özgü) | D-406 §3 |
| `--streamrate 8` silindi | `jetson_paket/systemd/navitas-cogullayici.service` | **K1 DÜŞTÜ** | D-406 §3 (K2) |
| Nano kurulum belgesinde `scripts/` → `codes/` | `jetson_paket/JETSON_NANO_KURULUM.md` | test **DÜŞTÜ** (`belge ~/navitas/codes/ diyor, jetson_baslat.sh scripts/ ariyor`) | D-407 §1 |
| çerçeveleme atlanıp ham bayt fan-out | `comms/seri_hub.py` | **2 test** yakaladı | D-404 §1 |
| `_kanit_yaz` tanımı geçici kaldırıldı (3 Eyl) | `comms/yks_gui.py` | **6/6 test düştü** (2 failure + 4 error); dosya `cmp` ile bayt-eş geri yüklendi | D-412 |
| var olmayan başlığa `§6.99.7` atfı eklendi (4 Eyl) | `FDR/BOLUM_6_GEREKSINIM_IZLENEBILIRLIGI.md` | **T1 DÜŞTÜ**; `cmp` bayt-eş (ilk geri yükleme dosya kilidine takıldı, yeniden denendi) | D-420 §5 |
| `--izinli-kaynak` bayrağı runbook'tan çıkarıldı (4 Eyl) | `SAHA_RUNBOOK.md` §3 | **T1 düştü** (`test_runbook_komutlari_kosuyor`); `cmp` bayt-eş | D-421 §2 |
| (1) eski mutlak sapma tavanı geri konuldu · (2) `_yerel_saat_adimi` öldürüldü (4 Eyl) | `comms/iha_komut_alici.py` | (1) **17 test düştü** · (2) **5 test düştü**; `git diff -U0` ile silinen assert **0** (71 → 140); ayna `jetson_paket/kod/` bayt-eş doğrulandı | D-422 §6 |

**🟡 Dürüst mutasyon skoru — bir kapı takımı zayıf çıktı, yazıldı ve sonra kapatıldı.**
`comms/seri_hub.py` için bağımsız çürütücü **25 mutant** üretti. **İlk ölçümde**
repo suiti **13'ünü yakaladı** (`results/faz_b_oncesi/curutucu_d405/BULGULAR_OZET.md`,
ham loglar `mut_seri_hub/log_*.txt`); kaçanların adları ve neyi açıkta bıraktıkları
aynı belgede tek tek yazılıdır — iki öğrenilen tüketiciden yalnız sonuncusuna
fan-out, `OGRENILEN_TAVANI` (32) tahliye mantığı, yeniden açmada `FrameReader`
sıfırlaması, beş fail-visible sayaç yolu.

**Sertleştirmeden sonra aynı 25 mutant yeniden koşuldu: 24/25.** Kapı takımı
`test_faz_b_seri_hub.py` 11 → **31 test**, `test_faz_b_protocol_dayaniklilik.py`
**4 test** (yeni) ile büyüdü; commit `c112381`, kayıt `REVIEW_LOG.md` D-405.

**Tek kaçan hâlâ vardır ve bilerek testsizdir:** `l_arizada_ogrenmez` — seri arıza
anında yeni tüketici öğrenilmemesi. Marjinal görüldüğü için test yazılmadı; bu
raporun kuralınca **açık** sayılır ve §4.13'te öyle listelenir. Skorun "13" değil
"24" olması, ilk sayının silinmesiyle değil, **ikinci ölçümün koşulmasıyla**
elde edildi; ikisi de artefaktta durur.

**🔴 Ölçen aracın kendisi de ölçülür (D-370).** Mutasyon betiği
`scripts/olcum/129_t141_mutasyon_olcumu.py`, `\n` ile biten bir desen arıyordu;
hedef dosya `simulation/scripts/ika_nav.py` **tamamen CRLF**'ti (ölçüldü: 658
CRLF, 0 çıplak LF). Yani **M2′ mutasyonu hiç uygulanmıyordu** ve betik yine
`exit 0` dönüyordu — çıkış kodunu okuyan bir kapı bunu **başarı** sanardı.
İki önlem geldi: desen dosyanın kendi satır sonuna uyarlanır, ve **uygulanmayan
mutasyon artık `exit 1`**'dir. `OLCULEMEDI != GECTI` kuralı çıkış kodu düzeyine
indirildi.

### 4.2.3 Çürütücü turları — bağımsız ajan kusur arar

**Kural (Anayasa madde 19).** *"Bir iş, onu yazanın onayıyla kapanmaz."* Kodu
yazan, kendi kodunu denetlemez; ayrı bir ajan **kusur bulmakla görevlendirilir**
ve her bulgu **koşulmuş komut + ham çıktı (repro)** ile gelmek zorundadır.
Bulgular kabul edilmeden önce mimar tarafından **yeniden üretilir**.

| tur | kapsam | kadro | hasat | kanıt |
|---|---|---|---|---|
| **D-383** (1 Eyl) | telsiz gecikmesi, YKS tazelik, şekil kapısı, nihai ret | 3 bağımsız ajan (357k token, 74 araç çağrısı) | **4 gerçek kusur**: "308 ms ACK gecikmesi" aslında bir **soket zaman aşımı sabiti**; YKS duvar-saati asimetrisi (saat 30 s geri alınınca BAYAT → TAZE); şekil kapısı "H"yi değil "çerçeveli yapıyı" ölçüyormuş; nihai ret sahnedeki **gerçek pedi** öldürüyormuş | REVIEW_LOG D-383 |
| **D-405** (3 Eyl) | mühür atlatma, hub protokol/ACK, arıza/kaynak, kuru-vs-gerçek, test vakumu | 5 mercek | **1 KRİTİK + 16 ÖNEMLİ + 18 KÜÇÜK**, ayrıca **5 çürütülemedi** kalemi | `results/faz_b_oncesi/curutucu_d405/BULGULAR_OZET.md` (30 KB) + `BULGULAR_TAM.md` (81 KB) + repro betikleri |
| **D-407** (3 Eyl) | D-405/D-406 kapanışlarının denetimi | 5 mercek (kota nedeniyle kısmen ana döngüde koşuldu) | **2 gerçek kusur** (Nano belgesi yanlış dizin; mühür kapsamı eksik) + T207 gerçek topolojide **doğrulandı** + köprü sağlam çıktı | `results/faz_b_oncesi/curutucu_d407/` |
| **D-411** (3 Eyl) | bu raporun taslağı: 302 dosya yolu iddiası (294 geçerli), 30 satır-numarası atfı (3'ü anlamca yanlış satır), tüm sayısal iddialar | "yazanı olmayan" göz (kayıtta kadro sayısı yazılı değil) | **71 bulgu, 6 KRİTİK**: 21 Eylül uçuş günü sanılıyordu; suit sayısı üç farklı değer taşıyordu; `seed` kusuru D-138 diye atıf alıyordu (doğrusu D-140); K6 `2/256 = %1,17` (doğrusu %0,78); hub skoru "13/25" kalmış (ölçülen 24/25). **30 KÜÇÜK bulgu kapatılmadı ve kapatılmış gibi yazılmadı** | REVIEW_LOG D-411 |
| **D-421** (4 Eyl) | "cumartesiye hazır mıyız" iddiası — dört eksen | her eksen ayrı doğrulayıcıyla | **13 tıkayıcı bulgu**; en ağırı: runbook komutu `EXIT=2` ile ölüyken kapısı 22/22 yeşil (§4.2.4 madde 5); Nano'ya internet zorunluluğu hiçbir listede yoktu; cuma kartında iki yanlış sayı; saat kilidi ayrı tura verildi (→ D-422). Kayıt: *"Onaylayan tur hicbir sey bulmazdi. Curuten tur 13 tikayici buldu."* | REVIEW_LOG D-421 |

**D-405'in KRİTİK bulgusu, örnek olarak:** sürüm dondurma mührünün özeti
**çalışma ağacı baytına** bağlıydı (CRLF). Aynı commit'in başka bir checkout'unda
künye tutmuyordu — Jetson/Linux'ta 18/19, başka bir Windows klonunda 2/19 dosya
"ihlal" diyordu. Yani şartname §6.1'in *"yarışan yazılım beyanla birebir"*
iddiasının tek kanıtı **tek makineye bağlıydı** ve saha günü yanlış "MÜHÜR
İHLALİ" alarmı olasıydı. Öneri ölçüldü de: CRLF→LF normalize sha256 iki klon
arasında **17/17 paket + defter eşit**.

⚠ **Yordam dürüstlüğü:** D-407 turunda kredi bitince beş mercekli iş akışı
düştü; ajanların bıraktığı repro betikleri **ana döngüde koşuldu**. Kayıt bunu
şöyle yazar: *"Ajan sayısı değil koşulan ölçüm kanıttır."* Aynı kayıt kendi
denetim borcunu da yazar: bu turdaki düzeltmeleri **yazan da onaylayan da aynı
taraftır**; mimar-dışı denetim açıktır (§4.13.3).

### 4.2.4 Vakum denetimi — test bir şeyi gerçekten kilitliyor mu

**Kural.** Bir testin yeşil olması, bir şey **koruduğu** anlamına gelmez. Test
hiçbir şeyi bağlamıyorsa (payda boş, mutasyon uygulanmıyor, iki kol aynı şeyi
koşuyor) o test bir **vakumdur** ve varlığı zararlıdır: güven üretir, koruma
üretmez.

**Bu projedeki dört vakum, hepsi ölçüldü ve kapatıldı** (4–5 Eylül'de ölçülen üç vakum daha 5–7'dedir):

1. **D-15 · Anayasa madde 4 kapısı hiç çalışmamıştı.** Yasak bağımlılık kapısı
   olarak dolaşan komut `grep -rnE "^\s*(import\|from)\s+(scipy\|skimage\|sklearn)"`
   idi. `-E` kipinde `\|` alternasyon **değil**, düz bir karakterdir; komut
   `import\|from` dizisini arar ve **her zaman 0 döner**. Kanıt **pozitif
   kontrolle** verildi: aynı komut kalıbı kodda kesinlikle var olan `numpy|cv2`
   için de **0** döndü — yani kapı kördü. Doğru kapı
   (`git ls-files "*.py" | xargs grep -nE ...`) pozitif kontrolde **46** eşleşme
   verdi. Madde 4 **fiilen sağlanıyordu**, ama bunu o güne kadar hiçbir koşum
   kanıtlamamıştı.

2. **D-375 · FP16 denkliğinin ilk ölçümü vakumdu.** İlk koşum "F1/F2 GEÇTİ"
   verdi ama `bit_es_orani = 1,0`: **893 karenin 893'ünde** maskeler bit-eşti.
   *Fazla mükemmeldi.* Ölçen araç ölçüldü: ultralytics predictor'ı ilk çağrıda
   kurulur, sonraki çağrının `half=True`'su **sessizce yok sayılır** — iki kol
   da FP32 koşmuştu. *"GEÇTİ", hiçliğin ölçümüydü."* Sınıfın adı kayda geçti:
   **FARKSIZLIK ≠ DENKLİK**. Düzeltme koda kondu (iki ayrı model örneği +
   `_dtype_dogrula`; tutmazsa betik `OLCULEMEDI` deyip `exit 1`). Gerçek ölçüm
   sonra geçti (§4.8.3).

3. **Kabul zincirinin kendi vakumu → K8 doğdu.** 2026-08-28'de v37 adayı
   K0'dan K7'ye **zincirin tamamını** geçti (K1 258/260, K7 87/87 = %100,0) ve
   "ÜRETİME ALINIR" verdikti aldı. Ama elimizdeki tek gerçekçi karede zemin
   kaplaması %4,4 → %56,1 çıkıp üretim karar yolunu `ZEMIN_MASKESI_SUPHELI` ile
   kırdı: model o karede **hiç rota üretemiyordu**. Bunu yakalayan tek şey
   `tests/test_gercek_arena_kapisi.py` idi ve **zincirin içinde değildi**. K8
   (`scripts/olcum/155_gercek_kare_kapisi.py`) tam olarak bunu zincire taşır ve
   **yeni bir eşik uydurmaz**: üretimde zaten var olan zemin sağlamlık kapısını
   gerçek kare üzerinde koşar. `n = 1`'dir ve betik bunu kendisi yazar.

4. **K7'nin ölçüm kümesi vakuma karşı daraltıldı.** Şerit numarası içerik
   genişliğinin üçte birlerinden hesaplanır; koridor kapısı bir sınıra denk
   geldiğinde etiket **tanım gereği** belirsizdir. Ölçüldü (D-312): kabul
   kümesinin **%54'ü (105/193)** böyledir ve şerit ayrışmasının **%100'ü**
   oradan gelir. K7 bu yüzden dondurulmuş **88 karelik** bir alt kümede ölçülür
   (`config/k7_iyi_kosullu_kume.json`); aksi hâlde kapı, tanım gereği belirsiz
   olan bir şeyi ölçüyormuş gibi yapardı — CONTRACTS bunu açıkça *"D-15 sınıfı
   vakum kapı"* diye adlandırır.

5. **D-421 §2 · Runbook kapısı 22/22 yeşilken komut ölüydü (4 Eyl).** `SAHA_RUNBOOK.md`
   §3'teki `iha_komut_alici` komutu `error: --izinli-kaynak HOST:PORT saha
   komutlari icin zorunlu` / `EXIT=2` ile düşüyordu; kapısı `tests/test_p4_runbook.py`
   **22/22 geçiyordu**. Kayıt: *"Yaptigi sey sabit bir jeton listesiyle `assertIn`
   substring aramasiydi; listede `--izinli-kaynak` yoktu. Komut OLUYKEN kapi yesil."*
   Asimetri: bloğun ilk satırı (`iha_inis_yayinci`) kalkıyor, ikincisi ölüyor — sahada
   zincir yarı canlı görünür, ARM/DISARM/RTL/LAND/PARAŞÜT hiç ACK almaz. Yeni kapı
   `tests/test_runbook_komutlari_kosuyor.py` (3 test) komutu **gerçekten koşar**; T2
   vakumluluk (≥ 3 komut ve kusurun çıktığı komut kapsamda). Kayıt bunu aynı sınıfın
   **dördüncü** tekrarı diye yazar (D-415, D-419 §5, sahte-kapı dedektörü, runbook):
   *"Dordunde de olcum aletinin kendisi olculmemisti."*

6. **D-423 · Kapı doğru kopyada düşerdi (4 Eyl).** `JETSON_NANO_KURULUM.md` §3.4'e
   yazılan kapı `ls ~/wheels | wc -l` → **48** bekliyordu; komut **51** basar
   (48 `.whl` + 3 metin dosyası). *"Iki sayi da gercek, ama ayni seyi olcmuyorlar."*
   Kusuru düzeltme turu üretti: D-421 §4'te karttaki "51" ölçülüp "48" yapılmış, aynı
   turda yazılan kapı kendine uygulanmamıştı. Sahadaki insan doğru kopyada 51 ≠ 48
   görüp kurulumu durdururdu. Onarım: `ls ~/wheels/*.whl | wc -l` = 48; kapı
   `tests/test_wheels_sayisi_belgelerle_tutarli.py` (4 test) dosya sistemini sayıp
   kılavuz ve kart sayılarıyla karşılaştırır ve kendi vakumluluğunu ölçer (`.whl`
   sayısı ≠ toplam dosya sayısı; eşitlerse *"test kendi kendini anlamsizlastirmis
   demektir"*). Kural genişletildi: *"bir belgeye sayi yazan her duzeltme, o sayiyi
   ureten komutun gercekten o sayiyi bastigini gostermek zorundadir."*

7. **D-425 §2 · TEYİT listesi var olmayan parametreyi yakalayamaz (5 Eyl, sahada).**
   D-424 firmware boşluğunu kapatırken `/Copter/stable/` = **4.7.1** indirdi ve
   README'ye "TEYİT listesi bunun için var" yazdı. Sahada `Compare Params`:
   **`Missing 9 params`** (`SYSID_THISMAV SR1_POSITION SR1_EXTRA3 SR2_POSITION
   SR2_EXTRA3 RTL_ALT LAND_SPEED WPNAV_SPEED ARMING_CHECK`) — Copter-4.7 SI
   reformu: `SR1_*` → `MAV1_*` (ad), `RTL_ALT` 3500 cm → `RTL_ALT_M` 35, `WPNAV_SPEED`
   300 cm/s → `WP_SPD` 3 m/s (300 kalırsa **300 m/s**), `ARMING_CHECK` → `ARMING_SKIPCHK`
   (**anlam ters**). Kayıt: *"TEYIT listesi dort parametrenin ANLAMINI kontrol eder —
   var olmayan dokuz parametreyi yakalayamaz. Yani D-424, kendi onarimini olcmeden
   kapatti."* `test_faz_b_pixhawk_sablon.py` (12) dosyanın **iç** tutarlılığını
   kilitler, firmware uyumunu ölçmez (ölçemez — kart yoktu). Kapanış: 4.7'ye port
   **edilmedi**, sürüm **4.5.7'ye sabitlendi** (`scripts/pixhawk_firmware_indir.py`
   `SURUM = "stable-4.5.7"`, `firmware-version.txt` `4.5.` ile başlamazsa çıkış 2;
   indirilen `arducopter.apj` 1.585.371 B, board_id 56, git 2a3dc4b7);
   `tests/test_pixhawk_firmware_yolu.py` +4 (`SurumKilidiTests`). Saha ölçümü 15:08:
   `ArduCopter V4.5.7 (2a3dc4b7)` · `Frame: QUAD/X` · `PreArm: Check frame class`
   kayboldu (D-426 §1). Kural: *"beyan edilen bagimlilik ZORLANIR"* — "kararlı
   sürüm" bir sürüm değil, bugünkü karardır.

Ek olarak, **her ölçüm betiğinde vakum kapıları** vardır. Örnek (T99,
`results/t99_uretim_imzasi/olcum_20260903.json`): `V1_vakum_yok = true`
(araç maskesi gerçekten dolu — 7/260 karede 252–1787 px), `V3_tek_cikarim = true`
(kare başına 1 segmentasyon çağrısı, sayaçla), `V4_determinizm = true`.
🔴 Aynı ölçümün dürüstlük notu: ilk duman koşumunda (8 kare) V1 **düşmüştü**,
tam kümede geçti — *"küçük örnekle 'vakum' hükmü verilseydi yanlış olurdu."*

### 4.2.5 Bu dördünün ürettiği rapor kuralı

| # | kural | bu bölümde nerede işliyor |
|---|---|---|
| 1 | Her sayı bir artefakttan gelir (dosya yolu + üreten betik) | §4.14 Kanıt dizini |
| 2 | `ÖLÇÜLEMEDİ ≠ GEÇTİ` | §4.13 Kalan test borcu |
| 3 | Geçilmeyen kapı geçilmedi diye yazılır | §4.8.2 |
| 4 | Sentetik ölçüm saha başarımı diye sunulmaz | §4.8.1 kapsam uyarısı |

### 4.2.6 Test altyapısının nihai hâli — koşum ortamı ve fikstürler

Yönergenin istediği "test altyapısı gereksinimlerinin nihai hâli" bu projede
donanım öykünücüsü değil, **gerçek kütüphaneler üzerine kurulan fikstürler**
demektir. Her biri depoda durur ve koşulabilir.

| altyapı | ne sağlar | nerede |
|---|---|---|
| Tek yorumlayıcı | tüm kapılar aynı ortamda koşar; çıplak `python` Windows Store saplaması olduğu için kullanılmaz | `O:\navitas-local-train\venv\Scripts\python.exe` |
| Sahte Pixhawk | gerçek MAVLink çerçevelerini (HEARTBEAT + GLOBAL_POSITION_INT + EXTENDED_SYS_STATE) UDP'ye basar | `scripts/sahte_pixhawk.py` |
| SiK köprüsü | iki `serial_for_url("socket://…")` ucunu karşılıklı pompalayan TCP röle; çift yönlü ACK turunu mümkün kılar — tek uçlu `loop://` kılmaz | `tests/test_p2_seri_hat.py` |
| Kuru koşu fikstürü | kamera ve model halkalarının donanımsız koşulması | `data/kuru_kosu_fikstur/` · `results/saha_kuru_kosu_20260903_120254/ozet.json` |
| Mutant koşucusu | kapı takımına uygulanan bozmaların otomatik koşumu ve ham log'u | `results/faz_b_oncesi/ekransiz_denetim/mutant_kos.py` |
| Loopback İKA | gerçek telsiz yokken telsiz halkasının uçtan uca kapatılması | `scripts/saha_kuru_kosu.py` |

⚠ **Bu altyapının kapsamadığı dört şey:** gerçek RF, gerçek Pixhawk, gerçek
Jetson, gerçek arena. Dördü de §4.13.1'de kalem olarak durur ve hiçbiri
"fikstürde geçti" diye kapatılmamıştır.

⚠ **Beşinci sınır (D-427, 5 Eylül):** bu altyapı **YKS ile aynı makinede** koşar;
`comms/test_comms.py` üretim portlarına (5005/5006) bind ettiği için YKS açıkken tam
suit koşamaz (§4.1.3, T209). Sahada tam suit ancak YKS kapatılarak koşulur.

---

## 4.3 Sensör gereksinimleri, sensör yerleşimleri, test takvimi ve detaylı test zaman bütçe planlaması · `Y-4-M03`

> *Yönerge: "…testlerde kullanılacak sensör gereksinimleri, sensör yerleşimleri,
> test takvimi ve detaylı test zaman bütçe planlaması raporda sunulmalıdır."*

### 4.3.1 Sensör gereksinimleri

FDA görev test aracının (çoklu rotor) karar zincirini besleyen sensörler ve her
birinin bugün **hangi kapıya** bağlı olduğu:

| sensör | ne besler | bugün bağlı olduğu kapı |
|---|---|---|
| Raspberry Pi HQ (IMX477) kamera | görüntü işleme, rota tespiti | §4.8.1 kabul kapıları (**sentetik** küme) · köprü dayanıklılığı §4.10.1 |
| Pixhawk 6C iç IMU | uçuş kontrolü, `VIBE` kaydı | kapı yok — kalibrasyon ve kabul §4.6 / §4.4 |
| Holybro M9N GNSS | konum, `GLOBAL_POSITION_INT` | §4.9.1 kapı G1 (irtifa 30,0 ± 0,05 m; konum 1e-6 derece) — **sahte Pixhawk akışında** |
| Uçuş kontrolcüsü `EXTENDED_SYS_STATE` türevi | iniş kanıtı (`yerde_mi`) | §4.9.1 G3b/G4 · §4.9.4 T207 akış isteği |
| Pitot tüpü | **FDA görev test aracında YOKTUR** — çoklu rotor hava hızı sensörü taşımaz; pitot yarışma final aracının (sabit kanat) kalemidir | kapsam dışı (bu araçta) |

### 4.3.2 Sensör yerleşimleri

**BEYAN GEREKLİ (insan):** her sensörün araç üzerindeki fiziksel yerleşimi —
GNSS direği yüksekliği, pusula ile güç kablosu arasındaki ayrım, kamera bakış
açısı ve titreşim yalıtımı, telsiz anten yönelimi. Montaj 5–19 Eylül'de
yapılacak; yerleşim ölçüsü ve fotoğrafı bu alt bölüme girecektir.

### 4.3.3 Test takvimi — planlanan uçuş test kapıları (6–19 Eylül)

| adım | ne | kapı |
|---|---|---|
| 3.1 | İlk hover (Stabilize/AltHold, 2–3 m, 2 dk) — pervaneler ilk kez takılır | log `VIBE`, EKF yeşil, kırım yok |
| 3.2 | Loiter + kısa Auto (30 m) + geofence; **iniş kanıtı canlı** | YKS'de "İNİŞ" (IHA_LANDED ACK'li) |
| 3.3 | Algı canlı: 30 m'de OPEN_ROUTE YKS'de | yanlış güzergâh **0** |
| 3.4 | Tam prova ×3 (kalkış → tarama → tespit → hakem onayı → iniş) | **≤ 10 dk**, 3 temiz prova |
| 3.5 | Sıkı prova: kapalı kutudan, kronometre, hands-off | **0 müdahale** |
| 3.6 | Sürüm dondurma (türev kaydı → commit → `--dondur` → künye commit) | künye repoda, `--dogrula` **0** |

⚠ **Tek pil (4S 10 Ah) + iMAX B6 ⇒ günde en fazla 2 uçuş.** Bu, prova sayısının
en sert kısıtıdır ve planın kendisinde yazılıdır.

### 4.3.4 Detaylı test zaman bütçe planlaması

🔴 **ÖLÇÜLEMEDİ: uçuş başına gerçek görev süresi (kalkış → tarama → tespit →
hakem onayı → iniş) ölçülmedi; ilk gerçek sayı 6–19 Eylül prova uçuşlarından
gelecektir.** Bugün elde olan tek uçuş bütçesi kısıtı yukarıdaki pil kısıtıdır
(günde en fazla 2 uçuş) ve prova kapısı **≤ 10 dk**'dır (§4.3.3, adım 3.4).

Yer tarafında **ölçülmüş** zaman bütçeleri şunlardır; karar zincirinin tazelik
penceresini (`YKS_TESPIT_TAZELIK_S = 5,0` s) bağlarlar:

| bütçe kalemi | ölçülen | nerede |
|---|---|---|
| tam test paketi koşum süresi | **390,534 s** (1896 test) | §4.1.2 |
| uçtan uca kare gecikmesi (üretim zinciri + telsiz halkası) | **p95 0,113 s** | §4.9.5 |
| model yükleme (uçuş öncesi, bütçe dışı) | **2,64 s** | §4.9.5 |
| rota üretimi, kuru koşu halkası | **31 ms** | §4.11.1 |
| hub UDP→seri gecikmesi (en kötü koşul B) | p95 **70,8 / 76,8 ms**, maks **79,7 ms** | §4.9.3 |

---

## 4.4 Ekipman kabul testleri — İHA ve İKA'da kullanılacak tüm ekipmanlar · `Y-4-M04`

> *Yönerge: "Ekipman kabul testleri kapsamında, İHA ve İKA'da kullanılacak tüm
> ekipmanların kabul testlerinin gerçekleştirilmiş olması ve elde edilen
> sonuçların raporda sunulması gerekmektedir."*

🔴 **ÖLÇÜLEMEDİ: hiçbir ekipmanın fiziksel kabul testi yapılmadı. Donanım kutusu
5 Eylül 2026'da açılacak; kabul testleri 5–19 Eylül arasında koşulacak ve
sonuçları bu alt bölüme sayıyla girecektir.**

Kabul testi bekleyen ekipmanlar ve her biri için **önceden yazılmış** kabul
kapısı aşağıdadır. Sağ sütunda bugün **hiçbir sayı yoktur**; boşluk bilerek
boştur.

| ekipman | koşulacak kabul kapısı | bugünkü sonuç |
|---|---|---|
| ~~Jetson Nano 4GB~~ **Jetson Orin Nano Developer Kit 4 GB** (6 Eylül'de kartla ölçüldü — D-431) | PT ve ONNX için p50 **ve** p95 FPS ≥ 0,61 (türetimi §4.8.2.3) | ~~**ÖLÇÜLEMEDİ** — 5 Eylül'de Jetson araca takılmadı (D-426 §4)~~ → **6 Eylül ÖLÇÜM (D-431):** genel kapı kartta **15/15 · 15/15**; `jetson_fps.py` 120 örnek: **PT 1,35/1,06 FPS · engine 1,58/1,33 FPS** ≥ 0,61 → **GEÇTİ**; 10 dk sürekli 900 örnek, gpu ≤ 56,3 °C; **ONNX HATA** (`cudaErrorNoKernelImageForDevice`) → ONNX kolu bu kartta geçmedi, ölçülemedi; engine↔pt denkliği D-303 oransal **DÜŞTÜ** → uçuş `.pt`; kamera köprüsü dosya kaynağıyla açıldı. **ÖLÇÜLEMEDİ:** CSI kamera (bağlı değil), Pixhawk MAVLink kapısı (`--kuru`: `[YOK]` `/dev/ttyACM0`). Kanıt `results/jetson_20260906/` |
| Pixhawk 6C + güç modülü (plan PM02; sahada **PM06** — BEYAN, §4.13.4) | `scripts/mavlink_dogrula.py` 3/3 · `EXTENDED_SYS_STATE` akışı (§4.9.4) | **KISMEN**: firmware 4.5.7 + parametre yükleme OLCUM (tutanak 15:08); PM06 → `POWER1` OLCUM (18:03). `mavlink_dogrula.py` kapısı **koşulmadı** → ÖLÇÜLEMEDİ (§4.13.1 #6); parametre dökümü yok (#9) |
| Holybro M9N GNSS | 3B fix ve `GLOBAL_POSITION_INT` canlı akışı (§4.9.1 G1 ölçütleri) | **KISMEN**: alıcı tanındı — OLCUM `u-blox 1 HW: 000A0000 SW: ROM SPG 5.10` (15:38). 3B fix ve akış kaydı yok → ÖLÇÜLEMEDİ |
| Raspberry Pi HQ (IMX477) | `nvarguscamerasrc` üzerinden köprü kare akışı (§4.10.1 ölçütleri) | **ÖLÇÜLEMEDİ** — 5 Eylül'de Jetson takılmadı; 6 Eylül'de köprü kartta **dosya kaynağıyla** açıldı (ÖLÇÜM, D-431) ama CSI kamera **bağlı değildi** → `nvarguscamerasrc` yolu ölçülmedi |
| 2 × SiK 433 MHz telsiz | RTT p95 < 0,2 s ve menzil (§4.5) | **KISMEN**: bağlantı BEYAN (~18:45, "tamam oldu"); RTT, kayıp ve menzil ÖLÇÜLEMEDİ (§4.5) |
| FCHUB-12S V2 · 5008 340KV × 4 · 12×10 pervane | tam yükte akım ve `VIBE` titreşim kaydı (§4.3.3 adım 3.1) | **KISMEN**: pervanesiz motor testi OLCUM (18:06); sıra/yön 4/4 BEYAN, video yok; ESC kalibrasyonu YAPILMADI; tam yükte akım ve `VIBE` ÖLÇÜLEMEDİ (pervane takılmadı). ESC künyesi sahada **"60 A V2"** ×4 (plan 80 A) — BEYAN, §4.13.4 |
| 4S 10 Ah 25C pil + iMAX B6 şarj | kapasite ve şarj çevrimi; günde 2 uçuş kısıtının doğrulanması | **KISMEN**: pil takıldı, `PreArm: Battery 1 low voltage failsafe` kayboldu — OLCUM (18:03). MP gerilimi ↔ multimetre (±0,1 V), kapasite ve şarj çevrimi ÖLÇÜLEMEDİ |
| FS-i6 kumanda + FS-iA6B alıcı | menzil ve failsafe davranışı (§4.5, §4.12) | **KISMEN**: bind BEYAN (16:18); `RCInput: decoding IBUS(1)` OLCUM (18:03); alıcı FS-iA6B teyit (B harfi, BEYAN). Menzil ve RC failsafe ÖLÇÜLEMEDİ (§4.5, §4.12) |
| İKA ekipmanları | 🔴 **gerçek İKA motor sürücüsü YOKTUR** (R12/T149); İKA ekipman listesi henüz kapalı değildir (§4.11) | ekipman seçilmedi |

Fiziksel künye teyidi §4.13.4 madde 1'de **BEYAN GEREKLİ** olarak durur; 5
Eylül'de ESC ve güç modülü plandan **farklı** çıktı (D-426 §3), etiket
fotoğrafı gelmedi.

---

## 4.5 Kumanda ve telemetri menzil testleri · `Y-4-M05`

> *Yönerge: "…kumanda ve telemetri sistemlerine yönelik sahada gerçekleştirilen
> menzil testlerinin sonuçları paylaşılmalıdır."*

🔴 **ÖLÇÜLEMEDİ: menzil (metre), paket kaybı ve RTT ölçülmedi. Kapı RTT
p95 < 0,2 s; ölçüm aracı `scripts/sik_rf_olc.py`, 5 Eylül'de koşulmadı.**

**5 Eylül 2026'da olan** (`REVIEW_LOG.md` D-426 §1) — menzil ölçümü **değildir**:

| ne | tür | kanıt |
|---|---|---|
| SiK çifti bağlandı (~18:45) | BEYAN | "tamam oldu" — RTT, kayıp ve mesafe kaydı yok |
| FS-i6 ↔ FS-iA6B bind (16:18) | BEYAN | "led sabit yanıyor" |
| Kumanda çerçevesi Pixhawk'ta çözülüyor (18:03) | OLCUM | `RCInput: decoding IBUS(1)` — mesafe kaydı yok |

"Bağlandı" bir menzil sayısı üretmez; iki bağlantı da mesafe kaydı olmadan
geldi. Menzil ölçümü uçuş testleriyle birlikte yapılacaktır (§4.3.3).

**Menzilin YERİNE GEÇMEYEN, bugün elde olan şey:** taşıyıcı katmanın gerçek
`pyserial` bayt akışında koştuğu ölçüm (§4.9.2) ve hub gecikmesi (§4.9.3).
İkisi de kablo ya da `socket://` üzerindedir; RF yoktur.

🔴 DDR'de yazılan *">%98 paket başarımı, 300 m"* iddiasının bugün **hiçbir
kanıtı yoktur** (R20, `results/sartname_bosluk/rapor.md`). Bu iddia menzil
ölçümü koşulana kadar bu raporda **tekrarlanmamıştır**.

---

## 4.6 IMU, pusula ve pitot tüpü kalibrasyonu kanıtları · `Y-4-M06`

> *Yönerge: "Sensör kalibrasyonunu doğrulamak için ise IMU, pusula ve pitot tüpü
> kalibrasyonlarının gerçekleştirildiğini gösteren kanıtların raporda yer alması
> beklenmektedir."*

🔴 **ÖLÇÜLEMEDİ: 5 Eylül 2026'da Pixhawk 6C ele alındı (§4.4) ama kalibrasyon
kanıtı (ekran çıktısı, `INS_*` / `COMPASS_*` parametre dökümü) yoktur.**
Yönergenin üç kalemine cevap (`REVIEW_LOG.md` D-426 §4):

- **IMU (accel + level):** BEYAN "yapıldı" — kartın gövdeye sabitlenip
  sabitlenmediği belirsiz ("bantlanmadı"); parametre dökümü alınmadı.
  **Teyit yok → ÖLÇÜLEMEDİ.** Kart sabitlendikten sonra yeniden yapılır.
- **Pusula:** **YAPILMADI.** Jetson araca takılı değildi; kalibrasyon her şey
  takılıyken, dışarıda yapılır ve Jetson takılınca **yeniden** gerekir.
- **Pitot tüpü:** **KAPSAM DIŞI** — FDA görev test aracı çoklu rotordur, hava
  hızı sensörü taşımaz (aşağıdaki tablo).

| kalibrasyon | hangi araçta | bugünkü kanıt |
|---|---|---|
| IMU (ivmeölçer + jiroskop) | FDA görev test aracı (çoklu rotor) | 5 Eylül: BEYAN "yapıldı", kart sabit değildi, döküm yok → **ÖLÇÜLEMEDİ** (D-426 §4) |
| Pusula (manyetometre) | FDA görev test aracı (çoklu rotor) | 5 Eylül: **YAPILMADI** (Jetson takılı değil; D-426 §4). Kapı: ofset < 300 (`SAHA_HAZIRLIK_PLANI_20260903.md` §2.4) |
| Pitot tüpü | 🔴 FDA görev test aracında **pitot tüpü yoktur** — çoklu rotor hava hızı sensörü taşımaz. Pitot, yarışma final aracının (sabit kanat + mancınık) kalemidir ve o araç **henüz üretilmemiştir**. | kapsam dışı (bu araçta) |

⚠ Pixhawk parametrelerinin kendisi **repo dışıdır** (R17). Kalibrasyon sonrası
parametre dökümü `config/pixhawk/` altına kanıt olarak alınacaktır
(§4.13.1 kalem 9). 5 Eylül'de döküm **alınmadı** (D-426 §4); 6 Eylül 20:22 dökümü
`config/pixhawk/arducopter_fda_20260906.param` repodadır ve accel/pusula ofsetlerini taşır (D-428 §1, §5g;
`config/pixhawk/README.md` §1 adım 6). Şablon dosyası
`config/pixhawk/arducopter_fda.param` kalibrasyon değeri **içermez**
(README §2: kalibrasyonlar parametre dosyasında yoktur, dosya bunları ezmez).

**BEYAN GEREKLİ (insan):** kalibrasyonun yapıldığı tarih, kullanılan yer
istasyonu yazılımının adı ve sürümü, kalibrasyon sonrası `COMPASS_*` ve `INS_*`
parametre dökümü. 5 Eylül accel kalibrasyonu için: kartın o anda sabit olup
olmadığı (D-426 §4 "bantlanmadı") — sabit değildiyse kalibrasyon yeniden.

---

## 4.7 Görev icra simülasyonu · `Y-4-M07`

> *Yönerge Bölüm 4, Bölüm 3.3.3'teki simülasyonun **aynısını** ister: İHA ve
> İKA'nın üç boyutlu CAD modelleriyle sanal görev icrası (kalkış → görüntü
> işleme ile rota tespiti → verinin İKA'ya aktarılması → İKA'nın otonom
> sürüşü), otonom karar verme **başarı oranları**, **sanal görev süresi**,
> sistem tepkileri **grafiklerle** ve ekran kaydı videosunun **linki**.*

**Çapraz atıf — burada tekrarlanmaz.** Bu gereksinimin sahibi **Bölüm 3.3.3**
(`Y-3.3.3-M01`, `Y-3.3.3-M02`, `Y-3.3.3-M03`) olup Bölüm 4 aynı çalışmayı ikinci
kez yazmaz.

🔴 **Bugünkü durum, Bölüm 3.3.3 ile birebir aynıdır: yönergenin istediği CAD
modelli görev icra simülasyonu çıktıları — başarı oranı, sanal görev süresi,
grafikler ve ekran kaydı videosu linki — bu raporda YOKTUR.**

Dürüstlük notu: depoda bir Gazebo simülasyon ağacı **vardır**
(`simulation/scripts/` altında `mission_demo.py`, `ika_nav.py`,
`iha_flight.py`, `drive_ika.py`, `score.py`). Bu bölümün ölçüm defterinde o
ağaçtan gelen tek kayıt **D-370**'tir ve o da bir simülasyon başarımı değil,
**ölçen aracın kendi kusurudur**: `simulation/scripts/ika_nav.py` tamamen
CRLF olduğu için mutasyon betiğinin deseni hiç uygulanmıyordu (§4.2.2).
Yani simülasyon ağacından bu rapora giren **hiçbir başarı sayısı yoktur**.

⚠ Bu bölümdeki sentetik arena ölçümleri (§4.8.1) **görev icra simülasyonu
değildir**: CAD modeli, kalkış-iniş ve İKA otonom sürüşü içermez; yalnız
algı–karar zincirini dondurulmuş bir kare kümesi üzerinde ölçer. Sentetik kare
kümesi görev icra simülasyonu diye sunulmamıştır.

---

## 4.8 Görüntü işleme performansı — test sonuçları ve doğruluk matrisleri · `Y-4-M08`

> *Yönerge: "Görüntü işleme performansı, rota tespiti için kullanılan yapay zekâ
> veya görüntü işleme modelinin yarışma sahasına benzer koşullarda (farklı ışık
> açıları, gölgeler vb.) gerçekleştirilen test sonuçları ve doğruluk matrisleri
> raporda sunulmalıdır."*

🔴 **Yönergenin "yarışma sahasına benzer koşullar" şartı BUGÜN
KARŞILANMAMIŞTIR.** Aşağıdaki kabul kümesi sentetiktir ve farklı ışık açısı /
gölge çeşitliliği içermez; gerçek koşul ölçümü §4.13.1 kalem 1'dedir. Elde olan
gerçek görüntü, arenaya **dağılım dışı** olan DJİ uçuş kareleridir ve onlarla
alınan sonuç §4.8.2.1 ile §4.8.2.3'te **geçilmemiş eşik** olarak yazılıdır.

### 4.8.1 Kabul kapıları K0–K8 — sonuç tablosu

**Ölçüm:** `scripts/olcum/65_kabul_denetcisi.py` · verdikt JSON
`scripts/olcum/results/t63/t150_baglama_v36_kabul_verdikt.json` (1 Eylül 2026,
üretim modeli `models/navitas_seg_v36_best.pt`, üretim kipinde — HB hedeflemesi
bağlı, D-386).

| kapı | ne ölçer | eşik (ön kayıtlı) | ölçülen | sonuç |
|---|---|---|---|---|
| **K0** | körlük yok — boş maske üretmiyor | figür zemin > 0 · boş maske 0 | figür zemin **%2,66** · raw 0/67 boş · copy-paste 0/393 boş | **GEÇTİ** |
| **K1** | rota üretilen kare | ≥ 230/260 | **256/260** | **GEÇTİ** |
| **K2** | rotanın molozdan geçmesi | ≤ %15 | **6/256 (%2,3)** | **GEÇTİ** |
| **K3** | ağır moloz teması | ≤ %3 | **0/256** | **GEÇTİ** |
| **K4** | arena dışına taşma | ≤ %5 | **2/256** | **GEÇTİ** |
| **K5** | bariyer kesişimi (dik nüfus) | = 0 px | **0 px** · ölçülebilir kare 178 / bariyerli 181 | **GEÇTİ** |
| **K5A** | bariyer kesişimi (**açılı** nüfus, t189) | = 0 px | **0 px** · ölçülebilir kare 176 / bariyerli 185 | **GEÇTİ** |
| **K6** | yanlış güzergâh | ≤ %5 | **2/256 (%0,78)** — `sa_000013`, `sa_000090` | **GEÇTİ** |
| **K7** | **yayınlanan şerit** referansla aynı mı | doğruluk ≥ %95 **ve** rota üretilen ≥ 80/88 | **84/85 = %98,8** · rota üretilen **85/88** | **GEÇTİ** |
| **K8** | gerçek kare üzerinde üretim karar yolu kırılmıyor | `ZEMIN_MASKESI_SUPHELI` **dönmemeli** | zemin kaplaması **%4,44** · ret sebebi `UC_BANT_TEMAS_YOK` | **GEÇTİ** |

**Verdikt:** `true` (on kapının onu).

**Tazelik (5 Eylül):** `scripts/olcum/results/t63/` altında bu verdiktten (1 Eylül 23:30)
sonra yazılmış denetçi çıktısı yoktur (`ls -lt`, en yeni dosya
`t150_baglama_v36_kabul_verdikt.json`); tablo en güncel koşumdur, 5 Eylül'de yeni koşum
yapılmadı. Tablodaki on değer JSON'un `olcum.K1_rota … K8_zemin_kaplamasi` alanlarıyla
5 Eylül'de yeniden karşılaştırıldı: fark yok.

**Kabul kümesi ve parmak izi:** `sentetik_arena_kadraj_t66`, n = 547 dosya,
`sha256:604c037f780b7c6e8305472bb9cd11cec2212dcffbec1763f0c8b7e27e250586`
(yöntem: sıralı `rglob` üzerinden ad + boyut; içerik okunmaz). Küme değişirse
özet değişir ve kapı bunu görür.

🔴 **KAPSAM — kayıt defterinin kendi cümlesi:**
> *"ARENA ÖLÇÜMLERİNİN TAMAMI SENTETİKTİR (T66 ada kadrajı, n=260); gerçek
> ARENA karesi YOKTUR — K0..K6 SAHA BAŞARIMI İDDİA ETMEZ."*

🔴 **K7'nin referans semantiği — bir K7 düşüşü "model yanlış gördü" diye
okunamaz.** Referans, kümenin YOLO etiketinden rasterlenen maskeyle üretilir ve
**etiketsiz alan geçilemez** sayılır. Ölçüldü (D-315, `sa_000090`): model şerit
3'te **89.913 px** serbest görürken yer gerçeği **18.042 px** görüyor; engel
pikselleri ise neredeyse **aynı** (42.123 ↔ 43.781). Fark bariyeri kaçırmak
değil, **etiket kapsamı**dır. K7 düşerse önce etiket kapsamı denetlenir.

⚠ **K5 alt ölçümü ÖLÇÜLEMEDİ:** `K5_figur_bilgi_px = null`,
`K5_figur_bilgi_durum = "OLCULEMEDI"`. Bu satır verdikt JSON'ında böyle durur ve
"geçti" sayılmaz.

### 4.8.2 Geçilmeyen ve düşen kapılar — gizlenmiyor

Bu alt bölüm bilerek öne alınmıştır. Üretim modeli, kendi ön kayıtlı
eşiklerinden **ikisini geçmeden** terfi etmiştir; bunun gerekçesi, bedeli ve
eşiklerin **değiştirilmediği** aşağıda yazılıdır.

#### 4.8.2.1 🔴 v36 · gerçek-kare eşikleri GEÇİLMEDİ

**Kapı:** `scripts/olcum/142_gece_olcum.py`, DOĞRULAMA kümesi `dji/DOGRULAMA/`
= `DJI_20260822172613_0038_D`. CONTRACTS §12 gereği 0038 kareleri **eğitime ve
erken durdurmaya girmez** (test 29 + val 82 kare, iki bağımsız **kör** etiket
geçişinin uzlaşısı).

**Kanıt paketinin ham metni** (`results/fdr/GORUNTU_ISLEME_KANIT.md` §3, üreteç
`scripts/olcum/167_fdr_kanit_paketi.py`):

```text
🔴 ON KAYITLI ESIKLER GECILMEDI: ROTA >= 10 istendi, olculen 8;
MASKE_YOK <= 10 istendi, olculen 16. GECILEN: FP <= 1 (1) ve
YANLIS GUZERGAH = 0 (0). Terfi bu esikleri GECEREK degil, KULLANICI
KARARIYLA yapildi. ESIKLER DEGISMEDI ve sonraki terfileri baglar.
```

| ölçüt | eşik (ön kayıt §4b/§11) | v36 (test29) | sonuç |
|---|---|---:|---|
| ROTA | ≥ 10/29 | **8** | 🔴 **GEÇİLMEDİ** |
| MASKE_YOK | ≤ 10/29 | **16** | 🔴 **GEÇİLMEDİ** |
| FP | ≤ 1 | 1 | geçti |
| YANLIŞ GÜZERGÂH | = 0 | 0 | geçti |

val82 kolu: ROTA 30 · TP 28 · FP 2 · YANLIŞ 7.

**Terfinin gerekçesi (kullanıcı kararı, 2026-08-26 · D-293):** gerçek karede
yanlış güzergâh v35'in **15/21**'inden v36'nın **7/38**'ine indi; engel üstü
waypoint **79 → 3**.

**Terfinin bedeli — aynı kayıtta yazılı:** arena K3 **0 → 1**, K4 **1 → 4**,
K6 **5 → 7** (üçü de kapı içinde kaldı); kaplama67 0,51 → 0,42; figür zemin
0,15 → 0,04; val82 FP **0 → 2**. Ayrıca **karar kararlılığı v35'ten kötüdür**
(D-295 §3; `karar_cevrilmesi` v36 **14/260**, v35 **9/260**) ve fazlalığın
tamamı "rota VAR/YOK çevrilmesi"dir — yön fail-closed'dır ama saha
elverişliliğini düşürür. Terfi **geri alınmadı**; geri alma kullanıcı kararıdır.

**Ne DEĞİŞMEDİ:** eşikler gevşetilmedi, yeniden yazılmadı. Bir sonraki aday yine
`ROTA ≥ 10 ∧ MASKE_YOK ≤ 10 ∧ FP ≤ 1 ∧ YANLIŞ = 0` ile ölçülür. Eşiği geçmeyen
bir adayın üretime alınması **ancak insanın açık kararıyla** olur ve her
defasında CONTRACTS §12.1'e yazılır.

**Önceki üretim modeli silinmedi:** `navitas-seg-v35-512` (sha `e00f6b8e…`)
yedek adaydır ve **farklı hata yapar** — arena K3/K4/K6'da daha iyi (0/1/5).
Geri dönüş yolu açık tutulmuştur.

**Bağımsız çürütücü:** `results/gece_20260826/v7a_curut/` — üç lensli tur terfi
engeli bulmadı; bulmadığı da kayıtlıdır.

#### 4.8.2.2 🔴 Çözünürlük 640 denemesi REDDEDİLDİ (D-377)

`INFER_SIZE` 512 → 640 denendi. Karar sırası **sonuç görülmeden** yazılıydı.

| ölçüt | eşik | ölçülen | sonuç |
|---|---|---|---|
| I2 · sentetik gerileme yasağı | fark ≤ 0,02 | p_S **0,9846 → 0,7808** (fark **−0,2038**) | 🔴 **DÜŞTÜ**, 10 kat aşarak |
| I3 · en uzun körlük koşusu | **en uzun koşu < 5 s** (mutlak eşik, ön kayıt §3) | **51 kare (~51 s) → 52 kare (~52 s)** | 🔴 **DÜŞTÜ** |
| I4 · FPS bütçesi | maliyet oranı bütçe içinde | oran **1,300**; etkin 0,692 FPS (gerekli 0,472) | geçti |
| I1 · kör kare kurtarma | (karar bağlayıcı değil) | kirli havuz **%21,6** → temiz alt küme **%5,6** | — |

**HÜKÜM: RED.** FPS hiç kısıt değildi; fayda yoktu. Örüntü de yazıldı: 640 bir
**genelleme düzeltmesi değil, ezber yükselticisidir** — eğitimde görülen veride
p 0,574 → 0,703 (koşu 28 → 24), görmediği veride p 0,346 → 0,424 ama **en uzun
körlük 51 → 52** (kötüleşme). Kapıyı belirleyen en uzun koşudur.

⚠ Ön kayıt olmasaydı I1'in %21,6'sı ile I2'nin −0,204'ü aynı masaya konur ve
"kırsalda kazandırıyor, arenada biraz kaybettiriyor" diye **tartılabilirdi**.

#### 4.8.2.3 🔴 Ölçüm havuzunda sızıntı bulundu ve hüküm düzeltildi (D-376)

İlk gerçek-kare genelleme ölçümünde kullanılan havuzun **%62'si modelin eğitim
kümesindeydi**. Temizlenince:

| küme | p (geçerli rota yayınlama olasılığı) | kapsam |
|---|---:|---|
| sentetik arena (260) | **0,9846** | göreve benzer, **sentetik** |
| gerçek DJİ, **sızıntısız** (243) | **0,3457** | gerçek, arenaya **OOD** |
| yalnız 0038 (en kötü uçuş) | **0,326** | gerçek doğrulama uçuşu |

Kirli okuma daha iyimserdi. Başlık düzeltildi, kayıt **silinmedi**; çürütülmüş
kayıt üstü çizilip düzeltmesine işaret verir (D-373).

**Türetilmiş FPS eşiği buradan gelir.** Sözleşme `YKS_TESPIT_TAZELIK_S = 5,0` s
ve karar kare başınadır ⇒ `GEREKLI_FPS ≥ 1 / (5 · p)`. En kötü uçuşta
`1 / (5 × 0,326) = 0,61 FPS`. **Saha `p`'si ÖLÇÜLEMEDİ** — gerçek arena
görüntüsü yoktur; iki sayı alt/üst çerçevedir ve **arası tahmin edilmemiştir**.

#### 4.8.2.4 Düşen ve doğrulanamayan diğer ölçütler (tam liste)

| # | ölçüt | ne oldu | kayıt |
|---|---|---|---|
| 1 | P5 · H1 (toplam çevrilme ≤ %40) | **DÜŞTÜ ve düşük kaldı**; eşik gevşetilmedi, EK-1 ölçütleri bileşim görülmeden yazıldı | D-396 |
| 2 | T61 · dört iç-tutarlılık adayı | **DOĞRULANAMADI**; biri (V varyansı) zayıf ama anlamlı. Küçük örnek yanılttı | D-401 |
| 3 | T52 · ayırt edici ölçüt | **DOĞRULANAMADI**; köprü tavanı 0,55 olduğu gibi kaldı | D-398 |
| 4 | T101 · W2 kapısı | **DÜŞTÜ ve sebebi yazıldı**: iki sayı farklı popülasyon sayıyordu; *"%49,0 vs %29,6 sürüm kayması kanıtı DEĞİLDİR"* | D-400 §3 |
| 5 | D-379 · şekil kapısının "H harfini doğrulama" iddiası | **DARALTILDI**: çürütücü 17 H-olmayan şekil sentezledi, 16'sı geçti. Kapı artık *"ped yapısında"* olduğunu doğrular, **harf kimliğini doğrulamaz** | D-383 §3 |
| 6 | CONTRACTS §12.1 gerçek-kare şerit tabanı (2026-08-27, referans v3) | Kayıt *"Üretim modeli bu kapıyı geçmiyor — kullanıcı kararıyla üretimde kalır; kapı gelecek terfileri bağlar"* der. ⚠ **DOĞRULANACAK:** o satır yazıldığında üretim modeli v35'ti; v36 sonrası yeniden koşulmuş bir ölçüm bu bölümde bulunamadı | CONTRACTS §12.1 |

### 4.8.3 FP16 karar denkliği (D-375) — vakum kapatıldıktan sonra

| ölçüt | eşik | ölçülen | sonuç |
|---|---|---|---|
| F1 · zarar yönü (FP32 doğruyken FP16 yanlış şerit) | 0 | **0/260** | GEÇTİ |
| F2 · karar uyuşması | ≥ 0,98 | **631/633 = 0,9968** | GEÇTİ |

Dört uyuşmazlığın dördü sınır vakasıdır; biri **lehimize** (`sa_000216`: FP32
yanlış şerit, FP16 doğru). Kalan pay yalnız TensorRT katman birleştirmesidir ve
**Jetson'da `.engine` ile ölçülecektir** (§4.13.1).

### 4.8.4 Doğruluk matrisleri

**ÖLÇÜLDÜ — 7 Eylül 2026.** Sınıf bazlı karışıklık matrisi kör **DOĞRULAMA kümesi `test29`**
(CONTRACTS §12; 29 kare, 3840×2160) üzerinde, üretim modeli v36 (`1d1caca6…6911`) ve
üretim çalışma noktasında (CONF 0,30 · imgsz 512), **CPU** ile üretildi:
`scripts/olcum/176_piksel_karisiklik_matrisi.py` →
`results/gece_20260907/karisiklik/piksel_karisiklik_test29.{json,md,png}` (+ `kosum.log`,
`ultralytics_val/`); nöbetçi `tests/test_gece_karisiklik_matrisi.py`. Tam tablo ve kare bazlı
sayılar §3.3.4.2.8 (b)'dedir; özet — piksel düzeyi (satır tahmin, sütun yer gerçeği):

| tahmin \ yer gerçeği | zemin | engel | ETİKETSİZ |
|---|---:|---:|---:|
| zemin | **12.004.796** | 790.630 | 3.445.818 |
| engel | 3.080.875 | **92.405.877** | 11.819.510 |
| yok | 8.515.024 | 28.602.498 | 79.872.572 |

IoU zemin **0,4922** · engel **0,7400** (etiketsiz sütun FP sayılmadan; sayılarak
0,4313 · 0,6760); örnek düzeyi (`ultralytics` val, aynı CONF/imgsz): zemin 15/1/1 ·
engel 1/33/11 · arka plan 35/142/—.

Bu ölçümün 5 Eylül'e kadar **yapılmama gerekçesi** ölçülmüş bir olguydu ve hâlâ geçerlidir:
referans YOLO etiketinden rasterlenen maskedir ve **etiketsiz alan geçilemez sayılırsa**
(§4.8.1, D-315) matris etiket kapsamı eksikliğini model hatası gibi gösterir — `sa_000090`
karesinde model şerit 3'te 89.913 px serbest görürken yer gerçeği 18.042 px görür, engel
pikselleri ise neredeyse aynıdır (42.123 ↔ 43.781). 176 bu itirazı **matrisin içine alarak**
çözer: etiketsiz piksel **üçüncü, ayrı sütundur**, engele katılmaz ve IoU iki paydayla
verilir. Kümenin piksellerinin %39,6'sı etiketsizdir; bu sütun model hatası **değildir**.

Karar düzeyi ölçüm (K7: *"yayınlanan şerit referansla aynı mı"*, **84/85 = %98,8**, §4.8.1)
matrisin yerine geçmez, yanında durur. **SINIR:** `test29` arena değildir (kırsal yol; kırmızı H,
moloz, fiziki bariyer yok) ve ışık/gölge kesiti içermez — o satır **ÖLÇÜLEMEDİ** kalır. Gerçek
arena karesi geldiğinde (§4.13.1 kalem 1) aynı betik o küme üzerinde koşar.

---

## 4.9 Haberleşme testi — paket yapısı, veri hızı ve iletişim gecikmesi · `Y-4-M09`

> *Yönerge: "Haberleşme sistemi açısından ise İHA ile İKA arasında ve ayrıca yer
> istasyonu ile araçlar arasında aktarılan veri paketlerinin nihai yapısı,
> kullanılan veri hızı ve iletişim gecikmesi test sonuçları raporda
> belirtilmelidir."*

**Paket yapısının nihai hâli Bölüm 3.3.4'tedir (`Y-3.3.4-M03`); bu alt bölümde o
yapının ÖLÇÜLMÜŞ davranışı — gecikme, çerçeveleme dayanıklılığı, kayıp —
yazılıdır.** Ölçümlerin tamamı donanım gelmeden koşuldu (Faz A / Faz B).

Kullanıcının emri açıktı: *"aviyonik geldiği an yazılım için ek bir şey yapmamız
gerekmesin."* Aşağıdaki testlerin ortak sınıfı **`KOD_VAR ≠ KOŞUYOR`**: bu
katmanlar bugüne dek yalnız sahte nesnelerle sınanmıştı; `pymavlink` ve
`pyserial` venv'de **kurulu bile değildi** (2 Eylül 2026 öncesi
`find_spec` = `None`).

### 4.9.1 P1 — MAVLink katmanı ilk kez GERÇEK çerçevelerle koştu (D-387 / D-389)

`pymavlink 2.4.49` kuruldu; `scripts/sahte_pixhawk.py` gerçek MAVLink
çerçeveleri (HEARTBEAT + GLOBAL_POSITION_INT + EXTENDED_SYS_STATE) UDP'ye basar.
`tests/test_p1_canli_mavlink.py` (14 test) üretim sınıflarını bu akışa bağladı.

| kapı | ölçüt | sonuç |
|---|---|---|
| G1 | irtifa 30,0 ± 0,05 m; konum 1e-6 derece içinde | GEÇTİ |
| G2 | canlı akıştan `mpp`; `mpp_irtifadan` ile birebir | GEÇTİ |
| G3b | ON_GROUND akışında `yerde_mi(ardışık 3)` True | GEÇTİ |
| G4 | IN_AIR'de False (fail-closed) | GEÇTİ |
| G5 | yabancı sysid=99 kabul edilmez | GEÇTİ |
| G6 | donuk `time_boot_ms` yaşı yenilemez | GEÇTİ |
| G7 | yayın durunca bayatlar | GEÇTİ |

🔴 **BULGU A — pencere alçalmada kullanılmıyordu.** 10 s son tarihle, alçalan
akışta `yerde_mi` **0,002 s içinde False** döndü: ilk EXTENDED_SYS_STATE örneği
IN_AIR ise fonksiyon **anında** dönüyordu. `comms/iha_inis_yayinci.py` bunu
**tek kez** çağırır ve False'ta `exit 3` verir — **IHA_LANDED hiç
yayınlanmazdı**; şartname §2.2.5 zinciri buradan kırılırdı. İkinci ölçüm daha
kritik: araç **temas ettikten sonra** yapılan çağrı da 0,000 s'de False döndü
(sokette biriken eski IN_AIR paketleri). Yani *"önce inmesini bekle, sonra
yayıncıyı başlat"* yordamı da tek başına yetmiyordu. **Kapanış (D-389):** A1+A2
birlikte — yayıncı son tarihe kadar döngüde çağırır, `yerde_mi` IN_AIR örneğini
sayacı sıfırlayarak tolere eder. "Ardışık 3 temiz örnek" garantisi korundu.

### 4.9.2 P2 — saha taşıyıcısı (SiK seri) ilk kez GERÇEK bayt akışında koştu (D-388)

**Neden sınıfsal:** UDP datagramdır, mesaj sınırlarını korur; seri hat **bayt
akışıdır**, sınır yoktur. Çerçeveleme (`protocol.FrameReader`, newline) bu farkı
kapatmak zorundadır ve **gerçek bir bayt akışında hiç koşmamıştı**.

**Yöntem:** `loop://` tek uçludur, iki taraflı ACK turunu sınayamaz. Bu yüzden
**SiK köprüsü** kuruldu — TCP röle iki `serial_for_url("socket://…")` ucunu
karşılıklı pompalar; SiK telsizin transparan davranışının birebir karşılığı.
Her iki uç **gerçek pyserial** nesnesidir.

| kapı | ölçüt | sonuç |
|---|---|---|
| S1 | iki uçlu köprüde ACK turu tamamlanır | GEÇTİ |
| S2 | mesaj **bayt bayt** gönderilse de birebir toparlanır | GEÇTİ |
| S3 | tek okumadaki 3 çerçeve sırasıyla ayrışır | GEÇTİ |
| S4 | RF gürültüsü (araya çöp): bozuk çerçeve atılır, **sonraki geçerli çerçeve yine ayrışır** | GEÇTİ |
| **S5** | tampon ≤ 64 KiB | 🔴 **DÜŞTÜ — ölçülen 1.048.576 bayt** |

🔴 **S5 kusuru ve kapanışı.** Newline'sız 1 MiB çöp beslendiğinde iç tampon
**sınırsız** büyüyordu. SiK hattında RF gürültüsü newline üretmeden akabilir;
15 dakikalık uçuşta Jetson'da sessiz bellek büyümesi demektir. Düzeltme:
`CERCEVE_TAMPON_TAVANI = 64 * 1024` sözleşmeye girdi (madde 16 — test bu sabiti
**içe aktarır**, yeniden yazmaz), `FrameReader` **önce süzer, sonra atar**
(tersi olsaydı meşru bir çerçevenin peşindeki dev çöp o çerçeveyi de yutardı;
kapı S5d bunu kilitler), `atilan_bayt` sayacı gözlemlenebilir kılar.
**Disiplin notu:** eşik yazıldığı hâliyle düştü, düşüşü kaydedildi, kod
düzeltildi, **aynı eşikle** yeniden koşuldu.

⚠ **Bu ölçümün KANITLAMADIĞI:** gerçek RF yoktur — menzil, paket kaybı, SiK'in
kendi çerçeveleme/ECC katmanı, baud uyuşmazlığı burada yoktur. **433 MHz RF
ölçümü 5 Eylül'e ertelendi ve hâlâ ölçülmemiştir** (§4.13.1).

### 4.9.3 SiK hub — uçtan uca çoğullama ve gecikme (D-404 / D-405)

**Sorun:** Jetson'da Pixhawk seri hattı **tek sahiplidir**; üretimde üç ayrı
süreç aynı `/dev/ttyUSB0`'ı istiyordu. Çözüm: `comms/seri_hub.py` —
NAVITAS-çerçeve seri çoğullayıcı (CONTRACTS §7.5).

**Uçtan uca kapı:** `tests/test_faz_b_seri_hub.py` — YKS-seri → hub → **gerçek
`IhaKomutAlici`** → ACK → seri (sahte uç yok, gerçek bileşen).

**🔴 D-404 §7.2'de "ÖLÇÜLMEDİ" yazılan gecikme, D-405 turunda ÖLÇÜLDÜ.**
Soru: tek iplikli döngüde UDP→seri gecikmesi, paraşüt tekrar aralığının
(0,20 s) altında kalıyor mu? Ölçüm (`r2_gecikme.py`, gerçek `SerialLink`
`socket://`, hub `calistir()` ipliğinde, 50 PARACHUTE tekrarı, iki koşum):

| koşul | p50 | p95 | maks |
|---|---:|---:|---:|
| A · boş seri girişi | 10,6 / 10,0 ms | 31,0 / 31,2 ms | — |
| B · seri girişinde 20 Hz HEARTBEAT | 45,5 / 47,1 ms | 70,8 / 76,8 ms | **79,7 ms** |
| C · seri → UDP | 8,9 / 7,0 ms | 16,2 / 15,2 ms | — |
| taban (hub'sız köprü) | 1,1 / 0,5 ms | — | — |

**Hepsi 200 ms'in altında; kayıp 0/50.** ⚠ B'deki artış `socket://`
artefaktı ağırlıklıdır ve Windows zamanlayıcı granülerliği ölçüldü (1 ms UDP
zaman aşımı fiilen **15,6 ms**; boş `hub.poll` **46,8 ms**, Linux'ta ~21 ms).
**Gerçek Jetson/Linux ölçümü yapılmadı.**

**Aynı turda bulunan ve kapatılmayan hub kusurları (§4.13'e taşındı):**
derin iç içe JSON satırında `RecursionError` ile hub sürecinin ölmesi; "portu
tek başına açar" garantisinin kodda zorlanmaması (`SO_REUSEADDR` + `exclusive`
yok → çift başlatma sessiz).

### 4.9.4 T207 — akış isteği (D-406 / D-407) · KRİTİK sınıf bulgu

**Bulgu (P kolu, ArduCopter kaynağından okundu):** `EXTENDED_SYS_STATE`,
Copter-4.5 `GCS_Mavlink.cpp` STREAM_*_msgs dizilerinin **hiçbirinde yoktur** —
`SR*_EXTRA3` onu akıtmaz; yalnız `MAV_CMD_SET_MESSAGE_INTERVAL` ile akar, istek
bağlantıya özeldir ve **Pixhawk reboot'unda silinir**. Bugün bu isteği yalnız
`scripts/mavlink_dogrula.py` gönderiyordu
(`grep SET_MESSAGE_INTERVAL comms/ codes/` = **0**).
**Saha sonucu:** *pil değişimi = reboot* ⇒ `--kapi` yeniden koşulmazsa **iniş
kanıtı hiç oluşmaz** ⇒ İKA sürüş iznini asla alamaz.

**Kapanış:** `iha_inis_yayinci.AkisIstekcisi` — başta ve her 10 s
`SET_MESSAGE_INTERVAL`; 5 s EXTENDED yoksa **bir kez** KIRMIZI + anında yeniden
istek. Sabitler sözleşmeye girdi (`MAVLINK_AKIS_ISTEK_ARALIGI_S = 10`,
`MAVLINK_AKIS_SESSIZLIK_TAVANI_S = 5`, `..._HIZ_CARPANI = 2`).

**Gerçek topolojide doğrulama (D-407 §2,
`results/faz_b_oncesi/curutucu_d407/akis_istegi/r_topoloji2.py`):**

| senaryo | proxy gönderdi | yayıncı aldı | geri gelen komut | ilk gecikme | id/aralık | alarm |
|---|---:|---:|---:|---:|---|---|
| A · EXTENDED **akmıyor** (ArduCopter varsayılanı) | 25 | 25 | **4** | **0,30 s** | 511/33 @125000 µs (8 Hz) · 511/245 @500000 µs (2 Hz) | `sessizlik_uyarisi 1`, `sessiz=True` ✔ |
| B · EXTENDED akıyor | 50 | 50 | 4 | 0,30 s | aynı | alarm YOK, `sessiz=False` ✔ |

`ertelenen: 0`. **Tasarım tuzağı (ölçüldü):** pymavlink `udp:` sunucu kipinde
akran görülmeden `write` hiçbir şey göndermez **ve hatayı yutar** — istek bu
yüzden akran görülene dek ertelenir.

### 4.9.5 Uçtan uca kare gecikmesi (D-382 / D-383)

33 ölçülen gerçek karede (+3 ısınma karesi), üretim zinciri + gerçek telsiz halkası (UDP loopback ACK):
**p95 0,113 s** — tazelik penceresinin (5,0 s) çok altında. Model yükleme 2,64 s
(uçuş öncesi, bütçe dışı).

🔴 **İlk ölçüm yanlıştı ve düzeltmesi kayıtlı:** ilk ölçümdeki ~0,46 s'nin
~0,3 s'si bir **soket zaman aşımı sabiti** çıktı (bağımsız çürütücü buldu,
D-383); düzeltme sonrası telsiz payı ~2 ms (`p50 307,6 → 2,3 ms`).
⚠ Bu hüküm **yalnız UDP loopback yapılandırmasınındır**: üretim seri
varsayılanlarıyla çevrim 1,0 s ölçülmüştü. **Seri telsiz hattı üzerinden uçtan
uca gecikme ÖLÇÜLMEDİ.**

### 4.9.6 Veri hızı ve ölçülemeyen haberleşme kalemleri

**Ölçülmüş veri hızı — yalnız MAVLink akış isteği düzeyinde.** Üretim, akışı
`MAV_CMD_SET_MESSAGE_INTERVAL` ile **kendisi ister**; gerçek topolojide geri
gelen komutlar **511/33 @125000 µs (8 Hz)** ve **511/245 @500000 µs (2 Hz)**
olarak ölçüldü (§4.9.4). Jetson tarafında `--streamrate 8` systemd biriminde
kilitlidir; silindiğinde kapı K1 düşer (mutant tablosu, §4.2.2).

🔴 **ÖLÇÜLEMEDİ: SiK telsiz hattının gerçek etkin veri hızı, paket kaybı ve
menzili ölçülmedi; ölçüm 6–19 Eylül'dedir (§4.5).** 5 Eylül durumu: SiK çifti
Mission Planner'a **bağlandı** — BEYAN, sözlü "tamam oldu" (`REVIEW_LOG.md:29828`,
D-426 §1). RTT, kayıp ve menzil için `scripts/sik_rf_olc.py` **koşulmadı**;
"bağlandı" bir ölçüm değildir. Aynı gün kumanda hattı için bir ÖLÇÜM satırı
vardır (`RCInput: decoding IBUS(1)`, §4.10.4) — o RC hattıdır, telemetri değil.

🔴 **ÖLÇÜLEMEDİ: seri telsiz hattı üzerinden uçtan uca gecikme ölçülmedi.
Bugünkü p95 0,113 s hükmü yalnız UDP loopback yapılandırmasınındır; üretim seri
varsayılanlarıyla çevrim 1,0 s ölçülmüştü (§4.9.5).**

🔴 **ÖLÇÜLEMEDİ: İHA↔İKA hattı iki gerçek araç arasında hiç koşulmadı. Bugünkü
kanıt loopback İKA'dır (§4.11.1) ve gerçek İKA motor sürücüsü yoktur
(R12/T149).**

### 4.9.7 Uçuş komut hattı YKS → İHA — ACK kaynağı, terminal durum, saat ofseti, tekrar savunması (D-419 §1 / D-422)

Bileşen `comms/iha_komut_alici.py`; Jetson'da koşan dosya paket kopyasıdır
(`jetson_paket/kod/iha_komut_alici.py`, `cmp` bayt-eş, 5 Eylül). Karşı uç
`scripts/sahte_pixhawk.py` (gerçek ArduPilot gibi component **1** ile ACK basar).

**Teşhis ikili aramayla ölçüldü, tahmin edilmedi (D-419 §1, `REVIEW_LOG.md:28989-29008`):**

| deney | ne kapatıldı | sonuç |
|---|---|---|
| A | K-3 ACK bileşen kapısı | `Ran 23 tests ... OK` — iki düşük de kalktı |
| B | K-2 sonuç önbelleği | hâlâ 2 düşük |
| C | K-1 yaş kapısı | hâlâ 2 düşük |

Kök neden alıcının kendi logundaydı: `COMMAND_ACK yabanci component=1
(beklenen 3) — yok sayildi`. Eski kod `COMMAND_ACK.srcComponent`ı (kim
cevapladı) `COMMAND_LONG.target_component` ile (kime gönderdim) eşitliyordu.

| kapı | kusur | kapanış (kapı kaldırılmadı) |
|---|---|---|
| K-3 ACK kaynağı (`REVIEW_LOG.md:29009`) | ACK basan bileşen yanlış alanla karşılaştırılıyordu | `_ack_basabilen_bilesenler` (`comms/iha_komut_alici.py:523`): {`MAVLINK_BELIRTILMEMIS_COMPONENT` = 0 (`:111`), `MAV_COMP_ID_AUTOPILOT1`, `target_component`}; gimbal/kamera/companion (ör. 154) reddedilir |
| K-2 terminal durum (`:29015`) | MAVLink'e hiç ulaşmamış teşebbüs (`mav is None`, hedef bilinmiyor, aktarım istisnası) anahtarı kalıcı zehirliyordu | `_komut_sonuclari[anahtar] = bool(kabul)` ACK beklemesi **döndükten sonra**; ACK zaman aşımı **bilerek terminal** (tel çıkmıştır); bunu kilitleyen `test_timeout_ve_ret_duplicate_gecikmis_eylem_uretmez` değiştirilmedi |
| K-1 saat ofseti (`:29026`) | `ham = simdi − damga` iki saatin farkı + gecikme; yaş ham farkla ölçülüyordu | kayan penceredeki **en küçük** ham fark = ofset kestirimi (gecikme ≥ 0); `yas = ham − ofset`. Sabitler `comms/iha_komut_alici.py:149,155,160`: `KOMUT_SAAT_OFSETI_EN_AZ_ORNEK = 2`, `KOMUT_SAAT_OFSETI_PENCERESI_S = 60.0`, `KOMUT_SAAT_SAPMA_TAVANI_S = 30*60` |

**D-422 — sapma 30 dk'yı aşınca kritik komutlar KALICI red (D-421 §11'de açık
bırakılmıştı).** `_saat_ofseti_ornekle` sapma tavanını aşan örneği atıyordu;
ofset bilinmezken örnek = iki saatin farkı, dolayısıyla öğrenmek için gereken
örneğin kendisi eleniyordu. RTC pilsiz Jetson sabit bir epoch'a açılır (1970 ya
da son kapanma). Teşhis gerçek nesneyle yeniden üretildi (`REVIEW_LOG.md:29449-29451`, birebir):

| senaryo | ARM gecti mi | MAVLink'e giden | ofset |
|---|---|---|---|
| 2 saat sapma, 20 basamak merdiven | **HAYIR** | **0** | `None` (0 ornek) |
| 1970'e acilmis Jetson (~53 yil) | **HAYIR** | **0** | `None` |
| ofset -600 s ogrenildi, sonra +600 s ILERI adim | 60,00 s **OLU** | — | 241 komut reddedildi |

Onarım (`REVIEW_LOG.md:29460-29483`): (1) tavan artık öğrenmeyi değil **kaymayı**
engeller — aday ofset bant içindeyse 2 örnek, dışındaysa **6 birbirini
destekleyen** örnek; (2) saat adımı trafikten değil **yerel** ölçülür
(`_yerel_saat_adimi`, `comms/iha_komut_alici.py:420`: `duvar_farki −
monotonik_farki`; eşik `max(KOMUT_YAS_TAVANI_S)` = 8 s'ten türetildi), adım
bulununca pencere atılmaz, düzeltilir; (3) üç görünür kayıt.
🔴 Mimarın ilk talimatı ("adım trafikten çıkarılsın") **yanlıştı** ve amele bunu
ölçerek buldu (`REVIEW_LOG.md:29484-29504`): ısrarlı bayat gönderici reddedilen
çerçeveleriyle kestirimi kendi üzerine yürütüp **10. ısrarda MAVLink'e
ulaşıyordu**; tasarım atıldı, "REDDEDİLEN ALTERNATİF" olarak modül başlığına
yazıldı ve `test_adim_kaniti_TRAFIKTEN_cikarilmaz_israrli_BAYAT_gonderici_yuruyemez`
(`tests/test_iha_komut_saat_ve_tekrar.py:684`) ile kilitlendi.

**Tekrar (replay) savunması — ölçülen şey Pixhawk'a giden `COMMAND_LONG`
sayısıdır (`REVIEW_LOG.md:29511-29516`, birebir):**

| senaryo | COMMAND_LONG |
|---|---|
| ayni (oturum,seq,cmd) 40 kez | **1** |
| 10 dk saklanip 500 kez | **1** |
| yeni `seq`, damga eski (200 israr) | **1** |
| yeni `oturum` + yeni `seq`, damga eski (200 israr) | **1** |
| NTP adimi sonrasi eski cerceve | **0** |
| bayat damgali PARACHUTE (200 israr) | **1** |

Eski modül (`git show HEAD:comms/iha_komut_alici.py`) yan yana yüklenip beş
senaryoda kıyaslandı: sonuç birebir aynı. **Dürüstçe yazılan takas
(`REVIEW_LOG.md:29520-29542`):** replay anahtarı zayıflamadı ama tazelik tavanı
**genişledi** — soğuk alıcıda (ofset öğrenilmemiş ve saldırgan tek konuşan)
yakalama yaşı tavanı 1800 s'den sınırsıza çıktı, saldırgana maliyet 3 → 7 paket.
Kabul gerekçesi ölçüldü: meşru YKS bir kez konuşunca delik kapanır (2 saat ve
1 gün bayat için 40/40 red, eski ve yeni kodda); delik zaten vardı (≤ 10 dk
bayat çerçeve eski kodda 3. tekrarda geçiyordu); saat kapısı zaten sahtecilik
savunması değildi — taze damgalı, uydurma `oturum`lu yeni çerçeve tek pakette
geçer (eski ve yeni kodda); gerçek çevre `izinli_kaynak` adres pinidir ve
değişmedi.

Onarım sonrası (`REVIEW_LOG.md:29547-29549`, birebir):

| senaryo | once | sonra |
|---|---|---|
| 2 saat sapma | hic gecmiyor | **7. basamakta** geciyor (ofset -7200,0) |
| 1970 Jetson | hic gecmiyor | **7. basamakta** geciyor (ofset -1699999900,0) |
| tavani asan ILERI adim | **60,00 s olu** | **0,25 s** (adimdan sonraki ILK komut geciyor) |

ACK'li tekrar merdiveni 8 × 0,25 s olduğundan operatörün tek basışı yeter
(~1,75 s); kestirim tam sınırda oluşur (7/8) — cuma kartına "tek basış geçmezse
ikinci kez bas" notu düşüldü.

**Kapı ve mutasyon (`REVIEW_LOG.md:29050-29055`, `29555-29568`):**
`tests/test_faz_b_iha_komut_alici.py` **23 OK** (önce 2 düşük);
`tests/test_iha_komut_saat_ve_tekrar.py` **18 → 42 test** (`git diff -U0`: silinen
assert 0, assert 71 → 140). Mutasyon: eski mutlak tavan geri konuldu → **17 test
düştü**; `_yerel_saat_adimi` öldürüldü → **5 test düştü**; dosya `cmp` bayt-eş
geri yüklendi, ayna bayt-eş. Regresyon: 12 test dosyası / 212 test OK; genel
kapı 15/15 · 15/15.

⚠ **Bu ölçümlerin KANITLAMADIĞI:** hat gerçek Pixhawk'a hiç bağlanmadı; 5
Eylül'de Pixhawk yalnız Mission Planner'a bağlıydı (§4.10.4). Gerçek
`COMMAND_ACK` bileşen kimliği ve Jetson'un RTC'siz açılış saati **ÖLÇÜLEMEDİ**.

---

## 4.10 Sistem üzerinde gerçekleştirilen tüm yer testleri · `Y-4-M10`

> *Yönerge: "Bunlara ek olarak, sistem üzerinde gerçekleştirilen tüm yer testleri
> raporda sunulmalıdır."*

⚠ **Kapsam dürüstlüğü:** §4.10.1–§4.10.3'teki yer testlerinin tamamı **yazılım
yer testidir** (3–4 Eylül, donanım yok). §4.10.4 ilk **donanım yer testidir**
(5 Eylül; Pixhawk 6C tezgâhta, Mission Planner'a bağlı): pervanesiz motor testi
koşuldu (`starting motor test` → `finished motor test`, ÖLÇÜM). O tutanakta
(D-426) pervaneli çalıştırma, titreşim kaydı ve ARM denemesi **yoktur**; araç
uçuş yapılandırmasında monte değildir ve Jetson takılı değildir (§4.13.1 kalem
4; `REVIEW_LOG.md:29867`). Donanım-öncesi ölçümlerin ortak sınıfı
(`KOD_VAR ≠ KOŞUYOR`) §4.9'da yazılıdır ve §4.10.1–§4.10.3 için geçerlidir.

### 4.10.1 Kamera köprüsü — dayanıklılık (D-407 §2)

Jetson'ın CSI kamerası (IMX477) `nvarguscamerasrc` ister; üretim çıkarım
süreci ise sistem Python'undan ayrıdır. Köprü (`scripts/kamera_koprusu.py`,
Python 3.6 uyumlu — 6 Eylül'de kartın sistem Python'u **3.12** çıktı, uyum kısıtı fiilen gerekmedi; köprü kartta sistem Python 3.12 + cv2 4.6 ile dosya kaynağında açıldı, CSI kamera bağlı değildi → ÖLÇÜLEMEDİ, D-431) MJPEG olarak servis eder.

| ölçüm | sonuç |
|---|---|
| bellek sızıntısı (50/150/300 kare) | izlenen bellek **0,48 MB sabit** (tepe 0,74 MB), RSS ~72 MB sabit, iplik 4 |
| 40 ardışık istemci | iplik 4 → 3, `istemci_sayisi=0`, `dusen_kare=0`, `kodlama_hatasi=0`, KIRMIZI log **0** |
| istemci kopma senaryoları (RST, FIN, okumayan istemci, 3'ten 2'si koparken) | hepsi başarılı, üretici yaşadı |
| Python 3.6 uyumu | çürütme **başarısız** (kod doğru): "bulunan" 3.7/3.9 API'leri dokstringdeki **yasak listesi metniydi** |

⚠ **Test vakumu (KÜÇÜK, AÇIK):** K5 kapısı yalnız **söz dizimi** bakıyor
(walrus/posonly/match); **API adı** yakalanmıyor. Öneri: K5'e API kara listesi.

### 4.10.2 Ekransız kip (D-404 §2 / §8)

**Bloker:** `run_camera` ve `run_video` her karede **koşulsuz** `cv2.imshow`
çağırıyordu. DISPLAY'siz Jetson'da systemd altında ilk karede `cv2.error` →
`Restart=always` döngüsü (şartname §6.2 hands-off ihlali).

**Kapanış:** `--ekransiz` bayrağı; ekransızda görsel **hiç üretilmez**.
🔴 Kritik şart: **karar yolu bayt-eş aynıdır** (Anayasa madde 15).
Bağımsız denetçi bunu doğruladı: karar yolu **6 kipte (4 video + 2 kamera) 23
kayıtlık izle birebir**; `frame_idx`/`fps_buf` artışları `continue`'lardan
öncedir. Hüküm **KOŞULLU GEÇTİ** oldu; şartı §4.2.2'deki mutant tablosunda.

### 4.10.3 Kuru koşular — `results/faz_b_oncesi/` (D-404 §4)

Her dosyanın son satırı **gerçek çıkış kodudur**.

| dosya | beklenen | ölçülen |
|---|---|---|
| `jetson_baslat_kuru_udp.txt` | exit 0; 14550/14551/14552 uçları, `/dev/tty` ile hiçbir tüketici yok | **exit 0** |
| `jetson_baslat_kuru_sik.txt` | exit 0; hub satırı `--port /dev/ttyUSB0 --bind 127.0.0.1:5100 --tuketici 127.0.0.1:5007` | **exit 0** |
| `jetson_baslat_kuru_udp_EKSIK_beyan.txt` | **fail-closed**: `[EKSIK] YKS_IP`, `[EKSIK] IKA_IP` | **exit 3** |
| `saha_baslat_komutlar.txt` | YKS satırında `--iha <JETSON_IP>:5007` (D-403 KRİTİK-1) | **exit 0** |
| `cuma_kontrol/muhur_dogrula.txt` | künye yok → "DONDURULMADI" | **exit 3** |
| `seri_hub_help.txt` | CLI `--port --baud --bind --tuketici --log-aralik` | **exit 0** |

**4 Eylül yeniden koşumu** — `results/faz_b_oncesi/cuma_kontrol/*_0904.txt`.
4 Eylül'de ~2200 satır kod değişti (Codex + altı worktree birleştirmesi); 3
Eylül ölçümleri geçersiz sayıldı ve kart baştan koşuldu
(`results/faz_b_oncesi/CUMA_KONTROL_KARTI.md` §A; D-421 önsöz). Ana makine
Windows'tur: `[YOK]` satırları Jetson'daki kullanıcı/yorumlayıcı/seri port
denetimleridir ve burada beklenen sonuçtur.

| dosya (4 Eylül) | ölçülen | son satır / çıkış |
|---|---|---|
| `jetson_udp_0904.txt` (01:01) | KIP=udp; 4 birim ExecStart: çoğullayıcı `--streamrate 8 --out udp:127.0.0.1:14550/14551/14552`; `rpi_inference.py --camera --ekransiz … --yks-hedef 192.168.1.10:5005 --ika-hedef 192.168.1.20:5006`; `iha_komut_alici.py --bind 0.0.0.0:5007 --izinli-kaynak 192.168.1.10:5005`; paket `[VAR]` 3/3, `mavproxy.py [YOK]`; `[TAM] beyanlar tam` | `KURU SONUC: eksik (beyan: tam · [YOK]: 7) — gercek kosum DURUR (cikis 3)` |
| `jetson_sik_0904.txt` (01:01) | KIP=sik; hub `--port /dev/ttyUSB0 --baud 57600 --bind 127.0.0.1:5100 --tuketici 127.0.0.1:5007`; üç tüketici `127.0.0.1:5100`'e; paket `[VAR]` 4/4 | `KURU SONUC: eksik (beyan: tam · [YOK]: 9) — gercek kosum DURUR (cikis 3)` |
| `saha_baslat_0904.txt` (01:00) | YKS FDA: `yks_gui.py --fda --ika <IKA_IP>:5006 --iha <JETSON_IP>:5007 --kamera-url http://<JETSON_IP>:8080`; SiK: `--serial COM5 --baud 57600` | `exit=0` |
| `paket_0904.txt` (01:01) | paket aynası **18** `[JETSON_PAKET]` satırı (`seri_hub.py`, `mavlink_dogrula.py`, `kamera_koprusu.py` dâhil) | — |
| `bellek_0904.txt` (02:45) | saha belleği: git `7a0bdac`; `jetson_paket` 343 dosya 1011,1 MB; `wheels` 51 dosya 257,3 MB; TOPLAM ~1268,5 MB; MANIFEST **405** dosya | — |
| `muhur_0904.txt` (01:01) | `[DONDURMA] DONDURULMADI: kunye yok` | mühür henüz basılmadı (beklenen) |
| `kuru_kosu_0904.txt` (01:00) | §4.11.1'de ham | `exit=1` (kopuk halka varken 0 dönmez: `scripts/saha_kuru_kosu.py:1251,1256`) |
| `tam_suit.txt` (09:58) | `Ran 2104 tests in 390.131s` · `OK (skipped=3)` — dosya 3 Eylül'deki 1896'lık koşumun üzerine yazıldı (§4.14 satır 2 o anın sayısıdır) | `exit=0` |

⚠ 5 Eylül'de tam suit **2138** testle üç kez koşuldu (`REVIEW_LOG.md:29893-29895`,
D-427): YKS açıkken **1 FAIL** (`test_p8_sim_katmani.test_comms_loopback_gecer`,
`WinError 10013`), YKS kapalıyken **OK**. Sebep ortamdır: `comms/test_comms.py:35-36`
üretim portları 5005/5006'ya bind eder; kod değişmedi, değişen tek şey YKS'nin
açık olmasıydı. Kuyruk: T209 (ephemeral port). Bu bir kod düşüğü değildir ama
"YKS açıkken tam suit yeşil" koşulu sahada sağlanamaz — bilinerek kabul edildi.

**Runbook komutları gerçekten koşuluyor (D-421 §1–§2, `REVIEW_LOG.md:29299-29350`).**
`SAHA_RUNBOOK.md` §3'ün `iha_komut_alici` satırı `--izinli-kaynak` olmadan
`error: --izinli-kaynak HOST:PORT saha komutlari icin zorunlu`, `EXIT=2`
veriyordu; blok **asimetrik** ölüyordu (birinci satır `iha_inis_yayinci`
kalkıyor, ikincisi ölüyor — sahada zincir yarı canlı görünür, ARM/RTL/LAND
düğmeleri hiç ACK almaz). Bunu kilitlediği ilan edilen `tests/test_p4_runbook.py`
(22 test) sabit jeton listesiyle substring arıyordu ve **yeşildi**. Yeni kapı
`tests/test_runbook_komutlari_kosuyor.py` (**3 test**: T1 hiçbir runbook komutu
argparse tarafından reddedilmiyor · T2 ≥ 3 komut kapsamda, kusurun çıktığı komut
dâhil · T3 yer tutucu sözlüğü kapsamlı) bash bloklarındaki her depo betiği
çağrısını **koşar**. Mutasyon: bayrak runbook'tan çıkarıldı → T1 düştü; dosya
`cmp` bayt-eş. Bugünkü satır `--izinli-kaynak <YKS_IP>:5005` taşır
(`SAHA_RUNBOOK.md:93-96`). Aynı kusur sınıfının dördüncü tekrarı (D-415, D-419 §5,
sahte-kapı dedektörü, bu): **ölçüm aletinin kendisi ölçülmemişti**.

🔴 Bu koşumların **hiçbiri saha kanıtı değildir**; yalnız *"ilk koşum kör
olmayacak"* kanıtıdır.

### 4.10.4 5 Eylül — Pixhawk 6C tezgâh yer testi (D-424 / D-425 / D-426)

Sahada tek takım üyesi vardı (pilot R2 ve takım lideri sahada değildi); mimar
uzaktan yönlendirdi. **ÖLÇÜM** = Mission Planner `Messages` satırı (oturuma
birebir yapıştırıldı), **BEYAN** = sözlü bildirim. Kural: sahadan gelen "oldu"
kanıt değildir, yapıştırılan satır kanıttır (D-426 §6, `REVIEW_LOG.md:29879-29886`).

**Kronoloji (`REVIEW_LOG.md:29819-29829`):**

| saat | adım | tür | kanıt satırı |
|---|---|---|---|
| 14:52 | ArduCopter flash — MP ikonu **4.7.1** yükledi | ÖLÇÜM | `ArduCopter V4.7.1 (dbe79216)` · Compare Params: `Missing 9 params` |
| 15:08 | **4.5.7'ye yeniden flash**, `arducopter_fda.param` yüklendi | ÖLÇÜM | `ArduCopter V4.5.7 (2a3dc4b7)` · `Frame: QUAD/X` · `PreArm: Check frame class` kayboldu |
| 15:38 | GPS tanındı | ÖLÇÜM | `u-blox 1 HW: 000A0000 SW: ROM SPG 5.10` |
| 16:18 | RC bind (FS-i6 ↔ FS-iA6B) | BEYAN | "led sabit yanıyor" |
| 18:03 | RC protokolü çözülüyor | ÖLÇÜM | `RCInput: decoding IBUS(1)` |
| 18:03 | pil takıldı, PM06 → POWER1 | ÖLÇÜM | `PreArm: Battery 1 low voltage failsafe` listeden kayboldu |
| 18:05 | emniyet düğmesi fiziksel çözüldü | ÖLÇÜM | `PreArm: Hardware safety switch` kayboldu; öncesinde 12× `Motor Test: Safety switch` |
| 18:06 | **pervanesiz motor testi** | ÖLÇÜM | `starting motor test` → `finished motor test` |
| ~18:30 | motor sırası ve yönleri 4/4 (kablo taşıma + faz değişimi sonrası) | BEYAN | video yok — **BEYAN GEREKLİ (insan)** |
| ~18:45 | SiK telemetri bağlandı | BEYAN | "tamam oldu" — RTT/kayıp ÖLÇÜLEMEDİ (§4.9.6) |
| — | uçuş modları SwC: Stabilize / Loiter / RTL | BEYAN | — |

**Firmware boşluğu sahada bulundu ve aynı gün kapatıldı (D-424 / D-425).**
Pixhawk 6C fabrikadan **PX4** ile gelir; depoda ve saha belleğinde ArduCopter
firmware dosyası **yoktu**, flash yordamı hiçbir belgede **yoktu**
(`REVIEW_LOG.md:29633-29639`). MP'nin "en son kararlı" ikonu 4.7.1 yükledi ve
`.param` dosyasının 31 parametresinden **9'u yok** çıktı (`REVIEW_LOG.md:29716-29720`:
`SYSID_THISMAV SR1_POSITION SR1_EXTRA3 SR2_POSITION SR2_EXTRA3 RTL_ALT
LAND_SPEED WPNAV_SPEED ARMING_CHECK` — Copter-4.7 SI birim reformu; `WPNAV_SPEED`
300 cm/s → `WP_SPD` m/s, `ARMING_CHECK` → `ARMING_SKIPCHK` anlam **ters**).
Karar: 4.7'ye port **edilmedi**, sürüm **4.5.7'ye sabitlendi** — mevcut
yapılandırma ölçülmüş ve kapılıdır, port edilmiş 4.7 ölçülmemiş olurdu.
Artefaktlar: `scripts/pixhawk_firmware_indir.py:74` `SURUM = "stable-4.5.7"`;
`firmware/firmware-version.txt` = `4.5.7-FIRMWARE_VERSION_TYPE_OFFICIAL`,
`firmware/arducopter.apj` **1.585.371 B**, board_id 56 (= Pixhawk6C), git
`2a3dc4b7` (`REVIEW_LOG.md:29787`; ikili depoya girmez, saha belleğindedir);
kapı `tests/test_pixhawk_firmware_yolu.py` (**10** test; `firmware/` yoksa son
test **atlanır ve söyler**). Sıra kuralı belgeye girdi: **firmware → param**,
tersi tüm parametreleri siler.

**Sahada bulunan tuzaklar (D-426 §2, `REVIEW_LOG.md:29831-29847`):** RC alıcı
`CH6`'ya takılmıştı (tek kanal PWM, Pixhawk görmez) → `i-BUS SERVO` portuna
alındı; `RC_PROTOCOLS` teşhis sırasında 4 → 1 (All) yapıldı ve **geri alınmadı**
(tercih 4 = yalnız iBUS; dökümde görülecek); emniyet düğmesi her güç kesmede
yeniden kilitlenir, `BRD_SAFETY_DEFOFF` değiştirilmedi; motor testi %5'te
dönmedi, %10–15'te döndü; PM06'nın 8 pinli kablosu `POWER1`'e (6 pin) uymadı,
6 pinli kablo bulundu, uydurma adaptör yapılmadı.

**Künye üç yerde plandan farklı çıktı (BEYAN, D-426 §3, `REVIEW_LOG.md:29848-29858`):**
ESC **"60 A V2"** ×4 (plan 80 A); güç modülü **PM06** (plan PM02); RC alıcı
FS-iA6B **teyit** (B harfi görüldü). Marka/model için **BEYAN GEREKLİ (insan)**;
Bölüm 3/5/7 künyesi düzeltilecek.

**Yapılmadı / ÖLÇÜLEMEDİ — uçuştan önce açık (D-426 §4, `REVIEW_LOG.md:29859-29870`):**

| ne | durum | rol |
|---|---|---|
| RC failsafe testi (kumanda kapat → CH3 < 975? `Radio Failsafe`?) | **ÖLÇÜLEMEDİ** — iki kez istendi, sonuç gelmedi; `.param` yorumundaki "iBUS alıcısı çerçeve basmayı keser" **varsayımdır** | R3 / R2 |
| ESC kalibrasyonu | **YAPILMADI** ("hepsi birden" yordamı verildi; ESC markası bilinmiyor) | R3 |
| parametre dökümü (5 Eylül) | **dosya YOK** (kontrol edildi) → 6 Eylül 20:22 dökümü `config/pixhawk/arducopter_fda_20260906.param` repoda (D-428 §5g) | R3 |
| pil gerilimi MP ↔ multimetre (±0,1 V) | ÖLÇÜLEMEDİ | — |
| pusula kalibrasyonu | dışarıda, her şey takılıyken — **Jetson takılı DEĞİL**; Jetson takılınca yeniden | R3 |
| accel + level | BEYAN "yapıldı" — kart sabitlenmiş miydi belirsiz; **teyit yok** | R3 |
| ESC sinyal kablosu kırmızı tel (BEC) | soruldu, cevap gelmedi | R3 |

**Uçuş kararı:** 18:5x'te gelen "uçalım" **reddedildi** (`REVIEW_LOG.md:29871-29878`):
plan "Paz 6 sabah: pusula dışarıda + ilk hover 3.1"; ESC kalibrasyonu yok;
failsafe sonucu yok; alacakaranlık; pilot (R2) planda. İlk hover kapısı (3.1):
Stabilize/AltHold, 2–3 m, 2 dk; VIBE logu, EKF yeşil, kırım yok; pervaneler
ilk kez o zaman takılır.

⚠ **Bu alt bölümün KANITLAMADIĞI:** Jetson, kamera ve NAVITAS yazılımı bu
tezgâha **bağlı değildi**; `mavlink_dogrula --kapi` gerçek Pixhawk'ta koşmadı
(§4.13.1 kalem 6 açık). Motor yön/sıra doğruluğu ve SiK bağlantısı **BEYAN**dır.

---

## 4.11 Alt sistemlerin bir arada ve yerde bütünleşik çalıştığını gösteren kanıtlar · `Y-4-M11`

> *Yönerge: "Entegrasyon öncesinde tüm alt sistemlerin bir arada çalışabildiğini
> ve yerde bütünleşik olarak çalıştırıldığını gösteren kanıtların raporda yer
> alması beklenmektedir."*

Bu gereksinimin bugünkü tek kanıtı **saha zincirinin halka halka kuru
koşumu**dur; kopuk halka gizlenmemiştir.

### 4.11.1 Kuru koşu — `scripts/saha_kuru_kosu.py`

Saha zincirinin **halka halka** sahiplik denetimi. Çıktı (ham, 3 Eylül,
`results/faz_b_oncesi/cuma_kontrol/cuma_kontrol.txt` §5; 4 Eylül yeniden
koşumu bu bloğun altındadır):

```text
  hedef_konumu   GECTI      HB saha kaynagindan alinabiliyor
  rota           GECTI      rota uretildi: yol_no=2  [31 ms]
  aktarim        GECTI      uretim yolu run_camera karari loopback IKA'ya OPEN_ROUTE olarak yazdi
  telsiz halkasi GECTI      run_camera -> KararYayinci -> loopback IKA:
                            {'open_route_alindi': True, 'heartbeat': 1, 'ack': ['ika'], 'hata': None}
  surus_izni     GECTI      IHA_LANDED saha kod yolunda uretiliyor
  motor          SAHIPSIZ   gercek motor surucusu yok; send_vel yalnizca gz subprocess'i
------------------------------------------------------------------------------
GECTI 9 · DUSTU 0 · SAHIPSIZ 1 · ATLANDI 0
KOPUK HALKALAR (1): motor
Zincir saha kosumunda TAMAMLANMAZ.
```

**4 Eylül yeniden koşumu** (ham, tam dosya;
`results/faz_b_oncesi/cuma_kontrol/kuru_kosu_0904.txt`, 01:00; çıktı dizini
`results/saha_kuru_kosu_20260904_010058/`; aynı sabah 09:52'de ikinci koşum
`results/saha_kuru_kosu_20260904_095222/ozet.json`, §4.11.2):

```text
rota_bul: [ICERIK_YOK_LETTERBOX_SUPHESI: icerik=None ile tuval letterbox gorunumlu — zemin saglamlik kapisi bu paydada olu olabilir; cagiran `icerik` gecirmeli]
Kamera acilamadi (kaynak='/dev/video7').
Kamera acilamadi (kaynak=3).
==============================================================================
SAHA KURU KOSUSU — CONTRACTS.md §11 · Gazebo YOK · donanim YOK
==============================================================================
  kamera         GECTI      kaynak parametrik ve VideoCapture'a BESLENIYOR (cihaz yolu str, indeks int olarak cozuluyor)  [2382 ms]
                            -> codes/rpi_inference.py:run_camera
  model_yukleme  GECTI      agirlik manifestten turetiliyor, --model besliyor, uyusmazlikta fail-closed ve kayit defteriyle eslesiyor  [40 ms]
                            -> codes/rpi_inference.py:load_model
  cikarim        GECTI      tek kare cikarimi tamamlandi  [2357 ms]
                            -> codes/rpi_inference.py:57
  maske          GECTI      {0,1} anahtarli maskeler uretildi  [39 ms]
                            -> codes/rpi_inference.py:60-83
  olcek          GECTI      canli telemetri bu kare icin gecerli mpp uretti
                            -> codes/rpi_inference.py
  hedef_konumu   GECTI      HB saha kaynagindan alinabiliyor
                            -> codes/rpi_inference.py (T150/D-386: goruntu= + sekil kapisi)
  rota           GECTI      rota uretildi: yol_no=2  [28 ms]
                            -> codes/rpi_inference.py:analyze_path (run_camera yolu)
  aktarim        GECTI      saha paketi haberlesme kodunu tasiyor; uretim yolu run_camera karari loopback IKA'ya OPEN_ROUTE olarak yazdi
                            -> codes/rpi_inference.py:run_camera
  telsiz halkasi  GECTI      run_camera -> KararYayinci -> loopback IKA: {'open_route_alindi': True, 'heartbeat': 1, 'ack': ['ika'], 'hata': None}
  surus_izni     GECTI      IHA_LANDED saha kod yolunda uretiliyor
                            -> comms/iha_inis_yayinci.py:386
  motor          SAHIPSIZ   gercek motor surucusu yok; send_vel yalnizca gz subprocess'i ve ika_nav simulation/ altinda
------------------------------------------------------------------------------
GECTI 9 · DUSTU 0 · SAHIPSIZ 1 · ATLANDI 0
KOPUK HALKALAR (1): motor
Zincir saha kosumunda TAMAMLANMAZ.
Cikti: O:\navitas\results\saha_kuru_kosu_20260904_010058
exit=1
```

İlk üç satır stderr'dir (`rota_bul` tanısal uyarısı; `/dev/video7` ve indeks 3
Windows'ta açılamaz — halka bunu "kaynak VideoCapture'a besleniyor" olarak
ölçer, kamera açılmasını değil). `surus_izni` işaretçisi 3 Eylül'de `:375`, 4
Eylül'de `:386`: dosya değişti, halka aynı. `exit=1` kopuk halka varken tasarım
gereğidir (`scripts/saha_kuru_kosu.py:1251,1256`). Dosya CRLF'dir ve ilk
satırdaki uzun tire cp1254 baytı olarak bozuk kaydedilmiştir; burada `—` ile
yazıldı.

🔴 **"SAHİPSİZ" gizlenmiyor.** Gerçek İKA motor sürücüsü yoktur (R12/T149);
donanım kararı gelmeden kapanmaz. FDA görev test uçuşunda (21 Eylül) İKA
kullanılmaz, dolayısıyla bu kopuk halka **o uçuşu engellemez** — ama yarışma
görevi (§2.2.5) için **açık kalemdir**.

### 4.11.2 Aynı koşumun makine okunur çıktısı

`results/saha_kuru_kosu_20260903_120254/ozet.json` (3 Eylül) ile
`results/saha_kuru_kosu_20260904_010058/ozet.json` ve
`results/saha_kuru_kosu_20260904_095222/ozet.json` (4 Eylül 01:00 ve 09:52)
aynı zinciri JSON olarak tutar; üçünde de `sayim` = `{GECTI: 9, DUSTU: 0,
SAHIPSIZ: 1, ATLANDI: 0}`, `kopuk_halkalar` = `["motor"]`, `cikis_kodu` = 1.
09:52 koşumunun halka süreleri (`sure_ms`; CPU, Windows PC — Jetson değil):
kamera 2223,3 · model_yukleme 47,7 · cikarim **3304,4** · maske 65,6 · rota 31,6
ms; `aktarim.detay.uretim_yolu_telsiz` = `{open_route_alindi: true, heartbeat: 1,
ack: ["ika"], hata: null}`; `surus_izni.detay.tum_ureticiler` kanonik dosya ile
paket aynasını (`jetson_paket/kod/iha_inis_yayinci.py:386`) birlikte sayar.
`halka_sirasi` alanı on halkayı sırayla sayar (kamera → model_yukleme →
cikarim → maske → olcek → hedef_konumu → rota → aktarim → surus_izni → motor);
her halka için `durum`, `sebep` ve `dosya` alanları vardır ve sözleşme bağı
`CONTRACTS.md §11` olarak dosyanın içinde yazılıdır.

🔴 **Bu bir DONANIM entegrasyon kanıtı değildir.** Halkaların tamamı yazılım
tarafındadır; kamera halkası fikstür karesiyle
(`data/kuru_kosu_fikstur/images/sa_000000.jpg`) koşulmuştur. Gerçek kamera,
gerçek Pixhawk ve gerçek telsizle **aynı anda** koşulan bir yer entegrasyonu
5–19 Eylül'dedir ve bugün yoktur.

---

## 4.12 Arıza emniyet doğrulaması — eve dönüş, motor kesme · `Y-4-M12`

> *Yönerge: "…arıza emniyet doğrulaması kapsamında, gerekli arıza durumlarının
> oluşması halinde sistemin verdiği tepkilerin (eve dönüş, motor kesme vb.)
> **sahada test edildiğini** gösteren verilerin raporda sunulması
> gerekmektedir."*

🔴 **ÖLÇÜLEMEDİ: hiçbir arıza emniyet tepkisi sahada test edilmedi. Eve dönüş
(RTL), motor kesme (DISARM), geofence ihlali ve telemetri kaybı davranışları
gerçek araçta hiç tetiklenmedi; 5 Eylül'de uçuş yapılmadı. Ölçüm uçuş
testlerindedir (§4.3.3).**

**5 Eylül 2026 durumu** (`REVIEW_LOG.md` D-426 §4; kart masa üstünde, pervanesiz):

| arıza senaryosu | şablon parametresi (`config/pixhawk/arducopter_fda.param`) | 5 Eylül |
|---|---|---|
| RC kaybı (kumanda kapatma) | `FS_THR_ENABLE,1` (satır 129) | **ÖLÇÜLEMEDİ** — test iki kez istendi, sonuç gelmedi. Dosyadaki yorum *"iBUS alıcısı sinyal kaybında çerçeve basmayı keser"* (satır 128) **varsayımdır**, ölçülmedi; alıcının failsafe'de ne yaptığı bilinmiyor |
| YKS/Jetson bağlantı kaybı | `FS_GCS_ENABLE,1` (satır 134) | tetiklenmedi |
| Düşük pil | `BATT_FS_LOW_ACT,2` / `BATT_FS_CRT_ACT,1` (satır 120 / 123) | tetiklenmedi; pil takılı, PreArm pil uyarısı kayboldu (OLCUM, §4.4) |
| Geofence | `FENCE_ENABLE,1` / `FENCE_ACTION,1` (satır 140 / 154) | tetiklenmedi; karttaki değer dökümsüz (§4.13.1 #9) |
| Motor kesme (DISARM) | — | uçuş yok |
| Emniyet düğmesi | `BRD_SAFETY_DEFOFF` değiştirilmedi | fiziksel düğme çözüldü, OLCUM `PreArm: Hardware safety switch` kayboldu — bu bir **arm ön koşuludur**, arıza tepkisi değil |

⚠ Parametrelerin **kartta** hangi değerde olduğu 5 Eylül'de ölçülmedi: döküm
alınmadı; `RC_PROTOCOLS` sahada 4 → 1 yapılıp geri alınmadı (D-426 §2), dolayısıyla
şablon ile kart en az bir satırda **farklıdır**. **6 Eylül 20:22 dökümü** (`config/pixhawk/arducopter_fda_20260906.param`, D-428 §5g) bunu ölçtü: `RC_PROTOCOLS=1`; ayrıca `FS_THR_ENABLE` 1→**3** ve `BATT_FS_LOW_ACT` 2→**1** bilinçsiz değişmiş (D-428 §5b) — 30 m görev öncesi mimar kararı bekler; `FS_GCS_ENABLE` (dökümde 1) ve ikinci pusula kalibrasyonu bu dökümde yok → üçüncü döküm şart.

**Saha testinin YERİNE GEÇMEYEN, bugün elde olan şey**, arıza emniyet
komutlarının **yazılım yolunun** kapı altında olmasıdır:

| tepki | yazılım yolu | koşulan kapı |
|---|---|---|
| Eve dönüş (RTL) ve iniş (LAND) | `comms/iha_komut_alici.py` — `CMD_RTL` / `CMD_LAND`, ARM ile **aynı** fail-closed kaynak/zaman/oturum kapısından ve güçlü Pixhawk ACK şartından geçer | `tests/test_iha_rtl_land.py` — **6 test** (`grep -c "def test_"`); üçü mutasyon testidir: yanlış `MAV_CMD` güçlü ACK sayılmaz · reddedilen LAND ACK'i YKS'ye ACK üretmez · bayat RTL/LAND eyleyiciye ulaşmaz |
| Motor kesme (DISARM) | `comms/iha_komut_alici.py` — `CMD_DISARM` → `MAV_CMD_COMPONENT_ARM_DISARM`, `param1 = 0` (`ARM_DISARM_PARAM1_DISARM`) | `tests/test_iha_komut_guvenligi.py` — **10 test** (`grep -c "def test_"`); oturumsuz ve bozuk oturum reddi, bayat/bool/NaN/ileri-zaman reddi, tekrar ACK'inin eyleyiciyi yinelememesi, yabancı component ACK'inin kabul edilmemesi |
| Kaynak pini olmayan komut | kaynak pinsiz ARM/DISARM/PARACHUTE/RTL/LAND **kabul edilmez** (`comms/iha_komut_alici.py`) | aynı iki kapı dosyası |
| Geofence ihlali | 🔴 karttaki parametreler **repo dışıdır** (R17); şablon `config/pixhawk/arducopter_fda.param:140` `FENCE_ENABLE,1` · `:154` `FENCE_ACTION,1`; yazılım tarafında kapı **yoktur** | yok — §4.13.1 kalem 9; 5 Eylül dökümü alınmadı |
| Arıza sonrası yerde olduğunun doğrulanması | `yerde_mi` sözleşmesi: ON_GROUND + irtifa + aynı sysid + ardışık 3 örnek | `tests/test_inis_kaniti.py` (26 test, §4.1.2) · P1 kapıları G3b/G4 (§4.9.1) |

⚠ **Bu tablo bir arıza emniyet kanıtı DEĞİLDİR.** Gösterdiği şey, komutun doğru
`MAV_CMD`'ye çevrildiği ve reddedilmesi gerekenin reddedildiğidir; **gerçek
Pixhawk'ın gerçek arızada ne yaptığını göstermez**. Yönergenin istediği "sahada
test edilmiş veri" 6–19 Eylül'de üretilecektir; ilgili kapılar §4.3.3'te adım
3.2 (geofence + iniş kanıtı canlı) ve adım 3.5 (hands-off, 0 müdahale) olarak
önceden yazılıdır.

**BEYAN GEREKLİ (insan):** her arıza emniyet senaryosu için tetikleme yöntemi
(telemetri kablosunu çekme, geofence sınırını aşma, kumandayı kapatma), tarih,
pilot rol kodu ve uçuş log dosyasının adı.

---

## 4.13 Karşılanamayan ve kısmen karşılanan gereksinimlerin nedenleri — kalan test borcu

> Bu alt bölüm yönergenin Bölüm 6 beklentisini (`Y-6-M05`: *"karşılanamayan veya
> yalnızca kısmi olarak karşılanan gereksinimler bulunması durumunda, bu durumun
> nedenleri açıkça belirtilmeli"*) besler. Kuralı tektir: **ölçülmeyen, "sorun
> çıkmadı" diye yazılmaz.**

### 4.13.1 Ölçülmemiş olanlar

| # | ne | neden ölçülmedi | ne zaman | eşik |
|---|---|---|---|---|
| 1 | **Gerçek arena / HTAB karesi** | Arena benzeri saha + kırmızı H çekimi yok; **maket çekimi yapılmayacaktır** (kullanıcı kararı) | 21 Eylül'e kadar **açık kalır** | — |
| ~~2~~ | ~~**Jetson Nano gerçek FPS**~~ → **ÖLÇÜLDÜ 6 Eylül (D-431)** — kart Orin Nano Developer Kit 4 GB | 5 Eylül: Jetson araca **takılmadı** (D-426 §4) → 6 Eylül kartta: pt **1,35/1,06** · engine **1,58/1,33** FPS (120 örnek), 10 dk 900 örnek, ONNX HATA | 6 Eylül | **≥ 0,61 FPS** p50 **ve** p95 → **GEÇTİ**; eşik gevşetilmedi. Sınır: kamera bağlı değil, kareler diskten (`results/jetson_20260906/jetson_fps_20260906_orin_nano/ozet.json`) |
| 3 | **SiK 433 MHz RF menzili / kayıp oranı** | Gerçek SiK çifti yok; UDP loopback ve `socket://` köprü kanıt sayılmaz → 5 Eylül: çift bağlandı (BEYAN, ~18:45), `scripts/sik_rf_olc.py` **koşulmadı**, mesafe kaydı yok (§4.5) | uçuş testleriyle | RTT p95 < 0,2 s. DDR'deki *">%98, 300 m"* iddiasının kanıtı **yoktur** (R20) |
| 4 | **Uçuş testleri** (hover, Loiter/Auto, canlı algı, 3 tam prova, sıkı prova) | Araç monte edilmedi | **6–19 Eylül** | ≤ 10 dk, 0 müdahale, yanlış güzergâh 0 |
| ~~5~~ | ~~**TensorRT `.engine` ↔ PT karar kıyası**~~ → **ÖLÇÜLDÜ 6 Eylül ve DÜŞTÜ (D-431)** | `tensorrt` PC'de yok → Jetson'da ölçüldü: F1 0 · F2 0,9953 · **D-303 oransal 3/126 DÜŞTÜ** (§4.8.3) | 6 Eylül | FP16 payı **kapanmadı**: engine üretime alınmadı, uçuş `.pt`; T66 ile tekrar |
| 6 | **Gerçek Pixhawk üzerinde EXTENDED akışı ve `--kapi`** | Pixhawk yok → 5 Eylül: Pixhawk 4.5.7 ile çalışır durumda (§4.4), `scripts/mavlink_dogrula.py` **koşulmadı** (D-426'da koşum kaydı yok) | uçuş öncesi | `mavlink_dogrula` 3/3 |
| 7 | **`jetson_baslat.sh` systemd / `--kur` / `--kapi` / `--dogrudan`** | Windows'ta koşulamaz → 6 Eylül kartta `--kuru`: dosya/yorumlayıcı `[VAR]`, `[YOK]` yalnız `/dev/ttyACM0`, çıkış 3 (D-431); `--kapi` Pixhawk bağlı olmadığı için **ÖLÇÜLEMEDİ** | Pixhawk Jetson'a bağlanınca | kuru çıktı == gerçek `ExecStart`; `--kapi` 3/3 |
| 8 | **Gerçek İKA motor sürücüsü** | Donanım arayüzü kararı verilmedi (R12/T149) | yarışma görevi öncesi | kuru koşuda `motor SAHİPSİZ` |
| 9 | **Pixhawk geofence parametrelerinin kendisi** | Repo dışı (R17) → 5 Eylül: şablon yüklendi (OLCUM, §4.4 15:08) ama döküm **alınmadı** (D-426 §4) → 6 Eylül 20:22 dökümü `config/pixhawk/arducopter_fda_20260906.param` repoda: `FENCE_ENABLE,1` · `FENCE_ALT_MAX,50` (D-428 §5g); üçüncü döküm bekleniyor | uçuş öncesi | `config/pixhawk/` kanıt olarak |
| 10 | **K5 figür bilgi px** | verdikt JSON'ında `OLCULEMEDI` | — | — |
| ~~11~~ | ~~**Nano kurulum belgesinin dış iddiaları**~~ (bionic `python3.8`, `jetson-io` IMX477 menüsü, Qengineering CUDA wheel) → **6 Eylül'de KONUSUZ KALDI (D-431):** kart Nano değil Orin Nano Developer Kit 4 GB (JetPack 7.2.1, Python 3.12); belge bu kart için GEÇERSİZ bandı alır | Kaynakla doğrulanmadı; 14/14 aarch64 wheel bu kartta kullanılmadı | — | — |
| 12 | **RC failsafe** (kumanda kapatma → `Radio Failsafe`, CH3 değeri) — 5 Eylül eklendi | İki kez istendi, sonuç gelmedi (D-426 §4); `config/pixhawk/arducopter_fda.param:128` yorumu **varsayım** | uçuş öncesi (§4.3.3 adım 3.1 öncesi) | `Radio Failsafe` mesajı görülür ve `FS_THR_ENABLE=1` tepkisi (RTL) — §4.12 |
| 13 | **ESC kalibrasyonu** — 5 Eylül eklendi | YAPILMADI; ESC markası bilinmiyor ("60 A V2" etiketi, BEYAN) | uçuş öncesi | ArduPilot "hepsi birden" yordamı ya da marka belgesiyle gereksizlik kanıtı (D-426 §4) |
| 14 | **Pusula kalibrasyonu** — 5 Eylül eklendi | YAPILMADI — Jetson takılı değil; takılınca yeniden gerekir (D-426 §4) | Jetson takılı, dışarıda | ofset < 300 (`SAHA_HAZIRLIK_PLANI_20260903.md` §2.4) |
| 15 | **Accel + level teyidi** — 5 Eylül eklendi | BEYAN "yapıldı"; kart sabit değildi, döküm yok (D-426 §4) | kart sabitlenince | `INS_*` dökümü |
| 16 | **Parametre dökümü** — 5 Eylül eklendi | 5 Eylül: dosya yok (D-426 §4) → **6 Eylül 20:22:** `config/pixhawk/arducopter_fda_20260906.param` repoda (D-428 §5g); `RC_PROTOCOLS=1` (şablon 4), `FS_THR_ENABLE`/`BATT_FS_LOW_ACT` sapması (D-428 §5b); ikinci pusula kalibrasyonu ve `FS_GCS_ENABLE` bu dökümde yok | uçuş öncesi (üçüncü döküm) | döküm repoda, şablonla `Compare Params` farkı listeli |
| 17 | **Pil gerilimi MP ↔ multimetre** — 5 Eylül eklendi | ölçülmedi (D-426 §4) | uçuş öncesi | ±0,1 V |
| 18 | **Motor sırası/yönü** — 5 Eylül eklendi | BEYAN 4/4, video yok (D-426 §1) | pervane takılmadan önce | video — §4.13.4 madde 7 |

### 4.13.2 Kapı/test boşlukları — **3'ü kapandı, 3'ü açık**

> Bu tablo silinmez, **üstü çizilir**: kapanan boşluk da kayıttır. 1–3 D-405
> turunda kapatıldı (kanıt satırlarda); 4–6 **hâlâ açıktır**.

| # | boşluk | risk | kayıt |
|---|---|---|---|
| 1 | ~~`seri_hub` 25 mutantın 12'si kaçtı~~ → **KAPANDI (D-405, `c112381`)**: sertleştirme sonrası aynı 25 mutant **24/25** yakalandı; kapı takımı 11 → **31 test** + 4 yeni dayanıklılık testi. **Tek kaçan kaldı:** `l_arizada_ogrenmez` (seri arıza anında yeni tüketici öğrenilmemesi) — bilerek testsiz, marjinal | Kalan kaçanın riski: arıza anında yanlış tüketici öğrenilirse çerçeve yanlış uca gider (tek uçlu sahada gözlenemez) | D-405, `REVIEW_LOG.md:28096` |
| 2 | ~~Hub derin iç içe JSON'da RecursionError ile ölüyor~~ → **KAPANDI**: çerçeve işleme `except Exception` ile sarıldı (`comms/seri_hub.py:408`), bozuk satır yutulur ve **aynı okuyucudan sonraki geçerli çerçeve geçer** | — | D-405; kapı `tests/test_faz_b_protocol_dayaniklilik.py` (4 test) |
| 3 | ~~Hub "tek sahiplik" garantisi kodda zorlanmıyor~~ → **KAPANDI**: UDP ucu `UDPLink(..., reuse=False)` (`seri_hub.py:574`, `link.py:29`) — ikinci hub `OSError` ile **çıkış 3**, sessiz sağır kopya yok; seri port `SerialLink(exclusive=True)` (`link.py:81`) | Linux'ta `exclusive` çekirdek düzeyinde, Windows'ta değil — saha Jetson'dur | D-405 |
| 4 | Kamera köprüsü K5 kapısı **API adı** denetlemiyor (yalnız söz dizimi) | Py3.6 uyumu sessizce bozulabilir | D-407 |
| 5 | `rpi_inference` ekransız kipte **SIGTERM işlenmiyor** (T204); `save=True` iken codec yoksa ölü yazıcıya sessiz yazma (T205) | Tanı kaybı; kayıt kaybı | D-404 §8 |
| 6 | Depo `core.autocrlf=true`: ayna/kaynak bayt eşitliği kapıları **kırılgan** — bir turda 11 test bu yüzden düştü (içerik doğruydu, düşen çalışma kopyasıydı) | Yanlış kırmızı | D-407 §4 |

### 4.13.3 🔴 DENETİM BORCU (Anayasa madde 19)

*"Bir iş, onu yazanın onayıyla kapanmaz."* Aşağıdaki kalemlerde **yazan ile
onaylayan aynı taraftır** ve bağımsız denetim beklemektedir:

1. **D-407 turundaki düzeltmeler** (Nano belgesi dizin hizası, mühür kapsamı) —
   mimar-dışı denetim ya da **5 Eylül'de Jetson'daki ilk gerçek koşum**.
2. **D-404 §7 madde 4** — `jetson_baslat.sh` systemd kipleri Windows'ta
   koşulamadı; Jetson'daki ilk koşum ilk kanıttır.
3. **D-406 K2/T207 kodu** ajanlar tarafından yazıldı; mimar diff/test/mutasyon
   çıktılarını okudu — **bağımsız üçüncü göz yok**.
4. **D-412 `_kanit_yaz`** — eksik metot bu turda yazıldı ve 6 testle + mutasyonla
   kapatıldı, ama **yazan ile onaylayan aynı taraftır**; bağımsız denetim bekler.

#### 4.13.3.1 🔴 Bu turda ölçülen kendi hatamız — yeşil rapor kırmızı depoyla

`ef02e19` commit'i **belge commit'i olarak duyuruldu** ama `comms/yks_gui.py`'ye
ait 16 satırı da beraberinde götürdü (Codex'in yarım kalan hakem-kanıt işi).
Götürülen satırlar arasında `self._kanit_yaz(...)` **çağrısı** vardı; **tanımı**
yoktu. Sonuç: `YksArayuz.__init__` her gerçek kurulumda `AttributeError` ile
ölüyordu — sahada **YKS hiç açılmazdı**.

Daha ağırı: aynı turda "tam süit 1882 test OK" diye **yazıldı**. O koşum
süpürmeden **önceydi** ve commit'ten sonra süit yeniden koşulmadı. Kırmızı kapı,
"kapı geçti" cümlesinin yazıldığı anda depoda duruyordu. Kusur bu turun ilk
süit koşumunda **6 hata** olarak çıktı ve orada yakalandı.

Ders yordama geçirildi: **commit öncesi `git status` kapsamı okunur**;
`comms/` veya `codes/` altında beklenmeyen dosya varsa commit genişletilmez.
Kayıt: `REVIEW_LOG.md` D-412.

Bu maddeler kapanmadan ilgili kayıtlar "tamamlanmış" sayılmaz ve bu raporda da
öyle sayılmamıştır.

### 4.13.4 BEYAN GEREKLİ (insan)

1. **BEYAN GEREKLİ (insan):** donanım künyesinin fiziksel teyidi. 5 Eylül kutu
   açılışında (D-426 §3) plandan **farklı** çıkan iki kalem: **ESC "60 A V2" ×4**
   (plan 80 A DShot) ve **güç modülü PM06** (plan PM02) — ikisi de sözlü BEYAN;
   **etiket fotoğrafı ve tam marka/model gerekli**. Teyit edilen: RC alıcı
   **FS-iA6B** (B harfi görüldü, BEYAN). Teyit kaydı olmayan: ~~Jetson Nano 4GB~~ (6 Eylül'de kartta ÖLÇÜLDÜ: **Jetson Orin Nano Developer Kit 4 GB**, beyan yanlışlandı — D-431),
   Holybro M9N (GPS `u-blox` OLCUM'u marka etiketi değildir), RPi HQ (IMX477),
   FCHUB-12S V2, 5008 340KV ×4, 12×10 pervane, 2× SiK 433 MHz, 4S 10 Ah 25C.
   Bu rapordaki "Pixhawk 6C + PM02" ifadeleri künye teyidiyle düzeltilecektir.
2. ~~**BEYAN GEREKLİ (insan):** Jetson Nano üzerinde ölçülen p50/p95 FPS değerleri (PT ve ONNX; `--cihaz` beyanıyla)~~ → **ÖLÇÜLDÜ 6 Eylül (D-431):** `--cihaz 0` (Orin GPU); PT **1,35/1,06** · engine **1,58/1,33** FPS; ONNX **HATA** (sm_87 çekirdeği yok) — `results/jetson_20260906/jetson_fps_20260906_orin_nano/ozet.json`.
3. **BEYAN GEREKLİ (insan):** SiK 433 MHz çift üzerinde ölçülen RTT p50/p95,
   paket kaybı ve **menzil** (metre) — `scripts/sik_rf_olc.py` çıktısı.
4. **BEYAN GEREKLİ (insan):** 6–19 Eylül uçuş testlerinin her biri için tarih,
   pilot, log dosyası ve kapı sonucu (`results/prova/` üç klasör).
5. **BEYAN GEREKLİ (insan):** 21 Eylül Adıyaman uçuş alanı izni ve alan
   koordinatları (mühürden sonra **tek izinli değişiklik**, tutanakla).
6. **BEYAN GEREKLİ (insan):** sürüm mührünün basıldığı tarih ve künye commit'i
   (planlı: 17 Eylül; `--dogrula` çıkışı 0 olmalıdır).
7. **BEYAN GEREKLİ (insan):** 5 Eylül motor testinin sıra/yön videosu (D-426 §1,
   ~18:30 satırı "video: BEYAN GEREKLİ") ve ESC sinyal kablosundaki kırmızı
   telin (BEC) durumu (D-426 §4, cevap gelmedi).

---

## 4.14 Kanıt dizini

| # | sayı / iddia | dosya yolu | üreten betik / komut | ölçüm tarihi |
|---|---|---|---|---|
| 1 | Genel kapı **15/15 · 15/15** (iki kol) | `codes/test_rota_sentetik.py` (stdout) | `…\venv\Scripts\python.exe codes/test_rota_sentetik.py` | 2026-09-03 |
| 2 | Tam suit **1896 test · OK (skipped=3) · 390,534 s** | `results/faz_b_oncesi/cuma_kontrol/tam_suit.txt` (bu bölümde ham) | `…\venv\Scripts\python.exe -m unittest discover -s tests` | 2026-09-03 |
| 3 | `tests/` altında **153** `test_*.py` | `O:\navitas\tests\` | `ls tests/ \| grep -c "^test_"` | 2026-09-03 |
| 4 | Kayıt defteri **414 başlık / 408 benzersiz** | `REVIEW_LOG.md` | `grep -cE "^### D-[0-9]+"` · `\| sort -u \| wc -l` | 2026-09-03 |
| 5 | **36 ön kayıt artefaktı** | `results/**/ON_KAYIT*` | `find results -iname "*on_kayit*"` | 2026-09-03 |
| 6 | Kabul kapıları K0–K8 ölçülen değerleri ve verdikt `true` | `scripts/olcum/results/t63/t150_baglama_v36_kabul_verdikt.json` | `scripts/olcum/65_kabul_denetcisi.py` | 2026-09-01 |
| 7 | Kabul kümesi parmak izi (n=547, `sha256:604c037f…`) | aynı JSON, `kabul_kumesi_parmak_izi` | aynı betik | 2026-09-01 |
| 8 | K7 tabanı **84/85 = %98,8**, rota üretilen **85/88** | `scripts/olcum/results/t63/t150_baglama_v36_k7.json` · `CONTRACTS.md` §12.1 | `scripts/olcum/151_k7_serit_dogrulugu.py` | 2026-09-01 |
| 9 | K8 gerçek kare: zemin kaplaması **%4,44**, ret `UC_BANT_TEMAS_YOK` | aynı verdikt JSON | `scripts/olcum/155_gercek_kare_kapisi.py` | 2026-09-01 |
| 10 | v36 ön kayıtlı eşiklerin geçilmediği **ham metin** (ROTA 8 < 10; MASKE_YOK 16 > 10) | `results/fdr/GORUNTU_ISLEME_KANIT.md` §3 | `scripts/olcum/167_fdr_kanit_paketi.py`; dayanak **D-293** · ön kayıt `results/gece_20260826/ON_KAYIT.md` §15 | 2026-08-26 (karar) / 2026-09-01 (paket) |
| 11 | v36 terfi bedeli (K3 0→1, K4 1→4, K6 5→7, val82 FP 0→2) | `results/fdr/GORUNTU_ISLEME_KANIT.md` §3 · `REVIEW_LOG.md` D-293 | aynı paket | 2026-08-26 |
| 12 | Çürütücü turu (v36 terfisi) — terfi engeli bulunmadı | `results/gece_20260826/v7a_curut/` | üç lensli çürütücü | 2026-08-26 |
| 13 | Çözünürlük 640 RED: I2 **0,9846 → 0,7808**, I3 **51 → 52 s**, I4 oran **1,300** | `results/b4_fps/infer_size_20260901.json` · `infer_size_R_TEMIZ_hukum.txt` | `scripts/olcum/166_infer_size_640.py` · nöbetçi `tests/test_166_infer_size_nobetcisi.py` (17) | 2026-09-01 |
| 14 | Ön kayıtlı karar sırası (*"I2 düşerse RED"*) | `results/b4_fps/ON_KAYIT_INFER_SIZE.md` §5 + EK-1 | — (sonuç görülmeden yazıldı) | 2026-09-01 |
| 15 | Sızıntı düzeltmesi: p **0,3457** (temiz, n=243) · **0,326** (yalnız 0038) · sentetik **0,9846** | `results/fdr/GORUNTU_ISLEME_KANIT.md` §4 · `REVIEW_LOG.md` D-376 | `scripts/olcum/167_fdr_kanit_paketi.py` | 2026-09-01 |
| 16 | Türetilmiş FPS eşiği **0,61** = 1/(5×0,326) | `REVIEW_LOG.md`:26042 · `FAZ_B_GUN_PLANI.md` §1 | türetme, `YKS_TESPIT_TAZELIK_S = 5,0` (CONTRACTS) | 2026-09-01 |
| 17 | FP16: F1 **0/260**, F2 **631/633 = 0,9968**; ilk ölçümün vakumu (bit-eş 1,0) | `results/b4_fps/fp16_denklik_20260901.json` (893 kare) | `scripts/olcum/164_fp16_karar_denkligi.py` · nöbetçi `tests/test_164_fp16_nobetcisi.py` (12) | 2026-09-01 |
| 18 | Uçtan uca kare gecikmesi **p95 0,113 s**; telsiz payı `p50 307,6 → 2,3 ms` | `results/fdr/GORUNTU_ISLEME_KANIT.md` §4.1b · `REVIEW_LOG.md` D-382/D-383 | 33 ölçülen gerçek kare (+3 ısınma), üretim zinciri + UDP loopback ACK | 2026-09-01 |
| 19 | Mutasyon betiğinin CRLF kusuru; `ika_nav.py` **658 CRLF / 0 LF** | `REVIEW_LOG.md` D-370 | `scripts/olcum/129_t141_mutasyon_olcumu.py` (düzeltilmiş) | 2026-08-31 |
| 20 | Ekransız kip: 7/7 mutant yakalandı (ilk turda 4'ü kaçmıştı) | `results/faz_b_oncesi/ekransiz_denetim/mutant_sonuc_9test.txt` · `mutant_kos.py` | bağımsız denetçi ajanı | 2026-09-02 |
| 21 | `seri_hub` mutasyon skoru: **ilk 13/25**, sertleştirmeden sonra **24/25** (kaçan: `l_arizada_ogrenmez`); vakum bulguları | `results/faz_b_oncesi/curutucu_d405/BULGULAR_OZET.md` (+ `BULGULAR_TAM.md`, `mut_seri_hub/log_*.txt`) | 5 mercekli çürütücü turu | 2026-09-02 |
| 22 | Hub UDP→seri gecikmesi: A p95 **31,0/31,2 ms**, B p95 **70,8/76,8 ms** (maks 79,7), C p95 **16,2/15,2 ms**; kayıp **0/50** | `results/faz_b_oncesi/curutucu_d405/` (`r2_gecikme.py`, `olc_granul.py`) | gerçek `SerialLink` `socket://` + hub ipliği, 2 koşum × 50 örnek | 2026-09-02 |
| 23 | T207 gerçek topoloji: A/B senaryoları, ilk gecikme **0,30 s**, 511/33 @125000 µs · 511/245 @500000 µs | `results/faz_b_oncesi/curutucu_d407/akis_istegi/r_topoloji2.py` | çürütücü ikinci tur | 2026-09-03 |
| 24 | Kamera köprüsü: bellek **0,48 MB sabit**, 40 istemci sonrası `dusen_kare=0` | `results/faz_b_oncesi/curutucu_d407/kopru/` (`mjpeg_repro.py`, `istemci_repro.py`) | çürütücü ikinci tur | 2026-09-03 |
| 25 | Kuru koşu **9 GEÇTİ · 0 DÜŞTÜ · 1 SAHİPSİZ (motor)** | `results/faz_b_oncesi/cuma_kontrol/cuma_kontrol.txt` §5 | `scripts/saha_kuru_kosu.py` | 2026-09-03 |
| 26 | Jetson açılış kuru koşuları (udp exit 0 · sik exit 0 · eksik beyan exit 3) | `results/faz_b_oncesi/jetson_baslat_kuru_*.txt` | `bash jetson_paket/jetson_baslat.sh --kuru` | 2026-09-03 |
| 27 | P1 kapıları G1–G8 ve BULGU A (`yerde_mi` 0,002 s'de False) | `results/p1_mavlink/ON_KAYIT.md` · `REVIEW_LOG.md` D-387/D-389 | `tests/test_p1_canli_mavlink.py` (14) + `scripts/sahte_pixhawk.py` | 2026-09-02 |
| 28 | P2 S5 kusuru: tampon **1.048.576 bayt** (eşik 65.536) ve düzeltme | `results/p2_seri/ON_KAYIT.md` · `REVIEW_LOG.md` D-388 | `tests/test_p2_seri_hat.py` (10), gerçek `pyserial` SiK köprüsü | 2026-09-02 |
| 29 | D-15 vakum kapısı ve pozitif kontrol (yanlış komut 0/0; doğru komut 0/**46**) | `REVIEW_LOG.md` D-15 | `git ls-files "*.py" \| xargs grep -nE …` | 2026-08-05 |
| 30 | K7 alt küme gerekçesi: kabul kümesinin **%54'ü (105/193)** kötü koşullu | `CONTRACTS.md` §12.1 · `config/k7_iyi_kosullu_kume.json` (88 kare) | D-312 ölçümü | 2026-08-27 |
| 31 | K7 referans semantiği: `sa_000090` model 89.913 px ↔ GT 18.042 px serbest; engel 42.123 ↔ 43.781 | `CONTRACTS.md` §12.1 · `REVIEW_LOG.md` D-315 | etiket kapsamı ölçümü | 2026-08-27 |
| 32 | T99 vakum kapıları `V1/V3/V4 = true`; araç maskesi 7/260 karede dolu | `results/t99_uretim_imzasi/olcum_20260903.json` · `ON_KAYIT.md` | `scripts/olcum/` T99 ölçüm betiği | 2026-09-03 |
| 33 | Suit büyüme dizisi 1489 → 1617 → 1685 → 1826 → 1827 → 1875 → 1882 → **1896** | `REVIEW_LOG.md` D-388 §5, D-403 §6, D-404 §5, D-406, D-407 §4 + bu koşum | `unittest discover` | 2026-09-02…03 |
| 34 | Uçuş testi planı ve kapıları (3.1–3.7), takvim | `SAHA_HAZIRLIK_PLANI_20260903.md` §3, §4, §5 | — (plan) | 2026-09-03 |
| 35 | Gerçek donanım künyesi (Nano 4GB, Pixhawk 6C, M9N, RPi HQ, 4S 10 Ah) | `SAHA_HAZIRLIK_PLANI_20260903.md` §0.2 | **kullanıcı beyanı**, 3 Eylül 2026 — kutu 5 Eylül'de açılıp teyit edilecek | 2026-09-03 |
| 36 | Şartname §5.3.1 Tablo 4 (Bölüm 4 = 15 puan) ve §5.3.2 görev kuralları | `results/sartname_bosluk/sartname_metin.txt` s.17–18 | PyMuPDF metin çıkarımı | 2026-08-26 |
| 37 | Yükümlülük haritası R1–R22 (R20 SiK "hâlâ ÖLÇÜLMEDİ", R12 motor "YOK") | `results/sartname_bosluk/rapor.md` | `scripts/…/rapor_uret.py` + elle tarama | 2026-08-26 |
| 38 | Tam suit **2104 test · OK (skipped=3) · 390,131 s** | `results/faz_b_oncesi/cuma_kontrol/tam_suit.txt:353,355` (HEAD, commit `3db848c`) | `…\venv\Scripts\python.exe -m unittest discover -s tests` | 2026-09-04 |
| 39 | Tam suit **1896** ham çıktısının dosya kaynağı (satır 2'deki yol artık 4 Eylül koşumunu tutar) | `git show 2705b4e:results/faz_b_oncesi/cuma_kontrol/tam_suit.txt` → `Ran 1896 tests in 390.534s` · `OK (skipped=3)` | aynı komut | 2026-09-03 |
| 40 | Tam suit **2138 test** (5 Eylül; 3 koşum: OK / 1 FAIL / 1 FAIL — ortam, `WinError 10013`, port 5005/5006) | `REVIEW_LOG.md` D-427 (satır 29893–29895); ham çıktı dosyası **yok** | aynı komut | 2026-09-05 |
| 41 | Suit büyüme dizisi 1896 → 2052 → 2080 → 2104 → 2138 | `tam_suit.txt` @ `2705b4e` / `bb832a2` / `7a0bdac` / `3db848c` (`git show <c>:results/faz_b_oncesi/cuma_kontrol/tam_suit.txt \| grep "^Ran "`) + `REVIEW_LOG.md` D-427 | `unittest discover` | 2026-09-03…05 |
| 42 | `tests/` altında **180** `test_*.py` | `O:\navitas\tests\` | `ls tests/ \| grep -c "^test_"` | 2026-09-05 |
| 43 | Kayıt defteri **432 başlık / 426 benzersiz**, son kayıt D-427 | `REVIEW_LOG.md` | `grep -cE "^### D-[0-9]+"` · `grep -oE "^### D-[0-9]+" \| sort -u \| wc -l` | 2026-09-05 |
| 44 | 3–5 Eylül kapı dosyaları test sayıları 42 · 10 · 7 · 6 · 4 · 3 · 3 · 3 (= 78) | `tests/test_iha_komut_saat_ve_tekrar.py` · `test_pixhawk_firmware_yolu.py` · `test_fdr_sarkan_atif_kapisi.py` · `test_yks_hakem_kanit_yolu.py` · `test_wheels_sayisi_belgelerle_tutarli.py` · `test_runbook_komutlari_kosuyor.py` · `test_yarisma_adi_kapisi.py` · `test_yks_harita_yerlesimi.py` | `grep -c "def test_" <dosya>` | 2026-09-05 |
| 45 | Kuru koşu 4 Eylül: GECTI 9 · DUSTU 0 · SAHIPSIZ 1 (`motor`) · çıkış 1 | `results/saha_kuru_kosu_20260904_095222/ozet.json` (`sayim`, `kopuk_halkalar`, `cikis_kodu`) | `scripts/saha_kuru_kosu.py` | 2026-09-04 |
| 46 | Mutasyonlar 3–4 Eylül: `_kanit_yaz` → 6/6 düştü · `§6.99.7` → T1 düştü · `--izinli-kaynak` → T1 düştü · sapma tavanı → 17 düştü, `_yerel_saat_adimi` → 5 düştü | `REVIEW_LOG.md` D-412 (satır 28569), D-420 §5 (29272), D-421 §2 (29339), D-422 §6 (29559–29561) | ilgili kapı dosyaları + `cmp` bayt-eş | 2026-09-03…04 |
| 47 | Vakum örnekleri 5–7: runbook kapısı 22/22 yeşilken komut `EXIT=2` · wheels kapısı 51 ≠ 48 · TEYİT listesi `Missing 9 params` | `REVIEW_LOG.md` D-421 §1–2 (29304–29331), D-423 (29575–29586), D-425 §1–2 (29718–29720, 29753–29758) | — | 2026-09-04…05 |
| 48 | Çürütücü turları D-411 (71 bulgu, 6 KRİTİK, 30 KÜÇÜK açık) · D-421 (13 tıkayıcı) | `REVIEW_LOG.md` D-411 (28450–28520), D-421 (29288–29428) | — | 2026-09-03…04 |
| 49 | Tam suit YKS canlıyken koşamaz: `test_comms.py:35-36` bind 5005/5006, `WinError 10013`; T209 | `REVIEW_LOG.md` D-427 (29897–29929) · `comms/test_comms.py:35-36` · `comms/link.py:34` | — | 2026-09-05 |
| 50 | 5 Eylül kabul tutanağı: `ArduCopter V4.5.7 (2a3dc4b7)` · `Frame: QUAD/X` · `u-blox 1 HW: 000A0000 SW: ROM SPG 5.10` · `RCInput: decoding IBUS(1)` · PreArm pil/emniyet satırlarının kaybolması · `starting/finished motor test` | `REVIEW_LOG.md` D-426 §1 (satır 29819–29829) | Mission Planner `Messages` sekmesi, birebir yapıştırma (OLCUM); 4/4 yön, SiK, mod anahtarı **BEYAN** | 2026-09-05 |
| 51 | 4.7.1 flash sonrası `Compare Params` **Missing 9 params** (SYSID_THISMAV, SR1/SR2_POSITION, SR1/SR2_EXTRA3, RTL_ALT, LAND_SPEED, WPNAV_SPEED, ARMING_CHECK) | `REVIEW_LOG.md` D-425 (satır 29718) | Mission Planner `Compare Params` | 2026-09-05 |
| 52 | Firmware 4.5.7 sabit: `firmware/arducopter.apj` **1.585.371 B**, `board_id` **56**, `firmware/firmware-version.txt` = `4.5.7-FIRMWARE_VERSION_TYPE_OFFICIAL` | `scripts/pixhawk_firmware_indir.py` (`SURUM = "stable-4.5.7"` satır 74, `BOARD_ID = 56` satır 54) · kapı `tests/test_pixhawk_firmware_yolu.py` (**10** test, `grep -c "def test_"`; firmware yoksa `skipTest`) | `python scripts/pixhawk_firmware_indir.py` · `ls -l firmware/` | 2026-09-05 |
| 53 | Künye farkı: ESC **"60 A V2"** ×4 (plan 80 A), güç modülü **PM06** (plan PM02), RC alıcı **FS-iA6B** teyit | `REVIEW_LOG.md` D-426 §3 (satır 29852–29854) | **takım üyesi beyanı**, kutu açılışı — etiket fotoğrafı yok (§4.13.4 madde 1) | 2026-09-05 |
| 54 | 5 Eylül'de yapılmayan/ölçülemeyen: RC failsafe, ESC kalibrasyonu, parametre dökümü (**yok**; 6 Eylül'de alındı: `arducopter_fda_20260906.param`, D-428 §5g), pil gerilimi ±0,1 V, pusula, accel teyidi, BEC kırmızı tel | `REVIEW_LOG.md` D-426 §4 (satır 29863–29869) | — (tutanak; ölçüm yok) | 2026-09-05 |
| 55 | Şablon failsafe/çit parametreleri: `RC_PROTOCOLS,4` (:101; sahada 1'e alındı, geri alınmadı — D-426 §2, satır 29836) · `FS_THR_ENABLE,1` (:129; yorum :128 **varsayım**) · `FS_GCS_ENABLE,1` (:134) · `BATT_FS_LOW_ACT,2` / `CRT_ACT,1` (:120/:123) · `FENCE_ENABLE,1` / `FENCE_ACTION,1` (:140/:154) · `RTL_ALT,3500` (:161) | `config/pixhawk/arducopter_fda.param` (31 parametre, Copter-4.5 kaynağı, satır 17) | `tests/test_faz_b_pixhawk_sablon.py` (**12** test) — iç tutarlılık; kart değeri **dökümsüz** | 2026-09-05 |
| 56 | Kuru koşu 4 Eylül (01:00 ve 09:52): **9 GEÇTİ · 0 DÜŞTÜ · 1 SAHİPSİZ (motor)**, `cikis_kodu` 1; 09:52 `sure_ms` cikarim 3304,4 (CPU) | `results/faz_b_oncesi/cuma_kontrol/kuru_kosu_0904.txt` · `results/saha_kuru_kosu_20260904_010058/ozet.json` · `results/saha_kuru_kosu_20260904_095222/ozet.json` | `scripts/saha_kuru_kosu.py` | 2026-09-04 |
| 57 | Jetson açılış kuru koşuları 4 Eylül: udp `[YOK]: 7` · sik `[YOK]: 9`, ikisi de `cikis 3` (ana makine Windows, beyanlar tam); saha açılış kartı `exit=0` | `results/faz_b_oncesi/cuma_kontrol/jetson_udp_0904.txt` · `jetson_sik_0904.txt` · `saha_baslat_0904.txt` | `bash jetson_paket/jetson_baslat.sh --kuru` · `scripts/saha_baslat.py --komutlar` | 2026-09-04 |
| 58 | Paket aynası **18** dosya; saha belleği MANIFEST **405** dosya, ~1268,5 MB (jetson_paket 343 · wheels 51); mühür `DONDURULMADI` | `results/faz_b_oncesi/cuma_kontrol/paket_0904.txt` · `bellek_0904.txt` · `muhur_0904.txt` | `scripts/jetson_paket_hazirla.py` · `scripts/bellek_hazirla.py` · `scripts/surum_dondur.py --dogrula` | 2026-09-04 |
| 59 | Tam suit 4 Eylül **2104 test · OK (skipped=3) · 390,131 s** (aynı dosya; satır 2'deki 1896 3 Eylül anının sayısıdır) | `results/faz_b_oncesi/cuma_kontrol/tam_suit.txt` (git `3db848c`) | `…\venv\Scripts\python.exe -m unittest discover -s tests` | 2026-09-04 |
| 60 | Tam suit 5 Eylül **2138** test, üç koşum: YKS açıkken 1 FAIL (`test_comms_loopback_gecer`, `WinError 10013`, 5005/5006), kapalıyken OK — ortam, T209 | `REVIEW_LOG.md:29887-29930` (D-427; tablo 29893-29895) · `comms/test_comms.py:35-36` | `unittest discover` + `netstat` / Win32_Process | 2026-09-05 |
| 61 | Runbook komut kapısı: `--izinli-kaynak` eksik komut `EXIT=2`; eski kapı 22/22 yeşildi; yeni kapı **3 test**, mutasyon T1 düştü | `REVIEW_LOG.md:29299-29350` (D-421 §1–§2) · `SAHA_RUNBOOK.md:93-96` | `tests/test_runbook_komutlari_kosuyor.py` | 2026-09-04 |
| 62 | Komut hattı K-1/K-2/K-3: ikili arama (A: 23 OK), `_ack_basabilen_bilesenler`, ofset = pencere min ham fark; **23 OK** · **42 test** | `REVIEW_LOG.md:28989-29055` (D-419 §1) · `comms/iha_komut_alici.py:111,149,155,160,420,523` (ayna `cmp` bayt-eş) | `tests/test_faz_b_iha_komut_alici.py` (23) · `tests/test_iha_komut_saat_ve_tekrar.py` (42) | 2026-09-04 |
| 63 | Saat kilidi: teşhis (2 saat / 1970 / +600 s adım), tekrar savunması (40×/500×/200× → 1 COMMAND_LONG), önce/sonra (7. basamak, 0,25 s); mutasyon **17 + 5** düştü | `REVIEW_LOG.md:29449-29451, 29511-29516, 29547-29549, 29555-29568` (D-422) | aynı testler; `git show HEAD:comms/iha_komut_alici.py` yan yana kıyas | 2026-09-04 |
| 64 | Hakem kanıt kaydı: `KANIT_OLAYLARI` **16** olay, `KANIT_TEKRAR_ARALIGI_S` 30 s; demo **16 satır / 9 olay** (ROTA→ACK→aktarım kanıtı); gerçek koşum **747 satır**, aralık **p50 30,06 s**; öncesi 32 satır / eski adlar | `comms/yks_gui.py:127-151` · `CONTRACTS.md` §6.8 · `results/prova/20260904_103744_8536/hakem_log.jsonl` · `results/prova/20260904_095651_8620/hakem_log.jsonl` · `results/prova/20260903_184612_1660/hakem_log.jsonl` | `tests/test_yks_hakem_kanit_olaylari.py` (22) · `tests/test_yks_hakem_kanit_yolu.py` (6); aralık: `monotonic_s` farkları (python, 5 Eylül) | 2026-09-04 |
| 65 | 5 Eylül tezgâh ÖLÇÜM satırları: `ArduCopter V4.5.7 (2a3dc4b7)`, `Frame: QUAD/X`, `u-blox 1 HW: 000A0000 SW: ROM SPG 5.10`, `RCInput: decoding IBUS(1)`, PreArm pil/emniyet satırları kayboldu, `starting motor test` → `finished motor test`; BEYAN: motor 4/4, SiK bağlandı, modlar | `REVIEW_LOG.md:29819-29829` (D-426 §1) | Mission Planner `Messages` (oturuma yapıştırılan satırlar) | 2026-09-05 |
| 66 | Firmware 4.5.7 sabit: `firmware-version.txt` = `4.5.7-FIRMWARE_VERSION_TYPE_OFFICIAL`, `arducopter.apj` 1.585.371 B, board_id 56, git 2a3dc4b7; 4.7.1'de **9** parametre eksik; `SURUM = "stable-4.5.7"` | `firmware/` (repo dışı, saha belleği) · `REVIEW_LOG.md:29633-29639, 29716-29720, 29787` (D-424/D-425) · `scripts/pixhawk_firmware_indir.py:74` | `scripts/pixhawk_firmware_indir.py` · `tests/test_pixhawk_firmware_yolu.py` (10) | 2026-09-05 |
| 67 | 5 Eylül ÖLÇÜLEMEDİ/yapılmadı: RC failsafe, ESC kalibrasyonu, param dökümü (dosya yok), pil gerilimi, pusula (Jetson takılı değil), accel teyit, BEC teli; künye farkı ESC 60 A V2 / PM06 (BEYAN) | `REVIEW_LOG.md:29848-29870` (D-426 §3–§4) | — (insan girdisi bekliyor) | 2026-09-05 |
| 68 | K0–K8 tablosunun tazeliği: `t63/` altında 1 Eylül 23:30'dan sonra verdikt yok; on değer JSON ile yeniden karşılaştırıldı, fark yok | `scripts/olcum/results/t63/t150_baglama_v36_kabul_verdikt.json` | `ls -lt scripts/olcum/results/t63/ \| head` | 2026-09-05 |
| 69 | Eğitim-val karışıklık matrisi (örnek düzeyi, conf 0,25 · IoU 0,45, n=73): 68/0/22 · 0/108/55 · 70/132/— | `codes/runs/segment/gece_v7a_v35taban/confusion_matrix.png` (+`_normalized.png`; depo dışı, `.gitignore` `runs/`) | Ultralytics 8.4.92 eğitim sonu doğrulaması (`best.pt` = üretim `.pt`, SHA-256 eş; D-115) | 2026-08-26 |
| 70 | Eğitim-val maske P 0,6236 · R 0,4168 (toplam, sınıf bazlı değil) | `codes/runs/segment/gece_v7a_v35taban/results.csv` satır 3 (epoch 2) | Ultralytics eğitim (`scripts/olcum/139_gece_egitim.py`) | 2026-08-26 |
| 71 | v36 sınıf bazlı artefakt YOK; `sinif_bazli` en son v15 | `results/capraz_dogrulama_v15_ft2sinif_20260812/capraz_dogrulama.json` | `scripts/olcum/11_capraz_dogrulama.py` | 2026-08-12 |

---

## 4.15 Bu bölümün kendi sınırı

Yukarıdaki hiçbir tablo, sistemin **görev test uçuşunda çalışacağını**
kanıtlamaz. Kanıtladıkları şunlardır: (a) karar geometrisi 15 deterministik
sahnede iki kolda da doğrudur; (b) algı zinciri sentetik kabul kümesinde on
kapının onunu geçmektedir; (c) haberleşme katmanı gerçek MAVLink çerçeveleri ve
gerçek seri bayt akışı üzerinde koşmuş, iki gerçek kusur bulunmuş ve
kapatılmıştır; (d) yordam, kendi hatalarını **bulup yazacak** kadar
işlemektedir — bu bölümdeki geçilmemiş eşikler, vakum ölçümler ve kaçan
mutantlar bunun kanıtıdır.

**Kanıtlanmamış olan tek şey en önemlisidir: gerçek arenada, gerçek Jetson
üzerinde, gerçek telsizle çalıştığı.** O ölçüm 5–21 Eylül arasındadır ve bu
raporun sonraki sürümünde **sayıyla** yer alacaktır.
