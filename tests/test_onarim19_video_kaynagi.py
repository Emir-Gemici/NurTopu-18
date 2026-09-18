"""ONARIM-19 — video telemetri kaynagi kesfi (comms/video_kaynagi.py).

Kilit davranislar: aday siralamasi, HTTP kokunun /video ucundan dogrulanmasi,
TCP elemesinin akis denemesini ONLEMESI, ayni ucun tekrar tekrar denenmemesi,
ilk CANLI'dan sonra durma, onbellek, kopru komutu ve YKS URL'si.
Gercek SIYI donanimi yok: dogrulayicilar ENJEKTE edilir (sahte), gercek akis
kanitini `ONARIM/ONARIM-19_video_telemetri.md` icindeki canli kosum tasir.
"""
import json
import sys
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "comms"))

import video_kaynagi as vk  # noqa: E402


def _sahte_tcp(acik_ucler, sayac=None):
    def f(host, port, zaman_asimi_s=0.1):
        if sayac is not None:
            sayac.append((host, port))
        return (host, int(port)) in acik_ucler
    return f


def _sahte_akis(canli_urller, sayac=None, arac_yok=False):
    def f(url, zaman_asimi_s=0.1):
        if sayac is not None:
            sayac.append(url)
        if arac_yok:
            return None, {"sebep": "ffprobe yok"}
        if url in canli_urller:
            return True, {"genislik": 1280, "yukseklik": 720, "codec": "h264",
                          "yontem": "sahte"}
        return False, {"sebep": "akis cozulemedi"}
    return f


class AdayUretimi(unittest.TestCase):
    def test_elle_verilen_ilk_sirada(self):
        adaylar = vk.adaylari_uret(elle="rtsp://10.0.0.5:554/x")
        self.assertEqual(adaylar[0].url, "rtsp://10.0.0.5:554/x")
        self.assertEqual(adaylar[0].tur, vk.TUR_RTSP)
        self.assertEqual(adaylar[0].host, "10.0.0.5")
        self.assertEqual(adaylar[0].port, 554)

    def test_hatirlanan_elleden_sonra_digerlerinden_once(self):
        adaylar = vk.adaylari_uret(elle="rtsp://a:1/x", hatirlanan="rtsp://b:2/y")
        self.assertEqual([a.url for a in adaylar[:2]], ["rtsp://a:1/x", "rtsp://b:2/y"])

    def test_hatirlanan_elleyle_ayniysa_tekrarlanmaz(self):
        adaylar = vk.adaylari_uret(elle="rtsp://a:1/x", hatirlanan="rtsp://a:1/x")
        self.assertEqual(sum(1 for a in adaylar if a.url == "rtsp://a:1/x"), 1)

    def test_url_ler_tekil(self):
        adaylar = vk.adaylari_uret(jetson_ip=vk.JETSON_SIYI_IP)
        urller = [a.url for a in adaylar]
        self.assertEqual(len(urller), len(set(urller)))

    def test_cihaz_adaylari_varsayilan_kapali(self):
        """PC'nin kendi web kamerasi da /dev/video0'dir: istenmeden taranmaz."""
        adaylar = vk.adaylari_uret()
        self.assertFalse([a for a in adaylar if a.tur == vk.TUR_CIHAZ])
        acik = vk.adaylari_uret(cihaz_da=True,
                                cihaz_listele=lambda: ["video0", "video2"])
        self.assertEqual([a.url for a in acik if a.tur == vk.TUR_CIHAZ],
                         ["/dev/video0", "/dev/video2"])

    def test_oncelik_sirali(self):
        adaylar = vk.adaylari_uret(elle="rtsp://a:1/x")
        oncelikler = [a.oncelik for a in adaylar]
        self.assertEqual(oncelikler, sorted(oncelikler))

    def test_kesif_adresi_siyiden_once_denenir(self):
        """Internet/router yokken (link-local) Jetson IP'si yalniz kesiften bilinir."""
        adaylar = vk.adaylari_uret(kesif_ip="169.254.201.50")
        self.assertEqual(adaylar[0].url, "http://169.254.201.50:8081/")
        self.assertIn("KESIFTEN", adaylar[0].aciklama)
        siyi = next(i for i, a in enumerate(adaylar) if a.host == "192.168.144.25")
        self.assertLess(1, siyi)

    def test_kesif_adresi_elleden_sonra(self):
        adaylar = vk.adaylari_uret(elle="rtsp://a:1/x", kesif_ip="169.254.201.50")
        self.assertEqual(adaylar[0].url, "rtsp://a:1/x")
        self.assertEqual(adaylar[1].url, "http://169.254.201.50:8081/")

    def test_kesif_ipsiz_eski_davranis(self):
        adaylar = vk.adaylari_uret(jetson_ip="10.21.8.7")
        self.assertTrue(any(a.url.startswith("http://10.21.8.7:") for a in adaylar))
        self.assertFalse(any("KESIFTEN" in a.aciklama for a in adaylar))

    def test_siyi_ana_yolu_once(self):
        adaylar = [a for a in vk.adaylari_uret() if a.host == "192.168.144.25"]
        self.assertTrue(adaylar[0].url.endswith(vk.SIYI_RTSP_YOLLARI[0]))


