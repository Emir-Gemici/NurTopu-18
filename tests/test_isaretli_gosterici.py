"""T228 — JETSON ISARETLI GOSTERICI KAPILARI (scripts/isaretli_gosterici.py · jetson_paket/gosterici/ ·
jetson_baslat.sh GOSTERICI_KIP / ISARETLI_YAYIN).

NEDEN (REVIEW_LOG D-443 · results/fdr_sprint_20260910/H9_MK15/TASARIM.md §1-§5): Jetson'in isaretli
karesi MK15 video hattina (DP -> HDMI -> SIYI donusturucu) tam ekran verilir; yedek RTSP. Video KARAR
URETMEZ ama hakemin gordugu sey oldugu icin ASLA eski kareyi taze gibi gostermemeli. Jetson bu
makinede yok: x11/drm/rtsp'nin Jetson kosumu OLCULEMEDI; burada PC'de GERCEK bilesenlerle (gercek
kamera_koprusu HTTP sunucusu, gercek HTTP istemcisi, gercek bash betigi + shim'li sahte Jetson)
kilitlenir. Mock kutuphanesi yok; drm gozetmeni icin sahte surec nesnesi (gst-launch PC'de yok).

Kapilar:
  G1 durum mantigi (saf): taze -> CANLI; yas > 2 s -> BAYAT; > 5 s / hata / kare yok -> GORUNTU_YOK;
     esikler KESIN buyuk; BAYAT esigi on kayit (2 s), yok esigi = kamera_koprusu.AKIS_KARE_BEKLEME_S
  G2 tuval: GORUNTU_YOK eski kareyi ASLA cizmez; BAYAT kareyi gri+karartir ve bant tasir; CANLI
     kareyi gosterir; boyut hep 1280x720; Turkce sebep ASCII'lenir; tuval kaydi yazilir
  G3 KareCekici: gercek kamera_koprusu (dosya kaynagi) -> CANLI, kopru kapaninca GORUNTU_YOK;
     sahte HTTP: ayni sira tazelik UZATMAZ (-> BAYAT -> YOK), 503 JSON sebebi, bozuk JPEG
  G4 boru dizgileri: drm (souphttpsrc ... nvdrmvideosink set_mode=1 [conn_id]); GORUNTU YOK borusu
     eski kare kaynagi TASIMAZ; rtsp tuval/http (x264enc zerolatency ultrafast 2000 key-int-max 10,
     rtph264pay pay0, 1280x720, 5/1); --kaynak yol tasiyamaz, uclar kamera_koprusu'ndan
  G5 IP: SIYI .11/.12/.20/.25 REDDEDILIR; .30 kabul; anlamsiz adresler red; alt ag disi UYARI
  G6 CLI: --kuru her kip exit 0 (surecle de); yasak IP -> 2; x11 DISPLAY yok -> 2 (Linux; Windows'ta
     platform enjeksiyonuyla ayni yol); drm gst yok / rtsp gi yok -> 3
  G7 drm gozetmeni (sahte surec): YOK -> kirmizi boru; CANLI -> video; BAYAT -> video DURUR;
     hemen biten boru -> Argus uyarisi + bekleme (surec dongusu yok)
  G8 jetson_paket/gosterici: .desktop Exec (bash -n), DRM birimi gozcu kilidi + onkosul + VARSAYILAN
     KAPALI (systemd/ altinda degil, betik kurmaz), xorg sablonu TAHMIN basligi, kurulum belgesi
  G9 paket aynasi: KOPYALAR tasir, bayt-es, kod/ dizininden izole import; kilavuz kopyalar
  G10 jetson_baslat.sh: bash -n; varsayilan kapali (env'de gorunur, --isaretli-yayin YOK); x11 ile rpi
     --isaretli-yayin + gosterici bolumu; T227'siz paket [YOK] + exit 3, T227'li exit 0; gecersiz
     kip / yayin / port cakismasi exit 1; --kur T227'siz kurulu rpi ile HATA ve hic systemctl yok;
     port sabiti gostericiyle AYNI
Mutasyon (results/fdr_sprint_20260910/H9_MK15/t228/mutasyon_t228.py): bayat esigi kaldirilirsa,
yasak IP kontrolu kaldirilirsa, GORUNTU_YOK eski kareyi cizerse, jetson_baslat bayragi vermezse,
--kur T227 denetimi kaldirilirsa bu dosya DUSER.
"""
import contextlib
import io
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import cv2
import numpy as np

