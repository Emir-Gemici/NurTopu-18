# -*- coding: utf-8 -*-
"""tests/belge_kilidi.py — ORTAK belge kilidi yardimcisinin kendi kapisi (T240, D-460 karar 2).

Her normallestirme kurali icin POZITIF (kural isliyor) ve NEGATIF (kural fazla is
yapmiyor, yalanci alarm uretmiyor) vaka vardir. Beyaz liste disi cizik icin,
kilidin UYDURMA bir sozdizimini kalip eklemeden yakaladigi gosterilir: yardimcida
`<sil>` diye bir sey yazili degildir, yine de yakalanir.

Kapinin ozu: bu dosyadaki her vaka, D-460 denetiminde OLCULEN bir kacisa ya da o
kacisin duzeltmesinin YAN ETKISINE karsilik gelir.
"""

import re
import sys
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
for _y in (KOK / "tests",):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

import belge_kilidi as bk  # noqa: E402


class CizikAyiklama(unittest.TestCase):
    """cizikleri_ayikla: ~~...~~ · ~...~ · <del>/<s>/<strike>."""

    def test_cift_tilde_duser(self):
        self.assertEqual("a  b", bk.cizikleri_ayikla("a ~~gizli~~ b"))

    def test_cift_tilde_satir_asar(self):
        # T226 D1: cizili aralik satir asabilir (re.S)
        self.assertEqual("a  b", bk.cizikleri_ayikla("a ~~gizli\nikinci satir~~ b"))

    def test_tek_tilde_duser(self):
        # KACAN MUTANT: T228 A3, T221 W1 — GFM tek tildeyi de uzeri cizili render eder
        self.assertEqual("baslik —  (10 Eylul)",
                         bk.cizikleri_ayikla("baslik — ~ÖLÇÜLEMEDİ~ (10 Eylul)"))

    def test_tek_tilde_satir_asar_ama_bos_satir_asmaz(self):
        self.assertEqual("a  b", bk.cizikleri_ayikla("a ~gizli\ndevam~ b"))
        ham = "a ~acik\n\nikinci paragraf~ b"
        self.assertEqual(ham, bk.cizikleri_ayikla(ham), "bos satir asan aralik cizgi degildir")

    def test_NEGATIF_yaklasik_isareti_korunur(self):
        # Belgelenen tek istisna: "~<rakam>" yaklasiktir (ucu de gercek belgelerde var)
        for ham in ("kirmizi ekran ~3 s gorunur", "kamera ~3 fps", "dongu (~8 Hz)",
                    "kenar ~1,4 px sisiyor"):
            with self.subTest(ham=ham):
                self.assertEqual(ham, bk.cizikleri_ayikla(ham))

    def test_NEGATIF_iki_yaklasik_isareti_birbirine_baglanmaz(self):
        ham = "her ~3 s'de bir dusurur; acilista ~3 s gorunur"
        self.assertEqual(ham, bk.cizikleri_ayikla(ham))

    def test_html_cizgileri_duser(self):
        # KACAN MUTANTLAR: T226 D1b/D1d, T228 A4/A5
        for etiket in ("del", "s", "strike"):
            with self.subTest(etiket=etiket):
                self.assertEqual(
                    "hukum:  var",
                    bk.cizikleri_ayikla("hukum: <{0}>KOSULMADI</{0}> var".format(etiket)))

    def test_html_cizgisi_buyuk_harf_ve_oznitelikli(self):
        self.assertEqual("a  b", bk.cizikleri_ayikla('a <DEL class="x">gizli</DEL> b'))

    def test_NEGATIF_kod_icindeki_tilde_ve_etiket_korunur(self):
        ham = "ev dizini `~/navitas/scripts` ve `<s>` ornegi"
        self.assertEqual(ham, bk.cizikleri_ayikla(ham))

    def test_NEGATIF_kod_citi_icindeki_cizgi_korunur(self):
        ham = "once\n\n```bash\nrm ~~/tmp/x~~ && echo '<s>x</s>'\n```\n\nsonra"
        self.assertEqual(ham, bk.cizikleri_ayikla(ham))


