# B3 Yaw / kadraj zarfı — ön kayıt

Tarih: 2026-08-29

Bu metin, `scripts/olcum/162_yaw_kadraj_zarfi.py` ile herhangi bir model
çıktısı veya zarf sonucu üretilmeden önce yazılmıştır. Sonuç görüldükten sonra
ölçüt, örnek seçimi veya gerekli saha aralığı değiştirilmez.

## Dondurulan örneklem ve bozulma ızgarası

- Küme: üretim model defterindeki `profiles.competition.kabul_kumesi`
  (`sentetik_arena_kadraj_t66`).
- Örneklem: manifest sırasındaki, `durum=YAZILDI`, görseli ve etiketi bulunan,
  `arena.acik_serit` alanı boş olmayan ilk **12** kare. Model çıktısına göre
  kare seçilmez veya elenmez.
- Yaw: **-30°..+30°**, 5° adımla (13 değer).
- Kadraj durumları: merkez ile yatay ve dikey eksenlerin her birinde
  **±5%, ±10%, ±15%, ±20%** merkez kayması (17 durum).
- Tam çapraz ızgara ölçülür: **13 × 17** hücre; her hücre aynı 12 temel kareyi
  kullanır. Görüntü ve rasterleştirilmiş YOLO-segment etiketi aynı affine
  matrisle dönüştürülür; görüntüde doğrusal, etikette en yakın-komşu örnekleme
  kullanılır.

On iki uygun girdi bulunamazsa veya temel kararlardan hiçbiri karşılaştırılabilir
bir şerit üretmezse sonuç **OLCULEMEDI** olur; eksik payda sessizce geçişe
çevrilmez.

## Kabul edilebilir zarf

Bir hücre ancak iki koşulu birlikte sağlarsa kabul edilir:

1. rota üretim oranı **>= %90**;
2. bozulmuş karede yayımlanan şeridin aynı karenin bozulmamış üretim kararıyla
   aynı olma oranı **>= %95**.

Rota üretim oranının paydası 12 temel karedir. Aynı-şerit oranının paydası,
bozulmamış üretim kararında şerit yayımlayabilen karelerdir; bozulmuş karede
rota çıkmaması bu paydada **uyuşmazlık** sayılır. Böylece az rota üretip yüksek
şerit doğruluğu gösterme yolu kapalıdır. Okunamayan/eksik girdi hücreyi
`OLCULEMEDI` yapar.

## Sahada sağlanması gereken aralık

Operasyonel gerekli zarf şudur:

- yaw: **-10°..+10°** (uçlar dahil);
- kadraj merkezi: yatayda **-10%..+10%** ve dikeyde **-10%..+10%**; bu görevde
  eksenler ayrı ayrı bozulduğu için zorunlu hücreler merkez, `x±5`, `x±10`,
  `y±5`, `y±10` durumlarıdır.

Bu aralık, tek seferlik test uçuşunda operatörün görsel hizalamayla ulaşması
beklenen ama sıfır hata varsaymayan saha toleransı olarak sonuçtan bağımsız
seçilmiştir. ±30° / %20 taramasının iç yarısını zorunlu tutmak, sınırı ölçmek
için her iki yönde de en az iki ek bozulma basamağı bırakır.

Gerekli aralıktaki **her hücre** yukarıdaki iki eşiği sağlamalıdır; ortalama ile
kötü bir yön gizlenmez.

## Kırılma ve saha sınırı raporlama kuralı

Görev tanımındaki kırılma eşiği ayrıca korunur:

- yaw kırılma açısı: merkez kadrajda, mutlak açı artarken iki işareti birlikte
  değerlendiren grupta rota üretimi **veya** aynı-şerit oranının ilk kez
  **%90'ın altına** düştüğü mutlak açı;
- kadraj kırılma sınırı: yaw=0° iken aynı büyüklükteki yatay/dikey dört yönü
  birlikte değerlendiren grupta bu oranlardan birinin ilk kez **%90'ın altına**
  düştüğü yüzde.

Tarama sonuna kadar kırılma yoksa `>30°` veya `>20%` yazılır; ölçülmeyen daha
geniş alan güvenli ilan edilmez. Saha kontrol listesi önerisi, yalnız kesintisiz
biçimde kabul edilen simetrik aralığın iç sınırını kullanır; tahminle genişletilmez.

## İddia sınırı

Bu ölçüm sentetik kabul kümesinde üretim kararının kontrollü görüntü geometrisi
bozulmasına dayanımını ölçer. Gerçek uçuş, kamera merceği, perspektif, irtifa,
hareket bulanıklığı veya arena domain başarımı için tek başına kanıt değildir.
