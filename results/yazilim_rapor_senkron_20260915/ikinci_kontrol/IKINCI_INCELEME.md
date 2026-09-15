# İkinci kontrol — yazılım, deney kanıtları ve önceki düzeltmeler

Bu kontrol önceki incelemenin bazı sonuçlarını doğruladı, iki açıklama eksikliğini ortaya çıkardı ve ek kod/kanıt sınırları buldu. **Önceki Word belgesini “bütün teknik sorunları giderilmiş, teslim onaylı” olarak sunmak doğru değildir.** Bu tur belgeyi değiştirmeyen bir kaynak ve hesap denetimidir; aşağıdaki düzeltme notları önceki incelemeyle birlikte okunmalıdır. Bağımsız kişi/ajan onayı değildir.

## 1. Önceki çalışmamda netleştirilmesi gerekenler

### E01 — 7/15 sonucunun çalışma ayarı eksik anlatılmış

Önceki Word'de 7/15'i ayrı tarihsel deney olarak eklemek doğru; fakat çıkarım boyutunu belirtmemem eksikti. `k3b/v1_15harita_yerlesim_d441.json` ana sonuçları **1024 piksel çıkarım**, conf=0,15 ile elde edilmiş. Aynı kaydın `teshis_imgsz=512` kolu **6/15**. Model ağırlığı iki durumda da v36; model kimliğindeki “512” bütün tarihsel koşuların bu boyutta yapıldığını garanti etmiyor.

15 kaydı yeniden saydım: ana kolda 7 doğru, tanısal 512 kolunda 6 doğru. `H1/README_T214A.md` §1 bunu ayrıca açıklıyor: daha sonraki üretim mozaik 512 ölçümü de tohum 42 için 6/15, fakat **yeniden render edilmiş ayrı karelerden** geliyor. Bu iki 6/15 aynı deney değildir; 7→6 farkını yalnız çözünürlüğe bağlamak da doğru olmaz.

**Word düzeltme notu:** §3.3.3.4 deney tablosunda ve §3.3.4 yerleşim paragrafında “7/15: eski 1024 piksel koşusu; 512 tanısal kolu 6/15; sonraki 512 üretim ölçümü ayrı render” bilgisi bulunmalı. Güncel `simulation/scripts/iha_haritala.py:64–81,325–332` zaten çıkarım=512, tuval=1024 ayrımını yapıyor; güncel kodda hâlâ 1024 çıkarım kusuru var demiyorum.

### E02 — Precision sayıları doğru, kapsamı koşullu

Eklediğim zemin %93,82 / engel %96,77 precision ve %50,87 / %75,87 recall değerleri ham matristen yeniden hesaplandı, doğru. Ancak precision **yalnız gerçek etiketi zemin veya engel olan pikseller üzerinde** hesaplanıyor. Matrisin %39,55'i etiketsiz alan; zemin tahminlerinin %21,22'si, engel tahminlerinin %11,01'i bu alana düşüyor. Bu bölgelerde doğru/yanlış hükmü verilmemiş.

Önceki Word'de dışlama açıklaması var; tablo sütununu “Etiketli alan precision” şeklinde adlandırmak daha açık olur. Sayıları tüm görüntünün, bütün engel nesnelerinin veya görevlerin doğruluk oranı diye sunmayın. Etiketsiz piksellerin tümünü hata saymak da kanıtsız olur.

## 2. Yeni doğrulanan kod ve kanıt bulguları

### E03 — İzleyici bütün seviyeleri atlayınca başarısızlık bildirmiyor

`simulation/scripts/iha_haritala.py:494–524`: her seviyede SCAN_DONE yoksa 1800 s bekleyip `continue` yapıyor; sonunda normal dönüş ve “izleme bitti” mesajı var. `main():556–558` bu dönüşü hata koduna çevirmiyor.

Gerçek `watch` fonksiyonunu değiştirmeden AST üzerinden aldım; yalnız YOLO ve saati taklit ederek boş geçici dizinde çalıştırdım. **3 zaman aşımı, 0 çıkarım çağrısı, normal `None` dönüşü** üretildi. GPU/simülasyon testi değildir; hata bildirim yolunun kontrollü yeniden üretimidir. CLI'nin bu dalı normal dönüş nedeniyle hata çıkışını kendiliğinden oluşturmaz; gerçek rv41 sürecinin geçmiş çıkış kodunu ölçtüğümü iddia etmiyorum.

**Gerekli düzeltme:** seviye bazlı tamamlandı/atlandı/başarısız durumları, eksik değerlendirmeyi belirten süreç sonucu ve bunları sınayan test. Rota bulunamaması ile modelin hiç değerlendirme yapamaması ayrı tutulmalı.

