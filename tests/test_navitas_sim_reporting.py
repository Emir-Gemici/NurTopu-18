"""NEDEN: Bir simülasyon worker'ı çöktüğünde ana süreç boş sonuç kümesini
başarı sanmamalı; beklenen görevlerin raporu görünür kalmalı ve çıkış 1 olmalıdır.
"""

import contextlib
import io
import sys
import threading
import unittest
from pathlib import Path
from unittest import mock


KOK = Path(__file__).resolve().parents[1]
BETIKLER = KOK / "simulation" / "scripts"
if str(BETIKLER) not in sys.path:
    sys.path.insert(0, str(BETIKLER))

import navitas_sim


class GorevRaporuTests(unittest.TestCase):
    def _main_kos(self, argv, *, iha=True, ika=True):
        stdout = io.StringIO()
        stderr = io.StringIO()
        iha_cagrisi = mock.Mock()
        ika_cagrisi = mock.Mock()
        if isinstance(iha, BaseException):
            iha_cagrisi.side_effect = iha
        elif callable(iha):
            iha_cagrisi.side_effect = iha
        else:
            iha_cagrisi.return_value = iha
        if isinstance(ika, BaseException):
            ika_cagrisi.side_effect = ika
        elif callable(ika):
            ika_cagrisi.side_effect = ika
        else:
            ika_cagrisi.return_value = ika
        with mock.patch.object(sys, "argv", ["navitas_sim.py", *argv]), \
             mock.patch.object(navitas_sim.time, "sleep"), \
             mock.patch.object(navitas_sim, "check_topics", return_value=True), \
             mock.patch.object(navitas_sim.iha_flight, "fly", iha_cagrisi), \
             mock.patch.object(
                 navitas_sim, "iha_inisini_yayinla", return_value=True), \
             mock.patch.object(navitas_sim, "dinamik_ika_gorevi", ika_cagrisi), \
             contextlib.redirect_stdout(stdout), \
             contextlib.redirect_stderr(stderr):
            try:
                kod = navitas_sim.main()
            except SystemExit as exc:
                kod = exc.code
        return kod, stdout.getvalue(), stderr.getvalue()

    def test_ika_thread_istisnasi_exit_1_ve_rapor_uretir(self):
        worker_adlari = []

        def ika_cokusu(*_args, **_kw):
            worker_adlari.append(threading.current_thread().name)
            raise RuntimeError("sentetik İKA çökmesi")

        kod, stdout, _ = self._main_kos(
            ["--ika-only", "--no-wait"],
            ika=ika_cokusu,
        )

        self.assertEqual(1, kod)
        self.assertEqual(["ika-nav"], worker_adlari)
        self.assertIn("GÖREV SONUCU", stdout)
        self.assertIn("İKA görevi: ✗ BAŞARISIZ", stdout)
        self.assertIn("RuntimeError: sentetik İKA çökmesi", stdout)
        for satir in stdout.splitlines():
            if "GÖREV SONUCU" in satir or "İKA görevi:" in satir:
                print(f"[T10_KAPI_OUTPUT] {satir.strip()}")
        print(f"[T10_KAPI] worker={worker_adlari[0]} exception exit=1 rapor=VAR")

    def test_ika_cokerken_iha_basarisi_yanlis_exit_0_uretmez(self):
        kod, stdout, _ = self._main_kos(
            ["--no-wait"],
            iha=True,
            ika=RuntimeError("İKA worker hatası"),
        )

        self.assertEqual(1, kod)
        self.assertIn("İHA uçuşu : ✓ TAMAMLANDI", stdout)
        self.assertIn("İKA görevi: ✗ BAŞARISIZ", stdout)

    def test_beklenen_tek_worker_basariliysa_exit_0(self):
        kod, stdout, _ = self._main_kos(
            ["--iha-only", "--no-wait"],
            iha=True,
        )

        self.assertEqual(0, kod)
        self.assertIn("İHA uçuşu : ✓ TAMAMLANDI", stdout)
        self.assertNotIn("İKA görevi", stdout)

    def test_iki_only_bayragi_bos_gorev_yaratmaz(self):
        kod, _, stderr = self._main_kos(
            ["--iha-only", "--ika-only", "--no-wait"],
        )

        self.assertEqual(2, kod)
        self.assertIn("aynı anda kullanılamaz", stderr)


if __name__ == "__main__":
    unittest.main()
