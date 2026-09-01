"""NEDEN: Saha IHA_LANDED latch'i tek, eski veya bozuk bir MAVLink
mesajiyla acilirsa IKA inis tamamlanmadan surus izni alabilir. Durum makinesinin
yalniz ardışık Pixhawk yerde + düşük irtifa çiftlerini kabul ettiğini kanıtlar.
"""

from __future__ import annotations

import sys
import threading
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


def _p(relative_alt, sysid=1, time_boot_ms=1000):
    return Mesaj(kanit.MESAJ_GLOBAL_POSITION_INT,
                 sysid=sysid,
                 relative_alt=relative_alt,
                 time_boot_ms=time_boot_ms)


class SahteSaat:
    def __init__(self, simdi=0.0):
        self.simdi = simdi

    def __call__(self):
        return self.simdi


class CanliAkis:
    def __init__(self, mesajlar=(), target_system=1):
        self.mesajlar = list(mesajlar)
        self.cagrilar = []
        self.target_system = target_system

    def recv_match(self, **kwargs):
        self.cagrilar.append(kwargs)
        if not self.mesajlar:
            return None
        siradaki = self.mesajlar.pop(0)
        if isinstance(siradaki, BaseException):
            raise siradaki
        return siradaki


class BagilIrtifaOkuyucuTests(unittest.TestCase):
    def test_taze_telemetri_metre_doner_ve_nonblocking_okunur(self):
        saat = SahteSaat(10.0)
        mav = CanliAkis([_p(30_250, sysid=7, time_boot_ms=123)],
                        target_system=7)
        okuyucu = kanit.BagilIrtifaOkuyucu(mav, 1.0, monotonic=saat)

        self.assertEqual(30.25, okuyucu.oku())
        self.assertTrue(all(cagri == {
            "type": kanit.MESAJ_GLOBAL_POSITION_INT,
            "blocking": False,
        } for cagri in mav.cagrilar))

    def test_tazelik_esiginde_eski_deger_donmez(self):
        saat = SahteSaat(10.0)
        mav = CanliAkis([_p(30_000, time_boot_ms=1)])
        okuyucu = kanit.BagilIrtifaOkuyucu(
            mav, 0.5, beklenen_sysid=1, monotonic=saat)
        self.assertEqual(30.0, okuyucu.oku())

        saat.simdi = 10.5
        self.assertIsNone(okuyucu.irtifa_m())
        saat.simdi = 10.6
        self.assertIsNone(okuyucu.irtifa_m())

    def test_duplicate_ve_sira_disi_paket_yasi_yenilemez(self):
        saat = SahteSaat(1.0)
        mav = CanliAkis([_p(30_000, time_boot_ms=100)])
        okuyucu = kanit.BagilIrtifaOkuyucu(
            mav, 1.0, beklenen_sysid=1, monotonic=saat)
        self.assertEqual(30.0, okuyucu.oku())

        saat.simdi = 1.8
        mav.mesajlar.extend([
            _p(99_000, time_boot_ms=100),
            _p(98_000, time_boot_ms=99),
        ])
        self.assertEqual(30.0, okuyucu.oku())
        saat.simdi = 2.0
        self.assertIsNone(okuyucu.oku())

    def test_yeni_paket_irtifayi_ve_yasi_yeniler(self):
        saat = SahteSaat(1.0)
        mav = CanliAkis([_p(30_000, time_boot_ms=100)])
        okuyucu = kanit.BagilIrtifaOkuyucu(
            mav, 1.0, beklenen_sysid=1, monotonic=saat)
        self.assertEqual(30.0, okuyucu.oku())

        saat.simdi = 1.8
        mav.mesajlar.append(_p(31_500, time_boot_ms=101))
        self.assertEqual(31.5, okuyucu.oku())
        saat.simdi = 2.7
        self.assertEqual(31.5, okuyucu.oku())

    def test_baglanti_target_system_kaynagi_sabitler(self):
        saat = SahteSaat()
        mav = CanliAkis([_p(30_000, sysid=2, time_boot_ms=1)],
                        target_system=1)
        okuyucu = kanit.BagilIrtifaOkuyucu(mav, 1.0, monotonic=saat)
        self.assertIsNone(okuyucu.oku())

    def test_beklenen_sysid_ve_target_system_yoksa_fail_closed(self):
        mav = CanliAkis([_p(30_000, sysid=4, time_boot_ms=1)],
                        target_system=None)
        with self.assertRaisesRegex(ValueError, "beklenen_sysid"):
            kanit.BagilIrtifaOkuyucu(mav, 1.0)
        self.assertEqual([], mav.cagrilar)

    def test_irtifa_snapshot_okumasi_kuyrugu_tuketmez(self):
        saat = SahteSaat()
        mav = CanliAkis([_p(30_000, time_boot_ms=1)])
        okuyucu = kanit.BagilIrtifaOkuyucu(mav, 1.0, monotonic=saat)
        self.assertIsNone(okuyucu.irtifa_m())
        self.assertEqual([], mav.cagrilar)
        self.assertEqual(30.0, okuyucu.oku())

    def test_poller_recv_aninda_damgalar_sonradan_sorgu_tazelemez(self):
        saat = SahteSaat(0.0)
        mav = CanliAkis([_p(30_000, time_boot_ms=1)])
        okuyucu = kanit.BagilIrtifaOkuyucu(
            mav, 0.5, monotonic=saat)
        self.assertTrue(okuyucu.baslat())
        try:
            gercek_deadline = time.monotonic() + 1.0
            while okuyucu.irtifa_m() is None:
                if time.monotonic() >= gercek_deadline:
                    self.fail("poller telemetriyi işlemedi")
                threading.Event().wait(0.001)
            saat.simdi = 0.5
            self.assertIsNone(okuyucu.irtifa_m())
        finally:
            self.assertTrue(okuyucu.durdur())

    def test_durdurulan_okuyucu_taze_snapshot_i_bile_kullanmaz(self):
        saat = SahteSaat(0.0)
        mav = CanliAkis([_p(30_000, time_boot_ms=1)])
        okuyucu = kanit.BagilIrtifaOkuyucu(
            mav, 0.5, beklenen_sysid=1, monotonic=saat)
        self.assertEqual(30.0, okuyucu.oku())

        self.assertTrue(okuyucu.durdur())
        self.assertIsNone(okuyucu.irtifa_m())

    def test_ayni_mav_ikinci_okuyucu_ve_yerde_mi_tuketimini_reddeder(self):
        mav = CanliAkis()
        birinci = kanit.BagilIrtifaOkuyucu(mav, 0.1)
        ikinci = kanit.BagilIrtifaOkuyucu(mav, 0.1)
        self.assertTrue(birinci.baslat())
        try:
            self.assertFalse(ikinci.baslat())
            with mock.patch.object(kanit, "_yerde_mi_sahipli") as asil:
                self.assertFalse(kanit.yerde_mi(mav))
                asil.assert_not_called()
        finally:
            self.assertTrue(birinci.durdur())
        self.assertTrue(ikinci.baslat())
        self.assertTrue(ikinci.durdur())

    def test_gecersiz_mesaj_ve_okuma_hatasi_cache_i_gecersiz_kilar(self):
        # D-389: BEKLENEN kaynaktan bozuk alan cache'i siler (korundu).
        # Kaynagi okunamayan/yabanci paket ise artik AYRI sozlesmede:
        # asagida `test_yabanci_veya_adsiz_kaynak_cache_e_dokunmaz`.
        bozuklar = [
            _p(0, time_boot_ms=2),
            _p(True, time_boot_ms=2),
            _p(float("nan"), time_boot_ms=2),
            Mesaj(kanit.MESAJ_GLOBAL_POSITION_INT, sysid=1,
                  relative_alt=30_000),
            _p(30_000, time_boot_ms=True),
            Mesaj("UNKNOWN", sysid=1),
            OSError("baglanti koptu"),
        ]
        for bozuk in bozuklar:
            with self.subTest(bozuk=bozuk):
                saat = SahteSaat()
                mav = CanliAkis([_p(30_000, time_boot_ms=1)])
                okuyucu = kanit.BagilIrtifaOkuyucu(
                    mav, 1.0, beklenen_sysid=1, monotonic=saat)
                self.assertEqual(30.0, okuyucu.oku())
                mav.mesajlar.append(bozuk)
                self.assertIsNone(okuyucu.oku())
                self.assertIsNone(okuyucu.oku())

    def test_yabanci_veya_adsiz_kaynak_cache_e_dokunmaz(self):
        """D-389 (B1): yabanci/adsiz paket KANIT DEGILDIR — atlanir.

        Eski davranis (gecersiz kil) ucuncu bir tarafa bizi kor etme
        yetkisi veriyordu: D-387'de olculdu, yabanci trafik altinda
        erisilebilirlik 0/193. Sizinti kapisi ayri testte durur:
        yabancinin DEGERI hicbir zaman donmez.
        """
        yabancilar = [
            _p(130_000, sysid=99, time_boot_ms=2),   # yabanci arac
            _p(130_000, sysid=True, time_boot_ms=2),  # adsiz/bozuk kimlik
            _p(130_000, sysid=0, time_boot_ms=2),     # rezerv kimlik
        ]
        for yabanci in yabancilar:
            with self.subTest(yabanci=yabanci):
                saat = SahteSaat()
                mav = CanliAkis([_p(30_000, time_boot_ms=1)])
                okuyucu = kanit.BagilIrtifaOkuyucu(
                    mav, 1.0, beklenen_sysid=1, monotonic=saat)
                self.assertEqual(30.0, okuyucu.oku())
                mav.mesajlar.append(yabanci)
                # Yabanci paket ne DEGER getirir ne cache SILER:
                self.assertEqual(30.0, okuyucu.oku(),
                                 "yabanci paket cache'i sildi (D-389 B1) "
                                 "ya da yabanci deger sizdi")

    def test_gecersiz_kurucu_parametreleri_reddedilir(self):
        for tazelik in (True, 0, -1, float("nan"), float("inf"), "1"):
            with self.subTest(tazelik=tazelik):
                with self.assertRaises(ValueError):
                    kanit.BagilIrtifaOkuyucu(CanliAkis(), tazelik)
        for sysid in (True, 0, -1, 256, 1.0, "1"):
            with self.subTest(sysid=sysid):
                with self.assertRaises(ValueError):
                    kanit.BagilIrtifaOkuyucu(
                        CanliAkis(), 1.0, beklenen_sysid=sysid)
        for hedef in (None, 0, True, -1, 256, 1.0, "1"):
            with self.subTest(target_system=hedef):
                with self.assertRaises(ValueError):
                    kanit.BagilIrtifaOkuyucu(
                        CanliAkis(target_system=hedef), 1.0)


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
        # D-389 (A2): IN_AIR artik terminal DEGIL — ilerlemeyi sifirlar.
        # Korunan ozellik AYNI: IN_AIR'in yarim biraktigi cift SAYILMAZ.
        # IN_AIR'den sonra yalniz IKI temiz cift var -> 3'e ulasilamaz.
        mav = SahteMav([
            _e(), _e(2), _p(100),
            _e(), _p(100), _e(), _p(100),
        ])
        self.assertFalse(kanit.yerde_mi(mav))

    def test_in_air_sonrasi_uc_temiz_cift_kanit_uretir(self):
        """D-389 (A2): alcalmadaki IN_AIR bekleme penceresini oldurmez.

        D-387 BULGU A: eski sozlesmede ilk IN_AIR terminal'di; yayinci tek
        cagri + exit 3 ile IHA_LANDED'i hic yayinlamiyordu (soket birikintisi
        temas SONRASI cagriyi da dusuruyordu). Yeni sozlesme: sayac sifirlanir,
        okuma son tarihe kadar surer; IN_AIR'den sonra UC temiz cift -> True.
        """
        mav = SahteMav([
            _e(), _e(2), _p(100),
            _e(), _p(100), _e(), _p(100), _e(), _p(100),
        ])
        self.assertTrue(kanit.yerde_mi(mav))

    def test_yabanci_extended_kaniti_dusuremez(self):
        """D-389 (B1 kardesi): pine uymayan kaynak atlanir, terminal olmaz."""
        mav = SahteMav([
            _e(sysid=1), _e(2, sysid=99), _p(100, sysid=1),
            _e(sysid=1), _p(100, sysid=1), _e(sysid=1), _p(100, sysid=1),
        ])
        self.assertTrue(kanit.yerde_mi(mav, beklenen_sysid=1),
                        "yabanci EXTENDED inis kanitini dusurdu")

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
