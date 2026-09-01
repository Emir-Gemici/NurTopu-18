# CODEX GÖREV PROMPTLARI · 2026-09-01 · Veren: Claude 2 (ustabaşı)

> Bu dosya `CODEX_PROMPTLARI_20260831.md`'nin **yerine geçer** — o turun
> teslimi çalışma ağacına hiç ulaşmadı ve içindeki betik numarası (163)
> bu arada dolduruldu. Aşağıdaki iki prompt **kendi başına yeterlidir**;
> Codex'e olduğu gibi yapıştırılır.
>
> 🔴 **TESLİM PROTOKOLÜ DEĞİŞTİ (her iki görev için bağlayıcı):**
> **COMMIT YOK · PUSH YOK.** Denetimi ve commit'i ustabaşı yapar.
> Teslim = **tek yama dosyası + rapor**, aşağıda tarif edildiği gibi.

---

## CODEX-1 · A2 — TESPİT YAŞI (`karar_yas`) · SÖZLEŞME DEĞİŞİKLİĞİ ONAYLI

```text
GOREV EMRI · Codex-1 · A2 · TESPIT YASI (karar_yas)
Veren: Claude 2 (ustabasi) · 2026-09-01. Once CODEX_WORKERS.md'yi oku.
Master'in SON halinden basla (0c97bb8 ya da sonrasi).

── TESLIM PROTOKOLU — ONCE BUNU OKU ────────────────────────────────────────
GECEN TURUN TESLIMI HIC ULASMADI; bu yuzden teslim artik SU SEKILDEDIR:
  1. COMMIT YAPMA, PUSH YAPMA. Degisiklikler calisma agacinda kalir.
  2. Isin sonunda TEK yama uret:
       git diff > results/codex_teslim/A2_20260901.patch
     (yeni dosyalar icin once `git add -N <dosya>` yap ki diff'e girsinler)
  3. Raporunu results/codex_teslim/A2_RAPOR.md dosyasina YAZ (icerigi en
     altta). Bulut kopyada calisiyorsan kullaniciya geri tasinacak seyler
     YALNIZ bu iki dosyadir — baska hicbir seye gerek kalmamali.
  4. O:\navitas'a dogrudan yazabiliyorsan yama YINE uretilir (denetim
     yamadan okunur), degisiklikler agacta birakilir.

── YORUMLAYICI — HER ZAMAN bu tam yol ──────────────────────────────────────
  O:\navitas-local-train\venv\Scripts\python.exe
"python" Windows Store saplamasidir; SESSIZCE hicbir sey yapmaz.

── NEDEN — ve onem 31 Agustos'tan beri ARTTI ───────────────────────────────
TEKNOFEST duyurusu: test ucusu IKILIDIR (100/0) ve sartlardan biri "GERCEK
ZAMANLI aktarilan guzergah tespitinin hakem heyetince ONAYLANMASI".
Sartname SS6.4: veri akisi saglanamazsa ucus GECERSIZ.

🔴 YENI OLCUM (D-374, 2026-09-01): gercek ucus goruntusunde model, sahne
bagintili 45-51 SANIYELIK araliklarda HIC karar uretemiyor; FPS ve
cozunurluk bunu COZMUYOR (D-377). O aralikta hakem ekranindaki tek dogru
bilgi "algi en son NE ZAMAN karar uretti"dir — tasiyacak alan `karar_yas`.
Kullanicinin onayina sunulan K1 karari (bayatlayinca kutu bosalmasin, son
tespit YAS DAMGASIYLA gorunsun) BU ALANA bagli. Sen alani ve bayatlik
davranisini kur; K1'in gorunum kismi AYRI istir, ona GIRME.

── KUSUR — USTABASI OLCTU, TAHMIN DEGIL ────────────────────────────────────
comms/yks_gui.py:988   ->  self.rota_zaman = time.time()      # ALIM zamani
comms/yks_gui.py:2499  ->  yaslar.append(simdi - self.rota_zaman)
comms/yks_gui.py:~2503 ->  _hb = son_hb["iha"]; yaslar.append(simdi - _hb)
                           yas = min(yaslar)
(Satir numaralari 8c34884'te olculdu; kaymis olabilir — DESENLE bul.)

🔴 `min()` BILINCLIDIR, KORLEMESINE KALDIRMA. T172/D-321: IHA rotayi ACK
alana kadar tekrarlar, ACK gelince SUSAR. Yalniz rota yasina bakmak
protokolun NORMAL davranisini ariza sayiyordu. `min()`i kaldirirsan D-321'i
GERI GETIRIRSIN.

GERCEK BOSLUK: heartbeat AYRI IS PARCACIGINDA uretilir (CONTRACTS:862,
IHA_HEARTBEAT_ARALIK_S = 1.0). Algi hatti ASILIRSA heartbeat AKMAYA DEVAM
EDER ve ekran "CANLI" der. HAT canliligi ile ALGI canliligi karisiyor;
hakem bir saat once uretilmis tespiti "gercek zamanli" sanip ONAYLAYABILIR.

── COZUM (ustabasi tasarimi — bunu uygula) ─────────────────────────────────
Karar yasi OPEN_ROUTE'a DEGIL, HEARTBEAT'e konur (ACK'ten sonra da akan
tek kanal o).

1) comms/protocol.py
   HEARTBEAT_TELEMETRI_ALANLARI demetine "karar_yas" EKLE. Fail-closed
   kalip AYNEN: alan None ise YAZILMAZ (sifir DEGIL); sozlesme disi alan
   ValueError.

2) IHA tarafi (codes/rpi_inference.py — kamera/karar dongusu)
   Her KARAR uretiminde MONOTONIK damga tut. KARAR = analyze_path'in
   dondugu an; rota CIKSA DA CIKMASA DA (NO_ROUTE de karardir) damga
   tazelenir. Heartbeat gonderilirken:
       karar_yas = time.monotonic() - son_karar_damgasi
   ⚠ `time.time()` DEGIL. ⚠ HIC karar uretilmediyse alan GONDERILMEZ.

3) comms/yks_gui.py
   KARAR KUTUSU tazeligi artik `karar_yas`a bakar:
     · karar_yas VARSA ve > YKS_TESPIT_TAZELIK_S -> karar BAYAT, onay
       dugmesi KAPANIR (mevcut bayatlik davranisi AYNEN kullanilir)
     · karar_yas VARSA ve <= esik -> mevcut davranis BIREBIR korunur
     · karar_yas YOKSA -> "TESPIT YASI BILINMIYOR" yazilir, TAZE SAYILMAZ.
       🔴 EKSIK ALAN "TAZE" DEGILDIR. Bu D-321'i geri getirmez: yeni IHA
       alani HER heartbeat'te yollar; yokluk eski/bozuk yayinci demektir.
   HAT canliligi icin heartbeat kullanimi DEGISMEZ.

4) CONTRACTS.md SS6 — HEARTBEAT satirina alan ve anlami:
   "IHA'nin son ALGI KARARININ yasi (sn, monotonik). Alan YOKSA yas
    BILINMIYOR demektir; TAZE sayilmaz."

── NOBETCI TEST (ZORUNLU) — tests/test_a2_karar_yasi.py ────────────────────
  a) SOZLESME: alan var; None ise yazilmiyor; sozlesme disi alan ValueError.
  b) MONOTONIK: uretici time.monotonic() kullaniyor — AST ILE, metin
     aramasiyla DEGIL (D-354/D-361: docstring'deki ad "kullanim" sanildi).
  c) DAVRANIS — ASIL KAPI: heartbeat AKARKEN karar_yas esigi asarsa kutu
     BAYAT olmali, onay dugmesi KAPANMALI (bugun yakalanamayan senaryo).
  d) GERILEME KORUMASI (D-321): karar_yas TAZEyken IHA ACK sonrasi
     OPEN_ROUTE'u kesse bile onay dugmesi ACIK KALMALI. Bunu yazmadan isi
     bitmis SAYMA.
  e) EKSIK ALAN: yoksa "BILINMIYOR" gorunur, TAZE sayilmaz.
  f) MUTASYON: karar_yas denetimi kaldirilinca (c) DUSMELI. Mutasyon KOD
     uzerinde; UYGULANDIGINI ayrica dogrula — desen bulunamayan mutasyon
     "gecti" SAYILMAZ (D-370, D-375: iki kez basimiza geldi).
  g) CAPA: tazelik islevi Tk penceresi acmadan cagrilabiliyor.

── KAPILAR (AYRI kosulur, cikti OKUNUR) ────────────────────────────────────
  <venv> codes/test_rota_sentetik.py            -> 15/15
  <venv> -m unittest discover -s tests          -> OK (su an 1413 test)
🔴 Kapi kirmiziysa teslim ETME; dususu raporla.

── YASAKLAR ────────────────────────────────────────────────────────────────
· COMMIT/PUSH YOK (teslim protokolu).
· min(yaslar) mantigini korlemesine kaldirma (D-321).
· Esik uydurma: YKS_TESPIT_TAZELIK_S = 5.0 mevcut ve gerekceli. Yeni sayi
  gerekiyorsa ONERI yaz, mimar karar verir.
· Eksik alani 0 ile doldurma.
· K1'in gorunum degisikligine (bayat kutuda son tespiti gosterme) GIRME —
  o ayri onay bekliyor.
· Kuyruga gorev ekleme; oneri olarak bildir.

── RAPOR (results/codex_teslim/A2_RAPOR.md) ────────────────────────────────
1. Degistirilen dosyalar + satir araliklari
2. Nobetci test adi ve test sayisi
3. (c) ve (d) testlerinin HAM ciktisi — ikisi BIRLIKTE
4. Mutasyonun GERCEKTEN uygulanip DUSTUGUNU gosteren cikti
5. Iki kapinin HAM ciktisi
6. CONTRACTS SS6 satirinin YENI hali
7. REVIEW_LOG kayit ONERISI (sen yazma)
8. Yamanin yolu ve `git diff --stat` ozeti
```

