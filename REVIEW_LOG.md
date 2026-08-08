# NAVITAS — DENETİM KAYDI

> Anayasa (`CLAUDE.md`) madde 6: *"Hata veya mantık riski görürsen `REVIEW_LOG.md`
> dosyasına ekle."* Bu dosya **kanıt** taşır: çalıştırılan komut + gerçek çıktı.
> Kanıtsız iddia buraya yazılmaz.
>
> Görev karşılıkları: `TASK_QUEUE.md` · Mimari gerekçe: `ARCHITECT_PLAN.md`

---

## Kayıt 2026-08-03 · Codex Faz-2 teslimatlarının çekişmeli denetimi

**Yöntem:** Beş bağımsız denetim kolu (NO_ROUTE zinciri, ölçüm yolu, Jetson, veri
hattı, görsel test) + her kritik bulgu için ayrı **çürütme** ajanı. Çürütme ajanına
"savunma avukatısın, bu iddianın yanlış olduğunu göster, emin değilsen çürüt" talimatı
verildi.

**Kapsam uyarısı — dürüstlük notu:** Denetim **tamamlanamadı**. İki ayrı koşuda
toplam 19 ajandan 19'u oturum limitine takıldı (`session limit · resets 7:50pm`).
Tamamlanan kollar: **noroute, ölçüm, görsel**. Hiç koşamayan kollar:
**Jetson (`export_tensorrt.py`, `jetson_fps.py`, `rpi_yayin.py`)** ve
**veri hattı (`extract_key_frames.py`, `copy_paste_augmentation.py`)**.
Bu iki alan yalnız mimarın kendi doğrulamasından geçti, bağımsız çürütmeden geçmedi.

**Sonuç:** **11 bulgu ayakta kaldı, 0 tanesi çürütüldü.**

---

### K-01 · KRİTİK · Letterbox düzeltmesi commit'e girmemiş, temiz klon çöküyor
`codes/test_accuracy.py:29` · `codes/rpi_inference.py` · Görev **T1**

```
$ git show 5f05e28 --stat
 codes/test_accuracy.py                            | 26 +++++-----
 codes/test_batch.py                               | 20 ++++----
 results/letterbox_olcum_karsilastirma_20260802.md | 34 ++++++++++
 3 files changed, 56 insertions(+), 24 deletions(-)
   → codes/rpi_inference.py commit'te YOK

$ git show HEAD:codes/rpi_inference.py | grep -n "_maskeleri_icerige_kirp"
   → HİÇ eşleşme yok

$ git worktree add --detach <tmp> HEAD
$ cd <tmp>/codes && .../python.exe test_accuracy.py --help
ImportError: cannot import name '_maskeleri_icerige_kirp' from 'rpi_inference'
EXIT=1
$ cd O:/navitas/codes && .../python.exe test_accuracy.py --help
EXIT=0   (çalışma ağacında düzgün)
```

**Çürütme denemesi sonucu:** çürütülemedi. Import satırı korumasız (try/except veya
geç import yok) ve bu betikler ölü kod değil, doğrudan CLI giriş noktaları. Denetim
salt okunurdu; geçici worktree scratchpad'e açılıp silindi, repoda hiçbir dosya
değiştirilmedi.

**Etki:** Depoyu master'dan klonlayan herkes ölçüm yolunu hiç açamıyor. Madde 0.3'ün
düzeltmesi **depoda yok**, yalnız bu makinedeki commit edilmemiş dosyalarda var.

---

### K-02 · KRİTİK · Tek geçici NO_ROUTE, İKA görevini geri dönülmez iptal ediyor
`simulation/scripts/ika_nav.py:319` · Görev **T2**

```python
while time.time() - t0 < timeout:
    no_route = rx.last_no_route          # döngünün İLK işi
    if no_route is not None:
        rx.stop(); rx.link.close()
        return no_route                  # soket kapandı, dönüş yok
```

Kanıt koşusu — sahte İHA önce NO_ROUTE, **2 sn sonra geçerli OPEN_ROUTE**, timeout 8 sn:
```
[IHA] t=0.6s NO_ROUTE gonderildi seq=1
[ika_nav] ✗ İHA NO_ROUTE bildirdi: KAPALI_DAR — İKA güvenli duruşta
[IKA] t=0.9s DONUS: NO_ROUTE KAPALI_DAR
>>> gecici NO_ROUTE gorevi KALICI iptal etti; 2 sn sonra gelen
    gecerli OPEN_ROUTE hic degerlendirilmedi.
```

`IkaReceiver`'ın özellikle koruduğu son geçerli rota (`latest`) bu yolda hiç okunmuyor:
`grep -rn "last_no_route" simulation/` → yalnız `ika_nav.py:319`.

**Etki:** İHA kare kare tarıyor. 1. karede KAPALI_DAR, 5. karede açık yol bulunsa bile
(her ikisi de 900 s / 600 s bütçesinin içinde) İKA hiç hareket etmiyor; kurtarılabilir
bir görev **sıfır puanla** bitiyor.

---

### K-03 · KRİTİK · Güvenlik testi 18/18 karede hiçbir şey ölçmüyor
`codes/test_rota_guvenlik.py:117` · Görev **T3**

Kök neden — letterbox dolgusu tohum bandını yutuyor:
```
ham foto şekli: (900, 1600, 3)
letterbox içerik kutusu: x0=0 y0=196 nw=896 nh=504  → içerik y ∈ [196, 700)
_merkez_tohumu bant yüksekliği pay=71
  ALT bant y ∈ [825, 896) → içerikle kesişiyor mu: False
  ÜST bant y ∈ [  0,  71) → içerikle kesişiyor mu: False
geçilebilir ALT %8 bandında px: 0 / ÜST %8 bandında px: 0
=> A* başlangıç/hedef tohumu BOŞ: True
```
Sonuç: `durum="KAPALI"`, `n_wp=0`, her iki kipte de 18/18. Videolar da 1024×576 (16:9),
aynı dolgu oluşuyor.

**Etki:** Raporlanan "ham ihlal oranı 0,000" ve "enjekte TAM 0" rakamları güvenlik
hakkında **hiçbir bilgi taşımıyor**.

#### T3 kapı düşümü · 2026-08-03 · Codex-1

İçerik kutusuna bağlı tohum düzeltmesinden sonra gerçek veri kapısı, dış yorumlayıcı
ve iki gerçek modelle yeniden çalıştırıldı:

```text
Komut: O:\navitas-local-train\venv\Scripts\python.exe -B codes/test_rota_guvenlik.py --hepsi --adim 24 --imgsz 896 --conf 0.25 --navitas-model O:\navitas\models\navitas_seg_v20_best.pt --coco-model O:\navitas\yolov8m-seg.pt --out O:\navitas\results\rota_guvenlik_t3_gate_20260803_full
Exit: 1
n_kare=280
ihlal_sayisi_ham=0
ihlal_orani_ham=0.0
karar_sayisi_ham=83
tohum_yok_ham=182
karar_sayisi_enjekte=83
tohum_yok_enjekte=182
```

Tohum dolgusu kusuru artık `KAPALI` diye gizlenmiyor ve 83 karede gerçekten rota
üretiliyor; ancak ham rotaların hiçbiri COCO araç maskesini güvenlik yarıçapı içinde
kesmedi. Dolayısıyla zorunlu `ihlal_orani_ham > 0.10` kapısı sağlanmadı: ölçüm bu
veri/model birleşiminde **güçsüz**. Kapı kuralı gereği T3 `READY_FOR_REVIEW`
yapılmadı ve tekrar `[ ]` bırakıldı.

#### T3 asıl 18-kare kapı ve kâhin teşhisi · 2026-08-04 · Codex-1

Özgün `18/18` kanıtının örneklemesi `tests/test_costmap_on_images.py` üzerinden
yeniden kuruldu: 6 ham fotoğraf + dört videonun baş/orta/son üçer karesi. Gerçek
komut exit 1 ile `ham=0/18`, `enjekte=0/18`, `durum=GUCSUZ` üretti; tam konsol
çıktısı T3 altına yapıştırıldı.

DT/kesişim hesabı sentetik temasla ayrıca doğrulandı; yönü doğrudur. Sorun kâhinin
alan uyumsuzluğudur:

```text
280-kare adli dağılım:
  COCO araç maskesi olmayan       : 230/280
  hem COCO maskesi hem rota olan  :  10/280
  mevcut paydayla teorik azami oran: 10/280 = 0.0357 < 0.10

ilk 896x896 foto:
  COCO yolov8m-seg.pt             : 2 araç
  DOTA yolov8m-obb.pt             : 93 small/large vehicle

sabit 18 kare, DOTA OBB salt-okunur prototip:
  ham karar / ihlal / oran        : 6 / 6 / 0.333
  enjekte ihlal                   : 0
```

COCO güven eşiğini `0.35`ten `0.02`ye indirmek 18 karede yine sıfır kesişim verdi;
eşik ayarı çözüm değildir. Üretim algı hattı `simulation/scripts/iha_haritala.py`
içinde aynı DOTA OBB modelini ve `small vehicle` / `large vehicle` poligonlarını
zaten kullanıyor. OBB'ye geçmek testi oyunlaştırmadan kapıyı anlamlı kılıyor ve T4'ün
`0 enjekte karar` kusurunu görünür bırakıyor.

Ancak `ARCHITECT_PLAN.md:156` açıkça **COCO-kâhin** diyor ve T3'ün Yap satırı yalnız
tohum düzeltmesini kapsıyor. DOTA OBB'ye geçiş gerekli olsa da semantik bir test-harness
ve mimari değişikliktir; Codex bunu sessizce yapmadı. Seçenekler:

1. Mimar/insan DOTA OBB kâhinini onaylar; sabit 18-kare manifesti, tekil OBB kısa
   ekseninden ölçek, `--arac-model` CLI'si ve eski `--coco-model` uyumluluk takma adı
   ile uygulanır.
2. COCO şartı korunur; hava görüntüsüne uygun ayrı bir segmentasyon ağırlığı sağlanır
   veya `%10` kapısı mimar tarafından yeniden tanımlanır.

Bu karar verilene kadar zorunlu kapı mevcut planla matematiksel olarak erişilemez;
T3 tekrar `[ ]` bırakıldı.

#### T3 karar ve çözüm · 2026-08-04

İnsan, üretim-uyumlu DOTA OBB kâhinine geçişi onayladı. `ARCHITECT_PLAN.md` modül
tablosu güncellendi; test yolu DOTA `small vehicle` / `large vehicle` poligonlarını
tekil maskelere çeviriyor, ölçeği tekil kısa eksenlerden çıkarıyor ve eski COCO-seg
sonuç biçimini geriye uyumlu tutuyor. Kâhin maskesinin ham planlayıcı engeline
sızmadığı regresyonla kilitlendi.

Nihai sabit kapı: `18` kare, ham `4/18 = 0.2222`, enjekte ihlal `0`, exit `0`.
Zorunlu `ham > 0.10` şartı sağlandı. Enjekte kipte karar sayısının `0/18` olması
ayrıca doğrulandı; bu T3'ün ham güç kapısını bozmaz ve sıradaki **T4** kusurunun
beklenen yeniden üretimidir. Evrensel sentetik kapı son kodda `15/15` geçti.

---

### K-04 · KRİTİK · Geçme ölçütü çekimserliği denetlemiyor
`tests/test_costmap_on_images.py:238` · Görev **T4**

```python
enj_tam_sifir = enj_ihlal == 0
ham_guclu     = ham_oran > 0.10
durum = "GECTI" if enj_tam_sifir and ham_guclu else (...)
#   enjekte_karar_var HİÇBİR YERDE ölçüte girmiyor
```
Sahte `bir_kare_isle` ile ölçüldü (ham kipte 2/6 ihlal, enjekte kipte `karar_var=False`):
```
çıkış kodu: 0
ozet: {"ham_ihlal_orani": 0.3333, "enjekte_ihlal": 0,
       "enjekte_kesisim_..._tam_sifir": true, "ham_test_guclu": true, "durum": "GECTI"}
enjekte kipte karar üretilen kare sayısı: 0 / 6
```

**Etki:** Tek bir geometri ölçümü yapılmamışken "GEÇTİ" ilan edilip 0 ile çıkılıyor.
K-03 ile birleşince bugünkü gerçek davranış tam olarak budur.

#### T4 çözüm · 2026-08-04 · Codex-1

