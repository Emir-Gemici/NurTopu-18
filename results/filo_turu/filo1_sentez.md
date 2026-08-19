# FILO 1 · T118 PAYDA TARAMASI — SENTEZ (15 lane)
# Kosum: 15 statik kod-inceleme lane'i, 2026-08-20. HICBIR lane model/olcum kosmadi.
# Sentezleyen: FILO1 sentez ajani, 2026-08-20. On kayit: results/filo_turu/on_kayit.md (uygulandi, degistirilmedi).
# NOT: Lane 7 ve Lane 8 AYNI grubu taradi (54_arena_cozunurluk.py + 67_onnx_karar_denkligi.py) — capraz dogrulama olarak kullanildi, sayimlarda TEK sayildi. Bulgulari birbiriyle tutarli.

## 1. PAYDA DAGILIMI (tablo satiri bazinda; lane 8 dublikasyonu dusuldu)

| Payda kategorisi | Satir sayisi | Nerede yogun |
|---|---|---|
| ICERIK kutusu | 21 | karar_sozlesmesi.py (426/556/577), rpi_inference.py (1233/1237), 57, 58, 62, 70, 72, v21 |
| LETTERBOX karesi (dolgu paydada) | 17 | 93_t106 (8), 65_kabul_denetcisi (4), 67_onnx (3), 62:89, saha_kuru_kosu:549 |
| HAM goruntu (tam kare) | 20 | 48_arena_iou (9), 54_arena_cozunurluk (4), 71 (4), 40/47 (3) |
| maske-toplami / rota-alani (diger oran) | 9 | 48 (moloz GT x3), 54:142, 61_rota (kalin rota x5) |
| kaplama-degil (uretim parametresi, geometri, fotometri, sayac, docstring) | ~104 | 51_sentetik_arena (26/26), test_rota_guvenlik+59 (17/17), costmap, 79, 63, 66, 69, 74, 80 vd. |
| TOPLAM (dedup) | ~171 | (lane oz-bildirimlerinde gruplu satirlar nedeniyle ±2 belirsizlik; lane 7 "12 aday" ilan edip 10 satir listeledi) |

## 2. ESIGE KARSI KULLANILAN DEGERLER ve ESIGIN KALIBRE PAYDASI

| Kullanim yeri | Esik | Deger paydasi | Esik kalibre paydasi | Hukum |
|---|---|---|---|---|
| codes/karar_sozlesmesi.py:577-578 | ZEMIN_KAPLAMA_TAVANI=0.67 (:423) | ICERIK (zemin_kaplamasi :426-443) | ICERIK — T59, D-84/D-85/D-86, v24 conf=0.30 (:371-423) | UYUMLU |
| codes/karar_sozlesmesi.py:581 | ZEMIN_KENAR_DAYANMA_TAVANI=0.50 (:480) | ICERIK cevre pikselleri | ICERIK — T52, D-69/D-71 | UYUMLU |
| codes/rpi_inference.py:1233 | min_area_ratio=0.01 (:1081) | ICERIK alani | ICERIK — K-07 duzeltmesiyle (letterbox hali REGRESYON ilan edilmisti); 0.01'in ampirik kokeni BELIRSIZ | UYUMLU (koken izi eksik) |
| codes/rpi_inference.py:1453/1463 | DARK_L_MEAN=80.0 | HAM goruntu LAB L (kaplama degil, parlaklik) | HAM — bilincli (dolgu oncesi cagri, yorumla belgeli); 80.0 kokeni BELIRSIZ | UYUMLU |
| scripts/olcum/62_haritalama_gorseli.py:62-64 | 0.67 (zemin_maskesi_reddi uzerinden) | ICERIK | ICERIK (T59) | UYUMLU |
| scripts/v21_degerlendir_ve_paketle.py:70/89 | ASGARI_ZEMIN_ORANI=0.05 (K-8) | ICERIK | Ayni zincir, D-18/D-20 — ICERIK; K-8 SOZLESME METNI payda konusunda SESSIZ | UYUMLU (metin eksik) |
| scripts/olcum/61_rota_moloza_basma.py:128-130 | 0.0 / 0.05 / 0.10 | kalin rota alani (ozgun kare) | Ayni betik/payda (D-90, T68/K3); 0.05-0.10 ilk secim gerekcesi BELIRSIZ | UYUMLU |
| codes/test_rota_guvenlik.py:406-552 | 0.10 test gucu, ==0.0 gecme | kare sayimi (kaplama degil) | Ayni paydada; 0.10 D-atifsiz BELIRSIZ | UYUMLU |
| scripts/olcum/59_t60_uretec_sadakati.py:171/177 | DOKU_KORUMA_ORANI=0.75 + LAB bantlari | doku ornegi maske pikselleri | Ayni yordam; 0.75 dis kalibrasyon izi BELIRSIZ | UYUMLU |
| scripts/olcum/93_t106_guven_bandi.py:245/183/224 | BAND_ORANI>=3, 1e-9 esitlik, 0.01 sayaci | LETTERBOX (oran/esitlikte payda sadelesir) | Betik-ici; 0.01 rapor sayaci kalibrasyonsuz (kapi degil) | UYUMLU (ic-kapali) |
| scripts/olcum/65_kabul_denetcisi.py:49-50 | K0_ORAN_ALT/UST = 0.5/2.0 | LETTERBOX/LETTERBOX orani (pay-taban ayni) | Olcumle turetilmedi (emirle verilmis, T110 kaydi); BLOKLAMAZ | UYUMLU (kalibrasyonsuz ama payda-ici) |
| scripts/olcum/57_t51_kadraj_kapilari.py:135-137, 70_...:129-131 | 0.67 (yalniz RAPOR kiyasi) | ICERIK | ICERIK (T59); 57'de kaynak farki GT-vs-model KASITLI (KAPI 5 tanisi); 70:131'de "%67" ciplak yazi sabiti (madde 16 uslup riski) | UYUMLU |

