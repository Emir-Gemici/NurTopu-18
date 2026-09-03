"""NEDEN (TASK_QUEUE T204 + T205 · REVIEW_LOG D-404 §8, bagimsiz denetci
KUCUK-2 ve KUCUK-3). Iki olculen kusur, ikisi de EKRANSIZ saha kipinde:

T204 — KONTROLLU DURDURMA YOK. `codes/rpi_inference.py` `signal`i HIC
islemiyordu. `systemctl stop navitas-rpi-inference` SIGTERM yollar ve Python
varsayilani surecin ANINDA olmesidir: `run_camera`/`run_video` icindeki
`cap.release()` ve `main()` finally'si (`yayinci.stop`, `link.close`,
`canli_olcek.kapat`) HIC kosmuyordu — kamera serbest birakilmiyor, telsiz
is parcacigi kapatilmiyordu. Ekranli kipte 'q' bu yolu sagliyordu; ekransiz
kipte 'q' YOKTUR, tek dogal bitis 30 ardisik dusen karedir.

T205 — SESSIZ OLU YAZICI. `cv2.VideoWriter` ASLA None dondurmez: codec ya da
yazma izni yoksa nesne yine uretilir ve `bool(writer)` TRUE kalir. Eski kod
her kareyi bu olu yaziciya yaziyor, sonda "Kaydedildi:" basiyordu — KAYIT
SESSIZCE KAYBOLUYORDU. Ustelik ekransiz kipin "gorsel HIC uretilmez" vaadi de
bozuluyordu (`if ekransiz and not writer` yanlis dala giriyordu).

Bu dosyanin kilitleri:
  1) sinyal GERCEKTEN yollanir (`signal.raise_signal`), sahte cagri degil;
  2) her cikis yolunda (sinyal, istisna, KeyboardInterrupt) `cap.release()`
     TAM 1 kez kosar — `finally` gercekten var;
  3) dusen-kare yeniden deneme dongusu de sinyali gorur (SIGTERM 30 x bekleme
     kadar cevapsiz kalmaz — systemd TimeoutStopSec=5);
  4) olu yazici GORUNUR sekilde basarisiz olur ve KARAR YOLU DEGISMEZ
     (madde 15: yayinlanan kararlar saglam yazicidakiyle BIREBIR ayni).
"""

import contextlib
import io
import signal
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import cv2
import numpy as np

KOK = Path(__file__).resolve().parents[1]
for _yol in (KOK / "codes", KOK / "comms"):
    if str(_yol) not in sys.path:
        sys.path.insert(0, str(_yol))

import rpi_inference as ri  # noqa: E402


class SahteKamera:
    """`cv2.VideoCapture` yerine: N kare verir, `release` cagrilarini SAYAR."""

    def __init__(self, kare=5, sekil=(360, 640, 3), acik=True):
        self.kalan = kare
        self.sekil = sekil
        self._acik = acik
        self.release_sayisi = 0
        self.okuma_sayisi = 0

    def isOpened(self):
        return self._acik

    def read(self):
        self.okuma_sayisi += 1
        if self.kalan <= 0:
            return False, None
        self.kalan -= 1
        return True, np.full(self.sekil, 127, np.uint8)

    def get(self, prop):
        return {cv2.CAP_PROP_FPS: 30.0,
                cv2.CAP_PROP_FRAME_COUNT: 5,
                cv2.CAP_PROP_FRAME_WIDTH: 640,
                cv2.CAP_PROP_FRAME_HEIGHT: 360}.get(prop, 0)

    def release(self):
        self.release_sayisi += 1


class SahteYazici:
    """`cv2.VideoWriter` yerine: `isOpened` DENETLENIYOR mu, olcer.

    🔴 Gercek cv2 davranisi taklit edilir: acilamamis yazici bile TRUTHY'dir
    (`__bool__` tanimlanmaz) ve `write()` sessizce yutar. Kusurun ozu budur.
    """

    def __init__(self, acik=True):
        self._acik = acik
        self.yazilan = 0
        self.release_sayisi = 0

    def isOpened(self):
        return self._acik

    def write(self, _kare):
        self.yazilan += 1

    def release(self):
        self.release_sayisi += 1


