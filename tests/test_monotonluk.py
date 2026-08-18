"""S3 KAPISI — MONOTONLUK INVARIANTI, mimarinin TEK degismezi (CLAUDE.md m.15).

Sozlesme: "Serbest alan OTORITEDIR; nesne katmani yalniz CIKARIR."
Formel:   serbest(K1 AND NOT K2)  ALT KUMESI  serbest(K1)

Yani Katman-2'ye eklenen HER yeni engel kaynagi sistemi ancak daha GUVENLI
yapabilir; serbest alani BUYUTEMEZ.

🔴 NEDEN BU DOSYA TASINDI. Bu testler `codes/test_monotonluk.py` icinde
YAZILIYDI ama `def test_` iceren TEK BIR fonksiyon bile yoktu: script
biciminde, `main()` donus koduyla calisiyordu ve `tests/` altinda degildi.
Yani `unittest discover -s tests` onu HIC KOSMUYORDU — bugune kadar hicbir
regresyon bu dosya tarafindan yakalanamazdi. Dosya `git mv` ile buraya
tasindi ve unittest'e cevrildi; IKI KOPYA BIRAKILMADI (D-158 bulgu 4:
izlenmeyen/kosulmayan test dosyasi ayni kusur sinifidir).
⚠ `REVIEW_LOG.md:1413` eski yolu (`codes/test_monotonluk.py`) anar; o bir
TARIHSEL kayittir ve DEGISTIRILMEDI.

ESKI HALINE GORE EKLENENLER (S3 istegi):
  · 10 tohum -> **50 tohum**
  · tek sinif cifti -> **ALT KUME KAFESI**: engel kumelerinin tum alt kumeleri
    ((), (MOLOZ,), (ARAC,), (MOLOZ,ARAC)) ve her `A alt-kumesi B` cifti
  · **MUTASYON KANITI** (D-15/K-04: sifir olcum basari sayilmaz)

🔴🔴 MUTASYON OLCULDU VE S3'UN KENDI FORMULU KOR CIKTI — bu dosyanin en
onemli bulgusu budur. S3 "cikarmadan sonra bir `dilate` eklenirse serbest
alan sessizce buyur" diyor ve kapi olarak `serbest(B) alt-kumesi serbest(A)`
istiyor. Enjekte edilip OLCULDU (tohum 0, tam engel kumesi):

    sabit referansa (yamasiz kosuma) gore buyume : 1388 px   YAKALAR
    engel pikseli uzerinde serbest               : 0 -> 22   YAKALAR
    ALT KUME KAFESI ihlali                       : 0         🔴 YAKALAMAZ

Sebep matematikseldir: `dilate` MONOTON bir islemdir, yani X alt-kumesi Y
iken dilate(X) alt-kumesi dilate(Y) olmaya devam eder. Duzgun (her alt kumeye
AYNI sekilde uygulanan) bir genisletme kafesi HIC BOZMAZ; iki taraf birlikte
buyur. Yani S3'un literal formulu, S3'un korktugu regresyonu TESPIT EDEMEZ.

Bu yuzden burada UC savunma birden vardir:
  (1) ALT KUME KAFESI — beyan edilen invariant. ASIMETRIK regresyonlari
      yakalar (or. yalniz bir katman varken uygulanan bir genisletme).
  (2) ENGEL PIKSELI SIZINTISI — 50 tohum x tum alt kumelerde hicbir engel
      pikseli serbest olamaz. Duzgun genisletmeyi YAKALAYAN kapi budur.
  (3) SABIT REFERANS — mutasyon testinde yamali cikti, YAMASIZ ciktiyla
      kiyaslanir; "sessizce buyume" olayinin dogrudan tanimi.

⚠ Sinif kimlikleri `codes/sinif_semasi.py`den gelir; ciplak sayi YAZILMAZ
(CLAUDE.md madde 16).
"""

import itertools
import unittest

import cv2
import numpy as np

from codes import costmap_path_finder as C
from codes.sinif_semasi import (COSTMAP_YOL_KATMANLARI, KATMAN_ARAC,
                                KATMAN_MOLOZ, KATMAN_ZEMIN)

