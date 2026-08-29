# CODEX GÖREV PROMPTLARI · 2026-08-29 · Veren: Claude 2 (ustabaşı)

> Her bloğu ilgili Codex ajanına **AYNEN** yapıştır.
> ✅ **PUSH SERBEST** (kullanıcı emri 2026-08-28, `CLAUDE.md §5`) — ama
> **kapı kırmızıyken push YOK** (D-360). Suit **ayrı** koşulur, sonucu
> **okunur**, ancak sonra commit + push.
> 🔴 **Commit yazarı deponun kendi yapılandırmasından gelir**
> (`Emir-Gemici <yunusgemici2007@gmail.com>`). `git -c user.email=...` ile
> **EZME** (D-356). **AI atfı yok** (madde 17).
>
> **Dayanak:** `FDA_PLANI_20260829.md` · TEKNOFEST duyurusu 2026-08-29 ·
> REVIEW_LOG D-368.
>
> ⚠ **KİLİT ÇAKIŞMASI:** Codex-1 `comms/yks_gui.py`'ye dokunur, Codex-2
> dokunmaz. **A2 görevi (`karar_yas`) A1 BİTMEDEN BAŞLAMAZ** — aynı dosya.

---

## NEDEN BU İKİ İŞ ÖNCE

TEKNOFEST duyurusu (2026-08-29): test uçuşu **ikilidir (100 ya da 0)** ve
şartlarından biri *"gerçek zamanlı olarak YKS'ye aktarılan güzergâh
tespitinin **hakem heyeti tarafından onaylanması**"*.

Şartname §6.4 aynı şeyi uçuş geçerliliğine bağlıyor:

> *"Aktarılan verinin doğruluğunun Alan Hakemi tarafından **teyit
> edilemediği** … durumlarda uçuş **GEÇERSİZ** sayılacaktır."*

Ve duyuru: **enkaz alanına girdikten sonra görüntü işleme arızası telafi
sebebi DEĞİLDİR.** İkinci şans yok.

---

## CODEX-1 · A1 — HAKEM EKRANI ROTAYI YANLIŞ YERE ÇİZİYOR

