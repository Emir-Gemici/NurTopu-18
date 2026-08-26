# T49 — Sentetik arena uç-bant tanısı

Bu çıktı karar eşiğini değiştirmez; üretim koduna yazmaz.

## (a) Bant oranı süpürmesi

| oran | bant px | açık | karar dağılımı |
|---:|---:|---:|---|
| 0.02 | 12 | 2 | {"ACIK_1": 1, "ACIK_2": 1, "UC_BANT_TEMAS_YOK": 22} |
| 0.03 | 19 | 2 | {"ACIK_1": 1, "ACIK_2": 1, "UC_BANT_TEMAS_YOK": 22} |
| 0.04 | 25 | 2 | {"ACIK_1": 1, "ACIK_3": 1, "UC_BANT_TEMAS_YOK": 22} |
| 0.05 | 32 | 3 | {"ACIK_1": 2, "ACIK_3": 1, "UC_BANT_TEMAS_YOK": 21} |
| 0.06 | 38 | 3 | {"ACIK_1": 2, "ACIK_3": 1, "UC_BANT_TEMAS_YOK": 21} |
| 0.07 | 44 | 3 | {"ACIK_1": 2, "ACIK_3": 1, "UC_BANT_TEMAS_YOK": 21} |
| 0.08 | 51 | 3 | {"ACIK_1": 2, "ACIK_3": 1, "UC_BANT_TEMAS_YOK": 21} |
| 0.09 | 57 | 3 | {"ACIK_1": 2, "ACIK_3": 1, "UC_BANT_TEMAS_YOK": 21} |
| 0.10 | 64 | 4 | {"ACIK_1": 2, "ACIK_2": 1, "ACIK_3": 1, "UC_BANT_TEMAS_YOK": 20} |
| 0.11 | 70 | 5 | {"ACIK_1": 2, "ACIK_2": 2, "ACIK_3": 1, "UC_BANT_TEMAS_YOK": 19} |
| 0.12 | 76 | 5 | {"ACIK_1": 2, "ACIK_2": 2, "ACIK_3": 1, "UC_BANT_TEMAS_YOK": 19} |
| 0.13 | 83 | 7 | {"ACIK_1": 3, "ACIK_2": 3, "ACIK_3": 1, "UC_BANT_TEMAS_YOK": 17} |
| 0.14 | 89 | 8 | {"ACIK_1": 3, "ACIK_2": 4, "ACIK_3": 1, "UC_BANT_TEMAS_YOK": 16} |
| 0.15 | 96 | 8 | {"ACIK_1": 4, "ACIK_2": 3, "ACIK_3": 1, "UC_BANT_TEMAS_YOK": 16} |
| 0.16 | 102 | 11 | {"ACIK_1": 4, "ACIK_2": 5, "ACIK_3": 2, "UC_BANT_TEMAS_YOK": 13} |
| 0.17 | 108 | 11 | {"ACIK_1": 3, "ACIK_2": 6, "ACIK_3": 2, "UC_BANT_TEMAS_YOK": 13} |
| 0.18 | 115 | 12 | {"ACIK_1": 5, "ACIK_2": 5, "ACIK_3": 2, "UC_BANT_TEMAS_YOK": 12} |
| 0.19 | 121 | 12 | {"ACIK_1": 4, "ACIK_2": 6, "ACIK_3": 2, "UC_BANT_TEMAS_YOK": 12} |
| 0.20 | 128 | 12 | {"ACIK_1": 4, "ACIK_2": 5, "ACIK_3": 3, "UC_BANT_TEMAS_YOK": 12} |

**Net:** ETKILI AMA TEK NEDEN DEGIL: %8'de 3/24 acik, %20'de 12/24 acik; 12 kare taranan ust sinirda da acilmadi.

## (b) Yer gerçeği geometrisi

- Üretici replay fiziksel şerit dağılımı: `{2: 5, 3: 13, 4: 2, 5: 4}`; JPEG provenance `24/24`
- Class-0 poligon dağılımı: `{1: 15, 2: 5, 3: 1, 4: 2, 5: 1}`
- Class-0 bağlı bileşen dağılımı: `{1: 20, 2: 3, 3: 1}`
- GT karar, %8: `{'ACIK_1': 1, 'ACIK_3': 1, 'UC_BANT_TEMAS_YOK': 22}`
- GT karar, %20: `{'ACIK_1': 4, 'ACIK_2': 5, 'ACIK_3': 3, 'UC_BANT_TEMAS_YOK': 12}`
- GT boşluk: `{'ust_medyan_px': 101.0, 'ust_maks_px': 328, 'ust_bant_disinda_kare': 20, 'alt_medyan_px': 74.5, 'alt_maks_px': 159, 'alt_bant_disinda_kare': 16}`
- **Net:** DOGRU: dogrulanmis uretici replay'inde fiziksel serit sayisi {2: 5, 3: 13, 4: 2, 5: 4}; yalniz 13/24 kare tam 3 seritli. GT class-0 poligon sayisi yalniz 1/24, birlesik maske bilesen sayisi yalniz 1/24 karede tam 3. %8 tam-goruntu bantlarina ayni GT bileseniyle iki uctan temas eden kare 2/24. n_ser degeri salt YOLO etiketlerinden birebir geri kazanilamaz; etiket-only sonuc DOGRULANAMADI, fakat kaynak replay'iyle dogrulandi.

## (c) Parçalanma

- Bileşen sayısı dağılımı: `{1: 20, 2: 3, 6: 1}`
- UC ret atıfları: `{'ALT_BANTTA_YETERSIZ_ZEMIN': 2, 'IKI_BANTTA_YETERSIZ_ZEMIN': 14, 'UST_BANTTA_YETERSIZ_ZEMIN': 5}`
- Bant zemin piksel toplamı (tüm/en büyük): üst `24954/24954`, alt `31008/30740`
- **Net:** ANA NEDEN DEGIL: %8 UC_BANT retlerinin 0/21 tanesi bagli-bilesen ayrismasina atfedildi; kalan 21/21 ret, tum model maskesinde bile bir veya iki uc bandinda yeterli zemin olmamasindan geldi.

## Görsel kanıt

- `results\t49_sentetik_arena_tani_20260811\gorseller\a1_bant_duyarli_sa_000297.png`
- `results\t49_sentetik_arena_tani_20260811\gorseller\a2_bant_yetersiz_sa_000301.png`
- `results\t49_sentetik_arena_tani_20260811\gorseller\b1_gt_iki_serit_sa_000300.png`
- `results\t49_sentetik_arena_tani_20260811\gorseller\b2_gt_cok_koridor_sa_000306.png`
- `results\t49_sentetik_arena_tani_20260811\gorseller\c1_bilesen_sa_000306.png`
- `results\t49_sentetik_arena_tani_20260811\gorseller\c2_bilesen_sa_000310.png`

## Sınır

Bu tanı model/karar zincirini ayrıştırır. Eşik düzeltmesi yapmaz. Üretecin gerçek `n_ser` değeri YOLO etiketlerinde saklanmadığı için salt etiketten birebir geri kazanımı **DOĞRULANAMADI**. Ayrı kaynak replay'i ilk 24 JPEG'i 24/24 bayt-eşit üretip şerit sayılarını doğruladı.
