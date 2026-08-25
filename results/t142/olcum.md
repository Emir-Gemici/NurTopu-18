# T142 / T135 ÖLÇÜM — zemin sağlamlık kapısı eşikleri v35'e karşı · letterbox paydası

Tarih 2026-08-26 · kod DEĞİŞTİRİLMEDİ · eşik DEĞİŞTİRİLMEDİ (öneri yalnız §5).
Betik: scratchpad `t142_olc.py` (65_kabul_denetcisi.kaplama() yolu birebir: `_preprocess -> predict(imgsz 512, conf 0,30, GPU) -> get_masks -> _maskeleri_icerige_kirp`, sınıf 0).
Ölçüm fonksiyonları üretimin KENDİSİ: `karar_sozlesmesi.zemin_kaplamasi / zemin_kenar_dayanmasi`.
Ham çıktı: `results/t142/olcum.json` (kare kare, 4 alan) · `results/t142/olcum_stdout.txt`.

## 0. Defter kontrolü (D-252) — yeniden ölçülmeyen / doğrulanan
- `results/t133/kapatma_curutme_10.json` T52 kaydı v35 için kadraj 260 + otopark 67 + arena'yı ZATEN ölçmüştü (kaplama 0,1795..0,6442 · kenar maks 0,5004 sa_000176; otopark kap 0,3704..0,6626, kenar maks 0,3999; arena 0,1508 / 0,0000). Bu koşum aynı sayıları birebir üretti (§1) — kayıt alıntılanır, çelişki yok.
- D-86 v24 otopark (kap 0,770..0,866 · kenar 0,579..0,971) ve D-283 v24 arena (0,579 / 0,585) da birebir üretildi.
- Bu koşumun YENİ kısmı: (i) `icerik=None` (letterbox) paydasıyla AYRI hesap, (ii) DJI 0038 val 59, (iii) 4 aday eşik çifti tablosu, (iv) v24'ün sentetikte alt eşiklerde ödediği bedel.

## 1. Dağılımlar (min / p05 / p50 / p95 / maks)

| model / küme | n | içerik oranı | kaplama (icerik=None) | kaplama (kutu) | kenar (icerik=None) | kenar (kutu) |
|---|---|---|---|---|---|---|
| v35 / a sentetik kadraj_t66 | 260 | 1,00 (640x640, letterbox YOK) | 0,1795/0,2197/0,3298/0,5075/**0,6442** | aynı | 0,000/0,0125/0,1377/0,2778/**0,5004** | aynı |
| v35 / b otopark raw_frames | 67 | 0,5625 (576x1024) | 0,2083/0,2346/0,2855/0,3500/0,3727 | 0,3704/0,4171/0,5076/0,6223/0,6626 | 0,000/0,0054/0,0904/0,1759/0,2273 | 0,000/0,0942/0,2356/0,3607/0,3999 |
| v35 / c DJI 0038 val | 59 | 0,5625 (2160x3840) | 0/0/0/0,0535/0,0776 | 0/0/0/0,0951/0,1380 | 0/0/0/0,0157/0,0210 | 0/0/0/0,0405/0,0617 |
| v35 / d arena s9 | 1 | 0,5987 (634x1059) | 0,0903 | 0,1508 | 0,000 | 0,000 |
| v24 / a sentetik | 260 | 1,00 | 0/0,0231/0,2723/0,5131/0,7651 | aynı | 0/0/0,0692/0,3245/0,6882 | aynı |
| v24 / b otopark (ÇÖKÜŞ, D-85/86) | 67 | 0,5625 | 0,4333/0,4347/0,4507/0,4842/**0,4869** | **0,7703**/0,7727/0,8013/0,8608/0,8656 | 0,0890/0,1097/0,2605/0,2815/**0,2815** | **0,5792**/0,6604/0,8501/0,9516/0,9712 |
| v24 / c DJI 0038 val | 59 | 0,5625 | 0/0/0/0,0845/0,1242 | 0/0/0/0,1503/0,2208 | 0/0/0/0,0188/0,0856 | 0/0/0/0,0719/0,1095 |
| v24 / d arena s9 (ÇÖKÜŞ, D-283) | 1 | 0,5987 | 0,3464 | 0,5785 | 0,1907 | 0,5846 |

