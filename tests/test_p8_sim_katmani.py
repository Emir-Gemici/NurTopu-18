"""P8 (D-392) — GAZEBO/SIM KATMANI EL ATMASI.

Harita taramasi (plan v2) bulgulari:
  1. `comms/yks_monitor.py` OPEN_ROUTE'a "HAKEM ONAYI: (otomatik)" basip
     ACK'i kendisi donuyordu — sahada acilirsa iki asamali onayi DELER.
     Simdi calistirma kilidi var: `--legacy-bilerek` olmadan exit 2.
  2. 7 sim betigini hicbir test zorlamiyordu -> duman kapisi (--help exit 0).
     CONTRACTS 11.1 geregi sim sahada kanit sayilmaz; kapi enflasyonu yok.
  3. `iha_flight.fly` yalniz mock'laniyordu -> davranis testleri.
  4. `comms/test_comms.py` genel kapinin disindaydi -> sarmalandi.
     (`drone/test_uctan_uca.py` BILEREK sarmalanmadi: model yukler; genel
      kapiyi GPU isine cevirirdi — o, P4 runbook'unda manuel maddedir.)
"""
import math
import re
import socket
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

KOK = Path(__file__).resolve().parents[1]
# T220 / K10 #2: eskiden ciplak `O:/navitas-local-train/venv/Scripts/python.exe`
# idi — Jetson'da 10 test `FileNotFoundError` ile dusuyordu. Suit uretim
# yorumlayicisiyla kosar (madde 13); alt surecler AYNI yorumlayiciyi kullanir.
VENV = sys.executable
SIM = KOK / "simulation" / "scripts"
for _y in (SIM,):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

import iha_flight  # noqa: E402


class YksMonitorKilidi(unittest.TestCase):
    """D-392: emekli hakem monitörü bilerek olmadan KOSMAZ."""

    def test_bayraksiz_kosum_exit2_ve_uyari(self):
        s = subprocess.run(
            [VENV, str(KOK / "comms" / "yks_monitor.py")],
            capture_output=True, text=True, timeout=30,
            encoding="utf-8", errors="replace")
        self.assertEqual(s.returncode, 2,
                         "emekli betik bayraksiz kostu — onay kapisi "
                         "delinebilir (D-392)")
        self.assertIn("EMEKL", s.stderr, "uyari metni yok")
        self.assertIn("--legacy-bilerek", s.stderr)

    def test_import_yolu_bozulmadi(self):
        """test_comms `from yks_monitor import FrameReader` yapar — kilit
        import'u degil KOSUMU engellemeli."""
        s = subprocess.run(
            [VENV, "-c",
             "import sys; sys.path.insert(0, r'%s')\n"
             "from yks_monitor import FrameReader\n"
             "print('ok')" % str(KOK / "comms")],
            capture_output=True, text=True, timeout=30)
        self.assertEqual(s.returncode, 0, s.stderr)
        self.assertIn("ok", s.stdout)


class SimBetikleriDuman(unittest.TestCase):
    """7 kapisiz betige duman kapisi: --help exit 0 (agir is yapmadan)."""

    BETIKLER = ("world_generator", "drive_ika", "mission_demo",
                "mission_time", "harita_onizleme", "iha_perceive_all",
                "iha_detect_send")

    def test_yedi_betik_help_exit0(self):
        for ad in self.BETIKLER:
            with self.subTest(betik=ad):
                s = subprocess.run(
                    [VENV, str(SIM / f"{ad}.py"), "--help"],
                    capture_output=True, timeout=60)
                self.assertEqual(
                    s.returncode, 0,
                    f"{ad} --help exit {s.returncode}: "
                    f"{s.stderr.decode('utf-8', 'replace')[:200]}")


