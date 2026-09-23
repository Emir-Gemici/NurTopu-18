"""NEDEN: FDA kalkış/intikal ve hakem RTL akışı gerçek donanıma komut göndermeden sınanır."""

import math
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

KOK = Path(__file__).resolve().parents[1]
for dizin in (KOK / "codes", KOK / "comms", KOK / "tests"):
    sys.path.insert(0, str(dizin))

from pymavlink import mavutil
import fda_gorev as gorev
from fda_mavlink import FdaPlanYukleyici, GorevYuklemeHatasi
from yks_fda_panel import FdaGorevDenetleyici
from protocol import ack, command, heartbeat
from test_iha_komut_saat_ve_tekrar import _alici, _Mav, KAYNAK, IHA_SAATI


def ayar(**degisiklik):
    sonuc = dict(id="a" * 32, lat=37.7487228, lon=38.2180109,
                 yon=0.0, yukseklik_m=30.0, ileri_m=40.0)
    sonuc.update(degisiklik)
    return sonuc


def telemetri(**degisiklik):
    sonuc = dict(lat=ayar()["lat"], lon=ayar()["lon"], yon=0.0,
                 alt=0.0, hiz=0.0, armed=False, mod="LOITER",
                 gps_fix=3, pixhawk_canli=True, gorev_hazir=True)
    sonuc.update(degisiklik)
    return sonuc


class Saat:
    def __init__(self):
        self.simdi = 100.0

    def __call__(self):
        return self.simdi


class GorevFiksturu(unittest.TestCase):
    def setUp(self):
        self.gecici = tempfile.TemporaryDirectory(prefix="navitas_fda_")
        self.addCleanup(self.gecici.cleanup)
        self.yol = Path(self.gecici.name) / "gorev.json"
        self.saat = Saat()
        self.veri = telemetri()
        self.kapi = gorev.AlgiGorevKapisi(self.yol, lambda: self.veri, self.saat)
        self.kapi.etkinlestir()

    def plan_yaz(self, **alanlar):
        plan = dict(v=1, algi_oturumu=self.kapi.oturum, dogrulandi=True,
                    ayar=ayar(), ozet=gorev.ayar_ozeti(ayar()), hedef_irtifa_m=30.0)
        plan.update(alanlar)
        gorev.atomik_json_yaz(self.yol, plan)
        self.kapi.guncelle()

    def hedefe_gel(self):
        enlem, boylam = gorev.hedef_konumu(ayar())
        self.veri.update(lat=enlem, lon=boylam, alt=30.0, mod="AUTO", armed=True)


