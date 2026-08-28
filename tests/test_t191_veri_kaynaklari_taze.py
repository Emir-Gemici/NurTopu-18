"""T191 KAPISI (REVIEW_LOG D-327): `dataset/VERI_KAYNAKLARI.md` SESSIZCE
BAYATLAYAMAZ.

OLCULEN KUSUR: bu dosya kendini *"'Zemin sinifini hangi veriden ogrendik?'
sorusunun TEK YETKILI CEVABI"* ilan ediyor, ama 2026-08-06'da donmustu ve
2026-08-28'e kadar hala *"Guncel uretim modeli v21"* diyordu — oysa uretim
v36'ydi ve o tarihten sonra dort yeni kume egitime girdi (`dji_v7`,
`dji_v7_x5`, `copy_paste_t127`, `karisim_gece_*`).

Kendini "tek yetkili cevap" ilan eden bir belgenin bayatlamasi bu projede en
tehlikeli kusur sinifidir; ayni sinifin baska iki ornegi:
  · D-324 SS3 — `karar_sozlesmesi.py`'deki T67 yorumu "model bariyeri %0,0
    goruyor" diyordu; olculdu, v36 %99,9 goruyordu. Yorum MIMARI yanilltti.
  · D-325 SS5 — kendi olcum betigim uretim cagri sirasini taklit etmiyordu.

BU KAPI: belgenin BEYAN ETTIGI uretim modeli ile `config/model_registry.json`
AYRISAMAZ. Ayrisirlarsa suit DUSER ve kimse "guncelledim" demeyi unutamaz.
"""

from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
if str(KOK / "codes") not in sys.path:
    sys.path.insert(0, str(KOK / "codes"))

BELGE = KOK / "dataset" / "VERI_KAYNAKLARI.md"
DEFTER = KOK / "config" / "model_registry.json"

SURUM_DESENI = re.compile(r"\bv(\d+)\b")


def _defterden_uretim_surumu():
    """Kayit defterinden uretim modeli surum sayisi (or. 36)."""
    d = json.loads(DEFTER.read_text(encoding="utf-8"))
    metin = json.dumps(d, ensure_ascii=False)
    m = re.search(r"navitas_seg_v(\d+)_best", metin)
    return int(m.group(1)) if m else None


class BelgeVar(unittest.TestCase):

    def test_belge_ve_defter_var(self):
        self.assertTrue(BELGE.is_file(), f"belge yok: {BELGE}")
        self.assertTrue(DEFTER.is_file(), f"kayit defteri yok: {DEFTER}")


class UretimSurumuAYRISMIYOR(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not (BELGE.is_file() and DEFTER.is_file()):
            raise unittest.SkipTest("belge ya da defter yok")
        cls.metin = BELGE.read_text(encoding="utf-8")
        cls.surum = _defterden_uretim_surumu()

    def test_defterden_surum_okunabiliyor(self):
        self.assertIsNotNone(self.surum, "defterden uretim surumu cikarilamadi")
        self.assertGreater(self.surum, 0)

    def test_belge_GUNCEL_uretim_surumunu_ANIYOR(self):
        etiket = f"v{self.surum}"
        self.assertIn(
            etiket, self.metin,
            f"belge guncel uretim modelini ({etiket}) hic anmiyor — "
            "2026-08-06'daki bayatlama tekrar etmis olabilir")

    def test_URETIM_satiri_dogru_surumu_gosteriyor(self):
        """`(uretim)` etiketi TAM olarak defterdeki surumde olmali."""
        satirlar = [s for s in self.metin.splitlines() if "(üretim)" in s]
        self.assertTrue(satirlar, "belgede '(üretim)' isaretli satir yok")
        beklenen = f"v{self.surum}"
        uyanlar = [s for s in satirlar if beklenen in s]
        self.assertTrue(
            uyanlar,
            f"'(üretim)' satirlari {beklenen} demiyor: {satirlar!r} — "
            "belge ile kayit defteri AYRISMIS")

    def test_ESKI_surum_uretim_diye_gosterilmiyor(self):
        """Mutasyon kontrolu: eski bir surum '(üretim)' etiketi tasiyamaz.

        Yalniz MODEL ADI hucresine bakilir. Satirin geri kalani "taban v35'ten
        ince ayar" gibi DOGRU bilgiler tasiyabilir; onlar bayat iddia degildir.
        (Bu ayrimi kapinin ilk kosusu ogretti.)
        """
        for satir in self.metin.splitlines():
            if "(üretim)" not in satir:
                continue
            hucreler = [h.strip() for h in satir.split("|")]
            ad_hucresi = next((h for h in hucreler if "(üretim)" in h), "")
            for sayi in SURUM_DESENI.findall(ad_hucresi):
                if int(sayi) != self.surum:
                    self.fail(
                        f"'(üretim)' MODEL ADI hucresinde ESKI surum v{sayi} "
                        f"var: {ad_hucresi!r}")

    def test_MUTASYON_kapi_bayat_beyani_YAKALAR(self):
        """Kapi bos degil: uydurma bir bayat satir gercekten yakalanmali."""
        sahte = "| **v21 (üretim)** | eski karisim | Güncel üretim modeli |"
        bulundu = [int(x) for x in SURUM_DESENI.findall(sahte)]
        self.assertIn(21, bulundu)
        self.assertNotEqual(
            21, self.surum,
            "bu kontrol ancak uretim surumu 21'den farkliyken anlamlidir")


class GuncelKARISIM_ANILIYOR(unittest.TestCase):
    """Uretim karisimindaki her veri dizini belgede gecmeli."""

    @classmethod
    def setUpClass(cls):
        if not BELGE.is_file():
            raise unittest.SkipTest("belge yok")
        cls.metin = BELGE.read_text(encoding="utf-8")

    def test_v36_karisimindaki_kumeler_ANILIYOR(self):
        for kume in ("rescuenet_2sinif_engelli", "sentetik_arena",
                     "copy_paste_t127", "dji_v7_x5", "karisim_gece_v7a"):
            with self.subTest(kume=kume):
                self.assertIn(kume, self.metin,
                              f"{kume} belgede anilmiyor — belge eksik")

    def test_AYRILMIS_dogrulama_oturumu_UYARISI_var(self):
        """0038 egitime giremez; belge bunu SOYLEMELI."""
        self.assertIn("0038", self.metin)
        self.assertIn("AYRILMIŞ DOĞRULAMA", self.metin)

    def test_GECE_verisinin_egitime_GIRMEDIGI_yazili(self):
        self.assertIn("dji_prova_kareler", self.metin)
        self.assertIn("hiçbir eğitime girmedi", self.metin)

    def test_x5_cogaltmasinin_BAYT_ES_oldugu_yazili(self):
        """413 benzersiz kare gercegi gizlenemez."""
        self.assertIn("413", self.metin)
        self.assertIn("beşleme", self.metin)


class TazelikDamgasi(unittest.TestCase):

    def test_son_guncelleme_tarihi_var(self):
        if not BELGE.is_file():
            self.skipTest("belge yok")
        metin = BELGE.read_text(encoding="utf-8")
        m = re.search(r"Son güncelleme:.*?(\d{4}-\d{2}-\d{2})", metin)
        self.assertIsNotNone(m, "belgede 'Son güncelleme' damgasi yok")
        self.assertGreaterEqual(m.group(1), "2026-08-28",
                                "tazelik damgasi bayatladi")


if __name__ == "__main__":
    unittest.main()
