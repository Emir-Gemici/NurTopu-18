"""AKIS-D gercek veri karsilastirmasi: T227 kod degisikligi uzerinde eski / yeni tazeleyici.

Taban  = 56157d22 (T227'nin ebeveyni): codes/rpi_inference.py, codes/karar_sozlesmesi.py,
         comms/iha_sender.py, FDR/sekiller/akis_a.mmd
Calisma = 73a5b4f9 (T227 amelesi) codes/rpi_inference.py (+706 satir)
Hakem  = 73a5b4f9 FDR/sekiller/akis_a.mmd (amelenin ELLE duzelttigi, mimar
         t227_akis_kapsam.py ile "kapsam disi 0" dogruladi) — ayni ID'li dugumler.

Gecici bir git deposunda:
  1. ESKI tazeleyici (56157d22:scripts/akis_satir_tazele.py) .mmd kopyasi uzerinde,
  2. YENI tazeleyici (calisma agaci) --taban HEAD,
  3. her iki sonucun her dugumu icin satir + kapsam (qualname), hakemle karsilastirma,
  4. akis_diyagram_dogrula --taban HEAD eski aracin ciktisina: KAPSAM DEGISTI sayisi.
GPU yok, model yok. Kullanim: python t227_gercek_karsilastirma.py  (cikti stdout)
"""
import contextlib
import importlib.util
import io
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
DEPO = Path(__file__).resolve().parents[3]
TABAN, T227 = "56157d22", "73a5b4f9"
DOSYALAR = ("codes/rpi_inference.py", "codes/karar_sozlesmesi.py", "comms/iha_sender.py",
            "FDR/sekiller/akis_a.mmd")
KIMLIK = ("-c", "user.name=akis-d", "-c", "user.email=akis-d@example.invalid",
          "-c", "commit.gpgsign=false", "-c", "core.autocrlf=false")
PY = sys.executable

_sp = importlib.util.spec_from_file_location("akis_dogrula", DEPO / "scripts" / "akis_diyagram_dogrula.py")
D = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(D)


def git(kok, *a, bayt=False):
    r = subprocess.run(["git", *KIMLIK, *a], cwd=str(kok), capture_output=True)
    if r.returncode:
        raise RuntimeError(f"git {a}: {r.stderr.decode(errors='replace')}")
    return r.stdout if bayt else r.stdout.decode("utf-8", errors="replace")


def yerler(metin):
    d = {}
    for s in metin.replace("\r\n", "\n").split("\n"):
        m = re.match(r'^\s*(?:subgraph\s+)?([A-Za-z][A-Za-z0-9_]*)[\[{]"(?:.*)<br/>([^"<]+):(\d+)"', s)
        if m:
            d[m.group(1)] = (m.group(2), int(m.group(3)))
    return d


def main():
    gecici = Path(tempfile.mkdtemp(prefix="akis_d_t227_")).resolve()
    try:
        git(gecici, "init", "-q")
        for f in DOSYALAR:
            p = gecici / f
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(git(DEPO, "show", f"{TABAN}:{f}", bayt=True))
        git(gecici, "add", "-A")
        git(gecici, "commit", "-q", "-m", "taban 56157d22")
        (gecici / "codes/rpi_inference.py").write_bytes(
            git(DEPO, "show", f"{T227}:codes/rpi_inference.py", bayt=True))
        eski_betik = gecici / "_eski_tazele.py"
        eski_betik.write_bytes(git(DEPO, "show", f"{TABAN}:scripts/akis_satir_tazele.py", bayt=True))
        mmd = gecici / "FDR/sekiller/akis_a.mmd"
        taban_mmd = mmd.read_text(encoding="utf-8")
        hakem = yerler(git(DEPO, "show", f"{T227}:FDR/sekiller/akis_a.mmd"))

        # 1. ESKI arac (kopya uzerinde)
        eski_mmd = gecici / "_eski_akis_a.mmd"
        eski_mmd.write_text(taban_mmd, encoding="utf-8")
        r = subprocess.run([PY, str(eski_betik), str(gecici), str(eski_mmd)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        print(f"== ESKI tazeleyici (56157d22) cikis={r.returncode}\n{r.stdout.strip()}")
        eski = yerler(eski_mmd.read_text(encoding="utf-8"))

        # 2. YENI arac (--taban HEAD, gercek .mmd uzerinde)
        r = subprocess.run([PY, str(DEPO / "scripts/akis_satir_tazele.py"), str(gecici), str(mmd),
                            "--taban", "HEAD"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        print(f"\n== YENI tazeleyici --taban HEAD cikis={r.returncode}\n{r.stdout.strip()}")
        yeni = yerler(mmd.read_text(encoding="utf-8"))

        # 3. dugum dugum karsilastirma
        kaynak = D.KapsamKaynagi(gecici)
        def kap(dosya, satir, ref=None):
            h = kaynak.harita(dosya, ref)
            k = h.kapsam(satir) if h else None
            return D.kapsam_metni(k) if k else "?"
        taban = yerler(taban_mmd)
        print("\n== dugum | taban satir [kapsam] | ESKI arac | YENI arac | HAKEM (amele elle) | "
              "eski=hakem | yeni=hakem")
        say = {"eski_yanlis": [], "yeni_yanlis": [], "eski_kapsam_disi": [], "yeni_kapsam_disi": []}
        for kimlik, (dosya, ts) in taban.items():
            e, y, h = eski[kimlik][1], yeni[kimlik][1], hakem.get(kimlik, (dosya, None))[1]
            kt = kap(dosya, ts, "HEAD")
            ke, ky, kh = kap(dosya, e), kap(dosya, y), (kap(dosya, h) if h else "-")
            if e != h:
                say["eski_yanlis"].append(kimlik)
            if y != h:
                say["yeni_yanlis"].append(kimlik)
            if ke != kt:
                say["eski_kapsam_disi"].append(kimlik)
            if ky != kt:
                say["yeni_kapsam_disi"].append(kimlik)
            print(f"{kimlik:4} | {dosya}:{ts} [{kt}] | {e} [{ke}] | {y} [{ky}] | {h} [{kh}] | "
                  f"{'ok' if e == h else 'FARKLI'} | {'ok' if y == h else 'FARKLI'}")
        n = len(taban)
        print(f"\nOZET ({n} dugum): ESKI arac hakemden farkli {len(say['eski_yanlis'])} "
              f"{say['eski_yanlis']}; kapsam disi {len(say['eski_kapsam_disi'])} {say['eski_kapsam_disi']}")
        print(f"OZET ({n} dugum): YENI arac hakemden farkli {len(say['yeni_yanlis'])} "
              f"{say['yeni_yanlis']}; kapsam disi {len(say['yeni_kapsam_disi'])} {say['yeni_kapsam_disi']}")

        # 4. dogrula --taban eski aracin ciktisina (T227 kusurunun urettigi .mmd)
        mmd.write_text(eski_mmd.read_text(encoding="utf-8"), encoding="utf-8")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            ok_metin = D.dosyayi_dogrula(mmd, gecici)
            ok_kapsam = D.dosyayi_dogrula(mmd, gecici, taban="HEAD")
        print("\n== akis_diyagram_dogrula ESKI aracin ciktisina (seceneksiz, sonra --taban HEAD)")
        print(buf.getvalue().strip())
        print(f"seceneksiz gecti={ok_metin} · --taban HEAD gecti={ok_kapsam}")
    finally:
        def _yaz(islev, p, _h):
            os.chmod(p, stat.S_IWRITE)
            islev(p)
        shutil.rmtree(gecici, onexc=_yaz)


if __name__ == "__main__":
    main()
