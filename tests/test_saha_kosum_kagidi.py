"""T219 — SAHA KOSUM KAGIDI KAPISI: kagit yalan soylemesin.

NEDEN: SAHA_KOSUM_KAGIDI_20260910.md ekibin mimar olmadan kosacagi TEK sayfadir. Bir
komut satiri olu ise (betik yok, bayrak degismis) ekip sahada durur ve "olmadi"
der — D-421 sinifi kusur. Bu kapi belgeyi degil KOMUTU olcer:

  K1  8 bolum basligi (## 1. … ## 8.) tam ve sirali; her adimin sonunda
      OLCULDU / OLCULEMEDI kutusu var; kagit <= 120 satir (2 sayfa A4 esdegeri)
  K2  kagitta gecen her depo betigi/belgesi diskte VAR (results/ ciktilari haric)
  K3  her .py betigi `--help` ile 0 doner; .sh betikleri `bash -n` ve `--help` ile 0
      (vakumluluk: en az 5 farkli .py sinanir)
  K4  FDR/ACIK_KALEMLER.md kagida isaret ediyor; kagit sonuc klasorunu anıyor
  K5  kagittaki 6 Eylul akim iddiasi (0,44 A · 9,35 V · UYARI) kanit dosyasinda duruyor
  K6  scripts/tlog_akim_ozet.py: sentetik tlog'da PWM yuksek + akim dusuk pencereyi
      UYARI ile isaretler; akim mesaji yoksa OLCULEMEDI (cikis 2); dosya yoksa 2
  K7  scripts/kamera_fov_hesapla.py: bilinen geometri (1280 px, 640 px, 1 m, 2 m ->
      odak 1280 px, FOV 53,13 deg); gecersiz girdi cikis 2
  K8  scripts/mavlink_dogrula.py --baud: varsayilan 57600 = jetson_baslat PIXHAWK_BAUD
      = .param SERIAL2_BAUD 57; deger mavlink_connection'a ULASIYOR; 0 reddedilir
"""
from __future__ import annotations

import io
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
KAGIT = KOK / "SAHA_KOSUM_KAGIDI_20260910.md"
ACIK_KALEMLER = KOK / "FDR" / "ACIK_KALEMLER.md"
KANIT_DIZIN = KOK / "results" / "fdr_sprint_20260910" / "saha_kosum"
KANIT_AKIM = KANIT_DIZIN / "tlog_akim_ozet_20260906.txt"
AZAMI_SATIR = 120
#: Ham satir sayisi tek basina yaniltir (uzun satirlar sarar). Ikinci olcut: 2 A4
#: sayfa x ~60 basili satir x ~100 karakter (10 pt, dar kenar) = 12 000 karakter.
#: 10 Eylul olcumu: 62 ham satir, ~11 500 karakter (sarma 120'de ~130 basili satir).
AZAMI_KARAKTER = 12_000
ASGARI_PY_SAYISI = 5

for _y in (KOK / "scripts",):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

import kamera_fov_hesapla as kfh  # noqa: E402
import mavlink_dogrula as md  # noqa: E402
import tlog_akim_ozet as tao  # noqa: E402

BASLIK = re.compile(r"^## ([1-8])\. ", re.M)
KUTU = re.compile(r"\[ \] ÖLÇÜLDÜ\s+\[ \] ÖLÇÜLEMEDİ — neden:")
# results/ altindaki yollar CIKTIDIR (henuz yok); depo betik/belge yollari sinanir.
DEPO_YOLU = re.compile(
    r"(?<![\w/\\])((?:scripts|codes|jetson_paket|tests|config/pixhawk|FDR)/"
    r"[\w.\-/]+\.(?:py|sh|md|param))")
ORTAM = {**os.environ, "PYTHONIOENCODING": "utf-8"}


def _metin():
    return KAGIT.read_text(encoding="utf-8")


def _depo_yollari():
    return sorted(set(DEPO_YOLU.findall(_metin())))


class K1_Bicim(unittest.TestCase):
    def test_sekiz_baslik_sirali(self):
        self.assertEqual(BASLIK.findall(_metin()), [str(i) for i in range(1, 9)])

    def test_her_adimda_kutu(self):
        self.assertGreaterEqual(len(KUTU.findall(_metin())), 8)

    def test_iki_sayfa(self):
        satirlar = _metin().splitlines()
        n, k = len(satirlar), sum(len(s) for s in satirlar)
        self.assertLessEqual(n, AZAMI_SATIR, f"kagit {n} satir > {AZAMI_SATIR}")
        self.assertLessEqual(k, AZAMI_KARAKTER, f"kagit {k} karakter > {AZAMI_KARAKTER}")

    def test_kural_cumlesi(self):
        self.assertIn("ÖLÇÜLEMEDİ ≠ GEÇTİ", _metin())


