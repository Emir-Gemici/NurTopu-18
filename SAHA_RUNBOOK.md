# SAHA RUNBOOK — kanonik saha yordamı (P4 · D-394 · 2026-09-02)

> **Bu dosya saha günü yordamının TEK güncel kaynağıdır.** Eski iki belge
> (`results/t123/saha_gunu_kontrol_listesi.md` — eski model sürümleriyle bayat;
> `results/saha_zinciri_20260826/saha_gunu.md` — 26 Ağustos dünyası, "Jetson
> 30 Eylül'de" varsayımı) TARİHSEL KAYITTIR, komut kopyalanmaz.
> Sürüm/komut satırları belge kapısıyla kilitlidir: `tests/test_p4_runbook.py`
> (model adı kayıt defterinden doğrulanır — çıplak sürüm sözü burada değil,
> `config/model_registry.json`'dadır).
>
> Takvim (plan v2): aviyonik+Jetson **5 Eylül**, kesin hazır **21 Eylül**,
> tek atış **30 Eylül**.

## 0. Sahaya çıkmadan (PC'de, her seferinde)

| ✓ | ne | komut | başarı ölçütü |
|---|---|---|---|
| ☐ | Genel kapı | `<venv> -B codes/test_rota_sentetik.py` | `15/15` (madde 14) |
| ☐ | Test paketi | `<venv> -B -m unittest discover -s tests -q` | `OK` |
| ☐ | Kuru koşu | `<venv> -B scripts/saha_kuru_kosu.py --cikti results/saha_kuru_kosu_<tarih>` | Kopuk halka yalnız **`motor`** (GercekSurucu arka ucu Faz B'de dolana dek — D-390). Yeni kopuk çıkarsa **regresyon**: sahaya çıkma |
| ☐ | Paket aynası | `<venv> scripts/jetson_paket_hazirla.py` | "hepsi senkron" |
| ☐ | Model pakette | `ls jetson_paket/models/` | Üretim modeli `navitas_seg_v36_best.pt` **ve** `navitas_seg_v36_best_512_fp16.onnx` |
| ☐ | H3 video (manuel, model yükler) | `<venv> drone/test_uctan_uca.py --hizli` | exit 0 — **genel kapıda DEĞİL** (bilerek: GPU işi, D-392) |

## 1. Açılış kartı (thazırlık ≤ 900 s — §6.2, her 30 s +1 puan)

İstasyon başına **TEK komut** (`scripts/saha_baslat.py` süreyi ölçüp yazar):

```bash
<venv> scripts/saha_baslat.py yks --ika <IKA_IP>:5006 --iha <JETSON_IP>:5007   # YKS (--iha: paraşüt/ARM alıcısı, D-403)
<venv> scripts/saha_baslat.py ika --yks <YKS_IP>:5005     # İKA istasyonu
<venv> scripts/saha_baslat.py --komutlar                  # kartı yazdır
```

SiK (433 MHz) ile: `saha_baslat.py yks --serial COM5 --baud 57600`.
⚠ `--yks` İKA'da UDP'de fiilen **zorunludur** (CONTRACTS §6.6/K8: OPEN_ROUTE
IKA_GO'dan önce gelir; adres verilmezse hakem aktarım kanıtı hiç gitmez).

## 2. YKS operatör kartı

- **A** = ARM/DISARM (uçuşta DISARM iki adımlı teyit ister — T180).
- **FIRLATMA** yalnız ARM'dayken damga atar (yazılım kilidi, D-393).
- **PARAŞÜT (manuel −50)**: iki adımlı teyit; komut ACK gelene dek tekrarlar,
  ACK yoksa ekran KIRMIZI uyarır (D-393). Yalnız son çare — §6.4 sınırı.
- **R** = onay sıfırlama (tekrar fırlatma yordamının 1. adımı).
- İKA BAŞLAT: yalnız IHA_LANDED + hakem onayı sonrası açılır (§2.2.5 kilidi).

## 3. İHA / Jetson (5 Eylül'den itibaren)

Cihaz kurulum ve `.engine` derleme: `jetson_paket/JETSON_KILAVUZ.md` +
`jetson_paket/GUN1_KONTROL_LISTESI.md` (Gün-1 kapıları: T16/T17 FPS ve
karar denkliği). İniş kanıtı yayıncısı (Jetson'da, uçuş öncesi hazır):

🔴 **Önce çoğullayıcı (CONTRACTS §7.4):** seri Pixhawk tek sahiplidir; üç
süreç aynı anda `/dev/ttyACM0` açamaz. Jetson'da mavlink-router (ya da
MAVProxy `--master /dev/ttyACM0 --out udp:127.0.0.1:14550 --out
udp:127.0.0.1:14551 --out udp:127.0.0.1:14552`) portu tek başına açar;
tüketiciler UDP uçlarından bağlanır. Doğrulama: `scripts/mavlink_dogrula.py
--mavlink udp:127.0.0.1:1455N --sysid 1` üç uçta da GEÇTİ.

```bash
python3 jetson_paket/kod/iha_inis_yayinci.py \
    --mavlink udp:127.0.0.1:14551 --sysid 1 --kanit-timeout 900 \
    --ika <IKA_IP>:5006 --yks <YKS_IP>:5005
python3 jetson_paket/kod/iha_komut_alici.py \
    --mavlink udp:127.0.0.1:14552 --sysid 1 --bind 0.0.0.0:5007
```

- `iha_komut_alici` = YKS'nin PARAŞÜT/ARM/DISARM komutlarını Pixhawk'a aktarır
  ve **yalnız aktarım başarılıysa** ACK döner (D-393 dürüstlük sözleşmesi);
  YKS bu sürecin `--bind` adresini `--iha` olarak bilmeli.
- **SiK (433 MHz) kipi — CONTRACTS §7.5:** seri SiK portu da tek sahiplidir;
  üç süreç `--serial /dev/ttyUSB0` ile AÇILMAZ. `seri_hub` portu tek başına
  açar, süreçler UDP loopback üzerinden konuşur (kodları değişmez):
  ```bash
  python3 jetson_paket/kod/seri_hub.py --port /dev/ttyUSB0 --bind 127.0.0.1:5100 \
      --tuketici 127.0.0.1:5007
  # rpi_inference  --yks-hedef 127.0.0.1:5100 --ika-hedef 127.0.0.1:5100
  # iha_inis_yayinci --yks 127.0.0.1:5100 --ika 127.0.0.1:5100
  # iha_komut_alici  --bind 0.0.0.0:5007
  ```
  Tek komut: `jetson_baslat.sh` (KIP=udp|sik) — `jetson_paket/JETSON_BASLAT.md`.

- `--sysid 1` = ArduPilot varsayılan sistem kimliği (D-389: pin beyana dayanır;
  araç farklı sysid'e ayarlandıysa buradaki değeri ona eşitle).
- `--kanit-timeout 900` = İHA görev süresi (§6.2); yayıncı iniş kanıtını bu
  pencere boyunca bekler ve tek geçici hata görevde vazgeçmez (D-389 A1+A2).
- SiK üzerinden: `--serial /dev/ttyUSB0` (UDP adresleri yerine).

## 4. Tekrar fırlatma / reset (§6.2 — süre 15 dk'dan yer)

```bash
<venv> scripts/saha_baslat.py --reset     # yordamı yazdırır
```

Özet: YKS'de R + gerekirse yeniden ARM; İKA süreci ÖLDÜRÜLMEZ (güvenli
duruşta beklemeye devam eder); Jetson yeniden başlatılmaz; kronometre yeni
fırlatmada yeniden damgalanır. Hiçbir adımda araca fiziksel müdahale yok
(hands-off ihlali −100).

## 5. Prova ve kanıt

Her saha provası `simulation/PROVA_SENARYOSU.md` faz damgalarına göre koşulur;
video + hakem_log çıktısı `results/prova/<tarih>/` altına taşınır (UHDR §5.5
kanıtı). Sim koşusu saha kanıtı değildir (CONTRACTS 11.1) — gerçek prova
kayıtları esastır.
