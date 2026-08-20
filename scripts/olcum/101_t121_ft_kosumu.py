"""T121 BELIRLEYICI KOSUM baslaticisi — v34'ten yamali etiketlerle fine-tune.

ON KAYIT: results/t121_on_kayit.md (D-107; GPU kosumundan ONCE yazildi).
RECETE tek kaynaktan IMPORT edilir (56_t53_gercek_karisim.RECETE — v15_ft2sinif
args.yaml kokenli, imgsz=512/D-112 dahil); yalniz sunlar degisir ve nedenleri
on kayitta: epochs=40, patience=15 (tek gece), taban=v34 best (D-211 "ayni
recete ile fine-tune"), data=karisim_t121.yaml (yalniz ETIKET degisti).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(KOK / "scripts" / "olcum"))

import importlib

m56 = importlib.import_module("56_t53_gercek_karisim")

AD = "t121_etiket_ft"
DATA = KOK / "dataset" / "karisim_t121.yaml"
TABAN = KOK / "models" / "navitas_seg_v34_best.pt"
RUNS = KOK / "codes" / "runs" / "segment"


def main() -> int:
    if os.environ.get("FOR_DISABLE_CONSOLE_CTRL_HANDLER") != "1":
        print("!! FOR_DISABLE_CONSOLE_CTRL_HANDLER=1 degil", flush=True)
    if not DATA.is_file():
        raise SystemExit(f"karisim yok: {DATA}")
    if not TABAN.is_file():
        raise SystemExit(f"taban agirlik yok: {TABAN}")

    kw = dict(m56.RECETE)
    kw.update(epochs=40, patience=15)
    from ultralytics import YOLO
    print(f"[{AD}] taban={TABAN.name} data={DATA.name} "
          f"epochs={kw['epochs']} imgsz={kw['imgsz']} batch={kw['batch']}",
          flush=True)
    model = YOLO(str(TABAN))
    model.train(data=str(DATA), project=str(RUNS), name=AD,
                exist_ok=True, resume=False, **kw)
    print(f"[{AD}] EGITIM TAMAMLANDI -> {RUNS / AD / 'weights' / 'best.pt'}",
          flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
