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
     hemen biten boru -> Argus uyarisi, surec dongusu yok. T228-D: saf karar tablosu (HISTEREZIS
     2 ardisik taze; CANLI'dan cikis ANINDA; baslatma araligi >= 3 s; olen video -> YOK hemen);
     donmus boru (identity nabzi > 3 s) -> GORUNTU YOK, hic nabiz -> DOGRULANACAK uyarisi; nabiz
     ayristiricisi (sahte -v ciktisi; toleransli + secici), gercek boru okuyucu, --nabiz-sina;
     drm_kos baglantisi (-v, stdout BORU, izleyici) gercek KareCekici + sahte HTTP + sahte Popen.
     T228-D2: yayin 503 olup geri gelince IKINCI video borusu YENI nabiz izleyicisiyle surer (NG);
     olen video borusunun GORUNTU YOK sebebi 'video borusu kendiliginden bitti (rc=N)' (yayin
     tazeyse; degilse yayinin kendi sebebi)
  G8 jetson_paket/gosterici: .desktop Exec (bash -n), DRM birimi gozcu kilidi + onkosul + VARSAYILAN
     KAPALI (systemd/ altinda degil, betik kurmaz), xorg sablonu TAHMIN basligi, kurulum belgesi.
     D-453: kurulum belgesi (markdown) kilitleri YENI icerigi cizili (~~...~~) araliklar AYIKLANMIS
     metinde arar; §1 kodlayici / §5 / §9'da olculmemis 'doğrulandı/GEÇTİ/ölçüldü' yok; eski
     metnin cizili durdugu HAM metinde denetlenir. D-454 (T228-D2): yasak/celiski aramalari
     NORMALLESTIRILMIS metinde ('tutar', karma yazim, kalin parcali / yumusak tireli hukum,
     tipografik kesme/tirnak); belge GENELINDE olculmemis GECTI yok; §4 sonuclari tam ÖLÇÜLECEK;
     §5 'N ardışık' / '≥ N s' / '> N s' kodla ayni (celiskili ikinci hukum yok); eski nabizsiz
     boru canli metinde yok
  G9 paket aynasi: KOPYALAR tasir, bayt-es, kod/ dizininden izole import; kilavuz kopyalar
  G10 jetson_baslat.sh: bash -n; varsayilan kapali (env'de gorunur, --isaretli-yayin YOK); x11 ile rpi
     --isaretli-yayin + gosterici bolumu; T227'siz paket [YOK] + exit 3, T227'li exit 0; gecersiz
     kip / yayin / port cakismasi exit 1; --kur T227'siz kurulu rpi ile HATA ve hic systemctl yok;
     port sabiti gostericiyle AYNI
  G11 x11 DONGUSU (T228-D): x11_kos'a sahte cv2 + sahte/gercek cekici enjekte edilir (pencere
     acilmaz) — CANLI iken yayin 503 / erisilemez olunca ILK cizim kirmizi GORUNTU YOK (eski kare
     yok); tuval kaydi 01_CANLI -> 02_GORUNTU_YOK
Mutasyon (results/fdr_sprint_20260910/H9_MK15/t228/mutasyon_t228.py): bayat esigi kaldirilirsa,
yasak IP kontrolu kaldirilirsa, GORUNTU_YOK eski kareyi cizerse, jetson_baslat bayragi vermezse,
--kur T227 denetimi kaldirilirsa bu dosya DUSER. T228-D (t228d/mutasyon_t228d.py): x11 dongusu
hatayi yok sayarsa (MG), histerezis / baslatma araligi / aninda cikis / boru nabzi esigi
kaldirilirsa, -v ya da identity dusurulurse, belge kilitleri silinirse DUSER. T228-D2: nabiz
izleyicisi borular arasi paylasilirsa (NG), belge notlari silinmeden CIZILIRSE ya da olculmemis
madde 'doğrulandı' tasirsa (NK*), olen videonun sebebi 'yayin dogrulaniyor'a donerse (NS) DUSER.
D-454 sinifi (NK11-NK21): 'tutar' / karma yazim / kalin parcali / yumusak tireli hukum, §4 sonuc
hucresi / basligi ve ust hukum cizilmesi, kalin sayili ya da ASCII '>=' ile celiskili ikinci
hukum, tipografik tirnakla CANLI metne donen eski boru DUSER.
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
import unicodedata
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
        self.otomatik_sira = False     # T228-D: her 200 yanitinda sira +1 (surekli taze yayin)
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
                    if dis.otomatik_sira:
                        dis.sira = str(int(dis.sira or "0") + 1)
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
                         ["souphttpsrc", "multipartdemux", "jpegdec", "identity", "nvvidconv",
                          "nvdrmvideosink"])
        for parca in ("location=http://127.0.0.1:8081" + kk.VIDEO_YOLU, "video/x-raw(memory:NVMM)",
                      "width=1280", "height=720", "nvdrmvideosink set_mode=1",
                      "jpegdec ! identity name=nabiz silent=false ! nvvidconv"):
            self.assertIn(parca, b)
        self.assertEqual(g.NABIZ_ADI, "nabiz")
        self.assertNotIn("conn_id", b)
        self.assertIn("nvdrmvideosink set_mode=1 sync=false conn_id=2", g.drm_boru(conn_id=2))
        self.assertNotIn("kmssink", b)
        # T228-D: -v nabiz satirlarini stdout'a bastirir; --kuru ve drm_kos AYNI argv (tek kaynak)
        self.assertEqual(g.drm_video_argv("/usr/bin/gst-launch-1.0", conn_id=2),
                         ["/usr/bin/gst-launch-1.0", "-v", "-e", g.drm_boru(conn_id=2)])
        self.assertEqual(g.drm_video_argv("gst-launch-1.0", stdbuf="/usr/bin/stdbuf"),
                         ["/usr/bin/stdbuf", "-oL"] + g.drm_video_argv("gst-launch-1.0"),
                         "stdbuf oneki: -v satirlari satir tamponlu")

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
        self.assertIn("gst-launch-1.0 -v -e 'souphttpsrc location=http://127.0.0.1:8081/video", out)
        self.assertIn("jpegdec ! identity name=nabiz silent=false ! nvvidconv", out)
        self.assertIn("[DOGRULANACAK] gst-launch-1.0 -v nabiz satiri bicimi", out)
        self.assertIn("--nabiz-sina", out)
        self.assertIn("[BILGI] drm_kos video borusunu `stdbuf -oL` onekiyle kosar", out)
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
    """subprocess.Popen yerine: poll/terminate/kill/wait. `omur` poll sayisi sonra kendiliginden
    biter. T228-D: `t` baslama ani (sahte saat), `nabiz` baslamaya gore ilerleyen tampon ofsetleri
    (s) — `son_nabiz(simdi)` gozetmenin `ilerleme_oku`'suna verilir."""

    def __init__(self, argv, kayit, omur=None, t=None, nabiz=None):
        self.argv = argv
        self.returncode = None
        self.sonlandirildi = False
        self.kalan = omur
        self.t = t
        self.nabiz = nabiz
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

    def son_nabiz(self, simdi):
        gecen = [self.t + o for o in (self.nabiz or ()) if self.t + o <= simdi]
        return max(gecen) if gecen else None


