# BÖLÜM 3 — GENEL SİSTEM SPESİFİKASYONLARI (40 puan)

> **Şartname dayanağı (§5.3.1):** *"Ayrıca sistemin gerçek görev koşullarında çalışabilir
> olduğunu göstermek amacıyla nihai mekanik, aviyonik ve yazılım mimarisi, alt sistem
> etkileşimleri ile üretim, montaj ve saha kurulum süreçleri ayrıntılı biçimde belirtmelidir."*
> (`results/sartname_bosluk/sartname_metin.txt` satır 693-696)

---

## 3.0 Bu bölümün okunma kuralı

Bu raporda **hiçbir sayı metne elle yazılmamıştır.** Her sayının yanında onu üreten
artefaktın yolu ve betiği durur; bölüm sonundaki **Kanıt dizini** hepsini tek tabloda
listeler. Projede uygulanan dört yazım kuralı bu bölümde de geçerlidir:

| kural | uygulaması |
|---|---|
| **Ölçülmeyen "ölçülemedi"dir** | Ölçülmemiş hiçbir büyüklük "sorun çıkmadı" diye yazılmaz. `ÖLÇÜLEMEDİ ≠ GEÇTİ` bu projede bir slogan değil, kabul denetçisinin kod satırıdır: alt betik çökerse kapı `OLCULEMEDI` döner ve terfiyi **bloklar** (`scripts/olcum/65_kabul_denetcisi.py:456, 608, 636, 664`). |
| **Geçmeyen kapı "geçmedi"dir** | §3.5.3'te üretim modelinin **ön kayıtlı iki eşiği geçmeden** terfi ettiği açıkça yazılıdır. Gizlenmemiştir; eşikler de gevşetilmemiştir. |
| **Sentetik ölçüm saha başarımı değildir** | §3.5'teki K0–K7 ölçümlerinin tamamı sentetik arena kümesindedir. Kabul denetçisi bunu her koşumda kendi çıktısına basar. |
| **Emin olunmayan "DOĞRULANACAK"tır** | Kutudan çıkmamış donanımın hiçbir değeri ölçüm gibi sunulmaz; **BEYAN GEREKLİ (insan)** satırı bırakılır (§3.10). |

### 3.0.1 🔴 İKİ AYRI ARAÇ — bu bölümün en kritik kapsam ayrımı

Bu raporda **iki farklı sistem** anlatılır ve karıştırılmaları yorumu bozar:

| | **Yarışma günü aracı** (§2.2) | **Görev test uçuşu aracı** (§5.3.2 · 30 Eylül–3 Ekim; prova 21 Eylül) |
|---|---|---|
| platform | sabit kanat İHA + **mancınık** fırlatma | **çoklu rotor (quadcopter)**, dikey iniş-kalkış |
| iniş | **paraşüt** | motorlu iniş (`NAV_LAND`) |
| ikinci araç | **İKA** (diferansiyel sürüş) zorunlu | **İKA yok** |
| alan | HTAB / İHA-UB (300 m) | **20 × 20 m** simüle test alanı |
| irtifa | görev planına göre | **asgari 30 m** |
| süre | İHA 900 s · İKA 600 s | **tüm operasyon 600 s** |
| aktarım hedefi | YKS **ve** İKA | **yalnız YKS** (hakem canlı onaylar) |

Bu ayrım yazılımda da uygulanmıştır: `yks_gui --fda` bayrağı ayrı bir görev kipi kurar
(`CONTRACTS.md` §6.7). Ayrımın nasıl uygulandığı §3.6.6'dadır.

### 3.0.2 DDR → FDR revizyonu (şartname §5.3.1: *"bütün revizyonlar FDR kapsamında sunulmalıdır"*)

DDR aşamasında beyan edilen aviyonik listesi ile **fiilen tedarik edilen donanım farklıdır**.
Fark gizlenmez; tablo aşağıdadır ve gerekçesi §3.2'dedir.

| kalem | DDR beyanı (`navitas-teknofest/references/avionics_software.md`, `ddr_requirements.md`) | **FDR gerçeği** (kullanıcı beyanı 3 Eylül 2026, `SAHA_HAZIRLIK_PLANI_20260903.md` §0.2) |
|---|---|---|
| görev bilgisayarı | Jetson **Orin NX** (16 GB) | **Jetson Nano 4GB** |
| uçuş kontrolcüsü | Pixhawk **6X** | **Pixhawk 6C** + PM02 |
| GNSS | Holybro **M10** | **Holybro M9N** |
| kamera | Arducam IMX477 | **Raspberry Pi HQ (IMX477, CSI)** |
| RC | TBS Crossfire | **FlySky FS-i6 / FS-iA6B (iBUS)** |
| İKA bilgisayarı | Raspberry Pi 5 | **tedarik edilmedi** — İKA hattı finale bırakıldı |
| model | YOLOv8-**seg nano**, NCNN, 640 | **YOLOv8m-seg**, `navitas-seg-v36-512`, PyTorch/ONNX, **512** |

> ⚠ **DOĞRULANACAK:** DDR referans notlarındaki güç/batarya tabloları ("Tüm değerler tahmini")
> FDR donanımına **taşınmamıştır**. FDR'nin güç bütçesi 5 Eylül montajında ölçülecektir (§3.10).

---

## 3.1 Sistem mimarisi — üç istasyon ve aralarındaki mesaj akışı

### 3.1.1 İstasyonlar

| istasyon | çalıştığı donanım | sorumluluğu | üretim kodu |
|---|---|---|---|
| **İHA / görev bilgisayarı** | Jetson Nano 4GB (Pixhawk 6C'ye bağlı) | kamera → algı → costmap → A* rota → karar eşikleme → telsiz yayını; iniş kanıtı; komut alımı | `codes/rpi_inference.py`, `comms/iha_sender.py`, `comms/iha_inis_yayinci.py`, `comms/iha_komut_alici.py` |
| **YKS / hakem ekranı** | saha dizüstü (Tk arayüzü) | canlı rota + ret sebebi gösterimi, iki aşamalı hakem onayı, kronometreler, komut üretimi | `comms/yks_gui.py`, `comms/kamera_istemci.py` |
| **İKA** | (yarışma günü) diferansiyel sürüş aracı | rota önbelleği, sürüş izni kilidi, waypoint takibi | `comms/ika_receiver.py`, `simulation/scripts/ika_nav.py`, `simulation/scripts/ika_surucu.py` |

Üç istasyon **tek bir mesaj sözleşmesiyle** konuşur: satır sonu (`\n`) ile çerçevelenmiş
JSON, taşıyıcıdan bağımsız (UDP simülasyon / SiK 433 MHz saha). Sözleşmenin tamamı
`CONTRACTS.md` §6'dadır; kod `comms/protocol.py`.

### 3.1.2 Mesaj tipleri

| tip | üretici | alanlar | anlam |
|---|---|---|---|
| `OPEN_ROUTE` | İHA | `road` (1=sol, 2=orta, 3=sağ), `conf`, `ref_xy`, `waypoints` | doğrulanmış açık güzergâh |
| `NO_ROUTE` | İHA | `sebep`, `detay` | rota üretilemedi — **sessizlikten farklıdır** |
| `HEARTBEAT` | herkes | `node`; İHA ayrıca `karar_yas` | hat canlılığı + **algı yaşı** |
| `ACK` | YKS / İKA | `ref` (seq), `ref_tip` | alındı onayı |
| `CMD` | YKS | `cmd`, `hedef` | operatör komutu (`IKA_GO`, `ARM`, `PARACHUTE`, …) |
| `IHA_LANDED` | İHA | `seq` | Pixhawk kanıtlı iniş bildirimi |

**Yayın kuralı (K1, `CONTRACTS.md` §6.5):** her karede **tam bir** mesaj çıkar —
`OPEN_ROUTE` **veya** `NO_ROUTE`. Sessizlik yoktur. Ret sebepli bir karar hiçbir koşulda
`OPEN_ROUTE` olamaz; güven kapısı **çoğaltılmaz**, tek yerde durur
(`comms/iha_sender.py:145 send_open_route`).

### 3.1.3 ACK bağlama sözleşmesi (`ref` / `ref_tip`) — ölçülmüş bir kusurun ürünü

`seq` sayaçları **düğüm başınadır.** YKS'nin `IKA_GO` `seq`'i ile İHA'nın `OPEN_ROUTE`
`seq`'i çakışabilir; tipsiz eşleme, hub fan-out'unda **çapraz kabul** üretiyordu (ölçüldü,
`REVIEW_LOG.md` D-405 Q4 / T206). Sözleşme:

- `ACK.ref_tip` alanı, onaylanan mesajın `type`'ını taşır (`"OPEN_ROUTE"`, `"NO_ROUTE"`,
  `"CMD"`, `"IHA_LANDED"`). Üretici: `protocol.ack(ref, node, ref_tip)`.
- Alıcı, `ref_tip` varsa `ref` **ve** tiple eşler; yoksa yalnız `ref` ile — **geriye
  uyumlu**, eski ACK'lar reddedilmez.
- Kural **her iki uçta** geçerlidir: YKS tarafı `AckliTekrar.ack_geldi`, İHA tarafı
  `IhaSender._tekrarli_gonder`.
- **Bilinmeyen tip sessizce yok sayılır** — geriye uyumluluk bunun üzerine kuruludur
  (`CONTRACTS.md` §6.1).

### 3.1.4 Mesaj akışı — yarışma günü kipi (§2.2)

```
        ┌──────────────────────── İHA (Jetson Nano 4GB) ────────────────────────┐
        │  CSI kamera ──► kamera köprüsü ──► rpi_inference (algı+rota+karar)    │
        │        Pixhawk 6C ──► MAVLink çoğullayıcı ──┬─► irtifa (mpp)          │
        │                                             ├─► iniş kanıtı           │
        │                                             └─◄─ komut aktarımı       │
        └───────────┬──────────────────────────────────────────┬────────────────┘
                    │ OPEN_ROUTE / NO_ROUTE / HEARTBEAT        │ IHA_LANDED
                    │ (ACK'li, 8 tekrar × 0,25 s)              │ (ACK'li)
                    ▼                                          ▼
   ┌────────────────────────────┐                 ┌──────────────────────────────┐
   │   YKS  (hakem ekranı)      │                 │            İKA               │
   │  · rota + ref_xy çizimi    │  CMD(IKA_GO)    │  · rota önbelleği (latest)   │
   │  · NO_ROUTE sebebi (kırmızı)│ ───────────────►│  · sürüş izni kilidi         │
   │  · ONAY 1/2  (canlı görüldü)│                 │  · waypoint takibi           │
   │  · ONAY 2/2  (İKA'ya aktarıldı) ◄─────────────┤  ACK(ref_tip="OPEN_ROUTE")   │
   │  · kronometreler (900/600 s)│  ACK(ref_tip="CMD")                            │
   └──────────────┬─────────────┘                 └──────────────────────────────┘
                  │ ACK(ref, ref_tip)  ──►  İHA           sür ⟺ (geçerli OPEN_ROUTE)
                  ▼                                            ∧ (İHA inişi tamam)
        hakem sözlü onayı (§2.2.3)                             ∧ (YKS'den IKA_GO)
```

**Kritik nokta — İKA'nın ACK'i YKS'ye de gider.** Denetimde ölçüldü ki 2. hakem onayı
("İKA'ya aktarıldı") hiçbir kanıta dayanmıyordu: İKA'nın ACK'i yalnız gönderene (İHA)
dönüyordu (`results/sartname_bosluk/rapor.md` R6). Sözleşme değişti: İKA ACK'i **hem**
gönderene **hem** bildiği YKS akranına gider; YKS düğmesi **fail-closed**'dur — geçerli
rota `seq`'i için `ACK(ref_tip="OPEN_ROUTE")` ekranda görünmeden 2. onay verilemez
(`CONTRACTS.md` §6.6). UDP kurulumunda `--yks host:port` **fiilen zorunludur**: şartname
sırasında `OPEN_ROUTE`, `IKA_GO`'dan **önce** gelir, yani YKS adresi `IKA_GO`'dan
öğrenilemez.

### 3.1.5 Mesaj akışı — FDA görev test uçuşu kipi (§5.3.2 · 30 Eylül–3 Ekim)

```
   İHA (çoklu rotor)                              YKS (hakem ekranı, --fda)
   ─────────────────                              ─────────────────────────
   rpi_inference ──OPEN_ROUTE/NO_ROUTE──────────► rota + şerit no + güven
                 ──HEARTBEAT(karar_yas)─────────► tazelik kutusu (≤ 5 s)
                 ◄────────────ACK(ref_tip)─────── ONAY 2/2
                 ──IHA_LANDED───────────────────► görev süresi biter
   iha_komut_alici ◄──CMD(ARM/DISARM)──────────── ARM kilidi

   İKA halkası YOK  ·  PARAŞÜT düğmesi KAPALI  ·  IKA_GO gönderilmez
   Onay dayanağı: "FDA §5.3.2: İKA yok — onay YKS aktarımına dayanır"
```

### 3.1.6 Alıcı davranışı — bağlayıcı kurallar (`CONTRACTS.md` §6.1)

1. `NO_ROUTE`, `latest` içindeki **son geçerli rotayı EZMEZ**; ayrı alana yazılır.
2. `NO_ROUTE` **geçici** bir durumdur. İHA kare kare tarar; bir karede rota bulunamaması
   görevi iptal etmez, alıcı dinlemeye devam eder.
3. Sürüş sırasında `NO_ROUTE` gelirse araç **güvenli duruşa** geçer; yeni geçerli
   `OPEN_ROUTE` gelince devam eder.
4. `HEARTBEAT`teki `karar_yas` alanı **yoksa** yaş BİLİNMİYOR demektir; alıcı **taze
   saymaz**. Gerekçe ölçülmüştür: 45–51 s süren bir algı körlüğünde heartbeat akmaya
   devam ediyordu (`REVIEW_LOG.md` D-374) — **hat canlılığı algı canlılığı değildir.**

---

## 3.2 Nihai mekanik yapılandırma

### 3.2.1 Görev test uçuşu aracı — 3B baskı quadcopter (§5.3.2; prova 21 Eylül, resmî uçuş 30 Eylül–3 Ekim)

Kaynak: kullanıcı beyanı 3 Eylül 2026, `SAHA_HAZIRLIK_PLANI_20260903.md` §0.2.
**Aviyonik kutusu 3 Eylül itibarıyla açılmamıştır**; künye 5 Eylül montajında kutudan
çıkanla teyit edilecektir.

| kalem | değer | durum |
|---|---|---|
| Gövde | Quadcopter, **3B baskı** (`dronesolid/`: kol, gövde, alt gövde, bacak, dome, GPS tutucu). GPS çubuğu + ayaklar ABS beyaz, kalanı **ABS-CF** siyah | **basıldı ve monte** |
| Motor | **5008 340 KV × 4** | kutuda |
| Pervane | **12 × 10** | kutuda |
| ESC | **80 A, DShot destekli × 4** — ilk uçuşlarda **PWM 400 Hz** (MAIN 1–4) | kutuda |
| Güç dağıtımı | **Matek XCLASS FCHUB-12S V2** (PDB + akım sensörü) | kutuda |
| Uçuş kontrolcüsü | **Pixhawk 6C** + **PM02** güç modülü (POWER1, fabrika kalibreli V/I) | kutuda |
| GNSS / pusula | **Holybro M9N**, direk üstü | kutuda |
| RC | **FlySky FS-i6** + FS-iA6B alıcı (**iBUS**) | **bind edilmedi** |
| Telemetri | **2 × SiK 433 MHz** (drone + YKS) | kutuda |
| Görev bilgisayarı | **Jetson Nano 4GB** (JetPack 4.6.x) | **kurulumu YOK** — §3.7 |
| Kamera | **Raspberry Pi HQ (IMX477, CSI)**, standart lens | kutuda |
| Pil / şarj | **1 × 4S 10 Ah 25C** · iMAX B6 (50 W → ~3 A → ~3 saat dolum) | **günde en çok 2 uçuş** |
| Güç kesme | anahtar yok — **pil fişi çekilir** (XT60/XT90) | yordam: pervane en son, pil en son |

