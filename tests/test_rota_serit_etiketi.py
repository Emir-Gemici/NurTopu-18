"""T31 + T32 KAPISI: `road` etiketi ve guven ROTADAN mi olculuyor?

Kusur (REVIEW_LOG D-41, olcum: Claude 1 · 2026-08-10):
  · `open_path` koridorun UST %30 bandinin centroid'inden turetiliyordu.
    67 gercek drone karesinin 67'sinde yayinlanan etiket (hep `2`) rotanin
    GERCEKTEN gectigi seritle (32 karede 1, 35 karede 3) uyusmuyordu.
  · `confidence = in_third / bx.size` ayni banttan hesaplaniyordu: enjekte-kapi
    deneyinde kapi sol/orta/sag gezerken deger HIC degismiyordu
    (0,326 / 0,326 / 0,326) ve tespit KOTULESTIKCE yukseliyordu — az piksel
    tek ucte-bire duserse oran 1,0 olur.

`road` yalniz ekran etiketi degil, IKA'nin planlama girdisidir
(`comms/ika_receiver.py:11` -> `plan_path(route["road"])`), bu yuzden KRITIK.

Bu paket DORT seyi birden kanitlar:
  1. POZITIF KONTROL — eski centroid tanimi bu sahnelerde GERCEKTEN yanlis
     serit uretiyor. Yoksa test bosluk olur (REVIEW_LOG D-15 / K-04:
     "sifir olcum basari sayilmaz").
  2. Yeni tanim ayni sahnelerde BILINEN dogru seridi uretiyor.
  3. AYIRT EDICI sahne — rota serit degistirdiginde darbogaz tanimi ile
     baskin-serit tanimi ayrisiyor ve yalniz darbogaz dogru cevabi veriyor.
  4. T32 — kil gibi ince koridor artik YUKSEK guven uretmiyor; eski metrik
     ayni sahnede 1,000 veriyordu.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

KOK = Path(__file__).resolve().parents[1]
if str(KOK / "codes") not in sys.path:
    sys.path.insert(0, str(KOK / "codes"))

from karar_sozlesmesi import (ROTA_DARBOGAZ_TAM_ORANI, MASKE_YOK_SEBEBI,
                              rota_darbogaz_guveni, serit_no)
from rpi_inference import _rota_serit_olcumu, analyze_path

H, W = 600, 900          # serit sinirlari: x = 300 ve x = 600


# ── Yardimcilar ──────────────────────────────────────────────────────────────

def _eski_centroid_seridi(koridor):
    """T31 ONCESI uretim kodu — POZITIF KONTROL icin birebir korunur.

    `codes/rpi_inference.py` (T31 oncesi): koridorun ust %30 bandindaki
    piksellerin yatay centroid'i hangi ucte-bire duserse `open_path` odur.
    """
    ys, xs = np.nonzero(koridor)
    if xs.size == 0:
        return None
    ymin, ymax = int(ys.min()), int(ys.max())
    band = ys <= ymin + 0.30 * (ymax - ymin + 1)
    bx = xs[band] if band.any() else xs
    return serit_no(float(bx.mean()), 0, koridor.shape[1])


def _eski_guven(koridor):
    """T32 ONCESI uretim metrigi — `in_third / bx.size`."""
    ys, xs = np.nonzero(koridor)
    if xs.size == 0:
        return 0.0
    ymin, ymax = int(ys.min()), int(ys.max())
    band = ys <= ymin + 0.30 * (ymax - ymin + 1)
    bx = xs[band] if band.any() else xs
    op = serit_no(float(bx.mean()), 0, koridor.shape[1])
    lo = (op - 1) * koridor.shape[1] / 3.0
    hi = op * koridor.shape[1] / 3.0
    return round(int(((bx >= lo) & (bx < hi)).sum()) / max(1, bx.size), 3)


def _bariyer_ve_kapi(kapi_serit, kapi_px=64):
    """UC ayri dikey koridor + tam genislikte bariyer + TEK temiz kapi.

    Yer gercegi belli: alt->ust gecis yalniz `kapi_serit` icinden mumkun.

    ⚠ T48: eskiden `trav = np.ones(...)` idi, yani "tum kare surulebilir".
    Zemin kaplama kapisi bunu HAKLI OLARAK supheli sayiyor (kaplama %100 >
    tavan). Sahne arena semantigine yaklastirildi: uc koridor, aralari
    gecilemez. Kaplama %50 — tavanin altinda, test ettigi sey degismedi.
    """
    # KUM SAATI: ustte ve altta UC SERIDI DE kesen genis bantlar, aralarinda
    # serit basina birer dikey baglanti. Iki ozellik birden gerekli:
    #   · kaplama %51 (< T48 tavani) -> zemin kapisi atesle-MEZ;
    #   · ust bant uc seride yayildigi icin ESKI centroid tanimi hala orta
    #     seride dusuyor -> pozitif kontrol AYIRT EDICI kaliyor.
    trav = np.zeros((H, W), np.uint8)
    trav[0:80, :] = 1
    trav[H - 80:H, :] = 1
    for merkez in (W // 6, W // 2, 5 * W // 6):
        trav[80:H - 80, merkez - 50:merkez + 50] = 1
    engel = np.zeros((H, W), np.uint8)
    engel[290:310, :] = 1
    merkez = {1: W // 6, 2: W // 2, 3: 5 * W // 6}[kapi_serit]
    engel[290:310, merkez - kapi_px // 2:merkez + kapi_px // 2] = 0
    return trav, engel


def _zikzak(kapi_px=24):
    """Alt ve ust uc SERIT 3'te; tek gecis SERIT 1'deki dar kapidan.

    Bu sahnede darbogaz seridi (1) ile baskin serit (3) AYRISIR — iki aday
    tanimi ancak boyle bir sahne ayirt eder.
    """
    m = np.zeros((H, W), np.uint8)
    m[340:H, 700:780] = 1                                    # alt dikey (serit 3)
    m[300:348, 110:780] = 1                                  # alt yatay
    m[252:308, 130 - kapi_px // 2:130 + kapi_px // 2] = 1     # KAPI (serit 1)
    m[212:260, 110:780] = 1                                  # ust yatay
    m[0:220, 700:780] = 1                                    # ust dikey (serit 3)
    return m


def _serit_maskesi(serit, genislik=220):
    """Tek seride oturan tam yukseklik koridor."""
    m = np.zeros((H, W), np.uint8)
    merkez = {1: W // 6, 2: W // 2, 3: 5 * W // 6}[serit]
    m[:, merkez - genislik // 2:merkez + genislik // 2] = 1
    return m


# ── T31 ──────────────────────────────────────────────────────────────────────

class T31SeritEtiketiTests(unittest.TestCase):
    """`road` bilinen kapi seridini adlandiriyor mu?"""

    def test_kapi_seridi_yayinlanan_road_ile_ayni(self):
        """KAPI: enjekte-kapi deneyi — kapi nereye acilirsa `road` odur."""
        for kapi_serit in (1, 2, 3):
            with self.subTest(kapi_serit=kapi_serit):
                trav, engel = _bariyer_ve_kapi(kapi_serit)
                yol, guven, wps, ret = analyze_path(
                    trav, n_waypoints=8, return_reason=True,
                    min_area_ratio=0.001, engel_mask=engel)
                self.assertIsNotNone(
                    yol, f"kapi serit {kapi_serit} acikken karar verilmedi: {ret}")
                self.assertEqual(
                    yol, kapi_serit,
                    f"kapi serit {kapi_serit}'de ama yayinlanan road={yol}")

    def test_pozitif_kontrol_eski_centroid_yanlis_serit_uretiyor(self):
        """POZITIF KONTROL: duzeltme etkisizlestirilirse kusur GERI GELIR.

        Eski centroid tanimi ayni sahnelerde kapi seridini bulamaz. Bu test
        gecmezse yukaridaki kapi testi bir sey kanitlamiyor demektir.
        """
        yanlis = 0
        for kapi_serit in (1, 2, 3):
            trav, engel = _bariyer_ve_kapi(kapi_serit)
            yol, guven, wps, koridor, ret = analyze_path(
                trav, n_waypoints=8, return_clean=True, return_reason=True,
                min_area_ratio=0.001, engel_mask=engel)
            self.assertIsNotNone(yol)
            if _eski_centroid_seridi(koridor) != kapi_serit:
                yanlis += 1
        self.assertGreaterEqual(
            yanlis, 2,
            "Eski centroid tanimi bu sahnelerde yanlis serit URETMIYOR; "
            "kapi testi kusuru ayirt edemiyor (D-15 vakum kapi riski).")

    def test_road_rotanin_gectigi_seritle_uyusuyor(self):
        """Yayinlanan etiket, waypoint zincirinin uzerinde bulundugu serit."""
        for kapi_serit in (1, 2, 3):
            with self.subTest(kapi_serit=kapi_serit):
                trav, engel = _bariyer_ve_kapi(kapi_serit)
                yol, guven, wps, koridor, ret, olc = analyze_path(
                    trav, n_waypoints=8, return_clean=True, return_reason=True,
                    return_olcum=True, min_area_ratio=0.001, engel_mask=engel)
                self.assertIsNotNone(yol)
                # Bariyer satirindaki waypoint kapinin icinde olmali.
                bariyer_wp = min(wps, key=lambda p: abs(p[1] - 300))
                self.assertEqual(
                    serit_no(bariyer_wp[0], 0, W), yol,
                    f"road={yol} ama rota bariyeri serit "
                    f"{serit_no(bariyer_wp[0], 0, W)}'den geciyor")

    def test_ayirt_edici_sahne_darbogaz_kazanir_baskin_kaybeder(self):
        """AYIRT EDICI: rota serit degistiginde hangi tanim dogru?

        Zikzak sahnede alt/ust uc serit 3'te, tek gecis serit 1'deki kapidan.
        Dogru cevap 1'dir; baskin-serit tanimi 3 der ve YANILIR.
        """
        olcumler = []
        for kapi_px in (16, 24, 48, 64):
            m = _zikzak(kapi_px)
            yol, guven, wps, koridor, ret, olc = analyze_path(
                m, n_waypoints=8, return_clean=True, return_reason=True,
                return_olcum=True, min_area_ratio=0.001)
            if yol is None or olc is None:
                continue
            olcumler.append((kapi_px, olc))
        self.assertTrue(olcumler, "zikzak sahnede hic karar uretilmedi")
        ayrisan = [o for _, o in olcumler
                   if o["darbogaz_serit"] != o["baskin_serit"]]
        self.assertTrue(
            ayrisan,
            "Iki aday tanim bu sahnede AYRISMIYOR; sahne ayirt edici degil.")
        for _, olc in olcumler:
            self.assertTrue(
                olc["cok_seritli"],
                "Zikzak rota tek seritte gorunuyor; sahne bozulmus.")
        # Baskin tanimi bu sahnede sistematik olarak YANILIR.
        self.assertTrue(
            all(o["baskin_serit"] == 3 for _, o in olcumler),
            "baskin_serit beklenen sekilde 3 demiyor; sahne degismis")

    def test_ornekleme_karari_degistirmez(self):
        """CONTRACTS SS6.4/5: `n_waypoints` `road`'u degistiremez."""
        for kapi_serit in (1, 3):
            trav, engel = _bariyer_ve_kapi(kapi_serit)
            kararlar = set()
            for n in (8, 16, 24, 32):
                yol, guven, wps = analyze_path(
                    trav, n_waypoints=n, min_area_ratio=0.001,
                    engel_mask=engel)
                kararlar.add((yol, guven))
            self.assertEqual(
                len(kararlar), 1,
                f"kapi serit {kapi_serit}: ornekleme karari degistirdi "
                f"-> {kararlar}")

    def test_cok_seritli_rota_kayda_geciyor(self):
        """Tek etiketin yetersiz kaldigi durum SESSIZ gecmemeli."""
        m = _zikzak(48)
        yol, guven, wps, koridor, ret, olc = analyze_path(
            m, n_waypoints=8, return_clean=True, return_reason=True,
            return_olcum=True, min_area_ratio=0.001)
        self.assertIsNotNone(olc)
        self.assertTrue(olc["cok_seritli"])
        self.assertEqual(sum(olc["seritler"]), olc["rota_px"])
        self.assertEqual(len([s for s in olc["seritler"] if s > 0]), 3)

    def test_tek_seritli_rota_cok_seritli_isaretlenmez(self):
        """Yanlis pozitif olmasin: duz koridor tek serittir."""
        for serit in (1, 2, 3):
            with self.subTest(serit=serit):
                yol, guven, wps, koridor, ret, olc = analyze_path(
                    _serit_maskesi(serit), n_waypoints=8, return_clean=True,
                    return_reason=True, return_olcum=True,
                    min_area_ratio=0.001)
                self.assertEqual(yol, serit)
                self.assertFalse(olc["cok_seritli"])


