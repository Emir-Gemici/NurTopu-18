# FAZ B — CUMARTESİ DONANIM GÜNÜ PLANI (5 Eylül 2026)

> **Yazan: Claude 2 — Fable 5.1, mimar.** Kullanıcı: *"3.'yü beraber yapacağız."*
> Bu belge saat sırasıyla ne yapılacağını, her adımın **mekanik kapısını** ve
> **düşerse ne olacağını** yazar. Göz kararı yok: her adımın bir aracı ve bir
> çıkış kodu var. Kaynaklar: `SAHA_RUNBOOK.md` §3, `jetson_paket/GUN1_KONTROL_LISTESI.md`,
> D-387..D-402.
>
> ⛔ **Değişmezler:** üretim kodu bu gün DEĞİŞMEZ (dondurma yakın, §6.1);
> ölçülen her sayı ham çıktısıyla `results/faz_b_20260905/` altına gider;
> `ÖLÇÜLEMEDİ ≠ GEÇTİ`.

## 0. Gelmeden önce (cuma akşamı, PC)

| ✓ | ne | kapı |
|---|---|---|
| ☐ | Genel kapı + tam suit | 15/15 · OK |
| ☐ | Kuru koşu | `scripts/saha_kuru_kosu.py` → tek kopuk: `motor` |
| ☐ | Paket aynası | `scripts/jetson_paket_hazirla.py` → "hepsi senkron" |
| ☐ | Dört Faz B aracı sahte uçlarla yeşil | `tests/test_faz_b_*.py` OK |
| ☐ | Model dosyaları pakette | `.pt` + `_512_fp16.onnx` |

## 1. 🔴 İLK KARAR — MAVLink çoğullayıcı (Jetson'da, her şeyden önce)

**Ölçülen olgu (3 Eylül):** Pixhawk'ı bugün **iki** üretim süreci ayrı ayrı açıyor
(`rpi_inference` irtifa okuyucu · `iha_inis_yayinci`), üçüncüsü geliyor
(`iha_komut_alici` — paraşüt/ARM aktarımı). Seri port (`/dev/ttyACM0`)
**tek sahiplidir**; ikinci süreç açılamaz ya da ilkinin akışını çalar.
Kılavuzların hiçbiri çoğullayıcıdan söz etmiyordu (grep: 0).

**Karar (CONTRACTS §7.4):** Jetson'da **mavlink-router** (ya da MAVProxy
`--out udp:127.0.0.1:14550 --out udp:127.0.0.1:14551 --out udp:127.0.0.1:14552`)
seri portu tek başına açar; her tüketici **kendi UDP ucundan** okur:

| tüketici | uç | not |
|---|---|---|
| `rpi_inference --mavlink` | `udp:127.0.0.1:14550` | irtifa→mpp |
| `iha_inis_yayinci --mavlink` | `udp:127.0.0.1:14551` | iniş kanıtı, `--sysid 1` |
| `iha_komut_alici --mavlink` | `udp:127.0.0.1:14552` | paraşüt/ARM aktarımı (yazar) |

Kapı: üç uç aynı anda açıkken `scripts/mavlink_dogrula.py --mavlink udp:127.0.0.1:1455N`
üçünde de GEÇTİ. Düşerse: çoğullayıcı kurulmadan **hiçbir** MAVLink işi başlamaz.

## 2. Saat sırası