```text
GOREV EMRI · Codex-1 · A1 · HAKEM EKRANI ROTA ANKORU
Veren: Claude 2 (ustabasi) · 2026-08-29. Once CODEX_WORKERS.md'yi oku.
Master'in SON halinden basla. Dayanak: FDA_PLANI_20260829.md FAZ A.

── YORUMLAYICI — HER ZAMAN bu tam yol ──────────────────────────────────────
  O:\navitas-local-train\venv\Scripts\python.exe
"python" komutu Windows Store saplamasidir: SESSIZCE hicbir sey yapmaz, hata
bile vermez. Onu kullanirsan testlerin "gecti" saniyorsun ama HIC KOSMADI.

── KUSUR (kendim olctum, 2026-08-29) ───────────────────────────────────────
comms/yks_gui.py:746

    ref = self.rota.get("ref_xy") or [25.0, 2.0]

`[0.0, 0.0]` BOS OLMAYAN bir listedir, yani TRUTHY. Dolayisiyla `or`
yedegi ASLA devreye girmez ve uretimin gonderdigi [0,0] AYNEN kullanilir.

Sozlesme ne diyor (codes/karar_sozlesmesi.py:160-162):

    # Saha yayin referansi (CONTRACTS SS6.5): uretim yolunda dunya cercevesi
    # YOKTUR; ref_xy her zaman YEREL ANKOR [0, 0]'dir ve IKA saf oteleme yapar.
    YAYIN_REF_XY = (0.0, 0.0)

Yani URETIM DOGRU. Kusur GUI'dedir: yerel ankoru DUNYA koordinati sanip
haritanin (0,0) kosesinden cizmeye basliyor. Sonuc: yesil rota oku arenanin
guneybati kosesine duser ve UC SERIDIN DE DISINDA kalir.

DEMO kipi `ref_xy=[25,2]` yolladigi icin PROVA DOGRU, SAHA YANLIS gorunur —
kusuru en tehlikeli hale getiren sey budur.

NEDEN KRITIK: hakem ekranda gordugu guzergahi ONAYLAYACAK. Sartname SS6.4:
"Aktarilan verinin dogrulugunun Alan Hakemi tarafindan TEYIT EDILEMEDIGI ...
durumlarda ucus GECERSIZ sayilacaktir." TEKNOFEST duyurusu (2026-08-29) test
ucusunu IKILI yapiyor: 100 ya da 0.

── YAPILACAK ───────────────────────────────────────────────────────────────
1) Ankor, rotanin AIT OLDUGU SERIDIN cizim tablosundan gelsin.
   GUI zaten seritleri ciziyor (`_mxy` ve serit geometrisi mevcut). Yayinlanan
   `road` numarasi hangi seride karsilik geliyorsa, ankor O SERIDIN giris
   noktasi olsun. `ref_xy` YEREL bir ofsettir; waypoint'ler ona EKLENIR.
2) `or [25.0, 2.0]` KALDIRILSIN. Yedek deger, kusuru gizleyen seydi.
   `ref_xy` YOKSA (None) rota CIZILMEZ ve ekrana "ANKOR YOK" yazilir —
   fail-closed. Yanlis yerde cizmek, hic cizmemekten KOTUDUR.
3) 🔴 EKRANDA "SEMATIK" UYARISI DURACAK.
   Cizilen sey gercek dunya koordinati DEGILDIR; serit tablosundan turetilmis
   bir GOSTERIMDIR. Uyarisiz duzeltmek, GORUNUR bir celiskiyi GORUNMEZ bir
   yalana cevirir — hakem "dogru yerde" sanip onaylar.
   Metin ornegi: "SEMATIK GOSTERIM — serit tablosundan turetildi, GPS degil"
   Uyari metni `width=` ile sarmalanmali (tasma olmasin).
4) Suresi/limiti ekranda sabit yazili metin VARSA sozlesme sabitinden turet
   (ornek: YKS_TESPIT_TAZELIK_S). Sabit yazili sayi bayatlar.

── NOBETCI TEST (ZORUNLU) ──────────────────────────────────────────────────
Yeni dosya: tests/test_a1_hakem_ekrani_ankoru.py

  a) YAPI: `or [25.0, 2.0]` (ya da benzeri truthy-yedek) KODDA YOK.
     Denetimi AST ile yap, METIN ARAMASIYLA DEGIL — docstring'de gecen bir
     ad "kullanim" sanilir (D-354/D-361'de tam bu hata yapildi).
  b) DAVRANIS: `ref_xy=[0,0]` ve bilinen bir `road` ile cizilen rota,
     O SERIDIN sinirlari ICINDE kalmali. Uc serit icin de sina.
  c) FAIL-CLOSED: `ref_xy=None` ise rota CIZILMEZ ve "ANKOR YOK" gorunur.
  d) MUTASYON: ankor tekrar (0,0)'a sabitlenirse test DUSMELI.
     Mutasyonu KOD uzerinde yap, yorum uzerinde DEGIL.
  e) SEMATIK uyarisi ekranda VAR mi.
  f) CAPA: cizim fonksiyonu ayristirilabiliyor mu (yoksa yukaridakiler
     BOSA doner).

Tkinter penceresi ACMADAN sina: GUI'nin cizim mantigini saf fonksiyona
ayirmak GEREKIYORSA ayir, ama DAVRANISI DEGISTIRME.

── KAPILAR (ikisi de ZORUNLU, AYRI kosulur) ───────────────────────────────
  <venv> codes/test_rota_sentetik.py            -> 15/15 GECMELI
  <venv> -m unittest discover -s tests          -> OK olmali
🔴 Suit'i commit/push ile AYNI ZINCIRDE kosma. Once kos, CIKTIYI OKU, sonra
commit. (D-360: kapi kirmiziyken push edildi, bir kez yasandi.)

── YASAKLAR ────────────────────────────────────────────────────────────────
· Uretim yayinini DEGISTIRME. `YAYIN_REF_XY = (0,0)` SOZLESMEDIR (CONTRACTS
  SS6.5); kusur GUI'dedir. Sozlesmeye dokunmak MIMAR KARARIDIR.
· Esik uydurma. Yeni bir sayi gerekiyorsa ONCE oneri olarak yaz, mimar onaylar.
· Kuyruga yeni gorev EKLEME (belge haritasi: kuyrugu mimar yazar). Gerekirse
  ONERI olarak bildir.
· AI atfi YOK. Commit yazari deponun kendi ayarindan gelir; `-c user.email`
  ile EZME (D-356).

── RAPOR (bitirince) ───────────────────────────────────────────────────────
1. Degistirilen dosyalar + satir araliklari
2. Nobetci testin ADI ve kac test oldugu
3. MUTASYON kontrolunun GERCEKTEN dustugunu gosteren cikti
4. Iki kapinin HAM ciktisi (kirpma yok)
5. REVIEW_LOG'a onerdigin kayit METNI (sen YAZMA, oneri olarak ver)
```

