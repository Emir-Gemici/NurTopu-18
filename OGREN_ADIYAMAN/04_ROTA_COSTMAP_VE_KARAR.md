# 04 · ROTA, COSTMAP VE KARAR — maskeden "şerit 2 açık" cümlesine

> Kaynaklar: `CONTRACTS.md` §3 (çerçeveler), §4 (geometri), §5 (ölçek), §6.2–§6.4 (road, karar geçerliliği, ret sebepleri), §8
> (çözünürlük), §11.2-EK (karar yolu beyanı) · `codes/rpi_inference.py` (`analyze_path`, `run_camera`) · `codes/karar_sozlesmesi.py`
> (eşikler, ret sebepleri, `serit_no`, `rota_serit_karari`, HB dedektörü) · `codes/costmap_path_finder.py` (`rota_bul`, A*).
> Kod düzeyi ayrıntı için `ozet/A_codes.md`.

---

## Seviye 1 — Bir cümle ve büyük resim

Model bir "zemin maskesi" verir; biz o maskeden **İKA'nın gerçekten sığacağı, kareyi alttan üste geçen, tek bir koridor** çıkarır,
o koridorun **gövdesinin hangi üçte birde** olduğunu söyleriz (1 sol · 2 orta · 3 sağ) ve **on ayrı sebepten biriyle reddedebiliriz**.
Karar her karede bağımsızdır ve her karede telsize **tam bir mesaj** gider: `OPEN_ROUTE(road, conf, waypoints)` ya da
`NO_ROUTE(sebep, detay)`. Sessizlik yoktur.

```
zemin maskesi ──AND NOT engel──▶ serbest ──dist ≥ r_gerekli──▶ C-uzayı ──en büyük bileşen──▶ koridor
      ──alt VE üst bant teması (K-A)──▶ A* tanık yol ──güven ≥ 0,20 (K-B)──▶ şerit kararı (gövde) ──▶ OPEN_ROUTE
                                                              └─ herhangi bir adım düşerse ──▶ NO_ROUTE(sebep)
```

## Seviye 2 — Nasıl çalışır, adım adım

### 2.1 Üç koordinat çerçevesi (`CONTRACTS.md` §3) — karıştırınca sessizce yanlış şerit çıkar
| çerçeve | tanım |
|---|---|
| **Kaynak** | kameranın ham piksel uzayı (ör. 1600×900) |
| **Tuval** | letterbox sonrası **kare** uzay (`max(h,w)²`), kenarlar gri 114 dolgu |
| **İçerik** | tuvalin içindeki gerçek görüntü dikdörtgeni `(x0, y0, w, h)` |

**Kural: her oran, eşik ve bölge hesabı İÇERİK dikdörtgenine göre yapılır, tuvale göre asla.** Ölçülmüş ihlaller (düzeltildi):
şerit sınırları tuvale göreydi → 576×1024 portrede net SAĞ koridor için ORTA dönüyordu (şartname: 0 puan); tohum bandı
tuvalin alt/üst %8'i → 16:9'da bantlar tamamen gri dolguda, 18/18 karede rota yok.

