# T240 — Ortak belge kilidi yardımcısı ve belge kilitlerinin geçirilmesi

**D-460 karar 2 + T240'a verilen RED hükmünün kapatılması (T240-B) + D-461 mimar eki.**

Bağımsız mimar denetimi (D-460) T226-D2 · T228-D2 · T221-D3'ü REDDETTİ; ortak gerekçe tekti:
her test dosyası çizik ayıklamasını **kendi** yazmıştı ve üçü de yalnız `~~...~~` biliyordu.
Denetimde kurulan **19 gerçek dosya mutasyonunun 19'u kaçmıştı**. T240 o 19 kaçışı kapattı.

**T240'ın kendisi de bağımsız çürütücüden RED aldı** (kapılar yeşil, 19/19 + 4/4 doğrulandı,
kilit hiçbir yerde gevşemedi — ama çürütücünün 12 yeni mutasyonundan 5'i kaçtı, ikisi işin
"kapattım" dediği sınıfların **içinde**). T240-B o 5 kaçışı kapatır, **beyanları ölçülene
çeker** ve D-461'in zorunlu ek kilidini (ön kayıt tekliği) ekler.

Bu belge yalnız **koşulan** komutların çıktısını kaydeder. Ham çıktılar:
`kapi_ciktisi.txt` (kapı) ve `mutasyon_ciktisi.txt` / `mutasyon_kosum.raw.txt` (mutasyon).

---

## 1. Ne değişti

| dosya | ne |
|---|---|
| `tests/belge_kilidi.py` | Ortak yardımcı (yalnız stdlib): `cizikleri_ayikla`, `beyaz_liste_disi_cizik`, `normalize`, `olumlu_hukum_var`, `on_kayitli_metin_esit`, `hukum_cumleleri`, **`kabul_olcutu_tekligi` (YENİ, D-461)**. **T240-B:** `_varliklari_coz` / `_varlik_cozumle` (HTML varlık çözümlemesi, `import html`), ön kayıtlı `HUKUM_SOZCUKLERI` ve `KABUL_CELISKI_SOZCUKLERI` listeleri, cümle sınırına paragraf/madde/tablo satırı eklendi. Her fonksiyonun docstring'inde **hangi ölçülen kaçış** için var olduğu yazılı. |
| `tests/test_belge_kilidi.py` | Yardımcının kendi kapısı: **42 → 60 test**. Her normalleştirme kuralı için pozitif + negatif vaka; uydurma çizme sözdizimi; **T240-B:** `HtmlVarlikBicimi` (7 test) ve `KabulOlcutuTekligi` (7 test) sınıfları. |
| `tests/test_yks_mk15_hakem_ekrani.py` | H4e (CONTRACTS §6.8) yardımcıdan geçti; beyaz liste, ön kayıtlı kaynak hükmü (örneği **koddan**), kalın başlıklı paragraf demeti, paragraf komşuluğu. **T240-B:** §6.8'in **kapalı hüküm cümlesi kümesi** (YENİ; 37 cümle, ön kayıtlı). |
| `tests/test_isaretli_gosterici.py` | `_cizili_ayikla` / `_normal` / `_gecti_bul` yardımcıya bağlı ince kabuk; G8'e belge geneli beyaz liste dışı çizik kilidi. **T240-B:** §5'in **kapalı hüküm cümlesi kümesi** (YENİ; 23 cümle, ön kayıtlı; kod çitleri hariç). |
| `tests/test_faz_b_arduplane_sablon.py` | §6.6 başlığı ve `**Sonuç: … KOŞULMADI.**` ön kayıtlı metin eşitliğiyle bağlandı; ölçüm etiketleri, olumlu hüküm ailesi ve kapalı cümle kümesi; HTML kara listesi beyaz listeye çevrildi. **T240-B:** kapalı kümenin **SEÇİCİSİ** genişletildi (`("prova","olcut")` → ön kayıtlı `HUKUM_SOZCUKLERI` + alan sözcükleri); küme **5 → 18** cümle. |
| `tests/test_t235_alan_etiketi.py` | **T240-B (YENİ kullanım):** `ON_KAYIT §4`'e **ön kayıt tekliği** kilidi (`kabul_olcutu_tekligi`) — D-461'in zorunlu ek maddesinin gerçek belge üzerindeki ilk uygulaması. |
| `scripts/belge_kilidi_denetle.py` | Depo denetimi (kapı DEĞİL, çıkış 0): `tests/` altında markdown okuyup dizge arayan testleri bulur, yardımcıyı **kullanmayanları** raporlar → `acik_kilitler.md`. |