TOHUM_SAYISI = 50

#: Engel sinifi kumesinin TUM alt kumeleri. Kiyas `engel_sinif_idler` uzerinden
#: yapilir; MASKE SOZLUGU HER KOSUDA AYNIDIR — yoksa "katman yok" ile "katman
#: engel sayilmiyor" birbirine karisir ve olcum baska bir sey olcerdi.
ENGEL_ALT_KUMELERI = (
    (),
    (KATMAN_MOLOZ,),
    (KATMAN_ARAC,),
    (KATMAN_MOLOZ, KATMAN_ARAC),
)


def sahne(tohum: int, yan: int = 240):
    """Tekrarlanabilir sentetik sahne: zemin + moloz + arac.

    (Tasinan dosyadan AYNEN devralindi — sayilar D-… kayitlariyla
    kiyaslanabilir kalsin diye degistirilmedi.)
    """
    rng = np.random.default_rng(tohum)
    zemin = np.zeros((yan, yan), np.uint8)
    zemin[20:yan - 20, 20:yan - 20] = 1

    moloz = np.zeros((yan, yan), np.uint8)
    for _ in range(4):
        x, y = rng.integers(30, yan - 60, size=2)
        w, h = rng.integers(18, 45, size=2)
        moloz[y:y + h, x:x + w] = 1

    arac = np.zeros((yan, yan), np.uint8)
    for _ in range(3):
        x, y = rng.integers(30, yan - 50, size=2)
        w, h = rng.integers(12, 30, size=2)
        arac[y:y + h, x:x + w] = 1
    return zemin, moloz, arac


def alan(maskeler, engeller) -> np.ndarray:
    return C.serbest_alan(maskeler, mpp=None,
                          yol_sinif_idler=COSTMAP_YOL_KATMANLARI,
                          engel_sinif_idler=engeller)["serbest"].astype(bool)


def _maskeler(tohum):
    zemin, moloz, arac = sahne(tohum)
    return {KATMAN_ZEMIN: zemin, KATMAN_MOLOZ: moloz, KATMAN_ARAC: arac}


def _kafes_ihlalleri(tohumlar):
    """Her tohumda tum `A alt-kumesi B` ciftlerini sina.

    Doner: (ihlal_listesi, kucultme_sayaci, cift_sayisi)
      ihlal = (tohum, A, B, serbest(B) icinde olup serbest(A) disinda kalan px)
    """
    ihlaller = []
    kucultme = 0
    cift = 0
    for tohum in tohumlar:
        mk = _maskeler(tohum)
        serbestler = {alt: alan(mk, alt) for alt in ENGEL_ALT_KUMELERI}
        for a, b in itertools.permutations(ENGEL_ALT_KUMELERI, 2):
            if not set(a) < set(b):        # yalniz GERCEK alt kume ciftleri
                continue
            cift += 1
            sa, sb = serbestler[a], serbestler[b]
            disari = int((sb & ~sa).sum())
            if disari:
                ihlaller.append((tohum, a, b, disari))
            if int(sb.sum()) < int(sa.sum()):
                kucultme += 1
    return ihlaller, kucultme, cift


class _DilateEnjekteCv2:
    """MUTASYON: cikarmadan HEMEN SONRA serbest alani genisleten sahte `cv2`.

    `costmap_path_finder.py:271` cikarmanin TA KENDISIDIR:
        serbest = cv2.bitwise_and(zemin, cv2.bitwise_not(engel))
    ve modulde `bitwise_and` BASKA HICBIR YERDE kullanilmaz (grep ile
    dogrulandi). Bu yuzden yalniz o cagriyi sarmalamak, "biri cikarmadan sonra
    bir `dilate`/`MORPH_CLOSE` ekledi" regresyonunun BIREBIR kalibidir.

    Uretim dosyasina DOKUNULMAZ; yalniz modulun `cv2` niteligi gecici olarak
    degistirilir ve `finally` ile geri konur.
    """

    def __init__(self, gercek):
        self._g = gercek
        self._cekirdek = gercek.getStructuringElement(gercek.MORPH_RECT, (3, 3))

    def __getattr__(self, ad):
        return getattr(self._g, ad)

    def bitwise_and(self, *a, **kw):
        return self._g.dilate(self._g.bitwise_and(*a, **kw), self._cekirdek)


