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

    def test_ON_KAYITLI_anahtar_listesi_varsayilandir(self):
        """`HUKUM_SOZCUKLERI` ON KAYITLIDIR: cagiran onu GENISLETIR, daraltmaz."""
        self.assertEqual(bk.HUKUM_SOZCUKLERI, bk.hukum_cumleleri.__defaults__[0])
        for kok in ("kaynak", "zorunlu", "gecersiz", "kaldirildi", "olcut", "prova", "kural"):
            self.assertIn(kok, bk.HUKUM_SOZCUKLERI)
        # gerekce docstring'te yazili olmali (kume secicisi kara liste DEGILDIR)
        kaynak = (KOK / "tests" / "belge_kilidi.py").read_text(encoding="utf-8")
        self.assertIn("ON KAYITLI \"hukum tasiyan sozcuk\" listesi", kaynak)

    def test_paragraf_madde_ve_tablo_sinirlari_cumle_bolur(self):
        """Cumle birimi KUCUK ve KARARLI olmali: paragraf/madde/tablo satiri sinirdir.

        NEDEN: tablo satirlari tek devasa "cumle"ye yapissa, eklenen bir satir baska bir
        satirin metni icinde gizlenirdi; on kayit da okunamaz olurdu.
        """
        metin = ("| olay | kural |\n| a | kaynak zorunlu |\n| b | kaynak serbest |\n"
                 "\n- kural A: kaynak zorunlu\n- kural B: kaynak serbest\n")
        c = bk.hukum_cumleleri(metin)
        self.assertEqual(5, len(c), c)
        self.assertIn("| a | kaynak zorunlu |", c)
        self.assertIn("- kural b: kaynak serbest", c)

    def test_Y7_baslik_TASIMAYAN_celiskili_paragraf_kumeyi_bozar(self):
        """D-460 kacani Y7 (CONTRACTS §6.8): kalin baslik TASIMAYAN, kaynak paragrafinin
        hemen ardina DEGIL bolumun BASKA bir yerine konan celiskili hukum paragrafi.

        Kalin baslik demeti, on kayitli kaynak hukmu ve paragraf KOMSULUGU kilitlerinin
        UCUNDEN de kacmisti (olculdu: MK15 ve tum test_yks_*.py cikis 0). Kapali cumle
        kumesi onu NEREYE konursa konsun gorur.
        """
        taban = ("**Kaynak hükmü:** `kaynak` alanı zorunludur.\n\n"
                 "**Tekrar kuralı:** iki olay kenarda yazılır.\n\n"
                 "**Bağlayıcı ilkeler:** kanıt yazımı karar yolunu değiştirmez.\n")
        beklenen = bk.hukum_cumleleri(taban)
        y7 = "Not (12 Eylül): `kaynak` alanı artık zorunlu değildir.\n\n"
        for capa in ("**Kaynak hükmü:**", "**Tekrar kuralı:**", "**Bağlayıcı ilkeler:**"):
            with self.subTest(capa=capa):
                yeni = bk.hukum_cumleleri(taban.replace(capa, y7 + capa, 1))
                self.assertNotEqual(beklenen, yeni, "Y7 varyanti KACTI: " + capa)
                self.assertIn("not (12 eylul): kaynak alani artik zorunlu degildir.", yeni)


