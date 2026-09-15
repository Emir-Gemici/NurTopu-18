#!/usr/bin/env python3
"""iha_haritala model rotası, fail-closed yedek ve kanıt günlüğü testleri."""

import contextlib
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import numpy as np


SIM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SIM / "scripts"))

import iha_haritala


def _level_dir(tmp):
    level_dir = Path(tmp)
    (level_dir / "kareler").mkdir()
    (level_dir / "poses.csv").write_text("0,0,0,0,30,1.5708\n", encoding="utf-8")
    return level_dir


def _plan(durum="BELIRSIZ_TEK_KAPI", *, yol_no=None, waypoints=None):
    return {
        "durum": durum,
        "sebep": "Yalniz bir kapi tespit edildi — 3 guzergah ayirt edilemedi.",
        "yol_no": yol_no,
        "guven": 0.91 if durum == "ACIK" else 0.0,
        "waypoints_px": list(waypoints or []),
        "darbogaz_m": 2.4 if durum == "ACIK" else None,
        "ihlaller": [] if durum == "ACIK" else [{"tur": "tani"}],
        "adaylar": [{"etiket": 2}],
        "serbest": np.ones((8, 8), dtype=np.uint8),
    }


def _tohumlar(sekil=(8, 8)):
    bir = np.ones(sekil, dtype=np.uint8)
    return {
        "kb_ham": bir.copy(),
        "hb_ham": bir.copy(),
        "kb_tohum": bir.copy(),
        "hb_tohum": bir.copy(),
        "gecilebilir": bir.copy(),
        "serbest": bir.copy(),
    }


def _oy(sekil=(8, 8), *, gozlem=20, engel_kutusu=None, kare_sayisi=1,
        cikarim_sn=0.5):
    """Kare başı oylamanın çıktısını taklit et: her hücre bol gözlemli ve zemin.

    `engel_kutusu` verilirse o dilimdeki OYLARIN TAMAMI engel olur.
    """
    gozlem_d = np.full(sekil, gozlem, dtype=np.int32)
    zemin_oy = np.full(sekil, gozlem, dtype=np.int32)
    engel_oy = np.zeros(sekil, dtype=np.int32)
    if engel_kutusu is not None:
        y0, y1, x0, x1 = engel_kutusu
        zemin_oy[y0:y1, x0:x1] = 0
        engel_oy[y0:y1, x0:x1] = gozlem
    return {"zemin_oy": zemin_oy, "engel_oy": engel_oy, "gozlem": gozlem_d,
            "cikarim_sn": cikarim_sn, "kare_sayisi": kare_sayisi}


def _run_haritala(level_dir, plan, *, coord_route=None, coord_road=None,
                   yedek_izin=False, model=None, model_yolu=None):
    blank = np.zeros((8, 8, 3), dtype=np.uint8)
    stream = io.StringIO()
    rota_mock = mock.Mock(return_value=plan)
    with mock.patch.object(iha_haritala, "oy_haritasi_kur",
                           return_value=(blank, 1, _oy())), \
         mock.patch.object(iha_haritala, "_arac_maskesi",
                           return_value=np.zeros((8, 8), dtype=np.uint8)), \
         mock.patch.object(iha_haritala, "_tohumlari_c_uzayinda_hazirla",
                           return_value=_tohumlar()), \
         mock.patch.object(iha_haritala, "rota_bul", rota_mock), \
         mock.patch.object(iha_haritala, "_overlay", return_value=blank), \
         contextlib.redirect_stdout(stream):
        det = iha_haritala.haritala(
            level_dir, model=model, htab_cx=0.0, htab_cy=0.0,
            kb_xy=(0.0, 0.0), hb_xy=(0.1, 0.1),
            coord_route=coord_route, coord_road=coord_road,
            yedek_izin=yedek_izin, model_yolu=model_yolu)
    return det, stream.getvalue(), rota_mock


