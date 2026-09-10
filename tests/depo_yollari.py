"""T220 / K10 — testlerin DEPO KOKU ve (varsa) ANA DEPO adaylari: ciplak `O:/` YOK.

NEDEN (JETSON_OTURUM_DURUMU_20260909 SS5.3, results/jetson_20260906/K10_LISTE.md):
suitteki bazi testler worktree'de calisirken gitignore'lu varliklari (model
agirliklari, DJI kareleri, T66 manifesti) ANA DEPODAN okumak icin
`Path("O:/navitas/...")` yaziyordu. PC'de calisiyordu; Jetson'da (`~/navitas`,
Linux) ayni satirlar `FileNotFoundError` ile suiti kirmiziya boyuyordu ve
madde 16'ya (kodda ciplak sabit yok) aykiriydi.

Bu modul yolu TURETIR, yazmaz:
  1. `KOK`             : bu dosyadan yukari `tests/` -> depo koku.
  2. `ana_depo_adaylari()`: once KOK; sonra `NAVITAS_ANA_DEPO` ortam degiskeni
     (isaretci: `CLAUDE.md` + `codes/`); sonra git worktree kalibi
     `<ana>/.claude/worktrees/<ad>` ise `<ana>`. Hicbiri tutmazsa yalniz [KOK]
     doner — varlik yoksa test ATLAR (skip), sessizce gecmez.

Kullanim (testte):
    from depo_yollari import KOK, ana_depo_adaylari
    for kok in ana_depo_adaylari():
        aday = kok / "models" / ad

KESIF MUAFIYETI: test DEGIL, yardimci modul — `ana_depo_adaylari`/`ilk_var_olan` test_t143_turev_ve_kamera, test_t145_uygunluk, test_depo_koku_turetilir ve test_t220_jetson_istekleri tarafindan ice alinir; kendi basina kapi degildir (T120 kurali: `test_` onekli olmayan dosya test tasimaz).
KOSUM: O:\\navitas-local-train\\venv\\Scripts\\python.exe -m unittest discover -s tests -p "test_t220_jetson_istekleri.py"  (tests/depo_yollari.py bu kosumda K10CiplakYolYasagi tarafindan ice alinir; worktree kalibi ve NAVITAS_ANA_DEPO isaretcisi sentetik agacla sinanir)
"""
from __future__ import annotations

import os
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]


def _isaretci(d: Path) -> bool:
    return (d / "CLAUDE.md").is_file() and (d / "codes").is_dir()


def ana_depo_adaylari(kok: Path = KOK) -> list[Path]:
    """[kok, ...] — ana depo adaylari, tekrarsiz, sirayla (ciplak yol yok)."""
    kok = Path(kok).resolve()
    adaylar = [kok]
    ortam = os.environ.get("NAVITAS_ANA_DEPO")
    if ortam:
        aday = Path(ortam).expanduser()
        if _isaretci(aday):
            adaylar.append(aday.resolve())
    ebeveynler = kok.parents
    if (len(ebeveynler) >= 3 and ebeveynler[0].name == "worktrees"
            and ebeveynler[1].name == ".claude" and _isaretci(ebeveynler[2])):
        adaylar.append(ebeveynler[2].resolve())
    tekil: list[Path] = []
    for a in adaylar:
        if a not in tekil:
            tekil.append(a)
    return tekil


def ilk_var_olan(*goreli_parcalar: str, dosya: bool = True) -> Path | None:
    """Adaylarin altinda `goreli_parcalar` yolunu ILK bulundugu yerde dondur; yoksa None."""
    for kok in ana_depo_adaylari():
        aday = kok.joinpath(*goreli_parcalar)
        if (aday.is_file() if dosya else aday.is_dir()):
            return aday
    return None
