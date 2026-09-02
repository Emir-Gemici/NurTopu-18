"""NEDEN: Hakem ekranı yalnız gerçekten iletilen ARM, DISARM ve paraşüt
komutları için başarı durumu göstermeli; iletim yokluğu operatör onayı değildir.
"""

import sys
import time
import unittest
from pathlib import Path
from unittest import mock


KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "comms"))

import yks_gui  # noqa: E402
from protocol import decode  # noqa: E402


IHA_ADRESI = ("127.0.0.1", 5006)


class _SahteWidget:
    def __init__(self, **ayarlar):
        self.ayarlar = dict(ayarlar)

    def config(self, **ayarlar):
        self.ayarlar.update(ayarlar)

    def cget(self, ad):
        return self.ayarlar.get(ad)


class YksKomutDurustluguTests(unittest.TestCase):
    def _arayuz(self, arm_acik=False, adres_var=False):
        arayuz = object.__new__(yks_gui.YksArayuz)
        arayuz.arm_acik = arm_acik
        arayuz.arm_durum_zamani = time.monotonic()
        arayuz.arm_bekleyen_komut = None
        arayuz.arm_ack_zamani = None
        arayuz.link = mock.Mock()
        arayuz.son_adr = {"iha": IHA_ADRESI} if adres_var else {}
        arayuz._logla = mock.Mock()
        arayuz.btn_arm = _SahteWidget(
            state="normal",
            text="DISARM (A)" if arm_acik else "ARM (A)",
            bg=yks_gui.KIRMIZI if arm_acik else "#232e3a",
        )
        arayuz.lbl_arm = _SahteWidget(
            text=("SİSTEM: ARM — uçuşa hazır" if arm_acik
                  else "SİSTEM: DISARM — güvenli"),
            fg=yks_gui.SARI if arm_acik else yks_gui.SOLUK,
        )
        arayuz.btn_firlat = _SahteWidget(
            state="normal" if arm_acik else "disabled",
            bg=yks_gui.SARI if arm_acik else "#232e3a",
        )
        arayuz.parasut_teyit = 99.0
        arayuz.btn_parasut = _SahteWidget(
            state="normal", bg=yks_gui.KIRMIZI,
            text="EMİN MİSİN? tekrar bas (3 sn)",
        )
        # P9a (D-393): parasut artik ACK'li tekrarla gider; ayni durustluk
        # sozlesmesi AckliTekrar.baslat -> _ham_gonder uzerinden korunur.
        arayuz.parasut_tekrar = yks_gui.AckliTekrar(
            arayuz._ham_gonder, yks_gui.PARASUT_TEKRAR_ARALIGI_S,
            yks_gui.PARASUT_TEKRAR_UST_SINIRI)
        arayuz.parasut_ack_zamani = None
        arayuz.kok = mock.Mock()
        arayuz.arm_tekrar = yks_gui.AckliTekrar(
            arayuz._ham_gonder, yks_gui.ARM_TEKRAR_ARALIGI_S,
            yks_gui.ARM_TEKRAR_UST_SINIRI)
        arayuz._ceza_ekle = mock.Mock()
        arayuz._ucus = mock.Mock()
        return arayuz

    def _komut_dogrula(self, arayuz, beklenen_komut):
        arayuz.link.send.assert_called_once()
        veri, hedef = arayuz.link.send.call_args.args
        mesaj = decode(veri)
        self.assertEqual("CMD", mesaj["type"])
        self.assertEqual(beklenen_komut, mesaj["cmd"])
        self.assertEqual("iha", mesaj["hedef"])
        self.assertEqual(IHA_ADRESI, hedef)

    def _kirmizi_hata_dogrula(self, arayuz, komut):
        arayuz.link.send.assert_not_called()
        arayuz._logla.assert_called_once()
        metin, renk = arayuz._logla.call_args.args
        self.assertIn("GÖNDERİLEMEDİ", metin)
        self.assertIn(komut, metin)
        self.assertEqual("kirmizi", renk)

    def test_arm_adres_yokken_durum_ve_ekran_degismez(self):
        arayuz = self._arayuz()

        arayuz.arm_degistir()

        self._kirmizi_hata_dogrula(arayuz, "ARM")
        self.assertFalse(arayuz.arm_acik)
        self.assertEqual("normal", arayuz.btn_arm.cget("state"))
        self.assertEqual("ARM (A)", arayuz.btn_arm.cget("text"))
        self.assertEqual("disabled", arayuz.btn_firlat.cget("state"))
        self.assertNotIn("uçuşa hazır", arayuz.lbl_arm.cget("text"))

    def test_arm_adres_varken_ack_ve_heartbeat_gelmeden_baslamis_sayilmaz(self):
        arayuz = self._arayuz(adres_var=True)

        arayuz.arm_degistir()

        self._komut_dogrula(arayuz, "ARM")
        self.assertFalse(arayuz.arm_acik)
        self.assertEqual("ARM", arayuz.arm_bekleyen_komut)
        self.assertIn("BEKLENİYOR", arayuz.btn_arm.cget("text"))
        self.assertNotIn("uçuşa hazır", arayuz.lbl_arm.cget("text"))
        self.assertEqual("disabled", arayuz.btn_firlat.cget("state"))

    def test_disarm_adres_yokken_durum_ve_ekran_degismez(self):
        arayuz = self._arayuz(arm_acik=True)

        arayuz.arm_degistir()

        self._kirmizi_hata_dogrula(arayuz, "DISARM")
        self.assertTrue(arayuz.arm_acik)
        self.assertEqual("normal", arayuz.btn_arm.cget("state"))
        self.assertEqual("DISARM (A)", arayuz.btn_arm.cget("text"))
        self.assertEqual("normal", arayuz.btn_firlat.cget("state"))
        self.assertNotIn("DISARM", arayuz.lbl_arm.cget("text"))
        self.assertNotIn("güvenli", arayuz.lbl_arm.cget("text"))

    def test_disarm_adres_varken_ack_ve_heartbeat_gelmeden_guvenli_sayilmaz(self):
        arayuz = self._arayuz(arm_acik=True, adres_var=True)

        arayuz.arm_degistir()

        self._komut_dogrula(arayuz, "DISARM")
        self.assertTrue(arayuz.arm_acik)
        self.assertEqual("DISARM", arayuz.arm_bekleyen_komut)
        self.assertIn("BEKLENİYOR", arayuz.btn_arm.cget("text"))
        self.assertNotIn("güvenli", arayuz.lbl_arm.cget("text"))
        self.assertEqual("disabled", arayuz.btn_firlat.cget("state"))

    def test_parasut_adres_yokken_ceza_ve_basari_uydurmaz(self):
        arayuz = self._arayuz()

        with mock.patch.object(yks_gui.time, "time", return_value=100.0):
            arayuz.parasut()

        self._kirmizi_hata_dogrula(arayuz, "PARACHUTE")
        arayuz._ceza_ekle.assert_not_called()
        arayuz._ucus.assert_not_called()
        self.assertEqual(99.0, arayuz.parasut_teyit)
        self.assertEqual("normal", arayuz.btn_parasut.cget("state"))
        self.assertNotIn("AÇILDI", arayuz.btn_parasut.cget("text"))

    def test_parasut_adres_varken_eskisi_gibi_tetiklenir(self):
        arayuz = self._arayuz(adres_var=True)

        with mock.patch.object(yks_gui.time, "time", return_value=100.0):
            arayuz.parasut()

        self._komut_dogrula(arayuz, "PARACHUTE")
        arayuz._ceza_ekle.assert_called_once_with(
            50, "manuel paraşüt tetikleme (§2.2.4)")
        arayuz._ucus.assert_called_once_with(
            "PARAŞÜT — MANUEL TETİKLENDİ (−50)", yks_gui.KIRMIZI)
        self.assertEqual("disabled", arayuz.btn_parasut.cget("state"))
        # D-403 (curutucu): dugme GONDERIMDE "ACILDI" diyemez — ACK yok daha.
        # "ACILDI ✓" yalniz IHA ACK'inde (o da Pixhawk COMMAND_ACK ACCEPTED).
        self.assertEqual("PARAŞÜT GÖNDERİLDİ — İHA ACK bekleniyor",
                         arayuz.btn_parasut.cget("text"))
        self.assertNotIn("AÇILDI", arayuz.btn_parasut.cget("text"))


if __name__ == "__main__":
    unittest.main()
