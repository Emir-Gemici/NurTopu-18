# T243 — mesaj paket boyutu + gerçek görev veri hızı · **ÖLÇÜM**

**Kayıt:** D-462 C · yönerge maddesi Y-3.3.4-M03
**Ön kayıt:** `ON_KAYIT.md` (bu dizinde; ölçümden **önce** yazıldı, ayrı commit)
**Araç:** `scripts/paket_boyutu_olc.py` · **Tarih:** 12 Eylül 2026
**Etiket:** `olcum` — RF **değildir** (UDP loopback).

---

## Komut (yeniden üretmek için)

```
O:\navitas-local-train\venv\Scripts\python.exe -X utf8 -B ^
  scripts/paket_boyutu_olc.py --kip hepsi --pencere 60 ^
  --cikti-dizin results/fdr_sprint_20260910/T243
```

Ham çıktı: `kosum_ciktisi.txt`. Tablo `TABLO.md` bu komutla **üretilir**, elle
yazılmaz.

## Dosyalar

| dosya | içerik |
|---|---|
| `ON_KAYIT.md` | ölçülecek nicelikler, yöntem, rapor ölçütü, tohum (ölçümden önce) |
| `paket_boyutu.json` | N1–N5 — `protocol.encode()` ile sayılmış gerçek baytlar |
| `gorev_veri_hizi.json` | N6–N12 — dört koşumun bayt/paket sayaçları ve hız sözlükleri |
| `TABLO.md` | iki JSON'dan üretilen okunur tablo |
| `kosum_ciktisi.txt` | ölçümün ham stdout'u |
| `kosum_ciktisi_v1_eksik.txt` | **eksik** ilk koşumun ham çıktısı — aşağıya bakınız |
| `mutasyon_t243.py` · `mutasyon_ciktisi.txt` | nöbetçinin mutasyon kontrolü: gerçek dosyalarda 19 mutasyon (D-466 ile +3), her denemeden sonra sha256 ile bayt-eş geri yükleme |
| `kapi/` | koşulan kapıların ham çıktıları (genel kapı, `test_fdr*`, protokol, SiK, comms, İKA, akış doğrulayıcı, tam süit) |

## Ölçülen ne, ölçülmeyen ne

**Ölçüldü:** her mesaj tipinin gerçek `encode()` bayt boyutu; `OPEN_ROUTE`'un
waypoint sayısına göre eğrisi; tam telemetrili ve asgari `HEARTBEAT`;
`HEARTBEAT` alanlarının marjinal maliyeti; `seq`/`t` genişliğinin bayt etkisi;
gerçek üretim yollarıyla (`IhaSender` + `KararYayinci` + `IkaReceiver`) dört
koşumda gönderilen bayt/paket, ortalama ve tepe veri hızı, ortak ortam yükü.

**ÖLÇÜLEMEDİ:** SiK 433 MHz RF hattında fiilî veri hızı; telsizin hava hızı
(Air Speed). **ECC durumu: ÖLÇÜLEMEDİ** — SiK ayar sayfası hiç okunmadı
(`results/atolye_20260912/SONUC_SABLONU.md` A6 satırı boş, `A6_sik_ayar.txt`
yok). Bu üçü FDR §3.3.4.3.4'te **ÖLÇÜLEMEDİ** olarak kalır; buradaki sayılar
onların yerine geçmez. ECC açıkken etkin hava hızının yarıya indiği bilgisi
`ATOLYE_TEST_GUNU_20260912.md` A6 satırından **alıntıdır** ve orada
*"HESAP + BENZER ÖLÇÜM — ölçüm değil"* etiketiyle durur.

