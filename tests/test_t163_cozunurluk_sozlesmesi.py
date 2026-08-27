"""T163 KAPISI (ON_KAYIT SS29 · REVIEW_LOG D-308): `CONTRACTS.md SS8` cozunurluk
sozlesmesi URETIMLE celisemez.

KUSUR: SS8 kalin harflerle "Cikarim `imgsz` = 640. Degistirmek guvenli DEGILDIR"
diyordu; uretim ise v27'den beri 512'de kosuyordu. Yani sozlesme KENDI URETIMINI
yasakliyordu ve sahadaki bir kisi o satiri okuyup 640'a cevirseydi KABUL
EDILMEMIS bir cozunurlukte kosardi. JETSON kilavuzunun bayatligini T154/T157/T158
kapatmisti; `CONTRACTS.md`ye bakan kapi YOKTU.

BOS KAPI YASAGI (TEST_SPECS SS4.1): "duzelttim" demek yetmez. Kapi
  (1) SS8'in beyan ettigi cozunurlugun DEFTERDEKI ile ayni oldugunu,
  (2) SS8'te URETIM iddiasi tasiyan CIPLAK bir sayi kalmadigini,
  (3) olcum dosyasinin durdugunu ve tablodaki hukmun sayilarla tutarli oldugunu
kilitler; mutasyonda (SS8'e baska bir sayi ya da eski cumle yazilinca) DUSER.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
SOZLESME = KOK / "CONTRACTS.md"
DEFTER = KOK / "config" / "model_registry.json"
OLCUM = KOK / "results" / "t163" / "olcum.json"


# 🔴 DAR ISTISNA (gerekce zorunlu, satir bazli): SS8 kendi BAYATLIK KAYDINI
# tasiyor ve eski yasak cumlesini ALINTILIYOR. Alinti kanit zinciridir, silinmez.
# Ama istisna GENIS OLAMAZ: yalnizca asagidaki isaretlerden birini TASIYAN
# satirda gecerlidir. Isaretsiz bir satirda uretim disi bir `imgsz = N` iddiasi
# CANLI beyandir ve kapi DUSER (Mutasyon sinifi bunu kanitlar).
TARIHSEL_ISARETLER = ("TARİHSEL", "DÜZELTİLDİ", "diyordu", "önceki hâli")


def _ss8_metni() -> str:
    metin = SOZLESME.read_text(encoding="utf-8")
    bas = metin.index("## 8. Çözünürlük sözleşmesi")
    son = metin.index("## 9.", bas)
    return metin[bas:son]


def _canli_iddialar(metin: str):
    """SS8'deki CANLI `imgsz = N` beyanlari (tarihsel isaretli satirlar HARIC)."""
    cikti = []
    for satir in metin.splitlines():
        if any(isaret in satir for isaret in TARIHSEL_ISARETLER):
            continue
        cikti.extend(int(x) for x in
                     re.findall(r"`?imgsz`?\s*=\s*(\d{3,4})", satir))
    return sorted(set(cikti))


def _defterdeki_imgsz() -> int:
    d = json.loads(DEFTER.read_text(encoding="utf-8"))
    return int(d["profiles"]["competition"]["imgsz"])


class SozlesmeDefterleHizali(unittest.TestCase):

    def test_SS8_defterdeki_imgsz_i_gosteriyor(self):
        ss8 = _ss8_metni()
        imgsz = _defterdeki_imgsz()
        self.assertIn(str(imgsz), ss8,
                      f"SS8 uretim cozunurlugunu ({imgsz}) hic anmiyor")
        self.assertIn("model_registry.json", ss8,
                      "SS8 tek kaynagi (kayit defteri) gostermiyor")

    def test_SS8_ESKI_yasak_cumlesini_TASIMIYOR(self):
        """`imgsz = 640` bicimindeki URETIM IDDIASI geri gelemez."""
        ss8 = _ss8_metni()
        imgsz = _defterdeki_imgsz()
        # "imgsz = <sayi>" kalibi: yalniz defterdeki sayi gecerlidir.
        yabanci = sorted(set(_canli_iddialar(ss8)) - {imgsz})
        self.assertEqual([], yabanci,
                         f"SS8 hâlâ uretim disi bir cozunurluk ilan ediyor: "
                         f"{yabanci} (defter {imgsz})")

    def test_TARIHSEL_tablo_SILINMEDI(self):
        """Eski olcum kanit zinciridir; etiketlenir ama silinmez."""
        ss8 = _ss8_metni()
        self.assertIn("TARİHSEL", ss8, "v17 donemi tablosu etiketsiz/silinmis")
        self.assertIn("0,861", ss8, "v17 olcumu SS8'den dusurulmus")


