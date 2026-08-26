# T150 — HB (hedef bölge) dedektörünün ÖLÇÜMÜ

> **ON_KAYIT §16.** Üretime **bağlama YOK**; bu belge yalnız ölçüm ve öneridir.
> Yorumlayıcı: `O:\navitas-local-train\venv\Scripts\python.exe` · **GPU kullanılmadı**
> (`hb_maskesi` klasik OpenCV; maliyet ölçümü yer gerçeği maskesiyle koşuldu).
> Ham çıktılar: `olcum.json` · `ham_kareler.json` · `ham_gercek.json` ·
> `olcum_maliyet.json` · `tani_arena_figuru.json` · bindirmeler `bindirme/`.
> Betikler: `olc_hb.py` · `olc_hb_gercek.py` · `olc_hb_maliyet.py` · `tani_arena_figuru.py`

## HÜKÜM (önce)

🔴 **BAĞLANMAMALI.** Dedektör kendi üretecinin renk varsayımına kilitli.
İki ölçüm bağımsız olarak aynı sonuca çıkıyor:

1. **Şartname figüründeki gerçek HB pedi TESPİT EDİLEMİYOR** (`sartname_s9_arena.png`,
   ped penceresinde eşiği geçen kırmızı piksel **0**). Ped sahada figürdeki gibiyse
   (siyah ped + beyaz H) dedektör **hiçbir** karede HB bulamaz → `HEDEF_YOK` →
   **her kare rota kaybeder**.
2. **HB'nin olmadığı gerçek karelerde yanlış pozitif yıkıcı:** 67 gerçek otopark
   karesinin **67'sinde** (%100) kırmızı otomobil HB sanıldı; DJI kırsalda 111
   karenin **15'inde** (%13,5) kırmızı toprak/branda HB sanıldı. Bağlanırsa rota
   **yanlış varış noktasına** gider ve sistem görevi tamamladığını sanır — bu
   `HEDEF_YOK`'tan **daha tehlikelidir**.

---

## 1. Sentetik kabul kümesi (n=260) — yer gerçeği VAR

**Yer gerçeği bulundu:** `manifest.json` → `ornekler[].arena.hedef_kutu`
(260/260 dolu, hepsi 25,6 × 25,6 px, `hedef_varyanti = "metin_kirmizi_H"`,
`hedef_kenar_m = 2.0`, `icerik = [0,0,640,640]`). Ayrı `meta.txt` yok; manifest yeterli.

| ölçüt | değer |
|---|---|
| HB bulundu | **260 / 260** (%100) |
| hiç bulamama | **0** |
| tespit merkezi GT kutusunun içinde | **260 / 260** |
| merkez hatası (px) | medyan **0,71** · ort 0,72 · p90 0,95 · **maks 1,30** |
| kutu IoU | medyan **0,899** · min 0,836 · IoU ≥ 0,5 → 260/260 |
| **yanlış pozitif** (GT ile IoU < 0,10 bileşen) | **0 kare / 0 bileşen** |
| `mpp` (HB kenarından, `mpp_hb_pedinden`) | GT 0,078125 · tahmin medyan 0,074074 · bağıl hata medyan **%5,2**, maks **%8,6** |

⚠ **ÇEVRİMSELLİK UYARISI — bu tablo saha kanıtı DEĞİLDİR.** Bu küme, dedektörün
geliştirildiği ve `tests/test_hb_dedektoru.py` ile kilitlendiği **üretecin**
(`scripts/olcum/51_sentetik_arena.py` · `hb_ciz`) çıktısıdır. Üreteç pedi
`HB_KIRMIZI` çerçeve + kırmızı `H` ile çiziyor; dedektör tam bu varsayımı arıyor.
260/260 isabet, dedektörün **kendi varsayımını** doğrular, sahayı değil.

## 2. Gerçek kareler — HB YOK, dolayısıyla her tespit YANLIŞ POZİTİF

| küme | n | tespit | yanlış-pozitif oranı |
|---|---|---|---|
| `data/raw_frames` (67 gerçek otopark) | 67 | **67** | **%100** |
| `dataset/dji_kirsal_0038_bolum_v3/images` | 111 | **15** | **%13,5** |
| `data/arena_referans/sartname_s9_arena.png` | 1 | **0** | — (aşağı bak) |

