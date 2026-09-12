# T240 — Ortak belge kilidi yardımcısı ve belge kilitlerinin geçirilmesi

**D-460 karar 2 → T240-B (RED) → T240-C: D-465 mimar kararı, YÖNTEM DEĞİŞİKLİĞİ.**

Bağımsız mimar denetimi (D-460) T226-D2 · T228-D2 · T221-D3'ü REDDETTİ; ortak gerekçe tekti:
her test dosyası çizik ayıklamasını **kendi** yazmıştı ve üçü de yalnız `~~...~~` biliyordu.
Denetimde kurulan **19 gerçek dosya mutasyonunun 19'u kaçmıştı**. T240 o 19 kaçışı kapattı.
T240 bağımsız çürütücüden RED aldı (5 yeni kaçan); T240-B onları kapattı ve **yine RED aldı**
(3 yeni kaçan: `&#96;` sarmalı sahte kod aralığı — üstelik bir **GERİLEME**).

> ## D-465 (mimar kararı, 12 Eylül) — ESİTLİK > YOKLUK
>
> Üç turdur her RED **aynı biçimde** geldi: *"şu sözdizimiyle yasak metin geri kondu /
> hüküm gizlendi."* Bu bir kalıp eksikliği değil, **yöntem hatasıdır**:
> **YOKLUK (absence) denetiminin kaçış yüzeyi SONSUZDUR; EŞİTLİK denetiminin kaçış
> yüzeyi YOKTUR.** Ölçüm hükmü taşıyan yüzeyler bu turda ön kayıtlı **METİN EŞİTLİĞİNE**
> çevrildi: bölümün ham metni testte duran sabite EŞİT olmak zorundadır; bir sözcük
> değişirse test düşer ve **hangi sözdizimiyle** değiştiği ÖNEMSİZDİR.
>
> Bu yüzeylerde normalleştirme **yalnız boşluk/satır sonu** içindir. Çizik/varlık/vurgu
> **AYIKLAMASI KULLANILMAZ** — ayıklama, saklama yüzeyini açan şeyin ta kendisidir
> (ayıklanan metin testin gördüğü metinden düşer, yani gizlenir).

Bu belge yalnız **koşulan** komutların çıktısını kaydeder. Ham çıktılar:
`kapi_ciktisi.txt` (kapı), `mutasyon_ciktisi.txt` (mutasyon), `hangi_kilit_dusurdu.txt`
(hangi assert düşürdü), `acik_kilitler.md` (depo denetimi).

---

## 1. Ne değişti (T240-C)

| dosya | ne |
|---|---|
| `tests/belge_kilidi.py` | **K1:** `_COZULMEZ` yapı üreten simgelerin tamamına genişledi (küçüktür, büyüktür, backtick, tilde, yıldız, alt çizgi, köşeli ayraç, dikey çubuk, diyez, ters bölü); bu varlıklar **çözülmez** ve `beyaz_liste_disi_cizik` içinde **doğrudan aday** sayılır (`_yapi_varliklari`). **D-465 (1):** `bloklar()` — ön kayıtlı metin eşitliği birimi (YENİ). **K3:** `normalize`'a `metre/santimetre/milimetre/kilometre` ve `yüzde` katlaması; `_OLCUT_BIRIMI`'ne `cm\|mm`; `_buyuklukler`'e **önek katlaması** (`_OLCEK`: cm/mm/km→m, ms→s). **K4:** `kabul_olcutu_tekligi(..., mesru_buyuklukler)` ön kaydı. |
| `tests/test_belge_kilidi.py` | **60 → 74 test**, `self.assert` **110 → 148**. **D-465 (1):** `BlokEsitligi` sınıfı (5 test) — altı ayrı gizleme biçiminin EŞİTLİĞİ düşürdüğü, satır sarması ile çift boşluğun ise **düşürmediği** ölçülür. **K2:** `&#96;~~X~~&#96;` · `&#x60;` · `&grave;` · `&#96;<s>X</s>&#96;` · `&#96;&#96;&#96;` çit biçimi pozitif vakaları + gerileme kanıtı + KUSUR 1b. **K4:** A10/A7/§7.5 çapaları artık **gerçek bölümlerin TAMAMININ harfi harfine kopyası**. |
| `tests/test_yks_mk15_hakem_ekrani.py` | **D-465:** CONTRACTS §6.8 **32 blok** ön kayıtlı metin eşitliğiyle bağlandı (⟨ÖRNEK⟩ koddan). |
| `tests/test_isaretli_gosterici.py` | **D-465:** GOSTERICI_KURULUM **§1 (13) · §4 (12) · §5 (17) · §9 (9) = 51 blok** eşitliğe çevrildi (⟨DRM_BORU⟩ koddan); yeni test `test_G8_D465_on_kayitli_metin_esitligi_dort_bolum`. |
| `tests/test_faz_b_arduplane_sablon.py` | **D-465:** config/pixhawk/README §6.6 **22 blok** eşitliğe çevrildi; yeni test `test_a18b_D465_SS66_on_kayitli_metin_esitligi`. |
| `tests/test_t235_alan_etiketi.py` | **D-465:** t235 `ON_KAYIT §4` **3 blok** eşitliğe çevrildi; yeni test `test_SS4_ON_KAYITLI_METIN_ESITLIGI_D465`. |
| `scripts/belge_kilidi_denetle.py` | **D-465 (3):** rapor artık her geçen dosyanın **YÖNTEM SINIFINI** ölçer (EŞİTLİK / ayıklama / diğer). |
| `results/.../T240/mutasyon_t240.py` | **K5:** X15/X16/X17 gerçek dosya mutantı eklendi: **28 → 31** kaçan. |
| `results/.../T240/hangi_kilit_dusurdu.py` | **K5:** X15/X16/X17 + X15b/X17b (eski çizik kilidi de düşürüyor mu) eklendi. |
| `results/.../T240/sinir_olcumu.py` | **YENİ (D-465 (4)):** aynı hükmün **dokuz** gizleme biçimi için EŞİTLİK ile YOKLUK/AYIKLAMA yüzeylerini yan yana ölçer; §10'daki sınır listesinin sayıları buradan gelir. |

