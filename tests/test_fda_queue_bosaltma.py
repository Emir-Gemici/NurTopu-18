import sys
from pathlib import Path
import unittest

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "comms"))

from fda_mavlink import FdaPlanYukleyici, GELEN_KUTU_BOSALTMA_TAVANI


class _SurekliMav:
    def recv_match(self, blocking=False, timeout=0):
        return object()


class _SessizMav:
    def recv_match(self, blocking=False, timeout=0):
        return None


class FdaKutuBosaltmaTest(unittest.TestCase):
    def test_surekli_telemetri_sinirda_durur_plan_redde_donusmez(self):
        yukleyici = FdaPlanYukleyici(_SurekliMav(), "plan.json")
        sayi = yukleyici._gelen_kutusunu_bosalt()
        self.assertEqual(GELEN_KUTU_BOSALTMA_TAVANI, sayi)
        self.assertTrue(yukleyici.kutu_bosaltma_tavani_asildi)

    def test_sessiz_kuyruk_hemen_biter(self):
        yukleyici = FdaPlanYukleyici(_SessizMav(), "plan.json")
        self.assertEqual(0, yukleyici._gelen_kutusunu_bosalt())
        self.assertFalse(yukleyici.kutu_bosaltma_tavani_asildi)


if __name__ == "__main__":
    unittest.main()
