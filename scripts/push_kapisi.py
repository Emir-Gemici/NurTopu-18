#!/usr/bin/env python3
"""Push kapısı: tam süit + genel kapı ikisi de YEŞİLSE push; biri kırmızıysa asla.

NEDEN (7 Eylül 02:0x, D-430): mimar süit `FAILED (failures=1)` iken push etti —
zincir yalnız genel kapının çıktısına bakıyordu, süitin "OK" satırına bakmıyordu.
Anayasa §5: "kapı düşmüşken push yapılmaz." Kural insana değil betiğe bağlanır.

Ne yapar (sırayla, ard arda — paralel DEĞİL, mutasyon testleri dosyayı kısa süre
bozuk bıraktığı için iki koşum çakışınca sahte IndentationError üretir):
  1. UDP 5005/5006 doluysa (canlı yks_gui/ika_nav) hiç başlamaz — süit orada
     kesin düşer (D-427/T209); "kırmızı ama ortam" yorumu yapılmaz, beklenir.
  2. `python -m unittest discover -s tests` → son satır "OK" ya da "OK (skipped=N)"
     olmalı; çıkış kodu 0 olmalı.
  3. `codes/test_rota_sentetik.py` → "GENEL KAPI (madde 14): GECTI" olmalı.
  4. İkisi de geçtiyse `git push origin master`; aksi hâlde çıkış 3 ve sebep.
Çıktılar `results/push_kapisi/<zaman>/` altına yazılır (kanıt).

Kullanım:  python scripts/push_kapisi.py            (push eder)
           python scripts/push_kapisi.py --kuru     (push etmez, yalnız ölçer)
"""

import argparse
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

for _a in (sys.stdout, sys.stderr):
    try:
        _a.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

KOK = Path(__file__).resolve().parents[1]
PY = sys.executable
TEST_PORTLARI = ("5005", "5006")   # comms/test_comms.py loopback bind (D-427)


def _portlar_dolu() -> list[str]:
    q = subprocess.run(["netstat", "-ano", "-p", "udp"], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return [l.strip() for l in q.stdout.splitlines()
            if any(f":{p} " in l for p in TEST_PORTLARI)]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--kuru", action="store_true", help="push etme, yalnız ölç")
    a = ap.parse_args(argv)

    dolu = _portlar_dolu()
    if dolu:
        print("DURDU: test portları dolu (süit kesin düşer, D-427/T209):")
        for l in dolu:
            print("   ", l)
        return 3

    kayit = KOK / "results" / "push_kapisi" / dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    kayit.mkdir(parents=True, exist_ok=True)

    print("1/2 tam süit…")
    s = subprocess.run([PY, "-m", "unittest", "discover", "-s", "tests", "-q"], cwd=KOK,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    (kayit / "tam_suit.txt").write_text(s.stdout + s.stderr, encoding="utf-8")
    kuyruk = [l for l in (s.stdout + s.stderr).splitlines() if re.match(r"^(Ran |OK|FAILED)", l)]
    print("   ", " · ".join(kuyruk[-2:]))
    suit_ok = s.returncode == 0 and any(l.startswith("OK") for l in kuyruk)

    print("2/2 genel kapı…")
    g = subprocess.run([PY, "codes/test_rota_sentetik.py"], cwd=KOK,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    (kayit / "genel_kapi.txt").write_text(g.stdout + g.stderr, encoding="utf-8")
    son = (g.stdout + g.stderr).strip().splitlines()[-1] if (g.stdout + g.stderr).strip() else ""
    print("   ", son)
    kapi_ok = g.returncode == 0 and "GECTI" in son

    if not (suit_ok and kapi_ok):
        print(f"PUSH YOK — süit {'OK' if suit_ok else 'KIRMIZI'} · kapı {'OK' if kapi_ok else 'KIRMIZI'} "
              f"· kanıt {kayit.relative_to(KOK)}")
        return 3
    if a.kuru:
        print(f"KURU: ikisi de yeşil, push edilmedi · kanıt {kayit.relative_to(KOK)}")
        return 0
    p = subprocess.run(["git", "push", "origin", "master"], cwd=KOK, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    print(p.stdout.strip() or p.stderr.strip()[-300:])
    print(f"PUSH {'TAMAM' if p.returncode == 0 else 'HATA'} · kanıt {kayit.relative_to(KOK)}")
    return 0 if p.returncode == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