class OlcumKaydi(unittest.TestCase):

    def setUp(self):
        if not OLCUM.is_file():
            self.skipTest("T163 olcum dosyasi yok")
        self.veri = json.loads(OLCUM.read_text(encoding="utf-8"))

    def test_uretim_cozunurlugu_olculdu(self):
        imgsz = _defterdeki_imgsz()
        self.assertIn(str(imgsz), self.veri["cozunurlukler"],
                      "uretim cozunurlugu supurmede YOK")
        self.assertEqual(imgsz, self.veri["uretim_imgsz"])

    def test_hukum_sayilarla_tutarli(self):
        """SS8.1'in 'uretim en yuksek ROTA + serit' hukmu olcumle dogrulanir."""
        imgsz = str(_defterdeki_imgsz())
        kolonlar = self.veri["cozunurlukler"]
        uretim = kolonlar[imgsz]
        for ad, k in kolonlar.items():
            with self.subTest(imgsz=ad):
                self.assertLessEqual(
                    k["rota"], uretim["rota"],
                    f"{ad} uretimden COK rota veriyor — SS8.1 hukmu bayatladi")
                self.assertLessEqual(
                    k["serit_dogru"], uretim["serit_dogru"],
                    f"{ad} uretimden COK dogru serit veriyor — SS8.1 bayatladi")

    def test_her_yeri_boyama_cokusu_YOK(self):
        """SS8.2'nin 'v17 cokusu v36'da tekrarlanmiyor' cumlesinin kaniti."""
        for ad, k in self.veri["cozunurlukler"].items():
            with self.subTest(imgsz=ad):
                self.assertLess(
                    k["kaplama_azami"], 0.90,
                    f"{ad}'de kaplama %90'i asti — SS8.2'deki cumle artik "
                    "yanlis, yeniden yazilmali")


class Mutasyon(unittest.TestCase):
    """Kapi gercekten AYIRT EDIYOR mu — sahte SS8 metinleriyle sinanir."""

    def test_ISARETSIZ_eski_cumle_YAKALANIR(self):
        sahte = "> **Cikarim `imgsz` = 640. Degistirmek guvenli DEGILDIR.**"
        self.assertEqual([640], _canli_iddialar(sahte),
                         "desen isaretsiz yasak cumlesini yakalamiyor — kapi bos")

    def test_ISARETLI_alinti_muaf(self):
        alinti = "Onceki hâli **`imgsz` = 640** diyordu — oysa uretim 512."
        self.assertEqual([], _canli_iddialar(alinti),
                         "tarihsel alinti canli beyan sayildi")

    def test_ISTISNA_GENIS_DEGIL(self):
        """Isaret BASKA bir satirdaysa muafiyet TASMAZ."""
        iki_satir = "Bu bolum DÜZELTİLDİ." + chr(10) + "> **Cikarim `imgsz` = 640.**"
        self.assertEqual([640], _canli_iddialar(iki_satir),
                         "muafiyet satir sinirini asti — istisna genisledi")

    def test_bugunku_metin_temiz(self):
        self.assertEqual([], sorted(set(_canli_iddialar(_ss8_metni()))
                                    - {_defterdeki_imgsz()}))


if __name__ == "__main__":
    unittest.main()