Özet hesabı saf `guvenlik_ozeti()` fonksiyonuna ayrıldı ve durum önceliği
`GEOMETRI_HATASI → OLCUM_YOK → GUCSUZ → GECTI` olarak kilitlendi. Enjekte karar
sayısı `0` ise çekimserlik `1.0`, durum `OLCUM_YOK` ve süreç kodu `1` oluyor.
Gerçek 18-kare DOTA koşusu ham `4/18` ihlal üretirken enjekte karar `0/18` kaldı;
betik beklenen biçimde `[OLCUM_YOK]` yazıp exit `1` verdi. Hedefli durum matrisi
testleri `4/4`, evrensel sentetik kapı `15/15` geçti.

---

### K-05 · ÖNEMLİ · Şerit sınırları dolgulu tuvale göre — portre karede yanlış güzergâh
`codes/rpi_inference.py:151` · Görev **T5**

```python
open_path = 1 if cx < w / 3 else (2 if cx < 2 * w / 3 else 3)
#  w = trav_mask.shape[1] = KARE TUVAL genişliği, içerik genişliği DEĞİL
```
```
giriş 576x1024 → tuval 1024x1024, içerik x=[224,800)
tuval şerit sınırları        : 341, 683
içerik şerit sınırları (doğru): 416, 608
tuval sınırları içerik oranında: 0.204, 0.796   (olması gereken 0.333 / 0.667)
koridor içerik-x fraksiyonu [0.7, 0.8] => DOĞRU CEVAP 3 (SAĞ)
  üretim rpi_inference.analyze_path → 2  (güven 0.948)   ← YANLIŞ
  aynı koridor DOLGUSUZ maskede     → 3                  ← doğru
```
Aynı kusur ölçüm kopyasında da var: `codes/test_accuracy.py:110-114`.

**Etki:** Şartname §5.3.2 / §6.2 — **yanlış güzergâh tespiti 0 puan.** Yatay (w ≥ h)
karelerde yatay dolgu olmadığı için tetiklenmiyor; dikey/portre kaynakta tetikleniyor.

#### T5 çözüm · 2026-08-04 · Codex-1

`analyze_path` geriye uyumlu, keyword-only `icerik=(x0,y0,w,h)` metadata'sı aldı.
Şerit ve güven sınırları artık kare tuvalden değil `x0 + w/3` ile
`x0 + 2w/3` noktalarından hesaplanıyor. RPi image/video/camera yolları `_preprocess`
metadata'sını geçiriyor; zaten kırpılmış `iha_perceive` ve dolgusuz YKS yolu tam
maske varsayımını koruyor. 576×1024 portre regresyonunda aynı koridor eski hesapla
`2`, içerik hesabıyla `3` ve güven `1.0` verdi. Hedefli testler `4/4`, evrensel
sentetik kapı `15/15` geçti.

---

### K-06 · ÖNEMLİ · Sürüş sırasında gelen NO_ROUTE tamamen yok sayılıyor
`simulation/scripts/ika_nav.py:232` · Görev **T6**

`navigate()` döngüsü yalnız `link_ok`'u sorguluyor; `navigate` / `navigate_route`
imzalarında NO_ROUTE kanalı yok.

```
[ika_nav] ── Waypoint 2/5: (-20.0, -20.5)
[IHA] t=2.4s NO_ROUTE gonderildi
[ika_nav]   ✓ Ulaşıldı ... (3, 4, 5. waypoint'ler de tamamlandı)
[ika_nav] ══ HEDEF BÖLGEYE (HB) ULAŞILDI! ══
[IKA] rx.last_no_route: KAPALI_DAR
[IKA] NO_ROUTE'tan SONRA gonderilen hareket komutu sayisi: 49
>>> NO_ROUTE geldigi halde arac hedefe ULASTI mi: True
```

**Etki:** YKS hakem ekranı "ROTA YOK — İKA GÜVENLİ DURUŞTA" kırmızı bandını
gösterirken araç hiç yavaşlamadan geçersiz rotayı sürüyor. Operatör ve hakem gerçek
dışı bilgi görüyor; araç molozun/kapalı koridorun içine giriyor (§2.2.6 yapısal
bütünlük şartı).

**Çözüm doğrulaması (2026-08-04 · Codex-1):** `navigate` / `navigate_route`,
kilitli karar snapshot'ına bağlı `rota_gecerli` kapısı aldı. NO_ROUTE sırasında her
kontrol turu `send_vel(0, 0)` ile güvenli duruşta kalıyor; geçerli OPEN_ROUTE ile
aynı waypoint'ten devam ediyor. Son bool kontrolü ile nonzero motor çıkışı arasındaki
yarış, `IkaReceiver.run_if_route_valid` altında atomik sıralandı. Gerçek loopback UDP
testinde NO_ROUTE bu dar aralığa ACK'li enjekte edildi: etkin 3 komutta nonzero `0`,
toparlanma sonrasında nonzero `1`; hedefli kapı `3/3`, T2 regresyonu `4/4`, haberleşme
testi exit `0`, evrensel sentetik kapı `15/15` geçti. Gecikmiş kararların oturumlar
arası sıralanması bu çözümün kapsamı değildir ve **K-12** olarak açık kalır.

---

### K-07 · ÖNEMLİ · `min_area_ratio` dolgulu tuval alanına göre — regresyon
`codes/rpi_inference.py:138` · Görev **T7**

```python
if clean.sum() < min_area_ratio * h * w:   # h, w = KARE TUVAL boyutları
```
```
1024x576 üretim çözünürlüğü:
  koridor alanı = 9009 px = gerçek görüntünün %1.53'ü, tuvalin %0.86'sı
  üretim analyze_path → None   (eşik gerçek görüntüye göre olsaydı karar üretmeliydi)
oran: side²/(w·h) = 1024²/589824 = 1.778  →  fiili eşik %1.78
```
Letterbox öncesi tuval == içerik olduğu için eşik gerçekten %1 idi. Bu bir **regresyon**.

**Etki:** Yüksek irtifada, dar/uzak güzergâhta veya kısmi bulut gölgesinde ana koridor
gerçek görüntünün %1,0–%1,78'ini kapladığında İHA "tespit yok" diyor ve İKA'ya rota
gönderilmiyor. §6.4 gereği veri akışının kesilmesi uçuşu geçersiz kılabilir.

**Çözüm doğrulaması (2026-08-04 · Codex-1):** `analyze_path`, letterbox içerik
kutusunun kırpılmış genişlik ve yüksekliğini okuyup alan eşiğini
`min_area_ratio * icerik_w * icerik_h` ile hesaplıyor; metadata yoksa eski tam-maske
davranışı korunuyor, sıfır içerik boyutu güvenli `None` dönüyor. 576×1024 içeriğin
`%1,5001`'ini kaplayan deterministik koridor eski tuval hesabıyla `None`, yeni hesapla
sağ karar `3` üretti. Hedefli testler `5/5`, CLI smoke exit `0`, evrensel sentetik
kapı `15/15` geçti.

---

### K-08 · ÖNEMLİ · Iraksak `analyze_path` kopyası ölçüm yolunu geçersiz kılıyor
`codes/test_accuracy.py:83` · Görev **T8**

```
test_accuracy.analyze_path is rpi_inference.analyze_path ? False
yerel kopya: 58 satır | 'h * 0.4' içeriyor: True | connectedComponents içeriyor: False

SENARYO1 (orta koridor + sol üst kopuk gürültü blobu):
  üretim → 2 (güven 1.0)      ölçüm → 1 (güven 0.646)
SENARYO2 (sadece küçük gürültü, alan ~%0.3):
  üretim → None               ölçüm → 1 (güven 1.0)
SENARYO3 (üst-sol geniş kol + üst-sağ ince kol, tek bileşen):
  üretim → 2 (0.085)          ölçüm → 3 (0.411)
```
Ayrışma noktaları: ölçüm kopyası sabit üst-%40 bandı + üç-bölge piksel argmax; üretim
en-büyük-bağlı-bileşen + `min_area_ratio` kapısı + üst-%30 x-centroid.

**Etki:** `accuracy_results.json` ve GENEL DOĞRULUK yüzdesi **sevk edilen karar
kuralını ölçmüyor.** Küçük gürültü içeren bir karede üretim "tespit yok" derken ölçüm
"sol" diyor ve etiket "sol" ise bunu **doğru** sayıyor — gerçekte araç hiç rota almazdı.
K-01 görüş alanını düzeltti; ölçülen kural hâlâ yanlış, dolayısıyla sayılar hâlâ geçersiz.

**Çözüm doğrulaması (2026-08-04 · Codex-1):** `codes/test_accuracy.py` içindeki
yerel karar kopyası silindi; ölçüm yolu `rpi_inference.analyze_path` nesnesini
doğrudan kullanıyor ve letterbox içerik kutusunu iletiyor. Kimlik kapısı `True`,
hedefli testler `3/3`, CLI smoke exit `0`, evrensel sentetik kapı `15/15` geçti.
Üç deterministik ayrışma sahnesinde üretim sözleşmesiyle uyum `0/3`'ten `3/3`'e
çıktı. Altı etiketsiz gerçek karede karar `2/6` kez değişti; bu sonuç doğruluk
olarak sunulmadı. Etiketli P001–P030 görselleri çalışma alanında `0/30` olduğu ve
eski `accuracy_results.json` bulunmadığı için gerçek etiketli doğruluk
**BULUNAMADI**; ayrıntı `results/analyze_path_olcum_karsilastirma_20260804.md`.

---

### K-09 · ÖNEMLİ · `mpp=None` olduğunda ihlal eşiği 27,9 px'ten 1,10 px'e çöküyor
`codes/test_rota_guvenlik.py:170` · Görev **T9**

```python
mpp = mpp_arac_maskesinden([m for m in maskeler_coco.values() if m.any()])
olc = olcek_px(mpp)
sonuc_ham = _rota_uret({0: maskeler_nav[0], 1: maskeler_nav[1]}, mpp)
```
Kâhinden türetilen ölçek **ham kipte de planlayıcıya geçiyor** — "kâhin planlayıcıya
verilmez" iddiası maske için doğru, **ölçek için değil**.

```
ozet.json (18 kare):  14/18 karede mpp=None → r_gerekli_px = 1.10
                       kalan 4 karede 17.72 – 27.88 px
costmap_path_finder.olcek_px(None) → m=1.0, r_gerekli_px = 1.10
```

**Etki:** 14 karede rota bir aracın 2 piksel yanından geçse bile "ihlal yok" sayılıyor;
aynı sahne kâhin aracı görseydi eşik ~25× büyük olacaktı. İhlal oranı sistematik olarak
düşük raporlanıyor ve "ENJEKTE TAM 0" sonucu **ölçek gürültüsüyle** üretilmiş oluyor.

**Çözüm doğrulaması (2026-08-04 · Codex-1):** Görevdeki ölçüm-dışı bırakma
seçeneği uygulandı. `mpp=None` gerçek-görüntü karesi `_rota_uret`'e girmiyor;
`OLCEK_YOK`, `ihlal=null`, `r_gerekli_px=null` üretiyor. İhlal, karar,
çekimserlik ve `TOHUM_YOK` sayaçlarının tamamı yalnız `mpp is not None`
altkümesinden hesaplanıyor. Sıfır ölçek kapsaması `OLCUM_YOK`, kısmi kapsama
`KISMI_OLCUM` ve ikisi de exit `1`; tam başarı yalnız `TAM_OLCUM` ile mümkün.
Gerçek DOTA tek-kare probunda `mpp=None` üretici beklendiği gibi exit `1` verdi;
yazılan `ozet.json` için null/sayaç/oran kapısı exit `0` geçti. Hedefli ölçek
testleri `3/3`, downstream durum testleri `7/7`, tüm unittest keşfi `33/33` ve
evrensel sentetik kapı `15/15` geçti. `mpp` mevcut olduğunda DOTA tahmininin iki
kipte ortak plan ölçeği olması bu seçenekle değişmedi; dış irtifa/FOV ölçeği T14
profil çalışmasının kapsamındadır.

---

### K-10 · KÜÇÜK · Erken `return` — rapor ölü kod, çökmüş thread'de yanlış başarı
`simulation/scripts/navitas_sim.py:169` · Görev **T10**