class GorevTest(GorevFiksturu):
    def test_yonler_ve_mesafe(self):
        for yon, eksen, isaret in ((0, 0, 1), (90, 1, 1), (180, 0, -1), (270, 1, -1)):
            with self.subTest(yon=yon):
                plan = ayar(yon=yon)
                baslangic = (plan["lat"], plan["lon"])
                hedef = gorev.hedef_konumu(plan)
                self.assertAlmostEqual(gorev.mesafe_m(baslangic, hedef), 40.0, places=4)
                self.assertGreater((hedef[eksen] - baslangic[eksen]) * isaret, 0)

    def test_bozuk_ayarlar(self):
        for alan, deger in (("yon", None), ("yon", 360), ("yon", math.nan),
                            ("ileri_m", 0), ("yukseklik_m", -1), ("lat", True),
                            ("lon", math.inf), ("id", "x" * 32)):
            with self.subTest(alan=alan, deger=deger), self.assertRaises(ValueError):
                gorev.ayar_dogrula(ayar(**{alan: deger}))

    def test_yuksel_intikal_kararlilik_algi(self):
        self.plan_yaz()
        self.assertEqual(self.kapi.durum, "RC_AUTO_BEKLENIYOR")
        self.veri.update(armed=True, mod="AUTO", alt=5)
        self.assertFalse(self.kapi.guncelle())
        self.assertEqual(self.kapi.durum, "YUKSELME_VEYA_IRTIFA_DUZELTME")
        self.veri["alt"] = 30
        self.assertFalse(self.kapi.guncelle())
        self.assertEqual(self.kapi.durum, "HEDEFE_INTIKAL")
        self.hedefe_gel()
        self.assertFalse(self.kapi.guncelle())
        self.saat.simdi += 2.01
        self.assertTrue(self.kapi.guncelle())
        self.veri["mod"] = "RTL"
        self.assertFalse(self.kapi.guncelle())

    def test_kararlilik_kesilince_sayac_sifirlanir(self):
        self.plan_yaz()
        self.hedefe_gel()
        self.kapi.guncelle()
        self.saat.simdi += 1
        self.veri["hiz"] = 1
        self.assertFalse(self.kapi.guncelle())
        self.veri["hiz"] = 0
        self.saat.simdi += 2
        self.assertFalse(self.kapi.guncelle())
        self.saat.simdi += 2
        self.assertTrue(self.kapi.guncelle())

    def test_bayat_kopuk_yanlis_oturum_plan_kapali(self):
        for degisiklik in ({"dogrulandi": False}, {"ozet": "bozuk"}, {"algi_oturumu": "eski"}):
            self.plan_yaz(**degisiklik)
            self.hedefe_gel()
            self.assertFalse(self.kapi.guncelle())
            self.veri = telemetri()

    def test_telemetri_yok_algi_yok(self):
        self.plan_yaz()
        self.hedefe_gel()
        for alan, deger in (("pixhawk_canli", False), ("gps_fix", None), ("alt", math.nan),
                            ("lat", None), ("hiz", -1), ("mod", "LOITER"), ("armed", None)):
            onceki = self.veri[alan]
            self.veri[alan] = deger
            self.assertFalse(self.kapi.guncelle())
            self.veri[alan] = onceki

    def test_inisten_sonra_eski_plan_yeniden_acilmaz(self):
        self.plan_yaz()
        self.hedefe_gel()
        self.kapi.guncelle()
        self.veri["armed"] = False
        self.kapi.guncelle()
        self.veri["armed"] = True
        self.saat.simdi += 5
        self.assertFalse(self.kapi.guncelle())
        self.assertEqual(self.kapi.durum, "YENI_GOREV_GEREKLI")

    def test_havada_ilk_gorulen_plan_kapali(self):
        self.hedefe_gel()
        self.plan_yaz()
        self.assertFalse(self.kapi.guncelle())

    def test_heartbeat_gorev_alani_ve_lease(self):
        self.plan_yaz()
        paket = heartbeat("iha", **self.kapi.telemetri())
        self.assertTrue(paket["gorev_hazir"])
        self.assertEqual(paket["gorev_id"], ayar()["id"])
        gorev.hazirlik_oku(self.yol, self.saat())
        self.saat.simdi += 4
        with self.assertRaises(ValueError):
            gorev.hazirlik_oku(self.yol, self.saat())
        self.kapi.guncelle()
        self.kapi.kapat()
        with self.assertRaises(ValueError):
            gorev.hazirlik_oku(self.yol, self.saat())


class Mesaj(SimpleNamespace):
    def get_type(self):
        return self.tur

    def get_srcSystem(self):
        return getattr(self, "kaynak_sys", 1)

    def get_srcComponent(self):
        return 1


