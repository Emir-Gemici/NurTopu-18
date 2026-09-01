# T198 kalan iş — HB ŞEKİL DOĞRULAMASI · ön kayıt

Tarih: **2026-09-01** — hiçbir şekil puanı dağılımı ölçülmeden önce yazıldı
(D-107). Kural: aşağıdaki tanım ve türetme kuralı, sonuç görüldükten sonra
değiştirilmez; ayrışma sağlanamazsa hüküm **AYIRAMIYOR** olarak yazılır ve
kapı bağlanmaz.

## 0. Kapatılan boşluk

D-295/T150 ölçtü: dedektör 67 gerçek otopark karesinin **67'sinde** kırmızı
OTOMOBİLİ HB sandı; 111 kırsal karede 15 kez kırmızımsı toprağı. T198'in
ölçek denetimi (D-344) riski azalttı ama **doğru boyuttaki** sahtekârı
ayıramaz (D-351: ~50 m'de otomobil bandı kıl payı geçiyor). Kalan iş
defterde açık: *"kırmızı H HARFİNİN KENDİSİNİ doğrulayan bir ölçüt."*

⚠ Renk sorusu (şartname metni "kırmızı H", figürü akromatik ped) **insan
görevi H-E'dir** ve bu iş onu ÇÖZMEZ; şekil ölçütü, `hb_maskesi` hangi rengi
anahtarlarsa anahtarlasın harf/halka yapısını blob'dan ayırır.

## 1. Neyin şekli? — maskenin değil, HAM kırmızının

`hb_maskesi` bilerek **kutu doldurur** (şartname "bölge" ister) ve genişlik
oranlı morfolojik kapama uygular — çıktısında şekil bilgisi YOKTUR (bugün
ölçüldü: poster önizlemesi tek parça, solidity 1,0). Şekil puanı bu yüzden
**ham kırmızı maskeden** hesaplanır: kroma eşiği + bariyer çıkarması
uygulanmış, **kapama ve kutu doldurma uygulanmamış** katman.

## 2. Dondurulan puan tanımı

Aday kutusu içinde:
1. Ham kırmızı pikseller alınır; `minAreaRect` ile baskın yönelime
   **ters döndürülür** (nadir bakışta ped ~afin; gimbal 90°).
2. Sıkı kırpılıp **128×128** tuvale ölçeklenir.
3. **Şablonla IoU** hesaplanır; şablon, kendi basılı posterimizin geometri
   SAYILARINDAN çizilir (`results/hb_baski/OKUBENI.md` — matbaa föyü):
   çerçeve kalınlığı **%4,58** · H dış kutusu **%40,5 × %48,2** (ortalanmış) ·
   kol kalınlığı **%9,55**. Önizleme PNG'sinden ÇİZİLMEZ (kendi kendini
   sınamak çevrimsel olurdu); sayılardan çizilir.
4. H, 90°'ye kadar yönelim belirsizliği taşır: IoU **0/90/180/270**
   döndürmelerinin en büyüğüdür.

Puan ∈ [0,1]. Tek yönlü kullanılır: **alt sınırın altı HB DEĞİLDİR.**

## 3. Eşik türetme kuralı — D-344'ün (ölçek bandı) kalıbı

- Pozitifler: t66 kümesinin 260 sentetik pedi, **aynı aday hattından**
  geçirilerek (üretimle aynı seçim; yer gerçeği kutusu değil).
- Alt sınır = pozitif puanların **%0,5 dilimi × 0,85 payı**.
- Sayı bu kuralla ölçümden TÜRETİLİR; kural şimdi, sayı sonra. Kural
  sonuca bakılarak değiştirilmez.

## 4. Kabul ölçütleri — SONUÇ GÖRÜLMEDEN

- **P1 (fail-closed korunur):** türetilmiş alt sınır pozitiflerin en az
  **258/260**'ını (%99,2) tutmalı. Tutmuyorsa eşik SIKILAŞTIRILMAZ,
  hüküm **AYIRAMIYOR** yazılır.
- **N1 (otomobil):** T150'nin 67 otopark tespitinden şekil kapısını geçen
  **≤ %10** olmalı (bugün %100).
- **N2 (toprak):** kırsal 15 yanlış pozitiften geçen sayısı raporlanır
  (bilgi; kapı N1'dir — otomobil, rotayı yanlış hedefe götüren senaryodur).
- P1 ve N1 birlikte sağlanmazsa şekil kapısı **bağlanmaz**; ölçüm ve
  ayrışamama defterde kalır.

## 5. Kapsam ve çevrimsellik

- Pozitifler **sentetiktir** ve dedektörün geliştirildiği üretecin çizimidir
  (D-295'in çevrimsellik uyarısı aynen geçerli). Basılı poster, üretecin
  ölçülmüş geometrik ikizidir (OKUBENI: ölçüler üreteçten alındı) — yani
  30 Eylül testindeki gerçek ped bu şablonun kendisidir. **Yarışma
  organizasyonunun pedi ise bilinmiyor** (H-E açık); bu ölçüt onun için
  yalnız "H benzeri yapı / düz blob" ayrımı kadar genellik iddia eder.
- Geriye dönük uyum: `hb_konumu(..., sekil_esigi=None)` — verilmezse
  davranış BUGÜNKÜYLE AYNI. Üretime bağlama (T150) mimar kararıdır.
- Madde 15: şekil denetimi yalnız aday REDDEDEBİLİR → `HEDEF_YOK`
  çekimserliği artar → fail-closed. Serbest alana dokunmaz.
