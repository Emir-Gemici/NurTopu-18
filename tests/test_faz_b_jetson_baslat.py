"""FAZ B · GOREV C — JETSON ACILIS KAPILARI (jetson_paket/jetson_baslat.sh + systemd/).

NEDEN: sartname §6.2 thazirlik — Jetson TEK komutla kalkmali; hands-off sonrasi
olen surec KENDI kalkmali (Restart=always). CONTRACTS §7.4 (D-403): seri Pixhawk
tek sahipli; uclar (14550/14551/14552) ve --sysid/--mav-sysid pinleri BELGEDE
degil KODDA olmali. Bu test o kodu (bash betigi + birim dosyalari) GERCEKTEN
kosarak (`bash jetson_baslat.sh --kuru`, Git Bash/Linux bash) ve CONTRACTS.md
metniyle karsilastirarak kilitler. Mock yok; systemd/seri cihaz gerektiren
kipler (--kur/--kapi/--dogrudan) burada KOSULMAZ — yalniz --kuru ve dosya kilitleri.

Kapilar (adlari ne kilitledigini soyler):
  K1 --kuru KIP=udp exit 0; 14550/14551/14552, --mav-sysid, --sysid, mavproxy satiri;
     hicbir tuketici /dev/tty ile --mavlink almaz, --serial/--telsiz-seri yok
  K2 --kuru KIP=sik: seri-hub satiri; tuketiciler 127.0.0.1:5100'e; /dev/ttyUSB0 yalniz hub'da
  K3 her .service: Restart=always, RestartSec, StartLimitIntervalSec=0, EnvironmentFile,
     After=network.target, tuketiciler After/Wants cogullayici; ExecStart .py kod/ altinda MEVCUT
     (depoda hic olmayan betik icin GORUNUR skip — "YAPILAMADI", sessiz gecis degil)
  K4 ExecStart --mavlink uclari == CONTRACTS.md §7.4 tablosu (metin kilidi)
  K5 --kuru komutlari == birimlerin ExecStart'i (bagimsiz Python yerine-koyma ile)
  K6 pinler KODDAN: SYSID varsayilani = iha_komut_alici.VARSAYILAN_HEDEF_SYSID; 5007 =
     VARSAYILAN_BIND; KANIT_TIMEOUT = karar_sozlesmesi.SARTNAME_IHA_GOREV_SURESI_S
  K7 beyan eksik -> --kuru cikis 3 + [EKSIK]; KIP taninmiyor -> cikis 1 (fail-closed)
  K8 CRLF kopyasi (Windows autocrlf / USB) ayni env+birim ciktisini verir, exit 0
  K9 --kuru paket denetimi DOGRU SOYLER ([VAR]/[YOK] dosya sistemiyle ayni); kilavuz --kuru'yu once der
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
for _y in (KOK / "comms", KOK / "codes"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

import iha_komut_alici  # noqa: E402
from karar_sozlesmesi import SARTNAME_IHA_GOREV_SURESI_S  # noqa: E402

PAKET = KOK / "jetson_paket"
BETIK = PAKET / "jetson_baslat.sh"
BIRIM_DIZIN = PAKET / "systemd"
KOD = PAKET / "kod"
CONTRACTS = KOK / "CONTRACTS.md"
KILAVUZ = PAKET / "JETSON_BASLAT.md"

COGULLAYICI = "navitas-cogullayici"
SERI_HUB = "navitas-seri-hub"
RPI = "navitas-rpi-inference"
INIS = "navitas-iha-inis-yayinci"
KOMUT = "navitas-iha-komut-alici"
TUKETICILER = (RPI, INIS, KOMUT)
TUM_BIRIMLER = (COGULLAYICI, SERI_HUB) + TUKETICILER

# Betigin ExecStart dosya adi -> CONTRACTS §7.4 tablo satiri (`rpi_inference --mavlink`)
PY_ADI = {RPI: "rpi_inference", INIS: "iha_inis_yayinci", KOMUT: "iha_komut_alici"}

BEYAN_TAM = {"YKS_IP": "10.0.0.1", "IKA_IP": "10.0.0.2", "FOV": "78"}
# Betigin okudugu beyan anahtarlari: gelistirici ortamindan SIZMASIN
BEYAN_ANAHTARLARI = ("KIP", "YKS_IP", "IKA_IP", "FOV", "ODAK", "SENARYO", "KAMERA",
                     "UB_REFERANS", "SYSID", "PIXHAWK_SERI", "PIXHAWK_BAUD", "SIK_SERI",
                     "SIK_BAUD", "KANIT_TIMEOUT", "NAVITAS_KOK", "PYTHON3", "LOG_DIZIN",
                     "ENV_DOSYA", "NAVITAS_PAKET_DIZIN", "NAVITAS_CR_KOPYA")
SERI_CIHAZ_KALIBI = re.compile(r"/dev/tty")


def _bash_bul():
    """Git Bash (Windows) ya da sistem bash'i; WSL saplamasi (System32) ELENIR."""
    if os.name == "nt":
        for pf in (os.environ.get("ProgramFiles", r"C:\Program Files"),
                   os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")):
            for alt in ("Git/bin/bash.exe", "Git/usr/bin/bash.exe"):
                aday = Path(pf) / alt
                if aday.is_file():
                    return str(aday)
    yol = shutil.which("bash")
    if yol and "system32" not in yol.lower():
        return yol
    return None


def _posix(p):
    return str(p).replace("\\", "/")


def _kos(betik, ek_env, *args):
    """`bash <betik> --kuru ...` GERCEK kosum; (cikis, stdout, stderr)."""
    bash = _bash_bul()
    if bash is None:
        raise unittest.SkipTest("bash yok (Git Bash / Linux bash gerekli) — YAPILAMADI")
    env = dict(os.environ)
    for k in BEYAN_ANAHTARLARI:
        env.pop(k, None)
    env.update(ek_env)
    p = subprocess.run([bash, _posix(betik), "--kuru", *args], env=env,
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=60)
    return p.returncode, p.stdout, p.stderr


def _bolumler(cikti):
    """--kuru ciktisini bolumlere ayir: env (dict), birimler (dict), paket (list), beyan (list)."""
    b = {"env": {}, "birimler": {}, "paket": [], "beyan": [], "sonuc": None}
    bolum = None
    for satir in cikti.splitlines():
        if satir.startswith("## "):
            if "(yazilacak icerik)" in satir:
                bolum = "env"
            elif satir.startswith("## birimler"):
                bolum = "birimler"
            elif satir.startswith("## paket denetimi"):
                bolum = "paket"
            elif satir.startswith("## beyan denetimi"):
                bolum = "beyan"
            else:
                bolum = None
            continue
        if satir.startswith("KURU SONUC:"):
            b["sonuc"] = satir
            continue
        if bolum == "env" and "=" in satir:
            k, v = satir.split("=", 1)
            b["env"][k] = v
        elif bolum == "birimler":
            m = re.match(r"^(navitas-[\w-]+)\.service: (.*)$", satir)
            if m:
                b["birimler"][m.group(1)] = m.group(2)
        elif bolum == "paket":
            b["paket"].append(satir)
        elif bolum == "beyan":
            b["beyan"].append(satir)
    return b


def _birim_oku(ad):
    """Birim dosyasini anahtar -> [deger, ...] olarak oku (yorum/bolum satirlari atlanir)."""
    metin = (BIRIM_DIZIN / f"{ad}.service").read_text(encoding="utf-8")
    alanlar = {}
    for satir in metin.splitlines():
        satir = satir.rstrip("\r")
        if not satir or satir.startswith("#") or satir.startswith("["):
            continue
        k, _, v = satir.partition("=")
        alanlar.setdefault(k.strip(), []).append(v.strip())
    return alanlar


def _exec_start(ad):
    alanlar = _birim_oku(ad)
    if "ExecStart" not in alanlar:
        raise AssertionError(f"{ad}: ExecStart yok")
    return alanlar["ExecStart"][0]


def _navitas_py(komut):
    """Komut satirindaki ilk /home/navitas/navitas/... .py yolu (yoksa None)."""
    for t in komut.split():
        if t.startswith("/home/navitas/navitas/") and t.endswith(".py"):
            return t
    return None


def _arg_degeri(komut, bayrak):
    parcalar = komut.split()
    if bayrak not in parcalar:
        return None
    i = parcalar.index(bayrak)
    return parcalar[i + 1] if i + 1 < len(parcalar) else None


def _sozlesme_uclari():
    """CONTRACTS.md §7.4 tablosu: {'rpi_inference': 14550, ...} — metin kilidi."""
    m = CONTRACTS.read_text(encoding="utf-8")
    bas = m.index("### 7.4")
    son = m.find("\n## ", bas)
    bolum = m[bas:son if son > 0 else None]
    eslesme = re.findall(
        r"\|\s*`(\w+) --mavlink`\s*\|\s*`udp:127\.0\.0\.1:(\d+)`\s*\|", bolum)
    return {ad: int(port) for ad, port in eslesme}


class JetsonBaslatKuruUdp(unittest.TestCase):
    """K1/K5/K6/K9 — `bash jetson_baslat.sh --kuru` KIP=udp, GERCEK kosum."""

    @classmethod
    def setUpClass(cls):
        cls.kod, cls.out, cls.err = _kos(BETIK, {"KIP": "udp", **BEYAN_TAM})
        cls.b = _bolumler(cls.out)

    def test_K1_kuru_exit_0_ve_hicbir_sey_baslatilmadi(self):
        self.assertEqual(self.kod, 0, f"stdout:\n{self.out}\nstderr:\n{self.err}")
        self.assertIn("HICBIR SEY BASLATILMADI", self.out)
        self.assertIn("[TAM] beyanlar tam", self.out)
        self.assertEqual(set(self.b["birimler"]), {COGULLAYICI, *TUKETICILER},
                         "KIP=udp'de hub OLMAMALI, dort birim olmali")

    def test_K1_cogullayici_mavproxy_uc_ucu_ve_seri_master(self):
        k = self.b["birimler"][COGULLAYICI]
        self.assertIn("mavproxy.py", k)
        self.assertIn("--master=/dev/ttyACM0", k)
        self.assertIn("--baudrate 57600", k)
        for port in (14550, 14551, 14552):
            self.assertIn(f"--out udp:127.0.0.1:{port}", k)
        self.assertIn("--daemon", k)
        self.assertIn("--non-interactive", k)

    def test_K1_tuketiciler_cogullayici_ucundan_sysid_pinli(self):
        rpi = self.b["birimler"][RPI]
        inis = self.b["birimler"][INIS]
        komut = self.b["birimler"][KOMUT]
        self.assertIn("--camera", rpi)
        self.assertEqual(_arg_degeri(rpi, "--mavlink"), "udp:127.0.0.1:14550")
        self.assertEqual(_arg_degeri(rpi, "--mav-sysid"), "1")
        self.assertEqual(_arg_degeri(rpi, "--fov"), "78")
        self.assertEqual(_arg_degeri(rpi, "--yks-hedef"), "10.0.0.1:5005")
        self.assertEqual(_arg_degeri(rpi, "--ika-hedef"), "10.0.0.2:5006")
        self.assertEqual(_arg_degeri(inis, "--mavlink"), "udp:127.0.0.1:14551")
        self.assertEqual(_arg_degeri(inis, "--sysid"), "1")
        self.assertEqual(_arg_degeri(inis, "--kanit-timeout"), "900")
        self.assertEqual(_arg_degeri(inis, "--yks"), "10.0.0.1:5005")
        self.assertEqual(_arg_degeri(inis, "--ika"), "10.0.0.2:5006")
        self.assertEqual(_arg_degeri(komut, "--mavlink"), "udp:127.0.0.1:14552")
        self.assertEqual(_arg_degeri(komut, "--sysid"), "1")
        self.assertEqual(_arg_degeri(komut, "--bind"), "0.0.0.0:5007")

    def test_K1_hicbir_tuketici_seri_cihazi_dogrudan_acmaz(self):
        """CONTRACTS §7.4: `--mavlink /dev/tty*` YASAK; --serial/--telsiz-seri de yok."""
        for ad in TUKETICILER:
            k = self.b["birimler"][ad]
            self.assertIn("--mavlink", k, ad)
            self.assertIsNone(SERI_CIHAZ_KALIBI.search(k),
                              f"{ad}: seri cihaz dogrudan veriliyor: {k}")
            self.assertTrue(_arg_degeri(k, "--mavlink").startswith("udp:127.0.0.1:"), k)
            self.assertNotIn("--serial", k, ad)
            self.assertNotIn("--telsiz-seri", k, ad)

    def test_K5_kuru_komutlari_birimlerin_ExecStartiyla_AYNI(self):
        """Betigin bash yerine-koymasi, birimden BAGIMSIZ Python yerine-koymayla ayni."""
        env = self.b["env"]
        self.assertTrue(env, "env bolumu bos")

        def koy(m):
            ad = m.group(1) or m.group(2)
            self.assertIn(ad, env, f"birimde ${ad} var ama env'de yok")
            return env[ad]

        for ad, komut in self.b["birimler"].items():
            beklenen = re.sub(r"\$\{(\w+)\}|\$(\w+)", koy, _exec_start(ad))
            self.assertEqual(" ".join(komut.split()), " ".join(beklenen.split()), ad)

    def test_K6_pinler_koddan_gelir_sysid_bind_kanit_timeout(self):
        env = self.b["env"]
        self.assertEqual(int(env["SYSID"]), iha_komut_alici.VARSAYILAN_HEDEF_SYSID,
                         "betigin SYSID varsayilani alicinin sozlesmesinden sapti")
        self.assertEqual(_arg_degeri(self.b["birimler"][KOMUT], "--bind"),
                         iha_komut_alici.VARSAYILAN_BIND)
        self.assertEqual(float(env["KANIT_TIMEOUT"]), SARTNAME_IHA_GOREV_SURESI_S)
        self.assertEqual(env["KIP"], "udp")
        self.assertEqual(env["PIXHAWK_SERI"], "/dev/ttyACM0")

    def test_K9_paket_denetimi_dogru_soyler(self):
        """[VAR]/[YOK] satirlari dosya sistemiyle ayni — kuru rapor yalan soylemez."""
        gorulen = 0
        for satir in self.b["paket"]:
            m = re.match(r"^\[(VAR|YOK)\] (\S+\.py)", satir)
            self.assertIsNotNone(m, f"paket satiri bicimi: {satir!r}")
            durum, ad = m.groups()
            if "(PATH)" in satir:
                self.assertEqual(ad, "mavproxy.py")
                continue
            self.assertEqual(durum, "VAR" if (KOD / ad).is_file() else "YOK", satir)
            gorulen += 1
        self.assertEqual(gorulen, len(TUKETICILER))
        for ad in TUKETICILER:
            self.assertIn(f"[VAR] {PY_ADI[ad]}.py", self.b["paket"])

    def test_K9_kilavuz_once_kuru_der(self):
        m = KILAVUZ.read_text(encoding="utf-8")
        ilk_komut = m.index("--kuru")
        self.assertLess(ilk_komut, m.index("sudo -E"),
                        "kilavuz --kuru'yu kurulumdan ONCE soylemeli")
        for ad in TUM_BIRIMLER:
            self.assertIn(ad, m, f"kilavuz {ad} birimini anmiyor")
        self.assertIn("Restart=always", m)


class JetsonBaslatKuruSik(unittest.TestCase):
    """K2 — KIP=sik: seri hub kalkar, /dev/ttyUSB0'i YALNIZ hub acar."""

    @classmethod
    def setUpClass(cls):
        cls.kod, cls.out, cls.err = _kos(BETIK, {"KIP": "sik", "FOV": "78"})
        cls.b = _bolumler(cls.out)

    def test_K2_sik_exit_0_ve_hub_satiri_var(self):
        self.assertEqual(self.kod, 0, f"stdout:\n{self.out}\nstderr:\n{self.err}")
        self.assertEqual(set(self.b["birimler"]), set(TUM_BIRIMLER))
        hub = self.b["birimler"][SERI_HUB]
        self.assertIn("seri_hub.py", hub)
        # CONTRACTS §7.5: hub CLI'si --port (comms/seri_hub.py); --serial DEGIL.
        self.assertEqual(_arg_degeri(hub, "--port"), "/dev/ttyUSB0")
        self.assertNotIn("--serial", hub)
        self.assertEqual(_arg_degeri(hub, "--baud"), "57600")
        self.assertEqual(_arg_degeri(hub, "--bind"), "127.0.0.1:5100")
        self.assertEqual(_arg_degeri(hub, "--tuketici"), "127.0.0.1:5007")

    def test_K2_tuketiciler_hub_loopbackine_konusur_seri_porta_DOKUNMAZ(self):
        rpi = self.b["birimler"][RPI]
        inis = self.b["birimler"][INIS]
        komut = self.b["birimler"][KOMUT]
        self.assertEqual(_arg_degeri(rpi, "--yks-hedef"), "127.0.0.1:5100")
        self.assertNotIn("--ika-hedef", rpi, "tek hatta cift yazma yok")
        self.assertEqual(_arg_degeri(inis, "--yks"), "127.0.0.1:5100")
        self.assertNotIn("--ika", inis.split())
        self.assertEqual(_arg_degeri(komut, "--bind"), "127.0.0.1:5007",
                         "komut alici hub'in --tuketici ucunda dinlemeli")
        for ad in TUKETICILER:
            k = self.b["birimler"][ad]
            self.assertNotIn("/dev/ttyUSB0", k, ad)
            self.assertIsNone(SERI_CIHAZ_KALIBI.search(k), f"{ad}: {k}")
            self.assertNotIn("--serial", k, ad)
            self.assertNotIn("--telsiz-seri", k, ad)
            self.assertTrue(_arg_degeri(k, "--mavlink").startswith("udp:127.0.0.1:"), k)
        # /dev/ttyUSB0 ciktida YALNIZ hub satirinda
        sahipler = [ad for ad, k in self.b["birimler"].items() if "/dev/ttyUSB0" in k]
        self.assertEqual(sahipler, [SERI_HUB])
        self.assertEqual(self.b["env"]["KIP"], "sik")

    def test_K2_hub_betigi_paket_denetiminde_dogru_raporlanir(self):
        var = (KOD / "seri_hub.py").is_file()
        beklenen = "[VAR] seri_hub.py" if var else "[YOK] seri_hub.py"
        self.assertTrue(any(s.startswith(beklenen) for s in self.b["paket"]),
                        f"{beklenen!r} yok: {self.b['paket']}")


class JetsonBaslatFailClosed(unittest.TestCase):
    """K7 — beyan eksik / KIP bilinmiyor: betik DURUR, sessiz varsayilan yok."""

    def test_K7_udp_beyan_eksik_cikis_3_ve_EKSIK_satirlari(self):
        kod, out, err = _kos(BETIK, {"KIP": "udp"})
        self.assertEqual(kod, 3, f"stdout:\n{out}\nstderr:\n{err}")
        b = _bolumler(out)
        eksik = "\n".join(b["beyan"])
        for ad in ("FOV", "YKS_IP", "IKA_IP"):
            self.assertRegex(eksik, rf"\[EKSIK\] .*{ad}", eksik)
        self.assertIn("gercek kosum DURUR", b["sonuc"] or "")
        # komutlar yine de basilir (once bak): kullanici ne kosulacagini gorur
        self.assertIn(RPI, b["birimler"])

    def test_K7_sik_yalniz_FOV_ister_IP_istemez(self):
        kod, out, _ = _kos(BETIK, {"KIP": "sik"})
        self.assertEqual(kod, 3)
        eksik = "\n".join(_bolumler(out)["beyan"])
        self.assertRegex(eksik, r"\[EKSIK\] .*FOV")
        self.assertNotIn("YKS_IP", eksik)
        self.assertNotIn("IKA_IP", eksik)

    def test_K7_FOV_ve_ODAK_birlikte_verilmez(self):
        kod, out, _ = _kos(BETIK, {"KIP": "udp", **BEYAN_TAM, "ODAK": "900"})
        self.assertEqual(kod, 3)
        self.assertRegex("\n".join(_bolumler(out)["beyan"]), r"\[EKSIK\] .*birlikte")

    def test_K7_bilinmeyen_KIP_cikis_1_HATA(self):
        kod, out, err = _kos(BETIK, {"KIP": "wifi", **BEYAN_TAM})
        self.assertEqual(kod, 1, out)
        self.assertIn("HATA", err)
        self.assertNotIn("navitas-rpi-inference.service:", out)

    def test_K7_ODAK_verilince_fov_yerine_odak_gecer(self):
        kod, out, _ = _kos(BETIK, {"KIP": "udp", "YKS_IP": "10.0.0.1",
                                   "IKA_IP": "10.0.0.2", "ODAK": "900",
                                   "SENARYO": "kirsal", "KAMERA": "/dev/video1"})
        self.assertEqual(kod, 0, out)
        rpi = _bolumler(out)["birimler"][RPI]
        self.assertEqual(_arg_degeri(rpi, "--odak"), "900")
        self.assertNotIn("--fov", rpi)
        self.assertEqual(_arg_degeri(rpi, "--senaryo"), "kirsal")
        self.assertEqual(_arg_degeri(rpi, "--kaynak"), "/dev/video1")


class JetsonBaslatCrlf(unittest.TestCase):
    """K8 — Windows calisma agaci CRLF'tir (core.autocrlf=true, olculdu); USB kopyasi
    CR tasir. Betik + birimler CRLF'e cevrilip ayni --kuru ciktisini vermeli."""

    def test_K8_crlf_kopya_ayni_env_ve_birim_ciktisi(self):
        with tempfile.TemporaryDirectory() as d:
            kok = Path(d) / "jetson_paket"
            (kok / "systemd").mkdir(parents=True)
            crlf = BETIK.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
            self.assertIn(b"\r\n", crlf)
            (kok / BETIK.name).write_bytes(crlf)
            for p in BIRIM_DIZIN.glob("*.service"):
                icerik = p.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
                (kok / "systemd" / p.name).write_bytes(icerik)
            kod_c, out_c, err_c = _kos(kok / BETIK.name, {"KIP": "sik", "FOV": "78"})
        kod_l, out_l, _ = _kos(BETIK, {"KIP": "sik", "FOV": "78"})
        self.assertEqual(kod_l, 0)
        self.assertEqual(kod_c, 0, f"CRLF kopya dustu:\nstdout:\n{out_c}\nstderr:\n{err_c}")
        self.assertNotIn("\\r", err_c)
        bc, bl = _bolumler(out_c), _bolumler(out_l)
        self.assertEqual(bc["env"], bl["env"])
        self.assertEqual(bc["birimler"], bl["birimler"])
        self.assertIn(SERI_HUB, bc["birimler"])

    def test_K8_cr_korumasi_set_e_den_ONCE_ve_ilk_komut(self):
        """Calisma kopyasi checkout'a gore LF ya da CRLF olabilir (autocrlf) — kilit
        dosyanin EOL'u DEGIL, CR korumasinin `set -euo pipefail`ten ONCE gelmesidir:
        aksi halde CRLF kopyada `pipefail\\r` ilk satirda patlar, koruma hic kosmaz."""
        satirlar = [s.rstrip("\r") for s in
                    BETIK.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(satirlar[0], "#!/usr/bin/env bash")
        komutlar = [s for s in satirlar if s.strip() and not s.startswith("#")]
        self.assertIn("grep -q $'\\r' \"$0\"", komutlar[0],
                      "CR korumasi ilk komut degil")
        self.assertTrue(komutlar[0].rstrip().endswith("# CRLF"),
                        "koruma satiri CR'i yutacak satir sonu yorumuyla bitmeli")
        self.assertEqual(komutlar[1], "set -euo pipefail")


class SystemdBirimleri(unittest.TestCase):
    """K3/K4 — birim dosyalari: gozcu alanlari, siralama, ExecStart dosyalari, CONTRACTS uclari."""

    def test_K3_bes_birim_dosyasi_var(self):
        self.assertEqual({p.stem for p in BIRIM_DIZIN.glob("*.service")}, set(TUM_BIRIMLER))

    def test_K3_gozcu_alanlari_her_birimde(self):
        for ad in TUM_BIRIMLER:
            with self.subTest(birim=ad):
                a = _birim_oku(ad)
                self.assertEqual(a.get("Restart"), ["always"], ad)
                self.assertIn("RestartSec", a, ad)
                self.assertGreater(float(a["RestartSec"][0]), 0)
                # RestartSec=2 ile varsayilan StartLimitBurst=5/10s cokme dongusunde
                # 10 s'de dolar ve systemd PES EDER — hands-off ihlali. 0 = sinirsiz.
                self.assertEqual(a.get("StartLimitIntervalSec"), ["0"], ad)
                self.assertEqual(a.get("EnvironmentFile"), ["/etc/navitas.env"], ad)
                self.assertIn("network.target", " ".join(a.get("After", [])), ad)
                self.assertEqual(a.get("WantedBy"), ["multi-user.target"], ad)
                self.assertTrue(a["ExecStart"][0].startswith("/"),
                                f"{ad}: ExecStart mutlak yol degil")

    def test_K3_tuketiciler_cogullayiciya_bagli(self):
        for ad in TUKETICILER:
            with self.subTest(birim=ad):
                a = _birim_oku(ad)
                self.assertIn(f"{COGULLAYICI}.service", " ".join(a.get("After", [])), ad)
                self.assertIn(f"{COGULLAYICI}.service", " ".join(a.get("Wants", [])), ad)
                self.assertIn(f"{SERI_HUB}.service", " ".join(a.get("After", [])),
                              f"{ad}: KIP=sik'te hub'dan sonra kalkmali")
        for ad in (COGULLAYICI, SERI_HUB):
            self.assertNotIn("Wants", _birim_oku(ad), f"{ad}: kimseyi cekmemeli")

    def test_K3_ExecStart_py_dosyasi_pakette_MEVCUT(self):
        """ExecStart'taki NAVITAS .py dosyasi jetson_paket/kod/ altinda olmali.
        Depoda HIC olmayan betik (seri_hub.py, 2026-09-02) icin GORUNUR skip:
        paket bir seyi aynalayamaz; betik depoya girince bu kapi zorunlu olur."""
        for ad in TUM_BIRIMLER:
            with self.subTest(birim=ad):
                yol = _navitas_py(_exec_start(ad))
                if ad == COGULLAYICI:
                    self.assertIsNone(yol)
                    self.assertIn("mavproxy.py", _exec_start(ad))
                    continue
                self.assertIsNotNone(yol, f"{ad}: ExecStart'ta NAVITAS .py yok")
                dosya = Path(yol).name
                depoda = [k for k in ("comms", "codes", "scripts")
                          if (KOK / k / dosya).is_file()]
                if not depoda and not (KOD / dosya).is_file():
                    self.skipTest(f"YAPILAMADI: {dosya} depoda HIC yok — {ad} birimi "
                                  f"paketlenemez (hub betigi ayri gorev, D-403 §4b)")
                self.assertTrue((KOD / dosya).is_file(),
                                f"{ad}: {dosya} depoda var ama jetson_paket/kod/ TASIMIYOR "
                                f"(scripts/jetson_paket_hazirla.py KOPYALAR) — D-193 sinifi")

    def test_K4_ExecStart_mavlink_uclari_CONTRACTS_7_4_ile_AYNI(self):
        sozlesme = _sozlesme_uclari()
        self.assertEqual(set(sozlesme), set(PY_ADI.values()),
                         f"CONTRACTS §7.4 tablosu okunamadi/degisti: {sozlesme}")
        for ad in TUKETICILER:
            with self.subTest(birim=ad):
                k = _exec_start(ad)
                self.assertEqual(Path(_navitas_py(k)).stem, PY_ADI[ad])
                self.assertEqual(_arg_degeri(k, "--mavlink"),
                                 f"udp:127.0.0.1:{sozlesme[PY_ADI[ad]]}", k)
                self.assertIsNone(SERI_CIHAZ_KALIBI.search(k), k)
        cog = _exec_start(COGULLAYICI)
        cikislar = {int(t.rsplit(":", 1)[1]) for t in cog.split() if t.startswith("udp:127.0.0.1:")}
        self.assertEqual(cikislar, set(sozlesme.values()),
                         "cogullayici --out uclari sozlesme tablosundan sapti")
        self.assertIn("--master=${PIXHAWK_SERI}", cog)

    def test_K4_sysid_pini_birimde_degiskenle_KODDA(self):
        self.assertIn("--mav-sysid ${SYSID}", _exec_start(RPI))
        self.assertIn("--sysid ${SYSID}", _exec_start(INIS))
        self.assertIn("--sysid ${SYSID}", _exec_start(KOMUT))
        self.assertIn("--kanit-timeout ${KANIT_TIMEOUT}", _exec_start(INIS))
        hub = _exec_start(SERI_HUB)
        self.assertEqual(_arg_degeri(hub, "--bind"), "127.0.0.1:5100")
        self.assertEqual(_arg_degeri(hub, "--tuketici"), "127.0.0.1:5007")


if __name__ == "__main__":
    unittest.main()
