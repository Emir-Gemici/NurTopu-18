# ONARIM-06 — T227 `rpi_inference --isaretli-yayin`: yayınlanmış karar bindirmeli video

**Durum:** KAPANDI (yazılım + Jetson'da dosya kaynağıyla koşuldu) · canlı CSI kamera ve gösterici/MK15 zinciri **koşulmadı**
**Tarih:** 17 Eylül 2026 · **Liste:** madde 06 · **Ham kanıt:** `results/onarim/onarim06_isaretli_yayin/`

## Sorun
T227 (D-443 kusur b): modelin **seçtiği rotayı** gösteren görüntü yoktu; YKS'ye yalnız ham kamera gidiyordu. D-448'deki ilk uygulama FPS kapısından düşmüş ve **hiç birleşmemiş** (commit `73a5b4f9` depoda yok). `jetson_baslat.sh` bayrağı arıyor, bulamayınca `GOSTERICI_KIP`'i kapalı tutuyordu.

## Çözüm (TASARIM §1.1 / §4 T227'ye göre)
- `codes/isaretli_yayin.py` (yeni):
  - `isaretli_kare_ciz()` saf çizim: kamera içeriği + zemin (yeşil) / engel (kırmızı) maske + rota noktaları + büyük etiket `SECILEN ROTA: n - AD` / `ROTA YOK - <sebep>` + güven, kare no, yayın no, UTC, "KARAR URETMEZ". 1280×720, en-boy korunur (4:3 içerik dolgulanır).
  - `IsaretliYayin`: çıkarım döngüsü yalnız **referans** bırakır (`kare_bildir`, ≤ 2 Hz, fazlası sayılıp atlanır); çizim + JPEG **ayrı iplikte**. HTTP için `scripts/kamera_koprusu.py`'nin `KareUretici` + `KopruSunucusu` **yeniden kullanıldı** (`/kare.jpg`, `/video`, `/durum`) — `isaretli_gosterici` buradan okur.
  - Bindirme **yayınlanan** karardan: yalnız `KararYumusatici`'dan geçen kararda `karar_yayinlandi` çağrılır; bastırılan farklı şerit adayı etiketi değiştirmez.
- `codes/rpi_inference.py`: `--isaretli-yayin HOST:PORT` (yalnız `--camera`, biçim denetimi), `run_camera(..., isaretli=None)`, `isaretli_yayin_ac` (port doluysa UYARI + yayınsız devam), `_isaretli_bildir` (hata kararı etkilemez).
- Paket: `scripts/jetson_paket_hazirla.py` KOPYALAR'a `isaretli_yayin.py`, `kare_keskinligi.py` (22 → 24); paket yeniden üretildi (bayat `rpi_inference.py` ve `config/model_registry.json` kopyaları da tazelendi).

## Kanıt
```
tests/test_onarim06_isaretli_yayin.py  Ran 9  OK
  etiket · çizim boyut/renk/etiket · 4:3 dolgu · açık/kapalı yayınlar BİREBİR · bastırılan aday bindirmeyi değiştirmez
  · HTTP /kare.jpg 1280x720 + /durum + ≤2 Hz · CLI yalnız --camera + HOST:PORT · port doluysa None
mutasyon: `if satir.get("yayinlandi")` -> `if True` : FAILED (bastırılan aday testi); geri alınca OK
test_jetson_comms_paketi OK (önceden 2 FAIL — bayat kopyalar da düzeldi) · test_rpi_canli_olcek OK · test_faz_b_rpi_ekransiz OK
test_p5_histerezis OK · test_isaretli_gosterici OK · test_faz_b_jetson_baslat OK · test_fdr_t244_ic_celiski OK · test_fdr_sarkan_atif_kapisi OK
```
Satır kayması atıfları: `rpi_inference.py:2568,2719 → 2569,2728` (t244 testi, FDR B3 iki yer, ACIK_KALEMLER).

### Jetson ölçümü (17 Eyl 13:50–14:02, v36 `.pt`, 36 DJI karesi → dosya köprüsü 10 fps → `--camera`)
| koşu | yayın | fps_ortalama | fps_p95 |
|---|---|---|---|
| kapali1 | yok | 5,551 | 6,522 |
| acik1 | 127.0.0.1:8081 | 5,629 | 6,542 |
| kapali2 | yok | 5,796 | 6,567 |
| acik2 | 127.0.0.1:8081 | 5,564 | 6,523 |
Ortalama kapalı 5,67 · açık 5,60 → **−%1,3** (koşular arası oynama ±%2,2 içinde) → ön kayıtlı "FPS etkisi ≤ %5" **geçti** (not: kapı PC'de tanımlıydı; bu Jetson ölçümü, `fps_ortalama` çıkarım süresinden türer).
Canlı uç: `/durum` → `kare_sayaci 41 · boyut [1280, 720] · son_kare_yasi 0,033 s · kodlama_hatasi 0`; `isaretli_kare.jpg` (ROTA YOK – HEDEF_YOK, maske bindirmeli).
⚠ İlk betikteki `acik1.jpg` 503 JSON'du (curl kare yokken kaydetmiş) — ürün değil ölçüm betiği hatası; ayrı koşuyla gerçek kare alındı.

## Geniş karşılaştırma (commit öncesi ↔ sonrası, temiz worktree, 87 test dosyası)
Düzelen (kırmızı → yeşil): `test_jetson_comms_paketi`, `test_jetson_paket_defteri`, `test_k0_iki_olcum_hatti`, `test_t135_kamera_dogrula_icerik`, `test_t143_turev_ve_kamera`, `test_t220_jetson_istekleri` (paket kopyalarının tazelenmesiyle).
Yeni kırmızı 1: `test_kilavuz_kurulum_yordami` — kılavuzun `cp kod/...` satırı yeni iki modülü kopyalamıyordu → `JETSON_KILAVUZ.md` ve `jetson_paket/JETSON_KILAVUZ.md` satırına `kod/isaretli_yayin.py kod/kare_keskinligi.py` eklendi → **OK**. Genel kapı 15/15 · 15/15.

## Kalan
- Canlı CSI kamerayla ve `GOSTERICI_KIP=x11` gösterici ile uçtan uca koşu (kamera ölçümü bekleyen maddelerle birlikte).
- Ağdan erişim: varsayılan 127.0.0.1; YKS'ye göndermek için `--isaretli-yayin 0.0.0.0:8081` ya da gösterici/RTSP (ONARIM-09 kapsamında karar).
