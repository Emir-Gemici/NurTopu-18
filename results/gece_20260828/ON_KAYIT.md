# GECE PROGRAMI — 2026-08-28 · ÖN KAYIT (D-107: sonuç görülmeden yazıldı)

> **Yetki (kullanıcı, verbatim):** *"hala etiketleme ve yol bulma yetersiz ayrıca
> dji klasöründeki yeni verileri de test klasörüne alabilirsin ve tüm kontrol
> sende bugünlük başamele de mimarda sensin projenin teknofest şartnamesine göre
> kusursuz çalışmasını istiyorum bunun için herşeyi yap gerekli etiketlemeleri
> yap sonrasında ise model eğit 15 saat boyunca kontrol tamamen sende tüm
> onayları veriyorum"* ve *"bize şartnamede verilen görselde yollar nasıl
> kapandıysa dubaya benzeyen ince uzun şeyle bizde de veri setinde o lazım adını
> bilmiyorum araştır"*.
>
> **Alan:** Claude 2 — bugün **mimar + başamele** (vekâlet, 1 gün).
>
> **Korunanlar (yetki bunları kaldırmadı):** anayasa **madde 15** (serbest alanı
> BÜYÜTEN işlem yok) · madde 16 (sabitler sözleşmeden) · `python` değil venv ·
> OpenCV/NumPy/heapq · kapı 15/15 + `discover -s tests`.
> **Kalkan:** `git push` yasağı — kullanıcı 2026-08-28 *"pushları yap"* dedi.
> (Push GitHub'ca reddediliyor; ayrı kayıt: §7.)

---

## 0. NESNENİN ADI — araştırıldı, GÖRSELDEN saptandı

Kullanıcı *"dubaya benzeyen ince uzun şey, adını bilmiyorum"* dedi.
`data/arena_referans/sartname_s9_arena.png` **görülerek** saptandı:

> Nesne **duba (trafik konisi) DEĞİLDİR.** Adı **bariyer kolu** — otopark ve
> kontrol noktası bariyerlerinin kırmızı-beyaz çapraz şeritli ince uzun çubuğu
> ("bariyer çubuğu" da denir). Dubayla karıştırılmasının sebebi **aynı
> kırmızı-beyaz reflektif şeritleme**.

Görselde **iki adet**, iki koridorun **enine** yatıyor — üç güzergâhtan ikisini
kapatan şey budur. Ölçülen en/boy oranları **7,0** ve **14,2**.

⚠ Sistemde bunun için zaten bir ad var: `ince_bariyer_maskesi` (T67, KATMAN 2).
Yani nesne **isimsiz değildi**; eksik olan onun **veri setinde** olmasıydı.

---

## 1. ÖLÇÜLMÜŞ DURUM (ön kayıttan ÖNCE ölçüldü, aşağıda ham çıktı)

### 1a. 🔴 Bariyer dedektörü DÖNME KÖRÜ
`codes/karar_sozlesmesi.py::ince_bariyer_maskesi` bileşeni `bw > 4·bh` ile
seçiyor — yani **yalnız YATAY** kolu arıyor. Şartname karesinde ölçüldü:

| dönme | bariyer pikseli | bulunan kol |
|---|---|---|
| 0° | 3644 | 2 |
| **90°** | **0** | **0** |
| 180° | 3644 | 2 |
| **270°** | **0** | **0** |

**Sonuç:** İHA arenaya 90° farklı bir yönelimle girerse bariyer tespiti
**tamamen kör**. Model de yardım edemez (§1b). Kapalı iki koridor **açık**
görünür → yanlış güzergâh → şartname §2.1 uyarınca **0 puan**.

### 1b. 🔴 KENDİ İDDİAMI ÇÜRÜTTÜM — "model bariyeri hiç görmüyor" YANLIŞ

Bu ön kaydın ilk hâlinde *"model bariyer piksellerinin %0,0'ını ENGEL diyor"*
yazıyordu. Kaynağım `codes/karar_sozlesmesi.py`'deki T67 yorumu ve D-92/D-93
idi. **Ölçtüm, yanlıştı.** v36 şartname karesinde bariyer piksellerinin
**%99,9'unu** ENGEL diyor.

> **Ders:** kod yorumu bir ÖLÇÜM DEĞİL, bir ölçümün TARİHİDİR. D-92 eski bir
> modelde ölçülmüştü; yorum güncellenmedi ve beni yanlış yönlendirdi.
> Yorum artık düzeltilecek (T184 gövdesinde).

Aynı şekilde **D-93 de bayat**: keşif ölçümü T68'in bunu büyük ölçüde
kapattığını gösterdi — kabul kümesi manifestinde (n=260) **122 kare** bariyer
taşıyor, bunların **163'ü geçilebilir şeride** konmuş. Kalan kusur: tek
geçilebilir şeritli sahnelerin **%35,17'sinde** havuz yine kapalı şeritlere
geri düşüyor (`51_sentetik_arena.py:1202`).

### 1b-YENİ. 🔴 ASIL KUSUR: model bariyeri yalnız YATAYA YAKIN açılarda görüyor

Şartname karesi döndürülüp v36'ya verildi (bariyer maskesi **aynı** dönüşümle
taşındı):

