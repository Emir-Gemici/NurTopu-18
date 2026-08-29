"""B3 yaw/kadraj olcumunun uretim zinciri ve etiket esligi nobetcisi."""
from __future__ import annotations

import ast
import contextlib
import importlib.util
import io
import types
import unittest
from pathlib import Path
from unittest import mock

import cv2
import numpy as np


KOK = Path(__file__).resolve().parents[1]
BETIK = KOK / "scripts" / "olcum" / "162_yaw_kadraj_zarfi.py"


def _modulu_yukle():
    spec = importlib.util.spec_from_file_location("b3_yaw_kadraj_zarfi", BETIK)
    modul = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(modul)
    return modul


def _cagri_adi(cagri: ast.Call) -> str:
    if isinstance(cagri.func, ast.Name):
        return cagri.func.id
    if isinstance(cagri.func, ast.Attribute):
        if isinstance(cagri.func.value, ast.Name):
            return f"{cagri.func.value.id}.{cagri.func.attr}"
        return cagri.func.attr
    return ""


def _mutant_modul(kaynak: str):
    modul = types.ModuleType("b3_yaw_kadraj_zarfi_mutant")
    modul.__file__ = str(BETIK)
    modul.__package__ = None
    exec(compile(kaynak, str(BETIK), "exec"), modul.__dict__)
    return modul


