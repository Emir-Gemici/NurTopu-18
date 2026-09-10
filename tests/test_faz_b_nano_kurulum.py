"""FAZ B · GOREV N — JETSON NANO 4GB KURULUM KAPILARI (+ D-431 ORIN NANO KILIDI).

NEDEN (SAHA_HAZIRLIK_PLANI_20260903.md §1.3 / §1.5): Nano cumartesi KURULMAMIS
geliyor; sistem Python 3.6, repo ultralytics (>= 3.8) ister. Kurulum belgesi
(jetson_paket/JETSON_NANO_KURULUM.md), Python 3.8 gereksinim listesi
(jetson_paket/kod/requirements_nano.txt) ve cevrimdisi tekerlek betigi
(scripts/nano_tekerlek_indir.py) birbirine ve jetson_baslat.sh'a KILITLI olmali;
yoksa cumartesi bir dosya bir seyi, oteki baska seyi soyler. Bu test uc dosyayi
GERCEKTEN okur, betigi GERCEKTEN kosar (--kuru: internet YOK, indirme YOK) ve
sabitleri betigin kendi adlarindan alir (madde 16: ciplak sabit yok).

D-431 (6 Eylul 2026, OLCULDU): kart Jetson Nano degil **Jetson Orin Nano Developer
Kit 4 GB** (JetPack 7.2.1 / L4T R39.2.1, Ubuntu 24.04, Python 3.12.3, kok NVMe).
Nano belgesi SILINMEDI (madde 18; kural 8: olculmus satir silinmez, etiketlenir)
ama basina "🔴 GEÇERSİZ" bandi kondu; esas belge artik
jetson_paket/JETSON_ORIN_NANO_KURULUM.md (6 Eylul kurulum tutanagi). Bu dosyanin
Nano'ya OZGU belge kilitleri (K1, K4) bant varken ATLANIR — assert SILINMEZ; bant
kalkarsa (belge yeniden esas olursa) eski kilitler kendiliginden geri gelir.
Betik/gereksinim kilitleri (K2, K3, K5–K7) kosmaya devam eder: arsiv betigin
sabitleri degismez. Yeni K8: bant + Orin belgesi + arsiv butunlugu.

Kapilar:
  K1 belge var; adimlarin metin kilidi: python3.8, venv38, jetson-io,
     nvarguscamerasrc, swap, 0,61 (+ "Nano'da boyle DEGIL" isareti, betik/gereksinim adlari)
     [D-431: GECERSIZ bandi varsa ATLANIR — K8 arsiv butunlugunu ayrica kilitler]
  K2 requirements_nano.txt = requirements_rpi.txt ustkumesi (+ torch, torchvision);
     opencv-python-headless LISTELENMEZ (gercek indirmede olculdu: ultralytics
     opencv-python ister, headless ile cift cv2 kurulur) — gerekcesi dosyada yazili
  K3 nano_tekerlek_indir.py --kuru: cikis 0, her gereksinim satiri icin bir pip
     komutu; --platform/--python-version/--only-binary/--implementation/--abi/--dest
     bayraklari; dest dizini ACILMAZ (indirme yok)
  K4 belge, betigin sabitlerini (python surumu, birincil platform) aynen tasir;
     PYTHON3 yolu jetson_baslat.sh SERVIS_KULLANICI'sinin ev dizinindedir
     [D-431: GECERSIZ bandi varsa ATLANIR]
  K5 wheels/ .gitignore'da (tekerlekler repoya girmez)
  K6 fail-closed: gereksinim dosyasi yoksa cikis 1 + HATA; bos dosya da 1
  K7 betigin platform listesi glibc 2.27 ustunu (manylinux_2_28+) ICERMEZ; wheel
     ad denetimi yalniz-2_28 / x86 / cp39 wheel'ini reddeder, sikistirilmis etiket
     kumesini (icinde 2014_aarch64 olan) kabul eder
  K8 (D-431) Nano belgesinin BASINDA GECERSIZ bandi var ve Orin belgesine + D-431'e
     yonlendirir; bant Nano metnini SILMEMIS (K1 kilitleri, OZET satiri, wheels
     kapisi hala orada); Orin belgesi VAR ve kritik satirlari tasir: JetPack 7.2.1,
     venv312, Python 3.12, PYTHON3=/home/<kullanici>/venv312/bin/python (+ SUDO_USER
     turetimi, mavproxy symlink), ucus .pt (engine URETIME ALINMAZ, D-303), FPS
     esigi 0,61 ve olculen p50/p95 (1,35/1,06 · 1,58/1,33), OLCULEMEDI (kamera,
     Pixhawk), olcum kaynagi (nv_tegra_release); Orin belgesinin kendisi bantli
     DEGIL; arsiv betigi ve gereksinim listesi de bantli; venv312 betigi pakette.
"""
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
SCRIPTS = KOK / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import nano_tekerlek_indir as nti  # noqa: E402

