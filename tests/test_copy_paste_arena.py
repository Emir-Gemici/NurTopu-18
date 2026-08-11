"""NEDEN: T40 arena kipi uc koridoru, pozitif kontrolu ve etiket kapsamasini
yer gercegiyle kilitler; agir YOLO modellerini birim testlere yuklemez.
"""

from __future__ import annotations

import random
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import numpy as np


KOK = Path(__file__).resolve().parents[1]
BETIKLER = KOK / "scripts"
KODLAR = KOK / "codes"
for yol in (str(BETIKLER), str(KODLAR), str(KOK)):
    if yol not in sys.path:
        sys.path.insert(0, yol)

import copy_paste_augmentation as cp  # noqa: E402
from karar_sozlesmesi import hedef_bant_yuksekligi, serit_no  # noqa: E402
from sinif_semasi import ENGEL  # noqa: E402


class ArenaGeometrisiTestleri(unittest.TestCase):
    """Kontrollu semantigin karar sonucunu ve fail-closed yonunu olcer."""

    def setUp(self):
        self.sekil = (500, 500)
        self.icerik = (0, 0, 500, 500)
        self.mpp = 0.1
        self.bos = np.zeros(self.sekil, dtype=np.uint8)

    def test_serit_haritasi_her_x_icin_tek_otoriteyi_kullanir(self):
        icerik = (20, 10, 300, 80)
        harita = cp.arena_serit_haritasi((100, 360), icerik)
        self.assertFalse(harita[:10].any())
        self.assertFalse(harita[90:].any())
        for x in range(icerik[0], icerik[0] + icerik[2]):
            self.assertEqual(serit_no(x, icerik[0], icerik[2]), int(harita[25, x]))

    def test_uc_acik_seridin_her_biri_dogru_yol_no_uretir(self):
        for acik in (1, 2, 3):
            with self.subTest(acik=acik):
                geometri = cp.arena_geometrisi_uret(
                    self.bos, random.Random(7), icerik=self.icerik,
                    mpp=self.mpp, acik_serit=acik)
                self.assertIsNotNone(geometri)
                sonuc = cp.arena_rotasi(
                    geometri.zemin, self.bos, self.bos, geometri.bariyer,
                    mpp=self.mpp, icerik=self.icerik)
                self.assertEqual("ACIK", sonuc["durum"])
                self.assertEqual(acik, sonuc["yol_no"])

    def test_acik_serit_de_kapaninca_karar_acik_kalmaz(self):
        for acik in (1, 2, 3):
            with self.subTest(acik=acik):
                geometri = cp.arena_geometrisi_uret(
                    self.bos, random.Random(9), icerik=self.icerik,
                    mpp=self.mpp, acik_serit=acik)
                sonuc = cp.arena_rotasi(
                    geometri.zemin, self.bos, self.bos,
                    np.maximum(geometri.bariyer, geometri.pozitif_bariyer),
                    mpp=self.mpp, icerik=self.icerik)
                self.assertNotEqual("ACIK", sonuc["durum"])

    def test_hedef_iki_metre_ve_acik_seridin_ust_bandindadir(self):
        geometri = cp.arena_geometrisi_uret(
            self.bos, random.Random(11), icerik=self.icerik,
            mpp=self.mpp, acik_serit=2)
        x0, y0, w, h = geometri.hedef_kutu
        self.assertEqual(round(cp.ARENA_HEDEF_KENAR_M / self.mpp), w)
        self.assertEqual(w, h)
        self.assertLess(y0 + h, hedef_bant_yuksekligi(self.icerik[3]) + 1)
        harita = cp.arena_serit_haritasi(self.sekil, self.icerik)
        self.assertTrue(np.all(harita[y0:y0 + h, x0:x0 + w] == 2))
        self.assertFalse(np.any(geometri.hedef & geometri.bariyer))

    def test_tam_engelli_sahne_ornek_uretmez(self):
        dolu = np.ones(self.sekil, dtype=np.uint8)
        self.assertIsNone(cp.arena_geometrisi_uret(
            dolu, random.Random(13), icerik=self.icerik, mpp=self.mpp))

    def test_ayni_tohum_ayni_maskeleri_ve_manifesti_uretir(self):
        bir = cp.arena_geometrisi_uret(
            self.bos, random.Random(17), icerik=self.icerik, mpp=self.mpp)
        iki = cp.arena_geometrisi_uret(
            self.bos, random.Random(17), icerik=self.icerik, mpp=self.mpp)
        self.assertEqual(bir.acik_serit, iki.acik_serit)
        self.assertEqual(bir.bariyerler, iki.bariyerler)
        self.assertTrue(np.array_equal(bir.zemin, iki.zemin))
        self.assertTrue(np.array_equal(bir.bariyer, iki.bariyer))
        self.assertTrue(np.array_equal(bir.hedef, iki.hedef))

    def test_yazilan_poligon_arac_piksellerini_kapsar(self):
        zemin = np.ones((120, 160), dtype=np.uint8)
        arac = np.zeros_like(zemin)
        arac[30:80, 40:110] = 1
        hedef = np.zeros_like(zemin)
        etiket = cp.arena_yolo_etiketi(zemin, arac, hedef, min_alan=1.0)
        yazilan = cp.yolo_sinif_maskesi(etiket, zemin.shape, ENGEL)
        kapsama = int(((arac > 0) & (yazilan > 0)).sum()) / int(arac.sum())
        self.assertGreaterEqual(kapsama, cp.ARENA_ARAC_KAPSAMA_ESIGI)

    def test_bir_piksel_yapistirma_bariyer_sayilmaz(self):
        """Gorunur tek piksel, planlanan dikdortgenin etiketi olamaz."""
        tuval = np.zeros((100, 100, 3), dtype=np.uint8)
        kimlik = np.zeros((100, 100), dtype=np.int32)
        plan = np.zeros((100, 100), dtype=np.uint8)
        plan[40:60, 20:80] = 1
        koridor = np.zeros((100, 100), dtype=np.uint8)
        koridor[:, 20:80] = 1
        aset = np.zeros((8, 8, 4), dtype=np.uint8)
        aset[:, :, 3] = 255

        def yalniz_bir_piksel(
            goruntu, kimlik_haritasi, _rgba, merkez_x, merkez_y, _olcek,
            _aci, _rng, *, kimlik_no, **_kwargs,
        ):
            goruntu[merkez_y, merkez_x] = (1, 2, 3)
            kimlik_haritasi[merkez_y, merkez_x] = kimlik_no
            return True

        with mock.patch.object(cp, "rgba_oku", return_value=aset):
            sonuc = cp.arena_molozunu_yapistir(
                tuval, kimlik, plan, [Path("sahte.png")],
                yalniz_bir_piksel, random.Random(19), 1,
                koridor=koridor, korunan=np.zeros_like(plan),
                min_poligon_alan=16.0,
            )
        # Islem atomik ve fail-closed olmali: basarisiz deneme tuvali de
        # kimlik haritasini da kismen kirletmemeli.
        self.assertIsNone(sonuc)
        self.assertFalse(tuval.any())
        self.assertFalse(kimlik.any())

    def test_rota_sonucu_ornek_uygunluk_filtresi_olamaz(self):
        """SUT karari, yanlislarini ATLANDI yaparak kabul kapisindan gizleyemez."""
        sekil = (100, 100)
        zemin = np.ones(sekil, dtype=np.uint8)
        bariyer = np.zeros(sekil, dtype=np.uint8)
        bariyer[40:50, :30] = 1
        bariyer[40:50, 70:] = 1
        pozitif = np.zeros(sekil, dtype=np.uint8)
        pozitif[40:50, 30:70] = 1
        hedef = np.zeros(sekil, dtype=np.uint8)
        hedef[5:15, 45:55] = 1
        geometri = cp.ArenaGeometrisi(
            zemin=zemin, bariyer=bariyer, pozitif_bariyer=pozitif,
            hedef=hedef, acik_serit=2, kapali_seritler=[1, 3],
            bariyerler=[{"serit": 1, "kutu": [0, 40, 30, 10]},
                        {"serit": 3, "kutu": [70, 40, 30, 10]}],
            icerik=(0, 0, 100, 100), mpp=0.2,
            hedef_kutu=(45, 5, 10, 10),
        )
        arac = np.zeros(sekil, dtype=np.uint8)
        arac[60:70, 45:55] = 1
        bgr = np.zeros((*sekil, 3), dtype=np.uint8)

        girdi = KOK / "tests" / "_arena_mock_girdi"
        cikti = KOK / "tests" / "_arena_mock_cikti"
        kaynak = girdi / "kare.jpg"
        args = SimpleNamespace(
            girdi=girdi, tohum=23, min_poligon_alan=1.0,
            val_oran=0.0, jpeg_kalite=95,
        )
        sol = np.zeros(sekil, dtype=np.uint8)
        sag = np.zeros(sekil, dtype=np.uint8)
        sol[40:50, :30] = 1
        sag[40:50, 70:] = 1
        bariyer_sonuclari = [
            cp.ArenaBariyerSonucu(sol, (0, 40, 30, 10), (0, 30, 30, 30), 1),
            cp.ArenaBariyerSonucu(sag, (70, 40, 30, 10), (70, 30, 30, 30), 1),
            cp.ArenaBariyerSonucu(
                pozitif, (30, 40, 40, 10), (30, 30, 40, 30), 1),
        ]
        with (
            mock.patch.object(cp, "arena_geometrisi_uret", return_value=geometri),
            mock.patch.object(
                cp, "arena_molozunu_yapistir", side_effect=bariyer_sonuclari),
            mock.patch.object(
                cp, "arena_rotasi",
                side_effect=AssertionError("ureteci karar koduna baglama"),
            ) as rota_mock,
            mock.patch.object(Path, "mkdir"),
            mock.patch.object(cp, "atomik_jpeg_yaz"),
            mock.patch.object(cp, "atomik_png_yaz"),
            mock.patch.object(cp, "atomik_bytes_yaz"),
        ):
            ozet = cp.arena_cesidi_uret(
                args, cikti, kaynak, bgr, self.bos[:100, :100], arac,
                np.zeros(sekil, dtype=np.uint8), [Path("enkaz.png")],
                mock.Mock(), 0,
            )
        self.assertEqual("YAZILDI", ozet.durum)
        rota_mock.assert_not_called()
        self.assertNotIn("rota_durum", ozet.arena)
        self.assertNotIn("pozitif_kontrol_durum", ozet.arena)

    def test_rastgele_kip_varsayilanlari_ve_tam_kare_etiketi_korunur(self):
        args = SimpleNamespace(arena=False, cikti=None, zemin_model=None)
        cp.kip_varsayilanlarini_uygula(args)
        self.assertEqual(KOK / "dataset" / "copy_paste_moloz", args.cikti)
        self.assertEqual("navitas_seg_v20_best.pt", args.zemin_model.name)
        etiket = cp.yolo_etiketi(self.bos, self.bos, min_alan=1.0)
        self.assertTrue(etiket.startswith("0 0.000000 0.000000 1.000000"))

    def test_arena_kipi_v21_ve_kompozit_ciktiyi_secer(self):
        args = SimpleNamespace(arena=True, cikti=None, zemin_model=None)
        cp.kip_varsayilanlarini_uygula(args)
        self.assertEqual(KOK / "data" / "arena_kompozit", args.cikti)
        self.assertEqual("navitas_seg_v21_best.pt", args.zemin_model.name)


if __name__ == "__main__":
    unittest.main()
