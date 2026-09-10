"""AKIS-D kapsam korumasi nobetcisi — akis_satir_tazele / akis_diyagram_dogrula --taban.

🔴 KORUNAN KUSUR (D-448 (6), T227 amelesi kanitladi): akis_satir_tazele buyuk
eklemede dugumu eski satira EN YAKIN ayni metne bagliyor ve BASKA fonksiyondaki
ayni metne kayiyordu (T227: a06/a15/a17/a19/a21/a27/a28/a30/a33/a36/a40/a41);
akis_diyagram_dogrula yalniz metni denetledigi icin "TUM DUGUMLER TUTTU" diyordu.

Gecici GERCEK git deposunda (mock yok; betik alt surecte kosar):
  K1 iki fonksiyonda ayni metin; tabanda f1'deki satira bagli dugum, f1 ustune /
     f1 icine satir eklenince f1'deki yeni satira baglanir (f2'ye DEGIL);
     alt-grafik basligi da tazelenir; ic ice tanimdaki ayni metne baglanmaz.
  K2 f1'den metin (ya da f1'in kendisi) silinirse "KAPSAM ICINDE BULUNAMADI",
     cikis 1, dugum DEGISMEZ, baslik guncellenmez.
  K3 kapsamda birden cok aday → en yakin; esit uzaklikta ESITLIK hatasi.
  K4 eski satir tabanda metni tasimiyorsa TABANDA TUTMUYOR (tahmin yok).
  K5 --kuru hicbir dosya yazmaz; --taban varsayilani HEAD; gecersiz taban → 2;
     kod commit'lendiyse eski commit --taban olarak verilebilir.
  K6 ayni ad iki kez tanimli (property setter): kacinci tanim korunur; tanim
     sayisi degisirse KAPSAM BELIRSIZ (tazele ve dogrula).
  K7 akis_diyagram_dogrula --taban kapsam degisimini yakalar (seceneksiz metin
     denetimi "tuttu" der — eski kor nokta); kapsam ici kayma ve yeni dugum hata
     degildir; kapsam hatasi varken --tablo yazilmaz.
  K8 cok parcali etiket ARDISIK satirlarda aranir.
"""
import contextlib
import importlib.util as _u
import io
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

KOK = Path(__file__).resolve().parents[1]
TAZELE = KOK / "scripts" / "akis_satir_tazele.py"
DOGRULA = KOK / "scripts" / "akis_diyagram_dogrula.py"

_sp = _u.spec_from_file_location("akis_dogrula_kapsam_testi", DOGRULA)
M = _u.module_from_spec(_sp)
_sp.loader.exec_module(M)

GIT_KIMLIK = ("-c", "user.name=akis-kapsam-test", "-c", "user.email=akis@example.invalid",
              "-c", "commit.gpgsign=false", "-c", "core.autocrlf=false")


def _git(kok, *args):
    r = subprocess.run(["git", *GIT_KIMLIK, *args], cwd=str(kok), capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr}")
    return r.stdout


def _sil(yol):
    def _yazilabilir_yap(islev, p, _hata):
        os.chmod(p, stat.S_IWRITE)
        islev(p)
    try:
        shutil.rmtree(yol, onexc=_yazilabilir_yap)
    except OSError:
        pass


# ── Fikstur: iki fonksiyonda AYNI metin (f2 once, f1 sonra) ─────────────────
TABAN_KOD = (
    "def f2(x):\n"                # 1
    "    sonuc = hesapla(x)\n"    # 2  <- f2'deki ayni metin
    "    return sonuc\n"          # 3
    "\n"                          # 4
    "\n"                          # 5
    "def f1(x):\n"                # 6
    "    y = x + 1\n"             # 7
    "    sonuc = hesapla(x)\n"    # 8  <- dugum n1 buna bagli
    "    return sonuc\n")         # 9
BASLIK = "%% koddan turetildi 0000000 2026-09-10\nflowchart TD\n"
TABAN_MMD = (BASLIK
             + '  subgraph s1["def f1()<br/>pkg/mod.py:6"]\n'
             + '    n1["sonuc = hesapla(x)<br/>pkg/mod.py:8"]\n'
             + "  end\n"
             + '  n2["def f2()<br/>pkg/mod.py:1"]\n'
             + "  n1 --> n2\n")
