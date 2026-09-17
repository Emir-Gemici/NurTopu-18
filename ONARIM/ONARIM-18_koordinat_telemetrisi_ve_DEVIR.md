# ONARIM-18 — Koordinat telemetrisi uçtan uca testi (SITL) + CODEX DEVRİ

**Durum:** TEST YAPILDI · **2 KUSUR BULUNDU, DÜZELTİLMEDİ** (kullanıcı kotası bitti → Codex'e devir)
**Tarih:** 17 Eylül 2026 ~17:40 · Kullanıcı isteği: *"kordinat ile bağlanmayı test et, hataları ayıkla gider, sistemin patlamasına karşı güçlü olsun, sonra bana eğit öğret"*

## Codex için okuma sırası (TÜMÜNÜ değil, yalnız bunlar)
1. Bu dosya.
2. `ONARIM/ONARIM-00_LISTE.md` (madde durumları).
3. Kod: `comms/yks_gui.py` `_heartbeat_sirasi_gecerli` (~satır 1877) ve `elif tip == MESAJ_HEARTBEAT:` bloğu (~2086–2140) · `comms/protocol.py` `heartbeat()` (126) · `comms/iha_inis_yayinci.py` `main()` (467–560) · `comms/inis_kaniti.py` `_yerde_mi_sahipli` (937).
4. Bağlam gerekirse: `ONARIM-09_yks_coklu_hat.md`, `ONARIM-03b_yks_kesfi.md`, `ONARIM-10_jetson_paket_senkronu.md` §4–5.
Kurallar: `CLAUDE.md` (commit yazarı `trs-1342`, AI atfı YASAK; genel kapı `codes/test_rota_sentetik.py` 15/15; OpenCV/NumPy/heapq).

## Test düzeni (tekrar kurmak için)
- PC: ArduCopter **4.5.7 SITL** `~/projects/navitas_sitl/arducopter` (firmware.ardupilot.org, sha256 `b9035c08f003ab29…`) — `./arducopter -S --model + --speedup 1 --defaults copter.parm -I0 --home 40.9599799,29.1335529,20,0` (TCP 5760).
- PC köprü: `scripts/tezgah/mavlink_tcp_udp_kopru.py --jetson 10.21.8.7:14560` (`--kes-bas/--kes-sure` hat kopması testi için).
- Jetson: `sudo systemctl stop navitas-cogullayici` → elle `mavproxy.py --master=udpin:0.0.0.0:14560 --streamrate 8 --out udp:127.0.0.1:14550 --out …14551 --out …14552 --daemon --non-interactive`. **Bitince** manuel MAVProxy'yi PID ile öldür (⚠ `pkill -f`/`pgrep -f` desenleri SSH kabuğunun kendisini de eşler), `systemctl reset-failed && start navitas-cogullayici`.
- PC YKS yerine: `scripts/tezgah/yks_telemetri_dinle.py --sure 40 --jsonl …` (eşleşme duyurusu yapar, 5005 dinler, `--komut RTL@20` gönderebilir).

## Ölçülen (KESİN)
- MAVProxy SITL'e bağlandı: `Received 1389 parameters`, `GPS 1: detected as u-blox`.
- **Koordinat telemetrisi uçtan uca ÇALIŞIYOR:** `rpi_inference` heartbeat'i (1 Hz) YKS'ye: `lat 40.9599798, lon 29.133553, gps_fix 6, uydu 10, bat 12.6, mod STABILIZE, armed false, pixhawk_canli true, alt -0.027`. Yol: SITL → köprü → Jetson MAVProxy → 14550 okuyucu → hub → LAN (keşifle bulunan YKS 10.21.8.156:5005).
- Görev kaydı (`gorev_kaydi.jsonl`) `pixhawk_ms`, `irtifa_m`, `armed`, `mod` dolu.

## 🔴 KUSUR 1 — heartbeat çakışması: YKS koordinatları kalıcı kaybedebilir
- İki süreç **aynı `node="iha"`** ile heartbeat yollar: `rpi_inference` (1 Hz, telemetrili, seq ~11954) ve `iha_inis_yayinci` (iniş sonrası ~2 Hz, **telemetrisiz**, seq ~350). Ölçüm: 12 s'de 13 telemetrili + 24 boş heartbeat.
- YKS `_heartbeat_sirasi_gecerli` seq'i **yalnız node başına** tutar (`seq <= onceki` ve 3 s tazelikteyse RED). YKS heartbeat'i **snapshot** sayar: kabul edilen boş heartbeat `self.tel["iha"] = {}` yapar ve `arm_acik`'i bilinmez kılar.
- Senaryo: `rpi_inference` yeniden başlarsa (OOM/çökme; systemd kaldırır) seq'i 1'den başlar < inis seq → rpi'nin koordinatlı heartbeat'leri **inis yaşadıkça sürekli reddedilir** → YKS koordinat/arm/batarya göstermez. Ters sırada boş heartbeat'ler telemetriyi siler.
- **Önerilen düzeltme (uygulanmadı):** `protocol.heartbeat` her süreç için rastgele **`akis`** kimliği eklesin; YKS (ve İKA alıcısı, kontrol et) seq sırasını **(node, akis)** başına tutsun; hiç telemetri alanı taşımamış bir akıştan gelen heartbeat yalnız canlılığı (`son_hb`) güncellesin, `tel`/`arm`'ı SİLMESİN (telemetri akışının boş snapshot'ı ise GNSS kaybı güvenliği için silmeye devam etsin). CONTRACTS heartbeat bölümü + `tests/test_yks_mk15_hakem_ekrani.py` ön kayıtlı metinler + heartbeat testleri (15 dosya `heartbeat(` kullanıyor) güncellenmeli. Test: iki akış, rpi yeniden başlatma simülasyonu → telemetri kaybolmamalı.