| açı | model ENGEL oranı | eski KATMAN 2 |
|---|---|---|
| 0° | %99,9 | 2 kol |
| 15° | %99,8 | 0 kol |
| 30° | %99,6 | 0 kol |
| 45° | %69,2 | 0 kol |
| **60°** | **%0,0** | 0 kol |
| 75° | %100,0 | 0 kol |
| **90°** | **%30,8** | 2 kol |
| **120°** | **%0,0** | 0 kol |
| **135°** | **%0,0** | 0 kol |

**Kök neden ölçüldü** — `codes/runs/segment/gece_v7a_v35taban/args.yaml`:
**`degrees: 0.0`** ve **`flipud: 0.0`**. v36 **hiç dönme artırımı görmeden**
eğitildi. Nadir (dik bakan) hava görüntüsünde İHA'nın yönelimi **keyfîdir**;
"yukarısı" diye bir şey yoktur.

⚠ Ayrıca: `config/model_registry.json` v36 için *"reçete t127 birebir"* diyor.
**Değildir.** `139_gece_egitim.py`'nin reçete sözlüğü şu alanları hiç
geçirmiyor: `degrees` (15→0), `flipud` (0,5→0), `copy_paste` (0,3→0),
`cos_lr` (true→false), `close_mosaic` (20→10), `optimizer` (AdamW→auto —
bunun sonucu `lr0` 0,001'den **0,001667**'ye sessizce ezildi, logda yazılı).

Kullanıcının *"veri setinde o lazım"* sezgisi **doğru yeri** işaret ediyordu;
eksik olan bariyerin **kendisi değil AÇISI**.

### 1c. DJI kareleri eğitime GİREMEZ (bugün ölçüldü + GÖRÜLDÜ)
`data/dji_prova_kareler/` — 8 uçuş, **569 kare**, 3840×2160.

| uçuş | kare | parlaklık |
|---|---|---|
| 201722 | 2 | 73,2 |
| 201756 | 6 | 53,8 |
| 202028 | 119 | 23,6 |
| 202420 | 122 | 22,0 |
| 204144 | 39 | 18,1 |
| 205748 | 177 | 20,9 |
| 210528 | 104 | 26,4 |

Sekiz uçuşun **birer karesine gözle bakıldı**: alacakaranlıkta yerden tarla,
beton duvar, **kumandayı tutan bir kişi**, gece otoparkta araba, kırmızı ışıkta
gölgeler. **Hiçbiri havadan nadir arena çekimi değil**; arena, koridor, bariyer
ve H pedi **hiçbir karede yok**.

**Hüküm:** bu kareler *"etiketleme yetersiz"* sorununu **çözemez** — etiketlense
**yanlış şey** etiketlenmiş olur. Test klasörüne **dayanıklılık kümesi** olarak
alınır (§4/G5), **eğitime girmez**. Bu bir kapasite kararı değil **veri
gerçeğidir**; gündüz + nadir + arena benzeri çekim **insan işidir** (T109 hattı).

---

## 2. SORULAR (her biri AYRI ölçülür; biri diğerini örtmez)

