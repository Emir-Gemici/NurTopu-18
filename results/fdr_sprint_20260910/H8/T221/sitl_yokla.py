#!/usr/bin/env python3
"""T221 · K11 — Bu makinede ArduPilot SITL (ArduPlane) provasi kosulabilir mi? OLCUM, kurulum DEGIL.

Hicbir sey KURMAZ, hicbir ikili CALISTIRMAZ. Yalniz sunlari olcer ve basar:
  1. PATH'te SITL / MAVProxy / konteyner araclari (shutil.which)
  2. WSL dagitim kaydi (HKCU\\...\\Lxss, winreg ile salt okuma; wsl.exe CALISTIRILMAZ)
  3. venv'de SITL'e yarayan pip paketleri (importlib.metadata)
  4. ArduPilot firmware sunucusunda Plane 4.5.7 icin hangi SITL ikilileri var (HTTP liste)
  5. features.txt'te HAL_PARACHUTE_ENABLED satiri (Pixhawk6C ve SITL_x86_64_linux_gnu)
  6. --ikili verilirse SITL ikilisinde dizge taramasi (CALISTIRILMADAN; bayt sayimi)

KULLANIM (PC, depo venv'i; cikti kanit dosyasidir):
  python -B results/fdr_sprint_20260910/H8/T221/sitl_yokla.py [--ikili YOL] \\
      > results/fdr_sprint_20260910/H8/T221/sitl_yoklama.txt

EK TARAMA (T221-D, D-449 · 10 Eyl): --ek --ikili YOL yalniz "## 6.1" blogunu basar (1-5 ve HUKUM
YOK): genisletilmis dizge listesi + features.txt PARACHUTE satir numaralari ve '!' orani + README
SS6.6 olcut 1 gerekcesinin Plane-4.5.7 kaynak satirlari. Blok sitl_yoklama.txt SS6'nin sonuna,
"## HUKUM"dan once eklenir; T221'in 12:37 kosumunun ciktisi YERINDE kalir (yeniden kosulmaz).

CIKIS: 0 = SITL kosulabilir (en az bir yol VAR) | 2 = OLCULEMEDI (yol yok). Hukum son satirdadir.
--ek: 0 (hukum basmaz).
"""

import argparse
import hashlib
import importlib.metadata
import platform
import re
import shutil
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

for _akim in (sys.stdout, sys.stderr):
    try:
        _akim.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

SUNUCU = "https://firmware.ardupilot.org/Plane/stable-4.5.7/"
ARACLAR = ("sim_vehicle.py", "arduplane", "arduplane.exe", "ArduPlane.elf", "mavproxy.py",
           "MAVProxy.exe", "dronekit-sitl", "docker", "podman", "wsl.exe")
PAKETLER = ("dronekit", "dronekit-sitl", "MAVProxy", "pymavlink")
ELF_BASLIGI = b"\x7fELF"
# Ikilide CALISTIRMADAN sayilan dizgeler. "SER2_RTSCTS" ve sonrasi T221-D eki (D-449, 10 Eyl):
#   SER2_RTSCTS   README SS6.6 olcut 1 beklenen-yok adi BRD_SER2_RTSCTS'in var_info adi (grup oneki
#                 "BRD_" ayri dizgedir); AP_BoardConfig.cpp #ifdef HAL_HAVE_RTSCTS_SERIAL2 -> 0 beklenir
#   RTSCTS        butun SERn_RTSCTS adlari ve baska RTSCTS dizgeleri
#   SAFETY_DEFLT  POZITIF KONTROL: ayni AP_BoardConfig var_info'sunda KOSULSUZ ad. >= 1 degilse
#                 "SER2_RTSCTS 0" tarama yonteminin korlugu olabilir (adlar duz dizge mi?)
#   Chute has no channel  AP_Parachute.cpp arming_checks mesaji
#   Parachute: Too low    ArduPlane/parachute.cpp parachute_manual_release mesaji
#   Ignored unknown param AP_Param.cpp read_param_defaults_file mesaji (yalniz ENABLE_DEBUG): 0 ise
#                 SITL .param'daki bilinmeyen adi SESSIZ atlar -> olcut 1 sayimi mesajla yapilamaz
DIZGELER = (b"CHUTE_",b"AP_Parachute", b"Parachute: Released", b"TKOFF_THR_MINACC",
            b"TKOFF_TDRAG_ELEV", b"SHOVE_X", b"FS_LONG_ACTN", b"ArduPlane V4.5.7",
            b"SER2_RTSCTS", b"RTSCTS", b"SAFETY_DEFLT", b"Chute has no channel",
            b"Parachute: Too low", b"Ignored unknown param")

