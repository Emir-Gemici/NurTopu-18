"""T90 KAPISI: koridor etiketi TEK KAYNAKTAN (`serit_no`) gelir.

NEDEN (REVIEW_LOG D-145). `koridor_adaylari()` kendi serit numarasini
uretiyordu: `n_kapi == 3` iken soldan saga SIRA NUMARASI (i+1), aksi halde
kapiyi SERBEST ALAN BBOX'ina gore uce bolerek. Oysa
`karar_sozlesmesi.serit_no()` docstring'i "Tek kaynak: hem karar hem
gorsellestirme burayi cagirir" der ve sinirlari LETTERBOX ICERIK KUTUSUNDAN
alir (CONTRACTS SS8).

Olculdu (v30, sentetik_arena_kadraj_t66, n=260): 470 aday kapinin 104'u (%22,1)
iki semada FARKLI numara aliyordu. Etiket bosuna degil: `rota_bul`un `yol_no`su
`simulation/scripts/iha_haritala.py:329` -> `comms/protocol.py:51` ->
`comms/ika_receiver.py:11` yoluyla `plan_path(route["road"])`e girer ve
`simulation/scripts/hakem_log.py:108` bununla puanlar. IKA WAYPOINT ile degil
SERIT NUMARASI ile plan yapar.

BU TESTLER IKI ESKI SEMAYI DA GERI GELMEYE KARSI KILITLER; her sahne, eski
semanin BASKA bir cevap verdigi bir sahnedir (yorumlarda eski cevap yazilidir),
yoksa test bosa gecerdi.
"""

import unittest

import numpy as np

from codes.costmap_path_finder import koridor_adaylari, rota_bul
from codes.karar_sozlesmesi import serit_no

TUVAL = 240
R_GEREKLI = 5.0          # min_kapi_px = 2 * R_GEREKLI = 10 px
KORIDOR_DEGERI = 10.0


def _dt(koridorlar, tuval=TUVAL):
    """Tam yukseklikte dikey koridorlardan sentetik mesafe donusumu."""
    dt = np.zeros((tuval, tuval), np.float32)
    for x0, x1 in koridorlar:
        dt[:, x0:x1] = KORIDOR_DEGERI
    return dt


def _etiketler(adaylar):
    return [a["etiket"] for a in adaylar]


class KoridorEtiketiTekKaynakTests(unittest.TestCase):
    def test_her_adayin_etiketi_serit_no_ile_birebir(self):
        """Sozlesme: etiket == serit_no(kapi_merkez_x, icerik_x0, icerik_w).

        Bu esitlik YAYINLANAN alan uzerinden kurulur; disaridan yapilan bir
        denetim etiketi yeniden uretebilmelidir.
        """
        icerik = (0, 0, TUVAL, TUVAL)
        adaylar, _tani = koridor_adaylari(
            _dt([(10, 40), (100, 130)]), R_GEREKLI, icerik=icerik)

        self.assertTrue(adaylar, "aday kapi uretilemedi — sahne gecersiz")
        for a in adaylar:
            self.assertEqual(
                serit_no(a["kapi_merkez_x"], icerik[0], icerik[2]),
                a["etiket"])

    def test_serbest_alan_bbox_uclemesi_geri_gelmez(self):
        """Serbest alan icerik kutusunu DOLDURMAZSA eski sema kayardi.

        Sahne: iki koridor tuvalin SOL YARISINDA. Icerik kutusuna gore
        merkezler serit 1 ve serit 2'dedir.
        ESKI SEMA (serbest alan bbox'i 10..129 uce bolunur) 1 ve **3** verirdi.
        """
        icerik = (0, 0, TUVAL, TUVAL)
        adaylar, tani = koridor_adaylari(
            _dt([(10, 40), (100, 130)]), R_GEREKLI, icerik=icerik)

        self.assertEqual(2, tani["n_kapi"])
        self.assertEqual([1, 2], _etiketler(adaylar))

    def test_uc_kapida_sira_numarasi_dayatilmaz(self):
        """`n_kapi == 3` iken eski sema KOSULSUZ (1, 2, 3) verirdi.

        Sahne: uc koridorun UCU DE tuvalin sol ucte ikisinde. Gercek serit
        numaralari (1, 1, 2)'dir; ucu de ayri seritmis gibi numaralanmasi
        IKA'ya var olmayan bir ayrim bildirirdi.
        """
        icerik = (0, 0, TUVAL, TUVAL)
        adaylar, tani = koridor_adaylari(
            _dt([(10, 40), (60, 90), (110, 140)]), R_GEREKLI, icerik=icerik)

        self.assertEqual(3, tani["n_kapi"])
        self.assertEqual([1, 1, 2], _etiketler(adaylar))
        self.assertNotEqual([1, 2, 3], _etiketler(adaylar))

    def test_ayni_serit_iki_kapiya_verilebilir(self):
        """Iki kapi ayni seritteyse ikisi de o numarayi ALIR.

        Bu KASITLIDIR: eski sema farkli numara UYDURARAK var olmayan bir
        ayrim bildiriyordu. Numara uydurmak yerine gercek anlatilir.
        """
        icerik = (0, 0, TUVAL, TUVAL)
        adaylar, _tani = koridor_adaylari(
            _dt([(10, 40), (45, 75)]), R_GEREKLI, icerik=icerik)

        self.assertEqual([1, 1], _etiketler(adaylar))

    def test_etiket_icerik_kutusunu_izler(self):
        """AYNI maske, FARKLI icerik kutusu -> FARKLI serit. Sozlesme budur.

        ESKI SEMA iki durumda da 2 verirdi (bbox ayni kaliyordu).
        """
        dt = _dt([(100, 130)])

        tam, _t1 = koridor_adaylari(dt, R_GEREKLI, icerik=(0, 0, TUVAL, TUVAL))
        dar, _t2 = koridor_adaylari(dt, R_GEREKLI, icerik=(100, 0, 140, TUVAL))

        self.assertEqual([2], _etiketler(tam))
        self.assertEqual([1], _etiketler(dar))

    def test_etiketler_sozlesme_araliginda(self):
        icerik = (0, 0, TUVAL, TUVAL)
        adaylar, _tani = koridor_adaylari(
            _dt([(10, 40), (100, 130), (190, 220)]), R_GEREKLI, icerik=icerik)

        self.assertTrue(adaylar)
        for a in adaylar:
            self.assertIn(a["etiket"], (1, 2, 3))


