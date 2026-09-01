"""P3/T149 (D-390) — IKA SURUCU SOYUTLAMASI.

ON KAYIT: results/p3_ika_surucu/ON_KAYIT.md (T1..T8 uygulamadan once yazildi).

NEDEN: ika_nav motor komutunu dogrudan subprocess'e basiyordu; gercek donanim
icin katman yoktu (T149) ve `subprocess.run(timeout=1)` zaman asiminda istisna
firlatip navigate dongusunu COKERTIYORDU. Simdi surucu arayuzu var:
hiz_ver/konum_al/durdur/saglikli — istisna sizmaz, ariza False'tur, ardisik
ariza tavaninda navigate guvenli durusla False doner.

Kilit: T141 bayt-esitligi — GazeboSurucu eski send_vel/get_pose ile BIREBIR
ayni komutu uretir/ayni ayristirmayi yapar.
"""
import subprocess
import sys
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

KOK = Path(__file__).resolve().parents[1]
for _y in (KOK / "comms", KOK / "simulation" / "scripts"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

import ika_nav  # noqa: E402
import ika_surucu  # noqa: E402
from ika_receiver import IkaReceiver  # noqa: E402
from link import UDPLink  # noqa: E402
from protocol import command, encode, iha_landed, open_route  # noqa: E402


class T1BaytEsitlik(unittest.TestCase):
    """GazeboSurucu, eski send_vel/get_pose'un BIREBIR karsiligi."""

    def test_T1_hiz_komutu_bayt_es(self):
        surucu = ika_surucu.GazeboSurucu()
        with mock.patch.object(ika_surucu.subprocess, "run") as kosum:
            self.assertTrue(surucu.hiz_ver(1.234, -0.5))
        kosum.assert_called_once_with(
            ["gz", "topic", "-p", "~/ika/vel_cmd", "-m",
             "position { x: 1.234 y: -0.500 z: 0 }"],
            capture_output=True, timeout=1)

    def test_T2_format_A_ayristirma_kilidi(self):
        text = ("position: (-23.0, -23.0, 0.12)\n"
                "orientation: (0.924, 0.0, 0.0, 0.383)\n")
        x, y, z, yaw = ika_surucu.GazeboSurucu.ciktiyi_ayristir(text)
        self.assertEqual((x, y, z), (-23.0, -23.0, 0.12))
        # (w,x,y,z) cozumu: yaw = atan2(2*w*z, 1-2*z^2) — eski get_pose'la ayni
        import math
        beklenen = math.atan2(2 * (0.924 * 0.383), 1 - 2 * 0.383 * 0.383)
        self.assertAlmostEqual(yaw, beklenen, places=6)

    def test_T2_format_B_ayristirma_kilidi(self):
        x, y, z, yaw = ika_surucu.GazeboSurucu.ciktiyi_ayristir(
            "1.5 -2.5 0.1 0.0 0.0 1.57")
        self.assertEqual((x, y, z, yaw), (1.5, -2.5, 0.1, 1.57))

    def test_T2_bozuk_cikti_none_dortlusu(self):
        self.assertEqual(ika_surucu.GazeboSurucu.ciktiyi_ayristir("garbage"),
                         (None, None, None, None))

    def test_T5_zaman_asimi_cokertmez(self):
        surucu = ika_surucu.GazeboSurucu()
        with mock.patch.object(
                ika_surucu.subprocess, "run",
                side_effect=subprocess.TimeoutExpired(cmd="gz", timeout=1)):
            self.assertFalse(surucu.hiz_ver(1.0, 1.0))   # istisna DEGIL False
            self.assertEqual(surucu.ardisik_hata, 1)
        with mock.patch.object(ika_surucu.subprocess, "run",
                               side_effect=OSError("gz yok")):
            self.assertFalse(surucu.hiz_ver(1.0, 1.0))
            self.assertEqual(surucu.ardisik_hata, 2)


class SaglikSozlesmesi(unittest.TestCase):
    def test_T4_gecici_ariza_tolere_edilir(self):
        surucu = ika_surucu.SahteSurucu(arizali_cagrilar={1, 2})
        self.assertFalse(surucu.hiz_ver(1, 1))
        self.assertFalse(surucu.hiz_ver(1, 1))
        self.assertTrue(surucu.saglikli(), "2 hata tavana varmamali")
        self.assertTrue(surucu.hiz_ver(1, 1))
        self.assertEqual(surucu.ardisik_hata, 0, "basari sayaci sifirlamali")

    def test_T3_tavan_asiminda_sagliksiz(self):
        surucu = ika_surucu.SahteSurucu(arizali_cagrilar={1, 2, 3})
        for _ in range(3):
            surucu.hiz_ver(1, 1)
        self.assertFalse(surucu.saglikli())

    def test_T7_gercek_surucu_fail_loud(self):
        with self.assertRaises(ika_surucu.IkaSurucuHatasi) as baglam:
            ika_surucu.GercekSurucu()
        self.assertIn("DONANIM_YOK", str(baglam.exception))


class NavigateFailClosed(unittest.TestCase):
    """T3 — donanim sustu -> navigate durdurmayi dener ve False doner."""

    def tearDown(self):
        ika_nav.surucu_ayarla(None)

    def test_T3_donanim_susunca_ika_durur(self):
        # Poz akisi var (arac ilerliyor gibi) ama komutlar 2. cagridan
        # itibaren ariza veriyor -> tavana varinca navigate birakmali.
        surucu = ika_surucu.SahteSurucu(
            pozlar=[(0.0, 0.0, 0.0, 0.0)],
            arizali_cagrilar=set(range(2, 50)))
        ika_nav.surucu_ayarla(surucu)
        sonuc = ika_nav.navigate([(0.0, 0.0), (5.0, 0.0)], verbose=False)
        self.assertFalse(sonuc, "ON_KAYIT T3: surucu yanitsizken navigate "
                                "False donmeli")
        self.assertGreaterEqual(
            surucu.ardisik_hata, ika_surucu.ARDISIK_HATA_TAVANI)

    def test_T3b_son_komut_durdurma_denemesidir(self):
        denemeler = []

        class KayitliSahte(ika_surucu.SahteSurucu):
            def _hiz_ver(self, sag, sol):
                denemeler.append((sag, sol))
                return len(denemeler) <= 1   # ilk komut gecer, sonra ariza

        surucu = KayitliSahte(pozlar=[(0.0, 0.0, 0.0, 0.0)])
        ika_nav.surucu_ayarla(surucu)
        sonuc = ika_nav.navigate([(0.0, 0.0), (5.0, 0.0)], verbose=False)
        self.assertFalse(sonuc)
        self.assertEqual(denemeler[-1], (0.0, 0.0),
                         "son deneme durdurma (0,0) olmali")


class Surus2_2_5KilidiSurucuYolundan(unittest.TestCase):
    """T6 — §2.2.5: izinler gelmeden surucuye sifir-disi komut DUSMEZ.

    Fark: onceki kapilar `mock.patch(send_vel)` kullanir; burada komutlar
    GERCEK surucu yolundan (surucu_ayarla) akar — soyutlama katmani da
    kilidin altindadir.
    """

    def tearDown(self):
        ika_nav.surucu_ayarla(None)

    def test_T6_izinsiz_sifir_disi_komut_yok_izinle_var(self):
        surucu = ika_surucu.SahteSurucu(pozlar=[
            (0.0, 0.0, 0.0, 0.0), (0.6, 0.0, 0.0, 0.0),
            (1.2, 0.0, 0.0, 0.0), (1.75, 0.0, 0.0, 0.0),
        ])
        ika_nav.surucu_ayarla(surucu)

        alici_link = UDPLink(bind=("127.0.0.1", 0), timeout=0.05)
        receiver = IkaReceiver(alici_link, send_ack=True)
        receiver.start()
        self.addCleanup(receiver.stop)
        hedef = ("127.0.0.1", alici_link.port)
        gonderen = UDPLink(bind=("127.0.0.1", 0), timeout=0.05)

        # 1) izinsiz bekleme: kisa timeout -> False; surucu yalniz (0,0) gordu
        self.assertFalse(
            ika_nav.receiver_surus_izni_bekle(receiver, timeout=0.3))
        izinsiz_komutlar = list(surucu.komutlar)
        self.assertTrue(izinsiz_komutlar, "guvenli durus komutu bile yok")
        self.assertTrue(all(k == (0.0, 0.0) for k in izinsiz_komutlar),
                        f"ON_KAYIT T6: izinsiz sifir-disi komut: "
                        f"{izinsiz_komutlar}")

        # 2) izinleri GERCEK mesajlarla ver: IHA_LANDED + IKA_GO
        gonderen.send(encode(iha_landed(seq=501)), hedef)
        gonderen.send(encode(command("IKA_GO", "ika", seq=502)), hedef)
        self.assertTrue(
            ika_nav.receiver_surus_izni_bekle(receiver, timeout=2.0),
            "izinler verildi ama surus izni acilmadi")

        # 3) izinden sonra surucu yolundan gercek surus: sifir-disi komutlar
        sonuc = ika_nav.navigate([(0.0, 0.0), (2.0, 0.0)], verbose=False)
        self.assertTrue(sonuc, "kisa rota tamamlanmali")
        sifir_disi = [k for k in surucu.komutlar if k != (0.0, 0.0)]
        self.assertTrue(sifir_disi,
                        "izin sonrasi hic sifir-disi komut akmadi")
        self.assertEqual(surucu.komutlar[-1], (0.0, 0.0),
                         "varista son komut durdurma olmali")


class ModulDelegasyonu(unittest.TestCase):
    """T8'in yapisal yarisi: imzalar ve delegasyon."""

    def tearDown(self):
        ika_nav.surucu_ayarla(None)

    def test_send_vel_get_pose_surucuye_delege(self):
        surucu = ika_surucu.SahteSurucu(pozlar=[(1.0, 2.0, 0.0, 0.5)])
        ika_nav.surucu_ayarla(surucu)
        self.assertTrue(ika_nav.send_vel(0.7, 0.3))
        self.assertEqual(surucu.komutlar, [(0.7, 0.3)])
        self.assertEqual(ika_nav.get_pose(), (1.0, 2.0, 0.0, 0.5))

    def test_surucu_ayarlanmadan_saglikli(self):
        ika_nav.surucu_ayarla(None)
        self.assertTrue(ika_nav.surucu_saglikli(),
                        "surucu hic kullanilmadiysa saglikli sayilmali "
                        "(mock'lu testler icin)")

    def test_MUTASYON_saglik_kapisi_navigate_icinde(self):
        """navigate icindeki saglik kapisi sokulursa yakala (D-370 sinifi)."""
        kod = (KOK / "simulation" / "scripts" / "ika_nav.py").read_text(
            encoding="utf-8")
        govde = "\n".join(s for s in kod.splitlines()
                          if not s.lstrip().startswith("#"))
        self.assertIn("if not surucu_saglikli():", govde,
                      "navigate saglik kapisi yok — donanim sustugunda "
                      "fail-closed durus kayboldu")
        mutant = govde.replace("if not surucu_saglikli():", "if False:", 1)
        self.assertNotEqual(govde, mutant, "MUTASYON UYGULANMADI")


if __name__ == "__main__":
    unittest.main()
