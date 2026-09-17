# Jetson log incelemesi — 17 Eylül 2026 düşüşü

**İnceleme tarihi:** 2026-09-17, Jetson üzerinde (oturum bilgisayarı = kazadaki kart)
**Soru:** Uçuş sırasında Jetson log tuttu mu? (uçuş + **model/çıkarım** logları dahil)
**Kısa cevap:** **Hayır. Uçuş saatine ait tek bir uygulama/model logu yok.** Jetson'ın o pencerede diske yazabildiği tek şey, yarım kalmış 4 açılışın ilk 12-43 saniyesidir.

---

## 1. Zaman çizelgesi (Jetson tarafı, kanıtlı)

| Zaman | Olay | Kanıt |
|---|---|---|
| 15 Eyl 23:00 → 16 Eyl 00:35 | Masaüstü oturumu (86 dk), ekran Acer EK220Q bağlı | boot `e7980a31` |
| **16 Eyl 00:35:22** | **Temiz kapanış** (`shutdown now`) | `systemd-poweroff` → `Journal stopped`; `.bash_history` son satırlar |
| 16 Eyl 00:35 → 17 Eyl 10:05 | **BOŞLUK — 4 açılış denemesi, hepsi yarım** | aşağıda §2 |
| **17 Eyl 02:53** | **Düşüş** (Pixhawk logundan, Windows PC'de incelendi) | Jetson'da karşılığı **yok** |
| 17 Eyl 10:05:37 | Bugünkü normal açılış, kart sağlıklı | boot `a8232b5f` |

Düşüş saati (02:53) tam olarak Jetson'ın kayıt boşluğunun içinde kalıyor. İki kayıt **çelişmiyor**; Jetson olaya dair bağımsız kanıt **üretemedi**.

---

## 2. Boşluktaki 4 açılış — ne oldu?

`wtmp` (`last -x reboot`) 16 Eyl 00:35 temiz kapanışından sonra **4 açılış** gösteriyor ve bunların **hiçbirinin eşleşen `shutdown` kaydı yok** → dördü de ani güç kesilmesiyle bitti.

Journal'da üçünün izi var (biri hiç kayıt bırakmamış):

| boot id | Diske yazılan son an | Ne kadar ilerledi |
|---|---|---|
| `7d7e98a2` | uptime **12,1 s** | Ethernet (r8168) sürücüsü yüklenirken kesildi |
| `c10c05a6` | uptime **10,8 s** | PCIe link-up sırasında kesildi |
| `b7a9fa7c` | uptime **~42,8 s** | gdm/X açılmış (`Xorg.0.log.old`), NetworkManager kirası yazılmış, sonra kesildi |
| (4.) | — | journal'a hiç yazamadan gitti |

**Kesilme biçimi:** `/sys/fs/pstore` **boş** ve yeni bir ramoops kaydı yok. Elde tek ramoops dosyası 13 Eylül'e ait (824. saniyede `reboot: Restarting system`, yani o gün verilen normal reboot). Ramoops DRAM'de tutulur; sıcak yeniden başlatmada kalır, **gerçek güç kesilmesinde kaybolur**. Yani bu 4 açılış **çekirdek paniği/kilitlenme değil, besleme kaybı** ile bitti.

**Kart tarafında hata kaydı yok:** regülatör/PMIC/termal/watchdog hata satırı hiçbirinde geçmiyor. Kesilmeler PCIe + Ethernet + GPU sürücülerinin yüklendiği, akımın tepe yaptığı ~11-12. saniyeye denk geliyor — bu **brownout (besleme yetersizliği)** imzasıdır, modül arızası imzası değildir.

---

## 3. Saat tuzağı — mekanizma kanıtlı (ilk raporun ötesinde detay)

**Zincir, çıkarım değil, doğrudan kanıtla kapatıldı:**

1. **RTC'nin pil desteği yok/bitik.** Kart `nvvrs-pseq-rtc` (PMIC RTC, `hctosys=1` → kernel'in gerçekten kullandığı saat budur) ve `tegra_rtc` (`hctosys=0`, kullanılmıyor, zaten 1970'de donuk) olmak üzere iki RTC taşıyor. **Bugünkü açılışta bile** — kart fişte, ağ takılıyken — kernel şunu yazdı:
   `[ 9.791964] nvvrs-pseq-rtc nvvrs-pseq-rtc: setting system clock to 1970-01-01T00:00:30 UTC (30)`
   Yani PMIC RTC'si her güç döngüsünde **~0 saniyeye** sıfırlanıyor; şu an "doğru" görünmesi yalnızca bu oturumda NTP'nin üzerine yazmış olmasından. Bu, Jetson Orin Nano Dev Kit'in fabrika hâliyle RTC pil konektörü (taşıyıcı kart üstü CR2032 girişi) **boş** gelmesiyle bire bir örtüşüyor — donanımsal, yazılımla tam çözülemez.
2. **systemd'nin "temmuz tabanı" da kanıtlı:** `/usr/lib/clock-epoch` yok → systemd, RTC saatini (1970) mantıksız bulunca kendi ikilisinin mtime'ını taban alıyor: `/usr/lib/systemd/systemd` → `2026-07-28 18:04:45.000000000` — **§ önceki bulgudaki "28 Temmuz" tabanıyla saniyesi saniyesine aynı.** (Bu tarih muhtemelen JetPack imajının bu NVMe'ye yazıldığı/paketlerin açıldığı tarih.)
3. **NTP geldiğinde ne kadar hızlı düzeliyor:** bugünkü açılışta `systemd-timesyncd`, uptime 52. saniyede (kernel'in RTC'yi okumasından ~42 sn sonra) `Initial clock synchronization to Thu 2026-09-17 10:05:37` diyor. Yani ağ varsa düzelme **saniyeler** içinde; ağ yoksa (sahada tipik durum) kart tüm oturum boyunca temmuz tabanında kalır.

**Sonuçları:**
- `journalctl --list-boots` bu açılışları **28 Temmuz** diye sıralıyor, listenin en başına atıyor; "16-17 Eylül'de kayıt yok" diye bakan biri bunları göremez.
- Sahada ağsız üretilecek **her log yanlış zaman damgası taşır** → Pixhawk `.BIN` logu ile eşleştirilemez.

**🟢 UYGULANDI (2026-09-17, bu oturumda):** `fake-hwclock` kuruldu — açılışta (`sysinit.target`'tan önce) diskteki son bilinen saati okuyup, mevcut saat ondan **geride ise ileri alıyor** (asla geri almıyor, güvenli); kapanışta ve **10 dakikada bir** (varsayılan 1 saat yerine, saha koşumları için sıkılaştırıldı — drop-in `/etc/systemd/system/fake-hwclock-save.timer.d/10dk-saha.conf`) diske yazıyor. Artık ağsız bir açılışta kart "28 Temmuz" yerine **son kayıttan en fazla ~10 dk eski** bir saatle kalkacak. Donanımsal asıl çözüm (RTC pil takmak) hâlâ öneri listesinde (§6-A); bu yalnız yazılım telafisi.

---

## 4. Model/çıkarım logları — neden hiç yok

Zincirin **her** halkası kapalı:

1. **Otomatik başlatma yok.** `navitas` adlı systemd birimi yok (`/etc/systemd` taraması boş), kullanıcı crontab'ı boş, `~/.config/autostart` yok. Kullanıcı birimi olarak yalnız `ag-portal-giris` (captive portal girişi) var. → Kart açılsa bile model **kendiliğinden başlamaz**.
2. **Çalıştırıcı elle başlatılır:** `jetson_paket/jetson_baslat.sh`, varsayılan `LOG_DIZIN=$NAVITAS_KOK/results/jetson_log`. Bu dizin **hiç oluşmamış** (yalnız eski `jetson_log_20260906/09/10/12` var).
3. **Son python çalıştırma izi 15 Eyl 17:10** (`comms/__pycache__/inis_kaniti.cpython-312.pyc`). 16-17 Eylül'de **hiçbir** `.pyc` dokunulmamış.
4. **`results/` altında 13 Eylül'den sonra tek dosya yok**; ev dizininde 16 Eyl 00:36 - 17 Eyl 10:05 arasında yazılmış kullanıcı dosyası **yok**.
5. **Kamera hâlâ bağlı değil.** 16 Eyl açılışında `imx477 9-001a: board setup failed`, `probe of 9-001a failed with error -121`. Kamera yoksa model kare alamaz.
6. Ayrıca `--kuru` zaten `eksik` veriyordu (FOV/ODAK, YKS_IP, IKA_IP beyanları yok) → uçuş kipinde başlatılmak istense **açılmazdı**.

**Sonuç:** Jetson bu uçuşta görev yazılımı çalıştırmadı; dolayısıyla üretilmemiş bir model logu aranıyor. Kayıp bir log yok, **hiç yazılmadı**.

---

## 5. Kartın bugünkü durumu ("çalışmıyor / şarj almıyor")

Bugün 10:05'te **normal açıldı** ve sorunsuz çalışıyor:

- Güç kipi 10W, sıcaklıklar 49-52 °C (cpu 51,3 · gpu 49,8 · tj 51,8)
- NVMe SMART: `critical_warning 0`, `media_errors 0`, `available_spare %100`, aşınma %17
- Bugünkü açılışta ext4/NVMe/GÇ hatası **yok**
- `unsafe_shutdowns: 331`, `power_cycles: 8657` — **taban değer kaydımız olmadığı için** bu sayıların ne kadarının düşüşe ait olduğunu söyleyemem (ÖLÇÜLEMEDİ)

**Yorum:** Modül ve NVMe ayakta. "Şarj almıyor" Jetson'ın kendi özelliği olamaz (kartta pil yok) → LiPo / BEC / güç kablosu-konnektör tarafı. Pixhawk analizi GPS-pusula-telemetri kablolarının **yere çarpmadan 0,4-0,5 sn önce havada koptuğunu** söylüyor; aynı anda Jetson besleme hattının da zedelenmiş olması beklenir. Boşluktaki 4 açılışın ~11-12. saniyede kesilmesi bu tabloyla tutarlı.

---

## 6. Öneriler ve yapılan işler

**🟢 A. Saat sorunu — YAZILIM TELAFİSİ UYGULANDI (2026-09-17):**
- `fake-hwclock` kuruldu + etkin (§3). Kalıcı asıl çözüm hâlâ **donanımsal**: taşıyıcı kartın RTC pil girişine CR2032 takılması — bunu yazılımla yapamam, karar/satın alma takımın.
- **Uygulanmadı, öneri kalıyor:** Log dosya adlarına duvar saati yanında **boot id + monotonik saniye** eklenmesi (uygulama kodu değişikliği, mimar kararı).
- **Uygulanmadı, öneri kalıyor:** Açılışta Pixhawk GPS zamanından saat kurma (`mavlink_dogrula` hattı üzerinden) — fake-hwclock'tan daha kesin olur ama kod değişikliği ister.

**🟢 B. Log dayanıklılığı — UYGULANDI (2026-09-17):** `/etc/systemd/journald.conf` (eski hâli `journald.conf.navitas-onceki-20260917` olarak yedeklendi) → `Storage=persistent` açıkça yazıldı, `SyncIntervalSec` 5 dk'dan **5 sn**'ye indirildi (güç kesilmesinde kaybolan pencere daraldı), `RateLimitBurst` 100000/30sn'ye çıkarıldı (çökme anındaki mesaj patlaması hız sınırına takılıp kaybolmasın diye). `systemctl restart systemd-journald` ile etkin, doğrulandı.
- **Kalan sınır:** Bu yalnız pencereyi daraltır, sıfırlamaz — 5 saniyelik bir yazma aralığında olursa yine kaybolabilir. Tam garanti için uygulama logunun kendisi satır bazlı `flush()+fsync()` yapmalı (bkz. C).
- **Uygulanmadı, öneri kalıyor:** `/sys/fs/pstore` (ramoops) DTB'de 2 MB ayrılmış sabit bir alan; büyütmek cihaz ağacı değişikliği ister, bu oturumda dokunulmadı (riskli, açılışı bozabilir).

**🔴 C. Görev logu hiç yoksa uçuşun anlamı yok — ANALİZ EDİLDİ, UYGULANMADI (mimar kararı gerekiyor):** `jetson_baslat.sh` çalıştırıldığında `LOG_DIZIN`'i kendi `mkdir -p` ediyor (satır 554/652) — yani script'te bir kusur yok, **hiç çalıştırılmadığı** için `results/jetson_log` oluşmadı. Jetson'ı uçuşta otomatik göreve sokmak için gerekenler: (1) açılışta `jetson_baslat.sh`'ı başlatan bir systemd birimi, (2) FOV/ODAK, YKS_IP, IKA_IP beyanlarının kalıcı bir dosyada tutulması (şu an `--kuru` bunlar eksik olduğu için `eksik` çıkışı veriyor), (3) kamera bağlantısının kalıcı hâle getirilmesi. **Bunu kasıtlı olarak uygulamadım:** uçuş-kritik yazılımı kartın açılışına otomatik bağlamak güvenlik/operasyon kararı — takım/mimar onayı olmadan yapılmaz (repo kuralı: "mimar kararı gerektiren şeyleri uygulama, listele"). Detaylı analiz `LOG-DURUMU.md`'de.

**D. Yeni hover kuralınız için:** `scripts/tlog_akim_ozet.py` ve `scripts/ucus_logu_devrilme.py` zaten var; VibeZ ≤ 16 ve motor çıkış farkı ≤ 60 µs kapısını otomatik veren küçük bir betik (`scripts/olcum/…_hover_kapisi.py`) eklenebilir — istenirse yazarım.

**E. Defter:** Bu bir bulgu kaydı (D-###) hak ediyor — hem düşüş hem RTC/journald düzeltmesi için. Numara çakışması bu depoda tekrarlayan hata olduğu için önce `git fetch origin` + master'daki en yüksek D numarası görülmeli. Bu oturumda **depoya dokunulmadı, commit atılmadı** (yapılan değişiklikler `navitas` git deposunun dışında, işletim sistemi seviyesinde — `/etc/systemd/journald.conf`, `apt install fake-hwclock`).

---

## 7. Pixhawk bulguları (Windows PC'de incelendi — bu oturumda doğrulanmadı, olduğu gibi aktarılıyor)

Kullanıcı takımı Pixhawk `.BIN`/tlog'unu Windows PC'de incelemiş. Özet (bu bir **değerlendirme**, ölçüm değil):

- Düşüş **17 Eyl 02:53**, ~0,7 m hover'da düz uçuşta.
- Düşmeden önceki **13 sn** boyunca motor çıkış farkı **+16 µs → +520 µs**'ye büyüdü, yön **14°** kaydı → kol/gövdenin uçuşta giderek esnediğine işaret.
- **202,4. saniyede** ön-sağ köşe itkisini kaybetti, ardından pervaneler birbirine girdi.
- GPS, pusula, telemetri **yere çarpmadan 0,4-0,5 sn önce, havada** koptu → gövde uçuşta katlandı, kablolar o an koptu.
- Pil/güç/kumanda/GPS/EKF/ayarlarda sorun yok; pilot girişi olayı başlatmadı; pilotun tepkisi (karşı çubuk + 0,8 sn'de disarm) doğru.
- Titreşim, oturumun başından beri önceki uçuşların **2,5-3 katı** — muayeneden geçmiş olmasına rağmen.
- Değerlendirme payı: **gövde/tasarım %70-85**, pilotaj/operasyon %10-25. En olası neden: 3B baskı gövdede gözle görülmeyen iç hasar (katman çatlağı / gevşek bağlantı) ya da gövdenin bu yük için yetersiz dayanıklılığı.
- Yeni kural: düşüş yaşamış baskı parçalar muayeneden geçse de **değiştirilecek**; her ilk kısa hover sonrası log kapısı **VibeZ ≤ 16, motor çıkış farkı ≤ 60 µs** — bu uçuştan önceki kısa hover'ın logu **bu kapıdan zaten geçemezdi**.

**Jetson tarafıyla ilişki:** 02:53 Jetson'ın kayıt boşluğunun (16 Eyl 00:35 → 17 Eyl 10:05) tam içinde — çelişki yok, ama Jetson bu bulgulara ne destek ne çürütme sunabiliyor (§1, §4). İki inceleme **bağımsız** ve **tutarlı**: ikisi de "yazılım/Jetson kaynaklı değil" sonucuna farklı kanıtlardan varıyor.

---

## 8. Kullanılan kanıt komutları

```
journalctl -F _BOOT_ID / --list-boots / _BOOT_ID=<id> -o short-monotonic
last -x reboot | last -x shutdown            # wtmp
find / -newermt "2026-07-28 17:00" ! -newermt "2026-07-28 20:00"
find / -newermt "1970-01-01" ! -newermt "1970-01-02"
sudo cat /var/lib/systemd/pstore/console-ramoops-0 ; ls /sys/fs/pstore
sudo nvme smart-log /dev/nvme0 ; nvpmodel -q ; lsusb
cat /sys/class/rtc/rtc0/hctosys ; hwclock -r --rtc=/dev/rtc0    # RTC mekanizma kanıtı
dmesg | grep -i rtc                                              # "setting system clock to 1970..."
ls -la /usr/lib/clock-epoch /usr/lib/systemd/systemd              # systemd tabanı
apt-get install fake-hwclock ; systemctl list-timers fake-hwclock-save.timer
grep -v '^#' /etc/systemd/journald.conf
```