YARDIMCI_10 = "def yardimci():\n" + "".join(f"    a{i} = {i}\n" for i in range(8)) + "\n"
F1_ICINE_10 = "    y = x + 1\n" + "".join(f"    y += {i}\n" for i in range(10))


class _GeciciDepo(unittest.TestCase):
    KOD = TABAN_KOD
    MMD = TABAN_MMD

    def setUp(self):
        self.kok = Path(tempfile.mkdtemp(prefix="akis_kapsam_")).resolve()
        self.addCleanup(_sil, self.kok)
        _git(self.kok, "init", "-q")
        self.yaz("pkg/mod.py", self.KOD)
        self.yaz("sekil/akis_t.mmd", self.MMD)
        _git(self.kok, "add", "-A")
        _git(self.kok, "commit", "-q", "-m", "taban")
        self.mmd = self.kok / "sekil" / "akis_t.mmd"

    def yaz(self, goreli, metin):
        p = self.kok / goreli
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(metin.encode("utf-8"))

    def kodu_degistir(self, eski, yeni):
        p = self.kok / "pkg" / "mod.py"
        metin = p.read_text(encoding="utf-8")
        self.assertEqual(metin.count(eski), 1, f"fikstur: {eski!r} tekil degil")
        p.write_bytes(metin.replace(eski, yeni).encode("utf-8"))

    def tazele(self, *ek):
        r = subprocess.run([sys.executable, str(TAZELE), str(self.kok), str(self.mmd), *ek],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        return r.returncode, r.stdout + r.stderr

    def yer(self, kimlik):
        for s in self.mmd.read_text(encoding="utf-8").splitlines():
            m = re.match(r'\s*(?:subgraph\s+)?' + re.escape(kimlik)
                         + r'[\[{]"(?:.*)<br/>([^"<]+:\d+)"', s)
            if m:
                return m.group(1)
        return None

    def kapsam_hatalari(self):
        metin = self.mmd.read_text(encoding="utf-8")
        dugumler, hatalar, _ = M.dogrula_metin(metin, self.kok)
        _, _, kh, _ = M.mmd_kapsam_denetle(self.mmd, dugumler, self.kok, "HEAD")
        return hatalar, kh

    def dogrula_main(self, *argv):
        buf = io.StringIO()
        with mock.patch.object(M, "KOK", self.kok), contextlib.redirect_stdout(buf):
            rc = M.main(list(argv))
        return rc, buf.getvalue()


class K1_KapsamIcindeBaglanir(_GeciciDepo):
    def test_f1_ustune_ekleme_f1_deki_satira_baglar_f2_ye_degil(self):
        """f1 ustune 10 satir: f1 metni 18, f2'ninki 2. Eski algoritma eski satir 8'e EN
        YAKINI secerdi: |8-2|=6 < |8-18|=10 → f2 (T227 kusuru)."""
        self.kodu_degistir("def f1(x):\n", YARDIMCI_10 + "def f1(x):\n")
        rc, out = self.tazele()                                   # --taban varsayilani HEAD
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.yer("n1"), "pkg/mod.py:18", out)
        self.assertEqual(self.yer("s1"), "pkg/mod.py:16", out)   # alt-grafik basligi da
        self.assertEqual(self.yer("n2"), "pkg/mod.py:1", out)
        self.assertEqual(self.kapsam_hatalari(), ([], []))       # iki arac tutarli
        self.assertNotIn("0000000", self.mmd.read_text(encoding="utf-8").splitlines()[0])

    def test_f1_icine_ekleme_kapsam_disi_daha_yakin_olsa_da_f1(self):
        """f1 icine, metnin ustune 10 satir: kapsam basina gore beklenen satir 8; f2'nin
        satiri 2 (|6|) f1'in yeni satiri 18'den (|10|) YAKIN — yalniz kapsam kisiti kurtarir."""
        self.kodu_degistir("    y = x + 1\n", F1_ICINE_10)
        rc, out = self.tazele("--taban", "HEAD")
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.yer("n1"), "pkg/mod.py:18", out)
        self.assertEqual(self.yer("s1"), "pkg/mod.py:6", out)
        self.assertEqual(self.kapsam_hatalari(), ([], []))