## 3. [UYUSMAZLIK] LISTESI

DOGRULANMIS [UYUSMAZLIK]: 0 / 15 lane. Hicbir lane, bir kaplama degerinin FARKLI paydada kalibre edilmis bir esige karsi KOD ICINDE kullanildigini bulamadi.

GIZLI RISKLER (uyusmazlik DEGIL; oncelik sirali, asagi-akis okuyucu/rapor duzleminde dogabilir):
1. scripts/olcum/48_arena_iou.py:149,163,183 — JSON alani "kaplama" HAM-goruntu paydasinda, uretimin ICERIK-paydali zemin_kaplamasi ile AYNI AD; 40_surum_degerlendirme.py:55,152 karnesine "%4,2" olarak zaten aktarilmis (lane 2 + lane 12).
2. scripts/olcum/65_kabul_denetcisi.py:126-134 — kaplama() LETTERBOX paydasinda (ICERIK degerinin ~0,56-0,60 kati); bastigi "figur zemin %X" 0,67 ile kiyaslanirsa hata ORADA dogar (lane 3).
3. scripts/olcum/54_arena_cozunurluk.py:143 — ayni "kaplama" ad cakismasi, HAM payda (lane 7+8, bagimsiz iki lane ayni bulgu).
4. scripts/olcum/93_t106_guven_bandi.py:97 — mutlak yuzdeler LETTERBOX paydasinda (16:9'da ICERIK degerinin ~0,5625 kati); baska raporda 0,67 ile yan yana konursa uyusmazlik dogar (lane 1).
5. scripts/olcum/67_onnx_karar_denkligi.py:113 — kaplama farki LETTERBOX paydasinda; ICERIK-payda degerleriyle mutlak kiyaslanamaz (lane 7+8).
6. scripts/saha_kuru_kosu.py:543-549 — "piksel_orani" LETTERBOX paydasinda rapora yazilir (lane 14).
7. scripts/olcum/71_gercek_kare_etiketleyici.py:328 — print'teki "~0,81" degerinin kosum kaynagi BELIRSIZ (lane 11).
8. codes/karar_sozlesmesi.py:426 — zemin_kaplamasi icerik=None cagrilirsa payda tum maske olur; bu lane'lerde boyle cagri GORULMEDI, savunma notu (lane 12).
9. ARCHITECT_PLAN K-8 metni — "kare alaninin %5'i" paydayi acikca tanimlamiyor; "K-8 paydasi = ICERIK" satiri onerilir, karar mimarin (lane 13).
10. Kadro notu: Lane 7 ve 8 ayni grubu taradi — grup listesi dagitiminda dublikasyon; sonuc acisindan zararsiz (iki lane tutarli), ama bir grup taranmamis olabilir (dagitim listesi bu sentezde gorulmedi — OLCULEMEDI).

## 4. ON KAYIT IDDIASI DURUMU
On kayit karar kurali (67 raw_frames, v34, uretim zinciri, >=%80 red) HICBIR lane tarafindan KOSULMADI — bu sentezde OLCULEMEDI. Yazili emsal kanit (lane 9): scripts/olcum/70_gercek_kare_rota_denemesi.py:106-109 yorumu ayni kareyi tuval paydasinda %45,3, ICERIK paydasinda %78 olarak OLCUMLE belgeliyor — mimarin "denetci ~%45'i tuval paydasinda okudu" hipoteziyle yon olarak ortusur; nicel hukum icin on-kayit olcumu ayrica kosulmali.
