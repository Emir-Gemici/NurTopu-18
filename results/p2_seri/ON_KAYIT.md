# ÖN KAYIT — P2: SerialLink'i radiosuz sına (plan v2)

**Tarih:** 2026-09-02 · **Yazan:** Claude 2 (Opus 5, amele) ·
**Ön kayıt D-107 gereği SONUÇ GÖRÜLMEDEN yazıldı.**

## 0. Neden

`comms/link.py` `SerialLink` saha taşıyıcısıdır (SiK 433 MHz, transparan seri)
ama bugüne dek **yalnız sahte seri nesnesiyle** sınandı; `pyserial` venv'de
kurulu bile değildi (2026-09-02 öncesi `find_spec('serial')` = None).
D-383 §1 bunu zaten uyarmıştı: **B2-G2 "GEÇTİ" yalnız UDP-loopback içindi.**

UDP ile seri arasındaki fark tesadüfi değil, **sınıfsaldır**: UDP datagramdır,
mesaj sınırlarını korur. Seri hat **bayt akışıdır** — sınır yoktur. Çerçeveleme
(`protocol.FrameReader`, newline) bu farkı kapatmak zorundadır ve gerçek bir
bayt akışında hiç koşmadı.

## 1. Bu ölçümün sorusu

> Üretim mesaj katmanı (`IhaSender` + `FrameReader` + `SerialLink`) **gerçek
> pyserial bayt akışı** üzerinde, UDP'deki sözleşmenin aynısını üretiyor mu —
> parçalanma, birleşme ve RF gürültüsü altında?

Sahte nesne değil: gerçek `pyserial`, gerçek bayt akışı, iki ayrı uç.

## 2. Kapı ölçütleri (sonuç görülmeden yazıldı)

| # | senaryo | GEÇTİ ölçütü |
|---|---|---|
| S1 | Mutlu yol turu (iki uçlu SiK köprüsü) | İHA OPEN_ROUTE yollar, İKA ayrıştırıp ACK döner, `IhaSender` ACK'i görür (`acked` kümesi dolar) |
| S2 | Parçalanma | Tek mesaj bayt bayt (1 baytlık parçalar) gelse de `FrameReader` **tam ve birebir** mesajı üretir |
| S3 | Birleşme | Tek okumada 3 mesaj gelirse **üçü de** ayrışır, sırası korunur |
| S4 | Bozuk bayt (RF gürültüsü) | Araya çöp enjekte edilince bozuk çerçeve **atılır** ve **sonraki geçerli çerçeve yine ayrışır** (kurtarma) |
| S5 | Tampon disiplini | 1 MiB newline'sız çöp beslendiğinde `FrameReader` iç tamponu **≤ 64 KiB** kalmalı (sınırsız büyümemeli) |
| S6 | SerialLink API | Gerçek pyserial nesnesiyle `send`/`recv` çalışır; veri yokken `recv` → `(None, None)` |
| S7 | Genel kapı | `codes/test_rota_sentetik.py` 15/15 **ve** tam suit OK |

**S5 eşiği gerekçesi (şimdi yazıldı):** SiK hattında gürültü newline üretmeden
uzun süre akabilir. Sınırsız tampon, 15 dakikalık uçuşta Jetson'da sessiz
bellek büyümesi demektir; ayrıca çöp biriktikçe `split` maliyeti artar.
64 KiB, en uzun meşru çerçevemizin (heartbeat + rota, < 4 KiB) **on altı
katıdır** — meşru trafiği asla kesmez.

**Reddetme kuralı:** S1–S7'den biri düşerse P2 "bitti" sayılmaz; sebep
`REVIEW_LOG.md`'ye yazılır. Eşikler sonuca göre gevşetilmez.

## 3. Yöntem — iki uçlu gerçek seri köprü

`loop://` tek uçludur (yazan kendi yazdığını okur), iki taraflı ACK turunu
sınayamaz. Bu yüzden testte **SiK köprüsü** kurulur: TCP röle iki
`serial_for_url("socket://…")` ucunu karşılıklı pompalar — SiK telsizin
transparan davranışının birebir karşılığı. Her iki uç **gerçek pyserial**
nesnesidir; bayt akışı gerçektir. S4'te röle, yönlerden birine kasten çöp
enjekte eder.

## 4. Not — bu ölçüm neyi KANITLAMAZ

Gerçek RF yoktur: menzil, paket kaybı, SiK'in kendi çerçeveleme/ECC katmanı,
baud uyuşmazlığı ve gecikme burada yoktur. P2 "bayt akışı + çerçeveleme"
katmanını kapatır; **433 MHz RF ölçümü Faz B'de (5 Eylül).**
`OLCULEMEDI != GECTI`.

---

## 5. SONUÇ (2026-09-02, ölçüm sonrası yazıldı)

| # | sonuç | kanıt |
|---|---|---|
| S1 | **GEÇTİ** | İki uçlu gerçek seri köprüde OPEN_ROUTE → İKA ACK → `IhaSender` ACK'i gördü |
| S2 | **GEÇTİ** | Mesaj **bayt bayt** (1 baytlık parçalar) gönderildi; birebir toparlandı |
| S3 | **GEÇTİ** | Tek okumadaki 3 çerçeve sırasıyla ayrıştı (1, 2, 3) |
| S4 | **GEÇTİ** | Bozuk bayt atıldı, **sonraki geçerli çerçeve okundu**; bozuk çerçeve mesaj olarak sızmadı |
| S5 | 🔴 **DÜŞTÜ → DÜZELTİLDİ** | 1 MiB çöp → tampon **1.048.576 bayt** (tavan 65.536). Sebep: `FrameReader._buf` sınırsız. **Düzeltildi** (D-388): tavan sözleşmeye girdi, aşan birikim atılıyor + `atilan_bayt` sayacı. Düzeltme sonrası GEÇTİ |
| S6 | **GEÇTİ** | Gerçek `pyserial` nesnesiyle `send`/`recv`; veri yokken `(None, None)` |
| S7 | **GEÇTİ** | genel kapı 15/15 · tam suit **1489 test OK** |

**Ek ölçütler (düzeltmeyle birlikte, ölçümden sonra eklendi — gate değil kilit):**
S5b meşru büyük çerçeve (200 waypoint) tavanın çeyreğinin altında ve sorunsuz
ayrışıyor · S5c çöp atıldıktan sonra hat toparlanıyor · S5d **meşru çerçevenin
peşindeki dev çöp o çerçeveyi yutmuyor** (süzme, atmadan önce yapılıyor) ·
S6b `serial_for_url` değişikliği cihaz yolu sözleşmesini bozmuyor.

**⚠ Ön kayıt gevşetilmedi:** S5 yazıldığı eşikle (64 KiB) düştü, düşüşü
kaydedildi, **kod düzeltildi**, aynı eşikle yeniden koşuldu. Eşik sonuca göre
değiştirilmedi.

**P2 KAPANDI** (yazılım tarafı). RF ölçümü Faz B'de.
