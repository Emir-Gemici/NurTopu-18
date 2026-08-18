"""S5 KAPISI: cikarim `imgsz`i TEK KAYNAKTAN gelir ve DENETLENIR.

KUSUR (mimar tanisi, kodda okundu · REVIEW_LOG D-175). `model_kayit_dogrula`
kayit defteriyle yalniz `path`/dosya adini kiyasliyordu; **`imgsz` alanini HIC
okumuyordu.** Defterin `imgsz`i 640'a cevrilse `INFER_SIZE` 512'de kalir ve
HICBIR YERDE SES CIKMAZDI — defterin KENDI notunda yazili D-116/5 kusurunun
("surum v27'ye gecince cevrilmedi") birebir aynisi.

⚠ Bugun 512 == 512 UYUSUYOR. Yani bu CANLI BIR HATA DEGIL, ACIK BIR KAPIDIR;
bu dosya kapiyi kapatir ve acilirsa DUSER.

SINANANLAR:
  1. defter `imgsz` == calisan `imgsz` -> UYUMLU, `durum == "eslesti"`
  2. FARKLI -> UYUMSUZ ve `detay` IKI degeri de tasiyor
  3. alan YOKSA -> fail-closed (`path` yoklugu nasil ele aliniyorsa oyle)
  4. varsayilan disina cikilinca GORUNUR UYARI (stderr) basiliyor
  5. 🔴 MUTASYON: `imgsz` kiyasi kaldirilirsa (2) DUSER — testin gercekten
     bu alani sinadiginin kaniti (D-15/K-04)

⚠ URETIM `config/`i DEGISTIRILMEZ: gecici defterler `tmp` altinda kurulur ve
`kok=` parametresiyle verilir.
"""

import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from codes import rpi_inference as R

KOK = Path(__file__).resolve().parent.parent


def _gecici_defter(dizin, *, imgsz, path_="models/sahte_model.pt"):
    """`kok=` ile verilebilecek gecici bir kayit defteri kur."""
    cfg = Path(dizin) / "config"
    cfg.mkdir(parents=True, exist_ok=True)
    (cfg / "model_registry.json").write_text(json.dumps({
        "schema_version": 1,
        "default_profile": "sinama",
        "profiles": {"sinama": {"path": path_, "imgsz": imgsz,
                                "sha256": "0" * 64}},
    }, ensure_ascii=False), encoding="utf-8")
    return Path(dizin)


def _imgszsiz_defter(dizin, *, path_="models/sahte_model.pt"):
    cfg = Path(dizin) / "config"
    cfg.mkdir(parents=True, exist_ok=True)
    (cfg / "model_registry.json").write_text(json.dumps({
        "schema_version": 1,
        "default_profile": "sinama",
        "profiles": {"sinama": {"path": path_, "sha256": "0" * 64}},
    }, ensure_ascii=False), encoding="utf-8")
    return Path(dizin)


