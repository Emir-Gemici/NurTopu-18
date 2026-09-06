# DEVAM NOKTASI — 6 Eylül 2026, 21:00 (saha akşamı bitti, uçuş yok)

> Bugün iki iş oldu: (1) **Jetson aktarım paketi** HDD'ye alındı, (2) **saha
> oturumu** — Pixhawk tarafında 7 kalem ölçümle kapandı, RC failsafe ölçüldü ve
> **düştü**, kumanda pili bitti, uçuş **yapılmadı** (üç kez istendi, reddedildi).
> Tam kayıt: `REVIEW_LOG.md` **D-428**. Önceki devam noktası (4 Eylül gecesi)
> `git log`'da; oradaki açık kalemlerden kapanmayanlar aşağıda §4'te.

## 1. Jetson aktarım paketi — HAZIR

`D:\NAVITAS_JETSON_20260906\` · 9,7 GB · 17.764 dosya · HDD'de 28,6 GB boş kaldı.
- `OKU_BENI.md` (paket kılavuzu) + `izinleri_duzelt.sh` (NTFS sonrası `+x`
  onarımı; koşturuldu, 5/5 kritik dosya doğrulandı) + `navitas/` (repo düzeni).
- İçinde: `jetson_paket/` (966 MB), `wheels/` (51 aarch64 cp38), `models/`
  (tüm sürümler), `results/` (4,9 GB), `data/`, `test_images/`, `codes/`
  (runs/ hariç), tüm `.md`/PDF, `navitas_depo.bundle` (git geçmişi), 0038
  doğrulama kümesi.
- **sha256 doğrulandı:** `models/navitas_seg_v36_best.pt` =
  `1d1caca6…6911`, `jetson_paket/models/navitas_seg_v36_best_512_fp16.onnx` =
  `f4c9f5fe…deab` — `config/model_registry.json` ile birebir.
- `D:\navitas` (16 Ağustos, 56 GB eski yedek) **dokunulmadı**; operatör
  silinmesini istedi, mimar CLAUDE.md md. 18 gereği silmedi — karar Yunus'un.

## 2. Saha oturumu — ne kapandı (ölçüm) / ne kaldı

| ✅ kapandı | kanıt |
|---|---|
| Sürüm `ArduCopter V4.5.7 (2a3dc4b7)` | Messages |
| Pil gerilimi 15,8 = 15,8 (`BATT_VOLT_MULT 18.18` doğru) | multimetre + MP |
| Accel + level | 20:22 dökümünde `INS_ACCOFFS/SCAL`, `AHRS_TRIM` dolu (18:37'de sıfırdı) |
| Pusula ×2 (ikincisi temiz yerde, `Check mag field` sonrası) | ofset 13 / 130 (< 300) — 2. kalibrasyon sabah dökümünde |
| ESC kalibrasyonu (Skywalker 60A V2) | POWER1 çıkarılmış + USB passthrough + sonra pil yordamı; "5'te 5" (beyan) |
| ESC künyesi: Hobbywing Skywalker 60A V2, BEC 5 V/5 A | etiket (beyan) → FDR B3/5/7 |
| Motor testi | "motorlar doğru" (**beyan**) |
| Parametre dökümü | `config/pixhawk/arducopter_fda_20260906.param` (20:22) |

| 🔴 açık — pervane takılmadan önce | nasıl kapanır |
|---|---|
| **RC failsafe DÜŞTÜ** (alıcı son değeri tutuyor) | kumanda `RX Setup → Failsafe → All channels` (SwC Land, gaz altta) → test: TX kapat, CH5 Land'e zıplar, HUD `Land` |
| **Kumanda pili bitti** (TX uyarısı; RX full) | 4 yeni AA; ekranda TX gerilimi |
| `RC IN` fişi şüpheli (iki yeniden başlatmada RC gitti) | fişi sabitle, aracı sars, barlar kesilmesin |
| 3 ESC kırmızı tel (4 BEC paralel) | pil takılı değilken pini çıkar, bantla |
| Başıboş `SERVO` motor atamaları (MAIN 1–8, AUX 5–8) | `SERVO1–8, 13–16 = 0` → motor testi tekrar |
| Sabah dökümü | `arducopter_fda_20260906_sabah.param` → diff; 2. pusula + `FS_GCS_ENABLE` görülür |

## 3. Mimar kararı bekleyenler (uçuştan önce yazılır)

- `FS_THR_ENABLE` 1→3 ve `BATT_FS_LOW_ACT` 2→1 kartta **kimse bilmeden**
  değişmiş (D-428 §5b). Hop için Land doğru; **30 m görev** için karar: şablonu
  mu değiştiririz, kartı mı geri alırız.
- `FS_GCS_ENABLE`: hop için 5 (Land) istendi; görevde D-406 C anlamına (1) dönüş.
- `RC_PROTOCOLS`: 4'ün iBUS çözmediği **kanıtlanmadı** (TX pili + fiş karıştı).
  Sabah tek değişkenli test (D-428 §5a); sonucu şablon/README/test P5'e yansır.
- `SR1_*` 2/2 → `mavlink_dogrula` (MP kapalı) ile ölçülür.
- Belgelerdeki `arducopter_fda_20260905.param` atıfları → 06'ya (5 Eylül dökümü
  hiç alınmadı). README'ye ESC yordamı (D-428 §3) girer.

## 4. Önceki devam noktasından hâlâ açık (4 Eylül gecesi listesi)

- Nano'da `python3.8` kurulumu internet ister, çevrimdışı yedeği yok.
- Taşıyıcı kartın modeli depoda yazmıyor; eMMC boş çıkarsa kurtarma pini bilinmiyor.
- USB dışında Jetson'a dosya yolu (ethernet/scp) belgede yok — HDD paketi bunu
  kısmen kapattı (NTFS: `ntfs-3g` + `izinleri_duzelt.sh`).
- `YKS_IP` elle beyan, DHCP'de sessiz red (kod+belge).
- **T209** (`test_comms` 5005/5006'ya bind, D-427): YKS açıkken tam suit kırmızı.
  Bu akşam da YKS canlıydı (`results/prova/20260906_114143_11440/` yazıyordu).

## 5. Sabah sırası (40 dk, pervane en son)

1. Kumanda: yeni piller, TX gerilimi ≥ 5 V.
2. Failsafe menüsü + test (kapat → CH5 Land).
3. `RC IN` sabitle, sars-test.
4. 3 kırmızı tel dışarı (pil yok).
5. `SERVO1–8, 13–16 = 0` → Write → motor testi (A ön-sağ CCW, B arka-sağ CW,
   C arka-sol CCW, D ön-sol CW) — bu kez **liste hâlinde** yazılır.
6. `RC_PROTOCOLS` tek değişkenli testi (4 → reboot → decoding?).
7. Sabah dökümü → repo.
8. Pil ≥ 15,4 V, PreArm sıfır, pervane yönleri, somunlar.
9. **Hop:** Stabilize, diz boyu, ≤ 30 sn, MP `Set Mode → Land` hazır. Gündüz,
   ikinci kişi yanında.

## Açık uyarılar

- ⚠ **"Önce" dökümü üzerine yazıldı** — MP `Save to file` aynı ada. Sabah dökümü
  **farklı adla** kaydedilsin.
- ⚠ Codex ana ağaca canlı yazıyor olabilir; birleştirmeden önce `git status`
  ve mtime (D-412 dersi).
- ⚠ Operatör kimliği: oturuma "Halil" girdi, sonra "Emir'dim" dedi; tutanak
  ikisini de yazıyor. Pilot kararı kimde, kaptan netleştirsin.