def _tur(surec):
    """Surecin borusu: video (souphttpsrc) mu, GORUNTU YOK (videotestsrc) mu."""
    return "video" if "souphttpsrc" in surec.argv[-1] else "yok"


YOK = g.EkranDurumu(g.DURUM_YOK, "yayin erisilemiyor", None)
CANLI = g.EkranDurumu(g.DURUM_CANLI, "", 0.2)
BAYAT = g.EkranDurumu(g.DURUM_BAYAT, "kare 2.4 s eski (> 2 s)", 2.4)


class DrmGozetmen(unittest.TestCase):
    """Sahte saat: her yoklama DRM_YOKLAMA_S (1 s) ilerler; t = yoklama sirasi."""

    def _kos(self, durumlar, omur=None, nabiz=None, ilerleme=False):
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
        video = g.drm_video_argv("gst-launch-1.0")

        def baslat(argv):
            return _SahteSurec(argv, kayit, omur, t=saat[0],
                               nabiz=nabiz if argv == video else None)

        ek = {"ilerleme_oku": lambda p: p.son_nabiz(saat[0])} if ilerleme else {}
        n = g.drm_gozetmen(video, lambda sebep: ["gst-launch-1.0", g.drm_goruntu_yok_boru(sebep)],
                           durum_oku, baslat, lambda: bitti["e"], uyku=uyku, saat=lambda: saat[0],
                           log=lambda m, kirmizi=False: loglar.append((kirmizi, m)), **ek)
        return n, kayit, loglar, uykular

    @staticmethod
    def _baslatmalar(kayit):
        return [(s.t, _tur(s)) for s in kayit]

    def test_G7_yok_kirmizi_canli_video_bayatta_video_DURUR(self):
        n, kayit, loglar, _u = self._kos([YOK, YOK, CANLI, CANLI, CANLI, BAYAT, BAYAT, YOK])
        self.assertEqual(n, 3)
        yok1, video, yok2 = kayit
        self.assertIn("videotestsrc", yok1.argv[-1])
        self.assertNotIn("souphttpsrc", yok1.argv[-1])
        self.assertEqual(video.argv[:3], ["gst-launch-1.0", "-v", "-e"])
        self.assertIn("souphttpsrc", video.argv[-1])
        self.assertTrue(yok1.sonlandirildi, "yayin gelince kirmizi boru durdurulmali")
        self.assertTrue(video.sonlandirildi,
                        "kare BAYAT olunca video borusu DURMALI (son kare ekranda kalmasin)")
        self.assertIn("kare 2.4 s eski", yok2.argv[-1])
        self.assertTrue(any(k and "GORUNTU YOK" in m for k, m in loglar), loglar)

    def test_G7_hemen_biten_boru_uyari_ve_baslatma_sikligi_sinirli(self):
        n, kayit, loglar, _u = self._kos([CANLI] * 8, omur=0)
        self.assertEqual(self._baslatmalar(kayit),
                         [(0.0, "yok"), (3.0, "video"), (4.0, "yok"), (7.0, "video")],
                         "olen video -> GORUNTU YOK HEMEN; oteki baslatmalar >= {:g} s arayla "
                         "(surec dongusu yok)".format(g.DRM_ASGARI_ARALIK_S))
        self.assertEqual(n, 4)
        self.assertGreaterEqual(sum(1 for k, m in loglar if k and "Argus" in m), 3, loglar)
        self.assertFalse(any(s.sonlandirildi for s in kayit), "kendiliginden biten surec oldurulmez")

    def test_G7_olen_video_borusu_GORUNTU_YOK_sebebi_rc_ya_da_yayin_sebebi(self):
        """T228-D2 (T228-D curutucusu, kucuk bulgu): yayin TAZEYKEN video borusu kendiliginden
        olurse GORUNTU YOK ekraninda 'yayin dogrulaniyor' DEGIL gercek sebep yazar: 'video borusu
        kendiliginden bitti (rc=N)'. Yayin da bozuksa yayinin kendi sebebi (kok neden) gosterilir.
        Ekranda '=' izinli karakter degil (_gst_metni) -> 'rc 1'; log ham sebebi tasir."""
        _n, kayit, loglar, _u = self._kos([CANLI] * 6, omur=0)
        self.assertEqual(self._baslatmalar(kayit)[:3], [(0.0, "yok"), (3.0, "video"), (4.0, "yok")])
        metin = kayit[2].argv[-1]
        self.assertIn('text="GORUNTU YOK - video borusu kendiliginden bitti (rc 1)"', metin)
        self.assertNotIn("dogrulaniyor", metin)
        self.assertTrue(any(k and "GORUNTU YOK borusu basladi (video borusu kendiliginden bitti "
                                  "(rc=1))" in m for k, m in loglar), loglar)
        _n, kayit, _l, _u = self._kos([CANLI, CANLI, CANLI, CANLI, YOK, YOK], omur=0)
        self.assertEqual(self._baslatmalar(kayit)[:3], [(0.0, "yok"), (3.0, "video"), (4.0, "yok")])
        self.assertIn('text="GORUNTU YOK - yayin erisilemiyor"', kayit[2].argv[-1])

    def test_G7_histerezis_tek_taze_yoklama_videoya_DONMEZ_cikis_ANINDA(self):
        durumlar = [YOK, YOK, YOK, YOK, CANLI, YOK, CANLI, BAYAT, CANLI, CANLI, CANLI, BAYAT, YOK]
        _n, kayit, _l, _u = self._kos(durumlar)
        self.assertEqual(self._baslatmalar(kayit), [(0.0, "yok"), (9.0, "video"), (11.0, "yok")],
                         "t=4 ve t=6'daki TEK taze yoklama videoyu ACMAZ (aralik dolmus olsa da); "
                         "t=9 ikinci ARDISIK tazede acilir; t=11 ilk BAYAT'ta aralik (2 s < 3 s) "
                         "beklenmeden kapanir")
        video, yok2 = kayit[1], kayit[2]
        self.assertTrue(video.sonlandirildi)
        self.assertIn("kare 2.4 s eski", yok2.argv[-1])

    def test_G7_cirpinan_yayin_baslatma_sikligi_sinirli(self):
        durumlar = [YOK, CANLI, CANLI, CANLI, BAYAT, CANLI, CANLI, BAYAT, CANLI, CANLI, CANLI, CANLI]
        _n, kayit, _l, _u = self._kos(durumlar)
        b = self._baslatmalar(kayit)
        self.assertEqual(b, [(0.0, "yok"), (3.0, "video"), (4.0, "yok"), (9.0, "video")],
                         "t=2 ve t=6'da 2 ardisik taze var ama son baslatmadan < 3 s: video BEKLER")
        for (t0, _a), (t1, tur) in zip(b, b[1:]):
            if tur == "video":
                self.assertGreaterEqual(t1 - t0, g.DRM_ASGARI_ARALIK_S, b)

    def test_G7_donmus_boru_kare_taze_olsa_da_GORUNTU_YOK(self):
        _n, kayit, loglar, _u = self._kos([CANLI] * 12, nabiz=[0.5, 1.5, 2.5], ilerleme=True)
        self.assertEqual(self._baslatmalar(kayit), [(0.0, "yok"), (3.0, "video"), (9.0, "yok")],
                         "son nabiz t=5.5: t=8'de 2.5 s (donmus DEGIL), t=9'da 3.5 s > 3 s -> "
                         "GORUNTU YOK; t=11'de 2 ardisik taze ama aralik 2 s < 3 s")
        self.assertTrue(kayit[1].sonlandirildi, "donmus video borusu durdurulmali")
        self.assertIn("video borusu ilerlemiyor: son tampon 3.5 s once (> 3 s)", kayit[2].argv[-1])
        self.assertTrue(any(k and "ilerlemiyor" in m for k, m in loglar), loglar)

    def test_G7_hic_nabiz_yoksa_acilis_payindan_sonra_GORUNTU_YOK_ve_DOGRULANACAK(self):
        _n, kayit, loglar, _u = self._kos([CANLI] * 9, nabiz=[], ilerleme=True)
        self.assertEqual(self._baslatmalar(kayit), [(0.0, "yok"), (3.0, "video"), (7.0, "yok")],
                         "acilis payi 3 s: t=6'da 3,0 s (sinir, donmus DEGIL), t=7'de 4,0 s")
        self.assertIn("acilistan beri 4.0 s tampon yok (> 3 s)", kayit[2].argv[-1])
        self.assertTrue(any(k and "HIC nabiz" in m and "DOGRULANACAK" in m for k, m in loglar),
                        loglar)

    def test_G7_surekli_nabiz_video_borusu_surer(self):
        _n, kayit, loglar, _u = self._kos([CANLI] * 15, nabiz=[0.5 * i for i in range(1, 60)],
                                          ilerleme=True)
        self.assertEqual(self._baslatmalar(kayit), [(0.0, "yok"), (3.0, "video")])
        self.assertFalse(any("ilerlemiyor" in m for _k, m in loglar), loglar)

    def test_G7_saf_karar_tablosu(self):
        V, Y = g.BORU_VIDEO, g.BORU_YOK
        # (calisan, son_boru, taze, ardisik, simdi, son_baslatma_t) -> (boru, baslat, guvenlik)
        tablo = [
            ((None, None, False, 0, 0.0, None), (Y, True, False)),   # acilis: GORUNTU YOK hemen
            ((None, None, True, 1, 0.0, None), (Y, True, False)),    # acilis taze ama 1/2 -> YOK
            ((Y, Y, True, 1, 10.0, 0.0), (Y, False, False)),         # histerezis: 1 taze yetmez
            ((Y, Y, True, 2, 10.0, 0.0), (V, True, False)),          # 2 ardisik + aralik -> video
            ((Y, Y, True, 2, 2.9, 0.0), (Y, False, False)),          # aralik dolmadi -> bekle
            ((Y, Y, True, 2, 3.0, 0.0), (V, True, False)),           # aralik sinirda (>=) serbest
            ((V, V, True, 9, 0.1, 0.0), (V, False, False)),          # video surer (yeniden acma yok)
            ((V, V, False, 0, 0.1, 0.0), (Y, True, True)),           # CANLI'dan cikis ANINDA
            ((None, V, True, 1, 0.1, 0.0), (Y, True, True)),         # olen video -> YOK hemen
            ((None, Y, False, 0, 1.0, 0.0), (None, False, False)),   # olen YOK: aralik dolmadan bekle
            ((None, Y, False, 0, 3.0, 0.0), (Y, True, False)),
            ((None, Y, True, 2, 3.0, 0.0), (V, True, False)),
            ((Y, Y, False, 0, 50.0, 0.0), (Y, False, False)),        # YOK surer, gereksiz baslatma yok
        ]
        for girdi, beklenen in tablo:
            with self.subTest(girdi=girdi):
                self.assertEqual(tuple(g.drm_boru_karari(*girdi)), beklenen)
        self.assertEqual((g.DRM_CANLI_ARDISIK, g.DRM_ASGARI_ARALIK_S, g.DRM_BORU_DONMA_S),
                         (2, 3.0, 3.0), "gorev tanimi: 2 ardisik taze, >= 3 s aralik, > 3 s donma")

    def test_G7_boru_donmus_mu_sinir_ve_referans(self):
        self.assertFalse(g.boru_donmus_mu(10.0, 5.0, 7.0), "son nabiz tam 3,0 s once: sinir DEGIL")
        self.assertTrue(g.boru_donmus_mu(10.01, 5.0, 7.0))
        self.assertFalse(g.boru_donmus_mu(8.0, 5.0, None), "acilis payi = esik")
        self.assertTrue(g.boru_donmus_mu(8.5, 5.0, None))
        self.assertTrue(g.boru_donmus_mu(8.5, 5.0, 4.0), "baslamadan ONCEKI nabiz tazelik UZATMAZ")
        self.assertFalse(g.boru_donmus_mu(8.5, 5.0, 6.0))