class KapiSeritYayilimiTests(unittest.TestCase):
    """Kapi bir NOKTA degil bir ACIKLIKTIR; yayilimi TANI amaclidir."""

    def test_iki_seride_yayilan_kapi_bildirilir(self):
        # Serit 1/2 siniri x = 80. Kapi 60..109 -> iki seride yayilir.
        icerik = (0, 0, TUVAL, TUVAL)
        adaylar, _tani = koridor_adaylari(
            _dt([(60, 110)]), R_GEREKLI, icerik=icerik)

        self.assertEqual(1, len(adaylar))
        self.assertEqual((1, 2), adaylar[0]["serit_yayilimi"])

    def test_tek_seritte_kalan_kapinin_yayilimi_kendisidir(self):
        icerik = (0, 0, TUVAL, TUVAL)
        adaylar, _tani = koridor_adaylari(
            _dt([(10, 40)]), R_GEREKLI, icerik=icerik)

        self.assertEqual(1, len(adaylar))
        self.assertEqual((1, 1), adaylar[0]["serit_yayilimi"])
        self.assertEqual(1, adaylar[0]["etiket"])

    def test_yayilim_etiketi_DEGISTIRMEZ(self):
        """Yayilim karara girmez: etiket AGIRLIK MERKEZINDEN turer.

        Yayinlanan `road` TEK bir sayi olmak zorundadir
        (`comms/protocol.py:51`), bu yuzden yayilim yalnizca TANIDIR.
        """
        icerik = (0, 0, TUVAL, TUVAL)
        adaylar, _tani = koridor_adaylari(
            _dt([(60, 110)]), R_GEREKLI, icerik=icerik)

        aday = adaylar[0]
        self.assertEqual(
            serit_no(aday["kapi_merkez_x"], icerik[0], icerik[2]),
            aday["etiket"])
        self.assertNotEqual(aday["serit_yayilimi"][0],
                            aday["serit_yayilimi"][1])