**Ürün kodunun ve belgelerin baytları DEĞİŞMEDİ.** Değişen dosyalar YALNIZCA:
`tests/` (6 dosya), `scripts/belge_kilidi_denetle.py` ve `results/…/T240/`
(`git diff --name-only <merge> HEAD` ile ölçüldü). Dört kilitli belgenin sha256'sı
mutasyon koşumundan **önce ve sonra aynı**:

```
CONTRACTS.md                                       741a9ca26ddeecc55d951dace232db3c485c34293404fbd8749ca431956babbe
jetson_paket/gosterici/GOSTERICI_KURULUM.md        e01d16821d44ca555cf78f5bebb12be24d738b27cea8e6f4f7cc19d480cbd559
config/pixhawk/README.md                           e2efd44838b6cd922e4e8e9916d64e335843225703d6326f2d9294d92d9aa2c6
results/fdr_sprint_20260910/H1/t235/ON_KAYIT.md    7840e933197517a166912b0ebb338f4f3bf99784fa2dbf0844d4f10d61006172
ATOLYE_TEST_GUNU_20260912.md                       065c97307047bf4d8aa0e0a1c03d38059c0ca525b0f617ddf3937f8cc1ed6512
```

---

## 2. K1 — GERİLEMENİN kök nedeni ve düzeltmesi

**Çürütücünün ölçtüğü (X15/X16/X17, gerçek dosya + gerçek süit, çıkış 0):**
`- Dönüştürücünün canlı kodeki (H.264/H.265 çelişkili).` satırı
`- &#96;~~Dönüştürücünün canlı kodeki (H.264/H.265 çelişkili).~~&#96;` yapıldığında süit
**yeşil kaldı.** T240-B'nin `html.unescape` adımı `&#96;`'i çözüyor, `_kod_araliklari`
**çözülmüş** kopyada sahte bir kod aralığı "görüyor" ve içindeki `~~…~~` taramadan tamamen
gizleniyordu. Aynı girdi T240-B **ÖNCESİ** sürümde (64b60ae5) yakalanıyordu: **gerileme.**

**Neden yanlıştı (CommonMark/GFM):** varlık ve sayısal karakter referansları **YAPI belirten
simgelerin yerine kullanılamaz.** Okuyucu satırı önce yapıya ayırır, varlıkları ancak sonra
metin içeriği olarak çözer. Yani **çözülmüş bir backtick kod aralığı AÇAMAZ**, çözülmüş bir
tilde **çizgi AÇAMAZ**: `&#96;` okuyucuda düz bir backtick KARAKTERİDİR, içindeki `~~` ise
çizgiyi AÇAR. Hüküm belgede ÜSTÜ ÇİZİLİ görünürken testte yürürlükte sayılıyordu.

**İki yol vardı; (A) seçildi — gerekçesi kaynakta yazılı:**

| yol | ne yapar | neden seçilmedi / seçildi |
|---|---|---|
| (A) `_COZULMEZ` genişletme | yapı üreten simgeye çözen hiçbir varlık **çözülmez**; kod dışında görünen her biri **doğrudan** beyaz liste dışı adaydır | **SEÇİLDİ** — sınıfın tamamını tek kuralla kapatır: çözülmüş metin yapı üreten HİÇBİR simge KAZANMAZ |
| (B) `_kod_araliklari`'nı HAM metinde hesaplayıp haritayla taşımak | yalnız **kod aralığı** yanılgısını kapatır | `&#126;` (tilde), `&#42;` (yıldız), `&#124;` (tablo çubuğu) **hâlâ** çözülür ve tarama kopyasında OLMAYAN bir yapı üretir |

**(A)'nın bedeli ölçüldü:** çözülmeyen varlık "görünmez" kalabilirdi. Bu yüzden kod
**dışındaki** her yapı-varlığı doğrudan hatadır. Meşruluk ölçümü (kod aralıkları dışında):

| belge | kod disi varlik | cozulen | YAPI ureten |
|---|---|---|---|
| `CONTRACTS.md` | 0 | 0 | 0 |
| `jetson_paket/gosterici/GOSTERICI_KURULUM.md` | 4 | 0 | 0 |
| `config/pixhawk/README.md` | 0 | 0 | 0 |
| `results/fdr_sprint_20260910/H1/t235/ON_KAYIT.md` | 0 | 0 | 0 |

Yani bu sertleştirme gerçek belgelerde **hiçbir yanlış pozitif üretmez** (kapı yeşil,
`belge_kilidi_denetle.py` çıkış 0).

**Gerileme kanıtı, testte:** `&#96;~~kaynak alanı zorunludur~~&#96;` →
`"zorunludur" in normalize(...)` artık **False** (hüküm DÜŞER);
`beyaz_liste_disi_cizik` **4 hata** verir.

**KUSUR 1b (ters yön) de kapandı:** `&#126;` artık çözülmediği için `cizikleri_ayikla`
onu **SİLMEZ**; `&#126;` sarmalı çelişkili hüküm cümlesi `hukum_cumleleri` demetinde
**DURUR** (testle ölçüldü).

**Davranış değişikliği (güçlendirme, gizlenmiyor):** `&lt;s&gt;` eskiden yalnız
**çözülmüyordu** — yani hiçbir kilit onu görmüyordu. Artık kod dışında **adaydır**
(kod içinde temiz). `&#126;&#126;…&#126;&#126;` eskiden **ayıklanıyordu** (yanlıştı: çizgi
açmaz); artık **ayıklanmaz** ama dört varlığın dördü de adaydır.

---

## 3. D-465 (1)+(3) — hangi yüzey hangi sınıfta, gerekçesiyle

