"""T139 ADIM 3 — GORUNURLUK DOZ-YANIT EGRISI. Esik KOYMAZ, ONERMEZ.

ON KAYIT: results/t139/on_kayit.md (bu betik KOSULMADAN ONCE yazildi, D-107).

BOSLUK (mimarin cercevesi):
    maske BOS       -> MASKE_YOK -> fail-closed        ZATEN CALISIYOR
    maske BOS DEGIL -> sistem ona KOSULSUZ GUVENIYOR   BOSLUK BURADA
Soru: BOS OLMAYAN ama GUVENILMEZ maske nerede basliyor?

DOZ  : L = LAB L kanali ortalamasi.
YANIT: Y1 BAND_ORANI = kaplama(conf 0,10)/kaplama(conf 0,30)  [BIRINCIL]
       Y2 modeller arasi zemin maskesi IoU (v35/v34/v30)      [IKINCIL]

🔴 Y1 YENIDEN KULLANIMDIR, ICAT DEGIL: olcut `93_t106_guven_bandi.py`de
tanimli ve D-184'te kullanildi (figur: v30 1,62 · v34 9,59). `kaplamalar()`
oradan ICE AKTARILIR, kopyalanmaz.

⚠ ONCEDEN ILAN EDILEN SINIR: L ~73 ile ~118 arasinda HIC KARE YOK
(alacakaranlik verisi yok). Egri orada BOSLUK tasir ve oraya cizgi CEKILMEZ.
"""
from __future__ import annotations

import argparse
import importlib.util
import io
import json
import statistics
import sys
import time
from pathlib import Path

KOK = Path(__file__).resolve().parents[2]
CIKTI = KOK / "results" / "t139"
GECE = KOK / "data" / "dji_prova_kareler"
GUNDUZ = KOK / "data" / "raw_frames"


