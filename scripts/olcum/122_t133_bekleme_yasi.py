"""T133 — READY_FOR_REVIEW birikmesi: her gorev NE ZAMANDAN BERI bekliyor?

NEDEN: "39 gorev denetim bekliyor" bir SAYIDIR; sureci anlatan sey YAS
DAGILIMIDIR. Duzenli bir sizinti mi (her turda 1-2 birikiyor) yoksa bir
PATLAMA mi (tek gunde 15 gorev isaretlendi)? Care ikisinde FARKLIDIR:
sizinti -> denetim hizi yetersiz · patlama -> o turda bir yordam kirildi.

🔴 ISARET TARIH TASIMIYOR. `[STATUS: READY_FOR_REVIEW]` ne SAHIP ne TARIH
tasir (`[IN_PROGRESS: <ad>]` en azindan sahip tasiyor). Bu yuzden yas
kuyruktan OKUNAMAZ ve GIT GECMISINDEN cikarilmak zorundadir — kusurun
kendisi de budur: bekleme suresi hicbir yerde GORUNMUYOR.

YONTEM: TASK_QUEUE.md'nin her commit'i taranir; her commit'te
READY_FOR_REVIEW durumundaki gorev kimlikleri cikarilir; her gorev icin
ILK gorunum tarihi = beklemeye baslama tarihi.

CIKTI: results/t133/bekleme_yasi.json + stdout ozeti
🔴 HUKUM VERMEZ. Yalnizca olcer.
"""
from __future__ import annotations

import io
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

KOK = Path(__file__).resolve().parents[2]
DOSYA = "TASK_QUEUE.md"
CIKTI = KOK / "results" / "t133"
BUGUN = date(2026, 8, 21)   # ⚠ SABIT: betik yarin kosunca sayilar KAYMASIN

SATIR = re.compile(r"^- \[STATUS: READY_FOR_REVIEW\].*?\*\*((?:T|S)\d+[a-z]?)\b")


def kos(*arg: str) -> str:
    p = subprocess.run(arg, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", cwd=str(KOK))
    return p.stdout


def durumdakiler(icerik: str) -> set[str]:
    return {m.group(1) for m in (SATIR.match(s) for s in icerik.splitlines()) if m}


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError, OSError):
        pass

    ham = kos("git", "log", "--follow", "--format=%H|%ad", "--date=short",
              "--reverse", "--", DOSYA).splitlines()
    ilk_gorunum, son_gorunum, tarihce = {}, {}, []
    for kayit in ham:
        if "|" not in kayit:
            continue
        sha, tarih = kayit.split("|", 1)
        icerik = kos("git", "show", f"{sha}:{DOSYA}")
        if not icerik.strip():
            continue
        kume = durumdakiler(icerik)
        tarihce.append({"commit": sha[:8], "tarih": tarih, "adet": len(kume)})
        for g in kume:
            ilk_gorunum.setdefault(g, {"tarih": tarih, "commit": sha[:8]})
            son_gorunum[g] = tarih

    bugunku = durumdakiler((KOK / DOSYA).read_text(encoding="utf-8"))
    satirlar = []
    for g in sorted(bugunku):
        ilk = ilk_gorunum.get(g)
        if ilk is None:
            satirlar.append({"gorev": g, "ilk_tarih": None, "gun": None,
                             "not": "git gecmisinde bulunamadi"})
            continue
        y, m, d = (int(x) for x in ilk["tarih"].split("-"))
        satirlar.append({"gorev": g, "ilk_tarih": ilk["tarih"],
                         "commit": ilk["commit"],
                         "gun": (BUGUN - date(y, m, d)).days})

    satirlar.sort(key=lambda s: (-(s["gun"] or -1), s["gorev"]))
    CIKTI.mkdir(parents=True, exist_ok=True)
    io.open(CIKTI / "bekleme_yasi.json", "w", encoding="utf-8").write(
        json.dumps({"_ne": "T133 · READY_FOR_REVIEW bekleme yasi (git gecmisinden)",
                    "_bugun": BUGUN.isoformat(), "_uyari":
                    "Isaret TARIH TASIMIYOR; yas ancak git'ten cikarilabiliyor.",
                    "bugun_bekleyen": len(bugunku), "gorevler": satirlar,
                    "gunluk_adet": tarihce}, ensure_ascii=False, indent=1))

    print(f"bugun READY_FOR_REVIEW: {len(bugunku)}")
    yaslar = [s["gun"] for s in satirlar if s["gun"] is not None]
    if yaslar:
        print(f"yas (gun): en eski {max(yaslar)} · en yeni {min(yaslar)} · "
              f"ortanca {sorted(yaslar)[len(yaslar)//2]}")
    print("\nEN ESKI 8:")
    for s in satirlar[:8]:
        print(f"  {s['gorev']:6s} {s['ilk_tarih']}  {s['gun']:>3} gun")
    print("\nADET ZAMAN ICINDE (isaretin gunluk toplami):")
    onceki = None
    for t in tarihce:
        if onceki is None or t["adet"] != onceki:
            ok = "" if onceki is None else f"  ({t['adet']-onceki:+d})"
            print(f"  {t['tarih']} {t['commit']}  {t['adet']:>3}{ok}")
            onceki = t["adet"]
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