**Gözle doğrulandı** (`bindirme/gercek_*`):
`frame_000000_000000000.jpg` — kadrajın ortasındaki **kırmızı otomobil** magenta
kutuyla HB olarak işaretlenmiş. Otoparkta tespit edilen kutuların kenarı 32,5–48,5 px,
ima ettikleri `mpp` 0,032–0,034 m/px (yani "bu araba 2 m × 2 m" demiş oluyor).
DJI `frame_000024_000001590.jpg` — sol üstteki **kırmızımsı toprak yaması** işaretlenmiş.

### 2b. Arena figürü (n=1 — kanıt değil, bilgi)

Şartname §9 figüründe HB **vardır** ve gözle görülür: **siyah ped, beyaz H**.
Dedektör **bulamadı**. Sebep ölçüldü — **renk, şekil değil**:

| ölçüm (ped penceresi x=325,y=118,75×60) | değer |
|---|---|
| `BARIYER_KROMA_ESIGI` (ortak eşik) | 25 |
| ped `a*` (LAB, −128 kaydırmalı): min / medyan / **maks** | −6 / −1,0 / **+5** |
| pedde eşiği geçen kırmızı piksel | **0** / 4500 |
| ped ortalama BGR | (132,2 · 135,9 · 135,1) → **akromatik** |
| karedeki toplam kırmızı piksel | 1889 — **tamamı kırmızı-beyaz bariyerde** (`a*` maks 44) |

Yani figürdeki tek kromatik yapı **bariyerdir** ve T67 onu doğru eliyor
(`bindirme/arena_figuru_kroma_tani.jpg`: magenta yalnız bariyer bandında).

🔴 **Kaynak çelişkisi kod içinde zaten yazılı ama sonucu ölçülmemişti.** T71 (D-99)
"figür yapay zekâ ürünüdür, METİN otoritedir" diyerek şartname §2.1 metnini
("üzerinde **kırmızı** H harfi") seçti ve üreteci ona göre yazdı. Ölçüm şunu
gösteriyor: **bu seçim yanlışsa dedektör sahada %0 isabet verir.** Metin mi figür mü
doğru — bu **ölçülemez**, teyit gerektirir (§5, K1).

## 3. T67 (bariyer) ile ÇAKIŞMA sınaması

**439 karenin 0'ında** çakışma var — piksel toplamı **0** (sentetik 260 + otopark 67 +
DJI 111 + arena figürü 1).

Ama `karar_sozlesmesi.py` yorumundaki gerekçe **eksik**. Yorum çakışmazlığı
"arada boş bant" geometrisine bağlıyor (`HB_KARE_TOLERANSI` 1,6 < `BARIYER_EN_BOY_ORANI` 4,0).
Kod okundu: `hb_maskesi` ayrıca **bariyer maskesini 5×5 genişletip kırmızıdan
ÇIKARIYOR** (`karar_sozlesmesi.py` ~:983-988, "T67 ILE TUMLEYENLIK" bloğu). Yani
çakışmama **tasarımla garanti altındadır**; ölçüm bunu doğruladı, bağımsız olarak
sınamadı. Boş-bant iddiası tek başına sınanmış değildir.

## 4. ÜRETİME BAĞLAMA MALİYETİ (ölçüm — uygulama YOK)

### 4a. Kod okuması — `goruntu` geçilirse ne olur

- `codes/rpi_inference.py:1641-1648`: `goruntu is not None` ise `hb_konumu` çağrılır;
  **`None` dönerse `_don(None, 0.0, [], clean, hedef_yok_reddi(), None)`** —
  yani `HEDEF_YOK` sebebiyle **rota üretilmez** (fail-**closed**). Üst banda düşme yok.
