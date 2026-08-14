"""NEDEN: Letterbox icerik kutusu cekirdekte var olup cagri yerinde kaybolmamali."""

from __future__ import annotations

import ast
import importlib.util
import sys
import unittest
from pathlib import Path
from unittest import mock

import numpy as np


KOK = Path(__file__).resolve().parents[1]
for _dizin in (KOK / "codes", KOK / "scripts"):
    if str(_dizin) not in sys.path:
        sys.path.insert(0, str(_dizin))


def _modul_yukle(ad: str, goreli_yol: str):
    """Betigi main blogunu calistirmadan benzersiz adla ice aktar."""
    yol = KOK / goreli_yol
    spec = importlib.util.spec_from_file_location(ad, yol)
    if spec is None or spec.loader is None:
        raise ImportError(f"modul yuklenemedi: {yol}")
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def _rota_cagrisi(goreli_yol: str, ilk_arguman: str) -> ast.Call:
    """Ilk argumani adla verilen tek rota_bul cagrisini AST'den bul."""
    agac = ast.parse((KOK / goreli_yol).read_text(encoding="utf-8"))
    eslesen = []
    for dugum in ast.walk(agac):
        if not isinstance(dugum, ast.Call):
            continue
        if not isinstance(dugum.func, ast.Name) or dugum.func.id != "rota_bul":
            continue
        if (dugum.args and isinstance(dugum.args[0], ast.Name)
                and dugum.args[0].id == ilk_arguman):
            eslesen.append(dugum)
    if len(eslesen) != 1:
        raise AssertionError(
            f"{goreli_yol}: rota_bul({ilk_arguman}, ...) sayisi={len(eslesen)}")
    return eslesen[0]


def _icerik_degeri(cagri: ast.Call):
    """icerik keyword AST degerini veya yoksa None don."""
    return next((kw.value for kw in cagri.keywords if kw.arg == "icerik"), None)


class CostmapIcerikCagriYeriTests(unittest.TestCase):
    def test_letterbox_cagrilari_exact_icerik_adini_tasir(self):
        """Kaynak tuple yeniden hesaplanmadan dogrudan rota_bul'a gitmeli."""
        bagli = (
            ("scripts/jetson_fps.py", "maskeler"),
            ("jetson_paket/kod/jetson_fps.py", "maskeler"),
            ("scripts/saha_kuru_kosu.py", "maskeler"),
            ("scripts/v21_degerlendir_ve_paketle.py", "mk"),
        )
        for yol, ilk_arguman in bagli:
            with self.subTest(yol=yol):
                deger = _icerik_degeri(_rota_cagrisi(yol, ilk_arguman))
                self.assertIsInstance(deger, ast.Name)
                self.assertEqual("icerik", deger.id)

    def test_pad_siz_cagrilar_eski_tuval_kutusunu_tasimaz(self):
        """Fiziksel kirpik ve yerel mozaik eski koordinat kutusunu almamali."""
        pad_siz = (
            ("scripts/saha_kuru_kosu.py", "kirpik"),
            ("simulation/scripts/iha_haritala.py", "costmap_maskeleri"),
        )
        for yol, ilk_arguman in pad_siz:
            with self.subTest(yol=yol):
                cagri = _rota_cagrisi(yol, ilk_arguman)
                self.assertIsNone(_icerik_degeri(cagri))

    def test_jetson_fps_preprocess_kutusunu_aynen_tasir(self):
        modul = _modul_yukle("_t41_jetson_fps", "scripts/jetson_fps.py")
        tuval = np.zeros((8, 8, 3), np.uint8)
        icerik = (0, 2, 8, 4)
        maskeler = {0: np.ones((8, 8), np.uint8),
                    1: np.zeros((8, 8), np.uint8)}
        model = mock.Mock()
        rota = mock.Mock(return_value={"durum": "BELIRSIZ_COKLU", "yol_no": None})

        with (mock.patch.object(modul, "_preprocess",
                                return_value=(tuval, tuval, icerik)),
              mock.patch.object(modul, "get_masks", return_value=maskeler),
              mock.patch.object(modul, "_maskeleri_icerige_kirp",
                                return_value=maskeler),
              mock.patch.object(modul, "rota_bul", rota)):
            modul.tek_kare_isle(model, tuval, 8, 0.25, None)

        self.assertIs(icerik, rota.call_args.kwargs["icerik"])

    def test_v21_zinciri_preprocess_kutusunu_aynen_tasir(self):
        modul = _modul_yukle(
            "_t41_v21_degerlendir", "scripts/v21_degerlendir_ve_paketle.py")
        tuval = np.zeros((8, 8, 3), np.uint8)
        icerik = (0, 2, 8, 4)
        maskeler = {0: np.ones((8, 8), np.uint8),
                    1: np.zeros((8, 8), np.uint8)}
        model = mock.Mock()
        rota = mock.Mock(return_value={"durum": "BELIRSIZ_COKLU"})

        with (mock.patch.object(modul, "_preprocess",
                                return_value=(tuval, tuval, icerik)),
              mock.patch.object(modul, "get_masks", return_value=maskeler),
              mock.patch.object(modul, "_maskeleri_icerige_kirp",
                                return_value=maskeler),
              mock.patch.object(modul, "rota_bul", rota)):
            modul.zincir(model, tuval, 8, 0.25, None)

        self.assertIs(icerik, rota.call_args.kwargs["icerik"])

    def test_kuru_kosu_ana_maskeyi_baglar_kirpigi_baglamaz(self):
        modul = _modul_yukle(
            "_t41_saha_kuru_kosu", "scripts/saha_kuru_kosu.py")
        import costmap_path_finder

        icerik = (0, 2, 8, 4)
        maskeler = {0: np.ones((8, 8), np.uint8),
                    1: np.zeros((8, 8), np.uint8)}
        cagrilar = []

        def sahte_rota(girdi, *, mpp=None, icerik=None):
            cagrilar.append((girdi, icerik))
            durum = "BELIRSIZ_COKLU" if len(cagrilar) == 1 else "ACIK"
            return {"durum": durum, "yol_no": None}

        rapor = modul.Rapor()
        with mock.patch.object(costmap_path_finder, "rota_bul", sahte_rota):
            durum, _sonuc = modul.halka_rota(
                rapor, maskeler, icerik, modul.GECTI, mpp=0.05)

        self.assertEqual(modul.DUSTU, durum)
        self.assertEqual(2, len(cagrilar))
        self.assertIs(icerik, cagrilar[0][1])
        self.assertIsNone(cagrilar[1][1])
        self.assertTrue(rapor.satirlar[-1]["detay"]["icerik_aktarildi"])
        self.assertEqual("ACIK", rapor.satirlar[-1]["detay"]["kirpik_durum"])
        self.assertEqual(
            "rota uretilemedi: durum=BELIRSIZ_COKLU",
            rapor.satirlar[-1]["sebep"],
        )
        self.assertEqual(
            "yalniz_tanisal",
            rapor.satirlar[-1]["detay"]["kirpik_karsilastirma"],
        )


if __name__ == "__main__":
    unittest.main()
