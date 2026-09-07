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
     match / builtin-generic tip yok; yalniz stdlib + cv2 + numpy; koprunun kullandigi
     HER dis ad ve oznitelik 3.6 BEYAZ LISTESINDE (kara liste DEGIL — asagi bak);
     kod/ aynasi kanonikle bayt-es; kaynak cozumu ve nvargus boru metni
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
                     "kodlama_hatasi", "donuk_kare", "donuk_kare_ardisik",
                     "fps", "fps_tavani", "kalite", "boyut",
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


class ArizaMutasyonlari(unittest.TestCase):
    """Kamera surucusunun sessiz/tehlikeli uc ariza yonu gercek aga dokunmadan sinanir."""

    class _Cap:
        def __init__(self, read_sonucu=None, read_hatasi=None):
            self.read_sonucu = read_sonucu
            self.read_hatasi = read_hatasi
            self.birakildi = 0

        def isOpened(self):
            return True

        def read(self):
            if self.read_hatasi is not None:
                raise self.read_hatasi
            return self.read_sonucu

        def release(self):
            self.birakildi += 1

    def _video_capture_yamala(self, fabrika):
        asil = kk.cv2.VideoCapture
        kk.cv2.VideoCapture = fabrika
        self.addCleanup(setattr, kk.cv2, "VideoCapture", asil)

    def test_MUTASYON_read_istisnasi_ipligi_oldurmez_ve_yeniden_dener(self):
        """``cap.read -> RuntimeError``: thread canli, kaynak kirmizi, yeniden acma sayilir."""
        capler = []

        def ac(*_args):
            cap = self._Cap(read_hatasi=RuntimeError("surucu koptu"))
            capler.append(cap)
            return cap

        self._video_capture_yamala(ac)
        asil_aralik = kk.YENIDEN_ACMA_ARALIGI_S
        kk.YENIDEN_ACMA_ARALIGI_S = 0.02
        self.addCleanup(setattr, kk, "YENIDEN_ACMA_ARALIGI_S", asil_aralik)
        loglar = []
        u = kk.KareUretici("0", fps_tavani=0, log_aralik_s=0,
                           log=lambda m, kirmizi=False: loglar.append((kirmizi, m)))
        u.start()
        self.addCleanup(u.join, 2.0)
        self.addCleanup(u.durdur)
        self.assertTrue(_bekle(lambda: len(capler) >= 2, tavan_s=2.0),
                        "read istisnasindan sonra yeniden acma olmadi")
        self.assertTrue(u.is_alive(), "VideoCapture.read istisnasi uretici ipligini oldurdu")
        self.assertTrue(any(k and "read istisnasi RuntimeError" in m for k, m in loglar),
                        loglar)
        self.assertTrue(all(c.birakildi >= 1 for c in capler[:-1]),
                        "arizali capture nesnesi birakilmadi")

    def test_MUTASYON_yeniden_acma_eski_jpeg_onbellegini_atomik_siler(self):
        """Yeni capture acilirken onceki neslin JPEG'i/sure/boyutu sunulamaz."""
        u = kk.KareUretici("0", fps_tavani=0, log=lambda *_a, **_k: None)
        kare = np.full((24, 32, 3), 77, np.uint8)
        self.assertEqual(u._kare_yayinla(kare), (True, False))
        eski_sira = u.sira
        self.assertIsNotNone(u.jpeg)
        cap = self._Cap(read_sonucu=(True, kare.copy()))
        self._video_capture_yamala(lambda *_a: cap)
        acilan = u._ac()
        self.addCleanup(u._guvenli_birak, acilan)
        self.assertIs(acilan, cap)
        self.assertTrue(u.kaynak_acik)
        self.assertIsNone(u.jpeg)
        self.assertIsNone(u.sekil)
        self.assertIsNone(u.son_kare_t)
        self.assertEqual(u.sira, eski_sira, "nesiller arasinda sira geri alinmamali")
        self.assertEqual(u.kare_bekle(None, zaman_asimi_s=0.0,
                                      azami_yas_s=kk.AKIS_KARE_BEKLEME_S),
                         (None, eski_sira))
        # Ayni donmus tampon yeni capture neslinin ilk read'inde de taze sayilmaz.
        self.assertEqual(u._kare_yayinla(kare.copy()), (False, False))
        self.assertIsNone(u.jpeg)
        degisen = np.full_like(kare, 200)
        self.assertEqual(u._kare_yayinla(degisen), (True, False))
        self.assertEqual(u.sira, eski_sira + 1)

    def test_MUTASYON_ayni_jpeg_sirayi_ilerletmez_donunca_503(self):
        """``read=True`` olsa da bayt-es kare canlilik sayilmaz ve HTTP fail-closed olur."""
        simdi = [100.0]
        u = kk.KareUretici("0", fps_tavani=0, saat=lambda: simdi[0],
                           log=lambda *_a, **_k: None)
        kare = np.full((24, 32, 3), 123, np.uint8)
        self.assertEqual(u._kare_yayinla(kare), (True, False))
        ilk_sira = u.sira
        ilk_t = u.son_kare_t
        simdi[0] += kk.DONUK_KARE_AZAMI_S * 0.5
        self.assertEqual(u._kare_yayinla(kare.copy()), (False, False))
        self.assertEqual((u.sira, u.son_kare_t), (ilk_sira, ilk_t))
        simdi[0] += kk.DONUK_KARE_AZAMI_S * 0.5 + 0.001
        self.assertEqual(u._kare_yayinla(kare.copy()), (False, True))
        self.assertEqual(u.sira, ilk_sira, "donmus kare sira artirmis")
        self.assertEqual(u.donuk_kare, 2)

        cap = self._Cap(read_sonucu=(True, kare.copy()))
        u.kaynak_acik = True
        u._koptu(cap, "donuk kare mutasyonu")
        sunucu = kk.KopruSunucusu((kk.YEREL_HOST, 0), u)
        iplik = threading.Thread(target=sunucu.serve_forever,
                                 kwargs={"poll_interval": 0.02}, daemon=True)
        iplik.start()

        def kapat():
            sunucu.shutdown()
            sunucu.server_close()
            iplik.join(timeout=2.0)

        self.addCleanup(kapat)
        port = sunucu.server_address[1]
        kod, _, govde = _http(port, kk.KARE_YOLU)
        self.assertEqual(kod, 503)
        d = json.loads(govde.decode("utf-8"))
        self.assertFalse(d["kaynak_acik"])
        self.assertIsNone(d["son_kare_yasi_s"])
        self.assertIn("donuk kare", d["son_hata"])


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


