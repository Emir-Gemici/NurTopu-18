"""Mutanti enjekte edip ek_testler.py suitini kosar."""
import importlib.util
import os
import sys
import time
import unittest

BURASI = os.path.dirname(os.path.abspath(__file__))
KOK = r"O:\navitas"
for _y in ("comms", "codes", "tests"):
    _p = os.path.join(KOK, _y)
    if _p not in sys.path:
        sys.path.insert(0, _p)
if BURASI not in sys.path:
    sys.path.insert(0, BURASI)


def main():
    mutant = os.path.abspath(sys.argv[1])
    adlar = sys.argv[2:]
    spec = importlib.util.spec_from_file_location("seri_hub", mutant)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["seri_hub"] = mod
    spec.loader.exec_module(mod)
    import test_faz_b_seri_hub as T
    assert T.modul is mod
    import ek_testler as E
    assert E.modul is mod
    loader = unittest.defaultTestLoader
    if adlar:
        suite = unittest.TestSuite()
        for ad in adlar:
            suite.addTests(loader.loadTestsFromName(ad, E))
    else:
        suite = loader.loadTestsFromModule(E)
    t0 = time.monotonic()
    r = unittest.TextTestRunner(verbosity=2, stream=sys.stdout).run(suite)
    durum = "YAKALANDI" if (r.failures or r.errors) else "KACTI"
    print(f"EK-MUTANT {os.path.basename(mutant)}: {durum} ran={r.testsRun} "
          f"fail={len(r.failures)} err={len(r.errors)} "
          f"sure={time.monotonic() - t0:.1f}s", flush=True)
    for t, tb in r.failures + r.errors:
        son = [s for s in tb.strip().splitlines() if s.strip()][-1]
        print(f"  -> {t.id().split('.')[-1]}: {son[:220]}", flush=True)


if __name__ == "__main__":
    main()
