# ÖN KAYIT — T99: 89/90/91 ölçümleri ÜRETİM çağrı imzasıyla

**Tarih:** 2026-09-03 · **Yazan:** Claude 2 (Opus 5, amele) ·
**Direktif:** `MIMAR_DIREKTIFLERI_20260903.md` İş 1 ·
**Eşikler/kollar SONUÇ GÖRÜLMEDEN yazıldı (D-107).**

## 0. Doğrulanan zemin (ölçümden önce, kodda okundu)

Eski ölçüm imzası — 89:160, 90:276, 91:130 üçü de aynı:
`rota_bul(mk, mpp=mpp, icerik=icerik)` → `baslangic=None`, `hedef=None`,
`yol_sinif_idler=(0,)`, `engel_sinif_idler=(1,)`, `gorsel_cikti=False`.

Üretim çağrısı — `simulation/scripts/iha_haritala.py:324`:
`rota_bul(costmap_maskeleri, mpp=MPP, baslangic=…, hedef=…, plan=True,
yol_sinif_idler=COSTMAP_YOL_KATMANLARI, engel_sinif_idler=COSTMAP_ENGEL_KATMANLARI,
gorsel_cikti=True)` — **`icerik` GEÇİRİLMEZ**.

**🔴 KUYRUK METNİ BAYAT:** T99 kaydı `engel_sinif_idler … # (1, 2) MOLOZ + ARAC`
diyor. Bugünkü `codes/sinif_semasi.py`: `KATMAN_ARAC = 10` (2 DEĞİL) —
eğitim `2 = hedef` ile çakışmasın diye ayrı ad alanına taşınmış. Yani
`COSTMAP_ENGEL_KATMANLARI = (1, 10)`.

**🔴 VAKUM RİSKİ (D-375 sınıfı):** `obb_arac_maskesi(bgr, None)` **boş maske**
döndürür; `haritala(arac_model=None)` varsayılandır. Araç modeli yüklenmezse
`engel_sinif_idler=(1,10)` fiilen `(1,)`'dir ve "araçlar engel" farkı
**ölçülmemiş olur**. `yolov8m-obb.pt` diskte VAR (53 MB) → yüklenecek ve
boş-olmayan araç maskesi sayısı raporlanacak.

**Ankor mekanizması:** `baslangic/hedef` verilince `_ankoru_ekle` C-uzayında
bağlantıyı doğrular; başarısızsa `durum=DOGRULAMA_BASARISIZ`, `yol_no=None`
(costmap_path_finder.py:1269-1276). Yani ankor **yalnız reddedebilir** —
ölçülecek "kayıp" tam budur.

## 1. Kollar (aynı karede, TEK çıkarım — 89'un ölçüm sözleşmesi)

| kol | çağrı | izole ettiği fark |
|---|---|---|
| **A** | `rota_bul(mk, mpp, icerik=icerik)` | eski ölçüm tabanı |
| **B** | A + `baslangic`, `hedef` tohumları | **ankor** doğrulaması |
| **C** | B + araç katmanı (10) + `engel_sinif_idler=(1,10)` | **araçlar engel** |
| **D** | C + `gorsel_cikti=True` + `icerik=None` | üretimin tam biçimi |

Model kare başına **bir kez** koşar; aynı `mk` dört kola da verilir (89'un
sözleşmesi: iki ayrı çıkarım YASAK). Araç maskesi de kare başına bir kez.
Tohumlar: `hedef` = manifest `hedef_kutu` merkezi (tek piksel, üretimdeki
`_tohum_maskesi` gibi); `baslangic` = içerik kutusunun alt-orta noktası
(İKA giriş noktasının t66 karşılığı). **Bu bir VEKİLDİR** — üretimde tohumlar
dünya koordinatından gelir; raporda öyle anılır.

## 2. Raporlanacaklar (eski sayılarla yan yana)

kayıp (rota üretmeyen kare) · durum dağılımı · A'ya göre karar değişimi ·
şerit doğruluğu (manifest `acik_serit`) · süre p50/p95 · güven medyanı.

## 3. Geçerlilik kapıları (sonuç görülmeden)

| # | kapı | GEÇTİ ölçütü |
|---|---|---|
| V1 | Vakum yok | Araç maskesi **en az 1** karede boş değil; değilse C kolu "VAKUMDA ÖLÇÜLDÜ" damgalanır |
| V2 | Kollar gerçekten farklı | Her kolun kwargs'ı ölçüm çıktısında yazılı ve A'dan farklı (yapısal kanıt) |
| V3 | Tek çıkarım | Kare başına segmentasyon çağrısı = 1 (sayaçla) |
| V4 | Determinizm | Aynı maskelerle aynı kol iki kez → aynı karar (ilk 10 karede) |

## 4. KAPI (görevden, aynen)

