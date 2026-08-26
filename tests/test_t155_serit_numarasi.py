"""T155 — YAYINLANAN serit numarasi yer gercegiyle uyusuyor mu?

NEDEN (REVIEW_LOG D-295 / D-296 · ON_KAYIT SS17). Uretim yolu
(`rpi_inference.analyze_path`) yer gercekli 15 arena sahnesinin 9'unda YANLIS
serit numarasi yayinliyordu (6/15). Rotanin GEOMETRISI 15/15 dogru koridordaydi
— yanlis olan YAYINLANAN SAYIYDI. Sebep: yayin alani `darbogaz_serit`, rotanin
EN DAR noktasinin — yani TEK PIKSELIN — seridiydi ve o piksel 15 sahnenin
13'unde rotanin UCUNDA olculuyordu (y=39 / y=460), yani KB/HB yakininda uc
guzergahin BIRLESTIGI, serit kimliginin TANIMSIZ oldugu yerde.

`road` IKA'yi SURMEZ (D-166 — surus `waypoints`+`ref_xy` ile olur) ama
sartname SS2.2.3'te hakemin canli onayladigi ve PUANLANAN etikettir
(`comms/yks_gui.py`).

BU DOSYA UC SEYI BIRDEN TUTAR:
  1. DEGER KAPISI — yer gercekli sahnelerde yayinlanan sayi dogru mu
     (ozellikle T155 ONCESI YANLIS olan sahnelerden secilmis 9'u).
  2. MUTASYON MUHAFIZI — yayin hatti eski `darbogaz_serit`e cevrilirse bu
     dosyadan test DUSMELI (yoksa kapi vakumdur, D-15).
  3. BOZULMAMA — degisiklik YALNIZ yayinlanan sayiyi degistirmeli;
     waypoint'ler ve ret sebepleri AYNI kalmali (ON_KAYIT SS17 ek sart).

⚠ SINIR (raporda da aynen durur): sahneler SENTETIKtir ve maske KUSURSUZdur.
  Bu bir ALGI olcumu degil MANTIK olcumudur; gercek karelerde oran BU DEGILDIR.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
for _alt in ("codes", "simulation/scripts"):
    _p = str(KOK / _alt)
    if _p not in sys.path:
        sys.path.insert(0, _p)

import arena  # noqa: E402
from karar_sozlesmesi import rota_serit_karari, serit_no  # noqa: E402
from rpi_inference import analyze_path  # noqa: E402
import test_rota_sentetik as TRS  # noqa: E402

# T155 ONCESI YANLIS YAYINLANAN sahneler (results/t155/once_master.json).
# Gorev sarti "15 sahnenin en az 5'i, YANLIS cikanlardan secilmis"; dokuzunun
# TAMAMI alinir — eksiltmek kapiyi zayiflatirdi.
# (harita, senaryo, yer_gercegi, T155 ONCESI yayinlanan yanlis deger)
ONCEDEN_YANLIS = (
    (1, "kolay", 1, 2),
    (1, "zor", 3, 2),
    (2, "kolay", 1, 2),
    (2, "orta", 1, 2),
    (3, "zor", 1, 3),
    (4, "kolay", 3, 2),
    (4, "zor", 1, 2),
    (5, "kolay", 3, 2),
    (5, "zor", 2, 1),
)


def _kos(harita_id, senaryo):
    H, zemin, engel, _b, _h = TRS.sahne_uret(harita_id, senaryo)
    yol, guven, wps, ret, olc = analyze_path(
        zemin, icerik=None, engel_mask=engel, mpp=TRS.MPP,
        return_reason=True, return_olcum=True)
    return int(H["open"]), yol, wps, ret, olc


class T155DegerKapisiTests(unittest.TestCase):
    """1. YAYINLANAN sayi yer gercegiyle uyusuyor mu?"""

    def test_onceden_yanlis_dokuz_sahne_artik_dogru(self):
        """KAPI: T155 oncesi YANLIS olan 9 sahnenin hepsi artik dogru.

        Bagimsiz kahin: `arena.harita()` hangi guzergahi ACIK biraktigini
        uretecin kendi tohumundan bilir (`H["open"]`) ve bu bilgi karar
        yoluna HIC verilmez.
        """
        for hid, sen, gercek, eski_yanlis in ONCEDEN_YANLIS:
            with self.subTest(harita=hid, senaryo=sen):
                gt, yol, _wps, ret, _olc = _kos(hid, sen)
                self.assertEqual(gt, gercek, "yer gercegi kaymis — sahne degismis")
                self.assertIsNotNone(yol, f"{hid}/{sen}: karar uretilmedi ({ret})")
                self.assertEqual(
                    yol, gercek,
                    f"{hid}/{sen}: yayinlanan road={yol}, yer gercegi {gercek} "
                    f"(T155 oncesi {eski_yanlis} yayinlaniyordu)")

    def test_on_kayit_kapisi_15_sahnede_en_az_14(self):
        """KAPI (ON_KAYIT SS17): 15 sahnenin >= 14'unde yayin dogru."""
        dogru = 0
        toplam = 0
        yanlislar = []
        for hid in range(1, arena.HARITA_N + 1):
            for sen in arena.SCENARIOS:
                gt, yol, _wps, _ret, _olc = _kos(hid, sen)
                toplam += 1
                if yol == gt:
                    dogru += 1
                else:
                    yanlislar.append(f"{hid}/{sen}: yayin={yol} gercek={gt}")
        self.assertEqual(toplam, 15, "sahne sayisi 15 degil")
        self.assertGreaterEqual(
            dogru, 14,
            f"ON_KAYIT SS17 kapisi: {dogru}/15 (>= 14 gerekli). "
            f"Yanlislar: {yanlislar}")


