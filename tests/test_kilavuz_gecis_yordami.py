"""T123 KAPISI: iki JETSON_KILAVUZ'daki BIRINCIL->YEDEK GECIS YORDAMI kilitli.

NEDEN (D-211 §5 + mimar T123 emri): Jetson saha kurulumuyla AYNI GUN geliyor;
birincil aday sahada duserse gecis EL YORDAMIYLA yapilamaz. Kurulum yordami
T104 ile kilitliydi; GECIS yordami hic yoktu — bu dosya onu kilitler.

T104 dersleri aynen uygulanir:
  · Beklenen adlar ELLE YAZILMAZ — yordam metninden ve paket kaynaklarindan
    TURETILIR (elle liste bu projede tekrar tekrar bayatladi: D-146/157/159/163).
  · Iki kilavuz FARKLI baglam anlatabilir ama YORDAM AYNI olmak zorundadir.
  · Yordamin atif ettigi dosya/fonksiyon/alan adlari GERCEK olmali —
    T104/D-193'te kilavuz var olmayan yapiya isaret ediyordu ve saha kurulumu
    ImportError alirdi. Ayni sinif kusur burada da mumkun.
"""

from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
KILAVUZLAR = (KOK / "JETSON_KILAVUZ.md",
              KOK / "jetson_paket" / "JETSON_KILAVUZ.md")
BASLIK = "## 6C. BİRİNCİL→YEDEK MODEL GEÇİŞ YORDAMI"

for p in (KOK / "codes", KOK / "scripts"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


def bolum(metin: str) -> str:
    """6C bolumunu (bir sonraki '## ' basligina kadar) dondur."""
    i = metin.index(BASLIK)
    kalan = metin[i + len(BASLIK):]
    j = kalan.find("\n## ")
    return kalan if j < 0 else kalan[:j]


class GecisYordamiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.metinler = {p: p.read_text(encoding="utf-8") for p in KILAVUZLAR}

    def test_bolum_iki_kilavuzda_da_var(self):
        for p, m in self.metinler.items():
            self.assertIn(BASLIK, m, f"{p.name}: gecis yordami bolumu YOK")

    def test_adim_kumesi_iki_kilavuzda_ayni_ve_bos_degil(self):
        kumeler = {}
        for p, m in self.metinler.items():
            adimlar = re.findall(r"^### (G\d+)", bolum(m), re.M)
            self.assertTrue(adimlar, f"{p}: 6C icinde hic G-adimi yok")
            kumeler[str(p)] = adimlar        # iki kilavuzun BASENAME'i ayni!
        (a1, s1), (a2, s2) = kumeler.items()
        self.assertEqual(s1, s2, f"adim kumeleri ayristi: {a1}={s1} {a2}={s2}")

    def test_yordamin_cekirdek_islevleri_var(self):
        """Gecis yordami DOGRULAMA ve GERI ALMA icermeden yordam sayilmaz.

        Bunlar elle liste degil ISLEV degismezleridir: dogrulamasiz gecis
        fail-dangerous, geri almasiz gecis tek yonlu kumar olur.
        """
        for p, m in self.metinler.items():
            b = bolum(m)
            self.assertIn("model_kayit_dogrula", b,
                          f"{p.name}: dogrulama zinciri defter kapisina baglanmamis")
            self.assertIn("GERİ ALMA", b, f"{p.name}: geri alma adimi yok")
            self.assertIn("D-133", b, f"{p.name}: 'karar insanin' siniri kayip")

    def test_atif_yapilan_paket_dosyalari_paketin_tasidiklari(self):
        """Yordamdaki dosya atiflari paketleyicinin KOPYALAR'indan/paketten dogrulanir."""
        from jetson_paket_hazirla import KOPYALAR
        tasinanlar = {h.name for h in KOPYALAR.values()} | {
            p.name for p in (KOK / "jetson_paket").rglob("*") if p.is_file()}
        for p, m in self.metinler.items():
            b = bolum(m)
            # Yalniz PAKET-topolojili atiflar sinanir (scripts/, models/,
            # config/, kod/ onekli). Depo-tarafi atiflar (tests/...,
            # REVIEW_LOG vb.) paketin tasima yukumlulugu degildir.
            atiflar = set(re.findall(
                r"(?:scripts|models|config|kod)/([\w.]+\.(?:py|json))", b))
            atiflar = {a for a in atiflar if not a.startswith("<")}
            for ad in sorted(atiflar):
                self.assertIn(
                    ad, tasinanlar,
                    f"{p.name}: yordam '{ad}' dosyasina isaret ediyor ama paket"
                    f" onu TASIMIYOR (T104/D-193 sinifi kusur)")

    def test_dogrulama_fonksiyonu_gercekten_tanimli(self):
        import rpi_inference
        self.assertTrue(hasattr(rpi_inference, "model_kayit_dogrula"),
                        "yordamin dayandigi model_kayit_dogrula artik yok")

    def test_json_alan_atiflari_gercek(self):
        """Yordamda gecen defter/kunye alan adlari gercek dosyalarda VAR."""
        reg = json.loads((KOK / "jetson_paket" / "config" /
                          "model_registry.json").read_text(encoding="utf-8"))
        man = json.loads((KOK / "jetson_paket" / "models" /
                          "jetson_derleme_manifest.json").read_text(encoding="utf-8"))
        comp = reg["profiles"]["competition"]
        b = bolum(self.metinler[KILAVUZLAR[0]])
        for alan in re.findall(r"`(model_id|path|sha256|imgsz)`", b):
            self.assertIn(alan, comp, f"registry profilinde '{alan}' alani yok")
        for alan in re.findall(r"`(asil_model_pt|asil_model|paket_icerigi)`", b):
            self.assertIn(alan, man, f"manifestte '{alan}' alani yok")

    def test_yer_tutucu_tutarli(self):
        """<YEDEK> ya hic kalmamistir (dolduruldu) ya da G2 ve G6'da birlikte durur."""
        for p, m in self.metinler.items():
            b = bolum(m)
            g2 = "<YEDEK>" in b.split("### G3")[0]
            g6 = "<YEDEK>" in (b.split("### G6")[1] if "### G6" in b else "")
            self.assertEqual(
                g2, g6,
                f"{p.name}: <YEDEK> yer tutucusu yarim doldurulmus (G2={g2}, G6={g6})")


if __name__ == "__main__":
    unittest.main(verbosity=2)
