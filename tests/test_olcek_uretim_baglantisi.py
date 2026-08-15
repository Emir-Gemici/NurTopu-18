"""T86 KAPISI: olcek kahini URETIM karar yoluna gercekten bagli mi?

KUSUR SINIFI (D-98'in dersi): bir halkanin FONKSIYONUN VARLIGINI sinamasi
sahte GECTI uretir. T83 kahini yazdi ve `tests/test_olcek_kahini.py` onu
birim olarak dogruladi; ama D-126 ayni kayitta "uretim cagri yerlerine ve
EKRANA BAGLANMADI" diyordu ve D-136 sonucu olctu: 7 kaynagin 5'i OLCEK_YOK.

Bu paket kahinin DAVRANISINI uretim yolunda sinar:
  1. Telemetri/beyan varsa katman 1 kazanir ve carpan 1.00 kalir (GERIYE UYUM).
  2. Telemetri yoksa katman 3 devreye girer ve GUVEN CARPANI karara YANSIR.
  3. 🔴 KAPI GEVSEMEZ: hicbir katman uretemezse `rota_olcek_reddi` HALA reddeder.
  4. 🔴 SESSIZ DUSUS YOK: hangi katmanin neden dustugu metinde YAZILIDIR.
  5. Katman 2 senaryo BEYAN EDILMEDIKCE devreye girmez (2,5 kat olcek hatasi).
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

KOK = Path(__file__).resolve().parents[1]
for alt in ("codes", "comms"):
    if str(KOK / alt) not in sys.path:
        sys.path.insert(0, str(KOK / alt))

from karar_sozlesmesi import (OLCEK_GUVEN_CARPANI,  # noqa: E402
                              OLCEK_KAYNAK_ARAC,
                              OLCEK_KAYNAK_ARENA,
                              OLCEK_KAYNAK_ETIKETI,
                              OLCEK_KAYNAK_TELEMETRI,
                              olcek_guveni_uygula, rota_olcek_reddi,
                              olcek_kaynak_metni)
from rpi_inference import kare_olcek_kahini  # noqa: E402

ICERIK = (0, 0, 1024, 576)
#: 1,80 m / 24 px = 0,075 m/px — D-124'un olctugu bandin ortasi.
ARAC_KISA_KENAR_PX = 24.0


class _SahteOBB:
    """Ultralytics OBB donusunun YALNIZ okunan alanlarini taklit eder."""

    def __init__(self, kisa_kenarlar, sinif_adi="small vehicle"):
        self.names = {0: sinif_adi}
        self._kisa = list(kisa_kenarlar)

    def predict(self, bgr, imgsz=None, conf=None, verbose=False):
        import types

        class _T:
            def __init__(self, dizi):
                self._d = np.asarray(dizi, dtype=np.float32)

            def cpu(self):
                return self

            def numpy(self):
                return self._d

        n = len(self._kisa)
        # xywhr: [x, y, genislik, yukseklik, aci] — kisa kenar min(w, h).
        xywhr = np.zeros((n, 5), dtype=np.float32)
        for i, k in enumerate(self._kisa):
            xywhr[i] = (10.0, 10.0, k * 2.5, k, 0.0)
        return [types.SimpleNamespace(
            obb=types.SimpleNamespace(cls=_T(np.zeros(n)), xywhr=_T(xywhr),
                                      xyxyxyxy=None))]


def _kare():
    return np.zeros((576, 1024, 3), np.uint8)


class KatmanSirasiTests(unittest.TestCase):
    """Hangi katman kazaniyor — ve KAYNAGINI beyan ediyor mu?"""

    def test_beyan_VARSA_katman1_kazanir_carpan_DEGISMEZ(self):
        """GERIYE UYUM: arena yolu telemetriyle koşar, T86 onu bozmamali."""
        k = kare_olcek_kahini(0.0781, None, ICERIK, bgr=_kare(),
                              arac_modeli=_SahteOBB([ARAC_KISA_KENAR_PX]))
        self.assertEqual(OLCEK_KAYNAK_TELEMETRI, k["kaynak"])
        self.assertAlmostEqual(0.0781, k["mpp"])
        self.assertEqual(1.00, k["guven_carpani"])

    def test_beyan_YOKSA_katman3_devreye_girer(self):
        k = kare_olcek_kahini(None, None, ICERIK, bgr=_kare(),
                              arac_modeli=_SahteOBB([ARAC_KISA_KENAR_PX]))
        self.assertEqual(OLCEK_KAYNAK_ARAC, k["kaynak"])
        self.assertAlmostEqual(1.80 / ARAC_KISA_KENAR_PX, k["mpp"], places=6)

    def test_katman3_MEDYAN_kullanir_tek_kotu_kutu_kaydirmaz(self):
        """Bir kamyon/golge kutusu olcegi tek basina bozamamali (D-124)."""
        k = kare_olcek_kahini(None, None, ICERIK, bgr=_kare(),
                              arac_modeli=_SahteOBB([24.0, 24.0, 24.0, 300.0]))
        self.assertEqual(OLCEK_KAYNAK_ARAC, k["kaynak"])
        self.assertAlmostEqual(1.80 / 24.0, k["mpp"], places=6)

    def test_arac_SINIFI_ad_ile_eslesir_yabanci_sinif_olcek_URETMEZ(self):
        """S1/K-6: id kayar, ad kaymaz. `ship` bir arac referansi DEGILDIR."""
        k = kare_olcek_kahini(None, None, ICERIK, bgr=_kare(),
                              arac_modeli=_SahteOBB([24.0], sinif_adi="ship"))
        self.assertIsNone(k["kaynak"])
        self.assertIsNone(k["mpp"])


class KapiGevsemediTests(unittest.TestCase):
    """🔴 T86'nin DEGISTIRMEDIGI sey: olcek yoksa rota YAYINLANMAZ."""

    def test_hicbir_katman_uretmezse_OLCEK_KAPISI_HALA_REDDEDER(self):
        k = kare_olcek_kahini(None, None, ICERIK, bgr=_kare(), arac_modeli=None)
        self.assertIsNone(k["mpp"])
        self.assertIsNotNone(rota_olcek_reddi(k["mpp"]),
                             "olcek kahini bagliyken kapi GEVSEMIS — "
                             "olceksiz kare reddedilmiyor")

    def test_arac_YOKSA_olcek_uydurulmaz(self):
        k = kare_olcek_kahini(None, None, ICERIK, bgr=_kare(),
                              arac_modeli=_SahteOBB([]))
        self.assertIsNone(k["mpp"])
        self.assertIsNotNone(rota_olcek_reddi(k["mpp"]))

    def test_dedektor_PATLARSA_olcek_uydurulmaz(self):
        class _Patlak:
            names = {0: "small vehicle"}

            def predict(self, *a, **k):
                raise RuntimeError("cuda out of memory")

        k = kare_olcek_kahini(None, None, ICERIK, bgr=_kare(),
                              arac_modeli=_Patlak())
        self.assertIsNone(k["mpp"])
        self.assertIsNotNone(rota_olcek_reddi(k["mpp"]))
        self.assertIn("HATA", dict(k["denenen"])[OLCEK_KAYNAK_ARAC])

    def test_katman3_olcegi_GUVENI_DUSURUR(self):
        """Katman 3'ten gelen olcek telemetriyle AYNI guvende sunulamaz."""
        ham = 0.90
        k1 = kare_olcek_kahini(0.0781, None, ICERIK)
        k3 = kare_olcek_kahini(None, None, ICERIK, bgr=_kare(),
                               arac_modeli=_SahteOBB([ARAC_KISA_KENAR_PX]))
        g1 = olcek_guveni_uygula(ham, k1["kaynak"])
        g3 = olcek_guveni_uygula(ham, k3["kaynak"])
        self.assertAlmostEqual(ham * 1.00, g1)
        self.assertAlmostEqual(ham * OLCEK_GUVEN_CARPANI[OLCEK_KAYNAK_ARAC], g3)
        self.assertLess(g3, g1, "katman 3 guveni DUSURMUYOR")