**HESAPTIR, ölçüm değildir:** 57600 8N1 ham bütçesi (10 bit/bayt → 5760 B/s,
0,174 ms/bayt); hat doluluk oranları; görev süresi boyunca toplam bayt
(ekstrapolasyon, 900 s'lik koşum yapılmadı); §8 duyarlılık satırı.

## Sonuçlar (ayrıntı `TABLO.md`)

- Çerçeve boyutları: `IHA_LANDED` 71 B · `ACK` 87 B · `NO_ROUTE` 117 B ·
  `CMD` 124 B (`oturum` alanlı) · tam telemetrili `HEARTBEAT` 273 B ·
  21 waypoint'li `OPEN_ROUTE` 365 B. Kodda geçen `~200 B cerceve` tasarım notu
  gerçek çerçevelerin **altındadır**.
- `OPEN_ROUTE` eğimi 11,5 B/waypoint (üretim yolu), 16,0 B/waypoint (en geniş
  gösterim); sözleşme tavanındaki rota 847 B'ye çıkar.
- Görev karışımında İHA TX 1722,3–2008,7 B/s, 5,0–6,0 pkt/s; ortak ortam yükü
  2063,1–2148,5 B/s; tepe TX 1728–2364 B/s.
- Görev toplamı (ekstrapolasyon): İHA 900 s'de 1 550 097–1 807 864 B,
  İKA 600 s'de 1 033 398–1 205 243 B.
- 🔴 **Ölçümün asıl bulgusu:** karar **yayın** tavanı ≈ 1 karar/s. 1,353 Hz ve
  2,0 Hz beslemede yayınlanan karar sayısı değişmedi (saha 61/61, udp 50/50);
  her karar `repeat=4 × interval=0,25 s` = 1,0 s boyunca tutuluyor ve
  latest-wins yuvası fazlasını düşürüyor.

## Rapor ölçütünün karşılığı

Ölçülen en yüksek paylaşımlı doluluk **%37,30** (`udp_tavan`).
**RAPOR ÖLÇÜTÜ (ON_KAYIT §4 madde 2):** Hat doluluk oranı yüzde 80,0 ya da üzeri çıkarsa kırmızı risk satırı açılır.
Ölçülen değer bu oranın altında kaldığı için risk satırı **açılmadı**.

Bu bir kapı değildir; hüküm "ölçüldü"dür, "geçti" değildir.

Ayrı ve **hesaba** dayalı bir uyarı kayda geçer: `TABLO.md` §8, rota sözleşme
tavanındaki waypoint sayısına çıkarsa ortak ortam yükünün ~~3715,4–4003,6 B/s'ye~~
~~4003,6–4107,2 B/s'ye~~ **3995,8–4107,2 B/s**'ye taşındığını gösterir
(12 Eylül düzeltmesi, D-466; **ikinci düzeltme D-466 · T243-C**: ilk aralık
§8 tablosunun yalnız iki **2,0 Hz tavan** satırından geliyordu, ölçülen dört
koşumun tamamı alınınca alt sınır `saha` · 1,353 Hz kolundan **3995,8 B/s**
olur — eski alt sınır **7,8 B/s yüksek** duruyordu, yön yine *riski az
gösterme* yönündeydi). §8 duyarlılık tablosu artık **dört** satırdır;
ECC açık sütunu ham bütçeyi aşar. Bu bir ölçüm değil,
ölçülen iki büyüklüğün çarpımıdır ve telsiz ayarı okunmadan hükme bağlanamaz.

## 12 Eylül düzeltmesi (D-466) — çerçeve sayısı

Çürütücü kanıtlı kusur buldu: ilk hesapta `udp` kolunun `OPEN_ROUTE` çerçeve
sayısı, hatta giden **250** yerine **200** alınmıştı — `yks_gorulen_tipler`
sayacı yalnız YKS'ye ulaşan çerçeveleri sayar, İKA'ya giden 50 çerçeveyi atlar.
FDR §3.3.4.3.3 bu yüzden hat yükünü **eksik** gösteriyordu (3715,4 B/s · %64,50
yerine 4107,2 B/s · %71,31; ECC açıkken %129,01 yerine %142,61) — yön **riski az
gösteriyordu**. Düzeltme:

- Çerçeve sayısı iki yapılandırmada da **tek ölçüm formülüyle** bulunur:
  `gönderilen_paket − HEARTBEAT_sayısı × akran_sayısı` (saha 304 − 60×1 = 244;
  udp 370 − 60×2 = 250). Yapılandırmaya göre dal kalmadı.
- **Çapraz kilit:** `(gönderilen_bayt − HEARTBEAT çerçevesi × HEARTBEAT bayt) ÷
  çerçeve` değeri N1'de ölçülen `OPEN_ROUTE` boyutuna ±%2 içinde olmalıdır
  (ölçülen sapma: −%0,71 … −%0,41, `TABLO.md` §8 ikinci tablo). Tutmazsa hesap
  **yapılmaz**: sessiz yanlış sayı yerine açık boşluk (**OLCULEMEDI**).
- Eski sayılar **silinmedi**; FDR'de ve yukarıda çizili durur.
- **12 Eylül ikinci düzeltmesi (D-466 · T243-C) — bağımsız çürütücünün
  bulgusu.** `scripts/paket_boyutu_olc.py` §8 duyarlılık tablosunu yalnız
  `("saha_tavan", "udp_tavan")` için üretiyordu; 1,353 Hz kollarının duyarlılık
  sayıları (`3995,8` · `%69,37` · `%138,74` ve `4080,6` · `%70,84` · `%141,69`)
  **hiçbir dosyada durmuyordu**. Döngü artık ölçülen koşumların üzerinden
  geçer (`for ad in k["kosumlar"]`), §8 tablosu **dört** satırdır ve FDR'deki
  aralık dört koşumu kapsar (alt sınır 4003,6 → **3995,8 B/s**). Nöbetçide
  `DUYARLILIK_KOSUMLARI` artık `tuple(K["kosumlar"])`'dır: JSON'a bir koşum
  eklenirse aralık sessizce bayatlamaz.
- Nöbetçi artık FDR'deki duyarlılık sayılarını **hesabı üreten fonksiyondan
  bağımsız** formülle yeniden hesaplayıp karşılaştırır (çürütücünün bulgusu:
  eski nöbetçi aynı hatalı fonksiyonu yeniden koşuyordu) ve duyarlılık paragrafı
  D-465 uyarınca **metin eşitliğine** bağlıdır.

## İlk koşum neden değiştirildi (şeffaflık)

İlk koşum (`kosum_ciktisi_v1_eksik.txt`, aynı pencere, aynı kadanslar) ortak
ortam yükünü **eksik** sayıyordu: saha yapılandırmasında alıcı ACK üretmiyordu
(`send_ack=False`) ve üretilen ACK baytları hiçbir sayaca girmiyordu. Üretimde
`IkaReceiver.send_ack` varsayılanı `True`'dur ve o baytlar SiK'in ortak hava
kanalında **yer kaplar**. Düzeltilen koşum aynı pencereyle yeniden koşuldu ve
paylaşımlı doluluk **%29,90 → %35,82**'ye (saha) **yükseldi**. Yani düzeltme
sayıyı iyileştirmedi, **kötüleştirdi**; ilk çıktı silinmedi, bu dizinde durur.

## Sınırlar

1. UDP loopback ölçümüdür. RF yoktur; menzil, paket kaybı, SiK'in kendi
   çerçeveleme/ECC katmanı ve TDM dilim beklemesi burada yoktur.
2. `saha` koşumu SiK seri yolunun **UDP ikizidir** (tek yayın ortamı,
   `wait_ack=False`), seri portun kendisi değildir.
3. Rota geometrisi sentetiktir; **boyutlar sentetik değildir**, gerçek
   `protocol.encode()` çıktısından gelir.
4. 2,0 Hz satırı ölçülen bir kadans değil, **tavan senaryosudur**.
5. Kadans 1,353 Hz Jetson `pt` p50 739,076 ms ölçümünden gelir
   (`results/jetson_20260906/jetson_fps_20260906_orin_nano/ozet.json`); uçuş
   modeli `.pt`'dir (D-431).

**Kapanmayan sınırlar — sayılarak yazılır, kovalanmaz (T243-C, bağımsız
çürütücü ölçümü).** Aşağıdakiler kusur değil, kilidin ÖLÇÜLEN menzilidir:

6. **Çapraz kilidin ayırt etme penceresi — ölçüldü** (`kapi/kilit_penceresi.txt`,
   betiğin fonksiyonları çağrılmadan). ±%2 tolerans şu çerçeve sayılarını
   **geçirir**: `udp_tavan` ve `udp_jetson_olculmus` **244–253** (doğrusu 250,
   yani **−6 … +3** çerçevelik sapma kaçar), `saha_tavan` **239–247** (doğrusu
   244, **−5 … +3** kaçar), `saha_jetson_olculmus` **238–247** (**−6 … +3**).
   Gross hata (250 → 200) sapma **+%24,41** verir ve kesin yakalanır. "Çapraz
   kilitlenir" ifadesi bundan fazlasını söylemez: kilit **gross** hata
   kilididir, birkaç çerçevelik sapmayı görmez.
7. **Metin eşitliği (D-465/D-468) BLOĞU dondurur, BÖLÜMÜ değil.** Kilitli
   bloğun *dışına* çelişkili ikinci bir hüküm eklenebilir; çürütücü üç prob
   kurdu, üçü de kaçtı. T243-C bunlardan yalnız birini kapattı (aynı başla
   eklenen **ikinci kopya** artık düşürür — nöbetçi tek eşleşme arar); geri
   kalanı T244 ailesinin (çelişkili cümle süpürgesi) konusudur.
8. **`gorev_veri_hizi.json` yeniden üretilemez bir zamanlama ölçümüdür.** Tek
   yönlü kurcalanması yakalanır (TABLO.md yeniden üretilip karşılaştırıldığı
   için), JSON + FDR birlikte kurcalanması da yakalandı; ama JSON + FDR +
   TABLO **üçü birden** tutarlı değiştirilirse kilit geçilir. Kapatılamayan
   kaçıştır.
9. **Nöbetçinin kendi `KILIT_TOLERANS` sabiti** tek başına gevşetilse hiçbir
   test düşmüyordu (ölü yüzey). T243-C bunu tek satırlık bir ön kayıtla
   kapattı: `test_KILIT_TOLERANS_ON_KAYITLI`.

## Koşulan kapılar

Ham çıktılar `kapi/` altındadır; aşağıdaki satırlar o dosyalardan okunur ve
nöbetçi test tarafından yeniden karşılaştırılır (elle yazılmış sayı yok).

| kapı | çıktı dosyası | sonuç |
|---|---|---|
| genel kapı (`codes/test_rota_sentetik.py`) | `kapi/genel_kapi.txt` | **GEÇTİ — kol1 15/15 · kol2 şerit 15/15** |
| T243 nöbetçisi | süit içinde | OK |
| `test_fdr*` | `kapi/test_fdr.txt` | OK |
| `test_faz_b_protocol*` | `kapi/test_faz_b_protocol.txt` | OK |
| SiK (`*sik*`) | `kapi/test_sik_genis.txt` | OK |
| comms (`*comms*`) | `kapi/test_comms.txt` | OK |
| `test_iha_sender*` | `kapi/test_iha_sender.txt` | OK |
| İKA (`*ika*`) | `kapi/test_ika.txt` | OK |
| akış doğrulayıcı | `kapi/akis_diyagram.txt` | TÜM DÜĞÜMLER TUTTU |
| tam süit | `kapi/tam_suit.txt` | aşağıya bakınız |
| tam süit, **D-466 düzeltmesinden sonra** (3 koşum) | `kapi/tam_suit_3.txt`, `kapi/tam_suit_4.txt`, `kapi/tam_suit_5.txt` | T243 modülünden düşük YOK; küme farkı aşağıda sayıldı |

🔴 **Tam süit bu worktree'de temiz DEĞİLDİR ve bu gizlenmez.** Düşükler
`kapi/tam_suit.txt` dosyasındadır. Hepsi **izlenmeyen ikili artefakt yokluğu**
sınıfındandır: `models/*.pt` `.gitignore`'ludur (satır 41) ve
`data/kuru_kosu_fikstur/` altında yalnız `manifest.json` izlenir — bir git
worktree'si bu dosyaları hiç almaz.

Bu iddia **ölçüldü**, beyan edilmedi: `kapi/taban_kiyas.py` master'ı
`git archive` ile ayrı bir dizine açar ve düşen yedi modülü **hem tabanda hem
dalda** koşar. Ölçüt, daldaki düşen kümenin tabanın **alt kümesi** olmasıdır
(taban da aynı artefaktlardan yoksundur, hatta bazılarında daha çok düşer).
Sonuç `kapi/taban_kiyas.txt`: **7/7 modülde dal düşükleri tabanın alt kümesi —
T243 kaynaklı YENİ düşük YOK.**

D-466 düzeltmesinden sonra tam süit **üç kez** koşuldu; ham çıktılar
`kapi/tam_suit_3.txt`, `kapi/tam_suit_4.txt`, `kapi/tam_suit_5.txt`. Test
sayısı 2782 → 2794 (nöbetçiye eklenen D-466 kilitleri); bu sayı
`tam_suit_3/4/5` koşumlarınındır — kendi kusuru yüzünden kaldırılan iki test
sonrası **son durum 2793**'tür (`tam_suit_6`, `tam_suit_7` ve bağımsız
çürütücü koşumu). Düşen `FAIL:`/`ERROR:`
kümesinin `kapi/tam_suit_2.txt` (düzeltme öncesi) kümesinden **farkı**:

