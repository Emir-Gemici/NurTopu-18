# NAVITAS · FDR — GÖRÜNTÜ İŞLEME KANIT PAKETİ

> ⚙ Bu belge `scripts/olcum/167_fdr_kanit_paketi.py` tarafından **artefaktlardan üretilir**. Elle düzenlenmez; kaynak değişirse yeniden koşulur. Sayıların hiçbiri metne elle yazılmamıştır.

## 1. Üretim modeli — kayıt defterinden okundu

| alan | değer |
|---|---|
| `model_id` | `navitas-seg-v36-512` |
| çıkarım boyutu | `512` |
| arka uç | `pytorch` |
| SHA-256 | `1d1caca6f6da19ea35e69186a048da960ca5188be6ee6d49d6106457cac46911` |
| kabul kümesi | `sentetik_arena_kadraj_t66` |

> Kaynak: `config/model_registry.json` · `profiles.competition`. Saha paketindeki ayna kopya `jetson_paket/config/model_registry.json` ile aynı olmalıdır (nöbetçi: `tests/test_t202_jetson_paket_butunlugu.py`).

## 2. Kabul kapıları — sentetik arena kümesi (n=260)

| kapı | ne ölçer | eşik | ölçülen | sonuç |
|---|---|---|---|---|
| **K0** | körlük yok (boş maske üretmiyor) | `korluk YOK (figur > 0 · bos maske yok)` | `figur zemin %2,66 · raw bos 0/67 · cp bos 0/393` | GECTI |
| **K1** | rota üretilen kare | `>=230` | `255/260` | GECTI |
| **K2** | rotanın molozdan geçmesi | `<=15` | `5.88` | GECTI |
| **K3** | ağır moloz teması | `<=3` | `0.39` | GECTI |
| **K4** | arena dışına taşma | `<=5` | `1.57` | GECTI |
| **K5** | bariyer kesişimi | `=0` | `0` | GECTI |
| **K6** | yanlış güzergâh | `<=5` | `2.75` | GECTI |

⚠ **KAPSAM (kayıt defterinin kendi cümlesi):** *"ARENA ÖLÇÜMLERİNİN TAMAMI SENTETİKTİR (T66 ada kadrajı, n=260); gerçek ARENA karesi YOKTUR — K0..K6 SAHA BAŞARIMI İDDİA ETMEZ."*

> Kaynak: `scripts/olcum/65_kabul_denetcisi.py` · verdikt `scripts/olcum/results/t63/gece_v7a_kabul_verdikt.json`

## 3. 🔴 Gerçek kare kapısı — ÖN KAYITLI EŞİKLER GEÇİLMEDİ

Bu bölüm bilerek öne alınmıştır: üretim modeli, kendi ön kayıtlı eşiklerinin **ikisini geçmeden** terfi etmiştir ve gerekçesi kayıtlıdır.

```text
🔴 ON KAYITLI ESIKLER GECILMEDI: ROTA >= 10 istendi, olculen 8; MASKE_YOK <= 10 istendi, olculen 16. GECILEN: FP <= 1 (1) ve YANLIS GUZERGAH = 0 (0). Terfi bu esikleri GECEREK degil, KULLANICI KARARIYLA yapildi (bkz. `_surum_karari`). ESIKLER DEGISMEDI ve sonraki terfileri baglar (CONTRACTS SS12 ISTISNA satiri).
```

**Terfi kararı:** 2026-08-26 · KULLANICI KARARI · on kayitli ROTA >= 10 / MASKE_YOK <= 10 esikleri GECILMEDI (8/16); gerekce: gercek karede yanlis guzergah 15/21 -> 7/38, engel ustu waypoint 79 -> 3; bedel: K3 0->1, K4 1->4, K6 5->7 (kapi icinde), kaplama67 0,51->0,42, figur zemin 0,15->0,04 (⚠ bu sayi k109 hattidir, payda ICERIK; kabul zincirinin TUVAL paydali ayni-adli sayisi 0,0903->0,0266 — ayrim `metrics.k0_korluk._iki_olcum_hatti_notu`nda yazili, T154/D-294 SS4), val82 FP 0->2; dayanak D-293, ON_KAYIT SS15, curutucu results/gece_20260826/v7a_curut/. Onceki uretim: navitas-seg-v35-512 (sha e00f6b8e...) - SILINMEDI, YEDEK adaydir ve FARKLI HATA YAPAR: arena K3/K4/K6'da daha iyi (0/1/5) ve val82'de FP uret