class IhaFlightDavranisi(unittest.TestCase):
    """iha_flight.fly ilk kez KENDI davranisiyla siniyor (onceden hep mock)."""

    def _ucur(self, **kw):
        pozlar = []

        def sahte_set_pose(x, y, z, yaw_rad=0.0):
            pozlar.append((x, y, z, yaw_rad))
            return True

        with mock.patch.object(iha_flight, "set_pose",
                               side_effect=sahte_set_pose), \
             mock.patch.object(iha_flight.time, "sleep"):
            sonuc = iha_flight.fly(fps=5.0, speed_mult=50.0, verbose=False,
                                   **kw)
        return sonuc, pozlar

    def test_faz_sirasi_ve_inis(self):
        sonuc, pozlar = self._ucur()
        self.assertTrue(sonuc)
        self.assertGreater(len(pozlar), len(iha_flight.FLIGHT_PATH),
                           "ara adimlar uretilmedi")
        # Baslangic rampada, bitis inis noktasinda ve YERDE (z=0)
        self.assertEqual(pozlar[0][:3], (-105.0, 0.0, 1.5))
        self.assertEqual(pozlar[-1][:3], (85.0, 0.0, 0.0),
                         "ucus inis noktasinda YERDE bitmedi")
        # Seyir tavani asilmaz
        self.assertLessEqual(max(p[2] for p in pozlar), 20.0 + 1e-9)

    def test_x_ilerleyisi_monoton(self):
        """Ucus geri donmez: x hep ileri (rota duz cizgi dogu yonlu)."""
        _, pozlar = self._ucur()
        xler = [p[0] for p in pozlar]
        self.assertTrue(all(b >= a - 1e-9 for a, b in zip(xler, xler[1:])),
                        "x geriledi — segment gecisleri bozuk")

    def test_pose_hatasi_inisi_ILAN_ETMEZ(self):
        """NEDEN dokstringi: IHA_LANDED ancak son pose KABUL edilirse.

        set_pose RuntimeError verirse fly bunu YUTMAMALI (True donerse
        zincir inis yapilmamisken 'indi' der)."""
        with mock.patch.object(
                iha_flight, "set_pose",
                side_effect=RuntimeError("gz reddetti")), \
             mock.patch.object(iha_flight.time, "sleep"):
            with self.assertRaises(RuntimeError):
                iha_flight.fly(fps=5.0, speed_mult=50.0, verbose=False)

    def test_set_pose_gz_hatasinda_istisna(self):
        tamam = mock.Mock(returncode=0, stderr=b"")
        with mock.patch.object(iha_flight.subprocess, "run",
                               return_value=tamam) as kosum:
            self.assertTrue(iha_flight.set_pose(1.0, 2.0, 3.0, 0.5))
        arg = kosum.call_args.args[0]
        self.assertEqual(arg[:4], ["gz", "topic", "-p", "~/model/modify"])
        self.assertIn("name: 'iha'", arg[5])
        bozuk = mock.Mock(returncode=1, stderr=b"hata")
        with mock.patch.object(iha_flight.subprocess, "run",
                               return_value=bozuk):
            with self.assertRaises(RuntimeError):
                iha_flight.set_pose(1.0, 2.0, 3.0)


class CommsLoopbackSarmalayici(unittest.TestCase):
    """comms/test_comms.py artik genel kapinin ICINDE (D-392).

    Not: drone/test_uctan_uca.py BILEREK disarida — model yukler (GPU);
    genel kapi model yuklemez. O, saha gunu runbook'unda manuel adimdir.
    """

    def test_comms_loopback_gecer(self):
        s = subprocess.run(
            [VENV, str(KOK / "comms" / "test_comms.py")],
            capture_output=True, text=True, timeout=120,
            encoding="utf-8", errors="replace", cwd=str(KOK / "comms"))
        self.assertEqual(s.returncode, 0,
                         f"test_comms dustu:\n{s.stdout[-400:]}\n{s.stderr[-200:]}")
        self.assertIn("TEST GEÇTİ", s.stdout)


