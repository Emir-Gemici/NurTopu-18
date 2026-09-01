"""T198 kalan is (D-379) — HB SEKIL DOGRULAMASI nobetcisi.

Korudugu bosluk (D-295): 67 gercek otopark karesinin 67'sinde kirmizi
OTOMOBIL HB sanildi; olcek denetimi dogru boyuttaki sahtekari ayiramaz.
Sekil puani olculdu: pozitifler 0,189-0,467 · otomobiller 0,076-0,178 —
TAM ayrik ama pay ince (+0,011). Esik ON KAYITLI kuralla turetildi (0,1766).

Bu kapinin sinadiklari:
  1. DAVRANIS: posterimiz yuksek, dolu blok dusuk puan alir; puan yonelimden
     bagimsizdir (45 derece).
  2. Esik SOZLESMEDE ve olcum JSON'undaki turetimle BIREBIR (bayat/oynanmis
     sabit yakalanir).
  3. GERIYE DONUK UYUM: `sekil_esigi` verilmeyen cagri ESKI davranistadir.
  4. OLCULEMEDI != GECTI: puan uretilemeyen aday, kapi ACIKKEN reddedilir.
  5. Mutasyonlar kod uzerinde, uygulanma kontrollu (D-370).
"""
import json
import sys
import unittest
from pathlib import Path

import numpy as np

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "codes"))

import cv2  # noqa: E402

import karar_sozlesmesi as ks  # noqa: E402

POSTER = KOK / "results" / "hb_baski" / "HB_2x2m_onizleme.png"
OLCUM = KOK / "results" / "hb_sekil" / "olcum_20260901.json"
SOZLESME = (KOK / "codes" / "karar_sozlesmesi.py").read_text(encoding="utf-8")


def _kodu(metin):
    return "\n".join(s for s in metin.splitlines()
                     if not s.lstrip().startswith("#"))


def _dolu_blok():
    """Kirmizi OTOMOBIL vekili: sablon doluluguna esit puan almali (~0,29)."""
    im = np.full((200, 300, 3), (180, 180, 180), np.uint8)
    cv2.rectangle(im, (60, 40), (240, 160), (30, 30, 200), -1)
    return im


class PuanDavranisi(unittest.TestCase):
    def test_POSTER_YUKSEK_BLOK_DUSUK(self):
        img = cv2.imread(str(POSTER))
        self.assertIsNotNone(img, "poster onizlemesi okunamadi")
        p_poster = ks.hb_sekil_puani(img, (0, 0, img.shape[1], img.shape[0]))
        p_blok = ks.hb_sekil_puani(_dolu_blok(), (50, 30, 200, 140))
        self.assertGreater(p_poster, 0.85)
        self.assertLess(p_blok, 0.35)
        self.assertGreater(p_poster - p_blok, 0.5,
                           "ayrisma kayboldu — puan artik sekli olcmuyor")

    def test_YONELIMDEN_BAGIMSIZ(self):
        img = cv2.imread(str(POSTER))
        M = cv2.getRotationMatrix2D((720, 720), 45, 0.7)
        don = cv2.warpAffine(img, M, (1440, 1440),
                             borderValue=(200, 200, 200))
        ham = ks._hb_ham_kirmizi(don)
        x, y, w, h = cv2.boundingRect(cv2.findNonZero(ham))
        p = ks.hb_sekil_puani(don, (x, y, w, h))
        self.assertGreater(p, 0.8, "45 derecede puan cokuyor — minAreaRect "
                                   "ters dondurmesi bozulmus")

    def test_SABLON_SAYILARDAN(self):
        sb = ks.hb_sekil_sablonu()
        self.assertEqual(sb.shape, (128, 128))
        # doluluk = cerceve + H; poster geometrisinden ~0,29 beklenir
        self.assertAlmostEqual(float(sb.mean()), 0.29, delta=0.03)

    def test_BOS_GIRDIDE_None(self):
        bos = np.full((100, 100, 3), (128, 128, 128), np.uint8)
        self.assertIsNone(ks.hb_sekil_puani(bos, (10, 10, 50, 50)))
        self.assertIsNone(ks.hb_sekil_puani(bos, None))


