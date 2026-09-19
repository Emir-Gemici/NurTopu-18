"""2026-09-19 (Jetson olcumu): servis kipinde kamera YOK/KOPTU iken surec CIKMAZ.

NEDEN: `rpi_inference --camera --ekransiz` systemd altinda kosarken CSI kamera
yoktu; kopru `/video` 503 donuyor, `run_camera` KAMERA_ACILAMADI ile donuyor,
`main()` cikiyor ve systemd 2-60 s'de bir yeniden kaldiriyordu (sayac 32). Her
turda YOLO yeniden yukleniyor (~4,5 s CPU), telsiz halkasi (1 Hz HEARTBEAT)
yikiliyordu: YKS kalp atisini dakikada birkac saniye goruyordu. Ayni cikis
oturum ortasinda 30 ardisik dusen karede (KAMERA_BITIS_DUSEN_KARE) de oluyordu.

Kilitler (gercek uyku YOK: `bekle`/`saat` enjekte, `time.sleep` patlatilir):
  a) acilamadi x2 -> 3. acilista kareler islenir; `yeniden_acma` sayilir; TEK
     [KAMERA_BEKLIYOR], TEK [KAMERA_GERI_GELDI]; bekleme dilimleri <= 0,5 s;
     gorev kaydina kesinti basina BIR KAMERA_BEKLIYOR + KAMERA_GERI_GELDI.
  b) `kamera_bekle=False` -> eski davranis: ANINDA KAMERA_ACILAMADI; hat
     koptugunda KAMERA_BITIS_DUSEN_KARE ile doner (yeniden acma YOK).
  c) bekleme sirasinda sinyal -> KAMERA_BITIS_SINYAL, BASKA acma denemesi YOK.
  d) oturum ortasinda 30 dusen kare -> birak + yeniden ac, dongu SURER.
  e) tani satiri: 30 s'den once ikinci satir YOK; /dev/video durumu ve kopru
     /durum alanlari satirda; getirme/listeleme hatasi ISTISNA YUKSELTMEZ.
  f) main(): --ekransiz -> True; --ekransiz --kamera-bekleme-yok -> False;
     --ekransiz yok -> False.
  g) KARAR YOLU: yeniden acma histerezisi ATLATAMAZ (tek KararYumusatici);
     kesintili kosumun yayinlari kesintisiz kosumla BIREBIR ayni.
"""

import contextlib
import io
import re
import sys
import unittest
import urllib.error
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import cv2
import numpy as np

