# NAVITAS YKİ program teslimi

Bu dal, Windows üzerinde kullanılan iki YKİ varyantını ve bunların geliştirme
bilgilerini birlikte taşır:

- `demo/`: dahili İHA/İKA beslemeli hakem ekranı (`YKS.exe`).
- `new/`: 22 Eylül 2026 tarihli radyo telemetrili NEW paket (`NAVITAS_YKI.exe`)
  ve sistem günlüğü geliştirmesinin kaynakları.

## Önemli paketleme notu

EXE dosyaları PyInstaller **onedir** çıktısından alınmıştır. Kaynak ve EXE bu
dalda vardır; PyInstaller çalışma bağımlılıklarının tamamı (`_internal/`, model
ve eğitim kabul kümeleri) Git deposuna kopyalanmamıştır. Windows'ta geliştirme
ve yeniden paketleme için depo kökündeki Python sanal ortamını kullanın.

NEW paketi model/torch bağımlılıklarını da taşıdığı için mevcut tam onedir
çıktısı yaklaşık 4,8 GB'tır; bu dalda yalnız doğrulanmış EXE, spec ve kaynak
teslim edilmiştir. EXE'nin yanında çalıştırma için tam paket gerekiyorsa Windows
build betiğiyle yeniden üretin.

## Kaynak eşlemesi

| Teslim | Ana kaynak | Giriş noktası |
|---|---|---|
| Demo | `comms/` ve `codes/` | `comms/yks_gui.py` |
| NEW GUI | `yks-programlari/new/source/comms/yks_gui_new.py` | `comms/yks_gui.py` üzerine NEW günlük entegrasyonu |
| NEW günlük | `yks-programlari/new/source/comms/sistem_gunlugu.py` ve `sistem_gunlugu_ui.py` | YKİ içinden `NEW · Sistem günlükleri` |
| NEW Jetson tanısı | `yks-programlari/new/source/scripts/jetson_tani_aktar.py` | `JETSON_NEW_TANI_BASLAT.cmd` |
| Radyo başlatıcısı | `yks-programlari/new/navitas_yki_app.py` ve `radio_mode.py` | `NAVITAS_YKI.exe` |

## Windows'ta çalıştırma

### Demo

```powershell
cd <repo>\yks-programlari\demo
YKS_baslat.bat
YKS.exe --demo
YKS.exe --demo --fda --otokaydet 14 --kapat
```

Demo, sahte İHA/İKA heartbeat ve rota beslemesi üretir; yarışma telsizini
açmaz.

### NEW / radyo

```powershell
cd <repo>\yks-programlari\new
NAVITAS_YKI.exe --help
NAVITAS_YKI.exe --self-test
NAVITAS_YKI.exe --radyo COM7 --baud 57600
NAVITAS_YKI.exe --radyo COM7 --baud 57600 --kamera-url rtsp://192.168.144.25:8554/main.264
```

`--radyo` seçeneği RFD900A/SiK seri portunu açar ve yerel MAVLink tünelini
`127.0.0.1:14590` üzerinden YKİ'ye bağlar. Mission Planner aynı COM portunu
aynı anda açmamalıdır. Bağlantı penceresi EXE argümansız çalıştırıldığında
COM ve baud seçtirir.

NEW geliştirme tanı penceresi yalnız loopback kullanır:

```powershell
cd <repo>
YKI_NEW_TEST_BASLAT.cmd
```

Bu komut gerçek telsiz veya Pixhawk seri portu açmaz. Jetson tanısı salt
okunurdur; parola dosyaya yazılmaz:

```powershell
JETSON_NEW_TANI_BASLAT.cmd fe80::1%%22
```

## Komut satırı sözleşmesi

| Argüman | Anlam |
|---|---|
| `--demo` | Dahili sentetik İHA/İKA beslemesi; yalnız UDP kipinde |
| `--serial COMx` | Doğrudan SiK/RFD900A seri taşıyıcısı |
| `--baud 57600` | Seri baud hızı; varsayılan `57600` |
| `--tunel HOST:PORT` | Mission Planner/yer yönlendiricisi aynası |
| `--radyo COMx` | NEW başlatıcısının radyo kısayolu; tüneli otomatik kurar |
| `--fda` | Final görev akışı panelini açar |
| `--iha HOST:PORT` | UDP İHA komut alıcısı |
| `--ika HOST:PORT` | UDP İKA akranı |
| `--bind HOST:PORT` | YKS UDP dinleme ucu |
| `--kamera-url URL` | Ayrı ağdaki RTSP/HTTP kamera kaynağı |
| `--kamera-etiket METIN` | Hakem ekranındaki kamera etiketidir |
| `--tek-rota` | Tek yol görselleştirmesi |
| `--gorunum saha\|canli\|kamera\|rota\|yerel` | Açılış görünümü |
| `--otokaydet SANI` | Belirtilen saniye sonra ekran görüntüsü |
| `--kaydet-yolu DOSYA` | Otomatik ekran görüntüsü yolu |
| `--kapat` | Otomatik kayıt sonrasında kapanır |
| `--senaryo rc\|yks\|ika\|bat\|gnss\|algi` | Yalnız demo arıza tatbikatı |
| `--tani-dosyasi DOSYA` | NEW Jetson tanı JSON yolu |
| `--sistem-gunlugu` | NEW günlük panelini açılışta gösterir |

Argümanların gerçek doğrulaması için her EXE yanında `--help` çalıştırılmalı;
argüman hatasında uygulama güvenli şekilde kapanır.

## Windows yeniden paketleme

1. Python 3.13 ve sanal ortamı kurun.
2. `pip install -r requirements-windows.txt` (depo kökündeki mevcut Python
   ortamı da kullanılabilir).
3. `windows/build_demo.ps1` ile demo EXE'sini üretin.
4. `windows/build_new.ps1` ile NEW EXE'sini üretin.

Build betikleri kökü otomatik keşfeder; gerekirse `-ProjectRoot` verin.
Çıktıların SHA-256 değerlerini ilgili `SHA256SUMS.txt` dosyalarıyla karşılaştırın.

## Güvenlik ve saha sınırı

NEW `radio_mode.py` doğrudan RFD/MAVLink taşıyıcısıdır. Taze Pixhawk heartbeat'i
geldiğinde İHA uçuş düğmeleri gerçek `COMMAND_LONG` gönderir; YKI yalnız Pixhawk
`COMMAND_ACK` kabulünü güçlü ACK olarak gösterir. GUI'nin iki tık, tazelik ve
ACK sonrası heartbeat güvenlik kapıları korunur. Telemetri bayat veya yoksa
komut gönderilmez.

Bu radyo yolu Pixhawk/İHA içindir. `IKA_GO`, rota ve hakem aktarımı için ayrıca
İKA'yı taşıyan NAVITAS bağlantısı gerekir; bu komutlar doğrudan radyo üzerinden
sahte başarıyla kabul edilmez. Mission Planner aynı COM portunu açmaz; istenirse
yalnız UDP 14550 üzerinden izleyici olarak kullanılabilir.