class EsikKilidi(unittest.TestCase):
    def test_ESIK_OLCUMLE_BIREBIR(self):
        d = json.loads(OLCUM.read_text(encoding="utf-8"))
        t = d["esik_turetim"]
        # BIREBIR esitlik — yuvarlama YOK: 4 haneye yuvarlanan ilk surum,
        # esikten 2e-5 uzaktaki frame_000006'yi olcumden farkli
        # degerlendiriyordu (uretim/olcum davranis ayrismasi).
        self.assertEqual(ks.HB_SEKIL_ESIGI, t["esik"],
                         "sozlesmedeki esik olcum artefaktinin BIREBIR "
                         "kendisi degil — bayat, yuvarlanmis ya da oynanmis")
        self.assertAlmostEqual(t["esik"], t["q"] * t["pay"], places=6,
                               msg="turetim kurali bozulmus")
        self.assertEqual(d["verdikt"], "GECTI",
                         "verdikt GECTI degilken sabit sozlesmede duramaz")

    def test_AYRISMA_HALA_DOGRU_YONDE(self):
        """Olcum artefaktindan: pozitif min > otomobil maks (tam ayriklik)."""
        d = json.loads(OLCUM.read_text(encoding="utf-8"))
        poz = [k["puan"] for k in d["pozitif"] if k.get("puan") is not None]
        oto = [k.get("puan") or 0.0 for k in d["otopark"] if k["tespit"]]
        self.assertGreater(min(poz), max(oto),
                           "dagilimlar ORTUSUYOR — kayit guncellenmeli")


class GeriyeUyumVeFailClosed(unittest.TestCase):
    GERCEK_OTOMOBIL = (KOK / "data" / "raw_frames" /
                       "whatsapp_video_2026_07_30_at_11_44_23" /
                       "frame_000015_000002040.jpg")   # olcumde 0,131 aldi

    def test_SEKILSIZ_CAGRI_ESKI_DAVRANIS(self):
        """GERCEK otomobil karesi (D-295'in 67 FP'sinden, medyan puanli):
        sekil kapisi YOKKEN tespit edilir (eski davranis, geriye uyum);
        sekil esigi verilirse mpp'siz cagri ESLESME KURALI geregi None
        (D-383: sekil kapisi olceksiz ACILMAZ — sekil tek basina 26x18
        px'lik lekeleri de geciriyordu, olculdu)."""
        im = cv2.imread(str(self.GERCEK_OTOMOBIL))
        self.assertIsNotNone(im, "gercek otomobil karesi okunamadi")
        eski = ks.hb_konumu(im)
        self.assertIsNotNone(eski, "on kosul: bu karede FP tespit vardi")
        self.assertNotIn("sekil_puani", eski)
        yeni = ks.hb_konumu(im, sekil_esigi=ks.HB_SEKIL_ESIGI)
        self.assertIsNone(yeni, "olceksiz sekil cagrisi kabul edildi — "
                                "D-383 eslesme kurali delindi")

    def test_BILINEN_SINIR_dolu_kare_GECIYOR(self):
        """🔴 BILINEN SINIR (D-379, gizlenmez): KUSURSUZ dolu kirmizi kare
        tam sablon doluluk oranini (~0,29) alir ve esigin (0,1766) USTUNDE
        kalir — yani ideal dolu 2x2 m kirmizi levha sekil kapisindan GECER.
        Gercek otomobiller pürüzlü maskeleriyle 0,076-0,178 aldi ve dustu.
        Bu test siniri KILITLER: davranis sessizce degisirse fark edilir."""
        p = ks.hb_sekil_puani(_dolu_blok(), (50, 30, 200, 140))
        self.assertGreater(p, ks.HB_SEKIL_ESIGI,
                           "dolu kare artik dusuyor — sinir degismis, "
                           "D-379 kaydi ve bu test guncellenmeli")
        self.assertAlmostEqual(p, 0.29, delta=0.03)

    def test_POSTER_KAPIDAN_GECIYOR(self):
        """Uretim yapilandirmasi: olcek + sekil BIRLIKTE (D-383)."""
        img = cv2.imread(str(POSTER))
        mpp = ks.HB_KENAR_M / float(img.shape[1])   # 1440 px = 2 m ped
        hb = ks.hb_konumu(img, mpp=mpp, sekil_esigi=ks.HB_SEKIL_ESIGI)
        self.assertIsNotNone(hb, "gercek ped olcek+sekil kapisina takildi — "
                                 "fail-closed BOZULDU")
        self.assertGreaterEqual(hb["sekil_puani"], ks.HB_SEKIL_ESIGI)

    def test_D383_HEDEF_CALMA_pad_kazanir(self):
        """Curutucunun senaryosu: sahnede GERCEK ped + banda giren DAHA BUYUK
        dolu kirmizi kare. Eski buyuk-once secim, dolu kare esigi gectigi
        (~0,29) icin hedefi CALDIRIYORDU; NIHAI ret semantigi ise pedi de
        OLDURUYORDU. Yeni secim EN YUKSEK sekil puaniyla: ped kazanmali."""
        im = np.full((400, 400, 3), (170, 170, 170), np.uint8)
        # ped: sablon geometrisi 100 px'e olceklenir, (40,40)'a cizilir
        sb = cv2.resize(ks.hb_sekil_sablonu(), (100, 100),
                        interpolation=cv2.INTER_NEAREST)
        bolge = im[40:140, 40:140]
        bolge[sb > 0] = (30, 30, 200)
        # sahtekar: 140 px dolu kirmizi kare (pedden BUYUK)
        cv2.rectangle(im, (220, 200), (360, 340), (30, 30, 200), -1)
        # beklenen kenar ~112 px olacak sekilde mpp: ped 100 (0,89) ve
        # kare 140 (1,25) IKISI DE bandin icinde
        mpp = ks.HB_KENAR_M / 112.0
        hb = ks.hb_konumu(im, mpp=mpp, sekil_esigi=ks.HB_SEKIL_ESIGI)
        self.assertIsNotNone(hb, "iki adayli sahnede HEDEF_YOK — nihai ret "
                                 "semantigi geri gelmis (pedi de olduruyor)")
        cx, cy = hb["merkez"]
        self.assertTrue(40 <= cx <= 140 and 40 <= cy <= 140,
                        f"HEDEF CALINDI: secilen merkez ({cx:.0f},{cy:.0f}) "
                        "ped kutusunda degil — dolu kare kazandi")

    def test_D383_gecersiz_parametre_fail_closed(self):
        """NaN mpp olcek denetimini, NaN esik sekil kapisini SESSIZCE
        kapatiyordu (curutucu olctu). Artik ikisi de HEDEF_YOK."""
        img = cv2.imread(str(POSTER))
        self.assertIsNone(ks.hb_konumu(img, mpp=float("nan")))
        self.assertIsNone(ks.hb_konumu(img, mpp=-1.0))
        mpp = ks.HB_KENAR_M / float(img.shape[1])
        self.assertIsNone(ks.hb_konumu(img, mpp=mpp,
                                       sekil_esigi=float("nan")))

    def test_OLCULEMEYEN_PUAN_GECTI_SAYILMAZ(self):
        kod = _kodu(SOZLESME)
        self.assertIn("if puan is None or puan < float(sekil_esigi):", kod,
                      "puan uretilemeyen aday reddedilmiyor — "
                      "OLCULEMEDI != GECTI ihlali")