- **S1 — Dönme:** dedektör dönme-bağımsız yapılınca bariyer dört dönmede de
  bulunuyor mu, **ve kırmızı H pedi hâlâ eleniyor mu?**
- **S2 — Veri:** üreteç "açık şeride, rastgele açıyla bariyer" üretince model
  bariyeri **öğreniyor mu**? (%0,0 nereye çıkıyor?)
- **S3 — Aralıklı engel:** engeller ARALIKLI diziliyse (duba SIRASI gibi) yol
  bulucu aradan **geçiyor mu**? Geçiyorsa bu ayrı bir kusurdur.
- **S4 — Rota:** bariyer öğrenimi **yanlış güzergâh** sayısını düşürüyor mu?
- **S5 — Bozulmama:** yeni model eski kabul kümesinde **gerilemiyor** mu?

---

## 3. KARARLAR (sonuç görülmeden, gerekçesiyle)

- **K1 — Bariyer sınıfı:** bariyer **yeni bir sınıf DEĞİL**, `ENGEL = 1`'dir.
  Gerekçe: anlam birebir örtüşüyor; 3. sınıf açmak üretim profilini (2 sınıf)
  ve CONTRACTS §1.1/§1.2 çakışma tuzağını riske atar. Sınıf şeması
  **DEĞİŞMEZ**.
- **K2 — Katman 2 KALIR.** Dedektör düzeltilir ama kaldırılmaz: model öğrense
  bile klasik dedektör **monotonik olarak güvenlidir** (yalnız ENGEL katmanına
  ekler → serbest alan yalnız KÜÇÜLÜR, madde 15).
- **K3 — Görünüm çeşitliliği ZORUNLU.** D-99: şartname figürü **yapay zekâ
  üretimi**, bariyerin kırmızı-beyaz oluşu **uydurma olabilir**. Bu yüzden
  üreteç bariyeri **yalnız kırmızı-beyaz** üretmez; nötr/gri/sarı-siyah
  varyantlar da üretir. Aksi hâlde modele *"engel = kırmızıdır"* öğretiriz ve
  gerçek arenada **kör** kalırız.
- **K4 — DJI verisi eğitime girmez** (§1c). Test klasörüne alınır ve ne olduğu
  (gece, nadir değil, arenasız) **dosyanın yanında yazılı** olur.

---

## 4. KAPILAR — eşikler ŞİMDİ yazıldı, sonuca göre GEVŞETİLMEZ

> ⚠ **Dürüstlük notu:** G1'in ölçümü bu ön kayıttan **önce** yapıldı (§1a ve
> kırmızı-ped denemesi). Bu yüzden G1 bir *keşif* değil bir **KİLİTTİR**:
> eşik sonucu gevşetmek için değil, davranışı **dondurmak** için yazılıyor.
> G2–G7 gerçek anlamda ön kayıtlıdır — henüz hiçbiri ölçülmedi.

- **G1 · Dönme-bağımsızlık (KİLİT).** Şartname karesinin **dört** dönmesinde de
  `≥ 2` bariyer kolu bulunacak. **VE** kırmızı KARE ped (en/boy ≈ 1) dört
  dönmede de **engel sayılmayacak**. Biri bile düşerse değişiklik **geri alınır**.
- **G2 · Madde 15.** Yeni dedektör hiçbir karede serbest alanı **büyütmeyecek**:
  `serbest_yeni ⊆ serbest_eski` — kabul kümesinin **tamamında** sınanır.
  Tek karede bile ihlal → geri alınır.
- **G3 · Üreteç — GEÇTİ (ölçüldü).** Bariyer açısı en az 3 farklı kadranda
  olacaktı. `--bariyer-acisi 45` ile üretilen 12 karede 19 kol ölçüldü:
  açı **-59° … +37°**, kolların **%74'ü** ±10° dışında, **5 kadrana**
  yayılmış. (*"Açık şeritte bariyer %0,0"* şartı §1b'deki düzeltme yüzünden
  **düştü** — zaten %0,0 değildi.)