| koşum | tam_suit_2'ye göre fark | ne olduğu |
|---|---|---|
| `tam_suit_3.txt` | +`test_13_gercek_mavlink_hedefi_sahte_pixhawk_command_long_alir` | **süit içi kararsızlık**: modül tek başına 3/3 GEÇER (`kapi/kararsiz_faz_b_iha_komut_alici.txt`), aynı test `tam_suit_4` ve `tam_suit_5` koşumlarında düşmedi |
| `tam_suit_4.txt` | +`test_tam_suit_3_dusuk_kumesi_ONCEKIYLE_AYNI` | **testin kendi kusuru**: tam süit çıktısını okuyan bir nöbetçi testi yazmıştım; koşum sırasına bağlıydı. **Kaldırıldı** — aşağıya bakınız |
| `tam_suit_5.txt` | +`test_D466_SONRASI_tam_suit_te_T243_dusugu_YOK` | aynı kusurun ikinci biçimi: testi yeniden yazdım, **yine** kendi koşumunda düştü |
| `tam_suit_6.txt` | +`test_kapi_ciktilari_yerinde_ve_hukumleri_dosyadan` | **bootstrap**: o koşum sırasında `kapi/suit_kiyas.txt` henüz üretilmemişti |
| `tam_suit_7.txt` | — | son koşum; karşılaştırma `kapi/suit_kiyas.txt` |

