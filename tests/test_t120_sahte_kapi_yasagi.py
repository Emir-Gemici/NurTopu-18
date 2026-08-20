"""T120 KALICI KAPISI: `tests/` altinda SAHTE KAPI olamaz.

KUSUR IKI KEZ OLDU:
  · D-170 — kapi VARDI ama hic kosmuyordu;
  · T120/D-209 §1 — `test_costmap_on_images.py` kesif tarafindan TOPLANIYOR
    ama ICI BOS: "Ran 0 tests · NO TESTS RAN". Dosya `tests/` altinda, adi
    kalibina uyuyor: disaridan bakan "kapi var" sanir.
Ikinci cesit: `arena_kompozit_kapisi.py` / `t64_hakem_ekrani_kapisi.py`
`test_` onekli DEGIL — varsayilan kesif kalibi (`test*.py`) onlari HIC
gormuyor; "sifir test topluyor" bile denemez, kapsama girmiyorlar.

DEGISMEZ (mimar karari, T120):
    tests/ altindaki HER .py dosyasi ya >=1 test TOPLAR,
    ya da dosyanin KENDI ICINDE gerekceli bir MUAFIYET isareti tasir.

⚠ MUAFIYET LISTESI ELLE TUTULMAZ — dosyanin MODUL DOCSTRING'inden turetilir.
Elle liste bu projede dort kez bayatladi (D-146 · D-157 · D-159 · D-163);
T104'te dogru kalip zaten kuruldu (beklenen liste `KOPYALAR`dan turetiliyordu),
burada ayni kalip kullanilir: kaynak dosyanin KENDISI.

MUAFIYET BICIMI — modul docstring'inde, IKI satir, ikisi de SATIR BASINDA
(girinti YOK). Isaretlerin kendisi asagida `MUAFIYET_ISARETI` ve
`KOSUM_ISARETI` sabitlerinde durur; bicim sudur:
    <isaret> <bos olmayan gerekce>          <- ayni satirda gerekce ZORUNLU
    <kosum isareti> <dosyanin nasil kosuldugu>
`KOSUM` zorunludur: kosulamayan bir "muaf" dosya, muafiyetin arkasina
gizlenmis olu koddur.

🔴 GIRINTI KURALI NEDEN VAR — BU KAPI KENDINI YAKALADI: ilk yazimda bu
docstring bicimi ORNEK olarak yaziyordu ve kapi KENDI docstring'ini muaf
sandi ("HEM test HEM muafiyet -> BAYAT"). T112'deki oz-referans tuzaginin
aynisi. Cozum: isaret YALNIZ girintisiz satirda gecerlidir; anlatim/ornek
metin (girintili) muafiyet URETMEZ.

🔴 SAYIM YONTEMI VE NEDEN AST (olculdu, varsayilmadi):
Kapinin kendisi 63 dosya icin alt surec kosamaz (takim kapisini dakikalarca
bloklar). Bu yuzden AST kullanilir. AST'nin gecerliligi BAGIMSIZ OLARAK
olculdu (T120, 2026-08-20): 63 dosyanin her biri icin
`python -m unittest discover -s tests -p <ad>` ALT SUREC olarak kosuldu ve
"Ran N" satiri AST sayimiyla kiyaslandi -> **63/63 uyum, 0 ayrisma**.
Ham: `results/t120/bagimsiz_sayim.json`.
⚠ ALET UYARISI: ilk iki denemede alt surece `-t <kok>` verilmisti ve 63/63
dosya "sifir test" gorunmustu (ImportError: Start directory is not importable).
Yani olcum aletinin kendisi once YANLIS sonuc uretti; pozitif kontrol
(takimin 677 testi geciyor olmasi) bunu yakaladi. Ayni sinif: T95 prob kusuru.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
TESTS = KOK / "tests"
MUAFIYET_ISARETI = "KESIF MUAFIYETI:"
KOSUM_ISARETI = "KOSUM:"
KESIF_KALIBI = "test"          # unittest varsayilani: `test*.py`


def toplanabilir_test_sayisi(agac: ast.AST) -> int:
    """AST'den toplanabilir test sayisi: TestCase turevlerindeki `test*` metodlar.

    `load_tests` / `suite` / `additional_tests` kancalari da test toplatabilir;
    bunlar varsa dosya "test toplayan" sayilir (sayisi bilinemez -> 1 kabul).
    """
    sayi = 0
    for d in ast.walk(agac):
        if isinstance(d, ast.ClassDef):
            if any("TestCase" in ast.unparse(b) for b in d.bases):
                sayi += sum(
                    1 for g in d.body
                    if isinstance(g, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and g.name.startswith("test"))
        elif isinstance(d, (ast.FunctionDef, ast.AsyncFunctionDef)) and \
                d.name in ("load_tests", "suite", "additional_tests"):
            sayi = max(sayi, 1)
    return sayi


def _isaretli_satir(belge: str, isaret: str) -> str | None:
    """Isaretin GIRINTISIZ satirdaki degeri; yoksa None.

    Girinti kurali oz-referans icindir (bkz. modul docstring'i): anlatim ya da
    ornek metin girintilidir ve muafiyet URETMEZ. Deger AYNI SATIRDAN alinir —
    bir sonraki satira TASMAZ (aksi halde bos gerekce, alttaki satiri gerekce
    sanardi; bu kusur ilk yazimda gercekten olustu).
    """
    for satir in belge.splitlines():
        if satir.startswith(isaret):
            return satir[len(isaret):].strip()
    return None


def muafiyet(agac: ast.AST) -> tuple[bool, str]:
    """(muaf_mi, sebep) — MODUL DOCSTRING'inden TURETILIR, elle listeden DEGIL.

    Gerekce ve KOSUM satiri zorunludur; ikisinden biri eksikse muafiyet
    GECERSIZDIR (yarim isaret, muafiyet degildir) ve sebep AYIRT EDILIR:
    "isaret yok" ile "isaret var ama bozuk" ayni sey degildir.
    """
    # clean=False ZORUNLU: varsayilan `get_docstring` cleandoc uygular ve ORTAK
    # GIRINTIYI SILER — girintili ornek metin sutun 0'a kayar, oz-referans
    # korumasi etkisizlesir. (Bu kusur olculdu: kapi kendi ornegini muaf sandi.)
    belge = ast.get_docstring(agac, clean=False) or ""
    gerekce = _isaretli_satir(belge, MUAFIYET_ISARETI)
    if gerekce is None:
        return False, "isaret yok"
    if not gerekce:
        return False, "BOZUK MUAFIYET: gerekce BOS (isaretle ayni satirda olmali)"
    kosum = _isaretli_satir(belge, KOSUM_ISARETI)
    if kosum is None:
        return False, ("BOZUK MUAFIYET: KOSUM satiri yok — kosulamayan muafiyet "
                       "kabul edilmez")
    if not kosum:
        return False, "BOZUK MUAFIYET: KOSUM satiri BOS"
    return True, gerekce


def dosya_durumu(kaynak: str, ad: str) -> dict:
    """Tek dosyanin kapiya gore durumu. SAF fonksiyon — dosya sistemi yok.

    Bu ayrim bilerek yapildi: kural birim testlerle (sentetik kaynak metinleri)
    HEM pozitif HEM negatif yonde sinanabilsin, gercek depo tarandiginda ise
    ayni kural kosulsun. Iki kopya kural YAZILMAZ.
    """
    try:
        agac = ast.parse(kaynak)
    except SyntaxError as exc:
        return {"ad": ad, "gecerli": False, "sebep": f"parse hatasi: {exc}"}
    n = toplanabilir_test_sayisi(agac)
    muaf, sebep = muafiyet(agac)
    kalipta = ad.startswith(KESIF_KALIBI)
    if n > 0 and muaf:
        return {"ad": ad, "gecerli": False, "test": n, "muaf": True,
                "sebep": "HEM test topluyor HEM muafiyet isareti tasiyor — "
                         "isaret BAYAT, biri kaldirilmali"}
    if n > 0:
        if not kalipta:
            return {"ad": ad, "gecerli": False, "test": n, "muaf": False,
                    "sebep": f"{n} test tasiyor ama adi `{KESIF_KALIBI}*` "
                             "degil — kesif onu HIC toplamaz (olu kapi)"}
        return {"ad": ad, "gecerli": True, "test": n, "muaf": False,
                "sebep": f"{n} test topluyor"}
    if muaf:
        return {"ad": ad, "gecerli": True, "test": 0, "muaf": True,
                "sebep": f"muaf: {sebep}"}
    if sebep.startswith("BOZUK"):
        # "isaret hic yok" ile "isaret var ama bozuk" AYNI SEY DEGILDIR:
        # ikincisi sessizce sahte kapi diye raporlanirsa yazan kisi neyi
        # duzeltecegini bilemez.
        return {"ad": ad, "gecerli": False, "test": 0, "muaf": False,
                "sebep": sebep}
    return {"ad": ad, "gecerli": False, "test": 0, "muaf": False,
            "sebep": "SIFIR test topluyor ve muafiyet isareti YOK (sahte kapi)"}


# ── Kural birim testleri (sentetik kaynak — dosya sistemine dokunmaz) ────────

BOS = '"""Yalniz bir aciklama."""\n'
MUAF = ('"""Aciklama.\n\nKESIF MUAFIYETI: elle kosulan agir arac.\n'
        'KOSUM: python -B tests/x.py --cikti a\n"""\n')