**Elektriksel kaba hesap (beyan, ölçüm değil):** 4S'te asılı uçuşta yaklaşık
10–12 A/motor, tepe 30+ A/motor. PM02'nin sürekli akım sınırı nedeniyle **sürekli tam gaz
yapılmaz**. Bu satır bir **tahmindir**; gerçek akım 5 Eylül'de PM02'nin kendi telemetrisiyle
ölçülecektir.

**Jetson beslemesi — karar ve gerekçesi:** FCHUB'ın 2 A BEC'i Nano için **yetmez**; ayrı bir
**5 V / 5 A UBEC** FCHUB pil pad'lerinden beslenir, Nano'nun barrel jack'ine (J25) girer ve
**J48 jumper takılır**. Ortak GND zorunludur.

**Pixhawk ↔ Jetson bağlantısı:** `TELEM2` → Nano 40-pin UART (`/dev/ttyTHS1`, pin 8 TX /
pin 10 RX / pin 6 GND, **3,3 V**; 5 V hattı bağlanmaz), MAVLink2 57600.
Yedek: micro-USB → `/dev/ttyACM0`. Tek kablo, USB hub yok.

**Kamera optiği — ölçüm değil, hesap:** RPi HQ'nun standart 6 mm geniş açı lensinde yatay
FOV yaklaşık 55–63°; 30 m irtifada kare genişliği ≈ 31–37 m olur ve **20 × 20 m alan tek
karede sığar**. 16 mm lensle ≈ 12 m olurdu ve sığmazdı. ⚠ Bu bir **hesaptır**; `--fov`
değeri 5 Eylül'de `kamera_dogrula` ile **ölçülecek** ve beyan ölçümle değiştirilecektir.

### 3.2.2 Yarışma günü aracı (sabit kanat + mancınık + paraşüt + İKA)

**BEYAN GEREKLİ (insan):** Sabit kanat İHA gövdesi, mancınık, paraşüt podu ve İKA şasisinin
nihai mekanik künyesi, kütle dağılımı ve montaj fotoğrafları bu bölüme eklenecektir. Bugün
repoda bu sistemlerin **ölçülmüş** hiçbir mekanik verisi yoktur; DDR'deki BOM tahminidir
(§3.0.2) ve buraya taşınmamıştır.

**Yazılım tarafı hazır ve kilitlidir:** §2.2 yarışma kipi `yks_gui`'nin **varsayılan
kipidir** ve FDA kipi eklenirken **bayt-eş** korunmuştur (regresyon testi:
`tests/test_faz_b_yks_fda_kipi.py` senaryo 2 — yarışma kipinde İKA kanıtsız onay hâlâ
REDDEDİLİR).

### 3.2.3 Bugün ölçülmemiş mekanik büyüklükler

| büyüklük | durum |
|---|---|
| kalkış kütlesi (gerçek tartı) | **ÖLÇÜLEMEDİ** — 5 Eylül §2.1: her parça tartılır ve fotoğraflanır |
| ağırlık merkezi | **ÖLÇÜLEMEDİ** — 5 Eylül §2.2, ölçüt CG ± 1 cm |
| titreşim (`VIBE`) | **ÖLÇÜLEMEDİ** — ölçüt uçuşta `VIBE` < 30 |
| pusula ofseti | **ÖLÇÜLEMEDİ** — ölçüt < 300 |
| itki / asılı kalma akımı | **ÖLÇÜLEMEDİ** — PM02 telemetrisiyle ölçülecek |
| uçuş süresi (4S 10 Ah ile) | **ÖLÇÜLEMEDİ** — hesap yapılmadı, tahmin yazılmaz |

---

## 3.3 Aviyonik mimari

### 3.3.1 Güç ve sinyal topolojisi

```
  4S 10Ah LiPo
      │ XT60/XT90  (tek güç kesici: fiş)
      ▼
   ┌────────┐   6-pin    ┌──────────────┐
   │  PM02  ├───────────►│  Pixhawk 6C  │  POWER1  (5,1–5,3 V · BATT_MONITOR=4)
   └───┬────┘            │              │
       │                 │  TELEM1 ─────┼──► SiK 433 MHz  ──►  YKS (MAVLink)
       ▼                 │  TELEM2 ─────┼──► Jetson UART /dev/ttyTHS1 (MAVLink2 57600)
  ┌─────────────┐        │  MAIN 1..4 ──┼──► ESC ×4  ──► motor 5008 340KV ×4
  │ FCHUB-12S V2│        │  RCIN ◄──────┼─── FS-iA6B (iBUS)
  └──┬───────┬──┘        │  GPS1  ◄─────┼─── Holybro M9N
     │       │           └──────────────┘
     │       └──► 5V/5A UBEC ──► Jetson Nano J25 (+ J48 jumper)
     └──► ESC ×4 güç                         │
                                  CSI ◄──────┴── Raspberry Pi HQ (IMX477)
```

### 3.3.2 🔴 MAVLink çoğullayıcı — Jetson'da ZORUNLU (`CONTRACTS.md` §7.4 · D-403)

**Bu sözleşme ölçülmüş bir kusurdan doğdu.** Denetimde görüldü ki Pixhawk'ı **iki** üretim
süreci ayrı ayrı açıyordu — `codes/rpi_inference.py:314` (irtifa okuyucu) ve
`comms/iha_inis_yayinci.py:170` (iniş kanıtı) — ve **üçüncüsü** eklenmek üzereydi
(`comms/iha_komut_alici.py`, paraşüt/ARM aktarımı). Seri port (`/dev/ttyACM0`) **tek
sahiplidir**: ikinci süreç ya açılamaz ya birincinin akışını çalar. `inis_kaniti._mav_sahiplen`
süreç **içi** sahipliği koruyordu; süreçler **arası** koruma yoktu. Kılavuzlarda çoğullayıcı
hiç geçmiyordu (grep sayımı: **0**).

**Bağlayıcı kural:** Jetson'da seri portu **yalnız çoğullayıcı** açar (mavlink-router veya
MAVProxy `--out udp:127.0.0.1:1455N`); her tüketici kendi UDP ucundan bağlanır.

| tüketici | uç | yön |
|---|---|---|
| `rpi_inference --mavlink` | `udp:127.0.0.1:14550` | okur (irtifa → `mpp`) |
| `iha_inis_yayinci --mavlink` | `udp:127.0.0.1:14551` | okur (`landed_state`) |
| `iha_komut_alici --mavlink` | `udp:127.0.0.1:14552` | **yazar** (`COMMAND_LONG`) |

Hiçbir üretim süreci `--mavlink /dev/tty*` ile doğrudan açılmaz; kural **kodla** kilitlidir
(`iha_komut_alici --mavlink` seri cihazı reddeder, ancak `--seri-pixhawk-bilerek` ile aşılır).

**Kapı:** `scripts/mavlink_dogrula.py` üç uçta **aynı anda** koşar ve şunları arar:
`HEARTBEAT` sysid eşleşmesi, `GLOBAL_POSITION_INT ≥ MAVLINK_KONUM_ASGARI_HZ` (**4,0 Hz**),
`EXTENDED_SYS_STATE ≥ MAVLINK_DURUM_ASGARI_HZ` (**1,0 Hz**).

**Eşikler uydurulmadı, tüketicinin sözleşmesinden türetildi** (`codes/karar_sozlesmesi.py`
sonu, gerekçe yorumda):
- `TELEMETRI_IRTIFA_TAZELIK_S = 0,50 s` → pencereyi sürekli dolu tutmak için Nyquist 2 Hz,
  paket kaybı/jitter için 2× pay → **4 Hz**. Altında irtifa penceresi aralıklarla boşa düşer
  ve rota kesik kesik `OLCEK_YOK` olur.
- `yerde_mi` **3 ardışık** (`ON_GROUND` + düşük irtifa) çifti ister; 1 Hz'de kanıt ≤ 3 s'de
  oluşur → **1 Hz**. Daha yavaşı iniş kanıtını şartname süresi içinde üretemez.

> ⚠ **Gerçek Pixhawk üzerinde bu kapı henüz KOŞULMADI** — kart kutudadır. Kapı 5 Eylül'de
> koşulacaktır (`FAZ_B_GUN_PLANI.md` §1). `ÖLÇÜLEMEDİ ≠ GEÇTİ`.

### 3.3.3 🔴 SiK hub — NAVITAS-çerçeve seri çoğullayıcı (`CONTRACTS.md` §7.5 · D-404/D-405)

§7.4'ün **protokol ikizi**: SiK (433 MHz) kipinde Jetson'daki üç NAVITAS süreci
(`rpi_inference --telsiz-seri`, `iha_inis_yayinci --serial`, `iha_komut_alici --serial`)
aynı `/dev/ttyUSB0`'ı ister. Çözüm `comms/seri_hub.py`: portu **yalnız hub** açar,
tüketiciler kendi UDP kiplerinde kalır — **tüketici kodu değişmez.**

| yön / konu | davranış |
|---|---|
| tüketici → seri | çerçeve hub'ın UDP soketine (`--bind`, varsayılan `127.0.0.1:5100`) gider; hub datagramı olduğu gibi seriye yazar ve göndereni "öğrenilen" kümesine ekler |
| seri → tüketiciler | gelen baytlar kalıcı `FrameReader` ile **tam çerçeveye** toparlanır; her çerçeve `encode(decode(...))` ile tek satır yapılıp statik `--tuketici` listesi ∪ öğrenilenlerin **hepsine** yayınlanır |
| uzun ömürlü tüketici | öğrenilen küme sayı tavanlıdır (`OGRENILEN_TAVANI`); uzun ömürlü her tüketici **statik `--tuketici` ile de** verilir — öğrenme yalnız emniyettir |
| tek sahiplik | hub UDP ucunu `SO_REUSEADDR`'sız açar (ikinci hub `exit 3`); seri port `exclusive=True` (Linux flock) — **çift başlatma sessiz olamaz** |
| dayanıklılık | derin iç içe JSON (`RecursionError`), 4096 B üstü datagram, fan-out `OSError` → sayaç + KIRMIZI log, **süreç yaşar**; `SIGTERM` → `durdur()` |
| seri arızası | seri kapatılır, KIRMIZI log, 1 s'de bir yeniden açma; UDP tarafı yaşar; **arızada gelen çerçeveler düşürülür ve sayılır** (kuyruklanmaz — bayat rota yayınlanmasın) |

**Ölçülen zamanlama (Windows geliştirme makinesi, `CONTRACTS.md` §7.5):** UDP→seri
gecikmesi boşta **p50 10,6 ms / p95 31 ms**; 20 Hz seri girişiyle **p50 45 ms**. Bu değerler
`PARASUT_TEKRAR_ARALIGI_S` (0,20 s) sınırının altındadır. ⚠ **Gerçek SiK radyo üzerinde
ÖLÇÜLEMEDİ** — bu sayılar seri köprü ölçümüdür, RF ölçümü değildir.

**Topoloji (SiK kipi, `jetson_baslat.sh KIP=sik` ile bayt-eş aynı, testle kilitli):**
```
seri_hub --port /dev/ttyUSB0 --bind 127.0.0.1:5100 --tuketici 127.0.0.1:5007
rpi_inference    --yks-hedef 127.0.0.1:5100
iha_inis_yayinci --yks       127.0.0.1:5100
iha_komut_alici  --bind      127.0.0.1:5007
```
**Tek hatta bir kez:** SiK hattında hedef YKS'dir; `--ika-hedef` hub'a **verilmez**.
Gerekçe ölçüldü (D-405): İKA ACK'i SiK'ten hiç gelmediği için `IhaSender` **8 tekrar /
2,11 s** boşa tekrar ediyordu.

### 3.3.4 Akış isteği — üretim `EXTENDED_SYS_STATE`'i hiç istemiyordu (T207, KRİTİK)

ArduPilot `EXTENDED_SYS_STATE`'i **varsayılan akıtmaz**; istenmesi gerekir. Denetimde
(D-406, P kolu) ölçüldü ki üretim kodu bu isteği **hiç göndermiyordu** — yani iniş kanıtı
sahada hiç oluşmayabilirdi ve İKA kilidi hiç açılmazdı.

**Kapatma (T207, `comms/iha_inis_yayinci.AkisIstekcisi`):** başta ve her
`MAVLINK_AKIS_ISTEK_ARALIGI_S = 10 s`'de `SET_MESSAGE_INTERVAL` gönderilir
(`EXTENDED_SYS_STATE` + `GLOBAL_POSITION_INT`, aralık `1e6 / (hz × MAVLINK_AKIS_ISTEK_HIZ_CARPANI)`,
çarpan **2**). `MAVLINK_AKIS_SESSIZLIK_TAVANI_S = 5 s` boyunca `EXTENDED_SYS_STATE` gelmezse
**bir kez** KIRMIZI uyarı basılır ve istek anında yenilenir; toparlanınca yeşile döner.

**Ölçülmüş tasarım tuzağı:** pymavlink `udp:` **sunucu** kipinde akran görülmeden `write`
hiçbir şey göndermez **ve hatayı yutar**. Bu yüzden istek `mav_hedefi_biliniyor_mu` ile
akran görülene dek **ertelenir**, sonra 10 s beklemeden gönderilir.
Kilit: `tests/test_faz_b_akis_istegi.py` **17 test** (gerçek pymavlink/UDP + sahte Pixhawk);
mutasyon MUT-1 (periyodik yenileme kaldırıldı) → 3 test düştü, MUT-2 (sessizlik alarmı
kaldırıldı) → 3 test düştü; diğer 14 kapı her iki mutasyonda da geçti (hedefe özgülük kanıtı).

### 3.3.5 Uçuş kontrolcüsü yapılandırması — parametre ve görev şablonu

`config/pixhawk/arducopter_fda.param` (**31 parametre**, her satırın üstünde NEDEN yorumu)
ve `config/pixhawk/fda_gorev.waypoints` (QGC WPL 110) repoda durur ve
`tests/test_faz_b_pixhawk_sablon.py` (**12 test**) ile kilitlidir. Değerlerin kaynağı
**ArduPilot Copter-4.5 kaynak kodudur** (dosya adları `.param` başlığında); sözleşme
sabitleri `codes/karar_sozlesmesi.py`'den gelir.

**Görev sırası ve süre bütçesi** (`WPNAV_SPEED = 300 cm/s`, `LAND_SPEED = 50 cm/s`,
dosyadan okundu):

| # | komut | değer | gerekçe |
|---|---|---|---|
| 0 | `HOME` | yer tutucu (0°, 0°) | koordinatlar Adıyaman'da girilir |
| 1 | `NAV_TAKEOFF` | **32 m** göreli | şartname ≥ 30 m + **2 m baro/EKF payı**; `rpi_inference` 30 m altını `ASGARI_IRTIFA_ALTI` işaretler |
| 2–5 | `NAV_WAYPOINT` × 4 | 20 × 20 m karenin köşeleri, 32 m | tek pas tarama |
| 6 | `NAV_LOITER_TIME` | **60 s** | YKS canlı aktarım + iki aşamalı onay + hakem ACK penceresi |
| 7 | `NAV_LAND` | — | görev süresi inişte biter |

