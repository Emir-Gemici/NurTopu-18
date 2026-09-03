"""İHA kritik komutları: kaynak pini, yaş ve oturum tekrar güvenliği."""

import math
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


KOK = Path(__file__).resolve().parents[1]
for _yol in (KOK / "comms", KOK / "codes"):
    if str(_yol) not in sys.path:
        sys.path.insert(0, str(_yol))

import iha_komut_alici as ika  # noqa: E402
from protocol import (ACK_SONUC_KABUL, command, decode,  # noqa: E402
                      oturum_dogrula)


SIMDI = 10_000.0
KAYNAK = ("10.20.30.40", 5005)
OTURUM_A = "oturum_A_1234567890"
OTURUM_B = "oturum_B_1234567890"


class _Link:
    def __init__(self):
        self.gonderilen = []

    def send(self, veri, adr=None):
        self.gonderilen.append((decode(veri), adr))


class _Mav:
    def __init__(self, sonuc="kabul", *, component=1):
        self.sonuc = sonuc
        self.component = component
        self.komutlar = []
        self._bekleyen = []
        self.mav = SimpleNamespace(command_long_send=self._gonder)

    def _gonder(self, _sys, _comp, mav_cmd, *_param):
        self.komutlar.append(mav_cmd)
        self._bekleyen.append(mav_cmd)

    def recv_match(self, type=None, **_kw):
        if type != "COMMAND_ACK" or not self._bekleyen:
            return None
        if self.sonuc == "timeout":
            return None
        mav_cmd = self._bekleyen.pop(0)
        m = ika._mavutil_al().mavlink
        sonuc = (m.MAV_RESULT_ACCEPTED if self.sonuc == "kabul"
                 else m.MAV_RESULT_DENIED)
        return SimpleNamespace(
            command=mav_cmd,
            result=sonuc,
            get_srcSystem=lambda: 1,
            get_srcComponent=lambda: self.component,
        )


def _alici(mav=None, **kw):
    link = _Link()
    alici = ika.IhaKomutAlici(
        link, mav if mav is not None else _Mav(),
        duvar_saati=lambda: SIMDI,
        izinli_kaynak=kw.pop("izinli_kaynak", KAYNAK),
        **kw,
    )
    alici._logla = mock.Mock()
    return alici, link


def _cmd(cmd="ARM", *, seq=7, oturum=OTURUM_A, t=SIMDI):
    mesaj = command(cmd, "iha", seq=seq, oturum=oturum)
    mesaj["t"] = t
    return mesaj


class ProtokolOturumuTests(unittest.TestCase):
    def test_oturumsuz_cagri_alan_eklemez(self):
        self.assertNotIn("oturum", command("ARM", "iha", seq=1))

    def test_gecerli_oturum_degistirilmeden_tasinir(self):
        self.assertEqual(OTURUM_A, oturum_dogrula(OTURUM_A))
        self.assertEqual(OTURUM_A,
                         command("ARM", "iha", oturum=OTURUM_A)["oturum"])

    def test_bozuk_oturumlar_reddedilir(self):
        for kotu in (True, "kisa", "bosluk kabul edilmez", "ğ" * 20,
                     "x" * 65):
            with self.subTest(kotu=kotu), self.assertRaises(ValueError):
                command("ARM", "iha", oturum=kotu)


class KaynakVeZamanTests(unittest.TestCase):
    def test_tam_kaynak_kabul_yanlis_ve_none_red(self):
        for gelen, beklenen in ((KAYNAK, True),
                                ((KAYNAK[0], KAYNAK[1] + 1), False),
                                (("10.20.30.41", KAYNAK[1]), False),
                                (None, False)):
            with self.subTest(gelen=gelen):
                mav = _Mav()
                alici, link = _alici(mav)
                self.assertEqual(beklenen, alici.isle(_cmd(), gelen))
                self.assertEqual(1 if beklenen else 0, len(mav.komutlar))
                self.assertEqual(1 if beklenen else 0, len(link.gonderilen))

    def test_bayat_bool_nan_ve_ileri_zaman_red(self):
        arm_tavan = ika.KOMUT_YAS_TAVANI_S[ika.CMD_ARM]
        kotuler = (SIMDI - arm_tavan - 0.01, True, math.nan, SIMDI + 1.0)
        for t in kotuler:
            with self.subTest(t=t):
                mav = _Mav()
                alici, link = _alici(mav)
                self.assertFalse(alici.isle(_cmd(t=t), KAYNAK))
                self.assertEqual([], mav.komutlar)
                self.assertEqual([], link.gonderilen)
                self.assertEqual(1, alici.sayac["zaman_red"])

    def test_yas_tavani_tekrar_sozlesmesinden_turer(self):
        self.assertEqual(
            ika.ARM_TEKRAR_ARALIGI_S * ika.ARM_TEKRAR_UST_SINIRI,
            ika.KOMUT_YAS_TAVANI_S[ika.CMD_ARM])
        self.assertEqual(ika.KOMUT_YAS_TAVANI_S[ika.CMD_ARM],
                         ika.KOMUT_YAS_TAVANI_S[ika.CMD_DISARM])
        self.assertEqual(
            ika.PARASUT_TEKRAR_ARALIGI_S * ika.PARASUT_TEKRAR_UST_SINIRI,
            ika.KOMUT_YAS_TAVANI_S[ika.CMD_PARACHUTE])


class OturumTekrariTests(unittest.TestCase):
    def test_accepted_duplicate_ack_yineler_eyleyiciyi_yinelemez(self):
        mav = _Mav()
        alici, link = _alici(mav)
        mesaj = _cmd()

        self.assertTrue(alici.isle(mesaj, KAYNAK))
        self.assertTrue(alici.isle(dict(mesaj), KAYNAK))

        self.assertEqual(1, len(mav.komutlar))
        self.assertEqual(2, len(link.gonderilen))
        self.assertTrue(all(m[0]["sonuc"] == ACK_SONUC_KABUL
                            for m in link.gonderilen))
        self.assertEqual(1, alici.sayac["tekrar"])

    def test_timeout_ve_ret_duplicate_gecikmis_eylem_uretmez(self):
        for sonuc in ("timeout", "ret"):
            with self.subTest(sonuc=sonuc):
                mav = _Mav(sonuc)
                alici, link = _alici(mav)
                mesaj = _cmd()
                self.assertFalse(alici.isle(mesaj, KAYNAK))
                self.assertFalse(alici.isle(dict(mesaj), KAYNAK))
                self.assertEqual(1, len(mav.komutlar))
                self.assertEqual([], link.gonderilen)
                self.assertEqual(1, alici.sayac["tekrar"])

    def test_farkli_oturum_ayni_seq_yeni_komuttur(self):
        mav = _Mav()
        alici, link = _alici(mav)
        self.assertTrue(alici.isle(_cmd(oturum=OTURUM_A), KAYNAK))
        self.assertTrue(alici.isle(_cmd(oturum=OTURUM_B), KAYNAK))
        self.assertEqual(2, len(mav.komutlar))
        self.assertEqual(2, len(link.gonderilen))

    def test_yabanci_component_ack_kabul_edilmez(self):
        mav = _Mav(component=2)
        alici, link = _alici(mav, target_component=1)
        self.assertFalse(alici.isle(_cmd(), KAYNAK))
        self.assertEqual(1, len(mav.komutlar))
        self.assertEqual([], link.gonderilen)


if __name__ == "__main__":
    unittest.main()
