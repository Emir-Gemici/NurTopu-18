"""FAZ B — IKA SURUCU KABUL HARNESSI KILIDI (scripts/ika_surucu_kabul.py).

NEDEN: D-390 surucu soyutlamasini kurdu (CONTRACTS §7.2); 5 Eylul'de
GercekSurucu'nun arka ucu dolacak ve "sozlesmeye uyuyor mu" sorusu MEKANIK bir
kabul turuyla cevaplanacak. Bu dosya o turun kendisini kilitler: harness
bugun SahteSurucu ile GERCEK bilesen uzerinde (mock yok) kosulur; cikis
kodlari (0/1/2) ve adim hukumleri sozlesmedir.

Testler betigi ayri surecte, gercek yorumlayiciyla (sys.executable = venv)
kosar — kullanicinin sahada gorecegi cikti ve exit kodu olculur.
"""
import ast
import io
import json
import shutil
import subprocess
import sys
import tokenize
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
BETIK = KOK / "scripts" / "ika_surucu_kabul.py"

for _y in (KOK / "simulation" / "scripts",):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

import ika_surucu  # noqa: E402


def _kos(*args):
    return subprocess.run(
        [sys.executable, "-B", str(BETIK), *args],
        cwd=str(KOK), capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=120)


def _json_al(cikti):
    ayrac = "--- JSON ---"
    parcalar = cikti.split(ayrac)
    if len(parcalar) != 2:
        raise AssertionError(f"JSON ayraci tam bir kez beklenir; cikti:\n{cikti}")
    return json.loads(parcalar[1])


def _adim(rapor, ad):
    for a in rapor["adimlar"]:
        if a["ad"] == ad:
            return a
    raise AssertionError(f"{ad} raporda yok: {rapor}")


class SahteIleTamTur(unittest.TestCase):
    """(1) sahte ile TUM adimlar GECTI, exit 0."""

    @classmethod
    def setUpClass(cls):
        cls.r = _kos("--surucu", "sahte", "--json")
        cls.rapor = _json_al(cls.r.stdout)

    def test_exit_0_ve_sonuc_gecti(self):
        self.assertEqual(self.r.returncode, 0, self.r.stdout + self.r.stderr)
        self.assertEqual(self.rapor["sonuc"], "GECTI")
        self.assertEqual(self.rapor["cikis_kodu"], 0)
        self.assertNotIn("Traceback", self.r.stderr)

    def test_K1_K6_hepsi_gecti_ve_zorunlu(self):
        adlar = [a["ad"] for a in self.rapor["adimlar"]]
        self.assertEqual(adlar, ["K1", "K2", "K3", "K4", "K5", "K6"])
        for a in self.rapor["adimlar"]:
            self.assertEqual(a["durum"], "GECTI", a)
            self.assertTrue(a["zorunlu"], f"sahte'de {a['ad']} zorunlu olmali")

    def test_K3_rampa_5_adim_hedefe_varir(self):
        k3 = _adim(self.rapor, "K3")
        self.assertEqual(k3["veri"]["basarili_adim"], 5)
        self.assertAlmostEqual(k3["veri"]["hizlar"][-1], 0.30, places=9)
        self.assertLessEqual(self.rapor["rampa"]["hedef_ms"],
                             self.rapor["rampa"]["max_speed_ms"],
                             "rampa hedefi ika_nav.MAX_SPEED'i asamaz")

    def test_K5_tavan_kadar_ariza_sagliksiz_yapar(self):
        k5 = _adim(self.rapor, "K5")
        self.assertEqual(self.rapor["tavan"], ika_surucu.ARDISIK_HATA_TAVANI)
        self.assertEqual(k5["veri"]["ardisik_hata"],
                         ika_surucu.ARDISIK_HATA_TAVANI)
        self.assertFalse(k5["veri"]["saglikli"])

    def test_K6_basarili_komut_sayaci_sifirlar(self):
        k6 = _adim(self.rapor, "K6")
        self.assertEqual(k6["veri"]["ardisik_hata"], 0)
        self.assertEqual(k6["veri"]["toparlanma_ardisik_hata"], 0)

    def test_son_durdur_her_zaman_denenir(self):
        self.assertIs(self.rapor["son_durdur"], True)
        self.assertIn("SON DURDUR", self.r.stdout)

    def test_sahte_icin_gozle_teyit_istenmez(self):
        self.assertFalse(self.rapor["gozle_teyit_gerekli"])
        self.assertNotIn("GOZLE TEYIT ET", self.r.stdout)

    def test_tablo_satirlari_basildi(self):
        for ad in ("K1", "K2", "K3", "K4", "K5", "K6"):
            self.assertRegex(self.r.stdout, rf"(?m)^{ad}\s+GECTI\b")
        self.assertIn("SONUC: GECTI (exit 0)", self.r.stdout)


