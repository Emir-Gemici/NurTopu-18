# JETSON OTURUM DURUMU · 9 Eylül 2026 — Jetson tarafındaki ajandan depoya not

> **Kim yazdı:** Jetson Orin Nano üzerindeki Claude oturumu (Fable 5.1). **Kimin isteğiyle:** Halil (Navitas takımı;
> Jetson'daki kullanıcı adı `n4vitas`, GitHub hesabı `navitas26`). Halil'in sözü: *"ilk oturumda istenilenleri tespit et,
> hangisi olmadıysa onu bir dosyada yaz ve commit'e at; geliştiriciye ait yapay zeka commit'i incelediğinde ihtiyaç olanı
> anlasın, olanı anlasın, kendini ve nerede olduğunu, geçmişte ve bu süreçlerde neler olduğunu detaylıca anlat."*
>
> **Kime:** PC tarafındaki mimar (Claude 1) ve onun altındaki ajanlar. Bu dosya bir **ölçüm kaydı değil**, bir **devir
> notudur**; her sayı için kanıt yolu verilmiştir. Kural aynen: **ÖLÇÜLEMEDİ ≠ GEÇTİ.** Depo anayasası (`CLAUDE.md`)
> bu oturum için de bağlayıcıdır: kod çekirdeğine dokunulmadı, REVIEW_LOG'a yalnız eklendi, hiçbir dosya silinmedi.

---

## 1. Ben kimim, neredeyim

| | |
|---|---|
| Makine | Jetson **Orin Nano Developer Kit 4 GB** (p3767-0004), L4T R39.2.1 = JetPack 7.2.1, Ubuntu 24.04, Python 3.12, NVMe kök 233 GB. Künye: `results/jetson_20260906/ORTAM_KUNYESI.txt` |
| Paket kökü | `~/proje/NAVITAS_JETSON_20260906/navitas` (`~/navitas` symlink) — 6 Eylül'de HDD'den kopyalanan `D:\NAVITAS_JETSON_20260906` paketi + bu oturumda depodan aktarılan dosyalar. **Git deposu değil** (`.git` yok; `navitas_depo.bundle` 28 Ağustos hâli) |
| Depo klonu | `~/proje/github/navitas_github` — `yazilim-takimi/navitas` master, blob'suz sparse klon (9 Eyl 23:09, `181c310`) |
| Python | `~/venv312` (`--system-site-packages`): torch 2.11.0+cu130, ultralytics 8.4.142, tensorrt 10.16.2, pymavlink 2.4.49, onnxruntime-gpu 1.29 (CUDA sağlayıcısı sm_87'de çalışmaz) |
| Engine | `jetson_paket/models/navitas_seg_v36_best_512_fp16.engine` (57 283 989 B, sha `bb9bd868…0300`) — **yalnız bu kartta koşar**, depoya girmez (`.gitignore *.engine`) |
| Sistem | 8 GB `/swapfile`, `nvpmodel` 10W, `n4vitas` dialout+video, `~/.local/bin/mavproxy.py` → venv, `~/.local/bin/gh` 2.100.0 |
| Bağlı olmayan donanım | IMX477 kamera, Pixhawk, SiK — 6 ve 9 Eylül'de **bağlı değildi**; o kapılar hâlâ ÖLÇÜLEMEDİ |

## 2. Geçmiş — ne oldu, sırayla

**6 Eylül 2026, 17:05–19:30 (1. oturum, Jetson).** Paket "Jetson Nano 4 GB / JetPack 4.6 / Python 3.6" için hazırlanmıştı;
kart Orin Nano çıktı. Kurulum bu karta göre yapıldı (`orin_nano_root_kurulum.sh`, `orin_nano_venv_kurulum.sh`). Kapılar:
genel kapı 15/15 · defter GEÇTİ · T16 engine derlendi (530 s) ve deftere yazıldı · T17 FPS pt 1,35/1,06, engine 1,58/1,33
(eşik 0,61) · 10 dk sürekli koşum düşüşsüz · engine↔pt denkliği F1/F2 GEÇTİ, **D-303 oransal 3/126 DÜŞTÜ → uçuş `.pt`** ·
tam süit Ran 2121 F5/E30/S8 (26'sı ortam). Kayıt pakette D-428 olarak yazıldı; kullanıcı isteğiyle `GELISTIRICIYE_20260906`
devir klasörü (7 birleştirme + K1–K11 listesi) USB ile PC'ye gitti. Süreç: `results/jetson_20260906/JETSON_KURULUM_SURECI_20260906.md`.

**6–7 Eylül gecesi (PC, mimar).** Paket master'a işlendi: **D-431** (D-428 numarası çakıştı). K3/K4/K5 uygulandı, G0b ile
künye bantları (K1), K10 için yalnız liste (`results/jetson_20260906/K10_LISTE.md`). Ardından D-432…D-436, FDR, T211.

**9 Eylül 2026, 22:55–23:45 (2. oturum, Jetson — bu dosya).** `gh` ile depoya girildi, klon alındı, D-431 birleştirmesi
madde madde doğrulandı (`GITHUB_KONTROL_20260909.md`, paket dizininde), sonra **geri aktarım** yapıldı: depodaki
114 dosya (43 değişen + 71 yeni; liste `results/jetson_log_20260909/AKTARILAN_DOSYALAR.txt`) Jetson paketine kopyalandı.
Kapılar aktarım sonrası yeniden koşuldu (§4). Kod çekirdeği (`codes/`, `comms/` — `test_comms.py` hariç) depo ile
**birebir aynıydı**, engine yeniden derlenmedi (model v36 değişmedi).

## 3. İlk oturumda istenenler — ne oldu, ne olmadı

Kaynaklar: paket `OKU_BENI.md` + `jetson_paket/GUN1_KONTROL_LISTESI.md` (mimarın Jetson'dan istediği) ve Halil'in oturum
içi istekleri. ⚠ 1. oturumun ham sohbet kaydı 9 Eylül 23:03'te diskten kalkmış (oturum temizliği; ben silmedim); istek
listesi o oturumun ürettiği belgelerden ve hafıza notlarından derlendi.

| # | istenen | durum | kanıt / not |
|---|---|---|---|
| G1 | Sürümler ve güç: JetPack/TRT/CUDA notu, güç modu azami, tegrastats | ✅ | `ORTAM_KUNYESI.txt`; `nvpmodel -m 0`, `jetson_clocks`; tegrastats FPS koşumlarında |
| G2 | Paket bütünlüğü, v36 `.pt`/`.onnx` sha == defter | ✅ | `model_kayit_dogrula` → `eslesti` / `turev_eslesti` (6 ve 9 Eyl) |
| G3 | T16 FP16 engine derleme + tek kare çıkarım + defter kaydı | ✅ | `results/jetson_20260906/jetson_log_20260906/engine_export.log`, `turev_kaydet.log` |
| G4 | **Doğruluk: `test_goruntuleri/` üzerinde engine ↔ PC referans KARARI (şerit no)** | ❌ **yazıldığı şekliyle yapılamadı** | Pakette v36 için PC referans kararı dosyası **yok** (`results/pc_referans_v17_20260805` yalnız v17). Yerine D-375 yöntemi (engine↔pt, GT'li 126 kare + 633 DJI karesi) koşuldu → D-303 oransal düştü. **İhtiyaç:** PC'de v36 `.pt` ile `test_goruntuleri/sentetik_arena` + `drone_kareleri` için şerit kararı listesi (JSON) üretilip depoya konması; Jetson'da engine ile aynı liste üretilip fark sayılacak |
| G5 | T17 FPS, p50 ve p95 ayrı, eşik 0,61 | ✅ | `results/jetson_20260906/jetson_fps_20260906_orin_nano/ozet.json` |
| G6 | 10 dk sürekli koşum, termal | ✅ | `…_orin_nano_10dk/` |
| G7 | Kamera hattı + ayna testi (D-349) | ⛔ ÖLÇÜLEMEDİ | kamera bağlı değil; köprü dosya kaynağıyla GEÇTİ |
| G8 | Rapor: JSON + tegrastats + registry diff geri | ✅ | devir klasörü → depoda `results/jetson_20260906/` |
| G9 | Pixhawk: `jetson_baslat.sh --kapi`, 3 uçta `mavlink_dogrula` | ⛔ ÖLÇÜLEMEDİ | Pixhawk bağlı değil; `--kuru` yalnız `/dev/ttyACM0` `[YOK]` (6 ve 9 Eyl aynı) |
| H1 | Halil: keşif raporu **md** olarak | ✅ | `results/jetson_20260906/JETSON_KESIF_RAPORU_20260906.md` |
| H2 | Halil: süreci md'ye yaz | ✅ | `JETSON_KURULUM_SURECI_20260906.md`; 9 Eyl: `JETSON_GERI_AKTARIM_SURECI_20260909.md` (paket dizini) |
| H3 | Halil: geliştiriciye devir klasörü | ✅ | `GELISTIRICIYE_20260906` → D-431 ile birleşti |
| H4 | Halil: "yazılım hem İHA'ya hem kendi drone'umuza uyar mı?" | ◐ kod okuması | D-431 §4(10): Jetson tarafı standart MAVLink, gövde bağımsız; **ArduPlane parametre seti ve provası yok (K11)** |
| H5 | Halil: hafızaya yaz (sudo dahil) | ✅ 9 Eyl | 6 Eyl'de parola bilinçli yazılmamıştı, 9 Eyl'de kullanıcı isteğiyle yazıldı |

## 4. 9 Eylül geri aktarım sonrası kapılar (Jetson)

| kapı | sonuç | ham |
|---|---|---|
| Genel kapı madde 14 | **GEÇTİ** — kol1 15/15 · kol2 şerit 15/15 | `results/jetson_log_20260909/genel_kapi.log` |
| Kayıt defteri (FP32 girdisi çıkmış hâliyle) | v36 `.pt` `eslesti` · `.onnx`/`.engine` `turev_eslesti` · v35 RED | `defter_dogrula.log` |
| Defter aynası | `config/` ↔ `jetson_paket/config/` bayt-eş | — |
| `jetson_baslat.sh --kuru` (udp) | 12 `[VAR]`, tek `[YOK]` `/dev/ttyACM0` → çıkış 3 (Pixhawk yok) | `jetson_baslat_kuru.log` |
| Tam süit | **Ran 2204 · failures 4 · errors 28 · skipped 20** (447 s). 6 Eyl: 2121 · F5 E30 S8. 32 kırmızının tamamı ortam/bilinen: 18 `O:/…python.exe` (K10 #1–2), 5 kabul kümesi `O:/` (K10 #3–4), 2 `navitas-local-train/ayarlar.py` (K10 #5), 1 `/` altına tmp (K10 #6), 1 `dataset/test29_v3.yaml` pakette yok (`test_gece_karisiklik_matrisi`, yeni), 1 `git` yok → "commit f3441b4 depoda yok" (`test_gece_akis_diyagramlari`, yeni; paket git değil), 2 Py3.12 (`test_142 is`, `test_0_on_kosul recursion`), 1 K9 kuru koşu gerçek makinede sahte eksik üretemiyor, 1 `test_yks_kamera_istemci` zamanlama. **Aktarılan koddan kaynaklı yeni hata YOK**; 6 Eyl'deki `.gitignore` (K10 #7) ve tqdm hataları kapandı | `unittest_tam_suit.log` |

## 5. Geliştiriciden İHTİYAÇ olanlar (öncelik sırasıyla)

1. **K2 — T66 kabul kümesi Jetson'a.** `scripts/olcum/170_engine_karar_denkligi.py --s-kume kabul` hazır ama
   `config/model_registry.json` `kabul_kumesi` hâlâ `O:/navitas-local-train/calisma/sentetik_arena_kadraj_t66`. T66 (~260 kare +
   manifest) ve `_ACILI_t189` kümesi pakete/depoya konmadan engine kararı Jetson'da verilemez; registry yolu depo köküne
   göre olmalı (madde 16).
2. **G4 — v36 PC referans kararları** (`test_goruntuleri/sentetik_arena`, `drone_kareleri` için şerit no listesi). Yoksa
   Gün-1 §4 kapısı hiç ölçülemez.
3. **K10 — süitteki `O:\` çıplak yolları** (`tests/test_p4_runbook.py:15`, `test_p8_sim_katmani.py:24`, `test_depo_koku_turetilir.py`,
   registry `kabul_kumesi*`). Liste ve öneriler `results/jetson_20260906/K10_LISTE.md`; Jetson'da süit bu yüzden hep kırmızı.
4. **K11 — ArduPlane parametre seti** (final sabit kanat) + SITL provası.
5. `JETSON_KILAVUZ.md` başlığı ve FPS satırı hâlâ "Orin NX"; bant yok (K1'in kalan parçası).
6. `wheels/` (246 MB, cp38) silme kararı Halil'in (madde 18) — bant kondu, dosyalar duruyor.
7. K6 (post-process darboğazı) ve K8 (onnxruntime-gpu sm_87) mimar kararı.

## 6. Jetson'da OLANLAR (geliştiricinin yeniden yapması gerekmeyenler)

- Kurulum betikleri, venv, swap, güç kipi, symlinkler (§1). Yeniden kurulum gerekmez.
- Engine derlenmiş ve defterle eş; model v36 değişmedikçe yeniden derlenmez. Sürüm değişirse yordam
  `GERI_AKTARIM.md` §2 adım 4 (paket dizininde) — `yolo export … .pt`, `--turev-kaydet`, `jetson_paket_hazirla.py`.
- Depodaki 7 Eylül 13:16 hâli (belgeler, testler, betikler, pixhawk param) Jetson paketine işlendi.
- `gh` girişli; sonraki güncellemeler `cd ~/proje/github/navitas_github && git pull` + aynı aktarım yordamıyla alınır.

## 7. Sahada açık kalanlar (Jetson'dan bağımsız, takım)

IMX477 (`jetson-io` → ayna testi) · Pixhawk `--kapi` · SiK `KIP=sik` · T211 motor künyesi (insan) · D-433 `RC6_OPTION` ·
D-428 RC failsafe · D-434 devrilme kök nedeni.
