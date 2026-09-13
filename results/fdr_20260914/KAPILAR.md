# T263 — adım 1–2 kapı kanıtı, 14 Eylül 2026

Yazan: Codex-1. Bağımsız denetleyen bekliyor; bu kayıt görev kabulü değildir.
Tüm komutlar depo kökünde çalıştırıldı.

| Komut | Gerçek çıktı | Çıkış | Ham kayıt |
|---|---|---:|---|
| `MPLCONFIGDIR=/tmp/navitas-mpl .venv/bin/python -B -m unittest discover -s tests -p 'test_fdr*.py' -q` | `Ran 77 tests in 9.715s` / `OK` | 0 | `fdr_kapilari.log` |
| `MPLCONFIGDIR=/tmp/navitas-mpl .venv/bin/python -B -m unittest discover -s tests -p 'test_gece_sekiller.py' -q` | `Ran 11 tests in 0.011s` / `OK` | 0 | `sekil_kapisi.log` |
| `MPLCONFIGDIR=/tmp/navitas-mpl .venv/bin/python -B codes/test_rota_sentetik.py` | `GENEL KAPI (madde 14): GECTI — kol1 15/15 · kol2 serit 15/15` | 0 | `genel_kapi.log` |
| `python3 -B scripts/fdr_acik_kalem_cikar.py --dogrula` | `GUNCEL — 569 açık kalem satırı` | 0 | son kontrol; satır sayısı benzersiz iş sayısı değildir |
| `git diff --check` | çıktı yok | 0 | son kontrol |

## İlk başarısız çağrı

`MPLCONFIGDIR=/tmp/navitas-mpl .venv/bin/python -B -m unittest tests.test_fdr_t244_ic_celiski tests.test_fdr_sarkan_atif_kapisi tests.test_gece_sekiller tests.test_fdr_takvim_kapisi tests.test_fdr_bolum4_6eylul_kaniti -q`

→ `Ran 5 tests in 0.000s`, `FAILED (errors=5)`, çıkış 1.
Neden: `tests.*` modülleri import edilemedi (`ModuleNotFoundError`);
gerçek testler çalışmamıştı. Ham kayıt `belge_kapilari.log` korunur.
Keşif (`discover -s tests`) çağrısıyla yukarıdaki 77 + 11 test gerçekten koşuldu.

Tam depo süiti, yeni Gazebo/MuJoCo görev koşumu ve fiziksel saha ölçümü bu görevde yapılmadı.
