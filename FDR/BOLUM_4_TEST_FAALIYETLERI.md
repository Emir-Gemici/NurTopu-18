# BÖLÜM 4 — TEST FAALİYETLERİ (15 puan)

> **Bu bölümün iddiası.** NAVITAS'ın en olgun tarafı bir model ya da bir kart
> değil, **ölçüm yordamıdır**. Aşağıda önce yordam (bir sayının bu projede nasıl
> "kanıt" sayıldığı), sonra otomatik kapı envanteri, sonra kabul kapılarının
> sonuçları, sonra **geçilmeyen kapılar**, sonra donanım gelmeden koşulan
> entegrasyon testleri ve en sonda **kapanmamış test borcu** yer alır.
>
> **Bu bölümün iddia ETMEDİĞİ.** Hiçbir sayı "sahada çalışır" demez. Arena
> ölçümlerinin tamamı sentetiktir; elimizde **gerçek arena/HTAB karesi yoktur**
> ve maket çekimi yapılmayacaktır. Uçuş testleri 6–19 Eylül planlıdır ve bu
> rapor yazılırken **hiçbiri koşulmamıştır**. Jetson Nano üzerinde gerçek FPS
> **ölçülmemiştir**; SiK 433 MHz RF menzili **ölçülmemiştir**.
>
> **İki araç ayrımı.** Şartname §5.3.2 görev test uçuşu (21 Eylül, Adıyaman)
> **çoklu rotorlu** bir araçla yapılır: 3B baskı quadcopter, Pixhawk 6C + PM02,
> Jetson Nano 4GB, Raspberry Pi HQ (IMX477). Yarışma görevinin (§2.2) aracı
> **sabit kanat + mancınık + paraşüt + İKA**'dır ve ayrı sistemdir. Aşağıdaki
> testlerin **tamamı** algı–karar–haberleşme–yer istasyonu katmanına aittir; bu
> katman iki araçta da aynıdır. Uçuş kontrolcüsü yapılandırması ayrışır ve
> ayrıştığı yerde ayrıca yazılmıştır.

---

## 1. TEST YORDAMI — bir sayı bu projede nasıl kanıt olur

Dört mekanizma birlikte çalışır. Hiçbiri sonradan icat edilmiş bir rapor süsü
değildir; her biri **bu projede bir kez gerçek zarar önlediği için** kuraldır ve
zararın kaydı `REVIEW_LOG.md`'de durur (414 başlık · 408 benzersiz kayıt,
`grep -cE "^### D-[0-9]+"`, 3 Eylül 2026).

### 1.1 Ön kayıt — eşik, sonuç görülmeden yazılır (D-107)

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
1 JSON), `find results -iname "*on_kayit*"` (3 Eylül 2026).

**Ön kaydın somut olarak iş gördüğü dört olay:**

| olay | ön kayıtta ne yazılıydı | ölçüm ne çıktı | sonuç |
|---|---|---|---|
| **Çözünürlük 640** (D-377, `results/b4_fps/ON_KAYIT_INFER_SIZE.md` §5) | *"I2 düşerse → RED. I1 ne olursa olsun."* | I1 = **%21,6** (umut verici), I2 = **−0,204** (tavan −0,02) | **RED.** Karar sırası önceden yazılı olduğu için "kırsalda kazandırıyor, arenada biraz kaybettiriyor" tartışması hiç açılmadı |
| **P2 tampon tavanı** (D-388, `results/p2_seri/ON_KAYIT.md` S5) | tampon **≤ 64 KiB** kalmalı; gerekçe: en uzun meşru çerçevenin 16 katı | ölçülen **1.048.576 bayt** (sınırsız) | **DÜŞTÜ** → kod düzeltildi, **aynı eşikle** yeniden koşuldu; eşik gevşetilmedi |
| **P5 yayın histerezisi** (D-396, `results/p5_histerezis/ON_KAYIT.md`) | H1: toplam çevrilme ≤ %40 | H1 **düştü ve düşük kaldı** | Eşik **gevşetilmedi**; yerine EK-1 ölçütleri (H1a/H1b) *bileşim görülmeden* yazıldı, ölçüm sonra koşuldu |
| **T61 iç tutarlılık** (D-401, `results/t61_ic_tutarlilik/ON_KAYIT.md`) | tur **eşiksizdir**; eşik ancak ikinci bir ön kayıtla, tüm kümede süpürülerek yazılır | dört aday **DOĞRULANAMADI** | Keşif turu eşik **üretmedi**; "alt kümede ayrık görünen eşik tümde ayırmaz" dersi (D-86) korundu |