- Bugün **hiçbir üretim çağrısı `goruntu` geçmiyor** — doğrulandı:
  `codes/rpi_inference.py:1944 · 2047 · 2141` üçü de `analyze_path(masks[0],
  icerik=…, engel_mask=…, mpp=…, return_reason=True, olcek_kaynagi=…)`, `goruntu` yok.
  Şartname §2.2.6 (İKA'nın HB sınırlarına girmesi) yazılımda **sahipsiz** — teyit edildi.

🔴 **Kod kusuru (bağlanırsa tetiklenir).** `_bagli_koridor_yolu`
(`rpi_inference.py:1046-1049`):

```python
if hedef_tohumu is not None:
    kesisim = (np.asarray(hedef_tohumu) > 0) & (koridor > 0)
    if kesisim.any():
        ust_tohum = kesisim.astype(np.uint8)
```

`kesisim` **boşsa** `ust_tohum` varsayılan **ÜST BANT** olarak kalır. Yukarıdaki
yorum "HB koridora bağlı değilse bağlantı kapısı zaten reddeder" diyor — bu **yanlış**:
kesişim boşken bağlantı kapısı **üst bandı** sınar, HB'yi değil. Yani "HB bulundu ama
koridorda değil" hâli **sessizce üst banda düşer** (fail-**open**) ve çıktıda hiçbir iz
bırakmaz. Sentetik kümede bu dal **hiç tetiklenmedi** (259/259 karede son waypoint
değişti → kesişim her karede doluydu); ama gerçek karedeki yanlış-pozitif kutu koridor
dışına düşerse sessizce çalışır.

### 4b. Sayı — `analyze_path` iki kipte, YER GERÇEĞİ maskesiyle (GPU yok)

Sentetik kümenin YOLO etiketleri maskeye çevrildi (sınıf 0 zemin, sınıf 1 engel;
engel zeminden çıkarıldı — madde 15) ve `analyze_path` **aynı karede iki kez** koşuldu:
`goruntu=None` (bugünkü üretim) ve `goruntu=im` (T72 bağlanmış). Bu **mükemmel algı
üst sınırıdır**; gerçek modelle sayılar ancak daha kötü olur.

| ölçüt | bugün (`goruntu=None`) | HB bağlı (`goruntu=im`) |
|---|---|---|
| rota üretilen | **259 / 260** | **259 / 260** |
| **bağlama nedeniyle kaybedilen kare** | — | **0** |
| ret sebebi (1 kare, her iki kipte aynı) | `ZEMIN_MASKESI_SUPHELI` | `ZEMIN_MASKESI_SUPHELI` |
| son waypoint → GT HB kutusuna uzaklık (px) | medyan **9,2** · p90 27,5 · **maks 349,1** | medyan **0,0** · p90 0,6 · **maks 1,22** |
| son waypoint HB kutusunda (≤ 2 px) | **0 / 259** | **259 / 259** |

**Okuma:** sentetik kümede bağlama **hiç rota kaybettirmiyor** ve varış noktasını
gerçekten HB'ye taşıyor — bugün rota HB'ye **hiçbir karede** varmıyor (maks 349 px
uzakta bitiyor). Yani şartname §2.2.6 açığı **gerçektir** ve mekanizma sentetikte
**çalışıyor**. Sorun mekanizmada değil, **dedektörün girdisinde**.

**Gerçek karede maliyet — ölçülen iki uç:**
- Ped figürdeki gibiyse (akromatik): tespit 0 → **her kare `HEDEF_YOK`** → rota %100 kaybı.
- Ped kırmızıysa bile HB'siz sahnede: otoparkta 67/67 sahte tespit → rota **yanlış
  hedefe** gider. Bu iki uç arasında güvenli bir aralık **ölçülmedi**, çünkü gerçek
  kırmızı H pedi olan tek bir kare bile yok.

## 5. HÜKÜM ve ÖNERİ

### Fail-open mu fail-closed mu — şartnameyle hangisi tutarlı

Şartname §2.2.6 görev başarısını **İKA'nın HB sınırlarına girmesi** diye tanımlıyor;
üst banda varmak görevi tamamlamaz. Dolayısıyla **"HB bulunamazsa üst banda düş"
şartnameyle TUTARSIZDIR**: rota üretilir, görev sayılmaz, üstelik hiçbir uyarı çıkmaz.
Mevcut kodun tercihi (`HEDEF_YOK` = fail-closed) **doğrudur ve korunmalıdır**.

Ama fail-closed'ı **etkinleştirmek** için önce dedektörün gerçek pedde çalıştığının
kanıtı gerekir — yoksa fail-closed **her kareyi keser**. Bugün o kanıt **yoktur**.

### Öneri (uygulama YOK — mimar vekilinin kararına)

- **K1 · İNSAN GÖREVİ (madde 9 — yalnız mimar kuyruğa ekler).** HB pedinin **gerçek
  rengi ve deseni** yarışma şartnamesi/SSS'sinden teyit edilsin. Mümkünse 2 m × 2 m
  ped basılıp DJI ile gimbal 90°'de 5–10 kare çekilsin. **T150'nin ÖLÇÜLEMEDİ kalan
  tek kalemi budur** ve başka hiçbir ölçüm onun yerine geçmez.
- **K2 · Dedektör renk varsayımından ayrılmalı.** "Yüksek kromalı kırmızı" yerine
  birincil ölçüt **"yüksek kontrastlı KARE ped + içinde H topolojisi"** olmalı
  (H: tek bileşen, delik yok, üç çubuk — veya şablon eşleme). Renk **ikincil kanıt**
  olarak kalsın. Böylece hem figürdeki siyah/beyaz ped hem metindeki kırmızı H yakalanır.
- **K3 · Ölçek çapraz kontrolü ZORUNLU kapı olsun.** HB kenarı tanımı gereği 2,0 m'dir;
  `mpp_hb_pedinden` ile telemetri `mpp`'si `olcek_capraz_kontrolu` bandını aşan aday
  **reddedilmeli**. Otopark yanlış-pozitiflerinin ima ettiği `mpp` 0,032–0,034 m/px;
  gerçek irtifa ölçeğiyle çelişiyorsa çoğu düşerdi. ⚠ Bu **ölçülmemiş** bir öneridir —
  o karelerde telemetri `mpp`'si yok (ÖLÇÜLEMEDİ).
- **K4 · Bağlanırsa sessiz geri düşüş kapatılsın.** `_bagli_koridor_yolu`'da
  `hedef_tohumu` verilmiş ama `kesisim` boşsa **üst banda düşülmemeli**; fail-closed
  bir ret (`HEDEF_YOK` veya bağlantı reddi) dönmeli. Bugünkü kod bu hâlde sessizce
  fail-open oluyor (§4a).
- **K5 · Bağlama kapısı önerisi (ön kayıt gerektirir, sonuca göre gevşetilmez).**
  Üretime girmesi için: **gerçek HB pedi bulunan ≥ 20 karede isabet ≥ %90**
  **ve** **HB'siz gerçek ≥ 100 karede yanlış-pozitif ≤ %2**.
  Bugünkü durum: isabet **ÖLÇÜLEMEDİ** (gerçek ped yok), yanlış-pozitif **%100**
  (otopark) / **%13,5** (DJI) → **kapı DÜŞÜYOR.**

## 6. ÖLÇÜLEMEDİ

- **Gerçek kırmızı H pedi üzerinde isabet oranı** — böyle bir kare yok (ON_KAYIT §16
  bunu zaten öngörmüştü). Saha isabeti ÖLÇÜLEMEDİ olarak kalıyor.
- **Gerçek üretim modeli (v36) maskesiyle bağlama maliyeti** — GPU yasak
  (yalnız `karar_cevrilmesi` ajanı GPU koşar). Ölçüm **yer gerçeği maskesiyle** yapıldı;
  bu mükemmel algı üst sınırıdır, gerçek sayı ancak daha kötü olur.
- **Telemetri `mpp` çapraz kontrolünün yanlış-pozitifleri ne kadar eleyeceği** —
  67 otopark ve 111 DJI karesinde telemetri ölçeği yok.
- **Arena figürü sonucu n=1'dir** — kanıt değil, bilgidir (görev metninde de böyle yazılı).
- **"Arada boş bant" iddiasının tek başına yeterliliği** — ölçülemedi, çünkü
  `hb_maskesi` bariyer piksellerini zaten çıkarıyor; iki mekanizma ayrıştırılamadı (§3).

## 7. Kapılar (koşuldu)

```
> O:\navitas-local-train\venv\Scripts\python.exe codes/test_rota_sentetik.py
     5      zor       2       2  0.797               ACIK   42  OK
------------------------------------------------------------------------------
SONUC: 15/15 dogru
[OK] TUM DETERMINISTIK SAHNELER GECTI

> O:\navitas-local-train\venv\Scripts\python.exe -m unittest discover -s tests -q
Ran 962 tests in 75.125s

OK (skipped=2)
```

Bu görevde **üretim kodu değiştirilmedi** (yalnız `results/t150/` altına ölçüm betiği
ve çıktı yazıldı), bu yüzden mutasyon kanıtı gerekmez — yeni test eklenmedi.
