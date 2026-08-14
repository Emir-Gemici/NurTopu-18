"""T70: uretim algi yolunda canli irtifa olcegi fail-closed kapilari."""

import contextlib
import io
import math
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import cv2
import numpy as np


KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "codes"))

import rpi_inference as ri  # noqa: E402


class _SiraliOkuyucu:
    def __init__(self, *degerler):
        self.degerler = iter(degerler)
        self.cagri = 0
        self.baslatildi = 0
        self.durduruldu = 0

    def baslat(self):
        self.baslatildi += 1
        return True

    def durdur(self):
        self.durduruldu += 1
        return True

    def irtifa_m(self):
        self.cagri += 1
        deger = next(self.degerler)
        if isinstance(deger, Exception):
            raise deger
        return deger


class _Model:
    def predict(self, *_args, **_kwargs):
        return [object()]


class _TekKareKamera:
    def __init__(self, kare):
        self.kare = kare
        self.okundu = False

    def isOpened(self):
        return True

    def read(self):
        if self.okundu:
            return False, None
        self.okundu = True
        return True, self.kare.copy()

    def release(self):
        pass


class _VideoKareleri:
    def __init__(self, *kareler):
        self.kareler = list(kareler)
        self.indis = 0

    def isOpened(self):
        return True

    def read(self):
        if self.indis >= len(self.kareler):
            return False, None
        kare = self.kareler[self.indis]
        self.indis += 1
        return True, kare.copy()

    def get(self, ozellik):
        if ozellik == cv2.CAP_PROP_FRAME_COUNT:
            return len(self.kareler)
        if ozellik == cv2.CAP_PROP_FPS:
            return 30.0
        if ozellik == cv2.CAP_PROP_FRAME_WIDTH:
            return self.kareler[0].shape[1]
        if ozellik == cv2.CAP_PROP_FRAME_HEIGHT:
            return self.kareler[0].shape[0]
        return 0.0

    def release(self):
        pass


