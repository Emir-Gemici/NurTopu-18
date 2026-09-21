"""Kamera koprusu `--dondur` nobetcisi (21 Eyl 2026, saha montaj duzeltmesi).

Kullanici canli videoda gordu: yaka kartinin yazisi SOLDA duruyordu, USTTE olmaliydi
(sol -> ust = saat yonunde 90°). Duzeltme koprude, kare JPEG'e basilmadan HEMEN ONCE
yapilir; boylece ayni kareyi goren herkes (hakem ekrani, rpi_inference, kayit)
ayni yonu gorur.

Kilitlenenler:
  D1 `kare_dondur` yonu: SOLDAKI isaret 90'da USTE, 270'te ALTA, 180'de SAGA gider.
  D2 0 derece BAYT-ES: ayni nesne doner, uretilen JPEG eski davranisla birebir.
  D3 90'da en/boy yer degistirir ve /durum `boyut` + `dondur` bunu DURUSTCE soyler.
  D4 gecersiz aci (45) hem yapicida hem argparse'ta REDDEDILIR — sessiz yok sayma yok.
  D5 `_cozunurluk_eslesti` kamera kipi istegini dondurme ONCESI boyutla kiyaslar
     (1280x720 istegi + 90 derece -> sunulan 720x1280 "eslesti" sayilir).
  D6 UCTAN UCA (mock yok): sahte AVI -> kopru(dondur=90) -> HTTP /kare.jpg -> isaret ustte.
  D7 ayna: jetson_paket/kod/kamera_koprusu.py kanonikle bayt-es.
"""

import sys
import tempfile
import time
import unittest
import urllib.request
import json
from pathlib import Path

import cv2
import numpy as np

