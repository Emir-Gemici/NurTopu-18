# T235-D · FDA yol etiketi tezgâhı — ölçüm (ON_KAYIT §2 + §3)

> ⚠ **BENZETIM (SENTETIK MASKE), SAHA ÖLÇÜMÜ DEĞIL.** Render yok, GPU yok, MuJoCo koşusu yok. Bu klasördeki her sayı *benzetim (sentetik maske), saha ölçümü değil* etiketlidir (K1 satırları: *benzetim (MuJoCo sentetik kareler, yer gerçeği poz), saha ölçümü değil*).
>
> Ön kayıt: `results/fdr_sprint_20260910/H1/t235/ON_KAYIT.md` (ölçümden önce yazıldı; eşik, ızgara, çekiliş, tohum değişmedi).
> Üreteç: `simulation/mujoco/t235_etiket_tezgahi.py` · ham tablo: `k3_hucre_tablosu.json`, `k1_uygulama.json` (bu README aynı koşumdan üretildi) · türetme: `kapi_duyarliligi.json` (kayıtlı tablodan hesap; yeni çekiliş yok).

## Hüküm (ON_KAYIT §2 karar kuralı — önceden yazılı; sonuç ne çıktıysa o)

- **A0: DUSTU** · **A1: DUSTU** — benzetim (sentetik maske), saha ölçümü değil.
- **Karar:** A0 DUSTU, A1 DUSTU -> KARE kalir (ON_KAYIT SS2).
- YKS etiketin cercevesini niteler (T235-A).
- Alan sığma payı < 1 m olduğu için FDA'da kullanılmayacak yapılandırma: 16:9@32m (benzetim (sentetik maske), saha ölçümü değil).
- **K1 (uygulama testi, bağımsız kanıt değil):** A1 dünya yoluyla 28/28 (beklenen 28/28); KARE negatif kontrolü ÜRETİLDİ (kerteriz: 3/8, kosum_tur3_uretim: 6/20) → **GEÇTİ** (benzetim (MuJoCo sentetik kareler, yer gerçeği poz), saha ölçümü değil).
- **FDA'da yayınlanan yol etiketi: KARE.** **T235-C (poz kolu / A1'in üretime bağlanması) AÇILMAZ** — ON_KAYIT §2 karar kuralı A1'i yalnız "A0 düşer, A1 geçerse" açar.
- Eşik gevşetilmedi. "GEÇTİ" yalnız bu tezgâh kapısı içindir; saha doğrulaması değildir, FDR'ye "düzeltildi" diye yazılamaz (ON_KAYIT §7).

## Koşullu yeniden hüküm ve duyarlılık (D-457 ön kaydı) — TÜRETME, yeni ölçüm YOK

> ⚠ Bu bölümdeki her sayı `k3_hucre_tablosu.json`'daki **kayıtlı** hücrelerden hesaplandı (`kapi_duyarliligi.json`); tezgâh yeniden koşulmadı, yeni çekiliş üretilmedi. Eşik (%99) ve iki koşul aynıdır; yalnız hangi hücrelerin sayıldığı değişir.

- **Duyarlılık:** kapıya giren 16 hücre tek başına değerlendirildiğinde kapı AYNI çıkıyor (A0: DUSTU, A1: DUSTU) → kapı dışı 20 hücre (s = 5 m ve bilgi hücresi) hükmü taşımadı.
- **12 Eylül A9'da ölçülen kamera kipinin yapılandırması geçerli sayılır; kapı AYNI eşikle (%99,0 ve KARE'den 0,5 puan) yalnız o yapılandırmanın hücreleriyle kurulur. Ölçüm yeniden koşulmaz; kayıtlı tablo okunur.**

