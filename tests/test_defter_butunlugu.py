"""NEDEN: Defter ve kuyruk bozulmalarini taban-kilitleme kapilariyla yakalar."""

from __future__ import annotations

import re
import unittest
from collections import Counter
from pathlib import Path
from typing import Collection, Mapping


KOK = Path(__file__).resolve().parents[1]
DEFTER_YOLU = KOK / "REVIEW_LOG.md"
KUYRUK_YOLU = KOK / "TASK_QUEUE.md"

# Tam UC diyez + bosluk zorunlu. Bilerek kelime siniri yok: gorevde verilen
# desen D-60b basligini da sayisal D-60 olarak olcer; `#### D-223'e EK` ise
# eslesmez.
D_BASLIK_DESENI = re.compile(r"^### D-(\d+)", re.MULTILINE)
D_ATIF_DESENI = re.compile(r"\bD-(\d+)")
BOZUK_SATIR_DESENI = re.compile(r"^avitas", re.MULTILINE)

# D-255 olcumundeki alti tarihsel cakisma ayri ve acik tutulur. O olcum
# yazilirken master'a ikinci bir `### D-255` basligi da eklendi; pozitif
# kontrolun gercek dosyada gecmesi icin bu eszamanli baslangic kusuru da adiyla
# kilitlenir. Hicbir taban calisma aninda dosyadan TURETILMEZ.
TARIHSEL_BILINEN_CAKISMA = frozenset({39, 40, 41, 60, 61, 62})
# D-259: bu cakisma BASELINE'LANMADI, DUZELTILDI — ustabasi kendi kaydini
# D-255 -> D-258'e tasidi (mimarinkine dokunulmaz). Liste bos birakiliyor;
# Codex'in bayat-koruması bu duzeltmeyi zaten YAKALADI ve kapiyi dusurdu.
ESZAMANLI_BASLANGIC_CAKISMA = frozenset()
BILINEN_CAKISMA = TARIHSEL_BILINEN_CAKISMA | ESZAMANLI_BASLANGIC_CAKISMA
BILINEN_CAKISMA_ADETLERI = {
    39: 2,
    40: 2,
    41: 2,
    60: 2,
    61: 2,
    62: 2,
}
DEFTER_BASLIK_TABANI = 264
DEFTER_TEKIL_TABANI = 258
KUYRUK_ATIF_OLCUM_TABANI = 203
BOZUK_SATIR_TABANI = 13


def d_numarasi_durumu(
    defter: str,
    *,
    bilinen_cakisma: Collection[int] = BILINEN_CAKISMA,
    bilinen_adetleri: Mapping[int, int] = BILINEN_CAKISMA_ADETLERI,
    baslik_tabani: int = DEFTER_BASLIK_TABANI,
    tekil_tabani: int = DEFTER_TEKIL_TABANI,
) -> dict:
    """D-numarasi kuralinin saf sonucu; dosya sistemi kullanmaz."""
    numaralar = [int(x) for x in D_BASLIK_DESENI.findall(defter)]
    sayac = Counter(numaralar)
    cakismalar = {d: adet for d, adet in sayac.items() if adet > 1}
    bilinen = set(bilinen_cakisma)
    guncel = set(cakismalar)
    yeni = sorted(guncel - bilinen)
    bayat = sorted(bilinen - guncel)
    adet_sapmalari = {
        d: {"beklenen": bilinen_adetleri.get(d), "gercek": sayac.get(d, 0)}
        for d in sorted(bilinen)
        if sayac.get(d, 0) != bilinen_adetleri.get(d)
    }

    hatalar = []
    if len(numaralar) < baslik_tabani:
        hatalar.append(
            f"D-baslik tabani azaldi: {len(numaralar)} < {baslik_tabani}; "
            "taban guncellenmeli"
        )
    if len(sayac) < tekil_tabani:
        hatalar.append(
            f"tekil D tabani azaldi: {len(sayac)} < {tekil_tabani}; "
            "taban guncellenmeli"
        )
    if yeni:
        hatalar.append(f"yeni D-numarasi cakismasi: {yeni}")
    if bayat:
        hatalar.append(f"BILINEN_CAKISMA listesi bayat: {bayat}; liste guncellenmeli")
    if adet_sapmalari:
        hatalar.append(
            f"bilinen cakisma adetleri degisti: {adet_sapmalari}; "
            "liste guncellenmeli"
        )
    return {
        "gecerli": not hatalar,
        "hatalar": hatalar,
        "baslik_sayisi": len(numaralar),
        "tekil_sayisi": len(sayac),
        "cakismalar": dict(sorted(cakismalar.items())),
        "yeni_cakismalar": yeni,
        "bayat_cakismalar": bayat,
        "adet_sapmalari": adet_sapmalari,
    }


