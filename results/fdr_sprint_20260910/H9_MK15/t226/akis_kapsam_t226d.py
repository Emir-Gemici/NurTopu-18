"""T226-D — akış d tazelemesinin KAPSAM (qualname) denetimi (D-448 §6, AKIS-D).

NEDEN: `scripts/akis_satir_tazele.py` düğüm etiketini dosyada eski satıra EN
YAKIN yerde arar; büyük eklemede düğümü BAŞKA fonksiyondaki aynı metne
bağlayabiliyor (T227'de 12 düğüm). `akis_diyagram_dogrula` yalnız metni
denetler. Bu betik, satırı değişen HER düğüm için eski satırın (taban
commit'teki kaynak) ve yeni satırın (çalışma ağacı) içinde bulunduğu en içteki
fonksiyon/sınıf adını (qualname, AST) karşılaştırır; farklıysa HATA.

KOSUM (depo kökünden, tazelemeden SONRA):
  O:/navitas-local-train/venv/Scripts/python.exe -B \
      results/fdr_sprint_20260910/H9_MK15/t226/akis_kapsam_t226d.py [--taban HEAD]
Çıkış: 0 hepsi aynı kapsamda · 1 en az bir düğüm başka kapsama kaydı
"""
import argparse
import ast
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
KOK = Path(__file__).resolve().parents[4]
DUGUM = re.compile(r'^\s*(?:subgraph\s+)?([A-Za-z][A-Za-z0-9_]*)\s*(?:\["|\{")'
                   r'.*<br/>([A-Za-z0-9_./-]+\.py):(\d+)"(?:\]|\})\s*$')


def dugumler(metin):
    sonuc = {}
    for s in metin.replace("\r\n", "\n").split("\n"):
        m = DUGUM.match(s)
        if m:
            sonuc[m.group(1)] = (m.group(2), int(m.group(3)))
    return sonuc


def kapsamlar(kaynak):
    """[(bas, son, qualname)] — dekoratör satırları dahil."""
    agac = ast.parse(kaynak)
    cikti = []

    def gez(dugum, yigin):
        for alt in ast.iter_child_nodes(dugum):
            if isinstance(alt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                bas = min([alt.lineno] + [d.lineno for d in alt.decorator_list])
                ad = ".".join(yigin + [alt.name])
                cikti.append((bas, alt.end_lineno, ad))
                gez(alt, yigin + [alt.name])
            else:
                gez(alt, yigin)

    gez(agac, [])
    return cikti


def kapsam(tablo, satir):
    icerenler = [(son - bas, ad) for bas, son, ad in tablo if bas <= satir <= son]
    return min(icerenler)[1] if icerenler else "<modul>"


def git_goster(rev, yol):
    return subprocess.run(["git", "-C", str(KOK), "show", f"{rev}:{yol}"],
                          capture_output=True, check=True).stdout.decode("utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--taban", default="HEAD")
    ap.add_argument("--mmd", default="FDR/sekiller/akis_d.mmd")
    a = ap.parse_args()
    eski = dugumler(git_goster(a.taban, a.mmd))
    yeni = dugumler((KOK / a.mmd).read_text(encoding="utf-8"))
    kaynak_eski, kaynak_yeni = {}, {}
    degisen = hata = 0
    for kimlik, (dosya, satir) in sorted(yeni.items()):
        if kimlik not in eski:
            print(f"  YENI DUGUM {kimlik}: {dosya}:{satir}")
            continue
        e_dosya, e_satir = eski[kimlik]
        if (e_dosya, e_satir) == (dosya, satir):
            continue
        degisen += 1
        if e_dosya not in kaynak_eski:
            kaynak_eski[e_dosya] = kapsamlar(git_goster(a.taban, e_dosya))
        if dosya not in kaynak_yeni:
            kaynak_yeni[dosya] = kapsamlar((KOK / dosya).read_text(encoding="utf-8"))
        k_eski = kapsam(kaynak_eski[e_dosya], e_satir)
        k_yeni = kapsam(kaynak_yeni[dosya], satir)
        durum = "AYNI" if (e_dosya == dosya and k_eski == k_yeni) else "HATA"
        hata += durum == "HATA"
        print(f"  {durum} {kimlik}: {e_dosya}:{e_satir} [{k_eski}] -> "
              f"{dosya}:{satir} [{k_yeni}]")
    print(f"{a.mmd}: taban {a.taban} · {len(yeni)} dugum · satiri degisen {degisen} · "
          f"kapsam HATASI {hata}")
    return 1 if hata else 0


if __name__ == "__main__":
    raise SystemExit(main())
