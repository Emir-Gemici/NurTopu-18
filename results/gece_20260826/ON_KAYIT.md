# GECE PROGRAMI — 2026-08-26 → 27 · ÖN KAYIT (D-107: sonuç görülmeden yazıldı)

> **Yetki:** kullanıcı, 2026-08-26: *"codex işini bitirdi ... etiketleme ve yol
> bulma yetersiz ... dji klasöründeki yeni verileri de test klasörüne alabilirsin
> ... tüm kontrol sende, bugünlük başamele de mimar da sensin ... şartnameye göre
> kusursuz çalışmasını istiyorum, bunun için her şeyi yap"* ve
> *"tüm onayları veriyorum, onay bekleme, 9 saat yokum, boş durma."*
> **Alan:** Claude 2 — bu gece **mimar + başamele** (vekâlet 2, 1 gün).
>
> **Korunanlar (yetki bunları kaldırmadı):** `git push` YOK (§5 açıkça kalkmadı) ·
> anayasa madde 15 (serbest alanı büyüten işlem yok) · `python` değil venv ·
> OpenCV/NumPy/heapq · kapı 15/15 + `discover -s tests`. **Terfi:** "tüm onaylar"
> kapsamındadır; ama YALNIZ §4'teki ön kayıtlı kapı geçerse ve bağımsız çürütücü
> kıramazsa — sayıya bakıp karar değiştirilmez.

## 0. Defter araması (D-252) — ne biliniyor, ne bilinmiyor
- Gerçek gündüz karede üretim v35: bakır 0038 **rota 11/59, MASKE_YOK 35/59**
  (`results/dji_kirsal/bakir_0038_taban.json`). Tek gerçek arena karesinde
  **yol=None** (D-283). Gece prova kareleri (20 Ağustos, 569 kare) **kullanılamaz**
  (T138: MASKE_YOK 546/569, parlaklık 13–70) — bu gece test verisi DEĞİLDİR.
- Rotanın olmamasının üç ölçülmüş nedeni vardır (D-280/281/282): **model körlüğü**
  (MASKE_YOK), **yönelim** (yol bant eksenine dik → YAPISAL, 18/59; elle etiket
  tavanı 28/59; döndürünce 14/18 geçiyor), **parçalılık** (kural kaldırınca 0 kazanç).
- dji_kirsal_v1 "reçete aynen" DEĞİLDİ: `135` zinciri `lr0`/`warmup` geçirmedi →
  koşum lr0 **0,01** (t127: 0,001), warmup 3 (t127: 5). Ayrıca dji payı eğitimde
  **101/12.849 = %0,8**; val'de dji yok → erken durdurma kırsalı hiç görmedi
  (best = epoch 1). Bu iki kusur bu gece **düzeltilerek** eğitilir.

## 1. SORULAR (her biri ayrı ölçülür; biri diğerini örtmez)
- **S1 — Model:** dji payı ve val düzeltilince kırsal görme **rotaya dönüşüyor mu?**
- **S2 — Yönelim:** K-A bandı görüntü eksenine değil **rota eksenine** göre
  kurulunca (görüntüyü rota ekseni dikey olacak şekilde döndürüp bandı orada
  sınamak — serbest alan değişmez, madde 15 korunur) gerçek karede kaç kare
  kazanılıyor, sentetik arenada kaç kare **kaybediliyor**?
- **S3 — Eşik (T142/T135):** zemin sağlamlık kapısı v35 (ve aday) dağılımına göre
  nerede ayırt edici?
- **S4 — Saha hattı (T143):** `.engine` kayıt reddi ve sessiz kamera bitişi.
- **S5 — Veri (T144):** `len(l)` kırpması.

## 2. VERİ — bölüm, bu gece için SABİT
- **Eğitim:** 0037 + 0039 (101 kare, mevcut etiket) — **×20 çoğaltılmış** (sabit
  bağlantı kopyası, `dataset/dji_kirsal_x20`), böylece pay ≈ 2.020/14.770 = %13,7.
- **0038 (59 kare) ikiye bölünür — SIRALI AD LİSTESİNDE tek/çift:**
  çift konum (30 kare) → **val** (erken durdurma bunu görür);
  tek konum (29 kare) → **TEST** (hiçbir eğitim/durdurma kararında YOK).
  ⚠ Ardışık kareler benzer; val↔test sızıntısı **erken durdurmaya** sızar, test
  sayısına sızmaz — çünkü test hiçbir karara girmez. Bu yazılıdır.
