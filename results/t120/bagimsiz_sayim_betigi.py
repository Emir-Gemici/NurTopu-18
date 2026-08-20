"""T120 BAGIMSIZ SAYIM — mimarin yonteminden FARKLI iki yolla.

Mimarin yontemi: in-process `unittest.defaultTestLoader.discover(pattern=...)`,
ciktisi bastirilmis, countTestCases()<=0 sayildi.

BURADAKI IKI FARKLI YOL:
  A) ALT SUREC: her dosya icin `python -m unittest discover -s tests -p <ad> -v`
     ayri bir surecte kosulur, "Ran N tests" satiri AYRISTIRILIR. Bu yol
     in-process loader'in yuttugu/gizledigi ImportError'lari ve modul duzeyinde
     patlayan dosyalari GORUR (cikis kodu + stderr).
  B) AST: dosya PARSE edilir; unittest.TestCase turevi sinif ve `test_` ile
     baslayan metod sayilir; ayrica `load_tests`, `suite()` gibi ozel kesif
     kancalari aranir (bunlar TestCase olmadan da test toplatabilir).

Iki yol AYRISIRSA bu bir bulgudur ve raporlanir.
"""
import ast
import io
import json
import re
import subprocess
import sys
from pathlib import Path

KOK = Path(r"O:\navitas")
TESTS = KOK / "tests"
PY = r"O:\navitas-local-train\venv\Scripts\python.exe"

sonuc = []
for p in sorted(TESTS.glob("*.py")):
    # ── A: alt surec kosumu ────────────────────────────────────────────────
    r = subprocess.run(
        [PY, "-B", "-m", "unittest", "discover", "-s", str(TESTS),
         "-p", p.name],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(KOK), timeout=900,
    )
    cikti = (r.stdout or "") + (r.stderr or "")
    m = re.search(r"^Ran (\d+) tests?", cikti, re.M)
    alt_surec_n = int(m.group(1)) if m else None
    import_hatasi = ("ImportError" in cikti or "ModuleNotFoundError" in cikti
                     or "_FailedTest" in cikti)

    # ── B: AST ─────────────────────────────────────────────────────────────
    kaynak = p.read_text(encoding="utf-8", errors="replace")
    try:
        agac = ast.parse(kaynak)
        ast_ok = True
    except SyntaxError:
        agac, ast_ok = None, False
    testcase_sinif, test_metod, kanca = 0, 0, []
    if agac is not None:
        for d in ast.walk(agac):
            if isinstance(d, ast.ClassDef):
                tabanlar = []
                for b in d.bases:
                    tabanlar.append(ast.unparse(b))
                if any("TestCase" in t for t in tabanlar):
                    testcase_sinif += 1
                    for g in d.body:
                        if isinstance(g, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                                and g.name.startswith("test"):
                            test_metod += 1
            if isinstance(d, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                    and d.name in ("load_tests", "suite", "additional_tests"):
                kanca.append(d.name)

    sonuc.append({
        "dosya": p.name,
        "alt_surec_ran": alt_surec_n,
        "alt_surec_exit": r.returncode,
        "import_hatasi": import_hatasi,
        "ast_testcase_sinifi": testcase_sinif,
        "ast_test_metodu": test_metod,
        "ast_kancalari": kanca,
        "ast_parse_ok": ast_ok,
        "kesif_kalibinda": p.name.startswith("test"),
    })
    print(f"{p.name:52s} ran={str(alt_surec_n):>5s} exit={r.returncode} "
          f"ast={testcase_sinif}/{test_metod} kalip={p.name.startswith('test')}",
          flush=True)

cikti_yolu = Path(__file__).with_name("t120_bagimsiz.json")
io.open(cikti_yolu, "w", encoding="utf-8").write(
    json.dumps(sonuc, ensure_ascii=False, indent=1))

sifir_alt = [s for s in sonuc if not s["alt_surec_ran"]]
sifir_ast = [s for s in sonuc if s["ast_test_metodu"] == 0 and not s["ast_kancalari"]]
kalip_disi = [s for s in sonuc if not s["kesif_kalibinda"]]
ayrisan = [s for s in sonuc
           if bool(s["alt_surec_ran"]) != bool(s["ast_test_metodu"] or s["ast_kancalari"])]

print("\n" + "=" * 70)
print(f"toplam .py                     : {len(sonuc)}")
print(f"A) alt surecte SIFIR test      : {len(sifir_alt)}  -> {[s['dosya'] for s in sifir_alt]}")
print(f"B) AST'de test metodu YOK      : {len(sifir_ast)}  -> {[s['dosya'] for s in sifir_ast]}")
print(f"kesif kalibi disi (test* degil): {len(kalip_disi)}  -> {[s['dosya'] for s in kalip_disi]}")
print(f"IKI YOL AYRISAN                : {len(ayrisan)}  -> {[s['dosya'] for s in ayrisan]}")
print(f"import hatasi goren            : {[s['dosya'] for s in sonuc if s['import_hatasi']]}")
print(f"json -> {cikti_yolu}")