class Pixhawk:
    def __init__(self, saat, kapi):
        self.saat = saat
        self.kapi = kapi
        self.kod = mavutil.mavlink
        self.kuyruk = []
        self.satirlar = {}
        self.cagrilar = []
        self.adet = None
        self.armed = False
        self.son_hb = 0
        self.bozuk_okuma = False
        self.koordinat_farki = (0, 0)
        self.ack_ret = False
        self.sessiz = False
        self.kaynak_sys = 1
        self.mod = 5
        self.landed = self.kod.MAV_LANDED_STATE_ON_GROUND
        self.hdg = 0
        self.parametreler = dict(AUTO_OPTIONS=2, FENCE_ENABLE=1, FENCE_TYPE=3,
                                 FENCE_ALT_MAX=100, FENCE_RADIUS=100,
                                 FENCE_MARGIN=2, ARMING_CHECK=1)
        self.mav = SimpleNamespace(srcSystem=255, srcComponent=190)
        for ad in ("command_long", "param_request_read", "mission_count", "mission_item_int",
                   "mission_item", "mission_request_list", "mission_request_int", "mission_ack",
                   "mission_set_current"):
            setattr(self.mav, ad + "_send", self.gonderici(ad))

    def mesaj(self, tur, **alanlar):
        return Mesaj(tur=tur, kaynak_sys=self.kaynak_sys,
                     target_system=255, target_component=190, mission_type=0, **alanlar)

    def gonderici(self, ad):
        def gonder(*argumanlar):
            self.cagrilar.append((ad, argumanlar))
            if self.sessiz:
                return
            if ad == "command_long":
                kimlik = argumanlar[4]
                mesajlar = {
                    24: self.mesaj("GPS_RAW_INT", fix_type=3),
                    33: self.mesaj("GLOBAL_POSITION_INT", lat=round(ayar()["lat"] * 1e7),
                                  lon=round(ayar()["lon"] * 1e7), relative_alt=0, vx=0, vy=0, hdg=self.hdg),
                    242: self.mesaj("HOME_POSITION", latitude=round(ayar()["lat"] * 1e7),
                                   longitude=round(ayar()["lon"] * 1e7), altitude=650000),
                    245: self.mesaj("EXTENDED_SYS_STATE", landed_state=self.landed),
                }
                self.kuyruk.append(mesajlar[kimlik])
            elif ad == "param_request_read":
                kimlik = argumanlar[2].decode()
                self.kuyruk.append(self.mesaj("PARAM_VALUE", param_id=kimlik, param_value=self.parametreler[kimlik]))
            elif ad == "mission_count":
                self.adet = argumanlar[2]
                self.kuyruk.append(self.mesaj("MISSION_REQUEST_INT", seq=0))
            elif ad in ("mission_item_int", "mission_item"):
                sira = argumanlar[2]
                self.satirlar[sira] = argumanlar
                if sira + 1 < self.adet:
                    self.kuyruk.append(self.mesaj("MISSION_REQUEST_INT", seq=sira + 1))
                else:
                    self.kuyruk.append(self.mesaj("MISSION_ACK", type=1 if self.ack_ret else 0))
            elif ad == "mission_request_list":
                self.kuyruk.append(self.mesaj("MISSION_COUNT", count=self.adet))
            elif ad == "mission_request_int":
                sira = argumanlar[2]
                satir = self.satirlar[sira]
                self.kuyruk.append(self.mesaj(
                    "MISSION_ITEM_INT", seq=sira, frame=satir[3], command=satir[4],
                    autocontinue=satir[6], param1=satir[7], param2=satir[8],
                    param3=satir[9], param4=satir[10],
                    x=satir[11] + self.koordinat_farki[0],
                    y=satir[12] + self.koordinat_farki[1],
                    z=satir[13] + (1 if self.bozuk_okuma else 0)))
            elif ad == "mission_set_current":
                self.kuyruk.append(self.mesaj("MISSION_CURRENT", seq=argumanlar[2]))
        return gonder

    def recv_match(self, blocking=False, timeout=0):
        if not blocking:
            return self.kuyruk.pop(0) if self.kuyruk else None
        self.saat.simdi += 0.05
        self.kapi.guncelle()
        if self.saat() - self.son_hb >= 0.5:
            self.son_hb = self.saat()
            return self.mesaj("HEARTBEAT", base_mode=128 if self.armed else 0,
                              custom_mode=self.mod, autopilot=3, type=2)
        return self.kuyruk.pop(0) if self.kuyruk else None