**Ürün kodu ve belgelerin baytları değişmedi.** Dört belgenin sha256'sı mutasyon koşumundan
önce ve sonra aynı: `CONTRACTS.md 741a9ca26dde…`, `GOSTERICI_KURULUM.md e01d16821d44…`,
`config/pixhawk/README.md e2efd44838b6…`, `…/H1/t235/ON_KAYIT.md 7840e9331975…`.

---

## 2. T240-B: çürütücünün RED gerekçesi, madde madde

Çürütücü **beyan edilen her şeyi doğruladı** (kapılar, 19/19 + 4/4, bayt-eşlik, gevşememe),
ama kendi 12 mutasyonundan 5'i kaçtı. Aşağıda her biri **kapatıldı ve ölçüldü**:

| # | kaçan | nerede | neden kaçtı | T240-B çözümü (YAPISAL) |
|---|---|---|---|---|
| Y4 | `&#822;` (U+0336'nın HTML varlık biçimi), harf harf | CONTRACTS §6.8 | tarayıcı varlık biçimini **hiç görmüyordu**; aynı karakterin çıplak hâli (Y3) DÜŞÜYORDU | `_varliklari_coz`: kod aralıkları maskeliyken `html.unescape`; `cizikleri_ayikla` / `normalize` / `beyaz_liste_disi_cizik` üçü de varlık-çözümlü metni görür |
| Y4b | `&#x336;` (onaltılık) | CONTRACTS §6.8 | aynı | aynı |
| Y7 | kalın başlık **TAŞIMAYAN** ve kaynak paragrafının hemen ardına **DEĞİL** başka yere konan çelişkili hüküm paragrafı | CONTRACTS §6.8 | kalın başlık demeti onu saymıyor, tam eşitlik ve komşuluk kilitleri bozulmuyordu | §6.8'e **kapalı hüküm cümlesi kümesi** (T221'de zaten vardı, buraya verilmemişti) |
| Y5 | aile **dışı** eş anlamlı: "hatasız yürüdü / kusursuz işledi" | GOSTERICI_KURULUM §5 | A8 sınıfı hâlâ **kara listeye** bağlıydı | §5'e **kapalı hüküm cümlesi kümesi** |
| Y10 | eşik **birim** kaydırması `≥ 3 s` → `≥ 3000 ms` | GOSTERICI_KURULUM §5 | G8'in `(?:≥|>=)\s*(\d+)\s*s` kalıbı "ms" biçimini hiç görmüyordu; §5'teki diğer `≥ 3 s` ayakta kaldığı için `set(degerler)=={3.0}` tutuyordu | aynı kapalı küme: değişen cümle kümeden **düşer** |
| Y11 | anahtar sözcüksüz README çelişkisi ("Zincir yerinde; kapılar sorun çıkarmadı.") | config/pixhawk/README.md §6.6 | kapalı küme vardı ama **SEÇİCİSİ dardı** (`"prova"`/`"olcut"`) | seçici ön kayıtlı `HUKUM_SOZCUKLERI` + alan sözcüklerine genişletildi |

Y11'i amele `açık_kalan`da bildirmişti; çürütücü de "gizlenmiş kusur değil" dedi — yine de
**kapatıldı**, çünkü kapalı kümenin gücü seçicisine bağlıdır ve bu ders ölçülmüştür.

### D-461 (mimar eki) — ÖN KAYIT TEKLİĞİ

T236-B çürütücüsü ölçtü: `ON_KAYIT §4`'e **ikinci ve gevşetilmiş** bir kabul ölçütü
("T236 SITL kapısı (gözden geçirilmiş): ≤ 4,0 m · ±15° · ≥ %70 · ±3,0 m") eklenince
**hiçbir test düşmüyordu** — bugünkü kilitler yalnız **özgün satırın varlığını** koruyordu,
ölçütün **tekliğini** değil. `belge_kilidi.kabul_olcutu_tekligi(metin, kapi_adi, on_kayitli_olcut)`
dört kuralı birden koşar:

