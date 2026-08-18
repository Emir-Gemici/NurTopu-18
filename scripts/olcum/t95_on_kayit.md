# T95 — `rota_bul` (KATMAN B) ACIKLIK KORUMASI · ON KAYIT
# Yazan: Claude 1 (mimar) · 2026-08-18 · OLCUMLER KOSULMADAN once yazildi (D-107)
# Kanit: REVIEW_LOG D-158 (bagimsiz denetim bulgusu 2) · gorev T95

## SORU

T94 `yol_duzelt`e ACIKLIK KORUMA kurali ekledi ve yalniz `rpi_inference`
(KATMAN A / `analyze_path`) yolunda devreye aldi. `rota_bul` ayni fonksiyonu
`dt_px` GECIRMEDEN cagiriyor (`codes/costmap_path_finder.py:1116`), oysa
`sonuc["dt_px"]` bir satir once kapsamda. D-154'te olculen kusur (string-pulling
emniyet payini yiyor, medyan 4,00 px) bu yolda HALA CANLI.

`rota_bul` -> `simulation/scripts/iha_haritala.py:329` -> `road`.

## NEDEN KORLEMESINE EKLENMIYOR

Bu oturumda bes kez ayni sey oldu: makul gorunen bir degisiklik OLCULDUGUNDE
dustu (D-152 LAMBDA, D-153 izgara, D-156 sabit esik...). Ayrica bu yolun
`rpi_inference`tan IKI YAPISAL FARKI var ve ikisi de kuralin davranisini
degistirebilir:

  1. `rota_bul` `yol_duzelt`i VARSAYILAN `aci_esigi_derece=15.0` ile cagirir;
     `rpi_inference` `0.0` kullanir. Denetim bulgusu 1 tam da bu daldi
     (asama 2 korumayi siliyordu). Duzeltildi, ama BU YOLDA HIC OLCULMEDI.
  2. `rota_bul` `gecilebilir_tam` olarak C-UZAYINI (`dt_px >= r_gerekli_px`)
     verir; `rpi_inference` `koridor > 0` verir. Kural C-uzayinda daha az
     serbestlik gorur.

## OLCUM SOZLESMESI

- Kume: `calisma/sentetik_arena_kadraj_t66` (n=260), TEMIZ kare (cekilis yok).
- Model kare basina YALNIZ BIR KEZ kosar; ayni `mk` maskeleri hem taban hem
  koruma kosumuna gider (D-139 dersi). Iki ayri cikarim YASAK.
- Taban ve koruma AYNI KOSUMDA olculur. Mutlak sayi degil, TABANLA kiyas.
- Kayip tanimi: `_polyline_asgari_aciklik(yol_px, dt_px)` (yol_duzelt GIRDISI)
  eksi `_polyline_asgari_aciklik(sonuc, dt_px)` (yol_duzelt CIKTISI), tam
  cozunurlukte, uretimin `cv2.distanceTransform(..., DIST_L2, 5)` alaninda.

  ⚠ GOREV METNIMDEKI "maximin karsilastirmasi" DUZELTILDI. Maximin, A*'in
  KENDI alt-optimalligini de icerir (T74'un sorusu) ve bu degisiklik onu
  duzeltemez. T95'in olcecegi sey SON ISLEM kaybidir; maximin KAPSAM DISI.

## KABUL — HEPSI BIRDEN TUTMALI (sonuc gorulmeden yazildi)

    olcut                              esik
    (1) rota_bul durum == ACIK         >= ayni kosumdaki TABAN
    (2) kayip medyani                  taban - koruma >= 1,00 px
    (3) pay < 3 px olan ACIK kare      <= ayni kosumdaki TABAN
    (4) `duzelt` suresi medyani        <= 2 kat taban
    (5) waypoint medyani               <= 16
    (6) codes/test_rota_sentetik.py    15/15
    (7) unittest discover -s tests     >= 584 OK, HIC dusme yok

⚠ (1) neden MUTLAK SAYI DEGIL: TASK_QUEUE'ya once "ACIK >= 34/260" yazmistim;
34, T90 ONCESI bir sayidir ve T90'in fail-closed etiket korumasi onu OLCULEREK
31'e indirdi (D-146). Yani kapi, uretimin KENDISININ saglamadigi bir esik
istiyordu — D-157'de yakalanan hatanin BIREBIR aynisi. Duzeltildi.

⚠ (2)'deki 1,00 px keyfi degil: waypointler tam sayi piksele yuvarlanir
(`int(round(...))`), yani 1 px bu yolun KUANTUM adimidir. Medyan kazanci
1 px'in altinda kalirsa kazanc, rasterin yuvarlamasindan AYIRT EDILEMEZ ve
degisiklik yalniz karmasiklik ekler.

## RED KURALI

- (1), (3), (4), (5), (6) veya (7) duserse: degisiklik URETIME YAZILMAZ,
  gorev `[ ]` kalir, sonuc REVIEW_LOG'a yazilir. "Neredeyse" kabul edilmez.
- (2) duserse (kazanc yok veya kuantum altinda): degisiklik URETIME YAZILMAZ;
  kusur "canli ama olculen etkisi yok" olarak kaydedilir. Bu bir BASARISIZLIK
  DEGIL, gecerli bir olcum sonucudur.
- Olcut sonuca gore GEVSETILMEZ. Gevsetmek gerekiyorsa gerekce olcutun KENDI
  AMACINDAN gelmeli ve ACIKCA kayda gecmeli (D-157 usulu).

────────────────────────────────────────────────────────────────────────────
## SONRADAN EKLENDI — OLCUT (5) GECERSIZ ILAN EDILDI (2026-08-18, D-160)

Bu blok olcum KOSULDUKTAN SONRA yazildi ve bilerek AYRI tutuldu; yukaridaki
on kayit metnine DOKUNULMADI (D-107).

(5) "waypoint medyani <= 16" GECERSIZDIR. 16 KATMAN A'nin sayisidir; KATMAN
B'nin tabani 31'dir, yani olcut uretimin KENDISININ saglamadigi bir esik
istiyordu — D-146 ve D-157'de yakalanan kusurun UCUNCU tekrari. Kokeni:
`rpi_inference.py:847` `wp_aralik_px = max(shape)*2` (bolme yok) vs
`costmap_path_finder.py:1116` `olc["wp_aralik_px"]` (boler).

    (5') waypoint medyani <= taban + 2      (taban 31 -> 33; olculen 32)

Amacindan turetildi ("dugum patlamasi olmasin"); sert sinir MAKS_WP = 64.
AYIRT EDICI OLGU: koruma 64'e dayansaydi REDDEDILIRDI.

⚠ SONUC DEGISMEZ: (4) dusuyor, T95 yine REDDEDILIR. (5') bu turda hicbir
kararı cevirmiyor — bu yuzden gevsetme degil, DUZELTME sayilir.

(4) GEVSETILMEDI. Gerekcesi D-160 §3.

⚠ ON KAYITTAKI BELIRSIZLIK: (4)'e "duzelt suresi medyani" yazildi ama ALAN ADI
verilmedi. `sure_ms["duzelt"]` penceresi `yol_duzelt`ten fazlasini sarar
(:1096-1108). Bundan sonra on kayit bir alan adi veriyorsa TAM YOLUYLA verir.
