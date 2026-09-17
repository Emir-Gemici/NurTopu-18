# Jetson acil devir — 12 Eylül 2026

Halil’in talebi: Claude’un son oturumunu devral, önce Jetson eksiklerini doğrula/gider, ardından üç yerine tek yol altyapısını hazırla.

## Başlangıç kanıtları
- Claude son oturumu: d148f5ad-7fb5-43d0-9b1b-6ce726dfd590; son esas mesaj 2026-09-12 11:16:25 UTC.
- Kaynak HEAD ve fetch sonrası origin/master: bdda2e3b8a13bb01c18a8427b8802b611597a2f7. Dal: jetson/tek-yol-20260912.
- Çalışan paket: /home/n4vitas/proje/NAVITAS_JETSON_20260906/navitas. Git ağacı: /home/n4vitas/proje/github/navitas_github.
- Yeniden koşulan genel kapı: tanısal 15/15, üretim 15/15.
- T220 başlangıç yeniden koşumu: 29 test, 1 başarısızlık, 1 atlama; açılı kabul kümesi özeti uyuşmuyordu.
- Claude tam süit kaydı: 2792 test, 16 başarısızlık, 11 hata, 26 atlama. Bu tarihli kayıt güncel düzeltilmiş ağacın sonucu değildir.
- Claude G4 kaydı: 49/49 karar eş; yalnız 2 kare pozitif rota. Diğer 47 karede rota yok. Gerçek drone 19 karesinin tamamı rota vermedi (18 ölçek yok, 1 uç bant teması yok). Bu denklik kapısı gerçek uçuş başarısı değildir.
- Claude K2 kesilmiş, nihai JSON yok ve süreç kalmamış. Yeniden tam T66 + R denklik koşumu paket results/codex_jetson_20260912 altında başlatıldı.

## Tespit edilen gerçek nedenler
- Açılı küme dosyaları paket/depoda bayt eş. Windows PureWindowsPath sıralaması 735ecc81..., POSIX Path sıralaması b08680e4... üretir. Sebep URETIM_KOMUTU.md sırasıdır; dosya bozulması değildir. Tarihi sıralama taşınabilir hale getirildi; registry/veri değiştirilmedi.
- Aktarım denetimi: codes/comms/scripts/tests/config/simulation ve paket kaynaklarında eksik yok. Tek fark cihazın kendi jetson_derleme_manifest.json dosyası; korunuyor. dataset/test29_v3.yaml eksikti, depodaki dosya kopyalandı. Eski results/jetson_20260906 eksiklerini Claude tamamlamış.
- MuJoCo eksikti; depo ortam kaydındaki 3.13.0 kuruldu. Fizik smoke: mj_step 0.002 saniye, başarılı.
- Paket .git içermez; git izlenme/geçmiş testlerini bu kopyada çalıştırmak yanlış ortamdır. Tam süit kaynak git ağacında ölçülecek.
- /dev/video0, /dev/ttyACM0 ve /dev/ttyUSB0 yok. /dev/ttyTHS1 var; bu bağlantı veya heartbeat kanıtı değildir. Kamera/Pixhawk/SiK saha kapıları halen ÖLÇÜLEMEDİ.

## Tek yol analizi
- Model traversable/blocked ayrımı yapar; sınıfları üç yol kimliğini temsil etmez. Sırf yol sayısı için yeniden eğitim gerektiği kanıtlanmış değildir. Yeni saha başarımı ayrıca ölçülmeli.
- Üretim analyze_path tek rota üretir. Üçlü varsayımlar etiketleme, genişlik reddi, tanısal kapı ve YKS/protokoldedir.
- SERIT_SAYISI=3 değerini 1 yapmak W/3 korumasını W genişliğine çıkarır; açık arazi reddini gevşetir. Küresel sayı değiştirilmez.
- road=1/2/3 mevcut protokolde sol/orta/sağdır. Tek fiziksel yol kimliği bu semantiğe sessizce yerleştirilmez.
- Fiziksel tek koridor mu, üçlü parkurdan tek güzergâh mı sorusu Halil’e iletildi. Yanıt gelene kadar saha geometrisine bağlı üretim değişikliği yapılmıyor; Jetson doğrulaması sürüyor.

Bu ara rapordur; nihai test ve ölçüm sonuçları ayrı sonuç raporuna yazılacak.