def _nabiz_satiri(pts="0:00:01.234567890", ad="nabiz", bosluk="   "):
    return ("/GstPipeline:pipeline0/GstIdentity:{a}: last-message = chain{b}******* ({a}:sink) "
            "(1382400 bytes, dts: none, pts: {p}, duration: none, offset: -1, offset_end: -1, "
            "flags: 00004040 discont tag-memory , meta: none) 0x7f8c00b1c0").format(
                a=ad, b=bosluk, p=pts)


#: `gst-launch-1.0 -v` ciktisi ORNEGI — GStreamer 1.x (gstidentity.c last-message, gst-launch
#: deep-notify) kaynak bilgisinden KURULDU; Jetson'da OLCULMEDI (GOSTERICI_KURULUM §5
#: DOGRULANACAK; sahada `--nabiz-sina`).
GST_V_ORNEK = [
    "Setting pipeline to PAUSED ...",
    "Pipeline is live and does not need PREROLL ...",
    "/GstPipeline:pipeline0/GstJpegDec:jpegdec0.GstPad:src: caps = video/x-raw, "
    "format=(string)I420, width=(int)1280, height=(int)720",
    "/GstPipeline:pipeline0/GstIdentity:nabiz.GstPad:src: caps = video/x-raw, "
    "format=(string)I420, width=(int)1280, height=(int)720",
    "/GstPipeline:pipeline0/GstIdentity:nabiz: last-message = event   ******* (nabiz:sink) E "
    "(type: stream-start (10254), GstEventStreamStart, stream-id=(string)chain0, "
    "flags=(GstStreamFlags)GST_STREAM_FLAG_NONE, group-id=(uint)1;) 0x7f8c001f20",
    _nabiz_satiri("0:00:01.000000000"),
    _nabiz_satiri("0:00:01.500000000"),
    'Got EOS from element "pipeline0".',
]


