"""T216 (D-438 §2e) — `simulation/scripts/mission_demo.py` URETIM PORTUNA BAGLANMAZ.

NEDEN: demo IKA/YKS alicilarini sabit 127.0.0.1:5006 / :5005'e bind ediyordu.
Bunlar CONTRACTS'taki URETIM YKS/IKA portlaridir; saha PC'sinde `yks_gui`
acikken (5 Eylul, D-427 sinifi) demo `WinError 10013` ile duser. T209'un
`comms/test_comms.py` icin uyguladigi kalip (ephemeral bind + `UDPLink.port`)
buraya da uygulandi. Iki kilit:

  T1  vakumluluk: kaynakta uretim portu sabiti YOK (yorum disi kodda sayi gecmez)
  T2  uretim portlari TUTULUYORKEN demo gercek rota.json ile exit 0 ve
      "UCTAN UCA AKIS TUTARLI" yazar (gercek UDP soketleri, gercek comms)
  T3  cp1254 konsol: cikti pipe'a cp1254 ile yazilsa da betik DUSMEZ
      (D-438 §2a sinifi — '✓' / '═' karakterleri)

Port sayilari burada CIPLAK yazilmaz (madde 16): uretim argparse
varsayilanlarindan okunur (`tests/test_p8_sim_katmani.py` ile ayni yordam).
"""
import json
import re
import socket
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
# T220 / K10: eskiden ciplak `O:/navitas-local-train/venv/Scripts/python.exe` idi
# (test_p4/test_p8 ile ayni kusur, Jetson'da FileNotFoundError). Suit uretim
# yorumlayicisiyla kosar (madde 13); alt surec AYNI yorumlayiciyi kullanir.
VENV = sys.executable
DEMO = KOK / "simulation" / "scripts" / "mission_demo.py"
URETIM_KAYNAK = {"yks": "yks_gui.py", "ika": "ika_receiver.py"}

# comms/test_comms.py ile ayni gecerli geometri (ilk nokta [0,0], segment <= 2,1 m)
ROTA = {"yol_no": 2, "guven": 0.91, "referans_xy": [-20.0, -24.5],
        "rota_yerel": [[0.0, 0.0], [0.3, 1.8], [-0.4, 3.5], [0.4, 5.0]]}


def _uretim_portlari():
    portlar = {}
    for ad, dosya in URETIM_KAYNAK.items():
        src = (KOK / "comms" / dosya).read_text(encoding="utf-8")
        m = re.search(r'"--bind",\s*default="0\.0\.0\.0:(\d+)"', src)
        assert m, f"{dosya}: `--bind` varsayilani bulunamadi"
        portlar[ad] = int(m.group(1))
    return portlar


def _tutucu_ac(port):
    """Portu canli YKS gibi tut (SO_EXCLUSIVEADDRUSE); baska surec tutuyorsa None."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
        s.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
    try:
        s.bind(("127.0.0.1", port))
    except OSError:
        s.close()
        return None
    return s


class MissionDemoPortu(unittest.TestCase):

    def test_T1_kaynakta_sabit_uretim_portu_yok(self):
        src = DEMO.read_text(encoding="utf-8")
        kod = "\n".join(satir.split("#", 1)[0] for satir in src.splitlines())
        for ad, port in _uretim_portlari().items():
            sabit = f'("127.0.0.1", {port})'
            self.assertFalse(sabit in src,
                             f"mission_demo.py hala {ad} uretim portuna sabit bagli: {sabit}")
            self.assertIsNone(re.search(rf"\b{port}\b", kod),
                              f"mission_demo.py yorum disi kodunda {ad} portu ({port}) geciyor")
        self.assertIn('bind=("127.0.0.1", 0)', src, "ephemeral bind yok")
        self.assertIn("ika_link.port", src)
        self.assertIn("yks_link.port", src)

    def _demoyu_kos(self, env=None):
        with tempfile.TemporaryDirectory() as d:
            rota = Path(d) / "rota.json"
            rota.write_text(json.dumps(ROTA), encoding="utf-8")
            return subprocess.run(
                [VENV, "-B", str(DEMO), "--rota-json", str(rota)],
                capture_output=True, timeout=120, env=env)

    def test_T2_uretim_portlari_tutuluyorken_demo_gecer(self):
        portlar = _uretim_portlari()
        tutan = {}
        for ad, port in portlar.items():
            t = _tutucu_ac(port)
            if t is not None:
                self.addCleanup(t.close)
            tutan[ad] = "bu test" if t is not None else "baska surec"
        s = self._demoyu_kos()
        out = s.stdout.decode("utf-8", "replace")
        self.assertEqual(
            s.returncode, 0,
            f"uretim portlari {portlar} tutuluyorken ({tutan}) demo dustu:\n"
            f"{out[-600:]}\n{s.stderr.decode('utf-8', 'replace')[-600:]}")
        self.assertIn("UÇTAN UCA AKIŞ TUTARLI", out)
        self.assertIn("ACK: ['ika', 'yks']", out)

    def test_T3_cp1254_pipe_ile_dusmez(self):
        """Cikti kodlamasi zorla cp1254: reconfigure(errors='replace') olmasa
        '✓'/'═' UnicodeEncodeError ile exit 1 olurdu (D-438 §2a)."""
        import os
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "cp1254"
        env.pop("PYTHONUTF8", None)
        s = self._demoyu_kos(env=env)
        self.assertEqual(s.returncode, 0,
                         f"cp1254 ciktida demo dustu:\n"
                         f"{s.stderr.decode('utf-8', 'replace')[-400:]}")
        self.assertNotIn(b"UnicodeEncodeError", s.stderr)


if __name__ == "__main__":
    unittest.main()
