"""T186 KAPISI (ON_KAYIT 2026-08-28 · REVIEW_LOG D-324 §5/§10):
egitim recetesi SESSIZCE EKSILEMEZ.

OLCULEN KUSUR:
  `config/model_registry.json` v36 icin "recete t127 birebir" diyor.
  DEGILDIR. `scripts/olcum/139_gece_egitim.py`'nin `recete` sozlugu su
  alanlari HIC gecirmiyor ve hepsi ultralytics varsayilanina dusuyor:

      alan          t127      v36'da fiilen
      degrees       15,0      0,0
      flipud        0,5       0,0
      copy_paste    0,3       0,0
      cos_lr        true      false
      close_mosaic  20        10
      optimizer     AdamW     auto

  Sonuncusu en sinsisi: `optimizer='auto'` kalinca ultralytics, betigin
  OZELLIKLE duzeltmek icin yazildigi `lr0=0,001`'i YOK SAYDI (etkin
  0,001667; `results/gece_20260826/egitim_v7a.log` icinde acikca yazili).
  Yani duzeltmenin kendisi sessizce iptal oldu.

  `degrees=0` ve `flipud=0` ise ASIL kusurun kok nedenidir: nadir (dik
  bakan) hava goruntusunde IHA'nin yonelimi KEYFIDIR, ama model hic
  dondurulmus kare gormedi ve bariyeri 60/120/135 derecede %0,0 goruyor.

BU KAPI NE YAPAR: yeni egitim betiginin (`152_bariyer_aci_egitimi.py`)
recetesinin TAM oldugunu ve dondurme artiriminin ACIKCA verildigini
kilitler. Bir alan silinirse kapi DUSER.
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
BETIK = KOK / "scripts" / "olcum" / "152_bariyer_aci_egitimi.py"
T127 = KOK / "codes" / "runs" / "segment" / "t127_temiz" / "args.yaml"


def _yukle():
    yol = str(KOK / "scripts" / "olcum")
    if yol not in sys.path:
        sys.path.insert(0, yol)
    spec = importlib.util.spec_from_file_location("t152_egitim", BETIK)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class BetikVar(unittest.TestCase):

    def test_betik_yuklenebiliyor(self):
        self.assertTrue(BETIK.is_file(), f"egitim betigi yok: {BETIK}")
        self.assertIsNotNone(_yukle())


class RecetetamlikKapisi(unittest.TestCase):
    """`_recete_tam_mi` GERCEKTEN ayirt ediyor mu (bos kapi yasagi)."""

    @classmethod
    def setUpClass(cls):
        cls.m = _yukle()

    def test_eksik_alan_EGITIMI_DURDURUR(self):
        with self.assertRaises(SystemExit) as k:
            self.m._recete_tam_mi({"data": "x"})
        self.assertIn("RECETE EKSIK", str(k.exception))

    def test_TAM_recete_kabul_edilir(self):
        tam = {a: 0 for a in self.m.ZORUNLU_ALANLAR}
        self.m._recete_tam_mi(tam)          # patlamamali

    def test_MUTASYON_v36_nin_dusurdugu_alanlar_ZORUNLU_listede(self):
        """v36 tam bu alti alani kaybetti. Biri listeden cikarsa ayni
        kusur sessizce geri gelebilir."""
        for alan in ("degrees", "flipud", "copy_paste", "cos_lr",
                     "close_mosaic", "optimizer"):
            with self.subTest(alan=alan):
                self.assertIn(alan, self.m.ZORUNLU_ALANLAR,
                              f"`{alan}` zorunlu listede degil — v36'daki "
                              f"sessiz dusme tekrar edebilir")

    def test_MUTASYON_eksik_alan_TEK_BASINA_yakalanir(self):
        """Her zorunlu alan icin: yalniz o alan eksikse kapi DUSMELI."""
        for alan in ("degrees", "flipud", "optimizer", "lr0"):
            with self.subTest(alan=alan):
                tam = {a: 0 for a in self.m.ZORUNLU_ALANLAR if a != alan}
                with self.assertRaises(SystemExit) as k:
                    self.m._recete_tam_mi(tam)
                self.assertIn(alan, str(k.exception))


class DondurmeArtirimiACIK(unittest.TestCase):
    """Kok nedenin duzeltildigi KAYNAKTAN dogrulanir."""

    KAYNAK = BETIK.read_text(encoding="utf-8")

    def test_degrees_180_verilmis(self):
        self.assertIn("degrees=180.0", self.KAYNAK,
                      "dondurme artirimi verilmemis — v36'nin kusuru surer")

    def test_flipud_ve_optimizer_referanstan(self):
        self.assertIn('flipud=ref["flipud"]', self.KAYNAK)
        self.assertIn('optimizer=ref["optimizer"]', self.KAYNAK)

    def test_optimizer_AUTO_birakilmamis(self):
        """'auto' kalirsa ultralytics lr0'i SESSIZCE ezer (v36'da oldu)."""
        self.assertNotIn('optimizer="auto"', self.KAYNAK)
        self.assertNotIn("optimizer='auto'", self.KAYNAK)

    def test_referans_recete_gercekten_AdamW(self):
        """Kontrol: t127 args'i okunuyor ve orada optimizer AdamW."""
        if not T127.is_file():
            self.skipTest("t127 args.yaml yok")
        import yaml
        with open(T127, encoding="utf-8") as fh:
            ref = yaml.safe_load(fh)
        self.assertEqual("AdamW", ref["optimizer"])
        self.assertEqual(0.001, ref["lr0"])
        self.assertEqual(15.0, ref["degrees"],
                         "t127'nin degrees'i degismis — kayit bayatliyor")

    def test_v36_gercekten_degrees_SIFIR_ile_kosmus(self):
        """Kusurun KENDISI kayitta duruyor mu (kor duzeltme yok)."""
        v36 = KOK / "codes" / "runs" / "segment" / "gece_v7a_v35taban" / "args.yaml"
        if not v36.is_file():
            self.skipTest("v36 args.yaml yok")
        import yaml
        with open(v36, encoding="utf-8") as fh:
            a = yaml.safe_load(fh)
        self.assertEqual(0.0, a["degrees"],
                         "v36 degrees=0 degil — D-324 §4'un olcumu bayat")
        self.assertEqual(0.0, a["flipud"])