class NabizAyristirici(unittest.TestCase):
    def test_G7_nabiz_ayristir_toleransli_ve_secici(self):
        A = g.nabiz_ayristir
        self.assertEqual(A(_nabiz_satiri("0:00:01.234567890")), {"pts_s": 1.23456789})
        self.assertEqual(A(_nabiz_satiri("1:02:03.5"))["pts_s"], 3723.5)
        for pts in ("none", "99:99:99.999999999"):
            with self.subTest(pts=pts):
                self.assertEqual(A(_nabiz_satiri(pts)), {"pts_s": None}, "NONE zaman -> pts yok")
        # toleransli: tek bosluk, yol yok (yalniz pad adi), CRLF, satir basi ad, chain-list
        self.assertIsNotNone(A(_nabiz_satiri(bosluk=" ")))
        self.assertEqual(A("last-message = chain ******* (nabiz:sink) (100 bytes, pts: 0:00:03.5)"
                           "\r\n"), {"pts_s": 3.5})
        self.assertIsNotNone(A("nabiz: last-message = chain-list   ******* (nabiz:sink) (...)"))
        # secici: olay (stream-start / eos), caps (baska eleman ve nabiz pad'i), baska identity,
        # benzer ad, EOS bildirimi, bos
        for satir in (GST_V_ORNEK[0], GST_V_ORNEK[2], GST_V_ORNEK[3], GST_V_ORNEK[4],
                      "/GstPipeline:pipeline0/GstIdentity:nabiz: last-message = event   ******* "
                      "(nabiz:sink) E (type: eos (28174), ) 0x1",
                      _nabiz_satiri(ad="identity0"), _nabiz_satiri(ad="nabizci"), GST_V_ORNEK[-1],
                      "", "nabiz"):
            with self.subTest(satir=satir[:70]):
                self.assertIsNone(A(satir))

    def test_G7_nabiz_izleyici_ayni_ya_da_geri_pts_ilerleme_DEGIL(self):
        loglar = []
        iz = g.NabizIzleyici(log=lambda m, kirmizi=False: loglar.append(m))
        self.assertFalse(iz.besle(GST_V_ORNEK[0], simdi=1.0))
        self.assertIsNone(iz.son())
        self.assertTrue(iz.besle(_nabiz_satiri("0:00:01.0"), simdi=2.0))
        self.assertEqual(iz.son(), 2.0)
        self.assertFalse(iz.besle(_nabiz_satiri("0:00:01.0"), simdi=3.0), "ayni pts ilerleme DEGIL")
        self.assertFalse(iz.besle(_nabiz_satiri("0:00:00.5"), simdi=3.5), "geri pts ilerleme DEGIL")
        self.assertEqual(iz.son(), 2.0)
        self.assertTrue(iz.besle(_nabiz_satiri("0:00:01.5"), simdi=4.0))
        self.assertTrue(iz.besle(_nabiz_satiri("none"), simdi=5.0), "pts'siz nabiz ilerleme sayilir")
        self.assertFalse(iz.besle(GST_V_ORNEK[4], simdi=6.0), "olay satiri nabiz DEGIL")
        self.assertEqual(iz.son(), 5.0)
        o = iz.ozet()
        self.assertEqual((o["nabiz"], o["son_pts"]), (3, 1.5))
        self.assertIn("gst: Setting pipeline to PAUSED ...", loglar)
        self.assertEqual(sum("ilk nabiz" in m for m in loglar), 1, loglar)

    def test_G7_nabiz_izleyici_gercek_boruyu_EOFa_kadar_okur(self):
        satirlar = [GST_V_ORNEK[0]] + [_nabiz_satiri("0:00:0{}.000000000".format(i))
                                       for i in range(1, 5)]
        kod = ("import sys, time\n"
               "for s in {!r}:\n"
               "    sys.stdout.write(s + '\\n'); sys.stdout.flush(); time.sleep(0.05)\n").format(
                   satirlar)
        p = subprocess.Popen([sys.executable, "-B", "-c", kod], stdout=subprocess.PIPE, text=True,
                             encoding="utf-8", errors="replace", bufsize=1)
        iz = g.NabizIzleyici(log=_sessiz)
        iplik = iz.akimi_oku(p.stdout)
        iplik.join(30)
        self.assertFalse(iplik.is_alive(), "okuyucu iplik EOF'ta bitmeli")
        self.assertEqual(p.wait(30), 0)
        p.stdout.close()
        o = iz.ozet()
        self.assertEqual((o["satir"], o["nabiz"], o["son_pts"]), (5, 4, 4.0))

    def test_G7_nabiz_sina_cli_eslesti_0_eslesmedi_1(self):
        def kos(girdi):
            return subprocess.run([sys.executable, "-B", str(KANONIK), "--nabiz-sina"],
                                  input=girdi, capture_output=True, text=True, encoding="utf-8",
                                  errors="replace", timeout=60)
        p = kos("\n".join(GST_V_ORNEK) + "\n")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("NABIZ_SINA: ESLESTI — 8 satir, 2 nabiz", p.stdout)
        p = kos(GST_V_ORNEK[0] + "\n" + GST_V_ORNEK[4] + "\n")
        self.assertEqual(p.returncode, g.CIKIS_NABIZ_YOK, p.stdout + p.stderr)
        self.assertIn("NABIZ_SINA: ESLESMEDI — 2 satir", p.stdout)
        self.assertIn("DOGRULANACAK", p.stdout)
        self.assertIn("\n  " + GST_V_ORNEK[0] + "\n", p.stdout, "ilk taninmayan satirlar basilmali")

    def test_G7_nabiz_sina_zamanlama_ZAMANINDA_0_TOPLU_1(self):
        satirlar = "".join(_nabiz_satiri("0:00:{:012.9f}".format(0.2 * i)) + "\n" for i in range(20))
        for adim_s, beklenen, parca in (
                (0.2, 0, "ZAMANINDA: varis yayilimi 3.80 s / pts yayilimi 3.80 s"),
                (0.0, g.CIKIS_NABIZ_YOK, "NABIZ_SINA: TOPLU"),
                (0.05, g.CIKIS_NABIZ_YOK, "TAMPONLU")):
            with self.subTest(adim_s=adim_s):
                saat = [0.0]

                def saat_oku(adim_s=adim_s):
                    saat[0] += adim_s
                    return saat[0]

                cikti = []
                self.assertEqual(g.nabiz_sina(io.StringIO(satirlar), cikti=cikti.append,
                                              saat=saat_oku), beklenen, cikti)
                self.assertIn(parca, "\n".join(cikti))
        self.assertEqual((g.NABIZ_SINA_ASGARI_PTS_S, g.NABIZ_SINA_VARIS_ORANI), (1.0, 0.5))

    def test_G7_nabiz_sina_gercek_boru_ZAMANINDA_0_TOPLU_1(self):
        satirlar = [_nabiz_satiri("0:00:{:012.9f}".format(0.2 * i)) for i in range(11)]
        for bekleme, beklenen, parca in ((0.2, 0, "ZAMANINDA"), (0.0, g.CIKIS_NABIZ_YOK, "TOPLU")):
            with self.subTest(bekleme=bekleme):
                cocuk = ("import sys, time\n"
                         "for s in {!r}:\n"
                         "    sys.stdout.write(s + '\\n'); sys.stdout.flush(); time.sleep({})\n"
                         ).format(satirlar, bekleme)
                p = subprocess.Popen([sys.executable, "-B", "-c", cocuk], stdout=subprocess.PIPE,
                                     text=True, encoding="utf-8", errors="replace", bufsize=1)
                cikti = []
                try:
                    kod = g.nabiz_sina(p.stdout, cikti=cikti.append)
                finally:
                    p.stdout.close()
                    p.wait(30)
                self.assertEqual(kod, beklenen, cikti)
                self.assertIn(parca, "\n".join(cikti))