class _AsimetrikEnjekteCv2(_DilateEnjekteCv2):
    """MUTASYON: genisletmeyi YALNIZ bazi alt kumelerde uygulayan sahte `cv2`.

    ALT KUME KAFESI savunmasinin (1) vacuous OLMADIGINI kanitlar. Duzgun
    (her alt kumeye ayni) genisletme kafesi bozmaz — ama gercek regresyonlar
    cogu zaman KOSULLUDUR ("yeni katman varsa su morfolojiyi de uygula") ve
    ISTE ONU kafes yakalar.
    """

    def __init__(self, gercek):
        super().__init__(gercek)
        self.acik = False

    def bitwise_and(self, *a, **kw):
        sonuc = self._g.bitwise_and(*a, **kw)
        return self._g.dilate(sonuc, self._cekirdek) if self.acik else sonuc


#: Yama sizintisini sinamak icin import aninda yakalanan ORIJINAL referans.
_ORIJINAL_SERBEST_ALAN = C.serbest_alan


def _zemin_maskesi(mk):
    """Uretimin `yol_sinif_idler` olarak verdigi maskelerin BIRLESIMI.

    ⚠ Test `KATMAN_ZEMIN`i CIPLAK VARSAYMAZ: `serbest_alan`a hangi yol
    siniflari veriliyorsa (`COSTMAP_YOL_KATMANLARI`) zemin de ONLARDAN
    turetilir. Yarin ikinci bir surulebilir sinif eklenirse test kendiliginden
    dogru kalir (madde 16).
    """
    ilk = next(iter(mk.values()))
    zemin = np.zeros(ilk.shape, dtype=bool)
    for c in COSTMAP_YOL_KATMANLARI:
        if c in mk:
            zemin |= mk[c].astype(bool)
    return zemin


def _zemin_disi_ihlaller(tohumlar):
    """`serbest ⊆ zemin` ihlalleri. Doner: [(tohum, alt_kume, px), ...]"""
    ihlaller = []
    for tohum in tohumlar:
        mk = _maskeler(tohum)
        zemin = _zemin_maskesi(mk)
        for alt in ENGEL_ALT_KUMELERI:
            n = int((alan(mk, alt) & ~zemin).sum())
            if n:
                ihlaller.append((tohum, alt, n))
    return ihlaller


class _KenarYumusatmaYamasi:
    """MUTASYON (T102 · D-171 §3): `serbest = dilate(serbest) & ~engel_ham`.

    "Kenari yumusatayim, sonra engelleri TEKRAR cikarayim" — masum gorunen,
    hatta OZENLI gorunen bir regresyon. Mimar olctu: alt kume kafesi ve engel
    sizintisi kapilarinin IKISI DE geciyor, ama serbest alan 40183 px buyuyor
    ve buyume ETIKETSIZ ARKA PLANA oluyor. Mimarinin kendi kuralina gore
    ("bilinmeyen -> engel") orasi engel olmaliydi.

    `serbest_alan`in DONDURDUGU sozluk uzerinde calisir — regresyonun gercek
    bicimi de budur. Uretim dosyasina DOKUNULMAZ.
    """

    def __init__(self, gercek):
        self._g = gercek
        self._c = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))

    def __call__(self, *a, **kw):
        s = self._g(*a, **kw)
        genis = cv2.dilate(s["serbest"], self._c)
        s["serbest"] = cv2.bitwise_and(genis, cv2.bitwise_not(s["engel_ham"]))
        return s