### 2.2 Ölçek: metre/piksel (`mpp`) — Halka 5 (`CONTRACTS.md` §5)
`mpp = 2·h·tan(FOV_yatay/2) / W_px`. İrtifa `h` uçuş kontrolcüsünden canlı gelir (`GLOBAL_POSITION_INT.relative_alt`,
`comms/inis_kaniti.py` tek okuyucu). Kurallar:
- Tazelik: örnek yaşı ≥ **0,5 s** ise, hiç örnek yoksa ya da sysid değişirse irtifa **yok** sayılır → `OLCEK_YOK`.
- Makullük bandı: `SARTNAME_ASGARI_IRTIFA_M = 30`, `IRTIFA_MAKUL_UST_M = 200`; dışı ölçek üretmez.
- `W_px` = karar maskesinin **içerik genişliği**, model giriş boyutu (512) değil (aksi 640'ta yarıçapı %20 eksik hesaplar).
- İkinci kaynak: HB pedinin bilinen 2,0 m kenarı (`hb_konumu`, n=260 sentetikte 260/260 tespit, mpp sapması %5,2). İkisi varsa
  telemetri seçilir, HB yalnız doğrular; bağıl fark > **0,25** ise **hiçbiri** (çelişkide ortalama alınmaz, fail-closed).
- `mpp` yoksa görev yolunda **rota üretilmez**. Eski sessiz varsayım (`m = 1.0` → gövde açıklığı 1,10 px, ~11 kat küçük) kapatıldı.

### 2.3 C-uzayı ve serbest alan
`serbest = zemin AND NOT engel` (çıkarma en son). `cv2.distanceTransform` ile her serbest pikselin en yakın engele uzaklığı
`dist`; `gecilebilir = dist ≥ r_gerekli_px` (`r_gerekli_px = 1,10 m / mpp`). Bu "yapılandırma uzayı"dır: nokta-robot burada
gidebiliyorsa 0,70 m'lik gövde + paylar orada sığar. Ölçülen etki (7 kompozit kare, kusursuz yer gerçeği): C-uzayı yokken
doğru şerit 1/7, darboğaz 1 px; C-uzayı ile **6/7**, darboğaz 13–15 px, güven 0,64–0,74.

### 2.4 Koridor seçimi ve iki geçerlilik kapısı (`CONTRACTS.md` §6.3)
- **En büyük bağlı bileşen** alınır.
- **K-A · Uç-bant teması:** bileşen **hem** başlangıç (alt) **hem** hedef (üst) bandına temas etmeli. Bant = içerik yüksekliğinin
  %8'i (`HEDEF_BANT_ORANI=0.08`, `costmap._tohum_maske` ile aynı oran), temas genişliği ≥ içerik genişliğinin %2'si. Bir kez
  yalnız üst bant istenmişti; Codex ölçtü: bariyerle kopmuş koridorda OpenCV üst parçayı seçiyor, "hedefe temas var,
  başlangıca yok" ve kusur `yol=2` diye geri dönüyordu → iki uç şart.
- **A* tanık yol:** alt tohumdan üst tohuma, C-uzayında, açıklık ağırlıklı (`1 + 3·u²`). Plan bütçesi `ROTA_PLAN_MAKS_HUCRE = 32768`;
  aşarsa `GORUS_HATTI_KOPUK`. Ardışık waypoint'ler arası görüş hattı engelden geçiyorsa `KENAR_GUVENSIZ`.
- **K-B · Güven eşiği** `ROTA_GUVEN_ESIGI = 0.20`. `guven = min(1, darboğaz / (0,035 · icerik_w))`. Bir kez 0,50 kondu (sentetik
  0,797'den), gerçek GUI yolunda 52 kararın **hepsi** reddedildi (%100 çekimserlik, D-37). Gerçek 67 karede dağılım p50 0,307,
  std 0,030: metrik ayırt edici değil; 0,20 **seçici kapı değil taban koruyucu** (guven=0,0 yayınını engeller; ölçekli kipte
  fiilen ateşlemez; yalnız gövdenin ~4 px'ten ince göründüğü çözünürlükte korur).

### 2.5 Şerit kararı: `road` hangi istatistik? (`CONTRACTS.md` §6.2, T155/D-296)
```
road = olcum["serit_karari"] = karar_sozlesmesi.rota_serit_karari(rota_pikselleri, icerik_x0, icerik_w)
     = rotanın GÖVDESİNİ taşıyan şerit (en çok rota pikseli olan üçte bir; beraberlikte küçük indis)
```
Eskiden `darbogaz_serit` (rotanın en dar noktasının şeridi) yayınlanıyordu; 15 yer-gerçekli sahnede **6/15** doğruydu, çünkü
darboğaz pikseli 13 sahnede rotanın **ucunda**, üç güzergâhın **birleştiği** yerde ölçülüyordu. Gövde tanımıyla **15/15**;
waypoint'ler, retler, güven bayt-eş aynı kaldı (bozulmama ölçüldü). `darbogaz_serit` hesaplanır ama artık yalnız **tanı**.
`road` İKA'nın sürüş girdisi **değildir**; sürüş `waypoints + ref_xy` ile (saf öteleme, dönme yok). `road` hakemin onayladığı
**puanlanan etikettir**.

### 2.6 Ret sebepleri (`CONTRACTS.md` §6.4) — hakem ekranında üç farklı ret üç farklı metin
| sebep | ne zaman |
|---|---|
| `OLCEK_YOK` | mpp türetilemedi |
| `ZEMIN_MASKESI_SUPHELI` | zemin maskesi içeriğin `ZEMIN_KAPLAMA_TAVANI` (0,55) üstünü kaplıyor VE kenar oranı > 0,40 — maske sahneyi ayırt etmiyor (çatı/çim/toprak çöküşü) |
| `MASKE_YOK` | zemin maskesi hiç yok (`trav.sum()==0`) |
| `BILESEN_YOK` | bağlı bileşen yok |
| `UC_BANT_TEMAS_YOK` | K-A |
| `ALAN_YETERSIZ` | koridor alanı `min_area_ratio` altında |
| `GORUS_HATTI_KOPUK` | başlangıç–hedef bağlantısı / doğrulanmış waypoint zinciri kurulamadı |
| `KENAR_GUVENSIZ` | ardışık waypoint'ler arası görüş hattı engelden geçiyor |
| `DUSUK_GUVEN` | K-B |
| `KORIDOR_DEGIL` | darboğaz **bir şeridin tamamından** geniş (`darbogaz/icerik_w > 1/3`) — bu güzergâh değil açık arazi (arena dışı toprak) |
| `HEDEF_YOK` | HB karede bulunamadı (yalnız `goruntu=` verilirse; üretimde bağlı değil) |

Bağlayıcı: sebep kodları `karar_sozlesmesi`'nde sabit, çıplak string yok; `NO_ROUTE.sebep` bu tablodan; ret yine `yol=None,
waypoints=[]` (sebep bildirmek reddi yumuşatmaz); yeni ret yolu önce tabloya eklenir. Kapı iki yerde birden: çağrı yerleri
(anlamlı sebep) **ve** `IhaSender.send_open_route` (son savunma, eşik altı asla yayınlanmaz).

### 2.7 Histerezis (D-396, 3 Eylül)
Farklı bir şerit ancak arka arkaya K karede teyit edilirse yayına girer; `NO_ROUTE` **asla geciktirilmez**. Ölçüm: ham çevrilme
13→7 ve 24→11; bastırılan NO_ROUTE 0; ön kayıttaki özgün H1 eşiği **sağlanmadı** (`H1_ozgun=false`) — FDR bunu açık yazar.

## Seviye 3 — Ayrıntılar ve ölçümler

### 3.1 Kaplama kapısı tarihçesi (eşikler MODELE bağlı)
v21 için `(0.55, 0.50)`; v24'te gerçek arena karesi (kaplama 0,579) reddedilince `(0.67, 0.50)` yapıldı (T59) — sonra D-283 o
karenin **çökmüş** maske olduğunu (sahne tamamen yeşil) gösterdi: tavan bir çöküşü geçirmek için gevşetilmişti. v35 ile dört
kümede yeniden kalibre: **`(0.55, 0.40)`** — meşru v35 kümelerinde 0 ret, v24 otopark çöküşü 67/67 ve arena çöküşü 1/1 yakalandı.
Ders: **üretim modeli değişince bu kalibrasyon zorunlu adımdır**; kapı doku değil kaplama kapısıdır, orta şiddetli çökmeyi
(`sa_000150`: kaplama 0,617 geçer, yer gerçeği 0,380) yakalayamaz.

### 3.2 `KORIDOR_DEGIL` — arena sınırı neden yerelleştirilmedi
Üç aday imza (ızgara çizgileri, moloz kutusu, dış çerçeve) 260 kare + gerçek karede **üçü de** güvenilmez; gerçek sınır
perspektiften yamuk (~50–60 px indirgenemez hata). Ama kusur **dejenere**: rota ya tamamen içeride ya tamamen dışarıda
(238 kare 0,000 · 10 kare 1,000). Bu yüzden "sınır nerede" değil "bu bir koridor mu" sorulur: tavan 1/3 şerit. Ölçüm: meşru
0/239 yanlış elendi, kusurlu 5/10 yakalandı — **kısmi** çözüm, bilerek fit edilmedi.

### 3.3 İnce bariyer dedektörü (T67; Katman 2)
Şartname figüründe bariyerin 3644 pikselinin %0'ını model engel, %30,9'unu zemin sayıyordu; rota bariyeri 59 px kesiyordu.
Dedektör LAB `a* > 25` kroma + en/boy ≥ 4,0 (HB pedi 1,00 → elenir; bariyer kolu 7,0 / 14,2). Ölçütler **oran** (çözünürlükten
bağımsız). 🔴 Kalibrasyon zemini **tek bir yapay zekâ görüntüsü** (D-88/D-99): gerçek arenada bariyer kırmızı olmayabilir → dedektör
ateşlemez (fail-safe: hiçbir şey eklemez). "Kırmızı = engel" kuralı HB'yi öldürür; ayrım **şekille**.

### 3.4 Çözünürlük (`CONTRACTS.md` §8) — `imgsz` çıplak yazılmaz, registry'den okunur
v36, kabul kümesinden 12 kare: **512** → IoU 0,906, ROTA 12/12, doğru şerit 8/12; 640 → 11/12, 7/12; 1280 → 3/12. 512 hem ROTA
hem şerit ekseninde en iyi; 768'in IoU üstünlüğü +0,0036 beraberlik bandında. Sözleşme bir kez "640, değiştirme" diyordu; üretim
v27'den beri 512'ydi — sözleşme kendi üretimini yasaklıyordu (D-308). Tarihsel: v17 640'ta 0,861, 960'ta 0,034 (%96 boyuyor).

### 3.5 Karar yolu beyanı (S4'ün çözümü, T151/D-295)
Üretim halka 7 sahibi **`rpi_inference.analyze_path`** (`run_camera` → `KararYayinci`). `costmap_path_finder.rota_bul` **tanısal**:
saha gününde yalnız `kamera_dogrula`, `jetson_fps` ve PC kuru koşuda koşar. Açık kalan boşluk: `rota_bul`'daki `koridor_adaylari`
üç-güzergâh envanteri ve K2/K3 ihlal denetimi üretim yolunda **yok**.

### 3.6 Sık sorulan sayılar
| sabit | değer | nerede |
|---|---|---|
| `HEDEF_BANT_ORANI` / `BANT_TEMAS_MIN_ORANI` | 0,08 / 0,02 | `karar_sozlesmesi` |
| `ROTA_GUVEN_ESIGI` | 0,20 | `karar_sozlesmesi` |
| `ROTA_DARBOGAZ_TAM_ORANI` | 0,035 (otoparktan kalibre, birimsiz — açık ölçüm borcu) | `karar_sozlesmesi` |
| `ZEMIN_KAPLAMA_TAVANI` / kenar | 0,55 / 0,40 | `karar_sozlesmesi` |
| `SERIT_SAYISI` / `KORIDOR_GENISLIK_TAVANI_SERIT` | 3 / 1,0 | `karar_sozlesmesi` |
| `TELEMETRI_IRTIFA_TAZELIK_S` | 0,5 s | `karar_sozlesmesi` |
| `OLCEK_CAPRAZ_BANDI` | 0,25 | `karar_sozlesmesi` |
| `YKS_TESPIT_TAZELIK_S` | 5,0 s | `karar_sozlesmesi` |
| `ROTA_PLAN_MAKS_HUCRE` | 32768 | `karar_sozlesmesi` |
| `INCE_BETON_SERIT_ETKIN` | False (T153 kapalı: v35 15→14 düştü) | `karar_sozlesmesi:870` |

### 3.7 Kod düzeyi: `_analyze_path_cekirdek` sırası (`rpi_inference.py:1515`; ayrıntı `ozet/A_codes.md` §2)
1 `MASKE_YOK` (zemin 0 px) → 2 `ALAN_YETERSIZ` (içerik kutusu boş) → 3 zemin sağlamlık kapısı **ham** maskede → 4 morfoloji: `MORPH_OPEN`
çekirdek `max(3, w//60)`, `MORPH_CLOSE` fiziksel tavanlı (`KAPAMA_AZAMI_M = 0,25 m`, T188: duba sırasının bıraktığı delikleri kapama dolduruyor,
şerit ACIK çıkıyordu) → 5 **engel çıkarma en son** (D-24: kapama 7 px engelin %99'unu geri dolduruyordu) → 6 en büyük bağlı bileşen → 7 K-A →
8 alan ≥ %1 → 9 `distanceTransform`, C-uzayı → 10 HB hedefi (`goruntu` verilirse; T150 ile bağlandı, maliyet "sıfır": şerit 195/256 aynı,
hedef 253/256 doğru pedde) → 11 tanık yol: `_bagli_mi` tam çözünürlükte, `plan_izgarasi` MIN-havuz (muhafazakâr), `astar` 8 komşu +
**köşe kesme yasağı** (çapraz hamle iki ortogonal komşu da serbestse; "bir tekerleği arabaya koyan hata sınıfı budur"), `yol_duzelt`
görüş-hattı + açıklık koruma (kiriş alt yoldan %4'ten dar olamaz; D-154/156/157: 213/260 karede rota tek düz kirişe iniyordu) →
12 örnekleme (`n_waypoints` karara girmez) → 13 `_kenarlar_guvenli` → 14 şerit ve güven **rotanın kendisinden** → 15 `KORIDOR_DEGIL` →
16 `guven = min(1, darboğaz/(0,035·icerik_w)) × kaynak çarpanı` (telemetri 1,00 · arena 0,70 · araç referansı 0,86).
Sonra: yapısal ret ezilmez (ölçek reddi önce), K-B eşikleme, `KararYumusatici` histerezis (`KARAR_HISTEREZIS_KARE = 3`), yayın.
Diğer kod olguları: `--conf` varsayılan **0,30**; `normalize_light` yalnız LAB L ortalaması < 80 ise (gamma + CLAHE 2,5/8×8); letterbox
**pad** (114), crop değil (crop 1024×576'da genişliğin %56'sını atıyordu); `cv2.flip` kaldırıldı (D-349: 16 karenin 15'i sol-sağ takas);
`arac_maskesi.py` DOTA OBB, ad ile eşleşir (`small/large vehicle`), mükerrer IoU 0,5, ölçek için ≥ 3 araç, imgsz tavanı 640;
`test_rota_guvenlik.py` gerçek otopark karelerinde HAM/ENJEKTE iki kiple "rota arabaya değiyor mu" (çıkış 0 yalnız ham ihlal > 0,10 ise:
testin gücü kanıtlanır). Modül sonu **TAHMİNLER** listesi: `TAKIP_HATA_M`, `IKA_GENISLIK_M` (SDF'ten), `LAMBDA/US` ampirik değil — kod
kendi ölçülmemişlerini işaretler.

---

## Jüriye 30 saniyede

> "Maskeden karara dört adım: zemin eksi engel serbest alan; uzaklık dönüşümüyle İKA'nın 1,10 metrelik yarıçapının sığdığı
> yapılandırma uzayı; kareyi alttan üste geçen en büyük koridor üstünde A* tanık yol; rotanın gövdesinin hangi üçte birde
> olduğu şerit kararı. On ayrı ret sebebimiz var, hepsi hakem ekranında ayrı metinle görünür. Ölçeği uçuş kontrolcüsünün
> canlı irtifasından alırız; irtifa yarım saniyeden bayatsa rota üretmeyiz."

## Kendini sına

1. Neden hesaplar tuvale değil içerik dikdörtgenine göre yapılır? Ölçülmüş bir ihlal örneği ver.
2. `mpp` formülü nedir? İrtifa 0,6 s bayatsa ne olur?
3. C-uzayı nedir; `r_gerekli_px` nasıl bulunur?
4. K-A neden iki uç bandı birden ister? Kim buldu?
5. Güven eşiği 0,50 iken ne oldu; 0,20'nin gerçek rolü ne?
6. `darbogaz_serit` yerine `serit_karari` neden? Sayılarla.
7. `KORIDOR_DEGIL` neyi yakalar, neyi kaçırır?
8. `ZEMIN_MASKESI_SUPHELI` kapısı neden modele bağlıdır?
9. HB dedektörü üretimde bağlı mı? Neden?
10. Histerezis `NO_ROUTE`'u geciktirir mi?

<details><summary>Cevaplar</summary>

1. Letterbox dolgusu tuvalde gri alan yaratır; oranlar tuvale göre olursa 16:9 karede şerit sınırları kayar (portrede SAĞ→ORTA), tohum bandı dolguya düşer (18/18 rota yok). 2. `2·h·tan(FOV/2)/W_içerik`; `OLCEK_YOK` → `NO_ROUTE`, rota üretilmez (tazelik 0,5 s). 3. Engelden uzaklığı gövde yarıçapından büyük piksellerin kümesi; `1,10 / mpp`. 4. Kopuk koridorda OpenCV üst parçayı seçip "hedefe temas var" diyordu; Codex ölçtü (D-29). 5. Gerçek yolda 52/52 ret, %100 çekimserlik; 0,20 taban koruyucu: guven=0,0 yayınını ve ~4 px'ten ince gövdeyi engeller, ölçekli kipte fiilen ateşlemez. 6. Darboğaz pikseli rotanın ucunda, güzergâhların birleştiği yerde ölçülüyordu: 6/15; gövde tanımı 15/15, diğer her şey bayt-eş. 7. Arena dışı boş araziyi "koridor" sayan rotaları (darboğaz > 1/3 içerik) yakalar: 5/10; genişliği meşru azaminin altında kalan arena-dışı otopark gibi 4 kareyi kaçırır. 8. Kaplama dağılımı modelin çıktısına göre değişir; v21 için 0,55, v24'te yanlış, v35 ile (0,55, 0,40) yeniden kalibre edildi. 9. Hayır; gerçek iniş pedinde %0 isabet ölçüldü (D-295 §2), bağlansa her kare HEDEF_YOK; insan kararı. 10. Hayır; yalnız şerit değişimi K kare teyit ister, NO_ROUTE anında yayınlanır.
</details>

## Kaynaklar
`CONTRACTS.md` §3–§6, §8, §11.2-EK · `codes/karar_sozlesmesi.py` · `codes/rpi_inference.py` (`analyze_path`) · `codes/costmap_path_finder.py` ·
`results/t155/` · `results/t142/olcum.md` · `results/t163/` · `REVIEW_LOG.md` D-29, D-37/38, D-39, D-283/286, D-296, D-308, D-396.
