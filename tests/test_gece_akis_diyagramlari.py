"""Akis diyagramlari nobetcisi — Y-3.3.4-M01 (FDR §3.3.4.1.17).

🔴 KORUNAN KUSUR (6 Eylul gecesi, curutucu): diyagramlarda dosya:satir
tasimayan sozde dugumler vardi ("Cx0 yok sayilir" gibi). Kod degisince
diyagram sessizce yalan soyler. Bu kapi:

  1. FDR/sekiller/akis_{a..e}.mmd ve .svg VAR; svg `<svg` ile baslar,
     > 2 KB, XML olarak ayrisir.
  2. Her .mmd'nin HER dugumu (alt-grafik basliklari dahil) dosya:satir
     tasir ve metin GERCEKTEN o dosyada o satirda (±3) durur —
     `scripts/akis_diyagram_dogrula.py` ile; %100 tutmali, esik gevsetilmez.
     Kenarlarda tanimsiz ID (Mermaid'in kendiliginden urettigi dugum) YOK.
  3. .mmd basligi "koddan turetildi <commit> <tarih>" tasir.
  4. akis_<x>_dugumler.md tablosu .mmd'den yeniden uretilenle BIREBIR ayni
     (bayat tablo yok).
  5. SVG, .mmd'den turetilmis: her dugumun dosya:satir metni SVG'de gecer.
  6. Pozitif kontrol: dogrulayici yanlis satiri, dosya:satirsiz dugumu ve
     tanimsiz kenar ID'sini YAKALAR (yakalamayan dogrulayici kapi degildir).
"""
import importlib.util as _u
import re
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
SEKILLER = KOK / "FDR" / "sekiller"
BETIK = KOK / "scripts" / "akis_diyagram_dogrula.py"
HARFLER = ("a", "b", "c", "d", "e")
ASGARI_SVG_BAYT = 2048
ASGARI_DUGUM = 20

_sp = _u.spec_from_file_location("akis_dogrula", BETIK)
M = _u.module_from_spec(_sp)
sys.modules["akis_dogrula"] = M
_sp.loader.exec_module(M)


def _mmd(harf):
    return (SEKILLER / f"akis_{harf}.mmd").read_text(encoding="utf-8")


class DosyalarVar(unittest.TestCase):
    def test_bes_mmd_ve_bes_svg(self):
        for h in HARFLER:
            self.assertTrue((SEKILLER / f"akis_{h}.mmd").is_file(), f"akis_{h}.mmd yok")
            self.assertTrue((SEKILLER / f"akis_{h}.svg").is_file(), f"akis_{h}.svg yok")
            self.assertTrue((SEKILLER / f"akis_{h}_dugumler.md").is_file(),
                            f"akis_{h}_dugumler.md yok")

    def test_svg_baslangic_boyut_xml(self):
        for h in HARFLER:
            yol = SEKILLER / f"akis_{h}.svg"
            veri = yol.read_bytes()
            self.assertTrue(veri.startswith(b"<svg"), f"{yol.name} '<svg' ile baslamiyor")
            self.assertGreater(len(veri), ASGARI_SVG_BAYT, f"{yol.name} {len(veri)} B")
            self.assertNotIn(b"Syntax error", veri, f"{yol.name} hata cizimi")
            ET.fromstring(veri)  # XML degilse ParseError


class DugumlerKodaTutar(unittest.TestCase):
    def test_her_dugum_dosya_satir_tasir_ve_kodda_durur(self):
        for h in HARFLER:
            dugumler, hatalar, baslik = M.dogrula_metin(_mmd(h), KOK)
            self.assertEqual(hatalar, [], f"akis_{h}: " + " | ".join(hatalar))
            self.assertGreaterEqual(len(dugumler), ASGARI_DUGUM, f"akis_{h} cok kucuk")
            tutan = sum(1 for d in dugumler if d.dogrulama is not None)
            self.assertEqual(tutan, len(dugumler), f"akis_{h}: {tutan}/{len(dugumler)}")
            self.assertIsNotNone(baslik, f"akis_{h}: 'koddan turetildi' basligi yok")

    def test_her_diyagram_karar_ve_fonksiyon_icerir(self):
        """Yalniz kutu zinciri degil: kosul metni alintili KARAR dugumleri de var."""
        for h in HARFLER:
            dugumler, _, _ = M.dogrula_metin(_mmd(h), KOK)
            turler = {d.tur for d in dugumler}
            self.assertIn("karar", turler, f"akis_{h}: karar dugumu yok")
            self.assertIn("fonksiyon", turler, f"akis_{h}: fonksiyon dugumu yok")

    def test_baslik_commit_depoda_var(self):
        """'koddan turetildi <commit>' gercek bir commit olmali."""
        import subprocess
        for h in HARFLER:
            m = re.match(r"%% koddan turetildi ([0-9a-f]{7,40}) (\d{4}-\d{2}-\d{2})", _mmd(h))
            self.assertIsNotNone(m, f"akis_{h}: baslik yok")
            q = subprocess.run(["git", "cat-file", "-e", m.group(1) + "^{commit}"],
                               cwd=KOK, capture_output=True)
            self.assertEqual(q.returncode, 0, f"akis_{h}: commit {m.group(1)} depoda yok")


