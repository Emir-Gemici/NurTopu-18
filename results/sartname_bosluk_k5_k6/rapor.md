# K5+K6 — şartname §6.2 süre limitleri (2026-08-26)

Kaynak: `results/sartname_bosluk/rapor.md` satır 85-86 (K5, K6).

## Şartname alıntıları (PDF, venv fitz, sayfa 23-24)

- §6.2: *"Uçuş süresi, İHA'nın mancınık sisteminden ayrılması (fırlatma) ile başlar.
  Güzergâh tespiti, veri aktarımı ve İHA'nın paraşütle inişini tamamlaması ile sona
  erer. Bu işlemler için tanınan maksimum süre 15 dakikadır."*
- §6.2: *"... İKA'nın HB'ye ulaşması için verilen maksimum süre 10 dakikadır. Bu
  sürenin aşılması durumunda İKA görevi başarısız kabul edilecektir."*
- §6.4 Süre Aşımı: *"Bu süreçler için tanımlanan azami süre 15 dakikadır."*
- (sayfa 19 §5 FDR test uçuşu "maksimum 10 dakika" — final sahası değil, alınmadı.)

## Yapılan

| kusur | eski | yeni |
|---|---|---|
| K5 | `ika_nav.py --timeout 60` TEK deadline: rota+IHA_LANDED+IKA_GO+sürüş | `ika_gorevi()`: **bekleme** deadline (`IKA_BEKLEME_SURESI_S`=900) + **sürüş** deadline (`IKA_SURUS_SURESI_S`=600, izin anında başlar); `navigate(..., surus_deadline_monotonic, saat)` süre dolunca `send_vel(0,0)` + False; çıkış kodları 0/1/2/3/4. `--timeout` = `--bekleme-suresi` takma adı. `navitas_sim.dinamik_ika_gorevi` aynı gövdeyi kullanır (`--surus-suresi` eklendi, `--route-timeout 60` simülasyonda kaldı). |
| K6 | `iha_inis_yayinci` CLI iniş sonrası heartbeat yok → 3 s'de `link_lost` | `--heartbeat-sure` (varsayılan `IHA_INIS_HEARTBEAT_SURESI_S`=600) + `--heartbeat-aralik` (0,5 < hb_timeout 3); `iha_inisini_yayinla(heartbeat_suresi, heartbeat_araligi, saat)`; `heartbeat_until` Event yolu (simülasyon) korunur. |

Sabitler gerekçeli: `codes/karar_sozlesmesi.py` sonu. Sözleşme: `CONTRACTS.md §7.1` (yeni).
Kılavuz: `jetson_paket/JETSON_KILAVUZ.md §3` (ika_nav saha komutu + heartbeat notu), `simulation/KULLANIM.md`.
İkiz: `jetson_paket/kod/{iha_inis_yayinci,karar_sozlesmesi}.py` — `diff` boş.

## Kapılar (gerçek çıktı)

```
codes/test_rota_sentetik.py            -> SONUC: 15/15 dogru
unittest discover -s tests (worktree)  -> Ran 774 tests  FAILED (failures=3, errors=8, skipped=13)
taban (git stash, değişiklik yok)      -> Ran 765 tests  FAILED (failures=3, errors=8, skipped=13)
düşen küme diff                        -> DUSEN_KUME_AYNI (11 ortam: model_registry/saha_parametrik/imgsz/yks_gui kompozit — worktree'de model/veri yok)
tests/test_k5_k6_sure_limitleri.py     -> Ran 9 tests OK
[K5] bekleme_deadline=+900s surus_deadline=izin+600s rota=61s izin=+240s exit=0
[K5] surus deadline=5s -> durdu adim=5 son_vel=(0, 0) sonuc=False
[K6] gercek UDP: landed→bitis=1.64s > hb_timeout=0.4s, heartbeat_gorulen=21, link_lost=False, exit=0
[K6] heartbeat_suresi=600s aralik=0.5s -> heartbeat=1200
[K6] heartbeat_suresi=0s aralik=0.5s -> heartbeat=0
```

## Mutasyon kanıtı (kök satır bozuldu → koştu → düştü → bayt-eş geri alındı)

```
[M1 ika_gorevi: surus deadline = bekleme deadline (ayrim kaldirildi)] exit=1 FAILED (failures=1) FAIL: test_bekleme_60s_de_dusmez_ve_surus_deadline_i_ayri_isler   geri alindi bayt-es=True
[M2 navigate: surus deadline kontrolu kaldirildi]                     exit=1 FAILED (failures=1) FAIL: test_navigate_surus_deadline_dolunca_durur_false_doner       geri alindi bayt-es=True
[M3 iha_inisini_yayinla: heartbeat suresi 0'a cekildi]                exit=1 FAILED (failures=1) FAIL: test_gercek_udp_inis_sonrasi_heartbeat_surer_link_lost_olmaz geri alindi bayt-es=True
[M4 CLI varsayilani 0]                                                exit=1 FAILED (failures=1) FAIL: test_cli_varsayilani_sozlesmeden_gelir                        geri alindi bayt-es=True
```

## Açık noktalar

- `results/t123/saha_gunu_kontrol_listesi.md` git'te izlenmiyor ve ana dizinde; worktree'den
  düzenlenmedi. Oraya `JETSON_KILAVUZ §3`'teki `ika_nav.py comms --bind 0.0.0.0:5006` bloğu
  kopyalanmalı.
- Gerçek MAVLink/SiK ile saha koşumu ÖLÇÜLEMEDİ (donanım yok); UDP loopback ile ölçüldü.
- `git stash` deposu worktree'ler arasında ORTAK: taban ölçümü sırasında başka bir ajanın
  stash'i (rpi_inference/iha_sender/saha_kuru_kosu/test_rpi_telsiz_yayin) benim `pop`umla
  bu worktree'ye geldi; commit'lenmeden `diger_ajan_geri_kondu_wf640-2_rpi_telsiz` adıyla
  yeniden stash'lendi (stash@{0}). Paralel ajanlar taban için stash yerine `git worktree`
  ya da `git diff | git apply -R` kullanmalı.
