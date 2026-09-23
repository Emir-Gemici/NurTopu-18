"""NEDEN: Videosuz tek-rota incelemesi geometri uydurmadan hakem onayına dayanmalıdır."""

import copy
from functools import partial
import io
import json
import math
from pathlib import Path
import sys
import time
import unittest
from unittest import mock

KOK = Path(__file__).resolve().parents[1]
for dizin in ("comms", "tests", "scripts"):
    sys.path.insert(0, str(KOK / dizin))

from rota_inceleme import rota_plani
import yks_gui
from protocol import open_route, heartbeat, rota_yok, ack, encode
from test_yks_mk15_hakem_ekrani import _GercekEkran
import saha_baslat


def paket(seq=9123):
    return open_route(3, .91, ref_xy=[-4, 7],
                      waypoints=[[0, 0], [1, 0], [1, 1], [2, 1]], seq=seq)


class RotaHesabi(unittest.TestCase):
    def test_saha_baslatici_tek_rota_aktarir(self):
        komut = saha_baslat.komut_uret("yks", iha="127.0.0.2:5007", tek_rota=True)
        self.assertIn("--tek-rota", komut)
        self.assertNotIn("--fda", komut)
        self.assertIn("--fda", saha_baslat.komut_uret("yks", fda=True))
        with self.assertRaises(ValueError):
            saha_baslat.komut_uret("ika", tek_rota=True)

    def test_ref_sadece_bir_kez_eklenir_serit_ofseti_yok(self):
        plan = rota_plani(paket())
        self.assertEqual(plan["noktalar"], [(-4, 7), (-3, 7), (-3, 8), (-2, 8)])
        self.assertEqual(plan["toplam"], 3)

    def test_numara_geometriyi_degistirmez(self):
        once = rota_plani(paket())
        degisik = paket()
        degisik["road"] = 1
        self.assertEqual(once, rota_plani(degisik))

    def test_sol_sag_donus_ve_ilk_yon_bilinmiyor(self):
        adimlar = rota_plani(paket())["adimlar"]
        self.assertIsNone(adimlar[1]["donus"])
        self.assertIn("bilinmiyor", adimlar[1]["hareket"])
        self.assertEqual(adimlar[2]["donus"], 90)
        self.assertIn("sola", adimlar[2]["hareket"])
        self.assertEqual(adimlar[3]["donus"], -90)
        self.assertIn("sağa", adimlar[3]["hareket"])

    def test_tekrar_nokta_yonu_sifirlamaz(self):
        mesaj = paket()
        mesaj["waypoints"].insert(2, [1, 0])
        adimlar = rota_plani(mesaj)["adimlar"]
        self.assertIsNone(adimlar[2]["yon"])
        self.assertEqual(adimlar[3]["donus"], 90)

    def test_paket_degistirilmez_ve_ozet_geometriye_baglidir(self):
        mesaj = paket()
        eski = copy.deepcopy(mesaj)
        plan = rota_plani(mesaj)
        self.assertEqual(mesaj, eski)
        mesaj["waypoints"][-1][0] += .1
        self.assertNotEqual(plan["sha256"], rota_plani(mesaj)["sha256"])

    def test_gecersiz_koordinatlar_reddedilir(self):
        for kotu in (None, [0], [True, 0], [float("nan"), 0], [0, float("inf")], ["1", 0]):
            with self.subTest(kotu=kotu), self.assertRaises(ValueError):
                mesaj = paket()
                mesaj["ref_xy"] = kotu
                rota_plani(mesaj)

    def test_noktasiz_tek_noktali_ve_durgun_reddedilir(self):
        for noktalar in ([], [[0, 0]], [[0, 0], [0, 0]]):
            with self.subTest(noktalar=noktalar), self.assertRaises(ValueError):
                mesaj = paket()
                mesaj["waypoints"] = noktalar
                rota_plani(mesaj)

    def test_uretici_geometri_sinirlari_korunur(self):
        mesaj = paket()
        mesaj["waypoints"][1] = [40, 0]
        with self.assertRaises(ValueError):
            rota_plani(mesaj)

    def test_artieksi_180_siniri(self):
        mesaj = paket()
        mesaj["waypoints"] = [[0, 0], [-1, .01], [-2, 0]]
        aci = rota_plani(mesaj)["adimlar"][2]["donus"]
        self.assertLess(abs(aci), 2)


