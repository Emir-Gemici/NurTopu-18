# YKS canlı kontrolü — 20 Eylül 2026

Kullanıcıyla gerçek YKS ekranında iki aşamalı onay provası yapıldı. Saha dalı
`bilgilendirme-he`, HEAD `324ce42b3e9a7865a8b74d46c4ad0b6f948eed65`.

## Sonuç: USB ağı üzerinden canlı onay yolu GEÇTİ

100 saniyelik koşu: 95 OPEN_ROUTE, 4 NO_ROUTE gönderildi. Hakem günlüğünde
HAKEM_ONAYI_1 ve HAKEM_ONAYI_2 tam birer kez var (19:58:28 ve 19:58:40).
74 farklı OPEN_ROUTE ACK ve 4 NO_ROUTE ACK Jetson'a döndü.
En uzun yeni-seq ACK boşluğu 2,1 saniye; ön kayıt sınırı 10 saniye.
Toparlanmayan NO_ROUTE ve gönderilmemiş seq'e ACK yok. Eşik gevşetilmedi.
Yerel bağımsız kayıt kontrolü dört NO_ROUTE sonrasını ve onay sayısını ayrıca doğruladı.

YKS komutu (gerçek pencere, otomatik onay yok):
```
/usr/bin/python3 -B /home/trs/projects/navitas-wt-bilgilendirme/comms/yks_gui.py --fda --bind 0.0.0.0:5005 --ika 127.0.0.1:5006 --iha 192.168.55.1:5193 --hakem-log /home/trs/projects/navitas-unified-20260822/results/yks_canli_20260920_1959/hakem_log.jsonl
```
Jetson komutu:
```
ssh -o BatchMode=yes -o ConnectTimeout=5 jetson 'python3 -u -B /home/n4vitas/rota_testi_yeniseq.py --hub 192.168.55.100:5005 --dinle-adres 0.0.0.0 --dinle-port 5193 --sure 100 --no-route-her 20 --serit 2 --seq-basla 19000 --kayit /home/n4vitas/onay_testi_codex_20260920_1959.json'
```
Gerçek çıktı: `GECTI`, `gerekce: []`, exit 0. Tam sonuç ve ham zamanlar
`onay_testi.json`; gerçek ekran olayları `hakem_log.jsonl`.
Yerel/uzak test aracı SHA256 eşit:
`5b70bfe314e43bae29d89df72843acebbba6343182be9b3dc391e13c65daa9e5`.

## Diğer gerçek kontroller

- Yeni-seq/askı testleri: 33 test OK, exit 0 (`onay_33.txt`).
- Telemetri akla yatkınlık: 13 test OK, exit 0.
- Bağlantı zayıflığı: 6 test OK, exit 0.
- FDA kipi: 17 test OK, exit 0.
- Ölçüm aracı: 5 test OK, 3/3 mutant yakalandı, exit 0
  (`arac_kendi_testi_ag_erisimli.txt`). İlk sandbox denemesi UDP soket izni
  nedeniyle 5 error verdi; bu ham kayıt da korundu. Öz testler 3 saniyelik
  kendi penceresini kullanır; canlı koşu 10 saniyedir.
- Genel kapı gerçekten denendi: `python3 -B codes/test_rota_sentetik.py`,
  `ModuleNotFoundError: No module named 'cv2'`, exit 1. Başarı sayılmadı.
- Jetson altı servis active/running. Üretim inference NRestarts=0.
  Kamera durumunda yaklaşık 10 FPS, 0 düşen kare, kaynak açık.
- Son üç gerçek model karesinde MASKE_YOK, zemin_px=0, keskinlik=3.2;
  mpp, irtifa, armed, mod ve pixhawk zamanı null. Ham kanıt:
  `jetson_uretim_durumu.txt`. Bu örneklerden tüm sahaya genelleme yapılmaz.

## Kabulün sınırı ve kalanlar

Bu koşu gerçek Jetson, gerçek YKS arayüzü, insan tıklaması ve gerçek UDP
ile yapıldı. Rota test betiğinden geldi; kameradan/modelden üretilmedi.
Telsiz, MAVLink tüneli ve yer yönlendiricisi bu koşuda yoktu.
Üretim servisleri durdurulmadı/değiştirilmedi: üretim ayrı loopback hub'a,
test ise doğrudan laptop 5005'e gönderdi; ACK yalnız test 5193'e yönlendirildi.
Araç kontrol komutu gönderilmedi, üretim kodu değiştirilmedi.

YKS onay kalıcılığı bu kurulumda doğrulandı; tüm sistem saha kabulü değildir.
Sonraki kontroller: gerçek telsizle aynı prova; kamera odağı/gerçek zemin;
Pixhawk telemetrisi ve ölçek; arena referansıyla alan ihlali denetimi.
Commit/push yapılmadı. Bağımsız mimar kabulü veya görev kapatma yapılmadı.

Prova bitiminde yalnız test YKS süreci SIGINT ile kapatıldı; Python
KeyboardInterrupt nedeniyle YKS kapanış kodu 130. Bu kasıtlı kapanıştır;
Jetson ölçüm betiğinin sonuç kodu 0 olarak ayrıdır. Üretim servisleri korunmuştur.
