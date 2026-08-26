"""T161 KAPISI (ON_KAYIT SS22 · REVIEW_LOG D-300): depo koku `__file__`den TURETILIR.

KUSUR: `scripts/olcum/ayarlar.py` depo kokunu CIPLAK MUTLAK YOL olarak tutuyordu.
36 olcum betigi `from ayarlar import REPO` + `sys.path.insert(0, REPO / "codes")`
yaptigi icin, bir worktree'de (ya da deponun herhangi bir kopyasinda) kosan
kapilar KENDI kodunu degil ANA DEPONUNKINI import ediyordu. Yani worktree
ajaninin yazdigi kod OLCULMEDEN yesil gorunebiliyordu — D-15 sinifi vakum kapi.

BOS KAPI YASAGI (TEST_SPECS SS4.1): "kok turetiliyor" demek yetmez. Kapi
UCTAN UCA olcer: sahte bir agac kurulur, kendi `codes/rpi_inference.py`si
konur, ALT SUREC o agactan kosulur ve GERCEKTEN kendi modulunu yukledigi
dogrulanir. Ciplak yol geri konursa desen kilidi DUSER.
"""

from __future__ import annotations

import ast
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
OLCUM_AYARLAR = KOK / "scripts" / "olcum" / "ayarlar.py"
EGITIM_AYARLAR = KOK / "navitas-local-train" / "ayarlar.py"

# Ciplak depo koku: `Path(r"X:\...navitas")` bicimindeki her atama.
CIPLAK_KOK = re.compile(r'Path\(\s*r?["\'][A-Za-z]:[\/]{1,2}navitas["\']\s*\)')


class CiplakYolYasagi(unittest.TestCase):
    """Kok ATAMASI ciplak mutlak yol olamaz (madde 16)."""

    def test_olcum_ayarlarinda_ciplak_kok_yok(self):
        s = OLCUM_AYARLAR.read_text(encoding="utf-8")
        self.assertIsNone(CIPLAK_KOK.search(s),
                          "scripts/olcum/ayarlar.py'de ciplak depo koku geri geldi")
        self.assertIn("_depo_koku(__file__)", s)

    def test_egitim_ayarlarinda_ciplak_kok_yok(self):
        s = EGITIM_AYARLAR.read_text(encoding="utf-8")
        self.assertIsNone(CIPLAK_KOK.search(s),
                          "navitas-local-train/ayarlar.py'de ciplak depo koku geri geldi")
        self.assertIn("_depo_koku(__file__)", s)

    def test_dort_betik_kendi_koku_tanimlamiyor(self):
        """63/69/70/71 kendi ciplak REPO'sunu tanimliyordu; artik `ayarlar`dan alir."""
        for ad in ("63_bariyer_kesisimi", "69_arac_referans_olcegi",
                   "70_gercek_kare_rota_denemesi", "71_gercek_kare_etiketleyici"):
            s = (KOK / "scripts" / "olcum" / f"{ad}.py").read_text(encoding="utf-8")
            with self.subTest(betik=ad):
                self.assertIsNone(CIPLAK_KOK.search(s),
                                  f"{ad}: ciplak depo koku geri geldi")
                self.assertIn("from ayarlar import REPO", s)


class BulucuAynasi(unittest.TestCase):
    """Iki `ayarlar.py`deki `_depo_koku` BIREBIR ayni kalmali (ithal edilemiyor)."""

    @staticmethod
    def _govde(yol: Path) -> str:
        agac = ast.parse(yol.read_text(encoding="utf-8"))
        for d in agac.body:
            if isinstance(d, ast.FunctionDef) and d.name == "_depo_koku":
                return ast.dump(d, annotate_fields=True)
        raise AssertionError(f"_depo_koku yok: {yol}")

    def test_iki_kopya_ayni(self):
        self.assertEqual(self._govde(OLCUM_AYARLAR), self._govde(EGITIM_AYARLAR),
                         "iki ayarlar.py'deki _depo_koku ayrismis (ayna bozuldu)")


class AnaDepodaBozulmama(unittest.TestCase):
    """Ana depoda deger DEGISMEDI — davranis ayni, yalniz turetme degisti."""

    def test_olcum_repo_ana_depoyu_gosteriyor(self):
        sys.path.insert(0, str(KOK / "scripts" / "olcum"))
        try:
            import ayarlar
            self.assertEqual(KOK.resolve(), Path(ayarlar.REPO).resolve())
        finally:
            sys.path.pop(0)

    def test_isaretciler_ana_depoda_var(self):
        self.assertTrue((KOK / "CLAUDE.md").is_file())
        self.assertTrue((KOK / "codes").is_dir())


