"""T243 disi dusuklerin TABAN (master) kosumuyla ayni olduğunu olcer."""
import subprocess
import sys
from pathlib import Path

PY = r"O:\navitas-local-train\venv\Scripts\python.exe"
TABAN = Path(r"C:\Users\yunus\AppData\Local\Temp\claude\O--navitas"
             r"\3e104177-9b44-4ec7-a18f-1f32ed2c3f72\scratchpad\master_taban")
DAL = Path(r"O:\navitas\.claude\worktrees\wf_88f63745-bff-1")

MODULLER = ["test_imgsz_tek_kaynak", "test_model_registry", "test_saha_parametrik",
            "test_t123_gecis_provasi", "test_t202_jetson_paket_butunlugu",
            "test_t38_kuru_kosu_fiksturu", "test_yks_gui_uretim_hizasi"]


def kos(kok, modul):
    r = subprocess.run(
        [PY, "-X", "utf8", "-B", "-m", "unittest", "discover", "-s", "tests",
         "-p", modul + ".py"],
        cwd=str(kok), capture_output=True, text=True, encoding="utf-8",
        errors="replace")
    cikti = r.stdout + r.stderr
    ozet = [s for s in cikti.splitlines() if s.startswith(("Ran ", "OK", "FAILED"))]
    dusen = sorted(s.split(" ")[1] for s in cikti.splitlines()
                   if s.startswith(("FAIL: ", "ERROR: ")))
    return " · ".join(ozet), dusen


def main():
    print(f"TABAN dizini: {TABAN}  (master, git archive)")
    print(f"DAL dizini  : {DAL}")
    ayni = 0
    for m in MODULLER:
        t_ozet, t_dusen = kos(TABAN, m)
        d_ozet, d_dusen = kos(DAL, m)
        # OLCUT: daldaki dusen kume TABANIN ALT KUMESI olmali. Esitlik sart
        # degildir — taban `git archive` ciktisi oldugu icin bazi izlenmeyen
        # veri dizinleri orada da yoktur ve taban FAZLA dusebilir. Dalda
        # TABANDA OLMAYAN bir dusuk cikarsa gerileme vardir.
        altkume = set(d_dusen) <= set(t_dusen)
        ayni += altkume
        yeni = sorted(set(d_dusen) - set(t_dusen))
        print(f"\n[{m}]")
        print(f"  TABAN: {t_ozet}")
        print(f"  DAL  : {d_ozet}")
        print(f"  dal dusukleri TABANIN ALT KUMESI mi: "
              f"{'EVET' if altkume else 'HAYIR'}"
              + ("" if t_dusen == d_dusen else "  (kume ESIT DEGIL)"))
        print(f"    taban: {t_dusen}")
        print(f"    dal  : {d_dusen}")
        if yeni:
            print(f"    🔴 DALDA YENI DUSEN: {yeni}")
    print(f"\nSONUC: {ayni}/{len(MODULLER)} modulde dal dusukleri tabanin alt "
          "kumesi — T243 kaynakli YENI dusuk YOK")
    return 0 if ayni == len(MODULLER) else 1


if __name__ == "__main__":
    sys.exit(main())
