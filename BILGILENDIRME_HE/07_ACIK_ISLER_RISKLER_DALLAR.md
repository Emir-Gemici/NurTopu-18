# 07 — Açık işler, riskler, git dal haritası

## Uçuştan ÖNCE (yarın) — öncelik sırasıyla

| # | İş | Kim | Nerede |
|---|---|---|---|
| 1 | Pervane somunları: dördü de elle kontrol. İki düşüş iki köşede aynı imzayı taşıyor | İNSAN | 06 |
| 2 | Pixhawk açılışında "MAG0 initial yaw alignment complete". GPS1 kablosunu oturt | İNSAN | 04 |
| 3 | Jetson telemetri kapısı kurulumu (`uygula.py`) | Jetson açık + ethernet | 03 |
| 4 | Kamera ok testi, montaj açısı (+90/−90). Görev üreticisine ve pilot kartına yaz | İNSAN + Jetson | 05 |
| 5 | Canlı telsiz onay testi: her saniye yeni seq, hakem iki adım, onay kalıcı mı. Yeni seq'li test betiği **henüz yazılmadı** | yazılım + Halil | 02 |
| 6 | YKİ'yi bu daldan yeniden aç. Arkadaş .exe kullanacaksa paketi bu daldan yeniden üret | İNSAN | 02 |
| 7 | Jetson güç yolu: fiş, regülatör çıkışı. 10 dk duvar adaptörü ya da kablo oynatma testi | İNSAN | 03 |
| 8 | Yazılımla uçuş yalnız Jetson açıkken. Yalnız MP bağlıyken GUIDED'da 5 s kopma LAND'a düşürür | kural | 04 |

## Uçuştan SONRA

- **K8:** Jetson karar trafiğini azalt. Aynı kararı yalnız değişince ya da 1 Hz'de gönder. K8b'nin 278 ms'sinin asıl kaldıracı bu.
- **gps_fix tazeliği:** `inis_kaniti` içinde GPS alanlarına 2,5 s tazelik. Ortak modül olduğu için onay gerekiyor (03).
- **Dal birleştirme:** tünel çizgisi ↔ origin/master (aşağıdaki harita). Halil'in çakışma raporu origin/master'da: commit 034da6dc.
- **origin/master'da `IKA_IZ_GENISLIGI_M 0.39` → 0.4595** (ölçülü değer, D-472).
- **Defter numarası çakışması:** origin/master'da Halil'in bir **D-505**'i var ("K8 belgesi REVIZYON 2 + D-505").
  Bu çizginin D-505 … D-516 kayıtları farklı olaylar. Birleştirirken birinin numarası değiştirilmeli.