# ══════════════════════════════════════════════════════════════════════════════
# K5 · PYTHON 3.6 BEYAZ LISTESI
#
# NEDEN BEYAZ LISTE (olculen kusur — FDR/BOLUM_4 §6.2 satir 4):
#   Bu kapi 2026-09-03'e kadar bir KARA LISTE idi: `ThreadingHTTPServer`,
#   `breakpoint`, `removeprefix`, `removesuffix`, `isqrt`, `cached_property`,
#   `fromisoformat` adlari tek tek aranirdi. Kara listenin kusuru yapisaldir:
#   listede OLMAYAN yeni bir 3.7+ API'si sessizce gecer. Olculen ornek — o kara
#   liste `sys.stdout.reconfigure` (3.7), `time.monotonic_ns` (3.7),
#   `str.isascii` (3.7), `contextlib.nullcontext` (3.7), `math.prod` (3.8)
#   adlarinin hicbirini GORMUYORDU.
#   [D-431: 6 Eylul'de kart Orin Nano / JetPack 7.2.1 / sistem Py 3.12 + cv2 4.6
#   cikti; asagidaki Nano kunyesi GECERSIZ, kisit bilerek TUTULUYOR — daha siki
#   kapi gevsetilmez.]
#   Jetson Nano'da (JetPack 4.6 / Ubuntu 18.04) kopru SISTEM Python 3.6 ile
#   kosar — CSI kamera yalniz o yorumlayicinin GStreamer'li OpenCV'siyle acilir.
#   Yani kacan bir 3.7+ cagrisi PC'de degil, SAHADA, ilk kez patlar.
#
# KAPI TERSINE CEVRILDI: koprunun kullandigi HER dis ad ve HER oznitelik,
# asagida KAYNAGIYLA sayilan 3.6 kumesinde OLMAK ZORUNDADIR. Kumede olmayan
# her ad testi ADIYLA ve SATIRIYLA dusurur. Yeni bir ad eklemek isteyen, onu
# 3.6 belgesinde dogrulayip bu envantere yazmak zorundadir (fail-closed).
#
# BEYAZ LISTE NASIL KURULDU (kaynaklar):
#   * PY36_BUILTIN_ADLARI — CPython 3.6 `dir(builtins)`. 3.13'un builtins'inden
#     3.6 SONRASI eklenenler dusuruldu: breakpoint (3.7), aiter/anext (3.10),
#     EncodingWarning (3.10), ExceptionGroup/BaseExceptionGroup (3.11),
#     PythonFinalizationError/_IncompleteInputError (3.13). Ayrica `site`nin
#     enjekte ettigi exit/quit/copyright/credits/license (python -S ile YOK) ve
#     Windows'a ozgu WindowsError (kopru Linux'ta kosar) BILEREK disarida.
#     `_py36_envanter_butunlugu` bu kumenin bugunku builtins'in ALT KUMESI
#     oldugunu dogrular — yazim hatasi kapisi.
#   * PY36_MODUL — modul basina 3.6 kutuphane belgesi envanteri. Her girdi 3.6
#     belgesinde VAR olarak dogrulandi; "versionadded 3.7+" olan hicbir ad
#     alinmadi (ornek: http.server'da ThreadingHTTPServer 3.7 -> YOK,
#     time'da *_ns aileleri 3.7 -> YOK, signal'da valid_signals/raise_signal/
#     strsignal 3.8 -> YOK, threading'de excepthook/get_native_id 3.8 -> YOK).
#   * PY36_NESNE_YONTEMLERI — 3.6 yerlesik tip yontemleri (str/bytes/list/dict/
#     set/io/sayi). str.removeprefix/removesuffix (3.9), str.isascii (3.7),
#     io.TextIOWrapper.reconfigure (3.7), int.bit_count (3.10) BILEREK YOK.
#   * PY36_MIRAS_OZNITELIKLERI — koprunun TUREDIGI 3.6 sinif API'leri
#     (http.server.BaseHTTPRequestHandler, socketserver.BaseServer/TCPServer,
#     threading.Thread/Event/Condition). socketserver.block_on_close (3.7) ve
#     Thread.native_id (3.8) BILEREK YOK.
#   * CV2_41_ADLARI / NUMPY_ADLARI — Jetson'daki SISTEM paketleri
#     (python3-opencv 4.1.1, python3-numpy 1.13/1.19). Bu kume ayrica OpenCV
#     4.5+ API kaymasini da yakalar: 4.1'de olmayan bir cv2 adi da duser.
#
# YANLIS ALARM KAPISI: yerel degiskenler, dongu/with/except hedefleri, kendi
# tanimladigi fonksiyon/sinif adlari, PARAMETRE adlari, `self.x = ...` ile
# kendi actigi oznitelikler ve `add_argument("--x")` ile kendi urettigi argparse
# alanlari kontrolden HARIC tutulur (asagidaki iki toplayici).
#
# BILINEN SINIR (durustce yazildi): kontrol ADA bakar, TURE bakmaz — oznitelik
# adlari duz bir kumede toplanir, `x.read` ile `y.read` ayirt edilmez. Anahtar
# argumanlarina (`print(..., flush=True)`) bakilmaz. Bu kapi 3.6'da OLMAYAN bir
# adin sessizce girmesini engeller; 3.6'da olan bir adin YANLIS nesnede
# kullanilmasini engellemez.
# ══════════════════════════════════════════════════════════════════════════════