class K2_K3_Komutlar(unittest.TestCase):
    def test_K2_yollar_diskte(self):
        yollar = _depo_yollari()
        self.assertTrue(yollar, "kagitta hic depo yolu bulunamadi (regex mi bozuk?)")
        eksik = [y for y in yollar if not (KOK / y).is_file()]
        self.assertEqual([], eksik)

    def test_K3_py_help_sifir(self):
        pyler = [y for y in _depo_yollari() if y.endswith(".py")]
        self.assertGreaterEqual(len(pyler), ASGARI_PY_SAYISI, pyler)
        for y in pyler:
            with self.subTest(betik=y):
                r = subprocess.run([sys.executable, "-B", str(KOK / y), "--help"],
                                   cwd=str(KOK), env=ORTAM, capture_output=True,
                                   text=True, timeout=120)
                self.assertEqual(0, r.returncode, r.stderr[-600:])
                self.assertIn("usage", r.stdout.lower())

    def test_K3_sh_bash_n_ve_help(self):
        shler = [y for y in _depo_yollari() if y.endswith(".sh")]
        self.assertTrue(shler, "kagitta .sh betigi yok — jetson_baslat.sh bekleniyordu")
        bash = shutil.which("bash")
        if bash is None:
            self.skipTest("bash yok (Git Bash/Linux gerekir)")
        for y in shler:
            with self.subTest(betik=y):
                r = subprocess.run([bash, "-n", str(KOK / y)], capture_output=True,
                                   text=True, timeout=60)
                self.assertEqual(0, r.returncode, r.stderr)
                r = subprocess.run([bash, str(KOK / y), "--help"], cwd=str(KOK),
                                   capture_output=True, text=True, timeout=60)
                self.assertEqual(0, r.returncode, r.stderr)
                self.assertIn("KULLANIM", r.stdout)


class K4_K5_Isaret_ve_Kanit(unittest.TestCase):
    def test_K4_acik_kalemler_isaret(self):
        self.assertIn(KAGIT.name, ACIK_KALEMLER.read_text(encoding="utf-8"))
        self.assertIn("results/fdr_sprint_20260910/saha_kosum", _metin())

    def test_K5_akim_iddiasi_kanitta(self):
        self.assertTrue(KANIT_AKIM.is_file(), KANIT_AKIM)
        k = KANIT_AKIM.read_text(encoding="utf-8")
        self.assertIn("akim tepe 0.44 A", k)
        self.assertIn("9.35", k)
        self.assertIn("UYARI", k)
        self.assertIn("PWM tepe 1949", k)
        m = _metin()
        for iddia in ("0,44 A", "9,35 V", "1949 PWM"):
            self.assertIn(iddia, m)


# ── K6: sentetik tlog ───────────────────────────────────────────────────────

#: Gercek tlog damgalari epoch'tur (2026-09-06 ~ 1,788e9 s); 0'dan baslatmak
#: `not t` sinifi hatayi gizlerdi — taban bilerek epoch.
EPOCH_TABAN_S = 1_788_000_000.0


def _sentetik_tlog(yol: Path, pencereler):
    """pencereler: [(baslangic_s, akim_cA, pwm)] — her pencerede 3 BATTERY_STATUS +
    3 SERVO_OUTPUT_RAW; tlog = 8 bayt big-endian us zaman damgasi + MAVLink paketi."""
    from pymavlink.dialects.v20 import ardupilotmega as m2
    mav = m2.MAVLink(None, srcSystem=1, srcComponent=1)
    with yol.open("wb") as f:
        for bas, akim, pwm in pencereler:
            for i in range(3):
                t = EPOCH_TABAN_S + bas + i * 10.0
                gerilim = [15000] + [65535] * 9
                if akim is not None:
                    b = mav.battery_status_encode(0, 0, 0, 0, gerilim, akim, 0, 0, 50)
                    f.write(struct.pack(">Q", int(t * 1e6)) + b.pack(mav))
                # time_usec uint32 (acilistan beri us) — pencereleme tlog BASLIGINDAKI
                # 8 baytlik epoch damgasini kullanir, bu alan degil.
                s = mav.servo_output_raw_encode(
                    int((bas + i * 10.0) * 1e6) % 2**32, 0,
                    1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000,
                    servo9_raw=pwm, servo10_raw=1000, servo11_raw=pwm, servo12_raw=1000)
                f.write(struct.pack(">Q", int((t + 0.5) * 1e6)) + s.pack(mav))