PAKET = KOK / "jetson_paket"
BELGE = PAKET / "JETSON_NANO_KURULUM.md"
ORIN_BELGE = PAKET / "JETSON_ORIN_NANO_KURULUM.md"
ORIN_VENV_BETIK = PAKET / "orin_nano_venv_kurulum.sh"
BASLAT_SH = PAKET / "jetson_baslat.sh"
GEREKSINIM_NANO = PAKET / "kod" / "requirements_nano.txt"
GEREKSINIM_RPI = PAKET / "kod" / "requirements_rpi.txt"
BETIK = SCRIPTS / "nano_tekerlek_indir.py"
GITIGNORE = KOK / ".gitignore"
PYTHON = sys.executable

# Belgenin tasimasi gereken adim kilitleri (gorev tanimi, madde: "metin kilidi")
BELGE_KILITLERI = ("python3.8", "venv38", "jetson-io", "nvarguscamerasrc", "swap", "0,61")
# Orin kilavuzuyla celisen yerlerin isareti
CELISKI_ISARETI = "Nano'da böyle DEĞİL"
NANO_EK_PAKETLER = ("torch", "torchvision")

# ── D-431: GECERSIZ bandi ────────────────────────────────────────────────────
#: Nano belgesinin basindaki bant (kural 8: silme yok, etiket + dogrusu). Orin
#: belgesinin kendi metnindeki "GEÇERSİZDİR" sozu bant DEGILDIR — isaret 🔴 ile.
GECERSIZ_BANDI = "🔴 **GEÇERSİZ"
GECERSIZ_KAYDI = "D-431"
#: Bant belgenin ILK satirlarinda olmali (basligin hemen altinda), sonda degil.
BANT_PENCERESI = 1500
#: Orin belgesinin tasimak zorunda oldugu olculmus kunye/karar satirlari.
ORIN_KILITLERI = (
    "JetPack 7.2.1", "Python 3.12", "Orin Nano", "venv312",
    "orin_nano_venv_kurulum.sh", "nv_tegra_release",
    "0,61", "1,35", "1,06", "1,58", "1,33",          # FPS esigi + olculen p50/p95
    "ÜRETİME ALINMAZ", "D-303", "ÖLÇÜLEMEDİ",
)
ORIN_PYTHON3_KALIBI = re.compile(r"PYTHON3=/home/([a-z0-9_]+)/venv312/bin/python")
#: test_wheels_sayisi_belgelerle_tutarli ile ayni kapi: bant §3.4'u silmemis olmali.
WHEELS_KAPISI = re.compile(r"`ls ~/wheels/\*\.whl \| wc -l`\s*\*\*(\d+)\*\*")


def _nano_gecersiz() -> bool:
    """Nano belgesinin basinda D-431 bandi var mi (K1/K4 atlama kosulu)."""
    if not BELGE.is_file():
        return False
    bas = BELGE.read_text(encoding="utf-8")[:BANT_PENCERESI]
    return GECERSIZ_BANDI in bas and GECERSIZ_KAYDI in bas


NANO_GECERSIZ = _nano_gecersiz()
ATLAMA_NEDENI = ("Nano belgesi GECERSIZ bantli (D-431: kart Orin Nano cikti) — "
                 "Nano'ya ozgu belge kilitleri arsiv; K8 kosar")


def _gereksinim_adlari(yol: Path):
    return {nti.paket_adi(s) for s in nti.gereksinimleri_oku(yol)}