#: CPython 3.6 builtins (yukarida sayilan gerekcelerle 3.13'ten suzuldu).
PY36_BUILTIN_ADLARI = frozenset("""
ArithmeticError AssertionError AttributeError BaseException BlockingIOError
BrokenPipeError BufferError BytesWarning ChildProcessError ConnectionAbortedError
ConnectionError ConnectionRefusedError ConnectionResetError DeprecationWarning
EOFError Ellipsis EnvironmentError Exception False FileExistsError
FileNotFoundError FloatingPointError FutureWarning GeneratorExit IOError
ImportError ImportWarning IndentationError IndexError InterruptedError
IsADirectoryError KeyError KeyboardInterrupt LookupError MemoryError
ModuleNotFoundError NameError None NotADirectoryError NotImplemented
NotImplementedError OSError OverflowError PendingDeprecationWarning
PermissionError ProcessLookupError RecursionError ReferenceError ResourceWarning
RuntimeError RuntimeWarning StopAsyncIteration StopIteration SyntaxError
SyntaxWarning SystemError SystemExit TabError TimeoutError True TypeError
UnboundLocalError UnicodeDecodeError UnicodeEncodeError UnicodeError
UnicodeTranslateError UnicodeWarning UserWarning ValueError Warning
ZeroDivisionError __build_class__ __debug__ __doc__ __import__ __loader__
__name__ __package__ __spec__ abs all any ascii bin bool bytearray bytes
callable chr classmethod compile complex delattr dict dir divmod enumerate eval
exec filter float format frozenset getattr globals hasattr hash help hex id
input int isinstance issubclass iter len license list locals map max memoryview
min next object oct open ord pow print property range repr reversed round set
setattr slice sorted staticmethod str sum super tuple type vars zip
""".split())

