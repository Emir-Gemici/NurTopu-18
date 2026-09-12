"""NÖBETÇİ — Mancınık enerji şematiği (Y-3.2.3-A02).

Mancınık ÜRETİLMEDİ; k/x/m/θ hiçbiri ölçülmedi/beyan edilmedi (§3.2.3). Bu
şekil yalnız ANALİTİK ÇERÇEVEYİ (enerji zinciri) sembolik değişkenlerle çizer.
Bu dosya o sözü ÖLÇER:

  T1  SVG geçerli XML, kök <svg>
  T2  drift kilidi: diskteki dosya üreticinin çıktısıyla bayt-eş
  T3  SVG'de HİÇBİR sayısal fiziksel değer yok (yalnız değişken adı + "BEYAN
      GEREKLİ" rozeti) — k, x, m, θ, v0, R'nin altıda da bu rozet var
  T4  BOLUM_3 §3.2.3 bu şekli embed eder ve mutasyon (rozet silinmesi,
      sayı eklenmesi) BOLUM_3'ün kendi metniyle ÇELİŞMEZ biçimde kalmaz
"""
from __future__ import annotations

import re
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
SEKILLER = KOK / "FDR" / "sekiller"
SVG = SEKILLER / "mancinik_enerji.svg"
BETIK = KOK / "scripts" / "fdr_mancinik_enerji_svg.py"
BOLUM_3 = KOK / "FDR" / "BOLUM_3_SISTEM_SPESIFIKASYONLARI.md"

DEGISKENLER = ["k (yay sabiti)", "m", "x", "v0 (çıkış hızı)",
               "θ (fırlatma açısı)", "R (menzil)"]


def _uret():
    return subprocess.run([sys.executable, "-B", str(BETIK)],
                          cwd=KOK, capture_output=True, text=True, check=True)


class MancinikEnerjiSemasi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _uret()
        cls.metin = SVG.read_text(encoding="utf-8")

    def test_T1_gecerli_svg(self):
        kok = ET.fromstring(self.metin)
        self.assertTrue(kok.tag.endswith("svg"), kok.tag)

    def test_T2_drift_kilidi(self):
        onceki = self.metin
        sonuc = _uret()
        self.assertEqual(0, sonuc.returncode, sonuc.stderr)
        self.assertEqual(onceki, SVG.read_text(encoding="utf-8"),
                         "betik iki kere aynı SVG'yi üretmeli (deterministik)")
        dogrula = subprocess.run([sys.executable, "-B", str(BETIK), "--dogrula"],
                                 cwd=KOK, capture_output=True, text=True)
        self.assertEqual(0, dogrula.returncode, dogrula.stdout + dogrula.stderr)

    def test_T3_sayisal_fiziksel_deger_YOK(self):
        # Yalnız sembolik ifadeler serbest (E, k, x, m, v0, θ, R, g, 2, ½) —
        # bunlar DEĞİŞKEN/SABİT ADI ya da matematik operatörüdür, ÖLÇÜM DEĞİL.
        # Yakalanmak istenen: "k = 340" gibi bir SAYI = DEĞİŞKEN ataması.
        atama_riski = re.findall(
            r"\b(k|x|m|v0|θ|R)\s*[=:]\s*[-+]?\d", self.metin)
        self.assertEqual([], atama_riski,
                         f"sembolik değişkene sayısal değer atanmış: {atama_riski}")
        for ad in DEGISKENLER:
            with self.subTest(degisken=ad):
                self.assertIn(ad, self.metin)
        self.assertEqual(6, self.metin.count("(BEYAN GEREKLİ)"),
                         "her değişkenin tam bir 'BEYAN GEREKLİ' rozeti olmalı")

    def test_T4_bolum3_embed_ve_tutarlilik(self):
        metin = BOLUM_3.read_text(encoding="utf-8")
        self.assertIn("mancinik_enerji.svg", metin)
        # Mancınık A02 satırı (3 `A02` satırından biri — bu şekli anan satır)
        # hâlâ BEYAN GEREKLİ demeli: şekil eklenmesi hükmü "GEÇTİ"ye çevirmez
        # (madde 6: kanıtsız bulgu yazılmaz).
        img_idx = metin.find("mancinik_enerji.svg")
        onceki_satir_baslangici = metin.rfind("| `A02`", 0, img_idx)
        self.assertNotEqual(-1, onceki_satir_baslangici,
                            "şekilden önce mancınık A02 satırı bulunamadı")
        satir = metin[onceki_satir_baslangici:metin.find("\n", onceki_satir_baslangici)]
        self.assertIn("BEYAN GEREKLİ", satir)
        self.assertIn("KISMEN", satir)


if __name__ == "__main__":
    unittest.main()
