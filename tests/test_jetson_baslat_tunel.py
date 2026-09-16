"""K6 — `jetson_baslat.sh` KIP=tunel (CONTRACTS §7.6 · results/tunel_20260916/ON_KAYIT.md).

NEDEN: tek RFD900A Pixhawk TELEM1'de; Jetson TELEM2'de. KIP=tunel'de hub seri port
yerine MAVLink TUNNEL ucunu acar ve MAVProxy'ye ek `--out` + SONDA `--streamrate -1`
verilir (TELEM2 57600'da 8 Hz akis hatti doyururdu, HESAP). Kilitlenenler:
  * --kuru KIP=tunel hazir makinede exit 0; cogullayicida ` --out udp:127.0.0.1:14553 `
    ve SON `--streamrate` = -1 (optparse son degeri alir; `_arg_degeri` ILK degeri
    okur, bu yuzden ayri "son gorulen" ikizi); hub `--tunel` var, `--port` / `/dev/tty` yok;
  * udp/sik: 14553 YOK, tek `--streamrate` (= 8, D-406 B), hub'da `--tunel` YOK;
  * ham ExecStart `$COGULLAYICI_EK_ARGS` / `$HUB_TASIYICI_ARGS` (suslu parantezsiz —
    systemd `${VAR}`'i TEK arguman yapar); literal `--streamrate 8` yerinde;
  * fail-closed: tunel + /dev/ttyACM* ya da PIXHAWK_BAUD != 57600 -> cikis 1;
    birim metni sozlesmeden saparsa (ek --out yok / hub'a --port) -> cikis 1;
  * [DOGRULA] satirlari basilir ve [VAR]/[YOK] sayimina GIRMEZ;
  * kurulu comms/mavlink_tunel.py ve scripts/sik_rf_olc.py icin [VAR]/[YOK];
    --kur mavlink_tunel.py yoksa DURUR;
  * --kur / --kapi shim'le: hub enable+restart alir.
Yontem `tests/test_faz_b_jetson_baslat.py` ile AYNI (gercek bash + shim).
"""
from __future__ import annotations

