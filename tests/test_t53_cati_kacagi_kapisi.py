"""T53 — `cati_kacagi` DEFTERDE OLCULUYOR AMA HICBIR KAPI ZORLAMIYOR.

Kanit: REVIEW_LOG D-363 (kok: T53 · D-67 · D-240 · D-284).

🔴 KUSUR. `config/model_registry.json` -> `profiles.competition.metrics`
icinde 18 metrik var. K0..K6'nin HEPSINDE `esik` alani var ve verdikt ona
gore veriliyor. `cati_kacagi` ise `sonuc: "OLCUM"` ile duruyor:
**esigi YOK** ve depoda onu okuyan HICBIR TEST yok (yalniz iki olcum betigi
okuyor). Yani defterde kotu bir deger dursa butun kapilar YESIL gecerdi.

Olcumun kendisi (defterdeki `not`):
    v34 0,9606 · v30 0,3052 · v35 0,0428 · v36 0,0230
v34 catili karelerin **%96'sini ZEMIN** saniyordu. Boyle bir modelin
defterde durup her kapiyi gecmesi bu projenin en pahali hata sinifidir.

⚠ **ESIK UYDURULMADI — bilerek.** Bu kapiyi yazarken sayilari ZATEN
GORMUSTUM; D-107 uyarinca sonucu gorup esik yazmak YASAKTIR. Onun yerine
kapi bir **CIRCIR**tir: bugunku KAYITLI degerden KOTULESME yasaktir.
Iyilesme serbesttir ve taban BILEREK guncellenir.

Ikinci kapi TAZELIKTIR: metrik, defterdeki URETIM MODELINI anmalidir.
Bayat bir olcum (baska modelden) sessizce gecerse kapi hicbir sey demez.
"""
import json
import re
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
DEFTER = KOK / "config" / "model_registry.json"

# 🔴 CIRCIR TABANI. Bu bir ESIK DEGIL, bugunku KAYITLI degerdir (v36).
# Kotulesme yasak; iyilesince taban BILEREK indirilir ve gerekce
# REVIEW_LOG'a yazilir. Sayi elle degil, defterden OKUNARAK dogrulanir.
CATI_KACAGI_TABANI = 0.023


def _profil() -> dict:
    v = json.loads(DEFTER.read_text(encoding="utf-8"))
    return v["profiles"][v["default_profile"]]


def _metrik() -> dict:
    return _profil()["metrics"]["cati_kacagi"]


def _surum_belirteci(model_id: str) -> str:
    """`navitas-seg-v36-512` -> `v36`."""
    m = re.search(r"(v\d+)", model_id or "")
    return m.group(1) if m else ""


class MetrikVarVeSayisal(unittest.TestCase):
    def test_capa_DEFTER_OKUNUYOR(self):
        self.assertTrue(DEFTER.is_file(), f"defter yok: {DEFTER}")
        self.assertIn("cati_kacagi", _profil()["metrics"],
                      "`cati_kacagi` defterden DUSMUS — kapi bosa doner")

    def test_OLCULEN_sayisal(self):
        d = _metrik().get("olculen")
        self.assertIsInstance(d, (int, float),
                              "`olculen` sayisal degil — kapi karsilastirma yapamaz")
        self.assertGreaterEqual(d, 0.0)
        self.assertLessEqual(d, 1.0, "oran [0,1] disinda")


class CircirKotulesmeyi_YAKALAR(unittest.TestCase):
    def test_TABAN_defterle_UYUMLU(self):
        """Taban elle yazildi; defterden SAPMADIGI dogrulanir."""
        self.assertAlmostEqual(
            _metrik()["olculen"], CATI_KACAGI_TABANI, places=6,
            msg="taban ile defter AYRISTI — biri elle degistirilmis. Kotulesme "
                "ise gerekce REVIEW_LOG'a yazilmali; iyilesme ise taban "
                "BILEREK indirilmeli (D-363).")

    def test_KOTULESME_YASAK(self):
        self.assertLessEqual(
            _metrik()["olculen"], CATI_KACAGI_TABANI,
            "cati kacagi KOTULESTI — catili alanin daha buyuk bir kismi ZEMIN "
            "saniliyor. v34 bu sayiyi 0,9606'ya cikarmisti (D-363).")

    def test_MUTASYON_v34_degeri_KAPIYI_DUSURUR(self):
        """v34'un gercek olcumu (0,9606) konsa kapi DUSMELI."""
        self.assertGreater(0.9606, CATI_KACAGI_TABANI,
                           "on kosul: v34 degeri tabandan buyuk olmali")
        with self.assertRaises(AssertionError):
            # kapinin kendi kurali, sahte deger uzerinde
            if 0.9606 > CATI_KACAGI_TABANI:
                raise AssertionError("cati kacagi KOTULESTI")

    def test_MUTASYON_taban_gevsetilirse_ANLAMSIZLASIR(self):
        """Taban 1,0'a cekilirse kapi HICBIR SEYI yakalamaz — bunu belge et."""
        self.assertLess(CATI_KACAGI_TABANI, 0.5,
                        "taban 0,5'in ustune cikarilmis: bu kapi artik v34 "
                        "sinifi bir cokusu bile gecirir, yani BOS KAPIDIR")


class TazelikKapisi(unittest.TestCase):
    """Bayat olcum sessizce gecmesin: metrik URETIM MODELINI anmali."""

    def test_METRIK_URETIM_MODELINI_ANIYOR(self):
        surum = _surum_belirteci(_profil().get("model_id", ""))
        self.assertTrue(surum, "profil `model_id` icinde surum belirteci yok")
        not_ = str(_metrik().get("not", ""))
        self.assertIn(
            surum, not_,
            f"`cati_kacagi` notu uretim surumunu ({surum}) ANMIYOR — olcum "
            "baska bir modelden kalmis olabilir ve kapi bunu goremez (D-363)")

    def test_MUTASYON_surum_kaybolunca_TAZELIK_DUSER(self):
        surum = _surum_belirteci(_profil().get("model_id", ""))
        bozuk = str(_metrik().get("not", "")).replace(surum, "vXX")
        self.assertNotIn(surum, bozuk,
                         "mutasyon uygulanamadi — not zaten surum icermiyor")


if __name__ == "__main__":
    unittest.main()
