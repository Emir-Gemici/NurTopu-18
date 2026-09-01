"""T169 KAPISI (ON_KAYIT SS36 · REVIEW_LOG D-317): hakem ekrani BAYAT tespiti
canliymis gibi gosteremez.

SARTNAME SS6.2 (lafzen): "Iha tarafindan tespit edilen acik yol guzergahi,
GERCEK ZAMANLI olarak Yer Kontrol Istasyonuna aktarilmali ve Alan Hakemi
tarafindan monitor uzerinden izlenmelidir. Hakem, tespitin basarili oldugunu
sozlu olarak onaylamalidir. Hakem onayi alinmayan tespitler gecersiz sayilir."

KUSUR: `comms/yks_gui.py` dugum canliligini izliyordu (nokta 3 s'de kirmiziya
doner) ama KARAR KUTUSUNUN tazelik korumasi YOKTU. Telsiz kesilse bile 36
puntoluk yesil "ACIK GUZERGAH — 2" ekranda kaliyor ve ONAY DUGMESI ETKIN
kaliyordu; hakem dakikalar once uretilmis bir tespiti "canli" sanip sozlu onay
verebilirdi.

BOS KAPI YASAGI (TEST_SPECS SS4.1) — on kayitli dort eksen:
  1. TAZE tespitte davranis BIREBIR AYNI (dugme etkin, bayat degil),
  2. yas esigi asinca BAYAT + dugme KAPALI; yeni tespit gelince ACILIR,
  3. mutasyon: yaslandirma kaldirilirsa / esik ciplak yazilirsa kilit DUSER,
  4. FAIL-CLOSED: bayatken `onayla()` cagrilsa bile ACK URETILMEZ (dugme TEK
     savunma degildir — otomatik onay ve zamanlayici ayni yolu cagirir).
"""

from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path
from unittest import mock

