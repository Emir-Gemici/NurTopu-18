"""P5 · H1c DAMGASI — olcumun TEKRAR KOSULABILIR ve BOS OLMAYAN oldugunu sinar.

ON KAYIT: results/p5_histerezis/ON_KAYIT.md (EK-1, H1c). Olcut oradaki
metinden okunur; burada tanim UYDURULMAZ, GEVSETILMEZ.

NEDEN (olculen kusur — bu dosyanin varlik sebebi):
  1. H1c ON_KAYIT'ta yaziliydi ama KOSULMAMISTI (FDR/ACIK_KALEMLER §4b #24);
     "yazilmis olcut" ile "kosulmus olcut" ayni sey degildir.
  2. Betikteki ILK siniflandirici (iii) "H5 tavani yayini" sinifini
     `kare icinde 2 kez gorulen kimlik` VEKILIYLE etiketliyordu. O vekil ON
     KAYITTA GECMEZ ve dort kovayi (no_route/cogunluk/h5_tavani/azinlik)
     INSA GEREGI tuketiyordu; dolayisiyla "siniflandirilamayan = 0" olcutu
     H1a'nin ("azinlik = 0") birebir kopyasina donusup ASLA DUSEMEYEN bir
     olcut oluyordu. Bos kapi olcum degildir.
  3. Olcum GPU'lu (2600 cikarim) oldugu icin suit onu kosamaz; suitin
     kosabilecegi sey olcumun SAF CEKIRDEGIDIR — kare oynatma, gerekce
     turetimi ve siniflandirma. Determinizm burada kilitlenir.

Kilitlenenler:
  * `yayin_gerekcesi` turetimi `KararYumusatici.suz`un GERCEK karariyla
    uyusur (uyusmazsa olcum duser, sessizce yanlis etiketlemez);
  * H1c uc sinifin (i)/(ii)/(iii) HEPSI erisilebilir ve sinif disi bir
    gerekce "siniflandirilamayan" uretir (olcut dusebilir — bos degil);
  * ayni girdi + ayni tohum -> ayni sonuc (tekrar kosulabilirlik);
  * artefakt ON_KAYIT ile tutarli (H1c alanlari var ve yayimlanan cevrilmeyi
    tam ortuyor).
"""
import json
import sys
import types
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
BETIK = KOK / "scripts" / "olcum" / "171_histerezis_kararliligi.py"
ON_KAYIT = KOK / "results" / "p5_histerezis" / "ON_KAYIT.md"
OLCUM = KOK / "results" / "p5_histerezis" / "olcum_20260903.json"

sys.path.insert(0, str(KOK / "codes"))

import numpy as np  # noqa: E402

from karar_sozlesmesi import (KARAR_HISTEREZIS_KARE,  # noqa: E402
                              KararYumusatici)

KAYNAK = BETIK.read_text(encoding="utf-8")
KAYIT_METNI = ON_KAYIT.read_text(encoding="utf-8")

# Betigin TAMAMI import EDILMEZ: `68_karar_kararliligi` modul duzeyinde
# `uretim_pt()` cagirir, yani diskte `.pt` ISTER — o dosya git'te DEGILDIR
# (`models/*.pt` yoksayili). Suite modele bagli olamaz; onun yerine betigin
# SAF CEKIRDEGI (sabitler -> `def main(` oncesi) KAYNAK METINDEN derlenir.
# Boylece olculen sey yine gercek betik metnidir, ama kapi GPU'ya ve modele
# bagli degildir. Cekirdegin main() tarafindan GERCEKTEN kullanildigi
# `KablolamaKilidi` ile ayrica sinanir (olu kod sinanmis sayilmaz).
BAS_ISARETI = 'GEREKCE_FAIL_CLOSED = "fail_closed"'
SON_ISARETI = "def main("


def _cekirdek(metin):
    """Betigin saf cekirdegini (agir importsuz) yurut ve MODUL olarak dondur.

    Modul dondurulur (SimpleNamespace degil) ki fonksiyonlarin globalleri ile
    disaridan gorulen ad alani AYNI sozluk olsun — mutasyon testleri gercek
    bagi yamalayabilsin.
    """
    mod = types.ModuleType("m171_cekirdek")
    mod.__dict__.update({"np": np, "KararYumusatici": KararYumusatici,
                         "KARAR_HISTEREZIS_KARE": KARAR_HISTEREZIS_KARE})
    bas, son = metin.index(BAS_ISARETI), metin.index(SON_ISARETI)
    exec(compile(metin[bas:son], str(BETIK), "exec"), mod.__dict__)
    return mod


M = _cekirdek(KAYNAK)


