"""FAZ B · GOREV K — KAMERA KOPRUSU KAPILARI (scripts/kamera_koprusu.py · jetson_paket/kod aynasi).

NEDEN (SAHA_HAZIRLIK_PLANI_20260903.md §1.4 · §0.2): Jetson Nano'da RPi HQ (IMX477, CSI)
yalniz GStreamer nvarguscamerasrc ile okunur; GStreamer'li OpenCV yalniz SISTEM Python
3.6'da var. rpi_inference (ultralytics, Python >= 3.8 venv, GStreamer'siz opencv) kamerayi
dogrudan acamaz. Kopru: sistem Python'da kare -> JPEG -> http://127.0.0.1:8080/video
(multipart MJPEG, DroidCam kalibi); rpi_inference --kaynak http://... bunu okur.
Nano cumartesi geliyor: kopru burada GERCEK bilesenlerle (gercek HTTP sunucu, gercek
cv2.VideoCapture FFmpeg okuyucu, gercek rpi_inference.kamera_kareleri) PC'de SAHTE
kaynakla (gecici MJPG AVI, 30 kare) kilitlenir. Mock yok. nvarguscamerasrc borusu PC'de
ACILAMAZ (GStreamer yok) — o yol yalniz metin olarak kilitlenir; gercek olcum cumartesi.

Kapilar:
  K1 sahte kaynak -> kopru -> PC'de cv2.VideoCapture("http://127.0.0.1:<port>/video")
     >= 5 kare; boyut/dtype dogru; kareler DEGISIYOR (ayni kare iki kez yayinlanmaz)
  K2 /durum JSON alanlari (kaynak_acik, kare_sayaci, fps, son_hata, boyut, port, video_url ...);
     /kare.jpg tek taze kare; bilinmeyen yol 404
  K3 kaynak YOKKEN kopru AYAKTA: /durum 200 + kaynak_acik:false + son_hata; yeniden acma
     ~1 s'de bir SAYILIR (mesgul dongu yok); /video ve /kare.jpg 503 (bayat/sahte kare YOK);
     KIRMIZI log; kaynak SONRADAN gelince kendiliginden acilir (fail-visible, cokme yok)
  K4 rpi_inference.kamera_kaynagi_coz("http://...") ile uyum: cozum ayni str; URETIM
     jeneratoru kamera_kareleri(cap, ozet) kopruden kare uretir, ozet["okunan"] artar
  K5 Python 3.6 uyumu (ast): walrus / posonly / `from __future__ import annotations` /
     match / builtin-generic tip yok; yalniz stdlib + cv2 + numpy; 3.7+ API adlari
     (ThreadingHTTPServer, removeprefix/removesuffix) kodda yok; kod/ aynasi kanonikle
     bayt-es; kaynak cozumu ve nvargus boru metni
  K6 CLI (systemd'nin kostugu yol): `--kaynak <avi> --port 0` "dinliyor http://..." basar,
     /durum cevap verir; gecersiz --kalite -> cikis 2 (fail-closed)
"""
import ast
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

import cv2
import numpy as np