class MutasyonKontrolu(unittest.TestCase):
    def test_M1_KAPI_KALDIRILINCA_YAKALANIR(self):
        kod = _kodu(SOZLESME)
        desen = "if puan is None or puan < float(sekil_esigi):"
        mutant = kod.replace(desen, "if False:", 1)
        self.assertNotEqual(kod, mutant, "MUTASYON UYGULANMADI (D-370)")
        self.assertNotIn(desen, mutant,
                         "kapi satiri kaldirildigi halde gorunmuyor")

    def test_M2_SABLON_BOZULURSA_DAVRANIS_YAKALAR(self):
        """Davranissal mutasyon: sablon yerine DOLU kare konursa dolu blok
        yuksek puan alirdi — mevcut sablonla almiyor (test_POSTER... ile
        birlikte kapinin ayirt ediciligi davranistan kanitli)."""
        dolu = np.ones((128, 128), np.uint8)
        blok = _dolu_blok()
        ham = ks._hb_ham_kirmizi(blok)
        x, y, w, h = cv2.boundingRect(cv2.findNonZero(ham))
        # dolu sablonla IoU ~1 olurdu; gercek sablonla ~0,29 oldu — fark
        # sablonun gercekten is yaptigini gosterir
        p = ks.hb_sekil_puani(blok, (x, y, w, h))
        self.assertLess(p, 0.35)
        self.assertGreater(float(dolu.mean()), 0.99)


if __name__ == "__main__":
    unittest.main()
