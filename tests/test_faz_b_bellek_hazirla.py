"""SAHA_HAZIRLIK_PLANI §1.10 — saha belleği hazırlayıcının kapıları.

NEDEN: 5 Eylül'de Jetson kutudan çıkacak ve internet olmayabilir; belleğe
konacak bir parça unutulursa sahada telafisi yok. Betik toplamayı
mekanikleştirir; bu testler onun **eksik olanı gördüğünü** ve **sessizce
"hazır" demediğini** kilitler.

Kilitler:
  B1  zorunlu parça eksikken çıkış 3 ve EKSIKLER.txt (sessiz başarı yok)
  B2  `--eksige-ragmen` geçer ama MANIFEST bunu YAZAR
  B3  tam kaynakta kopya birebir (sha256) ve MANIFEST her dosyayı listeler
  B4  `--kuru` HİÇBİR ŞEY kopyalamaz ama eksikleri aynı şekilde raporlar
  B5  kurallar gerçek repo yollarına bakar (kural listesi bayat kalamaz)
  B6  insanın koyacağı parçalar (JetPack imajı, GPU wheel) raporda görünür
"""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "scripts"))

import bellek_hazirla as bh  # noqa: E402

PY = sys.executable
BETIK = KOK / "scripts" / "bellek_hazirla.py"


def _kos(*ek, kok=None):
    r = subprocess.run([PY, "-B", str(BETIK), *ek], cwd=kok or KOK,
                       capture_output=True, text=True, timeout=600,
                       encoding="utf-8", errors="replace")
    return r.returncode, (r.stdout or "") + (r.stderr or "")