class ImgszTekKaynak(unittest.TestCase):

    # ── 1) URETIM BUGUN UYUSUYOR — davranis DEGISMEDI ─────────────────────
    def test_uretim_defteri_ile_INFER_SIZE_UYUSUYOR(self):
        uyumlu, detay = R.model_kayit_dogrula(R.varsayilan_model_yolu())
        self.assertTrue(uyumlu, detay)
        self.assertEqual("eslesti", detay["durum"])
        self.assertEqual(detay["beklenen_imgsz"], detay["calisan_imgsz"])

    def test_INFER_SIZE_defterden_TURETILIYOR(self):
        """Ciplak sabit degil: modulun degeri defterin degeridir."""
        self.assertEqual(R._kayittan_imgsz(), R.INFER_SIZE)

    # ── 2) FARKLIYSA fail-closed, ve detay IKI degeri de tasir ────────────
    def test_imgsz_FARKLIYSA_uyumsuz(self):
        with tempfile.TemporaryDirectory() as td:
            kok = _gecici_defter(td, imgsz=640)
            uyumlu, detay = R.model_kayit_dogrula(
                Path("models/sahte_model.pt"), kok=kok, calisan_imgsz=512)
        self.assertFalse(uyumlu, "imgsz 640 vs 512 — UYUMLU sayilmamali")
        self.assertEqual("IMGSZ ESLESMIYOR", detay["durum"])
        self.assertEqual(640, detay["beklenen_imgsz"])
        self.assertEqual(512, detay["calisan_imgsz"])

    def test_imgsz_AYNIYSA_uyumlu(self):
        """Ayirt edicilik: ayni defterde yalniz imgsz esitlenince UYUMLU."""
        with tempfile.TemporaryDirectory() as td:
            kok = _gecici_defter(td, imgsz=512)
            uyumlu, detay = R.model_kayit_dogrula(
                Path("models/sahte_model.pt"), kok=kok, calisan_imgsz=512)
        self.assertTrue(uyumlu, detay)
        self.assertEqual("eslesti", detay["durum"])

    # ── 3) ALAN YOKSA fail-closed (`path` ile AYNI mantik) ────────────────
    def test_defterde_imgsz_YOKSA_uyum_SAYILMAZ(self):
        with tempfile.TemporaryDirectory() as td:
            kok = _imgszsiz_defter(td)
            uyumlu, detay = R.model_kayit_dogrula(
                Path("models/sahte_model.pt"), kok=kok, calisan_imgsz=512)
        self.assertFalse(uyumlu, "yokluk UYUM SAYILMAZ")
        self.assertEqual("profilde `imgsz` yok", detay["durum"])

    # ── 4) VARSAYILAN DISINA CIKILINCA GORUNUR UYARI ──────────────────────
    def test_cikarim_boyu_OVERRIDE_uyarisi_STDERR_e_basiliyor(self):
        yakala = io.StringIO()
        with tempfile.TemporaryDirectory() as td:
            kok = _gecici_defter(td, imgsz=512)
            with mock.patch.object(sys, "stderr", yakala):
                deger = R.cikarim_boyu(896, kok=kok)
        cikti = yakala.getvalue()
        self.assertEqual(896, deger, "istenen deger DONMELI (karar cagiranin)")
        self.assertIn("UYARI", cikti)
        self.assertIn("VARSAYILAN DISINA", cikti)
        self.assertIn("512", cikti)
        self.assertIn("896", cikti)

    def test_cikarim_boyu_AYNI_degerde_SUSUYOR(self):
        """Ayirt edicilik: uyari her cagride basilmiyor, yalniz SAPMADA."""
        yakala = io.StringIO()
        with tempfile.TemporaryDirectory() as td:
            kok = _gecici_defter(td, imgsz=512)
            with mock.patch.object(sys, "stderr", yakala):
                deger = R.cikarim_boyu(512, kok=kok)
        self.assertEqual(512, deger)
        self.assertEqual("", yakala.getvalue())

    # ── 5) 🔴 MUTASYON KANITI ─────────────────────────────────────────────
    def test_MUTASYON_imgsz_kiyasi_kaldirilirsa_test_DUSER(self):
        """`imgsz` kiyasi cikarilirsa yukaridaki (2) testi GECER — yani o test
        gercekten BU alani siniyor, baska bir seyi degil (D-15/K-04).

        `model_kayit_dogrula` yalniz-ad kiyasina indirgenerek taklit edilir;
        uretim dosyasina DOKUNULMAZ.
        """
        def _yalniz_ad(model_yolu, kok=None, calisan_imgsz=None):
            veri = json.loads(
                (Path(kok) / "config" / "model_registry.json").read_text(
                    encoding="utf-8"))
            profil = veri["profiles"][veri["default_profile"]]
            return (Path(profil["path"]).name == Path(model_yolu).name,
                    {"durum": "eslesti"})

        with tempfile.TemporaryDirectory() as td:
            kok = _gecici_defter(td, imgsz=640)
            gercek_uyumlu, _d = R.model_kayit_dogrula(
                Path("models/sahte_model.pt"), kok=kok, calisan_imgsz=512)
            mutant_uyumlu, _d2 = _yalniz_ad(
                Path("models/sahte_model.pt"), kok=kok, calisan_imgsz=512)
        self.assertFalse(gercek_uyumlu, "gercek kod imgsz sapmasini KACIRDI")
        self.assertTrue(
            mutant_uyumlu,
            "MUTASYON BOS: imgsz kiyasi kaldirilinca da UYUMSUZ cikti — "
            "demek ki (2) testi imgsz'i degil BASKA bir seyi siniyor")

    # ── 6) load_model mesaji iki degeri de GOSTERIYOR ─────────────────────
    def test_load_model_hata_mesaji_IMGSZ_degerlerini_yaziyor(self):
        sahte = {"durum": "IMGSZ ESLESMIYOR", "beklenen_imgsz": 640,
                 "calisan_imgsz": 512, "kayit_defteri": "x", "profil": "y",
                 "beklenen": "z"}
        with mock.patch.object(R, "model_kayit_dogrula",
                               lambda *a, **k: (False, sahte)):
            with self.assertRaises(RuntimeError) as ctx:
                R.load_model(R.varsayilan_model_yolu())
        mesaj = str(ctx.exception)
        self.assertIn("profilin imgsz'i  : 640", mesaj)
        self.assertIn("calisan imgsz     : 512", mesaj)


if __name__ == "__main__":
    unittest.main()
