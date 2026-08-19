# FILO 1 · LANE 12/15 — PAYDA TARAMASI (T118 payda sozlesmesi)
# Kosum: statik kod incelemesi (dosya okuma), 2026-08-20. Hicbir model/olcum KOSULMADI;
# tum tespitler kod ve yorum satirlarindan. On kayit okundu, degistirilmedi.
# Grup 12 (0-indeksli): codes/karar_sozlesmesi.py · scripts/olcum/79_k5_koken.py ·
# scripts/olcum/40_surum_degerlendirme.py · scripts/olcum/47_arena_yer_gercegi.py

| dosya:satir | PAYDA NE | ESIGE/KAPIYA karsi mi | Esik hangi paydada kalibre | Uyum |
|---|---|---|---|---|
| codes/karar_sozlesmesi.py:426 | `zemin_kaplamasi(trav, icerik)` — ICERIK kutusu (icerik=None ise ham maske boyutu; uretim cagrisi icerikli) | Evet: donen deger 577'de ZEMIN_KAPLAMA_TAVANI=0.67'ye karsi (tanim: ayni dosya:423) | ICERIK kutusu: T48 blogu (satir 355: "kaplama := ... ICERIK kutusundaki piksel orani", uretim zinciri `_maskeleri_icerige_kirp`) ve T59 yeniden kalibrasyonu (satir 371-396, D-84/D-85/D-86, v24 uretim zinciri conf=0.30) | UYUMLU |
| codes/karar_sozlesmesi.py:556 | Yorum satiri: `kaplama > ZEMIN_KAPLAMA_TAVANI` kural ilani — payda 577'deki cagriyla ayni (ICERIK kutusu) | Evet, ayni kapi (zemin_maskesi_reddi docstring) | ICERIK kutusu (T59, D-84/D-85) | UYUMLU |
| codes/karar_sozlesmesi.py:577 | `oran = zemin_kaplamasi(trav, icerik)` — ICERIK kutusu; 568'de `icerik_kutusu_gecerli_mi` fail-closed, gecersiz kutuda red (payda kaymasi onlenmis) | Evet: 578'de 0.67 tavani, 581'de ZEMIN_KENAR_DAYANMA_TAVANI=0.50 (tanim: 480, T52/D-69/D-71) | Kaplama tavani: ICERIK paydasinda (T59 tablosu, satir 383-396). Kenar tavani: ICERIK kutusu CEVRE pikselleri paydasi (satir 465-479, 320 mesru + 67 cokmus, D-69/D-71) | UYUMLU |
| scripts/olcum/79_k5_koken.py:82 | Kaplama-degil: `duyarlilik = blok[ust].mean()` — payda BARIYER piksel kumesi (klasik dedektor maskesi), tani metrigi; esik yok | Hayir (K5 esigi kesisim_px=0 px sinir olcutu, oran degil) | — | KAPLAMA-DEGIL |
| scripts/olcum/79_k5_koken.py:102 | Kaplama-degil: kesisim pikselleri koordinat ortalamasi (merkez noktasi), oran bile degil | Hayir | — | KAPLAMA-DEGIL |
| scripts/olcum/79_k5_koken.py:181 | Kaplama-degil: `blocked_kapsama` — payda YEREL dilimdeki bariyer pikselleri; H2 tani metrigi, esiksiz | Hayir | — | KAPLAMA-DEGIL |
| scripts/olcum/40_surum_degerlendirme.py:55 | Yorum/karne metni: "kaplama %4,2" — kaynak 48_arena_iou.py `p.mean()` = HAM GORUNTU paydasi (icerik kirpma yok) | Hayir: yer gercegi %3,6 ile kiyas notu, hicbir tavana karsi kullanilmiyor | — (esik yok; ama okur %4,2'yi 0.67 ICERIK tavaniyla kiyaslarsa payda farkli olur — kodda boyle kiyas YOK) | UYUMLU (esiksiz) |
| scripts/olcum/40_surum_degerlendirme.py:152 | Ayni sayinin ozet metnindeki tekrari (HAM GORUNTU paydasi, 48_arena_iou kaynakli) | Hayir | — | UYUMLU (esiksiz) |
| scripts/olcum/47_arena_yer_gercegi.py:107 | `mz.mean()` — HAM GORUNTU paydasi (yer gercegi moloz maskesi, tum kare); yalnizca overlay etiketi | Hayir (gorsel dogrulama ciktisi) | — | UYUMLU (esiksiz) |
| scripts/olcum/47_arena_yer_gercegi.py:123 | Kaplama-degil: print metnindeki "kaplamali" kelimesi, insan talimati; sayi yok | Hayir | — | KAPLAMA-DEGIL |

## Notlar
- Bu lane'de tek gercek kapi kullanimi karar_sozlesmesi.py:577-581'dir; hem kaplama (0.67)
  hem kenar (0.50) tavani ICERIK-kutusu paydasinda kalibre edilmis (T59 blogu satir 371-396,
  D-84/D-85/D-86 atiflari; T52 blogu satir 465-479, D-69/D-71) ve olcum de ayni paydada
  yapiliyor. [UYUSMAZLIK] YOK.
- karar_sozlesmesi.py:433-434: `icerik=None` verilirse payda TUM maske olur (letterbox
  kirpilmamis ham maske). Uretim (`analyze_path`/`rpi_inference`) icerikli cagiriyor; ama
  icerik=None ile cagiran bir tuketici 0.67'yi FARKLI paydada kullanmis olur. Bu lane'in
  dosyalarinda boyle cagri gorulmedi; diger lane'lerin bulgusudur.
- 40_surum_degerlendirme.py'deki %4,2 (48_arena_iou kaynakli, HAM GORUNTU paydasi) ile
  0.67 tavani (ICERIK paydasi) AYNI cumlede kiyaslanmiyor — kodda uyusmazlik dogmuyor,
  yalnizca okur icin karisiklik riski (BILGILENDIRICI).
