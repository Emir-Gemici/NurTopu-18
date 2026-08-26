"""T123 KAPISI: geçiş yordamının KODU METIN OLARAK DEGIL, KOSULARAK sinanir.

🔴 NEDEN VAR (T123'te olculdu): `tests/test_kilavuz_gecis_yordami.py` yordami
7 testle kilitliyordu — ama ADLARI ve METNI. Kodun KENDISI hic kosulmamisti ve
G2 adimi SAHA GUNU COKERDI:

    beklenen = man["paket_icerigi"].get("models/" + ad)
    -> AttributeError: 'list' object has no attribute 'get'

Iki hata bir satirda: (1) `paket_icerigi` SOZLUK DEGIL LISTEDIR,
(2) anahtarlari CIPLAK dosya adidir, `"models/"` oneki YOKTUR.

G2, *"bozuk yedekle gecme"* KAPISIDIR. Coktugunde operatorun onunde iki kotu
secenek kalir: kapiyi ATLAYIP dogrulanmamis yedekle gecmek, ya da tikanmak.
Bu, T104/D-193'un birebir tekrari olurdu — orada da kilavuz var olmayan bir
yapiya isaret ediyordu ve kurulum ImportError alirdi. O dosyanin kendi
docstring'i bu riski YAZIYORDU; yine de metin kilidi yakalamadi. Ders:
**calistirilabilir bir yordam ancak CALISTIRILARAK kilitlenir.**

YONTEM: G2'nin python blogu kilavuzdan AYIKLANIR ve YALNIZ kok satiri
(`kok = pathlib.Path.home() / "navitas"` — saha yerlesimi) depo yerlesimine
cevrilerek CALISTIRILIR. Baska hicbir satir degistirilmez ve bu testle
DOGRULANIR; aksi halde mantik sessizce baypas edilebilirdi.
"""

from __future__ import annotations

import io
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
KILAVUZLAR = (KOK / "JETSON_KILAVUZ.md",
              KOK / "jetson_paket" / "JETSON_KILAVUZ.md")
PAKET = KOK / "jetson_paket"
KUNYE = PAKET / "models" / "jetson_derleme_manifest.json"


def g2_blogu(kilavuz: Path) -> str:
    """G2 basligindan sonraki ILK `python3 - <<'PY' ... PY` blogunu ayikla."""
    metin = kilavuz.read_text(encoding="utf-8")
    i = metin.find("### G2")
    if i < 0:
        raise AssertionError(f"G2 basligi yok: {kilavuz}")
    m = re.search(r"python3 - <<'PY'\n(.*?)\nPY\n", metin[i:], re.S)
    if not m:
        raise AssertionError(f"G2 python blogu yok: {kilavuz}")
    return m.group(1)


def kok_satirini_cevir(kod: str, yeni_kok: Path) -> tuple[str, int]:
    """Saha kokunu depo kokune cevir. -> (kod, degisen_satir_sayisi)."""
    yeni = kod.replace(
        'kok = pathlib.Path.home() / "navitas"',
        f'kok = pathlib.Path(r"{yeni_kok}")')
    fark = sum(1 for a, b in zip(kod.splitlines(), yeni.splitlines()) if a != b)
    return yeni, fark


