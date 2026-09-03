"""YKİ uçuş telemetrisi tek MAVLink tüketicisinde ve fail-closed kalır."""

import sys
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "comms"))
import inis_kaniti as kanit  # noqa: E402


SYSID = 42
COMPONENT = 1
ARM = 128


class Saat:
    def __init__(self):
        self.deger = 0.0

    def __call__(self):
        return self.deger


class Mesaj:
    def __init__(self, tip, *, sysid=SYSID, component=COMPONENT, **alanlar):
        self.tip = tip
        self.sysid = sysid
        self.component = component
        for ad, deger in alanlar.items():
            setattr(self, ad, deger)

    def get_type(self):
        return self.tip

    def get_srcSystem(self):
        return self.sysid

    def get_srcComponent(self):
        return self.component


class Akis:
    def __init__(self, mesajlar=()):
        self.mesajlar = list(mesajlar)
        self.target_system = SYSID
        self.target_component = COMPONENT

    def recv_match(self, **_kwargs):
        if not self.mesajlar:
            return None
        sonuc = self.mesajlar.pop(0)
        if isinstance(sonuc, BaseException):
            raise sonuc
        return sonuc


def konum(**alanlar):
    taban = dict(time_boot_ms=1, relative_alt=12000, lat=390000000,
                 lon=320000000, vx=300, vy=400, hdg=12345)
    taban.update(alanlar)
    return Mesaj(kanit.MESAJ_GLOBAL_POSITION_INT, **taban)


def hb(**alanlar):
    taban = dict(base_mode=ARM, mode_string="AUTO")
    taban.update(alanlar)
    return Mesaj(kanit.MESAJ_HEARTBEAT, **taban)


def bat(**alanlar):
    taban = dict(voltage_battery=16800)
    taban.update(alanlar)
    return Mesaj(kanit.MESAJ_SYS_STATUS, **taban)


class UcusTelemetrisiTests(unittest.TestCase):
    def setUp(self):
        mavlink = SimpleNamespace(MAV_MODE_FLAG_SAFETY_ARMED=ARM,
                                  MAV_COMP_ID_AUTOPILOT1=COMPONENT)
        self.yama = mock.patch.object(
            kanit, "_mavutil_al", return_value=SimpleNamespace(
                mavlink=mavlink,
                mode_string_v10=lambda mesaj: mesaj.mode_string))
        self.yama.start()

    def tearDown(self):
        self.yama.stop()

    def okuyucu(self, mesajlar, saat):
        return kanit.BagilIrtifaOkuyucu(
            Akis(mesajlar), 0.5, durum_tazelik_s=1.5, monotonic=saat)

    def test_hiz_yon_batarya_mod_armed_ve_canlilik_snapshotta(self):
        saat = Saat()
        okuyucu = self.okuyucu([konum(), bat(), hb()], saat)
        sonuc = okuyucu.telemetri_oku()
        self.assertEqual(5.0, sonuc["hiz"])
        self.assertEqual(123.45, sonuc["yon"])
        self.assertEqual(16.8, sonuc["bat"])
        self.assertEqual("AUTO", sonuc["mod"])
        self.assertTrue(sonuc["armed"])
        self.assertTrue(sonuc["pixhawk_canli"])

    def test_akislar_ayri_tazelikte_ve_bozuk_alan_fail_closed(self):
        saat = Saat()
        okuyucu = self.okuyucu([konum(), bat(), hb()], saat)
        okuyucu.telemetri_oku()
        saat.deger = 0.5
        sonuc = okuyucu.telemetri_snapshot()
        self.assertNotIn("hiz", sonuc)
        self.assertEqual(16.8, sonuc["bat"])
        self.assertEqual("AUTO", sonuc["mod"])
        saat.deger = 1.5
        self.assertEqual({}, okuyucu.telemetri_snapshot())

        saat.deger = 2.0
        okuyucu._mav.mesajlar.extend([
            bat(voltage_battery=kanit.MAVLINK_UINT16_AZAMI),
            hb(mode_string="UNKNOWN"),
            konum(time_boot_ms=2, vx=float("nan"), hdg=65535),
        ])
        sonuc = okuyucu.telemetri_oku()
        self.assertNotIn("bat", sonuc)
        self.assertNotIn("mod", sonuc)
        self.assertNotIn("hiz", sonuc)
        self.assertNotIn("yon", sonuc)
        self.assertTrue(sonuc["pixhawk_canli"])

    def test_yabanci_sysid_ve_component_hicbir_alani_ezmez(self):
        saat = Saat()
        okuyucu = self.okuyucu([konum(), bat(), hb()], saat)
        beklenen = okuyucu.telemetri_oku()
        saat.deger = 0.1
        okuyucu._mav.mesajlar.extend([
            konum(sysid=99, time_boot_ms=2, vx=0, vy=0, hdg=0),
            bat(component=77, voltage_battery=9000),
            hb(component=77, base_mode=0, mode_string="STABILIZE"),
            bat(component=0, voltage_battery=9000),
        ])
        self.assertEqual(beklenen, okuyucu.telemetri_oku())

    def test_baglanti_componenti_ve_acik_parametre_pinlenir(self):
        saat = Saat()
        akis = Akis([hb(component=9)])
        akis.target_component = 9
        okuyucu = kanit.BagilIrtifaOkuyucu(
            akis, 0.5, durum_tazelik_s=1.5, monotonic=saat)
        self.assertTrue(okuyucu.telemetri_oku()["armed"])
        akis2 = Akis([hb(component=8)])
        okuyucu2 = kanit.BagilIrtifaOkuyucu(
            akis2, 0.5, beklenen_component=8,
            durum_tazelik_s=1.5, monotonic=saat)
        self.assertTrue(okuyucu2.telemetri_oku()["armed"])

    def test_poller_recv_hatasindan_sonra_cache_temizleyip_toparlanir(self):
        akis = Akis([OSError("gecici"), hb()])
        okuyucu = kanit.BagilIrtifaOkuyucu(
            akis, 0.1, durum_tazelik_s=1.0)
        self.assertTrue(okuyucu.baslat())
        son = time.monotonic() + 1.0
        while time.monotonic() < son:
            if okuyucu.telemetri_snapshot().get("pixhawk_canli"):
                break
            time.sleep(0.01)
        self.assertTrue(okuyucu.telemetri_snapshot().get("pixhawk_canli"))
        self.assertTrue(okuyucu.durdur())


if __name__ == "__main__":
    unittest.main()
