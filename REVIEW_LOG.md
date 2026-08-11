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

---

### D-30 · KRITIK · T26'nin tarif ettigi yalniz-hedef kapisi kendi sentetik kapisini dusurmuyor
Bulan: Codex-2 (T26 uygulama-oncesi pozitif kontrol) · 2026-08-09 ·
`codes/rpi_inference.py:246-306`

T26, en buyuk bagli bilesenin icerik kutusunun ust hedef seridine temasini
dogrulamayi istiyor. Ancak gorevin kendi bariyerli sahnesinde secilen bilesen zaten
**ust kenara temas ediyor**; eksik olan baslangic (alt kenar) baglantisi:

```text
BARIYER yol=2 guven=1.0 wp=4 y_min=0 y_max=299 ust_temas=True alt_temas=False
ACIK    yol=2 guven=1.0 wp=8 y_min=0 y_max=639 ust_temas=True alt_temas=True
```

Komut, T26'daki sahneyi birebir kurdu: `z[:,260:380]=1`,
`e[300:340,:]=1`, ardindan `analyze_path(..., engel_mask=e,
return_clean=True)`. Bariyer iki esit parca urettigi icin
`connectedComponentsWithStats` ilk etiket olan **ust parcayi** seciyor. Yalniz
"hedef bandina temas" denetimi eklenirse bu parca yine gecer ve T26 kapisi hala
`yol=2` doner.

**Gerekli invariant:** karar bileseni, icerik kutusundaki baslangic bandina bagli
olmali ve **ayni etiket** hedef bandina da ulasmali. Baslangic/hedef bant oranlari
`CONTRACTS.md`'de tek kaynak olarak tanimlanmadan uygulayicinin sayi secmesi
sozlesme ihlalidir. Mevcut `CONTRACTS.md` bu oranlari tanimlamiyor; yalniz eski
%8 tuval kusurunu tarihsel bulgu olarak aniyor.

---

### D-31 · KRITIK · T25 dosya kapsami OPEN_ROUTE yayin kapisini kapsamiyor
Bulan: Codex-2 (T25 uygulama-oncesi cagri haritasi) · 2026-08-09 ·
`comms/iha_sender.py:108-118,202-213`

T25 yalniz `codes/rpi_inference.py`, `comms/yks_gui.py` ve
`simulation/scripts/iha_perceive.py` dosyalarini listeliyor. Bunlarin hicbiri
protokol `OPEN_ROUTE` mesaji yayinlamiyor: ilki yerel JSON/gorsel, ikincisi GUI
gosterimi, ucuncusu JSON/overlay uretiyor. Gercek yayin noktasi
`IhaSender.send_open_route`; ayrica `iha_sender.py` CLI herhangi bir `conf`
degerini dogrudan bu metoda geciriyor:

```text
comms/iha_sender.py:108  def send_open_route(...)
comms/iha_sender.py:212  sender.send_open_route(road, conf, ...)
simulation/scripts/iha_detect_send.py:134  sender.send_open_route(...)
simulation/scripts/hakem_log.py:156  sender.send_open_route(...)
simulation/scripts/mission_demo.py:66  sender.send_open_route(...)
```

Bu nedenle yalniz T25'te listelenen uc dosyayi degistiren bir test, "esik alti
karar OPEN_ROUTE olarak **yayinlanmadi**" kapisini uctan uca kanitlayamaz.
Guven esigi de `CONTRACTS.md`'de tanimli degil ve Codex'in bu dosyaya yazma
yetkisi yok. Mimar once esik degerini ve kapinin `IhaSender` seviyesinde mi,
cagri yerlerinde mi (ya da ikisinde birden mi) uygulanacagini belirlemelidir.

---

### D-32 · ONEMLI · Sozdizimi kapisini gecen ama CALISMAYAN kod: `_h.update(_blk)`
Bulan: Claude 1 · 2026-08-09 · gpt-oss-120b (N4) kosum ciktisi

> ⚠ **BU KAYIT YAZILDIKTAN SONRA DUZELTILDI (ayni gun).** Ilk yazimda hata
> "`comms/yks_gui.py` icinde bulundu ve duzeltildi" deniyordu. **Yanlisti.**
> Hata N4'un uretti(gi) **gecici surumde** vardi; o surum kosum ortasinda
> kayboldu (bkz. D-33) ve depodaki dosya `40859b3` commit'indeki temiz haline
> dondu. Depoya **hicbir zaman girmedi.** Asagidaki ders yine de gecerlidir:
> kanit N4'un kosum kayitlarinda ve bagimsiz `ast` taramasindadir.

S9'un SHA hesabi blogunu gpt-oss-120b (N4) yazdi. Uretilen kod:

    for _blok in iter(lambda: _fh.read(1 << 20), b""):
        _h.update(_blk)          # <- _blok DEGIL _blk

Dongu degiskeninin adi `_blok`, govdede `_blk`. Calisma zamaninda **NameError**.

**Hicbir otomatik kapi yakalamadi:**

| kapi | neden goremedi |
|---|---|
| `ast.parse` (harness her degisiklikten sonra kosuyordu) | sozdizimi GECERLI; tanimsiz isim calisma zamani hatasidir |
| headless algi kapisi (`s9_kapi.py`) | yalniz `_algi_gorseller` cagriliyor; `_algi_kos` yolu hic calismiyor |
| `codes/test_rota_sentetik.py` 15/15 | GUI'ye hic dokunmuyor |
| `unittest discover` 101 test | model yukleme yolu test edilmiyor |
| icerik dogrulamasi (`"hashlib.sha256()" in src`) | ifade vardi; degisken adi kontrol edilmiyordu |

Saha etkisi **(eger o surum commit edilseydi)**: hakem `V` ile algi gorunumune
gecince, model yuklenirken `ALGI HATASI: name '_blk' is not defined` basilacakti
— yani S9'un duzeltmeye calistigi **kanit butunlugu ekrani hic acilmayacakti.**

Gozle denetimde bulundu; `ast` tabanli tanimsiz-isim taramasiyla bagimsiz
dogrulandi:

    SUPHELI: _algi_kos() satir 894: '_blk' kullanilmis ama ATANMAMIS

Duzeltildikten sonra, blogun birebir kopyasi ayri kosuldu:

    hesaplanan SHA (ilk 8) : 799e07f9
    D-21 kaydindaki v21    : 799e07f9   -> ESLESTI

**Ders — kapi tasarimi.** "Sozdizimi OK" bir kapi degil, yalnizca on kosuldur.
Yerel modele yazdirilan kodda, **degistirilen kod yolunu gercekten kosturan**
bir kapi sart. Ayrica metin aramasiyla yapilan icerik dogrulamasi ("su ifade
dosyada var mi") *"birseyler yazildi"* der, *"dogru calisiyor"* demez.
Dogrulama degisen davranisi olcmelidir.

---

### D-33 · KRITIK · ZATEN COMMIT EDILMIS bir gorev, calisma agaci geride oldugu icin bastan yapildi
Bulan: Claude 1 · 2026-08-09 · `comms/yks_gui.py`, `TASK_QUEUE.md`

> ⚠ Bu kayit once "ayni dosyada eszamanli iki calisma" olarak yazilmisti.
> `git show` ile **yanlislandi**; asagidaki hali olculmus gercektir.

S9 gorevi N4'e verilirken iki sey dogru sanildi, ikisi de yanlisti:

| sanilan | olculen gercek |
|---|---|
| "S9 acik" — `TASK_QUEUE.md:987` satiri `- [ ]` idi | S9 **dun tamamlanmis ve commit edilmis**: `40859b3 yks: hakem ekrani kanit butunlugu ve dayaniklilik (S9 + S10)` |
| "calisma agacindaki dosya guncel" | Dosya **commit'ten GERIDE** idi: 1406 satir / sha `A05C9224…`, icinde hala `navitas_seg_v20_best.pt`, `v17`, `SHA 8e8d46a6…`, `d.iterdir()` |

`git show 40859b3:comms/yks_gui.py` olcumu (1438 satir):

    ALGI_MODEL_DOSYA -> 5     navitas_seg_v20_best -> 0     8e8d46a6 -> 0
    d.rglob -> 1              d.iterdir -> 0                "drone" -> 3
    mAP50 0.6751 -> 0         _blk -> 0

Yani S9'un **tamami** commit'te zaten vardi. `git status` dosyayi `M` gosteriyordu
ama bu "ilerlemis" degil, **"gerilemis"** anlamina geliyordu — ve kimse bakmadi.

**Ne oldu:** N4 ~6 saat boyunca zaten yapilmis bir isi bastan yapti. Kosumun
ortasinda calisma agaci commit'teki haline dondu; N4'un urettigi kod (ve
icindeki `_blk` hatasi, D-32) **sessizce kayboldu**. Son `git diff HEAD` bunu
kanitliyor: calisma agaci ile commit arasinda yalniz **3 bicim duzeltmesi** var,
N4'un yazdigi tek satir yok.

**Kok neden — gorev secimi `git`'e bakmiyor.** Kuyruk durumu (`- [ ]`) tek
otorite sayildi. Oysa gorevin gercekten yapilip yapilmadiginin otoritesi
**depodur**. Kuyruk ile depo ayrisabilir ve bu turda ayristi.

**Kural (bundan sonra baglayicidir):** Bir goreve baslamadan once
1. `git log --oneline -15` icinde gorev kodu (T*/S*) araniir;
2. hedef dosya icin `git status` **ve** `git diff HEAD --stat` bakilir;
3. calisma agaci commit'ten **geride** ise once bu ayrisma cozulur, is baslatilmaz.
Uzun kosumlarda hedef dosyanin sha'si baslangicta kaydedilip bitiste
karsilastirilmalidir; bu turda fark ancak tam `difflib` dokumuyle gorulebildi.

---

### D-34 · TIKAYICI · T20'nin kok nedeni kuyrugun tarif ettiginden BIR KATMAN DERIN
Bulan: Claude 1 (4 ajanli denetim kosumu) · 2026-08-10 · saha inis kaniti zinciri

T20 kuyrukta "iha_detect_send.py `send_iha_landed()` cagirmiyor" diye tarif
edilmisti. Denetim bunu **yetersiz** buldu: eksik olan TASIMA cagrisi degil,
**KANIT KAYNAGI**.

**Uretici zinciri — 3 halkanin 3'u saha disinda:**

    comms/protocol.py:93-106    def iha_landed(seq=None)                    VAR
    comms/iha_sender.py:135-139 def send_iha_landed(...)                    VAR
    TEK CAGIRAN: simulation/scripts/navitas_sim.py:95                       SIM-ONLY

`git ls-files "*.py" | xargs grep -n "send_iha_landed"` -> `simulation/` disinda
tek bir **uretim** cagrisi yok (`scripts/saha_kuru_kosu.py` eslesmeleri AST
dedektoru, `tests/` fixture).

**Kanit kaynagi asimetrisi:**

| yol | inis kaniti nereden | durum |
|---|---|---|
| simulasyon | `iha_flight.fly()` -> Gazebo son yer temasi pose komutunun KABULU (`iha_flight.py:51-59` returncode) | VAR |
| saha | — | **HIC YOK** |

`grep -rniE "pymavlink|mavutil|dronekit|pixhawk|LANDED_STATE|relative_alt" --include=*.py`
-> uretim kodunda **SIFIR**. `drone/rpi_yayin.py:479-496` telemetrisi yalniz
`t/calisma_sn/cpu_c` tasiyor; **irtifa alani bile yok** ve `drone/` kendi
HELLO/ACK protokolunu kullanip `comms/protocol.py`'yi hic import etmiyor.

**Kuyrugun onerdigi (a) secenegi MIMARI OLARAK YANLIS.** `iha_detect_send.py`
tek atimlik bir surectir: tespit + gonderim yapip `:144 link.close()` ile cikar,
ve gorev kurali geregi **IHA HAVADAYKEN** kosar. Inis, o surec BITTIKTEN sonra
gerceklesir. O dosyaya `send_iha_landed()` eklemek ancak ayri bir mod/dongu
eklenirse anlamlidir.

**Canli kapi kosumu (2026-08-10), `scripts/saha_kuru_kosu.halka_surus_izni`:**

    DURUM: DUSTU
    sebep : "kapi dogru ama beslemesi kopuk"
    tum_ureticiler   : ["simulation/scripts/navitas_sim.py:95"]
    saha_ureticileri : []
    kapi_probu       : bos_kapali=true · yalniz_ika_go_kapali=true
                       iki_latch_ile_acik=true · prob_gecerli=true

Yani **kapinin kendisi dogru calisiyor**; kopuk olan besleme.

**T13 ile CELISKI YOK — ayni zincirin iki ucu.** T13 tuketici ucunu fail-closed
kapatti (dogru is); tam bu yuzden T20 artik "eksik ozellik" degil, sahada
**P_gorev = 0** ureten tikayicidir.

**Kapsam uyarisi:** T20 tek basina kapansa bile IKA sahada YINE hareket etmez.
`results/saha_kuru_kosu_20260808/ozet.json` halka 10 (gercek motor surucusu)
**SAHIPSIZ**, halka 8 (aktarim) jetson paketinde yok (`eksik_moduller =
[iha_sender.py, link.py, protocol.py]`, `pyserial_bagimliligi=false`);
`CONTRACTS.md:273-275` ikisini de sahipsiz gosteriyor. T20'nin kapi ciktisi
**"IKA hareket etti" diye ILAN EDILMEMELIDIR** — kanit yalnizca "IHA_LANDED
latch'i SAHA kaynagindan acildi" olabilir.

---

### D-35 · KRITIK · Sozlesme belgesi cozulmus bir cakismayi YURURLUKTE gosteriyordu
Bulan: Claude 1 (4 ajanli denetim kosumu) · 2026-08-10 · `CONTRACTS.md` §1.2-§1.3

S2 (sinif-id cakismasi) **kodda cozulmus** ve commit edilmisti
(`codes/sinif_semasi.py`: egitim ad alani `0/1/2`, costmap ad alani `0/1/10`;
`iha_haritala.py:60,327` sabitten okuyor, ciplak sayi yok). Ama `CONTRACTS.md`
§1.2 hala **"⛔ CAKISMA — cozulene kadar gecerli uyari"** basligiyla eski kodu
(`{0,1,2: arac}`, `engel_sinif_idler=(1, 2)`) **yururlukteki kod** diye
gosteriyordu ve `KATMAN_ARAC=10` ad alanini hic tanimlamiyordu. §1.3 de
`engel_sinif_idler = (1,)` diyordu — gercek deger `(1, 10)`.

**Neden KRITIK:** `CLAUDE.md` madde 16 *"Sozlesmeler CONTRACTS.md'den okunur"*
diyor. Bu belgeyi okuyup yeni bir costmap tuketicisi yazan bir sonraki ajan
`{0,1,2}` semasini **geri getirirdi**. Kuyruk S6'yi (hedef tohumu) acikca
"S2 sozlesmesinden sonra" diye isaretliyor — yani tuzak bir sonraki gorev icin
kurulmus durumdaydi.

`sinif_semasi.dogrula()` bunu ancak KATMAN sabitleri degistirilirse yakalar;
yeni bir cagri yeri ciplak `(1, 2)` yazarsa **sessizce gecer** — CONTRACTS.md'nin
kendi uyardigi gibi: *"Sozlukte olmayan id sessizce atlanir ... sessizce
guvenligi dusurur."*

**Duzeltildi (2026-08-10):** §1.2 "✅ CAKISMA COZULDU" olarak yeniden yazildi,
iki ad alani tablosu ve `KATMAN_ARAC=10` gerekcesi eklendi; §1.3 sabitleri
`sinif_semasi`'den okuyacak sekilde guncellendi.

**Ders:** kod duzeltilince **sozlesme belgesi ayni commit'te guncellenmeli.**
Belge ile kod ayristiginda tehlikeli olan taraf koddaki kusur degil, **belgedeki
bayat dogrudur** — cunku bir sonraki yazar ona uyar. Denetimde artik su soru da
sorulur: *"bu gorev bir sozlesmeyi degistirdi mi; degistirdiyse CONTRACTS.md
guncellendi mi?"*

---

### D-36 · ONEMLI · Ilk Jetson FPS sayisi VEKIL DONANIMDA alindi ve KANITSIZ
Bildiren: kullanici · 2026-08-10 · kayit: Claude 1

> ⚠ **BU KAYIT YAZILDIKTAN SONRA DUZELTILDI (ayni gun).** Ilk yazimda "Jetson
> donanimi DEGISTI (Orin NX -> Nano 4GB)" deniyordu. **Yanlisti.** Kullanici
> netlestirdi: uretim hedefi **Orin NX 16 GB** olarak KORUNUYOR; Nano 4GB yalnizca
> elde olan **vekil test kartidir**. Belgelerin Orin NX varsaymasi dogrudur,
> degistirilmeyecektir.

**1) Olcum vekil donanimda yapildi — uretim hedefi degismedi.**

