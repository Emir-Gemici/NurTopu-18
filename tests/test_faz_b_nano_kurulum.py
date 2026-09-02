"""FAZ B · GOREV N — JETSON NANO 4GB KURULUM KAPILARI.

NEDEN (SAHA_HAZIRLIK_PLANI_20260903.md §1.3 / §1.5): Nano cumartesi KURULMAMIS
geliyor; sistem Python 3.6, repo ultralytics (>= 3.8) ister. Kurulum belgesi
(jetson_paket/JETSON_NANO_KURULUM.md), Python 3.8 gereksinim listesi
(jetson_paket/kod/requirements_nano.txt) ve cevrimdisi tekerlek betigi
(scripts/nano_tekerlek_indir.py) birbirine ve jetson_baslat.sh'a KILITLI olmali;
yoksa cumartesi bir dosya bir seyi, oteki baska seyi soyler. Bu test uc dosyayi
GERCEKTEN okur, betigi GERCEKTEN kosar (--kuru: internet YOK, indirme YOK) ve
sabitleri betigin kendi adlarindan alir (madde 16: ciplak sabit yok).

Kapilar:
  K1 belge var; adimlarin metin kilidi: python3.8, venv38, jetson-io,
     nvarguscamerasrc, swap, 0,61 (+ "Nano'da boyle DEGIL" isareti, betik/gereksinim adlari)
  K2 requirements_nano.txt = requirements_rpi.txt ustkumesi (+ torch, torchvision);
     opencv-python-headless LISTELENMEZ (gercek indirmede olculdu: ultralytics
     opencv-python ister, headless ile cift cv2 kurulur) — gerekcesi dosyada yazili
  K3 nano_tekerlek_indir.py --kuru: cikis 0, her gereksinim satiri icin bir pip
     komutu; --platform/--python-version/--only-binary/--implementation/--abi/--dest
     bayraklari; dest dizini ACILMAZ (indirme yok)
  K4 belge, betigin sabitlerini (python surumu, birincil platform) aynen tasir;
     PYTHON3 yolu jetson_baslat.sh SERVIS_KULLANICI'sinin ev dizinindedir
  K5 wheels/ .gitignore'da (tekerlekler repoya girmez)
  K6 fail-closed: gereksinim dosyasi yoksa cikis 1 + HATA; bos dosya da 1
  K7 betigin platform listesi glibc 2.27 ustunu (manylinux_2_28+) ICERMEZ; wheel
     ad denetimi yalniz-2_28 / x86 / cp39 wheel'ini reddeder, sikistirilmis etiket
     kumesini (icinde 2014_aarch64 olan) kabul eder
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


def _gereksinim_adlari(yol: Path):
    return {nti.paket_adi(s) for s in nti.gereksinimleri_oku(yol)}


def _kos(argv, cwd=None):
    return subprocess.run([PYTHON, str(BETIK), *argv], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", cwd=cwd or str(KOK),
                          timeout=120)


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
        m = re.search(r'SERVIS_KULLANICI="\$\{SERVIS_KULLANICI:-([a-z0-9_]+)\}"', sh)
        self.assertIsNotNone(m, "jetson_baslat.sh SERVIS_KULLANICI varsayilani okunamadi")
        kullanici = m.group(1)
        beklenen = f"PYTHON3=/home/{kullanici}/venv38/bin/python"
        self.assertIn(beklenen, self.metin)
        self.assertIn(f"kullanıcı adı `{kullanici}`", self.metin)
        self.assertIn(f"/home/{kullanici}/venv38/bin/mavproxy.py", self.metin,
                      "MAVProxy venv38'de; birim PATH'i icin symlink adimi belgede olmali")


class K5GitignoreTests(unittest.TestCase):
    def test_wheels_repoya_girmez(self):
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


if __name__ == "__main__":
    unittest.main()