### E04 — Kayıt betiği izleyicinin çıkış sonucunu toplamıyor

`simulation/docker/record.sh:87–91` izleyiciyi arka planda başlatıyor. Son bölümde PID varlığına bakıyor, en çok 60 s bekliyor ve `kill ... || true` uyguluyor; **`wait "$WATCHER_PID"` ile çıkış kodu alınmıyor**. Hakem logu yedeği de `|| true` ile hatayı bastırabiliyor. Sonra “Kayıt tamam” yazılıyor.

Bu, videonun oluştuğu fakat algı değerlendirmesinin eksik kaldığı bir kaydı tamamlanmış algı testi sanma riskidir. Kaynak incelemesiyle doğrulandı; bu tur canlı konteyner arızası enjekte edilmedi. İKA'nın yanlış rota sürdüğü veya tehlikeli davrandığı sonucu buradan çıkmaz.

**Gerekli düzeltme:** video, algı ve hakem çıktılarının ayrı tamamlanma durumları; alt sürecin çıkış kodunun toplanması; gerekli dosyalar/istenen seviyeler eksikse açık eksik sonuç.

### E05 — Veri kümesi “SHA-256” parmak izi içerik özeti değil

`scripts/olcum/176_piksel_karisiklik_matrisi.py:96–104` yalnız dosya adı + byte sayısını özetliyor. Ham ölçüm JSON'u bu sınırlamayı zaten yazıyor. Deney: aynı `label.txt` dosyasını `AAAA` → `BBBB` değiştirdim. İçerik SHA'sı değişti, bu fonksiyonun parmak izi **değişmedi**.

Bu, veri değiştirilmiş demek değildir. İki tarafta aynı bu parmak izinin görülmesi, görüntü/etiket içeriklerinin aynı olduğunu kanıtlamaz. Model dosyası için yaptığımız gerçek içerik SHA denetimi bundan farklıdır.

**Gerekli düzeltme:** yeni teslimlerde dosya başına içerik SHA'sı içeren ek manifest; tarihsel özeti sessizce değiştirmemek. Böylece Emir'le aynı boyutlu fakat farklı içerikli etiketler kullanılması ihtimali kontrol edilebilir.

### E06 — v36 seçimi bütün kabul ölçütlerini geçmiş olma anlamına gelmiyor

`config/model_registry.json → profiles.competition._surum_karari` ve `CONTRACTS.md §12`: v36, 26 Ağustos kullanıcı kararıyla seçilmiş; ilgili gerçek kare kabulünde ROTA≥10 / MASKE_YOK≤10 karşılanmamış (**8 / 16**). Terfi istisnası açıkça kayıtlı. Bazı hata türleri v35'e göre iyileşirken bazıları kötüleşmiş; kayıt defteri bu bedelleri yazıyor.

**Doğru ifade:** “v36 seçili üretim modelidir; seçim kayıtlı ödünleşim ve istisna içerir.” “v36 her ölçütte en iyidir” veya “seçili olduğuna göre bütün kabul kapılarını geçti” savunulamaz. Bu inceleme model seçimini değiştirmez ve v37'ye terfi önermez.

### E07 — 29 kare, 29 bağımsız görev veya arena testi değil

Piksel JSON'u `DJI_20260822172613_0038_D` çekiminden 29 kareyi, 512/conf=0,30 koşulunu tanımlıyor. CONTRACTS §12 bunları eğitim/erken durdurma dışında tutulan **doğrulama** kümesi olarak tanımlar. Dosya yolunda `test` geçmesi tek başına bağımsız yarışma testi anlamına gelmez. Kayıt defteri bu kırsal çekimde kırmızı H, moloz yığını ve bariyer bulunmadığını da açıkça sınırlar.

Dolayısıyla %71,81 etiketli piksel doğruluğundan arena görevinin yeterliliği çıkmaz. Bu, görüntü işleme hiç çalışmıyor demek de değildir; ölçümün kapsamını korumaktır.

### E08 — “105 koşum” tek bir modelin 105 bağımsız deneyi değil

`H1/kosum_tur3/*_*_*_*.json` dosyalarını yeniden saydım: **45 yer gerçeği + 45 model-mozaik + 15 kare tabanlı = 105 sonuç kaydı**. Başarılar sırasıyla **45, 9, 0**. İlk iki kol 15 harita/seviye kombinasyonunun üç tohumla ölçümleri. 9/45, harita bazında üç tohumun da başarılı olması ölçütünde **0/15**.

