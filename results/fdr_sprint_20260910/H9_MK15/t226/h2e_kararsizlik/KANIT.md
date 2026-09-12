# H2e kararsızlığı — kök neden ve kanıt (12 Eylül 2026)

**İş:** `tests/test_yks_mk15_hakem_ekrani.py::H2e_RotaYokSonrasiAnaHarita`
tam süitte 6 alt testte düşüyor, tek başına geçiyor.
**Gözlem (mimar, ana ağaç):** `mimar_011758_tam_suit.txt`
→ `Ran 2620 tests · FAILED (failures=6, skipped=12)`; iki hata biçimi
`:726` "NO_ROUTE yerleşimi OPEN_ROUTE'a sızdı" ve `:728`
`'.!frame3.!frame.!canvas' unexpectedly found in {...: (34, 189, 227)}`
(1,5 ölçekte `(51, 156, 243)`).

> **Atıf kaynağı (12 Eyl 06:35, çürütücü KUSUR 1 üzerine düzeltildi).**
> Bu çıktı mimarın ANA AĞACINDA (`O:\navitas`) `results/push_kapisi/20260912_011758/`
> altında **izlenmeyen** (untracked) bir dizinde duruyordu; hiçbir commit'te yoktu,
> yani atıf repodan doğrulanamıyordu (anayasa md. 6 · D-209). İki dosya bu kanıt
> dizinine **bayt-eş** kopyalandı ve atıflar buraya çevrildi:
> `mimar_011758_tam_suit.txt` (sha256 `1af052cfdf8bb369…b292b6b4`),
> `mimar_011758_genel_kapi.txt` (sha256 `64930014f4afe964…c06ad7491`).
> Ana ağaçtaki özgün dizin commit'lenmedi (orası dalın dışı); izlenen kopya budur.

Yorumlayıcı: `O:\navitas-local-train\venv\Scripts\python.exe -X utf8 -B`.
Çalışma ağacı: `O:\navitas\.claude\worktrees\wf_56b658bb-aff-1`.

---

## 1. Yöntem

1. **Yeniden üretme denemesi.** Tam süit (`scripts/push_kapisi.py --kuru`)
   **3 kez** koşuldu. Üçü de H2e'yi düşürmedi:
   `results/push_kapisi/20260912_013837` (ortam eksikleri, H2e YOK),
   `20260912_015144` → `Ran 2616 · OK (skipped=22)`,
   `20260912_020233` → `Ran 2616 · OK (skipped=22)` (3. koşum H2e'ye geçici
   durum kaydı eklenmiş hâliyle).
   ⚠ İlk koşumdaki 21 düşüş H2e ile ilgisizdi: çalışma ağacında `models/`,
   `data/kuru_kosu_fikstur/images`, `data/arena_kompozit/images`,
   `jetson_paket/models` yoktu. Ana ağaçtaki (git dışı) dosyalar sabit bağ
   (hardlink/junction) ile ağaca getirildi; keşif sayısı 2620'ye döndü.
2. **Sıkıştırılmış bağlam (delta debugging).** `h2e_tani.py`:
   - `--tum-import` (2620 testin tamamı içe aktarılır, yalnız H2e koşar) ×3 → OK
     (`d1_tum_import.txt`),
   - H2e'den önce gelen **46 Tk/yks modülünün tamamı aynı süreçte koşturuldu**,
     sonra H2e ×2 → OK (`d2_tk_onek.txt`, `onceki_tk_moduller.txt`).
   Yani kusur ne içe aktarma sırasından ne de Tk modüllerinin bıraktığı
   durumdan geliyor.
3. **Ölçüm.** `_olculu_alan` değerleri gerçek Tk ile ölçüldü
   (`olcum_alan_yalniz.txt`, 742×450 tuval):
   | NO_ROUTE `detay` | OLCEK 1,0 | OLCEK 1,5 |
   |---|---|---|
   | boş / alan yok (tek satır bant) | **(34, 189, 227)** | **(51, 156, 243)** |
   | 624 karakter (uzun bant) | — | (51, 478, **0**) |
   Mimarın gördüğü iki değer **tam olarak "tek satırlık bant"** değerleridir.
