"""T153 dedektorun TEK BASINA (model yok, CPU) uzlasi referansiyla kesisimi — 111 kare.
Dedektor pikselleri GT'de nereye dusuyor: sinif1 (engel, DOGRU) / sinif0 (yol, YANLIS: mesru zemin
cikarildi) / etiketsiz. Cikti results/t153/dedektor_gt.json + stdout.
"""
import io
import json
import sys
from pathlib import Path

import cv2
import numpy as np

WT = Path(r"O:\navitas\.claude\worktrees\wf_2d1c9d5e-54f-1")
sys.path.insert(0, str(WT / "codes"))
from rpi_inference import _preprocess  # noqa: E402
from karar_sozlesmesi import ince_beton_serit_maskesi  # noqa: E402

ANA = Path(r"O:\navitas")
V3 = ANA / "dataset" / "dji_kirsal_0038_bolum_v3" / "images"
UZ = ANA / "results" / "gece_20260826" / "t152_uzlasi"
W, H = 960, 540


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    satirlar = []
    for b in ("test", "val"):
        for p in sorted((V3 / b).glob("*.jpg")):
            img = cv2.imread(str(p))
            sq, small, (x0, y0, cw, ch) = _preprocess(img)
            h, w = sq.shape[:2]
            m = ince_beton_serit_maskesi(small)
            m = cv2.resize(m, (w, h), interpolation=cv2.INTER_NEAREST)
            m = cv2.resize(m[y0:y0 + ch, x0:x0 + cw], (W, H), interpolation=cv2.INTER_NEAREST) > 0
            u = np.squeeze(cv2.imread(str(UZ / f"{p.stem}_uc.png"), cv2.IMREAD_GRAYSCALE))
            n = int(m.sum())
            satirlar.append({"kare": p.name, "bolum": "test29" if b == "test" else "val82", "px": n,
                             "gt1": int((m & (u == 2)).sum()), "gt0": int((m & (u == 1)).sum()),
                             "etiketsiz": int((m & (u == 0)).sum()),
                             "gt1_toplam": int((u == 2).sum()), "gt0_toplam": int((u == 1).sum())})
    ates = [s for s in satirlar if s["px"] > 0]
    top = {k: sum(s[k] for s in satirlar) for k in ("px", "gt1", "gt0", "etiketsiz")}
    ozet = {"n": len(satirlar), "ateslenen_kare": len(ates),
            "px_toplam": top["px"],
            "pay_gt1": round(top["gt1"] / top["px"], 4) if top["px"] else None,
            "pay_gt0": round(top["gt0"] / top["px"], 4) if top["px"] else None,
            "pay_etiketsiz": round(top["etiketsiz"] / top["px"], 4) if top["px"] else None,
            "gt0_uzerine_yazan_kare": sum(1 for s in satirlar if s["gt0"] > 0),
            "gt0_>100px_kare": [s["kare"] for s in satirlar if s["gt0"] > 100]}
    json.dump({"ozet": ozet, "kareler": satirlar}, io.open(WT / "results" / "t153" / "dedektor_gt.json", "w", encoding="utf-8"), indent=1)
    print(json.dumps(ozet, ensure_ascii=False, indent=1))
    print("en cok px:", [(s["kare"][-20:-4], s["px"], s["gt1"], s["gt0"]) for s in sorted(satirlar, key=lambda s: -s["px"])[:10]])


if __name__ == "__main__":
    main()