> Doğrulama kümesi `dji/DOGRULAMA/` = `DJI_20260822172613_0038_D`; CONTRACTS §12 gereği **0038 kareleri eğitime ve erken durdurmaya girmez**.

## 4. Gerçek zamanlılık — eşik TÜRETİLDİ, tahmin edilmedi

Şartname §6.4: hakem onayı alınmayan tespit geçersizdir. Sözleşme `YKS_TESPIT_TAZELIK_S = 5,0` s; karar kare başınadır (kareler arası uzlaşma yoktur). Buradan:

```
GEREKLI_FPS  >=  1 / (5 · p)
```
`p` = bir karenin geçerli rota yayınlama olasılığı.

| küme | p | gereken FPS | kapsam |
|---|---|---|---|
| sentetik arena (260) | 0,9846 | 0,203 | göreve benzer, **sentetik** |
| gerçek DJİ, **sızıntısız** (243) | 0,3457 | 0,579 | gerçek, arenaya **OOD** |

⚠ **D-376:** ilk ölçümde kullanılan gerçek-kare havuzunun **%62'si modelin eğitim kümesindeydi**; yukarıdaki satır sızıntı ayıklandıktan sonrasıdır. Kirli okuma daha iyimserdi.

**Saha `p`'si ÖLÇÜLEMEDİ** — gerçek arena görüntüsü yoktur (maket çekimi yapılmayacaktır). İki sayı alt/üst çerçevedir; arası tahmin edilmemiştir.

### 4.1 Çözünürlük denendi ve **reddedildi** (D-377)

- Sentetik arenada gerileme: `0,9846` → `0,7808` → **RED**
- FPS maliyeti oranı: `1,302` (bütçe kısıt değildi)
- Ön kayıt *"I2 düşerse RED, I1 ne olursa olsun"* diye **sonuç görülmeden** yazılmıştı.

### 4.1b Uçtan uca kare gecikmesi — ölçüldü (D-382/D-383)

- 36 gerçek karede, üretim zinciri + gerçek telsiz halkası (UDP loopback ACK): **p95 0,113 s** — tazelik penceresinin çok altında.
- ⚠ İlk ölçümdeki ~0,46 s'nin ~0,3 s'si bir **soket zaman aşımı sabiti** çıktı (bağımsız çürütücü buldu, D-383); düzeltme sonrası telsiz payı ~2 ms. Seri telsiz hattı **ÖLÇÜLEMEDİ** (saha/Gün-1).
- Model yükleme 2,64 s — uçuş öncesi, bütçe dışı.

### 4.2 FP16 karar denkliği (D-375)

- Zarar yönü (FP32 doğruyken FP16 yanlış şerit): `0` → **GECTI**
- Karar uyuşması: `0,9968` (eşik `0,98`) → **GECTI**

## 5. Yöntem — bu paketin asıl iddiası

Sayılardan çok, sayıların **nasıl** üretildiği:

1. **Ön kayıt (D-107).** Eşik, sonuç görülmeden yazılır ve sonradan gevşetilmez. D-377'de bu kural somut iş gördü: umut verici bir ara sayı (%21,6) önceden yazılmış bir RED kuralıyla karşılaştı.
2. **`ÖLÇÜLEMEDİ != GEÇTİ`.** Ölçülemeyen şey geçmiş sayılmaz; paydası olmayan oran rapora girmez.
3. **Mutasyon kontrolü.** Her kapı, kaldırıldığında **düşerek** ayırt ediciliğini kanıtlar. Mutasyon koda uygulanır, yoruma değil; uygulanmayan mutasyon başarı sayılmaz (D-370).
4. **Çürütme kaydı.** Yanlış çıkan iddialar **silinmez**, üstü çizilip düzeltmesine işaret verilir (D-373). Bu paket, kendi hatalarını da gösterir.

> Kanıt defteri: `REVIEW_LOG.md`. Bugüne dek **çürütülmüş kendi iddiaları** dâhil her kayıt ölçümlüdür.