4. **Provokasyon.** Yabancı bir `127.0.0.1` ucundan (ayrı soket) NO_ROUTE
   serpildi → düşüş yeniden üretildi.

## 2. Kök neden — FİKSTÜR (ürün kusuru DEĞİL)

⚠ **Bu bölüm 12 Eylül'de YENİDEN YAZILDI** — bağımsız çürütücünün KABUL
hükmündeki iki ZORUNLU düzeltme (anayasa md. 6: kanıtsız bulgu yazılmaz).
İlk sürüm kök nedeni "imza eşleşmesine" dayandırıyordu; o dayanak **hem
yanlış atıflıydı hem ayırt edici değildi**. Doğrusu §2.1'dedir; imzanın neden
hüküm taşıyamayacağı §2.3'te ölçümle yazılıdır.

### 2.1 ASIL DAYANAK — ürün kaynağından tümdengelim

Üç satır kök nedeni **mantıksal olarak zorluyor** (satır numaraları bu daldaki
`comms/yks_gui.py` sürümüne göredir):

| Satır | Kod | Ne yapar |
|---|---|---|
| `comms/yks_gui.py:1593` | `alanlar.pop(str(c), None)` | `_harita_ciz` HER çizimde ölçülü alan önbelleğini ya **yazar** ya **siler** — üçüncü hâl yok (`:1590-1594`) |
| `comms/yks_gui.py:1963` | `self._harita_ciz()` | YENİ bir OPEN_ROUTE işlenirken **aynı çağrı içinde, eşzamanlı** çizim yapılır |
| `comms/yks_gui.py:1911` | `self.rota_yok = None` | OPEN_ROUTE `rota_yok`u **temizler** |

Zincir:

1. OPEN_ROUTE işlenince `rota_yok = None` olur ve `_harita_ciz()` **aynı
   çağrının içinde** koşar. `rota_yok` boş, ana harita `inset_var` — yani
   `rota_yok_metni` yok — olduğundan ölçülü yerleşime **girilmez** ve
   `alanlar.pop(...)` ile önbellek **silinir**.
2. Öyleyse ölçüm anında `_olculu_alan` DOLU ise, bizim OPEN_ROUTE'umuzdan
   **SONRA** bir NO_ROUTE işlenmiş olmak **ZORUNDADIR**. Başka yol yok:
   önbelleği dolduran tek kod yolu ölçülü yerleşimdir, ona da yalnız
   `rota_yok_metni` varken girilir.
3. Test kendi çerçevelerini **artan seq** ile ve sırayla gönderir; kendi
   NO_ROUTE'ları ölçülen OPEN_ROUTE'tan ÖNCEDİR (`_mesaj_ver` her çerçevenin
   işlendiğini bekler). Öyleyse o NO_ROUTE **YABANCIDIR** — aynı süreçte
   koşan başka bir ucun datagramıdır.

Sonuç: **ürünün önbellek yaşam döngüsü kusursuzdur; kusur fikstürdedir.**
Bu çıkarım hiçbir ölçüm gürültüsüne bağlı değildir — yalnız üç kaynak satırına
ve testin kendi gönderim sırasına dayanır. Bağımsız çürütücü aynı tümdengelimi
kendi yolundan kurdu ve C1/C2/C3 mutasyonlarıyla sınadı (§2.3, §4).

### 2.2 Fikstürün iki kusuru

