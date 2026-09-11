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
     kod commit'lendiyse varsayilan TABAN SUPHELI (2), eski commit --taban ile.
  K6 ayni ad iki kez tanimli (property setter): kacinci tanim korunur; tanim
     sayisi degisirse KAPSAM BELIRSIZ (tazele ve dogrula).
  K7 akis_diyagram_dogrula --taban kapsam degisimini yakalar (seceneksiz metin
     denetimi "tuttu" der — eski kor nokta); kapsam ici kayma ve yeni dugum hata
     degildir; kapsam hatasi varken --tablo yazilmaz.
  K8 cok parcali etiket ARDISIK satirlarda aranir.
AKIS-D2 (curutucu RED: KUSUR-1 ve kacan N1-N4 mutasyonlari):
  K9  kod commit'lenip .mmd tazelenmediyse (curutucu karsi-ornegi: basa f3, tek
      dugum n1:8) varsayilan tazele TABAN SUPHELI → cikis 2, hicbir sey yazilmaz;
      elle --taban L dogru; elle --taban HEAD uyariyla surer, basligi damgalamaz;
      dogrula --taban HEAD TABAN SUPHELI, --taban L KAPSAM DEGISTI.
  K9b satir kaydirmayan commit supheli DEGIL (toptan dosya farki yanlis alarm).
  K9c onceki tazelemeyle degismis dugum ikinci kosuda calisma agacina gore de
      cozulur; sonuc farkliysa TABAN SUPHELI (yoksa f2'deki dugum f1'e kayiyordu).
  K10 dogrula: ayni adli fonksiyon BASKA dosyada → "dosya degisti" (N1).
  K11 dekorator satiri tanima aittir: tazele ve dogrula (N2).
  K12 goreli konum capasi def satiri: iki dekorator eklenince ayni gecis (N2b).
  K13 async def kapsamdir: tazele ve dogrula (N3).
  K14 dosya:N-M araliginin sonu da kayar (N4).
  K15 dogrula --mmd goreli yolla cokmez (D-440 EK).
