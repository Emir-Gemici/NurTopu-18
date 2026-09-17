# LOG-DURUMU.md — 17 Eylül 2026 düşüş sonrası Jetson log incelemesi (tam oturum kaydı)

**Amaç:** Bu dosya, 2026-09-17 tarihli Jetson oturumunda konuşulan, sorulan, cevaplanan ve yapılan **her şeyin** birebir kaydıdır. Başka bir AI (mimar/ana AI) bu oturumu denetleyecek — bu yüzden özetlenmiş sonuç yerine, sorulan her soru + verilen her cevap + çalıştırılan komutlar + değiştirilen dosyalar sırayla yazıldı.

**Kim yazdı:** Claude (bu Jetson'da çalışan oturum), kullanıcı `n4vitas` için.
**Ortam:** Jetson Orin Nano 4GB, JetPack 7.2.1, kullanıcı `n4vitas`. Proje ağaçları hakkında bkz. `CLAUDE.md` başındaki not / hafıza `navitas-jetson-proje`.
**Bağlantılı belge:** `~/proje/NAVITAS_JETSON_20260906/JETSON_DUSUS_LOG_INCELEME_20260917.md` (asıl bulgu raporu — burada onun içeriği de özetleniyor, ama esas kanıt orada).

**Oturum kimliği:**
- Claude Code oturum id: `session_01NdAy98ohGcupFQzfFdpc3b` (`https://claude.ai/code/session_01NdAy98ohGcupFQzfFdpc3b`)
- Oturuma özel scratchpad dizini (geçici dosyalar buradaydı, örn. `sudo` parolası, test JSON çıktısı — hiçbiri kalıcı değil): `/tmp/claude-1000/-home-n4vitas/83b01997-b6b7-4a19-af74-79afbd77ac48/scratchpad`
- Ana çalışma dizini: `/home/n4vitas` (oturum sırasında ayrıca `~/navitas` = `/home/n4vitas/proje/NAVITAS_JETSON_20260906/navitas` ve `~/.claude/projects/-home-n4vitas/memory` dizinlerinde de işlem yapıldı)
- Makine: `navitas-jetson` (hostname), kullanıcı `n4vitas`, tarih 2026-09-17

---

## 1. Kullanıcının ilk isteği (turn 1)

> "selam, dun ucus gerceklestirdik ve dustu jetson calismaz sarj almaz oldu loglari incele
> ucus sirasinda log tutup tutmadigina bak ve sadece ucma degil model loglari dahil"

Yani: (a) dün bir düşüş oldu, (b) Jetson şu an çalışmıyor/şarj almıyor deniyor, (c) uçuş sırasında Jetson log tuttu mu incelensin, (d) yalnız uçuş logu değil **model/çıkarım** logu da dahil edilsin.

## 2. Yapılan inceleme ve bulgular (turn 1 cevabı)

Kronolojik olarak şunlar çalıştırıldı:

1. Hafızadaki proje bağlamı okundu (`navitas-jetson-proje`, `navitas-jetson-ortam`, `navitas-devir-bekleyen`, `navitas-referanslar`, `navitas-repo-kurallari`, `navitas-sudo-parola`).
2. `uptime`, `date`, `uname -a`, ev dizini listesi — kartın şu an (17 Eyl 10:10) az önce açıldığı (5 dk uptime) görüldü.
3. `journalctl --list-boots` — 16 Eylül'e ait açık bir kayıt **yok gibi göründü**; listede çok sayıda **"28 Temmuz 18:04:45"** damgalı açılış vardı, bu ilk bakışta kafa karıştırıcıydı.
4. `find /home/n4vitas -newermt "2026-09-15" ...` — 15-17 Eylül arası değişen dosyalar tarandı; navitas proje ağacında **hiçbir** yeni dosya bulunamadı (yalnız Firefox/agnet/portal-yakalama gibi ilgisiz dosyalar).
5. `journalctl --since "2026-09-16 00:00" --until "2026-09-17 09:00"` → boş değildi ama içerik incelendiğinde her şeyin **16 Eylül 00:35'te bir "temiz kapanış" ile bittiği**, sonra hiçbir gerçek-zaman-damgalı kayıt olmadığı görüldü.
6. Boot ID bazında (`journalctl -F _BOOT_ID`, her ID için ilk/son zaman + satır sayısı) tarama yapıldı → 16 Eylül 00:35'teki kapanıştan sonra journal'da bir sonraki gerçek-zamanlı kayıt **bugün (17 Eyl) 10:05:37**'de başlıyordu. Aradaki boşlukta 4 açılış "28 Temmuz" damgasıyla görünüyordu.
7. RTC donanımı sorgulandı (`cat /sys/class/rtc/rtc*/time,date`), `timedatectl` çalıştırıldı → NTP senkron olduğu, ama RTC'nin ayrı bir hikâyesi olduğu anlaşıldı.
8. `last -x reboot`, `last -x shutdown` (wtmp) → 16 Eyl 00:35 temiz kapanıştan sonra **4 açılış**, **hiçbirinde eşleşen shutdown kaydı yok** → hepsi ani güç kesilmesiyle bitmiş.
9. Bu 3 açılışın (4.'sü hiç kayıt bırakmamış) `journalctl _BOOT_ID=<id>` çıktıları tek tek okundu → uptime'ları sırasıyla **10,8 sn**, **12,1 sn**, **~42,8 sn**'de kesiliyordu. Kesilme noktaları: PCIe link-up, Ethernet sürücü yükleme, gdm/X başlangıcı.
10. `/sys/fs/pstore` (ramoops) kontrol edildi → **boş**, yalnız `/var/lib/systemd/pstore/console-ramoops-0` diskte **13 Eylül**'e ait eski bir kayıttı (824. saniyede normal `reboot`) → yeni panik/kilitlenme kaydı yok, yani kesilmeler **çekirdek paniği değil, besleme kaybı**.
11. Kart tarafında regülatör/PMIC/termal/watchdog hata satırı arandı → **hiç yok**.
12. `.bash_history` son 60 satırı okundu → 16 Eylül gecesi kamera/GPIO (`jetson-io.py`, `i2cdetect`, `gst-launch-1.0 nvarguscamerasrc`) denemeleri ve en son `shutdown now` görüldü.
13. `jetson_baslat.sh` içinde log hedefleri arandı (`LOG_DIZIN`, `results/`, `tee`) → varsayılan `LOG_DIZIN=$NAVITAS_KOK/results/jetson_log`.
14. `results/` dizini listelendi → bu dizin **hiç oluşmamış** (yalnız eski `jetson_log_20260906/09/10/12` var).
15. `find . -name "*.pyc" -newermt "2026-09-14"` → son çalıştırılan Python izi **15 Eylül 17:10** (`comms/__pycache__/inis_kaniti.cpython-312.pyc`), 16-17 Eylül'de hiçbir python dosyası çalışmamış.
16. `journalctl` içinde `imx477` aranarak kamera durumu kontrol edildi → 16 Eylül açılışında `imx477 9-001a: board setup failed`, `probe of 9-001a failed with error -121` → **kamera hâlâ bağlı/çalışır değil**.
17. Kartın **bugünkü** sağlık durumu ölçüldü: `nvpmodel -q` (10W), termal bölgeler (49-52 °C), `lsusb`, `nvme smart-log /dev/nvme0` (`critical_warning 0`, `media_errors 0`, `available_spare %100`, aşınma %17, ama `unsafe_shutdowns 331` / `power_cycles 8657` — taban değer olmadığı için düşüşe atfedilemedi).
18. Sistemd birimleri / crontab / autostart tarandı → `navitas` adında bir servis **yok**; kullanıcı biriminde yalnız `ag-portal-giris` (captive portal) var → **kart açılsa bile uçuş yazılımı kendiliğinden başlamıyor**.

### Sonuç (turn 1'de kullanıcıya söylenen):

- Jetson uçuşa dair **hiçbir uygulama/model logu tutmadı** — çünkü uçuş yazılımı o pencerede hiç çalıştırılmadı (otomatik başlatma yok, elle başlatılmamış, kamera zaten bağlı değildi, `--kuru` zaten `eksik` veriyordu).
- 16 Eylül 00:35 temiz kapanıştan sonra **4 açılış denemesi** oldu, hepsi ~11-43 saniyede **ani güç kesilmesiyle** yarıda kaldı (panik değil, besleme kaybı — pstore boş).
- Bu açılışlar journal'da **"28 Temmuz"** diye görünüyordu çünkü kartın RTC'si ağsız açılışta gerçek zamanı veremiyor; bu yüzden ilk bakışta "16-17 Eylül'de kayıt yok" sanılıyordu.
- Bugün kart **sağlıklı** açıldı (10W, 49-52 °C, NVMe hatasız); "şarj almıyor" Jetson'ın kendi özelliği olamaz (kartta pil yok) → LiPo/BEC/kablo tarafı olmalı.
- 5 öneri sıralandı (saat düzeltme, log dayanıklılığı, otomatik başlatma, hover kapı betiği, defter kaydı) — **hiçbiri bu turn'de uygulanmadı**, yalnız listelendi.
- Rapor dosyası yazıldı: `~/proje/NAVITAS_JETSON_20260906/JETSON_DUSUS_LOG_INCELEME_20260917.md`.
- İlgili hafıza dosyaları (`navitas-jetson-ortam.md`, `navitas-devir-bekleyen.md`) bu bulgularla güncellendi.

## 3. Kullanıcının araya giren mesajı (turn devam ederken)

Kullanıcı, ben hâlâ araç çağrıları çalıştırırken şu bilgiyi ekledi — **Windows PC'de Pixhawk logunun ayrıca incelendiğini** bildirdi:

> "dün log'u incelemişler win pcden: 17 Eylül 02:53 düşüşünün logunu inceledik. Drone yerden ~0,7 m yükseklikte düz hover yaparken, düşmeden önceki 13 saniye boyunca motorlar arasındaki çıkış farkı sürekli büyüdü (+16 µs'den +520 µs'ye) ve drone yönünü 14° kaçırdı. [...] 202,4. saniyede ön-sağ köşe aniden itkisini kaybetti, hemen ardından pervaneler birbirine girdi. GPS, pusula ve telemetri bağlantısı yere çarpmadan 0,4–0,5 saniye önce, yani havada koptu [...]. Olaydan önce pil, güç, kumanda, GPS, EKF ve ayarlarda hiçbir sorun yok. Pilot girişi olayı başlatmadı [...]. Titreşim oturumun başından beri önceki uçuşların 2,5–3 katıydı. En olası neden, 3B baskı gövdede gözle görülmeyen bir iç hasar [...] veya gövdenin bu yük için yeterince dayanıklı olmaması. [...] gövde/tasarım %70–85, pilotaj ve operasyon %10–25 [...]; bu log ölçümü değil, değerlendirme. Bundan sonra düşüş yaşamış baskı parçaları muayeneden geçse bile değiştirilecek. Her ilk kısa hover'dan sonra log kontrol edilecek (titreşim VibeZ ≤ 16, motor çıkış farkı ≤ 60 µs); geçmezse uçulmayacak. Bu uçuştan önceki kısa hover'ın logu da bu kontrolden geçemezdi."

Bu bilgi **doğrudan bende doğrulanmadı** (Pixhawk log dosyasına bu oturumda erişilmedi) — olduğu gibi kayda geçirildi. Kritik nokta: bildirilen düşüş saati **17 Eylül 02:53**, Jetson'ın journal boşluğunun (16 Eyl 00:35 → 17 Eyl 10:05) **tam içinde**. İki bulgu birbirini çürütmüyor; ikisi de bağımsız kanıtlarla "yazılım/Jetson kaynaklı değil" sonucuna varıyor.

## 4. Kullanıcının ikinci isteği (bu turn — 4 ayrı iş)

> "daha detayli analiz yap
> sonra sistemin varsayilan saatini cevrimdisi olsa bile gosterecek sekilde ayarla
> ayrica log sistemi tutmak ve bununla ilgili varsayimlar icin analiz ve harekete gec.
> sonra bu oturumda yazistigimiz soyledigimiz cevapladigimiz her seyi LOG-DURUMU.md dosyasinda projenin anadizininde yaz
> ana ai'yi baglayip senin soylediklerini incelettirecegim."

4 ayrı görev: (1) daha detaylı analiz, (2) çevrimdışıyken de doğru saat gösteren varsayılan saat ayarı, (3) log sistemi + varsayımlar için analiz ve **eylem**, (4) bu dosyanın yazılması. Aşağıda her biri ayrı ayrı raporlanıyor.

---

## 5. (1) Daha detaylı analiz — RTC mekanizmasının kanıtı

İlk raporda "RTC yedek pili muhtemelen yok" çıkarımı vardı; bu turn'de **doğrudan kanıtla** kapatıldı:

```
$ sudo cat /sys/class/rtc/rtc0/hctosys   → 1        (nvvrs-pseq-rtc = kernel'in KULLANDIĞI saat)
$ sudo cat /sys/class/rtc/rtc1/hctosys   → 0        (tegra_rtc = kullanılmıyor, zaten 1970'te donuk)
$ sudo hwclock -r --rtc=/dev/rtc0        → 2026-09-17 10:35:07  (şu an "doğru" — çünkü NTP üzerine yazdı)
$ dmesg | grep rtc
[ 9.791964] nvvrs-pseq-rtc nvvrs-pseq-rtc: setting system clock to 1970-01-01T00:00:30 UTC (30)
```

**Bu satır bugünkü açılışta, kart fişteyken ve ağ bağlıyken bile çıktı.** Yani PMIC RTC'si (nvvrs-pseq-rtc — gerçekten kullanılan RTC) **her güç döngüsünde ~0 saniyeye sıfırlanıyor**. Şu an doğru görünmesi yalnızca bu oturumda NTP'nin üzerine yazmasından. Bu, Jetson Orin Nano Dev Kit'in fabrika çıkışında RTC pil konektörünün (taşıyıcı kart üstü CR2032 girişi) **boş** gelmesiyle bire bir örtüşüyor.

`systemd`'nin bunu "28 Temmuz" tabanına yükseltmesinin mekanizması da kanıtlandı:

```
$ ls /usr/lib/clock-epoch                        → yok
$ ls -la --time-style=full-iso /usr/lib/systemd/systemd
-rwxr-xr-x 1 root root 133456 2026-07-28 18:04:45.000000000 +0300 /usr/lib/systemd/systemd
```

`/usr/lib/clock-epoch` yok olduğu için systemd, RTC'den gelen 1970 değerini mantıksız bulunca **kendi ikilisinin mtime'ını** taban alıyor — bu da JetPack imajının bu NVMe'ye yazıldığı tarihle (28 Temmuz 2026) **saniyesi saniyesine eşleşiyor**. Ağ varsa NTP bunu saniyeler içinde düzeltiyor (bugün: uptime 52. saniyede `Initial clock synchronization to Thu 2026-09-17 10:05:37`); ağ yoksa (sahada tipik) kart **tüm oturum boyunca** 28 Temmuz'da kalıyor.

**Ayrıca doğrulanan/elenen ihtimaller:**
- wtmp/journal boot sıralaması `__SEQNUM` üzerinden global kronolojik olarak güvenilir **DEĞİL** (her journal dosyasının kendi "Sequential number ID"si var, boot'lar arası tek bir sayaç değil) — bu yüzden 4 ölü açılışın **birbirine göre sırası** `last -x reboot`'un dosya-ekleme sırasından güvenilir, ama düşüş anına (02:53) göre **önce mi sonra mı** olduğu, hiçbir açılış NTP'ye ulaşamadığı için **belirlenemedi** (ÖLÇÜLEMEDİ, uydurulmadı).
- NVMe SMART taban değeri (önceki oturumlardan kayıtlı bir `power_cycles`/`unsafe_shutdowns` ölçümü) hiçbir rapor/log dosyasında bulunamadı → düşüşe kaç güç döngüsü/ani kapanmanın ait olduğu **söylenemez** (ÖLÇÜLEMEDİ).
- `/sys/fs/pstore`'un DTB'de sabit 2 MB ayrılmış bir alan olduğu, büyütülmesinin cihaz ağacı değişikliği gerektirdiği ve bu oturumda **dokunulmadığı** teyit edildi (riskli, açılışı bozabilir).

Tüm bu detaylar ana rapora (`JETSON_DUSUS_LOG_INCELEME_20260917.md` §3, §7) işlendi.

---

## 6. (2) Çevrimdışı varsayılan saat düzeltmesi — UYGULANDI

**Sorun:** Yukarıdaki mekanizma yüzünden ağsız açılışta kart "28 Temmuz 2026" gösteriyordu — sahada üretilecek her log yanlış damgalı olurdu.

**Gerçek/kalıcı çözüm donanımsal** (RTC pil takmak) — bunu yazılımla tam çözemem, satın alma/donanım kararı takımın. Yazılımla yapılabilecek **en iyi telafi** uygulandı:

```
$ sudo apt-get install -y fake-hwclock
```

- Paket: `fake-hwclock 0.13` (Ubuntu universe deposundan, çevrimiçi kuruldu).
- Otomatik etkinleşen 3 systemd birimi:
  - `fake-hwclock-load.service` — `Before=sysinit.target`, `DefaultDependencies=no` → **açılışta çok erken** çalışır, `/etc/fake-hwclock.data`'daki son kaydı okur, **mevcut saat ondan eskiyse ileri alır** (kaynak: `/usr/sbin/fake-hwclock` betiği, `load` komutu: `if NOW_SEC <= SAVED_SEC then date -u -s "$SAVED"`). **Asla geri almaz** — güvenli.
  - `fake-hwclock-save.service` — `Before=shutdown.target` → her kapanış/reboot'ta anlık saati diske yazar.
  - `fake-hwclock-save.timer` — periyodik kayıt. **Varsayılan 1 saat yerine 10 dakikaya sıkılaştırıldı** (saha koşumlarında ani güç kesilmesi ihtimaline karşı — RTC'nin doğal "11 dakikada bir hctosys" senkron aralığıyla da uyumlu):
    ```
    $ sudo cat /etc/systemd/system/fake-hwclock-save.timer.d/10dk-saha.conf
    [Timer]
    OnCalendar=
    OnCalendar=*:0/10
    ```
    (Paketin kendi birim dosyası değiştirilmedi — bir drop-in ile ezildi, paket güncellemesinde kaybolmaz.)
- Elle ilk kayıt zorlandı ve doğrulandı:
  ```
  $ sudo /usr/sbin/fake-hwclock save
  $ cat /etc/fake-hwclock.data
  2026-09-17 07:36:00
  ```
- Bugünkü açılışta `fake-hwclock-load.service`'in **doğru çalıştığı** teyit edildi (henüz kayıtlı veri güncel olduğu için "geçmişte" deyip hiçbir şey yapmadı — beklenen davranış):
  ```
  Sep 17 10:35:43 fake-hwclock[14474]: Current system time: 2026-09-17 07:35:43
  Sep 17 10:35:43 fake-hwclock[14474]: fake-hwclock saved clock information is in the past: 2026-09-17 07:35:41
  ```

**Sonuç:** Bundan sonra kart ağsız açılırsa, "28 Temmuz" yerine **son kayıttan en fazla ~10 dakika eski** bir saatle kalkacak — düşüş öncesi gibi bir senaryoda artık kabaca doğru gün/saat aralığında log üretilir, Pixhawk logu ile hizalanabilir. **Tam kesinlik için hâlâ RTC pili veya GPS-zaman senkronu önerilir** (madde 8'e bakınız).

**Neden komple/farklı bir çözüm değil:** `hwclock`'u gerçek RTC'ye yazdırmak (`hwclock -w`) burada işe yaramaz çünkü sorun RTC'nin *donanımsal olarak* zamanı tutamaması — üzerine yazsak da bir sonraki güç kaybında yine sıfırlanır. `fake-hwclock` tam bu senaryo için (RTC'siz/pilsiz kartlar — orijinal olarak Raspberry Pi için) tasarlanmış, doğru araç.

---

## 7. (3) Log sistemi + varsayımlar — analiz ve eylem

**Analiz edilen varsayımlar ve sonuçları:**

| Varsayım | Doğru mu? | Kanıt |
|---|---|---|
| "journalctl --list-boots tarihe göre güvenilir sıralıdır" | ❌ **Yanlış** | RTC/saat sorunu (§5) — boot'lar "28 Temmuz"a yığılıyor |
| "Kart açıksa uçuş yazılımı da çalışıyordur" | ❌ **Yanlış** | Otomatik başlatma birimi yok (§ turn 1, madde 18) |
| "Sistem saatine güvenilebilir (log damgaları doğrudur)" | ❌ **Yanlış** (çevrimdışıyken) | §5 — artık `fake-hwclock` ile kısmen düzeltildi |
| "journald'ın varsayılan ayarları saha kullanımı için yeterli" | ❌ **Yanlış** | Varsayılan `SyncIntervalSec` 5 dk — ani güç kesilmesinde bu kadar geniş bir pencere kaybolabilir |
| "jetson_baslat.sh, LOG_DIZIN'i kendi oluşturmuyor (kusurlu)" | ❌ **Yanlış** — script'te kusur yok | `jetson_baslat.sh:554,652` `mkdir -p "$LOG_DIZIN/mavproxy"` zaten var; dizin sadece **hiç çalıştırılmadığı** için yoktu |
| "pstore (ramoops) güç kesilmesini de yakalar" | ❌ **Yanlış** | Yalnız panik/watchdog resetini yakalar (DRAM'de tutulur); gerçek güç kaybında kaybolur — bu yüzden 4 ölü açılışın hiçbirinde ramoops kaydı yok |

**Eyleme geçilenler (host/işletim sistemi seviyesi — repo'ya/uçuş koduna dokunmadan):**

1. **journald dayanıklılığı sıkılaştırıldı.** Eski hâli yedeklendi: `/etc/systemd/journald.conf.navitas-onceki-20260917`. Yeni içerik:
   ```ini
   [Journal]
   Storage=persistent
   Compress=yes
   SyncIntervalSec=5s
   RateLimitIntervalSec=30s
   RateLimitBurst=100000
   ```
   - `Storage=persistent`: zaten fiilen aktifti (auto modu + `/var/log/journal` var olduğu için), **açıkça** yazıldı ki bir gün o dizin silinirse sessizce volatile'a düşmesin.
   - `SyncIntervalSec` 5 dakikadan **5 saniyeye** indirildi — ani güç kesilmesinde kaybolan pencere daraldı (tam sıfırlanmadı, bkz. kalan sınır aşağıda).
   - `RateLimitBurst` yükseltildi — bir çökme anında kısa sürede çok sayıda kernel/uygulama mesajı gelirse (motor arızası, panik, vb.) hız sınırına takılıp mesajların "... suppressed" ile yutulmaması için.
   - `systemctl restart systemd-journald` ile etkinleştirildi, `systemctl is-active` ve `journalctl -n 3` ile doğrulandı.
   - **Kalan sınır (dürüstçe belirtilmeli):** 5 saniyelik pencere hâlâ sıfır değil; tam garanti isteniyorsa uygulama logunun kendisi satır bazlı `flush()+os.fsync()` yapmalı — bu, model/uçuş logu Python koduna dokunmayı gerektirir (madde 4 aşağıda, mimar kararı).

2. **`jetson_baslat.sh` kodu incelendi, kusur olmadığı doğrulandı** (`LOG_DIZIN` zaten `mkdir -p` ediliyor) — bu yüzden dizini elle önceden oluşturmak gibi kozmetik bir "düzeltme" yapılmadı; gerçek sorun operasyonel (hiç çalıştırılmamış), kod değil.

3. **Bilinçli olarak yapılmayan/uygulanmayan** (repo kuralı gereği — "mimar kararı gerektiren şeyleri uygulama, listele"):
   - Jetson'ı açılışta otomatik olarak `jetson_baslat.sh`'ı çalıştıran bir systemd birimi **eklenmedi**. Gerekçe: uçuş-kritik yazılımı kartın açılışına otomatik bağlamak bir güvenlik/operasyon kararı — üstelik tam bir kaza soruşturması ortasında, takım onayı olmadan kartın davranışını sessizce değiştirmek riskli olur.
   - FOV/ODAK, YKS_IP, IKA_IP beyanlarının kalıcı dosyaya yazılması **yapılmadı** — bu da uygulama/operasyon kararı, iş navitas git deposuna dokunmayı gerektirir.
   - `/sys/fs/pstore` boyutunun büyütülmesi (DTB overlay) **yapılmadı** — riskli, açılışı bozabilir.
   - Görev logunun satır bazlı `fsync()` etmesi için Python kod değişikliği **yapılmadı** — repo koduna dokunmak, mimar/takım kararı.

Bu 4 madde ana rapora da (`JETSON_DUSUS_LOG_INCELEME_20260917.md` §6-C) "🔴 ANALİZ EDİLDİ, UYGULANMADI" olarak işlendi.

---

## 8. Değiştirilen/oluşturulan dosyaların tam listesi (bu oturum, host seviyesi)

| Dosya/birim | İşlem | Not |
|---|---|---|
| `/etc/systemd/journald.conf` | değiştirildi | eskisi `.navitas-onceki-20260917` uzantısıyla yedeklendi |
| `fake-hwclock` paketi | kuruldu | `apt-get install -y fake-hwclock`, 7148 B, universe deposu |
| `/etc/fake-hwclock.data` | oluşturuldu | ilk kayıt elle zorlandı |
| `/etc/systemd/system/fake-hwclock-save.timer.d/10dk-saha.conf` | oluşturuldu | 1 saatlik varsayılanı 10 dk'ya indiren drop-in |
| `fake-hwclock-load.service` / `fake-hwclock-save.service` / `fake-hwclock-save.timer` | etkinleştirildi | paket kurulumunun kendisi etkinleştirdi (`enabled`) |
| `~/proje/NAVITAS_JETSON_20260906/JETSON_DUSUS_LOG_INCELEME_20260917.md` | yazıldı + güncellendi | ana bulgu raporu |
| `~/.claude/projects/-home-n4vitas/memory/navitas-jetson-ortam.md` | güncellendi | saat tuzağı bulgusu eklendi |
| `~/.claude/projects/-home-n4vitas/memory/navitas-devir-bekleyen.md` | güncellendi | düşüş + Jetson bulgusu özeti eklendi |
| `~/navitas/LOG-DURUMU.md` (bu dosya) | yazıldı | — |

**navitas git deposuna (kod, REVIEW_LOG, CONTRACTS) hiçbir dokunuş yok, commit atılmadı.** Yukarıdaki tüm değişiklikler Jetson'ın işletim sistemi seviyesinde (`/etc/systemd/*`, apt paketi) — proje kodunun dışında.

---

## 9. Mimar/takımın karar vermesi gereken açık maddeler

1. **RTC pili** — taşıyıcı kartın RTC/CR2032 girişine pil takılsın mı? (Kesin çözüm; fake-hwclock yalnız telafi.)
2. **Jetson'ı açılışta otomatik göreve sokma** — systemd birimi + FOV/ODAK/YKS_IP/IKA_IP kalıcı beyan dosyası eklensin mi? Güvenlik/operasyon kararı.
3. **Log dosya adlarına boot id + monotonik saniye eklenmesi** — kod değişikliği, uygulama tarafı.
4. **Görev logunun satır bazlı fsync etmesi** — kod değişikliği, uygulama tarafı.
5. **Açılışta Pixhawk GPS'inden saat kurma** — `mavlink_dogrula` hattı üzerinden, fake-hwclock'tan daha kesin olur ama kod değişikliği ister.
6. **REVIEW_LOG D-### kaydı** — hem düşüş hem bu host-seviyesi düzeltmeler için bir bulgu kaydı açılması gerekiyor; `git fetch origin` + master'daki en yüksek D numarası görülmeden numara verilmedi (bu depoda tekrarlayan çakışma hatası, hafıza `navitas-repo-kurallari`'da not edilmiş).
7. **Hover kapı betiği** (`scripts/olcum/…_hover_kapisi.py`, VibeZ ≤ 16 + motor farkı ≤ 60 µs) — istenirse yazılabilir, henüz yazılmadı.

---

## 10. Kısa özet (tek paragraf — bu bölüme kadarki turn'ler)

Jetson, 17 Eylül 02:53'teki düşüşe dair hiçbir log tutmadı çünkü uçuş yazılımı o pencerede hiç çalıştırılmadı (otomatik başlatma yok, kamera bağlı değildi, gerekli beyanlar eksikti) ve kart, 16 Eylül 00:35 temiz kapanıştan sonra 17 Eylül 10:05'e kadar 4 kez ani güç kesilmesiyle (besleme kaybı, panik değil) yarım açıldı — bu açılışlar, kartın RTC'sinin pil desteği olmadığı (her güç döngüsünde ~0 saniyeye sıfırlandığı, kanıtlı: `dmesg`'de "setting system clock to 1970-01-01T00:00:30") ve ağsız halde systemd'nin bunu paketlerin kuruluş tarihi olan 28 Temmuz 2026'ya yükselttiği için ilk bakışta "kayıt yok" sanıldı. Bu turn'de: (a) bu mekanizma doğrudan kanıtla kesinleştirildi, (b) `fake-hwclock` kurulup 10 dakikalık kayıt aralığıyla yapılandırılarak çevrimdışı açılışlarda saatin artık "28 Temmuz"a değil son bilinen zamana yakın bir değere kalkması sağlandı, (c) journald'ın güç-kesilmesi dayanıklılığı sıkılaştırıldı (`Storage=persistent`, `SyncIntervalSec=5s`, `RateLimitBurst` artırıldı), (d) uçuş yazılımının otomatik başlatılması gibi güvenlik kararı gerektiren maddeler bilinçli olarak uygulanmadı, yalnız listelendi. navitas git deposuna hiç dokunulmadı.

---

## 11. Kullanıcının üçüncü isteği: hover kapı betiği

Önceki bölümde (§6-D) önerilen "hover kapı betiği" kullanıcı tarafından soruldu ("ne demek"), açıklandıktan sonra "evet yaz, .BIN ve tlog ikisini de destekle" denildi.

**Yazıldı:** `scripts/hover_kapisi.py` (279 satır), `scripts/tlog_akim_ozet.py` ve `scripts/ucus_logu_devrilme.py` ile **aynı kalıpta** (aynı `pymavlink.mavutil` okuma yöntemi, aynı "OLCULEMEDI != sessiz gecti" kültürü, aynı çıkış kodu sözleşmesi).

- **Ölçer:** VibeZ tepe (DataFlash `VIBE.VibeZ` / tlog `VIBRATION.vibration_z`) ve motor çıkış farkı tepe (yapılandırılmış kanallar arası max-min; varsayılan AUX1-4 = SERVO9-12, D-428 §5d ile aynı).
- **Eşikler:** `VIBEZ_ESIK=16`, `MOTOR_FARK_ESIK_US=60` — takımın 2026-09-17 kararı, kod içinde ön-kayıtlı sabit; `--vibez-esik`/`--motor-fark-esik-us` yalnız keşif/teşhis içindir, asıl kapı kararı için gevşetilmemesi gerektiği docstring'de ve `--help`'te açıkça yazılı.
- **Çıktı:** pencereli eğilim tablosu (düşüşten önceki "13 saniyede kademeli büyüme" türü paterni yakalamak için) + `KAPI: TAMAM` / `KAPI: BASARISIZ` hükmü + çıkış kodu (0/1/2) + isteğe bağlı `--json`.

**Test edildi (bu oturumda, gerçek veriyle):**
- `--help`, eksik dosya (`OLCULEMEDI`, çıkış 2) ✅
- Gerçek tlog'a karşı (`results/ucus_loglari/20260906/…19-52-44.tlog`, ~2 saatlik uçuş): VIBRATION ve SERVO_OUTPUT_RAW (AUX9-12) doğru okundu, VibeZ tepe 50,32 m/s/s ve motor fark tepe 799 µs bulundu (ikisi de eşiği aştığı için) → `KAPI: BASARISIZ`, çıkış kodu 1 — **beklenen ve doğru** (bu bir kısa hover değil, uzun bir uçuş oturumu; script tasarım gereği "tüm dosyanın tepe değerine" bakıyor).
- `--json` çıktısı geçerli JSON, tüm alanlar doğru.
- Çoklu dosya + "en kötü sonuç" mantığı (BAŞARISIZ > ÖLÇÜLEMEDİ > TAMAM önceliğiyle) doğrulandı.
- Eşik override (`--vibez-esik 100 --motor-fark-esik-us 1000`) aynı log'u `KAPI: TAMAM` yaptı — parametre akışı (global mutasyon yerine saf fonksiyon parametreleri, ilk yazımda `global` sözdizimi hatası çıktı, düzeltildi) doğru çalışıyor.
- `python3 -m py_compile` temiz.

**Test EDİLEMEYEN / açık sınır:** `.BIN` (DataFlash) yolu bu Jetson'da **canlı test edilemedi** — makinede hiç `.bin` dosyası yok (arandı, sıfır sonuç). Kod, `ucus_logu_devrilme.py`'nin zaten kanıtlı kullandığı **aynı** alan adlarını kullanıyor (`VIBE.VibeZ`, `RCOU.C9-C12`) ve `pymavlink.DFReader` modülünün bu venv'de kurulu olduğu doğrulandı (`import pymavlink.DFReader` başarılı) — mekanizma güvenilir ama gerçek bir `.BIN` dosyasıyla uçtan uca doğrulanmadı. Elde bir DataFlash log'u olduğunda bu betikle koşulup sonucun bu dosyaya eklenmesi önerilir.

**navitas git deposuna commit atılmadı** (CLAUDE.md madde 17 — izin gerekir).

---

## 12. Kamera durumu — DÜZELTME (turn 1'deki bulgu artık geçerli değil)

Turn 1'de (§2, madde 16) "kamera hâlâ bağlı değil, `imx477 9-001a: board setup failed`" denmişti — bu **16 Eylül'deki eski bir açılıştan** okunmuştu ve o an doğruydu.

**Bugün (17 Eylül, mevcut açılış) durum farklı:** iki IMX477 kamera portu var (i2c bus 9 ve 10). Bugünkü `dmesg`:
```
[ 9.751316] tegra-camrtc-capture-vi tegra-capture-vi: subdev imx477 9-001a bound     ← BAŞARILI
[10.107980] imx477 10-001a: imx477_board_setup: error during i2c read probe (-121)   ← BAŞARISIZ (aynı hata, diğer port)
[10.108402] imx477: probe of 10-001a failed with error -121
```
`/dev/video0` artık **var** (`crw-rw----+ 1 root video 81, 0`). Yani **bir kamera portu (bus 9) şu an gerçekten bağlı ve kernel'e tanıtılmış** — muhtemelen 16 Eylül'den bugüne fiziksel olarak yeniden takılmış/düzeltilmiş. İkinci port (bus 10) hâlâ aynı `-121` hatasını veriyor — muhtemelen o porta hiç kamera takılı değil (fiziksel, yazılımla teşhis edilemez).

**Doğrulanmadı:** `v4l2-ctl` bu Jetson'da kurulu değil (`command not found`), bu yüzden gerçekten kare alınabildiği (yalnız kernel'in "bound" demesi değil, fiilen görüntü akışı) bu oturumda **test edilmedi**. `jetson_paket/kod/kamera_dogrula.py` (OpenCV `cv2.VideoCapture`) depoda hazır — istenirse gerçek kare/FPS testi bu betikle yapılabilir, bu oturumda çalıştırılmadı (kullanıcının bugünkü öncelik sırasına göre — §13).

---

## 13. ÖNEMLİ NOT (kullanıcı vurguladı): koordinat telemetrisi var, video telemetri yok — bugünkü öncelik sırası

Kullanıcının birebir sözü:
> "kordinat telemetrisi var video telemetri yok ayni ag'da baglanip video'yu test etmek istemistim ama bugun her ikisine bagakacagiz oncelik kordinat telemetrisi."

Yani: konum/koordinat telemetrisi (muhtemelen Pixhawk MAVLink hattı — GPS/konum verisi YKS/IKA'ya ya da yer istasyonuna gidiyor) çalışıyor; video telemetri çalışmıyor. Bugün ikisi de ele alınacak ama **öncelik koordinat telemetrisi**.

**Bu oturumda kod içinde bulunan, video telemetrisini doğrudan ilgilendiren bir mimari kısıt (kullanıcıya iletilmesi gerekir):**

`jetson_baslat.sh` içindeki "işaretli gösterici" (T228, D-443, `H9_MK15/TASARIM.md`) tasarımı **video akışını bilerek LAN'a açmıyor** — yalnız `127.0.0.1` (loopback). Yorum satırları (`jetson_paket/jetson_baslat.sh:46-51,192-200`):
```
Video SiK'e GIRMEZ. 0.0.0.0 yalniz acik beyanla; ... Varsayilan 127.0.0.1 (disariya KAPALI).
YALNIZ loopback: isaretli yayin LAN'a acilmaz — disari DP->HDMI donusturucu ya da yedek RTSP ile gider.
```
Yani "aynı ağda bağlanıp video'yu test etmek" senaryosu **mevcut tasarımla doğrudan desteklenmiyor** — bu ihmal değil, kasıtlı bir güvenlik/mimari karar (D-443: gösterici "KARAR ÜRETMEZ", LAN'a açık video hattı istenmemiş). Ağ üzerinden video için iki resmî yol var: DP→HDMI donanım çıkışı (yerinde), ya da "yedek RTSP" (elle kurulur, `gosterici/GOSTERICI_KURULUM.md`).

**Ayrıca ikinci bir gerçek engel var:** `rpi_inference`'a video-overlay bayrağını (`--isaretli-yayin`) veren T227 görevi **depoda hâlâ birleşmemiş** — `jetson_baslat.sh` bunu kendisi denetliyor (`isaretli_destek_var()` fonksiyonu) ve T227 yoksa `GOSTERICI_KIP` kapalı kalmaya zorlanıyor ("argparse çıkış 2 → Restart döngüsü" riskini önlemek için). Yani kamera artık kısmen bağlı olsa bile (§12), "işaretli" (karar kutulu) video yayını şu an **yazılımca da eksik**.

**Sonuç — bugünkü test planına etkisi:** Koordinat telemetrisi önceliği doğru sıralama, çünkü video tarafı hem mimari olarak LAN'a kapalı hem de T227 bayrağı eksik olduğu için "aynı ağda bağlanıp izleme" bugünkü hâliyle çalışmaz; ya loopback/DP-HDMI/RTSP yoluna gidilmeli ya da bu iki kısıt (LAN erişimi + T227) önce çözülmeli. Bu madde §14'e (öneriler) de işlendi.

---

## 14. Geride kalan (tüm oturum + proje hafızası) ve ekosistem için yazılım önerileri

### 14.1 Geride kalan — açık maddeler (mimar/takım kararı ya da insan işi bekliyor)

**Bu oturumdan (Jetson/log/saat):**
1. RTC pili (donanım, CR2032) — `fake-hwclock` yalnız telafi, kalıcı çözüm değil.
2. Jetson'ı açılışta otomatik göreve sokan systemd birimi — güvenlik kararı, uygulanmadı.
3. FOV/ODAK/YKS_IP/IKA_IP kalıcı beyan dosyası — `--kuru` hâlâ `eksik` veriyor.
4. Log dosya adlarına boot id + monotonik saniye eklenmesi (kod değişikliği).
5. Açılışta Pixhawk GPS'inden saat kurma (`mavlink_dogrula` hattı, kod değişikliği).
6. REVIEW_LOG D-### kaydı — düşüş + host-seviyesi düzeltmeler için; `git fetch origin` + master'daki en yüksek numara görülmeden açılmadı.
7. `/sys/fs/pstore` (ramoops) boyutu — DTB overlay gerekir, riskli, ertelendi.

**Proje hafızasından (`navitas-devir-bekleyen`, güncel durum 2026-09-13):**
8. K2 — T66 kabul kümesi depoda yok (registry hâlâ `O:/` yolu gösteriyor).
9. K6, K8, K11 — açık, mimar işi.
10. K10 — yalnız liste yapıldı, `test_p4_runbook` ve `test_p8_sim_katmani` hâlâ `O:/` yolunda.
11. Telsiz frekans çelişkisi **hâlâ çözülmedi**: gövdedeki radyo RFD900A (900 MHz sınıfı) ama depo baştan sona 433 MHz diyor (`jetson_baslat.sh`, `CONTRACTS.md`, `SAHA_KOSUM_KAGIDI`, `comms/README.md`); gerçek firmware frekansı hiç ölçülmedi.
12. SiK RTT/kayıp ölçümü iki radyo ister — yapılmadı.
13. T211 motor künyesi, RC failsafe testi, D-433 RC6_OPTION — insan/saha işi, açık.
14. T220 (K2 T66/G4/K10/K1) ve T221 (K11 ArduPlane) — kuyrukta, henüz `[ ]`.
15. **T227** — `rpi_inference`'a `--isaretli-yayin` bayrağı eksik → video-overlay zinciri tamamlanamıyor (bugün yeniden gündeme geldi, §13).
16. Kamera port 10 (i2c bus 10) — hâlâ `-121` hatası; port 9 çalışıyor ama port 10'un fiziksel mi yoksa donanımsal bir arıza mı olduğu belirlenmedi.

### 14.2 Bu "istenen ekosistem" için yazılım önerileri (öncelik sırasıyla)

Bunlar **öneri** — hiçbiri bu oturumda uygulanmadı, mimar/takım onayı gerektirenler açıkça işaretli.

1. **[Mimar kararı] Otomatik görev başlatma + kalıcı beyan dosyası.** Jetson açılınca (ya da elle tek komutla) `jetson_baslat.sh`'ı doğru ortam değişkenleriyle (FOV/ODAK/YKS_IP/IKA_IP kayıtlı bir `.env`/JSON'dan okunarak) başlatan bir systemd birimi. Şu an her saha gününde bu değerler baştan elle veriliyor — hem yavaş hem unutmaya açık.
2. **[Mimar kararı] T227 (`--isaretli-yayin` bayrağı).** Video-overlay zincirinin tamamlanması için ön koşul; kamera artık kısmen çalıştığına göre (§12) bu görev artık gerçekten test edilebilir durumda — önceliği yükseltilebilir.
3. **[Kod, host'tan bağımsız] Kamera sağlık izleme betiği.** Kamera durumu oturumdan oturuma değişiyor (dün yok, bugün kısmen var) — nedeni bilinmiyor. Açılışta/periyodik `dmesg`'de `imx477.*bound` / `probe.*failed` satırlarını okuyup port 9/10 durumunu `results/`e loglayan küçük bir betik, "ne zamandır bağlı/bağlı değil" sorusunu ÖLÇÜLEBİLİR hâle getirir.
4. **[Kod] NVMe SMART taban değeri kaydı.** Bu oturumda "`unsafe_shutdowns 331`'in kaçı düşüşe ait?" sorusu taban değer olmadığı için ÖLÇÜLEMEDİ kaldı. Her saha günü başında `nvme smart-log`'u `results/`e yazan tek satırlık bir kanca (örn. `jetson_baslat.sh`'a veya ayrı bir cron'a) bunu gelecekte ölçülebilir yapar.
5. **[Kod] Ağ/video bağlanabilirlik ön-kontrolü.** "Aynı ağda bağlanıp video test etme" senaryosu için: YKS_IP/IKA_IP UDP erişilebilirliğini VE kamera FPS'ini tek komutta raporlayan bir betik — `SAHA_KOSUM_KAGIDI`'na eklenebilecek bir adım. §13'teki LAN kısıtı netleşmeden bu betiğin video kısmı loopback/RTSP moduna göre yazılmalı.
6. **[Kod] REVIEW_LOG D-numarası yardımcı betiği.** Çakışma "tekrarlayan hata" (2. kez) — `git fetch origin && git show origin/master:REVIEW_LOG.md | grep -oE "D-[0-9]+"` yapıp bir sonraki boş numarayı basan tek satırlık bir betik, bu sürtünmeyi ortadan kaldırır.
7. **[Yapıldı, bu oturumda] `scripts/hover_kapisi.py`** — §11. Saha akışına (her kısa hover sonrası) elle çağrılacak şekilde entegre edilebilir; otomatik kancaya (örn. Pixhawk log indirildiğinde tetiklenen bir izleyici) bağlanması ayrı bir öneri, henüz yapılmadı.

### 14.3 Bu oturumda YAPILAN (tekrar, netlik için)
`fake-hwclock` kurulumu + 10 dk kayıt aralığı, `journald.conf` sıkılaştırması, `scripts/hover_kapisi.py` yazımı+testi, kamera durumu düzeltmesi (§12), bu belgenin kendisi. Hiçbiri git'e commit edilmedi.