def _kos(argv, cwd=None):
    return subprocess.run([PYTHON, str(BETIK), *argv], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", cwd=cwd or str(KOK),
                          timeout=120)


@unittest.skipIf(NANO_GECERSIZ, ATLAMA_NEDENI)
class K1BelgeTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(BELGE.is_file(), f"belge yok: {BELGE}")
        self.metin = BELGE.read_text(encoding="utf-8")

    def test_adim_kilitleri(self):
        for kilit in BELGE_KILITLERI:
            with self.subTest(kilit=kilit):
                self.assertIn(kilit, self.metin)

    def test_orin_celiskileri_isaretli(self):
        self.assertGreaterEqual(self.metin.count(CELISKI_ISARETI), 3,
                                "Orin kilavuzuyla celisen yerler acikca isaretlenmeli")

    def test_belge_kaynaklari_adiyla_gecer(self):
        for ad in ("nano_tekerlek_indir.py", "requirements_nano.txt", "JETSON_KILAVUZ.md",
                   "kamera_koprusu", "model_kayit_dogrula", "jetson_fps.py", "--kuru",
                   "--kapi", "--durum", nti.KAYNAK_LISTESI_ADI, nti.RAPOR_ADI,
                   "SAHA_HAZIRLIK_PLANI_20260903.md"):
            with self.subTest(ad=ad):
                self.assertIn(ad, self.metin)

    def test_engine_olculemedi_ve_esik_gevsetilmez(self):
        self.assertIn("ÖLÇÜLEMEDİ", self.metin)
        self.assertIn("gevşetilmez", self.metin)

    def test_gercek_indirme_sonucu_belgede(self):
        """Betik PC'de GERCEKTEN kosuldu; ham OZET satiri belgede (placeholder degil)."""
        self.assertIn("OZET:", self.metin)
        self.assertNotIn("(§3.3 betik çıktısıyla doldurulur", self.metin)


class K2GereksinimTests(unittest.TestCase):
    def test_nano_rpi_ustkumesi(self):
        rpi = _gereksinim_adlari(GEREKSINIM_RPI)
        nano = _gereksinim_adlari(GEREKSINIM_NANO)
        self.assertTrue(rpi, "requirements_rpi.txt bos okundu")
        for ad in sorted(rpi):
            with self.subTest(paket=ad):
                self.assertIn(ad, nano)

    def test_torch_ve_torchvision(self):
        nano = _gereksinim_adlari(GEREKSINIM_NANO)
        for ad in NANO_EK_PAKETLER:
            self.assertIn(ad, nano)

    def test_opencv_secimi_gerekceli(self):
        """Gercek indirme bulgusu: ultralytics opencv-python ister; headless cift cv2 kurar."""
        metin = GEREKSINIM_NANO.read_text(encoding="utf-8")
        nano = _gereksinim_adlari(GEREKSINIM_NANO)
        self.assertIn("opencv-python", nano)
        self.assertNotIn("opencv-python-headless", nano, "headless ile opencv-python cakisir")
        yorumlar = "\n".join(s for s in metin.splitlines() if s.lstrip().startswith("#")).lower()
        for gerekce in ("headless", "ultralytics", "opencv-python>=4.6", "kamera_koprusu"):
            with self.subTest(gerekce=gerekce):
                self.assertIn(gerekce, yorumlar, "opencv secimi ve kopru gerekcesi yorumda yazilmali")

    def test_pymavlink_ve_derleme_araclari(self):
        """pymavlink listede; sdist'e duserse bagimliliklari ve derleme araclari da bellekte."""
        nano = _gereksinim_adlari(GEREKSINIM_NANO)
        self.assertIn("pymavlink", nano)
        for ad in ("lxml", "future", "setuptools", "wheel"):
            self.assertIn(ad, nano)