# README SS6.6 olcut 1 gerekcesinin (beklenen-yok) ve CHUTE_* on hukmunun Plane-4.5.7 kaynak satirlari.
# Satir numarasi elle YAZILMAZ: dosya etiketten indirilir, desen aranir, eslesen satir (ve istenirse
# ondan onceki k satir) numarasiyla basilir. (yol, ((desen, onceki_k), ...))
KAYNAK_URL = "https://raw.githubusercontent.com/ArduPilot/ardupilot/Plane-4.5.7/{yol}"
KAYNAK_SATIRLARI = (
    ("libraries/AP_BoardConfig/AP_BoardConfig.cpp",
     ((r"^#if AP_FEATURE_RTSCTS", 0), (r"^#ifdef HAL_HAVE_RTSCTS_SERIAL2", 0),
      (r'"SER2_RTSCTS"', 0), (r'"SAFETY_DEFLT"', 0))),
    ("libraries/AP_HAL_ChibiOS/hwdef/Pixhawk6C/hwdef.dat",
     ((r"^SERIAL_ORDER", 0), (r"UART5_(RTS|CTS)", 0))),
    ("libraries/AP_HAL_ChibiOS/hwdef/scripts/chibios_hwdef.py",
     ((r"HAL_HAVE_RTSCTS_SERIAL%u", 4), (r"define AP_FEATURE_RTSCTS", 1))),
    ("libraries/AP_Param/AP_Param.cpp",
     ((r'::printf\("Ignored unknown param %s in defaults file', 3),)),
    ("ArduPlane/config.h", ((r"^#define PARACHUTE ", 1),)),
    ("ArduPlane/Parameters.cpp", ((r'"CHUTE_"', 3),)),
    ("libraries/AP_Parachute/AP_Parachute.cpp",
     ((r"^#if HAL_PARACHUTE_ENABLED", 0), (r"^#endif // HAL_PARACHUTE_ENABLED", 0),
      (r'"Chute has no channel"', 0))),
    # butun #if/#endif satirlari: mesajin hangi blokta oldugu ic ice yapiyla birlikte gorunsun
    ("ArduPlane/parachute.cpp", ((r"^#(if|endif)", 0), (r'"Parachute: Too low"', 0))),
)


def _getir_bayt(url):
    try:
        with urllib.request.urlopen(url, timeout=60) as y:
            return y.read(), None
    except (urllib.error.URLError, OSError) as e:
        return None, f"HATA {e}"


def _getir(url):
    veri, hata = _getir_bayt(url)
    return hata if veri is None else veri.decode("utf-8", errors="replace")


def ikili_tara(yol):
    """Ikiliyi CALISTIRMADAN okur: boyut, sha256, ELF basligi, DIZGELER'in bayt sayimi."""
    veri = Path(yol).read_bytes()
    print(f"  bayt {len(veri)} · sha256 {hashlib.sha256(veri).hexdigest()} · "
          f"ELF={veri[:4] == ELF_BASLIGI}")
    for d in DIZGELER:
        print(f"  {d.decode():22s} {veri.count(d)}")


def features_satirlari():
    """features.txt: PARACHUTE satirlari NUMARASIYLA + '!' (derlenmedi) ile baslayan satir orani."""
    for kart in ("SITL_x86_64_linux_gnu", "Pixhawk6C"):
        metin = _getir(f"{SUNUCU}{kart}/features.txt")
        if metin.startswith("HATA"):
            print(f"    {kart:22s} {metin[:120]}")
            continue
        satirlar = metin.splitlines()
        olumsuz = sum(1 for s in satirlar if s.startswith("!"))
        bulunan = [f":{i} {s}" for i, s in enumerate(satirlar, 1) if "PARACHUTE" in s]
        print(f"    {kart:22s} satir {len(satirlar)} · '!' ile baslayan {olumsuz} · "
              f"{' · '.join(bulunan) or 'PARACHUTE satiri YOK'}")


def kaynak_satirlari():
    """KAYNAK_SATIRLARI: Plane-4.5.7 etiketinden indir, desenleri ara, satirlari numarasiyla bas."""
    for yol, desenler in KAYNAK_SATIRLARI:
        veri, hata = _getir_bayt(KAYNAK_URL.format(yol=yol))
        if veri is None:
            print(f"    {yol} {hata}")
            continue
        satirlar = veri.decode("utf-8", errors="replace").splitlines()
        print(f"    {yol} · {len(veri)} bayt · sha256 {hashlib.sha256(veri).hexdigest()}")
        secilen = set()
        for desen, onceki in desenler:
            eslesen = [i for i, s in enumerate(satirlar) if re.search(desen, s)]
            if not eslesen:
                print(f"      ESLESME YOK: {desen}")
            for i in eslesen:
                secilen.update(range(max(0, i - onceki), i + 1))
        for i in sorted(secilen):
            print(f"      :{i + 1} {satirlar[i].rstrip()}")