- Taban (aynı 29 test karesi, `bakir_0038_taban.json`'dan hesaplanır, koşum
  öncesi): betik `139` ilk çıktısında yazar; **v35 ve v1 tabanı buraya koşumdan
  ÖNCE geçer** (aşağıda §4'te doldurulur, sonuç görülmeden).
- **Kullanıcı izni:** DJI 0037–0039 kareleri test/val olarak **kullanılabilir**
  ("test klasörüne alabilirsin"). Arena figürü (`sartname_s9_arena.png`)
  eğitime **GİRMEZ**.

## 3. EĞİTİM REÇETESİ
- Taban ağırlık: **v35** (`models/navitas_seg_v35_best.pt`); t127 reçetesi
  **birebir** (`epochs 40 · patience 15 · imgsz 512 · batch 12 · seed 0 ·
  deterministic · lr0 0,001 · warmup 5 · workers 8`) — `139` betiği `lr0` ve
  `warmup_epochs`'u AÇIKÇA geçirir (135'in kusuru).
- Karışım: rescuenet_2sinif_engelli + sentetik_arena + copy_paste_t127 **AYNEN** +
  dji_kirsal_x20. Val: mevcut val + dji_kirsal val (30).
- Koşum adı: `gece_v2_v35taban`. İkinci koşum (zaman kalırsa): aynı reçete,
  taban **v34** (`gece_v2_v34taban`) — tek değişken taban.

## 4. KAPILAR — sonuca göre GEVŞETİLMEZ
### (a) Arena bozulmadı mı — KAPI (her kalem tek başına düşürür)
| ölçüt | GEÇTİ | v35 tabanı |
|---|---|---|
| kabul zinciri K0–K5 | VERDİKT True | True |
| K1 rota | ≥ 230/260 | 256 |
| 67 gerçek karede red | ≤ 5 | 0 |
| çatı kaçağı | ≤ 0,10 | 0,043 |

### (b) Kırsalda rotaya dönüştü mü — KAPI (terfi için)
Aynı **29 TEST karesi**, üretim yolu (`126` betiği, ölçeksiz sebep):
| ölçüt | terfi eşiği |
|---|---|
| rota üretilen | ≥ **v35 tabanı + 4** kare **ve** ≥ 1,5 × taban |
| MASKE_YOK | ≤ v35 tabanının 2/3'ü |

**Taban — koşumdan ÖNCE hesaplandı** (`139 hazirla`, `hazirlik.json`, aynı 29 test
karesi, ölçeksiz sebep): **v35 ROTA 6 · MASKE_YOK 16 · UC_BANT 7** ·
v34 ROTA 7 · MASKE_YOK 19 · dji_kirsal_v1 ROTA 6 · MASKE_YOK 14 · UC_BANT 9.
⇒ **Sayısal terfi eşiği: ROTA ≥ 10/29 ve MASKE_YOK ≤ 10/29.** Bu satır eğitim
başlamadan yazıldı ve değişmez.

### (b-ek) EK KAPI — 01:2x'te, eğitim bitmeden ve aday görülmeden eklendi; YALNIZ SIKILAŞTIRIR
Gözle bakınca (frame_000021: yol yok, tarla) anlaşıldı ki 0038'de **yolu olmayan kareler var**;
orada `MASKE_YOK` **doğru** cevaptır ve rota üretmek **yanlış pozitiftir** (şartname: yanlış
güzergâh = 0 puan). Bu yüzden rota sayısı tek başına yetmez:
- Elle etiket tavanı aynı 29 karede üretim yolundan geçirilir (`143_etiket_tavani.py`).
- **FP** = model rota üretir, etiket tavanı üretmez → **FP ≤ 1** ek kapıdır (`142`, `kapi_b`).
- TP/FN raporlanır. (b)'nin ROTA ≥ 10 eşiği olduğu gibi kalır (gevşetilmedi).

### (c) Raporlanır, kapı DEĞİL
`figur_zemin_orani` (v35 0,1508) · `kaplama67_icerik_medyan` (v35 0,5076) ·
arena figüründe yol var/yok · mAP eğrisi (best epoch — 1 ise "v35+1 epoch").