| yüzey | yöntem | ölçülen gerekçe |
|---|---|---|
| CONTRACTS §6.8 (**32 blok**) | **METİN EŞİTLİĞİ** (`bloklar`) | hüküm TABLOSU + bağlayıcı ilkeler; D1b/c/d/e, Y4, Y4b, Y7a/b/c hepsi bu bölümde ölçüldü |
| GOSTERICI_KURULUM §1 (**13**) | **METİN EŞİTLİĞİ** | §1 Kodlayıcı satırı "H.264/H.265 çelişkili · DOĞRULANACAK" hükmünü taşır |
| GOSTERICI_KURULUM §4 (**12**) | **METİN EŞİTLİĞİ** | doğrulama tablosunun SONUÇ sütunu (1–9 adım "ÖLÇÜLECEK") bir ölçüm hükmüdür |
| GOSTERICI_KURULUM §5 (**17**) | **METİN EŞİTLİĞİ** | DRM eşikleri ve histerezis hükümleri; A3/A6/A7/A8/A9, Y5, Y10 burada ölçüldü |
| GOSTERICI_KURULUM §9 (**9**) | **METİN EŞİTLİĞİ** | ÖLÇÜLEMEDİ/AÇIK listesi; **X15/X16/X17 tam burada kaçmıştı** |
| config/pixhawk/README §6.6 (**22**) | **METİN EŞİTLİĞİ** | "Sonuç: … KOŞULMADI", ÖLÇÜLEMEDİ başlığı, kabul ölçütleri bloğu; W1/W2/W3/W4/W6/W7, V1/V3, Y11 burada ölçüldü |
| t235 `ON_KAYIT §4` (**3**) | **METİN EŞİTLİĞİ** | T236 kabul ölçütü; D-461 ve X13/X14 burada ölçüldü |
| **TOPLAM** | | **108 blok** |
| aynı dört belgenin uzun anlatı paragrafları ve diğer bölümleri | **ayıklama + VARLIK denetimi** (`cizikleri_ayikla` + `assertIn`) | düşük değerli yüzey: bir komutun/yol adının belgede DURDUĞU denetlenir; burada **YOKLUK iddiası yoktur** |
| `beyaz_liste_disi_cizik` (belge geneli) | **beyaz liste** (ayıklamasız) | çizme sözdizimi kara listeyle kapanmaz; belgenin TAMAMINDA çalışır, eşitlik yüzeyinin dışında kalan bölümleri de tarar |

### D-465 (2) — ayıklamalı kilitler nerede kaldı (ve neden silinmedi)

**Kural:** ayıklamalı kilitler yalnız düşük değerli yüzeylerde kalır ve orada YOKLUK değil
VARLIK denetimi yapar. **Uygulanışı ve bir gerilim:**

- **Yetki artık eşitliktedir.** Yukarıdaki yedi yüzeyin hiçbiri artık ayıklamalı/YOKLUK
  kilidine **dayanmaz**: her birinin BİRİNCİL kilidi metin eşitliğidir.
- **Var olan YOKLUK assert'leri SİLİNMEDİ** (`olumlu_hukum_var` taramaları, kapalı hüküm
  cümlesi kümeleri, `kabul_olcutu_tekligi`). Silmek `assert` sayısını düşürürdü ve bu iş
  için bağlayıcı kural **"kilit GEVŞETİLMEZ"**tir. Bu yüzden **ikinci kat** olarak
  duruyorlar — ve iki kat birden ölçüldü: `hangi_kilit_dusurdu.py` X15b/X17b vakaları aynı
  mutantın hem eşitlik hem çizik kilidini düşürdüğünü kaydeder.
- Bu YOKLUK assert'leri aynı zamanda **eşitliğe çevrilmemiş** bölümleri de tarar (belge
  geneli). Orada tek kilit onlardır ve **zayıf oldukları §10.2 #3'te yazılıdır.**

Eşitlik yüzeyine çevrilen bloklarda **ayıklama kullanılmaz**; bu yüzden meşru çizik
(GOSTERICI §5'teki tarihli eski komut, README §6.6'daki çizili eski ölçüt 1) ön kayıtlı
blokta **HAM hâliyle** durur — FDR kuralı ("eski metin silinmez, çizilir + tarih") bozulmadan
korunur ve iki ön kayıt birbirine bağlanır (testte `assertIn` ile).

### Ölçüm: eşitlik yüzeyi ne yakalar, ayıklama/YOKLUK yüzeyi ne kaçırır

Üretici: `results/fdr_sprint_20260910/T240/sinir_olcumu.py` (çıkış 0). Aynı hüküm
(`| kaynak | zorunlu |`) **dokuz** ayrı sözdizimiyle geri çekiliyor/gizleniyor; tablo
`beyaz_liste_disi_cizik` (çizik taraması), `cizikleri_ayikla` + VARLIK denetimi ve
**EŞİTLİK** yüzeylerini yan yana koyar. Aynı koşum §2'deki K1 ölçümünü de basar.
**HAM ÇIKTI:**

```
# T240-C — ESITLIK vs YOKLUK/AYIKLAMA (D-465 gerekcesinin OLCUMU)
# taban blok sayisi: 5

| gizleme bicimi | beyaz_liste_disi_cizik hata | ayiklama hukmu DUSURDU | ESITLIK DUSURDU |
|---|---|---|---|
| ~~ cift tilde | 2 | EVET | **EVET** |
| <s> etiketi | 2 | EVET | **EVET** |
| &#822; varlik cizgisi | 2 | EVET | **EVET** |
| &#96; sarmali sahte kod araligi | 4 | EVET | **EVET** |
| &amp;#96; cift kacisli varlik | 4 | EVET | **EVET** |
| HTML yorumu | 0 | hayir | **EVET** |
| markdown baglantisi | 0 | hayir | **EVET** |
| sifir genislikli karakter | 0 | EVET | **EVET** |
| U+0333 birlesen cift alt cizgi | 0 | EVET | **EVET** |

## MESRU duzenleme (esitligi BOZMAMALI — bosluk hukmun anlami degildir)

  satir sarmasi          esitlik KORUNDU=True
  cift bosluk            esitlik KORUNDU=True

## K1 OLCUMU — kod ARALIKLARI DISINDA HTML varligi

| belge | kod disi varlik | cozulen | YAPI ureten |
|---|---|---|---|
| `CONTRACTS.md` | 0 | 0 | 0 |
| `jetson_paket/gosterici/GOSTERICI_KURULUM.md` | 4 | 0 | 0 |
| `config/pixhawk/README.md` | 0 | 0 | 0 |
| `results/fdr_sprint_20260910/H1/t235/ON_KAYIT.md` | 0 | 0 | 0 |

HUKUM: her gizleme ESITLIKCE yakalandi, mesru duzenleme yanlis pozitif uretmedi, kilitli belgelerde kod disi YAPI VARLIGI yok
```