class CommsLoopbackUretimPortundanBagimsiz(unittest.TestCase):
    """T209 / D-427: comms/test_comms.py loopback'i URETIM YKS/IKA portlarina
    bind ETMEZ.

    5 Eylul'de saha PC'sinde `yks_gui --bind 0.0.0.0:5005` acikken tam suit
    uc kez `link.py:34 -> WinError 10013` ile dustu (D-427 tablosu); saha PC'si
    = YKS PC'si oldugundan push kapisi (anayasa §5) YKS kapanana dek kilitli
    kaliyordu. Cozum: ephemeral bind + `getsockname()`; sabit port yalniz
    sozlesme belgesine aittir.

    Port sayilari burada CIPLAK yazilmaz (madde 16): uretim argparse
    varsayilanlarindan okunur (`comms/yks_gui.py` ve `comms/ika_receiver.py`
    `--bind`). Uretim portu degisirse tutucu da onu izler.
    """
    TEST_COMMS = KOK / "comms" / "test_comms.py"
    URETIM_KAYNAK = {"yks": "yks_gui.py", "ika": "ika_receiver.py"}

    @classmethod
    def _uretim_portlari(cls):
        portlar = {}
        for ad, dosya in cls.URETIM_KAYNAK.items():
            src = (KOK / "comms" / dosya).read_text(encoding="utf-8")
            m = re.search(r'"--bind",\s*default="0\.0\.0\.0:(\d+)"', src)
            assert m, f"{dosya}: `--bind` varsayilani bulunamadi; uretim portu okunamadi"
            portlar[ad] = int(m.group(1))
        return portlar

    @staticmethod
    def _tutucu_ac(port):
        """Portu canli YKS gibi tutar: SO_REUSEADDR YOK, Windows'ta
        SO_EXCLUSIVEADDRUSE (link.py `reuse=False` yolu, D-405). Port zaten
        baska surecte (gercek YKS/IKA) tutuluyorsa tutucu acilmaz — on kosul
        ("port dolu") zaten saglanmistir; None doner."""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            s.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        try:
            s.bind(("127.0.0.1", port))
        except OSError:
            s.close()
            return None
        return s

    def test_uretim_portlari_tutuluyorken_test_comms_gecer(self):
        """(a) 5005 VE 5006'yi tutan iki sahte soket ACIKKEN test_comms cikis 0."""
        portlar = self._uretim_portlari()
        tutan = {}
        for ad, port in portlar.items():
            t = self._tutucu_ac(port)
            if t is not None:
                self.addCleanup(t.close)
                self.assertEqual(t.getsockname()[1], port)
            tutan[ad] = "bu test" if t is not None else "baska surec (gercek YKS/IKA?)"
        s = subprocess.run(
            [VENV, str(self.TEST_COMMS)],
            capture_output=True, text=True, timeout=120,
            encoding="utf-8", errors="replace", cwd=str(KOK / "comms"))
        self.assertEqual(
            s.returncode, 0,
            f"uretim portlari {portlar} tutuluyorken ({tutan}) test_comms dustu "
            f"— D-427 geri geldi:\n{s.stdout[-400:]}\n{s.stderr[-400:]}")
        self.assertIn("TEST GEÇTİ", s.stdout)

    def test_kaynakta_sabit_uretim_portu_yok(self):
        """(b) Vakumluluk: ustteki test yesilken kaynak hala sabit porta bind
        ediyor olamaz — `("127.0.0.1", 5005)` / `("127.0.0.1", 5006)` sabitleri
        test_comms.py metninde YOK; yorum disi kodda port sayisi hic gecmez."""
        src = self.TEST_COMMS.read_text(encoding="utf-8")
        kod = "\n".join(satir.split("#", 1)[0] for satir in src.splitlines())
        for ad, port in self._uretim_portlari().items():
            sabit = f'("127.0.0.1", {port})'
            # assertNotIn degil: dusunce tum kaynak metni mesaja dokuluyor.
            self.assertFalse(sabit in src,
                             f"test_comms.py hala {ad} uretim portuna sabit bagli: {sabit}")
            self.assertIsNone(re.search(rf"\b{port}\b", kod),
                              f"test_comms.py yorum disi kodunda {ad} uretim portu ({port}) geciyor")


if __name__ == "__main__":
    unittest.main()
