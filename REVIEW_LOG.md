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