def betik93():
    """93_t106_guven_bandi'ni ICE AKTAR (adi rakamla basliyor)."""
    sys.path.insert(0, str(KOK / "codes"))
    sys.path.insert(0, str(KOK / "scripts" / "olcum"))
    yol = KOK / "scripts" / "olcum" / "93_t106_guven_bandi.py"
    spec = importlib.util.spec_from_file_location("t106_band", yol)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError, OSError):
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--y2-ornek", type=int, default=150)
    ap.add_argument("--en-fazla", type=int, default=0)
    args = ap.parse_args()

    import cv2
    import numpy as np
    from ultralytics import YOLO
    B = betik93()

    kareler = ([("gece", p) for p in sorted(GECE.rglob("*.jpg"))] +
               [("gunduz", p) for p in sorted(GUNDUZ.rglob("*.jpg"))])
    if args.en_fazla:
        kareler = kareler[:args.en_fazla]
    print(f"kare: {len(kareler)} (gece {sum(1 for k,_ in kareler if k=='gece')} · "
          f"gunduz {sum(1 for k,_ in kareler if k=='gunduz')})")

    def L_of(p):
        im = cv2.imread(str(p))
        return float(cv2.cvtColor(im, cv2.COLOR_BGR2LAB)[:, :, 0].mean())

    # ── Y1 · BAND_ORANI, TUM kareler, v35 ─────────────────────────────────
    m35 = YOLO(str(KOK / "models" / "navitas_seg_v35_best.pt"), task="segment")
    t0 = time.perf_counter()
    satir = []
    for kume, p in kareler:
        L = L_of(p)
        k30 = B.kaplamalar(m35, p, 0.30)
        k10 = B.kaplamalar(m35, p, 0.10)
        if k30 is None or k10 is None:
            continue
        z30, e30 = k30
        z10, e10 = k10
        # BAND_ORANI: payda 0 ise TANIMSIZ (D-184 boyle sayiyor)
        band = (z10 / z30) if z30 > 0 else None
        satir.append({"kume": kume, "kare": p.name, "klip": p.parent.name[:38],
                      "L": round(L, 2), "zemin30": round(z30, 5),
                      "zemin10": round(z10, 5), "engel30": round(e30, 5),
                      "BAND_ORANI": (round(band, 3) if band is not None else None),
                      "bos_mu": z30 <= 0})
    print(f"Y1 bitti: {time.perf_counter()-t0:.0f} sn")

    # ── Y2 · modeller arasi IoU, L'ye gore ESIT ARALIKLI alt orneklem ─────
    sirali = sorted(satir, key=lambda s: s["L"])
    n = min(args.y2_ornek, len(sirali))
    idx = [round(i * (len(sirali) - 1) / max(n - 1, 1)) for i in range(n)]
    secilen = [sirali[i] for i in sorted(set(idx))]
    yol_of = {s["kare"] + "|" + s["klip"]: None for s in secilen}
    tum = {p.name + "|" + p.parent.name[:38]: p for _, p in kareler}
    modeller = {ad: YOLO(str(KOK / "models" / f"navitas_seg_{ad}_best.pt"),
                         task="segment")
                for ad in ("v35", "v34", "v30")}
    from rpi_inference import (_preprocess, _maskeleri_icerige_kirp,  # noqa: E402
                               get_masks, INFER_SIZE)

    def zemin_maske(model, p):
        im = cv2.imread(str(p))
        sq, small, icerik = _preprocess(im)
        h, w = sq.shape[:2]
        r = model.predict(small, imgsz=INFER_SIZE, conf=0.30, verbose=False)
        mk = _maskeleri_icerige_kirp(get_masks(r, h, w), icerik)
        return mk[0] > 0

    t0 = time.perf_counter()
    y2 = []
    for s in secilen:
        p = tum.get(s["kare"] + "|" + s["klip"])
        if p is None:
            continue
        m = {ad: zemin_maske(mo, p) for ad, mo in modeller.items()}
        ciftler = {}
        for a, b in (("v35", "v34"), ("v35", "v30"), ("v34", "v30")):
            bir = int(np.count_nonzero(m[a] | m[b]))
            kes = int(np.count_nonzero(m[a] & m[b]))
            ciftler[f"{a}_{b}"] = (kes / bir) if bir else None
        olculen = [v for v in ciftler.values() if v is not None]
        y2.append({"kume": s["kume"], "kare": s["kare"], "L": s["L"],
                   "ciftler": {k: (round(v, 4) if v is not None else None)
                               for k, v in ciftler.items()},
                   "IoU_ort": round(sum(olculen)/len(olculen), 4) if olculen else None,
                   "hepsi_bos": not olculen})
    print(f"Y2 bitti: {time.perf_counter()-t0:.0f} sn · {len(y2)} kare")

    # ── OZET: L kovalarina gore ────────────────────────────────────────────
    def kova(L):
        for ust in (10, 20, 30, 40, 60, 80, 120, 140):
            if L < ust:
                return f"<{ust}"
        return ">=140"

    print(f"\n{'L kovasi':10s} {'n':>4s} {'bos maske':>10s} {'BAND ORANI medyan':>19s} "
          f"{'zemin30 medyan':>15s}")
    ozet_kova = {}
    for k in ("<10", "<20", "<30", "<40", "<60", "<80", "<120", "<140", ">=140"):
        grup = [s for s in satir if kova(s["L"]) == k]
        if not grup:
            continue
        bandlar = [s["BAND_ORANI"] for s in grup if s["BAND_ORANI"] is not None]
        bos = sum(1 for s in grup if s["bos_mu"])
        med = statistics.median(bandlar) if bandlar else None
        zmed = statistics.median([s["zemin30"] for s in grup])
        ozet_kova[k] = {"n": len(grup), "bos_maske": bos,
                        "band_olculen": len(bandlar),
                        "band_medyan": med, "zemin30_medyan": zmed}
        print(f"{k:10s} {len(grup):4d} {bos:6d}/{len(grup):<4d} "
              f"{(f'{med:.3f}' if med is not None else 'TANIMSIZ'):>19s} "
              f"{zmed:15.5f}")

    print(f"\n{'L kovasi':10s} {'n':>4s} {'modeller arasi IoU medyan':>28s}")
    for k in ("<10", "<20", "<30", "<40", "<60", "<80", "<120", "<140", ">=140"):
        grup = [s for s in y2 if kova(s["L"]) == k and s["IoU_ort"] is not None]
        if not grup:
            continue
        med = statistics.median([s["IoU_ort"] for s in grup])
        ozet_kova.setdefault(k, {})["iou_medyan"] = round(med, 4)
        ozet_kova[k]["iou_n"] = len(grup)
        print(f"{k:10s} {len(grup):4d} {med:28.4f}")

    CIKTI.mkdir(parents=True, exist_ok=True)
    io.open(CIKTI / "doz_yanit.json", "w", encoding="utf-8").write(json.dumps({
        "_ne": "T139 · gorunurluk doz-yanit. ESIK KOYMAZ, ONERMEZ.",
        "_on_kayit": "results/t139/on_kayit.md",
        "_y1": "BAND_ORANI = kaplama(conf 0,10)/kaplama(conf 0,30) — 93_t106'dan ICE AKTARILDI",
        "_y2": "modeller arasi zemin maskesi IoU (v35/v34/v30)",
        "_sinir": "L ~73-118 arasinda HIC KARE YOK; egri orada BOSLUK tasir",
        "kova_ozeti": ozet_kova, "y1": satir, "y2": y2,
    }, ensure_ascii=False, indent=1))
    print(f"\nyazildi: {CIKTI / 'doz_yanit.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
