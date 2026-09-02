"""FAZ B — SURUM DONDURMA KAPISI v2 (scripts/surum_dondur.py · sartname SS6.1 · D-405).

NEDEN: Yarisan yazilim beyanla BIREBIR ayni olmali, muhur sonrasi mudahale
yok. Bu dosya IKI seyi kilitler:

  (A) KAPI — `config/DONDURMA_KUNYESI.json` VARSA bugunku kapsam kunyeyle
      birebir ve kunye git'e bagli olmali; degilse test DUSER ve fark listesi
      ciktida durur (muhur ihlali GORUNUR). Kunye YOKSA test GECER ama bunu
      ciktisinda "DONDURULMADI (henuz)" diye SOYLER — skip degil, gorunur not.
      Ayrica betikteki kapsam sabitleri MIMAR LISTESIYLE (D-405 §2) birebir ve
      bugun diskte var olmali (liste bayatlarsa sessizce "YOK" yazilmasin).

  (B) MEKANIZMA — gecici dizinde SAHTE paket + sahte model/onnx + sahte defter +
      GERCEK gecici git deposu ile betigin CLI sozlesmesi (mock yok: git gercek
      subprocess, ozetler gercek hashlib):
        S6  ozet icerik-kanonik: CRLF/LF ayni ozet (metin), ikili ham; LF
            deposunun kunyesi autocrlf=true KLONUNDA BIREBIR (Jetson benzetimi)
        S1  saha_yapilandirma + yks_ika kunyede; YOK -> BELIRDI; systemd glob
        S2  ayna sabitken KAYNAK degisince --dogrula 1 (paket_kaynak)
        S3  kunye commit'siz -> 1; elle degistirilmis -> 1; izlenen yol kirli -> 1
        S4  Jetson'a giden .pt/.onnx kunyede; kanonik/defterle farkli -> RED
        SIRA engine yer tutucu/kayitsiz -> --dondur 2; --engine-kayitsiz-bilerek
        VAKUM (curutucu 3 mutasyonu): izlenen dosya kirli -> --dondur 2 + "M "
            satiri; eksik alanli kunye -> 1; kunyedeki HER dosya tek tek bozulunca
            1 ve adi FARK LISTESINDE (subTest)
"""
import hashlib
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
from karar_sozlesmesi import MODEL_TUREV_SHA_YER_TUTUCU  # noqa: E402

BETIK = KOK / "scripts" / "surum_dondur.py"
ETIKET = "sahte-v0-yarisma"
TARIH = "2026-09-18"
SUREC_TAVAN_S = 120
GIT_KIMLIK = ("-c", "user.name=test", "-c", "user.email=test@navitas.local")

# ── MIMAR LISTELERI (D-405 §2 madde 2 + gorev emri) — betik BUNLARLA birebir ──
MIMAR_SAHA = (
    "jetson_paket/jetson_baslat.sh",
    "jetson_paket/systemd/navitas-cogullayici.service",
    "jetson_paket/systemd/navitas-iha-inis-yayinci.service",
    "jetson_paket/systemd/navitas-iha-komut-alici.service",
    "jetson_paket/systemd/navitas-kamera-koprusu.service",
    "jetson_paket/systemd/navitas-rpi-inference.service",
    "jetson_paket/systemd/navitas-seri-hub.service",
    "jetson_paket/kod/requirements_rpi.txt",
    "jetson_paket/kalibrasyon/kalibrasyon.yaml",
    "jetson_paket/kalibrasyon/dogruluk_kapisi_kareleri.json",
)
MIMAR_YKS_IKA = (
    "comms/yks_gui.py", "comms/komut_tekrar.py", "comms/protocol.py", "comms/link.py",
    "comms/iha_sender.py", "comms/ika_receiver.py", "simulation/scripts/ika_nav.py",
    "simulation/scripts/ika_surucu.py", "scripts/saha_baslat.py",
)
MIMAR_TEST_DOSYALARI = ("test_faz_b_surum_dondurma.py", "test_jetson_comms_paketi.py",
                        "test_uretim_modeli_hizasi.py")
MIMAR_OZET_YONTEMI = "sha256 v2: metin lf-normalize | ikili ham"
MIMAR_METIN_UZANTILARI = {".py", ".sh", ".service", ".md", ".yaml", ".yml", ".json",
                          ".txt", ".cfg", ".ini"}
MIMAR_IKILI_UZANTILARI = {".pt", ".onnx", ".engine", ".npz", ".npy", ".png", ".jpg"}

# Sahte ikililer NUL tasir: git bunlari IKILI sayar (autocrlf dokunmaz) — gercek
# .pt/.onnx gibi. Sahte metinler LF ile yazilir (Windows write_text CRLF yapar,
# blob'lar LF olsun ki autocrlf=true klon testi gercek depoyu taklit etsin).
SAHTE_PT = b"sahte model agirligi\x00\n" * 200
SAHTE_ONNX = b"sahte onnx grafi\x00\n" * 50
SAHTE_ENGINE_SHA = hashlib.sha256(b"sahte engine (Jetson'da derlendi)").hexdigest()
FARK_DURUMLARI = (sd.DURUM_FARKLI, sd.DURUM_YOK, sd.DURUM_BELIRDI)

# Sahte kokte S1 kapsamindan VAR olanlar; kalanlar BILEREK yok ("YOK" + BELIRDI).
EK_VAR = (
    "jetson_paket/jetson_baslat.sh",
    "jetson_paket/systemd/navitas-rpi-inference.service",
    "jetson_paket/systemd/navitas-seri-hub.service",
    "jetson_paket/kod/requirements_rpi.txt",
    "jetson_paket/kalibrasyon/kalibrasyon.yaml",
    "comms/yks_gui.py", "comms/komut_tekrar.py",
    "simulation/scripts/ika_nav.py", "scripts/saha_baslat.py",
)


