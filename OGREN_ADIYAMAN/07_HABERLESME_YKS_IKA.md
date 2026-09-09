# 07 · HABERLEŞME, YKS VE İKA KİLİDİ — kararı yere indirmek, hakeme kanıtlamak

> Kaynaklar: `comms/` (14 modül; kod düzeyi özet `ozet/B_comms.md`, dosya:satır atıflı) · `CONTRACTS.md` §6–§7 · `scripts/mavlink_dogrula.py`,
> `sahte_pixhawk.py`, `sik_rf_olc.py` · `config/pixhawk/README.md` · `REVIEW_LOG.md` D-02, D-06, D-374, D-381, D-383, D-393, D-403–D-407, D-422, D-427.
> Ön bilgi: UDP = adressiz, onaysız datagram; kaybolabilir. MAVLink = Pixhawk'ın ikili paket dili. Her ikisi bu dosyada yalnız projede kullanıldığı kadar anlatılır.

---

## Seviye 1 — Bir cümle ve büyük resim

Üç cihaz, iki dil: cihazlar arasında **NAVITAS protokolü** (tek satır JSON + `\n`, taşıyıcıdan bağımsız: WiFi/UDP ya da SiK 433 MHz seri),
Jetson ile Pixhawk arasında **MAVLink**. İHA her karede `OPEN_ROUTE` ya da `NO_ROUTE` yayınlar ve **ACK gelene dek tekrarlar**; YKS
hakem ekranında **iki aşamalı onay** verir (tespit görüldü → İKA'ya ulaştığı kanıtlandı); İKA ancak `OPEN_ROUTE ∧ IHA_LANDED ∧ IKA_GO`
üçlüsü tamamsa hareket eder; iniş kanıtı insan düğmesi değil **Pixhawk'ın kendi beyanıdır**. Her kritik olay `hakem_log.jsonl`'e
fsync'li yazılır. Tasarımın omurgası: **kanıtsız yeşil ışık yok**.

```
JETSON (İHA)                                   YKS PC                         İKA (RPi)
rpi_inference ─KararYayinci─► OPEN/NO_ROUTE ─► yks_gui :5005   ┐        ika_receiver :5006
                              HEARTBEAT(karar_yas) 1 Hz        │            latest / last_no_route
iha_inis_yayinci ───────────► IHA_LANDED  ────────────────────►│            iha_landed latch
iha_komut_alici :5007 ◄─ CMD(ARM/RTL/LAND/PARACHUTE) ◄─────────┘ ─CMD(IKA_GO)─► ika_go latch
   │ COMMAND_LONG ▼ ▲ COMMAND_ACK                                ▲ ACK(OPEN_ROUTE) kopyası (K8)
MAVLink çoğullayıcı udp:14550/14551/14552 ── /dev/ttyACM0 ── PIXHAWK
```

## Seviye 2 — Nasıl çalışır

### 2.1 Protokol (`comms/protocol.py`)
Her mesaj tek satır JSON, `"v": 1`, `node` (`iha/ika/yks`), `seq` (düğüm başına sayaç), `t`. Tipler:
| tip | üretici | alanlar | not |
|---|---|---|---|
| `OPEN_ROUTE` | İHA | `road` 1/2/3, `label`, `conf`, `ref_xy` ([0,0] sahada), `waypoints` (yerel metre) | doğrulanmış açık güzergâh |
| `NO_ROUTE` | İHA | `sebep` (zorunlu), `detay` | sessizlikten **farklıdır** |
| `HEARTBEAT` | herkes | `node` + isteğe bağlı telemetri (`x,y,alt,hiz,yon,bat,bat_yuzde,uydu,lat,lon,gps_fix,armed,mod,pixhawk_canli`) + İHA'da **`karar_yas`** | `None` alan yazılmaz; alan yoksa "bilinmiyor", taze sayılmaz |
| `ACK` | alıcı | `ref` (onaylanan seq), `node`, **`ref_tip`**, `ref_cmd`, `sonuc` | `ref_tip` çapraz kabulü önler (seq'ler düğüm başına) |
| `CMD` | YKS | `cmd` (`IKA_GO/ARM/DISARM/RTL/LAND/PARACHUTE`), `hedef`, `oturum` | oturum = YKS sürecinin uuid'si |
| `IHA_LANDED` | İHA | — | yalnız Pixhawk kanıtıyla üretilir |
`FrameReader` newline çerçeveleri ayıklar; bozuk JSON, `RecursionError` (derin iç içe `[[[[`) sessizce atılır; tampon tavanı **64 KiB**
(SiK gürültüsü newline üretmeden aksa bile tampon şişmez). **CRC yok** (bilinen sınır; bozuk satır atılır).

### 2.2 Taşıyıcılar (`comms/link.py`)
`UDPLink(reuse=False)`: `SO_REUSEADDR` yok → ikinci süreç aynı porta bağlanamaz (D-405: eskiden ikinci süreç sessizce datagramları
çalıyordu). `recv()` `ConnectionResetError`'ı yutar (D-06: Windows'ta ölü akrana gönderim sonraki `recvfrom`'u patlatıp YKS dinleyicisini
öldürüyordu). `SerialLink(exclusive=True)`: flock; `recv` ilk bayta kadar bekleyip `in_waiting` kadar okur (D-403: eski `read(256)` ACK
turunu **622,6 ms**'ye çıkarıyordu, paraşüt tekrar aralığının 3 katı; şimdi 0,8 ms).

### 2.3 Akış (a): rota yayını — `comms/iha_sender.py` `KararYayinci` (K1, §6.5)
Kamera döngüsü kararı **latest-wins tek yuvaya** yazar, ACK beklemez; ayrı iş parçacığı gönderir. Sıra: ret sebebi varsa `NO_ROUTE`;
`open_path None` ise `NO_ROUTE(KARAR_YOK)`; piksel rota yerel metreye çevrilir (`x=(px−px₀)·mpp`, `y=(py₀−py)·mpp`, ilk nokta [0,0],
segment ≤ 2,10 m, yarıçap ≤ 60 m; düşerse `NO_ROUTE(OLCEK_YOK|ROTA_GEOMETRI)`); **güven kapısı son savunma** `send_open_route`'ta
(eşik altı → NO_ROUTE); `_tekrarli_gonder` 8 × 0,25 s ACK bekler, tüm ACK'ler gelince pencere erken terk edilir (D-383: eski "308 ms
telsiz gecikmesi" bu beklemenin ölçümüydü, gerçek RTT 0,06 ms). Heartbeat ayrı iş parçacığı 1,0 s < İKA `hb_timeout` 3,0 s; alan
toplama kendi try'ında (T171: eksik öznitelik telsizi sessizce susturuyordu). `karar_yas` = son **algı kararının** yaşı (D-374: gerçek
uçuşta 45–51 s kör aralıkta hat canlı görünür, algı ölüdür).

### 2.4 Akış (b): YKS'den Pixhawk'a komut — `comms/iha_komut_alici.py` (D-393/D-403)
1. YKS `CMD(cmd, "iha", oturum)` gönderir; `AckliTekrar` aynı seq ile PARACHUTE 0,20 s × 40, ARM/RTL/LAND 0,25 s × 20 tekrarlar.
2. Hedef `--iha HOST:5007` ile **pinlenir** (D-403 KRİTİK-1: heartbeat'ten öğrenilen adres `rpi_inference`'ın efemer portuydu, paraşüt
   komutu alıcıya **hiç ulaşmazdı**).
3. Alıcı: `hedef==iha` · kaynak `--izinli-kaynak` pinine eşit (zorunlu) · `cmd` izinli kümede · **saat kapısı** (aşağıda) · oturumlu
   anahtar `(oturum, seq, cmd)` daha önce ACCEPTED ise eylem tekrarlanmaz, ACK yinelenir · MAVLink akranı görülmeden gönderim yok
   (pymavlink `udp:` sunucu kipinde akran yokken **sessizce hiçbir şey göndermez**).
4. `command_long_send` (PARACHUTE→`DO_PARACHUTE RELEASE`, ARM/DISARM→`COMPONENT_ARM_DISARM`, RTL→`NAV_RETURN_TO_LAUNCH`, LAND→`NAV_LAND`);
   0,5 s içinde `COMMAND_ACK` (aynı `command`, kaynak sysid = hedef, bileşen otopilot, `MAV_RESULT_ACCEPTED`) gelirse **ancak o zaman**
   YKS'ye `ACK(ref_tip="CMD", ref_cmd, sonuc="ACCEPTED")`. Ret/zaman aşımı → ACK yok, kırmızı log; YKS tekrarlar, ekran "ACK YOK".
5. **İdempotentlik bilerek yok** (D-403 KRİTİK-2): eski `(cmd, seq)` hafızası, YKS her açılışta seq'i 1'den başlattığı için yeniden açılan
   YKS'nin PARACHUTE'unu "mükerrer" sayıp MAVLink'e göndermeden ACK'lıyordu — yeşil "İHA ALDI", paraşüt kapalı. Oturum anahtarı çözdü.
6. YKS'de kabul: güçlü ACK (`kritik_komut_ack_gecerli_mi` beş alan) **ve** ARM için 2,5 s içinde beklenen `armed` değerini taşıyan taze
   Pixhawk heartbeat; RTL/LAND için `mod` alanı eşleşmeli. Paraşüt için ACK yalnız "komut kabul edildi"; mekanik açılma sensörü **yok**, ekran bunu yazar.

**Saat kilidi (D-422):** Jetson'da RTC yok; komut yaşı YKS damgasıyla ölçülüyordu; 2 saat sapmada ARM 0/20 **kalıcı** reddediliyordu ve
sapma büyüdükçe ofseti öğrenmek için gereken örnek de eleniyordu. Çözüm: NTP minimum-filtresi mantığıyla ofset öğrenilir (bant içi 2,
bant dışı 6 destekleyen örnek), yaş ofsete göre; yerel saat adımı monotonik/duvar farkından yakalanır. Bedel: sapma varken merdivenin
ilk 2 basamağı reddedilir, 3.'de geçer. Ölçüldü: ofset −600 s öğrenildiğinde 60 s ölü pencere ve 241 komut reddi vardı → kapatıldı.

### 2.5 Akış (c): iniş kanıtı — `comms/iha_inis_yayinci.py` + `inis_kaniti.py`
`yerde_mi`: Pixhawk `EXTENDED_SYS_STATE.landed_state == ON_GROUND` ve ardından `GLOBAL_POSITION_INT.relative_alt < 1,0 m`, **aynı sysid**,
**3 ardışık temiz çift**, mutlak deadline. Yabancı sysid **atlanır** (D-389: eskiden geçersiz kılıyordu, üçüncü tarafa bizi kör etme yetkisi
veriyordu). ON_GROUND dışı meşru durum terminal değil, ilerlemeyi sıfırlar. ArduCopter `EXTENDED_SYS_STATE`'i hiçbir `SR*` akışında
kendiliğinden vermez → `AkisIstekcisi` `SET_MESSAGE_INTERVAL` ile ister, her 10 s yeniler, 5 s sessizlikte kırmızı uyarı + yeniden istek
(T207/D-406: istek bağlantıya özeldir, Pixhawk yeniden başlayınca — pil değişimi — silinir, kanıt sessizce ölürdü). Kanıt gelince
`IHA_LANDED` 8 × 0,25 s ACK'li, sonra 600 s boyunca 0,5 s'de bir heartbeat (K6: `link_lost` yalnız heartbeat gerçekten kesilince).
`relative_alt` home'a göre bağıl; birincil kanıt `landed_state`. Aynı dosyadaki `BagilIrtifaOkuyucu` `rpi_inference`'ın ölçek irtifasını verir.

### 2.6 Akış (d): İKA alıcısı — `comms/ika_receiver.py`
`OPEN_ROUTE` → `latest`, ACK gönderene **ve** YKS adresine kopya (K8; `--yks` UDP'de fiilen zorunlu çünkü OPEN_ROUTE IKA_GO'dan önce
gelir). `NO_ROUTE` → `last_no_route`, `latest` **ezilmez** (geçici durum; sürüşte gelirse güvenli duruş). `IHA_LANDED` → latch + ACK.
`CMD IKA_GO` → latch (ilk alımda `ika_go_monotonic` sabitlenir, mükerrer alım yalnız ACK'lanır — YKS'nin tekrarı ancak böyle durur).
Sürüş izni `ika_go ∧ iha_landed`; `run_if_route_valid` = link canlı ∧ izin ∧ rota ∧ NO_ROUTE yok. 3 s mesaj yoksa `link_lost`.

### 2.7 YKS hakem ekranı — `comms/yks_gui.py` (4535 satır, Tk)
Paneller: HTAB haritası + rota, canlı algı (üretim modeliyle gerçek çıkarım; telsiz vs. yerel algı **karıştırma yasağı** T81), RAW kamera,
"AÇIK YOL TESPİTİ", hakem onayı, düğüm durumu + Pixhawk modu + ham GNSS, günlük, kronometreler (İHA 15:00, İKA 10:00, hazırlık 15:00),
düğmeler: ALAN GİRİŞİ / TAKIM HAZIR / MÜDAHALE(−100) / ARM / FIRLATMA / İHA İNDİ / PARAŞÜT(−50) / İKA BAŞLAT / HB TEMAS / ACİL RTL / ACİL LAND.
- **İki aşamalı onay** `onayla`: 1/2 "tespit doğrulandı"; 2/2 "İKA'ya aktarıldı" **yalnız** İKA'dan `ACK(ref=rota.seq, ref_tip=OPEN_ROUTE)`
  ekranda görüldüyse; ACK İHA'ya ancak 2/2'de gider. Fail-closed retler: `ANKOR_YOK`, `BAYAT_TESPIT`, `IKA_ACK_KANITI_YOK`.
- **Tazelik**: yaş = min(son OPEN_ROUTE yaşı, son İHA heartbeat yaşı) > **5 s** → BAYAT; `karar_yas` alanı hiç gelmediyse taze sayılmaz.
  Tüm damgalar `time.monotonic` (D-384: duvar saati geri atlayınca bayat tespit taze görünüyordu).
- Güven eşiği altı OPEN_ROUTE'a ACK **üretilmez** (`ROTA_REDDEDILDI` kaydı). NO_ROUTE ve IHA_LANDED ACK'i otomatiktir (teslim kanıtı, rota onayı değil).
- **Aktarım havadayken** (§2.2.3): İKA ACK kopyası geldiği an `_iha_havada_mi` damgası; iniş kanıtı ACK'ten önce gelirse kırmızı ihlal riski.
- **ARM gerçeği**: `armed` yalnız Pixhawk heartbeat'inden; FIRLATMA ancak taze heartbeat ile ARM doğrulanmışsa. Kritik komutlar iki tık, DISARM teyit 4 s, paraşüt 3 s "EMİN MİSİN?" (modal yok).
- **Kaynak kilidi**: İHA verisi Jetson IP'sinden, ACK'ler tam uçlardan; heartbeat pinlenen adresi ezemez. Protokol zarfı: `v != 1` ret; heartbeat seq geri/tekrar ret.
- **Model soyu**: hakem ekranı model adını registry etkin profilinden okur, yüklerken sha + imgsz doğrular; uyuşmazsa yüklenmez.
- **Kanıt kaydı** (`hakem_kaydi.py`, §6.8): JSONL, satır başına `flush+fsync`, oturum uuid, monotonik damga; 16 olay (`ROTA_ALINDI`,
  `HAKEM_ONAYI_1/2`, `IKA_AKTARIM_KANITI`, `IHA_INIS_KANITI`, `KRONOMETRE_*`, `KAMERA_KANIT`, `TELEMETRI_KANIT` [kenar + 30 s tekrar], `UI_OLAYI` …).
  Dosya açılamazsa kurucu yükseltir; sonradan yazma hatası **FIRLATMA ve ONAY'ı kilitler, ARM/RTL/LAND açık kalır** (aracı indirebilmek emniyettir).
  `YKS_ARAYUZ_HAZIR` satırı model sha'sı, repo commit'i, çalışma ağacı durumu ve `yks_gui.py`'nin kendi sha'sını taşır.
- **`--fda` kipi** (§6.7, D-407): süre 600 s; 2/2 onay İKA kanıtı aramaz (dayanak "YKS'de canlı görüldü + hakem onayı"); PARAŞÜT ve İKA düğmeleri
  yalnız UI'da değil **eylemde** kapalı; FIRLATMA → "KALKIŞ"; iniş kanıtı zorunlu. Ölçülen tıkanma: yarışma kipinde 2/2 `ika_aktarim_kaniti_var()`
  istediği için FDA'da onay hiç tamamlanmıyor, İHA'ya ACK gitmiyordu — uçuşu geçersiz kılacak GUI kilidi.
- `yks_monitor.py` **emekli** (D-392): otomatik hakem onayı basıyordu; `--legacy-bilerek` olmadan exit 2.

### 2.8 Seri port sahipliği: MAVLink çoğullayıcı ve SiK hub
Bkz. 10 §2.4. Kısaca: Pixhawk `/dev/ttyACM0` yalnız çoğullayıcı (MAVProxy `--out udp:127.0.0.1:1455N --streamrate 8`); SiK `/dev/ttyUSB0` yalnız
`seri_hub.py` (UDP 5100; statik tüketici 5007; datagram = çerçeve; seri okuma 20 ms; arızada UDP çerçeveleri **düşürülür, kuyruklanmaz**;
öğrenilen tüketici tavanı 32; SIGTERM sayaç logu). SiK hattında hedef YKS'dir; `--ika-hedef` hub'a verilmez (İKA ACK'i seriden gelmediği için
8 tekrar/2,11 s boşa gidiyordu, D-405). İKA'nın saha hattı (SiK çok-noktalı mı, WiFi mi) **karara bağlanmadı**.

### 2.9 Yardımcı araçlar
`scripts/mavlink_dogrula.py` ön-uçuş kapısı: beklenen sysid'den HEARTBEAT (15 s), `SET_MESSAGE_INTERVAL`, 10 s pencerede Hz: HEARTBEAT ≥ 0,5,
`GLOBAL_POSITION_INT ≥ 4`, `EXTENDED_SYS_STATE ≥ 1` değilse exit 1. `scripts/sahte_pixhawk.py`: gerçek MAVLink çerçevesi/CRC ile sysid 1
comp 1 (comp 0 olsaydı `inis_kaniti` reddediyordu); senaryolar `ucus/inis/yerde/yabanci/donuk-saat`; COMMAND_LONG'a `kabul/ret/sessiz`.
`scripts/sik_rf_olc.py`: iki SiK ile `CMD(RF_PROBE)` RTT; p95 < 0,20 s ve < 0,25 s → UYUMLU; hiç ACK yok → ÖLÇÜLEMEDİ (exit 2).
`comms/kamera_istemci.py`: YKS'nin Jetson `/kare.jpg` + `/durum` istemcisi (5 Hz, tazelik 2 s; aynı kare tekrar gelirse tazelik yenilenmez).

## Seviye 3 — Sayılar ve sınırlar

| sabit | değer | nerede |
|---|---|---|
| Portlar | YKS 5005 · İKA 5006 · İHA komut 5007 · hub 5100 · MAVLink 14550/14551/14552 · kamera HTTP 8080 | `comms/*`, CONTRACTS §7.4–7.5 |
| SiK | `/dev/ttyUSB0` 57600 baud | `link.py` |
| Rota/iniş tekrar | 8 × 0,25 s | `iha_sender.py` |
| IKA_GO / ARM / RTL / LAND tekrar | 0,25 s × 20 · DISARM teyit 4,0 s | `karar_sozlesmesi` |
| PARACHUTE tekrar | 0,20 s × 40 · ceza −50 | `karar_sozlesmesi` |
| `COMMAND_ACK` tavanı | 0,5 s | `MAVLINK_KOMUT_ACK_TAVANI_S` |
| Heartbeat | İHA 1,0 s · İKA `hb_timeout` 3,0 s · iniş sonrası 0,5 s × 600 s | |
| Tazelik | YKS tespit 5,0 s · ARM durumu 2,5 s · irtifa 0,5 s | |
| MAVLink akış asgari | `GLOBAL_POSITION_INT` 4 Hz · `EXTENDED_SYS_STATE` 1 Hz (istek çarpanı 2) | `karar_sozlesmesi` |
| Uçtan uca gecikme (33 gerçek kare, loopback) | önişleme 5,0/7,1 · çıkarım 12,3/14,9 · maske 17,5/24,1 · karar 49,7/68,6 · telsiz+ACK 2,3/2,6 · **toplam p50/p95 84,8/113,2 ms** (PC) | `results/fda_butce/olcum_20260901.json` |
| Hub zamanlama (Windows) | UDP→seri p50 10,6 / p95 31 ms; 20 Hz'de 45 ms | CONTRACTS §7.5 |
| Hakem kaydı 5 Eylül provası | 1115 satır, 277 dk | `results/prova/20260905_*/hakem_log.jsonl` |

**ÖLÇÜLEMEDİ (dürüst liste):** gerçek SiK 433 MHz RTT/kayıp/menzil (DDR ">%98, 300 m" kanıtsız); gerçek Pixhawk `COMMAND_ACK`; kamera
hattı gecikmesi; İKA saha hattı topolojisi; `iha_komut_alici` örnek ucu 14560 ↔ sözleşme 14552 (servis dosyasındaki gerçek değer
doğrulanmalı). Tüm komut hattı ölçümleri **sahte Pixhawk** ile.

---

## Jüriye 30 saniyede

> "Cihazlar arasında tek satır JSON konuşuyoruz, taşıyıcı WiFi ya da 433 MHz telsiz fark etmez. İHA her karede ya açık güzergâhı ya
> da sebebiyle 'rota yok' der, onay gelene kadar tekrarlar. Hakem iki aşamada onaylar; ikinci aşama İKA'nın aldığına dair ACK
> ekranda görünmeden açılmaz. İKA, İHA'nın indiğini insan düğmesinden değil Pixhawk'ın kendi 'yerdeyim' beyanından öğrenir; üç
> koşul birden sağlanmadan tekerlek dönmez. Paraşüt ya da ARM komutunda 'alındı' demek için Pixhawk'ın kabul cevabını bekleriz.
> Her olay diske fsync'li yazılır. Gerçek telsiz hattını henüz ölçmedik, bunu raporda 'ölçülemedi' diye yazıyoruz."

## Kendini sına

1. `NO_ROUTE` ile sessizlik arasındaki fark ne; `NO_ROUTE` İKA'da `latest`'i ezer mi?
2. `ref_tip` neden var? Somut kusuru anlat.
3. İHA'da idempotentlik hafızası neden kaldırıldı?
4. "İHA ALDI" yeşil yanması için YKS neyi bekler? Paraşütte neyi bilemez?
5. İniş kanıtının üç şartı? Yabancı sysid gelirse?
6. `EXTENDED_SYS_STATE` neden periyodik istenir?
7. Saat kilidi D-422: kusur neydi, çözümün bedeli ne?
8. Hakem 2/2 onayı hangi kanıtla açılır; FDA kipinde neden farklı?
9. Kanıt kaydı yazılamazsa hangi düğmeler kilitlenir, hangileri kalır, neden?
10. "308 ms telsiz gecikmesi" nasıl çürüdü?

<details><summary>Cevaplar</summary>

1. NO_ROUTE sebepli, açık bir ret; sessizlik hakem ekranında "belki"; ezmez, `last_no_route`'a yazılır, sürüşte güvenli duruş. 2. `seq` düğüm başına; OPEN_ROUTE seq=7 bekleyen gönderici IHA_LANDED seq=7'nin ACK'ini "aktarıldı" sayıyordu (D-405 Q4). 3. YKS her açılışta seq 1'den başlıyor; yeniden açılan YKS'nin PARACHUTE'u "mükerrer" sayılıp MAVLink'e gitmeden ACK'lanıyordu; oturumlu anahtar geldi. 4. Beş alanlı güçlü ACK (ref, node=iha, ref_tip=CMD, ref_cmd, sonuc=ACCEPTED) ve ARM için taze heartbeat'te `armed`; paraşütün mekanik açıldığını (sensör yok). 5. ON_GROUND + relative_alt < 1 m + aynı sysid, 3 ardışık çift; atlanır (kanıt sayılmaz, geçersiz kılmaz). 6. ArduCopter bu mesajı SR akışlarında vermez; istek bağlantıya özel, Pixhawk reboot'unda silinir. 7. Mutlak sapma filtresi ofseti öğrenmek için gereken örneği eliyordu → 2 saat sapmada ARM kalıcı red; şimdi ofset öğreniliyor, bedeli merdivenin ilk 2 basamağının reddi. 8. İKA'dan gelen `ACK(ref=rota.seq, ref_tip=OPEN_ROUTE)`; FDA'da İKA yok, kanıt hiç gelmeyeceği için dayanak "YKS'de canlı görüldü + hakem onayı". 9. FIRLATMA ve ONAY kilitlenir; ARM/DISARM/RTL/LAND açık kalır: kanıt kaydı bozukken bile aracı indirebilmek emniyetin kendisidir. 10. Bağımsız çürütücü, ACK penceresinin 0,3 s soket zaman aşımına kadar beklediğini buldu; gerçek loopback RTT 0,06 ms; p95 0,458 → 0,113 s (D-383).
</details>

## Kaynaklar
`comms/protocol.py`, `link.py`, `iha_sender.py`, `ika_receiver.py`, `iha_komut_alici.py`, `iha_inis_yayinci.py`, `inis_kaniti.py`, `seri_hub.py`, `yks_gui.py`, `hakem_kaydi.py`,
`komut_tekrar.py` · `CONTRACTS.md` §6–§7 · `tests/test_ika_go_ackli_tekrar.py`, `test_iha_landed_gate.py`, `test_faz_b_yks_fda_kipi.py`, `test_yks_hakem_kanit_olaylari.py`,
`test_iha_komut_saat_ve_tekrar.py` · `ozet/B_comms.md`.