class MonotonlukInvarianti(unittest.TestCase):

    # ── 1) ASIL KAPI: alt kume kafesi, 50 tohum ───────────────────────────
    def test_alt_kume_kafesi_50_tohumda_invariant(self):
        ihlaller, _kucultme, cift = _kafes_ihlalleri(range(TOHUM_SAYISI))
        self.assertEqual(
            cift, TOHUM_SAYISI * 5,
            f"beklenen cift sayisi {TOHUM_SAYISI * 5}, olculen {cift} — "
            "kafes eksik kuruldu, test KAPSAMI daralmis olurdu")
        self.assertEqual(
            [], ihlaller,
            f"{len(ihlaller)} ihlal: engel EKLEMEK serbest alani BUYUTTU "
            f"(ilk 3: {ihlaller[:3]})")

    # ── 2) POZITIF KONTROL: engel katmani gercekten CIKARIYOR ─────────────
    def test_POZITIF_KONTROL_engel_katmani_gercekten_cikariyor(self):
        """Hicbir tohumda kuculme olmuyorsa sahneler AYIRT EDICI DEGILDIR ve
        yukaridaki test BOS YERE yesil yanar (D-15/K-04)."""
        _ihlaller, kucultme, cift = _kafes_ihlalleri(range(TOHUM_SAYISI))
        self.assertGreater(
            kucultme, cift // 2,
            f"{kucultme}/{cift} ciftte kuculme olctum — engel katmani cogu "
            "sahnede HICBIR SEY cikarmiyorsa invariant testi vacuous'tur")

    # ── 3) ENGEL SIZINTISI — duzgun genisletmeyi YAKALAYAN kapi ───────────
    def test_engel_pikseli_50_tohumda_hicbir_alt_kumede_serbest_degil(self):
        """Cikarma SON islem mi? Genisletme ASIMETRIK olmasa bile burada patlar."""
        sizinti = []
        for tohum in range(TOHUM_SAYISI):
            zemin, moloz, arac = sahne(tohum)
            mk = {KATMAN_ZEMIN: zemin, KATMAN_MOLOZ: moloz, KATMAN_ARAC: arac}
            ham = {KATMAN_MOLOZ: moloz.astype(bool), KATMAN_ARAC: arac.astype(bool)}
            for alt in ENGEL_ALT_KUMELERI:
                if not alt:
                    continue
                birlesim = np.zeros_like(moloz, dtype=bool)
                for c in alt:
                    birlesim |= ham[c]
                n = int((alan(mk, alt) & birlesim).sum())
                if n:
                    sizinti.append((tohum, alt, n))
        self.assertEqual([], sizinti,
                         f"{len(sizinti)} vakada engel pikseli SERBEST "
                         f"(ilk 3: {sizinti[:3]})")

    # ── 4) MUTASYON KANITI ────────────────────────────────────────────────
    def _mutasyonlu_alanlar(self, tohumlar):
        """Ayni sahneler icin (yamasiz, yamali) serbest alan sozlukleri."""
        saglam, mutasyonlu = {}, {}
        for tohum in tohumlar:
            mk = _maskeler(tohum)
            saglam[tohum] = {a: alan(mk, a) for a in ENGEL_ALT_KUMELERI}
        gercek = C.cv2
        C.cv2 = _DilateEnjekteCv2(gercek)
        try:
            for tohum in tohumlar:
                mk = _maskeler(tohum)
                mutasyonlu[tohum] = {a: alan(mk, a) for a in ENGEL_ALT_KUMELERI}
        finally:
            C.cv2 = gercek
        return saglam, mutasyonlu

    def test_MUTASYON_dilate_SABIT_REFERANSA_gore_serbest_alani_BUYUTUR(self):
        """"Sessizce buyume" olayinin DOGRUDAN tanimi: ayni engel kumesinde,
        yamali cikti yamasiz ciktinin DISINA tasiyor mu?"""
        tohumlar = range(5)
        saglam, mut = self._mutasyonlu_alanlar(tohumlar)
        buyume = sum(int((mut[t][a] & ~saglam[t][a]).sum())
                     for t in tohumlar for a in ENGEL_ALT_KUMELERI)
        self.assertGreater(
            buyume, 0,
            "MUTASYON KONTROLU BOS: cikarmadan sonra `dilate` enjekte edildigi "
            "halde serbest alan HIC buyumedi — duzenek regresyon uretemiyor")

    def test_MUTASYON_dilate_ENGEL_PIKSELINE_SIZINTI_uretir(self):
        """(3) numarali kapinin gercekten AYIRT EDICI oldugunu kanitlar."""
        zemin, moloz, arac = sahne(0)
        mk = {KATMAN_ZEMIN: zemin, KATMAN_MOLOZ: moloz, KATMAN_ARAC: arac}
        engel = (moloz | arac).astype(bool)
        tam = (KATMAN_MOLOZ, KATMAN_ARAC)
        self.assertEqual(0, int((alan(mk, tam) & engel).sum()),
                         "yamasiz halde zaten sizinti var — kiyas anlamsiz")
        gercek = C.cv2
        C.cv2 = _DilateEnjekteCv2(gercek)
        try:
            sizinti = int((alan(mk, tam) & engel).sum())
        finally:
            C.cv2 = gercek
        self.assertGreater(sizinti, 0,
                           "engel sizintisi kapisi bu regresyonu YAKALAMIYOR")

    def test_MUTASYON_ASIMETRIK_genisletmeyi_KAFES_YAKALAR(self):
        """(1) numarali savunmanin vacuous OLMADIGINI kanitlar.

        Genisletme YALNIZ `KATMAN_ARAC` engel kumesinde varken uygulanir —
        yani "yeni katman eklendi, bir de su morfolojiyi koyayim" kalibinin
        birebir modeli. Kafes bunu YAKALAMALIDIR.
        """
        mk = _maskeler(0)
        gercek = C.cv2
        sahte = _AsimetrikEnjekteCv2(gercek)
        C.cv2 = sahte
        try:
            serbestler = {}
            for alt in ENGEL_ALT_KUMELERI:
                sahte.acik = KATMAN_ARAC in alt
                serbestler[alt] = alan(mk, alt)
        finally:
            C.cv2 = gercek
        ihlal = sum(int((serbestler[b] & ~serbestler[a]).sum())
                    for a in ENGEL_ALT_KUMELERI for b in ENGEL_ALT_KUMELERI
                    if set(a) < set(b))
        self.assertGreater(
            ihlal, 0,
            "ALT KUME KAFESI asimetrik genisletmeyi de yakalayamiyor — "
            "o zaman (1) numarali savunma HICBIR SEY yakalamiyor demektir")

    def test_MUTASYON_alt_kume_kafesi_bu_regresyonu_YAKALAYAMIYOR(self):
        """🔴 BILINEN SINIRI CIVILER (D-…, bu dosyanin baslik notu).

        `dilate` MONOTONDUR: her alt kumeye ayni sekilde uygulanan bir
        genisletme `A alt-kumesi B` sirasini BOZMAZ. Yani S3'un literal
        formulu bu regresyona KORDUR ve tek basina kapi olamaz.

        ⚠ BU TEST DUSERSE IYI HABERDIR: kafes artik duzgun genisletmeyi de
        yakaliyor demektir. O zaman bu testi SIL ve dosya basligindaki
        aciklamayi guncelle — sinir ortadan kalkmistir.
        """
        _saglam, mut = self._mutasyonlu_alanlar(range(5))
        ihlal = sum(int((mut[t][b] & ~mut[t][a]).sum())
                    for t in range(5)
                    for a in ENGEL_ALT_KUMELERI for b in ENGEL_ALT_KUMELERI
                    if set(a) < set(b))
        self.assertEqual(
            0, ihlal,
            "kafes artik duzgun genisletmeyi YAKALIYOR — bu bir iyilesmedir; "
            "testi sil ve dosya basligindaki sinir notunu guncelle")

    def test_MUTASYON_geri_alininca_invariant_YENIDEN_saglaniyor(self):  # noqa: E501
        """Yamanin gercekten geri alindigini kanitlar (sizinti kontrolu)."""
        ihlaller, _k, _c = _kafes_ihlalleri(range(5))
        self.assertEqual([], ihlaller)
        self.assertIs(C.cv2, cv2, "modulun `cv2`si yamali kalmis")

    # ── 4) BOS ENGEL MASKESI serbest alani BIREBIR birakmali ──────────────
    def test_bos_engel_maskesi_serbest_alani_DEGISTIRMIYOR(self):
        zemin, moloz, _arac = sahne(42)
        bos = np.zeros_like(moloz)
        mk_yok = {KATMAN_ZEMIN: zemin, KATMAN_MOLOZ: moloz}
        mk_bos = {KATMAN_ZEMIN: zemin, KATMAN_MOLOZ: moloz, KATMAN_ARAC: bos}
        s_yok = alan(mk_yok, (KATMAN_MOLOZ,))
        s_bos = alan(mk_bos, (KATMAN_MOLOZ, KATMAN_ARAC))
        self.assertEqual(0, int((s_yok ^ s_bos).sum()))

    def test_bos_engel_kumesi_en_genis_serbest_alani_verir(self):
        """`()` alt kumesi kafesin TEPESIDIR: her alt kume onun icinde kalmali."""
        mk = _maskeler(3)
        ust = alan(mk, ())
        for alt in ENGEL_ALT_KUMELERI[1:]:
            self.assertEqual(0, int((alan(mk, alt) & ~ust).sum()),
                             f"{alt} kumesi bos kumeden GENIS serbest alan verdi")

    # ── 5) EKSIK KATMAN sessizce serbest alani BUYUTMEMELI ────────────────
    def test_eksik_katman_serbest_alani_buyutmuyor(self):
        zemin, moloz, _arac = sahne(42)
        mk = {KATMAN_ZEMIN: zemin, KATMAN_MOLOZ: moloz}   # ARAC sozlukte YOK
        s_yok = alan(mk, (KATMAN_MOLOZ,))
        s_eksik = alan(mk, (KATMAN_MOLOZ, KATMAN_ARAC))
        self.assertEqual(0, int((s_eksik & ~s_yok).sum()))

    # ── 6) DAVRANIS: hicbir engel pikseli serbest olamaz ──────────────────
    def test_hicbir_engel_pikseli_serbest_degil(self):
        zemin, moloz, arac = sahne(7)
        mk = {KATMAN_ZEMIN: zemin, KATMAN_MOLOZ: moloz, KATMAN_ARAC: arac}
        s = alan(mk, (KATMAN_MOLOZ, KATMAN_ARAC))
        sizinti = int((s & (moloz | arac).astype(bool)).sum())
        self.assertEqual(0, sizinti, f"{sizinti} px engel uzerinde serbest")


    # ── 7) `serbest ALT-KUMESI zemin` — T102 · D-171 §3 ───────────────────
    # UCUNCU KACIS YOLU. Kafes (1) ve engel sizintisi (2) "dilate + engeli
    # TEKRAR cikar" yamasini IKISI DE gecirir; buyume ETIKETSIZ ARKA PLANA
    # olur ve mimarinin "bilinmeyen -> engel" kuralini ihlal eder.
    def test_serbest_alan_ZEMIN_ALT_KUMESIDIR_50_tohum(self):
        ihlaller = _zemin_disi_ihlaller(range(TOHUM_SAYISI))
        self.assertEqual(
            [], ihlaller,
            f"{len(ihlaller)} vakada serbest alan ZEMIN DISINA tasti — "
            f"etiketsiz arka plan surulebilir sayildi (ilk 3: {ihlaller[:3]})")

    def test_POZITIF_KONTROL_sahne_zemin_disinda_ETIKETSIZ_alan_iceriyor(self):
        """Yukaridaki test ancak tasacak YER varsa ayirt edicidir.

        Sahnede zemin disinda etiketsiz bir kusak OLMAZSA `serbest & ~zemin`
        zaten hep 0 cikar ve test BOS YERE yesil yanar (D-15/K-04).
        """
        for tohum in (0, 17, 49):
            mk = _maskeler(tohum)
            zemin = _zemin_maskesi(mk)
            disari = int(zemin.size - zemin.sum())
            self.assertGreater(disari, 0,
                               f"tohum {tohum}: zemin tuvali dolduruyor, "
                               "tasacak yer YOK")
            engel = np.zeros(zemin.shape, dtype=bool)
            for c in ENGEL_ALT_KUMELERI[-1]:
                engel |= mk[c].astype(bool)
            etiketsiz = int((~zemin & ~engel).sum())
            self.assertEqual(
                disari, etiketsiz,
                f"tohum {tohum}: zemin disinda {disari - etiketsiz} px ENGEL "
                "var — kusak tamamen etiketsiz degil, kontrol zayiflar")

    def test_MUTASYON_kenar_yumusatma_ZEMIN_DISINA_TASAR_ama_1_ve_2_GECER(self):
        """🔴 T102'nin ASIL KAPISI — ve yeni savunmanin GEREKLI oldugunun kaniti.

        Ayni yamada UC olcu birden alinir:
          · (A) `serbest ALT-KUMESI zemin`  -> DUSMELI  (yeni savunma yakalar)
          · (1) alt kume kafesi             -> GECMELI  (kor oldugu kanit)
          · (2) engel pikseli sizintisi     -> GECMELI  (kor oldugu kanit)

        ⚠ (1)/(2) icin yazilan "GECMELI" iddialari BILINEN SINIRI civiler.
        Bunlar duserse IYI HABERDIR (eski kapilar guclenmis demektir); o zaman
        bu test guncellenmeli, `serbest ALT-KUMESI zemin` kapisi KALMALIDIR.
        """
        gercek = C.serbest_alan
        C.serbest_alan = _KenarYumusatmaYamasi(gercek)
        try:
            tohumlar = range(5)
            zemin_disi = sum(n for _t, _a, n in _zemin_disi_ihlaller(tohumlar))
            kafes, _kucultme, _cift = _kafes_ihlalleri(tohumlar)
            # ⚠ Sizinti YALNIZ o alt kumede ENGEL SAYILAN siniflara karsi
            # olculur. Ilk yazimimda birlesimi sabit `moloz|arac` almistim ve
            # 22017 px "sizinti" cikti — oysa `(MOLOZ,)` kosumunda `arac` zaten
            # cikarilmamisti, yani o bir ihlal DEGILDI. Kapinin kendi tanimi
            # (`test_engel_pikseli_...`) ile AYNI olmalidir.
            sizinti = 0
            for tohum in tohumlar:
                mk = _maskeler(tohum)
                for alt in ENGEL_ALT_KUMELERI:
                    if not alt:
                        continue
                    birlesim = np.zeros(mk[KATMAN_ZEMIN].shape, dtype=bool)
                    for c in alt:
                        birlesim |= mk[c].astype(bool)
                    sizinti += int((alan(mk, alt) & birlesim).sum())
        finally:
            C.serbest_alan = gercek

        self.assertGreater(
            zemin_disi, 0,
            "MUTASYON KONTROLU BOS: `dilate + engeli tekrar cikar` yamasi "
            "zemin disina HIC tasmadi — yeni kapi regresyon uretemiyor")
        self.assertEqual(
            [], kafes,
            f"ALT KUME KAFESI bu yamayi artik YAKALIYOR ({len(kafes)} ihlal) "
            "— iyi haber; testi guncelle, yeni kapi yine de kalsin")
        self.assertEqual(
            0, sizinti,
            f"ENGEL SIZINTISI kapisi bu yamayi artik YAKALIYOR ({sizinti} px) "
            "— iyi haber; testi guncelle, yeni kapi yine de kalsin")

    def test_MUTASYON_kenar_yumusatma_geri_alininca_YENIDEN_saglaniyor(self):
        """Yamanin sizmadigini kanitlar."""
        self.assertEqual([], _zemin_disi_ihlaller(range(5)))
        self.assertIs(C.serbest_alan, _ORIJINAL_SERBEST_ALAN,
                      "modulun `serbest_alan`i yamali kalmis")


if __name__ == "__main__":
    unittest.main()