def _maskeler():
    return {0: np.ones((640, 640), np.uint8), 1: np.zeros((640, 640), np.uint8)}


def _analiz(*_a, **_k):
    return ("1", 0.9, [(1, 2), (3, 4)], None)


class _Yayinla:
    """`_karari_yayinla` yerine: cagrilari toplar, istege gore SINYAL yollar."""

    def __init__(self, sinyal_kare=None, gercek_sinyal=False):
        self.cagrilar = []
        self._sinyal_kare = sinyal_kare
        self._gercek = gercek_sinyal

    def __call__(self, yayinci, open_path, path_conf, waypoints, mpp, reddi):
        self.cagrilar.append((open_path, float(path_conf), list(waypoints),
                              mpp, reddi))
        if self._sinyal_kare is not None and len(self.cagrilar) == self._sinyal_kare:
            if self._gercek:
                signal.raise_signal(signal.SIGTERM)
            else:
                ri.durdurmayi_iste()


@contextlib.contextmanager
def _algi_sahtesi(yayinla, *, draw=None):
    draw = draw if draw is not None else mock.MagicMock(side_effect=lambda sq, _m: sq)
    with mock.patch.object(ri, "get_masks", return_value=_maskeler()), \
            mock.patch.object(ri, "analyze_path", _analiz), \
            mock.patch.object(ri, "draw_masks", draw), \
            mock.patch.object(ri, "_draw_waypoints", side_effect=lambda v, _w: v), \
            mock.patch.object(ri, "_karari_yayinla", yayinla):
        yield draw


class DurdurmaBayragiTemiz(unittest.TestCase):
    """Her testte bayrak SIFIRLANIR: sizinti baska testi kandirmasin."""

    def setUp(self):
        ri.durdurma_bayragini_sifirla()

    def tearDown(self):
        ri.durdurma_bayragini_sifirla()


# ── T204/1 · SINYAL ISLEYICISI: GERCEK SIGTERM/SIGINT ────────────────────────

class SinyalIsleyicisi(DurdurmaBayragiTemiz):
    def test_1_gercek_SIGTERM_bayragi_kurar(self):
        eskiler = ri._durdurma_sinyallerini_kur()
        try:
            self.assertFalse(ri.durdurma_istendi())
            signal.raise_signal(signal.SIGTERM)   # GERCEK sinyal teslimi
            self.assertTrue(ri.durdurma_istendi(),
                            "SIGTERM kontrollu durdurmayi TETIKLEMEDI")
        finally:
            ri._durdurma_sinyallerini_geri_al(eskiler)

    def test_2_gercek_SIGINT_bayragi_kurar(self):
        eskiler = ri._durdurma_sinyallerini_kur()
        try:
            signal.raise_signal(signal.SIGINT)
            self.assertTrue(ri.durdurma_istendi())
        finally:
            ri._durdurma_sinyallerini_geri_al(eskiler)

    def test_3_onceki_isleyiciler_GERI_ALINIR(self):
        onceki = {s: signal.getsignal(s)
                  for s in (signal.SIGTERM, signal.SIGINT)}
        eskiler = ri._durdurma_sinyallerini_kur()
        self.assertNotEqual(onceki[signal.SIGTERM],
                            signal.getsignal(signal.SIGTERM))
        ri._durdurma_sinyallerini_geri_al(eskiler)
        for s, isleyici in onceki.items():
            self.assertEqual(isleyici, signal.getsignal(s),
                             "isleyici geri alinmadi (kutuphane hijyeni)")

    def test_4_kurulum_bayragi_SIFIRLAR(self):
        """Onceki kosumdan kalan bayrak yeni kosumu ANINDA bitirmesin."""
        ri.durdurmayi_iste()
        eskiler = ri._durdurma_sinyallerini_kur()
        try:
            self.assertFalse(ri.durdurma_istendi())
        finally:
            ri._durdurma_sinyallerini_geri_al(eskiler)


