# B2 — FDA 10 DAKİKA BÜTÇESİ, UÇTAN UCA · ön kayıt

Tarih: **2026-09-01** — hiçbir süre ölçümü yapılmadan önce yazıldı (D-107).
(Codex-2 kotaya girdi; işi başamele devraldı — tasarım
`CODEX_PROMPTLARI_20260901.md` B2 ile aynı, betik no **169**.)

## 0. Çerçeve — bütçenin NEYİ kısıtladığı önce netleşir

`SARTNAME_FDA_OPERASYON_SURESI_S = 600 s` (sözleşme, T170/D-318) **görev
zaman çizelgesini** kısıtlar: kalkış → tespit → hakem onayı → iniş → İKA →
HB. Bunun büyük kısmı uçuş/insan işidir ve **PC'de ölçülemez**.

Yazılımın bütçeye giren payı iki türlüdür:
1. **Kare gecikmesi** (yakalama → karar → telsiz → ekran): birikmez,
   tespit penceresi boyunca akar. Bütçeye etkisi, hakemin taze tespiti
   NE KADAR erken görebildiğidir. Bunun sözleşme sınırı zaten var:
   `YKS_TESPIT_TAZELIK_S = 5 s` — gecikme bundan büyükse tespit ekranda
   hiç "taze" olamaz.
2. **Uçuş öncesi hazırlık** (model yükleme/soğuk başlangıç): bütçe DIŞI
   (kalkıştan önce yapılır) — ölçülür, bilgi olarak yazılır; toplama girmez.

## 1. Dondurulan ölçüm

- **Girdi:** `data/dji_gunduz_1280` — 36 gerçek kare (1280 genişlik; üretim
  kamera sınıfı, T174: model 512'de koşar, kaynak 1280×720). **36'sının
  tamamı**, ad sırasıyla (seçim yok).
- **Zincir üretimle birebir** (D-351): `_preprocess` → `predict(512, 0.30)`
  → `get_masks` → `_maskeleri_icerige_kirp` → `rota_olcek_reddi` +
  `analyze_path` → `_rota_kararini_esikle` → `KararYayinci.karar()` →
  UDP loopback'te sahte İKA/YKS **ACK'iyle** gönderim.
- **mpp sabit 0,078125** (t66 sözleşme değeri): ölçülen şey SÜREDİR,
  geometri değil; `analyze_path` maliyeti maske boyutundan gelir. Bu kareler
  için gerçek mpp bilinmiyor — geometri iddiası ÜRETİLMEZ.
- Adım süreleri `time.perf_counter` ile; her adım ayrı, ayrıca uçtan uca
  toplam (yakalama→ACK).
- Isınma: ilk 3 kare ölçüme **girmez** (CUDA ısınması); ayrı raporlanır.

## 2. Eşikler — SONUÇ GÖRÜLMEDEN

- **B2-G1 (kapı):** uçtan uca kare gecikmesi **p95 ≤ YKS_TESPIT_TAZELIK_S
  (5 s)**. Gerekçe: tazelik penceresinden uzun gecikme, tespitin ekranda
  hiç taze görünememesi demektir. Sözleşmeden türedi, uydurulmadı.
- **B2-G2 (kapı):** p95 ≤ **1 s** ise ayrıca `IHA_HEARTBEAT_ARALIK_S` ile
  uyumlu ("her heartbeat dönemine bir karar") — GEÇTİ/GEÇMEDİ ayrı yazılır;
  G1 asıl kapıdır.
- **Bilgi (kapı değil):** model yükleme süresi; adım payları (p50/p95).

## 3. Zaman çizelgesi — ölçülen / varsayılan / ÖLÇÜLEMEDİ

600 s'lik çizelgeye yazılım dışı kalemler şöyle girer:

| kalem | durum |
|---|---|
| kalkış + HTAB'a intikal + tespit uçuşu + iniş | **ÖLÇÜLEMEDİ** (uçuş; B1/saha) |
| hakem sözlü onayı | **VARSAYIM-ÖNERİ: 30 s** — kaynağı YOK; sayıyı mimar/kullanıcı seçer, çizelgede `ÖNERİ` damgasıyla durur |
| İKA intikali | **ÖLÇÜLEMEDİ** (saha) — sözleşme üst sınırı `SARTNAME_IKA_GOREV_SURESI_S` ayrı ve zaten kilitli |
| algı+karar+telsiz kare gecikmesi | **BU ÖLÇÜM** |
| model yükleme | ölçülür, **bütçe dışı** (uçuş öncesi) |

ÖLÇÜLEMEDİ kalemler toplama **0 olarak girmez**; çizelge "600 − bilinenler"
biçiminde pay olarak raporlanır, "sığar/sığmaz" hükmü uçuş kalemleri
ölçülmeden **verilmez**.

## 4. ÖLÇÜLEMEDİ kuralları

- Gerçek telsiz (SiK seri) yok: ACK yolu **UDP loopback** ile ölçülür ve
  öyle etiketlenir; seri hat gecikmesi **ÖLÇÜLEMEDİ** (Gün-1/B1).
- Kamera donanımı yok: "yakalama" = diskten okuma; gerçek kamera yakalama
  gecikmesi **ÖLÇÜLEMEDİ** (Gün-1 §7'de kamera_dogrula ile).
- GPU bu PC'de RTX 5080'dir; Jetson süreleri **bu ölçümden türetilmez**
  (Gün-1 §5 gerçek sayıyı verir). Bu ölçümün işi ZİNCİRİN yapısı ve
  PC referansıdır.
