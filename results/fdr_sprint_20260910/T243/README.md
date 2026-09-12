# T243 — mesaj paket boyutu + gerçek görev veri hızı · **ÖLÇÜM**

**Kayıt:** D-462 C · yönerge maddesi Y-3.3.4-M03
**Ön kayıt:** `ON_KAYIT.md` (bu dizinde; ölçümden **önce** yazıldı, ayrı commit)
**Araç:** `scripts/paket_boyutu_olc.py` · **Tarih:** 12 Eylül 2026
**Etiket:** `olcum` — RF **değildir** (UDP loopback).

---

## Komut (yeniden üretmek için)

```
O:\navitas-local-train\venv\Scripts\python.exe -X utf8 -B ^
  scripts/paket_boyutu_olc.py --kip hepsi --pencere 60 ^
  --cikti-dizin results/fdr_sprint_20260910/T243
```

Ham çıktı: `kosum_ciktisi.txt`. Tablo `TABLO.md` bu komutla **üretilir**, elle
yazılmaz.

## Dosyalar

| dosya | içerik |
|---|---|
| `ON_KAYIT.md` | ölçülecek nicelikler, yöntem, rapor ölçütü, tohum (ölçümden önce) |
| `paket_boyutu.json` | N1–N5 — `protocol.encode()` ile sayılmış gerçek baytlar |
| `gorev_veri_hizi.json` | N6–N12 — dört koşumun bayt/paket sayaçları ve hız sözlükleri |
| `TABLO.md` | iki JSON'dan üretilen okunur tablo |
| `kosum_ciktisi.txt` | ölçümün ham stdout'u |
| `kosum_ciktisi_v1_eksik.txt` | **eksik** ilk koşumun ham çıktısı — aşağıya bakınız |

## Ölçülen ne, ölçülmeyen ne

**Ölçüldü:** her mesaj tipinin gerçek `encode()` bayt boyutu; `OPEN_ROUTE`'un
waypoint sayısına göre eğrisi; tam telemetrili ve asgari `HEARTBEAT`;
`HEARTBEAT` alanlarının marjinal maliyeti; `seq`/`t` genişliğinin bayt etkisi;
gerçek üretim yollarıyla (`IhaSender` + `KararYayinci` + `IkaReceiver`) dört
koşumda gönderilen bayt/paket, ortalama ve tepe veri hızı, ortak ortam yükü.

**ÖLÇÜLEMEDİ:** SiK 433 MHz RF hattında fiilî veri hızı; telsizin hava hızı
(Air Speed). **ECC durumu: ÖLÇÜLEMEDİ** — SiK ayar sayfası hiç okunmadı
(`results/atolye_20260912/SONUC_SABLONU.md` A6 satırı boş, `A6_sik_ayar.txt`
yok). Bu üçü FDR §3.3.4.3.4'te **ÖLÇÜLEMEDİ** olarak kalır; buradaki sayılar
onların yerine geçmez. ECC açıkken etkin hava hızının yarıya indiği bilgisi
`ATOLYE_TEST_GUNU_20260912.md` A6 satırından **alıntıdır** ve orada
*"HESAP + BENZER ÖLÇÜM — ölçüm değil"* etiketiyle durur.