# ── T204/2 · run_camera: KAMERA HER YOLDA SERBEST BIRAKILIR ─────────────────

class KameraKontrolluDurdurma(DurdurmaBayragiTemiz):
    def _kos(self, kamera, yayinla, *, kareler=None):
        with mock.patch.object(cv2, "VideoCapture", return_value=kamera), \
                mock.patch.object(cv2, "destroyAllWindows"), \
                _algi_sahtesi(yayinla), \
                contextlib.redirect_stdout(io.StringIO()) as cikti:
            if kareler is not None:
                with mock.patch.object(ri, "kamera_kareleri", kareler):
                    ozet = ri.run_camera(
                        SimpleNamespace(predict=lambda *a, **k: [object()]),
                        0.30, canli_olcek=(lambda _w: 0.05),
                        yayinci=object(), ekransiz=True)
            else:
                ozet = ri.run_camera(
                    SimpleNamespace(predict=lambda *a, **k: [object()]),
                    0.30, canli_olcek=(lambda _w: 0.05),
                    yayinci=object(), ekransiz=True)
        return ozet, cikti.getvalue()

    def test_1_GERCEK_SIGTERM_dongusu_kapatir_ve_kamerayi_BIRAKIR(self):
        kamera = SahteKamera(kare=20)
        yayinla = _Yayinla(sinyal_kare=2, gercek_sinyal=True)
        eskiler = ri._durdurma_sinyallerini_kur()
        try:
            ozet, cikti = self._kos(kamera, yayinla)
        finally:
            ri._durdurma_sinyallerini_geri_al(eskiler)
        self.assertEqual(2, len(yayinla.cagrilar),
                         "sinyalden sonra kare islenmeye devam etti")
        self.assertEqual(ri.KAMERA_BITIS_SINYAL, ozet["bitis"])
        self.assertEqual(1, kamera.release_sayisi,
                         "cap.release() kosmadi — finally YOK")
        # Sinyal, `kamera_kareleri` kapisinda ya da `run_camera` kapisinda
        # yakalanabilir (hangisi once gorurse); ikisi de AYNI bitis nedenini
        # yazar. Kilit metin degil, GORUNURLUK ve neden.
        self.assertIn("kontrollu durdurma", cikti.lower())
        self.assertIn(ri.KAMERA_BITIS_SINYAL, cikti)

    def test_2_bayrak_kosum_ONCESINDE_kuruluysa_hic_kare_islenmez(self):
        kamera = SahteKamera(kare=20)
        yayinla = _Yayinla()
        ri.durdurmayi_iste()
        ozet, _ = self._kos(kamera, yayinla)
        self.assertEqual([], yayinla.cagrilar)
        self.assertEqual(ri.KAMERA_BITIS_SINYAL, ozet["bitis"])
        self.assertEqual(1, kamera.release_sayisi)
        self.assertEqual(0, kamera.okuma_sayisi, "sinyalden sonra okuma yapildi")

    def test_3_run_camera_KENDI_kapisiyla_da_durur(self):
        """Uretici sinyali gormezse bile tuketici dongusu durmali.

        `kamera_kareleri` bilerek SINYAL KOR bir sahteyle degistirildi:
        kalan kapi yalniz `run_camera` icindekidir.
        """
        kamera = SahteKamera(kare=20)
        yayinla = _Yayinla(sinyal_kare=2)

        def kor_uretici(cap, ozet, **_k):
            for _ in range(20):
                ozet["okunan"] = ozet.get("okunan", 0) + 1
                yield np.full((360, 640, 3), 127, np.uint8)

        ozet, _ = self._kos(kamera, yayinla, kareler=kor_uretici)
        self.assertEqual(2, len(yayinla.cagrilar))
        self.assertEqual(ri.KAMERA_BITIS_SINYAL, ozet["bitis"])
        self.assertEqual(1, kamera.release_sayisi)

    def test_4_ISTISNA_yolunda_da_kamera_birakilir(self):
        kamera = SahteKamera(kare=20)
        yayinla = _Yayinla()
        with mock.patch.object(cv2, "VideoCapture", return_value=kamera), \
                mock.patch.object(cv2, "destroyAllWindows"), \
                mock.patch.object(ri, "get_masks",
                                  side_effect=RuntimeError("algi coktu")), \
                mock.patch.object(ri, "_karari_yayinla", yayinla), \
                contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(RuntimeError):
                ri.run_camera(SimpleNamespace(predict=lambda *a, **k: [object()]),
                              0.30, canli_olcek=(lambda _w: 0.05),
                              yayinci=object(), ekransiz=True)
        self.assertEqual(1, kamera.release_sayisi,
                         "istisna yolunda cap.release() kosmadi")

    def test_5_KeyboardInterrupt_yolunda_da_kamera_birakilir(self):
        kamera = SahteKamera(kare=20)
        with mock.patch.object(cv2, "VideoCapture", return_value=kamera), \
                mock.patch.object(cv2, "destroyAllWindows"), \
                mock.patch.object(ri, "get_masks",
                                  side_effect=KeyboardInterrupt), \
                contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(KeyboardInterrupt):
                ri.run_camera(SimpleNamespace(predict=lambda *a, **k: [object()]),
                              0.30, canli_olcek=(lambda _w: 0.05),
                              yayinci=object(), ekransiz=True)
        self.assertEqual(1, kamera.release_sayisi)