---

## CODEX-2 · B3 — YAW/KADRAJ ZARFI ÖLÇÜLMEDİ

```text
GOREV EMRI · Codex-2 · B3 · YAW/KADRAJ ZARFI OLCUMU
Veren: Claude 2 (ustabasi) · 2026-08-29. Once CODEX_WORKERS.md'yi oku.
Master'in SON halinden basla. Dayanak: FDA_PLANI_20260829.md FAZ B.
⚠ comms/yks_gui.py'ye DOKUNMA — Codex-1 orada calisiyor.

── YORUMLAYICI — HER ZAMAN bu tam yol ──────────────────────────────────────
  O:\navitas-local-train\venv\Scripts\python.exe
"python" Windows Store saplamasidir; SESSIZCE hicbir sey yapmaz.

── OLCULMEMIS OLAN ─────────────────────────────────────────────────────────
30 Eylul... duzeltme: 23-25 EYLUL test ucusu TEK SEFERLIKTIR ve duyuruya gore
enkaz alanina girdikten sonraki goruntu isleme hatasi TELAFI SEBEBI DEGILDIR.
Yani dronun YAW'i (yonelimi) ve KADRAJI ilk seferde dogru olmali.

BUGUN BILINMEYEN: sistem hangi yaw acisinda / hangi kadraj kaymasinda rota
uretmeyi BIRAKIYOR ya da YANLIS SERIT yayinliyor? Kimse olcmedi.

⚠ Kabul kumesi (`sentetik_arena_kadraj_t66`) `kip=kadraj` ile uretildi ve
kadraj kaymasini YAPI GEREGI icermiyor — yani mevcut kapilarla bu OLCULEMEZ.

── YAPILACAK ───────────────────────────────────────────────────────────────
Yeni betik: scripts/olcum/162_yaw_kadraj_zarfi.py

1) Kabul kumesinden N kare al (N <= 40; GPU'yu az kullan).
2) Her kareyi kontrollu bicimde BOZ:
     · yaw: -30..+30 derece, 5 derecelik adimlarla dondur
     · kadraj: kare merkezini yatay/dikey %0..%20 kaydir
   Dondurme/kaydirma sonrasi ETIKET DE ayni donusumden gecmeli — yoksa
   "yanlis serit" olcumu anlamsiz olur.
3) Her bozulmus kareyi URETIM CAGRI SIRASINDAN gecir:
     _preprocess -> model.predict(imgsz=INFER_SIZE, conf=0.30)
     -> get_masks(results, ...)  [results LISTESI]
     -> _maskeleri_icerige_kirp -> analyze_path(...)
   ⚠ Bu sira BIREBIR boyle olmali; kisayol alirsan olctugun sey URETIM DEGIL.
4) Her (yaw, kadraj) hucresi icin SAY:
     · rota URETILDI mi
     · yayinlanan SERIT, bozulmamis karedekiyle AYNI mi
5) Cikti: JSON + ekrana tablo. "Kirilma acisi" = rota uretiminin ya da
   serit dogrulugunun ilk kez %90'in altina dustugu aci.

── ON KAYIT — OLCUMDEN ONCE YAZILACAK ──────────────────────────────────────
🔴 Sayilari GORMEDEN once `results/yaw_zarfi/ON_KAYIT.md` dosyasina sunu yaz:
  · "kabul edilebilir zarf" olcutu NEDIR (ornek: rota uretimi >= %90 VE
    serit dogrulugu >= %95)
  · bu olcut hangi (yaw, kadraj) araliginda saglanmali
Sonuclari gorup olcut degistirmek YASAKTIR (D-107). Olcut tutmazsa bu bir
BULGUDUR, esik gevsetme gerekcesi DEGILDIR.

── NOBETCI TEST (ZORUNLU) ──────────────────────────────────────────────────
Yeni dosya: tests/test_b3_yaw_zarfi.py
  a) Betik ayristirilabiliyor ve URETIM cagri sirasini kullaniyor (AST ile
     `analyze_path` ve `_maskeleri_icerige_kirp` cagrilari DOGRULANSIN).
  b) Etiketin de donusumden gectigi sinaniyor (aksi halde "yanlis serit"
     sayisi anlamsizdir) — sentetik bir maske ile davranissal sina.
  c) MUTASYON: donusum etikete UYGULANMAZSA test DUSMELI.
  d) CAPA: N=0 ise betik SESSIZCE "gecti" DEMEZ, OLCULEMEDI der.

── CIKTI — SAHA KONTROL LISTESI ────────────────────────────────────────────
Olcum bitince JETSON_KILAVUZ.md'ye eklenecek metni ONERI olarak yaz (sen
EKLEME, Codex-1 kilavuza dokunuyor olabilir):
  "Dronu su yaw araliginda konumlandirin: ... · kadraj kaymasi en fazla ..."
Sayilar OLCUMDEN gelecek, tahminden degil.

── KAPILAR (ikisi de ZORUNLU, AYRI kosulur) ───────────────────────────────
  <venv> codes/test_rota_sentetik.py            -> 15/15
  <venv> -m unittest discover -s tests          -> OK
🔴 Suit'i commit/push ile AYNI ZINCIRDE kosma (D-360).

── YASAKLAR ────────────────────────────────────────────────────────────────
· comms/yks_gui.py'ye DOKUNMA (Codex-1'de).
· Model EGITME. GPU'yu 40 kareden fazlasi icin mesgul etme.
· Uretim kodunu (codes/) DEGISTIRME — bu is bir OLCUMDUR.
· Esik uydurma; on kayit kurali yukarida.
· AI atfi YOK; commit yazarini `-c` ile EZME.

── RAPOR ───────────────────────────────────────────────────────────────────
1. ON KAYIT dosyasinin TAM metni (olcumden once yazildigi gorulsun)
2. Olcum tablosu (yaw x kadraj) — HAM
3. Kirilma acisi ve kadraj siniri
4. Nobetci test adi + mutasyonun dustugu cikti
5. Iki kapinin HAM ciktisi
6. Saha kontrol listesi ONERISI
```

