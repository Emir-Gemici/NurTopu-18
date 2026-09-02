"""FAZ B — SURUM DONDURMA KAPISI (scripts/surum_dondur.py · sartname SS6.1).

NEDEN: Yarisan yazilim beyanla BIREBIR ayni olmali, muhur sonrasi mudahale
yok. Bu dosya IKI seyi kilitler:

  (A) KAPI — `config/DONDURMA_KUNYESI.json` VARSA bugunku paket / model /
      defter ozetleri kunyeyle birebir olmali; degilse test DUSER ve fark
      listesi ciktida durur (muhur ihlali GORUNUR). Kunye YOKSA test GECER
      ama bunu ciktisinda "DONDURULMADI (henuz)" diye SOYLER — skip degil,
      gorunur not: dondurma ani kullanici karari (plan ~18 Eylul), kapinin
      sessizce yesil durmasi degil.

  (B) MEKANIZMA — gecici dizinde SAHTE paket + sahte model + sahte defter +
      GERCEK gecici git deposu ile betigin CLI sozlesmesi:
        --dondur -> 0 ve kunye alanlari tam
        --dogrula -> 0 (birebir); bir dosya degisince/silinince -> 1 ve
                     fark listesinde ADIYLA
        kirli agac -> --dondur 2 (kunye YAZILMAZ); --kirli-bilerek -> 0 ve
                     kirlilik kunyede
        model/defter tutarsiz -> 2; paket bayat -> 2
        kunye yok -> --dogrula/--goster 3 (ayirt edilebilir)
      Mock yok: git gercek subprocess, ozetler gercek hashlib.
"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
for _y in (KOK / "scripts", KOK / "codes"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

import surum_dondur as sd  # noqa: E402

BETIK = KOK / "scripts" / "surum_dondur.py"
ETIKET = "sahte-v0-yarisma"
TARIH = "2026-09-18"
SUREC_TAVAN_S = 120
GIT_KIMLIK = ("-c", "user.name=test", "-c", "user.email=test@navitas.local")


def _kos(*args, kok=None):
    """Betigi GERCEK yorumlayiciyla ayri surecte kos -> (exit, cikti)."""
    komut = [sys.executable, str(BETIK)]
    if kok is not None:
        komut += ["--kok", str(kok)]
    komut += list(args)
    r = subprocess.run(komut, capture_output=True, text=True, timeout=SUREC_TAVAN_S)
    return r.returncode, (r.stdout + r.stderr)


def _git(kok, *args):
    r = subprocess.run(["git", *GIT_KIMLIK, *args], cwd=str(kok), capture_output=True,
                       text=True, timeout=SUREC_TAVAN_S)
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr}")
    return r.stdout


# ── (A) KAPI ────────────────────────────────────────────────────────────────

class MuhurKapisi(unittest.TestCase):
    """Kunye varsa paket kunyeyle birebir; yoksa GORUNUR not ile gecer."""

    def test_KUNYE_VARSA_PAKET_MODEL_DEFTER_KUNYEYLE_BIREBIR(self):
        kunye = sd.kunye_yolu(KOK)
        if not kunye.is_file():
            not_ = (f"[SURUM_DONDURMA] DONDURULMADI (henuz): {kunye.relative_to(KOK)} yok - "
                    "muhur basilinca bu kapi paket/model/defter ozetlerini kunyeyle kiyaslar")
            print(not_, file=sys.stderr)
            print(not_)
            return
        kod, cikti = _kos("--dogrula")
        self.assertEqual(
            kod, sd.CIKIS_TAMAM,
            "MUHUR IHLALI: kunye var ama bugunku dosyalar kunyeden sapiyor "
            f"(exit {kod}). Sartname SS6.1 - muhur sonrasi mudahale yok.\n{cikti}")
        self.assertIn("BIREBIR", cikti)

    def test_CIKIS_KODLARI_AYIRT_EDILEBILIR(self):
        kodlar = (sd.CIKIS_TAMAM, sd.CIKIS_FARK, sd.CIKIS_RED, sd.CIKIS_DONDURULMADI)
        self.assertEqual(len(set(kodlar)), 4, kodlar)
        self.assertEqual(sd.CIKIS_TAMAM, 0)

    def test_PAKET_LISTESI_KOPYALAR_ILE_AYNI(self):
        """Kunyenin paket listesi jetson_paket_hazirla.KOPYALAR'dan TURETILIR."""
        from jetson_paket_hazirla import KOPYALAR
        self.assertEqual(len(sd.PAKET_ESLEMESI), len(KOPYALAR))
        hedefler = {h for _, h in sd.PAKET_ESLEMESI}
        self.assertIn("jetson_paket/kod/rpi_inference.py", hedefler)
        self.assertIn("jetson_paket/config/model_registry.json", hedefler)
        self.assertIn("jetson_paket/kod/iha_komut_alici.py", hedefler)


