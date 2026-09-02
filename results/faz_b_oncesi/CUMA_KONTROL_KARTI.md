# CUMA AKŞAMI KONTROL KARTI — 4 Eylül (yazdırılacak)

> Cumartesi sabahı kutu açılmadan önce bu kartın **tamamı** işaretli olmalı.
> Kaynak: `SAHA_HAZIRLIK_PLANI_20260903.md` §1 · ölçüm çıktıları:
> `results/faz_b_oncesi/cuma_kontrol/`

## A. Yazılım kapıları — **3 Eylül gecesi koşuldu, hepsi GEÇTİ**

| ✓ | kapı | sonuç (3 Eylül) |
|---|---|---|
| ✅ | Genel kapı `codes/test_rota_sentetik.py` | **15/15 · 15/15** |
| ✅ | Tam test paketi | **1875 test OK** (skipped 3) |
| ✅ | Kuru koşu `scripts/saha_kuru_kosu.py` | **9 GEÇTİ · 1 SAHİPSİZ** (yalnız `motor` — İKA gerçek sürücüsü; FDA uçuşunda gerekmez) |
| ✅ | Paket aynası `scripts/jetson_paket_hazirla.py` | 18 dosya senkron |
| ✅ | Model dosyaları pakette | `navitas_seg_v36_best.pt` + `_512_fp16.onnx` (54,8 / 54,6 MB) |
| ✅ | Jetson açılış `jetson_baslat.sh --kuru` (udp + sik) | exit 3 — PC'de beklenen (`[YOK]` satırları Jetson yolları); uçlar 14550/14551/14552, `--streamrate 8`, köprü satırı doğru |
| ✅ | Mühür `scripts/surum_dondur.py --dogrula` | exit 3 "DONDURULMADI" (mühür 17 Eylül) |
| ✅ | Çevrimdışı tekerlekler `wheels/` | **14/14 paket · 51 dosya · 246 MB** |
| ✅ | Saha belleği `scripts/bellek_hazirla.py` | **404 dosya · 1,27 GB** → `O:\navitas_bellek` |

**Cuma akşamı tekrar koşulacak tek şey:** genel kapı + tam suit (gün içinde kod
değiştiyse). Değişmediyse yukarıdaki sonuçlar geçerlidir.

## B. İnsanın yapacakları — cuma akşamına kadar

| ✓ | ne | neden / not |
|---|---|---|
| ☐ | **microSD ≥ 64 GB (UHS-I)** + kart okuyucu al | JetPack imajı yazılacak |
| ☐ | **JetPack 4.6.x** "Jetson Nano Developer Kit SD Card Image" indir, balenaEtcher ile yaz | Nano gerekmez, PC'de yapılır |
| ☐ | **5 V / 5 A UBEC** al | Jetson beslemesi; FCHUB'ın küçük BEC'i yetmez |
| ☐ | **JST-GH 6-pin kablo** + dişi-dişi jumper | TELEM1 (SiK) ve TELEM2 → Nano UART |
| ☐ | **USB webcam** (yedek kamera) | CSI yolu ilk gün açılmazsa `--kaynak 0` |
| ☐ | XT60/XT90 fiş, kablo bağı, ısı makaronu, damper bant | kablolama |
| ☐ | **Yedek pervane seti (12×10, CW+CCW)** | ilk uçuşlarda en sık kırılan parça |
| ☐ | (öneri) **2. pil 4S 10 Ah + ≥150 W şarj** | tek pil → günde 2 uçuş |
| ☐ | (öneri) GPU torch wheel'i (JetPack 4.6 / Py3.8) indir, belleğe koy | v36 YOLOv8m; CPU'da FPS kapısı düşebilir |
| ☐ | Küçük ekran + klavye, ethernet kablosu | Nano ilk açılış |
| ☐ | Multimetre, tartı, baret/yelek | kablolama kontrolü, UHDR kütle, saha |
| ☐ | `O:\navitas_bellek` klasörünü **USB'ye kopyala** | 1,27 GB; `MANIFEST.txt` içindedir |
| ☐ | Bu kartı + `FAZ_B_GUN_PLANI.md` + `JETSON_NANO_KURULUM.md` **yazdır** | sahada ekran olmayabilir |

## C. Cumartesi sabahı ilk üç iş (kutu açılınca)

1. **Envanter + tartı** — künye tablosuyla karşılaştır, farkları tutanağa (UHDR ister).
2. **Mekanik yerleşim** — Pixhawk ok ileri + damper, GPS direkte, kamera nadir.
3. **Kablolama pervanesiz, pil en son** — `SAHA_HAZIRLIK_PLANI` §2.3 tablosu.

⚠ **Pervaneler ilk uçuşa kadar takılmaz.** Motor testi ve tüm yer provaları pervanesiz.

## D. Sahada kural olarak hatırlanacak üç şey

- **Pil değişimi = Pixhawk yeniden başlar = akış isteği silinir** → `jetson_baslat.sh --kapi`
  yeniden koşulur (iniş kanıtı bu akışa bağlı, D-406).
- **`--fda` bayrağı** 21 Eylül uçuşunda YKS'yi doğru kipe alır: bütçe 10 dk, paraşüt ve
  İKA kapalı, hakem onayı İKA kanıtı beklemez (D-408).
- **Kamera köprüsü** `scripts/kamera_koprusu.py` içindir ve Jetson'da `~/navitas/scripts/`
  altına kopyalanır (`codes/` değil — yanlışı `--kur`'u durdurur, D-407).
