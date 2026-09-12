"""T244 kapi kosucusu — gorev tanimindaki TUM kapilari kosar, ham ciktiyi kaydeder.

Kapilar (gorev tanimi):
  1. tests/test_fdr*.py            (yeni nobetci T244 dahil)
  2. tests/test_gece*.py
  3. tests/test_d373*.py
  4. scripts/fdr_acik_kalem_cikar.py --dogrula   (acik kalem listesi GUNCEL mi)
  5. tests/test_seri_pixhawk_kilidi.py  (madde 1 kaynak kapisi)
  6. tests/test_p5_h1c_damgasi.py       (madde 2 kaynak kapisi)
  7. codes/test_rota_sentetik.py        (GENEL KAPI, madde 14 -> 15/15)

Ham cikti: `T244/kapi_ciktisi.txt`. Cikis 0 = hepsi gecti.

KOSUM (depo kokunden):
  O:/navitas-local-train/venv/Scripts/python.exe -B -X utf8 \
      results/fdr_sprint_20260910/T244/kapi_t244.py
"""
import subprocess
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
KOK = Path(__file__).resolve().parents[3]
PY = sys.executable
CIKTI = Path(__file__).resolve().parent / "kapi_ciktisi.txt"

KAPILAR = [
    ("test_fdr*", [PY, "-B", "-X", "utf8", "-m", "unittest", "discover",
                   "-s", "tests", "-p", "test_fdr*.py"]),
    ("test_gece*", [PY, "-B", "-X", "utf8", "-m", "unittest", "discover",
                    "-s", "tests", "-p", "test_gece*.py"]),
    ("test_d373*", [PY, "-B", "-X", "utf8", "-m", "unittest", "discover",
                    "-s", "tests", "-p", "test_d373*.py"]),
    ("acik_kalem --dogrula", [PY, "-B", "-X", "utf8",
                              "scripts/fdr_acik_kalem_cikar.py", "--dogrula"]),
    ("test_seri_pixhawk_kilidi", [PY, "-B", "-X", "utf8", "-m", "unittest", "discover",
                                  "-s", "tests", "-p", "test_seri_pixhawk_kilidi.py"]),
    ("test_p5_h1c_damgasi", [PY, "-B", "-X", "utf8", "-m", "unittest", "discover",
                             "-s", "tests", "-p", "test_p5_h1c_damgasi.py"]),
    ("GENEL KAPI (madde 14)", [PY, "-B", "-X", "utf8", "codes/test_rota_sentetik.py"]),
]


def main():
    satirlar = ["# T244 kapi ciktisi · {} · {}".format(
        time.strftime("%Y-%m-%d %H:%M:%S"), Path(PY).name)]
    kotu = 0
    for ad, argv in KAPILAR:
        p = subprocess.run(argv, cwd=KOK, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=3600)
        cikti = (p.stdout + p.stderr).strip()
        kotu += 1 if p.returncode != 0 else 0
        satirlar += ["", "=" * 78, "KAPI: {}".format(ad),
                     "KOMUT: " + subprocess.list2cmdline(argv),
                     "EXIT: {}".format(p.returncode), "-" * 78, cikti]
        print("{:<26} exit={} {}".format(ad, p.returncode,
                                         cikti.strip().splitlines()[-1] if cikti else ""))
    satirlar += ["", "=" * 78,
                 "OZET: {}/{} kapi GECTI".format(len(KAPILAR) - kotu, len(KAPILAR))]
    CIKTI.write_text("\n".join(satirlar) + "\n", encoding="utf-8")
    print("OZET: {}/{} kapi GECTI -> {}".format(
        len(KAPILAR) - kotu, len(KAPILAR), CIKTI.relative_to(KOK).as_posix()))
    return 0 if kotu == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