class SahteArizaliRampa(unittest.TestCase):
    """(2) sahte + arizali_cagrilar -> K3 DUSTU, exit 1; rampa kesilir ama
    arac yine DURDURULUR (K4 GECTI, son durdur True)."""

    @classmethod
    def setUpClass(cls):
        # cagri 1 = K1 durdur; cagri 3 = K3'un 2. adimi
        cls.r = _kos("--surucu", "sahte", "--arizali-cagrilar", "3", "--json")
        cls.rapor = _json_al(cls.r.stdout)

    def test_exit_1_ve_K3_dustu(self):
        self.assertEqual(self.r.returncode, 1, self.r.stdout + self.r.stderr)
        k3 = _adim(self.rapor, "K3")
        self.assertEqual(k3["durum"], "DUSTU")
        self.assertEqual(k3["veri"]["dusen_adim"], 2)
        self.assertEqual(k3["veri"]["basarili_adim"], 1,
                         "ilk False'ta rampa KESILMELI (hizlanmaya devam yok)")
        self.assertEqual(self.rapor["sonuc"], "DUSTU")

    def test_dusen_adimda_durmaz_arac_durdurulur(self):
        self.assertEqual(_adim(self.rapor, "K1")["durum"], "GECTI")
        self.assertEqual(_adim(self.rapor, "K4")["durum"], "GECTI",
                         "K3 dusse de durdur() denenmeli ve basarili olmali")
        self.assertIs(self.rapor["son_durdur"], True)
        self.assertIn("SONUC: DUSTU (exit 1)", self.r.stdout)

    def test_K1_arizasi_da_exit_1(self):
        r = _kos("--surucu", "sahte", "--arizali-cagrilar", "1", "--json")
        rapor = _json_al(r.stdout)
        self.assertEqual(r.returncode, 1)
        self.assertEqual(_adim(rapor, "K1")["durum"], "DUSTU")


class GercekArkaUcsuz(unittest.TestCase):
    """(3) gercek + arka uc yok -> exit 2 ve DONANIM_YOK metni; cokme yok."""

    def test_exit_2_donanim_yok(self):
        r = _kos("--surucu", "gercek")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("DONANIM_YOK", r.stdout)
        self.assertIn("beklenen (Faz B oncesi)", r.stdout)
        self.assertNotIn("Traceback", r.stderr)

    def test_bozuk_arka_uc_exit_2_ve_acik_sebep(self):
        r = _kos("--surucu", "gercek", "--arka-uc", "olmayan_modul_xyz:Sinif")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("SURUCU_KURULAMADI", r.stdout)
        self.assertIn("olmayan_modul_xyz", r.stdout)
        self.assertNotIn("Traceback", r.stderr)


class GazeboGzYok(unittest.TestCase):
    """gazebo secilip gz yoksa: hiz_ver False -> K3 DUSTU 'gz komutu yok',
    exit 1, COKME YOK."""

    def test_gz_yokken_dustu_ama_cokmedi(self):
        if shutil.which("gz") is not None:
            self.skipTest("gz mevcut; bu kilit gz'siz gelistirme makinesi icindir")
        r = _kos("--surucu", "gazebo", "--json")
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        rapor = _json_al(r.stdout)
        k3 = _adim(rapor, "K3")
        self.assertEqual(k3["durum"], "DUSTU")
        self.assertIn("gz komutu yok", k3["sebep"])
        self.assertEqual(_adim(rapor, "K5")["durum"], "ATLANDI")
        self.assertFalse(_adim(rapor, "K5")["zorunlu"])
        self.assertTrue(rapor["gozle_teyit_gerekli"])
        self.assertIn("GOZLE TEYIT ET", r.stdout)


class KonumYokUyarisi(unittest.TestCase):
    """K2: hepsi None -> KONUM YOK uyarisiyla KABUL (dusurmez)."""

    def test_konum_yok_uyari_ile_gecer(self):
        r = _kos("--surucu", "sahte", "--sahte-konum-yok", "--json")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        k2 = _adim(_json_al(r.stdout), "K2")
        self.assertEqual(k2["durum"], "GECTI")
        self.assertIn("KONUM YOK", k2["uyari"])
        self.assertIn("KONUM YOK", r.stdout)


class MetinKilidi(unittest.TestCase):
    """(4) ARDISIK_HATA_TAVANI ika_surucu'dan IMPORT edilir; kaynakta ciplak
    '3' sayi belirteci yok (madde 16)."""

    @classmethod
    def setUpClass(cls):
        cls.kaynak = BETIK.read_text(encoding="utf-8")

    def test_tavan_ika_surucu_dan_import_edilir(self):
        agac = ast.parse(self.kaynak)
        ithal = [
            n for n in ast.walk(agac)
            if isinstance(n, ast.ImportFrom) and n.module == "ika_surucu"
            and any(a.name == "ARDISIK_HATA_TAVANI" for a in n.names)
        ]
        self.assertTrue(ithal, "from ika_surucu import ARDISIK_HATA_TAVANI yok")

    def test_ciplak_3_sayi_belirteci_yok(self):
        sayilar = [
            (t.start[0], t.string)
            for t in tokenize.generate_tokens(io.StringIO(self.kaynak).readline)
            if t.type == tokenize.NUMBER and t.string == "3"
        ]
        self.assertEqual(sayilar, [], f"ciplak 3 bulundu (satir, belirtec): "
                                      f"{sayilar}")

    def test_neden_dokstringi_var(self):
        dok = ast.get_docstring(ast.parse(self.kaynak)) or ""
        self.assertIn("NEDEN", dok)
        self.assertIn("7.2", dok)


if __name__ == "__main__":
    unittest.main()