AKIS-D2 EK (T226-D amelesi bulgusu: tazeleyicinin dugum deseni `subgraph …["def …<br/>
dosya:N"]` basliklarini yakalamiyordu; T226-D'de 5 baslik elle AST ile tazelendi):
  K16  alt-grafik basliklari (`def Sinif.metot()`, `ID ["` bosluklu bicim, `<br>`, `<br />`)
       iki aracta da dugumdur; tazele kaydirir ve satirin geri kalanini BAYT-ES korur;
       dogrula --taban basligin baska metoda kaymasini yakalar.
  K16b acilis/kapanis uyusmayan satir iki aracta da dugum DEGIL.
  K16g GERCEK FDR/sekiller/akis_{a..e}.mmd: iki arac ayni dugum kumesini gorur, her
       subgraph satiri tazeleyicide dugumdur.
  K17  `def B._tik()` basligi ayni adli A._tik'e kaymaz (tazele); kayma dogrula --taban'da
       KAPSAM DEGISTI.
AKIS-D2 2. RED (curutucu KUSUR-A ve kacan Y2/Y3/Y14/Y16/X1/X4/Y10 mutasyonlari):
  K18  🔴 KUSUR-A: ikinci taban DOSYA duzeyinde (".mmd'ye dokunan son commit")
       secilirse, .mmd kod commit'inden SONRA baska bir nedenle commit'lenince o
       secim tabanin kendisine dusuyor ve dugum SESSIZCE baska fonksiyonda kaliyordu.
       Ikinci taban artik dugum basina `git blame` ile alinir. K18b: ayni kurgu,
       D commit'inde .mmd'ye elle yeni dugum eklenmis.
  K19  tabanda arama penceresinin sinirlari: eski+3 ve eski-3 bulunur, eski+4 bulunmaz.
  K20  tabanda esit uzak iki aday → TABANDA ESITLIK, dugum degismez.
  K21  --taban HEAD'den eskiyse dugum satirinin koken commit'i de O TABANDAN okunur
       (.mmd tabandan sonra yeniden commit'lendi).
  K22  `async def ad(self, x)` govdeli metodun `def Sinif.ad()` alt-grafik basligi tazelenir.
  K23  TABAN SUPHELI TABANDAKI satirla hesaplanir (calisma satiri farkliyken).
  K24  etiketin ORTA parcasinda ':N' varsa (dilim `a[1:3]`) dosya:satir yalniz SONDAN okunur.
  K25  CRLF satir sonlu .mmd tazelendikten sonra CRLF kalir.
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
_st = _u.spec_from_file_location("akis_tazele_kapsam_testi", TAZELE)
T = _u.module_from_spec(_st)
_st.loader.exec_module(T)

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
    EK = {}                                   # ek kod dosyalari {goreli_yol: metin}

    def setUp(self):
        self.kok = Path(tempfile.mkdtemp(prefix="akis_kapsam_")).resolve()
        self.addCleanup(_sil, self.kok)
        _git(self.kok, "init", "-q")
        self.yaz("pkg/mod.py", self.KOD)
        for goreli, metin in self.EK.items():
            self.yaz(goreli, metin)
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
        once = self.mmd.read_bytes()
        rc, out = self.tazele()          # varsayilan: n1 satiri tabandaki .mmd'de yok → suphe
        self.assertEqual(rc, 2, out)
        self.assertIn("TABAN SUPHELI: akis_t.mmd: n1:", out)
        self.assertEqual(self.mmd.read_bytes(), once)
        rc, out = self.tazele("--taban", "HEAD")    # elle: tahmin yok, TABANDA TUTMUYOR
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

    def test_kod_commitlendiyse_varsayilan_supheli_eski_commit_taban_verilir(self):
        self.kodu_degistir("    y = x + 1\n", F1_ICINE_10)
        _git(self.kok, "commit", "-q", "-am", "kod")
        rc, out = self.tazele()                  # varsayilan HEAD: sonuc tabana bagli
        self.assertEqual(rc, 2, out)
        self.assertIn("TABAN SUPHELI: akis_t.mmd: n1:", out)
        rc, out = self.tazele("--taban", "HEAD")  # elle HEAD: eski satir tutmaz (yuksek sesle)
        self.assertEqual(rc, 1, out)
        self.assertIn("TABANDA TUTMUYOR", out)
        rc, out = self.tazele("--taban", "HEAD~1")
        self.assertEqual(rc, 0, out)
        self.assertNotIn("TABAN UYARISI", out)
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


# ── AKIS-D2 (curutucu RED) ───────────────────────────────────────────────────
F3_BASA = ("def f3(x):\n" + "".join(f"    a{i} = {i}\n" for i in range(6))
           + "    sonuc = hesapla(x)\n    return sonuc\n\n\n")      # 11 satir; f3 metni 8
G_BASA_6 = "def g(x):\n    a = 1\n    b = 2\n    return a\n\n\n"    # 6 satir


class K9_KodCommitlenince_TabanSupheli(_GeciciDepo):
    """Curutucu karsi-ornegi (KUSUR-1): taban f2:2 / f1:8, tek dugum n1 → :8 (f1). Basa
    f3 eklenip COMMIT'lenir: ayni metin 8 (f3), 13 (f2), 19 (f1). fd65b427 varsayilan HEAD
    ile cikis 0 verip n1'i f3'te birakiyor, basligi yeniden damgaliyordu; dogrula
    --taban HEAD de 'tuttu' diyordu."""
    MMD = BASLIK + '  n1["sonuc = hesapla(x)<br/>pkg/mod.py:8"]\n'

    def setUp(self):
        super().setUp()
        self.kodu_degistir("def f2(x):\n", F3_BASA + "def f2(x):\n")
        _git(self.kok, "commit", "-q", "-am", "basa f3 (.mmd tazelenmedi)")

    def test_varsayilan_taban_supheli_cikis_2_hicbir_sey_yazilmaz(self):
        once = self.mmd.read_bytes()
        rc, out = self.tazele()
        self.assertEqual(rc, 2, out)
        self.assertRegex(out, r"TABAN SUPHELI: akis_t\.mmd: n1: pkg/mod\.py:8 — sonuc tabana "
                              r"bagli: secilen taban \w{7} → 8 \[f3\] · \w{7} \(dugum satirinin "
                              r"koken commit'i\) → 19 \[f1\]")
        self.assertIn("SONUC: TABAN SUPHELI (1 dugum) — hicbir dosya yazilmadi", out)
        self.assertEqual(self.mmd.read_bytes(), once)             # dugum de baslik da ayni

    def test_kuru_da_supheli(self):
        rc, out = self.tazele("--kuru")
        self.assertEqual(rc, 2, out)
        self.assertIn("TABAN SUPHELI", out)

    def test_dogru_taban_elle_verilince_f1(self):
        rc, out = self.tazele("--taban", "HEAD~1")
        self.assertEqual(rc, 0, out)
        self.assertNotIn("TABAN SUPHELI", out)
        self.assertNotIn("TABAN UYARISI", out)
        self.assertEqual(self.yer("n1"), "pkg/mod.py:19", out)
        self.assertIn("[f1]", out)

    def test_elle_head_uyariyla_surer_baslik_damgalanmaz(self):
        rc, out = self.tazele("--taban", "HEAD")
        self.assertEqual(rc, 0, out)                              # kullanicinin acik secimi
        self.assertIn("TABAN UYARISI: akis_t.mmd: n1: pkg/mod.py:8", out)
        self.assertEqual(self.yer("n1"), "pkg/mod.py:8")
        self.assertIn("0000000", self.mmd.read_text(encoding="utf-8").splitlines()[0])

    def test_dogrula_taban_head_supheyi_raporlar(self):
        rc0, out0 = self.dogrula_main("--mmd", str(self.mmd))
        self.assertEqual(rc0, 0, out0)                            # metin denetimi 'tuttu'
        rc, out = self.dogrula_main("--mmd", str(self.mmd), "--taban", "HEAD")
        self.assertEqual(rc, 1, out)
        self.assertRegex(out, r"TABAN SUPHELI: n1: düğüm satırı \w{7} commit'inden beri "
                              r"değişmedi, kod değişti — pkg/mod\.py:8 o commit'te \[f1\], "
                              r"tabanda \[f3\]")
        self.assertIn("KAPSAM DEGISTI 0 · TABAN SUPHELI 1", out)

    def test_dogrula_dogru_taban_kapsam_degisti(self):
        rc, out = self.dogrula_main("--mmd", str(self.mmd), "--taban", "HEAD~1")
        self.assertEqual(rc, 1, out)
        self.assertRegex(out, r"KAPSAM DEGISTI: n1: taban pkg/mod\.py:8 \[f1\] → "
                              r"çalışma pkg/mod\.py:8 \[f3\]")
        self.assertIn("TABAN SUPHELI 0", out)


class K9b_SatirKaydirmayanCommitSupheliDegil(_GeciciDepo):
    def test_satir_icerigi_degisen_commit_supheli_degil(self):
        """F1 (curutucu): f1'de satir ICERIGI degisti, satir kaymadi."""
        self.kodu_degistir("    y = x + 1\n", "    y = x + 2\n")
        _git(self.kok, "commit", "-q", "-am", "f1'de satir icerigi degisti (satir kaymadi)")
        rc, out = self.tazele()
        self.assertEqual(rc, 0, out)
        self.assertIn("akis_t.mmd: 0 dugum tazelendi; cozulemeyen 0", out)
        self.assertNotIn("TABAN SUPHELI", out)
        rc, out = self.dogrula_main("--mmd", str(self.mmd), "--taban", "HEAD")
        self.assertEqual(rc, 0, out)
        self.assertIn("TABAN SUPHELI 0", out)

    def test_ayni_kapsamda_ustune_ekleme_commiti_dogru_kayar_supheli_degil(self):
        """F3 (curutucu): dugumun USTUNE ayni fonksiyonda bir satir eklenip commit'lendi —
        iki taban da ayni sonucu verir (9), suphe YOK; ikinci kosu 0 degisiklik."""
        self.kodu_degistir("    y = x + 1\n", "    y = x + 1\n    y = x + 2\n")
        _git(self.kok, "commit", "-q", "-am", "f1'de dugumun ustune bir satir (.mmd tazelenmedi)")
        rc, out = self.tazele()
        self.assertEqual(rc, 0, out)
        self.assertNotIn("TABAN SUPHELI", out)
        self.assertEqual(self.yer("n1"), "pkg/mod.py:9", out)
        rc, out = self.tazele()
        self.assertEqual(rc, 0, out)
        self.assertIn("akis_t.mmd: 0 dugum tazelendi; cozulemeyen 0", out)
        self.assertNotIn("TABAN SUPHELI", out)

    def test_dosya_sonuna_ekleme_commitlenince_supheli_degil(self):
        p = self.kok / "pkg" / "mod.py"
        p.write_bytes(p.read_bytes() + b"\n\ndef f9():\n    return 9\n")
        _git(self.kok, "commit", "-q", "-am", "sona f9 (.mmd tazelenmedi, satir kaymadi)")
        rc, out = self.tazele()
        self.assertEqual(rc, 0, out)
        self.assertIn("akis_t.mmd: 0 dugum tazelendi; cozulemeyen 0", out)
        self.assertNotIn("TABAN SUPHELI", out)
        self.assertNotIn("TABAN UYARISI", out)
        rc, out = self.dogrula_main("--mmd", str(self.mmd), "--taban", "HEAD")
        self.assertEqual(rc, 0, out)
        self.assertIn("TABAN SUPHELI 0", out)


class K9c_OncekiTazelemeSonrasiIkinciKosu(_GeciciDepo):
    """.mmd bir kez tazelenince satirlari CALISMA AGACINA goredir; ikinci kosu onlari HEAD
    koduna gore okursa (HEAD'in 8. satiri f1'in metni) f2'deki dugumu SESSIZCE f1'e tasir."""
    MMD = BASLIK + '  n2["sonuc = hesapla(x)<br/>pkg/mod.py:2"]\n'

    def test_ikinci_kosu_supheli_ilk_kosu_dogru(self):
        self.kodu_degistir("def f2(x):\n", G_BASA_6 + "def f2(x):\n")
        rc, out = self.tazele()
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.yer("n2"), "pkg/mod.py:8", out)     # f2'nin yeni satiri
        once = self.mmd.read_bytes()
        rc, out = self.tazele()                                   # ayni kodla ikinci kosu
        self.assertEqual(rc, 2, out)
        self.assertRegex(out, r"TABAN SUPHELI: akis_t\.mmd: n2: pkg/mod\.py:8 — sonuc tabana "
                              r"bagli: secilen taban \w{7} → 14 \[f1\] · calisma agaci .* → 8 \[f2\]")
        self.assertEqual(self.mmd.read_bytes(), once)


class K10_DosyaDegisimi(_GeciciDepo):
    KOD = "def f1(x):\n    sonuc = hesapla(x)\n    return sonuc\n"
    EK = {"pkg/b.py": "def f1(x):\n    sonuc = hesapla(x)\n    return sonuc\n"}
    MMD = BASLIK + '  n1["sonuc = hesapla(x)<br/>pkg/mod.py:2"]\n'

    def test_dogrula_baska_dosyadaki_ayni_adli_fonksiyona_kayma(self):
        self.yaz("sekil/akis_t.mmd", self.MMD.replace("pkg/mod.py:2", "pkg/b.py:2"))
        rc0, out0 = self.dogrula_main("--mmd", str(self.mmd))
        self.assertEqual(rc0, 0, out0)                            # metin denetimi 'tuttu'
        rc, out = self.dogrula_main("--mmd", str(self.mmd), "--taban", "HEAD")
        self.assertEqual(rc, 1, out)
        self.assertIn("KAPSAM DEGISTI: n1: dosya değişti — taban pkg/mod.py:2 → "
                      "çalışma pkg/b.py:2", out)


DEKOR_KOD = ("def dekor(f):\n"     # 1
             "    return f\n"      # 2
             "\n"                  # 3
             "\n"                  # 4
             "@dekor\n"            # 5  <- n1 (g1'in dekoratoru)
             "def g1():\n"         # 6
             "    return 1\n"      # 7
             "\n"                  # 8
             "\n"                  # 9
             "@dekor\n"            # 10 (g2)
             "def g2():\n"         # 11
             "    return 2\n")     # 12
G0_EK = "@dekor\ndef g0():\n    return 0\n\n\n"                  # 5 satir, g1'in ustune


class K11_DekoratorSatiriTanimaAittir(_GeciciDepo):
    KOD = DEKOR_KOD
    MMD = BASLIK + '  n1["@dekor<br/>pkg/mod.py:5"]\n'

    def test_tazele_dekorator_dugumu_kendi_fonksiyonunda_kalir(self):
        # dekorator modul kapsaminda sayilsaydi: modulun @dekor satirlari 5/10/15, beklenen 5 → g0
        self.kodu_degistir("@dekor\ndef g1():\n", G0_EK + "@dekor\ndef g1():\n")
        rc, out = self.tazele()
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.yer("n1"), "pkg/mod.py:10", out)   # g1'in dekoratoru
        self.assertIn("[g1]", out)

    def test_dogrula_baska_fonksiyonun_dekoratorune_kayma(self):
        self.kodu_degistir("@dekor\ndef g1():\n", G0_EK + "@dekor\ndef g1():\n")
        rc, out = self.dogrula_main("--mmd", str(self.mmd), "--taban", "HEAD")  # n1 :5 → g0
        self.assertEqual(rc, 1, out)
        self.assertRegex(out, r"KAPSAM DEGISTI: n1: taban pkg/mod\.py:5 \[g1\] → "
                              r"çalışma pkg/mod\.py:5 \[g0\]")