def d_numarasi_kapisi(defter: str, **ayarlar) -> dict:
    """D-numarasi durumu bozuksa AssertionError ureten saf kapi."""
    durum = d_numarasi_durumu(defter, **ayarlar)
    if not durum["gecerli"]:
        raise AssertionError("; ".join(durum["hatalar"]))
    return durum


def kuyruk_atif_durumu(
    kuyruk: str,
    defter: str,
    *,
    atif_tabani: int = KUYRUK_ATIF_OLCUM_TABANI,
) -> dict:
    """Kuyruktaki sayisal D atiflarinin defter basliklarindaki saf karsiligi."""
    atiflar = {int(x) for x in D_ATIF_DESENI.findall(kuyruk)}
    basliklar = {int(x) for x in D_BASLIK_DESENI.findall(defter)}
    eksik = sorted(atiflar - basliklar)
    hatalar = []
    if not atiflar:
        hatalar.append("kuyrukta hic D-numarasi atfi yok; tarama vakumda")
    if len(atiflar) < atif_tabani:
        hatalar.append(
            f"kuyruk D-atfi tabani azaldi: {len(atiflar)} < {atif_tabani}; "
            "taban guncellenmeli"
        )
    if eksik:
        hatalar.append(f"defterde bulunmayan kuyruk atiflari: {eksik}")
    return {
        "gecerli": not hatalar,
        "hatalar": hatalar,
        "atif_sayisi": len(atiflar),
        "defter_baslik_sayisi": len(basliklar),
        "eksik": eksik,
    }


def kuyruk_atif_kapisi(kuyruk: str, defter: str, **ayarlar) -> dict:
    """Kuyruk -> defter atif durumu bozuksa AssertionError ureten saf kapi."""
    durum = kuyruk_atif_durumu(kuyruk, defter, **ayarlar)
    if not durum["gecerli"]:
        raise AssertionError("; ".join(durum["hatalar"]))
    return durum


def bozuk_satir_durumu(kuyruk: str, *, taban: int = BOZUK_SATIR_TABANI) -> dict:
    """Sutun sifirda `avitas` ile baslayan satir sayisinin saf taban durumu."""
    sayi = len(BOZUK_SATIR_DESENI.findall(kuyruk))
    if sayi > taban:
        hatalar = [f"bozuk satir tabani asildi: {sayi} > {taban}"]
    elif sayi < taban:
        hatalar = [f"bozuk satir sayisi azaldi: {sayi} < {taban}; taban guncellenmeli"]
    else:
        hatalar = []
    return {"gecerli": not hatalar, "hatalar": hatalar, "sayi": sayi, "taban": taban}


def bozuk_satir_kapisi(kuyruk: str, *, taban: int = BOZUK_SATIR_TABANI) -> dict:
    """Bozuk satir tabani degismisse AssertionError ureten saf kapi."""
    durum = bozuk_satir_durumu(kuyruk, taban=taban)
    if not durum["gecerli"]:
        raise AssertionError("; ".join(durum["hatalar"]))
    return durum