**Hesaplanan kötü-durum görev süresi: 221,5 s** — koşulan fonksiyon
`tests/test_faz_b_pixhawk_sablon.py::sure_butcesi_s`, girdiler `arducopter_fda.param` +
`fda_gorev.waypoints`. Şartname sınırı `SARTNAME_FDA_OPERASYON_SURESI_S = 600 s`; test
ayrıca **bütçenin yarısını** (300 s) aşmamayı arar ki hakem onayı gecikirse pilotun loiter
uzatma payı kalsın.

> ⚠ Bu bir **plan hesabıdır**, uçuş ölçümü değildir. Rüzgâr, köşe yavaşlamaları, GNSS fix
> bekleme ve hakem etkileşimi bu toplama girmemiştir.

**Cumartesi teyide bırakılan değerler (dosyada TEYİT işaretli):** `BRD_SER2_RTSCTS=0`,
`RC_PROTOCOLS=4` (iBUS), `BATT_FS_LOW_ACT` / `BATT_FS_CRT_ACT`. Ayrıca kutudan çıkanla
doğrulanacaklar: `FRAME_CLASS=1` (quad), `FRAME_TYPE` (X), `MOT_PWM_TYPE=0`,
`SYSID_THISMAV=1`, `SERIAL1`/`SERIAL2` (57600 MAVLink2), `SRx_POSITION` 4 Hz,
`SRx_EXTRA3` 1 Hz, `BATT_MONITOR=4`, `FENCE_ENABLE=1` (irtifa 50 m + poligon),
`RTL_ALT 3500`, `LAND_SPEED 50`, `FS_THR_ENABLE 1`, `FS_GCS_ENABLE 1`,
`BATT_FS_LOW/CRT` (4S: 14,4 / 14,0 V), `ARMING_CHECK=1`.

---

## 3.4 Yazılım mimarisi

### 3.4.1 Üretim algı zinciri — adım adım

Görev yolundaki tek karar zinciri `codes/rpi_inference.py:run_camera` (satır 2183)
içindedir. Adımlar, gerçek çağrı sırasıyla:

```
 kamera karesi (BGR)
   │
   ├─[1]─ _preprocess(img)                       rpi_inference.py:1888
   │        → sq (kare tuval, gri 114 dolgu) · small · icerik=(x0,y0,w,h)
   │
   ├─[2]─ model.predict(small, imgsz=INFER_SIZE) rpi_inference.py:2100
   │        INFER_SIZE = model_registry.json → profiles.competition.imgsz = 512
   │        (çıplak sayı YAZILMAZ — CONTRACTS §8, test_t163_cozunurluk_sozlesmesi.py)
   │
   ├─[3]─ get_masks(results, h, w)               rpi_inference.py:740
   │        → {0: zemin, 1: engel}  (sinif_semasi'nden okunan anahtarlar)
   │        + Katman-2 dedektörleri: ince bariyer (_ince_bariyeri_ekle:827)
   │
   ├─[4]─ kare_olcek_kahini(mpp, canli_olcek, icerik, bgr=...)   rpi_inference.py:449
   │        → mpp (metre/piksel). Kaynak hiyerarşisi CONTRACTS §5.1/§5.4.
   │        mpp YOKSA → NO_ROUTE(OLCEK_YOK). Rota ÜRETİLMEZ.
   │
   ├─[5]─ analyze_path(trav_mask, ..., goruntu=sq, sekil_esigi=HB_SEKIL_ESIGI)
   │        rpi_inference.py:1348 → 2116
   │        · en büyük bağlı bileşen (koridor)
   │        · K-A uç-bant teması (alt+üst bant, içerik dikdörtgenine göre)
   │        · C-uzayı: gecilebilir = (dist ≥ r_gerekli_px)
   │        · açıklık ağırlıklı A*: maliyet = 1,0 + λ·u^p   (λ=3,0 · p=2,0)
   │        · HB pedi görünürse A* HEDEFİ pedin kutusudur (T150/D-386)
   │        → open_path (1|2|3) · path_conf · waypoints · karar_reddi
   │
   ├─[6]─ _rota_kararini_esikle(...)             rpi_inference.py:1775 → 2133
   │        güven < ROTA_GUVEN_ESIGI (0,20) → yol None, waypoints boş
   │
   ├─[7]─ KararYumusatici.suz(open_path, karar_reddi)   karar_sozlesmesi.py:2140
   │        yayın histerezisi, K = KARAR_HISTEREZIS_KARE = 3
   │        (NO_ROUTE ASLA geciktirilmez — §3.4.6)
   │
   └─[8]─ _karari_yayinla(...)                   rpi_inference.py:281 → 2139
            → KararYayinci.karar(...) → IhaSender.send_open_route / send_no_route
            → SiK 433 MHz (veya UDP) → YKS + İKA
```

Aynı zincir `run_video` (satır 2214) ve tek kare için `run_image` (satır 1982) kollarında da
**birebir aynı sırayla** çalışır; ayrım yalnız kaynaktadır.

**İki üretim yolu sorunu kapandı.** Denetimde `analyze_path` (Jetson) ile `rota_bul`
(simülasyon/`jetson_fps`) arasında hangi yolun yayına gittiği **belirsizdi**
(`results/sartname_bosluk/rapor.md` R1). Bugün üretim yayın yolu tektir: `run_camera` →
`analyze_path` → `KararYayinci`. Kuru koşu bunu satır satır kanıtlar (§3.9).

### 3.4.2 Değişmez kural — *"Serbest alan OTORİTEDİR; nesne katmanı yalnızca ÇIKARIR"*

```
serbest = zemin  AND NOT  engel               ← ÇIKARMA EN SON
serbest(K1 ∧ ¬K2)  ⊆  serbest(K1)             ← DEĞİŞMEZ
```

Çıkarmadan sonra serbest alanı **büyüten** hiçbir işlem eklenmez: `cv2.dilate`,
`MORPH_CLOSE`, `MORPH_DILATE`, `bitwise_or`, `np.maximum` — **hepsi yasaktır.** (Bağlı
bileşen alan filtresi bir **silme** işlemidir; sorun değil.) Uygulama:
`codes/costmap_path_finder.py:212-213`.

**Bu kuralın mühendislik değeri:** Katman-2'ye yeni bir dedektör eklemek **monotonik olarak
güvenlidir** — sistem ancak daha güvenli olabilir. İnce bariyer dedektörü (§3.4.2b) tam bu
sayede, model yeniden eğitilmeden eklenebildi.

**Ölçülmüş uyum:** C-uzayı kısıtı için `{dist ≥ r} ⊆ {dist > 0}`; 7 kompozit karede fazla
piksel **0** (`CONTRACTS.md` §5.3).

#### 3.4.2b Katman-2 dedektörü — ince bariyer (T67 · D-92/D-93/D-99)

**Neden var, ölçüldü (model kullanılmadan):** şartname figüründe bariyerin **3644**
pikselinin **%0,0**'ını model engel sayıyor, **%30,9**'unu **zemin** sayıyordu; üretilen rota
bariyeri **59 px** kesiyordu. Korumaların **hiçbiri** ateşlemiyordu (zemin kapısı susuyor,
ret yok, güven 0,75). Rotayı yayından alıkoyan tek şey `OLCEK_YOK` idi — bir kapı değil, bir
**eksiklik**.

🔴 **Dürüst sınır (D-99):** ölçüm zemini gerçek arena **değildir**. Şartname Şekil 1 alt
yazısı: *"Görsel tamamen yapay zeka ile oluşturulmuştur. Gerçek alanı doğrudan
yansıtmamaktadır."* Dolayısıyla bariyerin kırmızı-beyaz görünümü **uydurmadır** ve
dedektörün renk anahtarı (`BARIYER_KROMA_ESIGI = 25`, LAB `a*`) yapay bir görüntüden
kalibre edilmiştir. Gerçek arenada engeller kırmızı **olmayabilir** — o durumda dedektör
**hiç ateşlemez**: hiçbir şey ekler, hiçbir şey çıkarır; sistem T67 öncesi davranışa döner
(fail-safe). **Ayakta kalan gerekçe** şartname **metnidir** (§2.1): kapalı güzergâhlar
*"fiziki engellerle kapatılacaktır"* — ince-engel riski **gerçektir**, yalnız görünümü
bilinmiyor.

### 3.4.3 Koordinat çerçeveleri — üç çerçeve, karıştırılırsa sessizce yanlış güzergâh

| çerçeve | tanım | kaynağı |
|---|---|---|
| **Kaynak** | ham kameranın kendi piksel uzayı (ör. 1600×900) | `cv2.imread` / kamera |
| **Tuval** | letterbox sonrası **kare** uzay (`max(h,w)²`), kenarlar gri `114` | `_preprocess` |
| **İçerik** | tuvalin içindeki gerçek görüntü dikdörtgeni `(x0, y0, w, h)` | `_preprocess` 3. dönüş değeri |

> **Kural:** her oran, eşik ve bölge hesabı **İÇERİK** dikdörtgenine göre yapılır — tuvale
> göre asla.

Kuralın nedeni **ölçülmüş üç ihlaldir** (düzeltildi, tekrarlanmasın diye sözleşmede durur):

| hata | ölçülen sonuç |
|---|---|
| şerit sınırları tuval genişliğine bölünüyordu | 576×1024 portrede net **SAĞ** koridor için **ORTA** dönüyordu → şartname: **0 puan** |
| `min_area_ratio` tuval alanına göreydi | 16:9'da eşik %1 yerine fiilen **%1,78** |
| tohum bandı tuvalin alt/üst %8'iydi | 16:9'da bantlar tamamen gri dolguda kalıyordu → **18/18 karede rota yok** |

**Yerel ↔ dünya:** `OPEN_ROUTE` waypoint'leri `ref_xy`'ye **göreli metre** cinsindendir;
`ref_xy` daima `[0, 0]`'dır (`YAYIN_REF_XY`) çünkü sahada ortak bir dünya çerçevesi yoktur.
İKA kendi çerçevesine **saf öteleme** ile oturtur; **dönme yoktur**
(`simulation/scripts/ika_nav.py:206`).

Piksel → yerel metre dönüşümü: `x = (px − px₀)·mpp`, `y = (py₀ − py)·mpp` — piksel `y`
aşağı, yerel `y` **ileri**. İlk nokta `[0,0]`. Kenar `MAX_SEGMENT_M`'i aşarsa **mevcut kenar
bölünür**, yeni geometri eklenmez; sonuç `rota_geometrisini_dogrula`'dan geçer, geçmezse
`NO_ROUTE(ROTA_GEOMETRI)`.

### 3.4.4 Ölçek (`mpp`) sözleşmesi — fail-closed'ın kalbi

`mpp` = metre / piksel. **İki bağımsız kaynak** vardır:

| # | kaynak | formül | bugün üretilebilir mi |
|---|---|---|---|
| **(a)** | **irtifa + kamera FOV/odak** | `mpp = 2·h·tan(FOV/2)/W_px` · `mpp = h/f_px` | ✅ **birincil** — MAVLink `GLOBAL_POSITION_INT.relative_alt`, tek okuyucu `comms/inis_kaniti.BagilIrtifaOkuyucu` (`comms/inis_kaniti.py:244-300`) |
| (b) | **HB pedinin bilinen 2,0 m kenarı** | `mpp = HB_KENAR_M / pedin piksel kenarı` | ✅ **ikincil, yalnız DOĞRULAR** |

**(b)'nin ölçülen başarımı** (n = 260 sentetik kadraj): tespit **260/260**, merkez hatası
medyan **0,71 px**, `mpp` medyan sapma **%5,2** (p90 **%8,6**).

**İki kaynak çelişirse ne olur — kodda değil sözleşmede tanımlıdır** (`CONTRACTS.md` §5.4):

| durum | seçilen `mpp` |
|---|---|
| yalnız telemetri | telemetri |
| yalnız HB | HB |
| ikisi var, bağıl fark ≤ `OLCEK_CAPRAZ_BANDI` (**0,25**) | **telemetri** (hiyerarşi değişmez; HB yalnız doğrular) |
| ikisi var, fark bandı aşıyor | **hiçbiri** → `("celiskili", fark)` |

🔴 **Çelişkide ortalama ALINMAZ.** İki bağımsız ölçüm çelişiyorsa *hangisinin doğru
olduğunu bilmiyoruz* demektir; uydurma bir orta değer, ölçülmemiş bir ölçeği ölçülmüş gibi
gösterir. Bant `0,25` seçildi çünkü HB'nin ölçülen sistematik sapmasının (**%5,2**)
yaklaşık **4,8 katıdır**: gerçek bir çelişkiyi yakalayacak kadar dar, dedektörün kendi
sapmasını çelişki saymayacak kadar geniş. Ölçüldü: n=260'ta **260 "doğrulandı" · 0
"çelişkili"**.

**Tazelik — bağlayıcı:** irtifa sabit bir CLI değeri değildir. Örneğin yaşı yalnız host
`time.monotonic()` ile ölçülür (Pixhawk saati host saatine **çevrilmez**).
`TELEMETRI_IRTIFA_TAZELIK_S = 0,50 s`; yaş bu sınıra ulaşır/aşarsa, hiç örnek yoksa veya
kaynak sysid değişirse irtifa **yok** sayılır ve `OLCEK_YOK` üretilir. **Bayat son değer
tekrar kullanılmaz.**

**Makullük bandı:** `SARTNAME_ASGARI_IRTIFA_M = 30,0` (§5.3.2) ve `IRTIFA_MAKUL_UST_M = 200,0`.
Bandın dışındaki telemetri **ölçek üretmez**.

🔴 **Kapatılan sessiz varsayım — ölçülmüş bir tuzak.** Eski `costmap_path_finder.olcek_px(None)`
hâlâ `m = 1.0` alıp `r_gerekli_px = 1,10 piksel` döndürür. Bu *"ölçek yok"* değil *"ölçek
1 metre/piksel"* demektir. Kompozit arenada gerçek değer `1,10 / 0,0868 = 12,7 px` — yani
gövde açıklığı sessizce **~11 kat** küçülüyordu ve hiçbir uyarı basılmıyordu. Sayı geriye
uyum için korundu; **görev yolu artık onu kullanmıyor** ve `tests/test_olcek_ve_c_uzayi.py`
farkı kilitliyor.

### 3.4.5 Geometri sabitleri ve C-uzayı

Tek kaynak: `codes/costmap_path_finder.py`.

| sabit | değer | anlam |
|---|---|---|
| `IKA_GENISLIK_M` | 0,70 | İKA gövde genişliği |
| `MASKE_HATA_M` | 0,25 | segmentasyon sınır belirsizliği |
| `TAKIP_HATA_M` | 0,50 | sürüş takip hatası |
| **`R_GEREKLI_M`** | **1,10** | `0,70/2 + 0,25 + 0,50` — **geçilebilirlik yarıçapı** |
| `ALGI_PAYI_M` | 0,25 | engel genişletme payı |
| `AC_M` / `KAPAT_M` | 0,30 / 0,40 | zemin morfolojisi |
| `LAMBDA_ACIKLIK` / `US_ACIKLIK` | 3,0 / 2,0 | A* açıklık cezası `1,0 + λ·u^p` |
| `WP_ARALIK_M` / `MAKS_WP` | 2,0 / 64 | waypoint aralığı ve tavanı |

Geçilebilirlik testi **C-uzayında** yapılır (`gecilebilir = dt_px >= r_gerekli_px`), **ham
maskede asla**. `scipy.ndimage` ve `cv2.ximgproc` bu projede yasak/yok olduğu için koridor
merkezinden geçme davranışı medial-axis yerine **açıklık ağırlıklı A\*** ile elde edilir;
bu **bilinçli bir ikamedir**, eksiklik değil.

