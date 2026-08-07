"""NEDEN: İHA göndericisi hedef adres olmadan başarı izlenimi veya ham socket
traceback'i üretmemeli; argparse anlaşılır hata ve exit 2 ile durmalıdır.
"""

import subprocess
import sys
import unittest
from pathlib import Path


KOK = Path(__file__).resolve().parents[1]
GONDERICI = KOK / "comms" / "iha_sender.py"


class IhaSenderCliTests(unittest.TestCase):
    def _kos(self, *args):
        return subprocess.run(
            [sys.executable, "-B", str(GONDERICI), *args],
            cwd=str(GONDERICI.parent),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=False,
        )

    def test_no_route_hedefsiz_argparse_exit_2(self):
        sonuc = self._kos("--no-route", "KAPALI_DAR", "--detay", "test")

        self.assertEqual(2, sonuc.returncode)
        self.assertIn(
            "--serial, --ika veya --yks hedeflerinden biri gerekli",
            sonuc.stderr,
        )
        self.assertNotIn("Traceback", sonuc.stderr)
        self.assertNotIn("ROTA YOK gönderiliyor", sonuc.stdout)
        print("[T11_KAPI] exit=2 argparse=VAR traceback=YOK gonderim_mesaji=YOK")

    def test_open_route_hedefsiz_ayni_argparse_kapisinda_durur(self):
        sonuc = self._kos("--road", "2")

        self.assertEqual(2, sonuc.returncode)
        self.assertIn(
            "--serial, --ika veya --yks hedeflerinden biri gerekli",
            sonuc.stderr,
        )
        self.assertNotIn("Traceback", sonuc.stderr)


if __name__ == "__main__":
    unittest.main()