| kural | ne | hangi ölçülen kaçış |
|---|---|---|
| (a) | kapı adı normalleştirilmiş metinde **tam 1 kez** | T236-B: ikinci "T236 SITL kapısı (gözden geçirilmiş)" satırı |
| (b) | ön kayıtlı ölçütün kısıtladığı her büyüklükte **rakip eşik yok** (aynı birimde farklı sayı) | T236-B: `≤ 4,0 m`, `±15°`, `≥ %70`, `±3,0 m` |
| (c) | kabul bloğu **ön kayıtlı metin eşitliği** ile bağlı (alt dizge `in` değil) | ATOLYE-2 A7: ölçütün içine "∧ YKS video paneli BAYAT değil" eklenmesi |
| (d) | kabul yüzeyinde **çelişkili ikinci hüküm sözcüğü yok** (ön kayıtlı liste) | ATOLYE-2 A10 "kabul yalnız p50 ile verilir"; T229-D2 §7.5 parantez içine konan "… geçersiz" |

Kural (b) **yalnız** ön kayıtlı ölçütün kısıtladığı büyüklüklere bakar: bölümdeki
karşılaştırmasız sayılar (örneğin "`FENCE` 50 m altında") eşik değil, ölçüm bağlamıdır —
negatif vaka olarak testte durur.

**Ölçülen sınır (iddia edilmiyor):** T229-D2 çapasında (b) **tetiklenmez**, çünkü ön kayıtlı
ölçütün eşikleri birimsizdir (birimi sabit adı taşır: `..._ZAMAN_ASIMI_S ≤ 0,05`), mutant ise
"≤ 0,20 s" yazar. Orada mutantı (c) ve (d) yakalar. Bu, testte **açıkça** `assertNotIn` ile
kayıtlıdır — ÖLÇÜLEMEDİ ≠ GEÇTİ.

Bu kilit bu işte **yalnız** t235 `ON_KAYIT §4`'e uygulandı (mimar direktifi); beş işe
yayılması **T242**'dir.

---

## 3. Kaçan 28 mutantın hepsi yeniden kuruldu ve DÜŞTÜ

Koşucu: `results/fdr_sprint_20260910/T240/mutasyon_t240.py`.
Her mutasyon **tek tek gerçek dosyaya** yazıldı, **ilgili süit gerçekten koşuldu**,
sonra dosya **sha256 ile bayt-eş** geri yüklendi.

```
## 0. Mutasyonsuz TABAN
  test_faz_b_arduplane_sablon.py         cikis=0  OK
  test_isaretli_gosterici.py             cikis=0  OK (skipped=1)
  test_t235_alan_etiketi.py              cikis=0  OK
  test_yks_mk15_hakem_ekrani.py          cikis=0  OK
  TABAN: YESIL

## 2. OZET
  KACAN mutantlar   : 28/28 DUSTU
  KONTROL mutantlar : 4/4 DUSTU
  geri yukleme      : hepsi bayt-es
  HUKUM             : GECTI
```

