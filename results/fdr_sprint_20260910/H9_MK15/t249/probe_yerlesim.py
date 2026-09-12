r"""T249 tanı: pencere/tuval YERLEŞİMİNİN zaman izi.

`deiconify()` ve `gorunum("kamera")` sonrasında pencere ve tuval boyutlarını
10 ms aralıkla 1,5 s örnekler, yalnız DEĞİŞİM noktalarını basar. Amaç:
`_pompala(lambda: False, 0.2)` sabit uykusunun gerçekten bir şey bekleyip
beklemediğini ÖLÇMEK — bekliyorsa iz birden çok değişim noktası gösterir.

Kullanım:
  O:\navitas-local-train\venv\Scripts\python.exe -X utf8 -B ^
      results/fdr_sprint_20260910/H9_MK15/t249/probe_yerlesim.py
"""
from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(KOK))
sys.path.insert(0, str(KOK / "tests"))

import test_yks_mk15_hakem_ekrani as T  # noqa: E402


def _sikistir(iz):
    sik = []
    for kayit in iz:
        if not sik or sik[-1][1:] != kayit[1:]:
            sik.append(kayit)
    return sik


class ProbeH2c(T.H2c_EtiketCakismasi):
    """`_olcekli_kur` yerine ÖLÇEN sürüm; hiçbir assert koşmaz."""

    def _olcekli_kur(self, olcek):
        app = self._kur(olcek=olcek)
        self.kok.deiconify()
        t0, iz = time.monotonic(), []
        while time.monotonic() - t0 < 1.5:
            self.kok.update()
            iz.append((round(time.monotonic() - t0, 3), self.kok.geometry(),
                       self.kok.winfo_width(), self.kok.winfo_height(),
                       app.harita.winfo_ismapped(),
                       app.harita.winfo_width(), app.harita.winfo_height()))
            time.sleep(0.01)
        print(f"olcek={olcek} HARITA gorunumu degisim noktalari "
              f"(t, wm-geometry, kok_w, kok_h, haritalandi, tuval_w, tuval_h):")
        for k in _sikistir(iz):
            print("   ", k)

        app.gorunum("kamera")
        t0, iz = time.monotonic(), []
        while time.monotonic() - t0 < 1.5:
            self.kok.update()
            iz.append((round(time.monotonic() - t0, 3),
                       self.kok.winfo_width(), self.kok.winfo_height(),
                       app.mini_harita.winfo_ismapped(),
                       app.mini_harita.winfo_width(),
                       app.mini_harita.winfo_height()))
            time.sleep(0.01)
        print(f"olcek={olcek} KAMERA gorunumu (kucuk harita) degisim noktalari "
              f"(t, kok_w, kok_h, haritalandi, mini_w, mini_h):")
        for k in _sikistir(iz):
            print("   ", k)
        return app

    def test_H2c_olcek_1_0(self):
        self._olcekli_kur(1.0)

    def test_H2c_olcek_1_5_hakem_ekrani(self):
        self._olcekli_kur(1.5)


if __name__ == "__main__":
    takim = unittest.TestLoader().loadTestsFromTestCase(ProbeH2c)
    sonuc = unittest.TextTestRunner(verbosity=1).run(takim)
    raise SystemExit(0 if sonuc.wasSuccessful() else 1)