Sonuç kaydı sayısı ile fiilen hareket eden araç sayısı da aynı değil; NO_ROUTE kayıtları var. Bu 105'i “model 105 görevde sınandı” veya 45/45 yer gerçeğini “model kusursuz” diye sunmayın. Eski `H1/kosum/README_T213B.md` 33/45 ve 0/45; yeni `README_T214A.md` 45/45 ve 9/45 veriyor. Bunlar ayrı tarihsel deneyler; yanlış klasörden alıntı yapmak sahte bir çelişki üretir.

## 3. Sohbette söylenen ile bizim yorumumuz

- 15 Eylül 20:25:44 mesajında 12/15, **ön kayıt eşiği** olarak yazılmış. 20:39:29 mesajı “v37 en güncel, en iyisi v36” diyor. İncelenen aralıkta Emir'in “güncel model 12/15 başarı veriyor” dediği bir mesaj yok. Bu söz ona atfedilmemeli.
- %75,87 gerçek engel pikselinin engel tahmini alma oranı ve %0,65 gerçek engel pikselinin zemin tahmini alma oranı **ham matrisle uyumlu**. Bu iki sayıyı yanlış diye reddetmek doğru olmaz. Bu sayılardan tek başına “görev için yeterli” sonucu çıkarmak ise desteklenmiyor; %23,48 tahmin-yok ve zemin recall'ı %50,87 de aynı ölçümün parçaları.
- Modeli ve sahneyi ayırma düzeltmesi geçerli. Sohbetin v1/v2/v3'ü model sürümü gibi yorumlaması, kaynak K3B varyant tanımlarıyla uyuşmuyor.
- Eski metinlerin yeni DOCX'lere taşınması kanıtlı; bunu belirli kişinin okumadan kopyaladığına veya yanlış model kullandığına bağlayan kanıt yok.

## 4. Yeniden kontrol edilen önceki işlemler

- Önceki kanıt dosyasındaki mevcut **16 dosyanın içerik SHA'ları** yeniden eşleşti; kaynak Word, model ve mevcut üretim katkıları korunmuş.
- Düzeltilmiş Word ile kaynak Word arasında yalnız `word/document.xml` farklı. **124 medya parçası ve diğer ZIP parçaları aynen korunmuş.** Bu içerik korumasıdır; görsellerdeki tarihsel motor bilgileri kendiliğinden güncellenmiş değildir.
- 29 karenin tek tek matrislerini topladım; toplam matrisle birebir. Eklenen precision/recall hesabında aritmetik hata bulunmadı.
- 105 sonuç JSON'u yeniden sayıldı; 45/45, 9/45, 0/15 doğrulandı. Yeni model çıkarımı yapılmadı.
- Yerel HEAD `ab906f3a`, kayıtlı `origin/master` `0a043107`; ayrışma `0 7`. Bu tur canlı uzak sunucu tekrar sorgulanmadı; “uzak şu anda kesin aynı” iddiası yok. Önceki canlı gözlem kendi zamanına aittir.
- Önceki görsel kontrol tüm sayfaların küçük önizleme taraması + değişen sayfaların ayrıntılı kontrolüydü; **179 sayfanın tamamının %100 yakınlaştırmada bağımsız denetimi değildi**. “Kusursuz nihai teslim” onayı sayılmaz. Bu tur yeni render yapılmadı.

## 5. Tekrarlanabilir doğrulama

Komut (depo kökünde):

```sh
python results/yazilim_rapor_senkron_20260915/ikinci_kontrol/dogrula.py
```

Gerçek çıkış kodu: **0**. Çıktı `dogrulama.log`, hesaplar ve kaynak SHA'ları `dogrulama.json` içindedir. 0, bu denetim beklentilerinin sağlandığı anlamına gelir; izleyici kusurunun düzeldiği anlamına gelmez. Bu tur üretim kodu değiştirilmedi; model/saha/HIL koşulmadı; commit/push yapılmadı.

## 6. Öncelik sırası

1. Word'ün 7/15 satırına 1024/512 ayrımını ve precision başlığına etiketli alan kapsamını geçirmek; yeniden sayfalama ve görsel kontrol yapmak.
2. İzleyici/kayıt tamamlanma ve hata kodu zincirini düzeltmek; zaman aşımı, model çökmesi, eksik seviye ve başarılı tam akış testlerini koşmak.
3. Paylaşılacak deney paketine dosya içeriği SHA manifesti eklemek; kod/model/deney/Word kimliklerini aynı teslim kaydında eşlemek.
4. Sonuçların karşılaştırılacağı ortak çıkarım ayarlarını sabitleyip gereken yeni deneyleri koşmak. Tarihsel sayıları bu yeni deneyle karıştırmamak.
