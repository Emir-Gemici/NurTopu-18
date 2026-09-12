"""D-404 (Faz B, donanim-oncesi kapanis): `rpi_inference --ekransiz` kipi.

NEDEN: Gorev C olcumu — `run_camera` her karede KOSULSUZ `cv2.imshow` cagiriyordu;
ekransiz Jetson'da (systemd, DISPLAY yok) ilk karede `cv2.error` ile cokup
`Restart=always` dongusune giriyordu (sartname §6.2 hands-off ihlali).

Kilitler:
  1) ekransiz=True  -> imshow DISPLAY yok diye patlasa bile kosum TAMAMLANIR,
     butun kareler islenir; gorsel HIC uretilmez (draw_masks cagrilmaz).
  2) ekransiz=False -> davranis DEGISMEDI: imshow patlarsa hata yukselir
     (sessiz yutma yok; masaustu kullanicisi hatayi gorur).
  3) KARAR YOLU BAYT-ES: ayni kare dizisiyle iki kipte `_karari_yayinla`ya
     giden argumanlar birebir ayni (madde 15 — algoritma degismedi).
  4) run_video: kayitsiz + ekransiz kosumda imshow/draw_masks yok.
  5) CLI `--ekransiz` bayragi var; systemd birimi bu bayrakla kosar ve
     DISPLAY/XAUTHORITY tasimaz (birim dosyasi metin kilidi).
"""

import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import cv2
import numpy as np

