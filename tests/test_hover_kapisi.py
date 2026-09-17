"""scripts/hover_kapisi.py — saf hesap birimleri (pymavlink ve log dosyasi gerekmez).

Sahte mesajlarla: esik altinda TAMAM, VibeZ ya da motor farki esigi asinca BASARISIZ,
esik tam sinirda TAMAM (<=), DataFlash (VIBE/RCOU) ve tlog (VIBRATION/SERVO_OUTPUT_RAW)
alan adlari, 0.0 zaman damgasinin atlanmamasi ve on kayitli esiklerin degismemesi.
"""
import importlib.util
import sys
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("hover_kapisi", KOK / "scripts" / "hover_kapisi.py")
hk = importlib.util.module_from_spec(_spec)
sys.modules["hover_kapisi"] = hk
_spec.loader.exec_module(hk)


class _Msg:
    def __init__(self, tip, t, **alanlar):
        self._tip = tip
        self._timestamp = t
        for k, v in alanlar.items():
            setattr(self, k, v)

    def get_type(self):
        return self._tip


def _tlog(t, vz, pwm):
    return [_Msg("VIBRATION", t, vibration_z=vz),
            _Msg("SERVO_OUTPUT_RAW", t, **{f"servo{9 + i}_raw": p for i, p in enumerate(pwm)})]


def _bin(t, vz, pwm):
    return [_Msg("VIBE", t, VibeZ=vz),
            _Msg("RCOU", t, **{f"C{9 + i}": p for i, p in enumerate(pwm)})]


def _hukum(mesajlar):
    satirlar = hk.pencereleri_hesapla(mesajlar, 2.0, hk.VARSAYILAN_KANALLAR)
    return hk.hukum(satirlar)


class HoverKapisiTest(unittest.TestCase):
    def test_on_kayitli_esikler_degismedi(self):
        self.assertEqual(hk.VIBEZ_ESIK, 16.0)
        self.assertEqual(hk.MOTOR_FARK_ESIK_US, 60.0)

    def test_esik_altinda_tamam(self):
        m = []
        for i in range(10):
            m += _tlog(float(i), 8.0, [1500, 1510, 1520, 1530])
        tamam, vz, mf = _hukum(m)
        self.assertTrue(tamam)
        self.assertEqual((vz, mf), (8.0, 30))

    def test_sinirda_tamam(self):
        tamam, vz, mf = _hukum(_tlog(0.0, 16.0, [1500, 1560, 1530, 1530]))
        self.assertTrue(tamam)
        self.assertEqual((vz, mf), (16.0, 60))

    def test_motor_farki_buyuyunce_basarisiz(self):
        m = []
        for i, fark in enumerate([16, 40, 120, 520]):
            m += _tlog(float(i * 3), 10.0, [1500, 1500 + fark, 1500, 1500])
        tamam, _, mf = _hukum(m)
        self.assertFalse(tamam)
        self.assertEqual(mf, 520)

    def test_vibez_asinca_basarisiz(self):
        tamam, vz, _ = _hukum(_tlog(0.0, 16.5, [1500, 1500, 1500, 1500]))
        self.assertFalse(tamam)
        self.assertEqual(vz, 16.5)

    def test_dataflash_alanlari(self):
        tamam, vz, mf = _hukum(_bin(0.0, 30.0, [1400, 1500, 1450, 1450]))
        self.assertFalse(tamam)
        self.assertEqual((vz, mf), (30.0, 100))

    def test_olcum_yoksa_tamam_denmez(self):
        tamam, vz, mf = _hukum([_Msg("VIBRATION", 0.0, vibration_z=5.0)])
        self.assertFalse(tamam)
        self.assertIsNone(mf)

    def test_sifir_zaman_damgasi_atlanmaz(self):
        satirlar = hk.pencereleri_hesapla(_tlog(0.0, 5.0, [1500, 1520, 1500, 1500]), 2.0,
                                          hk.VARSAYILAN_KANALLAR)
        self.assertEqual(len(satirlar), 1)
        self.assertEqual(satirlar[0]["n_vibe"], 1)

    def test_eksik_dosya_olculemedi(self):
        kod = hk.tek_dosya(Path("/yok/boyle_bir_log.bin"), 2.0, hk.VARSAYILAN_KANALLAR, 3, None)
        self.assertEqual(kod, hk.CIKIS_OLCULEMEDI)


if __name__ == "__main__":
    unittest.main()