class CokmeDayanikliligi(unittest.TestCase):
    """5 haftada 8 BSOD; ultralytics checkpoint'i ATOMIK OLMAYAN
    `write_bytes` ile yaziyor. Yedek atomik olmali."""

    KAYNAK = BETIK.read_text(encoding="utf-8")

    def test_save_period_verilmis(self):
        self.assertIn("save_period=5", self.KAYNAK)

    def test_yedek_ATOMIK_yaziliyor(self):
        self.assertIn("os.replace(gecici, hedef)", self.KAYNAK,
                      "yedek atomik degil — cokme aninda yarim dosya kalir")

    def test_yedek_DONUSUMLU_iki_kopya(self):
        self.assertIn("last_{ep % 2}.pt", self.KAYNAK,
                      "tek yedek varsa yazilirken cokme onu da goturur")

    def test_yedekleme_EGITIMI_DURDURMAZ(self):
        self.assertIn("[YEDEK UYARI]", self.KAYNAK,
                      "yedek hatasi egitimi dusurebilir")

    def test_devam_yolu_var(self):
        self.assertIn("--devam", self.KAYNAK)
        self.assertIn("resume", self.KAYNAK)


class KarisimDurustlugu(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.m = _yukle()

    def test_eski_kume_ATILMAMIS(self):
        """Gerileme riski olmasin diye v7a'nin tamami korunur."""
        adlar = [d.parent.parent.name for d in self.m.TRAIN_DIZINLERI]
        for gerekli in ("rescuenet_2sinif_engelli", "sentetik_arena",
                        "copy_paste_t127", "dji_v7_x5"):
            self.assertIn(gerekli, adlar,
                          f"{gerekli} karisimdan dusmus — eski dagilim bozuldu")

    def test_YENI_acili_kume_eklenmis(self):
        adlar = [d.parent.parent.name for d in self.m.TRAIN_DIZINLERI]
        self.assertIn("sentetik_arena_bariyer_acili", adlar)

    def test_val_DEGISMEMIS(self):
        """Karsilastirilabilirlik: val kumesi v7a ile ayni kalmali."""
        self.assertEqual(1, len(self.m.VAL_DIZINLERI))
        self.assertIn("dji_v7", str(self.m.VAL_DIZINLERI[0]))


if __name__ == "__main__":
    unittest.main()
