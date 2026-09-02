"""NEDEN: YKİ canlı kamera istemcisi ağ kesilince donmuş kareyi canlı
göstermemeli ve Tk/komut döngüsünü ağ I/O'sunda bekletmemelidir.

Gerçek dosyalara veya SiK'e dokunmadan yerel bir HTTP köprüsüyle sınanır.
"""
import json
import sys
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import cv2
import numpy as np


KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "comms"))
import kamera_istemci as ki  # noqa: E402


def _bekle(kosul, tavan_s=3.0):
    son = time.monotonic() + tavan_s
    while time.monotonic() < son:
        deger = kosul()
        if deger:
            return deger
        time.sleep(0.01)
    return None


class _Kaynak:
    def __init__(self):
        self.kilit = threading.Lock()
        self.kare_http = 200
        self.durum_http = 200
        self.kaynak_acik = True
        self.dondur = False
        self.kare_gecikme_s = 0.0
        self.sira = 0
        self.jpeg = self._jpeg(0)

    @staticmethod
    def _jpeg(sira):
        kare = np.zeros((24, 32, 3), dtype=np.uint8)
        kare[:, :, :] = ((sira * 17) % 255, 80, 160)
        ok, tampon = cv2.imencode(".jpg", kare)
        if not ok:
            raise RuntimeError("test JPEG kodlanamadi")
        return tampon.tobytes()

    def kare(self):
        with self.kilit:
            gecikme = self.kare_gecikme_s
        if gecikme:
            time.sleep(gecikme)
        with self.kilit:
            if not self.dondur:
                self.sira += 1
                self.jpeg = self._jpeg(self.sira)
            return self.kare_http, self.sira, self.jpeg

    def durum(self):
        with self.kilit:
            return self.durum_http, {
                "kaynak_acik": self.kaynak_acik,
                "kaynak": "sahte-csi",
                "kare_sayaci": self.sira,
                "son_hata": None if self.kaynak_acik else "CSI KOPTU",
            }


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, _bicim, *_args):
        pass

    def do_GET(self):
        if self.path == ki.KARE_YOLU:
            kod, sira, govde = self.server.kaynak.kare()
            self.send_response(kod)
            self.send_header("Content-Type", "image/jpeg")
            self.send_header("Content-Length", str(len(govde)))
            self.send_header("X-Kare-Sira", str(sira))
            self.end_headers()
            try:
                self.wfile.write(govde)
            except OSError:
                pass
            return
        if self.path == ki.DURUM_YOLU:
            kod, veri = self.server.kaynak.durum()
            govde = json.dumps(veri).encode("utf-8")
            self.send_response(kod)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(govde)))
            self.end_headers()
            self.wfile.write(govde)
            return
        self.send_error(404)


class _Kopru:
    def __init__(self):
        self.kaynak = _Kaynak()
        self.sunucu = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        self.sunucu.kaynak = self.kaynak
        self.iplik = threading.Thread(target=self.sunucu.serve_forever, daemon=True)
        self.iplik.start()

    @property
    def url(self):
        return "http://127.0.0.1:{}{}".format(
            self.sunucu.server_address[1], ki.KARE_YOLU)

    @property
    def kok_url(self):
        return "http://127.0.0.1:{}".format(self.sunucu.server_address[1])

    def kapat(self):
        self.sunucu.shutdown()
        self.sunucu.server_close()
        self.iplik.join(2.0)