class BeyazListeDisiCizik(unittest.TestCase):
    """beyaz_liste_disi_cizik: kalip eklemeden yakalayan BEYAZ LISTE kilidi."""

    def test_temiz_metin_hatasiz(self):
        self.assertEqual([], bk.beyaz_liste_disi_cizik("hicbir cizik yok, ~3 s yaklasik"))

    def test_izinli_cizik_gecer(self):
        izin = "~~10 Eylul (T228): eski komut~~"
        self.assertEqual([], bk.beyaz_liste_disi_cizik("metin " + izin + " devam", (izin,)))

    def test_izinsiz_cizik_yakalanir(self):
        izin = "~~10 Eylul (T228): eski komut~~"
        h = bk.beyaz_liste_disi_cizik("metin " + izin + " ve ~~baska~~ cizik", (izin,))
        self.assertTrue(h)
        self.assertTrue(all("baska" in x for x in h), h)

    def test_tek_tilde_ve_html_yakalanir(self):
        for ham in ("~ÖLÇÜLEMEDİ~", "<del>x</del>", "<s>x</s>", "<strike>x</strike>"):
            with self.subTest(ham=ham):
                self.assertTrue(bk.beyaz_liste_disi_cizik("hukum " + ham + " sonu"), ham)

    def test_UYDURMA_SOZDIZIMI_kalip_eklemeden_yakalanir(self):
        """KILIDIN VAROLUS GEREKCESI: yardimcida bu sozdizimlerinin HICBIRI yazili degil.

        Kara liste yaklasimi bunlari goremezdi; beyaz liste (bilinen zararsiz etiketler
        disindaki HER etiket + her cizme isareti) kalip eklemeden yakalar.
        """
        uydurma = (
            "<sil>ÖLÇÜLEMEDİ</sil>",                                     # hic duyulmamis etiket
            '<span style="text-decoration:line-through">ÖLÇÜLEMEDİ</span>',  # CSS ile cizgi
            '<qzx7 data-state="retracted">ÖLÇÜLEMEDİ</qzx7>',             # baska uydurma etiket
            "Ö̶L̶Ç̶Ü̶L̶E̶M̶E̶D̶İ̶",  # birlesen
            "∼ÖLÇÜLEMEDİ∼",                                              # tilde benzeri (U+223C)
        )
        for ham in uydurma:
            with self.subTest(ham=ham):
                self.assertTrue(bk.beyaz_liste_disi_cizik("hukum " + ham + " sonu"),
                                "uydurma cizme sozdizimi KACTI: " + ham)
        # ... ve bu etiket adlari yardimcinin kaynaginda HIC GECMIYOR: kilit onlari
        # kalip eklenmis oldugu icin degil, BEYAZ LISTE disinda kaldiklari icin yakaliyor.
        kaynak = (KOK / "tests" / "belge_kilidi.py").read_text(encoding="utf-8")
        for ad in ("qzx7", "sil"):
            self.assertNotIn(ad, bk.ZARARSIZ_ETIKETLER)
        self.assertNotIn("qzx7", kaynak)

    def test_NEGATIF_zararsiz_etiket_ve_kod_ici_isaret(self):
        self.assertEqual([], bk.beyaz_liste_disi_cizik("satir sonu<br/> ve H<sub>2</sub>O"))
        self.assertEqual([], bk.beyaz_liste_disi_cizik("`~/navitas` ve `<s>` ile `~~x~~`"))

    def test_NEGATIF_stil_tasiyan_zararsiz_etiket_yakalanir(self):
        self.assertTrue(bk.beyaz_liste_disi_cizik('<br style="text-decoration:line-through"/>'))