# ── T204/3 · DUSEN KARE DONGUSU DE SINYALI GORUR ────────────────────────────

class DusenKareDongusuSinyal(DurdurmaBayragiTemiz):
    def test_1_kamera_kopukken_SIGTERM_30_denemeyi_BEKLEMEZ(self):
        """Kusur olsaydi: 30 x KAMERA_DUSEN_KARE_BEKLEME_S boyunca cevapsiz."""
        kamera = SahteKamera(kare=0)          # her okuma dusuyor
        ozet = {}
        beklemeler = []
        ri.durdurmayi_iste()
        uretici = ri.kamera_kareleri(kamera, ozet,
                                     bekle=beklemeler.append, log=lambda *_: None)
        self.assertEqual([], list(uretici))
        self.assertEqual(ri.KAMERA_BITIS_SINYAL, ozet["bitis"])
        self.assertEqual(0, len(beklemeler),
                         "sinyal geldigi halde yeniden deneme beklemesi yapildi")
        self.assertEqual(0, kamera.okuma_sayisi)

    def test_2_sinyal_yokken_T143_davranisi_DEGISMEZ(self):
        kamera = SahteKamera(kare=0)
        ozet = {}
        beklemeler = []
        uretici = ri.kamera_kareleri(kamera, ozet, ust_sinir=3,
                                     bekle=beklemeler.append, log=lambda *_: None)
        self.assertEqual([], list(uretici))
        self.assertEqual(ri.KAMERA_BITIS_DUSEN_KARE, ozet["bitis"])
        self.assertEqual(2, len(beklemeler))   # 3. denemede kontrollu bitis


# ── T204/4 · main(): SIGTERM TELSIZ HALKASINI DA KAPATIR ────────────────────