class SessizDususYokTests(unittest.TestCase):
    """🔴 Hangi katmanin NEDEN devreye girmedigi YAZILI olmali."""

    def test_dokum_UC_katmani_da_sayar(self):
        k = kare_olcek_kahini(None, None, ICERIK, bgr=_kare(), arac_modeli=None)
        kaynaklar = [x for x, _ in k["denenen"]]
        self.assertEqual([OLCEK_KAYNAK_TELEMETRI, OLCEK_KAYNAK_ARENA,
                          OLCEK_KAYNAK_ARAC], kaynaklar)

    def test_DEDEKTOR_yoklugu_ile_ARAC_yoklugu_AYRI_raporlanir(self):
        """Ikisi ayni sey degildir: biri yapilandirma, digeri sahne."""
        yok = dict(kare_olcek_kahini(None, None, ICERIK, bgr=_kare(),
                                     arac_modeli=None)["denenen"])
        bos = dict(kare_olcek_kahini(None, None, ICERIK, bgr=_kare(),
                                     arac_modeli=_SahteOBB([]))["denenen"])
        self.assertIn("dedektor", yok[OLCEK_KAYNAK_ARAC])
        self.assertIn("arac YOK", bos[OLCEK_KAYNAK_ARAC])
        self.assertNotEqual(yok[OLCEK_KAYNAK_ARAC], bos[OLCEK_KAYNAK_ARAC])

    def test_ekran_metni_KAYNAGI_ve_CARPANI_tasir(self):
        k = kare_olcek_kahini(None, None, ICERIK, bgr=_kare(),
                              arac_modeli=_SahteOBB([ARAC_KISA_KENAR_PX]))
        metin = olcek_kaynak_metni(k)
        self.assertIn(OLCEK_KAYNAK_ETIKETI[OLCEK_KAYNAK_ARAC], metin)
        self.assertIn("0.86", metin)

    def test_olceksiz_metin_HER_katmanin_sebebini_yazar(self):
        metin = olcek_kaynak_metni(
            kare_olcek_kahini(None, None, ICERIK, bgr=_kare(), arac_modeli=None))
        for kaynak in (OLCEK_KAYNAK_TELEMETRI, OLCEK_KAYNAK_ARENA,
                       OLCEK_KAYNAK_ARAC):
            with self.subTest(kaynak=kaynak):
                self.assertIn(OLCEK_KAYNAK_ETIKETI[kaynak], metin)