| | test (bugun) | uretim hedefi |
|---|---|---|
| kart | **Jetson Nano 4GB** | **Jetson Orin NX 16GB** |
| GPU | Maxwell · 128 CUDA cekirdek | Ampere · Tensor cekirdekli |
| CPU | 4x Cortex-A57 | 8x Cortex-A78AE |
| RAM | 4 GB paylasimli | 16 GB |
| JetPack hatti | 4.6 (Ubuntu 18.04 / Python 3.6 / TRT 8.2) | 5.x/6.x (Python 3.8+) |

Aradaki fark **mertebe duzeyindedir**. Sonuc olarak Nano'da olculen her sayi
Orin NX icin bir **ALT SINIR**dir. Bu, FPS tarafinda rahatlatici bir isarettir:
kapsama hesabindan gereken hiz **0,9-2,6 FPS**; zayif kartta bile bunun katbekat
ustu goruluyorsa hedef kartta hiz **risk maddesi olmaktan cikar**.

**Kalan bagimliliklar (Orin NX icin hala gecerli):**
  - T16'nin `.engine` adimi Orin NX'in TensorRT surumunde derlenmelidir — engine
    hem TensorRT surumune hem GPU mimarisine kilitlidir. **Nano'da derlenen engine
    de Orin NX'te calismaz**; vekil kart bu adimi kapatmaz.
  - H2 kunyesi (JetPack + TensorRT + Python surumu) hala kayitsiz. Kunye **hedef
    kartta** toplanmalidir; Nano kunyesi yalnizca vekil kosumu belgelemek icindir.
  - `ultralytics` Python 3.8+ ister; Nano'nun JetPack 4.6 hatti Python 3.6 tasir.
    Vekil kosumun hangi yiginla yapildigi **kayda gecmemistir** — bu, 14 FPS'in
    dogrulanmasi gereken bir baska yonudur.

**2) Bildirilen sayi: 14 FPS. Su an KANIT DEGIL — sebep tek degil, dort.**

| # | Eksik | Neden onemli |
|---|---|---|
| a | **Cikti dosyasi yok** (yalniz ekranda gorulmus) | T17'nin kapisi acikca `results/jetson_fps_<tarih>/` altinda olculmus sayi istiyor |
| b | **Girdi kumesi bilinmiyor** | `jetson_fps.py --girdi` VARSAYILANI `data/raw_frames` yani **drone kareleri**. Kilavuz G3: *"drone kareleriyle olcersen model bos maske dondurur, costmap neredeyse bos izgarada calisir ve FPS YANILTICI YUKSEK cikar."* Kural: olcum `test_goruntuleri/sentetik_arena/` ile yapilir |
| c | **Model/format/imgsz bilinmiyor** | Kilavuz G1: varsayilan `--pt` **v20**'dir, kilavuzun kendi onerisi **v21**; `--onnx` varsayilani pakette **YOK** |
| d | **Guc modu kayitsiz** | Kilavuz: *"Guc modunu MAKSIMUM yap — yoksa olcum yalan soyler"* (Nano'da 5W vs 10W ciddi fark) |

Ek olarak kilavuz G2, bu zincirde FPS'in **"bir miktar iyimser"** olabilecegini
zaten not ediyor: `rota_bul` tohum bantlari letterbox dolgusuna dustugu icin
`koridor_adaylari` erken donuyor (D-25).

**3) Ihtiyati not — sayinin yonu.** Nano 4GB'da segmentasyon + costmap zinciriyle
14 FPS, PC referansiyla (RTX 5080, 60 ornek, imgsz 640: **34,04 FPS**) yan yana
konunca yalniz ~2,4x yavas demektir. Donanim mertebe farki dusunuldugunde bu oran
**(b) siki ile tutarlidir**: bos maske -> bos costmap -> erken donus. Sayi yanlis
demiyorum; **hangi kosulda alindigi bilinmedigi icin kullanilamaz** diyorum.

**4) Kapsam sinirlari (olcum duzgun tekrarlansa bile gecerli).**
`jetson_fps.py:162` `rota_bul(..., plan=False)` cagiriyor — yani **A\* rota
planlama olcum disinda**. Ayrica kilavuz kendi kapsamini soyle yaziyor:
*"Bugunku Jetson testi sunlari kanitlayabilir: kamera aciliyor mu, model
yukleniyor mu, cikarim hizi ne, TensorRT engine derleniyor mu. Sunlari
kanitlayamaz: rota aktarimi, ACK, IKA'nin hareket etmesi."*

**5) Perspektif — panige gerek yok.** Kapsama hesabindan gereken hiz
**0,9-2,6 FPS**. 14 FPS bunun 5-15 kati; olcum duzgun tekrarlandiginda deger
yariya inse bile sartname tarafinda sikinti gorunmuyor. Ustelik sayi **vekil
(zayif) kartta** alindi ve hedef kart Orin NX 16GB — yani gercek deger bunun
ustundedir. Bu yuzden T17 "acik" kalir ama **risk maddesi degildir**; yalnizca
kanit borcudur.

**6) Vekil kartin ASIL degeri hiz degil, YIGIN dogrulamasi.** Nano kosumu su
sorulari zaten cevapladi ya da cevaplayabilir: model yukleniyor mu, kamera
aciliyor mu, zincir uctan uca cokuyor mu, 4 GB'da bellek yetiyor mu. Bunlar
Orin NX gelmeden kapatilabilecek sorulardir ve degerlidir. Kapatamadigi tek sey
**hedef kartin gercek FPS'i** ve **engine derlemesi**dir (T16).

**7) KARSILASTIRMA TABANI DA COKUK — uc PC referansi 48x celisiyor.**
Ayni makinede (RTX 5080), ayni zincirde, ayni imgsz=640:

| dosya | ornek | toplam p50 | FPS |
|---|---:|---:|---:|
| `jetson_paket/PC_REFERANS.md` | **60** | 27,380 ms | **34,04** |
| `results/jetson_fps_pc_smoke/rapor.md` | 3 | 84,535 ms | 11,96 |
| `results/jetson_fps_pc_smoke_dogrulanmis/rapor.md` | **2** | **1402,872 ms** | **0,713** |

**48x fark** ve en kotu sonuc **"dogrulanmis"** adini tasiyor — ad yaniltici,
icerik en guvenilmez olani. Sebep ornek sayisi: 2-3 karelik kosumlar model
yukleme + CUDA baslatma maliyetini olcuyor, kararli hizi degil. `jetson_fps.py`
varsayilanlari **`--isinma 15 --tekrar 120`** ile bunu zaten cozuyor; bu uc kosum
varsayilanin ALTINDA degerlerle yapilmis.

**Sonuc — baglayici:** Jetson sayilari yalniz **60+ ornekli, isinmali** PC
referansiyla (34,04 FPS @640) karsilastirilir. Diger iki dosya karsilastirma
tabani olarak **kullanilmaz**; silinmezler (olcum gecmisi) ama
`ARCHITECT_PLAN.md`'ye taban olarak girmezler. Vekil Nano kosumu da `--isinma`
ve `--tekrar` degerleri kayda gecmeden gecerli sayilmaz — 14 FPS'in dorduncu
bilinmeyeni budur.

---

### D-37 · KRİTİK · K-B güven eşiği gerçek GUI yolunda %100 çekimserlik üretiyor
Bildiren: Codex-2 · 2026-08-10 · T25 uygulama kapısı

`CONTRACTS.md` §6.3/K-B'deki bağlayıcı `ROTA_GUVEN_ESIGI = 0.50`, GUI'nin
gerçek 67-kare zincirinde (`navitas_seg_v21_best.pt`, `imgsz=512`, GUI eşik ve
fallback'leri) ölçüldü. Ham sonuç `52` karar / `15` çekimserdi. Ham kararların
güven dağılımı `min=0.243`, `p50=0.319`, `max=0.363`; eşik sonrası 52 kararın
tamamı `DUSUK_GUVEN` ile reddedildi: `0` karar / `67` çekimser (**%100**).

Yayın güvenliği kapısı doğru çalışıyor: eşik altı karar telde `OPEN_ROUTE`
olmuyor, ACK'li `NO_ROUTE/DUSUK_GUVEN` oluyor. Ancak sözleşmenin kendi
kalibrasyon hükmüne göre bu aşırı çekimserlik **sahada kullanılamaz**. Codex
eşik değerini değiştiremez; Claude 1 gerçek veriyle K-B'yi yeniden
değerlendirip önce `CONTRACTS.md`'yi güncellemeden T25 kapanmamalıdır.

T26 altındaki `52 → 52` tablosu yalnız K-A uç-band kapısını ölçer; K-B güven
eşiğinin önce/sonra sonucu olarak kullanılamaz.

---

### D-38 · ONEMLI · K-B yeniden kalibre edildi (0,50 -> 0,20); metrik gercek veride AYIRT EDICI DEGIL
Bulan: Claude 1 · 2026-08-10 · D-37'nin uzerine, bagimsiz olcum

Codex'in bulgusu (D-37) dogrulandi ve **tam dagilim** cikarildi. Ayni zincir
(v21, `imgsz=512`, GUI esikleri), gercek 67 kare, `data/raw_frames`:

    ham karar: 45 / 67   cekimser: 22   (K-A uc-band kapisi sonrasi)

    GUVEN DAGILIMI (45 kararli kare)
      min 0,2440 · p05 0,2510 · p10 0,2572 · p25 0,2790
      p50 0,3070 · p75 0,3250 · p90 0,3386 · max 0,3520
      ortalama 0,3018   std 0,0304        1/3 tabani = 0,3333

    ESIK SUPURMESI
      esik    gecen  cekimserlik
      0,20      45      %32,8     <- K-A'nin kendi cekimserligi
      0,26      39      %41,8
      0,28      33      %50,7
      0,30      26      %61,2
      0,3333     9      %86,6
      0,3600     0     %100,0

**1) Benim ilk esigim (0,50) olcumsuzdu.** Dayanagi SENTETIK sahne guveniydi
(`0,797` / `1,000`). Gercek karelerde guven **hicbir zaman 0,352'yi gecmiyor**.
Sentetik ile gercek arasindaki bu ayrisma, arena domain boslugunun (bkz. v13/v17
olcumleri) guven metrigindeki karsiligidir.

**2) Asil bulgu: metrik gercek veride ayirt edici DEGIL.** `std = 0,0304` ve tum
kutle 1/3 cevresinde. Esik suurmesinde yumusak gecis yok — 0,30'dan 0,36'ya
%61'den %100'e sicriyor. Buraya secici bir esik koymak kotu karari elemek degil,
**rastgele kare elemektir.**

**3) Ek gozlem: 45 kararin HEPSI `yol=2`.** En dusuk (0,2440) ve en yuksek
(0,3520) kareler dahil. Iki aciklama var ve ayrilmadi:
  (a) kareler genis acik alan gosteriyor; koridor uc seride esit yayiliyor,
      centroid hep ortaya dusuyor — yani dusuk guven "belirsizlik" degil,
      "her yer gecilebilir" demek;
  (b) metrik korlugu.
Ayirt etmek icin **margin tabanli** guven gerekir (secilen serit ile ikinci en
iyi arasindaki fark). `in_third / bx.size` mutlak orani bu isi gormuyor.
Ayri gorev olarak acilmali.

**4) Karar.** `ROTA_GUVEN_ESIGI = 0.20`. K-B artik **secici kapi degil, TABAN
KORUYUCUSU**: olculen en dusuk gecerli karar (0,244) altinda kalir, gercek
kararlari elemez; `guven=0.0` yayinini engelleyerek D-28 kusurunu kapatir;
sentetik yolu (0,797) etkilemez. Guvenligin agirligi **K-A**'dadir — koridorun
uc bantlara temasi olculebilir geometrik bir olgudur.

**5) YAN BULGU — testler sozlesme sabitini CIPLAK yazmis (madde 16 ihlali).**
Esik 0,50 -> 0,20 yapilinca 7 test dustu:

    ERROR: test_karar_sozlesmesi.test_ret_detayi_olculen_deger_ve_esigi_tasir
    FAIL : test_rota_guven_esigi (4 test, ornek: guven=0.499)
    FAIL : test_iha_sender_cli.test_cli_normal_dusuk_ve_acik_no_route_yollari
    FAIL : test_yks_gui ... dusuk_guven_onaya_acilmaz
    Ran 120 tests -> FAILED (failures=6, errors=1)
    (genel kapi codes/test_rota_sentetik.py 15/15 ETKILENMEDI)

