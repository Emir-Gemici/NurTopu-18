"""T160 KAPISI (ON_KAYIT §21 · D-298 §5b): saha kuru kosusunun `rota` halkasi
URETIM karar yolunu (`analyze_path`) kosuyor mu?

NEDEN: T151 karari (CONTRACTS §11.2-EK) uretim yolunu `analyze_path` ilan etti;
Jetson `run_camera` onu kosuyor. Kuru kosu ise `costmap_path_finder.rota_bul`
cagiriyordu — yani zincirin 7. halkasi SAHANIN KOSMAYACAGI yolu doguluyordu.
D-297 §5 bunu "olculemedi" diye kaydetmisti.

BOS KAPI YASAGI (TEST_SPECS §4.1): "analyze_path cagriliyor" demek yetmez.
Mutasyon UC yonlu kosulur:
  1. uretim yolu ROTA dondururse halka GECTI olmali,
  2. uretim yolu RET dondururse halka DUSTU olmali,
  3. TANISAL yol (`rota_bul`) tam TERSINI soylerken bile hukum DEGISMEMELI —
     hukmun gercekten uretim yolundan geldiginin tek kaniti budur.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

KOK = Path(__file__).resolve().parents[1]
for _yol in (KOK / "scripts", KOK / "codes", KOK / "comms"):
    if str(_yol) not in sys.path:
        sys.path.insert(0, str(_yol))

import rpi_inference                                   # noqa: E402
import saha_kuru_kosu as sk                            # noqa: E402


ICERIK = (0, 0, 64, 64)


def _maskeler():
    trav = np.zeros((64, 64), np.uint8)
    trav[:, 24:40] = 1
    return {0: trav, 1: np.zeros((64, 64), np.uint8)}


def _sahte_rota_bul(donus):
    """GERCEK fonksiyon nesnesi: halka `__code__.co_varnames` okuyor (Mock olmaz)."""
    def rota_bul(maskeler, mpp=None, icerik=None):
        return donus
    return rota_bul


def _halkayi_kos(analyze_donus, rota_bul_donus):
    """`halka_rota`yi sahte iki yolla kosar, (durum, satir) doner."""
    rapor = sk.Rapor()
    sahte_rb = _sahte_rota_bul(rota_bul_donus)
    with mock.patch.object(rpi_inference, "analyze_path",
                           return_value=analyze_donus):
        with mock.patch("costmap_path_finder.rota_bul", sahte_rb):
            durum, _sonuc = sk.halka_rota(rapor, _maskeler(), ICERIK,
                                          sk.GECTI, mpp=0.01)
    satir = next(s for s in rapor.satirlar if s["halka"] == "rota")
    return durum, satir


ROTA_VAR = (2, 0.91, [(0.0, 0.0), (0.0, 2.0)], None)
ROTA_YOK = (None, 0.0, [], ("GORUS_HATTI_KOPUK", "sahte ret"))
RB_ACIK = {"durum": "ACIK", "yol_no": 2}
RB_KAPALI = {"durum": "BELIRSIZ_TEK_KAPI", "yol_no": None}


class UretimYoluHalkasi(unittest.TestCase):

    def test_hukum_uretim_yolundan_gelir(self):
        """Uretim ROTA derse halka GECTI, kaynak satiri uretim yolunu gosterir."""
        durum, satir = _halkayi_kos(ROTA_VAR, RB_ACIK)
        self.assertEqual(durum, sk.GECTI, satir)
        self.assertEqual(satir["detay"]["karar_yolu"], "analyze_path")
        self.assertEqual(satir["dosya"], sk.URETIM_KARAR_YOLU)
        self.assertIn("rpi_inference", satir["dosya"])
        self.assertEqual(satir["detay"]["yol_no"], 2)

    def test_uretim_reddi_halkayi_dusurur(self):
        durum, satir = _halkayi_kos(ROTA_YOK, RB_KAPALI)
        self.assertEqual(durum, sk.DUSTU, satir)
        self.assertEqual(satir["detay"]["durum"], "GORUS_HATTI_KOPUK")
        self.assertIsNone(satir["detay"]["yol_no"])

    def test_tanisal_yol_hukmu_CEVIREMEZ(self):
        """🔴 Bos kapi kaniti: `rota_bul` ACIK dese bile uretim RET ise DUSTU."""
        durum, satir = _halkayi_kos(ROTA_YOK, RB_ACIK)
        self.assertEqual(durum, sk.DUSTU,
                         "tanisal yol hukmu cevirdi — halka hâlâ rota_bul'a bagli")
        self.assertTrue(satir["detay"]["tanisal_rota_bul"]["iki_yol_ayristi"])

    def test_tanisal_yol_KAPALI_iken_uretim_ROTA_gecirir(self):
        """Ters yon: `rota_bul` reddederken uretim rota bulursa halka GECTI."""
        durum, satir = _halkayi_kos(ROTA_VAR, RB_KAPALI)
        self.assertEqual(durum, sk.GECTI,
                         "uretim rota buldu ama halka tanisal rede takildi")
        self.assertTrue(satir["detay"]["tanisal_rota_bul"]["iki_yol_ayristi"])

    def test_tanisal_kayit_SILINMEDI(self):
        """`rota_bul` sonucu hukum disi ama kayittan DUSURULMEZ (T79/D-58)."""
        _durum, satir = _halkayi_kos(ROTA_VAR, RB_ACIK)
        tanisal = satir["detay"]["tanisal_rota_bul"]
        self.assertEqual(tanisal["durum"], "ACIK")
        self.assertTrue(satir["detay"]["rota_bul_cagrildi"])

    def test_kaynak_gercekten_uretim_yolunu_cagiriyor(self):
        """Sahte donus degil, GERCEK `analyze_path` cagriliyor mu — sayacla."""
        rapor = sk.Rapor()
        with mock.patch.object(rpi_inference, "analyze_path",
                               wraps=rpi_inference.analyze_path) as sahte:
            sk.halka_rota(rapor, _maskeler(), ICERIK, sk.GECTI, mpp=0.01)
        self.assertEqual(sahte.call_count, 1, "analyze_path cagrilmadi")
        _a, kw = sahte.call_args
        self.assertEqual(kw["icerik"], ICERIK)
        self.assertTrue(kw["return_reason"])
        self.assertEqual(kw["mpp"], 0.01)


class SurumKilidi(unittest.TestCase):
    """Kaynak satiri ciplak yazilmasin; `run_camera` ile hizali kalsin."""

    def test_run_camera_hâlâ_analyze_path_kosuyor(self):
        govde = (KOK / "codes" / "rpi_inference.py").read_text(encoding="utf-8")
        bas = govde.index("def run_camera(")
        self.assertIn("analyze_path(", govde[bas:],
                      "run_camera artik analyze_path kosmuyor — T160 hizasi bozuldu")

    def test_halka_rota_ciplak_dosya_satiri_yazmiyor(self):
        govde = (KOK / "scripts" / "saha_kuru_kosu.py").read_text(encoding="utf-8")
        bas = govde.index("def halka_rota(")
        son = govde.index("def halka_aktarim(")
        self.assertNotIn('"codes/costmap_path_finder.py:729"', govde[bas:son],
                         "halka hâlâ tanisal yolu kaynak gosteriyor")


if __name__ == "__main__":
    unittest.main()