class CanliOlcekSaglayiciTesti(unittest.TestCase):
    def test_her_kare_canli_irtifa_ve_gercek_icerik_genisligi_kullanilir(self):
        okuyucu = _SiraliOkuyucu(30.0, 50.0)
        saglayici = ri.CanliOlcekSaglayici(
            okuyucu, yatay_fov_derece=60.0)

        mpp_640 = saglayici.kare_mpp(640)
        mpp_1024 = saglayici.kare_mpp(1024)

        self.assertEqual(2, okuyucu.cagri)
        self.assertAlmostEqual(
            2.0 * 30.0 * math.tan(math.radians(30.0)) / 640.0,
            mpp_640,
        )
        self.assertAlmostEqual(
            2.0 * 50.0 * math.tan(math.radians(30.0)) / 1024.0,
            mpp_1024,
        )
        self.assertNotAlmostEqual(
            2.0 * 30.0 * math.tan(math.radians(30.0)) / ri.INFER_SIZE,
            mpp_640,
        )

    def test_bayat_olcum_son_bilinen_irtifaya_donusturulmez(self):
        okuyucu = _SiraliOkuyucu(30.0, None)
        saglayici = ri.CanliOlcekSaglayici(
            okuyucu, yatay_fov_derece=60.0)

        self.assertIsNotNone(saglayici.kare_mpp(640))
        self.assertIsNone(saglayici.kare_mpp(640))
        self.assertEqual(2, okuyucu.cagri)

    def test_okuma_hatasi_olcek_yoktur(self):
        saglayici = ri.CanliOlcekSaglayici(
            _SiraliOkuyucu(RuntimeError("baglanti koptu")),
            yatay_fov_derece=60.0,
        )
        self.assertIsNone(saglayici.kare_mpp(640))

    def test_fov_ve_odak_tam_olarak_bir_tane_olmalidir(self):
        for kwargs in ({}, {"yatay_fov_derece": 60.0, "odak_px": 500.0}):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    ri.CanliOlcekSaglayici(_SiraliOkuyucu(30.0), **kwargs)

    def test_baglan_ortak_okuyucu_ve_sozlesme_tazeligini_kullanir(self):
        olaylar = []
        baglanti = SimpleNamespace(
            close=mock.Mock(side_effect=lambda: olaylar.append("close")))
        olusturulan = {}
        okuyucu = _SiraliOkuyucu(30.0)

        def baslat():
            okuyucu.baslatildi += 1
            olaylar.append("baslat")
            return True

        def durdur():
            okuyucu.durduruldu += 1
            olaylar.append("durdur")
            return True

        okuyucu.baslat = baslat
        okuyucu.durdur = durdur

        def okuyucu_uret(mav, tazelik_s, beklenen_sysid=None):
            olusturulan.update(
                mav=mav, tazelik_s=tazelik_s,
                beklenen_sysid=beklenen_sysid)
            return okuyucu

        modul = SimpleNamespace(
            mavlink_baglantisi_ac=mock.Mock(return_value=baglanti),
            BagilIrtifaOkuyucu=okuyucu_uret,
        )
        with mock.patch.object(ri, "_inis_kaniti_modulu", return_value=modul):
            saglayici = ri.CanliOlcekSaglayici.baglan(
                "udpin:0.0.0.0:14550", yatay_fov_derece=60.0,
                beklenen_sysid=7)

        self.assertIs(baglanti, olusturulan["mav"])
        self.assertEqual(
            ri.TELEMETRI_IRTIFA_TAZELIK_S, olusturulan["tazelik_s"])
        self.assertEqual(7, olusturulan["beklenen_sysid"])
        self.assertEqual(["baslat"], olaylar)
        self.assertEqual(1, okuyucu.baslatildi)
        self.assertIsNotNone(saglayici.kare_mpp(640))
        saglayici.kapat()
        baglanti.close.assert_called_once_with()
        self.assertEqual(1, okuyucu.durduruldu)
        self.assertEqual(["baslat", "durdur", "close"], olaylar)

    def test_poller_sahipligi_alinamazsa_baglanti_kapatilip_reddedilir(self):
        baglanti = SimpleNamespace(close=mock.Mock())
        okuyucu = _SiraliOkuyucu(30.0)
        okuyucu.baslat = mock.Mock(return_value=False)
        modul = SimpleNamespace(
            mavlink_baglantisi_ac=mock.Mock(return_value=baglanti),
            BagilIrtifaOkuyucu=mock.Mock(return_value=okuyucu),
        )
        with mock.patch.object(ri, "_inis_kaniti_modulu", return_value=modul):
            with self.assertRaises(RuntimeError):
                ri.CanliOlcekSaglayici.baglan(
                    "fake", yatay_fov_derece=60.0, beklenen_sysid=1)
        baglanti.close.assert_called_once_with()

    def test_saglayici_kurucusu_hatasinda_once_poller_durur_sonra_kapanir(self):
        olaylar = []
        baglanti = SimpleNamespace(
            close=mock.Mock(side_effect=lambda: olaylar.append("close")))
        okuyucu = _SiraliOkuyucu(30.0)
        okuyucu.baslat = mock.Mock(
            side_effect=lambda: olaylar.append("baslat") or True)
        okuyucu.durdur = mock.Mock(
            side_effect=lambda: olaylar.append("durdur") or True)
        modul = SimpleNamespace(
            mavlink_baglantisi_ac=mock.Mock(return_value=baglanti),
            BagilIrtifaOkuyucu=mock.Mock(return_value=okuyucu),
        )

        with mock.patch.object(ri, "_inis_kaniti_modulu", return_value=modul):
            with self.assertRaises(ValueError):
                ri.CanliOlcekSaglayici.baglan(
                    "fake", yatay_fov_derece=60.0, odak_px=500.0,
                    beklenen_sysid=1)

        self.assertEqual(["baslat", "durdur", "close"], olaylar)

    def test_poller_durmazsa_baglanti_thread_altindan_kapatilmaz(self):
        okuyucu = _SiraliOkuyucu(30.0)
        okuyucu.durdur = mock.Mock(return_value=False)
        baglanti = SimpleNamespace(close=mock.Mock())
        saglayici = ri.CanliOlcekSaglayici(
            okuyucu, yatay_fov_derece=60.0, baglanti=baglanti)

        self.assertFalse(saglayici.kapat())
        baglanti.close.assert_not_called()


