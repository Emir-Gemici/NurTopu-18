r"""T249 kapısı: hakem ekranı modülünün ARDIŞIK koşumları (yüklü / yüksüz).

Üç yüzey, her biri `--tur` kez:
  A) modül tek başına, DPI KAPALI      (`kos_dpi.py --dpisiz`)
  B) modül tek başına, DPI AÇIK        (`kos_dpi.py`)         ← kararsızlığın ortamı
  C) MuJoCo modülü + hakem modülü AYNI SÜREÇTE (`birlikte.py`) ← tam süitin sırası

`--yuk N` verilirse ölçüm boyunca N ayrı işlemde CPU yükü koşar.
"""
from __future__ import annotations

import argparse
import multiprocessing
import subprocess
import sys
import time
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]
CIK = Path(__file__).resolve().parent
PY = sys.executable


def _yuk(bayrak):
    x = 1
    while not bayrak.value:
        x = (x * 1103515245 + 12345) % 2147483647
    return x


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tur", type=int, default=5)
    ap.add_argument("--yuk", type=int, default=0)
    ap.add_argument("--onek", default="ardisik")
    a = ap.parse_args()

    surecler, bayrak = [], None
    if a.yuk:
        bayrak = multiprocessing.Value("i", 0)
        for _ in range(a.yuk):
            pr = multiprocessing.Process(target=_yuk, args=(bayrak,))
            pr.start()
            surecler.append(pr)
        print(f"[yuk] {a.yuk} CPU surec kosuyor", flush=True)

    yuzeyler = [
        ("A_dpisiz", [PY, "-X", "utf8", "-B", str(CIK / "kos_dpi.py"), "--dpisiz"]),
        ("B_dpili", [PY, "-X", "utf8", "-B", str(CIK / "kos_dpi.py")]),
        ("C_birlikte", [PY, "-X", "utf8", "-B", str(CIK / "birlikte.py")]),
    ]
    tum = True
    try:
        for ad, komut in yuzeyler:
            for i in range(1, a.tur + 1):
                t0 = time.monotonic()
                p = subprocess.run(komut, cwd=str(KOK), capture_output=True,
                                   text=True, encoding="utf-8", errors="replace")
                sure = time.monotonic() - t0
                dosya = CIK / f"{a.onek}_{ad}_{i}.txt"
                dosya.write_text(p.stdout + p.stderr, encoding="utf-8")
                kuyruk = [s for s in (p.stdout + p.stderr).splitlines() if s.strip()]
                print(f"{ad} {i}/{a.tur}: EXIT={p.returncode} · {sure:.1f}s · "
                      f"{kuyruk[-1] if kuyruk else ''}", flush=True)
                tum = tum and p.returncode == 0
    finally:
        if bayrak is not None:
            bayrak.value = 1
            for pr in surecler:
                pr.join(timeout=5)
                if pr.is_alive():
                    pr.terminate()
    print("ARDISIK_SONUC", "GECTI" if tum else "DUSTU")
    return 0 if tum else 1


if __name__ == "__main__":
    multiprocessing.freeze_support()
    raise SystemExit(main())