**(a) Kaynak kilidi bu fikstürde hiçbir şey ayırmıyor.**
`comms/yks_gui.py:739 mesaj_kaynagi_dogrula` İHA verisi (OPEN_ROUTE /
NO_ROUTE / IHA_LANDED) için **yalnız IP'ye** bakar — `adr[0] == iha_peer[0]`.
Bu **saha kuralıdır ve doğrudur** (Jetson'un algı yayıncısı efemer port
kullanır). Ama fikstür üç ucu da `127.0.0.1`'e bağlıyordu: aynı süreçte
koşan **herhangi** bir ucun gönderdiği tek bir NO_ROUTE datagramı hakem
ekranının `rota_yok` alanını eziyor.

**(b) Ölçüm öncesi bekleme SABİT UYKUYDU ve durumu EKSİK denetliyordu.**
`_mesaj_ver` OPEN_ROUTE'ta yalnız `rota.seq`e bakıyor, `rota_yok`un
temizlendiğine bakmıyordu; sonra körlemesine `_pompala(lambda: False, 0.15)`
ile 150 ms olay pompalıyordu. O pencerede işlenen bir NO_ROUTE:
`rota_yok` yeniden dolar → `_harita_ciz` ölçülü yerleşime girer →
`_olculu_alan[str(harita)]` yazılır → sonraki `_cizim()` OPEN_ROUTE
çizimini **ölçülü** üretir. Test bunu "ürün sızdırdı" diye okur.

### 2.3 İmza eşleşmesi AYIRT EDİCİ DEĞİLDİR (yanlış atıf düzeltildi)

İlk sürüm burada `mutasyon_M4.txt`ten iki satır alıntılayıp "mimarın
çıktısının birebir aynısı" diyordu. **İki ayrı hata vardı.**

**Hata 1 — alıntı o dosyada YOK.** Ölçüm (çürütücü, yeniden doğrulandı;
12 Eyl 06:36'da **kopyalanan dosya adıyla yeniden koşuldu**, ham çıktı
`atif_grep_cikti.txt`):

```
$ grep -c "unexpectedly found" mutasyon_M4.txt
0
$ grep -c "unexpectedly found" mimar_011758_tam_suit.txt
4
```

`mutasyon_M4.txt`in GERÇEK altı düşüşü (dosyadaki `AssertionError` satırları,
sırasıyla):

```
AssertionError: '.!frame3.!frame.!canvas' not found in {} : Önkoşul: uzun NO_ROUTE arena alanını değiştirmeli
AssertionError: Lists differ: [...[94.8, 121.6, 133.2, 390.40000000000003]...] != [...[34.0, 96.0, 354.0, 416.0]...]
AssertionError: Lists differ: [...[34.0, 96.0, 354.0, 416.0]...] != [...[94.8, 121.6, 133.2, 390.40000000000003]...]
AssertionError: Lists differ: [...144.0]...] != [...156.0]...]
AssertionError: False is not true : ekran çerçeveyi TAM işlemedi: {... 'seq': 146 ...} · rota=145 · rota_yok={... 'seq': 923 ...} · kuyruk=0 · kaynak reddi=0
AssertionError: False is not true : ekran çerçeveyi TAM işlemedi: {... 'seq': 148 ...} · rota=147 · rota_yok={... 'seq': 940 ...} · kuyruk=0 · kaynak reddi=0
```

Mimarın 12 Eylül 01:17 çıktısı (`mimar_011758_tam_suit.txt`):

```
AssertionError: Lists differ: [...34.0, 96.0]...] != [...34.0, 189.0]...]
AssertionError: '.!frame3.!frame.!canvas' unexpectedly found in {'.!frame3.!frame.!canvas': (34, 189, 227)}   (×2)
AssertionError: Lists differ: [...144.0]...] != [...156.0]...]
AssertionError: '.!frame3.!frame.!canvas' unexpectedly found in {'.!frame3.!frame.!canvas': (51, 156, 243)}   (×2)
```

