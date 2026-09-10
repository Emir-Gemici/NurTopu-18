"""T235-B/D kilitleri — alan-olcekli yol etiketi (A0), KBH izdusumu (A1), hiz kapisi,
tezgah negatif kontrolu (K3n) ve tezgah ciktisinin tohumla bayt-es yeniden uretimi.

On kayit: results/fdr_sprint_20260910/H1/t235/ON_KAYIT.md SS1, SS2, SS5, SS6.
Tezgah: simulation/mujoco/t235_etiket_tezgahi.py -> H1/t235/olcum/ (benzetim, saha olcumu degil).

Mutasyon hedefleri (gercek dosyada; hepsi yakalanmali): W/6 -> W/3 · x aynasi · kerteriz (beta)
isareti · montaj yaw isareti · hiz kapisinin kaldirilmasi.
"""

import json
import math
import sys
import unittest
from pathlib import Path

import numpy as np

KOK = Path(__file__).resolve().parents[1]
for _p in (KOK / "codes", KOK / "simulation" / "mujoco", KOK / "simulation" / "scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import karar_sozlesmesi as ks  # noqa: E402

ON_KAYIT = KOK / "results" / "fdr_sprint_20260910" / "H1" / "t235" / "ON_KAYIT.md"


def _kbh(px, py, **kw):
    ortak = dict(merkez_px=(256.0, 256.0), mpp=0.1, iha_dogu_m=0.0, iha_kuzey_m=0.0,
                 hdg_derece=0.0, montaj_yaw_derece=0.0, kerteriz_derece=0.0)
    ortak.update(kw)
    return ks.kbh_donustur(px, py, **ortak)


class Sabitler(unittest.TestCase):

    def test_alan_genislikleri_sartname_ve_tek_kaynakla_es(self):
        self.assertEqual(20.0, ks.FDA_ALAN_GENISLIK_M)
        self.assertEqual(50.0, ks.HTAB_ALAN_GENISLIK_M)
        self.assertEqual(ks.SENARYO_BOYUTLARI_M["FDA"], ks.FDA_ALAN_GENISLIK_M)
        self.assertEqual(ks.SENARYO_BOYUTLARI_M["HTAB"], ks.HTAB_ALAN_GENISLIK_M)
        import arena
        self.assertEqual(arena.HTAB, ks.HTAB_ALAN_GENISLIK_M)

    def test_hiz_ve_tazelik_esikleri_ON_KAYIT_SS5(self):
        self.assertEqual(1.0, ks.ALAN_ETIKETI_HIZ_ESIGI_M_S)
        self.assertEqual(0.5, ks.ALAN_ETIKETI_TAZELIK_S)
        metin = ON_KAYIT.read_text(encoding="utf-8")
        self.assertIn("≤ 1,0 m/s", metin)
        self.assertIn("tazelik ≤ 0,5 s", metin)

    def test_orta_serit_yari_genisligi_W_bolu_6(self):
        self.assertAlmostEqual(20.0 / 6.0, ks.alan_serit_yari_genisligi_m(20.0), places=12)
        self.assertAlmostEqual(50.0 / 6.0, ks.alan_serit_yari_genisligi_m(50.0), places=12)
        for kotu in (None, 0.0, -20.0, float("nan"), float("inf"), True, "20"):
            self.assertIsNone(ks.alan_serit_yari_genisligi_m(kotu), kotu)


class A0AlanSeritKarari(unittest.TestCase):
    # mpp 0,05 m/px, W = 20 m -> b = (20/6)/0,05 = 66,667 px; merkez 256 -> sinirlar 189,33 / 322,67
    X0, W, MPP = 0, 512, 0.05

    def _k(self, xs, **kw):
        pix = [(x, 100) for x in xs]
        return ks.alan_serit_karari(pix, kw.get("x0", self.X0), kw.get("w", self.W),
                                    kw.get("mpp", self.MPP), kw.get("alan", ks.FDA_ALAN_GENISLIK_M))

    def test_W6_sinirlari_merkezden(self):
        self.assertEqual(1, self._k([189])[0])
        self.assertEqual(2, self._k([190])[0])
        self.assertEqual(2, self._k([322])[0])
        self.assertEqual(3, self._k([323])[0])
        _k, _s, pay = self._k([256])
        self.assertAlmostEqual(256.0 - 200.0 / 3.0, pay["sol_sinir_px"], places=9)
        self.assertAlmostEqual(256.0 + 200.0 / 3.0, pay["sag_sinir_px"], places=9)

    def test_sinirlar_icerik_kutusunun_merkezini_izler(self):
        # icerik 100..1124 (w 1024): merkez 612 -> sinirlar 545,33 / 678,67
        self.assertEqual(1, self._k([545], x0=100, w=1024)[0])
        self.assertEqual(2, self._k([546], x0=100, w=1024)[0])
        self.assertEqual(2, self._k([678], x0=100, w=1024)[0])
        self.assertEqual(3, self._k([679], x0=100, w=1024)[0])

    def test_kare_genisligine_bagli_DEGIL_KARE_ise_bagli(self):
        """Merkezden 4 m sagdaki rota: A0 her genislikte 3; KARE 512'de 2, 256'da 3."""
        for w in (256, 512, 1024):
            x = w / 2.0 + 4.0 / self.MPP
            self.assertEqual(3, self._k([x], w=w)[0], w)
        self.assertEqual(2, ks.rota_serit_karari([(256 + 80, 0)], 0, 512)[0])

    def test_x_aynasi_simetri(self):
        rng = np.random.default_rng(7)
        for _ in range(200):
            xs = rng.integers(0, 512, rng.integers(1, 40)).astype(float) + 0.25
            k, s, _p = self._k(xs.tolist())
            ka, sa, _pa = self._k((512.0 - xs).tolist())   # merkez 256'ya gore ayna
            self.assertEqual(tuple(reversed(s)), sa)
            # Etiket aynasi yalniz TEKIL cogunlukta beklenir: beraberlik kurali (kucuk serit,
            # rota_serit_karari ile ayni) tanim geregi ayna-simetrik DEGILDIR.
            if sorted(s)[-1] != sorted(s)[-2]:
                self.assertEqual({1: 3, 2: 2, 3: 1}[k], ka)

    def test_cogunluk_ve_beraberlik_kucuk_serit(self):
        k, s, _p = self._k([100, 110, 250, 260, 400])
        self.assertEqual((2, 2, 1), s)
        self.assertEqual(1, k)
        self.assertEqual(2, self._k([100, 250, 260])[0])

    def test_pay_bilgisi(self):
        self.assertAlmostEqual(20.0 / 6.0, self._k([256])[2]["pay_m"], places=9)
        self.assertAlmostEqual(1.0, self._k([256 + 200.0 / 3.0 + 20.0])[2]["pay_m"], places=9)
        self.assertAlmostEqual(0.5, self._k([256 - 200.0 / 3.0 - 10.0])[2]["pay_m"], places=9)
        # medyan kazanan seridin DISINDA -> negatif pay
        k, _s, pay = self._k([100, 110, 120, 250, 260, 400, 410])
        self.assertEqual(1, k)
        self.assertLess(pay["pay_m"], 0.0)

    def test_liste_ve_numpy_ayni(self):
        pix = [(190, 3), (400, 5), (401, 9), (20, 2)]
        a = ks.alan_serit_karari(pix, 0, 512, 0.05)
        b = ks.alan_serit_karari(np.array(pix), 0, 512, 0.05)
        self.assertEqual(a[:2], b[:2])
        self.assertEqual(a[2], b[2])

    def test_fail_closed(self):
        bos = (None, (0, 0, 0), None)
        self.assertEqual(bos, self._k([]))
        for mpp in (None, 0.0, -0.1, float("nan"), True):
            self.assertEqual(bos, self._k([256], mpp=mpp), mpp)
        self.assertEqual(bos, self._k([256], w=0))
        self.assertEqual(bos, self._k([256], alan=0.0))
        self.assertEqual(bos, ks.alan_serit_karari([(float("nan"), 1)], 0, 512, 0.05))


class A1KbhDonustur(unittest.TestCase):

    def test_kimlik_ve_x_aynasi(self):
        x, y = _kbh(266, 256)
        self.assertAlmostEqual(1.0, x, places=12)
        self.assertAlmostEqual(0.0, y, places=12)
        x, y = _kbh(256, 246)      # goruntu-yukari = ileri
        self.assertAlmostEqual(0.0, x, places=12)
        self.assertAlmostEqual(1.0, y, places=12)
        x, y = _kbh(246, 256, iha_dogu_m=2.0, iha_kuzey_m=3.0)
        self.assertAlmostEqual(1.0, x, places=12)
        self.assertAlmostEqual(3.0, y, places=12)

    def test_kerteriz_isareti(self):
        # Baslangic -> Hedef = DOGU (beta 90): gozlemcinin sagi GUNEY.
        x, y = _kbh(256, 256, iha_dogu_m=0.0, iha_kuzey_m=-2.0, kerteriz_derece=90.0)
        self.assertAlmostEqual(2.0, x, places=12)
        self.assertAlmostEqual(0.0, y, places=12)
        x, y = _kbh(256, 246, hdg_derece=90.0, kerteriz_derece=90.0)   # ileri piksel = dogu = +y
        self.assertAlmostEqual(0.0, x, places=12)
        self.assertAlmostEqual(1.0, y, places=12)
        # genel: goruntu-yukari = beta ise piksel ekseni KBH ekseniyle cakisir
        for beta in (37.0, 123.0, 250.0, -65.0):
            x, y = _kbh(256 + 50, 256 - 20, hdg_derece=beta - 90.0, montaj_yaw_derece=90.0,
                        kerteriz_derece=beta)
            self.assertAlmostEqual(5.0, x, places=9, msg=beta)
            self.assertAlmostEqual(2.0, y, places=9, msg=beta)

    def test_montaj_yaw_isareti(self):
        # hdg 30 + montaj 60 = goruntu-yukari DOGU; beta 0 -> ileri piksel KBH +x
        x, y = _kbh(256, 246, hdg_derece=30.0, montaj_yaw_derece=60.0)
        self.assertAlmostEqual(1.0, x, places=12)
        self.assertAlmostEqual(0.0, y, places=12)
        x, y = _kbh(256, 246, hdg_derece=0.0, montaj_yaw_derece=90.0)
        self.assertAlmostEqual(1.0, x, places=12)
        self.assertAlmostEqual(0.0, y, places=12)

    def test_sim_izdusumuyle_es(self):
        """Bagimsiz kod: sim_karar_toplayici.piksel_dunya (kerteriz K1 kurali: hdg = 90 - yaw,
        montaj = teta - 90, beta 0, orijin HTAB merkezi)."""
        import sim_karar_toplayici as skt
        rng = np.random.default_rng(20260910)
        for _ in range(300):
            x, y, yaw, teta = rng.uniform(-20, 20), rng.uniform(-20, 20), rng.uniform(-180, 180), rng.choice([0, 90, 180, 270])
            mpp = rng.uniform(0.02, 0.1)
            px, py = rng.uniform(0, 1280), rng.uniform(0, 1280)
            ref = skt.piksel_dunya(px, py, (0, 0.0, x, y, 30.0, math.radians(yaw)), 1280, 1280, mpp,
                                   math.radians(teta))
            kx, ky = ks.kbh_donustur(px, py, merkez_px=(640.0, 640.0), mpp=mpp, iha_dogu_m=x,
                                     iha_kuzey_m=y, hdg_derece=90.0 - yaw,
                                     montaj_yaw_derece=teta - 90.0, kerteriz_derece=0.0)
            self.assertAlmostEqual(ref[0], kx, places=9)
            self.assertAlmostEqual(ref[1], ky, places=9)

    def test_uzaklik_korunur_ve_dizi_skaler_ayni(self):
        kw = dict(iha_dogu_m=4.0, iha_kuzey_m=-7.0, hdg_derece=211.0, montaj_yaw_derece=-33.0,
                  kerteriz_derece=77.0)
        xs = np.array([10.0, 300.0, 511.0])
        ys = np.array([40.0, 256.0, 499.0])
        dx, dy = _kbh(xs, ys, **kw)
        for i in range(3):
            sx, sy = _kbh(float(xs[i]), float(ys[i]), **kw)
            self.assertAlmostEqual(sx, dx[i], places=12)
            self.assertAlmostEqual(sy, dy[i], places=12)
        self.assertAlmostEqual(math.hypot(dx[0] - dx[1], dy[0] - dy[1]),
                               0.1 * math.hypot(xs[0] - xs[1], ys[0] - ys[1]), places=9)

    def test_fail_closed(self):
        self.assertIsNone(_kbh(1, 1, mpp=0.0))
        self.assertIsNone(_kbh(1, 1, mpp=None))
        self.assertIsNone(_kbh(1, 1, hdg_derece=float("nan")))
        self.assertIsNone(_kbh(1, 1, kerteriz_derece=None))
        self.assertIsNone(_kbh(1, 1, iha_dogu_m=True))
        self.assertIsNone(_kbh(1, 1, merkez_px=None))
        self.assertIsNone(_kbh(1, 1, merkez_px=(1.0,)))


class A1KbhSeritKarari(unittest.TestCase):
    # mpp 1/30 m/px, W 20 m -> W/6 = 3,333 m = 100 px
    KW = dict(merkez_px=(256.0, 256.0), mpp=1.0 / 30.0, iha_dogu_m=0.0, iha_kuzey_m=0.0,
              hdg_derece=0.0, montaj_yaw_derece=0.0, kerteriz_derece=0.0)

    def _k(self, xs, **kw):
        a = dict(self.KW)
        a.update(kw)
        return ks.kbh_serit_karari([(x, 256) for x in xs], **a)

    def test_W6_sinirlari_ortasi_kapali(self):
        self.assertEqual(1, self._k([256 - 101])[0])
        self.assertEqual(2, self._k([256 - 100])[0])
        self.assertEqual(2, self._k([256 + 100])[0])
        self.assertEqual(3, self._k([256 + 101])[0])

    def test_alan_genisligi_olcekler(self):
        self.assertEqual(3, self._k([256 + 101])[0])
        self.assertEqual(2, self._k([256 + 101], alan_genislik_m=ks.HTAB_ALAN_GENISLIK_M)[0])
        self.assertEqual(3, self._k([256 + 251], alan_genislik_m=ks.HTAB_ALAN_GENISLIK_M)[0])

    def test_iha_konumu_etiketi_kaydirir(self):
        # IHA alan merkezinin 4 m SOLUNDA (beta 0 -> bati), rota goruntu merkezinde -> sol serit
        self.assertEqual(1, self._k([256], iha_dogu_m=-4.0)[0])
        self.assertEqual(3, self._k([256], iha_dogu_m=4.0)[0])

    def test_cogunluk_beraberlik(self):
        k, s = self._k([100, 110, 256, 257])
        self.assertEqual((2, 2, 0), s)
        self.assertEqual(1, k)

    def test_fail_closed(self):
        self.assertEqual((None, (0, 0, 0)), self._k([]))
        self.assertEqual((None, (0, 0, 0)), self._k([256], mpp=float("nan")))
        self.assertEqual((None, (0, 0, 0)), self._k([256], alan_genislik_m=-1.0))


class HizKapisi(unittest.TestCase):

    def test_sinirlar(self):
        f = ks.alan_etiketi_kullanilabilir_mi
        self.assertTrue(f(1.0, 0.5))
        self.assertTrue(f(0.0, 0.0))
        self.assertTrue(f(0.3, 0.2))
        self.assertFalse(f(math.nextafter(1.0, 2.0), 0.5))
        self.assertFalse(f(1.0, math.nextafter(0.5, 1.0)))
        self.assertFalse(f(3.0, 0.1), "kose bacagi hizi (3 m/s) alan etiketine GIREMEZ")
        self.assertFalse(f(0.5, 0.8), "bayat hiz ornegi")

    def test_fail_closed(self):
        f = ks.alan_etiketi_kullanilabilir_mi
        for v, t in ((None, 0.1), (0.1, None), (float("nan"), 0.1), (0.1, float("nan")),
                     (float("inf"), 0.1), (True, 0.1), (0.1, False), (-0.1, 0.1), (0.1, -0.01),
                     ("0.1", 0.1)):
            self.assertFalse(f(v, t), (v, t))


class TezgahNegatifKontrol(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import t235_etiket_tezgahi as t
        cls.t = t

    def test_K3n_KARE_s5_merkezli_hatasiz_222(self):
        k3n = self.t.k3n_kos()
        self.assertTrue(k3n["gecti"])
        for s in k3n["yapilandirmalar"]:
            self.assertEqual([2, 2, 2], s["KARE"], s)
            self.assertEqual([1, 2, 3], s["A0"], s)
            self.assertEqual([1, 2, 3], s["A1"], s)

    def test_tezgah_sabit_uretec_degil(self):
        """KARE s = 8 m'de (32 m, orta ucte-bir |x| < 5,59 m) [1,2,3] vermeli: tezgah ayirt eder."""
        t = self.t
        out = [t.sahne_etiketleri(8.0, "4:3", 32.0, yol, (0, 0), 0.0, (0, 0), [(0, 0)])["KARE"]
               for yol in (1, 2, 3)]
        self.assertEqual([1, 2, 3], out)

    def test_on_kayit_parametreleri_tezgahta_aynen(self):
        t = self.t
        metin = ON_KAYIT.read_text(encoding="utf-8")
        for parca in ("tohum 20260910", "hücre başına 2000", "≥ %99,0", "0,5 puandan",
                      "pay < 1,0 m", "s ∈ {5; 6,67; 8} m", "σ_c ∈ {0,5; 1,0} m", "σ_ψ ∈ {2°; 5°}",
                      "σ_g ∈ {1,0; 2,0} m", "[2°, 3°]", "HFOV 55,3°", "[2, 2, 2]"):
            self.assertIn(parca, metin, parca)
        self.assertEqual(20260910, t.TOHUM)
        self.assertEqual(2000, t.CEKILIS_N)
        self.assertEqual((5.0, 6.67, 8.0), t.S_DEGERLERI_M)
        self.assertEqual((0.5, 1.0), t.SIGMA_C_M)
        self.assertEqual((2.0, 5.0), t.SIGMA_PSI_DERECE)
        self.assertEqual((1.0, 2.0), t.SIGMA_G_M)
        self.assertEqual((2.0, 3.0), t.EGIM_ARALIGI_DERECE)
        self.assertEqual(99.0, t.KAPI_ORAN_YUZDE)
        self.assertEqual(0.5, t.KAPI_KARE_FARK_PUAN)
        self.assertEqual(1.0, t.ALAN_SIGMA_ASGARI_PAY_M)
        self.assertEqual(((("4:3", 32.0), ("16:9", 40.0), ("16:9", 32.0))), t.KIP_H)
        self.assertEqual((("4:3", 32.0), ("16:9", 40.0)), t.NOMINAL_KIP_H)
        self.assertEqual((1.0, 5.0, 2.0), (t.NOMINAL_SIGMA_C_M, t.NOMINAL_SIGMA_PSI_DERECE, t.NOMINAL_SIGMA_G_M))
        self.assertAlmostEqual(55.3, t.HFOV_DERECE, places=1)


class TezgahYenidenUretim(unittest.TestCase):
    """Tezgah ciktisi tohumla BAYT-ES yeniden uretilir ve kayitli tabloyla es."""

    HUCRE = (6.67, "4:3", 32.0, 1.0, 5.0)          # nominal hucre

    @classmethod
    def setUpClass(cls):
        import t235_etiket_tezgahi as t
        cls.t = t
        cls.kayit = json.loads((t.CIKTI_DIZIN / t.K3_JSON).read_text(encoding="utf-8"))
        cls.a = t.tezgah_kos([cls.HUCRE])
        cls.b = t.tezgah_kos([cls.HUCRE])

    def test_ayni_tohum_bayt_es(self):
        self.assertEqual(self.t.json_metni(self.a).encode("utf-8"), self.t.json_metni(self.b).encode("utf-8"))

    def test_kayitli_tabloyla_es(self):
        anahtar = self.t.hucre_anahtari(*self.HUCRE)
        kayitli = [h for h in self.kayit["hucreler"] if h["hucre"] == anahtar]
        self.assertEqual(1, len(kayitli))
        self.assertEqual(kayitli[0], self.a["hucreler"][0])
        self.assertEqual(self.kayit["k3n"], self.a["k3n"])
        self.assertEqual(self.kayit["alan_sigma"], self.a["alan_sigma"])

    def test_kayitli_hukum_on_kayit_kuralindan(self):
        """Hukum tablodan on kayitli kuralla yeniden kurulur; elle yazilmis bir hukum yoktur."""
        t = self.t
        self.assertEqual(len(t.izgara()), len(self.kayit["hucreler"]))
        kapi = t.kapi_degerlendir(self.kayit["hucreler"])
        self.assertEqual(self.kayit["kapi"], json.loads(json.dumps(kapi)))
        self.assertEqual(self.kayit["hukum"],
                         json.loads(json.dumps(t.hukum_kur(self.kayit["k3n"], kapi, self.kayit["alan_sigma"]))))
        for h in self.kayit["hucreler"]:
            self.assertEqual(t.ETIKET, h["etiket"])
            self.assertEqual(6000, h["sahne_n"])

    def test_K1_kayitli(self):
        k1 = json.loads((self.t.CIKTI_DIZIN / self.t.K1_JSON).read_text(encoding="utf-8"))
        self.assertEqual([28, 28], k1["A1_dunya"])
        self.assertTrue(k1["KARE_negatif_kontrol_uretildi"])
        self.assertEqual({"kerteriz": [3, 8], "kosum_tur3_uretim": [6, 20]},
                         {k: [o["KARE=dunya"], o["n"]] for k, o in k1["ozet"].items()})
        self.assertTrue(k1["gecti"])


if __name__ == "__main__":
    unittest.main()
