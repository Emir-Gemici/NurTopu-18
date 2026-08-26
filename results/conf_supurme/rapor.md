# ON_KAYIT §18-A — GÜVEN EŞİĞİ (conf) SÜPÜRMESİ · **ÖLÇÜM, KAPI DEĞİL**

**Tarih:** 2026-08-26 gece · **Model:** `models/navitas_seg_v36_best.pt` (kayıt
defterinden çözüldü — `codes/model_registry.resolve_model()`; çıplak yol yok)
**Süre:** 3.248 sn, tek süreç sıralı GPU (PC bugün BSOD verdi:
`results/pc_cokme_20260826/rapor.md`)

> 🔴 **HÜKÜM: ADAY EŞİK YOK.** Ön kayıtlı öneri kuralını sağlayan hiçbir eşik
> çıkmadı. Üretim eşiği **0,30** olarak **KALIR**; `CONTRACTS`/kod eşiği
> değiştirilmedi, `61`/`65`/`rpi_inference` CONF sabitlerine **DOKUNULMADI**.
> Sentetik kabul zinciri (K0–K6) **KOŞULMADI** — ön kayıt onu *yalnız aday
> eşikte* koşturur (§18-A madde iv) ve aday yoktur. (Aşağıda §5.)

---

## 1. Ne koşuldu

Zincir üretimin **aynısıdır** ve kopyalanmamıştır: ölçüm sarmalayıcısı
`results/conf_supurme/supurme.py`, çıkarımı `scripts/olcum/126_t138_gece_kumesi.py`
alt süreç olarak koşar:

```
_preprocess → predict(imgsz=INFER_SIZE, conf=E) → get_masks
→ _maskeleri_icerige_kirp → analyze_path(mpp=None, return_clean,
  return_reason, return_olcum)  + olceksiz_wps
```

Analiz tanımları da kopyalanmadı (D-90 dersi: tanım iki yerde ayrı yaşamaz):

| ölçüt | tanımın yaşadığı yer |
|---|---|
| TP / FP / FN (elle etiket tavanına göre) | `142_gece_olcum.py` (b-ek) bloğunun **aynı** kuralı |
| **YANLIŞ GÜZERGÂH** | `scripts/olcum/rota_yol_olcumu.py` → `142_gece_olcum.rota_yol_kapisi` **doğrudan çağrılır** (yol_payı ≥ 0,90 **ve** engel_wp = 0) |
| GERÇEK KAYIP | model rota üretmiyor **ama** elle etiket tavanı üretiyor; `MASKE_YOK` (körlük) / `UC_BANT_TEMAS_YOK` (bant kapısı) diye ayrıştırılır |

**Küme ve referanslar** (uzlaşı referansı v3):

| küme | kareler | etiket (`--etiket-dizin` karşılığı) | tavan JSON |
|---|---|---|---|
| test29 (29) | `dataset/dji_kirsal_0038_bolum_v3/images/test` | `.../labels/test` | `results/gece_20260826/test29_etiket_tavani_v3.json` (ROTA 12) |
| val82 (82) | `dataset/dji_kirsal_0038_bolum_v3/images/val` | `.../labels/val` | `results/gece_20260826/sizinti/val82_etiket_tavani.json` (ROTA 43) |

**Kod değişikliği (tek):** `126`ya `--conf` eklendi. Varsayılan **üretim
değeridir (0,30)**; argümansız koşum önceki davranışın ve JSON çıktısının
**bayt-eşidir** (üretim dışı eşikte çıktıya yalnız `_conf` anahtarı eklenir, ki
kanıt izlenebilir olsun). Kilit + mutasyon kanıtı:
`tests/test_conf_esigi_supurmesi.py` (§6).

**Taban doğrulaması (bağımsız kanıt):** süpürmenin 0,30 satırı, terfi
koşumunda kaydedilen v36 sayılarını **birebir** yeniden üretti —
`config/model_registry.json → metrics.gercek_kare_kapisi`: test29 ROTA 8 ·
MASKE_YOK 16 · TP 7 · FP 1 · FN 5 · yanlış güzergâh 0; val82 ROTA 30 ·
MASKE_YOK 35 · TP 28 · FP 2 · FN 15 · yanlış güzergâh 7. Yani sarmalayıcı
üretim hattını doğru taklit ediyor, "yeni bir alet yeni bir sayı üretiyor"
durumu **yok**.

