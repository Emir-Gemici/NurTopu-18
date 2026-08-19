"""T105 KAPISI: K5'te OLCULEMEDI ucuncu durumdur — GECTI DEGIL, DUSTU DEGIL.

KUSUR (REVIEW_LOG D-180). `65_kabul_denetcisi` K5'i alt betigin stdout'undan
ayristirir; satir basilmazsa `kes = None` kalir ve eski kod
`gecti["K5"] = (kes == 0)` ile bunu DUSTU sayardi. `63_bariyer_kesisimi.py`
TEK karede kosar; o karede rota cikmazsa kesisim OLCULEMEZ. Olculdu: v22/v23/
v30 UCU DE None'a dusuyordu — satir hicbir modeli ayirt etmiyordu ve "rota
bariyere basti" seklinde YANLIS ATIF uretiyordu.

🔴 MIMARIN KISITI — bu testlerin kilitledigi sey: **OLCULEMEDI != GECTI.**
OLCULEMEDI terfiyi YINE BLOKLAR (fail-closed) ama raporda DUSTU'den AYRI
gorunur. "Olculemeyeni gecir" seklinde bir duzeltme KABUL EDILMEZ — asagida
bunu dogrudan sinayan bir test vardir ve boyle bir "duzeltme" yapilirsa DUSER.

⚠ Model YUKLENMEZ; `65`in saf fonksiyonlari (`k5_durumu`, `k5_gecti`) sinanir
(test_k0_gorunurlugu.py kalibi).
"""

import importlib.util
import sys
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
_OLCUM = KOK / "scripts" / "olcum"
if str(_OLCUM) not in sys.path:
    sys.path.insert(0, str(_OLCUM))

_spec = importlib.util.spec_from_file_location(
    "kabul_denetcisi_t105", _OLCUM / "65_kabul_denetcisi.py")
K65 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(K65)


class K5UcuncuDurum(unittest.TestCase):

    # ── UC DURUM AYRIK ────────────────────────────────────────────────────
    def test_uc_durum_dogru_etiketleniyor(self):
        self.assertEqual("GECTI", K65.k5_durumu(0))
        self.assertEqual("DUSTU", K65.k5_durumu(5))
        self.assertEqual("DUSTU", K65.k5_durumu(1))
        self.assertEqual("OLCULEMEDI", K65.k5_durumu(None))

    def test_OLCULEMEDI_ne_GECTI_ne_DUSTU(self):
        """Ucuncu durum digerlerinden AYRIKTIR — rapor onlari karistiramaz."""
        d = K65.k5_durumu(None)
        self.assertNotEqual("GECTI", d)
        self.assertNotEqual("DUSTU", d)

    # ── 🔴 FAIL-CLOSED KILIDI: OLCULEMEDI TERFIYI BLOKLAR ─────────────────
    def test_OLCULEMEDI_terfiyi_BLOKLAR(self):
        """MIMARIN KISITI. Biri `k5_gecti`yi "None'u da gecir" diye
        "duzeltirse" bu test DUSER — kisit koddan sokulup atilamaz."""
        self.assertFalse(K65.k5_gecti(None),
                         "OLCULEMEDI GECTI sayildi — 'olculemeyeni gecir' "
                         "duzeltmesi KABUL EDILMEZ (T105 kisiti)")

    def test_yalniz_sifir_kesisim_GECER(self):
        self.assertTrue(K65.k5_gecti(0))
        self.assertFalse(K65.k5_gecti(1))
        self.assertFalse(K65.k5_gecti(173))
        self.assertFalse(K65.k5_gecti(None))

    # ── ESKI DAVRANISLA FARKIN KANITI ─────────────────────────────────────
    def test_eski_davranis_None_ile_ayni_VERDIKT_farkli_RAPOR(self):
        """Eski kod da None'u bloklardi (kes == 0 -> False); yeni kodun
        FARKI verdikt degil RAPORDUR. Bu test o denkligi ve farki birlikte
        civiler: verdikt ayni kalir, etiket ayrisir."""
        eski_verdikt = (None == 0)                    # noqa: E711 — eski ifade
        self.assertEqual(eski_verdikt, K65.k5_gecti(None),
                         "verdikt eski davranistan SAPMIS — T105 yalniz "
                         "raporu ayristirir, kapiyi degistirmez")
        self.assertEqual("OLCULEMEDI", K65.k5_durumu(None),
                         "rapor etiketi ayrismali — kusurun kendisi buydu")


if __name__ == "__main__":
    unittest.main()