**C-uzayının ölçülen etkisi** (arena kompoziti, kusursuz yer gerçeği maskesi, tek değişken
`mpp`; `CONTRACTS.md` §5.3):

| | doğru şerit | yanlış şerit | ret | rota darboğazı | güven |
|---|---:|---:|---:|---|---|
| C-uzayı **yok** | 1/7 | 0 | 6 | **1,0 px** (4 karede) | 0,028–0,117 |
| C-uzayı **var** | **6/7** | **0** | 1 | **13,0–15,0 px** | 0,644–0,744 |

Kalan 1 ret `UC_BANT_TEMAS_YOK`'tur ve C-uzayından **önce de** vardı — K-A'nın kendi
fail-closed reddidir.

### 3.4.6 Yayın histerezisi (K = 3) — analiz katmanına dokunmadan

**Sorun ölçüldü:** şerit seçimi sürekli büyüklükler üzerinde ayrık bir karardır; **binde-4**
algı gürültüsü kararları kareler arasında çevirebiliyordu (T68 ölçümü: tohuma göre 4–7/260;
T92 bant oynaklığı 34/260). Yayımlanan şerit zikzak yaparsa İKA'nın hedefi zikzak yapar.

**Çözüm yayın katmanındadır** (`codes/karar_sozlesmesi.py:2117` `KARAR_HISTEREZIS_KARE = 3`,
sınıf `KararYumusatici`). Analiz katmanına **dokunulmamıştır** (madde 15).

| kural | davranış |
|---|---|
| `NO_ROUTE` / ret | **ANINDA** yayımlanır ve durum sıfırlanır — fail-closed asla geciktirilmez |
| ilk rota, `NO_ROUTE` sonrası ilk rota | ANINDA yayımlanır |
| yayımlanan şeritle aynı şerit | ANINDA yayımlanır (tazelik yenilenir) |
| **farklı** şerit | ancak **K = 3 ardışık** karede aynı yeni şeritle görülürse yayına geçer |
| **H5 tavanı** | bastırma `K − 1` ardışık kareye dayanınca **bir sonraki kare ne olursa olsun** yayımlanır — yayın bundan fazla bayatlayamaz |

H5 tavanı bir tasarım hatasını **birim testi yakaladığı için** vardır: yayımlanan 2 iken
analiz 1/3 arasında salınırsa tavansız sürüm **süresiz** bastırıyordu.

**Ölçüm** (`results/p5_histerezis/olcum_20260903.json`, σ = 2,0/255, kare başına 5 örnek,
n = 260, model v36):

| tohum | ham çevrilme | **yayımlanan çevrilme** | bastırılan | bastırılan `NO_ROUTE` |
|---|---:|---:|---:|---:|
| 7 | 13 | **7** | 6 | **0** |
| 42 | 24 | **11** | 14 | **0** |

Yani çevrilmelerin yaklaşık yarısı yayına hiç çıkmadı ve **hiçbir `NO_ROUTE` geciktirilmedi**.
Gecikme tavanı 3 karedir: uçtan uca p95 0,113 s ile ≈ **0,34 s**, `YKS_TESPIT_TAZELIK_S / 2`
(2,5 s) değerinin çok altında.

> Eşik değişikliği **yeni ön kayıt** ister (`results/p5_histerezis/ON_KAYIT.md`).

### 3.4.7 Yayın sözleşmesi (K1) — `CONTRACTS.md` §6.5

**Neden var:** denetimde ölçüldü ki `codes/rpi_inference.py` `run_camera`/`run_video`
telsize **hiç** yazmıyordu; `OPEN_ROUTE`/`NO_ROUTE` üreticisi yalnız bir Gazebo betiğiydi.
Sahada **İHA kararı YKS'ye ve İKA'ya ulaşmıyordu**
(`results/sartname_bosluk/rapor.md` R4, KRİTİK).

| kural | değer / davranış |
|---|---|
| kurulum | yalnız `--yks-hedef` / `--ika-hedef` / `--telsiz-seri` verilince; **hedef yoksa gönderici hiç yüklenmez, davranış bayt-eş aynıdır** |
| `open_path is None`, sebep yok | `NO_ROUTE(KARAR_YOK)` |
| ölçek yok / geometri bozuk | `NO_ROUTE(OLCEK_YOK)` / `NO_ROUTE(ROTA_GEOMETRI)` |
| `HEARTBEAT` | ayrı iş parçacığı, `IHA_HEARTBEAT_ARALIK_S = 1,0 s` < `IkaReceiver.hb_timeout = 3,0 s` (2 ardışık kayıp bağlantıyı düşürmez) |
| kuyruk | **latest-wins tek yuva**: kamera döngüsü ACK beklemez; ACK'li gönderim ayrı iş parçacığındadır; `stop()` bekleyen son kararı gönderip durur |
| telsiz hatası | kamera döngüsünü **düşürmez**; `yayinci.hata`'ya yazılır ve çıkışta basılır |

`KARAR_YOK` ve `ROTA_GEOMETRI` sebepleri `ROTA_RET_SEBEPLERI` kümesine **girmez** — o küme
analiz katmanının ret sebepleridir; bunlar **yayın katmanının** fail-closed varsayılanlarıdır.

### 3.4.8 Çıplak sayı yasağı (madde 16) — nasıl kilitlendiği

Bu projede ölçülmüş kusurların büyük kısmı algoritma hatası değil, **iki modülün aynı sayıya
farklı anlam vermesiydi.** En pahalı örnek: `iha_haritala.py` çalışma anında
`{0: zemin, 1: moloz, 2: araç}` kuruyor ve `engel_sinif_idler=(1, 2)` veriyordu; eğitim
şemasında `2 = hedef` (H brandası) olduğu için 3 sınıflı bir model bu yola verilseydi
**H brandası ENGEL sayılacaktı** → İKA hedefe hiç ulaşamaz → `P_görev = 0`.

**Çözüm — tek otorite `codes/sinif_semasi.py`, iki ad alanı ayrıldı:**

| ad alanı | sabitler | kim üretir |
|---|---|---|
| **Eğitim sınıfı** | `ZEMIN=0` · `ENGEL=1` · `HEDEF=2` | model çıktısı / YOLO etiketi |
| **Costmap katmanı** | `KATMAN_ZEMIN=0` · `KATMAN_MOLOZ=1` · **`KATMAN_ARAC=10`** | çalışma anı |

Araç katmanı **10**'dan başlar; eğitim sınıf uzayıyla (0..9) **çakışmasın** diye seçildi.
`sinif_semasi` **import anında** `dogrula()` koşar: sabitler çakışırsa **modül yüklenmez**.
Doğrulama `codes/test_sinif_semasi.py` → **8 GEÇTİ / 0 DÜŞTÜ**, içinde bir **pozitif kontrol**
vardır: *"eski şemada hedef ENGEL sayılıyordu"* testi kusuru yeniden üretir.

Aynı disiplin çözünürlük için de geçerlidir: `imgsz` yalnız
`config/model_registry.json → profiles.competition.imgsz` (**512**) üzerinden okunur,
`CONTRACTS.md` §8'de çıplak yazılmaz; kilit `tests/test_t163_cozunurluk_sozlesmesi.py`.

### 3.4.9 Model künyesi ve kayıt defteri fail-closed'u

| alan | değer |
|---|---|
| `model_id` | `navitas-seg-v36-512` |
| mimari | YOLOv8**m**-seg (27,2 M parametre) |
| çıkarım boyutu | **512** |
| arka uç (üretim) | `pytorch` |
| SHA-256 (`.pt`) | `1d1caca6f6da19ea35e69186a048da960ca5188be6ee6d49d6106457cac46911` |
| sınıflar | `{0: traversable, 1: blocked}` |
| ONNX türevi | `f4c9f5fe08883d1aecc9b4ac3ce9f98cea61de2f5298edde5d2c2a7a5056deab` |
| TensorRT `.engine` | `DERLENINCE_YAZILIR` → **yer tutucu = derlenmedi = RED** |

**Türev doğrulaması fail-closed'dur.** Eskiden `model_kayit_dogrula` yalnız **dosya adını**
kıyaslıyordu; her `.engine` "EŞLEŞMİYOR" ile reddediliyor ve Jetson'da TensorRT ancak
`--kayit-dogrulamasiz` ile — yani **fail-closed kapatılarak** — yükleniyordu (D-284, T18
çürütücüsü). Bugün: türevin `sha256`'sı yer tutucu değilse **ve** diskteki dosyanın özetiyle
birebir aynıysa geçer; kayıtsız/yabancı `.engine` **RED**; `kaynak_sha256` üretim `.pt`
özetiyle eşleşmezse türev **YETİM** sayılır ve **RED**.

Saha paketindeki ayna kopya `jetson_paket/config/model_registry.json` ile aynı olmak
zorundadır; nöbetçi `tests/test_t202_jetson_paket_butunlugu.py`.

**Sayısal denklik ölçümleri (kapı değil, ölçüm):**
- **ONNX ↔ PyTorch karar denkliği:** n=260'ta karar **259/260** aynı (1 uyuşmazlık:
  `sa_000215.jpg`, pt=2 · onnx=1); zemin maskesi IoU ortalaması **0,9975**; azami rota
  sapması **172,1 px = 13,443 m**. Ön kayıt kuralı `≤ 5/260` **sağlandı**. ⚠ Koşum CPU
  EP iledir; **TensorRT motorunun kendi denkliği Jetson'da AYRICA ölçülmelidir**.
- **FP16 karar denkliği:** zarar yönü (FP32 doğruyken FP16 yanlış şerit) **0** → GEÇTİ;
  karar uyuşması **0,9968** (eşik 0,98) → GEÇTİ.

---

## 3.5 Karar zinciri kabul kapıları — K0…K8 + K5A

Kapıların tamamı tek betikten koşulur: `scripts/olcum/65_kabul_denetcisi.py`. Eşikler
`REVIEW_LOG.md` D-107'de **sonuç görülmeden** yazılmıştır ve **değiştirilmemiştir**.

### 3.5.1 Kapı tablosu

| kapı | ne ölçer | eşik | ölçülen (bugünkü zincir) | sonuç |
|---|---|---|---|---|
| **K0** | **körlük yok** — model boş maske üretmiyor, figürde zemin görüyor | `figür > 0` · boş maske yok | figür zemin **%2,66** · ham boş **0/67** · copy-paste boş **0/393** | **GEÇTİ** |
| **K1** | rota üretilen kare sayısı | **≥ 230** / 260 | **256/260** | **GEÇTİ** |
| **K2** | rotanın molozdan geçmesi | **≤ %15** | **6/256 = %2,34** | **GEÇTİ** |
| **K3** | **ağır** moloz teması | **≤ %3** | **0/256 = %0,00** | **GEÇTİ** |
| **K4** | arena dışına taşma | **≤ %5** | **2/256 = %0,78** | **GEÇTİ** |
| **K5** | **bariyer kesişimi** (popülasyon) | **= 0 px**, her ölçülebilir karede | **0/178** ölçülebilir kare · toplam **0 px** | **GEÇTİ** |
| **K5A** | bariyer kesişimi — **açılı** bariyer kümesi | K5 ile **birebir aynı** | **0/176** ölçülebilir kare · **0 px** | **GEÇTİ** |
| **K6** | yanlış güzergâh (rota çizgisinin yer gerçeği sınıf 0 üstündeki payı ≥ 0,90 **ve** sınıf 1 üstünde 0 waypoint) | **≤ %5** | **2/256 = %0,78** | **GEÇTİ** |
| **K7** | **YAYINLANAN ŞERİT DOĞRULUĞU** | doğruluk **≥ %95** **ve** payda **≥ 80/88** | **84/85 = %98,82** (payda 85) | **GEÇTİ** |
| **K8** | **gerçek kare kapısı** — üretim karar yolu tek gerçekçi karede kırılıyor mu | `ZEMIN_MASKESI_SUPHELI` **dönmemeli** | zemin kaplaması **0,0444** · karar yolu reddi `UC_BANT_TEMAS_YOK` | **GEÇTİ** |

Kaynak: `scripts/olcum/results/t63/t150_baglama_v36_kabul_verdikt.json` (**1 Eylül
2026**, üretim kipi — hedef bağlaması T150 ile açık), model
`models/navitas_seg_v36_best.pt`. Toplu verdikt: **10/10 kapı GEÇTİ**. Bu koşum,
raporda "bugünkü zincir" diye anılan **tek** koşumdur; Bölüm 4 §3 de aynı dosyayı
kullanır (iki bölüm arasında sayı farkı yoktur).

**Kapıların kendi ayırt ediciliği ölçülmüştür.** Örnek: K5A kümesi (`sentetik_arena_kadraj_ACILI_t189`)
yatay kümenin aynı üreteç/tohum/parametreleriyle, yalnız `--bariyer-acisi 90` eklenerek
üretildi. **Mutasyonla ölçülen ayırt edicilik** (`scripts/olcum/results/t63/t189_ayirt_edicilik.json`):
T184 öncesi dedektör bu kümede **185/260 → 48/260** düşüyor (**52,7 puan**), yatay kümede ise
**181/260 → 181/260** hiç düşmüyor. Yani K5A, yatay kümenin göremediği **dönme körlüğünü**
gerçekten ölçüyor.

### 3.5.2 İki ölçüm hattı — aynı model, farklı karar katmanı

`config/model_registry.json` içindeki `metrics` bloğu **terfi anının** sayılarını taşır
(26 Ağustos, `gece_v7a_kabul_verdikt.json`). §3.5.1'deki tablo ise **bugünkü karar zinciriyle**
yeniden koşulmuş sayılardır. İkisi farklıdır ve **fark modelden değil zincirden gelir**:

| kapı | terfi anı (26 Ağu · registry) | özdenetim (28 Ağu) | **üretim kipi (1 Eyl · bugünkü zincir)** |
|---|---|---|---|
| K1 | 255/260 | 256/260 | **256/260** |
| K2 | 15/255 = %5,88 | 6/256 = %2,34 | **6/256 = %2,34** |
| K3 | 1/255 = %0,39 | 0/256 = %0,00 | **0/256 = %0,00** |
| K4 | 4/255 = %1,57 | 3/256 = %1,17 | **2/256 = %0,78** |
| K6 | 7/255 = %2,75 | 3/256 = %1,17 | **2/256 = %0,78** |

28 Ağustos ile 1 Eylül arasındaki fark **T150 hedef bağlamasıdır**: varış noktası
artık HB'den alınır, rota iki karede daha arena dışına taşmaz. Üç sütun da
saklanır; rapor "bugünkü zincir" derken **en yenisini** (1 Eylül) kullanır.

Aradaki iyileşme T184 (dönme körlüğü) ve T198 (şekil kapısı) düzeltmelerinin karar
katmanındaki etkisidir. **Bu sayı model başarımı değil ZİNCİR başarımıdır** ve öyle
okunmalıdır. Terfi anının sayıları **silinmemiştir**; kayıt defterinde durur.

### 3.5.3 🔴 GEÇİLMEYEN kapı — üretim modeli ön kayıtlı iki eşiği geçmeden terfi etti

Bu bölüm bilerek öne alınmıştır. Kayıt defterinin **kendi cümlesi**
(`config/model_registry.json → metrics.gercek_kare_kapisi.sonuc`):