class DogrulamaUcu(unittest.TestCase):
    def test_http_kok_video_ucundan_dogrulanir(self):
        a = vk.Aday("x", "http://1.2.3.4:8081/", vk.TUR_HTTP, 1, "")
        self.assertEqual(a.dogrulama_url, "http://1.2.3.4:8081/video")

    def test_rtsp_url_degismez(self):
        a = vk.Aday("x", "rtsp://1.2.3.4:8554/main.264", vk.TUR_RTSP, 1, "")
        self.assertEqual(a.dogrulama_url, "rtsp://1.2.3.4:8554/main.264")

    def test_acik_dogrulama_url_ustundur(self):
        a = vk.Aday("x", "http://h/", vk.TUR_HTTP, 1, "", dogrulama_url="http://h/ozel")
        self.assertEqual(a.dogrulama_url, "http://h/ozel")


class Tarama(unittest.TestCase):
    def test_kapali_port_akisi_hic_denemez(self):
        akis_sayac = []
        adaylar = [vk.Aday("a", "rtsp://1.1.1.1:8554/x", vk.TUR_RTSP, 1, "",
                           host="1.1.1.1", port=8554)]
        sonuclar = vk.tara(adaylar, tcp_dene_f=_sahte_tcp(set()),
                           akis_dogrula_f=_sahte_akis(set(), akis_sayac))
        self.assertEqual(sonuclar[0].durum, vk.DURUM_PORT_KAPALI)
        self.assertEqual(akis_sayac, [])

    def test_acik_port_ama_akis_yok(self):
        adaylar = [vk.Aday("a", "rtsp://1.1.1.1:8554/x", vk.TUR_RTSP, 1, "",
                           host="1.1.1.1", port=8554)]
        sonuclar = vk.tara(adaylar, tcp_dene_f=_sahte_tcp({("1.1.1.1", 8554)}),
                           akis_dogrula_f=_sahte_akis(set()))
        self.assertEqual(sonuclar[0].durum, vk.DURUM_AKIS_YOK)
        self.assertFalse(sonuclar[0].canli)

    def test_canli_bulunur_ve_kalanlar_atlanir(self):
        adaylar = [
            vk.Aday("a", "rtsp://1.1.1.1:8554/x", vk.TUR_RTSP, 1, "", host="1.1.1.1", port=8554),
            vk.Aday("b", "rtsp://1.1.1.1:8554/y", vk.TUR_RTSP, 2, "", host="1.1.1.1", port=8554),
            vk.Aday("c", "rtsp://2.2.2.2:8554/z", vk.TUR_RTSP, 3, "", host="2.2.2.2", port=8554),
        ]
        sonuclar = vk.tara(adaylar, tcp_dene_f=_sahte_tcp({("1.1.1.1", 8554)}),
                           akis_dogrula_f=_sahte_akis({"rtsp://1.1.1.1:8554/y"}))
        self.assertEqual([s.durum for s in sonuclar],
                         [vk.DURUM_AKIS_YOK, vk.DURUM_CANLI, vk.DURUM_ATLANDI])
        self.assertEqual(vk.sec(sonuclar).aday.ad, "b")

    def test_tam_envanterde_atlanmaz(self):
        adaylar = [
            vk.Aday("a", "rtsp://1.1.1.1:8554/x", vk.TUR_RTSP, 1, "", host="1.1.1.1", port=8554),
            vk.Aday("b", "rtsp://1.1.1.1:8554/y", vk.TUR_RTSP, 2, "", host="1.1.1.1", port=8554),
        ]
        sonuclar = vk.tara(adaylar, tcp_dene_f=_sahte_tcp({("1.1.1.1", 8554)}),
                           akis_dogrula_f=_sahte_akis({"rtsp://1.1.1.1:8554/x"}),
                           ilk_bulunanda_dur=False)
        self.assertEqual([s.durum for s in sonuclar], [vk.DURUM_CANLI, vk.DURUM_AKIS_YOK])

    def test_ayni_uc_bir_kez_denenir(self):
        """Bes RTSP yolu ayni host:port'tadir; TCP elemesi bes kez kosmaz."""
        tcp_sayac = []
        adaylar = [vk.Aday("a%d" % i, "rtsp://1.1.1.1:8554/y%d" % i, vk.TUR_RTSP, i, "",
                           host="1.1.1.1", port=8554) for i in range(5)]
        vk.tara(adaylar, tcp_dene_f=_sahte_tcp(set(), tcp_sayac),
                akis_dogrula_f=_sahte_akis(set()))
        self.assertEqual(tcp_sayac, [("1.1.1.1", 8554)])

    def test_arac_yoksa_arac_yok_durumu(self):
        adaylar = [vk.Aday("a", "rtsp://1.1.1.1:8554/x", vk.TUR_RTSP, 1, "",
                           host="1.1.1.1", port=8554)]
        sonuclar = vk.tara(adaylar, tcp_dene_f=_sahte_tcp({("1.1.1.1", 8554)}),
                           akis_dogrula_f=_sahte_akis(set(), arac_yok=True))
        self.assertEqual(sonuclar[0].durum, vk.DURUM_ARAC_YOK)
        self.assertIsNone(vk.sec(sonuclar))

    def test_udp_adayinda_tcp_elemesi_yok(self):
        tcp_sayac = []
        adaylar = [vk.Aday("u", "udp://1.1.1.1:37256", vk.TUR_UDP, 1, "",
                           host="1.1.1.1", port=37256)]
        sonuclar = vk.tara(adaylar, tcp_dene_f=_sahte_tcp(set(), tcp_sayac),
                           akis_dogrula_f=_sahte_akis({"udp://1.1.1.1:37256"}))
        self.assertEqual(tcp_sayac, [])
        self.assertTrue(sonuclar[0].canli)

    def test_sonuc_sozlugu_kanit_tasir(self):
        adaylar = [vk.Aday("a", "rtsp://1.1.1.1:8554/x", vk.TUR_RTSP, 1, "aciklama",
                           host="1.1.1.1", port=8554)]
        s = vk.tara(adaylar, tcp_dene_f=_sahte_tcp({("1.1.1.1", 8554)}),
                    akis_dogrula_f=_sahte_akis({"rtsp://1.1.1.1:8554/x"}))[0].sozluk()
        self.assertEqual(s["durum"], vk.DURUM_CANLI)
        self.assertEqual(s["ayrinti"]["genislik"], 1280)
        self.assertIn("yontem", s["ayrinti"])


