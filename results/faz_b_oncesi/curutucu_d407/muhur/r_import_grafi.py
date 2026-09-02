"""YKS/IKA istasyonunun (ve saha_baslat'in) calistirdigi depo-ici modullerin kunye kapsamina
gore durumu. Statik: ast ile import agaci; sys.path ekleme aliskanligi (codes/ comms/ scripts/
simulation/scripts) taklit edilir. Salt okunur."""
import ast
import sys
from pathlib import Path

KOK = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(KOK / "scripts")); sys.path.insert(0, str(KOK / "codes"))
import surum_dondur as sd  # noqa: E402

ARAMA = [KOK / "codes", KOK / "comms", KOK / "scripts", KOK / "simulation" / "scripts", KOK]
KAPSAM = set(sd.YKS_IKA) | set(sd.SAHA_YAPILANDIRMA) | {k for k, _ in sd.PAKET_ESLEMESI}


def coz(ad):
    parcalar = ad.split(".")
    for d in ARAMA:
        for i in range(len(parcalar), 0, -1):
            p = d.joinpath(*parcalar[:i]).with_suffix(".py")
            if p.is_file():
                return p
            p = d.joinpath(*parcalar[:i]) / "__init__.py"
            if p.is_file():
                return p
    return None


def importlar(yol):
    try:
        agac = ast.parse(yol.read_bytes(), filename=str(yol))
    except SyntaxError as exc:
        print(f"  ! parse: {yol}: {exc}")
        return []
    adlar = []
    for n in ast.walk(agac):
        if isinstance(n, ast.Import):
            adlar += [a.name for a in n.names]
        elif isinstance(n, ast.ImportFrom) and n.module and n.level == 0:
            adlar.append(n.module)
            adlar += [f"{n.module}.{a.name}" for a in n.names]
    return adlar


baslangic = [KOK / y for y in sd.YKS_IKA]
gorulen, kuyruk = {}, list(baslangic)
while kuyruk:
    y = kuyruk.pop()
    g = y.relative_to(KOK).as_posix()
    if g in gorulen:
        continue
    gorulen[g] = set()
    for ad in importlar(y):
        h = coz(ad)
        if h is None:
            continue
        try:
            hg = h.relative_to(KOK).as_posix()
        except ValueError:
            continue
        gorulen[g].add(hg)
        if hg not in gorulen:
            kuyruk.append(h)

disi = sorted(g for g in gorulen if g not in KAPSAM)
ici = sorted(g for g in gorulen if g in KAPSAM)
print(f"baslangic (YKS_IKA): {len(sd.YKS_IKA)}  ulasilan depo modulu: {len(gorulen)}")
print(f"KAPSAM ICI ({len(ici)}):")
for g in ici:
    print("   ", g)
print(f"KAPSAM DISI ({len(disi)}):")
for g in disi:
    kimden = sorted(k for k, v in gorulen.items() if g in v)
    print(f"    {g}    <- {', '.join(kimden)}")