🔴 **Kaldırılan test ve öğrenilen sınır — kayda geçer (silinmedi).** Tam süit
düşük kümesini `tam_suit_2` ile karşılaştıran bir nöbetçi testi yazıldı;
**iki kez**, iki ayrı biçimde, kendi koşumunda düştü (`tam_suit_4`,
`tam_suit_5`). Sebep yapısaldır: tam süit çıktısını **okuyan** bir test, o
çıktıyı **üreten** koşumun içinde koşar ve kabuk yönlendirmesi dosyayı başta
boşalttığı için yarım dosya görür. Hükmü koda kilitlemek ise sonsuz gerilemeye
girer: hüküm bir sonraki koşuma, o koşum da hükme bağlanır (`tam_suit_6`
bootstrap düşüğü bunu gösterir).

Ölçüm bu yüzden **süitin dışına** alındı — `taban_kiyas.py` kalıbı:

```
venv\Scripts\python.exe -X utf8 -B \
  results/fdr_sprint_20260910/T243/kapi/suit_kiyas.py \
  --once tam_suit_2.txt --sonra tam_suit_7.txt
```

Çıktı `kapi/suit_kiyas.txt`; ölçülen hüküm: **YENİ düşük 0 · GEÇEN düşük 0 ·
`test_t243_paket_boyutu` kaynaklı düşük 0** — düşen küme `tam_suit_2` ile
birebir aynı (22 düşük, 11 failure + 11 error). Nöbetçi **aracı ve donmuş ham
çıktıları** kilitler; **hükmü kilitlemez** — hüküm tek komutla yeniden
üretilebilir. (Bu paragraf `tam_suit_7` koşumundan **sonra** yazıldı; o koşumun
kanıt değeri README metnine bağlı değildir.)
Ölçüt de daraltıldı: tam küme eşitliği değil, *bu işin dokunduğu modül
(`test_t243_paket_boyutu`) tam süit içinde hiç düşük üretiyor mu?*

