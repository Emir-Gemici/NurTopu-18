"""T250 yalitim olcumu: master'in dd7cd12a commit'inin DELTASI (REVIEW_LOG.md ve
TASK_QUEUE.md) gecici olarak 46ffb503 surumune cevrilir, tam suit kosulur, sonra
iki dosya da sha256 dogrulanarak BAYT-ES geri yazilir.

Amac: son agactaki kirmiziligin TAMAMEN master'in dd7cd12a icerigi oldugunu,
bu dalin kendi iceriginin YESIL oldugunu olcmek. Bu dal o iki dosyaya DOKUNMAZ
(gorev kurali: REVIEW_LOG/TASK_QUEUE'ya dokunma).
"""
import hashlib, subprocess, sys
from pathlib import Path

KOK = Path(r"O:\navitas\.claude\worktrees\wf_56b658bb-aff-1")
ADLAR = ["REVIEW_LOG.md", "TASK_QUEUE.md"]
PYEXE = sys.executable

hamlar, shalar, eskiler = {}, {}, {}
for ad in ADLAR:
    f = KOK / ad
    hamlar[ad] = f.read_bytes()
    shalar[ad] = hashlib.sha256(hamlar[ad]).hexdigest()
    eskiler[ad] = subprocess.run(["git", "show", f"46ffb503:{ad}"], cwd=str(KOK),
                                 capture_output=True).stdout
    print(f"[YALITIM] {ad}: simdi {len(hamlar[ad])} B sha={shalar[ad][:16]}… · "
          f"46ffb503 {len(eskiler[ad])} B", flush=True)
    assert eskiler[ad] and eskiler[ad] != hamlar[ad]
try:
    for ad in ADLAR:
        (KOK / ad).write_bytes(eskiler[ad])
    p = subprocess.run([PYEXE, "-X", "utf8", "-B", "scripts/push_kapisi.py", "--kuru"],
                       cwd=str(KOK), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    print(p.stdout + p.stderr, flush=True)
    kod = p.returncode
finally:
    tamam = True
    for ad in ADLAR:
        (KOK / ad).write_bytes(hamlar[ad])
        yeni = hashlib.sha256((KOK / ad).read_bytes()).hexdigest()
        es = yeni == shalar[ad]
        tamam = tamam and es
        print(f"[YALITIM] {ad} geri yazildi sha={yeni[:16]}… "
              f"{'BAYT-ES' if es else 'BOZUK!'}", flush=True)
    assert tamam
print(f"YALITIM_SUITI EXIT={kod}", flush=True)
raise SystemExit(kod)