- **G4 · Model bariyeri HER AÇIDA görüyor** (§1b-YENİ ile değişti).
  Şartname karesi 15°'lik adımlarla 0–165° döndürülür (12 açı). Yeni model
  bariyer bölgesinde ENGEL oranını **12 açının en az 10'unda ≥ %60**
  verecek. Bugünkü taban: **12 açının 4'ü** (0/15/30/75 ≥ %60; 45'te %69,2
  ama 60/120/135'te %0,0 — ayrıntı §1b-YENİ).
  ⚠ Eşik **şimdi** yazıldı; eğitim daha başlamadı.
- **G5 · Bozulmama — kabul kümesi.** Yeni model, mevcut kabul kümesinde
  (`config/k7_iyi_kosullu_kume.json`, 88 kare) **K7 ≥ %95 doğru şerit** ve
  **rota üreten ≥ 80/88** eşiklerini koruyacak — yani **v36'nın kapısı**.
  Düşerse yeni model **yayınlanmaz**; v36 üretimde kalır.
- **G6 · Genel kapı.** `codes/test_rota_sentetik.py` **15/15** ve
  `unittest discover -s tests` **OK**. Her adımdan sonra.
- **G7 · Aralıklı engel (S3).** Aralıklı engel dizisi koridoru kapatıyorsa yol
  bulucu **geçmeyecek**. Ölçüm sentetik maskeyle yapılır. Geçiyorsa bu
  **ayrı bir kusur** olarak kaydedilir; bu gece **düzeltilmesi zorunlu değil**
  ama **gizlenemez**.

**Model yayınlama kuralı:** yeni model üretime **YALNIZ** G4 ∧ G5 ∧ G6 birlikte
geçerse alınır. G4 geçip G5 düşerse model **aday** olarak kalır, üretim v36'dır.

---

## 5. EĞİTİM — 15 saat

- Süre **bütçedir, hedef değildir**: 15 saat dolmadan erken durdurma tetiklenirse
  bu bir **başarısızlık değildir**, kayda geçirilir.
- Makine kararsız (5 haftada 8 BSOD, GPU sürücü örüntüsü — kullanıcı notu):
  eğitim **devam edilebilir** (resume) kurulacak ve ara ağırlıklar saklanacak.
  Kesinti olursa kaldığı yerden sürer; **sıfırdan başlatılmaz**.
- GPU işleri **sıralı** koşulur; ikinci bir GPU işi aynı anda başlatılmaz.

---

## 6. BAŞARISIZLIK TANIMI (şimdiden yazıldı)

Aşağıdakiler **başarısızlık değildir**, kayda geçer:
- Model bariyeri öğrenir ama rota sayısı artmaz (S4 düşer) — sebep ayrı ölçülür.
- 15 saat dolar, eşikler geçilmez → **v36 üretimde kalır**. Bu **dürüst** sonuçtur.

Aşağıdakiler **başarısızlıktır**:
- Kapı sonucu görüldükten sonra **gevşetilirse**.
- Bir ölçüm koşulmadan "geçti" denirse.
- DJI gece kareleri **eğitime** sokulursa (§1c'ye rağmen).

---

## 7. PUSH — kullanıcı dondurmayı kaldırdı, GitHub reddediyor

Kullanıcı 2026-08-28 *"pushları yap"* dedi (CLAUDE.md §5 kalktı). Ama push
**GitHub'ca reddedilir**: `1323fbb` commit'inde `git add -A` iki dosyayı
süpürmüş —

| dosya | boyut |
|---|---|
| `dronesolid/Bambu_Studio_win-v02.08.02.61.exe` | 409 MB |
| `navitas_depo.bundle` | 290 MB |

GitHub 100 MB/dosya sınırını aşan **hiçbir** push'u kabul etmez; dosya sonradan
silinse bile nesne pakette kalır. İkisi de uzakta **yok** (doğrulandı).

- **Güvenle itilebilir:** `1323fbb~1`'e kadar **138 commit** (iki dosyadan da
  temiz olduğu doğrulandı).
- **Kalan 28 commit:** itilmemiş geçmişten o iki nesnenin çıkarılması gerekir.
  Güvenlik dalı kuruldu: `yedek_push_oncesi_20260828` → `0c39e5c`.
- Dosyalar **diskten silinmez** (madde 18); yalnız git takibinden çıkar.