class K6_TlogAkimOzet(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.dizin = Path(self.d.name)

    def tearDown(self):
        self.d.cleanup()

    def _kos(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = tao.main(argv)
        return rc, out.getvalue(), err.getvalue()

    def test_supheli_pencere_uyari(self):
        tlog = self.dizin / "sentetik.tlog"
        # 0-59 s bosta; 60-119 s PWM 1949 ama 0,40 A (suphe); 120-179 s PWM 1949 ve 25 A
        _sentetik_tlog(tlog, [(0.0, 35, 1000), (60.0, 40, 1949), (120.0, 2500, 1949)])
        j = self.dizin / "ozet.json"
        rc, out, _ = self._kos([str(tlog), "--pencere", "60", "--json", str(j)])
        self.assertEqual(0, rc)
        self.assertIn("UYARI", out)
        p = json.loads(j.read_text(encoding="utf-8"))["pencereler"]
        self.assertEqual([3, 3, 3], [x["n_akim"] for x in p], "pencere kaymasi (t0 hatasi)")
        self.assertEqual([False, True, False], [x["supheli"] for x in p])
        self.assertAlmostEqual(25.0, p[2]["akim_maks_A"])
        self.assertEqual(1949, p[1]["pwm_maks"])

    def test_temiz_dosyada_uyari_yok(self):
        tlog = self.dizin / "temiz.tlog"
        _sentetik_tlog(tlog, [(0.0, 35, 1000), (60.0, 2500, 1949)])
        rc, out, _ = self._kos([str(tlog)])
        self.assertEqual(0, rc)
        self.assertNotIn("UYARI", out)
        self.assertIn("akim tepe 25.00 A", out)

    def test_akim_mesaji_yoksa_olculemedi(self):
        tlog = self.dizin / "akimsiz.tlog"
        _sentetik_tlog(tlog, [(0.0, None, 1500)])
        rc, out, err = self._kos([str(tlog)])
        self.assertEqual(tao.CIKIS_OLCULEMEDI, rc)
        self.assertIn("OLCULEMEDI", err)
        self.assertEqual("", out)

    def test_dosya_yoksa_olculemedi(self):
        rc, _, err = self._kos([str(self.dizin / "yok.tlog")])
        self.assertEqual(tao.CIKIS_OLCULEMEDI, rc)
        self.assertIn("OLCULEMEDI", err)


class K7_FovHesap(unittest.TestCase):
    def test_bilinen_geometri(self):
        s = kfh.hesapla(1280, 640, 1.0, 2.0, 720)
        self.assertAlmostEqual(1280.0, s["odak_px"])
        self.assertAlmostEqual(53.13, s["fov_yatay_derece"], places=2)
        self.assertAlmostEqual(31.42, s["fov_dusey_derece"], places=2)

    def test_gecersiz_girdi(self):
        with self.assertRaises(ValueError):
            kfh.odak_px(640, 0.0, 2.0)
        with self.assertRaises(ValueError):
            kfh.odak_px(640, 1.0, float("inf"))
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = kfh.main(["--genislik-px", "1280", "--isaret-px", "-5",
                           "--isaret-m", "1", "--mesafe-m", "2"])
        self.assertEqual(kfh.CIKIS_GECERSIZ, rc)
        self.assertIn("GECERSIZ", err.getvalue())

    def test_cikti_satiri(self):
        out = io.StringIO()
        with redirect_stdout(out):
            rc = kfh.main(["--genislik-px", "1280", "--isaret-px", "640",
                           "--isaret-m", "1.00", "--mesafe-m", "2.00"])
        self.assertEqual(0, rc)
        self.assertIn("ODAK=1280.0 px  FOV_yatay=53.13 derece", out.getvalue())


class K8_MavlinkDogrulaBaud(unittest.TestCase):
    def test_varsayilan_uc_kaynakla_ayni(self):
        self.assertEqual(57600, md.VARSAYILAN_BAUD)
        sh = (KOK / "jetson_paket" / "jetson_baslat.sh").read_text(encoding="utf-8")
        self.assertIn("PIXHAWK_BAUD:-57600", sh)
        param = (KOK / "config" / "pixhawk" / "arducopter_fda.param").read_text(encoding="utf-8")
        self.assertRegex(param, r"(?m)^SERIAL2_BAUD,57\s*$")

    def test_baud_baglantiya_ulasiyor(self):
        gorulen = {}

        def sahte(adres, **kw):
            gorulen.update(kw, adres=adres)
            raise OSError("sahte port yok")

        asil = md.mavutil.mavlink_connection
        md.mavutil.mavlink_connection = sahte
        try:
            r = md.dogrula("/dev/ttyTHS1", 1, 1.0, 1.0, 0.1, baud=57600)
        finally:
            md.mavutil.mavlink_connection = asil
        self.assertEqual(57600, gorulen.get("baud"))
        self.assertFalse(r["gecti"])
        self.assertIn("baglanti acilamadi", r["dusme_nedenleri"][0])

    def test_sifir_baud_reddedilir(self):
        err = io.StringIO()
        with redirect_stderr(err), self.assertRaises(SystemExit) as cm:
            md.main(["--mavlink", "udpin:127.0.0.1:0", "--baud", "0"])
        self.assertEqual(2, cm.exception.code)
        self.assertIn("--baud", err.getvalue())


if __name__ == "__main__":
    unittest.main()
