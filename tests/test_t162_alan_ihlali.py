"""T162 KAPISI (ON_KAYIT SS28 · REVIEW_LOG D-307): sartname SS6.2/SS6.4
"ALAN IHLALI" denetimi sahada GERCEKTEN calisiyor mu?

KUSUR (sartname bosluk raporu R17): `comms/yks_gui.py` IHA-UB tasmasini
heartbeat'teki `x`,`y` ile denetliyordu, ama URETIMDE o alanlari ureten hicbir
yol YOKTU (`iha_sender.send_heartbeat` yalniz node/seq/t yolluyordu). Yani kapi
sahada HIC ates almazdi: OLU KAPI. Ayrica `300` GUI'de UC YERDE ciplak sabitti
(madde 16).

BOS KAPI YASAGI (TEST_SPECS SS4.1): "alan eklendi" demek yetmez. Kapi
  (a) argumansiz heartbeat'in ALAN KUMESININ degismedigini,
  (b) INIS KANITI yolunun lat/lon bozuksa bile DEGISMEDIGINI,
  (c) uctan uca sahte GLOBAL_POSITION_INT ile x,y'nin GERCEKTEN yayina
      girdigini ve sinir disinda ihlal uretildigini,
  (d) referans yoksa alanin YAZILMADIGINI ve sabit mutasyonunda testin
      DUSTUGUNU
kanitlar.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
for _y in (KOK / "comms", KOK / "codes"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

import inis_kaniti                                   # noqa: E402
import protocol                                      # noqa: E402
from karar_sozlesmesi import (ALAN_IHLALI_SEBEBI,     # noqa: E402
                              SARTNAME_IHA_UB_KENAR_M, iha_ub_ihlali,
                              yerel_konum_m)


class SahteMesaj:
    """GLOBAL_POSITION_INT'in kullandigimiz en kucuk arayuzu."""

    def __init__(self, relative_alt, time_boot_ms, sysid, lat=None, lon=None):
        self.relative_alt = relative_alt
        self.time_boot_ms = time_boot_ms
        self._sysid = sysid
        if lat is not None:
            self.lat = lat
        if lon is not None:
            self.lon = lon

    def get_type(self):
        return "GLOBAL_POSITION_INT"

    def get_srcSystem(self):
        return self._sysid


class SahteMav:
    def __init__(self, mesajlar):
        self._mesajlar = list(mesajlar)

    def recv_match(self, type=None, blocking=False):
        del type, blocking
        return self._mesajlar.pop(0) if self._mesajlar else None


def _okuyucu(mesajlar, sysid=1, tazelik=5.0):
    return inis_kaniti.BagilIrtifaOkuyucu(SahteMav(mesajlar), tazelik,
                                          beklenen_sysid=sysid)


# --------------------------------------------- (a) BOZULMAMA (protokol)
class ProtokolBayutEs(unittest.TestCase):

    def test_argumansiz_heartbeat_alan_kumesi_AYNI(self):
        m = protocol.heartbeat("iha", seq=7)
        self.assertEqual({"v", "type", "node", "seq", "t"}, set(m))

    def test_None_alan_YAZILMAZ(self):
        m = protocol.heartbeat("iha", seq=7, x=None, y=None)
        self.assertNotIn("x", m)
        self.assertNotIn("y", m)

    def test_sozlesme_disi_alan_REDDEDILIR(self):
        with self.assertRaises(ValueError):
            protocol.heartbeat("iha", seq=7, konum=[1, 2])

    def test_x_y_verilince_yazilir(self):
        m = protocol.heartbeat("iha", seq=7, x=12.5, y=-3.25)
        self.assertEqual(12.5, m["x"])
        self.assertEqual(-3.25, m["y"])


