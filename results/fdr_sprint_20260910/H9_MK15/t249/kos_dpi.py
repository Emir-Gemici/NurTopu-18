r"""T249 kapısı: hakem ekranı modülünü SÜREÇ DPI FARKINDALIĞI AÇIKKEN koşar.

Tam süitte `tests/test_sim_mujoco_arena.py`in MuJoCo GL bağlamı süreç DPI
farkındalığını 0 → 2 yapar (ölçüm: `dpi_izi_cikti.txt`) ve bu GERİ ALINAMAZ.
Bu betik o durumu TEK MODÜLDE, 10 dakikalık tam süit koşmadan yeniden üretir.

Kullanım:
  O:\navitas-local-train\venv\Scripts\python.exe -X utf8 -B \
      results/fdr_sprint_20260910/H9_MK15/t249/kos_dpi.py [--dpisiz] [--sinif AD]
"""
from __future__ import annotations

import argparse
import sys
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dpisiz", action="store_true",
                    help="farkındalığı AÇMA (denetim koşumu)")
    ap.add_argument("--sinif", default="",
                    help="yalnız bu sınıf (ör. H2c_EtiketCakismasi)")
    a = ap.parse_args()
    if not a.dpisiz:
        import ctypes
        r = ctypes.windll.shcore.SetProcessDpiAwareness(1)
        print(f"[dpi] SetProcessDpiAwareness(1) -> {r}", flush=True)
    else:
        print("[dpi] KAPALI (denetim)", flush=True)
    sys.path.insert(0, str(KOK))
    sys.path.insert(0, str(KOK / "tests"))
    ad = "test_yks_mk15_hakem_ekrani"
    if a.sinif:
        ad += "." + a.sinif
    takim = unittest.TestLoader().loadTestsFromName(ad)
    sonuc = unittest.TextTestRunner(verbosity=2).run(takim)
    return 0 if sonuc.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