**Ölçülene çekilmiş iddia:** altı düşüşten **yalnız biri** örtüşüyor — 1,5
ölçekte `144.0 ↔ 156.0`. Diğer dördü ters yönlü (`not found in {}`), farklı
koordinatlı (`94.8, 121.6, …`) ya da amelenin bu görevde YENİ yazdığı tanı
iletisidir (`ekran çerçeveyi TAM işlemedi`). Yani **M4 düzeltme öncesi
fikstürün tamamı değil, KISMİ BİR GERİ ALMADIR**; "birebir aynı" iddiası
kanıtsızdı ve geri çekilmiştir.

**Hata 2 — imza zaten ayırt edici değil.** Çürütücünün C1 mutasyonu
(`_harita_ciz`in `alanlar.pop(str(c), None)` satırı `pass` yapılır: GERÇEK
ürün önbellek sızıntısı, **yabancı çerçeve enjeksiyonu YOK**) aynı imzayı
M4'ten **daha iyi** üretir — `curutucu_C1.txt`, 6/6 kırmızı, dört
`unexpectedly found` satırı dâhil. Öyleyse "(34,189,227)/(51,156,243)
değerleri fikstür hipotezini kanıtlar" akıl yürütmesi **tek başına
GEÇERSİZDİR**: aynı imzayı bir ürün kusuru da üretir. Kök nedeni kanıtlayan
şey imza değil, §2.1'deki tümdengelimdir. Ayrımı ölçen mutasyon çiftidir:

| Mutasyon | Ne değişti | Enjeksiyon | Sonuç | Ne öğretir |
|---|---|---|---|---|
| `curutucu_C1.txt` | ÜRÜN: önbellek silinmiyor | YOK | **6/6 KIRMIZI** | düzeltilmiş test gerçek ürün sızıntısını HÂLÂ yakalıyor (kapı gevşemedi); imza fikstüre özgü DEĞİL |
| `curutucu_C2.txt` | ÜRÜN: kaynak kilidi IP denetimi kapalı | VAR | **6/6 KIRMIZI** | düzeltmenin yükünü ürünün KENDİ kilidi taşıyor; test kilidi baypas etmiyor, ÖLÇÜYOR |
| `curutucu_C3.txt` | TEST: adres yalıtımı geri | YOK | **YEŞİL** | kusur YABANCI ÇERÇEVE gerektiriyor; yalıtımı kaldırmak tek başına düşürmüyor — seyrekliğin açıklaması |

⚠ **Açık kalan:** 12 Eylül 01:17 koşumunda o datagramı GÖNDEREN ucun kimliği
saptanamadı (3 tam süit koşumunda olay tekrar etmedi). Kanıtlanan şey
**MEKANİZMADIR**, olayın kendisi değil; mekanizma hem tümdengelimle (§2.1)
hem enjeksiyonla (`d3_yabanci_enjeksiyon.txt`) gösterilmiştir.
## 3. Düzeltme (yalnız fikstür; ürün kodu DEĞİŞMEDİ)

`tests/test_yks_mk15_hakem_ekrani.py`:

1. `_GercekEkran.IHA_ADRESI = "127.0.0.2"`, `IKA_ADRESI = "127.0.0.3"` —
   İHA/İKA uçları **ayrı geri döngü adresinde**. Artık ürünün KENDİ kaynak
   kilidi yabancı çerçeveyi reddediyor. Gevşetme değil: saha kurulumunun
   (İHA ayrı IP) aynısı, üstelik kilit artık gerçekten ölçülüyor.
   (Bu makinede `127.0.0.0/8` bağlanabiliyor, kaynak adresi korunuyor —
   ölçüldü.)
2. `_mesaj_ver` **sabit uykusuz**: hazır koşulu (1) `app.gelen.empty()`
   (işlenmemiş çerçeve yok) **ve** (2) durumun çerçevenin tam karşılığı
   olması — OPEN_ROUTE'ta `rota.seq == seq` **ve** `rota_yok is None`.
   Koşul sağlandıktan sonra ölçüme kadar **hiç olay pompalanmıyor**, yani
   ölçüm penceresi kapalı.
