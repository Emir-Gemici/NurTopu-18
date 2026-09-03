"""21 Eylul YKI operator guvenligi: telemetri ve acil-mod kanitlari.

Bu kapilar Tk penceresi, ag veya gercek Pixhawk acmadan iki sessiz tehlike
yonunu sinar:

* bozuk sayisal HEARTBEAT alanlari ana GUI tikini olduremez ve ekrana tasinmaz;
* RTL/LAND ``COMMAND_ACK ACCEPTED`` yalniz kabuldur, hedef ucus modunun
  gercekten goruldugu anlamina gelmez.
"""

import ast
import inspect
import sys
import time
import unittest
from pathlib import Path
from unittest import mock


KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "comms"))

import yks_gui  # noqa: E402
from protocol import ACK_SONUC_KABUL, ack, decode, heartbeat  # noqa: E402


IHA_ADRESI = ("127.0.0.1", 5007)


class _Widget:
    def __init__(self, **ayar):
        self.ayar = dict(ayar)

    def config(self, **ayar):
        self.ayar.update(ayar)

    def cget(self, ad):
        return self.ayar.get(ad)


def _taban_arayuz():
    """Mesaj alimi ve ``_durum_tazele`` icin kucuk, basiz YKI fiksturu."""
    g = object.__new__(yks_gui.YksArayuz)
    g.protokol_kilidi = False
    g.kaynak_kilidi = False
    g._son_heartbeat_seq = {}
    g.protokol_ret_sayaci = 0
    g.kaynak_ret_sayaci = 0
    g.link = mock.Mock()
    g.son_adr = {"iha": IHA_ADRESI}
    g.sabit_adr = {"iha": IHA_ADRESI}
    g.son_hb = {}
    g.tel = {}
    g.mod = {}
    g.karar_yas_rx = None
    g.arm_acik = None
    g.arm_durum_zamani = None
    g.arm_bekleyen_komut = None
    g.arm_ack_zamani = None
    g.iha_landed_seq = None
    g.iha_iz = []
    g._manuel_uyarildi = False
    g._kritik_teyit = {}
    g.rota = None
    g.rota_yok = None
    g.rota_zaman = None
    g.tespit_bayat = False
    g.onaylandi = False
    g.sayac = {
        "OPEN_ROUTE": 0, "OPEN_ROUTE_RED": 0, "NO_ROUTE": 0,
        "IHA_LANDED": 0, "HEARTBEAT": 0, "ACK_TX": 0,
    }
    g._logla = mock.Mock()
    g._kanit_durumu_yaz = mock.Mock()
    g._arm_ui_uygula = mock.Mock()
    g._arm_bekleyeni_tamamla = mock.Mock(return_value=False)
    g._acil_ui_uygula = mock.Mock()
    g._ucus = mock.Mock()

    g.lbl_saat = _Widget()
    g.lbl_dugum = {
        "iha": (_Widget(), _Widget()),
        "ika": (_Widget(), _Widget()),
    }
    g.lbl_gps = _Widget()
    g.lbl_sayac = _Widget()
    g.lbl_kron_iha = _Widget()
    g.lbl_kron_ika = _Widget()
    g.lbl_kron_haz = _Widget()
    g.t_iha0 = g.t_iha1 = None
    g.t_ika0 = g.t_ika1 = None
    g.t_haz0 = g.t_haz1 = None
    g.IHA_LIMIT = yks_gui.SARTNAME_IHA_GOREV_SURESI_S
    g.IKA_LIMIT = yks_gui.SARTNAME_IKA_GOREV_SURESI_S
    g.HAZIRLIK_LIMIT = yks_gui.SARTNAME_HAZIRLIK_SURESI_S
    g.fda_kipi = False
    g.gorunum_adi = "kamera"
    return g