⚠ Ön kayıt **her zaman** kurtarmadı: `results/gece_20260826/ON_KAYIT.md` §15'te
kullanıcı *"izin veriyorum kurala rağmen"* diye yazdı ve v36 kendi eşiklerini
geçmeden terfi etti. Bu olay §4.1'de tam olarak yazılıdır — ön kaydın rolü
burada da **olayı görünür kılmak** oldu; sessiz bir gevşetme mümkün olmadı.

### 1.2 Mutasyon kontrolü — kapı kaldırılınca DÜŞMELİ

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

**🔴 Dürüst mutasyon skoru — bir kapı takımı zayıf çıktı ve öyle yazıldı.**
`comms/seri_hub.py` için bağımsız çürütücü **25 mutant** üretti; repo suiti
**13'ünü yakaladı** (`results/faz_b_oncesi/curutucu_d405/BULGULAR_OZET.md`,
ham loglar `mut_seri_hub/log_*.txt`). Kaçanların adları ve neyi açıkta
bıraktıkları aynı belgede tek tek yazılıdır: iki öğrenilen tüketiciden yalnız
sonuncusuna fan-out, `OGRENILEN_TAVANI` (32) tahliye mantığı, yeniden açmada
`FrameReader` sıfırlaması, beş fail-visible sayaç yolu. **Bu bir eksiktir ve
kapanmamıştır** (§6).

**🔴 Ölçen aracın kendisi de ölçülür (D-370).** Mutasyon betiği
`scripts/olcum/129_t141_mutasyon_olcumu.py`, `\n` ile biten bir desen arıyordu;
hedef dosya `simulation/scripts/ika_nav.py` **tamamen CRLF**'ti (ölçüldü: 658
CRLF, 0 çıplak LF). Yani **M2′ mutasyonu hiç uygulanmıyordu** ve betik yine
`exit 0` dönüyordu — çıkış kodunu okuyan bir kapı bunu **başarı** sanardı.
İki önlem geldi: desen dosyanın kendi satır sonuna uyarlanır, ve **uygulanmayan
mutasyon artık `exit 1`**'dir. `OLCULEMEDI != GECTI` kuralı çıkış kodu düzeyine
indirildi.

### 1.3 Çürütücü turları — bağımsız ajan kusur arar

**Kural (Anayasa madde 19).** *"Bir iş, onu yazanın onayıyla kapanmaz."* Kodu
yazan, kendi kodunu denetlemez; ayrı bir ajan **kusur bulmakla görevlendirilir**
ve her bulgu **koşulmuş komut + ham çıktı (repro)** ile gelmek zorundadır.
Bulgular kabul edilmeden önce mimar tarafından **yeniden üretilir**.

| tur | kapsam | kadro | hasat | kanıt |
|---|---|---|---|---|
| **D-383** (1 Eyl) | telsiz gecikmesi, YKS tazelik, şekil kapısı, nihai ret | 3 bağımsız ajan (357k token, 74 araç çağrısı) | **4 gerçek kusur**: "308 ms ACK gecikmesi" aslında bir **soket zaman aşımı sabiti**; YKS duvar-saati asimetrisi (saat 30 s geri alınınca BAYAT → TAZE); şekil kapısı "H"yi değil "çerçeveli yapıyı" ölçüyormuş; nihai ret sahnedeki **gerçek pedi** öldürüyormuş | REVIEW_LOG D-383 |
| **D-405** (3 Eyl) | mühür atlatma, hub protokol/ACK, arıza/kaynak, kuru-vs-gerçek, test vakumu | 5 mercek | **1 KRİTİK + 16 ÖNEMLİ + 18 KÜÇÜK**, ayrıca **5 çürütülemedi** kalemi | `results/faz_b_oncesi/curutucu_d405/BULGULAR_OZET.md` (30 KB) + `BULGULAR_TAM.md` (81 KB) + repro betikleri |
| **D-407** (3 Eyl) | D-405/D-406 kapanışlarının denetimi | 5 mercek (kota nedeniyle kısmen ana döngüde koşuldu) | **2 gerçek kusur** (Nano belgesi yanlış dizin; mühür kapsamı eksik) + T207 gerçek topolojide **doğrulandı** + köprü sağlam çıktı | `results/faz_b_oncesi/curutucu_d407/` |

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
taraftır**; mimar-dışı denetim açıktır (§6).

