# SON GÜVENLİ GELİŞ TARİHİ — **19 EYLÜL** (T137 ölçümüyle güncellendi)

> ⚠ Bu dosya **T136**'da yazıldı ve **T137**'de ölçülen kapasiteyle **yeniden
> koşuldu**. Değişen tek şey V2'dir: *"1 kişi × 8 saat/gün (İNSAN)"* varsayımı
> yerine **ölçülmüş ajan kapasitesi** kondu (kullanıcı kararı: *"etiketlemeyi
> dinamik workflow'a sahip amele yapacak"*).
> **Önceki sonuç: 13 Eylül. Yeni sonuç: 19 Eylül (+6 gün).**

## 1. ÖLÇÜLEN BİRİM MALİYETLER

| adım | ölçülen | kaynak |
|---|---|---|
| kare çıkarma (4K, dedup) | **6,4 sn / dk video** · verim **26,1 kare/dk** | `results/t136/dji_prova/kosum.json` |
| etiket + çoğaltma (4K) | **4,6 sn / kare** | T136 fan-out |
| eğitim | **0,58 saat / 440 görüntü** (18 epoch) | `codes/runs/segment/t127_temiz` |
| kabul zinciri | ~7 dk | T136 fan-out |
| **elle etiketleme (İNSAN — ARTIK KULLANILMIYOR)** | ~0,03 saat/kare → 1566 kare ≈ 47 saat | T136 |
| 🔴 **ajan etiketleme (ÖLÇÜLDÜ, T137)** | **19,9 kare/saat** (7 ajan, duvar saati) | `results/t137/kapasite.json` |

### Ajan kapasitesi — ölçülen üç parti
```text
faz     ajan  kare  duvar saati   PARALEL verim   ajan basina
uyum      3    24     43,5 dk     33,1 kare/saat   237 sn/kare
kucuk     2    20     47,4 dk     25,3 kare/saat   176 sn/kare
buyuk     7    67    202,3 dk     19,9 kare/saat   261 sn/kare
```

🔴 **KAPASİTE AJAN SAYISIYLA ÖLÇEKLENMİYOR — KÖTÜLEŞİYOR.** 3 ajan 33,1
kare/saat, 7 ajan **19,9**. Sebep ölçüldü: büyük partide tek tek ajan süreleri
**`[150, 1150, 12137, 799, 649, 470, 2150]`** — **81 kat yayılım**. Faz duvar
saatini **tek bir geç kalan** belirliyor (bariyer).
- Ajan sürelerinin **toplamı**: 17.505 sn / 67 kare = **261 sn/kare**.
- **Dengeli dağıtılsaydı** 7 ajan aynı işi ~2.501 sn'de (**42 dk**) bitirirdi
  → ~**96 kare/saat**. ⚠ Bu bir **projeksiyondur, ölçüm değil**; plana
  **ölçülen 19,9** konmuştur.

## 2. VARSAYIMLAR

| # | varsayım | değer | not |
|---|---|---|---|
| V1 | çekim uzunluğu | **60 dk** 4K | ⚠ hâlâ bilinmiyor; sonuç buna **çok duyarlı** |
| **V2** | **etiketleyen** | **ajan · 19,9 kare/saat (ÖLÇÜLDÜ)** | eski: 1 kişi × 8 sa/gün |
| V3 | eğitim yeniden koşumu | 1 kez | |
| V4 | bitiş hedefi | **27 Eylül** | 30 Eylül CİHAZ günü (T109/T123) |
| V5 | başarısız çekim payı | **+3 gün** | T136 provası bunun gerçek olduğunu gösterdi |

## 3. HESAP

```text
60 dk video -> 1566 kare (26,1 kare/dk)
  kare cikarma      6,4 sn x 60          =    6,4 dk
  AJAN ETIKETLEME   1566 / 19,9 kare/sa  =   78,7 SAAT = 3,3 gun (INSANSIZ)
  etiket+cogaltma   4,6 sn x 1566        =    2,0 saat
  bolum + yaml                            =   <0,5 saat
  egitim (V3: 2 kosum)                    =   ~1 gun
  kabul zinciri + aday raporu             =   ~0,5 gun
                                            ------------------
                                    TOPLAM  ~5 GUN (cogunlukla insansiz)
27 Eylul - 5 gun - 3 gun (V5) = 19 EYLUL
```

## 🔴 4. SONUÇ

> **Görüntü en geç 19 Eylül'de gelmezse 30 Eylül'e yetişmez.**
> (Önceki hesap 13 Eylül'dü; ajan etiketlemesi **6 gün kazandırdı**.)

Bugün **22 Ağustos** → **28 gün** var.

⚠ **Ham saat olarak ajan İNSANDAN YAVAŞ** (78,7 saat vs ~47 saat) ama
**gözetimsiz** koşuyor: takvimde 3,3 gün sürekli iş, 6 iş gününe karşı. Kazanç
hızdan değil, **insanın hattan tamamen çıkmasından** geliyor (D-211 §1b).

⚠ V1 duyarlılığı: çekim **120 dk** olursa etiketleme 157 saate (6,6 gün) çıkar
ve son tarih **~15 Eylül**'e kayar.

## 🔴 5. BU TARİHİN ÖN KOŞULU — ÖNCE ŞARTNAME DÜZELTİLMELİ

T137 ölçtü (`results/t137/kalite_bulgusu.md`): ajanlar birbiriyle **IoU 0,88**
uyuşuyor ama T121 referansıyla **0,55** — ve üçü de **aynı yönde** sapıyor.
Sebep yetenek değil **görev tanımı**: ajanlar *"çatı üst yüzeyi"* çiziyor,
referans *"geçilemez bina bölgesi"* (duvar/cephe dâhil) çiziyor.

🔴 **Düzeltilmeden 1566 kare etiketlenirse model duvar yüzünü ZEMİN öğrenir** —
D-210'un kardeş kusuru, bu kez ölçeklenerek. Şartname cümlesi
`kalite_bulgusu.md §3`'te **öner-bekle** olarak duruyor; **karar mimarındır**
ve bu hesabın **ön koşuludur**.

## 6. ÇEKİMİN ÜÇ ŞARTI (T138'den — hepsi zorunlu)
**gündüz** (referans L≈129, gece L≈21 hiç örtüşmüyor) · **gimbal 90° nadir**
(klip 0020 ufuk çekimiydi) · **otopark/moloz sahnesi** (tarla ve yol alan dışı).


---

## 🔴 YENİDEN HESAP — 2026-08-25 (kullanıcı talimatı) · **V2 ÜÇÜNCÜ KEZ DEĞİŞTİ**

> Bu bölüm öncekini **geçersiz kılmaz, DÜZELTİR**. Değişen tek şey yine V2'dir:
> etiketleme hızı. Önceki değer (19,9 kare/saat) **çatı** işinden geliyordu;
> su/engel işi F4'te ölçüldü ve **2,7 kat ağır** çıktı.

### 1. ÖLÇÜLEN DEĞER (F4, `REVIEW_LOG.md` D-279)
```text
olculen kare 14 · toplam ajan-saniye 9.910 · kare basina 708 sn
  -> ajan basina 5,1 kare/saat      (T137 cati isi: 261 sn = 13,8 kare/saat)
```
Sebep: şartname maddesi (4) — *"suya bitişik olmayan geçilemez örtü de sınıf 1"*.
Mevcut RescueNet eşlemesiyle tutarlılık için eklendi; yükü **ölçülerek** görüldü.

### 2. 🔴 BAĞLAYICI BÜYÜKLÜK **AJAN-SAAT**, "kare/saat" DEĞİL
"Kare/saat" ajan sayısına bağlıdır ve tek başına yanıltır. Sabit olan iş yüküdür:
```text
T137 cati isi    : 1566 kare x 261 sn = 113,5 ajan-saat
F4   su/engel isi: 1566 kare x 708 sn = 308,0 ajan-saat
```
Duvar saati = **ajan-saat / (N × verim)**.

### 3. VERİM ÖLÇÜMLERİ — ve neden yukarı doğru güvenilmez
```text
T137 3 ajan : gercek 33,1 · ideal 41,4  -> verim %80
T137 7 ajan : gercek 19,9 · ideal 96,6  -> verim %21   <- ajan artinca COKTU
F4   3 ajan : gercek  7,2 · ideal 15,3  -> verim %47
```
🔴 **T137, ajan sayısı arttıkça verimin ÇÖKTÜĞÜNÜ ölçtü** (%80 → %21). Sebep
bariyer: faz duvar saatini **tek geç kalan** belirliyor. F4'te yılan dağıtımıyla
yayılım 81 kattan 26,9 kata indi ve verim %47 oldu — ama bu **yalnız N=3'te**
ölçüldü.

### 4. TARİH — N'ye göre (V4 27 Eylül · V5 +3 gün)
```text
N= 3: etiketleme  9,1 gun + diger 1,6 = 10,7 gun -> 14 EYLUL   ✅ OLCULDU
N= 6: etiketleme  4,6 gun + diger 1,6 =  6,2 gun -> 18 Eylul   ⚠ PROJEKSIYON
N=10: etiketleme  2,7 gun + diger 1,6 =  4,3 gun -> 20 Eylul   ⚠ PROJEKSIYON
N=20: etiketleme  1,4 gun + diger 1,6 =  3,0 gun -> 22 Eylul   ⚠ PROJEKSIYON
```
⚠ **N>3 satırları %47 verimin korunduğunu VARSAYAR ve bu ÖLÇÜLMEDİ.** T137'nin
verisi tersini söylüyor (N=7'de %21). Verim %21'e düşerse N=10 bile
9,1 → 6,1 güne ancak iner. **Plana N=3'ün ölçülen değeri konur: 14 EYLÜL.**

### 5. SONUÇ
> **Önceki: 19 Eylül. Yeni: 14 EYLÜL (−5 gün).**
> Görüntü en geç **14 Eylül**'de gelmezse 30 Eylül'e yetişmez.

**Tarihi geri kazanmanın tek ölçülmüş yolu ajan sayısını artırmak DEĞİL,
DENGELEMEYİ düzeltmektir** — F4'te A'nın 8 karesinde hâlâ 26,9 kat yayılım
vardı (min 117 sn, maks 3.152 sn) ve yük vekilim gerçek süreyi öngörmedi.
Vekil düzelirse verim %47'den yukarı çıkar ve tarih **ajan eklemeden** düzelir.
⚠ Bu bir **öneridir**; ölçülmeden plana konmaz.

### 6. DEĞİŞMEYENLER
V1 (60 dk çekim) hâlâ **bilinmiyor** ve sonuç buna çok duyarlı. ⚠ Eldeki yeni
çekim **19 dakika** (768 kare); 60 dk varsayımı **gelecek doğrulama uçuşu**
içindir. V3, V4, V5 değişmedi.

### 7. 🔴 BU TARİHİN BİLİNEN EKSİĞİ — 708 sn/kare YALNIZ SINIF 1'İN MALİYETİ

F3 ve F4'te amelelere açıkça *"Sınıf 0 çizme, bu turda istenmiyor"* dendi.
Yani ölçülen **708 sn/kare** işin **yarısıdır**.

Planın §3'ü iki sınıfı birden istiyor (yalnız sınıf 1 etiketlemek modelin bu
domende hiç rota üretmemesine yol açar — §1c: karelerin %51,4'ünde zaten
maske yok). Üç durumlu biçimde amele artık üç karar veriyor: **sınıf 1 ·
sınıf 0 · etiketsiz**.

⚠ **Sınıf 0'ın ek maliyeti ÖLÇÜLMEDİ.** İki yönde de tahmin yapmıyorum:
- tek bir bölütleme kararının parçası olduğu için maliyeti iki katına
  çıkarmayabilir;
- ama "burayı sürülebilir diye DOĞRULADIM" ile "buraya BAKMADIM" ayrımı,
  ameleyi kalan tüm alanı **incelemeye** zorlar — bu, F4'te hiç yapılmadı.

⇒ **14 Eylül bir ÜST SINIRDIR (iyimser taraf).** Gerçek tarih daha erken
olabilir. Kapatmanın tek dürüst yolu: F5'e **tam ölçekte değil**, önce
sınıf 0'ı da içeren **küçük bir ölçüm turuyla** girmek ve 708'i yeniden
ölçmek. Aksi hâlde 736 kare, maliyeti bilinmeyen bir varsayımla etiketlenir.