class K12_DekoratorEklenenFonksiyondaGoreliKonum(_GeciciDepo):
    KOD = ("def f1(x):\n"              # 1
           "    a = 0\n"               # 2
           "    sonuc = hesapla(x)\n"  # 3
           "    b = 1\n"               # 4
           "    sonuc = hesapla(x)\n"  # 5  <- n1 (ikinci gecis)
           "    return sonuc\n")       # 6
    MMD = BASLIK + '  n1["sonuc = hesapla(x)<br/>pkg/mod.py:5"]\n'

    def test_iki_dekorator_eklenince_ayni_gecise_baglanir(self):
        """Capa def satiri: 3 + (5-1) = 7. fd65b427'de capa dekoratorlu baslangicti:
        1 + 4 = 5 → ILK gecis (5), ayni fonksiyonda SESSIZ yanlis baglanti (cikis 0)."""
        self.kodu_degistir("def f1(x):\n", "@dekor_a\n@dekor_b\ndef f1(x):\n")
        rc, out = self.tazele()
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.yer("n1"), "pkg/mod.py:7", out)


class K13_AsyncDef(_GeciciDepo):
    KOD = ("async def a2(x):\n"               # 1
           "    sonuc = await hesapla(x)\n"   # 2
           "    return sonuc\n"               # 3
           "\n"                               # 4
           "\n"                               # 5
           "async def a1(x):\n"               # 6
           "    y = x + 1\n"                  # 7
           "    sonuc = await hesapla(x)\n"   # 8  <- n1
           "    return sonuc\n")              # 9
    MMD = BASLIK + '  n1["sonuc = await hesapla(x)<br/>pkg/mod.py:8"]\n'

    def test_tazele_async_kapsam_icinde(self):
        # async kapsam sayilmasaydi: modul satirlarinda adaylar 2 (a2) ve 18; beklenen 8 → 2
        self.kodu_degistir("async def a1(x):\n", YARDIMCI_10 + "async def a1(x):\n")
        rc, out = self.tazele()
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.yer("n1"), "pkg/mod.py:18", out)
        self.assertIn("[a1]", out)

    def test_dogrula_async_baska_fonksiyona_kayma(self):
        self.yaz("sekil/akis_t.mmd", self.MMD.replace("pkg/mod.py:8", "pkg/mod.py:2"))
        rc, out = self.dogrula_main("--mmd", str(self.mmd), "--taban", "HEAD")
        self.assertEqual(rc, 1, out)
        self.assertRegex(out, r"KAPSAM DEGISTI: n1: taban pkg/mod\.py:8 \[a1\] → "
                              r"çalışma pkg/mod\.py:2 \[a2\]")


