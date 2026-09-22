# NAVITAS YKI NEW

Geliştirme kopyası: `O:\navitas-YKI-NEW`  
Dal: `yki-new-gunluk-20260921`  
Eski çalışma kopyası: `O:\navitas`.

Bu kopya mevcut yerel değişikliklerle oluşturuldu. Oluşturma sırasında 756 dosya SHA-256 ile doğrulandı. Git çalışma ağacıdır: kaynak dosyaları ayrıdır, Git geçmişi ana depoyla ortaktır. Büyük video/veri koleksiyonunun ve cihaz ayarlarının tam yedeği değildir.

Kaydedilmemiş değişikliklerin ayrıca ZIP yedeği: `O:\navitas\results\yki_kopya_20260921\yerel_degisim_yedegi.zip`. Başlangıç manifesti aynı klasördedir. İlk oluşturma adı `navitas-yki-gelistirme` idi; kullanıcının NEW talebiyle klasör ve dal yukarıdaki adlara taşındı.

## Açılış

`YKI_NEW_TEST_BASLAT.cmd` dosyasını çalıştır. Pencere başlığında **NEW** görünür; **NEW · Sistem günlükleri** düğmesi tanı penceresini açar.

Bu başlatıcı yalnız PC'nin `127.0.0.1:15991–15993` bağlantı noktalarını kullanır. Radyo veya Pixhawk seri portunu açmaz. İHA/Pixhawk sinyalinin bu izole testte görünmemesi beklenir. Gerçek uçuş başlatıcısı değildir. Mevcut saha başlatıcısı ve çalışan ana kopya değiştirilmedi.

Yeni kod yüklenmeden açık kalmış NEW penceresi varsa, son değişiklikleri almak için yalnız NEW penceresini kapatıp bu başlatıcıyla tekrar aç.

## Jetson tanısı

Jetson USB bağlantısı kullanılabilir olduğunda `JETSON_NEW_TANI_BASLAT.cmd` çalıştır. Parola terminalde gizli istenir; dosyaya kaydedilmez. Varsayılan USB adresi `fe80::1%22`; arayüz numarası değişirse doğru adresi ilk argüman olarak ver.

Eşdeğer Python komutu (NEW klasöründe):

```powershell
& 'O:\navitas-local-train\venv\Scripts\python.exe' -X utf8 -B scripts/jetson_tani_aktar.py --host 'fe80::1%22'
```

Aktarım salt okunurdur: mevcut sağlık dosyası, servis durumları ve mevcut açılışa ait son 80 ilgili journal kaydı okunur. Uçuş/servis komutu veya Jetson'a dosya kurulumu yapılmaz. İnternet gerekmez. Bilinmeyen SSH sunucu anahtarı otomatik kabul edilmez.

Canlı tanı dosyası: `results/canli_tani/jetson.json`. Aktarımın kalıcı JSONL kaydı aynı klasörde. Aktarımı durdurmak için terminalde Ctrl+C kullan; ekran kısa süre sonra veriyi bayat gösterir. Çok hızlı günlük üretiminde bu son 80 kayıt penceresi tam journal yedeği sayılmaz.

21 Eylül son bağlantı denemesinde Jetson USB ağ arayüzü mevcut değildi; WinError10051 alındı ve tekrar denemesi durduruldu. Canlı başarılı aktarım henüz bu yeni araçla doğrulanmadı. Bu olay güç arızası kanıtı değildir.

## Günlük penceresi

- Jetson yanıtı, modelin kare işlemesi, kameranın kare üretmesi ve algı sonucu ayrı gösterilir. `MASKE_YOK` tek başına cihaz veya model süreci çöktü demek değildir.
- Pixhawk tazeliği mevcut YKİ telemetri durumundan alınır. Yeni bir seri port sahibi oluşturulmaz. Bayat mod/ARM/pil değerleri güncelmiş gibi gösterilmez.
- Arama ve kaynak filtresi, okunur günlük satırları, ham alanlar seçeneği ve otomatik kaydırmayı kapatma vardır.
- **Geçmiş kayıt aç:** JSONL/metin, Pixhawk DataFlash `.bin` veya MAVLink `.tlog` dosyaları. Arşiv üstteki canlı sağlık durumunu değiştirmez.
- Arşiv görünümü seçilen olayların son 2.000 satırını gösterir; metin dosyalarında en fazla son 8 MiB taranır. Pixhawk kaydında mesaj, hata, olay, mod ve güç/pil türleri seçilir. Bu görünüm bütün uçuş parametrelerinin analiz aracı değildir.
- **Görüneni dışarı aktar:** seçili/filtreli satırları JSONL kaydeder. Canlı panel olayları da yeni prova klasöründe ayrı `sistem_gunlugu_*.jsonl` dosyasına yazılır.

## Doğrulama ve açık işler

`results/new_dogrulama/checks.json` ve komut çıktıları gerçek kanıttır:

- 94 ilgili test geçti; üçü gerçek Tk panelinde canlı→bayat, bağlantı yok, boş arşiv ve kapanış yollarını sınar.
- Genel rota kapısı: iki kol 15/15, çıkış 0.
- Gerçek 19 Eylül Pixhawk `.bin` dosyasında 265.253 mesaj okundu; seçili son 2.000 kayıt sunuldu. Kaynak dosya salt okunur açıldı.
- Mevcut YKİ JSONL günlüğü de arşiv okuyucusunda açıldı.
- NEW ana pencere açılışı ve NEW ibaresi gözlendi. Günlük penceresinin bütün DPI/ekran boyutlarında görsel yerleşim kabulü ayrıca yapılmalı.

Pixhawk bağlı değil; Jetson yeni aktarım için yeniden bağlanmalı. Donanım üstünde arıza enjeksiyonu, bağımsız RTL/iniş, saha uçuşu ve başarılı canlı tanı aktarımı bu geliştirmeyle tamamlandı sayılmaz.

Tam depo test paketi yeniden çalıştırılmadı; önceki tam paket hataları hâlâ açık. Bağımsız kod denetimi ve tam paket kapısı tamamlanmadan üretime geçiş/push yapılmadı. Mevcut kamera ve uçuş ayarları değiştirilmedi.
