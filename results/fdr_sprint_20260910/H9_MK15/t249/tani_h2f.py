r"""T249 tanı: H2f (`_ana_open_route_kalinti`) ölçüm anında ana tuval
boyutunun ve kesişim sayısının ZAMANLA nasıl değiştiğini ölçer.

Kullanım:
  O:\navitas-local-train\venv\Scripts\python.exe -X utf8 -B \
      results/fdr_sprint_20260910/H9_MK15/t249/tani_h2f.py [--yuk N]

`--yuk N`: ölçüm boyunca N ayrı işlemde CPU yükü koşturur (kararsızlığı
büyütmek için). Çıktı: her OPEN_ROUTE'tan sonra 20 ms aralıkla 2 s boyunca
(tuval_w, tuval_h, kesişim sayısı) izi.
"""
from __future__ import annotations

import argparse
import multiprocessing
import sys
import time
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(KOK))
sys.path.insert(0, str(KOK / "tests"))

import test_yks_mk15_hakem_ekrani as T  # noqa: E402


def _yuk(bayrak):
    x = 0
    while not bayrak.value:
        x = (x * 1103515245 + 12345) % 2147483647
    return x


class TaniH2c(T.H2c_EtiketCakismasi):
    IZ = []

    def _ana_open_route_kalinti(self, olcek, seq):
        c = self.app.harita
        self.assertTrue(self._pompala(
            lambda: any("inset" in c.gettags(i) for i in c.find_all()), 3.0))
        for yol in (1, 2, 3):
            seq += 1
            self._mesaj_ver(dict(T.ROTA, seq=seq, road=yol,
                                 label=T.yks_gui.ROAD_LABEL[yol]))
            t0 = time.monotonic()
            iz = []
            while time.monotonic() - t0 < 2.0:
                self.kok.update()
                kutular = T._metin_kutulari(c)
                n = len(T._kesisen_ciftler(kutular))
                iz.append((round(time.monotonic() - t0, 3),
                           c.winfo_width(), c.winfo_height(), n))
                time.sleep(0.02)
            sik = []
            for kayit in iz:
                if not sik or sik[-1][1:] != kayit[1:]:
                    sik.append(kayit)
            TaniH2c.IZ.append((olcek, yol, sik))
            print(f"  olcek={olcek} road={yol}: {len(iz)} ornek, "
                  f"degisim noktalari={sik}", flush=True)

    def test_H2c_olcek_1_0(self):
        print("== olcek 1.0 ==", flush=True)
        self._h2c(1.0)

    def test_H2c_olcek_1_5_hakem_ekrani(self):
        print("== olcek 1.5 ==", flush=True)
        self._h2c(1.5)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--yuk", type=int, default=0)
    ap.add_argument("--dpi", action="store_true",
                    help="olcumden ONCE SetProcessDpiAwareness(1) (main()'in "
                         "yaptigi, SUREC GENELINDE geri alinamaz islem)")
    a = ap.parse_args()
    if a.dpi:
        import ctypes
        print("[dpi] SetProcessDpiAwareness(1) ->",
              ctypes.windll.shcore.SetProcessDpiAwareness(1), flush=True)
    surecler = []
    bayrak = None
    if a.yuk:
        bayrak = multiprocessing.Value("i", 0)
        for _ in range(a.yuk):
            p = multiprocessing.Process(target=_yuk, args=(bayrak,))
            p.start()
            surecler.append(p)
        print(f"[yuk] {a.yuk} surec kosuyor", flush=True)
    try:
        yukleyici = unittest.TestLoader()
        takim = yukleyici.loadTestsFromTestCase(TaniH2c)
        unittest.TextTestRunner(verbosity=2).run(takim)
    finally:
        if bayrak is not None:
            bayrak.value = 1
            for p in surecler:
                p.join(timeout=5)
                if p.is_alive():
                    p.terminate()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
