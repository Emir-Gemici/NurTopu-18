"""NEDEN: Hakem ekranı aktarımın uçuşun hangi anında tamamlandığını yalnız
elindeki iniş kanıtları ölçüsünde söylemeli; bilgi yokluğu başarı kanıtı değildir.
"""

import sys
import unittest
from pathlib import Path
from unittest import mock


KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "comms"))

import yks_gui  # noqa: E402
from protocol import decode  # noqa: E402


class _SahteWidget:
    def __init__(self):
        self.ayarlar = {}

    def config(self, **ayarlar):
        self.ayarlar.update(ayarlar)

    def cget(self, ad):
        return self.ayarlar.get(ad)


class YksAktarimZamaniTests(unittest.TestCase):
    def _arayuz(self, t_iha1, iha_landed_seq):
        arayuz = object.__new__(yks_gui.YksArayuz)
        # A1: aktarim zamani testi gecerli bir OPEN_ROUTE fiksturu kullanir;
        # eksik road/ref/waypoint artik hakli olarak ANKOR YOK fail-closed olur.
        arayuz.rota = {
            "seq": 8801,
            "road": 2,
            "ref_xy": [0.0, 0.0],
            "waypoints": [[0.0, 0.0], [0.0, 1.0]],
        }
        arayuz.rota_yok = None
        arayuz.onaylandi = False
        arayuz.tespit_onayli = True
        arayuz.rota_adr = None
        arayuz.link = mock.Mock()
        arayuz.sayac = {"ACK_TX": 0}
        arayuz.t_iha1 = t_iha1
        arayuz.iha_landed_seq = iha_landed_seq
        # K8: 2. onay İKA'nın OPEN_ROUTE ACK kanıtı olmadan verilmez;
        # bu testler aktarım-zamanı metnini sınar, kanıt hazır verilir.
        arayuz.ika_rota_ack = {8801: 1_700_000_000.0}
        arayuz.btn_onay = _SahteWidget()
        arayuz.lbl_onay = _SahteWidget()
        arayuz._logla = mock.Mock()
        arayuz._zincir = mock.Mock()
        return arayuz

    def _onay_karari_degismedi(self, arayuz):
        self.assertTrue(arayuz.onaylandi)
        self.assertEqual(1, arayuz.sayac["ACK_TX"])
        arayuz.link.send.assert_called_once()
        ack_mesaji = decode(arayuz.link.send.call_args.args[0])
        self.assertEqual("ACK", ack_mesaji["type"])
        self.assertEqual(8801, ack_mesaji["ref"])
        self.assertEqual("yks", ack_mesaji["node"])
        self.assertEqual("disabled", arayuz.btn_onay.cget("state"))
        self.assertEqual("ONAYLANDI ✓✓", arayuz.btn_onay.cget("text"))

    def test_iha_henuz_inmediyse_ekran_bunu_soyler(self):
        arayuz = self._arayuz(t_iha1=None, iha_landed_seq=None)

        arayuz.onayla()

        metin = arayuz.lbl_onay.cget("text")
        self.assertIn("İHA henüz inmedi", metin)
        self.assertNotIn("HAVADA TAMAMLANDI", metin)
        self._onay_karari_degismedi(arayuz)

    def test_operator_kronometresi_varsa_inis_sonrasi_uyarir(self):
        arayuz = self._arayuz(t_iha1=123.0, iha_landed_seq=None)

        arayuz.onayla()

        metin = arayuz.lbl_onay.cget("text")
        self.assertIn("aktarım İHA inişinden SONRA", metin)
        self.assertIn("§6.4 geçersizlik riski", metin)
        self.assertNotIn("HAVADA TAMAMLANDI", metin)
        self._onay_karari_degismedi(arayuz)

    def test_protocol_inisi_var_kronometre_yoksa_zaman_bilinmiyor(self):
        arayuz = self._arayuz(t_iha1=None, iha_landed_seq=8802)

        arayuz.onayla()

        metin = arayuz.lbl_onay.cget("text")
        self.assertIn("AKTARIM ZAMANI BİLİNMİYOR", metin)
        self.assertNotIn("✓", metin)
        self.assertNotIn("HAVADA TAMAMLANDI", metin)
        self.assertNotIn("İHA henüz inmedi", metin)
        self._onay_karari_degismedi(arayuz)


if __name__ == "__main__":
    unittest.main()