class RotaTaniTest(unittest.TestCase):
    def test_closed_costmap_default_removes_route_and_preserves_diagnosis(self):
        plan = _plan()
        coord_route = [(-1.0, -2.0), (1.5, 0.0), (3.0, 4.0)]
        with tempfile.TemporaryDirectory() as tmp:
            level_dir = _level_dir(tmp)
            (level_dir / "route.txt").write_text("bayat\n", encoding="utf-8")
            (level_dir / "rota.json").write_text("{}", encoding="utf-8")
            det, log, _ = _run_haritala(
                level_dir, plan, coord_route=coord_route, coord_road=2)
            single = json.loads((level_dir / "detection.json").read_text(encoding="utf-8"))
            harita = json.loads((level_dir / "iha_harita.json").read_text(encoding="utf-8"))

            self.assertFalse((level_dir / "route.txt").exists())
            self.assertFalse((level_dir / "rota.json").exists())

        for kayit in (det, single):
            self.assertEqual(kayit["rota_durum"], "ROTA_YOK")
            self.assertEqual(kayit["costmap_durum"], "BELIRSIZ_TEK_KAPI")
            self.assertEqual(kayit["costmap_sebep"], plan["sebep"])
            self.assertEqual(kayit["costmap_ihlalleri"], [{"tur": "tani"}])
            self.assertEqual(kayit["n_kapi"], 1)
        self.assertEqual(harita["kaynak"], "yok")
        self.assertIn("güvenli durur", log)

    def test_coordinate_fallback_is_opt_in_and_keeps_labels(self):
        plan = _plan()
        coord_route = [(-1.0, -2.0), (1.5, 0.0), (3.0, 4.0)]
        with tempfile.TemporaryDirectory() as tmp:
            level_dir = _level_dir(tmp)
            det, log, _ = _run_haritala(
                level_dir, plan, coord_route=coord_route, coord_road=2,
                yedek_izin=True)
            rota_json = json.loads((level_dir / "rota.json").read_text(encoding="utf-8"))
            harita = json.loads((level_dir / "iha_harita.json").read_text(encoding="utf-8"))

            self.assertTrue((level_dir / "route.txt").is_file())

        self.assertEqual(det["rota_durum"], "KOORDINAT_YEDEK")
        self.assertEqual(det["rota_kaynak"], "iha_koordinat_yedegi")
        self.assertEqual(det["costmap_durum"], "BELIRSIZ_TEK_KAPI")
        self.assertEqual(rota_json["kaynak"], "iha_koordinat_yedegi")
        self.assertEqual(harita["kaynak"], "iha_koordinat_yedegi")
        self.assertIn("İHA KOORDİNAT ROTASI", log)

    def test_open_costmap_publishes_model_route_without_fallback(self):
        plan = _plan("ACIK", yol_no=1, waypoints=[(4, 4), (4, 3)])
        fallback_route = [(-9.0, -9.0), (9.0, 9.0)]
        with tempfile.TemporaryDirectory() as tmp:
            level_dir = _level_dir(tmp)
            det, log, _ = _run_haritala(
                level_dir, plan, coord_route=fallback_route, coord_road=3,
                yedek_izin=True)
            single = json.loads((level_dir / "detection.json").read_text(encoding="utf-8"))
            harita = json.loads((level_dir / "iha_harita.json").read_text(encoding="utf-8"))
            route_txt = (level_dir / "route.txt").read_text(encoding="utf-8")

        self.assertEqual(det["rota_durum"], "ACIK")
        self.assertEqual(single["costmap_durum"], "ACIK")
        self.assertNotIn("rota_kaynak", single)
        self.assertNotIn("KOORDİNAT ROTASI", log)
        self.assertNotIn("-9.00 -9.00", route_txt)
        self.assertEqual(det["road"], 1)
        self.assertEqual(harita["kaynak"], "model_costmap")

    def test_kb_seed_without_cspace_intersection_cannot_publish_route(self):
        boyut = 64
        blank = np.zeros((boyut, boyut, 3), dtype=np.uint8)
        trav = np.ones((boyut, boyut), dtype=np.uint8)
        oy = _oy((boyut, boyut), engel_kutusu=(24, 41, 24, 41))
        plan = _plan("ACIK", yol_no=2, waypoints=[(32, 32), (32, 20)])
        rota_mock = mock.Mock(return_value=plan)

        with tempfile.TemporaryDirectory() as tmp:
            level_dir = _level_dir(tmp)
            (level_dir / "route.txt").write_text("bayat\n", encoding="utf-8")
            with mock.patch.object(iha_haritala, "MOZ_PX", boyut), \
                 mock.patch.object(iha_haritala, "MPP", iha_haritala.MOZ_M / boyut), \
                 mock.patch.object(iha_haritala, "oy_haritasi_kur",
                                   return_value=(blank, 1, oy)), \
                 mock.patch.object(iha_haritala, "_arac_maskesi",
                                   return_value=np.zeros_like(trav)), \
                 mock.patch.object(iha_haritala, "rota_bul", rota_mock), \
                 mock.patch.object(iha_haritala, "_overlay", return_value=blank):
                det = iha_haritala.haritala(
                    level_dir, model=None, htab_cx=0.0, htab_cy=0.0,
                    kb_xy=(0.0, 0.0), hb_xy=(0.0, 10.0))

            self.assertFalse((level_dir / "route.txt").exists())
            self.assertFalse((level_dir / "rota.json").exists())

        self.assertEqual(det["kb_tohum_px"], 0)
        self.assertEqual(det["rota_durum"], "ROTA_YOK")
        self.assertEqual(det["costmap_durum"], "DOGRULAMA_BASARISIZ")
        self.assertIn("KB 1x1 m tohum karesi C-uzayıyla kesişmiyor",
                      det["costmap_sebep"])
        self.assertEqual(int(rota_mock.call_args.kwargs["baslangic"].sum()), 0)

    def test_iha_harita_schema_and_model_provenance(self):
        plan = _plan()
        with tempfile.TemporaryDirectory() as tmp:
            level_dir = _level_dir(tmp)
            model_path = level_dir / "seg.pt"
            model_path.write_bytes(b"navitas-seg-test")
            model = SimpleNamespace(ckpt_path=model_path,
                                    names={0: "traversable", 1: "blocked"})
            det, _log, _ = _run_haritala(
                level_dir, plan, model=model, model_yolu=model_path)
            harita = json.loads((level_dir / "iha_harita.json").read_text(encoding="utf-8"))

            self.assertTrue((level_dir / "iha_harita.jpg").is_file())

        self.assertEqual(
            set(harita),
            {"kaynak", "model", "mozaik", "htab_merkez", "kb_xy", "hb_xy",
             "kb_px", "hb_px", "maske_ozet", "costmap", "tohum", "rota_px",
             "rota_dunya", "uretim_zamani",
             # kare başı oylama kanıtı — karar zinciri artık buradan çıkıyor
             "yontem", "kare_sayisi", "min_gozlem", "engel_orani",
             "bilinmeyen_hucre_orani", "ortalama_gozlem", "cikarim_sn"})
        self.assertEqual(harita["model"]["sha256"],
                         hashlib.sha256(b"navitas-seg-test").hexdigest())
        self.assertEqual(harita["model"]["imgsz"], iha_haritala.MOZ_PX)
        self.assertEqual(harita["model"]["names"]["0"], "traversable")
        self.assertTrue({"trav_px", "moloz_px", "arac_px", "engel_px"}
                        <= set(harita["maske_ozet"]))
        self.assertTrue({"kb_tohum_px", "hb_tohum_px", "kb_yolda", "hb_yolda",
                         "kb_ayni_bilesen"} <= set(harita["tohum"]))
        self.assertTrue(harita["uretim_zamani"].endswith("Z"))

    def test_htab_content_box_calculation_is_passed_to_planner(self):
        self.assertEqual(iha_haritala._htab_icerik_kutusu((1024, 1024)),
                         (55, 55, 914, 914))
        with tempfile.TemporaryDirectory() as tmp:
            level_dir = _level_dir(tmp)
            _det, _log, rota_mock = _run_haritala(level_dir, _plan())
        self.assertEqual(
            rota_mock.call_args.kwargs["icerik"],
            iha_haritala._htab_icerik_kutusu((8, 8)))