KOK = Path(__file__).resolve().parents[1]
for _p in (KOK / "codes", KOK / "comms"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import rpi_inference as ri  # noqa: E402

BIRIM = KOK / "jetson_paket" / "systemd" / "navitas-rpi-inference.service"


class _Kamera:
    def __init__(self, n, sekil=(360, 640, 3)):
        self.kalan = n
        self.sekil = sekil

    def isOpened(self):
        return True

    def read(self):
        if self.kalan <= 0:
            return False, None
        self.kalan -= 1
        return True, np.full(self.sekil, 127, np.uint8)

    def get(self, _prop):
        return 0

    def release(self):
        pass


def _maskeler():
    return {0: np.ones((640, 640), np.uint8), 1: np.zeros((640, 640), np.uint8)}


def _analiz_dizisi():
    """Kare sirasina gore degisen karar: histerezisi de calistirir."""
    sira = [
        ("1", 0.9, [(1, 2), (3, 4)], None),
        ("1", 0.9, [(1, 2), (3, 4)], None),
        (None, 0.0, [], ("KARAR_YOK", "sahte")),
    ]
    say = {"i": 0}

    def analiz(*_a, **_k):
        r = sira[min(say["i"], len(sira) - 1)]
        say["i"] += 1
        return r
    return analiz


def _imshow_display_yok(*_a, **_k):
    raise cv2.error("Navitas: DISPLAY yok (sahte cv2.error)")


class _Yayinla:
    """`_karari_yayinla` cagrilarini argumanlariyla toplar."""

    def __init__(self):
        self.cagrilar = []

    def __call__(self, yayinci, open_path, path_conf, waypoints, mpp, reddi):
        self.cagrilar.append((open_path, float(path_conf), list(waypoints),
                              mpp, reddi))


def _run_camera(kare, *, ekransiz, imshow, waitkey=0, yayinla=None):
    yayinla = yayinla or _Yayinla()
    draw = mock.MagicMock(side_effect=lambda sq, _m: sq)
    with mock.patch.object(cv2, "VideoCapture", return_value=_Kamera(kare)), \
            mock.patch.object(cv2, "imshow", side_effect=imshow), \
            mock.patch.object(cv2, "waitKey", return_value=waitkey), \
            mock.patch.object(cv2, "destroyAllWindows"), \
            mock.patch.object(ri, "get_masks", return_value=_maskeler()), \
            mock.patch.object(ri, "analyze_path", _analiz_dizisi()), \
            mock.patch.object(ri, "draw_masks", draw), \
            mock.patch.object(ri, "_draw_waypoints", side_effect=lambda v, _w: v), \
            mock.patch.object(ri, "_karari_yayinla", yayinla), \
            contextlib.redirect_stdout(io.StringIO()) as cikti:
        ozet = ri.run_camera(SimpleNamespace(predict=lambda *a, **k: [object()]),
                             0.30, canli_olcek=(lambda _w: 0.05),
                             yayinci=object(), ekransiz=ekransiz)
    return ozet, yayinla.cagrilar, draw, cikti.getvalue()


class EkransizKamera(unittest.TestCase):
    def test_1_ekransiz_display_yokken_TAMAMLANIR_ve_gorsel_uretilmez(self):
        ozet, cagrilar, draw, cikti = _run_camera(
            3, ekransiz=True, imshow=_imshow_display_yok)
        self.assertEqual(3, ozet["okunan"], ozet)
        self.assertIsNotNone(ozet["bitis"])
        self.assertNotEqual(ri.KAMERA_BITIS_KULLANICI, ozet["bitis"])
        self.assertEqual(0, draw.call_count, "ekransizda draw_masks cagrilmamali")
        self.assertGreaterEqual(len(cagrilar), 1, "karar yayini surmeli")
        self.assertIn("EKRANSIZ kip", cikti)

    def test_2_varsayilan_kipte_imshow_hatasi_YUKSELIR_davranis_degismedi(self):
        with self.assertRaises(cv2.error):
            _run_camera(3, ekransiz=False, imshow=_imshow_display_yok)

    def test_3_karar_yolu_iki_kipte_BIREBIR_ayni(self):
        _, ekranli, draw_e, _ = _run_camera(3, ekransiz=False, imshow=lambda *a, **k: None)
        _, ekransiz, draw_s, _ = _run_camera(3, ekransiz=True, imshow=_imshow_display_yok)
        self.assertEqual(ekranli, ekransiz)
        self.assertEqual(3, draw_e.call_count, "ekranli kipte her kare cizilir")
        self.assertEqual(0, draw_s.call_count)
        # Vakum kontrolu: karsilastirma bos listeyle gecmesin.
        self.assertGreaterEqual(len(ekranli), 2, ekranli)

    def test_4_ekranli_kipte_q_durdurur_ekransizda_waitKey_hic_cagrilmaz(self):
        ozet, _, _, _ = _run_camera(3, ekransiz=False,
                                    imshow=lambda *a, **k: None, waitkey=ord("q"))
        self.assertEqual(ri.KAMERA_BITIS_KULLANICI, ozet["bitis"])
        with mock.patch.object(cv2, "waitKey") as wk:
            with mock.patch.object(cv2, "VideoCapture", return_value=_Kamera(2)), \
                    mock.patch.object(cv2, "imshow", side_effect=_imshow_display_yok), \
                    mock.patch.object(ri, "get_masks", return_value=_maskeler()), \
                    mock.patch.object(ri, "analyze_path", _analiz_dizisi()), \
                    mock.patch.object(ri, "_karari_yayinla", _Yayinla()), \
                    contextlib.redirect_stdout(io.StringIO()):
                ri.run_camera(SimpleNamespace(predict=lambda *a, **k: [object()]),
                              0.30, canli_olcek=(lambda _w: 0.05),
                              yayinci=object(), ekransiz=True)
        self.assertEqual(0, wk.call_count)


class EkransizVideo(unittest.TestCase):
    def test_5_kayitsiz_ekransiz_videoda_imshow_ve_cizim_yok(self):
        with tempfile.TemporaryDirectory() as d:
            yol = Path(d) / "sahte.mp4"
            yol.write_bytes(b"\x00")
            draw = mock.MagicMock(side_effect=lambda sq, _m: sq)
            imshow = mock.MagicMock(side_effect=_imshow_display_yok)
            with mock.patch.object(cv2, "VideoCapture", return_value=_Kamera(3)), \
                    mock.patch.object(cv2, "imshow", imshow), \
                    mock.patch.object(cv2, "waitKey", return_value=0), \
                    mock.patch.object(cv2, "destroyAllWindows"), \
                    mock.patch.object(ri, "get_masks", return_value=_maskeler()), \
                    mock.patch.object(ri, "analyze_path", _analiz_dizisi()), \
                    mock.patch.object(ri, "draw_masks", draw), \
                    mock.patch.object(ri, "_karari_yayinla", _Yayinla()), \
                    contextlib.redirect_stdout(io.StringIO()):
                ri.run_video(SimpleNamespace(predict=lambda *a, **k: [object()]),
                             str(yol), 0.30, save=False, mpp=0.05,
                             ekransiz=True)
            self.assertEqual(0, imshow.call_count)
            self.assertEqual(0, draw.call_count)


class EkransizKayitliVideo(unittest.TestCase):
    """D-404 §2 bagimsiz denetim ONEMLI-1: ekransiz+KAYITLI video yolu (satir
    ~2141-2161) hicbir testte yurumuyordu; 4/7 mutant suitten geciyordu."""

    def _kos(self, *, ekransiz, save, kare=3):
        with tempfile.TemporaryDirectory() as d:
            yol = Path(d) / "sahte.mp4"
            yol.write_bytes(b"\x00")
            draw = mock.MagicMock(side_effect=lambda sq, _m: sq)
            imshow = mock.MagicMock()
            waitkey = mock.MagicMock(return_value=0)
            destroy = mock.MagicMock()
            yazici = mock.MagicMock()
            with mock.patch.object(cv2, "VideoCapture", return_value=_Kamera(kare)), \
                    mock.patch.object(cv2, "VideoWriter", return_value=yazici), \
                    mock.patch.object(cv2, "VideoWriter_fourcc", return_value=0), \
                    mock.patch.object(ri, "RESULTS_DIR", Path(d) / "sonuc"), \
                    mock.patch.object(cv2, "imshow", imshow), \
                    mock.patch.object(cv2, "waitKey", waitkey), \
                    mock.patch.object(cv2, "destroyAllWindows", destroy), \
                    mock.patch.object(ri, "get_masks", return_value=_maskeler()), \
                    mock.patch.object(ri, "analyze_path", _analiz_dizisi()), \
                    mock.patch.object(ri, "draw_masks", draw), \
                    mock.patch.object(ri, "_karari_yayinla", _Yayinla()), \
                    contextlib.redirect_stdout(io.StringIO()):
                ri.run_video(SimpleNamespace(predict=lambda *a, **k: [object()]),
                             str(yol), 0.30, save=save, mpp=0.05,
                             ekransiz=ekransiz)
        return SimpleNamespace(draw=draw, imshow=imshow, waitkey=waitkey,
                               destroy=destroy, yazici=yazici)

    def test_8_ekransiz_KAYITLI_video_her_kare_yazilir_pencere_yok(self):
        s = self._kos(ekransiz=True, save=True)
        self.assertEqual(3, s.yazici.write.call_count, "kayit ekransizda da SURER")
        self.assertEqual(3, s.draw.call_count, "gorsel yalniz yazici icin uretilir")
        self.assertEqual(0, s.imshow.call_count)
        self.assertEqual(0, s.waitkey.call_count)
        self.assertEqual(0, s.destroy.call_count)
        self.assertEqual(1, s.yazici.release.call_count)

    def test_9_destroyAllWindows_yalniz_ekranli_kipte(self):
        ekranli = self._kos(ekransiz=False, save=False)
        self.assertEqual(1, ekranli.destroy.call_count)
        self.assertEqual(3, ekranli.imshow.call_count)
        ekransiz = self._kos(ekransiz=False, save=True)
        self.assertEqual(3, ekransiz.yazici.write.call_count, "ekranli+kayitli: ikisi de")
        # Kamera dongusu: ekranlida 1, ekransizda 0.
        with mock.patch.object(cv2, "destroyAllWindows") as destroy:
            with mock.patch.object(cv2, "VideoCapture", return_value=_Kamera(2)), \
                    mock.patch.object(cv2, "imshow"), \
                    mock.patch.object(cv2, "waitKey", return_value=0), \
                    mock.patch.object(ri, "get_masks", return_value=_maskeler()), \
                    mock.patch.object(ri, "analyze_path", _analiz_dizisi()), \
                    mock.patch.object(ri, "draw_masks", side_effect=lambda sq, _m: sq), \
                    mock.patch.object(ri, "_karari_yayinla", _Yayinla()), \
                    contextlib.redirect_stdout(io.StringIO()):
                ri.run_camera(SimpleNamespace(predict=lambda *a, **k: [object()]),
                              0.30, canli_olcek=(lambda _w: 0.05),
                              yayinci=object(), ekransiz=False)
                self.assertEqual(1, destroy.call_count)
                ri.run_camera(SimpleNamespace(predict=lambda *a, **k: [object()]),
                              0.30, canli_olcek=(lambda _w: 0.05),
                              yayinci=object(), ekransiz=True)
                self.assertEqual(1, destroy.call_count, "ekransizda cagrilmadi")


class CliVeBirim(unittest.TestCase):
    def test_6_cli_ekransiz_bayragi_var(self):
        sonuc = subprocess.run(
            [sys.executable, "-B", str(KOK / "codes" / "rpi_inference.py"), "--help"],
            capture_output=True, text=True, timeout=120, cwd=KOK)
        self.assertEqual(0, sonuc.returncode, sonuc.stderr[-800:])
        self.assertIn("--ekransiz", sonuc.stdout)

    def test_7_systemd_birimi_ekransiz_kosar_DISPLAY_tasimaz(self):
        metin = BIRIM.read_text(encoding="utf-8")
        exec_start = [s for s in metin.splitlines() if s.startswith("ExecStart=")]
        self.assertEqual(1, len(exec_start), exec_start)
        self.assertIn("--ekransiz", exec_start[0])
        self.assertIn("--camera", exec_start[0])
        for s in metin.splitlines():
            if s.startswith("#"):
                continue
            self.assertNotIn("DISPLAY", s, s)
            self.assertNotIn("XAUTHORITY", s, s)


class EkransizFpsRaporu(unittest.TestCase):
    """T233: ekransiz kipte p95/ortalama FPS `ozet`e ve bitis satirina duser.

    NEDEN: `run_camera` ekransiz kipte `live_fps`i (ekrana yazilan) hic
    hesaplamiyordu — A10'da SS4.4 kapisinin p95 kosulu canli kamerada
    OLCULEMIYORDU. `time.perf_counter` sabit bir dizi ile taklit edilir:
    ilk 10 kare 100 ms (yavas), sonraki 30 kare 10 ms (hizli) — `fps_buf`
    (SON 30 kare) tum yavas kareleri ATAR; `tum_sureler` (oturum) atmaz.
    Iki hesap FARKLI sayi verir, bu yuzden mutasyon (yanlislikla `fps_buf`
    kullanma) test tarafindan YAKALANIR.
    """

    def _run_camera_zamanli(self, sureler_s, *, ekransiz):
        # Her kare 2 `perf_counter()` cagrisi tuketir (t0 ve sure sonu);
        # aralarindaki fark istenen sureyi verecek sekilde ciftlenir.
        zaman_dizisi = []
        for s in sureler_s:
            zaman_dizisi += [0.0, s]
        yayinla = _Yayinla()
        draw = mock.MagicMock(side_effect=lambda sq, _m: sq)
        with mock.patch.object(cv2, "VideoCapture",
                               return_value=_Kamera(len(sureler_s))), \
                mock.patch.object(cv2, "imshow"), \
                mock.patch.object(cv2, "waitKey", return_value=0), \
                mock.patch.object(cv2, "destroyAllWindows"), \
                mock.patch.object(ri, "get_masks", return_value=_maskeler()), \
                mock.patch.object(ri, "analyze_path", _analiz_dizisi()), \
                mock.patch.object(ri, "draw_masks", draw), \
                mock.patch.object(ri, "_draw_waypoints", side_effect=lambda v, _w: v), \
                mock.patch.object(ri, "_karari_yayinla", yayinla), \
                mock.patch.object(ri.time, "perf_counter", side_effect=zaman_dizisi), \
                contextlib.redirect_stdout(io.StringIO()) as cikti:
            ozet = ri.run_camera(SimpleNamespace(predict=lambda *a, **k: [object()]),
                                 0.30, canli_olcek=(lambda _w: 0.05),
                                 yayinci=object(), ekransiz=ekransiz)
        return ozet, cikti.getvalue()

    def test_ekransizda_oturum_capinda_p95_ve_ortalama_fps_raporlanir(self):
        sureler = [0.1] * 10 + [0.01] * 30  # 40 kare, fps_buf yalniz son 30'u tutar
        ozet, cikti = self._run_camera_zamanli(sureler, ekransiz=True)
        self.assertEqual(40, ozet["fps_ornek"], ozet)
        # tum_sureler ortalamasi: (10*100+30*10) ms / 40 = 32.5 ms -> 30.769 fps
        self.assertAlmostEqual(30.769, ozet["fps_ortalama"], places=2, msg=ozet)
        # p95 (40 ornek, ilk 30 hizli 10ms sirali sonra 10 yavas 100ms):
        # numpy yuzdelik indeksi 37-38 tamamen yavas grupta -> 100 ms -> 10.0 fps
        self.assertAlmostEqual(10.0, ozet["fps_p95"], places=2, msg=ozet)
        self.assertIn("fps_ortalama=30.769", cikti)
        self.assertIn("fps_p95=10.0", cikti)
        # Mutasyon kontrolu: fps_buf (son 30, hepsi hizli) kullanilsaydi
        # ortalama ~100 fps cikardi — 30,77 ile KARISTIRILAMAZ.
        self.assertLess(ozet["fps_ortalama"], 50.0, "fps_buf'a (son 30) kaymis olabilir")

    def test_ekranli_kipte_fps_alanlari_EKLENMEZ_davranis_degismedi(self):
        ozet, cikti = self._run_camera_zamanli([0.01, 0.01, 0.01], ekransiz=False)
        self.assertNotIn("fps_ortalama", ozet)
        self.assertNotIn("fps_p95", ozet)
        self.assertNotIn("fps_ortalama=", cikti)


if __name__ == "__main__":
    unittest.main()