# ── T32 ──────────────────────────────────────────────────────────────────────

class T32GuvenMetrigiTests(unittest.TestCase):
    """Guven rotanin darbogazindan mi geliyor?"""

    def test_ince_koridor_yuksek_guven_URETMEZ(self):
        """KAPI: kil gibi koridor. Eski metrik 1,000 veriyordu."""
        for genislik in (4, 8, 16, 32):
            with self.subTest(genislik=genislik):
                m = np.zeros((H, W), np.uint8)
                m[:, 100:100 + genislik] = 1
                eski = _eski_guven(m)
                yol, guven, wps = analyze_path(
                    m, n_waypoints=8, min_area_ratio=0.001)
                self.assertGreaterEqual(
                    eski, 0.99,
                    "POZITIF KONTROL: eski metrik bu sahnede 1,0 vermiyor; "
                    "kusur yeniden uretilemedi")
                yeni = guven if yol is not None else 0.0
                self.assertLess(
                    yeni, 0.75,
                    f"{genislik}px kil koridor {yeni} guven uretti "
                    "(eski kusur geri gelmis olabilir)")

    def test_saglikli_koridor_yuksek_guven_uretir(self):
        """Regresyon: dar olani cezalandirirken genisi de susturmuyoruz."""
        yol, guven, wps = analyze_path(
            _serit_maskesi(1, genislik=220), n_waypoints=8,
            min_area_ratio=0.001)
        self.assertEqual(yol, 1)
        self.assertGreaterEqual(guven, 0.99)

    def test_guven_kapi_genisligiyle_MONOTON_artar(self):
        """Eski metrigin yapamadigi sey: sahneyle birlikte degismek."""
        degerler = []
        for kapi_px in (16, 24, 32, 48, 64, 96):
            trav, engel = _bariyer_ve_kapi(1, kapi_px=kapi_px)
            yol, guven, wps = analyze_path(
                trav, n_waypoints=8, min_area_ratio=0.001, engel_mask=engel)
            if yol is not None:
                degerler.append((kapi_px, guven))
        self.assertGreaterEqual(len(degerler), 4)
        for (kx0, g0), (kx1, g1) in zip(degerler, degerler[1:]):
            self.assertLessEqual(
                g0, g1 + 1e-9,
                f"guven kapi {kx0}->{kx1} px genislerken dustu: {g0} -> {g1}")
        self.assertLess(
            degerler[0][1], degerler[-1][1],
            "guven kapi genisligine hic tepki vermiyor (eski kusur)")

    def test_kapi_konumu_degisince_guven_ESKIDE_sabitti(self):
        """POZITIF KONTROL: eski metrik kapi gezerken kipirdamiyordu."""
        eskiler, yeniler = [], []
        for kapi_serit in (1, 2, 3):
            trav, engel = _bariyer_ve_kapi(kapi_serit, kapi_px=48)
            yol, guven, wps, koridor, ret = analyze_path(
                trav, n_waypoints=8, return_clean=True, return_reason=True,
                min_area_ratio=0.001, engel_mask=engel)
            if yol is None:
                continue
            eskiler.append(_eski_guven(koridor))
            yeniler.append(guven)
        self.assertEqual(len(eskiler), 3)
        self.assertLess(
            max(eskiler) - min(eskiler), 1e-9,
            "POZITIF KONTROL: eski metrik kapi konumuyla degisiyor; "
            "D-41'deki kusur bu sahnede yeniden uretilemedi")

    def test_maske_yoksa_guven_sifir(self):
        """T32 kapisi: sinif-0 tespiti YOKKEN yuksek deger uretilemez."""
        yol, guven, wps, ret = analyze_path(
            np.zeros((H, W), np.uint8), n_waypoints=8, return_reason=True)
        self.assertIsNone(yol)
        self.assertEqual(guven, 0.0)
        self.assertEqual(ret[0], MASKE_YOK_SEBEBI)

    def test_her_ret_yolu_guveni_sifirlar(self):
        """Ret varsa guven 0,0 olmali — kismi kanit yayinlanamaz."""
        sahneler = {
            "bos": np.zeros((H, W), np.uint8),
            "ust_bant_yok": np.pad(np.ones((H // 2, W), np.uint8),
                                   ((H - H // 2, 0), (0, 0))),
            "kil": (lambda: (lambda m: m)(
                np.pad(np.ones((H, 3), np.uint8),
                       ((0, 0), (100, W - 103)))))(),
        }
        for ad, m in sahneler.items():
            with self.subTest(sahne=ad):
                yol, guven, wps, ret = analyze_path(
                    m, n_waypoints=8, return_reason=True, min_area_ratio=0.001)
                if yol is None:
                    self.assertEqual(guven, 0.0, f"{ad}: ret ama guven {guven}")
                    self.assertEqual(wps, [])
                    self.assertIsNotNone(ret)


# ── Sozlesme sabitleri ───────────────────────────────────────────────────────

class SozlesmeSabitleriTests(unittest.TestCase):
    """Madde 16 / D-38 SS5: test esigi SABITTEN turetir, ciplak yazmaz."""

    def test_guven_normalizeri_sozlesmeden_turetiliyor(self):
        icerik_w = 1000.0
        tam_aciklik = icerik_w * ROTA_DARBOGAZ_TAM_ORANI
        self.assertEqual(rota_darbogaz_guveni(tam_aciklik, icerik_w), 1.0)
        self.assertEqual(
            rota_darbogaz_guveni(tam_aciklik / 2.0, icerik_w), 0.5)
        self.assertEqual(
            rota_darbogaz_guveni(tam_aciklik * 4.0, icerik_w), 1.0,
            "guven [0,1] disina cikti")

    def test_gecersiz_aciklik_fail_closed(self):
        for kotu in (None, True, False, float("nan"), float("inf"), -3.0, 0.0):
            with self.subTest(deger=kotu):
                self.assertEqual(rota_darbogaz_guveni(kotu, 1000.0), 0.0)

    def test_gecersiz_icerik_genisligi_fail_closed(self):
        for kotu in (0, -10, float("nan")):
            with self.subTest(deger=kotu):
                self.assertEqual(rota_darbogaz_guveni(10.0, kotu), 0.0)

    def test_serit_no_icerik_kutusundan_okur(self):
        """Sinirlar kare tuvalden degil letterbox icerik kutusundan."""
        self.assertEqual(serit_no(50, 0, 900), 1)
        self.assertEqual(serit_no(450, 0, 900), 2)
        self.assertEqual(serit_no(850, 0, 900), 3)
        # icerik saga kaydirilmis letterbox: ayni piksel farkli serit
        self.assertEqual(serit_no(450, 400, 300), 1)
        self.assertEqual(serit_no(50, 0, 0), 2, "gecersiz genislikte orta")

    def test_olcum_cozunurlukten_bagimsiz(self):
        """CONTRACTS SS8: olcut oran, mutlak piksel degil."""
        kararlar = []
        for olcek in (1, 2):
            trav = np.ones((H * olcek, W * olcek), np.uint8)
            engel = np.zeros_like(trav)
            engel[290 * olcek:310 * olcek, :] = 1
            kx = (W * olcek) // 6
            genis = 48 * olcek
            engel[290 * olcek:310 * olcek,
                  kx - genis // 2:kx + genis // 2] = 0
            yol, guven, wps = analyze_path(
                trav, n_waypoints=8, min_area_ratio=0.001, engel_mask=engel)
            kararlar.append((yol, round(guven, 2)))
        self.assertEqual(
            kararlar[0], kararlar[1],
            f"cozunurluk iki katina cikinca karar degisti: {kararlar}")


class RotaOlcumBirimTests(unittest.TestCase):
    """`_rota_serit_olcumu` dogrudan — dogru pikselleri mi sayiyor?"""

    def test_olcum_line8_piksellerinden_sayiyor(self):
        dist = np.full((H, W), 5.0, np.float32)
        rota = [(100, 599), (100, 0)]          # duz dikey, serit 1
        olc = _rota_serit_olcumu(rota, dist, (0, 0, W, H))
        self.assertEqual(olc["darbogaz_serit"], 1)
        self.assertEqual(olc["baskin_serit"], 1)
        self.assertEqual(olc["seritler"], (600, 0, 0))
        self.assertEqual(olc["rota_px"], 600)
        self.assertFalse(olc["cok_seritli"])

    def test_darbogaz_en_kucuk_acikligi_secer(self):
        dist = np.full((H, W), 9.0, np.float32)
        dist[300, 700] = 1.0                   # tek dar nokta, serit 3
        rota = [(100, 300), (800, 300)]        # yatay, uc seridi de keser
        olc = _rota_serit_olcumu(rota, dist, (0, 0, W, H))
        self.assertEqual(olc["darbogaz_px"], 1.0)
        self.assertEqual(olc["darbogaz_serit"], 3)
        self.assertEqual(olc["darbogaz_xy"], (700, 300))
        self.assertTrue(olc["cok_seritli"])

    def test_bos_rota_none_doner(self):
        self.assertIsNone(
            _rota_serit_olcumu([], np.ones((H, W), np.float32), (0, 0, W, H)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
