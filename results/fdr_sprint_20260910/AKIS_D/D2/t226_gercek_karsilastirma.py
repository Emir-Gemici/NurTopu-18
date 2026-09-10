"""AKIS-D2 EK gercek veri: T226 / T226-D kod degisiklikleri uzerinde ESKI / YENI tazeleyici (akis_d).

T226-D amelesi bulgusu (REVIEW_LOG D-453): master'daki akis_satir_tazele'nin dugum deseni
`subgraph …["def …<br/>dosya:N"]` basliklarini yakalamiyor; basliklar elle AST ile tazelendi.
Iki GERCEK gecis (her biri gecici git deposunda: taban commit'lenir, calisma = sonraki surum):
  G1  9472ba47 → 77853afb  (T226)
  G2  77853afb → 15ad56d0  (T226-D WIP)
Hakem = sonraki commit'teki FDR/sekiller/akis_d.mmd (amelenin tazeledigi; basliklar elle AST).
  1. ESKI tazeleyici (master:scripts/akis_satir_tazele.py) .mmd KOPYASI uzerinde,
  2. YENI tazeleyici (calisma agaci) VARSAYILAN taban ile gercek .mmd uzerinde,
  3. her dugum: ESKI / YENI / HAKEM satiri + calisma agacindaki kapsam; alt-grafik basliklari
     ayrica sayilir; yalniz farkli satirlar ve TUM basliklar basilir,
  4. akis_diyagram_dogrula (YENI) ESKI aracin ciktisina: seceneksiz ve --taban HEAD.
Dugum ayristirma araclardan BAGIMSIZ kendi desenimizle (hakem tarafi araca guvenmez).
GPU yok, model yok. Kullanim: python t226_gercek_karsilastirma.py  (cikti stdout)
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
DEPO = Path(__file__).resolve().parents[4]
PY = sys.executable
MMD_YOL = "FDR/sekiller/akis_d.mmd"
GECISLER = (("G1 T226", "9472ba47", "77853afb"), ("G2 T226-D", "77853afb", "15ad56d0"))
ESKI_REF = "master"
KIMLIK = ("-c", "user.name=akis-d2", "-c", "user.email=akis-d2@example.invalid",
          "-c", "commit.gpgsign=false", "-c", "core.autocrlf=false")

_sp = importlib.util.spec_from_file_location("akis_dogrula_yeni", DEPO / "scripts" / "akis_diyagram_dogrula.py")
D = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(D)
RE_YER = re.compile(r'^\s*(subgraph\s+)?([A-Za-z][A-Za-z0-9_]*)\s*[\[{]"(?:.*)<br\s*/?>([^"<]+):(\d+)"')


def git(kok, *a, bayt=False):
    r = subprocess.run(["git", *KIMLIK, *a], cwd=str(kok), capture_output=True)
    if r.returncode:
        raise RuntimeError(f"git {a}: {r.stderr.decode(errors='replace')}")
    return r.stdout if bayt else r.stdout.decode("utf-8", errors="replace")


def yerler(metin):
    """ID → (dosya, satir, alt-grafik basligi mi)."""
    d = {}
    for s in metin.replace("\r\n", "\n").split("\n"):
        m = RE_YER.match(s)
        if m:
            d[m.group(2)] = (m.group(3), int(m.group(4)), bool(m.group(1)))
    return d


def kos(*a):
    r = subprocess.run([PY, *map(str, a)], capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    return r.returncode, (r.stdout + r.stderr).strip()


def gecis(ad, taban, calisma):
    print(f"\n{'=' * 100}\n{ad}: taban {taban} → calisma {calisma} · hakem {calisma}:{MMD_YOL}")
    g = Path(tempfile.mkdtemp(prefix="akis_d2_t226_")).resolve()
    try:
        git(g, "init", "-q")
        taban_mmd = git(DEPO, "show", f"{taban}:{MMD_YOL}")
        tb = yerler(taban_mmd)
        dosyalar = sorted({v[0] for v in tb.values()})
        for f in dosyalar + [MMD_YOL]:
            p = g / f
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(git(DEPO, "show", f"{taban}:{f}", bayt=True))
        git(g, "add", "-A")
        git(g, "commit", "-q", "-m", f"taban {taban}")
        degisen_kod = []
        for f in dosyalar:
            yeni = git(DEPO, "show", f"{calisma}:{f}", bayt=True)
            if yeni != (g / f).read_bytes():
                degisen_kod.append(f)
            (g / f).write_bytes(yeni)
        print(f"kod dosyalari {dosyalar} · degisen {degisen_kod}")
        hakem = yerler(git(DEPO, "show", f"{calisma}:{MMD_YOL}"))
        eski_dizin = g / "_eski"
        eski_dizin.mkdir()
        for f in ("akis_satir_tazele.py", "akis_diyagram_dogrula.py"):
            (eski_dizin / f).write_bytes(git(DEPO, "show", f"{ESKI_REF}:scripts/{f}", bayt=True))
        mmd = g / MMD_YOL
        eski_mmd = g / "_eski_akis_d.mmd"
        eski_mmd.write_bytes(mmd.read_bytes())

        rc, out = kos(eski_dizin / "akis_satir_tazele.py", g, eski_mmd)
        print(f"\n-- 1. ESKI tazeleyici ({ESKI_REF}) cikis={rc}\n   " + out.splitlines()[-1])
        eski = yerler(eski_mmd.read_text(encoding="utf-8"))
        rc, out = kos(DEPO / "scripts" / "akis_satir_tazele.py", g, mmd)
        satirlar = out.splitlines()
        print(f"-- 2. YENI tazeleyici (varsayilan taban) cikis={rc}\n   " + satirlar[0]
              + "\n   " + satirlar[-1])
        for s in satirlar:
            if "HATA" in s or "TABAN" in s and "taban:" not in s:
                print(f"   {s}")
        yeni = yerler(mmd.read_text(encoding="utf-8"))

        kaynak = D.KapsamKaynagi(g)

        def kap(dosya, satir, ref=None):
            h = kaynak.harita(dosya, ref)
            k = h.kapsam(satir) if h and satir else None
            return D.kapsam_metni(k) if k else "?"

        print("\n-- 3. dugum | taban [kapsam] | ESKI | YENI | HAKEM   (yalniz farkli olanlar + TUM basliklar)")
        say = {k: [] for k in ("eski_fark", "yeni_fark", "eski_baslik_fark", "yeni_baslik_fark",
                               "yeni_kapsam_disi", "hakemde_yok")}
        basliklar = 0
        for kimlik, (dosya, ts, baslik) in tb.items():
            basliklar += baslik
            if kimlik not in hakem:
                say["hakemde_yok"].append(kimlik)
                continue
            e, y, h = eski[kimlik][1], yeni[kimlik][1], hakem[kimlik][1]
            kt, ke, ky, kh = kap(dosya, ts, "HEAD"), kap(dosya, e), kap(dosya, y), kap(dosya, h)
            if e != h:
                say["eski_fark"].append(kimlik)
                if baslik:
                    say["eski_baslik_fark"].append(kimlik)
            if y != h:
                say["yeni_fark"].append(kimlik)
                if baslik:
                    say["yeni_baslik_fark"].append(kimlik)
            if ky != kt:
                say["yeni_kapsam_disi"].append(kimlik)
            if baslik or e != h or y != h:
                print(f"   {kimlik:5}{'(baslik)' if baslik else '        '} | {dosya}:{ts} [{kt}] | "
                      f"{e} [{ke}] {'ok' if e == h else 'FARKLI'} | {y} [{ky}] "
                      f"{'ok' if y == h else 'FARKLI'} | {h} [{kh}]")
        n = len(tb)
        print(f"\nOZET {ad} ({n} dugum, {basliklar} alt-grafik basligi): ESKI hakemden farkli "
              f"{len(say['eski_fark'])} (baslik {len(say['eski_baslik_fark'])}: {say['eski_baslik_fark']})")
        print(f"OZET {ad} ({n} dugum, {basliklar} alt-grafik basligi): YENI hakemden farkli "
              f"{len(say['yeni_fark'])} {say['yeni_fark']} (baslik {len(say['yeni_baslik_fark'])}) · "
              f"YENI kapsam disi {len(say['yeni_kapsam_disi'])} {say['yeni_kapsam_disi']} · hakemde yok "
              f"{say['hakemde_yok']}")

        mmd.write_bytes(eski_mmd.read_bytes())
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            ok_m = D.dosyayi_dogrula(mmd, g)
            ok_k = D.dosyayi_dogrula(mmd, g, taban="HEAD")
        hatalar = [s for s in buf.getvalue().splitlines() if s.strip().startswith(("HATA", "KAPSAM"))]
        bas_hata = [s for s in hatalar if re.search(r"\bsD\d+\b", s)]
        print(f"-- 4. dogrula ESKI aracin ciktisina: seceneksiz gecti={ok_m} · --taban HEAD gecti={ok_k} · "
              f"hata satiri {len(hatalar)}, alt-grafik basligina ait {len(bas_hata)}")
        for s in bas_hata[:3]:
            print(f"   {s.strip()}")
    finally:
        def _yaz(islev, p, _h):
            os.chmod(p, stat.S_IWRITE)
            islev(p)
        shutil.rmtree(g, onexc=_yaz)


def main():
    print(f"ESKI arac: {ESKI_REF}:scripts/akis_satir_tazele.py = "
          + git(DEPO, "log", "-1", "--format=%h %s", ESKI_REF, "--", "scripts/akis_satir_tazele.py").strip()[:90])
    for ad, taban, calisma in GECISLER:
        gecis(ad, taban, calisma)


if __name__ == "__main__":
    main()
