import queue
import sys
import unittest
from pathlib import Path
from unittest import mock


KOK = Path(__file__).resolve().parents[1]
if str(KOK / "comms") not in sys.path:
    sys.path.insert(0, str(KOK / "comms"))

import yks_gui  # noqa: E402
from protocol import encode, heartbeat  # noqa: E402


class _KapaliSoket:
    def fileno(self):
        return -1


class _Akis:
    def __init__(self, paketler):
        self.paketler = list(paketler)
        self.sock = _KapaliSoket()

    def recv(self):
        if self.paketler:
            return self.paketler.pop(0)
        raise OSError("kapalı")


def _gui():
    g = object.__new__(yks_gui.YksArayuz)
    g.protokol_kilidi = True
    g.kaynak_kilidi = True
    g._son_heartbeat_seq = {}
    g.protokol_ret_sayaci = 0
    g.kaynak_ret_sayaci = 0
    g.sabit_adr = {
        "iha": ("10.0.0.3", 5007),
        "ika": ("10.0.0.2", 5006),
    }
    g.son_adr = dict(g.sabit_adr)
    g.son_hb = {}
    g.tel = {}
    g.mod = {}
    g.karar_yas_rx = None
    g.arm_acik = None
    g.arm_durum_zamani = None
    g.iha_iz = []
    g._manuel_uyarildi = False
    g.sayac = {"HEARTBEAT": 0}
    g._logla = mock.Mock()
    g._arm_ui_uygula = mock.Mock()
    g._arm_bekleyeni_tamamla = mock.Mock()
    return g


class KaynakVeSiraTesti(unittest.TestCase):
    def test_iha_verisi_ayni_ip_efemer_porttan_kabul_edilir(self):
        g = _gui()
        g._mesaj_isle(heartbeat("iha", seq=2, armed=False),
                       ("10.0.0.3", 43123))
        self.assertFalse(g.arm_acik)
        self.assertIn("iha", g.son_hb)

    def test_yanlis_ip_armed_durumunu_degistiremez(self):
        g = _gui()
        g._mesaj_isle(heartbeat("iha", seq=2, armed=True),
                       ("10.0.0.99", 5007))
        self.assertIsNone(g.arm_acik)
        self.assertNotIn("iha", g.son_hb)
        self.assertEqual(1, g.kaynak_ret_sayaci)

    def test_geri_sirali_heartbeat_arm_durumunu_geri_saramaz(self):
        g = _gui()
        with mock.patch.object(yks_gui.time, "monotonic",
                               side_effect=[10.0, 10.0, 10.1, 10.1]):
            g._mesaj_isle(heartbeat("iha", seq=2, armed=False),
                           ("10.0.0.3", 40001))
            g._mesaj_isle(heartbeat("iha", seq=1, armed=True),
                           ("10.0.0.3", 40001))
        self.assertFalse(g.arm_acik,
                         "mutasyon: eski armed=true launch kilidini açtı")
        self.assertEqual(1, g.sayac["HEARTBEAT"])

    def test_guclu_ack_tam_komut_alici_ucundan_gelir(self):
        iha_ack = {"v": 1, "type": "ACK", "node": "iha", "ref": 4}
        self.assertTrue(yks_gui.mesaj_kaynagi_dogrula(
            iha_ack, ("10.0.0.3", 5007),
            ("10.0.0.3", 5007), ("10.0.0.2", 5006))[0])
        self.assertFalse(yks_gui.mesaj_kaynagi_dogrula(
            iha_ack, ("10.0.0.3", 43123),
            ("10.0.0.3", 5007), ("10.0.0.2", 5006))[0])

    def test_bozuk_protokol_surumu_durum_uretemez(self):
        g = _gui()
        m = heartbeat("iha", seq=3, armed=True)
        m["v"] = 999
        g._mesaj_isle(m, ("10.0.0.3", 40001))
        self.assertIsNone(g.arm_acik)
        self.assertEqual(1, g.protokol_ret_sayaci)


class CerceveSiniriTesti(unittest.TestCase):
    def _dinle(self, paketler, okuyucu=None):
        g = object.__new__(yks_gui.YksArayuz)
        g.link = _Akis(paketler)
        g.reader = okuyucu or yks_gui.FrameReader()
        g.gelen = queue.Queue()
        g.algi_kuyruk = queue.Queue()
        g._dinle()
        return g

    def test_newlinesiz_bozuk_udp_sonraki_datagrami_zehirlemez(self):
        iyi = encode(heartbeat("iha", seq=8, armed=False))
        g = self._dinle([(b'{"yarim":', ("10.0.0.9", 1000)),
                          (iyi, ("10.0.0.3", 2000))])
        self.assertEqual(1, g.gelen.qsize())
        self.assertEqual(8, g.gelen.get()[0]["seq"])

    def test_seri_parcali_cerceve_tamponu_korunur(self):
        iyi = encode(heartbeat("iha", seq=9, armed=False))
        g = self._dinle([(iyi[:9], None), (iyi[9:], None)])
        self.assertEqual(1, g.gelen.qsize())
        self.assertEqual(9, g.gelen.get()[0]["seq"])


if __name__ == "__main__":
    unittest.main()
