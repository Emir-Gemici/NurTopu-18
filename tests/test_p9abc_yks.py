"""P9a-b-c (D-393) — YKS: parasut ACK'li tekrar, arming kilidi, §2.2.3 sira.

Sartname:
  §2.2.4  parasut manuel tetiklenebilir (ceza ile) — SS7 Cceza: -50.
  §6.2    firlatma hakem onayi/arming sonrasi.
  §2.2.3  guzergah aktarimi IHA HAVADAYKEN tamamlanmali.

Kapanan kusurlar (olculdu):
  1. PARACHUTE tek atis `_cmd_gonder` ile gidiyordu — IKA_GO bile ACK'li
     tekrarliyken EN kritik acil komut tek UDP paketine emanetti; ustune
     `_ack_isle` iha dugumunun ACK'ini HIC islemiyordu (erken donus).
  2. Ceza `50` ciplak sayiydi (madde 16) -> PARASUT_MANUEL_CEZA_PUANI.
  3. `firlatma()` arm kilidini dugme durumuna emanet ediyordu (T180 sinifi:
     UI durumu emniyet sinyali degildir) -> yazilim kilidi.
  4. §2.2.3 sira denetimi yoktu: inis kaniti, IKA rota ACK'indan once
     gelirse kimse uyarmiyordu.
"""
import sys
import unittest
from pathlib import Path
from unittest import mock