class K3KuruKosumTests(unittest.TestCase):
    def test_kuru_komutlari_bayraklari_ve_indirmeme(self):
        with tempfile.TemporaryDirectory() as gecici:
            dest = Path(gecici) / "wheels_kuru"
            s = _kos(["--kuru", "--dest", str(dest)])
            self.assertEqual(s.returncode, nti.CIKIS_TAMAM, s.stdout + s.stderr)
            self.assertFalse(dest.exists(), "--kuru dizin acmamali / indirmemeli")
            komutlar = [l for l in s.stdout.splitlines() if l.startswith("KURU: ") and "<paket>" not in l]
            specler = nti.gereksinimleri_oku(GEREKSINIM_NANO)
            self.assertEqual(len(komutlar), len(specler))
            for spec, satir in zip(specler, komutlar):
                with self.subTest(spec=spec):
                    self.assertTrue(satir.endswith(" " + spec), satir)
                    self.assertIn("-m pip download", satir)
                    self.assertIn("--only-binary=:all:", satir)
                    self.assertIn(f"--python-version {nti.HEDEF_PYTHON_SURUMU}", satir)
                    self.assertIn(f"--implementation {nti.HEDEF_UYGULAMA}", satir)
                    self.assertIn(f"--abi {nti.HEDEF_ABI}", satir)
                    for p in nti.HEDEF_PLATFORMLAR:
                        self.assertIn(f"--platform {p}", satir)
                    self.assertIn(f"--dest {dest}", satir)
                    self.assertNotIn("--no-deps", satir, "birinci kademe bagimliliklari da indirir")

    def test_kuru_yedek_kademeler_gorunur(self):
        s = _kos(["--kuru"])
        self.assertEqual(s.returncode, 0)
        son = [l for l in s.stdout.splitlines() if "<paket>" in l]
        self.assertEqual(len(son), 1)
        self.assertIn("--no-deps", son[0])
        self.assertIn("--no-binary=:all:", son[0])


@unittest.skipIf(NANO_GECERSIZ, ATLAMA_NEDENI)
class K4BelgeBetikHizasiTests(unittest.TestCase):
    def setUp(self):
        self.metin = BELGE.read_text(encoding="utf-8")

    def test_python_surumu_ve_platform(self):
        self.assertIn(f"python{nti.HEDEF_PYTHON_SURUMU}", self.metin)
        self.assertIn(f"--python-version {nti.HEDEF_PYTHON_SURUMU}", self.metin)
        for p in nti.HEDEF_PLATFORMLAR:
            self.assertIn(p, self.metin)
        self.assertIn(nti.NANO_GLIBC, self.metin)

    def test_python3_yolu_servis_kullanicisinin_evinde(self):
        sh = BASLAT_SH.read_text(encoding="utf-8", errors="replace")
        # D-405 J kolu: varsayilan ic ice (${SUDO_USER:-${USER:-navitas}}) — en icteki
        # literal yedek servis kullanicisidir; ic ice olmayan eski bicim de kabul.
        m = re.search(r'SERVIS_KULLANICI="\$\{SERVIS_KULLANICI:-'
                      r'(?:\$\{SUDO_USER:-)?(?:\$\{USER:-)?([a-z0-9_]+)\}+"', sh)
        self.assertIsNotNone(m, "jetson_baslat.sh SERVIS_KULLANICI varsayilani okunamadi")
        kullanici = m.group(1)
        beklenen = f"PYTHON3=/home/{kullanici}/venv38/bin/python"
        self.assertIn(beklenen, self.metin)
        self.assertIn(f"kullanıcı adı `{kullanici}`", self.metin)
        self.assertIn(f"/home/{kullanici}/venv38/bin/mavproxy.py", self.metin,
                      "MAVProxy venv38'de; birim PATH'i icin symlink adimi belgede olmali")

    def test_D407_kurulum_hedefleri_jetson_baslat_ile_AYNI(self):
        """D-407 (curutucu S4): belge `cp kod/X.py ~/navitas/<dizin>/` derken
        jetson_baslat.sh ayni dosyayi BASKA dizinde ararsa `--kur` HATA ile durur.
        Olculdu: belge `kamera_koprusu.py`yi codes/ diyordu, betik scripts/ ariyor —
        cumartesi kurulumu tam o noktada dururdu (fail-closed ama zaman kaybi)."""
        # Yetkili kaynak: systemd birimlerinin ExecStart yollari (jetson_baslat.sh
        # `kurulu_py_dosyalari` ile tam onlari arar; dosya yoksa `--kur` HATA).
        aranan = {}
        for birim in sorted((PAKET / "systemd").glob("*.service")):
            for satir in birim.read_text(encoding="utf-8").splitlines():
                if not satir.startswith("ExecStart="):
                    continue
                for dizin, dosya in re.findall(
                        r"/(codes|comms|scripts)/([a-z0-9_]+\.py)", satir):
                    aranan[dosya] = dizin
        self.assertIn("kamera_koprusu.py", aranan,
                      "birim ExecStart'larinda kamera_koprusu.py yok")
        self.assertGreaterEqual(len(aranan), 4, aranan)
        # Belgedeki cp satirlari: `cp kod/<dosya> ... ~/navitas/<dizin>/`
        for satir in self.metin.splitlines():
            s = satir.strip()
            if not s.startswith("cp kod/"):
                continue
            hedef = re.search(r"~/navitas/([a-z]+)/", s)
            if hedef is None:
                continue
            for dosya in re.findall(r"kod/([a-z0-9_]+\.py)", s):
                if dosya in aranan:
                    self.assertEqual(
                        aranan[dosya], hedef.group(1),
                        f"{dosya}: belge ~/navitas/{hedef.group(1)}/ diyor, "
                        f"jetson_baslat.sh {aranan[dosya]}/ ariyor (D-407)")


