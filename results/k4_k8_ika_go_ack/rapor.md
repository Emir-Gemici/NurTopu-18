# K4+K8 — IKA_GO ACK'lı tekrar + hakem aktarım kanıtı (fail-closed)

Kaynak: `results/sartname_bosluk/rapor.md` K4 / K8 satırları · REVIEW_LOG D-02 · şartname §2.2.5 / §2.2.3.

## Bulgu (değişiklik öncesi, koddan)
- `comms/yks_gui.py::_cmd_gonder` IKA_GO'yu TEK paket gönderiyor, ACK beklemiyor, `btn_ika_go` kilitleniyordu.
- `_mesaj_isle` içinde `ACK` dalı YOKTU — İKA'nın ACK'ı yere düşüyordu.
- `comms/ika_receiver.py` IKA_GO'ya ACK ZATEN dönüyordu ve latch idempotentti (`ika_go_monotonic` ilk alımda sabit); ama OPEN_ROUTE ACK'ı yalnız gönderene (İHA) gidiyordu → YKS'de aktarım kanıtı görünmüyordu.
- `onayla` 2. adımı ("İKA'ya aktarıldı") kanıtsız veriyordu.

## Yapılan
| Dosya | Değişiklik |
|---|---|
| `codes/karar_sozlesmesi.py` (+ ayna `jetson_paket/kod/`) | `IKA_GO_TEKRAR_ARALIGI_S = 0.25`, `IKA_GO_TEKRAR_UST_SINIRI = 20` (gerekçe yorumda: SiK RTT < 100 ms; 20×0,25 = 5 s > İKA hb_timeout 3 s) |
| `comms/protocol.py` (+ ayna) | `ack(ref, node, ref_tip=None)` — isteğe bağlı `ref_tip`; seq çakışmasını ayırır, eski ACK uyumlu |
| `comms/komut_tekrar.py` (YENİ) | `AckliTekrar` durum makinesi (BOS/BEKLIYOR/ONAYLANDI/VAZGECILDI), saat enjekte edilir, Tk yok |
| `comms/ika_receiver.py` | `yks_peer` + `--yks`; OPEN_ROUTE/NO_ROUTE ACK kopyası YKS'ye; ACK'larda `ref_tip`; YKS adresi IKA_GO'dan öğrenilir; mükerrer IKA_GO her seferinde ACK'lanır (latch değişmez) |
| `comms/yks_gui.py` | `_ham_gonder` (aynı seq tekrar), `ika_baslat` → `AckliTekrar.baslat` + `kok.after` tik; `_ika_go_tik` üst sınırda KIRMIZI "İKA ONAY VERMEDİ ✗", düğme yeniden aktif, `t_ika0=None`; `_mesaj_isle` `ACK` dalı → `_ack_isle`: "İKA ALDI ✓ hh:mm:ss" etiketi + günlük; `ika_rota_ack` kanıt sözlüğü; `onayla` 2. adım kanıtsız RET; `_aktarim_onay_dugmesini_kur` düğme pasif + gerekçe / kanıt gelince aktif; demo İKA `yks_peer` ile, demo İHA rotayı İKA'ya da gönderir |
| `CONTRACTS.md` | YENİ §6.5 (ACK bağlama + IKA_GO tekrar sözleşmesi), §7 not |
| `comms/README.md` | `--yks` zorunluluğu, `komut_tekrar.py` satırı |
| `tests/test_ika_go_ackli_tekrar.py` (YENİ, 11 test) | durum makinesi; gerçek UDP loopback'te ilk 3 IKA_GO düşürülür → 4. ulaşır → ACK → tekrar durur; ACK hiç gelmez → üst sınır → kırmızı + düğme aktif + yeniden tetiklenebilir; mükerrer IKA_GO idempotent + her alım ACK; rota ACK YKS'ye yansır; kanıtsız 2. onay pasif/RET, kanıt gelince açılır |
| `tests/test_ika_go_gate.py`, `test_iha_landed_gate.py`, `test_yks_gui_aktarim_zamani.py` | fixture uyumu (yeni alanlar: `ika_go_tekrar`, `lbl_ika_go`, `ika_rota_ack`) — beklentiler değişmedi |

## Komutlar ve ham çıktılar
- `venv codes/test_rota_sentetik.py` → `SONUC: 15/15 dogru` · `[OK] TUM DETERMINISTIK SAHNELER GECTI`
- `venv -m unittest discover -s tests -q` (worktree, değişiklik SONRASI): `Ran 776 tests · FAILED (failures=3, errors=8, skipped=13)` → `unittest_yeni.txt`
- Taban (`git stash` ile, değişiklik ÖNCESİ): `Ran 765 tests · FAILED (failures=3, errors=8, skipped=13)` → `unittest_taban_stash.txt`
  - 11 düşüşün adları BİREBİR AYNI (model_registry / saha_parametrik / imgsz / kompozit dizini — worktree'de model+veri yok). Fark: +11 yeni test, hepsi OK.
- Yeni testler ayrıntılı: `yeni_testler_v.txt` — `Ran 11 tests · OK`, `[K4_UDP] dusurulen=3 ulasan_deneme=4 ika_go=True tekrar_durdu=1`
- Mutasyon: `mutasyon_cikti.txt` — 5 mutasyon (tekrar döngüsü kaldırıldı / YKS ACK dalı kaldırıldı / fail-closed kapı kaldırıldı / rota ACK yansıtma kaldırıldı / mükerrer IKA_GO ACK kaldırıldı) → hepsinde testler DÜŞTÜ; her geri alma sha256 ile bayt-eş doğrulandı.
- Aynalar: `diff comms/protocol.py jetson_paket/kod/protocol.py` ve `karar_sozlesmesi` → boş (AYNALAR_ES). `yks_gui.py`, `ika_receiver.py`, `komut_tekrar.py` için `jetson_paket/kod/` altında ayna YOK.

## ÖLÇÜLEMEDİ / açık
- Gerçek SiK 433 MHz hatta RTT ve 0,25 s aralığın hattı boğmadığı ölçülmedi (donanım yok); sabit gerekçesi hesapla.
- Tk penceresi gerçekten açılarak `kok.after` zincirinin akışı elle doğrulanmadı (mantık sahte saatle ölçüldü; `after` çağrısı mock ile doğrulandı).
- Rapor K8'deki "İHA ACK penceresi 2 s, hakem ACK'ı İHA'ya ulaşmayabilir" (iha_sender.py:93-121) bu görevde ele ALINMADI — ayrı iş.
