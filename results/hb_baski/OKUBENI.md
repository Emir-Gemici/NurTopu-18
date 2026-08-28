# HB (HEDEF BÖLGE) — 2 m × 2 m BASKI DOSYALARI

Şartname §2.1: *"Hedef Bölge (HB): … **2 metre x 2 metre** boyutlarında
**üzerinde kırmızı H harfinin** bulunacağı bir bölgedir."*

## Matbaaya gidecek dosyalar

| dosya | ne işe yarar |
|---|---|
| **`HB_2x2m_BASKI.pdf`** | **Basılacak dosya.** Vektörel, sayfa boyutu tam **2000 × 2000 mm** (doğrulandı). |
| `HB_2x2m_BASKI.svg` | Aynı çizim, CorelDRAW/Illustrator ile açılıp düzenlenebilir. |
| **`HB_2x2m_TEKNIK_FOY.pdf`** | **Matbaacıya verilecek föy**: ölçüler, renk kodları, malzeme ve "değiştirilmemesi gerekenler". |
| `HB_2x2m_onizleme.png` | Telefonda hızlı bakmak için. |

## Ölçüler nereden geldi

Uydurulmadı — **kendi üretecimizin çizdiği pedden ölçüldü**
(`scripts/olcum/51_sentetik_arena.py::hb_ciz`), çünkü basılan şey sistemin
üzerinde ayarlandığı şeyle aynı olmalı:

| öğe | kenarın yüzdesi | 2000 mm'de |
|---|---|---|
| kırmızı çerçeve | %4,58 | **92 mm** |
| H dış kutusu | %40,5 × %48,2 | **810 × 964 mm** |
| H kol kalınlığı | %9,3–9,8 | **190 mm** |

Tek fark: üretecin çizdiği H, yazı tipi taban hizası yüzünden **hafif aşağıda**
duruyor. Baskıda **ortalandı** — bu, tespit kutusunu daha kare yaptığı için
sistemin lehinedir.

## Renk neden RAL 3020

Tespit algoritması kırmızıyı LAB `a*` kanalından bulur ve eşiği **25**'tir.
Ölçüldü:

| aday | LAB a* |
|---|---|
| üretecimizin HB kırmızısı | 67 |
| **RAL 3020 Trafik Kırmızısı** | **67** ← birebir aynı |
| RAL 3001 Sinyal Kırmızısı | 53 |
| beyaz zemin | 0 |

RAL 3020 hem eğitim kromamızla birebir eşleşiyor hem de her matbaanın
tanıdığı bir standart.

## Doğrulandı: sistem bu pedi görüyor

Baskı görseli sahadaki ölçeğine küçültülüp gerçekçi zeminlere yerleştirildi ve
**üretim çağrı sırasıyla** sınandı:

| irtifa | 4K karede ped | üretimin 512'sinde | bulundu mu |
|---|---|---|---|
| 25 m | 208 px | 28 px | **evet** |
| 30 m | 173 px | 24 px | **evet** |
| 40 m | 130 px | 18 px | **evet** |
| 50 m | 104 px | 14 px | **evet** |

Zemin türü (toprak / beton / koyu nemli toprak) fark etmedi; merkez hatası
**0,7 px**.

## Parlaklık hakkında — ölçüldü, abartılmadı

Önce *"mat şart"* diyecektim. Ölçtüm, **öyle değil**: pedin bir şeridi güneşte
tamamen beyaza doysa bile (%70'e kadar denendi) dedektör pedi kusursuz
buluyor — çünkü kırmızı çerçeve tüm çevreyi dolaşıyor ve köşegen bir parlama
onu silemiyor.

**Sonuç:** mat **tercih edilir**, ama parlak branda da kabul edilebilir.

## Uyarılar

1. **Katlama payı ilave malzemeden olmalı.** 2000 mm **bitmiş** ölçüdür;
   kenar katlaması kırmızı çerçeveyi yerse çerçeve incelir.
2. **Yön fark etmez.** H 180° simetriktir ve tespit algoritması (T184'ten beri)
   açıdan bağımsızdır.
3. **Farklı bir kırmızı kullanılacaksa önce ölçelim.** Eşik `a* > 25`; pembeye
   ya da bordoya kaçan bir ton bu eşiğin altına düşebilir.