#: Modul basina 3.6 envanteri. `import X` ya da `from X import N` gorulurse X
#: BURADA OLMAK ZORUNDA; yoksa test "envanter yok" diye duser (fail-closed).
#: `from X import N` icinde N de X'in kumesinde olmak zorundadir — 3.7 adinin
#: ImportFrom ile "yerel ad" kilifina girip kontrolden kacmasi boyle engellenir.
PY36_MODUL = {
    "__future__": frozenset("""
        nested_scopes generators division absolute_import with_statement
        print_function unicode_literals generator_stop barry_as_FLUFL
    """.split()),                       # annotations (3.7) BILEREK YOK
    "argparse": frozenset("""
        ArgumentParser ArgumentError ArgumentTypeError Namespace Action FileType
        HelpFormatter RawDescriptionHelpFormatter RawTextHelpFormatter
        ArgumentDefaultsHelpFormatter MetavarTypeHelpFormatter SUPPRESS OPTIONAL
        ZERO_OR_MORE ONE_OR_MORE PARSER REMAINDER
        add_argument add_argument_group add_mutually_exclusive_group
        add_subparsers parse_args parse_known_args
        set_defaults get_default print_usage print_help format_usage format_help
        convert_arg_line_to_args prog usage description epilog prefix_chars
    """.split()),                       # exit_on_error / BooleanOptionalAction (3.9) YOK
    "collections": frozenset("""
        deque defaultdict OrderedDict Counter namedtuple ChainMap UserDict
        UserList UserString abc
        append appendleft clear copy count extend extendleft index insert maxlen
        pop popleft remove reverse rotate move_to_end most_common elements
        subtract new_child parents maps default_factory
    """.split()),
    "cv2": None,                        # asagida CV2_41_ADLARI (surum kunyeli)
    "http": frozenset(),                # `import http` govdesi kullanilmiyor
    "http.server": frozenset("""
        HTTPServer BaseHTTPRequestHandler SimpleHTTPRequestHandler
        CGIHTTPRequestHandler
    """.split()),                       # ThreadingHTTPServer (3.7) BILEREK YOK
    "json": frozenset("""
        dump dumps load loads JSONEncoder JSONDecoder JSONDecodeError
        encoder decoder scanner
    """.split()),
    "numpy": None,                      # asagida NUMPY_ADLARI
    "signal": frozenset("""
        signal getsignal alarm pause setitimer getitimer siginterrupt
        set_wakeup_fd pthread_kill pthread_sigmask sigwait sigwaitinfo
        sigtimedwait sigpending default_int_handler
        SIG_DFL SIG_IGN SIGABRT SIGALRM SIGBUS SIGCHLD SIGCONT SIGFPE SIGHUP
        SIGILL SIGINT SIGKILL SIGPIPE SIGQUIT SIGSEGV SIGTERM SIGUSR1 SIGUSR2
        SIGWINCH ITIMER_REAL ITIMER_VIRTUAL ITIMER_PROF NSIG Signals Handlers
        SIG_BLOCK SIG_UNBLOCK SIG_SETMASK
    """.split()),                       # valid_signals/raise_signal/strsignal (3.8) YOK
    "socketserver": frozenset("""
        BaseServer TCPServer UDPServer ThreadingMixIn ForkingMixIn
        ThreadingTCPServer ThreadingUDPServer ForkingTCPServer ForkingUDPServer
        UnixStreamServer UnixDatagramServer ThreadingUnixStreamServer
        ThreadingUnixDatagramServer BaseRequestHandler StreamRequestHandler
        DatagramRequestHandler
    """.split()),
    "sys": frozenset("""
        argv stdin stdout stderr __stdin__ __stdout__ __stderr__ exit path
        platform version version_info executable maxsize maxunicode modules
        exc_info getdefaultencoding getfilesystemencoding getrecursionlimit
        setrecursionlimit getsizeof getrefcount byteorder flags hexversion
        prefix base_prefix exec_prefix base_exec_prefix implementation intern
        settrace gettrace setprofile displayhook excepthook __displayhook__
        __excepthook__ dont_write_bytecode warnoptions float_info int_info
        thread_info api_version abiflags is_finalizing setswitchinterval
        getswitchinterval meta_path path_hooks path_importer_cache
        tracebacklimit set_asyncgen_hooks get_asyncgen_hooks
    """.split()),                       # stdlib_module_names (3.10), breakpointhook (3.7),
                                        # audit/addaudithook/unraisablehook (3.8) YOK
    "threading": frozenset("""
        Thread Lock RLock Condition Event Semaphore BoundedSemaphore Timer
        Barrier local current_thread main_thread active_count enumerate
        get_ident stack_size settrace setprofile TIMEOUT_MAX ThreadError
        BrokenBarrierError
        start run join is_alive name ident daemon setDaemon isDaemon getName
        setName acquire release locked notify notify_all wait wait_for set
        clear is_set
    """.split()),                       # excepthook/get_native_id/native_id (3.8) YOK
    "time": frozenset("""
        monotonic time sleep perf_counter process_time clock gmtime localtime
        mktime strftime strptime asctime ctime struct_time timezone altzone
        daylight tzname tzset get_clock_info clock_gettime clock_settime
        clock_getres CLOCK_MONOTONIC CLOCK_MONOTONIC_RAW CLOCK_REALTIME
        CLOCK_PROCESS_CPUTIME_ID CLOCK_THREAD_CPUTIME_ID
    """.split()),                       # *_ns ailesi + thread_time (3.7) BILEREK YOK
    "urllib": frozenset(),
    "urllib.parse": frozenset("""
        urlparse urlsplit urlunparse urlunsplit urljoin urldefrag parse_qs
        parse_qsl quote quote_plus quote_from_bytes unquote unquote_plus
        unquote_to_bytes urlencode SplitResult ParseResult DefragResult
        uses_relative uses_netloc uses_params
        scheme netloc path params query fragment username password hostname
        port geturl
    """.split()),
}

