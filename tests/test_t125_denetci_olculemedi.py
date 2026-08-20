"""T125 KAPISI: kabul denetcisi OLCEMEDIGINI 'DUSTU' SAYAMAZ.

Kusur (D-225 §5, mimar olctu): `65_kabul_denetcisi.py` KADRAJ'i kendi
konumundan turetiyordu; ayna kopyasinda dizin yok -> alt betik bos donuyor ->
`{}` -> K1..K4 "DUSTU" -> "VERDIKT: URETIME ALINMAZ". GIRDI YOKLUGU dort kapi
BASARISIZLIGI olarak satildi. Ayrica registry'deki `kabul_kumesi` tek-kaynak
alani hic okunmuyordu (madde 16 / "iki kopya, biri zorlanmiyor").

Bu kapi DAVRANISSALDIR (mutasyon degil senaryo — mimar emri):
  · girdi kumesi bulunamayan baglamda denetci verdikt URETMEZ (acik hata) —
    "DUSTU" demez, hicbir kapi sessizce "GECTI" olmaz;
  · alt betik JSON'u yoksa / payda sifirsa K1..K4 = OLCULEMEDI;
  · POZITIF KONTROL: gecerli sayilarla K1..K4 eskisi gibi GECTI/DUSTU uretir
    (esikler `ESIK` sozlugunden turetilir — ciplak sayi yok; vakumsuz kapi,
    D-15/K-04).
GPU'suz tam-zincir pozitif kontrol MUMKUN DEGIL (gercek kume 260 karelik
cikarim ister); o kontrol T125 dogrulama kosumuyla (iki baglam, ayni agirlik)
REVIEW_LOG kaydina yapistirilir.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
BETIK = KOK / "scripts" / "olcum" / "65_kabul_denetcisi.py"

for _p in (KOK / "scripts" / "olcum", KOK / "codes"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

spec = importlib.util.spec_from_file_location("kabul_denetcisi_t125", BETIK)
K65 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(K65)

OLC = ("K1", "K2", "K3", "K4")


def _saglam_girdi():
    """ESIK'ten TURETILMIS, dort kapiyi da GECTI yapan girdi (ciplak sayi yok)."""
    e = K65.ESIK
    r = int(e["K1_rota_min"])                    # tam esik: >= saglanir
    return {"n": r + 1, "rota_uretilen": r,
            "basan": int(r * e["K2_basma_maks"]),     # <= esik
            "agir": int(r * e["K3_agir_maks"]),
            "arena_disi": int(r * e["K4_arena_disi_maks"])}


class K14UcDurumTests(unittest.TestCase):
    def test_girdi_yoklugu_dustu_degil_olculemedi(self):
        durum, _ = K65.k14_durumlari(None)
        for k in OLC:
            self.assertEqual(durum[k], "OLCULEMEDI",
                             f"{k}: girdi yoklugu '{durum[k]}' sayildi")

    def test_payda_sifir_olculemedi(self):
        durum, _ = K65.k14_durumlari({"n": 0})
        self.assertEqual([durum[k] for k in OLC], ["OLCULEMEDI"] * 4)

    def test_rota_sifir_k1_olculdu_dustu_digerleri_olculemedi(self):
        """n>0 ama rota 0: K1 OLCULDU ve dustu; K2..K4'un paydasi yok."""
        d = dict(_saglam_girdi(), rota_uretilen=0, basan=0, agir=0, arena_disi=0)
        durum, _ = K65.k14_durumlari(d)
        self.assertEqual(durum["K1"], "DUSTU")
        for k in ("K2", "K3", "K4"):
            self.assertEqual(durum[k], "OLCULEMEDI")

    def test_pozitif_kontrol_saglam_girdi_gecti(self):
        durum, sayilar = K65.k14_durumlari(_saglam_girdi())
        self.assertEqual([durum[k] for k in OLC], ["GECTI"] * 4, durum)
        self.assertEqual(sayilar["rota_uretilen"], int(K65.ESIK["K1_rota_min"]))

    def test_pozitif_kontrol_esik_alti_dustu(self):
        """Olculdu-ve-altinda hala DUSTU'dur — esik davranisi DEGISMEDI."""
        d = _saglam_girdi()
        d["rota_uretilen"] = int(K65.ESIK["K1_rota_min"]) - 1
        d["basan"] = d["rota_uretilen"]          # oran 1.0 > K2 esigi
        durum, _ = K65.k14_durumlari(d)
        self.assertEqual(durum["K1"], "DUSTU")
        self.assertEqual(durum["K2"], "DUSTU")

    def test_olculemedi_gecti_degildir(self):
        """Verdikt eslemesi `durum == 'GECTI'` uzerinden — OLCULEMEDI bloklar."""
        durum, _ = K65.k14_durumlari(None)
        self.assertTrue(all(durum[k] != "GECTI" for k in OLC))


