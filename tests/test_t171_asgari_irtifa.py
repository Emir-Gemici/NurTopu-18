"""T171 KAPISI (ON_KAYIT SS38 · REVIEW_LOG D-319): SS5.3.2 "asgari 30 metre
irtifa" sarti sistemde HIC UYGULANMIYORDU ve uyum raporumuz uygulandigini
IDDIA EDIYORDU.

SARTNAME SS5.3.2: "...Acik Guzergah'i ASGARI 30 METRE IRTIFADAN ucarak, havadan
goruntu isleme ve yapay zeka algoritmalari vasitasiyla tespit etmek..."

OLCULDU (D-319): `rota_olcek_reddi` icindeki irtifa dalinin IKI KOLU DA
`return None` yapiyordu — yani dal OLUYDU; ustelik HICBIR CAGIRAN `irtifa_m`
GECMIYORDU. Sabit yalnizca o olu dalda, kuru kosunun sahte telemetrisinde ve
"30.0'a esittir" diyen bir testte geciyordu. Buna ragmen
`results/sartname_bosluk/rapor_uret.py` R15'i KANITLI_TEST diye isaretleyip
kanit olarak "rota_olcek_reddi (irtifa aralik disi -> OLCEK_YOK)" gosteriyordu:
YANLIS BIR UYUM IDDIASI.

YON (on kayitta SONUC GORULMEDEN yazildi): RET DEGIL, GOSTERIM. IHA kalkis ve
inis sirasinda da kare uretir; orada reddetmek zararli olurdu. Ama hakem,
asgari irtifanin ALTINDA uretilmis bir tespiti onaylarken bunu GORMELIDIR.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
for _y in (KOK / "comms", KOK / "codes"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

import yks_gui                                                  # noqa: E402
from karar_sozlesmesi import (ASGARI_IRTIFA_SEBEBI,             # noqa: E402
                              SARTNAME_ASGARI_IRTIFA_M,
                              asgari_irtifa_notu, rota_olcek_reddi)


class OluDalKaldirildi(unittest.TestCase):
    """MUTASYON: olu dal geri konursa / sabit orada anilirsa kilit DUSER."""

    KAYNAK = (KOK / "codes" / "karar_sozlesmesi.py").read_text(encoding="utf-8")

    def _govde(self):
        bas = self.KAYNAK.index("def rota_olcek_reddi(")
        son = self.KAYNAK.index("def asgari_irtifa_notu(", bas)
        return self.KAYNAK[bas:son]

    def test_imzada_irtifa_parametresi_YOK(self):
        self.assertIn("def rota_olcek_reddi(mpp):", self.KAYNAK,
                      "olu `irtifa_m` parametresi hâlâ imzada")

    def test_govdede_asgari_irtifa_KARARI_YOK(self):
        govde = self._govde()
        self.assertNotIn("SARTNAME_ASGARI_IRTIFA_M <", govde)
        self.assertNotIn("< SARTNAME_ASGARI_IRTIFA_M", govde,
                         "olu irtifa dali geri gelmis — sabit burada anilip "
                         "hicbir sey yapmiyor (vakum kapi)")

    def test_olcek_reddi_davranisi_KORUNDU(self):
        self.assertIsNone(rota_olcek_reddi(0.05))
        self.assertEqual("OLCEK_YOK", rota_olcek_reddi(None)[0])
        self.assertEqual("OLCEK_YOK", rota_olcek_reddi(0.0)[0])
        self.assertEqual("OLCEK_YOK", rota_olcek_reddi(True)[0])


class AsgariIrtifaNotu(unittest.TestCase):

    def test_asgari_altinda_NOT_uretir(self):
        n = asgari_irtifa_notu(5.0)
        self.assertIsNotNone(n)
        self.assertEqual(ASGARI_IRTIFA_SEBEBI, n[0])
        self.assertIn("5.0 m", n[1])
        self.assertIn("5.3.2", n[1])
        self.assertIn("ret DEGILDIR", n[1],
                      "not, RET sanilabilir — yon yanlis anlasilir")

    def test_asgari_ve_ustu_SESSIZ(self):
        self.assertIsNone(asgari_irtifa_notu(SARTNAME_ASGARI_IRTIFA_M))
        self.assertIsNone(asgari_irtifa_notu(100.0))

    def test_BILINMIYOR_not_URETMEZ(self):
        """"bilinmiyor" ile "asgarinin altinda" ayni sey degildir."""
        for gecersiz in (None, True, float("nan"), float("inf"), -5.0, 0.0, "x"):
            with self.subTest(deger=repr(gecersiz)):
                self.assertIsNone(asgari_irtifa_notu(gecersiz))

    def test_esik_parametrik_ve_SOZLESMEDEN(self):
        self.assertEqual(30.0, SARTNAME_ASGARI_IRTIFA_M)
        self.assertIsNotNone(asgari_irtifa_notu(40.0, asgari_m=50.0),
                             "esik parametresi kullanilmiyor — kapi bos")


class UretimIrtifayiYAYINLIYOR(unittest.TestCase):
    """Hakem ekrani `alt` okuyordu ama URETIM onu hic yayinlamiyordu."""

    def test_yayinci_irtifa_saglayici_aliyor(self):
        import iha_sender
        kaynak = (KOK / "comms" / "iha_sender.py").read_text(encoding="utf-8")
        self.assertIn("irtifa_saglayici", kaynak)
        self.assertIn('alanlar["alt"]', kaynak,
                      "heartbeat'e `alt` alani hic yazilmiyor")
        self.assertTrue(hasattr(iha_sender.KararYayinci, "__init__"))

    def test_URETIM_dongusu_alt_gecirir(self):
        import threading
        import iha_sender
        cagrilar = []
        y = iha_sender.KararYayinci.__new__(iha_sender.KararYayinci)

        class SahteGonderici:
            def send_heartbeat(_s, node="iha", **kw):
                cagrilar.append(kw)
                y._dur.set()
                return 1

        y.sender = SahteGonderici()
        y.konum_saglayici = lambda: (10.0, 20.0)
        y.irtifa_saglayici = lambda: 42.5
        y.heartbeat_aralik = 0.001
        y.heartbeat_sayisi = 0
        y.hata = []
        y._dur = threading.Event()
        y._heartbeat_dongusu()
        self.assertEqual([{"x": 10.0, "y": 20.0, "alt": 42.5}], cagrilar)

    def test_irtifa_YOKKEN_alan_yazilmaz(self):
        import threading
        import iha_sender
        cagrilar = []
        y = iha_sender.KararYayinci.__new__(iha_sender.KararYayinci)

        class SahteGonderici:
            def send_heartbeat(_s, node="iha", **kw):
                cagrilar.append(kw)
                y._dur.set()
                return 1

        y.sender = SahteGonderici()
        y.konum_saglayici = None
        y.irtifa_saglayici = lambda: None
        y.heartbeat_aralik = 0.001
        y.heartbeat_sayisi = 0
        y.hata = []
        y._dur = threading.Event()
        y._heartbeat_dongusu()
        self.assertEqual([{}], cagrilar, "irtifa yokken alan yazildi")

    def test_saglayici_PATLARSA_yayin_surer(self):
        import threading
        import iha_sender
        cagrilar = []
        y = iha_sender.KararYayinci.__new__(iha_sender.KararYayinci)

        class SahteGonderici:
            def send_heartbeat(_s, node="iha", **kw):
                cagrilar.append(kw)
                y._dur.set()
                return 1

        def patla():
            raise RuntimeError("telemetri koptu")

        y.sender = SahteGonderici()
        y.konum_saglayici = None
        y.irtifa_saglayici = patla
        y.heartbeat_aralik = 0.001
        y.heartbeat_sayisi = 0
        y.hata = []
        y._dur = threading.Event()
        y._heartbeat_dongusu()
        self.assertEqual([{}], cagrilar)
        self.assertEqual(1, y.heartbeat_sayisi, "hata heartbeat'i durdurdu")
        self.assertTrue(any("telemetri koptu" in h for h in y.hata))


class HakemEkraniGOSTERIYOR(unittest.TestCase):

    @staticmethod
    def _ekran(alt=None):
        o = object.__new__(yks_gui.YksArayuz)
        o.tel = {"iha": ({} if alt is None else {"alt": alt})}
        o.gunluk = []
        o._logla = lambda metin, renk=None: o.gunluk.append(metin)
        return o

    def test_asgari_altinda_UYARIR(self):
        o = self._ekran(alt=12.0)
        n = o._irtifa_notunu_goster()
        self.assertIsNotNone(n)
        self.assertTrue(any("12.0 m" in g for g in o.gunluk), o.gunluk)
        self.assertTrue(any("5.3.2" in g for g in o.gunluk))

    def test_asgari_ustunde_SAGLANIYOR_der(self):
        o = self._ekran(alt=35.0)
        self.assertIsNone(o._irtifa_notunu_goster())
        self.assertTrue(any("sağlanıyor" in g for g in o.gunluk), o.gunluk)

    def test_irtifa_YOKKEN_sessiz_KALMAZ(self):
        """'bilinmiyor' da yazilir — sessiz sifir yasak."""
        o = self._ekran(alt=None)
        self.assertIsNone(o._irtifa_notunu_goster())
        self.assertTrue(any("BİLİNMİYOR" in g for g in o.gunluk), o.gunluk)

    def test_OPEN_ROUTE_yolunda_CAGRILIYOR(self):
        kaynak = (KOK / "comms" / "yks_gui.py").read_text(encoding="utf-8")
        bas = kaynak.index("Hakem onayı BEKLENİYOR")
        self.assertIn("_irtifa_notunu_goster()", kaynak[bas: bas + 900],
                      "irtifa notu OPEN_ROUTE kabul yolunda cagrilmiyor")


class UyumRaporuDURUSTLESTI(unittest.TestCase):
    """YANLIS uyum iddiasi kayitta kalamaz."""

    def test_rapor_OLCEK_YOK_iddiasini_TASIMIYOR(self):
        p = KOK / "results" / "sartname_bosluk" / "rapor_uret.py"
        if not p.is_file():
            self.skipTest("rapor ureteci yok")
        metin = p.read_text(encoding="utf-8")
        self.assertNotIn("irtifa aralık dışı → OLCEK_YOK", metin,
                         "uyum raporu hâlâ YANLIS iddiayi tasiyor (D-319)")


if __name__ == "__main__":
    unittest.main()