| # | mutant | dosya | kilidi düşüren |
|---|---|---|---|
| 1 | D1b `<del>` | CONTRACTS §6.8 | `cizikleri_ayikla` + `beyaz_liste_disi_cizik` |
| 2 | D1c tek tilde `~…~` | CONTRACTS §6.8 | aynı |
| 3 | D1d `<s>` | CONTRACTS §6.8 | aynı |
| 4 | D1e çelişkili ikinci hüküm (kaynak hükmünün **ALTINA**, kalın başlıkla) | CONTRACTS §6.8 | kalın başlıklı paragraf demeti **ve** kapalı cümle kümesi |
| 5 | A3 tek tilde | GOSTERICI_KURULUM §5 | `cizikleri_ayikla` + beyaz liste |
| 6 | A4 `<del>` | GOSTERICI_KURULUM §9 | aynı |
| 7 | A5 `<s>` | GOSTERICI_KURULUM üst hüküm | aynı |
| 8 | A6 "**bir** ardışık" | GOSTERICI_KURULUM §5 | `normalize` sayı sözcüğü → rakam |
| 9 | A7 "**en az 1 saniye**" | GOSTERICI_KURULUM §5 | `normalize` birim + karşılaştırma eş anlamlısı |
| 10 | A8 "**teyit edildi** / **başarılı**" | GOSTERICI_KURULUM §5 | `olumlu_hukum_var` (genişletilmiş aile) |
| 11 | A9 "**6 saniyeyi aşan**" | GOSTERICI_KURULUM §5 | `normalize` sonek→önek karşılaştırma |
| 12 | W1 başlıkta `~ÖLÇÜLEMEDİ~` | README §6.6 | `on_kayitli_metin_esit` (başlık) + beyaz liste |
| 13 | W6 `~ÖLÇÜLEMEDİ~ · prova KANITLANDI` | README §6.6 | aynı |
| 14 | W2 "KANITLANDI" | README §6.6 | `olumlu_hukum_var` + cümle kümesi |
| 15 | W3 `_doğrulandı_` | README §6.6 | `normalize` vurgu sökme (`_` artık harf değil) |
| 16 | W4 `__koşuldu__` | README §6.6 | aynı |
| 17 | W7 "sorunsuz tamamlandı; … sağlanmış" | README §6.6 | `olumlu_hukum_var` + cümle kümesi |
| 18 | V1 numarasız çelişkili hüküm | README §6.6 | kapalı hüküm cümlesi kümesi (tek yakalayan) |
| 19 | V3 ikinci `**Sonuç …**` cümlesi | README §6.6 | ön kayıtlı Sonuç + cümle kümesi |
| 20 | **Y4** `&#822;` harf harf | CONTRACTS §6.8 | **varlık çözümlemesi** + beyaz liste |
| 21 | **Y4b** `&#x336;` onaltılık | CONTRACTS §6.8 | aynı |
| 22 | **Y7a** başlıksız çelişkili paragraf — kaynak hükmünün **ÖNÜNE** | CONTRACTS §6.8 | **kapalı hüküm cümlesi kümesi** (tek yakalayan) |
| 23 | **Y7b** aynı paragraf — "Bağlayıcı ilkeler"in önüne | CONTRACTS §6.8 | aynı |
| 24 | **Y7c** aynı paragraf — son paragrafın önüne | CONTRACTS §6.8 | aynı |
| 25 | **Y5** aile dışı eş anlamlı | GOSTERICI_KURULUM §5 | **kapalı hüküm cümlesi kümesi** |
| 26 | **Y10** eşik birimi `3 s` → `3000 ms` | GOSTERICI_KURULUM §5 | aynı |
| 27 | **Y11** anahtar sözcüksüz çelişki | README §6.6 | kümenin **genişletilmiş seçicisi** |
| 28 | **D461** ikinci gevşetilmiş kabul ölçütü | `…/H1/t235/ON_KAYIT.md` §4 | **`kabul_olcutu_tekligi`** (a+b+c+d birden) |

**Kontrol mutantları** (denetimde zaten düşenler; koşucunun kendisi sağlam mı):
D1 çift tilde, D1f tipografik tırnak, W5 düz DOĞRULANDI, W8 düz GEÇTİ → **4/4 DÜŞTÜ**.

### Hangi kilit düşürdü — hata metniyle ÖLÇÜLDÜ (iddia değil)

"Kapalı cümle kümesi tek yakalayandır" gibi hükümler ancak **hata metniyle** doğrulanabilir.
`hangi_kilit_dusurdu.py` her yeni mutantı uygular, **tek test metodunu** koşar, `AssertionError`
metnini kaydeder ve dosyayı sha256 ile bayt-eş geri yükler. Ham çıktı: `hangi_kilit_dusurdu.txt`
(çıkış 0, "HEPSİ DÜŞTÜ, geri yükleme bayt-eş").