class K14_AralikliAtif(_GeciciDepo):
    MMD = BASLIK + '  n1["sonuc = hesapla(x)<br/>pkg/mod.py:8-9"]\n'

    def test_aralik_sonu_da_kayar(self):
        self.kodu_degistir("def f1(x):\n", YARDIMCI_10 + "def f1(x):\n")
        rc, out = self.tazele()
        self.assertEqual(rc, 0, out)
        self.assertIn('<br/>pkg/mod.py:18-19"]', self.mmd.read_text(encoding="utf-8"), out)


class K15_GoreliMmdYolu(_GeciciDepo):
    def test_goreli_mmd_yolu_cokmez(self):
        eski_cwd = os.getcwd()
        os.chdir(self.kok)
        self.addCleanup(os.chdir, eski_cwd)                        # _sil'den ONCE calisir
        goreli = os.path.join("sekil", "akis_t.mmd")
        rc, out = self.dogrula_main("--mmd", goreli)
        self.assertEqual(rc, 0, out)
        self.assertIn(goreli + ": 3 düğüm · 3 tuttu", out)
        rc, out = self.dogrula_main("--mmd", goreli, "--taban", "HEAD")
        self.assertEqual(rc, 0, out)
        self.assertIn("KAPSAM DEGISTI 0", out)


# ── AKIS-D2 EK (T226-D amelesi bulgusu): alt-grafik basliklari `subgraph …["def …"]` ──────
SINIF_KOD = (
    "class Arayuz:\n"             # 1
    "    def _dinle(self):\n"     # 2  <- sK1 basligi
    "        m = oku()\n"         # 3  <- k1
    "        return m\n"          # 4
    "\n"                          # 5
    "    def _tik(self):\n"       # 6  <- sK2 basligi (ID ile [ arasi bosluk, <br />)
    "        m = oku()\n"         # 7  <- k2
    "        return m\n"          # 8
    "\n"                          # 9
    "\n"                          # 10
    "def main():\n"               # 11 <- sK3 basligi (<br>)
    "    m = oku()\n"             # 12 <- k3
    "    return m\n")             # 13