class HtmlVarlikBicimi(unittest.TestCase):
    """D-460 kacani Y4: cizme isaretinin HTML VARLIK bicimi (`&#822;`, `&#x336;`).

    OLCULEN KACIS: CONTRACTS §6.8'de `maliyeti 2 satır/dk'dır.` ->
    `m&#822;a&#822;l&#822;i&#822;y&#822;e&#822;t&#822;i&#822; 2 satır/dk'dır.` yapilinca
    MK15 suiti cikis 0 verdi (KACTI); AYNI karakterin ciplak hali (U+0336) DUSUYORDU.
    Yani belge okuyucuda USTU CIZILI gorunen bir hukum testte YURURLUKTE sayiliyordu.
    """

    def test_varlik_bicimli_birlesen_cizgi_yakalanir(self):
        harfharf = "".join(h + "&#822;" for h in "ÖLÇÜLEMEDİ")
        hatalar = bk.beyaz_liste_disi_cizik("prova " + harfharf + " sayilir")
        self.assertEqual(10, len(hatalar), hatalar)
        self.assertIn("birlesen uzeri cizgi", hatalar[0])

    def test_onaltilik_varlik_bicimi_de_yakalanir(self):
        self.assertTrue(bk.beyaz_liste_disi_cizik("prova m&#x336;aliyet"))
        self.assertTrue(bk.beyaz_liste_disi_cizik("prova m&#X336;aliyet"))

    def test_varlik_bicimli_tilde_YAPI_URETMEZ_ama_aday_sayilir(self):
        """D-465 DUZELTMESI: `&#126;&#126;...&#126;&#126;` CIZGI ACMAZ — ayiklanmaz, ADAY sayilir.

        ONCEKI DAVRANIS (T240-B, e70b3fe6) `&#126;`'i cozup `~~...~~` sanip ARALIGI
        AYIKLIYORDU. Bu YANLISTI ve kendi kacisini uretmisti: CommonMark/GFM'de varlik
        referansi YAPI belirten simgenin yerine KULLANILAMAZ — okuyucuda
        `&#126;&#126;eski&#126;&#126;` duz `~~eski~~` METNI olarak gorunur, ustu CIZILI
        DEGILDIR. Ayiklamak, cizilmemis bir hukmu testin gozunden DUSURMEK demekti.

        Simdi: metin YERINDE kalir (varlik kilidi ondan kacamaz) ve dort varligin dordu
        de "yapi ureten varlik bicimi" olarak beyaz liste disi ADAYDIR — yani belgede
        boyle bir yazim varsa kilit ZATEN duser. Assert sayisi 2 -> 3 (guclendi).
        """
        metin = "hukum &#126;&#126;eski&#126;&#126; sonu"
        self.assertEqual(metin, bk.cizikleri_ayikla(metin),
                         "varlik bicimli tilde CIZGI ACMAZ: ayiklanmamali")
        hatalar = bk.beyaz_liste_disi_cizik(metin)
        self.assertEqual(4, len(hatalar), hatalar)
        self.assertIn("yapi ureten varlik bicimi &#126;", hatalar[0])

    # ── D-465 / K2: `&#96;` SARMALI POZITIF VAKALAR (curutucunun X15/X16/X17'si) ──
    #: Her biri gercek dosya mutanti olarak da olculdu (mutasyon_t240.py X15/X16/X17).
    #: Ortak kok neden: `&#96;` COZULURSE sahte bir KOD ARALIGI acilir ve icindeki cizik
    #: taramadan tamamen gizlenir; okuyucuda ise `&#96;` duz backtick KARAKTERIDIR, kod
    #: araligi ACMAZ, icindeki `~~` ise cizgiyi ACAR.
    VARLIK_SARMALI = (
        ("&#96; ondalik", "Hüküm: &#96;~~X~~&#96; sonu."),
        ("&#x60; onaltilik", "Hüküm: &#x60;~~X~~&#x60; sonu."),
        ("&grave; adli", "Hüküm: &grave;~~X~~&grave; sonu."),
        ("&#96; + <s>", "Hüküm: &#96;<s>X</s>&#96; sonu."),
    )

    def test_K2_varlik_sarmali_cizik_ADAY_ve_X_DUSER(self):
        """`&#96;~~X~~&#96;` ve varyantlari: hata VERMELI ve `cizikleri_ayikla` X'i DUSURMELI."""
        for ad, metin in self.VARLIK_SARMALI:
            with self.subTest(ad=ad):
                hatalar = bk.beyaz_liste_disi_cizik(metin)
                self.assertTrue(hatalar, "varlik sarmali KACTI: " + ad)
                self.assertIn("yapi ureten varlik bicimi", " | ".join(hatalar))
                self.assertNotIn("X", bk.cizikleri_ayikla(metin),
                                 "sarmalin ICI cizilidir, ayiklanmali: " + ad)

    def test_K2_varlik_bicimli_CIT_kod_araligi_ACMAZ(self):
        """`&#96;&#96;&#96;` cit bicimi: kod citi ACMAZ, icindeki hukum GIZLENEMEZ."""
        metin = "&#96;&#96;&#96;\n~~ÖLÇÜLEMEDİ~~\n&#96;&#96;&#96;\n"
        hatalar = bk.beyaz_liste_disi_cizik(metin)
        self.assertTrue(hatalar, "varlik bicimli cit KACTI")
        self.assertEqual(2, sum("tilde" in h for h in hatalar),
                         "sahte citin ICINDEKI cizik gorulmeli (acilis + kapanis ~~): "
                         + repr(hatalar))
        self.assertNotIn("ÖLÇÜLEMEDİ", bk.cizikleri_ayikla(metin))

    def test_K2_GERILEME_KANITI_hukum_sozcugu_yururlukte_SAYILMAZ(self):
        """Curutucunun gerileme kaniti: `&#96;~~kaynak ... zorunludur~~&#96;` — hukum DUSMELI."""
        metin = "**Hüküm:** &#96;~~kaynak alanı zorunludur~~&#96; ve boş olamaz."
        self.assertNotIn("zorunludur", bk.normalize(metin),
                         "cizili hukum YURURLUKTE sayiliyor (T240-B gerilemesi)")
        self.assertTrue(bk.beyaz_liste_disi_cizik(metin))

    def test_K2_KUSUR1b_varlik_tildesi_hukum_cumlesini_DUSURMEZ(self):
        """KUSUR 1b: `&#126;` sarmali celiskili hukum `hukum_cumleleri` demetinden DUSMEMELI.

        Onceki surumde `&#126;` cozulup `~~` olunca `cizikleri_ayikla` cumleyi SILIYORDU ve
        kapali kume onu HIC gormuyordu. Artik cozulmedigi icin cumle kumede DURUR.
        """
        celiski = "&#126;Not (12 Eylül): `kaynak` alanı artık zorunlu değildir.&#126;"
        cumleler = bk.hukum_cumleleri(celiski)
        self.assertEqual(1, len(cumleler), cumleler)
        self.assertIn("kaynak alani artik zorunlu degildir", cumleler[0])

    def test_olumlu_hukum_varlik_arkasina_saklanamaz(self):
        """Iki ayri kilit birden tutar ve ikisi de gereklidir.

        Birlesen cizgi bir ARALIK sozdizimi degildir (baslangici/sonu yoktur), bu yuzden
        `cizikleri_ayikla` onu ayiklayamaz — `normalize` birlesen isaretleri NFKD ile atar,
        dolayisiyla gizlenen "GECTI" hukmu `olumlu_hukum_var`da GORULUR (gizlenme yolu
        kapali). Ayni metni `beyaz_liste_disi_cizik` ayrica HATA sayar: belgede boyle bir
        cizik varsa kilit zaten duser.
        """
        gizli = "".join(h + "&#822;" for h in "GEÇTİ")
        self.assertEqual("gecti", bk.olumlu_hukum_var("prova " + gizli + " sayilir"),
                         "varlik bicimli birlesen cizgi olumlu hukmu GIZLEYEMEZ")
        self.assertTrue(bk.beyaz_liste_disi_cizik("prova " + gizli + " sayilir"))
        self.assertEqual("gecti", bk.olumlu_hukum_var("prova GE&#199;T&#304; sayilir"),
                         "cizgi OLMAYAN varlik cozulup olumlu hukum GORULMELI")

    def test_NEGATIF_zararsiz_varliklar_yanlis_pozitif_uretmez(self):
        """`&#8212;` (em tire), `&amp;`, `&nbsp;`, `&copy;`, `&#176;` cizik DEGILDIR."""
        zararsiz = ("Emniyet &amp; kanıt &#8212; süre 3&nbsp;s içinde &copy; 2026.",
                    "Açı 55&#176; ve oran &#37;90; ölçüt &#8805; 3 s.",
                    "Boş: & tek başına, &yanlisad; ve &#; bozuk biçim.")
        for metin in zararsiz:
            with self.subTest(metin=metin):
                self.assertEqual([], bk.beyaz_liste_disi_cizik(metin))

    def test_kacinilan_etiket_ornegi_HAYALET_ETIKET_uretmez_ama_kod_DISINDA_ADAYDIR(self):
        """`&lt;s&gt;` markdown'da ETIKET ACMAZ; kod ICINDE temiz, kod DISINDA ADAYDIR.

        D-465 DEGISIKLIGI (guclendirme): `&lt;`/`&gt;` eskiden yalniz COZULMUYORDU, yani
        hicbir kilit onlari GORMUYORDU. Artik `_COZULMEZ` ailesinin tamami (yapi ureten
        simgelere cozen her varlik) kod DISINDA dogrudan beyaz liste disi ADAYDIR.
        OLCUM (bu kilidin bagladigi dort belgede, kod araliklari disinda): CONTRACTS 0,
        GOSTERICI_KURULUM 0, config/pixhawk/README 0, t235 ON_KAYIT 0 mesru varlik —
        yani bu sertlestirme gercek belgelerde HICBIR yanlis pozitif uretmez (ayrica
        `scripts/belge_kilidi_denetle.py` ciktisi degismedi).
        """
        self.assertEqual([], bk.beyaz_liste_disi_cizik("Ornek: `&lt;s&gt;` kod icinde temiz."))
        hatalar = bk.beyaz_liste_disi_cizik("Ornek &lt;s&gt;boyle&lt;/s&gt; kod disinda.")
        self.assertEqual(4, len(hatalar), hatalar)
        self.assertIn("yapi ureten varlik bicimi", hatalar[0])
        # ... ama HAYALET ETIKET uretmez: `<s>` etiketi olarak sayilmaz, cizik ayiklanmaz.
        self.assertNotIn("html etiketi", " | ".join(hatalar))
        self.assertIn("boyle", bk.cizikleri_ayikla("Ornek &lt;s&gt;boyle&lt;/s&gt; kod disinda."))

    def test_NEGATIF_kod_icinde_varlik_cozulmez(self):
        """Kod icinde `&amp;` harfi harfinedir (karar 2'nin varlik ikizi)."""
        self.assertEqual([], bk.beyaz_liste_disi_cizik("komut `echo m&#822;a` calisir"))
        self.assertIn("&#822;", bk.cizikleri_ayikla("komut `echo m&#822;a` calisir"))

    def test_hata_metnindeki_konum_HAM_metinden_okunur(self):
        """Cozumleme yalniz TARAMA kopyasinda; satir/baglam HAM metinden — konum KAYMAZ."""
        metin = "birinci satir\nikinci satir\nucuncu m&#822;aliyet\n"
        hatalar = bk.beyaz_liste_disi_cizik(metin)
        self.assertEqual(1, len(hatalar), hatalar)
        self.assertIn("satir 3", hatalar[0])
        self.assertIn("&#822;", hatalar[0], "baglam HAM metinden gelmeli")