Testler `0.499` gibi degerleri **elle** tasiyor. Sabit `ROTA_GUVEN_ESIGI`'nden
turetilseydi esik degisikligi testleri kendiliginden takip ederdi. Bu, madde
16'nin ("ciplak sabit yazilmaz") test tarafindaki karsiligidir ve esigin
kalibrasyon borcu oldugu bilinen bir sozlesmede **ozellikle** onemlidir.
Duzeltme T25 kapsaminda Codex'e birakildi: testler esigi sabitten turetecek
(`ROTA_GUVEN_ESIGI - epsilon` gibi), boylece bir sonraki kalibrasyonda kirilmaz.

---

### D-39 · KRITIK · "yks_gui yol algilamiyor" — IKI AYRI SEBEP, biri K-A/K-B DEGIL
Bildiren: kullanici · 2026-08-10 · olcum: Claude 1

Kullanici GUI'nin hic yol algilamadigini bildirdi. Olculdu: **iki bagimsiz sebep
ust uste biniyor** ve buyuk olani K-A/K-B ile ilgisiz.

**SEBEP 1 (baskin, REGRESYON DEGIL) — model varsayilan kaynakta zemin BULAMIYOR.**
GUI varsayilan kaynagi `gemini` (`yks_gui.py:119`). v21, `imgsz=512`, GUI zinciri:

    [gemini]                zemin%  engel%  silme sonrasi
      1.png                   0,00    0,00   BOS   2816x1536
      10.png 12.png 4.png     0,00    0,00   BOS   1024x559
      2.png                   0,00    1,21   BOS   2048x2048
      11.png 6.png 14.png     0,00   0-1,2   BOS
      -> 8 / 12 kare BOS
    [val]  7 / 12 kare BOS (bircogunda engel VAR ama zemin 0,00)
    [drone] 0 / 12 BOS · zemin %76,8-78,7 · engel ~%25 · silme sonrasi ~%73

Blok maskesi trav'i silmiyor; **zemin maskesi zaten uretilmiyor**. Ayni model
`drone` karelerinde kusursuz calisiyor. Bu, D-21'de kayitli domain boslugunun
GUI'deki dogrudan sonucudur ve K-A/K-B'den ONCE de vardi.

**SEBEP 2 (ikincil, benim degisikligim) — K-A/K-B eleme yapiyor.**
Ayni karelerde HEAD (K-A/K-B oncesi) ile calisma agaci karsilastirildi; girdi
(predict + get_masks) TEK SEFER uretilip iki `analyze_path`'e verildi:

    kaynak    maske bos   ESKI karar   YENI karar   kaybedilen
    gemini      8/12          4            1            3
    val         7/12          3            1            2
    drone       0/12          9            6            3   (%33)

Yani `gemini`'de kullanicinin gordugu sey: 12 karenin 8'inde zaten maske yok,
kalan 4 karardan 3'u de kapidan donuyor -> ekran tamamen olu gorunuyor.

**Degerlendirme.** K-A **dogru calisiyor**: T26'nin amaci "kareyi bastan basa
gecmeyen koridoru acik sayma"ydi ve gemini/val goruntulerinin geometrisi
(kismi koridor, kenara degmeyen alan) bu kapidan dogal olarak donuyor. Kapinin
gevsetilmesi T26 kusurunu geri getirir — YAPILMAYACAK. Ancak:

  a) GUI **red sebebini gostermiyor.** `_rota_kararini_esikle` K-B icin
     `(sebep, detay)` uretiyor ama K-A reddi sessizce `None` donuyor ve ekranda
     yalnizca "TESPIT YOK" yaziliyor. Kullanici "bozuk" ile "kapi kapatti"yi
     ayirt edemiyor. **Hakem ekraninda bu bir kanit butunlugu sorunudur** (S9
     ile ayni sinif).
  b) GUI **varsayilan kaynagi `gemini`** — model orada calismiyor. `drone`
     kaynagi S9'da tam bu yuzden eklenmisti ama varsayilan degistirilmedi.

**OLCUM SINIRI (durustluk notu):** bu olcumde GUI'nin **karolu cikarim** dali
(`yks_gui.py:895-909`, `max(h,w) > 1400` ise 768'lik karolar) taklit EDILMEDI;
dogrudan `predict(imgsz=512)` kullanildi. Bu yalniz buyuk kareleri (2816x1536,
2048x2048, 1600x900) etkiler; **1024x559 gibi karolanmayan kareler de BOS
cikti**, dolayisiyla sonuc karolamadan bagimsiz olarak gecerlidir.

---

### D-40 · KRITIK · `KENAR_GUVENSIZ` kapisi ORNEKLEME PARAMETRESINE duyarli — karar KARARSIZ
Bulan: Claude 1 · 2026-08-10 · kullanici bildirimi uzerine ("2 guzel fotoda kenar guvensiz")

T25/T28 sebep bildirimi calisir hale gelince retlerin dagilimi olculdu:

    [drone]  20 kare :  KENAR_GUVENSIZ 11 (%55) · KARAR 9 (%45)
    [gemini] 20 kare :  MASKE_YOK 14 (%70) · UC_BANT_TEMAS_YOK 3 · KARAR 2 · KENAR 1
    [test]   20 kare :  MASKE_YOK 7 · KARAR 7 · UC_BANT_TEMAS_YOK 4 · BILESEN_YOK 2

**BULGU 1 — sebep etiketi yanlis.** `KENAR_GUVENSIZ` donen vakalarin
**hepsinde uretilen waypoint sayisi 0**. Kenar yokken "kenar guvensiz" denemez.
Dogru ayrim: *"waypoint zinciri hic kurulamadi"* ile *"kurulan zincirin bir
kenari engelden geciyor"* ayri sebeplerdir. Ilki icin ayri bir kod gerekir
(ornegin `GORUS_HATTI_KOPUK` / `WAYPOINT_URETILEMEDI`).

**BULGU 2 (asil) — karar ornekleme parametresine gore SALINIYOR.**
Ayni goruntu, ayni maske; yalniz `n_waypoints` degistirildi:

    kare                8wp    16wp   24wp   32wp  | rota_bul (bagimsiz)
    frame_000002       KENAR  yol2   KENAR  yol2   | BELIRSIZ_COKLU
    frame_000003       yol2   KENAR  KENAR  yol2   | BELIRSIZ_COKLU
    frame_000005       yol2   KENAR  yol2   yol2   | BELIRSIZ_COKLU
    frame_000007       KENAR  KENAR  yol2   KENAR  | BELIRSIZ_COKLU
    frame_000012       KENAR  yol2   KENAR  yol2   | BELIRSIZ_COKLU

    8wp KARAR / 32wp KARAR:  4 kare tutarli ACIK · 5 kare tutarli RET
                             3 kare RET->KARAR · 2 kare KARAR->RET
    -> 14 karenin 5'inde (%36) karar ornekleme sayisina bagli DEGISIYOR.

Sahada kabul edilemez: ayni sahne, ayni maske, farkli karar. `n_waypoints`
bir **performans/cozunurluk** parametresidir; **guvenlik kararini belirlememelidir.**

**BULGU 3 — bagimsiz ikinci gorus tutarli.** `costmap_path_finder.rota_bul`
ayni maskelerde 13/14 karede `BELIRSIZ_COKLU`, 1'inde `ACIK` dedi. Yani
`rota_bul` **kararli**; salinim yalniz `analyze_path`'in kenar kapisinda.
Iki yolun ayni sahnede farkli gerekcelerle reddetmesi S4'un (iki iraksak karar
yolu) somut sonucudur.

**Degerlendirme.** T24 kusuru GERCEKTI ve duzeltme dogru yondeydi (D-28: iki ucu
zemin olan kenar engelin ustunden geciyordu). Ancak duzeltme, kararliligi
ornekleme adimina baglayan bir kapi uretti. Kok neden: waypoint'ler once
bantlardan **ornekleniyor**, sonra aralarindaki duz cizgi engelle sinaniyor.
Koridor kivrimliysa iki bant arasindaki duz cizgi engelden gecebilir — bant
sayisi degisince kesisim de degisir. Yani kapi, koridorun **gecilebilirligini**
degil, **ornekleme geometrisini** olcuyor.

**Yon (mimar onerisi, T30 olarak acildi):** kenar guvenligi waypoint ciftleri
uzerinden degil, koridorun **baglantililigi** uzerinden sinanmalidir —
`rota_bul._bagli_mi` bunu zaten yapiyor ve kararli sonuc veriyor. Waypoint'ler
baglantisi KANITLANMIS bir yol uzerinde uretilirse (A* ya da centerline takibi),
sonradan kenar denetimine gerek kalmaz ve `n_waypoints` yalniz cikti
yogunlugunu etkiler — karari degil.

---

### D-39 · ÖNEMLİ · D-38'deki 45/67 ölçümü güncel GUI karar yolu değil
Bildiren: Codex-2 · 2026-08-10 · T25 kapanış ölçümü

Aynı model (`799e07f9...`), aynı 67 kare, `imgsz=512` ve aynı maskelerle iki karar
yolu tek koşumda karşılaştırıldı:

| karar yolu | karar | çekimser | güven min / p50 / max |
|---|---:|---:|---|
| Güncel GUI: `trav[blok > 0] = 0` → `analyze_path(trav)` | **52** | 15 | `0,243 / 0,3185 / 0,363` |
| Engel son çıkarılır: `analyze_path(zemin, engel_mask=blok)` | **45** | 22 | `0,247 / 0,307 / 0,351` |

D-38'deki `45` ve `p50=0,307` ikinci yolla örtüşüyor; kayıt bunu “GUI zinciri”
diye etiketliyor, fakat `comms/yks_gui.py::_algi_kos` birinci yolu kullanıyor.
`ROTA_GUVEN_ESIGI=0,20` sonucu değişmiyor: **iki yolda da K-B ek ret = 0**.
Bu nedenle eşik kararı geçerli, fakat 67-kare kanıtı iki yolu ayrı adlandıracak
şekilde düzeltilmelidir. Engel çıkarma sırası zaten açık S4 kapsamındadır; T25
içinde sessizce değiştirilmedi.

---

### D-40 · KRİTİK · YKS GUI ham araç maskesini kenar kapısına bağlamıyordu
Bildiren: kullanıcı · doğrulayan/düzelten: Codex-2 · 2026-08-10

Kullanıcı, model araçları doğru etiketlediği hâlde sarı waypoint kenarlarının
araçların üstünden geçtiğini ve düğümler arası mesafenin aşırı uzun olduğunu
bildirdi. Kök neden `comms/yks_gui.py::_algi_kos` çağrı zincirindeydi:

1. `trav[blok > 0] = 0` aracı morfolojiden **önce** oyuyordu.
2. `analyze_path` daha sonra `MORPH_CLOSE` çalıştırıp ince araç boşluğunu geri
   doldurabiliyordu.
3. GUI `engel_mask=blok` vermediği için hem son çıkarma hem ham-engel kenar
   denetimi bu çağrı yerinde devre dışı kalıyordu.
4. Sekiz yatay bant azami edge uzunluğu koymuyordu; gerçek karede tek edge
   `1025,5 px` olabiliyordu.

**Düzeltme:** GUI artık ham `blok` maskesini `analyze_path(...,
engel_mask=blok)` ile son kapıya bağlıyor, 12 aday bandı kullanıyor ve güvenli
segmentleri mevcut `costmap_path_finder._maks_aralikla_bol` yardımcısıyla bir
bant yüksekliğini aşmayacak ara düğümlere bölüyor. Kalın sarı çizginin yalnız
görselleştirme nedeniyle araç etiketinin üstünü boyamaması için engel katmanı
en son çiziliyor.

**Gerçek 67 kare, v21 SHA `799e07f9...`, imgsz=512:**

| | karar | ihlalli kare | ihlalli edge | wp medyan | edge medyan / max |
|---|---:|---:|---:|---:|---:|
| önce | 52 | **13** | **14/364** | 8 | `72,0 / 1025,5 px` |
| sonra | 45 | **0** | **0/1202** | 24 | `33,0 / 46,7 px` |

Yeni `tests/test_yks_gui_rota_engel.py` dört kapı taşır: gerçek `_algi_kos`
çağrı bağını, eski kusurun pozitif kontrolünü, ince tam bariyer fail-closed
reddini, edge bölmeyi ve kalın çizgi/araç katman sırasını doğrular. Hedefli
çıktı `Ran 4 tests · OK`; tam keşif `Ran 125 tests · OK`; genel sentetik kapı
`15/15`, tümü exit `0`.

⚠ **Sınır:** Bu düzeltme etiketlenmiş araç pikseliyle kesişimi sıfırlar. Gerçek
İKA gövde açıklığı için `mpp` ve `R_GEREKLI_M=1,10 m` tabanlı C-space gerekir;
bu mekanizma costmap yolundadır ve açık S4/D-25 mimari migrasyonunun kapsamıdır.
YKS'nin bu görünümü yerel hakem görselleştirmesidir, doğrudan `OPEN_ROUTE`
yayınlamaz.

---

### D-41 · KRİTİK · D-40'ın 12-bant değişikliği geçerli rotayı reddediyor, tam maskede worker sessizce çöküyordu
Bildiren: kullanıcı · doğrulayan/düzelten: Codex-2 · 2026-08-10

D-40 sonrasında kullanıcı "şimdi hiç çalışmıyor" bildirdi. İki bağımsız regresyon
somut olarak yeniden üretildi:

1. `n_waypoints=12`, kenar uzunluğu sınırı değildir ve ara-bant görünürlük
   sezgisini değiştirir. Araçsız gerçek `road_104.jpg` maskesinde 8 bant
   `yol=1, guven=0,465` üretirken 12 bant `None` döndürdü. D-40'ın "12 aday
   bandı" değişikliği geri alındı; üretimle aynı 8 bant korundu. Azami edge
   uzunluğu bundan bağımsız `ALGI_MAKS_KENAR_ORANI=1/12` ile uygulanır.
2. Tamamı geçilebilir maskede OpenCV `distanceTransform` değeri `FLT_MAX`
   olabiliyor; `int(median)` çizgi kalınlığına çevrilince worker
   `int too big to convert` ile düşüyor, dış `except` yalnız günlüğe yazdığı
   için panel sonsuza dek "işleniyor" görünüyordu. Koridor 1 px kapalı sınırla
   pad edilip kırpıldı ve yarıçap görüntü boyutuyla sınırlandı.

