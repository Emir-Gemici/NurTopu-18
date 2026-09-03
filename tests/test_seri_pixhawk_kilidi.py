"""NEDEN (FDR/ACIK_KALEMLER §4b #23 · CONTRACTS §7.4 · D-403): Jetson'da
`/dev/ttyACM0` TEK SAHIPLIDIR ve UC uretim sureci onu istiyor —
`codes/rpi_inference.py` (bagil irtifa), `comms/iha_inis_yayinci.py` (inis
kaniti) ve `comms/iha_komut_alici.py` (PARACHUTE/ARM aktarimi). Ikinci surec
portu acarsa cerceveler bolunur ve IKI TARAF DA SESSIZCE KOR olur.

OLCULEN KUSUR (bu dosyanin varlik sebebi): kural CONTRACTS'ta yaziliydi ama
YALNIZ `iha_komut_alici`da KODLUYDU. Diger ikisi `--mavlink /dev/ttyACM0`
degerini KABUL EDIYORDU; ustelik `iha_inis_yayinci`nin modul kilavuzu bunu
ORNEK olarak gosteriyordu — yani belge sozlesmeyi ihlal etmeyi OGRETIYORDU.

BU DOSYANIN ISI: kilidin UCUNDE DE, AYNI mekanizmayla acik oldugunu
kanitlamak. "Ayni" burada olculur bir sozdur:
  * ayni bayrak adi   -> `--seri-pixhawk-bilerek` (dest `seri_pixhawk_bilerek`)
  * ayni hata metni   -> `inis_kaniti.seri_pixhawk_kilit_metni` BIREBIR
  * ayni cikis kodu   -> argparse `parser.error` = 2
Metin tek kaynaktan uretilir; uc surecin biri kalibi kopyalayip ayrisirsa
`test_3_*` duser.
"""

import contextlib
import io
import sys
import unittest
from pathlib import Path
from unittest import mock

KOK = Path(__file__).resolve().parents[1]
for _yol in (KOK / "comms", KOK / "codes"):
    if str(_yol) not in sys.path:
        sys.path.insert(0, str(_yol))

import iha_inis_yayinci as inis  # noqa: E402
import iha_komut_alici as komut  # noqa: E402
import inis_kaniti as kanit  # noqa: E402
import rpi_inference as ri  # noqa: E402

# Reddedilmesi gereken kaliplar: Linux, Windows ve pyserial URL yollari.
SERI_YOLLAR = ("/dev/ttyACM0", "/dev/ttyUSB0", "COM7", "serial:/dev/ttyUSB0")
# Kabul edilmesi gereken cogullayici uclari (CONTRACTS §7.4 tablosu).
COGULLAYICI_UCLARI = ("udp:127.0.0.1:14550", "udp:127.0.0.1:14551",
                      "udp:127.0.0.1:14552", "udpin:0.0.0.0:14550",
                      "tcp:127.0.0.1:5760")
YEREL = "127.0.0.1"


def _stderr_ile_cikis(cagri):
    """`cagri`yi kos; (SystemExit kodu, stderr metni) dondur."""
    yakala = io.StringIO()
    with contextlib.redirect_stderr(yakala):
        try:
            cagri()
        except SystemExit as exc:
            return exc.code, yakala.getvalue()
    return None, yakala.getvalue()


# ── 1) rpi_inference (BUGUNE DEK KILITSIZ) ───────────────────────────────────