KOK = Path(__file__).resolve().parents[1]
for _y in (KOK / "scripts", KOK / "codes"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

import kamera_koprusu as kk  # noqa: E402

W, H = 320, 180


def _isaretli_kare():
    """Siyah kare; SOL kenarin ortasinda beyaz blok (yonu okumak icin)."""
    k = np.zeros((H, W, 3), np.uint8)
    k[H // 2 - 20:H // 2 + 20, 0:40] = 255
    return k


def _parlak_kenar(k):
    """Beyaz blok hangi kenara dayali: 'sol'/'sag'/'ust'/'alt'."""
    g = k if k.ndim == 2 else cv2.cvtColor(k, cv2.COLOR_BGR2GRAY)
    h, w = g.shape
    b = 30
    ortalamalar = {"sol": g[:, :b].mean(), "sag": g[:, w - b:].mean(),
                   "ust": g[:b, :].mean(), "alt": g[h - b:, :].mean()}
    return max(ortalamalar, key=ortalamalar.get)


class D1Yon(unittest.TestCase):
    def test_referans_isaret_solda(self):
        self.assertEqual("sol", _parlak_kenar(_isaretli_kare()))

    def test_90_sol_usta_gider(self):
        r = kk.kare_dondur(_isaretli_kare(), 90)
        self.assertEqual((W, H), r.shape[:2])
        self.assertEqual("ust", _parlak_kenar(r))

    def test_180_sol_saga_gider(self):
        self.assertEqual("sag", _parlak_kenar(kk.kare_dondur(_isaretli_kare(), 180)))

    def test_270_sol_alta_gider(self):
        self.assertEqual("alt", _parlak_kenar(kk.kare_dondur(_isaretli_kare(), 270)))


class D2SifirBaytEs(unittest.TestCase):
    def test_sifir_ayni_nesne(self):
        k = _isaretli_kare()
        self.assertIs(k, kk.kare_dondur(k, 0))

    def test_sifir_jpeg_eski_davranisla_birebir(self):
        k = _isaretli_kare()
        u = kk.KareUretici("0", log=lambda *a, **kw: None)
        u._kare_yayinla(k)
        ok, beklenen = cv2.imencode(".jpg", k, [int(cv2.IMWRITE_JPEG_QUALITY), u.kalite])
        self.assertTrue(ok)
        self.assertEqual(beklenen.tobytes(), u.jpeg)


class D3DurumDurust(unittest.TestCase):
    def test_90_boyut_ve_dondur_raporlanir(self):
        u = kk.KareUretici("0", dondur=90, log=lambda *a, **kw: None)
        u._kare_yayinla(_isaretli_kare())
        d = u.durum()
        self.assertEqual([H, W], d["boyut"])       # 320x180 -> 180x320
        self.assertEqual(90, d["dondur"])

    def test_varsayilan_dondur_sifir_ve_boyut_aynen(self):
        u = kk.KareUretici("0", log=lambda *a, **kw: None)
        u._kare_yayinla(_isaretli_kare())
        d = u.durum()
        self.assertEqual([W, H], d["boyut"])
        self.assertEqual(0, d["dondur"])


class D4GecersizAciRed(unittest.TestCase):
    def test_yapici_45_reddeder(self):
        with self.assertRaises(ValueError):
            kk.KareUretici("0", dondur=45, log=lambda *a, **kw: None)

    def test_argparse_45_reddeder(self):
        with self.assertRaises(SystemExit):
            kk._parser().parse_args(["--dondur", "45"])

    def test_argparse_90_kabul(self):
        self.assertEqual(90, kk._parser().parse_args(["--dondur", "90"]).dondur)
        self.assertEqual(0, kk._parser().parse_args([]).dondur)


class D5CozunurlukEslesmesi(unittest.TestCase):
    def test_1280x720_istegi_90_derecede_eslesti(self):
        u = kk.KareUretici("0", dondur=90, genislik=1280, yukseklik=720,
                           log=lambda *a, **kw: None)
        u._kare_yayinla(np.zeros((720, 1280, 3), np.uint8) + 7)
        with u.kilit:
            self.assertTrue(u._cozunurluk_eslesti())

    def test_dondurmesiz_ayni_istek_eslesti(self):
        u = kk.KareUretici("0", genislik=1280, yukseklik=720, log=lambda *a, **kw: None)
        u._kare_yayinla(np.zeros((720, 1280, 3), np.uint8) + 7)
        with u.kilit:
            self.assertTrue(u._cozunurluk_eslesti())


class D6UctanUca(unittest.TestCase):
    def test_sahte_avi_kopru_90_http_kare_isaret_ustte(self):
        with tempfile.TemporaryDirectory() as d:
            yol = Path(d) / "isaretli.avi"
            yazici = cv2.VideoWriter(str(yol), cv2.VideoWriter_fourcc(*"MJPG"), 10.0, (W, H))
            if not yazici.isOpened():
                self.skipTest("YAPILAMADI: cv2.VideoWriter MJPG acilamadi")
            for i in range(40):
                k = _isaretli_kare()
                k[0:4, 0:4] = i          # her kare farkli (donuk kare korumasi)
                yazici.write(k)
            yazici.release()
            sunucu, uretici = kk.kopru_kur(str(yol), port=0, dondur=90,
                                           log=lambda *a, **kw: None)
            import threading
            threading.Thread(target=sunucu.serve_forever, kwargs={"poll_interval": 0.1},
                             daemon=True).start()
            port = sunucu.server_address[1]
            try:
                son = time.monotonic() + 8.0
                durum = None
                while time.monotonic() < son:
                    with urllib.request.urlopen(
                            "http://127.0.0.1:{}/durum".format(port), timeout=3) as c:
                        durum = json.loads(c.read().decode())
                    if durum.get("kare_sayaci", 0) > 0:
                        break
                    time.sleep(0.1)
                self.assertTrue(durum and durum["kare_sayaci"] > 0, durum)
                self.assertEqual([H, W], durum["boyut"])
                self.assertEqual(90, durum["dondur"])
                with urllib.request.urlopen(
                        "http://127.0.0.1:{}/kare.jpg".format(port), timeout=3) as c:
                    kare = cv2.imdecode(np.frombuffer(c.read(), np.uint8), cv2.IMREAD_COLOR)
                self.assertEqual((W, H), kare.shape[:2])
                self.assertEqual("ust", _parlak_kenar(kare))
            finally:
                kk.kopru_kapat(sunucu, uretici)


class D7Ayna(unittest.TestCase):
    def test_jetson_paket_aynasi_bayt_es(self):
        kanonik = (KOK / "scripts" / "kamera_koprusu.py").read_bytes().replace(b"\r\n", b"\n")
        ayna = (KOK / "jetson_paket" / "kod" / "kamera_koprusu.py").read_bytes().replace(
            b"\r\n", b"\n")
        self.assertEqual(kanonik, ayna)


if __name__ == "__main__":
    unittest.main(verbosity=2)
