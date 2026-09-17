"""ONARIM-03 (2026-09-17): `rpi_inference --gorev-kaydi` Jetson kare kaydi.

Kilitler:
  1) Her islenen kare icin bir KARE satiri; zemin/engel piksel sayisi, red kodu,
     yayinlandi bayragi dogru; GOREV_BASLADI (boot_id) ve KAMERA_BITTI + OTURUM_BITTI.
  2) KARAR YOLU BAYT-ES: kayitli ve kayitsiz kosumda `_karari_yayinla`ya giden
     argumanlar birebir ayni (kayit karari etkilemez).
  3) Yazma hatasi (disk dolu vb.) kosumu DURDURMAZ: bir kez UYARI, kayit kapanir,
     yayinlar yine birebir ayni.
  4) Kayit dizini acilamazsa UYARI + None (ucus surer).
  5) CLI: `--gorev-kaydi` yalniz `--camera` ile; birim yolu sozlesmesi.
"""

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import cv2

KOK = Path(__file__).resolve().parents[1]
for _p in (KOK / "codes", KOK / "comms", KOK / "tests"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import rpi_inference as ri  # noqa: E402
from test_faz_b_rpi_ekransiz import (  # noqa: E402
    _Kamera, _Yayinla, _analiz_dizisi, _maskeler)


def _kos(kare, gorev_kaydi):
    yayinla = _Yayinla()
    with mock.patch.object(cv2, "VideoCapture", return_value=_Kamera(kare)), \
            mock.patch.object(ri, "get_masks", return_value=_maskeler()), \
            mock.patch.object(ri, "analyze_path", _analiz_dizisi()), \
            mock.patch.object(ri, "_karari_yayinla", yayinla), \
            contextlib.redirect_stdout(io.StringIO()) as cikti:
        ozet = ri.run_camera(SimpleNamespace(predict=lambda *a, **k: [object()]),
                             0.30, canli_olcek=(lambda _w: 0.05),
                             yayinci=object(), ekransiz=True,
                             gorev_kaydi=gorev_kaydi)
    return ozet, yayinla.cagrilar, cikti.getvalue()


def _satirlar(yol):
    return [json.loads(s) for s in Path(yol).read_text(encoding="utf-8").splitlines()]


class GorevKaydi(unittest.TestCase):
    def setUp(self):
        self._d = tempfile.TemporaryDirectory()
        self.d = Path(self._d.name)

    def tearDown(self):
        self._d.cleanup()

    def _ac(self):
        with contextlib.redirect_stdout(io.StringIO()):
            kayit = ri.gorev_kaydi_ac(self.d / "gorev", Path("navitas_seg_v36_best.pt"))
        self.assertIsNotNone(kayit)
        return kayit

    def test_1_kare_satirlari_ve_alanlar(self):
        kayit = self._ac()
        ozet, cagrilar, _ = _kos(3, kayit)
        ri.gorev_kaydi_kapat(kayit)
        s = _satirlar(kayit.yol)
        olaylar = [r["olay"] for r in s]
        self.assertEqual(olaylar, ["OTURUM_BASLADI", "GOREV_BASLADI", "KARE", "KARE", "KARE",
                                   "KAMERA_BITTI", "OTURUM_BITTI"])
        bas = s[1]
        self.assertEqual(bas["model"], "navitas_seg_v36_best.pt")
        self.assertIn("boot_id", bas)
        kareler = [r for r in s if r["olay"] == "KARE"]
        self.assertEqual([r["kare"] for r in kareler], [1, 2, 3])
        for r in kareler:
            # 640x360 kare 640x640 kareye oturur; maske icerik kutusuna kirpilir
            self.assertEqual(r["zemin_px"], 640 * 360)
            self.assertEqual(r["engel_px"], 0)
            self.assertEqual(r["maske_hw"], [640, 640])
            self.assertIn("monotonic_s", r)
            self.assertIn("cikarim_ms", r)
        self.assertEqual(kareler[2]["red"], "KARAR_YOK")
        self.assertIsNone(kareler[2]["yol"])
        self.assertEqual(sum(1 for r in kareler if r["yayinlandi"]), len(cagrilar))
        self.assertEqual(s[5]["okunan"], ozet["okunan"])
        # yol sozlesmesi: <dizin>/<tarih>_<boot8>_<pid>/gorev_kaydi.jsonl
        self.assertEqual(kayit.yol.name, "gorev_kaydi.jsonl")
        self.assertTrue(kayit.yol.parent.name.endswith(f"_{os.getpid()}"))

    def test_2_karar_yolu_kayitli_kayitsiz_BIREBIR(self):
        _, kayitsiz, _ = _kos(3, None)
        kayit = self._ac()
        _, kayitli, _ = _kos(3, kayit)
        ri.gorev_kaydi_kapat(kayit)
        self.assertGreaterEqual(len(kayitsiz), 2, kayitsiz)
        self.assertEqual(kayitsiz, kayitli)

    def test_3_yazma_hatasi_kosumu_DURDURMAZ(self):
        kayit = self._ac()
        kayit._fsync = mock.MagicMock(side_effect=OSError(28, "No space left on device"))
        ozet, kayitli, cikti = _kos(3, kayit)
        _, kayitsiz, _ = _kos(3, None)
        self.assertEqual(3, ozet["okunan"])
        self.assertEqual(kayitsiz, kayitli)
        self.assertEqual(1, cikti.count("UYARI: gorev kaydi yazilamadi"), cikti)

    def test_4_acilamayan_dizin_UYARI_ve_None(self):
        engel = self.d / "dosya"
        engel.write_text("x")
        with contextlib.redirect_stdout(io.StringIO()) as c:
            kayit = ri.gorev_kaydi_ac(engel / "alt")
        self.assertIsNone(kayit)
        self.assertIn("UYARI: gorev kaydi ACILAMADI", c.getvalue())
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertIsNone(ri.gorev_kaydi_ac(None))

    def test_5_yol_boot_id_kisaltmasi(self):
        y = ri.gorev_kaydi_yolu("/k", boot_id="3f2a9c1e-aaaa-bbbb", pid=42, simdi=0)
        self.assertEqual(y.name, "gorev_kaydi.jsonl")
        self.assertTrue(y.parent.name.endswith("_3f2a9c1e_42"), y)
        self.assertTrue(ri.gorev_kaydi_yolu("/k", boot_id=None, pid=1).parent.name.endswith("_bootyok_1"))


class GorevKaydiCli(unittest.TestCase):
    def test_6_gorev_kaydi_yalniz_camera_ile(self):
        parser = ri._arguman_ayristirici()
        args = parser.parse_args(["--image", "x.jpg", "--gorev-kaydi", "/tmp/g"])
        self.assertEqual(args.gorev_kaydi, Path("/tmp/g"))
        with contextlib.redirect_stderr(io.StringIO()) as e, self.assertRaises(SystemExit) as cm:
            ri._argumanlari_dogrula(parser, args)
        self.assertEqual(cm.exception.code, 2)
        self.assertIn("--gorev-kaydi yalniz --camera", e.getvalue())


if __name__ == "__main__":
    unittest.main()
