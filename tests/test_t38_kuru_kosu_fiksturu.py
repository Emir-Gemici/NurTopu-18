"""T38 KAPISI (ON_KAYIT SS24 · REVIEW_LOG D-301): kuru kosu halka 7'yi MESRU
sinayabilecegi bir kareyle kosuyor mu?

KUSUR (kuyruk T38 / D-53): kuru kosu varsayilan kareyi `data/raw_frames`ten
aliyordu — bir OTOPARK cekimi. Sahnede alt<->ust koridor yok, dolayisiyla halka
7 orada MESRU sekilde GECEMEZ. Ustelik olcek, kareyle ILGISIZ sahte telemetriden
turetiliyordu: ayni kabul kumesi kareleri o mpp ile 6/12, KENDI olcegiyle 12/12
(results/t38/).

Cozum: depo ICINDE `data/kuru_kosu_fikstur` — kabul dagilimindan kare + O
KARENIN olcegi; yayinlanan sahte irtifa da o olcekten URETIM fonksiyonuyla
turetilir (`mpp_irtifadan`), yani telemetri yolu hâlâ sinanir.

BOS KAPI YASAGI (TEST_SPECS SS4.1) — kapi IKI YONLU + mutasyonlu:
  1. fikstur kareyle halka 7 GECER,
  2. otopark karesi acikca verilince halka 7 hâlâ DUSER (ayirt ediyor),
  3. fiksturun kare<->olcek tutarliligi bozulursa fikstur REDDEDILIR (fail-closed),
  4. olcek kucultulunce (govde acikligi piksel cinsinden buyur) rota DUSER —
     yani halka olcege GERCEKTEN duyarli.
"""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

import numpy as np