class UctanUcaKopyaAgac(unittest.TestCase):
    """🔴 ASIL KAPI: kopya agac KENDI `codes/`ini yuklemeli, ana depoyu DEGIL."""

    def _kos(self, ayarlar_kaynagi: Path):
        with tempfile.TemporaryDirectory() as td:
            kok = Path(td) / "sahte_depo"
            (kok / "codes").mkdir(parents=True)
            (kok / "scripts" / "olcum").mkdir(parents=True)
            (kok / "CLAUDE.md").write_text("# sahte depo koku\n", encoding="utf-8")
            (kok / "codes" / "rpi_inference.py").write_text(
                'SENTINEL = "TMP"\n', encoding="utf-8")
            shutil.copy2(ayarlar_kaynagi, kok / "scripts" / "olcum" / "ayarlar.py")
            prob = kok / "scripts" / "olcum" / "prob.py"
            prob.write_text(
                "import sys\n"
                "from pathlib import Path\n"
                "sys.path.insert(0, str(Path(__file__).parent))\n"
                "from ayarlar import REPO\n"
                "sys.path.insert(0, str(REPO / 'codes'))\n"
                "import rpi_inference\n"
                "print('SENTINEL=' + getattr(rpi_inference, 'SENTINEL', 'YOK'))\n"
                "print('KAYNAK=' + rpi_inference.__file__)\n",
                encoding="utf-8")
            return subprocess.run([sys.executable, str(prob)],
                                  capture_output=True, text=True, cwd=str(kok))

    def test_kopya_agac_kendi_kodunu_yukler(self):
        cp = self._kos(OLCUM_AYARLAR)
        self.assertEqual(0, cp.returncode, cp.stderr[-800:])
        self.assertIn("SENTINEL=TMP", cp.stdout,
                      "kopya agac ANA DEPONUN rpi_inference'ini yukledi "
                      f"(T161 geri geldi): {cp.stdout!r}")
        self.assertNotIn(str(KOK), cp.stdout.split("KAYNAK=")[-1],
                         "yuklenen modul ana depodan geldi")

    def test_MUTASYON_ciplak_kok_geri_konursa_kapi_duser(self):
        """Ciplak yollu bir `ayarlar.py` ayni agacta ANA DEPOYU yukler."""
        with tempfile.TemporaryDirectory() as td:
            mutant = Path(td) / "ayarlar.py"
            mutant.write_text(
                "from pathlib import Path\n"
                f'REPO = Path(r"{KOK}")\n', encoding="utf-8")
            cp = self._kos(mutant)
        self.assertNotIn("SENTINEL=TMP", cp.stdout,
                         "mutant ciplak yol KENDI kodunu yukledi — kapi bos, "
                         "olcum ayrimi yapmiyor")


class DepoDisindaCanliKlasor(unittest.TestCase):
    """`olcum_ayna.py` bu dosyayi deponun DISINA (canli calisma klasoru)
    kopyaliyor. Orada isaretci yukarida YOKTUR; bulucu kardes dizinlerde TEK
    isaretcili depoyu bulmali — bulamazsa fail-closed (ciplak yol varsaymaz)."""

    def test_depo_disinda_kardes_taramasiyla_bulunur(self):
        surucu = Path(KOK.anchor)                     # ornegin "O:\\"
        with tempfile.TemporaryDirectory(dir=str(surucu)) as td:
            hedef = Path(td) / "ayarlar.py"
            shutil.copy2(OLCUM_AYARLAR, hedef)
            cp = subprocess.run(
                [sys.executable, "-c",
                 "import sys;sys.path.insert(0, sys.argv[1]);"
                 "from ayarlar import REPO;print(REPO)", str(td)],
                capture_output=True, text=True)
        self.assertEqual(0, cp.returncode, cp.stderr[-600:])
        self.assertEqual(KOK.resolve(), Path(cp.stdout.strip()).resolve())

    def test_isaretcisiz_yalitilmis_agacta_FAIL_CLOSED(self):
        """Hicbir kademe tutmazsa sessiz varsayim YOK — ImportError."""
        with tempfile.TemporaryDirectory() as td:
            yalitik = Path(td) / "a" / "b"
            yalitik.mkdir(parents=True)
            shutil.copy2(OLCUM_AYARLAR, yalitik / "ayarlar.py")
            cp = subprocess.run(
                [sys.executable, "-c",
                 "import sys;sys.path.insert(0, sys.argv[1]);import ayarlar",
                 str(yalitik)],
                capture_output=True, text=True,
                env={"SYSTEMROOT": __import__("os").environ.get("SYSTEMROOT", ""),
                     "PATH": __import__("os").environ.get("PATH", "")})
        self.assertNotEqual(0, cp.returncode, "isaretcisiz agacta sessizce gecti")
        self.assertIn("depo koku bulunamadi", cp.stderr)

    def test_ORTAM_degiskeni_ezer(self):
        with tempfile.TemporaryDirectory() as td:
            yalitik = Path(td) / "a"
            yalitik.mkdir(parents=True)
            shutil.copy2(OLCUM_AYARLAR, yalitik / "ayarlar.py")
            ortam = dict(__import__("os").environ, NAVITAS_DEPO=str(KOK))
            cp = subprocess.run(
                [sys.executable, "-c",
                 "import sys;sys.path.insert(0, sys.argv[1]);"
                 "from ayarlar import REPO;print(REPO)", str(yalitik)],
                capture_output=True, text=True, env=ortam)
        self.assertEqual(0, cp.returncode, cp.stderr[-600:])
        self.assertEqual(KOK.resolve(), Path(cp.stdout.strip()).resolve())


if __name__ == "__main__":
    unittest.main()