Ek savunmalar: panoramik görüntüde waypoint aralığı, geometriyi kesmeden
`MAKS_WP=64` içine sığacak en küçük değere uyarlanır; bölünmüş rota ham engel
maskesine karşı yeniden denetlenir. Geçersiz güven değerinin yazı formatlaması
worker'ı düşüremez. Her beklenmeyen worker hatası artık ayrı `hata` paketiyle
ALGİ panelinde görünür; yalnız loga gömülmez.

**Güncel gerçek 67 kare:** 45 karar / 22 çekimser / **0 runtime hata**;
başarılı rotalarda edge max `43,28 px` (limit `48 px`), waypoint max `52`
(limit `64`). `road_104.jpg` yeniden `1·SOL, güven 0,47`; ilk gerçek drone
karesi `2·ORTA, güven 0,33` üretir.

**Kapılar:** `test_yks_gui_rota_engel.py` → `Ran 7 tests · OK`; tam keşif →
`Ran 128 tests · OK`; `codes/test_rota_sentetik.py` → `15/15`; GUI `--help`
exit `0`; `git diff --check` exit `0`. D-40'taki 12-bant ve 4/125 test kaydı bu
ek kayıtla düzeltilmiştir; D-40'ın ham araç maskesi kök nedeni geçerliliğini korur.

---

### D-42 · KAPATILDI · Rota reddi artık hakem ekranı, artefakt ve NO_ROUTE yolunda kanonik
Bildiren/düzelten: Codex-2 · 2026-08-10 · T25/T28

`analyze_path` önceden bütün yapısal retleri sessiz `None` ile birleştiriyordu.
Geriye uyumlu `return_reason=True` seçeneği eklendi; varsayılan 3 eleman ve
`return_clean=True` 4 eleman ariteleri değişmedi. Opt-in dönüşün son elemanı
§6.4'teki `MASKE_YOK`, `BILESEN_YOK`, `UC_BANT_TEMAS_YOK`,
`ALAN_YETERSIZ`, `KENAR_GUVENSIZ` veya K-B `DUSUK_GUVEN` kodunu, ölçülen
ayrıntısıyla taşıyor. Yapısal ret, güven eşiği tarafından ezilmiyor.

İki çağrı-yeri kopukluğu da ölçülerek kapatıldı: GUI analizden önce zemini
engelle oyup kaynak bilgisini kaybetmiyor; ham zemin ve engeli ayrı geçiriyor.
`iha_perceive` sınıf-1 engel maskesini analizöre iletiyor. Sentetik yatay bariyer
bu bağlantıdan önce `road=2` üretirken artık `UC_BANT_TEMAS_YOK`, `road=None`,
`waypoints=[]` üretiyor. GUI'de boş maske, bariyer ve düşük güven üç ayrı panel,
günlük ve banner metnidir. Yapısal sebep/detay, `IhaSender` + protokol
encode/decode yolunda tek `NO_ROUTE` olarak değişmeden korunur.

**Gerçek veri:** v21 SHA `799e07f9cef3820c3ad9f0365b0052fd8ee2edfc6df1b706830a0a9d3bc5be7d`,
67 drone karesi, GUI `imgsz=512` eşik zinciriyle `45 karar / 22 ret / 0 hata`;
22 retin tamamı `KENAR_GUVENSIZ`, sebepsiz ret yoktur. Kabul güveni
`0,247 / 0,307 / 0,351` (min/p50/max).

**Koşulan kapılar (tümü exit 0):** `test_rota_ret_nedenleri.py` 10/10,
`test_yks_gui_rota_engel.py` 7/7, `test_rota_guven_esigi.py` 8/8,
`test_*rota*.py` 36/36, tam keşif 138/138, sentetik rota 15/15,
`py_compile` ve `git diff --check` temiz.

---

### D-43 · KRİTİK · Rota kararı waypoint örnekleme sayısından ayrıldı
Bildiren: Claude 1 · düzelten: Codex-2 · 2026-08-10 · T30

T30 öncesi güvenlik kararı yatay bantlardan seçilen waypoint geometrisine bağlıydı.
Aynı 14 gerçek maskede `n_waypoints={8,16,24,32}` karşılaştırıldığında dört ayarın
tamamı hesaba katılınca **10/14 kare salınıyordu**; tarihsel `5/14` yalnız 8 ile 32
uçlarını karşılaştırıyordu. Toplam 29/56 retin tamamı ara bant adayının bulunamaması
nedeniyle oluştu; henüz kenar yokken yanlış `KENAR_GUVENSIZ` etiketi veriliyordu.

**Düzeltme:** `analyze_path`, en büyük koridorun başlangıç–hedef bağlantısını tam
çözünürlükte doğruladıktan sonra muhafazakâr MIN-havuzlu A* ile somut bir witness
yolu çıkarır. Kaba ızgara yol bulamazsa adım tam çözünürlüğe kadar küçülür; üretilen
zincirin bütün segmentleri tekrar tam maskede doğrulanır. `n_waypoints` ancak bu
kanıtlanmış kanonik yol üzerinde çıktı yoğunluğu olarak kullanılır ve karara girmez.
Witness kurulamaması `GORUS_HATTI_KOPUK`, kurulmuş zincirin son doğrulamadan
geçememesi `KENAR_GUVENSIZ` olur. T24'ün ham engel ve segment postcondition'ı
kaldırılmadı; mutasyon testi ihlalli witness'ı hâlâ reddediyor.

**Gerçek 14 kare, v21 SHA `799e07f9...`, imgsz=512:** 56 analyze çağrısında
karar/reason salınımı **0/14**, komşu ayarlar arasında **0/42**; her n için 14/14
`yol2`. Toplam 1.053 segmentte LOS ihlali ve ham engel teması **0**. Analyze
p50/p95/max `82,272 / 101,806 / 105,012 ms`.

**Gerçek 67-kare GUI zinciri:** 67/67 karar, 0 ret, 0 exception, yol2=67. GUI'nin
son densify zincirindeki 1.329 segmentte LOS/ham engel ihlali **0**; waypoint
min/p50/max `19/21/21`, en uzun edge `45,967 px` (`h/12=48 px`). Analyze
p50/p95/max `78,892 / 112,268 / 131,167 ms`. `road_104.jpg` yol1, güven `0,465`,
20 waypoint ve 0 ihlal üretir.

**Kapılar (tümü exit 0):** `test_analyze_path*.py` 20/20,
`test_rota_ret_nedenleri.py` 10/10, `test_rpi_letterbox.py` 5/5,
`test_yks_gui_rota_engel.py` 7/7, `test_rota_guven_esigi.py` 8/8;
tam keşif `Ran 141 tests in 27.333s · OK`; sentetik rota `15/15`; `py_compile`
ve `git diff --check` temiz.

⚠ **Sınır:** Bu düzeltme waypoint kararlılığı ile piksel-segment güvenliğini kapatır.
Çoklu koridorun görev-semantik seçimi ve `mpp/R_GEREKLI_M` tabanlı fiziksel İKA
gövde açıklığı mevcut S4/D-25 mimari kapsamındadır.

---

### D-44 · DÜZELTME · D-43'ün sınırsız A* ve uç-ankraj kapanış kayıtları güncellendi
Bildiren: bağımsız Codex denetimi · düzelten: Codex-2 · 2026-08-10 · T30

D-43 ilk uygulama ölçümüdür; kök neden ve `n_waypoints` ayrımı geçerlidir, ancak
kapanıştan önce iki ek kusur bulundu. Kaba plan hücresinin merkezi gerçek hedef
bandının dışında kalabiliyor, koşulsuz tam-çözünürlük fallback'i ise 512² dar-geçit
sahnesinde worker'ı **5,941 s** bloke ediyordu. D-43'teki “tam çözünürlüğe kadar”
ifadesi, performans ve endpoint güvenliği bakımından yürürlükte değildir.

**Son düzeltme:** A* zincirinin ilk ve son waypoint'i plan hücresi merkezine değil,
aynı hücredeki gerçek alt/üst tohum pikseline ankrajlanır ve kanonik dönüşten önce
üyelik yeniden doğrulanır. Bütün A* denemelerinin toplam bütçesi sözleşmeli
`ROTA_PLAN_MAKS_HUCRE=32768` plan hücresidir. Daha ince ızgara bütçeye sığmıyorsa
algoritma `GORUS_HATTI_KOPUK` ile fail-closed döner. Dar-geçit reprosu güncel kodda
`233,6 ms`, `20480/32768` hücre ve güvenli ret üretir.

**Güncel kaynak SHA `AF75CE176B313B8B...`; gerçek 14 kare:** 56/56 çağrı `yol2`,
karar/reason salınımı `0/14`, komşu geçiş `0/42`, endpoint-band ihlali `0/56`;
1.059 segmentte LOS/ham engel ihlali `0`. Analyze p50/p95/max
`88,299 / 111,716 / 144,223 ms`.

**Güncel 67-kare GUI zinciri:** 67/67 karar, 0 ret/hata, endpoint-band ihlali
`0/67`; 1.333 segmentte LOS/ham engel ihlali `0`; waypoint min/p50/max
`20/21/21`, en uzun edge `45,967 < 48 px`. Analyze p50/p95/max
`81,666 / 100,423 / 144,223 ms`; plan listesi azami `30692/32768` hücre.
`road_104.jpg` yine yol1, güven `0,465`, 20 waypoint ve 0 ihlal üretir.

**Güncel kapılar (tümü exit 0):** `test_analyze_path*.py` 22/22,
`test_rota_ret_nedenleri.py` 10/10, `test_rpi_letterbox.py` 5/5,
`test_yks_gui_rota_engel.py` 7/7, `test_rota_guven_esigi.py` 8/8;
tam keşif `Ran 143 tests in 28.172s · OK`; sentetik rota `15/15`; `py_compile`
ve `git diff --check` temiz. D-43'teki 20/141 test sayıları ile eski süre/segment
sayıları bu ek kayıtla düzeltilmiştir.

---

### D-41 · KRITIK · Rota DOGRU, ADI YANLIS: `road` etiketi 67/67 karede rotanin gectigi seride uymuyor
Bulan: Claude 2 (arastirma turu) · 2026-08-10 · kayit ve degerlendirme: Claude 1

`analyze_path` rotayi DOGRU buluyor ama yayinladigi `road` etiketini centroid'den
tureterek YANLIS hesapliyor. Olculdu: **67 karenin 67'sinde** centroid seridi,
piksel-kutlesi argmax seridinden farkli:

    frame_000000  yayin_yol=2 guven=0,326 | serit oranlari=[0,382, 0,326, 0,292] argmax=1 marjin=0,056
    frame_000003  yayin_yol=2 guven=0,272 | serit oranlari=[0,406, 0,272, 0,322] argmax=1 marjin=0,084
    marjin < 0,10 : 66/67 (%99)

Enjekte-kapi deneyinde (bilinen cevap) rotanin bariyer satirindaki dugumu
**serit-1**'den geciyor, yayinlanan etiket ise **2**.

**NEDEN KRITIK — bu bir gorsellestirme kusuru DEGIL.** `road` tel sozlesmesinin
alanidir ve IKA'nin PLANLAMA GIRDISIDIR:

    comms/protocol.py:31,39,51   open_route(road, ...) -> "road", "label"
    comms/ika_receiver.py:11     if route: plan_path(route["road"])
    comms/README.md:84           hedef_yol = route["road"]  # A* bunu kullanir
    comms/yks_gui.py:445         acik = self.rota["road"]
    comms/yks_gui.py:453-462     secili serit YESIL, digerleri KIRMIZI = gidilemez

Yani hakem ekrani, olculen 67 karenin hepsinde **rotanin gercekten gectigi seridi
KIRMIZI (gidilemez)** boyayip yanindakini yesil gosteriyor; ayni yanlis etiket
IKA'ya da gidiyor. Sartname §5.3.2/§6.2: yanlis guzergah **0 puan**.

**Guven metrigi de yanlis yerden olculuyor.** `in_third / bx.size` (`rpi_inference.py:274`)
yalniz ust %30 bandindan hesaplaniyor ve:
  - secilen seridin payi bile degil (ekrandaki 0,326; en yuksek pay 0,382);
  - tespit KOTULESTIKCE YUKSELIYOR — cok az piksel tek ucte-bire duserse oran 1,0
    olur. Ham tespit sayaci: `drone` 0/67 karede sinif-0 tespiti sifir (saglikli),
    `val` 18/40, `gemini_road` 14/40, `gemini_arena` 6/15 karede SIFIR tespit;
    bu bos karelerde guven paradoksal olarak yuksek cikiyor.
  - D-38'in onerdigi **marjin** metrigi de kurtarmiyor: ayni ust banttan
    hesaplandigi surece std(marjin)=0,029 ~ std(in_third)=0,029 (drone).
    **Sorun istatistigin sekli degil, NEREDEN olculdugudur.**

**S4 (iki iraksak karar yolu) ACIKLANDI — kusur degil, kapsam farki.**
`costmap_path_finder.py:781`:

    if tani["belirsiz"] and tani["n_kapi"] != 3:
        cikti["durum"] = "BELIRSIZ_COKLU"

`rota_bul` bir **UC-KAPILI ARENA dedektorudur** (3 kapi bekler); `analyze_path`
**tek-koridor** dedektorudur. Ayni 67 maskede rota_bul 66 `BELIRSIZ_COKLU` / 1
`ACIK` demesinin sebebi budur — tespit edilen kapi sayisi 3..10 arasinda
dagiliyor. Ikisi farkli SORULARI cevapliyor; ayrisma beklenen davranistir.

**val'daki "olu ekran" da kapinin DOGRU calismasidir.** GT ile esleştirmeli olcum
(40 kare): TP 18 · dogru negatif 13 · gercek kacirma 5 · FP 4. 18 dogru tespitin
15'i `UC_BANT_TEMAS_YOK` ile dondu, cunku RescueNet karesinde yol serit halinde
kareyi keser ve alt/ust uc bantlara temas etmez — K-A tam bunu elemek icin var.

**Sonuc — mimar degerlendirmesi:** rota bulma motoru saglam; bozuk olan **kanit
zinciri**. Sistem dogru yolu buluyor, ona yanlis isim veriyor ve urettigi guven
sayisi gorevi tanimlayan degiskenle iliskili degil. Gorevler: **T31** (road
etiketi) ve **T32** (guven metrigi).

---

### D-45 · COZULDU · T31/T32 uygulandi: `road` ve guven artik ROTADAN olculuyor
Bulan/duzelten: Claude 2 · 2026-08-10 · gorevler T31 (KRITIK) + T32
Kanit: D-41. Kod: `codes/rpi_inference.py`, `codes/karar_sozlesmesi.py`,
`comms/yks_gui.py`, `tests/test_rota_serit_etiketi.py`.

