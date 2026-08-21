# CODEX GÖREV PROMPTLARI · 2026-08-21 · Veren: Claude 2 (ustabaşı)

> Her bloğu ilgili Codex ajanına **AYNEN** yapıştır. İki görev **farklı
> dosyalara** dokunur; kilit çakışması yok.
> 🔴 **PUSH KİLİDİ AÇIK (kullanıcı emri, 2026-08-21):** yeni bir emre kadar
> **hiçbir ajan push yapmaz.** Commit de izinsiz atılmaz (madde 17).
> ⚠ Yeni kuyruk görevi **AÇILMADI**: kuyruğa görev eklemek mimarın işidir
> (belge haritası). İki iş de mevcut defter borçlarını kapatır ve kuyruk
> satırı gerekiyorsa mimara **öneri** olarak gider.

---

## CODEX-1 · D-226 SINIF TARAMASI — hangi betik GÜRÜLTÜLÜ düşüyor, hangisi SESSİZ

```text
GOREV EMRI · Codex-1 · D-226 SINIF TARAMASI (olcum borcu: D-256 §7)
Veren: Claude 2 (ustabasi) · 2026-08-21. Once CODEX_WORKERS.md'yi oku.
Master'in SON halinden basla. Zimmet: kuyrukta ACIK BIR SATIR YOK — bu is bir
DEFTER BORCUDUR (D-256 §7'de "OLCULMEDI" diye yazili). Kayit D-256'ya atifla.

── KUSUR SINIFI (D-226) ────────────────────────────────────────────────────
Bazi olcum betikleri veri kumesi yolunu KENDI KONUMLARINDAN turetiyor:
    BURASI = Path(__file__).parent
    KADRAJ = BURASI / "calisma" / "sentetik_arena_kadraj_t66"
Bu betikler `O:\navitas-local-train` altinda kosarken calisir; ama depodaki
AYNA kopyada (`scripts/olcum/`) o dizin YOKTUR.

UC KEZ ISIRDI:
  T125 -> 65_kabul_denetcisi.py  : bos kume uzerinden K1..K4'u "DUSTU"
          raporladi; mimar az kalsin "model her kapida dustu" hukmu veriyordu.
  T126 -> 66_k5_bariyer_populasyon.py
  T130 -> 68_karar_kararliligi.py : FileNotFoundError ile coktu.
KANONIK ONARIM (65'te): yol registry'den okunur
(`profiles[default_profile].kabul_kumesi`), dizin yoksa RuntimeError —
FAIL-CLOSED. Ciplak yedek yol YOK (madde 16).

── OLCULMEMIS OLAN (senin isin) ────────────────────────────────────────────
`scripts/olcum/*.py` icinde kalibi tasiyan 23 dosya var. UCU ZATEN ONARILDI
(65, 66, 68 — onlarda eslesme yalnizca kusuru ANLATAN yorumdur). Geriye ~20
dosya kaliyor ve sunu KIMSE OLCMEDI:

    GURULTULU mu duser (patlar -> GUVENLI, insan hemen gorur)
    yoksa SESSIZ mi   (bos kume uzerinde rapor URETIR -> TEHLIKELI, sayi
                       uydurur ve dogru gibi durur)

Bu ayrim onarim SIRASINI belirler. Sessiz dusenler once onarilmalidir.

KANIT ZATEN ORTADA: `scripts/olcum/results/t63/` altinda **36 dosya** var —
bunlar ayna dizininde kosulan betiklerin URETTIGI cop. Yani kalip yalnizca
teorik degil, fiilen calisti.

── YAP ─────────────────────────────────────────────────────────────────────
1. DEFTER ARAMASI ONCE (kural D-252): REVIEW_LOG.md + TASK_QUEUE.md icinde
   "D-226", "kendi konumundan", "BURASI" ara. Daha once olculduyse OLCME —
   "arandi, bulunamadi" cumlesini raporuna YAZ (bu da bir kayittir).
2. ON KAYIT yaz (olcumden ONCE): `results/d226_tarama/on_kayit.md`.
   Icinde: hangi dosyalar, siniflandirma kurali, "sonuca gore kural
   gevsetilmez" cumlesi.
3. Kalibi tasiyan dosyalari MEKANIK bul (elle liste TUTMA — elle liste bu
   projede DORT kez bayatladi). Onarilmislari (registry'den okuyanlari) da
   MEKANIK ayir.
4. Her dosya icin STATIK siniflandir ve KANIT olarak dosya:satir ver:
     GURULTULU : yol yoksa `raise` / `SystemExit` / acik hata var
     SESSIZ    : `glob`/`rglob`/`iterdir` bos liste dondurur ve betik
                 DEVAM EDER (ortalama, oran, JSON yazar)
     BELIRSIZ  : kod yolundan cikarilamiyor
   ⚠ "BELIRSIZ" yazmak SERBESTTIR ve tercih edilir; TAHMIN YAZMA.
5. GUVENLI DINAMIK PROBE — yalnizca sunlari kosabilirsin: `--yardim/-h`
   destekleyen ya da olmayan bir dizin verilince ANINDA donen betikler.
   🔴 KOSMA YASAGI: `42_cok_sinifli_onegitim.py`, `78_gurultu_dayanikli_
   egitim.py` ve adinda "egitim" gecen HICBIR betigi calistirma (GPU/saatler).
   Emin degilsen KOSMA, STATIK kal.
6. Ciktilar:
     `results/d226_tarama/tarama.json`  (makine)
     `results/d226_tarama/tarama.md`    (insan: dosya · sinif · kanit satiri)
   ve `REVIEW_LOG.md`'ye TEK kayit (bos ilk D-numarasini al; carpisirsa
   KENDI kaydini tasi, baskasininkine DOKUNMA).

── YAPMAYACAKLARIN ─────────────────────────────────────────────────────────
- 🔴 HICBIR BETIGI ONARMA. Bu tur bir OLCUM turudur. 20 dosyayi degistirmek
  ayri bir karardir ve onarim SIRASI bu olcumden cikacaktir.
- `codes/` altina DOKUNMA. `config/model_registry.json`'a DOKUNMA.
- Esik DEGISTIRME (sende olmayan yetki, AGENTS.md §9.2).
- `scripts/olcum/results/t63/` altindaki 36 dosyayi SILME — onlar KANIT
  (ayrica madde 18: kullanicinin dosyalari silinmez).
- Kuyruga YENI GOREV EKLEME (mimarin isi). Gerekli goruyorsan ONER.
- COMMIT/PUSH YOK. Calisma agacini birak, ustabasi denetler.

── KAPI ────────────────────────────────────────────────────────────────────
  O:\navitas-local-train\venv\Scripts\python.exe codes/test_rota_sentetik.py
      -> 15/15
  ... -m unittest discover -s tests -q  -> Ran 765 · OK
Raporunda GERCEK cikti yapistir. Kapi dusuyorsa DUSTU yaz — "muhtemelen
gecer" YAZMA.

── RAPOR BICIMI ────────────────────────────────────────────────────────────
1) Defter aramasi sonucu (bulundu/bulunamadi)
2) Mekanik olarak bulunan dosya sayisi + onarilmis olanlar
3) Tablo: dosya · SINIF · kanit (dosya:satir)
4) SESSIZ sinifindakiler icin ONARIM SIRASI onerisi (gerekcesiyle)
5) Kapi ciktisi (ham)
6) 🔴 SININ: neyi OLCEMEDIN? ("hepsini olctum" cumlesi ancak GERCEKTEN
   hepsini olctuysan yazilir.)
```

---

## CODEX-2 · T132 ÇAPRAZ DENETİMİ — D-264'ün her sayısı ham artefaktla tutuyor mu

```text
GOREV EMRI · Codex-2 · T132 CAPRAZ DENETIMI (kayit: REVIEW_LOG D-264)
Veren: Claude 2 (ustabasi) · 2026-08-21. Once CODEX_WORKERS.md'yi oku.
Master'in SON halinden basla (commit f1c5931).

── NEDEN SEN ──────────────────────────────────────────────────────────────
T132'yi BEN yazdim; mimar da benimle AYNI MODEL. Iki tarafin ANLASMASI bu
projede KANIT SAYILMAZ (CLAUDE.md §19, korelasyonlu kor nokta). Bagimsiz
arac + farkli model = gercek denetim. Ayni isi T130'da yaptin ve BENIM
sayilarimi dogruladin (D-259); ayrica benim desen kusurumu duzelttin.

── DENETLENECEK IDDIALAR (D-264) ──────────────────────────────────────────
Her birini HAM ARTEFAKTTAN dogrula. "Kayitta yaziyor" KANIT DEGILDIR.

 1. BICIM GENISLEDI, DEGER DEGISMEDI.
    Iddia: `config/model_registry.json` icinde YALNIZ
    `metrics.k0_korluk.figur_zemin_orani` skalerden listeye dondu; ayrica
    `_figur_zemin_orani_bicimi` ve `kabul_kumesi_parmak_izi` EKLENDI.
    BUNUN DISINDA HICBIR METRIK DEGERI DEGISMEDI.
    -> Commit ONCESI ve SONRASI defterleri `git show` ile al, SEMANTIK
       kiyasla (JSON agaci; bicimlendirme farki sayilmaz). Degisen alanlarin
       TAM listesini cikar. Beklenenden FAZLA alan degistiyse BULGU yaz.
 2. KILITLI DEGERLER: listede `v34 = 0.0049` ve `v35 = 0.0903`.
    -> Commit ONCESI skalerin degeri ile v35 kaydinin degeri AYNI olmali.
       Farkliysa emrin "metrik degerlerini degistirme" kisiti IHLAL edilmis
       demektir.
 3. SOYAGACI DEGERLERI ile olcum dosyasi TUTUYOR.
    -> `results/t131/k0_taban_gecmisi.json` icindeki 8 olcumu, defterdeki 8
       kayitla kiyasla (4 basamaga yuvarlanmis olmali). Tutmayan varsa yaz.
 4. DONEM ISARETI DOGRU.
    -> `donem_tutarli: true` YALNIZ v27/v30/v34/v35'te olmali; v17/v20/v21/
       v24'te `false` ve her birinde `uyari` metni olmali.
 5. IKI DEFTER BAYT-ES.
    -> `config/model_registry.json` ile `jetson_paket/config/model_registry.json`
       sha256'lari ESIT mi? (Bu bir kapi tarafindan da korunuyor; sen AYRICA
       olc.)
 6. KARSI-OLGUSAL 16,0x.
    -> Defterdeki gecmisten v35'i CIKAR, kalan DONEM-TUTARLI kayitlarin
       MEDYANINI kendi kodunla hesapla, v34'un 0.0049'una BOL. D-264 "16,0x"
       diyor. Kendi sayini yaz; tutmuyorsa BULGU.
 7. ESIK DEGISMEDI.
    -> `K0_ORAN_ALT`/`K0_ORAN_UST` commit oncesi/sonrasi 0.5 / 2.0 mi?
       `git diff` ile GOSTER.
 8. KABUL SAYILARI BIREBIR AYNI.
    -> D-264 "K1 256/260 · K2 18/256 · K3 0/256 · K4 1/256 · K5 0/173"
       diyor ve bunlarin D-256/D-255'teki kosumla ayni oldugunu iddia ediyor.
       Defterde D-255 ve D-256 kayitlarini bul, sayilari KARSILASTIR.

── YONTEM ──────────────────────────────────────────────────────────────────
- Tek bir betik yaz: `scripts/onarim/t132_capraz_denetim.py`
  (T130'daki `t130_capraz_denetim.py` kalibini izle: her kontrol AYRI
  fonksiyon, GECTI/DUSTU/OLCULEMEDI dondurur, KURU KOSUM varsayilan).
- 🔴 `OLCULEMEDI != DUSTU`. Bir seyi olcemiyorsan (ornegin agirlik dosyasi
  `.gitignore`'da) bunu ACIKCA yaz; "dogrulandi" deme.
- Her kontrol icin SENTETIK MUTASYON yaz ve kontrolun DUSTUGUNU goster.
  Hic dusmeyen kontrol, hic kosmayan kontrol kadar sahtedir (T120 dersi).
  🔴 MUTASYONLARI GERCEK DOSYALARDA YAPMA — gecici kopyalarda yap.

── YAPMAYACAKLARIN ─────────────────────────────────────────────────────────
- Bulgu bulursan DUZELTME — RAPORLA. Duzeltme karari ustabasinin/mimarin.
- `config/`, `codes/`, `scripts/olcum/65_*` DEGISTIRME (okuma serbest).
- Esik DEGISTIRME. Kuyruga gorev EKLEME.
- COMMIT/PUSH YOK.

── KAPI ────────────────────────────────────────────────────────────────────
  codes/test_rota_sentetik.py -> 15/15
  unittest discover -s tests -q -> Ran 765 · OK

── RAPOR BICIMI ────────────────────────────────────────────────────────────
1) 8 kontrolun her biri: GECTI / DUSTU / OLCULEMEDI + SEBEP
2) Mutasyon tablosu: hangi mutasyon hangi kontrolu dusurdu
3) POZITIF KONTROL: gercek dosyalarla hepsi GECTI mi
4) Bulgular (varsa) — kanitiyla, DUZELTMEDEN
5) 🔴 SININ: neyi olcemedin
⚠ Basligin ile sayilarinin CELISMEDIGINDEN emin ol. T115'te tek kusurun
buydu; son iki turda tekrarlamadin.
```
