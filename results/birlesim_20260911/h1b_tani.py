"""NEDEN: H1b'nin tam suit / tek modul farkini gercek Tk ile ayirir.

Testi veya urunu gevsetmez; tam kesif yalniz import yapar. Ekran olcumleri
orijinal testin temizliginden hemen once alinir. Cikti ilk dususu da saklar.
"""

import argparse
import contextlib
import io
import json
import sys
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(KOK / "tests"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tum-import", action="store_true")
    ap.add_argument("--olcek", type=float)
    kip = ap.add_mutually_exclusive_group()
    kip.add_argument("--configure-yok", action="store_true")
    kip.add_argument("--cizim-gecikmesi-ms", type=int, default=0)
    ap.add_argument("--cikti", required=True)
    args = ap.parse_args()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        if args.tum_import:
            kesif = unittest.defaultTestLoader.discover(str(KOK / "tests"))
            print("KESIF_TEST_SAYISI", kesif.countTestCases())
        import test_yks_mk15_hakem_ekrani as m

        class OlculuH1b(m.H1_KucukHaritaYerlesimi):
            def _kur(self, *a, **kw):
                if args.olcek is not None:
                    kw["olcek"] = args.olcek
                app = super()._kur(*a, **kw)
                if args.configure_yok:
                    app.mini_harita.unbind("<Configure>")
                    print("MUTASYON Configure bagi kaldirildi")
                elif args.cizim_gecikmesi_ms:
                    app.mini_harita.bind("<Configure>", lambda _e: self.kok.after(
                        args.cizim_gecikmesi_ms,
                        lambda: app._harita_ciz(app.mini_harita)))
                    print("GECIKME_MS", args.cizim_gecikmesi_ms)
                return app

            def _kapat(self):
                if self.app is not None and self.kok is not None:
                    c = self.app.mini_harita
                    print("H1B_OLCUM", json.dumps({
                        "OLCEK": m.yks_gui.OLCEK,
                        "tk_scaling": float(self.kok.tk.call("tk", "scaling")),
                        "ekran": [self.kok.winfo_screenwidth(),
                                  self.kok.winfo_screenheight()],
                        "pencere": self.kok.geometry(),
                        "mini": [c.winfo_width(), c.winfo_height()],
                        "alan": self.app._olculu_alan.get(str(c)),
                        "font": self.app.f_mini.metrics(),
                    }, ensure_ascii=False, sort_keys=True))
                super()._kapat()

        ad = ("test_H1b_gorunur_pencerede_harita_video_yaninda_cizili_"
              "onay_paneli_daralmadi")
        sonuc = unittest.TextTestRunner(stream=buf, verbosity=2).run(
            unittest.TestSuite([OlculuH1b(ad)]))
        kod = 0 if (sonuc.wasSuccessful() and sonuc.testsRun == 1
                    and not sonuc.skipped) else 1
        print("H1B_EXIT", kod)
    metin = buf.getvalue()
    Path(args.cikti).write_text(metin, encoding="utf-8")
    print(metin, end="")
    return kod


if __name__ == "__main__":
    raise SystemExit(main())