class G2KosulabilirTests(unittest.TestCase):
    """G2 CALISIYOR mu — metin degil, ICRA."""

    def test_g2_blogu_IKI_KILAVUZDA_da_var_ve_AYNI(self):
        a, b = (g2_blogu(k) for k in KILAVUZLAR)
        self.assertEqual(a, b, "iki kilavuzun G2 kodu AYRISMIS")

    def test_g2_KOSUYOR_ve_PATLAMIYOR(self):
        """🔴 Asil kapi: onceki surum burada AttributeError ile duserdi."""
        kod, fark = kok_satirini_cevir(g2_blogu(KILAVUZLAR[0]), PAKET)
        self.assertEqual(1, fark, "kok satirindan BASKA satir degistirildi — "
                                  "yordamin mantigi baypas edilmis olabilir")
        cikti = io.StringIO()
        import contextlib
        with contextlib.redirect_stdout(cikti):
            exec(compile(kod, "<G2>", "exec"), {"__name__": "__g2__"})
        self.assertTrue(cikti.getvalue().strip(), "G2 hicbir sey basmadi")

    def test_g2_YEDEGI_OK_diye_dogruluyor(self):
        kod, _ = kok_satirini_cevir(g2_blogu(KILAVUZLAR[0]), PAKET)
        cikti = io.StringIO()
        import contextlib
        with contextlib.redirect_stdout(cikti):
            exec(compile(kod, "<G2>", "exec"), {"__name__": "__g2__"})
        c = cikti.getvalue()
        self.assertIn("OK", c)
        self.assertNotIn("UYUSMAZ", c,
                         "paketteki yedek dosyalari kunyeyle UYUSMUYOR")

    def test_MUTASYON_kunyedeki_sha_bozulursa_UYUSMAZ_der(self):
        """POZITIF KONTROL: G2 gercekten KIYASLIYOR mu, yoksa hep OK mi diyor?

        Gercek pakete DOKUNULMAZ; gecici bir kopyada kunye bozulur (D-233:
        mutasyon gercek dosyada yapilmaz).
        """
        with tempfile.TemporaryDirectory() as d:
            sahte = Path(d) / "jetson_paket"
            (sahte / "models").mkdir(parents=True)
            man = json.loads(KUNYE.read_text(encoding="utf-8"))
            # 🔴 Yedek ADLARI yordamdan TURETILIR, elle YAZILMAZ. Onceki surumde
            # burada "navitas_seg_v34_best" CIVILIYDI; 2026-08-26'da yedek v34 ->
            # v35 olunca mutasyon v34'u bozuyor, G2 ise v35'i ariyordu ve test
            # FileNotFoundError ile patliyordu — elle listenin bayatlamasi
            # (D-146/157/159/163) bu dosyanin kendi docstring'inde uyarilan sinif.
            yedekler = re.findall(r'"(navitas_seg_v\d+_best[^"]*)"',
                                  g2_blogu(KILAVUZLAR[0]))
            self.assertTrue(yedekler, "yordamda yedek dosya adi YOK")
            for x in man["paket_icerigi"]:
                if x["dosya"] in yedekler:
                    x["sha256"] = "0" * 64          # 🔴 MUTASYON
            (sahte / "models" / "jetson_derleme_manifest.json").write_text(
                json.dumps(man, ensure_ascii=False), encoding="utf-8")
            for ad in yedekler:
                kaynak = PAKET / "models" / ad
                if kaynak.exists():
                    shutil.copy2(kaynak, sahte / "models" / ad)
            kod, _ = kok_satirini_cevir(g2_blogu(KILAVUZLAR[0]), sahte)
            cikti = io.StringIO()
            import contextlib
            with contextlib.redirect_stdout(cikti):
                exec(compile(kod, "<G2>", "exec"), {"__name__": "__g2__"})
        self.assertIn("UYUSMAZ", cikti.getvalue(),
                      "kunye BOZULDUGU HALDE G2 OK dedi — kapi bos")


class YedekPaketteTests(unittest.TestCase):
    """Yedek gercekten pakette mi — yordam onu VARSAYIYOR."""

    def setUp(self):
        self.man = json.loads(KUNYE.read_text(encoding="utf-8"))
        self.kunye = {x["dosya"]: x for x in self.man["paket_icerigi"]}

    def test_kunye_LISTE_bicimindedir(self):
        """G2'nin kusuru bu sekilden dogdu; sekil degisirse kod da degismeli."""
        self.assertIsInstance(self.man["paket_icerigi"], list)
        self.assertIn("dosya", self.man["paket_icerigi"][0])
        self.assertIn("sha256", self.man["paket_icerigi"][0])

    def test_BIRINCIL_ve_YEDEK_ikisi_de_pakette(self):
        birincil = self.man["asil_model_pt"]
        self.assertIn(birincil, self.kunye, "BIRINCIL kunyede yok")
        self.assertTrue((PAKET / "models" / birincil).exists())
        # Yedek adi yordamdan TURETILIR, elle yazilmaz
        kod = g2_blogu(KILAVUZLAR[0])
        yedekler = re.findall(r'"(navitas_seg_v\d+_best[^"]*)"', kod)
        self.assertTrue(yedekler, "yordamda yedek dosya adi YOK")
        for ad in yedekler:
            self.assertIn(ad, self.kunye, f"YEDEK kunyede yok: {ad}")
            self.assertTrue((PAKET / "models" / ad).exists(),
                            f"YEDEK dosyasi pakette yok: {ad}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
