# B4 — FP16 ↔ FP32 KARAR DENKLİĞİ · ön kayıt

Tarih: **2026-09-01** — hiçbir FP16 karşılaştırma sonucu üretilmeden önce
yazıldı (D-107).

## 0. Soru ve neden Jetson'sız cevaplanabilir

D-371 "FP16 kullanılacak" dedi; dayanağı B4'e şartlıydı. Sorunun sayısal
kısmı cihazdan bağımsızdır: IEEE half aritmetiği PC GPU'sunda da Jetson'da da
aynıdır (TensorRT katman birleştirmesi farklılık yaratabilir — o kalan pay
Gün-1 §4'te `.engine` ile kapanır; bkz. `GUN1_KONTROL_LISTESI.md`).

Ölçülen şey maske benzerliği DEĞİL, **yayınlanan karardır**: şerit no ya da
`None` + ret sebebi. Maske IoU'su karara çevrilmeden anlamsızdır (D-74'ün
dersi: IoU 2,2× arttı, karar düzeyinde hiçbir şey değişmedi).

## 1. Dondurulan yöntem

- Zincir `163_b4_p_ve_kosu.py` ile AYNI üretim zinciri; tek fark
  `model.predict(..., half=True)` (FP16 kolu). Aynı süreç, aynı kareler,
  aynı mpp.
- Kümeler: **S** (260, mpp manifestten) ve **R'nin ≥30 m katmanı** (633 kare;
  FOV 67,3 esas — EK-1'de donduruldu). Katman dışı R kareleri işlenmez:
  hüküm zaten katmanda verilir (EK-2) ve GPU süresi sıralılık kısıtı altında
  (BSOD örüntüsü) israf edilmez.
- ⚡ Maskeler bit-eş ise (`np.array_equal`, sınıf sınıf) karar bir kez
  hesaplanır ve iki kola yazılır — `analyze_path` deterministiktir; aynı
  girdi aynı kararı verir. Bit-eş OLMAYAN her karede iki kol ayrı koşulur.
- Kare başına kayıt: `(fp32_yol, fp16_yol, fp32_red, fp16_red)`.

## 2. Eşikler — SONUÇ GÖRÜLMEDEN yazıldı

- **F1 (zarar yönü, S):** S'te yer gerçeği var (`acik_serit`).
  FP32'nin **doğru** verdiği bir karede FP16'nın **yanlış şerit** vermesi:
  **0 tolerans.** Tek örnek bile F1'i düşürür ve D-371 yeniden açılır.
- **F2 (uyuşma, R katmanı):** yayınlanan karar uyuşması **≥ 0,98**.
  Gerekçe: uyuşmazlık oranı f, etkin `p`'yi en fazla f kadar oynatır;
  f ≤ 0,02 iken `GEREKLI_FPS = 1/(5p)` p ≥ 0,2 bölgesinde ≤ %10 oynar —
  eşik türetimini bozmaz. f > 0,02 ise FP16'nın FPS kazancı, gerektirdiği
  FPS artışıyla kıyaslanmadan karar verilemez.
- **F3 (ret simetrisi):** uyuşmazlıkların listesi ve ret sebepleri JSON'a
  yazılır; `None→şerit` ve `şerit→None` yönleri ayrı sayılır. F3 bilgi
  amaçlıdır, kapı değildir.

## 3. ÖLÇÜLEMEDİ kuralları

- CUDA yoksa FP16 kolu koşulamaz → sonuç **OLCULEMEDI**; CPU'da half
  emülasyonu ile "geçti" ÜRETİLMEZ.
- R'de yer gerçeği yoktur; F1 R'de değerlendirilmez (uyuşma F2'nin işidir).
