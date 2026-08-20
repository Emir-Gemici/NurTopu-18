"""T122 SECENEK KOSUMLARI — (a) ve (a)+(c) icin fine-tune baslatici.

ON KAYIT: results/t122_on_kayit.md (D-107). RECETE 101_t121_ft_kosumu ile
BIREBIR AYNI (56 zinciri RECETE'si + epochs=40, patience=15, taban v34);
degisen TEK sey `data` yaml'idir. Boylece uc kosum (t121_ft, A, B) ayni
receteyle kiyaslanabilir.
"""
from __future__ import annotations

import argparse
import importlib
import os
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(KOK / "scripts" / "olcum"))
m56 = importlib.import_module("56_t53_gercek_karisim")

TABAN = KOK / "models" / "navitas_seg_v34_best.pt"
RUNS = KOK / "codes" / "runs" / "segment"
ADLAR = {"a": "t122a_daralt", "ac": "t122ac_daralt_cati"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kip", choices=("a", "ac"), required=True)
    # T128 (D-135): tohum gurultusunu OLCMEK icin; recete DEGISMEZ.
    ap.add_argument("--tohum", type=int, default=None,
                    help="RECETE tohumunu ez (varsayilan: recetedeki 0)")
    # T128-B (D-251): tohum kolu ETKISIZ cikti; gercek kosum-ici degiskenligi
    # olcmek icin belirlenimcilik kapatilir. OLCUM kosumu — uretim recetesi
    # DEGISMEZ.
    ap.add_argument("--belirsiz", action="store_true",
                    help="deterministic=False ile kos (T128-B olcumu)")
    args = ap.parse_args()
    ad = ADLAR[args.kip]
    if args.belirsiz:
        ad = f"t122{args.kip}_belirsiz"
    elif args.tohum is not None:
        ad = f"t122{args.kip}_tohum{args.tohum}"
    data = KOK / "dataset" / f"karisim_t122{args.kip}.yaml"
    if not data.is_file():
        raise SystemExit(f"karisim yok: {data}")
    if os.environ.get("FOR_DISABLE_CONSOLE_CTRL_HANDLER") != "1":
        print("!! FOR_DISABLE_CONSOLE_CTRL_HANDLER=1 degil", flush=True)

    kw = dict(m56.RECETE)
    kw.update(epochs=40, patience=15)
    if args.tohum is not None:
        kw["seed"] = args.tohum
    if args.belirsiz:
        kw["deterministic"] = False
    from ultralytics import YOLO
    print(f"[{ad}] taban={TABAN.name} data={data.name} epochs={kw['epochs']} "
          f"imgsz={kw['imgsz']} batch={kw['batch']}", flush=True)
    YOLO(str(TABAN)).train(data=str(data), project=str(RUNS), name=ad,
                           exist_ok=True, resume=False, **kw)
    print(f"[{ad}] EGITIM TAMAMLANDI -> {RUNS / ad / 'weights' / 'best.pt'}",
          flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