class TabloBayatDegil(unittest.TestCase):
    def test_dugum_tablosu_mmd_ile_birebir(self):
        for h in HARFLER:
            dugumler, hatalar, baslik = M.dogrula_metin(_mmd(h), KOK)
            self.assertEqual(hatalar, [])
            beklenen = M.tablo_uret(h, dugumler, baslik)
            mevcut = (SEKILLER / f"akis_{h}_dugumler.md").read_text(encoding="utf-8")
            self.assertEqual(mevcut.replace("\r\n", "\n"), beklenen,
                             f"akis_{h}_dugumler.md bayat — "
                             "`python scripts/akis_diyagram_dogrula.py --tablo` kosun")


class SvgMmdIleUyumlu(unittest.TestCase):
    def test_svg_her_dugumun_dosya_satirini_icerir(self):
        for h in HARFLER:
            dugumler, _, _ = M.dogrula_metin(_mmd(h), KOK)
            kok = ET.fromstring((SEKILLER / f"akis_{h}.svg").read_bytes())
            metin = "".join(kok.itertext())
            eksik = [f"{d.dosya}:{d.satir}" for d in dugumler
                     if f"{d.dosya}:{d.satir}" not in metin]
            self.assertEqual(eksik, [], f"akis_{h}.svg .mmd'den bayat; SVG'de yok: {eksik[:5]}")


class PozitifKontrol(unittest.TestCase):
    """Dogrulayici yakalamiyorsa kapi degildir (D-354 sinifi)."""
    BASLIK = "%% koddan turetildi 0000000 2026-09-07\nflowchart TD\n"

    def test_yanlis_satir_yakalanir(self):
        metin = self.BASLIK + 'x1["def run_camera()<br/>codes/rpi_inference.py:10"]\n'
        _, hatalar, _ = M.dogrula_metin(metin, KOK)
        self.assertTrue(any("run_camera" in h for h in hatalar), hatalar)

    def test_dogru_satir_tutar(self):
        metin = self.BASLIK + 'x1["def run_camera()<br/>codes/rpi_inference.py:2298"]\n'
        dugumler, hatalar, _ = M.dogrula_metin(metin, KOK)
        self.assertEqual(hatalar, [])
        self.assertEqual(dugumler[0].dogrulama, "tam")

    def test_dosya_satirsiz_dugum_yakalanir(self):
        metin = self.BASLIK + 'x1["Cx0 yok sayilir"]\n'
        _, hatalar, _ = M.dogrula_metin(metin, KOK)
        self.assertTrue(any("dosya:satır" in h for h in hatalar), hatalar)

    def test_tirnaksiz_etiket_yakalanir(self):
        metin = self.BASLIK + "x1[Cx0 yok sayilir]\n"
        _, hatalar, _ = M.dogrula_metin(metin, KOK)
        self.assertTrue(any("tanınmayan satır" in h for h in hatalar), hatalar)

    def test_tanimsiz_kenar_id_yakalanir(self):
        metin = (self.BASLIK + 'x1["def run_camera()<br/>codes/rpi_inference.py:2298"]\n'
                 "x1 --> yok9\n")
        _, hatalar, _ = M.dogrula_metin(metin, KOK)
        self.assertTrue(any("yok9" in h for h in hatalar), hatalar)

    def test_kosul_metni_birebir_degilse_yakalanir(self):
        metin = self.BASLIK + 'x1{"if cap.isOpened():<br/>codes/rpi_inference.py:2316"}\n'
        _, hatalar, _ = M.dogrula_metin(metin, KOK)   # kodda `if not cap.isOpened():`
        self.assertTrue(any("YOK" in h for h in hatalar), hatalar)


if __name__ == "__main__":
    unittest.main()