KOK = Path(__file__).resolve().parents[1]
for _y in (KOK / "scripts", KOK / "codes", KOK / "comms"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

import kamera_koprusu as kk  # noqa: E402

KANONIK = KOK / "scripts" / "kamera_koprusu.py"
AYNA = KOK / "jetson_paket" / "kod" / "kamera_koprusu.py"
KARE_SAYISI = 30
BOYUT = (320, 240)          # (genislik, yukseklik)
KIRMIZI_KANAL_SABITI = 40   # sahte karelerde B,G,R'nin R'si sabit: icerik gercekten dosyadan mi?
TAVAN_S = 8.0


def _sahte_avi(dizin, ad="sahte.avi", n=KARE_SAYISI, boyut=BOYUT):
    """cv2.VideoWriter ile n kareli MJPG AVI; her kare farkli (mavi kanal i*8)."""
    yol = Path(dizin) / ad
    w = cv2.VideoWriter(str(yol), cv2.VideoWriter_fourcc(*"MJPG"), 10.0, boyut)
    if not w.isOpened():
        raise unittest.SkipTest("YAPILAMADI: cv2.VideoWriter MJPG acilamadi (FFmpeg yok?)")
    for i in range(n):
        k = np.zeros((boyut[1], boyut[0], 3), np.uint8)
        k[:, :, 0] = (i * 8) % 256
        k[:, :, 1] = 255 - (i * 8) % 256
        k[:, :, 2] = KIRMIZI_KANAL_SABITI
        cv2.putText(k, str(i), (20, boyut[1] // 2), cv2.FONT_HERSHEY_SIMPLEX, 2,
                    (255, 255, 255), 3)
        w.write(k)
    w.release()
    if not yol.is_file() or yol.stat().st_size == 0:
        raise unittest.SkipTest("YAPILAMADI: sahte AVI yazilamadi")
    return yol


def _http(port, yol, zaman_asimi=5.0):
    """GET -> (kod, basliklar, govde). HTTPError de (kod, ...) olarak doner."""
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}{yol}", timeout=zaman_asimi) as r:
            return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()


def _durum(port):
    kod, _, govde = _http(port, kk.DURUM_YOLU)
    return kod, json.loads(govde.decode("utf-8"))


def _bekle(kosul, tavan_s=TAVAN_S, adim_s=0.05):
    bitis = time.monotonic() + tavan_s
    while time.monotonic() < bitis:
        if kosul():
            return True
        time.sleep(adim_s)
    return kosul()


class _KopruTesti(unittest.TestCase):
    """Gercek kopru: efemer port, arka planda serve_forever; kapanis addCleanup ile."""

    def _kopru(self, kaynak, **kw):
        loglar = []

        def log(metin, kirmizi=False):
            loglar.append((kirmizi, metin))

        sunucu, uretici = kk.kopru_kur(str(kaynak), port=0, log_aralik_s=0, log=log, **kw)
        iplik = threading.Thread(target=sunucu.serve_forever,
                                 kwargs={"poll_interval": 0.05}, daemon=True)
        iplik.start()
        self.addCleanup(kk.kopru_kapat, sunucu, uretici)
        return sunucu.server_address[1], uretici, loglar

    def _sahte_kaynakli_kopru(self):
        dizin = tempfile.TemporaryDirectory()
        self.addCleanup(dizin.cleanup)          # LIFO: kopru kapandiktan SONRA silinir
        avi = _sahte_avi(dizin.name)
        port, uretici, loglar = self._kopru(avi)
        self.assertTrue(_bekle(lambda: _durum(port)[1]["kare_sayaci"] >= 1),
                        f"ilk kare gelmedi: {_durum(port)[1]}")
        return port, uretici, loglar


class KopruAkisi(_KopruTesti):
    """K1/K2 — sahte kaynakla akis ve durum."""

    def setUp(self):
        self.port, self.uretici, self.loglar = self._sahte_kaynakli_kopru()

    def test_K1_video_akisi_pcde_cv2_VideoCapture_ile_okunur(self):
        cap = cv2.VideoCapture(kk.video_url(self.port))
        self.addCleanup(cap.release)
        self.assertTrue(cap.isOpened(), "cv2.VideoCapture kopru URL'sini acamadi (FFmpeg mpjpeg)")
        kareler = []
        for _ in range(8):
            ok, kare = cap.read()
            if ok and kare is not None:
                kareler.append(kare)
        self.assertGreaterEqual(len(kareler), 5, "kopruden >= 5 kare okunmali")
        for k in kareler:
            self.assertEqual(k.shape, (BOYUT[1], BOYUT[0], 3))
            self.assertEqual(k.dtype, np.uint8)
            # icerik gercekten sahte dosyadan (kirmizi kanal sabiti; JPEG toleransi)
            self.assertLess(abs(float(np.median(k[:, :, 2])) - KIRMIZI_KANAL_SABITI), 12)
        ortalamalar = {int(round(float(k[:, :, 0].mean()))) for k in kareler}
        self.assertGreaterEqual(len(ortalamalar), 2,
                                "kareler degismiyor — ayni kare tekrar yayinlaniyor")
        # akis istemcisi sayildi (kilitli sayac)
        self.assertTrue(_bekle(lambda: _durum(self.port)[1]["istemci_sayisi"] >= 1, tavan_s=2.0))

    def test_K2_durum_json_alanlari_kare_jpg_ve_404(self):
        kod, d = _durum(self.port)
        self.assertEqual(kod, 200)
        for alan in ("kaynak", "kaynak_turu", "kaynak_acik", "kare_sayaci", "dusen_kare",
                     "kodlama_hatasi", "fps", "fps_tavani", "kalite", "boyut",
                     "son_kare_yasi_s", "son_hata", "acma_denemesi", "acma_sayisi",
                     "istemci_sayisi", "calisma_s", "port", "video_url"):
            self.assertIn(alan, d, alan)
        self.assertTrue(d["kaynak_acik"])
        self.assertEqual(d["kaynak_turu"], kk.KAYNAK_TURU_DOSYA)
        self.assertGreaterEqual(d["kare_sayaci"], 1)
        self.assertIsNone(d["son_hata"])
        self.assertEqual(d["boyut"], [BOYUT[0], BOYUT[1]])
        self.assertEqual(d["port"], self.port)
        self.assertEqual(d["video_url"], kk.video_url(self.port))
        self.assertEqual(d["kalite"], kk.VARSAYILAN_KALITE)
        self.assertEqual(d["fps_tavani"], kk.VARSAYILAN_FPS_TAVANI)
        self.assertEqual(d["acma_sayisi"], 1)
        self.assertEqual(d["acma_denemesi"], 1)
        self.assertTrue(_bekle(lambda: _durum(self.port)[1]["fps"] is not None), "fps olculmedi")
        fps = _durum(self.port)[1]["fps"]
        self.assertGreater(fps, 0.0)
        self.assertLessEqual(fps, kk.VARSAYILAN_FPS_TAVANI * 1.5, "fps tavani asildi")
        kod, basliklar, govde = _http(self.port, kk.KARE_YOLU)
        self.assertEqual(kod, 200)
        self.assertEqual(basliklar["Content-Type"], "image/jpeg")
        kare = cv2.imdecode(np.frombuffer(govde, np.uint8), cv2.IMREAD_COLOR)
        self.assertIsNotNone(kare)
        self.assertEqual(kare.shape, (BOYUT[1], BOYUT[0], 3))
        self.assertEqual(_http(self.port, "/yok")[0], 404)


class KaynakYok(_KopruTesti):
    """K3 — kaynak yokken ayakta, bayat kare yok, sonradan toparlar."""

    def test_K3_kaynak_yokken_kopru_ayakta_503_kirmizi_log_ve_sonradan_toparlar(self):
        dizin = tempfile.TemporaryDirectory()
        self.addCleanup(dizin.cleanup)
        yol = Path(dizin.name) / "henuz_yok.avi"
        port, uretici, loglar = self._kopru(yol)
        self.assertTrue(_bekle(lambda: _durum(port)[1]["acma_denemesi"] >= 1))
        kod, d = _durum(port)
        self.assertEqual(kod, 200, "durum ucu kaynak yokken de 200 vermeli")
        self.assertFalse(d["kaynak_acik"])
        self.assertIn("acilamadi", d["son_hata"] or "")
        self.assertEqual(d["kare_sayaci"], 0)
        self.assertIsNone(d["boyut"])
        self.assertEqual(d["acma_sayisi"], 0)
        # yeniden acma ~YENIDEN_ACMA_ARALIGI_S'de bir: mesgul dongu degil
        t0 = time.monotonic()
        self.assertTrue(_bekle(lambda: _durum(port)[1]["acma_denemesi"] >= 3, tavan_s=6.0))
        self.assertGreaterEqual(time.monotonic() - t0, 0.8 * kk.YENIDEN_ACMA_ARALIGI_S,
                                "acma denemeleri araliksiz — mesgul dongu")
        # bayat/sahte kare YOK: akis ve tek kare 503 + JSON hata
        kod, _, govde = _http(port, kk.VIDEO_YOLU)
        self.assertEqual(kod, 503)
        self.assertIn("hata", json.loads(govde.decode("utf-8")))
        self.assertEqual(_http(port, kk.KARE_YOLU)[0], 503)
        # tuketici tarafi: cv2 kaynagi ACAMAZ ya da kare alamaz (sessiz sahte kare yok)
        cap = cv2.VideoCapture(kk.video_url(port))
        try:
            if cap.isOpened():
                ok, kare = cap.read()
                self.assertFalse(ok and kare is not None, "kaynak yokken kare geldi")
        finally:
            cap.release()
        self.assertTrue(any(k and "acilamadi" in m for k, m in loglar), loglar)
        # kaynak SONRADAN gelir (atomik yeniden adlandirma) -> kendiliginden acilir
        gecici = _sahte_avi(dizin.name, ad="gecici.avi")
        os.replace(str(gecici), str(yol))
        self.assertTrue(_bekle(lambda: _durum(port)[1]["kaynak_acik"]
                               and _durum(port)[1]["kare_sayaci"] >= 1, tavan_s=8.0),
                        f"kaynak gelince acilmadi: {_durum(port)[1]}")
        d = _durum(port)[1]
        self.assertIsNone(d["son_hata"])
        self.assertEqual(d["boyut"], [BOYUT[0], BOYUT[1]])
        self.assertEqual(d["acma_sayisi"], 1)
        self.assertEqual(_http(port, kk.KARE_YOLU)[0], 200)
        self.assertTrue(any((not k) and "ACILDI" in m for k, m in loglar), loglar)


class RpiInferenceUyumu(_KopruTesti):
    """K4 — tuketici kodu DEGISMEZ: mevcut kamera_kaynagi_coz + kamera_kareleri kopruyu okur."""

    def test_K4_kamera_kaynagi_coz_ve_uretim_jeneratoru_kopruden_okur(self):
        try:
            import rpi_inference as ri
        except Exception as exc:  # noqa: BLE001 - kurulum kapisi
            self.skipTest(f"YAPILAMADI: rpi_inference import edilemedi: {exc!r}")
        port, uretici, _ = self._sahte_kaynakli_kopru()
        url = kk.video_url(port)
        coz = ri.kamera_kaynagi_coz(url)
        self.assertIsInstance(coz, str)
        self.assertEqual(coz, url, "URL indeks/dosya sanilmamali")
        cap = cv2.VideoCapture(coz)
        self.addCleanup(cap.release)
        self.assertTrue(cap.isOpened())
        ozet = {}
        uretec = ri.kamera_kareleri(cap, ozet)
        kareler = [next(uretec) for _ in range(3)]
        self.assertEqual(ozet.get("okunan"), 3)
        self.assertEqual(ozet.get("dusen_toplam", 0), 0)
        for k in kareler:
            self.assertEqual(k.shape, (BOYUT[1], BOYUT[0], 3))
            self.assertEqual(k.dtype, np.uint8)


class Python36Uyumu(unittest.TestCase):
    """K5 — sistem Python 3.6'da kosacak dosya: soz dizimi, bagimlilik, ayna, cozum."""

    def test_K5_ast_36_uyumu_yalniz_stdlib_cv2_numpy(self):
        kaynak = KANONIK.read_text(encoding="utf-8")
        agac = ast.parse(kaynak, str(KANONIK))
        yasak = []
        for d in ast.walk(agac):
            if isinstance(d, ast.NamedExpr):
                yasak.append(f"walrus satir {d.lineno}")
            if isinstance(d, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)) \
                    and getattr(d.args, "posonlyargs", []):
                yasak.append(f"posonly satir {d.lineno}")
            if isinstance(d, ast.ImportFrom) and d.module == "__future__" \
                    and any(a.name == "annotations" for a in d.names):
                yasak.append(f"__future__ annotations satir {d.lineno}")
            if hasattr(ast, "Match") and isinstance(d, ast.Match):
                yasak.append(f"match satir {d.lineno}")
            if isinstance(d, ast.Subscript) and isinstance(d.value, ast.Name) \
                    and d.value.id in ("list", "dict", "tuple", "set", "type"):
                yasak.append(f"builtin generic tip satir {d.lineno}")
            if isinstance(d, ast.Name) and d.id in ("ThreadingHTTPServer", "breakpoint"):
                yasak.append(f"{d.id} (3.7+) satir {d.lineno}")
            if isinstance(d, ast.Attribute) and d.attr in (
                    "ThreadingHTTPServer", "removeprefix", "removesuffix", "isqrt",
                    "cached_property", "fromisoformat"):
                yasak.append(f".{d.attr} (3.7+) satir {d.lineno}")
        self.assertEqual(yasak, [])
        self.assertIsNone(re.search(r"\{[A-Za-z_][\w.\[\]()]*=\}", kaynak),
                          "f-string '=' belirteci 3.8+")
        stdlib = set(getattr(sys, "stdlib_module_names", ())) | {
            "argparse", "json", "signal", "sys", "threading", "time", "collections",
            "http", "socketserver"}
        izinli = stdlib | {"cv2", "numpy"}
        for d in ast.walk(agac):
            if isinstance(d, ast.Import):
                for a in d.names:
                    self.assertIn(a.name.split(".")[0], izinli, a.name)
            elif isinstance(d, ast.ImportFrom):
                self.assertIn((d.module or "").split(".")[0], izinli, d.module)
        self.assertEqual(KANONIK.read_bytes(), AYNA.read_bytes(),
                         "jetson_paket/kod/kamera_koprusu.py bayat — scripts/jetson_paket_hazirla.py")
        self.assertIn("NEDEN", kaynak[:400])
        self.assertIn("SAHA_HAZIRLIK_PLANI_20260903", kaynak[:400])

    def test_K5_kaynak_cozumu_ve_nvargus_borusu(self):
        boru, api, tur = kk.kaynagi_coz("")
        self.assertEqual((api, tur), (cv2.CAP_GSTREAMER, kk.KAYNAK_TURU_NVARGUS))
        self.assertEqual(kk.kaynagi_coz(kk.KAYNAK_NVARGUS)[0], boru)
        for parca in ("nvarguscamerasrc", "sensor-id=0", "memory:NVMM", "nvvidconv",
                      "format=(string)BGR", "appsink", "drop=true", "max-buffers=1",
                      f"width=(int){kk.VARSAYILAN_GENISLIK}",
                      f"height=(int){kk.VARSAYILAN_YUKSEKLIK}",
                      f"framerate=(fraction){kk.VARSAYILAN_KAMERA_FPS}/1"):
            self.assertIn(parca, boru, parca)
        self.assertIn("width=(int)640", kk.nvargus_boru(genislik=640))
        self.assertEqual(kk.kaynagi_coz("0"), (0, cv2.CAP_ANY, kk.KAYNAK_TURU_INDEKS))
        self.assertEqual(kk.kaynagi_coz(" 2 "), (2, cv2.CAP_ANY, kk.KAYNAK_TURU_INDEKS))
        self.assertEqual(kk.kaynagi_coz("http://127.0.0.1:4747/video"),
                         ("http://127.0.0.1:4747/video", cv2.CAP_ANY, kk.KAYNAK_TURU_URL))
        self.assertEqual(kk.kaynagi_coz("videotestsrc ! appsink"),
                         ("videotestsrc ! appsink", cv2.CAP_GSTREAMER, kk.KAYNAK_TURU_GSTREAMER))
        self.assertEqual(kk.kaynagi_coz("/tmp/x.avi"), ("/tmp/x.avi", cv2.CAP_ANY, kk.KAYNAK_TURU_DOSYA))
        self.assertEqual(kk.video_url(), f"http://127.0.0.1:{kk.VARSAYILAN_PORT}{kk.VIDEO_YOLU}")
        self.assertEqual(kk.VIDEO_YOLU, "/video")
        # istemci "yeni kare" bekleyisi: ayni sira -> zaman asimi, kare yok
        u = kk.KareUretici("/yok/yok.avi", log=lambda *a, **k: None)
        self.assertEqual(u.kare_bekle(None, zaman_asimi_s=0.0), (None, 0))


