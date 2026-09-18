# ONARIM-19 — Video telemetri: YKİ'nin kaynağı KENDİ BULMASI

**Durum:** YAZILIM HAZIR (kod + 40 test + gerçek akışla uçtan uca koşum) · **donanım sahada DENENMEDİ**
**Tarih:** 18 Eylül 2026
**Kullanıcı isteği:** *"eğer video telemetri bağlayabilirsek güzel olur… kodlama olarak hazırlanması gerek"*
**Kapsam kuralı:** koordinat/rota/komut hattı **radyo telemetrisindedir ve bu iş ona DOKUNMAZ.**
Video bulunamazsa YKİ bugünkü "video kapalı" davranışında kalır; uçuş ve hakem akışı etkilenmez.

---

## 1. Sorun

Zincirin kopuk halkası video değil, **videonun nerede olduğunu bilmek**ti:

| Parça | Durum (18 Eylül, ölçüldü) |
|---|---|
| Jetson işaretli kare yayını (`--isaretli-yayin` → `/kare.jpg`, `/video`) | VAR (ONARIM-06) |
| `scripts/isaretli_gosterici.py` (Jetson ekranı → HDMI → hava birimi) | VAR (x11/drm/rtsp) |
| PC'de RTSP okuma yeteneği | VAR: OpenCV 4.10 `FFMPEG: YES`, `ffprobe` kurulu |
| `scripts/kamera_koprusu.py` RTSP/HTTP → MJPEG | VAR (`kaynagi_coz`: `"://"` → CAP_ANY/FFmpeg) |
| `comms/kamera_istemci.py` | **Yalnız HTTP** `/kare.jpg` + `/durum` okur; RTSP'yi açamaz |
| Kaynağın adresi/portu/yolu | **YOKTU** — sahada elle IP denemek gerekirdi |

Adres önceden bilinemez: SIYI'nin sürümüne, kumandanın USB/tethering kipine, yer biriminde
RJ45 olup olmamasına ve (router yokken) link-local adrese göre değişir.

## 2. Yapılan

**`comms/video_kaynagi.py` (yeni, 560 satır)** — aday tablosu + eleme + seçim:

* **Aday tablosu:** SIYI adresleri (`.25/.20/.11/.12`) × RTSP yolları (`main.264`, `video0`,
  `video1`, `stream=0`, `live`), SIYI FPV UDP (`37256`), kumanda USB/tethering
  (`192.168.42.1/.129`), Jetson HTTP köprüsü (`:8081` işaretli kare, `:8080` ham kamera),
  istenirse yerel yakalama kartı.
* **Sıra:** operatörün verdiği URL → son başarılı kaynak (önbellek) → **keşifle öğrenilen
  Jetson adresi** → aynı ağda görünen SIYI adayları → uzaktakiler → kumanda → Jetson → cihaz.
* **Doğrulama = akan video.** Açık TCP portu yetmez; aday ancak `ffprobe` (yoksa OpenCV)
  gerçek bir video akışı çözünce `CANLI` olur ve kanıtı (çözünürlük, codec, yöntem) taşır.
* **Fail-visible:** her aday için `CANLI / PORT_KAPALI / AKIS_YOK / ARAC_YOK / ATLANDI` + sebep.
* **Yanlış kaynak seçme riski kapalı:** PC'nin kendi web kamerası da `/dev/video0`'dır;
  yerel cihaz adayları **varsayılan olarak taranmaz** (`--cihaz-da` ister).
* **Hız:** aynı `host:port` birden çok yol için bir kez denenir → 25 aday **3,3 s** (ölçüldü).

**`comms/yks_gui.py --video-tara`** — açılışta kaynağı bulur; RTSP/UDP/cihaz ise
`kamera_koprusu`'nu alt süreç olarak başlatıp YKİ'yi `http://127.0.0.1:8090/`'a bağlar,
HTTP kaynağında köprü kurmaz. Bulamazsa **sarı** günlük + video kapalı. Tarama ya da köprü
patlarsa **kırmızı** günlük + video kapalı — hiçbir durumda YKİ düşmez, link nesnesine
dokunulmaz. YKİ kapanırken köprü süreci `atexit` ile bırakılır.

## 3. Kanıt

### 3.1 Testler — `tests/test_onarim19_video_kaynagi.py` **40/40 OK**
Aday üretimi/sıralaması, HTTP kökünün `/video` ucundan doğrulanması, TCP elemesinin akış
denemesini önlemesi, aynı ucun tekrar denenmemesi, ilk CANLI'dan sonra durma, önbellek
(bulamayınca eski kayıt bozulmaz), köprü komutu, YKİ entegrasyonu ve fail-closed yolları.