class YuklemeTest(GorevFiksturu):
    def setUp(self):
        super().setUp()
        self.pixhawk = Pixhawk(self.saat, self.kapi)
        self.yukleyici = FdaPlanYukleyici(self.pixhawk, self.yol, saat=self.saat)

    def test_tam_yukleme_geri_okuma_hareket_komutu_yok(self):
        self.assertTrue(self.yukleyici.hazirla(ayar(yon=0)))
        plan = gorev.json_oku(self.yol)
        self.assertTrue(plan["dogrulandi"])
        self.assertEqual([self.pixhawk.satirlar[sira][4] for sira in range(4)], [16, 22, 16, 17])
        self.assertEqual(self.pixhawk.satirlar[1][11:14], (0, 0, 30.0))
        self.assertEqual(self.pixhawk.satirlar[2][11:14], self.pixhawk.satirlar[3][11:14])

    def test_koordinat_geri_okuma_pixhawk_yuvarlamasi_kabul_edilir(self):
        self.pixhawk.koordinat_farki = (14, -19)
        self.assertTrue(self.yukleyici.hazirla(ayar(yon=0)))
        self.assertTrue(all(argumanlar[2] == mavutil.mavlink.MAV_CMD_REQUEST_MESSAGE
                            for ad, argumanlar in self.pixhawk.cagrilar if ad == "command_long"))
        self.assertEqual(self.pixhawk.cagrilar[-1], ("mission_set_current", (1, 1, 1)))

    def test_koordinat_geri_okuma_kucuk_sapma_kabul_edilir(self):
        self.pixhawk.koordinat_farki = (27, -27)
        self.assertTrue(self.yukleyici.hazirla(ayar(yon=0)))

    def test_armed_auto_havada_yanlis_yon_yukleme_yok(self):
        for alan, deger in (("armed", True), ("mod", 3), ("landed", 2), ("hdg", 9000)):
            onceki = getattr(self.pixhawk, alan)
            setattr(self.pixhawk, alan, deger)
            with self.subTest(alan=alan), self.assertRaises(GorevYuklemeHatasi):
                self.yukleyici.hazirla(ayar())
            setattr(self.pixhawk, alan, onceki)
            self.assertFalse(any(ad == "mission_count" for ad, _ in self.pixhawk.cagrilar))

    def test_parametre_ve_cit_reddi(self):
        for alan, deger in (("AUTO_OPTIONS", 0), ("FENCE_ENABLE", 0), ("FENCE_TYPE", 7),
                            ("FENCE_ALT_MAX", 30), ("FENCE_RADIUS", 40), ("ARMING_CHECK", 0)):
            onceki = self.pixhawk.parametreler[alan]
            self.pixhawk.parametreler[alan] = deger
            with self.subTest(alan=alan), self.assertRaises(GorevYuklemeHatasi):
                self.yukleyici.hazirla(ayar())
            self.pixhawk.parametreler[alan] = onceki
            self.assertFalse(any(ad == "mission_count" for ad, _ in self.pixhawk.cagrilar))

    def test_ack_red_ve_geri_okuma_red_plani_acmaz(self):
        for alan in ("ack_ret", "bozuk_okuma"):
            setattr(self.pixhawk, alan, True)
            with self.subTest(alan=alan), self.assertRaises(GorevYuklemeHatasi):
                self.yukleyici.hazirla(ayar())
            self.assertFalse(gorev.json_oku(self.yol)["dogrulandi"])
            setattr(self.pixhawk, alan, False)

    def test_algi_hazir_degilse_mavlink_yok(self):
        self.kapi.kapat()
        with self.assertRaises(ValueError):
            self.yukleyici.hazirla(ayar())
        self.assertEqual(self.pixhawk.cagrilar, [])

    def test_yanlis_sysid_ve_sessiz_arac_zaman_asimi(self):
        self.pixhawk.kaynak_sys = 2
        with self.assertRaises(GorevYuklemeHatasi):
            self.yukleyici.hazirla(ayar())
        self.assertEqual(self.pixhawk.cagrilar, [])

    def test_aktarim_sirasinda_arm_olursa_yukleme_kesilir(self):
        onceki = self.pixhawk.mav.mission_item_int_send

        def arm_ve_gonder(*argumanlar):
            onceki(*argumanlar)
            self.pixhawk.armed = True
            self.pixhawk.son_hb = 0

        self.pixhawk.mav.mission_item_int_send = arm_ve_gonder
        with self.assertRaisesRegex(GorevYuklemeHatasi, "ARM"):
            self.yukleyici.hazirla(ayar())
        self.assertFalse(gorev.json_oku(self.yol)["dogrulandi"])
        self.assertEqual(len(self.pixhawk.satirlar), 1)

    def test_gercek_mavlink1_ve_2_serilestirme(self):
        import io
        from pymavlink.dialects.v10 import ardupilotmega as mavlink1
        from pymavlink.dialects.v20 import ardupilotmega as mavlink2
        for diyalekt in (mavlink1, mavlink2):
            with self.subTest(diyalekt=diyalekt.__name__):
                akis = io.BytesIO()
                baglanti = SimpleNamespace(mav=diyalekt.MAVLink(akis, srcSystem=255, srcComponent=190))
                yukleyici = FdaPlanYukleyici(baglanti, self.yol, saat=self.saat, mavlink=diyalekt)
                yukleyici.son = self.saat() + 30
                yukleyici.hb_zamani = self.saat()
                yukleyici.hb = self.pixhawk.mesaj("HEARTBEAT", base_mode=0, custom_mode=5, autopilot=3, type=2)
                home = SimpleNamespace(latitude=round(ayar()["lat"] * 1e7),
                                       longitude=round(ayar()["lon"] * 1e7), altitude=650000)
                for sira, satir in enumerate(yukleyici._satirlar(ayar(), 30, home)):
                    yukleyici._satir_gonder(sira, satir, True)
                paketler = diyalekt.MAVLink(None).parse_buffer(akis.getvalue())
                self.assertEqual([paket.command for paket in paketler], [16, 22, 16, 17])
                self.assertEqual(paketler[1].frame, diyalekt.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT)
                self.assertEqual(paketler[1].z, 30.0)


