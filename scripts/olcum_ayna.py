#!/usr/bin/env python3
"""OLCUM AYNASI — `scripts/olcum/` ile canli betikleri KIYASLA (T112 · D-189).

`O:\\navitas-local-train` bir git deposu DEGILDIR; `scripts/olcum/` o
betiklerin TEK SURUM KONTROLUDUR. Iki taraf sessizce ayrisabilir ve ayristi
da: D-166'da bir gerekce duzeltmesi yalniz repo aynasina uygulanmis, canli
betik curutulmus gerekceyi tasimaya devam etmisti (D-189).

🔴 VARSAYILAN YON YOKTUR. Bu arac kendi basina hangisinin DOGRU oldugunu
bilemez — D-166'da dogru olan REPO kopyasiydi, T104'te PAKET kopyasi. Yon
verilmeden `--uygula` cagrilirsa HATA verir. Karar INSANINDIR.

Kullanim:
  venv\\Scripts\\python.exe scripts/olcum_ayna.py                 # yalniz LISTELE
  venv\\Scripts\\python.exe scripts/olcum_ayna.py --uygula --repodan
  venv\\Scripts\\python.exe scripts/olcum_ayna.py --uygula --canlidan

⚠ KAPSAM: yalnizca IKI TARAFTA DA var olan dosyalar. Yalniz canlida bulunan
betikler bu aracin konusu DEGILDIR (T113).
"""

from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
REPO_AYNA = KOK / "scripts" / "olcum"


def canli_kok(verilen=None):
    """Canli olcum dizini. Testteki `canli_kok()` ile AYNI turetim."""
    import os
    if verilen:
        return Path(verilen)
    ortam = os.environ.get("NAVITAS_OLCUM_KOK")
    return Path(ortam) if ortam else KOK.parent / "navitas-local-train"


def ciftler(repo_dizin, canli_dizin):
    if not Path(repo_dizin).is_dir() or not Path(canli_dizin).is_dir():
        return []
    repo = {p.name: p for p in Path(repo_dizin).glob("*.py")
            if "__pycache__" not in p.parts}
    canli = {p.name: p for p in Path(canli_dizin).glob("*.py")
             if "__pycache__" not in p.parts}
    return [(repo[a], canli[a]) for a in sorted(repo.keys() & canli.keys())]


def ayrisanlar(repo_dizin, canli_dizin):
    return [(r, c) for r, c in ciftler(repo_dizin, canli_dizin)
            if not filecmp.cmp(r, c, shallow=False)]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--canli", default=None, help="canli olcum dizini")
    ap.add_argument("--uygula", action="store_true",
                    help="ayrisan ciftleri KOPYALA (yon zorunlu)")
    yon = ap.add_mutually_exclusive_group()
    yon.add_argument("--repodan", action="store_true",
                     help="repo aynasi DOGRU kabul edilir -> canliya kopyalanir")
    yon.add_argument("--canlidan", action="store_true",
                     help="canli betik DOGRU kabul edilir -> repoya kopyalanir")
    args = ap.parse_args()

    canli = canli_kok(args.canli)
    if not canli.is_dir():
        print(f"CANLI DIZIN YOK: {canli}", file=sys.stderr)
        return 2

    tum = ciftler(REPO_AYNA, canli)
    fark = ayrisanlar(REPO_AYNA, canli)
    print(f"cift: {len(tum)} · AYRISAN: {len(fark)}")
    for r, c in fark:
        print(f"  AYRISIK  {r.name}")
        print(f"    repo : {r}  ({r.stat().st_size} B)")
        print(f"    canli: {c}  ({c.stat().st_size} B)")
    if not fark:
        print("  (hepsi senkron)")

    if not args.uygula:
        return 1 if fark else 0

    # 🔴 YON ZORUNLU — sessiz varsayilan YOK.
    if not (args.repodan or args.canlidan):
        print("HATA: --uygula icin YON zorunludur (--repodan ya da --canlidan). "
              "Hangisinin dogru oldugu INSAN KARARIDIR; bu arac tahmin etmez.",
              file=sys.stderr)
        return 2

    for r, c in fark:
        kaynak, hedef = (r, c) if args.repodan else (c, r)
        shutil.copy2(kaynak, hedef)
        print(f"  KOPYALANDI  {kaynak} -> {hedef}")
    print(f"{len(fark)} cift hizalandi "
          f"({'repodan' if args.repodan else 'canlidan'}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