| mutant | düşüren assert (ölçülen hata metni) |
|---|---|
| Y4 / Y4b | `assertEqual([], beyaz_liste_disi_cizik(...))` → `['satir 48: beyaz liste disi cizik (birlesen uzeri cizgi) …']` |
| Y7a / Y7b / Y7c | `assertEqual(beklenen, cumleler)` → `Tuples differ: … != … 'not (12 eylul): kaynak alani artik zorunl…'` — **kalın başlık demeti ve komşuluk assert'leri ondan ÖNCE koşar ve GEÇER**, yani yakalayan tek yapı kapalı kümedir |
| Y5 / Y10 | §5 kapalı kümesi → `Tuples differ: … '- saha kurali (12 eylul): -v nabiz satiri b…'` / `… '≥ 3000 ms aralikla yeniden acilir.'` |
| Y11 | `SS6.6 on kayitli hukum cumlesi kumesi degisti` (m12/m21 meta-testleri) |
| D461 | `kabul olcutu tekligi: 'T236 SITL kapısı' … 2 kez` + rakip eşik + blok eşitsizliği + "gozden gecirilmis" |

### Beyan düzeltmesi (D-460 bulgu 3 sınıfı — "ölçülenden fazlasını söyleme")

Önceki KANIT.md, D1e satırında çözümü "kalın başlıklı hüküm paragrafı demeti (yapısal)"
diye yazıyordu. **Bu hüküm ölçülenden genişti:** demet yalnız **kalın başlık taşıyan**
paragrafları sayar; başlıksız bir çelişkili paragraf (Y7) ondan da, ön kayıtlı kaynak
hükmünden de, komşuluk kilidinden de kaçıyordu (ölçüldü: MK15 **ve** 233 testlik
`test_yks_*.py` çıkış 0). Doğru ifade tabloda: **D1e'nin ölçülen varyantı** kalın başlıklı
ve kaynak hükmünün altındaydı; **başlıksız varyantı (Y7) kapalı cümle kümesiyle** kapandı ve
§6.8'in **üç ayrı yerinde** ayrı ayrı ölçüldü.

Aynı sınıfta yardımcının kendi docstring'i de düzeltildi: "gelecekte çıkacak yeni sözdizimi
buraya kalıp eklenmeden yakalanır" cümlesi **ölçülen kapsama** çekildi — "düz metin **ve HTML
varlık biçimindeki** çizme işaretleri, tilde koşuları, tilde benzerleri ve
`ZARARSIZ_ETIKETLER` dışındaki her etiket"; kapsam dışında kalan bir biçim için **iddia
yoktur**.

---

## 4. Kapı (hepsi gerçekten koşuldu)

Yorumlayıcı `O:\navitas-local-train\venv\Scripts\python.exe -X utf8 -B`,
kök `O:\navitas\.claude\worktrees\wf_fabd3bac-230-1`. Ham çıktı: `kapi_ciktisi.txt`
(başında koşum anındaki `HEAD` damgalı: **`94f54347`**).

| adım | sonuç |
|---|---|
| `test_belge_kilidi.py` | Ran **60** tests · **OK** · çıkış 0 |
| `test_yks_mk15_hakem_ekrani.py` **üç ardışık** | 39/39 OK (25,5 s · 25,5 s · 25,5 s) · çıkış 0,0,0 |
| `test_isaretli_gosterici.py` | Ran 62 tests · **OK** (skipped=1) · çıkış 0 |
| `test_faz_b_arduplane_sablon.py` | Ran 44 tests · **OK** · çıkış 0 |
| `test_t235_alan_etiketi.py` | Ran **56** tests · **OK** · çıkış 0 |
| `test_yks_*.py` | Ran 233 tests · **OK** · çıkış 0 |
| **GENEL KAPI** `codes/test_rota_sentetik.py` | `GENEL KAPI (madde 14): GECTI — kol1 15/15 · kol2 serit 15/15` · çıkış 0 |
| `scripts/belge_kilidi_denetle.py` | çıkış 0 · rapor yazıldı |

### Taşınan koşul (gizlenmiyor)

Üç süit `data/arena_kompozit/` verisine bağlı; bu dizin **git'te izlenmiyor** (`.gitignore`)
ve taze bir checkout'ta kapı yeniden üretilemez. Bu worktree'de veri yerinde olduğu için kapı
yeşil. **Birleştirmeden sonra ana ağaçta yeniden koşulmalıdır.** Silinmişse:
`shutil.copytree(r"O:\navitas\data\arena_kompozit\images", <worktree>/data/arena_kompozit/images)`.

