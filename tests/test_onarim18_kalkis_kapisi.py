"""NEDEN: Açılışta yerde duran İHA iniş izni üretememeli; iniş süresi
kalkıştan başlamalı ve iki kanıt aynı MAVLink sistemine ait olmalı.
"""
import contextlib
import io
import sys
import unittest
from pathlib import Path
from unittest import mock

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "comms"))
import iha_inis_yayinci as yayinci
from test_faz_b_akis_istegi import KayitMav, MavMesaj, SYSID


class AkisBitti(BaseException):
    """Testin süresiz beklemeyi gözlemledikten sonra kontrollü kesmesi."""


def durum(deger, kaynak=SYSID):
    return MavMesaj(yayinci.MESAJ_EXTENDED_SYS_STATE, kaynak,
                    landed_state=deger)


def yerde(kaynak=SYSID):
    sonuc = []
    for _ in range(3):
        sonuc.extend([durum(1, kaynak), MavMesaj(
            yayinci.MESAJ_GLOBAL_POSITION_INT, kaynak, relative_alt=250)])
    return sonuc


class SaatliMav(KayitMav):
    def __init__(self, olaylar):
        super().__init__()
        self.olaylar_akisi = iter(olaylar)
        self.zaman = 10.0

    def recv_match(self, **kwargs):
        try:
            gecen, mesaj = next(self.olaylar_akisi)
        except StopIteration:
            raise AkisBitti
        self.zaman += gecen
        if isinstance(mesaj, Exception):
            raise mesaj
        return mesaj


class KalkisKapisi(unittest.TestCase):
    def kos(self, mav, sysid=SYSID, sure=900):
        args = ["--mavlink", "mock:pixhawk", "--kanit-timeout", str(sure),
                "--heartbeat-sure", "0", "--ika", "127.0.0.1:5006"]
        if sysid is not None:
            args += ["--sysid", str(sysid)]
        return yayinci.main(args, saat=lambda: mav.zaman)

    @contextlib.contextmanager
    def ortam(self, mav):
        with mock.patch.object(yayinci, "mavlink_baglantisi_ac", return_value=mav), \
             mock.patch.object(yayinci.time, "monotonic", side_effect=lambda: mav.zaman), \
             mock.patch.object(yayinci.time, "sleep"), \
             mock.patch.object(yayinci, "iha_inisini_yayinla", return_value=True) as yayin, \
             contextlib.redirect_stdout(io.StringIO()), \
             contextlib.redirect_stderr(io.StringIO()):
            yield yayin

    def test_yerde_binlerce_saniye_bekler_inis_uretmez_timeout_baslamaz(self):
        mav = SaatliMav([(1000, m) for m in yerde()])
        with self.ortam(mav) as yayin:
            with self.assertRaises(AkisBitti):
                self.kos(mav)
            yayin.assert_not_called()
        self.assertNotIn("inis_kaniti_deadline_monotonic", vars(mav))
        self.assertTrue(mav.kapandi)

    def test_in_air_ve_takeoff_sonrasi_gercek_inis_kaniti_yayinlanir(self):
        for kalkis in (2, 3):
            with self.subTest(kalkis=kalkis):
                mav = SaatliMav([(1000, durum(1)), (1000, durum(kalkis))]
                               + [(0.1, m) for m in yerde()])
                with self.ortam(mav) as yayin:
                    self.assertEqual(0, self.kos(mav))
                    yayin.assert_called_once()
                self.assertEqual(2010 + 900, mav.inis_kaniti_deadline_monotonic)
                self.assertTrue(mav.kapandi)

    def test_yabanci_ve_bozuk_kalkis_yerdeki_araca_izin_vermez(self):
        bozuk = [durum(2, SYSID + 1), durum(True), durum("2"), durum(99),
                 durum(2, 0), durum(2, 256), durum(0), durum(4)]
        mav = SaatliMav([(0.1, m) for m in bozuk + yerde()])
        with self.ortam(mav) as yayin:
            with self.assertRaises(AkisBitti):
                self.kos(mav)
            yayin.assert_not_called()

    def test_beyansiz_ilk_kaynak_kalkis_ve_iniste_ayni_kalir(self):
        mav = SaatliMav([(0.1, durum(1)), (0.1, durum(2, SYSID + 1)),
                        (0.1, durum(2))]
                       + [(0.1, m) for m in yerde(SYSID + 1)])
        with self.ortam(mav) as yayin:
            with self.assertRaises(AkisBitti):
                self.kos(mav, sysid=None)
            yayin.assert_not_called()

    def test_kalkis_sonrasi_timeout_asilirsa_inis_yayinlanmaz(self):
        mav = SaatliMav([(1000, durum(1)), (0.1, durum(2)), (901, durum(1))])
        with self.ortam(mav) as yayin:
            self.assertEqual(3, self.kos(mav))
            yayin.assert_not_called()
        self.assertTrue(mav.kapandi)

    def test_kalkis_beklerken_gecici_okuma_hatasi_toparlanir(self):
        mav = SaatliMav([(1, OSError("geçici")), (1000, durum(1)),
                        (0.1, durum(2))] + [(0.1, m) for m in yerde()])
        with self.ortam(mav) as yayin:
            self.assertEqual(0, self.kos(mav))
            yayin.assert_called_once()

    def test_kalkis_beklerken_akis_istekleri_yenilenir(self):
        mav = SaatliMav([(20, durum(1)) for _ in range(5)])
        with self.ortam(mav):
            with self.assertRaises(AkisBitti):
                self.kos(mav)
        self.assertGreater(len(mav.komutlar), 3)


if __name__ == "__main__":
    unittest.main()
