"""T133 — READY_FOR_REVIEW envanteri MEKANIK cikarilir (elle liste TUTULMAZ).

NEDEN: 39 gorev mimarin denetimini bekliyor ve isaret haftalardir bayat.
Triyajin ILK adimi listenin kendisidir; elle yazilmis bir liste bu projede
DORT kez bayatladi, ve bu gorev tam olarak "bayat isaret" sorunudur — listeyi
elle tutmak kusuru kendi cozumunde tekrar etmek olurdu.

CIKTI: results/t133/envanter.json (gorev · satir · baslik · dosyalar · atiflar)
🔴 BU BETIK HUKUM VERMEZ, KOVA ATAMAZ. Yalnizca ne oldugunu cikarir.
"""
from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[2]
KUYRUK = KOK / "TASK_QUEUE.md"
CIKTI = KOK / "results" / "t133"

BASLIK = re.compile(r"^- \[STATUS: READY_FOR_REVIEW\]\s*(.*)$")
HERHANGI_MADDE = re.compile(r"^- \[")
GOREV_ID = re.compile(r"\*\*((?:T|S)\d+[a-z]?)\b")
DOSYA = re.compile(r"`([^`]*(?:\.py|\.md|\.json|\.yaml|/)[^`]*)`")
ATIF = re.compile(r"\bD-(\d+)\b")


def main() -> int:
    # T132'de olculen kusur burada da isirdi: betik olarak kosup cikti
    # yakalandiginda stdout cp1254 olur ve baslikta gecen '→' PATLATIR.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError, OSError):
        pass
    satirlar = io.open(KUYRUK, encoding="utf-8").read().splitlines()
    kayitlar, su = [], None
    for i, s in enumerate(satirlar, 1):
        m = BASLIK.match(s)
        if m:
            if su:
                kayitlar.append(su)
            su = {"satir": i, "baslik_ham": m.group(1), "govde": []}
            continue
        if su is not None and HERHANGI_MADDE.match(s):
            kayitlar.append(su)
            su = None
            continue
        if su is not None:
            su["govde"].append(s)
    if su:
        kayitlar.append(su)

    for k in kayitlar:
        tam = k["baslik_ham"] + "\n" + "\n".join(k["govde"])
        gid = GOREV_ID.search(k["baslik_ham"])
        k["gorev"] = gid.group(1) if gid else "?"
        # Baslik: ilk ** ... ** blogu, kisaltilmis
        b = re.sub(r"\*\*", "", k["baslik_ham"])
        k["baslik"] = b.split(" · ")[0].strip()[:150]
        k["dosyalar"] = sorted({d for d in DOSYA.findall(tam)})
        k["atiflar"] = sorted({int(a) for a in ATIF.findall(tam)})
        k["govde_satir"] = len(k["govde"])
        del k["govde"]

    CIKTI.mkdir(parents=True, exist_ok=True)
    io.open(CIKTI / "envanter.json", "w", encoding="utf-8").write(
        json.dumps({"_ne": "T133 · READY_FOR_REVIEW envanteri (MEKANIK)",
                    "_kaynak": "TASK_QUEUE.md",
                    "n": len(kayitlar), "kayitlar": kayitlar},
                   ensure_ascii=False, indent=1))
    print(f"READY_FOR_REVIEW: {len(kayitlar)}")
    for k in kayitlar:
        print(f"  {k['gorev']:6s} s{k['satir']:<5d} dosya {len(k['dosyalar'])} "
              f"· atif {len(k['atiflar'])} · {k['baslik'][:78]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