class RpiInferenceKilidi(unittest.TestCase):
    def _dogrula(self, argv):
        parser = ri._arguman_ayristirici()
        args = parser.parse_args(argv)
        return _stderr_ile_cikis(lambda: ri._argumanlari_dogrula(parser, args))

    def test_1_seri_cihaz_REDDEDILIR(self):
        for yol in SERI_YOLLAR:
            with self.subTest(yol=yol):
                kod, hata = self._dogrula(
                    ["--camera", "--mavlink", yol, "--mav-sysid", "1",
                     "--fov", "60"])
                self.assertEqual(2, kod, f"{yol}: kilit ACIK degil")
                self.assertIn("TEK SAHIPLIDIR", hata)

    def test_2_cogullayici_ucu_KABUL_EDILIR(self):
        for uc in COGULLAYICI_UCLARI:
            with self.subTest(uc=uc):
                kod, _ = self._dogrula(
                    ["--camera", "--mavlink", uc, "--mav-sysid", "1",
                     "--fov", "60"])
                self.assertIsNone(kod, f"{uc}: mesru uc reddedildi")

    def test_3_bilerek_bayragi_kilidi_ACAR(self):
        kod, _ = self._dogrula(
            ["--camera", "--mavlink", "/dev/ttyACM0", "--mav-sysid", "1",
             "--fov", "60", "--seri-pixhawk-bilerek"])
        self.assertIsNone(kod)

    def test_4_bayrak_VARSAYILAN_OLARAK_KAPALI(self):
        """Fail-closed: bayrak verilmezse kilit acik sayilmaz."""
        args = ri._arguman_ayristirici().parse_args(
            ["--camera", "--mavlink", "udp:127.0.0.1:14550",
             "--mav-sysid", "1", "--fov", "60"])
        self.assertFalse(args.seri_pixhawk_bilerek)

    def test_5_mavlinksiz_kosumda_kilit_KARISMAZ(self):
        """--image/--video yollari (mavlink None) etkilenmez."""
        kod, _ = self._dogrula(["--video", "x.mp4", "--mpp", "0.05"])
        self.assertIsNone(kod)


# ── 2) iha_inis_yayinci (BUGUNE DEK KILITSIZ; KILAVUZU DA YANLISTI) ──────────

class InisYayinciKilidi(unittest.TestCase):
    def _main(self, argv):
        return _stderr_ile_cikis(lambda: inis.main(argv))

    def test_1_seri_cihaz_REDDEDILIR(self):
        for yol in SERI_YOLLAR:
            with self.subTest(yol=yol):
                kod, hata = self._main(
                    ["--mavlink", yol, "--kanit-timeout", "5",
                     "--ika", "10.0.0.2:5006"])
                self.assertEqual(2, kod, f"{yol}: kilit ACIK degil")
                self.assertIn("TEK SAHIPLIDIR", hata)

    def test_2_kilit_BAGLANTI_ACILMADAN_ONCE_kosar(self):
        """Port bir an icin bile kapilmaz: `mavlink_baglantisi_ac` CAGRILMAZ."""
        with mock.patch.object(inis, "mavlink_baglantisi_ac") as ac:
            kod, _ = self._main(["--mavlink", "/dev/ttyACM0",
                                 "--kanit-timeout", "5",
                                 "--ika", "10.0.0.2:5006"])
        self.assertEqual(2, kod)
        ac.assert_not_called()

    def test_3_bilerek_bayragi_kilidi_ACAR(self):
        """Bayrakla parser hatasi YOK; akis baglanti yoluna gecer (kod 2, ama
        `parser.error` degil — `mavlink_baglantisi_ac` cagrilmis olmali)."""
        with mock.patch.object(inis, "mavlink_baglantisi_ac",
                               side_effect=ConnectionError("yok")) as ac, \
                contextlib.redirect_stderr(io.StringIO()):
            kod = inis.main(["--mavlink", "/dev/ttyACM0",
                             "--seri-pixhawk-bilerek", "--kanit-timeout", "5",
                             "--ika", "10.0.0.2:5006"])
        self.assertEqual(2, kod)
        ac.assert_called_once_with("/dev/ttyACM0")

    def test_4_cogullayici_ucu_KABUL_EDILIR(self):
        with mock.patch.object(inis, "mavlink_baglantisi_ac",
                               side_effect=ConnectionError("yok")) as ac, \
                contextlib.redirect_stderr(io.StringIO()):
            kod = inis.main(["--mavlink", "udp:127.0.0.1:14551",
                             "--kanit-timeout", "5", "--ika", "10.0.0.2:5006"])
        self.assertEqual(2, kod)
        ac.assert_called_once_with("udp:127.0.0.1:14551")

    def test_5_modul_kilavuzu_seri_cihaz_ORNEGI_VERMEZ(self):
        """Kilavuz `--mavlink /dev/ttyACM0` OGRETIYORDU — geri konmasin."""
        kaynak = (KOK / "comms" / "iha_inis_yayinci.py").read_text(
            encoding="utf-8")
        dokstring = kaynak.split('"""')[1]
        for yol in SERI_YOLLAR:
            self.assertNotIn(f"--mavlink {yol}", dokstring,
                             "kilavuz sozlesmeyi ihlal etmeyi ogretiyor")
        self.assertIn("--mavlink udp:127.0.0.1:14551", dokstring,
                      "kilavuz bu surecin cogullayici ucunu gostermeli")