class K1c_IcIceTanimHaric(_GeciciDepo):
    KOD = ("def f1(x):\n"                  # 1
           "    def ic():\n"               # 2
           "        sonuc = hesapla(x)\n"  # 3  (f1.ic)
           "        return sonuc\n"        # 4
           "    sonuc = hesapla(x)\n"      # 5  <- n1 (f1'in kendi satiri)
           "    return sonuc\n")           # 6
    MMD = BASLIK + '  n1["sonuc = hesapla(x)<br/>pkg/mod.py:5"]\n'

    def test_ic_ice_tanimdaki_ayni_metne_baglanmaz(self):
        # ic()'den sonra 5 satir: f1'in metni 10; beklenen 5 → f1.ic'teki 3 (|2|) daha yakin
        self.kodu_degistir("        return sonuc\n", "        return sonuc\n"
                           + "".join(f"    z{i} = {i}\n" for i in range(5)))
        rc, out = self.tazele()
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.yer("n1"), "pkg/mod.py:10", out)
        self.assertIn("[f1]", out)


class K2_KapsamIcindeYoksaTahminYok(_GeciciDepo):
    def test_f1_den_metin_silinirse_bulunamadi_f2_ye_kaymaz(self):
        self.kodu_degistir("    y = x + 1\n    sonuc = hesapla(x)\n",
                           "    y = x + 1\n    sonuc = baska(x)\n")
        once = self.mmd.read_bytes()
        rc, out = self.tazele()
        self.assertEqual(rc, 1, out)
        self.assertRegex(out, r"HATA n1: .*KAPSAM ICINDE BULUNAMADI: metin \[f1\] icinde yok")
        self.assertEqual(self.yer("n1"), "pkg/mod.py:8")           # f2:2'ye KAYMADI
        self.assertEqual(self.mmd.read_bytes(), once)              # baslik da guncellenmedi

    def test_kapsam_silinirse_bulunamadi(self):
        self.kodu_degistir("def f1(x):\n", "def f1_yeni(x):\n")
        rc, out = self.tazele()
        self.assertEqual(rc, 1, out)
        self.assertRegex(out, r"HATA n1: .*KAPSAM ICINDE BULUNAMADI: kapsam \[f1\] calisma agacinda yok")
        self.assertEqual(self.yer("n1"), "pkg/mod.py:8")


class K3_EnYakin(_GeciciDepo):
    KOD = ("def f1(x):\n"              # 1
           "    y = x + 1\n"           # 2
           "    sonuc = hesapla(x)\n"  # 3
           "    y = y * 2\n"           # 4
           "    y = y * 3\n"           # 5
           "    y = y * 4\n"           # 6
           "    sonuc = hesapla(x)\n"  # 7  <- n1 (ikinci gecis)
           "    return sonuc\n")       # 8
    MMD = BASLIK + '  n1["sonuc = hesapla(x)<br/>pkg/mod.py:7"]\n'

    def test_kapsamda_iki_aday_en_yakin_secilir(self):
        # 3. satirdan sonra 3 satir: adaylar 3 ve 10; beklenen 7 → 10 (|3| < |4|)
        self.kodu_degistir("    y = y * 2\n", "    k0 = 0\n    k1 = 1\n    k2 = 2\n    y = y * 2\n")
        rc, out = self.tazele()
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.yer("n1"), "pkg/mod.py:10", out)


class K3b_Esitlik(_GeciciDepo):
    def test_esit_uzak_iki_aday_hata_ve_degismez(self):
        # f1: 7 sonuc, 8 y, 9 sonuc; beklenen 8 → 7 ve 9 esit uzak
        self.kodu_degistir("    y = x + 1\n    sonuc = hesapla(x)\n",
                           "    sonuc = hesapla(x)\n    y = x + 1\n    sonuc = hesapla(x)\n")
        rc, out = self.tazele()
        self.assertEqual(rc, 1, out)
        self.assertRegex(out, r"HATA n1: .*ESITLIK: \[f1\] icinde 7 ve 9")
        self.assertEqual(self.yer("n1"), "pkg/mod.py:8")


