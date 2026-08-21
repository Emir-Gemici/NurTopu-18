"""T136 KAPISI: DJI hattinin IKI BAGLAYICI KISITI mekanik olarak ZORLANIR.

NEDEN: goruntu 30 Eylul'e dogru gelecek ve hattin O GUN ILK KEZ kosmasi kabul
edilemez. Iki kisit sozle degil KAPIYLA tutulur:

  KISIT 2 — DOGRULAMA OTURUMU CEKIMDE AYRILIR.
    Sonradan bolmek AYNI DAGILIMDIR ve T111'in "alan disi" duvarini YIKMAZ.
    Olculmustu (D-256 §5): egitim disi 11 kare "ayni saha ve ayni oturumdandi",
    bu yuzden KANIT degil ZAYIF DESTEK sayildi. Hat, ayrilmamis veri gelirse
    DURMALIDIR — ve `--prova` bu kapiyi ACMAZ, yalnizca kosumun ADAY
    URETEMEYECEGINI kabul eder.

  KISIT 3 — BOLUM ANAHTARI KAYNAK DUZEYINDE (D-233 · T127).
    Varyant duzeyinde bolmek val'i egitimin IKIZI yapar; olculmustu: val
    orneklerinin 55/55'inin (%100) kaynagi egitimde de vardi, yani o bilesenin
    val metrigi EZBERI olcuyordu.

⚠ Bu dosya MODEL YUKLEMEZ, VIDEO OKUMAZ, EGITIM KOSMAZ. Yalnizca hattin SAF
kapi fonksiyonlari sinanir; gercek `dji/` dizinine DOKUNULMAZ (gecici dizinler).
"""

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "dji_hatti_t136", KOK / "scripts" / "dji_hatti.py")
HAT = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(HAT)


def _kur(kok: Path, yerlesim: dict) -> Path:
    """{oturum|'': [dosya adlari]} -> gecici cekim agaci."""
    for oturum, adlar in yerlesim.items():
        d = kok / oturum if oturum else kok
        d.mkdir(parents=True, exist_ok=True)
        for ad in adlar:
            (d / ad).write_bytes(b"x")
    return kok


class OturumTespitiTests(unittest.TestCase):
    def test_kokteki_dosyalar_AYRILMAMIS_sayilir(self):
        with tempfile.TemporaryDirectory() as d:
            _kur(Path(d), {"": ["a.mp4", "b.jpg"]})
            o = HAT.oturumlari_bul(Path(d))
        self.assertEqual({"_AYRILMAMIS"}, set(o))
        self.assertEqual(2, len(o["_AYRILMAMIS"]))

    def test_alt_klasorler_OTURUM_olur(self):
        with tempfile.TemporaryDirectory() as d:
            _kur(Path(d), {"ucus1": ["a.mp4"], "DOGRULAMA": ["b.mp4", "c.jpg"]})
            o = HAT.oturumlari_bul(Path(d))
        self.assertEqual({"ucus1", "DOGRULAMA"}, set(o))
        self.assertEqual(2, len(o["DOGRULAMA"]))

    def test_alakasiz_uzantilar_SAYILMAZ(self):
        with tempfile.TemporaryDirectory() as d:
            _kur(Path(d), {"ucus1": ["a.mp4", "notlar.txt", "gpx.gpx"]})
            o = HAT.oturumlari_bul(Path(d))
        self.assertEqual(1, len(o["ucus1"]))


