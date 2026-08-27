"""T166 (REVIEW_LOG D-310 SS5): kabul kumesinin `acik_serit` alani, kumenin
KENDI etiket maskesiyle turetilen seritle uyusuyor mu? — 260 karenin TAMAMI.

Yontem (D-302/D-310'da gecerliligi olculen TAVAN kolu): her karenin YOLO
etiketinden sinif 0/1 maskesi rasterlenir, URETIM zinciri (`analyze_path` +
`_rota_kararini_esikle`) o maskeyle kosulur ve yayinlanan `road`, manifestteki
`acik_serit` ile kiyaslanir. Model KULLANILMAZ — bu bir VERI KUMESI olcumudur.

Cikti: ayrisan karelerin LISTESI. `acik_serit`'i yer gercegi sayan her olcum
(K7 kapi onerisi dahil) ya bu listeyi DISLAMALI ya da maskeyi referans almalidir.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[2]
for _y in (KOK / "codes", KOK / "comms"):
    sys.path.insert(0, str(_y))

import cv2  # noqa: E402
import numpy as np  # noqa: E402
import rpi_inference as ri  # noqa: E402


def _etiket(lbl: Path, w: int, h: int):
    m0 = np.zeros((h, w), np.uint8)
    m1 = np.zeros((h, w), np.uint8)
    if not lbl.is_file():
        return m0, m1
    for satir in lbl.read_text(encoding="utf-8").splitlines():
        p = satir.split()
        if len(p) < 7:
            continue
        c = int(float(p[0]))
        k = np.array([float(x) for x in p[1:]], np.float32).reshape(-1, 2)
        k[:, 0] *= w
        k[:, 1] *= h
        cv2.fillPoly(m0 if c == 0 else m1, [k.astype(np.int32)], 255)
    return m0, m1


def main():
    defter = json.loads((KOK / "config" / "model_registry.json")
                        .read_text(encoding="utf-8"))
    kume = Path(defter["profiles"]["competition"]["kabul_kumesi"])
    mf = json.loads((kume / "manifest.json").read_text(encoding="utf-8"))
    arena = {Path(o["cikti"]).name: o["arena"] for o in mf["ornekler"]
             if isinstance(o.get("arena"), dict)}

    kareler = []
    for alt in ("val", "train"):
        kareler += [(p, kume / "labels" / alt / (p.stem + ".txt"))
                    for p in sorted((kume / "images" / alt).glob("*.jpg"))]
    kareler = [(g, l) for g, l in kareler if g.name in arena]
    print(f"kare {len(kareler)}", flush=True)

    satirlar = []
    for i, (gorsel, lbl) in enumerate(kareler, 1):
        a = arena[gorsel.name]
        img = cv2.imread(str(gorsel))
        sq, small, icerik = ri._preprocess(img)
        yan = sq.shape[0]
        x0, y0, w, h = icerik
        g0, g1 = _etiket(lbl, img.shape[1], img.shape[0])
        trav = np.zeros((yan, yan), np.uint8)
        blok = np.zeros((yan, yan), np.uint8)
        trav[y0:y0 + h, x0:x0 + w] = g0
        blok[y0:y0 + h, x0:x0 + w] = g1
        hy, gv, hw, red = ri.analyze_path(trav, icerik=icerik, engel_mask=blok,
                                          mpp=a.get("mpp"), return_reason=True)
        tavan, _g, _w, red = ri._rota_kararini_esikle(hy, gv, hw, red)
        beklenen = a.get("acik_serit")
        satirlar.append({
            "kare": gorsel.name, "acik_serit": beklenen, "tavan_serit": tavan,
            "ret": (red[0] if isinstance(red, (tuple, list)) else red),
            "uyusuyor": bool(tavan is not None and tavan == beklenen),
            "tavan_rota_yok": bool(tavan is None),
            "belirsiz": a.get("belirsiz"),
        })
        if i % 50 == 0:
            print(f"  {i}/{len(kareler)}", flush=True)

    n = len(satirlar)
    rota_var = [s for s in satirlar if not s["tavan_rota_yok"]]
    uyusan = [s for s in rota_var if s["uyusuyor"]]
    ayrisan = [s for s in rota_var if not s["uyusuyor"]]
    ozet = {
        "n": n, "tavan_rota_uretti": len(rota_var),
        "uyusan": len(uyusan), "ayrisan": len(ayrisan),
        "tavan_rota_yok": n - len(rota_var),
        "ayrisan_pay": round(len(ayrisan) / len(rota_var), 4) if rota_var else None,
        "ayrisan_kareler": sorted(s["kare"] for s in ayrisan),
    }
    print(json.dumps({k: v for k, v in ozet.items() if k != "ayrisan_kareler"},
                     indent=1, ensure_ascii=False))
    print(f"AYRISAN {len(ayrisan)}/{len(rota_var)} "
          f"({ozet['ayrisan_pay']}) — ilk 15: {ozet['ayrisan_kareler'][:15]}")

    p = KOK / "results" / "t166" / "olcum.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"ozet": ozet, "kareler": satirlar}, indent=1,
                            ensure_ascii=False), encoding="utf-8")
    print("yazildi:", p)


if __name__ == "__main__":
    main()
