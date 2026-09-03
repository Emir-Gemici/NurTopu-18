"""FAZ B · GOREV C — JETSON ACILIS KAPILARI (jetson_paket/jetson_baslat.sh + systemd/).

NEDEN: sartname §6.2 thazirlik — Jetson TEK komutla kalkmali; hands-off sonrasi
olen surec KENDI kalkmali (Restart=always). CONTRACTS §7.4 (D-403): seri Pixhawk
tek sahipli; uclar (14550/14551/14552) ve --sysid/--mav-sysid pinleri BELGEDE
degil KODDA olmali. Bu test o kodu (bash betigi + birim dosyalari) GERCEKTEN
kosarak (`bash jetson_baslat.sh ...`, Git Bash/Linux bash) ve CONTRACTS.md
metniyle karsilastirarak kilitler.

D-405 (curutucu, "KURU vs GERCEK AYRISMASI"): --kur/--kapi/--dogrudan/--durdur
yollari da KOSULUR — systemd/seri cihaz yerine gecici dizinde SAHTE systemctl /
sudo / id / python3 / mavproxy.py bash shim'leri (her cagriyi SHIM_LOG'a yazar) ve
sahte "kurulu Jetson" (NAVITAS_KOK, seri cihaz dosyalari, ENV_DOSYA, SYSTEMD_DIZIN,
LOG_DIZIN) verilir. Mock kutuphanesi yok; betik gercek bash'te gercek komutlarla
kosar, yalniz ana makineye dokunan uclar shim'dir. NEDEN shim (fail-closed secim):
--kuru artik herhangi bir [YOK]'ta 3 ile durur; PC'de mavproxy/python3/seri cihaz
yoktur — "PC'de beklenir" diye kosulsuz tutmak, --kuru'nun yalan soylemesini
testte yasallastirirdi. Shim ile "hazir makine" gercekten kurulur, exit 0 hak edilir.

Kapilar (adlari ne kilitledigini soyler):
  K1 --kuru KIP=udp: hazir makinede exit 0; varsayilanlarla exit = (0 | 3) [YOK] sayisiyla
     TUTARLI; 14550/14551/14552, --mav-sysid, --sysid, mavproxy satiri; hicbir tuketici
     /dev/tty ile --mavlink almaz, --serial/--telsiz-seri yok
  K2 --kuru KIP=sik: seri-hub satiri; tuketiciler 127.0.0.1:5100'e; /dev/ttyUSB0 yalniz hub'da
  K3 her .service BOLUM kilidi: [Unit] StartLimitIntervalSec=0 + After=network.target,
     [Service] Restart=always, RestartSec, EnvironmentFile, User=navitas, [Install] WantedBy;
     StartLimitIntervalSec [Service]'e tasinirsa (systemd sessizce yok sayar) DUSER;
     tuketiciler After/Wants cogullayici; ExecStart .py kod/ altinda MEVCUT
  K4 ExecStart --mavlink uclari == CONTRACTS.md §7.4 tablosu (metin kilidi)
  K5 --kuru komutlari == birimlerin ExecStart'i (bagimsiz Python yerine-koyma ile;
     hem varsayilan hem ezilmis NAVITAS_KOK/PYTHON3 ciftleriyle)
  K6 pinler KODDAN: SYSID varsayilani = iha_komut_alici.VARSAYILAN_HEDEF_SYSID; 5007 =
     VARSAYILAN_BIND; KANIT_TIMEOUT = karar_sozlesmesi.SARTNAME_IHA_GOREV_SURESI_S
  K7 beyan eksik -> --kuru cikis 3 + [EKSIK]; KIP taninmiyor -> cikis 1 (fail-closed)
  K8 CRLF kopyasi (Windows autocrlf / USB) ayni env+birim ciktisini verir, exit 0 VE
     koruma dali GERCEKTEN kosar (basliga "(CR'siz kopya: ...)" basar, gecici dosya silinir);
     bu bash CR'i goremiyorsa GORUNUR skip ("YAPILAMADI"), sessiz gecis degil
  K9 --kuru DOGRU SOYLER: paket [VAR]/[YOK] dosya sistemiyle ayni; ana makine denetimi
     (kullanici / yorumlayici / seri cihaz / kurulu .py / mavproxy PATH) gercekle ayni;
     herhangi [YOK] -> "KURU SONUC: eksik" + exit 3 (D-405: "[YOK] mavproxy iken tamam" yalani);
     bosluk/glob iceren deger -> [UYARI]; kilavuz --kuru'yu once der
  K10 shim ile GERCEK kosum (D-405):
     --kur: root denetimi (root degilse HATA + PAKET yolu, /tmp kopya yolu DEGIL); daemon-reload
       -> enable -> RESTART sirasi (enable --now DEGIL); ikinci --kur'da yeni beyan env'e yazilir
       ve yine restart; yazilan birimler CR'siz, User=/EnvironmentFile=/WorkingDirectory=/PATH
       sed'lenmis, bolum kilidi korunmus; env dosyasi == --kuru env bolumu
     --kapi: uc uc AYNI ANDA (baslangiclar en erken bitisten once), 3/3 -> tuketiciler
       enable+restart; 2/3 -> HATA exit 1, tuketiciler BASLATILMAZ, eski .rc dosyasi sayilmaz
     --dogrudan: KAMERA='*' glob GENISLEMEZ (set -f); --durdur nohup pid'lerini oldurur
  K11 Gorev K (SAHA_HAZIRLIK_PLANI_20260903 §1.4): KAMERA=http://127.0.0.1:<port>/video ->
     navitas-kamera-koprusu SISTEM Python'la (${KAMERA_PYTHON}, PYTHON3 venv'e ezilse de) kalkar,
     rpi_inference --kaynak ayni URL; port URL'den; yanlis yol -> cikis 1; loopback disi
     KAMERA kopru kaldirmaz; 8080 ve /video kamera_koprusu sabitleriyle AYNI (madde 16)
"""
import getpass
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
for _y in (KOK / "comms", KOK / "codes", KOK / "scripts"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

import iha_komut_alici  # noqa: E402
import kamera_koprusu  # noqa: E402
import seri_hub  # noqa: E402
from karar_sozlesmesi import MAVLINK_KONUM_ASGARI_HZ, SARTNAME_IHA_GOREV_SURESI_S  # noqa: E402

PAKET = KOK / "jetson_paket"
BETIK = PAKET / "jetson_baslat.sh"
BIRIM_DIZIN = PAKET / "systemd"
KOD = PAKET / "kod"
CONTRACTS = KOK / "CONTRACTS.md"
KILAVUZ = PAKET / "JETSON_BASLAT.md"
RUNBOOK = KOK / "SAHA_RUNBOOK.md"   # betigin YKS/IKA uclari icin gosterdigi otorite

COGULLAYICI = "navitas-cogullayici"
SERI_HUB = "navitas-seri-hub"
RPI = "navitas-rpi-inference"
INIS = "navitas-iha-inis-yayinci"
KOMUT = "navitas-iha-komut-alici"
TUKETICILER = (RPI, INIS, KOMUT)
TUM_BIRIMLER = (COGULLAYICI, SERI_HUB) + TUKETICILER          # MAVLink/seri birimleri (KIP'e gore)
KAMERA_KOPRUSU = "navitas-kamera-koprusu"   # Gorev K: yalniz KAMERA=http://127.0.0.1:<port>/video ile
BIRIM_DOSYALARI = TUM_BIRIMLER + (KAMERA_KOPRUSU,)            # paketteki TUM birim dosyalari
KOPRU_URL = kamera_koprusu.video_url()      # http://127.0.0.1:8080/video (kamera_koprusu sabitleri)
MAV_UCLAR = ("udp:127.0.0.1:14550", "udp:127.0.0.1:14551", "udp:127.0.0.1:14552")

# Betigin ExecStart dosya adi -> CONTRACTS §7.4 tablo satiri (`rpi_inference --mavlink`)
PY_ADI = {RPI: "rpi_inference", INIS: "iha_inis_yayinci", KOMUT: "iha_komut_alici"}
# Kurulu kopyada (JETSON_KILAVUZ §2) dosyalarin yeri: kod/<ad>.py -> <NAVITAS_KOK>/<alt>/<ad>.py
KURULU_YERI = {"rpi_inference.py": "codes", "iha_inis_yayinci.py": "comms",
               "iha_komut_alici.py": "comms", "seri_hub.py": "comms",
               "mavlink_dogrula.py": "scripts", "kamera_koprusu.py": "scripts"}

# Birim dosyalarindaki sabitler; betik ezilmis degerle bunlari sed'ler (yerine_koy + birimleri_kur)
KOK_VARSAYILAN = "/home/navitas/navitas"
PYTHON3_VARSAYILAN = "/usr/bin/python3"
ENV_DOSYA_VARSAYILAN = "/etc/navitas.env"
KULLANICI_VARSAYILAN = "navitas"

BEYAN_TAM = {"YKS_IP": "10.0.0.1", "IKA_IP": "10.0.0.2", "FOV": "78"}
# Betigin/shim'lerin okudugu anahtarlar: gelistirici ortamindan SIZMASIN
BEYAN_ANAHTARLARI = ("KIP", "YKS_IP", "IKA_IP", "FOV", "ODAK", "SENARYO", "KAMERA",
                     "UB_REFERANS", "SYSID", "PIXHAWK_SERI", "PIXHAWK_BAUD", "SIK_SERI",
                     "SIK_BAUD", "KANIT_TIMEOUT", "NAVITAS_KOK", "PYTHON3", "LOG_DIZIN",
                     "ENV_DOSYA", "SYSTEMD_DIZIN", "SERVIS_KULLANICI", "SUDO_USER", "USER",
                     "NAVITAS_PAKET_DIZIN", "NAVITAS_CR_KOPYA",
                     "SHIM_LOG", "SHIM_UID", "SHIM_KULLANICI", "FAKE_DUSEN", "FAKE_SURE",
                     "FAKE_SLEEP", "NAVITAS_TEST_PATH_ON", "KAMERA_PYTHON",
                     "KAMERA_KOPRU_ARGS")
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


def _msys(p):
    """Betige VERILEN yol: Windows'ta /c/Users/... (MSYS bicimi; cd/test/sed ile ayni dize
    geri doner), baska yerde oldugu gibi."""
    s = _posix(p)
    if os.name == "nt" and re.match(r"^[A-Za-z]:/", s):
        return "/" + s[0].lower() + s[2:]
    return s


def _bash():
    bash = _bash_bul()
    if bash is None:
        raise unittest.SkipTest("bash yok (Git Bash / Linux bash gerekli) — YAPILAMADI")
    return bash


def _kos(betik, ek_env, secenek="--kuru", timeout=90):
    """`bash <betik> <secenek>` GERCEK kosum; (cikis, stdout, stderr).

    Shim dizinleri (NAVITAS_TEST_PATH_ON, ':' ayracli) bash ICINDE PATH'in onune alinir:
    Git for Windows'un `Git/bin/bash.exe` sarmalayicisi ortamdaki PATH'in onune
    /mingw64/bin:/usr/bin ekler (olculdu) — disaridan verilen shim /usr/bin/id.exe'nin
    arkasinda kalirdi. Ic `exec bash` gercek /usr/bin/bash'tir, PATH'e dokunmaz."""
    env = dict(os.environ)
    for k in BEYAN_ANAHTARLARI:
        env.pop(k, None)
    env.update(ek_env)
    p = subprocess.run([_bash(), "-c",
                        'if [ -n "${NAVITAS_TEST_PATH_ON:-}" ]; then PATH="$NAVITAS_TEST_PATH_ON:$PATH"; fi; '
                        'exec bash "$1" "$2"', "_", _posix(betik), secenek],
                       env=env, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=timeout)
    return p.returncode, p.stdout, p.stderr


def _bash_test(bayrak, yol):
    """bash `test <bayrak> <yol>` — betigin kullandigi ayni sinama (-e/-f/-x)."""
    return subprocess.run([_bash(), "-c", 'test "$1" "$2"', "_", bayrak, yol],
                          capture_output=True, timeout=30).returncode == 0


def _bash_id_var(kullanici):
    return subprocess.run([_bash(), "-c", 'id -u "$1" >/dev/null 2>&1', "_", kullanici],
                          capture_output=True, timeout=30).returncode == 0


def _bash_komut_var(ad, on_path):
    return subprocess.run([_bash(), "-c", 'PATH="$1:$PATH" command -v "$2" >/dev/null 2>&1',
                           "_", on_path, ad], capture_output=True, timeout=30).returncode == 0


def _bolumler(cikti):
    """--kuru ciktisini bolumlere ayir: env (dict), birimler (dict), paket, makine, beyan, sonuc."""
    b = {"env": {}, "birimler": {}, "paket": [], "makine": [], "beyan": [], "sonuc": None}
    bolum = None
    for satir in cikti.splitlines():
        if satir.startswith("## "):
            if "(yazilacak icerik)" in satir:
                bolum = "env"
            elif satir.startswith("## birimler"):
                bolum = "birimler"
            elif satir.startswith("## paket denetimi"):
                bolum = "paket"
            elif satir.startswith("## ana makine denetimi"):
                bolum = "makine"
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
        elif bolum in ("paket", "makine", "beyan"):
            b[bolum].append(satir)
    return b


def _yok_sayisi(b):
    return sum(1 for s in b["paket"] + b["makine"] if s.startswith("[YOK]"))


def _birim_oku_metin(metin):
    """Birim metnini BOLUM -> {anahtar: [deger, ...]} olarak oku (D-405 K3 bulgusu:
    bolum atilinca StartLimitIntervalSec'in [Service]'e kaymasi gorunmezdi)."""
    bolumler = {}
    bolum = None
    for satir in metin.splitlines():
        satir = satir.rstrip("\r")
        if not satir or satir.startswith("#"):
            continue
        if satir.startswith("["):
            bolum = satir.strip("[]").strip()
            bolumler.setdefault(bolum, {})
            continue
        if bolum is None:
            raise AssertionError(f"bolumsuz alan: {satir!r}")
        k, _, v = satir.partition("=")
        bolumler[bolum].setdefault(k.strip(), []).append(v.strip())
    return bolumler


def _birim_oku(ad):
    return _birim_oku_metin((BIRIM_DIZIN / f"{ad}.service").read_text(encoding="utf-8"))


def _exec_start(ad):
    a = _birim_oku(ad)
    if "ExecStart" not in a.get("Service", {}):
        raise AssertionError(f"{ad}: [Service] ExecStart yok")
    return a["Service"]["ExecStart"][0]


def _navitas_py(komut, kok=KOK_VARSAYILAN):
    """Komut satirindaki ilk <kok>/... .py yolu (yoksa None)."""
    for t in komut.split():
        if t.startswith(kok + "/") and t.endswith(".py"):
            return t
    return None


def _arg_degeri(komut, bayrak):
    parcalar = komut.split()
    if bayrak not in parcalar:
        return None
    i = parcalar.index(bayrak)
    return parcalar[i + 1] if i + 1 < len(parcalar) else None


def _runbook_yks_portu():
    """SAHA_RUNBOOK'un ilan ettigi YKS UDP ucu (`--yks <YKS_IP>:<port>`) — metin kilidi.

    NEDEN (K6 "pinler KODDAN" yordami): betikteki `YKS_PORT` yalniz bir bash
    sabiti; betigin kendi yorumu otorite olarak SAHA_RUNBOOK §1/§3'u gosterir.
    Bu portu teste ciplak yazmak, kapiyi "betik ne yaziyorsa o" haline getirirdi.
    Port kritiktir: yks_gui TEK soket kullanir (`--bind` ile acar, komutu ve
    ACK'i AYNI soketten yollar), yani IHA'ya varan komutun KAYNAK ucu budur;
    --izinli-kaynak ile ayrisirsa saha ARM/RTL komutlari eyleyicide reddedilir.
    K4'un CONTRACTS.md metin kilidiyle ayni yordam."""
    portlar = {int(p) for p in re.findall(r"--yks\s+<YKS_IP>:(\d+)",
                                          RUNBOOK.read_text(encoding="utf-8"))}
    return portlar


def _sozlesme_uclari():
    """CONTRACTS.md §7.4 tablosu: {'rpi_inference': 14550, ...} — metin kilidi."""
    m = CONTRACTS.read_text(encoding="utf-8")
    bas = m.index("### 7.4")
    son = m.find("\n## ", bas)
    bolum = m[bas:son if son > 0 else None]
    eslesme = re.findall(
        r"\|\s*`(\w+) --mavlink`\s*\|\s*`udp:127\.0\.0\.1:(\d+)`\s*\|", bolum)
    return {ad: int(port) for ad, port in eslesme}


def _gozcu_kilidi(tc, a, ad, env_dosya=ENV_DOSYA_VARSAYILAN, kullanici=KULLANICI_VARSAYILAN):
    """K3 bolum kilidi — repo birimleri VE kurulu (sed'lenmis) birimler icin ayni."""
    tc.assertEqual(set(a), {"Unit", "Service", "Install"}, f"{ad}: bolumler")
    u, s, i = a["Unit"], a["Service"], a["Install"]
    # RestartSec=2 ile varsayilan StartLimitBurst=5/10s cokme dongusunde 10 s'de dolar
    # ve systemd PES EDER — hands-off ihlali. 0 = sinirsiz; YALNIZ [Unit] altinda gecerli.
    tc.assertEqual(u.get("StartLimitIntervalSec"), ["0"], f"{ad}: [Unit] StartLimitIntervalSec")
    tc.assertNotIn("StartLimitIntervalSec", s,
                   f"{ad}: StartLimitIntervalSec [Service] altinda — systemd sessizce yok sayar")
    tc.assertIn("network.target", " ".join(u.get("After", [])), ad)
    tc.assertEqual(s.get("Restart"), ["always"], f"{ad}: [Service] Restart")
    tc.assertIn("RestartSec", s, ad)
    tc.assertGreater(float(s["RestartSec"][0]), 0)
    tc.assertEqual(s.get("Type"), ["simple"], ad)
    tc.assertEqual(s.get("EnvironmentFile"), [env_dosya], f"{ad}: EnvironmentFile")
    tc.assertEqual(s.get("User"), [kullanici], f"{ad}: User")
    tc.assertTrue(s["ExecStart"][0].startswith("/"), f"{ad}: ExecStart mutlak yol degil")
    tc.assertEqual(i.get("WantedBy"), ["multi-user.target"], f"{ad}: [Install] WantedBy")


# ── Sahte "kurulu Jetson" (D-405 shim yontemi) ──────────────────────────────────
_SHIM_MAVPROXY = """#!/usr/bin/env bash
echo "$EPOCHREALTIME mavproxy $*" >> "$SHIM_LOG"
for a in "$@"; do printf 'ARGV[%s]\\n' "$a"; done
sleep "${FAKE_SLEEP:-1}"
"""
_SHIM_PYTHON3 = """#!/usr/bin/env bash
echo "$EPOCHREALTIME python3 $*" >> "$SHIM_LOG"
for a in "$@"; do printf 'ARGV[%s]\\n' "$a"; done
hepsi="$*"
case "$hepsi" in *mavlink_dogrula*)
  port="${hepsi##*--mavlink udp:127.0.0.1:}"; port="${port%% *}"
  echo "$EPOCHREALTIME DOGRULA_BASLA $port" >> "$SHIM_LOG.dogrula_$port"
  sleep "${FAKE_SURE:-1}"
  echo "$EPOCHREALTIME DOGRULA_BITTI $port" >> "$SHIM_LOG.dogrula_$port"
  case " $hepsi " in *" --mavlink ${FAKE_DUSEN:-yok} "*) echo "DUSTU (sahte)"; exit 1;; esac
  echo "GECTI (sahte)"; exit 0;;
esac
sleep "${FAKE_SLEEP:-1}"
"""
_SHIM_SYSTEMCTL = """#!/usr/bin/env bash
echo "$EPOCHREALTIME systemctl $*" >> "$SHIM_LOG"
case "$1" in is-active) echo active;; show) echo 0;; esac
exit 0
"""
_SHIM_SUDO = """#!/usr/bin/env bash
echo "$EPOCHREALTIME sudo $*" >> "$SHIM_LOG"
if [ "$1" = -u ]; then shift 2; fi
exec "$@"
"""
_SHIM_ID = """#!/usr/bin/env bash
echo "$EPOCHREALTIME id $*" >> "$SHIM_LOG"
if [ "$1" = -u ] && [ $# -eq 1 ]; then echo "${SHIM_UID:-0}"; exit 0; fi
if [ "$1" = -u ] && [ "${2:-}" = "$SHIM_KULLANICI" ]; then echo 1000; exit 0; fi
echo "id: '${2:-}': no such user" >&2; exit 1
"""


class _AnaMakine:
    """Gecici dizinde sahte kurulu Jetson. bin/: mavproxy.py + python3 shim'leri (PATH'e
    konur — ana makine denetimi gecer); sbin/: systemctl + sudo + id shim'leri (yalniz
    --kur/--kapi icin; `id -u` root der). kok/: kod/ dosyalarinin JETSON_KILAVUZ §2
    yerlesimiyle kopyasi; dev/: seri cihaz dosyalari; etc/, log/."""

    def __init__(self, sbin=False, kullanici=None, crlf_paket=False, lf_paket=False):
        self.d = Path(tempfile.mkdtemp(prefix="navitas_jb_"))
        self.kullanici = kullanici or getpass.getuser()
        self.bin = self.d / "bin"
        self.sbin = self.d / "sbin"
        self.kok = self.d / "kok"
        self.etc = self.d / "etc"
        self.systemd = self.etc / "systemd"
        self.log = self.d / "log"
        self.shim_log = self.d / "shim.log"
        for p in (self.bin, self.sbin, self.kok, self.systemd, self.log, self.d / "dev"):
            p.mkdir(parents=True)
        self._shim(self.bin / "mavproxy.py", _SHIM_MAVPROXY)
        self._shim(self.bin / "python3", _SHIM_PYTHON3)
        self.sbin_acik = sbin
        if sbin:
            self._shim(self.sbin / "systemctl", _SHIM_SYSTEMCTL)
            self._shim(self.sbin / "sudo", _SHIM_SUDO)
            self._shim(self.sbin / "id", _SHIM_ID)
        for ad, alt in KURULU_YERI.items():
            if (KOD / ad).is_file():
                (self.kok / alt).mkdir(exist_ok=True)
                shutil.copyfile(KOD / ad, self.kok / alt / ad)
        (self.d / "dev" / "ttyACM0").write_bytes(b"")
        (self.d / "dev" / "ttyUSB0").write_bytes(b"")
        self.bos = self.d / "bos_dosya"   # var ama -x DEGIL (yorumlayici-yok senaryosu)
        self.bos.write_bytes(b"")
        self.env_dosya = self.etc / "navitas.env"
        self.paket = PAKET
        if crlf_paket or lf_paket:
            # crlf_paket: USB/Windows kopyasi (betik + birimler CRLF).
            # lf_paket: Jetson/Linux checkout'u (LF). Calisma kopyasi autocrlf ile
            # CRLF olabilir (ana agacta oyle; D-405 birlesmesinde olculdu) — "LF
            # kopya" hicbir zaman calisma kopyasinin kendisi degildir, ACIKCA uretilir.
            eol = b"\r\n" if crlf_paket else b"\n"
            self.paket = self.d / "jetson_paket"
            (self.paket / "systemd").mkdir(parents=True)
            (self.paket / "kod").mkdir()
            for kaynak, hedef in [(BETIK, self.paket / BETIK.name)] + [
                    (p, self.paket / "systemd" / p.name) for p in BIRIM_DIZIN.glob("*.service")]:
                hedef.write_bytes(kaynak.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", eol))
            for p in KOD.iterdir():
                if p.is_file():
                    shutil.copyfile(p, self.paket / "kod" / p.name)
        self.betik = self.paket / BETIK.name

    @staticmethod
    def _shim(yol, icerik):
        yol.write_bytes(icerik.encode("utf-8"))   # LF; shebang'li dosya Git Bash'te de -x
        yol.chmod(yol.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    @property
    def path_on(self):
        yollar = [_msys(self.bin)] + ([_msys(self.sbin)] if self.sbin_acik else [])
        return ":".join(yollar)

    def env(self, **ek):
        e = {
            "NAVITAS_TEST_PATH_ON": self.path_on,   # _kos bash icinde PATH'in onune alir
            "SHIM_LOG": _msys(self.shim_log),
            "SHIM_KULLANICI": self.kullanici,
            "SERVIS_KULLANICI": self.kullanici,
            "PYTHON3": _msys(self.bin / "python3"),
            "KAMERA_PYTHON": _msys(self.bin / "python3"),
            "PIXHAWK_SERI": _msys(self.d / "dev" / "ttyACM0"),
            "SIK_SERI": _msys(self.d / "dev" / "ttyUSB0"),
            "NAVITAS_KOK": _msys(self.kok),
            "ENV_DOSYA": _msys(self.env_dosya),
            "SYSTEMD_DIZIN": _msys(self.systemd),
            "LOG_DIZIN": _msys(self.log),
        }
        e.update(ek)
        return e

    def shim_satirlari(self):
        if not self.shim_log.is_file():
            return []
        return [s.split(" ", 1)[1] for s in
                self.shim_log.read_text(encoding="utf-8", errors="replace").splitlines() if " " in s]

    def shim_sifirla(self):
        if self.shim_log.is_file():
            self.shim_log.unlink()
        for p in self.d.glob("shim.log.dogrula_*"):
            p.unlink()

    def dogrula_zamanlari(self):
        """{port: (basla, bitti)} — python3 shim'inin mavlink_dogrula kosumlari."""
        z = {}
        for p in self.d.glob("shim.log.dogrula_*"):
            port = p.name.rsplit("_", 1)[1]
            basla = bitti = None
            for s in p.read_text(encoding="utf-8").splitlines():
                t, olay, _ = s.split(" ", 2)
                if olay == "DOGRULA_BASLA":
                    basla = float(t)
                elif olay == "DOGRULA_BITTI":
                    bitti = float(t)
            z[port] = (basla, bitti)
        return z

    def temizle(self):
        shutil.rmtree(self.d, ignore_errors=True)


class JetsonBaslatKuruUdp(unittest.TestCase):
    """K1/K5/K6/K9 — `bash jetson_baslat.sh --kuru` KIP=udp, GERCEK kosum: varsayilanlarla
    (bu makinenin gercegi) VE sahte hazir makinede (exit 0 hak edilir)."""

    @classmethod
    def setUpClass(cls):
        cls.kod, cls.out, cls.err = _kos(BETIK, {"KIP": "udp", **BEYAN_TAM})
        cls.b = _bolumler(cls.out)
        cls.m = _AnaMakine()
        cls.kod_h, cls.out_h, cls.err_h = _kos(BETIK, cls.m.env(KIP="udp", **BEYAN_TAM))
        cls.b_h = _bolumler(cls.out_h)

    @classmethod
    def tearDownClass(cls):
        cls.m.temizle()

    def test_K1_hazir_makinede_exit_0_ve_hicbir_sey_baslatilmadi(self):
        self.assertEqual(self.kod_h, 0, f"stdout:\n{self.out_h}\nstderr:\n{self.err_h}")
        self.assertIn("HICBIR SEY BASLATILMADI", self.out_h)
        self.assertIn("[TAM] beyanlar tam", self.out_h)
        self.assertEqual(_yok_sayisi(self.b_h), 0, self.out_h)
        self.assertTrue(self.b_h["sonuc"].startswith("KURU SONUC: tamam"), self.b_h["sonuc"])
        self.assertIn("sudo -E bash", self.b_h["sonuc"])
        self.assertEqual(set(self.b_h["birimler"]), {COGULLAYICI, *TUKETICILER},
                         "KIP=udp'de hub OLMAMALI, dort birim olmali")
        self.assertEqual(len(self.m.shim_satirlari()), 0, "--kuru hicbir shim'i CALISTIRMAZ")

    def test_K1_varsayilanlarla_exit_YOK_sayisiyla_tutarli(self):
        """Varsayilan yollarla (bu makinede ne varsa): [YOK] yoksa 0/tamam, varsa 3/eksik —
        Jetson'da tam kurulumda 0, PC'de 3; ikisi de DOGRU (kuru rapor yalan soylemez)."""
        yok = _yok_sayisi(self.b)
        self.assertIn("HICBIR SEY BASLATILMADI", self.out)
        self.assertIn("[TAM] beyanlar tam", self.out)
        self.assertEqual(set(self.b["birimler"]), {COGULLAYICI, *TUKETICILER})
        if yok == 0:
            self.assertEqual(self.kod, 0, self.out)
            self.assertTrue(self.b["sonuc"].startswith("KURU SONUC: tamam"), self.b["sonuc"])
        else:
            self.assertEqual(self.kod, 3, f"stdout:\n{self.out}\nstderr:\n{self.err}")
            self.assertRegex(self.b["sonuc"] or "",
                             rf"^KURU SONUC: eksik \(beyan: tam · \[YOK\]: {yok}\) — gercek kosum DURUR")

    def test_K1_cogullayici_mavproxy_uc_ucu_ve_seri_master(self):
        k = self.b["birimler"][COGULLAYICI]
        self.assertIn("mavproxy.py", k)
        self.assertIn("--master=/dev/ttyACM0", k)
        self.assertIn("--baudrate 57600", k)
        for port in (14550, 14551, 14552):
            self.assertIn(f"--out udp:127.0.0.1:{port}", k)
        self.assertIn("--daemon", k)
        self.assertIn("--non-interactive", k)
        # D-406 B: MAVProxy varsayilan --streamrate 4, baglaninca REQUEST_DATA_STREAM(ALL,4)
        # ile SR2_POSITION=8'i 4 Hz'e cekerdi (= asgari, jitter payi sifir). 8 = 2x asgari;
        # deger CONTRACTS sabitinden turetilir (madde 16), ciplak 8 degil.
        self.assertEqual(_arg_degeri(k, "--streamrate"), str(int(2 * MAVLINK_KONUM_ASGARI_HZ)),
                         "cogullayici --streamrate 8 (D-406 B) yok/yanlis: " + k)
        self.assertEqual(_arg_degeri(_exec_start(COGULLAYICI), "--streamrate"),
                         str(int(2 * MAVLINK_KONUM_ASGARI_HZ)), "birim dosyasinda --streamrate 8 yok")

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

    def _k5(self, b):
        env = b["env"]
        self.assertTrue(env, "env bolumu bos")

        def koy(m):
            ad = m.group(1) or m.group(2)
            self.assertIn(ad, env, f"birimde ${ad} var ama env'de yok")
            return env[ad]

        for ad, komut in b["birimler"].items():
            beklenen = re.sub(r"\$\{(\w+)\}|\$(\w+)", koy, _exec_start(ad))
            # betigin belgeledigi sabit ciftler (KOK_VARSAYILAN/PYTHON3_VARSAYILAN -> ezilmis)
            beklenen = beklenen.replace(KOK_VARSAYILAN, env["NAVITAS_KOK"])
            beklenen = beklenen.replace(PYTHON3_VARSAYILAN, env["PYTHON3"])
            self.assertEqual(" ".join(komut.split()), " ".join(beklenen.split()), ad)

    def test_K5_kuru_komutlari_birimlerin_ExecStartiyla_AYNI(self):
        """Betigin bash yerine-koymasi, birimden BAGIMSIZ Python yerine-koymayla ayni —
        varsayilan yollarla VE ezilmis NAVITAS_KOK/PYTHON3 ile (sed ciftleri)."""
        self._k5(self.b)
        self._k5(self.b_h)
        self.assertNotEqual(self.b_h["env"]["NAVITAS_KOK"], KOK_VARSAYILAN)
        self.assertIn(self.b_h["env"]["NAVITAS_KOK"], self.b_h["birimler"][RPI])
        self.assertTrue(self.b_h["birimler"][RPI].startswith(self.b_h["env"]["PYTHON3"] + " "))

    def test_K6_pinler_koddan_gelir_sysid_bind_kanit_timeout(self):
        env = self.b["env"]
        self.assertEqual(int(env["SYSID"]), iha_komut_alici.VARSAYILAN_HEDEF_SYSID,
                         "betigin SYSID varsayilani alicinin sozlesmesinden sapti")
        self.assertEqual(_arg_degeri(self.b["birimler"][KOMUT], "--bind"),
                         iha_komut_alici.VARSAYILAN_BIND)
        # Kritik eyleyicinin KAYNAK PINI: --izinli-kaynak, BEYAN EDILEN YKS
        # soketi olmali. Beklenen deger betigin ciktisindan OKUNMAZ; iki
        # bagimsiz capadan kurulur:
        #   (1) host = teste girdi olarak verilen YKS_IP (BEYAN_TAM). `env`
        #       bolumunde YKS_IP yoktur ve OLMAMALIDIR: deger uretim aninda
        #       *_TELSIZ_ARGS icine pisirilir; /etc/navitas.env'e ayrica
        #       yazilsaydi operator "orayi duzeltirsem kaynak degisir" diye
        #       yanilirdi — oysa ARGS zaten sabitlenmistir (fail-visible).
        #   (2) port = SAHA_RUNBOOK'un ilan ettigi YKS ucu (_runbook_yks_portu).
        # Ciplak dize yazmak, betik ne uretirse onu onaylayan bos kapi olurdu.
        runbook_portlari = _runbook_yks_portu()
        self.assertEqual(len(runbook_portlari), 1,
                         f"SAHA_RUNBOOK tek YKS portu ilan etmeli: {runbook_portlari}")
        yks_ucu = f"{BEYAN_TAM['YKS_IP']}:{runbook_portlari.pop()}"
        self.assertEqual(_arg_degeri(self.b["birimler"][KOMUT], "--izinli-kaynak"),
                         yks_ucu,
                         "UDP eyleyici yalniz BEYAN EDILEN YKS soketini kabul etmeli")
        # Ayni kosumda telemetrinin gittigi uc ile AYNI olmali: izinli kaynak
        # telemetri hedefinden ayrisirsa komut yolu sahada tek yonlu kalir.
        self.assertEqual(_arg_degeri(self.b["birimler"][INIS], "--yks"), yks_ucu)
        self.assertEqual(_arg_degeri(self.b["birimler"][RPI], "--yks-hedef"), yks_ucu)
        self.assertEqual(float(env["KANIT_TIMEOUT"]), SARTNAME_IHA_GOREV_SURESI_S)
        self.assertEqual(env["KIP"], "udp")
        self.assertEqual(env["PIXHAWK_SERI"], "/dev/ttyACM0")
        self.assertEqual(env["NAVITAS_KOK"], KOK_VARSAYILAN, "JETSON_KILAVUZ §2 ~/navitas")
        self.assertEqual(env["PYTHON3"], PYTHON3_VARSAYILAN)

    def _k9_paket(self, b):
        gorulen = 0
        for satir in b["paket"]:
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
            self.assertIn(f"[VAR] {PY_ADI[ad]}.py", b["paket"])

    def _k9_makine(self, b, path_on=""):
        """Ana makine satirlari gercekle ayni: betigin kullandigi AYNI sinamalar (id -u, -x, -e,
        -f, PATH'te command -v) bagimsiz bash cagrisiyla tekrarlanir (path_on: kosumun shim dizinleri)."""
        gorulen = set()
        kullanici = None
        for satir in b["makine"]:
            m = re.match(r"^\[(VAR|YOK)\] (kullanici|yorumlayici|Pixhawk seri|SiK seri|kurulu) (\S+)", satir)
            self.assertIsNotNone(m, f"ana makine satiri bicimi: {satir!r}")
            durum, tur, deger = m.groups()
            if tur == "kullanici":
                kullanici = deger
                gercek = _bash_id_var(deger)
            elif tur == "yorumlayici":
                gercek = _bash_test("-x", deger)
            elif tur == "kurulu":
                gercek = _bash_test("-f", deger)
            else:
                gercek = _bash_test("-e", deger)
            self.assertEqual(durum, "VAR" if gercek else "YOK", satir)
            gorulen.add(tur)
        self.assertLessEqual({"kullanici", "yorumlayici", "Pixhawk seri", "kurulu"}, gorulen, b["makine"])
        self.assertEqual(sum(1 for s in b["makine"] if " kurulu " in s), len(b["birimler"]) - 1,
                         "cogullayici disinda her birimin kurulu .py satiri")
        mav = [s for s in b["paket"] if "mavproxy.py (PATH)" in s]
        self.assertEqual(len(mav), 1, b["paket"])
        self.assertIsNotNone(kullanici)
        on_path = f"/home/{kullanici}/.local/bin:/usr/local/bin:/usr/bin:/bin"
        if path_on:
            on_path = f"{on_path}:{path_on}"
        self.assertTrue(mav[0].startswith("[VAR]" if _bash_komut_var("mavproxy.py", on_path) else "[YOK]"), mav[0])

    def test_K9_paket_ve_ana_makine_denetimi_dogru_soyler(self):
        """[VAR]/[YOK] satirlari dosya sistemiyle ayni — hem varsayilan hem hazir makinede."""
        self._k9_paket(self.b)
        self._k9_paket(self.b_h)
        self._k9_makine(self.b)
        self._k9_makine(self.b_h, self.m.path_on)
        self.assertIn(f"[VAR] kullanici {self.m.kullanici} (birimlerde User=)", self.b_h["makine"])
        self.assertTrue(all(s.startswith("[VAR]") for s in self.b_h["makine"]), self.b_h["makine"])

    def test_K9_herhangi_YOK_eksik_ve_exit_3_beyan_tamken(self):
        """D-405: `[YOK] mavproxy` iken "KURU SONUC: tamam" yalani. Hazir makinede tek tek
        eksilt: mavproxy PATH'ten, kullanici, Pixhawk cihazi, kurulu .py — her biri 3."""
        m = self.m
        e = m.env(KIP="udp", **BEYAN_TAM, NAVITAS_TEST_PATH_ON="")   # shim bin PATH'te DEGIL
        kod, out, _ = _kos(BETIK, e)
        b = _bolumler(out)
        self.assertEqual(kod, 3, out)
        self.assertIn("[YOK] mavproxy.py (PATH)", "\n".join(b["paket"]))
        self.assertIn("[TAM] beyanlar tam", out)
        self.assertRegex(b["sonuc"], r"eksik \(beyan: tam · \[YOK\]: 1\)")
        for ek, satir in (
                ({"SERVIS_KULLANICI": "olmayan_navitas_kullanicisi"},
                 "[YOK] kullanici olmayan_navitas_kullanicisi"),
                ({"PIXHAWK_SERI": _msys(m.d / "dev" / "yok_ttyACM9")}, "[YOK] Pixhawk seri "),
                ({"PYTHON3": _msys(m.bos)}, "[YOK] yorumlayici "),
                ({"NAVITAS_KOK": _msys(m.d / "bos_kok")}, "[YOK] kurulu ")):
            with self.subTest(ek=ek):
                kod, out, _ = _kos(BETIK, m.env(KIP="udp", **BEYAN_TAM, **ek))
                b = _bolumler(out)
                self.assertEqual(kod, 3, out)
                self.assertTrue(any(s.startswith(satir) for s in b["makine"]), b["makine"])
                self.assertRegex(b["sonuc"], r"^KURU SONUC: eksik \(beyan: tam · \[YOK\]: [1-9]")

    def test_K9_bosluk_glob_iceren_deger_UYARI(self):
        """systemd ($VAR) ve bash (nohup $k) degeri boler/genisletir — --kuru soyler (D-405)."""
        kod, out, _ = _kos(BETIK, self.m.env(KIP="udp", **BEYAN_TAM, KAMERA="*"))
        b = _bolumler(out)
        self.assertEqual(kod, 0, out)
        self.assertTrue(any(s.startswith("[UYARI] KAMERA='*'") for s in b["beyan"]), b["beyan"])
        kod, out, _ = _kos(BETIK, self.m.env(KIP="udp", **BEYAN_TAM, KAMERA="/tmp/a b.mp4"))
        self.assertTrue(any(s.startswith("[UYARI] KAMERA=") for s in _bolumler(out)["beyan"]), out)
        self.assertNotIn("[UYARI]", self.out_h, "temiz degerlerde uyari yok")

    def test_K9_kilavuz_once_kuru_der(self):
        m = KILAVUZ.read_text(encoding="utf-8")
        ilk_komut = m.index("--kuru")
        self.assertLess(ilk_komut, m.index("sudo -E"),
                        "kilavuz --kuru'yu kurulumdan ONCE soylemeli")
        for ad in TUM_BIRIMLER:
            self.assertIn(ad, m, f"kilavuz {ad} birimini anmiyor")
        self.assertIn("Restart=always", m)
        self.assertIn("SERVIS_KULLANICI", m, "degisken listesinde SERVIS_KULLANICI (D-405)")
        self.assertNotIn("`enable --now`;", m, "kilavuz artik enable+restart der (D-405)")


class JetsonBaslatKuruSik(unittest.TestCase):
    """K2 — KIP=sik: seri hub kalkar, /dev/ttyUSB0'i YALNIZ hub acar."""

    @classmethod
    def setUpClass(cls):
        cls.kod, cls.out, cls.err = _kos(BETIK, {"KIP": "sik", "FOV": "78"})
        cls.b = _bolumler(cls.out)
        cls.m = _AnaMakine()
        cls.kod_h, cls.out_h, cls.err_h = _kos(BETIK, cls.m.env(KIP="sik", FOV="78"))
        cls.b_h = _bolumler(cls.out_h)

    @classmethod
    def tearDownClass(cls):
        cls.m.temizle()

    def test_K2_sik_exit_0_ve_hub_satiri_var(self):
        self.assertEqual(self.kod_h, 0, f"stdout:\n{self.out_h}\nstderr:\n{self.err_h}")
        self.assertEqual(set(self.b_h["birimler"]), set(TUM_BIRIMLER))
        self.assertTrue(any(s.startswith("[VAR] SiK seri ") for s in self.b_h["makine"]), self.b_h["makine"])
        yok = _yok_sayisi(self.b)
        self.assertEqual(self.kod, 0 if yok == 0 else 3, self.out)
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
        # SiK'te izinli kaynak = seri-hub'in KENDI UDP ucu: hub, seri hattan
        # cozdugu cerceveyi --bind ile actigi soketten tuketicilere yollar
        # (seri_hub.SeriHub docstring'i: "hub'in KENDI UDP soketi"), yani
        # eyleyiciye varan komutun kaynak ucu hub'in bind adresidir.
        # Ciplak "127.0.0.1:5100" yerine iki capa (madde 16):
        #   (1) kod otoritesi seri_hub.VARSAYILAN_BIND,
        #   (2) AYNI kosumda hub biriminin gercekten aldigi --bind.
        # Biri kaysa oteki tutmaz; kapi ciplak dizeyle gecmez.
        self.assertEqual(_arg_degeri(komut, "--izinli-kaynak"),
                         seri_hub.VARSAYILAN_BIND,
                         "SiK komutu yalniz seri-hub'in kod sozlesmesindeki ucundan gelmeli")
        self.assertEqual(_arg_degeri(komut, "--izinli-kaynak"),
                         _arg_degeri(self.b["birimler"][SERI_HUB], "--bind"),
                         "izinli kaynak, hub'in GERCEKTEN dinledigi/yolladigi uc olmali")
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

    @classmethod
    def setUpClass(cls):
        cls.m = _AnaMakine()

    @classmethod
    def tearDownClass(cls):
        cls.m.temizle()

    def test_K7_udp_beyan_eksik_cikis_3_ve_EKSIK_satirlari(self):
        kod, out, err = _kos(BETIK, self.m.env(KIP="udp"))
        self.assertEqual(kod, 3, f"stdout:\n{out}\nstderr:\n{err}")
        b = _bolumler(out)
        eksik = "\n".join(b["beyan"])
        for ad in ("FOV", "YKS_IP", "IKA_IP"):
            self.assertRegex(eksik, rf"\[EKSIK\] .*{ad}", eksik)
        self.assertRegex(b["sonuc"] or "", r"eksik \(beyan: eksik · \[YOK\]: 0\) — gercek kosum DURUR")
        # komutlar yine de basilir (once bak): kullanici ne kosulacagini gorur
        self.assertIn(RPI, b["birimler"])

    def test_K7_sik_yalniz_FOV_ister_IP_istemez(self):
        kod, out, _ = _kos(BETIK, self.m.env(KIP="sik"))
        self.assertEqual(kod, 3)
        eksik = "\n".join(_bolumler(out)["beyan"])
        self.assertRegex(eksik, r"\[EKSIK\] .*FOV")
        self.assertNotIn("YKS_IP", eksik)
        self.assertNotIn("IKA_IP", eksik)

    def test_K7_FOV_ve_ODAK_birlikte_verilmez(self):
        kod, out, _ = _kos(BETIK, self.m.env(KIP="udp", **BEYAN_TAM, ODAK="900"))
        self.assertEqual(kod, 3)
        self.assertRegex("\n".join(_bolumler(out)["beyan"]), r"\[EKSIK\] .*birlikte")

    def test_K7_bilinmeyen_KIP_cikis_1_HATA(self):
        kod, out, err = _kos(BETIK, self.m.env(KIP="wifi", **BEYAN_TAM))
        self.assertEqual(kod, 1, out)
        self.assertIn("HATA", err)
        self.assertNotIn("navitas-rpi-inference.service:", out)

    def test_K7_ODAK_verilince_fov_yerine_odak_gecer(self):
        kod, out, _ = _kos(BETIK, self.m.env(KIP="udp", YKS_IP="10.0.0.1", IKA_IP="10.0.0.2",
                                              ODAK="900", SENARYO="kirsal", KAMERA="/dev/video1"))
        self.assertEqual(kod, 0, out)
        rpi = _bolumler(out)["birimler"][RPI]
        self.assertEqual(_arg_degeri(rpi, "--odak"), "900")
        self.assertNotIn("--fov", rpi)
        self.assertEqual(_arg_degeri(rpi, "--senaryo"), "kirsal")
        self.assertEqual(_arg_degeri(rpi, "--kaynak"), "/dev/video1")
        self.assertNotIn(KAMERA_KOPRUSU, _bolumler(out)["birimler"],
                         "/dev/videoN kaynagi kamera koprusu KALDIRMAZ (Gorev K)")


class JetsonBaslatCrlf(unittest.TestCase):
    """K8 — Windows calisma agaci CRLF'tir (core.autocrlf=true, olculdu); USB kopyasi
    CR tasir. Betik + birimler CRLF'e cevrilip ayni --kuru ciktisini vermeli VE koruma
    dali (mktemp/tr/exec/trap) GERCEKTEN kosmali (D-405: eski `grep -q $'\\r'` MSYS'te
    CR gormuyordu, dal hic kosmadan test geciyordu)."""

    @staticmethod
    def _bu_bash_cr_gorur(dosya):
        """Betikle AYNI algi kalibi bu bash'te CR goruyor mu? (gormuyorsa skip, dal bozuksa FAIL)"""
        p = subprocess.run([_bash(), "-c",
                            'case "$(head -c 4096 "$1")" in *$\'\\r\'*) echo GORDU;; *) echo YOK;; esac',
                            "_", _posix(dosya)], capture_output=True, text=True, timeout=30)
        return p.stdout.strip() == "GORDU"

    def test_K8_crlf_kopya_ayni_cikti_ve_koruma_dali_KOSAR(self):
        m = _AnaMakine(crlf_paket=True)
        ml = _AnaMakine(lf_paket=True)   # LF kopya ACIKCA uretilir (calisma kopyasi autocrlf ile CRLF olabilir)
        try:
            self.assertIn(b"\r\n", m.betik.read_bytes())
            self.assertNotIn(b"\r\n", ml.betik.read_bytes())
            kod_c, out_c, err_c = _kos(m.betik, m.env(KIP="sik", FOV="78"))
            # Ayni ana makine ortami (m.env): yalniz betigin satir sonu farkli olsun,
            # env/birim bolumleri birebir kiyaslanabilsin.
            kod_l, out_l, _ = _kos(ml.betik, m.env(KIP="sik", FOV="78"))
            self.assertEqual(kod_l, 0, out_l)
            self.assertEqual(kod_c, 0, f"CRLF kopya dustu:\nstdout:\n{out_c}\nstderr:\n{err_c}")
            self.assertNotIn("\\r", err_c)
            bc, bl = _bolumler(out_c), _bolumler(out_l)
            self.assertEqual(bc["env"], bl["env"])
            self.assertEqual(bc["birimler"], bl["birimler"])
            self.assertIn(SERI_HUB, bc["birimler"])
            self.assertTrue(bc["sonuc"].startswith("KURU SONUC: tamam"), bc["sonuc"])
            # "kurmak icin" yolu PAKET dizinidir, silinen /tmp kopyasi DEGIL
            self.assertIn(f"/{m.paket.name}/jetson_baslat.sh", bc["sonuc"])
            self.assertNotIn("/tmp/tmp.", bc["sonuc"])
            isaret = re.search(r"\(CR'siz kopya: (\S+)\)", out_c.splitlines()[0])
            if isaret is None:
                if not self._bu_bash_cr_gorur(m.betik):
                    self.skipTest("YAPILAMADI: bu bash CR'i goremiyor (MSYS CR yutuyor) — "
                                  "koruma dali burada kosturulamadi")
                self.fail("bu bash CR'i GORUYOR ama koruma dali kosmadi (basligta "
                          f"'(CR'siz kopya: ...)' yok):\n{out_c.splitlines()[0]}")
            gecici = isaret.group(1)
            self.assertFalse(_bash_test("-e", gecici), f"CR'siz gecici kopya silinmedi: {gecici}")
            self.assertNotIn("(CR'siz kopya", out_l, "LF kopyada dal kosmamali")
        finally:
            m.temizle()
            ml.temizle()

    def test_K8_cr_korumasi_set_e_den_ONCE_ve_ilk_komut(self):
        """Calisma kopyasi checkout'a gore LF ya da CRLF olabilir (autocrlf) — kilit
        dosyanin EOL'u DEGIL, CR korumasinin `set -euo pipefail`ten ONCE gelmesidir:
        aksi halde CRLF kopyada `pipefail\\r` ilk satirda patlar, koruma hic kosmaz.
        Algi bash-ICI olmali (head -c + case); MSYS grep CR'i gormez (D-405)."""
        satirlar = [s.rstrip("\r") for s in
                    BETIK.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(satirlar[0], "#!/usr/bin/env bash")
        komutlar = [s for s in satirlar if s.strip() and not s.startswith("#")]
        self.assertIn("case \"$(head -c 4096 \"$0\"", komutlar[0], "CR korumasi ilk komut degil")
        self.assertIn("*$'\\r'*)", komutlar[0], "algi bash-ici case kalibi olmali")
        self.assertNotIn("grep", komutlar[0], "MSYS grep CR gormez — grep ile algi YASAK")
        self.assertIn("tr -d '\\r'", komutlar[0])
        self.assertTrue(komutlar[0].rstrip().endswith("# CRLF"),
                        "koruma satiri CR'i yutacak satir sonu yorumuyla bitmeli")
        self.assertEqual(komutlar[1], "set -euo pipefail")


class SystemdBirimleri(unittest.TestCase):
    """K3/K4 — birim dosyalari: gozcu alanlari BOLUMUYLE, siralama, ExecStart dosyalari, CONTRACTS uclari."""

    def test_K3_alti_birim_dosyasi_var(self):
        """5 MAVLink/seri birimi + kamera koprusu (Gorev K) — fazlasi/eksigi sessiz gecmez."""
        self.assertEqual({p.stem for p in BIRIM_DIZIN.glob("*.service")}, set(BIRIM_DOSYALARI))

    def test_K3_gozcu_alanlari_her_birimde_DOGRU_BOLUMDE(self):
        for ad in BIRIM_DOSYALARI:
            with self.subTest(birim=ad):
                _gozcu_kilidi(self, _birim_oku(ad), ad)

    def test_K3_tuketiciler_cogullayiciya_bagli(self):
        for ad in TUKETICILER:
            with self.subTest(birim=ad):
                u = _birim_oku(ad)["Unit"]
                self.assertIn(f"{COGULLAYICI}.service", " ".join(u.get("After", [])), ad)
                self.assertIn(f"{COGULLAYICI}.service", " ".join(u.get("Wants", [])), ad)
                self.assertIn(f"{SERI_HUB}.service", " ".join(u.get("After", [])),
                              f"{ad}: KIP=sik'te hub'dan sonra kalkmali")
        for ad in (COGULLAYICI, SERI_HUB, KAMERA_KOPRUSU):
            self.assertNotIn("Wants", _birim_oku(ad)["Unit"], f"{ad}: kimseyi cekmemeli")

    def test_K3_ExecStart_py_dosyasi_pakette_MEVCUT(self):
        """ExecStart'taki NAVITAS .py dosyasi jetson_paket/kod/ altinda olmali.
        Depoda HIC olmayan betik icin GORUNUR skip: paket bir seyi aynalayamaz."""
        for ad in BIRIM_DOSYALARI:
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


class JetsonBaslatKurKapiShim(unittest.TestCase):
    """K10 — --kur / --kapi / --dogrudan / --durdur GERCEKTEN kosar (D-405 shim yontemi).
    Paket CRLF kopyadir (USB/Windows): CR korumasi + `tr -d '\\r'` kurulum yolu da sinanir."""

    KULLANICI = "saha"   # navitas DEGIL: User=/PATH sed'inin gercekten uygulandigi gorulsun

    def _shim_komutlar(self, m, komut):
        return [s.split() for s in m.shim_satirlari() if s.startswith(komut + " ")]

    def _systemctl(self, m):
        """[(alt_komut, [args...]), ...] sirali."""
        return [(p[1], p[2:]) for p in self._shim_komutlar(m, "systemctl")]

    def test_K10_kur_root_degilse_HATA_paket_yolu_ve_hicbir_systemctl_yok(self):
        m = _AnaMakine(sbin=True, kullanici=self.KULLANICI, crlf_paket=True)
        try:
            kod, out, err = _kos(m.betik, m.env(KIP="udp", **BEYAN_TAM, SHIM_UID="1000"), "--kur")
            self.assertEqual(kod, 1, f"stdout:\n{out}\nstderr:\n{err}")
            self.assertIn("HATA: root gerekli: sudo -E bash ", err)
            self.assertIn(f"/{m.paket.name}/jetson_baslat.sh", err, "hata mesaji PAKET yolunu gostermeli")
            self.assertNotIn("/tmp/tmp.", err, "CR kopyasinda trap'in sildigi gecici dosya onerilmez")
            self.assertEqual(self._systemctl(m), [], "root degilken hicbir systemctl cagrisi yok")
            self.assertFalse(m.env_dosya.exists())
            self.assertEqual(list(m.systemd.iterdir()), [])
        finally:
            m.temizle()

    def test_K10_kur_daemon_reload_enable_RESTART_sirasi_ve_birimler_sedlenmis_CRsiz(self):
        m = _AnaMakine(sbin=True, kullanici=self.KULLANICI, crlf_paket=True)
        try:
            e = m.env(KIP="udp", **BEYAN_TAM)
            kod, out, err = _kos(m.betik, e, "--kur")
            self.assertEqual(kod, 0, f"stdout:\n{out}\nstderr:\n{err}")
            self.assertIn("[YAZILDI] " + e["ENV_DOSYA"], out)
            self.assertIn("thazirlik (bu betik):", out)
            sc = self._systemctl(m)
            altlar = [a for a, _ in sc]
            self.assertIn("daemon-reload", altlar)
            self.assertIn("enable", altlar)
            self.assertIn("restart", altlar, "D-405: `start` aktif birimde no-op — RESTART sart")
            self.assertLess(altlar.index("daemon-reload"), altlar.index("enable"))
            self.assertLess(altlar.index("enable"), altlar.index("restart"),
                            "restart daemon-reload ve enable'dan SONRA")
            self.assertNotIn("start", altlar)
            udp_birimler = [f"{b}.service" for b in (COGULLAYICI, RPI, INIS, KOMUT)]
            self.assertEqual(dict(sc)["enable"], udp_birimler, "enable: KIP=udp birimleri BASLATMA sirasinda")
            self.assertEqual(dict(sc)["restart"], udp_birimler, "restart: ayni birimler")
            self.assertTrue(any("--now" not in a for al, a in sc if al == "enable"))
            self.assertIn(("disable", ["--now", f"{SERI_HUB}.service"]), sc, "KIP=udp'de hub kapatilir")
            self.assertIn(["id", "-u"], self._shim_komutlar(m, "id"), "root denetimi")
            self.assertIn(["id", "-u", self.KULLANICI], self._shim_komutlar(m, "id"),
                          "servis kullanicisi denetimi (D-405 217/USER)")
            # env dosyasi == --kuru env bolumu (ayni beyanla)
            env_metin = m.env_dosya.read_bytes()
            self.assertNotIn(b"\r", env_metin)
            _, out_k, _ = _kos(m.betik, e)
            self.assertEqual(dict(s.split("=", 1) for s in env_metin.decode("utf-8").splitlines()),
                             _bolumler(out_k)["env"])
            # yazilan 6 birim: CR'siz, sed'lenmis, bolum kilidi korunmus
            yazilan = {p.stem for p in m.systemd.glob("*.service")}
            self.assertEqual(yazilan, set(BIRIM_DOSYALARI))
            for ad in BIRIM_DOSYALARI:
                with self.subTest(birim=ad):
                    ham = (m.systemd / f"{ad}.service").read_bytes()
                    self.assertNotIn(b"\r", ham, f"{ad}: kurulu birimde CR (tr -d yok?)")
                    a = _birim_oku_metin(ham.decode("utf-8"))
                    _gozcu_kilidi(self, a, ad, env_dosya=e["ENV_DOSYA"], kullanici=self.KULLANICI)
                    s = a["Service"]
                    self.assertEqual(s.get("WorkingDirectory"), [e["NAVITAS_KOK"]], ad)
                    ex = s["ExecStart"][0]
                    self.assertNotIn(KOK_VARSAYILAN, ex, ad)
                    self.assertNotIn("/home/navitas/", "\n".join(s.get("Environment", [])), ad)
                    if ad == COGULLAYICI:
                        self.assertIn(f"PATH=/home/{self.KULLANICI}/.local/bin:/usr/local/bin:/usr/bin:/bin",
                                      s.get("Environment", []), ad)
                    elif ad == KAMERA_KOPRUSU:
                        self.assertTrue(ex.startswith("/usr/bin/env ${KAMERA_PYTHON} "
                                                      + e["NAVITAS_KOK"] + "/"), ex)
                    else:
                        self.assertTrue(ex.startswith(e["PYTHON3"] + " " + e["NAVITAS_KOK"] + "/"), ex)
            # D-405 repro: beyan degisti, ikinci --kur -> env yenilenir VE yine restart
            m.shim_sifirla()
            e2 = m.env(KIP="udp", YKS_IP="10.0.0.9", IKA_IP="10.0.0.2", FOV="90")
            kod, out, err = _kos(m.betik, e2, "--kur")
            self.assertEqual(kod, 0, f"stdout:\n{out}\nstderr:\n{err}")
            env2 = m.env_dosya.read_text(encoding="utf-8")
            self.assertIn("RPI_EK_ARGS=--fov 90\n", env2)
            self.assertIn("RPI_TELSIZ_ARGS=--yks-hedef 10.0.0.9:5005 --ika-hedef 10.0.0.2:5006\n", env2)
            sc2 = self._systemctl(m)
            self.assertIn(("restart", udp_birimler), sc2, "ikinci --kur: yeni beyan canli surece uygulanmali")
        finally:
            m.temizle()

    def test_K10_birim_kurulum_hatti_tr_d_CR_ile_baslar_METIN_KILIDI(self):
        """birimleri_kur'daki birim yazma hatti `tr -d '\\r' < <birim>` ile BASLAMALI.
        NEDEN metin kilidi (D-405 mutasyon M2): MSYS GNU sed 4.9 metin kipinde CR'i KENDISI
        yutar (olculdu: printf 'a\\r\\n' | sed '' -> 'a\\n'); Windows'ta `tr -d` kaldirilsa
        kurulu birim yine CR'siz cikar, davranissal test mutanti goremez. Jetson/Linux'ta
        sed CR'i korur: `$`-capali User=/EnvironmentFile= sed'leri eslesmez, birim CR ile
        yazilir. Davranissal kilit asagida (sed CR koruyorsa kosar)."""
        satirlar = [s.rstrip("\r") for s in BETIK.read_text(encoding="utf-8").splitlines()]
        hat = [s for s in satirlar if "birim_dosyasi \"$b\"" in s and "> \"$SYSTEMD_DIZIN/" not in s]
        self.assertEqual(len(hat), 1, f"birimleri_kur yazma hatti tek satirda bulunamadi: {hat}")
        self.assertRegex(hat[0], r"^\s*tr -d '\\r' < \"\$\(birim_dosyasi \"\$b\"\)\" \\$", hat[0])
        # ve o hattin sonu SYSTEMD_DIZIN'e yazar (sed satirlari arada)
        i = satirlar.index(hat[0])
        blok = "\n".join(satirlar[i:i + 8])
        self.assertIn('> "$SYSTEMD_DIZIN/$b.service"', blok)
        self.assertIn("sed -e", blok)

    @staticmethod
    def _bu_sed_cr_korur():
        p = subprocess.run([_bash(), "-c", "printf 'a\\r\\n' | sed -e 's/x/y/' | od -An -c"],
                           capture_output=True, text=True, timeout=30)
        return "\\r" in p.stdout

    def test_K10_kur_CRLF_birimler_kurulunca_CRsiz_DAVRANIS(self):
        """CRLF paketten kurulan birimlerde CR yok — bu bash'in sed'i CR'i kendisi yutuyorsa
        (MSYS) olculemez: GORUNUR skip, sessiz gecis degil."""
        if not self._bu_sed_cr_korur():
            self.skipTest("YAPILAMADI: bu ortamin sed'i CR'i kendisi yutuyor (MSYS) — `tr -d` "
                          "kilidi burada davranissal olculemez; metin kilidi ustte, Linux'ta olculur")
        m = _AnaMakine(sbin=True, kullanici=self.KULLANICI, crlf_paket=True)
        try:
            kod, out, err = _kos(m.betik, m.env(KIP="sik", FOV="78"), "--kur")
            self.assertEqual(kod, 0, f"stdout:\n{out}\nstderr:\n{err}")
            for ad in BIRIM_DOSYALARI:
                ham = (m.systemd / f"{ad}.service").read_bytes()
                self.assertNotIn(b"\r", ham, f"{ad}: kurulu birimde CR")
                a = _birim_oku_metin(ham.decode("utf-8"))
                self.assertEqual(a["Service"].get("User"), [self.KULLANICI], ad)
        finally:
            m.temizle()

    def test_K10_kapi_uc_uc_AYNI_ANDA_3_of_3_tuketiciler_kalkar(self):
        m = _AnaMakine(sbin=True, kullanici=self.KULLANICI, crlf_paket=True)
        try:
            e = m.env(KIP="sik", FOV="78", FAKE_SURE="1.5")
            kod, out, err = _kos(m.betik, e, "--kapi", timeout=120)
            self.assertEqual(kod, 0, f"stdout:\n{out}\nstderr:\n{err}")
            for uc in MAV_UCLAR:
                self.assertIn(f"[GECTI] {uc}", out)
                self.assertIn(f"## kapi: {uc} (log: ", out)
            self.assertNotIn("[DUSTU]", out)
            self.assertIn("GECTI (sahte)", out, "uc logu ciktiya basilir")
            self.assertIn("thazirlik (bu betik, kapi dahil):", out)
            for port in ("14550", "14551", "14552"):
                self.assertEqual((m.log / "kapi" / f"{port}.rc").read_text().strip(), "0")
            sc = self._systemctl(m)
            self.assertEqual(sc[0][0], "daemon-reload")
            for b in TUKETICILER:
                self.assertIn(("stop", [f"{b}.service"]), sc, "onceki tuketiciler 1455N uclarini birakir")
            for b in (COGULLAYICI, SERI_HUB):
                self.assertIn(("enable", [f"{b}.service"]), sc)
                self.assertIn(("restart", [f"{b}.service"]), sc, f"{b}: PIXHAWK/SIK degismis olabilir (D-405)")
            tuketici_birimler = [f"{b}.service" for b in TUKETICILER]
            self.assertIn(("enable", tuketici_birimler), sc)
            self.assertIn(("restart", tuketici_birimler), sc)
            # uc sudo -u <kullanici> <PYTHON3> <kok>/scripts/mavlink_dogrula.py --mavlink <uc> --sysid 1
            sudolar = self._shim_komutlar(m, "sudo")
            self.assertEqual(len(sudolar), 3, sudolar)
            beklenen = {tuple(["sudo", "-u", self.KULLANICI, e["PYTHON3"],
                               e["NAVITAS_KOK"] + "/scripts/mavlink_dogrula.py",
                               "--mavlink", uc, "--sysid", "1"]) for uc in MAV_UCLAR}
            self.assertEqual({tuple(s) for s in sudolar}, beklenen)
            # AYNI ANDA: her ucun baslangici, en erken bitisten ONCE (CONTRACTS §7.4)
            z = m.dogrula_zamanlari()
            self.assertEqual(set(z), {"14550", "14551", "14552"}, z)
            self.assertTrue(all(b is not None and s is not None for b, s in z.values()), z)
            en_gec_baslangic = max(b for b, _ in z.values())
            en_erken_bitis = min(s for _, s in z.values())
            self.assertLess(en_gec_baslangic, en_erken_bitis,
                            f"uclar SIRALI kosmus (paralel degil): {z}")
            # tuketici restart'i tum dogrulamalar bittikten SONRA
            ham = [s for s in m.shim_log.read_text(encoding="utf-8").splitlines()
                   if " systemctl restart " + tuketici_birimler[0] in s]
            self.assertEqual(len(ham), 1, ham)
            self.assertGreater(float(ham[0].split(" ", 1)[0]), max(s for _, s in z.values()))
        finally:
            m.temizle()

    def test_K10_kapi_2_of_3_HATA_tuketiciler_BASLATILMAZ_eski_rc_sayilmaz(self):
        m = _AnaMakine(sbin=True, kullanici=self.KULLANICI, crlf_paket=True)
        try:
            # eski kosumdan kalan "gecti" rc dosyasi: yeni kosum bunu SAYMAMALI
            (m.log / "kapi").mkdir(parents=True)
            (m.log / "kapi" / "14551.rc").write_text("0\n")
            e = m.env(KIP="udp", **BEYAN_TAM, FAKE_SURE="1", FAKE_DUSEN="udp:127.0.0.1:14551")
            kod, out, err = _kos(m.betik, e, "--kapi", timeout=120)
            self.assertEqual(kod, 1, f"stdout:\n{out}\nstderr:\n{err}")
            self.assertIn("HATA: kapi 2/3 — tuketiciler BASLATILMADI", err)
            self.assertIn("[DUSTU] udp:127.0.0.1:14551 (rc=1)", out)
            self.assertIn("[GECTI] udp:127.0.0.1:14550", out)
            self.assertIn("[GECTI] udp:127.0.0.1:14552", out)
            self.assertIn("DUSTU (sahte)", out)
            self.assertNotIn("thazirlik", out)
            self.assertEqual((m.log / "kapi" / "14551.rc").read_text().strip(), "1")
            sc = self._systemctl(m)
            self.assertIn(("restart", [f"{COGULLAYICI}.service"]), sc)
            for alt, args in sc:
                if alt in ("enable", "restart", "start"):
                    for b in TUKETICILER:
                        self.assertNotIn(f"{b}.service", args,
                                         f"kapi 2/3 iken tuketici {alt}: {args}")
            self.assertEqual(len(self._shim_komutlar(m, "sudo")), 3, "uc uc yine de denenir")
        finally:
            m.temizle()

    def test_K10_dogrudan_glob_GENISLEMEZ_ve_durdur_oldurur(self):
        """--kuru '--kaynak *' derken --dogrudan 'codes comms ...' kosuyordu (D-405: set -f).
        Sahte python3 ARGV'yi loga yazar; --durdur nohup pid'lerini oldurur."""
        m = _AnaMakine()   # sbin YOK: gercek id/kullanici, systemctl yok -> nohup yolu
        try:
            e = m.env(KIP="udp", **BEYAN_TAM, KAMERA="*", FAKE_SLEEP="15")
            kod, out, err = _kos(m.betik, e, "--dogrudan", timeout=120)
            self.assertEqual(kod, 0, f"stdout:\n{out}\nstderr:\n{err}")
            self.assertIn("GOZCU YOK", out)
            self.assertIn(f"[BASLAT] {RPI}: ", out)
            self.assertIn("--kaynak *", out)
            rpi_log = m.log / f"{RPI}.log"
            son = time.time() + 10
            while time.time() < son:
                if rpi_log.is_file() and "ARGV[--kaynak]" in rpi_log.read_text(encoding="utf-8", errors="replace"):
                    break
                time.sleep(0.2)
            self.assertTrue(rpi_log.is_file(), f"{rpi_log} yok")
            argv = rpi_log.read_text(encoding="utf-8", errors="replace").splitlines()
            self.assertIn("ARGV[--kaynak]", argv, argv)
            self.assertEqual(argv[argv.index("ARGV[--kaynak]") + 1], "ARGV[*]",
                             f"glob genisledi (set -f yok?): {argv}")
            self.assertNotIn("ARGV[codes]", argv)
            for b in (COGULLAYICI, RPI, INIS, KOMUT):
                self.assertTrue((m.log / f"{b}.pid").is_file(), f"{b}.pid yok")
            self.assertFalse((m.log / f"{SERI_HUB}.pid").exists(), "KIP=udp'de hub kalkmaz")
            kod, out, err = _kos(m.betik, e, "--durdur", timeout=60)
            self.assertEqual(kod, 0, f"stdout:\n{out}\nstderr:\n{err}")
            for b in (COGULLAYICI, RPI, INIS, KOMUT):
                self.assertIn(f"[OLDURULDU] {b} (nohup)", out)
                self.assertFalse((m.log / f"{b}.pid").exists(), f"{b}.pid silinmedi")
        finally:
            time.sleep(0.5)
            m.temizle()


class KameraKoprusuBirimi(unittest.TestCase):
    """K11 — Gorev K (SAHA_HAZIRLIK_PLANI_20260903 §1.4): Jetson Nano'da CSI IMX477
    yalniz sistem Python 3.6 + GStreamer'li sistem OpenCV ile okunur; rpi_inference
    (Py>=3.8 venv) kopruden okur. KAMERA=http://127.0.0.1:<port>/video verilince
    navitas-kamera-koprusu KAMERA_PYTHON ile kalkar, rpi_inference ayni URL'yi alir."""

    def setUp(self):
        # D-405: --kuru artik ana makinedeki her eksigi gorur ve [YOK] varsa 3 verir.
        # Kamera kapilarini gelistirici PC'sinin tesadufi kurulumuna baglamamak icin
        # gercek betigi, tum dosya/yorumlayici/cihazlari bulunan sahte Jetson'da kos.
        self.m = _AnaMakine(sbin=True, kullanici="saha")

    def tearDown(self):
        self.m.temizle()

    def _kuru_hazir(self, **ek):
        beyan = {"KIP": "udp", **BEYAN_TAM, "KAMERA": KOPRU_URL}
        beyan.update(ek)
        env = self.m.env(**beyan)
        kod, out, err = _kos(self.m.betik, env)
        return env, kod, out, err, _bolumler(out)

    def test_K11_kopru_birimi_kalkar_ve_rpi_ayni_urlyi_okur(self):
        env, kod, out, err, b = self._kuru_hazir()
        self.assertEqual(kod, 0, f"stdout:\n{out}\nstderr:\n{err}")
        self.assertEqual(_yok_sayisi(b), 0, out)
        self.assertEqual(set(b["birimler"]), {COGULLAYICI, KAMERA_KOPRUSU, *TUKETICILER})
        sira = list(b["birimler"])
        self.assertLess(sira.index(KAMERA_KOPRUSU), sira.index(RPI),
                         "kopru rpi_inference'tan ONCE kalkmali")
        kopru = b["birimler"][KAMERA_KOPRUSU]
        self.assertTrue(kopru.startswith(f"/usr/bin/env {env['KAMERA_PYTHON']} "), kopru)
        self.assertIn(env["NAVITAS_KOK"] + "/scripts/kamera_koprusu.py", kopru)
        self.assertEqual(_arg_degeri(kopru, "--port"), str(kamera_koprusu.VARSAYILAN_PORT))
        self.assertEqual(_arg_degeri(b["birimler"][RPI], "--kaynak"), KOPRU_URL)
        self.assertEqual(b["env"]["KAMERA_PYTHON"], env["KAMERA_PYTHON"])
        self.assertEqual(int(b["env"]["KAMERA_KOPRU_PORT"]), kamera_koprusu.VARSAYILAN_PORT)
        self.assertEqual(b["env"].get("KAMERA_KOPRU_ARGS", ""), "")
        # K5 kalibi: kuru satiri == birim ExecStart'i (bagimsiz Python yerine-koyma)
        beklenen = _exec_start(KAMERA_KOPRUSU)
        beklenen = beklenen.replace(KOK_VARSAYILAN, b["env"]["NAVITAS_KOK"])
        beklenen = beklenen.replace(PYTHON3_VARSAYILAN, b["env"]["PYTHON3"])
        beklenen = re.sub(r"\$\{(\w+)\}|\$(\w+)",
                          lambda m: b["env"][m.group(1) or m.group(2)], beklenen)
        self.assertEqual(" ".join(kopru.split()), " ".join(beklenen.split()))
        self.assertIn("[VAR] kamera_koprusu.py", b["paket"])
        self.assertIn("[TAM] beyanlar tam", out)

    def test_K11_kopru_sistem_pythonda_kalir_PYTHON3_venve_ezilse_de(self):
        """Nano'da PYTHON3 = venv (ultralytics); kopru GStreamer icin SISTEM Python ister."""
        venv_yolu = self.m.bin / "venv38-python"
        self.m._shim(venv_yolu, _SHIM_PYTHON3)
        venv = _msys(venv_yolu)
        env, kod, out, err, b = self._kuru_hazir(PYTHON3=venv)
        self.assertEqual(kod, 0, f"stdout:\n{out}\nstderr:\n{err}")
        self.assertTrue(b["birimler"][RPI].startswith(venv + " "), b["birimler"][RPI])
        self.assertTrue(b["birimler"][KAMERA_KOPRUSU].startswith(
            f"/usr/bin/env {env['KAMERA_PYTHON']} "),
                         b["birimler"][KAMERA_KOPRUSU])
        self.assertNotIn(venv, b["birimler"][KAMERA_KOPRUSU])
        self.assertEqual(b["env"]["PYTHON3"], venv)
        self.assertEqual(b["env"]["KAMERA_PYTHON"], env["KAMERA_PYTHON"])
        # KAMERA_PYTHON da ezilebilir (baska sistem python yolu) — o zaman kopru onu kosar
        kamera_python_yolu = self.m.bin / "python3.6"
        self.m._shim(kamera_python_yolu, _SHIM_PYTHON3)
        kamera_python = _msys(kamera_python_yolu)
        _, kod, out, _, b = self._kuru_hazir(KAMERA_PYTHON=kamera_python)
        self.assertEqual(kod, 0, out)
        self.assertTrue(b["birimler"][KAMERA_KOPRUSU].startswith(
            f"/usr/bin/env {kamera_python} "))

    def test_K11_port_urlden_gelir_ve_yanlis_url_fail_closed(self):
        _, kod, out, _, b = self._kuru_hazir(KAMERA="http://127.0.0.1:9090/video")
        self.assertEqual(kod, 0, out)
        self.assertEqual(_arg_degeri(b["birimler"][KAMERA_KOPRUSU], "--port"), "9090")
        self.assertEqual(b["env"]["KAMERA_KOPRU_PORT"], "9090")
        self.assertEqual(_arg_degeri(b["birimler"][RPI], "--kaynak"), "http://127.0.0.1:9090/video")
        for kotu in ("http://127.0.0.1:9090/kare.jpg", "http://127.0.0.1:9090",
                      "http://127.0.0.1:abc/video", "http://localhost:8080/durum"):
            with self.subTest(KAMERA=kotu):
                _, kod, out, err, _ = self._kuru_hazir(KAMERA=kotu)
                self.assertEqual(kod, 1, f"stdout:\n{out}\nstderr:\n{err}")
                self.assertIn("HATA", err)
                self.assertNotIn("navitas-rpi-inference.service:", out,
                                  "fail-closed: hatali KAMERA ile komut basilmaz")

    def test_K11_loopback_disi_kaynaklar_kopru_kaldirmaz(self):
        """USB (UVC) yedek `--kaynak 0` ve DroidCam WiFi kopru istemez (plan §1.4 yedek)."""
        for kaynak in ("0", "/dev/video1", "http://192.168.1.42:4747/video"):
            with self.subTest(KAMERA=kaynak):
                _, kod, out, _, b = self._kuru_hazir(KAMERA=kaynak)
                self.assertEqual(kod, 0, out)
                self.assertNotIn(KAMERA_KOPRUSU, b["birimler"])
                self.assertEqual(_arg_degeri(b["birimler"][RPI], "--kaynak"), kaynak)
                self.assertEqual(int(b["env"]["KAMERA_KOPRU_PORT"]), kamera_koprusu.VARSAYILAN_PORT)

    def test_K11_sik_kipinde_hub_ve_kopru_birlikte(self):
        _, kod, out, _, b = self._kuru_hazir(KIP="sik")
        self.assertEqual(kod, 0, out)
        self.assertEqual(set(b["birimler"]), set(BIRIM_DOSYALARI))
        self.assertEqual(_arg_degeri(b["birimler"][RPI], "--kaynak"), KOPRU_URL)
        self.assertEqual(_arg_degeri(b["birimler"][RPI], "--yks-hedef"), "127.0.0.1:5100")
        self.assertNotIn("/dev/tty", b["birimler"][KAMERA_KOPRUSU])

    def test_K11_birim_dosyasi_KAMERA_PYTHON_ile_ve_gozcu(self):
        a = _birim_oku(KAMERA_KOPRUSU)
        _gozcu_kilidi(self, a, KAMERA_KOPRUSU)
        u, s = a["Unit"], a["Service"]
        k = s["ExecStart"][0]
        # systemd: ExecStart'in ilk sozcugu degisken OLAMAZ -> /usr/bin/env ${KAMERA_PYTHON}
        self.assertTrue(k.startswith("/usr/bin/env ${KAMERA_PYTHON} "), k)
        self.assertIn("/home/navitas/navitas/scripts/kamera_koprusu.py", k)
        self.assertIn("--port ${KAMERA_KOPRU_PORT}", k)
        self.assertIn("$KAMERA_KOPRU_ARGS", k)
        self.assertNotIn("/usr/bin/python3", k,
                         "yorumlayici sabit yazilmaz: birimleri_kur sed'i onu PYTHON3'e cevirirdi")
        self.assertIn("video", " ".join(s.get("SupplementaryGroups", [])), "nvargus: video grubu")
        self.assertNotIn("DISPLAY", " ".join(s.get("Environment", [])))
        self.assertNotIn("Wants", u)
        metin = (BIRIM_DIZIN / f"{KAMERA_KOPRUSU}.service").read_text(encoding="utf-8")
        self.assertIn("nvarguscamerasrc", metin)
        self.assertIn("3.6", metin)
        self.assertTrue((KOK / "scripts" / "kamera_koprusu.py").is_file())
        self.assertTrue((KOD / "kamera_koprusu.py").is_file(), "paket kopruyu tasimali")

    def test_K11_aktif_kopru_kurulumda_enable_ve_RESTART_alir(self):
        beyan = {"KIP": "udp", **BEYAN_TAM, "KAMERA": KOPRU_URL}
        env = self.m.env(**beyan)
        kod, out, err = _kos(self.m.betik, env, "--kur")
        self.assertEqual(kod, 0, f"stdout:\n{out}\nstderr:\n{err}")
        systemctl = [s.split()[1:] for s in self.m.shim_satirlari()
                     if s.startswith("systemctl ")]
        etkin = [f"{ad}.service" for ad in (COGULLAYICI, KAMERA_KOPRUSU, *TUKETICILER)]
        self.assertIn(["enable", *etkin], systemctl)
        self.assertIn(["restart", *etkin], systemctl,
                      "kamera koprusu yeni beyanla canli surece RESTART edilmelidir (D-405)")
        kurulu = _birim_oku_metin(
            (self.m.systemd / f"{KAMERA_KOPRUSU}.service").read_text(encoding="utf-8"))
        _gozcu_kilidi(self, kurulu, KAMERA_KOPRUSU,
                      env_dosya=env["ENV_DOSYA"], kullanici=self.m.kullanici)
        ex = kurulu["Service"]["ExecStart"][0]
        self.assertTrue(ex.startswith("/usr/bin/env ${KAMERA_PYTHON} "
                                      + env["NAVITAS_KOK"] + "/scripts/kamera_koprusu.py"), ex)
        env_metin = self.m.env_dosya.read_text(encoding="utf-8")
        self.assertIn(f"KAMERA_PYTHON={env['KAMERA_PYTHON']}\n", env_metin)
        self.assertIn(f"KAMERA_KOPRU_PORT={kamera_koprusu.VARSAYILAN_PORT}\n", env_metin)

    def test_K11_kopru_sabitleri_koddan(self):
        """8080 ve /video betikte CIPLAK degil: kamera_koprusu ile AYNI (madde 16)."""
        metin = BETIK.read_text(encoding="utf-8")
        m = re.search(r"^KAMERA_KOPRU_PORT_VARSAYILAN=(\d+)", metin, re.M)
        self.assertIsNotNone(m, "betikte KAMERA_KOPRU_PORT_VARSAYILAN yok")
        self.assertEqual(int(m.group(1)), kamera_koprusu.VARSAYILAN_PORT)
        m = re.search(r'^KAMERA_KOPRU_YOL="([^"]+)"', metin, re.M)
        self.assertIsNotNone(m, "betikte KAMERA_KOPRU_YOL yok")
        self.assertEqual(m.group(1), kamera_koprusu.VIDEO_YOLU)
        self.assertEqual(KOPRU_URL, f"http://127.0.0.1:{kamera_koprusu.VARSAYILAN_PORT}/video")


if __name__ == "__main__":
    unittest.main()
