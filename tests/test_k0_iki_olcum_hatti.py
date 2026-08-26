"""T154 · K0 FIGUR ZEMIN ORANI — AYNI AD, IKI OLCUM HATTI (D-294 §4, ikinci madde)

Kusur sinifi: defterde iki AYRI olcum hattinin sayisi AYNI ADLA duruyor.

  * `metrics.k0_korluk.figur_zemin_orani` -> v36 icin **0,0266**
    kaynak `scripts/olcum/65_kabul_denetcisi.py::kaplama()`; oran LETTERBOX
    TUVALI uzerinden alinir (`(mk[0] > 0).mean()`).
  * `metrics._surum_karari` metnindeki "figur zemin 0,15->0,04" -> v36 icin
    **0,0444**; kaynak k109 hatti `scripts/olcum/109_t122_kiyas.py`
    (`zemin_ve_mevcut_engel` -> `alani_kirp`), payda ICERIK DIKDORTGENI.

Okuyucu ikisini ayni sey sanip "defter kendi kendisiyle celisiyor" diye okuyabilir.
ALAN ADI DEGISTIRILMEZ (geriye uyumluluk: `65_kabul_denetcisi`, `118_t131_*`,
`test_k0_gorunurlugu`, `test_t132_taban_gorunurlugu` bu adi okuyor — D-263 §5);
bunun yerine defterde ACIKLAYICI NOT tutulur ve bu kapi notu kilitler.

🔴 Kapinin ASIL isi bir SAYI kilidi: iki hattin farkinin PAYDA oldugu, figurun
kendi geometrisinden (634x1059 -> icerik/tuval = 0,598678) TEKRAR HESAPLANIR.
Boylece not "guzel bir cumle" olmaktan cikar; yanlissa kapi duser.

T157/e (D-295 §4): iki bacagin da k109 sayisi HAM OLCUM CIKTISINDAN okunur.
Uretim bacagi zaten `gece_v7a_olcum.json`'dan okuyordu; taban bacagi ise
`k109_v35 = 0.1508` diye CIPLAK yaziliydi ve hicbir seye bagli degildi.
Artik `results/gece_20260826/v35_ref2_olcum.json` + `results/t152/
v35_t152_olcum.json` okunur, surum de o dosyalarin `agirlik` alanindan cozulur.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

import cv2

KOK = Path(__file__).resolve().parents[1]
DEFTER = KOK / "config" / "model_registry.json"
AYNA = KOK / "jetson_paket" / "config" / "model_registry.json"
FIGUR = KOK / "data" / "arena_referans" / "sartname_s9_arena.png"
K109_HAM = KOK / "results" / "gece_20260826" / "gece_v7a_olcum.json"

# T157/e: TABAN (v35) bacagi da HAM JSON'a baglidir. Onceden `k109_v35 = 0.1508`
# CIPLAK yaziliydi (D-295 §4): uretim bacagi olcumun kendisinden okurken taban
# bacagi elle kopyalanmis bir sayiyi kiyasliyordu — ham cikti degisse ya da sayi
# yanlis kopyalanmis olsa kapi bunu GOREMEZDI. Iki AYRI v35 kosumu baglanir;
# k109 figur olcumu SARTNAME FIGURUNDEN turer, yani kosum/kume degisse bile ayni
# cikmak ZORUNDADIR — ikisinin uyusmasi baglantiyi ayrica dogrular.
K109_TABAN_HAM = (KOK / "results" / "gece_20260826" / "v35_ref2_olcum.json",
                  KOK / "results" / "t152" / "v35_t152_olcum.json")
AGIRLIK_SURUM_DESENI = re.compile(r"navitas_seg_(v\d+)_best")

NOT_ALANI = "_iki_olcum_hatti_notu"

# Notun ADIYLA anmasi gereken seyler: iki hattin BETIGI, hangi JSON'dan
# okundugu ve iki PAYDA. Biri eksikse okuyucu hangi sayinin nereden geldigini
# yine bilemez, yani not isini gormemis olur.
NOTTA_GECMELI = (
    "65_kabul_denetcisi.py",
    "kaplama()",
    "109_t122_kiyas.py",
    "k109",
    "gece_v7a_olcum.json",
    "TUVAL",
    "ICERIK",
)


def _profil():
    return json.loads(DEFTER.read_text(encoding="utf-8"))["profiles"]["competition"]


def _uretim_surumu(profil):
    """`navitas-seg-v36-512` -> `v36` (defterdeki model_id'den, ciplak yazilmaz)."""
    for parca in profil["model_id"].split("-"):
        if parca.startswith("v") and parca[1:].isdigit():
            return parca
    raise AssertionError(f"model_id surum tasimiyor: {profil['model_id']}")


def _65_hattinin_degeri(profil, surum):
    """`figur_zemin_orani` icinden URETIM surumune ait kayit (65 hatti)."""
    ham = profil["metrics"]["k0_korluk"]["figur_zemin_orani"]
    if not isinstance(ham, list):          # eski SKALER bicim (T132 geriye uyum)
        return float(ham)
    for kayit in ham:
        if kayit.get("surum") == surum:
            return float(kayit["deger"])
    raise AssertionError(f"soyagacinda {surum} kaydi yok")


def _taban_hattinin_degeri():
    """(surum, k109 figur_zemin_orani) — CIPLAK sayi degil, HAM JSON (T157/e).

    Surum de sayinin kendi dosyasindan (`agirlik` alani) okunur; boylece
    "hangi surumun sayisi" sorusu testin metnine degil OLCUM CIKTISINA baglidir.
    """
    ilk = json.loads(K109_TABAN_HAM[0].read_text(encoding="utf-8"))
    m = AGIRLIK_SURUM_DESENI.search(str(ilk.get("agirlik", "")).replace("\\", "/"))
    if m is None:
        raise AssertionError(
            f"{K109_TABAN_HAM[0].name} `agirlik` alani surum tasimiyor: "
            f"{ilk.get('agirlik')!r}")
    return m.group(1), float(ilk["k109"]["figur_zemin_orani"])


class IkiOlcumHattiBelgeliTests(unittest.TestCase):
    """Defter, hangi sayinin hangi hattan geldigini SOYLUYOR mu?"""

    def setUp(self):
        self.profil = _profil()
        self.k0 = self.profil["metrics"]["k0_korluk"]

    def test_ACIKLAYICI_NOT_defterde_VAR(self):
        self.assertIn(
            NOT_ALANI, self.k0,
            "iki olcum hattini ayiran not silinmis; ayni ad iki sayiyi "
            "gosteriyor ve okuyucu hangisinin hangisi oldugunu bilemez "
            "(D-294 SS4)")

    def test_NOT_iki_hattin_da_KAYNAGINI_adiyla_aniyor(self):
        metin = self.k0.get(NOT_ALANI, "")
        for parca in NOTTA_GECMELI:
            with self.subTest(gecmeli=parca):
                self.assertIn(parca, metin,
                              f"not `{parca}` demiyor — hangi sayinin hangi "
                              f"hattan geldigi yine belirsiz kalir")

    def test_SURUM_KARARI_kendi_sayisinin_HANGI_HAT_oldugunu_soyluyor(self):
        """`_surum_karari` figur sayisi veriyorsa hatti da yazmali."""
        karar = self.profil.get("_surum_karari", "")
        if "figur zemin" not in karar:
            self.skipTest("`_surum_karari` figur zemin sayisi tasimiyor")
        self.assertIn(
            "k109", karar,
            "`_surum_karari` figur zemin sayisi veriyor ama hangi hattan "
            "oldugunu SOYLEMIYOR; k0_korluk.figur_zemin_orani ile ayni "
            "sanilir (D-294 SS4)")
        self.assertIn(
            NOT_ALANI, karar,
            f"`_surum_karari` okuyucuyu `{NOT_ALANI}` alanina yonlendirmiyor")

    def test_ALAN_ADI_DEGISMEDI(self):
        """Geriye uyumluluk: okuyan kod/testler bu adi bekliyor (D-263 SS5)."""
        self.assertIn("figur_zemin_orani", self.k0)
        self.assertIn("olculen", self.k0)

    def test_AYNA_defter_BAYT_ES(self):
        self.assertEqual(DEFTER.read_bytes(), AYNA.read_bytes(),
                         "jetson_paket defter aynasi kok defterden farkli — "
                         "saha paketi baska bir aciklama tasir")


class IkiHattinFarkiPaydaTests(unittest.TestCase):
    """🔴 SAYI KILIDI — fark PAYDADIR ve figurun geometrisinden hesaplanir."""

    def setUp(self):
        self.profil = _profil()
        self.surum = _uretim_surumu(self.profil)

    def _icerik_tuval_orani(self):
        """`rpi_inference._preprocess` letterbox'inda icerik / tuval alani.

        Model YUKLENMEZ: `_preprocess` kareyi `max(h, w)` kenarli bir tuvale
        ORTALAR, yani oran yalniz figurun en-boyuna baglidir.
        """
        img = cv2.imread(str(FIGUR))
        self.assertIsNotNone(img, f"figur okunamadi: {FIGUR}")
        h, w = img.shape[:2]
        yan = max(h, w)
        return (h * w) / float(yan * yan)

    @unittest.skipUnless(FIGUR.is_file() and K109_HAM.is_file(),
                         "figur ya da k109 ham ciktisi diskte yok")
    def test_URETIM_surumunde_iki_hattin_orani_PAYDA_oranidir(self):
        tuval_hatti = _65_hattinin_degeri(self.profil, self.surum)
        k109 = json.loads(K109_HAM.read_text(encoding="utf-8"))["k109"]
        icerik_hatti = float(k109["figur_zemin_orani"])
        beklenen = self._icerik_tuval_orani()
        olculen = tuval_hatti / icerik_hatti
        self.assertAlmostEqual(
            beklenen, olculen, delta=0.01,
            msg=(f"{self.surum}: 65 hatti {tuval_hatti} / k109 hatti "
                 f"{icerik_hatti} = {olculen:.4f}, oysa figurun icerik/tuval "
                 f"orani {beklenen:.6f}. Iki sayi ayni maskenin IKI PAYDAYLA "
                 f"okunusu DEGILSE defterdeki aciklama YANLISTIR"))

    @unittest.skipUnless(FIGUR.is_file() and all(p.is_file()
                                                 for p in K109_TABAN_HAM),
                         "figur ya da v35 k109 ham ciktilari diskte yok")
    def test_TABAN_surumde_de_ayni_PAYDA_orani(self):
        """Taban surum ayni kalibi tutuyor mu — SAYI HAM JSON'DAN (T157/e)."""
        surum, k109_taban = _taban_hattinin_degeri()
        taban = _65_hattinin_degeri(self.profil, surum)
        beklenen = self._icerik_tuval_orani()
        self.assertAlmostEqual(
            beklenen, taban / k109_taban, delta=0.01,
            msg=(f"{surum}: {taban} / {k109_taban} = "
                 f"{taban / k109_taban:.4f} != icerik/tuval {beklenen:.6f}"))

    @unittest.skipUnless(all(p.is_file() for p in K109_TABAN_HAM),
                         "v35 k109 ham ciktilari diskte yok")
    def test_TABAN_sayisi_CIPLAK_degil_HAM_JSONDAN(self):
        """Kaynak baglantisinin KENDISI kapidir: iki ayri kosum, ayni sayi."""
        degerler = {}
        for yol in K109_TABAN_HAM:
            ham = json.loads(yol.read_text(encoding="utf-8"))
            agirlik = str(ham.get("agirlik", ""))
            m = AGIRLIK_SURUM_DESENI.search(agirlik.replace("\\", "/"))
            with self.subTest(kaynak=yol.name):
                self.assertIsNotNone(
                    m, f"{yol.name} `agirlik` alani surum tasimiyor "
                       f"({agirlik!r}); hangi surumun sayisi oldugu KANITSIZ")
                degerler[yol.name] = (m.group(1),
                                      float(ham["k109"]["figur_zemin_orani"]))
        surumler = {v[0] for v in degerler.values()}
        self.assertEqual(
            1, len(surumler),
            f"taban kaynaklari AYNI surumden degil: {degerler}")
        sayilar = {round(v[1], 5) for v in degerler.values()}
        self.assertEqual(
            1, len(sayilar),
            f"k109 figur olcumu sartname figurunden turer, iki kosumda AYNI "
            f"cikmali; ayrisiyor: {degerler}")
        self.assertNotEqual(self.surum, surumler.pop(),
                            "taban kaynagi URETIM surumunu gosteriyor; taban "
                            "bacagi ayri bir surumu kiyaslamalidir")


if __name__ == "__main__":
    unittest.main(verbosity=2)
