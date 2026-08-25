"""T144 (4): HF asolodin/rescuenet-roads yerel onbellegindeki etiket degerleri
T54 eslemesini (TRAVERSABLE_HAM={7}, BLOCKED_HAM=9 id) tetikliyor mu? Salt okuma."""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from dataset import download_and_convert as D  # noqa: E402
from datasets import load_dataset  # noqa: E402

ds = load_dataset("asolodin/rescuenet-roads")
out = {"TRAVERSABLE_HAM": sorted(D.TRAVERSABLE_HAM), "BLOCKED_HAM": sorted(D.BLOCKED_HAM)}
for split in ("train", "validation", "test"):
    d = ds[split]
    n = min(200, len(d))
    say = {}
    shape = None
    for i in range(0, len(d), max(1, len(d) // n)):
        lbl = np.array(d[i]["label"])
        shape = lbl.shape
        u, c = np.unique(lbl, return_counts=True)
        for a, b in zip(u.tolist(), c.tolist()):
            say[a] = say.get(a, 0) + b
    out[split] = {"n_toplam": len(d), "n_ornek": n, "shape": shape, "deger_px": say}
    print(split, len(d), shape, say, flush=True)
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "hf_girdi_kontrol.json"), "w") as fh:
    json.dump(out, fh, indent=1)