Sınır kareler: v35 sentetik en yüksek kaplama sa_000233 0,6442 (kenar 0,224); en yüksek kenar sa_000176 0,5004 (kaplama 0,494) — tek başına 0,50'yi aşan tek kare, AND'in kaplama kolu sayesinde geçiyor.

## 2. Eşik tablosu — AND reddi (kaplama > K VE kenar > E), gerçek İÇERİK KUTUSU paydasıyla

| çift K/E | v35 sentetik RET (meşru, n=260) | v35 otopark RET (67) | v35 DJI RET (59) | v35 arena RET (1) | v24 otopark YAKALAMA (çöküş, 67) | v24 arena YAKALAMA (çöküş, 1) | v24 sentetik RET (260) |
|---|---|---|---|---|---|---|---|
| **0,67/0,50 (mevcut)** | **0** | 0 | 0 | 0 | **67/67** | **0/1** | 1 |
| 0,60/0,45 | **0** | 0 | 0 | 0 | 67/67 | 0/1 | 3 |
| 0,55/0,40 | **0** | 0 | 0 | 0 | 67/67 | **1/1** | 4 |
| 0,50/0,35 | **0** | **6** | 0 | 0 | 67/67 | 1/1 | 5 |

Tek kol aşımları (v35 sentetik, kutu): kaplama>K -> 0 / 5 / 8 / 14 ; kenar>E -> 1 / 1 / 1 / 1.
v35 otopark 0,50/0,35'te reddedilen 6 kare: frame_000009 (0,626/0,355), 000013 (0,602/0,351), 000016 (0,601/0,392), 000017 (0,642/0,400), 000018 (0,663/0,375), 000011 (0,598/0,363).
v24 sentetik 0,50/0,35 reddi: sa_000135 (0,680/0,544), sa_000162 (0,604/0,603), sa_000176 (0,570/0,658), sa_000196 (0,648/0,688), sa_000023 (0,682/0,379). D-86'daki sa_000150 bu koşumda v24'te 0,335/0,075 (D-86: 0,617/0,658) — sayı uyuşmuyor; D-86'nın hangi ön işleme/eşikle ölçtüğü kayıtta yok, ÖLÇÜLEMEDİ.

Aynı tablo `icerik=None` (letterbox tuvali) paydasıyla — 16:9 kümelerde HER satır 0: v24 otopark çöküşü **0/67** yakalanır (dört çiftte de), v24 arena 0/1. Sentetik 640x640'ta letterbox olmadığından None = kutu.

## 3. T135 — letterbox paydasında İKİ kol da ölü (yalnız kaplama değil)
- kaplama tavanı = içerik oranı = **0,5625** (16:9) — D-268 §6 ile aynı.
- **kenar tavanı**: `_maskeleri_icerige_kirp` dolguyu sıfırladığı için tuvalin üst/alt kenarı hep 0; yalnız sol/sağ kenar (içerik yüksekliği) sayılır -> tavan = 2h/(4w-4) = **0,2815** (16:9; 1920x1080 için 0,2814, 1280x720 ve 1024x576 için 0,2815). Ölçüm: v24 otopark ken_none maks **0,2815** = tavana tam dayanmış (kutu paydasında aynı kare 0,9712).
- Sonuç: `icerik=None` + 16:9 letterbox + kırpılmış maske -> kaplama <= 0,5625 ve kenar <= 0,2815 -> **dört aday çiftin hiçbiri ateşleyemez** (0,50/0,35 dâhil). D-268 §6'nın "kenar kolu çalışmaya devam eder" cümlesi kırpılmış maske için YANLIŞTIR.

