# CODEX GÖREV PROMPTLARI · 2026-08-31 · Veren: Claude 2 (ustabaşı)

> ✅ **PUSH SERBEST** — ama **kapı kırmızıyken push YOK** (D-360). Suit **ayrı**
> koşulur, çıktısı **okunur**, ancak sonra commit + push.
> 🔴 **Commit yazarı deponun kendi yapılandırmasından gelir**
> (`Emir-Gemici <yunusgemici2007@gmail.com>`); `-c user.email` ile **EZME**
> (D-356). **AI atfı yok** (madde 17).
>
> **Bağlam:** `FDA_PLANI_20260829.md` · FDA **21-25 Eylül** · test uçuşu
> **ikili (100/0)** · enkaz alanına girdikten sonraki görüntü işleme arızası
> **telafi sebebi değil**.
>
> **Kullanıcı kararları (2026-08-31):** A2 **onaylandı** · sahada **FP16**
> kullanılacak (D-371) · **FAZ B öne çekildi**.

---

## CODEX-1 · A2 — TESPİT YAŞI (`karar_yas`) · SÖZLEŞME DEĞİŞİKLİĞİ ONAYLI

```text
GOREV EMRI · Codex-1 · A2 · TESPIT YASI (karar_yas)
Veren: Claude 2 (ustabasi) · 2026-08-31. Once CODEX_WORKERS.md'yi oku.
Master'in SON halinden basla. A1 (8c34884) BITTI ve DENETLENDI (D-369).

── YORUMLAYICI — HER ZAMAN bu tam yol ──────────────────────────────────────
  O:\navitas-local-train\venv\Scripts\python.exe
"python" Windows Store saplamasidir; SESSIZCE hicbir sey yapmaz.

── NEDEN (sartname + duyuru) ───────────────────────────────────────────────
TEKNOFEST duyurusu (2026-08-29): test ucusu IKILIDIR (100 ya da 0) ve
sartlarindan biri "GERCEK ZAMANLI olarak YKS'ye aktarilan guzergah tespitinin
hakem heyeti tarafindan ONAYLANMASI".
Sartname SS6.4: "veri akisinin saglanamadigi durumlarda ucus GECERSIZ."

── KUSUR — USTABASI OLCTU, TAHMIN DEGIL ────────────────────────────────────
comms/yks_gui.py:988   ->  self.rota_zaman = time.time()      # ALIM zamani
comms/yks_gui.py:2499  ->  yaslar.append(simdi - self.rota_zaman)
comms/yks_gui.py:~2503 ->  _hb = son_hb["iha"]; yaslar.append(simdi - _hb)
                           yas = min(yaslar)

🔴 `min()` BILINCLIDIR, KORLEMESINE KALDIRMA. T172/D-321'de olculdu: IHA
rotayi ACK ALANA KADAR tekrarlar, ACK gelince SUSAR. Yalniz rota yasina
bakmak protokolun NORMAL davranisini ariza sayiyordu; demo kipinde IKA
ACK'ledikten 5 sn sonra hakemin onay dugmesi KAPANIYORDU. `min()`i kaldirirsan
D-321'i GERI GETIRIRSIN.

GERCEK BOSLUK: heartbeat AYRI IS PARCACIGINDA uretilir
(CONTRACTS:862 — `IHA_HEARTBEAT_ARALIK_S = 1.0`). Algi hatti ASILIRSA
heartbeat AKMAYA DEVAM EDER ve ekran "CANLI" der. Yani HAT CANLILIGI ile
ALGI CANLILIGI birbirine karistiriliyor. Hakem bir saat once uretilmis bir
tespiti "gercek zamanli" sanip ONAYLAYABILIR.

── COZUM (ustabasi tasarimi — bunu uygula) ─────────────────────────────────
Karar yasi OPEN_ROUTE'a DEGIL, HEARTBEAT'e konur. Sebep: IHA ACK'ten sonra
OPEN_ROUTE gondermeyi BIRAKIR ama heartbeat AKMAYA DEVAM EDER. Yani algi
canliligini tasiyabilecek TEK kanal heartbeat'tir.

1) comms/protocol.py
   HEARTBEAT_TELEMETRI_ALANLARI = ("x","y","alt","hiz","bat","uydu")
   demetine "karar_yas" EKLE. Mevcut fail-closed kalip AYNEN korunur:
     · alan None ise YAZILMAZ (sifir DEGIL) — "bilmiyorum" ile "0 sn" ayri
     · sozlesme disi alan ValueError

2) IHA tarafi (codes/rpi_inference.py — kamera/karar dongusu)
   Her KARAR uretiminde MONOTONIK bir damga tut. KARAR = analyze_path'in
   DONDUGU AN; rota CIKSA DA CIKMASA DA (NO_ROUTE de bir karardir) damga
   tazelenir. Heartbeat gonderilirken:
       karar_yas = time.monotonic() - son_karar_damgasi
   ⚠ `time.time()` DEGIL `time.monotonic()`: saat esitlemesi YOK, duvar saati
   geri atlayabilir.
   ⚠ HENUZ HIC KARAR URETILMEDIYSE alan GONDERILMEZ (0 gonderme).

3) comms/yks_gui.py
   KARAR KUTUSU tazeligi artik `karar_yas`a bakar:
     · karar_yas VARSA ve > YKS_TESPIT_TAZELIK_S  -> karar BAYAT, onay dugmesi
       KAPANIR (mevcut bayatlik davranisi AYNEN kullanilir)
     · karar_yas VARSA ve <= esik -> mevcut davranis (heartbeat yedegi DAHIL)
       BIREBIR korunur
     · karar_yas YOKSA (eski IHA / alan gelmiyor) -> "TESPIT YASI BILINMIYOR"
       yazilir ve karar kutusu TAZE SAYILMAZ.
       🔴 EKSIK ALAN "TAZE" DEMEK DEGILDIR. Bu, D-321'i geri getirmez cunku
       yeni IHA alani HER heartbeat'te gonderir; alan yoklugu yalniz
       ESKI/BOZUK bir yayinci demektir ve o durumda hakem onaylamamalidir.
   HAT canliligi icin heartbeat kullanimi DEGISMEZ.

4) CONTRACTS.md SS6
   HEARTBEAT satirina `karar_yas` alani ve anlami yazilir:
   "IHA'nin son ALGI KARARININ yasi (sn, monotonik). Alan YOKSA yas
    BILINMIYOR demektir; TAZE sayilmaz."

── NOBETCI TEST (ZORUNLU) ──────────────────────────────────────────────────
Yeni dosya: tests/test_a2_karar_yasi.py

  a) SOZLESME: karar_yas alani var; None ise YAZILMIYOR; sozlesme disi alan
     hala ValueError.
  b) MONOTONIK: uretici `time.monotonic()` kullaniyor (AST ile denetle,
     METIN ARAMASIYLA DEGIL — docstring'de gecen ad "kullanim" sanilir;
     D-354/D-361'de tam bu hata yapildi).
  c) DAVRANIS — ASIL KAPI: heartbeat AKARKEN karar_yas esigi ASARSA karar
     kutusu BAYAT olmali ve onay dugmesi KAPANMALI. Bu, bugun YAKALANAMAYAN
     senaryodur.
  d) GERILEME KORUMASI (D-321): karar_yas TAZE iken, IHA ACK sonrasi
     OPEN_ROUTE gondermeyi biraksa bile onay dugmesi ACIK KALMALI.
     Bu testi YAZMADAN isi bitmis sayma — D-321 tam bu yuzden olustu.
  e) EKSIK ALAN: karar_yas YOKSA "BILINMIYOR" gorunur ve TAZE SAYILMAZ.
  f) MUTASYON: karar_yas denetimi kaldirilirsa (c) DUSMELI. Mutasyonu KOD
     uzerinde yap, YORUM uzerinde DEGIL.
  g) CAPA: tazelik islevi Tk penceresi ACMADAN cagrilabiliyor mu.

── KAPILAR (ikisi de ZORUNLU, AYRI kosulur) ───────────────────────────────
  <venv> codes/test_rota_sentetik.py            -> 15/15
  <venv> -m unittest discover -s tests          -> OK
🔴 Suit'i commit/push ile AYNI ZINCIRDE kosma; once kos, CIKTIYI OKU.

── YASAKLAR ────────────────────────────────────────────────────────────────
· `min(yaslar)` mantigini KORLEMESINE kaldirma (D-321).
· Esik uydurma: YKS_TESPIT_TAZELIK_S = 5.0 MEVCUT ve gerekcesi yazili.
  Yeni bir sayi gerekiyorsa ONERI olarak bildir, mimar karar verir.
· Eksik alani 0 ile doldurma (fail-closed kalibi bozar).
· Kuyruga gorev EKLEME; oneri olarak bildir.

── RAPOR ───────────────────────────────────────────────────────────────────
1. Degistirilen dosyalar + satir araliklari
2. Nobetci test adi ve test sayisi
3. (c) ve (d) testlerinin HAM ciktisi — ikisi birlikte gorulmelidir
4. MUTASYON kontrolunun GERCEKTEN dustugunu gosteren cikti
5. Iki kapinin HAM ciktisi
6. CONTRACTS SS6 satirinin YENI hali
7. REVIEW_LOG kayit ONERISI (sen YAZMA)
```

