# K1 — Üretim algı yolu telsiz halkası (şartname §2.2.3) · 2026-08-26

Kaynak boşluk: `results/sartname_bosluk/rapor.md` K1 — `codes/rpi_inference.py`
`run_camera`/`run_video` telsize HİÇ yazmıyordu; OPEN_ROUTE/NO_ROUTE üreticisi yalnız
Gazebo betiğiydi. Sahada İHA kararı YKS'ye ve İKA'ya ulaşmıyordu.

## Yapılan

| dosya | değişiklik |
|---|---|
| `codes/karar_sozlesmesi.py` | `KARAR_YOK_SEBEBI`, `ROTA_GEOMETRI_SEBEBI`, `IHA_HEARTBEAT_ARALIK_S = 1.0`, `YAYIN_REF_XY = (0,0)` (çıplak sayı yok) |
| `comms/iha_sender.py` | `piksel_rotayi_yerele_cevir` (tuval px → yerel m, y ters, ≤ `MAX_SEGMENT_M` bölme, `rota_geometrisini_dogrula`'dan geçer); `KararYayinci` (karar iş parçacığı latest-wins + ayrı HEARTBEAT iş parçacığı; fail-closed: ret sebebi/None → NO_ROUTE; OPEN_ROUTE yalnız `IhaSender.send_open_route` üzerinden — güven kapısı ÇOĞALTILMADI); `yayinci_kur` |
| `codes/rpi_inference.py` | `_iha_sender_modulu` (tembel, yalnız hedef verilince), `_karari_yayinla`; `run_camera`/`run_video` `yayinci=None` kwarg + her karede yayın; argparse `--yks-hedef/--ika-hedef/--telsiz-seri/--telsiz-baud`; `main` kurulum/`stop`/`close`; hedef yalnız `--camera`/`--video` ile |
| `scripts/saha_kuru_kosu.py` | halka 8 artık ÜRETİM YOLUNU ölçer (`_uretim_yolu_telsiz_probu`: `run_camera` sahte kamera/model → gerçek UDP → `IkaReceiver`); rapora **`telsiz halkasi`** satırı |
| `CONTRACTS.md` | **§6.5** yeni (yayın sözleşmesi); §11.2 halka 8 sahibi güncellendi |
| `JETSON_KILAVUZ.md` + `jetson_paket/JETSON_KILAVUZ.md` | saha komutu `--yks-hedef/--ika-hedef` ve `--telsiz-seri` |
| `jetson_paket/kod/{rpi_inference,karar_sozlesmesi,iha_sender}.py` | ayna güncellendi — `diff` boş (AYNA_IKIZ_BOS_DIFF) |
| `tests/test_rpi_telsiz_yayin.py` | 11 test, gerçek loopback UDP |
| `tests/test_rpi_canli_olcek.py` | `run_camera` çağrı kilidi `yayinci=None` ile genişletildi |

## Komutlar ve gerçek çıktılar

```
venv -m unittest discover -s tests -p test_rpi_telsiz_yayin.py
Ran 11 tests in 6.955s
OK

venv codes/test_rota_sentetik.py
SONUC: 15/15 dogru
[OK] TUM DETERMINISTIK SAHNELER GECTI

venv scripts/saha_kuru_kosu.py --atla-cikarim --cikti results/K1_telsiz_halkasi/kuru_kosu
  aktarim        GECTI      ... uretim yolu run_camera karari loopback IKA'ya OPEN_ROUTE olarak yazdi
  telsiz halkasi GECTI      run_camera -> KararYayinci -> loopback IKA: {'open_route_alindi': True, 'heartbeat': 3, 'ack': ['ika'], 'hata': None}
  (kamera/olcek DUSTU: worktree'de data/raw_frames yok — ortam)

venv -m unittest discover -s tests -p test_saha_kuru_kosu.py   -> Ran 32  OK
venv -m unittest discover -s tests -p test_jetson_comms_paketi.py -> Ran 5  OK
venv -m unittest discover -s tests -p test_iha_sender_cli.py   -> Ran 3  OK
venv -m unittest discover -s tests -p test_rpi_canli_olcek.py  -> Ran 20 OK
```

Tam küme (worktree; model/veri/registry yok):

| | Ran | sonuç |
|---|---|---|
| taban (`git stash` ile temiz) | 765 | FAILED (failures=3, errors=8, skipped=13) — `taban_temiz_unittest.txt` |
| sonra | 776 | FAILED (failures=3, errors=8, skipped=13) — `son_unittest.txt` |

`diff` düşen test listeleri: **SON_DUSENLER_TABANLA_AYNI** (11 ortam düşüşü birebir aynı:
test_saha_parametrik ×7, test_model_registry, test_imgsz_tek_kaynak ×2, test_yks_gui_uretim_hizasi).
+11 = yeni testler.

## Mutasyon kanıtı (TEST_SPECS §4.1)

`run_camera` içindeki `_karari_yayinla(...)` çağrısı kaldırıldı:

```
sha256 önce : eb18a551...8d077f
mutasyon uygulandi
FAIL: test_esik_alti_guven_open_route_olarak_KACAMAZ
FAIL: test_karar_yok_sessizlik_degil_no_route_karar_yok
FAIL: test_open_route_ika_ve_yks_ye_ulasir_road_sozlesmesiyle
FAIL: test_ret_sebepli_karar_no_route_olur
Ran 11 tests in 33.629s
FAILED (failures=4)
sha256 sonra: eb18a551...8d077f  -> BAYT_ES_GERI_ALINDI
```

## ÖLÇÜLEMEDİ

- SiK 433 MHz seri hat üzerinde gerçek gönderim (donanım yok); `--telsiz-seri` yolu `SerialLink` ile
  `wait_ack=False` olarak kuruldu, yalnız UDP loopback ölçüldü.
- Jetson üzerinde kamera döngüsü FPS'e etkisi (gönderim ayrı iş parçacığında, ölçüm cihaz gelince).
