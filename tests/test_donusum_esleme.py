"""T54 KAPISI: kanonik donusum "cati zemin degildir" diyor — TEK KAYNAKTAN.

KUSUR (D-67 · kok neden): `dataset/download_and_convert.py` yalniz
road-clear(7)->0 ve road-blocked(8)->1 aliyordu; bina/agac/su/havuz ETIKETSIZ
arka plana dusuyordu. Etiketsiz arka plan denetim almaz -> modele hicbir yerde
"cati zemin DEGILDIR" denmedi.

⚠ SEMA TUZAGI (D-195): HAM RescueNet id'leri ile 11-sinif ara kume indeksleri
AYNI DEGILDIR ve gorev metninde bir kez KARISTIRILDI (harfiyen uygulansa ARAC
yanlislikla girer, su/havuz DISARIDA kalirdi). Bu testler HAM kumeleri
ACIK LITERALLE civiler — tam da bu karisikligi bir daha SESSIZ gecirmemek icin.

ARAC KARARI OLCUMLE (D-199): DOTA OBB, RescueNet arac piksellerinin %0,0'ini
yakaliyor (n=40, 4.469.436 px, kesisim 0). "Cift sayim" bu veride BOSTUR;
arac ENGELDIR ve uretimde egitilen kume (57 zinciri) de oyle sayar.
"""

import unittest
from pathlib import Path

from dataset import download_and_convert as D

KOK = Path(__file__).resolve().parent.parent

#: HAM RescueNet id'leri (RESMI Note.txt · D-195'teki tablo).
HAM_TRAVERSABLE = {7}
HAM_VEHICLE = {6}
HAM_BLOCKED = {8, 1, 2, 3, 4, 5, 9, 10} | HAM_VEHICLE   # arac DAHIL (olculdu)


class DonusumEslemesi(unittest.TestCase):

    # ── TEK KAYNAK ────────────────────────────────────────────────────────
    def test_esleme_41_AYNASINDAN_okunuyor(self):
        """Ikinci kopya YOK: kaynak `scripts/olcum/41_cok_sinifli_veri.py`."""
        self.assertTrue(D._ESLEME_AYNASI.is_file(), str(D._ESLEME_AYNASI))
        self.assertEqual("41_cok_sinifli_veri.py", D._ESLEME_AYNASI.name)
        self.assertEqual(10, len(D.SINIF_ESLEME),
                         "SINIF_ESLEME 10 ham sinif tasimali (0=Background haric)")

    def test_esleme_degisirse_DONUSUM_KENDILIGINDEN_izler(self):
        """Turetim ADLARDAN: 41'deki `traversable` hangi ham id'deyse o."""
        beklenen = {h for h, (_i, ad) in D.SINIF_ESLEME.items()
                    if ad == "traversable"}
        self.assertEqual(beklenen, D.TRAVERSABLE_HAM)

    # ── HAM KUMELER (D-195 tuzagina karsi ACIK literal) ───────────────────
    def test_traversable_HAM_7(self):
        self.assertEqual(HAM_TRAVERSABLE, D.TRAVERSABLE_HAM,
                         "traversable HAM 7'dir (Road-Clear) — 11-sinif "
                         "indeksi 0 ile KARISTIRILMASIN (D-195)")

    def test_blocked_HAM_kumesi_TAM(self):
        self.assertEqual(HAM_BLOCKED, D.BLOCKED_HAM,
                         "engel kumesi {8}+{1,2,3,4,5,9,10}+{6 arac} olmali — "
                         "eksik sinif 'cati zemin degildir' dersini geri alir")

    def test_bina_agac_su_havuz_ENGELDE(self):
        """D-67'nin kalbi: cati/agac/su/havuz artik etiketsiz DEGIL."""
        for ham, ad in ((2, "building_no_damage"), (3, "building_minor"),
                        (4, "building_major"), (5, "building_total"),
                        (9, "tree"), (1, "water"), (10, "pool")):
            self.assertIn(ham, D.BLOCKED_HAM, f"HAM {ham} ({ad}) engel DEGIL")

    def test_ARAC_karari_OLCUMLE_engelde(self):
        """DOTA kapsamasi %0,0 olculdu (D-199) — arac egitim etiketinde ENGEL."""
        self.assertLessEqual(D.VEHICLE_HAM, D.BLOCKED_HAM)
        self.assertEqual(HAM_VEHICLE, D.VEHICLE_HAM)

    def test_traversable_ile_blocked_AYRIK_ve_background_DISARIDA(self):
        self.assertEqual(set(), D.TRAVERSABLE_HAM & D.BLOCKED_HAM)
        self.assertNotIn(0, D.TRAVERSABLE_HAM | D.BLOCKED_HAM,
                         "Background(0) etiketlenmez — YOLO'da ortuk")

    # ── URETIMDE EGITILEN KUMEYLE TUTARLILIK ──────────────────────────────
    def test_57_zinciriyle_AYNI_semantik(self):
        """`57_t54_engel_eslemesi.py::ESLEME` (11-sinif -> 2) ile bu donusum
        (HAM -> 2) AYNI 2-sinif sonucu vermeli. Kopru: 41'in HAM -> 11-sinif
        eslemesi. Iki zincir ayrisirsa egitilen veri ile kanonik donusturucu
        FARKLI ders verir — dort kez yasanan 'iki kopya' kusuru."""
        import ast
        yol = KOK / "scripts" / "olcum" / "57_t54_engel_eslemesi.py"
        agac = ast.parse(yol.read_text(encoding="utf-8"))
        esleme57 = None
        for dugum in ast.walk(agac):
            if isinstance(dugum, ast.Assign):
                for hedef in dugum.targets:
                    if getattr(hedef, "id", None) == "ESLEME":
                        esleme57 = ast.literal_eval(dugum.value)
        self.assertIsNotNone(esleme57, "57'de ESLEME bulunamadi")
        for ham, (idx11, _ad) in D.SINIF_ESLEME.items():
            benim = 0 if ham in D.TRAVERSABLE_HAM else 1
            self.assertEqual(esleme57[idx11], benim,
                             f"HAM {ham}: kanonik {benim}, 57 zinciri "
                             f"{esleme57[idx11]} — iki zincir AYRISTI")


if __name__ == "__main__":
    unittest.main()
