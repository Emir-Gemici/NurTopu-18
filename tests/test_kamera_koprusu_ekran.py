"""Kamera koprusu EKRAN hatti nobetcisi (21 Eyl 2026).

Kullanici karari: kamera fiziksel olarak 90° yan monte ve montaj DEGISTIRILEMEZ.
Iki ayri goruntu hatti:
    MODEL  : /video, /kare.jpg  -> dondurulmus 720x1280, TAM FOV  (dokunulmaz)
    EKRAN  : /ekran, /ekran.jpg -> 1280x720 yatay, yazilar duz, ekrani doldurur
Tam FOV + bozulmamis oran + 16:9 doldurma ayni anda mumkun olmadigi icin ekran
hatti ORTADAN KIRPAR; bu kirpma model hesabina (FOV, mpp, koordinat, tespit) KARISMAZ.

Kilitlenenler:
  E1 720x1280 -> 1280x720 (yatay).
  E2 ORAN KORUNUR: kare bir isaret ekranda da kare kalir (esnetme YOK), olcek 1280/720.
  E3 ORTADAN kirpar: merkezdeki isaret merkezde kalir; ust/alt kenardaki isaretler kirpilir.
  E4 zaten 16:9 olan kare aynen gecer.
  E5 MODEL HATTI BAYT-ES: /kare.jpg ureticinin JPEG'iyle birebir; boyut 720x1280.
  E6 uctan uca: /ekran.jpg ve /ekran akisi 1280x720; /durum ekran_url tasir.
  E7 ekran istemcisi model sayacini (istemci_sayisi) KIRLETMEZ.
"""

import json
import sys
import tempfile
import threading
import time
import unittest
import urllib.request
from pathlib import Path

import cv2
import numpy as np