3. `_yalniz_bizim_cerceveler` önkoşulu: sızıntı hükmünden önce ekranın
   **yalnız bu testin** çerçevelerini işlediği doğrulanır
   (`sayac[OPEN_ROUTE]`/`sayac[NO_ROUTE]`). Tutmazsa düşüş "YABANCI ÇERÇEVE"
   der — ürünü haksız yere suçlamaz.
4. H2e'deki `_pompala(lambda: False, 0.2)` yerine **gerçek yerleşim koşulu**:
   `winfo_ismapped()` **ve** tuval boyutu 742×450. (H1b'de aynı sınıf
   `d812b1e2` ile kapanmıştı.)
5. Hazır koşulu düşerse mesaj artık durumu yazıyor: `rota`, `rota_yok`,
   kuyruk boyu, kaynak reddi sayısı — "ürün temizlemedi" ile "yabancı
   çerçeve geldi" ayrımı düşüş satırında görünüyor.

Hiçbir assert gevşetilmedi, kapsam daraltılmadı, `skip`/`expectedFailure`
kullanılmadı. Yeni bağımlılık yok. Ürün kodu (`comms/yks_gui.py`)
**değişmedi** — M5 mutasyonu dışında, o da `finally` ile bayt bayt geri
yazıldı (`git status` temiz).

**Süre kazancı (yan etki):** modül 22,3 s → 14,8 s; sabit uykular kalktı.

## 4. Kanıt

| Ne | Dosya | Sonuç |
|---|---|---|
| Tam süit ×3 (düzeltme öncesi) | `results/push_kapisi/20260912_015144`, `…_020233` | H2e düşmedi (yeniden üretilemedi) |
| Tüm modüller içe aktarılmış ×3 | `d1_tum_import.txt` | OK |
| 46 Tk modülü önce koşuldu ×2 | `d2_tk_onek.txt` | OK |
| **Mimarın 01:17 tam süiti** (atıf dayanağı, bayt-eş kopya) | `mimar_011758_tam_suit.txt`, `mimar_011758_genel_kapi.txt` | `Ran 2620 · FAILED (failures=6, skipped=12)`; `grep -c "unexpectedly found"` = **4** (yeniden koşuldu 12 Eyl 06:35) |
| §2.3 atıf doğrulaması (ham grep çıktısı) | `atif_grep_cikti.txt` | M4 = **0**, mimar çıktısı = **4**; dört satırın dosyadaki satır numaraları (399/408/434/443) + sha256 |
| Alan ölçümü | `olcum_alan_yalniz.txt` | (34,189,227) / (51,156,243) = tek satır bant |
| Yabancı enjeksiyon, düzeltme ÖNCESİ | `d3_yabanci_enjeksiyon.txt` | 6 düşüş (aynı imza) |
| Yabancı enjeksiyon, düzeltme SONRASI | `d4_enjeksiyon_duzeltme_sonrasi.txt` | OK ×2, kabul edilen çerçeve 9/6 (tam) |
| Mutasyon M0–M4 | `mutasyon_ciktisi.txt`, `mutasyon_M*.txt` | **GECTI** (M1/M2/M4 kırmızı, M0/M3 yeşil) |
| Enjeksiyon altında 5 ardışık koşum | `ardisik_1..5.txt` | 5/5 OK, her koşumda 9 OPEN / 6 NO_ROUTE |
| Tam süit ×4 (düzeltme sonrası) | `kapi_kosum_A/B/C/D.txt` | A: 2616 OK · B, C, D: **Ran 2620 · OK (skipped=19)** |
| Tam süit ×2 (SON içerik) | `kapi_kosum_E.txt`, `kapi_kosum_F.txt` | **Ran 2620 · OK (skipped=19)** (502,8 s / 496,2 s) |
| Genel kapı (madde 14) | yukarıdaki her koşum + `genel_kapi_son.txt` | **kol1 15/15 · kol2 şerit 15/15** |
| **Çürütücü mutasyonu C0–C4** (bağımsız) | `curutucu_mutasyon.py`, `curutucu_C0..C4.txt` | C1/C2 **KIRMIZI**, C0/C3/C4 yeşil — §2.3 |