class T155MutasyonMuhafiziTests(unittest.TestCase):
    """2. Yayin hatti eski alana cevrilirse BU DOSYADAN test dusmeli."""

    def test_darbogaz_serit_bu_sahnelerde_YANLIS_kalmayi_surduruyor(self):
        """MUTASYON MUHAFIZI — vakum kapi degil.

        `open_path = olcum["serit_karari"]` satiri `olcum["darbogaz_serit"]`e
        geri cevrilirse `test_onceden_yanlis_dokuz_sahne_artik_dogru` DUSER.
        Bu test o mutasyonun ETKILI oldugunu ISPATLAR: ayni 9 sahnede
        `darbogaz_serit` HALA yanlis deger tasiyor. Ikisi birlikte kapiyi
        vakumdan cikarir (D-15).
        """
        for hid, sen, gercek, eski_yanlis in ONCEDEN_YANLIS:
            with self.subTest(harita=hid, senaryo=sen):
                _gt, _yol, _wps, _ret, olc = _kos(hid, sen)
                self.assertIsNotNone(olc, f"{hid}/{sen}: olcum uretilmedi")
                self.assertEqual(
                    olc["darbogaz_serit"], eski_yanlis,
                    f"{hid}/{sen}: darbogaz_serit={olc['darbogaz_serit']}, "
                    f"T155 oncesi {eski_yanlis} olculmustu")
                self.assertNotEqual(
                    olc["darbogaz_serit"], gercek,
                    f"{hid}/{sen}: darbogaz_serit artik dogru — bu sahne "
                    "mutasyonu ayirt etmiyor, kapi zayifladi")

    def test_yayin_alani_serit_kararina_bagli(self):
        """Yayinlanan deger olcumun `serit_karari` alanidir (tum 15 sahne)."""
        for hid in range(1, arena.HARITA_N + 1):
            for sen in arena.SCENARIOS:
                with self.subTest(harita=hid, senaryo=sen):
                    _gt, yol, _wps, _ret, olc = _kos(hid, sen)
                    if yol is None or olc is None:
                        continue
                    self.assertEqual(yol, olc["serit_karari"])


class T155BozulmamaTests(unittest.TestCase):
    """3. Degisiklik YALNIZ yayinlanan sayiyi degistirdi."""

    # results/t155/once_master.json — T155 ONCESI (master) waypoint sayilari
    # ve ret sebepleri. Bayt-es kiyasin testteki ozeti; tam kiyas
    # `results/t155/bozulmama_kiyas.py` ile kosulur (142 waypoint, 0 fark).
    ONCEKI_WP_SAYISI = {
        (1, "kolay"): 8, (1, "orta"): 8, (1, "zor"): 12,
        (2, "kolay"): 8, (2, "orta"): 10, (2, "zor"): 10,
        (3, "kolay"): 8, (3, "orta"): 10, (3, "zor"): 10,
        (4, "kolay"): 8, (4, "orta"): 13, (4, "zor"): 12,
        (5, "kolay"): 8, (5, "orta"): 9, (5, "zor"): 8,
    }

    def test_waypoint_KOORDINATLARI_t155_oncesiyle_BAYT_ES(self):
        """ON_KAYIT §17 BOZULMAMA sarti — SAYI degil KOORDINAT kilidi (D-296).

        Cururtucu olctu: sayi kilidi, waypoint'leri sayiyi koruyarak KAYDIRAN
        bir degisikligi yakalamaz; on kayit tam olarak bunu sart kosuyordu.
        Referans `results/t155/once_master.json` (T155 ONCESI master kodu).
        """
        import json as _json
        ref_yol = KOK / "results" / "t155" / "once_master.json"
        self.assertTrue(ref_yol.is_file(), f"referans yok: {ref_yol}")
        ref = {(s["harita"], s["senaryo"]): s for s in
               _json.loads(ref_yol.read_text(encoding="utf-8"))["satirlar"]}
        self.assertEqual(15, len(ref), "referans 15 sahne olmali")
        for anahtar, s in sorted(ref.items()):
            with self.subTest(sahne=anahtar):
                _g, _yol, wps, ret, _olc = _kos(anahtar[0], anahtar[1])
                self.assertEqual(
                    [[int(x), int(y)] for x, y in s["waypointler"]],
                    [[int(x), int(y)] for x, y in wps],
                    f"{anahtar}: waypoint KOORDINATLARI degisti — T155 yalniz "
                    "YAYINLANAN sayiyi degistirmeliydi (madde 15, on kayit §17)")
                self.assertEqual(s["ret"], ret[0] if isinstance(ret, tuple) else ret,
                                 f"{anahtar}: ret sebebi degisti")

    def test_waypoint_sayilari_t155_oncesiyle_ayni(self):
        """KAPI (ON_KAYIT SS17 ek sart): rota DEGISMEDI, yalniz ADI degisti."""
        for hid in range(1, arena.HARITA_N + 1):
            for sen in arena.SCENARIOS:
                with self.subTest(harita=hid, senaryo=sen):
                    _gt, _yol, wps, _ret, _olc = _kos(hid, sen)
                    self.assertEqual(
                        len(wps), self.ONCEKI_WP_SAYISI[(hid, sen)],
                        f"{hid}/{sen}: waypoint sayisi degisti — T155 rotayi "
                        "etkilememeliydi")

    def test_hicbir_sahnede_ret_uretilmiyor(self):
        """T155 oncesi 15 sahnenin hicbirinde ret yoktu; sonrasinda da yok."""
        for hid in range(1, arena.HARITA_N + 1):
            for sen in arena.SCENARIOS:
                with self.subTest(harita=hid, senaryo=sen):
                    _gt, yol, _wps, ret, _olc = _kos(hid, sen)
                    self.assertIsNone(ret, f"{hid}/{sen}: yeni ret {ret}")
                    self.assertIsNotNone(yol)

    def test_darbogaz_tani_alani_korundu(self):
        """`darbogaz_serit` ve `seritler` TANI olarak sozlukte duruyor."""
        _gt, _yol, _wps, _ret, olc = _kos(1, "kolay")
        for alan in ("darbogaz_serit", "baskin_serit", "seritler",
                     "darbogaz_px", "darbogaz_xy", "serit_karari"):
            self.assertIn(alan, olc, f"{alan} olcum sozlugunden dusmus")


