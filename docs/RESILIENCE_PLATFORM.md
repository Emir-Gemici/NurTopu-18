# Navitas Dayanıklılık Platformu

Bu belge yarışma çalışma zamanındaki kritik sözleşmeleri tanımlar. Amaç, model
metriği ile sahada çalışan artefaktın, algı çıktısı ile İKA rotasının ve simülasyon
başarısı ile gerçek görev başarısının birbirine karışmasını önlemektir.

## Model sözleşmesi

Tek kaynak `config/model_registry.json` dosyasıdır.

- `competition`: v4 PyTorch, 640 px, SHA-256 doğrulamalı. Raporlanan RescueNet val
  mask mAP50 değeri 0.6751'dir.
- `rpi_ncnn`: v2 NCNN, 512 px. Düşük güç fallback'idir; competition profiliyle
  metrik-eşdeğer değildir. v4 NCNN export/parity kapısı geçmeden “güncel model”
  olarak sunulmamalıdır.

Runtime bilinmeyen profil, eksik artefakt veya hash uyuşmazlığında kapalı biçimde
hata verir. Deneysel `--model` yolu bilinçli bir operatör override'ıdır.

## Güvenli rota sözleşmesi

`codes/path_planning.py` şu sırayı uygular:

1. traversable maskeyi morfolojik olarak temizler;
2. blocked maskeyi araç açıklığı kadar genişletip geçilebilir alandan çıkarır;
3. yalnız İKA başlangıç bandına bağlı ve hedef bandına uzanan bileşeni kabul eder;
4. yeterli açıklıkta waypoint üretilemezse `road=None` ile fail-safe olur.

Geometrik güven skoru model confidence değildir. İkisi raporlarda ayrı tutulmalıdır.

## Haberleşme sözleşmesi

Protokol v2; newline JSON taşımasını korurken şunları zorunlu kılar:

- CRC32 bütünlük kontrolü;
- mesaj tipi, sürüm, sayı, koordinat ve waypoint sınırları;
- 16 KiB çerçeve/tampon sınırı;
- boot session + sequence tabanlı tekrar/eski mesaj reddi;
- ACK'in rota session'ına bağlanması;
- seri SiK hattında da teslim ACK'i.

CRC32 kimlik doğrulama veya şifreleme değildir. Düşmanca radyo ortamı için sonraki
kapı PSK-HMAC/AEAD ve anahtar yönetimidir.

## Simülasyon kanıt sözleşmesi

- Model bir rota üretemediyse ground-truth ile başarıya çevrilmez.
- Worker exception görev sürecine başarısız exit kodu olarak taşınır.
- İKA waypoint'leri seçilen senaryo/map dünya origin'ine çevrilir.
- OPEN_ROUTE koordinatları varsa arena ground-truth rotasından önce gelir.
- Görev süreleri limit altına zorla kırpılmaz; ham değer ayrıca değerlendirilir.

## Doğrulama

```bash
python -m unittest discover -s tests -v
python -m compileall -q codes comms dataset drone simulation tests
bash -n simulation/launch/navitas.launch simulation/launch.sh simulation/docker/*.sh
python -m comms.test_comms
```

CI aynı çekirdek testleri ve örnek dünya XML üretimini her push/PR'da çalıştırır.

## Sonraki kalifikasyon kapıları

1. v4/640 için NCNN veya TensorRT export; PT/export maske IoU ve rota parity testi.
2. Kilitli, bağımsız arena test seti ve blocked recall/IoU + görev başarı metriği.
3. İKA `WAIT_GO -> MOVING -> LINK_LOST` durum makinesi ve sürekli heartbeat.
4. Kamera homografisiyle piksel waypoint'lerin metre koordinatına kalibrasyonu.
5. RF saha testi, gecikme/kayıp ölçümü ve kimlik doğrulamalı protokol v3.