class AliciTest(unittest.TestCase):
    def test_oturumlu_hazirlik_tekrari_bir_yukleme(self):
        yukleyici = Mock()
        yukleyici.hazirla.return_value = True
        alici, link, _, _ = _alici(_Mav(), gorev_yukleyici=yukleyici)
        mesaj = command(gorev.CMD_FDA_HAZIRLA, "iha", oturum="test-oturumu-fda-2026")
        mesaj.update(t=IHA_SAATI, gorev=ayar(), teshis=True)
        self.assertTrue(alici.isle(mesaj, KAYNAK))
        self.assertTrue(alici.isle(mesaj, KAYNAK))
        yukleyici.hazirla.assert_called_once()
        mesaj["gorev"]["ileri_m"] = 50
        self.assertFalse(alici.isle(mesaj, KAYNAK))
        self.assertEqual(link.gonderilen[-1][0]["sonuc"], "REJECTED")

    def test_eksik_yukleyici_ve_yabanci_kaynak_red(self):
        alici, link, _, _ = _alici(_Mav())
        mesaj = command(gorev.CMD_FDA_HAZIRLA, "iha", oturum="test-oturumu-fda-2026")
        mesaj.update(t=IHA_SAATI, gorev=ayar(), teshis=True)
        self.assertFalse(alici.isle(mesaj, ("yanlis", 9000)))
        self.assertEqual(link.gonderilen, [])
        self.assertFalse(alici.isle(mesaj, KAYNAK))
        self.assertEqual(link.gonderilen[-1][0]["neden"], "GOREV_KAPALI")


