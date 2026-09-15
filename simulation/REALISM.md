# Gerçekçilik geliştirme sürümü

Bu, mevcut üreticinin yerine sessizce geçen bir sürüm değildir. Kaynak kod,
eski `.world` dosyaları ve önceki kayıtlar korunur. Kilitli `world_generator.py`
ve `navitas_anim.cc` değiştirilmez. `realism_scene.py` güncel üreticinin çıktısını
ayrı bir klasöre derler; eski kutulu `rec_kolay.world` geliştirme tabanı değildir.

## Üret ve aç

Depo kökünden; Python ortamında NumPy/OpenCV, masaüstünde Podman/Gazebo imajı gerekir:

```bash
.venv/bin/python -B simulation/scripts/realism_scene.py --output simulation/realism_runs/benim_v1
bash simulation/docker/realism_open.sh simulation/realism_runs/benim_v1/candidate.world
```

Bu makinedeki son doğrulanmış adayı açmak için:

```bash
bash simulation/docker/realism_open.sh
```

Bu komut `realism_runs/current/candidate.world` dosyasını **duraklatılmış** açar.
Eski kayıt başlatıcılarını veya görev dünyalarını değiştirmez. `current` yalnız
doğrulanan bir sürümü gösterir; yeni üretim kendiliğinden etkinleştirilmez.

Çıktı klasörü önceden varsa üretim durur; eski sürümün üzerine yazılmaz.
`realism_runs` üretilmiş büyük mesh/texture/kayıt içerir, Git'e alınmaz.
Tekrar üretim kaynak betikler ve `--seed` ile yapılır. `manifest.json` kaynak ve
varlık SHA-256'larını, seed'i, materyalleri ve geometri künyelerini içerir.

## Uygulananlar

- COLLADA içinde metre ölçeği, yüz normalleri ve gerçek UV koordinatları;
  Ogre materyaline hem script hem doku dizini açıkça verilir.
- Her saha için ayrı seed'li makro değişim, orta ölçekli aşınma/toz, mikro agrega
  ve çatlak dokusu. Üç güzergâh aynı yüzey işleminden geçer; açık yol renkle verilmez.
- Üç alanda 0,5 m aralıklı, santimetre ölçeğinde eğim/aşınma içeren gerçek zemin
  mesh'i; görüntü ve temas aynı yüzeyi kullanır. Bu bir su akış simülasyonu değildir.
- Yol parçalarının üst üste binen renkli dikdörtgenleri yerine tek zemin yüzeyi;
  dış sahada tekrar etmeyen UV kaplaması. Izgara ve neon çerçeve estetiği kaldırılır.
- Kırık plaka, blok, duvar/kolon, tuğla, ahşap, agrega ve paslı içi boş borular.
  Mevcut mesh'ler bağlı katı parçalara ayrılır; dönüş/ölçekleri korunur, yeni
  yerleşimin yatay/düşey kaymaları manifeste yazılır. Mikro parçalar dahil edilir.
- 6 cm destek ızgarasında parçalar zemine veya önceki parçaların üst yüzeyine
  oturtulur. Yükseklik/yer değiştirme maliyeti yapay kule oluşmasını azaltır.
  Tam parça sınırıyla geçit koruması yapılır; açık yolu kesen eski bariyerler
  kapalı yol üzerinde uygun bir noktaya taşınır, kaldırılmaz veya küçültülmez.
- Birleştirilmiş **statik** molozun collision ve visual geometrisi aynı mesh'tir.
  Eski parçaların roll/pitch/yükseklik bilgisini kaybeden collision kutuları kullanılmaz.
- Materyale göre açık sürtünme/restitution tanımı. Bunlar mühendislik başlangıç
  varsayımlarıdır, gerçek sahada ölçülmüş değerler değildir.

Kaynak konumlarıyla karşılaştırma için `--retain-placement` molozun yeni destek
yerleşimini atlar. Varsayılan yerleşim statiktir; fizik motorunda çökme çözdüğü
iddia edilmez. Kütle/atalet bu statik varlıklar için `not applicable` olarak
kaydedilir, ölçülmüş dinamik özellikler uydurulmaz.

## Gerçek motorla karşılaştır

