"""KAPI: UC DURUMLU maskede "ETIKETSIZ" egitimde SERBEST ALAN OLMAMALI.

🔴 NEDEN VAR (amele B buldu, F4 · D-279 §4): eski cikti bicimi `{0,255}` idi.
Sartnamenin urettigi "ETIKETSIZ" hukmu diske **0** yaziliyordu ve YOLO'ya
cevrilirken 0 = sinif 0 = SURULEBILIR oluyordu. Amele B'nin cumlesi:

    "Her belirsizlik guvensiz yone dusuyor."

Bu, projenin iki cekirdek kuralinin TERSIDIR:
  · anayasa madde 15 — serbest alani BUYUTEN hicbir islem eklenmez
  · D-210          — bilinmeyen ZEMIN ILAN EDILMEZ

Yeni bicim (kullanici karari 2026-08-25):
    0 = ETIKETSIZ  -> HICBIR poligon    (fail-safe)
    1 = SINIF 0    -> class 0 poligonu
    2 = SINIF 1    -> class 1 poligonu

Bu kapi, cevirimin ETIKETSIZ bolgeler icin HICBIR SATIR uretmedigini
CALISTIRARAK dogrular. Mutasyon testi asagida: 0'i sinif 0 sayan (eski, bozuk)
davranis bu kapiyi DUSURUR.
"""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import numpy as np

KOK = Path(__file__).resolve().parent.parent
_yol = KOK / "scripts" / "olcum" / "132_uc_durumlu_maske.py"
_spec = importlib.util.spec_from_file_location("uc_durumlu", _yol)
UC = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(UC)


def _sahne() -> np.ndarray:
    """Uc bolgeli sentetik maske: solda ETIKETSIZ, ortada sinif 0, sagda sinif 1."""
    m = np.zeros((200, 300), np.uint8)          # sol ucte 0 = ETIKETSIZ
    m[20:180, 110:190] = UC.SINIF0              # orta: surulebilir
    m[20:180, 210:290] = UC.SINIF1              # sag: gecilemez
    return m


class UcDurumluTests(unittest.TestCase):

    def test_bicim_sabitleri_sozlesmeye_uygun(self):
        self.assertEqual((0, 1, 2), (UC.ETIKETSIZ, UC.SINIF0, UC.SINIF1))
        self.assertEqual({0, 1, 2}, UC.GECERLI)

    def test_her_iki_sinif_icin_poligon_uretiliyor(self):
        satirlar = UC.maske_to_yolo(_sahne())
        sinif = sorted({s.split()[0] for s in satirlar})
        self.assertEqual(["0", "1"], sinif,
                         f"iki sinif da uretilmeli, uretilen: {sinif}")

    def test_ETIKETSIZ_bolge_HICBIR_poligon_URETMEZ(self):
        """🔴 ASIL KAPI: sol uctaki ETIKETSIZ serit hicbir satirda gorunmemeli."""
        m = _sahne()
        satirlar = UC.maske_to_yolo(m)
        h, w = m.shape
        for s in satirlar:
            parca = s.split()
            xs = [float(v) for v in parca[1::2]]
            # ETIKETSIZ bolge x < 110/300 = 0,367; hicbir poligon oraya girmemeli
            self.assertGreater(min(xs) * w, 100.0,
                               f"poligon ETIKETSIZ bolgeye tasti: {s[:70]}")

    def test_TAMAMEN_ETIKETSIZ_maske_BOS_etiket_uretir(self):
        """Hicbir sey cizilmemis kare -> hicbir anotasyon. 'Her yer zemin' DEGIL."""
        bos = np.zeros((200, 300), np.uint8)
        self.assertEqual([], UC.maske_to_yolo(bos))

    def test_MUTASYON_0_sinif0_sayilirsa_kapi_DUSER(self):
        """POZITIF KONTROL: eski (bozuk) davranisi taklit et — yakalanmali.

        Eski binary semada 0 sinif 0 demekti. Onu simule edip ayni iddiayi
        kurunca kapi DUSMELI; dusmezse bu test hicbir sey olcmuyor demektir.
        """
        m = _sahne()
        sahte = np.where(m == UC.ETIKETSIZ, UC.SINIF0, m).astype(np.uint8)
        satirlar = UC.maske_to_yolo(sahte)
        h, w = m.shape
        tasan = [s for s in satirlar
                 if min(float(v) for v in s.split()[1::2]) * w <= 100.0]
        self.assertTrue(tasan,
                        "MUTASYON YAKALANMADI: 0 sinif 0 sayildigi halde "
                        "ETIKETSIZ bolgede poligon olusmadi — kapi bos")


if __name__ == "__main__":
    unittest.main(verbosity=2)