def _dizi(kimlikler):
    """`68_karar_kararliligi.karar` ciktisinin sekli: (yol, red, ...)."""
    return [(yol, red, 0.9, 10, 5) for (yol, red) in kimlikler]


class GerekceTuretimi(unittest.TestCase):
    """Turetim durum makinesinin KENDISIYLE uyusmali (vekil degil, mekanizma)."""

    def test_gerekce_suz_ile_capraz_denetlenir(self):
        # Rota/ret desenleri: tek-kare gurultu, kalici gecis, celisen aday,
        # NO_ROUTE araya girmesi, uzun salinim.
        desenler = [
            [(2, None), (1, None), (2, None), (2, None), (2, None)],
            [(2, None), (1, None), (1, None), (1, None), (1, None)],
            [(2, None), (1, None), (3, None), (1, None), (3, None)],
            [(2, None), (None, "KAPALI"), (1, None), (1, None), (1, None)],
            [(1, None), (2, None), (1, None), (2, None), (1, None)],
            [(None, None), (None, "OLCEK_YOK"), (4, None), (4, None), (5, None)],
        ]
        for desen in desenler:
            y = KararYumusatici()
            for yol, red in desen:
                gerekce = M.yayin_gerekcesi(y, yol, red)
                gercek = y.suz(yol, red)
                self.assertEqual(
                    gercek, gerekce != M.GEREKCE_BASTIRILDI,
                    f"gerekce turetimi saptı: {desen} · ({yol},{red}) -> "
                    f"{gerekce} ama suz()={gercek}")

    def test_kare_oynat_sapmada_DUSER(self):
        """Turetim ile durum makinesi ayrisirsa olcum sessizce devam ETMEZ."""
        gercek = M.yayin_gerekcesi
        try:
            M.yayin_gerekcesi = lambda y, yol, red: M.GEREKCE_BASTIRILDI
            with self.assertRaises(AssertionError):
                M.kare_oynat(_dizi([(2, None), (2, None)]))
        finally:
            M.yayin_gerekcesi = gercek


class H1cSiniflandirmasi(unittest.TestCase):
    """ON_KAYIT EK-1 (i)/(ii)/(iii) — hepsi erisilebilir, disi DUSER."""

    def test_i_no_route_gecisleri(self):
        s = M.kare_oynat(_dizi([(2, None), (None, "KAPALI"),
                                (1, None), (1, None), (1, None)]))
        self.assertEqual({"no_route": 2}, s["h1c_siniflar"])

    def test_ii_kalici_cogunluk_gecisi(self):
        K = KARAR_HISTEREZIS_KARE
        s = M.kare_oynat(_dizi([(2, None)] + [(1, None)] * (K + 1)))
        self.assertEqual({"cogunluk": 1}, s["h1c_siniflar"])

    def test_iii_h5_tavani_yayini(self):
        """Celisen aday: gecis K teyidiyle DEGIL, bayatlama tavaniyla gelir."""
        s = M.kare_oynat(_dizi([(2, None), (1, None), (3, None),
                                (1, None), (3, None)]))
        self.assertEqual({"h5_tavani": 1}, s["h1c_siniflar"],
                         "H5 tavani yayini (iii) olarak etiketlenmedi")

    def test_iii_TEK_gorulen_serit_de_tavandan_yayimlanabilir(self):
        """(iii)'un KOMPOZISYON VEKILIYLE ayrildigi yer — H1c'nin dis dayanagi.

        2,1,3,4,5 dizisinde 4 yalnizca BIR kez gorunur ama yayina H5 tavani
        (bayatlama siniri) ile cikar. Eski `kimlik_sayisi == 2` vekili bunu
        (iii) sayamaz ve "siniflandirilamayan" uretirdi; ON_KAYIT ise (iii)'u
        MEKANIZMAYLA tanimlar. Bu vaka olmadan vekile geri donus sessiz gecer.

        ⚠ Ayni cevrilme H1a'nin ihlalidir (azinlik rota->rota sizintisi) —
        H1a ile H1c AYRI olcutlerdir; biri digerini ortmez. Olculen veride
        (tohum 7/42) bu vaka HIC olusmadi, ama olcut bunu ayirt edebilmelidir.
        """
        s = M.kare_oynat(_dizi([(2, None), (1, None), (3, None),
                                (4, None), (5, None)]))
        self.assertEqual({"h5_tavani": 1}, s["h1c_siniflar"],
                         "tek gorulen serit tavandan yayimlandiginda (iii) "
                         "sinifi tutmadi")
        self.assertEqual({"azinlik": 1}, s["siniflar"],
                         "ayni cevrilme H1a vekilinde azinlik sayilmali")

    def test_sinif_disi_gerekce_SINIFLANDIRILAMAYAN_uretir(self):
        """Olcut BOS DEGIL: uc sinifin disi 'siniflandirilamayan' olur."""
        self.assertEqual(
            M.H1C_SINIFLANDIRILAMAYAN,
            M.h1c_sinifi(M.GEREKCE_AYNI_SERIT, 5, KARAR_HISTEREZIS_KARE))
        self.assertEqual(
            M.H1C_SINIFLANDIRILAMAYAN,
            M.h1c_sinifi("yeni_yayin_yolu", 5, KARAR_HISTEREZIS_KARE))

    def test_ii_ON_KAYIT_kompozisyon_sartini_da_arar(self):
        """(ii) = '5 ornegin >=3'u yeni karar'; mekanizma tek basina yetmez."""
        K = KARAR_HISTEREZIS_KARE
        self.assertEqual("cogunluk", M.h1c_sinifi(M.GEREKCE_K_TEYIDI, K, K))
        self.assertEqual(M.H1C_SINIFLANDIRILAMAYAN,
                         M.h1c_sinifi(M.GEREKCE_K_TEYIDI, K - 1, K))