**Degisen sey.** `analyze_path` artik karari koridorun ust %30 bandindan degil,
DOGRULANMIS witness rotasindan okuyor. Sira degisti: witness A* ve kenar kapisi
ONCE kosuyor, serit ve guven SONRA turetiliyor. Olcum waypoint DUGUMLERINDEN
degil segmentlerin LINE_8 piksellerinden yapiliyor (`_rota_pikselleri`), boylece
`n_waypoints` karara giremiyor (SS6.4/5). Rasterizasyon `_gorus_hatti` ile ayni
kaynaktan (`_bresenham_noktalari`) — ikinci yuvarlama uretilmedi.

**T31 — iki aday tanim OLCULDU.**

    (a) darbogaz seridi  : rotanin EN DAR gectigi serit
    (b) baskin serit     : en cok rota pikseli tasiyan serit
    (c) ust uc seridi · (d) alt uc seridi  (ek adaylar)

Enjekte-kapi deneyi (3 gercek kare x 2 bariyer kalinligi x 3 serit x 2 kapi
genisligi = 36 senaryo, 28 karar / 8 ret) DORT tanimi da AYIRT EDEMEDI:

    (a) 28/28 · (b) 28/28 · (c) 28/28 · (d) 28/28 · ESKI centroid 12/28 (%43)

Sebep olculdu: bu sahnelerde ve 67 gercek karede rota HIC serit degistirmiyor
(`cok_seritli` 0/67). Bu yuzden AYIRT EDICI sahne kuruldu — alt ve ust uc
serit 3'te, tek gecis serit 1'deki dar kapidan (yer gercegi = 1):

    kapi_px   (a)darbogaz  (b)baskin  (c)ust  (d)alt   guven   seritler(1,2,3)
       16          1            3        3       3     0,032   (381, 600, 632)
       24          1            3        3       3     0,032   (377, 600, 636)
       32          3            3        3       3     0,063   (377, 600, 636)
       48          1            3        3       3     0,032   (365, 600, 638)
       64          1            3        3       3     0,044   (351, 600, 642)

    (a) 4/5 dogru · (b) 0/5 · (c) 0/5 · (d) 0/5

**SECIM: (a) darbogaz seridi.** Gerekce iki katmanli:
  1. OLCUM — serit degisen sahnede dogru cevabi veren TEK tanim odur;
  2. ANLAM — darbogaz, IKA'nin gecemedigi yerdir. (b)/(c)/(d) aracin cogunlukla
     nerede oldugunu soyler; NEREDE KALABILECEGINI soylemez. Fail-closed tercih
     kritik gecisi adlandirmaktir.
  (a)'nin 1/5 kaybi (kapi_px=32) kok neden degil: o sahnede rota, kanal
  koselerinde duvara 2 px yaklasiyor ve gercek darbogaz gercekten serit 3'te.
  Uretimde bu senaryolarin HEPSI zaten K-B'den donuyor (guven 0,032-0,063 <
  0,20) — etiket telde hic gorunmuyor.

**COK SERITLI ROTA — tek etiketin yetersizligi kayda gecti.** Rota birden fazla
seride giriyorsa tek `road` alani rotayi anlatmaz. Karar YUMUSATILMADI (rota
dogrulanmis, yalniz ADI eksik); bunun yerine `_rota_serit_olcumu` `cok_seritli`
ve serit basina piksel dagilimini dondurur, hakem ekrani ikisini de basar ve
sari uyari gunlugu yazar. Yeni bir ret sebebi EKLENMEDI — eklemek dogrulanmis
gecerli rotayi reddetmek olurdu (kullanilabilirlik kaybi, guvenlik kazanci yok).

**T32 — guven metrigi.** Yeni tanim: rota boyunca olculen EN KUCUK aciklik
(distance transform yaricapi), icerik genisligine ORAN olarak
(`ROTA_DARBOGAZ_TAM_ORANI = 0.035`, `karar_sozlesmesi.rota_darbogaz_guveni`).
Mutlak piksel degil oran — cozunurluk degisince olcut kaymaz (SS8); kapi testi
ayni sahneyi 2x cozunurlukte kosup ayni karari dogruluyor.

Normalizer OLCUMLE secildi (67 gercek kare, std maksimumu):

    N       std      p50    doygun(=1,0)   K-B 0,20'de cekimserlik
    0,020  0,3862   1,000      42/67            14/67 (%21)
    0,028  0,4022   1,000      35/67            15/67 (%22)
    0,035  0,4029   0,809      31/67            18/67 (%27)   <- secildi
    0,040  0,4019   0,708      28/67            18/67 (%27)
    0,050  0,3999   0,566      25/67            22/67 (%33)

Fiziksel capa da ayni yeri gosteriyor: 50 m'lik icerik genisliginde 0,035 x W
yaricap ~1,75 m, yani `R_GEREKLI_M = 1,10 m`'nin ~1,6 kati — "rahatca genis"
noktasi. K-B esiginde guven 0,20 ~ 0,35 m yaricap: hala TABAN KORUYUCUSU.

**Ayirt edicilik — once/sonra (ayni kareler, ayni model, tek degisken metrik):**

    kaynak         n   pearson(guven, model_tespit_guveni)      std
                          ESKI          YENI            ESKI      YENI
    drone         67     -0,173        +0,333          0,0287    0,4029
    gemini_road   11     -0,397        +0,158          0,2903    0,3914
    val            3     -0,577        -0,577          0,0014    0,1296   (n=3, anlamsiz)

Eski metrigin negatif korelasyonu ("tespit kotulestikce guven yukseliyor")
iki kaynakta da POZITIFE dondu; dagilim genisligi drone'da 14 kat arti.

**KOSULAN KAPILAR (gercek cikti).**

    KAPI 1  enjekte-kapi, bilinen cevap : kapi serit 1/2/3 -> road 1/2/3
            (kalici test: tests/test_rota_serit_etiketi.py)
    KAPI 2  67 gercek kare               : road ROTANIN uzerinde 67/67
                                           UYUMSUZ 0/67   (onceden 67/67)
                                           road dagilimi {1: 32, 3: 35}
    KAPI 3  POZITIF KONTROL (mutasyon)   : serit tekrar centroid'den alininca
                                           UYUMSUZ 67/67 GERI GELDI,
                                           dagilim yine {2: 67}
    KAPI 4  T32, sinif-0 tespiti SIFIR   : 8/82 kare · karar 0 · azami guven 0,0
    KAPI 5  codes/test_rota_sentetik.py  : 15/15 · exit 0
    KAPI 6  unittest discover -s tests   : Ran 190 tests · OK · exit 0
    EK      comms/test_comms.py exit 0 · yks_gui.py --help exit 0 · py_compile temiz

**YAN BULGU — TIKAYICI · D-01'in tekrari: Jetson ikizi 456 satir BAYATTI.**
`jetson_paket/kod/rpi_inference.py` kanonik `codes/rpi_inference.py` ile
ayrisikti; icinde T24 (kenar guvenligi), T28 (ret sebepleri), T30 (witness
yolu) ve T31/T32 kusurlarinin HICBIRININ duzeltmesi yoktu. Jetson, kapatildigi
sanilan KRITIK kusurlarla ucacakti. Sebep olculdu: `tests/test_jetson_comms_paketi.py`
KOPYALAR sozlugu yalniz haberlesme dosyalarini kilitliyordu; **karar motoru
listede degildi.** Jetson'a ozgu icerik yok (fark tamamen eski surum), kopya
guvenle senkronlandi ve `rpi_inference.py` + `costmap_path_finder.py` KOPYALAR
sozlugune EKLENDI — kapi artik bunu goruyor.

**ACIK KALAN — durustluk notu.** Yeni guven GEOMETRIKTIR, ALGISAL DEGILDIR.
D-41'in "tespit kotulestikce guven yukseliyor" bulgusunun tamami kapanmadi:

    test_images/gemini/6.png         model tespit maks 0,0894 -> ESKI 1,000 · YENI 0,837
    test_images/gemini/road_127.jpg  model tespit maks 0,0821 -> ESKI 1,000 · YENI 0,502

Model 0,089 guvenle GENIS bir blob uretirse geometri saglikli gorunur. Kapanmasi
icin `boxes.conf` degerinin `get_masks` uzerinden karara tasinip
`conf = min(geometrik, algisal)` yapilmasi gerekir; bu ayri gorevdir (T33
onerisi), T32 kapsaminda DEGILDI ve sessizce yapilmadi.

**Ayrica acik:** `analyze_path`'in `distanceTransform`'u goruntu disini hala
SERBEST sayiyor (`rpi_inference.py`; GUI cizim yolu 1 px cerceveyle duzeltmis).
Olculdu: dist maks 308,7 -> 129,0 px, uc waypoint x 1016 -> 918. Bu, rota
GEOMETRISINI degistirir; T30'un kanitlanmis kararliligini ayni degisiklikte
bozmamak icin T31/T32 kapsamina ALINMADI — ayri gorev olarak durmali.

⚠ **KAYIT NUMARASI CAKISMASI (uclucu oldu):** `D-39`, `D-40` ve `D-41` bu
dosyada IKI kez kullanildi (`D-41` icin :2213 ve :2355). `CONTRACTS.md` SS6.4
basligi "D-39"a atif veriyor ve hangisi oldugu belirsiz. Kayitlar silinmez
(madde 6); ikinci ucluye `b` soneki verilip atiflarin duzeltilmesi gerekiyor.

---

### D-46 · ÖNEMLİ · T20-b'nin kalıntısı: ekran doğrulamadığı §6.4 iddiasını "✓" ile basıyor

**Bağlam.** T20-b `t_iha1`'i (operatör UI kronometresi) sürüş izni kilidinden
çıkardı; sürüş izninin otoritesi artık yalnız doğrulanmış protokol latch'i
`iha_landed_seq`. Bu düzeltme doğrudur ve mimar denetiminden geçti (4/4 kapı,
gerçek UDP baytlarıyla ölçüldü). Ancak `t_iha1` **başka bir yerde** hâlâ bilgi
kaynağı olarak kullanılıyor.

**Bulgu.** `comms/yks_gui.py:772`:

    havada = (" · AKTARIM HAVADA TAMAMLANDI ✓ (§2.2.3)" if not self.t_iha1
              else " · ⚠ aktarım İHA inişinden SONRA (§6.4 geçersizlik riski)")

`t_iha1` yalnız `iha_indi()` içinde kuruluyor (`:1293`), o da `t_iha0` yoksa
`:1291`'de erken dönüyor. Operatör ARM → FIRLATMA dizisini basmadıysa İHA
**gerçekten inmiş olmasına rağmen** `t_iha1` `None` kalır.

**Ölçüm — koşuldu (Claude 1, 2026-08-11):**

    t_iha1 = None | landed_seq = 8802 (IHA GERCEKTEN INMIS)
    EKRAN: Hakem onayı tam — ACK(seq=8801) İHA'ya iletildi
           · AKTARIM HAVADA TAMAMLANDI ✓ (§2.2.3)

Yani **bilgi yokluğu onaya çevriliyor**: `t_iha1` boşluğu iki farklı gerçeği
(«İHA henüz inmedi» ve «İHA indi ama operatör düğmeye basmadı») tek bir "✓"
altında topluyor.

**Neden T20-b'nin kendisi değil, kalıntısı.** T20-b'den önce `t_iha1` boşken
İKA zaten hareket edemiyordu, dolayısıyla bu ekran hâli fiilen ulaşılamazdı.
Düzeltmeden sonra "operatör dizisi basılmamış" **canlı bir çalışma kipi** oldu.
Kusur T20-b tarafından ÜRETİLMEDİ, **erişilebilir hâle getirildi**.

**Sınıf.** S9 ile aynı: hakem ekranının doğrulamadığı bir şeyi iddia etmesi.
Karar güvenliği (fail-closed) etkilenmiyor — kilit sağlam; etkilenen **kanıt
dürüstlüğü**. Şartname §6.4 aktarımın havada tamamlanmasını istiyor; bunu
doğrulayamadığımız bir durumda "TAMAMLANDI ✓" basmak hakemi yanıltır.

**Görev:** `TASK_QUEUE.md` **T34**. Üçüncü durum ("BİLİNMİYOR") eklenecek;
karar yolu değiştirilmeyecek.

---

### D-47 · KRİTİK · Gönderilemeyen komut hakem ekranında BAŞARILI görünüyor

**Bulgu.** `comms/yks_gui.py:_cmd_gonder()` başarısızlıkta doğru davranıp
`False` dönüyor, ancak **4 çağrı yerinin 3'ü dönüş değerini yok sayıyor**:

    :1272   self._cmd_gonder("ARM", "iha")        # dönüş yok sayılıyor
    :1277   self._cmd_gonder("DISARM", "iha")     # dönüş yok sayılıyor
    :1387   self._cmd_gonder("PARACHUTE", "iha")  # dönüş yok sayılıyor
    :1320   if not self._cmd_gonder("IKA_GO", "ika"): return   # DOĞRU kalıp

**Ölçüm — koşuldu (Claude 1, 2026-08-11), İHA adresi henüz öğrenilmemiş:**

    link.send cagrildi mi : False   (ARM TELE CIKMADI)
    EKRAN                 : SİSTEM: ARM — uçuşa hazır
    FIRLATMA butonu       : normal
    ic durum arm_acik     : True
    gunluk                : ['CMD GÖNDERİLEMEDİ → iha: ARM — UDP adresi yok']

Yani tek bir soluk günlük satırı dışında **her gösterge başarı bildiriyor**.

**Üç ayrı sonuç, üçü de ciddi:**

1. **PARAŞÜT (§2.2.4) — en tehlikelisi.** `parasut()` gönderim düşse bile
   ekrana "PARAŞÜT AÇILDI (manuel)" yazıyor, butonu `state="disabled"` yapıyor
   ve −50 cezayı işliyor. Buton kapandığı için **operatörün tekrar deneme yolu
   da kapanıyor.** Acil durumda operatör paraşütün açıldığına inanır.
2. **DISARM — ters yönde ölümcül.** Gönderim düşerse ekran "DISARM — güvenli"
   der; İHA hâlâ ARM'lıdır. Emniyet iddiası doğrulanmamıştır.
3. **ARM — zincirleme yanıltma.** FIRLATMA butonu açılır, operatör basar,
   §6.4 uçuş kronometresi **hiç başlamamış bir uçuş için** işlemeye başlar.

**Sınıf.** S9, T34 ve D-46 ile aynı aile: hakem ekranının doğrulamadığı bir
durumu ilan etmesi. Fark: bunlar yalnız gösterge değil, **operatörün emniyet
kararını** besliyor.

