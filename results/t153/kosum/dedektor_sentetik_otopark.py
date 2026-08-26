"""T153 dedektor TEK BASINA (CPU): sentetik kabul kumesi (t66, 260 kare) + 67 gercek otopark karesi.
Kac karede ateslendi, kac px. Sifir ise K1-K6 'birebir' sonucunun NEDENI budur (dedektor sentetikte susuyor);
sifir degilse 65'in ACIK kosumunda engel maskesi degismis ama K'lar etkilenmemis demektir.
"""
import io
import json
import sys
from pathlib import Path

import cv2

WT = Path(r"O:\navitas\.claude\worktrees\wf_2d1c9d5e-54f-1")
sys.path.insert(0, str(WT / "codes"))
from rpi_inference import _preprocess  # noqa: E402
from karar_sozlesmesi import ince_beton_serit_maskesi  # noqa: E402

KUMELER = {
    "t66_sentetik": Path(r"O:\navitas-local-train\calisma\sentetik_arena_kadraj_t66"),
    "raw_frames_67": Path(r"O:\navitas\data\raw_frames"),
    "arena_figur": Path(r"O:\navitas\data\arena_referans"),
}


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sonuc = {}
    for ad, kok in KUMELER.items():
        kareler = sorted(list(kok.rglob("*.jpg")) + list(kok.rglob("*.png")))
        ates = []
        for p in kareler:
            img = cv2.imread(str(p))
            if img is None:
                continue
            _sq, small, _ic = _preprocess(img)
            m = ince_beton_serit_maskesi(small)
            n = int(m.sum()) if m is not None else 0
            if n:
                ates.append((p.name, n))
        sonuc[ad] = {"kare": len(kareler), "ateslenen": len(ates), "px_toplam": sum(n for _, n in ates),
                     "ateslenen_kareler": ates[:40]}
        print(ad, json.dumps({k: v for k, v in sonuc[ad].items() if k != "ateslenen_kareler"}), "ilk:", ates[:8])
    json.dump(sonuc, io.open(WT / "results" / "t153" / "dedektor_sentetik_otopark.json", "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
