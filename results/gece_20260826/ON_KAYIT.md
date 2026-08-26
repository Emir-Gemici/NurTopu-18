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

## 9. EK — v6 (05:0x, sonuç görülmeden)
v5 gerçek domende en iyiydi (TP 10/13, FP 1) ama arena kabulünü kaybetti (K1 < 230, çatı 0,135). v3 arenayı korudu ama MASKE_YOK 11. Tek denenmemiş orta yol: **rescuenet'siz karışım**.
- **v6** = v35 taban; eğitim DJI ×20 (209 kare) + sentetik_arena (5400) + copy_paste_t127 (344); val DJI 0038 (82); epochs 10 · patience 5; reçete aynı.
- Kapılar §4 aynen (a: kabul K0–K5, K1 ≥ 230, 67'de red ≤ 5, çatı ≤ 0,10; b: ROTA ≥ 10, MASKE_YOK ≤ 10, FP ≤ 1). Sıralama kuralı §7. Düşerse "rescuenet'siz karışım da yetmedi" yazılır.

## 10. EK — TEST29 REFERANS TAMAMLAMA (kullanıcı kararı, 2026-08-27 sabah; sonuç görülmeden)
Kullanıcı: *"29 test karesinin bantlarını tamamlat, v3 ve v6'yı yeniden ölç."*
- **Körlük:** ameleler yalnız kareyi ve MEVCUT elle etiketi görür (`145 hazirla` tabanı); hiçbir model çıktısı, FP listesi ya da kare adı-ipucu verilmez. 29 karenin **tamamı** işlenir (yalnız FP kareleri değil).
- **İzin verilen değişiklik:** yol/koridor kare kenarına kadar sürüyorsa sınıf 0'ı kenara UZATMAK; açıkça yol olan etiketsiz bölgeleri sınıf 0 yapmak; açıkça engel olan etiketsiz bölgeleri sınıf 1 yapmak. **Yasak:** tabandaki sınıf 1'i silmek (`145 kur` geri koyar); çiğ toprak/mera/tarlayı sınıf 0 yapmak (madde 8/12).
- **Ölçüm:** yeni küme `dataset/dji_kirsal_0038_bolum_v2/…/test` (eski küme dokunulmaz); `143` yeni tavan; `142 --test-dizin v2 --tavan yeni` ile **v35, v3, v6** aynı kapılarla (ROTA ≥ 10, MASKE_YOK ≤ 10, FP ≤ 1, (a) tam). ROTA/MASKE_YOK eşikleri v35 tabanından türetilmişti ve **değişmez** (referans değişimi bu iki sayıyı etkilemez; yalnız FP/TP referansı değişir).
- **Yorum kuralı:** referans genişleyince FP'nin düşmesi beklenir; TP artar. Bir aday geçerse §4(d) uygulanır (çürütücü + terfi). Her ikisi geçerse §7 sıralaması (FP en düşük, sonra TP).

## 11. EK — T152 (kullanıcı: "başla", 2026-08-27; sonuç görülmeden)
**(1) İkinci kör etiket geçişi:** 29 test + 30 val (0038 çift-konum) + 52 val (dalga 2/3 0038) = **111 kare**, ameleler yalnız kareyi görür (mevcut etiket, model çıktısı, FP listesi YOK), sıfırdan çizer (`140` aracı, şartname §4b + EK-2..5).
**Uzlaşı kuralı (deterministik, güvenli yön):** piksel sınıf 0 ⇔ İKİ geçiş de sınıf 0; sınıf 1 ⇔ geçişlerden EN AZ BİRİ sınıf 1; aksi hâlde ETİKETSİZ. Geçiş A = mevcut referans (test: `test29_referans` v2; val: mevcut etiketler), geçiş B = yeni. Uyuşmazlık haritası kare başına yazılır (sınıf 0 IoU, sınıf 1 IoU, uyuşmayan piksel payı). Yeni küme `dataset/dji_kirsal_0038_bolum_v3`.
**(2) Yeni kapı (b-ek2), 142'ye eklenir:** her ROTA karesinde (i) rota çizgisinin (ardışık waypoint'leri birleştiren poligon çizgi, tuval koordinatı) **uzlaşı sınıf 0 üstündeki payı ≥ 0,90**, (ii) **sınıf 1 üstünde 0 waypoint**. Biri bile tutmayan rota karesi **YANLIŞ GÜZERGÂH** sayılır ve kapı: YANLIŞ GÜZERGÂH = 0 (şartname: yanlış güzergâh 0 puan). ETİKETSİZ üstünden geçen çizgi payı yalnız raporlanır (kapı değil — İlke B: bilinmeyen zemin sayılmaz ama cezalandırılmaz).
**(3) Yeniden ölçüm:** v35, v3, v6 aynı kapılarla ((a) önceki koşumdan; ROTA ≥ 10, MASKE_YOK ≤ 10, FP ≤ 1 yeni tavana göre, YANLIŞ GÜZERGÂH = 0). Geçen aday §4(d) çürütücüsünden geçer. Hiçbiri geçmezse "aday yok" yazılır; eşik gevşetilmez.

