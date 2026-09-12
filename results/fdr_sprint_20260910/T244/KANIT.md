# T244-B — kabul ölçütü kilidi: ÖLÇÜLEN KAPSAMA ve SAYILAN SINIR

**Tarih:** 12 Eylül 2026 · **Dal:** `worktree-wf_88f63745-bff-2` · **Karar:** D-466
**Dosya:** `tests/test_fdr_t244_ic_celiski.py` · `results/fdr_sprint_20260910/T244/mutasyon_t244.py`

> Bu belgede yazan her cümle koşulmuş bir ölçüme bağlıdır. **ÖLÇÜLEMEDİ ≠ GEÇTİ**
> ve **ölçülenden fazlasını söyleyen beyan yoktur**: kapanmayan sınıf aşağıda
> sayılarak yazılıdır (D-465 (4)).

---

## 1. Neden yeniden yazıldı (ölçülen kusur, D-466)

T244'ün ilk teslimatındaki kilit **kapanmamış bir deliği KAPANDI ilan ediyordu**.
Çürütücü ölçtü: kilitli kesitlerin **dışına** konan çelişkili ikinci kabul
hükümlerinin **6/6'sı kaçtı** (çıkış 0, `OK`). Mekanizma yalnız
`CELISKI_SOZCUKLERI` listesindeki 8 büyük harfli ifadenin birebir geçmesiyle
düşüyordu: aynı yere konan `Gözden geçirilmiş kapı: engine kabul edilir.`
**YAKALANDI**, eş anlamlısı `Revize edilmiş kabul kapısı: engine kabul edilir.`
**KAÇTI**. Kapsama **sözlük düzeyindeydi, yapısal değil**.

Eski beyan (ilk teslimat) ~~"D-463'ün T240'a verdiği iki delik bu kilitte de
ölçüldü ve KAPATILDI"~~ → **12 Eylül 2026 düzeltmesi (D-466):** HTML varlık
biçimli çizik (D-463 (a)) **ÖLÇÜLDÜ ve KAPANDI**; çelişkili ikinci hüküm
(D-463 (b)) **DARALTILDI, KAPANMADI** — kapanmayan sınıf §4'te sayılıdır.

## 2. Yeni kilit: sözlük değil BİÇİM

Tarama iki bölümün (`FDR/BOLUM_3_SISTEM_SPESIFIKASYONLARI.md`,
`FDR/BOLUM_4_TEST_FAALIYETLERI.md`) **TAMAMINI** gezer; kilitli kesit kavramına
bağlı değildir. İki yapısal kural:

| kural | tuttuğu biçim |
|---|---|
| **K1** — sayı taşıyan kabul ölçütü | aynı birimde (a) karşılaştırma işareti (`≤ ≥ < >`) **ya da** "eşik / kapı / ölçüt / kabul" sözcüğü, (b) `n/m` ya da `%x` (`%x,y`) sayısı, (c) hüküm sözcüğü (GEÇTİ · KABUL · SAYILIR · YETERLİ · olumlu hüküm) |
| **K2** — kip (edim) biçimi | aynı birimde (i) hüküm nesnesi (KABUL · EŞİK · KAPI · ÖLÇÜT · GEÇTİ · DÜŞTÜ · ÖLÇÜLEMEDİ · KURAL · HÜKÜM) ve (ii) kip eki (`-ABİLİR` / `-MALIDIR` / SAYILIR / EDİLİR / ALINIR) |

K1 ya da K2 tutan her birim `ON_KAYITLI_KABUL_BIRIMLERI` içinde **tam dizgi**
olarak yoksa kapı düşer (D-465 (1) "ön kayıtlı metin eşitliği"). Ön kayıt bugün
**73 birim** taşır. Yeni bir kabul hükmü **nereye konursa konsun** — kilitli
kesitin içine de dışına da — ön kayda eklenmeden geçemez.

**Yapı yorumlanmaz, silinir (D-465 (3)).** Çizme işaretleri (`~~`, tek tilde,
`<del>/<s>/<strike>`), birleştirici çizik (U+0335…U+0338), vurgu/kod imleri ve
HTML varlıkları burada **ayıklanmaz**; yalnız işaret olarak silinir, **içerik
kalır ve taranır**. Çizili bir kabul hükmü de ön kayda girmek zorundadır —
böylece "çizik/varlık içine saklama" yüzeyi açılmaz. Paragrafın satırları
birleştirilir, yani hükmü iki satıra bölerek kaçmak da mümkün değildir
(`Revize edilmiş kabul\nkapısı: …` ölçüldü, **düştü**).

## 3. ÖLÇÜLEN — mutasyonla gösterildi

