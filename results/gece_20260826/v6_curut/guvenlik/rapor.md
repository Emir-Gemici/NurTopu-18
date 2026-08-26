# LENS 3 — GÜVENLİK / SAHA · v6 (gece_v6_v35taban) çürütme raporu

Varsayım: aday terfi ETMEMELİ. Betik: `curut_guvenlik.py` (bu klasör), ham çıktı `olcum.json`, `curut_stdout.txt`, bindirmeler `bindirme/`, kontak sayfaları `kontak_v6_rota.jpg`, `kontak_v6_supheli4.jpg`, `etiket_v1_v2_205_196.jpg`.
Koşum: `O:\navitas-local-train\venv\Scripts\python.exe results\gece_20260826\v6_curut\guvenlik\curut_guvenlik.py` (GPU çıkarım, conf 0,30, imgsz 512, 126/65 ile aynı yol).
Yeniden üretim: v6 test29 ROTA 12 · MASKE_YOK 8 · ZEMIN_MASKESI_SUPHELI 1, v35 ROTA 6; otopark67 kaplama medyanı v6 0,4667 / v35 0,5076 — kayıtlı sayılarla BİREBİR.

## HÜKÜM: ÇÜRÜTÜLDÜ — kapı (b) FP ≤ 1, ON_KAYIT §10'un YASAKLADIĞI bir referans değişikliğiyle geçiyor

### K1 (TERFİ ENGELİ) — frame_000205'in FP→TP dönüşü mera'nın sınıf 0 yapılmasıyla oldu
- v1 tavanla (ilk ölçüm, `gece_v6_v35taban_olcum.json`): FP **2** (000205, 000218) → `b_gecti false`.
- v2 tavanla (`gece_v6_ref2_olcum.json`): FP **1** (000218) → `b_gecti true`. Tek fark 000205.
- Etiket alanı (kare oranı, sınıf 0): 000205 v1 **0,107** → v2 **0,313** (×2,9). `etiket_v1_v2_205_196.jpg` üst satır: v2'de eklenen bölge yolun ÜSTÜNDEKİ ÇİM/MERA şerididir (asfalt değil). ON_KAYIT §10: *"Yasak: çiğ toprak/mera/tarlayı sınıf 0 yapmak."*
- v6'nın 000205 rotası: çizgi piksellerinin yalnız **%31,7**'si etiket sınıf 0 üstünde, **%66,6**'sı etiketsiz; 8 waypoint'ten 3'ü etiket-0 üstünde (`olcum.json test29.v6`). Bindirmede rota çim tarladan başlayıp yolu ÇAPRAZ kesip yine çime iniyor (`kontak_v6_supheli4.jpg` sağ üst).
- Sonuç: §10'a uygun referansla v6 FP = 2 > 1 → **(b) DÜŞER**, terfi adayı değildir.

### K2 (TERFİ ENGELİ) — v6'nın "TP" saydığı rotaların bir kısmı YOL ÜSTÜNDE DEĞİL (göz + etiket kesişimi)
12 rota karesi, tek satır hüküm (rota çizgisi ∩ etiket-0 oranı / waypoint etiket-0):
| kare | hüküm |
|---|---|
| 000062 | yol üstünde (1,00 · 8/8) |
| 000111 | yol üstünde (1,00 · 8/8) |
| 000120 | yol üstünde (1,00 · 8/8) |
| 000135 | yol üstünde (1,00 · 8/8) |
| 000139 | yol üstünde (1,00 · 8/8) |
| 000143 | ŞÜPHELİ — maske yolu ve yanındaki çimenlik alanı birleştiriyor, rota çim üstünden ve taş yığınının yanından geçiyor (0,62 · 6/8) |
| 000152 | yol üstünde (1,00 · 8/8) |
| 000160 | büyük ölçüde yol (0,75 · 6/8), uç kısım çime taşıyor |
| 000196 | **YOL ÜSTÜNDE DEĞİL** — asfalt yol sol köşede, rota çim/çıplak toprak tarladan dikey geçiyor (0,21 · 2/8) |
| 000205 | **YOL ÜSTÜNDE DEĞİL** — rota çim tarladan başlayıp yolu çapraz kesiyor (0,32 · 3/8); FP→TP dönüşü K1 |
| 000215 | yol üstünde (1,00 · 8/8) |
| 000218 | **YANLIŞ POZİTİF** — yol solda, rota yola paralel çim/toprak tarladan (0,49 · 4/8) |
- 000196'nın "TP" olması da referansa bağlıdır: v1 ve v2'de mera sınıf 0, asfalt yol ise **sınıf 1** (kırmızı) etiketlenmiş (`etiket_v1_v2_205_196.jpg` alt satır). Bu referansla "yol üstünde" hükmü verilemez; şartname yorumuna göre (yanlış güzergâh = 0 puan) 196 ve 205 saha güvenliği açısından yanlış güzergâhtır.
- Sayısal özet: 12 rotanın 3'ü (196, 205, 218) rota çizgisinin ≥ %51'i etiketsiz (çim/toprak); 2'si daha (143, 160) %25–38 etiketsiz.

