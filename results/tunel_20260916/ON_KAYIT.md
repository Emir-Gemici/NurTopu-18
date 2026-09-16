# ÖN KAYIT — MAVLink TUNNEL köprüsü (tek RFD900A, telsiz Pixhawk'ta)

**Tarih:** 2026-09-16 · **Karar sahibi:** kullanıcı (16 Eylül): tek RFD900A çifti Pixhawk
TELEM1'de kalır; Jetson Orin NX, Pixhawk TELEM2'ye 3 telli UART ile bağlı (`/dev/ttyTHS1`,
57600); Mission Planner uçuşta kullanılabilir kalmalı (acil LAND/RTL, prearm, batarya).

Bu belge **sonuçlar görülmeden** yazıldı. Kapılar sonradan gevşetilmez; düşen kapı
düşmüş olarak kaydedilir (anayasa: ÖLÇÜLEMEDİ ≠ GEÇTİ).

## 1. Sorun (koddan ve ölçümden)

- NAVITAS çerçeveleri (`comms/protocol.py` `encode`: tek satır JSON + `\n`) bugün ya UDP ile
  ya şeffaf seri telsizle (`comms/link.py` `SerialLink`) taşınıyor. Pixhawk yalnız MAVLink
  yönlendirir; ham NAVITAS baytlarını TELEM2'den TELEM1'e geçirmez.
- Çerçeve boyutları (16 Eylül, `protocol.encode` ile ölçüldü): tam telemetrili `HEARTBEAT`
  250 B; `OPEN_ROUTE` 12 yol noktası 256 B, 30 yol noktası 473 B. MAVLink2 `TUNNEL`
  (id 385) yükü en fazla 128 B → **parçalama zorunlu**.
- Parametre dökümleri (`14.09.2026.param`, `config/pixhawk/emir.param`):
  `SERIAL1_PROTOCOL=2`, `SERIAL2_PROTOCOL=2`, `BRD_SER2_RTSCTS=0`, `SYSID_THISMAV=1`,
  `SYSID_MYGCS=255`.
- Ortam: pymavlink 2.4.49 geliştirme venv'inde var (`MAVLink_tunnel_message` mevcut);
  MAVProxy geliştirme venv'inde **yok**, Jetson'da var (`navitas-cogullayici`).
- Tekrar aralıkları (`codes/karar_sozlesmesi.py`): `IKA_GO_TEKRAR_ARALIGI_S=0.25`,
  `PARASUT_TEKRAR_ARALIGI_S=0.20`. A6 ham telsiz ölçümü: RTT p95 126,5 ms (D-478).

## 2. Hedef mimari

```
HAVA: rpi_inference / iha_inis_yayinci / iha_komut_alici
        -UDP 127.0.0.1:5100- seri_hub (tünel taşıyıcı)
        -MAVLink TUNNEL- MAVProxy (navitas-cogullayici, ek --out)
        -TELEM2 /dev/ttyTHS1- Pixhawk -TELEM1- RFD900A
YER : RFD900A - COM - yer MAVLink yönlendiricisi -UDP- Mission Planner
                                                 -UDP- tünel ucu - yks_gui
```

Tüketici süreçlerin kodu **değişmez** (CONTRACTS §7.5 ilkesi korunur).

## 3. Kapsam

- Yeni: MAVLink TUNNEL bayt-akışı taşıyıcısı; `SerialLink` arayüzü (`send`, `recv` +
  zaman aşımı, `close`) — `seri_hub` ve `yks_gui` onu seri port yerine kullanabilir.
- `comms/seri_hub.py`: seri port yerine tünel taşıyıcı seçeneği.
- `comms/yks_gui.py`: tünel taşıyıcı seçeneği; saha taşıyıcısına özgü davranışlar
  (etiket, demo engeli, `tasiyici` alanı) tünel için de geçerli.
- `jetson_paket/jetson_baslat.sh` + systemd: `KIP=tunel`; `navitas-cogullayici`'ya ek
  `--out`; `PIXHAWK_SERI` TELEM2. `KIP=udp` ve `KIP=sik` davranışı **değişmez**.
- `jetson_paket/kod` ayna kopyaları + paket sözleşme testi.
- `CONTRACTS.md` yeni §7.6; sabitler (payload_type, başlık biçimi, kimlikler) tek kaynakta,
  test kilitli, kodda çıplak sayı yok.
- Tezgâh ölçüm aracı: `scripts/sik_rf_olc.py` tünel kipiyle, **aynı eşikler**.
- Saha runbook'u: yer tarafı kurulumu (Windows), MP'nin UDP bağlantısı, Jetson ortam
  değişkenleri, Pixhawk reboot sonrası yordam.