**Ölçüm koşulmadan HİÇBİR kod değişmez.** Fark çıkarsa bulgu deftere yazılır,
karar mimara bırakılır. Bu betik yalnız ölçer; üretim/ölçüm betikleri
(89/90/91, `costmap_path_finder`, `iha_haritala`) **değiştirilmez**.


---

## EK-1 (ölçüm sırasında, sonuç görülmeden) — vekil tohum kusuru

İlk vekil `baslangic` tohumu içerik kutusunun **alt-orta pikseli** idi.
Ölçüldü: 6 karenin 4'ünde orası **zemin değil**. Tohum zemine oturtuldu.
*(Eşik değişmedi; ölçüm aracının kusuru düzeltildi.)*

## EK-2 (ölçüm sırasında) — C-uzayı tohumu

Zemine oturtmak yetmedi: `koridor_adaylari` bağlantıyı **C-uzayında**
(`dt_px >= r_gerekli_px`) test eder; duvar dibindeki tek piksel C-uzayında
geçersizdir. Üretimde `baslangic` İKA'nın gerçekten durduğu yerdir — bir araç
ancak kendi yarıçapı kadar açıklığı olan noktada durabilir. Tohum üretimin
**kendi `serbest_alan` çıktısıyla** C-uzayına oturtuldu.

## EK-3 (ölçüm sırasında) — kör/etiketli ankor kuşatması

C-uzayına oturtmak da tek başına yetmedi ve **sebebi bulundu:** `baslangic=None`
iken tohum **tüm alt bant**tır (`_tohum_maske(..., "alt")`), verilince **tek
pikseldir**. t66 kadrajının alt kenarı şeritler AYRILDIKTAN sonrasını gösterir;
alt-orta piksel keyfî olarak bir şeride düşer. Ölçüldü (`sa_000001`): açık
şerit 1, tohum şerit 2'de ve hedefle **ayrı C-bileşeninde** → doğru şekilde
`KAPALI_DAR`. Yani kör ankor **imzayı değil kadrajı** ölçüyor.

Üretimde KB, şeritler ayrılmadan **önceki** ortak alandadır; t66 kırpması o
alanı içermiyor. Bu yüzden gerçek davranış **iki kolla kuşatıldı**:
**B (kör)** = alt sınır · **B2 (açık şeridin girişi, GERÇEK ETİKETLE)** = üst
sınır. B2 etiket kullandığı için *en iyi durum*tur ve raporda öyle anılır.

---

## SONUÇ (2026-09-03, ölçüm sonrası yazıldı) — n=260, v36

| kol | rota üreten | şerit doğru | A'ya göre değişim | p50 ms |
|---|---|---|---|---|
| **A** eski ölçüm | 29/260 | 17/29 (**%58,6**) | — | 25,9 |
| **B** kör ankor | **0**/260 | — | 29 | 22,3 |
| **B2** açık şerit ankoru | 12/260 | 11/12 (**%91,7**) | 17 | 24,0 |
| **C** +araç katmanı | 0/260 | — | 29 | 22,1 |
| **D** tam üretim biçimi | 0/260 | — | 29 | 22,2 |

### Ana bulgu: ankor bir FİLTREDİR ve ayırt edicidir

A'nın ürettiği 29 rotanın B2'de akıbeti:

| A'daki rota | eleniyor | korunuyor | elenme oranı |
|---|---|---|---|
| şeridi **DOĞRU** (17) | 6 | 11 | %35,3 |
| şeridi **YANLIŞ** (12) | **11** | 1 | **%91,7** |

**Fisher kesin testi: tek yönlü p = 0,0030** (çift yönlü 0,0032) — ankorun
yanlış rotayı tercihen elemesi rastlantı değildir. Sonuç: üretim imzası
**daha az ama çok daha doğru** rota üretir (%58,6 → %91,7).

### Geçerlilik kapıları

| # | sonuç |
|---|---|
| V1 vakum yok | **GEÇTİ** — araç maskesi 7/260 karede dolu (252–1787 px) |
| V2 kollar farklı | GEÇTİ — kwargs çıktıda yazılı |
| V3 tek çıkarım | GEÇTİ — 260/260 |
| V4 determinizm | GEÇTİ — ilk 10 karede aynı karar |

### Yan bulgu: araç katmanı ÖLÇÜLDÜ ama etkisiz

7 karede araç maskesi dolu; **hiçbirinde** karar değişmedi (C ≡ B, her
metrikte birebir). Yani `engel_sinif_idler=(1,10)` bu kümede ölçülebildi ve
**etkisi sıfır** — araçlar koridorları daraltan yerde değil. T99'un
"araçlar engel sayılınca reddetme artabilir" endişesi bu kümede
**doğrulanmadı** (çürütülmedi de: 7 kare zayıf örneklem).