class OturumKapisiTests(unittest.TestCase):
    """KISIT 2 — ayrilmamis veri gelirse DURUR."""

    def test_DOGRULAMA_yoksa_zincir_DURUR(self):
        oturumlar = {"_AYRILMAMIS": [Path("a.mp4")] * 14}
        with self.assertRaises(SystemExit) as tuzak:
            HAT.oturum_kapisi(oturumlar, prova=False)
        self.assertIn("DOGRULAMA", str(tuzak.exception))

    def test_POZITIF_KONTROL_DOGRULAMA_varsa_GECER(self):
        """Kapi her seyi reddetmiyor — ayrilmis veri GECER."""
        oturumlar = {"ucus1": [Path("a.mp4")] * 10,
                     HAT.DOGRULAMA_ADI: [Path("b.mp4")] * 3}
        durum = HAT.oturum_kapisi(oturumlar, prova=False)
        self.assertTrue(durum["gecti"])
        self.assertFalse(durum["prova_mi"])
        self.assertEqual(3, durum["dogrulama_dosya"])
        self.assertEqual(10, durum["egitim_dosya"])

    def test_prova_kapiyi_ACMAZ_yalnizca_ADAY_URETEMEZ_der(self):
        """🔴 `--prova` bir MUAFIYET DEGILDIR: gecti=False kalir."""
        oturumlar = {"_AYRILMAMIS": [Path("a.mp4")] * 14}
        durum = HAT.oturum_kapisi(oturumlar, prova=True)
        self.assertFalse(durum["gecti"],
                         "--prova kapiyi ACIYOR — o zaman kapi yok demektir")
        self.assertTrue(durum["prova_mi"])
        self.assertEqual(0, durum["dogrulama_dosya"])

    def test_DOGRULAMA_varsa_prova_bayragi_kosum_ADAY_sayar(self):
        oturumlar = {"ucus1": [Path("a.mp4")], HAT.DOGRULAMA_ADI: [Path("b.mp4")]}
        durum = HAT.oturum_kapisi(oturumlar, prova=True)
        self.assertTrue(durum["gecti"])
        self.assertFalse(durum["prova_mi"])