class _SahteGstCiktisi:
    """`gst-launch-1.0 -v` stdout'u yerine (readline). Once iki baslik satiri, sonra nabiz satirlari:
    `aralik_s` verilirse surekli (her aralikta bir); verilmezse `adet` nabizdan sonra boru DONAR
    (readline surec durdurulana kadar bekler, sonra EOF)."""

    def __init__(self, kapandi, aralik_s=None, adet=2):
        self.kapandi = kapandi
        self.aralik_s = aralik_s
        self.adet = adet
        self.baslik = [GST_V_ORNEK[0], GST_V_ORNEK[3]]
        self.n = 0

    def readline(self):
        if self.baslik:
            return self.baslik.pop(0) + "\n"
        if self.aralik_s is None and self.n >= self.adet:
            self.kapandi.wait(30)
            return ""
        if self.kapandi.is_set() or (self.aralik_s is not None and self.kapandi.wait(self.aralik_s)):
            return ""
        self.n += 1
        return _nabiz_satiri("0:00:{:012.9f}".format(self.n * 0.1)) + "\n"


class _SahtePopen:
    """subprocess.Popen yerine (drm_kos `baslat=`): argv/kwargs kaydeder; stdout=PIPE istenirse sahte
    -v ciktisi verir. Surec kendiliginden bitmez."""

    def __init__(self, argv, kayit, aralik_s=None, **kw):
        self.argv = list(argv)
        self.kw = kw
        self.t = time.monotonic()
        self.returncode = None
        self.sonlandirildi = False
        self._kapandi = threading.Event()
        self.stdout = (_SahteGstCiktisi(self._kapandi, aralik_s)
                       if kw.get("stdout") == subprocess.PIPE else None)
        kayit.append(self)

    def poll(self):
        return self.returncode

    def terminate(self):
        self.sonlandirildi = True
        self.returncode = -15
        self._kapandi.set()

    def kill(self):
        self.returncode = -9
        self._kapandi.set()

    def wait(self, timeout=None):
        return self.returncode


