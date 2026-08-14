"""Navitas v3 yerel eğitim — ortak ayarlar ve yardımcılar.

Kod O:\\navitas reposunda kalır (tek doğru kaynak); bu klasör yalnızca
çalışma alanıdır (venv, log, kanıt çıktıları). Colab eşleniği:
navitas-model-guclendirme.ipynb — buradaki 01→04 akışı onun birebir yerelidir.
"""
import os
import subprocess
from pathlib import Path

REPO    = Path(r"O:\navitas")
BURASI  = Path(__file__).parent
CALISMA = BURASI / "calisma"          # log + kanıt dosyaları buraya
CALISMA.mkdir(exist_ok=True)
LOG     = CALISMA / "konsol.log"

DATA_YAML   = REPO / "dataset" / "rescuenet_yolo" / "data.yaml"
RUN_NAME    = "navitas_seg_v3"
BEST        = REPO / "codes" / "runs" / "segment" / RUN_NAME / "weights" / "best.pt"
MODEL_HEDEF = REPO / "models" / "navitas_seg_v3_best.pt"


def logla(*p):
    s = " ".join(str(x) for x in p)
    print(s)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(s + "\n")


def komut(args, cwd=None):
    """Alt komutu koştur; çıktıyı ekrana VE konsol.log'a akıt."""
    logla(f"\n$ {' '.join(str(a) for a in args)}")
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    pr = subprocess.Popen([str(a) for a in args], cwd=cwd, env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          text=True, encoding="utf-8", errors="replace")
    for satir in pr.stdout:
        logla(satir.rstrip("\n").split("\r")[-1])
    pr.wait()
    logla(f"[çıkış: {pr.returncode}]")
    return pr.returncode