TESTLI = ('"""Aciklama."""\nimport unittest\n\n'
          'class A(unittest.TestCase):\n    def test_x(self):\n        pass\n')


class KuralTests(unittest.TestCase):
    def test_sifir_test_ve_isaretsiz_dosya_DUSER(self):
        d = dosya_durumu(BOS, "test_bos.py")
        self.assertFalse(d["gecerli"])
        self.assertIn("sahte kapi", d["sebep"])

    def test_muafiyet_isaretli_dosya_GECER(self):
        """POZITIF KONTROL: muafiyet mekanizmasi OLU KOD degil."""
        d = dosya_durumu(MUAF, "arac.py")
        self.assertTrue(d["gecerli"], d["sebep"])
        self.assertTrue(d["muaf"])

    def test_test_toplayan_dosya_GECER(self):
        d = dosya_durumu(TESTLI, "test_x.py")
        self.assertTrue(d["gecerli"])
        self.assertEqual(d["test"], 1)

    def test_gerekcesiz_isaret_GECERSIZ(self):
        kaynak = '"""A.\n\nKESIF MUAFIYETI:\nKOSUM: x\n"""\n'
        self.assertFalse(dosya_durumu(kaynak, "a.py")["gecerli"])

    def test_kosumsuz_isaret_GECERSIZ(self):
        kaynak = '"""A.\n\nKESIF MUAFIYETI: sebep var ama kosum yok.\n"""\n'
        d = dosya_durumu(kaynak, "a.py")
        self.assertFalse(d["gecerli"])
        self.assertIn("KOSUM", d["sebep"])

    def test_isaret_yorumda_ise_SAYILMAZ(self):
        """Isaret MODUL DOCSTRING'inde olmali — rastgele yorum yetmez."""
        kaynak = ('# KESIF MUAFIYETI: kacamak\n# KOSUM: x\n'
                  '"""Gercek docstring."""\n')
        self.assertFalse(dosya_durumu(kaynak, "a.py")["gecerli"])

    def test_girintili_ornek_muafiyet_URETMEZ(self):
        """OZ-REFERANS KORUMASI: bicimi ANLATAN dosya muaf olmaz.

        Bu kapinin kendisi ilk yazimda tam buradan dustu (docstring'inde
        bicim ornegi vardi ve kendini muaf sandi) — T112 tuzagi.
        """
        kaynak = ('"""A.\n\n    KESIF MUAFIYETI: bu bir ORNEK.\n'
                  '    KOSUM: ornek komut\n"""\n')
        d = dosya_durumu(kaynak, "a.py")
        self.assertFalse(d["gecerli"])
        self.assertFalse(d["muaf"])

    def test_kalip_disi_ad_ile_test_tasimak_GECERSIZ(self):
        """Kesif KAPSAMI denetimi: `test*` olmayan ad + test = olu kapi."""
        d = dosya_durumu(TESTLI, "kapi.py")
        self.assertFalse(d["gecerli"])
        self.assertIn("kesif onu HIC toplamaz", d["sebep"])

    def test_hem_test_hem_muafiyet_BAYAT_sayilir(self):
        kaynak = TESTLI.replace('"""Aciklama."""',
                                '"""A.\n\nKESIF MUAFIYETI: eski.\nKOSUM: x\n"""')
        d = dosya_durumu(kaynak, "test_x.py")
        self.assertFalse(d["gecerli"])
        self.assertIn("BAYAT", d["sebep"])


