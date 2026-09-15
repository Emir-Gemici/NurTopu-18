"""T276 KAPISI — scripts/ucus_bin_analiz.py: ArduPilot .bin analiz aracinin saf mantigi.

NEDEN: 12-15 Eylul ucus loglari mimarin denetlenmemis scratch betigiyle tarandi (D-482
denetim borcu). Uretim araci her sayiyi LOGDAN cikarir; bu kapi o cikarimin kurallarini
sentetik veriyle ve iki KUCUK gercek logla kilitler:

  K1  hucre sayisi: ilk BAT gerilimi → 3S/4S (3,2-4,3 V/hucre; birden cok adayda 3,8 V'a yakin)
  K2  arm penceresi bolme: EV ARMED/DISARMED; acik pencere log sonunda kapanir; ARMED'siz
      DISARMED yalniz RCOU logun basinda aktifse "armli basladi" sayilir (LAND'de yerde
      yazilan sahte DISARMED 281 s'lik hayalet pencere uretmisti — ilk kosuda yakalandi)
  K3  EV yoksa ARM.ArmState; RCOU > 1100 araliklari (≥ 1 s) EV/ARM pencereleriyle ortusmuyorsa
      "RCOU" kaynakli pencere olarak EKLENIR (15 Eyl 11-14-33: ARMED olayi yok, 43,5 s ucus var —
      yalniz EV'ye bakan ilk tarama kacirmisti)
  K4  motorlu sure (CTUN.ThO > 0,15) ve tur: 0 → arm_yalniz, < 5 s → kisa_sicrama, ≥ 5 → ucus
  K5  aski maskesi: irtifa > 1 m, |dikey hiz| < 0,5 m/s (CTUN.Alt turevi), gaz 0,25-0,75 —
      tirmanis/inis ve yer orneklerini DISLAR
  K6  IMU FFT: 25 Hz'de 5 Hz sinus → tepe 5 Hz, genlik ~2 m/s²; Nyquist raporlanir
  K7  MODE.Rsn / kip / ERR eslemeleri (1 RC, 4 PIL_FS, 19 CRASH; bilinmeyen → RSN_n)
  K8  kullanici beyani etiketi: acik liste > kopya adindan tarih > yok (None)
  K9  sha256 kopya gruplama: ayni bayt → KOPYA_OF, verilis sirasi esasi belirler
  K10 gercek log (12 Eylul 17-42-38, 1,2 MB): 3S, 1 pencere, kisa_sicrama, ThH 0,35, sha on eki
      ilk taramayla (tarama_ham.json) birebir; 16-45-10 (0,6 MB): arm penceresi YOK
  K11 --help → 0 (T232 kurali: kagida yazilan komut olu olmasin)
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

KOK = Path(__file__).resolve().parents[1]
if str(KOK / "scripts") not in sys.path:
    sys.path.insert(0, str(KOK / "scripts"))

import ucus_bin_analiz as U  # noqa: E402

PY = sys.executable
LOG_KISA = KOK / "results/ucus_20260912/2026-09-12 17-42-38.bin"
LOG_BOS = KOK / "results/ucus_20260912/2026-09-12 16-45-10.bin"


class HucreSayisi(unittest.TestCase):
    def test_3s_ve_4s(self):
        for v, n in ((11.05, 3), (12.6, 3), (10.76, 3), (12.11, 3), (16.69, 4), (16.12, 4), (15.0, 4),
                     (14.0, 4), (22.2, 6)):
            self.assertEqual(U.hucre_sayisi(v)[0], n, f"V={v}")

    def test_belirsiz_ve_gecersiz(self):
        n, adaylar = U.hucre_sayisi(16.69)
        self.assertEqual(n, 4); self.assertIn(5, adaylar)          # 5S x 3,34 V de aralikta → "coklu"
        self.assertEqual(U.hucre_sayisi(11.05)[1], [3])            # tek aday
        for v in (None, 0.0, -1.0, float("nan"), 1.0):
            self.assertEqual(U.hucre_sayisi(v), (None, []), f"V={v}")


class ArmPencereleri(unittest.TestCase):
    def test_ev_bolme_ve_acik_pencere(self):
        ev = [(1.0, 10), (5.0, 11), (7.0, 10), (12.0, 11), (20.0, 10)]
        p = U.arm_pencereleri(ev, [], None, None, 0.0, 25.0)
        self.assertEqual(p, [(1.0, 5.0, "EV"), (7.0, 12.0, "EV"), (20.0, 25.0, "EV")])

    def test_sahte_disarmed_hayalet_pencere_uretmez(self):
        # ilk kosu kusuru: 291 s'de yerde LAND'deyken DISARMED → 9,5-291 hayalet pencere
        ev = [(291.0, 11), (297.4, 10), (340.9, 11)]
        rc_t = np.array([9.5, 100.0, 290.0]); rc_m = np.array([1007.0, 1007.0, 1007.0])
        p = U.arm_pencereleri(ev, [], rc_t, rc_m, 9.5, 424.0)
        self.assertEqual(p, [(297.4, 340.9, "EV")])
        # ama RCOU logun basinda aktifse (log armli basladi) DISARMED pencereyi kapatir
        rc_m2 = np.array([1500.0, 1500.0, 1007.0])
        p2 = U.arm_pencereleri([(50.0, 11)], [], rc_t, rc_m2, 9.5, 424.0)
        self.assertEqual(p2[0], (9.5, 50.0, "EV"))

    def test_arm_ve_rcou_yedekleri(self):
        p = U.arm_pencereleri([], [(3.0, 1), (9.0, 0), (11.0, 1)], None, None, 0.0, 15.0)
        self.assertEqual(p, [(3.0, 9.0, "ARM"), (11.0, 15.0, "ARM")])
        t = np.arange(0, 10, 0.5); m = np.where((t >= 2) & (t < 6), 1400.0, 1000.0)
        p = U.arm_pencereleri([], [], t, m, 0.0, 10.0)
        self.assertEqual(len(p), 1); self.assertEqual(p[0][2], "RCOU")
        self.assertAlmostEqual(p[0][0], 2.0); self.assertAlmostEqual(p[0][1], 6.0)
        self.assertEqual(U.arm_pencereleri([], [], np.zeros(0), np.zeros(0), 0.0, 1.0), [])

    def test_armed_olayi_eksik_ucus_rcou_ile_tamamlanir(self):
        # 15 Eyl 11-14-33: EV'de yalniz DISARMED (146,7) var, ARMED yok; RCOU 99,8-146,8 aktif.
        # EV'li baska bir pencere de olsun: ikisi de bulunmali, EV penceresinin ici tekrar edilmemeli.
        t = np.arange(0, 200, 0.1)
        m = np.where(((t >= 20) & (t < 40)) | ((t >= 99.8) & (t < 146.8)), 1500.0, 1000.0)
        ev = [(19.0, 10), (41.0, 11), (146.7, 11)]
        p = U.arm_pencereleri(ev, [], t, m, 0.0, 200.0)
        self.assertEqual(len(p), 2)
        self.assertEqual(p[0], (19.0, 41.0, "EV"))
        self.assertEqual(p[1][2], "RCOU"); self.assertAlmostEqual(p[1][0], 99.8, places=1)
        self.assertAlmostEqual(p[1][1], 146.8, places=1)
        # 1 s'den kisa RCOU parazitleri pencere olmaz; < 2 s bosluklar birlesir
        m2 = np.where(((t >= 50) & (t < 50.5)) | ((t >= 60) & (t < 63)) | ((t >= 64) & (t < 67)), 1500.0, 1000.0)
        p2 = U.arm_pencereleri([], [], t, m2, 0.0, 200.0)
        self.assertEqual(len(p2), 1); self.assertAlmostEqual(p2[0][0], 60.0, places=1)
        self.assertAlmostEqual(p2[0][1], 67.0, places=1)


class MotorluVeTur(unittest.TestCase):
    def test_motorlu_sure_ve_siniflar(self):
        t = np.arange(0, 20, 0.1)
        tho = np.where((t >= 3) & (t < 5), 0.5, 0.0)          # 2 s motorlu
        s, a, b = U.motorlu_sure(t, tho)
        self.assertAlmostEqual(s, 2.0, places=1); self.assertAlmostEqual(a, 3.0); self.assertAlmostEqual(b, 4.9)
        self.assertEqual(U.ucus_turu(s), "kisa_sicrama")
        tho8 = np.where((t >= 3) & (t < 11), 0.5, 0.0)
        self.assertEqual(U.ucus_turu(U.motorlu_sure(t, tho8)[0]), "ucus")
        self.assertEqual(U.motorlu_sure(t, np.zeros_like(t)), (0.0, None, None))
        self.assertEqual(U.ucus_turu(0.0), "arm_yalniz")
        self.assertEqual(U.ucus_turu(4.99), "kisa_sicrama"); self.assertEqual(U.ucus_turu(5.0), "ucus")
        # esik altindaki gaz (0,15) motorlu sayilmaz
        self.assertEqual(U.motorlu_sure(t, np.full_like(t, 0.15))[0], 0.0)


class AskiMaskesi(unittest.TestCase):
    def _profil(self):
        t = np.arange(0, 30, 0.1)
        alt = np.piecewise(t, [t < 5, (t >= 5) & (t < 10), (t >= 10) & (t < 20), t >= 20],
                           [0.0, lambda x: (x - 5) * 0.8, 4.0, lambda x: np.maximum(4.0 - (x - 20) * 0.8, 0.0)])
        tho = np.piecewise(t, [t < 5, (t >= 5) & (t < 10), (t >= 10) & (t < 20), t >= 20],
                           [0.0, 0.7, 0.5, 0.3])
        return t, alt, tho

    def test_tirmanis_inis_yer_dislanir(self):
        t, alt, tho = self._profil()
        m = U.aski_maskesi(t, alt, tho)
        self.assertFalse(m[t < 5].any(), "yerde aski olmaz")
        self.assertFalse(m[(t > 6) & (t < 9)].any(), "tirmanista (0,8 m/s) aski olmaz")
        self.assertFalse(m[(t > 21) & (t < 24)].any(), "iniste aski olmaz")
        self.assertTrue(m[(t > 11) & (t < 19)].all(), "sabit 4 m + gaz 0,5 → aski")
        self.assertGreaterEqual(int(m.sum()), 80); self.assertLessEqual(int(m.sum()), 105)

    def test_gaz_ve_irtifa_siniri(self):
        t = np.arange(0, 10, 0.1)
        self.assertFalse(U.aski_maskesi(t, np.full_like(t, 0.8), np.full_like(t, 0.5)).any(), "irtifa 0,8 m < 1")
        self.assertFalse(U.aski_maskesi(t, np.full_like(t, 3.0), np.full_like(t, 0.8)).any(), "gaz 0,8 > 0,75")
        self.assertFalse(U.aski_maskesi(t, np.full_like(t, 3.0), np.full_like(t, 0.2)).any(), "gaz 0,2 < 0,25")
        self.assertTrue(U.aski_maskesi(t, np.full_like(t, 3.0), np.full_like(t, 0.5)).all())
        self.assertEqual(U.en_uzun_kosu([False, True, True, False, True, True, True, False]), (4, 6))
        self.assertIsNone(U.en_uzun_kosu([False, False]))


class ImuFFT(unittest.TestCase):
    def test_sinus_tepesi_ve_nyquist(self):
        fs = 25.0; t = np.arange(0, 16, 1 / fs)
        z = -9.81 + 2.0 * np.sin(2 * np.pi * 5.0 * t) + 0.3 * np.sin(2 * np.pi * 2.0 * t)
        f = U.imu_fft(t, z)
        self.assertIsNotNone(f)
        self.assertAlmostEqual(f["fs_hz"], 25.0, places=1); self.assertAlmostEqual(f["nyquist_hz"], 12.5, places=1)
        tepe = f["tepeler"][0]
        self.assertAlmostEqual(tepe["f_hz"], 5.0, delta=0.15)
        self.assertAlmostEqual(tepe["genlik_ms2"], 2.0, delta=0.3)
        self.assertAlmostEqual(f["tepeler"][1]["f_hz"], 2.0, delta=0.15)
        self.assertIsNone(U.imu_fft(t[:10], z[:10]), "64 ornek alti FFT yok")


class Eslemeler(unittest.TestCase):
    def test_rsn_kip_err(self):
        self.assertEqual(U._rsn(1), "RC"); self.assertEqual(U._rsn(4), "PIL_FS"); self.assertEqual(U._rsn(19), "CRASH")
        self.assertEqual(U._rsn(5), "GCS_FS"); self.assertEqual(U._rsn(6), "EKF_FS"); self.assertEqual(U._rsn(10), "FENCE")
        self.assertEqual(U._rsn(99), "RSN_99")
        self.assertEqual(U._kip(9), "LAND"); self.assertEqual(U._kip(5), "LOIT"); self.assertEqual(U._kip(4), "GUID")
        self.assertEqual(U._kip(77), "KIP_77"); self.assertEqual(U._kip(5, "Loiter"), "Loiter")
        self.assertEqual(U._err_ad(6, 1), ("FS_PIL", "TETIKLENDI")); self.assertEqual(U._err_ad(8, 0), ("FS_GCS", "temizlendi"))
        self.assertEqual(U._err_ad(11, 2), ("GPS", "GLITCH")); self.assertEqual(U._err_ad(12, 1)[1], "CRASH")
        self.assertEqual(U.EV_AD[62], "EKF_YAW_RESET")   # devrilme betigindeki E-STOP etiketi yanlisti
        self.assertEqual(U._f32(0.47259318828582764), 0.472593)

    def test_temiz_json(self):
        o = U._temiz({"a": np.float64(1.5), "b": np.int64(3), "c": float("nan"), "d": [np.bool_(True)]})
        self.assertEqual(o, {"a": 1.5, "b": 3, "c": None, "d": [True]})
        json.dumps(o)


class Beyan(unittest.TestCase):
    def test_etiketler(self):
        self.assertEqual(U.beyan_etiketi(["2026-09-13 09-26-58"])["etiket"], "B")
        self.assertEqual(U.beyan_etiketi(["62 13.09.2026 09-38-02"])["etiket"], "B")
        self.assertEqual(U.beyan_etiketi(["2026-09-12 17-42-38"])["etiket"], "A")      # tarih kurali
        self.assertEqual(U.beyan_etiketi(["2026-09-14 19-43-06"])["etiket"], "C")
        self.assertEqual(U.beyan_etiketi(["2026-09-15 11-18-16"])["etiket"], "D")
        self.assertEqual(U.beyan_etiketi(["1980-01-06 08-07-20"])["etiket"], "A")      # acik liste (GPS'siz)
        # GPS'siz ad + MP kopya adi → kopya adindan tarih (13.09) → A
        b = U.beyan_etiketi(["1980-01-06 07-59-23", "60 13.09.2026 09-06-12"])
        self.assertEqual(b["etiket"], "A"); self.assertIn("tarih kurali", b["dayanak"])
        b = U.beyan_etiketi(["1980-01-12 15-45-52"])
        self.assertIsNone(b["etiket"]); self.assertEqual(b["kaynak"], "kullanici_beyani")
        self.assertEqual(U.mp_no(["1980-01-06 07-59-23", "60 13.09.2026 09-06-12"]), 60)
        self.assertIsNone(U.mp_no(["2026-09-15 11-18-16"]))
        for k in U.KONFIG.values():
            self.assertIn(k["pil"], ("3S", "4S"))


class KopyaGrupla(unittest.TestCase):
    def test_sha_ile_kopya(self):
        with tempfile.TemporaryDirectory() as d:
            a = Path(d) / "a.bin"; b = Path(d) / "b.bin"; c = Path(d) / "c.bin"
            a.write_bytes(b"\x01" * 5000); b.write_bytes(b"\x01" * 5000); c.write_bytes(b"\x02" * 5000)
            esas, kopya, sha = U.kopya_grupla([a, b, c])
            self.assertEqual(esas, [a, c]); self.assertEqual(kopya, [(b, a)])
            self.assertEqual(sha[a], sha[b]); self.assertNotEqual(sha[a], sha[c]); self.assertEqual(len(sha[a]), 64)
            esas2, kopya2, _ = U.kopya_grupla([b, a, c])       # sira esasi belirler
            self.assertEqual(esas2, [b, c]); self.assertEqual(kopya2, [(a, b)])


@unittest.skipUnless(LOG_KISA.is_file() and LOG_BOS.is_file(), "gercek loglar yok")
class GercekKucukLog(unittest.TestCase):
    def test_kisa_sicrama_logu(self):
        L = U.log_analiz(LOG_KISA)
        self.assertTrue(L["sha256"].startswith("91c94f15e473"))   # tarama_ham.json ile ayni
        self.assertEqual(L["hucre"]["n"], 3); self.assertAlmostEqual(L["hucre"]["V_ilk"], 11.05, places=1)
        self.assertEqual(L["kullanici_beyani"]["etiket"], "A"); self.assertTrue(L["kullanici_beyani"]["hucre_uyum"])
        self.assertEqual(L["arm_penceresi_kaynak"], "EV"); self.assertEqual(L["arm_pencere_n"], 1)
        u = L["ucuslar"][0]
        self.assertEqual(u["pencere_kaynak"], "EV")
        self.assertEqual(u["tur"], "kisa_sicrama"); self.assertGreater(u["motorlu_s"], 3.5); self.assertLess(u["motorlu_s"], 5.0)
        self.assertIsNone(u["aski"]); self.assertEqual(u["aski_n"], 0)
        self.assertAlmostEqual(L["parm"]["MOT_THST_HOVER"], 0.35, places=3)
        self.assertEqual(L["parm"]["INS_HNTCH_ENABLE"], 0.0); self.assertEqual(L["parm"]["INS_GYRO_FILTER"], 20.0)
        self.assertEqual(L["ozet"], {**L["ozet"], "ucus_n": 0, "kisa_sicrama_n": 1, "arm_yalniz_n": 0})
        self.assertEqual(u["vibe"]["Z"]["maks"], 49.9)              # ilk tarama: vibeZ 49.9
        self.assertTrue(L["imu"]["var"]); self.assertFalse(L["imu"]["acc_gyr_hizli"])
        self.assertAlmostEqual(L["imu"]["fs_hz"], 25.0, delta=0.5)
        self.assertEqual(u["kip_arm"], "STAB")
        json.dumps(U._temiz(L))

    def test_ucussuz_log(self):
        L = U.log_analiz(LOG_BOS)
        self.assertTrue(L["sha256"].startswith("5b33f4552041"))
        self.assertEqual(L["arm_pencere_n"], 0); self.assertEqual(L["ucuslar"], [])
        self.assertEqual(L["hucre"]["n"], 3); self.assertEqual(L["ozet"]["toplam_motorlu_s"], 0.0)


class Cli(unittest.TestCase):
    def test_help_sifir(self):
        r = subprocess.run([PY, str(KOK / "scripts/ucus_bin_analiz.py"), "--help"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        self.assertEqual(r.returncode, 0, r.stderr); self.assertIn("kullanici_beyani", r.stdout)
        r = subprocess.run([PY, str(KOK / "scripts/ucus_bin_analiz.py")], capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        self.assertEqual(r.returncode, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
