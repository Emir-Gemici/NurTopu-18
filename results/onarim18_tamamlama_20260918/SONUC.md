# ONARIM-18 — 18 Eylül 2026 tamamlama kanıtı

Kullanıcı: “madem sen yaptın sen bitir işini”. Yazan: Codex-1.
Bu çalışma üreticinin doğrulamasıdır; bağımsız onay veya görev kapatma değildir.
Başlangıç HEAD: a967ace6. ONARIM-18 üretim düzeltmeleri bu commit içinde zaten
vardı; Jetson paketindeki iki eş kopya ve 17 Eylül devir kayıtları commit dışındaydı.
Bu tur üretim mantığı değiştirilmedi; eksik çalışma kanıtları tamamlandı.

Yorumlayıcı: `/home/trs/projects/navitas-unified-20260822/.venv/bin/python`.
Komutlarda `PY` bunun tam yoludur. Testler bu Linux PC'de çalıştı.

## Doğrulanan davranışlar

- İki yayıncı aynı `node=iha` kullansa da ayrı süreç/akış kimlikleri sayesinde
  birbirinin sıra sayacını bastırmıyor. Salt canlılık mesajı koordinatı silmiyor.
- Telemetri üreticisi ölünce diğer heartbeat'ler eski GNSS/ARM durumunu canlı
  tutmuyor. Telemetri mevcut 2,5 saniyelik sınırda temizleniyor.
- Yeniden başlayan üreticinin yeni akış kimliği ve baştan başlayan sayacı
  telemetriyi tekrar görünür kılıyor.
- İniş yayıncısı önce aynı kaynaktan kalkış kanıtı bekliyor; yerde açılış iniş
  sayılmıyor. İniş timeout'u kalkış kanıtından sonra başlıyor.

## Komutlar ve gerçek çıktılar

`$PY -B results/onarim18_tamamlama_20260918/dogrula.py` hedefli grubu, iki
mutasyon koşumunu, genel kapıyı ve tam süiti sırayla çalıştırır. Alt komutların
**tam argv ve exit kodları** `kapilar.json` içindedir. Grup adları betikte açıkça
listelidir; yinelenen modül yoktur.

| Koşum | Gerçek çıktı | Exit |
|---|---|---|
| Hedefli protokol/iniş/telemetri/paket/dayanıklılık grubu | `Ran 186 tests in 29.816s` / `OK` | 0 |
| Heartbeat mutasyonları | `MUTASYON: 4/4 yakalandi` | 0 |
| Kalkış mutasyonları | `MUTASYON: 4/4 yakalandi` | 0 |
| `codes/test_rota_sentetik.py` | `GENEL KAPI (madde 14): GECTI — kol1 15/15 · kol2 serit 15/15` | 0 |
| `-B -m unittest discover -s tests -p 'test_yks*.py'` | `Ran 236 tests in 31.476s` / `FAILED (failures=1)` | 1 |

Geniş YKS tek hatası H2c ölçek 1,5: `ana road3 945x630: KALINTI KESİŞİM SAYISI
DEĞİŞTİ (beklenen 1, ölçülen 0)`. Test Windows'ta kaydedilmiş eski metin
kesişimini birebir bekliyor; burada kesişim yok. Bu tur kabul ölçütü değiştirilmedi.
17 Eylül raporundaki b75b1722 taban ölçümü ve REVIEW_LOG D-503 aynı hatayı kaydediyor.

### Gerçek ArduCopter SITL (Jetson olmadan)

Komut: `$PY -B results/onarim18_tamamlama_20260918/sitl_dogrula.py` → **exit 0**.
Yerel mevcut ArduCopter ikilisi, ayrı geçici çalışma dizini, instance 10,
loopback TCP 5860 ve efemer UDP portları. Diğer SITL/servislere dokunulmadı.

Ölçülen akış (`sitl.log`, `sitl_sonuc.json`, `sitl_yayinci.log`):

- 9,977 s: yerde, GPS fix 6, armed=false.
- 17,981 s: yerde bekleme tamam; **IHA_LANDED yok**, yayıncı çalışıyor.
- 49,460 s: IN_AIR, bağıl irtifa **3,059 m**; hâlâ iniş mesajı yok.
- 57,438 s: ON_GROUND.
- 58,452 s: **IHA_LANDED seq=1**, bağıl irtifa **0,044 m**.
- 58,529 s: ACK alan yayıncı **exit 0**; `SITL_PASS packets=1`.

İlk koşu ARM reddiyle exit 1 oldu; `sitl_ilk_kosu/` altında korundu. İkinci koşu
STATUSTEXT'i kaydeder: `Arm: Need Position Estimate`; EKF konum kestirimi
hazır olunca ARM kabul edilir. Bekleme boyunca yanlış iniş yayını olmadı.
Yalnız izole simülasyonda ARMING_CHECK=0 ve FS_GCS_ENABLE=0 kullanıldı; bu
koşum uçuşa hazırlık/failsafe parametre kabulü değildir. ACK ucunu ölçüm betiği
oynar; gerçek İKA alıcısı+latch yolu ayrıca hedefli gruptaki mevcut UDP testinde
geçmiştir. Fiziksel Pixhawk, Jetson, telsiz veya gerçek uçuş doğrulanmış sayılmaz.

