"""P4 + P9d (D-394) — SAHA RUNBOOK belge kapisi + tek-komut acilis.

T154 kalibi: runbook'taki surum/komut sozleri koddan/kayit defterinden
DOGRULANIR — belge bayatlarsa bu kapi duser (CONTRACTS §8'in D-308 dersi:
"dosyaya bakan kapi yoksa dosya yalan soyler").
"""
import json
import subprocess
import sys
import time
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
VENV = "O:/navitas-local-train/venv/Scripts/python.exe"
for _y in (KOK / "scripts",):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

import saha_baslat  # noqa: E402

RUNBOOK = (KOK / "SAHA_RUNBOOK.md").read_text(encoding="utf-8")


class RunbookBelgeKapisi(unittest.TestCase):
    def test_uretim_modeli_kayit_defterinden(self):
        """Runbook'taki model adi etkin profilin GERCEK dosyasi olmali."""
        kayit = json.loads((KOK / "config" / "model_registry.json")
                           .read_text(encoding="utf-8"))
        profil = kayit["profiles"][kayit["default_profile"]]
        model_adi = Path(profil["path"]).name
        self.assertIn(model_adi, RUNBOOK,
                      f"runbook etkin uretim modelini ({model_adi}) anmiyor — "
                      "bayat surum riski (D-308 sinifi)")

    def test_bayat_surumler_gecmiyor(self):
        for bayat in ("v34", "v35"):
            self.assertNotIn(bayat, RUNBOOK,
                             f"runbook'ta bayat surum sozu: {bayat}")

    def test_saha_bilesenlerinin_satirlari_var(self):
        for gerekli in ("saha_baslat.py", "iha_inis_yayinci.py", "--sysid",
                        "--kanit-timeout", "--yks", "test_uctan_uca.py",
                        "PROVA_SENARYOSU.md", "GUN1_KONTROL_LISTESI.md"):
            self.assertIn(gerekli, RUNBOOK, f"runbook eksik: {gerekli}")

    def test_kuru_kosu_beklentisi_guncel(self):
        """Runbook tek kopuk halka olarak yalniz `motor` demeli (D-394:
        hedef_konumu kapandi; motor Faz B'ye dek acik)."""
        self.assertIn("`motor`", RUNBOOK)
        self.assertNotIn("hedef_konumu`, `rota", RUNBOOK)

    def test_bayat_belgeler_isaretli(self):
        for yol in ("results/t123/saha_gunu_kontrol_listesi.md",
                    "results/saha_zinciri_20260826/saha_gunu.md"):
            metin = (KOK / yol).read_text(encoding="utf-8")
            self.assertIn("SAHA_RUNBOOK.md", metin,
                          f"{yol} guncel runbook'a isaret etmiyor")
            self.assertIn("TARIHSEL KAYIT", metin)


class SahaBaslatKomutlari(unittest.TestCase):
    """P9d: komutlar TEK yerden uretilir ve gercek bilesenlere isaret eder."""

    def test_yks_komutu(self):
        komut = saha_baslat.komut_uret("yks", ika="10.0.0.2:5006")
        self.assertTrue(komut[1].endswith("yks_gui.py"))
        self.assertEqual(["--ika", "10.0.0.2:5006"], komut[2:])
        self.assertTrue(Path(komut[1]).is_file(), "yks_gui.py yolu gecersiz")

    def test_ika_komutu_yks_adresli(self):
        komut = saha_baslat.komut_uret("ika", yks="10.0.0.1:5005")
        self.assertTrue(komut[1].endswith("ika_nav.py"))
        self.assertEqual("comms", komut[2])
        self.assertIn("--yks", komut, "K8: --yks olmadan aktarim kaniti gitmez")
        self.assertTrue(Path(komut[1]).is_file())

    def test_serial_kipinde_baud(self):
        komut = saha_baslat.komut_uret("yks", serial="COM5", baud=57600)
        self.assertEqual(["--serial", "COM5", "--baud", "57600"], komut[2:])

    def test_bilinmeyen_kip_reddi(self):
        with self.assertRaises(ValueError):
            saha_baslat.komut_uret("jetson")

    def test_acilis_olcumu_ilk_isarete_kadar(self):
        """Gercek alt surecte ilk cikti satirina kadar sure olculur."""
        import io
        cikti = io.StringIO()
        cocuk = saha_baslat.acilis_olc(
            [VENV, "-c", "import time; time.sleep(0.3); print('HAZIR')"],
            cikti=cikti)
        cocuk.wait()
        metin = cikti.getvalue()
        self.assertIn("AÇILIŞ", metin)
        self.assertIn("HAZIR", metin)

    def test_komut_karti_ve_reset_exit0(self):
        for bayrak in ("--komutlar", "--reset"):
            s = subprocess.run([VENV, str(KOK / "scripts" / "saha_baslat.py"),
                                bayrak], capture_output=True, text=True,
                               timeout=60, encoding="utf-8", errors="replace")
            self.assertEqual(0, s.returncode, s.stderr[:200])
        self.assertIn("R tusu", subprocess.run(
            [VENV, str(KOK / "scripts" / "saha_baslat.py"), "--reset"],
            capture_output=True, text=True, timeout=60,
            encoding="utf-8", errors="replace").stdout)


if __name__ == "__main__":
    unittest.main()