class DrmKosNabizBaglantisi(unittest.TestCase):
    """drm_kos: GERCEK KareCekici + sahte HTTP yayini (her istekte yeni kare -> hep CANLI) + sahte
    Popen. Video argv'si -v/identity tasir, stdout BORUYA alinir, NabizIzleyici gozetmene baglidir.
    Sureler hiz icin kucultulur (modul sabitleri; drm_kos onlari CAGRI aninda okur, geri yuklenir)."""

    KUCUK = (("DRM_YOKLAMA_S", 0.05), ("DRM_ASGARI_ARALIK_S", 0.3), ("DRM_BORU_DONMA_S", 0.6))

    def setUp(self):
        self.y = _SahteYayin()
        self.addCleanup(self.y.kapat)
        self.y.otomatik_sira = True
        for ad, deger in self.KUCUK:
            self.addCleanup(setattr, g, ad, getattr(g, ad))
            setattr(g, ad, deger)

    def _kos(self, aralik_s, sure, stdbuf_yolu="", kayit=None):
        kayit = [] if kayit is None else kayit
        args = g._parser().parse_args(["--kip", "drm", "--kaynak", self.y.kok, "--sure", str(sure)])
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            kod = g.drm_kos(args, baslat=lambda argv, **kw: _SahtePopen(argv, kayit, aralik_s, **kw),
                            gst_yolu="gst-launch-1.0", stdbuf_yolu=stdbuf_yolu)
        return kod, kayit, out.getvalue() + err.getvalue()

    def test_G7_drm_kos_ikinci_video_borusu_YENI_nabiz_izleyicisiyle_surer(self):
        """NG (T228-D curutucusu; REVIEW_LOG D-453): yayin kisa sure 503 olup geri gelince IKINCI
        video borusu acilir; -v ciktisinda pts (gercek gst-launch gibi) yeniden ~0'dan baslar.
        Nabiz izleyicisi borular arasinda PAYLASILIRSA 'pts > son_pts' saglanmaz: saglikli ikinci
        boru 'donmus' sayilir, GORUNTU YOK <-> video dongusu. Dogru kod: her video borusuna YENI
        NabizIzleyici; ikinci boru cikisa kadar surer. Ilk boru >= ILK_NABIZ nabiz basar (son pts
        >= 2,4 s) -> paylasimli izleyicide ikinci boru >= 25 x 0,05 s = 1,25 s ilerlemez
        (> donma esigi 0,6 s): mutant zamanlamadan bagimsiz duser."""
        ILK_NABIZ, IKINCI_ASGARI = 24, 20
        kayit, hata = [], []

        def video_nabzi(i, n):
            return (len(kayit) > i and _tur(kayit[i]) == "video" and kayit[i].stdout is not None
                    and kayit[i].stdout.n >= n)

        def senaryo():
            try:
                if not _bekle(lambda: video_nabzi(1, ILK_NABIZ), tavan_s=15.0, adim_s=0.01):
                    hata.append("ilk video borusu {} nabza ulasmadi".format(ILK_NABIZ))
                    return
                self.y.kod, self.y.son_hata = 503, "kaynak acilamadi"
                if not _bekle(lambda: len(kayit) >= 3, tavan_s=10.0, adim_s=0.01):
                    hata.append("yayin 503 iken GORUNTU YOK borusu acilmadi")
            finally:
                self.y.kod, self.y.son_hata = 200, None

        iplik = threading.Thread(target=senaryo, daemon=True)
        iplik.start()
        kod, _ayni, log = self._kos(aralik_s=0.05, sure=4.5, kayit=kayit)
        iplik.join(30)
        self.assertEqual(hata, [], log)
        self.assertEqual(kod, g.CIKIS_TAMAM, log)
        self.assertEqual([_tur(s) for s in kayit], ["yok", "video", "yok", "video"],
                         "ikinci video borusu cikisa kadar SURMELI (donmus sayilmamali)\n" + log)
        self.assertTrue(kayit[1].sonlandirildi, "yayin 503 olunca ilk video borusu durdurulmali")
        self.assertIn("yayin HTTP 503", kayit[2].argv[-1])
        self.assertEqual(kayit[3].argv, g.drm_video_argv("gst-launch-1.0", self.y.kok))
        self.assertGreaterEqual(kayit[3].stdout.n, IKINCI_ASGARI,
                                "gozlem penceresi kisa: ikinci boru donma esiginden (0,6 s) uzun "
                                "gozlenmeli\n" + log)
        self.assertNotIn("ilerlemiyor", log)
        self.assertEqual(log.count("ilk nabiz"), 2,
                         "her video borusunun KENDI izleyicisi ilk nabzini loglar\n" + log)

    def test_G7_drm_kos_donmus_boru_GORUNTU_YOK_borusuna_gecer(self):
        kod, kayit, log = self._kos(aralik_s=None, sure=2.5)
        self.assertEqual(kod, g.CIKIS_TAMAM, log)
        self.assertGreaterEqual(len(kayit), 3, log)
        self.assertEqual([_tur(s) for s in kayit[:3]], ["yok", "video", "yok"], log)
        video, yok2 = kayit[1], kayit[2]
        self.assertEqual(video.argv, g.drm_video_argv("gst-launch-1.0", self.y.kok))
        self.assertEqual(video.kw.get("stdout"), subprocess.PIPE, "-v ciktisi boruya alinmali")
        self.assertIsNone(kayit[0].stdout, "GORUNTU YOK borusunun ciktisi boruya ALINMAZ")
        self.assertTrue(video.sonlandirildi)
        self.assertIn("video borusu ilerlemiyor", yok2.argv[-1])
        gecikme = yok2.t - video.t
        self.assertGreater(gecikme, 0.6, "esikten ONCE kapatildi")
        self.assertLess(gecikme, 0.6 + 1.0, "donmus boru gec algilandi")
        self.assertIn("ilk nabiz", log)
        self.assertIn("gst: Setting pipeline to PAUSED ...", log)

    def test_G7_drm_kos_surekli_nabiz_video_surer(self):
        kod, kayit, log = self._kos(aralik_s=0.05, sure=2.0)
        self.assertEqual(kod, g.CIKIS_TAMAM, log)
        self.assertEqual([_tur(s) for s in kayit], ["yok", "video"], log)
        self.assertNotIn("ilerlemiyor", log)
        self.assertTrue(kayit[1].sonlandirildi, "cikista video borusu durdurulur")
        self.assertIn("[UYARI] stdbuf yok", log)

    def test_G7_drm_kos_stdbuf_onekli_video_borusu(self):
        kod, kayit, log = self._kos(aralik_s=0.05, sure=1.2, stdbuf_yolu="/usr/bin/stdbuf")
        self.assertEqual(kod, g.CIKIS_TAMAM, log)
        self.assertEqual([_tur(s) for s in kayit], ["yok", "video"], log)
        video = kayit[1]
        self.assertEqual(video.argv, ["/usr/bin/stdbuf", "-oL"] +
                         g.drm_video_argv("gst-launch-1.0", self.y.kok))
        self.assertEqual(video.kw.get("stdout"), subprocess.PIPE)
        self.assertEqual(kayit[0].argv[0], "gst-launch-1.0", "GORUNTU YOK borusuna onek GEREKMEZ")
        self.assertNotIn("stdbuf yok", log)
        self.assertIn("ilk nabiz", log)


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
        m = _cizili_ayikla(KURULUM.read_text(encoding="utf-8"))   # D-453: cizili metin sayilmaz
        for parca in ("AutomaticLoginEnable=true", "WaylandEnable=false", "~/.config/autostart",
                      "DisplayPort", "DP→HDMI", "Mini HDMI", "192.168.144.25", "setip.txt",
                      "rtsp://192.168.144.25:8554/main.264", "Camera 1", "EDID", "Argus", "3 fps",
                      "ÖLÇÜLEMEDİ", "kmssink", "nvdrmvideosink", "192.168.144.30",
                      "gir1.2-gst-rtsp-server-1.0", "KARAR ÜRETMEZ"):
            self.assertIn(parca, m)
        for dosya in (DESKTOP, DRM_BIRIM, XORG):
            self.assertIn(dosya.name, m)

    def test_G8_kurulum_T228D_kodek_celiskisi_nabiz_DOGRULANACAK_eski_komut_cizili(self):
        ham = KURULUM.read_text(encoding="utf-8")
        m = _cizili_ayikla(ham)   # D-453: YENI icerik cizili araliklar AYIKLANMIS metinde aranir
        kodlayici = re.search(r"(?m)^\| Kodlayıcı \|.*$", m)
        self.assertIsNotNone(kodlayici, "§1 Kodlayıcı satiri yok")
        for parca in ("H.264/H.265 çelişkili", "TASARIM §5", "V1.1", "DOĞRULANACAK"):
            self.assertIn(parca, kodlayici.group(0))
        bol5 = _kurulum_bolumu(m, "## 5. DRM kipi", "\n## 6.")
        self.assertIn(g.komut_metni(g.drm_video_argv("gst-launch-1.0")), bol5,
                      "§5 video borusu komutu kodla (--kuru) AYNI olmali")
        for parca in ("identity name=nabiz silent=false", "--nabiz-sina", "2 ardışık", "≥ 3 s",
                      "> 3 s", "nabız satırı biçimi Jetson'da ÖLÇÜLEMEDİ — DOĞRULANACAK",
                      "ZAMANINDA", "TOPLU", "`drm_kos` video borusunu `stdbuf -oL` önekiyle koşar",
                      "`video borusu kendiliginden bitti (rc N)`"):
            self.assertIn(parca, bol5)
        self.assertRegex(m, r'(?m)^\| drm kipinde kırmızı "video borusu kendiliginden bitti '
                            r'\(rc N\)" \|', "§8 sorun giderme satiri (T228-D2)")
        bol9 = _kurulum_bolumu(m, "## 9. ÖLÇÜLEMEDİ")
        for parca in ("`gst-launch-1.0 -v` nabız satırı biçimi", "`stdbuf -oL`",
                      "Dönüştürücünün canlı kodeki (H.264/H.265 çelişkili)"):
            self.assertIn(parca, bol9, "§9 OLCULEMEDI maddesi dusmemeli ya da cizilmemeli")
        # D-453/D-454: olculmemis GECTI yok — NORMALLESTIRILMIS metinde aranir ('tutar', karma yazim,
        # kalin parcali ya da yumusak tireli 'doğrulandı' da sayilir)
        for ad, metin in (("§1 Kodlayıcı", kodlayici.group(0)), ("§5", bol5), ("§9", bol9)):
            bulunan = _gecti_bul(metin)
            self.assertIsNone(bulunan, "{}: '{}' — Jetson'da OLCULMEDI; olculunce bu kilit KANITLA "
                              "(§4 sonuc sutunu) guncellenir".format(ad, bulunan))
        self.assertRegex(m, r"(?m)^\| 9 \|.*--nabiz-sina.*\| ÖLÇÜLECEK \|$")
        # eski komut SILINMEDI, cizildi + tarih (runbook kurali) — HAM metinde denetlenir
        self.assertRegex(_kurulum_bolumu(ham, "## 5. DRM kipi", "\n## 6."),
                         r"~~10 Eylül \(T228\): `gst-launch-1\.0 -e 'souphttpsrc[^`]*`~~")

    def test_G8_D453_D454_olculmemis_hukum_celiski_eski_komut(self):
        """D-453/D-454 (T228-D2): kilitli hukumlere CIZIP ya da BASKA SOZLE donulemez. Metin cizili
        araliklar ayiklanip NORMALLESTIRILIR (_normal: tipografik kesme/tire, kalin/italik, yumusak
        tire, Turkce harf katlamasi).
        (1) Belge GENELINDE olculmemis GECTI yok — tek istisna ust kural cumlesi 'ÖLÇÜLEMEDİ ≠ GEÇTİ'.
        (2) Ust hukum 'hiçbiri Jetson'da koşulmadı'; §4 basligi 'hepsi şu an ÖLÇÜLEMEDİ'; §4
            tablosunun 1-9. adimlarinin sonuc hucresi TAM 'ÖLÇÜLECEK'.
        (3) §5'te CELISKILI ikinci hukum yok: 'N ardışık', '≥ N s' / '>= N s', '> N s' sayilarinin
            HEPSI koddaki on kayitli sabitlerle ayni (kalin sayi da sayilir).
        (4) Eski (nabizsiz) video borusu §5 CANLI metninde yok: gst-launch + souphttpsrc tasiyan her
            satirda '-v' ve identity nabzi var (tipografik tirnakli kopya da yakalanir)."""
        m = _cizili_ayikla(KURULUM.read_text(encoding="utf-8"))
        n = _normal(m)
        kural = _normal("ÖLÇÜLEMEDİ ≠ GEÇTİ")
        self.assertIn(kural, n, "ust kural cumlesi 'ÖLÇÜLEMEDİ ≠ GEÇTİ' dusmemeli")
        bulunan = _gecti_bul(n.replace(kural, ""))
        self.assertIsNone(bulunan, "belgede olculmemis hukum '{}' — Jetson'da hicbir adim KOSULMADI; "
                          "olculunce §4 sonuc sutunu ve bu kilit KANITLA guncellenir".format(bulunan))
        self.assertIn("hiçbiri Jetson'da koşulmadı", m, "ust hukum cizilmemeli/degismemeli")
        bol4 = _kurulum_bolumu(m, "## 4. Doğrulama sırası")
        self.assertIn("hepsi şu an ÖLÇÜLEMEDİ", bol4.split("\n", 1)[0], "§4 basligi")
        sonuclar = {int(s.group(1)): s.group(2) for s in
                    re.finditer(r"(?m)^\|\s*(\d+)\s*\|.*\|([^|\n]*)\|[ \t]*$", bol4)}
        self.assertTrue(set(range(1, 10)) <= set(sonuclar), "§4 adimlari: {}".format(sorted(sonuclar)))
        for no, sonuc in sorted(sonuclar.items()):
            self.assertEqual(_normal(sonuc).strip(), "olculecek", "§4 adim {} sonuc hucresi '{}' — "
                             "tam ÖLÇÜLECEK olmali".format(no, sonuc.strip()))
        n5 = _normal(_kurulum_bolumu(m, "## 5. DRM kipi", "\n## 6."))
        sayi = r"(\d+(?:[.,]\d+)?)"
        for ad, kalip, sabit in (
                ("'N ardışık' (DRM_CANLI_ARDISIK)", sayi + r"\s*ardisik", g.DRM_CANLI_ARDISIK),
                ("'≥ N s' (DRM_ASGARI_ARALIK_S)", r"(?:≥|>=)\s*" + sayi + r"\s*s(?![a-z])",
                 g.DRM_ASGARI_ARALIK_S),
                ("'> N s' (DRM_BORU_DONMA_S)", r"(?<![<>=≥≤!-])>(?!=)\s*" + sayi + r"\s*s(?![a-z])",
                 g.DRM_BORU_DONMA_S)):
            degerler = [float(x.replace(",", ".")) for x in re.findall(kalip, n5)]
            self.assertTrue(degerler, "§5'te {} hukmu yok".format(ad))
            self.assertEqual(set(degerler), {float(sabit)},
                             "§5'te CELISKILI {} hukmu: {} (kod {})".format(ad, degerler, sabit))
        borular = [s for s in n5.splitlines() if "gst-launch" in s and "souphttpsrc" in s]
        self.assertTrue(borular, "§5 video borusu komutu yok")
        for s in borular:
            self.assertIn("gst-launch-1.0 -v ", s, "§5 CANLI metinde nabizsiz (eski) video borusu: " + s)
            self.assertIn("identity name=nabiz silent=false", s, "§5 CANLI metinde nabizsiz boru: " + s)