### 1.4 Vakum denetimi — test bir şeyi gerçekten kilitliyor mu

**Kural.** Bir testin yeşil olması, bir şey **koruduğu** anlamına gelmez. Test
hiçbir şeyi bağlamıyorsa (payda boş, mutasyon uygulanmıyor, iki kol aynı şeyi
koşuyor) o test bir **vakumdur** ve varlığı zararlıdır: güven üretir, koruma
üretmez.

**Bu projedeki dört vakum, hepsi ölçüldü ve kapatıldı:**

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
   sonra geçti (§5.8).

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

Ek olarak, **her ölçüm betiğinde vakum kapıları** vardır. Örnek (T99,
`results/t99_uretim_imzasi/olcum_20260903.json`): `V1_vakum_yok = true`
(araç maskesi gerçekten dolu — 7/260 karede 252–1787 px), `V3_tek_cikarim = true`
(kare başına 1 segmentasyon çağrısı, sayaçla), `V4_determinizm = true`.
🔴 Aynı ölçümün dürüstlük notu: ilk duman koşumunda (8 kare) V1 **düşmüştü**,
tam kümede geçti — *"küçük örnekle 'vakum' hükmü verilseydi yanlış olurdu."*

### 1.5 Bu dördünün ürettiği rapor kuralı

| # | kural | bu bölümde nerede işliyor |
|---|---|---|
| 1 | Her sayı bir artefakttan gelir (dosya yolu + üreten betik) | §7 Kanıt dizini |
| 2 | `ÖLÇÜLEMEDİ ≠ GEÇTİ` | §6 Kalan test borcu |
| 3 | Geçilmeyen kapı geçilmedi diye yazılır | §4 |
| 4 | Sentetik ölçüm saha başarımı diye sunulmaz | §3 kapsam uyarısı |

---

## 2. OTOMATİK KAPI ENVANTERİ — koşularak ölçüldü

Aşağıdaki iki kapı **bu bölüm yazılırken koşuldu** (3 Eylül 2026); çıktılar ham
olarak konmuştur.

### 2.1 Genel kapı — `codes/test_rota_sentetik.py`

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

### 2.2 Tam test paketi — `python -m unittest discover -s tests`

**Koşum çıktısı (ham, 3 Eylül 2026, yorumlayıcı
`O:\navitas-local-train\venv\Scripts\python.exe`):**

