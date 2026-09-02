"""Mutant seri_hub modulunu `sys.modules['seri_hub']` olarak enjekte edip
tests/test_faz_b_seri_hub.py suitini kosar. Repo DEGISMEZ.

Kullanim: kos_mutant.py <mutant.py> [TestSinifi.test_adi ...]
"""
import importlib.util
import os
import sys
import time
import unittest

KOK = r"O:\navitas"
for _y in ("comms", "codes", "tests"):
    _p = os.path.join(KOK, _y)
    if _p not in sys.path:
        sys.path.insert(0, _p)


class _Sonuc(unittest.TextTestResult):
    def startTest(self, test):
        self._t0 = time.monotonic()
        super().startTest(test)

    def stopTest(self, test):
        super().stopTest(test)
        print(f"  [sure] {test.id().split('.')[-1]} "
              f"{time.monotonic() - self._t0:.2f}s", file=sys.__stdout__,
              flush=True)


def main():
    mutant = os.path.abspath(sys.argv[1])
    adlar = sys.argv[2:]
    spec = importlib.util.spec_from_file_location("seri_hub", mutant)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["seri_hub"] = mod
    spec.loader.exec_module(mod)
    import test_faz_b_seri_hub as T
    assert T.modul is mod, "enjeksiyon basarisiz: test modulu orijinali aldi"
    assert T.SeriHub is mod.SeriHub
    assert mod.__file__ == mutant, mod.__file__
    loader = unittest.defaultTestLoader
    if adlar:
        suite = unittest.TestSuite()
        for ad in adlar:
            suite.addTests(loader.loadTestsFromName(ad, T))
    else:
        suite = loader.loadTestsFromModule(T)
    t0 = time.monotonic()
    r = unittest.TextTestRunner(verbosity=1, stream=sys.stdout,
                                resultclass=_Sonuc).run(suite)
    durum = "YAKALANDI" if (r.failures or r.errors) else "KACTI"
    print(f"MUTANT {os.path.basename(mutant)}: {durum} ran={r.testsRun} "
          f"fail={len(r.failures)} err={len(r.errors)} "
          f"sure={time.monotonic() - t0:.1f}s", flush=True)
    for t, tb in r.failures + r.errors:
        son = [s for s in tb.strip().splitlines() if s.strip()][-1]
        print(f"  -> {t.id().split('.')[-1]}: {son[:220]}", flush=True)
    return 0 if durum == "YAKALANDI" else 1


if __name__ == "__main__":
    raise SystemExit(main())