#: D-453 (mimar kurali, 10 Eylul): markdown belge kilitleri YENI icerigi cizili (~~...~~) araliklar
#: AYIKLANMIS metinde arar — ustu cizilen not ya da OLCULEMEDI/DOGRULANACAK maddesi kilidi GECMEZ;
#: eski metnin cizili durdugunu denetleyen kilit HAM metinde kalir.
def _cizili_ayikla(metin):
    return re.sub(r"~~.*?~~", "", metin, flags=re.S)


def _kurulum_bolumu(metin, baslik, bitis="\n## "):
    return metin.split(baslik, 1)[1].split(bitis, 1)[0]


#: D-454 (T221-D2 curutucusu: 'tutar', tipografik kesme ’, 'tamamı', kalin sayilar kilidi deldi):
#: yasak/celiski aramalari NORMALLESTIRILMIS metinde yapilir — sifir genislikli karakter ve yumusak
#: tire ayiklanir; NFKD + birlesik isaretler atilir (ğ->g, ş->s, İ->I ...), ı->i; kesme/tirnak
#: (’ ‘ ‚ ‛ ´ ` ʼ ʹ ′) -> ', tireler (‐ ‑ ‒ – — ― −) -> -, vurgu (* _) ayiklanir, kucuk harf.
#: '≠' NFKD'de '=' + U+0338'e ayrisir, isaret atilinca '=' olurdu (anlam TERSINE doner) -> once '!='.
_SIFIR_GENISLIK = dict.fromkeys(map(ord, "\u00ad\u200b\u200c\u200d\u200e\u200f\u2060\ufeff"))
_KATLA = str.maketrans({**{c: "'" for c in "\u2018\u2019\u201a\u201b\u00b4`\u02bc\u02b9\u2032"},
                        **{c: "-" for c in "\u2010\u2011\u2012\u2013\u2014\u2015\u2212"},
                        "\u0131": "i", "*": None, "_": None})


def _normal(metin):
    s = metin.translate(_SIFIR_GENISLIK).replace("\u2260", "!=")  # '≠' (U+2260)
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    return s.translate(_KATLA).lower()


#: Olculmemis GECTI kalibi (D-453/D-454) — _normal() ciktisi uzerinde: OLCULEMEDI/DOGRULANACAK
#: tasiyan yerlerde bu hukumler ancak Jetson olcumu KANITLA islenince (kilit de o zaman guncellenir)
#: yazilabilir. 'tutar/tuttu/tutuyor' D-454 (T221-D2 'doğrulandı: tutar') ile eklendi.
_GECTI_KALIBI = re.compile(r"(?<![a-z0-9])(?:dogrulan(?:di|mistir)|gec(?:ti|mistir)|"
                           r"olcul(?:du|mustur)|tut(?:ar|tu|uyor)|onaylandi)(?![a-z0-9])")


def _gecti_bul(metin):
    """Normallestirilmis metinde ilk olculmemis GECTI hukmu (yoksa None)."""
    b = _GECTI_KALIBI.search(_normal(metin))
    return b.group(0) if b else None


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


# ── G11 ───────────────────────────────────────────────────────────────────────
class _SahteCv:
    """cv2 yerine (x11_kos `cv=`): pencere ACMAZ. imshow tuvali (ve cizim anindaki saati) saklar;
    waitKey `adim(cizilen_tuval_sayisi)`'ni cagirir ve onun tus kodunu dondurur."""
    error = cv2.error
    WINDOW_NORMAL = cv2.WINDOW_NORMAL
    WND_PROP_FULLSCREEN = cv2.WND_PROP_FULLSCREEN
    WINDOW_FULLSCREEN = cv2.WINDOW_FULLSCREEN

    def __init__(self, adim, saat_oku=time.monotonic):
        self.adim = adim
        self.saat_oku = saat_oku
        self.tuvaller = []
        self.cizim_saatleri = []
        self.cagrilar = []

    def namedWindow(self, ad, bayrak):
        self.cagrilar.append(("namedWindow", ad, bayrak))

    def setWindowProperty(self, ad, ozellik, deger):
        self.cagrilar.append(("setWindowProperty", ad, ozellik, deger))

    def imshow(self, ad, tuval):
        self.cagrilar.append(("imshow", ad))
        self.tuvaller.append(np.array(tuval, copy=True))
        self.cizim_saatleri.append(self.saat_oku())

    def waitKey(self, _ms):
        return self.adim(len(self.tuvaller))

    def destroyAllWindows(self):
        self.cagrilar.append(("destroyAllWindows",))