class K5GitignoreTests(unittest.TestCase):
    def test_wheels_repoya_girmez(self):
        if not GITIGNORE.is_file():
            # T220 / K10 #7: Jetson paketi git DEGIL, `.gitignore` tasinmaz.
            self.skipTest(f".gitignore yok (paket git degil): {GITIGNORE}")
        satirlar = [s.strip() for s in GITIGNORE.read_text(encoding="utf-8").splitlines()]
        self.assertIn("wheels/", satirlar)
        self.assertEqual(nti.WHEELS_VARSAYILAN, KOK / "wheels")


class K6FailClosedTests(unittest.TestCase):
    def test_gereksinim_yoksa_cikis_1(self):
        with tempfile.TemporaryDirectory() as gecici:
            yok = Path(gecici) / "yok.txt"
            s = _kos(["--kuru", "--gereksinim", str(yok)])
            self.assertEqual(s.returncode, nti.CIKIS_HATALI_CAGRI)
            self.assertIn("HATA", s.stderr)

    def test_gereksinim_bossa_cikis_1(self):
        with tempfile.TemporaryDirectory() as gecici:
            bos = Path(gecici) / "bos.txt"
            bos.write_text("# yalniz yorum\n\n", encoding="utf-8")
            s = _kos(["--kuru", "--gereksinim", str(bos)])
            self.assertEqual(s.returncode, nti.CIKIS_HATALI_CAGRI)

    def test_yanlis_platform_yakalanir(self):
        """Sikistirilmis etiket kumesi (icinde 2_28 de gecen) UYUMLU; yalniz-2_28, x86, cp39 RED."""
        uyumlu = (
            "numpy-1.24.4-cp38-cp38-manylinux_2_17_aarch64.manylinux2014_aarch64.whl",
            "pymavlink-2.4.49-cp38-cp38-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl",
            "opencv_python-4.8.1.78-cp37-abi3-manylinux_2_17_aarch64.manylinux2014_aarch64.whl",
            "psutil-7.2.2-cp36-abi3-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl",
            "polars-1.8.2-cp38-abi3-manylinux_2_24_aarch64.whl",
            "six-1.17.0-py2.py3-none-any.whl",
            "ultralytics-8.4.118-py3-none-any.whl",
        )
        kotu_beklenen = (
            "torch-2.4.1-cp38-cp38-manylinux_2_28_aarch64.whl",
            "x-1.0-cp38-cp38-win_amd64.whl",
            "y-1.0-cp38-cp38-manylinux_2_17_x86_64.manylinux2014_x86_64.whl",
            "z-1.0-cp39-cp39-manylinux2014_aarch64.whl",
            "w-1.0-py39-none-any.whl",
        )
        for ad in uyumlu:
            with self.subTest(ad=ad):
                self.assertTrue(nti.wheel_uyumlu_mu(ad))
        for ad in kotu_beklenen:
            with self.subTest(ad=ad):
                self.assertFalse(nti.wheel_uyumlu_mu(ad))
        with tempfile.TemporaryDirectory() as gecici:
            d = Path(gecici)
            for ad in uyumlu + kotu_beklenen + ("pymavlink-2.4.49.tar.gz",):
                (d / ad).write_bytes(b"")
            self.assertEqual(nti.yanlis_platform_dosyalari(d), sorted(kotu_beklenen))