class BlokEsitligi(unittest.TestCase):
    """D-465 (1): `bloklar` — ON KAYITLI METIN ESITLIGI birimi.

    KILIDIN VAROLUS GEREKCESI: YOKLUK denetiminin kacis yuzeyi SONSUZDUR (her yasak
    bicimin baska bir yazimi vardir), ESITLIK denetiminin kacis yuzeyi YOKTUR. Asagidaki
    vakalar ikisini YAN YANA olcer: ayni hukmu ALTI ayri sozdizimiyle gizleme girisimi
    `beyaz_liste_disi_cizik`'in yalniz birinde hata verdigi, EŞITLIGIN ise ALTISINDA da
    dustugu gosterilir.
    """

    TABAN = ("## 4. Kabul\n"
             "\n"
             "- **T236 kapısı:** yatay **≤ 2,0 m**, zamanın **≥ %90**'ında.\n"
             "- İkinci madde.\n"
             "\n"
             "| alan | kural |\n"
             "|---|---|\n"
             "| kaynak | zorunlu |\n"
             "\n"
             "```bash\n"
             "echo bir\n"
             "\n"
             "echo iki\n"
             "```\n")

    def test_yapisal_birimler_ayrilir_ve_SAYILABILIR(self):
        b = bk.bloklar(self.TABAN)
        self.assertEqual(7, len(b), b)
        self.assertEqual("## 4. Kabul", b[0])
        self.assertIn("- İkinci madde.", b)
        self.assertIn("| kaynak | zorunlu |", b)

    def test_kod_citinin_ICI_harfi_harfine_korunur(self):
        """Cit icindeki BOS SATIR blok ACMAZ ve satir sonlari AYNEN durur."""
        b = bk.bloklar(self.TABAN)
        cit = [x for x in b if x.startswith("```")]
        self.assertEqual(1, len(cit), b)
        self.assertEqual("```bash\necho bir\n\necho iki\n```", cit[0])

    def test_NEGATIF_satir_sarmasi_ve_bosluk_ESITLIGI_BOZMAZ(self):
        """Bosluk/satir sonu hukmun anlami DEGILDIR (D-465: normallestirme yalniz budur)."""
        sarmali = self.TABAN.replace("yatay **≤ 2,0 m**, zamanın",
                                     "yatay **≤ 2,0 m**,\n  zamanın", 1)
        self.assertEqual(bk.bloklar(self.TABAN), bk.bloklar(sarmali))
        self.assertEqual(bk.bloklar(self.TABAN),
                         bk.bloklar(self.TABAN.replace("İkinci madde.",
                                                       "İkinci   madde.", 1)))

    def test_ALTI_GIZLEME_BICIMI_de_ESITLIGI_DUSURUR(self):
        """ESITLIK vs YOKLUK — D-465'in gerekcesinin OLCUMU.

        Ayni hukum alti ayri sozdizimiyle geri cekiliyor/gizleniyor. `bloklar` ALTISINDA
        DA duser; `beyaz_liste_disi_cizik` yalnizca varlik/cizik tasiyanlarda hata verir.
        Bu fark, olcum hukmu tasiyan yuzeylerin neden ESITLIGE cevrildigini gosterir.
        """
        hedef = "| kaynak | zorunlu |"
        gizlemeler = (
            ("~~ ile", "| kaynak | ~~zorunlu~~ |"),
            ("<s> ile", "| kaynak | <s>zorunlu</s> |"),
            ("&#822; varlik cizgisi", "| kaynak | z&#822;o&#822;runlu |"),
            ("&#96; sarmali sahte kod araligi", "| kaynak | &#96;~~zorunlu~~&#96; |"),
            ("HTML yorumu", "| kaynak | <!-- zorunlu --> |"),
            ("markdown baglantisi", "| kaynak | [zorunlu](#) |"),
        )
        taban = bk.bloklar(self.TABAN)
        for ad, yeni in gizlemeler:
            with self.subTest(gizleme=ad):
                self.assertNotEqual(taban, bk.bloklar(self.TABAN.replace(hedef, yeni, 1)),
                                    "ESITLIK kacirdi: " + ad)

    def test_AYIKLAMA_YOKTUR_cizili_metin_blokta_DURUR(self):
        """Cizik ayiklamasi saklama yuzeyi acar; bu yuzden `bloklar` AYIKLAMAZ.

        FDR kurali geregi cizili duran ESKI metin blogun ICINDE HAM haliyle kalir —
        boylece "eski metin silinmez, cizilir" kurali ile on kayit birbirine baglanir.
        """
        cizili = self.TABAN.replace("- İkinci madde.", "- ~~İkinci madde (10 Eylül)~~", 1)
        b = bk.bloklar(cizili)
        self.assertIn("- ~~İkinci madde (10 Eylül)~~", b)
        self.assertNotIn("- İkinci madde.", b)