class Katman2BeyanTests(unittest.TestCase):
    """🔴 Senaryo BEYAN EDILIR, tahmin edilmez (yanlis senaryo = 2,5 kat hata)."""

    def test_senaryo_BEYAN_EDILMEDIKCE_katman2_calismaz(self):
        k = kare_olcek_kahini(None, None, ICERIK, arena_sinir_px=900.0,
                              senaryo=None)
        self.assertIsNone(k["mpp"])
        self.assertIn("BEYAN EDILMEDI", dict(k["denenen"])[OLCEK_KAYNAK_ARENA])

    def test_senaryo_beyan_edilince_katman2_uretir_ve_carpani_070(self):
        k = kare_olcek_kahini(None, None, ICERIK, arena_sinir_px=900.0,
                              senaryo="HTAB")
        self.assertEqual(OLCEK_KAYNAK_ARENA, k["kaynak"])
        self.assertAlmostEqual(50.0 / 900.0, k["mpp"], places=6)
        self.assertEqual(0.70, k["guven_carpani"])

    def test_katman2_katman3ten_ONCE_denenir(self):
        """Siralama kullanicinin karari; olcum onu dogrulamasa da (D-126) UYULUR."""
        k = kare_olcek_kahini(None, None, ICERIK, bgr=_kare(),
                              arac_modeli=_SahteOBB([ARAC_KISA_KENAR_PX]),
                              arena_sinir_px=900.0, senaryo="HTAB")
        self.assertEqual(OLCEK_KAYNAK_ARENA, k["kaynak"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
