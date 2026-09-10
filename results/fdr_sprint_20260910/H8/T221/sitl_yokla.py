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

CIKIS: 0 = SITL kosulabilir (en az bir yol VAR) | 2 = OLCULEMEDI (yol yok). Hukum son satirdadir.
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
DIZGELER = (b"CHUTE_",b"AP_Parachute", b"Parachute: Released", b"TKOFF_THR_MINACC",
            b"TKOFF_TDRAG_ELEV", b"SHOVE_X", b"FS_LONG_ACTN", b"ArduPlane V4.5.7")


def _getir(url):
    try:
        with urllib.request.urlopen(url, timeout=60) as y:
            return y.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, OSError) as e:
        return f"HATA {e}"


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
    a = ap.parse_args(argv)

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
        veri = Path(a.ikili).read_bytes()
        print(f"  bayt {len(veri)} · sha256 {hashlib.sha256(veri).hexdigest()} · "
              f"ELF={veri[:4] == ELF_BASLIGI}")
        for d in DIZGELER:
            print(f"  {d.decode():22s} {veri.count(d)}")
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
