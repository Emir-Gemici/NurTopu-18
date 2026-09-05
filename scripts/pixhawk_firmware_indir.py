#!/usr/bin/env python3
"""Pixhawk 6C icin ArduCopter firmware'ini PC'de CEVRIMDISI indirir.

NEDEN (D-424, 5 Eylul sahada olculdu):
  * Pixhawk 6C fabrikadan **PX4 yuklu** cikar; bizim yiginimizin tamami
    ArduCopter'dir (`config/pixhawk/arducopter_fda.param`, `SYSID_THISMAV`,
    `SRx_*`, `FENCE_*`). Yani kart kutudan cikinca **flash SART**.
  * 5 Eylul'e kadar bu adim hicbir belgede yoktu: plan §2.4 yalnizca
    "ArduCopter kararli surum" diyordu — sanki kartta zaten varmis gibi.
    Depoda da saha belleginde de firmware dosyasi YOKTU.
  * Mission Planner firmware'i **internetten indirir**. 5 Eylul'de atolyede
    internet vardi ve kurtardi; 21 Eylul Adiyaman'da internet VARSAYILMAZ.
    Kart bir sebeple yeniden flash gerekirse (bozulan parametre, yanlis surum,
    yedek karta gecis) sahada internetsiz cakilirdik. Tek atislik ucus.

  Bu betik `wheels/` ile AYNI kaliptadir (`scripts/nano_tekerlek_indir.py`):
  PC'de indirilir, `firmware/` altina konur, `scripts/bellek_hazirla.py` onu
  saha bellegine kopyalar. Depoya ikili dosya girmez (`.gitignore`).

KULLANIM (PC, depo venv'i):
  python scripts/pixhawk_firmware_indir.py --kuru    ne indirecegini basar, INDIRMEZ
  python scripts/pixhawk_firmware_indir.py           firmware/ altina indirir
  python scripts/pixhawk_firmware_indir.py --dest E:/firmware   dogrudan bellege

CIKIS KODLARI: 0 indi ve dogrulandi | 1 hatali cagri (fail-closed) |
2 indirilemedi ya da **board_id yanlis** (fail-visible).

⚠ `board_id` KAPISI: `.apj` icindeki `board_id` Pixhawk 6C icin **56**'dir.
Baska bir kartin firmware'i yanlislikla indirilirse Mission Planner reddeder
ama sahada bunu kesfetmek zaman kaybidir — burada, PC'de yakalanir.
"""

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]

# Windows konsolu cp1254'tur; "⚠" gibi imler UnicodeEncodeError atar ve raporu
# TAM BITTIKTEN SONRA oldurur (dosyalar inmis olur, betik yine de 1 doner —
# fail-silent'tan beter, YANLIS bir basarisizlik). bellek_hazirla.py ile ayni
# koruma: akimlari utf-8'e al, imle takilma.
for _akim in (sys.stdout, sys.stderr):
    try:
        _akim.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

# Pixhawk 6C = ArduPilot kart adi "Pixhawk6C", board_id 56 (hwdef.dat).
KART = "Pixhawk6C"
BOARD_ID = 56
TABAN = f"https://firmware.ardupilot.org/Copter/stable/{KART}/"

# arducopter.apj  -> Mission Planner "Load custom firmware" bunu ister (bootloader VAR sayar)
# arducopter_with_bl.hex -> bootloader'i da iceren tam imaj; kart bootloader'i
#   bozulursa DFU/SWD ile yazilir. Ikisi de alinir: ilki normal yol, ikincisi kurtarma.
DOSYALAR = ("arducopter.apj", "arducopter_with_bl.hex", "firmware-version.txt")
ZORUNLU = ("arducopter.apj",)


def _indir(ad: str, hedef: Path) -> tuple[bool, str]:
    url = TABAN + ad
    try:
        with urllib.request.urlopen(url, timeout=60) as y:
            veri = y.read()
    except (urllib.error.URLError, OSError) as e:
        return False, f"{e}"
    hedef.write_bytes(veri)
    return True, f"{len(veri)} bayt"


def _apj_dogrula(yol: Path) -> tuple[bool, str]:
    """`.apj` gercekten Pixhawk6C icin mi? board_id yanlissa fail-visible."""
    try:
        d = json.loads(yol.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return False, f"apj okunamadi: {e}"
    bid = d.get("board_id")
    ozet = d.get("summary", "?")
    if bid != BOARD_ID:
        return False, (f"board_id={bid} (beklenen {BOARD_ID}), summary={ozet} — "
                       f"BU BASKA BIR KARTIN FIRMWARE'I")
    return True, f"board_id={bid} · summary={ozet} · git={d.get('git_identity', '?')}"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dest", default=str(KOK / "firmware"),
                    help="hedef klasor (varsayilan: depo koku/firmware)")
    ap.add_argument("--kuru", action="store_true",
                    help="ne indirilecegini basar, INDIRMEZ")
    a = ap.parse_args(argv)

    hedef = Path(a.dest)
    print(f"KART: {KART} (board_id {BOARD_ID}) · KAYNAK: {TABAN}")
    print(f"HEDEF: {hedef}")

    if a.kuru:
        for ad in DOSYALAR:
            print(f"  [KURU] {TABAN}{ad}")
        print("KURU KOSU — hicbir sey indirilmedi.")
        return 0

    hedef.mkdir(parents=True, exist_ok=True)
    eksik_zorunlu = []
    for ad in DOSYALAR:
        ok, bilgi = _indir(ad, hedef / ad)
        isaret = "OK  " if ok else "HATA"
        print(f"  [{isaret}] {ad:26s} {bilgi}")
        if not ok and ad in ZORUNLU:
            eksik_zorunlu.append(ad)

    if eksik_zorunlu:
        print(f"\nHATA: zorunlu dosya inmedi: {', '.join(eksik_zorunlu)}")
        return 2

    ok, bilgi = _apj_dogrula(hedef / "arducopter.apj")
    print(f"\nKAPI board_id: {'GECTI' if ok else 'DUSTU'} — {bilgi}")
    if not ok:
        return 2

    surum = (hedef / "firmware-version.txt")
    if surum.is_file():
        print(f"SURUM: {surum.read_text(encoding='utf-8', errors='replace').strip()}")

    print("\nSahada yukleme: Mission Planner > Setup > Install Firmware >")
    print("  'Load custom firmware' > arducopter.apj   (Disconnect DURUMDA)")
    print("⚠ Flash TUM PARAMETRELERI SIFIRLAR — once firmware, SONRA .param dosyasi.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
