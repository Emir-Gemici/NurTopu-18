"""`scripts/arena_kare_teshis.py` nobetcisi — aracin AYIRT EDICI oldugunu sinar.

Bir teshis aracinin tek tehlikesi HER ZAMAN AYNI SEYI SOYLEMESIDIR: hep "GECTI"
diyen bir arac operatoru yanlis guvene, hep "DUSTU" diyen bir arac ise aracin
kendisini terk etmeye goturur. Bu yuzden testler iki YONU de zorlar ve
depodaki GERCEK kareleri kullanir (uydurma dizi degil):

  · saglam kare  -> zincirin 5 halkasi da GECTI, cikis 0
  · bulanik kare -> ilk kopan halka ODAK, cikis 1

Ayrica sirali teshis sozlesmesi sinanir: zemin maskesi 0 piksel iken rota reddi
MASKE_YOK olmali (HEDEF_YOK degil), cunku `analyze_path` HB bloguna varmadan
doner. Bu satir bir kez yanlis olursa saha "HB bozuk" diye yanlis halkayi tamir
etmeye baslar — 20 Eylul'de tam bu risk yasandi (D-524 ek 4).
"""

import subprocess
import sys
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
ARAC = KOK / "scripts" / "arena_kare_teshis.py"
SAGLAM = KOK / "data" / "kabul" / "sentetik_arena_kadraj_t66" / "images" / "val" / "sa_000000.jpg"
BULANIK = KOK / "SAHA_20260920" / "kanit" / "kare_20260920.jpg"

# `SAGLAM` karenin gercek olcegi ~0,0755 m/px; FOV 54 ve 640 px genislikte bunun
# irtifa karsiligi. Yanlis irtifa HB'nin BOYUT bandini dusurur (D-524 ek 1'de
# mimar tam bu hatayi yapti), o yuzden burada aciklamasiyla birlikte durur.
SAGLAM_IRTIFA_M = 47.4


def _kos(*argv):
    sonuc = subprocess.run(
        [sys.executable, "-X", "utf8", "-B", str(ARAC), *argv],
        capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(KOK))
    return sonuc.returncode, (sonuc.stdout or "") + (sonuc.stderr or "")


class AracVar(unittest.TestCase):
    def test_arac_ve_kareler_depoda(self):
        for yol in (ARAC, SAGLAM, BULANIK):
            self.assertTrue(yol.exists(), f"test girdisi depoda yok: {yol}")


class SaglamKare(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.kod, cls.cikti = _kos("--dosya", str(SAGLAM), "--irtifa", str(SAGLAM_IRTIFA_M))

    def test_cikis_kodu_sifir(self):
        self.assertEqual(0, self.kod, self.cikti)

    def test_hukum_gecti(self):
        self.assertIn("zincirin tamami GECTI", self.cikti)

    def test_bes_halkanin_hepsi_gecti(self):
        self.assertEqual(5, self.cikti.count("[OK]"), self.cikti)
        self.assertNotIn("[DUS]", self.cikti)

    def test_rota_gercekten_uretildi(self):
        self.assertRegex(self.cikti, r"5\. rota .*serit \d+ · guven [01]\.\d+ · \d+ waypoint")


class BulanikKare(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.kod, cls.cikti = _kos("--dosya", str(BULANIK), "--irtifa", "30")

    def test_cikis_kodu_bir(self):
        self.assertEqual(1, self.kod, self.cikti)

    def test_ilk_kopan_halka_odak(self):
        self.assertIn("ilk kopan halka: odak", self.cikti)

    def test_odak_bulanik_raporlanir(self):
        self.assertRegex(self.cikti, r"1\. odak .*keskinlik 3\.6 → BULANIK")

    def test_maske_sifir_iken_red_MASKE_YOK_olur(self):
        # Sirali sozlesme: zemin 0 px iken HB'ye SIRA GELMEZ, red MASKE_YOK'tur.
        self.assertRegex(self.cikti, r"5\. rota .*red: MASKE_YOK")
        self.assertNotRegex(self.cikti, r"5\. rota .*red: HEDEF_YOK")

    def test_sonraki_halkalarin_durumu_da_raporlanir(self):
        # Operator tek duzeltmeden sonra ikinci duvara carpmamali: odak dusse bile
        # HB satiri yazilir.
        self.assertIn("3. HB", self.cikti)
        self.assertIn("tumu:", self.cikti)


class OlcekVerilmezse(unittest.TestCase):
    def test_irtifasiz_kosum_fail_open_uyarisi_basar(self):
        kod, cikti = _kos("--dosya", str(SAGLAM))
        self.assertIn("2. olcek (mpp)", cikti)
        self.assertIn("BOYUT ve SEKIL kapilari acilmaz", cikti)
        self.assertIn(str(kod), {"0", "1"})


class YanlisIrtifaHByiDusurur(unittest.TestCase):
    """Ayirt edicilik kaniti: ayni SAGLAM kare, yalniz irtifa iki katina cikarilir.

    Bu mutasyon aracin gercekten olctugunu gosterir — arac irtifayi yok sayiyor
    olsaydi iki kosum da ayni sonucu verirdi.
    """

    def test_iki_kat_irtifada_HB_boyut_bandindan_duser(self):
        kod, cikti = _kos("--dosya", str(SAGLAM), "--irtifa", str(SAGLAM_IRTIFA_M * 2))
        self.assertEqual(1, kod, cikti)
        self.assertIn("3. HB", cikti)
        self.assertIn("aday VAR ama kapidan gecmedi", cikti)
        self.assertIn("ilk kopan halka: HB", cikti)


if __name__ == "__main__":
    unittest.main(verbosity=2)
