"""T112 KAPISI: `scripts/olcum/` aynasi CANLI betiklerle BIREBIR ayni mi?

NEDEN (karar D-189 · olcum D-188). `O:\\navitas-local-train` bir git deposu
DEGILDIR (`git rev-parse` -> *not a git repository*). Yani `scripts/olcum/`
bir "fazlalik kopya" degil, o betiklerin **TEK SURUM KONTROLUDUR**.

🔴 CANLI BIR AYRISMA BULUNDU (D-189): D-166'da yanlis bir oncul uc yerde
duzeltilirken `76_serit_etiketi_celiskisi.py`nin YALNIZ repo aynasi
duzeltilmis; canli betik curutulmus gerekceyi tasimaya devam ediyordu. Bir
kapi olsaydi bu, kesfedildigi gun degil **D-166 commit'inde** yakalanirdi.

⚠ Ayni kalip projede DORT kez tekrarladi: D-158 bulgu 4 · D-170 (test vardi
ama kosmuyordu) · T104 · D-188. `codes/` -> `jetson_paket/kod/` aynasi ZATEN
arac + testle korunuyor ve orada ayrisma YASANMADI. Bu dosya yeni bir sey
icat etmez; CALISAN kalibi (`tests/test_jetson_comms_paketi.py`) eksik olan
yere tasir.

────────────────────────────────────────────────────────────────────────────
BAGLAYICI SARTLAR (D-189 §3) — hepsi bu dosyada uygulanmistir:

  1. CIFTLER MEKANIK BULUNUR. Elle liste TUTULMAZ; elle liste BAYATLAR ve bu
     oturumun tekrar eden kusurudur. Iki tarafta AYNI ADLA bulunan `*.py`
     dosyalari cift sayilir (`__pycache__` haric).
  2. KIYAS BAYT BAZINDA (`filecmp.cmp(..., shallow=False)`).
  3. 🔴 YON IDDIA EDILMEZ. Test yalniz "ayni mi" der. Hangisinin DOGRU oldugu
     INSAN KARARIDIR: D-166'da dogru olan REPO kopyasiydi, T104'te PAKET
     kopyasi. Bu dosyada otomatik kopyalama/onarim YOKTUR (ve bunu bir test
     kilitler).
  4. 🔴 CANLI DIZIN YOKSA `skipTest` — dusmez ama SESSIZ de kalmaz; atlama
     sebebi acikca yazilir. Gerekce: bu kapi baska makinede ve PC garantiye
     gittiginde kosulamaz; orada kirmizi yanmasi YANLIS ALARM olur.
     ⚠ Bedeli bilincli kabul edildi: koruma yalnizca ayrismanin
     URETILEBILDIGI makinede vardir.
  5. CANLI DIZIN YOLU TEK YERDE (madde 16): `NAVITAS_OLCUM_KOK` ortam
     degiskeni, yoksa `KOK.parent / "navitas-local-train"`. Turetim
     gerekcesi: repo `O:\\navitas`, canli calisma alani `O:\\navitas-local-train`
     — ikisi KARDES dizinlerdir ve bu yerlesim `ayarlar.py`de de varsayilir
     (`REPO = Path(r"O:\\navitas")`). Ciplak mutlak yol GOMULMEZ; makine
     degisirse ortam degiskeni yeter.
  6. POZITIF KONTROL: ayrisan bir cift YAKALANIR (gecici dizinlerle sinanir;
     gercek dosyalara DOKUNULMAZ).
  7. KAPSAM: bu test YALNIZ IKI TARAFTA DA VAR OLAN ciftleri kiyaslar.
     Yalnizca canlida bulunan betikler **bu testin konusu DEGILDIR** — o
     eksik **T113**'tur. (Olculdu: canlida 105 `.py`, repoda 37; 68 `.py`
     yalniz canlida. ⚠ T113'un "46" sayisi NUMARALI betikleri sayar —
     canlida 82, repoda 36; iki sayi farkli kapsamlardir, celismezler.)
────────────────────────────────────────────────────────────────────────────
"""

import filecmp
import os
import tempfile
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
REPO_AYNA = KOK / "scripts" / "olcum"


def canli_kok():
    """Canli olcum dizini — TEK KAYNAK (D-189 §3.5)."""
    ortam = os.environ.get("NAVITAS_OLCUM_KOK")
    if ortam:
        return Path(ortam)
    return KOK.parent / "navitas-local-train"


def ayna_ciftleri(repo_dizin, canli_dizin):
    """Iki tarafta da AYNI ADLA bulunan `*.py` -> [(repo_yolu, canli_yolu)].

    Liste ELLE TUTULMAZ (D-189 §3.1): dizin taranir. `__pycache__` haric.
    """
    if not Path(repo_dizin).is_dir() or not Path(canli_dizin).is_dir():
        return []
    repo = {p.name: p for p in Path(repo_dizin).glob("*.py")
            if "__pycache__" not in p.parts}
    canli = {p.name: p for p in Path(canli_dizin).glob("*.py")
             if "__pycache__" not in p.parts}
    return [(repo[ad], canli[ad]) for ad in sorted(repo.keys() & canli.keys())]


def ayrisan_ciftler(repo_dizin, canli_dizin):
    """Bayt bazinda AYRISAN ciftler. YON IDDIA ETMEZ — yalniz 'ayni degil' der."""
    return [(r, c) for r, c in ayna_ciftleri(repo_dizin, canli_dizin)
            if not filecmp.cmp(r, c, shallow=False)]