**HESAPTIR, ölçüm değildir:** 57600 8N1 ham bütçesi (10 bit/bayt → 5760 B/s,
0,174 ms/bayt); hat doluluk oranları; görev süresi boyunca toplam bayt
(ekstrapolasyon, 900 s'lik koşum yapılmadı); §8 duyarlılık satırı.

## Sonuçlar (ayrıntı `TABLO.md`)

- Çerçeve boyutları: `IHA_LANDED` 71 B · `ACK` 87 B · `NO_ROUTE` 117 B ·
  `CMD` 124 B (`oturum` alanlı) · tam telemetrili `HEARTBEAT` 273 B ·
  21 waypoint'li `OPEN_ROUTE` 365 B. Kodda geçen `~200 B cerceve` tasarım notu
  gerçek çerçevelerin **altındadır**.
- `OPEN_ROUTE` eğimi 11,5 B/waypoint (üretim yolu), 16,0 B/waypoint (en geniş
  gösterim); sözleşme tavanındaki rota 847 B'ye çıkar.
- Görev karışımında İHA TX 1722,3–2008,7 B/s, 5,0–6,0 pkt/s; ortak ortam yükü
  2063,1–2148,5 B/s; tepe TX 1728–2364 B/s.
- Görev toplamı (ekstrapolasyon): İHA 900 s'de 1 550 097–1 807 864 B,
  İKA 600 s'de 1 033 398–1 205 243 B.
- 🔴 **Ölçümün asıl bulgusu:** karar **yayın** tavanı ≈ 1 karar/s. 1,353 Hz ve
  2,0 Hz beslemede yayınlanan karar sayısı değişmedi (saha 61/61, udp 50/50);
  her karar `repeat=4 × interval=0,25 s` = 1,0 s boyunca tutuluyor ve
  latest-wins yuvası fazlasını düşürüyor.

## Rapor ölçütünün karşılığı

Ölçülen en yüksek paylaşımlı doluluk **%37,30** (`udp_tavan`).
**RAPOR ÖLÇÜTÜ (ON_KAYIT §4 madde 2):** Hat doluluk oranı yüzde 80,0 ya da üzeri çıkarsa kırmızı risk satırı açılır.
Ölçülen değer bu oranın altında kaldığı için risk satırı **açılmadı**.

Bu bir kapı değildir; hüküm "ölçüldü"dür, "geçti" değildir.

Ayrı ve **hesaba** dayalı bir uyarı kayda geçer: `TABLO.md` §8, rota sözleşme
tavanındaki waypoint sayısına çıkarsa ortak ortam yükünün 3715,4–4003,6 B/s'ye
taşındığını gösterir; ECC açık sütunu ham bütçeyi aşar. Bu bir ölçüm değil,
ölçülen iki büyüklüğün çarpımıdır ve telsiz ayarı okunmadan hükme bağlanamaz.

## İlk koşum neden değiştirildi (şeffaflık)

İlk koşum (`kosum_ciktisi_v1_eksik.txt`, aynı pencere, aynı kadanslar) ortak
ortam yükünü **eksik** sayıyordu: saha yapılandırmasında alıcı ACK üretmiyordu
(`send_ack=False`) ve üretilen ACK baytları hiçbir sayaca girmiyordu. Üretimde
`IkaReceiver.send_ack` varsayılanı `True`'dur ve o baytlar SiK'in ortak hava
kanalında **yer kaplar**. Düzeltilen koşum aynı pencereyle yeniden koşuldu ve
paylaşımlı doluluk **%29,90 → %35,82**'ye (saha) **yükseldi**. Yani düzeltme
sayıyı iyileştirmedi, **kötüleştirdi**; ilk çıktı silinmedi, bu dizinde durur.

## Sınırlar

1. UDP loopback ölçümüdür. RF yoktur; menzil, paket kaybı, SiK'in kendi
   çerçeveleme/ECC katmanı ve TDM dilim beklemesi burada yoktur.
2. `saha` koşumu SiK seri yolunun **UDP ikizidir** (tek yayın ortamı,
   `wait_ack=False`), seri portun kendisi değildir.
3. Rota geometrisi sentetiktir; **boyutlar sentetik değildir**, gerçek
   `protocol.encode()` çıktısından gelir.
4. 2,0 Hz satırı ölçülen bir kadans değil, **tavan senaryosudur**.
5. Kadans 1,353 Hz Jetson `pt` p50 739,076 ms ölçümünden gelir
   (`results/jetson_20260906/jetson_fps_20260906_orin_nano/ozet.json`); uçuş
   modeli `.pt`'dir (D-431).

## Kilit

Nöbetçi test `tests/test_t243_paket_boyutu.py`: FDR'deki ve bu README'deki her
sayıyı JSON'dan **yeniden hesaplar** (bayat sayı kilidi), ölçüm betiğini
yeniden koşarak paket boyutu tablosunun `protocol.encode()` ile hâlâ bayt-eş
olduğunu doğrular ve belge kilidi kurallarını uygular. Kilidin normalleştirme
fonksiyonları o dosyada **tek yerde** toplanmıştır ve **T242 ile kanonik
yardımcıya (`tests/belge_kilidi.py`) geçirilecektir** (D-460, D-461).