**Kapsam dışı:** İKA hattı, video, algı kodu, ArduPilot parametre değişikliği (yalnız
doğrulama listesi).

## 4. Kapılar

| Kapı | Ölçüt |
|---|---|
| K1 | `codes/test_rota_sentetik.py` → `GENEL KAPI (madde 14): GECTI` (15/15) |
| K2 | `python -m unittest discover -s tests -q` → **yeni başarısızlık yok**; taban `d8783c59` üzerinde değişiklikten önce koşulur, tabanda düşen testler adıyla listelenir |
| K3 | Birim: parça sınırları (0, 1, başlık-yükü sınırının −1/0/+1'i, 248, 256, 473, 4096 B, desteklenen tavan ve tavan+1) birebir geri kurulur; yabancı payload_type, yabancı mesaj tipi ve kendi yankısı yok sayılır; eksik çerçeve zaman aşımında düşer ve sayılır, yarım/bozuk bayt yukarı verilmez; yinelenen parça tek teslim; `recv` zaman aşımı `SerialLink`'ten uzun değil; `close` idempotent; UDP karşı ucu yokken/yeniden başlarken süreç ölmez (sayaç + KIRMIZI log) |
| K4 | Uçtan uca benzetim: gerçek pymavlink MAVLink2 paketleri; ArduPilot yayın yönlendirmesini taklit eden UDP yönlendirici (öğrenilen rota, gelen kanala geri göndermeme); yer tünel ucu ↔ yönlendirici ↔ hava `seri_hub` (tünel) ↔ gerçek `IhaKomutAlici` + sahte Pixhawk → PARACHUTE→ACK döner. Parça kaybı %0 ve %5'te `OPEN_ROUTE` ACK'i protokolün kendi tekrar bütçesi içinde alınır (zorunlu); %20 raporlanır. %0 kayıpta UDP→tünel→UDP gecikmesi p95 < `PARASUT_TEKRAR_ARALIGI_S` |
| K5 | Mutasyon: çürütücü en az 6 mutant üretir (parça boyu off-by-one, indis sırası, payload_type süzgeci, kendi-yankı süzgeci, zaman aşımı düşürme, yinelenen parça); her biri en az bir testi düşürmeli |
| K6 | `KIP=udp` ve `KIP=sik` için mevcut `jetson_baslat` ve `seri_hub` testleri aynen geçer |
| K7 | §7.6 sabitleri kodda tek kaynaktan; test kilidi |
| K8 | **Gerçek donanım tezgâh ölçümü İNSAN görevidir.** `sik_rf_olc` tünel kipi; eşik RTT p95 < min(0,25; 0,20) s. Benzetim sonucu bunun yerine GEÇTİ sayılmaz; ölçülene dek **ÖLÇÜLEMEDİ** |

Yeni testler yalnız efemer port (0) kullanır.

## 5. Tasarımda karara bağlanacak bilinen riskler

- **R1** ArduPilot yayın mesajını yalnız rota öğrendiği kanallara iletir; iki ucun kanalı
  rota tablosunda kalıcı görünmeli (yaşam mesajı?). Kimlik seçimi MP'yi ve FS_GCS'i
  (D-406 C) yanıltmamalı.
- **R2** Jetson MAVProxy ile yer MAVProxy'nin varsayılan kimliği aynı (255/230) → rota
  tablosunda kanal çakışması riski.
- **R3** Windows yer tarafında MAVProxy kurulu değil → yer yönlendiricisi seçimi (MAVProxy /
  MP MAVLink Mirror / köprünün kendisi), MP bağlantısının köprüye bağımlı olmaması
  gerekçesiyle yapılır.
- **R4** Bant: A6'da NAVITAS trafiği ~320 B/s; tünel başlık yükü + MP akışları
  Air Speed 128 içinde kalmalı.
- **R5** Pixhawk yeniden başlaması (pil değişimi) ve MAVProxy yeniden başlaması: hub'ın
  mevcut arıza semantiği (düşür, say, yeniden aç) karşılanır.

## 6. Yöntem

Tasarım (salt okuma) → iki bağımsız eleştiri (protokol/dayanıklılık · saha/ArduPilot/
entegrasyon) → nihai şartname → worktree amelesi (taban `d8783c59`) → üç bağımsız çürütücü
(mutasyon/test vakumu · gerileme/entegrasyon · saha/sözleşme) → düzeltme turları → mimar
denetimi → birleştirme. Commit yazarı Emir-Gemici, AI atfı yok. Push yok (T278).