### Gerçek süreç öldürme / UDP / 10 saniye kesinti

Komut: `$PY -B results/onarim18_tamamlama_20260918/udp_kesinti_dogrula.py`
→ **exit 0**. Ham kanıt: `udp_kesinti.log`, `udp_sonuc.json`.

İki ayrı süreç gerçek `protocol.heartbeat` ile UDP yayınlar. YKS üretim
mesaj işleyicisi ve yaşlandırma kodu kullanılır; yalnız Tk widget'ları fikstürdür.
Telemetri süreci kill ile öldürülür, sağlık yayını **10 saniye** devam eder:
koordinat `{}`, ARM `null`, bağlantı heartbeat'i tazedir. Yeni süreç başlatılınca
**1 saniyelik gözlemde** koordinat/ARM geri gelir; akış kimliği değişmiştir,
sağlık yayıncısı değişmemiştir, sıra reddi sayısı **0**. Üç assertion aşaması PASS.
Bu, R1/R4'ün yerel yazılım karşılığıdır; systemd yeniden başlatması ve radyo
kesintisi testi değildir.

## Paket ve kalan saha sınırı

İki paket dosyası kaynakla SHA-256 eş:

- `iha_inis_yayinci.py`: `7a1d341ad13d570c8922d0afaea66880e23f3b8e93f8ed36a5d3b9456114859e`
- `protocol.py`: `08c4dbe9937e4db4f8d6eb8deaf43a9f11ecdb6c377784872e616d53f6c299d5`

26 paket kopyasının testi hedefli grupta geçti. Devirdeki Jetson
`10.21.8.7:22` için salt TCP erişim denemesi **timed out** (`jetson_erisim.json`).
Bu nedenle canlı aktarım, servis restart'ı ve R1–R5 Jetson/saha kabulü yapılamadı.
YKS ve iki Jetson yayıncısı birlikte güncellenmeli. CONTRACTS önerisi önceki
SONUC.md'de; bu belgeye yazma yetkisi mimardadır. Bağımsız denetim bekliyor.

## Sistemi okumak

Pixhawk uçuş durumunu ve konumu üretir. MAVProxy aynı akışı model/telemetri,
iniş kanıtı ve komut süreçlerine dağıtır. Hub bunları YKS'ye taşır.

**Bağlantı canlılığı**, **telemetri tazeliği** ve **iniş kanıtı** üç ayrı şeydir.
Diğer süreç haber veriyor diye modelin eski konumu taze olmaz. İHA yerde
çalıştırıldı diye uçuş tamamlanmış sayılmaz. İKA sürüşü de yalnız iniş mesajına
bağlı değildir; rota ve hakemin IKA_GO koşulu ayrıca gereklidir.

## Tam depo süiti — kırmızı

Komut: `$PY -B -m unittest discover -s tests -v`.
Gerçek çıktı: `Ran 3010 tests in 498.792s`;
`FAILED (failures=42, errors=10, skipped=34)`; **exit 1**.
Ham izler `tam_suit.log`, bütün 52 hata/başarısızlık başlığı
`tam_suit_bulgulari.txt` içindedir. Alt-testler nedeniyle bu 52 sayısı
52 ayrı test yöntemi anlamına gelmez.

Bulgular: FDR/atölye/akış diyagramı satır atıfları, REVIEW_LOG ileri işaretleri,
depo kökü keşfi, model kayıt defteri, simülasyon API uyumsuzluğu, eksik trimesh,
eksik model ve görüntü fikstürleri, simülasyon SHA/PNG eşliği, T155 waypoint
referansları, Jetson ONNX paket beyanı ve yukarıdaki YKS görsel beklentisi.

**Bunların tümüne “önceden vardı” denmiyor:** ONARIM-18 öncesi tam süit bu tur
çalıştırılmadı. Özellikle iha_inis_yayinci/YKS satır kaymalarına bağlı FDR atıfları
bu düzeltmelerin belge entegrasyon borcu olabilir. Eşikler/bayt-eşliği ölçütleri
gevşetilmedi, model/simülasyon veya mimar belgeleri değiştirilmedi.

A görevi önceki gibi açık bırakıldı; B'nin hedefli kapıları yeşil ve bağımsız
denetime hazır durumu korundu. Hiçbir görev [x] yapılmadı. Tam süit yeşil
olmadığından teslim yayımlanmadı; commit/push yapılmadı. Gerçek Jetson saha
ölçümü ve bağımsız denetim tamamlanmış sayılmaz.
