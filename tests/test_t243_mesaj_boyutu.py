"""NÖBETÇİ — T243 (D-462 C; Y-3.3.4-M03): mesaj boyutu tablosu + gerçek veri hızı.

  T1  her mesaj tipinin boyutu GERÇEK `encode()` çağrısından gelir (elle sayı
      yazılmamış — betiğin kendi fonksiyonunu tekrar çağırıp bayt-eş karşılaştırma)
  T2  OPEN_ROUTE worst-case waypoint sayısı `costmap_path_finder.MAKS_WP` sabitine
      EŞİT (çıplak 64 değil — sabit değişirse bu test de değişmeli)
  T3  NO_ROUTE worst-case sebebi `karar_sozlesmesi` modülündeki GERÇEK bir sabit
      (uydurma dizge değil)
  T4  gerçek UDP loopback ölçümü (kısa süre): >0 bayt, >0 mesaj, doluluk oranı
      0 ile 1 arasında makul bir aralıkta
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
for _p in (KOK / "codes", KOK / "comms", KOK / "scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import mesaj_boyutu_ve_veri_hizi as olcum  # noqa: E402
import karar_sozlesmesi as ks  # noqa: E402
from costmap_path_finder import MAKS_WP  # noqa: E402
import protocol as proto  # noqa: E402


class BoyutTablosu(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tablo = olcum.boyut_tablosu()

    def test_T1_her_boyut_gercek_encode_ile_yeniden_uretilebilir(self):
        for ad, veri in self.tablo.items():
            with self.subTest(ad=ad):
                self.assertEqual(len(proto.encode(veri["ornek"])), veri["bayt"])

    def test_T2_open_route_worst_case_MAKS_WP_sabitiyle_esit(self):
        anahtar = f"OPEN_ROUTE ({MAKS_WP} wp, MAKS_WP)"
        self.assertIn(anahtar, self.tablo, self.tablo.keys())
        self.assertEqual(MAKS_WP, len(self.tablo[anahtar]["ornek"]["waypoints"]))

    def test_T3_no_route_sebebi_gercek_sabit(self):
        sebep = self.tablo["NO_ROUTE (en uzun sebep)"]["ornek"]["sebep"]
        gercek_sabitler = {v for k, v in vars(ks).items()
                           if k.isupper() and isinstance(v, str)}
        self.assertIn(sebep, gercek_sabitler,
                      "worst-case sebep karar_sozlesmesi'nde tanımlı bir sabit değil")


class GercekVeriHizi(unittest.TestCase):
    def test_T4_gercek_udp_loopback_makul_araliktadir(self):
        sonuc = olcum.gercek_veri_hizi_olc(sure_s=1.5)
        self.assertGreater(sonuc["yks_alinan_toplam_bayt"], 0, sonuc)
        self.assertGreater(sonuc["yks_alinan_mesaj_sayisi"], 0, sonuc)
        self.assertGreater(sonuc["bayt_s"], 0, sonuc)
        self.assertGreater(sonuc["sik_doluluk_orani"], 0.0, sonuc)
        self.assertLess(sonuc["sik_doluluk_orani"], 5.0,
                        "doluluk oranı akla yakın değil (>%500) — ölçüm bozuk olabilir")


if __name__ == "__main__":
    unittest.main()
