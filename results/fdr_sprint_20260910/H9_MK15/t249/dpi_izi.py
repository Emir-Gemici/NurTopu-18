r"""T249 tanı: tam süit boyunca SÜREÇ DPI FARKINDALIĞININ nerede değiştiğini ölçer.

`comms/yks_gui.py:4875` `main()` içinde `SetProcessDpiAwareness(1)` çağırır.
Bu çağrı SÜREÇ GENELİNDEDİR ve GERİ ALINAMAZ: ondan sonra açılan her Tk kökü
`winfo_screenwidth()` olarak sanal değil FİZİKSEL çözünürlüğü görür
(bu makinede 1707×1067 → 2560×1600). `YksArayuz._arayuz_kur` pencere boyutunu
`min(S(1240), int(sw * 0.92))` ile EKRAN BOYUTUNDAN türettiği için ana harita
tuvali de büyür — T226-D3'ün H2f kilidi tuval boyutuna bağlıdır.

Çıktı: farkındalık değerinin değiştiği ilk test kimliği.
Kullanım:
  O:\navitas-local-train\venv\Scripts\python.exe -X utf8 -B \
      results/fdr_sprint_20260910/H9_MK15/t249/dpi_izi.py
"""
from __future__ import annotations

import ctypes
import sys
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]


def farkindalik():
    """0 = UNAWARE, 1 = SYSTEM_DPI_AWARE, 2 = PER_MONITOR."""
    v = ctypes.c_int(-1)
    try:
        ctypes.windll.shcore.GetProcessDpiAwareness(None, ctypes.byref(v))
    except Exception as exc:                     # pragma: no cover
        return f"OKUNAMADI({exc!r})"
    return v.value


class IzSonucu(unittest.TextTestResult):
    onceki = None

    def _bak(self, nerede, test):
        d = farkindalik()
        if d != IzSonucu.onceki:
            print(f"[DPI] {IzSonucu.onceki} -> {d}  ({nerede}: {test.id()})",
                  flush=True)
            IzSonucu.onceki = d

    def startTest(self, test):
        self._bak("ONCE", test)
        super().startTest(test)

    def stopTest(self, test):
        super().stopTest(test)
        self._bak("SONRA", test)


def main():
    print(f"[DPI] baslangic = {farkindalik()}", flush=True)
    takim = unittest.TestLoader().discover(str(KOK / "tests"))
    kosucu = unittest.TextTestRunner(verbosity=0, resultclass=IzSonucu)
    sonuc = kosucu.run(takim)
    print(f"[DPI] bitis = {farkindalik()}", flush=True)
    return 0 if sonuc.wasSuccessful() else 1


if __name__ == "__main__":
    sys.path.insert(0, str(KOK))
    raise SystemExit(main())
