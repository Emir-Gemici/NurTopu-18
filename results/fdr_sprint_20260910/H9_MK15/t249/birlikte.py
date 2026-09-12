r"""T249 kapısı: MuJoCo modülü ile hakem ekranı modülünü AYNI SÜREÇTE,
tam süitteki SIRAYLA koşar.

Tam süitte `test_sim_mujoco_arena` (alfabetik olarak 's') hakem ekranından
('y') ÖNCE gelir ve MuJoCo'nun GL bağlamı süreç DPI farkındalığını 0 → 2
yapar (`dpi_izi_cikti.txt`). Bu betik o BİTİŞİKLİĞİ 10 dakikalık tam süit
koşmadan yeniden üretir — yani H2f kilidinin gerçek koşum ortamıdır.
"""
from __future__ import annotations

import ctypes
import sys
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]


def farkindalik():
    v = ctypes.c_int(-1)
    try:
        ctypes.windll.shcore.GetProcessDpiAwareness(None, ctypes.byref(v))
    except Exception as exc:
        return f"OKUNAMADI({exc!r})"
    return v.value


def main():
    sys.path.insert(0, str(KOK))
    sys.path.insert(0, str(KOK / "tests"))
    y = unittest.TestLoader()
    print(f"[DPI] baslangic = {farkindalik()}", flush=True)
    t1 = y.loadTestsFromName("test_sim_mujoco_arena")
    s1 = unittest.TextTestRunner(verbosity=0).run(t1)
    print(f"[DPI] mujoco SONRASI = {farkindalik()}", flush=True)
    t2 = y.loadTestsFromName("test_yks_mk15_hakem_ekrani")
    s2 = unittest.TextTestRunner(verbosity=1).run(t2)
    print(f"[DPI] bitis = {farkindalik()}", flush=True)
    print(f"MUJOCO {'OK' if s1.wasSuccessful() else 'DUSTU'} · "
          f"HAKEM {'OK' if s2.wasSuccessful() else 'DUSTU'}", flush=True)
    return 0 if (s1.wasSuccessful() and s2.wasSuccessful()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