#: (D-431: Orin Nano'da sistem cv2 4.6 — asagidaki 4.1 kumesi kapi olarak
#: TUTULUR, gevsetilmez; "JetPack 4.6" kunyesi GECERSIZ, tarihce.)
#: OpenCV 4.1.1 — JetPack 4.6 sistem paketi (python3-opencv). Kopru YALNIZ bu
#: adlari kullanabilir; 4.5+ ile gelen bir ad da bu kapidan gecemez.
CV2_41_ADLARI = frozenset("""
    VideoCapture VideoWriter VideoWriter_fourcc imencode imdecode imread imwrite
    error resize cvtColor putText rectangle circle line getBuildInformation
    read isOpened release set get grab retrieve open getBackendName write
    CAP_ANY CAP_GSTREAMER CAP_FFMPEG CAP_V4L2 CAP_IMAGES
    CAP_PROP_POS_FRAMES CAP_PROP_POS_MSEC CAP_PROP_FRAME_COUNT
    CAP_PROP_FRAME_WIDTH CAP_PROP_FRAME_HEIGHT CAP_PROP_FPS CAP_PROP_BUFFERSIZE
    IMWRITE_JPEG_QUALITY IMREAD_COLOR IMREAD_GRAYSCALE IMREAD_UNCHANGED
    COLOR_BGR2RGB COLOR_RGB2BGR COLOR_BGR2GRAY FONT_HERSHEY_SIMPLEX
    INTER_LINEAR INTER_AREA INTER_NEAREST
""".split())

#: NumPy — Jetson sistem paketi (python3-numpy 1.13/1.19 serisi).
NUMPY_ADLARI = frozenset("""
    ndarray dtype uint8 uint16 int32 int64 float32 float64 bool_
    zeros ones empty full array asarray ascontiguousarray frombuffer fromstring
    shape ndim size itemsize nbytes astype tobytes tolist copy reshape ravel
    flatten clip mean median sum min max abs argmax argmin where concatenate
""".split())

# Ucuncu taraf envanterleri modul tablosuna BAGLANIR: boylece `from cv2 import
# VideoCapture` gibi bir ImportFrom da ad ad denetlenir (None birakilsaydi
# atlanirdi).
PY36_MODUL["cv2"] = CV2_41_ADLARI
PY36_MODUL["numpy"] = NUMPY_ADLARI

#: 3.6 yerlesik tip yontemleri (str/bytes/list/tuple/dict/set/io/sayi).
#: removeprefix/removesuffix (3.9), isascii (3.7), reconfigure (3.7),
#: bit_count (3.10) BILEREK YOK.
PY36_NESNE_YONTEMLERI = frozenset("""
    capitalize casefold center count encode decode endswith expandtabs find
    format format_map index isalnum isalpha isdecimal isdigit isidentifier
    islower isnumeric isprintable isspace istitle isupper join ljust lower
    lstrip maketrans partition replace rfind rindex rjust rpartition rsplit
    rstrip split splitlines startswith strip swapcase title translate upper
    zfill hex fromhex
    append clear copy extend insert pop remove reverse sort
    fromkeys get items keys popitem setdefault update values
    add difference difference_update discard intersection intersection_update
    isdisjoint issubset issuperset symmetric_difference
    symmetric_difference_update union
    close closed detach fileno flush isatty mode name newlines peek raw read
    read1 readable readinto readline readlines seek seekable tell truncate
    writable write writelines buffer encoding errors line_buffering
    bit_length to_bytes from_bytes conjugate real imag numerator denominator
    is_integer as_integer_ratio
    __init__ __new__ __call__ __enter__ __exit__ __iter__ __next__ __len__
    __repr__ __str__ __class__ __dict__ __doc__ __module__ __name__ __bases__
    __mro__ __getitem__ __setitem__ __contains__ __eq__ __hash__
""".split())