## 12. EK — K6 "rota yol üstünde" (sentetik kabul zinciri) + engel→zemin sızıntı ölçümü (kullanıcı: "önerdiğini yap", 2026-08-27; sonuç görülmeden)
**K6 (yeni kabul ölçütü, `65_kabul_denetcisi`):** kabul kümesi (t66, n=260, YOLO yer gerçeği) — her ROTA karesinde rota çizgisinin yer gerçeği **sınıf 0 üstündeki payı ≥ 0,90** ve **sınıf 1 üstünde 0 waypoint**; tutmayan kare YANLIŞ GÜZERGÂH. **Kapı: yanlış güzergâh oranı ≤ %5** (K4 "arena dışı ≤ %5" ile aynı ölçek; sonuç görülmeden yazıldı). Payda = rota üretilen kare; rota yoksa K1 zaten düşer. Eşik v35'in ölçülecek değerine göre DEĞİŞTİRİLMEZ: v35 düşerse "üretim modeli K6'yı geçmiyor" diye yazılır ve kural gelecek terfileri bağlar (v35'in geri alınması kullanıcı kararıdır).
**Sızıntı ölçümü (kapı değil):** v35/v3/v6 için uzlaşı referansı (111 kare: test 29 + val 82, `t152_uzlasi/*_uc.png`) üzerinde (i) yer gerçeği sınıf 1 piksellerinin modelce zemin sayılan payı (engel→zemin sızıntısı), (ii) yer gerçeği sınıf 0'ın modelce yakalanan payı (geri çağırma), (iii) "rota yol üstünde" payı val 82 karede (n büyütmek için). Sonuç yeniden eğitim KARARI için girdidir; bu turda eğitim YOK.