class B3YawKadrajZarfiTesti(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.kaynak = BETIK.read_text(encoding="utf-8")
        cls.agac = ast.parse(cls.kaynak, filename=str(BETIK))
        cls.modul = _modulu_yukle()

    def test_betik_ayristirilir_ve_uretim_cagri_sirasi_birebirdir(self):
        fonksiyon = next(
            n for n in self.agac.body
            if isinstance(n, ast.FunctionDef) and n.name == "uretim_karari"
        )
        cagrilar = sorted(
            ((n.lineno, _cagri_adi(n)) for n in ast.walk(fonksiyon)
             if isinstance(n, ast.Call)),
            key=lambda x: x[0],
        )
        adlar = [ad for _satir, ad in cagrilar]
        zincir = ["_preprocess", "model.predict", "get_masks",
                  "_maskeleri_icerige_kirp", "analyze_path"]
        konumlar = [adlar.index(ad) for ad in zincir]
        self.assertEqual(konumlar, sorted(konumlar), cagrilar)

        get_masks_cagrisi = next(
            n for n in ast.walk(fonksiyon)
            if isinstance(n, ast.Call) and _cagri_adi(n) == "get_masks"
        )
        self.assertIsInstance(get_masks_cagrisi.args[0], ast.Name)
        self.assertEqual("results", get_masks_cagrisi.args[0].id,
                         "get_masks'e LISTE yerine results[0] verilmis")

    def _etiket_hizasi_iddiasi(self, modul):
        h, w = 60, 80
        maske = np.zeros((h, w), dtype=np.uint8)
        maske[20:35, 30:45] = 1
        goruntu = np.zeros((h, w, 3), dtype=np.uint8)
        goruntu[maske > 0] = (255, 255, 255)

        donen_goruntu, donen_etiket, matris = modul.goruntu_ve_etiketi_donustur(
            goruntu, {0: maske}, yaw_derece=0, x_pct=10, y_pct=-5,
        )
        beklenen = cv2.warpAffine(
            maske, matris, (w, h), flags=cv2.INTER_NEAREST,
            borderMode=cv2.BORDER_CONSTANT, borderValue=0,
        )
        self.assertTrue(np.array_equal(beklenen, donen_etiket[0]),
                        "etiket goruntuyle ayni affine matristen gecmedi")

        goruntu_izi = (cv2.cvtColor(donen_goruntu, cv2.COLOR_BGR2GRAY) > 127)
        self.assertTrue(np.array_equal(goruntu_izi.astype(np.uint8), beklenen),
                        "sentetik isaretin goruntu ve etiket konumu ayrildi")

    def test_goruntu_ve_etiket_ayni_affine_donusumden_gecer(self):
        self._etiket_hizasi_iddiasi(self.modul)

    def test_fov_disi_yansitilmaz_sabit_dolguyla_kapanir(self):
        h, w = 20, 20
        goruntu = np.full((h, w, 3), 255, dtype=np.uint8)
        etiket = {0: np.ones((h, w), dtype=np.uint8)}

        donen_goruntu, donen_etiket, _matris = (
            self.modul.goruntu_ve_etiketi_donustur(
                goruntu, etiket, yaw_derece=0, x_pct=20, y_pct=0,
            )
        )

        self.assertTrue(np.all(
            donen_goruntu[:, -1] == self.modul.GORUNTU_DOLGU_DEGERI
        ), "FOV disi piksel yansitilarak sahte goruntu uretilmis")
        self.assertTrue(np.all(donen_etiket[0][:, -1] == 0),
                        "FOV disinda fail-closed etiket dolgusu kullanilmamis")

    def test_MUTASYON_etiket_donusumu_kaldirilirsa_iddia_duser(self):
        hedef = (
            "donusmus_etiketler = _maskeleri_affine_donustur(etiketler, "
            "matris, boyut)"
        )
        mutant_satir = (
            "donusmus_etiketler = {int(k): np.asarray(v).copy() for k, v in "
            "etiketler.items()}"
        )
        self.assertEqual(1, self.kaynak.count(hedef),
                         "mutasyon gercek kod satirini tekil bulamadi")
        mutant = _mutant_modul(self.kaynak.replace(hedef, mutant_satir, 1))
        with self.assertRaises(AssertionError):
            self._etiket_hizasi_iddiasi(mutant)

    def test_N_sifir_OLCULEMEDI_ve_sifir_olmayan_cikis(self):
        ozet = self.modul.hucresi_ozetle([], beklenen_n=0)
        self.assertEqual("OLCULEMEDI", ozet["durum"])
        self.assertFalse(ozet["gecti"])
        self.assertIsNone(ozet["rota_orani"])
        self.assertIsNone(ozet["ayni_serit_orani"])

        with mock.patch.object(self.modul, "raporu_yaz") as yaz, \
             contextlib.redirect_stdout(io.StringIO()) as stdout:
            kod = self.modul.main(["--n", "0"])
        self.assertNotEqual(0, kod)
        self.assertIn("OLCULEMEDI", stdout.getvalue())
        rapor = yaz.call_args.args[0]
        self.assertEqual("OLCULEMEDI", rapor["durum"])

    def test_izgara_on_kayitla_tam_eslesir(self):
        self.assertEqual(tuple(range(-30, 31, 5)), self.modul.YAW_DEGERLERI)
        self.assertEqual(17, len(self.modul.KADRAJ_DURUMLARI))
        self.assertEqual(12, self.modul.ON_KAYIT_N)
        self.assertEqual(40, self.modul.AZAMI_N)
        self.assertEqual(0.90, self.modul.ROTA_KABUL_ORANI)
        self.assertEqual(0.95, self.modul.SERIT_KABUL_ORANI)

    def test_on_kayit_hashi_git_satir_sonu_donusumunde_degismez(self):
        lf = self.modul.ON_KAYIT_YOLU.read_bytes().replace(b"\r\n", b"\n")
        crlf = lf.replace(b"\n", b"\r\n")
        sahte_yol = mock.Mock()
        sahte_yol.is_file.return_value = True
        sahte_yol.read_bytes.return_value = crlf
        self.assertEqual(self.modul.ON_KAYIT_SHA256,
                         self.modul.on_kayit_dogrula(sahte_yol))

    def test_kirilma_iyi_yonla_ortalanmaz_en_kotu_yon_kazanir(self):
        hucreler = []
        for yaw in self.modul.YAW_DEGERLERI:
            for kadraj in self.modul.KADRAJ_DURUMLARI:
                rota_orani = 1.0
                if yaw == 5 and kadraj["ad"] == "merkez":
                    rota_orani = 0.83
                hucreler.append({
                    "yaw_derece": yaw,
                    "kadraj": kadraj,
                    "ozet": {
                        "durum": "GECTI",
                        "rota_orani": rota_orani,
                        "ayni_serit_orani": 1.0,
                    },
                })

        kirilmalar = self.modul.kirilmalari_bul(hucreler)
        self.assertEqual(5, kirilmalar["yaw"]["ilk_kirilma_derece"])
        grup = next(g for g in kirilmalar["yaw"]["gruplar"]
                    if g["mutlak_yaw"] == 5)
        self.assertEqual("EN_KOTU_YON", grup["birlesim"])
        self.assertAlmostEqual(0.83, grup["rota_orani"])


if __name__ == "__main__":
    unittest.main()
