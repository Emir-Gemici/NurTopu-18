"""21 Eylul drone testi: YKI ARM gercegi ve ham GNSS fail-closed kapilari."""

import sys
import time
import unittest
from pathlib import Path
from unittest import mock


KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "comms"))

import yks_gui  # noqa: E402
from protocol import ACK_SONUC_KABUL, ack, decode, heartbeat  # noqa: E402


class _Widget:
    def __init__(self, **ayar):
        self.ayar = dict(ayar)

    def config(self, **ayar):
        self.ayar.update(ayar)

    def cget(self, ad):
        return self.ayar.get(ad)


def _arayuz(armed=False):
    g = object.__new__(yks_gui.YksArayuz)
    g.link = mock.Mock()
    g.son_adr = {"iha": ("127.0.0.1", 5007)}
    g.sabit_adr = {"iha": ("127.0.0.1", 5007)}
    g._logla = mock.Mock()
    g.kok = mock.Mock()
    g.arm_acik = armed
    g.arm_durum_zamani = time.monotonic()
    g.arm_bekleyen_komut = None
    g.arm_ack_zamani = None
    g._kritik_teyit = {}
    g.arm_tekrar = yks_gui.AckliTekrar(
        g._ham_gonder, yks_gui.ARM_TEKRAR_ARALIGI_S,
        yks_gui.ARM_TEKRAR_UST_SINIRI)
    g.parasut_tekrar = None
    g.ika_go_tekrar = mock.Mock()
    g.ika_go_tekrar.ack_geldi.return_value = False
    g.rota = None
    g.btn_arm = _Widget(state="normal", text="ARM (A)", bg="#232e3a")
    g.btn_force_arm = _Widget(state="disabled", text="FORCE ARM (2×)", bg="#232e3a")
    g.lbl_arm = _Widget(text="", fg=yks_gui.SOLUK)
    g.btn_firlat = _Widget(state="disabled", bg="#232e3a")
    g.son_hb = {}
    g.tel = {}
    g.mod = {}
    g._manuel_uyarildi = False
    g.iha_iz = []
    g.karar_yas_rx = None
    g.sayac = {"HEARTBEAT": 0}
    g.iha_landed_seq = None
    g.t_iha0 = g.t_iha1 = None
    return g


class ArmGercegiTests(unittest.TestCase):
    def _arm_baslat(self, g):
        g.arm_degistir()
        g.link.send.assert_not_called()
        g.arm_degistir()
        veri, hedef = g.link.send.call_args.args
        self.assertEqual(("127.0.0.1", 5007), hedef)
        return decode(veri)

    def test_gonderim_tek_basina_arm_ve_firlatma_acmaz(self):
        g = _arayuz(False)
        mesaj = self._arm_baslat(g)
        self.assertEqual("ARM", mesaj["cmd"])
        self.assertFalse(g.arm_acik)
        self.assertEqual("ARM", g.arm_bekleyen_komut)
        self.assertEqual("disabled", g.btn_firlat.cget("state"))

    def test_force_arm_iki_tikla_ve_ayri_komut_olarak_gonderilir(self):
        g = _arayuz(False)
        g._arm_ui_uygula()
        g.force_arm()
        g.link.send.assert_not_called()
        self.assertIn("TEKRAR BAS", g.btn_force_arm.cget("text"))
        g.force_arm()
        veri, hedef = g.link.send.call_args.args
        self.assertEqual(("127.0.0.1", 5007), hedef)
        mesaj = decode(veri)
        self.assertEqual("FORCE_ARM", mesaj["cmd"])
        self.assertEqual("FORCE_ARM", g.arm_bekleyen_komut)
        self.assertEqual("disabled", g.btn_force_arm.cget("state"))

    def test_zayif_ve_yanlis_ack_dusurulur(self):
        for degisen in ("ref_cmd", "sonuc", "ref_tip", "node"):
            with self.subTest(degisen=degisen):
                g = _arayuz(False)
                mesaj = self._arm_baslat(g)
                guclu = ack(mesaj["seq"], "iha", "CMD", ref_cmd="ARM",
                            sonuc=ACK_SONUC_KABUL)
                guclu[degisen] = {
                    "ref_cmd": "DISARM", "sonuc": "REJECTED",
                    "ref_tip": "OPEN_ROUTE", "node": "ika",
                }[degisen]
                g._ack_isle(guclu, ("127.0.0.1", 5007))
                self.assertTrue(g.arm_tekrar.bekliyor)
                self.assertEqual("ARM", g.arm_bekleyen_komut)

    def test_guclu_ack_yetmez_eslesen_heartbeat_ile_tamamlanir(self):
        g = _arayuz(False)
        mesaj = self._arm_baslat(g)
        guclu = ack(mesaj["seq"], "iha", "CMD", ref_cmd="ARM",
                    sonuc=ACK_SONUC_KABUL)
        g._ack_isle(guclu, ("127.0.0.1", 5007))
        self.assertEqual("ARM", g.arm_bekleyen_komut)
        self.assertEqual("disabled", g.btn_firlat.cget("state"))

        g._mesaj_isle(heartbeat("iha", armed=True), ("127.0.0.1", 5007))

        self.assertIsNone(g.arm_bekleyen_komut)
        self.assertTrue(g.arm_acik)
        self.assertEqual("normal", g.btn_firlat.cget("state"))
        self.assertIn("PIXHAWK HEARTBEAT", g.lbl_arm.cget("text"))

    def test_bayat_armed_telemetrisi_komutu_ve_firlatmayi_kapatir(self):
        g = _arayuz(True)
        g.arm_durum_zamani -= yks_gui.ARM_DURUM_TAZELIK_S + 0.1
        g.arm_degistir()
        g.link.send.assert_not_called()
        g.firlatma()
        self.assertIsNone(g.t_iha0)
        self.assertEqual("disabled", g.btn_firlat.cget("state"))


class GpsGosterimiTests(unittest.TestCase):
    def test_ham_gnss_etiketi_haritadan_acikca_ayrilir(self):
        metin = yks_gui.gps_gosterim_metni({
            "lat": 37.7648123, "lon": 38.2786456,
            "gps_fix": 3, "uydu": 14,
        })
        self.assertIn("37.7648123", metin)
        self.assertIn("38.2786456", metin)
        self.assertIn("fix 3", metin)
        self.assertIn("SEMANTİK HARİTADA KULLANILMAZ", metin)

    def test_yeni_heartbeat_eksik_gpsyi_bayat_onbellekten_siler(self):
        g = _arayuz(False)
        g._mesaj_isle(heartbeat(
            "iha", lat=37.7, lon=38.2, gps_fix=3, uydu=12, armed=False), None)
        self.assertIn("lat", g.tel["iha"])

        g._mesaj_isle(heartbeat("iha", armed=False), None)

        self.assertNotIn("lat", g.tel["iha"])
        self.assertNotIn("lon", g.tel["iha"])
        self.assertNotIn("gps_fix", g.tel["iha"])

    def test_armed_sayisal_bir_ile_taklit_edilemez(self):
        self.assertIsNone(yks_gui.arm_telemetri_degeri({"armed": 1}))
        self.assertIsNone(yks_gui.arm_telemetri_degeri({"armed": "true"}))
        self.assertTrue(yks_gui.arm_telemetri_degeri({"armed": True}))


if __name__ == "__main__":
    unittest.main()
