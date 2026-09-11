"""H2e kararsizligini SIKISTIRILMIS baglamda yeniden ureten tani kosucusu.

NEDEN: `test_yks_mk15_hakem_ekrani.H2e_RotaYokSonrasiAnaHarita` tam suitte
dusuyor ama tek basina gecyor. Bu kosucu ne testi ne de urunu gevsetir;
yalnizca
  · istenen onceki test modullerini AYNI SURECTE kosar (delta debugging),
  · H2e kosarken gelen HER mesaji (tip, seq, kaynak adres) kaydeder,
  · dusus aninda uygulama durumunu (rota/rota_yok/sayaclar/olculu alan) basar.

Kullanim:
  py h2e_tani.py --cikti out.txt                       (yalniz H2e)
  py h2e_tani.py --once test_a1_*.py test_b*.py ...    (once bunlari kos)
  py h2e_tani.py --once-dosya liste.txt                (desenleri dosyadan al)
  py h2e_tani.py --tekrar 5                            (H2e'yi 5 kez kos)
"""

import argparse
import contextlib
import io
import json
import sys
import time
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(KOK / "tests"))

OLAYLAR = []          # (t, "MESAJ"/"CIZIM", ayrinti)


def _kanca(yks_gui):
    """`_mesaj_isle` ve `_harita_ciz` cagrilarini kaydet (davranisi DEGISTIRMEZ)."""
    ham_isle = yks_gui.YksArayuz._mesaj_isle
    ham_ciz = yks_gui.YksArayuz._harita_ciz

    def isle(self, m, adr):
        onceki = (self.rota_yok or {}).get("seq") if self.rota_yok else None
        try:
            return ham_isle(self, m, adr)
        finally:
            OLAYLAR.append((time.monotonic(), "MESAJ", {
                "tip": m.get("type"), "seq": m.get("seq"),
                "node": m.get("node"), "adr": list(adr) if adr else None,
                "rota_yok_once": onceki,
                "rota_yok_sonra": ((self.rota_yok or {}).get("seq")
                                   if self.rota_yok else None),
                "rota_seq": (self.rota or {}).get("seq") if self.rota else None,
            }))

    def ciz(self, tuval=None):
        kayit = {
            "tuval": str(tuval) if tuval is not None else None,
            "rota_yok_seq": ((self.rota_yok or {}).get("seq")
                             if self.rota_yok else None),
            "detay_uz": len((self.rota_yok or {}).get("detay") or "")
                        if self.rota_yok else None,
            "gorunum": getattr(self, "gorunum_adi", None),
        }
        try:
            return ham_ciz(self, tuval)
        finally:
            kayit["alan"] = {k: list(v) for k, v in
                             getattr(self, "_olculu_alan", {}).items()}
            OLAYLAR.append((time.monotonic(), "CIZIM", kayit))

    yks_gui.YksArayuz._mesaj_isle = isle
    yks_gui.YksArayuz._harita_ciz = ciz


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", nargs="*", default=[],
                    help="H2e'den ONCE ayni surecte kosulacak modul desenleri")
    ap.add_argument("--once-dosya", help="desenleri satir satir iceren dosya")
    ap.add_argument("--tum-import", action="store_true",
                    help="tum test modullerini yalniz IMPORT et (kosma)")
    ap.add_argument("--tekrar", type=int, default=1)
    ap.add_argument("--kanca", action="store_true", help="mesaj/cizim gunlugu")
    ap.add_argument("--enjekte-ms", type=int, default=0,
                    help="YABANCI bir 127.0.0.1 soketinden bu periyotla "
                         "NO_ROUTE serp (kaynak kilidi denemesi)")
    ap.add_argument("--cikti", required=True)
    args = ap.parse_args()

    desenler = list(args.once)
    if args.once_dosya:
        desenler += [s.strip() for s in
                     Path(args.once_dosya).read_text(encoding="utf-8").splitlines()
                     if s.strip() and not s.startswith("#")]

    buf = io.StringIO()
    kod = 0
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        if args.tum_import:
            kesif = unittest.defaultTestLoader.discover(str(KOK / "tests"))
            print("KESIF_TEST_SAYISI", kesif.countTestCases())
        print("ONCE_DESEN_SAYISI", len(desenler))
        for d in desenler:
            t0 = time.monotonic()
            s = unittest.defaultTestLoader.discover(str(KOK / "tests"), pattern=d)
            r = unittest.TextTestRunner(stream=buf, verbosity=0).run(s)
            print(f"ONCE {d} test={r.testsRun} hata={len(r.errors)} "
                  f"dusus={len(r.failures)} sure={time.monotonic() - t0:.1f}s")

        import test_yks_mk15_hakem_ekrani as m
        import yks_gui
        if args.kanca:
            _kanca(yks_gui)

        class TaniliH2e(m.H2e_RotaYokSonrasiAnaHarita):
            def _kur(self, *a, **kw):
                app = super()._kur(*a, **kw)
                if args.enjekte_ms:
                    self._serp(app)
                return app

            def _serp(self, _app):
                """YABANCI uc: yks'nin portuna NO_ROUTE serper (kaynak kilidi
                yalniz IP'ye bakiyor mu?)."""
                import threading
                from link import UDPLink
                from protocol import encode
                yabanci = UDPLink(bind=("127.0.0.1", 0), timeout=0.05)
                hedef = ("127.0.0.1", self.link.port)
                dur = threading.Event()
                self.addCleanup(dur.set)
                self.addCleanup(yabanci.close)

                # `detay` ALANI YOK: sahada `iha_sender.send_no_route(sebep)`
                # boyle uretir (detay=None -> alan hic konmaz). Bant TEK SATIR
                # olur; olculu alan 1,0'da (34,189,227), 1,5'te (51,156,243) —
                # mimarin gordugu degerlerin ta kendisi.
                yok = {k: v for k, v in m.YOK_ROTA.items() if k != "detay"}

                def kos():
                    n = 900
                    while not dur.wait(args.enjekte_ms / 1000.0):
                        n += 1
                        try:
                            yabanci.send(encode(dict(yok, seq=n)), hedef)
                        except OSError:
                            return

                threading.Thread(target=kos, daemon=True).start()

            def _gecisleri_denetle(self, olcek):
                del OLAYLAR[:]
                try:
                    super()._gecisleri_denetle(olcek)
                finally:
                    app = self.app
                    print("H2E_DURUM", json.dumps({
                        "olcek": olcek,
                        "OLCEK": yks_gui.OLCEK,
                        "tk_scaling": (float(self.kok.tk.call("tk", "scaling"))
                                       if self.kok else None),
                        "link_port": self.link.sock.getsockname()[1],
                        "iha_port": self.iha.sock.getsockname()[1],
                        "ika_port": self.ika.sock.getsockname()[1],
                        "rota": (app.rota or {}).get("seq") if app else None,
                        "rota_yok": (app.rota_yok if app else None),
                        "sayac": ({str(k): v for k, v in app.sayac.items()}
                                  if app else None),
                        "harita": str(app.harita) if app else None,
                        "olculu_alan": ({k: list(v) for k, v in
                                         getattr(app, "_olculu_alan", {}).items()}
                                        if app else None),
                        "harita_wh": ([app.harita.winfo_width(),
                                       app.harita.winfo_height()] if app else None),
                    }, ensure_ascii=False, sort_keys=True, default=str))
                    if OLAYLAR:
                        t0 = OLAYLAR[0][0]
                        print("H2E_OLAY_SAYISI", len(OLAYLAR))
                        for t, tur, ay in OLAYLAR[-80:]:
                            print(f"  {t - t0:7.3f} {tur} "
                                  f"{json.dumps(ay, ensure_ascii=False, sort_keys=True)}")

        for i in range(args.tekrar):
            suit = unittest.TestSuite([TaniliH2e("test_H2e_olcek_1_0"),
                                       TaniliH2e("test_H2e_olcek_1_5")])
            sonuc = unittest.TextTestRunner(stream=buf, verbosity=2).run(suit)
            print(f"H2E_TUR {i + 1}/{args.tekrar} "
                  f"{'OK' if sonuc.wasSuccessful() else 'DUSTU'} "
                  f"dusus={len(sonuc.failures)} hata={len(sonuc.errors)}")
            if not sonuc.wasSuccessful():
                kod = 1
        print("H2E_EXIT", kod)
    metin = buf.getvalue()
    Path(args.cikti).write_text(metin, encoding="utf-8")
    print(metin[-4000:], end="")
    return kod


if __name__ == "__main__":
    raise SystemExit(main())
