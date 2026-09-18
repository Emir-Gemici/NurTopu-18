"""NEDEN: ONARIM-18 teslim kapilarinin komut, ham cikti ve exit kaniti."""
import json
import os
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[2]
out = Path(__file__).resolve().parent
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', MPLCONFIGDIR='/tmp/navitas-mpl')
groups = ['test_onarim18_heartbeat_akislari', 'test_t162_alan_ihlali',
          'test_a2_karar_yasi', 'test_yki_gnss_telemetri', 'test_t243_mesaj_boyutu',
          'test_iha_inis_yayinci', 'test_rpi_telsiz_yayin', 'test_onarim18_kalkis_kapisi',
          'test_inis_kaniti', 'test_faz_b_akis_istegi', 'test_k5_k6_sure_limitleri',
          'test_seri_pixhawk_kilidi', 'test_jetson_comms_paketi',
          'test_faz_b_protocol_dayaniklilik', 'test_yks_gui_dayaniklilik']
code = ('import sys,unittest; sys.path.insert(0,"tests"); '
        f's=unittest.defaultTestLoader.loadTestsFromNames({groups!r}); '
        'r=unittest.TextTestRunner(verbosity=2).run(s); sys.exit(not r.wasSuccessful())')
jobs = [('hedefli', ['-c', code]),
        ('heartbeat_mutasyon', ['results/onarim18_heartbeat_20260917/mutasyon.py']),
        ('kalkis_mutasyon', ['results/onarim18_kalkis_20260917/mutasyon.py']),
        ('genel_kapi', ['codes/test_rota_sentetik.py']),
        ('tam_suit', ['-m', 'unittest', 'discover', '-s', 'tests', '-v'])]
summary = []
for name, args in jobs:
    cmd = [sys.executable, '-B', *args]
    print('BASLADI', name, flush=True)
    with (out / (name + '.log')).open('w') as f:
        try:
            result = subprocess.run(cmd, cwd=root, env=env, stdout=f, stderr=subprocess.STDOUT, timeout=1500)
            rc = result.returncode
        except subprocess.TimeoutExpired:
            rc = 124
    summary.append(dict(name=name, command=cmd, exit=rc))
    (out / 'kapilar.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print('BITTI', name, 'exit=', rc, flush=True)
raise SystemExit(any(j['exit'] for j in summary))