---

## 5. Kilit gevşemedi — önce/sonra sayılabilir

`self.assert|hatalar.append` sayısı **master → HEAD**:

| dosya | master | HEAD |
|---|---|---|
| `tests/test_yks_mk15_hakem_ekrani.py` | 214 | **220** |
| `tests/test_isaretli_gosterici.py` | 369 | **371** |
| `tests/test_faz_b_arduplane_sablon.py` | 218 | **224** |
| `tests/test_t235_alan_etiketi.py` | 246 | **248** |
| `tests/test_belge_kilidi.py` | 0 (yoktu) | **110** |

Eklenen satırlarda `skip` / `expectedFailure` / `maxDiff` / `sleep(` **araması: 0 sonuç**.
Kapsam daralması yok; kapalı kümeler **büyüdü**: §6.6 **5 → 18** cümle; §6.8 **yok → 37**;
§5 **yok → 23**. Hiçbir ön kayıtlı sabit gevşetilmedi, hiçbir kilit satırı silinmedi.

---

## 6. Depo denetimi — hangi kilitler hâlâ açık

`acik_kilitler.md` (üretici `scripts/belge_kilidi_denetle.py`, salt okuma, AST, **kapı değil**):

| ölçüm | değer |
|---|---|
| taranan test dosyası | 206 |
| markdown okuyup dizge arayan | 58 |
| ortak yardımcıdan **geçen** | **5** |
| **AÇIK** (yardımcıyı kullanmayan) | **53** |
| AÇIK **ve** kaynağında çizme sözdizimi sabiti olan (ağır) | **4** |

Ağır dördü: `test_fdr_bolum4_6eylul_kaniti.py`, `test_fdr_sarkan_atif_kapisi.py`,
`test_gece_ika_baglanti_semasi.py`, `test_t220_jetson_istekleri.py`.
Bu dört dosya **ölçülmedi**, yalnız listelendi: **ÖLÇÜLEMEDİ ≠ GEÇTİ**.

---

## 7. Sınırlar ve açık kalanlar

- **ÖLÇÜLMEDİ:** yukarıdaki 53 açık kilidin hiçbiri mutasyonla sınanmadı. Sayı,
  "hangi kilitler delinebilir" sorusunun **üst sınırıdır**, kusur sayısı değildir.
- **ÖLÇÜLMEDİ:** `kabul_olcutu_tekligi` beş işe (T242) uygulanmadı; bu işte **tek** gerçek
  kullanımı t235 `ON_KAYIT §4`'tür. ATOLYE-2 A10/A7 ve T229-D2 §7.5 mutantları yalnız
  **birim düzeyinde** (gerçek belge metni kopyalanarak) düşürüldü, o belgelere kilit
  BAĞLANMADI.
- **Kapalı kümenin gücü seçicisine bağlıdır** (Y11 dersi). Seçici listeleri
  (`HUKUM_SOZCUKLERI` + bölüme özgü alan sözcükleri) ön kayıtlıdır ve gerekçeleri
  yardımcının docstring'inde yazılıdır; genişletilebilir, **daraltılamaz**.
- `normalize` **belgelenmiş tek yön** seçer: sözcük → sembol (`saniye`→`s`,
  `milisaniye`→`ms`, `derece`→`°`). Birim kuralı **sayıya bağlıdır**. `ms ↔ s`
  **büyüklük** katlaması YOKTUR; Y10 sınıfını kapatan şey normalize değil, **kapalı
  cümle kümesidir** (değişen cümle kümeden düşer).
- Varlık çözümlemesi `<` ve `>` üreten varlıkları **bilerek çözmez**: `&lt;s&gt;` markdown'da
  etiket açmaz, harfi harfine görünür; çözseydik kaçınılan bir etiket örneği hayalet çizik
  olurdu. Negatif vaka testte durur.
- `cizikleri_ayikla` tek tildede **belgelenmiş bir istisna** taşır: `~<rakam>`
  ("~3 s", "~8 Hz") yaklaşık işaretidir.
- **Bağımsızlık (madde 19):** bu işi yazan ajan kendi işini KABUL ETMEZ; kapatma onayı
  ayrı bir denetimdedir.