class KabulKumesiTekKaynakTests(unittest.TestCase):
    def _kok(self, icerik):
        tmp = Path(tempfile.mkdtemp(prefix="t125_"))
        (tmp / "config").mkdir()
        (tmp / "config" / "model_registry.json").write_text(
            json.dumps(icerik), encoding="utf-8")
        return tmp

    def test_alan_yoksa_acik_hata(self):
        kok = self._kok({"default_profile": "competition",
                         "profiles": {"competition": {}}})
        with self.assertRaises(RuntimeError):
            K65.kabul_kumesi_yolu(kok)

    def test_dizin_yoksa_acik_hata(self):
        kok = self._kok({"default_profile": "competition",
                         "profiles": {"competition": {
                             "kabul_kumesi": str(kok_yok := Path(
                                 tempfile.gettempdir()) / "t125_yok_dizin")}}})
        self.assertFalse(kok_yok.exists())
        with self.assertRaises(RuntimeError):
            K65.kabul_kumesi_yolu(kok)

    def test_pozitif_kontrol_gercek_dizin_doner(self):
        hedef = Path(tempfile.mkdtemp(prefix="t125_kume_"))
        kok = self._kok({"default_profile": "competition",
                         "profiles": {"competition": {
                             "kabul_kumesi": str(hedef)}}})
        self.assertEqual(K65.kabul_kumesi_yolu(kok), hedef)

    def test_uretim_registrysi_gercek_kumeye_isaret_ediyor(self):
        """Tek kaynak SAHICI: bugunku registry'nin alani gercek bir dizindir."""
        yol = K65.kabul_kumesi_yolu()
        self.assertTrue(yol.is_dir())


class SenaryoTests(unittest.TestCase):
    def test_kume_yokken_verdikt_uretilmez(self):
        """Mimarin senaryosu: girdi kumesi bulunamayan baglamda denetci
        'DUSTU' DEMEZ — acik hatayla durur, VERDIKT basilmaz."""
        tmp = Path(tempfile.mkdtemp(prefix="t125_senaryo_"))
        (tmp / "config").mkdir()
        (tmp / "config" / "model_registry.json").write_text(json.dumps(
            {"default_profile": "competition",
             "profiles": {"competition": {
                 "kabul_kumesi": str(tmp / "olmayan_kume")}}}),
            encoding="utf-8")
        p = subprocess.run(
            [sys.executable, "-B", str(BETIK),
             "--model", str(tmp / "olmayan_model.pt"),
             "--ad", "t125_senaryo", "--kok", str(tmp)],
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertNotEqual(p.returncode, 0, "denetci acik hatayla DURMADI")
        self.assertNotIn("VERDIKT", p.stdout, "bos kumeyle verdikt uretildi")
        self.assertNotIn("DUSTU", p.stdout, "olculemeyen DUSTU diye basildi")
        self.assertNotIn("GECTI", p.stdout, "olculemeyen sessizce GECTI oldu")
        self.assertIn("kabul kumesi dizini yok", p.stdout + p.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
