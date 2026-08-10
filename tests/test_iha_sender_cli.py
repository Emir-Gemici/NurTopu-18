"""NEDEN: İHA göndericisi hedef adres olmadan başarı izlenimi veya ham socket
traceback'i üretmemeli; argparse anlaşılır hata ve exit 2 ile durmalıdır.
"""

import json
import socket
import subprocess
import sys
import threading
import unittest
from pathlib import Path


KOK = Path(__file__).resolve().parents[1]
GONDERICI = KOK / "comms" / "iha_sender.py"
sys.path.insert(0, str(KOK / "codes"))
from karar_sozlesmesi import ROTA_GUVEN_ESIGI

ESIK_ALTI = ROTA_GUVEN_ESIGI - 0.001


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

    def _kos_yks_ile(self, *args):
        """Gercek CLI'yi gecici UDP YKS ile kos; alinan cerceveleri dondur."""
        soket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        soket.bind(("127.0.0.1", 0))
        soket.settimeout(0.05)
        gelen = []
        dur = threading.Event()

        def dinle():
            while not dur.is_set():
                try:
                    veri, adres = soket.recvfrom(65535)
                except socket.timeout:
                    continue
                except OSError:
                    return
                for satir in veri.splitlines():
                    mesaj = json.loads(satir.decode("utf-8"))
                    gelen.append(mesaj)
                    ack = {
                        "v": 1, "type": "ACK", "ref": mesaj["seq"],
                        "node": "yks", "seq": 9001, "ts": 0,
                    }
                    soket.sendto(
                        (json.dumps(ack, separators=(",", ":")) + "\n").encode(),
                        adres,
                    )

        is_parcacigi = threading.Thread(target=dinle, daemon=True)
        is_parcacigi.start()
        try:
            sonuc = self._kos(
                *args, "--yks", f"127.0.0.1:{soket.getsockname()[1]}")
            return sonuc, list(gelen)
        finally:
            dur.set()
            is_parcacigi.join(timeout=1.0)
            soket.close()

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

    def test_cli_normal_dusuk_ve_acik_no_route_yollari(self):
        normal, normal_mesajlar = self._kos_yks_ile(
            "--road", "2", "--conf", str(ROTA_GUVEN_ESIGI))
        self.assertEqual(0, normal.returncode, normal.stderr)
        self.assertEqual({"OPEN_ROUTE"}, {m["type"] for m in normal_mesajlar})
        self.assertIn("Açık yol gönderiliyor", normal.stdout)

        dusuk, dusuk_mesajlar = self._kos_yks_ile(
            "--road", "2", "--conf", str(ESIK_ALTI))
        self.assertEqual(0, dusuk.returncode, dusuk.stderr)
        self.assertEqual({"NO_ROUTE"}, {m["type"] for m in dusuk_mesajlar})
        self.assertEqual("DUSUK_GUVEN", dusuk_mesajlar[0]["sebep"])
        self.assertIn("ROTA YOK gönderiliyor: DUSUK_GUVEN", dusuk.stdout)
        self.assertNotIn("Açık yol gönderiliyor", dusuk.stdout)

        yok, yok_mesajlar = self._kos_yks_ile(
            "--no-route", "KAPALI_DAR", "--detay", "test")
        self.assertEqual(0, yok.returncode, yok.stderr)
        self.assertEqual({"NO_ROUTE"}, {m["type"] for m in yok_mesajlar})
        self.assertEqual("KAPALI_DAR", yok_mesajlar[0]["sebep"])
        self.assertIn("ROTA YOK gönderiliyor: KAPALI_DAR", yok.stdout)


if __name__ == "__main__":
    unittest.main()