class CanliOlcekKararYoluTesti(unittest.TestCase):
    @staticmethod
    def _maskeler():
        return {
            0: np.ones((640, 640), dtype=np.uint8),
            1: np.zeros((640, 640), dtype=np.uint8),
        }

    def test_run_image_bayat_telemetride_rota_ve_payload_uretmez(self):
        girdi = KOK / "tests" / "sahte_canli_kare.jpg"
        goruntu = np.full((360, 640, 3), 127, np.uint8)
        analyze = mock.Mock(return_value=(1, 0.99, [(10, 10), (10, 300)], None))
        harita = mock.Mock(return_value=np.zeros((640, 640, 3), np.uint8))
        cikti = io.StringIO()
        with mock.patch.object(Path, "is_dir", return_value=False), \
                mock.patch.object(Path, "is_file", return_value=True), \
                mock.patch.object(Path, "mkdir"), \
                mock.patch.object(cv2, "imread", return_value=goruntu), \
                mock.patch.object(cv2, "imwrite", return_value=True), \
                mock.patch.object(ri, "get_masks", return_value=self._maskeler()), \
                mock.patch.object(ri, "analyze_path", analyze), \
                mock.patch.object(ri, "generate_ika_map", harita), \
                contextlib.redirect_stdout(cikti):
            ri.run_image(
                _Model(), str(girdi), 0.30,
                canli_olcek=lambda _w: None,
            )

        self.assertIsNone(analyze.call_args.kwargs["mpp"])
        harita.assert_not_called()
        self.assertIn("NO_ROUTE: OLCEK_YOK", cikti.getvalue())
        self.assertNotIn("payload:", cikti.getvalue())

    def test_run_image_canli_olcegi_icerik_genisligiyle_analyze_path_e_verir(self):
        girdi = KOK / "tests" / "sahte_canli_kare.jpg"
        goruntu = np.full((360, 640, 3), 127, np.uint8)
        gorulen_genislikler = []
        olaylar = []

        def olcek(w):
            olaylar.append("provider")
            gorulen_genislikler.append(w)
            return 0.05

        def predict(*_args, **_kwargs):
            olaylar.append("predict")
            return [object()]

        def karar(*_args, **_kwargs):
            olaylar.append("analyze")
            return None, 0.0, [], ("KAPALI", "test")

        model = SimpleNamespace(predict=predict)
        analyze = mock.Mock(side_effect=karar)
        with mock.patch.object(Path, "is_dir", return_value=False), \
                mock.patch.object(Path, "is_file", return_value=True), \
                mock.patch.object(Path, "mkdir"), \
                mock.patch.object(cv2, "imread", return_value=goruntu), \
                mock.patch.object(cv2, "imwrite", return_value=True), \
                mock.patch.object(ri, "get_masks", return_value=self._maskeler()), \
                mock.patch.object(ri, "analyze_path", analyze), \
                contextlib.redirect_stdout(io.StringIO()):
            ri.run_image(model, str(girdi), 0.30, mpp=0.99,
                         canli_olcek=olcek)

        self.assertEqual([640], gorulen_genislikler)
        self.assertEqual(0.05, analyze.call_args.kwargs["mpp"])
        self.assertEqual(["predict", "provider", "analyze"], olaylar)

    def test_run_video_canli_olcegi_her_kare_yeniden_sorar(self):
        kare = np.full((360, 640, 3), 127, np.uint8)
        video = _VideoKareleri(kare, kare)
        gorulen_genislikler = []

        def olcek(w):
            gorulen_genislikler.append(w)
            return 0.05

        analyze = mock.Mock(return_value=(None, 0.0, [], ("KAPALI", "test")))
        with mock.patch.object(Path, "is_file", return_value=True), \
                mock.patch.object(cv2, "VideoCapture", return_value=video), \
                mock.patch.object(cv2, "imshow"), \
                mock.patch.object(cv2, "waitKey", return_value=-1), \
                mock.patch.object(cv2, "destroyAllWindows"), \
                mock.patch.object(ri, "get_masks", return_value=self._maskeler()), \
                mock.patch.object(ri, "analyze_path", analyze), \
                contextlib.redirect_stdout(io.StringIO()):
            ri.run_video(
                _Model(), "sahte.mp4", 0.30, save=False,
                canli_olcek=olcek,
            )

        self.assertEqual([640, 640], gorulen_genislikler)
        self.assertEqual([0.05, 0.05], [
            cagri.kwargs["mpp"] for cagri in analyze.call_args_list])

    def test_run_camera_statik_mpp_verilse_bile_bypass_olamaz(self):
        kare = np.full((360, 640, 3), 127, np.uint8)
        kamera = _TekKareKamera(kare)
        analyze = mock.Mock(return_value=(1, 0.99, [(10, 10), (10, 300)], None))
        waypoint_ciz = mock.Mock(side_effect=lambda vis, _wps: vis)
        with mock.patch.object(cv2, "VideoCapture", return_value=kamera), \
                mock.patch.object(cv2, "imshow"), \
                mock.patch.object(cv2, "waitKey", return_value=ord("q")), \
                mock.patch.object(cv2, "destroyAllWindows"), \
                mock.patch.object(ri, "get_masks", return_value=self._maskeler()), \
                mock.patch.object(ri, "analyze_path", analyze), \
                mock.patch.object(ri, "_draw_waypoints", waypoint_ciz), \
                contextlib.redirect_stdout(io.StringIO()):
            ri.run_camera(_Model(), 0.30, mpp=0.05, canli_olcek=None)

        self.assertIsNone(analyze.call_args.kwargs["mpp"])
        waypoint_ciz.assert_not_called()

    def test_run_camera_canli_olcegi_her_kare_karar_aninda_kullanir(self):
        kare = np.full((360, 640, 3), 127, np.uint8)
        kamera = _TekKareKamera(kare)
        olaylar = []
        genislikler = []

        def predict(*_args, **_kwargs):
            olaylar.append("predict")
            return [object()]

        def olcek(genislik):
            olaylar.append("provider")
            genislikler.append(genislik)
            return 0.05

        def karar(*_args, **_kwargs):
            olaylar.append("analyze")
            return None, 0.0, [], ("KAPALI", "test")

        analyze = mock.Mock(side_effect=karar)
        with mock.patch.object(cv2, "VideoCapture", return_value=kamera), \
                mock.patch.object(cv2, "imshow"), \
                mock.patch.object(cv2, "waitKey", return_value=ord("q")), \
                mock.patch.object(cv2, "destroyAllWindows"), \
                mock.patch.object(ri, "get_masks", return_value=self._maskeler()), \
                mock.patch.object(ri, "analyze_path", analyze), \
                contextlib.redirect_stdout(io.StringIO()):
            ri.run_camera(
                SimpleNamespace(predict=predict), 0.30,
                canli_olcek=olcek,
            )

        self.assertEqual([640], genislikler)
        self.assertEqual(0.05, analyze.call_args.kwargs["mpp"])
        self.assertEqual(["predict", "provider", "analyze"], olaylar)


