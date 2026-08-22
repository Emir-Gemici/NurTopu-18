# T123 · YEDEK HANGİ ARIZAYA KARŞI? — ölçümle cevap

> Görev bunu sormadan geçmeyi yasakladı, haklı olarak: senaryoyu ayırmadan
> "yedek" demek, saha günü **yanlış modele geçirtir**.
> ⛔ Bu dosya **terfi önerisi değildir.** Aday sabitlemek terfi değildir;
> seçim ve sevk **insanındır** (D-133).

## 1. ÖLÇÜM TABANI — beş model, aynı kabul kümesi (n=260)

| model | K1 rota | K2 basma | K3 ağır | K4 arena dışı | çatı kaçağı (eğitim/bakir) | gerçek kare red (67) | gece rota sızıntısı |
|---|---|---|---|---|---|---|---|
| **v35** (üretim) | 256 | %7,03 | 0 | 1 | 0,043 / — | **0/67** | **2** |
| **v34** (bugünkü yedek) | 258 | **%4,65** | 0 | 1 | 0,961 / **0,976** | 🔴 **67/67** | 3 |
| **t122ac** | 257 | %6,23 | 🔴 **1** | **0** | **0,020 / 0,011** | **0/67** | 3 |
| v30 | 258 | %5,43 | 0 | 1 | 0,305 / — | — | 5 |
| t121_ft | 259 | **%4,63** | 0 | 1 | 0,131 / 0,175 | — | — |

Kaynaklar: kabul zinciri çıktıları `scripts/olcum/results/t63/*_kabul.json`
(yeniden eğitim YOK) · çatı/bakir tablo **D-249** · gece sızıntısı
`results/t123/gece_kumesi_adaylar.json` (T138 yöntemi, 569 kare).

## 2. 🔴 SENARYO AYRIMI — asıl cevap

### (a) Birincil ÇOK moloza basıyor
- **v34 daha iyi** (%4,65 vs %7,03). t121_ft de (%4,63).
- ⚠ **AMA SAHADA GÖZLENEBİLİR Mİ?** K2 **yer gerçeği olan sentetik kabul
  kümesinde** ölçülür. Sahada "moloza bastı"yı ancak İKA **fiilen bastıktan
  sonra** görürsünüz — yani tetik, hasar oluştuktan sonra gelir.
- **Hüküm:** v34 bu senaryoda meşru bir yedektir, **ama bu senaryo saha günü
  zamanında tespit edilmesi EN ZOR olanıdır.**

### (b) Birincil GÖREMİYOR / rota üretmiyor
- 🔴 **v34 YEDEK OLAMAZ.** Gerçek karelerin **67/67'sini reddediyor** ve bakir
  11 karenin **11/11'ini** (D-249). Çatının **%97,6'sını** kaçırıyor.
- Yani "birincil göremiyor" diye v34'e geçilirse, **yedek DAHA AZ görür.**
  Bu bir yedeklilik değil, arızanın büyütülmesidir.
- **t122ac bu senaryonun doğru yedeğidir:** 0/67 red, çatı kaçağı v35'ten
  **daha iyi** (0,020 vs 0,043) ve bakir karelerde **daha da iyi** (0,011).
- ⚠ **Bu senaryo saha günü EN GÖRÜNÜR olanıdır:** ekran rota çizmez, `road`
  yayınlanmaz — operatör saniyeler içinde anlar.

### (c) Birincil ÇÖKÜYOR (teknik hata)
- Çalışan herhangi bir model yeter; v34 da t122ac de olur.
- Ayırt edici ölçüt yok — **G2 bütünlük kapısı** burada belirleyicidir.

## 3. 🔴 SONUÇ — "iki aday" hedefi KISMEN karşılanıyor

**v34, üç senaryonun YALNIZ BİRİNDE (a) doğru yedektir — ve o senaryo saha
günü en geç fark edilendir.** En görünür ve en olası arıza (b) için v34
**aktif olarak zararlıdır**.

Görev şunu istedi: *"Eğer hiçbir senaryoda v34 daha iyi değilse BUNU YAZ."*
Cevap nüanslı ve öyle yazılıyor: **v34 (a)'da daha iyidir, (b)'de belirgin
biçimde kötüdür.** Dolayısıyla:

> **Bugün elimizde (b) senaryosu için sabitlenmiş bir yedek YOKTUR.**

