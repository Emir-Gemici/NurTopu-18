"""ONARIM-04: kare keskinligi olcusu, bantlari ve gorev kaydina islenmesi.

Kilitler: dokulu kare NET, ayni kare sigma 10 bulanik BULANIK; olcu cozunurlukten
(yaklasik) bagimsiz; on kayitli esikler; gorev kaydi KARE satirinda `keskinlik`;
odak olcer dosya kipinde cikis kodlari.
"""
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

KOK = Path(__file__).resolve().parents[1]
for _p in (KOK / "codes", KOK / "comms", KOK / "scripts", KOK / "tests"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import kare_keskinligi as kk  # noqa: E402


def _dokulu(h=720, w=1280, tohum=7):
    rng = np.random.default_rng(tohum)
    kucuk = rng.integers(0, 256, (h // 8, w // 8, 3), dtype=np.uint8)
    return cv2.resize(kucuk, (w, h), interpolation=cv2.INTER_NEAREST)


class Keskinlik(unittest.TestCase):
    def test_on_kayitli_esikler(self):
        self.assertEqual((kk.KESKINLIK_NET_ESIK, kk.KESKINLIK_BULANIK_ESIK, kk.KESKINLIK_OLCEK_PX),
                         (100.0, 20.0, 640))

    def test_net_ve_bulanik_ayrisir(self):
        net = _dokulu()
        bulanik = cv2.GaussianBlur(net, (0, 0), 10)
        self.assertEqual(kk.keskinlik_bandi(kk.kare_keskinligi(net)), kk.KESKIN_NET)
        self.assertEqual(kk.keskinlik_bandi(kk.kare_keskinligi(bulanik)), kk.KESKIN_BULANIK)
        self.assertGreater(kk.kare_keskinligi(net), 50 * kk.kare_keskinligi(bulanik))

    def test_cozunurluk_bagimsiz_yaklasik(self):
        net = _dokulu()
        buyuk = cv2.resize(net, (1920, 1080), interpolation=cv2.INTER_LINEAR)
        a, b = kk.kare_keskinligi(net), kk.kare_keskinligi(buyuk)
        self.assertLess(abs(a - b) / a, 0.35, (a, b))

    def test_bant_sinirlari(self):
        self.assertEqual(kk.keskinlik_bandi(100.0), kk.KESKIN_NET)
        self.assertEqual(kk.keskinlik_bandi(99.9), kk.KESKIN_SUPHELI)
        self.assertEqual(kk.keskinlik_bandi(20.0), kk.KESKIN_SUPHELI)
        self.assertEqual(kk.keskinlik_bandi(19.9), kk.KESKIN_BULANIK)
        with self.assertRaises(ValueError):
            kk.keskinlik_bandi(float("nan"))
        with self.assertRaises(ValueError):
            kk.kare_keskinligi(np.zeros((0, 0, 3), np.uint8))

    def test_gri_kare_kabul(self):
        g = cv2.cvtColor(_dokulu(), cv2.COLOR_BGR2GRAY)
        self.assertGreater(kk.kare_keskinligi(g), kk.KESKINLIK_NET_ESIK)


class GorevKaydinaIslenir(unittest.TestCase):
    def test_kare_satirinda_keskinlik(self):
        import rpi_inference as ri
        from test_onarim03_gorev_kaydi import _kos, _satirlar
        with tempfile.TemporaryDirectory() as d:
            with contextlib.redirect_stdout(io.StringIO()):
                kayit = ri.gorev_kaydi_ac(Path(d) / "g")
            _kos(2, kayit)
            ri.gorev_kaydi_kapat(kayit)
            kareler = [r for r in _satirlar(kayit.yol) if r["olay"] == "KARE"]
        self.assertEqual(len(kareler), 2)
        for r in kareler:
            self.assertIn("keskinlik", r)
            self.assertIsNotNone(r["keskinlik"])
            self.assertLess(r["keskinlik"], kk.KESKINLIK_BULANIK_ESIK)  # sahte kamera duz gri kare


class OdakOlcerDosyaKipi(unittest.TestCase):
    def test_cikis_kodlari(self):
        import kamera_odak_olcer as oo
        with tempfile.TemporaryDirectory() as d:
            net, bul = Path(d) / "net.png", Path(d) / "bulanik.png"
            cv2.imwrite(str(net), _dokulu())
            cv2.imwrite(str(bul), cv2.GaussianBlur(_dokulu(), (0, 0), 10))
            with contextlib.redirect_stdout(io.StringIO()) as c:
                self.assertEqual(oo.main(["--dosya", str(net)]), oo.CIKIS_NET)
                self.assertEqual(oo.main(["--dosya", str(net), str(bul)]), oo.CIKIS_DEGIL)
                self.assertEqual(oo.main(["--dosya", str(Path(d) / "yok.png")]), oo.CIKIS_OLCULEMEDI)
            self.assertIn("BULANIK", c.getvalue())


if __name__ == "__main__":
    unittest.main()