class Determinizm(unittest.TestCase):
    """Olcum TEKRAR KOSULABILIR: ayni girdi/tohum -> ayni sonuc."""

    DESENLER = [
        [(2, None), (1, None), (2, None), (2, None), (2, None)],
        [(2, None), (1, None), (1, None), (1, None), (1, None)],
        [(2, None), (1, None), (3, None), (1, None), (3, None)],
        [(2, None), (None, "KAPALI"), (1, None), (1, None), (1, None)],
    ]

    def test_kare_oynat_iki_kosumda_ayni(self):
        birinci = [M.kare_oynat(_dizi(d)) for d in self.DESENLER]
        ikinci = [M.kare_oynat(_dizi(d)) for d in self.DESENLER]
        self.assertEqual(birinci, ikinci,
                         "ayni dizi iki kosumda farkli sonuc verdi — "
                         "oynatici durum tasiyor")

    def test_yumusatici_kare_basina_taze(self):
        """Sahneler arasi tasima olcumu kirletir (betik docstring'i)."""
        tek = M.kare_oynat(_dizi(self.DESENLER[0]))
        arka_arkaya = [M.kare_oynat(_dizi(d)) for d in self.DESENLER]
        self.assertEqual(tek, arka_arkaya[0])

    def test_gurultu_tohumla_birebir_tekrarlanir(self):
        img = (np.arange(64 * 48 * 3, dtype=np.uint8)
               .reshape(64, 48, 3))
        for tohum in (7, 42):                    # ON_KAYIT'taki iki tohum
            a = M.gurultulu_kare(np.random.default_rng(tohum), img, 2.0)
            b = M.gurultulu_kare(np.random.default_rng(tohum), img, 2.0)
            self.assertTrue(np.array_equal(a, b),
                            f"tohum {tohum} ayni gurultuyu uretmedi")
        f7 = M.gurultulu_kare(np.random.default_rng(7), img, 2.0)
        f42 = M.gurultulu_kare(np.random.default_rng(42), img, 2.0)
        self.assertFalse(np.array_equal(f7, f42),
                         "iki tohum ayni kareyi verdi — tohum baglanmamis")

    def test_gurultu_dizisi_rng_ilerletir(self):
        """Kare basina 4 kopya AYNI olamaz: rng cagri basina ilerlemeli."""
        img = np.full((32, 32, 3), 128, np.uint8)
        rng = np.random.default_rng(7)
        kopyalar = [M.gurultulu_kare(rng, img, 2.0) for _ in range(4)]
        for i in range(1, 4):
            self.assertFalse(np.array_equal(kopyalar[0], kopyalar[i]),
                             f"{i}. kopya ilkiyle ayni — rng ilerlemiyor")