class OlcumAynaSenkronu(unittest.TestCase):

    def _canli_ya_da_atla(self):
        canli = canli_kok()
        if not canli.is_dir():
            self.skipTest(
                f"CANLI OLCUM DIZINI YOK: {canli} — ayna senkronu BU MAKINEDE "
                "sinanamiyor. Bu bir BASARI DEGILDIR; koruma yalnizca "
                "ayrismanin uretilebildigi makinede vardir (D-189 §3.4). "
                "Baska bir yerdeyse `NAVITAS_OLCUM_KOK` ile bildirin.")
        return canli

    # ── ASIL KAPI ─────────────────────────────────────────────────────────
    def test_repo_aynasi_canli_betiklerle_BIREBIR(self):
        canli = self._canli_ya_da_atla()
        ayrisan = ayrisan_ciftler(REPO_AYNA, canli)
        self.assertEqual(
            [], [r.name for r, _c in ayrisan],
            f"{len(ayrisan)} betik AYRISTI. ⚠ Hangisinin dogru oldugu INSAN "
            "KARARIDIR (D-166'da repo, T104'te paket kopyasi dogruydu); test "
            "otomatik onarim YAPMAZ. Elle hizalayin ya da "
            "`scripts/olcum_ayna.py --uygula --repodan|--canlidan` kullanin.")

    def test_VACUITY_KONTROLU_cift_bulundu(self):
        """Sifir cift bulunursa yukaridaki test BOS YERE yesil yanar."""
        canli = self._canli_ya_da_atla()
        ciftler = ayna_ciftleri(REPO_AYNA, canli)
        self.assertGreater(
            len(ciftler), 0,
            f"HIC cift bulunamadi (repo={REPO_AYNA} canli={canli}) — kapi "
            "hicbir sey sinamiyor demektir")

    # ── POZITIF KONTROL ───────────────────────────────────────────────────
    def test_POZITIF_KONTROL_ayrisan_cift_YAKALANIYOR(self):
        """Gercek dosyalara DOKUNULMAZ; gecici dizinlerde sinanir."""
        with tempfile.TemporaryDirectory() as td:
            a, b = Path(td) / "a", Path(td) / "b"
            a.mkdir(), b.mkdir()
            (a / "ayni.py").write_text("x = 1\n", encoding="utf-8")
            (b / "ayni.py").write_text("x = 1\n", encoding="utf-8")
            (a / "farkli.py").write_text("y = 1\n", encoding="utf-8")
            (b / "farkli.py").write_text("y = 2\n", encoding="utf-8")
            (a / "yalniz_repoda.py").write_text("z = 0\n", encoding="utf-8")

            ciftler = ayna_ciftleri(a, b)
            ayrisan = ayrisan_ciftler(a, b)
        self.assertEqual(["ayni.py", "farkli.py"], [r.name for r, _ in ciftler],
                         "yalniz TEK tarafta olan dosya cift SAYILMAMALI")
        self.assertEqual(["farkli.py"], [r.name for r, _ in ayrisan])

    def test_POZITIF_KONTROL_bir_BAYT_farki_bile_yakalaniyor(self):
        """`shallow=False` gercekten icerige bakiyor mu (boyut ayni, icerik farkli)."""
        with tempfile.TemporaryDirectory() as td:
            a, b = Path(td) / "a", Path(td) / "b"
            a.mkdir(), b.mkdir()
            (a / "t.py").write_text("q = 1\n", encoding="utf-8")
            (b / "t.py").write_text("q = 2\n", encoding="utf-8")
            self.assertEqual(
                (a / "t.py").stat().st_size, (b / "t.py").stat().st_size,
                "sinama kurulumu bozuk: boyutlar farkli, `shallow` sinanmiyor")
            self.assertEqual(["t.py"], [r.name for r, _ in ayrisan_ciftler(a, b)])

    def test_dizin_YOKSA_cift_YOK_ve_patlamiyor(self):
        with tempfile.TemporaryDirectory() as td:
            yok = Path(td) / "boyle_bir_dizin_yok"
            self.assertEqual([], ayna_ciftleri(REPO_AYNA, yok))
            self.assertEqual([], ayrisan_ciftler(REPO_AYNA, yok))

    # ── YON IDDIA EDILMEDIGININ KILIDI (D-189 §3.3) ───────────────────────
    def test_bu_kapi_OTOMATIK_ONARIM_YAPMIYOR(self):
        """Test dosyasi kopyalama cagrisi ICERMEZ.

        Yon secmek INSAN KARARIDIR; bir kapinin sessizce "duzeltmesi" yanlis
        tarafi kazandirabilir ve ayrismanin KENDISINI gizler.
        """
        # ⚠ METIN ARAMASI KULLANILMAZ: ilk yazimimda yasak adlari duz metin
        # olarak aradim ve test KENDI yasak listesini yakalayip dustu
        # (oz-referans). AST hem bu tuzagi kaldirir hem daha kesindir:
        # yalniz GERCEK CAGRILARA bakar, yorum/dizgeye degil.
        import ast
        agac = ast.parse(Path(__file__).read_text(encoding="utf-8"))
        yasak_ad = {"copyfile", "copy", "copy2", "replace", "write_bytes",
                    "rename", "move"}
        bulunan = []
        for dugum in ast.walk(agac):
            if isinstance(dugum, ast.Call) and isinstance(dugum.func, ast.Attribute):
                if dugum.func.attr in yasak_ad:
                    bulunan.append(dugum.func.attr)
        self.assertEqual(
            [], bulunan,
            f"ayna testi ONARIM yapiyor gorunuyor: {sorted(set(bulunan))} — "
            "yon secmek INSAN KARARIDIR, kapi sessizce duzeltmemeli")


if __name__ == "__main__":
    unittest.main()