class _SahteCekici:
    """KareCekici arayuzu (iplik YOK); anlik() testin yazdigi durumu dondurur."""

    def __init__(self, kaynak, hz):
        self.kare_url = kaynak + kk.KARE_YOLU
        self.hz = hz
        self.durum = (None, None, None, None)
        self.olaylar = []

    def start(self):
        self.olaylar.append("start")

    def anlik(self):
        return self.durum

    def durdur(self):
        self.olaylar.append("durdur")

    def join(self, _t=None):
        self.olaylar.append("join")

    def sayaclar(self):
        return {"istek": 0, "basari": 0, "yeni_kare": 0, "hata": 0}


class X11Dongusu(unittest.TestCase):
    """T228-D: x11_kos DONGUSU sahte cv2 ile (pencere ACILMAZ). Kilitlenen cagri noktasi:
    dongudeki `ekran_durumu(saat(), son_t, cekme_hatasi)` — hata None'lanirsa (mutasyon MG) DUSER."""

    HATALAR = ("yayin HTTP 503: kaynak acilamadi (deneme 3)",
               "yayin erisilemiyor (http://127.0.0.1:8081/kare.jpg): [WinError 10061] baglanti "
               "reddedildi")

    def test_G11_x11_dongusu_CANLI_iken_503_ya_da_erisilemez_ILK_cizim_GORUNTU_YOK(self):
        for hata in self.HATALAR:
            with self.subTest(hata=hata[:30]):
                saat = [100.0]
                kare = _yesil_kare()
                tut = {}

                def uret(kaynak, hz):
                    c = tut["c"] = _SahteCekici(kaynak, hz)
                    c.durum = (kare, saat[0] - 0.1, None, "1")          # taze kare: CANLI
                    return c

                def adim(n, hata=hata):                                  # n: cizilen tuval sayisi
                    saat[0] += 0.2
                    c = tut["c"]
                    if n < 3:
                        c.durum = (kare, saat[0], None, str(n + 1))      # her cizimde yeni kare
                    elif n == 3:
                        c.durum = (kare, c.durum[1], hata, c.durum[3])   # yayin 503/erisilemez;
                    else:                                                # son kare cekicide KALIR
                        return ord("q")
                    return -1

                sahte = _SahteCv(adim, saat_oku=lambda: saat[0])
                d = tempfile.mkdtemp(prefix="navitas_t228d_x11_")
                self.addCleanup(shutil.rmtree, d, True)
                args = g._parser().parse_args(["--tuval-kaydi", d])
                out, err = io.StringIO(), io.StringIO()
                with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                    kod = g.x11_kos(args, ortam={}, platform="win32", saat=lambda: saat[0],
                                    cv=sahte, cekici_uret=uret)
                self.assertEqual(kod, g.CIKIS_TAMAM, err.getvalue())
                self.assertEqual(len(sahte.tuvaller), 4)
                for t in sahte.tuvaller[:3]:
                    self.assertEqual(_piksel(t, 360, 640), YESIL, "CANLI iken kare gosterilmeli")
                ilk = sahte.tuvaller[3]
                self.assertEqual(_piksel(ilk, 5, 5), g.KIRMIZI_ZEMIN,
                                 "hatadan sonraki ILK cizim kirmizi GORUNTU YOK degil")
                self.assertEqual(_yesil_piksel(ilk), 0, "GORUNTU YOK ekraninda eski kare pikseli var")
                # MG duyarliligi: ayni anda hata yok sayilsaydi ekran CANLI olurdu (kare 0,2 s)
                self.assertEqual(g.ekran_durumu(sahte.cizim_saatleri[3], tut["c"].durum[1],
                                                None).durum, g.DURUM_CANLI)
                self.assertIn("ekran CANLI -> GORUNTU_YOK ({})".format(hata), err.getvalue())
                self.assertEqual(sorted(os.listdir(d)),
                                 ["01_CANLI.jpg", "02_GORUNTU_YOK.jpg", "son.jpg"])
                self.assertEqual(tut["c"].olaylar, ["start", "durdur", "join"])
                self.assertEqual(sahte.cagrilar[:2],
                                 [("namedWindow", g.PENCERE_ADI, cv2.WINDOW_NORMAL),
                                  ("setWindowProperty", g.PENCERE_ADI, cv2.WND_PROP_FULLSCREEN,
                                   cv2.WINDOW_FULLSCREEN)])
                self.assertEqual(sahte.cagrilar[-1], ("destroyAllWindows",))

    def test_G11_x11_dongusu_gercek_cekici_gercek_HTTP_CANLI_sonra_503(self):
        y = _SahteYayin()
        self.addCleanup(y.kapat)
        y.otomatik_sira = True
        tut = {}

        def uret(kaynak, hz):
            tut["c"] = g.KareCekici(kaynak, hz=hz, log=_sessiz)
            return tut["c"]

        iz = {"faz": 0, "n_hata": None, "yas": None, "bitis": time.monotonic() + 15.0}

        def adim(n):
            if time.monotonic() > iz["bitis"]:
                return ord("q")
            if iz["faz"] == 0:
                if _yesil_piksel(sahte.tuvaller[-1]) > 1000:            # CANLI cizildi
                    y.otomatik_sira = False
                    y.kod, y.son_hata = 503, "kaynak acilamadi (deneme 3)"
                    c = tut["c"]
                    _bekle(lambda: c.anlik()[2] is not None, 3.0, 0.005)
                    iz["yas"] = time.monotonic() - c.anlik()[1]
                    iz["n_hata"], iz["faz"] = n, 1
                else:
                    time.sleep(0.02)
                return -1
            return ord("q")                                             # hatadan sonra TEK cizim

        sahte = _SahteCv(adim)
        args = g._parser().parse_args(["--kaynak", y.kok, "--hz", "20"])
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            kod = g.x11_kos(args, ortam={}, platform="win32", cv=sahte, cekici_uret=uret)
        self.assertEqual(kod, g.CIKIS_TAMAM, err.getvalue())
        self.assertEqual(iz["faz"], 1, "CANLI cizim hic olmadi: " + err.getvalue())
        self.assertEqual(len(sahte.tuvaller), iz["n_hata"] + 1, "hatadan sonra tam BIR cizim")
        self.assertLess(iz["yas"], g.BAYAT_ESIGI_S, "MG duyarliligi: hata aninda kare taze olmali")
        ilk = sahte.tuvaller[iz["n_hata"]]
        self.assertEqual(_piksel(ilk, 5, 5), g.KIRMIZI_ZEMIN)
        self.assertEqual(_yesil_piksel(ilk), 0, "GORUNTU YOK ekraninda eski kare pikseli var")
        self.assertIn("HTTP 503", err.getvalue())
        self.assertFalse(tut["c"].is_alive(), "cekici iplik durdurulmali")


if __name__ == "__main__":
    unittest.main()