# --------------------------------------------- (b) INIS KANITI DOKUNULMAZ
class InisKanitiDegismedi(unittest.TestCase):
    """lat/lon bozuk/eksik olsa bile irtifa yolu AYNEN calisir."""

    def _olc(self, **kw):
        o = _okuyucu([SahteMesaj(12_000, 10, 1, **kw)])
        self.assertTrue(o.oku())
        return o.irtifa_m(), o.konum_derece()

    def test_konum_yokken_irtifa_AYNI(self):
        irtifa, konum = self._olc()
        self.assertAlmostEqual(12.0, irtifa)
        self.assertIsNone(konum, "lat/lon yokken konum uretildi")

    def test_konum_BOZUKKEN_irtifa_AYNI(self):
        bozuklar = ({"lat": "x", "lon": 0},
                    {"lat": True, "lon": 0},
                    {"lat": 10 ** 12, "lon": 0},
                    {"lat": float("nan"), "lon": 0})
        for bozuk in bozuklar:
            with self.subTest(bozuk=sorted(bozuk)):
                irtifa, konum = self._olc(**bozuk)
                self.assertAlmostEqual(12.0, irtifa,
                                       msg="bozuk konum IRTIFAYI etkiledi")
                self.assertIsNone(konum)

    def test_saglam_konum_okunur(self):
        irtifa, konum = self._olc(lat=399_250_000, lon=328_660_000)
        self.assertAlmostEqual(12.0, irtifa)
        self.assertIsNotNone(konum)
        self.assertAlmostEqual(39.925, konum[0], places=6)
        self.assertAlmostEqual(32.866, konum[1], places=6)

    def test_bayat_ornekte_konum_da_None(self):
        """Tazelik sozlesmesi irtifayla AYNI — ayrisamaz."""
        o = _okuyucu([SahteMesaj(12_000, 10, 1,
                                 lat=399_250_000, lon=328_660_000)],
                     tazelik=1e-6)
        o.oku()
        self.assertIsNone(o.irtifa_m())
        self.assertIsNone(o.konum_derece())


# --------------------------------------------- (c) UCTAN UCA
class UctanUca(unittest.TestCase):

    def test_yayinci_x_y_tasiyor_ve_ihlal_uretiliyor(self):
        import rpi_inference as ri

        ref = (39.925, 32.866)
        okuyucu = _okuyucu([SahteMesaj(30_000, 10, 1,
                                       lat=int(39.9268 * 1e7),
                                       lon=int(32.8695 * 1e7))])
        self.assertTrue(okuyucu.oku())

        class SahteOlcek:
            pass

        olcek = SahteOlcek()
        olcek.okuyucu = okuyucu

        saglayici = ri._ub_konum_saglayici(olcek, ref)
        self.assertIsNotNone(saglayici, "konum saglayici kurulmadi")
        xy = saglayici()
        self.assertIsNotNone(xy, "saglayici konum uretmedi")
        self.assertIsNone(iha_ub_ihlali(*xy), f"ic nokta ihlal sayildi: {xy}")

        uzak = yerel_konum_m(ref[0], ref[1], ref[0] + 0.01, ref[1])
        ihlal = iha_ub_ihlali(*uzak)
        self.assertIsNotNone(ihlal, f"sinir disi nokta ihlal saymadi: {uzak}")
        self.assertEqual(ALAN_IHLALI_SEBEBI, ihlal[0])

    def test_referans_yoksa_saglayici_KURULMAZ(self):
        import rpi_inference as ri
        self.assertIsNone(ri._ub_konum_saglayici(object(), None))

    def test_okuyucusuz_olcekte_saglayici_KURULMAZ(self):
        import rpi_inference as ri
        self.assertIsNone(ri._ub_konum_saglayici(object(), (39.9, 32.8)))

    @staticmethod
    def _bir_heartbeat(konum_saglayici):
        """URETIM dongusunu GERCEKTEN kosar; ilk cagrida durdurur.

        ⚠ `send_heartbeat`i elle cagirmak KANIT DEGILDIR (bos kapi): kanitlanmasi
        gereken sey `KararYayinci._heartbeat_dongusu`nun konumu ALIP gecirmesidir.
        """
        import iha_sender
        cagrilar = []
        y = iha_sender.KararYayinci.__new__(iha_sender.KararYayinci)

        class SahteGonderici:
            def send_heartbeat(_self, node="iha", **kw):
                cagrilar.append(kw)
                y._dur.set()           # tek tur: dongu bir kez donsun
                return 1

        import threading
        y.sender = SahteGonderici()
        y.konum_saglayici = konum_saglayici
        y.heartbeat_aralik = 0.001
        y.heartbeat_sayisi = 0
        y.hata = []
        y._dur = threading.Event()
        y._heartbeat_dongusu()
        return cagrilar, y

    def test_URETIM_dongusu_x_y_gecirir(self):
        cagrilar, y = self._bir_heartbeat(lambda: (12.0, 34.0))
        self.assertEqual([{"x": 12.0, "y": 34.0}], cagrilar)
        self.assertEqual(1, y.heartbeat_sayisi)
        self.assertEqual([], y.hata)

    def test_URETIM_dongusu_konum_YOKKEN_alan_yazmaz(self):
        cagrilar, y = self._bir_heartbeat(None)
        self.assertEqual([{}], cagrilar, "saglayici yokken alan yazildi")
        cagrilar2, _y2 = self._bir_heartbeat(lambda: None)
        self.assertEqual([{}], cagrilar2, "konum None iken alan yazildi")

    def test_URETIM_dongusu_saglayici_PATLARSA_yayin_surer(self):
        """Konum hatasi heartbeat'i durdurmamali (baglanti-failsafe)."""
        def patla():
            raise RuntimeError("telemetri koptu")
        cagrilar, y = self._bir_heartbeat(patla)
        self.assertEqual([{}], cagrilar, "hata aninda alan yazildi")
        self.assertEqual(1, y.heartbeat_sayisi, "hata heartbeat'i durdurdu")
        self.assertTrue(any("telemetri koptu" in h for h in y.hata),
                        "konum hatasi kayda gecmedi")