# ── Gercek depo taramasi ────────────────────────────────────────────────────

class DepoTaramasiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dosyalar = sorted(p for p in TESTS.glob("*.py")
                              if p.name != "__init__.py")

    def test_tests_altinda_sahte_kapi_YOK(self):
        kotu = []
        for p in self.dosyalar:
            d = dosya_durumu(p.read_text(encoding="utf-8", errors="replace"),
                             p.name)
            if not d["gecerli"]:
                kotu.append(f"{p.name}: {d['sebep']}")
        self.assertEqual(
            kotu, [],
            "tests/ altinda sahte kapi var — her dosya ya >=1 test toplamali "
            "ya da modul docstring'inde 'KESIF MUAFIYETI: <gerekce>' + "
            "'KOSUM: <komut>' tasimali:\n  " + "\n  ".join(kotu))

    def test_tarama_gercekten_dosya_goruyor(self):
        """VAKUM KONTROLU (D-15/K-04): bos kume uzerinde 'gecti' demeyelim."""
        self.assertGreater(len(self.dosyalar), 50,
                           "tests/ taramasi bos/eksik — kapi bir sey sinamiyor")

    def test_muafiyet_mekanizmasi_gercek_kullanimda(self):
        """Muafiyet OLU KOD degil: en az bir GERCEK dosya onu tasiyor."""
        muaflar = [p.name for p in self.dosyalar
                   if dosya_durumu(p.read_text(encoding="utf-8",
                                               errors="replace"),
                                   p.name).get("muaf")]
        self.assertTrue(muaflar, "hicbir dosya muafiyet tasimiyor")

    def test_muaf_dosyalarin_kosum_komutu_var_olan_dosyayi_gosteriyor(self):
        """Muafiyetin KOSUM satiri kendi dosyasini isaret etmeli (bayat yol yok)."""
        for p in self.dosyalar:
            kaynak = p.read_text(encoding="utf-8", errors="replace")
            d = dosya_durumu(kaynak, p.name)
            if not d.get("muaf"):
                continue
            belge = ast.get_docstring(ast.parse(kaynak)) or ""
            _, _, kalan = belge.partition(KOSUM_ISARETI)
            satir = kalan.strip().splitlines()[0]
            self.assertIn(p.name, satir,
                          f"{p.name}: KOSUM satiri kendi dosyasini gostermiyor "
                          f"-> {satir}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