---

## SIRADAKİ (A1 bitince Codex-1'e verilecek)

### A2 — TESPİT YAŞI (`karar_yas`)

⚠ **A1 bitmeden başlamaz** (aynı dosya).

**Ön çalışma — ustabaşı notu, prompt yazılırken kullanılacak:**

Bugün ölçtüm: `comms/` genelinde `karar_yas` **0 kez** geçiyor.
`yks_gui._tespiti_yaslandir()` yaşı `min(rota_yaşı, heartbeat_yaşı)` ile
hesaplıyor.

🔴 **`min()` BİLİNÇLİDİR, körlemesine kaldırılamaz.** T172/D-321'de ölçüldü:
İHA rotayı ACK alana kadar **tekrarlar**, ACK gelince **susar**. Yalnız rota
yaşına bakmak, protokolün **normal** davranışını arıza sayıyordu — demo
kipinde İKA ACK'ledikten 5 sn sonra hakemin onay düğmesi kapanıyordu.

**Gerçek boşluk:** heartbeat **ayrı iş parçacığında** üretiliyor. Algı hattı
asılır ve heartbeat akmaya devam ederse ekran **"CANLI"** der. Yani
*hat canlılığı* ile *algı canlılığı* karıştırılıyor.

**Doğru çözüm:** `min()`'i kaldırmak değil — **kararın kendi yaşını mesajda
taşımak**. İHA, kararı ürettiği anda monotonik saatinden bir yaş/damga
koyar; GUI **karar kutusu** için onu kullanır, heartbeat'i **hat canlılığı**
için kullanmaya devam eder.

⚠ Bu bir **mesaj sözleşmesi değişikliğidir** (CONTRACTS §6 HEARTBEAT/
OPEN_ROUTE). Sözleşmeye dokunmak **mimar kararıdır**; Codex'e verilmeden
önce kullanıcı onayı alınacaktır.
