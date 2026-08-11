"""NEDEN: Kuru koşu yalnız üç dosya adı ve birkaç AST sembolü görerek halka
8'i geçirebilir. Jetson paketinin gerçek yayıncı bağımlılıklarını taşıdığını,
kanonik kaynaklardan ayrışmadığını ve izole dizinden import edildiğini kanıtlar.
"""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


KOK = Path(__file__).resolve().parents[1]
PAKET = KOK / "jetson_paket" / "kod"
KOPYALAR = {
    KOK / "codes" / "karar_sozlesmesi.py": PAKET / "karar_sozlesmesi.py",
    # KARAR MOTORU DA AYNALANIR (T31 · REVIEW_LOG D-41 yan bulgusu).
    # Bu iki satir yoktu ve `jetson_paket/kod/rpi_inference.py` 456 satir
    # BAYAT kaldi: T24 (kenar guvenligi), T28 (ret sebepleri), T30 (witness
    # yolu) ve T31/T32 hicbiri sahaya giden kopyada yoktu. Yani Jetson,
    # kapatilmis KRITIK kusurlarla ucacakti. D-01'in ("T4 duzeltmesi IKIZ
    # dosyada yapilmadi") tekrari; kapiyi dosya listesine bagliyoruz.
    KOK / "codes" / "rpi_inference.py": PAKET / "rpi_inference.py",
    KOK / "codes" / "costmap_path_finder.py": PAKET / "costmap_path_finder.py",
    KOK / "comms" / "protocol.py": PAKET / "protocol.py",
    KOK / "comms" / "link.py": PAKET / "link.py",
    KOK / "comms" / "iha_sender.py": PAKET / "iha_sender.py",
    KOK / "comms" / "inis_kaniti.py": PAKET / "inis_kaniti.py",
    KOK / "comms" / "iha_inis_yayinci.py": PAKET / "iha_inis_yayinci.py",
}


class JetsonCommsPaketiTests(unittest.TestCase):
    def test_paket_kopyalari_kanonik_kaynaklarla_birebir(self):
        for kaynak, hedef in KOPYALAR.items():
            with self.subTest(hedef=hedef.name):
                self.assertTrue(hedef.is_file(), f"paket dosyasi yok: {hedef}")
                self.assertEqual(kaynak.read_bytes(), hedef.read_bytes(),
                                 f"paket kopyasi bayat: {hedef.name}")

    def test_pymavlink_ve_pyserial_paket_bagimliligi(self):
        satirlar = {
            satir.strip().lower()
            for satir in (PAKET / "requirements_rpi.txt").read_text(
                encoding="utf-8").splitlines()
            if satir.strip() and not satir.lstrip().startswith("#")
        }
        self.assertIn("pyserial", satirlar)
        self.assertIn("pymavlink", satirlar)

    def test_uretim_yayincisi_pymavlink_olmadan_izole_import_edilir(self):
        kod = (
            "import pathlib,sys; "
            f"p=pathlib.Path({str(PAKET)!r}).resolve(); "
            "sys.path[:]=[str(p)]+[x for x in sys.path if x not in ('',str(p))]; "
            "import iha_inis_yayinci as y; "
            "assert pathlib.Path(y.__file__).resolve().parent == p; "
            "assert callable(y.iha_inisini_yayinla); "
            "print('JETSON_COMMS_IMPORT=OK')"
        )
        sonuc = subprocess.run(
            [sys.executable, "-B", "-c", kod], cwd=PAKET,
            capture_output=True, text=True, timeout=15)
        self.assertEqual(0, sonuc.returncode,
                         f"stdout={sonuc.stdout}\nstderr={sonuc.stderr}")
        self.assertIn("JETSON_COMMS_IMPORT=OK", sonuc.stdout)


if __name__ == "__main__":
    unittest.main()