def _acil_arayuz():
    g = _taban_arayuz()
    g.arm_tekrar = None
    g.parasut_tekrar = None
    g.ika_go_tekrar = mock.Mock()
    g.ika_go_tekrar.ack_geldi.return_value = False
    g.acil_bekleyen_komut = None
    g.acil_ack_zamani = None
    g.acil_tekrar = yks_gui.AckliTekrar(
        g._ham_gonder, yks_gui.ARM_TEKRAR_ARALIGI_S,
        yks_gui.ARM_TEKRAR_UST_SINIRI)
    g.btn_rtl = _Widget(state="normal", bg=yks_gui.KIRMIZI, text="ACIL RTL")
    g.btn_land = _Widget(state="normal", bg=yks_gui.KIRMIZI, text="ACIL LAND")
    g.lbl_acil = _Widget(text="ACIL UCUS KOMUTU: -", fg=yks_gui.SOLUK)
    # Bu fiksturda gercek cizim yordamlarini kullan: bekleyen durumun dugmelerde
    # gorunmesi, operatorun ACK'i tamamlanma sanmamasinin parcasidir.
    del g._acil_ui_uygula
    return g


class TelemetriAlanGuvenligiTests(unittest.TestCase):
    def test_bozuk_sayisal_alan_elenir_diger_alanlar_ve_gui_tiki_yasar(self):
        gecersizler = ("12.5", True, False, float("nan"), float("inf"),
                       float("-inf"))
        alanlar = ("bat", "hiz", "yon", "alt", "lat", "lon")

        for alan in alanlar:
            for deger in gecersizler:
                with self.subTest(alan=alan, deger=repr(deger)):
                    g = _taban_arayuz()
                    telemetri = {
                        "bat": 16.4, "hiz": 5.0, "yon": 123.0, "alt": 30.0,
                        "lat": 37.7648, "lon": 38.2786, "gps_fix": 3,
                        "uydu": 14, "pixhawk_canli": True, "armed": False,
                        "mod": "AUTO",
                    }
                    telemetri[alan] = deger

                    g._mesaj_isle(heartbeat("iha", seq=1, **telemetri), None)
                    # Ana Tk zincirindeki gercek cizim yolu da patlamamali.
                    g._durum_tazele()

                    self.assertNotIn(
                        alan, g.tel["iha"],
                        f"bozuk {alan} operator ekranina tasindi: {deger!r}")
                    self.assertEqual(3, g.tel["iha"].get("gps_fix"))
                    self.assertEqual(14, g.tel["iha"].get("uydu"))
                    self.assertIs(g.tel["iha"].get("pixhawk_canli"), True)
                    self.assertIs(g.arm_acik, False)
                    self.assertEqual("AUTO", g.mod.get("iha"))

    def test_sonlu_sayisal_alanlar_kaybolmaz(self):
        g = _taban_arayuz()
        beklenen = {
            "bat": 16.4, "hiz": 5.0, "yon": 123.0, "alt": 30.0,
            "lat": 37.7648, "lon": 38.2786,
        }
        g._mesaj_isle(heartbeat(
            "iha", seq=1, gps_fix=3, uydu=14, pixhawk_canli=True,
            armed=False, mod="AUTO", **beklenen), None)
        g._durum_tazele()
        for alan, deger in beklenen.items():
            self.assertEqual(deger, g.tel["iha"].get(alan), alan)