#: Koprunun TUREDIGI 3.6 sinif API'leri (http.server / socketserver / threading).
#: block_on_close (3.7) ve native_id (3.8) BILEREK YOK.
PY36_MIRAS_OZNITELIKLERI = frozenset("""
    client_address server close_connection requestline command path headers
    rfile wfile server_version sys_version error_message_format
    error_content_type protocol_version MessageClass responses default_request_version
    handle handle_one_request handle_expect_100 send_error send_response
    send_response_only send_header end_headers flush_headers log_request
    log_error log_message version_string date_time_string log_date_time_string
    address_string setup finish request connection rbufsize wbufsize timeout
    disable_nagle_algorithm weekdayname monthname extensions_map
    RequestHandlerClass address_family socket_type request_queue_size
    allow_reuse_address server_address socket server_name server_port
    serve_forever shutdown server_bind server_activate server_close get_request
    handle_request handle_error process_request process_request_thread
    verify_request finish_request close_request service_actions daemon_threads
""".split())

IZINLI_ADLAR = PY36_BUILTIN_ADLARI | {"__file__", "__all__", "__version__"}
IZINLI_OZNITELIKLER = (
    PY36_NESNE_YONTEMLERI | PY36_MIRAS_OZNITELIKLERI | CV2_41_ADLARI | NUMPY_ADLARI
    | frozenset().union(*[k for k in PY36_MODUL.values() if k is not None]))

#: 3.7+ API'si olup KASITLI ve KORUMALI kullanilan adlar. Kullanimi `try:` govdesi
#: icinde ve `except AttributeError` ile yakalanmis OLMAK ZORUNDA; korumasiz
#: kullanimda kapi yine duser. Kacamak degil, DARALTILMIS istisnadir.
KORUMALI_YENI_API = {
    "reconfigure": "io.TextIOWrapper.reconfigure (3.7) — 3.6'da AttributeError, "
                   "try/except AttributeError ile korunmali",
}


