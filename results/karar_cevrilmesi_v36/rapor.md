# KARAR ÇEVRİLMESİ — v36 ölçüm borcu kapatıldı

**Tarih:** 2026-08-26 · **Ajan:** `karar_cevrilmesi` (GPU izinli tek ajan)
**Dayanak:** `results/gece_20260826/ON_KAYIT.md` §16 · REVIEW_LOG D-294 §4 · D-256 §3 · D-203
**Kapsam:** ölçüm + kayıt defterinin `OLCULMEDI` alanının doldurulması. **Kod değiştirilmedi.**

> ⚠ **BU BİR KAPI DEĞİLDİR.** ÖN_KAYIT §16 açıkça yazıyor: sayı ne çıkarsa yazılır,
> v36 terfisi bu sayıya göre geri alınmaz. Aşağıdaki sonuç **v35'ten kötüdür** ve
> bu, hem raporda hem defter notunda açıkça yazılmıştır (D-256'nın "iki maliyet" kalıbı).

---

## 1. SONUÇ — tek tabloda

| ölçüm | v36 (üretim) | v35 (yedek) | fark |
|---|---|---|---|
| **tohum 7** (ön kayıtlı) | **14/260 · %5,38** | **9/260 · %3,46** | 🔴 **+5 kare, v36 KÖTÜ** |
| tohum 11 (duyarlılık) | 15/260 · %5,77 | 11/260 · %4,23 | 🔴 +4 kare, v36 KÖTÜ |
| şerit değişimi (t7 / t11) | 8 / 10 | 9 / 10 | ≈ EŞİT |
| **rota VAR/YOK çevrilmesi** (t7 / t11) | **6 / 5** | **0 / 1** | 🔴 farkın TAMAMI burada |
| null kontrol (sigma 0) | 0/260 | — | araç geçerli |
| darboğaz payı medyanı | 17,7 px | 17,9 px | — |
| pay < 3 px olan kare | 17/255 | 16/256 | — |

**Tarihsel bağlam:** v34 4/260 · v35 9/260 (D-256 §3). Bu eksen **v34 terfisinde KAPIYDI**
(eşik ≤ 8/260); bugünkü kabul zincirinde (`65_kabul_denetcisi`) kapı **değildir**.
O eski eşik bugün uygulansaydı **v36 (14) da v35 (9) de DÜŞERDİ** — yani v35 zaten eşiğin
üstündeydi, v36 aradaki mesafeyi büyüttü.

---

## 2. YÖNTEM — v35 ile birebir aynı parametreler

Betik: `scripts/olcum/68_karar_kararliligi.py` (adı ve arayüzü doğrulandı; `--model`,
`--kume`, `--sigma`, `--tekrar`, `--tohum`, `--json`).

- gürültü: Gauss **sigma = 2/255** (%0,8) · kare başına **3 tekrar** · **tohum 7**
- küme: profilin `kabul_kumesi` alanı → `O:/navitas-local-train/calisma/sentetik_arena_kadraj_t66`, **n = 260**
- CONF 0,30 · `INFER_SIZE` (imgsz 512) · yer gerçeği KULLANILMAZ (sorulan "karar doğru mu" değil, "karar AYNI MI")
- **model kayıt defterinden çözüldü**: v36 için argümansız koşuldu (`ayarlar.uretim_pt()` →
  `config/model_registry.json` → `profiles.competition.path`). Çıplak sürüm adı yazılmadı.
- v35 yolu da defterden okundu (`profiles.competition._yedek_surumler.v35.path`) ve CLI argümanı olarak verildi.
- **Eşli koşum (D-256 §3 kalıbı):** iki model **aynı oturumda, sıralı, tek süreçte**, aynı küme ve
  aynı tohumla ölçüldü — gürültü gerçekleştirmeleri iki model için özdeştir.

### Ölçümün geçerliliği — iki bağımsız kontrol

1. **Null kontrol (sigma 0):** v36 → **0/260**. Yani rapor edilen 14 kare, çıkarımın
   kendi belirsizliğinden veya betiğin gürültüsünden DEĞİL, **bindirilen gürültüden** gelir.
2. **Yeniden üretim:** v35 tohum 7'de **9/260** çıktı — `results/t130_kararlilik_tohum7.json`
   (2026-08-21, D-256) ile **birebir aynı**. Fark modeldendir, koşum ortamından değil.

---

## 3. KOMUTLAR ve HAM ÇIKTI

Yorumlayıcı her koşumda `O:\navitas-local-train\venv\Scripts\python.exe`, çalışma dizini `O:\navitas\scripts\olcum`.

### 3.1 v36 · tohum 7 (ÖN KAYITLI ÖLÇÜM)

```
<venv> 68_karar_kararliligi.py --tohum 7 --json O:/navitas/results/karar_cevrilmesi_v36/v36_tohum7.json
```

```
====================================================================
KARAR KARARLILIGI · navitas_seg_v36_best.pt
  gurultu: Gauss sigma=2.0/255 (%0.8) · kare basina 3 tekrar
====================================================================
  olculen kare        : 260
  KARARI CEVRILEN     : 14/260  (%5.38)
  darbogaz PAYI (darbogaz - r_gerekli), tum kareler:
    medyan 17.7 px · en dusuk 0.1 px · pay < 3 px olan kare: 17/255
====================================================================
    sa_000013.jpg  pay=13.919999999999998  ->  1/None | None/ZEMIN_MASKESI_SUPHELI | None/ZEMIN_MASKESI_SUPHELI | None/ZEMIN_MASKESI_SUPHELI
    sa_000031.jpg  pay=2.904497070312498  ->  1/None | 2/None | 2/None | 1/None
    sa_000041.jpg  pay=None  ->  None/GORUS_HATTI_KOPUK | 2/None | None/GORUS_HATTI_KOPUK | 2/None
    sa_000061.jpg  pay=2.510698242187498  ->  3/None | None/GORUS_HATTI_KOPUK | None/GORUS_HATTI_KOPUK | None/GORUS_HATTI_KOPUK
    sa_000078.jpg  pay=6.919999999999998  ->  2/None | 2/None | None/GORUS_HATTI_KOPUK | 2/None
    sa_000081.jpg  pay=0.904498977661131  ->  3/None | None/GORUS_HATTI_KOPUK | None/GORUS_HATTI_KOPUK | None/GORUS_HATTI_KOPUK
    sa_000098.jpg  pay=13.919999999999998  ->  1/None | 2/None | 2/None | 2/None
    sa_000100.jpg  pay=9.510698242187498  ->  3/None | 2/None | 3/None | 3/None
    sa_000129.jpg  pay=13.682794494628904  ->  2/None | 2/None | 1/None | 1/None
    sa_000133.jpg  pay=28.313798828124998  ->  2/None | 3/None | 3/None | 3/None
    sa_000148.jpg  pay=1.298297805786131  ->  2/None | 2/None | 3/None | 3/None
    sa_000174.jpg  pay=None  ->  None/UC_BANT_TEMAS_YOK | 2/None | 2/None | None/GORUS_HATTI_KOPUK

json -> O:\navitas\results\karar_cevrilmesi_v36\v36_tohum7.json
```

⚠ Betik listeyi **ilk 12 kare** ile kırpar (`cevrilenler[:12]`); 14 karenin tamamı JSON'dadır
(`sa_000198.jpg`, `sa_000215.jpg` ekranda görünmez).

### 3.2 v35 · tohum 7 (EŞLİ, aynı oturum)

```
<venv> 68_karar_kararliligi.py --model O:/navitas/models/navitas_seg_v35_best.pt --tohum 7 \
       --json O:/navitas/results/karar_cevrilmesi_v36/v35_tohum7_esli.json
```

```
====================================================================
KARAR KARARLILIGI · navitas_seg_v35_best.pt
  gurultu: Gauss sigma=2.0/255 (%0.8) · kare basina 3 tekrar
====================================================================
  olculen kare        : 260
  KARARI CEVRILEN     : 9/260  (%3.46)
  darbogaz PAYI (darbogaz - r_gerekli), tum kareler:
    medyan 17.9 px · en dusuk 0.1 px · pay < 3 px olan kare: 16/256
====================================================================
    sa_000031.jpg  pay=2.313798828124998  ->  1/None | 2/None | 1/None | 1/None
    sa_000076.jpg  pay=25.12000076293945  ->  3/None | 2/None | 2/None | 2/None
    sa_000129.jpg  pay=23.510698242187498  ->  1/None | 1/None | 1/None | 2/None
    sa_000148.jpg  pay=1.298297805786131  ->  2/None | 2/None | 2/None | 3/None
    sa_000164.jpg  pay=4.904497070312498  ->  2/None | 2/None | 1/None | 2/None
    sa_000171.jpg  pay=47.70759765625  ->  1/None | 2/None | 2/None | 2/None
    sa_000172.jpg  pay=10.919999999999998  ->  2/None | 2/None | 3/None | 3/None
    sa_000174.jpg  pay=None  ->  None/UC_BANT_TEMAS_YOK | None/UC_BANT_TEMAS_YOK | None/GORUS_HATTI_KOPUK | None/GORUS_HATTI_KOPUK
    sa_000176.jpg  pay=73.92  ->  3/None | 3/None | 1/None | 3/None

json -> O:\navitas\results\karar_cevrilmesi_v36\v35_tohum7_esli.json
```

### 3.3 v36 · tohum 11 (D-203 duyarlılık)

```
<venv> 68_karar_kararliligi.py --tohum 11 --json O:/navitas/results/karar_cevrilmesi_v36/v36_tohum11.json
```

```
====================================================================
KARAR KARARLILIGI · navitas_seg_v36_best.pt
  gurultu: Gauss sigma=2.0/255 (%0.8) · kare basina 3 tekrar
====================================================================
  olculen kare        : 260
  KARARI CEVRILEN     : 15/260  (%5.77)
  darbogaz PAYI (darbogaz - r_gerekli), tum kareler:
    medyan 17.7 px · en dusuk 0.1 px · pay < 3 px olan kare: 17/255
====================================================================
    sa_000013.jpg  pay=13.919999999999998  ->  1/None | None/ZEMIN_MASKESI_SUPHELI | None/ZEMIN_MASKESI_SUPHELI | None/ZEMIN_MASKESI_SUPHELI
    sa_000031.jpg  pay=2.904497070312498  ->  1/None | 1/None | 1/None | 2/None
    sa_000041.jpg  pay=None  ->  None/GORUS_HATTI_KOPUK | None/GORUS_HATTI_KOPUK | 2/None | 2/None
    sa_000061.jpg  pay=2.510698242187498  ->  3/None | None/GORUS_HATTI_KOPUK | 3/None | None/GORUS_HATTI_KOPUK
    sa_000081.jpg  pay=0.904498977661131  ->  3/None | 3/None | None/GORUS_HATTI_KOPUK | None/GORUS_HATTI_KOPUK
    sa_000098.jpg  pay=13.919999999999998  ->  1/None | 1/None | 2/None | 2/None
    sa_000100.jpg  pay=9.510698242187498  ->  3/None | 3/None | 2/None | 3/None
    sa_000129.jpg  pay=13.682794494628904  ->  2/None | 1/None | 1/None | 1/None
    sa_000131.jpg  pay=16.919999999999998  ->  2/None | 2/None | 2/None | 1/None
    sa_000133.jpg  pay=28.313798828124998  ->  2/None | 3/None | 3/None | 3/None
    sa_000148.jpg  pay=1.298297805786131  ->  2/None | 2/None | 3/None | 3/None
    sa_000171.jpg  pay=49.9044970703125  ->  2/None | 2/None | 1/None | 2/None

json -> O:\navitas\results\karar_cevrilmesi_v36\v36_tohum11.json
```

Kırpılan 3 kare (JSON'da): `sa_000174.jpg`, `sa_000198.jpg`, `sa_000215.jpg`.

### 3.4 v35 · tohum 11 (EŞLİ)

```
<venv> 68_karar_kararliligi.py --model O:/navitas/models/navitas_seg_v35_best.pt --tohum 11 \
       --json O:/navitas/results/karar_cevrilmesi_v36/v35_tohum11_esli.json
```

```
====================================================================
KARAR KARARLILIGI · navitas_seg_v35_best.pt
  gurultu: Gauss sigma=2.0/255 (%0.8) · kare basina 3 tekrar
====================================================================
  olculen kare        : 260
  KARARI CEVRILEN     : 11/260  (%4.23)
  darbogaz PAYI (darbogaz - r_gerekli), tum kareler:
    medyan 17.9 px · en dusuk 0.1 px · pay < 3 px olan kare: 16/256
====================================================================
    sa_000004.jpg  pay=11.919999999999998  ->  2/None | 2/None | 1/None | 1/None
    sa_000062.jpg  pay=None  ->  None/GORUS_HATTI_KOPUK | 3/None | 3/None | None/GORUS_HATTI_KOPUK
    sa_000076.jpg  pay=25.12000076293945  ->  3/None | 2/None | 3/None | 2/None
    sa_000129.jpg  pay=23.510698242187498  ->  1/None | 2/None | 2/None | 2/None
    sa_000148.jpg  pay=1.298297805786131  ->  2/None | 2/None | 3/None | 2/None
    sa_000171.jpg  pay=47.70759765625  ->  1/None | 2/None | 2/None | 2/None
    sa_000172.jpg  pay=10.919999999999998  ->  2/None | 2/None | 3/None | 3/None
    sa_000174.jpg  pay=None  ->  None/UC_BANT_TEMAS_YOK | None/GORUS_HATTI_KOPUK | None/GORUS_HATTI_KOPUK | None/GORUS_HATTI_KOPUK
    sa_000176.jpg  pay=73.92  ->  3/None | 3/None | 3/None | 1/None
    sa_000215.jpg  pay=4.919999999999998  ->  1/None | 1/None | 2/None | 1/None
    sa_000258.jpg  pay=9.510700149536131  ->  2/None | 3/None | 2/None | 2/None

json -> O:\navitas\results\karar_cevrilmesi_v36\v35_tohum11_esli.json
```

### 3.5 NULL KONTROL · v36 · sigma 0

```
<venv> 68_karar_kararliligi.py --sigma 0 --tohum 7 \
       --json O:/navitas/results/karar_cevrilmesi_v36/v36_sigma0_nulkontrol.json
```

```
====================================================================
KARAR KARARLILIGI · navitas_seg_v36_best.pt
  gurultu: Gauss sigma=0.0/255 (%0.0) · kare basina 3 tekrar
====================================================================
  olculen kare        : 260
  KARARI CEVRILEN     : 0/260  (%0.00)
  darbogaz PAYI (darbogaz - r_gerekli), tum kareler:
    medyan 17.7 px · en dusuk 0.1 px · pay < 3 px olan kare: 17/255
====================================================================
```

---

## 4. TOHUM DUYARLILIĞI — D-203 sınandı

D-203 bu ölçütün tohuma duyarlı olduğunu söylüyor. Bu yüzden ikinci bir tohum koşuldu.
**Tohum 11, ilk sonuçlar görülmeden seçildi ve yazıldı** (ön kayıt disiplini).

| | tohum 7 | tohum 11 | oynama |
|---|---|---|---|
| v36 | 14 | 15 | +1 |
| v35 | 9 | 11 | +2 |
| **v36 − v35** | **+5** | **+4** | **YÖN DEĞİŞMEDİ** |

- **Yön sağlamdır**: iki tohumda da v36 kötüdür. **Büyüklük tohuma duyarlıdır** (+5 / +4).
- Kararsız kare kümesinin kendisi de kısmen tohuma bağlıdır: v36 iki tohumun kesişimi 13,
  birleşimi 16; v35'te kesişim 7, birleşim 13. Yani **v36'nın kararsız kareleri daha
  tekrarlanabilir** (13/16) — gürültü hangi gerçekleşme olursa olsun aynı kareler düşüyor;
  v35'inkiler daha rastgele (7/13). Bu, v36'nın kararsızlığının **yapısal** olduğuna işaret eder.
- ⚠ İki tohum, iki örnektir. **Güven aralığı hesaplanmadı, hipotez testi koşulmadı** — n=2
  tohumla anlamlılık iddia edilmez. Yazılan tek şey: iki bağımsız tohumda da işaret aynıdır.

---

## 5. KUSURUN CİNSİ — sayı kadar önemli (yeni bulgu)

Çevrilen kareler, karar türüne göre ayrıldı:

| çevrilme türü | v36 (t7 / t11) | v35 (t7 / t11) |
|---|---|---|
| **şerit değişimi** (rota var, koridor değişti) | 8 / 10 | 9 / 10 |
| **rota VAR/YOK** (gürültü altında rota kayboluyor) | **6 / 5** | **0 / 1** |

**v36'nın fazlalığının tamamı ikinci satırdadır.** Zikzak riski (birinci satır — D-119/D-120'nin
asıl kaygısı) iki sürümde **eşittir**. Yeni olan şey: v36'da %0,8'lik gürültü, 5–6 karede rotayı
**tamamen düşürüyor** — `ZEMIN_MASKESI_SUPHELI` ve `GORUS_HATTI_KOPUK` redleriyle.

Bu, bağımsız olarak ölçülmüş başka bir sayıyla tutarlıdır: v36 gerçek karede daha az zemin
görüyor (kaplama içerik paydasıyla v35 0,5076 → v36 0,4171, defterde yazılı). Model
**red eşiğinin kenarında** duruyor; küçük bir gürültü onu eşiğin öbür tarafına atıyor.

**Yorum (ölçüm değil):** bu yön **fail-closed**'dır — yanlış rota üretilmiyor, rota
üretilmiyor. Anayasa madde 15'in tehlikeli ekseni (serbest alanı büyütmek) **bu değildir**.
Bedeli **saha elverişliliğidir**: İKA'ya verilecek rota, gürültülü karede yok sayılabilir.
Hangi bedelin ağır bastığı bu ölçümle **kararlaştırılamaz**; kullanıcı kararıdır.

Yalnız v36'da kararsız kareler: `013 041 061 078 081 098 100 131 133 198`
Yalnız v35'te kararsız kareler: `004 062 076 164 172 176 258`
Ortak: 6 kare. İki sürüm **farklı kareleri** düşürüyor — D-294'ün "v35 farklı hata yapar"
saptamasıyla aynı yönde.

---

## 6. KAYIT DEFTERİ — `OLCULMEDI` kalktı

`config/model_registry.json` → `profiles.competition.metrics.karar_cevrilmesi`:

- `olculen`: `null` → **`14`** (ön kayıtlı tohum 7; tam sayı — `scripts/olcum/118_t131_kayma_defteri.py`
  bu alanı skaler olarak okur, biçim korundu)
- `sonuc`: `"OLCULMEDI"` → `"OLCUM (KAPI DEGIL) · 🔴 v35'TEN KOTU"`
- `not`: parametreler, tarih, betik adı, eşli v35 kıyası, tohum duyarlılığı, kusurun cinsi,
  eski v34 eşiğiyle ilişkisi ve "terfi geri alınmadı" kaydı yazıldı.
- **Eklenen alanlar (yapı bozulmadı, yalnız eklendi):** `olculen_tohum11: 15`,
  `v35_esli: {tohum7: 9, tohum11: 11}`, `n: 260`.
  Bu alanları okuyan kod **yoktur** (`grep karar_cevrilmesi` → yalnız iki defter dosyası;
  `118` yalnız `olculen`'e erişir, o da skaler kaldı).

Ayna bayt-eş:

```
a9afe090ee441e194a95f41aa62bb54d  config/model_registry.json
a9afe090ee441e194a95f41aa62bb54d  jetson_paket/config/model_registry.json
diff -> bos
```

---

## 7. KAPI

```
<venv> codes/test_rota_sentetik.py
SONUC: 15/15 dogru
[OK] TUM DETERMINISTIK SAHNELER GECTI
```

```
<venv> -m unittest discover -s tests -q
Ran 962 tests in 78.059s
OK (skipped=2)
```

**Mutasyon kanıtı:** bu görevde **yeni test yazılmadı** (kod değiştirilmedi; yalnız ölçüm ve
defter alanı doldurulması). Mutasyon kanıtı yerine ölçüm aracının geçerliliği iki kontrolle
gösterildi: sigma 0 null kontrolü **0/260** (aracın saydığı şey gerçekten bindirilen gürültüdür,
çıkarımın kendi belirsizliği değil) ve v35'in 9/260 değerinin **birebir yeniden üretimi**
(aracın modeller arasında ayrım yapması ölçüm gürültüsü değildir). Her ikisinin ham çıktısı §3'tedir.

---

## 8. ÖLÇÜLMEDİ / SINIRLAR — tahmin edilmedi

- **Ölçüm SENTETİKTİR.** n=260 T66 ada kadrajı; gerçek arena karesi yoktur (D-88/D-99).
  Bu sayı saha kararlılığı iddia **etmez**.
- Gerçek DJI karelerinde (test29 / val82) karar çevrilmesi **ÖLÇÜLMEDİ** — bu betiğin
  kümesi kayıt defterinin `kabul_kumesi` alanıdır ve gerçek kare kümesine koşulmadı.
- sigma yalnız 2/255'te ölçüldü (artı sigma 0 null kontrolü). **Doz-yanıt eğrisi ÖLÇÜLMEDİ**;
  betiğin kendi başlığı bu seviyenin "gerçeğin ALT SINIRI" olduğunu söylüyor — saha
  gürültüsü daha büyüktür, dolayısıyla saha çevrilmesinin 14/260'tan yüksek olması beklenir,
  ama **ne kadar yüksek olduğu ölçülmedi** (bu bir beklenti, ölçüm değil).
- İki tohum ölçüldü; **istatistiksel anlamlılık test edilmedi**.
- `.onnx` / `.engine` türevleri için **ölçülmedi** — yalnız `.pt`.
- v34 aynı koşumda **yeniden ölçülmedi**; tarihsel 4/260 değeri (2026-08-21) olduğu
  gibi bırakıldı ve eşli kıyasa **sokulmadı**.

---

## 9. AÇIK KALAN — insan/mimar kararı

ÖN_KAYIT §16 gereği terfi **geri alınmadı** ve bu ölçüme dayanarak alınmamalıdır (kapı değil).
Ancak defterde şu artık yazılıdır: **v36, gürültü altında v35'ten daha sık rota kaybediyor.**
Saha gününde JETSON_KILAVUZ §6C birincil→yedek geçişi değerlendirilirken bu, v35 lehine
**yeni bir kalem**dir; v36 lehine olan kalemler (gerçek karede yanlış güzergâh 15/21 → 7/38,
engel üstü waypoint 79 → 3) defterde zaten duruyor. Karar **kullanıcınındır** (D-133).