# ── D-465 / K4: GERCEK BELGELERIN HARFI HARFINE KOPYASI OLAN CAPALAR ─────────
# NEDEN: curutucu (KUSUR 3) olctu — birim testi A10 bolumunu TEK SATIRA indirgemis,
# A7 ve §7.5 capalarindan da birer cumle ATILMISTI; oysa sinif docstring'i capalari
# "gercek belgelerin metni (harfi harfine kopya)" diye tanitiyordu. Olculenden
# fazlasini soyleyen beyan yasaktir (D-460 bulgu 3 sinifi). Capalar artik GERCEKTEN
# tam kopyadir; 12 Eylul 2026'da alinmis ANLIK GORUNTUDUR (canli dosya OKUNMAZ:
# ATOLYE kagidi 12 Eylul'de INSAN tarafindan doldurulacak ve bu birim testi o
# doldurmada kirilmamalidir — gercek dosyalarin kilidi kendi suitlerindedir).
#   kaynak: ATOLYE_TEST_GUNU_20260912.md §A10 · §A7 ; CONTRACTS.md §7.5
A10_BOLUM = (
    '### A10 — Jetson canlı kamera FPS (köprü + algı zinciri) · 15 dk\n'
    '- **Amaç:** algı zincirinin canlı CSI kaynağıyla kare hızını ölçmek (6 Eylül ölçümü dosya kaynağıydı, kamera bağlı değildi — D-431).\n'
    '- **Komut (Jetson):** A9 köprüsü açıkken `python -B codes/kamera_dogrula.py --kaynak http://127.0.0.1:8080/video --kare 60 --zincir --model jetson_paket/models/navitas_seg_v36_best.pt --imgsz 512 | tee results/atolye_20260912/A10_canli_fps.txt` · terminalin fotoğrafı `A10_ekran.jpg`. Model yolu 6 Eylül koşumundaki dosyadır (results/jetson_20260906/jetson_fps_20260906_orin_nano/ozet.json `vakalar[0].model`); yoksa `ls jetson_paket/models/*.pt` (manifest `asil_model_pt`).\n'
    '- **Beklenen görüntü:** `okunan kare : 60 (dusen: 0)` · `kare gecikmesi : p50=… ms p95=… ms` · `OLCULEN FPS` · `rota durumlari`.\n'
    '- **BEKLENTİ (BENZER ÖLÇÜM — ölçüm değil):** aynı kart, pt, imgsz 512, dosya kaynağı: p50/p95 739/942 ms = 1,35/1,06 FPS (results/jetson_20260906/jetson_fps_20260906_orin_nano/ozet.json:69-70, D-431). Canlı kaynakta köprü okuma + JPEG çözme payı eklenir (BİLİNMİYOR) → beklenti ≤ 1,35 FPS.\n'
    '- **Kabul (FDR/BOLUM_3_SISTEM_SPESIFIKASYONLARI.md:915):** p50 ve p95 ayrı ayrı ≥ 0,61 FPS ⇔ kare gecikmesi p95 ≤ 1000 / 0,61 = 1639 ms (HESAP).\n'
    '- **Sonuç: ÖLÇÜLECEK (12 Eylül atölye)** → `results/atolye_20260912/A10_canli_fps.txt` · `A10_ekran.jpg`\n'
    '- `[ ] ÖLÇÜLDÜ  [ ] ÖLÇÜLEMEDİ — neden: …… · saat: …… · kim: ……`\n'
)

