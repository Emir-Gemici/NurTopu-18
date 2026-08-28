"""T116 — "kaplama" ADI IKI FARKLI PAYDA TASIYOR. Kanit: REVIEW_LOG D-361.

🔴 KUSUR. Ayni kavram iki yerde, IKI FARKLI PAYDAYLA hesaplaniyor:

  scripts/olcum/65_kabul_denetcisi.py::kaplama
      maske ICERIGE KIRPILIR ama payda LETTERBOX TUVALIDIR:
          return float((mk[0] > 0).mean())          # payda = sq.shape

  codes/karar_sozlesmesi.py::zemin_kaplamasi(trav, icerik)
      payda ICERIK KUTUSUDUR (iw*ih).

Ve `ZEMIN_KAPLAMA_TAVANI = 0.55` **ICERIK** paydasina gore kalibredir
(T142/D-286).

OLCULDU (2026-08-28, v36, data/raw_frames'ten 8 kare): iki sayinin orani
SABIT **1,78x** (16:9 karenin kareye letterbox'lanmasi). Yani `65`in sayisi
sozlesmeninkinden 1,78 KAT KUCUKTUR. O sayiyi 0,55 tavaniyla kiyaslayan biri
fiilen tavani **0,98**'e cikarmis olur (0,55 x 1,78) — gercekte %98 zemin
goren bir kare bile "tavan altinda" gorunur.

BU DOSYA YENI ESIK KOYMAZ ve URETIM KODUNU DEGISTIRMEZ. Yaptigi sey farkin
VARLIGINI ve BUYUKLUGUNU kilitlemek, ve iki sayinin KARISTIRILMADIGINI
kaynak duzeyinde sinamaktir. Alan adlarinin duzeltilmesi (T118) MIMAR
KARARIDIR ve burada verilmez.
"""
import ast
import sys
import unittest
from pathlib import Path

import numpy as np

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "codes"))

from karar_sozlesmesi import ZEMIN_KAPLAMA_TAVANI, zemin_kaplamasi  # noqa: E402

DENETCI = KOK / "scripts" / "olcum" / "65_kabul_denetcisi.py"
TUVAL, IC_W, IC_H = 512, 512, 288          # 16:9 icerik, kare tuval


def _kaplama_govdesi() -> str:
    m = DENETCI.read_text(encoding="utf-8")
    i = m.index("def kaplama(")
    j = m.find("\ndef ", i + 10)
    return m[i:j if j > 0 else len(m)]


def _kullanilan_adlar(govde: str) -> set:
    """Govdede GERCEKTEN KULLANILAN adlar (AST).

    🔴 Metin aramasi YETMEZ ve ilk yazimda tam bu yuzden yanlis alarm verdi:
    `kaplama()`in docstring'ine sabitin ADINI yazinca metin araması onu
    "kullanim" sandi. AST yalnizca KULLANIMI gorur — docstring bir
    `Constant`tir, `Name` degil.
    """
    return {d.id for d in ast.walk(ast.parse(govde)) if isinstance(d, ast.Name)}


def _sahne():
    """16:9 icerik, kare tuvale letterbox'lanmis. Icerik TAMAMEN zemin."""
    z = np.zeros((TUVAL, TUVAL), np.uint8)
    y0 = (TUVAL - IC_H) // 2
    z[y0:y0 + IC_H, 0:IC_W] = 1
    return z, (0, y0, IC_W, IC_H)


class IkiPayda(unittest.TestCase):
    """Farkin VARLIGI ve BUYUKLUGU — model YUKLENMEDEN."""

    def test_ICERIK_paydasi_1_0_verir(self):
        z, ic = _sahne()
        self.assertAlmostEqual(
            zemin_kaplamasi(z, ic), 1.0, places=6,
            msg="icerik tamamen zeminken icerik paydasi 1,0 vermeli")

    def test_TUVAL_paydasi_ayni_maskede_DAHA_KUCUK(self):
        z, ic = _sahne()
        tuval_paydali = float((z > 0).mean())            # 65'in yaptigi
        icerik_paydali = float(zemin_kaplamasi(z, ic))   # sozlesmenin yaptigi
        self.assertLess(tuval_paydali, icerik_paydali,
                        "iki payda AYNI sonucu veriyor — test ayirt etmiyor")
        self.assertAlmostEqual(
            icerik_paydali / tuval_paydali,
            (TUVAL * TUVAL) / (IC_W * IC_H), places=3,
            msg="oran tuval/icerik ALAN oranina esit olmali")

    def test_TAVAN_ICERIK_paydasina_ait(self):
        """Tuval paydasiyla kiyas, tavani FIILEN yukseltir."""
        etkin = ZEMIN_KAPLAMA_TAVANI * (TUVAL * TUVAL) / (IC_W * IC_H)
        self.assertGreater(
            etkin, 0.9,
            "16:9 letterbox'ta tuval paydasiyla kiyas 0,55 tavanini fiilen "
            f"{etkin:.2f}'e cikarir — bu testin sabitledigi tehlike budur")


class KaristirilmiyorMu(unittest.TestCase):
    """Asil tehlike: `65`in sayisinin ICERIK paydali TAVANLA kiyaslanmasi."""

    def test_capa_GOVDE_AYRISTIRILIYOR(self):
        g = _kaplama_govdesi()
        self.assertIn("def kaplama(", g)
        self.assertIn("mean()", g)
        ast.parse(g)

    def test_65_kaplama_TAVANLA_KIYASLANMIYOR(self):
        self.assertNotIn(
            "ZEMIN_KAPLAMA_TAVANI", _kullanilan_adlar(_kaplama_govdesi()),
            "65'in TUVAL paydali sayisi ICERIK paydali tavanla KIYASLANIYOR — "
            "tavan fiilen 1,78 kat gevser (D-361)")

    def test_MUTASYON_tavan_kiyasi_eklenirse_YAKALANIR(self):
        g = _kaplama_govdesi()
        mutant = g.replace(
            "return float((mk[0] > 0).mean())",
            "return float((mk[0] > 0).mean()) > ZEMIN_KAPLAMA_TAVANI", 1)
        self.assertNotEqual(g, mutant, "mutasyon uygulanamadi")
        self.assertIn("ZEMIN_KAPLAMA_TAVANI", _kullanilan_adlar(mutant),
                      "tavan kiyasi eklendigi hâlde kapi gormuyor — BOS KAPI")

    def test_MUTASYON_docstring_BAHSI_kirletmiyor(self):
        """Docstring'de gecen ad 'kullanim' sayilmamali (AST'nin sebebi)."""
        g = _kaplama_govdesi()
        self.assertIn("ZEMIN_KAPLAMA_TAVANI", g,
                      "on kosul: ad docstring'de GECMELI, yoksa bu test bos")
        self.assertNotIn("ZEMIN_KAPLAMA_TAVANI", _kullanilan_adlar(g),
                         "docstring bahsi KULLANIM sayiliyor — metin aramasina "
                         "geri donulmus olabilir")

    def test_PAYDA_FARKI_BELGELENMIS(self):
        """Fark `kaplama()`in KENDI govdesinde yazili olmali."""
        g = _kaplama_govdesi()
        for parca in ("PAYDA", "LETTERBOX", "zemin_kaplamasi", "1,78"):
            self.assertIn(parca, g,
                          f"kaplama() govdesinde '{parca}' gecmiyor — iki payda "
                          "birbirine karistirilmaya acik (D-361)")


if __name__ == "__main__":
    unittest.main()