---

## 2. Tablo — test29 (29 kare · tavan ROTA 12)

| conf | ROTA | MASKE_YOK | UC_BANT | TP | FP | FN | YANLIŞ GÜZ. | gerçek kayıp (körlük+bant) |
|---|---|---|---|---|---|---|---|---|
| 0,10 | 9/29 | 9 | 11 | 8 | 1 | 4 | **0**/9 | **4** (2+2) |
| 0,15 | 9/29 | 11 | 9 | 8 | 1 | 4 | **0**/9 | **4** (2+2) |
| 0,20 | 8/29 | 13 | 8 | 7 | 1 | 5 | **0**/8 | **5** (3+2) |
| 0,25 | 8/29 | 14 | 7 | 7 | 1 | 5 | **0**/8 | **5** (4+1) |
| **0,30 (TABAN)** | **8/29** | **16** | **5** | **7** | **1** | **5** | **0**/8 | **5** (4+1) |
| 0,40 | 7/29 | 18 | 4 | 6 | 1 | 6 | **0**/7 | **6** (5+1) |
| 0,50 | 5/29 | 20 | 4 | 4 | 1 | 8 | **0**/5 | **8** (7+1) |

## 3. Tablo — val82 (82 kare · tavan ROTA 43)

| conf | ROTA | MASKE_YOK | UC_BANT | TP | FP | FN | YANLIŞ GÜZ. | yanlış payı | gerçek kayıp (körlük+bant) |
|---|---|---|---|---|---|---|---|---|---|
| 0,10 | 38/82 | 20 | 24 | 36 | 2 | 7 | **9**/38 | 0,24 | **7** (4+3) |
| 0,15 | 37/82 | 23 | 22 | 35 | 2 | 8 | **9**/37 | 0,24 | **8** (6+2) |
| 0,20 | 34/82 | 27 | 21 | 32 | 2 | 11 | **7**/34 | 0,21 | **11** (9+2) |
| 0,25 | 30/82 | 32 | 20 | 28 | 2 | 15 | **7**/30 | 0,23 | **15** (13+2) |
| **0,30 (TABAN)** | **30/82** | **35** | **17** | **28** | **2** | **15** | **7**/30 | 0,23 | **15** (13+2) |
| 0,40 | 25/82 | 43 | 14 | 23 | 2 | 20 | **6**/25 | 0,24 | **20** (19+1) |
| 0,50 | 20/82 | 55 | 7 | 19 | 1 | 24 | **6**/20 | 0,30 | **24** (23+1) |

## 4. Birleşik (111 kare) ve ÖN KAYITLI ÖNERİ KURALI

Kural (`ON_KAYIT §18-A`, sonuç görülmeden yazıldı, **sonuca göre
değiştirilmedi**): bir eşik ancak **(i)** gerçek kayıp ≥ 5 kare azalırsa,
**(ii)** yanlış güzergâh **artmazsa**, **(iii)** FP test29 ≤ 1 ve val82 ≤ 2
kalırsa, **(iv)** sentetik K0–K6 VERDİKT True kalırsa **önerilir**.

| conf | ROTA 111 | gerçek kayıp | körlük | bant | azalma (taban 20) | YANLIŞ (t29+v82) | FP (t29/v82) | (i) | (ii) | (iii) | **ADAY** |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0,10 | 47 | 11 | 6 | 5 | **+9** | 0 + **9** | 1/2 | ✅ | ❌ | ✅ | **HAYIR** |
| 0,15 | 46 | 12 | 8 | 4 | **+8** | 0 + **9** | 1/2 | ✅ | ❌ | ✅ | **HAYIR** |
| 0,20 | 42 | 16 | 12 | 4 | +4 | 0 + 7 | 1/2 | ❌ | ✅ | ✅ | **HAYIR** |
| 0,25 | 38 | 20 | 17 | 3 | 0 | 0 + 7 | 1/2 | ❌ | ✅ | ✅ | **HAYIR** |
| **0,30** | **38** | **20** | **17** | **3** | — (taban) | 0 + 7 | 1/2 | — | — | — | **TABAN** |
| 0,40 | 32 | 26 | 24 | 2 | −6 | 0 + 6 | 1/2 | ❌ | ✅ | ✅ | **HAYIR** |
| 0,50 | 25 | 32 | 30 | 2 | −12 | 0 + 6 | 1/1 | ❌ | ✅ | ✅ | **HAYIR** |