class SahteKok(unittest.TestCase):
    """Gerçek dosya sistemi, sahte kök: zorunlu parça bilerek eksiltilir."""

    def setUp(self):
        self.d = Path(tempfile.mkdtemp(prefix="navitas_bellek_"))
        self.kok = self.d / "depo"
        (self.kok / "jetson_paket").mkdir(parents=True)
        (self.kok / "jetson_paket" / "a.py").write_text("x = 1\n", encoding="utf-8")
        (self.kok / "jetson_paket" / "JETSON_NANO_KURULUM.md").write_text(
            "kurulum\n", encoding="utf-8")
        (self.kok / "jetson_paket" / "JETSON_BASLAT.md").write_text(
            "baslat\n", encoding="utf-8")
        (self.kok / "jetson_paket" / "GUN1_KONTROL_LISTESI.md").write_text(
            "gun1\n", encoding="utf-8")
        (self.kok / "config" / "pixhawk").mkdir(parents=True)
        (self.kok / "config" / "pixhawk" / "arducopter_fda.param").write_text(
            "SYSID_THISMAV,1\n", encoding="utf-8")
        (self.kok / "config" / "pixhawk" / "README.md").write_text(
            "oku\n", encoding="utf-8")
        for ad in ("SAHA_HAZIRLIK_PLANI_20260903.md", "FAZ_B_GUN_PLANI.md",
                   "SAHA_RUNBOOK.md"):
            (self.kok / ad).write_text(ad + "\n", encoding="utf-8")
        # Kural listesindeki HER zorunlu parça fikstürde de bulunmalı; aksi
        # halde testler kendi eksiklerini kusur sanır (B5 gerçek depoyu ayrıca
        # denetler). Yeni kural eklendiğinde burası da büyür — bilerek.
        for gore, _alt, zorunlu, _n in bh.KOPYA_KURALLARI:
            hedef = self.kok / gore
            if not zorunlu or hedef.exists():
                continue
            hedef.parent.mkdir(parents=True, exist_ok=True)
            hedef.write_text(f"{gore} (fikstur)\n", encoding="utf-8")
        self.eski_kok = bh.KOK
        bh.KOK = self.kok

    def tearDown(self):
        bh.KOK = self.eski_kok
        shutil.rmtree(self.d, ignore_errors=True)

    def test_B3_tam_kaynakta_kopya_birebir_ve_MANIFEST_tam(self):
        hedef = self.d / "bellek"
        self.assertEqual(0, bh.hazirla(hedef, kuru=False, eksige_ragmen=False))
        manifest = (hedef / "MANIFEST.txt").read_text(encoding="utf-8")
        kopyalar = [p for p in hedef.rglob("*")
                    if p.is_file() and p.name != "MANIFEST.txt"]
        self.assertTrue(kopyalar)
        for p in kopyalar:
            self.assertIn(bh._sha256(p), manifest,
                          f"MANIFEST {p.name} icin sha256 tasimiyor")
        self.assertEqual(
            (self.kok / "config" / "pixhawk" / "arducopter_fda.param").read_bytes(),
            (hedef / "config_pixhawk" / "arducopter_fda.param").read_bytes())
        self.assertIn("eksik zorunlu: 0", manifest)

    def test_B1_zorunlu_eksikte_cikis_3_ve_EKSIKLER_dosyasi(self):
        (self.kok / "SAHA_RUNBOOK.md").unlink()
        hedef = self.d / "bellek_eksik"
        self.assertEqual(3, bh.hazirla(hedef, kuru=False, eksige_ragmen=False))
        eksikler = (hedef / "EKSIKLER.txt").read_text(encoding="utf-8")
        self.assertIn("SAHA_RUNBOOK.md", eksikler)
        self.assertFalse((hedef / "MANIFEST.txt").exists(),
                         "eksikken MANIFEST yazilmamali (sessiz 'hazir' yok)")

    def test_B2_eksige_ragmen_gecer_ama_MANIFEST_YAZAR(self):
        (self.kok / "FAZ_B_GUN_PLANI.md").unlink()
        hedef = self.d / "bellek_bilerek"
        self.assertEqual(0, bh.hazirla(hedef, kuru=False, eksige_ragmen=True))
        manifest = (hedef / "MANIFEST.txt").read_text(encoding="utf-8")
        self.assertIn("BİLEREK GEÇİLDİ", manifest)
        self.assertNotIn("eksik zorunlu: 0", manifest)

    def test_B4_kuru_HICBIR_SEY_kopyalamaz(self):
        hedef = self.d / "bellek_kuru"
        self.assertEqual(0, bh.hazirla(hedef, kuru=True, eksige_ragmen=False))
        self.assertFalse(hedef.exists(), "--kuru dizin bile olusturmamali")
        (self.kok / "SAHA_RUNBOOK.md").unlink()
        self.assertEqual(3, bh.hazirla(hedef, kuru=True, eksige_ragmen=False),
                         "--kuru eksikleri ayni sekilde raporlamali")


class GercekDepo(unittest.TestCase):
    def test_B5_kurallar_GERCEK_repo_yollarina_bakiyor(self):
        """Kural listesi bayatlarsa (yol yeniden adlandırılırsa) burada düşer."""
        eksik = [g for g, _alt, zorunlu, _n in bh.KOPYA_KURALLARI
                 if zorunlu and not (KOK / g).exists()]
        self.assertEqual([], eksik, f"kural listesi bayat: {eksik}")

    def test_B6_insan_parcalari_raporda_GORUNUR(self):
        kod, cikti = _kos("--kuru")
        self.assertIn(kod, (0, 3), cikti[-800:])
        self.assertIn("İNSANIN KOYACAĞI", cikti)
        self.assertIn("JetPack", cikti)
        self.assertIn("GPU torch wheel", cikti)
        self.assertIn("jetson_paket -> jetson_paket/", cikti)

    def test_B7_wheels_istege_bagli_ama_RAPORLANIR(self):
        """Tekerlekler yoksa betik durmaz, ama sessiz de kalmaz."""
        kural = [k for k in bh.KOPYA_KURALLARI if k[0] == "wheels"]
        self.assertEqual(1, len(kural))
        self.assertFalse(kural[0][2], "wheels zorunlu degil (Nano'da pip de kurulabilir)")
        kod, cikti = _kos("--kuru")
        self.assertTrue("wheels" in cikti, cikti[-400:])


if __name__ == "__main__":
    unittest.main()