---

## CODEX-2 · B2 — 10 DAKİKALIK BÜTÇENİN UÇTAN UCA ÖLÇÜMÜ (T15)

```text
GOREV EMRI · Codex-2 · B2 · FDA 10 DAKIKA BUTCESI UCTAN UCA
Veren: Claude 2 (ustabasi) · 2026-08-31. Once CODEX_WORKERS.md'yi oku.
⚠ comms/yks_gui.py ve comms/protocol.py'ye DOKUNMA — Codex-1 orada.

── YORUMLAYICI ─────────────────────────────────────────────────────────────
  O:\navitas-local-train\venv\Scripts\python.exe

── NEDEN ───────────────────────────────────────────────────────────────────
TEKNOFEST duyurusu (2026-08-29): "Tum gorev surecinin MAKSIMUM 10 DAKIKA
icerisinde tamamlanmasi." Ucus IKILIDIR: asilirsa 0 puan.

Kod bu butceyi BILIYOR (karar_sozlesmesi, T170/D-318 — FDA'nin 10 dk'si
SS6.2'nin 15 dk'sindan AYRI tutulmus). AMA butcenin UCTAN UCA olcumu
YAPILMADI (kuyrukta T15 ACIK).

── YAPILACAK ───────────────────────────────────────────────────────────────
Yeni betik: scripts/olcum/163_fda_butce_olcumu.py

Gorev zincirinin HER adimini SURE olarak olc ve toplami butceyle kiyasla:
  1. model yukleme (soguk baslangic dahil)
  2. kare yakalama -> _preprocess
  3. cikarim (model.predict)
  4. get_masks + _maskeleri_icerige_kirp
  5. analyze_path
  6. _rota_kararini_esikle
  7. telsiz yayini (loopback; gercek telsiz YOK ise bunu ACIKCA yaz)
  8. hakem onayi icin gereken EN AZ sure (insan; SABIT bir varsayim yaz ve
     nereden geldigini soyle)

⚠ URETIM CAGRI SIRASI BIREBIR kullanilacak; kisayol alirsan olctugun sey
URETIM DEGILDIR.

── ON KAYIT — OLCUMDEN ONCE ────────────────────────────────────────────────
`results/fda_butce/ON_KAYIT.md` dosyasina, SAYILARI GORMEDEN once yaz:
  · kac kare uzerinde olculecek (n)
  · hangi yuzdelik raporlanacak (p50 / p95)
  · "kabul edilebilir" ne demek: toplam sure <= ? sn ve MARJ ne kadar
  · hangi adimlar OLCULEMEDI sayilacak (ornek: gercek telsiz yoksa)
Sonuclari gorup olcut degistirmek YASAKTIR (D-107).

⚠ MARJ UYDURMA. Butce 600 sn'dir; "kabul edilebilir toplam"i sen SEC ve
GEREKCESINI yaz (ornek: hakem onayi + kalkis + inis icin ayrilan pay).
Gerekce yoksa oneri olarak birak, mimar karar versin.

── NOBETCI TEST ────────────────────────────────────────────────────────────
tests/test_b2_fda_butcesi.py
  a) Betik URETIM cagri sirasini kullaniyor (AST ile).
  b) Butce sabiti karar_sozlesmesi'nden TURETILIYOR, betikte CIPLAK
     yazilmiyor (madde 16).
  c) OLCULEMEDI adimlar toplama 0 olarak GIRMIYOR — ayri raporlaniyor.
  d) MUTASYON: bir adim toplamdan dusurulurse test DUSMELI.

── KAPILAR ─────────────────────────────────────────────────────────────────
  <venv> codes/test_rota_sentetik.py   -> 15/15
  <venv> -m unittest discover -s tests -> OK
Suit'i AYRI kos, ciktiyi OKU, sonra commit.

── YASAKLAR ────────────────────────────────────────────────────────────────
· comms/yks_gui.py, comms/protocol.py'ye DOKUNMA.
· Model EGITME; GPU'yu uzun sure mesgul etme.
· Uretim kodunu degistirme — bu is bir OLCUMDUR.
· Gercek telsiz yoksa "olculdu" DEME; OLCULEMEDI yaz.

── RAPOR ───────────────────────────────────────────────────────────────────
1. ON KAYIT dosyasinin TAM metni
2. Adim adim sure tablosu (p50/p95) — HAM
3. Toplam ve MARJ
4. OLCULEMEDI kalan adimlar ve NEDEN
5. Nobetci test adi + mutasyon ciktisi
6. Iki kapinin HAM ciktisi
```