class PanelTest(unittest.TestCase):
    def setUp(self):
        self.saat = Saat()
        self.yks = SimpleNamespace(
            fda_kipi=True, demo=False, son_hb={"iha": self.saat()},
            mod_durum_zamani={"iha": self.saat()}, tel={"iha": telemetri()},
            mod={"iha": "LOITER"}, arm_acik=False, _arm_durumu_taze_mi=lambda _: True,
            _ham_gonder=Mock(return_value=True), _kanit_kilidi_var=lambda: False,
            _komut_mesaji=lambda cmd, hedef: command(cmd, hedef, oturum="panel-test-oturum-2026"),
            _kanit_yaz=Mock(), _logla=Mock(), acil_komut=Mock())
        self.panel = FdaGorevDenetleyici(self.yks, self.saat)

    def test_onizleme_komut_gondermez_yukleme_arm_gondermez(self):
        self.panel.onizle(30, 40)
        self.yks._ham_gonder.assert_not_called()
        self.panel.yukle()
        self.assertEqual(self.yks._ham_gonder.call_args.args[0]["cmd"], "FDA_HAZIRLA")
        self.assertEqual(self.panel.tekrar.durum, "BEKLIYOR")

    def test_ika_konumu_drone_gps_proxy_olarak_kaydedilir(self):
        self.yks.tel["iha"].update(lat=37.7491, lon=38.2192)
        self.yks.tel["ika"] = {}
        kayit = self.panel.ika_baslangic_al()
        self.assertEqual((kayit["lat"], kayit["lon"]), (37.7491, 38.2192))
        self.assertEqual(kayit["kaynak"], "drone_gps_proxy")

    def test_bayat_demo_armed_ve_algi_kapisiz_red(self):
        for alan, deger in (("demo", True), ("arm_acik", True), ("fda_kipi", False)):
            onceki = getattr(self.yks, alan)
            setattr(self.yks, alan, deger)
            with self.assertRaises(ValueError):
                self.panel.onizle(30, 40)
            setattr(self.yks, alan, onceki)
        self.saat.simdi += 4
        with self.assertRaises(ValueError):
            self.panel.onizle(30, 40)
        self.yks._ham_gonder.assert_not_called()

    def test_onizlemeden_sonra_yon_degisirse_yukleme_yok(self):
        self.panel.onizle(30, 40)
        self.yks.tel["iha"]["yon"] = 90
        with self.assertRaises(ValueError):
            self.panel.yukle()
        self.yks._ham_gonder.assert_not_called()

    def test_ack_sadece_guclu_ve_dogru_komut(self):
        self.panel.onizle(30, 40)
        self.panel.yukle()
        seq = self.panel.tekrar.mesaj["seq"]
        self.panel.ack(ack(seq, node="iha"))
        self.assertTrue(self.panel.tekrar.bekliyor)
        self.panel.ack(ack(seq, node="iha", ref_tip="CMD", ref_cmd="FDA_HAZIRLA", sonuc="ACCEPTED"))
        self.assertEqual(self.panel.tekrar.durum, "ONAYLANDI")

    def test_hakem_rtl_ayri_ve_varis_oncesi_kapali(self):
        with self.assertRaises(ValueError):
            self.panel.basarili_rtl()
        self.yks.acil_komut.assert_not_called()
        self.yks.arm_acik = True
        self.yks.mod["iha"] = "AUTO"
        self.yks.tel["iha"].update(gorev_durum="ALGI_AKTIF", gorev_id="a" * 32)
        self.panel.basarili_rtl()
        self.yks.acil_komut.assert_called_once_with("RTL", teyit_anahtari="FDA_BASARILI_RTL",
                                                  teyit_metni="HAKEM: GÖREV BAŞARILI → RTL")