- `sik_ayar.py`: "OK" kontrolü + geri okuma + uzak doğrulanmadan ATZ engeli (D-507, Halil'e öneri).
- Belgelerde "kırmızı ≤ 4 s" ifadesini "sarı 3 s, kırmızı 5 s" yap (02).
- YKİ İHA durumunun TAZE/BAYAT arasında 1–2 s gidip gelmesi (D-516 madde 6). Sarı "ZAYIF" bandı kısmen çözüyor; ayrıca bakılmalı.
- `RADIO_STATUS` akmıyor, RSSI ölçülemiyor (D-508 ölçüm 6).
- Jetson'da kod üç kaynaktan karışık. Tek saha dalı ve sha256 manifest gerekiyor (`jetson_manifest.py` hazır).
- Kamera için kalıcı çözüm: `rota_ekseni_derece` ya da montaj açısı parametresi (05).
- Testlerin bıraktığı izlenmeyen `results/prova/2026091*_*` klasörleri silinmedi.

## Riskler (yarın için)

| Risk | Etki | Azaltma |
|---|---|---|
| Pervane somunu gevşemesi | düşüş (iki kez oldu) | her uçuş öncesi elle kontrol |
| Jetson güç kesintisi | 1–2 dk rotasız | güç yolu testi. YKİ'de "kimlik SICRAMASI" = Jetson yeniden açıldı |
| Harici pusula kopması | yaw hatası, kayma | MAG0 kuralı, kablo sabitleme |
| Kamera yönü işareti yanlış | yanlış şerit, **0 puan** | ok testi, YKİ'de rotanın aşağıdan yukarı aktığını görmek |
| Onay düzeltmesi canlı denenmedi | hakem onayı tamamlanamaz | canlı test (02) |
| K8 düştü | rota geç gelebilir | tekrar mekanizması var. Kararlar 0,4 s'de geldi, ACK 0,22 s'de |
| .exe paketi bayat | arkadaşın YKİ'si eski davranır | Python ile aç ya da paketi yeniden üret |

## Git dal haritası (19 Eyl 21:30)

| Dal | Yerel | origin | Ne var |
|---|---|---|---|
| **`bilgilendirme-he`** | bu commit | itildi | `tunel-saha-20260918` (eb6a0c20) + 19 Eyl dosyaları + bu belgeler |
| `tunel-saha-20260918` | eb6a0c20 | febc273d | Saha YKİ ve yönlendirici dalı. Yerel master'ın tamamını içerir. Bu akşamki 6 YKİ/yönlendirici commit'i origin'de bu dalda yok, `bilgilendirme-he`'de var |
| `kamera-dayanikli-20260919` | c9ee27f0 | 67467c4f | Jetson `rpi_inference` (kamera beklemesi + telemetri kapısı). Tabanı origin/master 7aec0a1a. c9ee27f0 dosyaları bu dalda `results/jetson_20260919/kurulum2/` altında birebir duruyor |
| `master` (yerel, O:\navitas) | f3314ba3 | — | origin/master'dan 82 ileri, 107 geri. Tamamı `tunel-saha`'nın içinde |
| `origin/master` | — | 7aec0a1a | Halil (trs-1342): 107 commit. K8 belgeleri, `sik_ayar`, FOV ölçümü (53–54°), ONARIM-19 video, `fda_gorev_uret.py`, çakışma raporu |

- **Ortak taban:** bdda2e3b. Tünel çizgisi ile origin/master o noktadan beri ayrı gidiyor.
  Çakışma beklenen yerler: `comms/yks_gui.py`, `REVIEW_LOG.md`, `jetson_paket/`, `codes/rpi_inference.py`.
- ⚠ **Denetlenmemiş commit:** tünel çizgisinde `3f13b2e1` "WIP DENETLENMEDI: Codex'in YKS tek-rota / rota koordinat paneli" (14 Eyl) var.
  YKİ'deki "rota" görünümü buradan geliyor. Defterde denetim kaydı yok. Uçuş sonrası denetlenmeli.
- `tests/test_yks_gui_uretim_hizasi.py` görünüm listesinde "rota" eksikti. Bu dalda düzeltildi; tek satır.

## Bu dalın test durumu (itmeden önce koşuldu)

Kanıt: `results/push_kapisi/20260919_211422/` (`tam_suit.txt`, `genel_kapi.txt`, `taban_karsilastirma.txt`).

| Kapı | Sonuç |
|---|---|
| Genel kapı (`codes/test_rota_sentetik.py`) | **GEÇTİ** — kol1 15/15 · kol2 şerit 15/15 |
| Tam süit (3119 test) | **KIRMIZI** — 21 başarısız, 11 hata, 34 atlandı |
| Taban karşılaştırması | tabanda (eb6a0c20, temiz klasör) **33** kırmızı, bu dalda **32**. Bu dalın getirdiği yeni kırmızı **yok**; bir tanesi düzeldi |

Kırmızılar 14 dosyada toplanıyor. Hepsi tabanda da aynı adla kırmızı:

- **Git dışı dosyalar:** model ağırlıkları, kayıt defteri ve fikstür kareleri yeni bir klasörde yok.
  İlgili dosyalar: `test_saha_parametrik`, `test_model_registry`, `test_imgsz_tek_kaynak`, `test_t123_gecis_provasi`, `test_t38_kuru_kosu_fiksturu`.
- **Satır atıfları kaydı:** bugünkü `yks_gui` değişiklikleri belgelerdeki `dosya:satır` atıflarını kaydırdı.
  İlgili dosyalar: `test_atolye_test_gunu`, `test_gece_akis_diyagramlari`, `test_fdr_t244_ic_celiski`.
- **Defter işaretleri:** `test_d373_defter_geri_isaret`, `test_defter_butunlugu`.
- **Diğer:** `test_mavlink_tunel_uctan_uca` (K4 256 B tampon), `test_t202_jetson_paket_butunlugu`, `test_saha_kuru_kosu`, `test_yks_gui_uretim_hizasi` (kompozit dizini).

Anayasa §5 "tam süit yeşil olmadan push yok" der. Bu dal kullanıcının açık "push at" emriyle itildi.
Taban karşılaştırması kanıt olarak eklendi. Süitin yeşile dönmesi ayrı bir iş ve **uçuş sonrasına** kaldı.
