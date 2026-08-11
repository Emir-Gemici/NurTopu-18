"""NEDEN: Saha IHA_LANDED latch'i tek, eski veya bozuk bir MAVLink
mesajiyla acilirsa IKA inis tamamlanmadan surus izni alabilir. Durum makinesinin
yalniz ardışık Pixhawk yerde + düşük irtifa çiftlerini kabul ettiğini kanıtlar.
"""

from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


KOK = Path(__file__).resolve().parents[1]
COMMS = KOK / "comms"
if str(COMMS) not in sys.path:
    sys.path.insert(0, str(COMMS))

import inis_kaniti as kanit  # noqa: E402


class Mesaj:
    def __init__(self, tip, sysid=1, **alanlar):
        self._tip = tip
        self._sysid = sysid
        for ad, deger in alanlar.items():
            setattr(self, ad, deger)

    def get_type(self):
        return self._tip

    def get_srcSystem(self):
        return self._sysid


class SahteMav:
    def __init__(self, mesajlar, deadline=None):
        self.mesajlar = list(mesajlar)
        self.cagrilar = []
        self.inis_kaniti_deadline_monotonic = (
            time.monotonic() + 60.0 if deadline is None else deadline)

    def recv_match(self, **kwargs):
        self.cagrilar.append(kwargs)
        if not self.mesajlar:
            return None
        siradaki = self.mesajlar.pop(0)
        if isinstance(siradaki, BaseException):
            raise siradaki
        return siradaki


def _e(durum=1, sysid=1):
    return Mesaj(kanit.MESAJ_EXTENDED_SYS_STATE, sysid=sysid,
                 landed_state=durum)


def _p(relative_alt, sysid=1):
    return Mesaj(kanit.MESAJ_GLOBAL_POSITION_INT,
                 sysid=sysid,
                 relative_alt=relative_alt)


class InisKanitiTests(unittest.TestCase):
    def setUp(self):
        mavlink = SimpleNamespace(MAV_LANDED_STATE_ON_GROUND=1)
        self.mavutil = SimpleNamespace(mavlink=mavlink)
        self.yama = mock.patch.object(
            kanit, "_mavutil_al", return_value=self.mavutil)
        self.yama.start()

    def tearDown(self):
        self.yama.stop()

    def test_uc_taze_yerde_ve_dusuk_irtifa_cifti_gecer(self):
        mav = SahteMav([_e(), _p(999), _e(), _p(0), _e(), _p(500)])
        self.assertTrue(kanit.yerde_mi(mav))
        self.assertTrue(all(
            cagri["type"] == [kanit.MESAJ_EXTENDED_SYS_STATE,
                              kanit.MESAJ_GLOBAL_POSITION_INT]
            and cagri["blocking"] is True
            and cagri["timeout"] > 0
            for cagri in mav.cagrilar))

    def test_tavan_esitligi_fail_closed(self):
        self.assertFalse(kanit.yerde_mi(SahteMav([_e(), _p(1000)]), ardisik=1))

    def test_irtifa_beklerken_in_air_mesaji_yutulmaz(self):
        mav = SahteMav([
            _e(), _e(2), _p(100),
            _e(), _p(100), _e(), _p(100), _e(), _p(100),
        ])
        self.assertFalse(kanit.yerde_mi(mav))

    def test_tek_yerde_mesaji_uc_irtifayi_kanit_saymaz(self):
        self.assertFalse(kanit.yerde_mi(
            SahteMav([_e(), _p(100), _p(100), _p(100)])))

    def test_farkli_sysid_durum_ve_irtifa_eslenmez(self):
        self.assertFalse(kanit.yerde_mi(
            SahteMav([_e(sysid=1), _p(100, sysid=2)]), ardisik=1))

    def test_butun_ornekler_ayni_sysid_olmalidir(self):
        self.assertFalse(kanit.yerde_mi(SahteMav([
            _e(sysid=1), _p(100, sysid=1),
            _e(sysid=2), _p(100, sysid=2),
        ]), ardisik=2))

    def test_yuksek_irtifa_ve_okuma_hatalari_false(self):
        vakalar = [
            [_e(), _p(1001)],
            [None],
            [OSError("baglanti koptu")],
            [Mesaj(kanit.MESAJ_EXTENDED_SYS_STATE)],
            [_e(), Mesaj(kanit.MESAJ_GLOBAL_POSITION_INT)],
            [_e(), _p(True)],
            [Mesaj("UNKNOWN")],
        ]
        for mesajlar in vakalar:
            with self.subTest(mesajlar=mesajlar):
                self.assertFalse(kanit.yerde_mi(SahteMav(mesajlar), ardisik=1))

    def test_gecersiz_parametreler_false(self):
        for ardisik, tavan in ((0, 1.0), (True, 1.0), (1, 0.0),
                               (1, float("nan")), (1, True)):
            with self.subTest(ardisik=ardisik, tavan=tavan):
                self.assertFalse(kanit.yerde_mi(
                    SahteMav([]), ardisik=ardisik, tavan_m=tavan))

    def test_deadline_yok_gecmis_ve_sonlu_degilse_okuma_yapmaz(self):
        mav_yok = SahteMav([_e(), _p(100)])
        del mav_yok.inis_kaniti_deadline_monotonic
        vakalar = [
            mav_yok,
            SahteMav([_e(), _p(100)], deadline=time.monotonic() - 1.0),
            SahteMav([_e(), _p(100)], deadline=float("nan")),
            SahteMav([_e(), _p(100)], deadline=float("inf")),
        ]
        for mav in vakalar:
            with self.subTest(deadline=getattr(
                    mav, "inis_kaniti_deadline_monotonic", None)):
                self.assertFalse(kanit.yerde_mi(mav, ardisik=1))
                self.assertEqual([], mav.cagrilar)

    def test_yalniz_gps_akisi_mutlak_deadline_i_uzatmaz(self):
        class YalnizGpsMav:
            inis_kaniti_deadline_monotonic = 2.0

            def __init__(self):
                self.timeoutlar = []

            def recv_match(self, **kwargs):
                self.timeoutlar.append(kwargs["timeout"])
                return _p(100)

        mav = YalnizGpsMav()
        with mock.patch.object(
                kanit.time, "monotonic",
                side_effect=[0.0, 0.5, 1.5, 2.0]):
            self.assertFalse(kanit.yerde_mi(mav, ardisik=1))
        self.assertEqual([2.0, 0.5], mav.timeoutlar)


class PymavlinkBagimliligiTests(unittest.TestCase):
    def test_eksik_pymavlink_acik_import_hatasi_verir(self):
        with mock.patch.object(
                kanit.importlib, "import_module",
                side_effect=ModuleNotFoundError("pymavlink")):
            with self.assertRaisesRegex(ImportError, "pymavlink gerekli"):
                kanit._mavutil_al()


if __name__ == "__main__":
    unittest.main()
