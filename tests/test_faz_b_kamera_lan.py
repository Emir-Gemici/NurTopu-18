"""NEDEN: Kamera köprüsünün YKİ LAN yayını açık beyan olmadan dışarı
açılmamalı; açıldığında /durum dinleme jokerini değil istemcinin gerçek Host
ucunu ilan etmelidir. Video SiK hattına eklenmez.
"""
import json
import os
import shutil
import subprocess
import sys
import threading
import unittest
import urllib.request
from pathlib import Path


KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "scripts"))
import kamera_koprusu as kk  # noqa: E402

BETIK = KOK / "jetson_paket" / "jetson_baslat.sh"


def _bash_bul():
    if os.name == "nt":
        aday = Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Git" / "bin" / "bash.exe"
        if aday.is_file():
            return str(aday)
    return shutil.which("bash")


def _kuru(**ek):
    bash = _bash_bul()
    if not bash:
        raise unittest.SkipTest("bash yok — jetson_baslat davranis kapisi kosulamadi")
    env = dict(os.environ)
    for ad in (
            "KIP", "YKS_IP", "IKA_IP", "FOV", "ODAK", "SENARYO", "KAMERA",
            "KAMERA_PYTHON", "KAMERA_KOPRU_BIND", "KAMERA_KOPRU_ARGS",
            "UB_REFERANS", "PIXHAWK_SERI", "PIXHAWK_BAUD", "SIK_SERI",
            "SIK_BAUD", "SYSID", "NAVITAS_KOK", "PYTHON3", "ENV_DOSYA",
            "SYSTEMD_DIZIN", "LOG_DIZIN", "SERVIS_KULLANICI"):
        env.pop(ad, None)
    env.update({
        "KIP": "udp",
        "YKS_IP": "10.42.0.10",
        "IKA_IP": "10.42.0.11",
        "FOV": "60",
        "KAMERA": "http://127.0.0.1:8080/video",
        "PYTHONIOENCODING": "utf-8",
    })
    env.update(ek)
    return subprocess.run(
        [bash, str(BETIK).replace("\\", "/"), "--kuru"], env=env,
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=45)


def _birim_satiri(cikti, ad="navitas-kamera-koprusu.service"):
    onek = ad + ": "
    for satir in cikti.splitlines():
        if satir.startswith(onek):
            return satir[len(onek):]
    return None


class KameraKoprusuHostTesti(unittest.TestCase):
    def test_varsayilan_bind_loopback(self):
        args = kk._parser().parse_args([])
        self.assertEqual(args.host, "127.0.0.1")
        self.assertEqual(kk.YEREL_HOST, "127.0.0.1")

    def test_durum_urlsi_istegin_gercek_hostunu_ilan_eder(self):
        # Kaynak yok olabilir; /durum bilerek her zaman 200 ve sunucu ayaktadır.
        sunucu, uretici = kk.kopru_kur(
            "kesinlikle_yok_kamera.avi", port=0, host="127.0.0.1",
            log=lambda *_a, **_k: None)
        iplik = threading.Thread(target=sunucu.serve_forever, daemon=True)
        iplik.start()
        port = sunucu.server_address[1]
        try:
            istek = urllib.request.Request(
                "http://127.0.0.1:{}/durum".format(port),
                headers={"Host": "10.42.0.2:{}".format(port)})
            acici = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with acici.open(istek, timeout=2.0) as yanit:
                veri = json.loads(yanit.read().decode("utf-8"))
            self.assertEqual(veri["bind_host"], "127.0.0.1")
            self.assertEqual(veri["istek_host"], "10.42.0.2:{}".format(port))
            self.assertEqual(
                veri["video_url"], "http://10.42.0.2:{}/video".format(port))
            self.assertEqual(
                veri["kare_url"], "http://10.42.0.2:{}/kare.jpg".format(port))
            self.assertEqual(
                veri["durum_url"], "http://10.42.0.2:{}/durum".format(port))
        finally:
            kk.kopru_kapat(sunucu, uretici)
            iplik.join(2.0)

    def test_host_basligi_kontrol_karakteri_ve_yol_tasiyamaz(self):
        for kotu in ("", "10.0.0.1/x", "a b", "k@x", "x?y", "x:abc"):
            with self.subTest(host=kotu):
                self.assertIsNone(kk._http_yetkisi_dogrula(kotu))
        self.assertEqual(kk._http_yetkisi_dogrula("10.42.0.2:8080"),
                         "10.42.0.2:8080")


class JetsonBaslatKameraLanTesti(unittest.TestCase):
    def test_varsayilan_disariya_kapali(self):
        sonuc = _kuru()
        # Geliştirici PC'de cihaz/paket eksikleri 3 normaldir; beyan ve komut yine
        # tam basılır. Bu kapı exit 0 UYDURMAZ.
        self.assertIn(sonuc.returncode, (0, 3), sonuc.stderr)
        self.assertIn("KAMERA_KOPRU_BIND=127.0.0.1", sonuc.stdout)
        komut = _birim_satiri(sonuc.stdout)
        self.assertIsNotNone(komut, sonuc.stdout)
        self.assertNotIn(" --host ", " " + komut + " ")

    def test_explicit_bind_lan_komuta_ve_envye_ulasir(self):
        sonuc = _kuru(KAMERA_KOPRU_BIND="0.0.0.0")
        self.assertIn(sonuc.returncode, (0, 3), sonuc.stderr)
        self.assertIn("KAMERA_KOPRU_BIND=0.0.0.0", sonuc.stdout)
        self.assertIn("KAMERA_KOPRU_ARGS=--host 0.0.0.0", sonuc.stdout)
        komut = _birim_satiri(sonuc.stdout)
        self.assertIn(" --host 0.0.0.0", komut)
        self.assertIn("KAMERA LAN'A ACIK", sonuc.stdout)
        self.assertIn("video SiK'e GIRMEZ", sonuc.stdout)

        ozel = _kuru(KAMERA_KOPRU_BIND="10.42.0.2", KAMERA_KOPRU_ARGS="--fps 5")
        self.assertIn(ozel.returncode, (0, 3), ozel.stderr)
        self.assertIn("--host 10.42.0.2 --fps 5", _birim_satiri(ozel.stdout))

    def test_bind_tek_sahipli_ve_yerel_ipv4(self):
        ham = _kuru(KAMERA_KOPRU_ARGS="--host 0.0.0.0")
        self.assertEqual(ham.returncode, 1)
        self.assertIn("KAMERA_KOPRU_BIND kullan", ham.stderr)

        for kotu in ("8.8.8.8", "kamera.local", "192.168.1.999", "::",
                     "10.42.0.2."):
            with self.subTest(bind=kotu):
                sonuc = _kuru(KAMERA_KOPRU_BIND=kotu)
                self.assertEqual(sonuc.returncode, 1)
                self.assertIn("yalniz yerel IPv4", sonuc.stderr)

        sekme = _kuru(KAMERA_KOPRU_ARGS="--host\t0.0.0.0")
        self.assertEqual(sekme.returncode, 1)
        self.assertIn("KAMERA_KOPRU_BIND kullan", sekme.stderr)

    def test_bind_kopru_yokken_sessizce_yutulmaz(self):
        sonuc = _kuru(KAMERA="/dev/video0", KAMERA_KOPRU_BIND="0.0.0.0")
        self.assertEqual(sonuc.returncode, 1)
        self.assertIn("yalniz KAMERA=http://127.0.0.1", sonuc.stderr)


if __name__ == "__main__":
    unittest.main()
