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
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import cv2

KOK = Path(__file__).resolve().parents[1]
DEFTER = KOK / "config" / "model_registry.json"
AYNA = KOK / "jetson_paket" / "config" / "model_registry.json"
FIGUR = KOK / "data" / "arena_referans" / "sartname_s9_arena.png"
K109_HAM = KOK / "results" / "gece_20260826" / "gece_v7a_olcum.json"

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

    @unittest.skipUnless(FIGUR.is_file(), "figur diskte yok")
    def test_TABAN_surumde_de_ayni_PAYDA_orani(self):
        """v35 tabani ayni kalibi tutuyor mu (0,0903 / 0,1508)?"""
        taban = _65_hattinin_degeri(self.profil, "v35")
        # k109 hattinin v35 degeri defterde DUZ METINDEDIR:
        # `gercek_kare_zemin_kaplamasi.not` ve `_surum_karari` "0,15" der;
        # ham sayi `142_gece_olcum.py` ciktisinda 0,1508'dir.
        k109_v35 = 0.1508
        beklenen = self._icerik_tuval_orani()
        self.assertAlmostEqual(
            beklenen, taban / k109_v35, delta=0.01,
            msg=(f"v35: {taban} / {k109_v35} = {taban / k109_v35:.4f} != "
                 f"icerik/tuval {beklenen:.6f}"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
