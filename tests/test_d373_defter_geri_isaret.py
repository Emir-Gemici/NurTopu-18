"""D-373 — CURUTULMUS KAYIT GERI ISARET VERMEK ZORUNDA.

🔴 KUSUR: `REVIEW_LOG.md`'de duzeltmeler **ileri** kayitta yasiyor, ama
**orijinal kayit geri isaret vermiyordu**. `### D-280`'i acan okur, D-285 §3'te
curutulmus bir hukmu **AYAKTA** sanirdi.

Bu 2026-08-31'de iki kez gerceklesti:
  1) D-372 yazildi — D-285 §3'un (2026-08-26) TEKRARI oldugu fark edilmedi.
  2) "Kalan denetim borcu: D-279, D-281, D-282 dogrulanmadi" diye
     raporlandi — oysa D-285 dordunu de bes gun once dogrulamisti.

OLCULDU (duzeltme oncesi): bulunan duzelten/duzeltilen cifti 15, orijinalinde
ileri isaret **0/15**.

⚠ Ayrica: ELLE yazilan liste EKSIK cikti. Once elle 11 cift sayildi; kesif
deseni kosulunca 5 cift daha bulundu (D-43, D-48<-D-60, D-237, D-338, D-345).
D-60 ise D-48'in **sayisini gecersiz ilan etmis**ti. Ders: DESENI LISTEDEN
ONCE KOS.

Bu kapi, yeni bir duzelten kayit yazilip orijinali isaretsiz kalirsa DUSER.
"""
import re
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
DEFTER = KOK / "REVIEW_LOG.md"
METIN = DEFTER.read_text(encoding="utf-8")
SATIRLAR = METIN.splitlines()

ISARET = "⬆ **SONRADAN"          # ⬆ **SONRADAN ...
BASLIK_PENCERESI = 6                  # isaret basliktan hemen sonra gelir
DUZELTME_SOZU = r"ÇÜRÜ|çürü|YANLIŞ|yanlış|DÜZELT|düzelt|GEÇERSİZ|geçersiz"


def _kayit_yerleri(satirlar):
    yer = {}
    for i, s in enumerate(satirlar):
        m = re.match(r"^### (D-\d+)\b", s)
        if m:
            yer.setdefault(m.group(1), i)
    return yer


def _ciftler(satirlar):
    """(duzeltilen, duzelten) ciftlerini KESFET — elle liste tutulmaz."""
    bulunan = set()
    for s in satirlar:
        # (A) D-285 kalibi: "#### 2. D-279 — KISMEN -> duzeltme"
        m = re.match(r"^#### \d+\. (D-\d+) — .*düzelt", s)
        if m:
            bulunan.add((m.group(1), "alt-bolum"))
            continue
        # (B) baslik kalibi: "### D-342 ... D-341'IN ANA IDDIASI CURUTULDU"
        m = re.match(r"^### (D-\d+) ", s)
        if m and re.search(DUZELTME_SOZU, s):
            kendi = m.group(1)
            for h in re.findall(r"D-(\d+)", s):
                if "D-" + h != kendi:
                    bulunan.add(("D-" + h, kendi))
    return bulunan


def _isaretsizler(satirlar):
    """Isaret VAR olmasi yetmez — DUZELTEN KAYDI ANMASI gerekir.

    Sebep: D-48'in `-> D-51` isareti vardi ama D-60'i anmiyordu; oysa D-60
    D-48'in **sayisini gecersiz ilan etmisti**. "Bir isaret var" yeterli
    olsaydi bu kapi o kusuru GORMEZDI.
    """
    yer = _kayit_yerleri(satirlar)
    eksik = []
    for duzeltilen, duzelten in sorted(_ciftler(satirlar)):
        i = yer.get(duzeltilen)
        if i is None:                      # kayit yok — ayri testin isi
            continue
        blok = "\n".join(s for s in satirlar[i:i + BASLIK_PENCERESI]
                         if ISARET in s)
        if not blok:
            eksik.append((duzeltilen, duzelten))
        elif duzelten != "alt-bolum" and duzelten not in blok:
            eksik.append((duzeltilen, duzelten))
    return eksik