KOK = Path(__file__).resolve().parents[1]
for _y in (KOK / "scripts", KOK / "tests"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

import isaretli_gosterici as g  # noqa: E402
import kamera_koprusu as kk  # noqa: E402
import test_faz_b_jetson_baslat as jb  # noqa: E402  (shim'li sahte Jetson + bash yardimcilari)
from jetson_paket_hazirla import KOPYALAR  # noqa: E402

KANONIK = KOK / "scripts" / "isaretli_gosterici.py"
AYNA = KOK / "jetson_paket" / "kod" / "isaretli_gosterici.py"
GOSTERICI_DIZIN = KOK / "jetson_paket" / "gosterici"
DESKTOP = GOSTERICI_DIZIN / "navitas-isaretli-gosterici.desktop"
DRM_BIRIM = GOSTERICI_DIZIN / "navitas-isaretli-gosterici-drm.service"
XORG = GOSTERICI_DIZIN / "xorg-1280x720-edid-yok.conf"
KURULUM = GOSTERICI_DIZIN / "GOSTERICI_KURULUM.md"
YESIL = (0, 255, 0)


def _sessiz(*_a, **_k):
    return None


def _yesil_kare(w=640, h=360):
    k = np.zeros((h, w, 3), np.uint8)
    k[:] = YESIL
    return k


def _yesil_piksel(t):
    """Taze karenin (saf yesil) pikselleri: G yuksek, B ve R dusuk."""
    return int(np.count_nonzero((t[:, :, 1] > 200) & (t[:, :, 0] < 80) & (t[:, :, 2] < 80)))


def _piksel(t, y, x):
    return tuple(int(v) for v in t[y, x])


def _jpeg(renk=(0, 255, 0), w=160, h=90):
    k = np.zeros((h, w, 3), np.uint8)
    k[:] = renk
    ok, b = cv2.imencode(".jpg", k)
    assert ok
    return b.tobytes()


def _cagir(argv, **kw):
    """g.main'i surec icinde kos -> (cikis, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        kod = g.main(argv, **kw)
    return kod, out.getvalue(), err.getvalue()


def _bekle(kosul, tavan_s=8.0, adim_s=0.05):
    bitis = time.monotonic() + tavan_s
    while time.monotonic() < bitis:
        if kosul():
            return True
        time.sleep(adim_s)
    return kosul()


def _sahte_avi(dizin, n=20, boyut=(320, 240)):
    """cv2.VideoWriter ile n kareli MJPG AVI; her kare farkli."""
    yol = Path(dizin) / "t228_sahte.avi"
    w = cv2.VideoWriter(str(yol), cv2.VideoWriter_fourcc(*"MJPG"), 10.0, boyut)
    if not w.isOpened():
        raise unittest.SkipTest("YAPILAMADI: cv2.VideoWriter MJPG acilamadi (FFmpeg yok?)")
    for i in range(n):
        k = np.zeros((boyut[1], boyut[0], 3), np.uint8)
        k[:, :, 0] = (i * 12) % 256
        k[:, :, 1] = 128
        cv2.putText(k, str(i), (20, boyut[1] // 2), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
        w.write(k)
    w.release()
    return yol


class _SahteYayin:
    """Kucuk sahte HTTP yayini (efemer port): /kare.jpg davranisi testten surulur."""

    def __init__(self):
        self.kod = 200
        self.sira = "1"
        self.govde = _jpeg()
        self.son_hata = None
        self._kapali = False
        dis = self

        class _Ist(BaseHTTPRequestHandler):
            def log_message(self, *_a):
                pass

            def do_GET(self):
                if self.path.split("?", 1)[0] != kk.KARE_YOLU:
                    self.send_response(404)
                    self.end_headers()
                    return
                if dis.kod == 200:
                    self.send_response(200)
                    self.send_header("Content-Type", "image/jpeg")
                    self.send_header("Content-Length", str(len(dis.govde)))
                    if dis.sira is not None:
                        self.send_header("X-Kare-Sira", dis.sira)
                    self.end_headers()
                    self.wfile.write(dis.govde)
                    return
                govde = json.dumps({"hata": "kaynak acik degil ya da taze kare yok",
                                    "son_hata": dis.son_hata}).encode("utf-8")
                self.send_response(dis.kod)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(govde)))
                self.end_headers()
                self.wfile.write(govde)

        self.sunucu = HTTPServer(("127.0.0.1", 0), _Ist)
        self.port = self.sunucu.server_address[1]
        self.iplik = threading.Thread(target=self.sunucu.serve_forever,
                                      kwargs={"poll_interval": 0.05}, daemon=True)
        self.iplik.start()

    @property
    def kok(self):
        return "http://127.0.0.1:{}".format(self.port)

    def kapat(self):
        if self._kapali:
            return
        self._kapali = True
        self.sunucu.shutdown()
        self.sunucu.server_close()
        self.iplik.join(2.0)


# ── G1 ────────────────────────────────────────────────────────────────────────
class DurumMantigi(unittest.TestCase):
    def test_G1_taze_bayat_yok(self):
        self.assertEqual(g.ekran_durumu(10.0, 9.5).durum, g.DURUM_CANLI)
        d = g.ekran_durumu(10.0, 7.5)
        self.assertEqual(d.durum, g.DURUM_BAYAT, "yas 2,5 s > 2 s -> BAYAT (on kayit)")
        self.assertAlmostEqual(d.yas_s, 2.5)
        self.assertIn("2.5 s eski", d.sebep)
        d = g.ekran_durumu(10.0, 4.0)
        self.assertEqual(d.durum, g.DURUM_YOK)
        self.assertIn("6.0 s", d.sebep)

    def test_G1_esikler_kesin_buyuk_ve_on_kayitli(self):
        self.assertEqual(g.BAYAT_ESIGI_S, 2.0, "on kayit: kare yasi > 2 s -> BAYAT (gevsetilmez)")
        self.assertEqual(g.GORUNTU_YOK_ESIGI_S, float(kk.AKIS_KARE_BEKLEME_S),
                         "yok esigi koprunun taze kare tavaniyla AYNI")
        self.assertEqual(g.ekran_durumu(100.0, 98.0).durum, g.DURUM_CANLI)      # tam 2 s
        self.assertEqual(g.ekran_durumu(100.0, 97.99).durum, g.DURUM_BAYAT)
        self.assertEqual(g.ekran_durumu(100.0, 95.0).durum, g.DURUM_BAYAT)      # tam 5 s
        self.assertEqual(g.ekran_durumu(100.0, 94.99).durum, g.DURUM_YOK)
        # esigi asan yas metinde esikten kucuk/esit OKUNMAZ (0,1'e yukari; PC dumani bulgusu)
        self.assertIn("kare 2.1 s eski (> 2 s)", g.ekran_durumu(100.0, 97.96).sebep)
        self.assertIn("son taze kare 5.1 s once (> 5 s)", g.ekran_durumu(100.0, 94.99).sebep)

    def test_G1_hata_ve_kare_yok_her_zaman_GORUNTU_YOK(self):
        d = g.ekran_durumu(10.0, 9.9, hata="yayin erisilemiyor (x): refused")
        self.assertEqual(d.durum, g.DURUM_YOK, "taze kare olsa da erisilemeyen yayin CANLI olmaz")
        self.assertIn("erisilemiyor", d.sebep)
        d = g.ekran_durumu(10.0, None)
        self.assertEqual((d.durum, d.yas_s), (g.DURUM_YOK, None))
        self.assertEqual(g.ekran_durumu(5.0, 6.0).yas_s, 0.0, "negatif yas yok")


# ── G2 ────────────────────────────────────────────────────────────────────────
class Tuval(unittest.TestCase):
    def test_G2_GORUNTU_YOK_eski_kareyi_ASLA_cizmez(self):
        kare = _yesil_kare()
        for d in (g.EkranDurumu(g.DURUM_YOK, "yayin erisilemiyor", 7.0),
                  g.EkranDurumu(g.DURUM_YOK, "henuz kare alinmadi", None)):
            with self.subTest(sebep=d.sebep):
                t = g.tuval_ciz(d, kare, saat_metni="12:00:00")
                self.assertEqual(t.shape, (g.TUVAL_YUKSEKLIK, g.TUVAL_GENISLIK, 3))
                self.assertEqual(_yesil_piksel(t), 0, "GORUNTU YOK ekraninda eski kare pikseli var")
                self.assertEqual(_piksel(t, 5, 5), g.KIRMIZI_ZEMIN)
                beyaz = np.count_nonzero((t[:, :, 0] > 200) & (t[:, :, 1] > 200) & (t[:, :, 2] > 200))
                self.assertGreater(int(beyaz), 2000, "GORUNTU YOK yazisi yok")
        # savunma: kare None iken CANLI/BAYAT istense de kirmizi ekran
        for durum in (g.DURUM_CANLI, g.DURUM_BAYAT):
            t = g.tuval_ciz(g.EkranDurumu(durum, "x", 0.1), None)
            self.assertEqual(_piksel(t, 5, 5), g.KIRMIZI_ZEMIN, durum)

    def test_G2_BAYAT_kareyi_karartir_ve_bant_tasir(self):
        t = g.tuval_ciz(g.EkranDurumu(g.DURUM_BAYAT, "kare 3.0 s eski (> 2 s)", 3.0), _yesil_kare())
        self.assertEqual(t.shape, (720, 1280, 3))
        self.assertEqual(_yesil_piksel(t), 0, "BAYAT kare taze renginde gosteriliyor")
        self.assertEqual(_piksel(t, 5, 5), g.AMBER, "ust BAYAT bandi yok")
        alt = t[720 // 5 + 10:, :]
        self.assertLessEqual(int(alt.max()), int(255 * g.BAYAT_KARARTMA) + 1, "kare karartilmamis")
        self.assertGreater(float(alt.mean()), 20.0, "karartilmis kare yine de gorunur olmali")

    def test_G2_CANLI_kareyi_gosterir_ve_bantlar(self):
        t = g.tuval_ciz(g.EkranDurumu(g.DURUM_CANLI, "", 0.4), _yesil_kare())
        self.assertEqual(_piksel(t, 360, 640), YESIL)
        t = g.tuval_ciz(g.EkranDurumu(g.DURUM_CANLI, "", 0.1), _yesil_kare(480, 360))   # 4:3
        self.assertEqual(_piksel(t, 360, 10), (0, 0, 0), "4:3 kare yanlardan bantlanmali")
        self.assertEqual(_piksel(t, 360, 640), YESIL)

    def test_G2_turkce_sebep_ascii_ve_uzun_sebep_tasmaz_tuval_kaydi(self):
        self.assertEqual(g.ascii_metin("bağlantı reddedildi — ş"), "baglanti reddedildi - s")
        uzun = "yayin erisilemiyor (http://127.0.0.1:8081/kare.jpg): " + "x" * 300
        t = g.tuval_ciz(g.EkranDurumu(g.DURUM_YOK, uzun, None), None)
        self.assertEqual(t.shape, (720, 1280, 3))
        d = tempfile.mkdtemp(prefix="navitas_t228_tuval_")
        self.addCleanup(shutil.rmtree, d, True)
        with contextlib.redirect_stdout(io.StringIO()):
            k = g.TuvalKaydi(d)
            k.durum_degisti(g.DURUM_YOK, t)
            k.son(t)
        self.assertEqual(sorted(os.listdir(d)), ["01_GORUNTU_YOK.jpg", "son.jpg"])


# ── G3 ────────────────────────────────────────────────────────────────────────
class KareCekiciSahteYayin(unittest.TestCase):
    def setUp(self):
        self.y = _SahteYayin()
        self.addCleanup(self.y.kapat)
        self.t = [0.0]
        self.c = g.KareCekici(self.y.kok, saat=lambda: self.t[0], log=_sessiz)

    def _durum(self, simdi):
        _k, son_t, h, _s = self.c.anlik()
        return g.ekran_durumu(simdi, son_t, h)

    def test_G3_ayni_sira_tazelik_UZATMAZ_bayat_sonra_yok(self):
        self.assertTrue(self.c.cek_bir_kez())
        self.assertEqual(self._durum(0.5).durum, g.DURUM_CANLI)
        self.t[0] = 1.0
        self.assertFalse(self.c.cek_bir_kez(), "ayni sira + ayni govde YENI kare degil")
        self.t[0] = 2.5
        self.assertFalse(self.c.cek_bir_kez())
        self.assertEqual(self._durum(2.5).durum, g.DURUM_BAYAT,
                         "yayin ayakta ama kare 2,5 s yeni degil -> BAYAT")
        self.t[0] = 5.5
        self.c.cek_bir_kez()
        self.assertEqual(self._durum(5.5).durum, g.DURUM_YOK)
        self.y.sira, self.y.govde = "2", _jpeg((0, 0, 255))
        self.t[0] = 6.0
        self.assertTrue(self.c.cek_bir_kez())
        self.assertEqual(self._durum(6.1).durum, g.DURUM_CANLI)
        kare, _t, _h, sira = self.c.anlik()
        self.assertEqual(sira, "2")
        self.assertGreater(float(kare[:, :, 2].mean()), 200.0, "yeni kare cozulmedi")

    def test_G3_sirasiz_kaynakta_icerik_imzasi(self):
        self.y.sira = None
        self.assertTrue(self.c.cek_bir_kez())
        self.assertFalse(self.c.cek_bir_kez())
        self.y.govde = _jpeg((255, 0, 0))
        self.assertTrue(self.c.cek_bir_kez())
        # yayin yeniden basladi: sira ayni olabilir ama icerik farkli -> yeni
        self.y.sira = "1"
        self.assertTrue(self.c.cek_bir_kez())
        self.y.govde = _jpeg((0, 0, 255))
        self.assertTrue(self.c.cek_bir_kez())

    def test_G3_503_sebebi_ve_geri_gelis(self):
        self.assertTrue(self.c.cek_bir_kez())
        self.y.kod, self.y.son_hata = 503, "kaynak acilamadi (deneme 3)"
        self.t[0] = 0.2
        self.assertFalse(self.c.cek_bir_kez())
        d = self._durum(0.3)
        self.assertEqual(d.durum, g.DURUM_YOK, "503 iken son kare 0,3 s yasli olsa da GORUNTU YOK")
        self.assertIn("HTTP 503", d.sebep)
        self.assertIn("kaynak acilamadi", d.sebep)
        self.y.kod, self.y.sira, self.y.govde = 200, "9", _jpeg((10, 20, 30))
        self.t[0] = 0.4
        self.assertTrue(self.c.cek_bir_kez())
        self.assertEqual(self._durum(0.5).durum, g.DURUM_CANLI)

    def test_G3_bozuk_jpeg_ve_erisilemeyen_yayin(self):
        self.y.govde, self.y.sira = b"bu bir jpeg degil", "5"
        self.assertFalse(self.c.cek_bir_kez())
        self.assertIn("JPEG cozulemedi", self._durum(0.0).sebep)
        self.y.kapat()
        self.assertFalse(self.c.cek_bir_kez())
        d = self._durum(0.0)
        self.assertEqual(d.durum, g.DURUM_YOK)
        self.assertIn("erisilemiyor", d.sebep)
        self.assertEqual(self.c.sayaclar()["hata"], 2)


class KareCekiciGercekKopru(unittest.TestCase):
    def test_G3_gercek_kopru_CANLI_kopru_kapaninca_GORUNTU_YOK(self):
        d = tempfile.mkdtemp(prefix="navitas_t228_kopru_")
        self.addCleanup(shutil.rmtree, d, True)
        avi = _sahte_avi(d)
        sunucu, uretici = kk.kopru_kur(str(avi), port=0, log_aralik_s=0, log=_sessiz)
        iplik = threading.Thread(target=sunucu.serve_forever, kwargs={"poll_interval": 0.05},
                                 daemon=True)
        iplik.start()
        kapali = [False]

        def kapat():
            if not kapali[0]:
                kapali[0] = True
                kk.kopru_kapat(sunucu, uretici)
                iplik.join(2.0)

        self.addCleanup(kapat)
        c = g.KareCekici("http://127.0.0.1:{}".format(sunucu.server_address[1]), log=_sessiz)
        self.assertTrue(_bekle(c.cek_bir_kez), "kopruden kare gelmedi")
        kare, son_t, h, sira = c.anlik()
        self.assertIsNone(h)
        self.assertIsNotNone(sira, "kopru X-Kare-Sira basligi gondermeli")
        self.assertEqual(kare.shape, (240, 320, 3))
        self.assertEqual(g.ekran_durumu(time.monotonic(), son_t, h).durum, g.DURUM_CANLI)
        self.assertTrue(_bekle(c.cek_bir_kez), "ikinci yeni kare gelmedi")
        self.assertNotEqual(c.anlik()[3], sira)
        kapat()
        self.assertFalse(c.cek_bir_kez())
        _k, son_t, h, _s = c.anlik()
        d2 = g.ekran_durumu(time.monotonic(), son_t, h)
        self.assertEqual(d2.durum, g.DURUM_YOK)
        self.assertIn("erisilemiyor", d2.sebep)


# ── G4 ────────────────────────────────────────────────────────────────────────
class BoruDizgileri(unittest.TestCase):
    def test_G4_drm_borusu_elemanlar_sirali_ve_parametreler(self):
        b = g.drm_boru()
        self.assertEqual(g.boru_elemanlari(b),
                         ["souphttpsrc", "multipartdemux", "jpegdec", "nvvidconv", "nvdrmvideosink"])
        for parca in ("location=http://127.0.0.1:8081" + kk.VIDEO_YOLU, "video/x-raw(memory:NVMM)",
                      "width=1280", "height=720", "nvdrmvideosink set_mode=1"):
            self.assertIn(parca, b)
        self.assertNotIn("conn_id", b)
        self.assertIn("nvdrmvideosink set_mode=1 sync=false conn_id=2", g.drm_boru(conn_id=2))
        self.assertNotIn("kmssink", b)

    def test_G4_drm_GORUNTU_YOK_borusu_eski_kare_kaynagi_TASIMAZ(self):
        b = g.drm_goruntu_yok_boru('yayin "erisilemiyor"! (x)')
        el = g.boru_elemanlari(b)
        self.assertEqual(el[0], "videotestsrc")
        self.assertIn("textoverlay", el)
        self.assertEqual(el[-1], "nvdrmvideosink")
        self.assertNotIn("souphttpsrc", b, "GORUNTU YOK borusu yayini (eski kareyi) okuyamaz")
        self.assertIn('text="GORUNTU YOK - yayin erisilemiyor (x)"', b)
        self.assertEqual(b.count('"'), 4, "tirnak/unlem kacisi: text=... ve font-desc=... disinda tirnak yok")

    def test_G4_rtsp_tuval_ve_http_borulari(self):
        for tur in (g.RTSP_BORU_TUVAL, g.RTSP_BORU_HTTP):
            with self.subTest(tur=tur):
                b = g.rtsp_boru(tur)
                self.assertTrue(b.startswith("( ") and b.endswith(" )"), "GstRtspServer fabrika bicimi")
                for parca in ("x264enc tune=zerolatency speed-preset=ultrafast bitrate=2000 "
                              "key-int-max=10", "rtph264pay name=pay0", "width=1280", "height=720",
                              "framerate=5/1"):
                    self.assertIn(parca, b)
                self.assertEqual(g.boru_elemanlari(b)[-2:], ["x264enc", "rtph264pay"])
        tuval = g.rtsp_boru(g.RTSP_BORU_TUVAL)
        self.assertEqual(g.boru_elemanlari(tuval), ["appsrc", "videoconvert", "x264enc", "rtph264pay"])
        self.assertIn("appsrc name={} ".format(g.RTSP_APPSRC_ADI), tuval)
        self.assertIn("format=BGR", tuval)
        http = g.boru_elemanlari(g.rtsp_boru(g.RTSP_BORU_HTTP))
        self.assertEqual(http[:3], ["souphttpsrc", "multipartdemux", "jpegdec"])
        self.assertIn("videoconvert", http)
        self.assertEqual(g.rtsp_url("192.168.144.30"), "rtsp://192.168.144.30:8554/isaretli")
        self.assertEqual((g.RTSP_FPS, g.X264_BITRATE_KBPS, g.X264_KEY_INT_MAX), (5, 2000, 10))
        with self.assertRaises(ValueError):
            g.rtsp_boru("udp")

    def test_G4_kaynak_kok_yol_tasiyamaz_uclar_kopruden(self):
        self.assertEqual(g.kaynak_kok("http://127.0.0.1:8081/"), "http://127.0.0.1:8081")
        for kotu in ("http://127.0.0.1:8081/kare.jpg", "rtsp://127.0.0.1:8554", "127.0.0.1:8081",
                     "http://127.0.0.1:abc", "http://:8081", "http://127.0.0.1:8081/?a=1"):
            with self.subTest(kaynak=kotu), self.assertRaises(ValueError):
                g.kaynak_kok(kotu)
        self.assertEqual((g.KARE_YOLU, g.VIDEO_YOLU), (kk.KARE_YOLU, kk.VIDEO_YOLU))


# ── G5 ────────────────────────────────────────────────────────────────────────
class JetsonIp(unittest.TestCase):
    def test_G5_SIYI_sabitleri_REDDEDILIR(self):
        self.assertEqual(set(g.SIYI_SABIT_IP), {"192.168.144.11", "192.168.144.12",
                                               "192.168.144.20", "192.168.144.25"})
        for son in (11, 12, 20, 25):
            with self.subTest(son=son):
                with self.assertRaises(ValueError) as cm:
                    g.jetson_ip_dogrula("192.168.144.{}".format(son))
                self.assertIn("YASAK", str(cm.exception))

    def test_G5_oneri_kabul_anlamsiz_red_alt_ag_disi_uyari(self):
        self.assertEqual(g.JETSON_IP_ONERI, "192.168.144.30")
        self.assertEqual(g.jetson_ip_dogrula(" 192.168.144.30 "), ("192.168.144.30", []))
        for kotu in ("0.0.0.0", "224.0.0.1", "255.255.255.255", "192.168.144.0",
                     "192.168.144.255", "192.168.144.300", "jetson.local", "", "::1"):
            with self.subTest(ip=kotu), self.assertRaises(ValueError):
                g.jetson_ip_dogrula(kotu)
        ip, uyari = g.jetson_ip_dogrula("10.0.0.11")
        self.assertEqual(ip, "10.0.0.11", "SIYI alt agi disinda .11 SIYI adresi degildir")
        self.assertTrue(uyari and "SIYI alt aginda" in uyari[0], uyari)


# ── G6 ────────────────────────────────────────────────────────────────────────
class Cli(unittest.TestCase):
    def test_G6_kuru_her_kip_exit_0_hicbir_sey_acmaz(self):
        for kip in g.KIPLER:
            with self.subTest(kip=kip):
                kod, out, err = _cagir(["--kip", kip, "--kuru"], ortam={"DISPLAY": ":0"},
                                       platform="linux")
                self.assertEqual(kod, 0, out + err)
                self.assertIn("HICBIR SEY ACILMADI", out)
                self.assertIn("KARAR URETMEZ", out)
                self.assertIn("KOMUT (Jetson): /usr/bin/python3 ~/navitas/scripts/"
                              "isaretli_gosterici.py --kip " + kip, out)
                self.assertTrue(out.rstrip().endswith("KURU: tamam (cikis 0) — hicbir sey acilmadi"))
        _k, out, _e = _cagir(["--kip", "drm", "--kuru", "--conn-id", "3"])
        for satir in g.DRM_ON_KOSUL:
            self.assertIn(satir + "\n", out)
        self.assertIn("gst-launch-1.0 -e 'souphttpsrc location=http://127.0.0.1:8081/video", out)
        self.assertIn("nvdrmvideosink set_mode=1 sync=false conn_id=3", out)
        self.assertIn("[UYARI] nvidia-drm", out)
        self.assertIn("Argus", out)
        _k, out, _e = _cagir(["--kip", "rtsp", "--kuru"])
        self.assertIn("rtsp://192.168.144.30:8554/isaretli", out)
        self.assertIn("x264enc tune=zerolatency", out)
        _k, out, _e = _cagir(["--kip", "x11", "--kuru"], ortam={}, platform="linux")
        self.assertIn("[UYARI] DISPLAY yok", out, "kuru DISPLAY eksigini soyler ama cikis yine 0")
        _k, out, _e = _cagir(["--kip", "rtsp", "--jetson-ip", "10.1.2.3", "--kuru"])
        self.assertIn("[UYARI] --jetson-ip 10.1.2.3 SIYI alt aginda", out)

    def test_G6_kuru_surec_olarak_exit_0(self):
        for kip in g.KIPLER:
            with self.subTest(kip=kip):
                p = subprocess.run([sys.executable, "-B", str(KANONIK), "--kip", kip, "--kuru"],
                                   capture_output=True, text=True, encoding="utf-8",
                                   errors="replace", timeout=60)
                self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
                self.assertIn("KURU: tamam", p.stdout)

    def test_G6_yasak_ip_cikis_2_kuru_da(self):
        for ip in ("192.168.144.11", "192.168.144.25"):
            with self.subTest(ip=ip):
                err = io.StringIO()
                with self.assertRaises(SystemExit) as cm, contextlib.redirect_stderr(err):
                    g.main(["--kip", "rtsp", "--jetson-ip", ip, "--kuru"])
                self.assertEqual(cm.exception.code, 2)
                self.assertIn("YASAK", err.getvalue())
        p = subprocess.run([sys.executable, "-B", str(KANONIK), "--kip", "rtsp", "--jetson-ip",
                            "192.168.144.12", "--kuru"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=60)
        self.assertEqual(p.returncode, 2, p.stdout + p.stderr)
        self.assertIn("YASAK", p.stderr)
        self.assertNotIn("KURU: tamam", p.stdout)

    def test_G6_x11_DISPLAY_yoksa_cikis_2_pencere_acilmaz(self):
        argv = ["--kip", "x11", "--sure", "0.5", "--kaynak", "http://127.0.0.1:9"]
        kod, _out, err = _cagir(argv, ortam={}, platform="linux")
        self.assertEqual(kod, 2, err)
        self.assertIn("DISPLAY yok", err)
        kod, _out, err = _cagir(argv, ortam={"WAYLAND_DISPLAY": "wayland-0"}, platform="linux")
        self.assertEqual(kod, 2, err)
        self.assertIn("WaylandEnable=false", err)
        self.assertIsNone(g.ekran_ortami_hatasi({}, "win32"), "Windows'ta DISPLAY denetimi yok")
        self.assertIsNone(g.ekran_ortami_hatasi({"DISPLAY": ":0"}, "linux"))

    @unittest.skipUnless(sys.platform.startswith("linux"),
                         "Linux'a ozgu surec kapisi — Windows'ta ayni yol platform enjeksiyonuyla "
                         "test_G6_x11_DISPLAY_yoksa_cikis_2_pencere_acilmaz'da sinandi")
    def test_G6_x11_DISPLAY_yok_surec_cikis_2_linux(self):
        env = {k: v for k, v in os.environ.items() if k not in ("DISPLAY", "WAYLAND_DISPLAY")}
        p = subprocess.run([sys.executable, "-B", str(KANONIK), "--kip", "x11", "--sure", "1"],
                           env=env, capture_output=True, text=True, timeout=60)
        self.assertEqual(p.returncode, 2, p.stdout + p.stderr)
        self.assertIn("DISPLAY yok", p.stderr)

    def test_G6_drm_gst_yoksa_3_rtsp_gi_yoksa_3(self):
        sinandi = 0
        if shutil.which("gst-launch-1.0") is None:
            kod, _o, err = _cagir(["--kip", "drm", "--sure", "0.1"])
            self.assertEqual(kod, g.CIKIS_BAGIMLILIK, err)
            self.assertIn("gst-launch-1.0 yok", err)
            sinandi += 1
        if not g.gi_durumu()[0]:
            kod, _o, err = _cagir(["--kip", "rtsp", "--sure", "0.1"])
            self.assertEqual(kod, g.CIKIS_BAGIMLILIK, err)
            self.assertIn("gir1.2-gst-rtsp-server-1.0", err)
            sinandi += 1
        if not sinandi:
            self.skipTest("YAPILAMADI: bu makinede gst-launch-1.0 ve gi var — bagimlilik-yok yolu "
                          "sinanamaz")


# ── G7 ────────────────────────────────────────────────────────────────────────
class _SahteSurec:
    """subprocess.Popen yerine: poll/terminate/kill/wait. `omur` poll sayisi sonra kendiliginden biter."""

    def __init__(self, argv, kayit, omur=None):
        self.argv = argv
        self.returncode = None
        self.sonlandirildi = False
        self.kalan = omur
        kayit.append(self)

    def poll(self):
        if self.returncode is None and self.kalan is not None:
            if self.kalan <= 0:
                self.returncode = 1
            else:
                self.kalan -= 1
        return self.returncode

    def terminate(self):
        self.sonlandirildi = True
        self.returncode = -15

    def kill(self):
        self.returncode = -9

    def wait(self, timeout=None):
        if self.returncode is None:
            self.returncode = 0
        return self.returncode


YOK = g.EkranDurumu(g.DURUM_YOK, "yayin erisilemiyor", None)
CANLI = g.EkranDurumu(g.DURUM_CANLI, "", 0.2)
BAYAT = g.EkranDurumu(g.DURUM_BAYAT, "kare 2.4 s eski (> 2 s)", 2.4)


class DrmGozetmen(unittest.TestCase):
    def _kos(self, durumlar, omur=None):
        kalan = list(durumlar)
        bitti = {"e": False}

        def durum_oku():
            d = kalan.pop(0)
            if not kalan:
                bitti["e"] = True
            return d

        saat = [0.0]
        uykular = []

        def uyku(s):
            uykular.append(s)
            saat[0] += s

        kayit = []
        loglar = []
        video = ["gst-launch-1.0", "-e", g.drm_boru()]
        n = g.drm_gozetmen(video, lambda sebep: ["gst-launch-1.0", g.drm_goruntu_yok_boru(sebep)],
                           durum_oku, lambda argv: _SahteSurec(argv, kayit, omur),
                           lambda: bitti["e"], uyku=uyku, saat=lambda: saat[0],
                           log=lambda m, kirmizi=False: loglar.append((kirmizi, m)))
        return n, kayit, loglar, uykular

    def test_G7_yok_kirmizi_canli_video_bayatta_video_DURUR(self):
        n, kayit, loglar, _u = self._kos([YOK, YOK, CANLI, CANLI, CANLI, BAYAT, BAYAT, YOK])
        self.assertEqual(n, 3)
        yok1, video, yok2 = kayit
        self.assertIn("videotestsrc", yok1.argv[-1])
        self.assertNotIn("souphttpsrc", yok1.argv[-1])
        self.assertEqual(video.argv[:2], ["gst-launch-1.0", "-e"])
        self.assertIn("souphttpsrc", video.argv[-1])
        self.assertTrue(yok1.sonlandirildi, "yayin gelince kirmizi boru durdurulmali")
        self.assertTrue(video.sonlandirildi,
                        "kare BAYAT olunca video borusu DURMALI (son kare ekranda kalmasin)")
        self.assertIn("kare 2.4 s eski", yok2.argv[-1])
        self.assertTrue(any(k and "GORUNTU YOK" in m for k, m in loglar), loglar)

    def test_G7_hemen_biten_boru_uyari_ve_bekleme_surec_dongusu_yok(self):
        n, kayit, loglar, uykular = self._kos([CANLI, CANLI, CANLI, CANLI], omur=0)
        self.assertEqual(n, 4)
        self.assertEqual(uykular.count(g.DRM_ASGARI_OMUR_S), 3, uykular)
        self.assertGreaterEqual(sum(1 for k, m in loglar if k and "Argus" in m), 3, loglar)
        self.assertFalse(any(s.sonlandirildi for s in kayit), "kendiliginden biten surec oldurulmez")


# ── G8 ────────────────────────────────────────────────────────────────────────
def _desktop_alanlari(metin):
    alanlar, bolum = {}, None
    for s in metin.splitlines():
        s = s.rstrip("\r")
        if not s or s.startswith("#"):
            continue
        if s.startswith("["):
            bolum = s
            continue
        k, _, v = s.partition("=")
        alanlar[(bolum, k)] = v
    return alanlar


class GostericiDosyalari(unittest.TestCase):
    def test_G8_desktop_Exec_x11_ve_kabuk_sozdizimi(self):
        a = _desktop_alanlari(DESKTOP.read_text(encoding="utf-8"))
        de = "[Desktop Entry]"
        self.assertEqual(a[(de, "Type")], "Application")
        self.assertEqual(a[(de, "X-GNOME-Autostart-enabled")], "true")
        self.assertNotIn("%", a[(de, "Exec")], "Exec'te kacissiz % alan kodu olamaz")
        argv = shlex.split(a[(de, "Exec")])
        self.assertEqual(argv[:2], ["sh", "-c"])
        self.assertEqual(len(argv), 3)
        betik = argv[2]
        port = urllib.parse.urlsplit(g.VARSAYILAN_KAYNAK).port
        for parca in ("/usr/bin/python3", "/navitas/scripts/isaretli_gosterici.py", "--kip x11",
                      "s/^ISARETLI_YAYIN=//p", "/etc/navitas.env", "127.0.0.1:{}".format(port),
                      "0|2) exit"):
            self.assertIn(parca, betik)
        p = subprocess.run([jb._bash(), "-n", "-c", betik], capture_output=True, text=True, timeout=30)
        self.assertEqual(p.returncode, 0, p.stderr)

    def test_G8_drm_birimi_gozcu_onkosul_VARSAYILAN_KAPALI(self):
        a = jb._birim_oku_metin(DRM_BIRIM.read_text(encoding="utf-8"))
        jb._gozcu_kilidi(self, a, DRM_BIRIM.stem)
        s = a["Service"]
        onler = s.get("ExecStartPre", [])
        self.assertTrue(any("systemctl stop gdm" in x for x in onler), onler)
        self.assertTrue(any("loginctl terminate-seat seat0" in x for x in onler), onler)
        self.assertTrue(any(re.search(r"modprobe nvidia-drm modeset=1$", x) for x in onler), onler)
        self.assertTrue(all(x.lstrip("-").startswith("+") for x in onler),
                        "onkosullar tam yetkiyle ('+') kosmali: {}".format(onler))
        ex = s["ExecStart"][0]
        self.assertTrue(ex.startswith("/usr/bin/env ${KAMERA_PYTHON} "
                                      "/home/navitas/navitas/scripts/isaretli_gosterici.py"), ex)
        self.assertIn("--kip drm", ex)
        self.assertIn("--kaynak http://${ISARETLI_YAYIN}", ex)
        self.assertIn("video", " ".join(s.get("SupplementaryGroups", [])))
        metin = DRM_BIRIM.read_text(encoding="utf-8")
        for parca in ("VARSAYILAN KAPALI", "Argus", "3 fps", "DOGRULANACAK"):
            self.assertIn(parca, metin)
        # VARSAYILAN KAPALI: systemd/ altinda DEGIL, jetson_baslat birim listelerinde YOK
        self.assertFalse((jb.BIRIM_DIZIN / DRM_BIRIM.name).exists())
        betik = jb.BETIK.read_text(encoding="utf-8")
        self.assertNotIn("gosterici", re.search(r'^TUM_BIRIMLER="([^"]*)"', betik, re.M).group(1))
        self.assertNotIn("gosterici", re.search(r"^birimler\(\) \{.*?^\}", betik, re.M | re.S).group(0))
        env_anahtar = re.search(r"^ENV_ANAHTARLAR=\(([^)]*)\)", betik, re.M | re.S).group(1).split()
        for v in ("KAMERA_PYTHON", "ISARETLI_YAYIN", "GOSTERICI_KIP"):
            self.assertIn(v, env_anahtar, "birim ${} degiskenini /etc/navitas.env'den okur".format(v))

    def test_G8_xorg_sablonu_TAHMIN_basligi_ve_720p(self):
        metin = XORG.read_text(encoding="utf-8")
        ilk = metin.splitlines()[0]
        self.assertIn("TAHMIN", ilk)
        self.assertIn("DOGRULANACAK", ilk)
        m = re.search(r'^\s*Modeline\s+"1280x720_60"\s+([\d.]+)\s+1280\s+\d+\s+\d+\s+(\d+)\s+720\s+'
                      r'\d+\s+\d+\s+(\d+)', metin, re.M)
        self.assertIsNotNone(m, "1280x720 Modeline yok")
        pclk, htop, vtop = float(m.group(1)), int(m.group(2)), int(m.group(3))
        self.assertAlmostEqual(pclk * 1e6 / (htop * vtop), 60.0, places=3)
        for parca in ("AllowNonEdidModes", '"nvidia"', "GERI ALMA", "Xorg.0.log"):
            self.assertIn(parca, metin)

    def test_G8_kurulum_belgesi_kapsami(self):
        m = KURULUM.read_text(encoding="utf-8")
        for parca in ("AutomaticLoginEnable=true", "WaylandEnable=false", "~/.config/autostart",
                      "DisplayPort", "DP→HDMI", "Mini HDMI", "192.168.144.25", "setip.txt",
                      "rtsp://192.168.144.25:8554/main.264", "Camera 1", "EDID", "Argus", "3 fps",
                      "ÖLÇÜLEMEDİ", "kmssink", "nvdrmvideosink", "192.168.144.30",
                      "gir1.2-gst-rtsp-server-1.0", "KARAR ÜRETMEZ"):
            self.assertIn(parca, m)
        for dosya in (DESKTOP, DRM_BIRIM, XORG):
            self.assertIn(dosya.name, m)


# ── G9 ────────────────────────────────────────────────────────────────────────
class PaketAynasi(unittest.TestCase):
    def test_G9_KOPYALAR_tasir_bayt_es(self):
        self.assertEqual(KOPYALAR.get(KANONIK), AYNA, "isaretli_gosterici.py KOPYALAR'da yok")
        self.assertTrue(AYNA.is_file(), "paket kopyasi yok — scripts/jetson_paket_hazirla.py")
        self.assertEqual(KANONIK.read_bytes(), AYNA.read_bytes(), "paket kopyasi bayat")

    def test_G9_paket_kod_dizininden_izole_import(self):
        kod = ("import pathlib,sys; p=pathlib.Path({!r}).resolve(); "
               "sys.path[:]=[str(p)]+[x for x in sys.path if x not in ('',str(p))]; "
               "import isaretli_gosterici as g; "
               "assert pathlib.Path(g.__file__).resolve().parent == p; "
               "assert pathlib.Path(g._kk.__file__).resolve().parent == p; "
               "assert g.KARE_YOLU == g._kk.KARE_YOLU; "
               "print('GOSTERICI_IMPORT=OK')").format(str(AYNA.parent))
        p = subprocess.run([sys.executable, "-B", "-c", kod], cwd=str(AYNA.parent),
                           capture_output=True, text=True, timeout=60)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("GOSTERICI_IMPORT=OK", p.stdout)

    def test_G9_kilavuz_kurulum_blogu_kopyalar(self):
        for k in (KOK / "JETSON_KILAVUZ.md", KOK / "jetson_paket" / "JETSON_KILAVUZ.md"):
            with self.subTest(kilavuz=str(k.relative_to(KOK))):
                self.assertRegex(k.read_text(encoding="utf-8"),
                                 r"(?m)^cp kod/isaretli_gosterici\.py ~/navitas/scripts/")


# ── G10 ───────────────────────────────────────────────────────────────────────
class JetsonBaslatGosterici(unittest.TestCase):
    """GERCEK bash + shim'li sahte kurulu Jetson (test_faz_b_jetson_baslat._AnaMakine)."""

    T227_SATIRI = '    p.add_argument("--isaretli-yayin", default=None)  # sahte T227 bayragi\n'

    def _rpi_metni(self, t227):
        taban = "".join(s for s in (jb.KOD / "rpi_inference.py").read_text(
            encoding="utf-8").splitlines(True) if "--isaretli-yayin" not in s)
        return taban + (self.T227_SATIRI if t227 else "")

    def _makine(self, t227_paket, t227_kurulu, sbin=False):
        m = jb._AnaMakine(sbin=sbin, kullanici="saha" if sbin else None, lf_paket=True)
        self.addCleanup(m.temizle)
        shutil.copytree(GOSTERICI_DIZIN, m.paket / "gosterici")
        (m.kok / "scripts").mkdir(exist_ok=True)
        shutil.copyfile(KANONIK, m.kok / "scripts" / KANONIK.name)
        (m.paket / "kod" / "rpi_inference.py").write_text(self._rpi_metni(t227_paket), encoding="utf-8")
        (m.kok / "codes" / "rpi_inference.py").write_text(self._rpi_metni(t227_kurulu), encoding="utf-8")
        return m

    def _kuru(self, m, **ek):
        beyan = {"KIP": "udp"}
        beyan.update(jb.BEYAN_TAM)
        beyan.update(ek)
        kod, out, err = jb._kos(m.betik, m.env(**beyan))
        return kod, out, err, jb._bolumler(out)

    def test_G10_bash_n_sozdizimi(self):
        d = tempfile.mkdtemp(prefix="navitas_t228_bashn_")
        self.addCleanup(shutil.rmtree, d, True)
        lf = Path(d) / jb.BETIK.name      # calisma kopyasi autocrlf ile CRLF olabilir -> LF kopya
        lf.write_bytes(jb.BETIK.read_bytes().replace(b"\r\n", b"\n"))
        p = subprocess.run([jb._bash(), "-n", jb._posix(lf)], capture_output=True, text=True, timeout=30)
        self.assertEqual(p.returncode, 0, p.stderr)

    def test_G10_varsayilan_kapali_mevcut_davranis(self):
        m = jb._AnaMakine()
        self.addCleanup(m.temizle)
        kod, out, err, b = self._kuru(m)          # gercek paket, gercek betik
        self.assertEqual(kod, 0, out + err)
        self.assertEqual(b["env"].get("GOSTERICI_KIP"), "kapali", "--kuru env bolumunde gorunmeli")
        self.assertEqual(b["env"].get("ISARETLI_YAYIN"), "127.0.0.1:8081")
        self.assertNotIn("--isaretli-yayin", b["birimler"][jb.RPI], "kapaliyken bayrak VERILMEZ")
        self.assertEqual(set(b["birimler"]), {jb.COGULLAYICI, *jb.TUKETICILER})
        self.assertIn("## gosterici (T228): GOSTERICI_KIP=kapali", out)

    def test_G10_x11_T227siz_paket_YOK_exit_3_bayrak_verilir(self):
        m = self._makine(t227_paket=False, t227_kurulu=False)
        kod, out, err, b = self._kuru(m, GOSTERICI_KIP="x11")
        self.assertEqual(kod, 3, out + err)
        self.assertEqual(jb._arg_degeri(b["birimler"][jb.RPI], "--isaretli-yayin"), "127.0.0.1:8081")
        self.assertIn("[YOK] paket rpi_inference --isaretli-yayin (T227)", out)
        self.assertIn("[YOK] kurulu rpi_inference --isaretli-yayin (T227)", out)
        self.assertIn("[VAR] paket kod/isaretli_gosterici.py", out)
        self.assertIn("[VAR] paket gosterici/navitas-isaretli-gosterici.desktop", out)
        self.assertRegex(b["sonuc"] or "", r"^KURU SONUC: eksik \(beyan: tam · \[YOK\]: 2\)")

    def test_G10_T227li_paket_her_kip_exit_0(self):
        m = self._makine(t227_paket=True, t227_kurulu=True)
        env = m.env()
        for kip, dosya in (("x11", "gosterici/navitas-isaretli-gosterici.desktop"),
                           ("drm", "gosterici/navitas-isaretli-gosterici-drm.service"),
                           ("rtsp", "gosterici/GOSTERICI_KURULUM.md")):
            with self.subTest(kip=kip):
                kod, out, err, b = self._kuru(m, GOSTERICI_KIP=kip)
                self.assertEqual(kod, 0, out + err)
                self.assertEqual(b["env"]["GOSTERICI_KIP"], kip)
                self.assertIn("[VAR] paket " + dosya, out)
                self.assertIn("[VAR] paket rpi_inference --isaretli-yayin (T227)", out)
                self.assertIn("[VAR] kurulu rpi_inference --isaretli-yayin (T227)", out)
                self.assertIn("komut: {} {}/scripts/isaretli_gosterici.py --kip {} --kaynak "
                              "http://127.0.0.1:8081".format(env["KAMERA_PYTHON"],
                                                             env["NAVITAS_KOK"], kip), out)
                self.assertEqual(set(b["birimler"]), {jb.COGULLAYICI, *jb.TUKETICILER},
                                 "gosterici birim listesine GIRMEZ")
                if kip == "drm":
                    self.assertIn("Argus", out)
                if kip == "rtsp":
                    self.assertIn("rtsp://<JETSON_IP>:8554/isaretli", out)
        kod, out, err, b = self._kuru(m, GOSTERICI_KIP="x11", ISARETLI_YAYIN="127.0.0.1:18081")
        self.assertEqual(kod, 0, out + err)
        self.assertEqual(jb._arg_degeri(b["birimler"][jb.RPI], "--isaretli-yayin"), "127.0.0.1:18081")
        self.assertIn("--kaynak http://127.0.0.1:18081", out)

    def test_G10_gecersiz_kip_yayin_port_cakismasi_fail_closed(self):
        m = self._makine(t227_paket=True, t227_kurulu=True)
        for ek, parca in (({"GOSTERICI_KIP": "hdmi"}, "GOSTERICI_KIP='hdmi' taninmiyor"),
                          ({"GOSTERICI_KIP": "x11", "ISARETLI_YAYIN": "0.0.0.0:8081"}, "yalniz 127.0.0.1"),
                          ({"GOSTERICI_KIP": "x11", "ISARETLI_YAYIN": "192.168.144.30:8081"},
                           "yalniz 127.0.0.1"),
                          ({"GOSTERICI_KIP": "x11", "ISARETLI_YAYIN": "127.0.0.1:"}, "port sayi degil"),
                          ({"GOSTERICI_KIP": "x11", "ISARETLI_YAYIN": "127.0.0.1:abc"}, "port sayi degil"),
                          ({"GOSTERICI_KIP": "x11", "ISARETLI_YAYIN": "127.0.0.1:0"}, "port 1-65535"),
                          ({"GOSTERICI_KIP": "x11", "ISARETLI_YAYIN": "127.0.0.1:70000"}, "port 1-65535"),
                          ({"GOSTERICI_KIP": "x11", "KAMERA": "http://127.0.0.1:8081/video"},
                           "kamera koprusuyle AYNI")):
            with self.subTest(ek=ek):
                kod, out, err, _b = self._kuru(m, **ek)
                self.assertEqual(kod, 1, out + err)
                self.assertIn(parca, err)
                self.assertNotIn("navitas-rpi-inference.service:", out, "fail-closed: komut basilmaz")

    def test_G10_kur_T227siz_kurulu_rpi_HATA_hicbir_systemctl_yok(self):
        m = self._makine(t227_paket=True, t227_kurulu=False, sbin=True)
        e = m.env(KIP="udp", GOSTERICI_KIP="x11", **jb.BEYAN_TAM)
        kod, out, err = jb._kos(m.betik, e, "--kur")
        self.assertEqual(kod, 1, out + err)
        self.assertIn("--isaretli-yayin TANIMIYOR (T227 yok)", err)
        self.assertEqual([s for s in m.shim_satirlari() if s.startswith("systemctl ")], [],
                         "birimler kurulmadan DURMALI (argparse cikis 2 dongusu yerine)")
        self.assertFalse(m.env_dosya.exists())
        (m.kok / "codes" / "rpi_inference.py").write_text(self._rpi_metni(True), encoding="utf-8")
        kod, out, err = jb._kos(m.betik, e, "--kur")
        self.assertEqual(kod, 0, out + err)
        env = m.env_dosya.read_text(encoding="utf-8")
        self.assertIn("GOSTERICI_KIP=x11\n", env)
        self.assertIn("ISARETLI_YAYIN=127.0.0.1:8081\n", env)
        self.assertRegex(env, r"(?m)^RPI_EK_ARGS=.*--isaretli-yayin 127\.0\.0\.1:8081$")

    def test_G10_port_sabiti_ve_varsayilan_gostericiyle_AYNI(self):
        metin = jb.BETIK.read_text(encoding="utf-8")
        m = re.search(r"^ISARETLI_YAYIN_PORT_VARSAYILAN=(\d+)", metin, re.M)
        self.assertIsNotNone(m)
        kaynak = urllib.parse.urlsplit(g.VARSAYILAN_KAYNAK)
        self.assertEqual(int(m.group(1)), kaynak.port)
        self.assertEqual(kaynak.hostname, "127.0.0.1")
        self.assertRegex(metin, r'(?m)^GOSTERICI_BETIK="' + re.escape(KANONIK.name) + '"$')
        self.assertIn('GOSTERICI_KIP="${GOSTERICI_KIP:-kapali}"', metin)


if __name__ == "__main__":
    unittest.main()
