# K10 — tests/ içinde Jetson'da ORTAM hatası veren çıplak yol / PC varsayımı listesi

> Kaynak: paket `kanit/jetson_log_20260906/unittest_tam_suit.log` (6 Eylül 18:06, Orin Nano,
> `Ran 2121 · F5 E30 S8`) — bu dosya **yalnız LİSTE**dir; düzeltme bu turda YAPILMADI
> (G0b görev tanımı: "bu turda DÜZELTME, yalnız liste"). Satır numaraları 7 Eylül worktree
> hâlidir (`git grep -n`), log satırları paket logundandır. Toplam **26** ortam hatası
> = K10 beyanındaki 26 ile tutuyor (7 + 10 + 1 + 4 + 3 + 1).

| # | test dosyası:satır | çıplak yol / varsayım | Jetson'daki hata (log satırı) | düşen test sayısı | öneri (uygulanmadı) |
|---|---|---|---|---|---|
| 1 | `tests/test_p4_runbook.py:15` | `VENV = "O:/navitas-local-train/venv/Scripts/python.exe"` | `FileNotFoundError: … 'O:/navitas-local-train/venv/Scripts/python.exe'` (log 441–540, `SahaBaslatKomutlari` 7 test) | 7 | yorumlayıcıyı `sys.executable`'dan al (madde 13 PC'de zaten venv ile koşuyor); ya da `VENV` yoksa `unittest.SkipTest("PC venv'i yok")` |
| 2 | `tests/test_p8_sim_katmani.py:22` | `VENV = "O:/navitas-local-train/venv/Scripts/python.exe"` | aynı `FileNotFoundError` (log 557–701: `CommsLoopbackSarmalayici` 1, `SimBetikleriDuman` 7 alt-test, `YksMonitorKilidi` 2) | 10 | aynı: `sys.executable` |
| 3 | `tests/test_t125_denetci_olculemedi.py:126` → `scripts/olcum/65_kabul_denetcisi.py:73` → `config/model_registry.json:10` | `profiles.competition.kabul_kumesi = "O:/navitas-local-train/calisma/sentetik_arena_kadraj_t66"` (çıplak PC yolu **registry'de**) | `RuntimeError: kabul kumesi dizini yok: O:/…/sentetik_arena_kadraj_t66` (log 718–727) | 1 | kabul kümesi Jetson'a taşınmadı (T66 ~260 kare, paket dışı); test "küme yoksa `SkipTest` + ÖLÇÜLEMEDİ" demeli — fail-closed betik davranışı (RuntimeError) **doğru**, test onu ortam olarak ayırmalı. Kalıcı çözüm: registry yolu `_depo_koku` türevi (madde 16) |
| 4 | `tests/test_t189_k5a_acili_kol.py:95,100,106,117` → `65_kabul_denetcisi.py:73/101` → `model_registry.json:10,12` | `kabul_kumesi` + `kabul_kumesi_acili = "O:/…/sentetik_arena_kadraj_ACILI_t189"` | `RuntimeError: acili kabul kumesi dizini yok …` ×3, `kabul kumesi dizini yok …` ×1 (log 747–792) | 4 | #3 ile aynı |
| 5 | `tests/test_depo_koku_turetilir.py:28` (kullanım: 44, 65→72) | `EGITIM_AYARLAR = KOK / "navitas-local-train" / "ayarlar.py"` — kardeş depo PC'de var, pakette yok | `FileNotFoundError: …/navitas/navitas-local-train/ayarlar.py` (log 345–363, 2 test) | 2 | dosya yoksa `SkipTest("kardeş depo yok")`; ya da paket `navitas-local-train/ayarlar.py`'yi taşısın |
| 6 | `tests/test_depo_koku_turetilir.py:146` | `tempfile.TemporaryDirectory(dir=str(Path(KOK.anchor)))` — sürücü kökü `O:\` varsayımı; Linux'ta `anchor = "/"` → `/` altına yazma | `PermissionError: [Errno 13] Permission denied: '/tmpsyqhnuqa'` (log 378) | 1 | Linux'ta `dir=None` (varsayılan `/tmp`); `KOK.anchor` yalnız Windows'ta anlamlı |
| 7 | `tests/test_faz_b_nano_kurulum.py` K5 `test_wheels_repoya_girmez` | `.gitignore` okur — paket `git` olmadan taşındı, `.gitignore` yok | `FileNotFoundError` (log 409) | 1 | `.gitignore` yoksa `SkipTest` (paket git değil); depoda koşunca zorunlu kalır |

**Ortam dışı, ama aynı logda (K10 beyanı, referans için — bu listenin konusu DEĞİL):**
`test_donusum_esleme` / `test_t144_kirpma` / `test_t54_esleme_uygulaniyor` import hatası (tqdm — oturumda kuruldu),
`test_faz_b_protocol_dayaniklilik` ön koşulu + `test_k6 … is` (Py 3.12 davranışı, 2),
`test_faz_b_jetson_baslat K9` (gerçek makinede sahte eksik üretemiyor, 1),
`test_t143 … YER_TUTUCU` (engine sha gerçek — K3, G0a), `test_uretim_modeli_hizasi manifest` (düzeltildi),
`test_yks_kamera_istemci` (zamanlama, 1).

**Doğrulama komutu (worktree, 7 Eylül):**
```
grep -n -E "O:[\\/]|navitas-local-train|KOK\.anchor" tests/test_p4_runbook.py tests/test_p8_sim_katmani.py tests/test_t125_denetci_olculemedi.py tests/test_t189_k5a_acili_kol.py tests/test_depo_koku_turetilir.py
grep -n "kabul_kumesi" config/model_registry.json
```
t125/t189'da çıplak yol **test dosyasında değil**, `config/model_registry.json` satır 10/12'dedir; testler
`65_kabul_denetcisi.kabul_kumesi_yolu()` üzerinden ona ulaşır (fail-closed RuntimeError, D-115/133 tasarımı).
