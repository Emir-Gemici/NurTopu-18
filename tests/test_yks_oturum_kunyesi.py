"""YKİ kanıt kaydı, koşunun yeniden kurulabilir başlangıç künyesini taşır."""

import ast
import sys
import unittest
from pathlib import Path
from unittest import mock


KOK = Path(__file__).resolve().parents[1]
GUI_YOLU = KOK / "comms" / "yks_gui.py"
if str(KOK / "comms") not in sys.path:
    sys.path.insert(0, str(KOK / "comms"))

import yks_gui  # noqa: E402


class OturumKunyesiTests(unittest.TestCase):
    def test_kunye_model_ag_ve_calistirma_baglamini_kaydeder(self):
        profil = {
            "model_id": "navitas-seg-v35-512",
            "path": "models/navitas_seg_v35_best.pt",
            "imgsz": 512,
            "sha256": "ab" * 32,
        }
        commit = "12" * 20
        with (mock.patch.object(yks_gui, "_kayit_profili",
                                return_value=(profil, Path("registry.json"))),
              mock.patch.object(yks_gui, "_repo_commit_oku",
                                return_value=commit)):
            kunye = yks_gui.yki_oturum_kunyesi(
                fda_kipi=True,
                dinleme="0.0.0.0:5005",
                iha_hedef=("10.0.0.2", 5007),
                ika_hedef=("10.0.0.3", 5006),
                seri_port=None,
                baud=57600,
                kamera_url="http://10.0.0.2:8080",
                algi_kaynagi="arena_kadraj",
                gorunum="kamera",
                baslatma_argumanlari=("--fda", "--kamera-url", "http://10.0.0.2:8080"),
            )

        self.assertEqual("fda", kunye["gorev_kipi"])
        self.assertTrue(kunye["fda_kipi"])
        self.assertEqual(yks_gui.PROTOCOL_VERSION, kunye["protokol_surum"])
        self.assertEqual(["10.0.0.2", 5007], kunye["iha_hedef"])
        self.assertEqual(["10.0.0.3", 5006], kunye["ika_hedef"])
        self.assertIsNone(kunye["baud"],
                          "UDP koşusunda kullanılmayan seri baud kanıt diye yazılmamalı")
        self.assertEqual("navitas_seg_v35_best.pt", kunye["model"]["dosya"])
        self.assertEqual(profil["sha256"], kunye["model"]["sha256"])
        self.assertEqual(commit, kunye["repo_commit"])
        self.assertEqual("arena_kadraj", kunye["algi_kaynagi"])
        self.assertEqual("kamera", kunye["gorunum"])
        self.assertEqual(
            ["--fda", "--kamera-url", "http://10.0.0.2:8080"],
            kunye["baslatma_argumanlari"])

    def test_git_kimligi_yoksa_kunye_uydurmaz(self):
        with (mock.patch.object(yks_gui, "_kayit_profili",
                                return_value=({}, Path("registry.json"))),
              mock.patch.object(yks_gui, "_repo_commit_oku", return_value=None)):
            kunye = yks_gui.yki_oturum_kunyesi(
                fda_kipi=False, dinleme="COM5", seri_port="COM5", baud=57600)

        self.assertIsNone(kunye["repo_commit"])
        self.assertEqual(57600, kunye["baud"])
        self.assertEqual("COM5", kunye["seri_port"])

    def test_hazir_olayi_zorunlu_alanlarla_kunyeyi_birlestirir(self):
        kayit = mock.Mock()
        link = mock.Mock()
        kunye = {"repo_commit": "34" * 20, "kamera_url": None,
                 "model": {"model_id": "navitas-seg-v35-512"}}
        with (mock.patch.object(yks_gui, "HakemKaydi", return_value=kayit),
              mock.patch.object(yks_gui.YksArayuz, "_arayuz_kur"),
              mock.patch.object(yks_gui.YksArayuz, "_dinle"),
              mock.patch.object(yks_gui.YksArayuz, "_tik"),
              mock.patch.object(yks_gui.threading, "Thread") as thread):
            uygulama = yks_gui.YksArayuz(
                mock.Mock(), link, demo=False, hakem_log_yolu=Path("kanıt.jsonl"),
                oturum_kunyesi=kunye)

        kayit.yaz.assert_called_once()
        olay, = kayit.yaz.call_args.args
        alanlar = kayit.yaz.call_args.kwargs
        self.assertEqual("YKS_ARAYUZ_HAZIR", olay)
        self.assertFalse(alanlar["demo"])
        self.assertEqual("udp", alanlar["tasiyici"])
        self.assertEqual(uygulama.komut_oturumu, alanlar["komut_oturumu"])
        self.assertEqual(kunye["repo_commit"], alanlar["repo_commit"])
        self.assertEqual(kunye["model"], alanlar["model"])
        thread.return_value.start.assert_called_once_with()

    def test_kunye_zorunlu_kaynak_alanini_ezemez(self):
        with (mock.patch.object(yks_gui, "HakemKaydi", return_value=mock.Mock()),
              mock.patch.object(yks_gui.YksArayuz, "_arayuz_kur"),
              mock.patch.object(yks_gui.YksArayuz, "_dinle"),
              mock.patch.object(yks_gui.YksArayuz, "_tik"),
              mock.patch.object(yks_gui.threading, "Thread")):
            with self.assertRaisesRegex(ValueError, "zorunlu alanı ezemez"):
                yks_gui.YksArayuz(
                    mock.Mock(), mock.Mock(), hakem_log_yolu=Path("kanıt.jsonl"),
                    oturum_kunyesi={"tasiyici": "serial"})


class MainBaglantisiTests(unittest.TestCase):
    def test_main_kunyeyi_uretir_ve_arayuze_aktarir(self):
        agac = ast.parse(GUI_YOLU.read_text(encoding="utf-8"),
                         filename=str(GUI_YOLU))
        main = next(n for n in agac.body
                    if isinstance(n, ast.FunctionDef) and n.name == "main")
        cagrilar = [n for n in ast.walk(main) if isinstance(n, ast.Call)]

        self.assertTrue(any(
            isinstance(c.func, ast.Name) and c.func.id == "yki_oturum_kunyesi"
            for c in cagrilar), "main() oturum künyesi üretmiyor")
        kurucular = [c for c in cagrilar
                     if isinstance(c.func, ast.Name) and c.func.id == "YksArayuz"]
        self.assertEqual(1, len(kurucular))
        anahtar = {k.arg: k.value for k in kurucular[0].keywords}
        self.assertIn("oturum_kunyesi", anahtar)
        self.assertIsInstance(anahtar["oturum_kunyesi"], ast.Name)
        self.assertEqual("oturum_kunyesi", anahtar["oturum_kunyesi"].id)


if __name__ == "__main__":
    unittest.main()