(A koşumu `wheels`/`firmware` bağlanmadan önce yapıldı; o yüzden 2616.
B'den sonra keşif sayısı mimarın ağacıyla aynı: **2620**.)

### Mutasyon tablosu

`mutasyon_h2e.py` gerçek kaynak dosyayı **bayt düzeyinde** bozar ve `finally`
içinde sha256 doğrulayarak aynen geri yazar (satır sonu dâhil).

| # | Mutasyon | Hedef | Beklenen | Gerçek |
|---|---|---|---|---|
| M0 | yok (enjeksiyon var) | — | 0 | 0 |
| M1 | ayrı geri döngü adresi geri alınır | test | 1 | 1 |
| M2 | hazır koşulu gevşetilir + 0,15 s sabit uyku geri gelir | test | 1 | 1 |
| M3 | yabancı çerçeve önkoşulu silinir (adres yalıtımı durur) | test | 0 | 0 |
| M4 | düzeltme öncesi fikstürün tamamı + seyrek enjeksiyon | test | 1 | 1 |
| M5 | **ÜRÜN**: OPEN_ROUTE `rota_yok`u temizlemiyor (enjeksiyon YOK) | ürün | 1 | 1 |

`MUTASYON_SONUC GECTI` (`mutasyon_ciktisi.txt`).

- **M4** KISMİ bir geri almadır: altı düşüşünden yalnız biri (1,5 ölçekte
  `144.0 ↔ 156.0`) mimarın imzasıyla örtüşür. İlk sürümdeki "birebir aynı"
  iddiası **geri çekildi** — gerekçe ve ölçüm §2.3'te.
- **M5 kapının gevşemediğinin kanıtıdır**: gerçek ürün sızıntısında test
  KIRMIZI olur ve tanıyı açıkça yazar —
  `ekran çerçeveyi TAM işlemedi: {...OPEN_ROUTE seq 144...} · rota=144 ·
  rota_yok={...NO_ROUTE seq 143...} · kuyruk=0 · kaynak reddi=0`
  (yani "ürün temizlemedi", "yabancı çerçeve yok" ayrımı düşüş satırında).
- **M3**'ün yeşil olması tasarım gereğidir: yalıtım tek başına yeterlidir,
  sayaç önkoşulu ikinci savunma hattı ve **tanı** içindir.
- **Çürütücü mutasyonları** (C0–C4) bu görevin amelesinden BAĞIMSIZ yazıldı ve
  koşuldu; `curutucu_mutasyon.py` çürütücünün kendi çalışma ağacı/geçici dizin
  yollarını **olduğu gibi** taşır (kanıt bütünlüğü için değiştirilmedi), bu
  yüzden yeniden koşmak için `KOK`/`CIK` sabitleri güncellenmelidir. Çıktılar:
  `curutucu_C0..C4.txt`. C4 çürütücünün kendi kurgu hatasıdır (ana haritada
  `olcu["alan"]` ROTA YOK bandı yokken zaten `None`; mutasyon yakın-etkisiz) —
  test zayıflığı DEĞİLDİR.

## 5. Mimarın dikkatine — ürün tarafında ayrı bir gözlem (bu görevin konusu DEĞİL)

Uzun `detay` taşıyan NO_ROUTE'ta ana haritanın arena alanı 742×450 tuvalde
`(51, 478, 0)` çıkıyor: **ölçek 0**, yani arena tamamen kayboluyor
(`_harita_olculu_yerlesim` üst bandı 12 tura kadar aşağı itiyor, alt sınır
yok). Hakem ekranında uzun bir ret gerekçesi haritayı yutabilir.
Ölçüm: `olcum_alan_yalniz.txt`. Karar mimarındır; bu görevde
**değiştirilmedi**.