## 13. EK — T153 Katman 2 "ince beton şerit" çıkarıcı (kullanıcı: "devam et", 2026-08-26; sonuç görülmeden)
**Uygulama:** `karar_sozlesmesi.ince_beton_serit_maskesi(bgr)` — T67 (bariyer) kalıbı: klasik OpenCV, yalnız ÇIKARIR (sınıf 1'e OR'lanır; serbest alan büyümez, madde 15). Hedef: açık renkli (yüksek parlaklık, düşük kroma), **dar** (fiziksel ~0,3–1,2 m ≈ 512'de 3–14 px, letterbox tuvalinde ölçeğe göre) ve **uzun** (en/boy ≥ 4) beton şeritler (drenaj kanalı, bordür). Varsayılan **KAPALI** (`INCE_BETON_SERIT_ETKIN = False`); kapalıyken `get_masks` bayt-eş.
**Ölçüm (AÇIK vs KAPALI, aynı ağırlıklar v35/v3/v6):** (i) val82 + test29 (uzlaşı referansı v3): YANLIŞ GÜZERGÂH, ROTA, TP/FP; **meşru rota kaybı** = KAPALI'da TP olup AÇIK'ta rota üretmeyen kare; (ii) sentetik kabul (t66 n=260): K1–K6 **birebir aynı olmalı** (sentetik ızgara çizgileri yanlış tetiklenirse K1 düşer — bu, dedektörün bu hâliyle GEÇERSİZ olduğu anlamına gelir); (iii) 67 gerçek otopark karesinde red sayısı ≤ 5 kalmalı.
**Benimseme kuralı (varsayılanı AÇIK yapmak için):** v35'te 111 karede YANLIŞ GÜZERGÂH ≥ %50 azalır **ve** meşru rota kaybı ≤ 1 **ve** yeni FP 0 **ve** sentetik K1–K6 birebir **ve** 67'de red ≤ 5. Biri tutmazsa dedektör KAPALI kalır, sayılar yazılır; eşikler sonuca göre oynatılmaz.

## 14. EK — Etiket dalga 4 + v7 eğitimleri (kullanıcı: "a", 2026-08-26; sonuç görülmeden)
**Veri:** 0037/0039'un etiketsiz kalan **277** nadir karesi (0038 = DOĞRULAMA, **dokunulmaz**; CONTRACTS §12). Kör dalga: 56 amele × ~5 kare, şartname §4b + EK-2..5 (madde 12), **vurgu:** beton kanal / bordür / oluk / banket → sınıf 1 (İlke A), yol tam genişlik ve kenara kadar sınıf 0; 7 tutarlılık denetçisi (madde 8/12 + yol-kenara-kadar + uydurma yol). Sonra `144` ile küme (train = 0037/0039 tümü: 101 + 108 + ~277 ≈ 486 kare).
**Eğitim (GPU sıralı, reçete t127 birebir; val = 0037/0039 karelerinden rastgele %15, tohum 0 — yalnız erken durdurma için; 0038 hiçbir karara girmez):**
- **v7a** = tam karışım (rescuenet + sentetik + copy_paste) + DJI ×5 (≈ 2.430 kopya, pay ≈ %16).
- **v7b** = sentetik + copy_paste + DJI ×5 (rescuenet YOK; v6 reçetesi), epochs 10 · patience 5.
**Kapılar (§4(a) + CONTRACTS §12; sonuca göre değişmez):** (a) kabul zinciri K0–K6 VERDİKT True, K1 ≥ 230, 67'de red ≤ 5, çatı ≤ 0,10; (b) test29 (uzlaşı v3): ROTA ≥ 10, MASKE_YOK ≤ 10, FP ≤ 1, **YANLIŞ GÜZERGÂH = 0**; val82 raporlanır (yanlış güzergâh v35 tabanı 10'un altında olmalı, kapı değil). Geçen aday §4(d) çürütücüsünden geçerse terfi; ikisi geçerse §7 sıralaması (FP, sonra TP). Hiçbiri geçmezse "aday yok".
**Beklenen risk (yazılı):** aynı sahanın verisi; best epoch yine 1 çıkabilir — o zaman "veri hacmi değil çeşitliliği" hükmü D-287 ile kesinleşir.

