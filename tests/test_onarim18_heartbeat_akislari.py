"""NEDEN: İki İHA yayıncısı ve yeniden başlama telemetriyi silememeli;
salt canlılık mesajları eski Pixhawk verisini taze gösterememeli.
"""
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "comms"))
import protocol
import yks_gui
from test_yks_operator_guvenligi import _taban_arayuz


class HeartbeatAkislari(unittest.TestCase):
    def setUp(self):
        self.g = _taban_arayuz()
        self.g.protokol_kilidi = True

    def gonder(self, akis, seq, zaman, **alanlar):
        m = protocol.heartbeat("iha", seq=seq, **alanlar)
        if akis is None:
            m.pop("akis")
        else:
            m["akis"] = akis
        with mock.patch.object(yks_gui.time, "monotonic", return_value=zaman):
            self.g._mesaj_isle(m, None)

    def telemetri(self, akis="a" * 32, seq=10000, zaman=10):
        self.gonder(akis, seq, zaman, lat=40.9599798, lon=29.133553,
                    gps_fix=6, uydu=10, bat=12.6, armed=True,
                    mod="AUTO", pixhawk_canli=True)

    def test_iki_yayinci_her_iki_sirada_da_telemetriyi_korur(self):
        for once_saglik in (False, True):
            with self.subTest(once_saglik=once_saglik):
                self.setUp()
                if once_saglik:
                    self.gonder("b" * 32, 40000, 9.9)
                self.telemetri()
                self.gonder("b" * 32, 40001, 10.1)
                self.assertEqual(40.9599798, self.g.tel["iha"]["lat"])
                self.assertTrue(self.g.arm_acik)
                self.assertEqual("AUTO", self.g.mod["iha"])
                self.assertEqual(10, self.g._son_telemetri["iha"])
                self.assertEqual(10.1, self.g.son_hb["iha"])

    def test_yeniden_baslayan_model_seq_bir_ile_hemen_doner(self):
        self.telemetri()
        self.gonder("b" * 32, 40000, 10.1)
        self.gonder("c" * 32, 1, 10.2, lat=41.0, lon=29.0,
                    gps_fix=6, armed=False)
        self.gonder("b" * 32, 40001, 10.3)
        self.assertEqual(41.0, self.g.tel["iha"]["lat"])
        self.assertFalse(self.g.arm_acik)
        self.assertEqual(0, self.g.protokol_ret_sayaci)

    def test_ayni_akista_tekrar_ve_geri_sira_reddedilir(self):
        self.telemetri()
        for seq in (10000, 9999):
            self.gonder("a" * 32, seq, 10.1, armed=False)
        self.assertTrue(self.g.arm_acik)
        self.assertEqual(1, self.g.sayac["HEARTBEAT"])
        self.assertEqual(10, self.g.son_hb["iha"])

    def test_telemetri_akisinin_bos_snapshoti_gnss_ve_armi_siler(self):
        self.telemetri()
        self.gonder("a" * 32, 10001, 10.1)
        self.assertEqual({}, self.g.tel["iha"])
        self.assertIsNone(self.g.arm_acik)
        self.assertNotIn("iha", self.g.mod)

    def test_saglik_canliyken_model_kaybi_esikte_gecersizlesir(self):
        self.telemetri()
        self.gonder("b" * 32, 1, 10 + yks_gui.ARM_DURUM_TAZELIK_S - 0.1)
        self.assertIn("lat", self.g.tel["iha"])
        self.gonder("b" * 32, 2, 10 + yks_gui.ARM_DURUM_TAZELIK_S)
        self.assertEqual({}, self.g.tel["iha"])
        self.assertIsNone(self.g.arm_acik)
        self.assertNotIn("iha", self.g.mod)
        self.telemetri(seq=10001, zaman=14)
        self.assertIn("lat", self.g.tel["iha"])

    def test_gui_tiki_saglik_canliyken_gnssyi_bayat_gosterir(self):
        self.telemetri()
        self.gonder("b" * 32, 1, 10 + yks_gui.ARM_DURUM_TAZELIK_S - 0.1)
        with mock.patch.object(yks_gui.time, "monotonic", return_value=13.1):
            self.g._durum_tazele()
        self.assertEqual({}, self.g.tel["iha"])
        self.assertIn("BAYAT", self.g.lbl_gps.cget("text"))
        self.assertEqual(yks_gui.SARI, self.g.lbl_dugum["iha"][0].cget("fg"))

    def test_akis_kimligi_olmayan_eski_snapshot_davranisi_korunur(self):
        self.telemetri(akis=None)
        self.gonder(None, 10001, 10.1)
        self.assertEqual({}, self.g.tel["iha"])
        self.assertIsNone(self.g.arm_acik)

    def test_bozuk_akis_kimligi_durumu_degistiremez(self):
        self.telemetri()
        for akis in (None, [], {}, 1, "", "x" * 65, " " * 32):
            m = protocol.heartbeat("iha", armed=False)
            m["akis"] = akis
            self.g._mesaj_isle(m, None)
        self.assertTrue(self.g.arm_acik)
        self.assertEqual(7, self.g.protokol_ret_sayaci)

    def test_akis_kayitlari_sinirlidir(self):
        for i in range(yks_gui.HEARTBEAT_AKIS_TAVANI * 2):
            self.gonder(f"{i:032x}", 1, float(i), armed=False)
        self.assertEqual(yks_gui.HEARTBEAT_AKIS_TAVANI,
                         len(self.g._son_heartbeat_seq))
        self.assertLessEqual(len(self.g._telemetri_akislari),
                             yks_gui.HEARTBEAT_AKIS_TAVANI)

    def test_surec_kimligi_sabit_yeni_surecte_farkli(self):
        m = protocol.heartbeat("iha")
        self.assertEqual(m["akis"], protocol.heartbeat("iha")["akis"])
        diger = subprocess.check_output(
            [sys.executable, "-c",
             "from protocol import heartbeat; print(heartbeat('iha')['akis'])"],
            cwd=KOK / "comms", text=True).strip()
        self.assertNotEqual(m["akis"], diger)
        self.assertEqual(32, len(diger))

    def test_fork_ile_miras_alinan_kimlik_yenilenir(self):
        onceki = protocol.heartbeat("iha")["akis"]
        with mock.patch.object(protocol.os, "getpid", return_value=-1):
            yeni = protocol.heartbeat("iha")["akis"]
        self.assertNotEqual(onceki, yeni)


if __name__ == "__main__":
    unittest.main()