class VideosuzHakem(_GercekEkran):
    def _tek_kur(self):
        with mock.patch.object(yks_gui, "YksArayuz", partial(yks_gui.YksArayuz, tek_rota=True)):
            arayuz = self._kur()
        arayuz.gorunum("rota")
        self.kok.update()
        return arayuz

    def _gonder(self, mesaj):
        self.iha.send(encode(mesaj), self.hedef)
        self.assertTrue(self._pompala(lambda: self.app.rota is not None and self.app.rota["seq"] == mesaj["seq"]))
        self._hb_gonder()
        self.app._rota_panelini_tazele()
        self.kok.update()

    def test_gercek_udp_rota_tablosu_ve_tek_cizgi(self):
        app = self._tek_kur()
        self._gonder(paket())
        panel = app.rota_paneli
        self.assertEqual(4, len(panel.tablo.get_children()))
        self.assertEqual(str(panel.tablo.item("3", "values")[1]), "-3.00")
        self.assertEqual(panel.plan["noktalar"], rota_plani(paket())["noktalar"])
        self.assertEqual("TEK ROTA", app.lbl_karar.cget("text"))
        app.gorunum("harita")
        self.kok.update()
        metinler = [app.harita.itemcget(kimlik, "text") for kimlik in app.harita.find_all() if app.harita.type(kimlik) == "text"]
        self.assertFalse(any("KAPALI" in metin or "ORTA" in metin or "ŞERİT" in metin for metin in metinler))
        panel.sec(3)
        self.assertIn("90.0° sola", panel.detay.cget("text"))

    def test_video_yoksa_plan_gorunur_ve_fda_onayi_kilitleri_korunur(self):
        app = self._tek_kur()
        app.fda_kipini_uygula()
        app.gorunum("kamera")
        self._gonder(paket())
        self.assertEqual("pack", app.videosuz_rota.winfo_manager())
        self.assertEqual("", app.lbl_kamera_img.winfo_manager())
        self.assertIsNotNone(app.videosuz_rota.plan)
        app.onayla()
        self.assertTrue(app.tespit_onayli)
        app.onayla()
        self.assertTrue(app.onaylandi)
        mesajlar = self._al(self.iha)
        self.assertTrue(any(mesaj.get("type") == "ACK" and mesaj.get("ref") == paket()["seq"] for mesaj in mesajlar))
        self.assertFalse(app.ika_rota_ack)
        self.assertEqual("disabled", str(app.btn_ika_go.cget("state")))
        app.hakem_kaydi.kapat()
        satirlar = [json.loads(satir) for satir in self.log_yolu.read_text(encoding="utf-8").splitlines()]
        onay = next(satir for satir in satirlar if satir["olay"] == "HAKEM_ONAYI_2")
        self.assertEqual(onay["rota_sha256"], rota_plani(paket())["sha256"])
        self.assertEqual(onay["waypoints"], paket()["waypoints"])

    def test_veri_ve_video_yoksa_rota_ve_onay_yok(self):
        app = self._tek_kur()
        app.gorunum("kamera")
        self.kok.update()
        self.assertIsNone(app.videosuz_rota.plan)
        app.onayla()
        self.assertFalse(app.onaylandi)
        self.assertEqual("disabled", str(app.btn_onay.cget("state")))

    def test_ret_gelince_eski_rota_ve_adimlar_silinir(self):
        app = self._tek_kur()
        self._gonder(paket())
        mesaj = rota_yok("MASKE_YOK", seq=9124)
        self.iha.send(encode(mesaj), self.hedef)
        self.assertTrue(self._pompala(lambda: app.rota_yok is not None))
        self.assertIsNone(app.rota_paneli.plan)
        self.assertFalse(app.rota_paneli.tablo.get_children())
        self.assertFalse(app.rota_paneli.harita.find_withtag("rota"))

    def test_bayat_plan_sari_ve_onay_kapali(self):
        app = self._tek_kur()
        self._gonder(paket())
        app.karar_yas_rx = (yks_gui.YKS_TESPIT_TAZELIK_S + 1, time.monotonic())
        app._durum_tazele()
        self.assertIn("ESKİ PLAN", app.rota_paneli.durum)
        self.assertEqual("disabled", str(app.btn_onay.cget("state")))
        app.onayla()
        self.assertFalse(app.onaylandi)

    def test_ayni_seq_degisik_geometri_onayi_tasiyamaz(self):
        app = self._tek_kur()
        app.fda_kipini_uygula()
        self._gonder(paket())
        app.onayla()
        app.onayla()
        yeni = paket()
        yeni["waypoints"][-1][0] += .1
        self.iha.send(encode(yeni), self.hedef)
        self.assertTrue(self._pompala(lambda: not app.onaylandi))
        self.assertFalse(app.tespit_onayli)
        self.assertEqual(app.rota_paneli.plan["sha256"], rota_plani(yeni)["sha256"])

    def test_yarisma_kipinde_ika_ack_olmadan_ikinci_onay_yok(self):
        app = self._tek_kur()
        self._gonder(paket())
        app.onayla()
        app.onayla()
        self.assertTrue(app.tespit_onayli)
        self.assertFalse(app.onaylandi)

    def test_gecersiz_geometri_dogrudan_onayla_ile_gecemez(self):
        app = self._tek_kur()
        self._gonder(paket())
        app.rota["waypoints"] = [[0, 0], [40, 0]]
        app._onay_dugmesini_ciz(True, "TEST")
        self.assertEqual("disabled", str(app.btn_onay.cget("state")))
        app.onayla()
        self.assertFalse(app.tespit_onayli)

    def test_video_geri_gelince_ve_tekrar_kopunca(self):
        from PIL import Image

        app = self._tek_kur()
        app.gorunum("kamera")
        self._gonder(paket())
        resim = io.BytesIO()
        Image.new("RGB", (4, 4)).save(resim, format="JPEG")
        app.kamera_istemci = mock.Mock()
        app.kamera_istemci.snapshot.return_value = {
            "jpeg": resim.getvalue(), "surum": 1, "durum": "CANLI", "kare_yasi_s": 0}
        app._kamera_tazele()
        self.assertFalse(app._videosuz_rota_acik)
        self.assertEqual("pack", app.lbl_kamera_img.winfo_manager())
        self.assertEqual("pack", app.mini_harita_cerceve.winfo_manager())
        app.kamera_istemci.snapshot.return_value = {"jpeg": None, "surum": 2, "durum": "KOPUK"}
        app._kamera_tazele()
        self.assertTrue(app._videosuz_rota_acik)
        self.assertEqual("", app.lbl_kamera_img.winfo_manager())
        self.assertIsNone(app._kamera_foto)
        self.assertEqual(app.videosuz_rota.plan["sha256"], rota_plani(paket())["sha256"])


if __name__ == "__main__":
    unittest.main()