BASLIK_SK1 = '  subgraph sK1["def Arayuz._dinle()<br/>pkg/mod.py:{}"]'
BASLIK_SK2 = '  subgraph sK2 ["def Arayuz._tik()<br />pkg/mod.py:{}"]'
BASLIK_SK3 = '  subgraph sK3["def main()<br>pkg/mod.py:{}"]'
EK_MMD = (BASLIK
          + BASLIK_SK1.format(2) + '\n    k1["m = oku()<br/>pkg/mod.py:3"]\n  end\n'
          + BASLIK_SK2.format(6) + '\n    k2["m = oku()<br/>pkg/mod.py:7"]\n  end\n'
          + BASLIK_SK3.format(11) + '\n    k3["m = oku()<br/>pkg/mod.py:12"]\n  end\n'
          + "  k1 --> k2\n  k2 --> k3\n")
EK_METOT = "    def _yeni(self):\n        a = 1\n        b = 2\n        return a\n\n"   # 5 satir
EK_FONK = "def yardimci():\n    return 0\n\n\n"                                          # 4 satir


def _iki_arac_dugumleri(metin):
    """→ (dogrulayicinin dosya:satir + metin tasiyan dugum ID'leri, tazeleyicinin dugum
    ID'leri, tazeleyicinin alt-grafik basligi ID'leri)."""
    dg = {d.kimlik for d in M.ayristir(metin)[0] if d.dosya is not None and len(d.parcalar) >= 2}
    tz, bas = set(), set()
    for _, s, a in T.dugum_satirlari(M.satirlara_bol(metin)):
        tz.add(a[0])
        if s.lstrip().startswith("subgraph"):
            bas.add(a[0])
    return dg, tz, bas


class K16_AltGrafikBasliklari(_GeciciDepo):
    KOD = SINIF_KOD
    MMD = EK_MMD

    def satir(self, kimlik):
        for s in self.mmd.read_text(encoding="utf-8").splitlines():
            if re.match(r"\s*(?:subgraph\s+)?" + re.escape(kimlik) + r"\s*[\[{]", s):
                return s
        return None

    def test_iki_arac_ayni_dugum_kumesini_gorur(self):
        dg, tz, bas = _iki_arac_dugumleri(self.MMD)
        self.assertEqual(dg, {"sK1", "k1", "sK2", "k2", "sK3", "k3"})
        self.assertEqual(tz, dg)
        self.assertEqual(bas, {"sK1", "sK2", "sK3"})
        rc, out = self.dogrula_main("--mmd", str(self.mmd))        # fikstur gecerli diyagram
        self.assertEqual(rc, 0, out)
        self.assertIn("6 düğüm · 6 tuttu · tam satır 6 · hata 0", out)

    def test_tazele_basliklari_kaydirir_bicimi_bayt_es_korur(self):
        self.kodu_degistir("    def _dinle(self):\n", EK_METOT + "    def _dinle(self):\n")
        self.kodu_degistir("def main():\n", EK_FONK + "def main():\n")
        rc, out = self.tazele()
        self.assertEqual(rc, 0, out)
        self.assertIn("sK1: pkg/mod.py:2 -> 7  [Arayuz._dinle]", out)
        self.assertIn("sK2: pkg/mod.py:6 -> 11  [Arayuz._tik]", out)
        self.assertIn("sK3: pkg/mod.py:11 -> 20  [main]", out)
        self.assertEqual(self.satir("sK1"), BASLIK_SK1.format(7))
        self.assertEqual(self.satir("sK2"), BASLIK_SK2.format(11))  # bosluk ve <br /> ayni
        self.assertEqual(self.satir("sK3"), BASLIK_SK3.format(20))  # <br> ayni
        self.assertEqual([self.yer(k) for k in ("k1", "k2", "k3")],
                         ["pkg/mod.py:8", "pkg/mod.py:12", "pkg/mod.py:21"])
        rc, out = self.dogrula_main("--mmd", str(self.mmd))
        self.assertEqual(rc, 0, out)
        self.assertIn("6 düğüm · 6 tuttu · tam satır 6 · hata 0", out)
        rc, out = self.dogrula_main("--mmd", str(self.mmd), "--taban", "HEAD")
        self.assertEqual(rc, 0, out)
        self.assertIn("6 düğüm karşılaştırıldı · tabanda yok 0 · KAPSAM DEGISTI 0", out)

    def test_dogrula_basligin_baska_metoda_kaymasini_yakalar(self):
        # sK2 :6 → :4 (Arayuz._dinle'nin 'return m' satiri); 'def _tik(' 4±3 icinde → metin tuttu
        self.yaz("sekil/akis_t.mmd", EK_MMD.replace(BASLIK_SK2.format(6), BASLIK_SK2.format(4)))
        rc0, out0 = self.dogrula_main("--mmd", str(self.mmd))
        self.assertEqual(rc0, 0, out0)
        rc, out = self.dogrula_main("--mmd", str(self.mmd), "--taban", "HEAD")
        self.assertEqual(rc, 1, out)
        self.assertIn("KAPSAM DEGISTI: sK2: taban pkg/mod.py:6 [Arayuz._tik] → "
                      "çalışma pkg/mod.py:4 [Arayuz._dinle]", out)


class K16b_UyusmayanSekilIkiAractaDaDugumDegil(unittest.TestCase):
    def test_acilis_kapanis_uyusmayan_satir(self):
        metin = (BASLIK + '  x1["a = 1<br/>pkg/mod.py:3"}\n' + '  x2{"a = 1<br/>pkg/mod.py:3"]\n'
                 + '  x3["a = 1<br/>pkg/mod.py:3"]\n')
        dg, tz, _ = _iki_arac_dugumleri(metin)
        self.assertEqual(dg, {"x3"})
        self.assertEqual(tz, dg)