## 🔴 KUSUR 2 — İHA uçmadan IHA_LANDED yayınlanıyor (otomatik başlatmayla güvenlik riski)
- `iha_inis_yayinci` açılınca `yerde_mi` (ON_GROUND + irtifa < 1 m, 3 ardışık) doğrulanır; **önce uçuş görülmüş olma şartı YOK**. ONARIM-10'da servisler açılışta otomatik başladığı için drone yerdeyken Jetson açılınca **IHA_LANDED hemen yayınlanır** (SITL'de görüldü: `IHA_LANDED ACK eksik: seq=1`). İKA iniş kapısını açabilir (IKA_GO ayrıca hakem tetiklemesi ister, yine de kanıt zinciri yanlış).
- Ek: `--kanit-timeout 900` açılıştan sayılır; kalkış olmazsa 15 dk'da çıkış kodu 3 → systemd yeniden başlatır (bugün **NRestarts=6**; koruma drop-in'i beklemeyi 60 s'ye kadar büyütür).
- **Önerilen düzeltme (uygulanmadı):** `main()` önce **kalkış kanıtı** beklesin (beklenen sysid'den `EXTENDED_SYS_STATE.landed_state` IN_AIR/TAKEOFF ya da armed + bağıl irtifa > eşik); kalkış görülene dek süresiz bekle (çıkma), `--kanit-timeout` kalkış anından başlasın; sonra mevcut `yerde_mi` aynen. `inis_kaniti.yerde_mi` DEĞİŞMEZ (belge kuralı). Test: yerde başlayan akışta IHA_LANDED YOK; IN_AIR → ON_GROUND akışında VAR; timeout kalkıştan sayılır. SITL ile doğrulanabilir (arm + takeoff komutu MAVLink ile).

## Henüz yapılmayan dayanıklılık testleri (plan)
R1 köprüyü 10 s kes (`--kes-bas 15 --kes-sure 10`) → YKS BAYAT, dönünce TAZE · R2 `systemctl restart navitas-seri-hub` akış sırasında · R3 5009/5010'a bozuk UDP seli → hub yaşar · R4 `kill -9` rpi_inference → systemd kaldırır, telemetri geri gelir (**Kusur 1 düzelmeden başarısız olması beklenir**) · R5 YKS duyurusu durunca Jetson davranışı.

## Gerçek Pixhawk / GPS (ayrı)
Pixhawk PC USB'de; iki GPS modülü algılanmıyor, buzzer çok kısık → GPS1 portu 5V beslemesi yetersiz/arızalı şüphesi (ONARIM-15). Kalıcı port izni için kullanıcı şu komutu çalıştırmadı: `echo 'SUBSYSTEM=="tty", ATTRS{idVendor}=="3162", MODE="0666"' | sudo tee /etc/udev/rules/99-pixhawk.rules && sudo udevadm control --reload-rules && sudo udevadm trigger`.

## Jetson son durum (17:45)
6 servis active (`KIP=ikili`, `YKS_ESLESME`); manuel test MAVProxy kapatıldı, `navitas-cogullayici` yeniden `/dev/ttyTHS1` (Pixhawk bağlı değil → "Waiting for heartbeat", beklenen). Sudo parolası hiçbir dosyada yok; kullanıcıdan istenmeli.

## Kullanıcıya "eğit öğret" (yapılmadı)
Kullanıcı sistemin nasıl çalıştığını öğrenmek istedi; kusurlar giderildikten sonra kısa bir anlatım: Pixhawk → MAVProxy çoğullayıcı → rpi_inference (model + telemetri heartbeat) / iha_inis_yayinci (iniş kanıtı) / iha_komut_alici (komut) → seri_hub (SiK + LAN aynası) → YKS (keşif, çoklu hat, hakem kaydı).
