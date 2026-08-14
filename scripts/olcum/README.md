# `scripts/olcum/` — ölçüm ve araştırma araçları

Bu klasör **üretim kodu değildir.** `REVIEW_LOG.md`'deki sayıları üreten
araçların yedeğidir.

## Neden burada duruyorlar

Bu betikler `O:\navitas-local-train` altında yazıldı ve orada koşuyorlar.
**O dizin bir git deposu değil** — 2026-08-15'te fark edildi. Yani
`REVIEW_LOG.md`'nin D-104'ten D-129'a kadarki bütün ölçümlerinin arkasındaki
araçlar tek bir diskte duruyordu. Disk giderse kayıtlardaki sayılar
**yeniden üretilemez** hâle gelirdi; kayıt kalır, kanıt gitmiş olurdu.

Buradaki kopyalar o riski kaldırır. **Asıl koşum yeri hâlâ
`O:\navitas-local-train`'dir**; oradaki `ayarlar.py`, `calisma/` ve
`results/` bu depoya taşınmaz.

## Araçlar

| dosya | ne ölçer | kayıt |
|---|---|---|
| `56_t53_gercek_karisim.py` | eğitim koşucusu (ön-eğitim + karışım fine-tune) | D-109, D-112 |
| `60_kadraj_karar_dogrulugu.py` | şerit tabanlı karar doğruluğu (**terk edildi** — tanıma bağımlı) | D-90 |
| `61_rota_moloza_basma.py` | **projenin standart ölçütü**: rota × yer gerçeği molozu | D-90, D-104 |
| `62_haritalama_gorseli.py` | 4 panelli harita: özgün / segmentasyon / C-uzayı / rota | — |
| `63_bariyer_kesisimi.py` | modelden bağımsız bariyer dedektörü (LAB a\*>25) | D-92, D-100 |
| `64_surum_kiyasi.py` | çok modelli kıyas koşucusu | — |
| `65_kabul_denetcisi.py` | **D-107 kabul ölçütlerini mekanik koşar** (K0..K5) | D-115, D-119 |
| `66_k5_bariyer_populasyon.py` | K5'i gövde yarıçapıyla, 172 karede | D-115 |
| `67_onnx_karar_denkligi.py` | `.pt` ↔ `.onnx` **karar** denkliği (maske değil) | D-119 |
| `68_karar_kararliligi.py` | algılayıcı gürültüsü altında koridor seçimi kararlılığı | D-122 |
| `69_arac_referans_olcegi.py` | araçtan metre/piksel (telemetrisiz ölçek kâhini) | D-124, D-126 |
| `70_gercek_kare_rota_denemesi.py` | gerçek karelerde rota: ölçek verilirse ne oluyor | D-124 |
| `71_gercek_kare_etiketleyici.py` | gerçek karelerin yarı otomatik etiketlenmesi | D-127, D-128 |

## Koşum

Yorumlayıcı **her zaman** `O:\navitas-local-train\venv\Scripts\python.exe`
(`python` Windows Store saplamasıdır, sessizce hiçbir şey yapmaz).

Uzun eğitimler `FOR_DISABLE_CONSOLE_CTRL_HANDLER=1` olmadan başlatılmaz —
konsol kapanınca eğitim izsiz ölür.

## Kural

Bu araçlar **karar vermez, ölçer.** Eşikler `codes/karar_sozlesmesi.py`'den
okunur; buradaki hiçbir betik üretim eşiğini değiştirmez.