def ek_tarama(yol):
    """T221-D '## 6.1' blogu. sitl_yoklama.txt SS6'nin sonuna eklenir; 1-5 ve HUKUM yeniden kosulmaz."""
    print(f"## 6.1 Ek tarama (T221-D · D-449 · "
          f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} · sitl_yokla.py --ek) - "
          f"ikili CALISTIRILMADI: {yol}")
    ikili_tara(yol)
    print(f"  features.txt ({SUNUCU}<kart>/features.txt; satir numarali):")
    features_satirlari()
    print(f"  kaynak satirlari ({KAYNAK_URL.format(yol='<yol>')}):")
    kaynak_satirlari()
    print("  not: dizge sayimi parametre tablosunu KANITLAMAZ; yalniz adin ikilide duz dizge olarak "
          "bulunup bulunmadigini soyler (pozitif kontrol SAFETY_DEFLT). features.txt ile ikili "
          "celisirse hakem KOSUMDUR (README SS6.6 on hukum).")
    return 0


def wsl_dagitimlari():
    """Kayitli WSL dagitimlari (winreg salt okuma). Windows disinda None."""
    try:
        import winreg
    except ImportError:
        return None
    adlar = []
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Lxss") as k:
            i = 0
            while True:
                try:
                    alt = winreg.EnumKey(k, i)
                except OSError:
                    break
                with winreg.OpenKey(k, alt) as ak:
                    try:
                        adlar.append(winreg.QueryValueEx(ak, "DistributionName")[0])
                    except OSError:
                        adlar.append(alt)
                i += 1
    except FileNotFoundError:
        return []
    return adlar


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ikili", default=None,
                    help="onceden indirilmis SITL ikilisi (yalniz dizge taramasi; calistirilmaz)")
    ap.add_argument("--ek", action="store_true",
                    help="yalniz '## 6.1' ek tarama blogu (T221-D); --ikili gerekir, HUKUM basmaz")
    a = ap.parse_args(argv)
    if a.ek:
        if not a.ikili:
            ap.error("--ek icin --ikili gerekir")
        return ek_tarama(a.ikili)

    print(f"# T221 SITL yoklamasi · {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    print(f"platform: {platform.platform()} · python {platform.python_version()}")

    print("\n## 1. PATH (shutil.which)")
    bulunan = {}
    for ad in ARACLAR:
        yol = shutil.which(ad)
        bulunan[ad] = yol
        print(f"  {ad:16s} {yol or 'YOK'}")

    print("\n## 2. WSL dagitim kaydi (HKCU Lxss, salt okuma; wsl.exe CALISTIRILMADI)")
    dag = wsl_dagitimlari()
    if dag is None:
        print("  Windows degil")
    else:
        print(f"  kayitli dagitim: {dag if dag else 'YOK'}")
    if bulunan.get("wsl.exe"):
        print("  not: System32\\wsl.exe her Windows 11'de bulunan yukleyici saplamasidir; "
              "dagitim yoksa Linux calismaz")

    print("\n## 3. venv pip paketleri")
    for p in PAKETLER:
        try:
            print(f"  {p:14s} {importlib.metadata.version(p)}")
        except importlib.metadata.PackageNotFoundError:
            print(f"  {p:14s} YOK")

    print(f"\n## 4. Firmware sunucusu: {SUNUCU}")
    liste = _getir(SUNUCU)
    sitl = sorted(set(re.findall(r'href="/Plane/stable-4\.5\.7/(SITL[^"/]*)"', liste)))
    print(f"  SITL dizinleri: {sitl if sitl else liste[:120]}")
    print("  (Windows yerel SITL ikilisi bu listede YOK; ikisi de Linux ELF'tir)")

    print("\n## 5. features.txt HAL_PARACHUTE_ENABLED")
    for kart in ("Pixhawk6C", "SITL_x86_64_linux_gnu"):
        metin = _getir(f"{SUNUCU}{kart}/features.txt")
        satir = [s for s in metin.splitlines() if "PARACHUTE" in s]
        print(f"  {kart:22s} {satir if satir else metin[:80]}")

    if a.ikili:
        print(f"\n## 6. SITL ikilisi dizge taramasi (CALISTIRILMADI): {a.ikili}")
        ikili_tara(a.ikili)
        print("  not: features.txt '!HAL_PARACHUTE_ENABLED' derken ikilide CHUTE_/AP_Parachute "
              "dizgeleri var -> SITL'de CHUTE_* varligi ancak KOSUMDA gorulur")

    yollar = [ad for ad in ("sim_vehicle.py", "arduplane", "arduplane.exe", "ArduPlane.elf",
                            "dronekit-sitl", "docker", "podman") if bulunan.get(ad)]
    kosulabilir = bool(yollar) or bool(dag)
    print("\n## HUKUM")
    if kosulabilir:
        print(f"HUKUM: KOSULABILIR ({yollar or dag}) -> README SS6.6 yordamiyla prova kosulur")
        return 0
    print("HUKUM: OLCULEMEDI - bu makinede SITL ikilisi, sim_vehicle.py, WSL dagitimi, docker/podman "
          "YOK; ArduPlane SITL provasi KOSULMADI (README SS6.6 Linux/WSL yordami)")
    return 2


if __name__ == "__main__":
    sys.exit(main())
