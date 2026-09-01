"""T150 (D-386) — HB HEDEFLEMESI URETIME BAGLI ve ZINCIR URETIMI YANSITIYOR.

Korunanlar:
  1. Uretimin UC cagri yeri de analyze_path'e `goruntu=sq` gecirir —
     baglama sessizce sokulemez (D-351 sinifi: zincir/uretim ayrismasi).
  2. analyze_path'in ic HB cagrisi OLCEK+SEKIL ciftiyle kosar (mpp varsa
     sekil esigi sozlesmeden acilir; ciplak sabit yok, madde 16).
  3. Kabul zinciri (65 -> 61) uretim kipinde kosar (--hb-hedefli); bayrak
     61'de gercekten goruntu'ya baglidir.
  4. DAVRANIS: goruntu verilip HB gorunmeyen karede HEDEF_YOK cekimserligi
     (sonda 259/260 olctu; buradaki test mekanik kaniti kilitler).

Mutasyonlar KOD uzerinde, uygulanma kontrollu (D-370/D-375).
"""
import sys
import unittest
from pathlib import Path

import numpy as np

KOK = Path(__file__).resolve().parents[1]
for _y in (KOK / "codes",):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

RPI = (KOK / "codes" / "rpi_inference.py").read_text(encoding="utf-8")
B61 = (KOK / "scripts" / "olcum" / "61_rota_moloza_basma.py").read_text(
    encoding="utf-8")
B65 = (KOK / "scripts" / "olcum" / "65_kabul_denetcisi.py").read_text(
    encoding="utf-8")


def _kodu(metin):
    return "\n".join(s for s in metin.splitlines()
                     if not s.lstrip().startswith("#"))


class BaglamaKilidi(unittest.TestCase):
    def test_UC_URETIM_CAGRISI_DA_GORUNTU_GECIRIYOR(self):
        kod = _kodu(RPI)
        self.assertEqual(
            kod.count("goruntu=sq)"), 3,
            "uretim cagrilarinin ucu de goruntu=sq gecirmeli "
            "(run_image / run_video / run_camera) — biri koparsa o yol "
            "HB'siz kalir ve zincirden ayrisir")

    def test_IC_HB_CAGRISI_OLCEK_SEKIL_CIFTI(self):
        kod = _kodu(RPI)
        self.assertIn("sekil_esigi=HB_SEKIL_ESIGI if mpp is not None else None",
                      kod, "ic HB cagrisi sekil kapisiz — kirmizi otomobil "
                           "olcek bandindan gecebilir (D-351)")

    def test_ZINCIR_URETIM_KIPINDE(self):
        self.assertIn('"--hb-hedefli"', _kodu(B65),
                      "65, 61'i HB'siz cagiriyor — zincir uretimi yansitmaz")
        kod61 = _kodu(B61)
        self.assertIn("goruntu=sq if args.hb_hedefli else None", kod61,
                      "61'in bayragi goruntu'ya bagli degil — bos bayrak")

    def test_DAVRANIS_hb_gorunmeyen_karede_HEDEF_YOK(self):
        """Sentetik: gecilebilir dikey serit VAR, kirmizi ped YOK ->
        goruntu verilince HEDEF_YOK; goruntu verilmeyince rota VAR."""
        from rpi_inference import analyze_path
        from karar_sozlesmesi import HEDEF_YOK_SEBEBI
        N = 200
        zemin = np.zeros((N, N), np.uint8)
        zemin[:, 80:120] = 1                       # ust-alt bagli koridor
        gri = np.full((N, N, 3), (128, 128, 128), np.uint8)
        yol, _, _, red = analyze_path(zemin, mpp=0.10, return_reason=True)
        self.assertIsNotNone(yol, "on kosul: goruntu'suz rota uretilmeli")
        yol2, _, _, red2 = analyze_path(zemin, mpp=0.10, return_reason=True,
                                        goruntu=gri)
        self.assertIsNone(yol2, "ped gorunmezken rota uretildi — "
                                "fail-closed bozuldu")
        self.assertEqual((red2[0] if isinstance(red2, tuple) else red2),
                         HEDEF_YOK_SEBEBI)


class MutasyonKontrolu(unittest.TestCase):
    def test_M1_bir_cagridan_goruntu_dusurulurse_yakalanir(self):
        kod = _kodu(RPI)
        mutant = kod.replace("goruntu=sq)", ")", 1)
        self.assertNotEqual(kod, mutant, "MUTASYON UYGULANMADI (D-370)")
        self.assertLess(mutant.count("goruntu=sq)"), 3,
                        "cagri dusuruldu ve sayim dusmedi")

    def test_M2_zincir_bayragi_dusurulurse_yakalanir(self):
        kod = _kodu(B65)
        mutant = kod.replace('"--hb-hedefli"', '"--x"', 1)
        self.assertNotEqual(kod, mutant, "MUTASYON UYGULANMADI (D-370)")
        self.assertNotIn('"--hb-hedefli"', mutant,
                         "bayrak dusuruldu ve gorunmuyor — zincir sessizce "
                         "HB'siz olcume doner")


if __name__ == "__main__":
    unittest.main()
