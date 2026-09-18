# İKİ DAL — ÇAKIŞMA RAPORU (karar için)

**Tarih:** 18 Eylül 2026 · **Yazan:** mimar (Claude 1) · **Amaç:** karar vermek değil, **kararın
ne olduğunu ve neyi etkilediğini görünür kılmak.** Telsiz seçimi ve birleştirme **insan kararıdır**.

| | `master` | `origin/tunel-saha-20260918` |
|---|---|---|
| Son commit | `a967ace6` (18 Eyl) | `7e35405c` (18 Eyl) |
| Ortak ata | `bdda2e3b` | aynı |
| Fark | **+82** commit | **+88** commit |
| Telsiz | **433 MHz** (SiK); RFD900A **yasak** | **RFD900A 915–928 MHz** |
| Taşıyıcı | `KIP=udp \| sik \| ikili` (LAN + SiK) | `KIP=tunel` (MAVLink `TUNNEL`, Pixhawk üzerinden) |
| Video | ONARIM-19: YKİ kaynağı tarayıp buluyor | "video telemetri yok" (kapsam dışı) |

---

## 1. Telsiz çelişkisi — aynı gün, aynı olgu, iki zıt karar

**13 Eylül'de iki taraf da aynı gerçeği gördü:** gövdedeki modül **RFD900A (915 MHz)**, oysa
depo baştan sona **433 MHz** diyordu. Çözümleri ters oldu:

| | Karar | Kayıt |
|---|---|---|
| **Dal** | Gerçek donanım RFD900A → **belgeleri donanıma uydur** (29 yerde 433 → RFD900A) | `d5bf2af5`, `fb2dcf1c` (D-480) |
| **Master** | Kullanıcı kararı: *"433'ü kullanacağız, asla 900 olanı kullanmayacağız"* → **donanımı belgeye uydur** | D-499 |

**Sonraki 5 günde ne oldu:**

* Dal, tüm saha mimarisini RFD900A üzerine kurdu ve **gerçek ölçüm aldı**: ham RFD RTT p95
  **126,5 ms**, kayıp %0 (D-478/479, Air Speed 128).
* Master 433 varsayımıyla ilerledi, ama **433'lük donanım hiç gelmedi**: `ONARIM-09` kendi
  kaydında *"gerçek SiK koşusu yok"* diyor. **Master'ın telsiz hattı bugüne kadar hiç ölçülmedi.**

**Bugünkü fiziksel gerçek:** elde RFD900A **var ve ölçülmüş**; 433'lük çift **yok**.
Yarın uçulacaksa, ortada yalnızca RFD900A olduğu için **fiilen dal mimarisiyle uçulur** —
`master`'ın telsiz kararı bir donanım siparişine bağlıdır, bugünkü uçuşa değil.

## 2. 🔴 Dalın kendi kapısı DÜŞTÜ — bu, telsiz seçiminden bağımsız bir risk

`D-494` (18 Eyl, dalın kendi ölçümü): **K8 DÜŞTÜ.**
K8a kayıp %3,5 · p95 **268 ms** · K8b p95 **360 ms** · eşik **200 ms** ·
473 B'lık `OPEN_ROUTE` çerçevesinde **%43 kayıp**.

Anlamı: tünel taşıyıcısı çalışıyor ama **rota mesajları güvenilir taşınmıyor.** Uçuşta YKİ'ye
rota gelmemesi ya da geç gelmesi beklenmelidir. Bu, birleştirme kararından ayrı ve **uçuştan
önce** karara bağlanmalı (eşik gevşetilmesi bir seçenek değil — ön kayıtlı).

## 3. REVIEW_LOG numara çakışması — birleştirmenin en kirli yeri

`D-469` … `D-486` aralığı **iki dalda tamamen farklı olayları** anlatıyor. Örnekler:

| No | `master` | dal |
|---|---|---|
| D-478 | İKA URDF kütle kusuru | ✅ A6 GEÇTİ (RFD RTT 126,5 ms) |
| D-479 | T261 mesh yolu düzeltmesi | Mimarın teşhisi çürütüldü (Air Speed 64→128) |
| D-480 | İKA gerçek kütlesi 7,56 kg | Belgelerde 433 → RFD900A |
| D-482 | FDR durum güncellemesi | 13 Eylül uçuş logları okundu |

Master ayrıca `D-487`…`D-503`'ü, dal `D-485`/`D-486`'yı kullanmış. **Otomatik birleştirme bu
dosyada anlamlı sonuç vermez**; REVIEW_LOG elle, karar karar çözülmeli (bir taraf yeniden
numaralanmalı — master bunu bir kez yaptı: `ONARIM-11`, D-477…484 → D-495…502).

## 4. Kodda çakışacak dosyalar

Her iki dalda da değişen **33 dosya** var. Kritik olanlar:

| Dosya | Neden çakışır |
|---|---|
| `comms/seri_hub.py` | master: LAN aynası + keşif · dal: `--tunel` taşıyıcısı |
| `comms/yks_gui.py` | master: `--coklu`, `--eslesme`, `--video-tara` · dal: `--tunel` |
| `comms/link.py` | master: `CokluLink` · dal: `TunelLink` |
| `comms/iha_inis_yayinci.py` | master: kalkış kapısı (ONARIM-18) · dal: D-495 aynı konu, **ayrı çözüm** |
| `jetson_paket/jetson_baslat.sh` | master: `KIP=ikili` · dal: `KIP=tunel` |
| `CONTRACTS.md` | master §7.5'te bitiyor · dal §7.6 (TUNNEL sözleşmesi) ekliyor |
| `REVIEW_LOG.md` | yukarıdaki numara çakışması |

**İyi haber:** bu değişiklikler çoğunlukla **eklemeli**. `KIP` üç değer yerine dört değer alabilir
(`udp | sik | ikili | tunel`), `Link` sınıfları yan yana durabilir. Yani birleştirme teknik olarak
mümkün; zor olan **hangi düzenin "saha düzeni" sayılacağına karar vermek.**

## 5. Karar gereken üç şey (insan)

1. **Telsiz:** RFD900A mı (elde var, ölçüldü) yoksa 433 MHz mi (belge kararı, donanım yok)?
   Bu karar verilmeden birleştirme yapılmamalı — iki dal bu noktada ters.
2. **Saha taşıyıcısı:** `tunel` (tek telsiz, Mission Planner ile paylaşımlı, **K8 düştü**) mü,
   yoksa `ikili`/`sik` (ayrı telsiz çifti gerekir, henüz ölçülmedi) mi?
3. **Birleştirme zamanı:** Emir tarafı "uçuştan sonra" diyor (T278). Katılıyorum — bugün
   birleştirmek, ölçülmüş bir düzeni ölçülmemiş bir düzenle karıştırma riski taşır.

## 6. Birleştirme yapılacaksa önerilen sıra (uçuştan SONRA)

1. Telsiz kararı yazıya geçsin, **tek** karar kaydı olsun (iki D numarası değil).
2. REVIEW_LOG'da bir taraf yeniden numaralansın (master bunu daha önce yaptı, yordam belli).
3. Kod eklemeli birleştirilsin: `KIP` dört değerli, `Link` sınıfları yan yana, `CONTRACTS` §7.6 eklensin.
4. Birleşik dalda **tam süit + genel kapı** koşulsun; K8 yeniden ölçülsün (düşük eşik gevşetilmeden).