KOK = Path(__file__).resolve().parents[1]
for _y in (KOK / "scripts", KOK / "codes", KOK / "comms"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

import saha_kuru_kosu as sk                       # noqa: E402
from karar_sozlesmesi import mpp_irtifadan        # noqa: E402

FIKSTUR = KOK / "data" / "kuru_kosu_fikstur"


class FiksturSozlesmesi(unittest.TestCase):

    def setUp(self):
        mf = FIKSTUR / "manifest.json"
        if not mf.is_file():
            self.skipTest("fikstur yok")
        self.veri = json.loads(mf.read_text(encoding="utf-8"))

    def test_kareler_ve_sha_tutuyor(self):
        self.assertTrue(self.veri["kareler"], "fikstur bos")
        for k in self.veri["kareler"]:
            yol = FIKSTUR / k["dosya"]
            with self.subTest(kare=k["dosya"]):
                self.assertTrue(yol.is_file(), yol)
                self.assertEqual(k["sha256"],
                                 hashlib.sha256(yol.read_bytes()).hexdigest(),
                                 "fikstur karesi degismis")

    def test_irtifa_URETIM_fonksiyonuyla_mpp_yi_veriyor(self):
        fov = float(self.veri["yatay_fov_derece"])
        for k in self.veri["kareler"]:
            with self.subTest(kare=k["dosya"]):
                olculen = mpp_irtifadan(float(k["irtifa_m"]),
                                        int(k["genislik_px"]),
                                        yatay_fov_derece=fov)
                self.assertIsNotNone(olculen)
                self.assertAlmostEqual(float(k["mpp"]), olculen, places=9)

    def test_okuyucu_dortlu_donuyor(self):
        fk = sk.kuru_kosu_fiksturu()
        self.assertIsNotNone(fk, "fikstur okunamadi")
        yol, mpp, irtifa, fov = fk
        self.assertTrue(Path(yol).is_file())
        self.assertGreater(mpp, 0)
        self.assertGreater(irtifa, 0)
        self.assertGreater(fov, 0)


class FiksturFailClosed(unittest.TestCase):
    """MUTASYON 3: kare<->olcek tutarliligi bozulursa fikstur KULLANILMAZ."""

    def _sahte_fikstur(self, degistir):
        kok = Path(tempfile.mkdtemp()) / "fx"
        (kok / "images").mkdir(parents=True)
        (kok / "images" / "a.jpg").write_bytes(b"x")
        veri = {"yatay_fov_derece": 60.0,
                "kareler": [{"dosya": "images/a.jpg", "sha256": "0" * 64,
                             "genislik_px": 640, "yukseklik_px": 640,
                             "mpp": 0.078125, "irtifa_m": 43.30127}]}
        degistir(veri)
        (kok / "manifest.json").write_text(json.dumps(veri), encoding="utf-8")
        return kok

    def test_saglam_fikstur_kabul(self):
        kok = self._sahte_fikstur(lambda v: None)
        with unittest.mock.patch.object(sk, "FIKSTUR_DIZINI", kok):
            self.assertIsNotNone(sk.kuru_kosu_fiksturu())

    def test_irtifa_bozulursa_RED(self):
        kok = self._sahte_fikstur(
            lambda v: v["kareler"][0].__setitem__("irtifa_m", 43.30127 * 3))
        with unittest.mock.patch.object(sk, "FIKSTUR_DIZINI", kok):
            self.assertIsNone(sk.kuru_kosu_fiksturu(),
                              "tutarsiz irtifa/mpp fikstur KABUL EDILDI")

    def test_mpp_bozulursa_RED(self):
        kok = self._sahte_fikstur(
            lambda v: v["kareler"][0].__setitem__("mpp", 0.078125 / 3))
        with unittest.mock.patch.object(sk, "FIKSTUR_DIZINI", kok):
            self.assertIsNone(sk.kuru_kosu_fiksturu())

    def test_gorsel_yoksa_RED(self):
        kok = self._sahte_fikstur(
            lambda v: v["kareler"][0].__setitem__("dosya", "images/yok.jpg"))
        with unittest.mock.patch.object(sk, "FIKSTUR_DIZINI", kok):
            self.assertIsNone(sk.kuru_kosu_fiksturu())

    def test_manifest_yoksa_RED(self):
        with tempfile.TemporaryDirectory() as td:
            with unittest.mock.patch.object(sk, "FIKSTUR_DIZINI", Path(td)):
                self.assertIsNone(sk.kuru_kosu_fiksturu())


class HalkaOlcegeDuyarli(unittest.TestCase):
    """MUTASYON 4: olcek kucultulunce (govde acikligi px olarak buyur) DUSER."""

    @staticmethod
    def _koridor(genislik_px):
        trav = np.zeros((256, 256), np.uint8)
        orta = 128
        trav[:, orta - genislik_px // 2: orta + genislik_px // 2] = 1
        return {0: trav, 1: np.zeros((256, 256), np.uint8)}

    def test_dogru_olcekte_GECER_kucuk_olcekte_DUSER(self):
        icerik = (0, 0, 256, 256)
        d1, _ = sk.halka_rota(sk.Rapor(), self._koridor(40), icerik, sk.GECTI,
                              mpp=0.078125)
        d2, _ = sk.halka_rota(sk.Rapor(), self._koridor(40), icerik, sk.GECTI,
                              mpp=0.078125 / 6)
        self.assertEqual(sk.GECTI, d1, "dogru olcekte rota uretilemedi")
        self.assertEqual(sk.DUSTU, d2,
                         "olcek 6 kat kuculdugu hâlde halka GECTI — "
                         "halka olcege duyarsiz, kapi bos")


class VarsayilanKare(unittest.TestCase):
    """Halka 1 varsayilan olarak FIKSTURU kullanmali ve bunu RAPORA yazmali."""

    def test_varsayilan_fiksturden_gelir(self):
        if not (FIKSTUR / "manifest.json").is_file():
            self.skipTest("fikstur yok")
        rapor = sk.Rapor()
        durum, kare = sk.halka_kamera(rapor, None)
        satir = next(s for s in rapor.satirlar if s["halka"] == "kamera")
        self.assertEqual(sk.GECTI, durum)
        self.assertIsNotNone(kare)
        self.assertTrue(satir["detay"]["fikstur_kullanildi"],
                        "varsayilan kare hâlâ data/raw_frames'ten geliyor (T38)")
        self.assertIn("kuru_kosu_fikstur", satir["detay"]["kare"])

    def test_acik_kare_fiksturu_EZER(self):
        otopark = next((p for p in (KOK / "data" / "raw_frames").rglob("*.jpg")), None)
        if otopark is None:
            self.skipTest("raw_frames bos")
        rapor = sk.Rapor()
        sk.halka_kamera(rapor, otopark)
        satir = next(s for s in rapor.satirlar if s["halka"] == "kamera")
        self.assertFalse(satir["detay"]["fikstur_kullanildi"])


if __name__ == "__main__":
    unittest.main()