class K4_TabandaTutmuyor(_GeciciDepo):
    def test_mmd_tabana_gore_bayatsa_tahmin_yok(self):
        # .mmd sanki daha yeni bir koddan turetilmis: n1 → 18 (tabanda 9 satir var)
        self.yaz("sekil/akis_t.mmd", TABAN_MMD.replace("pkg/mod.py:8", "pkg/mod.py:18"))
        self.kodu_degistir("def f1(x):\n", YARDIMCI_10 + "def f1(x):\n")
        rc, out = self.tazele()
        self.assertEqual(rc, 1, out)
        self.assertRegex(out, r"HATA n1: .*TABANDA TUTMUYOR")
        self.assertEqual(self.yer("n1"), "pkg/mod.py:18")


class K5_KuruVeTaban(_GeciciDepo):
    def test_kuru_dosya_yazmaz(self):
        self.kodu_degistir("def f1(x):\n", YARDIMCI_10 + "def f1(x):\n")
        once = self.mmd.read_bytes()
        rc, out = self.tazele("--kuru")
        self.assertEqual(rc, 0, out)
        self.assertIn("n1: pkg/mod.py:8 -> 18  [f1]", out)
        self.assertIn("KURU", out)
        self.assertEqual(self.mmd.read_bytes(), once)

    def test_gecersiz_taban_cikis_2(self):
        rc, out = self.tazele("--taban", "boyle-bir-ref-yok")
        self.assertEqual(rc, 2, out)
        self.assertIn("TABAN GECERSIZ", out)

    def test_kod_commitlendiyse_eski_commit_taban_verilir(self):
        self.kodu_degistir("    y = x + 1\n", F1_ICINE_10)
        _git(self.kok, "commit", "-q", "-am", "kod")
        rc, out = self.tazele()                  # HEAD artik yeni kod → eski satir tutmaz
        self.assertEqual(rc, 1, out)
        self.assertIn("TABANDA TUTMUYOR", out)
        rc, out = self.tazele("--taban", "HEAD~1")
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.yer("n1"), "pkg/mod.py:18", out)


class K6_AyniAdliTanimlar(_GeciciDepo):
    KOD = ("class C:\n"                 # 1
           "    @property\n"            # 2
           "    def x(self):\n"         # 3
           "        return self._x\n"   # 4  (C.x 1. tanim)
           "\n"                         # 5
           "    @x.setter\n"            # 6
           "    def x(self, v):\n"      # 7
           "        self._x = v\n"      # 8
           "        return self._x\n")  # 9  <- n1 (C.x 2. tanim)
    MMD = BASLIK + '  n1["return self._x<br/>pkg/mod.py:9"]\n'
    UCUNCU_TANIM = "class C:\n    @property\n    def x(self):\n        return 0\n\n"

    def test_kacinci_tanim_korunur(self):
        self.kodu_degistir("        self._x = v\n", "        self._x = v\n"
                           + "".join(f"        v{i} = {i}\n" for i in range(6)))
        rc, out = self.tazele()
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.yer("n1"), "pkg/mod.py:15", out)
        self.assertIn("[C.x#2]", out)

    def test_tanim_sayisi_degisirse_belirsiz(self):
        self.kodu_degistir("class C:\n", self.UCUNCU_TANIM)
        rc, out = self.tazele()
        self.assertEqual(rc, 1, out)
        self.assertRegex(out, r"HATA n1: .*KAPSAM BELIRSIZ: \[C\.x\] adli tanim sayisi degisti "
                              r"\(taban 2, calisma 3\)")
        self.assertEqual(self.yer("n1"), "pkg/mod.py:9")

    def test_dogrula_ayni_adli_baska_tanima_kayma_yakalanir(self):
        self.yaz("sekil/akis_t.mmd", self.MMD.replace("pkg/mod.py:9", "pkg/mod.py:4"))
        rc, out = self.dogrula_main("--mmd", str(self.mmd), "--taban", "HEAD")
        self.assertEqual(rc, 1, out)
        self.assertRegex(out, r"KAPSAM DEGISTI: n1: aynı adlı başka tanım — taban "
                              r"pkg/mod\.py:9 \[C\.x#2\] → çalışma pkg/mod\.py:4 \[C\.x\]")

    def test_dogrula_tanim_sayisi_degisirse_belirsiz(self):
        self.kodu_degistir("class C:\n", self.UCUNCU_TANIM)                    # setter 13'e
        self.yaz("sekil/akis_t.mmd", self.MMD.replace("pkg/mod.py:9", "pkg/mod.py:13"))
        rc, out = self.dogrula_main("--mmd", str(self.mmd), "--taban", "HEAD")
        self.assertEqual(rc, 1, out)
        self.assertIn("KAPSAM BELIRSIZ: n1: C.x adlı tanım sayısı değişti (taban 2, çalışma 3)",
                      out)