⚠ **Bunlar bu işin kendi kusurlarıydı ve gizlenmedi:** üç başarısız deneme
(`tam_suit_4`, `tam_suit_5`, `tam_suit_6`) ham çıktılarıyla dizinde durur.

⚠ **Sınır (kapatılmadı):** süit içi kararsızlık bu işte **çözülmedi**, yalnız
ölçüldü ve sayıldı. `test_13_...` tek başına geçer, süitte bazen düşer; sebebi
(yuva/zamanlama) bu işin kapsamı dışındadır ve T243'ün dokunduğu dosyalarla
ilişkisi yoktur.

### 🔴 `test_H2c_olcek_1_5_hakem_ekrani` — ölçüm sonucu: T243'ten DEĞİL

Bu iş master'la **iki kez** birleştirildi; ikinci birleşim D-463/D-464'ü
(`tests/test_yks_mk15_hakem_ekrani.py`, 85 satır) getirdi. Birleşimden **sonra**
tam süitte yeni bir düşük göründü:
`test_H2c_olcek_1_5_hakem_ekrani (olcek=1.5, durum='ana_open_route_road3')` —
*"KALINTI KESİŞİM SAYISI DEĞİŞTİ (beklenen 1, ölçülen 0)"*. Ölçülenler:

| ölçüm | sonuç | kanıt |
|---|---|---|
| modül **tek başına**, 3 ardışık koşum (dal) | **3/3 OK** | bu bölümdeki koşum |
| tam süit içinde, birleşimden sonra, iki ardışık koşum | **2/2 DÜŞTÜ** | `kapi/tam_suit.txt`, `kapi/tam_suit_2.txt` |
| tam süit, **T243 modülü keşif dışına alınarak** | **yine DÜŞTÜ** | `kapi/tam_suit_t243siz.txt` |