class Cli(unittest.TestCase):
    """K6 — systemd'nin kostugu giris noktasi."""

    def test_K6_cli_dinliyor_satiri_durum_ve_gecersiz_kalite(self):
        dizin = tempfile.TemporaryDirectory()
        self.addCleanup(dizin.cleanup)
        avi = _sahte_avi(dizin.name)
        p = subprocess.Popen(
            [sys.executable, "-u", str(KANONIK), "--kaynak", str(avi), "--port", "0",
             "--log-aralik", "0"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            encoding="utf-8", errors="replace")
        def _temizle():
            if p.poll() is None:
                p.kill()
                p.wait(timeout=10)
            p.stdout.close()

        self.addCleanup(_temizle)
        satirlar = []

        def oku():
            for s in p.stdout:
                satirlar.append(s.rstrip("\r\n"))

        threading.Thread(target=oku, daemon=True).start()
        self.assertTrue(_bekle(lambda: any("dinliyor" in s for s in satirlar), tavan_s=30.0),
                        f"'dinliyor' satiri yok: {satirlar}")
        satir = next(s for s in satirlar if "dinliyor" in s)
        m = re.search(r"dinliyor http://127\.0\.0\.1:(\d+)/video", satir)
        self.assertIsNotNone(m, satir)
        port = int(m.group(1))
        self.assertNotEqual(port, 0)
        self.assertIn(kk.LOG_ONEKI, satir)
        self.assertTrue(_bekle(lambda: _durum(port)[1]["kare_sayaci"] >= 1), satirlar)
        d = _durum(port)[1]
        self.assertTrue(d["kaynak_acik"])
        self.assertEqual(d["port"], port)
        p.terminate()
        p.wait(timeout=10)
        r = subprocess.run([sys.executable, str(KANONIK), "--kalite", "0", "--port", "0"],
                           capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("--kalite", r.stderr)


if __name__ == "__main__":
    unittest.main()