**Görev:** `TASK_QUEUE.md` **T37**.

---

### D-48 · KRİTİK · Hakem ekranı kendi çıkarım hattını yazmış; üretimden 67/67 ayrışıyor

**Bulgu.** `yks_gui._algi_kos()` (`:999-1035`) çıkarım parametrelerini **çıplak
sabit** olarak taşıyor ve üretim yolundan yapısal olarak ayrışıyor:

| Parametre | `rpi_inference` / `iha_perceive` | `yks_gui` |
|---|---|---|
| `imgsz` | `INFER_SIZE = 512` / `CANON = 1024` | çıplak `512` |
| letterbox | `_letterbox_square` **var** | **YOK** — ham görüntü |
| zemin eşiği | `conf = 0.15` | çıplak `0.30` → fallback `0.05` |
| engel eşiği | — | çıplak `0.10` |
| `min_area_ratio` | `0.01` (varsayılan) | çıplak `0.02` |

**Ölçüm — koşuldu (Claude 1, 2026-08-11), 67 gerçek drone karesi:**

    toplam 67 kare · AYNI 0 · IRAKSAK 67 (%100.0)
    SONUC: HAKEM EKRANI URETIMDEN AYRISIYOR (67/67 kare)

Hakem ekranı her karede "rota açık" derken üretim parametreleri aynı kareyi
her seferinde `UC_BANT_TEMAS_YOK` ile reddediyor. **Hakemin ekranda gördüğü
karar, sahada koşacak kodun vereceği karar değildir.**

**Anayasa madde 16 ihlali.** Eşikler ve çözünürlük tek kaynaktan okunmuyor.
T8'de `analyze_path`'in ıraksak kopyası için verilen karar birebir geçerli:
ölçüm/gösterim yolu üretim yolundan ayrı olamaz.

**Sıra uyarısı.** Önce D-49/T35. Aksi hâlde GUI'yi üretime hizalamak ekranı
"doğru ama 67/67 reddeden" bir hâle sokar.

**Görev:** `TASK_QUEUE.md` **T36**.

---

### D-49 · KRİTİK · D-25'in kökü bulundu: üretim yolu letterbox içerik kutusunu geçirmiyor → %100 ret

**Bağlam.** D-25 ve saha kuru koşusunun `rota DUSTU` halkası
("letterbox'li girdide durum=KAPALI_DAR, ayni maske kirpilinca durum=ACIK")
bugüne kadar bir *belirti* olarak kayıtlıydı. Kök neden izole edildi.

**Ölçüm — dört kollu izolasyon, koşuldu (Claude 1, 2026-08-11), 16 gerçek kare:**

    kol                           ACIK  ret dagilimi
    A ham 512   (hakem ekrani)    16/16  —
    B ham 1024                    16/16  —
    C lbox 1024 icerik YOK         0/16  UC_BANT_TEMAS_YOK=16
    D lbox 1024 icerik VAR        16/16  —

- **A vs B → `imgsz` suçsuz.** 512 ile 1024 aynı sonucu veriyor. S5 kapsamındaki
  çözünürlük kırılganlığı bu kusurun sebebi DEĞİL.
- **B vs C → suçlu letterbox.** Tek fark dolgu; sonuç 16/16 açıktan 0/16'ya düşüyor.
- **C vs D → çözüm zaten kodda.** `analyze_path` `icerik=` parametresini taşıyor
  (`codes/rpi_inference.py:523`); geçirilince 16/16 geri geliyor.

**Kök neden.** `analyze_path`, letterbox'ın gri dolgusunu içerik sanıyor. K-A'nın
başlangıç/hedef uç bantları (`HEDEF_BANT_ORANI = 0.08`) tuvalin en üst/en alt
%8'inden hesaplanınca **dolgunun içine** düşüyor; hiçbir koridor banda değemiyor
→ `UC_BANT_TEMAS_YOK`. Kusur K-A'da değil, **K-A'ya yanlış çerçeve verilmesinde**.

**Ağırlığı.** `simulation/scripts/iha_perceive.py:106` üretim çağrısı `icerik=`
geçirmiyor. Yani üretim algı yolu gerçek karelerin **%100'ünü** reddediyor —
sahada rota hiç üretilmez. D-25 bir köşe durumu değil, **tam kapanmadır**.

**Not.** Hakem ekranının letterbox yapmaması bu kusurdan tesadüfen kaçıyor;
bu bir çözüm değil, D-48'deki ıraksamanın sebebi.