```text
----------------------------------------------------------------------
Ran 1875 tests in 377.827s

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
| **3 Eyl (bu bölüm)** | **1875** | bu koşum |

`tests/` altında **153** adet `test_*.py` dosyası vardır (`ls tests/ | grep -c "^test_"`).

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

### 2.3 Kuru koşu — `scripts/saha_kuru_kosu.py`

Saha zincirinin **halka halka** sahiplik denetimi. Çıktı (ham, 3 Eylül,
`results/faz_b_oncesi/cuma_kontrol/cuma_kontrol.txt` §5):

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

🔴 **"SAHİPSİZ" gizlenmiyor.** Gerçek İKA motor sürücüsü yoktur (R12/T149);
donanım kararı gelmeden kapanmaz. FDA görev test uçuşunda (21 Eylül) İKA
kullanılmaz, dolayısıyla bu kopuk halka **o uçuşu engellemez** — ama yarışma
görevi (§2.2.5) için **açık kalemdir**.

### 2.4 Bu envanterin kapsamadığı şey

| kapı kipi | neden koşulamadı |
|---|---|
| `jetson_baslat.sh --kur` / `--kapi` / `--dogrudan` (systemd) | Windows'ta koşulamaz; **Jetson'daki ilk koşum ilk kanıt olacak** (5 Eylül) |
| TensorRT `.engine` derleme ve karar kıyası | `tensorrt` çalışma zamanı PC'de yok (venv'e bilerek kurulmadı); ORT CPU'ya geri düştü ve betik geri düşmeyi **"dönüştü" saymadı** (fail-closed çalıştı) |
| Gerçek MAVProxy | PC'de `[YOK] mavproxy.py (PATH)`; kuru koşu bunu **gizlemez, raporlar** |

---

## 3. KABUL KAPILARI K0–K8 — sonuç tablosu

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

---

## 4. GEÇİLMEYEN KAPILAR — gizlenmiyor

Bu alt bölüm bilerek öne alınmıştır. Üretim modeli, kendi ön kayıtlı
eşiklerinden **ikisini geçmeden** terfi etmiştir; bunun gerekçesi, bedeli ve
eşiklerin **değiştirilmediği** aşağıda yazılıdır.

### 4.1 🔴 v36 · gerçek-kare eşikleri GEÇİLMEDİ

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

### 4.2 🔴 Çözünürlük 640 denemesi REDDEDİLDİ (D-377)

`INFER_SIZE` 512 → 640 denendi. Karar sırası **sonuç görülmeden** yazılıydı.

| ölçüt | eşik | ölçülen | sonuç |
|---|---|---|---|
| I2 · sentetik gerileme yasağı | fark ≤ 0,02 | p_S **0,9846 → 0,7808** (fark **−0,2038**) | 🔴 **DÜŞTÜ**, 10 kat aşarak |
| I3 · en uzun körlük koşusu | ≤ 5 s artış | **51 s → 52 s** | 🔴 **DÜŞTÜ** |
| I4 · FPS bütçesi | maliyet oranı bütçe içinde | oran **1,300**; etkin 0,692 FPS (gerekli 0,472) | geçti |
| I1 · kör kare kurtarma | (karar bağlayıcı değil) | kirli havuz **%21,6** → temiz alt küme **%5,6** | — |

**HÜKÜM: RED.** FPS hiç kısıt değildi; fayda yoktu. Örüntü de yazıldı: 640 bir
**genelleme düzeltmesi değil, ezber yükselticisidir** — eğitimde görülen veride
p 0,574 → 0,703 (koşu 28 → 24), görmediği veride p 0,346 → 0,424 ama **en uzun
körlük 51 → 52** (kötüleşme). Kapıyı belirleyen en uzun koşudur.

⚠ Ön kayıt olmasaydı I1'in %21,6'sı ile I2'nin −0,204'ü aynı masaya konur ve
"kırsalda kazandırıyor, arenada biraz kaybettiriyor" diye **tartılabilirdi**.

### 4.3 🔴 Ölçüm havuzunda sızıntı bulundu ve hüküm düzeltildi (D-376)

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

### 4.4 Düşen ve doğrulanamayan diğer ölçütler (tam liste)

| # | ölçüt | ne oldu | kayıt |
|---|---|---|---|
| 1 | P5 · H1 (toplam çevrilme ≤ %40) | **DÜŞTÜ ve düşük kaldı**; eşik gevşetilmedi, EK-1 ölçütleri bileşim görülmeden yazıldı | D-396 |
| 2 | T61 · dört iç-tutarlılık adayı | **DOĞRULANAMADI**; biri (V varyansı) zayıf ama anlamlı. Küçük örnek yanılttı | D-401 |
| 3 | T52 · ayırt edici ölçüt | **DOĞRULANAMADI**; köprü tavanı 0,55 olduğu gibi kaldı | D-398 |
| 4 | T101 · W2 kapısı | **DÜŞTÜ ve sebebi yazıldı**: iki sayı farklı popülasyon sayıyordu; *"%49,0 vs %29,6 sürüm kayması kanıtı DEĞİLDİR"* | D-400 §3 |
| 5 | D-379 · şekil kapısının "H harfini doğrulama" iddiası | **DARALTILDI**: çürütücü 17 H-olmayan şekil sentezledi, 16'sı geçti. Kapı artık *"ped yapısında"* olduğunu doğrular, **harf kimliğini doğrulamaz** | D-383 §3 |
| 6 | CONTRACTS §12.1 gerçek-kare şerit tabanı (2026-08-27, referans v3) | Kayıt *"Üretim modeli bu kapıyı geçmiyor — kullanıcı kararıyla üretimde kalır; kapı gelecek terfileri bağlar"* der. ⚠ **DOĞRULANACAK:** o satır yazıldığında üretim modeli v35'ti; v36 sonrası yeniden koşulmuş bir ölçüm bu bölümde bulunamadı | CONTRACTS §12.1 |

---

## 5. DONANIM-ÖNCESİ ENTEGRASYON TESTLERİ (Faz A / Faz B)

Kullanıcının emri açıktı: *"aviyonik geldiği an yazılım için ek bir şey yapmamız
gerekmesin."* Aşağıdaki testlerin ortak sınıfı **`KOD_VAR ≠ KOŞUYOR`**: bu
katmanlar bugüne dek yalnız sahte nesnelerle sınanmıştı; `pymavlink` ve
`pyserial` venv'de **kurulu bile değildi** (2 Eylül 2026 öncesi
`find_spec` = `None`).

### 5.1 P1 — MAVLink katmanı ilk kez GERÇEK çerçevelerle koştu (D-387 / D-389)

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

### 5.2 P2 — saha taşıyıcısı (SiK seri) ilk kez GERÇEK bayt akışında koştu (D-388)

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
ölçümü 5 Eylül'e ertelendi ve hâlâ ölçülmemiştir** (§6).

### 5.3 SiK hub — uçtan uca çoğullama ve gecikme (D-404 / D-405)

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

**Aynı turda bulunan ve kapatılmayan hub kusurları (§6'ya taşındı):**
derin iç içe JSON satırında `RecursionError` ile hub sürecinin ölmesi; "portu
tek başına açar" garantisinin kodda zorlanmaması (`SO_REUSEADDR` + `exclusive`
yok → çift başlatma sessiz).

### 5.4 T207 — akış isteği (D-406 / D-407) · KRİTİK sınıf bulgu

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

### 5.5 Kamera köprüsü — dayanıklılık (D-407 §2)

Jetson Nano'nun CSI kamerası (IMX477) `nvarguscamerasrc` ister; üretim çıkarım
süreci ise sistem Python'undan ayrıdır. Köprü (`scripts/kamera_koprusu.py`,
Python 3.6 uyumlu) MJPEG olarak servis eder.

| ölçüm | sonuç |
|---|---|
| bellek sızıntısı (50/150/300 kare) | izlenen bellek **0,48 MB sabit** (tepe 0,74 MB), RSS ~72 MB sabit, iplik 4 |
| 40 ardışık istemci | iplik 4 → 3, `istemci_sayisi=0`, `dusen_kare=0`, `kodlama_hatasi=0`, KIRMIZI log **0** |
| istemci kopma senaryoları (RST, FIN, okumayan istemci, 3'ten 2'si koparken) | hepsi başarılı, üretici yaşadı |
| Python 3.6 uyumu | çürütme **başarısız** (kod doğru): "bulunan" 3.7/3.9 API'leri dokstringdeki **yasak listesi metniydi** |

⚠ **Test vakumu (KÜÇÜK, AÇIK):** K5 kapısı yalnız **söz dizimi** bakıyor
(walrus/posonly/match); **API adı** yakalanmıyor. Öneri: K5'e API kara listesi.

### 5.6 Ekransız kip (D-404 §2 / §8)

**Bloker:** `run_camera` ve `run_video` her karede **koşulsuz** `cv2.imshow`
çağırıyordu. DISPLAY'siz Jetson'da systemd altında ilk karede `cv2.error` →
`Restart=always` döngüsü (şartname §6.2 hands-off ihlali).

**Kapanış:** `--ekransiz` bayrağı; ekransızda görsel **hiç üretilmez**.
🔴 Kritik şart: **karar yolu bayt-eş aynıdır** (Anayasa madde 15).
Bağımsız denetçi bunu doğruladı: karar yolu **6 kipte (4 video + 2 kamera) 23
kayıtlık izle birebir**; `frame_idx`/`fps_buf` artışları `continue`'lardan
öncedir. Hüküm **KOŞULLU GEÇTİ** oldu; şartı §1.2'deki mutant tablosunda.

### 5.7 Kuru koşular — `results/faz_b_oncesi/` (D-404 §4)

Her dosyanın son satırı **gerçek çıkış kodudur**.

| dosya | beklenen | ölçülen |
|---|---|---|
| `jetson_baslat_kuru_udp.txt` | exit 0; 14550/14551/14552 uçları, `/dev/tty` ile hiçbir tüketici yok | **exit 0** |
| `jetson_baslat_kuru_sik.txt` | exit 0; hub satırı `--port /dev/ttyUSB0 --bind 127.0.0.1:5100 --tuketici 127.0.0.1:5007` | **exit 0** |
| `jetson_baslat_kuru_udp_EKSIK_beyan.txt` | **fail-closed**: `[EKSIK] YKS_IP`, `[EKSIK] IKA_IP` | **exit 3** |
| `saha_baslat_komutlar.txt` | YKS satırında `--iha <JETSON_IP>:5007` (D-403 KRİTİK-1) | **exit 0** |
| `surum_dondur_dogrula.txt` | künye yok → "DONDURULMADI" | **exit 3** |
| `seri_hub_help.txt` | CLI `--port --baud --bind --tuketici --log-aralik` | **exit 0** |

🔴 Bu koşumların **hiçbiri saha kanıtı değildir**; yalnız *"ilk koşum kör
olmayacak"* kanıtıdır.

### 5.8 FP16 karar denkliği (D-375) — vakum kapatıldıktan sonra

| ölçüt | eşik | ölçülen | sonuç |
|---|---|---|---|
| F1 · zarar yönü (FP32 doğruyken FP16 yanlış şerit) | 0 | **0/260** | GEÇTİ |
| F2 · karar uyuşması | ≥ 0,98 | **631/633 = 0,9968** | GEÇTİ |

Dört uyuşmazlığın dördü sınır vakasıdır; biri **lehimize** (`sa_000216`: FP32
yanlış şerit, FP16 doğru). Kalan pay yalnız TensorRT katman birleştirmesidir ve
**Jetson'da `.engine` ile ölçülecektir** (§6).

### 5.9 Uçtan uca kare gecikmesi (D-382 / D-383)

36 gerçek karede, üretim zinciri + gerçek telsiz halkası (UDP loopback ACK):
**p95 0,113 s** — tazelik penceresinin (5,0 s) çok altında. Model yükleme 2,64 s
(uçuş öncesi, bütçe dışı).

🔴 **İlk ölçüm yanlıştı ve düzeltmesi kayıtlı:** ilk ölçümdeki ~0,46 s'nin
~0,3 s'si bir **soket zaman aşımı sabiti** çıktı (bağımsız çürütücü buldu,
D-383); düzeltme sonrası telsiz payı ~2 ms (`p50 307,6 → 2,3 ms`).
⚠ Bu hüküm **yalnız UDP loopback yapılandırmasınındır**: üretim seri
varsayılanlarıyla çevrim 1,0 s ölçülmüştü. **Seri telsiz hattı üzerinden uçtan
uca gecikme ÖLÇÜLMEDİ.**

---

## 6. KALAN TEST BORCU — ölçülmeyen, "sorun çıkmadı" diye yazılmaz

### 6.1 Ölçülmemiş olanlar

| # | ne | neden ölçülmedi | ne zaman | eşik |
|---|---|---|---|---|
| 1 | **Gerçek arena / HTAB karesi** | Arena benzeri saha + kırmızı H çekimi yok; **maket çekimi yapılmayacaktır** (kullanıcı kararı) | 21 Eylül'e kadar **açık kalır** | — |
| 2 | **Jetson Nano gerçek FPS** | Donanım 5 Eylül'de geliyor | 5 Eylül | **≥ 0,61 FPS** p50 **ve** p95; türetimi §4.3. **Eşik gevşetilmez** |
| 3 | **SiK 433 MHz RF menzili / kayıp oranı** | Gerçek SiK çifti yok; UDP loopback ve `socket://` köprü kanıt sayılmaz | 5 Eylül+ | RTT p95 < 0,2 s. DDR'deki *">%98, 300 m"* iddiasının kanıtı **yoktur** (R20) |
| 4 | **Uçuş testleri** (hover, Loiter/Auto, canlı algı, 3 tam prova, sıkı prova) | Araç monte edilmedi | **6–19 Eylül** | ≤ 10 dk, 0 müdahale, yanlış güzergâh 0 |
| 5 | **TensorRT `.engine` ↔ PT karar kıyası** | `tensorrt` PC'de yok | Jetson Gün-1 | FP16 payı kapanır |
| 6 | **Gerçek Pixhawk üzerinde EXTENDED akışı ve `--kapi`** | Pixhawk yok | 5 Eylül | `mavlink_dogrula` 3/3 |
| 7 | **`jetson_baslat.sh` systemd / `--kur` / `--kapi` / `--dogrudan`** | Windows'ta koşulamaz | Jetson ilk koşum | kuru çıktı == gerçek `ExecStart` |
| 8 | **Gerçek İKA motor sürücüsü** | Donanım arayüzü kararı verilmedi (R12/T149) | yarışma görevi öncesi | kuru koşuda `motor SAHİPSİZ` |
| 9 | **Pixhawk geofence parametrelerinin kendisi** | Repo dışı (R17) | 5 Eylül | `config/pixhawk/` kanıt olarak |
| 10 | **K5 figür bilgi px** | verdikt JSON'ında `OLCULEMEDI` | — | — |
| 11 | **Nano kurulum belgesinin dış iddiaları** (bionic `python3.8`, `jetson-io` IMX477 menüsü, Qengineering CUDA wheel) | Kaynakla doğrulanmadı; betiğin **gerçek indirmesi** 14/14 aarch64 wheel ile çoğunu dolaylı teyit ediyor | 5 Eylül kart | belge zaten "kapı çıktısını deftere yapıştır" der |