def _py36_bagli_adlar(agac):
    """Modulun KENDI tanimladigi/bagladigi adlar (yanlis alarm kapisi).

    import adlari, fonksiyon/sinif adlari, PARAMETRE adlari, atama/dongu/with/
    except hedefleri, global/nonlocal beyanlari. Kapsam (scope) ayrimi YAPILMAZ:
    bilerek gevsek — amac dis API kacagini yakalamak, ad golgelemesi degil.
    """
    bagli = set()
    for d in ast.walk(agac):
        if isinstance(d, ast.Import):
            for a in d.names:
                bagli.add(a.asname or a.name.split(".")[0])
        elif isinstance(d, ast.ImportFrom):
            for a in d.names:
                bagli.add(a.asname or a.name)
        if isinstance(d, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            bagli.add(d.name)
        if isinstance(d, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            a = d.args
            for arg in (list(getattr(a, "posonlyargs", [])) + list(a.args)
                        + list(a.kwonlyargs)):
                bagli.add(arg.arg)
            for v in (a.vararg, a.kwarg):
                if v is not None:
                    bagli.add(v.arg)
        if isinstance(d, ast.Name) and isinstance(d.ctx, (ast.Store, ast.Del)):
            bagli.add(d.id)
        if isinstance(d, ast.ExceptHandler) and d.name:
            bagli.add(d.name)
        if isinstance(d, (ast.Global, ast.Nonlocal)):
            bagli.update(d.names)
    return bagli


def _py36_oz_oznitelikler(agac):
    """Modulun KENDI actigi oznitelikler: `self.x = ...`, sinif govdesi uyeleri,
    metot adlari ve `add_argument("--x")` ile urettigi argparse alanlari."""
    oz = set()
    for d in ast.walk(agac):
        if isinstance(d, ast.Attribute) and isinstance(d.ctx, (ast.Store, ast.Del)):
            oz.add(d.attr)
        if isinstance(d, ast.ClassDef):
            for g in d.body:
                if isinstance(g, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    oz.add(g.name)
                hedefler = (g.targets if isinstance(g, ast.Assign)
                            else [g.target] if isinstance(g, ast.AnnAssign) else [])
                for t in hedefler:
                    if isinstance(t, ast.Name):
                        oz.add(t.id)
        if isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute) \
                and d.func.attr == "add_argument":
            for a in d.args:
                if isinstance(a, ast.Constant) and isinstance(a.value, str) \
                        and a.value.startswith("--"):
                    oz.add(a.value[2:].replace("-", "_"))
            for kw in d.keywords:
                if kw.arg == "dest" and isinstance(kw.value, ast.Constant):
                    oz.add(str(kw.value.value))
    return oz


def _py36_korumali_dugumler(agac):
    """`except AttributeError` ile korunan try GOVDELERINDEKI Attribute dugumleri."""
    korumali = set()
    for d in ast.walk(agac):
        if not isinstance(d, ast.Try):
            continue
        yakalar = False
        for h in d.handlers:
            tipler = (h.type.elts if isinstance(h.type, ast.Tuple)
                      else [h.type] if h.type is not None else [])
            if any(isinstance(t, ast.Name) and t.id == "AttributeError" for t in tipler):
                yakalar = True
        if not yakalar:
            continue
        for g in d.body:
            for i in ast.walk(g):
                if isinstance(i, ast.Attribute):
                    korumali.add(id(i))
    return korumali


def _py36_ihlalleri(kaynak, dosya="<kaynak>"):
    """Beyaz liste kapisi -> ["satir N: <ad> — <gerekce>", ...] (bos = temiz)."""
    agac = ast.parse(kaynak, dosya)
    bagli = _py36_bagli_adlar(agac)
    oz = _py36_oz_oznitelikler(agac)
    korumali = _py36_korumali_dugumler(agac)
    ihlal = []

    for d in ast.walk(agac):
        # 1) import edilen her modul icin 3.6 envanteri BULUNMALI (fail-closed)
        if isinstance(d, ast.Import):
            for a in d.names:
                if a.name not in PY36_MODUL and a.name.split(".")[0] not in PY36_MODUL:
                    ihlal.append("satir {}: {} — modul icin 3.6 envanteri YOK "
                                 "(PY36_MODUL'e ekle)".format(d.lineno, a.name))
        elif isinstance(d, ast.ImportFrom):
            m = d.module or ""
            kume = PY36_MODUL.get(m)
            if m not in PY36_MODUL:
                # Ithal edilen AD da raporlanir: `from functools import
                # cached_property` gibi bir 3.8 API'si ImportFrom ile "yerel ad"
                # kilifina girer, ADIYLA gorunmezse rapor yaniltir.
                for a in d.names:
                    ihlal.append("satir {}: {}.{} — modul icin 3.6 envanteri YOK "
                                 "(PY36_MODUL'e ekle)".format(d.lineno, m, a.name))
            elif kume is not None:
                for a in d.names:
                    if a.name not in kume:
                        ihlal.append("satir {}: {} — {} modulunun 3.6 envanterinde "
                                     "YOK".format(d.lineno, a.name, m))
        # 2) cozulmeyen her AD 3.6 builtins'inde olmali
        elif isinstance(d, ast.Name) and isinstance(d.ctx, ast.Load):
            if d.id not in bagli and d.id not in IZINLI_ADLAR:
                ihlal.append("satir {}: {} — 3.6 beyaz listesinde YOK "
                             "(yerel de degil)".format(d.lineno, d.id))
        # 3) kendi acmadigi her OZNITELIK 3.6 envanterinde olmali
        elif isinstance(d, ast.Attribute) and isinstance(d.ctx, ast.Load):
            if d.attr in oz:
                continue
            if d.attr in KORUMALI_YENI_API:
                if id(d) not in korumali:
                    ihlal.append("satir {}: .{} — {} (KORUMASIZ kullanim)".format(
                        d.lineno, d.attr, KORUMALI_YENI_API[d.attr]))
                continue
            if d.attr not in IZINLI_OZNITELIKLER:
                ihlal.append("satir {}: .{} — 3.6 beyaz listesinde YOK "
                             "(kendi oznitelIgi de degil)".format(d.lineno, d.attr))
    return ihlal


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
        self.assertEqual(yasak, [])
        # 3.7+ API kapisi ARTIK BEYAZ LISTE: eski kara liste yalniz sayili adi
        # arardi (ThreadingHTTPServer/removeprefix/...), listede olmayan yeni bir
        # API sessizce gecerdi. Simdi TERSI: kullanilan her ad 3.6 envanterinde
        # OLMAK ZORUNDA. Kapinin kendisi asagida ornekle dogrulanir.
        self.assertEqual(_py36_ihlalleri(kaynak, str(KANONIK)), [])
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

    def test_K5_beyaz_liste_kapisi_bos_degil(self):
        """Kapinin KENDISI olculur: bos kapi yazmamak icin negatif/pozitif kontrol.

        NEDEN: beyaz liste, koprunun BUGUN kullandigi adlara gore yazilirsa
        totolojiye duser ("gecen sey gecer"). Burada kapiya bilerek 3.7+ ornek
        verilir; DUSMEZSE kapi bostur. Ilk yedi ornek eski KARA LISTENIN
        kapsadigi adlardir (gerileme kanit), kalanlar kara listenin KACIRDIGI
        adlardir (bu isin gerekcesi).
        """
        eski_kara_liste = [
            ("ThreadingHTTPServer",
             "from http.server import ThreadingHTTPServer\ns = ThreadingHTTPServer\n"),
            ("breakpoint", "def f():\n    breakpoint()\n"),
            ("removeprefix", "def f(s):\n    return s.removeprefix('a')\n"),
            ("removesuffix", "def f(s):\n    return s.removesuffix('a')\n"),
            ("isqrt", "import math\ndef f(n):\n    return math.isqrt(n)\n"),
            ("cached_property", "from functools import cached_property\n"),
            ("fromisoformat",
             "import datetime\ndef f(s):\n    return datetime.date.fromisoformat(s)\n"),
        ]
        kara_listenin_kacirdiklari = [
            ("reconfigure", "import sys\nsys.stdout.reconfigure(encoding='utf-8')\n"),
            ("monotonic_ns", "import time\ndef f():\n    return time.monotonic_ns()\n"),
            ("isascii", "def f(s):\n    return s.isascii()\n"),
            ("nullcontext", "from contextlib import nullcontext\n"),
            ("prod", "import math\ndef f(x):\n    return math.prod(x)\n"),
            ("get_running_loop",
             "import asyncio\ndef f():\n    return asyncio.get_running_loop()\n"),
            ("importlib.metadata", "import importlib.metadata\n"),
        ]
        for etiket, ornek in eski_kara_liste + kara_listenin_kacirdiklari:
            with self.subTest(ornek=etiket):
                rapor = _py36_ihlalleri(ornek, "<negatif:{}>".format(etiket))
                self.assertTrue(rapor, "kapi GECIRDI (bos kapi): {}".format(etiket))
                self.assertIn(etiket, " | ".join(rapor),
                              "ihlal raporu adi vermiyor: {}".format(rapor))
        # pozitif kontrol: yalniz 3.6 API'si kullanan kod GECMELI (yanlis alarm yok)
        temiz = (
            "import json\n"
            "import time\n"
            "from collections import deque\n"
            "from urllib.parse import urlsplit\n"
            "def f(gelen):\n"
            "    d = deque(maxlen=3)\n"
            "    d.append(time.monotonic())\n"
            "    p = urlsplit('//' + gelen.strip())\n"
            "    return json.dumps({'h': p.hostname}).encode('utf-8')\n"
        )
        self.assertEqual(_py36_ihlalleri(temiz, "<pozitif>"), [])
        # KORUMALI istisna: reconfigure yalniz try/except AttributeError icinde gecer
        korumali = ("import sys\n"
                    "try:\n"
                    "    sys.stdout.reconfigure(encoding='utf-8')\n"
                    "except AttributeError:\n"
                    "    pass\n")
        self.assertEqual(_py36_ihlalleri(korumali, "<korumali>"), [])

    def test_K5_envanterin_kendisi_36_kalir(self):
        """Beyaz listenin GEVSEMEDIGI olculur (D-107: esik/kapsam gevsetilmez).

        (a) Sayilan builtins bugunku yorumlayicida GERCEKTEN var -> yazim hatasi
            kapisi. (b) 3.6 SONRASI eklendigi bilinen adlarin hicbiri envantere
            sizmamis -> envanteri genisletirken kapinin bosalmasi engellenir.
        """
        import builtins
        eksik = sorted(PY36_BUILTIN_ADLARI - set(dir(builtins)))
        self.assertEqual(eksik, [], "envanterde bugun var olmayan builtin (yazim hatasi?)")
        for ad in ("breakpoint", "aiter", "anext", "ExceptionGroup",
                   "BaseExceptionGroup", "EncodingWarning"):
            self.assertNotIn(ad, IZINLI_ADLAR, ad)
        for ad in ("ThreadingHTTPServer", "removeprefix", "removesuffix", "isascii",
                   "isqrt", "prod", "cached_property", "fromisoformat", "monotonic_ns",
                   "time_ns", "perf_counter_ns", "thread_time", "nullcontext",
                   "native_id", "block_on_close", "valid_signals", "raise_signal",
                   "strsignal", "stdlib_module_names", "breakpointhook", "bit_count",
                   "get_running_loop", "annotations", "reconfigure"):
            self.assertNotIn(ad, IZINLI_OZNITELIKLER, ad)
        self.assertIn("reconfigure", KORUMALI_YENI_API)   # tek daraltilmis istisna
        self.assertEqual(sorted(KORUMALI_YENI_API), ["reconfigure"])


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
