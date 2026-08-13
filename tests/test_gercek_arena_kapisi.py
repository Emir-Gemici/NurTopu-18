"""T59 KAPISI: GERCEK ARENA karesini kapi bir daha ELEMEYECEK.

Kusur (REVIEW_LOG D-84): `data/arena_referans/sartname_s9_arena.png` — sartname
s.9'dan cikarilan, projenin sahip oldugu TEK gercek arena goruntusu. Uretim
modeli v24 onu DOGRU segmentliyor, ama T48/T52 kapisi reddediyordu:

    kaplama 0.579 > tavan 0.55  VE  kenar 0.585 > tavan 0.50  ->  RET

Esikler v21 ciktilariyla ve sentetik/otopark dagilimlariyla turetilmisti;
gercek arena o dagilimlarin DISINDA kaldi. D-85 karariyla kaplama tavani
0.67'ye cikarildi.

BU PAKET NEDEN VAR: esigin sayisal degeri degil, DAVRANIS kilitlenir — "dogru
segmentlenmis gercek arena kapidan GECER". Esik ileride yeniden oynatilirsa
(model degisiminde bu ZORUNLUDUR) ve gercek arenayi tekrar elerse, bu test
duser. Sessiz geri donus mumkun olmaz.

⚠ Bu paket MODEL AGIRLIGI GEREKTIRIR (v24 · ~55 MB, `.gitignore` disinda).
Agirlik ya da kare yoksa testler ATLANIR — temiz klonda yanlis sebeple kirmizi
yanmaz. Olculen degerler ayrica SABIT olarak da sinanir (agirliksiz kosar),
boylece kapinin esik mantigi her ortamda kilitli kalir.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import cv2

KOK = Path(__file__).resolve().parents[1]
if str(KOK / "codes") not in sys.path:
    sys.path.insert(0, str(KOK / "codes"))

from karar_sozlesmesi import (ZEMIN_KAPLAMA_TAVANI,  # noqa: E402
                              ZEMIN_KENAR_DAYANMA_TAVANI,
                              ZEMIN_MASKESI_SUPHELI_SEBEBI, zemin_kaplamasi,
                              zemin_kenar_dayanmasi, zemin_maskesi_reddi)
from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp,  # noqa: E402
                           _preprocess, analyze_path, get_masks)

ARENA = KOK / "data" / "arena_referans" / "sartname_s9_arena.png"
MODEL = KOK / "models" / "navitas_seg_v24_best.pt"
CONF = 0.30

# T59 · v24 ile OLCULEN degerler (bkz. REVIEW_LOG D-86). Agirliksiz ortamda da
# esik mantiginin sinanabilmesi icin sabit tutulur.
ARENA_KAPLAMA = 0.579
ARENA_KENAR = 0.585

_ATLA = not (ARENA.is_file() and MODEL.is_file())
_ATLA_SEBEBI = (f"gercek arena karesi ve/veya v24 agirligi yok "
                f"(arena={ARENA.is_file()} model={MODEL.is_file()})")


class OlculenDegerlerKapidanGecerTests(unittest.TestCase):
    """Agirliksiz kosar: OLCULEN sayilar kapiyi atesliyor mu?"""

    def test_gercek_arena_kaplamasi_TAVANIN_ALTINDA(self):
        self.assertLessEqual(
            ARENA_KAPLAMA, ZEMIN_KAPLAMA_TAVANI,
            f"gercek arena kaplamasi {ARENA_KAPLAMA} tavani "
            f"({ZEMIN_KAPLAMA_TAVANI}) asiyor — dogru segmentlenmis GERCEK "
            f"arena reddedilir (D-84 kusurunun geri donusu)")

    def test_kenar_TEK_BASINA_reddi_getirmez(self):
        """Arena kenari tavanin USTUNDE; reddi ancak kaplama ile BIRLIKTE verir."""
        self.assertGreater(
            ARENA_KENAR, ZEMIN_KENAR_DAYANMA_TAVANI,
            "olcum bayat: arena kenari artik tavanin ustunde degil")
        self.assertLessEqual(
            ARENA_KAPLAMA, ZEMIN_KAPLAMA_TAVANI,
            "kapi AND birlesimidir; kaplama da asilirsa arena ELENIR")

    def test_ESKI_esik_bu_kareyi_ELIYORDU(self):
        """Regresyonun neye karsi oldugu testte GORUNUR olsun."""
        eski_kaplama_tavani = 0.55
        self.assertGreater(ARENA_KAPLAMA, eski_kaplama_tavani)
        self.assertGreater(ARENA_KENAR, ZEMIN_KENAR_DAYANMA_TAVANI)


@unittest.skipIf(_ATLA, _ATLA_SEBEBI)
class GercekArenaUretimZinciriTests(unittest.TestCase):
    """URETIM zinciriyle gercek kareyi kosar — sabitler bayatlarsa yakalanir."""

    @classmethod
    def setUpClass(cls):
        from ultralytics import YOLO
        img = cv2.imread(str(ARENA))
        if img is None:
            raise unittest.SkipTest(f"arena karesi okunamadi: {ARENA}")
        model = YOLO(str(MODEL), task="segment")
        sq, small, icerik = _preprocess(img)
        h, w = sq.shape[:2]
        sonuc = model.predict(small, imgsz=INFER_SIZE, conf=CONF, verbose=False)
        cls.maskeler = _maskeleri_icerige_kirp(get_masks(sonuc, h, w), icerik)
        cls.icerik = icerik
        cls.kaplama = zemin_kaplamasi(cls.maskeler[0], icerik)
        cls.kenar = zemin_kenar_dayanmasi(cls.maskeler[0], icerik)

    def test_model_gercek_arenada_KOR_DEGIL(self):
        """v21 burada tek piksel zemin bulamiyordu (D-84)."""
        self.assertGreater(
            self.kaplama, 0.0,
            "uretim modeli gercek arenada zemin BULAMIYOR — D-84'teki v21 "
            "korlugunun geri donusu")

    def test_OLCULEN_degerler_SABITLERLE_tutarli(self):
        self.assertAlmostEqual(ARENA_KAPLAMA, self.kaplama, places=2,
                               msg="testteki sabit kaplama BAYAT")
        self.assertAlmostEqual(ARENA_KENAR, self.kenar, places=2,
                               msg="testteki sabit kenar BAYAT")

    def test_kapi_GERCEK_ARENADA_ATESLEMEZ(self):
        """Bu paketin asil iddiasi."""
        ret = zemin_maskesi_reddi(self.maskeler[0], self.icerik)
        self.assertIsNone(
            ret,
            f"kapi GERCEK ARENAYI eledi (kaplama {self.kaplama:.3f} · "
            f"kenar {self.kenar:.3f}) — D-84 kusuru geri geldi")

    def test_karar_yolu_ZEMIN_MASKESI_SUPHELI_dondurmez(self):
        """Kapi `analyze_path` icinden de susmali."""
        _yol, _guven, _wp, ret = analyze_path(
            self.maskeler[0], icerik=self.icerik,
            engel_mask=self.maskeler.get(1), return_reason=True)
        sebep = ret[0] if ret else None
        self.assertNotEqual(
            ZEMIN_MASKESI_SUPHELI_SEBEBI, sebep,
            "karar yolu gercek arenayi zemin kapisiyla reddetti")


if __name__ == "__main__":
    unittest.main(verbosity=2)
