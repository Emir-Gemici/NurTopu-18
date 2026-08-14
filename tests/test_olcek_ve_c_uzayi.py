"""T43 KAPISI: Halka 5 (olcek) sahiplendi mi, C-uzayi analyze_path kolunda mi?

Kusur (REVIEW_LOG D-59, D-22):
  · `mpp` saha kod yolunda URETILEMIYORDU (Halka 5 SAHIPSIZ) ve
    `olcek_px(None)` sessizce `m = 1.0` alip `r_gerekli_px`'i 1,10 PIKSEL
    yapiyordu. Bu "olcek yok" degil "olcek 1 m/piksel" demektir; gercek deger
    kompozit arenada 12,7 px. Govde acikligi ~11 kat kuculuyordu, uyari YOK.
  · `analyze_path` kolunda C-uzayi hic yoktu: `yol_duzelt`in gorus-hatti
    kisayolu pikselin SERBEST olmasini ariyor, ACIKLIGINI degil. Olculdu:
    kusursuz yer gercegi maskesiyle arena kompozitinde darbogaz 6 karenin
    4'unde 1,0 px ve karar zinciri 7/7 reddediyordu.

Bu paket UC seyi kanitlar:
  1. Olcek sozlesmesi fail-closed — tahmini olcek URETMEZ.
  2. C-uzayi ANTI-EXTENSIVE (madde 15): serbest(sonra) subset serbest(once).
  3. POZITIF KONTROL — C-uzayi devre disi birakilinca eski kusur (rota
     molozu siyiriyor, darbogaz ~1 px) GERI GELIR.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import cv2
import numpy as np

KOK = Path(__file__).resolve().parents[1]
if str(KOK / "codes") not in sys.path:
    sys.path.insert(0, str(KOK / "codes"))

from costmap_path_finder import R_GEREKLI_M, olcek_px
from karar_sozlesmesi import (OLCEK_YOK_SEBEBI, ROTA_DARBOGAZ_TAM_ORANI,
                              ROTA_GUVEN_ESIGI, SARTNAME_ASGARI_IRTIFA_M,
                              TELEMETRI_IRTIFA_TAZELIK_S,
                              mpp_irtifadan, olcek_gecerli_mi,
                              r_gerekli_piksel, rota_olcek_reddi)
from rpi_inference import analyze_path

H, W = 600, 900


def _dar_gecitli_sahne(gecit_px=30, mpp=0.05):
    """Tam genislikte bariyer + tek gecit; gecit fiziksel gerekten DAR.

    `r_gerekli_px = 1,10 / mpp`. `gecit_px` yari-genisligi bundan kucukse
    C-uzayi bu gecidi kapatmak ZORUNDADIR.
    """
    # ⚠ T48: eskiden `np.ones(...)` idi (kaplama %100) ve zemin kaplama kapisi
    # onu HAKLI OLARAK supheli sayiyor. Alan 450 px genisligindeki tek koridora
    # indirildi -> kaplama %50, tavanin altinda; testin olctugu sey degismedi.
    trav = np.zeros((H, W), np.uint8)
    trav[:, 60:510] = 1
    engel = np.zeros((H, W), np.uint8)
    engel[290:310, :] = 1
    kx = W // 6
    engel[290:310, kx - gecit_px // 2:kx + gecit_px // 2] = 0
    return trav, engel, mpp


class OlcekSozlesmesiTests(unittest.TestCase):
    """Halka 5 — `mpp` uretimi ve fail-closed davranis."""

    def test_canli_irtifa_tazelik_esigi_sozlesmede_kilitli(self):
        """T70: bayat son irtifa varsayimla yeniden kullanilamaz."""
        self.assertEqual(0.50, TELEMETRI_IRTIFA_TAZELIK_S)

    def test_fov_yolu_bilinen_geometriyi_uretir(self):
        # h=40 m, FOV=60 deg, W=1024 -> 2*40*tan(30) / 1024
        beklenen = (2.0 * 40.0 * np.tan(np.radians(30.0))) / 1024.0
        self.assertAlmostEqual(
            beklenen, mpp_irtifadan(40.0, 1024, yatay_fov_derece=60.0), places=9)

    def test_odak_yolu_pinhole(self):
        self.assertAlmostEqual(
            40.0 / 900.0, mpp_irtifadan(40.0, 1024, odak_px=900.0), places=9)

    def test_gecersiz_girdi_TAHMIN_URETMEZ(self):
        kotu = [
            (None, 1024, {"yatay_fov_derece": 60.0}),
            (40.0, None, {"yatay_fov_derece": 60.0}),
            (0.0, 1024, {"yatay_fov_derece": 60.0}),
            (-5.0, 1024, {"yatay_fov_derece": 60.0}),
            (float("nan"), 1024, {"yatay_fov_derece": 60.0}),
            (float("inf"), 1024, {"yatay_fov_derece": 60.0}),
            (True, 1024, {"yatay_fov_derece": 60.0}),
            (40.0, 1024, {}),                       # ne FOV ne odak
            (40.0, 1024, {"yatay_fov_derece": 0.0}),
            (40.0, 1024, {"yatay_fov_derece": 180.0}),
            (10_000.0, 1024, {"yatay_fov_derece": 60.0}),   # makul band disi
        ]
        for h, w, kw in kotu:
            with self.subTest(irtifa=h, genislik=w, **kw):
                self.assertIsNone(mpp_irtifadan(h, w, **kw))

    def test_olcek_yoksa_kanonik_OLCEK_YOK_reddi(self):
        for kotu in (None, 0.0, -1.0, float("nan"), float("inf"), True, "x"):
            with self.subTest(mpp=kotu):
                ret = rota_olcek_reddi(kotu)
                self.assertIsNotNone(ret)
                self.assertEqual(OLCEK_YOK_SEBEBI, ret[0])
        self.assertIsNone(rota_olcek_reddi(0.05))

    def test_r_gerekli_piksel_olcek_yoksa_None(self):
        """`None` = 'kisit UYGULANAMAZ', 'kisit yok' DEGIL."""
        self.assertIsNone(r_gerekli_piksel(None, R_GEREKLI_M))
        self.assertIsNone(r_gerekli_piksel(0.0, R_GEREKLI_M))
        self.assertAlmostEqual(
            R_GEREKLI_M / 0.0868, r_gerekli_piksel(0.0868, R_GEREKLI_M), places=6)

    def test_olcek_gecerli_mi_fail_closed(self):
        self.assertTrue(olcek_gecerli_mi(0.05))
        for kotu in (None, True, False, 0.0, -1.0, float("nan"), "0.05"):
            self.assertFalse(olcek_gecerli_mi(kotu), kotu)

    def test_SESSIZ_VARSAYIM_belgelendi(self):
        """`olcek_px(None)` hala 1,10 px veriyor — bu kusur ACIKCA kayitli.

        Sayiyi degistirmiyoruz (sentetik 'olceksiz kip' ona dayali); ama
        gorev yolu artik `rota_olcek_reddi` ile bunu KULLANMIYOR.
        """
        self.assertAlmostEqual(1.10, olcek_px(None)["r_gerekli_px"], places=6)
        self.assertAlmostEqual(
            R_GEREKLI_M / 0.0868, olcek_px(0.0868)["r_gerekli_px"], places=6)
        # Aradaki oran ~11x: sessiz varsayimın buyuklugu.
        self.assertGreater(
            olcek_px(0.0868)["r_gerekli_px"] / olcek_px(None)["r_gerekli_px"],
            10.0)

    def test_asgari_irtifa_sabiti_sozlesmeden(self):
        self.assertEqual(30.0, SARTNAME_ASGARI_IRTIFA_M)


class CUzayiMadde15Tests(unittest.TestCase):
    """Madde 15: serbest alan yalniz DARALABILIR."""

    def _clean(self, trav, engel, mpp):
        _y, _g, _w, clean = analyze_path(
            trav, engel_mask=engel, mpp=mpp, return_clean=True)
        return clean

    def test_c_uzayi_serbest_alani_BUYUTMEZ(self):
        for gecit in (20, 40, 80, 160):
            for mpp in (0.02, 0.05, 0.0868):
                with self.subTest(gecit=gecit, mpp=mpp):
                    trav, engel, _ = _dar_gecitli_sahne(gecit, mpp)
                    once = self._clean(trav, engel, None)
                    dist = cv2.distanceTransform(once, cv2.DIST_L2, 5)
                    r = r_gerekli_piksel(mpp, R_GEREKLI_M)
                    c_uzayi = (dist >= r).astype(np.uint8)
                    fazla = int(np.count_nonzero((c_uzayi > 0) & (once == 0)))
                    self.assertEqual(
                        0, fazla,
                        "C-uzayi serbest alani BUYUTTU — madde 15 ihlali")
                    self.assertLessEqual(int(c_uzayi.sum()), int(once.sum()))

    def test_olceksiz_kipte_koridor_DEGISMEZ(self):
        """`mpp=None` -> C-uzayi uygulanmaz, eski davranis birebir korunur."""
        trav, engel, _ = _dar_gecitli_sahne(80, 0.05)
        a = analyze_path(trav, engel_mask=engel, mpp=None)
        b = analyze_path(trav, engel_mask=engel)
        self.assertEqual(a[:2], b[:2])


class CUzayiKararTests(unittest.TestCase):
    """C-uzayi gercekten fiziksel acikligi zorluyor mu?"""

    def test_gerekten_DAR_gecit_fail_closed_reddedilir(self):
        """Gecit yari-genisligi `r_gerekli_px`in altindaysa karar VERILMEZ."""
        mpp = 0.05                      # r_gerekli_px = 22.0
        r = r_gerekli_piksel(mpp, R_GEREKLI_M)
        trav, engel, _ = _dar_gecitli_sahne(gecit_px=24, mpp=mpp)   # yari = 12 < 22
        olceksiz = analyze_path(trav, engel_mask=engel, mpp=None)
        olcekli = analyze_path(trav, engel_mask=engel, mpp=mpp,
                               return_reason=True)
        self.assertIsNotNone(
            olceksiz[0],
            "POZITIF KONTROL: olceksiz kip bu dar gecidi kabul ETMIYOR; "
            "sahne kusuru ayirt edemiyor")
        self.assertIsNone(
            olcekli[0],
            f"gecit yari-genisligi 12 px < r_gerekli {r:.1f} px oldugu halde "
            "karar uretildi")

    def test_yeterince_GENIS_gecit_kabul_edilir(self):
        mpp = 0.05
        trav, engel, _ = _dar_gecitli_sahne(gecit_px=140, mpp=mpp)  # yari 70 > 22
        yol, guven, wps = analyze_path(trav, engel_mask=engel, mpp=mpp)
        self.assertEqual(1, yol)
        self.assertGreaterEqual(len(wps), 2)

    def test_darbogaz_C_UZAYI_TABANININ_altina_inemez(self):
        """C-uzayi acikken rota uzerindeki en dar nokta >= r_gerekli_px."""
        mpp = 0.05
        r = r_gerekli_piksel(mpp, R_GEREKLI_M)
        trav, engel, _ = _dar_gecitli_sahne(gecit_px=200, mpp=mpp)
        yol, guven, wps, clean, ret, olcum = analyze_path(
            trav, engel_mask=engel, mpp=mpp, return_clean=True,
            return_reason=True, return_olcum=True)
        self.assertIsNotNone(yol)
        self.assertGreaterEqual(olcum["darbogaz_px"], r - 1e-6)
        self.assertFalse(olcum["olceksiz"])
        self.assertAlmostEqual(r, olcum["r_gerekli_px"], places=6)

    def test_olcum_sozlugu_olceksiz_kipi_ISARETLER(self):
        trav, engel, _ = _dar_gecitli_sahne(200, 0.05)
        *_, olcum = analyze_path(
            trav, engel_mask=engel, mpp=None, return_olcum=True)
        self.assertTrue(olcum["olceksiz"])
        self.assertIsNone(olcum["mpp"])
        self.assertIsNone(olcum["r_gerekli_px"])

    def test_POZITIF_KONTROL_c_uzayisiz_rota_molozu_siyiriyor(self):
        """C-uzayi kapaliyken darbogaz gercekten kucuk kaliyor mu?

        Bu test gecmezse yukaridaki kapilar bir sey kanitlamiyor demektir
        (D-15 vakum kapi korumasi).
        """
        mpp = 0.05
        trav, engel, _ = _dar_gecitli_sahne(gecit_px=24, mpp=mpp)
        *_, olcum = analyze_path(
            trav, engel_mask=engel, mpp=None, return_olcum=True)
        self.assertIsNotNone(olcum)
        self.assertLess(
            olcum["darbogaz_px"], r_gerekli_piksel(mpp, R_GEREKLI_M),
            "olceksiz kipte darbogaz zaten yeterli — sahne ayirt edici degil")


class KBRolTests(unittest.TestCase):
    """T43 · Gorev 3: C-uzayi gelince K-B'nin rolu ne oldu?"""

    def test_c_uzayi_guvene_HESAPLANABILIR_TABAN_koyar(self):
        """guven >= r_gerekli_px / (ROTA_DARBOGAZ_TAM_ORANI * icerik_w).

        Bu, K-B'nin olceklı kipte NE ZAMAN atesleyebilecegini belirler ve
        esigin gerekcesi bu esitsizlige dayanir (CONTRACTS SS6.3).
        """
        mpp, icerik_w = 0.05, float(W)
        r = r_gerekli_piksel(mpp, R_GEREKLI_M)
        taban = min(1.0, r / (ROTA_DARBOGAZ_TAM_ORANI * icerik_w))
        trav, engel, _ = _dar_gecitli_sahne(gecit_px=200, mpp=mpp)
        yol, guven, wps = analyze_path(trav, engel_mask=engel, mpp=mpp)
        self.assertIsNotNone(yol)
        self.assertGreaterEqual(guven + 1e-9, taban)

    def test_K_B_ince_olcekte_ATESLEYEMEZ_kaba_olcekte_ATESLER(self):
        """Kritik olcek: mpp > R_GEREKLI_M / (K-B * TAM_ORAN * icerik_w)."""
        kritik = R_GEREKLI_M / (ROTA_GUVEN_ESIGI * ROTA_DARBOGAZ_TAM_ORANI * W)
        for mpp in (kritik / 4.0, kritik / 2.0):
            taban = r_gerekli_piksel(mpp, R_GEREKLI_M) / (
                ROTA_DARBOGAZ_TAM_ORANI * W)
            self.assertGreaterEqual(
                taban, ROTA_GUVEN_ESIGI,
                f"mpp={mpp}: K-B olcekli kipte atesleyebiliyor")
        for mpp in (kritik * 2.0, kritik * 4.0):
            taban = r_gerekli_piksel(mpp, R_GEREKLI_M) / (
                ROTA_DARBOGAZ_TAM_ORANI * W)
            self.assertLess(
                taban, ROTA_GUVEN_ESIGI,
                f"mpp={mpp}: K-B kaba olcekte de atesleyemiyor")


if __name__ == "__main__":
    unittest.main(verbosity=2)