class BolumKapisiTests(unittest.TestCase):
    """KISIT 3 — bolum anahtari KAYNAK duzeyinde (D-233)."""

    @staticmethod
    def _manifest(dizin: Path, kayitlar: list) -> Path:
        p = dizin / "manifest.json"
        p.write_text(json.dumps({"kayitlar": kayitlar}), encoding="utf-8")
        return p

    def test_POZITIF_KONTROL_temiz_bolum_GECER(self):
        with tempfile.TemporaryDirectory() as d:
            p = self._manifest(Path(d), [
                {"kaynak": "k1", "bolum": "train"},
                {"kaynak": "k1", "bolum": "train"},
                {"kaynak": "k2", "bolum": "val"},
                {"kaynak": "k2", "bolum": "val"},
            ])
            durum = HAT.bolum_kapisi(p)
        self.assertEqual(0, durum["kirli_val"])
        self.assertEqual(2, durum["val"])

    def test_kaynagi_egitimde_olan_val_zinciri_DURDURUR(self):
        with tempfile.TemporaryDirectory() as d:
            p = self._manifest(Path(d), [
                {"kaynak": "k1", "bolum": "train"},
                {"kaynak": "k1", "bolum": "val"},      # 🔴 AYNI kaynak
            ])
            with self.assertRaises(SystemExit) as tuzak:
                HAT.bolum_kapisi(p)
        self.assertIn("TEMIZ DEGIL", str(tuzak.exception))

    def test_duz_liste_bicimli_manifest_de_okunur(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "manifest.json"
            p.write_text(json.dumps([{"kaynak": "k1", "bolum": "train"},
                                     {"kaynak": "k2", "bolum": "val"}]),
                         encoding="utf-8")
            durum = HAT.bolum_kapisi(p)
        self.assertEqual(0, durum["kirli_val"])


class ParlaklikKapisiTests(unittest.TestCase):
    """🔴 PROVANIN BULDUGU KUSUR — ilk cekim AKSAM yapilmisti.

    Olculdu (2026-08-21): 569/569 karenin ortalama parlakligi 80'in ALTINDA
    (medyan 20,3); uretim modeli o karelerde zemini HIC gormedi (30 karede
    zemin orani medyani 0,0000, uretim hatti 30/30 REDDETTI). MODEL kusuru
    DEGIL, CEKIM KOSULU kusuru.

    ⚠ ESIK UYDURULMAZ: referans `data/raw_frames`ten TURETILIR (bugunku
    uretim modellerini ureten veri; olculdu min 118,7 · medyan 128,7).
    Kural ORTUSME sorusudur: yeni cekimin EN AYDINLIK karesi referansin EN
    KARANLIK karesine ulasamiyorsa hat DURUR.
    """

    @staticmethod
    def _kare_yaz(dizin: Path, n: int, deger: int):
        import numpy as np
        try:
            import cv2
        except ImportError:  # pragma: no cover
            raise unittest.SkipTest("cv2 yok")
        dizin.mkdir(parents=True, exist_ok=True)
        for i in range(n):
            cv2.imwrite(str(dizin / f"k{i}.jpg"),
                        np.full((180, 320), deger, np.uint8))
        return dizin

    def test_karanlik_cekim_zinciri_DURDURUR(self):
        with tempfile.TemporaryDirectory() as d:
            yeni = self._kare_yaz(Path(d) / "yeni", 5, 20)     # karanlik
            ref = self._kare_yaz(Path(d) / "ref", 5, 128)      # calisan veri
            with self.assertRaises(SystemExit) as tuzak:
                HAT.parlaklik_kapisi(yeni, ref, prova=False)
        self.assertIn("KARANLIK", str(tuzak.exception))

    def test_POZITIF_KONTROL_aydinlik_cekim_GECER(self):
        """Kapi her seyi reddetmiyor — referansla ortusen cekim GECER."""
        with tempfile.TemporaryDirectory() as d:
            yeni = self._kare_yaz(Path(d) / "yeni", 5, 130)
            ref = self._kare_yaz(Path(d) / "ref", 5, 128)
            durum = HAT.parlaklik_kapisi(yeni, ref, prova=False)
        self.assertEqual("ORTUSUYOR", durum["durum"])

    def test_prova_kipinde_PATLAMAZ_ama_ORTUSME_YOK_der(self):
        with tempfile.TemporaryDirectory() as d:
            yeni = self._kare_yaz(Path(d) / "yeni", 5, 20)
            ref = self._kare_yaz(Path(d) / "ref", 5, 128)
            durum = HAT.parlaklik_kapisi(yeni, ref, prova=True)
        self.assertEqual("ORTUSME_YOK", durum["durum"])

    def test_referans_okunamazsa_OLCULEMEDI_der_GECTI_demez(self):
        """Yokluk ne BASARI ne BASARISIZLIK (D-180 dersi)."""
        with tempfile.TemporaryDirectory() as d:
            yeni = self._kare_yaz(Path(d) / "yeni", 3, 20)
            bos = Path(d) / "bos"; bos.mkdir()
            durum = HAT.parlaklik_kapisi(yeni, bos, prova=False)
        self.assertEqual("OLCULEMEDI", durum["durum"])

    def test_esik_KODA_GOMULU_DEGIL(self):
        """Referans dizinden turetiliyor mu — yoksa uydurma esik olurdu."""
        kaynak = (KOK / "scripts" / "dji_hatti.py").read_text(encoding="utf-8")
        govde = kaynak.split("def parlaklik_kapisi", 1)[1].split("def _medyan")[0]
        self.assertIn("ref_min", govde)
        self.assertNotIn("< 80", govde)
        self.assertNotIn("< 100", govde)


class KahinACIKCA_VerilirTests(unittest.TestCase):
    """🔴 Etiket kahini SESSIZCE secilemez.

    D-210'un kusuru tam buradaydi: uretec BILINMEYENI zemin ilan ediyordu ve
    kimse hangi kahinin hangi esikte kullanildigini sorgulamamisti. Hat, kahini
    ZORUNLU ve ACIK bir arguman yapar; varsayilan YOKTUR.
    """

    def test_kahin_argumani_ZORUNLU(self):
        kaynak = (KOK / "scripts" / "dji_hatti.py").read_text(encoding="utf-8")
        self.assertIn('"--kahin"', kaynak)
        blok = kaynak.split('"--kahin"', 1)[1].split("ap.add_argument")[0]
        self.assertIn("required=True", blok,
                      "kahin argumani zorunlu DEGIL — sessizce varsayilan "
                      "secilebilir, D-210 sinifi")
        self.assertNotIn("default=", blok,
                         "kahin argumaninin VARSAYILANI var — acik secim degil")


if __name__ == "__main__":
    unittest.main(verbosity=2)