### (d) TERFİ KURALI
(a) ∧ (b) geçerse **ve** taze bir çürütücü ajan ("aday terfi ETMEMELİ" varsayımıyla,
ölçümü yeniden üreterek) kıramazsa → `config/model_registry.json` güncellenir
(kullanıcı yetkisi, bu gece). Aksi hâlde aday **kalır**, terfi ÖNERİLMEZ, sayılar
olduğu gibi yazılır. "Az farkla kaçırdı, verelim" **YAPILMAZ**.

## 5. YÖNELİM (S2) — kapı
- Uygulama: `analyze_path(..., rota_ekseni_derece=None)`; verilmezse davranış
  **bayt-eş aynı** (mevcut 15/15 + testler değişmeden geçer). Verilirse maske
  döndürülür, K-A ve A* döndürülmüş çerçevede koşar, rota geri döndürülür.
  Serbest alan **hiçbir** noktada büyümez (döndürme interpolasyonu `INTER_NEAREST`;
  döndürmede kenara gelen piksel **engel** sayılır — fail-closed).
- Ölçüm: 0038'in **59** karesinde elle etiket + v35 maskesi ile eksen ∈ {0°, 90°}
  "en iyi eksen" tavanı; sentetik kabul kümesinde (n=260) eksen 0° iken K1 **≥ 256
  sabit kalmalı** (bayt-eş).
- Üretimde eksen **uydurulmaz**: kaynak ya operatörün girdiği KB→HB kerteriz + araç
  yönü, ya da ölçüm için açık parametre. Otomatik "en iyi eksen seçimi" bu gece
  **ÜRETİME GİRMEZ** (fail-open riski: kapalı dikey koridor yerine enine rastgele
  koridor).

## 6. KAPI (genel) — her adımdan sonra
`codes/test_rota_sentetik.py` → **15/15** · `discover -s tests -q` → tümü OK
(başlangıç 819 OK, 2 skip). Düşerse adım geri alınır.

## 7. EK — v3 ve v4 koşumları (03:2x, v4 sonucu görülmeden yazıldı)
- **v3** = v2 reçetesi + etiket dalga 2/3 (train +108 kare ×20, val +52 0038 karesi). Eğitim 16 epoch'ta durdu, **best epoch 1** (v2'de 4, v1'de 1). Kapı ölçümü koşuyor; kapılar §4 ile AYNI.
- **v4** = v3 karışımı, **val YALNIZ gerçek DJI 0038** (çift-konum 30 + dalga 52 = 82 kare). Gerekçe: rescuenet/sentetik ağırlıklı val, modelin gerçek domene uyumunu "gerileme" sayıp epoch 1–4'te durduruyor; arena koruması zaten kapı (a)'dadır (kabul zinciri K0–K5 + 67 gerçek kare + çatı). Kapılar §4 ile AYNI; ek olarak v4'te (a)'nın **düşmesi** beklenen bir risktir ve düşerse *"gerçek val arenayı bozdu"* diye yazılır, kapı gevşetilmez.
- Terfi kuralı §4(d) her aday için aynıdır; birden fazla aday geçerse **FP en düşük, sonra TP en yüksek** olan seçilir (bu sıralama kuralı burada, sonuç görülmeden yazıldı).

## 8. EK — v5 (04:5x, v4 ölçümü ve v5 sonucu görülmeden yazıldı)
Dört koşumda da (v1, v2, v3, v4) **best epoch 1–4**; v4'te DJI-only val mAP50-95 epoch 1'de 0,0955 ve sonra **düşüyor** — yani karışımla daha uzun eğitmek gerçek domeni de iyileştirmiyor (×20 kopya + karışım = ezber/çekişme). Kalan tek denenmemiş kaldıraç: **karışımsız** ince ayar.
- **v5** = v35 taban, eğitim YALNIZ DJI ×20 (0037/0039: 101+108 kare), val DJI 0038 (82), **epochs 10 · patience 5**, diğer reçete aynı (lr0 0,001, warmup 5).
- Beklenen risk: kapı (a) **düşer** (arena karışımı yok). Düşerse *"karışımsız ince ayar arenayı bozdu"* diye yazılır; **arena kapısı gevşetilmez**, v5 aday olamaz. (a) geçerse §4(b) ve (b-ek) aynen uygulanır; §7 sıralama kuralı geçerli.
