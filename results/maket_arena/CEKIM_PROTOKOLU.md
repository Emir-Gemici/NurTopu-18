# MAKET ARENA ÇEKİM PROTOKOLÜ — 2026-08-28

> **Neden bu iş en kıymetlisi:** elimizde **sıfır** gerçek arena fotoğrafı var.
> Kabul zincirimizin **on kapısının tamamı sentetiktir** ve zincir bunu her
> koşuda kendi yazıyor: *"Bu ölçümlerin tamamı SENTETİKTİR."* Şartname
> figüründe rota üretemiyoruz (T192) ve bunun neden olduğunu **tahmin
> ediyoruz**. 20–30 kare gerçek görüntü, tahmini ölçüme çevirir.

## Ne çekilecek — en az / ideal

| | asgari (işe yarar) | ideal |
|---|---|---|
| zemin | çıplak sıkıştırılmış toprak, düz bir alan | aynısı, ~20×20 m temiz |
| engel | **6–10 parça** iri moloz/beton/briket, **yığınlar hâlinde** | 3 koridor oluşturacak şekilde dizilmiş |
| HB | basılı 2×2 m ped, yere serili | aynısı |
| bariyer | kırmızı-beyaz şeritli uzun bir çubuk (süpürge sapı + bant olur) | gerçek dubalı bariyer kolu |

**Kritik nokta:** moloz **dağınık serpilmiş değil, YIĞIN hâlinde** olmalı ve
yığınlar **aralarında geçit bırakacak** şekilde dizilmeli. Şartname §2.1
güzergâhları *"moloz yığınları arasında oluşturulmuş üç yol"* diye tanımlıyor.
Tek bir yığın bile olsa, "yığın + yanından geçit" örüntüsü lazım.

## Uçuş

| ayar | değer | neden |
|---|---|---|
| **irtifa** | **30 m** (asgari), ayrıca 25 m ve 40 m'de birer geçiş | §5.3.2 asgari 30 m; ölçek duyarlılığını görmek için üç irtifa |
| **gimbal** | **90° nadir (tam aşağı)** | eğitim dağılımımız nadir; ufuk gören kare işe yaramaz |
| **kare sayısı** | **20–30** yeter | etiketleme insan emeği; azı iyi olan çoğu kötüden değerlidir |
| **çakışma** | kareler arası **kaydırma olsun** | aynı kadrajın 30 kopyası tek kare değerindedir |
| **saat** | öğle değil, **sabah 09–11 veya ikindi 15–17** | tepe güneşi gölgeyi siler, kontrastı bozar |
| **hava** | rüzgârsız, **açık ya da hafif bulutlu** | ikisi de olur; ikisi de çekilirse daha iyi |

⚠ **Gece/alacakaranlık çekmeyin.** `data/dji_prova`'daki 543 kare tam bu yüzden
kullanılamıyor: ortalama parlaklık 19/255, nadir gündüz işine uygun **sıfır**
kare (D-337).

## HB pedi hakkında

- Basılan ped **RAL 3020 kırmızı** olmalı; ölçüldü, eğitim kromamızla LAB `a*`
  değeri **birebir 67**.
- **Yön fark etmez**, H 180° simetriktir ve tespit T184'ten beri açıdan
  bağımsızdır.
- Mat tercih edilir ama **parlak branda da olur** — ölçüldü: pedin bir şeridi
  güneşte %70'e kadar beyaza doysa bile dedektör pedi buluyor.
- 2000 mm **bitmiş** ölçüdür; katlama payı **ilave malzemeden** olmalı, yoksa
  kırmızı çerçeve incelir.

## Çekim sırasında bir kare de şöyle olsun

1. **HB pedi karede** — ölçek çıkarımını (`mpp_hb_pedinden`) gerçek veriyle
   sınamak için.
2. **Bariyer bir geçidi kapatırken** — K5/K5A'nın yer gerçeğini gerçek
   görüntüde sınamak için.
3. **Hiçbir engel olmayan boş bir kare** — modelin çıplak toprağı sürülebilir
   sayıp saymadığını *tek başına* ölçmek için. **Bu kare T192 için en
   kıymetlisidir.**

## Bana ne lazım

Kareleri şuraya koymanız yeter: `data/maket_arena_20260829/`
Yanına bir satır not: **hangi irtifa, hangi saat, hangi cihaz**.

Gerisini ben yaparım: etiketleme (üç durumlu maske hattı), ölçüm, ve
`159_t192_figur_rota.py` ile aynı ölçütün **gerçek** karede koşulması.

## Bu çekim neyi çözer, neyi çözmez

**Çözer:** "model gerçek çıplak toprağı sürülebilir görüyor mu?" — bugün bunu
yalnız yapay zekâ üretimi tek bir figürden tahmin ediyoruz (D-99).

**Çözmez:** yarışma arenasının kendisi bu değildir. n küçük kalacak ve bu
ölçüm de "sahada çalışır" demeyecek. Ama **ilk gerçek zeminimiz** olacak.