### K3 — frame_000116: v6 karenin %97,7'sini ZEMİN sayıyor, bunun %60,6'sı etiketli ENGEL
- v35 aynı karede MASKE_YOK (0,0). v6: kaplama 0,977 · kenar 0,630 → yalnız `ZEMIN_MASKESI_SUPHELI` kapısı kurtarıyor (`kontak_v6_rota.jpg` 1. satır 3. kare: tüm çim tarla yeşil).
- Bu yeni bir hata kipi: v35 "görmez", v6 "her şeyi zemin görür". Kapı (b) MASKE_YOK ≤ 10'u bu kare **düşürerek** yardımcı oluyor (MASKE_YOK yerine SUPHELI sayılıyor). Kapı kaldırılsa/eşik gevşetilse rota doğar. Terfi engeli değil, ama saha riski olarak yazılır.

### K4 — T142 eşiği (0,55/0,40), v6 dağılımı (soru 4)
| küme | v6 kap_box maks | v6 ken_box maks | ret_AND | v35 kap maks | v35 ken maks |
|---|---|---|---|---|---|
| sentetik 260 | 0,6299 | 0,3615 | **0** | 0,6442 | 0,5004 |
| otopark 67 | 0,5996 | **0,4312** | **0** | 0,6626 | 0,3999 |
- 0 ret: bekleneni sağlıyor. Ama otopark `11_44_39/frame_000017`: kaplama **0,5259**, kenar **0,4312** — kenar tavanı AŞILMIŞ, kaplama tavana 0,024 uzak; `frame_000018` 0,5008/0,3695. v35'te kenar 0,40'ı aşan gerçek kare 0'dı; v6'da 1. Eşik v6 için ayırt edici ama pay daralmış: kaplamada 0,024'lük kayma ile gerçek otopark karesi reddedilir. (Sentetikte kenar 0,35–0,40 arası 1 kare.)

### K5 — Arena figürü (soru 3)
- v6: kaplama içerik **0,0815** (tuval 0,0488), engel 0,2769, yol **YOK** (`UC_BANT_TEMAS_YOK`: alt 16 px / üst 176 px, gereken 22). v35: 0,1508 / yol yok (üst 0 px). v6 orta koridoru v35'ten daha az görüyor; figürde ikisi de rota üretmiyor (bilgi, kapı değil).

### K6 — Soru 1: v6 v35'ten belirgin kötü mü? (t122/kiyas.json + k109)
| eksen | v35 (t127_temiz) | v6 | dji_kirsal_v1 |
|---|---|---|---|
| çatı kaçağı ort | 0,0428 | 0,0391 | 0,0158 |
| disk çatı→zemin | 0,0035 | 0,0000 | 0,0 |
| disk zemin→zemin | 0,9227 | **0,9416** | 0,9081 |
| kaplama67 TUVAL medyan | 0,2855 | **0,2625** | 0,2154 |
| kaplama67 içerik medyan | 0,5076 | 0,4667 | 0,3829 |
| figür zemin | 0,1508 | **0,0815** | 0,3900 |
| 67'de red | 0 | 0 | 0 |
- Çatı ve disk eksenlerinde belirgin KÖTÜ DEĞİL (çatı daha iyi, disk zemin daha iyi). Kaplama %8 düşük, figür zemin yarıya inmiş: gerçek/otopark sahnede "daha az zemin" yönü; D-240 bağımsız tahmini %47–52 → v6 0,467 hâlâ bandın içinde. Bu eksende terfi engeli yok.

