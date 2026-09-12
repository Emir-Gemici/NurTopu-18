"""AKIS-D2 KUSUR-1 karsi-ornegi (curutucu, fd65b427 RED): kod commit'lenip .mmd tazelenmediyse.

Gecici GERCEK git deposu (curutucunun kurgusu aynen):
  taban (HEAD~1): pkg/mod.py f2:2 ve f1:8 'sonuc = hesapla(x)'; tek dugum n1 → pkg/mod.py:8 (f1).
  HEAD          : basa f3 eklenip COMMIT'lendi; ayni metin 8 (f3), 13 (f2), 19 (f1).
Beklenen:
  ESKI (fd65b427) tazeleyici varsayilan HEAD → cikis 0, n1 :8'de (f3) kalir, baslik damgalanir
                  (curutucunun olctugu SESSIZ kayma); ESKI dogrula --taban HEAD 'tuttu'.
  YENI tazeleyici varsayilan → TABAN SUPHELI, cikis 2, .mmd bayt-es; --taban HEAD~1 → 19 [f1].
  YENI dogrula --taban HEAD → TABAN SUPHELI; --taban HEAD~1 → KAPSAM DEGISTI [f1] → [f3].
Araclar gercek CLI (alt surec) ya da dosyayi_dogrula ile kosulur; ESKI araclar
`git show fd65b427:scripts/...` ile gecici dizine alinir. GPU yok, model yok.
Kullanim: python kusur1_karsi_ornek.py  (cikti stdout)
"""
import contextlib
import importlib.util
import io
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
DEPO = Path(__file__).resolve().parents[4]
PY = sys.executable
ESKI_REF = "fd65b427"
KIMLIK = ("-c", "user.name=akis-d2", "-c", "user.email=akis-d2@example.invalid",
          "-c", "commit.gpgsign=false", "-c", "core.autocrlf=false")
TABAN_KOD = ("def f2(x):\n    sonuc = hesapla(x)\n    return sonuc\n\n\n"
             "def f1(x):\n    y = x + 1\n    sonuc = hesapla(x)\n    return sonuc\n")
F3 = ("def f3(x):\n" + "".join(f"    a{i} = {i}\n" for i in range(6))
      + "    sonuc = hesapla(x)\n    return sonuc\n\n\n")
MMD = ("%% koddan turetildi 0000000 2026-09-10\nflowchart TD\n"
       '  n1["sonuc = hesapla(x)<br/>pkg/mod.py:8"]\n')


def git(kok, *a, bayt=False):
    r = subprocess.run(["git", *KIMLIK, *a], cwd=str(kok), capture_output=True)
    if r.returncode:
        raise RuntimeError(f"git {a}: {r.stderr.decode(errors='replace')}")
    return r.stdout if bayt else r.stdout.decode("utf-8", errors="replace")


def modul(ad, yol):
    sp = importlib.util.spec_from_file_location(ad, yol)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def kos(betik, *a):
    r = subprocess.run([PY, str(betik), *map(str, a)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return r.returncode, (r.stdout + r.stderr).strip()


def dogrula(D, mmd, kok, taban):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        ok = D.dosyayi_dogrula(mmd, kok, taban=taban)
    return ok, buf.getvalue().strip()


def goster(mmd):
    return [s for s in mmd.read_text(encoding="utf-8").splitlines()
            if s.startswith("%%") or "n1[" in s]


def main():
    g = Path(tempfile.mkdtemp(prefix="akis_d2_k1_")).resolve()
    try:
        git(g, "init", "-q")
        (g / "pkg").mkdir()
        (g / "sekil").mkdir()
        (g / "pkg" / "mod.py").write_bytes(TABAN_KOD.encode("utf-8"))
        mmd = g / "sekil" / "akis_t.mmd"
        mmd.write_bytes(MMD.encode("utf-8"))
        git(g, "add", "-A")
        git(g, "commit", "-q", "-m", "taban")
        (g / "pkg" / "mod.py").write_bytes((F3 + TABAN_KOD).encode("utf-8"))
        git(g, "commit", "-q", "-am", "basa f3 (.mmd tazelenmedi)")
        print("depo: HEAD~1 = taban (f2:2, f1:8) · HEAD = basa f3 (f3:8, f2:13, f1:19) · "
              "n1 → pkg/mod.py:8 · .mmd'nin son commit'i HEAD~1")
        eski = g / "_eski"
        eski.mkdir()
        for f in ("akis_satir_tazele.py", "akis_diyagram_dogrula.py"):
            (eski / f).write_bytes(git(DEPO, "show", f"{ESKI_REF}:scripts/{f}", bayt=True))
        De = modul("akis_dogrula_eski", eski / "akis_diyagram_dogrula.py")
        Dy = modul("akis_dogrula_yeni", DEPO / "scripts" / "akis_diyagram_dogrula.py")
        yeni_tazele = DEPO / "scripts" / "akis_satir_tazele.py"

        print(f"\n== 1. ESKI ({ESKI_REF}) dogrula --taban HEAD")
        ok, out = dogrula(De, mmd, g, "HEAD")
        print(out)
        print(f"gecti={ok}")
        print("\n== 2. YENI dogrula --taban HEAD")
        ok, out = dogrula(Dy, mmd, g, "HEAD")
        print(out)
        print(f"gecti={ok}")
        print("\n== 3. YENI dogrula --taban HEAD~1 (dogru taban)")
        ok, out = dogrula(Dy, mmd, g, "HEAD~1")
        print(out)
        print(f"gecti={ok}")

        once = mmd.read_bytes()
        rc, out = kos(yeni_tazele, g, mmd)
        print(f"\n== 4. YENI tazeleyici varsayilan cikis={rc}\n{out}")
        print(f"   .mmd bayt-es: {mmd.read_bytes() == once}")
        rc, out = kos(yeni_tazele, g, mmd, "--taban", "HEAD~1", "--kuru")
        print(f"\n== 5. YENI tazeleyici --taban HEAD~1 --kuru cikis={rc}\n{out}")

        rc, out = kos(eski / "akis_satir_tazele.py", g, mmd)
        print(f"\n== 6. ESKI ({ESKI_REF}) tazeleyici varsayilan (HEAD) cikis={rc}\n{out}")
        for s in goster(mmd):
            print(f"   {s}")
        h = Dy.KapsamKaynagi(g).harita("pkg/mod.py")
        print(f"   n1 :8 calisma agacinda [{Dy.kapsam_metni(h.kapsam(8))}] (dogrusu 19 [f1]) · "
              f"dosya degisti (baslik damgasi): {mmd.read_bytes() != once}")
    finally:
        def _yaz(islev, p, _h):
            os.chmod(p, stat.S_IWRITE)
            islev(p)
        shutil.rmtree(g, onexc=_yaz)


if __name__ == "__main__":
    main()