### 6.2 Kapanmamış kapı/test boşlukları (kod doğru, **kilit yok**)

| # | boşluk | risk | kayıt |
|---|---|---|---|
| 1 | `seri_hub` 25 mutantın **12'si kaçtı**: iki öğrenilen tüketiciye fan-out, `OGRENILEN_TAVANI` (32) tahliyesi, yeniden açmada `FrameReader` sıfırlaması, 5 fail-visible sayaç yolu | Sahada YKS ACK'i `rpi_inference`'a ulaşmazsa OPEN_ROUTE tekrarı tükenir | D-405 |
| 2 | Hub derin iç içe JSON'da **RecursionError ile ölüyor**; SiK hattının tek erişim noktası | Tek bozuk çerçeve hattı düşürür | D-405 |
| 3 | Hub "tek sahiplik" garantisi kodda **zorlanmıyor** (`SO_REUSEADDR`, `exclusive` yok) | Çift başlatma sessiz | D-405 |
| 4 | Kamera köprüsü K5 kapısı **API adı** denetlemiyor (yalnız söz dizimi) | Py3.6 uyumu sessizce bozulabilir | D-407 |
| 5 | `rpi_inference` ekransız kipte **SIGTERM işlenmiyor** (T204); `save=True` iken codec yoksa ölü yazıcıya sessiz yazma (T205) | Tanı kaybı; kayıt kaybı | D-404 §8 |
| 6 | Depo `core.autocrlf=true`: ayna/kaynak bayt eşitliği kapıları **kırılgan** — bir turda 11 test bu yüzden düştü (içerik doğruydu, düşen çalışma kopyasıydı) | Yanlış kırmızı | D-407 §4 |