def _kos(*args, kok=None):
    """Betigi GERCEK yorumlayiciyla ayri surecte kos -> (exit, cikti)."""
    komut = [sys.executable, str(BETIK)]
    if kok is not None:
        komut += ["--kok", str(kok)]
    komut += list(args)
    r = subprocess.run(komut, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=SUREC_TAVAN_S)
    return r.returncode, (r.stdout + r.stderr)


def _git(kok, *args):
    r = subprocess.run(["git", *GIT_KIMLIK, *args], cwd=str(kok), capture_output=True,
                       text=True, encoding="utf-8", errors="replace", timeout=SUREC_TAVAN_S)
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr}")
    return r.stdout


def _lf_yaz(yol: Path, metin: str):
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_bytes(metin.encode("utf-8"))


def _kunye_dosyalari(kunye: dict) -> list:
    """[(kategori, yol, beklenen)] — kunye JSON'undan BAGIMSIZ sayim (betigin
    kunye_beklenenleri'ne dayanmaz: M-D mutanti o fonksiyonu budarsa test de
    ayni dosyayi atlamasin)."""
    dosyalar = [("model", kunye["model"]["yol"], kunye["model"]["sha256"]),
                ("defter", "config/model_registry.json", kunye["registry_sha256"])]
    for kat in ("paket", "paket_kaynak", "paket_modelleri", "saha_yapilandirma", "yks_ika"):
        dosyalar += [(kat, y, o) for y, o in sorted(kunye[kat].items())]
    return dosyalar


def _fark_yollari(cikti: str) -> set:
    """--dogrula fark listesindeki `  DURUM  kategori  yol` satirlari -> {(durum, kat, yol)}.
    Git bagi satirlari (' M yol', '?? yol') iki parcalidir, buraya GIRMEZ — boylece
    'adi listede' iddiasi git status'a degil FARK LISTESINE dayanir (M-D mutanti)."""
    sonuc = set()
    for satir in cikti.splitlines():
        p = satir.split()
        if len(p) == 3 and p[0] in FARK_DURUMLARI:
            sonuc.add((p[0], p[1], p[2]))
    return sonuc


# ── (A) KAPI — gercek kok ──────────────────────────────────────────────────