class K16g_GercekDiyagramlar(unittest.TestCase):
    """GERCEK FDR/sekiller/akis_{a..e}.mmd: iki arac ayni dugum kumesini gorur; her subgraph
    satiri tazeleyicide de dugumdur (master'daki eski desen basliklarin hepsini atliyordu)."""

    def test_bes_diyagramda_iki_arac_ayni_dugum_kumesi(self):
        toplam = 0
        for h in ("a", "b", "c", "d", "e"):
            metin = (KOK / "FDR" / "sekiller" / f"akis_{h}.mmd").read_text(encoding="utf-8")
            dg, tz, bas = _iki_arac_dugumleri(metin)
            subgraph = sum(1 for s in metin.splitlines() if s.lstrip().startswith("subgraph"))
            self.assertGreaterEqual(len(dg), 20, f"akis_{h}")
            self.assertEqual(tz, dg, f"akis_{h}: yalniz dogrula {sorted(dg - tz)} · yalniz "
                                     f"tazele {sorted(tz - dg)}")
            self.assertEqual(len(bas), subgraph, f"akis_{h}: tazeleyici {len(bas)}/{subgraph} baslik")
            toplam += len(bas)
        self.assertGreaterEqual(toplam, 5)


IKI_SINIF_KOD = (
    "class A:\n"                 # 1
    "    def _tik(self):\n"      # 2  (A._tik — ayni adli metot)
    "        return 1\n"         # 3
    "\n"                         # 4
    "\n"                         # 5
    "class B:\n"                 # 6
    "    x = 0\n"                # 7
    "\n"                         # 8
    "    def _tik(self):\n"      # 9  <- sB basligi "def B._tik()"
    "        return 2\n")        # 10


class K17_DefBasligiAyniAdliBaskaSinifaKaymaz(_GeciciDepo):
    KOD = IKI_SINIF_KOD
    MMD = (BASLIK + '  subgraph sB["def B._tik()<br/>pkg/mod.py:9"]\n'
           + '    b1["return 2<br/>pkg/mod.py:10"]\n  end\n')

    def test_tazele_baslik_kendi_sinifinin_metodunda_kalir(self):
        """B'de _tik ustune 10 satir: B._tik 19. Eski algoritma eski satir 9'a en yakin
        'def _tik(' satirini secerdi: A'nin 2'si (|7| < |10|)."""
        self.kodu_degistir("    x = 0\n", "    x = 0\n" + "".join(f"    y{i} = {i}\n" for i in range(10)))
        rc, out = self.tazele()
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.yer("sB"), "pkg/mod.py:19", out)
        self.assertEqual(self.yer("b1"), "pkg/mod.py:20", out)
        self.assertIn("sB: pkg/mod.py:9 -> 19  [B._tik]", out)

    def test_dogrula_baslik_ayni_adli_baska_sinif_metoduna_kayma(self):
        self.yaz("sekil/akis_t.mmd", self.MMD.replace("pkg/mod.py:9", "pkg/mod.py:2"))
        rc0, out0 = self.dogrula_main("--mmd", str(self.mmd))
        self.assertEqual(rc0, 0, out0)                            # metin: 'def _tik(' tam satirda
        rc, out = self.dogrula_main("--mmd", str(self.mmd), "--taban", "HEAD")
        self.assertEqual(rc, 1, out)
        self.assertIn("KAPSAM DEGISTI: sB: taban pkg/mod.py:9 [B._tik] → "
                      "çalışma pkg/mod.py:2 [A._tik]", out)


# ── AKIS-D2 2. RED (curutucu KUSUR-A + kacan mutasyonlar) ────────────────────
class K18_DugumKokeniMmdBaskaNedenleCommitlendi(_GeciciDepo):
    """🔴 KUSUR-A karsi-ornegi. Kurgu: A (.mmd n1 → f1:8) → C (basa f3, KOD commit'i,
    .mmd tazelenmedi) → D (.mmd'ye YALNIZ '%% not' yorumu, commit). Ikinci taban dosya
    duzeyinde secilseydi L = D = taban olur, suphe dusER ve varsayilan tazele cikis 0
    verip n1'i f3'te birakir, basligi yeniden damgalardi (curutucu F4 olcumu).
    `git blame` n1 SATIRINI A'ya baglar → suphe."""
    MMD = BASLIK + '  n1["sonuc = hesapla(x)<br/>pkg/mod.py:8"]\n'
    MMD_D_EKI = "%% not\n"

    def setUp(self):
        super().setUp()
        self.kodu_degistir("def f2(x):\n", F3_BASA + "def f2(x):\n")
        _git(self.kok, "commit", "-q", "-am", "C: basa f3 (.mmd tazelenmedi)")
        # Ek satir n1'in ONUNE girer: blame satir eslemesi de kilitlenir (bir satir
        # kayarsa n1'in kokeni D sanilir ve suphe kaybolur).
        self.yaz("sekil/akis_t.mmd", self.MMD.replace('  n1["', self.MMD_D_EKI + '  n1["'))
        _git(self.kok, "commit", "-q", "-am", "D: .mmd baska bir nedenle commit'lendi")

    def test_varsayilan_taban_supheli_dugum_kokenine_gore(self):
        once = self.mmd.read_bytes()
        rc, out = self.tazele()
        self.assertEqual(rc, 2, out)
        self.assertRegex(out, r"TABAN SUPHELI: akis_t\.mmd: n1: pkg/mod\.py:8 — sonuc tabana "
                              r"bagli: secilen taban \w{7} → 8 \[f3\] · \w{7} \(dugum satirinin "
                              r"koken commit'i\) → 19 \[f1\]")
        self.assertEqual(self.mmd.read_bytes(), once)      # dugum de baslik damgasi da ayni

    def test_dogrula_taban_head_supheyi_raporlar(self):
        rc0, out0 = self.dogrula_main("--mmd", str(self.mmd))
        self.assertEqual(rc0, 0, out0)                     # metin denetimi 'tuttu' der
        rc, out = self.dogrula_main("--mmd", str(self.mmd), "--taban", "HEAD")
        self.assertEqual(rc, 1, out)
        self.assertRegex(out, r"TABAN SUPHELI: n1: düğüm satırı \w{7} commit'inden beri "
                              r"değişmedi, kod değişti — pkg/mod\.py:8 o commit'te \[f1\], "
                              r"tabanda \[f3\]")
        self.assertIn("TABAN SUPHELI 1", out)

    def test_dogru_taban_elle_verilince_f1(self):
        rc, out = self.tazele("--taban", "HEAD~2")
        self.assertEqual(rc, 0, out)
        self.assertNotIn("TABAN UYARISI", out)
        self.assertEqual(self.yer("n1"), "pkg/mod.py:19", out)