class MainKontrolluDurdurma(DurdurmaBayragiTemiz):
    def test_1_SIGTERM_yayinciyi_durdurur_ve_kamerayi_birakir(self):
        kamera = SahteKamera(kare=50)
        yayinci = mock.Mock()
        yayinci.heartbeat_aralik = 1.0
        yayinci.hata = []
        yayinci.stop.return_value = True
        sender_modulu = SimpleNamespace(
            yayinci_kur=lambda **_k: SimpleNamespace(start=lambda: yayinci))
        canli = mock.Mock()
        canli.kapat.return_value = True
        canli.okuyucu = SimpleNamespace()
        yayinla = _Yayinla(sinyal_kare=2, gercek_sinyal=True)
        argv = ["rpi_inference.py", "--camera", "--ekransiz",
                "--mavlink", "udp:127.0.0.1:14550", "--mav-sysid", "1",
                "--fov", "60", "--yks-hedef", "127.0.0.1:5005"]
        onceki_sigterm = signal.getsignal(signal.SIGTERM)
        with mock.patch.object(sys, "argv", argv), \
                mock.patch.object(ri.CanliOlcekSaglayici, "baglan",
                                  return_value=canli), \
                mock.patch.object(ri, "_iha_sender_modulu",
                                  return_value=sender_modulu), \
                mock.patch.object(ri, "load_model",
                                  return_value=(
                                      SimpleNamespace(
                                          predict=lambda *a, **k: [object()]),
                                      Path("sahte_model.pt"),
                                      {"durum": "sahte"})), \
                mock.patch.object(cv2, "VideoCapture", return_value=kamera), \
                mock.patch.object(cv2, "destroyAllWindows"), \
                _algi_sahtesi(yayinla), \
                contextlib.redirect_stdout(io.StringIO()):
            ri.main()
        self.assertEqual(2, len(yayinla.cagrilar))
        self.assertEqual(1, kamera.release_sayisi, "kamera birakilmadi")
        self.assertEqual(1, yayinci.stop.call_count, "telsiz yayinci durdurulmadi")
        yayinci.sender.link.close.assert_called_once()
        self.assertEqual(1, canli.kapat.call_count, "MAVLink okuyucu kapatilmadi")
        self.assertEqual(onceki_sigterm, signal.getsignal(signal.SIGTERM),
                         "main() SIGTERM isleyicisini geri almadi")


# ── T205 · SESSIZ OLU YAZICI ────────────────────────────────────────────────

