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

⚠ Bu paket MODEL AGIRLIGI GEREKTIRIR. Hangi agirlik oldugu BURADA YAZILMAZ:
`config/model_registry.json` etkin profilinden okunur (madde 16; 2026-08-26
itibariyla v35 · ~55 MB, `.gitignore` disinda). D-266'ya kadar `MODEL` v24'e
CIVILIYDI — uretim v35'e gectikten sonra bile kapi eski modeli kosuyor, uretim
modeli ne kadar bozulursa bozulsun DUSEMIYORDU ("yapisal olarak dusemeyen bos
yesil"). Artik uretim modeli degisince bu kapi YENI modeli kosar.
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
from model_registry import load_registry  # noqa: E402
from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp,  # noqa: E402
                           _preprocess, analyze_path, get_masks)

ARENA = KOK / "data" / "arena_referans" / "sartname_s9_arena.png"
KAYIT_DEFTERI = KOK / "config" / "model_registry.json"
CONF = 0.30


def _kayittan_uretim_modeli():
    """Etkin profilin agirlik yolu ve kimligi — CIPLAK surum adi YAZILMAZ.

    Defter okunamazsa istisna FIRLATIR (fail-closed): defter repoda tutulur,
    yoklugu "agirlik yok" gibi ATLANACAK bir durum degil, KUSURDUR.
    """
    veri = load_registry(KAYIT_DEFTERI)
    profil = veri["profiles"][veri["default_profile"]]
    return KOK / profil["path"], str(profil.get("model_id", "?"))


MODEL, MODEL_KIMLIGI = _kayittan_uretim_modeli()

# 🔴 SABITLER URETIM MODELINE AITTIR, v24'e DEGIL (mimar vekili, 2026-08-26, D-283).
# Eski cift (0.579, 0.585) v24 ile olculmustu ve 12 gun boyunca test v24'e civili
# kaldigi icin "bayat sabit" hicbir zaman ateslemedi. MODEL defterden okunur hale
# gelince (T59 onarimi, D-266) sabit ILK KEZ gercek modelle karsilastirildi ve
# 0.579 != 0.1508 cikti. Fark bir gerileme DEGIL: v24'un 0.579'u COKMUS bir
# maskeydi (arena disini, moloz kenarlarini ve H pedini zemin sayiyordu —
# results/t133/arena_v24_v35_bindirme.jpg); v35 yalniz orta koridoru zemin
# sayiyor. D-62'nin dersi: yuksek kaplama "cok gorme" DEGIL, cokme olabilir.
# ⚠ Bu sabitler YENIDEN v35'e civilenmis oluyor. Model degisince test yine
#   "bayat sabit" diye DUSECEK — bu bilincli: kapinin isi tam da budur.
ARENA_KAPLAMA = 0.1508
ARENA_KENAR = 0.0000

_ATLA = not (ARENA.is_file() and MODEL.is_file())
_ATLA_SEBEBI = (f"gercek arena karesi ve/veya uretim agirligi ({MODEL_KIMLIGI}: "
                f"{MODEL.name}) yok (arena={ARENA.is_file()} "
                f"model={MODEL.is_file()})")


class OlculenDegerlerKapidanGecerTests(unittest.TestCase):
    """Agirliksiz kosar: OLCULEN sayilar kapiyi atesliyor mu?"""

    def test_MODEL_kayit_defterinden_geliyor_CIVILI_DEGIL(self):
        """D-266 kilidi: `MODEL` satiri bir daha surum adina CIVILENEMEZ.

        Civili kalsaydi uretim modeli degisince bu kapi ESKI modeli kosar,
        uretim ne kadar bozulursa bozulsun dusemezdi.
        """
        kaynak = Path(__file__).read_text(encoding="utf-8")
        self.assertNotRegex(
            kaynak, r'(?m)^MODEL\s*=.*\.pt',
            "`MODEL` dogrudan bir `.pt` adina baglanmis — defterden okunmali")
        # Desen kendi metniyle ESLESMEZ (`\d+` harfleri rakam degildir).
        self.assertNotRegex(kaynak, r'navitas_seg_v\d+_best\.pt',
                            "bir surum agirligi koda civilenmis (D-266)")
        veri = load_registry(KAYIT_DEFTERI)
        beklenen = KOK / veri["profiles"][veri["default_profile"]]["path"]
        self.assertEqual(beklenen, MODEL)

    def test_gercek_arena_kaplamasi_TAVANIN_ALTINDA(self):
        self.assertLessEqual(
            ARENA_KAPLAMA, ZEMIN_KAPLAMA_TAVANI,
            f"gercek arena kaplamasi {ARENA_KAPLAMA} tavani "
            f"({ZEMIN_KAPLAMA_TAVANI}) asiyor — dogru segmentlenmis GERCEK "
            f"arena reddedilir (D-84 kusurunun geri donusu)")

    def test_kenar_TEK_BASINA_reddi_getirmez(self):
        """Arena kenari tavanin USTUNDE; reddi ancak kaplama ile BIRLIKTE verir."""
        if ARENA_KENAR <= ZEMIN_KENAR_DAYANMA_TAVANI:
            self.skipTest("v24-donemi kilidi: uretim modelinde kenar dayanma "
                          f"{ARENA_KENAR} tavanin ALTINDA — AND birlesimi bu "
                          "modelde sinanamiyor (D-283)")
        self.assertGreater(
            ARENA_KENAR, ZEMIN_KENAR_DAYANMA_TAVANI,
            "olcum bayat: arena kenari artik tavanin ustunde degil")
        self.assertLessEqual(
            ARENA_KAPLAMA, ZEMIN_KAPLAMA_TAVANI,
            "kapi AND birlesimidir; kaplama da asilirsa arena ELENIR")

    def test_ESKI_esik_bu_kareyi_ELIYORDU(self):
        """Regresyonun neye karsi oldugu testte GORUNUR olsun."""
        eski_kaplama_tavani = 0.55
        if ARENA_KAPLAMA <= eski_kaplama_tavani:
            self.skipTest("v24-donemi regresyon kilidi: uretim modelinin kaplamasi "
                          f"{ARENA_KAPLAMA} ESKI tavani (0.55) bile ASMIYOR. 0.67 "
                          "tavaninin bu kare icin GEREKCESI KALMADI (D-283, T142)")
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