class K7_DogrulaTaban(_GeciciDepo):
    def test_baska_fonksiyona_kayma_yakalanir_metin_denetimi_gormez(self):
        # Kod ayni; .mmd'de n1 f1:8 → f2:2 (T227 kusurunun urettigi durum)
        self.yaz("sekil/akis_t.mmd", TABAN_MMD.replace("pkg/mod.py:8", "pkg/mod.py:2"))
        rc0, out0 = self.dogrula_main("--mmd", str(self.mmd))
        self.assertEqual(rc0, 0, out0)                     # eski kor nokta: metin 'tuttu'
        self.assertNotIn("kapsam", out0)                   # seceneksiz cikti degismedi
        rc, out = self.dogrula_main("--mmd", str(self.mmd), "--taban", "HEAD", "--tablo")
        self.assertEqual(rc, 1, out)
        self.assertRegex(out, r"KAPSAM DEGISTI: n1: taban pkg/mod\.py:8 \[f1\] → "
                              r"çalışma pkg/mod\.py:2 \[f2\]")
        self.assertIn("KAPSAM DEGISTI 1", out)
        self.assertIn("SONUÇ: HATA VAR", out)
        self.assertFalse((self.kok / "sekil" / "akis_t_dugumler.md").exists(),
                         "kapsam hatasi varken --tablo yazdi")

    def test_kapsam_ici_kayma_ve_yeni_dugum_hata_degil(self):
        self.kodu_degistir("    y = x + 1\n", F1_ICINE_10)
        self.yaz("sekil/akis_t.mmd", TABAN_MMD.replace("pkg/mod.py:8", "pkg/mod.py:18")
                 + '  n3["return sonuc<br/>pkg/mod.py:3"]\n')
        rc, out = self.dogrula_main("--mmd", str(self.mmd), "--taban", "HEAD")
        self.assertEqual(rc, 0, out)
        self.assertIn("3 düğüm karşılaştırıldı · tabanda yok 1", out)
        self.assertIn("KAPSAM DEGISTI 0", out)

    def test_gecersiz_taban_cikis_2(self):
        rc, out = self.dogrula_main("--mmd", str(self.mmd), "--taban", "boyle-bir-ref-yok")
        self.assertEqual(rc, 2, out)
        self.assertIn("TABAN GEÇERSİZ", out)


class K8_CokParcaliEtiket(_GeciciDepo):
    MMD = BASLIK + '  n1["y = x + 1<br/>sonuc = hesapla(x)<br/>pkg/mod.py:7"]\n'

    def test_parcalar_ardisik_satirlarda_aranir(self):
        # f1 basina 'y = x + 1' (ardindan 'sonuc = ...' YOK) + 2 satir: blok 10-11'e
        self.kodu_degistir("    y = x + 1\n    sonuc = hesapla(x)\n",
                           "    y = x + 1\n    z = 0\n    z += 1\n"
                           "    y = x + 1\n    sonuc = hesapla(x)\n")
        rc, out = self.tazele()
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.yer("n1"), "pkg/mod.py:10", out)


if __name__ == "__main__":
    unittest.main()