```
== main() gövdesinin son ifadeleri (AST) ==
satır 169  Return
satır 170  If    <-- ULAŞILMAZ    if "iha" in results:
satır 172  If    <-- ULAŞILMAZ    if "ika" in results:
satır 174  Expr  <-- ULAŞILMAZ    print("═"*50)

== YANLIŞ BAŞARI ==
her iki thread de çökse     results={}                  exit=0  ← BAŞARI
ika çökse, iha başarılı     results={'iha': True}       exit=0  ← BAŞARI
ika başarısız dönse         results={'iha':1,'ika':0}   exit=1
```
Gerçek koşu (`--ika-only --no-wait --route-timeout 3`): gerçek exit 1, ama
`İKA görevi: ✗ BAŞARISIZ` satırı **hiç basılmıyor** — operatör boş bir
"GÖREV SONUCU" başlığı görüyor.

**Kök neden:** `all(...)` ifadesi `results` içinde **var olan** anahtarlar üzerinde
dönüyor. Thread bir istisna fırlatırsa `results`'a hiç yazmaz, `all([])` boş küme
üzerinde `True` döner.

**Çözüm doğrulaması (2026-08-04 · Codex-1):** Beklenen görev listesi argümanlardan
thread başlamadan kurulup sonuçları `False` ile önceden dolduruluyor. Worker
istisnaları görünür hata ve başarısız sonuç olarak kaydediliyor; rapor bütün
beklenen görevleri yazdıktan sonra dönüş yapılıyor. Gerçek `ika-nav` thread'inde
`RuntimeError` kapısı `GÖREV SONUCU` ve `İKA görevi: ✗ BAŞARISIZ` satırlarını
basıp ana sonuç `1` üretti. Hedef testler `4/4`, tüm unittest keşfi `37/37`, CLI
smoke exit `0` ve evrensel sentetik kapı `15/15` geçti. Bağımsız `SystemExit(7)`
ve Ctrl+C probları da nonzero + görünür rapor verdi.

---

### K-11 · KÜÇÜK · `--no-route` adres bayrağı olmadan `TypeError` ile çöküyor
`comms/iha_sender.py:87` · Görev **T11**

```
$ cd comms && python iha_sender.py --no-route KAPALI_DAR --detay test
[İHA] ROTA YOK gönderiliyor: KAPALI_DAR · test
Traceback (most recent call last):
  File "O:\navitas\comms\iha_sender.py", line 91, in _tekrarli_gonder
    self.link.send(data, peer)
  File "O:\navitas\comms\link.py", line 29, in send
    self.sock.sendto(data, peer or self.peer)
TypeError: sendto(): AF_INET address must be tuple, not NoneType
```
Argparse doğrulaması `--no-route` için `--ika` / `--yks` / `--serial` zorunluluğunu
kontrol etmiyor (`iha_sender.py:160-176`). Aynı çökme `--road` yolunda da var;
`--no-route` bayrağı bu yolu yeni bir girişten erişilebilir kıldı.

**Etki:** Sahada operatör adres bayrağını unutursa, "ROTA YOK gönderiliyor" satırı
zaten basılmış olduğu için gönderildiğini sanabilir.

**Çözüm doğrulaması (2026-08-04 · Codex-1):** `main()`, payload doğrulamasından
sonra fakat link kurulmadan ve gönderim mesajı basılmadan önce en az bir
`--serial` / `--ika` / `--yks` hedefini zorunlu kılıyor. Görevdeki birebir
`--no-route KAPALI_DAR --detay test` komutu anlaşılır argparse hatasıyla exit `2`
verdi; traceback ve sahte gönderim satırı yok. Hedefli subprocess testleri `2/2`,
`comms/test_comms.py` exit `0`, tüm unittest keşfi `39/39` ve evrensel sentetik
kapı `15/15` geçti.

---

### K-12 · ÖNEMLİ · Gecikmiş karar mesajı daha yeni güvenlik kararını ezebiliyor
`comms/ika_receiver.py:60-74` · Görev henüz kuyruklanmadı

`decision_generation` yalnız yerel varış sayacıdır; mesajın `seq` tazeliği veya
tekrarı denetlenmiyor. UDP tekrar/sıra değişiminde eski bir `OPEN_ROUTE`, daha yeni
`NO_ROUTE` sonrasında gelirse `last_no_route` temizleniyor:

```
NO_ROUTE(seq=20) -> OPEN_ROUTE(seq=19)
{'latest_seq': 19, 'no_route': None, 'generation': 2}
```

**Etki:** İKA, yeni güvenli duruş kararından sonra gecikmiş eski rotayı güncel sanıp
hareket kapısını yeniden açabilir. Salt `seq < last_seq` reddi de gönderici yeniden
başladığında sayaç 1'e dönebildiği için yeterli değildir; protokol oturum kimliği
veya açık bir yeniden-senkronizasyon kuralı gerekir. T6 uygulanırken aktif rota
geçerliliği geri çağrımına ek olarak bu karar sıralaması ele alınmalıdır.

---

### K-13 · KRİTİK · YKS'nin `IKA_GO` komutu İKA sürüş kapısına bağlı değildi
`comms/ika_receiver.py`, `simulation/scripts/ika_nav.py` · Görev **T12**

**Çözüm doğrulaması (2026-08-04 · Codex-1):** Alıcı yalnız
`CMD + IKA_GO + hedef=ika` birleşimini kalıcı manuel izin olarak kurup ACK'liyor;
bilinmeyen ve yanlış hedefli komutlar kapıyı açmıyor. Üretim simülasyonu geçerli
OPEN_ROUTE sonrasında bu izni sıfır hızda bekliyor. Atomik motor kapısı da manuel
izni her sıfır-olmayan komuttan hemen önce rota kararıyla birlikte denetliyor.
Gerçek YKS constructor'ı ile pinlenen hedef üzerinden loopback UDP kapısında IKA_GO
öncesi sıfır-olmayan motor komutu `0`, doğru komut sonrasında `1` ve aynı `seq`
için ACK düğümü `ika` oldu. Adres yokluğu, pin koruması, bozuk/yanlış komut,
ACK taşıyıcı hatası ve çelişkili CLI kipleri hedefli testlere bağlandı. Hedef test
`9/9`, NO_ROUTE regresyonları `7/7`, haberleşme testi exit `0`, tüm unittest keşfi
`48/48` ve evrensel sentetik kapı `15/15` geçti.

**Ara kapı düşümü (2026-08-04 · Codex-1, task açık bırakıldı):** Üretim
YKS→UDP→İKA testi geçtiği halde hedefli keşif `exit 1` verdi. Windows alt süreci
argparse stderr'ini CP1254 yazdı; test bunu zorla UTF-8 çözdüğü için Türkçe metin
`kullan�lamaz` oldu ve aşağıdaki assertion düştü:

```text
FAIL: test_serial_ile_udp_ika_adresi_birlikte_reddedilir
AssertionError: '--serial ile --ika birlikte kullanılamaz' not found in
'yks_gui.py: error: --serial ile --ika birlikte kullan�lamaz\n'
Ran 8 tests in 0.379s
FAILED (failures=1)
EXIT_CODE=1
```

Bu koşu geçiş kanıtı sayılmadı. Alt sürecin kodlaması açıkça UTF-8 yapılmadan kapı
yeniden değerlendirilmeyecek.

**Yeniden koşu sonucu:** Alt sürece `PYTHONIOENCODING=utf-8` verilerek kodlama
varsayımı kaldırıldı; aynı test dahil hedefli keşif `9/9`, `EXIT_CODE=0` geçti.

---

### K-14 · KRİTİK · İKA sürüş kapısında İHA iniş kanıtı yoktu
`comms/protocol.py`, `comms/ika_receiver.py`, `simulation/scripts/navitas_sim.py` · Görev **T13**

**Çözüm doğrulaması (2026-08-04 · Codex-1):** Protokole ayrı, ACK'li
`IHA_LANDED` olayı eklendi. İKA'nın kalıcı sürüş izni artık geçerli OPEN_ROUTE,
YKS'den doğru hedefli `IKA_GO` ve İHA'dan doğrulanmış `IHA_LANDED` koşullarının
hepsini gerektiriyor; atomik sıfır-olmayan motor çıkışı da aynı kapıyı denetliyor.
İki izin geliş sırasından bağımsız, fakat ilk yerel alınma zamanları ortak mutlak
son tarih içinde değilse kapı fail-closed kalıyor. İHA yayıncısı İKA görevi bitene
dek heartbeat sürdürüyor; ikincil YKS ACK'i eksikse canlılığı korurken görev sonucunu
yanlışlıkla başarılı yapmıyor.

Gerçek loopback UDP kapısında `IKA_GO` sonrası, iniş sinyali öncesi sıfır-olmayan
motor komutu `0`; ACK'li `IHA_LANDED` sonrası `1` oldu. Deadline-sonrası iki latch
yarışında `navigate_calls=0`. Hedef test `10/10`, tüm unittest keşfi `58/58`,
haberleşme regresyonu exit `0` ve evrensel sentetik kapı `15/15` geçti.

**Simülasyon sınırı:** Gazebo modeli statik ve uçuş yolu inişi son `z=0` pose yayın
komutunun exit `0` olmasıyla tamamlanmış sayıyor. Bu, fiziksel temas sensörü/readback
kanıtı değildir; kayıtta yalnız simülasyon uçuş endpoint'inin başarıyla yayımlandığı
iddia edilir. Gerçek temas doğrulaması donanım/sensör entegrasyonu kapsamındadır.

---

## Doğrulanan davranışlar (çürütme denemesinden geçti, sorun YOK)

Bunlar denetimde **çalıştırılarak** doğrulandı; kayda geçiyor ki tekrar denetlenmesin:

- `protocol.rota_yok()` encode/decode ve parçalı `FrameReader` beslemesiyle tam tur
  dönüyor; boş/boşluk sebep reddediliyor; UTF-8 Türkçe bozulmuyor.
- `open_route()`'a **dokunulmamış** — `road` 1-3 dışında hâlâ `ValueError`.
- Gerçek localhost UDP çiftinde: NO_ROUTE geldiğinde `IkaReceiver.latest` **eski
  geçerli rotayı** tutmaya devam ediyor; `last_no_route` ayrı alana yazılıyor; yeni
  OPEN_ROUTE `last_no_route`'u temizliyor. Doğru `seq`'e ACK dönüyor.
