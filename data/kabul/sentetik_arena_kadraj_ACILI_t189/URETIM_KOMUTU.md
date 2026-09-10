# K5A AÇILI BARİYER NÜFUSU — T189

Bu küme **kabul zincirinin K5A kolunun** yer gerçeğidir.
`config/model_registry.json` → `profiles.competition.kabul_kumesi_acili`

## Neden var

K5'in asıl nüfusu (`sentetik_arena_kadraj_t66`) T184'ten **önce** üretildi;
manifestinde `bariyer_acisi` alanı bile yok ve içindeki **her bariyer
yataydır**. Bu yüzden K5, T184'ün düzelttiği dönme körlüğünü ne
yakalayabilir ne de düzelmeyi doğrulayabilirdi (vakum kapı, TEST_SPECS §4.1).

## Yeniden üretme (birebir)

```
O:\navitas-local-train\venv\Scripts\python.exe scripts/olcum/51_sentetik_arena.py ^
  --adet 260 --kadraj --seed 7 --val-orani 0.1 --ayni-malzeme-orani 0.45 ^
  --dar-orani 0.28 --bariyer-acisi 90 ^
  --banka O:/navitas-local-train/doku_bankasi ^
  --cikti O:/navitas-local-train/calisma/sentetik_arena_kadraj_ACILI_t189
```

Yatay kümeden **tek fark** `--bariyer-acisi 90`'dır. Açı `uniform(-90, +90)`
çekilir; θ ile θ+180 aynı doğrultu olduğundan bu **tüm yönelimleri** kapsar.

## Ayırt ediciliği ölçüldü (ölçümden ÖNCE kayda geçildi: D-334 + D-336)

`scripts/olcum/156_t189_bariyer_aci_kanit.py` · sonuç:
`scripts/olcum/results/t63/t189_ayirt_edicilik.json`

| nüfus | sağlam dedektör | T184 öncesi mutant |
|---|---|---|
| **açılı** | 185/260 (%71,2) | **48/260 (%18,5)** |
| **yatay** (kontrol) | 181/260 (%69,6) | 181/260 (%69,6) |

Açılıda **52,7 puan** düşüş (şart: ≥ 40); yatayda **hiç** düşüş yok — kusurun
tamamen dönmeye özgü olduğunun kanıtı.

⚠ **Yatay küme DEĞİŞTİRİLMEZ**: K1/K7'nin ön kayıtlı sayıları ona bağlıdır.
Bu küme **ikinci bir koldur**, yerine geçmez.
