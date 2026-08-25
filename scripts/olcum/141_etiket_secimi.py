"""141 — ETIKET DALGA 2 KARE SECIMI: etiketsiz havuzdan, MEVCUT etiketlilere gore
en-uzak-nokta ornekleme (8x8 gri ozellik; F5'in yontemi). Nadir disi (rel_alt<20)
ve zaten maskesi olan kareler haric.

  python 141_etiket_secimi.py --n 40 --grup 8 --cikti results/gece_20260826/etiket_dalga2_atama.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np

KOK = Path(__file__).resolve().parents[2]
KARE_KOK = KOK / "results" / "dji_20260822" / "kareler_1fps"
IRTIFA = KOK / "results" / "dji_20260822" / "kareler_irtifa.json"
MASKE_KOKLERI = [KOK / "results" / "dji_20260822" / "f5_olcek", KOK / "results" / "dji_20260822" / "f4",
                 KOK / "results" / "dji_20260822" / "f5", KOK / "results" / "dji_20260822" / "referans",
                 KOK / "results" / "dji_kirsal" / "bant_tamamlama", KOK / "results" / "dji_20260822" / "su_bindirme"]


def ozellik(p: Path) -> np.ndarray:
    im = cv2.imread(str(p), cv2.IMREAD_GRAYSCALE)
    im = cv2.resize(im, (8, 8), interpolation=cv2.INTER_AREA).astype(np.float32).ravel()
    return (im - im.mean()) / (im.std() + 1e-6)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--grup", type=int, default=8)
    ap.add_argument("--cikti", type=Path, required=True)
    a = ap.parse_args()

    etiketli = set()
    for mk in MASKE_KOKLERI:
        for p in mk.rglob("*_uc.png"):
            etiketli.add(p.name[:-len("_uc.png")])
        for p in mk.rglob("*_sinif1.png"):
            etiketli.add(p.name[:-len("_sinif1.png")])
    irt = json.loads(IRTIFA.read_text(encoding="utf-8"))
    # kareler_irtifa: liste ya da sozluk olabilir -> {dosya: rel_alt}
    rel = {}
    if isinstance(irt, dict):
        for k, v in irt.items():
            if isinstance(v, dict) and "rel_alt" in v:
                rel[k] = v["rel_alt"]
            elif isinstance(v, list):
                for e in v:
                    if isinstance(e, dict) and "dosya" in e:
                        rel[e["dosya"]] = e.get("rel_alt")
    else:
        for e in irt:
            rel[e["dosya"]] = e.get("rel_alt")

    havuz, ref = [], []
    for kaynak in sorted(KARE_KOK.iterdir()):
        for p in sorted(kaynak.glob("*.jpg")):
            govde = f"{kaynak.name}__{p.stem}"
            anahtar = f"{kaynak.name}/{p.name}"
            ra = rel.get(anahtar)
            if govde in etiketli:
                ref.append(p)
            elif ra is not None and ra < 20:
                continue
            else:
                havuz.append((p, ra))
    print(f"etiketli {len(ref)} · havuz {len(havuz)} (nadir disi haric)")
    F_ref = np.stack([ozellik(p) for p in ref]) if ref else np.zeros((0, 64), np.float32)
    F_hav = np.stack([ozellik(p) for p, _ in havuz])
    # en-uzak-nokta: mevcut etiketlilere + secilenlere olan en kucuk uzakligi enbuyukle
    if len(F_ref):
        d = np.min(np.linalg.norm(F_hav[:, None, :] - F_ref[None, :, :], axis=2), axis=1)
    else:
        d = np.full(len(havuz), np.inf)
    secilen = []
    for _ in range(min(a.n, len(havuz))):
        i = int(np.argmax(d))
        secilen.append(i)
        d = np.minimum(d, np.linalg.norm(F_hav - F_hav[i], axis=1))
        d[i] = -1
    kareler = [{"dosya": f"{havuz[i][0].parent.name}/{havuz[i][0].name}", "rel_alt": havuz[i][1]} for i in secilen]
    gruplar = {chr(65 + g): kareler[g::a.grup] for g in range(a.grup)}
    cikti = {"_ne": f"ETIKET DALGA 2 — {len(kareler)} kare, {a.grup} amele; en-uzak-nokta (8x8 gri), mevcut {len(ref)} etiketliye gore",
             "_sartname": "results/dji_20260822/SU_ETIKETLEME_PLANI.md §4b + EK-2 + EK-3 + EK-4",
             "_arac": "scripts/olcum/140_uc_maske_araci.py", "kaynak_kareler": "results/dji_20260822/kareler_1fps",
             "gruplar": gruplar}
    a.cikti.parent.mkdir(parents=True, exist_ok=True)
    a.cikti.write_text(json.dumps(cikti, indent=1, ensure_ascii=False), encoding="utf-8")
    kaynak_say = {}
    for k in kareler:
        kaynak_say[k["dosya"].split("/")[0][-6:]] = kaynak_say.get(k["dosya"].split("/")[0][-6:], 0) + 1
    print("secildi", len(kareler), kaynak_say, "->", a.cikti)


if __name__ == "__main__":
    main()