class OyHaritasiTest(unittest.TestCase):
    """Kare başı oylama: her karede çıkarım + dünya ızgarasında oy birikimi."""

    def test_sparse_cells_stay_unknown_and_are_not_traversable(self):
        # Aynı hücreye 3 kare bakıyor ve ÜÇÜ DE 'zemin' diyor. min_gozlem=8
        # olduğu için yine de BİLİNMEYEN kalmalı: az kanıt yol demek değildir.
        oy = {
            "zemin_oy": np.array([[3, 12]], dtype=np.int32),
            "engel_oy": np.zeros((1, 2), dtype=np.int32),
            "gozlem": np.array([[3, 12]], dtype=np.int32),
            "cikarim_sn": 0.0,
            "kare_sayisi": 12,
        }
        zemin, engel, bilinmeyen, ozet = iha_haritala.oy_haritasindan_maske(
            oy, min_gozlem=8, engel_orani=0.35)

        self.assertEqual(int(bilinmeyen[0, 0]), 1)
        self.assertEqual(int(zemin[0, 0]), 0, "az gözlemli hücre GEÇİLEBİLİR SAYILAMAZ")
        self.assertEqual(int(engel[0, 0]), 0)
        # Yeterli gözlemli komşu normal karar alır — eşik her şeyi silmiyor.
        self.assertEqual(int(zemin[0, 1]), 1)
        self.assertEqual(int(bilinmeyen[0, 1]), 0)
        self.assertEqual(ozet["bilinmeyen_hucre_orani"], 0.5)
        self.assertEqual(ozet["min_gozlem"], 8)

    def test_model_silence_is_unknown_not_road(self):
        # Hücreye 40 kare baktı ama hiçbiri sınıf üretmedi → BİLİNMEYEN.
        oy = {
            "zemin_oy": np.zeros((1, 1), dtype=np.int32),
            "engel_oy": np.zeros((1, 1), dtype=np.int32),
            "gozlem": np.full((1, 1), 40, dtype=np.int32),
            "cikarim_sn": 0.0, "kare_sayisi": 40,
        }
        zemin, _engel, bilinmeyen, _ozet = iha_haritala.oy_haritasindan_maske(oy)
        self.assertEqual(int(zemin[0, 0]), 0)
        self.assertEqual(int(bilinmeyen[0, 0]), 1)

    def test_obstacle_votes_win_below_symmetric_majority(self):
        # 20 gözlemin 7'si (=%35) engel diyor → ENGEL. 6'sı (=%30) diyor → zemin.
        # Eşik 0.50'nin ALTINDA: engel lehine muhafazakâr.
        oy = {
            "zemin_oy": np.array([[13, 14]], dtype=np.int32),
            "engel_oy": np.array([[7, 6]], dtype=np.int32),
            "gozlem": np.full((1, 2), 20, dtype=np.int32),
            "cikarim_sn": 0.0, "kare_sayisi": 20,
        }
        zemin, engel, bilinmeyen, _ozet = iha_haritala.oy_haritasindan_maske(
            oy, min_gozlem=8, engel_orani=0.35)
        self.assertEqual(int(engel[0, 0]), 1, "%35 engel oyu ENGEL demeli")
        self.assertEqual(int(zemin[0, 0]), 0)
        self.assertEqual(int(engel[0, 1]), 0)
        self.assertEqual(int(zemin[0, 1]), 1)
        self.assertEqual(int(bilinmeyen.sum()), 0)
        # Bir hücre asla iki sınıfa birden ait olamaz.
        self.assertEqual(int((zemin & engel).sum()), 0)

    def test_every_frame_is_inferred_and_votes_accumulate_in_world_grid(self):
        """`_infer` TEK BİR KEZ mozaikte değil, HER KAREDE ham kare üzerinde koşar."""
        import cv2

        boyut = 64
        gorulen = []

        def sahte_infer(img, model, conf, imgsz):
            gorulen.append(img.shape)
            zemin = np.ones(img.shape[:2], dtype=np.uint8)
            engel = np.zeros(img.shape[:2], dtype=np.uint8)
            return img, {0: zemin, 1: engel}, None, 0.0, [], "raw"

        with tempfile.TemporaryDirectory() as tmp:
            kare_dir = Path(tmp) / "kareler"
            kare_dir.mkdir()
            pozlar = {}
            for k in range(3):
                cv2.imwrite(str(kare_dir / f"scan_{k:05d}.jpg"),
                            np.full((40, 40, 3), 200, dtype=np.uint8))
                pozlar[k] = (0.0, 0.0, iha_haritala.SCAN_Z, np.pi / 2)
            with mock.patch.object(iha_haritala, "MOZ_PX", boyut), \
                 mock.patch.object(iha_haritala, "MPP", iha_haritala.MOZ_M / boyut), \
                 mock.patch.object(iha_haritala, "_infer", side_effect=sahte_infer):
                mozaik, n, oy = iha_haritala.oy_haritasi_kur(
                    kare_dir, pozlar, 0.0, 0.0, model=None, conf=0.15)

        self.assertEqual(n, 3)
        self.assertEqual(len(gorulen), 3, "model HER KAREDE koşmalı")
        # Kare mozaiğe ölçeklenmeden ÖNCE, doğal 40x40 hâliyle verildi.
        self.assertEqual(set(gorulen), {(40, 40, 3)})
        self.assertEqual(mozaik.shape, (boyut, boyut, 3))
        # Üç kare de aynı poza sahip → örtüşen bölgede tam 3 oy birikti.
        self.assertEqual(int(oy["gozlem"].max()), 3)
        self.assertEqual(int(oy["zemin_oy"].max()), 3)
        self.assertEqual(int(oy["engel_oy"].max()), 0)
        # Kare dışına taşan bölge OY VERMEZ: gözlem hiçbir yerde kare sayısını aşamaz
        # ve tuvalin hiç görülmeyen köşeleri 0 kalır (döndürülmüş ayak kare değil).
        self.assertLessEqual(int(oy["gozlem"].max()), 3)
        self.assertEqual(oy["kare_sayisi"], 3)
        self.assertGreaterEqual(oy["cikarim_sn"], 0.0)

    def test_frame_skip_processes_every_nth_accepted_frame(self):
        boyut = 64
        with tempfile.TemporaryDirectory() as tmp:
            kare_dir = Path(tmp) / "kareler"
            kare_dir.mkdir()
            import cv2
            pozlar = {}
            for k in range(6):
                cv2.imwrite(str(kare_dir / f"scan_{k:05d}.jpg"),
                            np.full((40, 40, 3), 200, dtype=np.uint8))
                pozlar[k] = (0.0, 0.0, iha_haritala.SCAN_Z, np.pi / 2)
            sahte = mock.Mock(side_effect=lambda img, *a, **k: (
                img, {0: np.ones(img.shape[:2], np.uint8),
                      1: np.zeros(img.shape[:2], np.uint8)}, None, 0.0, [], "raw"))
            with mock.patch.object(iha_haritala, "MOZ_PX", boyut), \
                 mock.patch.object(iha_haritala, "MPP", iha_haritala.MOZ_M / boyut), \
                 mock.patch.object(iha_haritala, "_infer", sahte):
                _m, n, oy = iha_haritala.oy_haritasi_kur(
                    kare_dir, pozlar, 0.0, 0.0, model=None, conf=0.15,
                    kare_atlama=3)
        self.assertEqual(n, 2)                 # 6 kabul edilen kare → 0. ve 3.
        self.assertEqual(sahte.call_count, 2)
        self.assertEqual(oy["kare_sayisi"], 2)

    def test_default_thresholds_are_conservative_towards_obstacles(self):
        """Ön kayıtlı eşikler: 0.50 simetrik çoğunluğun ALTINDA, tek kare üstünde."""
        self.assertEqual(iha_haritala.MIN_GOZLEM, 8)
        self.assertLess(iha_haritala.ENGEL_ORANI, 0.5)
        # Asgari gözlem sayısında tek bir kare kararı çeviremesin.
        self.assertGreater(iha_haritala.ENGEL_ORANI,
                           1.0 / iha_haritala.MIN_GOZLEM)

    def test_iha_harita_json_carries_voting_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            level_dir = _level_dir(tmp)
            _det, _log, _rota = _run_haritala(level_dir, _plan())
            harita = json.loads(
                (level_dir / "iha_harita.json").read_text(encoding="utf-8"))
            self.assertTrue((level_dir / "iha_oy_haritasi.jpg").is_file())

        self.assertEqual(harita["yontem"], "kare_basi_oylama")
        self.assertEqual(harita["kare_sayisi"], 1)
        self.assertEqual(harita["min_gozlem"], iha_haritala.MIN_GOZLEM)
        self.assertEqual(harita["engel_orani"], iha_haritala.ENGEL_ORANI)
        self.assertEqual(harita["bilinmeyen_hucre_orani"], 0.0)
        self.assertEqual(harita["ortalama_gozlem"], 20.0)
        self.assertEqual(harita["cikarim_sn"], 0.5)


if __name__ == "__main__":
    unittest.main()
