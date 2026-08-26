"""T153 olcum surucusu — GPU isleri SIRALI (ayni anda tek YOLO sureci; PC 2026-08-26 BSOD).

Her is: ana depodaki olcum betigi (scripts/olcum/142 veya 65), PYTHONPATH bu dizin
(sitecustomize -> worktree codes onceden yuklenir), NAVITAS_INCE_BETON_SERIT=1 (ACIK)
ya da 0 (KAPALI). Ciktilar results/t153/olcum, loglar results/t153/log.
Kullanim: surucu.py <is_adi> [<is_adi> ...]   (is adlari asagidaki ISLER'den)
"""
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

PY = r"O:\navitas-local-train\venv\Scripts\python.exe"
ANA = Path(r"O:\navitas")
WT = Path(r"O:\navitas\.claude\worktrees\wf_2d1c9d5e-54f-1")
BURASI = Path(__file__).resolve().parent
T153 = WT / "results" / "t153"
OLCUM = T153 / "olcum"
LOG = T153 / "log"
V3 = ANA / "dataset" / "dji_kirsal_0038_bolum_v3"
GECE = ANA / "results" / "gece_20260826"
AGIRLIK = {
    "v35": ANA / "models" / "navitas_seg_v35_best.pt",
    "v3": ANA / "codes" / "runs" / "segment" / "gece_v3_v35taban" / "weights" / "best.pt",
    "v6": ANA / "codes" / "runs" / "segment" / "gece_v6_v35taban" / "weights" / "best.pt",
}
BOLUM = {
    "test29": (V3 / "images" / "test", V3 / "labels" / "test", GECE / "test29_etiket_tavani_v3.json"),
    "val82": (V3 / "images" / "val", V3 / "labels" / "val", GECE / "sizinti" / "val82_etiket_tavani.json"),
}


def ortam(acik):
    e = dict(os.environ)
    e["PYTHONPATH"] = str(BURASI)
    e["NAVITAS_INCE_BETON_SERIT"] = "1" if acik else "0"
    e["PYTHONIOENCODING"] = "utf-8"
    return e


def kos(ad, cmd, acik, cwd=ANA):
    LOG.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    print(f"== {ad} ({'ACIK' if acik else 'KAPALI'}) basladi {time.strftime('%H:%M:%S')}", flush=True)
    with open(LOG / f"{ad}.log", "w", encoding="utf-8") as f:
        f.write("CMD: " + " ".join(str(c) for c in cmd) + f"\nNAVITAS_INCE_BETON_SERIT={'1' if acik else '0'}\n\n")
        f.flush()
        r = subprocess.run([str(c) for c in cmd], cwd=str(cwd), env=ortam(acik), stdout=f, stderr=subprocess.STDOUT)
    print(f"   bitti {time.time() - t0:.0f} sn exit {r.returncode}", flush=True)
    return r.returncode


def is_142(model, bolum, acik):
    kip = "acik" if acik else "kapali"
    ad = f"t153_{kip}_{model}_{bolum}"
    kare, etiket, tavan = BOLUM[bolum]
    OLCUM.mkdir(parents=True, exist_ok=True)
    cmd = [PY, ANA / "scripts" / "olcum" / "142_gece_olcum.py", "--agirlik", AGIRLIK[model], "--ad", ad,
           "--atla-kabul", "--test-dizin", kare, "--etiket-dizin", etiket, "--tavan", tavan, "--cikti", OLCUM]
    return kos(ad, cmd, acik)


def is_65(model, acik):
    kip = "acik" if acik else "kapali"
    ad = f"t153_{kip}_{model}"
    cmd = [PY, ANA / "scripts" / "olcum" / "65_kabul_denetcisi.py", "--model", AGIRLIK[model], "--ad", ad]
    rc = kos(ad + "_65", cmd, acik)
    kabul = T153 / "kabul"
    kabul.mkdir(parents=True, exist_ok=True)
    for son in ("_kabul_verdikt.json", "_kabul.json", "_k5_populasyon.json"):
        kaynak = ANA / "scripts" / "olcum" / "results" / "t63" / f"{ad}{son}"
        if kaynak.is_file():
            shutil.copy2(kaynak, kabul / kaynak.name)
    return rc


ISLER = {}
for _m in ("v35", "v3", "v6"):
    for _b in ("test29", "val82"):
        for _a in (True, False):
            ISLER[f"142_{_m}_{_b}_{'acik' if _a else 'kapali'}"] = (lambda m=_m, b=_b, a=_a: is_142(m, b, a))
    for _a in (True, False):
        ISLER[f"65_{_m}_{'acik' if _a else 'kapali'}"] = (lambda m=_m, a=_a: is_65(m, a))

if __name__ == "__main__":
    for ad in sys.argv[1:]:
        ISLER[ad]()
    print("TUMU BITTI", time.strftime("%H:%M:%S"))