```bash
.venv/bin/python -B simulation/scripts/realism_capture.py \
  simulation/realism_runs/benim_v1/candidate.world \
  simulation/realism_runs/benim_v1/capture_after --label after

podman run --rm --network=none --security-opt label=disable --shm-size=1g \
  -v "$PWD/simulation":/sim:ro \
  -v "$PWD/simulation/realism_runs/benim_v1/capture_after":/evidence:rw \
  navitas-gazebo:11 bash /sim/docker/realism_capture.sh
```

Aynısını `before.world` ve **farklı** çıktı klasörüyle çalıştır.
Üç kamera aynı poz/FOV/çözünürlük kullanır. Çekim kopyasında aktörler sabitlenir,
görev pluginleri/sensörleri çıkarılır; kaynak dünyaya dokunulmaz. Bu kareler
**statik görsel denetimdir**, görev veya sensör doğrulaması değildir. Yeni kare
gelmezse betik sıfır olmayan kodla çıkar; eski kaydı başarı diye göstermez.

## Doğrulama ve sınırlar

```bash
.venv/bin/python -B -m unittest discover -s simulation/tests -p 'test_realism*.py' -v
.venv/bin/python -B codes/test_rota_sentetik.py
.venv/bin/python -B simulation/scripts/realism_geometry_check.py \
  simulation/realism_runs/benim_v1/candidate.world \
  simulation/realism_runs/benim_v1/geometry_check
```

Geometri denetimi, son SDF içindeki collision mesh ve bariyer kutularını bağımsız
olarak 10 cm/piksel maskeye yansıtır. Üç bölgenin dokuz yolunda açıklığı ölçer;
gerekli yarıçapı planlayıcının `R_GEREKLI_M` sabitinden okur. Beklenen açık yol
kapalıysa veya kapalı yol açık görünüyorsa sıfır olmayan kodla çıkar. Bu merkez
güzergâh kontrolüdür; araç dinamiği veya tüm alternatif yolların araması değildir.

Gerçek Gazebo temas testi, ayrı ve yeni bir çıktı klasöründe:

```bash
.venv/bin/python -B simulation/scripts/realism_contact_probe.py prepare \
  simulation/realism_runs/benim_v1/contact \
  --candidate simulation/realism_runs/benim_v1/candidate.world
podman run --rm --network=none --security-opt label=disable \
  -v "$PWD/simulation":/sim:ro \
  -v "$PWD/simulation/realism_runs/benim_v1/contact":/evidence:rw \
  navitas-gazebo:11 bash /sim/docker/realism_contact_probe.sh
.venv/bin/python -B simulation/scripts/realism_contact_probe.py check \
  simulation/realism_runs/benim_v1/contact
```

Temas testi yerçekimi altında düşen, düşey kılavuzlu iki küre kullanır. Molozlu
pozitif kontrol ile molozu çıkarılmış negatif kontrol karşılaştırılır. Yalnız
bir beton yüzeyi ve zemindeki teması sınar; bütün enkazın dengesini kanıtlamaz.

Genel 15/15 kapısı kusursuz maskelerde planlayıcıyı sınar; yeni dünyadaki gerçek
temas, model algısı veya tam görev başarısının yerine geçmez.

Hâlâ bağımsız çalışma/denetim gerektirenler: destek ızgarasının altında kalan
temaslar ve tam rijit-cisim dengesi, tüm sahada penetrasyon taraması, kısmen
gömülü varlıklar, lastik/zemin ve uçuş kalibrasyonu, gerçek araç CAD ölçüleri,
kör gerçek görüntülerde algı gerilemesi, dinamik çökme ve tam görev kapıları.
Donatı görselleri en yakın parça hareketine bağlanır; ayrıca dinamik donatı
modeli değildir. Statik triangle mesh collision dinamik
enkaz simülasyonu değildir. Üç eğitim alanı ve önceki işaret boyutları korunur;
bu paket resmî yarışma sahasının birebir/sertifikalı kopyası olarak sunulmaz.

Motor materyal davranışı: [Gazebo Classic resmî renk/doku açıklaması](https://classic.gazebosim.org/tutorials?cat=&tut=color_model).
