"""D-466 duzeltmesinden ONCEKI ve SONRAKI tam suit ciktilarini KARSILASTIRIR.

NEDEN AYRI BETIK: karsilastirmayi suitin ICINDE yapan bir test, okudugu dosyayi
URETEN kosumun icinde kosar — kabuk yonlendirmesi dosyayi basta bosalttigi icin
test yarim dosya gorur ve kendi kosumunda duser (12 Eylul'de olculdu:
tam_suit_4.txt ve tam_suit_5.txt). Bu yuzden olcum suitin DISINA alindi;
nobetci yalnizca bu betigin DONMUS ciktisindaki hukmu kilitler
(`taban_kiyas.py` kalibi).

OLCUT (dar ve kesin): bu isin DOKUNDUGU modul (`test_t243_paket_boyutu`) tam
suit icinde HIC dusuk uretmemeli. Tam kume esitligi olcut DEGILDIR: suit ici
kararsizlik olculdu (kapi/kararsiz_faz_b_iha_komut_alici.txt), kararsiz bir
buyukluk kilit olamaz. Kume farki yine de SAYILARAK basilir.

Kosum:
    venv\\Scripts\\python.exe -X utf8 -B \\
        results/fdr_sprint_20260910/T243/kapi/suit_kiyas.py \\
        --once tam_suit_2.txt --sonra tam_suit_6.txt
"""
import argparse
import re
import sys
from pathlib import Path

KAPI = Path(__file__).resolve().parent
#: Bu isin dokundugu nobetci modulu — dar olcut bunun uzerinedir.
MODUL = "test_t243_paket_boyutu"


def oku(ad):
    yol = KAPI / ad
    if not yol.is_file():
        print(f"OLCULEMEDI: dosya yok — {yol}", file=sys.stderr)
        return None
    metin = yol.read_text(encoding="utf-8", errors="replace")
    if not re.search(r"^Ran \d+ tests? in ", metin, re.M) or \
            not re.search(r"^(OK|FAILED)\b", metin, re.M):
        print(f"OLCULEMEDI: {ad} yarim (kosum tamamlanmamis)", file=sys.stderr)
        return None
    return metin


def dusukler(metin):
    return sorted(x.strip() for x in metin.splitlines()
                  if x.startswith(("FAIL:", "ERROR:")))


def ozet(metin):
    r = re.search(r"^Ran \d+ tests? in .*$", metin, re.M)
    o = re.search(r"^(OK|FAILED).*$", metin, re.M)
    return f"{r.group(0) if r else '?'} · {o.group(0) if o else '?'}"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--once", default="tam_suit_2.txt")
    ap.add_argument("--sonra", default="tam_suit_6.txt")
    a = ap.parse_args(argv)

    m1, m2 = oku(a.once), oku(a.sonra)
    if m1 is None or m2 is None:
        print("SONUC: OLCULEMEDI")
        return 2
    d1, d2 = dusukler(m1), dusukler(m2)
    print(f"ONCE  ({a.once}) : {ozet(m1)} · {len(d1)} dusuk")
    print(f"SONRA ({a.sonra}): {ozet(m2)} · {len(d2)} dusuk")

    yeni = [x for x in d2 if x not in d1]
    giden = [x for x in d1 if x not in d2]
    print(f"SONRAKI kosumda YENI dusuk: {len(yeni)}")
    for x in yeni:
        print(f"  + {x}")
    print(f"SONRAKI kosumda GECEN (onceki dusuk): {len(giden)}")
    for x in giden:
        print(f"  - {x}")

    t243 = [x for x in d2 if MODUL in x]
    print(f"{MODUL} kaynakli dusuk: {len(t243)}")
    for x in t243:
        print(f"  ! {x}")
    if t243:
        print(f"SONUC: {MODUL} modulunden DUSUK VAR")
        return 1
    print("SONUC: T243 modulunden dusuk YOK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
