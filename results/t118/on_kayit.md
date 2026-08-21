# T118 · ÖN KAYIT — üretim tavanının ÜRETİMDEKİ modele olan payı

> ⚠ Ölçümlerden **ÖNCE** yazıldı (D-107). Hüküm kuralları sonuca göre gevşetilmez.

## 0. Defter araması (D-252) — ÖNCE ARANDI, BULUNDU
`T118` defterde **10 yerde** geçiyor. Görevin **ölçüm kısmı BİTMİŞ**:
- **D-208 §1** (filo, 0/3 çürütücü): 67 otopark karesinin **67'sinde** üretim
  zinciri `zemin_maskesi_reddi` tetikliyor; üretim ölçüsü (İÇERİK paydası)
  medyan **0,800** > `ZEMIN_KAPLAMA_TAVANI` **0,67**. Denetçinin ~0,45'i aynı
  maskenin tuval-paydalı hâli (oran 0,5625).
- **D-208 §2** (sentez, 0/3): ~171 aday satırda **kod-içi payda uyuşmazlığı 0**;
  ama 6 dosya letterbox/ham paydalı değeri "kaplama" **adıyla** raporluyor.
- **D-214**: o 6 değerin **tüketimi** izlendi → **eşik/karar bozulması SIFIR**
  (eşiğe giren kıyaslar payda-sadeleşen oranlar). Kalan iş bir **adlandırma
  önerisidir ve kararı mimarındır.**
⇒ **Bu ölçümleri TEKRARLAMIYORUM.** Kuyruk satırı bunları yansıtmıyor (bayat).

## 1. TEKRAR OLMAYAN, ÖLÇÜLMEMİŞ SORU
D-208'in "67/67 ret" dayanağı **v34 dönemine** aittir. **2026-08-21'de üretim
v35'e geçti (T130/D-256).** Registry v35 için gerçek kare kaplamasını
**içerik paydasıyla 0,5076** yazıyor — yani **tavanın (0,67) ALTINDA**.
Mimar D-255 §2'de `t127_temiz` için *"67 gerçek karede red 0"* ölçmüş.
**Ölçülmemiş olan:** bu 0 redin **PAYI** — kareler tavana ne kadar yakın?
`red 0` ikili bir sonuçtur; 0,669'da duran bir küme ile 0,30'da duran bir küme
aynı "0" değerini verir ama saha riski **taban tabana zıttır** (Jetson 30 Eylül,
cihaz-öncesi doğrulama penceresi YOK — D-211).

## 2. Ölçüm
`codes.karar_sozlesmesi`'nin **kendi** fonksiyonları içe aktarılır (kopya YOK):
`zemin_kaplamasi` · `zemin_kenar_dayanmasi` · `zemin_maskesi_reddi`.
67 gerçek kare (`data/raw_frames/*.jpg`), model **registry'nin gösterdiği yerden**
(`resolve_model()`), maske üretimi denetçinin yolundan (`_preprocess` +
`_maskeleri_icerige_kirp`) — yani T131'de **bayt-eş olduğu ölçülen** yol.
İki model koşulur: **v35 (üretim)** ve **v34 (yedek)**; v34 D-208'in sayısını
yeniden üretirse alet doğrulanmış olur.

⚠ Ret **İKİ koşulun VE'sidir** (`karar_sozlesmesi:577-582`):
`kaplama > 0,67` **VE** `kenar_dayanmasi > 0,50`. İkisi de ölçülür; yalnız
kaplamaya bakmak D-208'i yanlış okumak olurdu.

## 3. HÜKÜM KURALLARI (önceden yazıldı)
- **H1 (alet doğrulaması):** v34 için ret sayısı **67/67** çıkmalı ve içerik
  paydalı kaplama medyanı **≈0,800** olmalı. Çıkmazsa **aletim yanlıştır** ve
  v35 sayılarını yayımlamam — önce aleti onarırım.
- **H2 (asıl soru):** v35 için ret sayısı **0/67** çıkarsa D-255 §2 bağımsız
  olarak doğrulanmış olur. Farklı çıkarsa **farkı yazarım** ve mimarın sayısını
  düzeltmem — **iki ölçüm çelişirse hakem üçüncü bir koşumdur**, benim hükmüm değil.
- **H3 (yeni bilgi — pay):** v35'in içerik paydalı kaplamasının **dağılımı**
  (min · medyan · maks) ve tavana en yakın karenin payı raporlanır.
  - maks < 0,60 ise → tavan **uzak**, saha riski düşük.
  - 0,60 ≤ maks ≤ 0,67 ise → 🔴 **tavan YAKIN**; bu bir uyarıdır, kapı değil.
  - maks > 0,67 ise → en az bir kare tavanı aşıyor demektir; o zaman "red 0"
    ancak **kenar koşulunun** kurtardığı anlamına gelir ve bunu ayrıca yazarım.

## 4. YETKİM OLMAYAN ŞEYLER (§9.2 · görevin kendi kısıtı)
`ZEMIN_KAPLAMA_TAVANI` (0,67) ve `ZEMIN_KENAR_DAYANMA_TAVANI` (0,50)
**değiştirilmez** — görev metni *"ÖNCE TARA VE ÖLÇ. EŞİK DEĞİŞTİRME"* diyor.
`codes/` altında **hiçbir şey değiştirilmez**. Adlandırma önerisi (D-214)
**uygulanmaz** — kararı mimarındır. Kapı eklenmez.