class K18b_DugumKokeniMmdYeniDugumleCommitlendi(K18_DugumKokeniMmdBaskaNedenleCommitlendi):
    """F4b: D commit'inde .mmd'ye elle YENI bir dugum eklendi (dokunulmayan baska dosyaya
    atif; n1 satiri yine A'nin, ama artik bir satir asagida). Sonuc ayni olmali."""
    EK = {"pkg/b.py": "def g(x):\n    deger = oku(x)\n    return deger\n"}
    MMD_D_EKI = '  n2["deger = oku(x)<br/>pkg/b.py:2"]\n'


SINIR_KOD = ("def f1(x):\n"              # 1
             "    a0 = 0\n"              # 2
             "    a1 = 1\n"              # 3
             "    a2 = 2\n"              # 4
             "    sonuc = hesapla(x)\n"  # 5
             "    a3 = 3\n"              # 6
             "    a4 = 4\n"              # 7
             "    a5 = 5\n"              # 8
             "    return sonuc\n")       # 9
SINIR_MMD = BASLIK + '  n1["sonuc = hesapla(x)<br/>pkg/mod.py:%d"]\n'


class K19_TabandaPencereUstSiniri(_GeciciDepo):
    """Tabanda arama penceresi ±SATIR_TOLERANSI: metin tam eski+3'te (2 → 5) bulunmali."""
    KOD = SINIR_KOD
    MMD = SINIR_MMD % 2

    def test_eski_arti_tolerans_bulunur(self):
        rc, out = self.tazele()
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.yer("n1"), "pkg/mod.py:5", out)


class K19b_TabandaPencereAltSiniri(_GeciciDepo):
    """Metin tam eski-3'te (8 → 5) bulunmali."""
    KOD = SINIR_KOD
    MMD = SINIR_MMD % 8

    def test_eski_eksi_tolerans_bulunur(self):
        rc, out = self.tazele()
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.yer("n1"), "pkg/mod.py:5", out)


class K19c_TabandaPencereDisi(_GeciciDepo):
    """Metin eski+4'te ise pencere DISI: TABANDA TUTMUYOR, tahmin yok."""
    KOD = SINIR_KOD
    MMD = SINIR_MMD % 1

    def test_eski_arti_tolerans_arti_bir_bulunmaz(self):
        once = self.mmd.read_bytes()
        rc, out = self.tazele()
        self.assertEqual(rc, 1, out)
        self.assertRegex(out, r"HATA n1: .*TABANDA TUTMUYOR: satir 1\+-3 metni tasimiyor")
        self.assertEqual(self.mmd.read_bytes(), once)


class K20_TabandaEsitlik(_GeciciDepo):
    """Tabanda eski satira ESIT uzak iki aday → TABANDA ESITLIK; dugum degismez."""
    KOD = ("def f1(x):\n"              # 1
           "    sonuc = hesapla(x)\n"  # 2
           "    y = x + 1\n"           # 3
           "    sonuc = hesapla(x)\n"  # 4
           "    return sonuc\n")       # 5
    MMD = BASLIK + '  n1["sonuc = hesapla(x)<br/>pkg/mod.py:3"]\n'

    def test_tabanda_esit_uzak_iki_aday_hata_ve_degismez(self):
        once = self.mmd.read_bytes()
        rc, out = self.tazele()
        self.assertEqual(rc, 1, out)
        self.assertRegex(out, r"HATA n1: .*TABANDA ESITLIK: 2 ve 4 eski satira esit uzak")
        self.assertEqual(self.mmd.read_bytes(), once)


class K21_DugumKokeniVerilenTabandanOkunur(_GeciciDepo):
    """--taban HEAD'den ESKI bir ref ise dugum satirinin koken commit'i de O TABANDAN
    okunmali: .mmd tabandan SONRA yeniden commit'lendiyse HEAD'den okumak kokeni E'ye
    baglar ve suphe kaybolur. Kurgu: A (n1 → f1:8) → C (basa f3) → E (.mmd elle 19)."""
    MMD = BASLIK + '  n1["sonuc = hesapla(x)<br/>pkg/mod.py:8"]\n'

    def setUp(self):
        super().setUp()
        self.kodu_degistir("def f2(x):\n", F3_BASA + "def f2(x):\n")
        _git(self.kok, "commit", "-q", "-am", "C: basa f3 (.mmd tazelenmedi)")
        self.yaz("sekil/akis_t.mmd", self.MMD.replace("pkg/mod.py:8", "pkg/mod.py:19"))
        _git(self.kok, "commit", "-q", "-am", "E: .mmd elle tazelendi (n1 → 19)")

    def test_dogrula_eski_tabanda_koken_tabandan_hesaplanir(self):
        rc, out = self.dogrula_main("--mmd", str(self.mmd), "--taban", "HEAD~1")
        self.assertEqual(rc, 1, out)
        self.assertRegex(out, r"TABAN SUPHELI: n1: düğüm satırı \w{7} commit'inden beri "
                              r"değişmedi, kod değişti — pkg/mod\.py:8 o commit'te \[f1\], "
                              r"tabanda \[f3\]")
        self.assertIn("TABAN SUPHELI 1", out)