### K7 — Jetson paketi / registry (soru 5, kod okuyarak)
`competition.path`/`sha256` v6'ya çevrilirse KIRILAN testler:
1. `tests/test_model_registry.py::test_default_is_verified_v35_competition_model` — `path.name == "navitas_seg_v35_best.pt"`, `model_id == "navitas-seg-v35-512"` sabit.
2. `tests/test_t143_turev_ve_kamera.py` — `URETIM_SHA = e00f6b8e…`, `ENGINE_ADI`, türev adı kümesi (satır 40–41, 97–116); `test_competition_path_ve_pt_sha_DEGISMEDI`, `test_turevler_…_hepsi_kaynaga_BAGLI` (her türevin `kaynak_sha256` == üretim sha), `test_diskteki_onnx_turevi_GERCEKTEN_GECER` (v35 .onnx sha ile), `test_paket_aynasi_BAYT_ES`.
3. `tests/test_jetson_paket_defteri.py::test_paket_defteri_depo_defteriyle_BIREBIR_AYNI` — `jetson_paket/config/model_registry.json` sha ≠ depo → `scripts/jetson_paket_hazirla.py` yeniden koşulmalı.
4. `tests/test_saha_parametrik.py::KayitDefteriDurumuTests` — `test_manifest_ile_kayit_defteri_ESLESIYOR` (`model_kayit_dogrula`), `test_UC_UC_ayni_agirligi_gosteriyor` (defter ad = manifest ad = `yks_gui.YksArayuz.ALGI_MODEL_DOSYA`) → manifest ve hakem ekranı da çevrilmeli.
5. `tests/test_hakem_kunye_algi_hizasi.py::test_gercek_defterde_kunye_sha_defterle_UYUSUYOR` — `hakem_log.MODEL_SHA8 == sha256[:8]`.
6. `tests/test_gercek_arena_kapisi.py` — `ARENA_KAPLAMA = 0.1508 / ARENA_KENAR = 0.0` v35'e çivili; v6 0,0815 ile `test_OLCULEN_degerler_SABITLERLE_tutarli` DÜŞER (bilinçli "bayat sabit" kapısı, satır 75–78).
7. `tests/test_t132_taban_gorunurlugu.py` — `metrics.k0_korluk.figur_zemin_orani` listesine v6 kaydı eklenmeli; `65_kabul_denetcisi` tabanı `model_id`'ye göre okur.
8. `tests/test_kilavuz_gecis_yordami.py` / `test_kilavuz_kurulum_yordami.py` — model adına doğrudan bağlı assert yok (alan adları ve paket dosya listesi); paket dosya adları değişirse `test_atif_yapilan_paket_dosyalari_paketin_tasidiklari` etkilenir.
Türevler (T143): v6 için `.onnx`/`.engine` YENİDEN dışa aktarılmalı; `turevler` altına yeni ad + `kaynak_sha256` = v6 sha yazılmalı, `.engine` sha `DERLENINCE_YAZILIR` yer tutucusu; Jetson'da `codes/model_registry.py --turev-kaydet` ile doldurulur; eski v35 türevleri `kaynak_sha256` uyuşmadığından YETİM → RED (fail-closed). `jetson_paket/models/jetson_derleme_manifest.json` (`asil_model_pt`, sha listesi) ve `jetson_paket_hazirla.py` yeniden koşumu gerekir.

## ÖLÇÜLEMEDİ
- Kabul zinciri (65) bu lens'te yeniden koşulmadı (GPU'yu hafif kullanma emri; `gece_v6_v35taban_65.log` mevcut). K1 257 kayıtlı sayıdır.
- 000196'daki asfaltın neden sınıf 1 etiketlendiği (v1'de de öyle) — etiketleme kararı, bu lens ölçmedi.
