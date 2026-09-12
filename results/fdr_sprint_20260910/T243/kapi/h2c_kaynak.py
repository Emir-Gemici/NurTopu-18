"""H2c dusugu T243'ten mi? Modul suitten CIKARILIP suit yeniden kosulur."""
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

PY = r"O:\navitas-local-train\venv\Scripts\python.exe"
KOK = Path(r"O:\navitas\.claude\worktrees\wf_88f63745-bff-1")
MODUL = KOK / "tests" / "test_t243_paket_boyutu.py"
GECICI = KOK / "tests" / "t243_suit_disi_gecici.py"
CIKTI = KOK / "results" / "fdr_sprint_20260910" / "T243" / "kapi" / "tam_suit_t243siz.txt"


def suit():
    r = subprocess.run(
        [PY, "-X", "utf8", "-B", "-m", "unittest", "discover", "-s", "tests",
         "-p", "test_*.py"],
        cwd=str(KOK), capture_output=True, text=True, encoding="utf-8",
        errors="replace")
    return r.stdout + r.stderr


def main():
    sha = hashlib.sha256(MODUL.read_bytes()).hexdigest()
    shutil.move(str(MODUL), str(GECICI))
    try:
        c = suit()
    finally:
        shutil.move(str(GECICI), str(MODUL))
        assert hashlib.sha256(MODUL.read_bytes()).hexdigest() == sha
    CIKTI.write_text(
        "T243 modulu suit DISINDA (tests/test_t243_paket_boyutu.py gecici olarak\n"
        "kesif desenine uymayan bir ada alindi; kosumdan sonra sha256 ile geri\n"
        "yuklendi). Soru: H2c dusugu T243'ten mi geliyor?\n\n" + c,
        encoding="utf-8")
    ozet = [s for s in c.splitlines() if s.startswith(("Ran ", "OK", "FAILED"))]
    dusen = sorted(s.split(" ")[1] for s in c.splitlines()
                   if s.startswith(("FAIL: ", "ERROR: ")))
    print(" · ".join(ozet))
    print(f"dusen sayisi: {len(dusen)}")
    print("H2c dusuyor mu: "
          + ("EVET -> T243'ten DEGIL" if any("H2c" in d for d in dusen)
             else "HAYIR -> T243 ile iliskili olabilir"))
    print(f"-> {CIKTI}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