---

## CODEX-2 · B2 — 10 DAKİKALIK BÜTÇENİN UÇTAN UCA ÖLÇÜMÜ (T15)

```text
GOREV EMRI · Codex-2 · B2 · FDA 10 DAKIKA BUTCESI UCTAN UCA
Veren: Claude 2 (ustabasi) · 2026-09-01. Once CODEX_WORKERS.md'yi oku.
Master'in SON halinden basla (0c97bb8 ya da sonrasi).
⚠ comms/yks_gui.py ve comms/protocol.py'ye DOKUNMA — Codex-1 orada.

── TESLIM PROTOKOLU — ONCE BUNU OKU ────────────────────────────────────────
COMMIT YOK, PUSH YOK. Isin sonunda:
  git diff > results/codex_teslim/B2_20260901.patch
  (yeni dosyalar icin once `git add -N <dosya>`)
Rapor: results/codex_teslim/B2_RAPOR.md. Bulutta calisiyorsan geri
tasinacak seyler YALNIZ bu iki dosya + olcum JSON'laridir.

── YORUMLAYICI ─────────────────────────────────────────────────────────────
  O:\navitas-local-train\venv\Scripts\python.exe

── NEDEN ───────────────────────────────────────────────────────────────────
TEKNOFEST duyurusu: "Tum gorev sureci MAKSIMUM 10 DAKIKA." Ucus IKILI:
asilirsa 0. Kod butceyi biliyor (karar_sozlesmesi, T170/D-318) ama uctan
uca OLCUM yapilmadi (T15 ACIK).

── YAPILACAK ───────────────────────────────────────────────────────────────
🔴 BETIK NUMARASI DEGISTI: yeni betik scripts/olcum/169_fda_butce_olcumu.py
   (163-168 bu hafta DOLDU — 163 yazarsan p olcumunun ustune yazarsin!)

Gorev zincirinin HER adimini SURE olarak olc, toplami butceyle kiyasla:
  1. model yukleme (soguk baslangic dahil)
  2. kare yakalama -> _preprocess
  3. cikarim (model.predict)
  4. get_masks + _maskeleri_icerige_kirp
  5. analyze_path
  6. _rota_kararini_esikle
  7. telsiz yayini (loopback; gercek telsiz yoksa ACIKCA yaz)
  8. hakem onayi icin gereken EN AZ sure (insan; SABIT varsayim + kaynak)

⚠ URETIM CAGRI SIRASI BIREBIR (D-351). Referans zincir icin
scripts/olcum/163_b4_p_ve_kosu.py'nin _cikarim/_karar islevlerine BAK —
ayni uretim halkalarini kullaniyor (rota_olcek_reddi + analyze_path +
_rota_kararini_esikle DAHIL; mpp'siz olcersen her kare NO_ROUTE olur ve
olctugun sey uretim degildir — D-374 EK-1'deki tuzak).

⚠ GPU KISITI: bu makinede GPU isleri SIRALI kosulur (BSOD gecmisi).
Olcumunu KISA tut (tek model yuklemesi + birkaç yuz kare), egitim yok,
uzun mesguliyet yok.

── ON KAYIT — OLCUMDEN ONCE ────────────────────────────────────────────────
results/fda_butce/ON_KAYIT.md — SAYILARI GORMEDEN yaz:
  · n (kac kare) · raporlanacak yuzdelikler (p50/p95)
  · "kabul edilebilir": toplam <= ? sn ve MARJ; gerekcesiyle
  · hangi adimlar OLCULEMEDI sayilacak
Sonuc gorup olcut degistirmek YASAK (D-107).
⚠ MARJ UYDURMA: gerekcesini yazamiyorsan ONERI olarak birak, mimar seçer.

── NOBETCI TEST — tests/test_b2_fda_butcesi.py ─────────────────────────────
  a) Betik URETIM cagri sirasini kullaniyor (AST ile).
  b) Butce sabiti karar_sozlesmesi'nden geliyor, betikte CIPLAK degil
     (madde 16).
  c) OLCULEMEDI adimlar toplama 0 olarak GIRMIYOR — ayri raporlaniyor
     (OLCULEMEDI != GECTI).
  d) MUTASYON: bir adim toplamdan dusurulurse test DUSMELI; mutasyonun
     UYGULANDIGINI ayrica dogrula (D-370/D-375).

── KAPILAR ─────────────────────────────────────────────────────────────────
  <venv> codes/test_rota_sentetik.py   -> 15/15
  <venv> -m unittest discover -s tests -> OK (su an 1413 test)
Kirmiziysa teslim etme; dususu raporla.

── YASAKLAR ────────────────────────────────────────────────────────────────
· COMMIT/PUSH YOK. comms/* dosyalarina DOKUNMA.
· scripts/olcum/163..168 ve results/{b4_fps,hb_sekil,fdr,t100}/ dizinlerine
  YAZMA — bu haftanin kapali olcumleri.
· Model egitme; uretim kodunu degistirme — bu is bir OLCUMDUR.
· Gercek telsiz yoksa "olculdu" DEME; OLCULEMEDI yaz.

── RAPOR (results/codex_teslim/B2_RAPOR.md) ────────────────────────────────
1. ON KAYIT dosyasinin TAM metni
2. Adim adim sure tablosu (p50/p95) — HAM
3. Toplam ve MARJ
4. OLCULEMEDI kalan adimlar ve NEDEN
5. Nobetci test adi + mutasyon ciktisi
6. Iki kapinin HAM ciktisi
7. Yamanin yolu ve `git diff --stat` ozeti
```