class SafKuralVeMutasyonTests(unittest.TestCase):
    def test_exact_uc_diyez_D223_alt_basligini_kayit_SAYMAZ(self):
        metin = "### D-223 asil kayit\n#### D-223'e EK alt baslik\n"
        durum = d_numarasi_kapisi(
            metin,
            bilinen_cakisma=frozenset(),
            bilinen_adetleri={},
            baslik_tabani=1,
            tekil_tabani=1,
        )
        self.assertEqual(durum["baslik_sayisi"], 1)
        self.assertEqual(durum["cakismalar"], {})

    def test_boundarysiz_kural_D60b_basligini_D60_sayar(self):
        metin = "### D-60 ilk\n### D-60b ikinci\n"
        durum = d_numarasi_kapisi(
            metin,
            bilinen_cakisma={60},
            bilinen_adetleri={60: 2},
            baslik_tabani=2,
            tekil_tabani=1,
        )
        self.assertEqual(durum["cakismalar"], {60: 2})

    def test_bilinen_cakisma_temizlenirse_liste_BAYAT_diye_DUSER(self):
        metin = "### D-1 ilk\n### D-2 tekil\n"
        with self.assertRaisesRegex(AssertionError, "liste.*guncellenmeli"):
            d_numarasi_kapisi(
                metin,
                bilinen_cakisma={1},
                bilinen_adetleri={1: 2},
                baslik_tabani=2,
                tekil_tabani=2,
            )

    def test_mutasyon_1_ikinci_D999_basligi_tekillik_kapisini_DUSURUR(self):
        taban = "### D-1 ilk\n### D-1 ikinci\n### D-2 tekil\n"
        ayarlar = {
            "bilinen_cakisma": {1},
            "bilinen_adetleri": {1: 2},
            "baslik_tabani": 3,
            "tekil_tabani": 2,
        }
        d_numarasi_kapisi(taban, **ayarlar)  # Pozitif kontrol.
        mutasyon = taban + "### D-999 ilk\n### D-999 ikinci\n"
        with self.assertRaisesRegex(AssertionError, "yeni D-numarasi cakismasi"):
            d_numarasi_kapisi(mutasyon, **ayarlar)

    def test_bilinen_cakismanin_ucuncu_kopyasi_adet_kapisini_DUSURUR(self):
        taban = "### D-1 ilk\n### D-1 ikinci\n"
        ayarlar = {
            "bilinen_cakisma": {1},
            "bilinen_adetleri": {1: 2},
            "baslik_tabani": 2,
            "tekil_tabani": 1,
        }
        d_numarasi_kapisi(taban, **ayarlar)
        with self.assertRaisesRegex(AssertionError, "adetleri degisti"):
            d_numarasi_kapisi(taban + "### D-1 ucuncu\n", **ayarlar)

    def test_mutasyon_2_D9999_atfi_atif_kapisini_DUSURUR(self):
        defter = "### D-1 kayit\n"
        kuyruk = "kanit: D-1\n"
        kuyruk_atif_kapisi(kuyruk, defter, atif_tabani=1)  # Pozitif kontrol.
        with self.assertRaisesRegex(AssertionError, "D-9999|9999"):
            kuyruk_atif_kapisi(
                kuyruk + "kanit: D-9999\n",
                defter,
                atif_tabani=1,
            )
        with self.assertRaisesRegex(AssertionError, "D-9999|9999"):
            kuyruk_atif_kapisi(
                kuyruk + "kanit: D-9999b\n",
                defter,
                atif_tabani=1,
            )

    def test_kuyruk_atif_populasyonu_azalirsa_taban_BAYAT_diye_DUSER(self):
        defter = "### D-1 kayit\n### D-2 kayit\n"
        with self.assertRaisesRegex(AssertionError, "taban guncellenmeli"):
            kuyruk_atif_kapisi("kanit: D-1\n", defter, atif_tabani=2)

    def test_mutasyon_3_yeni_avitas_satiri_bozuk_taban_kapisini_DUSURUR(self):
        taban = "".join(f"avitas_{i}\n" for i in range(BOZUK_SATIR_TABANI))
        bozuk_satir_kapisi(taban)  # Pozitif kontrol.
        with self.assertRaisesRegex(AssertionError, "tabani asildi"):
            bozuk_satir_kapisi(taban + "avitas_MUTASYON\n")

    def test_bozuk_satir_azalirsa_taban_BAYAT_diye_DUSER(self):
        metin = "".join(f"avitas_{i}\n" for i in range(BOZUK_SATIR_TABANI - 1))
        with self.assertRaisesRegex(AssertionError, "taban guncellenmeli"):
            bozuk_satir_kapisi(metin)

    def test_girintili_avitas_satiri_sutun_sifir_kapisina_GIRMEZ(self):
        durum = bozuk_satir_kapisi("  avitas_girintili\n", taban=0)
        self.assertEqual(durum["sayi"], 0)


class GercekDosyaPozitifKontrolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.defter = DEFTER_YOLU.read_text(encoding="utf-8")
        cls.kuyruk = KUYRUK_YOLU.read_text(encoding="utf-8")

    def test_gercek_defter_D_numarasi_tabani_GECER(self):
        durum = d_numarasi_kapisi(self.defter)
        self.assertGreaterEqual(durum["baslik_sayisi"], DEFTER_BASLIK_TABANI)
        self.assertGreaterEqual(durum["tekil_sayisi"], DEFTER_TEKIL_TABANI)

    def test_gercek_kuyruk_atiflarinin_tumu_defterde_VAR(self):
        durum = kuyruk_atif_kapisi(self.kuyruk, self.defter)
        self.assertGreaterEqual(durum["atif_sayisi"], KUYRUK_ATIF_OLCUM_TABANI)
        self.assertEqual(durum["eksik"], [])

    def test_gercek_bozuk_satir_tabani_GECER(self):
        durum = bozuk_satir_kapisi(self.kuyruk)
        self.assertEqual(durum["sayi"], BOZUK_SATIR_TABANI)


if __name__ == "__main__":
    unittest.main(verbosity=2)