**t122ac o boşluğu doldurmaya en yakın adaydır** ve tam kabul zincirini
geçmiştir (`t126_t122ac_kabul_verdikt.json` → `verdikt: True`). Ama iki
çekincesi vardır ve ikisi de yazılmalıdır:
1. 🔴 **Kontrol noktası KİRLİ bölümle seçildi** (D-233/D-249): t122ac'nin
   `best.pt`'si, kaynağı eğitimde de olan bir val kümesiyle seçildi. T127 zaten
   **bu yüzden** tekrarlandı ve v35 doğdu. Ağırlıklar geçersiz değildir ama
   **seçimi** şaibelidir.
2. **K3 = 1** (bir ağır basma) — v35, v34 ve v30'da 0.

⇒ **ÖNERİ (öner-bekle, karar insanın/mimarın):** (b) senaryosu için yedek
gerekiyorsa iki meşru yol var:
- **t122ac'yi TEMİZ bölümle yeniden seç** (T127'nin yaptığının aynısı, farklı
  reçete değil) — GPU maliyeti bir koşum; ya da
- **v35'in `last.pt`'sini** ikinci ağırlık olarak sabitle: aynı eğitimin farklı
  kontrol noktası, (c) için tam, (b) için v34'ten kesinlikle iyi.
⚠ Hiçbiri **bu turda uygulanmadı**; T123 aday sabitleme turudur, eğitim turu değil.

## 4. GEÇİŞ YORDAMI — SINANDI ve İKİ KUSUR BULUNDU

Yordam yazılıydı ve 7 testle **metin olarak** kilitliydi; ama **hiç
koşulmamıştı**. Koşunca:

🔴 **KUSUR 1 — G2 çöküyordu.**
```python
beklenen = man["paket_icerigi"].get("models/" + ad)
-> AttributeError: 'list' object has no attribute 'get'
```
İki hata bir satırda: `paket_icerigi` **sözlük değil liste**, ve anahtarları
**çıplak dosya adı** (`"models/"` öneki yok). G2, *"bozuk yedekle geçme"*
kapısıdır; çökünce operatörün önünde iki kötü seçenek kalır.

🔴 **KUSUR 2 — G6 doğrulama girdisi yanlış yolu gösteriyordu.**
`--girdi data/test_goruntuleri/sentetik_arena` → o dizin **yok**; gerçeği
`test_goruntuleri/sentetik_arena`. İki kılavuzda **ikişer** yerde geçiyordu.
Yani geçişin doğru olduğunu kanıtlayacak adım da çökerdi.

**İkisi de T104/D-193'ün birebir sınıfıdır** — kılavuz var olmayan yapıya
işaret ediyor. `test_kilavuz_gecis_yordami.py`'nin kendi docstring'i bu riski
**yazıyordu**; yine de metin kilidi yakalamadı.
**Ders: çalıştırılabilir bir yordam ancak ÇALIŞTIRILARAK kilitlenir.**

### Ölçülen süre (uçtan uca, gerçek dosyalarda, `finally` ile bayt-eş geri alma)
```text
G2  yedek butunlugu (sha256)          0,1 sn
G3  .oncesi kopyalari                 0,0 sn
G4  defter -> yedek                   0,0 sn
G5  kunye -> yedek                    0,0 sn
G6/1 dogrulama kosumu (jetson_fps)    5,9 sn   exit=0 · "2/2 vaka olculdu"
G8  geri alma                         0,0 sn
                              TOPLAM  5,9 sn
```
⚠ **Bu PC ölçümüdür (RTX 5080).** Jetson Orin NX'te G6 belirgin daha yavaş
olacaktır; **ölçülmedi ve cihaz gelmeden ölçülemez** (D-211 §5). Kalan beş
adım cihazdan bağımsızdır ve **saniyeler** sürer.

## 5. KİLİT — artık İCRA testli
`tests/test_t123_gecis_provasi.py` (6 test): G2'nin kodu kılavuzdan **ayıklanıp
ÇALIŞTIRILIYOR**; yalnız saha kök satırı depo köküne çevriliyor ve *başka
satırın değişmediği* ayrıca doğrulanıyor.
```text
POZITIF KONTROL                         T123 provasi 0/6 · eski metin kilidi 0/7
M1 G2 BOZUK haline geri alindi          T123 provasi 3/6 DUSTU · eski kilit 0/7 (YAKALAMIYOR)
M2 yordamdan BIR ADIM cikarildi         T123 provasi 3/6 DUSTU
GERI ALINDI                             0/6 · iki kilavuz da bayt-es
```
⚠ **Kendi alet kusurum:** M2'nin ilk koşumunda mutasyon **hiç uygulanmamıştı**
(kılavuzlar CRLF, desenim `\n` arıyordu) ve "düşmedi" görünmüştü. CRLF-duyarlı
hâliyle tekrarlandı; **düşüyor**. Yanlış sonucu yayımlamadan yakalandı.
