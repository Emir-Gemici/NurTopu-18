"""T110 KAPISI: K0 oran GORUNURLUGU raporlar, BLOKLAMAZ (karar D-186).

KARAR (D-186, mimar). K0'in cezalandirdigi yon (AZ zemin gormek) GUVENLI
yondur — fail-closed. Tehlikeli yonu (COK zemin gormek) K0 olcmez; onu K2/K3
olcer (n=258). Yani K0 bir EMNIYET degil YETENEK kapisidir:

  · `> 0` olcutu DEGISMEZ, figur icin sayisal esik KONMAZ.
  · Asil sorun 16 kat dususun SESSIZ gecmesiydi -> cozum GORUNURLUK.
  · Asil kusur baska yerdeydi: `bos == 0` yalnizca 8 karede bakiliyordu
    (raw_frames 67 -> 8 · copy_paste 393 -> 8). ORNEKLEME KALDIRILDI.

BU DOSYANIN ISI: oranin gercekten RAPORLADIGINI ve gercekten BLOKLAMADIGINI
sabitlemek; ve tabanin METINDEN degil SAYIDAN okundugunu (D-180 kusur sinifi).

⚠ Model YUKLENMEZ (emrin sarti): `65_kabul_denetcisi` icindeki uc SAF
fonksiyon sinanir — `k0_gecti`, `k0_taban_orani`, `k0_dikkat_satiri`.
"""

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
_OLCUM = KOK / "scripts" / "olcum"
_DENETCI = _OLCUM / "65_kabul_denetcisi.py"
# `65` kendi klasorundeki `ayarlar`i ithal eder (REPO koku oradan gelir).
if str(_OLCUM) not in sys.path:
    sys.path.insert(0, str(_OLCUM))

_spec = importlib.util.spec_from_file_location("kabul_denetcisi_t110", _DENETCI)
K65 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(K65)


def _gecici_defter(dizin, *, k0_alanlari):
    cfg = Path(dizin) / "config"
    cfg.mkdir(parents=True, exist_ok=True)
    (cfg / "model_registry.json").write_text(json.dumps({
        "schema_version": 1,
        "default_profile": "sinama",
        "profiles": {"sinama": {"path": "models/x.pt", "imgsz": 512,
                                "metrics": {"k0_korluk": dict(k0_alanlari)}}},
    }, ensure_ascii=False), encoding="utf-8")
    return Path(dizin)