| saat | adım | araç / komut | kapı | düşerse |
|---|---|---|---|---|
| 09:00 | Jetson açılış, JetPack/TensorRT sürümü | GUN1 §1 (1a–1e) | sürümler kaydedildi | kılavuzdaki sürüm tablosuyla uyuşmazlık → durdur, not al |
| 09:30 | Paket kopyala, kayıt defteri, model | GUN1 §2–3 | `model_kayit_dogrula` True | `--kayit-dogrulamasiz` YASAK (T73) |
| 10:00 | **`.engine` derle** (T16/T109) | GUN1 §3 `yolo export … format=engine imgsz=512 half=True` | dosya var + `model_registry.py` kaydı | ONNX'ten tekrar; olmazsa PT'yle devam (FPS kapısı PT'de ölçülür, engine "ÖLÇÜLEMEDİ") |
| 10:45 | **Gerçek FPS** (T17) | `jetson_fps.py` GUN1 §5 | uçtan uca ≥ **0,61 FPS** (türetilmiş eşik, D-374/376) p50 ve p95 ayrı | eşiğin altındaysa **kapı düşer, eşik gevşetilmez**; sebep deftere |
| 11:15 | `.engine`–PT karar denkliği | GUN1 §4 | uyuşmazlık ≤ 5/260 (D-303 kuralı) | engine ÜRETİME ALINMAZ, PT'yle uçulur |
| 12:00 | 🔴 çoğullayıcı kur | §1 | 3 uçta `mavlink_dogrula` GEÇTİ | bkz. §1 |
| 12:30 | **Pixhawk ön-uçuş doğrulama** | `mavlink_dogrula.py --sysid 1 --sure 10` | HEARTBEAT sysid=1 · GLOBAL_POSITION_INT ≥ 4 Hz · EXTENDED_SYS_STATE ≥ 1 Hz | EXTENDED gelmiyorsa ArduPilot `SR*_EXTRA3` / `SET_MESSAGE_INTERVAL` — araç zaten ister; hâlâ yoksa **iniş kanıtı sahada ÖLÜ** → uçuş yok |
| 13:00 | İniş kanıtı canlı prova (araç yerde) | `iha_inis_yayinci --mavlink udp:…:14551 --sysid 1 --kanit-timeout 60 --yks …` | IHA_LANDED ACK'li yayınlandı (D-389: alçalmayı bekler, yabancı sysid kör edemez) | ACK yoksa `--yks` adresi/port; kanıt yoksa EXTENDED akışı (bir üst satır) |
| 13:30 | **Paraşüt/ARM aktarım provası** (PARAŞÜT SERVOSU BAĞLI DEĞİLKEN) | YKS PARAŞÜT düğmesi → `iha_komut_alici` → Pixhawk | YKS'de "İHA ALDI ✓ PARACHUTE ACK"; Pixhawk MAVLink konsolunda `DO_PARACHUTE` görüldü | ACK yoksa alıcı hattı/`--bind`; ACK var komut yoksa **alıcı yalan söylüyor** → D-393 sözleşme ihlali, kırmızı |
| 14:00 | **SiK RF ölçümü** | `sik_rf_olc.py --rol yanki` (İKA tarafı) + `--rol olc --n 50` (YKS) | RTT p95 < 0,20 s (paraşüt tekrar aralığı) · kayıp raporlandı | p95 aşarsa tekrar aralıkları **yeniden ön kayıtla** (D-393 sabitleri) |
| 15:00 | **İKA sürücü arka ucu** | `GercekSurucu(arka_uc=…)` doldur → `ika_surucu_kabul.py --surucu gercek --arka-uc …` | K1–K6 GEÇTİ, K3 "GÖZLE TEYİT" | K3 hareket yoksa arka uç protokolü; fail-closed (K5) sahtede zaten kilitli |
| 16:00 | İKA tam zincir (gerçek sürücü) | `saha_baslat.py ika --yks …` + YKS'den IKA_GO | §2.2.5 kilidi: IHA_LANDED+IKA_GO gelmeden 0 hareket; sonra rota izleme | kuru koşu `motor` halkası bu adımda GEÇTİ'ye döner |
| 17:00 | Sabit kanat / mancınık / geofence yapılandırması (Pixhawk, insan+mimar) | GCS | görev planı + geofence + paraşüt otonom tetik parametreleri kaydedildi | yazılım tarafı yok — repo dışı, tutanağa |
| 18:00 | Gün kapanışı | `results/faz_b_20260905/` + `REVIEW_LOG` kaydı | her adımın ham çıktısı klasörde | eksik çıktı = ÖLÇÜLEMEDİ |

## 3. Uçtan uca "tek komut" hedefi (thazırlık, §6.2)

Gün sonunda üç istasyonun her biri **tek komutla** kalkmalı; süre ölçülüp yazılır:
- YKS PC: `saha_baslat.py yks --ika <IKA_IP>:5006`
- İKA: `saha_baslat.py ika --yks <YKS_IP>:5005`
- Jetson: çoğullayıcı + `rpi_inference` + `iha_inis_yayinci` + `iha_komut_alici`
  (bir `jetson_baslat.sh` bu üçünü + çoğullayıcıyı kaldırır — **cumartesi yazılır**,
  komutlar netleşince).

## 4. Getirilecekler (insan)

Jetson + güç · Pixhawk + telem kablosu (USB/ttyACM) · **iki** SiK 433 MHz + anten ·
İKA motor sürücüsü + kablolama şeması (arka uç protokolü için) · GCS'li dizüstü ·
paraşüt servosunu **bağlamadan** tetik provası için servo test ucu.

## 5. Bu belgenin sınırı

Hiçbir kapı burada "geçmiş" sayılmaz; hepsi cumartesi **koşulunca** deftere geçer.
Dört yeni aracın (`iha_komut_alici`, `mavlink_dogrula`, `sik_rf_olc`,
`ika_surucu_kabul`) bugün sahte uçlarla yeşil olması, gerçek donanımda
geçeceklerinin kanıtı değildir — sadece **ilk koşumun kör olmayacağının** kanıtıdır.
