"""T119 KAPISI: ayirt edici sahnede YAYINLANAN `road` DEGERI assert edilir.

Kusur zemini (Filo 3 mutasyon supurmesi + mimar hukmu D-209):
  `test_rota_serit_etiketi.py` ayirt edici zikzak sahnesinde yalniz `olcum`
  sozlugunun ALANLARINI (`darbogaz_serit`, `baskin_serit`) sinar; analyze_path
  cagrisinin YAYINLADIGI `yol` degerini o sahnede hic assert etmez. Sonuc:
  yayin hattina uygulanan bir alan mutasyonundan o dosyada SIFIR test dusuyordu
  (0/21) — yayin hatti fiilen korumasizdi.

BU DOSYANIN DEGISMEZ GOREVI: yayin hattini KORUMAK. Hangi alan yayinlanirsa
yayinlansin, o hatta uygulanan mutasyon BU DOSYADAN test dusurmelidir.

────────────────────────────────────────────────────────────────────────────
🔴 SOZLESME DEGISTI — T155 · 2026-08-26 · REVIEW_LOG D-296
────────────────────────────────────────────────────────────────────────────
Yayinlanan alan `darbogaz_serit` -> `serit_karari` (rotanin GOVDESI) oldu.
Bu dosyanin ONCEKI surumu bunun TERSINI assert ediyordu; asagidaki degisiklik
bir kapi GEVSETMESI DEGIL, kapinin YENI SOZLESMEYE nisanlanmasidir. Gerekce
ve karsi kanit ACIKCA burada durur:

LEHTE (degisikligi zorunlu kilan olcum, ON_KAYIT SS17 · results/t155/):
  Yer gercekli 15 arena sahnesinde (yer gercegi = URETECIN acik biraktigi
  guzergah, algoritmadan GIZLI) yayinlanan `road`:
      darbogaz_serit  6/15      serit_karari (govde)  15/15
  Ornek: harita 1/kolay, rota piksel dagilimi 419/3/0 — yayinlanan sayi 2'ydi,
  yani 422 pikselin 3'u kararı belirliyordu. Darbogaz 15 sahnenin 13'unde
  rotanin UCUNDA olculuyordu (y=39 / y=460), yani KB/HB yakininda uc guzergahin
  BIRLESTIGI, serit kimliginin TANIMSIZ oldugu yerde.

ALEYHTE (bu dosyanin kendi sahnesi — KAYIT ICIN DURUYOR):
  Asagidaki `_zikzak` sahnesinde alt/ust dikeyler serit 3'te, tek gecis ise
  serit 1'deki dar kapidadir. "Tek gecis hangi seritte" sorusunun cevabi 1'dir
  ve YENI sozlesme burada 3 yayinlar. Yani iki tanim bu sahnede CELISIR.

CELISKININ COZUMU — MIMARIN KARARINA BIRAKILDI (T155 raporu, acik soru):
  Iki tanim AYNI ismi (`road`) tasiyan IKI FARKLI soruyu yanitliyor:
    · "hangi guzergah acik"        -> govde  (arena geometrisi, sartname §2.2.3)
    · "darbogaz hangi seritte"     -> darbogaz (zikzak gibi orgu sahneler)
  Sartnamenin sordugu soru BIRINCISIDIR ve arena uc koridoru PARALELDIR: acik
  rota govdesiyle tek seritte kalir. `_zikzak` gibi uc seride BIRDEN yayilan
  dengeli bir rota arena geometrisinde OLUSMAZ.
  ⚠ Ayrica olculdu: `rota_bul` (bagimsiz karar yolu, arena'da 15/15) bu
  sahnelerin HICBIRINDE karar vermiyor — dordunde de `BELIRSIZ_TEK_KAPI`,
  `yol_no=None`. Yani zikzak celiskisinde HAKEMLIK YAPAMAZ; celiski ancak
  sozlesme duzeyinde cozulur.
  ONERILEN TAKIP (ayri on kayit ister, bu turda GIRMEDI): rota gercekten uc
  seride dengeli yayildiginda tek etiket yayinlamak yerine FAIL-CLOSED durmak
  — `rota_bul`un bu sahnelerde zaten yaptigi sey. Gercek karede ret oranini
  degistirecegi icin GPU'lu olcum olmadan baglanmaz.

Sahne ureticisi `test_rota_serit_etiketi._zikzak`ten IMPORT edilir — kopya
tutulmaz (tekrarlayan kusur sinifi: "iki kopya, yalniz biri zorlaniyor").
Cross-import emsali: `test_costmap_on_images.py:37`.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
if str(KOK / "codes") not in sys.path:
    sys.path.insert(0, str(KOK / "codes"))
if str(KOK / "tests") not in sys.path:
    sys.path.insert(0, str(KOK / "tests"))

from test_rota_serit_etiketi import _zikzak  # noqa: E402
from rpi_inference import analyze_path  # noqa: E402

# Kapinin yarim genisligi gate disindaki koridorlardan (dt yaricapi ~24 px,
# 48 px yukseklikli yatay bantlar) BELIRGIN kucuk kalsin diye dar kapilar:
# 16 px -> yaricap ~8, 24 px -> ~12. Boylece darbogaz KESIN kapidadir.
DAR_KAPILAR = (16, 24)
TUM_KAPILAR = (16, 24, 48, 64)
KAPI_SERIDI = 1          # _zikzak'in tek gecisi: serit 1'deki kapi
GOVDE_SERIDI = 3         # alt/ust dikeyler + rota kutlesi serit 3'te


def _kos(kapi_px):
    yol, guven, wps, koridor, ret, olc = analyze_path(
        _zikzak(kapi_px), n_waypoints=8, return_clean=True,
        return_reason=True, return_olcum=True, min_area_ratio=0.001)
    return yol, olc


class T119YayinlananRoadTests(unittest.TestCase):
    """Yayinlanan `road`, ayirt edici sahnede DEGER olarak sozlesmeye uyuyor mu?"""

    def test_zikzak_yayinlanan_road_govde_serididir(self):
        """KAPI: zikzakta yayinlanan deger = rotanin GOVDE seridi (3).

        Bagimsiz kahin: sahnenin rota kutlesi alt/ust dikeylerdedir ve onlar
        serit 3'tedir (`test_zikzak_sahne_gecerliligi_govde_hala_uc` bunu
        ayrica dogrular). Yayin `darbogaz_serit` uzerinden yapilsaydi DAR
        kapilarda bu test DUSERDI — alan adina degil YAYINLANAN DEGERE bakar.

        ⚠ Bu sahnede "tek gecis serit 1'de" de DOGRU bir ifadedir; dosya
        basligindaki celiski notu bu testin sinirini anlatir.
        """
        olculen = 0
        for kapi_px in TUM_KAPILAR:
            with self.subTest(kapi_px=kapi_px):
                yol, olc = _kos(kapi_px)
                if yol is None or olc is None:
                    continue
                olculen += 1
                self.assertEqual(
                    yol, GOVDE_SERIDI,
                    f"kapi_px={kapi_px}: rota govdesi serit {GOVDE_SERIDI}'te "
                    f"ama yayinlanan road={yol}")
        self.assertGreaterEqual(
            olculen, 1,
            "zikzakta hic karar uretilmedi — kapi bos kaldi "
            "(D-15/K-04: sifir olcum basari sayilmaz)")

    def test_zikzak_ayrisan_sahnede_yayin_darbogaza_esitlenmez(self):
        """KAPI: darbogaz != govde iken yayinlanan deger DARBOGAZ OLAMAZ.

        T155 mutasyon muhafizi: yayin hatti `serit_karari` -> `darbogaz_serit`
        geri cevrilirse DAR kapilarda bu test duser.
        """
        ayrisan = 0
        for kapi_px in TUM_KAPILAR:
            with self.subTest(kapi_px=kapi_px):
                yol, olc = _kos(kapi_px)
                if yol is None or olc is None:
                    continue
                if olc["darbogaz_serit"] == olc["serit_karari"]:
                    continue
                ayrisan += 1
                self.assertNotEqual(
                    yol, olc["darbogaz_serit"],
                    f"kapi_px={kapi_px}: yayinlanan road={yol} DARBOGAZ seride "
                    f"esit (govde={olc['serit_karari']}) — T155 oncesi yayin "
                    "hatti geri gelmis")
        self.assertGreaterEqual(
            ayrisan, 1,
            "hicbir sahnede darbogaz != govde — sahne ayirt edici degil, "
            "test bosluk (D-15 vakum kapi riski)")

    def test_zikzak_sahne_gecerliligi_govde_hala_uc(self):
        """POZITIF KONTROL: sahne bozulursa yukaridaki kapilar anlamsizlasir.

        Govde seridi 3 degilse zikzak geometrisi degismis demektir; o zaman
        "yayin darbogaza esitlenmedi" testi bir sey ayirt etmiyordur.
        """
        gorulen = 0
        for kapi_px in TUM_KAPILAR:
            yol, olc = _kos(kapi_px)
            if olc is None:
                continue
            gorulen += 1
            self.assertEqual(
                olc["serit_karari"], GOVDE_SERIDI,
                f"kapi_px={kapi_px}: serit_karari={olc['serit_karari']} — "
                "zikzak sahnesi beklenen geometride degil")
        self.assertGreaterEqual(gorulen, 2, "sahne olcumleri uretilemedi")

    def test_zikzak_darbogaz_alani_TANI_olarak_KORUNDU(self):
        """T155: `darbogaz_serit` silinmedi — dar kapida hala kapiyi gosterir.

        Yayin alani degisti, TANI alani degismedi. Bu test o taahhudu tutar:
        `darbogaz_serit` dar kapili zikzakta kapinin seridini (1) vermeye
        devam etmeli, yoksa hakem ekranindaki kanit satiri anlamsizlasir.
        """
        olculen = 0
        for kapi_px in DAR_KAPILAR:
            with self.subTest(kapi_px=kapi_px):
                yol, olc = _kos(kapi_px)
                if olc is None:
                    continue
                olculen += 1
                self.assertEqual(
                    olc["darbogaz_serit"], KAPI_SERIDI,
                    f"kapi_px={kapi_px}: darbogaz_serit="
                    f"{olc['darbogaz_serit']}, kapi serit {KAPI_SERIDI}'de")
        self.assertGreaterEqual(olculen, 1, "dar kapili olcum uretilemedi")

    def test_yayin_serit_karari_sozlesmesine_bagli(self):
        """Tutarlilik: her olculebilir sahnede yayin = olcumun `serit_karari`si.

        Tek basina yeterli kapi DEGILDIR (ic tutarlilik, yer gercegi degil);
        yukaridaki degere-dayali kapilarin yaninda regresyon sinyalidir.
        """
        for kapi_px in TUM_KAPILAR:
            with self.subTest(kapi_px=kapi_px):
                yol, olc = _kos(kapi_px)
                if yol is None or olc is None:
                    continue
                self.assertEqual(
                    yol, olc["serit_karari"],
                    f"kapi_px={kapi_px}: yayinlanan road={yol} != "
                    f"serit_karari={olc['serit_karari']}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