A7_BOLUM = (
    '### A7 — Menzil: SiK + MK15 video (açık alan varsa; yoksa ÖLÇÜLEMEDİ — sahada) · 25 dk\n'
    '- **Amaç:** SiK ve MK15 videonun görev için gereken mesafede çalışmasını göstermek.\n'
    "- **Adımlar:** yankı ucu İHA'nın kendisi (Jetson İHA'daki 12,2 V hattından, pil takılı, **pervanesiz**; hava SiK Jetson USB'de, A6 yankı komutu) uzağa taşınır; iki uçta telefon GPS koordinatı (ekran görüntüsü `A7_konum_<m>.png`); ≈100 m'de ve ulaşılan en uzak noktada — **Komut (PC):** `& $PY -B scripts/sik_rf_olc.py --rol olc --port COMx --baud 57600 --n 200 --aralik 0.2 --cikti results/atolye_20260912/A7_sik_<mesafe>m.json`. A11 zinciri kuruluysa aynı mesafede YKS video panelinin ekran fotoğrafı `A7_mk15_<mesafe>m.png`.\n"
    '- **Beklenen görüntü:** A6 ile aynı satırlar; YKS video panelinde CANLI görüntü (BAYAT değil).\n'
    '- **BEKLENTİ (HESAP — ölçüm değil):** gereken mesafe: İHA-UB kenarı `SARTNAME_IHA_UB_KENAR_M = 300.0` (codes/karar_sozlesmesi.py:2017); YKS bir köşedeyse en uzak nokta karşı köşe 300 × √2 = 424,3 m, 32 m kalkış irtifasıyla (config/pixhawk/README.md görev tablosu) eğik √(424,3² + 32²) = 425,5 m; YKS kenar ortasındaysa √(300² + 150²) = 335,4 m. Cihaz menzili: bu çift için ölçüm yok (DDR ">%98, 300 m" iddiasının kanıtı yok — SAHA_KOSUM_KAGIDI_20260910.md:31), MK15 için depoda sayı yok → BİLİNMİYOR; AIR_SPEED düştükçe SiK menzili artar (A6\'daki SiK belgesi).\n'
    '- **Kabul (bu kâğıtta ön kayıt; RTT eşiği A6 ile aynı):** ölçülen mesafe ≥ 425,5 m\'de `sik_rf_olc` çıkış 0 (p95 < 200 ms) ∧ aynı mesafede YKS videosu CANLI. Daha kısa mesafede ölçüldüyse sonuç "kısmi — d m" yazılır, menzil kabulü ÖLÇÜLEMEDİ.\n'
    '- **Sonuç: ÖLÇÜLECEK (12 Eylül atölye)** → `results/atolye_20260912/A7_sik_<mesafe>m.json` · `A7_konum_<m>.png` · `A7_mk15_<mesafe>m.png`\n'
    '- `[ ] ÖLÇÜLDÜ  [ ] ÖLÇÜLEMEDİ — neden: …… · saat: …… · kim: ……`\n'
)

C75_BOLUM = (
    '### 7.5 SiK hub — NAVITAS-çerçeve seri çoğullayıcı (Faz B · D-404 · 2026-09-03)\n'
    '\n'
    "**Olgu:** SiK (433 MHz) kipinde Jetson'daki üç NAVITAS süreci\n"
    '(`rpi_inference --telsiz-seri`, `iha_inis_yayinci --serial`,\n'
    "`iha_komut_alici --serial`) aynı `/dev/ttyUSB0`'ı ister — seri port tek\n"
    "sahiplidir (§7.4'ün NAVITAS-protokol ikizi). Çözüm `comms/seri_hub.py`:\n"
    'portu **yalnız hub** açar, tüketiciler kendi UDP kiplerinde kalır\n'
    '(**tüketici kodu değişmez**).\n'
    '\n'
    '| yön | davranış |\n'
    '|---|---|\n'
    '| tüketici → seri | Tüketici çerçeveyi hub\'ın UDP soketine (`--bind`, varsayılan `127.0.0.1:5100`) yollar; hub datagramı olduğu gibi seriye yazar ve göndereni "öğrenilen" kümesine ekler |\n'
    '| seri → tüketiciler | Hub gelen baytları kalıcı `FrameReader` ile **tam çerçeveye** toparlar; her çerçeveyi `encode(decode(...))` ile tek satır yapıp (statik `--tuketici` listesi ∪ öğrenilenler) adreslerinin **hepsine** yayınlar — datagram = çerçeve (D-403 KÜÇÜK-4 ile uyumlu) |\n'
    '| yalnız-dinleyen tüketici | `--tuketici HOST:PORT` statik listede olmalı (ör. `iha_komut_alici` 5007) — hiç göndermeden de alsın |\n'
    '| uzun ömürlü tüketici | **KURAL (D-405):** öğrenilen küme sayı tavanlıdır (`OGRENILEN_TAVANI`, en az tazelenen düşer, KIRMIZI log); uzun ömürlü her tüketici (`rpi_inference`, `iha_inis_yayinci`) **statik `--tuketici` ile de verilir** — öğrenme yalnız emniyettir |\n'
    "| tek sahiplik | Hub UDP ucunu `SO_REUSEADDR`'sız açar (ikinci hub exit 3); seri port `exclusive=True` (Linux flock; ikinci süreç `SerialException`) — çift başlatma **sessiz olamaz** |\n"
    "| dayanıklılık | Hiçbir çerçeve hub'ı öldürmez: derin iç içe JSON (`RecursionError`), 4096 B üstü datagram, fan-out `OSError` → sayaç + KIRMIZI log, süreç yaşar; `SIGTERM` → `durdur()` (son sayaç satırı journal'a düşer) |\n"
    '| zamanlama | `SERI_OKUMA_ZAMAN_ASIMI_S ≤ 0,05`, `UDP_OKUMA_ZAMAN_ASIMI_S ≤ 0,01` testle kilitli; UDP→seri p95 < `PARASUT_TEKRAR_ARALIGI_S` (ölçüldü: boşta p50 10,6 / p95 31 ms; 20 Hz seri girişiyle p50 45 ms — Windows) |\n'
    "| seri arızası | Seri kapatılır, KIRMIZI log, 1 s'de bir yeniden açma; UDP tarafı YAŞAR; arızada UDP'den gelen çerçeveler **düşürülür ve sayılır** (kuyruklanmaz — bayat rota yayınlanmasın) |\n"
    '\n'
    '**Topoloji (SiK kipi, Jetson — `jetson_baslat.sh KIP=sik` ile AYNI, test K2\n'
    'kilitler):** `seri_hub --port /dev/ttyUSB0 --bind 127.0.0.1:5100 --tuketici\n'
    '127.0.0.1:5007` · `rpi_inference --yks-hedef 127.0.0.1:5100` · `iha_inis_yayinci\n'
    '--yks 127.0.0.1:5100` · `iha_komut_alici --bind 127.0.0.1:5007`. **Tek hatta\n'
    "bir kez:** SiK hattında hedef YKS'dir; `--ika-hedef`/`--ika` hub'a VERİLMEZ\n"
    "(ölçüldü, D-405: İKA ACK'i SiK'ten hiç gelmediği için `IhaSender` 8 tekrar /\n"
    "2,11 s boşa tekrar ediyordu). İKA'nın hattı (SiK çok-noktalı mı, WiFi\n"
    '`--ika-hedef <IKA_IP>:5006` mi) **topolojiyle karara bağlanır** (cumartesi).\n'
    'ACK\'ler §6.6\'daki "ortam yayını" semantiğini korur: YKS\'nin ACK\'i seriden\n'
    'gelir, hub öğrenilen/statik tüketicilere yayınlar; her tüketici yalnız kendi\n'
    "`ref`'ini eşler. UDP kipinde (WiFi) hub **kullanılmaz**; süreçler doğrudan\n"
    'YKS/İKA adresine konuşur. Kilit: `tests/test_faz_b_seri_hub.py` (uçtan uca:\n'
    'YKS-seri → hub → gerçek `IhaKomutAlici` → ACK → seri).\n'
    '\n'
    '---\n'
    '\n'
    '## 8. Çözünürlük sözleşmesi\n'
    '\n'
    '> **Çıkarım `imgsz` = `config/model_registry.json → profiles.competition.imgsz`\n'
    '> (bugün **512**). Bu dosyada ÇIPLAK SAYI YAZILMAZ — kilit:\n'
    '> `tests/test_t163_cozunurluk_sozlesmesi.py`.**\n'
    '\n'
    "🔴 **BU BÖLÜM 2026-08-27'DE DÜZELTİLDİ (T163 · D-308).** Önceki hâli kalın harflerle\n"
    '**"`imgsz` = 640; değiştirmek güvenli DEĞİLDİR"** diyordu — oysa üretim **v27\'den beri\n'
    "512**'de koşuyordu. Yani sözleşme **kendi üretimini yasaklıyordu**; sahadaki bir kişi bu\n"
    "satırı okuyup 640'a çevirseydi **kabul edilmemiş** bir çözünürlükte koşacaktı. Bayatlık\n"
    'JETSON kılavuzunda T154/T157/T158 kapılarıyla kapatılmıştı; **bu dosyaya bakan kapı yoktu**,\n'
    'artık var.\n'
)