class K7PlatformListesiTests(unittest.TestCase):
    def test_glibc_ustu_platform_yok(self):
        ust = int(nti.NANO_GLIBC.split(".")[1])
        for p in nti.HEDEF_PLATFORMLAR:
            m = re.match(r"manylinux_2_(\d+)_aarch64", p)
            if m:
                self.assertLessEqual(int(m.group(1)), ust, p)
            else:
                self.assertEqual(p, "manylinux2014_aarch64", p)
            self.assertTrue(p.endswith("_aarch64"))
        self.assertIn("manylinux2014_aarch64", nti.HEDEF_PLATFORMLAR)
        self.assertFalse(nti.wheel_uyumlu_mu("a-1.0-cp38-cp38-manylinux_2_28_aarch64.whl"))
        self.assertFalse(nti.wheel_uyumlu_mu("a-1.0-cp38-cp38-manylinux2014_x86_64.whl"))

    def test_paket_adi_normalize(self):
        self.assertEqual(nti.paket_adi("numpy<2"), "numpy")
        self.assertEqual(nti.paket_adi("MAVProxy"), "mavproxy")
        self.assertEqual(nti.paket_adi("opencv_python-headless>=4.8; python_version<'3.9'"),
                         "opencv-python-headless")


class K8OrinNanoKilidiTests(unittest.TestCase):
    """D-431: 6 Eylul'de kart Orin Nano cikti. Nano belgesi bantli arsiv, Orin
    belgesi esas. Bu sinif bant VARKEN kosar; K1/K4'un atladigi yerde arsiv
    butunlugunu ve yeni belgeyi kilitler (assert silinmedi, yer degistirdi)."""

    def setUp(self):
        self.assertTrue(BELGE.is_file(), f"Nano belgesi yok (madde 18: silinmez): {BELGE}")
        self.nano = BELGE.read_text(encoding="utf-8")
        self.assertTrue(ORIN_BELGE.is_file(), f"Orin belgesi yok: {ORIN_BELGE}")
        self.orin = ORIN_BELGE.read_text(encoding="utf-8")

    def test_K8_nano_belgesi_basinda_GECERSIZ_bandi_ve_yonlendirme(self):
        bas = self.nano[:BANT_PENCERESI]
        self.assertIn(GECERSIZ_BANDI, bas, "Nano belgesinin basinda D-431 bandi yok")
        self.assertIn(GECERSIZ_KAYDI, bas)
        self.assertIn(ORIN_BELGE.name, bas, "bant Orin belgesine yonlendirmeli")
        self.assertTrue(NANO_GECERSIZ, "_nano_gecersiz() banti gormeli (K1/K4 atlama kosulu)")
        # bant "## 0." bolumunden ONCE: sona iliştirilmis bir dipnot bant sayilmaz
        self.assertLess(self.nano.index(GECERSIZ_BANDI), self.nano.index("## 0."))
        # bant dogrusunu da soyler: olculen kunye
        for kunye in ("Orin Nano", "JetPack 7.2.1", "Python 3.12"):
            with self.subTest(kunye=kunye):
                self.assertIn(kunye, bas)

    def test_K8_bant_arsivi_SILMEMIS(self):
        """Kural 8: olculmus satir silinmez, etiketlenir. K1'in kilitleri hala orada."""
        for kilit in BELGE_KILITLERI:
            with self.subTest(kilit=kilit):
                self.assertIn(kilit, self.nano)
        self.assertGreaterEqual(self.nano.count(CELISKI_ISARETI), 3)
        self.assertIn("OZET:", self.nano, "gercek indirme sonucu (3 Eylul) arsivde kalmali")
        self.assertIsNotNone(WHEELS_KAPISI.search(self.nano),
                             "§3.4 wheels kapisi silinmis (test_wheels_sayisi_belgelerle_tutarli)")
        self.assertIn(f"python{nti.HEDEF_PYTHON_SURUMU}", self.nano)

    def test_K8_orin_belgesi_kritik_satirlari_tasir(self):
        for kilit in ORIN_KILITLERI:
            with self.subTest(kilit=kilit):
                self.assertIn(kilit, self.orin)
        # Orin belgesi ESAS belgedir: kendisi bantli olamaz
        self.assertNotIn(GECERSIZ_BANDI, self.orin[:BANT_PENCERESI])
        # OLCULEMEDI != GECTI ilkesi belgede acik
        self.assertIn("ÖLÇÜLEMEDİ ≠ GEÇTİ", self.orin)

    def test_K8_orin_PYTHON3_yolu_venv312_ve_kullanici_turetimi(self):
        """Nano belgesi PYTHON3'u jetson_baslat.sh varsayilan kullanicisinin evinde
        veriyordu (K4). Orin'de kullanici olculdu ve varsayilandan FARKLI; belge
        bunu SUDO_USER turetimiyle aciklamali, yol venv312 olmali."""
        m = ORIN_PYTHON3_KALIBI.search(self.orin)
        self.assertIsNotNone(m, "Orin belgesinde PYTHON3=/home/<kullanici>/venv312/bin/python yok")
        kullanici = m.group(1)
        self.assertIn("SUDO_USER", self.orin, "kullanici varsayilandan farkli; turetim aciklanmali")
        self.assertIn(f"/home/{kullanici}", self.orin)
        self.assertIn("venv312/bin/mavproxy.py", self.orin,
                      "MAVProxy venv312'de; birim PATH'i icin symlink adimi belgede olmali")
        self.assertNotIn("venv38/bin/python", self.orin.split("## 1.")[1] if "## 1." in self.orin else "",
                         "Orin kurulum adimlarinda venv38 yolu olmamali")

    def test_K8_ucus_modeli_pt_engine_uretime_alinmaz(self):
        """D-303 oransal denklik dustu -> engine uretime ALINMAZ, ucus .pt (tutanak §8)."""
        i = self.orin.index("ÜRETİME ALINMAZ")
        pencere = self.orin[max(0, i - 400): i + 200]
        self.assertIn(".pt", pencere, "hukum cumlesi ucus modelini .pt olarak soylemeli")
        self.assertIn("D-303", pencere, "hukum D-303 esigine bagli olmali")
        self.assertIn("DÜŞTÜ", self.orin, "denklik tablosunda DUSTU hukmu olmali")

    def test_K8_arsiv_betik_ve_gereksinim_bantli_venv312_betigi_pakette(self):
        # argparse description = ilk docstring satiri: ASCII bant, GECERSIZ + D-431
        ilk = (nti.__doc__ or "").splitlines()[0]
        self.assertIn("GECERSIZ", ilk)
        self.assertIn(GECERSIZ_KAYDI, ilk)
        self.assertIn("orin_nano_venv_kurulum.sh", nti.__doc__)
        # Betigin sabitleri DEGISMEDI (arsiv, K3/K6/K7 hala anlamli)
        self.assertEqual(nti.HEDEF_ABI, "cp38")
        self.assertEqual(nti.NANO_GLIBC, "2.27")
        # Gereksinim listesinin ilk yorum satiri bantli
        gereksinim_ilk = GEREKSINIM_NANO.read_text(encoding="utf-8").splitlines()[0]
        self.assertTrue(gereksinim_ilk.startswith("#"))
        self.assertIn("GECERSIZ", gereksinim_ilk)
        self.assertIn(GECERSIZ_KAYDI, gereksinim_ilk)
        # Bantin isaret ettigi venv312 betigi pakette ve venv312'yi kuruyor
        self.assertTrue(ORIN_VENV_BETIK.is_file(), f"venv312 betigi yok: {ORIN_VENV_BETIK}")
        sh = ORIN_VENV_BETIK.read_text(encoding="utf-8", errors="replace")
        self.assertIn("venv312", sh)
        self.assertIn("--system-site-packages", sh)


if __name__ == "__main__":
    unittest.main()