```text
🔴 ON KAYITLI ESIKLER GECILMEDI: ROTA >= 10 istendi, olculen 8;
   MASKE_YOK <= 10 istendi, olculen 16.
   GECILEN: FP <= 1 (1) ve YANLIS GUZERGAH = 0 (0).
   Terfi bu esikleri GECEREK degil, KULLANICI KARARIYLA yapildi.
   ESIKLER DEGISMEDI ve sonraki terfileri baglar.
```

**Gerçek kare doğrulama kümesi** (`dataset/dji_kirsal_0038_bolum_v3`, iki bağımsız **kör**
etiket geçişinin uzlaşısı; 0038 kareleri eğitime ve erken durdurmaya **girmedi**):

| küme | n | rota | maske yok | TP | FP | FN | yanlış güzergâh | tavan (rota) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `test29` | 29 | **8** (eşik ≥10 ❌) | **16** (eşik ≤10 ❌) | 7 | **1** (≤1 ✅) | 5 | **0** (=0 ✅) | 12 |
| `val82` | 82 | 30 | 35 | 28 | 2 | 15 | 7 | 43 |

**Terfi gerekçesi (kayıtlı):** gerçek karede yanlış güzergâh **15/21 → 7/38**, engel üstü
waypoint **79 → 3**. **Kabul edilen bedel:** K3 0→1, K4 1→4, K6 5→7 (hepsi kapı içinde),
figür zemin oranı düştü, val82 FP 0→2. Dayanak `REVIEW_LOG.md` D-293, ön kayıt
`results/gece_20260826/ON_KAYIT.md` §15, çürütücü çıktıları
`results/gece_20260826/v7a_curut/`.

**Yedek aday silinmedi ve FARKLI HATA YAPAR:** önceki üretim `navitas-seg-v35-512`
(sha `e00f6b8e…`) arena K3/K4/K6'da daha iyidir (0/1/5) ama gerçek karede daha kötüdür.
İki modelin hata profili farklıdır; seçim bir **ödünleşimdir** ve öyle kayıtlıdır.

> **Bu satırın raporda durmasının nedeni:** eşikler sonradan gevşetilseydi bu terfi
> "kapıdan geçti" diye yazılabilirdi. Eşikler değişmedi; bu yüzden sonraki her terfi de aynı
> çıtayla ölçülecektir.

### 3.5.4 Kapıların kapsam sınırı — kabul denetçisinin kendi uyarısı

Denetçi her koşumda şu satırı **kendisi basar**:

```text
⚠ Bu olcumlerin tamami SENTETIKTIR. Hicbiri 'sahada calisir' anlamina gelmez
  (D-88 + D-99, kalici kisit).
```

Kayıt defterinin `_kapsam` alanı aynı şeyi söyler: *"ARENA ÖLÇÜMLERİNİN TAMAMI SENTETİKTİR
(T66 ada kadrajı, n=260); gerçek ARENA karesi YOKTUR — K0..K6 SAHA BAŞARIMI İDDİA ETMEZ."*

🔴 **ARENA BENZERİ SAHA KANITI (kırmızı H + moloz + bariyer) HÂLÂ YOKTUR.** Doğrulama
kümesi aynı gün, aynı kamera, aynı saha türü (kırsal) ve **arena değildir** — "alan dışı"
sorusunu yalnızca **kısmen** kapatır. K8 kapısı da `n = 1`'dir ve dayandığı figür şartnamenin
kendi ifadesiyle *"tamamen yapay zekâ ile oluşturulmuştur"*.

**BEYAN GEREKLİ (insan):** Arena benzeri gerçek saha görüntüsü (kırmızı H brandası + moloz +
fiziki bariyer, ≥ 30 m irtifadan) toplanırsa K0–K8 zinciri bu küme üzerinde yeniden koşulup
sonuç bu bölüme eklenecektir. Bu görüntü bugün **yoktur** ve maket çekimi **yapılmayacaktır**.

### 3.5.5 Ölçülmüş ama kapı OLMAYAN büyüklükler (dürüstlük gereği burada)

| büyüklük | ölçülen | not |
|---|---|---|
| **karar çevrilmesi** (kararsızlık) | v36 **14/260** (tohum 7) · **15/260** (tohum 11) | 🔴 **v35'ten KÖTÜ** (9/260 · 11/260). Eşli ölçüldü — aynı koşum oturumu, aynı gürültü gerçekleştirmeleri. Yön iki tohumda da aynı. Bu, §3.4.6 histerezisinin **var olma nedenidir**. |
| **çatı kaçağı** | **0,0230** (medyan 0,0119) | 55 çatılı gerçek karede tam maske ölçümü. v34 0,9606 → v35 0,0428 → v36 0,0230. Aynı koşumda disk sınaması: çatı→engel 0,9908 · çatı→zemin 0,0000 |
| **gerçek kare zemin kaplaması** | tuval paydası **0,2346** · içerik paydası **0,4171** | Bağımsız (modelsiz) tahmine göre gerçek sürülebilir oran %47–52'dir; v36 o aralığın **altına düştü**. Yani bu terfi *"daha az görüyor"* yönündedir — kabul edilen bedel budur |
| `mask mAP50-95` | 0,155 (val) | **ÖLÇÜM DEĞİL KARAR GİRDİSİ DEĞİL**: val kümesi 0037/0039'dan türetildiği için v35'in temiz-bölüm val'i ile **kıyaslanamaz**. Karara girmedi |

---

## 3.6 Emniyet mimarisi

### 3.6.1 Fail-closed ilkesi — "ölçemiyorsam üretmem"

Sistemin emniyet duruşu tek cümleyle özetlenir: **kanıt yoksa çıktı yoktur.** Uygulamaları:

| durum | davranış | kod |
|---|---|---|
| ölçek üretilemiyor | **rota ÜRETİLMEZ** → `NO_ROUTE(OLCEK_YOK)` | `karar_sozlesmesi.rota_olcek_reddi` |
| ölçek kaynakları çelişiyor | ortalama alınmaz → ölçek **yok** sayılır | `olcek_capraz_kontrolu` |
| güven < `ROTA_GUVEN_ESIGI` (0,20) | yol `None`, waypoint boş; ayrıca yayın katmanında **ikinci savunma** | `_rota_kararini_esikle` + `iha_sender.send_open_route` güven kapısı (`rota_guven_reddi(conf)`, `comms/iha_sender.py:152-155`) |
| zemin maskesi şüpheli | `ZEMIN_MASKESI_SUPHELI` (kaplama tavanı 0,55 · kenar dayanma tavanı 0,40) | `zemin_maskesi_reddi` |
| model kaydı uyuşmuyor | model **yüklenmez** | `rpi_inference.load_model` |
| kamera ardışık 30 kare düşürdü | **kontrollü bitiş** (`KAMERA_BITIS_DUSEN_KARE`) | `KAMERA_DUSEN_KARE_UST_SINIRI = 30` |
| İKA sürücüsü 3 ardışık arıza | son bir durdurma denenir, `navigate` **False** döner | `ARDISIK_HATA_TAVANI = 3` (10 Hz'de ~0,3 s) |
| ölçüm alt betiği çöktü | kapı `OLCULEMEDI` → terfi **bloklanır** | `65_kabul_denetcisi.py` |

**Ret sebepleri kanonik kodlardır** ve hakem ekranında ayrı ayrı görünür:
`OLCEK_YOK`, `ZEMIN_MASKESI_SUPHELI`, `MASKE_YOK`, `BILESEN_YOK`, `UC_BANT_TEMAS_YOK`,
`ALAN_YETERSIZ`, `GORUS_HATTI_KOPUK`, `KENAR_GUVENSIZ`, `DUSUK_GUVEN`, `KORIDOR_DEGIL`,
`HEDEF_YOK`, `ALAN_IHLALI`, `ASGARI_IRTIFA_ALTI`, `KARAR_YOK`, `ROTA_GEOMETRI`.

### 3.6.2 ARM kilidi — "düğme durumu emniyet sinyali DEĞİLDİR"

Ölçülmüş kusur (D-393 §2): `firlatma()` ARM kilidini **düğmenin görsel durumuna** emanet
ediyordu (düğme DISARM'da pasif). Kısayol ya da doğrudan çağrı kilidi aşabilirdi.
**Düzeltme:** `arm_acik` yoksa damga **atılmaz** ve KİLİT loglanır. Bu, projede *T180 sınıfı*
olarak adlandırılan genel kuralın uygulamasıdır: **UI durumu tek başına emniyet sinyali
değildir; eylemin kendisi de reddedilmelidir.**

Aynı kural FDA kipinde kapatılan her düğme için de geçerlidir (§3.6.6).

### 3.6.3 İki aşamalı hakem onayı (§2.2.3)

| adım | ön koşul | ne üretir |
|---|---|---|
| **ONAY 1/2** — "canlı görüldü" | ekranda geçerli `OPEN_ROUTE` (şerit no + güven + waypoint çizimi) | hakem sözlü onayı |
| **ONAY 2/2** — "İKA'ya aktarıldı" | İKA'dan `ACK(ref=seq, ref_tip="OPEN_ROUTE")` **ekranda görünmeli** | İHA'ya ACK gider, zaman damgası yazılır |

Kanıt gelmezse düğme **pasif** kalır ve gerekçe metni görünür. Bu **bilinçli bir seçimdir**:
kanıtsız onay yerine **görünür ret**.

**§2.2.3 sıra denetimi (D-393 §3):** aktarımın İHA **havadayken** tamamlanması gerektiği için
İKA'nın rota ACK'ine `HAVADA ✓` / sarı uyarı damgası basılır; `IHA_LANDED` geldiğinde ACK
hâlâ yoksa ekranda KIRMIZI **"İHLAL RİSKİ: aktarım İHA havadayken tamamlanmadı"** görünür.

**`IKA_GO` ACK'li tekrar (D-02 kapanışı):** Denetimde ölçüldü ki `IKA_GO` **tek atıştı**,
ACK beklenmiyordu ve gönderim sonrası düğme **kalıcı kilitleniyordu** — tek paket kaybı
görevi **geri dönülmez** biçimde bitiriyordu. Bugün: aynı `seq` ile
`IKA_GO_TEKRAR_ARALIGI_S = 0,25 s` aralıkla en çok `IKA_GO_TEKRAR_UST_SINIRI = 20` kez;
İKA'dan `ACK(ref_tip="CMD")` gelince durur. Üst sınır aşılırsa ekranda KIRMIZI
**"İKA ONAY VERMEDİ"**, düğme yeniden aktif, İKA kronometresi **başlamamış sayılır** —
görev kaybedilmez. İKA tarafı **idempotenttir**: mükerrer `IKA_GO` latch'i yeniden kurmaz
ama **her alım ACK'lanır** (YKS'nin tekrarı ancak böyle durur).
Kilit: `tests/test_ika_go_ackli_tekrar.py` — gerçek UDP loopback'te paket düşürme, ACK yok →
üst sınır, mükerrer `IKA_GO`, kanıtsız düğme pasif; **5 mutasyonun tamamı yakalandı**.

### 3.6.4 İKA hareket kilidi (§2.2.5)

```
sür  ⟺  (geçerli OPEN_ROUTE)  ∧  (İHA inişi tamamlandı)  ∧  (YKS'den IKA_GO geldi)
```

Şartname: *"İHA yere temas etmeden İKA hareket edemez. İHA iniş yapmadan harekete geçen
takımların görevi başarısız sayılacaktır."*

**İniş sinyalini üreten kimdir — denetimde kapanan boşluk.** Kapı kuruluydu ama üretim
zincirinde iniş sinyalini üreten **yoktu**; varsayılan koşumda kilit hiç açılmıyordu.
Bugün üretici `comms/iha_inis_yayinci.py`'dir ve kanıt **Pixhawk telemetrisidir**:
`EXTENDED_SYS_STATE.landed_state == ON_GROUND` **ardından** `GLOBAL_POSITION_INT.relative_alt < 1 m`,
**aynı sysid**, **3 ardışık çift**, mutlak deadline; sonra `send_iha_landed` ACK'li gider.

🔴 **Manuel "İHA İNDİ" düğmesi latch'i AÇMAZ** — kilit
`tests/test_iha_landed_gate.py:313` ile kilitlidir. Operatörün beyanı kanıt değildir.

**Sürücü katmanı da kilidin altındadır** (`CONTRACTS.md` §7.2): izinler gelmeden sürücüye
sıfır-dışı komut düşmez (`tests/test_p3_ika_surucu.py::T6`). `GercekSurucu` arka uçsuz
**kurulamaz** (`DONANIM_YOK` istisnası) — **sessiz iskelet yasaktır.**

**Varış = brandaya TEMAS (§7.3, SS7 P_görev):** görev *"branda üzerine fiziksel temas"* ile
biter; sınıra girmek 0 puandır. İki yarım da kilitlidir:
1. **İHA yarısı:** rotanın son waypoint'i HB pedinin kutusunda biter — ölçüldü **253/256**
   (ped görünmezken `HEDEF_YOK`).
2. **İKA yarısı:** `navigate` son waypoint'te `FINAL_WP_RADIUS = 0,3 m` kullanır ve
   **`FINAL_WP_RADIUS < HB_KENAR_M/2` (1,0 m)** eşitsizliği bağlayıcıdır → araç merkezi ped
   kenarından ≥ **0,7 m** içeride durur, gövde pedin üstündedir.

> ⚠ Gazebo **fiziksel temas** koşusu geliştirme makinesinde **ÖLÇÜLEMEDİ** (gz yok);
> Gazebo'lu makinede koşulacaktır. `ÖLÇÜLEMEDİ ≠ GEÇTİ`.

### 3.6.5 Süre limitleri (§6.2 / §6.4)

| sabit | değer | şartname alıntısı |
|---|---|---|
| `SARTNAME_IHA_GOREV_SURESI_S` | 900 | §6.2 *"Bu işlemler için tanınan maksimum süre 15 dakikadır."* |
| `SARTNAME_IKA_GOREV_SURESI_S` | 600 | §6.2 *"İKA'nın HB'ye ulaşması için verilen maksimum süre 10 dakikadır."* |
| `SARTNAME_FDA_OPERASYON_SURESI_S` | 600 | §5.3.2 tüm operasyon |
| `SARTNAME_HAZIRLIK_SURESI_S` | 900 | hazırlık kronometresi |
| `IHA_INIS_HEARTBEAT_ARALIGI_S` | 0,5 | < `IkaReceiver.hb_timeout` (3 s) |

**Bağlayıcı kural:** İKA'da **iki ayrı son tarih** vardır — bekleme ve sürüş. Sürüş saati
izin geldiği **anda** başlar; beklemede geçen süre sürüşten **düşülmez**. Tek ortak deadline
(eski `--timeout 60`) **yasaktır** — sahada iniş dakikalar sonra gelir. Sürüş süresi dolunca
İKA `send_vel(0,0)` ile durur; **serbest alan/rota kararına dokunulmaz** (madde 15).
Kilit: `tests/test_k5_k6_sure_limitleri.py` (sahte saat + gerçek UDP loopback; **4 mutasyonla
düştüğü gösterildi**).

### 3.6.6 FDA görev kipi (`--fda`) — görev test uçuşunda onayı İMKÂNSIZ kılan kilidin kaldırılması

**Ölçülen tıkanma (D-407/D-408):** `yks_gui` yarışma günü görevine göre yazıldı. Hakem onayı
2/2 adımı `ika_aktarim_kaniti_var()` istiyordu (K8, §2.2.3). FDA'da **İKA olmadığı için** bu
kanıt **hiç gelmez** → onay tamamlanamaz → İHA'ya ACK gitmez. Şartname §5.3.2 *"gerçek zamanlı
tespitin hakem heyetince doğrulanıp onaylanması"*nı zorunlu kıldığından bu, **uçuşu geçersiz
kılacak bir GUI kilidiydi.**

**Sözleşme (`CONTRACTS.md` §6.7) — `--fda` verildiğinde:**

| konu | yarışma kipi (§2.2) | **FDA kipi (§5.3.2)** |
|---|---|---|
| İHA süre bütçesi | 900 s | **600 s** |
| hakem onayı 2/2 | İKA'nın `OPEN_ROUTE` ACK kanıtı **şart** | **İKA kanıtı ARANMAZ**; 2/2 = "YKS'de canlı görüldü + hakem sözlü onayı" → ACK İHA'ya gider (`ref_tip` ile). Ekranda dayanak: *"FDA §5.3.2: İKA yok — onay YKS aktarımına dayanır"* |
| PARAŞÜT düğmesi | manuel yedek (−50 puan) | **KAPALI** — basılırsa komut **gönderilmez**, KIRMIZI: *"FDA kipinde paraşüt yok (çoklu rotor)"*; etiket `PARAŞÜT (FDA dışı)` |
| FIRLATMA düğmesi | mancınıktan ayrılma damgası | etiket **`KALKIŞ`**; damga = kalkış anı, kronometre burada başlar. **ARM kilidi AYNEN** |
| İKA BAŞLAT | §2.2.5 zinciri | **KAPALI**, `IKA_GO` **gönderilmez** |
| iniş kanıtı (`IHA_LANDED`) | zorunlu | **aynen zorunlu** |
| asgari irtifa notu | bilgi | **aynen** (30 m) |

Kip **açılışta** belirlenir, koşarken **değişmez** ve ekranda sürekli görünür. Sınıf
varsayılanı **yarışma kipidir**; `--fda` verilmedikçe davranış **bayt-eş** değişmez.

**Kanıt:** `tests/test_faz_b_yks_fda_kipi.py` **9 test** (gerçek `protocol.encode/ack`
çerçeveleri, link çağrıları çözülerek denetlenir), içinde **iki pozitif kontrol** vardır
(kanıt varken yarışma kipinde de onay tamamlanır; yarışma kipinde iki tıkla `PARACHUTE`
gerçekten gider) — yani "kilit hep kapalı" diye geçen sahte bir test yoktur.
**Mutasyon: 4/4 yakalandı** (M1 onay kilidi geri → test 1 düştü; M2 paraşüt kilidi kalk →
test 3 düştü; M3 İKA kilidi kalk → test 4 düştü; M4 etiketler uygulanmaz → test 5 düştü);
dosya `cmp` ile **bayt-eş** geri yüklendi.

> ⚠ **DENETİM BORCU (kayıtlı):** §6.7 sözleşmesini de uygulamasını da aynı el yazdı.
> Bağımsız denetim, 21 Eylül Adıyaman provasında **hakem rolü oynanarak**
> kapatılacaktır.

### 3.6.7 Tazelik ve körlük — "heartbeat akıyor" ≠ "sistem görüyor"

`HEARTBEAT.karar_yas` alanı, İHA'nın son **ALGI KARARININ** yaşını taşır (saniye, monotonik
saat). Alan **yoksa** yaş BİLİNMİYOR demektir ve alıcı **taze saymaz.**