class Normallestirme(unittest.TestCase):
    """normalize: her kural icin POZITIF + NEGATIF."""

    def test_cizikler_duser(self):
        self.assertEqual("a b", bk.normalize("a ~~gizli~~ b").replace("  ", " ").strip())

    def test_vurgu_sozcuk_ici_dahil_sokulur(self):
        # KACAN MUTANTLAR: T221 W3 `_dogrulandi_`, W4 `__kosuldu__`, tur-1 Z2 `d*ogrulandi*`
        for ham in ("_doğrulandı_", "__doğrulandı__", "**doğrulandı**", "d*oğrulandı*",
                    "`doğrulandı`"):
            with self.subTest(ham=ham):
                self.assertEqual("dogrulandi", bk.normalize(ham))

    def test_NEGATIF_vurgu_sokulmesi_sozcugu_bolmez(self):
        self.assertEqual("olcut1", bk.normalize("ölçüt_1"))

    def test_tipografik_kesme_ve_tirnak_duzlesir(self):
        # KACAN MUTANT: T226 D1f (duz tirnak -> tipografik tirnak)
        self.assertEqual("62'si", bk.normalize("62’si"))
        self.assertEqual("62'si", bk.normalize("62´si"))
        self.assertEqual('"kaynak"', bk.normalize("“kaynak”"))

    def test_NEGATIF_esitsizlik_isareti_tersine_donmez(self):
        # '≠' NFKD'de '=' + U+0338'e ayrisir; birlesik isaret atilinca ANLAM TERSINE donerdi
        self.assertEqual("olculemedi != gecti", bk.normalize("ÖLÇÜLEMEDİ ≠ GEÇTİ"))

    def test_turkce_sayi_sozcukleri_rakama_iner(self):
        # KACAN MUTANT: T228 A6 — kod 2 iken belgeye "**bir** ardisik" yazildi
        self.assertEqual("1 ardisik", bk.normalize("**bir** ardışık"))
        self.assertEqual("3 uc", bk.normalize("üç uç"))
        self.assertEqual("0,5 s", bk.normalize("yarım saniye"))
        self.assertEqual("1 kanal", bk.normalize("tek kanal"))
        self.assertEqual("10 adim", bk.normalize("on adım"))

    def test_NEGATIF_on_eki_on_sayisina_donmez(self):
        # Aksan katlamasi SONRA kosar: "ön hüküm" 10 hukum OLMAZ, "uç" 3 olmaz
        self.assertEqual("on hukum", bk.normalize("Ön hüküm"))
        self.assertEqual("on kayit", bk.normalize("ÖN KAYIT"))

    def test_NEGATIF_sayi_sozcugu_sozcuk_icinde_donmez(self):
        for ham, bek in (("birim", "birim"), ("onay", "onay"), ("altını", "altini"),
                         ("birlikte", "birlikte"), ("teknik", "teknik")):
            with self.subTest(ham=ham):
                self.assertEqual(bek, bk.normalize(ham))

    def test_birim_es_anlamlilari_katlanir(self):
        # KACAN MUTANTLAR: T228 A7/A9 — kilit "s" ariyordu, belgeye "saniye" yazildi
        self.assertEqual("3 s", bk.normalize("3 saniye"))
        self.assertEqual("3 s", bk.normalize("3 saniyelik"))
        self.assertEqual("250 ms", bk.normalize("250 milisaniye"))
        self.assertEqual("15 °", bk.normalize("15 derece"))

    def test_NEGATIF_birim_katlamasi_sayisiz_sozcugu_bozmaz(self):
        # Birim kurali SAYIYA baglidir: onunde rakam olmayan sozcuk birime cevrilmez
        for ham in ("derecelendirme", "saniyelerce surdu", "derece yuksekligi"):
            with self.subTest(ham=ham):
                self.assertNotIn("°", bk.normalize(ham))
                self.assertNotIn(" s ", " " + bk.normalize(ham) + " ")

    def test_karsilastirma_onek_es_anlamlilari(self):
        # KACAN MUTANT: T228 A7 — "en az 1 saniye" kilidin `≥ N s` kalibi disinda kalmisti
        for ham in ("en az 1 saniye", "asgari 1 s", ">= 1 s", "≥ 1 s"):
            with self.subTest(ham=ham):
                self.assertEqual("≥ 1 s", bk.normalize(ham))
        for ham in ("en çok 2 s", "azami 2 s", "<= 2 s"):
            with self.subTest(ham=ham):
                self.assertEqual("≤ 2 s", bk.normalize(ham))

    def test_karsilastirma_sonek_es_anlamlilari(self):
        # KACAN MUTANT: T228 A9 — "6 saniyeyi asan" kilidin `> N s` kalibi disinda kalmisti
        self.assertEqual("> 6 s", bk.normalize("6 saniyeyi aşan"))
        self.assertEqual("> 6 s", bk.normalize("6 s'den fazla"))
        self.assertEqual("> 3 s", bk.normalize("3 saniyeyi geçen"))
        self.assertEqual("≥ 3 s", bk.normalize("3 saniye ve üzeri"))

    def test_NEGATIF_sayisiz_karsilastirma_sozcugu_isarete_donmez(self):
        # "daha fazla" tek basina esik degildir; sayi olmadan sonek kurali islemez
        self.assertEqual("daha fazla bilgi", bk.normalize("daha fazla bilgi"))
        self.assertEqual("uzerinde calisiliyor", bk.normalize("üzerinde çalışılıyor"))

    def test_NEGATIF_en_az_birim_yoksa_esik_uretmez(self):
        n = bk.normalize("bu surumle en az bir kez koşulmuş olmalı")
        self.assertIn("≥ 1 kez", n)
        self.assertIsNone(re.search(r"≥\s*\d+\s*s(?![a-z])", n), n)