KOK = Path(__file__).resolve().parents[1]
for _y in (KOK / "comms", KOK / "codes"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

import yks_gui                                        # noqa: E402
from karar_sozlesmesi import YKS_TESPIT_TAZELIK_S     # noqa: E402


class SahteEtiket:
    def __init__(self):
        self.ayarlar = {}

    def config(self, **kw):
        self.ayarlar.update(kw)


class SahteDugme(SahteEtiket):
    pass


def _ekran(yas_sn=0.0, simdi=1_000_000.0):
    """Tk ACMADAN, yalnizca tazelik yolunun ihtiyaci olan alanlarla bir ornek."""
    o = object.__new__(yks_gui.YksArayuz)
    o.rota = {"seq": 7, "road": 2, "label": "orta", "conf": 0.9,
              "waypoints": [(0.0, 0.0), (0.0, 2.0)]}
    o.rota_yok = None
    o.rota_zaman = simdi - yas_sn
    o.tespit_bayat = False
    o.onaylandi = False
    o.tespit_onayli = False
    o.btn_onay = SahteDugme()
    o.lbl_onay = SahteEtiket()
    o.gunluk = []
    o._logla = lambda metin, renk=None: o.gunluk.append(metin)
    o._kutu_yaz = lambda kaynak, **kw: None
    # A2 (D-381): bu dosyanin ekseni HAT bayatligidir; algi yasi TAZE tutulur
    # ki olculen sey degismesin. Alanin yoklugu artik BILINMIYOR -> bayat
    # demektir (o eksenin kendi testleri test_a2_karar_yasi.py'dedir).
    o.karar_yas_rx = (0.2, time.monotonic())   # D-383: alim damgasi monotonik
    return o


class TazeDavranisDegismedi(unittest.TestCase):
    """MUTASYON 1'in tersi: taze tespitte HICBIR SEY degismemeli."""

    def test_taze_tespit_BAYAT_DEGIL(self):
        o = _ekran(yas_sn=0.0)
        self.assertFalse(o._tespiti_yaslandir(1_000_000.0))
        self.assertFalse(o.tespit_bayat)
        self.assertEqual({}, o.btn_onay.ayarlar, "taze tespitte dugmeye dokunuldu")
        self.assertEqual([], o.gunluk)

    def test_esik_SINIRINDA_taze_sayilir(self):
        o = _ekran(yas_sn=YKS_TESPIT_TAZELIK_S)
        self.assertFalse(o._tespiti_yaslandir(1_000_000.0),
                         "tam esikte bayat sayildi — `>` yerine `>=` kullanilmis")

    def test_rota_yokken_sessiz(self):
        o = _ekran()
        o.rota = None
        self.assertFalse(o._tespiti_yaslandir(1_000_000.0))
        o2 = _ekran()
        o2.rota_yok = ("MASKE_YOK", "x")
        self.assertFalse(o2._tespiti_yaslandir(1_000_000.0))


class Bayatlama(unittest.TestCase):

    def test_esik_asilinca_BAYAT_ve_DUGME_KAPALI(self):
        o = _ekran(yas_sn=YKS_TESPIT_TAZELIK_S + 1.0)
        self.assertTrue(o._tespiti_yaslandir(1_000_000.0))
        self.assertTrue(o.tespit_bayat)
        self.assertEqual("disabled", o.btn_onay.ayarlar.get("state"),
                         "bayat tespitte onay dugmesi ACIK kaldi")
        self.assertIn("BAYAT", o.btn_onay.ayarlar.get("text", ""))
        self.assertIn("BAYAT", o.lbl_onay.ayarlar.get("text", ""))
        self.assertTrue(any("BAYAT" in g for g in o.gunluk),
                        "bayatlama hakem gunlugune yazilmadi")

    def test_metin_YASI_ve_ESIGI_soyluyor(self):
        o = _ekran(yas_sn=YKS_TESPIT_TAZELIK_S + 7.0)
        o._tespiti_yaslandir(1_000_000.0)
        metin = o.lbl_onay.ayarlar["text"]
        self.assertIn("12 sn", metin, f"yas yazilmadi: {metin}")
        self.assertIn("§6.2", metin, "sartname maddesi yazilmadi")

    def test_bir_kez_isaretlenir_tekrar_gunluge_yazmaz(self):
        o = _ekran(yas_sn=YKS_TESPIT_TAZELIK_S + 1.0)
        o._tespiti_yaslandir(1_000_000.0)
        n = len(o.gunluk)
        o._tespiti_yaslandir(1_000_001.0)
        self.assertEqual(n, len(o.gunluk), "her saniye gunluge yaziyor (gurultu)")

    def test_ONAYLANMIS_tespitte_dugmeye_dokunulmaz(self):
        o = _ekran(yas_sn=YKS_TESPIT_TAZELIK_S + 1.0)
        o.onaylandi = True
        o._tespiti_yaslandir(1_000_000.0)
        self.assertNotIn("state", o.btn_onay.ayarlar,
                         "onay tamamlandiktan sonra dugme yeniden yazildi")


class FailClosedOnay(unittest.TestCase):
    """MUTASYON 4: dugme TEK savunma degildir."""

    def test_bayatken_onayla_ACK_URETMEZ(self):
        o = _ekran(yas_sn=YKS_TESPIT_TAZELIK_S + 1.0)
        o.link = mock.Mock()
        o.rota_adr = ("127.0.0.1", 5005)
        yks_gui.YksArayuz.onayla(o)
        self.assertFalse(o.tespit_onayli,
                         "BAYAT tespit 1. asama onayindan gecti")
        o.link.send.assert_not_called()
        self.assertTrue(any("REDDEDILDI" in g or "REDDEDİLDİ" in g
                            for g in o.gunluk),
                        "bayat onay reddi gunluge yazilmadi")


class CanlilikOlcutu(unittest.TestCase):
    """T172 · D-321: tazelik ROTA TEKRARINA degil HATTIN CANLILIGINA baglidir.

    IHA rotayi ACK ALANA KADAR tekrarlar; ACK gelince SUSAR. Eski olcut bunu
    ariza sayiyor ve demo kipinde hakemin onay dugmesini KAPATIYORDU.
    """

    @staticmethod
    def _ekran(rota_yas=None, hb_yas=None, simdi=1_000_000.0):
        o = _ekran(yas_sn=0.0, simdi=simdi)
        o.rota_zaman = None if rota_yas is None else simdi - rota_yas
        o.son_hb = {} if hb_yas is None else {"iha": simdi - hb_yas}
        return o

    def test_rota_SUSTU_ama_heartbeat_AKIYOR_bayat_DEGIL(self):
        """🔴 DEMO KIRICI KUSURUN KAPISI: ACK sonrasi rota susar, hb surer."""
        o = self._ekran(rota_yas=YKS_TESPIT_TAZELIK_S + 30.0, hb_yas=0.2)
        self.assertFalse(o._tespiti_yaslandir(1_000_000.0),
                         "rota tekrari kesildi diye tespit BAYAT sayildi — "
                         "hakem onay veremez, demo kilitlenir")
        self.assertFalse(o.tespit_bayat)
        self.assertEqual({}, o.btn_onay.ayarlar, "onay dugmesi kapatildi")

    def test_heartbeat_YOK_ama_rota_TAZE_bayat_DEGIL(self):
        o = self._ekran(rota_yas=0.5, hb_yas=YKS_TESPIT_TAZELIK_S + 30.0)
        self.assertFalse(o._tespiti_yaslandir(1_000_000.0))

    def test_IKISI_DE_kesikse_BAYAT(self):
        """Asil risk KORUNUR: hat olurse tespit bayattir."""
        o = self._ekran(rota_yas=YKS_TESPIT_TAZELIK_S + 10.0,
                        hb_yas=YKS_TESPIT_TAZELIK_S + 10.0)
        self.assertTrue(o._tespiti_yaslandir(1_000_000.0))
        self.assertEqual("disabled", o.btn_onay.ayarlar.get("state"))
        self.assertTrue(any("heartbeat" in g for g in o.gunluk), o.gunluk)

    def test_HIC_damga_yoksa_HUKUM_YOK(self):
        o = self._ekran(rota_yas=None, hb_yas=None)
        self.assertFalse(o._tespiti_yaslandir(1_000_000.0))
        self.assertEqual({}, o.btn_onay.ayarlar)

    def test_ONAYLANMIS_tespit_sonradan_BAYAT_ISARETLENMEZ(self):
        o = self._ekran(rota_yas=YKS_TESPIT_TAZELIK_S + 10.0,
                        hb_yas=YKS_TESPIT_TAZELIK_S + 10.0)
        o.onaylandi = True
        o._tespiti_yaslandir(1_000_000.0)
        self.assertFalse(o.tespit_bayat,
                         "onay TAZEYKEN verildi; sonradan bayat isaretlemek "
                         "hakemi yaniltir")
        self.assertEqual({}, o.btn_onay.ayarlar)
        self.assertEqual([], o.gunluk)


class SozlesmeKilidi(unittest.TestCase):
    """MUTASYON 3: esik SOZLESMEDEN gelmeli, GUI'de ciplak yazilmamali."""

    KAYNAK = (KOK / "comms" / "yks_gui.py").read_text(encoding="utf-8")

    def test_esik_sozlesmeden_ithal_ediliyor(self):
        self.assertIn("YKS_TESPIT_TAZELIK_S", self.KAYNAK)
        self.assertIn("from karar_sozlesmesi import", self.KAYNAK)

    def test_GUI_ciplak_tazelik_sayisi_yazmiyor(self):
        bas = self.KAYNAK.index("def _tespiti_yaslandir")
        son = self.KAYNAK.index("def _durum_tazele", bas)
        govde = self.KAYNAK[bas:son]
        self.assertNotIn("> 5.0", govde, "esik GUI'de ciplak yazilmis")
        self.assertIn("YKS_TESPIT_TAZELIK_S", govde)

    def test_yaslandirma_SANIYELIK_dongude_cagriliyor(self):
        bas = self.KAYNAK.index("def _durum_tazele")
        govde = self.KAYNAK[bas: bas + 400]
        self.assertIn("_tespiti_yaslandir", govde,
                      "yaslandirma saniyelik tazeleme dongusune bagli DEGIL — "
                      "ekran kendi kendine bayatlamaz")

    def test_sabit_sartname_ailesinde(self):
        from karar_sozlesmesi import IHA_HEARTBEAT_ARALIK_S
        self.assertGreater(YKS_TESPIT_TAZELIK_S, 3.0,
                           "tazelik, baglanti dusme esiginin (3 s) altinda "
                           "olamaz — ekran baglanti kopmadan bayat der")
        self.assertEqual(5.0, YKS_TESPIT_TAZELIK_S)
        self.assertGreaterEqual(YKS_TESPIT_TAZELIK_S,
                                5 * IHA_HEARTBEAT_ARALIK_S)


if __name__ == "__main__":
    unittest.main()