class AcilModDogrulamaTests(unittest.TestCase):
    def _acil_istegini_gonder(self, g, komut):
        g.acil_komut(komut)  # ilk tik: yalniz teyit
        g.link.send.assert_not_called()
        g.acil_komut(komut)  # ikinci tik: gercek komut
        veri, hedef = g.link.send.call_args.args
        self.assertEqual(IHA_ADRESI, hedef)
        mesaj = decode(veri)
        self.assertEqual(komut, mesaj["cmd"])
        return mesaj

    @staticmethod
    def _mod_dogrulandi_logu_var(g):
        return any(
            cagri.args and "MOD DOĞRULANDI" in str(cagri.args[0])
            for cagri in g._logla.call_args_list)

    def test_guclu_ack_yetmez_eslesen_taze_mod_heartbeati_tamamlar(self):
        for komut in ("RTL", "LAND"):
            with self.subTest(komut=komut):
                g = _acil_arayuz()
                mesaj = self._acil_istegini_gonder(g, komut)
                guclu = ack(
                    mesaj["seq"], "iha", "CMD", ref_cmd=komut,
                    sonuc=ACK_SONUC_KABUL)

                g._ack_isle(guclu, IHA_ADRESI)

                self.assertEqual(
                    komut, g.acil_bekleyen_komut,
                    "COMMAND_ACK yalniz kabuldur; hedef mod kaniti degildir")
                self.assertFalse(self._mod_dogrulandi_logu_var(g))
                self.assertNotIn("MOD DOĞRULANDI", g.lbl_acil.cget("text") or "")
                self.assertEqual("disabled", g.btn_rtl.cget("state"))
                self.assertEqual("disabled", g.btn_land.cget("state"))

                # ACK sonrasi AUTO akmaya devam ederse basari uydurulamaz.
                g._mesaj_isle(heartbeat(
                    "iha", seq=10, mod="AUTO", armed=True,
                    pixhawk_canli=True), None)
                self.assertEqual(komut, g.acil_bekleyen_komut)
                self.assertFalse(self._mod_dogrulandi_logu_var(g))
                self.assertNotIn("MOD DOĞRULANDI", g.lbl_acil.cget("text") or "")

                # Ancak yeni ve eslesen Pixhawk mod snapshot'i tamamlar.
                g._mesaj_isle(heartbeat(
                    "iha", seq=11, mod=komut, armed=True,
                    pixhawk_canli=True), None)
                self.assertIsNone(g.acil_bekleyen_komut)
                self.assertIn("MOD DOĞRULANDI", g.lbl_acil.cget("text") or "")
                self.assertTrue(self._mod_dogrulandi_logu_var(g))


class DemoBeslemeHizasiTests(unittest.TestCase):
    def test_demo_tum_iha_emniyet_komutlarini_duruma_yansitir(self):
        armed, mod = False, "AUTO"
        for komut, beklenen_arm, beklenen_mod in (
                ("ARM", True, "AUTO"),
                ("RTL", True, "RTL"),
                ("LAND", True, "LAND"),
                ("PARACHUTE", True, "LAND"),
                ("DISARM", False, "LAND")):
            with self.subTest(komut=komut):
                armed, mod, kabul = yks_gui.demo_iha_komutunu_uygula(
                    {"type": "CMD", "hedef": "iha", "cmd": komut},
                    armed, mod)
                self.assertTrue(kabul)
                self.assertIs(armed, beklenen_arm)
                self.assertEqual(beklenen_mod, mod)

        once = (armed, mod)
        armed, mod, kabul = yks_gui.demo_iha_komutunu_uygula(
            {"type": "CMD", "hedef": "ika", "cmd": "ARM"}, armed, mod)
        self.assertFalse(kabul)
        self.assertEqual(once, (armed, mod))

    def test_demo_heartbeat_pixhawk_ve_pil_yuzdesi_tasir(self):
        kaynak = inspect.getsource(yks_gui.demo_besle)
        agac = ast.parse(kaynak)
        guncellemeler = [n for n in ast.walk(agac)
                        if isinstance(n, ast.Call)
                        and isinstance(n.func, ast.Attribute)
                        and n.func.attr == "update"]
        anahtarlar = {k.arg for cagri in guncellemeler for k in cagri.keywords}
        self.assertIn("bat_yuzde", anahtarlar,
                      "demo pil yüzdesini göstermezse saha paneli kanıtlanamaz")
        self.assertIn("pixhawk_canli", anahtarlar,
                      "demo Jetson heartbeat'ini Pixhawk canlılığı sanmamalı")


if __name__ == "__main__":
    unittest.main()