class OzellikTaramasiTests(unittest.TestCase):
    """Elle secilmis sahneler yanlidir; sozlesme GENIS girdi uzayinda taranir.

    `serit_yayilimi`nin etiketi KAPSAMASI, `x0`in dogru bilesenden
    (`CC_STAT_LEFT`) okundugunu sinar: yanlis bilesenden okunsaydi yayilim
    agirlik merkezini kapsamazdi. Elle yazilan simetrik sahneler bunu
    yakalamaz.
    """

    TOHUM = 20260817          # sabit: test DETERMINISTIK olmali

    def test_rastgele_sahnelerde_sozlesme_tutar(self):
        rng = np.random.default_rng(self.TOHUM)
        sahne = aday = 0
        for _ in range(120):
            tuval = int(rng.integers(120, 400))
            r_ger = float(rng.integers(3, 9))
            dt = np.zeros((tuval, tuval), np.float32)
            yerlesim = []
            for x in sorted(rng.integers(0, tuval - 30,
                                         size=int(rng.integers(1, 5)))):
                gen = int(rng.integers(int(2 * r_ger) + 2,
                                       max(int(2 * r_ger) + 3, 90)))
                if any(x < bit + 6 and bas - 6 < x + gen
                       for bas, bit in yerlesim):
                    continue
                yerlesim.append((x, min(tuval, x + gen)))
                dt[:, x:min(tuval, x + gen)] = r_ger * 2
            if not yerlesim:
                continue
            ix0 = int(rng.integers(0, tuval // 3))
            iw = int(rng.integers(tuval // 2, tuval - ix0))
            adaylar, _tani = koridor_adaylari(
                dt, r_ger, icerik=(ix0, 0, iw, tuval))
            if not adaylar:
                continue
            sahne += 1
            for a in adaylar:
                aday += 1
                with self.subTest(tuval=tuval, icerik=(ix0, iw),
                                  cx=a["kapi_merkez_x"]):
                    self.assertEqual(
                        serit_no(a["kapi_merkez_x"], ix0, iw), a["etiket"])
                    alt, ust = a["serit_yayilimi"]
                    self.assertLessEqual(alt, a["etiket"])
                    self.assertLessEqual(a["etiket"], ust)
                    self.assertIn(a["etiket"], (1, 2, 3))
                    self.assertIn(alt, (1, 2, 3))
                    self.assertIn(ust, (1, 2, 3))
        # POZITIF KONTROL: tarama gercekten aday uretmis olmali, yoksa butun
        # iddialar BOSA gecer.
        self.assertGreater(sahne, 50, "tarama sahne uretemedi — test BOSA gecti")
        self.assertGreater(aday, 80, "tarama aday uretemedi — test BOSA gecti")


class RotaBulEtiketiYayinlarTests(unittest.TestCase):
    """`rota_bul["yol_no"]` bu etiketi YAYINLAR (iha_haritala.py:329)."""

    def _maskeler(self, koridorlar, tuval=TUVAL):
        zemin = np.zeros((tuval, tuval), np.uint8)
        for x0, x1 in koridorlar:
            zemin[:, x0:x1] = 1
        return {0: zemin, 1: np.zeros_like(zemin)}

    def test_yol_no_serit_no_ile_tutarlidir(self):
        """Sahne DETERMINISTIKTIR; `skipTest` YOK.

        Burada eskiden `skipTest` vardi: sahne karar uretmezse test sessizce
        devre disi kalirdi ve `r_gerekli` ya da belirsizlik esigi ilerde
        degisince suite YESIL kalirken bu iddia HIC kosmazdi (bagimsiz denetim
        bulgusu, D-146). Artik karar uretilmemesi BASARISIZLIKTIR.
        """
        maskeler = self._maskeler([(10, 60), (100, 150), (190, 235)])
        sonuc = rota_bul(maskeler, mpp=None, plan=False,
                         icerik=(0, 0, TUVAL, TUVAL))

        self.assertEqual("ACIK", sonuc["durum"])
        self.assertIsNotNone(sonuc["yol_no"],
                             "fikstur karar uretmeli — test devre disi kalmasin")
        kazanan = [a for a in sonuc["adaylar"]
                   if a["etiket"] == sonuc["yol_no"]]
        self.assertEqual(1, len(kazanan),
                         "kazanan etiketi TEK kapiya ait olmali")
        self.assertEqual(
            serit_no(kazanan[0]["kapi_merkez_x"], 0, TUVAL),
            kazanan[0]["etiket"])

    def test_etiket_cokusmesi_FAIL_CLOSED(self):
        """Iki GECILEBILIR kapi ayni seridi gosterirse karar VERILMEZ.

        `serit_no()` cok-bire eslemedir; eski sema (i+1) bunu farkli numara
        UYDURARAK gizliyordu. Numara uydurulmadigi icin belirsizlik artik
        GORUNUR ve fail-closed islenir: `road` hangi koridorun dogrulandigini
        soyleyemiyorsa IKA'ya (`plan_path(road)`) verilmez.

        T90 ONCESI bu sahne `ACIK · yol_no=1` doneriz — yani T90'in ACTIGI bir
        acigi kapatir; bagimsiz denetim bulgusu (D-146).
        """
        # Serit 1 siniri x = 80: ilk IKI koridorun merkezi de serit 1'de.
        maskeler = self._maskeler([(10, 50), (55, 95), (100, 150)])
        sonuc = rota_bul(maskeler, mpp=None, plan=False,
                         icerik=(0, 0, TUVAL, TUVAL))

        etiketler = [a["etiket"] for a in sonuc["adaylar"]]
        gecilebilir = [a["etiket"] for a in sonuc["adaylar"] if a["gecilebilir"]]
        self.assertEqual(3, len(etiketler), "sahne uc kapi uretmeli")
        self.assertGreater(
            len(gecilebilir), len(set(gecilebilir)),
            "sahne COKUSMA uretmeli, yoksa test BOSA gecer")

        self.assertEqual("BELIRSIZ_COKLU", sonuc["durum"])
        self.assertIsNone(sonuc["yol_no"])
        self.assertEqual([], sonuc["waypoints_px"])

    def test_gecilemez_kapinin_ayni_numarayi_tasimasi_KARARI_BOZMAZ(self):
        """Koruma DAR: yalniz GECILEBILIR kapilar arasindaki cokusma sayilir.

        Aksi halde gecilemez bir kapinin numara paylasmasi bosuna yetenek
        yakardi.
        """
        maskeler = self._maskeler([(10, 60), (100, 150), (190, 235)])
        sonuc = rota_bul(maskeler, mpp=None, plan=False,
                         icerik=(0, 0, TUVAL, TUVAL))

        self.assertEqual("ACIK", sonuc["durum"])
        self.assertEqual(
            len({a["etiket"] for a in sonuc["adaylar"] if a["gecilebilir"]}),
            len([a for a in sonuc["adaylar"] if a["gecilebilir"]]))


if __name__ == "__main__":
    unittest.main()