class Onbellek(unittest.TestCase):
    def test_yaz_oku(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            yol = str(Path(d) / "alt" / "video.json")
            self.assertTrue(vk.hatirla(yol, "rtsp://x/y"))
            self.assertEqual(vk.hatirlanan_oku(yol), "rtsp://x/y")

    def test_bozuk_dosya_none(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            yol = Path(d) / "v.json"
            yol.write_text("{bozuk", encoding="utf-8")
            self.assertIsNone(vk.hatirlanan_oku(str(yol)))

    def test_olmayan_dosya_none(self):
        self.assertIsNone(vk.hatirlanan_oku("/olmayan/dizin/yok.json"))

    def test_kesfet_bulunca_hatirlar(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            yol = str(Path(d) / "v.json")
            hedef = "rtsp://192.168.144.25:8554/" + vk.SIYI_RTSP_YOLLARI[0]
            secilen, _ = vk.kesfet(
                onbellek=yol,
                tcp_dene_f=_sahte_tcp({("192.168.144.25", vk.SIYI_RTSP_PORT)}),
                akis_dogrula_f=_sahte_akis({hedef}))
            self.assertIsNotNone(secilen)
            self.assertEqual(vk.hatirlanan_oku(yol), hedef)

    def test_kesfet_bulamazsa_onbellek_bozulmaz(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            yol = str(Path(d) / "v.json")
            vk.hatirla(yol, "rtsp://eski/yol")
            secilen, _ = vk.kesfet(onbellek=yol, tcp_dene_f=_sahte_tcp(set()),
                                   akis_dogrula_f=_sahte_akis(set()))
            self.assertIsNone(secilen)
            self.assertEqual(vk.hatirlanan_oku(yol), "rtsp://eski/yol")


class YksBaglama(unittest.TestCase):
    def test_http_kaynagi_kopru_istemez(self):
        a = vk.Aday("j", "http://10.0.0.9:8081/", vk.TUR_HTTP, 1, "")
        self.assertFalse(vk.kopru_gerekli(a))
        self.assertEqual(vk.yks_kamera_url(a), "http://10.0.0.9:8081/")

    def test_rtsp_kaynagi_kopruye_gider(self):
        a = vk.Aday("s", "rtsp://192.168.144.25:8554/main.264", vk.TUR_RTSP, 1, "")
        self.assertTrue(vk.kopru_gerekli(a))
        self.assertEqual(vk.yks_kamera_url(a, port=8090), "http://127.0.0.1:8090/")

    def test_kopru_komutu_gercek_betigi_gosterir(self):
        a = vk.Aday("s", "rtsp://192.168.144.25:8554/main.264", vk.TUR_RTSP, 1, "")
        komut = vk.kopru_komutu(a, port=8090, yorumlayici="PY", kok=KOK)
        self.assertEqual(komut[0], "PY")
        self.assertTrue(Path(komut[1]).exists(), "kopru betigi bulunamadi: %s" % komut[1])
        self.assertEqual(komut[2:], ["--kaynak", "rtsp://192.168.144.25:8554/main.264",
                                     "--port", "8090"])

    def test_cihaz_kaynagi_da_koprulenir(self):
        a = vk.Aday("c", "/dev/video3", vk.TUR_CIHAZ, 1, "")
        self.assertTrue(vk.kopru_gerekli(a))


class CliKuru(unittest.TestCase):
    def test_liste_hicbir_sey_denemez(self):
        import io
        import contextlib
        tampon = io.StringIO()
        with contextlib.redirect_stdout(tampon):
            kod = vk.main(["--liste", "--json", "--onbellek-yok"])
        self.assertEqual(kod, 0)
        veri = json.loads(tampon.getvalue())
        self.assertTrue(veri)
        self.assertIn("dogrulama_url", veri[0])

class YksGuiEntegrasyonu(unittest.TestCase):
    """`--video-tara`: YKS video kaynagini bulup baglar; BULAMAZSA YKS bozulmaz."""

    @classmethod
    def setUpClass(cls):
        try:
            import yks_gui
        except Exception as exc:                       # pragma: no cover
            raise unittest.SkipTest("yks_gui iceri alinamadi: %s" % exc)
        cls.yg = yks_gui

    def _args(self, **ek):
        import types
        d = {"kamera_url": None, "iha": None, "video_tara": True}
        d.update(ek)
        return types.SimpleNamespace(**d)

    def _sonuc(self, aday, ayrinti=None):
        return vk.Sonuc(aday, vk.DURUM_CANLI, "akis cozuldu",
                        ayrinti or {"genislik": 1280, "yukseklik": 720,
                                    "codec": "h264", "yontem": "sahte"})

    def test_bulunamazsa_video_kapali_ve_kirmizi_degil_sari(self):
        url, gunluk, surec = self.yg.video_kaynagini_hazirla(
            self._args(), kesfet=lambda **k: (None, []))
        self.assertIsNone(url)
        self.assertIsNone(surec)
        self.assertEqual(gunluk[0][1], "sari")
        self.assertIn("ETKİLENMEZ", gunluk[0][0])

    def test_http_kaynagi_kopru_acmaz(self):
        aday = vk.Aday("j", "http://169.254.201.50:8081/", vk.TUR_HTTP, 1, "Jetson")
        acildi = []
        url, gunluk, surec = self.yg.video_kaynagini_hazirla(
            self._args(),
            kesfet=lambda **k: (self._sonuc(aday), [self._sonuc(aday)]),
            kopru_ac=lambda *a, **k: acildi.append(a) or object())
        self.assertEqual(url, "http://169.254.201.50:8081/")
        self.assertIsNone(surec)
        self.assertEqual(acildi, [])

    def test_rtsp_kaynagi_kopru_acar(self):
        aday = vk.Aday("s", "rtsp://192.168.144.25:8554/main.264", vk.TUR_RTSP, 1, "SIYI")
        komutlar = []

        class SahteSurec:
            def poll(self):
                return None

        url, gunluk, surec = self.yg.video_kaynagini_hazirla(
            self._args(),
            kesfet=lambda **k: (self._sonuc(aday), [self._sonuc(aday)]),
            kopru_ac=lambda komut, **k: komutlar.append(komut) or SahteSurec())
        self.assertEqual(url, "http://127.0.0.1:%d/" % vk.VARSAYILAN_KOPRU_PORT)
        self.assertIsNotNone(surec)
        self.assertIn("--kaynak", komutlar[0])
        self.assertIn(aday.url, komutlar[0])

    def test_tarama_patlarsa_yks_yasar(self):
        def patla(**k):
            raise RuntimeError("ag yok")
        url, gunluk, surec = self.yg.video_kaynagini_hazirla(self._args(), kesfet=patla)
        self.assertIsNone(url)
        self.assertIsNone(surec)
        self.assertEqual(gunluk[0][1], "kirmizi")

    def test_kopru_acilamazsa_video_kapali(self):
        aday = vk.Aday("s", "rtsp://1.2.3.4:8554/x", vk.TUR_RTSP, 1, "")

        def patla(*a, **k):
            raise OSError("betik yok")
        url, gunluk, surec = self.yg.video_kaynagini_hazirla(
            self._args(), kesfet=lambda **k: (self._sonuc(aday), [self._sonuc(aday)]),
            kopru_ac=patla)
        self.assertIsNone(url)
        self.assertIsNone(surec)
        self.assertEqual(gunluk[-1][1], "kirmizi")

    def test_iha_adresi_kesif_ipsi_olarak_gecer(self):
        gorulen = {}

        def kesfet(**k):
            gorulen.update(k)
            return None, []
        self.yg.video_kaynagini_hazirla(self._args(iha=("169.254.201.50", 5009)),
                                        kesif_ip="169.254.201.50", kesfet=kesfet)
        self.assertEqual(gorulen.get("kesif_ip"), "169.254.201.50")

    def test_kamera_url_elle_aday_olarak_gecer(self):
        gorulen = {}

        def kesfet(**k):
            gorulen.update(k)
            return None, []
        self.yg.video_kaynagini_hazirla(self._args(kamera_url="rtsp://x/y"), kesfet=kesfet)
        self.assertEqual(gorulen.get("elle"), "rtsp://x/y")

    def test_kopru_kapatici_terminate_cagirir(self):
        olaylar = []

        class SahteSurec:
            def poll(self):
                return None

            def terminate(self):
                olaylar.append("terminate")

            def wait(self, timeout=None):
                olaylar.append("wait")

        self.yg._video_koprusunu_kapat(SahteSurec())
        self.assertEqual(olaylar, ["terminate", "wait"])

    def test_zaten_bitmis_surece_dokunmaz(self):
        olaylar = []

        class Bitmis:
            def poll(self):
                return 0

            def terminate(self):
                olaylar.append("terminate")

        self.yg._video_koprusunu_kapat(Bitmis())
        self.assertEqual(olaylar, [])

if __name__ == "__main__":
    unittest.main()
