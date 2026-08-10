# NAVITAS — YEREL LLM DONANIM VE ÇALIŞTIRMA SÖZLEŞMESİ

> **Bu dosya neden var:** Yerel model seçimi bu projede iki kez **tahminle** yapıldı
> ve iki kez de ölçüm tahmini yalanladı. §1–§3 ve §7'deki sayılar 2026-08-04/05
> tarihli gerçek koşumlardan; §4–§5 **2026-08-06'da** yeniden yazıldı (roller
> değişti, bir eleme geri alındı). Model değiştirmeden önce **bu dosya okunur.**
>
> Ayrım korunur: **ÖLÇÜLDÜ** = gerçek koşum · **TAHMİN** = aritmetik/bant genişliği.

---

## 1. Donanım — ÖLÇÜLDÜ

| | |
|---|---|
| CPU | Intel Core Ultra 9 275HX · 24C/24T |
| RAM | **95,38 GiB** kullanılabilir · DDR5-5600 · 2×48 GB çift kanal |
| Bant genişliği | 89,6 GiB/s teorik · ~70 GiB/s gerçekçi |
| GPU | RTX 5080 Laptop · **15,63 GiB** kullanılabilir VRAM |
| Ekran | **Intel iGPU'da** (2560×1600) → RTX'e bağlı ekran yok, VRAM'in tamamı boş |
| C: boş | ~223 GiB |
| Pagefile | 6 GiB sabit, **Automatic** (baskı altında kendiliğinden 18,09 GiB'a büyüdü) |

**Sistem tabanı — ÖLÇÜLDÜ:** LM Studio açık, model yüklü değil → **11,03 GiB**
(LM Studio 6 süreç = 0,62 GiB dâhil). Uygulama kapatarak bunun altına inilemez;
çekirdek + sürücü + pool payı ~3,6 GiB'dır ve boşaltılamaz.

---

## 2. `mmap` — en kritik ayar

**ÖLÇÜLDÜ:** Qwen Q8_0, `--gpu 0.15` ile yüklendi.

```
VRAM'e giden      : 11 274 MiB  (11,0 GiB)
RAM kullanımı     : 90,64 GiB
Beklenen (mmap-siz): 78,99 - 11,0 + 11,03 = 79,0 GiB
Fark              : +11,6 GiB
```

**GPU offload, mmap açıkken RAM'i boşaltmıyor.** llama.cpp GGUF'un tamamını
haritalı tutuyor — VRAM'e kopyaladığı kısmı dâhil.

Sonuç iki moda indirgenir:

| Mod | Davranış |
|---|---|
| **mmap AÇIK** | Sığmasa bile "loaded successfully" der, sessizce diskten sayfalar, hata vermez |
| **mmap KAPALI** | Ya tam sığar ve tam hızda koşar, **ya da yüklemede patlar** |

> **KURAL: `mmap` KAPALI.** (LM Studio → "Try mmap()" kapalı.)
> Sessiz yavaşlama yerine gürültülü hata isteriz.

**Windows bellek sıkıştırması bu yükü kurtarmaz.** Sıkıştırma *modified page list*
üzerinde çalışır (özel/kirli sayfalar). mmap'lenmiş GGUF sayfaları **dosya destekli
ve temizdir** — o listeye hiç girmezler; Windows onları sıkıştırmaz, **atar ve
`.gguf`'tan yeniden okur.**
*ÖLÇÜLDÜ: hard fault tepe **77 558/s** iken pagefile kullanımı **0,133 GiB**,
modified list **0,04 GiB**. Sayfalama tamamen `.gguf` dosyalarına karşı yapıldı.*

---

## 3. Ölçülen koşumlar (2026-08-04, mmap AÇIK)

| Konfigürasyon | tok/s | Available | Hard fault/s |
|---|---|---|---|
| Qwopus 35B-A3B yalnız (13,29 GiB, tamamı GPU) | **48,36** | 81,8 GiB | 13 |
| Qwen Q8_0 yalnız (`--gpu 0.15`) | **8,34** | 4,74 GiB | 186 |
| Qwen Q8_0 + Qwopus birlikte | **6,56** / 15,43 | **1,55 GiB** | 190–587 |

**Oturum tepeleri (358 örnek):** available min **0,67 GiB** · kullanımda max
**94,70 GiB (%99,3)** · standby **84,24 → 0,67 GiB** (dosya cache'i tamamen imha) ·
committed max **113,40 GiB** · hard fault max **77 558/s** · zamanın %36'sında
available < 5 GiB.

### Bu koşumlardan çıkan üç kural

1. **Eşzamanlı iki büyük model YASAK.** Ölçüldü: Qwopus 48,36 → 15,43 tok/s
   (**3,1× yavaşlama**). Roller zaten ardışıktır — aynı anda yüklemeye gerek yok.
2. **`--gpu max` zarifçe geri düşmez, motoru öldürür.** Ölçüldü: Qwen'e `--gpu max`
   verildi → 79,5 s bekledi → `SR exited before becoming healthy, exitCode=1`.
   Kısmi oran (`--gpu 0.15`) ile aynı model 54,3 s'de yüklendi.
3. **Yükleme süresi = model boyutu / disk.** Qwen Q8 (78,99 GiB) `--gpu off`
   ile **2 dk 50 s**. Model takası ucuz değildir — işi **toplu** yap, döngüde takas etme.

---

## 4. Seçilen modeller ve çalıştırma konfigürasyonu

> **2026-08-06 — roller yeniden atandı.** Önceki iki seçim (Qwen **Q8_0** ·
> MiniMax M2.5 UD-IQ3_XXS) kullanıcı tarafından **silindi**. İkisi de §7'nin
> ölçtüğü commit duvarına dayanıyordu. Aşağıdaki üçlü bir tercih değil, aynı
> ölçümlerin dayattığı bölüşümdür.

Roller **ardışıktır**; iki büyük model asla aynı anda yüklenmez.

### 4.0 Model bütçesi — türetilmiş

RAM 95,38 − sistem tabanı 11,03 = **84,35 GiB** model bütçesi.

| Aday | GiB | pay | aktif param | tok/s tavanı (TAHMİN) |
|---|---:|---:|---:|---:|
| **gpt-oss-120b** MXFP4 | 59,03 | **25,3** | 5,1B | ~26 |
| **Qwen3-Coder-Next** Q6_K | 61,03 | **23,3** | 3B | ~28 |
| Laguna-S-2.1 Q4_K_M | 66,28 | 18,1 | 8B | ~14 |
| Qwopus3.5-122B Q4_K_M | 71,48 | 12,9 | 10B | ~12 |
| *(referans)* Qwen **Q8_0** | *78,99* | *5,4* | *3B* | *ÖLÇÜLDÜ **1,97*** |

Boyutlar **ÖLÇÜLDÜ**: LM Studio indirme işinin `totalSizeBytes` alanı
(`~/.lmstudio/.internal/download-jobs-info.json` — §8'deki doğru kaynak).
tok/s tavanı **TAHMİN**: 70 GiB/s ÷ (aktif param × bit/8).

⚠ Ölçülen gerçek değer **1,97 tok/s = tavanın %7'si.** Bu fark model seçiminden
değil, §7'deki naif `--gpu 0.15` katman bölüşümünden geliyor. **Model
yargılanmadan önce `--n-cpu-moe` ölçülmeli** — dört aday da MoE ve `--gpu 0.15`
MoE yapısını hiç kullanmıyor.

⚠ **Disk:** dördü birden inerse C: 292,2 → ~46 GiB'a düşer; pagefile 64 GiB'a
büyüyebildiği için gerçek pay ~14 GiB olur. İki adayı iptal etmek 137 GiB
geri kazandırır.

### İşçi — `QWEN_CLEANUP.md`

| | |
|---|---|
| Model | **Qwen3-Coder-Next Q6_K** · 80B-A3B · `lmstudio-community/Qwen3-Coder-Next-GGUF` |
| Boyut | **61,03 GiB** (2 parça: 39 816 544 640 + 25 711 922 144 bayt) |
| Pay | **23,3 GiB** (Q8'de 5,4 idi) |
| GPU offload | **önce `--n-cpu-moe` dene** (§7); tökezlerse `--gpu 0.15` |
| Context | **16K** (32K commit limitini doldurdu — §7) |

**Neden Qwen3-Coder:** rol *"eski ve yeni kodu aynı girdiyle koştur, çıktılar
**birebir** aynı olsun"* diyor. Qwen3-Coder ajanik kodlama (araç çağırma, depo
ölçeğinde düzenleme) için tasarlandı; refactoring döngüsü birebir bu.

**Neden Q6_K, Q8_0 değil:** §5'teki *"Q5/Q6 yalnız hızı iyileştirir"* elemesi
**geri alındı** — gerekçesi ve dersi §5'in sonunda. Özet: Q8'in commit payı
1,10 GiB'a düştü ve Windows üç arka plan görevini öldürdü. Q6_K bir hız tercihi
değil, rolün makineyi öldürmesini durduran tercih. Sadakat kaybı ihmal
edilebilir — birebir karşılaştırmayı zaten model değil test koşumu yapıyor.

### Red team — `REDTEAM.md`

| | |
|---|---|
| Model | **gpt-oss-120b MXFP4** · 117B-A5,1B · `openai/gpt-oss-120b` |
| Boyut | **59,03 GiB** (2 parça) |
| Pay | **25,3 GiB** — dört adayın en genişi |
| GPU offload | **önce `--n-cpu-moe`** (§7); tökezlerse `--gpu` kısmi oran |
| Context | **16K başla** — commit payı ölçülene kadar yükseltme |
| Reasoning effort | K7/K8 → `high` · K1/K2/K5/K6 → `low` |

**Neden gpt-oss-120b:**
1. **Farklı aile** (Qwen değil) → geçidin bağımsızlığı korunur. Bu, MiniMax'ı
   seçerken de kullanılan ölçüttü ve hâlâ geçerli.
2. **En geniş pay.** §7'de süreç öldüren şey modelin zekâsı değil, payın
   tükenmesiydi. 25,3 GiB, red team koşumunun yanında bir arka plan işine yer
   bırakan tek konfigürasyon.
3. **Ayarlanabilir reasoning effort.** Rolün kontrolleri homojen değil: K7
   (kapı-açan-yok) ve K8 (ikiz dosya) **çıkarım** ister; K1/K2/K5/K6 örüntü
   eşlemedir. Tek modelde iki kip = iki ayrı model yüklemekten ucuz.
4. **MXFP4 sonradan sıkıştırma değil, modelin yayınlandığı özgün formattır.**
   Bozulacak daha yüksek hassasiyetli bir "orijinal" yok — bu yüzden §5'in
   "≥Q4 taban" kuralı buraya §5'teki DeepSeek maddesi gibi uygulanmaz.

🔴 **DÜRÜST MALİYET.** Ham ajanik kodlama gücünde MiniMax M2.5'in %80,2
SWE-bench Verified skorunun **altında**. Bu bir gerileme ve öyle kaydediliyor.
Karşılığında alınan şey: MiniMax bu makinede **1,97 tok/s** ve **0,78 GiB
available** ile koşuyordu — yani kâğıt üstündeki puan, gerçekten koşan bir
modelle takas edildi. Skor farkının bu rolde ne kadar kayıp ettirdiği
**ÖLÇÜLMEDİ** (bkz. §10).

### Mekanik tarayıcı — üçüncü rol · ⚠ ÖNERİ, ATAMA DEĞİL

| | |
|---|---|
| Model | **Qwopus3.6-35B-A3B-Coder-APEX-MTP I-Mini** · `mudler/…-GGUF` |
| Boyut | **13,29 GiB** — **tamamı VRAM'e sığıyor** (15,63 GiB) |
| ÖLÇÜLEN hız | **48,36 tok/s** · available 81,8 GiB · hard fault 13/s |
| Rol | K1 (yasaklı bağımlılık) · K2 (sınıf-id) · K5 · K6 — örüntü eşleme |

**Neden üçüncü bir rol var:** bölüşüm "iki büyük model" olarak kurulduğunda,
saniyede 2 token üreten bir model regex taraması yapmak için harcanıyordu. Bu
kontroller **çıkarım değil örüntü eşlemedir** ve 120B istemez. VRAM'e sığan
model diğerlerinin **~25 katı** hızda koşuyor (ÖLÇÜLDÜ) → bir gecede 10 kez
tekrar edilebilir, büyük modelin bütçesi K7/K8'e kalır.

🔴 **BU ROL ATANMADI — atanamaz.** Qwopus 35B, `AGENTS.md`'de **8 numaralı ajan**
ve `CLAUDE.md` madde 10 gereği **kullanıcının manuel denetimindedir**; Claude 1
ona müdahale etmez. Yukarıdaki ölçüm ve gerekçe **kullanıcıya sunulan bir
öneridir**. Kullanıcı onaylarsa `AGENTS.md` sürü tablosu ve `REDTEAM.md`'nin
K1/K2/K5/K6 bölümü güncellenir; onaylamazsa bu kontroller gpt-oss-120b'de
`low` effort ile koşar (§4 red team tablosu).

⚠ **Silinmemesi önerilir** — bu makinede VRAM'e tam sığan ve ölçülmüş tek hızlı
varlık. 59–71 GiB'lık adayların hiçbiri VRAM'e sığmıyor, yerine indirilecek
bir şey yok. Karar kullanıcınındır.

---

## 5. Elenen adaylar — gerekçeli

### 2026-08-06 turunda elenenler

| Aday | Boyut | Elenme nedeni |
|---|---|---|
| **Qwopus3.5-122B-A10B-Kimi-K2.6-destill-healed-abliterated** Q4_K_M | 71,48 GiB | **Abliterated** — artık akıştaki *reddetme yönü* cerrahi olarak silinmiş. Red team rolünün en değerli çıktısı **"DOĞRULANAMADI"**, yani bir reddetmedir; bu, denetçiye yapılabilecek tam ters müdahale. Ayrıca "destill + healed + abliterated" birleşiminin ne tarifi ne bağımsız değerlendirmesi var (DeepSeek V4-Flash'ı eleyen kuralın aynısı, daha sert hâli). Üstelik dördün en büyüğü ve en yavaşı: pay 12,9 GiB, A10B. `mmproj`'u (görü) tek ilginç yanı ama bu projede görüyü YOLO yapıyor. |
| **Laguna-S-2.1** Q4_K_M (poolside) | 66,28 GiB | Kötü model değil — **yanlış yuva.** 118B-A8B, ajanik kodlama için tasarlanmış, GGUF'ları 256K context. Ama **işçi sınıfı** bir model: Qwen ile *aynı* role rakip, ikinci rolü doldurmuyor, üstelik token başına ~2× yavaş (A8B vs A3B) ve 5,25 GiB daha büyük. ⚠ poolside *"stock llama.cpp `unknown model architecture: laguna` verir, fork gerekir"* diyor — **ÖLÇÜLDÜ: LM Studio 2.27.1 CUDA runtime'ının `llama-common.dll`'inde `laguna` dizesi VAR**, destek gelmiş. **Uyumluluk engel değil.** İşçi rolüne *meydan okuyucu* olarak saklanabilir; ama karar §10'daki kalibrasyon koşumuyla verilir, tahminle değil. |

### Önceki turlarda elenenler

| Aday | Boyut | Elenme nedeni |
|---|---|---|
| **DeepSeek V4-Flash** (antirez) | 90,89 GiB | Yönlendirilen uzmanlar **~2 bit** (IQ2_XXS/Q2_K) — bozulma tam K7/K8'in olduğu yerde. Skorları bağımsız doğrulanamıyor (DeepSWE 54,4 vendor-reported, harness yayınlanmadı; %80,6 **Pro-Max**'a ait). Pay 6,46 GiB. |
| **GLM-5.2** | 245 GB @2-bit | 744B — 2 bitte bile sığmıyor |
| **MiniMax UD-Q3_K_XL** | 94,34 GiB | Pay 3,01 GiB — çok dar |
| **MiniMax Q3_K_S** (standart) | 91,91 GiB | UD-IQ3_XXS'ten 5 GiB büyük, payı yarıya indiriyor (5,44 GiB), üstelik dinamik değil |
| **gpt-oss-20b** | ~12 GiB | Hızlı ve VRAM'e sığıyor ama K7/K8 için kapasitesi düşük. ⚠ **120b ile karıştırma** — 20b elendi, 120b §4'te red team olarak seçildi. |

### ≥Q4 taban kuralı — mekanizması

Kullanıcının *"Q4'ün altı çok sıkıntı yapıyor"* gözlemi doğru ve **MoE'de daha da
serttir**: token başına yalnız birkaç uzman ateşlendiği için nicemleme gürültüsü,
yoğun modeldeki gibi tüm parametre havuzuna yayılıp sönümlenmiyor. DeepSeek
V4-Flash'ı eleyen gerekçe tam buydu.

İki incelik, kuralı körlemesine uygulamamak için:

- **Bit sayısı tek başına karar vermiyor.** Unsloth `UD-` dinamik nicemleri
  hassas tensörleri (dikkat, gömme, çıkış, ilk/son katmanlar) yüksek tutar;
  `UD-Q3` ile standart `Q3` aynı iddia değildir. Yine de ≥Q4 taban kuralı sağlam.
- **Tek gerçek istisna: gpt-oss'un MXFP4'ü.** Orada MXFP4 sonradan sıkıştırma
  değil, modelin **yayınlandığı özgün formattır** — bozulacak daha yüksek
  hassasiyetli bir orijinal yok. "4,25 bit" ile bir BF16 modelin Q3'e ezilmesi
  aynı şey değildir.

### Qwen3-Coder-Next nicem boyutları (referans, HF'den byte kesinliğinde)

| Nicem | GiB | Not |
|---|---|---|
| UD-Q8_K_XL | 80,42 | |
| Q8_0 | 78,99 | eski seçim — **geri alındı** (aşağı bak), 2026-08-06'da silindi |
| UD-Q6_K_XL | 73,68 | **tuzak:** düz Q6_K'dan 12,4 GiB büyük, kazancı marjinal |
| **Q6_K** | **61,11** | ← **seçilen** · lmstudio-community sürümü ÖLÇÜLDÜ: **61,03** |
| UD-Q5_K_XL | 55,45 | Q6_K payı yine darsa yedek — ama **önce Q6_K ölçülsün** |
| UD-Q4_K_XL | 46,20 | |

---

### ⛔ GERİ ALINAN ELEME — "Qwen'i Q5/Q6'ya indirmek" (2026-08-06)

Bu tabloda daha önce şu satır vardı:

> **Qwen'i Q5/Q6'ya indirmek** · 55–61 GiB · *Yalnız **tok/s**'i iyileştirir.
> Ardışık gece koşumunda hız amaç fonksiyonu değil; Q8'in sadakati daha değerli.*

**Bu gerekçe yanlıştı ve aynı belgenin §7'si onu çürüttü.** Q8'in payı 5,4 GiB,
commit payı **1,10 GiB**'a düştü; ölçülen sonuç **Windows'un üç arka plan görevini
öldürmesi** oldu. Q6_K payı **23,3 GiB**'a çıkarıyor. Yani Q6_K bir hız tercihi
değil, **rolün makineyi öldürmesini durduran tercih**. Sadakat kaybı ihmal
edilebilir: birebir karşılaştırmayı model değil test koşumu yapıyor.

**Ders:** *"hız amaç fonksiyonu değil"* doğru bir cümledir — ama nicem boyutunu
**yalnız** hızla ilişkilendirmek hataydı. Boyut aynı zamanda **pay**dır, ve pay
tükendiğinde model yavaşlamaz; **süreçler ölür.** Bir sonraki nicem kararında
önce payı hesapla, sonra tok/s'e bak.

---

## 6. Context bütçesi — ÖLÇÜLDÜ

32K context'te prompt'un okuma listesi **taşabiliyor**. Ölçülen dosya maliyetleri
(~3,2 karakter/token):

| Dosya | karakter | ~token |
|---|---|---|
| `CLAUDE.md` | 4 402 | 1 376 |
| `AGENTS.md` | 8 064 | 2 520 |
| `CONTRACTS.md` | 10 011 | 3 128 |
| `TEST_SPECS.md` | 8 880 | 2 775 |
| **`TASK_QUEUE.md`** | **82 785** | **25 870** |
| **`REVIEW_LOG.md`** | **40 945** | **12 795** |

**Kural:** `TASK_QUEUE.md` ve `REVIEW_LOG.md` **asla tam okutulmaz.** İkisi de
grep ile daraltılır; yalnız ilgili blok okunur. Sabit dört belge ~9,8K token
tutuyor — geri kalan ~22K kod, komut çıktısı ve modelin kendi cevabına kalır.

*Bu kusur ölçülmeden fark edilmedi: ilk sürümde `QWEN_CLEANUP.md` beş dosyayı
tam okutuyordu = **35 669 token**, yani prompt daha başlarken 32K'yı aşıyordu.*

---

## 7. COMMIT LİMİTİ — süreç öldüren sınır, ÖLÇÜLDÜ

⚠ **En sert sınır RAM değil, commit limitidir.**

2026-08-05, Qwen Q8 `--gpu 0.15 -c 32768` yüklüyken:

```
Committed : 101,28 / limit 102,38 GiB   →  pay 1,10 GiB
Available :   4,08 GiB
```

Bu durumda **Windows arka plan süreçlerini öldürdü** — iki sürücü koşumu ve bir
indirme gözcüsü `killed` durumuna düştü. Süreçler çökmedi; sistem onlara bellek
veremediği için sonlandırdı.

**Sebep:** commit limiti = fiziksel RAM (95,38) + pagefile. Pagefile *Automatic*
ve ~7 GiB'da kalıyor. 78,99 GiB'lık model + 32K KV + sistem, limiti dolduruyor.

### ✅ UYGULANDI 2026-08-05 — ve sonucu beklediğim gibi ÇIKMADI

Sabit 32 GiB pagefile uygulandı, sistem yeniden başlatıldı. Ölçülen:

| | önce | sonra |
|---|---|---|
| Commit limiti | 108,92 GiB | **127,38 GiB** |
| Commit payı (MiniMax yüklü) | **0,79 GiB** | **20,01 GiB** |
| Available (MiniMax yüklü) | 0,79 GiB | **0,78 GiB** ← değişmedi |
| **Pagefile kullanımı** | — | **0,17 / 32,00 GiB** ← neredeyse sıfır |
| tok/s (kısa istem) | 1,11 | **1,97** |
| tok/s (1199 token istem) | — | 1,47 |

**Ben "~10 kat hızlanır" demiştim. Gerçek ~1,8 kat, ve o bile temiz reboot ile
karışık (önceki ölçüm 8K context ve günlerdir açık bir sistemdeydi; yeni ölçüm
16K context).**

**Neden 10× olmadı — sebep §2'de zaten yazıyordu:** pagefile kullanımı 0,17 GiB.
Sistem pagefile'a neredeyse hiç yazmıyor, çünkü mmap'lenmiş GGUF sayfaları
**dosya destekli**; Windows onları pagefile'a değil **`.gguf`'a karşı** sayfalıyor.
Available 0,79 → 0,78 GiB: fiziksel RAM baskısı hiç değişmedi.

**Pagefile'ın gerçekten çözdüğü şey hız değil, süreç ölümüdür.** Pay 0,79 → 20,01
GiB. Arka plan görevlerini öldüren duvar kalktı; bu tek başına yeterli gerekçe.

**Asıl darboğaz:** 95,38 GiB fiziksel RAM'e 86,91 GiB model + ~12 GiB sistem
sığmıyor. Bunu pagefile çözmez.

⚠ **Henüz denenmemiş gerçek kaldıraç:** MoE expert offload (`--n-cpu-moe`) —
uzmanlar RAM'de, dikkat katmanları GPU'da. Şu anki `--gpu 0.15` naif katman
bölüşümüdür ve MoE yapısını hiç kullanmaz. Aktif parametre 10B; bant genişliği
tavanı ~17 tok/s, şu an %11'indeyiz. 10× buradan gelebilir, pagefile'dan değil.

**Bağlayıcı kurallar:**

1. **Pagefile elle ≥32 GiB sabitlenmeli.** (C:'de ~223 GiB boş.) Yapılmadan
   büyük model + arka plan işi **aynı anda koşturulmaz**. *Bu belgede daha önce
   önerilmişti ama uygulanmadı; bedeli üç öldürülmüş görev oldu.*
   **2026-08-05'te uygulandı** — yönetici hesapla, `Win32_PageFileSetting`
   üzerinden `InitialSize=32768 / MaximumSize=65536`.
   ⚠ İlk deneme `-Filter "Name='C:\\\\pagefile.sys'"` escape'i yüzünden ayarı
   bulamadı, `New-CimInstance` de zaten-var hatası verdi ve betik yarıda öldü —
   geride **`AutomaticManagedPagefile=False` + `init=0 max=0`** bıraktı. Bu hâlde
   reboot atılsaydı pagefile tamamen kaybolur, commit limiti 95 GiB'a düşerdi.
   **Ders: filtre kullanma; tüm ayarları çekip `Where-Object` ile C: olanı seç,
   ve değişikliği reboot ÖNCESİ registry'den doğrula:**
   `HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management`
   → `PagingFiles` = `C:\pagefile.sys 32768 65536`

   ⚠ **Yönetici yetkisi gerekir — AI yapamaz, insan yapar.** Yükseltilmiş
   PowerShell'de:
   ```powershell
   $cs = Get-CimInstance Win32_ComputerSystem
   Set-CimInstance $cs -Property @{AutomaticManagedPagefile=$false}
   $pf = Get-CimInstance Win32_PageFileSetting -Filter "Name='C:\\\\pagefile.sys'"
   if ($pf) { Set-CimInstance $pf -Property @{InitialSize=32768; MaximumSize=65536} }
   else { New-CimInstance -ClassName Win32_PageFileSetting -Property @{Name='C:\pagefile.sys'; InitialSize=32768; MaximumSize=65536} }
   ```
   Ardından **yeniden başlat**. Sonuç: commit limiti 101,38 → ~127 GiB.
2. **Context 32K yerine 16K** — 8K'da available 4,74 GiB iken 32K'da 2,57 GiB'a
   düştü. KV cache commit'e doğrudan yazılıyor.
3. Büyük model yüklüyken **yeni arka plan süreci başlatma.** Koşum bitmeden
   ikinci iş açılmaz.

---

## 8. İndirme ilerlemesi nasıl ÖLÇÜLÜR

⚠ **Dosya boyutuna bakma.** LM Studio `.part` dosyalarını seyrek (sparse)
ayırıyor; disk üzerindeki boyut **0 GiB** görünürken indirme sorunsuz sürebilir.
*(Bu tuzağa düşüldü: 40 dakika "durmuş" sanıldı, gerçekte %23'e gelmişti.)*

**Doğru kaynak:** `~/.lmstudio/.internal/download-jobs-info.json` içindeki
`jobState.type == "active"` işinin `downloadedSizeBytes` / `totalSizeBytes`
alanları. `speedBytesPerSecond` de oradadır.

---

## 9. Ortam tuzakları — ÖLÇÜLDÜ

**`grep` bu makinede PATH'te YOK.** Kalibrasyon-1'de model prompt'un verdiği
`grep -n ...` komutunu koştu ve `'grep' is not recognized` aldı. `rg` de yok.
`findstr` var ama regex'i zayıf (alternasyon, `\s`, `+` desteklemiyor).

**Çalışan yol:** Git ile gelen grep — `C:\Program Files\Git\usr\bin\grep.exe`.
Sürücü harness bunu `GREP` aracı olarak sarmalıyor ve **kabuk kullanmadan**
(`shell=False`) çağırıyor.

⚠ **Kabuksuz çağırmak zorunlu:** grep desenleri `|` içerir (`(import|from)`).
Kabuk operatörü filtresiyle çalıştırılırsa bu desenler **reddedilir** ve
`REDTEAM.md`'deki K1, K2, K3, K5, K6 kontrollerinin tamamı sessizce kırılır.
*(Bu tuzağa bir kez düşüldü; smoke testi yakaladı.)*

🔴 **AMA KABUK KATMANINI ÇÖZMEK YETMEDİ — ikinci katman gözden kaçtı.**
grep varsayılan olarak **BRE** kipindedir ve BRE'de `|` alternasyon değil, düz
karakterdir. Kabuk sorunu çözülünce "alternasyon artık çalışıyor" sanıldı;
çalışmıyordu.

ÖLÇÜLDÜ 2026-08-05, K7 koşumu:
```
GREP -rn  "IHA_LANDED|IKA_GO|_LANDED|_READY|_ACK|MSG_|TIP_" --include=*.py .
   -> exit=1  (ESLESME YOK)
GREP -rnE "IHA_LANDED|IKA_GO|_LANDED|_READY|_ACK|MSG_|TIP_" --include=*.py .
   -> 75 eslesme
```
Sabitler `comms/protocol.py` ve `comms/ika_receiver.py`'de baştan beri vardı.
Model "sabit yok" görüp K7'yi **temiz** raporlayacaktı — sessiz yanlış negatif.

**Kural:** alternasyonda ya `-E` ya `\|`. Harness artık desende kaçışsız `|`
varken `-E` yoksa ve sonuç boşsa açık uyarı döndürüyor.

⚠ **venv sahte pozitifi.** Depo içinde `.gitignore`'lu `navitas-local-train/venv`
var. Düz `-rn ... .` komutu site-packages'i tarar: tek aramada **1348** sahte
eşleşme, hepsi kütüphane kaynağı. 16K context'i doldurur. Harness artık
`venv/.venv/.git/__pycache__/node_modules/navitas-local-train` dizinlerini
otomatik hariç tutuyor (model açıkça venv aramadıkça).
Elle denetimde en kesin küme: `git ls-files "*.py"` → **47 dosya**.

⚠ **Konsol kod sayfası koşum öldürüyor.** Günlük dosyası utf-8 açılsa bile
`print` stdout'a cp1254 ile yazar ve modelin çıktısındaki bir karakter
`UnicodeEncodeError` fırlatıp **tüm koşumu** öldürebilir (K7, tur 5). Harness
başlangıcında `sys.stdout/stderr.reconfigure(encoding="utf-8",
errors="replace")` zorunludur.

**Okuma sınırı:** harness 400 satırdan büyük dosyayı **reddeder**, sessizce
kırpmaz. İlk sürüm 900 satırda kırpıyordu ve `TASK_QUEUE.md`'nin açık görevleri
902–974. satırlardaydı — yani model dosyayı iki kez okudu, ikisinde de göremedi
ve ~40K token boşa gitti.

---

## 10. Doğrulanmamış kalanlar

*(Bu bölüm önceden yanlışlıkla ikinci bir "§8" olarak numaralanmıştı — §8 indirme
ölçümü, §9 ortam tuzakları, §10 budur.)*

Sıra **önem sırasıdır**; 1. madde diğer üçünün cevabını değiştirir.

1. 🔴 **MoE expert offload (`--n-cpu-moe`) hiç denenmedi.** Uzmanlar RAM'de,
   dikkat katmanları GPU'da. Kullanılan `--gpu 0.15` **naif katman
   bölüşümüdür** ve MoE yapısını hiç kullanmaz. Ölçülen 1,97 tok/s, §4.0'ın
   hesapladığı ~26–28 tok/s tavanının **%7'si**. **Bu ölçülmeden hiçbir model
   "yavaş" diye elenmemeli** — ilk inen modelde ilk iş budur.
2. **`mmap` kapalıyken GPU offload'ın RAM'i gerçekten boşalttığı** — mmap açık
   ölçümden türetildi, doğrudan test edilmedi. §4'teki tüm paylar buna dayanıyor.
3. ~~gpt-oss-120b'nin gerçek tok/s'i~~ — **ÖLÇÜLDÜ 2026-08-07.**

   | | ÖLÇÜLEN | TAHMİN edilmişti |
   |---|---|---|
   | Üretim hızı | **6,67 tok/s** (275 tok / 41,3 s) | ~26 |
   | Araç çağırma | **çalışıyor** — OpenAI uyumlu `tool_calls`, argümanlar doğru | test edilmemişti |
   | `llama-server` çalışma kümesi | **60,49 GiB** (boşta) | — |
   | RAM boş / commit boş | **16,23** / **34,75 GiB** | pay 25,3 |
   | pagefile | 0,06 / 32,00 GiB | — |

   **Tahmin %26 tuttu.** Aritmetik tavan (aktif param × bant genişliği) yine gerçeğin
   ~4 katını verdi — Qwen Q8'de de öyle olmuştu (1,97 vs ~28, %7). Bu iki ölçüm birlikte
   şunu söylüyor: **bu makinede MoE tavan hesabı sistematik olarak 4–14× iyimserdir**,
   çünkü hesap `--n-cpu-moe` benzeri bir yerleşimi varsayıyor ama kurulum onu kullanmıyor
   (bkz. madde 1). Bir sonraki nicem/model kararında tavanı **böl**, olduğu gibi alma.

   ⚠ Bellek **boştaki** ölçümdür; KV cache üretimde büyür ve context **131 072** yüklü —
   §7'nin 16K tavsiyesinin **8 katı**. Tepe bellek uzun koşumda yeniden ölçülmeli.

   *Pratik sonuç:* 6,67 tok/s'de araç döngüsünün turu ~40–90 s. Yerel modele iş verirken
   **okuma turlarını prompt'a göm** — dosya içeriğini baştan vermek, modele `READ`
   çağırtmaktan ucuzdur (prefill üretimden çok daha hızlı).
4. **Red team rolünde SWE-bench farkının gerçek bedeli.** gpt-oss-120b, MiniMax
   M2.5'in %80,2'sinin altında; ama bu farkın K7/K8 üzerinde ölçülmüş bir karşılığı
   yok. Kabul edilen bir gerilemedir, ölçülmemiş bir gerilemedir.
5. **İşçi rolünde Laguna-S-2.1 vs Qwen3-Coder-Next.** İkisi de aynı yuvaya aday.
   Karar **tahminle verilmeyecek** — bu dosyanın açılış cümlesi bunun bedelini
   iki kez kaydetti.

### Kalibrasyon koşumu — 5. maddenin kapısı

Aday değiştirmeden önce aynı üç girdi, aynı context, aynı sıcaklık; tek değişken
model. Eşleştirmeli, havuz metriği değil **görev bazında** rapor:

| # | Girdi | Geçme ölçütü |
|---|---|---|
| 1 | `REDTEAM.md` K1 (yasaklı bağımlılık taraması) | `-E` bayrağını kendiliğinden kullanır (§9 BRE tuzağı) ve 0 eşleşmeyi doğru raporlar |
| 2 | `QWEN_CLEANUP.md` refactor turu | Eski ve yeni kod aynı girdide **birebir** aynı çıktı |
| 3 | Uydurmaya davet eden bir soru | **"DOĞRULANAMADI"** der; kanıtsız bulgu yazmaz |

3. satır elemeyi tek başına yapar: kanıtsız bulgu yazan model bu projede
red team olamaz (anayasa madde 6).

---

## 11. Yerel modele iş yaptırma — ÖLÇÜLMÜŞ harness dersleri

> Kaynak: 2026-08-09, gpt-oss-120b (N4) ile **S9** görevi. İlk üç harness tasarımı
> düştü; dördüncüsü işi bitirdi. Aşağıdakiler tahmin değil, o koşumun kayıtları.
> **Yerel modele kod yazdırmadan önce bu bölüm okunur.**

| # | Ölçülen davranış | Tasarım kuralı |
|---|---|---|
| 1 | Tek büyük görevde (6 düzenleme) model **3 turda da aynı planı baştan kurdu**, hiçbirine başlamadı | Görevi **tek değişikliklik adımlara böl**; her adım **temiz bağlamla** başlasın |
| 2 | `max_tokens: 2500` + `effort: high` → bütçe reasoning'in ortasında bitti, `finish=length`, **sıfır araç çağrısı** (5 tur boşa) | `max_tokens` reasoning **ve** araç çağrısını birlikte kapsamalı. high effort'ta **≥32K** |
| 3 | Birebir metin eşleyen `degistir(eski, yeni)` aracı **art arda 4 kez** `BULUNAMADI` döndü (dosya CRLF; model `satırno<TAB>` önekini temizlerken girintiyi bozuyor) | **Satır aralığıyla** çalışan araç kullan: `satir_degistir(bas, son, beklenen_ilk, yeni)`. `beklenen_ilk` yanlış satırı ezmeyi önler |
| 4 | Model dosyayı bulmak için **3 tur okumaya** harcadı; içerik zaten prompt'taydı | İlgili kodu **taze ve satır numaralı** olarak prompt'a göm. Prefill üretimden çok daha hızlı — okuma turu en pahalı israf |
| 5 | Başarı ölçütü `bitir()` çağrısına bağlıydı; model **işi doğru yaptı ama** `bitir` çağırmadan tur sınırına çarptı → "BAŞARISIZ" sayıldı | Ölçüt **dosyanın gerçek içeriği** olmalı, modelin beyanı değil. Doğru koşul sağlanınca adım tur harcamadan kapanır |
| 6 | Model satır silmek için `yeni=""` gönderdi — bu **silmez, boş satır bırakır** | Prompt'ta açıkça söyle: silinecek satırı **aralığa dahil et**, `yeni` içinde ona yer verme |
| 7 | Bir düzenleme sözdizimini bozdu (`f"…{x})"`); model bunu **göremediği için** 3 tur aynı bölgede döndü | Her değişiklikten sonra **derle ve sonucu modele geri ver**. Görmediği hatayı düzeltemez |
| 8 | "Dosya bozuksa dur" koruması, **onarımı yapacak döngüyü** hiç başlatmadı | Bozuk durumda durma — **onarım adımını başa al** |
| 9 | Sözdizimi hatası mesajının **başı** gösteriliyordu; `SyntaxError … line N` traceback'in **sonunda** | Traceback'in son satırlarını ver |
| 10 | `_h.update(_blk)` — sözdizimi geçerli, içerik koşulu sağlandı, **kod çalışmıyor** (bkz. `REVIEW_LOG.md` D-32) | İçerik araması "bir şeyler yazıldı" der, "çalışıyor" demez. **Değişen kod yolunu gerçekten koşturan** bir kapı şart |

**Maliyet muhasebesi (dürüst).** Görev ~6 saatte bitti; bunun büyük kısmı model
hızı değil, **harness tasarım hatalarımdı** — 1, 2, 3, 5, 7, 8, 9 doğrudan bana ait.
6,67 tok/s'de her tasarım hatası 3–20 dakika. Yerel modelle çalışmanın gerçek
maliyeti token değil, **yanlış araç tasarımının tur cinsinden bedeli**.

**Ne iyi çalıştı:** N4 doğru araç verildiğinde adım başına **tek turda** iş
bitirdi (A3, A4, A5-onarım, A8). Planlaması ilk turdan itibaren doğruydu —
düşen şey plan değil, plana ulaşma yolu oldu.