class AlgiBaglamaTest(unittest.TestCase):
    def test_kapi_kapaliyken_kamera_okunur_model_calistirilmaz(self):
        import rpi_inference as ri
        from test_faz_b_rpi_ekransiz import _Kamera
        model = SimpleNamespace(predict=Mock())
        kapi = SimpleNamespace(guncelle=lambda: False, durum="HEDEFE_INTIKAL")
        yayinci = Mock()
        with patch.object(ri.cv2, "VideoCapture", return_value=_Kamera(3)), \
                patch.object(ri, "durdurma_istendi", return_value=False):
            sonuc = ri.run_camera(model, 0.5, ekransiz=True, gorev_kapisi=kapi, yayinci=yayinci)
        model.predict.assert_not_called()
        self.assertEqual(sonuc["okunan"], 3)
        self.assertEqual(yayinci.karar.call_count, 3)
        self.assertTrue(all(cagri.args[0] is None for cagri in yayinci.karar.call_args_list))

    def test_publisher_kuyruktaki_eski_acik_rotayi_yayinlamaz(self):
        from iha_sender import KararYayinci
        sender = Mock()
        sender.send_no_route.return_value = (1, set())
        yayinci = KararYayinci(sender, karar_izni=lambda: False)
        yayinci._karari_gonder(1, 0.99, [(1, 2), (3, 4)], 0.1, None)
        sender.send_open_route.assert_not_called()
        sender.send_no_route.assert_called_once()

    def test_yks_gorev_telemetrisi_tanimli_ve_bozuk_tur_elendi(self):
        from yks_gui import heartbeat_telemetrisi_dogrula
        temiz, bozuk = heartbeat_telemetrisi_dogrula(
            dict(gorev_hazir=True, gorev_id="a" * 32, gorev_durum="ALGI_AKTIF"))
        self.assertEqual(bozuk, ())
        self.assertEqual(temiz["gorev_durum"], "ALGI_AKTIF")
        temiz, bozuk = heartbeat_telemetrisi_dogrula(dict(gorev_hazir="True", gorev_durum=[]))
        self.assertEqual(temiz, {})
        self.assertIn("gorev_hazir", bozuk)

    def test_algi_gorev_modulu_repo_kamera_yolunda_bulunur(self):
        import rpi_inference as ri
        self.assertIs(ri._fda_gorev_modulu().AlgiGorevKapisi, gorev.AlgiGorevKapisi)

    def test_kapi_acikken_model_gercek_kamera_yolunda_cagrilir(self):
        import rpi_inference as ri
        from test_faz_b_rpi_ekransiz import _Kamera, _maskeler, _analiz_dizisi
        model = SimpleNamespace(predict=Mock(return_value=[object()]))
        kapi = SimpleNamespace(guncelle=lambda: True, durum="ALGI_AKTIF")
        with patch.object(ri.cv2, "VideoCapture", return_value=_Kamera(3)), \
                patch.object(ri, "durdurma_istendi", return_value=False), \
                patch.object(ri, "get_masks", return_value=_maskeler()), \
                patch.object(ri, "analyze_path", _analiz_dizisi()), \
                patch.object(ri, "_karari_yayinla"), \
                patch.object(ri, "kamera_kareleri", side_effect=lambda cap, ozet: (cap.read()[1] for sira in range(3))):
            ri.run_camera(model, 0.5, ekransiz=True, gorev_kapisi=kapi,
                          canli_olcek=lambda genislik: 0.05)
        self.assertEqual(model.predict.call_count, 3)

    def test_hakem_rtl_ilk_tik_ag_yok_acil_teyidiyle_karismaz(self):
        from test_yks_operator_guvenligi import _acil_arayuz
        from protocol import decode
        yks = _acil_arayuz()
        yks._kanit_yaz = Mock()
        with patch.object(yks, "_acil_tik"):
            yks.acil_komut("RTL")
            yks.acil_komut("RTL", teyit_anahtari="FDA_BASARILI_RTL", teyit_metni="Görev başarılı")
            yks.link.send.assert_not_called()
            yks.acil_komut("RTL", teyit_anahtari="FDA_BASARILI_RTL", teyit_metni="Görev başarılı")
        yks.link.send.assert_called_once()
        self.assertEqual(decode(yks.link.send.call_args.args[0])["cmd"], "RTL")
        self.assertEqual(yks.acil_bekleyen_komut, "RTL")
        self.assertIsNone(yks.acil_ack_zamani)

    def test_jetson_ikizleri_ve_kurulum_modulleri(self):
        for kaynak, hedef in (("comms/fda_gorev.py", "fda_gorev.py"),
                               ("comms/fda_mavlink.py", "fda_mavlink.py"),
                               ("comms/protocol.py", "protocol.py"),
                               ("comms/iha_sender.py", "iha_sender.py"),
                               ("comms/iha_komut_alici.py", "iha_komut_alici.py"),
                               ("codes/rpi_inference.py", "rpi_inference.py")):
            with self.subTest(kaynak=kaynak):
                self.assertEqual((KOK / kaynak).read_text(encoding="utf-8"),
                                 (KOK / "jetson_paket/kod" / hedef).read_text(encoding="utf-8"))
        kilavuz = (KOK / "jetson_paket/JETSON_KILAVUZ.md").read_text(encoding="utf-8")
        self.assertIn("cp kod/fda_gorev.py kod/fda_mavlink.py ~/navitas/comms/", kilavuz)


if __name__ == "__main__":
    unittest.main()