| ölçüm | sonuç | kanıt |
|---|---|---|
| Çürütücünün kaçan 6 cümlesi + eski sözlüğün 2 örneği, iki bölümün tamamında **3 konuma** (baş · orta · son) konarak | **48/48 DÜŞTÜ** (0 kaçan) | `test_T9c_KACAN_cumleler_HER_KONUMDA_duser` |
| Aynı 6 cümlenin **gerçek dosya** mutasyonu (kilitli kesit DIŞI: Bölüm 3 §3.4 başlığından önce, Bölüm 4 kapanış paragrafından önce) | **6/6 YAKALANDI** | `mutasyon_t244.py` MY1–MY6 · `mutasyon_ciktisi.txt` |
| Toplam gerçek dosya mutasyon bataryası | **19/19 YAKALANDI**, uygulanamayan 0, geri yükleme sha eşit | `mutasyon_ciktisi.txt` son satırlar |
| **Yanlış pozitif** — mutasyonsuz iki gerçek bölüm | **0 ihlal** (kilit YEŞİL) | `test_T9a_gercek_iki_bolum_MUTASYONSUZ_YESIL` |
| **Yanlış pozitif** — 5 meşru düzenleme: yazım düzeltmesi · satır yeniden sarma · yeni ÖLÇÜM satırı (kabul ölçütü değil) · yeni D atfı cümlesi · tablo satırı yer değiştirme | **0 yeni ihlal** | `test_T9d_MESRU_duzenleme_YANLIS_POZITIF_uretmez` |
| Ön kayıtta ölü girdi (belgede karşılığı olmayan dizgi) | **0** | `test_T9b_on_kayit_OLU_girdi_tasimaz` |

## 4. SINIR — KAPANMAYAN SINIF (sayılarak yazıldı, kovalanmaz)

Ölçüldü (`test_T9e_SINIR_kapanmayan_sinif_SAYILARAK_yazildi`): altı kaçış sınıfı
sınandı, **altısı da kaçıyor** (her biri 2 bölüm × 3 konum = 6/6 kaçış).

| # | kaçan sınıf | örnek |
|---|---|---|
| S1 | sayısız + kipsiz + kabul sözcüksüz olumlu hüküm | `Engine kolu artık yeşildir.` |
| S2 | aynı sınıf, "tamam" kipi | `Bu kalem tamamdır.` |
| S3 | olumsuzlamayla yazılmış olumlu hüküm | `RC failsafe için bugün bir sorun görülmemiştir.` |
| S4 | ölçütü **iki tablo satırına** bölme (birim sınırı satırdır) | `\| yeni ölçüt \| ≥ 6/15 \|` + `\| sonuç \| GEÇTİ \|` |
| S5 | eşiği yeni bir **birim sözcüğüyle** yazma | `Engine için yeni sınır üç birimdir ve karşılanmıştır.` |
| S6 | sayıyı **yazıyla** yazma | `Engine için ikinci eşik yüzde üçtür ve sağlanmıştır.` |

Ek olarak **kapatılamayan yapısal sınır:** ön kayıt listesinin kendisi depoda
durur; yazma yetkisi olan biri yeni bir kabul hükmünü listeye **ekleyerek**
geçirebilir. Bu kilit bunu engellemez, yalnız **görünür** kılar (fark `git
diff`'te ön kayıt satırı olarak çıkar ve `test_T9b`'deki sayı ön kaydı düşer).

**Tehdit modeli (D-465 (4)):** bu kilit, belgeyi iyi niyetle düzenleyen bir
ajanın ya da insanın ölçülmüş bir hükmü farkında olmadan aşındırmasını durdurur.
El yapımı bir düşmanı durdurmaz ve durdurması beklenmez. Yukarıdaki altı sınıf
**kovalanmaz**; sayılarak yazılır. `test_T9e` bu sayıyı **ölçüme bağlar**: kilit
güçlenir ya da zayıflarsa test düşer ve bu belge güncellenmek zorunda kalır.

## 5. Yanında düzeltilen iki küçük kusur (çürütücü ölçümü)

1. **`[YOK]` sayısı fazla beyan ediliyordu.** Rapor dört yerde "tek `[YOK]`"
   diyordu; `jetson_baslat_kuru.log:44` **`[YOK]: 2`** (ayrıca `mavproxy.py`
   PATH'te yok), yalnız `jetson_baslat_kuru2.log:44` **`[YOK]: 1`**. Dört yerde
   de eski metin çizildi ve düzeltme yazıldı; yeni nöbetçi sayıyı **log'dan**
   okuyup rapora bağlıyor (`test_T10_log_YOK_sayilari_ve_rapor_HIZALI`).
   Ana hüküm değişmedi: Pixhawk bağlı değil → çıkış 3 → MAVLink kapısı ÖLÇÜLEMEDİ.
2. **Çizgisiz düzenlenen tek yer** (`BOLUM_4` §4.4 Pixhawk satırı) kurala
   uyduruldu: ~~`mavlink_dogrula.py` kapısı **koşulmadı**~~ → **5 Eylül'de
   koşulmadı** (D-462 A4).

## 6. Koşulan kapılar (ham çıktı `kapi_ciktisi.txt`)

`codes/test_rota_sentetik.py` **15/15** · `test_fdr*` · `test_gece*` ·
`test_d373*` · `scripts/fdr_acik_kalem_cikar.py --dogrula` ·
`tests/test_fdr_t244_ic_celiski.py` tek başına **44 test OK** ·
`mutasyon_t244.py` **19/19**.