### Çağıran noktalar (okundu)
| yer | çağrı | icerik geçiyor mu | kapı durumu |
|---|---|---|---|
| `jetson_paket/kod/kamera_dogrula.py:118` | `rota_bul(mk, mpp=None, plan=False, gorsel_cikti=False)`; `mk` :117'de `_maskeleri_icerige_kirp` ile tam tuvale kırpılmış | **HAYIR** (`icerik` :112 `_preprocess` dönüşünde elde var, geçirilmiyor) | ÖLÜ: 16:9 kamerada iki kol da tavana takılı (§3). Düzeltme: `icerik=icerik` eklemek; `rota_bul` imzası (`costmap_path_finder.py:951-953`) zaten alıyor |
| `scripts/saha_kuru_kosu.py:722` | `rota_bul(kirpik, mpp=mpp)`; maske fiziksel kırpılmış (`v[y0:y0+h, x0:x0+w]`) | HAYIR ama gerek yok: maske zaten içerik boyutunda -> None = kutu | canlı. Bu yol yalnız TANISAL (:710 yorumu); otorite `:708 rota_bul(maskeler, mpp=mpp, icerik=icerik)` icerik GEÇİRİYOR |
| `scripts/jetson_fps.py:226-227` | `rota_bul(maskeler, mpp=None, plan=False, gorsel_cikti=False, icerik=icerik)` | **EVET** | canlı |
| `iha_haritala` (İKA yolu) | kare mozaik MOZ_PX=1024 | D-268 §6: kapı canlı | yeniden ölçülmedi |

Üretim yolunda `icerik`in kaynağı tek ve zaten mevcut: `rpi_inference._preprocess(bgr)` üçüncü dönüş değeri `(x0, y0, w, h)`. T135 için gereken yalnız `kamera_dogrula.py:118`e `icerik=icerik` geçirmek; ek hesap yok. (Kod değiştirilmedi — bu görev ölçüm.)

## 4. ÖLÇÜLEMEDİ
- v35'te çöküş sınıfı yok (D-283): otopark 0/67, arena kap 0,15. Dört çiftin **v35 çöküşünü** yakalama gücü ÖLÇÜLEMEDİ — vekil v24 maskeleri; v24 çöküşünün v35 çöküşüne benzediğine dair kanıt yok.
- v35 otoparkta 0,50/0,35'in 6 reddi meşru mu çöküş mü: T47 (D-284) v35'in çim/toprağın %37'sini zemin saydığını ölçmüştü; bu 6 kare o sınıfa mı giriyor, yer gerçeği olmadan ÖLÇÜLEMEDİ.
- DJI 0038: iki modelde de kaplama <= 0,22 — kapı bu kümede hiçbir eşikte ilgili değil; kırsal çöküş dağılımı yok.
- Gerçek arena n=1 (D-85'in sınırı sürüyor). D-86'daki sa_000150 sayıları yeniden üretilemedi (yukarıda).

## 5. Karar için öneri (eşik DEĞİŞTİRİLMEDİ)
1. **Eşik çifti önerisi: 0,55/0,40.** Meşru v35 sentetikte 0 ret (dört çift de 0); v35 otopark/DJI/arena 0 ret; çöküş vekilinde 67/67 + arena çöküşünü yakalayan **en muhafazakâr çift** (0,67 ve 0,60 arena çöküşünü kaçırıyor: kaplama 0,5785 < 0,60). 0,50/0,35 ek çöküş yakalamıyor ama v35 otoparkta 6 ret üretiyor ve v35 sentetikte kaplama kolunda 14 kare tek başına eşik üstüne çıkıyor — pay eriyor, tercih edilmez.
   Payın darlığı gizlenmiyor: 0,55'te v35 meşru kaplama kolunu 8 kare tek başına aşıyor (maks 0,6442), AND'i kenar kolu (o karelerde <= 0,28) kurtarıyor; sa_000176 kenar 0,5004 > 0,40 ama kaplama 0,494 < 0,55 ile geçiyor (pay 0,056).
2. Öneri **v24 vekiliyle** alınmıştır; v35'in kendi çöküş dağılımı yok. `karar_sozlesmesi.py:415` kuralı ("model değişince kalibrasyon zorunlu") için bu betik kalıcılaştırılmalı (ayrı görev; kod değişikliği bu görevin dışında).
3. **T135**: `kamera_dogrula.py:118` `icerik=icerik` geçirmeli (kaynak `_preprocess`). Kırpılmış maske + `icerik=None` 16:9'da iki kolu da öldürüyor (kaplama <= 0,5625, kenar <= 0,2815); D-268 §6'daki "kenar kolu çalışır" cümlesi düzeltilmeli. `rota_bul`un `icerik=None`da tam tuvali içerik sayması (:960) letterboxlı çağıran için sessiz fail-open; öneri: `rota_bul`, `icerik=None` iken maskenin tamamen boş üst/alt bantları varsa uyarı/sebep üretsin (mimar kararı).