class ArtefaktVeOnKayit(unittest.TestCase):
    """Kosulmus olcum diskte ve ON_KAYIT ile tutarli."""

    def test_on_kayitta_H1c_yazili(self):
        self.assertIn("H1c", KAYIT_METNI)
        self.assertIn("sınıflandırılamayan yayımlanmış çevrilme", KAYIT_METNI)

    def test_artefaktta_H1c_alanlari_var(self):
        veri = json.loads(OLCUM.read_text(encoding="utf-8"))
        self.assertIn("H1c", veri, "H1c damgasi artefakta yazilmamis")
        for tohum in ("7", "42"):
            s = veri["tohumlar"][tohum]
            self.assertIn("h1c_yayin_cevrilme_siniflari", s)
            self.assertIn("h1c_siniflandirilamayan", s)

    def test_siniflar_yayimlanan_cevrilmeyi_TAM_orter(self):
        """Eksik ortme 'olculemedi'dir; 'gecti' sayilamaz."""
        veri = json.loads(OLCUM.read_text(encoding="utf-8"))
        for tohum, s in veri["tohumlar"].items():
            self.assertEqual(
                s["yayimlanan_cevrilme"],
                sum(s["h1c_yayin_cevrilme_siniflari"].values()),
                f"tohum {tohum}: siniflar yayimlanan cevrilmeyi ortmuyor")

    def test_H1c_hukmu_sayilarla_tutarli(self):
        veri = json.loads(OLCUM.read_text(encoding="utf-8"))
        sifir = all(s["h1c_siniflandirilamayan"] == 0
                    for s in veri["tohumlar"].values())
        self.assertEqual(veri["H1c"], sifir,
                         "H1c hukmu ile sayilar celisiyor")

    def test_ozgun_H1_hala_DUSTU_kayitli(self):
        """Esik GEVSETILMEDI: H1 (%40) dustu ve oyle kalir (D-107)."""
        veri = json.loads(OLCUM.read_text(encoding="utf-8"))
        self.assertFalse(veri["H1_ozgun"],
                         "H1 ozgun hukmu degistirilmis — esik gevsetilemez")
        self.assertIn("%40", KAYIT_METNI)


class KablolamaKilidi(unittest.TestCase):
    """Sinanan cekirdek OLU KOD olamaz: olcumu gercekten main() kosar."""

    @staticmethod
    def _main_govdesi():
        return KAYNAK[KAYNAK.index(SON_ISARETI):]

    def test_main_cekirdegi_kullanir(self):
        govde = self._main_govdesi()
        for cagri in ("kare_oynat(", "gurultulu_kare("):
            self.assertIn(cagri, govde,
                          f"main() {cagri} cagirmiyor — cekirdek olu kod")

    def test_main_H1c_hukmunu_yazar_ve_verdikte_katar(self):
        govde = self._main_govdesi()
        self.assertIn('"H1c": h1c', govde, "H1c artefakta yazilmiyor")
        self.assertIn("h1c_siniflandirilamayan", govde)
        self.assertIn("h1a and h1b and h1c and h2", govde,
                      "H1c nihai verdikte katilmiyor — dusse bile cikis 0")

    def test_esik_ve_tohumlar_ON_KAYITTAKI_gibi(self):
        """Ayni veri/tohum sarti: 7 ve 42, sigma 2, kare basina 4 kopya."""
        self.assertIn('default=[7, 42]', KAYNAK)
        self.assertIn('"--sigma", type=float, default=2.0', KAYNAK)
        self.assertIn('"--tekrar", type=int, default=4', KAYNAK)

    def test_K_sozlesmeden_okunur_ciplak_sabit_degil(self):
        """Madde 16: esik `karar_sozlesmesi`den gelir."""
        self.assertIn("from karar_sozlesmesi import", KAYNAK)
        self.assertIn("esik_K\": KARAR_HISTEREZIS_KARE", KAYNAK)


class MutasyonKilidi(unittest.TestCase):
    """D-370: mutasyon uygulanmadiysa test DUSER."""

    def test_MUTASYON_h5_tavani_gerekcesi_dusurulurse_yakalanir(self):
        mutant = KAYNAK.replace(
            "    if yumusatici._bastirilan_ardisik >= yumusatici._esik - 1:\n"
            "        return GEREKCE_H5_TAVANI\n", "", 1)
        self.assertNotEqual(KAYNAK, mutant, "MUTASYON UYGULANMADI (D-370)")
        mutant_mod = _cekirdek(mutant)
        with self.assertRaises(AssertionError,
                               msg="H5 tavani gerekcesi dusurulunce olcum "
                                   "sessizce surdu"):
            mutant_mod.kare_oynat(_dizi([(2, None), (1, None), (3, None),
                                         (1, None), (3, None)]))

    def test_MUTASYON_kompozisyon_sarti_dusurulurse_yakalanir(self):
        mutant = KAYNAK.replace(
            "if gerekce == GEREKCE_K_TEYIDI and kimlik_sayisi >= esik:",
            "if gerekce == GEREKCE_K_TEYIDI:", 1)
        self.assertNotEqual(KAYNAK, mutant, "MUTASYON UYGULANMADI (D-370)")
        self.assertNotIn("kimlik_sayisi >= esik", mutant,
                         "(ii) kompozisyon sarti hala yerinde — mutasyon bos")


if __name__ == "__main__":
    unittest.main()
