"""T135 KAPISI (D-268 §6 · results/t142/olcum.md §3) — letterbox paydasi.

1. `jetson_paket/kod/kamera_dogrula.py` zinciri `rota_bul`a `icerik` GECIRMIYORDU:
   16:9 karede kirpilmis maske + tam tuval paydasi zemin saglamlik kapisinin
   IKI kolunu da olduruyordu (kaplama <= 0,5625, kenar <= 0,2815). Simdi
   `zincir_durumu` icerigi gecirir; sentetik cokus maskesi (icerigin tamami
   zemin) kapiyi ATESLER. Mutasyon: `icerik=icerik` kaldirilinca test duser.
2. `rota_bul(icerik=None)` letterbox gorunumlu maskede SESSIZ fail-open'di.
   Davranis DEGISMEDI; `sebep`e/loga ICERIK_YOK_LETTERBOX_SUPHESI notu ve
   `uyari` alani eklendi. Mutasyon: `letterbox_suphesi` hep False yapilinca duser.

Model YOK: maske ureticisi sahte; `_preprocess`, `_maskeleri_icerige_kirp`,
`rota_bul` URETIMIN KENDISI (jetson_paket/kod aynalari, ikiz oldugu ayrica
`test_paket_aynalari_ikiz` ile olculur).
"""

from __future__ import annotations

import hashlib
import logging
import sys
import unittest
from pathlib import Path

import numpy as np

KOK = Path(__file__).resolve().parents[1]
PAKET_KOD = KOK / "jetson_paket" / "kod"
for _p in (PAKET_KOD, KOK / "codes"):     # codes/ ONDE: uretim modulleri codes'tan yuklenir
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import costmap_path_finder as CPF  # noqa: E402
import kamera_dogrula as KD  # noqa: E402
import rpi_inference as R  # noqa: E402
from karar_sozlesmesi import (  # noqa: E402
    ICERIK_YOK_LETTERBOX_SUPHESI_NOTU, LETTERBOX_SUPHE_BANT_ORANI,
    ZEMIN_KAPLAMA_TAVANI, ZEMIN_KENAR_DAYANMA_TAVANI, ZEMIN_MASKESI_SUPHELI_SEBEBI,
    zemin_kenar_dayanmasi)


def _kare_16_9(w=320, h=180):
    """Sentetik 16:9 BGR kare (dokulu ki normalize_light bozulmasin)."""
    rng = np.random.default_rng(7)
    return rng.integers(40, 200, size=(h, w, 3), dtype=np.uint8)


def _cokus_maskeleri(tuval):
    """Tum tuval zemin (sinif 0), engel yok: icerik kirpmasi sonrasi icerigin
    %100'u zemin ve cevrenin %100'u dayanmis -> kapi ateslemeli."""
    yan = tuval.shape[0]
    return {0: np.ones((yan, yan), np.uint8), 1: np.zeros((yan, yan), np.uint8)}


class KameraDogrulaIcerikTests(unittest.TestCase):
    def test_letterboxlu_16_9_karede_kapi_ATESLER(self):
        """icerik GECIRILINCE cokus maskesi ZEMIN_MASKESI_SUPHELI doner."""
        durum = KD.zincir_durumu(_kare_16_9(), _cokus_maskeleri, rota_bul=CPF.rota_bul,
                                 preprocess=R._preprocess, kirp=R._maskeleri_icerige_kirp)
        self.assertEqual(ZEMIN_MASKESI_SUPHELI_SEBEBI, durum)

    def test_icerik_gecirilmezse_kapi_OLU_kalirdi(self):
        """Kusurun kendisi olculur: ayni maske, `icerik=None` -> kapi susar
        (kaplama = 0,5625 <= tavan). Bu test kusuru BELGELER; yukaridaki test
        duzeltmeyi kilitler."""
        tuval, _, icerik = R._preprocess(_kare_16_9())
        mk = R._maskeleri_icerige_kirp(_cokus_maskeleri(tuval), icerik)
        # T142 (D-286) sonrasi tavan 0,55: letterbox paydasinda kaplama 0,5625 artik
        # tavani ASAR ama kenar kolu olu (tavan 2h/(4w-4)=0,2815 < 0,40) -> AND kapisi susar.
        yan = mk[0].shape[0]
        kap = float(mk[0].mean())
        ken = zemin_kenar_dayanmasi(mk[0], (0, 0, yan, yan))
        self.assertFalse(kap > ZEMIN_KAPLAMA_TAVANI and ken > ZEMIN_KENAR_DAYANMA_TAVANI,
                         f"kap={kap:.4f} ken={ken:.4f}")
        durum_none = CPF.rota_bul(mk, mpp=None, plan=False, gorsel_cikti=False)["durum"]
        self.assertNotEqual(ZEMIN_MASKESI_SUPHELI_SEBEBI, durum_none)

    def test_zincir_kirpmayi_ve_icerigi_URETIMDEN_alir(self):
        """Sahte kirp/rota_bul ile: zincir preprocess'in icerigini kirp'e VE
        rota_bul'a aynen gecirir (imza sozlesmesi)."""
        gorulen = {}

        def kirp(mk, icerik):
            gorulen["kirp"] = icerik
            return mk

        def rota_bul(mk, **kw):
            gorulen["rota"] = kw
            return {"durum": "SAHTE"}

        durum = KD.zincir_durumu(_kare_16_9(320, 180), _cokus_maskeleri, rota_bul=rota_bul,
                                 preprocess=R._preprocess, kirp=kirp)
        self.assertEqual("SAHTE", durum)
        self.assertEqual((0, 70, 320, 180), gorulen["kirp"])
        self.assertEqual((0, 70, 320, 180), gorulen["rota"]["icerik"])
        self.assertFalse(gorulen["rota"]["plan"])