KOK = Path(__file__).resolve().parents[1]
for _p in (KOK / "codes", KOK / "comms", KOK / "scripts", KOK / "tests"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import rpi_inference as ri  # noqa: E402
from test_faz_b_rpi_ekransiz import _Yayinla, _maskeler  # noqa: E402

KOPRU_URL = "http://127.0.0.1:8080/video"
# Jetson'da 19 Eylul'de olculen kopru /durum cevabi (ozet).
KOPRU_DURUM = {"kaynak_acik": False, "son_hata": "30 ardisik dusen kare (ust sinir 30)",
               "acma_denemesi": 1304, "dusen_kare": 39120, "kare_sayaci": 0}


class _SahteKamera:
    """`cv2.VideoCapture` yerine: `kare` adet kare, sonra HEP dusen kare."""

    def __init__(self, acik=True, kare=0):
        self._acik = acik
        self.kalan = kare
        self.okuma = 0
        self.release_sayisi = 0

    def isOpened(self):
        return self._acik

    def read(self):
        self.okuma += 1
        if not self._acik or self.kalan <= 0:
            return False, None
        self.kalan -= 1
        return True, np.full((360, 640, 3), 127, np.uint8)

    def release(self):
        self.release_sayisi += 1


class _Fabrika:
    """Sirayla kamera verir; biterse ACILAMAYAN kamera. `tavan` asilirsa
    AssertionError — mutant sonsuz donguye girerse test ASILMAZ, DUSER."""

    def __init__(self, *kameralar, tavan=40):
        self.kameralar = list(kameralar)
        self.acilan = []
        self.tavan = tavan

    def __call__(self, kaynak):
        if len(self.acilan) >= self.tavan:
            raise AssertionError(f"yeniden acma tavani ({self.tavan}) asildi")
        i = len(self.acilan)
        kamera = self.kameralar[i] if i < len(self.kameralar) else _SahteKamera(acik=False)
        self.acilan.append((kaynak, kamera))
        return kamera


class _Saat:
    """Sahte monotonic saat; `bekle` saati ilerletir (gercek uyku yok)."""

    def __init__(self, dur_t=None):
        self.t = 0.0
        self.beklemeler = []
        self.dur_t = dur_t

    def __call__(self):
        return self.t

    def bekle(self, s):
        self.beklemeler.append(s)
        self.t += s
        if self.dur_t is not None and self.t >= self.dur_t:
            ri.durdurmayi_iste()


class _SahteKayit:
    def __init__(self, patlat=None):
        self.olaylar = []
        self.patlat = patlat
        self.kapandi = 0

    def yaz(self, olay, **alanlar):
        if self.kapandi:                      # HakemKaydi gibi: kapaliysa RED
            raise RuntimeError("kayit kapali")
        if olay == self.patlat:
            raise OSError(28, "No space left on device")
        self.olaylar.append((olay, alanlar))

    def kapat(self):
        self.kapandi += 1

    def adlar(self):
        return [o for o, _ in self.olaylar]


def _analiz(kararlar, dur_n):
    """Kare sirasina gore karar; `dur_n`. analizden sonra durdurma bayragi."""
    say = {"n": 0}

    def analiz(*_a, **_k):
        r = kararlar[min(say["n"], len(kararlar) - 1)]
        say["n"] += 1
        if say["n"] >= dur_n:
            ri.durdurmayi_iste()
        return r
    analiz.say = say
    return analiz


_R1 = (1, 0.9, [(1, 2), (3, 4)], None)
_R3 = (3, 0.9, [(5, 6), (7, 8)], None)


def _kos(fabrika, *, kamera_bekle, saat=None, analiz=None, kaynak=None,
         gorev_kaydi=None, cihazlar=(), durum=None, uyku=None):
    """run_camera'yi sahte kamera/algi ile kos; (ozet, yayinlar, cikti, durum_mock).

    `time.sleep` HER ZAMAN sahtedir (`uyku`): eski kipin dusen-kare beklemesi
    de gercek uyumaz. Servis kipi testleri `uyku`nun HIC cagrilmadigini
    (beklemelerin enjekte `bekle`den gectigini) ayrica dogrular."""
    saat = saat if saat is not None else _Saat()
    analiz = analiz if analiz is not None else _analiz([_R1], 10 ** 6)
    uyku = uyku if uyku is not None else mock.Mock()
    yayinla = _Yayinla()
    durum_mock = mock.Mock(side_effect=(durum if durum is not None
                                        else (lambda _u, _z: dict(KOPRU_DURUM))))
    with mock.patch.object(cv2, "VideoCapture", side_effect=fabrika), \
            mock.patch.object(ri.time, "sleep", uyku), \
            mock.patch.object(ri, "get_masks", return_value=_maskeler()), \
            mock.patch.object(ri, "analyze_path", analiz), \
            mock.patch.object(ri, "_karari_yayinla", yayinla), \
            mock.patch.object(ri, "_video_cihazlari", return_value=list(cihazlar)), \
            mock.patch.object(ri, "_kopru_durumunu_getir", durum_mock), \
            contextlib.redirect_stdout(io.StringIO()) as cikti:
        ozet = ri.run_camera(SimpleNamespace(predict=lambda *a, **k: [object()]),
                             0.30, canli_olcek=(lambda _w: 0.05), kaynak=kaynak,
                             yayinci=object(), ekransiz=True, gorev_kaydi=gorev_kaydi,
                             kamera_bekle=kamera_bekle, bekle=saat.bekle, saat=saat)
    return ozet, yayinla.cagrilar, cikti.getvalue(), durum_mock


def _satirlar(cikti, onek):
    return [s for s in cikti.splitlines() if s.startswith(onek)]


class _BayrakTemiz(unittest.TestCase):
    def setUp(self):
        ri.durdurma_bayragini_sifirla()

    def tearDown(self):
        ri.durdurma_bayragini_sifirla()


# ── a) acilamadi x2 -> acilir, kareler islenir ──────────────────────────────

class AcilamadiSonraGeldi(_BayrakTemiz):
    def test_a_iki_basarisiz_acilistan_sonra_kareler_islenir(self):
        iyi = _SahteKamera(acik=True, kare=10)
        k1, k2 = _SahteKamera(acik=False), _SahteKamera(acik=False)
        fabrika = _Fabrika(k1, k2, iyi)
        saat = _Saat()
        kayit = _SahteKayit()
        analiz = _analiz([_R1], 3)
        uyku = mock.Mock()
        ozet, yayinlar, cikti, _ = _kos(fabrika, kamera_bekle=True, saat=saat,
                                        analiz=analiz, gorev_kaydi=kayit, uyku=uyku)
        uyku.assert_not_called()
        self.assertEqual(3, len(fabrika.acilan), "3 acilis beklenirdi (2 basarisiz + 1)")
        self.assertEqual(3, analiz.say["n"], "kareler islenmedi")
        self.assertEqual(3, ozet["okunan"], ozet)
        self.assertGreaterEqual(len(yayinlar), 1, "karar yayini yok")
        self.assertEqual(1, ozet["yeniden_acma"], ozet)
        self.assertEqual(ri.KAMERA_BITIS_SINYAL, ozet["bitis"])
        bekliyor = _satirlar(cikti, "[KAMERA_BEKLIYOR]")
        geldi = _satirlar(cikti, "[KAMERA_GERI_GELDI]")
        self.assertEqual(1, len(bekliyor), cikti)
        self.assertEqual(1, len(geldi), cikti)
        self.assertIn("deneme=1", bekliyor[0])
        self.assertIn(f"neden={ri.KAMERA_BITIS_ACILAMADI}", bekliyor[0])
        self.assertIn("deneme=3", geldi[0])
        self.assertIn("bekleme_s=3.0", geldi[0], "geri cekilme 1 + 2 s olmali")
        # Basarisiz yakalayicilar birakildi; iyi olan run_camera finally'sinde.
        self.assertEqual([1, 1, 1], [k1.release_sayisi, k2.release_sayisi,
                                     iyi.release_sayisi])
        # Bekleme dilimli: SIGTERM en gec bir dilim gecikir.
        self.assertTrue(saat.beklemeler, "bekleme yapilmadi")
        self.assertLessEqual(max(saat.beklemeler), ri.KAMERA_SINYAL_YOKLAMA_S)
        self.assertAlmostEqual(3.0, sum(saat.beklemeler))
        # Gorev kaydi: kesinti basina BIR BEKLIYOR, bir GERI_GELDI, kareler sonra.
        adlar = kayit.adlar()
        self.assertEqual(1, adlar.count("KAMERA_BEKLIYOR"), adlar)
        self.assertEqual(1, adlar.count("KAMERA_GERI_GELDI"), adlar)
        self.assertLess(adlar.index("KAMERA_BEKLIYOR"), adlar.index("KAMERA_GERI_GELDI"))
        self.assertLess(adlar.index("KAMERA_GERI_GELDI"), adlar.index("KARE"))
        self.assertEqual("KAMERA_BITTI", adlar[-1])
        self.assertEqual(1, kayit.olaylar[-1][1]["yeniden_acma"])
        self.assertIn("yeniden_acma=1", cikti)   # bitis satiri

    def test_a2_kayit_yazma_hatasi_kosumu_DURDURMAZ(self):
        """KAMERA_BEKLIYOR yazilamazsa (disk dolu) kosum SURER, kareler islenir
        ve karar yayini kayitsiz kosumla BIREBIR ayni. ServisKamerasi'nin kayit
        referansi dongu govdesininkinden ayridir: govde kapanmis kayda ilk
        KARE'de BIR kez daha UYARI basabilir (en fazla 2) — her karede DEGIL."""
        fabrika = _Fabrika(_SahteKamera(acik=False), _SahteKamera(acik=True, kare=5))
        kayit = _SahteKayit(patlat="KAMERA_BEKLIYOR")
        ozet, kayitli, cikti, _ = _kos(fabrika, kamera_bekle=True,
                                       analiz=_analiz([_R1, _R3, _R3], 3), gorev_kaydi=kayit)
        ri.durdurma_bayragini_sifirla()
        _, kayitsiz, _, _ = _kos(
            _Fabrika(_SahteKamera(acik=False), _SahteKamera(acik=True, kare=5)),
            kamera_bekle=True, analiz=_analiz([_R1, _R3, _R3], 3))
        self.assertEqual(3, ozet["okunan"])
        self.assertGreaterEqual(len(kayitsiz), 1)
        self.assertEqual(kayitsiz, kayitli, "kayit hatasi karar yayinini degistirdi")
        self.assertIn(cikti.count("UYARI: gorev kaydi yazilamadi"), (1, 2), cikti)
        self.assertGreaterEqual(kayit.kapandi, 1)
        self.assertEqual([], kayit.adlar(), "kapanan kayda yazildi")


# ── b) kamera_bekle=False: ESKI davranis ────────────────────────────────────

class EskiDavranis(_BayrakTemiz):
    def test_b_acilamayinca_ANINDA_KAMERA_ACILAMADI(self):
        fabrika = _Fabrika(_SahteKamera(acik=False), _SahteKamera(acik=True, kare=5))
        saat = _Saat()
        ozet, yayinlar, cikti, durum = _kos(fabrika, kamera_bekle=False, saat=saat)
        self.assertEqual({"bitis": ri.KAMERA_BITIS_ACILAMADI, "okunan": 0,
                          "dusen_toplam": 0, "dusen_ardisik_maks": 0}, ozet)
        self.assertEqual(1, len(fabrika.acilan), "eski kipte yeniden acma YOK")
        self.assertEqual([], saat.beklemeler)
        self.assertEqual([], yayinlar)
        self.assertIn("Kamera acilamadi", cikti)
        self.assertNotIn("[KAMERA_BEKLIYOR]", cikti)
        durum.assert_not_called()

    def test_b2_hat_koptugunda_DUSEN_KARE_ile_doner(self):
        fabrika = _Fabrika(_SahteKamera(acik=True, kare=2), _SahteKamera(acik=True, kare=5))
        ozet, _, cikti, _ = _kos(fabrika, kamera_bekle=False)
        self.assertEqual(ri.KAMERA_BITIS_DUSEN_KARE, ozet["bitis"])
        self.assertEqual(2, ozet["okunan"])
        self.assertEqual(1, len(fabrika.acilan))
        self.assertNotIn("yeniden_acma", ozet, "eski kipin ozet sozlesmesi degismemeli")
        self.assertNotIn("[KAMERA_GERI_GELDI]", cikti)


# ── c) bekleme sirasinda sinyal ─────────────────────────────────────────────

class BeklerkenSinyal(_BayrakTemiz):
    def test_c_sinyal_beklemeyi_keser_BASKA_acma_denemesi_yok(self):
        k1 = _SahteKamera(acik=False)
        fabrika = _Fabrika(k1, _SahteKamera(acik=True, kare=5))
        saat = _Saat(dur_t=0.0)          # ilk bekleme diliminde SIGTERM
        ozet, yayinlar, cikti, _ = _kos(fabrika, kamera_bekle=True, saat=saat)
        self.assertEqual(ri.KAMERA_BITIS_SINYAL, ozet["bitis"])
        self.assertEqual(1, len(fabrika.acilan), "sinyalden sonra yeniden acildi")
        self.assertEqual(1, len(saat.beklemeler), saat.beklemeler)
        self.assertLessEqual(saat.beklemeler[0], ri.KAMERA_SINYAL_YOKLAMA_S)
        self.assertEqual([], yayinlar)
        self.assertEqual(1, k1.release_sayisi)
        self.assertIn("KONTROLLU DURDURMA", cikti)
        self.assertIn(f"neden={ri.KAMERA_BITIS_SINYAL}", cikti)   # bitis raporu

    def test_c2_bayrak_onceden_kuruluysa_hic_beklemez(self):
        fabrika = _Fabrika(_SahteKamera(acik=False))
        saat = _Saat()
        ri.durdurmayi_iste()
        ozet, _, _, _ = _kos(fabrika, kamera_bekle=True, saat=saat)
        self.assertEqual(ri.KAMERA_BITIS_SINYAL, ozet["bitis"])
        self.assertEqual([], saat.beklemeler)
        self.assertEqual(1, len(fabrika.acilan))


# ── d) oturum ortasinda hat koptu ───────────────────────────────────────────

class OturumOrtasindaKopma(_BayrakTemiz):
    def test_d_30_dusen_kare_sonrasi_yeniden_acar_ve_SURER(self):
        k1 = _SahteKamera(acik=True, kare=2)
        k2 = _SahteKamera(acik=True, kare=10)
        fabrika = _Fabrika(k1, k2)
        saat = _Saat()
        kayit = _SahteKayit()
        analiz = _analiz([_R1], 5)
        uyku = mock.Mock()
        ozet, _, cikti, _ = _kos(fabrika, kamera_bekle=True, saat=saat,
                                 analiz=analiz, gorev_kaydi=kayit, uyku=uyku)
        uyku.assert_not_called()
        self.assertEqual(2, len(fabrika.acilan))
        self.assertEqual(5, analiz.say["n"], "yeniden acilan kameranin kareleri islenmedi")
        self.assertEqual(5, ozet["okunan"])
        self.assertEqual(ri.KAMERA_DUSEN_KARE_UST_SINIRI, ozet["dusen_toplam"])
        self.assertEqual(ri.KAMERA_DUSEN_KARE_UST_SINIRI, ozet["dusen_ardisik_maks"])
        self.assertEqual(1, ozet["yeniden_acma"])
        self.assertEqual(ri.KAMERA_BITIS_SINYAL, ozet["bitis"])
        self.assertEqual(1, k1.release_sayisi)
        self.assertEqual(1, k2.release_sayisi)
        bekliyor = _satirlar(cikti, "[KAMERA_BEKLIYOR]")
        self.assertEqual(1, len(bekliyor), cikti)
        self.assertIn(f"neden={ri.KAMERA_BITIS_DUSEN_KARE}", bekliyor[0])
        self.assertEqual(1, len(_satirlar(cikti, "[KAMERA_GERI_GELDI]")))
        # Dusen-kare beklemeleri de enjekte `bekle`den gecti (gercek uyku yok).
        self.assertEqual(ri.KAMERA_DUSEN_KARE_UST_SINIRI - 1,
                         saat.beklemeler.count(ri.KAMERA_DUSEN_KARE_BEKLEME_S))
        self.assertEqual(1, kayit.adlar().count("KAMERA_BEKLIYOR"))
        self.assertEqual(ri.KAMERA_BITIS_DUSEN_KARE,
                         dict(kayit.olaylar)["KAMERA_BEKLIYOR"]["neden"])

    def test_d2_acilip_kare_vermeyen_kaynak_AYNI_kesintidir(self):
        """Acilir ama hic kare vermez (dusen kare) -> geri cekilme BUYUR, tani
        satiri tekrarlanmaz, GERI_GELDI basilmaz (acilmak yetmez, kare gerekir)."""
        kameralar = [_SahteKamera(acik=True, kare=1)] + [
            _SahteKamera(acik=True, kare=0) for _ in range(4)]
        fabrika = _Fabrika(*kameralar, _SahteKamera(acik=True, kare=5))
        analiz = _analiz([_R1], 3)
        ozet, _, cikti, _ = _kos(fabrika, kamera_bekle=True, analiz=analiz)
        self.assertEqual(3, analiz.say["n"])
        self.assertEqual(1, ozet["yeniden_acma"], "kare vermeyen acilis sayildi")
        self.assertEqual(1, len(_satirlar(cikti, "[KAMERA_BEKLIYOR]")), cikti)
        geldi = _satirlar(cikti, "[KAMERA_GERI_GELDI]")
        self.assertEqual(1, len(geldi), cikti)
        self.assertIn("deneme=5", geldi[0])


# ── e) tani satiri ──────────────────────────────────────────────────────────

class TaniSatiri(_BayrakTemiz):
    def test_e1_kopru_durumu_ve_dev_video_satirda(self):
        cagrilar = []

        def getir(url, zaman_asimi):
            cagrilar.append((url, zaman_asimi))
            return dict(KOPRU_DURUM)

        satir = ri.kamera_tani_satiri(KOPRU_URL, 3, 12.34,
                                      neden=ri.KAMERA_BITIS_ACILAMADI,
                                      cihaz_listele=lambda: [], durum_getir=getir)
        self.assertNotIn("\n", satir)
        self.assertTrue(satir.startswith("[KAMERA_BEKLIYOR]"), satir)
        for parca in (f"kaynak={KOPRU_URL!r}", "deneme=3", "bekleme_s=12.3",
                      "/dev/video*: YOK", "kaynak_acik=False",
                      "son_hata='30 ardisik dusen kare (ust sinir 30)'",
                      "acma_denemesi=1304", "dusen_kare=39120", "IPUCU",
                      "serit kabloyu", "sicak takilmaz", "YENIDEN BASLATILMALI"):
            self.assertIn(parca, satir)
        self.assertEqual([("http://127.0.0.1:8080/durum", ri.KAMERA_DURUM_ZAMAN_ASIMI_S)],
                         cagrilar)

    def test_e2_hatalar_ISTISNA_YUKSELTMEZ(self):
        def kopuk(_u, _z):
            raise urllib.error.URLError(ConnectionRefusedError(111, "Connection refused"))

        def zaman_asimi(_u, _z):
            raise TimeoutError("timed out")

        def listeleme_patlar():
            raise PermissionError("erisim yok")

        for getir, beklenen in ((kopuk, "URLError"), (zaman_asimi, "TimeoutError"),
                                (lambda _u, _z: ["liste"], "TypeError"),
                                (lambda _u, _z: (_ for _ in ()).throw(ValueError("bozuk json")),
                                 "ValueError")):
            with self.subTest(beklenen=beklenen):
                satir = ri.kamera_tani_satiri(KOPRU_URL, 1, 0.0, cihaz_listele=lambda: [],
                                              durum_getir=getir)
                self.assertIn("ALINAMADI", satir)
                self.assertIn(beklenen, satir)
        satir = ri.kamera_tani_satiri(KOPRU_URL, 1, 0.0, cihaz_listele=listeleme_patlar,
                                      durum_getir=lambda _u, _z: dict(KOPRU_DURUM))
        self.assertIn("OKUNAMADI", satir)
        self.assertNotIn("IPUCU", satir, "liste okunamadi != cihaz yok")

    def test_e3_cihaz_varsa_listelenir_ipucu_yok(self):
        satir = ri.kamera_tani_satiri(KOPRU_URL, 1, 0.0,
                                      cihaz_listele=lambda: ["/dev/video0"],
                                      durum_getir=lambda _u, _z: dict(KOPRU_DURUM))
        self.assertIn("/dev/video*: /dev/video0", satir)
        self.assertNotIn("IPUCU", satir)

    def test_e4_http_olmayan_kaynakta_durum_ISTENMEZ(self):
        getir = mock.Mock(return_value=dict(KOPRU_DURUM))
        for kaynak in (0, "/dev/video0", "rtsp://10.0.0.2:8554/x", "video.mp4"):
            with self.subTest(kaynak=kaynak):
                satir = ri.kamera_tani_satiri(kaynak, 1, 0.0, cihaz_listele=lambda: [],
                                              durum_getir=getir)
                self.assertNotIn("kopru", satir)
        getir.assert_not_called()

    def test_e5_kimlik_bilgisi_durum_istegine_TASINMAZ(self):
        getir = mock.Mock(return_value=dict(KOPRU_DURUM))
        satir = ri.kamera_tani_satiri("http://ali:gizli@10.0.0.5:8080/video", 1, 0.0,
                                      cihaz_listele=lambda: [], durum_getir=getir)
        self.assertEqual("http://10.0.0.5:8080/durum", getir.call_args.args[0])
        self.assertIn("kopru http://10.0.0.5:8080/durum:", satir)

    def test_e6_dongude_tani_30_s_den_SIK_basilmaz(self):
        """Hep acilamayan kamera, sahte saat t>=64 s'de SIGTERM. Geri cekilme
        1,2,5,5,... -> denemeler t=0,1,3,8,...,63; tani yalniz t=0, 33, 63."""
        fabrika = _Fabrika(tavan=40)
        saat = _Saat(dur_t=64.0)
        kayit = _SahteKayit()
        ozet, _, cikti, durum = _kos(fabrika, kamera_bekle=True, saat=saat,
                                     kaynak=KOPRU_URL, gorev_kaydi=kayit)
        self.assertEqual(ri.KAMERA_BITIS_SINYAL, ozet["bitis"])
        satirlar = _satirlar(cikti, "[KAMERA_BEKLIYOR]")
        zamanlar = [float(re.search(r"bekleme_s=([0-9.]+)", s).group(1)) for s in satirlar]
        self.assertEqual(0.0, zamanlar[0])
        self.assertGreaterEqual(zamanlar[1], ri.KAMERA_TANI_ARALIGI_S,
                                "30 s dolmadan ikinci tani satiri basildi")
        for once, sonra in zip(zamanlar, zamanlar[1:]):
            self.assertGreaterEqual(sonra - once, ri.KAMERA_TANI_ARALIGI_S, zamanlar)
        self.assertEqual([0.0, 33.0, 63.0], zamanlar)
        # /durum GET yalniz tani basilirken (hiz sinirli), dogru URL ve zaman asimiyla.
        self.assertEqual(3, durum.call_count)
        self.assertEqual(("http://127.0.0.1:8080/durum", ri.KAMERA_DURUM_ZAMAN_ASIMI_S),
                         durum.call_args.args)
        for s in satirlar:
            self.assertIn("kaynak_acik=False", s)
            self.assertIn("/dev/video*: YOK", s)
        # Gorev kaydina kesinti basina BIR kayit (her tani satirinda degil).
        self.assertEqual(["KAMERA_BEKLIYOR", "KAMERA_BITTI"], kayit.adlar())
        self.assertEqual(15, len(fabrika.acilan), "1 ilk + 14 yeniden acma denemesi")
        self.assertEqual(max(ri.KAMERA_YENIDEN_ACMA_BEKLEMELERI_S),
                         ri.KAMERA_YENIDEN_ACMA_BEKLEMELERI_S[-1], "son deger tavan")

    def test_e7_durum_yolu_kopruyle_AYNI(self):
        import kamera_koprusu as kk
        self.assertEqual(kk.DURUM_YOLU, ri.KAMERA_KOPRU_DURUM_YOLU)


# ── f) main() kablolamasi ───────────────────────────────────────────────────

class MainKablolama(_BayrakTemiz):
    def _kamera_bekle(self, ek):
        argv = ["rpi_inference.py", "--camera", "--mavlink", "fake",
                "--mav-sysid", "1", "--fov", "60", *ek]
        saglayici = SimpleNamespace(kapat=mock.Mock(return_value=True))
        with mock.patch.object(sys, "argv", argv), \
                mock.patch.object(ri.CanliOlcekSaglayici, "baglan", return_value=saglayici), \
                mock.patch.object(ri, "load_model",
                                  return_value=(object(), Path("m.pt"), {"durum": "sahte"})), \
                mock.patch.object(ri, "run_camera") as run_camera, \
                contextlib.redirect_stdout(io.StringIO()):
            ri.main()
        run_camera.assert_called_once()
        return run_camera.call_args.kwargs["kamera_bekle"]

    def test_f_arguman_kablolamasi(self):
        self.assertIs(True, self._kamera_bekle(["--ekransiz"]))
        self.assertIs(False, self._kamera_bekle(["--ekransiz", "--kamera-bekleme-yok"]))
        self.assertIs(False, self._kamera_bekle([]))
        self.assertIs(False, self._kamera_bekle(["--kamera-bekleme-yok"]))

    def test_f2_bayrak_yardimda_var(self):
        yardim = ri._arguman_ayristirici().format_help()
        self.assertIn("--kamera-bekleme-yok", yardim)


# ── g) karar yolu: yeniden acma histerezisi atlatamaz ───────────────────────

class KararYoluDegismez(_BayrakTemiz):
    def test_g_kesintili_kosum_yayinlari_kesintisizle_BIREBIR(self):
        # 2 kare serit 1, kesinti, sonra serit 3. Tek KararYumusatici korunursa
        # serit 3 ancak K ardisik teyitle yayinlanir; yeniden acmada sifirlansa
        # kesinti sonrasi ILK kare aninda yayinlanirdi (histerezis atlatilirdi).
        kararlar = [_R1, _R1, _R3, _R3, _R3, _R3]
        _, kesintisiz, _, _ = _kos(_Fabrika(_SahteKamera(acik=True, kare=20)),
                                   kamera_bekle=False, analiz=_analiz(kararlar, 6))
        ri.durdurma_bayragini_sifirla()
        _, kesintili, cikti, _ = _kos(
            _Fabrika(_SahteKamera(acik=True, kare=2), _SahteKamera(acik=True, kare=20)),
            kamera_bekle=True, analiz=_analiz(kararlar, 6))
        self.assertEqual(1, len(_satirlar(cikti, "[KAMERA_GERI_GELDI]")), cikti)
        self.assertEqual([c[0] for c in kesintisiz], [1, 1, 3, 3], kesintisiz)
        self.assertEqual(kesintisiz, kesintili)


class Sabitler(unittest.TestCase):
    def test_sabitler_sozlesmeden_ve_makul(self):
        b = ri.KAMERA_YENIDEN_ACMA_BEKLEMELERI_S
        self.assertEqual((1.0, 2.0, 5.0), tuple(b))
        self.assertEqual(sorted(b), list(b))
        self.assertEqual(30.0, ri.KAMERA_TANI_ARALIGI_S)
        self.assertEqual(0.5, ri.KAMERA_SINYAL_YOKLAMA_S)
        self.assertEqual(1.0, ri.KAMERA_DURUM_ZAMAN_ASIMI_S)
        import karar_sozlesmesi as ks
        self.assertIs(ks.KAMERA_TANI_ARALIGI_S, ri.KAMERA_TANI_ARALIGI_S)


if __name__ == "__main__":
    unittest.main()
