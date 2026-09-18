# FOV ÖLÇÜMÜ — IMX477 + 6 mm, Jetson canlı hattı (19 Eylül 2026, 01:1x)

**Sonuç: yatay FOV = 53–54° (ÖLÇÜLDÜ).** Kullanılan `--fov 63` **%17 fazladır.**

## Yöntem
Jetson'un kendi üretim hattından (`kamera_koprusu` → `/kare.jpg`, 1280×720, `Camera mode = 1`
= 1920×1080 sensör modu) kare alındı. Duvarda **8,0 × 8,0 cm** kare kağıt; kamera lensinden
kağıda mesafe şerit metreyle ölçüldü. Kağıdın piksel genişliği, parlaklık profilinden
(satır başına eşik = (maks + medyan)/2) **12 ayrı satırda** okundu, medyan alındı.

`FOV = 2·atan( (kağıt_m · (1280/piksel)) / 2 / mesafe_m )`

## Ölçümler

| Mesafe | Kağıt (medyan) | Görüntü genişliği | Yatay FOV | Kare |
|---|---|---|---|---|
| 1,00 m | **100 px** (99–100, 2 satır) | 1,024 m | **54,3°** | `kare_1m.jpg` |
| 2,00 m | **51 px** (12 satırda 49–52) | 2,008 m | **53,3°** | `kare_2m.jpg` |

**ÖN KAYIT (ölçümden ÖNCE yazıldı):** 1 m'deki 100 px doğruysa 2 m'de **50 ± 2 px** çıkmalıydı.
**Ölçülen 51 px → ön kayıt TUTTU.** Piksel oranı 100/51 = 1,96 (beklenen 2,00), yani iki
mesafe ölçümü de birbirini doğruluyor.

## Yorum

| Hipotez | Beklenen yatay FOV | Ölçümle uyum |
|---|---|---|
| Tam sensör (4056 px, 6,287 mm) | 55,3° | yakın (üst sınır) |
| **3840→1920 binning (FOV korunur)** | **52,8°** | ✅ **uyuyor** |
| Sensör merkezinden kırpma | 27,9° | ❌ elendi (2 kat sapma) |

**Sensör kırpma YAPMIYOR, binning yapıyor.** Sürücünün sunduğu iki mod (3840×2160, 1920×1080)
aynı görüş alanını kapsıyor.

## Kullanılacak değer
**`FOV=54`** (iki ölçümün ortalaması 53,8°). Belirsizlik ≈ ±1,5°: kağıt kadrajın
**merkezinde değil** (x≈800–855, merkez 640) ve bu lenste belirgin **varil bozulması** var
(masa kenarı görüntüde kavisli). Kenarlar sıkıştığı için ölçüm gerçek değerden bir miktar
**dar** çıkmış olabilir; merkezde tekrarlanırsa 55°'ye yaklaşabilir.

`FOV=55` de savunulabilir (ölçümün %2 içinde). **`FOV=63` savunulamaz.**

## Yan bulgu — keskinlik hükmü düzeltildi
Aynı oturumda tavana bakarken ölçülen keskinlik **13,2** "lens bulanık" sanılmıştı. Bu karelerde
duvar dokusu, priz ve kalem izi net seçiliyor: **odak iyi durumda**. Laplacian varyansı dokuya
duyarlıdır; düz beyaz tavanda kusursuz lensle de düşük çıkar. Odak hükmü yalnız dokulu hedefte
verilebilir.
