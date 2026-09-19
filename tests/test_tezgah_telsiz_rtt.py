"""TEZGAH `scripts/tezgah/telsiz_rtt_param.py` — Jetson'suz telsiz RTT ölçümü.

Gerçek donanım yok: MAVLink bağlantısı SAHTE. Sınanan: yüzdelik hesabı, zaman aşımı
sayımı, geç cevap sayımı, cevapsız turda ölçümün çökmemesi.
"""
import sys
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "scripts" / "tezgah"))
import telsiz_rtt_param as t  # noqa: E402


class Yuzdelik(unittest.TestCase):
    def test_bilinen_dizi(self):
        d = [10, 20, 30, 40, 50]
        self.assertEqual(t.yuzdelik(d, 0.0), 10)
        self.assertEqual(t.yuzdelik(d, 1.0), 50)
        self.assertEqual(t.yuzdelik(d, 0.5), 30)

    def test_bos_dizi_none(self):
        self.assertIsNone(t.yuzdelik([], 0.95))

    def test_tek_eleman(self):
        self.assertEqual(t.yuzdelik([7], 0.95), 7)


class _SahteMesaj:
    def __init__(self, ad):
        self.param_id = ad


class _SahteBaglanti:
    """recv_match: `cevap_deseni`ndeki her öğe bir prob için — True cevap, False sessizlik."""
    def __init__(self, cevap_deseni):
        self.desen = list(cevap_deseni)
        self.target_system = 1
        self.target_component = 1
        self.istek = 0
        self.mav = self

    def param_request_read_send(self, *a, **k):
        self.istek += 1

    def recv_match(self, type=None, blocking=False, timeout=0):
        i = self.istek - 1
        if 0 <= i < len(self.desen) and self.desen[i]:
            self.desen[i] = False          # bir kez cevapla
            return _SahteMesaj(t.VARSAYILAN_PARAM)
        return None


class OlcumMantigi(unittest.TestCase):
    def test_hepsi_cevapli(self):
        b = _SahteBaglanti([True] * 5)
        rtt, ta, gec = t.olc(b, t.VARSAYILAN_PARAM, 5, 0.0, 0.5, log=lambda *x: None)
        self.assertEqual(len(rtt), 5)
        self.assertEqual(ta, 0)
        self.assertEqual(b.istek, 5)

    def test_cevapsizlar_zaman_asimi_sayilir(self):
        b = _SahteBaglanti([True, False, True, False])
        rtt, ta, gec = t.olc(b, t.VARSAYILAN_PARAM, 4, 0.0, 0.2, log=lambda *x: None)
        self.assertEqual(len(rtt), 2)
        self.assertEqual(ta, 2)

    def test_hic_cevap_yoksa_cokmez(self):
        b = _SahteBaglanti([False] * 3)
        rtt, ta, gec = t.olc(b, t.VARSAYILAN_PARAM, 3, 0.0, 0.1, log=lambda *x: None)
        self.assertEqual(rtt, [])
        self.assertEqual(ta, 3)

    def test_yanlis_parametre_adi_cevap_sayilmaz(self):
        class Yanlis(_SahteBaglanti):
            def recv_match(self, **k):
                i = self.istek - 1
                if 0 <= i < len(self.desen) and self.desen[i]:
                    self.desen[i] = False
                    return _SahteMesaj("BASKA_PARAM")
                return None
        b = Yanlis([True, True])
        rtt, ta, gec = t.olc(b, t.VARSAYILAN_PARAM, 2, 0.0, 0.1, log=lambda *x: None)
        self.assertEqual(rtt, [])
        self.assertEqual(ta, 2)


if __name__ == "__main__":
    unittest.main()