KOK = Path(__file__).resolve().parents[1]
for _y in (KOK / "scripts", KOK / "codes"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

import kamera_koprusu as kk  # noqa: E402


def _dikey_kare():
    """720x1280 (dondurulmus model karesi); merkezde 100x100 beyaz kare,
    ust ve alt kenarda (kirpilacak bolgede) gri seritler."""
    k = np.zeros((1280, 720, 3), np.uint8)
    k[590:690, 310:410] = 255              # merkez: 100x100
    k[0:60, :] = 128                       # ust kenar (kirpilmali)
    k[1220:1280, :] = 128                  # alt kenar (kirpilmali)
    return k


def _beyaz_kutu(k):
    g = cv2.cvtColor(k, cv2.COLOR_BGR2GRAY)
    ys, xs = np.where(g > 200)
    return xs.min(), ys.min(), xs.max() - xs.min() + 1, ys.max() - ys.min() + 1


class E1Boyut(unittest.TestCase):
    def test_dikey_yataya_doner(self):
        self.assertEqual((720, 1280), kk.ekran_karesi(_dikey_kare()).shape[:2])


class E2OranKorunur(unittest.TestCase):
    def test_kare_isaret_kare_kalir(self):
        x, y, w, h = _beyaz_kutu(kk.ekran_karesi(_dikey_kare()))
        self.assertLess(abs(w - h), 4, (w, h))          # esnetme yok
        beklenen = 100 * 1280 / 720.0                    # ~177.8 px
        self.assertLess(abs(w - beklenen), 4, w)


class E3OrtadanKirpar(unittest.TestCase):
    def test_merkez_merkezde_kalir(self):
        x, y, w, h = _beyaz_kutu(kk.ekran_karesi(_dikey_kare()))
        self.assertLess(abs((x + w / 2.0) - 640), 3)
        self.assertLess(abs((y + h / 2.0) - 360), 3)

    def test_ust_ve_alt_kenar_kirpilir(self):
        e = cv2.cvtColor(kk.ekran_karesi(_dikey_kare()), cv2.COLOR_BGR2GRAY)
        self.assertLess(e[:10, :].mean(), 5)             # gri ust serit yok
        self.assertLess(e[-10:, :].mean(), 5)            # gri alt serit yok


class E4ZatenYatay(unittest.TestCase):
    def test_16_9_kare_aynen_gecer(self):
        k = np.random.RandomState(0).randint(0, 255, (720, 1280, 3)).astype(np.uint8)
        self.assertTrue(np.array_equal(k, kk.ekran_karesi(k)))


class _Kopru(unittest.TestCase):
    """Sahte AVI (320x180) -> kopru(dondur=90) -> gercek HTTP. Mock yok."""

    @classmethod
    def setUpClass(cls):
        cls._dizin = tempfile.TemporaryDirectory()
        yol = Path(cls._dizin.name) / "k.avi"
        y = cv2.VideoWriter(str(yol), cv2.VideoWriter_fourcc(*"MJPG"), 10.0, (320, 180))
        if not y.isOpened():
            raise unittest.SkipTest("YAPILAMADI: cv2.VideoWriter MJPG acilamadi")
        for i in range(60):
            k = np.zeros((180, 320, 3), np.uint8)
            k[70:110, 140:180] = 255
            k[0:4, 0:4] = i
            y.write(k)
        y.release()
        cls.sunucu, cls.uretici = kk.kopru_kur(str(yol), port=0, dondur=90,
                                               log=lambda *a, **kw: None)
        threading.Thread(target=cls.sunucu.serve_forever,
                         kwargs={"poll_interval": 0.1}, daemon=True).start()
        cls.port = cls.sunucu.server_address[1]
        son = time.monotonic() + 8.0
        while time.monotonic() < son and cls.uretici.durum()["kare_sayaci"] == 0:
            time.sleep(0.05)

    @classmethod
    def tearDownClass(cls):
        kk.kopru_kapat(cls.sunucu, cls.uretici)
        cls._dizin.cleanup()

    def _al(self, yol):
        with urllib.request.urlopen("http://127.0.0.1:{}{}".format(self.port, yol),
                                    timeout=5) as c:
            return c.read(), c.headers


class E5ModelHattiBaytEs(_Kopru):
    def test_kare_jpg_ureticinin_jpegiyle_birebir(self):
        govde, baslik = self._al(kk.KARE_YOLU)
        sira = int(baslik["X-Kare-Sira"])
        with self.uretici.kilit:
            ayni_sira = self.uretici.sira == sira
            jpeg = self.uretici.jpeg
        if ayni_sira:
            self.assertEqual(jpeg, govde)
        k = cv2.imdecode(np.frombuffer(govde, np.uint8), cv2.IMREAD_COLOR)
        self.assertEqual((320, 180), k.shape[:2])        # dondurulmus, dikey


class E6UctanUca(_Kopru):
    def test_ekran_jpg_yatay(self):
        govde, _b = self._al(kk.EKRAN_KARE_YOLU)
        k = cv2.imdecode(np.frombuffer(govde, np.uint8), cv2.IMREAD_COLOR)
        self.assertEqual((720, 1280), k.shape[:2])

    def test_ekran_akisi_yatay(self):
        c = urllib.request.urlopen("http://127.0.0.1:{}{}".format(self.port, kk.EKRAN_YOLU),
                                   timeout=5)
        try:
            tampon = b""
            son = time.monotonic() + 5.0
            while time.monotonic() < son and tampon.count(b"\xff\xd9") < 1:
                tampon += c.read(8192)
            bas = tampon.index(b"\xff\xd8")
            bit = tampon.index(b"\xff\xd9", bas) + 2
            k = cv2.imdecode(np.frombuffer(tampon[bas:bit], np.uint8), cv2.IMREAD_COLOR)
            self.assertEqual((720, 1280), k.shape[:2])
        finally:
            c.close()

    def test_durum_ekran_url_tasir(self):
        govde, _b = self._al(kk.DURUM_YOLU)
        d = json.loads(govde.decode())
        self.assertTrue(d["ekran_url"].endswith(kk.EKRAN_YOLU))
        self.assertEqual([1280, 720], d["ekran_boyut"])
        self.assertEqual([180, 320], d["boyut"])          # model hatti dikey kalir


class E7SayacKirlenmez(_Kopru):
    def test_ekran_istemcisi_model_sayacina_girmez(self):
        once = self.uretici.durum()["istemci_sayisi"]
        c = urllib.request.urlopen("http://127.0.0.1:{}{}".format(self.port, kk.EKRAN_YOLU),
                                   timeout=5)
        try:
            c.read(4096)
            time.sleep(0.2)
            self.assertEqual(once, self.uretici.durum()["istemci_sayisi"])
        finally:
            c.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
