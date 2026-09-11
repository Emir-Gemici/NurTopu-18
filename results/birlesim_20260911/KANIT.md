# 11 Eylül 2026 — T226 / T228 / T221 birleşim doğrulaması

Yorumlayıcı: `O:\navitas-local-train\venv\Scripts\python.exe` (`PY`).
Çalışma dizini `O:\navitas`. Kullanıcı commit ve birleştirmeye "onay" verdi.
Push yapılmadı; ölçüm komutunda `--kuru` zorunlu kullanıldı.

## İlk tam koşu (birleşim HEAD `d02e3b63`)

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONUTF8='1'
& 'O:\navitas-local-train\venv\Scripts\python.exe' -X utf8 -B scripts/push_kapisi.py --kuru
```

Gerçek çıktı: `Ran 2620 tests in 545.541s / FAILED (failures=3, skipped=13)`;
genel kapı `GENEL KAPI (madde 14): GECTI — kol1 15/15 · kol2 serit 15/15`.
PowerShell araç çıkışı 1. Ham iki çıktı `../push_kapisi/20260911_155724/` altında
değiştirilmeden korundu. Başarı değildir.

İki hata `test_atolye_test_gunu.K5_Kaynaklar.test_kod_atiflari_satirda_birebir`
alt vakaları: YKS atıfları 4015/4056 boş satıra denk geliyordu. Gerçek ifadeler
4373/4414'te bulundu; `ATOLYE_TEST_GUNU_20260912.md` içinde yalnız iki numara
güncellendi. Atölye kabul eşikleri/metni ve diğer kesinti dalları değişmedi.

Üçüncü hata H1b: küçük harita arena kutusu `[34,133,34,133]` (genişlik 0).
Aynı MK15 dosyasının ayrı tekrarı `Ran 39 tests in 21.307s / OK`, exit 0.
Tüm 2620 test modülünü keşfedip yalnız H1b'yi koşmak da `Ran 1 test in 0.742s / OK`,
exit 0 (`h1b_tum_import_once.txt`). **İlk hatanın kesin tetikleyicisi saptanmadı.**
Testin örtük DPI ve sabit 0,3 s yerleşim beklemesine bağımlılığı kaldırıldı:
`olcek=1.0` (Tk fontu + ürün geometrisi birlikte) ve gerçek arena genişliği
`> S(100)` olana kadar en çok 5 s olay pompalama. Ürün çizimi elle çağrılmıyor;
genişlik eşiği, panel boyutu ve taşmama kontrolleri aynen duruyor. H2c'nin
1,0/1,5 ölçek testleri korundu. Üretim kodu değiştirilmedi.

## Sıralı hedef kontrolleri

```text
PY -X utf8 -B -m unittest discover -s tests -p test_atolye_test_gunu.py -q
Ran 39 tests in 1.611s
OK
ATOLYE_EXIT=0

PY -X utf8 -B results/birlesim_20260911/h1b_tani.py --tum-import --cizim-gecikmesi-ms 800 --cikti results/birlesim_20260911/h1b_gecikme_800ms.txt
KESIF_TEST_SAYISI 2620
Ran 1 test in 1.323s
OK
H1B_EXIT 0

PY -X utf8 -B results/birlesim_20260911/h1b_tani.py --tum-import --configure-yok --cikti results/birlesim_20260911/h1b_configure_yok.txt
KESIF_TEST_SAYISI 2620
Ran 1 test in 5.484s
FAILED (failures=1)
H1B_EXIT 1
BEKLENEN_MUTANT_EXIT=1 GERCEK=1

PY -X utf8 -B -m unittest discover -s tests -p test_yks_mk15_hakem_ekrani.py -q
Ran 39 tests in 21.831s
OK
MK15_SONRA_EXIT=0
```

Tanı koşucusunun mutasyonu yalnız gerçek Tk nesnesinin `<Configure>` bağını
kaldırır; kaynak dosyaya yazmaz. Tuval 300×330 iken arena hâlâ sıfır olduğundan
beklenen H1b assert'i düşmüştür. 800 ms gecikme ise aynı çizim sonucuna ulaşmıştır.
Tam tanı çıktıları bu dizindedir; testin bozuk çizimi kabul etmediği ölçüldü.

ArduPlane SITL ve fiziksel MK15/Jetson ölçümü bu kontroller değildir; yapılmadı.
Üç görevin resmi bağımsız Claude incelemesi beklemektedir.

## Son tam koşu — geçti (HEAD `d812b1e2`)

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONUTF8='1'
& 'O:\navitas-local-train\venv\Scripts\python.exe' -X utf8 -B scripts/push_kapisi.py --kuru
$gateExit = $LASTEXITCODE
Write-Output "BIRLESIM_KAPI_EXIT=$gateExit"
exit $gateExit
```

```text
1/2 tam süit…
    Ran 2620 tests in 538.782s · OK (skipped=13)
2/2 genel kapı…
    GENEL KAPI (madde 14): GECTI — kol1 15/15 · kol2 serit 15/15
KURU: ikisi de yeşil, push edilmedi · kanıt results\push_kapisi\20260911_161757
BIRLESIM_KAPI_EXIT=0
```

Araç çıkışı 0. Ham çıktılar `../push_kapisi/20260911_161757/` altında.
Atlanan 13 test başarı sayılmadı; koşan 2607 test başarılı. İlk kırmızı koşu
ve H1b'nin kesin tetikleyicisinin bilinmediği notu bu yeşil sonuçla silinmedi.

## Kayıtlar güncellendikten sonra

```text
PY -X utf8 -B -m unittest discover -s tests -p test_defter_butunlugu.py -q
Ran 13 tests in 0.053s
OK
DEFTER_EXIT=0

PY -X utf8 -B -m unittest discover -s tests -p test_d373_defter_geri_isaret.py -q
Ran 6 tests in 0.236s
OK
GERI_ISARET_EXIT=0
```

`git diff --numstat -- REVIEW_LOG.md`: `51 0 REVIEW_LOG.md` — yalnız sona ek.
Son kullanıcı-dosyası SHA256 kontrolü devralma başıyla aynı:

- `dronesolid/files (3)/Plaka3_Alt_Cerceve.3mf`:
  `A1DD6138F92362AF7B21729F80A296895CFB9BE5B809FE18089F435D9E9971D1`.
- `results/prova/20260904_095651_8620/hakem_log.jsonl`:
  `538C542DF0C88898B8735393B9B3C27484A9A4A76AF3C9DFE396F54A2E558FEB`.

Bu iki önceden değiştirilmiş dosya commit kapsamına alınmadı.