# --------------------------------------------- (d) MUTASYON
class Mutasyon(unittest.TestCase):

    def test_kenar_kucultulunce_IC_NOKTA_ihlal_olur(self):
        """Sabit gercekten kullaniliyor mu — 300 yerine 30 verilirse deger."""
        self.assertIsNone(iha_ub_ihlali(150.0, 150.0))
        self.assertIsNotNone(iha_ub_ihlali(150.0, 150.0, kenar_m=30.0),
                             "kenar parametresi kullanilmiyor — kapi bos")

    def test_GUI_ciplak_sabit_kullanmiyor(self):
        kaynak = (KOK / "comms" / "yks_gui.py").read_text(encoding="utf-8")
        self.assertNotIn("<= 300", kaynak,
                         "GUI hâlâ ciplak 300 ile denetliyor (madde 16)")
        self.assertIn("_ihlal = iha_ub_ihlali(", kaynak,
                      "GUI sozlesme fonksiyonunu cagirmiyor")
        # Denetim HEARTBEAT dalinda olmali (mini-saha ciziminde degil).
        bas = kaynak.index("_ihlal = iha_ub_ihlali(")
        onceki = kaynak.rfind('elif tip == "HEARTBEAT":', 0, bas)
        self.assertNotEqual(-1, onceki,
                            "alan ihlali denetimi HEARTBEAT dalinda degil")

    def test_URETIM_heartbeat_yolunda_konum_kancasi_VAR(self):
        kaynak = (KOK / "comms" / "iha_sender.py").read_text(encoding="utf-8")
        self.assertIn("konum_saglayici", kaynak)
        self.assertIn("send_heartbeat(x=", kaynak,
                      "yayinci x,y'yi heartbeat'e gecirmiyor")

    def test_sozlesme_sabiti_sartnameye_uygun(self):
        self.assertEqual(300.0, SARTNAME_IHA_UB_KENAR_M)

    def test_yerel_konum_fail_closed(self):
        self.assertIsNone(yerel_konum_m(None, 0, 0, 0))
        self.assertIsNone(yerel_konum_m(True, 0, 0, 0))
        self.assertIsNone(yerel_konum_m(0, 0, 91.0, 0))
        self.assertIsNone(yerel_konum_m(0, 0, float("inf"), 0))
        self.assertEqual((0.0, 0.0), yerel_konum_m(39.9, 32.8, 39.9, 32.8))


if __name__ == "__main__":
    unittest.main()
