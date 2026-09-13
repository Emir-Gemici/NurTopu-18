# İKA / mancınık / İHA Gazebo model önizlemesi — 13 Eylül 2026

## Yöntem

Bu Linux geliştirme makinesinde `gazebo`/`gz`/`rosrun`/`roslaunch` kurulu değil
(sadece `dnf` mevcut, Fedora resmi depolarında Gazebo/gz paketi yok). Repoda
zaten mevcut olan `simulation/docker/Containerfile` imajı (`navitas-gazebo:11`,
gerçek OSRF Gazebo Classic 11) `podman` ile kullanılarak **gerçek** bir
headless Gazebo11 render'ı üretildi — bu bir sahte/sentetik görüntü değildir.

1. Her paketin URDF'si `gz sdf -p <urdf>` ile SDF'e çevrildi (konteyner içi).
2. Üç model + `sun` + `ground_plane` + 4 kamera sensörü (`<save>` ile JPG
   yazan) içeren `onizleme.world` derlendi (`build_world.py`).
3. `Xvfb` + `gzserver --verbose onizleme.world` headless çalıştırıldı,
   kameralar `/evidence/<isim>/*.jpg` yazdı.
4. `GAZEBO_MODEL_PATH`'e gerçek Gazebo'nun varsayılan model yolu
   (`/usr/share/gazebo-11/models`, sun+ground_plane için) **eklendi** —
   ilk denemede bunu ezmiştim, ışık/zemin yüklenmedi (düz gri, gölgesiz
   çıktı); düzeltilince gölge ve gökyüzü doğru rendered oldu.

## Sonuç dosyaları

- `iha_gazebo.jpg`, `mancinik_gazebo.jpg` — düzgün oturmuş, tek parça,
  3/4 açı, gölgeli gerçek Gazebo render'ı.
- `ika_gazebo.jpg` — **kasıtlı olarak "bozuk" bırakıldı**: bu paketin
  URDF eklem verisi D-458'de zaten kusurlu bulunmuştu, render bunu
  doğruluyor (gövde iki parçaya bölünmüş görünüyor, tekerler gövdeye
  bağlı değil). Bkz REVIEW_LOG.md D-477.
- `uc_model_birlikte_gazebo.jpg` — üç modelin aynı sahnede genel görünümü.
- `onizleme.world`, `build_world.py` — üretimi tekrarlamak için.

## Bulgular (REVIEW_LOG D-477'ye işlendi)

1. **İKA kütle/mesh kusuru (D-458) bağımsız doğrulandı** — artık gerçek
   Gazebo render'ıyla da görülüyor, sadece CSV okumasıyla değil. T239
   hâlâ açık, CONTRACTS değişmedi.
2. **Paket adı uyuşmazlığı → DÜZELTİLDİ (T261, D-479, aynı gün).**
   `IKA_GAZEBO_MODEL` ve `mancinik_gazebo_model` klasörlerinin URDF'leri
   mesh'lere SolidWorks montaj adıyla (`İKA_GAZEBO_MODEL` noktalı İ,
   `mancınık montaj.SLDASM`) referans veriyordu — gerçek klasör adıyla
   eşleşmiyordu (bu render'da elle symlink ekleyerek aşılmıştı). Dosyalar
   ASCII isme taşındı, package.xml/CMakeLists.txt/URDF/launch içindeki
   tüm ad referansları düzeltildi. Doğrulama: gerçek Gazebo11'de symlink
   OLMADAN `GAZEBO_MODEL_PATH=/repo` ile mesh'ler artık doğrudan bulunuyor.
3. Mancınık ve İHA CSV'lerindeki kütle/atalet değerleri link başına
   farklı ve büyüklük mertebesi makul (İKA'nın aksine, ki orada tüm
   linkler aynı 9,308 kg'ı taşıyor).

## SolidWorks kaynağı üzerinden bağımsız değer kontrolü

Bu üç paketin URDF/STL/CSV'leri SolidWorks'ten **dışa aktarılmış türev**
dosyalar — orijinal `.SLDASM`/`.SLDPRT` değil. Native SolidWorks dosyalarını
CAD çekirdeği olmadan (bu ortamda yok) açamıyorum. Kullanıcı Drive klasörünü
paylaştı (native `.SLDASM`/`.SLDPRT`/`.STEP` dosyaları + parça listesi
`.xlsx`/`.xlsm` dosyaları) — CAD dosyalarını hâlâ açamıyorum ama parça/malzeme
listeleri düz veri (xlsx/xlsm), onları okuyup İKA kütle iddiasını bağımsız
doğruladım (bkz D-478):

- `İKA/IKA_Sase_Malzemeleri.xlsx` (şasi/mekanik parça listesi): toplam
  **5617,4 gram**.
- `İKA/ika.xlsm` (elektronik/aviyonik liste): toplam **3,784 kg**.
- **Toplam = 9,4014 kg** — D-458'in bahsettiği DDR 9,4 kg ile tam örtüşüyor.
- URDF'nin "her tekerlek 9,308 kg" iddiası bu ışıkta **sayısal olarak
  imkânsız** (tek tekerlek ≈ aracın tamamı kadar ağır çıkıyor). D-478'e
  işlendi, T239 hâlâ açık (gerçek tekerlek kütlesi hâlâ ölçülmeli).