class T155OrtakFonksiyonTests(unittest.TestCase):
    """`rota_serit_karari` TEK TANIM — iki karar yolu da onu cagirir."""

    def test_sayim_ve_karar_govdeyi_secer(self):
        """icerik_w=300 -> sinirlar 100 ve 200: x=10 serit 1, x=150 serit 2.

        Govde serit 1'de (100 piksel), serit 2'de yalniz 5 piksel var —
        arena 1/kolay'daki 419/3/0 orugunun kucuk olcegi. Karar govdeyi
        secmeli; eski darbogaz tanimi burada 2 diyebilirdi.
        """
        karar, sayim = rota_serit_karari(
            [(10, 0)] * 100 + [(150, 0)] * 5, 0, 300)
        self.assertEqual(sayim, (100, 5, 0))
        self.assertEqual(karar, 1)

    def test_bos_rota_none_doner(self):
        karar, sayim = rota_serit_karari([], 0, 300)
        self.assertIsNone(karar)
        self.assertEqual(sayim, (0, 0, 0))

    def test_beraberlikte_kucuk_indis_deterministik(self):
        """Esit sayimda KUCUK serit indisi — yazi-tura atilmaz."""
        karar, sayim = rota_serit_karari(
            [(10, 0)] * 7 + [(150, 0)] * 7, 0, 300)
        self.assertEqual(sayim, (7, 7, 0))
        self.assertEqual(karar, 1)

    def test_serit_sinirlari_serit_no_ile_ayni_kaynaktan(self):
        """Karar `serit_no()` disinda bir bolusum UYDURMAZ (madde 16)."""
        for x in (0, 99, 100, 199, 200, 299):
            karar, _ = rota_serit_karari([(x, 0)], 0, 300)
            self.assertEqual(karar, serit_no(x, 0, 300),
                             f"x={x}: karar serit_no'dan ayristi")

    def test_rota_bul_capraz_denetimi_arena_da_uyusuyor(self):
        """`rota_bul` ayni ortak fonksiyonu cagirir ve 15/15 uyusur."""
        from costmap_path_finder import rota_bul
        uyusan = 0
        olculen = 0
        for hid in range(1, arena.HARITA_N + 1):
            for sen in arena.SCENARIOS:
                _H, zemin, engel, bas, hed = TRS.sahne_uret(hid, sen)
                r = rota_bul({0: zemin, 1: engel}, mpp=TRS.MPP,
                             baslangic=bas, hedef=hed, plan=True)
                if r["yol_no"] is None or r.get("rota_serit") is None:
                    continue
                olculen += 1
                uyusan += bool(r["serit_uyumu"])
        self.assertEqual(olculen, 15, "15 sahnede karar uretilemedi")
        self.assertEqual(
            uyusan, 15,
            "rota_bul'un kapi etiketi ile govde karari ayristi — iki karar "
            "yolu ayni seyi soylemiyor (D-295 tekrari)")


if __name__ == "__main__":
    unittest.main(verbosity=2)
