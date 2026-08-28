"""T54 — ESLEME SADECE TANIMLI DEGIL, MASKEYE UYGULANIYOR MU?

Kanit: REVIEW_LOG D-362 (kusur: D-284 §3).

🔴 NEDEN VAR. `tests/test_donusum_esleme.py` `BLOCKED_HAM` / `TRAVERSABLE_HAM`
KUMELERINI civiliyor ve iki zincirin (`download_and_convert` ↔
`57_t54_engel_eslemesi`) ayrismadigini sinar. Ama `process_split`in o
kumeleri MASKEYE UYGULAYIP uygulamadigini HIC sinamiyordu.

Yani su mutasyon — D-67'nin KOK NEDENININ birebir kendisi — mevcut kapilardan
SAG CIKIYORDU:

    blocked_mask = np.isin(lbl_np, [1, 8])          # sabit liste, kume DEGIL

Kume dogru tanimli kaldigi icin butun mevcut testler YESIL gecerdi; ama
uretilen etiketlerde zemin-olmayan siniflarin bir kismi ENGEL SAYILMAZDI.
v16 bu kusurdan molozа basmada %2,7 -> %31,6 cokmustu.

BU DOSYA URETIM KODUNU DEGISTIRMEZ. Iki sey yapar:
  1. YAPI — maskeler KUME ADLARINDAN kuruluyor mu (AST; sabit liste yasak),
  2. DAVRANIS — kumelerdeki HER ham id dogru maskeye dusuyor mu (sentetik
     etiket dizisiyle, dosya G/C YOK).
"""
import ast
import sys
import unittest
from pathlib import Path

import numpy as np

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "dataset"))

import download_and_convert as D  # noqa: E402

KAYNAK = (KOK / "dataset" / "download_and_convert.py").read_text(encoding="utf-8")


def _isin_cagrilari(metin: str):
    """`np.isin(...)` cagrilarinin (hedef_adi, ikinci_arguman_dugumu) listesi."""
    agac = ast.parse(metin)
    out = []
    for d in ast.walk(agac):
        if not isinstance(d, ast.Assign):
            continue
        deger = d.value
        # `.astype(...)` sarmalini soy
        while isinstance(deger, ast.Call) and isinstance(deger.func, ast.Attribute) \
                and deger.func.attr == "astype":
            deger = deger.func.value
        if (isinstance(deger, ast.Call) and isinstance(deger.func, ast.Attribute)
                and deger.func.attr == "isin" and len(deger.args) >= 2):
            hedef = getattr(d.targets[0], "id", None)
            out.append((hedef, deger.args[1]))
    return out


def _adlar(dugum) -> set:
    return {n.id for n in ast.walk(dugum) if isinstance(n, ast.Name)}


class MaskeKumedenKuruluyor(unittest.TestCase):
    """YAPI: sabit liste degil, KUME ADI kullanilmali."""

    def test_capa_ISIN_CAGRILARI_BULUNUYOR(self):
        c = _isin_cagrilari(KAYNAK)
        self.assertGreaterEqual(len(c), 2,
                                "np.isin cagrilari ayristirilamadi — asagidaki "
                                "testler BOSA doner")
        self.assertIn("road_mask", [h for h, _ in c])
        self.assertIn("blocked_mask", [h for h, _ in c])

    def test_ROAD_maskesi_TRAVERSABLE_HAMdan(self):
        for hedef, arg in _isin_cagrilari(KAYNAK):
            if hedef == "road_mask":
                self.assertIn("TRAVERSABLE_HAM", _adlar(arg),
                              "road_mask kume adindan kurulmuyor (sabit liste?)")
                return
        self.fail("road_mask atamasi bulunamadi")

    def test_BLOCKED_maskesi_BLOCKED_HAMdan(self):
        for hedef, arg in _isin_cagrilari(KAYNAK):
            if hedef == "blocked_mask":
                self.assertIn("BLOCKED_HAM", _adlar(arg),
                              "blocked_mask kume adindan kurulmuyor — D-67'nin "
                              "kok nedeni (sabit liste) geri gelmis olabilir")
                return
        self.fail("blocked_mask atamasi bulunamadi")

    def test_MUTASYON_sabit_liste_YAKALANIR(self):
        """D-67'nin birebir kok nedeni: kume yerine sabit liste."""
        mutant = KAYNAK.replace(
            "blocked_mask = np.isin(lbl_np, sorted(BLOCKED_HAM)).astype(np.uint8)",
            "blocked_mask = np.isin(lbl_np, [1, 8]).astype(np.uint8)", 1)
        self.assertNotEqual(KAYNAK, mutant, "mutasyon uygulanamadi")
        for hedef, arg in _isin_cagrilari(mutant):
            if hedef == "blocked_mask":
                self.assertNotIn("BLOCKED_HAM", _adlar(arg),
                                 "sabit liste konuldugu hâlde kapi gormuyor — "
                                 "BOS KAPI")
                return
        self.fail("mutant govdede blocked_mask bulunamadi")


class HerHamId_DOGRU_MASKEYE(unittest.TestCase):
    """DAVRANIS: kumelerdeki HER ham id dogru maskeye dusuyor mu?

    Dosya G/C YOK — sentetik bir etiket dizisi kurulur ve uretimin KENDI
    ifadeleri (`np.isin(..., sorted(KUME))`) uzerinde kosulur.
    """

    def test_her_ham_id_TEK_maskeye_duser(self):
        hepsi = sorted(D.TRAVERSABLE_HAM | D.BLOCKED_HAM)
        lbl = np.array(hepsi, dtype=np.int32).reshape(1, -1)
        road = np.isin(lbl, sorted(D.TRAVERSABLE_HAM))
        blocked = np.isin(lbl, sorted(D.BLOCKED_HAM))
        self.assertFalse((road & blocked).any(),
                         "bir ham id HEM zemin HEM engel maskesine dusuyor")
        self.assertTrue((road | blocked).all(),
                        "bir ham id HICBIR maskeye dusmuyor — sessizce kayboluyor")

    def test_ETIKETSIZ_0_hicbir_maskeye_girmez(self):
        lbl = np.zeros((4, 4), dtype=np.int32)
        self.assertFalse(np.isin(lbl, sorted(D.TRAVERSABLE_HAM)).any())
        self.assertFalse(np.isin(lbl, sorted(D.BLOCKED_HAM)).any(),
                         "ham 0 (etiketsiz) engel sayiliyor — payda semantigi bozulur")

    def test_ARAC_siniflari_ENGEL_tarafinda(self):
        """v16 dersi: arac ETIKETSIZ birakilamaz."""
        for ham in sorted(D.VEHICLE_HAM):
            lbl = np.array([[ham]], dtype=np.int32)
            self.assertTrue(np.isin(lbl, sorted(D.BLOCKED_HAM)).all(),
                            f"arac ham {ham} ENGEL maskesine dusmuyor")

    def test_MUTASYON_sabit_liste_DAVRANISI_BOZAR(self):
        """Sabit `[1, 8]` gercekten kayip uretir mi — sayiyla goster."""
        hepsi = sorted(D.BLOCKED_HAM)
        lbl = np.array(hepsi, dtype=np.int32).reshape(1, -1)
        dogru = int(np.isin(lbl, sorted(D.BLOCKED_HAM)).sum())
        mutant = int(np.isin(lbl, [1, 8]).sum())
        self.assertEqual(dogru, len(hepsi))
        self.assertLess(mutant, dogru,
                        "sabit liste HICBIR kayip uretmiyor — bu mutasyon "
                        "ayirt edici degil, test yeniden tasarlanmali")


if __name__ == "__main__":
    unittest.main()
