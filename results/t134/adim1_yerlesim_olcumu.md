# T134 · ADIM 1 — dört yerleşim ÖLÇÜLDÜ, sonra seçildi

> Sıra emirle bağlıydı: **ÖLÇ → YER SEÇ → UYGULA.** Bu dosya ölçüm kısmıdır.
> Ana ağaç her ölçümden sonra **bayt-eş** geri yazıldı (her koşumda doğrulandı).

## 0. Önce iki soru cevaplandı — ikisi de "hayır"

**Kabul zinciri (K1–K5) etkilenir mi? → HAYIR.**
`61_rota_moloza_basma.py:96` · `63_bariyer_kesisimi.py:71` ·
`66_k5_bariyer_populasyon.py:141` — **üçü de `analyze_path` çağırır**,
`rota_bul` değil. `61 · 63 · 65 · 66 · 109`'da `rota_bul` geçiş sayısı **0**.
⇒ Kabul zinciri kapıdan **zaten geçiyor**; (b) onu değiştirmez.
🔴 Yani emrin uyardığı *"K1 düşerse"* durumu **doğmadı** — K1'e dokunulmuyor.

**Genel kapı (15/15) etkilenir mi? → HAYIR.**
`codes/test_rota_sentetik.py` `rota_bul`u **doğrudan** çağırır (:134, :196).
15 sahnenin tamamı ölçüldü (`124_t134_kapi_etkisi.py`, testin KENDİ
`sahne_uret`i içe aktarılarak):
```text
kaplama: min 0,2986 · maks 0,4262   (tavan 0,67 · pay +0,2438)
kenar  : min 0,0065 · maks 0,0306   (tavan 0,50 · pay +0,4694)
REDDEDILEN: 0/15
```

## 1. Dört yerleşim, hepsi KOŞULARAK ölçüldü

| # | yerleşim | genel kapı | takım |
|---|---|---|---|
| 1 | `serbest_alan` **öncesi**, ham `icerik` | 15/15 | **19**/765 |
| 2 | `serbest_alan` **sonrası**, `sonuc["icerik"]` | 15/15 | **19**/765 |
| 3 | öncesi + `karar_sozlesmesi` doğrulayıcısı | 15/15 | **4**/765 |
| 4 | öncesi + **`rota_bul`un KENDİ doğrulayıcısı** | 15/15 | **0**/765 |

**Düşen hep aynı tek testti:** `test_gecersiz_icerik_kutulari_fail_closed_kalir`
(19 `subTest` alt vakası — 19 ayrı test değil).

⚠ **İlk okumam YANLIŞTI ve düzeltildi.** "19 dejenere fikstür reddediliyor"
sanmıştım; gerçek sebep başka: `zemin_maskesi_reddi` **tasarım gereği
fail-closed**tur (D-71) ve **geçersiz kutuda `ALAN_YETERSIZ`** döner, oysa
`rota_bul`un yayınlanan cevabı o durumda **`MASKE_YOK`**tur. İkisi de rota
üretmez — çakışan tek şey **yayınlanan sebep kodu**ydu.

## 2. Yerleşim 3'ün kalan 4 düşüşü YENİ BİR BULGU açtı

İki içerik-kutusu doğrulayıcısı **anlaşmıyor**:

| kutu | `karar_sozlesmesi.icerik_kutusu_gecerli_mi` | `costmap._icerik_kutusunu_dogrula` |
|---|---|---|
| `(0.0, 0, 64, 64)` float | **geçerli** | boş ROI |
| `{0:0, 1:0, 2:64, 3:64}` sözlük | **geçerli** | boş ROI |
| `{0, 1, 63, 64}` küme | **geçerli** | boş ROI |
| üreteç | **geçerli** | boş ROI |

Bir sözlüğün/kümenin/üretecin "içerik kutusu" sayılması açık bir **fail-open**.
🔴 **Düzeltilmedi** — T134'ün kapsamı dışında, **ÖNER-BEKLE** (D-268 §5).
Yerleşim 4 ikinci doğrulayıcıyı hiç kullanmaz: `rota_bul` **kendi**
fonksiyonunu çağırır (tek kaynak).

## 3. ÖLÇÜM neden HAM maskede yapılmalı (fan-out + çürütücü)

Bağımsız ajan + çürütücü ölçtü ve **iki yönde de** hüküm çeviriyor:
```text
tam cokmus maske : HAM 1,0000 -> serbest_alan sonrasi 0,5988   (kapi SUSAR)
mesru delikli    : HAM 0,5485 -> serbest_alan sonrasi 0,7197   (kapi YANLIS ATESLER)
ayni maske       : mpp=0,05 -> 0,7197 RET  ·  mpp=0,08 -> 0,5247 GECER
```
Yani `serbest_alan` çıktısında ölçmek kapıyı **başka bir kapı** yapardı ve
sayıyı `mpp`ye bağlardı; `analyze_path`in sayısı `mpp`den **bağımsızdır**.
Eşik 0,67 **ham dağılımdan** türetildi (`karar_sozlesmesi`: *"morfoloji/engel
çıkarma SONRASI değil"*).

**Seçilen varyant `analyze_path`in kapısına DENKTİR:** çürütücü 400 rastgele
vakada karar uyuşmazlığı **0/400**; kırpık-vs-ham bit-eşitliği 300 vakada
**0/300** fark (payda kutudan kurulur, kutu dışı hiç okunmaz).

## 4. ÇİFT KAPI — ölçüldü, idempotent

`iha_haritala.haritala()` tek üretim yolunda **ikisini de** çağırıyor:
`:281 _infer → analyze_path`, sonra `:324 rota_bul` — **aynı** `masks[0]`
nesnesiyle. Kapı fonksiyonu **saf**tır (maskeye dokunmaz, serbest alanı
büyütmez); ikinci geçiş aynı sayıyı üretir. Çürütücü kıramadı.

## 5. 🔴 KAPATILMAYAN SINIR — `icerik=None` + letterbox

Letterbox tuvalinde içerik oranı 0,5625'tir; `icerik=None` geçen bir çağrıda
kaplama **matematiksel olarak 0,5625'i aşamaz** ve 0,67 tavanı **hiç
ateşlenemez** (1920×1080, 1280×720, 640×360 için ölçüldü). Kapının **kenar
kolu** çalışmaya devam eder.
- **İKA yolu ETKİLENMEZ:** `iha_haritala` kare mozaik kullanır (`MOZ_PX=1024`)
  ve orada kaplama %96,5 ölçülmüştü — kapı canlı.
- `icerik` geçmeyen diğer çağıranlar: `kamera_dogrula.py:118` ·
  `saha_kuru_kosu.py:722` · `jetson_fps.py:226`. Bunlarda kolun ölü olup
  olmadığı **tuvale bağlıdır ve ayrı ölçülmelidir**.
- **ÖNER-BEKLE:** kapsam T134'ün dışında; kayıt D-268 §6.

## 6. KARAR: **(b) · yerleşim 4**
Ölçüm karar verdi, tercih değil: (b) tek maliyetsiz yerleşimdir (0/765),
tüm çağıranları kapsar ve madde 15 ile tutarlıdır. (a) yalnız `iha_haritala`yı
korurdu; ölçülen **28 çağrı yeri / 17 dosya** kapsam dışı kalırdı.