class OluVideoYazici(DurdurmaBayragiTemiz):
    def _run_video(self, yazici, *, ekransiz=True):
        kamera = SahteKamera(kare=3)
        yayinla = _Yayinla()
        with tempfile.TemporaryDirectory() as gecici:
            video = Path(gecici) / "sahne.mp4"
            video.write_bytes(b"")            # yalnizca is_file() kapisi icin
            with mock.patch.object(cv2, "VideoCapture", return_value=kamera), \
                    mock.patch.object(cv2, "VideoWriter", return_value=yazici), \
                    mock.patch.object(cv2, "destroyAllWindows"), \
                    _algi_sahtesi(yayinla) as draw, \
                    contextlib.redirect_stdout(io.StringIO()) as cikti, \
                    contextlib.redirect_stderr(io.StringIO()) as hata:
                ri.run_video(
                    SimpleNamespace(predict=lambda *a, **k: [object()]),
                    str(video), 0.30, save=True, mpp=0.05, ekransiz=ekransiz)
        return yayinla, draw, cikti.getvalue(), hata.getvalue(), kamera

    def test_1_acilamayan_yazici_GORUNUR_sekilde_basarisiz(self):
        yazici = SahteYazici(acik=False)
        _, draw, cikti, hata, _ = self._run_video(yazici)
        self.assertIn("KIRMIZI", hata)
        self.assertIn("VideoWriter ACILAMADI", hata)
        self.assertEqual(0, yazici.yazilan,
                         "OLU yaziciya kare yazildi — kayit sessizce kayboldu")
        self.assertNotIn("Kaydedildi:", cikti,
                         "kaydedilmemis dosya icin 'Kaydedildi:' YALANI basildi")
        self.assertIn("kayit yok", cikti)
        self.assertEqual(0, draw.call_count,
                         "ekransiz + kayitsiz kosumda gorsel uretildi")

    def test_2_saglam_yazici_HER_KAREYI_yazar(self):
        yazici = SahteYazici(acik=True)
        yayinla, draw, cikti, hata, _ = self._run_video(yazici)
        self.assertEqual(3, yazici.yazilan)
        self.assertEqual(3, draw.call_count)
        self.assertIn("Kaydedildi:", cikti)
        self.assertNotIn("KIRMIZI", hata)

    def test_3_KARAR_YOLU_olu_yazicida_DEGISMEZ(self):
        """madde 15: kayit kipinin kapanmasi karar/yayin yolunu ETKILEMEZ."""
        olu, _, _, _, _ = self._run_video(SahteYazici(acik=False))
        saglam, _, _, _, _ = self._run_video(SahteYazici(acik=True))
        self.assertEqual(3, len(saglam.cagrilar))
        self.assertEqual(saglam.cagrilar, olu.cagrilar,
                         "olu yazici karar yayinini degistirdi")

    def test_4_kamera_ve_yazici_HER_YOLDA_birakilir(self):
        yazici = SahteYazici(acik=True)
        _, _, _, _, kamera = self._run_video(yazici)
        self.assertEqual(1, kamera.release_sayisi)
        self.assertEqual(1, yazici.release_sayisi)

    def test_5_video_dongusu_de_SIGTERM_ile_kapanir(self):
        yazici = SahteYazici(acik=True)
        kamera = SahteKamera(kare=20)
        yayinla = _Yayinla(sinyal_kare=2, gercek_sinyal=True)
        eskiler = ri._durdurma_sinyallerini_kur()
        try:
            with tempfile.TemporaryDirectory() as gecici:
                video = Path(gecici) / "sahne.mp4"
                video.write_bytes(b"")
                with mock.patch.object(cv2, "VideoCapture", return_value=kamera), \
                        mock.patch.object(cv2, "VideoWriter", return_value=yazici), \
                        mock.patch.object(cv2, "destroyAllWindows"), \
                        _algi_sahtesi(yayinla), \
                        contextlib.redirect_stdout(io.StringIO()) as cikti:
                    ri.run_video(
                        SimpleNamespace(predict=lambda *a, **k: [object()]),
                        str(video), 0.30, save=True, mpp=0.05, ekransiz=True)
        finally:
            ri._durdurma_sinyallerini_geri_al(eskiler)
        self.assertEqual(2, len(yayinla.cagrilar))
        self.assertEqual(1, kamera.release_sayisi)
        self.assertEqual(1, yazici.release_sayisi)
        self.assertIn("KONTROLLU DURDURMA", cikti.getvalue())

    def test_6_ilk_kareden_once_durdurma_COKMEZ(self):
        """fps_buf bos kalir; eski kuyruk satiri ZeroDivisionError veriyordu."""
        yazici = SahteYazici(acik=True)
        kamera = SahteKamera(kare=20)
        ri.durdurmayi_iste()
        with tempfile.TemporaryDirectory() as gecici:
            video = Path(gecici) / "sahne.mp4"
            video.write_bytes(b"")
            with mock.patch.object(cv2, "VideoCapture", return_value=kamera), \
                    mock.patch.object(cv2, "VideoWriter", return_value=yazici), \
                    mock.patch.object(cv2, "destroyAllWindows"), \
                    _algi_sahtesi(_Yayinla()), \
                    contextlib.redirect_stdout(io.StringIO()) as cikti:
                ri.run_video(
                    SimpleNamespace(predict=lambda *a, **k: [object()]),
                    str(video), 0.30, save=True, mpp=0.05, ekransiz=True)
        self.assertIn("0 kare islendi", cikti.getvalue())
        self.assertEqual(1, kamera.release_sayisi)


if __name__ == "__main__":
    unittest.main()