KOK = Path(__file__).resolve().parents[1]
for _y in (KOK / "comms", KOK / "codes", KOK / "tests"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

import yks_gui  # noqa: E402
from komut_tekrar import VAZGECILDI, AckliTekrar  # noqa: E402
from protocol import ack  # noqa: E402
from karar_sozlesmesi import (PARASUT_MANUEL_CEZA_PUANI,  # noqa: E402
                              PARASUT_TEKRAR_ARALIGI_S,
                              PARASUT_TEKRAR_UST_SINIRI)
from test_ika_go_ackli_tekrar import _SahteSaat, _SahteWidget, _arayuz  # noqa: E402


def _p9_arayuz(saat=None):
    """_arayuz harness'i + P9 alanlari."""
    saat = saat or _SahteSaat()
    link = mock.Mock()
    link.send = mock.Mock(return_value=None)
    g = _arayuz(link, ("127.0.0.1", 5006), saat)
    g.son_adr["iha"] = ("127.0.0.1", 5007)
    g.parasut_tekrar = AckliTekrar(g._ham_gonder, PARASUT_TEKRAR_ARALIGI_S,
                                   PARASUT_TEKRAR_UST_SINIRI, saat=saat)
    g.parasut_ack_zamani = None
    g.parasut_teyit = 0.0
    g.btn_parasut = _SahteWidget(state="normal")
    g._ceza_ekle = mock.Mock()
    g._ucus = mock.Mock()
    g.arm_acik = False
    g.t_iha0 = None
    g.btn_firlat = _SahteWidget(state="normal")
    g.btn_iha_indi = _SahteWidget(state="disabled")
    return g, saat


class ParasutAckliTekrar(unittest.TestCase):
    def test_iki_adimli_teyit_ilk_basista_gondermez(self):
        g, _ = _p9_arayuz()
        g.parasut()
        self.assertIsNone(g.parasut_tekrar.mesaj, "ilk basista gonderilmemeli")
        self.assertGreater(g.parasut_teyit, 0.0)

    def test_teyitli_basista_ackli_tekrar_baslar_ve_ceza_islenir(self):
        g, _ = _p9_arayuz()
        g.parasut()
        g.parasut()                       # teyit penceresi icinde 2. basis
        m = g.parasut_tekrar.mesaj
        self.assertIsNotNone(m, "ACK'li tekrar baslamadi")
        self.assertEqual(("CMD", "PARACHUTE", "iha"),
                         (m["type"], m["cmd"], m["hedef"]))
        g._ceza_ekle.assert_called_once()
        self.assertEqual(PARASUT_MANUEL_CEZA_PUANI,
                         g._ceza_ekle.call_args.args[0],
                         "ceza sozlesme sabitinden gelmeli (madde 16)")

    def test_iha_ack_i_tekrari_durdurur(self):
        g, _ = _p9_arayuz()
        g.parasut(); g.parasut()
        seq = g.parasut_tekrar.mesaj["seq"]
        g._ack_isle(ack(seq, "iha", "CMD"), ("127.0.0.1", 5007))
        self.assertIsNotNone(g.parasut_ack_zamani,
                             "iha ACK'i islenmedi — eski kusur geri geldi")
        self.assertFalse(g.parasut_tekrar.bekliyor)

    def test_ack_yoksa_ust_sinirda_dugme_yeniden_acilir(self):
        g, saat = _p9_arayuz()
        g.parasut(); g.parasut()
        for _ in range(PARASUT_TEKRAR_UST_SINIRI + 1):
            saat.ilerle(PARASUT_TEKRAR_ARALIGI_S)
            g._parasut_tik()
        self.assertEqual(VAZGECILDI, g.parasut_tekrar.durum)
        self.assertEqual("normal", g.btn_parasut.cget("state"),
                         "ACK'siz kalan parasut dugmesi kilitli kaldi — "
                         "operator tekrar tetikleyemez")

    def test_ika_ack_i_parasutu_durduramaz(self):
        """Yanlis dugumden ACK sahtekarligi: ika, iha komutunu kapatamaz."""
        g, _ = _p9_arayuz()
        g.parasut(); g.parasut()
        seq = g.parasut_tekrar.mesaj["seq"]
        g._ack_isle(ack(seq, "ika", "CMD"), ("127.0.0.1", 5006))
        self.assertIsNone(g.parasut_ack_zamani)
        self.assertTrue(g.parasut_tekrar.bekliyor,
                        "ika dugumunun ACK'i PARACHUTE tekrarini kapatti")


class FirlatmaArmingKilidi(unittest.TestCase):
    def test_arm_yokken_firlatma_reddedilir(self):
        g, _ = _p9_arayuz()
        g.arm_acik = False
        g.firlatma()
        self.assertIsNone(g.t_iha0, "ARM'siz firlatma damgasi atildi (§6.2)")

    def test_arm_varken_firlatma_damgalanir(self):
        g, _ = _p9_arayuz()
        g.arm_acik = True
        g.firlatma()
        self.assertIsNotNone(g.t_iha0)


class AktarimHavadaSirasi(unittest.TestCase):
    """§2.2.3: inis kaniti IKA rota ACK'indan ONCE ise KIRMIZI uyari."""

    def _landed_gonder(self, g, seq=901):
        g.iha_landed_seq = None
        g.iha_indi = mock.Mock()
        g.sayac = {"ACK_TX": 0, "IHA_LANDED": 0}
        g._mesaj_isle({"type": "IHA_LANDED", "node": "iha", "seq": seq},
                      ("127.0.0.1", 5007))

    def test_rota_ack_yokken_inis_ihlal_uyarisi(self):
        g, _ = _p9_arayuz()
        g.rota = {"type": "OPEN_ROUTE", "seq": 55, "road": 1}
        g.ika_rota_ack = {}
        self._landed_gonder(g)
        loglar = " | ".join(str(c.args[0]) for c in g._logla.call_args_list)
        self.assertIn("İHLAL RİSKİ", loglar,
                      "aktarim kanitsiz iniste §2.2.3 uyarisi yok")

    def test_rota_ack_varsa_ihlal_uyarisi_yok(self):
        g, _ = _p9_arayuz()
        g.rota = {"type": "OPEN_ROUTE", "seq": 55, "road": 1}
        g.ika_rota_ack = {55: 123.0}
        self._landed_gonder(g)
        loglar = " | ".join(str(c.args[0]) for c in g._logla.call_args_list)
        self.assertNotIn("İHLAL RİSKİ", loglar)

    def test_open_route_ack_havada_damgasi(self):
        g, _ = _p9_arayuz()
        g.rota = {"type": "OPEN_ROUTE", "seq": 77, "road": 2}
        g.ika_rota_ack = {}
        g.iha_landed_seq = None
        g.son_hb = {}                       # heartbeat yok -> havada sayilmaz
        g._ack_isle(ack(77, "ika", "OPEN_ROUTE"), ("127.0.0.1", 5006))
        loglar = " | ".join(str(c.args[0]) for c in g._logla.call_args_list)
        self.assertIn("HAVADA DEĞİL", loglar,
                      "yerdeyken gelen aktarim kanitina havada-degil "
                      "damgasi basilmadi (§2.2.3)")


class IhaAdresPinleme(unittest.TestCase):
    """D-403 (curutucu KRITIK-1): `son_adr["iha"]` yalniz heartbeat/OPEN_ROUTE
    kaynagindan ogreniliyordu — o adres rpi_inference'in EFEMER portudur,
    komut alicisinin --bind'i degil; PARACHUTE alicaya HIC ulasmazdi.
    `--iha` pinler; heartbeat ezemez (ika ile ayni mekanizma)."""

    def _kur(self, iha_peer):
        g = object.__new__(yks_gui.YksArayuz)
        g.son_adr, g.sabit_adr = {}, {}
        if iha_peer is not None:
            g.son_adr["iha"] = iha_peer
            g.sabit_adr["iha"] = iha_peer
        return g

    def test_pinli_iha_adresini_heartbeat_ezemez(self):
        g = self._kur(("10.0.0.5", 5007))
        g._dugum_adresini_ogren("iha", ("10.0.0.5", 61234))   # efemer heartbeat
        self.assertEqual(("10.0.0.5", 5007), g.son_adr["iha"],
                         "heartbeat pinli komut-alici adresini ezdi")

    def test_pinsiz_iha_adresi_efemer_porta_kayar(self):
        """Pin YOKKEN eski kusur aynen yasar — belgelenmis davranis."""
        g = self._kur(None)
        g._dugum_adresini_ogren("iha", ("10.0.0.5", 61234))
        self.assertEqual(("10.0.0.5", 61234), g.son_adr["iha"])

    def test_ctor_iha_peer_parametresi_pinler(self):
        with mock.patch.object(yks_gui.YksArayuz, "_arayuz_kur"), \
             mock.patch.object(yks_gui.YksArayuz, "_tik"), \
             mock.patch.object(yks_gui.threading.Thread, "start"):
            g = yks_gui.YksArayuz(mock.Mock(), mock.Mock(),
                                  ika_peer=("1.1.1.1", 5006),
                                  iha_peer=("2.2.2.2", 5007))
        self.assertEqual(("2.2.2.2", 5007), g.sabit_adr["iha"])
        self.assertEqual(("1.1.1.1", 5006), g.sabit_adr["ika"])


if __name__ == "__main__":
    unittest.main()
