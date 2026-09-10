# MK15 VİDEO HATTI — TASARIM VE ÖN KAYIT (T225 → T226–T229, D-443)

> **Tarih:** 10 Eylül 2026 · **Mimar:** bu oturum · **Girdi:** kullanıcı (D-442, D-442 ek): SIYI MK15 "3 in 1"
> + Air Unit Mini + SIYI HDMI→Ethernet (HDMI giriş) dönüştürücü; kamera Raspberry Pi HQ + 6 mm.
> **Araştırma:** iş akışı `mk15-entegrasyon` (wf_9591eb9d; 4 rapor: SIYI resmi, topluluk, kod haritası,
> şartname) + `mk15-bosluk` (wf_2d31e42f; DP→HDMI, ekransız gösterim, Air Unit Mini, dönüştürücü — sonucu §5'e işlenir).
> Kural: ÖLÇÜLEMEDİ ≠ GEÇTİ; eşikler aşağıda önceden yazılı; gevşetilmez.

## 0. Kaynaklı gerçekler

| konu | gerçek | kaynak |
|---|---|---|
| Şartname | Canlı video ne zorunlu ne puanlı. Zorunlu olan: güzergâh verisi YKS'ye gerçek zamanlı + hakem monitörden izler + sözlü onay; gösterim biçimi serbest. **Veri** akışı koparsa uçuş geçersiz, video koparsa değil. | ŞART §2.2.3 (`results/sartname_bosluk/sartname_metin.txt:296-303`), §6.2 (:967-970), §6.4 (:1005-1008), §5.3.2 (:732-745) |
| MK15 kumanda HDMI | Ekranın **aynası** (SIYI FPV + OSD + Android arayüzü); ham akış değil. **Yalnız Enterprise** sürümde. Çözünürlük/kare hızı belgelenmemiş. | SIYI MK15 kılavuz v1.9 (res.siyi.biz, 2026.7); SIYI forum 2024-08-27 "it mirrors the screen only" |
| Hava birimi | Ethernet'ten standart RTSP (H.264/H.265) girişi, LAN&PWR GH1.25 8 pin; sabit IP'ler **.11 hava / .12 yer / .20 Android** (değişmez); 3. taraf cihaz 192.168.144.X, X ∉ {11,12,20}. Hat 8 Mbps aşağı. | kılavuz v1.9, SSS |
| HDMI giriş dönüştürücü | varsayılan **192.168.144.25**, `rtsp://192.168.144.25:8554/main.264`, H.264 1080p30, **12 V / 3 W**; IP web arayüzünden değişir. | SIYI dönüştürücü kılavuzu v1.1 (res.siyi.biz), manuals.plus |
| Jetson kodlayıcı | **Orin Nano'da NVENC yok** → RTSP yazılımla (x264) kodlanır; dönüştürücü yolu kodlamayı donanıma devreder. | NVIDIA Jetson Linux r36.2 "Software Encode in Orin Nano" |
| Gecikme | Üretici 130–250 ms (QGC, H.265; ölçüm değil); USB yakalama +49–85 ms (MS2130 / MS2109 ölçümleri). Uçtan uca MK15+HDMI+yakalama ölçümü yok. | kılavuz v1.1; HyperHDR testleri |
| Telemetri | MK15 datalink MAVLink; şeffaf seri hat belgelenmemiş → **NAVITAS çerçeveleri ve hakem ACK'ı SiK'te kalır.** | kılavuz v1.9 |
| Frekans | Şartnamede kural yok. BTK muafiyet: 5725–5875 MHz **25 mW e.i.r.p.**; 2400–2483,5 MHz 100 mW + LBT/DAA. MK15 bandı/gücü kaynaklarda çelişkili (2021 SIYI: 5,8 GHz, 27 dBm). → **BEYAN** (cihazın Link Status sayfasından okunur), DDK'ya sorulur. | BTK "Frekans Tahsisinden Muaf Telsiz Cihaz ve Sistemlerine İlişkin Teknik Ölçütler" |
| Güç | MK15 hava birimi 14,8–58,8 V (4S–14S, bayi) — Air Unit Mini ayrıca doğrulanacak; 6 Eylül tlog'unda yük altında 9,35–11,28 V okundu (PM06 doğruluğu şüpheli, D-440) → **kararma riski**; dönüştürücüye 12 V BEC. | bayi sayfası; D-440 |
| YKS video (ölçüldü) | YKS yalnız HTTP kabul eder. `kamera_koprusu.py --kaynak 0` Windows'ta web kamerasıyla uçtan uca **CANLI**, köprü kapanınca KARE_BAYAT → **kod değişmeden** yakalama kartı yolu kurulabilir. İndeks kaynağında çözünürlük/FPS/arka uç seçilemiyor. **Video ve şematik harita aynı anda görünmüyor** (pack_forget). | harita `kod-harita` (kamera_istemci.py:75-76, yks_gui.py:2512-2543, kamera_koprusu.py:153) |
| Jetson işaretli kare (ölçüldü) | Saha kipi `--camera --ekransiz` hiç görsel üretmez; ağa işaretli kare çıkışı yok; bindirmede şerit adı ve seq yok; bindirme **eşiklenmiş kare kararından** çizilir, yayın `KararYumusatici.suz`'dan geçer → bindirme henüz yayınlanmamış şeridi gösterebilir. | rpi_inference.py:2402-2419, :856-865, :2399-2401 |

## 1. Mimari (karar)

**Veri hattı (DEĞİŞMEZ, şartname dayanağı):** Jetson `rpi_inference` → SiK 433 MHz → YKS `OPEN_ROUTE` → hakem
iki aşama → ACK SiK'ten İHA'ya. Hakem onayı **yalnız bu veriye** verilir (CONTRACTS §6.7 değişmez).

**Video hattı (YENİ, görsel kanıt, karar üretmez):**
1. RPi HQ (CSI) → Jetson `rpi_inference` → **yayınlanmış karar** bindirmeli 1280×720 kare (≤ 2 Hz):
   kamera görüntüsü + geçilebilir/engel maskesi + rota + büyük etiket "SEÇİLEN ROTA: 2 · ORTA" + güven + seq +
   UTC saat + "ROTA YOK — sebep" durumu → yerel HTTP `127.0.0.1:8081` (`/kare.jpg`, `/video`, `/durum`).
2. `isaretli_gosterici` (Jetson) → tam ekran DP → DP→HDMI → **SIYI HDMI giriş dönüştürücü** (.25, H.264).
3. Air Unit Mini → RF → MK15 kumanda: SIYI FPV "Camera 1" tam ekran (OSD kapalı, bildirimler sessiz).
4. Kumanda HDMI (ayna) → **USB HDMI yakalama kartı** (UVC; MS2130 tercih) → YKS PC.
5. `kamera_koprusu.py --kaynak <indeks>` → `yks_gui --kamera-url http://127.0.0.1:8080` → hakem ekranı:
   **video + rota paneli aynı anda**; video panelinde kaynak etiketi "MK15 · HDMI · yakalama — karar üretmez".

**Yedek video yolu:** dönüştürücü/DP yolu çalışmazsa Jetson yazılım x264 1280×720 5 fps RTSP → hava birimine
doğrudan (Jetson IP 192.168.144.30, `rtsp://192.168.144.30:8554/isaretli`; hava birimi portu dönüştürücüdeyse anahtar gerekir).

**Yapılmayacaklar:** SiK'i MK15 datalink'i ile değiştirmek (ölçülmeden yok); FS-i6'yı MK15 RC ile değiştirmek
(ayrı karar; failsafe yeniden ölçülmeden yok); hotspot üzerinden PC'ye IP (menzili düşürür, SIYI önermiyor).

## 2. İşler

| iş | kapsam | kapı (ölçüm/test) |
|---|---|---|
| **T226** YKS hakem ekranı | (a) kamera görünümünde rota paneli + küçük şematik harita görünür kalır (video ve karar aynı anda); (b) video paneli başlığında kaynak etiketi ve "karar üretmez" notu; (c) `kamera_koprusu --kaynak <indeks>` için `--genislik/--yukseklik/--kamera-fps/--arka-uc {dshow,msmf}` (Windows yakalama kartı 1280×720/1920×1080); (d) KAMERA_KANIT `kaynak` alanında MK15 etiketi | yeni testler + web kamerasıyla uçtan uca (köprü → YKS CANLI, kapatınca BAYAT, onay düğmeleri video olmadan çalışır); test_yks_* tam; akış d tazelenir |
| **T227** Jetson işaretli yayın | `rpi_inference --isaretli-yayin 127.0.0.1:8081`: bindirme **yayınlanan** karardan (KararYumusatici çıktısı), 1280×720 16:9, ayrı iplikte JPEG ≤ 2 Hz; sunucu `kamera_koprusu`'nun HTTP sunucusunu yeniden kullanır (yeni sunucu yazılmaz); `--ekransiz` ile uyumlu | birim testler (karar→etiket, NO_ROUTE, eşik-altı kare yayınlanmış şeridi değiştirmez — mutasyon), HTTP uçları, **FPS etkisi ≤ %5** (PC, dosya kaynağı, 3 koşu, ön/son), akış a/c tazelenir, jetson_paket aynası |
| **T228** Jetson gösterici + yedek RTSP | `scripts/isaretli_gosterici.py` tam ekran (yöntem §5 araştırma sonucuna göre: nvdrmvideosink/kmssink ya da X kiosk), systemd birimi, `jetson_baslat.sh` bağlantısı; yedek `--rtsp` x264 720p 5 fps | PC'de boru dizgisi birim testleri + kuru koşu; x264 CPU yükü PC'de ölçülür; Jetson'da **İNSAN** |
| **T229** belgeler (yazılım kapsamı) | SAHA_RUNBOOK video bölümü (IP planı, 15 dk hazırlık, kurulum sırası), CONTRACTS §6.8 KAMERA_KANIT kaynak, FDR §3.3.1.1.13 kamera köprüsü, §3.3.4.3 video satırı (bit hızı/gecikme ÖLÇÜLEMEDİ), §4.9 video kopması testi, İHA bağlantı şemasına MK15 hatları (DOĞRULANACAK, kesik) | test_fdr*, test_gece*, şema nöbetçisi |

## 3. Saha (İNSAN) — T225 kâğıdına girer
1. Kumandada HDMI portu var mı (Enterprise); Air Unit Mini etiketi (gerilim aralığı).
2. Güç: hava birimi besleme yolu + dönüştürücü için 12 V BEC; yük altında gerilim ölçümü.
3. Bant/güç: MK15 Link Status sayfasından okunur; BTK sınırıyla karşılaştırılır; DDK'ya frekans sorusu.
4. Camdan cama gecikme: Jetson ekranında kronometre → YKS ekranı birlikte filme alınır (5 ölçüm, p50/maks).
5. Kurulum provası: YKS + kumanda + HDMI + yakalama kartı + köprü ≤ 15 dk hazırlık içinde.

**Kullanıcı cevapları (10 Eylül 15:3x, D-443 ek):**
- 1–2: cevap "SIYI Air Unit HDMI Girişinden Ethernet Çıkışına Dönüştürücü" — dönüştürücü **İHA tarafıdır**; kumandanın HDMI çıkışı ve PC'deki USB HDMI yakalama kartı sorusu **AÇIK** (mimar yeniden sordu).
- 3: mini HDMI → HDMI kablo var. Orin Nano DevKit'te HDMI yok, **DisplayPort** var → DP→HDMI adaptörü yine gerekli; mini HDMI ucu büyük olasılıkla dönüştürücü girişine gider (konektör doğrulanacak).
- 4: İHA'da Jetson için **12,2 V dönüştürücü** var → HDMI giriş dönüştürücüsü (12 V / 3 W) aynı hattan beslenebilir; regülatörün akım kapasitesi BEYAN GEREKLİ. Hava birimi beslemesi Air Unit Mini aralığına göre.
- 5: MK15 **5,8 GHz**; telemetri **SiK 433 MHz** (değişmez). BTK 5,8 GHz muafiyeti 25 mW e.i.r.p. riski açık — güç Link Status'tan okunacak.
- 6: IP ayarları sahada birlikte yapılacak.

## 4. Eşikler (ön kayıt)
- YKS: video ve rota paneli aynı ekranda — test ile EVET.
- Video koptuğunda veri hattı ve onay akışı etkilenmez — test ile EVET.
- Jetson FPS düşüşü ≤ %5 (PC ölçümü); Jetson'da ölçülene kadar ÖLÇÜLEMEDİ.
- Camdan cama gecikme ≤ 1,0 s (hakemin eşzamanlı görmesi için) — sahada ölçülür; ölçülmezse ÖLÇÜLEMEDİ.

## 5. Boşluk araştırması sonuçları (mk15-bosluk, wf_2d31e42f; doğrulayıcı 7/7 + 3 rastgele iddia, çürütülen yok)

| konu | sonuç | güven / kaynak |
|---|---|---|
| Jetson ekran çıkışı | DevKit'in tek çıkışı **DisplayPort**; **pasif ve aktif** DP→HDMI adaptör resmi olarak destekli (DP++ pin 13). Zincir: Jetson DP → DP(erkek)→HDMI(dişi) adaptör → kullanıcının mini HDMI↔HDMI kablosu → dönüştürücü. | YÜKSEK — docs.nvidia.com Orin Nano devkit hardware_layout; NVIDIA forum 249839 |
| Ekransız tam ekran | Belgeli yol **nvdrmvideosink** (gdm durdur + `modprobe nvidia-drm modeset=1`); NVIDIA JP 6.2 + IMX477 ile 30 fps doğruladı. **Uyarı:** DRM açılıp kullanılmazsa Argus 3 fps'e düşüyor; JetPack 7.2'de nvidia-drm varsayılan denylist'te (nv-load-display-modules). **Karar:** birincil yol varsayılan X11 masaüstü oturumu + otomatik oturum + tam ekran pencere (gdm kapanmaz, Argus riski yok); DRM yolu ikinci seçenek; kmssink kaynaksız → kullanılmaz. | YÜKSEK — R39.2 Accelerated GStreamer; forum 331128, 345587 |
| EDID/HPD | Dönüştürücünün EDID/HPD davranışı ve kabul ettiği giriş çözünürlükleri **belgesiz** → tezgâhta denenir; X yolunda EDID yoksa sahte xorg (dummy, IgnoreEDID, 1280×720) yedeği. | KAYNAK YOK / ORTA — forum 263892 |
| Dönüştürücü | Giriş **Mini HDMI** (kılavuz V1.1; v1.9 "Micro HDMI" diyor — çelişki), 12 V / 3 W; çıkış konnektöründe **12V pini** var, hava biriminin LAN&PWR portunda da 12V pini var → besleme büyük olasılıkla **hava biriminden aynı kabloyla** (çıkarım); IP web arayüzünden değil **SD karttaki setip.txt** ile değişir; varsayılan .25; canlı codec H.264/H.265 çelişkili. | YÜKSEK/ORTA — SIYI dönüştürücü kılavuzu V1.1 |
| Hava birimi | "Air Unit Mini" adında SIYI ürünü **yok**. Eldeki birim ya **MK15 Air Unit** (100 g, 1× LAN&PWR, **16,8–75,6 V = 4S–18S**, 2024 öncesi lotlar 6S–14S) ya **HM30 Air Unit** (74 g, 2× LAN&PWR, 12,6–25,2 V = 3S–6S, 2024 öncesi 3S–4S). **Risk:** MK15 Air Unit'in alt sınırı 4S'in DOLU gerilimi; yük altında kararabilir → ağırlık/port sayısı/etiketle birim belirlenir; MK15 Air Unit ise besleme yolu yeniden düşünülür. | YÜKSEK — MK15 kılavuz v1.9 s.21/s.24, SSS |
| Kumanda HDMI | Yalnız **Enterprise**; dönüştürücü resmi olarak "Enterprise HDMI Combo" ile gelir. SIYI FPV'de OSD/Mavlink OSD/harita/artı kapatılabilir; tam ekran ve bildirim gizleme belgesiz. | YÜKSEK — kılavuz v1.9, SSS |
| Frekans/güç | FCC 2AZBB-MK15TX: **5745–5825 MHz, 68,1 mW iletilen** → 5 dBi antenle ≈214 mW e.i.r.p. (HESAP) — BTK genel KET sınırı **25 mW e.i.r.p.** (Tablo 1 satır 26) ≈9 dB aşılıyor (FCC sürümü için; CE/TR gücü bilinmiyor). Şartnamede frekans kuralı yok → organizasyona sorulmalı. | YÜKSEK — FCC (Wayback), BTK ftm-teknik-olcutler-ek-5 |
| Yazılım kodlama | Orin Nano x264: 30 fps kamera, ultrafast %19–38 çekirdek başı (NVIDIA R39.2 tablosu); 720p 5 fps yükü bunun altında olmalı — Jetson'da ölçülür. | YÜKSEK — R39.2 SoftwareEncodeInOrinNano |
| 🔴 HQ kamera + JetPack 7.2.1 | Orin Nano'da R8 direnci için NVIDIA'dan kesin "gerekli" yok (koşullu). **Asıl risk:** JetPack 7.2 IMX477 sürücüsü — Arducam: NITO ISP dosyası eksik, beta sürücü 39.2.0'a bağlı, 39.2.1'de bağımlılık hatası; kullanıcı raporları: reset GPIO PH.06 düşük kalma, INVALID_SETTINGS. Stok sürücüyle 7.2.1'de başarılı IMX477 raporu bulunamadı. → **12 Eylül ilk test**; yedek: USB UVC kamera (`kamera_koprusu --kaynak <indeks>`, FOV 41–69°). | ORTA — forum.arducam.com 9297; NVIDIA forum 379028 |
| Gösterici uygulaması (T228, D-447) | `scripts/isaretli_gosterici.py` master'da: `--kip x11` varsayılan (tam ekran, 5 Hz, kare yaşı > 2 s BAYAT, > 5 s / 503 / erişilemez GÖRÜNTÜ YOK), `--kip drm` seçenek (nvdrmvideosink + gözetmen; donmuş boru takibi T228-D), `--kip rtsp` yedek (x264, `rtsp://<.30>:8554/isaretli`); `jetson_baslat` `GOSTERICI_KIP` varsayılan kapalı, T227 yoksa fail-closed. PC dumanı: 4 senaryo (CANLI/BAYAT/503/köprü yok). **Jetson'da hiçbir kip ÖLÇÜLEMEDİ** → 12 Eylül, `jetson_paket/gosterici/GOSTERICI_KURULUM.md` §4. | ÖLÇÜM (PC) — `results/fdr_sprint_20260910/H9_MK15/t228/` |