**🔴 ADAY EŞİK YOK.** İki ayrı sebeple, ve ikisi de aynı takası anlatıyor:

* **0,10 ve 0,15** kuralın *yalnız* (ii) maddesinden düşüyor: gerçek kayıp
  20 → 11/12 (körlük 17 → 6/8) **ama** val82'de yanlış güzergâh 7 → **9**.
  Yani düşük eşik körlüğü rotaya çevirirken **rotayı yola oturtmuyor**:
  0,10'da yeni yanlış kareler **72, 142, 144**, düzelen tek kare **64**
  (net +2). FP değişmedi (129, 223 — ikisi de tabanla aynı).
* **0,20 ve üstü** kuralın (i) maddesinden düşüyor: 0,20 yalnız 4 kare
  kazandırıyor (eşik 5), 0,25 tabanla **rota kümesi olarak aynı**
  (38/111, aynı TP/FP/FN, aynı yanlış güzergâh) — MASKE_YOK ile UC_BANT
  arasında yer değiştirme oluyor, karar değişmiyor. 0,40 ve 0,50 kaybı
  **büyütüyor** (26 ve 32 kare).

**Ölçümün asıl söylediği (yorum, kural değil):** conf eşiği bu modelde
körlük ile yanlış güzergâh arasında **düz bir takastır** ve iyi bir çalışma
noktası üretmiyor. Yanlış güzergâh **payı** her eşikte 0,21–0,30 bandında
sıkışık kalıyor (0,10'da 0,24 · 0,30'da 0,23 · 0,50'de 0,30); yani eşik
düşürmek "daha çok doğru rota" değil, **oransal olarak aynı kalitede daha çok
rota** veriyor. Şartname yanlış güzergâha 0 puan verdiği için (D-293) bu takas
kârlı değildir. Darboğaz eşik **değil**, modelin beton kanal/toprak yol
ayrımıdır (`results/gece_20260826/sizinti/rapor.md`: v36'nın sızıntısı tek
kaynaklı, **beton kanal = zemin**).

## 5. Sentetik kabul zinciri (K0–K6) — NE YAPILDI

**KOŞULMADI, ve bu bir eksik değil bir kuraldır:** ön kayıt K0–K6'yı *yalnız
aday eşikte* koşturur; aday çıkmadı. Görev iki seçenek sunmuştu, **hiçbiri
uygulanmadı** çünkü ikisi de yalnız aday varsa gerekiyordu:

* (a) `65_kabul_denetcisi.py`ye `--conf` eklemek: bu **tek betiği değil dört
  betiği** birden gerektirir — `65` kendi `kaplama()`sinde, `61` (K1–K4,
  K6), `63_bariyer_kesisimi` (çıplak `conf=0.30`) ve `66_k5_bariyer_populasyon`
  (K5) ayrı ayrı çıkarım koşuyor. Eşik yalnız bir kolda değişirse K0–K6
  **tutarsız bir modeli** ölçer.
* (b) Ayrı sarmalayıcıyla K0–K6 eşdeğerini hesaplamak: K1–K6 tanımlarını
  ikinci bir yerde yeniden yazmak demektir (D-90'ın yasakladığı şey).

Aday çıksaydı **(a)** seçilecekti (varsayılanlar korunarak, dört betikte de
`CONF` modül sabitine bağlanarak ve `126`nınkiyle aynı bayt-eşlik testiyle
kilitlenerek); doğrulaması da hazırdı: 0,30 ile koşum, defterdeki v36 kabul
sayılarını (K1 255/260 · K2 %5,88 · K3 %0,39 · K4 %1,57 · K6 %2,75) **birebir**
yeniden üretmek zorundaydı. **Bu turda 65/61/63/66 dosyalarına dokunulmadı.**

## 6. Kod değişikliği, kapı ve mutasyon

`scripts/olcum/126_t138_gece_kumesi.py`: `CONF = 0.30` modül sabiti + `--conf`
(varsayılan `CONF`) + `predict(..., conf=args.conf)`. Üretim eşiği
**değişmedi**.

`tests/test_conf_esigi_supurmesi.py` (5 sınama) iki şeyi kilitler:
1. **Üretim eşiği tek değerdir:** `126.CONF == 61.CONF == 65.CONF ==
   rpi_inference CLI `--conf` varsayılanı == 0,30`.
2. **Argümansız koşum bayt-eştir:** `126`, var olmayan bir ağırlıkla (GPU'suz,
   "AGIRLIK YOK → atlandı" yolu) koşulur; argümansız çıktı ile `--conf 0.30`
   çıktısı **aynı**, `_conf` anahtarı **yok**; `--conf 0.15` ile `_conf` **var**.

**MUTASYON KANITI** (kök satır bozuldu → kapı düştü → bayt-eş geri alındı;
sha256 `3b6eb414e9f2d4141a7daa9314fce23dcfc46794916ec222199671964062a1b7`
mutasyon öncesi ve sonrası **aynı**):

```
=== MUTASYON 1: 'args.conf != CONF' -> 'args.conf == CONF' ===
170:    if args.conf == CONF:
AssertionError: '_conf' not found in {...} : uretim disi esikle kosumda esik CIKTIYA yazilmali
Ran 5 tests in 9.763s
FAILED (failures=3)
=== GERI AL ===
3b6eb414e9f2d4141a7daa9314fce23dcfc46794916ec222199671964062a1b7 *scripts/olcum/126_t138_gece_kumesi.py

=== MUTASYON 2: CONF = 0.30 -> 0.15 ===
44:CONF = 0.15
AssertionError: '_conf' not found in {...}
Ran 5 tests in 9.843s
FAILED (failures=4)
=== GERI AL ===
3b6eb414e9f2d4141a7daa9314fce23dcfc46794916ec222199671964062a1b7 *scripts/olcum/126_t138_gece_kumesi.py
```

## 7. Ham kanıt

| dosya | ne |
|---|---|
| `results/conf_supurme/supurme.py` | ölçüm sarmalayıcısı (kapı değil, defter yazmaz) |
| `results/conf_supurme/olcum.json` | tüm sayılar + kare listeleri + ön kayıtlı kural hükmü |
| `results/conf_supurme/supurme.log` | koşum çıktısı (satır satır) |
| `results/conf_supurme/ham/<küme>_conf0NN.json` | 14 `126` koşumunun ham çıktısı (waypoint listeleri dâhil) |
| `results/conf_supurme/log_<küme>_conf0NN.log` | her `126` alt sürecinin stdout/stderr'i |

## 8. Sınırlar — ölçülemeyenler

* **Sentetik arena hiç ölçülmedi** (K0–K6 aday olmadığı için koşulmadı). Yani
  "düşük eşik arenayı bozar mı" sorusu bu raporda **ÖLÇÜLEMEDİ**; tablo yalnız
  111 gerçek kare hakkındadır.
* **Hız/gecikme ölçülmedi.** Düşük eşik daha çok maske → `analyze_path` daha
  yavaş: koşum süreleri 0,50'de 232 sn, 0,10'da 490 sn (val82) — bu bir PC
  ölçümüdür, **Jetson FPS'i değildir** ve kapıya girmez.
* **Tek uçuş, tek gün, tek saha türü** (0038, kırsal yol). Arena benzeri saha
  (kırmızı H, moloz, bariyer) kanıtı **yoktur** (T111/D-198 açık).
* Karar mimar vekilinindir; bu rapor **öneri bile üretmiyor** (aday yok) ve
  hiçbir eşiği değiştirmiyor.