class K0Gorunurlugu(unittest.TestCase):

    # ── 1) ORAN SATIRI band DISINDA basiliyor, ICINDE basilmiyor ──────────
    def test_oran_bandin_DISINDA_dikkat_satiri_BASILIYOR(self):
        for oran in (16.24, 2.01, 0.49, 0.0):
            with self.subTest(oran=oran):
                satir = K65.k0_dikkat_satiri(oran)
                self.assertIsNotNone(satir, f"oran {oran} icin uyari YOK")
                self.assertIn("DIKKAT", satir)
                self.assertIn(f"{oran:.2f}", satir)

    def test_oran_bandin_ICINDE_dikkat_satiri_BASILMIYOR(self):
        for oran in (K65.K0_ORAN_ALT, 1.00, 1.62, K65.K0_ORAN_UST):
            with self.subTest(oran=oran):
                self.assertIsNone(K65.k0_dikkat_satiri(oran),
                                  f"oran {oran} band ICINDE, uyari OLMAMALI")

    def test_dikkat_satiri_YONU_dogru_soyluyor(self):
        ust = K65.k0_dikkat_satiri(16.24)
        alt = K65.k0_dikkat_satiri(0.10)
        self.assertIn("TEHLIKELI", ust)
        self.assertIn("K2/K3", ust)
        self.assertIn("YETENEK", alt)
        self.assertIn("fail-closed", alt)

    # ── 2) 🔴 ORAN NE OLURSA OLSUN K0 VERDIKTI DEGISMIYOR ─────────────────
    def test_K0_olcutu_ORANDAN_BAGIMSIZ(self):
        """`k0_gecti` imzasinda `oran` YOKTUR — bloklamamasi yapisaldir.

        Ayrica davranissal olarak da sinanir: ayni (figur, bos, bos) girdisi
        icin sonuc, oran 0,01 de olsa 100 de olsa AYNIDIR — cunku oran
        fonksiyona GIREMEZ.
        """
        import inspect
        imza = inspect.signature(K65.k0_gecti)
        self.assertEqual(["figur", "raw_bos", "cp_bos"], list(imza.parameters),
                         "k0_gecti imzasina oran/dikkat sizmis")
        # olcut TABLOSU — D-186: `> 0` ve iki kumede de bos maske yok
        self.assertTrue(K65.k0_gecti(0.0049, 0, 0))
        self.assertTrue(K65.k0_gecti(0.0796, 0, 0))     # 16 kat sapma -> YINE GECER
        self.assertFalse(K65.k0_gecti(0.0, 0, 0))       # `> 0` dustu
        self.assertFalse(K65.k0_gecti(None, 0, 0))
        self.assertFalse(K65.k0_gecti(0.30, 1, 0))      # raw'da bos maske
        self.assertFalse(K65.k0_gecti(0.30, 0, 3))      # cp'de bos maske

    def test_dikkat_satiri_YAN_ETKISIZ(self):
        """Uyari yalniz METIN uretir; hicbir durum degistirmez."""
        once = K65.k0_gecti(0.0796, 0, 0)
        K65.k0_dikkat_satiri(16.24)
        self.assertEqual(once, K65.k0_gecti(0.0796, 0, 0))

    # ── 3) DEFTERDE ALAN YOKSA: oran None, verdikt ETKILENMEZ ─────────────
    def test_defterde_figur_zemin_orani_YOKSA_oran_None(self):
        with tempfile.TemporaryDirectory() as td:
            kok = _gecici_defter(td, k0_alanlari={
                "olculen": "figur zemin %0,49 · raw bos 0/8 · cp bos 0/8"})
            oran, taban, notu = K65.k0_taban_orani(0.0049, kok=kok)
        self.assertIsNone(oran)
        self.assertIsNone(taban)
        self.assertIn("taban kayitli DEGIL", notu)
        self.assertIsNone(K65.k0_dikkat_satiri(oran))
        # yokluk ne BASARI ne BASARISIZLIK — olcut yine kendi girdisine bakar
        self.assertTrue(K65.k0_gecti(0.0049, 0, 0))

    def test_taban_SAYIDAN_okunuyor_METINDEN_DEGIL(self):
        """`olculen` metni YANILTICI olsa bile oran SAYISAL alandan gelir.

        Metinde %9,99 yaziyor, sayisal alanda 0,0049 var; dogru taban
        0,0049 olmali (D-180: stdout/metin parse ederek karar URETILMEZ).
        """
        with tempfile.TemporaryDirectory() as td:
            kok = _gecici_defter(td, k0_alanlari={
                "olculen": "figur zemin %9,99 · raw bos 7/8 · cp bos 5/8",
                "figur_zemin_orani": 0.0049})
            oran, taban, _n = K65.k0_taban_orani(0.0049, kok=kok)
        self.assertAlmostEqual(0.0049, taban)
        self.assertAlmostEqual(1.0, oran, places=6)

    def test_taban_SIFIRSA_oran_hesaplanmiyor(self):
        with tempfile.TemporaryDirectory() as td:
            kok = _gecici_defter(td, k0_alanlari={"figur_zemin_orani": 0.0})
            oran, taban, notu = K65.k0_taban_orani(0.0049, kok=kok)
        self.assertIsNone(oran)
        self.assertEqual(0.0, taban)
        self.assertIn("hesaplanamadi", notu)

    # ── 4) POZITIF KONTROL ────────────────────────────────────────────────
    def test_POZITIF_KONTROL_oran_mantigi_kaldirilirsa_DUSER(self):
        """`k0_dikkat_satiri` her zaman None dondurse (yani oran mantigi
        kaldirilsa) (1) numarali testler DUSERDI — yani onlar gercekten bu
        mantigi siniyor (D-15/K-04)."""
        def _kaldirilmis(_oran):
            return None
        self.assertIsNone(_kaldirilmis(16.24))
        self.assertIsNotNone(K65.k0_dikkat_satiri(16.24),
                             "gercek kod 16 kat sapmayi bildirmiyor")

    def test_POZITIF_KONTROL_ornekleme_kaldirildi(self):
        """`bos` kontrolu TAM KUMEDE kosmali; 8'lik dilimleme kalmamali."""
        kaynak = _DENETCI.read_text(encoding="utf-8")
        self.assertNotIn("// 8)][:8]", kaynak,
                         "8 karelik ornekleme HALA duruyor (T110/D-186)")
        self.assertIn("yollar = sorted(kok.rglob(desen))", kaynak)


if __name__ == "__main__":
    unittest.main()