**Mutasyon kontrolü — 5/5 yakalandı:**

| Mutasyon | Sonuç |
|---|---|
| TCP elemesi kaldırıldı | FAILED |
| HTTP köküne `/video` eklenmiyor | FAILED |
| İlk CANLI'dan sonra durulmuyor | FAILED |
| Keşif adresi önceliği kaldırıldı | FAILED (2) |
| Köprü açılamayınca yine de URL dönüyor (fail-open) | FAILED |

### 3.2 Gerçek akışla uçtan uca koşum (sahte değil)
SIYI donanımı yok; yerine **gerçek bir ağ video akışı** kuruldu (`ffmpeg` → 1280×720 H.264 →
`kamera_koprusu` → HTTP MJPEG) ve zincirin tamamı koşuldu:

```
KEŞİF : elle http://127.0.0.1:8099/  →  CANLI  1280x720 mjpeg (ffprobe)
KÖPRÜ : kamera_koprusu.py --kaynak http://127.0.0.1:8099/video --port 8090
        /durum → kaynak_turu=url · kaynak_acik=True · fps=9.999 · boyut=[1280,720] · son_hata=None
YKİ   : KameraIstemci("http://127.0.0.1:8090/")
        durum=CANLI · kare_yasi_s=0.195 · jpeg=32659 bayt · hata=None
```

Yani: **ağdan gelen canlı video → keşif → köprü → YKİ ekranında gerçek kare.** Sahada
değişecek tek şey kaynağın adresi; yol aynı yoldur.

### 3.3 Genel kapı
`codes/test_rota_sentetik.py` → **GEÇTİ (kol1 15/15 · kol2 şerit 15/15)**.
YKİ/ONARIM/kamera süitleri: 34 dosya koşuldu, **tek kırmızı** `test_yks_mk15_hakem_ekrani.py`
(`H2c ana road3 945x630 kalıntı kesişim 1→0`). Bu kırmızı **bu işten önce de vardı**:
`git worktree` ile `HEAD` (b75b1722) ayrıca koşuldu, aynı tek hata orada da çıktı.

## 4. Sahada kullanım

```bash
# 1) ne bulunuyor, önce bak (hiçbir şeye bağlanmadan aday listesi: --liste)
python comms/video_kaynagi.py --tam
python comms/video_kaynagi.py --kesif-ip 169.254.201.50      # link-local Jetson

# 2) YKİ'yi taramayla aç
python comms/yks_gui.py --tunel 127.0.0.1:14570 --fda --video-tara
python comms/yks_gui.py ... --video-tara --kamera-url rtsp://192.168.144.25:8554/main.264
```

## 5. Sınırlar — DÜRÜST KAYIT

* **UÇUŞTA video Ethernet'ten GİDEMEZ.** Jetson'un WiFi kartı yok, havada kablo da yok.
  Uçuşta video ancak SIYI'nin kendi telsiziyle mümkündür (Jetson HDMI/DP → hava birimi →
  yer birimi → PC). Tablodaki **Jetson HTTP köprüsü adayları yalnız YERDE**, kablo takılıyken
  geçerlidir. Bu kısıt keşfi bozmaz: keşif neyin canlı olduğunu söyler, nerede olduğunu değil.
* **Gerçek SIYI donanımıyla HİÇ denenmedi** (donanım elde değil). RTSP yolu ve adresleri
  üreticinin yayımladığı değerlerden alınmıştır; sahada tutmazsa `--url` ile elle verilen
  kaynak **ilk sırada** denenir ve bir kez bulununca önbelleğe yazılır.
* **Yerel RTSP sunucusu kurulamadı** (`ffmpeg -f rtsp` yalnız istemcidir; RTSP sunucu yazılımı
  yok), bu yüzden RTSP taşıyıcısı yerine **HTTP taşıyıcılı gerçek akış** ölçüldü. İkisi de
  OpenCV/FFmpeg'in aynı yolundan geçer; yine de RTSP **sahada ilk kez sınanacaktır.**
* Video **KANIT**tır, karar üretmez (CONTRACTS §6.8 değişmedi). Hakem onayı ve rota verisi
  telsizdedir; bu modül o hatta hiç dokunmaz.

## 6. Açık işler

| İş | Kim |
|---|---|
| Gerçek SIYI ile tarama (hangi aday CANLI çıkıyor) | saha |
| Yer biriminde RJ45 / kumandada USB var mı — hangi fiziksel yol kullanılacak | insan |
| Uçuşta video isteniyorsa `isaretli_gosterici` kipinin (x11/drm) Jetson'da koşumu | saha |