**Görev:** `TASK_QUEUE.md` **T35** (T36'dan ÖNCE).

---

### D-50 · T35 zorunlu saha kapısı izin verilen dosyaların dışında kaldı

**Tarih:** 2026-08-11 · **Uygulayıcı:** Codex-2 · **Karar:** görev zorlanmadı,
`[ ]` bırakıldı; üretim kodu değiştirilmedi.

**Gerçek kapı koşumu:**

    O:\navitas-local-train\venv\Scripts\python.exe -B scripts/saha_kuru_kosu.py

İlgili gerçek çıktı:

    kamera             DUSTU
    model_yukleme      DUSTU
    cikarim            GECTI
    maske              GECTI
    olcek              SAHIPSIZ
    hedef_konumu       SAHIPSIZ
    rota               DUSTU      letterbox'li girdide durum=KAPALI_DAR, ayni maske kirpilinca durum=ACIK — tohum bandi dolguya dusuyor
    aktarim            GECTI
    surus_izni         GECTI
    motor              SAHIPSIZ

    GECTI 4 · DUSTU 3 · SAHIPSIZ 3 · ATLANDI 0
    KOPUK HALKALAR (6): kamera, model_yukleme, olcek, hedef_konumu, rota, motor
    Zincir saha kosumunda TAMAMLANMAZ.
    Cikti: O:\navitas\results\saha_kuru_kosu_20260811_123127
    EXIT_CODE=1

**Yapısal kanıt:** `scripts/saha_kuru_kosu.py` içindeki `rota` halkası,
T35 için yazma izni verilen `simulation/scripts/iha_perceive.py` veya
`codes/rpi_inference.py` yolunu çağırmıyor. Doğrudan
`costmap_path_finder.rota_bul(maskeler, mpp=None)` çağrısını yapıyor; `icerik`
değeri bu çağrıya taşınmıyor. `codes/costmap_path_finder.py` içindeki `rota_bul`
imzasında da `icerik` parametresi yok. Bu nedenle yalnız izin verilen iki üretim
dosyasını değiştirerek zorunlu `rota GECTI` kapısını etkilemek mümkün değil.

**Ek depo denetimi:** Mevcut `iha_perceive._infer` tam tuval maskelerini
`analyze_path` çağrısından önce `(x0, y0, nw, nh)` alanına kırpıyor. Dolayısıyla
orijinal tuval kutusunu zaten kırpılmış `nh × nw` maskeye doğrudan vermek koordinat
sistemlerini karıştırır. Tam tuval üzerinde `icerik=` kullanılması isteniyorsa dış
API'yi korumak için analizden sonra maske/içeriğin yeniden kırpılması ve waypoint
koordinatlarının içerik uzayına çevrilmesi gerekir.

`codes/rpi_inference.py` denetiminde letterbox kullanan üç üretim akışının üçü de
`_preprocess` tarafından döndürülen `icerik` kutusunu `analyze_path` çağrısına
zaten aktarıyor; eksik çağrı bulunmadı (`3/3`).

**Gerekli mimari kapsam genişlemesi:** Zorunlu saha kapısını düzeltmek için en az
`codes/costmap_path_finder.py` ve `scripts/saha_kuru_kosu.py` dosyalarında içerik
kutusu sözleşmesinin taşınmasına izin verilmesi gerekiyor. Dört kollu ölçümdeki
"aynı 16 kare" dosya listesi/koşum komutu depoda kayıtlı olmadığından birebir aynı
küme de bu koşumda doğrulanamadı. İlk zorunlu kapı düştüğü için diğer T35 kapıları
geçmiş ilan edilmedi.

---

### D-51 · DÜZELTME · D-48 ve D-49 yanlıştı: kusurlu yol `iha_perceive` değil `rota_bul`

**Kim buldu.** Codex-2, T35'i **zorlamadı** — `[ ]` bıraktı, üretim kodunu
değiştirmedi ve yapısal itirazını D-50'ye kanıtıyla yazdı. İtirazı ölçtüm;
**haklı**. Aşağısı benim kaydımın düzeltmesidir (madde 6: kayıt silinmez,
düzeltme eklenir).

**Hatanın kaynağı.** D-48/D-49 ölçümlerimde üretim yolunu **yeniden kurdum**
(letterbox + `analyze_path`) — gerçek fonksiyonu çağırmadım. Gerçek
`iha_perceive._infer` maskeleri `analyze_path`'e vermeden **önce** içerik
kutusuna kırpıyor (`simulation/scripts/iha_perceive.py:92-94`):

    return content, {0: masks[0][y0:y0 + nh, x0:x0 + nw],
                     1: masks[1][y0:y0 + nh, x0:x0 + nw]}

Yani dolgu `analyze_path`'e hiç ulaşmıyor. Benim "kol C"m üretimi temsil
etmiyordu. **T8'in dersini kendim ihlal ettim: ölçüm yolu üretim yolundan ayrı
olamaz.**

**Yeniden ölçüm — GERÇEK fonksiyonlar çağrıldı (16 kare):**

    yol                                              ACIK  ret dagilimi
    E iha_perceive._infer (letterbox + KIRPMA)      12/16  DUSUK_GUVEN=4
    F _preprocess + rota_bul (saha kuru kosusu)      0/16  KAPALI_DAR=16
    rota_bul imzasinda `icerik` var mi : False

**D-49 DÜZELTMESİ:**
- ✗ Yanlış: *"`iha_perceive.py:106` içerik kutusunu geçirmiyor → %100 ret."*
  `iha_perceive` kırpıyor ve **12/16 rota üretiyor**; kusurlu değil.
- ✓ Doğru: kusurlu yol `rpi_inference._preprocess` → `costmap_path_finder.rota_bul`.
  **0/16**, hepsi `KAPALI_DAR`. `rota_bul` imzasında `icerik` parametresi
  **hiç yok** (`codes/costmap_path_finder.py:729-730`) — sözleşme orada mevcut
  değil, geçirilmemiş değil.
- Ret sebebi de farklı: benim kurgumda `UC_BANT_TEMAS_YOK`, gerçek yolda
  `KAPALI_DAR`. Kök neden yönü (letterbox dolgusu geometriyi bozuyor) ayakta,
  **mekanizma farklı**: dolgu içeriği küçülttüğü için `r_gerekli_px` oranı
  bozuluyor.
- Sonuç: T35 için verdiğim kapı (`saha_kuru_kosu.py` → `rota GECTI`) izin
  verdiğim iki dosyadan **yapısal olarak ulaşılamazdı**. Kapı hatası bana aittir.

**D-48 DÜZELTMESİ — büyüklük yanlıştı, bulgu ayakta:**

    ONCE (kurgu ile) : toplam 67 kare · AYNI  0 · IRAKSAK 67 (%100.0)
    SIMDI (gercek)   : toplam 67 kare · AYNI 46 · IRAKSAK 21 ( %31.3)

Ayrışma yönü: hakem ekranı rota açıyor, üretim `DUSUK_GUVEN` ile reddediyor.
Madde 16 ihlali ve parametre tablosu **aynen geçerli**; yalnız oran %100 değil
**%31,3**. Bu hâliyle bile ciddi: hakem her üç kareden birinde sahada
verilmeyecek bir kararı görüyor.

**Ders (yeni değil, tekrarlanan).** Bir üretim yolunu ölçerken onu yeniden
kurmak, ölçülen şeyin ne olduğunu belirsizleştirir. D-33'ün ("depo otoritedir")
ölçüm karşılığı: **üretim fonksiyonu otoritedir, yeniden kurgusu değil.**

**Görevler:** T35 yeniden yazıldı (hedef `rota_bul`, dosya izni genişletildi).
T36 büyüklük düzeltmesiyle güncellendi.

---

### D-52 · T35 yeniden tanımındaki `16/16 AÇIK` kapısı fail-closed kararla çelişiyor

**Tarih:** 2026-08-11 · **Uygulayıcı:** Codex-2 · **Karar:** görev zorlanmadı,
`[ ]` bırakıldı; üretim ve test kodu değiştirilmedi.

**Gerçek ölçüm komutu:**

    O:\navitas-local-train\venv\Scripts\python.exe -B -

Standart girdiye verilen ölçüm gövdesi, görevde kayıtlı sıralı ilk 16 kareyi ve
`models/navitas_seg_v21_best.pt` modelini kullandı. Zincir gerçek üretim
fonksiyonlarıyla kuruldu:

    rpi_inference._preprocess
    model.predict(..., imgsz=rpi_inference.INFER_SIZE, conf=0.25)
    rpi_inference.get_masks
    rpi_inference._maskeleri_icerige_kirp
    costmap_path_finder.rota_bul(..., mpp=None, plan=False)

İçerik sözleşmesinin mevcut API'deki birebir güvenli eşdeğeri için
`_preprocess` tarafından döndürülen `(x0, y0, w, h)` kutusu yeniden hesaplanmadan
kullanıldı; aynı maskeler bu kutuya kırpılıp `rota_bul` gerçek fonksiyonuna verildi.
Gerçek çıktı:

    [T35_F_ONCE] kare=16 ACIK=0 dagilim={'KAPALI_DAR': 16}
    [T35_F_ROI_ESDEGERI] kare=16 ACIK=1 dagilim={'ACIK': 1, 'BELIRSIZ_COKLU': 15}
    [T35_F_ROI_KAPI] n_kapi_dagilimi={3: 1, 8: 2, 7: 3, 6: 8, 9: 2}
    EXIT_CODE=0

**Sonuç:** İçerik kutusu kusuru gerçektir: doğru uç bantları ilk kareyi
`KAPALI_DAR` durumundan `ACIK` durumuna taşır ve saha kuru koşusunun kullandığı
ilk kareyi onarabilir. Ancak zorunlu F kapısının beklediği **16/16 AÇIK** sonucu
yalnız içerik sözleşmesiyle oluşmuyor. On beş karede gerçek karar
`BELIRSIZ_COKLU`; algoritma beklenen üç yerine 5–9 kapı görüyor. Bu kararları
`ACIK` saymak, mevcut fail-closed çoklu-kapı semantiğini değiştirmek olur.

**Ölçek denetimi:** Letterbox işlevi içeriği ölçeklemiyor, yalnız dolgu ekliyor;
içerik piksel ölçeği değişmiyor. `r_gerekli_px` tuval veya içerik boyutundan
değil yalnız `R_GEREKLI_M / mpp` formülünden gelir (`CONTRACTS.md` §5). İçerik
oranından yeni bir fiziksel ölçek türetmek sözleşmeye aykırıdır. Karar semantiği
değiştirilmeden yapılan gerçek maske taramasında `r_gerekli_px=0.6188, 1.1,
1.4667, 1.9556, 2.2, 3.9111, 20.1143` değerlerinin hiçbiri 16/16 üretmedi; en
iyi ölçülen sonuç 6/16 AÇIK oldu.

**Madde 15 için güvenli onarım hazırdır ama kapıyı kapatmaz:** `rota_bul`a geriye
uyumlu `icerik=None` eklenmesi; `serbest = zemin AND NOT engel` sonrasında yalnız
ROI ile çıkarma yapılması; aday ve A* varsayılan tohumlarının
`hedef_bant_yuksekligi(icerik_h)` ile içerik uçlarından kurulması. Bu tasarım
serbest alanı büyütmez. Buna rağmen gerçek ölçüm 1/16'da kalır.

**Gerekli mimari karar:** Ya F kapısı, fail-closed sonucu koruyarak gerçek
`1 ACIK + 15 BELIRSIZ_COKLU` dağılımını kabul edecek şekilde ayrıştırılmalı; ya da
5–9 maske parçasını üç fiziksel güzergâha birleştirecek yeni ve test edilebilir
bir koridor-kümeleme sözleşmesi, sabitleriyle birlikte mimar tarafından
tanımlanmalıdır. Ölçülmemiş bir birleştirme kuralıyla 16/16 zorlanmamalıdır.

İlk zorunlu kapı düştüğü için saha kuru koşusu, 15/15 ve tam unittest kapıları
bu T35 denemesi adına geçmiş ilan edilmedi.

---

### D-53 · KRİTİK · Ölçüm zemini yanlış: `data/raw_frames` HTAB arenası değil, OTOPARK

**Kim zorladı.** Codex-2, T35'i **ikinci kez** zorlamadı (D-50, D-52). İkinci
itirazı kapımın kendisineydi. Doğruladım: **üç noktada da haklı**, ve itirazı
beni bunların hepsinden daha büyük bir şeye götürdü.

**1 · Mekanizma açıklamam yanlıştı (üçüncü kez).** T35'te *"dolgu içeriği
küçültünce `r_gerekli_px` oranı bozuluyor"* yazdım. Kodda doğrulanmadı:

    rpi_inference._preprocess:844-849 → yan = max(h, w); tuval = full((yan,yan,3),114)
        → ÖLÇEKLEME YOK, yalnız dolgu. İçerik piksel ölçeği değişmiyor.
    costmap_path_finder:107,111 → m = 1.0 if mpp is None; r_gerekli_px = r_gerekli_m / m
        → tuval veya içerik boyutundan BAĞIMSIZ (mpp=None iken sabit 1.10 px).

Codex-2'nin `CONTRACTS.md` §5 atfı doğru. Mekanizmayı belirtiden türettim,
türetimi okumadım.

**2 · `16/16 AÇIK` kapım T4'ün ters yüzüydü.** T4'te *"sıfır rota varken GEÇTİ"*
diye kusur yazmıştım. Burada tersini yaptım: **her karede rota isteyen** bir kapı
kurdum. Codex-2'nin ölçümü içerik sözleşmesinin `KAPALI_DAR ×16` → `ACIK ×1 +
BELIRSIZ_COKLU ×15` yaptığını gösteriyor; kapıyı tutturmak için `BELIRSIZ_COKLU`
kararlarını `ACIK` saymak gerekirdi — yani **fail-closed semantiğini bozmak.**
Bir amelenin ölçülmemiş bir kuralla kapı tutturmasını istemek benim hatamdı.

**3 · Asıl bulgu: ölçüm zemini yanlış.** `data/raw_frames` karelerine baktım
(`whatsapp_video_2026_07_30_at_11_44_03` ve `..._11_44_39`, ikisi de aynı sahne):

> **Bir OTOPARK.** Onlarca park hâlinde araç, bir bina, ağaçlar, asfalt.
> HTAB arenası **değil**. Şartnamenin tanımladığı 3 işaretli güzergâh **yok**.

`rota_bul` tam olarak şunu diyor (`costmap_path_finder.py:780-782`):

    if tani["belirsiz"] and tani["n_kapi"] != 3:
        cikti["durum"] = "BELIRSIZ_COKLU"
        cikti["sebep"] = f"{tani['n_kapi']} kapi tespit edildi (3 beklenir)."

Bir otoparkta 5–9 açıklık görüp **çekimser kalması DOĞRU DAVRANIŞTIR**, kusur
değil. `yol_no` `None` kalıyor, rota yayınlanmıyor — fail-closed çalışıyor.

**Zincirleme sonuçlar:**

- **T35'in zorunlu kapısı geçersizdi.** `scripts/saha_kuru_kosu.py` → `rota`
  halkasının GECTI olmasını istemek, dedektörden **bir otoparkın içinden
  güzergâh üretmesini** istemek demekti. Codex-2 iki kez haklı olarak reddetti.
- **Saha kuru koşusunun `rota` halkası bu girdiyle ASLA meşru şekilde geçemez**
  (`saha_kuru_kosu.py:250` → `data/raw_frames`). Kusur `rota_bul`'da değil,
  halkanın **zemininde**. Yeni görev: **T38**.
- **D-48'in yönü tersine döndü.** "Hakem ekranı açıyor, üretim `DUSUK_GUVEN` ile
  reddediyor" ayrışmasında **yanlış olan taraf hakem ekranıdır**: `analyze_path`
  (tek-koridor) bir otoparkta koridor buluyor, `rota_bul` (üç-kapı arena)
  çekimser kalıyor. Ayrışma gerçek, ama T36 "GUI'yi üretime hizala" yönünde
  okunmalı — üretimi GUI'ye değil.
- **T33 çok daha ciddileşti.** Otopark, *"araç zemin olarak etiketleniyor"*
  kusurunun (S1, D-21) azami hâli. Hakem ekranı bu karelerde rota açıyorsa rota
  büyük olasılıkla **park hâlindeki araçların üstünden** geçiyor. Ölçülmedi;
  T33 kapsamında ölçülmeli.

**Ders.** D-33 *"depo otoritedir"* demişti; D-51 *"üretim fonksiyonu otoritedir,
yeniden kurgusu değil"* ekledi. Bu kayıt üçüncüsünü ekliyor:
**ölçüm zeminine BAKMADAN ondan çıkarılan hiçbir sayı yorumlanamaz.**
Bu projede aynı 67 kare üzerinden T31, T32, D-37, D-38, D-48 ölçüldü ve hiçbirinde
zeminin bir otopark olduğu yazılmadı. Bu kareler **model davranışı** için geçerli
kanıttır; **görev kararı** için değil.

---

### D-54 · T35 üçüncü deneme: güvenli kod geçti, tam paket izinsiz kanonik aynada düştü

**Tarih:** 2026-08-11 · **Uygulayıcı:** Codex-2 · **Karar:** görev zorlanmadı,
`[ ]` bırakıldı; deneme kodu ve deneme testi geri alındı.

Onaylanan güvenli tasarım geçici olarak uygulandı: `rota_bul(..., icerik=None)`,
`serbest = zemin AND NOT engel` sonrasında yalnız ROI ile çıkarma ve hem aday hem
A* varsayılan tohumlarının `hedef_bant_yuksekligi(icerik_h)` üzerinden kurulması.
`codes/rpi_inference.py` içinde `rota_bul` çağrısı bulunmadığı doğrulandı; bu
dosyada uydurma bir sarmalayıcı eklenmedi. Regresyon sahnesi `_preprocess` tarafından
döndürülen kutuyu yeniden hesaplamadan taşıdı.

**Gerçek 16-kare karar-kalitesi koşumu:**

    O:\navitas-local-train\venv\Scripts\python.exe -B -

Standart girdi ölçüm gövdesi görevde kayıtlı sıralı ilk 16 kareyi,
`models/navitas_seg_v21_best.pt`, `imgsz=512`, `conf=0.25` ve gerçek
`_preprocess -> predict -> get_masks -> rota_bul(mpp=None, plan=False)` zincirini
kullandı. Gerçek çıktı:

    [T35_KUME] kare=16 model=models/navitas_seg_v21_best.pt imgsz=512 conf=0.25
    [T35_ONCE] ACIK=0 | KAPALI_DAR=16 | KAPALI_KOPUK=0 | BELIRSIZ_COKLU=0 | BELIRSIZ_TEK_KAPI=0 | MASKE_YOK=0
    [T35_SONRA] ACIK=1 | KAPALI_DAR=0 | KAPALI_KOPUK=0 | BELIRSIZ_COKLU=15 | BELIRSIZ_TEK_KAPI=0 | MASKE_YOK=0
    [T35_GECIS] KAPALI_DAR->ACIK=1 | KAPALI_DAR->BELIRSIZ_COKLU=15
    [T35_KALITE] KAPALI_DAR=16->0 serbest_artan=0 belirsizden_acilan=0 geometri_esdegeri_olmayan_acilma=0 belirsiz_coklu_fail_closed=15
    EXIT_CODE=0

Bu çıktı karar gevşemesi olmadığını gösterdi: `BELIRSIZ_COKLU` olan 15 karenin
tamamında `yol_no=None` ve waypoint boş kaldı. Tek `ACIK` geçişi aynı maskenin
gerçek içerik kırpığında da `ACIK` olduğu için geometri düzeltmesiyle eşdeğerdi.
Serbest piksel kümesinde büyüme olmadı.

**Geçen odak ve genel rota kapıları:**

    O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -p test_costmap_letterbox_icerik.py -v
    Ran 6 tests in 0.199s
    OK
    EXIT_CODE=0

    O:\navitas-local-train\venv\Scripts\python.exe -B codes/test_rota_sentetik.py
    SONUC: 15/15 dogru
    [OK] TUM DETERMINISTIK SAHNELER GECTI
    EXIT_CODE=0

**Düşen zorunlu tam paket kapısı:** İlk sandbox koşumundaki Windows TEMP izin
hataları ölçüm sayılmadı; komut gerçek TEMP erişimiyle sandbox dışında yeniden
çalıştırıldı:

    O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -q
    FAIL: test_paket_kopyalari_kanonik_kaynaklarla_birebir
          (hedef='costmap_path_finder.py')
    AssertionError: paket kopyasi bayat: costmap_path_finder.py
    Ran 208 tests in 32.925s
    FAILED (failures=1)
    EXIT_CODE=1

**Kök neden ve yetki engeli:** Tam paket, `codes/costmap_path_finder.py` ile
`jetson_paket/kod/costmap_path_finder.py` dosyalarının bayt eşitliğini zorunlu
kılıyor. T35 üçüncü tanımının dosya izni Jetson paket aynasını kapsamıyor. Testi
zayıflatmak veya bayat paketi kabul etmek doğru değildir. Bu nedenle görev
`READY_FOR_REVIEW` yapılmadı. Geri alma sonrasında iki dosyanın SHA-256 değeri
yeniden eşittir:

    0591E1DF34B3BBFB5EC3CA01073953D4DFC294F4728039F471D912A0823F1156

**Bir sonraki deneme için kod-inceleme şartı:** İçerik kutusu kısmen tuval dışına
taşıyorsa veya kesirli/bool/bozuk biçimdeyse sessizce kırpılıp kabul edilmemeli;
`_preprocess` zaten tam sınır içi tamsayı kutu üretir. Verilen geçersiz kutular
boş ROI ile fail-closed `MASKE_YOK` üretmeli ve bu durumlar test edilmelidir.

T35'in tamamlanması için en az
`jetson_paket/kod/costmap_path_finder.py` kanonik aynasına yazma izni gerekir.
Commit veya push yapılmadı.

---

### D-55 · ÖNEMLİ · T27 denetimimde kaçırdım: paket üreteci, parite testinin kapsadığı iki dosyayı üretmiyor

**Nasıl çıktı.** Codex-2 T35'i **üçüncü kez** zorlamadı (D-54). Bu kez kapı
değil **dosya izni** engeldi ve engelin kökü benim denetimimde kaçırdığım bir
tutarsızlık.

**Bulgu — kendim doğruladım:**

    scripts/jetson_paket_hazirla.py:15-22  KOPYALAR = { 6 dosya }
        karar_sozlesmesi · protocol · link · iha_sender · inis_kaniti · iha_inis_yayinci

    tests/test_jetson_comms_paketi.py:24-25  KOPYALAR ek olarak:
        codes/rpi_inference.py        -> paket/rpi_inference.py
        codes/costmap_path_finder.py  -> paket/costmap_path_finder.py

**Parite testi 8 dosyayı zorunlu kılıyor; üreteç 6 dosya üretiyor.** Kalan iki
dosya hâlâ **elle kopya**. Dolayısıyla `codes/rpi_inference.py` veya
`codes/costmap_path_finder.py`'ye dokunan her görev tam paketi düşürüyor ve tek
çözüm elle kopyalamak oluyor — **T27'nin kaldırmayı amaçladığı kırılganlığın ta
kendisi.**

**Benim hatam.** T27'yi 2026-08-10'da denetlerken 7/7 sha eşitliğini kendim
hesapladım ve "paket artık üretiliyor, kopya-dosya kırılganlığı yapısal olarak
kapandı" diye kapattım. **Üretecin listesi ile testin listesinin aynı olup
olmadığını kontrol etmedim.** İki liste ayrı yerlerde elle tutuluyor; sessizce
ıraksadılar. Sha eşitliğini doğrulamak, *eşitliği kimin sürdürdüğünü*
doğrulamaz.

**Sonuç.** T35 üç turdur ilerleyemiyor ve üçünde de sebep benim görev
tanımımdı: (1) yanlış hedef dosya (D-51), (2) fail-closed'u bozan kapı (D-52/53),
(3) parite aynasını kapsamayan dosya izni (bu kayıt). Codex-2 üçünde de kodu
zorlamadı ve kanıtla geri verdi — **istenen davranış tam olarak budur.**

**Görev:** `TASK_QUEUE.md` **T39** (üreteç ve test tek listeden okusun), T35'in
önüne alındı.

**Kalıcı kural (`AGENTS.md`'ye taşınacak):** `codes/` altındaki kanonik saha
modüllerinden birine dokunan her görev, `scripts/jetson_paket_hazirla.py`'yi
**yeniden koşmak zorundadır**; dosya izni Jetson aynasını da kapsamalıdır.

---

### D-56 · KARAR · Arena çekimi iptal; yerine kompozit zemin — ve kapanmayan sınır

**Karar (2026-08-11, kullanıcı).** Kurulu arenanın ≥30 m nadir çekimi uzun süre
yapılamayacak. `TASK_QUEUE.md` `FAZ 0-B` içindeki `[REQUIRES_HUMAN: ARENA CEKIMI]`
satırı **kaldırıldı** — `auto_orchestrator.py:31` bu satırı ilk taramada süresiz
beklerdi ve tüm insan kuyruğunu tıkardı. Kaldırma gerekçesi kayıtta duruyor;
görev gizlenmedi, **kapatıldı**.

**Neden bir alternatif şart.** D-53: elimizdeki tek gerçek ölçüm zemini
(`data/raw_frames`) bir **otopark**. Arena mantığı — üç kapı, uç bant teması,
güzergâh seçimi — bu zeminde **sınanamıyor**. Üç turdur T35 bunun bedelini ödedi.

**Değerlendirilen ve ELENEN seçenek: saf sentetik arena.** `dataset/sentetik_arena`
mevcut ve arena geometrisi taşıyor. Ama modelleri **bu üretecin verisiyle
eğitiyoruz**; aynı dağılımla test etmek dairesel olur ve bakir küme sayılmaz.

**Seçilen: kompozit zemin (T40).** `scripts/copy_paste_augmentation.py` gerçek
zemin üzerine `1=engel` ve `2=hedef` poligonları yapıştırıyor (S1'de araç kâhini
DOTA OBB'ye geçirildi). Sonuç: **gerçek görüntü istatistiği + kontrollü arena
semantiği + tam yer gerçeği.** Yer gerçeği elimizde olduğu için ilk kez
*beklenen kararı bilerek* kapı kurabiliyoruz — bugüne kadar hiçbir arena
ölçümünde bu yoktu.

**T40'ın en kritik tasarım kuralı.** Arka plan bir otopark: park hâlindeki
araçlar **engel katmanına girmek zorunda**. Girmezse v16'yı arena moloza basma
oranında %2,7'den %31,6'ya çökerten *"etiketsiz engel"* hatası birebir tekrarlanır.
Kâhin **DOTA OBB**, COCO değil (ölçüldü: aynı karede 2'ye karşı 93 araç).

**🔴 KAPANMAYAN SINIR — hiçbir raporda gizlenmeyecek.**
Gerçek 30 m arena karesi olmadan **modelin gerçek arenadaki başarımı
doğrulanamaz.** Ölçülmüş gerçek (K-3): mAP arena sıralamasını **tersine
çeviriyor** — mAP lideri v13 arenada en kötü, en düşük mAP'li v17 arenada en iyi.
Dolayısıyla kompozit veya sentetik zeminde iyi olan bir modelin arenada iyi
olacağı **kanıtlanmış değildir**.

T40 **karar mantığını** sınanabilir kılar. **Model başarımını sınamaz.**
Bu ayrım FDR/FDA belgelerinde de açıkça yazılmalıdır; aksi hâlde "arena test
edildi" ifadesi doğrulanmamış bir iddia olur — S9/T34/D-47 ile aynı kusur sınıfı,
bu kez belge düzeyinde.

**Ucuz insan alternatifi (bloke etmez, istendiğinde yapılabilir):** 20×20 m yerine
~2×2 m maket — karton moloz + kırmızı bez H, balkon/çatı/merdivenden nadir açıyla
telefon çekimi. Ölçek farkı `mpp` ile normalize edilir. Gerçek ışık, gölge ve
doku sağlar; domain boşluğunu **daraltır**, kapatmaz. Kuyruğa görev olarak
eklenmedi — kullanıcı imkân bulursa değerlendirilecek.

---

### D-57 · ÖNEMLİ · T35 sözleşmeyi getirdi, kusuru KAPATMADI — kapsamı ben dar tuttum

**Bağlam.** Codex-2 T35'i dördüncü turda tamamladı (önceki üçünde haklı olarak
reddetmişti: D-50, D-52/53, D-54/55). Sözleşme doğru ve güvenli.

**Bağımsız denetimim — Codex-2'nin raporuna bakmadan, gerçek zincirle koştum:**

    1 · DURUM DAGILIMI
      icerik GECIRILMEDEN (bugunku hal)  KAPALI_DAR=16
      icerik GECIRILINCE                 ACIK=1 | BELIRSIZ_COKLU=15
    2 · MADDE 15   serbest pikseli ARTAN kare : 0
    3 · FAIL-CLOSED  BELIRSIZ_COKLU olup yol/waypoint URETEN kare : 0
    4 · GECERSIZ ICERIK KUTUSU (tasan / negatif / kesirli / sifir alan / bool)
        -> hepsi durum=MASKE_YOK  yol_no=None

Dört kapının dördü geçti. 4. madde Codex-2'nin kendi eklediği şarttı: bozuk kutu
sessizce kırpılmıyor, fail-closed `MASKE_YOK` üretiyor.

**Kapanmayan kısım.** Sözleşme **hiçbir çağrı yerine bağlanmadı**. Altı üretim
çağrısının tamamı `icerik` geçirmiyor (`jetson_fps.py` ×2 kopya ·
`kamera_dogrula.py` · `saha_kuru_kosu.py` ×2 · `v21_degerlendir_ve_paketle.py` ·
`iha_haritala.py`). Saha yolu bugün hâlâ **16/16 `KAPALI_DAR`** üretiyor.

**Bu Codex-2'nin eksiği değil, benim kapsam kararım.** Üçüncü tanımda dosya
iznini bilerek dar tuttum ve `jetson_paket/kod/` için "elle düzenlenmeyecek"
dedim — `jetson_fps.py` ve `kamera_dogrula.py` üretilen dosya olmadığı için bu
onları fiilen kilitledi.

**Neden yine de doğru kayıt.** T35'i *"saha rotası düzeldi"* diye kapatmak, tam
olarak bu turda üç kez kapattığımız kusur sınıfı olurdu (S9 · T34 · D-47:
doğrulanmamış iddia). T35 **sözleşme var ve güvenli** demektir, o kadar.
Saha kuru koşusunun `rota` halkası hâlâ `DUSTU`.

**Yan bulgu — T39'un kusur SINIFI tam kapanmadı.** T39 iki listeyi tek kaynağa
indirdi (test artık `KOPYALAR`'ı üreteçten içe aktarıyor + `assertEqual(8, ...)`
koruması). Ancak paket dizininde **dokuzuncu bir ikiz** var ve sözleşmenin
dışında:

    paket dosyasi        uretecte?  ikiz                     durum
    jetson_fps.py        HAYIR      scripts/jetson_fps.py    AYNI
    kamera_dogrula.py    HAYIR      —                        (ikizi yok)

Bugün bayt-eşitler; bunu zorlayan hiçbir şey yok. D-01 ve D-55'in aynısı.
**T41** kapsamına alındı (liste 8 → 9).

**Görev:** `TASK_QUEUE.md` **T41**.

---

### D-58 · KRITIK · "Uretim yolu" TEK degil: iki uretim hatti 13/67 karede birbirinden ayrisiyor
Bulan: Claude 2 · 2026-08-11 · T36 sirasinda · olcum: 67 gercek kare, v21, tek kosum

T36 "hakem ekranini uretime hizala" diyor. Hizalamadan once **hangi uretim**
sorusunu olctum; cunku iki aday var ve **birbirlerinden de ayrisiyorlar**:

    R = codes/rpi_inference.py::run_image govdesi (:920-932)
        _preprocess letterbox -> predict(imgsz=INFER_SIZE=512, conf=0.30)
        -> get_masks (min_conf YOK) -> _maskeleri_icerige_kirp (dolgu SIFIRLANIR,
        tuval boyutu KALIR) -> analyze_path(icerik=VAR) -> _rota_kararini_esikle

    P = simulation/scripts/iha_perceive.py::_infer (:72-115)
        _letterbox_square(imgsz=CANON=1024) -> predict(conf=CONF_FLOOR=0.05)
        -> get_masks(min_conf=0.15) + taban esik fallback -> maskeler ICERIGE
        KIRPILIR (tuval boyutu GIDER) -> analyze_path(icerik YOK) -> K-B

    R ile P ayni maskeden AYNI mi? -> AYNI 54/67 · FARKLI 13/67 (%19,4)
      R dagilimi: {1: 26, 3: 31, DUSUK_GUVEN: 10}
      P dagilimi: {1: 22, 3: 26, DUSUK_GUVEN: 19}
    Farklarin ikisi SERIT farki (ayni sahnede R=3, P=1):
      frame_000014_000000672   R=(3, None)  P=(1, None)
      frame_000016_000000720   R=(3, None)  P=(1, None)
    Kalan 11'i "biri karar veriyor, digeri DUSUK_GUVEN" bicimindedir.

**Neden onemli.** T36'nin kapisi P'yi zincir olarak yaziyor. Ama `CONTRACTS.md`
SS11.2 Halka 3 (Cikarim) ve Halka 4 (Maske) sahibini **`codes/rpi_inference.py`**
yaziyor ve ikisi de **GECERLI**; SS11.1/1 ise *"`simulation/` altindaki hicbir
dosya sahip yazilamaz"* diyor. Yani gorevin kapisi ile sozlesme celisiyor.

**Karar (gerekceli).** Hakem ekrani **R'ye** hizalandi. Uc gerekce:
  1. SS11.2 sahibi R'dir; P sozlesme geregi sahip OLAMAZ.
  2. `jetson_paket/kod/rpi_inference.py` R'nin **bayt-birebir** kopyasidir
     (D-45'te kilitlendi) — yani **saha donanimi R'yi kosuyor**. `iha_perceive.py`
     saha paketinde hic YOKTUR.
  3. Hakem ekrani sartname SS2.2.3/SS6.2 geregi kanit belgesidir; sahada
     kosmayan bir yola hizalanirsa hakem sahada verilmeyecek karari onaylar.

**Kalan is (bu gorevin kapsaminda DEGIL):** R ile P'nin kendi arasindaki 13/67
ayrisma acik durumdadir. Ayrica `iha_perceive.DEFAULT_MODEL` hala
`navitas_seg_v2_best.pt` (v2) gosteriyor — uretim modeli v21'dir (D-20).
Ikisi de `simulation/` altinda oldugu icin bu turda dokunulmadi.

---

### D-59 · TIKAYICI · Arena kompozitinde karar zinciri KUSURSUZ maskeyle bile 7/7 reddediyor
Bulan: Claude 2 · 2026-08-11 · T36 Gorev 2 kapisi · kanit: yer gercegi maskeleri

T40'in urettigi `data/arena_kompozit` ilk kez **yer gercegi olan** uc-seritli
arena sahnesi veriyor (7 kare, manifest'te `arena.acik_serit`). Hakem ekrani
kaynagi eklendi; kapi "7/7 gosterilen serit == manifest" istiyordu.

**Olculen: UYUMLU 1 · UYUMSUZ 5 · CEKIMSER 1.** Kapi DUSTU.

Kok neden **GUI'de degil, modelde de degil**. Ayni 7 kare, modelin yerine
manifest'in KENDI zemin/engel maskeleri (kusursuz yer gercegi) verildi:

    ORACLE (yer gercegi maskesi) -> analyze_path + K-B
      DOGRU 0/7 · YANLIS 0/7 · RET 7/7
      6 kare DUSUK_GUVEN (guven 0,028 / 0,028 / 0,028 / 0,028 / 0,117 / 0,056)
      1 kare UC_BANT_TEMAS_YOK

K-B esigi (`ROTA_GUVEN_ESIGI = 0.20`) uygulanmadan HAM serit:

      DOGRU 4/7 · YANLIS SERIT 2/7 · YAPISAL RET 1/7

Yani: (a) karar mantigi arena geometrisinde ham hâlde 4/7 dogru, (b) K-B o
kararlarin **hepsini** eliyor.

**Neden guven bu kadar dusuk — olculdu.** T32 metrigi rotanin darbogazidir ve
alti karenin dordunde darbogaz **1,0 px**. Bu bir goruntu-kenari artefakti
DEGIL: darbogaz noktalari kenardan 117-214 px iceride ve `distanceTransform`'a
1 px kapali cerceve eklemek degeri degistirmiyor (1,0 -> 1,0). Rota **gercekten**
molozun kenarini siyiriyor. Sebep zincirin yukarisinda: `analyze_path`'te
C-uzayi sismesi YOK; `yol_duzelt`in gorus-hatti kisayolu pikselin SERBEST
olmasini ariyor, ACIKLIGI degil. Fiziksel govde acikligi `rota_bul`'un
`r_gerekli_px` yolundadir ve o da `mpp`'ye baglidir — SS11.2 Halka 5 **SAHIPSIZ**
(D-22). Uc acik kayit burada birlesiyor: Halka 5 yok -> C-uzayi yok -> rota
molozu siyiriyor -> darbogaz ~1 px -> K-B her arena karesini reddediyor.

**K-B supurmesi (arena kompoziti, yer gercegi maskesi, karar veren 6 kare):**

    esik 0,02 -> gecen 6/7      esik 0,10 -> gecen 1/7
    esik 0,03 -> gecen 2/7      esik 0,12 -> gecen 0/7
    esik 0,05 -> gecen 2/7      esik 0,20 -> gecen 0/7   <- YURURLUKTEKI

**Bu, D-37'nin yeni metrik uzerinde tekrari.** `0.20` degeri D-45'te acikca
"eski metrikten devralinamaz, yeniden kalibre edilmeli" diye isaretlenmisti;
otopark karelerinde %27 cekimserlik makul gorunuyordu. Arena yer gercegi
gelince goruldu ki ayni esik **arenada %100 cekimserlik** uretiyor.

**Yapilmadi, cunku dogru cozum esigi dusurmek DEGIL:** 0,03'e cekmek 6/7 karari
gecirir ama bu kararlarin ikisi zaten YANLIS SERIT ve hepsi 1 px acikligi olan
rotalar — yani fiziksel olarak surulemez rotalari yayinlamis oluruz. Once
C-uzayi (Halka 5 + `r_gerekli_px`) kapatilmali, sonra K-B o metrige gore
kalibre edilmelidir. Esigi tek basina oynatmak sartname SS5.3.2 acisindan
cekimserlikten daha tehlikelidir.

**Gorev durumu:** T36 Gorev 2'nin GUI tarafi tamamlandi (kompozit kaynak, acilis
kaynagi, yer gercegi gosterimi, fail-closed manifest, dort eski kaynak korundu);
"7/7 uyum" kapisi `[ ]` birakildi — kusur `comms/yks_gui.py` disindadir.