class MuhurKapisi(unittest.TestCase):
    """Kunye varsa kapsam kunyeyle birebir; yoksa GORUNUR not ile gecer."""

    def test_KUNYE_VARSA_KAPSAM_KUNYEYLE_BIREBIR_VE_GIT_BAGLI(self):
        kunye = sd.kunye_yolu(KOK)
        if not kunye.is_file():
            not_ = (f"[SURUM_DONDURMA] DONDURULMADI (henuz): {kunye.relative_to(KOK)} yok - "
                    "muhur basilinca bu kapi kapsam ozetlerini + git bagini kunyeyle kiyaslar")
            print(not_, file=sys.stderr)
            print(not_)
            return
        kod, cikti = _kos("--dogrula")
        self.assertEqual(
            kod, sd.CIKIS_TAMAM,
            "MUHUR IHLALI: kunye var ama bugunku dosyalar kunyeden sapiyor ya da git bagi "
            f"kopuk (exit {kod}). Sartname SS6.1 - muhur sonrasi mudahale yok.\n{cikti}")
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

    def test_S1_EK_KAPSAM_LISTELERI_MIMAR_KARARIYLA_BIREBIR_VE_DISKTE_VAR(self):
        """D-405 §2 madde 2: liste mimarindir; adlar `ls` ile dogrulandi. Bir dosya
        adi degisirse kunye sessizce 'YOK' yazmasin — bu test liste bayatlayinca duser."""
        self.assertEqual(sd.SAHA_YAPILANDIRMA, MIMAR_SAHA)
        self.assertEqual(sd.YKS_IKA, MIMAR_YKS_IKA)
        self.assertEqual(set(sd.EK_KAPSAM), {sd.KATEGORI_SAHA, sd.KATEGORI_YKS_IKA})
        self.assertTrue(set(sd.EK_KAPSAM) <= set(sd.KUNYE_DOSYA_KATEGORILERI))
        for y in MIMAR_SAHA + MIMAR_YKS_IKA:
            self.assertTrue((KOK / y).is_file(),
                            f"{y} bugun depoda YOK - liste bayat ya da dosya tasindi; "
                            "kunye 'YOK' yazar, mimar listesini guncelleyin")

    def test_S1_SYSTEMD_GLOB_bugunku_birimlerin_hepsi_listede(self):
        """Diskteki her .service sabit listede olmali (glob yalniz SONRADAN belirenler icin)."""
        diskte = set(sd.servis_dosyalari(KOK))
        self.assertTrue(diskte, "jetson_paket/systemd altinda hic .service yok")
        self.assertTrue(diskte <= set(sd.SAHA_YAPILANDIRMA),
                        f"listede olmayan birim: {sorted(diskte - set(sd.SAHA_YAPILANDIRMA))}")

    def test_TEST_KOMUTU_uc_suiti_kosar(self):
        """D-405 karar: kunyenin test_komutu dondurma + ayna==kaynak + model hizasi suitlerini kosar."""
        self.assertEqual(sd.TEST_DOSYALARI, MIMAR_TEST_DOSYALARI)
        metin = sd.test_komutu_metni()
        self.assertIn("--dogrula", metin)
        for d in MIMAR_TEST_DOSYALARI:
            self.assertTrue((KOK / "tests" / d).is_file(), d)
            self.assertIn(d, metin)

    def test_KUNYE_SEMASI_v2_zorunlu_alanlar(self):
        self.assertEqual(sd.KUNYE_SEMA_SURUMU, 2)
        beklenen = {"sema_surumu", "ozet_yontemi", "git_head", "git_kirli", "model",
                    "registry_sha256", "paket", "paket_kaynak", "paket_modelleri",
                    "saha_yapilandirma", "yks_ika", "engine_kayitsiz",
                    "engine_kayitsiz_bilerek", "test_komutu"}
        self.assertTrue(beklenen <= set(sd.KUNYE_ZORUNLU_ALANLAR),
                        sorted(beklenen - set(sd.KUNYE_ZORUNLU_ALANLAR)))

    # ── S6 · ozet yontemi ──
    def test_S6_OZET_YONTEMI_ve_uzanti_listesi_mimar_karari(self):
        self.assertEqual(sd.OZET_YONTEMI, MIMAR_OZET_YONTEMI)
        self.assertTrue(MIMAR_METIN_UZANTILARI <= set(sd.METIN_UZANTILARI),
                        sorted(MIMAR_METIN_UZANTILARI - set(sd.METIN_UZANTILARI)))
        self.assertFalse(MIMAR_IKILI_UZANTILARI & set(sd.METIN_UZANTILARI))

    def test_S6_OZET_metin_crlf_lf_AYNI_ikili_HAM(self):
        d = Path(tempfile.mkdtemp(prefix="ozet_"))
        self.addCleanup(shutil.rmtree, d, ignore_errors=True)
        govde = "# satir 1\nprint('x')\n\n# son\n"
        (d / "lf.py").write_bytes(govde.encode())
        (d / "crlf.py").write_bytes(govde.replace("\n", "\r\n").encode())
        (d / "lf.service").write_bytes(b"[Unit]\nDescription=x\n")
        (d / "crlf.service").write_bytes(b"[Unit]\r\nDescription=x\r\n")
        self.assertEqual(sd.sha256_kanonik(d / "lf.py"), sd.sha256_kanonik(d / "crlf.py"))
        self.assertEqual(sd.sha256_kanonik(d / "lf.service"), sd.sha256_kanonik(d / "crlf.service"))
        self.assertEqual(sd.sha256_kanonik(d / "lf.py"), hashlib.sha256(govde.encode()).hexdigest())
        # metin icerigi degisince (satir sonu disinda) ozet DEGISIR
        (d / "farkli.py").write_bytes(govde.replace("x", "y").encode())
        self.assertNotEqual(sd.sha256_kanonik(d / "lf.py"), sd.sha256_kanonik(d / "farkli.py"))
        # ikili: ham — tek bayt farki ve CRLF/LF farki AYRI ozet
        (d / "a.pt").write_bytes(SAHTE_PT)
        (d / "b.pt").write_bytes(SAHTE_PT[:-1] + b"\x01")
        (d / "c.pt").write_bytes(SAHTE_PT.replace(b"\n", b"\r\n"))
        ozetler = {sd.sha256_kanonik(d / f"{a}.pt") for a in "abc"}
        self.assertEqual(len(ozetler), 3)
        self.assertEqual(sd.sha256_kanonik(d / "a.pt"), sd.sha256_hesapla(d / "a.pt"))
        # uzanti metin ama icerik NUL tasiyor -> ham (fail-safe)
        (d / "nul_lf.json").write_bytes(b'{"a": "\x00"}\n')
        (d / "nul_crlf.json").write_bytes(b'{"a": "\x00"}\r\n')
        self.assertNotEqual(sd.sha256_kanonik(d / "nul_lf.json"), sd.sha256_kanonik(d / "nul_crlf.json"))


# ── (B) MEKANIZMA — sahte kok ───────────────────────────────────────────────