class RotaBulLetterboxSuphesiTests(unittest.TestCase):
    def _maske_16_9_tuvalde(self):
        tuval, _, icerik = R._preprocess(_kare_16_9())
        return R._maskeleri_icerige_kirp(_cokus_maskeleri(tuval), icerik), icerik

    def test_icerik_None_letterboxta_NOT_ve_uyari(self):
        mk, _ = self._maske_16_9_tuvalde()
        with self.assertLogs("costmap_path_finder", level=logging.WARNING) as log:
            c = CPF.rota_bul(mk, mpp=None, plan=False, gorsel_cikti=False)
        self.assertEqual(ICERIK_YOK_LETTERBOX_SUPHESI_NOTU, c["uyari"])
        self.assertIn(ICERIK_YOK_LETTERBOX_SUPHESI_NOTU, c["sebep"])
        self.assertTrue(any(ICERIK_YOK_LETTERBOX_SUPHESI_NOTU in s for s in log.output), log.output)

    def test_davranis_DEGISMEDI_yalniz_not(self):
        """Ayni girdi: durum/yol_no/guven/waypoints `_rota_bul_cekirdek` ile BIREBIR."""
        mk, _ = self._maske_16_9_tuvalde()
        c = CPF.rota_bul(mk, mpp=None, plan=False, gorsel_cikti=False)
        ham = CPF._rota_bul_cekirdek(mk, mpp=None, plan=False, gorsel_cikti=False)
        for alan in ("durum", "yol_no", "guven", "waypoints_px", "darbogaz_m"):
            self.assertEqual(ham[alan], c[alan], alan)
        self.assertTrue(c["sebep"].startswith(ham["sebep"]))

    def test_icerik_GECIRILINCE_not_yok(self):
        mk, icerik = self._maske_16_9_tuvalde()
        c = CPF.rota_bul(mk, mpp=None, plan=False, gorsel_cikti=False, icerik=icerik)
        self.assertNotIn("uyari", c)
        self.assertNotIn(ICERIK_YOK_LETTERBOX_SUPHESI_NOTU, c["sebep"])

    def test_kare_mozaikte_ve_bos_maskede_not_YOK(self):
        """Mesru kare mozaik (zemin cerceveye kadar) ve tamamen bos maske suphe degil."""
        yan = 200
        dolu = {0: np.ones((yan, yan), np.uint8), 1: np.zeros((yan, yan), np.uint8)}
        self.assertFalse(CPF.letterbox_suphesi(dolu, None))
        bos = {0: np.zeros((yan, yan), np.uint8)}
        self.assertFalse(CPF.letterbox_suphesi(bos, None))
        c = CPF.rota_bul(bos, mpp=None, plan=False, gorsel_cikti=False)
        self.assertNotIn("uyari", c)
        # yalniz TEK bant bos (ust) -> letterbox degil
        tek = {0: np.ones((yan, yan), np.uint8)}
        tek[0][: int(yan * LETTERBOX_SUPHE_BANT_ORANI) + 2, :] = 0
        self.assertFalse(CPF.letterbox_suphesi(tek, None))
        # kare olmayan tuvalde suphe yok
        dik = {0: np.zeros((180, 320), np.uint8)}
        dik[0][60:120, :] = 1
        self.assertFalse(CPF.letterbox_suphesi(dik, None))


class PaketAynasiTests(unittest.TestCase):
    def test_paket_aynalari_ikiz(self):
        for ad in ("costmap_path_finder.py", "karar_sozlesmesi.py", "rpi_inference.py"):
            with self.subTest(ad=ad):
                a = hashlib.sha256((KOK / "codes" / ad).read_bytes()).hexdigest()
                b = hashlib.sha256((PAKET_KOD / ad).read_bytes()).hexdigest()
                self.assertEqual(a, b, ad)


if __name__ == "__main__":
    unittest.main()
