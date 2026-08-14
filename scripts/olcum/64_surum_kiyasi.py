"""T63d — SABAH KIYASI: iki modeli AYNI dort olcutle karsilastir.

Tek komutla kosar; her olcut ayri betiktir ve KOPYALANMAZ, cagrilir:

  1. karar sinifi        60_kadraj_karar_dogrulugu.py   (serit tabanli — TANIMA BAGLI,
                                                         yalniz baglam icin)
  2. moloza basma        61_rota_moloza_basma.py        (TANIMDAN BAGIMSIZ — ASIL OLCUT)
  3. bariyer kesisimi    63_bariyer_kesisimi.py         (GERCEK arena · gorev kritik)

Kullanim:
  venv\\Scripts\\python.exe 64_surum_kiyasi.py \
      --modeller O:\\navitas\\models\\navitas_seg_v24_best.pt \
                 O:\\navitas\\codes\\runs\\segment\\v25_t60_renk\\weights\\best.pt
"""
import argparse
import subprocess
import sys
from pathlib import Path

BURASI = Path(__file__).parent
PY = Path(sys.executable)
KADRAJ = BURASI / "calisma" / "sentetik_arena_kadraj_t60"


def kos(betik, ek):
    p = subprocess.run([str(PY), "-B", str(BURASI / betik)] + ek,
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    return p.stdout or "", p.returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modeller", nargs="+", required=True, type=Path)
    args = ap.parse_args()

    for m in args.modeller:
        ad = m.parent.parent.name if m.name == "best.pt" else m.stem
        print("\n" + "=" * 74)
        print(f"MODEL: {ad}   ({m})")
        print("=" * 74)
        if not m.is_file():
            print("  !! agirlik YOK — atlandi")
            continue

        c, _ = kos("60_kadraj_karar_dogrulugu.py",
                   ["--model", str(m), "--kume", str(KADRAJ)])
        for s in c.splitlines():
            if any(k in s for k in ("TEHLIKELI", "DOGRU", "YANLIS", "RET ")):
                print("  [serit] " + s.strip())

        c, _ = kos("61_rota_moloza_basma.py",
                   ["--model", str(m), "--kume", str(KADRAJ)])
        for s in c.splitlines():
            if any(k in s for k in ("ROTA URETILDI", "MOLOZA BASIYOR",
                                    "AGIR BASMA", "ARENA DISINDA",
                                    "basma orani", "arena disi")):
                print("  [basma] " + s.strip())

        c, _ = kos("63_bariyer_kesisimi.py", ["--model", str(m)])
        for s in c.splitlines():
            if any(k in s for k in ("model ENGEL", "model ZEMIN",
                                    "ROTA x BARIYER", "karar:")):
                print("  [bariyer] " + s.strip())


if __name__ == "__main__":
    main()