### 6.3 🔴 DENETİM BORCU (Anayasa madde 19)

*"Bir iş, onu yazanın onayıyla kapanmaz."* Aşağıdaki kalemlerde **yazan ile
onaylayan aynı taraftır** ve bağımsız denetim beklemektedir:

1. **D-407 turundaki düzeltmeler** (Nano belgesi dizin hizası, mühür kapsamı) —
   mimar-dışı denetim ya da **5 Eylül'de Jetson'daki ilk gerçek koşum**.
2. **D-404 §7 madde 4** — `jetson_baslat.sh` systemd kipleri Windows'ta
   koşulamadı; Jetson'daki ilk koşum ilk kanıttır.
3. **D-406 K2/T207 kodu** ajanlar tarafından yazıldı; mimar diff/test/mutasyon
   çıktılarını okudu — **bağımsız üçüncü göz yok**.

Bu maddeler kapanmadan ilgili kayıtlar "tamamlanmış" sayılmaz ve bu raporda da
öyle sayılmamıştır.

### 6.4 BEYAN GEREKLİ (insan)

1. **BEYAN GEREKLİ (insan):** 5 Eylül kutu açılışında donanım künyesinin fiziksel
   teyidi — Jetson Nano 4GB, Pixhawk 6C + PM02, Holybro M9N, RPi HQ (IMX477),
   FCHUB-12S V2, 5008 340KV ×4, 12×10 pervane, 2× SiK 433 MHz, 4S 10 Ah 25C.
