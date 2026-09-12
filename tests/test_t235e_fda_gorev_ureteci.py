"""NÖBETÇİ — T235-E FDA görev üreteci (`scripts/fda_gorev_uret.py`).

İki ÖLÇÜLMÜŞ kusurun yapısal olarak geri gelemeyeceğini kilitler:

  K1  `NAV_LOITER_TIME` satırı MERKEZ lat/lon taşır (0,0 DEĞİL) — D-451 olgu 3:
      şablonda 0,0 olduğu için İHA son köşede bekliyordu, merkezde değil.
  K2  `CONDITION_YAW` satırı `NAV_LOITER_TIME`'dan **ÖNCE** gelir — D-457 SITL
      ölçümü: sonra konunca yaw 0/499 DÜŞTÜ (p50 134,8°), önce konunca 500/500
      GEÇTİ (p50 0,18–0,37°).
  K3  merkez = 4 köşenin ortalaması (mutasyon: 5. köşe / tek köşe yakalanır).
  K4  β kerterizi Başlangıç kenarı ortasından karşı kenar ortasına; komut açısı
      β − montaj_yaw (mutasyon: işaret ters çevrilirse yakalanır).
  K5  irtifa FENCE_ALT_MAX (50 m) altında olmak ZORUNDA — üstü reddedilir.
  K6  çıktı QGC WPL 110 biçimi: 12 sekmeli sütun, ilk satır başlık.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
for _p in (KOK / "scripts", KOK / "codes"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import fda_gorev_uret as ug  # noqa: E402

# ~20x20 m kare (şartname FDA alanı), Adıyaman civarı enlemde.
KOSELER = [(37.7500000, 38.2500000), (37.7501798, 38.2500000),
           (37.7501798, 38.2502271), (37.7500000, 38.2502271)]


def _satirlar(**kw):
    varsayilan = dict(koseler=KOSELER, baslangic_kenari=0, montaj_yaw=0.0,
                      irtifa_m=32.0, loiter_s=60.0)
    varsayilan.update(kw)
    return ug.gorev_satirlari(**varsayilan)


class GorevUreteci(unittest.TestCase):
    def setUp(self):
        self.satirlar, self.bilgi = _satirlar()
        self.komutlar = [s[1] for s in self.satirlar]

    def test_K1_loiter_MERKEZ_tasir_sifir_sifir_DEGIL(self):
        i = self.komutlar.index(ug.CMD_NAV_LOITER_TIME)
        lat, lon = self.satirlar[i][6], self.satirlar[i][7]
        self.assertNotEqual((0.0, 0.0), (lat, lon),
                            "LOITER_TIME 0,0 = 'bulunduğun yerde bekle' (köşede) — D-451 kusuru")
        self.assertAlmostEqual(self.bilgi["merkez"][0], lat, places=7)
        self.assertAlmostEqual(self.bilgi["merkez"][1], lon, places=7)

    def test_K2_condition_yaw_LOITERDAN_ONCE(self):
        self.assertIn(ug.CMD_CONDITION_YAW, self.komutlar, "CONDITION_YAW hiç yok")
        self.assertLess(self.komutlar.index(ug.CMD_CONDITION_YAW),
                        self.komutlar.index(ug.CMD_NAV_LOITER_TIME),
                        "D-457: CONDITION_YAW LOITER_TIME'dan SONRA konunca yaw 0/499 DÜŞTÜ")

    def test_K3_merkez_dort_kosenin_ortalamasi(self):
        beklenen_lat = sum(k[0] for k in KOSELER) / 4
        beklenen_lon = sum(k[1] for k in KOSELER) / 4
        self.assertAlmostEqual(beklenen_lat, self.bilgi["merkez"][0], places=9)
        self.assertAlmostEqual(beklenen_lon, self.bilgi["merkez"][1], places=9)
        # Negatif kontrol: tek köşe merkez DEĞİLDİR (boş kıyas olmasın).
        self.assertNotAlmostEqual(KOSELER[0][0], self.bilgi["merkez"][0], places=5)

    def test_K4_beta_ve_montaj_yaw_isareti(self):
        # Başlangıç kenarı 0-1 (batı kenarı) → karşı kenar doğuda → β ≈ 90°.
        self.assertAlmostEqual(90.0, self.bilgi["beta"], places=1)
        self.assertAlmostEqual(90.0, self.bilgi["komut_yaw"], places=1)
        # montaj_yaw ÇIKARILIR (eklenmez): β=90, montaj=30 → komut 60.
        _, bilgi30 = _satirlar(montaj_yaw=30.0)
        self.assertAlmostEqual(60.0, bilgi30["komut_yaw"], places=1)
        # Karşı kenardan başlanırsa β ters yöne döner (≈270°).
        _, bilgi2 = _satirlar(baslangic_kenari=2)
        self.assertAlmostEqual(270.0, bilgi2["beta"], places=1)

    def test_K5_irtifa_FENCE_ALT_MAX_altinda_olmali(self):
        with self.assertRaises(ValueError):
            _satirlar(irtifa_m=ug.FENCE_ALT_MAX_M)       # tam sınır da reddedilir
        with self.assertRaises(ValueError):
            _satirlar(irtifa_m=ug.FENCE_ALT_MAX_M + 10)
        with self.assertRaises(ValueError):
            _satirlar(irtifa_m=0.0)
        _satirlar(irtifa_m=ug.FENCE_ALT_MAX_M - 1)       # altı kabul

    def test_K5b_dort_koseden_az_ya_da_cok_REDDEDILIR(self):
        with self.assertRaises(ValueError):
            _satirlar(koseler=KOSELER[:3])
        with self.assertRaises(ValueError):
            _satirlar(koseler=KOSELER + [KOSELER[0]])

    def test_K6_wpl_bicimi(self):
        metin = ug.wpl_metni(self.satirlar)
        satirlar = metin.strip().split("\n")
        self.assertEqual("QGC WPL 110", satirlar[0])
        self.assertEqual(len(self.satirlar), len(satirlar) - 1)
        for i, satir in enumerate(satirlar[1:]):
            sutunlar = satir.split("\t")
            with self.subTest(satir=i):
                self.assertEqual(12, len(sutunlar), satir)
                self.assertEqual(str(i), sutunlar[0])
        # yalnız ilk satır "akım" (current) işaretli
        self.assertEqual("1", satirlar[1].split("\t")[1])
        self.assertEqual("0", satirlar[2].split("\t")[1])


if __name__ == "__main__":
    unittest.main()
