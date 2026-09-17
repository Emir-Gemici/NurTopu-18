"""scripts/hover_kapisi.py — saf hesap birimleri (pymavlink ve log dosyasi gerekmez).

Sahte mesajlarla: esik altinda TAMAM, VibeZ ya da motor farki esigi asinca BASARISIZ,
esik tam sinirda TAMAM (<=), DataFlash (VIBE/RCOU + ARM/CTUN) ve tlog (VIBRATION/
SERVO_OUTPUT_RAW + HEARTBEAT/GLOBAL_POSITION_INT) alan adlari, 0.0 zaman damgasinin
atlanmamasi, on kayitli esiklerin degismemesi.
ONARIM-01: yalniz HOVER ornekleri sayilir — ucussuz log TAMAM ALAMAZ (eski fail-open),
kalkis/inis/yerde ornekleri dislanir, GCS heartbeat'i arm durumunu belirlemez.
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


def _tlog_durum(t, armed=True, alt_m=1.0, vz_ms=0.0, tip=2):
    return [_Msg("HEARTBEAT", t, type=tip, base_mode=(128 if armed else 0)),
            _Msg("GLOBAL_POSITION_INT", t, relative_alt=int(alt_m * 1000), vz=int(vz_ms * 100))]


def _bin_durum(t, armed=True, alt_m=1.0, crt_ms=0.0):
    return [_Msg("ARM", t, ArmState=1 if armed else 0),
            _Msg("CTUN", t, Alt=alt_m, CRt=crt_ms * 100)]


def _tlog(t, vz, pwm, **durum):
    return _tlog_durum(t, **durum) + [
        _Msg("VIBRATION", t, vibration_z=vz),
        _Msg("SERVO_OUTPUT_RAW", t, **{f"servo{9 + i}_raw": p for i, p in enumerate(pwm)})]


def _bin(t, vz, pwm, **durum):
    return _bin_durum(t, **durum) + [
        _Msg("VIBE", t, VibeZ=vz),
        _Msg("RCOU", t, **{f"C{9 + i}": p for i, p in enumerate(pwm)})]


def _hukum(mesajlar, sayac=None):
    satirlar = hk.pencereleri_hesapla(mesajlar, 2.0, hk.VARSAYILAN_KANALLAR, sayac=sayac)
    return hk.hukum(satirlar)


class HoverKapisiTest(unittest.TestCase):
    def test_on_kayitli_esikler_degismedi(self):
        self.assertEqual(hk.VIBEZ_ESIK, 16.0)
        self.assertEqual(hk.MOTOR_FARK_ESIK_US, 60.0)
        self.assertEqual((hk.HOVER_ASGARI_IRTIFA_M, hk.HOVER_AZAMI_DIKEY_HIZ_MS), (0.3, 0.3))

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
        tamam, vz, mf = _hukum(_tlog_durum(0.0) + [_Msg("VIBRATION", 0.0, vibration_z=5.0)])
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


class HoverDilimi(unittest.TestCase):
    """ONARIM-01 — 17 Eylul'deki gercek .bin'lerde yer loglari TAMAM almisti."""

    def test_ucussuz_log_TAMAM_ALAMAZ(self):
        # yerde, disarm, motor 1000, VibeZ ~0: eski surum TAMAM diyordu
        m = []
        for i in range(20):
            m += _bin(float(i), 0.04, [1000, 1000, 1000, 1000], armed=False, alt_m=0.0)
        sayac = {}
        tamam, vz, mf = _hukum(m, sayac)
        self.assertFalse(tamam)
        self.assertEqual((vz, mf), (None, None))
        self.assertEqual(sayac, {"hover_disi_vibe": 20, "hover_disi_pwm": 20})

    def test_durum_mesaji_yoksa_hover_sayilmaz(self):
        m = [_Msg("VIBE", 0.0, VibeZ=3.0),
             _Msg("RCOU", 0.0, **{f"C{9 + i}": 1500 for i in range(4)})]
        tamam, vz, mf = _hukum(m)
        self.assertFalse(tamam)
        self.assertEqual((vz, mf), (None, None))

    def test_kalkis_ve_inis_gecicileri_dislanir(self):
        m = []
        m += _bin(0.0, 25.0, [1100, 1500, 1100, 1300], alt_m=0.1, crt_ms=1.5)   # kalkis
        m += _bin(1.0, 20.0, [1400, 1700, 1400, 1500], alt_m=0.8, crt_ms=1.0)   # tirmanis
        for i in range(5):
            m += _bin(2.0 + i, 6.0, [1600, 1630, 1610, 1620], alt_m=1.0, crt_ms=0.05)  # hover
        m += _bin(8.0, 30.0, [1200, 1500, 1250, 1300], alt_m=0.5, crt_ms=-0.9)  # inis
        sayac = {}
        tamam, vz, mf = _hukum(m, sayac)
        self.assertTrue(tamam)
        self.assertEqual((vz, mf), (6.0, 30))
        self.assertEqual(sayac, {"hover_disi_vibe": 3, "hover_disi_pwm": 3})

    def test_hover_icindeki_bozulma_yakalanir(self):
        m = []
        for i, fark in enumerate([16, 60, 200, 520]):
            m += _bin(float(i), 8.0, [1600, 1600 + fark, 1600, 1600], alt_m=0.7, crt_ms=0.0)
        tamam, _, mf = _hukum(m)
        self.assertFalse(tamam)
        self.assertEqual(mf, 520)

    def test_disarm_sonrasi_ornekler_dislanir(self):
        m = _bin(0.0, 5.0, [1600, 1610, 1605, 1600])
        m += _bin(1.0, 40.0, [1000, 1400, 1000, 1000], armed=False, alt_m=0.5)
        tamam, vz, mf = _hukum(m)
        self.assertTrue(tamam)
        self.assertEqual((vz, mf), (5.0, 10))

    def test_gcs_heartbeat_arm_durumunu_ezmez(self):
        m = _tlog_durum(0.0) + [_Msg("HEARTBEAT", 0.0, type=hk.MAV_TYPE_GCS, base_mode=0),
                                _Msg("VIBRATION", 0.0, vibration_z=4.0),
                                _Msg("SERVO_OUTPUT_RAW", 0.0,
                                     **{f"servo{9 + i}_raw": 1500 for i in range(4)})]
        tamam, vz, mf = _hukum(m)
        self.assertTrue(tamam)
        self.assertEqual((vz, mf), (4.0, 0))


if __name__ == "__main__":
    unittest.main()
