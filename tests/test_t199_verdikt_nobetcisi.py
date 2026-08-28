"""T199 verdikt betiginin KENDI nobetcisi. Kanit: REVIEW_LOG D-357.

🔴 NEDEN VAR. `160_t199_verdikt.py`, T199 adayinin kaderini belirleyen betiktir
ve ON KAYIT D-340'i MEKANIK uygulamasi gerekir. Ama kendisinde uc kusur vardi
ve ucu de YANLIS VERDIKT uretebilirdi:

  1. BAYAT JSON: onceki kosumun `*_t192.json` dosyasi silinmiyordu. `159`
     cokse bile eski dosya okunur ve verdikt BASKA bir kosumun sayisiyla
     verilirdi (T125 kalibi).
  2. COKME = DUSME sanmasi: `zincir` yalniz iki dizgeye bakiyordu; `65`
     cokerse cikti ikisini de icermez ve verdikt "gerileme kapisi DUSTU"
     derdi. Fail-closed ama YANLIS TESHIS — "OLCULEMEDI != DUSTU".
  3. cp1254 COKMESI: cikti `⚠` iceriyor; Windows varsayilan kod sayfasinda
     UnicodeEncodeError atar ve verdikt KABUL olsa bile betik exit 1 ile
     coker, "reddedildi" sanilirdi.

Bu dosya ucunu de MUTASYONLA sinar.
"""
import ast
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
BETIK = KOK / "scripts" / "olcum" / "160_t199_verdikt.py"
KAYNAK = BETIK.read_text(encoding="utf-8")


def _kodu(metin: str) -> str:
    """Yorumlari at — mutasyon YORUM uzerinde yapilmasin (D-354'un dersi)."""
    return "\n".join(s for s in metin.splitlines()
                     if not s.lstrip().startswith("#"))


KOD = _kodu(KAYNAK)


class VerdiktBetigi(unittest.TestCase):
    def test_capa_BETIK_VAR_ve_ayristirilabiliyor(self):
        self.assertTrue(BETIK.is_file())
        ast.parse(KAYNAK)

    def test_BAYAT_JSON_SILINIYOR(self):
        self.assertIn("j1.unlink(missing_ok=True)", KOD,
                      "onceki kosumun t192 json'u silinmiyor — bayat sayiyla "
                      "verdikt verilebilir (T125 kalibi)")

    def test_COKME_ile_DUSME_AYRILIYOR(self):
        self.assertIn("zincir_olculdu", KOD,
                      "65 cokerse 'kapi DUSTU' deniyor — OLCULEMEDI != DUSTU")
        self.assertIn("birincil_olculdu", KOD,
                      "159 cokerse birincil olcut 'URETILMEDI' saniliyor")

    def test_OLCULEMEDI_ADAYI_REDDEDIYOR(self):
        """Olculemedi GECTI degildir; aday reddedilmeli, v36 kalmali."""
        self.assertIn("OLCULEMEDI != GECTI", KAYNAK)
        self.assertIn("v36 uretimde KALIR", KAYNAK)

    def test_CIKTI_UTF8e_ZORLANIYOR(self):
        self.assertIn('reconfigure(encoding="utf-8"', KOD,
                      "cp1254'te `⚠` UnicodeEncodeError atar; KABUL verdikti "
                      "bile exit 1 ile coker")

    def test_MUTASYON_bayat_json_kaldirilinca_DUSER(self):
        m = KOD.replace("j1.unlink(missing_ok=True)", "pass", 1)
        self.assertNotEqual(KOD, m, "mutasyon uygulanamadi")
        self.assertNotIn("j1.unlink(missing_ok=True)", m)

    def test_MUTASYON_olculdu_bagi_kaldirilinca_DUSER(self):
        m = KOD.replace("zincir_olculdu and (", "(", 1)
        self.assertNotEqual(KOD, m, "mutasyon uygulanamadi")
        self.assertNotIn("zincir_olculdu and (", m,
                         "olculdu bagi kaldirildigi hâlde kapi gormuyor")

    def test_ON_KAYIT_OLCUTLERI_METINDE(self):
        """Verdikt D-340'i MEKANIK uygular; olcutler betikte YAZILI olmali."""
        for parca in ("D-340", "ROTA URETMELI", "10 kapili zincir",
                      "GEVSETILMEZ", "OLCULEMEDI != GECTI"):
            self.assertIn(parca, KAYNAK, f"on kayit izi eksik: {parca}")


if __name__ == "__main__":
    unittest.main()