class YksKameraIstemciTesti(unittest.TestCase):
    def setUp(self):
        self.kopru = _Kopru()
        self.istemci = ki.KameraIstemci(
            self.kopru.url,
            kare_araligi_s=0.03,
            durum_araligi_s=0.04,
            istek_zaman_asimi_s=0.2,
            kare_tazelik_s=0.14,
            durum_tazelik_s=0.14)

    def tearDown(self):
        self.istemci.durdur()
        self.kopru.kapat()

    def test_api_snapshot_alanlari_ve_baslat_nonblocking(self):
        ilk = self.istemci.snapshot()
        self.assertEqual(
            {"surum", "jpeg", "durum", "hata", "kare_yasi_s", "kaynak"}
            - set(ilk), set())
        self.assertIsNone(ilk["jpeg"])

        t0 = time.monotonic()
        self.assertTrue(self.istemci.baslat())
        self.assertLess(time.monotonic() - t0, 0.1, "baslat ağ I/O'sunda bekledi")
        self.assertFalse(self.istemci.baslat(), "ikinci baslat yeni worker acmamali")

        canli = _bekle(lambda: self.istemci.snapshot()
                       if self.istemci.snapshot()["durum"] == ki.DURUM_CANLI else None)
        self.assertIsNotNone(canli)
        self.assertIsInstance(canli["jpeg"], bytes)
        self.assertGreater(canli["surum"], 0)
        self.assertEqual(canli["kaynak"], self.kopru.url)
        self.assertFalse(canli["kare"].flags.writeable)

    def test_http_503_eski_jpegi_hemen_gizler_ve_yeniden_baglanir(self):
        self.istemci.baslat()
        canli = _bekle(lambda: self.istemci.snapshot()
                       if self.istemci.snapshot()["jpeg"] is not None else None)
        self.assertIsNotNone(canli)
        onceki_surum = canli["surum"]

        with self.kopru.kaynak.kilit:
            self.kopru.kaynak.kare_http = 503
        dustu = _bekle(lambda: self.istemci.snapshot()
                       if self.istemci.snapshot()["jpeg"] is None and
                       "HTTP 503" in (self.istemci.snapshot()["hata"] or "") else None)
        self.assertIsNotNone(dustu, "503'te eski JPEG gorunur kaldi")

        with self.kopru.kaynak.kilit:
            self.kopru.kaynak.kare_http = 200
        dondu = _bekle(lambda: self.istemci.snapshot()
                       if self.istemci.snapshot()["jpeg"] is not None and
                       self.istemci.snapshot()["surum"] > onceki_surum else None)
        self.assertIsNotNone(dondu, "baglanti geri gelince istemci toparlanmadi")

    def test_timeout_eski_jpegi_gizler_ve_yeniden_baglanir(self):
        self.istemci.baslat()
        self.assertIsNotNone(_bekle(lambda: self.istemci.snapshot()["jpeg"]))
        with self.kopru.kaynak.kilit:
            self.kopru.kaynak.kare_gecikme_s = 0.35
        dustu = _bekle(lambda: self.istemci.snapshot()
                       if self.istemci.snapshot()["jpeg"] is None and
                       self.istemci.snapshot()["hata"] else None)
        self.assertIsNotNone(dustu, "timeout'ta eski JPEG gorunur kaldi")

        with self.kopru.kaynak.kilit:
            self.kopru.kaynak.kare_gecikme_s = 0.0
        self.assertIsNotNone(
            _bekle(lambda: self.istemci.snapshot()
                   if self.istemci.snapshot()["jpeg"] is not None else None),
            "timeout kalkınca istemci toparlanmadı")

    def test_ayni_kare_tekrari_tazeligi_yenilemez(self):
        self.istemci.baslat()
        self.assertIsNotNone(_bekle(lambda: self.istemci.snapshot()["jpeg"]))
        with self.kopru.kaynak.kilit:
            self.kopru.kaynak.dondur = True
        bayat = _bekle(lambda: self.istemci.snapshot()
                       if self.istemci.snapshot()["durum"] == ki.DURUM_KARE_BAYAT else None,
                       tavan_s=2.0)
        self.assertIsNotNone(bayat)
        self.assertIsNone(bayat["jpeg"], "donmus kare canliymis gibi gosterildi")
        self.assertGreater(bayat["kare_istek"], 2, "bayatlik ag kesilmesiyle karismis olabilir")

    def test_durum_kaynak_kapali_jpegi_gizler(self):
        self.istemci.baslat()
        self.assertIsNotNone(_bekle(lambda: self.istemci.snapshot()["jpeg"]))
        with self.kopru.kaynak.kilit:
            self.kopru.kaynak.kaynak_acik = False
        kapali = _bekle(lambda: self.istemci.snapshot()
                        if self.istemci.snapshot()["durum"] == ki.DURUM_KAYNAK_KAPALI
                        else None)
        self.assertIsNotNone(kapali)
        self.assertIsNone(kapali["jpeg"])
        self.assertIn("CSI KOPTU", kapali["hata"])

    def test_url_sozlesmesi_ayni_kopru_ve_routable_hedef(self):
        kare, durum = ki.kamera_uclari("http://10.42.0.2:8080/kare.jpg")
        self.assertEqual(kare, "http://10.42.0.2:8080/kare.jpg")
        self.assertEqual(durum, "http://10.42.0.2:8080/durum")
        for kok in ("http://10.42.0.2:8080", "http://10.42.0.2:8080/"):
            with self.subTest(kok=kok):
                istemci = ki.KameraIstemci(kok)
                self.assertEqual(istemci.kare_url,
                                 "http://10.42.0.2:8080/kare.jpg")
                self.assertEqual(istemci.durum_url,
                                 "http://10.42.0.2:8080/durum")
                self.assertEqual(istemci.snapshot()["kaynak"],
                                 "http://10.42.0.2:8080/kare.jpg")
        for kotu in (
                "http://0.0.0.0:8080/kare.jpg",
                "file:///tmp/kare.jpg",
                "http://x:8080/video",
                "http://kullanici:sifre@x:8080/kare.jpg",
                "http://x:8080/kare.jpg?q=1"):
            with self.subTest(url=kotu), self.assertRaises(ki.KameraURLHatasi):
                ki.KameraIstemci(kotu)
        with self.assertRaises(ki.KameraURLHatasi):
            ki.KameraIstemci(
                "http://10.42.0.2:8080/kare.jpg",
                "http://10.42.0.3:8080/durum")

    def test_yks_kok_urlsi_gercekten_kare_ve_durum_okur(self):
        istemci = ki.KameraIstemci(
            self.kopru.kok_url,
            kare_araligi_s=0.03,
            durum_araligi_s=0.04,
            istek_zaman_asimi_s=0.2,
            kare_tazelik_s=0.14,
            durum_tazelik_s=0.14)
        try:
            istemci.baslat()
            canli = _bekle(lambda: istemci.snapshot()
                           if istemci.snapshot()["durum"] == ki.DURUM_CANLI else None)
            self.assertIsNotNone(canli)
            self.assertEqual(canli["kaynak"], self.kopru.kok_url + "/kare.jpg")
        finally:
            istemci.durdur()


if __name__ == "__main__":
    unittest.main()