2. **BEYAN GEREKLİ (insan):** Jetson Nano üzerinde ölçülen p50/p95 FPS değerleri
   (PT ve ONNX; `--cihaz` beyanıyla) — `JETSON_NANO_KURULUM.md` §8.1 kartına.
3. **BEYAN GEREKLİ (insan):** SiK 433 MHz çift üzerinde ölçülen RTT p50/p95,
   paket kaybı ve **menzil** (metre) — `scripts/sik_rf_olc.py` çıktısı.
4. **BEYAN GEREKLİ (insan):** 6–19 Eylül uçuş testlerinin her biri için tarih,
   pilot, log dosyası ve kapı sonucu (`results/prova/` üç klasör).
5. **BEYAN GEREKLİ (insan):** 21 Eylül Adıyaman uçuş alanı izni ve alan
   koordinatları (mühürden sonra **tek izinli değişiklik**, tutanakla).
6. **BEYAN GEREKLİ (insan):** sürüm mührünün basıldığı tarih ve künye commit'i
   (planlı: 17 Eylül; `--dogrula` çıkışı 0 olmalıdır).

### 6.5 Planlanan uçuş test kapıları (6–19 Eylül)

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

---

## 7. Kanıt dizini

| # | sayı / iddia | dosya yolu | üreten betik / komut | ölçüm tarihi |
|---|---|---|---|---|
| 1 | Genel kapı **15/15 · 15/15** (iki kol) | `codes/test_rota_sentetik.py` (stdout) | `…\venv\Scripts\python.exe codes/test_rota_sentetik.py` | 2026-09-03 |
| 2 | Tam suit **1875 test · OK (skipped=3) · 377,827 s** | konsol çıktısı (bu bölümde ham) | `…\venv\Scripts\python.exe -m unittest discover -s tests` | 2026-09-03 |
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
| 18 | Uçtan uca kare gecikmesi **p95 0,113 s**; telsiz payı `p50 307,6 → 2,3 ms` | `results/fdr/GORUNTU_ISLEME_KANIT.md` §4.1b · `REVIEW_LOG.md` D-382/D-383 | 36 gerçek kare, üretim zinciri + UDP loopback ACK | 2026-09-01 |
| 19 | Mutasyon betiğinin CRLF kusuru; `ika_nav.py` **658 CRLF / 0 LF** | `REVIEW_LOG.md` D-370 | `scripts/olcum/129_t141_mutasyon_olcumu.py` (düzeltilmiş) | 2026-08-31 |
| 20 | Ekransız kip: 7/7 mutant yakalandı (ilk turda 4'ü kaçmıştı) | `results/faz_b_oncesi/ekransiz_denetim/mutant_sonuc_9test.txt` · `mutant_kos.py` | bağımsız denetçi ajanı | 2026-09-02 |
| 21 | `seri_hub` mutasyon skoru **13/25**; vakum bulguları | `results/faz_b_oncesi/curutucu_d405/BULGULAR_OZET.md` (+ `BULGULAR_TAM.md`, `mut_seri_hub/log_*.txt`) | 5 mercekli çürütücü turu | 2026-09-02 |
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
| 33 | Suit büyüme dizisi 1489 → 1617 → 1685 → 1826 → 1827 → 1875 | `REVIEW_LOG.md` D-388 §5, D-403 §6, D-404 §5, D-406, D-407 §4 + bu koşum | `unittest discover` | 2026-09-02…03 |
| 34 | Uçuş testi planı ve kapıları (3.1–3.7), takvim | `SAHA_HAZIRLIK_PLANI_20260903.md` §3, §4, §5 | — (plan) | 2026-09-03 |
| 35 | Gerçek donanım künyesi (Nano 4GB, Pixhawk 6C, M9N, RPi HQ, 4S 10 Ah) | `SAHA_HAZIRLIK_PLANI_20260903.md` §0.2 | **kullanıcı beyanı**, 3 Eylül 2026 — kutu 5 Eylül'de açılıp teyit edilecek | 2026-09-03 |
| 36 | Şartname §5.3.1 Tablo 4 (Bölüm 4 = 15 puan) ve §5.3.2 görev kuralları | `results/sartname_bosluk/sartname_metin.txt` s.17–18 | PyMuPDF metin çıkarımı | 2026-08-26 |
| 37 | Yükümlülük haritası R1–R22 (R20 SiK "hâlâ ÖLÇÜLMEDİ", R12 motor "YOK") | `results/sartname_bosluk/rapor.md` | `scripts/…/rapor_uret.py` + elle tarama | 2026-08-26 |

---

### Bu bölümün kendi sınırı

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