# ── 3) UC SURECTE DE AYNI MEKANIZMA (kopyalanan kalip ayrisamasin) ───────────

class KilitTekKaynaktan(unittest.TestCase):
    def test_1_uc_surec_de_AYNI_bayragi_tanir(self):
        ayristiricilar = {
            "rpi_inference": ri._arguman_ayristirici(),
            "iha_inis_yayinci": inis._arg_parser(),
            "iha_komut_alici": komut._arg_parser(),
        }
        for ad, ayristirici in ayristiricilar.items():
            with self.subTest(surec=ad):
                secenekler = {
                    s for eylem in ayristirici._actions
                    for s in eylem.option_strings
                }
                self.assertIn(kanit.SERI_PIXHAWK_BILEREK_BAYRAGI, secenekler,
                              f"{ad}: bayrak adi ayristi")

    def test_2_uc_surec_de_AYNI_hata_metnini_basar(self):
        beklenen = kanit.seri_pixhawk_kilit_metni("/dev/ttyACM0")
        # Metin bos ya da genel bir sey olmasin: kilidin ozunu tasimali.
        self.assertIn("TEK SAHIPLIDIR", beklenen)
        self.assertIn("CONTRACTS", beklenen)

        _, rpi_hata = _stderr_ile_cikis(
            lambda: ri._argumanlari_dogrula(
                ri._arguman_ayristirici(),
                ri._arguman_ayristirici().parse_args(
                    ["--camera", "--mavlink", "/dev/ttyACM0",
                     "--mav-sysid", "1", "--fov", "60"])))
        _, inis_hata = _stderr_ile_cikis(
            lambda: inis.main(["--mavlink", "/dev/ttyACM0",
                               "--kanit-timeout", "5",
                               "--ika", "10.0.0.2:5006"]))
        _, komut_hata = _stderr_ile_cikis(
            # NEDEN `--izinli-kaynak` (3 Eylul): Codex kritik eyleyiciye
            # kaynak pinini ZORUNLU kildi. Verilmezse argparse SERI KILIDE
            # ULASMADAN hata veriyor ve bu test yanlis sebeple dusuyordu.
            # Iki sertlestirme de dogru; test ikisini de gecmelidir.
            lambda: komut.main(["--mavlink", "/dev/ttyACM0",
                                "--bind", f"{YEREL}:0",
                                "--izinli-kaynak", f"{YEREL}:5005"]))
        for ad, hata in (("rpi_inference", rpi_hata),
                         ("iha_inis_yayinci", inis_hata),
                         ("iha_komut_alici", komut_hata)):
            with self.subTest(surec=ad):
                self.assertIn(beklenen, hata, f"{ad}: hata metni ayristi")

    def test_3_yordam_saf_metindir_pymavlink_ISTEMEZ(self):
        """Kilit `--fps/--image` yolunu pymavlink'e bagimli kilmamali."""
        self.assertTrue(kanit.seri_pixhawk_yolu_mu("/dev/ttyACM0"))
        self.assertFalse(kanit.seri_pixhawk_yolu_mu("udp:127.0.0.1:14550"))
        self.assertFalse(kanit.seri_pixhawk_yolu_mu(None))


if __name__ == "__main__":
    unittest.main()