**Dokuzunun dokuzunda da EŞİTLİK düşürür.** İki tanesini (HTML yorumu, markdown bağlantısı)
ne çizik taraması ne de ayıklama görür — yani D-465 ÖNCESİ yöntemle **kaçarlardı**.
D-465'in gerekçesi budur ve bu tablo onun ölçümüdür. **Meşru düzenleme yanlış pozitif
üretmez:** satır sarması ve çift boşluk eşitliği **BOZMAZ** — boşluk/satır sonu hükmün
anlamı değildir.

---

## 4. K3 — birim sözcüğü ve önek kaçışı

| kaçan (çürütücü ölçümü) | neden kaçıyordu | düzeltme |
|---|---|---|
| X13 "sahada kabul yatay **en çok 4 metre** ve zamanın **en az yüzde 70**'i" | `normalize` yalnız `saniye/milisaniye/derece` katlıyordu; `metre`/`yüzde` katlanmıyordu → (b) rakip eşiği HİÇ görmüyordu | `_BIRIM_DESENI` + `_YUZDE_DESENI`: `4 metre`→`4 m`, `yüzde 70`→`%70` |
| X14 "sahada kabul **≤ 400 cm**" | `_OLCUT_BIRIMI` `cm` bilmiyordu; bilse bile `cm` ile `m` **ayrı büyüklük** sayılırdı | `_OLCUT_BIRIMI`'ne `cm\|mm`; `_OLCEK` önek katlaması (cm/mm/km→m, ms→s) |

**Negatif vaka testte durur:** aynı eşik başka önekle yazılırsa **rakip değildir**
(`≤ 200 cm` == `≤ 2,0 m` → temiz).

**Ölçülen sınır (iddia edilmiyor):** `dk` **bilerek** katlanmaz — "15 dk" bir süre bütçesi,
"900 s" bir eşik dilidir; bu belgelerde ikisi hiç aynı büyüklüğü anlatmıyor (ölçüldü) ve
katlansa yalancı alarm üretirdi.