class DefterGeriIsaret(unittest.TestCase):
    def test_capa_DEFTER_OKUNUYOR(self):
        self.assertTrue(DEFTER.is_file())
        self.assertGreater(METIN.count("### D-"), 300,
                           "defter beklenenden kucuk — capa tutmuyor")

    def test_KESIF_BOS_DEGIL(self):
        """BOS KAPI OLMASIN: desen gercekten cift buluyor mu (TEST_SPECS §4.1)."""
        c = _ciftler(SATIRLAR)
        self.assertGreaterEqual(
            len(c), 15,
            "kesif deseni cift bulamiyor — kapi BOS calisiyor olabilir")

    def test_HER_CURUTULEN_KAYIT_ILERI_ISARET_VERIYOR(self):
        eksik = _isaretsizler(SATIRLAR)
        self.assertEqual(
            [], eksik,
            "su kayitlar sonradan curutuldu/duzeltildi ama basliklarinin "
            "altinda ileri isaret YOK — okur curutulmus hukmu AYAKTA sanar "
            "(D-373):\n  " + "\n  ".join(f"{o} <- {d}" for o, d in eksik))

    def test_ISARET_KAYDIN_KENDI_NUMARASINI_ANMAZ(self):
        """Isaret baska bir kayda gostermeli; kendine gosteren isaret bos."""
        yer = _kayit_yerleri(SATIRLAR)
        for kayit, i in yer.items():
            for s in SATIRLAR[i:i + BASLIK_PENCERESI]:
                if ISARET in s:
                    hedefler = set(re.findall(r"D-\d+", s))
                    self.assertTrue(
                        hedefler - {kayit},
                        f"{kayit} isareti baska bir kayda gostermiyor")


class MutasyonKontrolu(unittest.TestCase):
    """Kapi GERCEKTEN ayirt ediyor mu — isaret kaldirilinca DUSMELI."""

    def test_BIR_ISARET_SILININCE_KAPI_DUSUYOR(self):
        eksik_once = _isaretsizler(SATIRLAR)
        self.assertEqual([], eksik_once, "on kosul: su an eksik olmamali")

        # ilk isaret satirini SIL (mutasyon)
        mutant = list(SATIRLAR)
        for i, s in enumerate(mutant):
            if ISARET in s:
                del mutant[i]
                break
        else:
            self.fail("defterde hic isaret yok — mutasyon uygulanamadi")

        self.assertNotEqual(SATIRLAR, mutant, "MUTASYON UYGULANMADI (D-370)")
        self.assertNotEqual(
            [], _isaretsizler(mutant),
            "isaret silindigi hâlde kapi gormuyor — BOS KAPI")

    def test_YENI_DUZELTEN_KAYIT_EKLENINCE_KAPI_DUSUYOR(self):
        """Gelecekteki asil senaryo: isaretsiz yeni bir duzeltme yazilir."""
        sentetik = "### D-999 · D-43'İN ANA İDDİASI ÇÜRÜTÜLDÜ (sentetik)"
        # ⚠ mutasyonun GERCEKTEN uygulandigini once dogrula (D-370 dersi):
        # ASCII'ye duz yazilan bir desen ("CURUTULDU") kesfe HIC takilmaz.
        self.assertTrue(re.search(DUZELTME_SOZU, sentetik),
                        "sentetik satir kesif desenine uymuyor — MUTASYON "
                        "UYGULANMADI, kapi bos olculurdu (D-370)")
        mutant = list(SATIRLAR) + [sentetik]
        self.assertIn(("D-43", "D-999"), _ciftler(mutant),
                      "sentetik cift kesfedilemedi — mutasyon etkisiz")
        eksik = _isaretsizler(mutant)
        self.assertIn(
            "D-43", [o for o, _ in eksik],
            "yeni bir duzelten kayit yazildi, orijinali isaretsiz kaldi ve "
            "kapi GORMEDI — bu kapinin var olma sebebi tam olarak budur")


if __name__ == "__main__":
    unittest.main()