**Neden:** ölçüldü ki 45–51 saniyelik bir algı körlüğünde heartbeat **akmaya devam ediyordu**
(D-374). Hat canlılığı algı canlılığı değildir.

**Çürütücünün bulduğu üç kaçak da kapatıldı (D-383 §2):**
- **Duvar saati asimetrisi:** İHA tarafı monotonikken YKS alım tarafı `time.time`'daydı;
  saat 30 s geri alınınca **bayat** tespit **TAZE** görünüyordu. Alım damgası ve geçen-süre
  hesabı monotonik yapıldı; repro artık bir testtir.
- **NaN kaçağı:** `nan > eşik` daima `False` olduğu için NaN bir `karar_yas`, BİLİNMİYOR
  korumasını atlatıp tespiti **kalıcı taze** gösteriyordu. İki katmanda süzülüyor; negatif de
  reddediliyor.
- **Ekran kendisiyle çelişiyordu:** bant KIRMIZI *"ALGI ZAMAN AŞIMI"* derken tazelik kutusu
  *"0,5 sn TAZE"* gösteriyordu. Düzeltildi.

---

## 3.7 Görev bilgisayarı yığını — Jetson Nano 4GB

### 3.7.1 Karar: Python 3.8 venv + çevrimdışı tekerlek kurulumu

**Kısıt:** JetPack 4.6.x (Ubuntu 18.04) sistem Python'u **3.6**'dır; repo `ultralytics`
ister (Python ≥ 3.8). NVIDIA'nın JetPack torch wheel'i **Py3.6 içindir** ve 3.8 venv'ine
giremez.

**Karar:** Nano'da `~/venv38` (Python 3.8) + PyPI aarch64 wheel'leri; kurulum **çevrimdışı**
(sahada internet varsayılmaz).

