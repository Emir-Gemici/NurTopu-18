"""TEZGAH aracı `scripts/tezgah/sik_ayar.py` — SiK AT komut mantığı.

Gerçek telsiz yok: seri port SAHTE. Sınanan: ATI5 dökümünün çözülmesi, aynı değere
yazmama, farklı değerde doğru AT komutu + kaydet + geri alma satırı, yerel/uzak ayrımı.
"""
import io
import sys
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "scripts" / "tezgah"))
import sik_ayar as sa  # noqa: E402

ATI5 = """ATI5
S0: FORMAT=25
S1: SERIAL_SPEED=57
S2: AIR_SPEED=128
S3: NETID=73
S4: TXPOWER=20
S14: MAX_WINDOW=131
OK
"""


class DokumCozme(unittest.TestCase):
    def test_parametreler_cozulur(self):
        p = sa.dokum_coz(ATI5)
        self.assertEqual(p["MAX_WINDOW"], (14, 131))
        self.assertEqual(p["AIR_SPEED"], (2, 128))
        self.assertEqual(p["NETID"], (3, 73))

    def test_bozuk_satirlar_atlanir(self):
        p = sa.dokum_coz("cop\nS9: BOS=\nOK\nS7: ECC=1\n")
        self.assertEqual(p, {"ECC": (7, 1)})

    def test_bos_metin(self):
        self.assertEqual(sa.dokum_coz(""), {})


class _SahteSeri:
    def __init__(self):
        self.yazilan = []
    def reset_input_buffer(self): pass
    def write(self, b): self.yazilan.append(b.decode().strip())
    def flush(self): pass
    def read(self, n): return b""


class YazmaMantigi(unittest.TestCase):
    def setUp(self):
        self.s = _SahteSeri()
        self.mevcut = sa.dokum_coz(ATI5)
        self.log = []

    def test_ayni_deger_yazilmaz(self):
        ok = sa._yaz_tek(self.s, "MAX_WINDOW", 131, self.mevcut, uzak=False, log=self.log.append)
        self.assertTrue(ok)
        self.assertEqual(self.s.yazilan, [])
        self.assertIn("zaten", " ".join(self.log))

    def test_farkli_deger_dogru_komut(self):
        sa._yaz_tek(self.s, "MAX_WINDOW", 33, self.mevcut, uzak=False, log=self.log.append)
        self.assertIn("ATS14=33", self.s.yazilan)
        self.assertIn("AT&W", self.s.yazilan)

    def test_uzak_RT_oneki(self):
        sa._yaz_tek(self.s, "MAX_WINDOW", 33, self.mevcut, uzak=True, log=self.log.append)
        self.assertIn("RTS14=33", self.s.yazilan)
        self.assertIn("RT&W", self.s.yazilan)

    def test_geri_alma_satiri_eski_degeri_tasir(self):
        sa._yaz_tek(self.s, "MAX_WINDOW", 33, self.mevcut, uzak=False, log=self.log.append)
        geri = [l for l in self.log if "GERI ALMA" in l]
        self.assertTrue(geri)
        self.assertIn("ATS14=131", geri[0])

    def test_olmayan_parametre_yazilmaz(self):
        ok = sa._yaz_tek(self.s, "YOK_BOYLE", 1, self.mevcut, uzak=False, log=self.log.append)
        self.assertFalse(ok)
        self.assertEqual(self.s.yazilan, [])


class KuruKosum(unittest.TestCase):
    def _kos(self, argv):
        tampon = io.StringIO()
        eski = sys.stdout
        sys.stdout = tampon
        try:
            kod = sa.main(argv)
        finally:
            sys.stdout = eski
        return kod, tampon.getvalue()

    def test_kuru_port_acmaz_ve_komutlari_yazar(self):
        kod, cikti = self._kos(["--kuru", "--yaz", "MAX_WINDOW=33", "--uzak-da"])
        self.assertEqual(kod, 0)
        self.assertIn("ATS<no>=33", cikti)
        self.assertIn("RTS<no>=33", cikti)

    def test_uzak_verilmezse_ESLESME_UYARISI(self):
        _, cikti = self._kos(["--kuru", "--yaz", "MAX_WINDOW=33"])
        self.assertIn("ESLESMEZ", cikti)

    def test_yazma_yoksa_uyari_yok(self):
        _, cikti = self._kos(["--kuru"])
        self.assertNotIn("ESLESMEZ", cikti)


if __name__ == "__main__":
    unittest.main()
