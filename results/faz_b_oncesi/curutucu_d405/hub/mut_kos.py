"""Verilen hub dosyasini 'seri_hub' olarak yukleyip tests/test_faz_b_seri_hub.py
suitini ona karsi kosar. Kullanim: mut_kos.py <hub.py>"""
import io
import sys
import unittest

from ortak import hub_modulu_yukle

dosya = sys.argv[1]
hub_modulu_yukle(dosya)
import test_faz_b_seri_hub as t  # noqa: E402

suite = unittest.defaultTestLoader.loadTestsFromModule(t)
akim = io.StringIO()
res = unittest.TextTestRunner(verbosity=1, stream=akim).run(suite)
dusen = [str(x[0]).split()[0] for x in res.failures + res.errors]
print(f"MUTANT {dosya.rsplit(chr(92), 1)[-1].rsplit('/', 1)[-1]}: ran={res.testsRun} "
      f"fail={len(res.failures)} err={len(res.errors)} "
      f"-> {'YAKALANDI ' + str(dusen) if dusen else 'HAYATTA (hicbir test dusmedi)'}")