**D-465 notu:** t235 `ON_KAYIT §4` artık **metin eşitliğine** de bağlı olduğu için X13/X14
sınıfı iki kilitten birden geçer; K3 düzeltmesi, kuralın **eşitliğe çevrilmemiş** yüzeylerde
(T242'ye taşınan dört belge) de işlemesi için yapıldı.

---

## 5. K4 — çapalar ölçülene çekildi, A10 yanlış pozitifi kapandı

Çürütücünün bulgusu (D-460 bulgu 3 sınıfı): birim testinin sınıf docstring'i çapaları
*"gerçek belgelerin metni (harfi harfine kopya)"* diye tanıtıyordu; oysa **A10 bölümü tek
satıra indirgenmişti**, A7 ve §7.5 çapalarından da birer cümle atılmıştı. Üstelik gerçek
A10 bölümünün TAMAMIYLA koşulduğunda kural (b) **mutasyonsuz yanlış pozitif** veriyordu.

**Yapılan:**
1. Üç çapa da **gerçek bölümün TAMAMININ harfi harfine kopyası** oldu (`A10_BOLUM`,
   `A7_BOLUM`, `C75_BOLUM`). Ölçüldü: **A7 ve §7.5 mutasyonsuz TEMİZ.**
2. A10'un yanlış pozitifi **giderildi**: kaynağı meşru bir
   `**BEKLENTİ (BENZER ÖLÇÜM — ölçüm değil):** … → beklenti ≤ 1,35 FPS` satırıdır (bir
   KABUL değil, BEKLENTİdir). `kabul_olcutu_tekligi` artık `mesru_buyuklukler` **ön kaydı**
   alır: `(("fps", 1.35),)`. Bu bir gevşetme **değildir** — yeni bir değer ancak **görünür
   bir test değişikliğiyle** girer ve **1,35 dışındaki her fps rakip eşiği yine DÜŞER**
   (`test_K4_A10_mesru_buyukluk_ON_KAYITLIDIR_baskasi_DUSER` bunu ölçer: `≥ 0,40 FPS` → hata).
3. Ön kayıt verilmediğinde (b)'nin patladığı **olgu kayda geçti**
   (`test_K4_A10_mesru_buyukluk_ON_KAYITSIZ_YANLIS_POZITIF_verir`) — ölçülenden fazlasını
   söyleyen beyan yerine ölçümün kendisi duruyor.
4. Docstring **ölçülene çekildi**: `T236_BOLUM` çapasının **SENTETİK** olduğu (yalnız kabul
   SATIRI harfi harfine) açıkça yazıldı; gerçek §4'ün tamamı artık ayrı süitte **eşitlikle**
   bağlı.
5. Çapaların **12 Eylül 2026 anlık görüntüsü** olduğu (canlı dosya OKUNMUYOR) ve **neden**
   öyle olduğu yazıldı: ATOLYE kâğıdı 12 Eylül'de İNSAN tarafından doldurulacaktır; gerçek
   dosyaların kilidi kendi süitlerindedir, birim testi o doldurmada kırılmamalıdır.

---

## 6. Kaçan 31 mutantın hepsi yeniden kuruldu ve DÜŞTÜ

Koşucu: `results/fdr_sprint_20260910/T240/mutasyon_t240.py`. Her mutasyon **tek tek gerçek
dosyaya** yazıldı, **ilgili süit gerçekten koşuldu**, sonra dosya **sha256 ile bayt-eş**
geri yüklendi.

```
## 0. Mutasyonsuz TABAN
  test_faz_b_arduplane_sablon.py         cikis=0  OK
  test_isaretli_gosterici.py             cikis=0  OK (skipped=1)
  test_t235_alan_etiketi.py              cikis=0  OK
  test_yks_mk15_hakem_ekrani.py          cikis=0  OK
  TABAN: YESIL

## 1. Mutasyonlar (her biri gercek dosyaya yazildi, suit kosuldu, sha256 ile geri alindi)
  [kontr] D1  cift tilde                     CONTRACTS.md                     cikis=1 -> DUSTU  geri_bayt_es=True sha=741a9ca26dde
  [KACAN] D1b <del>                          CONTRACTS.md                     cikis=1 -> DUSTU  geri_bayt_es=True sha=741a9ca26dde
  [KACAN] D1c tek tilde                      CONTRACTS.md                     cikis=1 -> DUSTU  geri_bayt_es=True sha=741a9ca26dde
  [KACAN] D1d <s>                            CONTRACTS.md                     cikis=1 -> DUSTU  geri_bayt_es=True sha=741a9ca26dde
  [KACAN] D1e celiskili ikinci hukum         CONTRACTS.md                     cikis=1 -> DUSTU  geri_bayt_es=True sha=741a9ca26dde
  [kontr] D1f tipografik tirnak              CONTRACTS.md                     cikis=1 -> DUSTU  geri_bayt_es=True sha=741a9ca26dde
  [KACAN] A3 tek tilde                       GOSTERICI_KURULUM.md             cikis=1 -> DUSTU  geri_bayt_es=True sha=e01d16821d44
  [KACAN] A4 <del>                           GOSTERICI_KURULUM.md             cikis=1 -> DUSTU  geri_bayt_es=True sha=e01d16821d44
  [KACAN] A5 <s>                             GOSTERICI_KURULUM.md             cikis=1 -> DUSTU  geri_bayt_es=True sha=e01d16821d44
  [KACAN] A6 sayi yaziyla                    GOSTERICI_KURULUM.md             cikis=1 -> DUSTU  geri_bayt_es=True sha=e01d16821d44
  [KACAN] A7 'en az' ile esik gevsetme       GOSTERICI_KURULUM.md             cikis=1 -> DUSTU  geri_bayt_es=True sha=e01d16821d44
  [KACAN] A8 'teyit edildi' / 'basarili'     GOSTERICI_KURULUM.md             cikis=1 -> DUSTU  geri_bayt_es=True sha=e01d16821d44
  [KACAN] A9 'asan' ile donma esigi          GOSTERICI_KURULUM.md             cikis=1 -> DUSTU  geri_bayt_es=True sha=e01d16821d44
  [KACAN] W1 baslikta ~OLCULEMEDI~           README.md                        cikis=1 -> DUSTU  geri_bayt_es=True sha=e2efd44838b6
  [KACAN] W6 ~OLCULEMEDI~ + KANITLANDI       README.md                        cikis=1 -> DUSTU  geri_bayt_es=True sha=e2efd44838b6
  [KACAN] W2 KANITLANDI                      README.md                        cikis=1 -> DUSTU  geri_bayt_es=True sha=e2efd44838b6
  [KACAN] W3 _dogrulandi_                    README.md                        cikis=1 -> DUSTU  geri_bayt_es=True sha=e2efd44838b6
  [KACAN] W4 __kosuldu__                     README.md                        cikis=1 -> DUSTU  geri_bayt_es=True sha=e2efd44838b6
  [KACAN] W7 'sorunsuz tamamlandi'           README.md                        cikis=1 -> DUSTU  geri_bayt_es=True sha=e2efd44838b6
  [KACAN] V1 numarasiz celiskili hukum       README.md                        cikis=1 -> DUSTU  geri_bayt_es=True sha=e2efd44838b6
  [KACAN] V3 ikinci 'Sonuc' cumlesi          README.md                        cikis=1 -> DUSTU  geri_bayt_es=True sha=e2efd44838b6
  [kontr] W5 duz DOGRULANDI                  README.md                        cikis=1 -> DUSTU  geri_bayt_es=True sha=e2efd44838b6
  [kontr] W8 duz GECTI                       README.md                        cikis=1 -> DUSTU  geri_bayt_es=True sha=e2efd44838b6
  [KACAN] Y4  &#822; harf harf               CONTRACTS.md                     cikis=1 -> DUSTU  geri_bayt_es=True sha=741a9ca26dde
  [KACAN] Y4b &#x336; onaltilik              CONTRACTS.md                     cikis=1 -> DUSTU  geri_bayt_es=True sha=741a9ca26dde
  [KACAN] Y7a celiskili paragraf (kaynak onu) CONTRACTS.md                     cikis=1 -> DUSTU  geri_bayt_es=True sha=741a9ca26dde
  [KACAN] Y7b celiskili paragraf (ilkeler onu) CONTRACTS.md                     cikis=1 -> DUSTU  geri_bayt_es=True sha=741a9ca26dde
  [KACAN] Y7c celiskili paragraf (son paragraf onu) CONTRACTS.md                     cikis=1 -> DUSTU  geri_bayt_es=True sha=741a9ca26dde
  [KACAN] Y5  aile disi es anlamli           GOSTERICI_KURULUM.md             cikis=1 -> DUSTU  geri_bayt_es=True sha=e01d16821d44
  [KACAN] Y10 esik birimi s -> ms            GOSTERICI_KURULUM.md             cikis=1 -> DUSTU  geri_bayt_es=True sha=e01d16821d44
  [KACAN] Y11 anahtarsiz README celiskisi    README.md                        cikis=1 -> DUSTU  geri_bayt_es=True sha=e2efd44838b6
  [KACAN] D461 ikinci gevsetilmis olcut      ON_KAYIT.md                      cikis=1 -> DUSTU  geri_bayt_es=True sha=7840e9331975
  [KACAN] X15 &#96; sarmali ~~cizik~~        GOSTERICI_KURULUM.md             cikis=1 -> DUSTU  geri_bayt_es=True sha=e01d16821d44
  [KACAN] X16 &#96; sarmali nabiz maddesi    GOSTERICI_KURULUM.md             cikis=1 -> DUSTU  geri_bayt_es=True sha=e01d16821d44
  [KACAN] X17 &#96; sarmali <s>cizik</s>     GOSTERICI_KURULUM.md             cikis=1 -> DUSTU  geri_bayt_es=True sha=e01d16821d44

## 2. OZET
  KACAN mutantlar   : 31/31 DUSTU
  KONTROL mutantlar : 4/4 DUSTU
  geri yukleme      : hepsi bayt-es
  HUKUM             : GECTI
mutasyon cikis=0
```

**Yeni üçü (T240-C):**

| # | mutant | dosya | kilidi düşüren (ölçülen hata metni) |
|---|---|---|---|
| 29 | **X15** `&#96;~~…~~&#96;` | GOSTERICI_KURULUM §9 kodek maddesi | `bloklar` eşitliği (`Tuples differ: … '- &#96;~~Dönüştürücünün canlı kodeki…'`) **ve** `beyaz_liste_disi_cizik` (`satir 241: … (tilde)`) |
| 30 | **X16** `&#96;~~…~~&#96;` | GOSTERICI_KURULUM §9 `-v` nabız maddesi | `bloklar` eşitliği |
| 31 | **X17** `&#96;<s>…</s>&#96;` | GOSTERICI_KURULUM §9 kodek maddesi | `bloklar` eşitliği **ve** `beyaz_liste_disi_cizik` (`… (yapi ureten varlik bicimi &#96;)`) |

**Kontrol mutantları** (denetimde zaten düşenler; koşucunun kendisi sağlam mı):
D1 çift tilde, D1f tipografik tırnak, W5 düz DOĞRULANDI, W8 düz GEÇTİ → **4/4 DÜŞTÜ**.

**Önceki turun bir hükmü ÖLÇÜMLE DÜZELDİ:** T240-B'de Y7a/b/c'nin "tek yakalayanı" kapalı
hüküm cümlesi kümesiydi. T240-C'den sonra `hangi_kilit_dusurdu.txt` gösteriyor ki üçünü de
artık **önce blok eşitliği** düşürüyor (`Tuples differ: … 'Not (12 Eylül): kaynak alanı
artık zoru…'`); kapalı küme **ikinci** kilit olarak duruyor. Y4/Y4b'yi ise hâlâ
`beyaz_liste_disi_cizik` düşürüyor (o assert daha önce koşuyor).

`hangi_kilit_dusurdu.py` ayrıca **X15b/X17b** vakalarını koşar: aynı mutantlar K1
düzeltmesinden sonra **eski (ayıklamalı) çizik kilidini de** düşürür — yani iki bağımsız
kilit birden tutar. Ham çıktı: `hangi_kilit_dusurdu.txt` (çıkış 0).

---

## 7. Kapı (hepsi gerçekten koşuldu)

Yorumlayıcı `O:\navitas-local-train\venv\Scripts\python.exe -X utf8 -B`,
kök `O:\navitas\.claude\worktrees\wf_fabd3bac-230-1`. Ham çıktı: `kapi_ciktisi.txt`.

Kapı çıktısındaki `HEAD` damgası (`40b0d9d2`) koşum anındaki **ARA (WIP) commit**'tir;
ara commit'ler sonunda **tek bir temiz commit'e indirildi**, o yüzden o hash artık
geçmişte DURMAZ. Kapının koştuğu `tests/` ve `scripts/` **baytları son commit'inkiyle
AYNIDIR** ve bu taze bir checkout'ta da **doğrulanabilir** — alt ağaç (subtree) sha1'leri:

```
git rev-parse HEAD:tests     -> 066d259c680d7a2e0c8e0fb6704f5865e3bd9fb5
git rev-parse HEAD:scripts   -> 7df279f2bac4c2cc24c9073aae318b31ac499ebc
```

Koşum anındaki `40b0d9d2:tests` ve `40b0d9d2:scripts` bu iki sha1'in **TA KENDİSİYDİ**;
son commit ile arasındaki tek fark `results/…/T240/` altındaki kanıt dosyalarıdır.

```
# T240-C KAPI — 2026-09-12 05:49:23
# yorumlayici: O:/navitas-local-train/venv/Scripts/python.exe
# depo koku  : O:/navitas/.claude/worktrees/wf_fabd3bac-230-1
# HEAD       : 40b0d9d2

== test_belge_kilidi.py  (cikis=0, 1 s)
----------------------------------------------------------------------
Ran 74 tests in 0.028s

OK

== MK15 (1/3)  (cikis=0, 24 s)
----------------------------------------------------------------------
Ran 39 tests in 24.351s

OK

== MK15 (2/3)  (cikis=0, 25 s)
----------------------------------------------------------------------
Ran 39 tests in 24.535s

OK

== MK15 (3/3)  (cikis=0, 26 s)
----------------------------------------------------------------------
Ran 39 tests in 24.964s

OK

== test_isaretli_gosterici.py  (cikis=0, 34 s)
----------------------------------------------------------------------
Ran 63 tests in 33.989s

OK (skipped=1)

== test_faz_b_arduplane_sablon.py  (cikis=0, 1 s)
----------------------------------------------------------------------
Ran 45 tests in 0.877s

OK

== test_t235_alan_etiketi.py  (cikis=0, 33 s)
----------------------------------------------------------------------
Ran 57 tests in 32.652s

OK

== test_yks_*.py (discover)  (cikis=0, 42 s)
----------------------------------------------------------------------
Ran 233 tests in 39.312s

OK

== GENEL KAPI codes/test_rota_sentetik.py  (cikis=0, 5 s)
URETIM YOLU: rota uretimi 15/15 · yayinlanan serit 15/15 (esik >= 14/15, ON_KAYIT SS18-B)
[OK] URETIM YOLU KOLU GECTI
------------------------------------------------------------------------------
GENEL KAPI (madde 14): GECTI — kol1 15/15 · kol2 serit 15/15

== scripts/belge_kilidi_denetle.py  (cikis=0, 1 s)
| `tests/test_yks_sik_yordami.py` | `assertIn`, `index`, `search` |


rapor yazildi: O:\navitas\.claude\worktrees\wf_fabd3bac-230-1\results\fdr_sprint_20260910\T240\acik_kilitler.md
```

### Taşınan koşul (gizlenmiyor)

Üç süit `data/arena_kompozit/` verisine bağlı; bu dizin **git'te izlenmiyor** (`.gitignore`)
ve taze bir checkout'ta kapı yeniden üretilemez. Bu worktree'de veri yerinde olduğu için kapı
yeşil. **Birleştirmeden sonra ana ağaçta yeniden koşulmalıdır.** Silinmişse:
`shutil.copytree(r"O:\navitas\data\arena_kompozit\images", <worktree>/data/arena_kompozit/images)`.

---

## 8. Kilit gevşemedi — önce/sonra sayılabilir

`self.assert|hatalar.append` sayısı:

| dosya | master | T240-B (e70b3fe6) | **T240-C** |
|---|---|---|---|
| `tests/test_yks_mk15_hakem_ekrani.py` | 214 | 220 | **221** |
| `tests/test_isaretli_gosterici.py` | 369 | 371 | **373** |
| `tests/test_faz_b_arduplane_sablon.py` | 218 | 224 | **229** |
| `tests/test_t235_alan_etiketi.py` | 246 | 248 | **250** |
| `tests/test_belge_kilidi.py` | 0 (yoktu) | 110 | **148** |

Test sayısı: `test_belge_kilidi` **60 → 74**, `test_isaretli_gosterici` **62 → 63**,
`test_faz_b_arduplane_sablon` **44 → 45**, `test_t235_alan_etiketi` **56 → 57**,
MK15 **39 → 39** (yeni assert var olan teste eklendi).

Eklenen satırlarda `skip` / `expectedFailure` / `maxDiff` / `sleep(` **araması: 0 sonuç**.
Hiçbir ön kayıtlı sabit gevşetilmedi, hiçbir kilit satırı silinmedi.

**İki testin BEKLENTİSİ değişti** (gevşeme değil, **düzeltme** — ikisi de kaynağında
gerekçeli):
1. `test_varlik_bicimli_tilde_cizigi_ayiklanir` → `..._YAPI_URETMEZ_ama_aday_sayilir`:
   `&#126;&#126;X&#126;&#126;` **çizgi açmaz**, ayıklanması yanlıştı. Assert 2 → 3.
2. `test_NEGATIF_kacinilan_etiket_ornegi_hayalet_cizik_uretmez` →
   `..._HAYALET_ETIKET_uretmez_ama_kod_DISINDA_ADAYDIR`: `&lt;s&gt;` kod dışında artık
   **hatadır** (önce hiç görülmüyordu). Assert 1 → 5.

---

## 9. Depo denetimi — hangi kilitler hâlâ açık

`acik_kilitler.md` (üretici `scripts/belge_kilidi_denetle.py`, salt okuma, AST, **kapı değil**):

```
| olcum | deger |
|---|---|
| taranan test dosyasi | 206 |
| markdown okuyup dizge arayan | 58 |
| ortak yardimcidan GECEN | 5 |
| ACIK (yardimci kullanmayan) | 53 |
| ACIK **ve** kendi cizik kalibi olan (agir) | 4 |
| GECENLERDEN on kayitli METIN ESITLIGI kullanan (D-465) | 5 |
| GECENLERDEN BLOK esitligi (`bloklar`) kullanan (D-465 (1)) | 5 |
```

---

## 10. SINIR LİSTESİ — bu kilitler neyi durdurur, neyi DURDURMAZ (D-465 (4))

> **Bu kilitler İYİ NİYETLİ AŞINMAYI durdurur: ölçümden sonra belgeye sessizce sızan
> gevşetme, geri alma, "artık geçti" yazımı, eşik kaydırması, yanlışlıkla silme.
> EL YAPIMI VARLIK KAÇIŞI ÜRETEN BİR DÜŞMANI DURDURMAZ VE DURDURMASI BEKLENMEZ.**
> Bu proje bir tehdit modeli değil, bir **doğrulama disiplini** kurar. Aşağıdaki kalan
> kaçışlar **kovalanmayacaktır**; sayılıp yazılmalarının nedeni, bir sonraki turda
> "kapatıldı" sanılmamalarıdır.

### 10.1 ÖLÇÜLÜP KAPATILAN kaçış sınıfları (sayı: 31 gerçek dosya mutantı)

| sınıf | mutantlar | adet | yöntem |
|---|---|---|---|
| çizme sözdizimi (`~~`, `~`, `<del>`, `<s>`) | D1b, D1c, D1d, A3, A4, A5, W1, W6 | **8** | beyaz liste + ayıklama |
| HTML **varlık** biçimi (`&#822;`, `&#x336;`) | Y4, Y4b | **2** | varlık çözümlemesi (yalnız KARAKTER tespiti) |
| **yapı üreten** varlık biçimi (`&#96;`, `&#96;<s>`) | X15, X16, X17 | **3** | `_COZULMEZ` + doğrudan aday (**T240-C**) |
| olumlu hüküm ailesi + vurgu/yazım varyantı | A8, W2, W3, W4, W7, Y5 | **6** | `olumlu_hukum_var` (geniş aile) + `normalize` vurgu sökme |
| sayı/birim/karşılaştırma yazımı | A6, A7, A9, Y10 | **4** | `normalize` katlamaları (**K3 ile genişledi**) |
| anahtar sözcük **taşımayan** çelişkili ikinci hüküm | D1e, V1, V3, Y7a, Y7b, Y7c, Y11 | **7** | kapalı hüküm cümlesi kümesi + **blok eşitliği** |
| ön kayıtlı eşiğin **ikizi** (ikinci, gevşetilmiş kabul ölçütü) | D461 | **1** | `kabul_olcutu_tekligi` (a+b+c+d) |
| **TOPLAM** | | **31** | |

Çürütücünün X13/X14'ü (birim sözcüğü / `cm` öneki) koşucuya **eklenmedi** — gerçek dosya
mutantı sayısı ön kayıtlı 31'dir. İkisi de birim düzeyinde ölçüldü
(`test_K3_rakip_esik_BIRIM_SOZCUGU_ile_yazilinca_DUSER`,
`test_K3_rakip_esik_farkli_ONEK_ile_yazilinca_DUSER`) **ve** gerçek §4 artık metin
eşitliğine bağlı olduğu için o belgede iki kilitten birden geçerler.

### 10.2 KALAN teorik kaçışlar — sayıldı, ölçüldü, KOVALANMAYACAK

| # | kaçış | durum |
|---|---|---|
| 1 | **Ön kayıtlı sabiti belgeyle BİRLİKTE değiştirmek.** Eşitlik bunu göremez. | **Tasarım gereği açıktır** — ön kaydın amacı kaçışı imkânsız kılmak değil, **görünür** kılmaktır. Hakemi test değil, **insan denetimi**dir (madde 19: bir iş, onu yazanın onayıyla kapanmaz). |
| 2 | **Yalnız boşluk/satır sonu taşıyan anlam.** `bloklar` boşluğu normalleştirir; satır sarması ve çift boşluk EŞİTLİĞİ BOZMAZ (ölçüldü). | Bilerek. Kod çitlerinin İÇİ harfi harfine korunur; dört belgede satır sonunun anlam taşıdığı başka blok YOK (ölçüldü). |
| 3 | **Eşitliğe çevrilmemiş bölümlere** çelişkili hüküm yazmak. CONTRACTS'ta 52, GOSTERICI_KURULUM'da 6, README'de 13 bölüm başlığı eşitlik dışındadır. | Sayıldı. Bu bölümlerde `beyaz_liste_disi_cizik` (belge geneli) ve `olumlu_hukum_var` çalışır; **metin eşitliği yoktur.** T242'nin kapsamı. |
| 4 | **Depo genelindeki 53 açık kilit** (§9). Hiçbiri mutasyonla sınanmadı. | **ÖLÇÜLEMEDİ ≠ GEÇTİ.** Sayı, "hangi kilitler delinebilir" sorusunun ÜST SINIRIDIR, kusur sayısı değildir. |
| 5 | **Kapalı hüküm cümlesi kümesinin seçicisi.** §6.8'in 51 cümlesinin 37'si, §5'in 26 cümlesinin 23'ü kümededir. Kümenin dışına **anahtar sözcük taşımayan** bir hüküm yazılabilirdi. | **T240-B'de ÖLÇÜLDÜ: kaçıyordu** — çürütücünün X3'ü (CONTRACTS §6.8, MK15 çıkış 0) ve X7'si (GOSTERICI §5, çıkış 0). **T240-C'de iki bölüm de metin eşitliğine bağlandı; ikisi de YENİDEN ÖLÇÜLDÜ ve artık DÜŞÜYOR** (aşağıdaki ham çıktı). Kapalı küme **ikinci** kilit olarak durur. |
| 6 | **Kod çitlerinin içeriği** eşitlik bloğunda harfi harfine korunur ama çit **dışındaki** hükümlerle tutarlılığı denetlenmez. | Kod içeriği ayrıca koddan üretilir (⟨DRM_BORU⟩, ⟨ÖRNEK⟩) — o kadarı ölçülü. |
| 7 | **Markdown okuyucu farkları.** "Varlık YAPI üretmez" kuralı CommonMark/GFM'e dayanır; başka bir işleyici farklı davranırsa analiz değişir. | Kaynak: CommonMark spec "Entity and numeric character references"; GitHub GFM aynı. Başka işleyici **ÖLÇÜLMEDİ**. |
| 8 | **Görsel/PDF çıktıda gizleme** (CSS, tema, yazı rengi). | Kapsam DIŞI: kilitler markdown KAYNAĞINI okur. |
| 9 | **Birim testindeki A10/A7/§7.5 çapaları CANLI dosyayla karşılaştırılmaz.** 12 Eylül 2026'da alınmış anlık görüntüdür; ATOLYE kâğıdı değişirse çapa sessizce eskir. | **Bilerek** — ATOLYE kâğıdı 12 Eylül'de İNSAN tarafından doldurulacaktır ve bir yardımcı birim testi o doldurmada kırılmamalıdır. Sınıf docstring'inde açıkça yazılıdır. `ATOLYE_TEST_GUNU_20260912.md` ve `CONTRACTS.md §7.5` **hiçbir süitte metin eşitliğiyle kilitli DEĞİLDİR** — T242'nin kapsamı. |

**X3/X7 yeniden ölçümü** (gerçek dosya + gerçek süit, sha256 ile bayt-eş geri yükleme):

```
X3 CONTRACTS §6.8 anahtarsiz celiski     cikis=1 -> DUSTU  geri_bayt_es=True
    AssertionError: Tuples differ: ('###[4574 chars].', '**Bağlayıcı ilkeler:**', '- Kanıt yazımı [1919 chars]a).') != ('###[4574 chars].', 'Not (12 Eylül): etiket biçimi isteğe bağl[2001 chars]a).')
X7 GOSTERICI §5 anahtarsiz celiski       cikis=1 -> DUSTU  geri_bayt_es=True
    AssertionError: Tuples differ: ('## [4807 chars]*.", '- **Geri alma:** `sudo systemctl disable[134 chars]t).') != ('## [4807 chars]*.", "- Not (12 Eylül): bu davranış 12 Eylül'd[198 chars]t).')
```

### 10.3 Ne DEĞİŞMEDİ

- `cizikleri_ayikla` tek tildede **belgelenmiş bir istisna** taşır: `~<rakam>` ("~3 s",
  "~8 Hz") yaklaşık işaretidir — üç belgede ölçülen tek meşru kullanım budur.
- `kabul_olcutu_tekligi` kural (b) **yalnız** ön kayıtlı ölçütün kısıtladığı büyüklüklere
  bakar; karşılaştırmasız sayılar ("`FENCE` 50 m altında") eşik değildir.
- **Ölçülen sınır (iddia edilmiyor):** T229-D2 çapasında (b) tetiklenmez (ön kayıtlı ölçütün
  eşikleri birimsizdir); orada mutantı (c) ve (d) yakalar — testte `assertNotIn` ile kayıtlı.

---

## 11. Bağımsızlık

**Madde 19:** bu işi yazan ajan **kendi işini KABUL ETMEZ**. T240-C bir KAPANIŞ turudur
(mimar kararı D-465): T240 ailesi bundan sonra yeni tur açmaz; kapatma onayı ayrı bir
denetimdedir.
