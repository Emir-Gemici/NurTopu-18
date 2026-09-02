"""Kacan mutantlar icin EKSIK testler (curutucu onerisi). Repo test modulunun
yardimcilarini (_HubKurulum, _tuketici, ...) yeniden kullanir; `seri_hub`
sys.modules'ta ne ise onu sinar (kos_ek.py enjekte eder)."""
import io
import sys
import time
import unittest
from unittest import mock

import serial

import seri_hub as modul
from link import UDPLink
from protocol import FrameReader, command, encode, heartbeat, decode
from test_faz_b_seri_hub import (_HubKurulum, _Yakala, _SahteSaat, _tuketici,
                                 _uc, _seri_cerceve_bekle, _tek_cerceve_dogrula,
                                 SikKoprusu, YEREL, TAVAN_S)


class TestEksik(unittest.TestCase):

    def test_b_iki_ogrenilen_ikisi_de_alir(self):
        """rpi_inference + iha_inis_yayinci ikisi de ogrenilir; YKS'den gelen
        cerceve IKISINE de gider (yalniz son gonderene degil)."""
        a = _tuketici(); b = _tuketici()
        self.addCleanup(a.close); self.addCleanup(b.close)
        k = _HubKurulum(self)
        a.send(encode(heartbeat("iha", seq=1)), k.hub_adr)
        k.tur(2)
        b.send(encode(heartbeat("iha", seq=2)), k.hub_adr)   # b EN SON gonderen
        k.tur(2)
        self.assertEqual({(YEREL, a.port), (YEREL, b.port)}, set(k.hub.ogrenilen))
        mesaj = command("IKA_GO", "ika", seq=5)
        k.yks_yaz(mesaj)
        a_gelen = k.topla(a, 1)
        b_gelen = k.topla(b, 1)
        self.assertEqual(1, len(a_gelen), "ILK ogrenilen (a) cerceve almadi")
        self.assertEqual(1, len(b_gelen), "son ogrenilen (b) cerceve almadi")
        _tek_cerceve_dogrula(self, a_gelen[0], mesaj)
        self.assertEqual(2, k.hub.sayac["fanout_gonderim"])

    def test_c_arizada_dusen_datagram_yeniden_acinca_TELDE_yok(self):
        """Arizada dusurulen PARACHUTE(seq=3), yeniden acmadan sonra seri hatta
        ASLA gorunmez (kuyruk yok) — sayac degil TEL kontrolu."""
        saat = _SahteSaat(1000.0)
        tuketici = _tuketici(); self.addCleanup(tuketici.close)
        kopru2 = SikKoprusu(); self.addCleanup(kopru2.kapat)
        yeni_link = _uc(kopru2); yks2 = _uc(kopru2); self.addCleanup(yks2.close)
        k = _HubKurulum(self, seri_ac=mock.Mock(return_value=yeni_link), saat=saat)
        k.hub_seri.recv = mock.Mock(side_effect=OSError("USB koptu"))
        k.tur()
        self.assertIsNone(k.hub.seri_link)
        tuketici.send(encode(command("PARACHUTE", "iha", seq=3)), k.hub_adr)
        k.tur(2)
        self.assertEqual(1, k.hub.sayac["dusurulen"])
        saat.t += modul.SERI_YENIDEN_ACMA_ARALIGI_S
        k.tur()
        self.assertIs(yeni_link, k.hub.seri_link)
        # taze bir datagram gonder; yks2 seq=4'u gorene dek TUM gelenleri topla
        tuketici.send(encode(command("PARACHUTE", "iha", seq=4)), k.hub_adr)
        with _Yakala(k.log):
            m, hepsi = _seri_cerceve_bekle(yks2, FrameReader(),
                                           lambda x: x.get("seq") == 4,
                                           pompa=k.hub.poll)
        self.assertIsNotNone(m)
        self.assertNotIn(3, [x.get("seq") for x in hepsi],
                         f"bayat (dusurulen) cerceve telde gorundu: {hepsi}")
        self.assertEqual([4], [x.get("seq") for x in hepsi])

    def test_h_yeniden_acmada_yarim_cerceve_atilir(self):
        """Ariza aninda okuyucuda YARIM cerceve var; yeniden acilan hatta gelen
        ilk TAM cerceve bozulmadan fan-out edilir, bozuk=0."""
        saat = _SahteSaat(1000.0)
        statik = _tuketici(); self.addCleanup(statik.close)
        kopru2 = SikKoprusu(); self.addCleanup(kopru2.kapat)
        yeni_link = _uc(kopru2); yks2 = _uc(kopru2); self.addCleanup(yks2.close)
        k = _HubKurulum(self, tuketiciler=[(YEREL, statik.port)],
                        seri_ac=mock.Mock(return_value=yeni_link), saat=saat)
        yarim = encode(heartbeat("yks", seq=1))[:-10]          # newline yok
        k.yks.send(yarim)
        bitis = time.monotonic() + TAVAN_S
        while time.monotonic() < bitis and len(k.hub.okuyucu._buf) < len(yarim):
            k.tur()
        self.assertEqual(yarim, k.hub.okuyucu._buf, "on kosul: yarim cerceve tamponda")
        k.hub_seri.recv = mock.Mock(side_effect=OSError("USB koptu"))
        k.tur()
        saat.t += modul.SERI_YENIDEN_ACMA_ARALIGI_S
        k.tur()
        self.assertIs(yeni_link, k.hub.seri_link)
        mesaj = command("IKA_GO", "ika", seq=8)
        yks2.send(encode(mesaj))
        gelen = k.topla(statik, 1)
        self.assertEqual(1, len(gelen), "yeniden acma sonrasi ilk cerceve gelmedi")
        _tek_cerceve_dogrula(self, gelen[0], mesaj)
        self.assertEqual(0, k.hub.sayac["bozuk"], "eski yarim cerceve yeni akisa bulasti")

    def test_i_ogrenilen_tavani_en_eski_dusurulur_uzun_omurlu_kalir(self):
        """Uzun omurlu tuketici L (arada tazelenir) tavan asilinca DUSMEZ; en
        eski kisa omurlu duser; kume tavanda kalir; L fan-out almaya devam eder."""
        L = _tuketici(); self.addCleanup(L.close)
        k = _HubKurulum(self)
        L.send(encode(heartbeat("iha", seq=0)), k.hub_adr); k.tur(2)
        kisa = []
        for i in range(modul.OGRENILEN_TAVANI + 4):
            u = _tuketici(); self.addCleanup(u.close); kisa.append(u)
            u.send(encode(heartbeat("iha", seq=i + 1)), k.hub_adr); k.tur(2)
            if i % 8 == 7:                       # L arada heartbeat atar (canli)
                L.send(encode(heartbeat("iha", seq=100 + i)), k.hub_adr); k.tur(2)
        L.send(encode(heartbeat("iha", seq=999)), k.hub_adr); k.tur(2)
        self.assertEqual(modul.OGRENILEN_TAVANI, len(k.hub.ogrenilen), "tavan uygulanmadi")
        self.assertIn((YEREL, L.port), k.hub.ogrenilen, "uzun omurlu tuketici dustu")
        self.assertNotIn((YEREL, kisa[0].port), k.hub.ogrenilen, "EN ESKI dusmedi")
        self.assertIn((YEREL, kisa[-1].port), k.hub.ogrenilen, "en yeni dustu")
        log = k.log.getvalue()
        self.assertIn("tavani", log)
        # L HICBIR ZAMAN tahliye edilmemis olmali (tahliye + yeniden ogrenme de
        # arada fan-out kaybidir): tahliye logunda L yok, L bir kez ogrenilmis.
        self.assertNotIn(f"dusuruldu: {YEREL}:{L.port}", log,
                         "uzun omurlu tuketici ARADA tahliye edildi")
        self.assertEqual(1, log.count(f"ogrenildi: {YEREL}:{L.port}"),
                         "L birden fazla kez ogrenildi (arada dusmus)")
        mesaj = command("IKA_GO", "ika", seq=5)
        k.yks_yaz(mesaj)
        self.assertEqual(1, len(k.topla(L, 1)), "L fan-out almadi")

    def test_k_seri_kapaliyken_bos_tur_bekler(self):
        """seri_link None: her poll BOS_TUR_BEKLEME_S bekler (sicak dongu yok)."""
        k = _HubKurulum(self)
        k.hub_seri.recv = mock.Mock(side_effect=OSError("koptu"))
        k.tur()
        self.assertIsNone(k.hub.seri_link)
        k.hub._dur = mock.Mock(wraps=k.hub._dur)
        k.tur(10)
        self.assertEqual(10, k.hub._dur.wait.call_count)
        k.hub._dur.wait.assert_called_with(modul.BOS_TUR_BEKLEME_S)

    def test_m_hedefsiz_fanout_sayilir_ve_kirmizi_loglanir(self):
        k = _HubKurulum(self)
        k.yks_yaz(command("IKA_GO", "ika", seq=5))
        bitis = time.monotonic() + TAVAN_S
        while time.monotonic() < bitis and k.hub.sayac["seri_cerceve"] < 1:
            k.tur()
        self.assertEqual(1, k.hub.sayac["hedefsiz"])
        self.assertEqual(0, k.hub.sayac["fanout_gonderim"])
        self.assertIn("HICBIR tuketici", k.log.getvalue())

    def test_n_fanout_oserror_hub_yasar_sayilir(self):
        statik = _tuketici(); self.addCleanup(statik.close)
        k = _HubKurulum(self, tuketiciler=[(YEREL, statik.port)])
        k.udp.send = mock.Mock(side_effect=OSError("ENOBUFS"))
        k.yks_yaz(command("IKA_GO", "ika", seq=5))
        bitis = time.monotonic() + TAVAN_S
        while time.monotonic() < bitis and k.hub.sayac["seri_cerceve"] < 1:
            k.tur()                              # OSError yukselirse burada patlar
        self.assertEqual(1, k.hub.sayac["fanout_hata"])
        self.assertEqual(0, k.hub.sayac["fanout_gonderim"])
        self.assertIn("yazilamadi", k.log.getvalue())

    def test_p_tek_turda_datagram_patlamasi_hepsi_seriye(self):
        """10 datagram tek poll'da bosaltilir ve HEPSI seriye yazilir."""
        tuketici = _tuketici(); self.addCleanup(tuketici.close)
        k = _HubKurulum(self)
        for i in range(10):
            tuketici.send(encode(heartbeat("iha", seq=i)), k.hub_adr)
        time.sleep(0.05)
        k.tur(1)
        self.assertEqual(10, k.hub.sayac["seri_yazilan"], "tek turda hepsi yazilmadi")
        with _Yakala(k.log):
            m, hepsi = _seri_cerceve_bekle(k.yks, FrameReader(),
                                           lambda x: x.get("seq") == 9, pompa=None)
        self.assertEqual(list(range(10)), [x.get("seq") for x in hepsi])

    def test_u_seri_ac_None_donerse_baglanmaz(self):
        saat = _SahteSaat(1000.0)
        k = _HubKurulum(self, seri_ac=mock.Mock(return_value=None), saat=saat)
        k.hub_seri.recv = mock.Mock(side_effect=OSError("koptu"))
        k.tur()
        saat.t += modul.SERI_YENIDEN_ACMA_ARALIGI_S
        k.tur()
        self.assertIsNone(k.hub.seri_link)
        self.assertEqual(1, k.hub.sayac["yeniden_acma_hatasi"])
        self.assertEqual(0, k.hub.sayac["yeniden_acma"])
        self.assertNotIn("YENIDEN ACILDI", k.log.getvalue())
        k.tur()                                   # aralik dolmadan tekrar YOK
        self.assertEqual(1, k.hub.seri_ac.call_count)


if __name__ == "__main__":
    unittest.main()
