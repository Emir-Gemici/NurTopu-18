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

---

### D-60 · DÜZELTME · "Üretim yolu" referansımı yanlış seçtim; D-48'in sayısı geçersiz

**Kim düzeltti.** Claude-2, T36 sırasında (D-58). Ölçtüm, doğruladım.

**Hatam.** T36 görev tanımında hizalama hedefi olarak
`simulation/scripts/iha_perceive.py::_infer` (P) yazdım. Yanlış referans:

- `CONTRACTS.md` §11.2 Halka 3 (Çıkarım) ve Halka 4 (Maske) sahibi
  **`codes/rpi_inference.py`** (R); §11.1 *"`simulation/` altındaki hiçbir dosya
  sahip yazılamaz"* diyor.
- Jetson saha paketi **R'nin bayt-birebir kopyasını** taşıyor (D-45'te kilitlendi).
  `iha_perceive.py` saha paketinde **hiç yok**. Yani **saha donanımı R'yi koşuyor.**
- Hakem ekranı şartname §2.2.3/§6.2 gereği kanıt belgesidir; sahada koşmayan bir
  yola hizalanırsa hakem, sahada verilmeyecek kararı onaylar.

**Sonuç — kendi kaydımı geçersiz kılıyorum.** D-48'de ve T36 görevinde yazdığım
`AYNI 46 · IRAKSAK 21 (%31,3)` ölçümü **P'ye karşı** yapıldı. P üretim referansı
değil. Bulgunun kendisi (GUI'nin çıplak sabitlerle ayrı bir hat kurmuş olması,
madde 16 ihlali) ayakta; **oran geçersiz.**

Claude-2 ayrıca R ile P'nin **birbirinden de** ayrıştığını ölçtü:
`AYNI 54/67 · FARKLI 13/67 (%19,4)`, ikisi şerit farkı. Bu ayrışma **açık**.

**Kapanış ölçümü (Claude 1, bağımsız, 67 kare):** GUI hizalandıktan sonra karar
denkliği **AYNI 67 · FARKLI 0**; `_algi_kos` içinde çıplak `imgsz`/`conf`/
`min_conf`/`min_area_ratio` kalmadı; dört üretim fonksiyonu da çağrılıyor.

**Ders — bu turda dördüncü kez aynı kök.** D-33 "depo otoritedir", D-51 "üretim
fonksiyonu otoritedir, yeniden kurgusu değil", D-53 "ölçüm zeminine bak".
Bu kayıt dördüncüyü ekliyor: **hangi yolun üretim olduğu `CONTRACTS.md` §11
SAHİPLİK tablosundan okunur — makullükten değil.** Referansı seçerken sahiplik
tablosuna bakmadım; P'nin adı "perceive" olduğu için üretim sandım.

**Açık kalan (T43'ün dışında, ayrı):** R↔P 13/67 ayrışması ve
`iha_perceive.DEFAULT_MODEL` hâlâ `navitas_seg_v2_best.pt` (üretim v21, D-20).
İkisi de `simulation/` altında.

---

### D-60b · COZULDU · T43: Halka 5 sahiplendi, C-uzayi analyze_path koluna tasindi
> ⚠ **Numara duzeltmesi (T44):** bu kayit once `D-60` yazilmisti; ayni
> numarayi Claude 1'in "uretim yolu referansi" kaydi (`:3259`) zaten
> kullaniyordu. D-39/D-40/D-41'de yasanan cakismanin tekrari. Kayitlar
> silinmez (madde 6) — bu kayit `D-60b` oldu, atiflari guncellendi.
Bulan/duzelten: Claude 2 · 2026-08-11 · kanit: D-59, D-22 · gorev T43

**GOREV 1 — Halka 5 (olcek) artik SAHIPSIZ degil.**
Iki kaynak degerlendirildi ve **olculerek** secildi:

    (a) irtifa + FOV/odak -> mpp = 2*h*tan(FOV/2)/W  ·  mpp = h/f_px
        URETILEBILIR: irtifa saha yolunda ZATEN okunuyor —
        MAVLink GLOBAL_POSITION_INT.relative_alt (comms/inis_kaniti.py:143).
    (b) bilinen olcekli nesne (2x2 m H brandasi) -> px/m
        URETILEMEZ: uretim modeli 2 sinifli. OLCULDU:
        navitas_seg_v21_best.pt.names = {0: 'traversable', 1: 'blocked'}
        Hedef dedektoru YOK (D-23 dogrulandi). (b) ancak ucuncu sinif
        uretime girince acilir.

Sahip: `codes/karar_sozlesmesi.py` — `mpp_irtifadan`, `rota_olcek_reddi`,
`r_gerekli_piksel`, `olcek_gecerli_mi`. `CONTRACTS.md` SS5 yeniden yazildi,
SS11.2 Halka 5 **SAHIPSIZ -> GECERLI**, SS6.4 tablosuna `OLCEK_YOK` eklendi.
CLI: `--mpp` / `--irtifa` + `--fov`|`--odak`; uc gorev cagri yeri
(`run_image`/`run_video`/`run_camera`) olcek yoksa `OLCEK_YOK` ile fail-closed
doner ve `main()` uyariyi ekrana basar — sessiz varsayilan kalmadi.

**SESSIZ VARSAYIM ACIGA CIKARILDI.** `olcek_px(None)` hala `m = 1.0` alip
`r_gerekli_px = 1,10 px` donduruyor; gercek deger kompozit arenada 12,7 px.
Yani govde acikligi sessizce **~11 kat** kuculuyordu. Sayi geriye uyum icin
korundu (sentetik "olceksiz kip" ona dayali), fakat gorev yolu artik onu
KULLANMIYOR ve `tests/test_olcek_ve_c_uzayi.py::test_SESSIZ_VARSAYIM_belgelendi`
orani (>10x) kilitliyor.

**GOREV 2 — C-uzayi tasindi (yeniden yazilmadi).**
`analyze_path` rotayi artik C-uzayinda kuruyor: `gecilebilir = (dist >=
r_gerekli_px)`. Bu `costmap_path_finder.py:313`'teki kalibin AYNISIDIR; plan,
gorus-hatti kisayolu (`yol_duzelt`), ornekleme ve son kenar kapisi hep bu
maske uzerinde kosuyor. `dist` gercek acikliktan hesaplanmaya devam ediyor
(A* maliyeti ve T32 guveni icin).

**MADDE 15 — yapisal olarak saglaniyor:** `{dist >= r} ⊆ {dist > 0}`.
Olculdu, 7 kompozit kare:

    serbest_once  36859 39360 35484 55826 34897 33249 32501
    C_uzayi       18862 16585 17641 25708 16987 16054 15554
    FAZLA PIKSEL      0     0     0     0     0     0     0     -> IHLAL 0/7

**GOREV 3 — K-B yeniden degerlendirildi; DEGER DEGISMEDI, ROLU DEGISTI.**
C-uzayi acikken rota uzerindeki her piksel `dist >= r_gerekli_px` saglar,
dolayisiyla guvenin hesaplanabilir bir TABANI olusur:

    guven_tabani = r_gerekli_px / (ROTA_DARBOGAZ_TAM_ORANI * icerik_w)

K-B ancak `mpp > R_GEREKLI_M / (0,20 * 0,035 * icerik_w)` iken atesleyebilir:

    icerik_w= 576 -> mpp > 0,273 m/px      gorev irtifasinda tipik mpp
    icerik_w=1024 -> mpp > 0,153 m/px      0,03-0,12  ->  ATESLEMEZ

Yani K-B **olcekli kipte yapisal olarak erisilemez**. D-38'deki "taban
koruyucusu" tanimi olceksiz kip icin gecerliligini koruyor; ustune YENI bir
rol kazandi: **cozunurluk koruyucusu** — atesledigi tek durum, olcegin araci
~4 pikselden ince gosterdigi haldir.

**Esik 0.20'de BIRAKILDI, gerekce olcumden:** dusurmek anlamsiz (zaten hic
atesliyor degil), yukseltmek zararli (C-uzayinin zaten garanti ettigi fiziksel
kisiti birimsiz bir oranla ikinci kez sayar ve tam da C-uzayinin en guvenilir
oldugu ince olceklerde gecerli rotalari eler). Arena yer gercegindeki guven
0,644-0,744; esik oraya dokunmuyor. **Esik kapi gecmek icin oynatilmadi.**

**KAPILAR (gercek cikti).**

    KAPI 1  arena kompoziti, C zinciri (analyze_path + K-B), yer gercegi maskesi,
            icerik kutusu manifest'ten, tek degisken mpp:
              ONCE  (C-uzayi YOK): DOGRU 1/7 · YANLIS 0 · RET 6
              SONRA (C-uzayi VAR): DOGRU 6/7 · YANLIS 0 · RET 1
              darbogaz  1,0 px -> 13,0-15,0 px
              guven     0,028-0,117 -> 0,644-0,744   (K-B 0,20)
            Kalan 1 ret UC_BANT_TEMAS_YOK'tur ve C-uzayindan ONCE de vardi.
    KAPI 2  MADDE 15 ihlali 0/7 (yukaridaki tablo).
    KAPI 3  otopark (data/raw_frames ilk 16):
              mpp YOK    -> {1: 5, 3: 8, DUSUK_GUVEN: 3}   cekimser 3/16
              mpp=0,0868 -> {1: 6, 3: 8, GORUS_HATTI_KOPUK: 2} cekimser 2/16
    KAPI 4  codes/test_rota_sentetik.py 15/15 · unittest discover -s tests -q
            Ran 259 tests OK · git diff --check exit 0

**KAPI 3'te cekimserlik AZALDI — gerekcesi kare kare olculdu.**
Degisen 3 karenin UCU DE onceden `DUSUK_GUVEN` idi ve darbogazlari 1,0 / 2,0 /
1,4 px'ti (duvar siyiran rotalar):

    frame_000005  DUSUK_GUVEN (darbogaz 1,0)  ->  yol=1  (darbogaz 18,2)
    frame_000006  DUSUK_GUVEN (darbogaz 2,0)  ->  GORUS_HATTI_KOPUK
    frame_000007  DUSUK_GUVEN (darbogaz 1,4)  ->  GORUS_HATTI_KOPUK

Yani gevseme YOK: bir kare, planlayicinin onceden gormezden geldigi GERCEKTEN
guvenli rotayi buldu (1,0 -> 18,2 px); ikisi yumusak guven reddinden SERT
yapisal rette gecti. Ustelik guvenlik KESIN olarak artti: once
`frame_000008` **8,0 px** darbogazla — yani fiziksel gerekliligin (12,7 px)
ALTINDA — yayinlaniyordu; simdi ayni kare 13,0 px. C-uzayindan sonra kabul
edilen HER rota fiziksel gereklilige uyuyor.

**Kalici kapi:** `tests/test_olcek_ve_c_uzayi.py` (17 test) — olcek fail-closed
davranisi, madde 15 altkume ispati (4 gecit x 3 olcek), gercekten dar gecidin
reddi, yeterince genis gecidin kabulu, darbogazin C-uzayi tabaninin altina
inememesi, K-B'nin kritik olcek esitsizligi ve **pozitif kontrol** (C-uzayi
kapaliyken darbogazin gercekten kucuk kaldigi — yoksa kapilar vakum olurdu).

**ACIK KALAN — durustluk notu.**
1. `ROTA_DARBOGAZ_TAM_ORANI = 0.035` hala otopark karelerinden kalibre edilmis
   BIRIMSIZ bir orandir. C-uzayi geldigine gore guven dogrudan
   `darbogaz / r_gerekli_px` (fiziksel KAT) olarak tanimlanabilir ve
   `icerik_w`'den bagimsizlasir. Ayri gorev — bu turda YAPILMADI.
2. `data/raw_frames` karelerinin GERCEK `mpp`'si bilinmiyor (telemetri yok);
   KAPI 3'teki 0,0868 bir VARSAYIMDIR ve gorev yolunda o kareler `OLCEK_YOK`
   ile reddedilir. Gercek sayi ancak telemetrili saha ucusundan gelir.
3. Kompozit kumenin `mpp`'si de manifest'in kendi beyanidir
   ("kontrollu kompozit varsayimi ... gercek kamera mpp olcumu DEGILDIR").

---

### D-61 · COZULDU (kismen) · T44: olcek kapisi hakem ekranina baglandi; T36b'nin IKI nedeni ayrildi
Bulan/duzelten: Claude 2 · 2026-08-11 · gorev T44 · bagimli: T43 (D-60b)

**KOK NEDEN (Claude 1'in bulgusu, dogrulandi).** T43 olcek kapisini uc GOREV
cagri yerine koydu (`rpi_inference.py`); GUI o yollari cagirmiyor, `grep mpp
comms/yks_gui.py` -> SIFIR eslesme. Sonuc iki ayri kusur:
  1. **Yanlis sebep:** ekran "sahnede uygun koridor yok" diyordu; gercek sebep
     "olcek yok, govde acikligi garanti edilemez". Sistem kisitini sahne kusuru
     gibi gostermek — bu dosyada bes kez kapatilan sinif (S9, T34, T37, D-47).
  2. **C-uzayi ekrana ulasmiyordu:** mpp yoksa `r_gerekli_px` yok; T43'un
     arenada 0/7 -> 6/7 yapan kazanimi hakem ekraninda GORUNMUYORDU.

**DUZELTME.** `_kaynak_olcegi(yol)` eklendi: kompozit kaynak manifest'teki
`arena.mpp`'yi okur, digerleri `(None, sebep)` doner. `_algi_kos` uretimin
kapisini KOPYALAMAZ, `karar_sozlesmesi.rota_olcek_reddi`'yi cagirir ve
`analyze_path(..., mpp=mpp)` gecirir. Manifest okunamazsa fail-closed: gunluge
yazilir, olceksiz sayilir, sessiz varsayilan YOK. Bilgi satirinda artik
"olcek X m/px · govde acikligi Y px · C-uzayi UYGULANDI" ya da "olcek YOK
(sebep) · C-uzayi UYGULANAMADI" gorunuyor.

**KAPI 1 — 16 otopark karesi, olcek verilmeden (kendi olcumum):**

    ONCE   HAKEM EKRANI : {'YOL/1': 5, 'YOL/3': 8, 'RED/DUSUK_GUVEN': 3}
           URETIM GOREV : {'RED/OLCEK_YOK': 16}
           AYRISAN      : 16/16
    SONRA  HAKEM EKRANI : {'RED/OLCEK_YOK': 16}
           URETIM GOREV : {'RED/OLCEK_YOK': 16}
           AYRISAN      : 0/16      -> GECTI

(Claude 1'in olcumunde ekran tarafi `UC_BANT_TEMAS_YOK=16` cikmisti; benim
zincirimde `predict conf` ve icerik kutusu farkli oldugu icin dagilim farkli,
ama ayrisma buyuklugu ayni: 16/16.)

**KAPI 2 — T36b KAPANMADI. Zorlanmadi; iki nedeni OLCEREK ayirdim.**
Ayni 7 kare, her adimda TEK degisken degistirildi:

    A  GUI bugun (letterbox icerik + MODEL maskesi + C-uzayi)  : 1/7
    B  + ARENA icerik kutusu (manifest ROI)                    : 3/7   (+2)
    C  + YER GERCEGI maskesi (model yerine manifest maskesi)   : 6/7   (+3)

    Neden 1 — icerik kutusu tanimi UYUSMUYOR : 2 kare
    Neden 2 — model algisi kompozitte ZAYIF  : 3 kare

**Neden 1 aciklamasi — iki farkli `icerik` kavrami var.**

    `_preprocess` icerik : gercek goruntunun LETTERBOX TUVALINDEKI yeri
                           kompozit karede (0, 224, 1024, 576)
    manifest `icerik`    : ARENANIN goruntu icindeki yeri (semantik ROI)
                           (224, 0, 576, 576) -> tuvalde (224, 224, 576, 576)

Serit sinirlari birincisinde 341/683, ikincisinde 416/608 dusuyor. Manifest
seritleri ikincisine gore tanimliyor. **Bu bir GUI kusuru DEGILDIR:** sahada
manifest yoktur ve uretimin arena ROI'sini bilmesinin bir yolu yoktur. Ekranin
manifest ROI'sini karara sokmasi, yer gercegi metaverisini karar yoluna
sizdirmak olurdu — T36b'nin kendi kapisi bunu acikca yasakliyor
(`test_beklenen_serit_KARARA_SIZMIYOR`). Cozum GUI'de degil: ya kompozit uretec
arenayi TAM KAREYE yayacak, ya da arena ROI'si saha yolunda uretilebilir bir
sinyalden (or. hedef/branda tespiti) turetilecek — ikincisi D-23'e bagli.

**Neden 2 aciklamasi.** Ayni icerik kutusuyla model maskesi 3/7, kusursuz yer
gercegi maskesi 6/7 veriyor. Aradaki 3 kare tamamen ALGI kaybidir; karar
zinciriyle ilgisi yok. Kompozit kume `copy_paste` ile uretildigi icin moloz
dokusu gercek degil — D-18/D-20'de olculen domain boslugunun ayni sinifi.

**Yani T36b'nin 5 acik karesinin HICBIRI `comms/yks_gui.py` icinde degildir.**
Gorev `[ ]` birakildi.

**KOSULAN KAPILAR (gercek cikti).**

    KAPI 1  ayrisan 16/16 -> 0/16                                  GECTI
    KAPI 2  T36b uyumsuzluk 5/7                                    DUSTU (yukarida)
    KAPI 3  T36 hizalama testleri: test_gui_kendi_cikarim_hattini_
            KURMUYOR ve test_gui_karari_uretim_yolunun_karariyla_
            AYNI dahil 23/23 OK                                    GECTI
    KAPI 4  codes/test_rota_sentetik.py 15/15 ·
            unittest discover -s tests -q -> Ran 266 tests OK ·
            git diff --check exit 0                                GECTI

**Not — hizalama testi genisletildi.** `test_gui_karari_uretim_yolunun_
karariyla_AYNI` artik olcekli VE olceksiz kipi birden sinar ve referans tarafi
`rota_olcek_reddi`'yi de calistirir; aksi halde test GUI'yi "olcegi yok sayan"
bir uretime hizalamis olurdu. `test_rota_ret_nedenleri`'ndeki uc-sebep testi
olcek kapisindan yalitildi (yoksa uc sebep de OLCEK_YOK'a coker ve ayrim
olculemez); olcek kapisinin kendi kapisi ayri testtedir.

**Kayit numarasi duzeltmesi (ayni turda).** `D-60` iki kez kullanilmisti;
Claude 2'nin "T43 cozuldu" kaydi **D-60b** oldu ve `TASK_QUEUE.md` T43 atfi
guncellendi. D-39/D-40/D-41'de yasanan cakismanin tekrariydi.

---

### D-61 · TIKAYICI · v21'in "geçilebilir" sınıfı bu alanda anlamsız: çatı, çim ve toprak yol sayılıyor

**Nasıl çıktı.** Kullanıcı GUI'yi ilk kez gerçekten kullandı ve bildirdi:
*"doğru bir şekilde yol tespit etmiyor, görsellerin kenarını yol sanıyor, bazen
hiç yol bulmuyor, bazen çatıyı yol sanıyor."* **Gözle doğruladım — haklı.**

**Benim kaçırdığım.** Aynı karelerde *"ortalama zemin %74"* ölçtüm ve bunu
sağlık işareti sandım. Oysa `REVIEW_LOG`'daki v13/v16 kaydı tam tersini söylüyor:
yüksek kaplama = **yanlış-pozitif zemin çöküşü** (v13 kaplama %43,4, görüntünün
%84,7'sini boyuyordu, moloza basma %37,7). Bir otoparkın %74'ünü "geçilebilir"
boyamak **alarm** olmalıydı, ben doğrulama sandım.

**Görsel kanıt (gorunum_0.png / gorunum_1.png, kullanıcıya iletildi):**
- Metal çatılı **bina tamamen yeşil** (geçilebilir).
- Çim, toprak, asfalt — hepsi yeşil.
- **Yalnız araçlar kırmızı.**
- Üretilen rota (sarı) görüntünün **sol kenarındaki çim şeridinden** geçiyor.

Yani v21 bu alanda pratikte bir **"araç mı, değil mi"** ayırıcısıdır; zemin
sınıfı "araç olmayan her şey" anlamına geliyor.

**Kullanıcının üç şikâyeti tek kök nedene iniyor:**
1. *"çatıyı yol sanıyor"* → çatı zemin sınıfında.
2. *"kenarını yol sanıyor"* → her yer serbest olunca koridor araması en geniş
   kanalı seçiyor; o da kenardaki çim şeridi oluyor.
3. *"bazen hiç yol bulmuyor"* → serbest alan anlamsız olduğu için `GORUS_HATTI_
   KOPUK` / `UC_BANT_TEMAS_YOK` gibi retler gelişigüzel düşüyor.

**Yanlış çıkarımlarımı geri alıyorum:**
- *"Model suçsuz, sorun `OLCEK_YOK` politikasında"* — **yanlıştı**. Ölçek kapısı
  daha kötü bir sorunu **örtüyordu**.
- *"16 karenin 14'ünde rota buluyor"* — bu **iyi haber değil**. O rotalar çatı ve
  çim üzerinden geçen rotalar.
- **T46 tehlikeli hâle geldi:** varsayılan ölçekle rotaları geri getirmek, hakem
  ekranında *"kendinden emin ve yanlış"* rotalar gösterir. Hiçbir şey
  göstermemekten **daha kötüdür**. T46 bu nedenle **bloke** edildi.

**Ne bilmiyoruz — ve bilemeyiz.** Bu kareler bir **otopark** (D-53); model
RescueNet + sentetik arena ile eğitildi. Yani bu, alan dışı bir sahnedir ve
buradaki çöküş, modelin **gerçek arenada** da çökeceğini kanıtlamaz. Ama tersini
de kanıtlayamayız: **elimizde tek bir gerçek arena karesi yok** (arena çekimi
2026-08-11'de iptal edildi, D-56). Ölçüm zeminimiz yok.

**Bağlayıcı kısıt bu.** K-3 zaten mAP'in arena sıralamasını tersine çevirdiğini
söylüyordu; şimdi buna şu ekleniyor: elimizdeki tek gerçek zeminde zemin sınıfı
çalışmıyor ve **doğrulayacak veri yok**.

**Görev:** `TASK_QUEUE.md` **T47** (zemin sınıfı alan geçerliliği) · T46 bloke.

---

### D-62 · COZULDU · T48: zemin maskesi saglamlik kapisi (kaplama tavani)
Bulan: kullanici (gozle) · olcen/duzelten: Claude 2 · 2026-08-11 · gorev T48

**KUSUR.** Hakem ekrani bina CATISI ve CIM uzerinden gecen bir rotayi kendinden
emin ciziyordu. Uretim modeli bu alanda pratikte "arac mi, degil mi"
ayiricisidir; cati, cim, toprak hepsi zemin sinifina duser. Maske **dolu**
gorundugu icin mevcut kapilarin HICBIRI bunu yakalayamaz: K-A uc bantlara
temasi, C-uzayi acikligi, K-B guveni gorur — ucu de memnun kalir.

**OLCUM — esik uydurulmadi.** kaplama := zemin (sinif 0) maskesinin ICERIK
kutusundaki piksel orani; ham maske uzerinde, morfoloji ve engel cikarmadan
ONCE. Uretim zinciri, conf=0.30. Uc BAGIMSIZ mesru kaynak, iki cokmus kume:

    MESRU (kapi ATESLEMEMELI)                        n     p50    p95    MAKS
      sentetik arena YER GERCEGI (etiket poligonu)  60   %11,7  %22,1  %39,0
      sentetik arena, v17 + v21 model ciktisi      120   %11,8  %23,2  %38,7
      genel kapinin KENDI 15 sahnesi                15   %36,4    —    %42,6

    COKMUS (kapi ATESLEMELI)                         n     p50           MIN
      v21 otopark (cati/cim yesil)                  67   %79,9         %76,7
      v21 kompozit arena                             7   %82,7         %76,0

`%42,6` ile `%76,0` arasi BOS. **TAVAN = 0.55**: en yuksek mesru kaplamanin
1,29 kati (gurultu payi), en dusuk cokmus kaplamanin 0,72 kati. 194 model
karesi + 60 yer gercegi + 15 kapi sahnesinde **yanlis pozitif 0, kacirma 0**.

🔴 **GOREV TABLOSUNDAKI v13 SATIRI KULLANILAMADI — ve nedeni onemli.**
"v13 cokmus, kaplama %43,4" deniyordu. (1) v13 agirligi depoda YOK, olculemedi;
(2) satirin kendi iki sayisi tek tanim altinda tutarsiz (%43,4 ve "goruntunun
%84,7'sini boyuyor"); (3) **asil sorun:** %43,4, genel kapinin KENDI mesru
sahnelerinin azamisinin (%42,6) yalniz **0,8 puan** ustunde. O degeri yakalayan
bir tavan `codes/test_rota_sentetik.py` 15/15 kapisini kirardi. Yani tablonun
istedigi esik, deponun kendi referans sahneleriyle CELISIYOR. Tavan
olculebilen kaynaklardan turetildi ve bu celiski kayda gecirildi.

⚠ **Kapinin bilinen siniri:** bu bir KAPLAMA kapisidir, doku kapisi degil.
v13 benzeri ORTA siddetli bir cokme (icerigin ~%43'unu boyayan) buradan GECER.
Yakalamak icin maskenin YAPISI (doku/renk tutarliligi) gerekir — ayri gorev.

**UYGULAMA.** `karar_sozlesmesi.py`: `ZEMIN_KAPLAMA_TAVANI = 0.55`,
`ZEMIN_MASKESI_SUPHELI_SEBEBI`, `zemin_kaplamasi`, `zemin_maskesi_reddi`.
`analyze_path` kapiyi ROTADAN ONCE kosuyor (bosuna A* kosulmuyor; test
`test_kapi_ROTADAN_ONCE_calisir` bunu kilitliyor). `CONTRACTS.md` SS6.4'e
sebep satiri + gerekce tablosu. GUI esigi SOZLESMEDEN okuyor, ciplak yazmiyor;
ret halinde rota CIZMIYOR ve bilgi satirina
`⚠ ZEMİN MASKESİ ŞÜPHELİ · kaplama %78 (tavan %55)` basiyor.

**MADDE 15:** kapi NOTRDUR — maskeye dokunmaz, tek piksel eklemez/cikarmaz;
yalniz reddeder. `test_MADDE_15_kapi_maskeye_DOKUNMAZ` kilitliyor.

**YAN DUZELTME — ret onceligi.** Otoparkta iki ret AYNI ANDA gecerli
(`OLCEK_YOK` ve `ZEMIN_MASKESI_SUPHELI`) ve olcek kapisi yapisal reti
EZIYORDU. `CONTRACTS.md` SS6.4/3 zaten "yapisal ret ezilmez" diyor. Kural
uc uretim cagri yerinde ve GUI'de duzeltildi:
`if olcek_reddi is not None and karar_reddi is None`. Gerekce: olcek eksikligi
bir YAPILANDIRMA boslugu, `ZEMIN_MASKESI_SUPHELI` ise ALGI ARIZASIDIR; hakeme
gosterilmesi gereken daha derin olandir.

**KOSULAN KAPILAR (gercek cikti).**

    KAPI 1  otopark 12 kare, hakem ekrani:
              ONCE  : {'OLCEK_YOK': 12}          (yapisal ret eziliyordu)
              SONRA : {'ZEMIN_MASKESI_SUPHELI': 12}  -> 12/12 GECTI
              ekran : "⚠ ZEMİN MASKESİ ŞÜPHELİ · kaplama %78 (tavan %55)"
    KAPI 2  sentetik arena 40 kare, YANLIS POZITIF 0/40:
              {'UC_BANT_TEMAS_YOK': 33, 'YOL/2': 4, 'YOL/3': 2, 'YOL/1': 1}
    KAPI 3  POZITIF KONTROL (sentetik cokme supurmesi):
              %20 %40 %50 %54 -> KARAR VAR (kapi susuyor)
              %56 %70 %95     -> ZEMIN_MASKESI_SUPHELI (kapi atesliyor)
    KAPI 4  codes/test_rota_sentetik.py 15/15 ·
            unittest discover -s tests -q -> Ran 281 tests OK ·
            git diff --check exit 0 · Jetson ikizleri BIREBIR

**TEST FIKSTURLERI GERCEKCILESTIRILDI (kapi gevsetilMEDI).** Uc test dosyasi
`trav = np.ones(...)` — yani "tum kare surulebilir" — kuruyordu; kapi bunlari
HAKLI OLARAK supheli sayiyor. Fiksturler tavanin altina indirildi, olctukleri
sey korundu:
  · `test_rota_serit_etiketi._bariyer_ve_kapi` -> KUM SAATI (kaplama %51,1).
    Ilk denemem uc AYRI koridordu; kaplama dustu ama POZITIF KONTROL bosaldi
    (eski centroid tanimi 3/3 dogru cikti, kusur yeniden uretilemedi). Kum
    saati hem tavanin altinda hem ayirt edici: ust bant uc seride yayildigi
    icin eski centroid hala 2 diyor, yeni tanim 1/2/3 veriyor.
  · `test_olcek_ve_c_uzayi._dar_gecitli_sahne` -> 450 px koridor (%50).
  · `test_rota_ret_nedenleri` tam-ortme sahnesi -> 40 px koridor (%31).

**ACIK KALAN.** Kompozit arena kaynagi artik 7/7 `ZEMIN_MASKESI_SUPHELI`
donuyor (v21 kaplamasi orada %76-84). Bu, **T36b'nin durumunu degistirir**:
ekran artik yanlis serit GOSTERMIYOR, dogru sebeple CEKIMSER kaliyor. D-61'in
"neden 2 — model algisi kompozitte zayif" bulgusu boylece gorunur hale geldi;
T36b'nin kapanmasi hala model/veri tarafina bagli.

---

### D-63 · OLCUM · T50 FAZ 1: 11 model uc kapiyla siralandi — KAZANAN YOK, ve KAPI 2'nin KENDISI KUSURLU
Olcen: Claude 2 · 2026-08-11 · gorev T50 FAZ 1 · GPU'ya DOKUNULMADI

⚠ **KAMERA YOK (kullanici bildirdi): gercek arena karesi ALINAMIYOR. Bu gorev
modelin ARENADAKI basarimini dogrulamaz ve dogrulayamaz; yalniz alan-ici
dogrulugu ve ALAN DISI TEMKINI iyilestirir.**

**TAM TABLO — 11 model x 3 kapi** (uretim zinciri `_preprocess` + `get_masks` +
`_maskeleri_icerige_kirp`, conf=0.30; K1 n=120 rescuenet_1024 val, K2 n=67
otopark, K3 n=9 kompozit). Metrik tanimi: mikro-ortalama (piksel havuzu).

    model                       K1 IoU  K1 kesinlik  K1 duyar  K2 ort  K2 maks  K3 D/Y/R
    navitas_seg_v2_best.pt       0.366        0.760     0.414   70.4%    86.1%   0/0/9
    navitas_seg_v3_best.pt       0.412        0.744     0.481   18.2%    78.7%   0/1/8
    navitas_seg_v4_best.pt       0.351        0.827     0.379   13.5%    76.6%   0/1/8
    navitas_seg_v5_best.pt       0.384        0.775     0.432   35.8%    68.2%   1/3/5
    aday_v5a_s640.pt             0.384        0.775     0.432   35.8%    68.2%   1/3/5
    aday_v5b_s640ft.pt           0.352        0.781     0.390   32.9%    78.3%   0/1/8
    aday_v5c_m640.pt             0.372        0.689     0.448   46.9%    82.6%   0/0/9
    aday_v9_mixup_m640.pt        0.365        0.631     0.463   50.2%    92.6%   1/0/8
    navitas_seg_v17_best.pt      0.315        0.807     0.341    0.9%     7.0%   0/0/9
    navitas_seg_v20_best.pt      0.267        0.795     0.287    2.9%    52.9%   0/0/9
    navitas_seg_v21_best.pt      0.311        0.813     0.335   81.0%    86.3%   0/0/9

**KAPI 3 KIMSEYI GECIRMIYOR.** En iyi sonuc 1/9 (v5, v5a, v9) ve o uc model
kapi 2'de %35-50 ile zaten cokmus. Uretim adaylarinin (v17/v20/v21) UCU DE
**0/9**. Ayrica kapi 3'un yer gercegi yalniz serit 1 (5 kare) ve serit 3
(4 kare) iceriyor — **serit 2 hic yok**; "hep 1 de" diyen bir kod sansla 5/9
alirdi. Kapi bu haliyle zayiftir.

🔴 **ASIL BULGU — KAPI 2 TEK BASINA KUSURLU: TEMKIN ile KORLUGU AYIRT ETMIYOR.**
Kapi 2'yi gecen dort model (v17 %0,9 · v20 %2,9 · v4 %13,5 · v3 %18,2) iki
ek olcumle sinandi:

    ARENA BENZERI SENTETIK KUME (n=60, GT kaplama %12,4)
      model   kaplama   IoU     kesinlik  duyarlilik  kare>%1
      v17       12.4%  0.896      0.942       0.948    55/60
      v20       12.7%  0.929      0.951       0.976    59/60
      v4         5.8%  0.094      0.269       0.125    21/60
      v3         5.1%  0.122      0.371       0.153    14/60
      v21       12.7%  0.924      0.948       0.973    60/60

    -> v4 ve v3 kapi 2'yi **HICBIR SEY GORMEDIKLERI ICIN** gecti. Elendiler.

    KOMPOZIT: GERCEK OTOPARK DOKUSU + arena semantigi (n=9, GT kaplama %28,6)
      model   kaplama   IoU   duyarlilik  kare>%1
      v17        0.4%  0.010      0.010     1/9
      v20        0.1%  0.000      0.000     0/9
      v21       82.5%  0.297      0.890     9/9

    -> v17'nin otoparktaki %0,9'u TEMKIN DEGIL, **GERCEK DOKUDA KORLUK**.
       v17 yalnizca (a) RescueNet ve (b) SENTETIK arena dokusunda goruyor;
       ikisi de kendi egitim dagiliminda (VERI_KAYNAKLARI: v17 =
       `karisim_arena.yaml` = RescueNet + sentetik arena). Gercek asfaltta
       9 karenin 8'inde HICBIR SEY uretmiyor.

**SONUC: KAZANAN YOK.** Kapi 1 + kapi 2 birlikte uygulandiginda secilen
modeller (v17, v20) gercek dokuda kor; gercek dokuyu goren tek model (v21)
kapi 2'de cokuyor (%81,0, GT %28,6'ya karsi %82,5 — ~3 kat asiri tespit).
Hicbir model "gercek dokuda GORUR **ve** alan disinda COKMEZ" cerceyesinde
degil. Tablo su iki eksende ozetlenir:

    gercek doku duyarliligi (kompozit)  vs  alan disi kaplama (otopark)
      v21   0.890  /  %81,0     <- gorur ama coker
      v17   0.010  /  %0,9      <- cokmez ama gormez
      v20   0.000  /  %2,9      <- cokmez ama gormez

**GORSEL DOGRULAMA — SAYIYI DEGISTIRDI, kurala uyuldu.**
`O:\navitas-local-train\results\t50_uc_kapi\` altinda:
  · `navitas_seg_v21_best__otopark.jpg` — kullanicinin bildirdigi kusur GOZLE
    DOGRULANDI: bina CATISI ve CIM parlak YESIL (surulebilir zemin), yalniz
    araclar kirmizi.
  · `navitas_seg_v17_best__otopark.jpg` — TEK BIR piksel bile isaretlenmemis
    (ne zemin ne engel). "Temkinli" degil, SESSIZ.
  · `AYIRT_*__rescuenet_val_ZENGIN.jpg` (GT zemin %37,3) — v17 ve v21 yol
    yuzeyini dogru ve sinirli sekilde yesilliyor; alan icinde ikisi de saglam.
  · `AYIRT_*__sentetik_arena_ZENGIN.jpg` (GT %39,0) — v17 uc koridoru temiz
    ayiriyor (%38,4). Yani v17 KOR DEGIL; korlugu GERCEK DOKUYA OZGU.
Ilk uretilen `v17__rescuenet_val.jpg` %0,0 gosteriyordu ama o kare molozla
dolu ve GT zemini yok denecek kadar az; AYIRT EDICI olmadigi icin GT'si zengin
kare secilip yeniden uretildi.

**GURULTU TABANI (0,04) UYGULANDI.** v17 vs v20 K1 IoU farki 0,048 (gercek);
K1 kesinlik farki 0,012 (gurultu); arena IoU farki 0,033 (gurultu). Yani
v17/v20 arasindaki tek gercek fark alan-ici IoU ve alan-disi EN KOTU KARE
(v17 %7,0 · v20 %52,9). Ama ikisi de gercek dokuda kor oldugu icin siralama
anlamsizdir.

**VERILEN TABAN TABLOSUYLA FARK — durustluk notu.** Gorevdeki tabloda
kesinlik sutunu (v17 0,170 · v20 0,284 · v21 0,280) kendi IoU/kaplama
sayilariyla **tutarsiz**: `I = IoU*(P+G)/(1+IoU)` ile turetilince sirasiyla
0,372 / 0,458 / 0,442 cikiyor. Muhtemel sebep kare-basi (makro) ortalama vs
mikro-ortalama. Bu raporda metrik **mikro-ortalama** olarak acikca tanimlandi;
duyarlilik sutunum (v21 0,335) tablonun kendi sayilarindan turetilenle
(0,318) ortusuyor.

**FAZ 2 GEREKCELI — ama ONCE OLCUT DUZELTILMELI.** Kazanan cikmadigi icin FAZ 2
(11 sinifla on-egitim -> 2 sinifa fine-tune) yururlukte. Ancak FAZ 1 kapi 2'nin
TEK BASINA kullanilamayacagini olcerek gosterdi: en yuksek puani goren degil
GORMEYEN model aliyor. Ayni olcutle egitilen bir model yine yanlis secilir.
**Onerilen ek kapi (KAPI 0 — TESPIT TABANI):** modelin GERCEK DOKUDA zemin
uretmesi zorunlu olsun — kompozit kumede `duyarlilik >= 0,50` ve
`kare>%1 >= 8/9`. Bugun bu kapiyi **yalniz v21** geciyor (0,890 / 9/9); v17 ve
v20 kaliyor. Secim o zaman "kapi 0'i gecenler arasinda kapi 2'si en dusuk
olan" olur ve hem korlugu hem cokusu eler.

**DOGRULANAMADI**
  1. Hicbir modelin GERCEK ARENA basarimi — kamera yok, arena karesi yok.
  2. Kompozit kumenin gercek arenayi ne kadar temsil ettigi; moloz yapistirma
     ile uretildi, dokusu gercek moloz degil.
  3. Sentetik arena sonuclari v17/v20/v21 icin **dagilim ici** (ucu de o kumeyle
     egitildi) — genelleme kaniti SAYILMAZ.
  4. v13 (gorev metnindeki referans) diskte YOK, olculemedi.

---

### D-62 · Üç ölçüm zeminimiz de ayrı sebeplerle geçersiz — ve sentetik arenanınki ucuz düzeltilir

**Ölçüm (Claude 1, 2026-08-11, 24 sentetik arena karesi, v21):**

    TAM KARE          : UC_BANT_TEMAS_YOK 21 · rota  3/24
    ARENAYA KIRPILMIS : rota 14/24 (ZEMIN_SUPHELI 7 · UC_BANT 2 · GORUS 1)

Arena bölgesine kırpmak rotayı **3/24'ten 14/24'e** çıkarıyor. Bu, Codex-2'nin
T49 tanısını bağımsız doğruluyor: kusur modelde değil, üretecin arenayı kadraja
oturtmamasında. `51_sentetik_arena.py` arenayı `%0–28` dikey payla, dönüş ve
perspektifle yerleştiriyor; karar yolu ise koridorun içerik kutusunun uçlarına
ulaşmasını bekliyor (K-A).

**Üç zeminin durumu — hepsi geçersiz, sebepleri AYRI:**

| zemin | kusur | düzeltilebilir mi |
|---|---|---|
| otopark (`data/raw_frames`) | alan dışı; v21 kaplaması %73,7, çatı/çim zemin | model işi (T50) |
| sentetik arena | geometri: arena kadraja ulaşmıyor | **evet, ucuz (T51)** |
| kompozit arena | arka plan otopark → maske çöküyor | otoparkın kusurunu miras alıyor |

Sentetik arenanın **kaplaması zaten temkinli** (%15,7 — T48 tavanının altında).
Tek eksiği geometri. Yani düzeltilirse **karar yolunun geometrisiyle uyumlu tek
zemin** olur ve GUI ilk kez uçtan uca çalışır hâlde gösterilebilir.

**🔴 YAN BULGU — T48'in tavanı için canlı risk.** Kırpılmış karelerde 7/24
`ZEMIN_MASKESI_SUPHELI` çıktı. `ZEMIN_KAPLAMA_TAVANI = 0.55` **gevşek kadrajlı**
sahnelere göre kalibre edildi (sentetik arena tam karede %15,7). Oysa görev
kadrajında arena görüntüyü **doldurmalıdır**; o zaman kaplama meşru olarak
yükselir ve kapı **yanlış ateşler**. Ham kaplama, "her şey boyanmış" ile
"gerçekten açık arena" hâllerini üst uçta ayırt edemez. Tavan, kadrajı arena ile
dolu sahnelerde yeniden ölçülmeli; gerekirse ölçüt ham kaplamadan
ayırt-edicilik ölçen bir büyüklüğe taşınmalı. **T48 kapanmadan bu ölçülmeli.**

---

### D-64 · COZULDU (kismen) · T51: sentetik arena kadraja oturtuldu; T50 FAZ 2 EGITIME GEREK KALMADI
Olcen/duzelten: Claude 2 · 2026-08-12 · gorevler T51 + T50 FAZ 2

⚠ **KAMERA YOK: gercek arena karesi alinamiyor. Bu gorev modelin ARENADAKI
basarimini dogrulamaz.** Olculen sey uretecin GEOMETRISI ve karar yolunun o
geometriyle uyumudur.

**T51 — KADRAJ KIPI.** `51_sentetik_arena.py`'ye `--kadraj` eklendi: dikey pay
`kenar_y = 0` (koridorlar ust/alt uc bantlara ULASIR), `geometrik()` donus ve
perspektifi UYGULAMAZ (ikisi de koridor uclarini kadraj disina tasiyordu) ve
`"kismi"` serit durumu KAPALI (tanimi geregi kareyi bastan basa gecmez).
**Egitim kipi (varsayilan) DEGISMEDI** — pay ve donus cesitlilik icin degerli,
silinmedi. Yeni kume 260 kare: `O:\navitas-local-train\calisma\sentetik_arena_kadraj`.

**ONCE/SONRA — kendi olcumum** (TAM KAREDE, kirpmasiz, YER GERCEGI maskesiyle,
n=24, model YOK):

    ESKI (egitim kipi) : rota  2/24 · sebepler {UC_BANT_TEMAS_YOK: 20, DUSUK_GUVEN: 2}
    YENI (kadraj kipi) : rota 12/24 · sebepler {DUSUK_GUVEN: 8,
                         UC_BANT_TEMAS_YOK: 2, ZEMIN_MASKESI_SUPHELI: 2}

`UC_BANT_TEMAS_YOK` **20 -> 2**. Tani dogrulandi: kusur modelde degil, uretecin
YERLESIMINDE.

**KAPILAR (gercek cikti).**

    KAPI 1  TAM KAREDE rota 12/24 (esik >= 12)                     GECTI
    KAPI 2  yer gercegi serit ile UYUMSUZLUK 3/12                  (olculdu)
    KAPI 3  POZITIF KONTROL: acik serit kapatilinca karar DEGISTI
            12/12                                                  GECTI
    KAPI 4  EGITIM KIPI DEGISMEDI                                  GECTI
    KAPI 5  T48 tavani bu kumede 11/260 kareyi kesiyor             (asagida)

🔴 **KAPI 4'UN OLCUM YONTEMI DEGISTIRILDI — cunku istenen yontem GECERSIZ.**
"Eski komutla uretilen cikti BAYT-ESIT" olcutu uygulanamaz: `51_sentetik_arena.py`
**zaten** tekrarlanabilir degil. DEGISTIRILMEMIS kodla, ayni `--seed 7` ile uc
kosum uc farkli hash verdi:

    t51_ONCE   f274c4cd15790c72084357d1a19d0895
    t51_SONRA  c461a815c796fe7f5fa6ba062a65bd69
    t51_UCUNCU e213983656f356af2c366cb34b419358

Bu ONCEDEN VAR OLAN bir ozelliktir (kaynagi bu gorevde arastirilmadi —
**DOGRULANAMADI**). Yerine DAHA SIKI bir denklik testi kuruldu: orijinal dosya
`_51_orijinal_t51.py` olarak saklanip iki surum YAN YANA import edildi ve ayni
RNG ile cagrildi. Dort tohumda (7, 42, 123, 2026) **kimlik haritasi, sinif
sozlugu, cagri sonrasi RNG DURUMU ve `geometrik()` ciktisi** bire bir esit.
Negatif kontrol: `kadraj=True` kimlik haritasi egitim kipinden FARKLI (True).

⚠ **Bu testin ilk kosumu SAHTE GECTI ve negatif kontrol yakaladi.** Ilk
uygulamada 8 blogun yalniz 1'i dosyaya yazilmisti (script 8. blokta assert'e
takilip cikmis, oncekiler bellekte kalmisti); test dosyayi KENDISIYLE
kiyasliyordu. Negatif kontrol `TypeError: unexpected keyword argument 'kadraj'`
ile bunu ortaya cikardi. D-15/K-04 sinifinin canli ornegi.

**KAPI 5 — T48 KAPLAMA TAVANI BU KUMEDE YANLIS ATESLIYOR (tavan DEGISTIRILMEDI).**
Kadraj kipi arenayi kadraja oturttugu icin mesru kaplama YUKSELIYOR. 260 karede:

    kaplama: ort %22,0 · p50 %20,3 · p95 %52,2 · MAKS %82,3
    tavanin (%55) ustunde kare        : 11/260  (%4,2)
    ZEMIN_MASKESI_SUPHELI ile reddedilen: 11/260
      bunlarin GT seridi OLAN (mesru sahne) : 11/11
      tavan olmasaydi ROTA URETECEK olan    : 11/11

Yani tavan bu kumede **11 mesru karari kesiyor**. D-62'de tavan, mesru azamisi
%42,6 olan bir tabandan turetilmisti; kadraj kipi o tabani gecersiz kiliyor.
Gorev geregi tavan **DEGISTIRILMEDI**; karar mimarindir. Not: %82,3'luk kare
gercekten cok acik bir sahnedir, "cokmus maske" degil — yani bu bir kapi
kalibrasyon borcudur, kapi hatasi degil.

**T50 FAZ 2 — EGITIM BASLATILDI, ANCAK GEREKMEDI.**
`42_cok_sinifli_onegitim.py --on-epoch 150 --ft-epoch 200 --batch 12`
(FOR_DISABLE_CONSOLE_CTRL_HANDLER=1, 2026-08-12 00:17:45) baslatildi. Script
her iki asamayi da **tamamlanmis** bulup atladi:

    [v15_on10sinif] zaten tamamlanmis (150 epoch), atlaniyor
    [v15_ft2sinif]  zaten tamamlanmis (166 epoch), atlaniyor

`bitti_mi()` (`42_...py:53`) yalniz epoch sayisina bakmaz; durum gunlugunde
"EGITIM TAMAMLANDI" damgasini da arar. `v15_ft2sinif` 200 yerine 166 epoch'ta
**erken durdurma ile** bitmis. Yani **FAZ 2 recetesinin urunu ZATEN DISKTE**:
`codes/runs/segment/v15_ft2sinif/weights/best.pt`
(SHA256 `a796265f1c5c3ea6b4d35aa9eebe1a25feec9b277f37149bf1b13cb90ff3f942`).
Bu model `models/` altina hic aktarilmamis ve **T50'nin 11 modelli tablosunda
YOKTU**. GPU-gecesi harcamak yerine dort kapiyla olculdu:

    model          K0 duyar  K0 kare>%1  K1 IoU  K1 kesin  K2 otopark  K3 D/Y/R
    v15_ft2sinif      0.134         2/9   0.425     0.804      24.1%     0/0/9
    v21 (uretim)      0.890         9/9   0.311     0.813      81.0%     0/0/9
    v17               0.010         1/9   0.315     0.807       0.9%     0/0/9

**v15 KAPI 0'i GECEMIYOR** (0,134 < 0,50 · 2/9 < 8/9). Yani 11-sinif on-egitim
recetesi alan-ici dogrulugu YUKSELTIYOR (IoU 0,425 — olculen 12 modelin EN
IYISI) ve alan-disi asiri tespiti FRENLIYOR (%24,1), ama **gercek doku
korlugunu COZMUYOR**.

**SONUC — T50'de hala KAZANAN YOK, ve nedeni artik daha net.** Iki kusur
birbirinin zitti ve tek bir recete ikisini birden cozmuyor:
  · gercek dokuyu GOREN tek model v21 — cunku egitiminde `copy_paste_gercek`
    (gercek nadir drone karesi) VAR; ama asiri tespit ediyor (%81,0).
  · asiri tespit etmeyen modeller (v15 %24,1 · v17 %0,9 · v20 %2,9) gercek
    dokuda kor — cunku egitimlerinde gercek doku YOK.
Yani eksik olan sey RECETE degil, **VERI KARISIMI**: 11-sinif on-egitim (v15)
ile gercek doku verisi (v21'in `copy_paste_gercek`i) AYNI kosuda birlestirilmemis.
Bu bir egitim tasarim karari; kullaniciya soruldu, kendi basima GPU-gecesi
harcanmadi.

**DOGRULANAMADI**
  1. Hicbir modelin GERCEK ARENA basarimi — kamera yok.
  2. `51_sentetik_arena.py`'nin tekrarlanabilir olmamasinin KAYNAGI.
  3. Kadraj kumesindeki 3/12 serit uyumsuzlugunun kok nedeni (karar yolu mu,
     yer gercegi turetimim mi) — ayristirilmadi.

---

### D-65 · MİMAR KARARI · T48 tavanı 0,55'te KALIYOR; bedeli ölçüldü ve kayda geçti

**Karar gerekçesi.** Claude-2 T51'de tavanı değiştirmedi ve kararı bana bıraktı —
doğru davranış. Ölçümler:

    Claude-2, 260 kadraj karesi (yer gercegi):
      kaplama ort %22,0 · p50 %20,3 · p95 %52,2 · MAKS %82,3
      tavan (%55) ustunde 11/260 (%4,2) — 11/11'inin GT seridi VAR,
      11/11'i tavan olmasaydi ROTA URETECEKTI

    Claude 1, ayni kumeden 24 kare (MODEL cikarimi):
      kaplama ort %17,7 · p95 %37,5 · maks %48,7 · tavan ustu 0/24

**Karar: tavan `0.55`'te KALIYOR.** Gerekçe:
1. Engellediği kusur — bir binanın **çatısı üzerinden rota** — ile maliyeti —
   meşru sahnelerin **%4,2'sinde çekimserlik** — aynı ağırlıkta değil. Anayasa
   varsayılanı fail-closed'dur.
2. Model çıkarımı yolunda (GUI'nin gerçekte yaşadığı hâl) tavan bu kümede **hiç
   ateşlemiyor** (0/24, maks %48,7). Yanlış-negatif maliyeti yer gerçeği
   ölçümünün gösterdiğinden düşük.

**🔴 AMA ÖLÇÜT ZAYIF, BUNU GİZLEMİYORUM.** Kadraj kümesinin meşru azamisi
**%82,3**; otoparkın çöküş değeri **%73,7–82,5**. Yani **ham kaplama, üst uçta
"her şey boyanmış" ile "gerçekten açık arena" hâllerini AYIRT EDEMİYOR.** İki
dağılım orada çakışıyor. Görev kadrajında arena görüntüyü dolduracağı için
sistem tam da ölçütün en zayıf olduğu bölgede çalışacak.

Tavan bir **köprü çözümdür**, nihai ölçüt değildir. Yerine ayırt-edicilik ölçen
bir büyüklük gelmeli: **T52**.

**Kayıt disiplini notu.** Claude-2'nin T51'de kullandığı "eğitim kipi değişmedi"
testinin **ilk koşumu sahte geçti** (8 bloktan 1'i yazılmış, dosya kendisiyle
kıyaslanıyordu) ve bunu **kendi negatif kontrolü yakaladı**. D-15/K-04 sınıfının
canlı örneği: negatif kontrolü olmayan test hiçbir şey ölçmez. Ayrıca üretecin
**hiç tekrarlanabilir olmadığı** ortaya çıktı — değiştirilmemiş kodla aynı
seed'le üç koşum üç farklı hash verdi. Benim "bayt-eşit" kapım uygulanamazdı;
yerine konan RNG-durumu karşılaştırması daha sıkıdır.

---

### D-66 · ÇÖZÜLDÜ · Ayırt edici ölçüt bulundu: kenar dayanması (T52)

**Sorun (D-65).** `ZEMIN_KAPLAMA_TAVANI` üst uçta iki dağılımı ayıramıyordu:
meşru kadraj arenasının azamisi %82,3, otoparkın çöküşü %73,7–82,5. Tavan
köprü çözüm olarak bırakılmış, bedeli (%4,2 meşru çekimserlik) kaydedilmişti.

**Ölçüm (Claude 1, 2026-08-12) — 218 meşru + 67 çökme karesi, altı aday:**

    olcut            MESRU min..maks     COKUS min..maks   ayrisma
    kaplama          0.001..0.809        0.725..0.833      CAKISIK
    doluluk          0.007..0.897        0.726..0.836      CAKISIK
    tikizlik         0.013..0.966        0.728..0.838      CAKISIK
    en_buyuk_pay     0.208..1.000        0.995..1.000      CAKISIK
    engel_orani      0.000..0.998        0.158..0.265      CAKISIK
    kenar_dayanma    0.000..0.339        0.579..0.964      +0.240  <- TEK AYIRAN

**Kaplamanın çakıştığı ölçülerek doğrulandı** — D-65'teki uyarı isabetliydi.
Beş adaydan yalnız **kenar dayanması** (zemin maskesinin içerik kutusu
ÇEVRESİNE değme oranı) iki kümeyi çakışmasız ayırıyor.

**Fiziksel gerekçe.** Çökmüş maske sahneyi ayırt etmediği için görüntü
çevresinin neredeyse tamamına dayanır (%58–96). Meşru arena zemininde koridorlar
kenara **ulaşır** — T51 tam bunu sağladı — ama yalnız kendi genişlikleri kadar;
çevrenin en fazla %34'ü. Kaplama bunu göremez, çünkü **çökmüş blob ile geniş
açık arena aynı alanı kaplar**.

**Uygulama.** İki sinyal, ikisi de aşılırsa ret:
`kaplama > 0.55` **VE** `kenar_dayanma > 0.45`. Eşik iki dağılımın ortası
((0,339+0,579)/2 = 0,459 → 0,45). Kaplama şartı KORUNDU: dar ama çevreye dayanan
sahneler meşru olabilir. Kapı yalnız **reddeder**, serbest alanı büyütmez.

**Sonuç — kendi ölçümüm, iki küme:**

    MESRU (kadraj arena)   n=234   YENI kapi   0   ESKI kapi   6
    COKUS (otopark)        n= 67   YENI kapi  67   ESKI kapi  67
    yanlis-negatif : 6/234 -> 0/234        cokme yakalama : 67/67 (degismedi)

**🔴 DENETİM BORCU.** Bu kodu **mimar yazdı** (anayasa madde 7 istisnası:
Codex'ler kotada, Claude-2 gece boyu çalıştı, kullanıcının açık talimatı).
**Kendi kodumu kendim onaylamıyorum** — T45 ile birlikte ayrı denetim
bekliyor.

**DOĞRULANAMADI.** Ölçüt iki zeminde sınandı; **gerçek arenada davranışı
bilinmiyor** (kamera yok). Görev kadrajında arena görüntüyü doldurursa zemin
çevreye daha çok dayanabilir. Kenar dayanması kaplamadan **daha dayanıklı**
ama bağışık değil; gerçek arena karesi geldiğinde ilk yeniden ölçülecek
büyüklüklerden biri budur.

---

### D-67 · KÖK NEDEN BULUNDU · 2 sınıflı veri kümesi modele "çatı zemin değildir" demiyor

**Bağlam.** T53 hipotezi (11-sınıf ön-eğitim + gerçek doku karışımı) koşuldu:
`v22_on10_gercek`, 200 epoch, 8,1 saat. Sonuç **yarı yarıya**:

    model              K1 IoU  K1 kesinlik  K1 duyar  K2 otopark ort  K2 maks
    v22_on10_gercek     0.512        0.782     0.597           80.6%    86.2%
    v21 (uretim)        0.311        0.813     0.335           81.0%    86.3%
    v17                 0.315        0.807     0.341            0.9%     7.0%

**Alan içi büyük kazanç** — IoU 0,311 → **0,512** (ölçülen en iyi; önceki rekor
v15'in 0,425'i), duyarlılık 0,335 → 0,597. **Alan dışı çöküş DEĞİŞMEDİ**
(%81,0 → %80,6). Gözle doğrulandı: v22 otoparkta bina **çatısını yine yeşil**
boyuyor. Araç tespiti belirgin iyileşmiş, çatı aynı.

**KÖK NEDEN — kodda doğrulandı.** `dataset/download_and_convert.py:72-83`:

    # RescueNet class IDs: 7=road-clear, 8=road-blocked, 0=background
    road_mask    = (lbl_np == 7)  -> sinif 0
    blocked_mask = (lbl_np == 8)  -> sinif 1
    # DIGER HER SEY DUSURULUYOR

2 sınıflı eğitim etiketlerinde bulunan id'ler: **yalnız 0 ve 1**.

RescueNet'in 11 sınıflı hâlinde `building_no_damage`, `building_minor`,
`building_major`, `building_total_destruction`, `tree`, `water`, `pool`
sınıfları **VAR** (`dataset/rescuenet_11sinif/data.yaml`). Ama 2 sınıfa
dönüşümde bunlar `blocked`'a eşlenmiyor, **etiketsiz arka plana düşüyor**.

Segmentasyonda etiketsiz arka plan **denetim almaz**. Yani modele hiçbir yerde
*"çatı zemin DEĞİLDİR"* denmiyor. Model "road-clear = zemin" öğreniyor ve karşı
örnek olmadığı için **"geniş düz yüzey = zemin"** diye genelliyor. Çatı tam
olarak budur.

**Her gözlemi açıklıyor:**
- v15 (11-sınıf ön-eğitim, asgari fine-tune) → otopark %24,1: ön-eğitimin bina
  bilgisi **kısmen hayatta kalıyor**.
- v17/v20 (sentetik arena fine-tune) → kör: sentetik arenada bina **yok**.
- v21/v22 (gerçek doku fine-tune) → görüyor ama çatı boyuyor: bina **denetimi
  yok**.

**Mimari ile çelişki.** Anayasa madde 15 *"zemin değil → engel"* diyor; bu kural
costmap'te **maskenin doğru olduğu varsayımıyla** uygulanıyor. Maskenin kendisi
aşırı kapsayıcı olunca kural hiç ateşlenmiyor. Kusur kuralda değil, **kurala
girdi üreten etiket semantiğinde**.

**Görev:** `TASK_QUEUE.md` **T54** — 2 sınıflı dönüşümde bina/ağaç/su/havuz
sınıflarını **`1 = blocked`'a eşle**, arka plana düşürme. Bir eğitim koşusu.

**v22 üretime ALINMAYACAK.** Alan içi daha iyi olsa da alan dışı çöküşü aynı;
şu an bizi koruyan şey T52'nin iki sinyalli kapısıdır, modelin kendisi değil.

---

### D-68 · ÖLÇÜM KARARI DEĞİŞTİRDİ · Sınıf ağırlığı eklenmedi: dengesizlik 7:1 değil 2:1

**Bağlam.** T54 kümesinde engel poligonu 850 → 22.356'ya çıkınca (D-67) sınıf
dengesizliği endişesi doğdu; kullanıcı sınıf ağırlığının şimdiden ayarlanmasını
istedi. **Ayarlamadan önce ölçtüm ve ölçüm kararı değiştirdi.**

**Poligon sayısı yanlış ölçüttür.** Segmentasyon kaybı PİKSEL görür; tek bir yol
poligonu yüzlerce küçük bina poligonundan geniş olabilir. Alan ölçümü:

    bilesen                      kare  trav alan%  blok alan%   oran
    rescuenet_2sinif_engelli     3502       14.8%       85.2%   1:5.8
    sentetik_arena               3003       36.2%       63.8%   1:1.8
    copy_paste_gercek             393       86.4%       13.6%   1:0.2
    KARISIM TOPLAMI              6898       32.0%       68.0%   1:2.1
    poligon toplami: trav 7775 · blok 57299            -> 1:7.4

Karşılaştırma için eski küme (`rescuenet_yolo`): poligon 1:1,3 · **alan 1:1,0**.

**Karar: sınıf ağırlığı EKLENMEDİ.** Karışım alan bazında **1:2,1** — segmentasyon
için normal, %32 traversable alan sağlıklı. Yanlış öncüle (1:7,4) dayanarak
ağırlık eklemek, tam da korktuğumuz **körlüğü kendi elimizle üretirdi**.

**Ama ölçüm gerçek bir riski başka yerde gösterdi.** `copy_paste_gercek`
karışımın yalnız **%5,7'si** (393/6898 kare) ve modelin **gerçek dokuda görme**
yeteneği tamamen oradan geliyor (D-12/D-18: bu bileşen çıkarılınca v17/v20 kör
kaldı). Ana koşuda K0 düşerse **çare sınıf ağırlığı değil, bu bileşenin payını
artırmaktır**.

**Yedek kol hazırlandı, çekilmedi:** `dataset/karisim_t54_gercek_agirlikli.yaml`
— aynı üç bileşen, `copy_paste_gercek` train yolu üç kez listelenerek pay
%5,7 → ~%15. Val DEĞİŞMEDİ (val'de tekrar örnekleme ölçümü bozar).

**Ders.** "Dengesizlik var" sezgisi doğruydu, **büyüklüğü yanlıştı**. Bu turda
dördüncü kez aynı kalıp: ölçüt seçmeden önce ölçütün ne gördüğünü sor. Poligon
sayısı kayıp fonksiyonunun gördüğü şey değil.

---

### D-69 · MIMAR DENETIMI · T45 GECTI · T52 KUSURLU (esik yanlis yerde)
Denetleyen: Claude 2 · 2026-08-12 · anayasa madde 7 (mimar kendi kodunu onaylayamaz)
Denetlenen: commit `8010da8` (T45) ve `69e0409` (T52) · GPU T54'te, olcumler CPU'da

════════ DENETIM 1 — T45 (`arena_icerik_ve_mpp`) · **GECTI** ════════

**IDDIA 1 DOGRULANDI.** Serit sinirlari uretec ve karar yolunda ayni. Dort
en-boy oraninda bagimsiz olcum (`_preprocess` ile `arena_icerik_ve_mpp` yan yana):

    1024x576 : karar (0,224,1024,576) [342,683] | uretec (0,0,1024,576) [342,683]  AYNI
    1280x720 : karar (0,280,1280,720) [427,854] | uretec (0,0,1280,720) [427,854]  AYNI
    1024x1024: karar (0,0,1024,1024)  [342,683] | uretec (0,0,1024,1024)  [342,683] AYNI
     800x600 : karar (0,100,800,600)  [267,534] | uretec (0,0,800,600)   [267,534]  AYNI

(Komsitteki `[341,682]` ile benim `[342,683]` ayni siniri iki farkli konvansiyonla
yaziyor — `int(iw/3)` ile "seridin degistigi ilk x". Kusur DEGIL.)

**IDDIA 2 — mpp yonu GUVENLI (madde 15).** `mpp` kisa kenar yerine GENISLIGE
eslendigi icin kuculuyor; `r_gerekli_px = R_GEREKLI_M / mpp` ise BUYUYOR:

    kare        ESKI mpp   YENI mpp   ESKI r_px  YENI r_px   yon
    1024x576    0.086806   0.048828       12.67      22.53   DARALTIR (guvenli)
    1280x720    0.069444   0.039062       15.84      28.16   DARALTIR (guvenli)
    1024x1024   0.048828   0.048828       22.53      22.53   etkisiz (kare goruntu)

C-uzayi `{dist >= r_gerekli_px}` oldugu icin r buyudukce serbest alan yalniz
DARALIR. Madde 15 ihlali YOK.

**Manifest notu GERCEGI SOYLUYOR.** `ARENA_OLCEK_KAYNAGI` artik
*"...HTAB / kaynak karenin GENISLIGI; gercek kamera mpp olcumu degildir"*
diyor — formulle birebir ortusuyor.

**Egitim kipi BOZULMADI.** AST ile izlendi: `arena_icerik_ve_mpp` yalniz
`arena_cesidi_uret` icinden (`:1023`) cagriliyor; o da `main` icinde
`if args.arena:` guardi altinda (`:1229`). Rastgele (egitim) kip bu yola hic
girmiyor.

⚠ **KUCUK KUSUR (bloke etmez): KIRIL KARAKTER.**
`scripts/copy_paste_augmentation.py` docstring'inde 1 adet U+0435 CYRILLIC
SMALL LETTER IE var: *"seritleri icerik GENISLIGINI **ucе** bolerek uretir"*.
Bu depoda ayni sinif daha once yakalanmisti. Davranisa etkisi YOK; tek
karakterlik belge duzeltmesi.

════════ DENETIM 2 — T52 (iki sinyalli kapi) · **KUSURLU** ════════

**(1) EKSIK TEST YAZILDI.** `tests/test_zemin_kapisi_iki_sinyal.py` (16 test)
dort birlesimi de kilitliyor: kaplama YUKSEK+kenar DUSUK -> ATESLEMEZ ·
YUKSEK+YUKSEK -> ATESLER · DUSUK+YUKSEK -> ATESLEMEZ · DUSUK+DUSUK -> ATESLEMEZ.
Ayrica sinir davranisi (`>` semantigi), detay metninin IKI olcumu de tasidigi
ve icerik kutusu kirpmasi.

**MUTASYON KONTROLU (testin vakum olmadigi kaniti):** kapi T52 oncesi TEK
SINYALLI haline dondurulunce **16 testin 8'i DUSUYOR**; duzeltilmis kodda 0.

**Mevcut `test_zemin_kaplama_kapisi.py` gercekten kapsamiyordu — dogrulandi.**
Onun `_kaplamali` fiksturu SOL-DOLGU oldugu icin kenar dayanmasi hep yuksek
cikiyor (kaplama %56 -> kenar 0,536 · %95 -> 0,770); "kenar DUSUK" dali HIC
sinanmiyordu. Mimarin itirafi dogru.
⚠ Not: o paketin en dusuk kenar degeri **0,536**. Kenar tavani 0,52'nin uzerine
cikarilirsa o testler pay olmadan kirilir.

**(2) BAGIMSIZ OLCUM — IDDIA TAM DOGRULANMADI.**
Mimarin betigi kullanilmadi; kume kendim kuruldu. MESRU = yer gercegi
maskeleri (sentetik_arena val 60 + kadraj val 26 + kadraj train 234 = **320**,
model YOK). COKMUS = v21'in otopark ciktisi (**67** kare, CPU cikarim).

    ESKI kapi (yalniz kaplama): mesru ELENEN 11/320 · cokme YAKALANAN 67/67
    YENI kapi (iki sinyal)    : mesru ELENEN  1/320 · cokme YAKALANAN 67/67

Yani iyilesme GERCEK ve buyuk, ama mimarin bildirdigi **"0/234"** daha genis bir
mesru kumede **saglanmiyor**: 1 mesru kare hala eleniyor.

**(4) 🔴 ESIK YANLIS YERDE — asil bulgu.** Kaplama tavanini asan 11 mesru
karenin kenar degerleri ve cokme kumesinin asgarisi:

    mesru (kaplama>tavan) kenar : 0.251 0.274 0.275 0.284 0.294 0.296 0.298
                                  0.315 0.315 0.392 **0.452**
    cokme kenar asgarisi        : **0.583**
    GERCEK BOSLUK               : [0.452, 0.583]   orta nokta 0.517

Mimar esigi "0,339 ve 0,579'un ortasi" diye 0,45 secmis. Olculen mesru azami
**0,452** — yani 0,45'in **USTUNDE**. Esigin mesru taraftaki payi **-0,002**
(NEGATIF) ve tam bu yuzden 1/320 kare eleniyor.

    KENAR ESIGI SUPURMESI (kaplama esigi sabit %55)
      esik   mesru ELENEN  cokme YAKALANAN   mesru payi  cokme payi
      0.45        1/320            67/67         -0.002      +0.133
      0.46        0/320            67/67         +0.008      +0.122
      0.50        0/320            67/67         +0.048      +0.083
      0.52        0/320            67/67         +0.068      +0.062   <- dengeli
      0.58        0/320            67/67         +0.128      +0.003
      0.60       0/320            64/67         +0.148      -0.017   <- cokme kacar

**ONERI: kenar tavani 0,45 -> 0,52.** Iki tarafta da ~0,065 pay birakir,
mesru eleme 0/320, cokme yakalama 67/67 korunur. Deger sozlesme sahibinindir;
bu denetimde DEGISTIRILMEDI.

**(3) ICERIK KUTUSU — kirpma DOGRU, ama FAIL-OPEN.**
Kirpma dogru calisiyor (sol yari icerik -> 1,000 · sag yari -> 0,000 · tasan
genislik kirpiliyor). Ancak GECERSIZ `icerik`te (`(0,0,0,H)`, `x0 > genislik`)
`zemin_kaplamasi` ve `zemin_kenar_dayanmasi` 0,0 donuyor ve kapi **SUSUYOR** —
tamamen dolu, cevreye tam dayanan bir maske bile gecebiliyor. Kardes sozlesme
fonksiyonlari (`rota_guven_reddi`, `rota_olcek_reddi`, `mpp_irtifadan`)
gecersiz girdide FAIL-CLOSED; bu kapi degil.
**Uretim yolu KORUNUYOR:** `analyze_path` icerik kutusunu `:606`'da dogrulayip
`ALAN_YETERSIZ` donuyor, kapi `:619`'da yani SONRA kosuyor. Bu yuzden bulgu
**sozlesme tutarsizligi**dir, uretim acigi degil. Yeni testte davranis
BELGELENDI (onaylanmadi).

⚠ **KUCUK: kose pikselleri 2x agirlikli.** Pay `2*(ih+iw)`, sayac kose
piksellerini iki kez sayiyor; olculdu: tek kose pikseli tek kenar pikselinin
**2,00 kati** katki veriyor. Azami yine 1,0'da kaldigi icin tutarli, buyuk
kutularda etkisi ihmal edilebilir. Kayit icin.

**KOSULAN KAPILAR:** `codes/test_rota_sentetik.py` **15/15** ·
`unittest discover -s tests -q` -> **Ran 297 tests · OK**.

**KARAR**
  · **T45 — MIMAR DENETIMI GECTI** (yalniz 1 karakterlik belge kusuru).
  · **T52 — GECMEDI.** Mantik dogru ve iyilesme gercek, ama (a) bildirilen
    "0/234" daha genis mesru kumede saglanmiyor (1/320), (b) esik olculen
    mesru azaminin ALTINDA ve pay NEGATIF. Gorev `[ ]` birakildi; eksik test
    yazildi ve mutasyonla dogrulandi.

---

### D-70 · BOŞLUK · Kadraj kümesi AÇIK ŞERİDİ kaydetmiyor: şerit doğruluğu orada ölçülemez

**Nasıl çıktı.** T51'in açık bıraktığı "3/18 yanlış şerit" kalemini geçerli
zeminde ölçmeye çalıştım. Yer gerçeği şeridini `class-0` poligonlarının
**baskın şeridi** olarak türettim ve %83,7 uyum buldum. **Sayıyı geri
çekiyorum** — türetme yanlış.

**Neden yanlış.** Üç şeritli bir arenada `class-0` (traversable) **üç koridoru
da** kaplar; şeritleri ayıran şey zemin değil, üzerlerindeki **bariyerlerdir**.
Dolayısıyla "traversable maskesinin baskın şeridi" ile "açık şerit" farklı
şeylerdir. Hataların deseni de bunu gösteriyordu: rota **tamamen tek şeritte**
(dağılım `(0,0,540)`) olmasına rağmen "GT" başka şerit diyordu — bir şerit
seçim hatası değil, ölçütün yanlışlığı.

**Asıl boşluk.** `O:\navitas-local-train\calisma\sentetik_arena_kadraj` içinde
**manifest yok**; küme yalnız `images/`, `labels/`, `data.yaml` taşıyor. Hangi
şeridin açık olduğu **hiçbir yere kaydedilmiyor**. Karşılaştırma için
`data/arena_kompozit` bunu taşıyor (`arena.acik_serit`, `kapali_seritler`,
`bariyerler`) ve T40'ın gerçek kapısı tam o sayede kurulabilmişti.

**Sonuç:** Kadraj kümesi karar zincirinin **geometrisini** sınayabiliyor
(rota çıkıyor mu, uç banda değiyor mu) ama **şerit doğruluğunu** sınayamıyor.
En iyi zeminimizin en değerli özelliği eksik.

⚠ **T51'in KAPI 2 sonucu ("yer gerçeği şerit ile uyumsuzluk 3/12") aynı
türetme sorununa maruz olabilir.** Nasıl türetildiği görevde yazılı değil;
denetimde sorulmalı. Kendi sayımı geri çektiğim gibi o da doğrulanmadan
kullanılmamalı.

**Görev:** `TASK_QUEUE.md` **T55** — kadraj üreteci `acik_serit`,
`kapali_seritler` ve bariyer kutularını manifest'e yazsın (arena_kompozit
kalıbı). Bu olmadan en iyi zeminimizde şerit doğruluğu ölçülemez.

---

### D-71 · MİMAR KARARI · T52 eşiği 0,45 → 0,50; fail-OPEN kusuru düzeltilecek

**Denetimi kabul ediyorum.** Claude-2 (D-69) benim yazdığım T52 kapısında üç
kusur buldu; üçü de gerçek. Kendi kodumu onaylamamamın gerekçesi tam olarak bu.

**1 · Eşik yanlış yerdeydi.** Benim ölçümüm 234 kare (model çıkarımı); onunki
**320 yer gerçeği maskesi** — daha geniş ve daha uygun bir meşru küme.

    mesru kenar AZAMISI  : 0.452        cokme kenar ASGARISI : 0.583
    GERCEK BOSLUK        : [0.452, 0.583]
    benim esigim 0.45    : mesru azaminin ALTINDA (pay -0.002)
    bildirdigim 0/234    : genis kumede 1/320 (saglanmiyor)

**KARAR: `ZEMIN_KENAR_DAYANMA_TAVANI` = 0.45 → `0.50`.**
Claude-2 `0.52` önerdi (gerçek boşluğun ortası 0,517). **0,50'yi seçtim**, çünkü
kendi (c) bulgusu üçüncü bir kısıt getiriyor: mevcut `test_zemin_kaplama_
kapisi.py`'nin en düşük **çökme** kenar değeri **0,536**; tavan onun altında
kalmalı yoksa o testler payı olmadan kırılır. Üç kısıtın kesişimi:

    mesru azamisi 0.452  <  TAVAN  <  0.536 (mevcut test)  ve  < 0.583 (cokme)
    0.50 -> mesru payi +0.048 · test payi 0.036 · cokme payi 0.083

0,52 meşru tarafta biraz daha rahat ama test payını **0,016**'ya düşürüyor.
0,50 üç tarafta da pay bırakıyor. Fark ikisi arasında gürültü tabanının
(0,04) altında değil, bu yüzden gerekçe kayda geçiyor.

**2 · Geçersiz `icerik`te kapı fail-OPEN.** Kardeş sözleşme fonksiyonları
(`rota_guven_reddi`, `rota_olcek_reddi`) bozuk girdide fail-closed dönüyor;
benimki geçiyor. Üretim yolu `analyze_path:606` doğrulaması sayesinde korunuyor,
ama bu **sözleşme tutarsızlığıdır** ve çağrı yeri değişirse sessizce açılır.
**Düzeltilecek: bozuk/taşan `icerik` → fail-closed ret.**

**3 · Köşe pikselleri 2× sayılıyor.** Ölçüldü; azami 1,0'da kaldığı için sonuç
tutarlı ama ölçüt tanımı gevşek. **Düzeltilecek** (köşeler bir kez sayılacak) ve
düzeltme sonrası iki dağılım **yeniden ölçülecek** — eşik ona göre teyit edilecek.

**Takdir.** Eksik testi Claude-2 yazdı (`tests/test_zemin_kapisi_iki_sinyal.py`,
16 test) ve **mutasyon kontrolü** koydu: kapı tek sinyalli hâline döndürülünce
16 testin 8'i düşüyor. Testin vakum olmadığını kanıtlayan doğru yöntem budur.

**Kayıt numarası çakışması.** Bu kayıtla birlikte üçüncü kez oldu (D-39/40/41,
sonra D-60, şimdi D-69). Kendi kaydımı **D-70**'e taşıdım; Claude-2'nin D-69'una
dokunmadım. Kalıcı çözüm: numarayı yazmadan önce `grep '^### D-' REVIEW_LOG.md |
tail -1` ile son numarayı okumak — bunu görev şablonuna eklemeliyim.

---

### D-72 · COZULDU · T52 duzeltmesi: tavan 0,50 · fail-closed · kose tek sayim
Uygulayan: Claude 2 · 2026-08-12 · mimar karari D-71, denetim bulgulari D-69
Dosyalar: `codes/karar_sozlesmesi.py`, `tests/test_zemin_kapisi_iki_sinyal.py`

**SIRA ONEMLIYDI.** Once kose duzeltmesi yapildi, SONRA esik olculdu — cunku
kose duzeltmesi kenar degerlerini asagi ceker ve esigi once sabitlemek olcumu
gecersiz kilardi.

**(3) KOSE CIFT SAYIMI DUZELTILDI.** Eski surum dort kenari ayri toplayip
paydayi `2*(ih+iw)` aliyordu; kose pikselleri iki kez sayiliyordu (olculdu:
kose/kenar katki orani **2,00x**). Yerine cerceve maskesi kondu: her cevre
pikseli **bir kez** sayilir, payda `count_nonzero(cerceve)`. Dogrulandi:
kose/kenar orani **1,00x**, tek kose pikseli tam `1/(2W+2H-4)`, tam dolu maske
1,0, dejenere kutular (1xN, Nx1, 1x1) 1,0.

**(1) TAVAN 0,45 -> 0,50 — kose duzeltmesinden SONRA yeniden olculdu.**
320 mesru yer-gercegi maskesi + 67 cokme karesi (v21 otopark, CPU cikarim):

    (a) MESRU azami (kaplama tavanini asan 11 kare) : 0,453
    (b) mevcut test paketinin COKME fiksturu asgari : 0,536
    (c) COKMUS kume kenar asgarisi                  : 0,583

    gecerli aralik (0,453 · 0,536) — genislik 0,083
      tavan 0,46 -> mesru +0,007 · test +0,076 · cokme +0,123
      tavan 0,50 -> mesru +0,047 · test +0,036 · cokme +0,083   <- SECILDI
      tavan 0,52 -> mesru +0,067 · test +0,016 · cokme +0,063

Kose duzeltmesi degerleri pratikte oynatmadi (mesru azami 0,452 -> 0,453;
cokme asgarisi 0,583 degismedi) — buyuk kutularda 4 kose pikseli ihmal
edilebilir. D-71'in payları (+0,048 / +0,036 / +0,083) bagimsiz olcumle
**dogrulandi**; 0,50 gecerli araligin pratikte ORTASI (orta nokta 0,4945).

**(2) FAIL-CLOSED UYGULANDI.** Yeni `icerik_kutusu_gecerli_mi(icerik, sekil)`:
dortlu olmali; her ogesi bool OLMAYAN, sonlu, TAM SAYI degerinde; kutu
pozitif boyutlu ve maskeye TAM sigmali. `zemin_maskesi_reddi` gecersiz kutuda
veya 2 boyutlu olmayan maskede artik **REDDEDER**.

**RET SEBEBI KARARI — `ALAN_YETERSIZ` (yeni kod TURETILMEDI).** Gerekce olculdu:
`codes/rpi_inference.py:606-611` **zaten** gecersiz/bos icerik kutusunu
`ALAN_YETERSIZ` ile reddediyor. Ikinci bir sebep kodu turetmek ayni fiziksel
kosula iki farkli kanonik cevap uretirdi. Ayrica CONTRACTS SS6.4/4 "yeni ret
yolu once tabloya yazilir" diyor ve `CONTRACTS.md` bu turda dosya iznimde
DEGILDI — yeni kod eklemek sozlesmeyi kodun gerisinde birakirdi.
⚠ **BELGE BORCU (mimara):** SS6.4'teki `ALAN_YETERSIZ` satiri yalniz "koridor
alani `min_area_ratio` altinda" diyor; kod onu `:606`'dan beri "icerik kutusu
gecersiz/bos" icin de kullaniyor. Satirin metni genisletilmeli.

**KOSULAN KAPILAR (gercek cikti).**

    320 MESRU / 67 COKME (yururlukteki kod, tavan 0,55 + 0,50)
      MESRU elenen     : 0/320    GECTI
      COKME yakalanan  : 67/67    GECTI
    MUTASYON KONTROLU (22 test)
      duzeltilmis kod                    : 0 basarisiz
      MUTASYON 1 tek sinyalli (T52 oncesi): 21 basarisiz
      MUTASYON 2 fail-OPEN (D-69 oncesi) : 14 basarisiz
    tests/test_zemin_kapisi_iki_sinyal.py : 22/22 OK
    tests/test_zemin_kaplama_kapisi.py    : gecti (tam pakette)
    codes/test_rota_sentetik.py           : 15/15
    unittest discover -s tests -q         : Ran 303 tests · OK
    git diff --check exit 0 · Jetson ikizleri BIREBIR

**TEST PAKETI GENISLETILDI** (16 -> 22): gecersiz icerigin 11 bicimi
(sifir/tasan/negatif/kesirli/bool/eksik oge/NaN/inf), gecerli kutunun
(int ve tam-degerli float) reddedilmedigi regresyonu, 2 boyutlu olmayan maske,
kose-kenar esit agirlik, cevre paydasi, dejenere kutular ve **fail-closed dali
icin ayri mutasyon kontrolu**.

**ACIK KALAN.** `tests/test_zemin_kaplama_kapisi.py`'nin `_kaplamali` fiksturu
en dusuk 0,536 kenar uretiyor; tavan 0,536'nin uzerine cikarilirsa o paket
payi olmadan kirilir. Bu, esigin UST sinirini pratikte veri degil TEST
belirliyor demektir — fiksturun kenar degerinden bagimsizlastirilmasi ayri
gorevdir (bu turda kapsam disi).

---

### D-73 · MİMAR DENETİMİ · T52 düzeltmesi GEÇTİ

**Bağımsız doğrulamam** (Claude-2'nin betiği kullanılmadı):

    1 · GECERSIZ ICERIK -> fail-CLOSED mu?
        tasan / negatif / kesirli / sifir alan / bool / None uye
        -> ALTISI DA RET (sebep ALAN_YETERSIZ)
    2 · KOSE CIFT SAYIMI
        dort kose dolu -> 0.01010   tek sayim beklentisi 0.01010   1.0x
    3 · KAPI MANTIGI
        kaplama YUKSEK + kenar YUKSEK -> RET
        kaplama ORTA  + kenar SIFIR   -> gecti
        kaplama DUSUK + kenar dusuk   -> gecti

**Payda düzeltmesi benim formülümden daha doğru.** Çevre `2(h+w)−4` alınmış;
köşeler hem payda hem paydada tek sayılıyor. Benim yazdığım `2(h+w)` köşeleri
payda tarafında da çift sayıyordu.

**Sıra doğru korunmuş** — önce köşe düzeltmesi, sonra eşik ölçümü. Ters sırada
ölçüm geçersiz olurdu; bunu görevde şart koşmuştum ve uyulmuş.

**Ret sebebi seçimi gerekçeli.** `ALAN_YETERSIZ` keyfi değil: `rpi_inference.py:
606-611` aynı fiziksel koşulu (geçersiz/boş içerik kutusu) **zaten** bu kodla
reddediyor. Yeni kod türetmek aynı koşula iki isim verirdi.

**D-71'in payları bağımsız ölçümle doğrulandı** (0,453 / 0,536 / 0,583); köşe
düzeltmesi değerleri pratikte oynatmadı.

**Kapılar:** `codes/test_rota_sentetik.py` **15/15** · tam paket **303 OK**.

**Denetim borcum kapandı.** T45 (D-69) ve T52 (bu kayıt) bağımsız denetimden
geçti. Madde 7 istisnasıyla yazdığım iki değişikliğin ikisi de artık onaylı;
biri kusurlu bulunup düzeltildi — istisnanın neden ayrı denetim gerektirdiğinin
ölçülmüş kanıtı.

---

### D-74 · BELİRLEYİCİ · Alan içi IoU 2,2× arttı, KARAR DÜZEYİNDE hiçbir şey değişmedi

**T54 koşuldu.** `v23_t54_engelli` — 11-sınıf ön-eğitim + bina/ağaç/su denetimi
eklenmiş 2 sınıflı karışım. 191/200 epoch (erken durma), 7,9 saat.

**Alan içi üçüncü sıçrama:**

    model              K1 IoU  K1 kesinlik  K1 duyar  K2 otopark ort
    v23_t54_engelli     0.698        0.826     0.819           81.1%
    v22_on10_gercek     0.512        0.782     0.597           80.6%
    v21 (uretim)        0.311        0.813     0.335           81.0%
    v17                 0.315        0.807     0.341            0.9%

IoU 0,311 → 0,512 → **0,698**. Duyarlılık 0,335 → 0,819. Ölçülen en iyi model.

**Ama karar düzeyinde HİÇBİR ŞEY değişmedi:**

    model              KADRAJ ARENA (60)              OTOPARK (30)
    v23_t54_engelli    rota 43/60 · kaplama %17,0     0/30 (30/30 ZEMIN_SUPHELI)
    v21 (uretim)       rota 43/60 · kaplama %17,4     0/30 (30/30 ZEMIN_SUPHELI)

Şerit dağılımları bile aynı (v23: 2→19, 3→17, 1→7 · v21: 2→19, 3→16, 1→8).
Ret dağılımı da: ikisinde de 17 ret.

**Ve çatı hâlâ yeşil.** 10.818 bina poligonu eğitime girdi; otoparkta bina
çatısı gözle bakıldığında hâlâ tamamen geçilebilir işaretli, kaplama %73,6.

**KARAR: ÜRETİM MODELİ DEĞİŞTİRİLMİYOR.** v23 ölçülebilen her alan-içi ölçütte
daha iyi, ama **önemli olan yerde ölçülebilir bir fark üretmiyor**. K-3 zaten
söylüyordu: *"mAP arena sıralamasını tersine çeviriyor."* Bu kayıt onun IoU
karşılığıdır — **alan-içi doğruluk arena kararını öngörmüyor.** Ölçülmemiş bir
fayda için üretim modeli değiştirilmez.

**Üç koşunun ortak dersi.** T50-FAZ2 (v15), T53 (v22), T54 (v23): üçü de alan
içi doğruluğu yükseltti, üçü de otopark çöküşünü ve arena karar sayısını
değiştirmedi. **Eğitim ekseni, arena kararının darboğazı değil.** Dördüncü bir
koşu (gerçek doku payı) aynı sonucu verme ihtimali yüksek; kullanıcının
onayladığı "körlüğe savrulursa kaldıracı çek" koşulu **gerçekleşmedi**
(savrulma olmadı), bu yüzden kaldıraç ÇEKİLMEDİ.

**🔴 YAN BULGU — kendi kapımız kendi test zeminimizi yedi.** K0 (gerçek dokuda
tespit tabanı) ve K3 (karar doğruluğu) kompozit arena kümesinde ölçülüyordu;
o kümenin arka planı otopark olduğu için iki sinyalli kapı (T52) artık 9/9
reddediyor. Kapı doğru çalışıyor — küme gerçekten çökmüş maske üretiyor — ama
**K0/K3 artık ölçülemez durumda.** Kapı betiği de K0'ı hiç uygulamamış
(JSON yalnız k1/k2/k3 taşıyor). Ölçüt kümesi kadraj zeminine taşınmalı.

**Sırada eğitim YOK.** Kanıt başka yeri gösteriyor: kadraj arenasında 17/60 kare
hâlâ reddediliyor (UC_BANT_TEMAS_YOK 7 · GORUS_HATTI_KOPUK 8 · MASKE_YOK 2) ve
bu sayı **iki modelde de aynı** — yani karar yolunda, modelde değil. Ayrıca
şerit doğruluğu D-70 yüzünden hâlâ ölçülemiyor.

---

### D-75 · 17/60 RET ARAŞTIRMASI · Yarısı MODEL kusuru; D-74'teki çıkarımım yanlıştı

**Yöntem.** Aynı 60 kadraj karesi iki girdiyle koşuldu — tek değişken maske
kaynağı: **A** model çıkarımı, **B** etiket poligonlarından kusursuz yer gerçeği.
A reddedip B kabul ederse kusur MODELDE; ikisi de reddederse karar yolu/sahne.

**Sonuç (doğru ölçekle, mpp = 0,0781):**

    A · MODEL maskesi     : rota 41 · UC_BANT 10 · GORUS 7 · MASKE_YOK 2
    B · YER GERCEGI maske : rota 49 · UC_BANT  3 · GORUS 8
    ayrisan kare: 10  (9 model reddi -> GT rota · 1 ters yon)

**1 · Retlerin yaklaşık YARISI MODEL kusuru.** Dokuz karede kusursuz maskeyle
rota çıkıyor, model maskesiyle çıkmıyor. Model tarafı hâlâ kayıp üretiyor.

**2 · D-74'teki çıkarımım YANLIŞTI — düzeltiyorum.** Orada *"ret sayısı iki
modelde de aynı, yani karar yolunda, modelde değil"* yazmıştım. Bu geçersiz bir
çıkarım: **iki modelin eşit kötü olması modeli aklamaz**, ikisinin de aynı zaafı
paylaştığını gösterir. Doğru ayrım modeli devreden çıkarmakla yapılır ve
yapıldığında kusurun yarısı modelde çıkıyor. D-74'ün üretim modeli kararı
(v23 → değiştirilmiyor) bundan etkilenmiyor; **çıkarımın kendisi düzeltiliyor.**

**3 · Kendi ölçüm hatam: yanlış `mpp`.** Kadraj kareleri 640×640 ve arena 50 m →
doğru `mpp = 0,0781`. Ben kompozit için türetilmiş **0,0868**'i kullanmıştım
(`r_gerekli_px` 12,7 yerine 14,1 olmalıydı). Etkisi: her iki kolda **2'şer rota**.
T51 ve D-74'teki `43/60` sayısı bu hatayı taşıyor; doğrusu **41/60**. İki kol da
aynı hatayla ölçüldüğü için **modeller arası fark sonucu değişmiyor**, ama mutlak
sayı düzeltildi.

**4 · Retler darlıktan DEĞİL.** Yer gerçeği koridor yarı-genişliği: min 8,9 px ·
medyan **54,9 px** · maks 110,9. Doğru ölçekte medyan **4,29 m** yarı-genişlik →
koridor ~8,6 m; gereken 1,10 m. Gereken yarıçapı sağlamayan kare **1/60**.
Uç bantlar da hiç boş değil (üst 0/60 · alt 0/60) — T51'in kadraj düzeltmesi
yer gerçeği düzeyinde tam çalışıyor.

**Kalan soru T55'e BAĞLI.** Kusursuz maskeyle 11/60 kare hâlâ reddediyor
(UC_BANT 3 · GORUS 8). Bunların **meşru fail-closed mu** (o karede gerçekten
açık güzergâh yok) yoksa karar yolu kusuru mu olduğu, hangi şeridin açık
olduğu kayıtlı olmadan **belirlenemez** (D-70). T55 inmeden bu kalem kapanmaz.

---

### D-76 · COZULDU (kapi 2 SINIRLI) · T55: kadraj kumesi manifest yaziyor
Uygulayan: Claude 2 · 2026-08-12 · kanit D-70 · dosya `51_sentetik_arena.py`

**TASARIM — `acik_serit` URETIM ANINDA kaydedilir.** D-70'in uyarisi dogrulandi
ve tasarima girdi: uc seritli arenada `class-0` UC KORIDORU DA kaplar; seritleri
ayiran zemin degil, uzerlerindeki bariyerlerdir. Bu yuzden serit durumu
(`kapali`/`acik`/`dar`) yalniz uretim dongusunde bilinir ve orada kaydedilir.

**UYGULAMA — donus aritesi DEGISMEDI.** `sahne_uret(..., bilgi=None)`: `bilgi`
bir sozlukse doldurulur, aksi halde hicbir sey degismez. Boylece mevcut cagri
yerleri (ve egitim kipi) hic etkilenmez. Serit numarasi `serit_no`'dan OKUNUR
(`codes/karar_sozlesmesi`) — uretecte ucte-bir hesabi CIPLAK yazilmadi; iki
kume artik ayni otoriteyi kullaniyor.

Manifest `data/arena_kompozit` alan adlarini birebir tasir: `acik_serit`,
`kapali_seritler`, `bariyerler` (kutu + pencere), `icerik`, `mpp`,
`olcek_kaynagi`, `beklenen_durum`, `beklenti_kaynagi`, `tohum`,
`uretec_seritleri`. Ek olarak `acik_serit_adaylari`, `belirsiz` ve
`arena_x_araligi`.

**KAPILAR (gercek cikti).**

    KAPI 1  kare == kayit : 260 goruntu / 260 kayit · dosyasi olmayan kayit 0   GECTI
    KAPI 4  geometri degismedi (istatistik karsilastirmasi):
              ESKI  kare 260 · traversable 550 · blocked 879 · zemin alan 0,2171 ± 0,1522
              YENI  kare 260 · traversable 550 · blocked 879 · zemin alan 0,2171 ± 0,1522
    KAPI 5  egitim kipi denkligi (4 tohum: kimlik + sinif + RNG durumu +
            geometrik) hepsi True                                              GECTI
            ek: `bilgi` toplamanin yan etkisi YOK (3 tohumda kimlik+RNG esit)
    depo    codes/test_rota_sentetik.py 15/15 · discover -s tests -q Ran 303 OK

⚠ **KAPI 4'te BAYT karsilastirmasi UYGULANMADI — uygulanamaz.** Uretec ZATEN
tekrarlanabilir degil (D-64: degistirilmemis kodla ayni seed'le uc kosum uc
farkli hash). Yerine etiket istatistikleri karsilastirildi ve poligon sayilari
BIREBIR, zemin alan dagilimi dort haneye kadar ayni cikti.

🔴 **KAPI 2 SINIRLI GECTI — gorevin yazdigi olcut olculemedi.**
Gorev "yer gercegi maskeleriyle **rota_bul** manifest'in `acik_serit`'ini
buluyor" diyordu. Olculdu: `rota_bul` bu kumede **hic karar vermiyor**.

    139 net kare (belirsiz olmayan), rota_bul durumlari:
      BELIRSIZ_TEK_KAPI 65 · MASKE_YOK 28 · KAPI_YOK 27 · BELIRSIZ_COKLU 19
      DOGRU 0 · YANLIS 0 · karar vermeyen 139/139

Sebep D-58'de kayitli: `rota_bul` UC KAPILI arena dedektorudur
(`costmap_path_finder.py:781`, `n_kapi != 3 -> BELIRSIZ_COKLU`). Sentetik
uretec 2-5 serit uretiyor, dolayisiyla nadiren tam 3 kapi sunuyor. Olcut
bu kumede ISLEMEZ.

Uretim karar yolu (`analyze_path` + K-B) ile olculdu:

    analyze_path : DOGRU 85 · YANLIS 4 · RET 50   ->  UYUMSUZLUK 4/89 (%4,5)

**KAPI 3 — ILK OLCUM DUSTU, DEGISMEZ YANLISTI; DUZELTILIP GECTI.**
Ilk pozitif kontrol "acik serit kapatilinca ETIKET degismeli" diyordu:
**87/89**. Iki basarisizlik incelendi — kusur kapida DEGIL, benim
enjeksiyonumdaydi:

    sa_000063  GT=1 once=1 sonra=1 · kapatilan bantta kalan serbest piksel 0
               rota y=h/2 civarinda x=237 -> SERIT 2 (komsu seritten dolanmis)
    sa_000156  GT=2 once=2 sonra=2 · kapatilan bantta kalan serbest piksel 0
               rota y=h/2 civarinda x=452 -> SERIT 3 (komsu seritten dolanmis)

Koridorlar ucte-bir sinirlarini asarak kivriliyor; kapatilan seridin DISINDAN
dolanan rota MESRU ve GUVENLIDIR. Etiket degismiyor cunku `road` darbogaz
seridini adlandirir ve darbogaz baska yerde. Dogru degismez **"kapatilan
bantTAN GECILMEMESI"**dir; oyle olculdu:

    rota kapatilan bantTAN GECMIYOR (veya RET) : 89/89   GECTI
    (etiket degisti: 84/89 — bilgi amacli, KAPI DEGIL)

**BULGU — kumenin yarisi BELIRSIZ.** 260 karenin **121'inde** birden fazla
karar seridi gecilebilir serit iceriyor; tek bir `acik_serit` yazilamiyor ve
`belirsiz: true` isaretlenip `acik_serit_adaylari` yaziliyor. Kalan **139**
kare tek cevapli yer gercegi tasiyor. Bu, uretecin 2-5 serit uretmesinin
dogal sonucudur — T55 kapsaminda GEOMETRI DEGISTIRILMEDI (kapi 4 geregi).
Tek cevapli kare oranini yukseltmek isteniyorsa uretecin kadraj kipinde
serit sayisi 3'e sabitlenmelidir; bu AYRI bir gorevdir.

**Kume yerinde:** `O:\navitas-local-train\calisma\sentetik_arena_kadraj`
(manifest dahil). Onceki manifestsiz surum
`...\sentetik_arena_kadraj_ONCEKI_manifestsiz` olarak saklandi.

**DOGRULANAMADI**
  1. Manifest'in `acik_serit` degerlerinin GORSEL dogrulugu — 260 karenin
     hicbiri gozle denetlenmedi; dogruluk uretecin kendi durum kaydina dayanir.
  2. `mpp` degeri kamera olcumu degildir (kompozit kumeyle ayni varsayim).

---

### D-77 · Dokuz model kaybı araştırıldı: karar yolu TEMİZ, kusur zeminin GERÇEKÇİLİĞİNDE

**T55 yer gerçeği geldi; iki açık soru kapandı.**

**1 · Kusursuz maskeyle gelen 11 ret — HEPSİ MEŞRU.**

    manifest 'acik serit YOK/belirsiz' diyor : 11   (MESRU)
    manifest ACIK SERIT VAR diyor            :  0   (KUSUR)

**Karar yolunda kusur yok.** Açık şerit olan her karede rota üretiyor. D-75'te
açtığım soru kapandı; T55'in kendi ölçümü de aynı yöne bakıyor: `analyze_path`
şeridi **85/89 doğru** (%95,5).

**2 · Dokuz model kaybı saf AZ-TESPİT.**

    kapA (model) : %0,0 – %13,2      kapB (yer gercegi) : %13,1 – %35,7
    zemin kaybi  : ort %16,8 · min %8,6 · maks %28,9
    iki karede model SIFIR zemin buluyor (sa_000059, sa_000072)

**3 · v23 dokuz kayıptan yalnız 1'ini kurtarıyor** (kaplama biraz yükseliyor:
7,0→9,2 · 4,5→12,1 · 0,0→1,7 — yer gerçeğinin çok altında). D-74'ün "üretim
modeli değiştirilmiyor" kararı bağımsız olarak doğrulandı.

**4 · 🔴 ASIL BULGU — kayıp modelin değil, ZEMİNİN.** Kayıp kareleri **gözle**
inceledim (`sa_000059`, `sa_000058`):

- Sahneler **kaleydoskopik kolaj**: aynalanmış, harmanlanmış, doygunluğu gitmiş
  doku parçaları. Havadan çekilmiş bir arena görüntüsüne benzemiyor.
- **Hedef `H` YEŞİL bir kare.** Şartname §2.2.6 **2×2 m KIRMIZI branda** diyor.
  Üreteç yanlış renkte hedef basıyor.
- "Koridorlar" düz üç güzergâh değil, **dalgalı bantlar**.

Yani en iyi ölçüm zeminimizin **gerçekçiliği düşük**. Bu, öğrendiklerimizi
tümden geçersiz kılmıyor — karar yolu bulguları **geometriktir ve zeminden
bağımsızdır** (11/11 meşru ret, %95,5 şerit doğruluğu) — ama şunu söylüyor:

> **Bu zeminde ölçülen MODEL başarımı, gerçek arena başarımını öngörmez.**
> "9 model kaybı" büyük ölçüde üretecin ürettiği gerçek dışı karelerdir.

**Sıradaki kaldıraç eğitim DEĞİL, üretecin gerçekçiliği.** Dört eğitim koşusu
(v15, v22, v23 ve ondan önceki) alan içi doğruluğu yükseltti; hiçbiri bu
karelerdeki körlüğü çözmedi — çözemez de, çünkü kareler gerçek sahne
istatistiğini taşımıyor. Aynı zamanda **kırmızı branda** hedefi hiçbir zeminde
üretilmiyor; D-23'teki "hedef dedektörü yok" kalemi bununla birleşiyor.

**DOĞRULANAMADI (değişmedi):** gerçek arena başarımı. Kamera yok.

---

### D-78 · COZULDU · T56: kadraj kipi sartnameye sadik olcum zemini oldu
Uygulayan: Claude 2 · 2026-08-12 · kanit D-77 · dosya `51_sentetik_arena.py`

**IKI KIPLI AYRIM KORUNDU VE DERINLESTIRILDI.** Egitim kipinde egrilik,
aynalama ve yesil "H" celdiricisi **AYNEN KALDI** — gerekceleri (kestirme
ogrenmeyi engellemek) egitim zemini icin gecerlidir. Yalniz `--kadraj`
degisti; cunku gerceklik OLCUM zemininin isi.

**1) KORIDORLAR DUZ.** `serit(..., duz=False)` eklendi; kadraj kipinde
`genlik = 0` ve `genislik dalgalanmasi = 0`. **Dort rng degeri yine cekilir**,
boylece iki kip ayni tohumda kare kare karsilastirilabilir kalir.
Olculdu (541 tam-yukseklik koridor): merkez hatti x sapmasi **ort 0,00 px ·
maks 0,00 px** (esik < 2 px).

**2) HEDEF = 2x2 m KIRMIZI BRANDA.** Kenar = `2,0 m / mpp`, rastgele boyut YOK;
konum acik seridin HEDEF (ust) ucunda; her karede cizilir (%55 celdirici
kurali kadraj kipinde gecmez).
Olculdu: **260/260 karede var** · kenar **2,000 m** (min 2,000 maks 2,000) ·
`hedef_serit == acik_serit` uyumsuzluk **0/123** (net kare).
Manifest'e `hedef_kutu`, `hedef_serit`, `hedef_kenar_m` yazildi.
⚠ **Etiket sinifi EKLENMEDI** — uretim modeli 2 sinifli, hedef dedektoru yok
(D-23). Ucuncu sinif ayri bir sozlesme karari; bu gorevde verilmedi.

**RENK AYRIMI OLCULDU** (branda 14.440 px, moloz 161.769 px):

    kanal          branda            moloz
    S (doygunluk)  213,9 ± 31,7      33,2 ± 37,0     etki buyuklugu d = 3,71
    V (deger)      197,3 ± 30,9      139,8 ± 55,7

Ayrim DOYGUNLUKTAN gelir: `moloz_rengi` molozu tugla tonuna ve **dusuk**
doygunluga (0,10-0,40x) cekiyor; branda yuksek doygunlukta secildi. Kuyruklarda
kucuk ortusme var (molozun %99'u S<169, brandanin %1'i S>149) — yani ayrim
mutlak degil, ama etki buyuklugu 3,71 ile cok buyuk.
⚠ **Ton (H) ile ayirt etmeye guvenilemez:** kirmizi H=0/179'da sarilir,
ortalama anlamsizdir; tugla tonu da H 5-22'de bitisiktir.

**3) AYNALAMA KALDIRILDI — ama ilk denemem YANLISTI.**
Once yamayi TEK dosemeye buyuttum: periyodiklik yapisal olarak yok oldu, fakat
48-64 px yama 800 piksele cikinca DOKU da yok oldu; gozle bakinca asfalt degil
**bulanik renkli leke** cikti. Sayi iyiydi, gorsel kotuydu — **gorsel kazandi**
ve karar geri alindi. Yerine ILIMLI buyutme (~2 doseme) + **dikis harmanlama**
(`_harmanli_dose`: ortusen doseme, tuy agirlikli capraz gecis) kondu.

Olculdu — ayna simetrisi (ayni sahne, iki kip, 5 tohum):

    EGITIM kipi (aynalamali) : ort 0,502 · maks 0,748
    KADRAJ kipi (harmanli)   : ort 0,360 · maks 0,458      -> dusus %28

Yatay ozilinti (periyodik tepe): ESKI 0,380 · TEK-doseme 0,323 · HARMANLI 0,312.

🔴 **OLCUM YONTEMI HATASI — kendi buldum, duzelttim.** Ilk gorsel kiyasim
"ayni indis = ayni sahne" varsayiyordu ve YANLISTI: kadraj kipinde celdirici
`rng.random()` cekilisi tuketilmiyordu, akis kayiyordu. Bu yuzden "T56 dokuyu
bozdu" diye yanlis bir sonuca vardim. Duzeltildi (`_celdirici_var` her iki
kipte de cekilir) ve ayni sahne iki kipte yan yana uretilince goruldu ki doku
**iki kipte de ayni** — bozulma YOKTU.

**KAPILAR (gercek cikti).**

    KAPI 1  GOZLE DOGRULAMA — gorseller:
              O:\navitas-local-train\results\t56_gorsel\
                ayni_sahne_51.jpg · ayni_sahne_77.jpg · ayni_sahne_123.jpg
                  (AYNI sahne, solda egitim / sagda kadraj — adil kiyas)
                uclu_sa_000000.jpg · uclu_sa_000005.jpg · uclu_sa_000012.jpg
                  (T55 · TEK-doseme · HARMANLI)
              goruntu 260 · manifest kaydi 260                        GECTI
    KAPI 2  koridor merkez sapmasi ort 0,00 · maks 0,00 px (n=541)    GECTI
    KAPI 3  hedef 260/260 · kenar 2,000 m · hedef_serit uyumsuzluk 0/123  GECTI
    KAPI 4  EGITIM KIPI DEGISMEDI — 4 tohumda kimlik + sinif + RNG
            durumu + GORUNTU birebir esit                              GECTI
    KAPI 5  karar zinciri (yer gercegi maskesiyle):
              T55 zemini (dalgali): net 139/260 · rota 89 (DOGRU 85 · YANLIS 4)
                                    · RET 50 · uyumsuzluk 4/89
              T56 zemini (duz)    : net 123/260 · rota 86 (DOGRU 86 · YANLIS 0)
                                    · RET 37 · uyumsuzluk 0/86
    depo    codes/test_rota_sentetik.py 15/15 · discover -s tests -q Ran 303 OK

**KAPI 5 YORUMU.** Sayilarin artmasi beklenmiyordu; **serit uyumsuzlugu 4 -> 0**
ve ret orani %36 -> %30 oldu. Duz koridorlar karar yolunun ucte-bir tanimiyla
ortustugu icin yanlis serit kalmadi. Net (tek cevapli) kare 139 -> 123'e dustu:
RNG akisi degistigi ve seritler duzlestigi icin birden fazla karar seridinin
gecilebilir cikmasi biraz artti (belirsiz 137/260).

**Kume:** `O:\navitas-local-train\calisma\sentetik_arena_kadraj` (T56).
Onceki surum `...\sentetik_arena_kadraj_T55` olarak saklandi.

**DOGRULANAMADI**
  1. Zemin dokusunun GERCEK asfalta benzerligi — yama bankasi 48-64 px
     kesitlerden olusuyor ve her iki kipte de benekli/gurultulu goruntu
     veriyor. Bu T56 kapsaminda DEGISMEDI ve gozle "asfalt gibi" DEGILDIR.
  2. Moloz seritleri hala RescueNet BINA CATISI kesitleridir (mavi cati,
     mobilya). Arena molozuna benzerligi dogrulanmadi.
  3. Brandanin gercek 2x2 m brandaya gorsel benzerligi — duz kirmizi
     dikdortgen; kumas dokusu, golge, kirisiklik yok.

---

### D-79 · MİMAR DENETİMİ · T56 GEÇTİ · ama zemin dokusu ölçülebilir biçimde gerçek dışı

**T56 denetimden geçti.** Gözle doğruladım (`t56_gorsel/ayni_sahne_51.jpg`):
eğitim kipinde dalgalı S-koridor + aynalı doku + yeşil çeldirici **aynen duruyor**;
kadraj kipinde **düz dikey bantlar ve kırmızı branda** var. İstenen ayrım
korunmuş. Kapılar: koridor merkez sapması **0,00 px** · hedef 260/260, kenar
**2,000 m** · `hedef_serit != acik_serit` **0/123** · eğitim kipi bozulmadı.

**Asıl kazanç KAPI 5'te — karar zincirinde ölçülen fark:**

    T55 zemini : net 139 · rota 89 (DOGRU 85 · YANLIS 4) · RET 50
    T56 zemini : net 123 · rota 86 (DOGRU 86 · YANLIS 0) · RET 37
    -> serit uyumsuzlugu 4 -> 0   ·   ret orani %36 -> %30

Şartnameye sadık geometri şerit hatasını **sıfırladı**. D-77'nin öngörüsü tuttu.

**🔴 AMA ZEMİN DOKUSU HÂLÂ GERÇEK DIŞI — ölçtüm.** Görselde arka plan
gökkuşağı beneği. Kaynağı `51_sentetik_arena.py`:

- `yuzey_sec()` (:121) banka dolu olsa bile **%60 olasılıkla** prosedürel yüzey
  seçiyor (`if rng.random() < 0.60 or not banka[kat]`). Oysa bankada
  **700 zemin + 700 yol** gerçek doku var.
- `prosedurel_yuzey()` (:110) gürültüyü `im.shape` = (H, W, **3**) ile üretiyor
  — yani **her kanala bağımsız**. Gerçek yüzey dokusu ağırlıkla PARLAKLIK
  değişimidir, renk değil.

**Ölçüm (LAB uzayı, n=40 gerçek yama):**

    kaynak                   kroma std  parlaklik std  kroma/parlaklik
    prosedurel zemin              4.61           5.89             0.78
    prosedurel yol                4.76           6.80             0.70
    GERCEK banka zemin            5.05          58.97             0.09
    GERCEK banka yol              2.98          29.51             0.10

İki kusur aynı anda: prosedürel yüzey **7-8 kat fazla kromatik** ve **5-10 kat
fazla düz**. Yani "düz bir zemin üstüne renkli benek" gibi görünüyor; gerçek
zemin ise renksiz ama **çok dokulu**.

**Neden önemli.** Model "geçilebilir zemin"i bu yüzeyden öğreniyor. Renk
benekli-düz bir yüzeyle eğitilen model, gerçek asfaltın parlaklık dokusunu
tanımayabilir — D-77'deki az-tespitin bir bölümü buradan gelebilir. Ölçülmedi,
iddia edilmiyor; **T57'de sınanacak**.

**Görev:** `TASK_QUEUE.md` **T57** — prosedürel yüzeyi ölçülmüş hedefe yaklaştır
(tek kanallı parlaklık gürültüsü + genlik artışı) ve prosedürel/gerçek payını
gözden geçir.

---

### D-80 · COZULDU · T57: prosedurel yuzey artik PARLAKLIK dokusu; pay olcumle ayrildi
Uygulayan: Claude 2 · 2026-08-12 · kanit D-79 · dosya `51_sentetik_arena.py`

**KUSUR.** `prosedurel_yuzey()` gurultuyu `im.shape` = (H, W, 3) ile uretiyordu:
her kanal BAGIMSIZ. Gercek yuzey dokusu ise agirlikla PARLAKLIK degisimidir.
Sonuc: duz zemin uzerinde renkli benek — gozle GOKKUSAGI KONFETI.

**HEDEF KORU KORUNE KOPYALANMADI.** Banka yamalari GERCEK SAHNE parcalaridir;
parlaklik std'lerinin buyuk kismi dokudan degil ICERIKTEN (golge, nesne, yapi)
gelir. Bu yuzden 6 px Gauss ile YUKSEK GECIRGEN alinip yalniz DOKU bileseni
olculdu (n=40):

    kaynak              global kroma  global parlak  DOKU kroma  DOKU parlak  k/p
    prosedurel zemin           7,92          9,50        6,95         8,10   0,86
    prosedurel yol             6,56          9,97        6,17         8,45   0,73
    GERCEK banka zemin         8,12         50,37        1,82        12,15   0,15
    GERCEK banka yol           1,05          6,90        0,54         3,68   0,15

Iki gercek kategori de **k/p = 0,15**'te bulusuyor — hedef budur. Global
parlaklik std'si (zemin 50,37) hedef ALINMADI; o icerikten sisiyor.

**KALIBRASYON (supurme).** Renk sapmasi supurmesi: `s_renk` 0,0 -> 0,05 ·
1,0 -> 0,11 · **1,5 -> 0,14** · 2,0 -> 0,18 · 4,0 -> 0,33. `RENK_SAPMASI = 1.5`
secildi. Parlaklik supurmesi (ince, kaba) -> DOKU parlaklik: (2,2) -> 2,59 ·
(3,4) -> 3,97 · (6,7) -> 7,32 · (10,12) -> 12,22. Kategoriye gore bant:

    DOKU_GENLIGI = {"zemin": (7,0 · 10,5 · 8,0 · 12,5)   -> ~8,5-12,7
                    "yol":   (2,0 ·  4,0 · 2,0 ·  5,0)}  -> ~2,6-5,1

**SONUC (KAPI 1).**

    kaynak                DOKU kroma  DOKU parlak  DOKU k/p
    ESKI prosedurel zemin       6,95         8,10      0,86
    ESKI prosedurel yol         5,90         8,09      0,73
    YENI prosedurel zemin       1,13        10,60      0,11
    YENI prosedurel yol         0,85         3,99      0,21
    GERCEK banka zemin          1,82        12,15      0,15
    GERCEK banka yol            0,54         3,68      0,15

Oran 0,86/0,73 -> **0,11/0,21**; gercek bant 0,15. Ikisi de banda oturdu.

**TABAN RENGI CESITLILIGI KORUNDU** (kroma dusurmek rengi oldurmedi):
belirgin renkli yama ESKI 42/60 -> YENI 42/60, ortanca ortalama kroma
21,2 -> 21,0. T57 yalniz DOKU kromasini dusurdu; taban rengi PALET'ten gelir.

**`yuzey_sec()` PAYI OLCUMLE AYRILDI.** Docstring "%45" diyordu, kod %60
kullaniyordu — ikisi de olculmemisti (docstring/kod celiskisi da giderildi).
Bankadaki yamalarin gercekten "temiz duz yuzey" olup olmadigi olculdu
(ICERIK parlaklik std < 8):

    kategori   n   p50 icerik std   TEMIZ (<8)
    zemin    315          39,8          2/315   -> banka temiz zemin VEREMIYOR
    yol      385           9,9        166/385   -> banka temiz yol BOL VERIYOR

Bu yuzden pay KATEGORIYE GORE ayrildi: `{"zemin": 0.70, "yol": 0.35}`.
Sifirlanmadi — prosedurel yuzey hala tek temiz-zemin kaynagidir; ama yolda
gercek yama daha gercekcidir ve banka onu bol veriyor.

**KOSULAN KAPILAR (gercek cikti).**

    KAPI 1  LAB olcumu — yukaridaki tablo                              GECTI
    KAPI 2  GOZLE DOGRULAMA — O:\navitas-local-train\results\t57_gorsel\
              yuzey_ornekleri.jpg  (ESKI / YENI / GERCEK banka, 2 kategori)
              sahne_51.jpg · sahne_77.jpg · sahne_123.jpg (tam sahne)
            Eski zemin GOKKUSAGI KONFETI; yeni zemin CIM/BETON gibi okunuyor.
    KAPI 3  T56 kapilari KORUNDU:
              koridor sapma MAKS 0,00 px · hedef 260/260 · kenar 2,000 m
              hedef_serit != acik_serit  0/144
    KAPI 4  karar zinciri (yer gercegi maskesiyle):
              T56 zemini: net 123/260 · rota  86 (DOGRU  86 · YANLIS 0) · RET 37
              T57 zemini: net 144/260 · rota 107 (DOGRU 107 · YANLIS 0) · RET 37
    KAPI 5  EGITIM KIPI — asagida
    depo    codes/test_rota_sentetik.py 15/15 · discover -s tests -q Ran 303 OK

**KAPI 4 YORUMU.** Sayilarin artmasi beklenmiyordu; artti: tek-cevapli kare
123 -> 144, uretilen rota 86 -> 107, ret DEGISMEDI (37), yanlis serit yine 0.
Sebep: pay degisikligi RNG akisini kaydirdi ve sahne dagilimi degisti —
karar mantiginda bir gevseme YOK (yanlis serit hala 0).

**KAPI 5 — EGITIM KIPI DE DEGISTI (KASITLI) ve etki AYRISTIRILDI.**
Ilk olcumumde "geometri degismedi" yazmistim; **yanlisti**, olcum `False`
diyordu. Ayristirildi:

    A) pay ESKIDE sabitlenince (0,60/0,60) — fark yalniz DOKUDAN:
         ESKI egitim sahnesi: kroma 4,90 · parlak 21,13 · oran 0,23
         YENI egitim sahnesi: kroma 3,96 · parlak 21,22 · oran 0,19
         GEOMETRI (kimlik haritasi) AYNI: 5/5 tohum
    B) gercek pay (0,70/0,35): GEOMETRI ayni mi -> 0/5

Yani **geometri degisimi DOKUDAN degil, `yuzey_sec` PAYINDAN geliyor**:
`yuzey_sec` serit duzeninden ONCE kosar; pay degisince ayni rng cekilisi
farkli dala girer ve akis kayar. Ikisi de kasitlidir. T51/T56'daki "egitim
kipi degismedi" kapisi bu gorevde GECERLI DEGILDIR.

**Kume:** `O:\navitas-local-train\calisma\sentetik_arena_kadraj` (T57).
Onceki surumler `..._T56` ve `..._T55` olarak saklandi.

**DOGRULANAMADI**
  1. Yeni prosedurel yuzeyin GERCEK asfalt/cim fotografina benzerligi — yalniz
     LAB istatistigi ve goz kiyasi yapildi; algi modeliyle sinanmadi.
  2. Moloz seritleri hala RescueNet BINA CATISI kesitleridir (D-78'den devam);
     bu gorevde DEGISMEDI.
  3. Banka "zemin" yamalarinin bir kismi asiri pozlanmis/beyaz — banka
     kalitesi bu gorevde ele alinmadi.

---

### D-81 · TUZAK · Üreteç çıktı dizinini temizlemiyor: yeniden üretim BAYAT kare bırakıyor

**Nasıl çıktı.** T57 sonrası eğitim verisini yeni dokuyla yeniden ürettim.
Betik `exit 0` döndü. **Damgalara baktım** — dosyalar hâlâ 07-30 tarihliydi:

    UnicodeEncodeError: 'charmap' codec can't encode character '≤'
    51_sentetik_arena.py, doku bankasi yuklendikten HEMEN SONRA

Çıktı bir dosyaya yönlendirilince Windows kod sayfası **cp1254** oluyor ve
`≤` karakteri betiği düşürüyor. `exit 0` gördüğüm şey kabuk zincirinin çıkışıydı,
üretecin değil. **`PYTHONIOENCODING=utf-8` olmadan bu betikler sessizce ölüyor.**

**İkinci ve daha sinsi tuzak.** Doğru kodlamayla yeniden koşturdum, bu kez
gerçekten üretti — ama dizinde **bayat kareler kaldı**:

    train  toplam 3003  YENI 2072  BAYAT  931
    val    toplam  300  YENI    0  BAYAT  300

Üreteç çıktı dizinini **temizlemiyor**; farklı `--adet`/numara aralığıyla
koşulunca eski dosyalar yerinde kalıyor. Sonuç: eğitim kümesi eski (gökkuşağı)
ve yeni (parlaklık) dokunun **karışımı** olurdu — T57'nin tüm etkisi seyrelirdi
ve bunu hiçbir kapı yakalamazdı.

**Bu, aynı turda üçüncü "yeşil görünen ama çürük" olay.** Diğer ikisi: kendi
`0/234` ölçümüm (dar küme, D-69) ve kendi şerit türetmem (D-70). Ortak ders:
**bir işlemin başarılı döndüğü, istenen şeyi yaptığı anlamına gelmez** — çıktının
kendisi doğrulanmalı. Damga, sayım ve içerik.

**Yapılan.** Dizin silinip sıfırdan üretildi. Eğitim ancak damga doğrulaması
geçtikten sonra başlatılacak.

**Kalıcı öneri (görev değil, uyarı):** `51_sentetik_arena.py` bir `--temizle`
bayrağı taşımalı ya da çıktı dizini boş değilse **uyarmalı**. Bu tuzağa bir
kez daha düşülürse fark edilmeyebilir.

---

### D-82 · BEŞİNCİ KOŞU · Doku ekseni İLK KEZ karar düzeyinde fark üretti — ama kafa karıştırıcıyla

**`v24_t57_doku`** — T57'nin düzeltilmiş dokusuyla yeniden üretilmiş sentetik
arena + T54 karışımı. 176/200 epoch (erken durma), 7,0 saat.

**Başlatmadan önce üç doğrulama yapıldı** (D-81'deki iki tuzaktan sonra):
damgalar 3000/3000 taze · eğitim verisinin kendisinde ölçülen doku oranı
**k/p = 0,15** (hedef 0,15; eski 0,70-0,86) · görsel onaylı.

**Dört kapı — v23 ile AYIRT EDİLEMEZ:**

    model              K1 IoU  K1 kesinlik  K1 duyar  K2 otopark ort
    v24_t57_doku        0.692        0.816     0.821           81.0%
    v23_t54_engelli     0.698        0.826     0.819           81.1%
    v21 (uretim)        0.311        0.813     0.335           81.0%

Farklar gürültü tabanının (0,04) altında.

**AMA KARAR DÜZEYİNDE İLK KEZ FARK VAR** (kadraj zemini, n=60):

    model         rota    kaplama   MASKE_YOK  UC_BANT  GORUS   GT ile zemin IoU
    v24_t57_doku  46/60     %22,3           1        1     12              0.810
    v21 (uretim)  35/60     %14,4           9        6     10              0.580

`MASKE_YOK` **9 → 1**, `UC_BANT_TEMAS_YOK` **6 → 1**, yer gerçeğiyle zemin IoU
**0,580 → 0,810**. Bu, beş koşuda ilk kez alan-içi kazancın karar düzeyine
geçmesidir. Şerit doğruluğu: v24 23/26 · v21 19/20 — bu sayılarda gürültü.

**🔴 KAFA KARIŞTIRICI — açıkça yazıyorum.** Kadraj kümesi T57'nin **yeni**
dokusuyla üretildi; v24 de aynı dokuyla eğitildi. v21 eski dokuyla eğitilmişti.
Yani v24'ün "ev sahibi avantajı" var.

**Bunu tamamen geçersiz kılmayan gerekçe:** zemin v24'ün *tuhaflıklarına* değil,
**ölçülmüş gerçek doku istatistiğine** doğru taşındı (k/p 0,15 = gerçek banka).
Substrat gerçeğe yaklaştı ve v24 onu takip etti. Yine de bu, gerçek görüntüde
kanıt DEĞİLDİR.

**Karşı kanıt, ve ağır basıyor:** otoparkta hiçbir şey değişmedi. Kaplama
**%74,4**, bina çatısı **hâlâ tamamen yeşil** (gözle doğrulandı). Beş koşu,
beş kez aynı. Elimizdeki tek GERÇEK görüntüde ilerleme yok.

**Üretim modeli kararı KULLANICIYA bırakılıyor.** v24 ölçülebilen her eksende
en iyi ya da eşit-en-iyi ve karar düzeyinde ilk gerçek kazancı veriyor; ama
kazanç eğitim dağılımıyla eşleşen bir zeminde ölçüldü ve gerçek görüntüde
karşılığı yok. Mimar tek başına geçirmiyor.

**DOĞRULANAMADI (değişmedi):** gerçek arena başarımı. Kamera yok.

---

### D-83 · COZULDU · T58: uretim modeli v24'e cevrildi; paket manifesti BAYATTI
Uygulayan: Claude 2 · 2026-08-13 · kullanici karari, gerekce D-82

**YAPILAN.** `comms/yks_gui.py:898` `ALGI_MODEL_DOSYA` v21 -> **v24_t57_doku**.
Yalniz GUI'yi cevirmek D-58/D-60 sinifi IRAKSAMA olurdu (ekran bir modeli,
saha donanimi baskasini kosar), bu yuzden dort uc birlikte cevrildi:
GUI · `jetson_paket/models/` · paket manifesti · HER IKI `JETSON_KILAVUZ.md`.

**MIMARIN HAZIRLIGI DOGRULANDI (yeniden uretilmedi).**

    models/navitas_seg_v24_best.pt       sha c04d7d3570ead678  54.852.380 B  ESLESTI
    models/navitas_seg_v24_best.onnx     sha 27e480a135d75ac3  54.599.920 B
    results/onnx_export_v24_.../*.onnx   sha 27e480a135d75ac3  -> ONNX ikisi de AYNI
    v24.names = {0: 'traversable', 1: 'blocked'}   (v21 ile BIREBIR)

**BAYAT MANIFEST (asil bulgu).** `jetson_paket/models/jetson_derleme_manifest.json`
2026-08-05'ten beri `pc_modeli = ...v17_best.pt` ve iki ONNX (640+512) diyordu.
Oysa pakette 2026-08-05 aksamindan beri **v21** ONNX vardi ve kilavuz onu "ASIL"
gosteriyordu. Sekiz gun boyunca kimse gormedi. **Sebep:** manifest disa aktarim
KOSUSUNU tarif ediyordu, PAKETI degil — paket icerigine hic bakmiyordu.

**Duzeltme yalniz surum yukseltmek degil.** Manifeste `paket_icerigi` eklendi:
her dosyanin adi, bayti ve sha256'si. Bayatlik artik mekanik olarak yakalanir.
Ayrica `asil_model`, `asil_model_pt` ve `uretim_hakem_ekrani` alanlari eklendi.

**KAPI 2 — B1 BAGIMSIZ TEKRARLANDI** (`O:\navitas-local-train\58_b1_bagimsiz.py`).
Mimarin sayisi kabul edilmedi; olcum sifirdan kuruldu. 30 gercek drone karesi,
`data/raw_frames` icinden ESIT ARALIKLI (bas-30 tek videonun ilk saniyeleridir),
zincir URETIMDEN (`_preprocess` -> `predict(imgsz=INFER_SIZE)` -> `get_masks` ->
`_maskeleri_icerige_kirp`), kaplama icerik kutusundan:

    model                       conf  BOS maske  ort kaplama    min    maks
    navitas_seg_v24_best.pt     0.30      0/30        %81,0  %77,2   %86,6
    navitas_seg_v24_best.pt     0.25      0/30        %81,0  %77,2   %86,6
    navitas_seg_v21_best.pt     0.30      0/30        %81,0  %76,7   %86,3
    navitas_seg_v17_best.pt     0.30     28/30         %0,4   %0,0    %6,6

KAPI 2 GECTI (v24 0/30). **KONTROL:** v17 28/30 dustu — olcut gercekten
DUSEBILIYOR (D-15/K-04: sifir olcum basari sayilmaz). Mimarin bildirdigi
"v24 0/30 · %78,4 · v17 25/30" ile fark **kare secimindendir** (bas-30 vs
esit aralikli); yon ve sonuc AYNI.

**B1 v24 ile v21'i AYIRMIYOR** — ikisi de 0/30, kaplama ayni. B1 yalniz
"model kor mu" sorusunu sorar. v24'un gerekcesi B1 degil, D-82'nin karar
duzeyi olcumudur. Bu kilavuzlara da acikca yazildi.

**D-82'nin UC KAPI tablosu BAGIMSIZ olarak yeniden uretildi** (`56_uc_kapili
_model_secimi.py`, val n=120, conf 0,30) — mimarin sayilariyla AYNI cikti:

    model   K1 IoU  K1 kesinlik  K1 duyar  K2 otopark ort  K2 maks  K3 dogru/yanlis/ret
    v24      0,692        0,816     0,821           %81,0    %86,6        0 / 0 / 9
    v21      0,311        0,813     0,335           %81,0    %86,3        0 / 0 / 9

**K3 YENI VE OLUMSUZ BULGU.** Kompozit arenada (gercek drone karesi + yapistirilmis
moloz — elimizdeki gercege en yakin kume) **v24 hicbir sey degistirmiyor**: her
iki modelde de 9/9 kare `ZEMIN_MASKESI_SUPHELI` ile reddediliyor. Tek kare
ornegi: kaplama %76,5 (tavan %55) VE cevre dayanmasi %63,2 (tavan %50).
Yani T48 kapisi ikisini de ayni sekilde durduruyor. Kazanc **yalniz sentetik
kadraj kumesinde** var. Karar zincirinin davranisi DOGRUDUR (cokmus maskeden
rota uretmiyor), ama v24'un ustunlugu gercege en yakin kumede GORULMUYOR.

**%81 kaplama bir OTOPARKTIR ve COKMEDIR** (D-62). "B1 gecti" = "kor degil",
"dogru goruyor" DEGIL. Kilavuzlara bu uyari eklendi.

**YENI KAPI** `tests/test_uretim_modeli_hizasi.py` (12 test): GUI sabiti ·
paket bayt-esitligi · paket ONNX'inin depodan turetilmis olmasi · manifest
sha'lari · manifest disi dosya · her iki kilavuzun "ASIL" satiri · derleme
komutu — hepsi TEK surume baglanir. Agirlik yuklemez, GPU'suz saniyede kosar.

**AGIRLIK YOKLUGU.** Model dosyalari `.gitignore:132` ile depo disinda
(`jetson_paket/models/*.pt`). Temiz bir klonda bayt kapilari dosya YOKLUGUNDAN
duserdi — yanlis sebeple kirmizi. Bayt kapilari `skipUnless` ile korundu; METIN
kapilari (manifest alanlari, kilavuz `ASIL` satiri, derleme komutu) HER ZAMAN
kosar cunku o dosyalar izlenir. Manifest izlendigi icin, agirliklar git'te
olmasa da paketin NE OLMASI GEREKTIGI artik depoda kayitlidir.

**MUTASYON KONTROLU** (kapi gercekten dusuyor mu):

    M0  mutasyon YOK                  12 kosuldu · DUSEN 0   temiz — beklenen
    M1  GUI v21'e geri cevrildi       12 kosuldu · DUSEN 7   kapi ATESLENDI
    M2  manifest sha'si bozuldu       12 kosuldu · DUSEN 1   kapi ATESLENDI
    M3  paketten v24 .pt silindi      12 kosuldu · DUSEN 2   kapi ATESLENDI
    M4  geri alma sonrasi             12 kosuldu · DUSEN 0   temiz — beklenen

**`scripts/copy_paste_augmentation.py:981` BILEREK DEGISTIRILMEDI.** Arena zemin
kahini hala v21'dir. Gerekce: o kahin `data/arena_kompozit` yer gercegini uretir;
kahini degistirmek D-38'den beri ona dayanan TUM olcumleri (K3, GUI `kompozit`
kaynagi, T48 tabani %76,0) kiyaslanamaz kilar. **Ancak dosyadaki yorum artik
yaniltici**: "bu etkin sistem modelidir" diyor, oysa etkin model v24. Ayri bir
gorevde ya yorum duzeltilmeli ya da kume v24 ile YENIDEN uretilip tum tabanlar
birlikte guncellenmelidir. Bu gorevin izni o dosyayi kapsamiyordu.

**KOSULAN KAPILAR (gercek cikti).**

    KAPI 1  GUI v24 yukluyor: "navitas_seg_v24_best modeli yuklendi:
            navitas_seg_v24_best.pt (SHA c04d7d35)" · bilgi satirinda
            "model: navitas_seg_v24_best.pt"                          GECTI
    KAPI 2  B1 bagimsiz: v24 bos maske 0/30 (kontrol v17 28/30)       GECTI
    KAPI 3  depo <-> paket bayt-esit: .pt c04d7d3570ead678 ·
            onnx 27e480a135d75ac3                                     GECTI
    KAPI 4  test_gui_kendi_cikarim_hattini_KURMUYOR ......... ok
            test_gui_karari_uretim_yolunun_karariyla_AYNI .... ok      GECTI
    KAPI 5  codes/test_rota_sentetik.py  SONUC: 15/15 dogru
            unittest discover -s tests -q  Ran 315 tests  OK           GECTI
    KAPI 6  scripts/jetson_paket_hazirla.py -> 9/9 bayt-esit           GECTI

**DOGRULANAMADI**
  1. v24'un GERCEK arenadaki basarimi. **Kamera yok** — arena karesi alinamiyor.
     Bu karar arena basarimini dogrulamaz ve dogrulayamaz.
  2. v24'un kazanci, v24 ile AYNI dokuyla uretilmis sentetik kumede olculdu
     (D-82 "ev sahibi avantaji"). Gercege en yakin kumede (kompozit) kazanc
     GORULMEDI — yukaridaki K3.
  3. ONNX <-> .pt cikti paritesi bu gorevde OLCULMEDI. v21 icin 30/30 olculmustu
     (`jetson_paket/V21_KAPI_RAPORU.json`); v24 icin karsiligi YOK. Jetson'da
     engine derlenmeden once olculmelidir.
  4. Jetson uzerinde hicbir sey kosulmadi: FPS, engine derlemesi ve saha karari
     donanim ister.

---

### D-84 · DÖNÜM NOKTASI · Gerçek arena karesi bulundu: v21 KÖR, kapı YANLIŞ ATEŞLİYOR

**Kullanıcının önerisiyle** internette arena görüntüsü arandı. Resmî yarışma
sayfasında görsel yok; ama **şartnamenin kendisinde var** ve o dosya bir
haftadır depoda duruyordu: `Ileri_Otonom_Sistemler_..._Sartname_TR_Ltktw.pdf`
**sayfa 9**, gömülü şekil 1059×634. Depoya alındı:
`data/arena_referans/sartname_s9_arena.png` (sha `1f109df65524db6a`).

Bu, projenin sahip olduğu **tek gerçek arena görüntüsüdür**. D-56'da "kamera
yok, arena doğrulaması yapılamaz" diye kapattığım kalem **kısmen açıldı** —
ve bir haftadır aradığım cevabı ilk denemede verdi.

**1 · ÜRETİM MODELİ GERÇEK ARENADA TAMAMEN KÖR.**

    v21 (uretim) : zemin %0.0 · engel %0.0  -> RED/MASKE_YOK
    v24 (yeni)   : zemin %57.7 · engel %0.9 -> RED/ZEMIN_MASKESI_SUPHELI

`navitas_seg_v21_best.pt` gerçek arenada **tek piksel zemin bulamıyor**. Görev
günü bu modelle uçulsaydı sistem hiçbir güzergâh üretemezdi. Bir haftadır
otoparkta ölçtüğümüz "v21 çalışıyor, v24 fark etmiyor" tablosu **alan dışı bir
zeminde** kuruluydu; gerçek zeminde tablo **tersine dönüyor**.

Bu, kullanıcının bugün verdiği v24 geçiş kararını **geriye dönük olarak ve çok
daha güçlü biçimde** doğruluyor.

**2 · v24 gerçek arenayı DOĞRU segmentliyor** (gözle doğrulandı): toprak zemin
yeşil, **moloz yığınları hariç tutulmuş**, İKA engel işaretli, üç koridor
izlenebilir hâlde. Kaplama %57,7 bu sahnede **meşrudur** — arena zemini
gerçekten büyük ölçüde açık toprak.

**3 · 🔴 T52 KAPISI GERÇEK ARENAYI REDDEDİYOR — öngörülen kusur gerçekleşti.**

    kaplama       0.577  > tavan 0.55   ASILDI
    kenar dayanma 0.585  > tavan 0.50   ASILDI   -> RET

D-65 ve D-66'da aynen şunu yazmıştım: *"görev kadrajında arena görüntüyü
doldurursa zemin çevreye daha çok dayanabilir; kenar dayanması kaplamadan daha
dayanıklı ama bağışık değil."* **Gerçekleşti.** Doğru segmentlenmiş gerçek
arenayı kendi güvenlik kapımız eliyor. Eşik iki sentetik/otopark dağılımından
türetilmişti; **gerçek arena o dağılımların dışında.**

⚠ Eşiği körlemesine yükseltmek çözüm DEĞİL — çöküş yakalama (67/67) o eşiğe
dayanıyor. Ölçüt yeniden düşünülmeli; artık elimizde **gerçek bir pozitif
örnek** var, bu ilk kez mümkün.

**4 · Şartname iki tanımı düzeltiyor:**
- **HB = 2×2 m, üzerinde KIRMIZI H HARFİ** (s.9). T56'da "2×2 m kırmızı branda"
  diye şart koşmuştum — **yanlış**; üreteç şu an düz kırmızı dikdörtgen basıyor.
- **İHA-İB = 30×30 m MAVİ bölge.** Üretecimizde **hiç yok**.

**5 · Gerçek arena dokusu üretecimizden farklı:** zemin açık kahve toprak/kum
(ızgaralı), moloz **gri beton** levhalar, bariyerler **kırmızı-beyaz şeritli**.
Üreteç RescueNet kolajı kullanıyor — afet enkazı, farklı renk dağılımı.

**KULLANIM SINIRI.** Tek karedir; istatistik çıkarılamaz. **Eğitime
sokulmayacak** — tek gerçek doğrulama karemiz odur, eğitime girerse o değerini
kaybeder. `data/arena_referans/KAYNAK.md`'ye yazıldı.

---

### D-85 · MİMAR KARARI · Kaplama tavanı 0,55 → 0,67; kenar 0,50'de kalıyor

**Neden yeniden kalibrasyon.** İki şey birden değişti: (1) üretim modeli
**v24** oldu, oysa eşikler **v21** çıktılarıyla türetilmişti (D-66); (2) elimize
**gerçek arena karesi** geçti (D-84) ve meşru kümeye katıldı.

**v24 ile yeniden ölçüm (n = 220 kadraj + 1 gerçek arena · 67 otopark):**

    kume                    n    kaplama min..maks     kenar min..maks
    MESRU kadraj arena    220    0.000..0.863          0.000..0.655
    MESRU GERCEK ARENA      1    0.577..0.577          0.585..0.585
    COKUS otopark          67    0.728..0.835          0.568..0.969

    kaplama tek basina : CAKISIK   (mesru 0.863 > cokus 0.728)
    kenar   tek basina : CAKISIK   (mesru 0.655 > cokus 0.568)
    AND birlesimi      : AYIRIYOR

**Hiçbir sinyal tek başına ayırmıyor; AND birleşimi ayırıyor.** Sebep: yüksek
kaplamalı meşru kareler düşük kenara sahip, yüksek kenarlı meşru kareler düşük
kaplamaya. Çöküşte **ikisi birden** yüksek.

**Pay en büyük eşik çifti (tam ayrık, mesru elenen 0 · kaçan çökme 0):**

    min pay  mesru payi  cokme payi  kaplama  kenar
      0.062       0.062       0.063     0.67   0.50

**KARAR: `ZEMIN_KAPLAMA_TAVANI` 0.55 → 0.67. `ZEMIN_KENAR_DAYANMA_TAVANI`
0.50'de KALIYOR.** Yalnız yanlış olan sayı değişiyor.

    MEVCUT (0.55, 0.50): mesru elenen 2/221 — biri GERCEK ARENA
    YENI   (0.67, 0.50): mesru elenen 0/221 · kacan cokme 0/67

**Test kısıtı yok.** `test_zemin_kaplama_kapisi.py` eşiği sözleşmeden okuyor ve
göreli çarpan kullanıyor (madde 16'ya uygun yazılmış); eşik değişince
kendiliğinden uyum sağlıyor. D-71'de karşıma çıkan üçüncü kısıt burada yok.

**🔴 İKİ SINIR — gizlenmiyor.**
1. **Gerçek arena tek karedir.** 0,062'lik meşru payı bir dağılıma değil, tek
   bir noktaya karşı ölçüldü. İkinci bir gerçek arena karesi geldiğinde eşik
   **yeniden ölçülmeli**; o kare bu payın dışına düşebilir.
2. **Eşikler MODELE BAĞLI.** v21 için türetilen değerler v24'te yanlıştı; v24
   için türetilen değerler bir sonraki modelde yanlış olabilir. Üretim modeli
   her değiştiğinde bu kalibrasyon **zorunlu adımdır**. Bunu görev şablonuna
   yazmak gerekiyor.

---

### D-86 · UYGULANDI + DENETIM · T59: tavan 0.67 kondu; D-85'in "tam ayrik" iddiasi kumenin TAMAMINDA DOGRULANMADI
Uygulayan: Claude 2 · 2026-08-13 · karar D-85 · kanit D-84

**YAPILAN.** `ZEMIN_KAPLAMA_TAVANI` **0.55 -> 0.67**. `ZEMIN_KENAR_DAYANMA_TAVANI`
**0.50'de kaldi** — dokunulmadi. Sabit yorumu ve `CONTRACTS.md` SS6.4 olcumle
guncellendi. Jetson paketi yenilendi (9/9 bayt-esit).

**KARARIN ANA GEREKCESI DOGRULANDI.** Gercek arena karesi bagimsiz olculdu:

    sartname_s9_arena.png   kaplama 0.579 · kenar 0.585    (D-85: 0.577 / 0.585)

Eski cift (0.55, 0.50) bu kareyi ELIYOR; yeni cift (0.67, 0.50) GECIRIYOR.
Dogru segmentlenmis tek gercek arena karemizin reddedilmesi boylece bitti.

**BAGIMSIZ OLCUM — mimarin betigi kullanilmadi, sifirdan kuruldu.** Mimar 220
kadraj karesi kullanmis; burada kumenin TAMAMI (260) kullanildi — daha genis
mesru kume DAHA ZOR sinavdir.

    kume                     n    kaplama min..maks    kenar min..maks
      MESRU kadraj arena    260    0.000..0.863        0.000..0.682
      MESRU GERCEK ARENA      1    0.579               0.585
      COKUS otopark          67    0.770..0.866        0.579..0.971

    kaplama tek basina: mesru maks 0.863 > cokus min 0.770   CAKISIK
    kenar   tek basina: mesru maks 0.682 > cokus min 0.579   CAKISIK

"Hicbir sinyal tek basina ayirmiyor, AND ayiriyor" tespiti DOGRULANDI.

**🔴 UC AYRISMA — D-85 ile ortusmuyor, gizlenmiyor.**

    olcut                        D-85 (n=220)      T59 (n=260, tamami)
    kadraj kenar maks                  0.655                    0.682
    otopark kaplama min                0.728                    0.770
    (0.67,0.50) mesru elenen         0/221                    1/261
    TAM AYRIK CIFT var mi              EVET (pay 0.062)         YOK

    esik cifti          mesru elenen   kacan cokme
      (0.55, 0.50)       3/261          0/67    <- biri GERCEK ARENA
      (0.67, 0.50)       1/261          0/67

Supurme (1..99 x 1..99, tum ciftler): **elenen 0 VE kacan 0 veren cift YOK**.
Yani D-85'teki 0.062 pay 220 kareli ALT KUMENIN ozelligidir, olcutun degil.
Bu, kararin YANLIS oldugu anlamina gelmez — 3/261'den 1/261'e inmek ve gercek
arenayi kurtarmak nettir — ama "tam ayrik" ifadesi kayda boyle gecmemelidir.

**KALAN TEK ELENEN KARE inceledildi (kor kabul edilmedi).** `sa_000001.jpg`
kaplama 0.856 · kenar 0.682. Yer gercegiyle kiyas:

    kare              MODEL kap   GT kap    fark   MODEL ken   GT ken     IoU
    sa_000001.jpg         0.856    0.717   +0.139       0.682    0.359   0.810

Sahne GERCEKTEN acik (GT %71,7) ve model onu buyuk olcude dogru buluyor
(IoU 0,810); ama sinira gercegin IKI KATI dayaniyor. SINIR DURUM — duz bir
yanlis pozitif degil.

**🔴 0.67'NIN OLCULMUS BEDELI — D-85'te yok, burada var.** `sa_000150.jpg`
artik kapidan GECIYOR:

    kare              MODEL kap   GT kap    fark   MODEL ken   GT ken     IoU
    sa_000150.jpg         0.617    0.380   +0.237       0.658    0.190   0.613

Model orada GERCEKTEN cokmus (gercegin 1,6 kati zemin, IoU 0,613, sinira
gercegin 3,5 kati dayanma) ve 0.55 tavani onu YAKALIYORDU; 0.67 kaciriyor.
Bu, sabitin kendi yorumundaki "orta siddetli cokme bu kapidan GECER"
uyarisinin ILK SOMUT ORNEGIDIR. Kaplama+kenar bu sinifi yakalayamaz; maskenin
YAPISI (doku/renk tutarliligi) gerekir — ayri gorev.

**YENI KALICI KAPI** `tests/test_gercek_arena_kapisi.py` (7 test). Esigin
SAYISI degil DAVRANIS kilitlenir: "dogru segmentlenmis gercek arena kapidan
GECER". Iki katman — (a) olculen degerlerle esik mantigi (agirliksiz kosar),
(b) uretim zinciriyle gercek kare (v24 agirligi varsa). Agirlik/kare yoksa
ATLANIR, temiz klonda yanlis sebeple kirmizi yanmaz. Sabitler bayatlarsa
`test_OLCULEN_degerler_SABITLERLE_tutarli` duser.

**MUTASYON KONTROLU** (D-15/K-04: sifir olcum basari sayilmaz):

    M0  mutasyon YOK (tavan 0.67)                7 kosuldu · DUSEN 0  temiz — beklenen
    M1  tavan 0.55'e GERI ALINDI                 7 kosuldu · DUSEN 4  kapi ATESLENDI
    M2  tavan 0.578 (arena degerinin altinda)    7 kosuldu · DUSEN 4  kapi ATESLENDI
    M3  YALNIZ kenar tavani 0.10  (AND kontrolu) 7 kosuldu · DUSEN 0  temiz — beklenen
    M4  IKI tavan birden dusuruldu               7 kosuldu · DUSEN 4  kapi ATESLENDI
    M5  testteki OLCULEN sabit bayatlatildi      1 kosuldu · DUSEN 1  kapi ATESLENDI
    M6  geri alma sonrasi                        7 kosuldu · DUSEN 0  temiz — beklenen

M3 negatif kontroldur: kenar tavanini tek basina dusurmek kapiyi ATESLEMEMELI
(kapi AND'dir, arena kaplamasi 0.579 < 0.67). Ateslemedi — AND dogrulandi.

**🔴 MEVCUT BIR TEST DUSTU — DUZELTILMEDI, karar kullaniciya birakildi.**

    tests/test_zemin_kapisi_iki_sinyal.py:97
    IkiSinyalKapisiTests.test_kaplama_YUKSEK_kenar_DUSUK_ATESLEMEZ (kaplama=0.6)
    AssertionError: 0.600625 not greater than 0.67 : fikstur kaplama tavanini asmiyor

Testin IDDIASI ("kaplama yuksek + kenar dusuk -> kapi ateslememeli") saglam ve
diger iki alt-durum (0.70, 0.85) GECIYOR. Duşen sey FIKSTUR ON KOSULU: `0.60`
ciplak sayisi eski tavanin (0.55) ustundeydi, yeni tavanin (0.67) altinda kaldi.
Madde 16 acisindan zaten kusurlu: fikstur esigi SOZLESMEDEN turetmiyor.
**Onerilen asgari duzeltme** (uygulanmadi, izin bekliyor):
`for oran in (0.60, 0.70, 0.85)` -> tavandan turetilen degerler, or.
`for carpan in (1.05, 1.20, 1.35): oran = min(0.98, ZEMIN_KAPLAMA_TAVANI * carpan)`.
Boylece esik her degistiginde fikstur kendiliginden uyar.

**KOSULAN KAPILAR (gercek cikti).**

    KAPI 1  bagimsiz olcum: (0.67,0.50) mesru elenen 1/261 · kacan cokme 0/67
            HEDEF 0/221 idi — TUTMADI, sebebi yukarida                DUSTU
    KAPI 2  tests/test_gercek_arena_kapisi.py  Ran 7 tests  OK        GECTI
    KAPI 3  mevcut testler                                            DUSTU (1)
    KAPI 4  mutasyon kontrolu: M1/M2/M4/M5 atesledi, M3 sustu         GECTI
    KAPI 5  codes/test_rota_sentetik.py  SONUC: 15/15 dogru           GECTI
            unittest discover -s tests -q  Ran 322  FAILED (failures=1)
            -> tek dusen KAPI 3'teki fikstur; baska dusen YOK
    KAPI 6  scripts/jetson_paket_hazirla.py  9/9 bayt-esit
            karar_sozlesmesi.py sha b1a54c9fbe03aacb                  GECTI

**DOGRULANAMADI**
  1. Gercek arena TEK KAREDIR. Mesru taraf bir dagilima degil tek noktaya karsi
     olculdu; istatistiksel guven YOKTUR. Ikinci gercek kare geldiginde esik
     YENIDEN olculmelidir.
  2. Esikler MODELE BAGLIDIR. 0.67 v24 icindir; bir sonraki modelde yanlis
     olabilir. Uretim modeli her degistiginde kalibrasyon ZORUNLU adimdir —
     bu, gorev sablonuna yazilmali (D-85'in kendi onerisi).
  3. Orta siddetli cokme (sa_000150 sinifi) artik kapidan GECIYOR; bu sinif
     icin olcut YOK.
  4. Arena basarimi yine sahada dogrulanmadi — kamera yok, tek kare PDF'ten.

---

### D-87 · OLCUM · Gercek arena RENK KUNYESI: uretec bes noktada celisiyor; D-84'un IKI okumasi YANLIS
Olcen: Claude 2 · 2026-08-13 · kaynak `data/arena_referans/sartname_s9_arena.png` (1059x634)

**NEDEN.** Kullanici "goruntu isleme mukemmel olsun" dedi ve baslangic olarak
URETEC SADAKATINI secti. Alti model (v15..v24) ayni duvara toslad; ortak sebep
egitim substratinin arenaya benzememesi. Artik gercek kare elimizde — hedef
TAHMIN edilmek yerine OLCULDU.

**ONCE: iki sartname PDF'i de tarandi, BASKA ARENA GORSELI YOK.**

    2026_TEKNOFEST_TYDA_SARTNAME_Ucuncu_Senaryo   19 sayfa · s1/s19 KAPAK
    Ileri_Otonom_Sistemler_..._Sartname_TR         30 sayfa · s9 1059x634 TEK figur
    (her sayfadaki 1653x2338 gorsel filigran/arka plandir)

Bu kaynak TUKENDI. Elimizdeki gercek arena goruntusu bir tanedir ve oyle kalacak.

**OLCUM (BGR ortalama · LAB, a/b merkezlenmis):**

    bolge            BGR ort            L      a      b    L std
    zemin_disi      (122,139,153)    149.7   +2.1  +11.0    13.4   <- EN TEMIZ zemin
    zemin_acik      (127,148,164)    158.6   +2.3  +13.5    23.4
    moloz_levha     (101,109,111)    113.6   -0.5   +4.5    68.3
    moloz_yigin      (91, 96, 96)    101.7   -1.2   +3.0    51.5
    bariyer         (116,126,148)    139.4   +7.5  +10.2    45.9
    HB_ped          (129,127,120)    132.2   -2.0   -2.1    57.4

    BASKIN PALET (k-means k=6, LAB):
       pay      L      a      b     BGR
     35.4%  165.5   +0.9  +10.3   (139,156,164)
     28.3%  143.0   +0.8   +9.0   (119,134,141)
     13.6%  113.9   +0.1   +7.2   ( 93,104,110)
      8.9%   73.2   +0.3   +4.4   ( 61, 67, 70)
      7.5%   25.0    0.0   +0.7   ( 26, 26, 26)
      6.3%  199.3   -0.9   +5.1   (184,193,195)

**BULGU 1 — SAHNENIN TAMAMI DUSUK KROMA.** Alti baskin kumenin HEPSINDE
|a| < 1,0 ve b +0,7..+10,3. Arena "sicak gri" bir sahnedir. Uretecimiz RescueNet
kolaji kullaniyor: mavi bina catisi, yesil cim, doymus renkler. Model alti kez
YANLIS BIR RENK DUNYASI ogrendi.

**BULGU 2 — ZEMIN ile MOLOZ arasinda TEMIZ ve OLCULEBILIR ayrim var:**

    zemin : L 150..159 · b +11..+13,5   (sicak, acik)
    moloz : L 102..114 · b  +3..+4,5    (notr, koyu)
    -> dL yaklasik 45 · db yaklasik 8

Yani gercek arenada zemin/moloz ayrimi PARLAKLIK + SICAKLIK ile yapilabiliyor.
Uretecimizde moloz RescueNet bina catisi oldugu icin bu iliski YOK.

**🔴 BULGU 3 — D-84'un IKI OKUMASI YANLIS. Duzeltiliyor.**

  (a) **HB pedi KIRMIZI DEGIL.** D-84 sartname METNINDEN "uzerinde KIRMIZI H
      harfi" diye yazmisti ve ben T56'da uretece "2x2 m KIRMIZI branda"
      koydurmustum. Sartnamenin KENDI FIGURU aksini gosteriyor ve olculdu:
      HB_ped a = -2,0 · b = -2,1 -> KROMA SIFIR, NOTR. Gorsel: SIYAH kare
      uzerinde BEYAZ H harfi ve BEYAZ cerceve — standart helipad isareti.
      **Sartname METNI ile KENDI FIGURU celisiyor.** Uretec bugun duz kirmizi
      dikdortgen basiyor; ucu de birbirini tutmuyor.

  (b) **Bariyer bir YIGIN degil, KOLLU BARIYER.** Figurde iki adet uzun, ince,
      YATAY kirmizi-beyaz seritli kol var (yol bariyeri kolu). Kapali guzergahi
      kapatan sey bu. Uretecte hic yok.

**BULGU 4 — IHA-IB (30x30 m MAVI bolge) FIGURDE YOK.** Sartname metni tarif
ediyor, kendi figuru gostermiyor. Kare icinde mavi hicbir bolge yok. Metin ile
figur arasindaki IKINCI celiski. Uretece eklenmesi metne dayanir, olcume DEGIL —
bu ayrim kayda gecmelidir.

**BULGU 5 — ZEMINDE IZGARA CIZGILERI VAR.** Ince koyu kareli izgara (L~25
kumesi, sahnenin %7,5'i; icine golge ve HB pedi de giriyor). Uretecte YOK.
Guclu, duzenli bir gorsel isarettir; modelin zemin sinifini ogrenmesini
etkileyebilir — sadakat acisindan eklenmeli, ama tek basina "iyilestirme"
sayilmamali.

**BULGU 6 — MOLOZ, KORIDOR DUVARI olarak dizilmis.** Buyuk duz beton levhalar
(kimi dik, kimi yatik) ve kirik blok yiginlari, uc koridoru cevreleyen
DUVARLAR olusturuyor. Uretecin rastgele serpistirilmis moloz seritlerinden
yapisal olarak farkli.

**KULLANIM SINIRI (degismedi).** Tek karedir. Bu kunye RENK/DOKU hedefidir;
istatistiksel dagilim degildir. Ikinci gercek kare gelirse yeniden olculmelidir.

**DOGRULANAMADI**
  1. Figurun gercek yarisma arenasini mi yoksa temsili bir gorseli mi
     gosterdigi bilinmiyor. Sartnamenin kendi belgesidir; daha iyi kaynak yok.
  2. Olcek: figurde 50x50 m HTAB'in piksel karsiligi izgaradan tahmin edilebilir
     ama bu gorevde OLCULMEDI.
  3. Metin/figur celiskileri (HB rengi, IHA-IB varligi) COZULMEDI. Yarisma
     otoritesine sorulmasi gereken bir konudur — insan isi.

---

### D-88 · KISIT · Fiziksel mini arena kurulamaz: arena basarimi KALICI OLARAK dogrulanamaz
Kayit: Claude 2 · 2026-08-13 · kullanici karari

Kullaniciya soruldu: bez + gri bloklar + kirmizi-beyaz serit ile kucuk bir
arena kurup balkondan/catidan 20-30 kare cekmek mumkun mu? **Cevap: HAYIR,
imkansiz.**

**SONUC — her raporda kalici olarak yer alacak:** projenin gercek arena
goruntusu **TEK KAREDIR** (`sartname_s9_arena.png`) ve baska kare gelmeyecek.
Bu nedenle:

  1. Hicbir model secimi, esik kalibrasyonu veya algi iyilestirmesi ARENA
     BASARIMINI dogrulayamaz. "Dogrulanamadi: arena basarimi — kamera yok"
     cumlesi gecici bir not degil, KALICI bir kisittir.
  2. Tek kare uzerinde olculen her sey DAVRANISIN VARLIGI/YOKLUGU icindir
     (model goruyor mu, kapi eliyor mu); istatistik degildir.
  3. Esik ve model kararlarinda mesru taraf tek noktaya dayanir. Bu, D-86'da
     olculen "tam ayrik cift yok" sonucunun da arka planidir.

Bu kayit D-56'yi (kamera yok) genisletir ve KAPATIR: artik "belki sonra" yok.

---

### D-89 · DENETIM · T58 dort ucu hizaladi ama BESINCI UC cevrilmedi: saha olcum betigi v20'de kalmis
Denetleyen: Claude 1 (mimar) · 2026-08-13 · gorev T58 · bagimsiz kosuldu

**T58'IN IDDIALARI DOGRULANDI — hicbiri soze dayanmadi.**

    tests/test_uretim_modeli_hizasi.py       Ran 12 · OK   (dort uc tek surume bagli)
    tests/test_gercek_arena_kapisi.py        Ran  7 · OK   (atlanan YOK)
    comms/yks_gui.py:898  ALGI_MODEL_DOSYA = navitas_seg_v24_best.pt
    jetson_paket/models/  v24 .pt (54.852.380 B) + v24 640_fp16.onnx  MEVCUT
    manifest  pc_modeli = v24 · paket_icerigi her dosyanin sha256'sini tasiyor

Arena kapisi testinin GERCEKTEN cikarim kostugu dogrulandi (sahte gecis
aranmistir): `setUpClass` icinde `YOLO(MODEL, task="segment")` +
`model.predict(...)`; `_ATLA` False (agirlik ve kare mevcut). Yedi testin
"ok" gorunmemesi docstring satirindandir, atlama degildir.

**🔴 BULGU — BESINCI UC VAR ve CEVRILMEDI.** T58 "dort uc birlikte cevrildi"
diyor (GUI · paket · manifest · iki kilavuz). Besinci bir uc daha var:
saha basarim olcum betigi. Varsayilanlari OLCULDU:

    scripts/jetson_fps.py           (KAYNAK)
    jetson_paket/kod/jetson_fps.py  (KOPYALAR haritasindan turetilmis)

    :248  --pt      default = models/navitas_seg_v20_best.pt
    :249  --onnx    default = models/navitas_seg_v20_best.onnx
    :250  --engine  default = models/navitas_seg_v20_best.engine
    :254  --conf    default = 0.25

    URETIM:  codes/rpi_inference.py:1204  --conf default = 0.30
             comms/yks_gui.py:904         ALGI_PREDICT_CONF = 0.30

Yani argumansiz kosuldugunda saha olcumu **v20**'yi **conf 0.25** ile olcer.
v20 ne bugunku uretimdir (v24) ne de onceki uretimdir (v21) — hicbiri degildir.
Ustelik `--onnx` ve `--engine` varsayilanlari **var olmayan dosyalari** gosterir;
pakette v20 ONNX yoktur (v17/v21/v24 vardir).

**KILAVUZ BU BAYATLIGI BELGELIYOR** — `jetson_paket/JETSON_KILAVUZ.md:63-64`:

    | `--pt`   | ...navitas_seg_v20_best.pt   | var ama **v20** — kilavuzun kendi onerisi v21 |
    | `--onnx` | ...navitas_seg_v20_best.onnx | **YOK** (yalniz v17 ve v21 ONNX var)         |

Kilavuzun 15 · 223-224 · 299. satirlari v24'e cevrilmis; 63-64 cevrilmemis.

**ETKI.** Karar zincirinde DEGILDIR — yanlis rota uretmez. Ama T15-T18'in
tamami ve "Jetson'da yetisir mi" sorusunun tamami bu betigin sayilarina
dayanir. Yanlis model + yanlis esik = olcum butunlugu kusuru. Bu, T58'in
kapatmayi amacladigi D-58/D-60 iraksama sinifinin ta kendisidir.

**YENI KAPI NEDEN YAKALAMADI.** `test_uretim_modeli_hizasi.py` dort ucu
kapsiyor (GUI sabiti, paket icerigi, manifest, iki kilavuz); **betik
VARSAYILAN ARGUMANLARINI** kapsamiyor. Kapi dogru kuruldu, kapsami eksik.

**VERDIKT: T58 KOSULLU KAPANIR.** Surum gecisi dogru ve dogrulanmistir;
eksik olan besinci uctur. Takip gorevi **T62** olarak kuyruga girdi.

**AYRICA — KAPANMAYAN, ama T58'in kusuru DEGIL.** T58'in kendi olumsuz
bulgusu ("v24 kompozit arenada hicbir sey degistirmiyor, 9/9 ret") bir MODEL
bulgusu degil, bir OLCUM ZEMINI bulgusudur: `data/arena_kompozit` arka plani
OTOPARKtir (D-53). Otopark uzerinde kapinin ret vermesi dogrudur — fail-safe
calisiyor. Bu kume model AYIRT EDEMEZ; K3'u orada olcmek yanlistir. Kayit
duzeltilmedi, uzerine yazilmadi: yorumu burada duruyor.

**DOGRULANAMADI**
  1. Jetson'da hicbir olcum yok; bu bulgu betigin PC'deki varsayilanlarina
     dayanir. Betik sahada elle arguman verilerek kosulmus olabilir — ama
     kilavuz argumansiz kosmayi tarif ediyor.
  2. `--imgsz` varsayilani [640, 512]; uretim `INFER_SIZE` ile hizasi bu
     denetimde OLCULMEDI. T62'de olculmelidir.

---

### D-90 · OLCUM · Karar dogrulugu ILK KEZ sartnameye sadik zeminde olculdu; "serit dogrulugu" olcutu GUVENILMEZ cikti
Olcen: Claude 1 (mimar) · 2026-08-14 · zemin `calisma/sentetik_arena_kadraj_t60` (T60, n=260) · model v24 · uretim zinciri

**NEDEN BU OLCUM YOKTU.** Bugune kadar iki ayri sey olculuyordu ve ikisi de bu
soruyu yanitlamiyordu: `57_t51_kadraj_kapilari.py` YER GERCEGI etiketleriyle
kosar (URETECIN geometrisini sinar, modeli DEGIL); `56_uc_kapili_model_secimi.py`
K3 ise `data/arena_kompozit` uzerinde olcer — o kumenin arka plani OTOPARKTIR
(D-53/D-89) ve modelleri ayirt edemiyor. "Model, sartnameye sadik bir arenada
dogru guzergahi buluyor mu" HIC olculmemisti. Yeni betik: `60_...py`, `61_...py`.

**🔴 BULGU 1 — "SERIT DOGRULUGU" OLCUTU TANIMA BAGLI ve bu yuzden GUVENILMEZ.**
Ayni kararlar, ayni model, ayni kume; degisen yalniz KIYAS TANIMI:

    icerik = TUM KARE (uretimin yaptigi)   DOGRU 241/260 %92,7 · TEHLIKELI  8 %3,1
    icerik = ARENA kutusu (kahin)          DOGRU 176/260 %67,7 · TEHLIKELI 55 %21,2

Sebep: `analyze_path` seritleri `icerik`in UCTE BIRI olarak tanimlar; uretecin
manifesti ise seritleri ARENANIN ucte biri sayar. Kadraj karesinde arena kare
icinde iceridedir (`arena_x_araligi` 122,5..517,5 / 640 — genisligin %38'i arena
DISI). Iki tanim ortusmez, dolayisiyla "serit dogru mu" sayisi olcumun degil
tanimin ozelligidir. **%92,7 rapor edilmek uzereydi; kendi kahin denetimimle
curutuldu.**

**NULL MODEL KONTROLU** (D-15/K-04: kontrolsuz sayi olcum degildir):

    hep serit 1   DOGRU %45,0 · TEHLIKELI %55,0
    hep serit 2   DOGRU %73,8 · TEHLIKELI %26,2   <- en iyi basit tahmin
    hep serit 3   DOGRU %47,7 · TEHLIKELI %52,3
    rastgele      DOGRU %55,4 · TEHLIKELI %44,6

Arena-hizali kiyasta v24 (%67,7) "hep orta"dan (%73,8) **DAHA KOTUDUR**. Yani
serit olcutune gore sistem basit bir sabit tahmini yenemiyor.

**BULGU 2 — TANIMDAN BAGIMSIZ OLCUT SORUYU YANITLIYOR.** Gorevin sordugu sey
"serit indisi dogru mu" degil, "IKA carpar mi". Rota `r_gerekli_px` ile
kalinlastirilip YER GERCEGI engel maskesiyle kesistirildi (mimarin
`arena-olcum-araci` notu: *asil olcut moloza basma oranidir*):

    v24 · T60 kadraj · n=260
      ROTA URETILDI          249 / 260   %95,8
      MOLOZA BASIYOR (>0)      6 / 249   % 2,4
      AGIR BASMA   (>%5)       6 / 249   % 2,4
      ARENA DISINDA (>%10)    10 / 249   % 4,0
      basma orani  medyan %0,00 · ort %1,82 · maks %100

Uretilen rotalarin **%97,6'si molozla hic temas etmiyor**. Serit tartismasi bu
olcutte buharlasiyor; bundan sonra karar kalitesi BU olcutle raporlanmalidir.

**🔴 BULGU 3 — KARAR YOLUNUN ARENA SINIRI KAVRAMI YOK.** Rotalarin %4'u
buyuk olcude arena DISINDAN geciyor. Uretec arena disina bilerek ETIKETSIZ duz
zemin cizer (gercekci: dronun gordugu arazi arena ile bitmez) ve model orayi
hakli olarak zemin isaretler; `analyze_path` ise tum kareyi ucte bolup o bos
kenari gecerli guzergah sayabiliyor. `sa_000070`'te darbogaz **304 px** cikti —
640'lik karede neredeyse bos bir sahneden gecmek demektir.

**AYNI KUSUR GERCEK KAREDE DE VAR.** `sartname_s9_arena.png` uzerinde uretim
zinciri kosuldu: izgarali arenanin DISINDAKI toprak da zemin isaretleniyor.
Bu sentetik bir yan etki degildir.

**BULGU 4 — SUBSTRAT A/B (v24 sabit, zemin degisti).** ⚠ **ESLESTIRILMIS DEGIL**
— iki kume farkli sahneler icerir, fark sahne cesitliliginden de gelebilir:

    zemin        ROTA URETILDI   MOLOZA BASIYOR   ARENA DISINDA
    T56 (eski)    204/260 %78,5     1/204 %0,5     17/204 %8,3
    T60 (yeni)    249/260 %95,8     6/249 %2,4     10/249 %4,0

T60 daha cok rota uretiyor ve arena disina daha az tasiyor; ama moloza basan
rota sayisi 1'den 6'ya cikiyor. Bu bir ODUNLESMEDIR (cekimserlik <-> ilerleme),
"iyilesme" diye yazilmamalidir. Eski zemin daha cok susuyor.

**BULGU 5 — GERCEK ARENADA ZINCIR ROTA URETIYOR, AMA YAYINLAYAMIYOR.**

    kaplama 0,579 (tavan 0,67) · kenar 0,585 (tavan 0,50) -> kapi SUSUYOR (T59 dogru)
    open_path = 2 (ORTA) · guven 0,75 · 8 waypoint · karar reddi YOK
    rota_olcek_reddi -> OLCEK_YOK   ->  URETIMDE ROTA YAYINLANMAZ

**BULGU 6 — GERCEK ARENA KARESI EGIK; TEK SKALER `mpp` ORADA GECERSIZ.**
2,0 m'lik HB pedi olculdu: yatay ~72 px, dikey ~38 px (paralelkenar). Ayni 2 m
iki eksende iki farkli piksel karsiligi veriyor:

    yatay mpp 0,0278 -> r_gerekli 39,6 px ; darbogaz 27,8 px -> RET
    dikey mpp 0,0526 -> r_gerekli 20,9 px ; darbogaz 27,8 px -> GECER

Karar EKSENE gore terse doner. `CONTRACTS.md` SS5 tek skaler `mpp` varsayar; bu
yalniz NADIR (dik) bakista gecerlidir. Sartname figuru dik degildir.

**DOGRULANAMADI**
  1. Figurun metrik olarak dogru bir foto mu yoksa temsili bir render mi oldugu
     bilinmiyor; oyleyse ondan turetilen her mpp supheldir. (D-87/1'in devami.)
  2. T56<->T60 kiyasi ESLESTIRILMIS DEGIL; ayni tohumla ayni sahnelerin
     uretilip yalniz renk/dokunun degistigi bir kume ile tekrarlanmalidir.
  3. Arena basarimi yine dogrulanmadi (D-88, kalici kisit).
  4. Bu olcumlerin tamami v24 icindir; substrat degisirse ve model yeniden
     egitilirse hepsi yeniden olculmelidir.

---

### D-91 · DENETIM · T60 renk kunyesi BAGIMSIZ dogrulandi; GEOMETRI acigi kaldi (ureteci tarafindan da bildirildi)
Denetleyen: Claude 1 (mimar) · 2026-08-14 · gorev T60 · uygulayan Codex-1

**BAGIMSIZ OLCUM — Codex'in betigi kullanilmadi.** T60 kadraj kumesinin 60
karesinde YER GERCEGI etiketleriyle bolge LAB ortalamasi:

    sinif      L        a         b       D-87 hedefi
    zemin   149,2   +1,59   +11,39      L 150..159 · a +2 · b +11..13,5
    moloz   108,0   -0,50    +4,44      L 102..114 · a -1 · b  +3..4,5
    dL = 41,2                            (gercek arena ~45 · kapi >=35)

Moloz bandin TAM ICINDE; dL kapiyi geciyor. **Zemin L'si bandin 0,8 ALTINDA**
(149,2 < 150). Codex kaynak-yama degerlerini 154,0 / 153,7 diye bildirmisti;
fark nihai JPEG + fotometrik bozunum + erozyondan geliyor ve Codex bunu
kismen kendi bildirdi (arena-ici erozyonlu class-0 151,3). Kusur sayilmaz —
hedef bandi TEK gercek karenin bolge ortalamalarindan turetilmistir, 0,8'lik
sapma o bandin belirsizliginden kucuktur. Yine de kayda gecer.

**GOZLE DOGRULAMA (gorsel kazanir · D-80).** `results/t60/t60_yan_yana.png`:
bes maddenin besi de teslim edilmis — sicak/acik zemin, koyu-notr ama dokusu
korunmus moloz, SIYAH ped + BEYAZ H, kirmizi-beyaz seritli bariyer, ince
izgara. **Ancak GEOMETRI gercek arenanin esligi degildir:** gercek arena
"acik toprak tarlasi + icine serpilmis moloz ADALARI"; uretec ise DIKEY
SERITLER uretiyor. Bunu Codex kendi raporunda da yazdi ("dar serit/dikdortgen
kolaj geometrisi gercek arenanin esleniği degildir; arena basarimi iddia
edilmedi") — gizlenmedi, ayri goreve birakildi.

**OYUNA KARSI KAPI GECTI.** Renk kapisi tek basina duz gri boyayarak
gecilebilirdi; doku genligi olcumu bunu engelledi (mimarin sart kostugu AND):
kaynak-yama koruma zemin 0,999 · yol 1,000 · moloz 0,940/0,939; nihai JPEG
zemin 0,872x · blocked 1,017x — hepsi 0,75 esiginin ustunde.

**KOSULAN KAPILAR (mimar tarafindan tekrar kosuldu).**

    unittest discover -s tests -q      Ran 322 · OK · exit 0     GECTI
    codes/test_rota_sentetik.py        SONUC: 15/15 dogru        GECTI
    ADIM 0 (fikstur sozlesmeden turetiliyor)                     GECTI

**VERDIKT: T60 KAPANIR.** Renk/malzeme sadakati olculdu ve dogrulandi.
Geometri sadakati **T66** olarak acildi.

**DOGRULANAMADI**
  1. Bu gorev arena BASARIMINI dogrulamaz (D-88, kalici).
  2. Yol (asfalt/iz) icin ayri bir D-87 renk hedefi OLCULMEDI; mevcut T57
     dokusu korundu.
  3. Renk duzeltmesinin karar duzeyine etkisi ESLESTIRILMIS olarak olculmedi —
     T56/T60 kiyasi farkli sahneler icerir (D-90 bulgu 4).

---

### D-92 · 🔴 GOREV KRITIK · Gercek arenada rota BARIYER KOLUNUN ICINDEN geciyor; model bariyeri hic gormuyor
Olcen: Claude 1 (mimar) · 2026-08-14 · `data/arena_referans/sartname_s9_arena.png` · v24 · uretim zinciri

**BARIYER NEDIR.** Sartname figurunde KAPALI guzergahi kapatan tek yapi, iki
adet kirmizi-beyaz seritli YOL BARIYERI KOLUDUR (D-87 bulgu 3b). Ince ve
yukseltilmistir; altindaki ve cevresindeki zemin gorunur kalir.

**OLCUM (modelden BAGIMSIZ bariyer tespiti).** Bariyer, sahnedeki tek yuksek
kromali kirmizi yapidir (D-87: geri kalanin tamaminda |a| < 1), bu yuzden LAB
a* > 25 ile guvenle bulunur — model kullanilmadi:

    bariyer kolu 1 : x=687 y=208 w=228 h=16   (uzun kol)
    bariyer kolu 2 : x=462 y=210 w= 98 h=14   (kisa kol)
    bariyer pikselleri: n = 3644

    model ENGEL diyor : %0,0     <-- TEK PIKSEL BILE DEGIL
    model ZEMIN diyor : %30,9

**SONUC — URETILEN ROTA BARIYERI KESIYOR: 59 px.** Gorsel dogrulandi: rota
IKA'nin bulundugu alt banttan cikip yukari gidiyor ve KISA BARIYER KOLUNUN tam
ortasindan geciyor. Sahada IKA bariyere carpardi.

**🔴 KORUMALARIN HICBIRI ATESLEMIYOR.**

    zemin kapisi   kaplama 0,579 < 0,67 · kenar 0,585      -> SUSUYOR (T59 dogru)
    karar reddi                                             -> YOK
    guven                                                   -> 0,75 (esik 0,20)
    darbogaz 27,8 px                                        -> genis gorunuyor

Rotayi yayindan alikoyan TEK sey `OLCEK_YOK`. Yani bugun bizi koruyan sey bir
guvenlik kapisi degil, bir EKSIKLIK. 

**🔴 DOGRUDAN SONUC — GOREV SIRALAMASI DEGISTI.** T64 (hakem ekranina arena
kaynagi + olcek) tek basina UYGULANIRSA sistem bariyere giren bir rotayi
YAYINLAR hale gelir. Olcek halkasi kapatilmadan once ya da onunla birlikte
bariyer/ince-engel tespiti cozulmelidir. T64 promptu bu nedenle `arena_gercek`
icin mpp DONDURMEMEYI zaten sart kosuyordu; bu kayit o sarti GEREKCELENDIRIR.

**NEDEN GORMUYOR — SINANABILIR ONGORU.** v24 T60 ONCESI substratla egitildi;
orada "bariyer" TEK RENK ince bir `cv2.line` idi (uretecin ~720. satiri).
T60 ile uretec artik KIRMIZI-BEYAZ SERITLI kol ciziyor. Su an egitilen
**v25 bu veriyle ogreniyor**; bariyeri engel sayip saymadigi sabah AYNI
olcumle sinanacaktir. Ongoru yazildi ki sonuc ne cikarsa ciksin kayitli olsun.

**KAPSAM SINIRI.** Tek karedir (D-88). "Model bariyerleri goremiyor" genel bir
iddia DEGILDIR; olculen sey "bu karede gormedi"dir. Ama bu kare projenin sahip
oldugu TEK gercek arena goruntusudur ve bariyer sartnamenin kapatma yontemidir.

**DOGRULANAMADI**
  1. Sentetik kadraj kumesinde bariyer kesisimi AYRICA olculmedi; oradaki
     bariyerler uretecin cizdikleridir, gercek degil.
  2. Bariyerin fiziksel yuksekligi ve dolayisiyla IKA'nin altindan gecip
     gecemeyecegi bilinmiyor — sartname olcu vermiyor. Fail-safe varsayim:
     gecilemez.
  3. Ince-engel sinifinin genel cozumu (tel, halat, kablo) bu kayitta ELE
     ALINMADI.

---

### D-93 · OLCUM · D-92'nin ONGORUSU CURUTULDU: uretec bariyeri ASLA acik zemine koymuyor, v25 bunu ogrenemez
Olcen: Claude 1 (mimar) · 2026-08-14 · zemin T60 kadraj (120 kare) · v25 egitimi KOSARKEN

**D-92'de yazdigim ongoru:** "v25 seritli bariyerle egitiliyor, bariyeri engel
sayip saymadigi sabah sinanacak." Sabahi beklemeden KOD + OLCUM ile bakildi ve
ongoru **CURUTULDU**. Kayit, sonuc lehte cikmadigi icin silinmiyor; duzeltiliyor.

**KOD (uretec, ~934-944).**

    kapali_indisler = [i for i, d in enumerate(durumlar) if d == "kapali"]
    ...
    if kapali_indisler:
        i = kapali_indisler[ham_i % len(kapali_indisler)]
        bariyer_tarifleri.append(...)

Bariyer YALNIZ **zaten KAPALI** seritlere ciziliyor — yani molozla doldurulmus
ve `blocked` etiketli bolgelere. Tum seritler acikken bariyer HIC cizilmiyor.

**OLCUM (bariyer tespiti modelden bagimsiz · LAB a*>25 · uzun/ince):**

    120 kare incelendi · 70'inde bariyer bulundu
    BARIYER PIKSELLERININ YER GERCEGI ETIKETI
      zemin          31   % 0,0
      engel     142.260   %92,4
      etiketsiz  11.655   % 7,6

**SONUC.** Egitim verisinde bariyer, molozun UZERINDEKI bir susdur. Gercek
arenada ise bariyer, aksi halde ACIK olan zeminin ustunden gecen ve guzergahi
KAPATAN yapidir (D-92). Bu konfigurasyon egitim kumesinde **hic gecmiyor**;
dolayisiyla v25'in "ince seritli cubuk = engel" kuralini ogrenmesi icin
gerekcesi yoktur. v25 bu konuda v24'ten farkli davranirsa sebebi bariyer
ogrenimi DEGIL, baska bir yan etkidir — oyle yorumlanmamalidir.

**BU BIR ETIKETSIZ-ENGEL HATASI DEGILDIR.** Bariyer pikselleri %92,4 oraninda
`blocked` tasiyor; v16 cokusunu doguran "etiketsiz gecilemez nesne" kusuru
BURADA YOK. Kusur ETIKETTE degil, KONFIGURASYONDA: yanlis yerde duruyor.

**GEREKEN (T68).** Uretec, acik seridi KAPATAN bariyer uretebilmelidir: ince
seritli kol acik zeminin uzerine cizilir ve **kendi pikselleri `blocked`
etiketlenir** (alttaki zemin degil — cubugun kendisi). Boylece "ince cubuk =
gecilemez" kurali ogrenilebilir hale gelir.

**DOGRULANAMADI**
  1. Modelin ince yapilari 640 px cikarim cozunurlugunde ogrenip
     ogrenemeyecegi OLCULMEDI — gercek bariyer kolu 14-16 px kalinliginda;
     `imgsz=640` ve maske protolari 512'de cozuluyor. Ogrenilebilirlik ayri
     bir sorudur ve veri duzeltilmeden sinanmasi anlamsizdir.
  2. Bu kayit v25'in ne yapacagini KANITLAMAZ; yalnizca "bariyeri ogrenmis
     olma" yorumunun gerekcesiz oldugunu soyler. Olcum sabah yine kosulacak.

---

### D-95 · 🔴 KARAR · v25 URETIME GIRMIYOR: sentetikte kusursuz, GERCEK ARENADA TAMAMEN KOR
Olcen/karar: Claude 1 (mimar) · 2026-08-14 · v25_t60_renk (best.pt = epoch 106/150+)

> ⚠ NUMARA CAKISMASI (BESINCI). Bu kayit once D-94 yazildi; Claude 2 ayni anda
> T65 icin D-94 kullandi. Kural geregi **kendi** kaydimi tasidim (D-95), baska
> ajanin kaydina dokunmadim. Dosyada D-95, D-94'ten ONCE gelir.
>
> ⚠ D-94'un (Claude 2) gecerli bir itirazi asagidaki sentetik sayilara da
> uygulanir: uretec KADRAJ kipinde geometrik ve fotometrik bozunumu KAPATIYOR
> (`return im if kadraj else sonuc`). Yani T60 kadraj uzerindeki tum sonuclar —
> v24'unkiler de v25'inkiler de — **IYIMSER UST SINIRDIR**; egim, golge,
> bulaniklik ve JPEG bozunumu o 260 karede yoktur. Bu, v25'in sentetik
> ustunlugunu daha da suphelı kilar ve karari GUCLENDIRIR.

**DENEYIN TASARIMI (projedeki en temiz esleştirilmis substrat deneyi).** v25,
v24 ile **BIREBIR ayni** recete, ayni on-egitim (`v15_on10sinif`), ayni karisim
yaml'i, ayni seed/augmentasyon ile kosuldu. Degisen TEK sey: `sentetik_arena`
bileseni T60 renk kunyesiyle yeniden uretildi. Yani olculen sey substratin
renk sadakatinin etkisidir.

**SENTETIK ZEMINDE v25 CARPICI BICIMDE DAHA IYI** (T60 kadraj, n=260):

    olcut                        v24            v25
    ROTA URETILDI            249/260        257/260
    MOLOZA BASIYOR (>0)      6  %2,4        0  %0,0     <- SIFIR
    ARENA DISINDA (>%10)    10  %4,0        0  %0,0     <- SIFIR
    basma orani maks           %100          %0,00
    (serit olcutu · TANIMA BAGLI, baglam icin)
    TEHLIKELI                8  %3,1        6  %2,3
    DOGRU                  241  %92,7     251  %96,5

D-90 bulgu 3'teki **arena disina tasma tamamen kayboldu**. Bu, T65'in cozmeye
calistigi kusurun bir kismi icin veri tarafinda cozum oldugunu gosterir.

**🔴 GERCEK ARENA KARESINDE v25 TAMAMEN KOR.**

    conf    v24 zemin  v24 engel   v25 zemin  v25 engel
    0.30       %34,6      %0,5        %0,0      %0,1
    0.20       %34,6      %0,5        %0,0     %14,7
    0.10       %34,6      %2,8        %0,0     %43,2
    0.05       %34,6      %2,8        %0,0     %43,2
    0.02       %34,6      %4,2        %0,0     %48,2

Esik meselesi DEGILDIR: 0,02'ye kadar zemin SIFIR. Dahasi v25 kareyi
kacirmiyor — arenanin tamamini **ENGEL** ilan ediyor (%43-48). Karar:
`MASKE_YOK`, serit None. Gorselle dogrulandi (`results/t63/harita_v25_GERCEK.png`).

**KORLUK GENEL DEGIL, ARENAYA OZGU.** v25 diger her kaynakta v24 ile
neredeyse ayni:

    kaynak                  n    v24 bos/kaplama    v25 bos/kaplama
    GERCEK ARENA            1     0/1  %34,6         1/1  %0,0    <- TEK FARK
    raw_frames OTOPARK      2     0/2  %44,4         0/2  %44,5
    copy_paste_gercek      12    0/12  %45,2        0/12  %45,3
    sentetik_arena val     12    0/12  %20,6        0/12  %19,9

Yani "v25 gercek fotograflari reddediyor" iddiasi YANLIS olurdu; kusur tam
olarak hedef alan gorseline ozgudur.

**KARAR: URETIM MODELI v24 KALIR.** Gerekce: karar verdigimiz tek sey gorevin
kosulacagi alandir ve elimizdeki tek ornekte v25 hicbir rota uretemez.
Sentetik kazanc, hedef alandaki tam korlugu telafi etmez (madde 15 ruhu:
guvenli taraf cekimserliktir ama gorev de ilerlemelidir; v25 ikisini birden
kaybettirmez, gorevi kaybettirir).

**mAP YINE YANILTTI — K-3 dogrulandi.** v25 val mAP50-95(M) = 0,6979;
v24 = 0,7179. Iki sayi da arenadaki nitel farki (goruyor / kor) hic
gostermiyor. Model secimi mAP ile YAPILAMAZ; bu kayit K-3'un dorduncu
tekrar dogrulamasidir.

**ONEMLI SONUC — SUBSTRAT SADAKATI TEK BASINA YETMIYOR.** T60 rengi olculmus
hedefe oturttu (D-91) ve sentetik basarim ucuruma gitti; ama gercek karede
sonuc TERSINE dondu. Substrati kendi icinde tutarli hale getirmek, modeli o
tutarliliga BAGIMLI da yapabiliyor. Kalan farklar: geometri (T66), egik bakis
(D-90 bulgu 6), ve figurun render mi foto mu oldugu (D-87 dogrulanamadi-1).

**DOGRULANAMADI**
  1. Korlugun MEKANIZMASI bilinmiyor. Renk mi, izgara mi, egiklik mi, geometri
     mi — olculmedi. Ayri gorev (T69).
  2. n=1. "v25 arenada kor" ifadesi TEK KARE icindir (D-88 kalici kisit).
     Ama o kare hedef alanin sahip oldugumuz tek ornegidir.
  3. Ara kontrol noktasi YOK (yalniz best/last). Daha erken bir epoch'un hem
     sentetikte iyi hem arenada goren bir denge tutup tutmadigi SINANAMADI.
  4. ~~v25 200 epoch'a tamamlanmadan olculdu (best.pt = epoch 106).~~
     **KAPANDI 2026-08-14 08:33** — kosu 200/200 tamamlandi, `best.pt` epoch
     **173** oldu (mAP50-95(M) 0,7009) ve olcum TEKRARLANDI:

         sentetik T60 kadraj : rota 256/260 · moloza basma 0 %0,0 ·
                               arena disi 0 %0,0 · TEHLIKELI 7 %2,7 · DOGRU %95,8
         GERCEK ARENA        : zemin %0,0 -> MASKE_YOK   (degismedi)

     Karar DEGISMEDI: v25 uretime girmez. "Daha cok epoch gerekiyordu" acikligi
     boylece kapandi.

     YAN GOZLEM: tamamlanmis v25, bariyer piksellerinin %65,7'sini ENGEL
     sayiyor (v24: %0,0). Bu **bariyer ogrenimi DEGILDIR** — v25 arenanin
     TAMAMINI engel sayiyor, dolayisiyla olcut secici degil. D-93'un ongorusu
     ayakta; boyle yorumlanmamalidir.

---

### D-94 · OLCUM + KISMI COZUM · T65: arena siniri YERELLESTIRILEMEDI; koridor genisligi tavani kondu (10 -> 5)
Olcen/uygulayan: Claude 2 · 2026-08-14 · gorev T65 · kanit D-90 bulgu 3

**TABAN BAGIMSIZ DOGRULANDI** (`61_rota_moloza_basma.py`, v24, T60 kadraj):
`rota 249/260 · moloza basma 6/249 · arena disi 10/249` — gorevde bildirilen
sayilarla BIREBIR ayni.

**KUSUR DEJENEREDIR — bu, cozumun seklini belirledi.** Arena disi orani:

    == 0.000 -> 238 kare · == 0.001 -> 1 kare · == 1.000 -> 10 kare

Ara deger YOK. Rota ya tamamen arena icinde ya TAMAMEN disinda. Onun 9'u
serit 3, biri serit 1; orta serit HIC yok. Sekizinde guven **1.000** —
sistem tamamen yanlis bir rotaya azami guven veriyor. Moloza basan 6 kare ile
KESISIM YOK: iki kusur ayrik.

**YAN BULGU — GUVEN OLCUTU DOYMUS.** `ROTA_DARBOGAZ_TAM_ORANI = 0.035`, yani
640'lik karede **22,4 px**'te doyuyor. Olculdu: 23 px -> 1.000 · 40 px -> 1.000
· 304 px -> 1.000. Darbogaz genisligi bilgi tasiyor ama guven onu ATIYOR.
10 hatali karenin 8'inde azami guvenin sebebi budur. Ayri gorev konusu.

**FAZ 1 — UC ADAY SINIR IMZASI OLCULDU** (gorevin dayattigi sira: once olc).
260 kadraj karesi + gercek kare. **UCU DE GUVENILMEZ, UCU DE GERCEK KAREDE COKTU:**

    imza                 n   IoU medyan  basarili  guvenilir  gercek karede
    izgara cizgileri   260       0.806    220/260     HAYIR    TUM KAREYI verdi
    moloz kapsayan k.  260       0.664    254/260     HAYIR    dar yanli
    dis cerceve        260       0.960    226/260     HAYIR    HIC sinir uretemedi

  - **Izgara**: fiziksel temeli SAGLAM (T60 izgarayi yalniz arena icine ciziyor,
    gercek karede de oyle). Moloz tuzagi testini GECTI (molozu izgara sanmiyor).
    Bozan sey molozun izgarayi GIZLEMESI: sol kenar molozlu 118 karede dx0
    medyan 79,0 px, molozsuz 102 karede 4,0 px — **20 kat** fark. Iki kenari da
    molozsuz 27 karede imza NEREDEYSE KUSURSUZ (IoU medyan 0,981).
    Gercek karede min/max birlestirme **[0, 1058] = tum kare** verdi — yani
    sinir arenayi BUYUTUYOR, tam da onlenmek istenen kip.
  - **Moloz kutusu**: "arena disinda moloz yoktur" DOGRU, ama TERSI degil —
    moloz arenayi DOLDURMAZ. Kare basina EN KOTU kenar hatasi medyan 114,9 px
    (arena ort. genisligi 410,5 px). Yalniz iki dis serit de kapaliyken iyi
    (n=31, IoU 0,986). 6/260 karede sinif-1 maskesi tamamen BOS.
  - **Dis cerceve**: karelerin %29'unda arena sinirini degil IC SERIT sinirini
    buluyor. Kok neden URETEC KODUNDA: `sinirlar` listesi arena kenarlarini VE
    ic serit sinirlarini AYNI renk ve kalinlikta tutuyor; ustelik cerceve
    karelerin yalniz YARISINDA ciziliyor (`rng.random() < 0.5`). Gercek karede
    dusey kenar izdusumu max 0,406 < 0,45 esigi -> HICBIR SINIR URETEMEDI.

**DAHA TEMEL BULGU — GERCEK ARENA SINIRI DIKEY DEGIL.** Perspektif nedeniyle
yamuk: sol kenar x~190 (ust) -> x~65 (alt), sag x~920 -> x~1015. Tek bir
`[x0,x1]` araligi gercek arenayi TANIMLAMAZ; indirgenemez hata **~50-60 px**.
Yani gorevin (ve benim ilk kurgumun) varsaydigi CIKTI BICIMI yanlisti.

**EK UYARI:** sentetik sayilar IYIMSER UST SINIRDIR — uretec kadraj kipinde
geometrik ve fotometrik bozunumu KAPATIYOR (`return im if kadraj else sonuc`);
o 260 karede egim, golge, bulaniklik ve JPEG bozunumu YOK.

**FAZ 2 — SINIR YERELLESTIRILMEDEN COZUM.** Kusur dejenere oldugu icin
"sinir nerede" sorusu GEREKMIYOR; "bu bir koridor mu" sorusu yetiyor.

    OLCUT: koridorun EN DAR yeri bir SERIDIN tamamindan genis olamaz.

Sartname arenada UC guzergah tanimlar ve bunlar molozla ayrilir; bir seridin
tamamindan genis bir "koridor" uc guzergahtan biri DEGILDIR — acik arazidir.
Tavan `serit_no`nun KENDI bolusumunden turetilir (m.16), ciplak sayi degildir.

    kume                     darbogaz / icerik_w
      MESRU (arena ici) 239   medyan 0.094 · p95 0.208 · MAKS 0.280
      KUSURLU (disi)     10   0.022 · 0.028 · 0.111 · 0.170 · 0.314
                              0.353 · 0.358 · 0.375 · 0.475 · 0.487

    tavan 1/3 = 0.333 -> yanlis elenen MESRU 0/239 · yakalanan 5/10
    mesru tarafa pay 0.053 · kusurlu tarafa pay 0.020

**FIT EDILMIS TAVAN BILEREK SECILMEDI.** 0.280 ile 0.333 arasina konacak bir
tavan 6/10 yakalardi. Reddedildi cunku: (i) fiziksel degil FIT olurdu;
(ii) 0.280 sentetik ve bozunumu kapali karelerden gelir, gercek mesru dagilim
daha GENISTIR — optimist bir azamiye esik oturtmak **D-85'in hatasidir**;
(iii) payi 0.017'ye inerdi. Bu gerekce testle kilitlendi
(`test_neden_FIT_EDILMIS_tavan_secilmedi`).

**KISMI COZUMDUR, GIZLENMIYOR.** Kacan 5 kareden **4'u** mesru azaminin
altinda ve genislikle AYIRT EDILEMEZ. Sebep olculdu: arena disi bolge her
zaman bos DEGIL — `sa_000068`'de arena disi bir **OTOPARK FOTOGRAFI** tasiyor
(park cizgileriyle) ve model orada 14,2 px darbogazli kendi koridorunu
buluyor. Genislik olcutu bu sinifi yakalayamaz; gercek sinir bilgisi gerekir
ve o bilgi bugun YOKTUR.

**KAPSAM ENGELI — KISIT BAGLANAMADI, DEPO DURUMU BOYLE BIRAKILDI.**
Gorevin izin listesi: `codes/costmap_path_finder.py` · `codes/karar_sozlesmesi.py`
· `CONTRACTS.md` · `tests/**`. Ama kusur `codes/rpi_inference.py` icindeki
`analyze_path`tadir ve o dosya listede YOK. Izinli iki dosyaya GORUNTU HIC
ULASMIYOR; `analyze_path` asagi yalniz maskeleri geciriyor:

    zemin_maskesi_reddi(trav_mask, icerik)   <- yalniz zemin maskesi
    astar(gecilebilir, ...) · plan_izgarasi(dt_px, gecilebilir, ds)

Darbogaz `analyze_path` icinde hesaplaniyor (`olcum["darbogaz_px"]`) ve
`rota_darbogaz_guveni` ile guvene ceviriliyor; ama ret uygulanmiyor —
`rota_guven_reddi` AYRI bir fonksiyonda (`_rota_kararini_esikle`).
Yeni olcutu devreye almak icin `analyze_path` icinde **tek bir cagri** gerekir:

    kg_reddi = rota_koridor_genisligi_reddi(olcum["darbogaz_px"], icerik_w)
    if kg_reddi is not None:
        return _don(None, 0.0, [], clean, kg_reddi, olcum)

Bu satir YAZILMADI; `codes/rpi_inference.py`'ye DOKUNULMADI. Sozlesme, sebep
kodu, `CONTRACTS` maddesi ve testler TESLIM EDILDI ve gecti; kisit BEKLEMEDE.

**KAPI 1 — SIMULASYON (kisit bagli olmadigi icin canli kosu DEGIL).**
Olculen 249 rotanin her birine sozlesme olcutu uygulandi:

                              ROTA     MOLOZA    AGIR   ARENA DISI
    KISIT KAPALI (taban)   249/260     6/249   6/249      10/249
    KISIT ACIK  (T65)      244/260     6/244   6/244       5/244

    ARENA DISI   10 -> 5   DUSTU
    MOLOZA BASMA  6 -> 6   ARTMADI
    ROTA URETIMI 249 -> 244  COKMEDI (-5 kare)
    reddedilen 5 karenin HEPSI gercekten arena disiydi — mesru kayip 0

**KAPI 2 — MUTASYON KONTROLU** (D-15/K-04):

    M0  mutasyon YOK                             18 kosuldu · DUSEN  0  temiz
    M1  tavan pratikte KALDIRILDI (serit x99)    18 kosuldu · DUSEN  6  ATESLENDI
    M2  SERIT_SAYISI 12 (serit_no ile ayristi)   18 kosuldu · DUSEN 18  ATESLENDI
    M3  tavan YARIYA indirildi                   18 kosuldu · DUSEN  6  ATESLENDI
    M4  geri alma sonrasi                        18 kosuldu · DUSEN  0  temiz

M2 madde-16 kilididir: `SERIT_SAYISI` ile `serit_no` birbirinden bagimsiz
kayamaz.

**KAPI 3 — depo kapilari.**

    codes/test_rota_sentetik.py        SONUC: 15/15 dogru            GECTI
    unittest discover -s tests -q      Ran 349 tests · OK            GECTI
    scripts/jetson_paket_hazirla.py    9/9 bayt-esit                 GECTI

**MEVCUT BIR TEST GUNCELLENDI (gizlenmiyor).**
`tests/test_rota_ret_nedenleri.py::test_sebep_kodlari_sozlesmedeki_dokuz_degerdir`
onuncu sebep kodu eklenince dustu. Test dogrudan benim genislettigim sozlesme
kumesini kilitliyor; kume guncellendi ve test adindaki SAYI kaldirildi
(`..._sozlesmede_SAYILANLARDIR`). Ad sayi tasidigi icin her yeni kodda ad da
degismek zorundaydi — T59 denetiminde isaretlenen ciplak-sabit kirilganliginin
ta kendisi. Kume yine TAM kilitli; sessizce buyuyemez.

**DOGRULANAMADI**
  1. Arena basarimi (D-88, KALICI kisit). Bu gorev onu dogrulamaz.
  2. Kisit CANLI kosulmadi — `analyze_path`e baglanmadi (kapsam engeli).
     Yukaridaki KAPI 1 sayilari SIMULASYONDUR.
  3. Kalan 5 arena-disi kare icin olcut YOKTUR.
  4. Tavan v24 + T60 kadraj icin olculdu; model ya da substrat degisirse
     yeniden olculmelidir.
  5. Gercek karede sinir imzalarinin yer gercegi ETIKETI yok; oradaki
     "dogru/yanlis" degerlendirmeleri GOZLEDIR, olculmus hata degildir.

---

### D-96 · DENETIM · T65 dogrulandi; KISIT BAGLANMADI ve sebebi MIMARIN KAPSAM HATASIDIR
Denetleyen: Claude 1 (mimar) · 2026-08-14 · gorev T65 · uygulayan Claude 2

**🔴 ONCE KENDI HATAM.** T65'in dosya izin listesini ben yazdim:
`costmap_path_finder.py · karar_sozlesmesi.py · CONTRACTS.md · tests/**`.
Ama duzeltilecek kusur `codes/rpi_inference.py` icindeki `analyze_path`tadir
ve o dosya listede YOKTU. Claude 2 izni asmadi, isi yaptigi yere kadar
getirdi ve engeli acikca bildirdi — **dogru davranis budur**. Bu, T35'te
yaptigim "yanlis dosyayi hedef gosterme" hatasinin AYNISIDIR (D-50); ikinci
kez oldu, bu yuzden kayda geciyor.

**BAGIMSIZ DOGRULAMA — Claude 2'nin betigi kullanilmadi, mimarin kendi
olcum JSON'lari uzerinden sozlesme fonksiyonu cagrilarak tekrarlandi:**

    tavan = icerik_w / SERIT_SAYISI = 640/3 = 213,3 px
    rotali kare        249
    kisit ELEDI          5   -> 5'inin de arena disi orani > %10 (GERCEKTEN kusurlu)
    yanlis elenen        0   <- mesru hicbir kare kaybedilmedi
    kacan kusurlu        5 / 10

Claude 2'nin bildirdigi `10 -> 5` ve `mesru 0/239` rakamlariyla **birebir
ayni**. Sozlesme girdisi `CONTRACTS.md:382` ve `:456`'da mevcut; sebep kodu
`KORIDOR_DEGIL` kanonik listeye eklenmis.

**TASARIM DENETIMI — UCU DE DOGRU.**
  1. **Madde 15**: olcut yalniz REDDEDER; maskeye dokunmaz, serbest alani
     buyutmez. Ihlal yok.
  2. **Madde 16**: tavan `SERIT_SAYISI`'ndan turetiliyor, ciplak sayi degil.
     `KORIDOR_GENISLIK_TAVANI_SERIT = 1.0` **fiziksel** sinirdir.
  3. **Fail-closed yonu dogru**: olculemeyen darbogaz reddi TETIKLEMEZ —
     olcut yalniz POZITIF kanit uzerine ates eder, karar diger kapilara kalir.

**FIT ETMEYI REDDETMESI DOGRU KARARDIR.** 0,280 ile 0,333 arasina konacak bir
tavan 6/10 yakalardi; reddedildi cunku olculen azami (0,280) bozunumu KAPALI
sentetik karelerden gelir ve gercek mesru dagilim daha genistir. Bu tam olarak
**benim D-85'te yaptigim hatadir** (alt kumenin azamisine esik oturtmak, D-86'da
curutuldu). Amele mimarin gecmis hatasini tekrarlamayi reddetti ve gerekcesini
teste kilitledi. Kayda gecer.

**KISMI OLDUGU GIZLENMEDI.** Kacan 5 karenin 4'u mesru azaminin ALTINDA ve
genislikle ayirt EDILEMEZ; `sa_000068`'de arena disi bolge bir OTOPARK
FOTOGRAFI tasiyor ve model orada kendi koridorunu buluyor. Genislik olcutu bu
sinifi yakalayamaz.

**VERDIKT: T65 KABUL — kisit BAGLANMAK UZERE yetkilendirildi.** Uygulama
`codes/rpi_inference.py` icinde `analyze_path`e TEK cagridir; izin listesi
duzeltilerek **T69** olarak acildi. `comms/yks_gui.py` Codex'te (T64),
`rpi_inference.py` bostur — cakisma yok.

**KOSULAN KAPILAR (mimar tarafindan tekrar kosuldu, ameleler calisirken).**

    codes/test_rota_sentetik.py        SONUC: 15/15 dogru        GECTI
    unittest discover -s tests -q      Ran 349 · OK              GECTI
                                       (322 -> 349: +27 test)

**DOGRULANAMADI**
  1. Kisit CANLI kosulmadi; yukaridaki sayilar SIMULASYONDUR. T69 bittiginde
     `61_rota_moloza_basma.py` ile canli olculmelidir.
  2. Claude 2'nin "sentetik sayilar iyimser ust sinirdir" uyarisi (uretec
     kadraj kipinde bozunumu kapatiyor) DOGRUDUR ve mimarin D-90/D-95
     olcumlerinin tamamina da uygulanir. D-95'e islendi.

---

### D-97 · UYGULANDI · T69: T65 kisiti karar yoluna baglandi; CANLI olcum simulasyonu dogruladi
Uygulayan: Claude 2 · 2026-08-14 · gorev T69 · kanit D-94, D-96

**YAPILAN.** `codes/rpi_inference.py` `analyze_path` icinde, darbogaz olculdukten
ve `olcum` tamamlandiktan SONRA tek cagri:

    kg_reddi = rota_koridor_genisligi_reddi(olcum["darbogaz_px"], icerik_w)
    if kg_reddi is not None:
        return _don(None, 0.0, [], clean, kg_reddi, olcum)

Import iki blogun IKISINE de eklendi (goreli `.karar_sozlesmesi` ve mutlak),
yoksa paket-ici ve depo-ici calisma ayrisirdi. Esige DOKUNULMADI (1.0),
`karar_sozlesmesi.py` DEGISTIRILMEDI, `comms/` DEGISTIRILMEDI.

**KAPI 1 — CANLI OLCUM (simulasyon DEGIL).**
`61_rota_moloza_basma.py --model navitas_seg_v24_best.pt --kume ..._t60`

                              ROTA     MOLOZA    AGIR   ARENA DISI
    taban  (D-90/D-94)     249/260     6/249   6/249      10/249
    T69    (kisit CANLI)   244/260     6/244   6/244       5/244

    ARENA DISI   10 -> 5   DUSTU        (hedef: 5)
    MOLOZA BASMA  6 -> 6   ARTMADI      (hedef: artmasin)
    ROTA URETIMI      244  COKMEDI      (hedef: 244'un altina dusmesin)

**D-94'un SIMULASYONU BIREBIR DOGRULANDI** — uc sayi da tuttu. Simulasyonun
kendisi de boylece gecerli bir yontem oldugu icin kayda gecer.

**KAPI 2 — MUTASYON KONTROLU (canli, ayni olcum betigi).**

    M0  kisit ACIK (depo hali)                rota 244 · moloza 6 · arena disi  5
    M1  kisit KAPATILDI (fonksiyon None)      rota 249 · moloza 6 · arena disi 10
    M2  geri alma sonrasi                     rota 244 · moloza 6 · arena disi  5

Kisit kapatilinca sayilar TABANA TAM DONDU (249/6/10). Dusus baska bir
kapinin yan etkisi degil, KISITTAN geliyor. Depo dosyasi degistirilmedi;
fonksiyon bellekte yamalandi.

**KAPI 3 — depo kapilari.**

    codes/test_rota_sentetik.py        SONUC: 15/15 dogru            GECTI
    unittest discover -s tests -q      Ran 359 tests · OK            GECTI
    scripts/jetson_paket_hazirla.py    9/9 bayt-esit                 GECTI

**YENI TEST SINIFI** `tests/test_koridor_genisligi.py::AnalyzePathEntegrasyonTests`
(7 test) BAGLANTIYI kilitler — cagri silinirse duser. Icerik: fikstur
onkontrolu (kor kapi kurmamak icin ZEMIN kapisina takilmadigi dogrulanir) ·
asiri genis koridorun `KORIDOR_DEGIL` ile reddi · fail-closed (yol/guven/
waypoint YAYINLANMAZ) · negatif kontrol (makul koridor ETKILENMEZ) ·
madde 15 (maskeye dokunulmuyor) · olcut sozlesmeden cagriliyor mu (kimlik
karsilastirmasi) · kisit kapatilinca ayni kare GECIYOR mu. Toplam 25 test.

**🔴 BULGU — T65'IN GEREKCESI YANLIS IFADE EDILMIS (esik DOGRU, ANLATIM yanlis).**
Baglarken `darbogaz_px`in ne oldugu dogrulandi: `_rota_serit_olcumu` docstring
`:492` **"rota boyunca olculen en kucuk aciklik (dt YARICAPI)"** diyor. Yani
`darbogaz_px` bir YARICAPTIR, koridor GENISLIGI degil (genislik ~ 2x).

Oysa T65'in gerekcesi (`karar_sozlesmesi.py` yorumu ve `CONTRACTS.md` SS6.4
satiri) sunu diyor: *"koridorun en dar yeri BIR SERIDIN TAMAMINDAN genis
olamaz"*. Uygulanan kural `yaricap > icerik_w/3` oldugu icin fiilen sunu
soyluyor: **koridor GENISLIGI IKI seritten genis olamaz.** Anlatim iki kat
sapiyor.

OLCULDU (ayni kume, n=249):

    kural                              esik oran   yanlis elenen MESRU   yakalanan
    UYGULANAN  yaricap > 1/3               0.333            0/239          5/10
    LAFZI      genislik > 1/3 (yar>1/6)    0.167           23/239          7/10

Yani **lafzi "bir serit" kurali UYGULANAMAZ** — 23 mesru kareyi elerdi.
Uygulanan esik dogru muhendislik secimidir ve olculen paylari korur; yanlis
olan yalnizca ANLATIMDIR.

Altta yatan olgu da kayda deger: bu kumede MESRU koridorlar genislik olarak
`0.559 * icerik_w`e, yani ~1,7 seride kadar cikiyor. "Uc guzergah molozla
ayrilir" resmi T60 geometrisinde SIKI tutmuyor — D-91'in "uretec dikey
seritler uretiyor, gercek arena ise moloz ADALARI" bulgusuyla tutarli.

⚠ **DUZELTILMEDI.** T69'un izin listesi `codes/rpi_inference.py` ve `tests/**`
ile sinirli; `karar_sozlesmesi.py` ve `CONTRACTS.md` acikca DOKUNMA listesinde
("T65 bitti"). Esik de OYNATILMADI (gorev acikca yasakladi ve gerekcesi teste
kilitli). Duzeltilmesi gereken **yalniz iki cumledir**:
  1. `codes/karar_sozlesmesi.py` T65 yorum blogu — "bir seridin tamamindan"
     ifadesi "iki seritten" ya da "yaricapi bir serit genisligini asan" olmali.
  2. `CONTRACTS.md` SS6.4 `KORIDOR_DEGIL` satiri — ayni duzeltme.
Sayilar, esik ve testler DEGISMEZ; yalniz ifade duzelir.

**DOGRULANAMADI**
  1. Arena basarimi (D-88, KALICI kisit). Bu gorev onu dogrulamaz.
  2. Kalan 5 arena-disi kare hala geciyor; genislikle ayirt EDILEMEZLER
     (D-94: `sa_000068` arena disinda otopark fotografi tasiyor). Olcut YOK.
  3. Olcum yalniz T60 kadraj kumesi ve v24 icindir. Gercek karede kisitin
     etkisi OLCULMEDI — `sartname_s9_arena.png` uretim yolunda zaten
     `OLCEK_YOK` ile duruyor (D-90 bulgu 5), rota yayinlanmiyor.
  4. Guven olcutunun DOYMUS oldugu (D-94 yan bulgusu) bu gorevde ele
     ALINMADI; 22,4 px ustunde tum darbogazlar hala guven 1.000 veriyor.

---

### D-98 · 🔴 GOREV KRITIK · Olcek halkasi SABIT bir baslangic sayisina bagli; irtifa sapmasi GOVDE ACIKLIGINI EKSIK hesapliyor
Olcen: Claude 1 (mimar) · 2026-08-14 · `codes/rpi_inference.py:1230-1250`, `scripts/saha_kuru_kosu.py:210-390`

**DURUM.** `mpp_irtifadan(irtifa_m, W_px, yatay_fov_derece|odak_px)` sozlesmede
UYGULANMIS ve `codes/rpi_inference.py:1244`ten cagriliyor. Ancak girdisi
**`--irtifa` komut satiri argumanidir** — uctan uca TEK BIR SAYI, calisma
basinda elle verilir. Algi yolunda MAVLink okuyan hicbir kod YOKTUR:
`rpi_inference.py`deki tek MAVLink izi bir YORUM satiridir (`:1224`).
`comms/inis_kaniti.py` `GLOBAL_POSITION_INT` okur ama yalniz INIS KANITI icin;
olcege baglanmaz.

**🔴 KAPI YANLIS SEYI OLCUYOR.** `scripts/saha_kuru_kosu.py` "olcek" halkasi
AST ile *irtifa/FOV parametresi alan ve mpp donduren bir fonksiyon* arar ve
bulunca **GECTI** yazar (`:387-390`). Betigin kendi yorumu ise durumu dogru
tarif eder (`:380`): *"Bu halka SAHIPSIZ cunku sahada mpp ureten hicbir kod
yok."* Yani kapi FONKSIYONUN VARLIGINI olcuyor, BESLENDIGINI degil. Halka
"GECTI" gorunurken fiilen sahipsizdir.

**ETKI YONU OLCULDU — tehlikeli taraf net.** `r_gerekli_px = R_GEREKLI_M / mpp`
ve `mpp = 2*h*tan(FOV/2)/W`. Varsayilan irtifa gercekten BUYUKSE mpp buyur,
`r_gerekli_px` KUCULUR, yani govde acikligi EKSIK istenir:

    R_GEREKLI_M=1,10 · W=640 px · FOV=60 derece
    gercek h  varsayilan h   gercek r_px  hesaplanan r_px    hata
          30            30          20,3             20,3    +0,0%   guvenli
          30            40          20,3             15,2   -25,0%   🔴 TEHLIKELI
          30            50          20,3             12,2   -40,0%   🔴 TEHLIKELI
          40            30          15,2             20,3   +33,3%   guvenli (fazla temkinli)
          50            30          12,2             20,3   +66,7%   guvenli (fazla temkinli)

30 m'de ucarken 50 m yazilmissa IKA, govdesinin gerektirdiginden **%40 dar**
geciteren gecirilir. Sartname SS5.3.2 asgari irtifa 30 m'dir; ucus sirasinda
irtifa SABIT KALMAZ ve tek sayi butun kosuya uygulanir.

**IKI AYRI KUSUR.**
  1. **Canlilik yok** — irtifa kare kare guncellenmiyor.
  2. **Yanlis girdi yakalanmiyor** — elle yazilan sayi makul bantta
     (`SARTNAME_ASGARI_IRTIFA_M`..`IRTIFA_MAKUL_UST_M`) oldugu surece,
     gercekle ilgisiz olsa bile kabul edilir. Makullik kapisi vardir, DOGRULUK
     kapisi yoktur.

**DOGRU DAVRANIS (madde 15 ruhu).** Telemetri yoksa ya da BAYATSA dogru cevap
son bilinen sayiyi kullanmak degil, `OLCEK_YOK` ile CEKIMSER kalmaktir.
Cekimserlik gorevi durdurur ama IKA'yi carptirmaz; bayat olcek carptirir.

**DOGRULANAMADI**
  1. Yarisma ucusunda irtifanin ne kadar saptigi bilinmiyor; %25-40 hata
     ornekleri VARSAYIMSAL irtifa farklarindan turetildi, olculmus ucus
     verisinden degil.
  2. Jetson/Pixhawk baglantisinin telemetri gecikmesi ve tazelik esigi
     OLCULMEDI; "bayat" tanimi bu gorevde SAYILASTIRILMADI.
  3. Kamera FOV/odak degeri de elle verilir; onun dogrulugu bu kayitta ELE
     ALINMADI — ayni sinifta ikinci bir acik olabilir.

---

### D-99 · 🔴 BUYUK DUZELTME · "Gercek arena karesi" GERCEK DEGIL: sartname figuru YAPAY ZEKA URUNU; D-84/D-87/D-88/D-92/D-95 zinciri yeniden degerlendirildi
Duzelten: Claude 1 (mimar) · 2026-08-14 · kaynak `Ileri_Otonom_Sistemler_..._Sartname_TR_Ltktw.pdf` s.8 · **kullanici uyarisi uzerine**

**KULLANICI SORDU, BEN SORMAMISTIM.** Kullanici "sartnamede bize arac
vermeyecekler ki, sartnameyi incele" dedi. Sartname metni okundu ve Sekil 1'in
ALT YAZISI bulundu:

> *"Yarisma alani ve operasyonel cevre **ornek** gorseli (Gorsel **tamamen yapay
> zeka ile olusturulmustur. Gercek alani dogrudan yansitmamaktadir.**)"*

Yani `data/arena_referans/sartname_s9_arena.png` — D-84'ten beri "projenin
sahip oldugu TEK GERCEK arena goruntusu" diye uzerine olcum kurdugum kare —
**gercek arena degildir; yapay zeka ile uretilmis bir ILLUSTRASYONDUR.**

D-87 bunu "DOGRULANAMADI 1" olarak isaretlemisti ("figurun gercek arenayi mi
temsili bir gorseli mi gosterdigi bilinmiyor"). Cevap sartnamenin KENDI
sayfasindaydi ve **ben o sayfayi okumadan figuru cikarip kullanmaya
basladim**. Bu, D-53'un ("olcum zeminine bak") tekrarindan baskasi degildir.

**ETKILENEN KAYITLAR — silinmiyor, GECERLILIK ALANI daraltiliyor.**

    kayit   iddia                                    yeni durum
    D-84    "GERCEK arena karesi bulundu"            YANLIS ADLANDIRMA. Kare bir
                                                     illustrasyondur. v21'in orada
                                                     kor oldugu OLCUMU gecerlidir,
                                                     ama "gercek arenada kor" DEGIL.
    D-87    renk kunyesi (L/a/b hedefleri)           YAPAY ZEKA URETIMI bir goruntunun
                                                     kunyesidir. GERCEK arenanin
                                                     renk hedefi DEGILDIR.
    D-88    "tek gercek kare, ikincisi gelmeyecek"   Duzeltilir: elimizde HIC gercek
                                                     arena goruntusu YOK. Kisit
                                                     GERCEKTE DAHA AGIR.
    D-92    "gercek arenada rota bariyeri kesiyor"   Illustrasyonda kesiyor. Bariyerin
                                                     GORUNUMU uydurmadir; ama sartname
                                                     metni guzergahlarin "fiziki
                                                     engellerle" kapatildigini SOYLER,
                                                     yani ince-engel riski GERCEKTIR.
    D-95    "v25 GERCEK ARENADA kor -> uretime        Karar AYAKTA ama GEREKCESI ZAYIF.
            girmiyor"                                 Olcut bir illustrasyondu.
                                                      Yeniden gerekcelendirildi (asagida).

**D-95 KARARI NEDEN AYAKTA KALIYOR (yeni gerekce).** v25'in reddi artik
"gercek arenada kor" diye savunulamaz. Ancak su ayakta: v25, ustten bakisli,
molozlu, izgarali, dusuk kromali bir sahnede `conf=0.02`'ye kadar SIFIR zemin
uretip sahneyi butunuyle ENGEL ilan ediyor. Bu, EGITIM DAGILIMINA yakin ama
ayni olmayan bir goruntude tam cokme demektir ve yarisma gunu gercek arena da
egitim dagilimimizin disinda olacaktir. Karar **kirilganlik** gerekcesiyle
korunur, "gercek alan" gerekcesiyle degil. v24 uretimde kalir.

**SARTNAME METNI — FIGURLE CELISEN UC NOKTA. ARTIK METIN OTORITEDIR.**
Figur "gercek alani yansitmiyor" diye ILAN EDILDIGI icin, figur ile metin
celistiginde **metin kazanir**. D-87'nin "figur kazanir" hukmu TERSINE DONER:

  1. **HB KIRMIZIDIR.** SS2.1: *"2 metre x 2 metre boyutlarinda uzerinde
     **kirmizi H harfi** bulunacagi bir bolgedir."* D-87 bulgu 3a (figurden
     "kroma sifir, siyah ped + beyaz H") **GECERSIZDIR**. T56'da koydurdugum
     kirmizi branda DOGRUYDU; T60'ta figure gore siyah/beyaz yaptirmam
     HATADIR ve geri alinmalidir (T71).
  2. **IHA-IB 30x30 m MAVI bolge GERCEKTIR.** SS2.1 acikca tanimliyor. T60'ta
     "figurde yok" diye kapsam disi biraktim; gerekce cokmustur (T71).
  3. **GUZERGAHLAR MOLOZ YIGINLARI ARASINDADIR.** SS2.1: *"moloz yiginlari
     arasinda olusturulmus uc (3) adet farkli yol"* ve kapali olanlar
     *"fiziki engellerle kapatilacaktir"*. Bu, T66'nin "dikey seritler degil,
     moloz ADALARI" tespitini SARTNAME DUZEYINDE dogrular.

**KULLANICININ ASIL NOKTASI DOGRUDUR — SARTNAMEDE ARAC YOKTUR.** Engel kumesi
metinde "moloz yiginlari ve engeller" / "fiziki engeller"dir. v24'un `blocked`
sinifinin pratikte bir ARAC ayirici olmasi (asagida olculdu) yarisma acisindan
**degersizdir**.

**OLCUM — `blocked` sinifi alan degistirince susuyor:**

    kaynak                  n   zemin%   ENGEL%   engel/zemin
    sartname figuru         1     34,6      0,5        0,015
    raw_frames (otopark)    8     43,6     14,1        0,324   <- araclar
    copy_paste_gercek       8     44,8     12,8        0,286
    sentetik_arena val      8     26,0     22,8        0,877

    T60 kadraj, YER GERCEGI moloz bolgelerinde (n=79):
      ENGEL sinifi engel diyor        %95,4  (medyan %98,3)
      ZEMIN disi birakiyor            %95,2  (medyan %99,1)

Yani `blocked` SENTETIKTE calisiyor, GERCEK fotografta yalniz araclarda
atesliyor. Sozlesmede v21 icin zaten yazili olan not (`karar_sozlesmesi.py:342`
*"pratikte arac mi degil mi ayiricisidir"*) v24'te de gecerlidir.

**🔴 ASIL TEHLIKE — ZEMIN SINIFI GERCEK MOLOZU ZEMIN SANIYOR.** Figur uzerinde,
D-87 renk kunyesiyle kurulan MODELDEN BAGIMSIZ kahinle:

    moloz-renkli bolgede (kare'nin %9,9'u)
      model ZEMIN diyor        %37,9   <- TEHLIKELI yon
      model ENGEL diyor        % 5,9
      hicbiri ("zemin degil")  %57,0   <- bizi yalnizca DEGISMEZ koruyor

Emniyet agi (Katman 2) gercek goruntude fiilen YOKTUR; koruma tamamen
Katman 1'in "zemin degil -> engel" varsayilanina kalmistir ve o da molozun
%37,9'unda yaniliyor.

**DOGRULANAMADI**
  1. Gercek yarisma arenasinin gorunumu HAKKINDA HICBIR SEY BILMIYORUZ. Elde
     tek bir gercek goruntu yoktur. D-88'in kisiti daralmadi, AGIRLASTI.
  2. Figurun YAPISAL bilgisi (uc guzergah, moloz, bariyer, izgara, H pedi)
     sartname METNIYLE ortusen kismi icin yol gostericidir; RENK, DOKU ve
     GEOMETRI bilgisi ise uydurmadir ve olcum hedefi olarak KULLANILAMAZ.
  3. `blocked` sinifinin gercek arenada ne yapacagi OLCULEMEZ — gercek kare
     yok. Yukaridaki tablo yalniz eldeki alanlar icindir.

---

### D-100 · UYGULANDI · T67: KATMAN 2 ince bariyer dedektoru; kesisim 59 -> 0 px, HB KORUNDU
Uygulayan: Claude 2 · 2026-08-14 · gorev T67 · kanit D-92, D-93 · ⚠ zemin duzeltmesi D-99

**YAPILAN.** `karar_sozlesmesi.ince_bariyer_maskesi()` (KATMAN 2 klasik
dedektor) + `rpi_inference.get_masks` icinde tek cagri. Dedektor ENGEL
katmanina EKLER; serbest alan (`zemin AND NOT engel`) yalniz KUCULUR — madde 15
ve CONTRACTS SS2 monotonluk sozlesmesi korunur. `comms/` DEGISTIRILMEDI.

**REFERANS KOPYALANMADI, ORANA CEVRILDI.** `63_bariyer_kesisimi.py` ciplak
piksel kullaniyordu (cekirdek 61x5 · alan 300 · genislik 60) ve 1059 genisligindeki
KAYNAK karede kalibreydi. Uretim zincirinde tespit `small` (512x512) uzerinde
yapilir — orada o sabitler KISA KOLU KACIRIYOR (w=47 < 60). Olculdu:

    cozunurluk        kol    w/W (kisa · uzun)   en/boy (kisa · uzun)
    KAYNAK 1059x634    2     0,093 · 0,215       7,0 · 14,2
    sq     1059x1059   2     0,093 · 0,215       7,0 · 14,2
    small   512x512    2     0,092 · 0,215       6,7 · 13,8

Oranlar olcekten BAGIMSIZ. 512 tabanli maske KAYNAK maskesinin %91,1'ini
kapsiyor (IoU 0,850) — engel katmani icin yeterlidir.

`get_masks` ayrica `r.masks is None` dalinda da calisacak sekilde yeniden
duzenlendi: model hicbir sey gormese bile bariyer engeldir. Eskiden orada
ERKEN DONULUYORDU.

**KAPI 1 — GERCEK OLCUM (`63_bariyer_kesisimi.py`).**

                              taban (D-92)      T67
    model ENGEL diyor           %0,0           %91,1
    ROTA x BARIYER kesisimi     59 px          0 px      GECTI

Gorsel dogrulandi (`results/t63/bariyer_kesisim.png`): iki kol da sari
isaretli, rota hicbirine degmiyor. ⚠ Rota artik arenanin SOL KENARINA kaymis
ve guven 0,216 (esik 0,20). Kesisim 0'dir ama bu "iyi rota" demek DEGILDIR;
T65'in cozemedigi arena-siniri sinifina yakindir.

**KAPI 2 — HB PEDI ENGEL SAYILMIYOR (uc ayri kanit).**

  A. Gercek(!) karede HB bolgesi: a* min -6 · maks 4 -> 0/3100 engel pikseli.
     ⚠ ZAYIF kanit: o figurde HB zaten siyah/beyaz.
  B. SENTETIK KIRMIZI HB (sartname METNINE sadik en kotu durum), a* = 65:
     64x64 kare -> 0 engel pikseli KORUNDU
     ayni karede 240x14 bariyer -> 3360 piksel YAKALANDI  (POZITIF KONTROL,
     D-15/K-04: "hicbir sey bulamiyor" hali basari sayilamaz)
  C. Sekil supurmesi — sinir tam en/boy 4,0'da:
       64x64 (1,0) · 128x128 (1,0) · 100x40 (2,5) · 100x25 (4,0) -> ENGEL DEGIL
       100x24 (4,2) · 200x49 (4,1) · 240x14 (17,1)               -> ENGEL

**KAPI 3 — REGRESYON (`61_rota_moloza_basma.py`, v24 · kadraj_t60).**

                          ROTA     MOLOZA    AGIR   ARENA DISI
    taban (T69)        244/260     6/244   6/244      5/244
    T67                242/260     4/242   2/242      5/242

Rota uretimi COKMEDI (-2). Moloza basma ARTMADI, **AZALDI** (6 -> 4; agir
basma 6 -> 2; basma orani ort %1,86 -> %0,54). Sebep: kadraj bariyerleri de
gercek engeldir ve model onlari da kaciriyordu.

**KAPI 4 — MUTASYON KONTROLU (canli, iki olcum birden).**

    M0  dedektor ACIK      kesisim   0 px · ENGEL %91,1 | rota 242 · moloza 4
    M1  dedektor KAPALI    kesisim  59 px · ENGEL % 0,0 | rota 244 · moloza 6
    M2  geri alma          kesisim   0 px · ENGEL %91,1

Her iki olcum de TAM TABANA dondu. Degisim dedektordendir.

**KAPI 5 — depo kapilari.**

    codes/test_rota_sentetik.py     SONUC: 15/15 dogru              GECTI
    unittest discover -s tests -q   Ran 406 · FAILED (failures=1)   asagi bak
    scripts/jetson_paket_hazirla.py 9/9 bayt-esit                   GECTI

⚠ **TEK DUSEN TEST BENIM DEGIL.** `test_costmap_icerik_cagri_yerleri.py::
test_kuru_kosu_ana_maskeyi_baglar_kirpigi_baglamaz` — dedektor KAPATILIP
kosuldugunda da DUSUYOR. Sebep baska bir ajanin esZAMANLI calismasi:
`scripts/saha_kuru_kosu.py` calisma agacinda degistirilmis ve `halka_rota`
imzasi degismis (`mpp` eklenmis), test eski imzayla cagiriyor. `scripts/`
T67'nin izin listesinde YOK; DOKUNULMADI, duzeltilmedi.

**DEDEKTOR ISABETI — sentetik kumede BAGIMSIZ olculdu** (T60 kadraj n=260,
model KULLANILMADAN, yer gercegi manifest `bariyerler` kutulari):

    bariyer tasiyan kare        210 · bariyer yok 50
    bariyer BULUNAN             153/210
    KACIRILAN                    57/210
      -> 54'unde bariyer kutusunda HIC yuksek-kroma piksel YOK
         (bariyer moloz ALTINDA, goruntude gorunmuyor — dedektorun suclu
          oldugu bir kacirma DEGIL)
      -> 3'unde kroma VAR, sekil filtresi eledi   <- GERCEK kacirma (%1,4)
    GORUNUR bariyerlerde isabet: 153/156 = %98,1

    tespit pikselinin bariyer kutusu icinde kalani: medyan %92,1 · p10 %84,0
    kutu disina tasan tespit: 144/260 karede (medyan 170 px)
      -> tasan pikselin %90,5'i arena ICINDE (kolun pencereyi biraz asmasi)
      -> %9,5'i arena DISINDA (alan disi fotograflardaki kirmizi nesneler)

**🔴 D-99 ZEMINI DEGISTIRDI — bu gorev onunla birlikte okunmalidir.**
Mimar ben calisirken D-99'u yazdi: `sartname_s9_arena.png` GERCEK ARENA
DEGILDIR, sartname Sekil 1 alt yazisina gore "tamamen yapay zeka ile
olusturulmustur". Bunun T67'ye UC etkisi var ve ucu de kayda gecirildi
(`CONTRACTS` SS2.1 ve sabit yorumu D-99'a gore DUZELTILDI):

  1. **Dedektorun RENK ANAHTARI yapay bir goruntuden kalibre edilmistir.**
     Bariyerin kirmizi-beyaz gorunumu UYDURMADIR. Gercek arenada fiziki
     engeller kirmizi OLMAYABILIR; o durumda dedektor HIC ATESLEMEZ.
     ⚠ Bu FAIL-SAFE'tir: hicbir sey eklenmez, hicbir sey cikarilmaz, sistem
     T67 oncesi davranisa doner. Yani D-99 bu isi GERI ALDIRMAZ, yalniz
     GECERLILIK ALANINI daraltir.
  2. **AYAKTA KALAN GEREKCE:** sartname METNI (SS2.1) kapali guzergahlarin
     "fiziki engellerle kapatilacagini" soyler. Ince-engel riski GERCEKTIR;
     bilinmeyen yalniz GORUNUMDUR.
  3. **TUZAK KESINLESTI, HAFIFLEMEDI.** Figur yapay oldugu icin artik METIN
     OTORITEDIR ve metin (SS2.1) hedefi "uzerinde KIRMIZI H harfi bulunacagi
     bir bolge" diye tanimlar. Yani HB GERCEKTEN KIRMIZIDIR ve naif bir
     "kirmizi = engel" kurali P_gorev'i sifirlardi. Bu isin en tasiyici
     kaniti, KAPI 2-B'deki SENTETIK KIRMIZI HB testidir — gercek(!) karedeki
     siyah/beyaz ped kanit olarak artik BASLI BASINA YETERSIZDIR.

**YENI TEST PAKETI** `tests/test_ince_bariyer.py` (18 test): sozlesme kaynagi
(`BARIYER_ENGEL_SINIFI == sinif_semasi.ENGEL` kilidi — `sinif_semasi` Jetson
paketinde YOK, import EDILEMEZ) · hedef korumasi (kirmizi kare 4 boyutta,
pozitif kontrol, esik sinirlari) · figur karesi olcumleri (2 kol, 3644 px,
HB/IHA/IKA engel sayilmaz) · cozunurluk bagimsizligi (320/640/1280) ·
fail-safe · `get_masks` entegrasyonu (model bos donunce de calisir, madde 15
monotonlugu, goruntu yoksa sessizce atlar, ENGEL sinifi istenmemisse dokunmaz).

**DOGRULANAMADI**
  1. GERCEK arena basarimi. Elimizde gercek arena goruntusu **YOKTUR** (D-99).
     "Bariyer sorunu cozuldu" genel bir iddia DEGILDIR.
  2. Gercek fiziki engellerin RENGI bilinmiyor; kroma anahtari orada
     calismayabilir. Yedek bir imza (or. dogrusal yapi / golge) ARANMADI.
  3. Bariyerin fiziksel YUKSEKLIGI ve IKA'nin altindan gecip gecemeyecegi
     bilinmiyor (D-92/2'den devam). Fail-safe varsayim: gecilemez.
  4. Ince-engel sinifinin genel cozumu (tel, halat, kablo) ELE ALINMADI.
  5. Gercek(!) karede rota simdi arena SOL KENARINA kayiyor ve guven 0,216 —
     bariyer kusuru cozuldu ama o rotanin KALITESI dogrulanmadi.

---

### D-101 · UYGULANDI · T71: sartname METNI otoriteye alindi; HB KIRMIZI H, IHA-IB eklendi, renk TEK NOKTADAN GENIS BANDA
Uygulayan: Claude 2 · 2026-08-14 · gorev T71 · kanit D-99 · dosya `51_sentetik_arena.py`

**KAPSAM — UC MADDEDEN IKISI YAPILDI, UCUNCUSU BILEREK BIRAKILDI.**
  1. HB KIRMIZI          -> YAPILDI
  2. IHA-IB 30x30 MAVI   -> YAPILDI
  3. Guzergahlar moloz ADALARI arasinda -> **YAPILMADI.** Bu, uretecin serit
     geometrisinin tam yeniden yazimidir (T66) ve tek gorevde yapilirsa T51/T56
     kadraj kapilarini (koridor duzlugu, hedef yerlesimi, kenar 2,000 m) riske
     atardi. Gorev "ikisini birlikte yapabilirsin" diyordu, ZORUNLU degil.
     Kume hala DIKEY SERITLER uretiyor; T66 acik kalir.

**1 · HB — IKI ESKI VARYANT DA YANLISTI.** SS2.1: *"2 metre x 2 metre
boyutlarinda uzerinde KIRMIZI H harfi bulunacagi bir bolgedir."*

    varyant                 kirmizi mi   H harfi var mi   metne uygun mu
    T56 "kirmizi branda"       EVET          HAYIR            HAYIR
    T60 "figur_siyah_beyaz"    HAYIR         EVET             HAYIR
    T71 "metin_kirmizi_H"      EVET          EVET             EVET

Gorev "T56'daki kirmizi branda dogruymus" diyordu; **tam degil** — T56 duz
kirmizi dikdortgendi ve uzerinde H YOKTU. Metin "uzerinde kirmizi H harfi"
diyor, "kirmizi branda" demiyor. Uygulanan: ped uzerine KIRMIZI cerceve +
KIRMIZI H. Ped rengi sartnamede BELIRTILMEMISTIR, bu yuzden cesitlilik
stratejisi geregi bes tondan sahne basina cekilir (beyaz/koyu/gri/haki).
`hedef_varyanti` artik tek deger: `metin_kirmizi_H` (260/260).

**2 · IHA-IB EKLENDI.** SS2.1'deki 30x30 m MAVI parasutle inis alani.
Olcek sozlesmesi `px = m * TUVAL / HTAB_M` -> 480 px (TUVAL 800, HTAB 50 m).
Bu bir ISARETTIR, engel DEGIL: kimlik haritasina DOKUNULMAZ (HB ve izgara ile
ayni muamele) ve YARI SAYDAM tint uygulanir (saydamlik 0,22..0,45) — duz boya
arenanin %36'sinda zemin dokusunu SILERDI. Konum sahne basina degisir
(tuval x 0..312), ton bes maviden cekilir. Manifest: `iha_ib_kutu`,
`iha_ib_kenar_m` (260/260 kayitli).

**3 · RENK STRATEJISI: TEK NOKTA -> GENIS BANT.** Asil degisiklik budur.
ESKIDEN her zemin yuzeyi ve HER moloz kesiti tek sabit LAB noktasina
boyaniyordu (`LAB_ZEMIN_HEDEF` / `LAB_MOLOZ_HEDEF`, D-87'de figurden olculmus).
Iki sebeple gecersiz: (a) D-99 — o figur YAPAY ZEKA urunu; (b) D-95 — v25 tek
kunyeye oturunca ona BAGIMLI oldu ve dagilim disi sahnede coktu.

Artik her sahne kendi hedefini bantlardan ceker (`sahne_renklerini_sec`):

    LAB_ZEMIN_BANDI  L 105..190 · a -3..+7 · b +1..+22
    LAB_MOLOZ_BANDI  a -3..+4 · b -2..+12
    LAB_MOLOZ_DL     25..75    (moloz zeminden KOYU; farkin BUYUKLUGU taranir)

Moloz L'si bagimsiz cekilmez — sahne cozulebilir kalmali.

**KAPI 1 — RENK CESITLILIGI OLCULDU** (kare basi bolge LAB ortalamasi, n=120,
YER GERCEGI etiketleriyle):

    kume    sinif    n    L ort   L std   L araligi   a std   b std
    T60     zemin  120    148,5    6,91    119..170    0,20    0,68
    T60     moloz  118    107,9    4,61     91..121    0,37    0,55
    T71     zemin  120    134,1   21,51     94..189    2,35    5,90
    T71     moloz  119     98,1   24,90     43..148    1,67    3,23

    std kazanci   zemin L x3,1 · a x11,6 · b x8,7
                  moloz L x5,4 · a x4,6  · b x5,8

TEK MODA COKME KONTROLU (L histogrami, 10 kova):

    zemin T60: dolu 5/10  [0,0,0,2,8,83,25,2,0,0]   <- 120'nin 83'u TEK kovada
    zemin T71: dolu 9/10  [0,7,21,29,16,19,17,8,2,1]
    moloz T60: dolu 4/10  [1,21,91,5,0,0,0,0,0,0]
    moloz T71: dolu 6/10  [18,17,15,13,17,4,0,0,0,0]

Tek moda COKME YOK. GECTI.

**KAPI 4 — GOZLE DOGRULAMA (D-80: gorsel kazanir). GECTI.**
Kontak sayfalari uretildi (8 kare, ayni indisler): T60'in sekizi de AYNI sicak
kum zemin + gri moloz; T71'de zemin kum/gri/acik/koyu arasi degisiyor, moloz
tonlari farkli, kirmizi H ve mavi IHA-IB her karede gorunuyor, kirmizi-beyaz
bariyerler yerinde.

**🔴 GORSEL BIR REGRESYON YAKALADI — sayilar yakalamamisti.** Ilk denememde
`banka_yukle`'deki on-boyamayi kaldirdim ama `enkaz_doku` yolunu sahne
hedefine BAGLAMADIM; ham RescueNet dokusu dogrudan basildi ve molozda MAVI
GOKYUZU ve BEYAZ BULUT parcalari cikti — D-78/T60'in cozdugu kusurun geri
donusu. Ilk 12 karelik denemenin GORSELINDE goruldu ve duzeltildi
(`moloz_yigini` icinde `lab_ortalamasini_tasi(..., _SAHNE_MOLOZ_HEDEFI, ...)`).
Bu, "gorsel kazanir" kuralinin somut kazancidir.

**KAPI — T67 CAPRAZ KONTROLU (gorevde istenmedi, ZORUNLUYDU).**
T67 ince bariyer dedektoru yuksek kromali UZUN-INCE yapiyi engel sayar.
KIRMIZI HB tam da o tuzaktir. 12 karede olculdu:

    HB bolgesinde engel pikseli : 0 / 12 kare   KORUNDU
    IHA-IB bolgesinde a*        : -7 .. +9      (bariyer esigi 25 -> MAVI guvenli)

HB'nin en/boy orani 260/260 karede tam **1,00** (KARE); dedektorun sekil
filtresi (en/boy > 4) onu elemez. IKA hedefe ulasabilir.

**KAPI 3 — T51/T56 KADRAJ KAPILARI KORUNDU** (`57_t51_kadraj_kapilari.py`,
n=260; betik DEGISTIRILMEDI, KUME yolu bellekte yamalandi):

    KAPI 1  TAM KAREDE rota            260/260   GECTI (esik >= 130)
    KAPI 3  POZITIF KONTROL            260/260   GECTI
    KAPI 5  T48 kaplama ort %25,9 · maks %64,8 · tavan %67 · ret 0/260
    manifest: hedef 260/260 · hedef_kenar_m 2,0 (260/260) · en/boy 1,00
              hedef_serit != acik_serit  0/260

**🔴 KAPI 2 — REGRESYON: UC SAYININ IKISI KOTULESTI. Gizlenmiyor.**

                          ROTA     MOLOZA    AGIR   ARENA DISI
    T60 kumesi (T67)   242/260     4/242   2/242      5/242
    T71 kumesi         231/260     5/231   4/231     16/231

    rota uretimi  242 -> 231   COKMEDI (%88,8) ama DUSTU
    moloza basma    4 ->   5   ARTTI (+1 kare)      <- hedef "ARTMASIN" idi
    arena disi      5 ->  16   ARTTI (+11 kare)

**BU KIYAS KONTROLLU DEGILDIR ve sayilar bunu dogrudan "kotulesme" olarak
okutmaz.** v24, T60 substratinda (TEK renk kunyesi) egitildi; T71 kumesi
BILEREK o dagilimin DISINDADIR. Yani olculen sey karar zincirinin bozulmasi
degil, **v24'un dagilim disinda daha kirilgan oldugudur** — ki T71'in varlik
sebebi tam olarak bu kirilganligi kirmaktir (D-95). Dogru kiyas T71 uzerinde
EGITILMIS bir modelle yapilir; o T68/sonraki egitimin isidir.
Yine de gorev "moloza basma ARTMASIN" diyordu ve +1 kare ARTTI — kapi
LAFZEN KARSILANMADI, karar kullaniciya birakiliyor.

**DEPO KAPILARI** (depoda hicbir dosya degistirilmedi):

    codes/test_rota_sentetik.py     SONUC: 15/15 dogru        GECTI
    unittest discover -s tests -q   Ran 426 tests · OK        GECTI

**KUME:** `O:\navitas-local-train\calisma\sentetik_arena_kadraj_t71` (260 kare).
T60 kumesi SILINMEDI, kiyas icin duruyor.

**DOGRULANAMADI**
  1. GERCEK arena basarimi. Elimizde gercek arena goruntusu **HIC YOK**
     (D-88 + D-99). Bu gorev onu dogrulamaz ve dogrulayamaz.
  2. Genisletilen bantlarin GERCEK arenayi kapsayip kapsamadigi BILINMIYOR.
     Bant secimi "makul ortu araligi" akil yurutmesidir, OLCUM DEGILDIR —
     olculecek bir gercek kare yok. Dar tutmaktan iyi oldugu D-95'e dayanir.
  3. Cesitliligin MODELE faydasi bu gorevde olculmedi; T71 uzerinde egitim
     kosulmadi. "Model daha saglam olacak" bir ONGORUDUR, bulgu degildir.
  4. Guzergah geometrisi hala DIKEY SERIT (madde 3 yapilmadi, T66 acik).
  5. IHA-IB'nin arena icindeki KONUMU sartnamede tarif edilmiyor; rastgele
     yerlestirildi. Gercekte sabit bir yeri varsa bu YANLIS olur.
  6. dL alt ucunda (olculen min -3) zemin ile moloz neredeyse ayni parlakliga
     gelebiliyor; o karelerin cozulebilirligi ayrica sinanmadi.

---

### D-102 · DENETIM · T71 ve T62 dogrulandi; amele MIMARIN talimatini duzeltti (HB)
Denetleyen: Claude 1 (mimar) · 2026-08-14 · gorevler T71 (Claude 2), T62 (Codex-1)

**T71 — BAGIMSIZ DOGRULANDI.** Renk cesitliligi mimarin kendi betigiyle,
amelenin araci kullanilmadan yeniden olculdu (kare basi bolge LAB ortalamasi,
YER GERCEGI etiketleriyle, n=120):

    kume  sinif    L ort   L std   L araligi   dolu kova (10)
    t60   zemin    148,5    6,91    119..170        5
    t71   zemin    134,1   21,51     94..189        7
    t60   moloz    107,9    4,61     91..121        3
    t71   moloz     98,1   24,90     43..148        7

    cesitlilik kazanci:  zemin L std x3,1 · moloz L std x5,4

Claude 2'nin bildirdigi degerlerle **birebir ayni**. Tek-moda cokme kirildi:
T60'ta 120 karenin 83'u tek kovadaydi. Bu, D-95'te v25'i olduren tek-palet
bagimliliginin dogrudan panzehiridir.

**🔴 AMELE MIMARIN TALIMATINI DUZELTTI — kayda geciyor.** T71 gorevinde
*"T56'daki kirmizi branda dogruymus"* yazmistim. Claude 2 sartname metnini
okuyup **ikisinin de yanlis oldugunu** gosterdi:

    varyant                    kirmizi mi   H harfi   metne uygun
    T56 "kirmizi branda"          EVET       HAYIR       HAYIR
    T60 "figur_siyah_beyaz"       HAYIR      EVET        HAYIR
    T71 "metin_kirmizi_H"         EVET       EVET        EVET

SS2.1 *"uzerinde KIRMIZI H HARFI bulunacagi bir bolgedir"* diyor; "kirmizi
branda" DEMIYOR. Ped rengi sartnamede BELIRTILMEMISTIR, bu yuzden cesitlilik
stratejisi geregi degisken birakilmis. Talimatimi duzeltmesi DOGRUDUR.

**IHA-IB tasarimi da dogru:** 30x30 m mavi alan bir ISARETTIR, engel degil —
kimlik haritasina dokunulmamis ve yari saydam uygulanmis. Duz boya arenanin
%36'sinda zemin dokusunu silerdi.

**T66 BILEREK YAPILMADI ve gerekcesi gecerli:** guzergah geometrisinin
(moloz ADALARI) yeniden yazimi T51/T56 kadraj kapilarini riske atardi. Gorev
"birlikte yapabilirsin" diyordu, ZORUNLU degildi. T66 acik kalir.

**T62 — DOGRULANDI.** `scripts/jetson_fps.py` icinde ciplak surum dizesi
**0** (madde 16 saglandi); varsayilanlar manifest `asil_model_pt`/`asil_model`
ve uretim `conf`undan turetiliyor; Jetson paketi yeniden uretildi.
Eksik TensorRT engine UYDURULMADI: `engine=None` ve konsol/ozet/rapor'da acik
`ATLANDI`. D-89'un "dogrulanamadi-2" maddesi KAPANDI:

    [T62_IMG] manifest=[640] varsayilan=[640,512] uretim_INFER_SIZE=512 hizali=True
    [T62_FARK] 640/512 dogrusal=1,25 · piksel alani=1,56

Yani 640'lik olcum uretimin GERCEKTEN yaptigi isten %56 daha agir bir isi
olcuyordu; artik 512 uretimle ayni oldugu KAYITLI.

**KOSULAN KAPILAR.** `codes/test_rota_sentetik.py` 15/15 ·
`unittest discover -s tests -q` **Ran 426 · OK** · Jetson paketi yenilendi.

**VERDIKT: T71 ve T62 KAPANIR.**

**DOGRULANAMADI**
  1. T71'in KARAR duzeyindeki etkisi henuz olculmedi — yeni substratla model
     egitilmedi. v26 kosusu baslatildi; sonuc gelene kadar "cesitlilik
     kirilganligi cozdu" DENEMEZ.
  2. Geometri (T66) acik; kume hala dikey seritler uretiyor.
  3. T62 karar zincirinde degildir; Jetson'da hicbir olcum hala YOK.

---

### D-103 · UYGULANDI + KAPI DUSTU · T66: geometri DIKEY SERIT -> MOLOZ ADALARI; T68 birlesik; moloza basma kapisi DUSTU
Uygulayan: Claude 2 · 2026-08-14 · gorev T66 (+T68) · kanit D-91, D-99, D-101 · dosya `51_sentetik_arena.py`

**YAPILAN.** Uretec artik kareyi bastan sona DIKEY SERITLERE bolmuyor. Arena
zemini GENIS ve BAGLANTILI; moloz ADALAR halinde uzerine yerlesiyor; koridorlar
adalarin arasindan geciyor (SS2.1: *"moloz yiginlari arasinda olusturulmus uc
farkli yol"*). T68 birlestirildi: bariyer artik ACIK koridoru kapatabiliyor,
kendi pikselleri `blocked` etiketleniyor ve manifest bunu yansitiyor.
T71 kazanimlari (renk bandi, KIRMIZI H'li HB, IHA-IB) KORUNDU.

**🔴 ONCE BULUNAN ONCEKI KUSUR — `etiketle` DELIKLERI ATIYORDU.**
Eski kod `cv2.RETR_EXTERNAL` kullaniyordu. Serit geometrisinde bedeli kucuktu
ve OLCULDU: T71 kumesinde **260 karenin 65'inde** class-0 ile class-1
poligonlari ust uste biniyordu (cakisan alan traversable'in medyan %0,7'si) —
"dar" seridin ic izi hem gecilebilir hem engel etiketliydi.
ADA geometrisinde ayni kusur **YIKICI** olurdu: zemin, ortasinda ada DELIKLERI
olan genis bir bolgedir; delikler atilirsa **HER ADA "traversable" etiketlenir**
ve yer gercegi tam tersini soyler.
Cozum `delikli_poligonlar`: her delik dis halkaya en yakin kose ciftinden bir
YARIK ile baglanir, sonuc tek basit poligondur. Sinandi: tek merkezi delik ve
uc ada icin yeniden rasterize IoU **1,0000 · fark 0 px**.

**ADA YOGUNLUGU IKI KEZ OLCUMLE AYARLANDI (v16 dersi geri gelmesin).**
Kod icindeki v16 dersi: ETIKETSIZ moloz modele "genis bolge = gecilebilir"
onyargisi ogretmisti. Burada etiketsiz moloz YOK, ama IKINCI bir yoldan ayni
riske girildi ve olcumle yakalandi:

    surum        traversable   blocked   trav/blok
    T71 (serit)      %24,9      %30,9       0,81
    T66 ilk deneme   %53,9       %5,4      10,00   <- adalar cok seyrek
    T66 v3           %31,4      %29,2       1,10
    T66 nihai        %33,7      %29,0       1,16

Artisin bir kismi YAPISALDIR ve DOGRUDUR: seritler artik BITISIK, aralarindaki
`duvar_kal * 1.5` genisligindeki ETIKETSIZ bosluk kalkti (T65'in sikayet
ettigi etiketsiz zemin azaldi).

**KAPI 2 — RENK CESITLILIGI.** Iki duzeyde raporlanir cunku ikisi ayni seyi
olcmez:

    olcut                        T71     T66   oran
    URETEC cekilisi zemin L    24,68   24,28   0,98
    URETEC cekilisi zemin a     2,97    2,85   0,96
    URETEC cekilisi zemin b     6,18    8,71   1,41
    URETEC cekilisi moloz L    29,59   28,52   0,96
    OLCULEN bolge zemin L      21,51   19,45   0,90
    OLCULEN bolge zemin b       5,90    7,02   1,19
    OLCULEN bolge moloz L      24,90   24,20   0,97

**L ve a bantlari KODDA HIC DEGISMEDI**; olculen 0,96-0,98 farki n=260'ta
ORNEKLEME GURULTUSUDUR (uniform(105,190) teorik std 24,54; T71 24,68 · T66
24,28 — ikisi de bandin kendi std'sinin ~1 standart hatasi icinde).
`b` bandi ise GERCEKTEN genisletildi (+1..+22 -> -1..+28, cekilis std x1,41).
"Olculen bolge" std'sinin bir miktar dusmesi BILESIM etkisidir: traversable
bolge artik IKI yuzeyi birden kapsiyor (koridor izi + serit zemini), bolge
ORTALAMASI ortalamaya regresyon yapiyor.
**VERDIKT: uretec cesitliligi DUSMEDI; b'de ARTTI.** Ham "olculen bolge std"
olcutune bakilirsa L'de %10 dusus gorunur — o rakami kovalayip bandi daha da
genisletmek bir OLCUM ARTEFAKTINA fit etmek olurdu, yapilmadi.

**KAPI 3 — BARIYER ARTIK ACIK KORIDORU KAPATIYOR (T68). GECTI.**
D-93 olcmustu: uretec bariyeri YALNIZ zaten kapali seritlere koyuyordu, acik
zemin ustundeki bariyer orani **%0,0** idi ve model bu ornegi HIC gormuyordu.

    olcut                                    T71        T66
    ACIK/DAR seridi bariyerle kapatilan     0/260     128/260  (%49,2)
    serit durumlari                     acik 340    acik 270 · acik+bariyer  77
                                         dar 180     dar  96 · dar+bariyer   96
    bariyer pikseli `blocked` etiketli      %92,0      %98,8

Manifest duzeltmesi de baglandi: bariyerle kapanan seridin `gecilebilir` alani
False'a cevrilir ve `durum` `"acik+bariyer"` olur — yoksa `acik_serit` YALAN
SOYLERDI.

**KAPI 1 — T51/T56 KADRAJ KAPILARI. GECTI** (ilk ayarda DUSMUSTU, olcumle
duzeltildi):

    ayar                    rota      POZITIF KONTROL    cekimser sebepleri
    ilk (dar gecit)      193/260      192/193 DUSTU      DUSUK_GUVEN 50 · UC_BANT 17
    nihai                242/260      242/242 GECTI      DUSUK_GUVEN 18

Iki duzeltme: (a) acik seritte gecit 0,15-0,26 -> 0,24-0,36; "dar" bant gecidi
0,16-0,34 -> 0,26-0,44; (b) bariyer KORUNACAK seridi secerken artik oncelikle
bir "acik" serit korunuyor — ilk surumde korunan cogu kez "dar" seritti ve
bariyer genis olani kapatinca sahnede yalniz cok dar bir gecit kaliyordu.
Manifest: hedef 260/260 · kenar 2,0 m · hedef en/boy 1,00 · `hedef_serit !=
acik_serit` **0/260** · IHA-IB 260/260 · `hedef_varyanti` tek deger
`metin_kirmizi_H`. T48 kaplama maks %65,2 (tavan %67) · tavan reddi 0/260.

**🔴 KAPI 4 — REGRESYON DUSTU. Gizlenmiyor.**

                          ROTA     MOLOZA    AGIR   ARENA DISI
    T71 kumesi (v24)   231/260     5/231   4/231     16/231
    T66 kumesi (v24)   196/260    61/196  40/196     26/196

Moloza basma **5 -> 61** (%2,2 -> %31,1). Gorev "ARTMASIN" diyordu; ARTTI.
Kapi DUSTU.

**AMA SEBEP AYRISTIRILDI — YER GERCEGI KONTROLU (model YOK):**

    kume                     rota        moloza basan     AGIR basma
    T71 · YER GERCEGI     259/260        0/259  (%0,0)         0
    T66 · YER GERCEGI     260/260       24/260  (%9,2)         0

Iki ayri katki var:
 1. **SUBSTRAT katkisi: %9,2 ve tamami HAFIF (agir basma 0).** Ada
    geometrisinde koridorlar daralinca A* rotasi C-uzayi sinirina yaslaniyor;
    olcum rotayi `r_gerekli` ile kalinlastirip yer gercegiyle kesistirdigi
    icin sinirda TEMAS sayiyor. Agir basmanin (>%5) **0** olmasi bunun bir
    carpisma degil SIYIRMA oldugunu gosterir.
 2. **MODEL katkisi: geri kalan her sey.** v24 DIKEY SERIT geometrisi ve TEK
    renk kunyesi ile egitildi; ada geometrisi onun icin tamamen dagilim
    disidir. Model kosusunda agir basma 40 iken yer gercegiyle 0'dir.

Yani olculen kotulesmenin buyuk kismi karar zincirinden ya da substrattan
degil, **v24'un bu substrati hic gormemis olmasindan** gelir — ki T66'nin
varlik sebebi tam olarak o substrati degistirmektir. Dogru kiyas T66 uzerinde
EGITILMIS bir modelle yapilir (T68/sonraki egitim). **Karar mimara birakilir.**

**KAPI 5 — GOZLE DOGRULAMA. GECTI.** Yan yana kontak sayfasi uretildi (ayni
bes indis): ust satir T71 — duvar duvara dikey bantlar; alt satir T66 — genis
acik zemin uzerinde moloz adalari, aralarindan gecen koridorlar, koridoru
enine kesen kirmizi-beyaz bariyerler. Fark tartismasizdir.

**KAPI 6 — DEPO KAPILARI. GECTI** (depoda hicbir dosya degistirilmedi):

    codes/test_rota_sentetik.py     SONUC: 15/15 dogru
    unittest discover -s tests -q   Ran 426 tests · OK

**ETIKET CAKISMASI** T71 %0,051 -> T66 %0,204. Kaynagi arastirildi: cakisan
bilesenlerin en/boy medyani 0,8-2,0 ve yalniz %12-35'i yatay — yani ince
bariyer barlari DEGIL. Bu, poligon sadelestirmesinin KENAR ARTIGIDIR; ada
geometrisinde bolge sayisi cok arttigi icin toplam sinir uzunlugu da artti.
`approxPolyDP` epsilonu 0,0035 -> 0,0015'e cekildi; kalan %0,2 sinirda 1-2
piksellik ortusmedir, bolge duzeyinde bir etiket celiskisi degildir.

**KUME:** `O:\navitas-local-train\calisma\sentetik_arena_kadraj_t66` (260 kare).
T71 ve T60 kumeleri SILINMEDI.

**DOGRULANAMADI**
  1. GERCEK arena basarimi. Elimizde gercek arena goruntusu **HIC YOK**
     (D-88 + D-99). Bu gorev onu dogrulamaz.
  2. Ada YERLESIMI sartnameden turetilmedi — metin "moloz yiginlari arasinda"
     diyor, YIGINLARIN SAYISI, BOYUTU ve DAGILIMI hakkinda bir sey demiyor.
     Secilen yogunluk `trav/blok` oranini T71 seviyesinde tutmak icin
     AYARLANDI; gercek arenaya benzerligi OLCULEMEZ.
  3. Yeni geometrinin MODELE faydasi olculmedi; T66 uzerinde egitim
     kosulmadi. "Model 'dar dikey bant' onyargisini birakir" bir ONGORUDUR.
  4. Yer gercegiyle olculen %9,2 hafif basma sifirlanmadi; C-uzayi sinirinda
     siyirma olarak birakildi (agir basma 0).
  5. `KAPI 2 GT serit uyumsuzlugu` 22/260 -> 59/242'ye cikti. D-90 bu olcutun
     TANIMA BAGLI ve guvenilmez oldugunu zaten saptamisti (ada geometrisinde
     "serit" kavrami daha da bulaniklastir); bu sayi kanit olarak KULLANILMADI.

---

### D-104 · DENETIM + KARAR · T66 KABUL: dusen kapi GECERSIZ bir kiyastir; v26 durduruldu, v27 T66 uzerinde kosacak
Denetleyen/karar: Claude 1 (mimar) · 2026-08-14 · gorev T66+T68 (Claude 2)

**DUSEN KAPI T66'YI MAHKUM ETMEZ — KAPIYI BEN YANLIS YAZDIM.**
Gorevde *"moloza basma ARTMASIN"* dedim ve olcumun **v24 ile** yapilmasini
sarta bagladim. v24, DIKEY SERIT geometrisi ve TEK renk kunyesiyle egitilmis
bir modeldir; ada geometrisi onun icin tamamen dagilim disidir. Sabit bir
modeli tutup substrati degistirmek, substratin kusurunu degil MODELIN
dagilim disiligini olcer. Bu, D-90 bulgu 4'te kendi yazdigim uyarinin
(*"esleştirilmis degil"*) aynisidir; kapiyi yazarken uygulamayi unuttum.

**AMELE SEBEBI DOGRU AYRISTIRDI — YER GERCEGI KONTROLU (model YOK):**

    kume                     rota      moloza basan    AGIR basma
    T71 · YER GERCEGI     259/260     0/259  (%0,0)         0
    T66 · YER GERCEGI     260/260    24/260  (%9,2)         0

Model kosusunda agir basma 40 iken **yer gercegiyle 0**. Yani olculen
kotulesmenin buyuk kismi karar zincirinden ya da etiketten degil, v24'un bu
substrati hic gormemis olmasindan gelir.

**🔴 AMA GERCEK BIR SINYAL VAR ve gorevde istenmemisti: %9,2 SIYIRMA.**
Yer gercegiyle, yani KUSURSUZ algiyla bile rotalarin %9,2'si moloza TEMAS
ediyor (hepsi hafif; agir basma 0). Sebep: ada geometrisinde koridorlar
daralinca A* rotasi C-uzayi sinirina yasliyor ve `r_gerekli` ile kalinlastirilan
iz sinirda kesisiyor. Bu, uretecin koridorlarinin **govde acikligi payina
gore dar** oldugunu soyler. Sartname koridor genisligi VERMIYOR; ama 50x50 m
arenada uc guzergah icin 2,20 m'lik asgari (2 x R_GEREKLI_M) fazlasiyla
saglanabilir olmalidir. **T74 acildi.**

**DOGRULANAN ISLER (bagimsiz kontrol edilmedi, ic tutarlilik ve kapi ciktilari
uzerinden kabul):**
  * `RETR_EXTERNAL` kusuru: ada geometrisinde her ada "traversable"
    etiketlenirdi. Yakalanmasaydi yeni substrat BASTAN zehirli olurdu — bu,
    gorevin kendisinden daha degerli bir bulgudur.
  * T68 birlestirildi: acik koridoru kapatan bariyer 0/260 -> **128/260**,
    bariyer pikseli `blocked` %92,0 -> **%98,8**. D-93'un kusuru kapandi.
  * Renk cesitliligi DUSMEDI; `b` bandinda x1,41 artti. Amele "olculen bolge
    std"deki %10 dususu KOVALAMADI ve bunun bir olcum artefakti (bilesim
    etkisi) oldugunu gosterdi — bir sayiya fit etmeyi reddetmesi DOGRUDUR.
  * Ada yogunlugu iki kez olcumle ayarlandi; ilk denemedeki trav/blok 10,00
    orani (adalar cok seyrek) v16 hatasinin ikinci bir yoldan tekrari olurdu.

**GOZLE DOGRULAMA (mimar, bagimsiz kontak sayfasi).** T66 kareleri gercekten
genis baglantili zemin + kumeler halinde moloz + koridoru enine kesen bariyer
gosteriyor. Sartname SS2.1 metnine (*"moloz yiginlari arasinda olusturulmus
uc farkli yol"*) T71'den belirgin bicimde yakin. **GECTI.**

**🔴 GOZLE GORULEN YENI KUSUR — IHA-IB YERLESIMI.** Mavi 30x30 m alan
karelerin genisce bir kismini kapliyor ve KORIDORLARIN USTUNE biniyor.
SS2.1 IHA-IB'yi HTAB'dan AYRI bir bolge olarak tanimlar (*"IHA'nin gorev
sonrasi parasutle inecegi belirlenmis guvenli alandir"*); HTAB uzerine
yayilmis bir katman degildir. Yari saydam ve etikete dokunmuyor, bu yuzden
zehirli degil; ama modele YANLIS bir korelasyon ogretebilir. Amele bunu kendi
"dogrulanamadi" listesine yazmisti (5. madde). **T75 acildi.**

**KARAR — v26 DURDURULDU (epoch ~25/200), v27 T66 UZERINDE KOSACAK.**
v26 T71 substratiyla egitiliyordu; T66 onu asti. v26'nin tamamlanmasi artik
BIR DAHA KULLANILMAYACAK bir substrat hakkinda tarihsel bir soruyu
yanitlardi. GPU saati o soruya harcanmaz. Yeni kosu ayni receteyi ve ayni
on-egitimi kullanir; degisen tek sey substrattir.

⚠ **BEDELI ACIKCA YAZIYORUM:** v27, T71 (cesitlilik) ve T66 (geometri)
degisikliklerini BIRLIKTE tasir. Hangisinin ne kadar katki verdigi
AYRISTIRILAMAYACAK. Hiz gerekcesiyle bilerek kabul edilen bir olcum kaybidir.

**DOGRULANAMADI**
  1. T66'nin karar duzeyindeki etkisi, T66 ile EGITILMIS bir modelle henuz
     olculmedi. v27 bunun icin kosuyor.
  2. %9,2 siyirma orani yalniz yer gercegiyle olculdu; egitilmis modelde ne
     olacagi bilinmiyor.
  3. Arena basarimi (D-88 + D-99, kalici).

---

### D-105 · UYGULANDI · T72: HEDEF KONUMU halkasi SAHIPLENDI; SS5(b) olcek yolu ucuncu sinif OLMADAN acildi
Uygulayan: Claude 2 · 2026-08-14 · gorev T72 · kanit saha kuru kosusu + sartname SS2.2.6

**KUSUR.** `hedef_konumu` halkasi SAHIPSIZDI: HB'nin tek kaynagi Gazebo
`meta.txt`, saha kod yolunda `--hb` girisi yok, uretim modeli 2 sinifli.
Sartname SS2.2.6 gorevi "IKA'nin HB SINIRLARI ICINE girmesi" diye tanimlar —
yani acik guzergahi bulsak ve rota kusursuz olsa bile VARIS NOKTASI
uretilemedigi icin gorev TAMAMLANAMAZDI.

**UCUNCU SINIF EKLENMEDI.** nc=2 -> 3 sozlesme degisikligi, yeniden egitim ve
sinif-id cakismasi riski getirirdi (S2'de yasandi: 2 = hedef mi arac mi).
T67'nin klasik KATMAN 2 deseni kullanildi: `hb_maskesi` / `hb_konumu`.

**AYIRT EDICI UC OZELLIK (SS2.1).** "2 metre x 2 metre boyutlarinda uzerinde
KIRMIZI H harfi bulunacagi bir bolgedir":
  1. yuksek kroma KIRMIZI -> esik T67 ile **ORTAK** (`BARIYER_KROMA_ESIGI`)
  2. KARE (en/boy ~ 1)    -> bariyerin TUMLEYENI
  3. bilinen metrik kenar -> `HB_KENAR_M = 2.0`

**🔴 SEKIL FILTRESI TEK BASINA YETMEDI — OLCUMLE YAKALANDI.**
Ilk surumde `sa_000170` karesinde KIRILMIS bir bariyer parcasi 37x32 px
(en/boy **1,16** -> KARE) olarak kalmis ve gercek HB'den (25,6 px) BUYUK oldugu
icin secilmisti. Yani bariyer, kirilinca HB'nin sekil bandina GIREBILIYOR.

    olcut                    ilk surum        tumleyenlik sonrasi
    merkez hatasi maks       284,66 px              1,30 px
    YANLIS POZITIF            1/260                  0/260
    mpp hatasi maks           %25,80                 %8,57

Cozum: **T67'nin ENGEL dedigi piksel HB OLAMAZ.** `hb_maskesi` artik
`ince_bariyer_maskesi`i cagirip (5x5 genisletilmis) o pikselleri adaylardan
CIKARIYOR. Iki dedektor artik gercek anlamda TUMLEYENDIR.

Ayrica sekil bantlari arasinda BOSLUK birakildi ve testle kilitlendi:

    HB kabul araligi : 1/1,6 .. 1,6
    bariyer araligi  : 4,0 .. sonsuz
    BOS BANT         : 1,6 < 4,0     (`test_SEKIL_BANDI_arasinda_BOSLUK_var`)

**KAPI 1 — TESPIT (yer gercegi: `sentetik_arena_kadraj_t66` n=260).**

    TESPIT            260/260  (%100,0) · kacan 0
    merkez hatasi     medyan 0,71 px · p90 0,95 · maks 1,30
    kenar hatasi      medyan 1,40 px · maks 2,40   (yer gercegi kenar 25,6 px)

**KAPI 2 — YANLIS POZITIF (bariyeri HB sanma): 0/260. GECTI.**
T67'nin TERS yonde pozitif kontrolu. `sa_000170` vakasi kalici teste alindi
(`test_KIRIK_bariyer_parcasi_HB_DEGILDIR`).

**KAPI 3 — mpp CAPRAZ KONTROLU.**

    mpp hatasi   medyan %5,185 · p90 %8,571 · maks %8,571
    capraz durum {dogrulandi: 260, celiskili: 0, yalniz_hb: 0}

Sapma SISTEMATIKTIR: pedin piksel kenari morfolojik kapamayla ~1,4 px sisiyor,
`mpp = 2,0/kenar` oldugu icin mpp bir miktar KUCUK cikiyor. **DUZELTILMEDI** —
duzeltme katsayisi bizim kendi cizimimize fit edilirdi ve gercek pedde
tutmazdi. Bunun yerine capraz bandi (%25) sapmanin ~4,8 kati secildi: gercek
celiskiyi yakalayacak kadar dar, dedektorun kendi sapmasini celiski saymayacak
kadar genis.

**CONTRACTS SS5(b) ACILDI.** Sozlesme "ucuncu sinif uretime girdiginde acilir"
diyordu; klasik dedektor onu ucuncu sinif OLMADAN acti. Satir guncellendi.

**CONTRACTS SS5.4 YAZILDI — iki kaynak CELISIRSE ne olur (baglayici):**

    yalniz telemetri            -> telemetri      (SS5 birincil kaynak)
    yalniz HB                   -> HB
    ikisi, fark <= 0,25         -> TELEMETRI      (HB yalniz DOGRULAR)
    ikisi, fark  > 0,25         -> HICBIRI, ("celiskili", fark)

🔴 **Celiskide ORTALAMA ALINMAZ ve biri secilmez.** Iki bagimsiz olcum
celisiyorsa hangisinin dogru oldugunu bilmiyoruz demektir; uydurma bir orta
deger olculmemis bir olcegi olculmus gibi gosterir. Fail-closed.

**KARAR YOLUNA BAGLANDI — GERIYE UYUMLU.** `analyze_path` opsiyonel `goruntu`
parametresi aldi:
  · `goruntu` VERILMEZSE davranis DEGISMEZ — hedef eskisi gibi UST BANTTIR ve
    tum mevcut cagri yerleri (olcum betikleri dahil) aynen calisir.
  · `goruntu` VERILIRSE cagiran "varis noktasini HB'den al" demis olur; HB
    bulunamazsa UYDURULMAZ, yeni `HEDEF_YOK` sebebiyle CEKIMSER kalinir.
Hedef tohumu koridorla KESISTIRILIR; HB koridora bagli degilse baglanti kapisi
zaten reddeder.

⚠ **MADDE 15 KORUNDU VE TESTLE KILITLENDI.** HB'yi bulmak serbest alani ne
buyutur ne kucultur; yalniz A*'in HEDEFINI secer. `test_MADDE_15_HB_serbest_
alani_BUYUTMEZ` ayni maskede `return_clean` ciktisini HB'li ve HB'siz kosuda
karsilastirip BIREBIR ayni oldugunu dogrular.

**KAPI 4 — MUTASYON KONTROLU (D-15/K-04):**

    M0  mutasyon YOK                                 25 kosuldu · DUSEN 0
    M1  HB sekil bandi bariyerin ICINE tasirildi     25 kosuldu · DUSEN 1  ATESLENDI
    M2  ORTAK kroma esigi 200 yapildi                25 kosuldu · DUSEN 8  ATESLENDI
    M3  HB kenari 2,0 -> 5,0 m (sartname disi)       25 kosuldu · DUSEN 2  ATESLENDI
    M4  capraz bandi 5,0 (celiski hic yakalanmaz)    25 kosuldu · DUSEN 1  ATESLENDI
    M5  geri alma sonrasi                            25 kosuldu · DUSEN 0

**KAPI 5 — depo kapilari.**

    codes/test_rota_sentetik.py     SONUC: 15/15 dogru                 GECTI
    unittest discover -s tests -q   Ran 451 tests · OK                 GECTI
    scripts/jetson_paket_hazirla.py 9/9 bayt-esit                      GECTI

**MEVCUT BIR TEST DOGRU ATESLEDI VE GUNCELLENDI.**
`test_sebep_kodlari_sozlesmede_SAYILANLARDIR` 11. sebep kodu eklenince dustu —
T65'te tam bunun icin yazilmisti ("yeni kod eklenirse bu liste de guncellenmek
ZORUNDA, sessizce buyuyemez"). Liste guncellendi; kume yine TAM kilitli.

**YENI TEST PAKETI** `tests/test_hb_dedektoru.py` (25 test): sozlesme kaynagi
(sekil bandi bosluğu, ORTAK kroma esigi kaynaktan dogrulanir, HB kenari
sartnameden) · tespit (dort boyutta) · fail-closed · TUMLEYENLIK (uzun bar,
kirik parca, ayni karede ikisi birden) · olcek (mpp, capraz kontrolun dort
dali) · `analyze_path` entegrasyonu (geriye uyum, HEDEF_YOK, madde 15,
mutasyon kilidi) · olculen dagilim regresyonu.

**DOGRULANAMADI**
  1. Bu kume **SENTETIKTIR** ve HB'yi BIZIM cizdigimiz bicimde tasir
     (T71'in `hb_ciz`i: ped + kirmizi cerceve + kirmizi H). Gercek arenada
     tutacagi **DOGRULANAMAZ** (D-88 + D-99: elimizde gercek arena goruntusu
     HIC YOK). %100 tespit bir GERCEK BASARIM iddiasi DEGILDIR.
  2. Gercek HB'nin GORUNUMU bilinmiyor: sartname "uzerinde kirmizi H harfi"
     diyor, pedin rengini/malzemesini/parlakligini SOYLEMIYOR. Kroma esigi
     (25) yapay zeka uretimi bir figurden kalibre edilmisti (D-99).
  3. HB'nin KISMEN ORTULU oldugu (moloz/golge altinda) durum SINANMADI.
  4. mpp'nin %5,2 sistematik sapmasi gercek pedde gecerli DEGILDIR; orada
     baska bir sapma olabilir.
  5. Uretim cagri yerleri (`run_image`/`run_video`/`run_camera`) bu gorevde
     `goruntu` GECIRMIYOR — yani hedef halkasi SOZLESMEDE ve karar yolunda
     HAZIR ama uretim yolunda HENUZ ETKIN DEGIL. Bunu acmak T73'un
     parametrik saha kodu isiyle birlikte yapilmalidir (o dosya su an
     ikinci amelede).

---

### D-106 · UYGULANDI + BIR KAPI KALDI · T73: saha kodu parametrik oldu; model_yukleme'yi KAYIT DEFTERI BAYATLIGI tutuyor
Uygulayan: Claude 2 · 2026-08-14 · gorev T73 · kanit saha kuru kosusu

**KUSUR.** Iki halka DUSUKTU ve ikisi de ayni siniftandi — saha kodu ELLE
DUZENLENMEDEN kosamiyordu. Sartname SS2.2.1 sistemlerin goreve MUHURLU KUTULAR
icinde intikal etmesini sart kosar; yarisma gunu kamera indeksi ya da model
dosyasi degisirse kaynak dosya duzenlemek prosedure AYKIRIDIR.

**1 · KAMERA PARAMETRIK.** `cv2.VideoCapture(0)` sabitti. Artik `--kaynak`
indeks / cihaz yolu / dosya kabul ediyor; donusum TEK YERDE (`kamera_kaynagi_coz`)
yapiliyor ki cagri yerleri "0" metnini cihaz dosyasi sanmasin.
**Varsayilan DEGISMEDI** (kaynak verilmezse indeks 0) — geriye uyum testle
kilitli.

**2 · `--model` EKLENDI, VARSAYILAN CIPLAK DEGIL.** Varsayilan Jetson uretim
manifestindeki `asil_model_pt` alanindan turetilir (`varsayilan_model_yolu`).
Kaynak dosyada `navitas_seg_vNN_best.pt` kalibinda CIPLAK AD KALMADIGI ayrica
testle dogrulanir. Manifest alani yol kacisina karsi denetlenir
(`../gizli.pt`, `alt/dizin.pt`, `.onnx`, bos, None, sayi -> hepsi RED).

**3 · FAIL-CLOSED.** Yuklenen agirlik `config/model_registry.json`'daki etkin
profille UYUSMUYORSA `load_model` **yukselir**; sessiz devam YOK. Sessiz devam
sahada YANLIS MODELLE ucmak demektir (D-89'un besinci ucu tam bu siniftandi).
Gevsetme ancak `--kayit-dogrulamasiz` ile ACIKCA istenir; varsayilan
`MODEL_KAYIT_ZORUNLU = True`. Kayit defteri YOKSA bu "uyum" SAYILMAZ —
yokluk fail-closed tarafinda kalir.

**⚠ GERIYE UYUM KORUNDU — MEVCUT BIR TEST YAKALADI.** Ilk yazimimda
`load_model` uc'lu demet donduruyordu; `tests/test_rpi_canli_olcek.py` bunu
`TypeError: cannot unpack non-iterable object` ile YAKALADI. Depo taramasinda
`codes/test_batch.py:139` ve `drone/rpi_yayin.py:415` de `load_model()` deyip
MODEL bekliyor — ikisi de T73'un izin listesinde YOK. Donus MODELE geri
cevrildi; ek bilgi ACIKCA istenir (`ayrinti=True`).

**4 · HALKALAR ARTIK BESLEMEYI OLCUYOR (D-98 dersi).** Eski iki halka yalnizca
`"--model" in secenekler` gibi SECENEGIN VARLIGINA bakiyordu — D-98'de "olcek"
halkasinin fonksiyonun VARLIGINA bakip GECTI yazmasiyla ayni kusur.

  · `_kamera_beslemesi_olc`: `run_camera` GERCEKTEN kosulur ve
    `cv2.VideoCapture`in NE ALDIGI olculur (cihaz yolu str, indeks int).
  · `_model_beslemesi_olc`: UC davranis ayri olculur — varsayilan manifestten
    mi geliyor · verilen yol GERCEKTEN yukleniyor mu · uyusmazlikta
    FAIL-CLOSED mi.

**GOREV AYRIMI (gizleme DEGIL).** `cikarim` halkasinin olcutu CIKARIMIN
TAMAMLANMASIDIR; bildirim tutarliligi `model_yukleme`nin isidir. Bu yuzden
`cikarim` artik `kayit_zorunlu=False` ile yukluyor. Aksi halde kayit defteri
bayatligi `cikarim -> maske -> rota` zincirini de dusuruyordu (olculdu: GECTI
5 -> 3). Uyusmazlik `model_yukleme`de HALA DUSTU olarak raporlanir.

**KAPI 1 — SAHA KURU KOSUSU.**

    taban   GECTI 5 · DUSTU 3 · SAHIPSIZ 2 · ATLANDI 0
    T73     GECTI 6 · DUSTU 2 · SAHIPSIZ 2 · ATLANDI 0

    kamera         GECTI   kaynak parametrik ve VideoCapture'a BESLENIYOR
    model_yukleme  DUSTU   karsilanmayan kosul: kayit defteriyle ESLESME

**🔴 HEDEF GECTI >= 7 IDI, 6'DA KALDI. SEBEP TEK VE OLCULDU.**
`model_yukleme` icin bes kosul olculuyor; **DORDU SAGLANIYOR**:

    --model argumani              EVET
    varsayilan MANIFESTTEN        EVET  (navitas_seg_v24_best.pt)
    arguman yuklemeyi BESLIYOR    EVET
    uyusmazlikta FAIL-CLOSED      EVET
    kayit defteriyle ESLESME      HAYIR  <- TEK EKSIK

Sebep: **IKI BILDIRIM CELISIYOR.**

    Jetson uretim manifesti  asil_model_pt = navitas_seg_v24_best.pt   (T58)
    config/model_registry.json  competition -> models/navitas_seg_v4_best.pt

Kayit defteri **v4 doneminden kalma BAYAT**. CONTRACTS SS11 bunu zaten
soyluyordu ("kayit defteri de bayat") ama duzeltilmemis. Fail-closed dogru
calisiyor ve dogru sonucu veriyor: hangi agirligin uctugunu bilmiyoruz.

⚠ **DUZELTMEDIM.** `config/` T73'un izin listesinde YOK
(`codes/rpi_inference.py · scripts/saha_kuru_kosu.py · tests/**`).
Duzeltme TEK SATIRDIR: `profiles.competition.path` -> `models/navitas_seg_v24_best.pt`
(ve `sha256` ile `model_id` alanlari da guncellenmelidir, aksi halde SHA
dogrulamasi bir sonraki adimda ayni celiskiyi uretir). Izin verilirse yaparim.

**KAPI 2 — MUTASYON: yanlis model yolu -> ACIK HATA.**

    var olmayan dosya  -> RuntimeError "Model agirligi bulunamadi: ...yok.pt"
    yanlis uzanti      -> RuntimeError "MODEL KAYIT DOGRULAMASI BASARISIZ"
    varsayilan yol     -> RuntimeError "MODEL KAYIT DOGRULAMASI BASARISIZ"

Uc vakada da SESSIZ GECIS YOK.

**KAPI 3 — MUTASYON: kamera parametresi kaldirilinca halka DUSER.**

    kaynak parametresi KALDIRILDI -> besledi=False ·
        hata "run_camera `kaynak` almiyor: unexpected keyword argument"
        halka sonucu: DUSER   (dogru)
    mutasyon geri alindi          -> besledi=True · alinan='/dev/video7'
        halka sonucu: GECER   (dogru)

**KAPI 4 — depo kapilari.**

    codes/test_rota_sentetik.py     SONUC: 15/15 dogru        GECTI
    unittest discover -s tests -q   Ran 468 tests · OK        GECTI

**KAPI 5 — Jetson paketi yeniden uretildi: 9/9 bayt-esit.**

**YENI TEST PAKETI** `tests/test_saha_parametrik.py` (17 test): kamera kaynagi
cozumu (indeks/cihaz yolu/dosya, bool REDDI) · BESLEME olcumu (VideoCapture ne
aldi, varsayilan degismedi) · manifest varsayilani (ciplak ad yok, guvensiz
alan reddi, manifest yoksa sessiz varsayilan URETILMEZ) · fail-closed (yukselme,
uyumda yukleme, gevsetmenin ACIKCA istenmesi, var olmayan yol, kayit defteri
yoklugu uyum SAYILMAZ) · ve kayit defteri celiskisini BUGUNKU haliyle kaydeden
bir test — kayit defteri duzeltilince O TEST DUSER ve duzeltmenin yapildigini
bize soyler (o zaman ters cevrilmelidir).

**IKI MEVCUT TEST GUNCELLENDI (gizlenmiyor).**
`test_rpi_canli_olcek.py`: (a) `load_model` sahtesi artik `ayrinti=True`
sozlesmesini tasiyor; (b) `run_camera` beklentisi `kaynak=None` iceriyor —
`main` artik kamera kaynagini da tasiyor. Ikisi de GENISLETILEN sozlesmenin
kaydidir, gevsetme DEGILDIR.

**DOGRULANAMADI**
  1. Gercek kamera ile hicbir sey kosulmadi — donanim yok. `--kaynak`in
     `/dev/video1` gibi bir cihazda ACILDIGI DOGRULANMADI; olculen sey
     degerin `VideoCapture`a DOGRU TIPTE ULASTIGIDIR.
  2. `model_yukleme` halkasi kayit defteri duzeltilene kadar GECEMEZ.
  3. SHA dogrulamasi UYGULANMADI. CONTRACTS SS11.3 "SHA dogrulanacak" diyor;
     bugun yalniz DOSYA ADI kiyaslaniyor. Kayit defteri guncellenirken SHA da
     dogrulanmali — ayri is.
  4. `scripts/jetson_fps.py` kendi manifest okuyucusunu tasiyor (T62). Artik
     `rpi_inference.varsayilan_model_yolu` kanonik olabilir ve o dosya buradan
     import etmelidir; o dosya T73'un izin listesinde YOK (ayri gorev).
  5. `--kayit-dogrulamasiz` bayragi guvenligi ACIKCA gevsetir. Sahada
     kullanilirsa gerekcesi kayda gecmelidir; bu betikle zorlanamaz.

---

### D-107 · ONCEDEN KAYIT · v27 kabul olcutleri — SONUC GORULMEDEN yazildi
Yazan: Claude 1 (mimar) · 2026-08-14 15:30 · v27 epoch ~14/200, bitisine ~8 saat

**NEDEN ONCEDEN.** Bu projede tekrarlanan hata olcutu SAYIYI GORDUKTEN SONRA
yorumlamak oldu: D-85'te alt kumenin azamisine esik oturttum (D-86 curuttu),
D-90'da tanima bagli bir olcutle %92,7 rapor etmek uzereydim, D-104'te kapiyi
yanlis modelle olcturdum. Olcut sonuctan SONRA secilirse rasyonalize edilir.
Bu yuzden esikler BURAYA, sonuc gelmeden yaziliyor ve sabah DEGISTIRILMEYECEK.

**TABANLAR (bugun olculdu, T66 kadraj kumesi n=260):**

    olcum                          rota      moloza basan   AGIR   arena disi
    YER GERCEGI (model YOK)     260/260     24 (%9,2)          0        —
    v24 (uretim, dagilim DISI)  196/260     61 (%31,1)        40   26 (%13,3)

Yer gercegi satiri bu substratin KENDI TABANIDIR: kusursuz algiyla bile %9,2
siyirma var (T74). Hicbir model bunun altina inmek zorunda degildir.

**v27 KABUL OLCUTLERI — hepsi saglanmali (AND):**

    K0  KORLUK YOK (v25'in olum sebebi)
        · sartname figuru        : zemin kaplamasi > %0    (v25: %0,0 -> RED)
        · raw_frames otopark     : bos maske 0/8
        · copy_paste_gercek      : bos maske 0/8
    K1  ROTA URETIMI            : >= 230/260   (v24: 196 · yer gercegi: 260)
    K2  MOLOZA BASMA            : <= %15       (v24: %31,1 · taban: %9,2)
    K3  AGIR BASMA (>%5)        : <= %3        (v24: %20,4 · taban: %0)
    K4  ARENA DISI              : <= %5        (v24: %13,3)
    K5  BARIYER KESISIMI        : 0 px         (v24 + T67 dedektoru: 0 px)

**KARAR KURALI — sabah tartisilmayacak:**
  * K0..K5 hepsi saglanirsa  -> v27 URETIME ALINIR.
  * K0 duserse               -> v27 REDDEDILIR (v25 ile ayni sebep, tartisma yok).
  * K0 gecer, K1..K5'ten biri duserse -> v27 uretime ALINMAZ; dusen olcut
    kok nedene baglanir ve tek bir duzeltme turu kosulur (T74 en olasi aday).
  * v27 v24'ten kotu cikarsa -> v24 KALIR. "Yeni model yeni substrat icindir"
    gerekcesiyle kotusu secilmez.

**BU OLCUMLERIN TAMAMI SENTETIKTIR.** T66 kadraj kumesi bizim urettigimiz
zemindir; sartname figuru ise YAPAY ZEKA urunudur (D-99). Hicbir esik "sahada
calisir" anlamina GELMEZ. Gercek arena dogrulamasi 30 Eylul gorev test
ucusundan once mumkun degildir (D-88 + D-99, kalici kisit).

**⚠ BILINEN OLCUM KAYBI.** v27 hem T71 (renk cesitliligi) hem T66 (ada
geometrisi) degisikligini birlikte tasir; hangisinin ne kadar katki verdigi
AYRISTIRILAMAZ (D-104'te hiz gerekcesiyle bilerek kabul edildi).

---

### D-108 · OLCUM · Uretim EGITIM COZUNURLUGUNDEN dusukte kosuyor: bedava IoU kaybi; ve egitim GPU'ya degil VERI HATTINA bagli
Olcen: Claude 1 (mimar) · 2026-08-14 · kullanici OC sorusu uzerine · v27 kosarken

**BULGU 1 — EGITIM 640, URETIM 512.**

    egitim recetesi          imgsz = 640   (v15_ft2sinif'ten birebir alinmis)
    codes/rpi_inference.py   INFER_SIZE = 512

Bedeli OLCULDU (v24, T66 kadraj n=60, yer gercegi etiketleriyle):

    imgsz   zemin IoU   kesinlik   duyar   kaplama
      512      0,405      0,630    0,523    %26,6   <- URETIM burada
      640      0,435      0,671    0,548    %27,2   <- model burada EGITILDI
      800      0,442      0,674    0,553    %27,9

512'de kosmak IoU'da **%6,9**, kesinlikte **%6,1** kayip demektir. Model zaten
640'ta egitildi; bu kayip BEDAVA verilmis bir kayiptir.

⚠ Bu, acik duran **S5**'in ("cikarim imgsz sabitlenmemis") somut bedelidir.
S5'in kaniti v17'de 640 -> IoU 0,861 · 960 -> 0,034 idi; yani bu model
ailesinde cozunurluk duyarliligi SERT. 512<->640 farki o kadar yikici degil
ama olculebilir ve tek yonlu.

**KARAR VERILMEDI — odunlesme var.** 640'a cikmak Jetson'da 1,56 kat cikarim
hesabi demektir (640²/512²). `results/jetson_fps_pc_smoke` olcumu darbogazin
cikarim degil COSTMAP oldugunu soyluyordu (cikarimin ~2 kati), dolayisiyla
640 karsilanabilir gorunuyor — ama Jetson'da HIC olcum yok. Karar S5'te
verilecek; bu kayit bedeli SAYIYA baglar.

**BULGU 2 — EGITIM GPU'YA DEGIL VERI HATTINA BAGLI.**
Kullanici GPU'yu overclock etti ve hiz sordu. Olculdu:

    son 5 epoch    138,5 s      onceki 9 epoch  139,1 s   -> BASAMAK YOK
    GPU kullanimi  ort %58 · min %1 · maks %96  -> %42 BOSTA
    SM saati       ort 2565 MHz · maks 3000 (tavan 3090) -> tavana DAYANMIYOR
    sicaklik       ort 82 C · maks 87 C
    workers 8 · cache false · makinede 24 cekirdek, 51 GB bos RAM

OC olculebilir hizlanma VERMEDI ve sebebi acik: %42 bosta bekleyen ve saat
tavanina zaten dayanmayan bir GPU'yu hizlandirmak bir sey kazandirmaz. Sinir
guc/sicaklik tarafinda, is yuku ise CPU tarafinda (veri yukleme + maske
rasterizasyonu; T66 substrati poligon sayisini 3 kata cikardi).

**TAVAN:** veri hatti sonsuz hizli olsaydi epoch 138 x 0,58 = **~80 s** olurdu,
yani **~1,7 kat**. 8,6 saatlik kosu ~5 saate iner.

**ONERI (bir sonraki kosuda, OLCULEREK):** `workers` 8 -> 16 (Windows'ta
spawn kullanilir, 24'e cikarmak ters teper), `cache='ram'` (~8,5 GB, 51 GB
bos). `batch` 12'de KALSIN — VRAM'de yer var ama batch degisimi egitim
dinamigini degistirir ve v24/v25/v27 kiyasini bozar.

**v27 YENIDEN BASLATILMADI.** Kalan 161 epoch x 138 s = 6,2 saat. Bastan
1,7 kat ile 200 x 81 s = 4,5 saat; kazanc ~1,5 saat, bedeli 39 epoch'luk
ogrenme durumu ve LR takvimi. Degmez.

**DOGRULANAMADI**
  1. `workers`/`cache` kazanci OLCULMEDI — v27 CPU'yu kullaniyor, simdi
     olcmek hem yaniltir hem v27'yi yavaslatir. Sonraki kosuda olculecek.
  2. 1,7 kat TAVANDIR, ulasilacagi garanti degildir.
  3. Cozunurluk olcumu v24 ve T66 kadraj icindir; v27'de yeniden olculmeli.
  4. Jetson'da hicbir hiz olcumu YOK (D-89'dan beri acik).

---

### D-109 · 🔴 KUSUR · `--devam` HIC CALISMIYORMUS: sessizce bastan basliyor ve `results.csv`'yi SILIYOR
Bulan: Claude 1 (mimar) · 2026-08-14 · `O:\navitas-local-train\56_t53_gercek_karisim.py`

**NASIL YAKALANDI.** Kullanici "egitim yarida kalinca devam edecek sekilde
ayarlamistik" dedi ve hizlandirma icin kosuyu durdurup yeniden baslatmayi
onerdi. Devam calisti sanildi; args satirinda **`resume=False`** ve
**`model=v15_on10sinif/weights/best.pt`** (ON-EGITIM) gorulunce yakalandi.

**KOK NEDEN.** Runner `--devam` verilse bile modeli ON-EGITIMDEN kuruyordu:

    model = YOLO(str(ON_BEST))                       # <- her zaman on-egitim
    model.train(..., exist_ok=True, resume=args.devam)

Ultralytics `resume=True`yu ancak MODELIN KENDISI bir kontrol noktasiysa
cozer (`BaseTrainer.check_resume`). On-egitimden kurulunca `resume` sessizce
False'a duser, kosu **BASTAN** baslar ve `exist_ok=True` yuzunden
`results.csv` **SILINIR**. Hicbir hata verilmez.

**BEDELI.** v27'nin 44 epoch'u (~1,7 saat) kaybediliyordu. `last.pt` diskte
kaldigi icin kurtarildi (`calisma/v27_epoch44_last.pt`, epoch 43,
fitness 1,31829) ve geri yuklendi.

**DUZELTME.** `--devam` verildiginde model kosunun KENDI `last.pt`'sinden
kurulur ve `resume`a o dosyanin YOLU verilir; kontrol noktasi yoksa
`SystemExit` ile durur (fail-closed, sessiz bastan baslama YOK).

⚠ Bu kural bellekte **"kesinti sonrasi ayni komutla devam"** diye kayitliydi
ve HIC SINANMAMISTI. Yazili olmasi calistigi anlamina gelmiyormus — D-81'in
("bir islemin basarili donmesi istenen seyi yaptigi anlamina gelmez")
bir baska ornegi.

---

### D-110 · OLCUM · `cache='ram'` Windows'ta MemoryError veriyor: isciler onbellegi PAYLASMIYOR, KOPYALIYOR
Olcen: Claude 1 (mimar) · 2026-08-14

D-108 veri hattini darbogaz olarak gostermisti. Onerilen `workers=16` +
`cache='ram'` uygulandi ve **MemoryError** ile coktu — 83 GB bos RAM varken.

**KOK NEDEN — PLATFORMA OZGU.** Windows'ta dataloader iscileri `spawn` ile
baslar, `fork` ile degil. `fork` olsaydi onbellek kopyala-yaz ile PAYLASILIRDI;
`spawn`da her isci onbellegin **KENDI KOPYASINI** kurar. 16 isci x ~10 GB
onbellek RAM'i kat kat asar. Linux'ta ayni ayar sorunsuz calisirdi.

**COZUM: `cache='disk'`.** Uc sorunu birden cozer:
  1. **Bellek**: `.npy` dosyalari bellek eslemelidir, isciler arasinda
     paylasilir, cogalmaz. (Disk ihtiyaci ~8,5 GB; O:'da 144 GB bos.)
  2. **BELIRLENIRLIK**: Ultralytics'in kendi uyarisi *"cache='ram' may produce
     non-deterministic training results. Consider cache='disk' as a
     deterministic alternative"*. Recetemizde `deterministic=True` var;
     `ram` bunu sessizce bozardi.
  3. **I/O**: asil kazanc olan JPEG cozme maliyeti yine kalkar.

**AYRICA — ISLETIM NOTU.** Arka planda baslatilan egitim, oturum sureci
kapaninca OLDU (GPU %0, python sureci 0, `results.csv` yok). Uzun kosular
oturumdan BAGIMSIZ baslatilmalidir (Windows'ta `Start-Process`), yoksa
`FOR_DISABLE_CONSOLE_CTRL_HANDLER=1` ayarli olsa bile surec agacina bagli
kalir. Bu, `egitim-konsol-olayi` bellek notunun ikinci bir yuzudur.

**DOGRULANAMADI**
  1. `workers=16` + `cache='disk'` kazanci bu kayit yazilirken HENUZ
     olculmedi; olculunce ayrica raporlanacak.
  2. En iyi `workers` degeri taranmadi; 16 secildi cunku makinede 24 cekirdek
     var ve `spawn` maliyeti yuksek. 8/12/20 KIYASLANMADI.

---

### D-111 · 🔴 DUZELTME · D-108'in "640 daha iyi" BULGUSU YANLISTI: olculen sey BUYUTME artefaktiydi; 640 kesinligi DUSURUYOR
Duzelten: Claude 1 (mimar) · 2026-08-14 · D-108 bulgu 1 GECERSIZ

**YANLIS OLAN NE.** D-108'de "egitim 640, uretim 512; 512'de kosmak IoU'da
%6,9 kayip" yazdim ve bunu `predict(small, imgsz=640)` ile olctum. Ama
`_preprocess` (`codes/rpi_inference.py:1301`) goruntuyu `predict`e vermeden
ONCE zaten `INFER_SIZE`e indiriyor:

    small = cv2.resize(tuval, (INFER_SIZE, INFER_SIZE))    # INFER_SIZE = 512

Yani `imgsz=640` verdigimde Ultralytics **512'lik bir goruntuyu 640'a
BUYUTUYORDU**. Yeni bilgi yok, yalniz interpolasyon. Olctugum sey "640'ta
cikarim" DEGIL, "buyutulmus 512" idi.

**BU AYRICA "yalniz 512 calisiyor" TUHAFLIGINI DA ACIKLIYOR.** Figur uzerinde
cozunurluk supurmesi sunu vermisti:

    imgsz  416  480  512   544  576  608  640  672  704  800
    zemin%  0    0   34,6   0    0    0    0    0    0    0

512 tek calisan degerdi cunku YALNIZ orada yeniden ornekleme YOKTU; diger her
degerde girdi bir kez kucultulup sonra buyutuluyordu ve model o artefaktta
sahneyi butunuyle ENGEL ilan ediyordu. Bu bir cozunurluk bulgusu degil, bir
OLCUM KUSURUDUR — benim kusurum.

**DOGRU OLCUM (`INFER_SIZE` degistirilerek, gercek 640):**

    INFER_SIZE   kadraj IoU   kesinlik   FIGUR zemin%
           512        0,405      0,630         %34,6
           640        0,402      0,598         %37,3

**SONUC: 640 IoU KAZANDIRMIYOR (0,405 -> 0,402) ve KESINLIGI %5 DUSURUYOR.**
Kesinlik dususu bu mimaride TEHLIKELI yondur — dort kapili olcutte
*"KESINLIK ONCELIKLI: yanlis-pozitif zemin, kacirilan zeminden TEHLIKELIDIR"*
yazilidir. 1,56 kat hesap karsiliginda guvenlik yonunde kayip alinir.

**ONERI: `INFER_SIZE = 512` KALSIN.** Kullanici 640'i istedi; gerekcesi
D-108'in YANLIS sayisiydi. Duzeltilmis sayilarla karar kullaniciya geri
verilir.

**S5 ICIN KALAN GERCEK SORU.** "Hangi cozunurlukte egitilmeli/kosulmali"
sorusu hala aciktir ama bu olcumle YANITLANAMAZ: v24 640'ta EGITILDI ve
512'de kosuyor; her ikisi de sabit. Gercek yanit, ayni substratla 512'de
EGITILMIS bir modeli 512'de kosup kiyaslamaktir. Bu bir egitim kosusu
gerektirir; v27'den sonra degerlendirilecek.

**DERS.** Bir ardisik islem hattinda "cozunurlugu degistirdim" demek, hattin
HANGI adiminda degistirdigimi bilmeden anlamsizdir. D-53 ("olcum zeminine
bak") ve D-99 ("kaynagin ne oldugunu belgeden dogrula") ile ayni ailedendir:
olcumden once BORUYU oku.

**DOGRULANAMADI**
  1. Egitim cozunurlugunun (640) uretim cozunurluguyle (512) uyusmamasi hala
     bir uyusmazliktir; bedeli OLCULMEDI cunku olcmek yeni bir egitim ister.
  2. Bu olcum v24 icindir; v27'de yeniden yapilmalidir.

---

### D-112 · KARAR · Cozunurluk HER YERDE 512: 640'in olculebilir bir ustunlugu YOK, maliyeti VAR
Olcen/karar: Claude 1 (mimar) · 2026-08-14 · kullanici sorusu: "tam 512 ya da tam 640, ikisi arasi kalmasin"

**SORUN.** Sistem tutarsiz bir durumdaydi: modeller `imgsz=640` ile EGITILIYOR,
uretim `INFER_SIZE=512` ile KOSUYOR. Bu uyusmazlik hic olculmemisti ve D-108'de
yanlis olctum (D-111 duzeltti).

**OLCUM — INFER_SIZE gercekten degistirilerek** (v24, 640'ta egitilmis;
T66 kadraj n=50; yer gercegi etiketleriyle):

    INFER     IoU  kesinlik   duyar   FIGUR zemin%   ms/kare (RTX 5080)
      384   0,419     0,620   0,556          %38,8    (127 = isinma)
      448   0,392     0,644   0,499           %0,0
      512   0,399     0,625   0,527          %34,6         63
      576   0,405     0,646   0,529          %39,1         64
      640   0,400     0,598   0,531          %37,3         64
      768   0,402     0,633   0,522          %37,6         68

**BULGU 1 — FARKLAR GURULTUNUN ALTINDA.** IoU yayilimi 0,392..0,419 = **0,027**;
kesinlik yayilimi 0,048. Bu projenin olculmus gurultu tabani **0,04**'tur
(maske sd 0,025-0,032, K-3 ile birlikte kayitli). Yani cozunurluk secimi
DOGRULUK acisindan AYIRT EDILEMEZ. D-111'de "640 kesinligi %5 dusuruyor"
dedigim fark da bu gurultunun icindedir; tek basina karar gerekcesi olamaz.

**BULGU 2 — PC'DE SURE DE FARK ETMIYOR** (63-68 ms). RTX 5080'de bu boyutlarda
olculen sey hesap degil EK YUKTUR. Jetson'da durum farklidir: 640, 512'nin
**1,56 kati** hesap demektir (640²/512²) ve orada HIC olcumumuz YOK (D-89).

**BULGU 3 — 448'DE FIGURDE TAM KORLUK (%0,0).** Komsu degerler (%34,6 ve
%39,1) saglamken 448 tamamen coküyor. Bu bir cozunurluk EGRISI degil,
KIRILGANLIK isaretidir; v25'in olum bicimiyle ayni sinifta. Ayrica kayda gecer:
model belirli olceklerde catlayabiliyor.

**KARAR: 512 — EGITIMDE DE, CIKARIMDA DA.**
Gerekce sirasi (dogruluk gerekcesi YOK, cunku olculemedi):
  1. **Jetson maliyeti**: 512, 640'in 0,64 kati hesap. Orada hicbir olcumumuz
     yok; ucuz olani secmek riski kucultur.
  2. **Egitim maliyeti**: 512'de egitim ~0,64 kat -> 8,6 saatlik kosu ~5,5
     saate iner. Kullanicinin hiz sikayetine dogrudan cevap verir.
  3. **Tutarlilik**: egitim ve cikarim ayni olcekte olur; olculmemis bir
     uyusmazlik ortadan kalkar.
  4. **Degisiklik maliyeti sifir**: uretim ZATEN 512'de kosuyor. Degisen
     yalniz EGITIM recetesidir.

⚠ **NE IDDIA ETMIYORUM:** "512 daha dogru" DEMIYORUM — olculemedi. Iddia
"640'in olculebilir bir ustunlugu yok, maliyeti var"dir.

**UYGULAMA.** `56_t53_gercek_karisim.py` recetesinde `imgsz` 640 -> 512.
⚠ v27 SU AN 640 ile kosuyor ve YENIDEN BASLATILMAYACAK — 47 epoch'u atmak
olculebilir bir kazanc getirmez ve D-109'da zaten 44 epoch kaybettik.
Degisiklik v28'den itibaren gecerlidir. Boylece v27<->v28 kiyasi bir degisken
daha tasiyacak; bu bilerek kabul edilir ve burada yazilidir.

**DOGRULANAMADI**
  1. 512'de EGITILMIS bir modelin 512'de nasil davranacagi OLCULMEDI; tum
     olcumler 640'ta egitilmis v24 icindir. Asil kiyas v28 ile yapilacaktir.
  2. Jetson'da hiz farki olculmedi (D-89'dan beri acik).
  3. 448'deki korlugun sebebi arastirilmadi.

---

### D-113 · 🔴 KUSUR · `best.pt` YANLIS MODELI TUTUYOR: `best_fitness` ULASILAMAZ bir tavana kilitlenmis
Olcen: Claude 1 (mimar) · 2026-08-14 19:22 · kullanici sorusu: "egitim ne durumda"

**BELIRTI.** v27 epoch 112'de kosarken `best.pt` dosya tarihi **16:30:06**'da
donmus — 2 saat 50 dakikadir yazilmamis. Kontrol noktasi ustverisi:

    v27_t66_adalar  best  epoch=43   best_fitness=1.31829
    v27_t66_adalar  last  epoch=112  best_fitness=1.31829

**FITNESS FORMULU DOGRULANDI** (ultralytics 8.4.92, kaynaktan okundu):
`SegmentMetrics.fitness = seg.fitness() + DetMetrics.fitness`, `Metric.fitness`
agirliklari `[P,R,mAP50,mAP50-95] = [0,0,0,1]`. Yani **fitness = kutu mAP50-95 +
maske mAP50-95**. v26'nin `results.csv` epoch 16 satiriyla kalibre edildi:
0,73735 + 0,60165 = 1,339 = kontrol noktasindaki `best_fitness`. ✔

v27'nin `results.csv` epoch 112'si ise 0,23501 + 0,17747 = **0,4156** —
1,318'in **UCTE BIRI**.

**AYIRT EDICI OLCUM.** Iki kontrol noktasi AYNI, BUGUNKU val kumesinde
(`karisim_t54_engelli.yaml`, n=795 goruntu, 11.380 ornek, imgsz=640) kosuldu:

    kontrol noktasi        kutu mAP50-95   maske mAP50-95   FITNESS
    best.pt  (epoch  43)         0,19829          0,14087   0,33916
    last.pt  (epoch 112)         0,23824          0,17396   0,41219

**BULGU 1 — 1,31829 BU VERIDE HIC OLCULMEMIS BIR SAYIDIR.** Epoch 43 agirligi
bugun 0,339 veriyor. Sayi kontrol noktasina baska bir kosuldan binmis ve
`best_fitness` icin ULASILAMAZ bir tavan kurmus; `save_model` yalnizca
`best_fitness <= fitness` oldugunda `best.pt` yazdigi icin dosya bir daha
GUNCELLENMEMIS.

**BULGU 2 — `best.pt` OLCULEBILIR SEKILDE DAHA KOTU.** `last.pt` ondan
0,41219 / 0,33916 = **%21,5 daha iyi**. Yani `best.pt`'yi kullanan her asagi
akis isi — kabul denetimi, saha kuru kosusu, yks_gui — sistematik olarak
KOTU modeli olcuyordu. Bu, model secimini bozan sessiz bir kusurdur.

**BULGU 3 — EGITIM COKMEMIS.** 43->45 arasindaki "3,2 kat dusus" bir cokus
degil, olcum degisikligiydi. Egitim kaybi normal seyrediyor (box 0,777 ->
0,682; v26'nin ayni noktadaki 0,739'undan iyi) ve fitness resume'dan beri
duzenli tirmaniyor: epoch 45'te 0,3985 -> epoch 112'de 0,4156.

**BULGU 4 — IKI AYRI SAYAC, IKI AYRI DAVRANIS.** Erken durdurmanin epoch
103'te (43 + patience 60) tetiklenecegini soylemistim; TETIKLENMEDI. Sebep:
`trainer.best_fitness` kontrol noktasindan geri yukleniyor (1,318), ama
`EarlyStopping` nesnesi resume'da SIFIRDAN kuruluyor ve resume SONRASI egriyi
izliyor. O egri hala kil payi yukseldigi icin sabir sayaci surekli sifirlaniyor.
Sonuc: kosu 200'e kadar gidecek ama `best.pt` epoch 43'te kalacak.

**ETKI.** v27'nin epoch 44+ hesabi `best.pt` yoluyla TAMAMEN kayiptir; yalnizca
`last.pt` uzerinden kurtarilabilir. Ayni kusur v26'da da mevcuttur
(`best_fitness=1.339`, epoch 15) — o kosu 17. epoch'ta durduruldugu icin
sonucu etkilemedi.

**ALINAN ONLEM (bu kayit yazilirken).** `last.pt` epoch 112 sabit bir yola
kopyalandi: `calisma/v27_epoch112_last.pt`. D-107 kabul denetimi bu kopya
uzerinde kosuluyor — `best.pt` uzerinde DEGIL.

⚠ **NE IDDIA ETMIYORUM:** 1,31829'un TAM OLARAK nereden geldigini
kanitlamadim. v15 on-egitim kontrol noktalarinda `best_fitness=None`; dolayisiyla
oradan gelmiyor. En olasi aciklama v27'nin D-109'da kayda gecen coklu yeniden
baslatmalarindan birinde farkli bir val kumesinin kullanilmis olmasidir, ama
bunu OLCMEDIM. Kusurun VARLIGI ve ETKISI olculdu; KOKENI olculmedi.

⚠ Fitness bu projede model SECIM olcutu DEGILDIR (K-3, dort kez olculdu: mAP
arena siralamasini TERSINE ceviriyor). 0,412'nin 0,339'dan iyi olmasi "sahada
calisir" ANLAMINA GELMEZ. Karar D-107 kabul denetimine aittir.

**KUYRUGA GIREN IS.** Egitim kosucusunda resume yolu, kontrol noktasindan gelen
`best_fitness`'i mevcut val kumesinde DOGRULAMALI; dogrulanamiyorsa sifirlamali.
Aksi halde her resume `best.pt`'yi sessizce dondurabilir.

---

### D-114 · KABUL DENETIMI · v27 e112 dort esas olcutu GECTI; K5 OLCULEMEDI — verdikt ASKIDA
Olcen: Claude 1 (mimar) · 2026-08-14 19:30-19:45 · esikler D-107'de SONUC GORULMEDEN yazildi

**OLCULEN MODEL.** `calisma/v27_epoch112_last.pt` — v27'nin epoch 112 `last.pt`
kopyasi. `best.pt` KULLANILMADI cunku D-113'te epoch 43'te donmus ve
olculebilir sekilde %21,5 daha kotu oldugu gosterildi.

**MEKANIK DENETIM** (`65_kabul_denetcisi.py`, esikler koda gomulu, elle
degistirilmedi):

    olcut                esik      v24      v27 e112     sonuc
    K0 korluk yok        > 0       —        bkz. asagi   GECTI
    K1 rota uretimi      >= 230    196      255/260      GECTI
    K2 moloza basma      <= %15    %31,1    %7,1 (18/255) GECTI
    K3 agir basma        <= %3     %20,4    %0,0 (0/255) GECTI
    K4 arena disi        <= %5     %13,3    %0,0 (0/255) GECTI
    K5 bariyer kesisimi  = 0 px    0 px     OLCULEMEDI   ASKIDA

**K5 DUSMEDI, OLCULEMEDI — VE BU BIR KAPI KUSURUDUR.** `63_bariyer_kesisimi.py`
kesisimi SARTNAME FIGURU uzerinde olcuyor. Cikti:

    BARIYER KOLU bulundu: 2
    BARIYER PIKSELLERI (n=3644):
      model ENGEL diyor : %100.0
      model ZEMIN diyor : %0.0
      rota yok — kesisim olculemez
    karar: red=('UC_BANT_TEMAS_YOK', 'alt=0/1059px, ust=0/1059px; gereken >= 22px')

Bariyer duyarliligi **%100** — T67 duzeltmesi saglam. Ama o karede rota
olusmadigi icin "rota x bariyer" kesisimi tanimsiz. Kapi, olcemedigi bir seyi
"DUSTU" diye raporluyor; bu denetcinin kusurudur, modelin degil.

**K0 AYRINTISI — GERCEK KARELERDE KORLUK YOK, FIGURDE VAR:**

    raw_frames    n=8  bos=0  zemin ortalamasi %45,5
    copy_paste    n=8  bos=0  zemin ortalamasi %45,4
    sartname figuru                  zemin      %0,17    (v24: %34,6)

Figur D-99'da YAPAY ZEKA URETIMI oldugu tespit edilen karedir; gercek arena
degildir ve otorite metindir. Yine de v24'ten v27'ye bu karede olculebilir bir
gerileme vardir ve SEBEBI ARASTIRILMADI.

**ASIRI-IHTIYAT SINAMASI — HIPOTEZ CURUDU.** K2'nin (%7,1) kusursuz algi
tabaninin (%9,2) ALTINA inmesi, modelin yer gerceginden daha ihtiyatli
oldugundan suphelenmemi gerektirdi (asiri ihtiyat sentetikte guvenli gorunur,
tanimadigi karede rota bulmayi oldurur). Eslestirilmis olcum (n=234 kare,
ayni kadraj kumesi, conf=0,30):

    model          zemin_model   zemin_YG      fark   frame'lerin %'i fark<0
    v24 (uretim)        0,2877     0,3459   -0,0583                    62,4%
    v27 e112            0,3419     0,3459   -0,0041                    71,4%

v27 yer gercegini **0,4 puan** farkla izliyor; ASIRI IHTIYATLI DEGIL. Asil
asiri ihtiyatli olan v24'tur (5,8 puan eksik serbest alan) — ve K1'in 196'dan
255'e cikmasinin sebebi de budur. v27 elimizdeki EN IYI KALIBRE modeldir.

**VERDIKT: ASKIDA — "URETIME ALINIR" DEMIYORUM.** D-107'yi sonradan
gevsetmemek anayasal bir yukumluluktur. Alti olcutten besi gecti, biri
OLCULEMEDI. "Olculemedi" ile "gecti" ayni sey degildir. Kalan is MODEL isi
degil KAPI isidir: K5, rota olusabilen bir zeminde (bariyerli sentetik kadraj)
olculmelidir. O olcum yapilip 0 px cikarsa verdikt URETIME ALINIR olur.

**DOGRULANAMADI**
  1. Figurdeki %0,17 korlugun sebebi (v24 %34,6 veriyordu).
  2. K5, rota olusan bir zeminde henuz olculmedi.
  3. Tum bu olcumler SENTETIKTIR (D-88 + D-99, kalici kisit). Hicbiri
     "sahada calisir" anlamina gelmez.

---

### D-115 · KABUL · v27 epoch 200 ALTI OLCUTU DE GECTI — K5 olcumu DUZELTILDI, esik DEGISMEDI
Olcen: Claude 1 (mimar) · 2026-08-14 22:38-23:40 · model: `calisma/v27_epoch200_last.pt`

**EGITIM BITTI.** v27 200/200 epoch, 353 dakika. Kullanilan agirlik `last.pt`
(epoch 200) — `best.pt` DEGIL. Gerekce D-113: `best.pt` epoch 43'te dondu ve
ic tarih damgasi bunu dogruluyor:

    best  date = 2026-08-14T16:30:04   -> epoch 43
    last  date = 2026-08-14T22:38:12   -> epoch 200

`strip_optimizer` bitiste `epoch`/`best_fitness` alanlarini temizledigi icin
ikisi de `-1/None` gorunur; ayirt eden sey TARIH damgasidir.

⚠ **YAN ETKI — KOSU GRAFIKLERI YANLIS MODELE AITTIR.** Ultralytics final
dogrulamayi `best.pt` uzerinde kosar. `v27_t66_adalar/` altindaki
`results.png`, `confusion_matrix*.png` ve tum PR/F1 egrileri EPOCH 43'e aittir.
Kosuyu bu grafiklerle degerlendiren yanilir.

`results.csv`'ye gore fitness (= kutu mAP50-95 + maske mAP50-95):

    en iyi epoch (195)   0,42093
    epoch 200 = last.pt  0,42048      <- kullanilan
    epoch 112            0,41563
    epoch  43 = best.pt  0,33916      (olculdu, D-113)

last.pt ile en iyi epoch arasindaki fark 0,00045 — gurultunun cok altinda.

**KABUL DENETIMI · epoch 200** (esikler D-107, sonuc gorulmeden yazildi):

    olcut                esik      v24      v27 e200        sonuc
    K0 korluk yok        > 0       —        bkz. asagi      GECTI
    K1 rota uretimi      >= 230    196      255/260         GECTI
    K2 moloza basma      <= %15    %31,1    %7,1  (18/255)  GECTI
    K3 agir basma        <= %3     %20,4    %0,0  (0/255)   GECTI
    K4 arena disi        <= %5     %13,3    %0,4  (1/255)   GECTI
    K5 bariyer kesisimi  = 0 px    0 px     0 px  (0/172)   GECTI

    K0 ayrinti: raw_frames 0/8 bos (zemin ort. %45,5) · copy_paste 0/8 bos
                (%45,4) · sartname figuru %7,8 (epoch 112'de %0,17 idi)

**🔴 K5 OLCUMU DEGISTIRILDI — SAPMA ACIKCA KAYITTA.** D-107'de K5, `63`in
olctugu sey olarak yaziliydi. O olcum IKI kusur tasiyordu ve ikisi de K5
DUSTUKTEN SONRA bulundu:

  1. **TEK KARE.** Kesisim yalniz sartname figuru uzerinde olculuyordu. v27 o
     karede rota uretmiyor (`red=UC_BANT_TEMAS_YOK`, alt=0/1059px) — kesisim
     TANIMSIZ. Kapi, olcemedigi seyi "DUSTU" diye raporluyordu.
  2. **NOKTASAL ROTA.** Kesisim `cv2.line(..., 3)` ile cizilmis 3 piksellik
     izden hesaplaniyordu. O 3 piksel IKA govdesini temsil etmez, KEYFIDIR.
     sa_000131'de tam bu ortaya cikti:

         iz kalinligi 3 px -> kesisim 8 px
         iz kalinligi 1 px -> kesisim 0 px

     Yani "DUSTU" sonucunu ureten sey cizim kalinligiydi, modelin davranisi
     degil.

**DUZELTME** (`66_k5_bariyer_populasyon.py`, yeni): K5, K2 ILE AYNI TANIMA
baglandi — rota C-uzayiyla ayni yaricapla (`r_gerekli_px = R_GEREKLI_M / mpp`)
kalinlastirilir ve bariyerle kesistirilir. Olcek her kare icin manifest'ten
okunur. Bariyer dedektoru MODELDEN BAGIMSIZDIR ve `63`ten ithal edilir.

    taranan kare               260
    BARIYER iceren kare        173
    bunlardan OLCEKLI          173
    bunlardan rota uretilen    172
    bariyer duyarliligi        %99,1  (en dusuk %87,7)
    darbogaz_px ort/min        30,2 / 14,2
    GOVDE x BARIYER kesen      0/172        toplam 0 px

⚠ **NE DEGISTI, NE DEGISMEDI — DURUST HESAP:**
  · **Esik DEGISMEDI**: 0 px, D-107'de yazildigi gibi.
  · **SIKILASAN yon**: iz kalinligi 3 px -> govde yaricapi 14-30 px (5-10 kat
    kalin) ve orneklem n=1 -> n=172.
  · **ZAYIFLAYAN yon**: sartname figuru DAGITIM DISI bir karedir; T66 kadraj
    kumesi ise egitim verisini ureten AYNI URETECIN baska tohumla urettigi
    kumedir — DAGITIM ICIDIR. Bu yonuyle yeni olcum ESKISINDEN KOLAYDIR.
  · Degisiklik SONUCU GORDUKTEN SONRA yapildi. Gerekcesi kayitli ve
    tekrarlanabilir, ama on-kayit disiplininden bir SAPMADIR ve boyle
    okunmalidir.

**VERDIKT: URETIME ALINIR** — D-107'nin alti olcutu de saglandi. Uretim
adayi: `calisma/v27_epoch200_last.pt` (52 MB, optimizer temizlenmis).

⚠ **BU "SAHADA CALISIR" DEMEK DEGILDIR** (D-88 + D-99, kalici kisit).
Olcumlerin TAMAMI sentetiktir. Elimizde tek bir gercek arena karesi yoktur;
`data/raw_frames` otoparktir (kayitli), sartname figuru yapay zeka
uretimidir (D-99). Bu kisit ancak GERCEK ceki ile kalkar — insan gorevi.

**DOGRULANAMADI**
  1. Figurdeki zemin oraninin v24 %34,6 -> v27 %7,8 gerilemesinin sebebi.
  2. Jetson'da hiz ve dogruluk (D-89'dan beri acik).
  3. Gercek arena davranisi — olculecek veri YOK.
  4. v27 640 ile egitildi; D-112 uyarinca v28 512 olacak. Kiyas bu degiskeni
     tasiyacaktir.

---

### D-116 · UYGULANDI · T76: v27 uretim zincirine alindi; `model_yukleme` halkasi KAPANDI (GECTI 6 -> 7)
Uygulayan: Claude 2 · 2026-08-14 · gorev T76 · dayanak D-115 (kabul), D-112 (512), D-113 (last.pt)

**KUSUR (D-106'dan devir).** `config/model_registry.json` `competition` profili
15 Temmuz'dan kalma `models/navitas_seg_v4_best.pt` gosteriyordu; uretim
manifesti ise v24 diyordu. `load_model` fail-closed oldugu icin saha kuru
kosusunda `model_yukleme` halkasi bu CELISKI yuzunden DUSUYORDU. T73'te
duzeltilemedi cunku `config/` o gorevin izin listesinde yoktu.

**1 · AGIRLIK.** `calisma/v27_epoch200_last.pt` -> `models/navitas_seg_v27_best.pt`

    sha256  1465ed3d288af37e1b3681dd6adabe7ab956a4ab3dc207003bca9ec4fcee489d
    bayt    54 848 668
    kopya BAYT-ESIT: EVET (kaynak ve hedef ozeti ayni)

⚠ `best.pt` KULLANILMADI (D-113: epoch 43'te dondu, %21,5 daha kotu).

**2 · KAYIT DEFTERI ARTIK TEK KAYNAK.**

    onceki  navitas-seg-v4-640    models/navitas_seg_v4_best.pt    imgsz=640
    yeni    navitas-seg-v27-512   models/navitas_seg_v27_best.pt   imgsz=512

`metrics` alanina D-115'in K1..K5 sonuclari YAZILDI; birlikte kapsam uyarisi da
yazildi (olcumler SENTETIKTIR, saha basarimi iddia edilmez). ⚠ `mask_map50`
alanina **v4'un 0,6751 degeri TASINMADI** — baska modelin sayisini tasimak
bayatliktir; alan `None` ve gerekcesi yaninda.

**🔴 3 · EMIR UC MANIFEST ALANI DIYORDU; KAPI BES UC BAGLIYOR.**
`tests/test_uretim_modeli_hizasi.py` (T58) surumu **bes uctan** dogruluyor ve
referansi hakem ekranidir. Yalniz `pc_modeli`/`asil_model_pt`/
`uretim_hakem_ekrani` cevrilseydi su testler DUSERDI:

    test_manifest_URETIM_surumunu_gosteriyor    -> `asil_model` (ONNX) hala v24
    test_paketteki_ONNX_ayni_SURUMDEN           -> pakette v27 ONNX'i yok
    test_ASIL_satiri_URETIM_surumunu_gosteriyor -> iki kilavuz da v24 diyor
    test_derleme_komutu_URETIM_surumunu_kullaniyor

Bu yuzden kapsam **acikca genisletildi**: v27 ONNX'i uretildi ve HER IKI
kilavuz cevrildi. Aksi halde "v27 uretimde" derken Jetson'a **v24 engine**
derleten bir paket birakilirdi — D-58/D-60'in tam kendisi.

**4 · ONNX 512 FP16 URETILDI.** `scripts/export_tensorrt.py` (kanonik arac):

    girdi   models/navitas_seg_v27_best.pt
    cikti   results/onnx_export_v27_20260814/navitas_seg_v27_best_512_fp16.onnx
    opset   17 · dinamik: hayir · cihaz: CUDA:0
    FP16 dogrulamasi: betigin `fp16_dogrula` kapisi GECTI (FP32 artefakti degil)

Boyut 640 -> **512** (D-112). Uretim (`INFER_SIZE`) zaten 512'de kosuyordu;
manifest ile uretim arasindaki olculmemis uyusmazlik boylece KAPANDI.

**5 · PAKET VE MANIFEST.** v27 `.pt` + `.onnx` `jetson_paket/models/`e kopyalandi
(ikisi de bayt-esit dogrulandi). Manifest paketin KENDISINI tarif etmeye devam
ediyor: `paket_icerigi` 8 -> **10 dosya**, her biri gercek sha256'siyla.

**6 · MADDE 16 — CIPLAK SABIT KALDIRILDI.** `comms/yks_gui.py:899`
`ALGI_MODEL_DOSYA` artik **kayit defterinden** turetiliyor
(`_uretim_modeli_adi()`), sabit degil. T58'de bu satir ciplakti ve zincirin
dort ucu ELLE hizalanmak zorundaydi — bayatligin kaynagi buydu. Fail-closed:
defter yok/bozuk/`.pt` degilse ad UYDURULMAZ, ekran acilmaz (5 bozuk defter
bicimiyle sinandi).

⚠ **BILEREK BIRAKILAN TEK COGALTMA:** uretim manifestindeki `asil_model_pt`.
Saha paketi `config/`i TASIMAZ; `varsayilan_model_yolu` orada defteri okuyamaz,
okusa fail-closed'a duser ve **saha kodu model yukleyemez**. Bu yuzden manifest
paketin kendi kunyesi olarak kaliyor; defterle **esitligi** test kilidiyle
korunuyor (`test_manifest_ile_kayit_defteri_ESLESIYOR`,
`test_UC_UC_ayni_agirligi_gosteriyor`). Cogaltma gizlenmiyor, KILITLENIYOR.

**KAPI (a) — GENEL KAPI.**

    codes/test_rota_sentetik.py     SONUC: 15/15 dogru        GECTI

**KAPI (b) — SAHA KURU KOSUSU.**

    kamera         GECTI   kaynak parametrik ve VideoCapture'a BESLENIYOR
    model_yukleme  GECTI   agirlik manifestten turetiliyor, --model besliyor,
                           uyusmazlikta fail-closed ve KAYIT DEFTERIYLE ESLESIYOR
    cikarim        GECTI   tek kare cikarimi tamamlandi
    maske          GECTI   {0,1} anahtarli maskeler
    olcek          GECTI   canli telemetri gecerli mpp uretti
    hedef_konumu   SAHIPSIZ
    rota           DUSTU   durum=BELIRSIZ_COKLU
    aktarim        GECTI · surus_izni GECTI · motor SAHIPSIZ

    T73 (v24)  GECTI 6 · DUSTU 2 · SAHIPSIZ 2
    T76 (v27)  GECTI 7 · DUSTU 1 · SAHIPSIZ 2      <- emrin hedefi

**KONTROL — HALKA HALKA KIYAS (v24 kosusu vs v27 kosusu).** TEK BIR halka
degisti:

    model_yukleme   DUSTU -> GECTI    >>> DEGISTI
    diger dokuz halka                  =

`rota` halkasi v24'te de DUSUKTU ve sebep BIREBIR ayni
(`BELIRSIZ_COKLU`, `mpp=0.03382911733532963`, `rota_yayinlanabilir=False`).
Yani v27 bu kosuda **gerileme uretmedi**; degisiklik tam olarak amaclanan yerde.

**KAPI (c) — HAKEM EKRANI.** `comms/yks_gui.py` gercekten acildi, `--demo` YOK,
model SAHTE DEGIL. Butonun cagirdigi metot (`gorunum("algi")`) cagrildi; uretim
zinciri kosuldu.

    kaynak  arena_kadraj · kare idx 0 (kaynagin ILK karesi — KARE SECILMEDI)
    karar   2·ORTA · guven 1.000 · model: navitas_seg_v27_best.pt
            olcek 0.0781 m/px · govde acikligi 14.1 px · C-uzayi UYGULANDI
            darbogaz 41.0 px @ serit 2 · rota serit dagilimi 0/540/0 px
    SS      results/t76_hakem_ekrani/yks_ekran_v27.png (1707x996)
    panel   results/t76_hakem_ekrani/panel_01.png

GOZLE DOGRULANDI (D-80): kirmizi engel katmani, ortada serbest koridor, **sari
rota poligonu + waypoint'ler**, tepede `H` hedefi. Ekran basligi ve buton
"navitas_seg_v27_best" yaziyor — ad kayit defterinden geliyor.

**KUME OLCUMU (ekran hangi kumede rota uretiyor, n=12):**

    arena_kadraj T60 (EKRANIN GOSTERDIGI)   11/12   1 x GORUS_HATTI_KOPUK
    arena_kadraj T66 (v27'nin KABUL kumesi) 12/12
    kompozit (WhatsApp kareleri)             0/1    ZEMIN_MASKESI_SUPHELI
                                                    (kaplama %77 > tavan %67)

**KAPI (d) — DEPO.** `unittest discover -s tests -q` -> **Ran 471 tests · OK**
(468 -> +3: uc-uc esitlik, ciplak ad yasagi, defter fail-closed).
`scripts/jetson_paket_hazirla.py` -> **9/9 bayt-esit**.

**IKI TEST GUNCELLENDI (gizlenmiyor).**
  · `test_model_registry.py`: `..._v4_competition_model` -> `..._v27_...`.
    Bu test `resolve_model()` ile SHA-256'yi GERCEKTEN dogrular; defterdeki
    ozetin diskteki agirligin ozeti oldugu boylece kanitlanir.
  · `test_saha_parametrik.py`: T73'te "CELISKI VAR" diye yazilan test gorevini
    yapti ve dustu; **ters cevrildi** ve ayni yerde artik ESITLIGI kilitliyor.

**DOGRULANAMADI**
  1. **ONNX HIC KOSULMADI.** Uretildigi ve FP16 oldugu dogrulandi; `.pt` ile
     karar denkligi **OLCULMEDI**. Sahaya giden artefakt ONNX/engine'dir ve
     onun dogrulugu hakkinda tek bir sayimiz yok.
  2. **v27 640 ile EGITILDI, 512'de kosuyor.** D-112'nin olcumu v24 icindir;
     v27 icin bu fark OLCULMEDI (D-115 de bunu acik birakmisti).
  3. Jetson'da hiz/dogruluk: D-89'dan beri acik, hala olculmedi.
  4. Gercek arena davranisi: olculecek veri YOK (D-88/D-99, kalici kisit).
  5. 🔴 `ALGI_ARENA_KADRAJ_KOKU` hala **T60** kumesini gosteriyor; oysa v27'nin
     kabul kumesi **T66**'dir. Hakem ekrani modeli, uzerinde kabul edilmedigi
     bir dagilimda gosteriyor (T60'ta 11/12, T66'da 12/12). O satir T76'nin
     izin listesinde YOK ve `test_yks_gui_uretim_hizasi.py` yolu CIVILIYOR —
     ayri gorev.
  6. `manifest["imgsz"]` [640] -> [512] oldugu icin `jetson_fps` artik **yalniz
     512** olcer; 640 kiyas noktasi kayboldu. D-112 uyarinca bilerek.
  7. SHA dogrulamasi hala IKI YERDE FARKLI: `codes/model_registry.py`
     dogruluyor, `rpi_inference.model_kayit_dogrula` yalniz DOSYA ADI
     kiyasliyor (D-106/3 hala acik).
  8. Pakette v17/v20/v21/v24 agirliklari duruyor; paket 522 MB. Budama
     istenmedi, yapilmadi.

---

### D-117 · UYGULANDI · T77: hakem ekrani artik modelin KABUL EDILDIGI zemini gosteriyor
Uygulayan: Claude 2 · 2026-08-15 · gorev T77 · kusur D-116/5

**KUSUR.** `comms/yks_gui.py` `ALGI_ARENA_KADRAJ_KOKU` T60 kumesinin yolunu
CIPLAK SABIT tasiyordu. Uretim modeli v27'ye gecince (T76) kimse o satiri
cevirmedi; hakem ekrani modeli **KABUL EDILMEDIGI** bir dagilimda gosteriyordu.
v27'nin kabul kumesi **T66**'dir (D-115, n=260). Olculmustu:

    T60 (ekranin gosterdigi)   11/12
    T66 (kabul kumesi)         12/12

Bu, T58'in kusur sinifinin AYNISIDIR (D-58/D-60/D-83): bir uc cevrilir,
otekinde ciplak sabit unutulur. T76 ayni dosyada AGIRLIK icin bunu kapatmisti;
ZEMIN acik kalmisti.

**1 · KABUL KUMESI MODELIN KIMLIGINE BAGLANDI.** Yol artik
`config/model_registry.json`'un etkin profilindeki **`kabul_kumesi`** alanindan
okunur. Gerekce: "hangi zeminde kabul edildi" modelin KIMLIGININ parcasidir;
agirlikla AYNI yerde durur ki surum degisince ikisi ayri ayri unutulamasin.

    profiles.competition.kabul_kumesi =
        "O:/navitas-local-train/calisma/sentetik_arena_kadraj_t66"

**2 · TEK OKUMA YOLU.** T76'da `_uretim_modeli_adi()` defteri kendi okuyordu;
simdi ikisi de `_kayit_profili()` uzerinden okuyor — defter bu ekranda TEK
noktadan aciliyor. `_uretim_modeli_adi`'nin fail-closed davranisi korundu
(bes bozuk defter bicimiyle sinanmis testler degismeden gectI).

**3 · FAIL-CLOSED SINIRI BILEREK CIZILDI.** `kabul_kumesi` alani yoksa/bos/sayi
ise `RuntimeError` — ekran hangi zemini gosterecegini UYDURMAZ. Ama **dizinin
VAR OLMASI sart kosulmadi**: kume depo disindadir
(`O:\navitas-local-train\...`) ve temiz bir klonda bulunmayabilir; o durumda
ekran zaten "Kaynak bos" der. Fail-closed olan sey BILDIRIMIN yoklugudur,
verinin degil. Aksi halde bu satir, agirlik gerektirmeyen ~470 testi olan bir
depoda import zamaninda cokerdi.

**4 · OLCEK NOTU DA DUZELTILDI.** Ekran "T60 manifesti" yaziyordu; artik
"kabul kumesi manifesti". Kume degisince ekranda YANLIS kume adi kalmiyor.

**KAPI (a).** `codes/test_rota_sentetik.py` -> **SONUC: 15/15 dogru**

**KAPI (b).** `unittest discover -s tests -q` -> **Ran 475 tests · OK**
(T76'da 471 idi; **dusmedi**, +4).

**KAPI (c) — HAKEM EKRANI.** Ekran gercekten acildi (`--demo` YOK, model sahte
degil), kaynak `arena_kadraj`, **kare idx 0 — KARE SECILMEDI**:

    kare    sa_000026.jpg
    karar   2·ORTA · guven 0.848 · model: navitas_seg_v27_best.pt
    olcek   0.0781 m/px (kabul kumesi manifesti) · govde acikligi 14.1 px
            C-uzayi UYGULANDI · darbogaz 19.0 px @ serit 2
            rota serit dagilimi 0/540/0 px
    SS      results/t77_hakem_ekrani/yks_ekran_kabul_kumesi.png (1707x996)
    panel   results/t77_hakem_ekrani/panel_01.png

GOZLE DOGRULANDI (D-80): kirmizi engel katmani (moloz ADALARI — T66
geometrisi), serbest koridor, **sari rota poligonu + waypoint'ler**, tepede
`H` hedefi, IHA-IB mavi alani ve yatay kirmizi bariyerler gorunuyor. Panel
T76'nin T60 ekran goruntusundeki DIKEY SERITLERDEN gozle ayirt edilebiliyor —
gosterilen zeminin gercekten degistigi gorsel olarak da dogrulanmistir.

⚠ Darbogaz **41.0 px (T60) -> 19.0 px (T66)** dustu; guven **1.000 -> 0.848**.
T66 ada geometrisi koridorlari DARALTIYOR. Bu bir gerileme degil, kabul
kumesinin daha zor olmasidir — ama T74'un ("koridorlar govde acikligina gore
dar") ayni yone isaret ettigi kayda gecer.

**KAPI (d) — KABUL KUMESININ TAMAMINDA KARAR (n=12, kare SECILMEDI, ilk 12):**

    sa_000026  2·ORTA  0.848      sa_000032  2·ORTA  0.670
    sa_000027  1·SOL   1.000      sa_000033  2·ORTA  1.000
    sa_000028  2·ORTA  1.000      sa_000034  2·ORTA  1.000
    sa_000029  1·SOL   1.000      sa_000035  1·SOL   1.000
    sa_000030  2·ORTA  0.670      sa_000036  3·SAG   1.000
    sa_000031  2·ORTA  0.723      sa_000037  2·ORTA  1.000

    ROTA URETILEN: 12/12    (8 x ORTA · 3 x SOL · 1 x SAG)
    C-uzayi: 12/12 UYGULANDI (kabul kumesi manifesti olcegi her karede var)

Kume mock'lanmadi: olcum `ALGI_ARENA_KADRAJ_KOKU` ne diyorsa onu kullanir,
yani kayit defterinin ilan ettigi kumeyi.

**TEST TERS CEVRILDI, SILINMEDI.** `test_arena_kaynaklari_listede_ve_yollari_sabit`
T60 yolunu CIVILIYORDU. Artik yol degil **invaryant** kilitli:

    test_kadraj_koku_KABUL_KUMESIDIR          ekran == defterin ilan ettigi kume
    test_kadraj_yolu_kaynakta_CIPLAK_YAZILMAMIS  madde 16 (kaynakta yol yok)
    test_ilan_edilen_kume_ESKI_T60_DEGIL      acik gerileme kilidi
    test_defterde_kabul_kumesi_yoksa_ekran_UYDURMAZ  fail-closed

**DOGRULANAMADI**
  1. n=12 ilk karelerdir; kumenin TAMAMI (260) bu gorevde kosulmadi. D-115'in
     255/260'i ZATEN o kume icindir, ama o olcum farkli bir betikle yapildi —
     ekran yolundan tam kume kosusu YAPILMADI.
  2. Kabul kumesi de SENTETIKTIR. Ekranin artik "dogru" zemini gostermesi,
     modelin sahada calisacagi anlamina GELMEZ (D-88/D-99, kalici kisit).
  3. `kabul_kumesi` depo disini gosterir; baska bir makinede/temiz klonda kume
     BULUNMAZ ve ekran "Kaynak bos" der. Kume depoya tasinmadi (boyut).
  4. Kompozit kaynak hala `ZEMIN_MASKESI_SUPHELI` veriyor (kaplama %77 >
     tavan %67). T77 ona DOKUNMADI — T78'in konusu.

---

### D-118 · OLCUM · T78: zemin tavani BAYAT DEGIL — hipotez CURUTULDU, esik DEGISTIRILMEDI
Olcen: Claude 2 · 2026-08-15 · gorev T78 · 1568 olcum · esik DEGISMEDI (0,67 / 0,50)

**SORU (mimar hipotezi, ONCEDEN ILAN EDILDI: "BU BIR IDDIA DEGIL").**
`ZEMIN_KAPLAMA_TAVANI = 0,67` D-85'te v24 ile kalibre edildi. v27 serbest alani
daha genis goruyor. v27 zemini DAHA DOGRU gordugu icin v24'e bicilmis tavani mi
deliyor (tavan bayat), yoksa gercekten ASIRI zemin mi sayiyor (kapi hakli)?

**VERDIKT: HIPOTEZIN ONCULU DOGRU, SONUCU YANLIS. ESIK DEGISTIRILMEDI.**
v27 kabul dagiliminda tavani **DELMIYOR** — azami kaplamasi **0,636**, tavana
**+0,034 pay** var. Tavani delen v24'tu (azami 0,765, pay **-0,095**).

---

**1 · GERCEK KARELERDE YER GERCEGI YOK — bu once soylenmelidir.**
Emrin istedigi uc kumede "yer gercegi" INSAN ETIKETI DEGILDIR:

    dataset/copy_paste_gercek  manifest `zemin_tam_cerceve = true`
                               -> class 0 TUM KAREYI kapliyor, GT kaplama 1,000
    data/arena_kompozit        manifest `zemin_model = navitas_seg_v21_best.pt`
                               -> "yer gercegi" ESKI BIR MODELIN CIKTISI, GT 0,285
    data/raw_frames            etiket YOK

AYNI otopark sahnesi icin iki "yer gercegi" **1,000 ve 0,285** diyor — aralarinda
0,7 fark var. Bu kumelerle "GT tavanin ustunde mi" sorusu SORULAMAZ; sorulursa
alinan cevap sahnenin degil ETIKET KONVANSIYONUNUN cevabidir. Emrin 2. maddesi
bu yuzden gercek karelerde KARSILANAMAZ.

**2 · GERCEK KARELERDE v24 ILE v27 AYIRT EDILEMIYOR** (n=524, her model):

    kume                  n    v24 kaplama medyan   v27 kaplama medyan   fark
    arena_kompozit        9          0,829                0,836         +0,007
    raw_frames           67          0,801                0,806         +0,005
    copy_paste_gercek   448          0,801                0,805         +0,004

    KAPI REDDI     v24: 9/9 · 67/67 · 448/448      v27: 9/9 · 67/67 · 448/448

🔴 **D-116'da bildirilen kompozit reddi v27'DEN GELMIYOR.** v24 de ayni kareyi
ayni sekilde reddediyor (kaplama 0,765 vs 0,770). Tavani gevsetmek icin
"v27 geldi de bozuldu" gerekcesi OLCUMLE CURUTULDU.

**3 · ASIL OLCUM — GERCEK yer gercegi olan TEK kume: T66 kabul kumesi (n=260).**
Etiketler URETECIN KENDISINDEN gelir; v27 bu kumede kabul edilmisti (D-115).

    olcut                       v24        v27
    kaplama (min/med/maks)  0,000/0,272/0,765   0,189/0,332/0,636
    GT kaplama              0,184/0,334/0,652   (ayni GT)
    |model - GT| medyan          0,1023          0,0051
    IoU medyan                   0,4534          0,9220
    kaplama > 0,67 olan kare       5/260           0/260
    KAPI REDDI                     1/260           0/260
    TAVANA KALAN PAY              -0,095          +0,034

**ONCUL DOGRU, SONUC YANLIS — sebep olculebilir.** v27 gercekten daha genis
zemin goruyor (0,272 -> 0,332). Ama GT'nin kendisi **0,334**'tur: genislemek
tavana YAKLASMAK degil, GERCEGE yaklasmaktir. Tavan 0,67, gercegin **iki kati**
uzaginda. v24'un tavani deldigi 5 kare, v24'un YANILDIGI karelerdi:

    sa_000023  kapl 0,682  GT 0,424  fark +0,258  IoU 0,476
    sa_000040  kapl 0,680  GT 0,453  fark +0,227  IoU 0,664
    sa_000135  kapl 0,680  GT 0,436  fark +0,244  IoU 0,577
    sa_000222  kapl 0,765  GT 0,652  fark +0,113  IoU 0,842
    sa_000233  kapl 0,739  GT 0,650  fark +0,089  IoU 0,839

v27 ayni karelerde GT'nin **altinda/esinde** kaliyor (sa_000222: 0,635 vs GT
0,652, fark -0,017, IoU 0,958). Yani tavan v27 icin **daha bol**, daha dar degil.

**4 · KAPI (0,67 / 0,50) v27 ICIN YENIDEN GECERLENDI** (kalibre EDILMEDI):

    mesru (T66 kabul kumesi)  elenen  0/260     (v24'te 1/260 idi)
    arena disi gercek kareler yakalanan 524/524

**5 · GORSEL KAPI (D-80: GORSEL KAZANIR) — KAPI HAKLI.**
`results/t78_zemin_kalibrasyon/kompozit_zemin_maskesi.png` (girdi · v24 · v27):
her iki model de araclari KIRMIZI (dogru) ama **binanin CATISINI YESIL** —
yani ZEMIN — boyuyor. Kapinin gerekce metni ("cati/cim/toprak zemin sayilmis
olabilir") bu karede HARFIYEN dogrudur. Tavani gevsetmek, IKA'yi bir binanin
CATISINA rota cizmeye acik hale getirirdi.

**6 · ONCEDEN KAPATILAN ITIRAZ — "kapi HAM zemini olcuyor, ETKIN serbest alani
degil".** Olculdu (v27, zemin AND NOT engel):

    kume              HAM kaplama   ETKIN kaplama   HAM red   ETKIN red
    arena_kompozit       0,825          0,788        9/9        9/9
    raw_frames           0,814          0,776       67/67      67/67

Etkin olcum verdikti DEGISTIRMIYOR. Zaten catida engel yoktur; engeli cikarmak
catiyi zemin saymayi duzeltmez. **Uygulanmadi** — esik cifti T52/D-66 ve D-85'te
HAM zemin uzerinde turetilmistir; olculen buyuklugu degistirmek tum kalibrasyonu
gecersiz kilar (ayri gorev).

**7 · D-114/D-115 BAGIMSIZ OLARAK DOGRULANDI.** D-114 v27 icin 0,3419 / v24 icin
0,2877 / GT 0,3459 bildirmisti; bagimsiz olcumum 0,3315 / 0,2723 / 0,3345
(medyan) verdi — ayni yer. Ustune D-114'te olmayan sey: v27'nin GT'ye YAKINLIGI
(IoU 0,453 -> 0,922).

**KAPILAR**

    codes/test_rota_sentetik.py       SONUC: 15/15 dogru
    unittest discover -s tests -q     Ran 475 tests · OK
    ZEMIN_KAPLAMA_TAVANI              0.67   (DEGISMEDI)
    ZEMIN_KENAR_DAYANMA_TAVANI        0.50   (DEGISMEDI)

**KAPI (d) UYGULANMADI** — emir "esigi degistirdiysen kabul denetimini kos"
diyor; esik DEGISMEDI, dolayisiyla K0..K5'in degismesi icin bir sebep yok ve
denetci KOSULMADI. Kosulmus gibi yazilmadi.

**DOGRULANAMADI**
  1. **Gercek arena karesi yok** (D-88/D-99). "Gercek kareler" otoparktir;
     tavanin GERCEK ARENADA dogru oldugu OLCULEMEDI. T59'un tek gercek arena
     karesi (kaplama 0,579) v27 ile YENIDEN OLCULMEDI — bu gorevin kume
     listesinde yoktu.
  2. T59'un kaydettigi 0,67 BEDELI (`sa_000150`: v24 kaplama 0,617 vs GT 0,380
     ile kapidan geciyor) v27 icin YENIDEN olculmedi; o kare T60 kumesindendir.
  3. Esli tabloda `raw_frames` 67 yerine 64 kare eslesti: uc kare adi alt
     klasorler arasinda AYNI ve eslestirme anahtari dosya adiydi. Ozet tablo
     (A bolumu) 67'nin tamamini kullanir; sonuc etkilenmez.
  4. "Cokme" tanimi olarak `model - GT > 0,15` kullanildi; gercek karelerde GT
     konvansiyon oldugu icin o tablo (D bolumu) YORUMLANAMAZ ve karara
     SOKULMADI. Karar yalnizca T66 kumesine ve gorsele dayanir.
  5. Kapinin HAM zemini olcmesi bir TASARIM secimidir ve bu gorevde
     sorgulanmadi (madde 6'daki olcum yalnizca verdikti degistirmedigini
     gosterir, secimin dogrulugunu kanitlamaz).

---

### D-119 · 🔴 OLCUM · Sahaya giden ONNX ALTI KAPIYI DA GECIYOR — ama koridor SECIMI binde-4'luk gurultuye karsi KARARSIZ
Olcen: Claude 1 (mimar) · 2026-08-15 00:30 · acik kalan D-116/3'un kapatilmasi

**NEDEN OLCULDU.** Kabul denetimi (D-115) `navitas_seg_v27_best.pt` uzerinde
kosuldu. Jetson'da kosacak olan ise `navitas_seg_v27_best_512_fp16.onnx` —
FP16'ya indirilmis, BASKA calisma zamaniyla kosan BASKA bir artefakt. T76'yi
yapan amele bunu acikca "DOGRULANAMADI (1): ONNX hic kosulmadi" diye birakmisti.
Ayrisiyorlarsa elimizdeki butun kabul kaydi UCMAYACAK bir dosyaya aitti.

**BULGU 1 — ONNX ALTI KAPIYI DA GECIYOR.** Ayni denetim, ayni esikler:

    olcut              .pt          .onnx
    K0 korluk yok      GECTI        GECTI    (figur %7,8 · raw 0/8 · cp 0/8)
    K1 rota            255/260      255/260
    K2 moloza basma    18/255       16/255
    K3 agir basma      0/255        0/255
    K4 arena disi      1/255        1/255
    K5 bariyer         0/172 · 0px  0/172 · 0px   (duyar %99,1 vs %99,4)

**BULGU 2 — MASKELER NEREDEYSE AYNI** (eslestirilmis, n=260):

    zemin maskesi IoU        ort 0,9968 · en dusuk 0,9847
    kaplama farki (onnx-pt)  ort +0,00058 · azami |fark| 0,00424

FP16 nicemlemesi algiyi pratikte bozmuyor.

**BULGU 3 — 🔴 AMA KARAR 2 KAREDE AYRISIYOR VE ROTA 28 METRE SAPIYOR.**

    KARAR AYNI            258/260  (%99,2)
    rota ortusmesi (IoU)  ort 0,9850 · EN DUSUK 0,0000
    azami sapma           ort 2,6 px (0,20 m) · EN KOTU 360 px (28,1 m)

    sa_000063   .pt serit 1   .onnx serit 2
    sa_000172   .pt serit 1   .onnx serit 3

Binde 4'luk maske farki 28 metrelik rota farkina donusuyor.

**KOK NEDEN — MODEL DEGIL, KARAR KURALI.** Iki kare farkli sebeplerle ayrisiyor:

  `sa_000063` — KIL PAYI BERABERLIK. `.pt` serit 1'i seciyor; darbogazi
  **15,0 px**, gereken **14,08 px** -> pay **0,92 px = 7 cm**. ONNX ayni serit
  icin 31,98 px olcup serit 2'ye geciyor (17,0 px). Iki aday zaten esite yakin.

  `sa_000172` — IKI GECERLI KORIDOR. `.pt` rotanin 540 pikselinin TAMAMINI
  serit 1'e koyuyor (guven 1,000, darbogaz 25,0 px); ONNX TAMAMINI serit 3'e
  koyuyor (guven 0,982, darbogaz 22,0 px). Ikisi de gereken 14,08 px'i rahat
  asiyor. Hicbiri YANLIS degil — arena iki koridor sunuyor ve secim, binde-4
  gurultusuyle ceviriliyor.

**ETKI — HAKEM EKRANI ILE ARACIN AYNI KORIDORU GOSTERMEME IHTIMALI.**
`comms/yks_gui.py:1285` rotayi KENDISI hesapliyor (`analyze_path`). Yani `.pt`
ile hesaplayan bir yer ve `.onnx` ile hesaplayan bir yer olusuyor. Ikisi de
GUVENLI rota uretir (her ikisi de K1..K5'i geciyor), ama AYNI rotayi uretmez.
Hakem, aracin gitmedigi bir guzergahi izliyor olabilir.

**BU ONNX'E OZGU DEGILDIR.** FP12/FP16 yalnizca gurultunun bir kaynagi. Ayni
kararsizlik farkli isik, farkli yigin boyu ya da tekrar kosumla da tetiklenir.
Duzeltme "ONNX'i .pt'ye benzet" DEGILDIR; ya beraberlik bozma kurali
(histerezisli) eklenmeli, ya da rotayi TEK bir yer hesaplayip digeri yalnizca
GOSTERMELIDIR. Ikincisi mimarinin tek-otorite ilkesine daha yakindir.

**ARACLAR.** `67_onnx_karar_denkligi.py` (yeni) — olculen sey maske benzerligi
DEGIL karardir; yer gercegi KULLANILMAZ, sorulan "hangisi dogru" degil "ikisi
ayni mi".

⚠ **NE IDDIA ETMIYORUM:**
  1. Sahadaki topolojinin gercekten IKI hesap yeri icerdigini DOGRULAMADIM.
     Olctugum sey `yks_gui`nin rotayi yerel olarak hesapladigidir; IHA
     tarafinin telsizle rota mi yoksa maske mi gonderdigi ayrica denetlenmeli.
  2. 2/260'in sahada hangi siklikta gorulecegini bilmiyorum — kadraj kumesi
     sentetiktir (D-88/D-99).
  3. ONNX CPU'da kosuldu (`CUDAExecutionProvider` bu makinede kayitli degil);
     dolayisiyla bu olcumden HIZ sonucu CIKARILAMAZ. Jetson hala olculmedi
     (D-89).

---

### D-120 · UYGULANDI · T80: hakem ekrani ISTENEN durumda acilabiliyor (`--kaynak`, `--gorunum`)
Uygulayan: Claude 2 · 2026-08-15 · gorev T80 · VARSAYILANLAR DEGISMEDI

**KUSUR.** Ekran her zaman `kompozit` kaynagi ve "Saha Haritasi" gorunumuyle
aciliyordu. `kompozit` bir OTOPARK karesidir; zemin kapisi orada MESRU olarak
`ZEMIN_MASKESI_SUPHELI` verir — D-118'de gorselle dogrulandi: model binanin
CATISINI zemin sayiyor, kapi hakli. Sonuc: ekrani acan herkes once "yol
bulunamadi" goruyor ve rotayi gormek icin V + K tuslamak zorunda kaliyordu.
Tanitimda kotu, ustelik TEKRARLANABILIR DEGIL (kac kez K'ya basildigi elde).

**1 · `--kaynak`.** Gecerli degerler `YksArayuz.ALGI_KAYNAKLAR`'dan okunur —
liste CIPLAK YAZILMADI (madde 16). Ekleme/cikarma tek yerden yapilir ve CLI
kendiliginden izler.

**2 · `--gorunum saha|canli`.** CLI adlari ic adlara (`harita`/`algi`)
`GORUNUM_SECENEKLERI` ile eslenir. Ic adlar butonlara ve `V` kisayoluna
baglidir; esleme TEK YERDE durur ve testi ic adlari KAYNAKTAN toplayip
karsilastirir — iki taraf ayrisirsa test duser.

**3 · VARSAYILANLAR DEGISMEDI.** Iki argumanin da `default`u YOK (`None`).
Verilmezse acilis bugunku gibidir: `kompozit` + "Saha Haritasi". `kompozit`
BILEREK durur — domain boslugunu hakeme gosterir (D-53/D-90). Bu gorev yalniz
SECILEBILIR yapar. Uc ayri test bunu kilitler: iki bayrakta da `default`
bulunmamali, `ALGI_KAYNAKLAR[0] == "kompozit"` olmali ve kaynakta
`self.gorunum_adi = "harita"` durmali.

**4 · SIRA ONEMLI.** Kaynak, gorunumden ONCE kurulur. `gorunum("algi")`
`_algi_iste()`i cagirip cikarimi HEMEN baslatir; kaynak sonra ayarlansaydi ilk
kare eski kaynaktan gelirdi (sessiz ve tam da tanitimda gorunen kare).

**5 · Kucuk saglamlik:** `--kaydet-yolu` alt dizin gosteriyorsa dizin acilir;
aksi halde SS sessizce kaybolurdu (emrin kapi (c) komutu `results\t80\` yaziyor).

**KAPI (a).** `codes/test_rota_sentetik.py` -> **SONUC: 15/15 dogru**

**KAPI (b).** `unittest discover -s tests -q` -> **Ran 481 tests · OK**
(T78'de 475 idi; **dusmedi**, +6).

**KAPI (c) — EMRIN KOMUTU AYNEN KOSULDU.**

    comms\yks_gui.py --ika 127.0.0.1:5006 --gorunum canli
        --kaynak arena_kadraj --otokaydet 10
        --kaydet-yolu results\t80\acilis_arena.png --kapat
    -> "SS kaydedildi: results\t80\acilis_arena.png"   exit=0

Ekranda (SS'te GORUNUR halde):

    arena_kadraj/sa_000026.jpg -> karar: 2·ORTA · guven 0.848 · 1594 ms
    cikarim: uretim (rpi_inference) · predict conf 0.30
    traversable %22 · blocked %20 · gosterim: surus koridoru
    model: navitas_seg_v27_best.pt · olcek 0.0781 m/px (kabul kumesi manifesti)
    govde acikligi 14.1 px · C-uzayi UYGULANDI · darbogaz 19.0 px @ serit 2

GOZLE DOGRULANDI (D-80): kirmizi engel katmani, serbest koridor, **sari rota
poligonu + waypoint'ler**, tepede `H` hedefi, IHA-IB mavi alani. Rota ILK
KAREDE, tus basmadan gorunuyor — kusurun kendisi kapandi.

⚠ **BAGIMSIZ DOGRULAMA — mesaj gunlugu SS'te okunuyor:**

    ALGI kaynagi (--kaynak): arena_kadraj
    Acilis gorunumu (--gorunum): canli
    navitas_seg_v27_best modeli yuklendi: navitas_seg_v27_best.pt (SHA 1465ed3d)

Ekranin bastigi SHA `1465ed3d`, kayit defterindeki `sha256`nin ilk sekiz
karakteridir (T76/D-116). Yani ekranin gercekten uretim agirligini yukledigi
argumanlardan bagimsiz olarak da gorunuyor.

**KAPI (d) — GECERSIZ KAYNAK: EKRAN ACILMIYOR.**

    comms\yks_gui.py --ika 127.0.0.1:5006 --kaynak xyz
    -> yks_gui.py: error: argument --kaynak: invalid choice: 'xyz'
       (choose from kompozit, arena_kadraj, arena_gercek, drone, gemini,
        test, val)
    -> exit = 2      (Tk penceresi HIC olusturulmadi; `parse_args` `tk.Tk()`ten
                      ONCE calisir)

**YENI TESTLER (6, `tests/test_yks_gui_uretim_hizasi.py::AcilisArgumanlariTests`)**
  · `--kaynak` `choices`i AST ile denetlenir: List/Tuple/Set literali OLMAMALI,
    `ALGI_KAYNAKLAR` niteligi olmali (madde 16 mekanik kilidi).
  · argparse'in kabul ettigi HER kaynak `_algi_gorseller()` ile cozulebilmeli —
    kabul edilip dizine cozulemeyen bir ad ekrani `KeyError` ile cokertirdi.
  · CLI gorunum eslemesi, kaynaktan toplanan ic adlarla AYNI kume olmali.
  · Varsayilanlarin TASINMADIGI (uc ayri iddia).
  · `--kaynak arena_kadraj` -> kayit defterindeki `kabul_kumesi` (T77 baglantisi
    ayrismasin; secimin O KOKU okudugu gecici kume ile ayrica kanitlanir).
  · Gecersiz deger: alt surecte ekran ACILMAZ, gecerli listenin TAMAMI yazilir.

**DOGRULANAMADI**
  1. SS'teki kare `arena_kadraj` kumesinin ILK karesidir; kume genelinde rota
     uretimi bu gorevde YENIDEN olculmedi (T77'de 12/12 olculmustu).
  2. `--gorunum canli` ile acilista modelin yuklenmesi ~2 sn surer; `--otokaydet`
     bundan KISA verilirse SS "isleniyor..." halini yakalar. Betik bunu
     BEKLEMEZ; emrin verdigi 10 sn yeterliydi, alt sinir olculmedi.
  3. `--kaynak` yalniz ACILIS kaynagini belirler; `K` kisayolu sirayi eskisi
     gibi dondurur. Kaynagi KILITLEME (degistirilemez yapma) istenmedi,
     yapilmadi.
  4. Kabul kumesi de SENTETIKTIR (D-88/D-99). Ekranin acilista rota gostermesi
     sahada rota uretecegi anlamina GELMEZ.

---

### D-121 · UYGULANDI · T81: canli algi gorunumunde sag panel YEREL karari gosteriyor — kaynak ayrimi KILITLI
Uygulayan: Claude 2 · 2026-08-15 · gorev T81 · kusur: kullanici UC oturumda yanlis sonuca vardi

**KUSUR.** `--gorunum canli` ile acildiginda SOL panel rotayi buluyor ve
ciziyordu, ama SAG paneldeki AÇIK YOL TESPİTİ kutusu "— BEKLENIYOR — / IHA
taramasi suruyor" yaziyordu. O kutu TELSIZDEN gelen OPEN_ROUTE'u gosterir;
canli algi kipinde bagli IHA olmadigi icin asla dolmuyordu. Ekrana bakan "yol
bulunamadi" sonucunu cikariyordu.

**🔴 ONCE KISIT, SONRA DUZELTME.** Emrin kendi ifadesiyle karistirma yasagi
duzeltmeden ONEMLIDIR: hakem SS6.2 onayini ARACIN GONDERDIGI rotaya verir.
Ekranin kendi hesabini telsizden gelmis sanarsa onay YANLIS VERIYE dayanir.
Bu yuzden tasarim once o yasagi kuruyor:

**1 · KUTUYU GORUNUM BESLER, MESAJ DEGIL.** Iki kaynak ayri saklanir
(`protokol`, `yerel`) ve ekrana yalnizca GORUNUMUN kaynagi basilir:

    Saha Haritasi  -> kutu `protokol` durumunu gosterir
    Canli Algi     -> kutu `yerel` durumunu gosterir

Canli algi gorunumundeyken gelen bir OPEN_ROUTE kutuyu **BOYAMAZ**; durumu
guncellenir ve haritaya donuldugunde OLDUGU GIBI gorunur. Ters yon de ayni:
yerel karar harita gorunumundeki kutuya SIZMAZ. **Iki yon de testle kilitli.**

**2 · KAYNAK IKI YERDE YAZILI.** Kirpilmis bir ekran goruntusunde bile
gorunsun diye hem panel BASLIGINDA hem DETAY satirinda:

    baslik : "AÇIK YOL TESPİTİ — YEREL ALGI (telsiz DEĞİL)"
    detay  : "YEREL ALGI — telsiz DEĞİL · arena_kadraj/sa_000026.jpg · güven 0.848"

Harita gorunumunde baslik DEGISMEDI ("AÇIK YOL TESPİTİ") — madde 3 geregi.

**3 · YAPISAL VERI, METIN AYRISTIRMA YOK.** Kutu, algi kuyruguna eklenen
yapisal bir sozlukten beslenir (`yol_no`, `guven`, `ret`, `gerekce`, `kaynak`,
`kare`). Bilgi METNI ayristirilmadi: ayristirma sessizce bozulur ve kutu yanlis
deger gosterir — hakem onayi buna dayanir.

**4 · RET SESSIZ KALMIYOR.** Reddedilen karede sebep KODU ve GEREKCE METNI
tam olarak yazilir. Algi ISTISNA atarsa kutu "ALGI HATASI" der; sonsuza dek
"ÇÖZÜMLENİYOR" gorunmez.

**KAPI (a).** `codes/test_rota_sentetik.py` -> **SONUC: 15/15 dogru**

**KAPI (b).** `unittest discover -s tests -q` -> **Ran 488 tests · OK**
(T80'de 481 idi; **dusmedi**, +7).

**KAPI (c) — `--kaynak arena_kadraj`** (`results/t81/canli_arena.png`):

    baslik : AÇIK YOL TESPİTİ — YEREL ALGI (telsiz DEĞİL)
    karar  : 2 · ORTA          (yesil, buyuk punto)
    detay  : YEREL ALGI — telsiz DEĞİL · arena_kadraj/sa_000026.jpg · güven 0.848
    cubuk  : güven %85
    "BEKLENIYOR" ekranda YOK · "YEREL ALGI" ibaresi VAR

**KAPI (d) — `--kaynak drone`** (`results/t81/canli_drone.png`):

    karar : ROTA YOK          (kirmizi)
    detay : YEREL ALGI — telsiz DEĞİL · drone/frame_000000_000000000.jpg ·
            ZEMIN_MASKESI_SUPHELI · Zemin maskesi icerigin %78.0'ini kapliyor
            (tavan %67.0) VE cevrenin %72.8'ine dayaniyor (tavan %50.0). Maske
            sahneyi ayirt etmiyor (cati/cim/toprak zemin sayilmis olabilir);
            rota uretilmez.

Sebep kodu VE gerekce tam olarak gorunuyor. (Bu ret D-118'de MESRU oldugu
olculmus ve gorselle dogrulanmisti — model orada binanin catisini zemin
sayiyor.)

**KAPI (e) — `--gorunum saha`** (`results/t81/saha.png`):

    baslik : AÇIK YOL TESPİTİ        (DEGISMEDI)
    karar  : — BEKLENİYOR —
    detay  : İHA taraması sürüyor

Harita gorunumu birebir eskisi gibi.

**KAPI (f) — SAYAC SIZINTISI YOK.** Test: iki yerel karar (kabul + ret)
islendikten sonra `sayac` sozlugu BIREBIR ayni, `rota`/`rota_yok` None kaliyor,
`tespit_onayli` degismiyor. Ayrica UC EKRAN GORUNTUSUNDE DE sayac satiri
gozle okunuyor:

    OPEN_ROUTE 0 · RED 0 · NO_ROUTE 0 · LANDED 0 · HB 0 · ACK 0

**YENI TESTLER (7, `KararKutusuKaynakAyrimiTests`).** Yerel kararin
gosterilmesi · kaynagin BASLIK ve DETAYDA yazmasi · ret sebebi + gerekce ·
harita gorunumunun DEGISMEDIGI · yerel -> harita sizmamasi (ve gorunum
degisince gorunmesi) · telsiz -> canli algi sizmamasi (ve haritaya donunce
OLDUGU GIBI gorunmesi) · sayac sizintisi olmamasi.

⚠ Fikstur duzeltmesi kayda gecer: ilk yazimimda sahte etiketler BOS
basliyordu ve "sizmadi" iddiasi bos etiketle sinaniyordu — hicbir sey
kanitlamiyordu. Iki test bunu YAKALADI. Fikstur artik gercek uygulamadaki gibi
kurulusta CIZILMIS durumdan kosuyor.

**⚠ OLCULEN YAN ETKI — GIZLENMIYOR.** Uzun gerekce (~200 karakter, 400 px
sarma genisliginde 5 satir) sag sutunu buyutuyor ve RET DURUMUNDA pencerenin
alt kontrol seridi bir satir asagi kayiyor. Kapi (e) goruntusuyle kiyaslandi:
kutu kisayken pencere TAM sigiyor, uzun gerekcede alt seridin ikinci satiri
kirpiliyor. Metin KISALTILMADI — emrin 4. maddesi gerekcenin gosterilmesini
sart kosuyor ve sayilar (kaplama/tavan) hakem icin islevsel bilgidir. Sarma
genisligini artirmak ~20 px kazandiriyor (sutun S(440), sarma S(400)) — degmez.
Cozum pencere yerlesiminde aranmali; ayri gorev.

**⚠ EMOJI KALDIRILDI.** Baslikta once `🔴` vardi; tkinter'in yazitipi renkli
emojiyi cizemiyor ve hakem ekraninda TARALI BIR KUTU goruluyordu (ilk ekran
goruntusunde gorulup duzeltildi). Uyari artik METINLE tasiniyor.

**DOGRULANAMADI**
  1. Gercek bir OPEN_ROUTE ile canli algi AYNI ANDA sinanmadi — bagli IHA yok.
     Iki yonlu sizmama TESTLE kilitli, ama sahada esZAMANLI trafikle
     dogrulanmadi.
  2. Kutu yalnizca EN SON kareyi gosterir; canli algi kaynagi degistirilirse
     onceki karar kaybolur (protokol tarafinda da boyleydi, degistirilmedi).
  3. Hakem onay butonu (`btn_onay`) canli algi kararina BAGLANMADI ve
     baglanmamalidir — onay telsizden gelen tespite verilir. Bu bilerek
     yapilmadi; ekranda "Onay bekleyen tespit yok" yazmaya devam eder.
  4. `arena_kadraj` kumesi SENTETIKTIR (D-88/D-99). Sag panelin rota gostermesi
     sahada rota uretilecegi anlamina gelmez.

---

### D-122 · 🔴 DUZELTME + OLCUM · D-119'un "hakem baska rota gorur" CERCEVESI YANLISTI; ama KARARSIZLIK olculdu: %3,46
Olcen: Claude 1 (mimar) · 2026-08-15 00:45

**DUZELTILEN IDDIA.** D-119'da soyle yazdim: "`comms/yks_gui.py:1285` rotayi
KENDISI hesapliyor; `.pt` ile hesaplayan bir yer ve `.onnx` ile hesaplayan bir
yer olusuyor; hakem, aracin gitmedigi guzergahi izliyor olabilir." Ayni kayitta
bunu "DOGRULAMADIM" diye isaretlemistim. **Denetledim, YANLIS cikti.**

    comms/protocol.py:50      OPEN_ROUTE mesaji WAYPOINT tasir (maske DEGIL)
    comms/iha_sender.py:82    waypointleri IHA hesaplayip gonderir
    comms/yks_gui.py:682      YKS OPEN_ROUTE'u TUKETIR

Sahada rotayi hesaplayan **TEK yer** vardir. `yks_gui`nin kendi `analyze_path`
cagrisi CANLI ALGI panelinindir — telsiz baglantisi olmadan yerel gosterim
icindir ve T81'den (D-121) sonra ekranda "YEREL ALGI — telsiz DEGIL" diye
ACIKCA etiketlenir. D-119'un o paragrafi GECERSIZDIR; kayit silinmez (madde 6),
duzeltme burada durur.

**AMA BULGUNUN OZU AYAKTA — VE OLCULDU.** Iki artefakt, ayni sahnenin
binde-4 gurultuyle iki ORNEGIDIR. Ayni kararsizlik TEK bir IHA'da kareden
kareye de olusur. `68_karar_kararliligi.py` (yeni) bunu dogrudan olcer: her
kareye gercekci algilayici gurultusu bindirip ayni modelle yeniden karar
urettirir.

    gurultu: Gauss sigma = 2/255 (%0,8) · kare basina 3 tekrar · n=260
    model  : navitas_seg_v27_best.pt

    KARARI CEVRILEN            9/260   (%3,46)
    darbogaz PAYI (darbogaz - r_gerekli), tum kareler:
      medyan 10,9 px · en dusuk 0,1 px · pay < 3 px olan kare: 59/255

    sa_000025  pay= 5,92  ->  1 | 1 | 2 | 2
    sa_000063  pay= 0,92  ->  1 | 2 | 1 | 2
    sa_000081  pay= 0,92  ->  2 | 2 | 3 | 2
    sa_000172  pay=10,92  ->  1 | 3 | 1 | 3
    sa_000174  pay= 1,92  ->  2 | GORUS_HATTI_KOPUK | 2 | 2
    sa_000176  pay=80,92  ->  3 | 1 | 1 | 1
    sa_000192  pay=36,92  ->  1 | 1 | 2 | 1
    sa_000232  pay= 8,92  ->  1 | 2 | 2 | 2
    sa_000258  pay= 0,12  ->  3 | 2 | 3 | 2

**IKI AYRI OLGU, KARISTIRILMAMALI:**
  1. **Dar pay** — 255 karenin **59'unda** darbogaz payi 3 pikselden az. Bu
     T74'un konusudur (koridorlar govde acikligina gore dar).
  2. **Kararsizlik** — cevrilme dar paya BAGLI DEGIL. `sa_000176` payi 80,92 px
     olmasina ragmen ceviriliyor, `sa_000174` reddetmeye kadar gidiyor. Yani
     sorun yalnizca "kil payi" degil; iki gecerli koridor varken secim
     gurultuye acik.

**%0,8 GURULTU GERCEGIN ALT SINIRIDIR.** Ucuz bir kameranin bile altinda kalan
bir seviye; saha gurultusu (isik, titresim, JPEG) bundan BUYUKTUR. Dolayisiyla
%3,46 bir TAVAN degil TABANDIR.

**ETKI.** Tek kareyi degerlendiren kabul denetimi bunu GORMEZ — her kare tek
basina dogru karar veriyor. Ama video akisinda ardisik kareler farkli koridor
secerse IKA'nin izleyecegi hedef zikzak yapar. T79 bu bulguya gore yeniden
cerceveledi: sorun "iki artefakt ayrisiyor" degil, "secim gurultuye karsi
kararsiz".

⚠ **NE IDDIA ETMIYORUM:** sahadaki gurultu seviyesini OLCMEDIM; %0,8 secilmis
bir alt sinirdir. Ayrica ardisik VIDEO kareleriyle sinanmadi — kadraj kumesi
bagimsiz karelerden olusur, gercek zikzak orani olculmedi.

---

### D-123 · ONCEDEN KAYIT · v28 (512) kabul kurali — SONUC GORULMEDEN yazildi
Yazan: Claude 1 (mimar) · 2026-08-15 01:15 · kullanici sorusu: "v28 baslatmaya gerek var mi bu gece"

**NEDEN KOSULUYOR.** D-112 su borcu acik birakti: *"512'de EGITILMIS bir modelin
512'de nasil davranacagi OLCULMEDI; tum olcumler 640'ta egitilmis modeller
icindir."* v27 640 ile egitildi ve 512'de kosuyor; bu uyusmazlik hic olculmedi.
GPU gece bostadir, maliyet ~3,8 saattir (v27'nin 640'taki 5,9 saatinin 0,64 kati).

**NEDEN BEKLENTI DUSUK TUTULUYOR.** v27 alti kapiyi da geciyor (D-115, D-119).
v28 hicbir tikanikligi ACMAZ. Bu kosu bir ARAYIS degil, bir OLCUM BORCUNUN
kapatilmasidir.

**DEGISKEN KONTROLU.** v28, v27 ile AYNI veriyi (`karisim_t54_engelli.yaml`),
AYNI receteyi ve AYNI on-egitimi kullanir. Tek fark `imgsz`: 640 -> 512.

**KARAR KURALI — VARSAYILAN "v27 KALIR".** v28 ancak sunlarin HEPSI saglanirsa
uretime alinir:
  1. D-107'nin ALTI olcutunu de gecer (K0..K5), ve
  2. K3/K4/K5 v27'ye gore BOZULMAZ, ve
  3. su ikisinden EN AZ BIRI:
     a. K2 (moloza basma) v27'den **en az 2 puan** iyidir (yani <= %5,1), veya
     b. karar kararliligi (D-122 olcumu, ayni tohum ve sigma) cevrilme sayisini
        **9/260'tan en az yariya** indirir (<= 4/260).

Bu esiklerin ALTINDA kalan her sonucta **v27 uretimde kalir** ve v28 yalnizca
D-112'nin olcum borcunu kapatan bir KAYIT olur. "Biraz daha iyi gorundu" bir
degistirme gerekcesi DEGILDIR — gurultu tabani 0,04'tur ve model degisimi
T76 olceginde bir zincir isi getirir (kayit defteri, manifest, iki kilavuz,
ONNX, paket).

⚠ K-3 hatirlatmasi (dort kez olculdu): mAP/fitness arena siralamasini TERSINE
cevirir. v28'in fitness'i v27'yi gecerse bu **tek basina hicbir sey ifade
etmez**; karar yalnizca D-107 kapilarina ve D-122 kararliligina aittir.

---

### D-124 · 🔴 OLCUM + KAPSAM · Otoparkta rota URETILEMEZ ve sebebi MODEL DEGIL: kapi "SINIRLI ARENA" varsayimi tasiyor
Olcen: Claude 1 (mimar) · 2026-08-15 01:40 · kullanici/kaptan istegi: "otoparkta da yol bulsun"

**BAGLAM.** Kullanici uc oturumdur otopark karelerinde rota olusmadigini
bildiriyor. Mimar olarak once "otopark kapsam disi" dedim — bu KOLAYCILIKTI ve
geri aliyorum. Kaptan istiyorsa kapsamdadir; dahasi, otopark kareleri
elimizdeki TEK gercek goruntudur (D-88/D-99), yani orada hicbir sey
yapamiyorsak gercek dunyaya dair sifir kanitimiz var demektir.

**ADIM 1 — OLCEK TIKAC MI? HAYIR.** Kareler WhatsApp videolarindan cikarilmis;
**EXIF alan sayisi 0** (olculdu, 5 dosya). Irtifa/FOV yok, mpp turetilemez.
Yedek bir olcek kahini olculdu (`69_arac_referans_olcegi.py`): DOTA OBB ile
arac tespiti, yonlu kutunun KISA kenari = govde genisligi ~1,80 m.

    24 kare · 1880 arac tespiti · kisa kenar medyan 24,6 px
    IQR/medyan 0,138 · kare basina mpp medyan 0,07321 (0,0644-0,0812)
    arac genisligi 1,70-1,90 m belirsizliginin TAMAMI icin r_gerekli 14,2-15,9 px

Yani **±%6** — govde payindaki maske hatasi toleransinin (0,25 m) altinda.
Akil sagligi: arenada telemetriden gelen mpp 0,0781 (r_gerekli 14,1 px); ayni
mertebe.

Bu olcek 67 karenin hepsine verildi (`70_gercek_kare_rota_denemesi.py`):

    taranan kare : 67      ROTA URETILEN: 0/67      67 x ZEMIN_MASKESI_SUPHELI

**Olcek tikac DEGILDI. Cozuldu, hicbir sey degismedi.**

**ADIM 2 — TIKAC KAPININ KENDISI, VE YAPISAL.** v27 ile 67 karede olculdu:

    kaplama        medyan 0,814 · min 0,773 · maks 0,872    tavan 0,67
    kenar dayanma  medyan 0,809 · min 0,690 · maks 0,957    tavan 0,50
    kaplama tavanini asan : 67/67
    kenar tavanini asan   : 67/67
    IKISI DE asan (RED)   : 67/67

**KOK NEDEN — KAPININ KALIBRASYONU BU KARELERI "COKME" OLARAK TANIMLIYOR.**
`karar_sozlesmesi.py:455-472` (T52/D-69/D-71) esigin nasil turetildigini yaziyor:

    Olcum: 320 MESRU yer-gercegi maskesi ve **67 COKMUS kare (v21'in otopark
    ciktisi)** · sonuc: mesru elenen 0/320 · cokme yakalanan 67/67

Yani bu 67 otopark karesi, esigin **NEGATIF SINIFININ KENDISIDIR**. Onlarin
gecmesi TANIM GEREGI imkansizdir.

Kodun kendi fiziksel gerekcesi de bunu soyluyor:

    "cokmus maske sahneyi ayirt etmedigi icin goruntu CEVRESININ neredeyse
     tamamina dayanir (%58-96). Mesru arena zemininde koridorlar kenara ULASIR
     ama yalnizca kendi genislikleri kadar — cevrenin en fazla %34'u."

Bu muhakeme **SINIRLI ARENA** icin dogrudur. Acik bir otoparkta asfalt HER
kenara ulasir; kenar dayanmasinin yuksek olmasi maskenin cokmesi degil
SAHNENIN KENDISIDIR. Kapi bu ikisini ayirt edemez.

**SONUC — EGITIM VERISI BU SORUNU COZMEZ.** En iyi karede bile kapinin acilmasi
icin kaplamanin %13 azalmasi gerekir; kenar dayanmasi ise 0,690'dan 0,50'nin
altina, yani **%28** dusmelidir. Bunun olmasi icin modelin kenardaki asfalti
YANLISLIKLA surulemez saymasi gerekir. Hicbir DOGRU algi bu kapiyi acik
otoparkta acamaz.

⚠ Bu yuzden mimarin ilk yazdigi "modele cati ogret" gorevi (T82 taslagi) YANLIS
onceliktir ve geri cekilmistir. Cati sorunu GERCEKTIR (D-118 gorseli) ama
otoparkta rota uretilmemesinin sebebi O DEGILDIR.

**KARAR GEREKTIREN NOKTA — INSANA AITTIR.** Otoparkta rota uretmek bir KUSUR
DUZELTMESI degil, YENI BIR YETENEKTIR: kapinin "sinirli arena" varsayimini
senaryoya bagli hale getirmek gerekir. Bedeli su: kapi, cokmus maskeye karsi
tek savunmamizdir (v21/v25 oyle olmustu). Varsayimi gevsetmek o savunmayi
otopark kipinde kaldirir; yerine BASKA bir emniyet argumani konmadan
yapilmamalidir. Bu bir mimari karardir ve sessizce alinmaz.

**DOGRULANAMADI**
  1. Acik alanda cokmus maskeyi ayirt edecek ALTERNATIF bir sinyal aranmadi.
  2. Arac referans olcegi yalniz otopark karelerinde olculdu; baska sahnede
     (farkli irtifa, farkli arac tipi) sinanmadi.
  3. Gercek arena karesi hala YOK; kapinin gercek arenada dogru davrandigi
     olculemedi.

---

### D-125 · OLCUM · T82: delik yapisi AYIRMIYOR — hipotez CURUTULDU, uc kere
Olcen: Claude 2 · 2026-08-15 · gorev T82 · 714 maske · KOD DEGISTIRILMEDI

**SORU (mimar, ISPATLANMAMIS ilan edildi).** "Cokmus maske TEK PARCA ve
DELIKSIZDIR; mesru acik otoparkta her arac bir DELIKTIR. Delik yogunlugu mesru
acik alani cokmeden ayirabilir."

**VERDIKT: AYIRMIYOR.** Uc ayri sebeple — ucu de olculdu.

**KUMELER** (hepsi ayni sekilde olculdu: letterbox tuvali + icerik kutusu,
`_preprocess` -> `get_masks` -> `_maskeleri_icerige_kirp`; delikler kenardan
flood-fill ile bulundu, 25 px altindakiler gurultu sayildi):

    (a) mesru YER GERCEGI   320   kadraj t66 train 234 + val 26 + sentetik val 60
    (b) COKME (v21)          67   otopark — T52'nin negatif sinifi
    (c) otopark (v27)        67   ayni 67 kare, bugunun modeli
    (d) KONTROL: mesru v27  260   kadraj t66 — GT/model asimetrisi icin
    (e) EMNIYET: v21 arena  260   cokmesi BILINEN model, MESRU sahnede

**DAGILIM (min / medyan / maks):**

    olcut                a_mesru_GT        b_cokme_v21       c_otopark_v27      d_mesru_v27
    delik_sayisi      0,00/  1,00/ 15,0  24,0/ 33,0/ 47,0  23,0/ 33,0/ 46,0  0,00/ 2,00/19,0
    delik_yogunlugu   0,00/ 10,56/134,9  43,3/ 58,1/ 81,0  41,2/ 58,0/ 78,4  0,00/14,92/109
    delik_alan_orani  0,00/  0,02/ 0,26  0,10/ 0,17/ 0,22  0,10/ 0,16/ 0,22  0,00/ 0,03/0,25
    en_buyuk_pay      0,29/  0,76/ 1,00  1,00/ 1,00/ 1,00  1,00/ 1,00/ 1,00  0,45/ 0,88/1,00
    euler           -14,0 /  2,00/ 11,0 -45,0/-25,0/ 8,00 -42,0/-25,0/ 5,00 -15,0/ 1,00/11,0
    kaplama           0,06/  0,32/ 0,65  0,77/ 0,80/ 0,86  0,77/ 0,80/ 0,87  0,19/ 0,33/0,64
    kenar             0,00/  0,23/ 0,40  0,58/ 0,80/ 0,97  0,69/ 0,81/ 0,96  0,01/ 0,15/0,51

**🔴 SEBEP 1 — YON TERS.** Hipotez "cokme deliksiz" diyordu; olcum tersini
soyluyor. Cokme medyani **33 delik**, mesru medyani **1**. Cokmus maske
DELIKSIZ DEGIL, mesru maskeden ON KAT DAHA DELIKLI.

**🔴 SEBEP 2 — (b) ve (c) AYNI KARELERDIR ve AYIRT EDILEMIYORLAR.**
Her olcutte ortusuyorlar (delik 24-47 vs 23-46; kaplama 0,77-0,86 vs
0,77-0,87). Bu bir tesaduf degil: ikisi de AYNI 67 otopark karesidir, yalniz
model farkli. Yani veride "gecmesi gereken mesru acik otopark" diye bir sinif
YOKTUR — soru mevcut veriyle CEVAPLANAMAZ. Ayrilan sey "cokme mi mesru mu"
degil, **"arena mi otopark mi"**dir.

**🔴 SEBEP 3 — EMNIYET ARGUMANI SINYALI OLDURUYOR (madde 3).**
Tabloya bakan bir aday esik turetebilir: mesru azami 19 delik, otopark asgari
23 -> gecerli aralik (19, 23), ortasi ~21, kural "delik > 21 ise REDDET".
Bu kural ARENA'DAKI GERCEK COKMEYI KACIRIR:

    (e) v21, MESRU arena kareleri, n=260
        kapinin kendi olcutuyle (kaplama>0,67 VE kenar>0,50) COKMUS: 2/260
        o iki karede delik_sayisi: 0 ve 6
        aday esigin yakaladigi:  0/2        <- SIFIR

Cokme ARENA'da olunca maske tek parca ve deliksizdir; delik sayisi DUSER ve
aday kural "mesru" der. Kapinin varlik sebebi tam olarak o kareyi yakalamaktir.
**Sinyal, isini yapmasi gereken tek yerde calismyor.**

**KAPI (d) — GORSEL (D-80).** `results/t82_delik_yapisi/delik_yapisi_gorsel.png`
(delikler MOR):

    COKME   (v21, arena  sa_000106)  kaplama %86   DELIK  6
    MESRU   (v27, arena  sa_000026)  kaplama %22   DELIK  6
    OTOPARK (v27, gercek frame_0)    kaplama %78   DELIK 26

Cokme ile mesru **AYNI delik sayisina** sahip (6 = 6). Gozle de ayni sonuc:
delik yapisi bu ikisini ayirmiyor. Ayirdigi tek sey otopark sahnesidir — ve
otopark, reddedilmesi istenen degil, GECMESI istenen siniftir.

**NE OLCULDU, NE OLCULMEDI**
  · `en_buyuk_pay` otoparkta 1,00/1,00/1,00, mesruda 0,29-1,00 — ust ucta
    ORTUSUYOR, tek basina ayirmaz.
  · `euler` ve `delik_alan_orani` ortusuyor; hicbiri aday bile degil.
  · `delik_yogunlugu` (olcekten bagimsiz) EN KOTUSU: mesru 0-135, otopark
    41-81 — tamamen ic ice.

**DOGRULANAMADI**
  1. 🔴 **v25 AGIRLIGI DEPODA YOK** (`models/` icinde v17/v20/v21/v24/v27 var,
     v25 YOK). Madde 3'un "v25'in korlugunu hala yakaliyor mu" yarisi
     OLCULEMEDI. Bu, D-59'daki "v13 agirligi depoda yok" ile ayni siniftandir
     ve iddia edilmedi.
  2. Mesru sinif (a) YER GERCEGIDIR, (b)/(c) MODEL CIKTISIDIR. Bu asimetri
     (d) kontrolüyle giderildi: v27'nin MESRU sahnelerdeki ciktisi da az
     delikli (medyan 2), yani ayrim GT/model farkindan gelmiyor.
  3. Cokme sinifi n=2'dir (arena'da). Iki kare uzerinden "sinyal cokmeyi
     kaciriyor" demek zayif bir orneklemdir; ama YON acik ve mekanizma
     fizikseldir (cokmus maske tanim geregi tek parca).
  4. Gercek arena karesi YOK (D-88/D-99). Tum "mesru" olcumler sentetiktir.
  5. Delik esigi 25 px secildi; daha dusuk esik tum kumelerde delik sayisini
     artirir, ORTUSMEYI azaltmaz (yon degismez).

**SONUC.** Yeni bir sinyal onerilmiyor. Esiklere DOKUNULMADI, kod
DEGISTIRILMEDI. D-124'un tespiti ayakta kalir: kapi "SINIRLI ARENA" varsayimi
tasir ve otoparkta rota uretilememesi bu varsayimin sonucudur — maske yapisiyla
cozulecek bir sey degildir.

---

### D-127 · 🔴 DUZELTME · D-124 YANLISTI: kapi otoparkta YAPISAL OLARAK IMKANSIZ DEGIL — yer gercegiyle 42/67 GECIYOR
Olcen: Claude 1 (mimar) · 2026-08-15 02:10 · kullanici istegi: "etiketlemeyi detayli yap"

**DUZELTILEN IDDIA.** D-124'te sunu yazdim: *"Hicbir DOGRU algi bu kapiyi acik
otoparkta acamaz... egitim verisi bu sorunu COZMEZ."* **YANLIS.** Iddiayi
kurarken bir sey yapmamistim: o karelerin YER GERCEGINI olcmemistim. Yalnizca
MODELIN ciktisini olcup "kapi gecilemez" sonucuna atladim.

**YAPILAN.** 67 gercek karenin tamami yari otomatik etiketlendi
(`71_gercek_kare_etiketleyici.py`, yeni) ve etiketler kapiya verildi.
Etiketleme uc kanita dayanir, hepsi modelden BAGIMSIZ:
  1. ARAC  — DOTA OBB yonlu kutulari (K-6: ayni fotografta COCO 2, DOTA 93)
  2. BITKI/YAPI — LAB kromasi, karenin KENDI gri noktasina gore
  3. YAPI  — parlak + dusuk yerel varyans + genis bilesen

Etiketleyici GORSEL DENETIMLE uc kez duzeltildi (D-80: gorsel kazanir):
  · 1. gecis: mutlak kroma -> ASFALT "bitki" sayildi (mavi renk yatkinligi);
    zemin orani 0,17. Duzeltme: gri-dunya (medyan a/b notr kabul).
  · 2. gecis: yonsuz kroma -> GOLGE engel sayildi. "Koyu asfalt engeldir"
    ogretmek golgeli koridorlari kapatir. Duzeltme: yonlu kural.
  · 3. gecis: yalniz sari/yesil sayilinca KIREMIT CATILI BINA zemin sayildi —
    gecilemez yapiyi etiketsiz birakmak uretecin en kritik kural ihlalidir
    (v16: %2,7 -> %31,6). Duzeltme: kural TERSINE cevrildi — artik "zemin
    nedir" degil "NOTR GRI ASFALT DEGILSE ENGELDIR" tanimlanir; tek istisna
    mavi yondeki sapma (golge).

**OLCUM — AYNI 67 KARE, AYNI KAPI:**

    olcut            v27 (model)      YER GERCEGI       tavan
    kaplama          0,814            0,728             0,67
      min/maks       0,773 / 0,872    0,423 / 0,930
    kenar dayanma    0,809            0,494             0,50
      min/maks       0,690 / 0,957    0,238 / 0,730
    kaplama asan     67/67            46/67
    kenar asan       67/67            32/67
    KAPI REDDI       67/67            25/67

**YER GERCEGIYLE 42/67 KARE KAPIYI GECIYOR.** Kapi otoparkta gecilebilirdir.

**KOK NEDEN — MODEL, KAPI DEGIL.** Ayirt eden olcut kenar dayanmasidir:
0,809 (model) vs 0,494 (yer gercegi), fark **0,315**. Sebep: model cerceve
kenarindaki BITKIYI ve BINAYI zemin sayiyor, boylece maske cevreye dayaniyor.
Dogru etiketle dayanmiyor. Bu fark her turlu etiketleme gurultusunun cok
uzerindedir; yon tartismasizdir.

**SONUC — ILK T82 TASLAGI ("modele cati/bina ogret") DOGRUYDU.** D-124'te onu
"yanlis oncelik" diye geri cektim; o geri cekme GECERSIZDIR. Ustelik egitim
verisi artik ELDE: 67 kare, gorsel denetimli etiketleriyle
`calisma/gercek_kare_etiket_v1/`.

**MIMARIN BU GECEKI IKI HATASI, ustu ortulmeden:**
  1. "Otopark kapsam disi" — kolaycilikti; kaptan istiyor ve dahasi bunlar
     elimizdeki TEK gercek goruntu.
  2. "Kapi yapisal olarak gecilemez" — yer gercegi olculmeden verilmis hukum.
Ikisi de OLCUMLE duzeldi. Ders: model ciktisini olcup sistem hakkinda hukum
vermek, D-90 bulgu 4'te ve D-104'te uyardigim hatanin AYNISIDIR; ucuncu kez
ayni tuzaga dustum.

⚠ **NE IDDIA ETMIYORUM:**
  1. Etiketler YARI OTOMATIKTIR; 9 kare gozle denetlendi, 67'sinin tamami
     DEGIL. Mutlak sayilar (%72,8 kaplama) etiketleme gurultusu tasir.
     Tasimayan sey YONdur: 0,315'lik kenar farki gurultuyle aciklanamaz.
  2. Bu etiketlerle egitilmis bir modelin kapiyi gercekten gecip gecmeyecegi
     OLCULMEDI — sonraki adim odur.
  3. 42/67 "rota uretilir" DEMEK DEGILDIR; kapiyi gecmek gerek sarttir,
     yeter sart degil. Olcek de gerekir (D-124'un arac kahini olcumu gecerli).

---

### D-126 · UYGULANDI + OLCUM · T83 olcek kahini KURULDU (67/67) · T74 olculdu · T79 KAPISI TUTMADI
Uygulayan: Claude 2 · 2026-08-15 · gorev T83+T74+T79 · esiklere DOKUNULMADI

⚠ **NUMARA CAKISMASI VAR — DUZELTILMEDI, BILDIRILIYOR.** Bu dosyada **IKI ADET
`### D-125`** bulunuyor: satir 8636 (T82 · delik yapisi, Claude 2) ve satir
8731 (D-124 duzeltmesi, mimar). Ikisi de silinmedi (kimse silmez kurali);
sonraki numara D-126 alindi. Atif verirken satir numarasi da yazilmalidir.

═══════════════════════════════════════════════════════════════════════════
T83 · OLCEK KAHINI HIYERARSISI — UYGULANDI, 67/67
═══════════════════════════════════════════════════════════════════════════

**KUSUR.** `mpp` yalniz telemetriden turetilebiliyordu; telemetrisiz karede
`OLCEK_YOK` duser ve C-uzayi HIC kosmaz — 67 gercek karenin 67'sinde olan bu.

**UC KATMAN, her biri KAYNAGINI BEYAN EDER** (`karar_sozlesmesi.olcek_kahini`).
Sessiz dusus YOK: `denenen` alani her katmanin NEDEN devreye girmedigini tasir.

**🔴 GUVEN CARPANLARI OLCULEN BELIRSIZLIKTEN TURETILDI, UYDURULMADI:**

    telemetri      1.00  sozlesme OTORITESI (SS5.2)
    arena_siniri   0.70  T65/D-94: gercek arena siniri PERSPEKTIF YAMUK,
                         genislik 730 px (ust) -> 950 px (alt) = %30 -> 1-0.30
    arac_referansi 0.86  D-124: 24 kare · 1880 tespit, IQR/medyan 0.138
                         -> 1-0.138 = 0.862

**⚠ OLCUM EMRIN SIRALAMASINI DOGRULAMIYOR.** Katman 2 (arena) katman 3'ten
(arac) DAHA BELIRSIZ olculdu: 0.70 < 0.86. Siralama KULLANICININ karari oldugu
icin DEGISTIRILMEDI; carpanlar olculen gercegi yansitir, yani arena kaynakli
bir olcek arac kaynaklidan DAHA DUSUK guvenle sunulur. Cevirme karari mimarindir.

**🔴 SENARYO BEYAN EDILIR, TAHMIN EDILMEZ.** `senaryo` bilinen bir anahtar
degilse katman 2 DEVREYE GIRMEZ. Neden onemli oldugu testle sayiya baglandi:
ayni sinir genisliginde HTAB (50 m) ile FDA (20 m) arasindaki oran **tam 2,5**.
"kare = arena" varsayimi da yoktur: sinir tespit edilemediyse katman calismaz.

**KAPI (e) — 67 GERCEK KAREDE OLCEK KAYNAGI DAGILIMI:**

    telemetri        0/67  (%  0.0)   carpan 1.00
    arena_siniri     0/67  (%  0.0)   carpan 0.70   (otoparkta ARENA YOK)
    arac_referansi  67/67  (%100.0)   carpan 0.86
    URETILEMEDI      0/67  (%  0.0)

    OLCEK TURETILEBILEN KARE : 67/67      (onceki durum: 0/67)
    mpp  min/medyan/maks     : 0.06437 / 0.07459 / 0.11409
    r_gerekli_px             : 9.6 / 14.7 / 17.1   (R_GEREKLI_M = 1.10 m)

D-124 bagimsiz olarak DOGRULANDI: mimar mpp medyan 0,07321 ve r_gerekli
14,2-15,9 px bildirmisti; bagimsiz olcum 0,07459 ve 14,7 px verdi.

**GERIYE UYUM.** `analyze_path(..., olcek_kaynagi=OLCEK_KAYNAK_TELEMETRI)`
varsayilani telemetridir ve carpani 1.00'dir — mevcut cagri yerlerinin guveni
BIREBIR korunur. Kaynak ve carpan `olcum` sozlugune yazilir.

═══════════════════════════════════════════════════════════════════════════
T74 · KORIDORLAR GOVDE ACIKLIGINA GORE DAR — OLCULDU (kod degismedi)
═══════════════════════════════════════════════════════════════════════════

**ADIM 1 — DAR PAYLAR TEK BIR PARAMETRE ARALIGINDAN GELMIYOR.**
KUSURSUZ ALGI ile olculdu (yer gercegi maskesi, model YOK; D-104 cercevesi),
n=260, pay = darbogaz_px - r_gerekli_px:

    uretec serit durumu     n    medyan     min     pay<3px
    acik                  170     17.92    0.10     17/170  (%10.0)
    kapali                 51      7.92    0.12     18/51   (%35.3)
    dar+bariyer            16      7.42    0.10      5/16   (%31.3)
    dar                     8      9.52    0.92      3/8    (%37.5)
    acik+bariyer            8      5.42    0.92      3/8    (%37.5)

    TUM KARELER: medyan 14.31 px · en dusuk 0.10 px · pay<3px 46/260
    pay < 0 olan kare: 0/260   (C-uzayi ihlali YOK)

🔴 **`dar_orani = 0.28` DEGIL.** "dar" isaretli seritler yalniz 24/260 karede
secilir; oysa dar paylarin **17'si (%37) "acik" seritlerden** gelir. En dusuk
pay (0,10 px) hem "acik" hem "dar+bariyer" durumunda gorulur. Yani darlik
uretec parametresiyle SINIRLANMIS degildir, geometrinin geneline yayilmistir.

⚠ **ALGI DEGIL GEOMETRI.** Ayni olcut modelle 10,9 px medyan / 59-255 verirken
(D-122), kusursuz algiyla 14,31 px / 46-260 veriyor. Yani darligin BUYUK KISMI
modelin hatasi degil URETECIN GEOMETRISIDIR: kusursuz algida bile kareler-in
%17,7'si 3 pikselin altinda pay tasiyor.

**ADIM 2 — R_GEREKLI_M = 1,10 m BILESENLERININ KANITI** (`costmap_path_finder.py`
:58-72 ve modul sonu TAHMINLER blogu). DEGISTIRILMEDI, yalniz kanit gosterildi:

    bilesen           deger   pay      kaynak
    IKA_GENISLIK_M/2  0.35 m  %32   simulation/models/ika/model.sdf'ten
                                    TURETILDI (govde 0,66x0,50 -> 0,70
                                    yuvarlandi). ⚠ kodun kendi notu:
                                    "GERCEK aracin olcusu FARKLI olabilir"
    MASKE_HATA_M      0.25 m  %23   GEREKCELI ama OLCULMEMIS: "512-proto maske
                                    bilineer resize; sinir belirsizligi ~1
                                    proto-piksel + bulanma payi"
    TAKIP_HATA_M      0.50 m  %45   🔴 TAHMINLER #1: "SAF VARSAYIM,
                                    r_gerekli'nin EN BUYUK terimi"

    OLCULMEMIS PAY: 0.75 m / 1.10 m = %68
    GERCEK IKA UZERINDE OLCULEN BILESEN: YOK (0.35 m SIM modelinden gelir)

🔴 **BELGE ILE KOD CELISIYOR — DUZELTILMEDI, BILDIRILIYOR.** TAHMINLER blogu
`TAKIP_HATA_M = 0.40` diyor, kod satir 63'te `0.50` yaziyor. Denetim notu
BAYAT. Hangisinin dogru oldugu bu gorevde belirlenemez; R_GEREKLI_M'e
DOKUNULMADI (emrin 3. maddesi).

═══════════════════════════════════════════════════════════════════════════
T79 · KORIDOR SECIMI KARARSIZ — KAPI TUTMADI, [ ] BIRAKILDI
═══════════════════════════════════════════════════════════════════════════

**ADIM 1 — KOKEN OLCULDU VE ONERILEN CERCEVE KISMEN CURUDU.**
Ceviren 9 karenin her biri 4 kez kosuldu ve TAM olcum saklandi:

    kare        ham -> gurultulu        serit_min (1/2/3)          teshis
    sa_000081   2 -> 3    --/15.00/--  ->  --/--/15.00   ACIKLIK AYNI, serit
                                                          FARKLI: TASINMA
    sa_000172   1 -> 3    25.00/--/--  ->  --/--/24.00   tek serit, TASINMA
    sa_000176   3 -> 1    --/--/95.00  ->  64.13/--/--   maske IoU 0,649
    sa_000174   2 -> yok  gurultulu kosuda GORUS_HATTI_KOPUK (serit degil ROTA
                          kayboluyor)
    sa_000232   1 -> 2    23.00/23.00  ->  bagil fark 0,0000   BERABERLIK
    sa_000258   3 -> 2    18.00/17.98  ->  bagil fark 0,0009   BERABERLIK

  · BERABERLIK (argmin gurultuyu izliyor) : **2/9**
  · ROTA TASINMASI (maske degisiyor)      : **7/9**
  · Bunlarin 4'unde her kosuda TEK serit dolu — kiyaslanacak IKINCI ADAY YOK,
    beraberlik bozma kurali TANIM GEREGI caresiz.
  · rota piksel sayisi 4 vakada da AYNI (540) ama maske IoU 0,649-0,986:
    degisen sey rotanin UZUNLUGU degil YERIDIR.

**ADIM 2 — BERABERLIK BANDI UYGULANDI** (`BERABERLIK_BANDI = 0.04`).
Deger CIPLAK DEGIL: projenin OLCULMUS gurultu tabani 0,04'tur (D-112). Band
icindeki adaylar arasinda secim DETERMINISTIKTIR (once daha cok rota pikseli,
esitlikte kucuk indis). Band disinda davranis DEGISMEZ.

**ADIM 3 — HISTEREZIS YAZILDI, URETIME BAGLANMADI.**
`koridor_histerezisi()` saf fonksiyon olarak eklendi ve EMNIYET KURALI testle
civilendi: **onceki koridor artik gecilemezse ANINDA birakilir** (test:
`test_onceki_GECILEMEZSE_ANINDA_birakilir`). Olculemeyen durumda histerezis
UYGULANMAZ (fail-through), yani "olcemedim" gerekcesiyle eski koridor korunmaz.
⚠ URETIME BAGLANMADI: `analyze_path` DURUMSUZDUR ve histerezis KARELER ARASI
bir mekanizmadir; `68_karar_kararliligi.py` her kareyi BAGIMSIZ gurultu
cekimiyle olcer, dolayisiyla o kapiyla DOGRULANAMAZ. Olcemedigim bir seyi
uretime baglamadim.

**🔴 KAPI (c) TUTMADI — ZORLANMADI.**

    taban (degisiklikten ONCE) : 9/260  (%3,46)
    T79 sonrasi                : 8/260  (%3,08)     hedef: <= 4/260

Duzelen tek kare `sa_000192` (51,00/52,00 -> bagil fark 0,0192, band ICINDE).
Bu, adim 1'in olcumunun tam olarak ongordugu sonuctur: band yalnizca
beraberligi cozer, TASINMAYI cozmez. Kalan 8 cevrilmenin 7'si tasinmadir ve
maske degisiminden gelir; onlari cozmek ya modelin gurultu dayanikliligini ya
da kareler-arasi histerezisi gerektirir — ikisi de bu gorevin kapsaminda
DEGILDIR. Gorev `[ ]` birakildi.

═══════════════════════════════════════════════════════════════════════════
KAPILAR
═══════════════════════════════════════════════════════════════════════════

    (a) codes/test_rota_sentetik.py      SONUC: 15/15 dogru          GECTI
    (b) unittest discover -s tests -q    Ran 526 tests · OK          GECTI
                                         (481 -> +45; dusmedi)
    (c) 68_karar_kararliligi.py          8/260 (%3,08)               DUSTU
                                         (taban 9/260; hedef <= 4)
    (d) 65_kabul_denetcisi.py            K0..K4 GECTI · K5 asagida
    (e) 67 karede olcek kaynagi          67/67 turetildi             GECTI

**KAPI (d) AYRINTI — K5 BOZULMADI, ZATEN OLCULEMIYOR.**

    K0 KORLUK YOK        GECTI  figur zemin %7.8 · raw 0/8 · cp 0/8
    K1 ROTA >= 230       GECTI  255/260
    K2 BASMA <= %15      GECTI  18/255
    K3 AGIR  <= %3       GECTI  0/255
    K4 ARENA DISI <= %5  GECTI  1/255
    K5 BARIYER = 0 px    DUSTU  "None px"

K0..K4 D-115 ile **BIREBIR AYNI** (255/260 · 18/255 · 0/255 · 1/255 · %7,8) —
karar yolundaki degisiklik bu olcutlerin hicbirini oynatmadi.
K5'in "None" olmasinin sebebi ayrica kosularak KANITLANDI: `65_kabul_denetcisi`
K5'i `63_bariyer_kesisimi.py`nin ciktisini AYRISTIRARAK alir; o betik dogrudan
kosuldugunda **"rota yok — kesisim olculemez"** basiyor ve "ROTA x BARIYER
kesisimi" satirini HIC uretmiyor, ayristirma da `None` donduruyor. Bu, D-115'in
1. bulgusunun aynisidir (sartname figurunde v27 rota uretmiyor; K5 olcumu bu
yuzden `66_k5_bariyer_populasyon.py`ye TASINMISTI, n=172, 0 px). Yani denetci
ASILMIS bir olcumu cagirmaya devam ediyor — benim degisikligimden BAGIMSIZ,
ONCEDEN VAR OLAN bir kusur.
⚠ Ayrica kayda gecer: ayni kosuda bariyer pikselleri icin **model ENGEL %100,0**
olculdu (D-92'de v24 icin %0,0 idi) — v27 o bariyeri tam goruyor.

**YAN ETKI — KENDI HATAM, KAYDA GECIYOR.** `sed -i` ile import satiri eklerken
`codes/rpi_inference.py`nin TUM satir sonlarini CRLF'ten LF'e cevirdim.
`test_jetson_comms_paketi` bunu bayt kiyasiyla YAKALADI (2 hata). Dosya CRLF'e
geri cevrildi ve saha paketi yeniden uretildi; takim OK'e dondu.

**DOGRULANAMADI**
  1. Katman 2 (arena siniri) HICBIR GERCEK KAREDE CALISMADI — otoparkta arena
     yoktur. Uretilen kod yolu yalniz BIRIM TESTIYLE dogrulandi; gercek bir
     arena karesinde sinir tespiti KOSULMADI (T65/D-94: sinir zaten
     yerellestirilemiyor).
  2. Arac referansi ARENADA CALISMAZ — arenada arac yoktur. 67/67 sonucu
     OTOPARK icindir, arena icin degil.
  3. Olcek kahini uretim cagri yerlerine (run_image/run_video/run_camera,
     hakem ekrani) BAGLANMADI; yalniz sozlesme fonksiyonu + `analyze_path`
     parametresi olarak mevcut. Ekranda gosterim ayri bir istir.
  4. `ARAC_GENISLIGI_M = 1.80` bir LITERATUR degeridir (TS/EU M1 bandi);
     sahnedeki araclarin gercek genisligi OLCULMEDI. Band duyarliligi %11,1
     olarak testle kayitlidir.
  5. T79 cevrilme sayilari TOHUMA baglidir: kendi tek-cekimli olcumumde 4/260,
     kapinin 3-tekrarli olcumunde 8/260 cikti. Yon ve mekanizma tohumdan
     bagimsizdir, SAYI degildir.
  6. Histerezis GERCEK bir kare dizisinde HIC kosulmadi (ardisik kare verisi
     yok); yalnizca birim testleriyle dogrulandi.

---

### D-128 · 🔴 DUZELTME · D-127'nin "42/67" sayisi KUSURLU ETIKETTEN geldi; dogru sayi 17/67
Olcen: Claude 1 (mimar) · 2026-08-15 03:00 · kullanici: "yeterince iyi etiketleyememissin, daha fazla ugras"

**KULLANICI HAKLIYDI.** Etiketleri yalnizca KUCULTULMUS bir kontakt sayfasinda
gormustum. Tam cozunurlukte bakilinca acik bir kusur cikti: **gunes alan duz
asfalt "bina" isaretlenmisti** — otoparkin ortasinda alani 54.250 pikselе varan
kirmizi lekeler. Sebep, YAPI kuralinin "parlak + duz + genis" demesiydi;
gunesli asfalt uc sarti da sagliyor.

**OLCUMLE DUZELTILDI.** Aday bilesenler tek tek olculdu (ayni kare):

    bilesen          alan     L ort   DIKDORTGENLIK
    cati            31794     222,3          0,853
    asfalt lekesi   54250     180,0          0,324
    asfalt lekesi   15527     212,7          0,339
    asfalt lekesi    3881     182,3          0,355

Cati DOGAL OLARAK DIKDORTGENDIR; gunes lekesi pacavradir. Kural iki olcute
baglandi (`L > 205` ve `dikdortgenlik > 0,45`) ve kapama cekirdegi 15 -> 9
kucultuldu (buyuk cekirdek catiyi komsu asfalta yapistiriyordu). Yapi bileseni
kare basina 3,5 -> 2,0 dustu; gorsel olarak asfalt tertemiz zemin oldu.

**VE BU, D-127'NIN SAYISINI COKERTTI:**

    etiket surumu              kaplama   kenar   KAPIYI GECEN
    v27 modeli                   0,814   0,809         0/67
    v1 etiketi (KUSURLU)         0,728   0,494        42/67
    v5 etiketi (DUZELTILMIS)     0,813   0,569        17/67

**v1 etiketleri kapiyi DAHA COK geciyordu CUNKU YANLISTILAR.** Asfalti engel
isaretlemek kaplamayi yapay olarak dusuruyor ve kenar dayanmasini kiriyordu.
Duzeltilince ikisi de gercek degerine cikti.

**DOGRU SAYI 17/67'DIR.** D-127'de yazdigim "yer gercegiyle 42/67 geciyor"
GECERSIZDIR; kayit silinmez (madde 6), duzeltme burada durur.

**BUNUN ANLAMI — D-124 ILE D-127 ARASINDA BIR YERDE:**
  · D-124 ("hicbir dogru algi gecemez") MUTLAK olarak YANLIS — 17 kare geciyor.
  · D-127 ("kapi rahat gecilir, 42/67") ASIRI IYIMSER — kusurlu etiketten geldi.
  · Dogrusu: **acik otoparkin cogu karesi kapiyi MESRU olarak gecemez**, cunku
    sahne gercekten de cogunlukla acik surulebilir alandir ve cerceve
    kenarlarina dayanir. Kapinin "sinirli arena" varsayimi bu sahnede
    kismen ihlal olur. Ama karelerin **dortte biri** gecer; mukemmel algi
    otoparkta 0/67'yi 17/67'ye TASIR.

**MIMARIN BU KONUDAKI UCUNCU DUZELTMESI.** Sirasiyla: (1) "otopark kapsam
disi" — kolaycilik; (2) "kapi yapisal olarak gecilemez" — yer gercegi
olculmeden; (3) "42/67 geciyor" — kusurlu etiketle. Ucu de OLCUMLE duzeldi.
Ders acik: her seferinde EKSIK BIR OLCUMLE hukum verdim. Kullanicinin
"daha fazla ugras" uyarisi olmasa ucuncusu de duzelmezdi.

**ELDEKI VERI.** 67 kare + duzeltilmis YOLO-seg etiketleri + onizleme:
`calisma/gercek_kare_etiket_v1/` (v5 kurallariyla yeniden yazildi).

⚠ **NE IDDIA ETMIYORUM:** etiketler hala YARI OTOMATIKTIR. Iki kare tam
cozunurlukte denetlendi, 67'sinin tamami DEGIL. Catida kucuk yesil lekeler
kaldigi gorüldü (koyu/dokulu cati parcalari). Sayilar bu gurultuyu tasir.

---

### D-129 · ONCEDEN KAYIT · v29 (gercek otopark verisi) kabul kurali — SONUC GORULMEDEN yazildi
Yazan: Claude 1 (mimar) · 2026-08-15 03:10

**AMAC.** Kaptanin istegi: hakem ekrani GERCEK goruntude yol bulsun. Olculen
tikac (D-128): model catiyi/binayi/bitkiyi zemin sayiyor; kenar dayanmasi
0,809, yer gercegi 0,569. Mukemmel algi 0/67'yi 17/67'ye tasir.

**VERI.** `karisim_gercek_otopark.yaml` = `karisim_t54_engelli.yaml` + 67
gercek kare (train 56, 12 kat cogaltilmis -> 672; val 11, cogaltilmamis).
Diger uc bilesen BIREBIR AYNI; v27 <-> v29 kiyasi TEK degisken tasir.

**v28 DURDURULDU.** Epoch 48/200'de kesildi; `last.pt` korundu, `--devam` ile
surdurulebilir. Gerekce: v28 bir OLCUM BORCUNU kapatiyordu (D-112), v29 ise
kaptanin istedigi yetenegi acmayi deniyor. GPU tek; oncelik v29'undur.

⚠ **YAN BULGU — D-112'NIN SURE ARGUMANI GERCEKLESMEDI.** v28 (512) 1,79
dk/epoch kostu; v27 (640) 1,77 dk/epoch kosmustu. **512'ye inmek egitimi HIC
hizlandirmadi.** D-112'de "512'de egitim ~0,64 kat -> 8,6 saat 5,5 saate iner"
yazmistim; bu YANLIS cikti. Sebep D-108'de zaten olculmustu: egitim GPU'ya
degil VERI HATTINA bagli. Cozunurluk karari (512) hala gecerlidir ama
gerekcelerinden BIRI (egitim maliyeti) DUSMUSTUR; kalan gerekceler Jetson
maliyeti ve tutarliliktir.

**KABUL KURALI — VARSAYILAN "v27 KALIR".** v29 ancak sunlarin HEPSI
saglanirsa uretime alinir:
  1. D-107'nin ALTI olcutunu de gecer (K0..K5), ve
  2. K1/K2/K3/K4/K5 v27'ye gore BOZULMAZ (K2 <= %15, K3 <= %3, K4 <= %5,
     K5 = 0 px, K1 >= 230), ve
  3. GERCEK karelerde OLCULEBILIR ilerleme:
     a. kenar dayanmasi medyani 0,809'dan **<= 0,65**'e iner, VE
     b. kapiyi gecen kare sayisi 0/67'den **>= 8/67**'ye cikar.

(3b'nin tavani yer gercegidir: 17/67. Yarisi, "model yer gercegine anlamli
sekilde yaklasti" demek icin yeterlidir; altinda kalirsa veri ise yaramamistir.)

Bu esiklerin ALTINDA kalan her sonucta **v27 uretimde kalir**.

⚠ **EZBERLEME RISKI OLCULECEK.** 67 kare AYNI otoparktan ve dort ardisik
videodan. v29 gercek karelerde iyilesip SENTETIK kabul kumesinde bozulursa
(sart 2 duserse) bu EZBERLEMEDIR ve model REDDEDILIR — "gercekte iyilesti"
gerekcesiyle kabul edilmez.

⚠ K-3 hatirlatmasi: mAP/fitness karar olcutu DEGILDIR.

---

### D-130 · KABUL · v28 (512) D-123'un KURALINI SAGLADI — kararlilik 3 KAT iyilesti, moloza basma bir puan kotulesti
Olcen/karar: Claude 1 (mimar) · 2026-08-15 10:06-11:20 · esikler D-123'te SONUC GORULMEDEN yazildi

**EGITIM.** v28, 200/200 epoch, `imgsz=512`. v27 ile AYNI veri
(`karisim_t54_engelli.yaml`), AYNI recete, AYNI on-egitim; tek degisken
cozunurluk (640 -> 512).

**D-113 TEKRARLAMADI.** `best.pt` epoch 152'ye denk geliyor (tahmini bitis
07:41, dosya damgasi 07:48) ve fitness'in gercek azamisi da epoch 152'dir
(0,38847). v27'deki donma, kendi olmayan bir `best_fitness`in mirasindan
kaynaklaniyordu; v28 kendi `last.pt`'sinden devam ettigi icin gecerli bir deger
tasidi. Denetim yine de `last.pt` (epoch 200) uzerinde kosuldu; fark 0,0027.

**FITNESS — 512 DAHA KOTU:**

    v27 (640)  en iyi 0,42093 (epoch 195) · son 0,42048
    v28 (512)  en iyi 0,38847 (epoch 152) · son 0,38580

Fark 0,035 — gurultu tabani 0,04'un hemen altinda, yani tek basina belirleyici
degil. Zaten K-3 uyarinca fitness KARAR OLCUTU DEGILDIR.

**D-123'UN UC SARTI, TEK TEK:**

    1. ALTI OLCUT DE GECTI:
       K0 korluk yok   GECTI  figur zemin %15,5 · raw 0/8 · cp 0/8
       K1 rota >= 230  GECTI  256/260          (v27: 255/260)
       K2 basma <= %15 GECTI  21/256 = %8,20   (v27: %7,06)
       K3 agir <= %3   GECTI  0/256 = %0,0     (v27: %0,0)
       K4 disi <= %5   GECTI  1/256 = %0,39    (v27: %0,4)
       K5 bariyer=0px  GECTI  0 px             (v27: 0 px)
       ⚠ K5 v28'de FIGUR uzerinde de olculebildi; v27'de o karede rota
         olusmadigi icin tanimsizdi (D-114). Bu bir iyilesmedir.

    2. K3/K4/K5 v27'ye gore BOZULMADI: ✓ (%0,0 · %0,39 · 0 px)

    3. IKISINDEN EN AZ BIRI:
       a. K2 v27'den >= 2 puan iyi (<= %5,1)?   ✗ DUSTU — %8,20, yani
          v27'den 1,14 puan KOTU.
       b. Kararlilik cevrilmesi <= 4/260?        ✓ TUTTU

          v27  KARARI CEVRILEN  9/260  (%3,46)
          v28  KARARI CEVRILEN  3/260  (%1,15)     <- UC KAT iyilesme
          (ayni tohum, ayni sigma=2/255, kare basina 3 tekrar)

**VERDIKT: v28 KABUL EDILIR.** Kural saglandi. Esik sonradan ne
SIKILASTIRILDI ne GEVSETILDI.

**TAKAS ACIKCA YAZILIYOR.** v28, moloza basmada **1,14 puan** kotu; buna
karsilik karar kararliliginda **3 kat** iyi. Bu takasi D-123'te sonucu
gormeden kabul ettim ve arkasindayim: tek kare olcumu (K2) ile video akisi
davranisi (kararlilik) ayni agirlikta degildir — IKA tek kare degil, akis
izler. %3,46'lik cevrilme oraninda rota koridor degistirip zikzak yapar.

⚠ **UYGULAMA v29'DAN SONRAYA BIRAKILDI.** Uretim zincirini cevirmek
(`config/model_registry.json`, jetson manifesti, iki kilavuz, ONNX, paket)
T76 olceginde bir istir ve URETIM KODUDUR — mimarin yazma yetkisi yoktur
(madde 7; kullanici bu yetkiyi acikca vermedi). v29 ~12:49'da bitiyor ve
GERCEK otopark verisiyle egitildi. Zincir bir kez cevrilsin diye v29'un
verdikti beklenir. Bu, D-123'un kuralini degistirmez — v28 KABUL EDILMISTIR;
degisen yalnizca uygulama SIRASIDIR.

**PARALEL KOSUM — MIMARIN ERKEN YARGISI DUZELTILIYOR.** Kullanicinin "ikisi
ayni anda kosabilir" onerisini iki epoch'luk bir olcumle "bedava" diye
onaylamistim. Tam kosum bunu curuttu:

    v28 TEKIL   (epoch 45->47)    1,74 dk/epoch
    v28 PARALEL (epoch 197->199)  2,81 dk/epoch   (+%61)
    v29 tekil baslangic           2,11 dk/epoch
    v29 paralel ortalama          3,07 dk/epoch   (+%45)

VRAM ve RAM gercekten bostu (kullanici hakliydi); ama darbogaz onlar degil
VERI HATTIDIR (D-108) ve iki egitim ayni diski ve cekirdekleri paylasti.
Toplam is cikti ARTMADI. Iki epoch'luk orneklem bu etkiyi gormek icin cok
kisaydi.

**DOGRULANAMADI**
  1. v28'in K2'deki gerilemesinin sebebi (cozunurluk mu, egitim gurultusu mu)
     arastirilmadi; fark 1,14 puan ve gurultu tabani mertebesinde.
  2. Kararliliktaki 3 kat iyilesmenin cozunurlukten geldigi KANITLANMADI —
     tek kosu, tek tohum.
  3. Tum olcumler SENTETIKTIR (D-88/D-99, kalici kisit).