Üçüncü satır belirleyicidir: T243 nöbetçisi süitte hiç yokken de aynı test
düşüyor. Yani bu **süit sırasına bağlı**, master kaynaklı bir düşüktür; T243'ün
dokunduğu dosyalarla (protokol, `comms/`, `yks_gui`) ilişkisi yoktur — T243 bu
modüllerin hiçbirini değiştirmedi.

⚠ Bu bir T243 bulgusu değildir ve **burada kapatılmaz**: `H2c` sahibi işe
(D-459/D-464 hattı) mimar tarafından yönlendirilmelidir. Bu paragraf, düşüğü
gizlememek için kayda geçirilmiştir.

Not: `kapi/tam_suit_t243siz.txt` koşumundaki fazladan
`test_tests_altinda_sahte_kapi_YOK` düşüğü **deneyin kendi artefaktıdır** —
modülü keşif deseninin dışına almak için geçici olarak yeniden adlandırmak
o kapıyı tetikler. Modül koşumdan sonra sha256 ile bayt-eş geri yüklendi.

## Kilit

Nöbetçi test `tests/test_t243_paket_boyutu.py`: FDR'deki ve bu README'deki her
sayıyı JSON'dan **yeniden hesaplar** (bayat sayı kilidi), ölçüm betiğini
yeniden koşarak paket boyutu tablosunun `protocol.encode()` ile hâlâ bayt-eş
olduğunu doğrular ve belge kilidi kurallarını uygular.

**D-466 ile eklenen üç kilit sınıfı** — bayat sayı değil **YANLIŞ sayı**
kilidi:

1. **BAĞIMSIZ HESAP.** Duyarlılık sayıları, onları üreten
   `M.tavan_waypoint_duyarliligi` çağrılmadan, nöbetçinin içinde elle yazılmış
   JSON aritmetiğiyle (`_bagimsiz`) yeniden hesaplanır ve FDR/TABLO metniyle
   karşılaştırılır. Eski nöbetçi aynı hatalı fonksiyonu yeniden koştuğu için
   kusuru onaylıyordu.
2. **ÇAPRAZ KİLİT ve GEVŞETİLEMEZLİĞİ.** Çerçeve sayısı ölçülen bayt/çerçeve
   ile ±%2 içinde tutarlı olmalıdır; sentetik bir prob (çerçeve sayısı elle
   250 → 200) kilide verilir ve kilidin bunu **reddettiği** ölçülür. Eşik
   gevşetilirse prob geçer ve test düşer.
3. **METİN EŞİTLİĞİ (D-465).** FDR §3.3.4.3.3'teki duyarlılık bloğu ve
   "Sonuç (D-466)" bloğu, ön kayıtlı metne **eşit** olmalıdır (normalleştirme
   yalnız boşluk/satır sonu; çizik/varlık ayıklaması YOK). Canlı sayılar
   bağımsız hesaptan doldurulur, çizili eski sayılar tarihsel sabittir.
**T243-C'den beri bu yüzey kanonik yardımcıyı KULLANIR** — blok ayırma ve
normalleştirme `tests/belge_kilidi.py` dosyasındaki `bloklar()` içindedir
(D-468), nöbetçide
kopyası yoktur; blok başına **tek eşleşme** şartı da eklendi (aynı başla
arkaya konan ikinci/çelişkili bir paragraf artık kilidi düşürür). Kalan
**yokluk taraması** yardımcıları (düşük değerli anlatı yüzeyleri) hâlâ o
dosyadadır ve T242 ile kanoniğe geçirilecektir (D-460, D-461).
