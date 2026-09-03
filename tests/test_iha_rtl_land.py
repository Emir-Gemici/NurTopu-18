#!/usr/bin/env python3
"""NEDEN: 21 Eylül uçuş testinde güvenli sonlandırma için RTL ve LAND,
ARM/DISARM ile aynı fail-closed kaynak/zaman/oturum ve güçlü Pixhawk ACK
kapısından geçmelidir. Bu testler MAV_CMD eşlemesini ve kapı mutasyonlarını
gerçek pymavlink sabitlerine karşı kilitler.
"""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

KOK = Path(__file__).resolve().parents[1]
for _yol in (KOK / "comms", KOK / "codes"):
    if str(_yol) not in sys.path:
        sys.path.insert(0, str(_yol))

from pymavlink import mavutil  # noqa: E402

import iha_komut_alici as ika  # noqa: E402
from protocol import FrameReader, command  # noqa: E402

SIMDI = 10_000.0
OTURUM = "ucus-oturumu-2109"


class _Link:
    def __init__(self):
        self.gonderilen = []

    def send(self, veri, adr=None):
        self.gonderilen.append((veri, adr))


class _Mav:
    def __init__(self, *, ack_komut=None, ack_sonuc=None):
        self.gonderilen = []
        self.ack_komut = ack_komut
        self.ack_sonuc = ack_sonuc
        self._bekleyen = []
        self.mav = SimpleNamespace(command_long_send=self._gonder)

    def _gonder(self, *alanlar):
        self.gonderilen.append(alanlar)
        self._bekleyen.append(alanlar[2])

    def recv_match(self, type=None, blocking=False, timeout=None):
        if type != "COMMAND_ACK" or not self._bekleyen:
            return None
        beklenen = self._bekleyen.pop(0)
        komut = beklenen if self.ack_komut is None else self.ack_komut
        sonuc = (mavutil.mavlink.MAV_RESULT_ACCEPTED
                 if self.ack_sonuc is None else self.ack_sonuc)
        return SimpleNamespace(
            command=komut,
            result=sonuc,
            get_srcSystem=lambda: ika.VARSAYILAN_HEDEF_SYSID,
            get_srcComponent=lambda: ika.VARSAYILAN_HEDEF_COMPONENT,
        )


def _mesaj(ad, *, seq=1, t=SIMDI, oturum=OTURUM):
    sonuc = command(ad, "iha", seq=seq, oturum=oturum)
    sonuc["t"] = t
    return sonuc


def _alici(mav):
    link = _Link()
    alici = ika.IhaKomutAlici(
        link, mav, saat=lambda: SIMDI, duvar_saati=lambda: SIMDI)
    alici._logla = lambda *_args, **_kwargs: None
    return alici, link


class RtlLandAktarimTestleri(unittest.TestCase):
    def test_rtl_ve_land_dogru_mav_cmd_ve_yedi_bos_parametre(self):
        beklenenler = {
            ika.CMD_RTL: mavutil.mavlink.MAV_CMD_NAV_RETURN_TO_LAUNCH,
            ika.CMD_LAND: mavutil.mavlink.MAV_CMD_NAV_LAND,
        }
        for sira, (ad, mav_cmd) in enumerate(beklenenler.items(), 1):
            with self.subTest(ad=ad):
                mav = _Mav()
                alici, link = _alici(mav)
                self.assertTrue(alici.isle(_mesaj(ad, seq=sira), None))
                self.assertEqual(1, len(mav.gonderilen))
                alanlar = mav.gonderilen[0]
                self.assertEqual(
                    (ika.VARSAYILAN_HEDEF_SYSID,
                     ika.VARSAYILAN_HEDEF_COMPONENT, mav_cmd,
                     ika.MAVLINK_ONAY_ILK_GONDERIM),
                    alanlar[:4])
                self.assertEqual(
                    (ika.MAVLINK_PARAM_KULLANILMIYOR,) * 7,
                    alanlar[4:],
                    "RTL/LAND kullanılmayan param1..param7 sıfır olmalı")
                acklar = list(FrameReader().feed(link.gonderilen[0][0]))
                self.assertEqual(ad, acklar[0].get("ref_cmd"))
                self.assertEqual(ika.ACK_SONUC_KABUL,
                                 acklar[0].get("sonuc"))

    def test_mutasyon_yanlis_mav_cmd_ack_guclu_ack_sayilmaz(self):
        mav = _Mav(ack_komut=mavutil.mavlink.MAV_CMD_NAV_LAND)
        alici, link = _alici(mav)
        self.assertFalse(alici.isle(_mesaj(ika.CMD_RTL), None))
        self.assertEqual([], link.gonderilen)
        self.assertEqual(0, alici.sayac["aktarilan"])

    def test_mutasyon_reddedilen_land_ack_yksye_ack_uretmez(self):
        mav = _Mav(ack_sonuc=mavutil.mavlink.MAV_RESULT_DENIED)
        alici, link = _alici(mav)
        self.assertFalse(alici.isle(_mesaj(ika.CMD_LAND), None))
        self.assertEqual([], link.gonderilen)
        self.assertEqual(0, alici.sayac["aktarilan"])

    def test_mutasyon_bayat_rtl_ve_land_eyleyiciye_ulasmaz(self):
        for ad in (ika.CMD_RTL, ika.CMD_LAND):
            with self.subTest(ad=ad):
                mav = _Mav()
                alici, link = _alici(mav)
                tavan = ika.KOMUT_YAS_TAVANI_S[ad]
                self.assertFalse(alici.isle(
                    _mesaj(ad, t=SIMDI - tavan - 0.001), None))
                self.assertEqual([], mav.gonderilen)
                self.assertEqual([], link.gonderilen)

    def test_oturum_tekrari_ack_yineler_ama_rtl_eyleyicisini_yinelemez(self):
        mav = _Mav()
        alici, link = _alici(mav)
        mesaj = _mesaj(ika.CMD_RTL, seq=17)
        self.assertTrue(alici.isle(mesaj, None))
        self.assertTrue(alici.isle(mesaj, None))
        self.assertEqual(1, len(mav.gonderilen),
                         "aynı oturum+seq+cmd eyleyiciyi yineledi")
        self.assertEqual(2, len(link.gonderilen),
                         "kayıp ilk YKS ACK'i yinelenebilmeliydi")
        self.assertEqual(1, alici.sayac["tekrar"])

    def test_rtl_land_yas_tavani_arm_sozlesmesinden_turer(self):
        beklenen = ika.ARM_TEKRAR_ARALIGI_S * ika.ARM_TEKRAR_UST_SINIRI
        self.assertEqual(beklenen, ika.KOMUT_YAS_TAVANI_S[ika.CMD_RTL])
        self.assertEqual(beklenen, ika.KOMUT_YAS_TAVANI_S[ika.CMD_LAND])


if __name__ == "__main__":
    unittest.main()
