"""T226-D — akış d ALT-GRAFİK (`subgraph sDx["def Sinif.ad()<br/>dosya:SATIR"]`)
başlıklarının satırını AST ile tazeler.

NEDEN: `scripts/akis_satir_tazele.py` düğüm regex'i `subgraph ` önekli satırları
YAKALAMAZ (ölçüldü: T226-D'de 5 alt-grafik başlığı bayat kaldı, doğrulayıcı
"def ... YOK" dedi). Metin araması yerine qualname ile tanım satırı bulunur —
başka fonksiyondaki aynı metne kayma OLAMAZ. Satır sonları (CRLF/LF) taban
commit'teki biçimde yazılır.

KOSUM (depo kökünden):
  O:/navitas-local-train/venv/Scripts/python.exe -B \
      results/fdr_sprint_20260910/H9_MK15/t226/akis_altgrafik_tazele_t226d.py
"""
import ast
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
KOK = Path(__file__).resolve().parents[4]
MMD = "FDR/sekiller/akis_d.mmd"
ALT = re.compile(r'^(\s*subgraph\s+[A-Za-z][A-Za-z0-9_]*\["def )'
                 r'([A-Za-z_][A-Za-z0-9_.]*)(\(\)<br/>)([A-Za-z0-9_./-]+\.py):(\d+)("\]\s*)$')


def tanimlar(kaynak):
    agac = ast.parse(kaynak)
    cikti = {}

    def gez(dugum, yigin):
        for alt in ast.iter_child_nodes(dugum):
            if isinstance(alt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                ad = ".".join(yigin + [alt.name])
                cikti.setdefault(ad, []).append(alt.lineno)
                gez(alt, yigin + [alt.name])

    gez(agac, [])
    return cikti


def main():
    taban = subprocess.run(["git", "-C", str(KOK), "show", f"HEAD:{MMD}"],
                           capture_output=True, check=True).stdout
    crlf = b"\r\n" in taban
    yol = KOK / MMD
    satirlar = yol.read_bytes().decode("utf-8").replace("\r\n", "\n").split("\n")
    onbellek = {}
    degisen = 0
    for i, s in enumerate(satirlar):
        m = ALT.match(s)
        if not m:
            continue
        on, qual, orta, dosya, sat, son = m.groups()
        if dosya not in onbellek:
            onbellek[dosya] = tanimlar((KOK / dosya).read_text(encoding="utf-8"))
        adaylar = onbellek[dosya].get(qual, [])
        if len(adaylar) != 1:
            raise SystemExit(f"{qual}: {len(adaylar)} tanim ({dosya}) — elle bak")
        yeni = adaylar[0]
        if yeni != int(sat):
            satirlar[i] = f"{on}{qual}{orta}{dosya}:{yeni}{son}"
            degisen += 1
        print(f"  {qual}: {dosya}:{sat} -> {yeni}")
    metin = "\n".join(satirlar)
    yol.write_bytes((metin.replace("\n", "\r\n") if crlf else metin).encode("utf-8"))
    print(f"{MMD}: alt-grafik basligi tazelendi {degisen}; satir sonu "
          f"{'CRLF' if crlf else 'LF'} (taban HEAD ile ayni)")


if __name__ == "__main__":
    main()
