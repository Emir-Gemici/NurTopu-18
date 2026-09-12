r"""T250 (çürütücü KUSUR 2) — `_ana_denetle` HANGİ TUVAL BOYUTUNDA koşuyor?

Çürütücünün bulgusu: T249 çivilemesi H2f kalıntı sayı kilidi için zorunluydu,
ama aynı satır `_ana_denetle`i de çivilenmiş tuvale taşıyınca ekrandan TÜREYEN
boyutta (süreç DPI farkındalığı açıkken 1,5 ölçekte 1142x725) hiçbir kapsam
noktası ölçülmez olmuştu. Düzeltmeden sonra `_ana_denetle` İKİ yüzeyde koşuyor;
bu betik o iki yüzeyin GERÇEK boyutlarını yazar — yani kapsamın geri
kazanıldığını ÖLÇÜMLE gösterir.

Kullanım:
  O:\navitas-local-train\venv\Scripts\python.exe -X utf8 -B \
      results/fdr_sprint_20260910/H9_MK15/t249/kapsam_izi.py [--dpi]

`--dpi`: ölçümden ÖNCE SetProcessDpiAwareness(1) — tam süitte MuJoCo GL
bağlamının süreç genelinde yaptığı şeyin aynısı (bkz. `dpi_izi_cikti.txt`).
"""
from __future__ import annotations

import argparse
import ctypes
import sys
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(KOK))
sys.path.insert(0, str(KOK / "tests"))

import test_yks_mk15_hakem_ekrani as T  # noqa: E402


class IzliH2c(T.H2c_EtiketCakismasi):
    IZ = []

    def _ana_denetle(self, ad):
        c = self.app.harita
        boyut = (c.winfo_width(), c.winfo_height())
        civili = boyut == self.ANA_TUVAL[self._olcek_izi]
        IzliH2c.IZ.append((self._olcek_izi, ad, boyut, civili))
        print(f"  olcek={self._olcek_izi} ad={ad!r} tuval={boyut[0]}x{boyut[1]} "
              f"civili={civili}", flush=True)
        return super()._ana_denetle(ad)

    def _h2c(self, olcek):
        self._olcek_izi = olcek
        return super()._h2c(olcek)

    def test_H2c_olcek_1_0(self):
        print("== olcek 1.0 ==", flush=True)
        self._h2c(1.0)

    def test_H2c_olcek_1_5_hakem_ekrani(self):
        print("== olcek 1.5 ==", flush=True)
        self._h2c(1.5)


def farkindalik():
    v = ctypes.c_int(-1)
    try:
        ctypes.windll.shcore.GetProcessDpiAwareness(None, ctypes.byref(v))
    except Exception as exc:                                   # pragma: no cover
        return f"OKUNAMADI({exc!r})"
    return v.value


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dpi", action="store_true")
    ap.add_argument("--mujoco", action="store_true",
                    help="olcumden ONCE test_sim_mujoco_arena kosulur — tam "
                         "suitteki GERCEK mekanizma (GL baglami farkindaligi "
                         "0->2 yapar); SetProcessDpiAwareness taklidi degil")
    a = ap.parse_args()
    if a.dpi:
        print("[dpi] SetProcessDpiAwareness(1) ->",
              ctypes.windll.shcore.SetProcessDpiAwareness(1), flush=True)
    if a.mujoco:
        print(f"[DPI] mujoco ONCESI = {farkindalik()}", flush=True)
        m = unittest.TestLoader().loadTestsFromName("test_sim_mujoco_arena")
        ms = unittest.TextTestRunner(verbosity=0).run(m)
        print(f"[DPI] mujoco SONRASI = {farkindalik()} · MUJOCO "
              f"{'OK' if ms.wasSuccessful() else 'DUSTU'}", flush=True)
    print(f"[DPI] farkindalik = {farkindalik()}", flush=True)
    takim = unittest.TestLoader().loadTestsFromTestCase(IzliH2c)
    sonuc = unittest.TextTestRunner(verbosity=2).run(takim)
    print("\n== OZET: _ana_denetle'in kostugu YUZEYLER ==", flush=True)
    yuzeyler = sorted({(o, b) for o, _ad, b, _c in IzliH2c.IZ})
    for o, b in yuzeyler:
        print(f"  olcek={o}: {b[0]}x{b[1]}", flush=True)
    for o in (1.0, 1.5):
        kume = {b for oo, _ad, b, _c in IzliH2c.IZ if oo == o}
        print(f"  olcek={o} FARKLI YUZEY SAYISI = {len(kume)}", flush=True)
    print(f"TOPLAM _ana_denetle cagrisi = {len(IzliH2c.IZ)}", flush=True)
    return 0 if sonuc.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