class SahteKok(unittest.TestCase):
    """Gecici git deposunda sahte paket/model/defter ile CLI sozlesmesi."""

    def setUp(self):
        self.kok = Path(tempfile.mkdtemp(prefix="dondurma_")).resolve()
        self.addCleanup(shutil.rmtree, self.kok, ignore_errors=True)
        # kanonik model + .onnx turevi + Jetson'a giden kopyalari (S4)
        self.model = self.kok / "models" / "sahte_v0.pt"
        self.onnx = self.kok / "models" / "sahte_v0.onnx"
        self.model.parent.mkdir(parents=True)
        self.model.write_bytes(SAHTE_PT)
        self.onnx.write_bytes(SAHTE_ONNX)
        self.paket_model = self.kok / sd.PAKET_MODEL_DIZINI / "sahte_v0.pt"
        self.paket_onnx = self.kok / sd.PAKET_MODEL_DIZINI / "sahte_v0.onnx"
        self.paket_model.parent.mkdir(parents=True)
        shutil.copy2(self.model, self.paket_model)
        shutil.copy2(self.onnx, self.paket_onnx)
        self.defter = self.kok / sd.DEFTER_GORELI
        self.ayna = self.kok / "jetson_paket" / "config" / "model_registry.json"
        self._defter_yaz(sd.sha256_hesapla(self.model))
        # sahte paket: KOPYALAR'in her (kaynak, hedef) cifti — hedef = kaynagin kopyasi
        for kaynak_g, hedef_g in sd.PAKET_ESLEMESI:
            kaynak = self.kok / kaynak_g
            if not kaynak.is_file():
                _lf_yaz(kaynak, f"# sahte {kaynak_g}\n")
            hedef = self.kok / hedef_g
            hedef.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(kaynak, hedef)
        # S1 ek kapsam: bir kismi VAR, kalani bilerek YOK
        for y in EK_VAR:
            _lf_yaz(self.kok / y, f"# sahte {y}\n")
        # gercek gecici git deposu, temiz agac
        _git(self.kok, "init", "-q")
        _git(self.kok, "config", "core.autocrlf", "false")
        self._commit("sahte kok")

    def _defter_yaz(self, ozet, *, engine_sha=SAHTE_ENGINE_SHA, onnx_sha=None, engine_var=True):
        """Defter (model_registry semasi: profil + `turevler` dosya adiyla; her turev
        kendi sha256 + kaynak/kaynak_sha256). Ayna varsa BAYT-ES kopyalanir."""
        turevler = {}
        if engine_var:
            turevler["sahte_v0.engine"] = {"backend": "tensorrt", "imgsz": 512, "sha256": engine_sha,
                                          "kaynak": "models/sahte_v0.pt", "kaynak_sha256": ozet}
        turevler["sahte_v0.onnx"] = {"backend": "onnx", "imgsz": 512,
                                     "sha256": onnx_sha if onnx_sha is not None else sd.sha256_hesapla(self.onnx),
                                     "kaynak": "models/sahte_v0.pt", "kaynak_sha256": ozet}
        veri = {"schema_version": 1, "default_profile": "competition",
                "profiles": {"competition": {"model_id": "sahte-seg-v0-512",
                                             "path": "models/sahte_v0.pt",
                                             "backend": "pytorch", "imgsz": 512,
                                             "sha256": ozet, "turevler": turevler}}}
        _lf_yaz(self.defter, json.dumps(veri, indent=1) + "\n")
        if self.ayna.is_file():
            shutil.copy2(self.defter, self.ayna)

    def _commit(self, mesaj):
        _git(self.kok, "add", "-A")
        _git(self.kok, "commit", "-q", "-m", mesaj)

    def _dondur(self, *ek):
        return _kos("--dondur", "--etiket", ETIKET, "--tarih", TARIH, *ek, kok=self.kok)

    def _dondur_ve_commit(self, *ek):
        """Muhur yordami: --dondur -> kunye commit (S3 bunu ZORLAR). -> kunye dict."""
        kod, cikti = self._dondur(*ek)
        self.assertEqual(kod, sd.CIKIS_TAMAM, cikti)
        self._commit("kunye commit")
        return self._kunye()

    def _dogrula(self):
        return _kos("--dogrula", kok=self.kok)

    def _kunye(self):
        return json.loads(sd.kunye_yolu(self.kok).read_text(encoding="utf-8"))

    def _kunye_yaz(self, kunye):
        _lf_yaz(sd.kunye_yolu(self.kok), json.dumps(kunye, indent=1, ensure_ascii=False) + "\n")

    def _paket_hedefi(self, ad="rpi_inference.py"):
        return self.kok / "jetson_paket" / "kod" / ad

    # ── dondur ──
    def test_DONDUR_temiz_agacta_kunye_yazar_ve_alanlar_tam(self):
        kod, cikti = self._dondur()
        self.assertEqual(kod, sd.CIKIS_TAMAM, cikti)
        self.assertIn("DONDURULDU", cikti)
        self.assertIn("SIMDI: git add config/DONDURMA_KUNYESI.json", cikti)
        k = self._kunye()
        for alan in sd.KUNYE_ZORUNLU_ALANLAR:
            self.assertIn(alan, k, alan)
        self.assertEqual(k["sema_surumu"], sd.KUNYE_SEMA_SURUMU)
        self.assertEqual(k["ozet_yontemi"], MIMAR_OZET_YONTEMI)
        self.assertEqual(k["etiket"], ETIKET)
        self.assertEqual(k["tarih"], TARIH)
        self.assertEqual(k["git_head"], _git(self.kok, "rev-parse", "HEAD").strip())
        self.assertFalse(k["git_kirli"])
        self.assertFalse(k["kirli_bilerek"])
        self.assertFalse(k["engine_kayitsiz_bilerek"])
        self.assertEqual(k["engine_kayitsiz"], [])
        self.assertEqual(k["model"]["yol"], "models/sahte_v0.pt")
        self.assertEqual(k["model"]["sha256"], sd.sha256_hesapla(self.model))
        self.assertEqual(k["registry_sha256"], sd.sha256_kanonik(self.defter))
        # paket (ayna) + paket_kaynak (S2)
        self.assertEqual(set(k["paket"]), {h for _, h in sd.PAKET_ESLEMESI})
        self.assertEqual(set(k["paket_kaynak"]), {s for s, _ in sd.PAKET_ESLEMESI})
        for kat in ("paket", "paket_kaynak"):
            for yol, ozet in k[kat].items():
                self.assertEqual(ozet, sd.sha256_kanonik(self.kok / yol), f"{kat}: {yol}")
        # paket_modelleri (S4): Jetson'a giden .pt + .onnx, ham ozet
        self.assertEqual(k["paket_modelleri"], {
            f"{sd.PAKET_MODEL_DIZINI}/sahte_v0.pt": sd.sha256_hesapla(self.paket_model),
            f"{sd.PAKET_MODEL_DIZINI}/sahte_v0.onnx": sd.sha256_hesapla(self.paket_onnx)})
        # S1: listeler tam; var olan ozetli, olmayan "YOK"
        self.assertEqual(set(k["saha_yapilandirma"]), set(sd.SAHA_YAPILANDIRMA))
        self.assertEqual(set(k["yks_ika"]), set(sd.YKS_IKA))
        for kat in (sd.KATEGORI_SAHA, sd.KATEGORI_YKS_IKA):
            for yol, ozet in k[kat].items():
                p = self.kok / yol
                self.assertEqual(ozet, sd.sha256_kanonik(p) if p.is_file() else sd.DURUM_YOK, yol)
        self.assertIn(sd.DURUM_YOK, k["saha_yapilandirma"].values())
        self.assertIn(sd.DURUM_YOK, k["yks_ika"].values())
        self.assertIn("--dogrula", k["test_komutu"])
        for d in MIMAR_TEST_DOSYALARI:
            self.assertIn(d, k["test_komutu"])
        self.assertNotIn("onceki_muhur", k)

    def test_DONDUR_kirli_agac_untracked_REDDEDILIR_kunye_yazilmaz(self):
        (self.kok / "yeni_dosya.txt").write_text("commit edilmedi\n", encoding="utf-8")
        kod, cikti = self._dondur()
        self.assertEqual(kod, sd.CIKIS_RED, cikti)
        self.assertIn("KIRLI", cikti)
        self.assertIn("yeni_dosya.txt", cikti)
        self.assertFalse(sd.kunye_yolu(self.kok).exists(), "red edildi ama kunye yazildi")

    def test_VAKUM_izlenen_dosya_commit_siz_degisince_DONDUR_RED_ve_M_satiri(self):
        """Curutucu M-B: yalniz '??' kirli sayilsaydi bu test duserdi."""
        p = self.kok / "jetson_paket" / "jetson_baslat.sh"
        _lf_yaz(p, p.read_text(encoding="utf-8") + 'SYSID="${SYSID:-2}"\n')
        kod, cikti = self._dondur()
        self.assertEqual(kod, sd.CIKIS_RED, cikti)
        self.assertIn("KIRLI", cikti)
        self.assertIn(" M jetson_paket/jetson_baslat.sh", cikti)
        self.assertFalse(sd.kunye_yolu(self.kok).exists())

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
        self.model.write_bytes(b"baska agirlik\x00\n" * 100)   # defter sha256 bayat kaldi
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
        _lf_yaz(self.kok / "codes" / "rpi_inference.py", "# yeni kaynak\n")
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

    def test_S4_DONDUR_paket_modeli_eksikse_RED(self):
        self.paket_model.unlink()
        self._commit("Jetson'a giden .pt silindi")
        kod, cikti = self._dondur()
        self.assertEqual(kod, sd.CIKIS_RED, cikti)
        self.assertIn("paket_modelleri", cikti)
        self.assertIn("EKSIK", cikti)
        self.assertIn(f"{sd.PAKET_MODEL_DIZINI}/sahte_v0.pt", cikti)
        self.assertFalse(sd.kunye_yolu(self.kok).exists())

    def test_S4_DONDUR_paket_modeli_kanonikten_farkliysa_RED(self):
        """Curutucu S4 reprosu: sahte agirlik `cp models/*` ile Jetson'a giderdi."""
        self.paket_model.write_bytes(b"SAHTE AGIRLIK\x00")
        self._commit("paket .pt sahte")
        kod, cikti = self._dondur()
        self.assertEqual(kod, sd.CIKIS_RED, cikti)
        self.assertIn("FARKLI", cikti)
        self.assertIn(f"{sd.PAKET_MODEL_DIZINI}/sahte_v0.pt", cikti)

    def test_S4_DONDUR_paket_onnx_defterden_farkliysa_RED(self):
        self.paket_onnx.write_bytes(b"SAHTE ONNX\x00")
        self._commit("paket .onnx sahte")
        kod, cikti = self._dondur()
        self.assertEqual(kod, sd.CIKIS_RED, cikti)
        self.assertIn("FARKLI", cikti)
        self.assertIn(f"{sd.PAKET_MODEL_DIZINI}/sahte_v0.onnx", cikti)

    def test_S4_DONDUR_paket_onnx_yoksa_YOK_yazilir_RED_degil(self):
        self.paket_onnx.unlink()
        self._commit("paket .onnx yok")
        kod, cikti = self._dondur()
        self.assertEqual(kod, sd.CIKIS_TAMAM, cikti)
        self.assertEqual(self._kunye()["paket_modelleri"][f"{sd.PAKET_MODEL_DIZINI}/sahte_v0.onnx"],
                         sd.DURUM_YOK)

    def test_S4_DONDUR_onnx_defterde_yer_tutucuysa_RED(self):
        self._defter_yaz(sd.sha256_hesapla(self.model), onnx_sha=MODEL_TUREV_SHA_YER_TUTUCU)
        self._commit("onnx turevi kayitsiz")
        kod, cikti = self._dondur()
        self.assertEqual(kod, sd.CIKIS_RED, cikti)
        self.assertIn("KAYITSIZ", cikti)
        self.assertIn(f"{sd.PAKET_MODEL_DIZINI}/sahte_v0.onnx", cikti)

    # ── muhur sirasi ──
    def test_SIRA_DONDUR_engine_yer_tutucuysa_RED_exit_2(self):
        self._defter_yaz(sd.sha256_hesapla(self.model), engine_sha=MODEL_TUREV_SHA_YER_TUTUCU)
        self._commit("engine DERLENINCE_YAZILIR")
        kod, cikti = self._dondur()
        self.assertEqual(kod, sd.CIKIS_RED, cikti)
        self.assertIn("engine kayitsiz", cikti)
        self.assertIn("muhur erken", cikti)
        self.assertIn("sahte_v0.engine", cikti)
        self.assertIn("--engine-kayitsiz-bilerek", cikti)
        self.assertFalse(sd.kunye_yolu(self.kok).exists())

    def test_SIRA_DONDUR_tensorrt_turevi_hic_yoksa_RED(self):
        self._defter_yaz(sd.sha256_hesapla(self.model), engine_var=False)
        self._commit("profilde tensorrt turevi yok")
        kod, cikti = self._dondur()
        self.assertEqual(kod, sd.CIKIS_RED, cikti)
        self.assertIn("engine kayitsiz", cikti)
        self.assertIn(sd.ENGINE_YOK_NOTU, cikti)

    def test_SIRA_DONDUR_engine_kayitsiz_bilerek_gecer_ve_kunyede(self):
        self._defter_yaz(sd.sha256_hesapla(self.model), engine_sha=MODEL_TUREV_SHA_YER_TUTUCU)
        self._commit("engine DERLENINCE_YAZILIR")
        kod, cikti = self._dondur("--engine-kayitsiz-bilerek")
        self.assertEqual(kod, sd.CIKIS_TAMAM, cikti)
        self.assertIn("KAYITSIZKEN", cikti)
        k = self._kunye()
        self.assertTrue(k["engine_kayitsiz_bilerek"])
        self.assertEqual(k["engine_kayitsiz"], ["sahte_v0.engine"])

    def test_DONDUR_bozuk_tarih_RED(self):
        kod, cikti = _kos("--dondur", "--etiket", ETIKET, "--tarih", "18.09.2026", kok=self.kok)
        self.assertEqual(kod, sd.CIKIS_RED, cikti)
        self.assertFalse(sd.kunye_yolu(self.kok).exists())

    def test_DONDUR_yeniden_muhurleme_oncekini_kunyeye_yazar(self):
        ilk_head = self._dondur_ve_commit()["git_head"]
        kod, cikti = _kos("--dondur", "--etiket", "ikinci", "--tarih", "2026-09-19", kok=self.kok)
        self.assertEqual(kod, sd.CIKIS_TAMAM, cikti)
        self.assertIn("onceki muhur DEGISTIRILDI", cikti)
        k = self._kunye()
        self.assertEqual(k["etiket"], "ikinci")
        self.assertEqual(k["onceki_muhur"], {"etiket": ETIKET, "tarih": TARIH,
                                             "git_head": ilk_head})

    def test_S1_DONDUR_listede_olmayan_service_glob_ile_kunyeye_girer(self):
        yeni = "jetson_paket/systemd/navitas-ek-surec.service"
        _lf_yaz(self.kok / yeni, "[Service]\nExecStart=/bin/true\n")
        self._commit("ek birim")
        kod, cikti = self._dondur()
        self.assertEqual(kod, sd.CIKIS_TAMAM, cikti)
        k = self._kunye()
        self.assertEqual(k["saha_yapilandirma"][yeni], sd.sha256_kanonik(self.kok / yeni))
        self.assertEqual(set(k["saha_yapilandirma"]), set(sd.SAHA_YAPILANDIRMA) | {yeni})

    # ── dogrula ──
    def test_DOGRULA_kunye_yoksa_DONDURULMADI_exit_3(self):
        kod, cikti = self._dogrula()
        self.assertEqual(kod, sd.CIKIS_DONDURULMADI, cikti)
        self.assertIn("DONDURULMADI", cikti)
        kod, cikti = _kos("--goster", kok=self.kok)
        self.assertEqual(kod, sd.CIKIS_DONDURULMADI, cikti)

    def test_S3_DOGRULA_kunye_commit_edilmemisse_exit_1(self):
        """Dondurma yordami 'commit et' adimini ZORLAR: untracked kunye muhur degildir."""
        self.assertEqual(self._dondur()[0], sd.CIKIS_TAMAM)
        kod, cikti = self._dogrula()
        self.assertEqual(kod, sd.CIKIS_FARK, cikti)
        self.assertIn("KUNYE COMMIT EDILMEMIS", cikti)

    def test_DOGRULA_dondur_ve_commit_sonrasi_BIREBIR_exit_0(self):
        kunye = self._dondur_ve_commit()
        kod, cikti = self._dogrula()
        self.assertEqual(kod, sd.CIKIS_TAMAM, cikti)
        self.assertIn("BIREBIR", cikti)
        self.assertIn(f"{len(_kunye_dosyalari(kunye))} dosya", cikti)
        self.assertIn("kunye HEAD'de", cikti)

    def test_S3_DOGRULA_kunye_elle_degistirilmisse_exit_1(self):
        """Curutucu S3 reprosu: ayna degisti, kunyedeki sha elle guncellendi -> v1'de BIREBIR idi."""
        kunye = self._dondur_ve_commit()
        hedef = self._paket_hedefi()
        _lf_yaz(hedef, hedef.read_text(encoding="utf-8") + "# muhur sonrasi\n")
        kunye["paket"]["jetson_paket/kod/rpi_inference.py"] = sd.sha256_kanonik(hedef)
        self._kunye_yaz(kunye)
        kod, cikti = self._dogrula()
        self.assertEqual(kod, sd.CIKIS_FARK, cikti)
        self.assertIn("KUNYE DEGISTIRILMIS", cikti)
        self.assertNotIn("BIREBIR", cikti)

    def test_S3_DOGRULA_izlenen_yol_kirliyse_exit_1_ozet_ayni_olsa_bile(self):
        """(b) tek basina: LF->CRLF icerik-kanonik ozeti DEGISTIRMEZ (fark listesi bos)
        ama git 'M' gorur -> muhur sonrasi commit'siz mudahale, exit 1."""
        self._dondur_ve_commit()
        p = self.kok / "jetson_paket" / "jetson_baslat.sh"
        p.write_bytes(p.read_bytes().replace(b"\n", b"\r\n"))
        kod, cikti = self._dogrula()
        self.assertEqual(kod, sd.CIKIS_FARK, cikti)
        self.assertIn("IZLENEN YOLLAR KIRLI", cikti)
        self.assertIn(" M jetson_paket/jetson_baslat.sh", cikti)
        self.assertEqual(_fark_yollari(cikti), set(), "ozet degismemeliydi")

    def test_DOGRULA_paket_dosyasi_degisince_exit_1_ve_listede(self):
        self._dondur_ve_commit()
        hedef = self._paket_hedefi()
        _lf_yaz(hedef, hedef.read_text(encoding="utf-8") + "# muhur sonrasi\n")
        kod, cikti = self._dogrula()
        self.assertEqual(kod, sd.CIKIS_FARK, cikti)
        self.assertIn("MUHUR IHLALI", cikti)
        self.assertIn((sd.DURUM_FARKLI, "paket", "jetson_paket/kod/rpi_inference.py"),
                      _fark_yollari(cikti))
        self.assertIn("1/", cikti)                       # tek dosya sapiyor

    def test_DOGRULA_paket_dosyasi_silinince_exit_1_YOK(self):
        self._dondur_ve_commit()
        self._paket_hedefi("protocol.py").unlink()
        kod, cikti = self._dogrula()
        self.assertEqual(kod, sd.CIKIS_FARK, cikti)
        self.assertIn((sd.DURUM_YOK, "paket", "jetson_paket/kod/protocol.py"), _fark_yollari(cikti))

    def test_S2_DOGRULA_kaynak_degisince_ayna_ayniyken_exit_1(self):
        """Curutucu S2 reprosu: codes/ degisti, ayna dokunulmadi -> v1'de BIREBIR idi."""
        self._dondur_ve_commit()
        kaynak = self.kok / "codes" / "rpi_inference.py"
        _lf_yaz(kaynak, kaynak.read_text(encoding="utf-8") + "# kaynak degisti\n")
        kod, cikti = self._dogrula()
        self.assertEqual(kod, sd.CIKIS_FARK, cikti)
        self.assertIn((sd.DURUM_FARKLI, "paket_kaynak", "codes/rpi_inference.py"), _fark_yollari(cikti))

    def test_S1_DOGRULA_saha_yapilandirma_degisince_exit_1(self):
        """Curutucu S1 reprosu: jetson_baslat.sh SYSID pini degisti -> v1'de BIREBIR idi."""
        self._dondur_ve_commit()
        p = self.kok / "jetson_paket" / "jetson_baslat.sh"
        _lf_yaz(p, p.read_text(encoding="utf-8").replace("sahte", 'SYSID="${SYSID:-2}"'))
        kod, cikti = self._dogrula()
        self.assertEqual(kod, sd.CIKIS_FARK, cikti)
        self.assertIn((sd.DURUM_FARKLI, sd.KATEGORI_SAHA, "jetson_paket/jetson_baslat.sh"),
                      _fark_yollari(cikti))

    def test_S1_DOGRULA_YOK_dosya_belirince_exit_1_BELIRDI(self):
        kunye = self._dondur_ve_commit()
        self.assertEqual(kunye["yks_ika"]["comms/ika_receiver.py"], sd.DURUM_YOK)
        _lf_yaz(self.kok / "comms" / "ika_receiver.py", "# muhur sonrasi belirdi\n")
        kod, cikti = self._dogrula()
        self.assertEqual(kod, sd.CIKIS_FARK, cikti)
        self.assertIn((sd.DURUM_BELIRDI, sd.KATEGORI_YKS_IKA, "comms/ika_receiver.py"),
                      _fark_yollari(cikti))

    def test_S1_DOGRULA_yeni_systemd_birimi_belirince_exit_1_BELIRDI(self):
        """Glob: kunyede ADI BILE olmayan birim (yeni surec) muhur sonrasi eklenirse duser."""
        self._dondur_ve_commit()
        yeni = "jetson_paket/systemd/navitas-yeni-surec.service"
        _lf_yaz(self.kok / yeni, "[Service]\nExecStart=/bin/true\n")
        kod, cikti = self._dogrula()
        self.assertEqual(kod, sd.CIKIS_FARK, cikti)
        self.assertIn((sd.DURUM_BELIRDI, sd.KATEGORI_SAHA, yeni), _fark_yollari(cikti))

    def test_S4_DOGRULA_paket_modeli_degisince_exit_1(self):
        self._dondur_ve_commit()
        self.paket_model.write_bytes(b"SAHTE AGIRLIK\x00")
        kod, cikti = self._dogrula()
        self.assertEqual(kod, sd.CIKIS_FARK, cikti)
        self.assertIn((sd.DURUM_FARKLI, "paket_modelleri", f"{sd.PAKET_MODEL_DIZINI}/sahte_v0.pt"),
                      _fark_yollari(cikti))

    def test_DOGRULA_model_degisince_exit_1(self):
        self._dondur_ve_commit()
        self.model.write_bytes(b"muhur sonrasi agirlik\x00\n" * 100)
        kod, cikti = self._dogrula()
        self.assertEqual(kod, sd.CIKIS_FARK, cikti)
        self.assertIn((sd.DURUM_FARKLI, "model", "models/sahte_v0.pt"), _fark_yollari(cikti))

    def test_DOGRULA_defter_degisince_exit_1(self):
        self._dondur_ve_commit()
        # Once capa: AYNI icerigi yeniden yazmak fark uretmez (kapi mtime'a
        # degil ozete bakiyor); sonra anlamli bir alan degisince DUSMELI.
        self._defter_yaz(sd.sha256_hesapla(self.model))
        self.assertEqual(self._dogrula()[0], sd.CIKIS_TAMAM)
        veri = json.loads(self.defter.read_text(encoding="utf-8"))
        veri["profiles"]["competition"]["imgsz"] = 640
        _lf_yaz(self.defter, json.dumps(veri, indent=1) + "\n")
        kod, cikti = self._dogrula()
        self.assertEqual(kod, sd.CIKIS_FARK, cikti)
        self.assertIn((sd.DURUM_FARKLI, "defter", "config/model_registry.json"), _fark_yollari(cikti))

    def test_DOGRULA_bozuk_kunye_exit_1(self):
        sd.kunye_yolu(self.kok).parent.mkdir(parents=True, exist_ok=True)
        sd.kunye_yolu(self.kok).write_text("{bozuk", encoding="utf-8")
        kod, cikti = self._dogrula()
        self.assertEqual(kod, sd.CIKIS_FARK, cikti)
        self.assertIn("bozuk", cikti)

    def test_VAKUM_eksik_alanli_kunye_exit_1(self):
        """Curutucu M-C: zorunlu alan denetimi kalksaydi gecerli-JSON ama eksik kunye gecerdi."""
        kunye = self._dondur_ve_commit()
        for alan in ("paket", "model", "ozet_yontemi", "paket_modelleri", "yks_ika"):
            with self.subTest(alan=alan):
                eksik = dict(kunye)
                del eksik[alan]
                self._kunye_yaz(eksik)
                kod, cikti = self._dogrula()
                self.assertEqual(kod, sd.CIKIS_FARK, cikti)
                self.assertIn("eksik alanli", cikti)
                self.assertIn(alan, cikti)

    def test_VAKUM_eski_sema_kunyesi_exit_1(self):
        kunye = self._dondur_ve_commit()
        kunye["sema_surumu"] = 1
        self._kunye_yaz(kunye)
        kod, cikti = self._dogrula()
        self.assertEqual(kod, sd.CIKIS_FARK, cikti)
        self.assertIn("sema surumu uyumsuz", cikti)

    def test_VAKUM_kunyedeki_HER_dosya_tek_tek_bozulunca_exit_1_ve_adi_listede(self):
        """Curutucu M-D: bir kategori sonuncuyu atlasaydi o dosya burada yakalanirdi.
        YOK girdileri icin dosya OLUSTURULUR (BELIRDI), digerleri bozulur (FARKLI)."""
        kunye = self._dondur_ve_commit()
        beklenenler = _kunye_dosyalari(kunye)
        self.assertGreater(len(beklenenler), 2 + len(sd.PAKET_ESLEMESI))
        for kat, yol, beklenen in beklenenler:
            with self.subTest(kategori=kat, yol=yol):
                p = self.kok / yol
                if beklenen == sd.DURUM_YOK:
                    self.assertFalse(p.exists(), yol)
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_bytes(b"# muhur sonrasi belirdi\n")
                    durum = sd.DURUM_BELIRDI
                else:
                    orijinal = p.read_bytes()
                    ikili = p.suffix.lower() not in sd.METIN_UZANTILARI
                    p.write_bytes(orijinal + (b"\x00bozuk" if ikili else b"\n# bozuk\n"))
                    durum = sd.DURUM_FARKLI
                try:
                    kod, cikti = self._dogrula()
                    self.assertEqual(kod, sd.CIKIS_FARK, cikti)
                    self.assertIn((durum, kat, yol), _fark_yollari(cikti), cikti)
                finally:
                    if beklenen == sd.DURUM_YOK:
                        p.unlink()
                    else:
                        p.write_bytes(orijinal)
        self.assertEqual(self._dogrula()[0], sd.CIKIS_TAMAM, "geri alma sonrasi BIREBIR olmali")

    def test_DOGRULA_git_head_farki_dogrulamayi_DUSURMEZ(self):
        """Kunye commit edilince HEAD degisir; olcut dosya ozetleri + git bagidir."""
        self._dondur_ve_commit()
        (self.kok / "NOT.md").write_bytes(b"# kapsam disi dosya\n")
        self._commit("kapsam disi commit")
        kod, cikti = self._dogrula()
        self.assertEqual(kod, sd.CIKIS_TAMAM, cikti)
        self.assertIn("bilgi", cikti)

    def test_S6_LF_deposunun_kunyesi_autocrlf_true_KLONUNDA_BIREBIR(self):
        """Curutucu S6 reprosu (klon_crlf/klon_lf): ayni commit'in CRLF checkout'unda v1
        18/19 FARKLI diyordu. v2: metin LF-normalize -> klonda --dogrula 0."""
        self._dondur_ve_commit()
        klon = Path(tempfile.mkdtemp(prefix="dondurma_klon_")).resolve()
        self.addCleanup(shutil.rmtree, klon, ignore_errors=True)
        _git(self.kok, "clone", "-q", "-c", "core.autocrlf=true", str(self.kok), str(klon))
        ayna = klon / "jetson_paket" / "kod" / "rpi_inference.py"
        self.assertIn(b"\r\n", ayna.read_bytes(), "klon CRLF degil - benzetim kurulamadi")
        self.assertNotEqual(sd.sha256_hesapla(ayna), sd.sha256_hesapla(self._paket_hedefi()),
                            "ham ozet klonda farkli olmali (v1 kusurunun on kosulu)")
        self.assertEqual(sd.sha256_kanonik(ayna), sd.sha256_kanonik(self._paket_hedefi()))
        self.assertEqual((klon / "models" / "sahte_v0.pt").read_bytes(), SAHTE_PT, "ikili dokunulmamali")
        kod, cikti = _kos("--dogrula", kok=klon)
        self.assertEqual(kod, sd.CIKIS_TAMAM, cikti)
        self.assertIn("BIREBIR", cikti)

    # ── goster ──
    def test_GOSTER_kunyeyi_json_olarak_basar(self):
        self.assertEqual(self._dondur()[0], sd.CIKIS_TAMAM)
        kod, cikti = _kos("--goster", kok=self.kok)
        self.assertEqual(kod, sd.CIKIS_TAMAM, cikti)
        veri = json.loads(cikti)
        self.assertEqual(veri["etiket"], ETIKET)
        self.assertEqual(veri["model"]["sha256"], sd.sha256_hesapla(self.model))
        self.assertEqual(veri["ozet_yontemi"], MIMAR_OZET_YONTEMI)


if __name__ == "__main__":
    unittest.main()