class KabulOlcutuTekligi(unittest.TestCase):
    """D-461 (T236-B curutucusu) — ON KAYIT TEKLIGI kilidi.

    OLCULEN KACIS: `ON_KAYIT §4`'e IKINCI ve GEVSETILMIS bir kabul olcutu eklenince
    hicbir test dusmuyordu; ozgun satir yerinde durdugu icin "varlik" kilitleri yesildi.
    Ayni sinif ATOLYE-2'de (A10/A7) ve T229-D2'de (CONTRACTS §7.5, parantez ICINE konan
    celiskili hukum) ayri ayri olculdu — uc belirtinin tek kok nedeni budur.

    CAPALARIN NE OLDUGU (D-465 / K4 — olculenden fazlasini soyleyen beyan yasak):
      · `A10_BOLUM`, `A7_BOLUM`, `C75_BOLUM`: ilgili bolumun TAMAMININ, HARFI HARFINE
        kopyasi (12 Eylul 2026'da alinmis anlik goruntu; testin canli dosyayi OKUMADIGI
        bilerek secildi — ATOLYE kagidi 12 Eylul'de INSAN tarafindan doldurulacak ve
        birim testi o doldurmada kirilmamalidir). Kaynaklar:
          - ATOLYE_TEST_GUNU_20260912.md  §A10, §A7
          - CONTRACTS.md                  §7.5
      · `T236_BOLUM`: SENTETIKTIR — t235 ON_KAYIT §4'un TAMAMI DEGILDIR; yalniz kabul
        SATIRI (`T236_OLCUT`) harfi harfine kopyadir. Gercek §4'un tamami
        `tests/test_t235_alan_etiketi.py` icinde ON KAYITLI METIN ESITLIGIYLE (D-465)
        ayrica baglidir.

    BIRIM TESTININ SINIRI: buradaki vakalar YARDIMCININ davranisini olcer. Gercek
    belgelerin kendisi ilgili suitlerde (test_t235_alan_etiketi, test_yks_mk15...,
    test_isaretli_gosterici, test_faz_b_arduplane_sablon) kilitlidir.
    """

    T236_ADI = "T236 SITL kapısı"
    T236_OLCUT = (
        "- **T236 SITL kapısı** (Windows SITL ikilisi bulunursa): bekleme süresince (ilk 10 s "
        "hariç) yatay konum merkezden **≤ 2,0 m** ve yaw β'dan **≤ ±5°** zamanın **≥ %90**'ında; "
        "irtifa hedeften **±1,0 m**. SITL koşulamazsa **ÖLÇÜLEMEDİ** (GEÇTİ değil) ve plan ilk "
        "kalkıştan önce Mission Planner simülasyonunda insanca doğrulanır (BEYAN)."
    )
    #: SENTETIK bolum (gercek §4'un TAMAMI DEGIL) — kabul satiri harfi harfine kopyadir.
    T236_BOLUM = (
        "## 4. FDA görev planı (T235-E) ve SITL (T236)\n"
        "- Görev üreteci: 4 köşe + Başlangıç kenarı + montaj yaw → merkez = köşe ortalaması.\n"
        "  İrtifa (kip, h) seçimine göre, `FENCE` 50 m altında.\n"
        + T236_OLCUT + "\n"
    )

    #: ATOLYE-2 A10'un kabul olcutu DISINDA mesruen tasidigi KARSILASTIRMALI buyukluk:
    #: "**BEKLENTİ (BENZER ÖLÇÜM — ölçüm değil):** ... → beklenti ≤ 1,35 FPS". Bu satir
    #: bir KABUL degil BEKLENTIDIR; kural (b) onu rakip esik sanip MUTASYONSUZ yanlis
    #: pozitif veriyordu (D-465 / K4, curutucu KUSUR 3). ON KAYIT olarak gecilir:
    #: kara liste gevsetmesi DEGILDIR — yeni bir deger ancak GORUNUR bir test
    #: degisikligiyle girer ve 1,35 disindaki HER fps degeri yine DUSURUR (asagida
    #: `test_K4_A10_mesru_buyukluk_ON_KAYITLIDIR_baskasi_DUSER` bunu olcer).
    A10_MESRU = (("fps", 1.35),)

    A10_ADI = "Kabul (FDR/BOLUM_3_SISTEM_SPESIFIKASYONLARI.md:915)"
    A7_ADI = "Kabul (bu kâğıtta ön kayıt; RTT eşiği A6 ile aynı)"
    C75_ADI = "zamanlama"

    @staticmethod
    def _madde(bolum, onek):
        """Bolumun `onek` ile baslayan TEK maddesi (harfi harfine, satir sonu haric)."""
        bulunan = [s for s in bolum.splitlines() if s.startswith(onek)]
        assert len(bulunan) == 1, (onek, len(bulunan))
        return bulunan[0]

    def test_TABAN_temiz(self):
        self.assertEqual([], bk.kabul_olcutu_tekligi(
            self.T236_BOLUM, self.T236_ADI, self.T236_OLCUT))

    def test_NEGATIF_olcut_disi_sayi_rakip_esik_sayilmaz(self):
        """`FENCE` 50 m KARSILASTIRMA tasimaz: esik degil, olcum baglamidir."""
        self.assertIn("FENCE` 50 m altında", self.T236_BOLUM)
        self.assertEqual([], bk.kabul_olcutu_tekligi(
            self.T236_BOLUM, self.T236_ADI, self.T236_OLCUT))

    def test_T236B_ikinci_gevsetilmis_olcut_DUSER(self):
        """D-461 ANA KANITI: ON_KAYIT §4'e eklenen ikinci olcut kilidi DUSURMELI."""
        mutant = self.T236_BOLUM + (
            "- **T236 SITL kapısı (gözden geçirilmiş):** ≤ 4,0 m · ±15° · ≥ %70 · ±3,0 m\n")
        hatalar = bk.kabul_olcutu_tekligi(mutant, self.T236_ADI, self.T236_OLCUT)
        self.assertTrue(hatalar, "D-461 mutanti KACTI")
        birlesik = " | ".join(hatalar)
        self.assertIn("tam 1 olmali", birlesik)                  # (a) teklik
        self.assertIn("rakip esik", birlesik)                    # (b) rakip esik
        self.assertIn("gozden gecirilmis", birlesik)             # (d) celiski sozcugu

    def test_K3_rakip_esik_BIRIM_SOZCUGU_ile_yazilinca_DUSER(self):
        """D-465 / K3 (curutucu KUSUR 2, gercek dosya mutanti X13).

        OLCULEN KACIS: "sahada kabul yatay en cok 4 metre ve zamanin en az yuzde 70'i
        olarak alinir" — DORT kural birden temiz donuyordu, cunku `normalize` "metre" ve
        "yuzde"yi katlamiyordu. Simdi katliyor: "4 metre" -> "4 m", "yuzde 70" -> "%70".
        """
        mutant = self.T236_BOLUM + ("- **Not (12 Eylül):** sahada kabul yatay en çok "
                                    "4 metre ve zamanın en az yüzde 70'i olarak alınır.\n")
        hatalar = bk.kabul_olcutu_tekligi(mutant, self.T236_ADI, self.T236_OLCUT)
        self.assertTrue(hatalar, "X13 (birim SOZCUGU) KACTI")
        birlesik = " | ".join(hatalar)
        self.assertIn("rakip esik ('m')", birlesik)
        self.assertIn("rakip esik ('%')", birlesik)

    def test_K3_rakip_esik_farkli_ONEK_ile_yazilinca_DUSER(self):
        """D-465 / K3 (curutucu KUSUR 2, gercek dosya mutanti X14): "≤ 400 cm" = "≤ 4,0 m"."""
        mutant = self.T236_BOLUM + "- **Not (12 Eylül):** sahada kabul ≤ 400 cm alınır.\n"
        hatalar = bk.kabul_olcutu_tekligi(mutant, self.T236_ADI, self.T236_OLCUT)
        self.assertTrue(hatalar, "X14 (cm oneki) KACTI")
        self.assertIn("rakip esik ('m')", " | ".join(hatalar))

    def test_K3_NEGATIF_onek_katlamasi_ayni_esigi_rakip_saymaz(self):
        """Ayni esik baska onekle YAZILIRSA rakip DEGILDIR: 2,0 m == 200 cm."""
        esdeger = self.T236_BOLUM + "- Not: ölçüm penceresi merkezden ≤ 200 cm alınır.\n"
        self.assertEqual([], bk.kabul_olcutu_tekligi(
            esdeger, self.T236_ADI, self.T236_OLCUT))

    def test_ATOLYE2_A10_GERCEK_bolum_yalniz_p50_ile_verilir_DUSER(self):
        """ATOLYE-2 kacani A10: "T233 birlesmezse kabul YALNIZ p50 ile verilir".

        Capa GERCEK A10 bolumunun TAMAMIDIR (kisaltilmis degil).
        """
        olcut = self._madde(A10_BOLUM, "- **Kabul (FDR/")
        self.assertEqual([], bk.kabul_olcutu_tekligi(
            A10_BOLUM, self.A10_ADI, olcut, self.A10_MESRU),
            "GERCEK A10 bolumu MUTASYONSUZ temiz olmali (D-465 / K4)")
        mutant = A10_BOLUM + "- **Not (12 Eylül):** T233 birleşmezse kabul yalnız p50 ile verilir.\n"
        hatalar = bk.kabul_olcutu_tekligi(mutant, self.A10_ADI, olcut, self.A10_MESRU)
        self.assertTrue(hatalar, "A10 mutanti KACTI")
        self.assertIn("yalniz p50 ile verilir", " | ".join(hatalar))

    def test_K4_A10_mesru_buyukluk_ON_KAYITSIZ_YANLIS_POZITIF_verir(self):
        """OLCULEN OLGU (curutucu KUSUR 3): on kayit VERILMEZSE (b) mutasyonsuz patlar.

        GERCEK A10 bolumunde mesru bir BEKLENTI satiri vardir ("→ beklenti ≤ 1,35 FPS");
        kural (b) onu rakip esik sanar. Eski birim testi bolumu TEK SATIRA indirgeyerek
        bunu gizlemisti, sinif docstring'i ise capalari "harfi harfine kopya" diye
        tanitiyordu — olculenden fazlasini soyleyen beyan. Olgu artik KAYITTADIR ve
        duzeltmesi `mesru_buyuklukler` ON KAYDIDIR.
        """
        olcut = self._madde(A10_BOLUM, "- **Kabul (FDR/")
        hatalar = bk.kabul_olcutu_tekligi(A10_BOLUM, self.A10_ADI, olcut)
        self.assertEqual(1, len(hatalar), hatalar)
        self.assertIn("rakip esik ('fps'): on kayitta [0.61] varken bolumde ayrica [1.35]",
                      hatalar[0])

    def test_K4_A10_mesru_buyukluk_ON_KAYITLIDIR_baskasi_DUSER(self):
        """ON KAYIT GEVSETME DEGILDIR: 1,35 disindaki HER fps rakip esigi yine DUSER."""
        olcut = self._madde(A10_BOLUM, "- **Kabul (FDR/")
        mutant = A10_BOLUM + "- **Not (12 Eylül):** sahada kabul ≥ 0,40 FPS alınır.\n"
        hatalar = bk.kabul_olcutu_tekligi(mutant, self.A10_ADI, olcut, self.A10_MESRU)
        self.assertTrue(hatalar, "on kayit FAZLA sey gecirdi")
        self.assertIn("rakip esik ('fps'): on kayitta [0.61] varken bolumde ayrica [0.4]",
                      " | ".join(hatalar))

    def test_ATOLYE2_A7_GERCEK_bolum_olcute_kosul_EKLEME_DUSER(self):
        """ATOLYE-2 kacani A7: olcutun icine "∧ YKS video paneli BAYAT degil" eklenmesi.

        Ozgun metin hala ICINDE durdugu icin alt dizge (`in`) kilidi YESIL kalirdi;
        ON KAYITLI METIN ESITLIGI (kural c) bunu gorur. Capa GERCEK A7 bolumunun
        TAMAMIDIR — eski surumde olcutun son cumlesi ("Daha kisa mesafede olculduyse
        ...") ATILMISTI (D-465 / K4).
        """
        olcut = self._madde(A7_BOLUM, "- **Kabul (bu kâğıtta")
        self.assertIn("menzil kabulü ÖLÇÜLEMEDİ.", olcut, "capa kisaltilmis olmamali")
        self.assertEqual([], bk.kabul_olcutu_tekligi(A7_BOLUM, self.A7_ADI, olcut),
                         "GERCEK A7 bolumu MUTASYONSUZ temiz olmali")
        mutant = A7_BOLUM.replace("YKS videosu CANLI.",
                                  "YKS videosu CANLI ∧ YKS video paneli BAYAT değil.", 1)
        hatalar = bk.kabul_olcutu_tekligi(mutant, self.A7_ADI, olcut)
        self.assertTrue(hatalar, "A7 mutanti KACTI")
        self.assertIn("kabul blogu on kayitli metinle ayni degil", " | ".join(hatalar))

    def test_T229D2_GERCEK_bolum_parantez_ICINE_konan_celiskili_hukum_DUSER(self):
        """T229-D2 kacani (CONTRACTS §7.5): duzeltme `ATIF` parantezinin ICINDEKI her seyi
        atip tam esitlik yapiyordu; celiskili ikinci hukum PARANTEZ ICINE konunca kaciyordu.

        Capa GERCEK §7.5 bolumunun TAMAMIDIR — eski surumde `| zamanlama |` satirinin
        "; UDP->seri p95 < `PARASUT_TEKRAR_ARALIGI_S` (olculdu: ...)" kismi ATILMISTI
        (D-465 / K4).
        """
        olcut = self._madde(C75_BOLUM, "| zamanlama |")
        self.assertIn("PARASUT_TEKRAR_ARALIGI_S", olcut, "capa kisaltilmis olmamali")
        self.assertEqual([], bk.kabul_olcutu_tekligi(C75_BOLUM, self.C75_ADI, olcut),
                         "GERCEK §7.5 bolumu MUTASYONSUZ temiz olmali")
        mutant = C75_BOLUM.replace(
            "p50 45 ms — Windows)",
            "p50 45 ms — Windows; sahada zaman aşımı ≤ 0,20 s alınır, üst kural geçersiz)", 1)
        hatalar = bk.kabul_olcutu_tekligi(mutant, self.C75_ADI, olcut)
        self.assertTrue(hatalar, "T229-D2 parantez mutanti KACTI")
        birlesik = " | ".join(hatalar)
        self.assertIn("kabul blogu on kayitli metinle ayni degil", birlesik)   # (c)
        self.assertIn("gecersiz", birlesik)                                    # (d)
        # OLCULEN SINIR (iddia edilmiyor): bu capada (b) RAKIP ESIK kurali TETIKLENMEZ,
        # cunku on kayitli olcutun esikleri BIRIMSIZDIR (birimi sabit ADI tasiyor:
        # `..._ZAMAN_ASIMI_S ≤ 0,05`), mutant ise "≤ 0,20 s" yaziyor. (b) yalniz on
        # kayitli olcutun KISITLADIGI buyukluklere bakar; burada onu (c) ve (d) yakalar.
        self.assertNotIn("rakip esik", birlesik)

    def test_ON_KAYITLI_celiski_sozcuk_listesi(self):
        """(d) kurali ON KAYITLIDIR; liste yardimcinin kaynagindadir, cagiranin degil."""
        for kalip in ("gozden\\s+gecirilmis", "kaldirildi", "gecersiz", "revize"):
            self.assertIn(kalip, bk.KABUL_CELISKI_SOZCUKLERI)


if __name__ == "__main__":
    unittest.main()