class OlumluHukum(unittest.TestCase):
    """olumlu_hukum_var: OLCULEMEDI != GECTI ailesi."""

    def test_aile_yakalanir(self):
        # A8 (teyit edildi / basarili), W2 (KANITLANDI), W7 (sorunsuz / saglanmis)
        for ham in ("geçti", "ölçüldü", "doğrulandı", "teyit edildi", "sağlandı",
                    "sağlanmış durumdadır", "başarılı", "başarıyla", "sorunsuz",
                    "çalıştı", "uygun bulundu", "gözlendi", "KANITLANDI", "koşuldu",
                    "tutar", "onaylandı"):
            with self.subTest(ham=ham):
                self.assertIsNotNone(bk.olumlu_hukum_var("saha koşumu " + ham + "."), ham)

    def test_altcizgi_ve_vurgu_arkasina_saklanamaz(self):
        # KACAN MUTANTLAR: W3/W4 — eski kalibin `(?<!\w)` siniri `_`yu HARF sayiyordu
        for ham in ("_doğrulandı_", "__koşuldu__", "**tutar**", "d*oğrulandı*"):
            with self.subTest(ham=ham):
                self.assertIsNotNone(bk.olumlu_hukum_var("SITL prova sonucu: " + ham), ham)

    def test_cizili_hukum_sayilmaz(self):
        self.assertIsNone(bk.olumlu_hukum_var("~~doğrulandı~~ · ~geçti~ · <s>koşuldu</s>"))

    def test_NEGATIF_olculmemis_etiketler_olumlu_sayilmaz(self):
        for ham in ("ÖLÇÜLEMEDİ", "DOĞRULANACAK", "ÖLÇÜLECEK", "koşulmadı", "ölçülmedi",
                    "doğrulanmadı", "sağlanamadı", "çalıştır", "çalışmıyor", "başarısızsa",
                    "kanıtlıdır", "görülür", "tutmazsa", "tutamazdı", "koşulmuş olmalı"):
            with self.subTest(ham=ham):
                self.assertIsNone(bk.olumlu_hukum_var("adim " + ham + "."), ham)

    def test_haric_yalniz_bildirileni_disarida_birakir(self):
        self.assertIsNone(bk.olumlu_hukum_var("çelişki (ölçüldü):", haric=("olculdu",)))
        self.assertEqual("gecti", bk.olumlu_hukum_var("(ölçüldü) ve geçti", haric=("olculdu",)))


class OnKayitliMetin(unittest.TestCase):
    """on_kayitli_metin_esit: bosluk-normalize TAM esitlik."""

    def test_satir_sarmasi_anlam_degildir(self):
        self.assertTrue(bk.on_kayitli_metin_esit("bir  iki\n  uc", "bir iki uc"))

    def test_tek_karakter_farki_duser(self):
        # KACAN MUTANT: W1 — baslik ALT DIZGE ile bakildigi icin ~ÖLÇÜLEMEDİ~ gecmisti
        baslik = "### 6.6 SITL provası — ÖLÇÜLEMEDİ (bu makine, 10 Eylül)"
        self.assertTrue(bk.on_kayitli_metin_esit(baslik, baslik))
        self.assertFalse(bk.on_kayitli_metin_esit(
            baslik.replace("ÖLÇÜLEMEDİ", "~ÖLÇÜLEMEDİ~"), baslik))
        self.assertFalse(bk.on_kayitli_metin_esit(baslik + " · prova KANITLANDI", baslik))


class HukumCumleleri(unittest.TestCase):
    """hukum_cumleleri: kapali cumle kumesi (V1/V3 sinifi)."""

    METIN = ("Prova KOŞULMADI. Bu bir hüküm değildir.\n"
             "Ölçüt 1 düşer. Sürüm 4.5.7 ile `bir.py` çalıştırılır.")

    def test_yalniz_anahtarli_cumleler_doner(self):
        c = bk.hukum_cumleleri(self.METIN, ("prova", "olcut"))
        self.assertEqual(("prova kosulmadi.", "olcut 1 duser."), c)

    def test_yeni_hukum_cumlesi_kumeyi_bozar(self):
        # V1: olumlu hukum sozcugu YOK, numarali olcut atfi YOK — kara liste goremez
        bozuk = self.METIN + " Bu koşullardan biri tutmasa da prova kabul edilir."
        self.assertNotEqual(bk.hukum_cumleleri(self.METIN, ("prova", "olcut")),
                            bk.hukum_cumleleri(bozuk, ("prova", "olcut")))

    def test_NEGATIF_kod_ici_nokta_cumle_bitirmez(self):
        c = bk.hukum_cumleleri("Prova `sim_vehicle.py -f plane` ile koşulmadı.", ("prova",))
        self.assertEqual(1, len(c), c)

    def test_cizili_cumle_sayilmaz(self):
        self.assertEqual((), bk.hukum_cumleleri("~~Prova doğrulandı.~~", ("prova",)))


if __name__ == "__main__":
    unittest.main()