ASYNC_SINIF_KOD = (
    "class A:\n"                       # 1
    "    def once(self):\n"            # 2
    "        return 0\n"               # 3
    "\n"                               # 4
    "    async def _tik(self, x):\n"   # 5  <- sA basligi ("def A._tik()")
    "        m = await oku(x)\n"       # 6  <- a1
    "        return m\n")              # 7
ASYNC_EK_METOT = "    def yeni(self):\n        return 1\n\n"          # 3 satir


class K22_AsyncGovdeliDefBasligi(_GeciciDepo):
    """`def Sinif.ad()` basligi kod metniyle eslesmediginde tanim satirina duser; bu
    eslesme `async def ad(self, x):` bicimini de tanimali (yoksa KAPSAM ICINDE BULUNAMADI)."""
    KOD = ASYNC_SINIF_KOD
    MMD = (BASLIK + '  subgraph sA["def A._tik()<br/>pkg/mod.py:5"]\n'
           + '    a1["m = await oku(x)<br/>pkg/mod.py:6"]\n  end\n')

    def test_async_def_basligi_kaydirilir(self):
        self.kodu_degistir("    def once(self):\n", ASYNC_EK_METOT + "    def once(self):\n")
        rc, out = self.tazele()
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.yer("sA"), "pkg/mod.py:8", out)
        self.assertEqual(self.yer("a1"), "pkg/mod.py:9", out)
        self.assertIn("[A._tik]", out)
        self.assertEqual(self.kapsam_hatalari(), ([], []))


class K23_SupheTabandakiSatirlaHesaplanir(_GeciciDepo):
    """Calisma .mmd'nin satiri taban .mmd'ninkinden FARKLIYKEN TABAN SUPHELI tabandaki
    satirla hesaplanmali: calisma satiriyla hesaplanirsa bildirilen kapsam yanlis olur
    (burada A'da 13. satir yok → 'ölçülemedi')."""
    MMD = BASLIK + '  n1["sonuc = hesapla(x)<br/>pkg/mod.py:8"]\n'

    def setUp(self):
        super().setUp()
        self.kodu_degistir("def f2(x):\n", F3_BASA + "def f2(x):\n")
        _git(self.kok, "commit", "-q", "-am", "C: basa f3 (.mmd tazelenmedi)")
        self.yaz("sekil/akis_t.mmd", self.MMD.replace("pkg/mod.py:8", "pkg/mod.py:13"))

    def test_dogrula_supheyi_taban_satiriyla_hesaplar(self):
        rc, out = self.dogrula_main("--mmd", str(self.mmd), "--taban", "HEAD")
        self.assertEqual(rc, 1, out)
        self.assertRegex(out, r"TABAN SUPHELI: n1: düğüm satırı \w{7} commit'inden beri "
                              r"değişmedi, kod değişti — pkg/mod\.py:8 o commit'te \[f1\], "
                              r"tabanda \[f3\]")
        self.assertRegex(out, r"KAPSAM DEGISTI: n1: taban pkg/mod\.py:8 \[f3\] → "
                              r"çalışma pkg/mod\.py:13 \[f2\]")


class K24_OrtaParcadaIkiNokta(_GeciciDepo):
    """Etiketin ORTA parcasi ':N' tasiyabilir (dilim `a[1:3]`): dosya:satir YALNIZ etiketin
    SONUNDAN okunmali, yoksa 'y = a[1' dosya adi sanilir."""
    KOD = ("def f1(x):\n"        # 1
           "    islem(x)\n"      # 2
           "    y = a[1:3]\n"    # 3
           "    return y\n")     # 4
    MMD = BASLIK + '  n1["islem(x)<br/>y = a[1:3]<br/>pkg/mod.py:2"]\n'

    def test_dosya_satir_etiketin_sonundan_okunur(self):
        self.kodu_degistir("def f1(x):\n", YARDIMCI_10 + "def f1(x):\n")
        rc, out = self.tazele()
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.yer("n1"), "pkg/mod.py:12", out)
        self.assertIn('n1["islem(x)<br/>y = a[1:3]<br/>pkg/mod.py:12"]',
                      self.mmd.read_text(encoding="utf-8"), out)


class K25_CrlfKorunur(_GeciciDepo):
    """CRLF satir sonlu .mmd tazelenince CRLF kalmali (git diff'i satir satir sismesin)."""
    MMD = TABAN_MMD.replace("\n", "\r\n")

    def test_crlf_mmd_crlf_kalir(self):
        self.assertIn(b"\r\n", self.mmd.read_bytes())
        self.kodu_degistir("def f1(x):\n", YARDIMCI_10 + "def f1(x):\n")
        rc, out = self.tazele()
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.yer("n1"), "pkg/mod.py:18", out)
        ham = self.mmd.read_bytes()
        self.assertNotIn(b"\n", ham.replace(b"\r\n", b""), "tek basina LF kaldi")


if __name__ == "__main__":
    unittest.main()