## 15. EK — v7a TERFİ YORDAMI (kullanıcı kararı: "izin veriyorum kurala rağmen", 2026-08-26)
**Karar:** ön kayıtlı §4(b)/§14 eşiklerinden **ROTA ≥ 10** (v7a 8) ve **MASKE_YOK ≤ 10** (v7a 16) geçilmedi; **geçilen:** (a) K0–K6 tam, 67'de red 0, çatı 0,023; FP ≤ 1 (test29 1); **YANLIŞ GÜZERGÂH test29 0** (val82 7/30, v35 10/15). Gerekçe: şartnamede yanlış güzergâh = 0 puan; v7a hiçbir ölçülen eksende v35'ten kötü değil, yanlış güzergâh payı %71 → %18. Bu **insan kararıdır** (D-133); eşikler **değiştirilmedi**, kayıtta "ön kayıtlı eşik geçilmedi" cümlesi durur. Anayasa ihlali yok (madde 15, kabul zinciri korundu).
**Şart:** üç lensli çürütücü (ölçüm / güvenlik / meşruiyet) **terfi_engeli** bulmazsa uygulanır; bulursa kullanıcıya geri döner.
**Altı hizalama noktası (tek commit, D-256 yordamı):** (1) `models/navitas_seg_v36_best.pt` ← `runs/segment/gece_v7a_v35taban/weights/best.pt` (bayt-eş, sha ÖLÇÜLÜR); (2) `config/model_registry.json`: model_id `navitas-seg-v36-512`, path, sha256, imgsz 512, `turevler` (v36 .onnx sha ölçülür, .engine yer tutucu), metrics (K0–K6 + gerçek-kare kapısı sayıları + figür taban listesine v36 satırı), `_surum_karari` (bu metin); (3) `jetson_paket/config/model_registry.json` ayna; (4) ONNX 512 fp16 opset 17 → `results/onnx_export_v36_<tarih>/` + `jetson_paket/models/`; (5) `jetson_paket/models/jetson_derleme_manifest.json` (pc_modeli, asil_model, onnxler, jetson_komutlari, paket_icerigi sha'ları ÖLÇÜLÜR) + .pt/.onnx kopyaları; (6) kılavuz ×2 (v36 adı, §6C yedek = v35) + testler (`test_model_registry`, `test_t143`, `test_gercek_arena_kapisi` sabitleri v36 ölçümüyle, `test_t132`, `test_hakem_kunye`, `test_saha_parametrik`, `test_jetson_paket_defteri`) — sürümü defterden türeten testler elle değişmez. **v35 silinmez** (yedek; §6C geçiş yordamı). Doğrulama: `resolve_model()`'in gösterdiği yoldan `65_kabul_denetcisi` yeniden koşulur → K0–K6 birebir; kapı 15/15 + discover; `olcum_ayna` hizası.

## 16. EK — v36 sonrası dört iş (2026-08-26 akşam; sonuç görülmeden)
- **T154 · kılavuz kapısı kör noktası:** `test_uretim_modeli_hizasi` desen kümesi genişletilir; mutasyon: eski sürüm adı enjekte edilince DÜŞMELİ. Kapı değil, testtir; eşik yok.
- **karar_cevrilmesi (ölçüm borcu, D-294 §4):** `68_karar_kararliligi` v36 için koşulur (v35 ile AYNI parametreler: sigma 2/255, tekrar 3, tohum 7, n=260) ve registry'deki `OLCULMEDI` alanı **ölçülen sayıyla** doldurulur. ⚠ Bu bir **kapı değildir** (bugünkü kabul zincirinde yok; v34 terfisinde kapıydı, eşik ≤ 8/260). Sayı ne çıkarsa yazılır; **v36 terfisi bu sayıya göre geri alınmaz** — geri alma kullanıcı kararıdır. v35 tabanı 9/260 (D-256 §3).
- **T151 · tek karar yolu:** `analyze_path` (Jetson `run_camera`) ile `rota_bul` (`iha_haritala`/`jetson_fps`) arasındaki seçim ÖLÇÜMLE hazırlanır (hangi yol hangi çağrıda, sözleşme farkları, T79 %3,46 kararsızlık); **karar mimar vekilinindir**, ajan yalnız kanıt ve öneri üretir. CONTRACTS §11.2 halka 7 ile Jetson kodu çelişiyor.
- **T150 · HB dedektörü:** `hb_maskesi` sentetik arena kabul kümesinde (n=260, yer gerçeği HB konumu varsa) isabet/yanlış-pozitif olarak ölçülür; **gerçek kırmızı H karesi YOK** → saha isabeti ÖLÇÜLEMEDİ olarak kalır. Üretime bağlama (`goruntu=` geçirme) YALNIZ ölçüm iyi çıkarsa **öneri** olur, bu turda üretime GİRMEZ (fail-closed riski: HB görünmeyen karede HEDEF_YOK her kareyi keser).

## 17. EK — T155 (şerit numarası) ve T157 (kapı delikleri) · 2026-08-26 akşam, sonuç görülmeden
**T155 kapısı:** yer gerçekli 15 sahnede (`results/t151/iki_yol_kiyasi.py` kümesi) üretim yolunun yayınladığı `road` **≥ 14/15 doğru** olmalı (bugünkü taban 6/15; `rota_bul` referansı 15/15). **Ek şart — bozulmama:** aynı 15 sahnede `analyze_path`in **waypoint listeleri ve ret sebepleri değişmemeli** (yalnız yayınlanan numara değişir); sentetik kabul K1–K6 ve T152 rota-yol kapısı **birebir** kalmalı. Biri tutmazsa değişiklik geri alınır ve sayılar yazılır; eşik sonuca göre gevşetilmez.
**T157:** üç delik (imgsz, uzantısız yol, çıplak `vNN` başlık) için ayrı mutasyon; ayrıca kılavuz satır 15'teki bayat başlık ("v27 → v30", gövde v36) düzeltilir. Kapı: mutasyonda test DÜŞMELİ.
**Sıra:** T155 → (ölçüm) → T156 eşiği ancak T155 sonrası ön kayıtla yazılır.

## 18. EK — Üç iş (2026-08-26 gece; kullanıcı: "kusursuz çalışsın, her şeyi yap") · sonuç görülmeden
**Ölçülen darboğaz (bu turda, v36 · uzlaşı referansı):** 111 gerçek karede rota üretilmeyen 73 karenin **53'ünde tavan da rota üretmiyor** (yol enine/yok — kayıp değil); **gerçek kayıp 20 kare: 17'si MODEL KÖRLÜĞÜ** (`MASKE_YOK` ama tavan ROTA), 3'ü K-A bant kapısı. Yani öncelik körlük.
- **A · conf eşiği süpürmesi (GPU, ölçüm — kapı değil):** üretim çıkarımı `conf=0,30` ile koşuyor (`rpi_inference` CLI varsayılanı; `126`/`61`/`65` zincirinde de 0,30). Bu eşik **hiç süpürülmedi**. Süpürme {0,10 · 0,15 · 0,20 · 0,25 · 0,30 (taban) · 0,40 · 0,50}, her eşikte: test29 + val82 → ROTA, MASKE_YOK, TP/FP, **YANLIŞ GÜZERGÂH**; ve sentetik kabul (K0–K6) yalnız **aday eşikte** (en iyi çıkanda) koşulur. **Öneri kuralı (sonuç görülmeden):** bir eşik ancak (i) gerçek kayıp (körlük+bant) **≥ 5 kare azalırsa**, (ii) **YANLIŞ GÜZERGÂH artmazsa**, (iii) FP test29'da ≤ 1 ve val82'de ≤ 2 kalırsa, (iv) sentetik K0–K6 VERDİKT True kalırsa **önerilir**. Öneri = değişiklik değil: `CONTRACTS`/kod eşiği bu turda **değişmez**, karar mimar vekilinindir ve ayrı commit'tir.
- **B · T156:** genel kapıya (`codes/test_rota_sentetik.py`) `analyze_path` kolu eklenir; `rota_bul` kolu **aynen kalır** (15/15 bozulmaz). Eşik: T155 sonrası ölçülen taban **15/15**; kapı **≥ 14/15** (T155 §17 ile aynı disiplin) ve şerit numarası ile birlikte **rota üretilme** de sınanır. Mutasyon: `analyze_path` kolunda şerit kararı bozulunca kapı DÜŞMELİ.
- **C · saha zinciri tazeleme (ölçüm, kod değişmez):** `scripts/saha_kuru_kosu.py` bugünkü kodla koşulur; `CONTRACTS §11.2` halka tablosu ve `results/sartname_bosluk/rapor.md` **bugünkü** duruma göre yenilenir (K1/K4/K5/K6/K8 kapandı, T151 kararı, v36 terfisi). Hangi halkalar hâlâ SAHİPSİZ/KUSURLU — ölçümle.