| 12 Eylül A9'da ölçülen kip | yapılandırma | koşul 1 | koşul 2 | A0 | FDA etiketi |
|---|---|---|---|---|---|
| 4:3 | 4:3@32m | ✓ | ✓ | **GECTI** | **A0** (bayrakla, varsayılan kapalı) |
| 16:9 | 16:9@40m | ✗ | ✓ | **DUSTU** | **KARE** |
| ölçülemezse | — | — | — | — | **KARE** |

A1 aynı ayrımda: 4:3 → DUSTU; 16:9 → DUSTU (hiçbir yapılandırmada geçmiyor → T235-C poz kolu bu tabloyla açılmaz). Tüm satırlar: benzetim (sentetik maske), saha ölçümü değil.

## Kapı (ON_KAYIT §2)

Nominal hücreler: s ∈ {6.67, 8} m, σ_c = 1 m, σ_ψ = 5°, (4:3, 32 m) ve (16:9, 40 m); A1 için σ_g = 2 m. Koşul 1: doğru oranı ≥ %99. Koşul 2: kapıya giren **hiçbir** hücrede (s = 5 m ve bilgi hücresi (16:9, 32 m) hariç; A1'de her σ_g) KARE'den 0.5 puandan fazla kötü değil. Kapı tamsayı sayımlarla değerlendirildi.

| yöntem | koşul 1 (nominal ≥ %99) | koşul 2 (KARE − 0,5 puan) | kapı |
|---|---|---|---|
| A0 | DÜŞTÜ — s=6.67 4:3@32m: %99.10 ✓; s=6.67 16:9@40m: %98.33 ✗; s=8 4:3@32m: %99.52 ✓; s=8 16:9@40m: %99.10 ✓ | GEÇTİ — ihlal 0/16 blok | **DÜŞTÜ** |
| A1 | DÜŞTÜ — s=6.67 4:3@32m sigma_g=2: %91.48 ✗; s=6.67 16:9@40m sigma_g=2: %90.30 ✗; s=8 4:3@32m sigma_g=2: %94.45 ✗; s=8 16:9@40m sigma_g=2: %93.62 ✗ | DÜŞTÜ — ihlal 4/32 blok | **DÜŞTÜ** |

Tüm oranlar: benzetim (sentetik maske), saha ölçümü değil.

A1 koşul 2 ihlalleri (4; en kötü 5): s=8|4:3@32m|sc=0.5|spsi=2 sigma_g=2: -5.30 puan; s=8|4:3@32m|sc=0.5|spsi=5 sigma_g=2: -5.22 puan; s=8|4:3@32m|sc=1|spsi=2 sigma_g=2: -3.13 puan; s=8|4:3@32m|sc=1|spsi=5 sigma_g=2: -2.95 puan — benzetim (sentetik maske), saha ölçümü değil.

Yapılandırma başına kapı (BİLGİ — ön kayıt iki yapılandırmayı birlikte bağlar, hükmü değiştirmez):

- A0: 4:3@32m: koşul1 ✓, koşul2 ✓; 16:9@40m: koşul1 ✗, koşul2 ✓ (benzetim (sentetik maske), saha ölçümü değil)
- A1: 4:3@32m: koşul1 ✗, koşul2 ✗; 16:9@40m: koşul1 ✗, koşul2 ✓ (benzetim (sentetik maske), saha ölçümü değil)

## Negatif kontrol K3n

KARE, s = 5 m, merkezli, hatasız karede [2, 2, 2] üretmeli (açık yol 1/2/3 sırasıyla). A0/A1 aynı sahnede BİLGİ (pozitif kontrol).

| (kip, h) | KARE | A0 | A1 | KARE üretti mi |
|---|---|---|---|---|
| (4:3, 32 m) | [2, 2, 2] | [1, 2, 3] | [1, 2, 3] | EVET |
| (16:9, 40 m) | [2, 2, 2] | [1, 2, 3] | [1, 2, 3] | EVET |
| (16:9, 32 m) | [2, 2, 2] | [1, 2, 3] | [1, 2, 3] | EVET |

K3n: **ÜRETİLDİ — tezgâh boş değil** (benzetim (sentetik maske), saha ölçümü değil).

## Alan sığma (HESAP, hatasız nominal kare)

| (kip, h) | mpp (m/px) | kare genişlik × boy (m) | 20×20 alan payı (m) | FDA'da kullanılır mı (pay ≥ 1,0 m) |
|---|---|---|---|---|
| (4:3, 32 m) | 0.06549 | 33.53 × 25.15 | +2.57 | EVET |
| (16:9, 40 m) | 0.08186 | 41.91 × 23.58 | +1.79 | EVET |
| (16:9, 32 m) | 0.06549 | 33.53 × 18.86 | -0.57 | HAYIR |

Tüm satırlar: benzetim (sentetik maske), saha ölçümü değil.

## Hücre tablosu (doğru oranı %, doğru/sahne; sahne = 2000 çekiliş × 3 açık yol)

Her hücre: benzetim (sentetik maske), saha ölçümü değil. `N` = nominal hücre, `b` = bilgi hücresi, `-` = kapı dışı (s = 5 m).

| s (m) | (kip, h) | σ_c (m) | σ_ψ (°) | | KARE | A0 | A1 σ_g=1 | A1 σ_g=2 | A0 − KARE (puan) | A0 pay p01/p05/medyan (m) | alan tam karede % |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 5 | (4:3, 32) | 0.5 | 2 | - | 56.25 (3375/6000) | 96.45 (5787/6000) | 91.62 (5497/6000) | 80.75 (4845/6000) | +40.20 | 0.04/0.24/2.06 | 98.1 |
| 5 | (4:3, 32) | 0.5 | 5 | - | 56.03 (3362/6000) | 96.30 (5778/6000) | 91.57 (5494/6000) | 80.75 (4845/6000) | +40.27 | 0.06/0.22/2.06 | 89.2 |
| 5 | (4:3, 32) | 1 | 2 | - | 56.82 (3409/6000) | 91.53 (5492/6000) | 91.63 (5498/6000) | 80.83 (4850/6000) | +34.72 | 0.04/0.20/1.97 | 90.0 |
| 5 | (4:3, 32) | 1 | 5 | - | 56.35 (3381/6000) | 91.52 (5491/6000) | 91.67 (5500/6000) | 80.87 (4852/6000) | +35.17 | 0.04/0.20/1.96 | 79.2 |
| 5 | (16:9, 40) | 0.5 | 2 | - | 36.92 (2215/6000) | 92.33 (5540/6000) | 88.67 (5320/6000) | 79.48 (4769/6000) | +55.42 | 0.02/0.19/1.98 | 68.0 |
| 5 | (16:9, 40) | 0.5 | 5 | - | 36.67 (2200/6000) | 92.12 (5527/6000) | 88.42 (5305/6000) | 79.35 (4761/6000) | +55.45 | 0.02/0.15/1.94 | 49.6 |
| 5 | (16:9, 40) | 1 | 2 | - | 40.53 (2432/6000) | 88.37 (5302/6000) | 88.80 (5328/6000) | 79.55 (4773/6000) | +47.83 | 0.06/0.19/1.91 | 62.6 |
| 5 | (16:9, 40) | 1 | 5 | - | 40.27 (2416/6000) | 88.10 (5286/6000) | 88.63 (5318/6000) | 79.40 (4764/6000) | +47.83 | 0.06/0.19/1.91 | 46.1 |
| 5 | (16:9, 32) | 0.5 | 2 | b | 56.32 (3379/6000) | 96.48 (5789/6000) | 91.70 (5502/6000) | 80.75 (4845/6000) | +40.17 | 0.04/0.24/2.07 | 0.0 |
| 5 | (16:9, 32) | 0.5 | 5 | b | 56.33 (3380/6000) | 96.53 (5792/6000) | 91.70 (5502/6000) | 80.88 (4853/6000) | +40.20 | 0.04/0.24/2.07 | 0.0 |
| 5 | (16:9, 32) | 1 | 2 | b | 56.85 (3411/6000) | 91.57 (5494/6000) | 91.67 (5500/6000) | 80.88 (4853/6000) | +34.72 | 0.04/0.20/1.97 | 0.0 |
| 5 | (16:9, 32) | 1 | 5 | b | 56.88 (3413/6000) | 91.68 (5501/6000) | 91.68 (5501/6000) | 80.92 (4855/6000) | +34.80 | 0.04/0.20/1.97 | 0.0 |
| 6.67 | (4:3, 32) | 0.5 | 2 |  | 86.52 (5191/6000) | 100.00 (6000/6000) | 99.10 (5946/6000) | 91.33 (5480/6000) | +13.48 | 1.09/1.53/2.82 | 98.1 |
| 6.67 | (4:3, 32) | 0.5 | 5 |  | 86.12 (5167/6000) | 100.00 (6000/6000) | 99.05 (5943/6000) | 91.43 (5486/6000) | +13.88 | 1.05/1.51/2.82 | 89.2 |
| 6.67 | (4:3, 32) | 1 | 2 |  | 83.95 (5037/6000) | 99.12 (5947/6000) | 99.10 (5946/6000) | 91.47 (5488/6000) | +15.17 | 0.24/0.96/2.82 | 90.0 |
| 6.67 | (4:3, 32) | 1 | 5 | N | 83.60 (5016/6000) | 99.10 (5946/6000) | 99.05 (5943/6000) | 91.48 (5489/6000) | +15.50 | 0.20/0.92/2.82 | 79.2 |
| 6.67 | (16:9, 40) | 0.5 | 2 |  | 62.30 (3738/6000) | 99.97 (5998/6000) | 98.25 (5895/6000) | 90.35 (5421/6000) | +37.67 | 0.76/1.21/2.68 | 68.0 |
| 6.67 | (16:9, 40) | 0.5 | 5 |  | 62.15 (3729/6000) | 99.97 (5998/6000) | 98.12 (5887/6000) | 90.28 (5417/6000) | +37.82 | 0.76/1.17/2.68 | 49.6 |
| 6.67 | (16:9, 40) | 1 | 2 |  | 62.18 (3731/6000) | 98.40 (5904/6000) | 98.25 (5895/6000) | 90.32 (5419/6000) | +36.22 | 0.18/0.68/2.72 | 62.6 |
| 6.67 | (16:9, 40) | 1 | 5 | N | 61.90 (3714/6000) | 98.33 (5900/6000) | 98.12 (5887/6000) | 90.30 (5418/6000) | +36.43 | 0.14/0.68/2.72 | 46.1 |
| 6.67 | (16:9, 32) | 0.5 | 2 | b | 86.62 (5197/6000) | 100.00 (6000/6000) | 99.10 (5946/6000) | 91.35 (5481/6000) | +13.38 | 1.07/1.53/2.82 | 0.0 |
| 6.67 | (16:9, 32) | 0.5 | 5 | b | 86.65 (5199/6000) | 100.00 (6000/6000) | 99.10 (5946/6000) | 91.45 (5487/6000) | +13.35 | 1.05/1.53/2.83 | 0.0 |
| 6.67 | (16:9, 32) | 1 | 2 | b | 84.00 (5040/6000) | 99.12 (5947/6000) | 99.10 (5946/6000) | 91.47 (5488/6000) | +15.12 | 0.24/0.96/2.82 | 0.0 |
| 6.67 | (16:9, 32) | 1 | 5 | b | 84.07 (5044/6000) | 99.12 (5947/6000) | 99.10 (5946/6000) | 91.43 (5486/6000) | +15.05 | 0.24/0.94/2.82 | 0.0 |
| 8 | (4:3, 32) | 0.5 | 2 |  | 99.68 (5981/6000) | 100.00 (6000/6000) | 99.55 (5973/6000) | 94.38 (5663/6000) | +0.32 | 1.24/1.76/3.74 | 98.1 |
| 8 | (4:3, 32) | 0.5 | 5 |  | 99.67 (5980/6000) | 100.00 (6000/6000) | 99.55 (5973/6000) | 94.45 (5667/6000) | +0.33 | 1.27/1.76/3.74 | 89.2 |
| 8 | (4:3, 32) | 1 | 2 |  | 97.57 (5854/6000) | 99.53 (5972/6000) | 99.55 (5973/6000) | 94.43 (5666/6000) | +1.97 | 0.42/1.25/3.64 | 90.0 |
| 8 | (4:3, 32) | 1 | 5 | N | 97.40 (5844/6000) | 99.52 (5971/6000) | 99.55 (5973/6000) | 94.45 (5667/6000) | +2.12 | 0.45/1.24/3.61 | 79.2 |
| 8 | (16:9, 40) | 0.5 | 2 |  | 80.87 (4852/6000) | 99.98 (5999/6000) | 99.13 (5948/6000) | 93.60 (5616/6000) | +19.12 | 0.96/1.45/3.54 | 68.0 |
| 8 | (16:9, 40) | 0.5 | 5 |  | 80.50 (4830/6000) | 99.98 (5999/6000) | 99.08 (5945/6000) | 93.55 (5613/6000) | +19.48 | 0.96/1.45/3.50 | 49.6 |
| 8 | (16:9, 40) | 1 | 2 |  | 80.68 (4841/6000) | 99.13 (5948/6000) | 99.13 (5948/6000) | 93.60 (5616/6000) | +18.45 | 0.30/1.00/3.46 | 62.6 |
| 8 | (16:9, 40) | 1 | 5 | N | 80.17 (4810/6000) | 99.10 (5946/6000) | 99.10 (5946/6000) | 93.62 (5617/6000) | +18.93 | 0.30/1.00/3.46 | 46.1 |
| 8 | (16:9, 32) | 0.5 | 2 | b | 99.70 (5982/6000) | 100.00 (6000/6000) | 99.55 (5973/6000) | 94.38 (5663/6000) | +0.30 | 1.24/1.76/3.74 | 0.0 |
| 8 | (16:9, 32) | 0.5 | 5 | b | 99.75 (5985/6000) | 100.00 (6000/6000) | 99.55 (5973/6000) | 94.42 (5665/6000) | +0.25 | 1.24/1.76/3.77 | 0.0 |
| 8 | (16:9, 32) | 1 | 2 | b | 97.55 (5853/6000) | 99.53 (5972/6000) | 99.55 (5973/6000) | 94.43 (5666/6000) | +1.98 | 0.42/1.25/3.64 | 0.0 |
| 8 | (16:9, 32) | 1 | 5 | b | 97.58 (5855/6000) | 99.53 (5972/6000) | 99.55 (5973/6000) | 94.42 (5665/6000) | +1.95 | 0.42/1.25/3.64 | 0.0 |

## T235-K1 — uygulama testi (ON_KAYIT §3; bağımsız kanıt DEĞİL)

Veri: `H1/k3_uretim_boru/kerteriz/harita_*.json` (8 OPEN_ROUTE) ve `H1/kosum_tur3/uretim_*/karar_toplayici.json` (20 OPEN_ROUTE). Rota `rota_dunya` → `sim_karar_toplayici.dunya_piksel` → `cv2.polylines` LINE_8 (1280 px; Analiz C yöntemi). A1: `kbh_serit_karari`, yer gerçeği poz, alan = HTAB (50 m; merkez köşe ortalaması [0.0, 0.0], kerteriz 0°), hdg = 90 − yaw, montaj = θ − 90.

| kaynak | kare | A1 = dünya yolu | KARE = dünya yolu | KARE yeniden = yayınlanan |
|---|---|---|---|---|
| kerteriz | 8 | 8/8 | 3/8 | 8/8 |
| kosum_tur3_uretim | 20 | 20/20 | 6/20 | 20/20 |

- `kbh_donustur` ↔ `sim_karar_toplayici.piksel_dunya` geri dönüş farkı (tüm rota pikselleri): en çok 0.00e+00 m. mpp ↔ çözünürlük tutarsız kare: 0.
- Hepsi: benzetim (MuJoCo sentetik kareler, yer gerçeği poz), saha ölçümü değil.

## Yöntem ve uygulama seçimleri

- **Sentetik maske:** 20×20 m alanda Başlangıç→Hedef doğrultusunda üç DÜZ yol, x = −s, 0, +s; y = −10…+10 m. Açık yolun merkez hattı rota sayılır ve üretim çıkarım tuvalinde (512 px kare, letterbox; içerik kutusu 4:3 [0, 64, 512, 384], 16:9 [0, 112, 512, 288]) `cv2.line` LINE_8 ile rasterlanır; kutu dışı kırpılır. mpp = `mpp_irtifadan(h, içerik genişliği, HFOV 55.30°)`.
- **Fiziksel kamera (her çekiliş):** görüntü merkezi yerde e_c + h·tan(eğim)·(cos φ, sin φ); görüntü-yukarısı alan +y'sinden saat yönünde ψ dönük; nadir, düz zemin.
- **KARE** `rota_serit_karari`, **A0** `alan_serit_karari` (W = 20 m), **A1** `kbh_serit_karari` — üretim modülündeki fonksiyonların kendisi çağrılır.
- **A1'in bildiği:** İHA konumu e_c + e_g (GPS kestirim hatası), baş = komut edilen (kerteriz − montaj); eğimi bilmez (ATTITUDE yok). ψ pusula kaynaklıdır: otopilot ölçülen başı tutar, A1 aynı pusulayı okur → A1'in yaw artığı da ψ'dir. A1 dönüşümünü sınamak için alan kerterizi 37°, montaj yaw 90° (KARE/A0 bu seçimden bağımsızdır).
- **Aynı çekilişler:** tohum 20260910 ile sabit sırada (z_c, z_ψ, eğim, yön, z_g) 2000 standart çekiliş üretilir; her hücre bunları σ ile ölçekler (ortak rastgele sayılar). Üç yöntem ve iki σ_g aynı çekilişi görür; hücre sonucu ızgaranın geri kalanından bağımsızdır (alt ızgara bayt-eş yeniden üretilir, `tests/test_t235_alan_etiketi.py`).
- **Açık yol "eşit":** her çekiliş üç açık yol için de değerlendirilir (hücre = 6000 sahne; açık yol başına sayım JSON'da).
- **s = 6,67 m** ön kayıttaki yazımıyla (6.67) alındı, 20/3 değil.
- Karar üretilemeyen sahne (rota karede yok) YANLIŞ sayılır; sayısı JSON'da `karar_yok`.

## Yeniden üretim

```
REM tam kosum (tezgah yeniden kosulur — ON KAYIT tohumuyla ayni sayilari uretmelidir)
O:\navitas-local-train\venv\Scripts\python.exe simulation/mujoco/t235_etiket_tezgahi.py
REM yalniz turetme (tezgah KOSULMAZ; kayitli JSON'lardan bu README ve kapi_duyarliligi.json)
O:\navitas-local-train\venv\Scripts\python.exe simulation/mujoco/t235_etiket_tezgahi.py --turetme
O:\navitas-local-train\venv\Scripts\python.exe -m unittest discover -s tests -p test_t235_alan_etiketi.py
REM mutasyon kosucusu (22 mutasyon; ham cikti mutasyon/mutasyon_ciktisi.txt)
O:\navitas-local-train\venv\Scripts\python.exe -X utf8 results/fdr_sprint_20260910/H1/t235/mutasyon/mutasyon_t235bd.py
```