# ── (B) MEKANIZMA — sahte kok ───────────────────────────────────────────────

class SahteKok(unittest.TestCase):
    """Gecici git deposunda sahte paket ile CLI sozlesmesi."""

    def setUp(self):
        self.kok = Path(tempfile.mkdtemp(prefix="dondurma_")).resolve()
        self.addCleanup(shutil.rmtree, self.kok, ignore_errors=True)
        # sahte model + defter (sha256 = diskteki gercek ozet)
        self.model = self.kok / "models" / "sahte_v0.pt"
        self.model.parent.mkdir(parents=True)
        self.model.write_bytes(b"sahte model agirligi\n" * 200)
        self.defter = self.kok / sd.DEFTER_GORELI
        self.defter.parent.mkdir(parents=True)
        self._defter_yaz(sd.sha256_hesapla(self.model))
        # sahte paket: KOPYALAR'in her (kaynak, hedef) cifti — hedef = kaynagin kopyasi
        for kaynak_g, hedef_g in sd.PAKET_ESLEMESI:
            kaynak = self.kok / kaynak_g
            if not kaynak.is_file():
                kaynak.parent.mkdir(parents=True, exist_ok=True)
                kaynak.write_text(f"# sahte {kaynak_g}\n", encoding="utf-8")
            hedef = self.kok / hedef_g
            hedef.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(kaynak, hedef)
        # gercek gecici git deposu, temiz agac
        _git(self.kok, "init", "-q")
        _git(self.kok, "config", "core.autocrlf", "false")
        self._commit("sahte kok")

    def _defter_yaz(self, ozet):
        veri = {"schema_version": 1, "default_profile": "competition",
                "profiles": {"competition": {"model_id": "sahte-seg-v0-512",
                                             "path": "models/sahte_v0.pt",
                                             "backend": "pytorch", "imgsz": 512,
                                             "sha256": ozet}}}
        self.defter.write_text(json.dumps(veri, indent=1) + "\n", encoding="utf-8")

    def _commit(self, mesaj):
        _git(self.kok, "add", "-A")
        _git(self.kok, "commit", "-q", "-m", mesaj)

    def _dondur(self, *ek):
        return _kos("--dondur", "--etiket", ETIKET, "--tarih", TARIH, *ek, kok=self.kok)

    def _kunye(self):
        return json.loads(sd.kunye_yolu(self.kok).read_text(encoding="utf-8"))

    def _paket_hedefi(self, ad="rpi_inference.py"):
        return self.kok / "jetson_paket" / "kod" / ad

    # ── dondur ──
    def test_DONDUR_temiz_agacta_kunye_yazar_ve_alanlar_tam(self):
        kod, cikti = self._dondur()
        self.assertEqual(kod, sd.CIKIS_TAMAM, cikti)
        self.assertIn("DONDURULDU", cikti)
        k = self._kunye()
        for alan in sd.KUNYE_ZORUNLU_ALANLAR:
            self.assertIn(alan, k, alan)
        self.assertEqual(k["etiket"], ETIKET)
        self.assertEqual(k["tarih"], TARIH)
        self.assertEqual(k["git_head"], _git(self.kok, "rev-parse", "HEAD").strip())
        self.assertFalse(k["git_kirli"])
        self.assertFalse(k["kirli_bilerek"])
        self.assertEqual(k["model"]["yol"], "models/sahte_v0.pt")
        self.assertEqual(k["model"]["sha256"], sd.sha256_hesapla(self.model))
        self.assertEqual(k["registry_sha256"], sd.sha256_hesapla(self.defter))
        self.assertEqual(set(k["paket"]), {h for _, h in sd.PAKET_ESLEMESI})
        for hedef_g, ozet in k["paket"].items():
            self.assertEqual(ozet, sd.sha256_hesapla(self.kok / hedef_g), hedef_g)
        self.assertIn("--dogrula", k["test_komutu"])
        self.assertNotIn("onceki_muhur", k)

    def test_DONDUR_kirli_agac_REDDEDILIR_kunye_yazilmaz(self):
        (self.kok / "yeni_dosya.txt").write_text("commit edilmedi\n", encoding="utf-8")
        kod, cikti = self._dondur()
        self.assertEqual(kod, sd.CIKIS_RED, cikti)
        self.assertIn("KIRLI", cikti)
        self.assertIn("yeni_dosya.txt", cikti)
        self.assertFalse(sd.kunye_yolu(self.kok).exists(), "red edildi ama kunye yazildi")

    def test_DONDUR_kirli_bilerek_gecer_ve_kirlilik_kunyede(self):
        (self.kok / "yeni_dosya.txt").write_text("commit edilmedi\n", encoding="utf-8")
        kod, cikti = self._dondur("--kirli-bilerek")
        self.assertEqual(kod, sd.CIKIS_TAMAM, cikti)
        self.assertIn("KIRLIYKEN", cikti)
        k = self._kunye()
        self.assertTrue(k["git_kirli"])
        self.assertTrue(k["kirli_bilerek"])
        self.assertTrue(any("yeni_dosya.txt" in s for s in k["git_durum"]), k["git_durum"])

    def test_DONDUR_model_defterle_uyusmazsa_RED(self):
        self.model.write_bytes(b"baska agirlik\n" * 100)   # defter sha256 bayat kaldi
        self._commit("model degisti, defter degismedi")
        kod, cikti = self._dondur()
        self.assertEqual(kod, sd.CIKIS_RED, cikti)
        self.assertIn("UYUSMUYOR", cikti)
        self.assertFalse(sd.kunye_yolu(self.kok).exists())

    def test_DONDUR_model_yoksa_RED(self):
        self.model.unlink()
        self._commit("model silindi")
        kod, cikti = self._dondur()
        self.assertEqual(kod, sd.CIKIS_RED, cikti)
        self.assertIn("model artefakti yok", cikti)

    def test_DONDUR_paket_kaynaktan_bayatsa_RED(self):
        (self.kok / "codes" / "rpi_inference.py").write_text("# yeni kaynak\n", encoding="utf-8")
        self._commit("kaynak degisti, paket tazelenmedi")
        kod, cikti = self._dondur()
        self.assertEqual(kod, sd.CIKIS_RED, cikti)
        self.assertIn("BAYAT", cikti)
        self.assertIn("jetson_paket/kod/rpi_inference.py", cikti)
        self.assertIn("jetson_paket_hazirla", cikti)

    def test_DONDUR_paket_hedefi_eksikse_RED(self):
        self._paket_hedefi("link.py").unlink()
        self._commit("paket dosyasi silindi")
        kod, cikti = self._dondur()
        self.assertEqual(kod, sd.CIKIS_RED, cikti)
        self.assertIn("EKSIK", cikti)
        self.assertIn("jetson_paket/kod/link.py", cikti)

    def test_DONDUR_bozuk_tarih_RED(self):
        kod, cikti = _kos("--dondur", "--etiket", ETIKET, "--tarih", "18.09.2026", kok=self.kok)
        self.assertEqual(kod, sd.CIKIS_RED, cikti)
        self.assertFalse(sd.kunye_yolu(self.kok).exists())

    def test_DONDUR_yeniden_muhurleme_oncekini_kunyeye_yazar(self):
        self.assertEqual(self._dondur()[0], sd.CIKIS_TAMAM)
        ilk_head = self._kunye()["git_head"]
        self._commit("kunye commit")           # kunye tracked -> agac temiz
        kod, cikti = _kos("--dondur", "--etiket", "ikinci", "--tarih", "2026-09-19", kok=self.kok)
        self.assertEqual(kod, sd.CIKIS_TAMAM, cikti)
        self.assertIn("onceki muhur DEGISTIRILDI", cikti)
        k = self._kunye()
        self.assertEqual(k["etiket"], "ikinci")
        self.assertEqual(k["onceki_muhur"], {"etiket": ETIKET, "tarih": TARIH,
                                             "git_head": ilk_head})

    # ── dogrula ──
    def test_DOGRULA_kunye_yoksa_DONDURULMADI_exit_3(self):
        kod, cikti = _kos("--dogrula", kok=self.kok)
        self.assertEqual(kod, sd.CIKIS_DONDURULMADI, cikti)
        self.assertIn("DONDURULMADI", cikti)
        kod, cikti = _kos("--goster", kok=self.kok)
        self.assertEqual(kod, sd.CIKIS_DONDURULMADI, cikti)

    def test_DOGRULA_dondurmadan_hemen_sonra_BIREBIR_exit_0(self):
        self.assertEqual(self._dondur()[0], sd.CIKIS_TAMAM)
        kod, cikti = _kos("--dogrula", kok=self.kok)
        self.assertEqual(kod, sd.CIKIS_TAMAM, cikti)
        self.assertIn("BIREBIR", cikti)
        self.assertIn(f"{2 + len(sd.PAKET_ESLEMESI)} dosya", cikti)

    def test_DOGRULA_paket_dosyasi_degisince_exit_1_ve_listede(self):
        self.assertEqual(self._dondur()[0], sd.CIKIS_TAMAM)
        hedef = self._paket_hedefi()
        hedef.write_text(hedef.read_text(encoding="utf-8") + "# muhur sonrasi\n",
                         encoding="utf-8")
        kod, cikti = _kos("--dogrula", kok=self.kok)
        self.assertEqual(kod, sd.CIKIS_FARK, cikti)
        self.assertIn("MUHUR IHLALI", cikti)
        self.assertIn(sd.DURUM_FARKLI, cikti)
        self.assertIn("jetson_paket/kod/rpi_inference.py", cikti)
        self.assertIn("1/", cikti)                       # tek dosya sapiyor

    def test_DOGRULA_paket_dosyasi_silinince_exit_1_YOK(self):
        self.assertEqual(self._dondur()[0], sd.CIKIS_TAMAM)
        self._paket_hedefi("protocol.py").unlink()
        kod, cikti = _kos("--dogrula", kok=self.kok)
        self.assertEqual(kod, sd.CIKIS_FARK, cikti)
        self.assertIn(sd.DURUM_YOK, cikti)
        self.assertIn("jetson_paket/kod/protocol.py", cikti)

    def test_DOGRULA_model_degisince_exit_1(self):
        self.assertEqual(self._dondur()[0], sd.CIKIS_TAMAM)
        self.model.write_bytes(b"muhur sonrasi agirlik\n" * 100)
        kod, cikti = _kos("--dogrula", kok=self.kok)
        self.assertEqual(kod, sd.CIKIS_FARK, cikti)
        self.assertIn("models/sahte_v0.pt", cikti)
        self.assertIn("model", cikti)

    def test_DOGRULA_defter_degisince_exit_1(self):
        self.assertEqual(self._dondur()[0], sd.CIKIS_TAMAM)
        # Once capa: AYNI icerigi yeniden yazmak fark uretmez (kapi mtime'a
        # degil ozete bakiyor); sonra anlamli bir alan degisince DUSMELI.
        self._defter_yaz(sd.sha256_hesapla(self.model))
        self.assertEqual(_kos("--dogrula", kok=self.kok)[0], sd.CIKIS_TAMAM)
        veri = json.loads(self.defter.read_text(encoding="utf-8"))
        veri["profiles"]["competition"]["imgsz"] = 640
        self.defter.write_text(json.dumps(veri, indent=1) + "\n", encoding="utf-8")
        kod, cikti = _kos("--dogrula", kok=self.kok)
        self.assertEqual(kod, sd.CIKIS_FARK, cikti)
        self.assertIn("config/model_registry.json", cikti)
        self.assertIn("defter", cikti)

    def test_DOGRULA_bozuk_kunye_exit_1(self):
        sd.kunye_yolu(self.kok).parent.mkdir(parents=True, exist_ok=True)
        sd.kunye_yolu(self.kok).write_text("{bozuk", encoding="utf-8")
        kod, cikti = _kos("--dogrula", kok=self.kok)
        self.assertEqual(kod, sd.CIKIS_FARK, cikti)
        self.assertIn("bozuk", cikti)

    def test_DOGRULA_git_head_farki_dogrulamayi_DUSURMEZ(self):
        """Kunye commit edilince HEAD degisir; olcut dosya ozetleridir."""
        self.assertEqual(self._dondur()[0], sd.CIKIS_TAMAM)
        self._commit("kunye commit")
        kod, cikti = _kos("--dogrula", kok=self.kok)
        self.assertEqual(kod, sd.CIKIS_TAMAM, cikti)
        self.assertIn("bilgi", cikti)

    # ── goster ──
    def test_GOSTER_kunyeyi_json_olarak_basar(self):
        self.assertEqual(self._dondur()[0], sd.CIKIS_TAMAM)
        kod, cikti = _kos("--goster", kok=self.kok)
        self.assertEqual(kod, sd.CIKIS_TAMAM, cikti)
        veri = json.loads(cikti)
        self.assertEqual(veri["etiket"], ETIKET)
        self.assertEqual(veri["model"]["sha256"], sd.sha256_hesapla(self.model))


if __name__ == "__main__":
    unittest.main()