**Gerçek indirme yapıldı** (`scripts/nano_tekerlek_indir.py`, PC'de, 3 Eylül):

```text
OZET: {'WHEEL': 14, 'WHEEL_BAGIMSIZ': 0, 'KAYNAK': 0, 'BASARISIZ': 0} | 51 dosya
```
- **14/14 paket** aarch64/cp38 wheel olarak indi, **kaynak paketi 0** (Nano'da derleme yok)
- torch **2.4.1 (CPU)**, torchvision 0.19.1, ultralytics 8.4.118, onnxruntime 1.19.2,
  MAVProxy 1.8.70
- toplam **51 dosya, 246 MB**; Nano'da tek komut:
  `pip install --no-index --find-links . -r requirements_nano.txt`
- Kilit: `tests/test_faz_b_nano_kurulum.py` (**19 test**)

🔴 **Dürüst risk (belgede yazılı, gizlenmiyor):** üretim modeli v36 **YOLOv8m-seg**'dir
(27,2 M parametre), `n` değil. Nano **CPU**'da 512'de hızı **ölçülmedi** ve FPS kapısının
altında çıkabilir. Çözüm sırası: (1) JetPack 4.6 için Python 3.8 **CUDA torch** topluluk
wheel'i (**insan görevi**), (2) `onnxruntime` ile `.onnx`, (3) CPU torch.
**Eşik gevşetilmez**; ölçüm 5 Eylül'dedir.

**TensorRT `.engine`:** venv38'de `tensorrt` modülü **yoktur** (JetPack 4.6 bağı Py3.6).
`.engine` bu kart için **ÖLÇÜLEMEDİ** sayılır; **PT/ONNX ile uçulur.**

### 3.7.2 Kamera köprüsü — iki Python sürümü arasındaki köprü

**Sorun:** CSI IMX477 yalnız GStreamer `nvarguscamerasrc` ile açılır; sistem OpenCV 4.1
(Py3.6) GStreamer'lıdır, ama pip'ten kurulan `opencv-python` (venv38) **GStreamer'sızdır**
ve kamerayı **açamaz**.

**Çözüm (`scripts/kamera_koprusu.py`, Python 3.6 uyumlu):** sistem python3 + sistem cv2 ile
CSI'yi açar ve HTTP üzerinden sunar:

| uç | içerik |
|---|---|
| `/video` | MJPEG akışı |
| `/kare.jpg` | tek kare |
| `/durum` | JSON durum (kaynak, kare sayacı, hata) |

`rpi_inference --kaynak http://127.0.0.1:8080/video` ile tüketilir. Kaynak düşerse
**fail-visible** davranır (sessizce boş kare üretmez) ve yeniden açmayı dener.
Servis birimi `navitas-kamera-koprusu.service`, `KAMERA_PYTHON=/usr/bin/python3`.
**Yedek:** USB webcam (UVC) `--kaynak 0`.
Testler: köprü **7**, `jetson_baslat` **42**, paket bütünlüğü **18 dosya**.

Ayrıca YKS hakem ekranı için `comms/kamera_istemci.py` bu köprünün `/kare.jpg` + `/durum`
uçlarını **ayrı ağdan** okur — görüntü **SiK hattına yüklenmez** ve bayat kare canlıymış gibi
gösterilmez (`jetson_baslat.sh KAMERA_KOPRU_BIND`; varsayılan loopback, LAN'a açılmak
**açıkça beyan edilir**).

### 3.7.3 systemd birimleri — tek komut, gözcülü açılış

`jetson_baslat.sh` altı birimi kurar; hepsi `Restart=always`, `RestartSec=2`:

| birim | görev | bağımlılık |
|---|---|---|
| `navitas-cogullayici` | MAVLink çoğullayıcı (§3.3.2) | ilk kalkar |
| `navitas-seri-hub` | SiK hub (§3.3.3) — yalnız `KIP=sik` | — |
| `navitas-kamera-koprusu` | CSI → MJPEG (§3.7.2) | `rpi_inference`'tan **önce** |
| `navitas-rpi-inference` | üretim algı yolu (`--camera --ekransiz --mavlink udp:127.0.0.1:14550 --mav-sysid`) | çoğullayıcı |
| `navitas-iha-inis-yayinci` | iniş kanıtı + akış isteği (`udp:…:14551`) | çoğullayıcı |
| `navitas-iha-komut-alici` | YKS komutları → Pixhawk (`udp:…:14552`) | çoğullayıcı |

Kullanım kipleri: `--kuru` (hiçbir şey başlatmaz, koşacağı komutları basar ve eksik beyanı
`[YOK]` ile **3 çıkış koduyla** durdurur) · `--kapi` (yalnız çoğullayıcıyı kaldırır ve üç
uçta **aynı anda** `mavlink_dogrula` koşar) · `--durum` (yeniden başlatma sayısı; artıyorsa
**çökme döngüsüdür**) · `--dogrudan` (systemd'siz, gözcüsüz — yalnız ayıklama).

**`--ekransiz` bayrağı ölçülmüş bir çökmeyi kapatır (D-404):** `rpi_inference` koşulsuz
`cv2.imshow` çağırıyordu; DISPLAY'siz Jetson'da ilk karede çöküp `Restart` döngüsüne
giriyordu. Karar yolu **bayt-eş aynıdır** (`tests/test_faz_b_rpi_ekransiz.py`).

### 3.7.4 FPS kapısı — **0,61 FPS**, türetilmiş (tahmin değil)

Şartname §6.4: hakem onayı alınmayan tespit **geçersizdir**. Sözleşme
`YKS_TESPIT_TAZELIK_S = 5,0 s` ve karar **kare başınadır** (kareler arası uzlaşma yoktur).
Buradan:

```
GEREKLI_FPS  ≥  1 / (5 · p)          p = bir karenin geçerli rota yayınlama olasılığı
```

| küme | p | gereken FPS | kapsam |
|---|---|---|---|
| sentetik arena (260) | 0,9846 | **0,203** | göreve benzer, **sentetik** |
| gerçek DJİ, **sızıntısız** (243) | 0,3457 | **0,579** | gerçek, arenaya **OOD** |
| gerçek DJİ, yalnız 0038 (230) | 0,3261 | **0,613** | en kötü okuma |

**Kapı en kötüsünden alındı: 0,61 FPS**, p50 **ve** p95 ayrı ayrı.

⚠ **D-376 düzeltmesi kayıtta durur:** ilk ölçümde kullanılan gerçek-kare havuzunun **%62'si
modelin eğitim kümesindeydi**; yukarıdaki satırlar **sızıntı ayıklandıktan sonrasıdır**.
Kirli okuma daha iyimserdi (p = 0,4866). Yanlış sayı silinmedi, **üstü çizilip düzeltmesine
işaret verildi**.

**Saha `p`'si ÖLÇÜLEMEDİ** — gerçek arena görüntüsü yoktur. İki sayı alt/üst çerçevedir;
**arası tahmin edilmemiştir.**

**Çözünürlük artırımı denendi ve REDDEDİLDİ (D-377):** sentetik arenada `p` 0,9846 → 0,7808
gerileme; FPS maliyeti oranı 1,302 (bütçe kısıt değildi). Ön kayıt *"I2 düşerse RED, I1 ne
olursa olsun"* diye **sonuç görülmeden** yazılmıştı ve umut verici bir ara sayı (%21,6) bu
kurala çarptı. Bu, ön kayıt disiplininin somut iş gördüğü bir vakadır.

### 3.7.5 Sürüm mührü ve paket bütünlüğü

`surum_dondur --dogrula` üç istasyonun (İHA/YKS/İKA) çalıştırdığı dosyaların kanonik
özetlerini mühürler ve doğrular; mühür **git bağına** ve kanonik özete dayanır (v2, **49
test**). ⚠ Mühürün ilk sürümünde **KRİTİK** bir kusur ölçülmüştü: özet **CRLF'ye bağlıydı**
ve Jetson'da (LF) doğrulanamıyordu (D-405). Düzeltildi ve testle kilitlendi.

**Kural:** 5 Eylül montajından itibaren üretim kodu **değişmez**; zorunlu değişiklik =
D-kaydı + kapı + **ayrı denetim**.

---

## 3.8 Haberleşme

### 3.8.1 Çerçeve protokolü (SiK 433 MHz / UDP)

- **Çerçeveleme:** satır sonu (`\n`) ile ayrılmış **tek satır JSON**, UTF-8
  (`comms/protocol.py:193 encode` / `:199 decode`). Taşıyıcıdan bağımsızdır.
- **Parçalı veri güvenli okuyucu:** `FrameReader` bayt akışından tam çerçeveleri ayıklar.
- **Tampon tavanı:** `CERCEVE_TAMPON_TAVANI = 64 KiB`. SiK hattında gürültü newline
  üretmeden uzun süre akabilir; tavansız tampon belleği tüketirdi. Tavan aşılınca tampon
  atılır ve hat **bir sonraki newline'da** senkronize olur.
- **Bozuk JSON satırı atılır**, süreç yaşar.
- ⚠ **Protokolde CRC/checksum YOKTUR.** SiK radyosunun kendi hata düzeltmesine güvenilir.
  Bu bilinçli bir sadeleştirmedir ve **ölçülmemiş bir risktir** (§3.10).

### 3.8.2 ACK'li tekrar parametreleri

| komut | aralık | üst sınır | pencere | sabit |
|---|---|---|---|---|
| `OPEN_ROUTE` / `NO_ROUTE` / `IHA_LANDED` | 0,25 s | 8 | 2,0 s | `iha_sender.py:97,145,166,190` |
| `IKA_GO` | 0,25 s | 20 | 5,0 s | `IKA_GO_TEKRAR_*` |
| `PARACHUTE` | 0,20 s | 40 | 8,0 s | `PARASUT_TEKRAR_*` |
| `ARM` / `DISARM` | 0,25 s | 20 | 5,0 s | `ARM_TEKRAR_*` (DISARM teyidi 4,0 s) |
| Pixhawk `COMMAND_ACK` tavanı | — | — | **0,5 s** | `MAVLINK_KOMUT_ACK_TAVANI_S` |

**`COMMAND_ACK` neden zorunlu:** `command_long_send` istisnasız dönmesi **kanıt değildir** —
pymavlink `udp:` sunucusu ölü akrana yazıp hatayı **yutar**; router/Pixhawk ölmüşken de
"aktarıldı" görünürdü (D-403). Bugün İHA komut alıcısı YKS'ye ACK'i **yalnız Pixhawk'ın
`COMMAND_ACK(MAV_RESULT_ACCEPTED)` cevabından sonra** döndürür.

### 3.8.3 Ölçülen gecikmeler

**Uçtan uca kare gecikmesi** — **33 ölçülen** gerçek 1280'lik kare (+3 ısınma karesi
ölçüm dışı), üretim zinciri birebir, gerçek `KararYayinci` + **UDP loopback** ACK.
Tablonun tamamı **tek koşumdan** gelir: `results/fda_butce/olcum_20260901.json`
(üreteç `scripts/olcum/169_fda_butce_olcumu.py`).

| adım | p50 (ms) | p95 (ms) |
|---|---:|---:|
| önişleme | 5,0 | 7,1 |
| çıkarım | 12,3 | 14,9 |
| maske | 17,5 | 24,1 |
| karar | 49,7 | 68,6 |
| telsiz + ACK | 2,3 | 2,6 |
| **TOPLAM** | **84,8** | **113,2** |

> ⚠ **Bu tablo bir düzeltmenin ürünüdür.** İlk koşumda (D-382) `telsiz+ACK`
> p50 **307,6 ms** ölçülmüştü ve toplam 395,7/457,8 ms görünüyordu. Bağımsız
> çürütücü bunun bir ölçüm değil, `link.recv`'in **soket zaman aşımı sabiti**
> olduğunu gösterdi (D-383); sabit düzeltilince kalem 2,3 ms'ye indi. Yukarıdaki
> tablo düzeltme **sonrası** koşumdur; çürütülen tablo `REVIEW_LOG.md` D-382'de
> üstü çizili olarak durur ve bu iki koşum **birbirine karıştırılmaz**.

Model yükleme + soğuk başlangıç **2,64 s** — uçuş öncesidir, **bütçe dışı**.

🔴 **Bu tablo bir çürütmenin ürünüdür (D-383 §1).** İlk ölçüm toplam p95 **457,8 ms**
veriyordu ve baskın kalem *"telsiz+ACK 307,6 ms"* idi. Bağımsız çürütücü ölçtü, mimar kodu
okuyarak doğruladı: **bu bir ölçüm değil, `link.recv`'in 0,3 s'lik soket zaman aşımı
sabitinin yansımasıydı** (gerçek loopback RTT **0,06 ms**). Erken çıkış eklendi; sayı
307,6 → **2,3 ms**, toplam p95 457,8 → **113,2 ms**.
**Üretim etkisi de vardı:** karar ipliğinin çevrimi ≥ 0,3 s → yayın hızı ~3,3/s; kamera daha
hızlı üretince latest-wins yuvası kararların bir kısmını **hiç yayınlatmıyordu.**

**Seri (SiK) hattın ikizi de ölçüldü ve düzeltildi (D-403 §3).** `SerialLink.recv` =
`ser.read(256)`: 256 bayt **ya da** 0,3 s zaman aşımı. ~70 baytlık bir ACK için her bekleme
zaman aşımına yuvarlanıyordu. **Gerçek iki uçlu seri köprüde, üretim `IhaSender` ile ölçüm:**
ACK turu **p50 622,6 ms** — paraşüt tekrar aralığının (0,20 s) **üç katı**. Hızlı okumayla
(ilk bayta kadar bekle + `in_waiting` boşalt) **0,8 ms**. Ön kayıtlı eşik p50 < 50 ms,
**sonuç görülmeden** yazılmıştı.

**SiK hub UDP→seri gecikmesi:** boşta p50 **10,6 ms** / p95 **31 ms**; 20 Hz seri girişiyle
p50 **45 ms** (Windows geliştirme makinesi).

### 3.8.4 🔴 ÖLÇÜLEMEDİ — haberleşmede kapatılmamış sayılar

| büyüklük | durum |
|---|---|
| **Gerçek SiK 433 MHz RF üzerinde RTT / paket kaybı** | **ÖLÇÜLEMEDİ.** Araç `scripts/sik_rf_olc.py` **yazıldı** (`--rol yanki` / `--rol olc --n 50`), hedef **RTT p95 < 0,20 s**; radyolar kutudadır, koşum 5 Eylül'dedir. `results/` altında ölçüm dosyası **yoktur.** |
| **Menzil** | **ÖLÇÜLEMEDİ.** DDR'deki *">%98, 300 m"* iddiasının repoda kanıtı **yoktur** |
| **B2-G2 hükmü** (p95 ≤ 1 s heartbeat dönemi) | yalnız **UDP loopback** yapılandırmasının hükmüdür. Üretim seri varsayılanlarıyla (`wait_ack=False`, 4×0,25 s) çevrim 1,0 s ve G2 **geçmezdi**. Bu satır kayıtta böyle durur |
| **Gerçek kamera yakalama gecikmesi** | **ÖLÇÜLEMEDİ** (CSI köprüsü Nano'da koşulmadı) |

---

## 3.9 Alt sistem etkileşimi — kuru koşu ile ölçülmüş zincir

`scripts/saha_kuru_kosu.py` on halkayı **gerçek kodu çağırarak** sınar ve her halka için
sahibini (dosya:fonksiyon) yazar. **Son koşum: 2026-09-02 23:59:54 — 9 GEÇTİ · 1 SAHİPSİZ ·
0 DÜŞTÜ.**

| # | halka | durum | kanıt / sahip |
|---|---|---|---|
| 1 | kamera | **GEÇTİ** | kaynak parametrik ve `VideoCapture`'a besleniyor (cihaz yolu `str`, indeks `int`) — `rpi_inference.run_camera` |
| 2 | model yükleme | **GEÇTİ** | ağırlık manifestten türetiliyor, uyuşmazlıkta fail-closed, kayıt defteriyle eşleşiyor — `rpi_inference.load_model` |
| 3 | çıkarım | **GEÇTİ** | tek kare çıkarımı tamamlandı |
| 4 | maske | **GEÇTİ** | `{0,1}` anahtarlı maskeler üretildi |
| 5 | ölçek | **GEÇTİ** | canlı telemetri bu kare için geçerli `mpp` üretti |
| 6 | hedef konumu | **GEÇTİ** | HB saha kaynağından alınabiliyor (T150/D-386: `goruntu=` + şekil kapısı) |
| 7 | rota | **GEÇTİ** | rota üretildi: `yol_no = 2` — `analyze_path` (`run_camera` yolu) |
| 8 | aktarım | **GEÇTİ** | **üretim yolu** `run_camera` kararı loopback İKA'ya `OPEN_ROUTE` olarak yazdı |
| 9 | sürüş izni | **GEÇTİ** | `IHA_LANDED` saha kod yolunda üretiliyor — `comms/iha_inis_yayinci.py:375` |
| 10 | **motor** | 🔴 **SAHİPSİZ** | gerçek motor sürücüsü **yok**; `send_vel` yalnız `gz` subprocess'i ve `ika_nav` `simulation/` altında |

Halka 10 bilerek açıktır: İKA donanımı tedarik edilmemiştir ve İKA hattı finale
bırakılmıştır (§3.0.1). Sürücü **arayüzü** hazırdır (`CONTRACTS.md` §7.2) ve `GercekSurucu`
arka uçsuz **kurulamaz** — boş bir iskeletin "çalışıyor" görünmesi engellenmiştir.

### 3.9.1 Kapı özeti (3 Eylül 2026 itibarıyla)

| kapı | sonuç |
|---|---|
| Genel kapı `codes/test_rota_sentetik.py` | **15/15** |
| Tam birim test suiti | **1882 OK** (skipped = 3) |
| Kabul zinciri K0–K8 + K5A (v36) | **10/10 GEÇTİ** |
| Saha kuru koşusu | 9 GEÇTİ · 1 SAHİPSİZ |
| Kanıt defteri kayıt sayısı | **414** (`grep -c "^### D-" REVIEW_LOG.md`) |

---

## 3.10 Bilinen açıklar, denetim borçları ve BEYAN GEREKLİ satırları

### 3.10.1 Yazılım tarafında kapatılmamış olanlar

| # | açık | neden kapanmadı |
|---|---|---|
| A1 | **Gerçek İKA motor sürücüsü** | Donanım tedarik edilmedi; İKA hattı finale bırakıldı. Arayüz ve sahte sürücü hazır, gerçek arka uç yok |
| A2 | **Gazebo fiziksel temas koşusu** (§7.3 İKA yarısı) | Geliştirme makinesinde `gz` yok — **ÖLÇÜLEMEDİ** |
| A3 | **TensorRT `.engine` denkliği** | Nano venv38'de `tensorrt` modülü yok; `.engine` bu kart için **ÖLÇÜLEMEDİ** |
| A4 | **Karar kararsızlığı** (v36 14/260, v35'ten kötü) | Histerezis (K=3) yayın katmanında bastırıyor ama **kök neden modeldedir**; ölçüm kayıtlı, kapı yok |
| A5 | **`min()` yolundaki duvar saati zayıflığı** (`rota_zaman` / `son_hb`) | Çürütücü işaret etti, `karar_yas` yolu düzeltildi; bu kol **A2'den eskidir** ve ayrı iş ister |
| A6 | **FDA kipi denetim borcu** | Sözleşmeyi ve uygulamayı aynı el yazdı; bağımsız denetim ilk gerçek provada |

### 3.10.2 BEYAN GEREKLİ (insan) — bu bölüme eklenecek ölçümler

```
BEYAN GEREKLI (insan): Kalkis kutlesi, agirlik merkezi ve her parcanin gercek
  tarti degerleri (5 Eylul montaj, SAHA_HAZIRLIK_PLANI §2.1).

BEYAN GEREKLI (insan): PM02 telemetrisinden okunan asili kalma akimi, tepe akim
  ve olculen ucus suresi (4S 10 Ah pil ile).

BEYAN GEREKLI (insan): Kamera yatay FOV'unun `kamera_dogrula` ile OLCULEN degeri
  (bugun 55-63 derece bir LENS HESABIDIR, olcum degildir) ve 30 m irtifada
  kare genisliginin dogrulanmasi.

BEYAN GEREKLI (insan): Gercek Pixhawk 6C uzerinde `scripts/mavlink_dogrula.py`
  cikitisi -- uc UDP ucunda ayni anda HEARTBEAT sysid, GLOBAL_POSITION_INT >= 4 Hz,
  EXTENDED_SYS_STATE >= 1 Hz.

BEYAN GEREKLI (insan): Gercek SiK 433 MHz cifti uzerinde `scripts/sik_rf_olc.py`
  RTT p95 ve paket kaybi olcumu; ayrica menzil beyaninin kaniti.

BEYAN GEREKLI (insan): Jetson Nano 4GB uzerinde `scripts/jetson_fps.py` p50/p95
  FPS olcumu (PT ve ONNX, cihaz bilgisi ile) -- kapi 0,61 FPS, esik gevsetilmez.

BEYAN GEREKLI (insan): `torch.cuda.is_available()` sonucu ve secilen cikarim
  arka ucu (CUDA torch topluluk wheel'i / onnxruntime / CPU torch).

BEYAN GEREKLI (insan): ArduCopter surum numarasi, kalibrasyon ciktilari (accel,
  pusula ofseti < 300), ESC kalibrasyonu ve pervanesiz motor testi videosu;
  sahada okunan `arducopter_fda_20260905.param` dokumunun repoya islenmesi.

BEYAN GEREKLI (insan): Adiyaman test alaninin gercek kose koordinatlari
  (`config/pixhawk/fda_gorev.waypoints` bugun Null Island yer tutucusudur).

BEYAN GEREKLI (insan): Arena benzeri gercek saha goruntusu (kirmizi H brandasi +
  moloz + fiziki bariyer, >= 30 m). Bugun YOKTUR; K0-K8 zinciri bu kume uzerinde
  yeniden kosulamadi. Maket cekimi yapilmayacaktir.

BEYAN GEREKLI (insan): Yarisma gunu araci (sabit kanat + mancinik + parasut) ve
  IKA sasisinin nihai mekanik kunyesi, montaj fotograflari, kutle dagilimi.
```

### 3.10.3 Bu bölümün asıl iddiası

Sayılardan çok, sayıların **nasıl** üretildiği:

1. **Ön kayıt.** Eşik, sonuç görülmeden yazılır ve sonradan gevşetilmez. Bu kural en az iki
   kez somut iş gördü: D-377'de umut verici bir ara sayı önceden yazılmış bir RED kuralına
   çarptı; D-107 eşikleri §3.5.3'te bir terfiyi *"geçemedi"* diye kayda geçirmeye zorladı.
2. **`ÖLÇÜLEMEDİ ≠ GEÇTİ`.** Ölçülemeyen şey geçmiş sayılmaz; paydası olmayan oran rapora
   girmez. Bu, kabul denetçisinde **kod satırıdır**, temenni değil.
3. **Mutasyon kontrolü.** Her kapı, kaldırıldığında **düşerek** ayırt ediciliğini kanıtlar.
   Mutasyon **koda** uygulanır, yoruma değil; uygulanmayan mutasyon başarı sayılmaz.
4. **Çürütme kaydı.** Yanlış çıkan iddialar **silinmez**, üstü çizilip düzeltmesine işaret
   verilir. §3.7.4'teki FPS sayısı, §3.8.3'teki gecikme tablosu ve §3.5.2'deki iki ölçüm
   hattı bu kuralın doğrudan ürünüdür — **bu bölüm kendi hatalarını da gösterir.**

---

## Kanıt dizini

Bölümde geçen her sayının kaynağı. Biçim: **değer** · *dosya yolu* · üreten betik/komut ·
ölçüm tarihi.

### K0–K8 kabul kapıları

| değer | dosya | üreten | tarih |
|---|---|---|---|
| K1 256/260 · K2 6/256 · K3 0/256 · K4 3/256 · K6 3/256 · K5 0/178 · K5A 0/176 · K7 84/85 (%98,82) · K8 GEÇTİ (0,0444) | `scripts/olcum/results/t63/t199_ozdenetim_kabul_verdikt.json` | `scripts/olcum/65_kabul_denetcisi.py` | 2026-08-28 21:25 |
| K0 figür zemin %2,66 · ham boş 0/67 · cp boş 0/393 | aynı dosya (`olcum.K0`) | `65_kabul_denetcisi.py` | 2026-08-28 |
| Terfi anı: K1 255/260 · K2 %5,88 · K3 %0,39 · K4 %1,57 · K5 0/172 · K6 %2,75 | `scripts/olcum/results/t63/gece_v7a_kabul_verdikt.json` · `config/model_registry.json → metrics` | `65_kabul_denetcisi.py` | 2026-08-26 |
| K7 ham ölçüm (88 kare alt küme, 85 rota, 84 doğru, yanlış: `sa_000090.jpg` 2→3) | `scripts/olcum/results/t63/v36_k7_baglama_k7.json` | K7 alt betiği (65 üzerinden) | 2026-08 |
| K5 popülasyon: taranan 260 · bariyerli 173 · ölçekli 173 · rota 172 · kesen 0 · 0 px | `scripts/olcum/results/t63/v36_k7_baglama_k5_populasyon.json` | `scripts/olcum/66_k5_bariyer_populasyon.py` | 2026-08 |
| K5A ayırt edicilik: 185/260 → 48/260 (52,7 puan) vs yatay 181/260 → 181/260 | `scripts/olcum/results/t63/t189_ayirt_edicilik.json` | mutasyon koşumu (T189) | 2026-08 |
| Eşikler (K1≥230 · K2≤%15 · K3≤%3 · K4≤%5 · K6≤%5 · K7≥%95 ve payda≥80) | `scripts/olcum/65_kabul_denetcisi.py:116-140` (`ESIK`) | ön kayıt `REVIEW_LOG.md` D-107 | sonuç görülmeden yazıldı |
| Kabul kümesi parmak izi: n=547 · `sha256:604c037f…` | `t199_ozdenetim_kabul_verdikt.json → kabul_kumesi_parmak_izi` | `65_kabul_denetcisi.py` | 2026-08-28 |

### Gerçek kare (DOĞRULAMA kümesi)

| değer | dosya | üreten | tarih |
|---|---|---|---|
| test29: n=29 · rota **8** (eşik ≥10) · maske_yok **16** (eşik ≤10) · TP 7 · FP 1 · FN 5 · yanlış güzergâh 0 · tavan 12 | `results/gece_20260826/gece_v7a_olcum.json` · `config/model_registry.json → metrics.gercek_kare_kapisi` | `scripts/olcum/142_gece_olcum.py` | 2026-08-26 |
| val82: n=82 · rota 30 · maske_yok 35 · TP 28 · FP 2 · FN 15 · yanlış güzergâh 7 · tavan 43 | `results/gece_20260826/gece_v7a_val82_olcum.json` | `142_gece_olcum.py` | 2026-08-26 |
| Terfi kararı metni (eşikler GEÇİLMEDİ) | `config/model_registry.json → metrics.gercek_kare_kapisi.sonuc` · `_surum_karari` | — | 2026-08-26 |
| Ön kayıt | `results/gece_20260826/ON_KAYIT.md` §12/§14/§15 · `REVIEW_LOG.md` D-107, D-293 | — | sonuç görülmeden |
| Çürütücü çıktıları | `results/gece_20260826/v7a_curut/` | — | 2026-08-26 |

### Model künyesi ve denklik

| değer | dosya | üreten | tarih |
|---|---|---|---|
| `navitas-seg-v36-512` · imgsz 512 · pytorch · sha256 `1d1caca6…` | `config/model_registry.json → profiles.competition` | `codes/model_registry.py` | 2026-08-26 |
| ONNX sha `f4c9f5fe…` · `.engine` = `DERLENINCE_YAZILIR` (RED) | aynı dosya → `turevler` | `model_registry.py --turev-kaydet` | — |
| ONNX↔PT karar denkliği 259/260 · IoU 0,9975 · sapma 172,1 px / 13,443 m | `results/t79/onnx_denklik_v36.json` | `scripts/olcum/67_onnx_karar_denkligi.py` | 2026-08 |
| FP16 zarar yönü 0 · karar uyuşması 0,9968 (eşik 0,98) | `results/fdr/GORUNTU_ISLEME_KANIT.md` §4.2 · `REVIEW_LOG.md` D-375 | `scripts/olcum/167_fdr_kanit_paketi.py` | 2026-09 |
| Karar çevrilmesi v36 14/260 (tohum 7) · 15/260 (tohum 11) · v35 9 / 11 | `results/karar_cevrilmesi_v36/` · `config/model_registry.json → metrics.karar_cevrilmesi` | `scripts/olcum/68_karar_kararliligi.py` | 2026-08-26 |
| Çatı kaçağı 0,0230 (medyan 0,0119, n=55) · çatı→engel 0,9908 · çatı→zemin 0,0000 | `config/model_registry.json → metrics.cati_kacagi` | T121 zinciri | 2026-08 |
| Gerçek kare zemin kaplaması: tuval 0,2346 · içerik 0,4171 | `results/gece_20260826/gece_v7a_olcum.json` (k109) | `142_gece_olcum.py` | 2026-08-26 |

### Zamanlama ve gecikme

| değer | dosya | üreten | tarih |
|---|---|---|---|
| Uçtan uca p50 **84,8** / p95 **113,2 ms** (33 ölçülen kare + 3 ısınma, UDP loopback ACK) | `results/fda_butce/olcum_20260901.json` · `REVIEW_LOG.md` D-383 §1 | `scripts/olcum/169_fda_butce_olcumu.py` | 2026-09-01 |
| Adım kırılımı: önişleme 4,9/6,2 · çıkarım 14,8/45,4 · maske 18,4/25,6 · karar 51,2/80,1 (p50/p95 ms) | aynı dosya · `REVIEW_LOG.md` D-382 §2 | `169_fda_butce_olcumu.py` | 2026-09-01 |
| Düzeltilen artefakt: telsiz+ACK 307,6 → **2,3 ms**; toplam 457,8 → 113,2 ms; gerçek loopback RTT 0,06 ms | `REVIEW_LOG.md` D-383 §1 | çürütücü reprosu + mimar doğrulaması | 2026-09-01 |
| Model yükleme 2,64 s (bütçe dışı) | `results/fdr/GORUNTU_ISLEME_KANIT.md` §4.1b | `167_fdr_kanit_paketi.py` | 2026-09 |
| Seri ACK turu p50 **622,6 ms → 0,8 ms** (gerçek iki uçlu seri köprü, üretim `IhaSender`) | `REVIEW_LOG.md` D-403 §3 · ön kayıt `results/p2_seri/ON_KAYIT.md` (eşik p50 < 50 ms) | `tests/test_p2_*` S8 | 2026-09-02 |
| SiK hub UDP→seri: boşta p50 10,6 / p95 31 ms · 20 Hz girişte p50 45 ms (Windows) | `CONTRACTS.md` §7.5 · `REVIEW_LOG.md` D-404/D-405 | `tests/test_faz_b_seri_hub.py` | 2026-09-03 |
| FPS kapısı **0,61** = 1/(5 × 0,3261) | `REVIEW_LOG.md` D-374 / **D-376** (sızıntı düzeltmesi) · `results/fdr/GORUNTU_ISLEME_KANIT.md` §4 | `167_fdr_kanit_paketi.py` | 2026-09 |
| p değerleri: sentetik 0,9846 (→0,203) · sızıntısız gerçek 0,3457 (→0,579) · 0038 tek 0,3261 (→0,613) | aynı | aynı | 2026-09 |
| Çözünürlük RED: 0,9846 → 0,7808 · FPS maliyet oranı 1,302 | `REVIEW_LOG.md` D-377 | ön kayıtlı karar | 2026-09 |

### Karar katmanı sözleşmeleri

| değer | dosya | üreten | tarih |
|---|---|---|---|
| Histerezis K=3; tohum 7: 13→7 (bastırılan 6, NO_ROUTE 0) · tohum 42: 24→11 (bastırılan 14, NO_ROUTE 0) | `results/p5_histerezis/olcum_20260903.json` · ön kayıt `results/p5_histerezis/ON_KAYIT.md` | P5 ölçüm betiği | 2026-09-03 |
| `KARAR_HISTEREZIS_KARE = 3` ve gerekçesi | `codes/karar_sozlesmesi.py:2109-2117` | — | — |
| Geometri sabitleri (`R_GEREKLI_M = 1,10` vb.) | `codes/costmap_path_finder.py` · `CONTRACTS.md` §4 | — | — |
| C-uzayı etkisi: doğru şerit 1/7 → 6/7 · darboğaz 1,0 px → 13,0–15,0 px · güven 0,028–0,117 → 0,644–0,744 | `CONTRACTS.md` §5.3 | arena kompoziti ölçümü | — |
| Madde 15 uyumu: 7 kompozit karede fazla piksel 0 | `CONTRACTS.md` §5.3 | — | — |
| HB'den `mpp`: tespit 260/260 · merkez hatası medyan 0,71 px · sapma medyan %5,2 (p90 %8,6) · 260 doğrulandı / 0 çelişkili | `CONTRACTS.md` §5.1/§5.4 · `REVIEW_LOG.md` D-105 | T72 ölçümü | 2026-08 |
| Ölçek çapraz bandı 0,25 (= sapmanın ~4,8 katı) | `codes/karar_sozlesmesi.py:1485` `OLCEK_CAPRAZ_BANDI` | — | — |
| Ölçeksiz tuzak: `1,10 / 0,0868 = 12,7 px` (~11 kat) | `CONTRACTS.md` §5.2 · `tests/test_olcek_ve_c_uzayi.py` | — | — |
| İnce bariyer: 3644 px · model %0,0 engel · %30,9 zemin · rota 59 px kesiyordu · güven 0,75 | `CONTRACTS.md` §2.1 · `REVIEW_LOG.md` D-92/D-93/D-99 | T67 ölçümü | 2026-08 |
| Çerçeve ihlalleri: 576×1024'te ORTA yerine SAĞ · %1 → %1,78 · 18/18 karede rota yok | `CONTRACTS.md` §3.1 | — | — |
| HB varış: son waypoint ped kutusunda 253/256 · `FINAL_WP_RADIUS = 0,3 m` < `HB_KENAR_M/2 = 1,0 m` → pay ≥ 0,7 m | `CONTRACTS.md` §7.3 · `tests/test_p9e_branda_temas.py` | T150/D-386, P9e/D-391 | 2026-09-02 |
| Sınıf şeması doğrulaması 8 GEÇTİ / 0 DÜŞTÜ (pozitif kontrol dâhil) | `codes/test_sinif_semasi.py` · `CONTRACTS.md` §1.2 | — | — |

### Aviyonik ve saha yığını

| değer | dosya | üreten | tarih |
|---|---|---|---|
| MAVLink çoğullayıcı zorunluluğu; üç uç 14550/14551/14552 | `CONTRACTS.md` §7.4 · `REVIEW_LOG.md` D-403 | grep + kod denetimi (çoğullayıcı geçişi: 0) | 2026-09-03 |
| `MAVLINK_KONUM_ASGARI_HZ = 4,0` · `MAVLINK_DURUM_ASGARI_HZ = 1,0` ve türetimleri | `codes/karar_sozlesmesi.py` (dosya sonu) | — | — |
| T207 akış isteği: `MAVLINK_AKIS_ISTEK_ARALIGI_S = 10` · `SESSIZLIK_TAVANI_S = 5` · `HIZ_CARPANI = 2`; 17 test, MUT-1/MUT-2 her biri 3 test düşürdü | `REVIEW_LOG.md` D-406 §3 · `tests/test_faz_b_akis_istegi.py` | ajan + mimar doğrulaması | 2026-09-03 |
| SiK hub topolojisi ve `--ika-hedef` verilmeme gerekçesi (8 tekrar / 2,11 s boşa) | `CONTRACTS.md` §7.5 · `REVIEW_LOG.md` D-405 | çürütücü ölçümü | 2026-09-03 |
| ArduCopter şablonu: 31 parametre, 12 test; kötü-durum süre **221,5 s** ≤ 600 s (`WPNAV_SPEED` 300 cm/s, `LAND_SPEED` 50 cm/s) | `config/pixhawk/arducopter_fda.param` · `config/pixhawk/fda_gorev.waypoints` · `config/pixhawk/README.md` | `tests/test_faz_b_pixhawk_sablon.py::sure_butcesi_s` (bu rapor için koşuldu) | 2026-09-03 |
| Jetson Nano wheel indirmesi: 14/14 WHEEL · 0 KAYNAK · 51 dosya · 246 MB | `wheels/INDIRME_RAPORU.txt` · `jetson_paket/JETSON_NANO_KURULUM.md` §3 | `scripts/nano_tekerlek_indir.py` | 2026-09-03 |
| Nano kurulum kilidi 19 test · kamera köprüsü 7 · `jetson_baslat` 42 · paket 18 dosya | `tests/test_faz_b_nano_kurulum.py`, `test_faz_b_kamera_koprusu.py`, `test_faz_b_jetson_baslat.py` | — | 2026-09-03 |
| systemd birimleri (`Restart=always`, `RestartSec=2`) | `jetson_paket/systemd/*.service` (6 birim) · `jetson_paket/jetson_baslat.sh` | — | 2026-09-03 |
| Donanım künyesi (§3.2.1 tablosunun tamamı) | `SAHA_HAZIRLIK_PLANI_20260903.md` §0.2 | **kullanıcı beyanı** (ölçüm değil) | 2026-09-03 |
| Mühür v2: 49 test; CRLF kusuru (KRİTİK) | `REVIEW_LOG.md` D-405 · `scripts/surum_dondur.py` | çürütücü + kapanış | 2026-09-03 |

### Emniyet ve YKS

| değer | dosya | üreten | tarih |
|---|---|---|---|
| FDA kipi sözleşmesi ve tablosu | `CONTRACTS.md` §6.7 | — | 2026-09-03 |
| FDA kipi: 9 test · **4/4 mutant yakalandı** · dosya `cmp` ile bayt-eş geri yüklendi | `tests/test_faz_b_yks_fda_kipi.py` · `REVIEW_LOG.md` D-408 §3 | — | 2026-09-03 |
| `IKA_GO` ACK'li tekrar: 0,25 s × 20 · 5 mutasyonun tamamı yakalandı | `CONTRACTS.md` §6.6 · `tests/test_ika_go_ackli_tekrar.py` | — | — |
| Paraşüt: 0,20 s × 40 · ceza sabiti `PARASUT_MANUEL_CEZA_PUANI = 50` | `codes/karar_sozlesmesi.py:2097-2099` · `REVIEW_LOG.md` D-393 §1 | — | 2026-09-02 |
| ARM kilidi kusuru ve düzeltmesi | `REVIEW_LOG.md` D-393 §2 · `tests/test_p9abc_yks.py` (10 test) | — | 2026-09-02 |
| Süre limitleri: 900 / 600 / 600 / 900 s · 4 mutasyonla düştüğü gösterildi | `codes/karar_sozlesmesi.py:1974-1991` · `tests/test_k5_k6_sure_limitleri.py` | — | — |
| Algı körlüğünde heartbeat akmaya devam ediyordu (45–51 s) | `REVIEW_LOG.md` D-374 | ölçüm | 2026-09 |
| Duvar saati / NaN / ekran çelişkisi kaçakları | `REVIEW_LOG.md` D-383 §2 | 3 bağımsız çürütücü ajan (357k token, 74 araç çağrısı) | 2026-09-01 |
| İniş kanıtı zinciri: `ON_GROUND` + `relative_alt < 1 m`, aynı sysid, 3 ardışık çift; manuel düğme latch'i açmaz | `comms/inis_kaniti.yerde_mi` (`comms/inis_kaniti.py:695-735`) · `tests/test_iha_landed_gate.py:313` | — | — |
| Sürücü arayüzü: `ARDISIK_HATA_TAVANI = 3` (10 Hz'de ~0,3 s), `DONANIM_YOK` | `CONTRACTS.md` §7.2 · `simulation/scripts/ika_surucu.py` · `tests/test_p3_ika_surucu.py` | — | 2026-09-02 |

### Zincir ve kapı özetleri

| değer | dosya | üreten | tarih |
|---|---|---|---|
| Kuru koşu 9 GEÇTİ · 1 SAHİPSİZ (motor) · 0 DÜŞTÜ | `results/faz_b_oncesi/cuma_kontrol/kuru_kosu/ozet.json` | `scripts/saha_kuru_kosu.py` | 2026-09-02 23:59:54 |
| Genel kapı 15/15 · tam suit **1875 OK** (skipped=3) | `REVIEW_LOG.md` D-408 §3 | `codes/test_rota_sentetik.py` · `python -m unittest discover -s tests` | 2026-09-03 |
| Kanıt defteri 414 kayıt | `REVIEW_LOG.md` | `grep -c "^### D-" REVIEW_LOG.md` | 2026-09-03 |
| Şartname yükümlülük haritası R1–R21 ve boşluk hükümleri | `results/sartname_bosluk/rapor.md` | `results/sartname_bosluk/rapor_uret.py` | 2026-08-27 |
| Şartname tam metni (§5.3.1 Tablo 4, §5.3.2) | `results/sartname_bosluk/sartname_metin.txt` satır 683-748 | PDF çıkarımı | 2026-08-26 |
| Görüntü işleme kanıt paketi (K0–K6, FPS, FP16, yöntem) | `results/fdr/GORUNTU_ISLEME_KANIT.md` | `scripts/olcum/167_fdr_kanit_paketi.py` | 2026-09 |
