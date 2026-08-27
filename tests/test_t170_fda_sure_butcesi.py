"""T170 KAPISI (ON_KAYIT SS37 · REVIEW_LOG D-318): SS5.3.2 FDA test ucusunun
10 DAKIKALIK operasyon limiti ve GUI sure limitlerinin SOZLESMEDEN gelmesi.

SARTNAME SS5.3.2 (lafzen): "Gorev test ucusunun basarili sayilabilmesi ve
takimlarin 100 tam puan alabilmesi icin; gercek zamanli guzergah tespitinin
alan hakem heyeti tarafindan dogrulanip onaylanmasi ve TUM OPERASYON SURECININ
(kalkis, tespit, veri aktarimi ve inis) MAKSIMUM 10 DAKIKA icerisinde
tamamlanmasi zorunludur. ... sureyi asan ... takimlar 0 PUAN alarak gorevden
basarisiz sayilacaktir."

IKI KUSUR:
  1. Bu 10 dakikalik limit sistemde HIC YOKTU. SS5.3.2'nin diger iki
     parametresi vardi (FDA alani 20 m, asgari irtifa 30 m); eksik olan
     YALNIZ sureydi. FDA ucusunda operator ekranda 15 DAKIKALIK butce gorur
     ve 10'u asarsa 0 puan alirdi — ekran uyarmazdi.
  2. GUI'nin sure limitleri (900/600/900) CIPLAK yaziliydi ve kronometre
     basliklarindaki "/ 15:00" metinleri de ELLE yazilmisti; sozlesme degisse
     ekran ESKI sayiyi gostermeye devam ederdi (madde 16).

BOS KAPI YASAGI (TEST_SPECS SS4.1): esikler sozlesmeden geliyor mu, baslik
SAYIDAN mi tureniyor, ve `--fda` gercekten butceyi degistiriyor mu — ucu de
mutasyonla sinanir.
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
for _y in (KOK / "comms", KOK / "codes"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

import yks_gui                                              # noqa: E402
from karar_sozlesmesi import (SARTNAME_FDA_OPERASYON_SURESI_S,   # noqa: E402
                              SARTNAME_HAZIRLIK_SURESI_S,
                              SARTNAME_IHA_GOREV_SURESI_S,
                              SARTNAME_IKA_GOREV_SURESI_S)

KAYNAK = (KOK / "comms" / "yks_gui.py").read_text(encoding="utf-8")


class SozlesmeSabitleri(unittest.TestCase):

    def test_FDA_limiti_sartname_degeri(self):
        self.assertEqual(600.0, SARTNAME_FDA_OPERASYON_SURESI_S,
                         "SS5.3.2 TUM operasyon icin 10 dakika der")

    def test_FDA_limiti_SS6_2_den_AYRI(self):
        """SS5.3.2'nin butcesi SS6.2'nin IHA suresi DEGILDIR."""
        self.assertNotEqual(SARTNAME_IHA_GOREV_SURESI_S,
                            SARTNAME_FDA_OPERASYON_SURESI_S)
        self.assertLess(SARTNAME_FDA_OPERASYON_SURESI_S,
                        SARTNAME_IHA_GOREV_SURESI_S,
                        "FDA butcesi yarisma gunu butcesinden SIKI olmali")

    def test_sartname_atfi_yazili(self):
        metin = (KOK / "codes" / "karar_sozlesmesi.py").read_text(encoding="utf-8")
        bas = metin.index("SARTNAME_FDA_OPERASYON_SURESI_S")
        pencere = metin[max(0, bas - 1400): bas]
        self.assertIn("5.3.2", pencere, "sabit sartname maddesine baglanmamis")
        self.assertIn("10 DAKIKA", pencere.upper())


class GUISozlesmedenOkuyor(unittest.TestCase):

    def test_limitler_sozlesmeden(self):
        self.assertEqual(SARTNAME_IHA_GOREV_SURESI_S, yks_gui.YksArayuz.IHA_LIMIT)
        self.assertEqual(SARTNAME_IKA_GOREV_SURESI_S, yks_gui.YksArayuz.IKA_LIMIT)
        self.assertEqual(SARTNAME_HAZIRLIK_SURESI_S,
                         yks_gui.YksArayuz.HAZIRLIK_LIMIT)

    def test_BOZULMAMA_degerler_eskisiyle_AYNI(self):
        """Baglama davranisi degistirmemeli: 900/600/900."""
        self.assertEqual(900.0, yks_gui.YksArayuz.IHA_LIMIT)
        self.assertEqual(600.0, yks_gui.YksArayuz.IKA_LIMIT)
        self.assertEqual(900.0, yks_gui.YksArayuz.HAZIRLIK_LIMIT)

    def test_MUTASYON_ciplak_sabit_geri_konamaz(self):
        """Sinif govdesinde `IHA_LIMIT = 900` bicimi YASAK."""
        bas = KAYNAK.index("class YksArayuz:")
        govde = KAYNAK[bas: bas + 1600]
        self.assertIsNone(
            re.search(r"IHA_LIMIT\s*=\s*\d+", govde),
            "IHA_LIMIT ciplak sayi olarak yazilmis (madde 16)")
        self.assertIsNone(re.search(r"IKA_LIMIT\s*=\s*\d+", govde))
        self.assertIn("SARTNAME_IHA_GOREV_SURESI_S", govde)


class BaslikSayidanTureniyor(unittest.TestCase):

    def test_ss_bicimlendirici(self):
        self.assertEqual("15:00", yks_gui._ss(900))
        self.assertEqual("10:00", yks_gui._ss(600))
        self.assertEqual("00:07", yks_gui._ss(7))

    def test_MUTASYON_elle_yazilmis_baslik_YOK(self):
        """Kronometre basliklarinda `/ 15:00` gibi ELLE yazilmis metin olamaz."""
        bas = KAYNAK.index("lbl_kron_iha.config")
        pencere = KAYNAK[bas - 200: bas + 700]
        self.assertNotIn("/ 15:00", pencere,
                         "baslik elle yazilmis — sozlesme degisse ekran ESKI "
                         "sayiyi gosterir")
        self.assertNotIn("/ 10:00", pencere)
        self.assertIn("_ss(self.IHA_LIMIT)", pencere)
        self.assertIn("_ss(self.HAZIRLIK_LIMIT)", pencere)


class ElleYazilmisSureMetniYOK(unittest.TestCase):
    """🔴 Kapinin IDDIA ETTIGI seyi GERCEKTEN olcen kontrol (demo denetimi
    bunu eksik buldu: eski test yalniz `lbl_kron_iha.config` cevresine
    bakiyordu, oysa WIDGET VARSAYILANLARINDA (`text="... / 15:00"`) uc tane
    daha duruyordu)."""

    # Widget metnine ELLE yazilmis "MM:SS": text="..." icinde saat bicimi.
    DESEN = re.compile(r"""text\s*=\s*["'][^"']*\d{1,2}:\d{2}""")

    @staticmethod
    def _kod_satirlari(metin):
        """Yorumlar TARIHSEL kayittir; canli metin sayilmaz."""
        return [s for s in metin.splitlines() if not s.strip().startswith("#")]

    def test_widget_varsayilanlarinda_elle_sure_YOK(self):
        govde = chr(10).join(self._kod_satirlari(KAYNAK))
        bulunan = self.DESEN.findall(govde)
        self.assertEqual([], bulunan,
                         f"kronometre metni ELLE yazilmis: {bulunan} — sozlesme "
                         "degisse ekran ESKI sayiyi gosterir")

    def test_kontrol_DESENI_calisiyor(self):
        """Mutasyon: elle yazilmis bir metin gercekten yakalaniyor mu?"""
        sahte = 'self.lbl.config(text="İHA saat --:-- / 15:00")'
        self.assertTrue(self.DESEN.findall(sahte),
                        "desen elle yazilmis sureyi yakalamiyor — kapi bos")

    def test_yorumdaki_TARIHSEL_metin_muaf(self):
        yorum = '        # eskiden text="İHA / 15:00" yaziyordu'
        self.assertEqual([], self.DESEN.findall(
            chr(10).join(self._kod_satirlari(yorum))),
            "tarihsel kayit canli beyan sayildi")


class FdaKipi(unittest.TestCase):

    def test_varsayilan_KAPALI(self):
        self.assertFalse(yks_gui.YksArayuz.fda_kipi)

    def test_bayrak_CLI_de_tanimli(self):
        self.assertIn('"--fda"', KAYNAK)
        bas = KAYNAK.index('"--fda"')
        self.assertIn("5.3.2", KAYNAK[bas: bas + 500])

    def test_kip_acilinca_butce_10_dakika(self):
        """Ornek duzeyinde ezilir; SINIF varsayilani DEGISMEZ."""
        o = object.__new__(yks_gui.YksArayuz)
        self.assertEqual(900.0, o.IHA_LIMIT)
        o.IHA_LIMIT = SARTNAME_FDA_OPERASYON_SURESI_S
        o.fda_kipi = True
        self.assertEqual(600.0, o.IHA_LIMIT)
        self.assertEqual(900.0, yks_gui.YksArayuz.IHA_LIMIT,
                         "sinif varsayilani kirlendi — yarisma gunu kipi bozuldu")

    def test_kip_ekranda_GORUNUYOR(self):
        bas = KAYNAK.index("lbl_kron_iha.config")
        pencere = KAYNAK[bas - 300: bas + 400]
        self.assertIn("fda_kipi", pencere,
                      "FDA kipi kronometrede gorunmuyor — operator hangi "
                      "butceye baktigini bilemez")
        self.assertIn("5.3.2", pencere)

    def test_uygulama_yolu_bayragi_KULLANIYOR(self):
        bas = KAYNAK.index("if args.fda:")
        pencere = KAYNAK[bas: bas + 600]
        self.assertIn("SARTNAME_FDA_OPERASYON_SURESI_S", pencere)
        self.assertIn("fda_kipi = True", pencere)
        self.assertIn("0 PUAN", pencere,
                      "operatore sonucu soylemiyor (sureyi asan 0 puan alir)")


if __name__ == "__main__":
    unittest.main()