- **Geriye uyumluluk:** HEAD sürümü (rota_yok'suz protocol + eski receiver) NO_ROUTE
  görünce çökmüyor, dinleme thread'i hayatta kalıyor, önbelleği bozulmuyor.
- `yks_gui.py` gerçek Tk penceresi + gerçek UDP ile: kırmızı **"ROTA YOK"** bandı,
  otomatik ACK, sayaç artışı, onay butonu devre dışı, eski yeşil rota çizgisi kalkıyor.
- `comms/test_comms.py` NO_ROUTE bölümüyle birlikte **geçiyor**.
- `_preprocess` gerçekten letterbox: 1024×576 ve 576×1024 girdilerde kenar işaretleri
  piksel düzeyinde korunuyor; eski merkezi crop aynı işaretleri **tamamen yok ediyordu**.
- `_maskeleri_icerige_kirp` dolgu bölgesini tam sıfırlıyor (3 farklı en-boy oranında sayıldı).
- `test_batch.py:117-119` yüzde paydası (`icerik[2]*icerik[3]`) **doğru** — kare, 16:9,
  9:16 ve 2000×200'de bile %100'ü aşmıyor.
- `get_masks` tekilleştirmesi davranışı **değiştirmedi** — eski iki kopyayla 8 rastgele
  denemede birebir aynı çıktı, toplam fark 0.
- Üç bindirmeli ekran görüntüsü (`2026-08-02 at 14.53.52*`) **hiçbir modele
  verilmiyor** — `YOLO.predict` yamalanıp beslenen her tuvalin md5'i kaydedildi,
  kesişim boş küme.
- COCO araç **maskesi** planlayıcıya sızmıyor — ham kipte class-1 maskesi navitas
  engel maskesiyle bit-birebir aynı (araçtan gelen fazla piksel = 0). *(Ölçek için
  aynısı geçerli değil — bkz. K-09.)*
- `_min_aciklik_araca_px` waypoint'ler **arasındaki** segmentleri de rasterize ediyor
  (`cv2.polylines`); iki waypoint arasında kalan araç kaçırılmıyor.

---

## Harness mantık riskleri (`auto_orchestrator.py`)

### H-R1 · `[HUMAN_COMPLETED]` koruması hiçbir zaman eşleşmiyor
`auto_orchestrator.py:31`

```python
if "[REQUIRES_HUMAN:" in line and "[HUMAN_COMPLETED]" not in line:
```
Yazılan biçim `[HUMAN_COMPLETED: <metin>]` — iki nokta üst üste içeriyor. Aranan
literal `"[HUMAN_COMPLETED]"` (iki nokta yok) dosyada **hiçbir zaman oluşmuyor**.

**Pratik etki: yok.** Değiştirme sonrası satırda `[REQUIRES_HUMAN:` de kalmadığı için
birinci koşul zaten `False` oluyor ve yeniden tetiklenmiyor. Yine de koruma amacını
yerine getirmiyor; biri ileride ilk koşulu gevşetirse sessizce sonsuz döngü olur.

### H-R2 · İlk taramada tüm manuel görevler için sırayla bloke oluyor
`auto_orchestrator.py:30-41`

Döngü dosyadaki **her** `[REQUIRES_HUMAN:` satırı için `trigger_human_alert()`
çağırıyor ve bu `input()`'ta bloke oluyor. Yani orkestratör açılır açılmaz altı manuel
görevi peş peşe soruyor; bağımlılık sırasını gözetmiyor ve tüm yazılım otomasyonunu
manuel işin arkasına diziyor.

**Azaltım (uygulandı):** `TASK_QUEUE.md` FAZ 0 kalemleri gerçek bağımlılık sırasına
göre yazıldı (en sıkışık teslim tarihi en üstte). **Not:** Codex bu satırları zaten
almıyor (`.codexrules` madde 2), dolayısıyla yazılım kuyruğu manuel işi beklemek
zorunda değil — yalnız orkestratör süreci bekliyor.

### H-R4 · TIKAYICI · Orkestratör Türkçe Windows'ta çıktı yönlendirilince çöküyor
`auto_orchestrator.py:9, 11, 12, 13, 48` · Görev **T0**

Gerçek alt süreçle, çıktı boruya yönlendirilerek ölçüldü:

```
--- varsayilan (kod sayfasi) ---
    donus kodu : 1   tamamlandi mi: False
      File ".../encodings/cp1254.py", line 19, in encode
        return codecs.charmap_encode(input, self.errors, encoding_table)[0]
    UnicodeEncodeError: 'charmap' codec can't encode characters in position 0-2

--- PYTHONIOENCODING=utf-8 ---
    donus kodu : 0   tamamlandi mi: True
```

**Kaynak ayrıştırıldı** — suç harness'in kendi emojisinde, görev metinlerinde değil:

```
1) auto_orchestrator.py basim satirlari, cp1254:
   [FAIL] satir  9: '🚨🚨🚨'   [FAIL] satir 11: '👉'
   [FAIL] satir 12: '👉'      [FAIL] satir 13: '👉'
   [FAIL] satir 48: '🤖'

2) TASK_QUEUE.md icindeki 6 gorev metni, cp1254:
   H1..H6 -> hepsi OK, hepsi saf ASCII
   -> gorev metinlerinde cp1254 hatasi: 0
```

**Etki:** Çıktı bir dosyaya veya boruya yönlendirildiğinde (günlükleme, süpervizör
altında koşma) orkestratör ilk manuel görevde çöküyor. Çökerse hiçbir manuel görev
yüzeye çıkmıyor ve çok-AI akışının insan bacağı hiç işlemiyor. Etkileşimli konsolda
Windows farklı bir yazma yolu kullandığı için sorun görünmeyebilir — bu, hatanın
gizli kalmasını sağlıyor.

**Çözüm:** `simulation/scripts/navitas_sim.py:22-26`'da bu kalıp **zaten var**:
```python
for _akim in (sys.stdout, sys.stderr):
    try:
        _akim.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass
```
Yeniden yazılmayacak, kopyalanacak.

### H-R3 · Etiket metni `]` karakteri içeremez
`auto_orchestrator.py:33` — `end = line.find("]", start)` ilk `]`'de kesiyor.
`TASK_QUEUE.md`'deki tüm manuel görev etiketleri buna göre yazıldı ve ayrıştırıcıya
karşı test edildi (aşağıya bkz.).

**İlgili tuzak — yakalandı ve düzeltildi:** Ayrıştırıcı düz metni görevden ayırt
edemiyor. `TASK_QUEUE.md`'nin ilk sürümünde "Kullanım kuralları" bölümü, kuralı
anlatmak için etiketi **literal olarak** içeriyordu; orkestratör bunu 7. bir görev
sanıp operatöre sordu (`beklenen 6, yakalanan 7`). Belgeleme metni etiketi düz yazıda
tekrar etmeyecek şekilde yeniden yazıldı. **Kural:** bu etiket `TASK_QUEUE.md` içinde
yalnız gerçek görev satırlarında geçebilir — örnek, açıklama veya şablon olarak asla.

---

## Anayasa madde 4 uyum taraması · 2026-08-03

| Kütüphane | Sonuç |
|---|---|
| `scipy` | **0 eşleşme** |
| `skimage` / `scikit-image` | **0 eşleşme** |
| `sklearn` | **0 eşleşme** |
| `networkx` | **0 eşleşme** |
| `torch` | yalnız `models/*_ncnn_model/model_ncnn.py` (Ultralytics üretimi) + `scripts/jetson_fps.py:132` (fonksiyon içi tembel import) |
| `matplotlib` | yalnız `simulation/scripts/harita_onizleme.py` (fonksiyon içi tembel import) |

**İHLAL YOK.** `codes/costmap_path_finder.py` bağımlılıkları: `heapq`, `cv2`, `numpy`,
`logging`.

---

## Kayıt 2026-08-04 · Strateji araştırması sırasında bulunan kusurlar

**Bağlam:** A/B/C görüntü işleme stratejisi araştırması (`RESEARCH_NOTES.md`) sırasında,
kararın kendisinden daha acil iki kusur ölçüldü.

### S1 · TIKAYICI · Veri üreteci araçları ZEMİN olarak etiketliyor
`scripts/copy_paste_augmentation.py:37,151,340` · Görev **S1**

Gerçek kod:
```python
COCO_ARAC_SINIFLARI = (2, 3, 5, 7)  # car, motorcycle, bus, truck        # :37
maskeler = get_masks(sonuc, yukseklik, genislik,
                     sinif_idler=COCO_ARAC_SINIFLARI)                    # :151
ayrac.add_argument("--arac-model", type=Path,
                   default=KOK / "yolov8m-seg.pt")                       # :340
```

Etiket yazımı (`:295-300`):
```python
satirlar = ["0 0.000000 0.000000 1.000000 0.000000 1.000000 1.000000 0.000000 1.000000"]
satirlar.extend(poligon_satirlari(1, engel, min_alan))
satirlar.extend(poligon_satirlari(2, hedef, min_alan))
```
**Sınıf 0 (zemin) daima TAM KARE dikdörtgen.** `engel` maskesine girmeyen her nesne
yalnız bu dikdörtgenin altında kalır -> **"zemin" etiketi alir**.

Kahin olcumu (T3 teshisinden, ayni hava fotografi 896x896):
```text
COCO yolov8m-seg.pt : 2 arac
DOTA yolov8m-obb.pt : 93 small/large vehicle
COCO conf 0.35 -> 0.02 indirildi: 18 karede yine SIFIR kesisim
```

**Etki:** Uretilen egitim verisinde araclarin ~%98'i **"surulebilir zemin" olarak
etiketleniyor.** Bu, v16'yi %2,7'den **%31,6**'ya cokerten *etiketsiz engel* hatasinin
birebir aynisi ve sentetik uretecin en kritik tasarim kuralinin ihlali
(`51_sentetik_arena.py`: *"Moloz her zaman blocked seridin icindedir -> ETIKETSIZ MOLOZ YOK."*).

**Sonuc:** S1 duzeltilmeden yeni egitim kosmak GPU-gun israfidir (risk R7).

### S2 · KRITIK · Sinif-id catismasi canli (K-2 riski gerceklesti)
`scripts/copy_paste_augmentation.py:318-321` <-> `simulation/scripts/iha_haritala.py:300,336`

```python
# copy_paste_augmentation.py:318-321  -> 2 = HEDEF
icerik = "...names:\n  0: zemin\n  1: engel\n  2: hedef\n"

# iha_haritala.py:300                 -> 2 = ARAC
costmap_maskeleri = {0: masks[0], 1: masks[1], 2: arac}
# iha_haritala.py:336
plan_sonucu = rota_bul(costmap_maskeleri, ..., engel_sinif_idler=(1, 2), ...)
```

**Etki:** 3 sinifli veriyle egitilmis bir model `iha_haritala` yoluna verilirse
**H brandasi ENGEL sayilir** -> IKA hedefe hicbir zaman ulasamaz -> `P_gorev = 0`
(sartname Tablo 6: 600 puan, K_zorluk ile 1200'e kadar).

`ARCHITECT_PLAN.md` K-2 bu yuzden "risk" ifadesinden **canli kusur** ifadesine
guncellendi; R5 riski R8'e tasindi.

---

## Kayit 2026-08-04 · Mimar denetimi: Codex-1 T3-T13 (mutasyon testiyle)

**Yontem:** Dort bagimsiz denetim kolu. Her gorev icin MUTASYON TESTI: gecici
git worktree'de Codex'in duzeltmesi GERI ALINDI ve test kosuldu. Test basarisiz
olmuyorsa test bostur.

**SONUC — BOS TEST YOK.** 11 gorevin 11'inde de mutasyon testi kusuru yakaladi.
Codex'in yazdigi testler gercek.

**Kapsam uyarisi — durustluk notu:** Cekismeli dogrulama TAMAMLANAMADI. Dort denetim
kolunun dordu de kostu, ancak **alti curutme ajaninin altisi da** oturum limitine
takildi (`session limit resets 12:20pm`). Asagidaki bulgular **bagimsiz curutmeden
gecmemistir**; denetim kolunun kendi kanitina dayanir.

| Gorev | Karar | Mutasyon |
|---|---|---|
| T5, T7, T8, T9, T10 | **GECTI** | kusuru yakaliyor |
| T3, T4, T6, T11, T12, T13 | **KISMI** | kusuru yakaliyor |

---

### D-01 · KRITIK · T4 duzeltmesi IKIZ dosyada yapilmadi
`codes/test_rota_guvenlik.py:416`

Cekimserlik kapisi `tests/test_costmap_on_images.py`'de eklendi ve calisiyor
(18 kare, enjekte 0/18 rota -> `[OLCUM_YOK]` + **exit 1**). Ayni kusur
`codes/test_rota_guvenlik.py`'de DUZELTILMEDI.

Gercek foto ile uctan uca kosuldu:
```text
enjekte kipte 0 rota · cekimserlik_enjekte = 1.000
  (betigin kendi <0.60 sartini ihlal ediyor)
buna ragmen: "[GECTI] ... arabaya DEGMIYOR"   EXITCODE=0
```

**Etki:** Ayni girdide iki ozet uygulamasi ZIT cikis kodu veriyor (1 ve 0). Mevcut
58 testin hicbiri bu yolu ortmuyor. Hangi betigin kosuldugu, sonucun ne cikacagini
belirliyor.

---

### D-02 · KRITIK · IKA_GO tek atislik ve ACK'siz
`comms/yks_gui.py:1053` · Gorev T12

Sartname 2.2.5 IKA intikalinin YKS'den manuel tetiklenmesini ZORUNLU kiliyor.
Tetik tek UDP paketi olarak gonderiliyor, ACK beklenmiyor, tekrar yok.

**Etki:** Tek paket kaybi gorevi GERI DONULMEZ bitiriyor. UDP teslimat garantisi
vermez; SiK Radio 433 MHz saha kosullarinda paket kaybi beklenen durumdur.
Karsilastirma: OPEN_ROUTE tekrarli gonderim + ACK ile korunuyor, IKA_GO korunmuyor.

---

### D-03 · KRITIK · Uretim zincirinde IHA_LANDED ureticisi yok
`simulation/scripts/navitas_sim.py:218` · Gorev T13

T13 inis kapisini dogru kurdu (sartname 2.2.5: IHA yere temas etmeden IKA hareket
edemez). Ancak **kapiyi ACAN taraf yok**: varsayilan calistirmada IHA_LANDED
sinyalini ureten hicbir kod yolu bulunmuyor.

**Etki:** YKS kilidi hic acilmiyor -> IKA hic hareket etmiyor -> `P_gorev = 0`.
Yani gorevi KORUMAK icin eklenen kapi, gorevi ENGELLIYOR.

**Genel ders (TEST_SPECS.md 4.6'ya islendi):** Bir kilit/kapi eklendiginde onu
ACACAK tarafin da var oldugu KANITLANMALIDIR.

---

### D-04 · ONEMLI · Ihlal orani paydasi rota uretilmeyen kareleri temiz sayiyor
`tests/test_costmap_on_images.py:168` · Gorev T3

```text
raporlanan: ham_ihlal_orani = 0.2222 (4/18)  ve  0.2368 (9/38)
gercek     : rota URETILEN karelerin 4/4'u ve 9/9'u ihlal ediyor
             -> karar basina oran = 1.00
ayrica     : 18 karenin 7'sinde navitas maskesi TAMAMEN BOS (zemin=0, engel=0)
             ve bunlar paydada
```
Ozet ham cekimserligi hic raporlamiyor.

**Etki:** %100 ihlal, 0,24 diye rapor ediliyor. Kapinin `> 0.10` esigi saglanmis
gorunuyor ama sayinin anlami yanlis okunuyor.

---

### D-05 · ONEMLI · Kalici NO_ROUTE'ta surus asamasinin zaman siniri yok
`simulation/scripts/ika_nav.py:347` · Gorev T6

T6 surus sirasinda NO_ROUTE gelince guvenli durusa gecmeyi dogru ekledi. Ancak
NO_ROUTE kalici olursa surus asamasinin zaman siniri yok: `navitas_sim` hic donmuyor
ve rapor basmiyor.

**Etki:** Sartname IKA'ya 600 sn siniri koyuyor. Sonsuz bekleme hem sinirlari asar
hem de operatore hicbir sey bildirmez.

---

### D-06 · ONEMLI · Ulasilamayan UDP akrani gondericiyi traceback ile olduruyor
`comms/link.py:34` · Gorev T11 komsulugu

`ConnectionResetError` yakalanmiyor.

**Etki:** Alici tarafi kapaliysa veya port kapaliysa IHA gonderici cokuyor.
Sartname 6.4: veri akisinin saglanamamasi ucusu GECERSIZ kilar.

---

### D-07 · ONEMLI · ika_receiver.py'de utf-8 stdout onyuklemesi yok
`comms/ika_receiver.py:18`

Alici ilk OPEN_ROUTE'ta Turkce karakter basarken oluyor. Cozum kalibi
`simulation/scripts/navitas_sim.py:22-26`'da hazir (ayni kusurun orkestratordeki
karsiligi H-R4 olarak zaten kayitli).

---

### D-08 · KUCUK · Letterbox duzeltmesi yalniz X ekseninde tamamlanmis
`codes/rpi_inference.py:181` · Gorev T5/T7 artigi

Serit sinirlari ve alan esigi icerik dikdortgenine baglandi, ancak **waypoint
bantlari hala DOLGULU tuval yuksekligini** boluyor.

**Etki:** Rota noktalarinin %25-33'u kayboluyor.

---

### D-09 · KUCUK · Olcum yolu tohumu plan izgarasindan kayiyor
`codes/test_rota_guvenlik.py:229` · Gorev T3

`_rota_uret` tohumu plan izgarasina `cv2.resize` ile indiriyor. Uretim kodu bunu
hatali sayip `_tohum_plan_izgarasi` ile degistirmisti; olcum yolu eski yontemde kalmis.

---

### D-10 · KUCUK · Bozuk adres bicimi hala ham traceback uretiyor
`comms/iha_sender.py:143` · Gorev T11

T11 adres bayragi EKSIK oldugunda temiz hata vermeyi duzeltti; adres bayragi
BOZUK BICIMDE verildiginde hala ham `ValueError` traceback'i cikiyor.

---

### D-11 · ONEMLI · Surus izni son tarihi rota son tarihiyle ayni
`simulation/scripts/navitas_sim.py:130` · Gorev T13

`--route-timeout` IHA ucus suresini kapsamiyor. Rota beklemesi ile surus izni ayni
son tarihi paylasirsa, IHA gec inerse IKA'nin surus penceresi hic acilmadan kapanir.

---

### D-12 · KRITIK · v17 gercek drone karelerinde tamamen kor
`models/navitas_seg_v17_best.pt` · Jetson hazirligi, 2026-08-05

Ayni model, ayni zincir (`_preprocess` -> `predict` -> `get_masks` ->
`_maskeleri_icerige_kirp`), uc farkli domain, 12'ser kare, `conf=0.25`:

| model | sentetik arena | RescueNet val | drone kareleri |
|---|---|---|---|
| v17 | 59 kutu · %10,8 serbest | 17 kutu · %12,6 serbest | **1 kutu · 11/12 kare bos** |
| v20 | 57 kutu · %10,9 serbest | 15 kutu · %12,2 serbest | **3 kutu · 9/12 kare bos** |

`conf` 0,25 -> 0,10 -> 0,02 indirildi; v17 ucunde de **sifir** tespit verdi
(kutu=0, sinif_dagilimi={}). Esik meselesi degil, **domain boslugu**.

Kareler: `data/raw_frames/` (67 kare, WhatsApp drone videolarindan
`extract_key_frames.py` ile uretilmis, ham 1024x576).

**Etki:** Mimari "serbest alan OTORITEDIR" der; serbest alan bos donerse hicbir yer
gecilebilir sayilmaz ve rota uretilemez. Emniyet yonunde (fail-safe) ama gorev
basarisiz. Ayrica FPS olcumu bu karelerle yapilirsa costmap bos izgarada calisir ve
**FPS yaniltici yuksek** cikar.

**Kanit betikleri:** scratchpad `neden_bos.py`, `v17_domain.py`

---

### D-13 · ONEMLI · `rpi_inference.py` model yolu ve kamera kaynagi sabit kodlu
`codes/rpi_inference.py:32-40` ve `:505`

```python
MODEL_DIR = next((p for p in [
    _here / "best_ncnn_model",
    _here.parent / "models" / "best_ncnn_model", ...   # :32-40
def run_camera(model, conf):
    cap = cv2.VideoCapture(0)                          # :505
```

CLI arguman listesi (`:553-558`) yalniz `--fps --image --video --camera --no-save
--conf` iceriyor; **`--model` ve kamera kaynagi argumani YOK**. `INFER_SIZE = 512`
de sabit.

**Etki (iki bacakli):**
1. Jetson'da v17/v20 ile canli demo kosulamaz — betik her zaman NCNN v2 modelini
   arar.
2. DroidCam bagli olsa bile kaynak verilemez; `VideoCapture(0)` disindaki hicbir
   dugum veya URL kullanilamaz. T18 bu kusuru kapsiyor ama kapsami model yolunu
   icermiyordu.

**Gecici cozum (uretim kodu degistirilmedi):** `jetson_paket/kod/kamera_dogrula.py`
kaynagi parametrik alir; olcum yolu `scripts/jetson_fps.py` zaten kendi YOLO
nesnesini kurdugu icin etkilenmiyor.

---

### D-14 · ONEMLI · ARCHITECT_PLAN'daki "darbogaz costmap" satiri artik gecerli degil
`ARCHITECT_PLAN.md` FPS tablosu · olcum 2026-08-05

Plan *"640: cikarim 26,5 ms · costmap 51,2 ms — darbogaz costmap, cikarimin ~2 kati"*
diyor. Taze olcum (`results/pc_referans_v17_20260805/`, sentetik arena 30 kare,
60 tekrar, RTX 5080, letterbox duzeltmeleri sonrasi):

| asama | PyTorch p50 | ONNX FP16 p50 |
|---|---|---|
| cikarim | **14,00 ms** | **14,79 ms** |
| maske | 2,23 ms | 2,31 ms |
| costmap | **8,89 ms** | **9,98 ms** |
| toplam | 27,38 ms | 29,23 ms |

Costmap 51,2 -> 8,89 ms; **darbogaz cikarima gecti**. Iki olcum farkli girdi
kumesiyle yapildi (eski `jetson_fps_pc_smoke`, yeni sentetik arena) ve aradaki
commit'ler letterbox yolunu degistirdi — kiyaslanabilir degiller, ancak plandaki
sayi artik hicbir guncel kosumu temsil etmiyor.

**Etki:** "Sinif sayisi/model hizi bu karari belirlemiyor, darbogaz costmap"
gerekcesi zayifladi. INT8'in getirisi eskiden sanildigindan yuksek.

**Yan bulgu — sahte kapi:** Ilk ONNX parite testi `data/raw_frames` ile kosuldu ve
serbest alan IoU **1,0000** verdi. Iki maske de BOStu (D-12); bos kumede IoU 1,0
cikar. Kapi bos-dogru (vacuous) gecmisti. Sentetik arenayla tekrarlandiginda gercek
parite kanitlandi: PyTorch ve ONNX 60 karede **birebir ayni** rota dagilimi
(`KAPALI_DAR 24 · BELIRSIZ_TEK_KAPI 22 · MASKE_YOK 6 · BELIRSIZ_COKLU 6 · ACIK 2`).

---

### D-15 · KRITIK · Anayasa madde 4 kapisi hicbir zaman calismadi (sahte gecis)
`REDTEAM.md` K1 · plan/dokuman dolasiminda yayilan komut · olculdu 2026-08-05

Yasak bagimlilik kapisi olarak dolasan komut:
```
grep -rnE "^\s*(import\|from)\s+(scipy\|skimage\|sklearn)" --include=*.py .
```
`-E` (ERE) kipinde `\|` alternasyon DEGIL, duz bir karakterdir. Komut tam olarak
`import\|from` dizisini arar ve **her zaman 0 doner** — kodda scipy olsa bile.

**Pozitif kontrolle kanit** (ayni komut kalibi, kodda KESIN var olan paketler):

| komut formu | yasak paketler | POZITIF KONTROL (numpy/cv2) |
|---|---|---|
| `-E` + `\|` (dolasan form) | 0 | **0** ← komut kor |
| `git ls-files` + dogru ERE | 0 | **46** ← kapi calisiyor |

Ilk satirda pozitif kontrol de 0; yani kapi hicbir seyi yakalayamiyordu.
"0 eslesme" sonucu "yasak paket yok" diye okundu, gercekte "komut bozuk" idi.

**Ikinci kusur — venv sahte pozitifi:** dogru ERE formu kullanilsa bile duz
`-rn ... .` komutu depo icindeki `.gitignore`'lu `navitas-local-train/venv`
dizinini tarar:
```
$ grep -rnE "^\s*(import|from)\s+(scipy|skimage|sklearn|networkx)" --include=*.py . \
    | cut -d/ -f1-2 | sort | uniq -c
   1348 navitas-local-train/venv
```
Tek aramada 1348 sahte pozitif — hepsi site-packages'taki kutuphane kaynagi.
Yerel modelin 16K context'i bu gurultuyle dolar.

**Sonuc:** Anayasa madde 4 **fiilen saglaniyor** (git'in takip ettigi 47 `.py`
dosyasinda 0 yasak import), ancak bunu bugune kadar hicbir kosum kanitlamadi.

**Dogru kapi:**
```
git ls-files "*.py" | xargs grep -nE "^[[:space:]]*(import|from)[[:space:]]+(scipy|skimage|sklearn|networkx)"
```
Beklenen 0; ayni komutu `(numpy|cv2)` ile kosup >0 aldigini DOGRULAMADAN
"temiz" yazilmaz.

---

### D-16 · ONEMLI · Surucu harness'inda uc kusur, biri sessiz yanlis negatif
scratchpad `drive.py` · K7 kosumu 2026-08-05

**(a) BRE alternasyonu — sessiz yanlis negatif.** `REDTEAM.md` "GREP araci kabuk
KULLANMAZ; alternasyon sorunsuz calisir" diyordu. Kabuk katmani icin dogru, ama
grep'in KENDI varsayilan kipi BRE'dir ve BRE'de `|` alternasyon degildir.
Model sunu kostu:
```
GREP -rn "IHA_LANDED|IKA_GO|_LANDED|_READY|_ACK|MSG_|TIP_" --include=*.py .
-> exit=1  (ESLESME YOK)
```
Ayni desen `-E` ile: **75 eslesme**. Sabitler `comms/protocol.py:14,15,102` ve
`comms/ika_receiver.py:47,48,233,243` konumlarinda bastan beri duruyordu.
Model "sabit yok" sanip K7'yi "temiz" raporlayacakti.
**Duzeltildi:** desende kacissiz `|` varken `-E` yoksa ve sonuc bossa, harness
"ESLESME YOK" yerine acik uyari donduruyor.

**(b) UnicodeEncodeError kosumu oldurdu.** Konsol cp1254; gunluk dosyasi utf-8
aciliyordu ama stdout'a yazan `print` cokuyordu:
```
File "...\cp1254.py", line 19, in encode
UnicodeEncodeError: 'charmap' codec can't encode characters in position 400-402
```
Kosum 5. turda tamamen kayboldu. **Duzeltildi:** stdout/stderr utf-8 +
`errors="replace"` ile yeniden yapilandiriliyor.

**(c) venv taramasi context yakiyor.** D-15'teki 1348 sahte pozitif harness
uzerinden modele gidiyordu. **Duzeltildi:** model acikca "venv"/"site-packages"
aramadikca `venv/.venv/.git/__pycache__/node_modules/navitas-local-train`
dizinleri otomatik haric tutuluyor.

Smoke testi duzeltmelerden sonra yeniden kosuldu: **0 dusen test**.

---

### D-17 · KRITIK · D-03 kapanmadi, sekil degistirdi: IHA_LANDED saha ucusunda URETILMIYOR
K7 denetimi (MiniMax M2.5 + mimar dogrulamasi) · 2026-08-05

D-03'te kapinin ACAN tarafi hic yoktu. Bugun ACAN taraf VAR — ama yalnizca
**simulasyon** yolunda. Saha ucusunda kilit acilmaz.

**OKUYAN taraf (kilit):**
```
comms/yks_gui.py:1111-1118
def ika_baslat(self):
    if not self.t_iha1 or self.iha_landed_seq is None:
        self._logla("KILIT  Uretim IHA_LANDED kaniti alinmadan IKA "
                    "hareket EDEMEZ (sartname §2.2.5) — komut REDDEDILDI")
        return
comms/ika_receiver.py:233
    elif tip == "IHA_LANDED" and msg.get("node") == "iha":
```

**YAZAN taraf — uc halkali zincir, 3. halka eksik:**

| halka | konum | durum |
|---|---|---|
| 1. mesaji kurar | `comms/protocol.py:93` `def iha_landed()` | var |
| 2. kurani cagirir | `comms/iha_sender.py:135` `def send_iha_landed()` | var |
| 3. **onu cagiran** | `simulation/scripts/navitas_sim.py:95` | **YALNIZ SIMULASYON** |

`navitas_sim.py` kendi basliginda: *"Navitas — Ana Simulasyon Kontrolcusu"*.

**Saha betigi bu mesaji hic gondermiyor.** `iha_detect_send.py` dosya basligi:
```
Saha (SiK telsiz):
  python3 iha_detect_send.py --scenario kolay --serial /dev/ttyUSB0
```
O betikteki TUM gonderimler:
```
$ grep -n "sender\.send_" simulation/scripts/iha_detect_send.py
134:        seq, acked = sender.send_open_route(road, conf, waypoints, ref_xy,
137:        seq, acked = sender.send_no_route(*no_route, wait_ack=not args.serial)
```
`send_iha_landed` **yok**.

**Gercek donanimda kosan yazilim protokolu hic kullanmiyor:**
```
$ git ls-files "drone/*.py" | xargs grep -nE "IhaSender|iha_sender|from comms|protocol"
   (CIKTI BOS)
```
`drone/rpi_yayin.py` yalnizca video yayini yapar (H.264 UDP 5600/5601, telemetri 5602).

**ETKI:** Saha gorev ucusunda IHA_LANDED hic uretilmez → `yks_gui.ika_baslat()`
her cagrida REDDEDILDI doner → IKA hicbir zaman hareket etmez → **P_gorev = 0**.
Sartname §2.2.5'i korumak icin konan kilit, gorevi engelliyor.

**Kanit uretimi:** arama `git ls-files "*.py"` (47 dosya, test/mock ayrildi)
uzerinde kosuldu; yargi MiniMax M2.5'e bagimsiz dogrulatildi
(kosum `k7y.log`, 3 tur, 2 arac cagrisi, 1273 token).

**Bu D-03'un yerine gecmez — D-03 kapali degil, evrilmis halidir.**

---

### D-18 · KRITIK · Sentetik arena egitimi modeli gercek dunyada korlestirdi
Olcum 2026-08-05 · 67 gercek nadir drone karesi (`data/raw_frames`)

D-12'de v17'nin gercek karelerde kor oldugu olculmustu. Sebep arandi: sorun
modelin kendisi degil, EGITIM SIRASI. Ayni zincir, bes model, dort conf esigi:

| model | conf 0,25 kullanilabilir | ort zemin | egitim gecmisi |
|---|---|---|---|
| v17 | **10/67** | %1,04 | sentetik arena + RescueNet karisimi |
| v20 | **10/67** | %4,11 | sentetik arena + multi_scale |
| v3 | 25/67 | %21,57 | RescueNet |
| v9mix | 46/67 | %53,85 | RescueNet + mixup |
| **v5c** | **58/67** | **%48,65** | RescueNet (yolov8m), sentetik arena GORMEDI |

conf 0,05'te: v5c **66/67** kare · v20 34/67 · v17 21/67.

"Kullanilabilir" olcutu: zemin maskesi kare alaninin >= %5'i.

**Yorum:** sentetik arena verisi arena IoU'sunu 0,031 -> 0,861 cikardi, ama
gercek fotografik dokuya karsi KATASTROFIK UNUTMA uretti. `karisim_arena.yaml`
kendi yorumunda bu riski yaziyordu ("yalniz sentetikle egitim gercek veriyi
unutturur"); karisim yapildi ama yeterli olmadi.

**Olculmus bedeli:** `copy_paste_augmentation.py` v20 zemin kahiniyle 67 kare x 3
kopya = 201 denemeden **yalniz 36 ornek** uretebildi; 165'i `zemin=0 px` diye
atlandi. Ayni betik v5c @ conf 0,05 ile calistirildiginda kare kaybi ortadan
kalkiyor. Yani gercek veri uretmek icin gerceklige bakabilen bir kahin sart --
arena sampiyonu bu isi yapamiyor.

**Gozle dogrulandi** (arena olcum aracinin gizli varsayim dersi):
`scratchpad/v5c_gozle.jpg` — v5c zemini yalnizca asfalti kapliyor; bina catisi,
agaclar ve kenar bitki ortusu zemin SAYILMIYOR. DOTA OBB ayni karede 70+ araci
isaretliyor. Kahin cifti (v5c zemin + OBB arac) uretim icin dogru.

**Etki:** model secimi olcutu degisiyor. Arena IoU tek basina model secemez;
"gercek nadir karede zemin cikarabiliyor mu" ayri bir kapi olmalidir.

---

### D-19 · ONEMLI · Uretecte arac modeline yanlis gorev zorlaniyordu
`scripts/copy_paste_augmentation.py:427` (S1 duzeltmesi sirasinda bulundu)

```python
arac_model = YOLO(str(args.arac_model), task="segment")
```

Arac modeli DOTA **OBB**'ye cevrildikten sonra bu satir bir OBB agirligina
`segment` gorevi dayatiyordu. Ultralytics gorevi zorlandiginda `obb` sonuc alani
bos kalabilir ve `obb_arac_maskesi()` SESSIZCE sifir arac dondurebilirdi --
yani S1 duzeltmesi gorunurde uygulanip fiilen hicbir sey degistirmeyebilirdi.

Kosumda sans eseri calisti: `obb_modeli_mi()` gorev alanina bakip basarisiz
olunca sinif ADLARINA ("small vehicle"/"large vehicle") bakiyor ve True donuyor.
Yani kusur bir yedek kontrol sayesinde ortaya cikmadi.

**Duzeltildi:** gorev zorlanmiyor, agirlik dosyasindan okunuyor
(`YOLO(str(args.arac_model))` -> `task=obb`). Ayrica model yuklenirken kahin
turu ekrana basiliyor ve OBB degilse bir kez acik uyari veriliyor:
`arac kahini: DOTA-OBB (task=obb)`.

---

### D-20 · COZUM · v21_gercek_doku D-12/D-18 korlugunu kapatti
Egitim 2026-08-05 · 141,1 dk · `codes/runs/segment/v21_gercek_doku`

**Recete:** v17/v20 ile BIREBIR AYNI (`v15_ft2sinif` tabani, imgsz 640, 60 epoch,
batch 12, mixup, box 7.5). **TEK DEGISKEN:** veri setine gercek nadir drone
kareleri eklendi (`dataset/copy_paste_gercek`, 393 train goruntu).
Karisim: `dataset/karisim_arena_gercek.yaml` — RescueNet 3449 + sentetik arena
3003 + gercek nadir 393 = 6845 goruntu, 0 corrupt.

**KAPI 1 — gercek nadir kare (ARCHITECT_PLAN K-8), 67 kare, conf 0,25:**

| model | kullanilabilir | ort zemin |
|---|---:|---:|
| v17 | 10/67 | %1,04 |
| v20 | 10/67 | %4,11 |
| **v21** | **67/67** | **%81,24** |

**KAPI 2 — arena:** `MASKE_YOK %0`; karar dagilimi cesitli
(`BELIRSIZ_TEK_KAPI 15 · KAPALI_DAR 12 · BELIRSIZ_COKLU 2 · ACIK 1`).
Arena yetenegi KAYBEDILMEDI.

**KAPI 3 — ONNX FP16 paritesi:** 30/30 ayni karar, **4 farkli karar durumu**
(bos-dogru degil; bu sabah 12 karede IoU 1,0000 alinmisti ve iki maske de bostu).

**S1'IN DOGRUDAN KANITI — arac ustunde zemin sizintisi.** Ayni karede DOTA OBB'nin
"arac" dedigi piksellerin yuzde kaci model tarafindan ZEMIN sayiliyor:

| model | zemin | engel | **arac ustunde zemin** |
|---|---:|---:|---:|
| v5c (uretim kahini) | %68,2 | %0,0 | **%70,2** |
| **v21** | %78,1 | %23,5 | **%2,0** |

v5c araclari hic gormuyor (engel %0) — bu yuzden S1'de DOTA OBB kahini sart oldu.
v21 ayni araclari **engel olarak ogrendi**. Gozle dogrulandi:
`scratchpad/v21_vs_v5c.jpg` — v5c panelinde araclarin tamami mor (zemin sayilan),
v21 panelinde turuncu (engel).

**Zincir:** S1 kahini duzeltti -> 448 gercek ornek uretildi -> v21 araclari engel
ogrendi. Uc adimin da olculmus kaniti var.

**Val metrikleri** (karisik val, 646 goruntu): box mAP50 0,960 · mask mAP50 0,960 ·
mask mAP50-95 0,739 · traversable mask mAP50 0,943 · blocked mask mAP50 0,976.
⚠ Bu sayilar karisik val'dendir ve model secimi icin TEK BASINA kullanilmaz
(K-8: arena + gercek kare kapilari asildir).

**Jetson paketi guncellendi:** `jetson_paket/models/navitas_seg_v21_best*.{pt,onnx}`
ve kanit dosyasi `jetson_paket/V21_KAPI_RAPORU.json`.

---

### D-21 · KRITIK · yks_gui hakem ekrani KOSMADIGI modelin adini basiyor
Bulan: Claude 1 · 2026-08-06 · `comms/yks_gui.py`

Tek bir algi yolunda **dort farkli model adi** ekrana basiliyor; hicbiri
yuklenen dosya degil:

| satir | ekranda yazan | gercek |
|---|---|---|
| `:171` | `CANLI ALGI — navitas_seg_v17` | — |
| `:181` `:194` `:997` | `v17` | — |
| `:885` | *(kod)* | **`navitas_seg_v20_best.pt` yukleniyor** |
| `:888` | `v17 modeli yuklendi … (SHA 8e8d46a6…)` | asagi bak |
| `:994-995` | `model: navitas_seg_v21_best.pt (mAP50 0.6751)` | v21 YUKLU DEGIL |

**SHA iddiasi hicbir modelle eslesmiyor** (`sha256sum models/*.pt`, ilk 8 hane):

    navitas_seg_v17_best.pt  8986c300
    navitas_seg_v20_best.pt  eeb95d17
    navitas_seg_v21_best.pt  799e07f9
    ekranda yazan            8e8d46a6   <- UCUNDE DE YOK

`mAP50 0.6751` de bayat: v21 karisik val mask mAP50 = 0,960 (bkz. D-20).

**Neden KRITIK:** bu ekran sartname §2.2.3/§6.2 geregi **Alan Hakeminin
izledigi** ekrandir. Juri "hangi model" diye sorup dogrularsa ekran yanlis
cevap verir. Kod hatasi degil, **kanit butunlugu** hatasidir.

**Ikinci bulgu — algi kaynaklari v21'in kazandigi alani hic gostermiyor.**
`_algi_gorseller()` uc kaynak taniyor: `test_images/gemini`,
`test_images/test/images`, `dataset/rescuenet_yolo/images/val`. Ucu de
512x512 RescueNet/uretilmis goruntu. **Gercek nadir drone kareleri
(`data/raw_frames`, 67 kare) listede YOK.**

Eslestirmeli olcum (ayni goruntu, ayni esik, ayni imgsz=512, tek degisken model;
kaynak basina 40 kare, yks_gui zinciri birebir kopyalandi):

| kaynak | v20 karar | v21 karar | v20 zemin | v21 zemin | ayni karar |
|---|---:|---:|---:|---:|---:|
| gemini | 25/40 | 25/40 | %9,02 | %8,95 | **37/40** |
| test | 31/40 | 31/40 | %12,14 | %12,28 | **37/40** |
| val | 29/40 | 30/40 | %10,07 | %11,36 | **36/40** |

Bu uc kaynakta v21 ~ v20 (farklar olcum gurultusu tabaninin altinda).
**Ayni iki model gercek nadir karede (67 kare):**

| zincir | model | zemin>=%5 | zemin ort | **engel ort** |
|---|---|---:|---:|---:|
| yks_gui (512) | v20 | 51/67 | %27,35 | **%0,00** |
| yks_gui (512) | **v21** | **67/67** | %76,88 | **%21,83** |
| uretim (640, letterbox) | v20 | 32/67 | %15,70 | **%0,00** |
| uretim (640, letterbox) | **v21** | **67/67** | %78,83 | **%20,11** |

v20 gercek karede **tek bir engel pikseli bile** uretmiyor (iki zincirde de %0,00).
Gozle dogrulandi: `scratchpad/yks_gui_v20_vs_v21.jpg` — otopark karesinde v20
panelinde butun araclar mor (zemin = uzerinden gecilebilir), v21 panelinde
turuncu (engel).

**Kapsam uyarisi (bos-dogru karsiti):** v21 bu 67 karenin **hepsinde** `karar=2`
veriyor. Kareler otopark/acik saha; 3 koridorlu arena yapisi YOK. Yani bu olcum
**algi kurtarimini kanitliyor, koridor SECIMINI kanitlamiyor.** Koridor secimi
yalnizca arena tipi goruntude sinanabilir ve orada v21 ~ v20.

**Dogrulanamayan iki iddia — geri cekildi:**
1. "yks_gui letterbox kullanmadigi icin maske kayiyor" → **YANLIS.** Olculdu:
   1024x576 karede `r.masks.data` sekli `(96, 288, 512)`, en-boy 1,778 =
   goruntunun en-boyu. Ultralytics dolguyu zaten kirpiyor; `get_masks`in
   `cv2.resize(m,(w,h))` cagrisi dogru. Kusur YOK.
2. "imgsz 512, v21 640'ta egitildi, bu ciddi kayip" → **OLCULDU, onemsiz.**
   Tek degisken imgsz, 67 gercek kare: 512 -> zemin %76,88 / engel %21,83;
   640 -> %73,84 / %19,01. Arena tipi 40 goruntude 20/40 vs 18/40 karar.
   Fark gurultu tabaninin altinda. S5 (imgsz kirilganligi) bu yolda tetiklenmiyor.

**Yapilmasi gereken** (kod ameleye gidecek, `TASK_QUEUE.md` S9):
`:885` v21'e cevrilecek; `:171/:181/:194/:997` etiketleri yuklenen dosyadan
TURETILECEK (elle yazilmayacak); `:888` SHA gercekten hesaplanacak veya
kaldirilacak; `:994-995` bayat mAP kaldirilacak; `_algi_gorseller()` sozluguene
`data/raw_frames` eklenecek (rglob — kareler video basina alt klasorde).

---

## Kayit 2026-08-07 · Cok ajanli tam depo taramasi (13 ajan, 86 kanitli bulgu)

Kapsam: algi/rota cekirdegi · haberlesme · simulasyon-saha ucurumu · test ve kapi
altyapisi · belge tutarliligi · veri ve model · sartname uyumu · depo hijyeni.
Asagida yalniz **yeni** ve **tikayici** kayitlar var; onceden kayitli kusurlar
(D-17, S1, S2, K-12 vb.) tekrar edilmedi, yalniz dogrulanma durumlari not edildi.

### D-22 · TIKAYICI · Saha kod yolu DORT ayri yerden kopuk ve hicbir test bunu gormuyor
Bulan: Claude 1 (cok ajanli tarama) · 2026-08-07

Depodaki 58 testin tamami ya simulasyon yolunu ya kutuphane sozlesmesini olcuyor.
**Saha kod yolunu (Gazebo'suz, ROS'suz, Jetson + SiK telsiz) ucu uca sinayan tek
bir test yok.** Bu yuzden asagidaki dort kopukluk ayni anda gorunmuyor; her biri
tek basina `P_gorev = 0` demek.

**Kopukluk 1 — Saha paketinde hicbir haberlesme kodu yok.**

    ls jetson_paket/kod/
    costmap_path_finder.py  jetson_fps.py  kamera_dogrula.py
    karisim_arena.yaml  requirements_rpi.txt  rpi_inference.py
    -> protocol.py / iha_sender.py / link.py / ika_receiver.py YOK

    jetson_paket/kod/requirements_rpi.txt (tam icerik):
    ultralytics
    opencv-python
    numpy
    -> pyserial YOK

Jetson'a takilan USB paketiyle IHA algi yapar ama sonucu **iletemez**.

**Kopukluk 2 — Hedef (HB) koordinatinin tek kaynagi Gazebo `meta.txt`.**

`simulation/scripts/iha_haritala.py:507` → `hb_xy=_meta_xy(meta, "HB_XY")`.
`HB_XY`'yi yazan tek yer `simulation/scripts/world_generator.py:590`, yani
**Gazebo dunya ureteci**. argparse'ta (`:471-488`) `--hb` / `--kb` yok.
Sahada `meta.txt` olmaz → `hb_xy=None` → `:296-306`:

    "rota_durum": "HEDEF_YOK",
    "rota_sebep": "HB koordinati bulunamadi; dinamik rota yayinlanmadi."

Yani sahada **her karede NO_ROUTE**. Kok neden asagida (D-23).

**Kopukluk 3 — `IHA_LANDED` saha yolunda uretilmiyor.** D-17 dogrulandi, kapanmadi:

    grep -rn 'send_iha_landed' --include=*.py .
    comms/iha_sender.py:135   (tanim)
    comms/iha_sender.py:137   (msg = iha_landed())
    simulation/scripts/navitas_sim.py:95   (TEK cagri)
    -> drone/ ve jetson_paket/ altinda SIFIR

**Kopukluk 4 — IKA aktuasyonu Gazebo'ya cakili, gercek motor surucusu yok.**

`simulation/scripts/ika_nav.py:90-100`:

    def send_vel(...):
        msg = f'position {{ x: {right_spd:.3f} ... }}'
        subprocess.run(['gz','topic','-p',topic,'-m',msg],
                       capture_output=True, timeout=1)

Depo genelinde `grep -E 'Serial|GPIO|pwm|arduino|pixhawk|mavlink|CAN'` →
`ika_nav.py` icinde **sifir eslesme**. Uc kosullu surus kapisi sahada saglansa
BILE, kapi acildiginda cagrilan `send_vel()` gercek tekerlegi dondurmez: arenada
`gz` ikilisi yoktur, `subprocess` `FileNotFoundError` verir ve `capture_output=True`
sayesinde hata **yutulur**. IKA fiziksel olarak hareketsiz kalir, hicbir uyari basilmaz.

**Neden TIKAYICI:** dordu de sahada gorev puanini sifirlar. Daha kotusu, hepsi
**sessizdir** — hicbiri istisna firlatmaz, log basmaz. Simulasyon kosumu
(`navitas_sim.py`) dordunu de maskeler cunku `gz` vardir, `meta.txt` vardir,
`IHA_LANDED`i sim'in kendisi uretir ve haberlesme kodu `comms/` altindadir.

**Yapilmasi gereken:** `TASK_QUEUE.md` FAZ 5 (T21-T23). Once **olcen** bir kuru
kosu, sonra onarim. Onarim once yapilirsa neyin duzeldigi olculemez.

### D-23 · KRITIK · Uretim modeli 2 sinifli — hedefi (kirmizi H) goren bilesen YOK
Bulan: Claude 1 (cok ajanli tarama) · 2026-08-07

`config/model_registry.json` competition profili: `"classes": {"0": "traversable",
"1": "blocked"}`. `dataset/combined_data.yaml:22`, `dataset/karisim_arena.yaml:25`,
`dataset/karisim_arena_gercek.yaml:51` → hepsi `nc: 2`.

`grep -E 'kirmizi|brand|hedef tespit'` → yalniz yorum satirlari; **tespit kodu yok.**
`codes/costmap_path_finder.py:233` hedefi geometrik varsayiyor: *"baslangic/hedef=None
ise varsayilan tohum: alt/ust %8 seridi."*

Sartname §2.2.6 gorevi *"IKA'nin HB sinirlari icerisine girmesi"* ile tanimliyor;
§6.2 hedef tespitini zorunlu kiliyor. Hedefi goren bilesen olmadigi icin sistem HB
konumunu **disaridan** almak zorunda — D-22 Kopukluk 2'nin kok nedeni budur.

`CONTRACTS.md §1.1` bunu zaten yaziyor: *"2 = hedef — 2 m x 2 m kirmizi H brandasi"*
ama *"Uretimdeki 2 sinifli modeller {0, 1} alt kumesini kullanir."* Yani sozlesme
ucuncu sinifi tanimliyor, uretim onu hic uretmiyor.

### D-24 · KRITIK · `analyze_path` MORPH_CLOSE oyulmus engeli geri kapatiyor — madde 15 ihlali
Bulan: Claude 1 (cok ajanli tarama) · 2026-08-07 · `codes/rpi_inference.py:139`

    clean = cv2.morphologyEx(clean, cv2.MORPH_CLOSE, k_close)
    # k_close = ELLIPSE(max(7, w//30), max(7, h//30))

Kapama (close) **extensive**tir: `A ⊆ close(A)`. Yani serbest alani BUYUTUR.
CLAUDE.md madde 15'in dogrudan ihlali. Olculdu (600x600, k_close=20x20, dikey
koridor + yatay engel oyugu):

| engel kalinligi | geri kapatilan | oran |
|---:|---:|---:|
| 3 px | 594 / 600 | **%99,0** |
| 7 px | 1386 / 1400 | **%99,0** |
| 12 px | 2311 / 2400 | %96,3 |
| 19 px | 3332 / 3800 | %87,7 |
| 25 px | 374 / 5000 | %7,5 |

Cekirdek `w//30` ile olcekleniyor: 4000 px genisliginde bir sahne fotografinda
cekirdek 133 px olur.

**Neden KRITIK:** `comms/yks_gui.py:929` molozu DOGRU sekilde oyuyor
(`trav[blok > 0] = 0`), sonra `:940` bu fonksiyonu cagirip donen maskeyi `:955-960`
**hakemin gordugu surus koridorunu cizmek icin** kullaniyor. Yani juriye gosterilen
koridor, tespit edilmis molozun ustunden gecebilir.

Karsit kanit — `costmap_path_finder.serbest_alan()` hatti TEMIZ: cikarma en son
islem (`:213`), sonrasinda yalniz anti-extensive baglantili-bilesen filtresi
(`:216-221`). `codes/test_monotonluk.py` 5/5 GECTI; olculdu:
`serbest(K1 ∧ ¬K2) \ serbest(K1) = 0 px`. Sorun tek hatta degil, **iki hattin bir
arada yasamasinda** (acik kusur S4).

### D-25 · TIKAYICI · `rota_bul()` letterbox dolgusunu bilmiyor: pad'lenmis her kare KAPALI_DAR
Bulan: Claude 1 (cok ajanli tarama) · 2026-08-07 · `codes/costmap_path_finder.py:232-242`

    grep -n "icerik" codes/costmap_path_finder.py   ->  0 satir

`_tohum_maske` bandi tam maske yuksekliginden hesapliyor: `pay = max(1, int(h * 0.08))`.
Olculdu (1024x1024 tuval, icerik y=[224,800), 3 koridor, sol kapali):

    varsayilan alt tohum bandi y = 943..1023   (icerik 224..799)
    alt tohum ile zemin kesisimi = 0
    ust tohum ile zemin kesisimi = 0
    mpp=None        durum=KAPALI_DAR  yol_no=None
    mpp=0.0546875   durum=KAPALI_DAR  yol_no=None
    KIRPIK mpp=None       durum=ACIK  yol_no=2
    KIRPIK mpp=0.0546875  durum=ACIK  yol_no=2

Etkilenen cagri yerleri (hepsi `rpi_inference._preprocess` ile pad'leyip varsayilan
tohumla cagiriyor): `scripts/jetson_fps.py:162`, `jetson_paket/kod/jetson_fps.py:162`,
`jetson_paket/kod/kamera_dogrula.py:118`, `scripts/v21_degerlendir_ve_paketle.py:71`.

**Neden TIKAYICI:** `kamera_dogrula.py` Jetson saha dogrulamasidir — gercek kamerada
**asla ACIK goremez**. Ayrica bu, D-20'de v21'in gercek karelerde `67/67 KAPALI_DAR`
vermesinin muhtemel gercek nedenidir; yani **model degil, tohum bandi** kusurlu
olabilir. Model secimi bu sayiya dayandirildi (ARCHITECT_PLAN K-8) — yeniden
olculmeden v21/v20 karsilastirmasi guvenilir sayilmamalidir.

Etkilenmeyenler ve nedeni: `iha_haritala` (mozaik zaten kare + acik KB/HB tohumu
geciriyor), `codes/test_rota_sentetik.py` (sentetik sahne zaten kare). **Genel kapi
15/15 bu yuzden kusuru yakalamiyor.**

### D-26 · TIKAYICI · v21'in "gercek kare kapisi" kendi egitim verisinde kosuluyor + val %100 sizintili
Bulan: Claude 1 (cok ajanli tarama) · 2026-08-07

**(a) Kapi ezberleme testi.** `scripts/v21_degerlendir_ve_paketle.py:46` →
`GERCEK_KARE = KOK / "data" / "raw_frames"`. Ayni dizin uretecin girdisi:
`scripts/copy_paste_augmentation.py:375` → `default=KOK / "data" / "raw_frames"`,
`dataset/copy_paste_gercek/manifest.json` → `"girdi": "data\\raw_frames"`.
Manifest ozeti: essiz kaynak kare **67**, uretime giren **56**, yazilan ornek **448**.
Yani v21 kendi egitim verisinin kaynak fotograflarinda sinaniyor.

**(b) Val bolumu foto duzeyinde %100 sizintili.**
`scripts/copy_paste_augmentation.py:327-331`:

    def bolum_sec(kaynak, cesit, tohum, val_oran):
        anahtar = f"{kaynak.as_posix()}:{cesit}:{tohum}".encode("utf-8")
        #                               ^^^^^ kopya indeksi anahtarda
        return "val" if deger < val_oran else "train"

Bolme anahtarina **kopya indeksi** girdigi icin ayni fotograf hem train hem val'e
dusuyor. Manifest uzerinden olculdu:

    train essiz kaynak 56 · val essiz kaynak 41 · KESISIM 41 · sadece val 0
    kopya sayisi/kare: Counter({8: 67})

**Neden TIKAYICI:** `best.pt` **sizintili val ile secildi**. D-20'de raporlanan
"karisik val mask mAP50 = 0,960" bu sizintiyi iceriyor. D-25 ile birlikte
degerlendirildiginde: v21'in v20'den ustun oldugu iddiasinin **iki bagimsiz
dayanagi da sarsilmis** durumda. TASK_QUEUE H10 (bakir ikinci cekim) hala gercek
anlamda acik — `[HUMAN_COMPLETED]` isaretli ama veri diskte yok.

### D-27 · ONEMLI · REVIEW_LOG kayitlarinin yarisi yetim; tek TIKAYICI yetim kayip goreve isaret ediyor
Bulan: Claude 1 (cok ajanli tarama) · 2026-08-07

40 kayittan **21'i yetim** (bir goreve baglanmamis): 1 TIKAYICI, 6 KRITIK, kalani
ONEMLI/KUCUK. Tek TIKAYICI yetim:

`REVIEW_LOG.md:592-593` → *"H-R4 · TIKAYICI · Orkestrator Turkce Windows'ta cikti
yonlendirilince cokuyor · `auto_orchestrator.py:9,11,12,13,48` · **Gorev T0**"*.
`ARCHITECT_PLAN.md:382` ayni kusuru T0 satiriyla listeliyor.

    grep -n "T0\b" TASK_QUEUE.md
    -> yalniz :10 ve :24 (auto_orchestrator gecmesi); T0 baslikli GOREV SATIRI YOK

**Neden onemli:** orkestrator coktugunde hicbir insan gorevi yuzeye cikmaz →
FAZ 0/0-B sessizce durur. H1/H7 (VTOL drone, 30 Eylul, FDA'nin %15'lik bacagi)
tam da bu kanaldan izleniyor. Yani izleme mekanizmasinin kendisi kirik ve bu
kiriklik kuyrukta gorunmuyor.

### D-28 · KRITIK · `analyze_path` waypoint'leri baglantisiz: iki ucu zemin olan KENAR engelin ustunden geciyor
Bulan: Kullanici (saha testi) · dogrulayan: Claude 1 · 2026-08-08 · `codes/rpi_inference.py:179-186`

Kullanici sahada test edip bildirdi: *"node sayisi cok az oldugu icin 2 node zemin
olsa bile arasindaki kenarlar engelin ustunden gecebiliyor."* **Dogrulandi ve
olculdu.**

Waypoint uretimi (`codes/rpi_inference.py:179-186`):

```python
for i in range(n_waypoints - 1, -1, -1):     # n_waypoints = 8
    y0 = i * h // n_waypoints
    y1 = (i + 1) * h // n_waypoints
    band = dist[y0:y1, :]
    if band.max() > 0.5:
        ly, lx = np.unravel_index(band.argmax(), band.shape)
        waypoints.append((int(lx), int(y0 + ly)))
```

Goruntu 8 yatay banda bolunuyor ve her bandin **distance-transform maksimumu**
waypoint yapiliyor. Ardisik iki bandin maksimumu goruntunun bambaska yerlerinde
olabilir ve **aralarindaki dogru hic denetlenmiyor**.

**Olcum** (640x640, iki dikey koridor + aralarinda engel duvari; alt yarida sol,
ust yarida sag koridor genis — `scratchpad/wp_kenar_probu.py`):

```text
analyze_path -> yol=2 guven=0.0 waypoint=8
waypointler (alt->ust): [(120,560), (120,480), (121,402), (122,399),
                         (520,240), (520,160), (520,80), (520,0)]
  IHLAL segment 3: (122,399) -> (520,240)  engel uzerinde 119 piksel
SONUC: 1/7 segment ENGELIN USTUNDEN geciyor
analyze_path imzasinda engel maskesi parametresi var mi: False

rota_bul -> durum=BELIRSIZ_COKLU yol_no=None wp=0
rota_bul segment ihlali: 0/0
```

Waypoint 3 sol koridorda (`x=122`), waypoint 4 sag koridorda (`x=520`); iki ucu da
zemin, aradaki kenar **119 engel pikselinin** ustunden geciyor.

**Dort ayri kusur ust uste biniyor:**

1. **Kenar denetimi yok.** Ardisik waypoint'ler arasinda gorus hatti kontrolu
   yapilmiyor. `costmap_path_finder` bu isi dogru yapiyor — `_gorus_hatti`,
   `_maks_aralikla_bol` (`:571-628`) ve `rota_dogrula` (`:696-716`) her segmenti
   `cv2.polylines` ile rasterize edip hem acikliga hem HAM engel maskesine
   bakiyor. Uretim yolu bu makinenin **hicbirini** kullanmiyor.
2. **Engel maskesi hic okunmuyor.** Imzada parametre yok (acik kusur S4).
   Kenar denetlense bile karsilastirilacak engel yok.
3. **Bant bos ise waypoint SESSIZCE atlaniyor** (`if band.max() > 0.5`), bu da
   kalan waypoint'ler arasindaki denetlenmemis atlamayi daha da uzatiyor.
4. **Bantlar tam tuval yuksekligi `h` uzerinden** hesaplaniyor, icerik kutusu
   uzerinden degil — letterbox'li girdide ust/alt bantlar gri dolguya dusuyor
   (D-25 ailesi).

**Ayrica: guven esigi hicbir yerde uygulanmiyor.** Yukaridaki olcumde
`guven=0.0` donmesine ragmen `yol=2` uretildi. `analyze_path`'in alti cagri
yerinin (`rpi_inference.py:390,470,530` · `test_accuracy.py:182` ·
`yks_gui.py:940` · `iha_perceive.py:106`) **hicbirinde** guven esigi yok;
`grep -rnE "conf *[<>]=?|guven *[<>]=?"` uretim kodunda tek eslesme veriyor
(`iha_perceive.py:88`) ve o da model tespit esigi, rota guveni degil.
Yani sifir guvenli bir karar dogrudan `OPEN_ROUTE`'a gidiyor.

**Neden KRITIK:** sartname §5.3.2/§6.2 yanlis guzergah tespitini **0 puan**
sayiyor; §2.2.6 IKA'nin yapisal butunlugunu sart kosuyor. Bu kusur her ikisini
de tetikleyebilir ve **sessizdir** — ne istisna ne uyari uretir.

**Neden simdiye kadar yakalanmadi:** genel kapi `codes/test_rota_sentetik.py`
`rota_bul`'u olcuyor, `analyze_path`'i degil. 15/15 gecerken uretimde kosan kod
denetlenmemis kaliyor. Bu, S4'un ("iki iraksak karar yolu") olculmus ve
somutlanmis halidir.

**Yapilmasi gereken:** `TASK_QUEUE.md` FAZ 7 (T24). Kalici cozum `analyze_path`
cagri yerlerini `costmap_path_finder.analyze_path_uyumlu`'ya (`:954`, su an
hicbir yerden cagrilmiyor) gecirmektir; ara cozum olarak `analyze_path`'e engel
maskesi + `_gorus_hatti` denetimi eklenebilir.

### D-29 · ONEMLI · Koridorun hedefe ULASTIGI dogrulanmiyor: kapali serit acik raporlanabilir
Bulan: Claude 1 (T24 uygulamasi sirasinda) · 2026-08-08 · `codes/rpi_inference.py:162-169`

Kullanici sordu: *"acik yolu secme konusunda yeterli mi emin degilim."* T24
uygulanirken olculdu: **yeterli degil.**

Duz bir koridorun ortasina yatay bariyer konuldu (koridor artik kareyi bastan
basa gecmiyor):

```text
z[:, 260:380] = 1          # duz dikey koridor
e[300:340, :]  = 1         # yatay bariyer
analyze_path(z, engel_mask=e)  ->  yol=2  guven=1.0  wp=4
```

Karar **`yol=2`, guven `1.0`** — yani "orta serit acik, tam guvenle". Oysa
koridor hedefe ulasmiyor.

**Neden:** serit karari, en buyuk bagli bilesenin **ust %30 bandinin centroid'i**
ile veriliyor (`:162-169`). O bilesenin goruntunun ust kenarina (hedef tarafa)
**ULASIP ULASMADIGI hic sorulmuyor.** Bariyer bileseni ikiye boluyor, en buyuk
parca aliniyor ve o parcanin kendi ust bandi "cikis" sayiliyor.

`rota_bul` bu durumu dogru yakaliyor: `KAPALI_KOPUK` durumu tam da bunun icin
var (`:732`). Uretim yolu bu makineyi kullanmiyor — S4/D-28 ile ayni kok neden.

**Neden T24 bunu kapatmadi:** T24 KENAR guvenligini onardi (ardisik waypoint'ler
arasindaki dogru artik denetleniyor). Bu ise UC NOKTA sorunudur: butun kenarlar
gecerli olabilir ama zincir hedefe varmayabilir. Iki ayri kusur.

**Etki:** sartname §5.3.2/§6.2 yanlis guzergah tespitini **0 puan** sayiyor.
IKA kapali bir seride yonlendirilir ve molozun onunde durur.

**Yapilmasi gereken:** `TASK_QUEUE.md` T26.

---

**Ikinci tutarsizlik:** `TASK_QUEUE.md:27` VTOL drone satiri `[HUMAN_COMPLETED]`
isaretli; ayni gorevin ikizi `:42` (H7) yine `[HUMAN_COMPLETED]` ama notu
*"Kullanici 3 Agustos'ta 'yok / belirsiz' bildirdi"* diyor. Durum "tamamlandi",
kanit "yok". `:36-38` bolum basligi bunu itiraf ediyor ama satirlar duzeltilmemis.