import re
import shutil
import sys
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
for _y in (KOK / "tests", KOK / "comms", KOK / "codes"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

import mavlink_tunel as mt  # noqa: E402
import test_faz_b_jetson_baslat as jb  # noqa: E402
from karar_sozlesmesi import MAVLINK_KONUM_ASGARI_HZ  # noqa: E402

COGULLAYICI_UC = f"udp:{mt.TUNEL_HAVA_UC}"


def _son_arg_degeri(komut, bayrak):
    """optparse ikizi: bayragin SON gorulen degeri (yoksa None)."""
    parcalar = komut.split()
    deger = None
    for i, p in enumerate(parcalar[:-1]):
        if p == bayrak:
            deger = parcalar[i + 1]
    return deger


def _tunel_makinesi(**kw):
    m = jb._AnaMakine(**kw)
    (m.kok / "comms").mkdir(exist_ok=True)
    (m.kok / "scripts").mkdir(exist_ok=True)
    shutil.copyfile(jb.KOD / "mavlink_tunel.py", m.kok / "comms" / "mavlink_tunel.py")
    shutil.copyfile(jb.KOD / "sik_rf_olc.py", m.kok / "scripts" / "sik_rf_olc.py")
    (m.d / "dev" / "ttyTHS1").write_bytes(b"")
    return m


def _tunel_env(m, **ek):
    return m.env(KIP="tunel", FOV="78", PIXHAWK_SERI=jb._msys(m.d / "dev" / "ttyTHS1"), **ek)


class JetsonBaslatTunelKuru(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = _tunel_makinesi()
        cls.kod, cls.out, cls.err = jb._kos(jb.BETIK, _tunel_env(cls.m))
        cls.b = jb._bolumler(cls.out)
        cls.kod_v, cls.out_v, cls.err_v = jb._kos(jb.BETIK, {"KIP": "tunel", "FOV": "78"})
        cls.b_v = jb._bolumler(cls.out_v)

    @classmethod
    def tearDownClass(cls):
        cls.m.temizle()

    def test_T1_hazir_makinede_exit_0_ve_birimler(self):
        self.assertEqual(0, self.kod, f"stdout:\n{self.out}\nstderr:\n{self.err}")
        self.assertEqual(set(jb.TUM_BIRIMLER), set(self.b["birimler"]))
        self.assertEqual(0, jb._yok_sayisi(self.b), self.out)
        self.assertTrue(self.b["sonuc"].startswith("KURU SONUC: tamam"), self.b["sonuc"])

    def test_T2_cogullayici_ek_out_ve_SON_streamrate_eksi_1(self):
        k = self.b["birimler"][jb.COGULLAYICI]
        self.assertIn(f" --out {COGULLAYICI_UC} ", f" {k} ")
        self.assertEqual("-1", _son_arg_degeri(k, "--streamrate"), k)
        self.assertEqual(-1, int(self._sh_sabiti("TUNEL_STREAMRATE")))
        self.assertEqual(2, k.split().count("--streamrate"))
        self.assertEqual(str(int(2 * MAVLINK_KONUM_ASGARI_HZ)), jb._arg_degeri(k, "--streamrate"),
                         "literal 8 yerinde kalir (udp/sik kilidi 527-530)")
        for uc in jb.MAV_UCLAR:
            self.assertIn(f"--out {uc}", k)
        self.assertEqual(f"--out {COGULLAYICI_UC} --streamrate {mt_streamrate()}",
                         self.b["env"]["COGULLAYICI_EK_ARGS"])

    def test_T3_hub_tunel_ucu_seri_port_YOK_tuketiciler_sik_ile_ayni(self):
        hub = self.b["birimler"][jb.SERI_HUB]
        self.assertEqual(mt.TUNEL_HAVA_UC, jb._arg_degeri(hub, "--tunel"))
        self.assertEqual(mt.KIMLIK_HAVA, jb._arg_degeri(hub, "--tunel-kimlik"))
        self.assertNotIn("--port", hub.split())
        self.assertNotIn("--baud", hub.split())
        self.assertIsNone(jb.SERI_CIHAZ_KALIBI.search(hub), hub)
        self.assertEqual("127.0.0.1:5100", jb._arg_degeri(hub, "--bind"))
        self.assertEqual("127.0.0.1:5007", jb._arg_degeri(hub, "--tuketici"))
        self.assertEqual("127.0.0.1:5100", jb._arg_degeri(self.b["birimler"][jb.RPI], "--yks-hedef"))
        self.assertEqual("127.0.0.1:5100", jb._arg_degeri(self.b["birimler"][jb.INIS], "--yks"))
        self.assertEqual("127.0.0.1:5007", jb._arg_degeri(self.b["birimler"][jb.KOMUT], "--bind"))
        for ad in jb.TUKETICILER:
            self.assertIsNone(jb.SERI_CIHAZ_KALIBI.search(self.b["birimler"][ad]))

    def test_T4_PIXHAWK_SERI_varsayilani_tunelde_ttyTHS1(self):
        self.assertEqual("/dev/ttyTHS1", self.b_v["env"]["PIXHAWK_SERI"])
        self.assertIn("--master=/dev/ttyTHS1", self.b_v["birimler"][jb.COGULLAYICI])
        self.assertEqual(str(mt_baud()), self.b_v["env"]["PIXHAWK_BAUD"])

    def test_T5_DOGRULA_satirlari_var_ve_YOK_sayimina_girmez(self):
        dogrula = [s for s in self.out.splitlines() if s.startswith("[DOGRULA]")]
        metin = "\n".join(dogrula)
        for parca in ("SR2_POSITION >= 8", "mavfwd", "/dev/ttyTHS*", "/dev/ttyTCU*",
                      "rate != -1", "BRD_SER2_RTSCTS=0", "SYSID_MYGCS=255",
                      "SERIAL2_PROTOCOL=2", "bit10=0", "3 tel"):
            self.assertIn(parca, metin)
        self.assertEqual(str(int(2 * MAVLINK_KONUM_ASGARI_HZ)),
                         self._sh_sabiti("TUNEL_SR2_POSITION_ASGARI"))
        self.assertEqual(0, self.kod, "DOGRULA satirlari cikisi 3 yapmamali")
        self.assertFalse(any(s.startswith("[DOGRULA]") for s in self.b["paket"] + self.b["makine"]))

    def test_T6_kurulu_tunel_dosyalari_VAR_eksikse_YOK_ve_exit_3(self):
        self.assertTrue(any(s.startswith("[VAR] kurulu") and s.endswith("comms/mavlink_tunel.py")
                            for s in self.b["makine"]), self.b["makine"])
        self.assertTrue(any(s.startswith("[VAR] kurulu") and s.endswith("scripts/sik_rf_olc.py")
                            for s in self.b["makine"]), self.b["makine"])
        self.assertTrue(any(s.startswith("[VAR] mavlink_tunel.py") for s in self.b["paket"]))
        m = _tunel_makinesi()
        try:
            (m.kok / "comms" / "mavlink_tunel.py").unlink()
            kod, out, err = jb._kos(jb.BETIK, _tunel_env(m))
            self.assertEqual(3, kod, out + err)
            self.assertTrue(any(s.startswith("[YOK] kurulu") and "comms/mavlink_tunel.py" in s
                                for s in jb._bolumler(out)["makine"]), out)
        finally:
            m.temizle()

    @staticmethod
    def _sh_sabiti(ad):
        m = re.search(rf'^{ad}="?([^"\s]+)"?', jb.BETIK.read_text(encoding="utf-8"), re.M)
        return m.group(1) if m else None


def mt_streamrate():
    return JetsonBaslatTunelKuru._sh_sabiti("TUNEL_STREAMRATE")


def mt_baud():
    return JetsonBaslatTunelKuru._sh_sabiti("TUNEL_TELEM2_BAUD")


class JetsonBaslatUdpSikTunelsiz(unittest.TestCase):
    """K6: udp/sik'te tunel izi YOK (mevcut testler zaten degismeden gecer)."""

    @classmethod
    def setUpClass(cls):
        cls.m = jb._AnaMakine()
        cls.udp = jb._bolumler(jb._kos(jb.BETIK, cls.m.env(KIP="udp", **jb.BEYAN_TAM))[1])
        cls.sik = jb._bolumler(jb._kos(jb.BETIK, cls.m.env(KIP="sik", FOV="78"))[1])

    @classmethod
    def tearDownClass(cls):
        cls.m.temizle()

    def test_T7_udp_sik_14553_yok_tek_streamrate_8_hub_tunelsiz(self):
        for ad, b in (("udp", self.udp), ("sik", self.sik)):
            with self.subTest(kip=ad):
                k = b["birimler"][jb.COGULLAYICI]
                self.assertNotIn(mt.TUNEL_HAVA_UC, k)
                self.assertEqual(1, k.split().count("--streamrate"))
                self.assertEqual(str(int(2 * MAVLINK_KONUM_ASGARI_HZ)), _son_arg_degeri(k, "--streamrate"))
                self.assertEqual("", b["env"]["COGULLAYICI_EK_ARGS"])
                self.assertFalse(any(s.startswith("[DOGRULA]") for s in b["paket"] + b["makine"]))
        hub = self.sik["birimler"][jb.SERI_HUB]
        self.assertNotIn("--tunel", hub.split())
        self.assertEqual(f"--port {self.sik['env']['SIK_SERI']} --baud {self.sik['env']['SIK_BAUD']}",
                         self.sik["env"]["HUB_TASIYICI_ARGS"])
        self.assertEqual("", self.udp["env"]["HUB_TASIYICI_ARGS"])


class JetsonBaslatTunelBirimMetni(unittest.TestCase):
    def test_T8_ham_ExecStart_dolar_VAR_bicimi_suslu_yok(self):
        cog = jb._exec_start(jb.COGULLAYICI)
        hub = jb._exec_start(jb.SERI_HUB)
        self.assertTrue(cog.endswith(" $COGULLAYICI_EK_ARGS"), cog)
        self.assertNotIn("${COGULLAYICI_EK_ARGS}", cog)
        self.assertIn(" $HUB_TASIYICI_ARGS ", hub)
        self.assertNotIn("${HUB_TASIYICI_ARGS}", hub)
        self.assertIn("--streamrate 8", cog, "literal 8 udp/sik icin yerinde")
        self.assertEqual(3, cog.count("udp:127.0.0.1:"), "ham metinde yeni udp:127.0.0.1: belirteci YOK")
        self.assertNotIn("${SIK_SERI}", hub)
        self.assertNotIn("--port", hub)
        ham = (jb.BIRIM_DIZIN / f"{jb.COGULLAYICI}.service").read_text(encoding="utf-8")
        self.assertIn("§7.6", ham, "NEDEN yorumu sozlesmeye atif yapar")


class JetsonBaslatTunelFailClosed(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = _tunel_makinesi()

    @classmethod
    def tearDownClass(cls):
        cls.m.temizle()

    def test_T9_ACM_ve_yanlis_baud_cikis_1(self):
        for ek, parca in (({"PIXHAWK_SERI": "/dev/ttyACM0"}, "PIXHAWK_SERI='/dev/ttyACM0'"),
                          ({"PIXHAWK_BAUD": "115200"}, "PIXHAWK_BAUD='115200'")):
            with self.subTest(ek=ek):
                env = _tunel_env(self.m)
                env.update(ek)
                kod, out, err = jb._kos(jb.BETIK, env)
                self.assertEqual(1, kod, out + err)
                self.assertIn("HATA:", err)
                self.assertIn(parca, err)
                self.assertNotIn("## birimler", out, "HICBIR SEY basilmadan durmali")

    def test_T10_birim_metni_sozlesmeden_saparsa_cikis_1(self):
        durumlar = (
            (jb.COGULLAYICI, " $COGULLAYICI_EK_ARGS", "", "--out udp:127.0.0.1:14553' yok"),
            (jb.COGULLAYICI, " $COGULLAYICI_EK_ARGS", " $COGULLAYICI_EK_ARGS --streamrate 8",
             "--streamrate -1 degil"),
            (jb.SERI_HUB, "$HUB_TASIYICI_ARGS", "$HUB_TASIYICI_ARGS --port /dev/ttyTHS2",
             "seri port veriliyor"),
        )
        for birim, eski, yeni, parca in durumlar:
            with self.subTest(birim=birim, yeni=yeni):
                m = _tunel_makinesi(lf_paket=True)
                try:
                    yol = m.paket / "systemd" / f"{birim}.service"
                    satirlar = yol.read_text(encoding="utf-8").splitlines()
                    i = next(j for j, s in enumerate(satirlar) if s.startswith("ExecStart="))
                    self.assertIn(eski, satirlar[i])
                    satirlar[i] = satirlar[i].replace(eski, yeni, 1)
                    yol.write_text("\n".join(satirlar) + "\n", encoding="utf-8", newline="\n")
                    kod, out, err = jb._kos(m.betik, _tunel_env(m))
                    self.assertEqual(1, kod, out + err)
                    self.assertIn(parca, err)
                finally:
                    m.temizle()


class JetsonBaslatTunelKurulum(unittest.TestCase):
    KULLANICI = "jetsonkullanici"

    def _systemctl(self, m):
        return [(k[1], k[2:]) for k in (s.split() for s in m.shim_satirlari()) if k[0] == "systemctl"]

    def test_T11_kur_hub_enable_restart_env_ek_args_kurulu_dosya_VAR(self):
        m = _tunel_makinesi(sbin=True, kullanici=self.KULLANICI)
        try:
            e = _tunel_env(m)
            kod, out, err = jb._kos(jb.BETIK, e, "--kur")
            self.assertEqual(0, kod, f"stdout:\n{out}\nstderr:\n{err}")
            sc = dict(self._systemctl(m))
            self.assertIn(f"{jb.SERI_HUB}.service", sc["enable"])
            self.assertIn(f"{jb.SERI_HUB}.service", sc["restart"])
            self.assertNotIn(("disable", ["--now", f"{jb.SERI_HUB}.service"]), self._systemctl(m))
            env = m.env_dosya.read_text(encoding="utf-8")
            self.assertIn(f"COGULLAYICI_EK_ARGS=--out {COGULLAYICI_UC} --streamrate -1\n", env)
            self.assertIn(f"HUB_TASIYICI_ARGS=--tunel {mt.TUNEL_HAVA_UC} --tunel-kimlik hava\n", env)
            self.assertIn("[VAR] kurulu", out)
            self.assertIn("comms/mavlink_tunel.py", out)
        finally:
            m.temizle()

    def test_T12_kur_mavlink_tunel_yoksa_DURUR_hicbir_birim_yazilmaz(self):
        m = _tunel_makinesi(sbin=True, kullanici=self.KULLANICI)
        try:
            (m.kok / "comms" / "mavlink_tunel.py").unlink()
            kod, out, err = jb._kos(jb.BETIK, _tunel_env(m), "--kur")
            self.assertEqual(1, kod, out + err)
            self.assertIn("mavlink_tunel.py yok", err)
            self.assertEqual([], list(m.systemd.iterdir()))
            self.assertNotIn("restart", [a for a, _ in self._systemctl(m)])
        finally:
            m.temizle()

    def test_T13_kapi_tunelde_hub_tuketicilerden_once_kalkar(self):
        m = _tunel_makinesi(sbin=True, kullanici=self.KULLANICI)
        try:
            kod, out, err = jb._kos(jb.BETIK, _tunel_env(m, FAKE_SURE="0.2"), "--kapi", timeout=180)
            self.assertEqual(0, kod, f"stdout:\n{out}\nstderr:\n{err}")
            restartlar = [b for a, bs in self._systemctl(m) if a == "restart" for b in bs]
            self.assertIn(f"{jb.SERI_HUB}.service", restartlar)
            self.assertLess(restartlar.index(f"{jb.SERI_HUB}.service"),
                            restartlar.index(f"{jb.RPI}.service"))
        finally:
            m.temizle()


if __name__ == "__main__":
    unittest.main()
