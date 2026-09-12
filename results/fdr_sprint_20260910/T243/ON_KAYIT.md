# T243 — ÖN KAYIT (ölçümden ÖNCE yazıldı)

**İş:** Mesaj paket boyutu tablosu + gerçek görev veri hızı ölçümü
**Kayıt:** D-462 C · yönerge maddesi Y-3.3.4-M03 ("aktarılan veri paketlerinin nihai
yapısı, veri hızı ve gecikme test sonuçları belirtilmelidir")
**Tarih:** 12 Eylül 2026 · **Yazan:** başamele (worktree `wf_88f63745-bff-1`)
**Durum:** bu dosya ölçüm betiği koşulmadan önce yazıldı ve ayrı commit'lendi.

> ⚠ Bu bir **kapı değildir**. Yönerge maddesinin sayısal karşılığıdır; hükmü
> "ölçüldü / ölçülemedi"dir, "geçti / kaldı" değildir. Ölçülmeyen hiçbir nicelik
> için olumlu hüküm yazılmaz.

---

## 1. Ölçülecek nicelikler

### 1.1 Paket boyutu (`comms/protocol.py` `encode()` gerçek bayt sayımı)

| no | nicelik | birim |
|---|---|---|
| N1 | mesaj tipi başına çerçeve boyutu: `OPEN_ROUTE`, `NO_ROUTE`, `HEARTBEAT`, `ACK`, `CMD`, `IHA_LANDED` | bayt |
| N2 | `OPEN_ROUTE` boyutu — waypoint sayısı **1..20** eğrisi | bayt / waypoint |
| N3 | `HEARTBEAT` iki uçta: **asgari alan** (yalnız `node`) ve **tam telemetri** (üretim yolunun ürettiği 15 alan) | bayt |
| N4 | alan başına marjinal maliyet: `len(encode(tam)) − len(encode(tam − alan))` | bayt |
| N5 | `seq` basamak sayısının maliyeti (`seq` ∈ {1, 10, 100, 1000, 10000}) ve gerçek saat altındaki `t` alanı bayt oynaması (min/maks) | bayt |

`OPEN_ROUTE` değişken alanları: `waypoints` (liste) ve `ref_xy`. Ölçüm iki
koordinat kümesiyle yapılır: (a) **üretim yolu** — `comms/iha_sender.py`
`piksel_rotayi_yerele_cevir` ile sentetik piksel rotadan üretilmiş yerel metre
waypoint'leri (ondalık biçim üretimdekiyle aynı: 2 ondalık); (b) **en geniş** —
sözleşme tavanındaki en uzun ondalık gösterim (`MAX_LOCAL_EXTENT_M = 60.0`,
`comms/iha_sender.py`) → koordinat başına 6 karakter, ör. `-59.99`. (b) bir
**üst sınırdır**, ölçülen tipik değer değildir.

### 1.2 Gerçek görev karışımı (fiilî veri hızı)

| no | nicelik | birim |
|---|---|---|
| N6 | görev karışımında İHA'nın gönderdiği toplam bayt / paket | bayt, çerçeve |
| N7 | ortalama gönderilen bayt/s, bit/s, paket/s (pencere boyunca) | B/s, bit/s, pkt/s |
| N8 | **tepe** bayt/s — 1,0 s'lik kovalarda en büyük değer | B/s |
| N9 | alınan (ACK) bayt/s, paket/s | B/s, pkt/s |
| N10 | görev süresi boyunca toplam bayt — İHA 900 s, İKA 600 s | bayt |

### 1.3 Hat doluluğu (57600 8N1)

| no | nicelik | birim |
|---|---|---|
| N11 | tek yön doluluk oranı = TX B/s ÷ 5760 B/s | % |
| N12 | paylaşımlı doluluk oranı = (TX + RX) B/s ÷ 5760 B/s | % |

---

## 2. Yöntem

### 2.1 Paket boyutu — betik `scripts/paket_boyutu_olc.py`, kip `--kip boyut`

1. Boyutlar **yalnız** `comms/protocol.py` üreticileri (`open_route`, `rota_yok`,
   `heartbeat`, `ack`, `command`, `iha_landed`) çağrılıp `protocol.encode()`
   sonucunun `len()`'i alınarak sayılır. Elle bayt hesabı, biçim tahmini ya da
   `json.dumps` kopyası **kullanılmaz**.
2. Tablonun bayt-eş yeniden üretilebilmesi için ölçüm sırasında iki kaynak
   sabitlenir: (a) `protocol.time.time` geçici olarak sabit `SABIT_ZAMAN =
   1789000000.123` döndürür (ölçüm bitince geri alınır); (b) her üreticiye
   `seq` açıkça verilir (`SABIT_SEQ = 1000`, 4 basamak). Bu iki sabitleme
   `t`/`seq` alanlarının **genişliğini** kilitler, alanların kendisini
   kaldırmaz — çerçeve alan alan üretimdekiyle aynıdır.
3. N5 gerçek saat altında ayrıca ölçülür: `SAAT_ORNEK = 200` örnekte
   `heartbeat("iha")` boyutunun min/maks'ı ve `seq` basamak eğrisi.
4. `HEARTBEAT` tam telemetri alan kümesi üretimden okunur: `codes/rpi_inference.py`
   `_telemetri_saglayici` 12 alan (`lat, lon, alt, hiz, yon, gps_fix, uydu, bat,
   bat_yuzde, armed, mod, pixhawk_canli`) + referans varsa `x, y` + `KararYayinci`
   `karar_yas` = **15 alan** — `protocol.HEARTBEAT_TELEMETRI_ALANLARI` kümesinin
   tamamı. Değerler üretimdeki büyüklük sınıfından (Adıyaman enlem/boylam,
   irtifa yaklaşık 30 m) seçilir ve ON_KAYIT §5'teki tohumla sabittir.

### 2.2 Gerçek görev karışımı — betik `scripts/paket_boyutu_olc.py`, kip `--kip karisim`

1. Taşıyıcı **UDP loopback**, üç uç, hepsi **ephemeral port** (`127.0.0.1:0`).
2. İHA ucu: gerçek `comms/iha_sender.py` `IhaSender` + gerçek `KararYayinci`
   (üretim sınıfı, `repeat`/`interval`/`wait_ack` üretim varsayılanlarıyla:
   `repeat=4`, `interval=0.25`, `wait_ack=True`).
3. İKA ucu: gerçek `comms/ika_receiver.py` `IkaReceiver` (`send_ack=True`) —
   ACK'i üretim yolu üretir.
4. YKS ucu: gerçek `protocol.ack(...)` üreten sayıcı bir UDP soketi (hakem ACK'i).
5. Bayt sayacı: link nesnesi `send`/`recv` çağrılarında `len(veri)` sayan saydam
   bir sarmalayıcıyla kuşatılır; hız sözlüğü `scripts/sik_rf_olc.py`
   `veri_hizi_hesapla` ile üretilir (yeni hesap kopyası yazılmaz).
6. Karar kadansı iki değerde koşulur, ikisi de **ölçülmüş** artefakttan:
   - **1,353 Hz** — Jetson Orin Nano üretim zinciri `pt` p50 739,076 ms
     (`results/jetson_20260906/jetson_fps_20260906_orin_nano/ozet.json`,
     `vakalar[0].metrikler_ms.toplam_ms.p50`) → 1000/739,076 = 1,353 Hz. Uçuş
     donanımının fiilî karar üretme hızıdır.
   - **2,0 Hz** — tavan koşulu. Üretimde karar kadansı algı zincirinin kare
     hızıyla sınırlıdır; PC sınıfı ölçüm medyanı 2,556 / 2,428 FPS (D-460, T227
     satırı) olduğundan 2,0 Hz İHA'nın hiçbir ölçülmüş yapılandırmasında
     aşılmayan bir üst sınırdır. Bu satır "ölçülen kadans" değil **tavan
     senaryosu** diye yazılır.
7. `HEARTBEAT` kadansı `IHA_HEARTBEAT_ARALIK_S = 1.0`
   (`codes/karar_sozlesmesi.py`) — sözleşmeden okunur, betiğe yazılmaz.
8. Pencere: kadans başına `PENCERE_S = 60.0` s gerçek zaman. N8 için 1,0 s'lik
   kovalar bu pencere içinde tutulur.
9. N10 **ekstrapolasyondur**: ölçülen ortalama B/s × görev süresi. Görev süreleri
   sözleşmeden okunur: `SARTNAME_IHA_GOREV_SURESI_S = 900` ve
   `SARTNAME_IKA_GOREV_SURESI_S = 600` (`codes/karar_sozlesmesi.py`).
   900 s'lik bir koşum **yapılmaz**; rapor bunu ekstrapolasyon diye yazar.
10. Mesaj boyutları ölçümün kendisinden (gerçek `encode()` akışı) gelir; sentetik
    olan yalnız **rota geometrisidir** (piksel waypoint'ler), boyut değil.

### 2.2-EK — ÖN KAYIT EKİ (12 Eylül, hâlâ ölçümden ÖNCE)

> Bu ek, ön kaydın ilk commit'inden (`66dd28e2`) sonra, **ölçüm betiği daha
> yazılmadan ve hiçbir sayı üretilmeden** yazıldı. Hiçbir eşiği gevşetmez; §4
> rapor ölçütü ve §1 nicelik listesi aynen durur. Yalnız **ölçülecek yapılandırma
> sayısını artırır** — sebebi, kaynak okunurken bulunan iki üretim olgusudur:
>
> **Olgu-1:** YKS `OPEN_ROUTE`'u kendiliğinden ACK'lemez. `comms/yks_gui.py`
> yalnız `NO_ROUTE` ve `IHA_LANDED` için ACK üretir; `OPEN_ROUTE` ACK'i hakem
> 2/2 onayına bağlıdır (`CONTRACTS.md` §6.6). Dolayısıyla `wait_ack=True` olan
> UDP yolunda `IhaSender._tekrarli_gonder` her karar için `repeat` turunun
> tamamını koşar; bir kararın hat yükü tek çerçeve değildir.
>
> **Olgu-2:** Saha taşıyıcısı (SiK seri) `comms/iha_sender.py` `yayinci_kur`
> içinde `peers={"broadcast": None}` **ve** `wait_ack=False` ile kurulur — yani
> sahadaki yük UDP dev yolundakiyle **aynı değildir**.

Bu yüzden karışım ölçümü **iki yapılandırmada** koşulur, ikisi de kadans başına
ayrı ayrı (toplam 4 koşum):

| yapılandırma | akranlar | `wait_ack` | üretimdeki karşılığı |
|---|---|---|---|
| `saha` | tek yayın hattı | `False` | SiK seri (`--telsiz-seri`) — sahada kullanılan yol |
| `udp` | `ika` + `yks` | `True` | UDP dev/sim yolu (`--yks-hedef` + `--ika-hedef`) |

`udp` yapılandırmasında YKS ucu **üretimdeki gibi davranır**: `OPEN_ROUTE`'a ACK
üretmez, `NO_ROUTE` ve `IHA_LANDED`'a üretir. İKA ucu gerçek `IkaReceiver`'dır ve
hepsine ACK üretir. Ölçüm, YKS'nin ACK'lememesini bir arıza gibi düzeltmez.

Ayrıca §1.1 N2 eğrisine, 1..20 satırlarının yanına sözleşme tavanı
`MAX_WAYPOINTS` (`comms/iha_sender.py`) bir **üst sınır satırı** olarak eklenir;
karışım ölçümünde kullanılan rota üretim yolundan gelen tek bir rotadır ve
waypoint sayısı çıktı JSON'una yazılır.

### 2.3 Hat doluluğu

`BAUD = 57600`, 8N1 → **10 bit/bayt** → ham `5760 B/s`, bayt başına `0,174 ms`.
Bu iki sayı hesaptır, ölçüm değildir; kaynak `ATOLYE_TEST_GUNU_20260912.md`
A6 beklenti satırı. Doluluk oranı = ölçülen B/s ÷ 5760.

**Çift yönlü paylaşım — açıkça yazılır:** 57600 baud host↔telsiz **UART** hızıdır
ve her yön için ayrıdır. SiK'in **hava** arayüzü ise TDM'dir: iki yön aynı kanalı
paylaşır, dolayısıyla hava tarafında bütçeye giren (TX + RX) toplamıdır. Hava hızı
(Air Speed) ayarı **okunmamıştır**.

**ECC durumu: ÖLÇÜLEMEDİ.** Telsiz ayar sayfası (Baud, Air Speed, ECC, …) hiç
okunmadı — `results/atolye_20260912/SONUC_SABLONU.md` A6 satırı boş, `A6_sik_ayar.txt`
yok. ECC açıkken etkin hava hızının yarıya indiği bilgisi `ATOLYE_TEST_GUNU_20260912.md`
A6 satırında **"HESAP + BENZER ÖLÇÜM — ölçüm değil"** etiketiyle durur; bu rapor onu
aynı etiketle taşır ve ECC'nin açık olduğunu **varsaymaz**. Doluluk iki sütunla
raporlanır: ECC kapalı ham bütçe ve ECC açık (bütçe yarı) — ikisi de hesaptır,
hangisinin geçerli olduğu telsiz ayarı okunana kadar **bilinmiyordur**.

---

## 3. Çıktılar

`results/fdr_sprint_20260910/T243/` altında:

| dosya | içerik |
|---|---|
| `paket_boyutu.json` | N1–N5 ham sayılar (makine okunur) |
| `gorev_veri_hizi.json` | N6–N12 ham sayılar, kadans başına |
| `TABLO.md` | okunur tablo — JSON'lardan üretilir, elle yazılmaz |
| `README.md` | ölçüm künyesi, komut, sınırlar, hüküm |
| `kosum_ciktisi.txt` | betiğin ham stdout/stderr'i |

Hepsi **"ölçüm"** etiketli; RF ölçümü **değildir** (UDP loopback).

---

## 4. Kabul ve rapor kuralları

1. **Bu iş bir kapı değildir.** Ölçüm koşar ve sayı üretirse "ölçüldü", üretmezse
   "ÖLÇÜLEMEDİ" yazılır. Üçüncü bir hüküm yoktur.
2. **RAPOR ÖLÇÜTÜ:** Hat doluluk oranı yüzde 80,0 ya da üzeri çıkarsa kırmızı risk satırı açılır.
3. Kötü sayı da rapora girer: doluluk yüksek çıkarsa madde 2 uygulanır, ölçüm
   gizlenmez ya da pencere kısaltılarak yeniden koşulmaz.
4. Ölçülen her sayı FDR'ye **JSON'dan** taşınır; nöbetçi test
   (`tests/test_t243_paket_boyutu.py`) FDR'deki her sayıyı JSON'dan yeniden
   hesaplayıp karşılaştırır — bayat sayı kilidi.
5. FDR'de eski metin **silinmez**: üstü çizili bırakılır, yanına tarih ve D-kaydı
   atfı yazılır.
6. UDP loopback sayıları **RF değildir** ve RF satırının ÖLÇÜLEMEDİ hükmünü
   değiştirmez (§3.3.4.3.4 aynen kalır).

---

## 5. Tohum ve belirlenim

`TOHUM = 20260912`. Betikte `random` / `numpy.random` **kullanılmaz**: paket
boyutu tablosu tümüyle belirlenimlidir (sabit saat + sabit `seq` + sabit
koordinatlar) ve aynı `comms/protocol.py` ile bayt-eş yeniden üretilir. Tohum
tablo künyesine yazılan kayıt alanıdır; sentetik piksel rota kapalı biçimli ve
rastgeleliksizdir. Gerçek görev karışımı ölçümü ise **zamana bağlıdır** ve bayt-eş
yeniden üretilmez — orada yeniden üretilebilir olan yöntemdir, sayı değil.

---

## 6. Kilit yordamı (belge kilidi)

Nöbetçi test, bu dosyada ve `README.md`'de aranan metni **normalleştirilmiş**
biçimde arar: `~~…~~` (satır aşan), tek tilde `~…~`, `<del>` / `<s>` / `<strike>`
aralıkları ayıklanır; kalın/italik işaretleri ve tipografik kesme/tırnak düzlenir.
Ek olarak: §4 maddesindeki rapor ölçütü normalleştirilmiş metinde **tam bir kez**
geçmelidir; aynı bölümde doluluk için ikinci/rakip bir yüzde eşiği bulunması,
eş anlamlı geri dönüş ("en az / aşan" ile yeniden yazım), ölçüm hükmünün olumluya
çevrilmesi ("doğrulandı / kanıtlandı / teyit edildi / tutar") ve çelişkili ikinci
hüküm sözcükleri ("gözden geçirilmiş", "güncellenmiş kapı", "kaldırıldı",
"geçersiz") kilidi **düşürür**.

Bu kilidin normalleştirme fonksiyonları nöbetçi test dosyasında **tek yerde**
toplanmıştır ve **T242 ile kanonik yardımcıya (`tests/belge_kilidi.py`) geçirilecektir**
(kanonik yardımcı T240 dalında yazılıyor, master'da henüz yok — D-460, D-461).