class CanliOlcekCliTesti(unittest.TestCase):
    def test_fov_ve_odak_birlikte_argparse_tarafindan_reddedilir(self):
        parser = ri._arguman_ayristirici()
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as ctx:
                parser.parse_args([
                    "--camera", "--mavlink", "fake",
                    "--fov", "60", "--odak", "500",
                ])
        self.assertEqual(2, ctx.exception.code)

    def test_kamera_statik_mpp_veya_mavlinksiz_acilamaz(self):
        for argv in (["--camera", "--mpp", "0.05"], ["--camera"]):
            with self.subTest(argv=argv):
                parser = ri._arguman_ayristirici()
                args = parser.parse_args(argv)
                with contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as ctx:
                        ri._argumanlari_dogrula(parser, args)
                self.assertEqual(2, ctx.exception.code)

    def test_kamera_canli_mavlink_ve_tek_geometriyle_gecerlidir(self):
        parser = ri._arguman_ayristirici()
        args = parser.parse_args([
            "--camera", "--mavlink", "fake", "--fov", "60",
            "--mav-sysid", "1",
        ])
        ri._argumanlari_dogrula(parser, args)

    def test_mavlink_kaynagi_sysid_olmadan_reddedilir(self):
        parser = ri._arguman_ayristirici()
        args = parser.parse_args([
            "--camera", "--mavlink", "fake", "--fov", "60",
        ])
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as ctx:
                ri._argumanlari_dogrula(parser, args)
        self.assertEqual(2, ctx.exception.code)

    def test_mavlink_sysid_araligi_disinda_reddedilir(self):
        for sysid in (0, 256):
            with self.subTest(sysid=sysid):
                parser = ri._arguman_ayristirici()
                args = parser.parse_args([
                    "--camera", "--mavlink", "fake", "--fov", "60",
                    "--mav-sysid", str(sysid),
                ])
                with contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as ctx:
                        ri._argumanlari_dogrula(parser, args)
                self.assertEqual(2, ctx.exception.code)

    def test_main_canli_saglayiciyi_kamera_dongusune_aynen_tasir(self):
        model = object()
        saglayici = SimpleNamespace(kapat=mock.Mock(return_value=True))
        argv = [
            "rpi_inference.py", "--camera", "--mavlink", "fake",
            "--mav-sysid", "1", "--fov", "60",
        ]
        # T73: `main` artik `load_model(..., ayrinti=True)` cagiriyor ve
        # (model, yol, detay) bekliyor — hangi agirligin yuklendigini EKRANA
        # basmak icin. Sahte donus de o sozlesmeyi tasimalidir.
        sahte_yukleme = (model, Path("sahte_model.pt"), {"durum": "sinama"})
        with mock.patch.object(sys, "argv", argv), \
                mock.patch.object(ri.CanliOlcekSaglayici, "baglan",
                                  return_value=saglayici) as baglan, \
                mock.patch.object(ri, "load_model",
                                  return_value=sahte_yukleme), \
                mock.patch.object(ri, "run_camera") as run_camera:
            ri.main()

        baglan.assert_called_once_with(
            "fake", yatay_fov_derece=60.0, odak_px=None,
            beklenen_sysid=1)
        # T73: `main` artik kamera KAYNAGINI da tasiyor. `--kaynak`
        # verilmediginde None gecer ve `run_camera` icinde indeks 0'a cozulur
        # (geriye uyum). Beklenti bu sozlesmeyi kilitler.
        run_camera.assert_called_once_with(
            model, 0.30, canli_olcek=saglayici, kaynak=None)
        saglayici.kapat.assert_called_once_with()

    def test_model_yukleme_hatasinda_poller_kapatilir(self):
        saglayici = SimpleNamespace(kapat=mock.Mock(return_value=True))
        argv = [
            "rpi_inference.py", "--camera", "--mavlink", "fake",
            "--mav-sysid", "1", "--fov", "60",
        ]
        with mock.patch.object(sys, "argv", argv), \
                mock.patch.object(
                    ri.CanliOlcekSaglayici, "baglan", return_value=saglayici), \
                mock.patch.object(ri, "load_model", side_effect=RuntimeError("model")):
            with self.assertRaises(RuntimeError):
                ri.main()
        saglayici.kapat.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
