"""T210 — TEST SÜİTİ SÜREÇ NÖBETÇİSİ: alt süreç ağacı kapatma + UDP dinleyici sayımı.

NEDEN (7 Eylül gecesi, `results/gece_20260907/sizinti_surecleri_0207.txt`):
tam süit her koşulduğunda `yks_gui.py --fda --ika 10.0.0.2:5006 …` ve
`ika_nav.py comms --yks 10.0.0.1:5005` süreçleri CANLI kalıyor, UDP 5005/5006'yı
tutuyor ve bir SONRAKİ süit `test_p8_sim_katmani.test_comms_loopback_gecer`
`WinError 10013` ile düşüyordu (D-427 ve D-430'un ortam kusuru sanılan kökü).

Ölçülen mekanizma (`results/gece_20260907/g1b_surec_sizintisi/deney_agac.txt`):
`subprocess.run(..., timeout=N)` zaman aşımında YALNIZ doğrudan çocuğu
öldürür (`TerminateProcess`). Windows'ta venv `python.exe` bir BAŞLATICIDIR
(venvlauncher; gerçek yorumlayıcıyı çocuk olarak açar). `saha_baslat.py`
kendi içinden `yks_gui`/`ika_nav`'ı `Popen` ile açar; zaman aşımında zincirin
ilk halkası ölür, torunlar (başlatıcı + gerçek yorumlayıcı) Windows'ta yetim
kalır ve dinlemeye devam eder. Bu modül ağacı **bütün olarak** kapatır
(`taskkill /T /F`; POSIX'te oturum grubuna SIGKILL) ve dinleyici sayımıyla
sızıntıyı ölçülebilir kılar.

Yalnız test yardımcısıdır; üretim kodu bu modülü içe almaz.

KESIF MUAFIYETI: test DEGIL, yardimci modul — `kos_agac_kapat` ve `udp_dinleyenler`'i `test_runbook_komutlari_kosuyor.py` ile `test_zz_nobetci_surec_sizintisi.py` ice alir; kendi basina kapi degildir (T120 kurali: `test_` onekli olmayan dosya test tasimaz).
KOSUM: O:\\navitas-local-train\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_zz_nobetci_surec_sizintisi.py" -v  (tests/surec_nobetcisi.py bu kosumda ice alinir ve pozitif kontrolle sinanir)
"""

import os
import signal
import subprocess
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
if str(KOK / "scripts") not in sys.path:
    sys.path.insert(0, str(KOK / "scripts"))

import saha_baslat  # noqa: E402  (istasyon uçları buradan; çıplak port yok)

WINDOWS = sys.platform.startswith("win")


def nobet_portlari():
    """Nöbet tutulan UDP portları — istasyon kartındaki uçlardan türetilir.

    5005 (YKS), 5006 (İKA), 5007 (İHA komut alıcı) burada YAZILMAZ;
    `scripts/saha_baslat.KART_*` uçlarından okunur ki sözleşme değişince
    nöbetçi kendiliğinden izler.
    """
    portlar = set()
    for uc in (saha_baslat.KART_YKS_HEDEF, saha_baslat.KART_IKA_HEDEF,
               saha_baslat.KART_IHA_HEDEF):
        portlar.add(uc.rsplit(":", 1)[1])
    return frozenset(portlar)


def udp_dinleyenler(portlar=None):
    """`netstat -ano -p udp` satırlarından (yerel_adres, pid) kümesi.

    Windows dışında `None` döner (ÖLÇÜLEMEDİ — çağıran skipTest eder).
    Sayım değil KÜME döner: "biri kapandı, biri sızdı" da yakalansın.
    """
    if not WINDOWS:
        return None
    portlar = nobet_portlari() if portlar is None else frozenset(portlar)
    q = subprocess.run(["netstat", "-ano", "-p", "udp"], capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    bulunan = set()
    for satir in q.stdout.splitlines():
        parca = satir.split()
        if len(parca) < 4 or parca[0].upper() != "UDP":
            continue
        yerel, pid = parca[1], parca[-1]
        if yerel.rsplit(":", 1)[-1] in portlar:
            bulunan.add((yerel, pid))
    return frozenset(bulunan)


def surec_komutu(pid):
    """Sızan PID'in komut satırı (yalnız hata mesajı için; ölçülemezse '?')."""
    if not WINDOWS:
        return "?"
    try:
        q = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             f"(Get-CimInstance Win32_Process -Filter 'ProcessId={int(pid)}')"
             ".CommandLine"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=20)
        return (q.stdout or "").strip() or "?"
    except (OSError, ValueError, subprocess.SubprocessError):
        return "?"


def agaci_oldur(p):
    """`p` ve TÜM torunlarını öldür (Windows: taskkill /T /F; POSIX: killpg).

    `p.kill()` yalnız doğrudan çocuğu vurur — ölçülen sızıntının kökü budur.
    Ağaç, ebeveyn bağları hâlâ canlıyken kapatılmalıdır (bu yüzden zaman
    aşımının hemen ardından çağrılır).
    """
    if p.poll() is not None:
        return
    if WINDOWS:
        subprocess.run(["taskkill", "/PID", str(p.pid), "/T", "/F"],
                       capture_output=True)
    else:
        try:
            os.killpg(os.getpgid(p.pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
    try:
        p.kill()   # taskkill bulunamadıysa bile doğrudan çocuk düşsün
    except OSError:
        pass
    try:
        p.wait(timeout=15)
    except subprocess.TimeoutExpired:
        pass


def kos_agac_kapat(komut, timeout, **popen_kw):
    """`subprocess.run(capture_output=True, timeout=…)` eşdeğeri; zaman aşımında
    ağacı KESİN kapatır.

    Döner: (çıkış_kodu, stdout, stderr). Zaman aşımında çıkış kodu 124'tür
    (süreç kalktı ve yaşıyordu — runbook kapısı için istenen durum).
    """
    popen_kw.setdefault("stdout", subprocess.PIPE)
    popen_kw.setdefault("stderr", subprocess.PIPE)
    popen_kw.setdefault("text", True)
    popen_kw.setdefault("encoding", "utf-8")
    popen_kw.setdefault("errors", "replace")
    if not WINDOWS:
        popen_kw.setdefault("start_new_session", True)
    p = subprocess.Popen(komut, **popen_kw)
    try:
        try:
            out, err = p.communicate(timeout=timeout)
            return p.returncode, out or "", err or ""
        except subprocess.TimeoutExpired:
            agaci_oldur(p)
            # Ağaç öldüğü için borular kapanır; biriken çıktı şimdi okunur.
            out, err = p.communicate()
            return 124, out or "", err or ""
    finally:
        agaci_oldur(p)
