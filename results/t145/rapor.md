# T145 — 138 kare uygunluk denetimine KARANLIK + GURULTULU kapısı (D-285 §5)

Tarih: 2026-08-26 · worktree `wf_0c06347c-47a-4` (taban `f1c5931`; 138 betiği
`O:\navitas\scripts\olcum\138_kare_uygunluk_denetimi.py`'den kopyalanıp değiştirildi)

## 1. Kusur (Codex D-282)
`0,03×` karartılmış + Gauss(12, 8) gürültülü kare: keskinlik 521 (> alt 465),
parlaklık 16, bayrak `[]`. Gürültü Laplacian'ı yükseltiyor; parlaklık alt sınırı yoktu.

## 2. Ölçüm (scratch `kesif.py`, gerçek çıktı)
```
REF  lap/yapi  n 67   min 0.057 p05 0.060 p50 0.076 p95 0.102 max 0.118
DJI  lap/yapi  n 768  min 0.272 p05 0.563 p50 1.003 p95 1.372 max 2.835
REF  parlaklik n 67   min 118.688 p05 123.550 p50 128.840 max 132.222
DJI  parlaklik n 768  min 78.528  p05 99.035  p50 119.019 max 157.262
160 etiketli kare: parlaklik min 96.29 · medyan 119.47 · maks 146.61
codex kar+noise (960x540, tohum 282): med_std 4.97 · lap/yapi 7.785 · L 15.99
codex tohum 1/2/3: lap/yapi 7.801 / 7.832 / 7.817
codex tam-cozunurluk (resize sonra): lap/yapi 3.768 · L 15.99
kar only 0.1x: lap/yapi 0.850 · L 13.7        noise s8/s15/s25/s40 (L=142): 0.976/1.246/1.852/2.946
```
Denenen ve ELENEN ölçüt: medyan-bulanık farkının std'si (mutlak). Kırsal çimen
dokusu bunu 12–29'a çıkarıyor (referans 5–7), gürültü sigma 8 yalnız 14,7→15,6
oynatıyor — doku ile gürültüyü ayıramıyor. Oran (Laplacian var / 5px yapı
enerjisi) ayırıyor: temiz maks 2,84 · karşı örnek 7,8 (960×540) / 3,77 (tam çöz.).

## 3. Sabitler (betikte gerekçeli)
- `PARLAKLIK_ALT = 85` — gece en aydınlık kare 76,2 (T138, 569/569 uygunsuz) ile
  etiketli gündüz min 96,3 arasındaki boşluğun ortası.
- `GURULTU_ORANI_UST = 3.5` — temiz maks 2,84 (+%23) ile en zayıf karşı örnek 3,77 arası.
- Bilinen sınır: parlak karede sigma ≤ 40 Gauss gürültü YAKALANMAZ (oran 2,95).
  Ölçüt "gürültü sinyale hâkim" durumunu hedefler.

## 4. 160 maske yeniden koşumu
```
python 138 --veri-kok O:/navitas --cikti results/t145/kare_uygunluk_t145.json
SONUC (160 kare)  BAYRAKSIZ (temiz): 152   ETIKET_COK_SEYREK 8
```
Önceki (`results/dji_kirsal/kare_uygunluk.json`) ile kare-kare fark: **[] — yeni
bayrak alan kare YOK.** 160 karede gurultu_orani min/p50/maks 0,42 / 0,94 / 1,67;
parlaklık min 96,29. En yakın kareler: gürültü `0037/frame_000284_000010740` (1,67),
parlaklık `0038/frame_000111_000004500` (96,29).

## 5. Test + mutasyon (tests/test_t145_uygunluk.py, 4 test)
```
M1 parlaklik alt siniri kaldirildi  -> FAILED (failures=2)  'KARANLIK' not found in ['GURULTULU']
M2 gurultu sinamasi kaldirildi      -> FAILED (failures=1)  'GURULTULU' not found in ['KARANLIK']
geri alindi: bayt-es = True         -> Ran 4 tests OK
```
