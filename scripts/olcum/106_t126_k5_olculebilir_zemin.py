"""K5 icin OLCULEBILIR ZEMIN: rota x bariyer kesisimini KABUL KUMESINDE olc.

🔴 BU BETIK KAPIYI DEGISTIRMEZ. Yetki siniri (AGENTS SS9.2): esik degistirmek
ve bir olcumu kapiya cevirmek basameleye ait DEGILDIR. Burada yalnizca
"K5 olculebilir mi" sorusu OLCULUR; K5'in neye bakacagina MIMAR karar verir.

SORUN (olculdu, D-231):
`63_bariyer_kesisimi.py` TEK karede kosar: `data/arena_referans/
sartname_s9_arena.png`. O karede UC MODEL de (v30 · v34 · t121_ft) rota
URETEMIYOR — `analyze_path` `UC_BANT_TEMAS_YOK` ile reddediyor (alt=0/1059px,
ust=0/1059px, gereken >=22px). Rota yoksa kesisim de yok: K5 her modelde
"OLCULEMEDI" donuyor ve TERFIYI BLOKLUYOR (fail-closed, D-180/T105 geregi
dogru davranis) — ama hicbir modeli AYIRT ETMIYOR.
⚠ Bariyerin KENDISI sorun degil: ayni figurde uc model de bariyer
piksellerinin %100'une ENGEL diyor. Yani K5'in sinamak istedigi guvenlik
ozelligi maske duzeyinde saglaniyor; olculemeyen sey ROTA ILE KESISIM.

BU BETIGIN OLCTUGU:
Kabul kumesinde (`profiles[default_profile].kabul_kumesi`, 65 denetcisiyle
AYNI kaynaktan okunur) her kare icin:
  · bariyer var mi (63'un MODELSIZ LAB a* dedektoru — ayni fonksiyon
    IMPORT edilir, kopyalanmaz),
  · uretim zinciri rota uretiyor mu,
  · uretiyorsa rota x bariyer kesisimi kac piksel.
Ornek olcum (v34, ilk 40 kare): 10 karede bariyer VE rota birlikte var.

CIKTI: results/t126/k5_zemin_<ad>.json
"""
from __future__ import annotations

import argparse
import importlib.util
import io
import json
import sys
from pathlib import Path

import cv2
import numpy as np

KOK = Path(__file__).resolve().parents[2]
for p in (KOK / "codes", KOK / "scripts" / "olcum"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp,  # noqa: E402
                           _preprocess, analyze_path, get_masks)


def _yukle(ad: str, dosya: str):
    """Rakamla baslayan modul adlari normal `import` ile alinamaz."""
    spec = importlib.util.spec_from_file_location(ad, KOK / "scripts" / "olcum" / dosya)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


B63 = _yukle("bariyer63", "63_bariyer_kesisimi.py")
K65 = _yukle("kabul65", "65_kabul_denetcisi.py")
CIKTI = KOK / "results" / "t126"
CONF = 0.30


def kare_olc(model, p: Path) -> dict | None:
    img = cv2.imread(str(p))
    if img is None:
        return None
    kol, kutular = B63.bariyer_maskesi(img)
    sq, small, icerik = _preprocess(img)
    h, w = sq.shape[:2]
    s = model.predict(small, imgsz=INFER_SIZE, conf=CONF, verbose=False)
    mk = _maskeleri_icerige_kirp(get_masks(s, h, w), icerik)
    trav, blok = mk[0], mk[1]
    yol, guven, wps, _c, red, _o = analyze_path(
        trav, icerik=icerik, engel_mask=blok, mpp=None,
        return_clean=True, return_reason=True, return_olcum=True)

    x0, y0, cw, ch = icerik
    kol_tuval = np.zeros((h, w), np.uint8)
    kol_tuval[y0:y0 + ch, x0:x0 + cw] = cv2.resize(
        kol, (cw, ch), interpolation=cv2.INTER_NEAREST)
    ust = kol_tuval > 0
    kayit = {
        "kare": p.name, "bariyer_kutu": len(kutular),
        "bariyer_px": int(ust.sum()),
        "rota_var": bool(yol is not None and wps),
        "red": None if red is None else red[0],
    }
    if kutular:
        kayit["bariyere_ENGEL_orani"] = round(float((blok[ust] > 0).mean()), 4)
        kayit["bariyere_ZEMIN_orani"] = round(float((trav[ust] > 0).mean()), 4)
    if kayit["rota_var"] and kutular:
        iz = np.zeros((h, w), np.uint8)
        pts = [(int(round(x)), int(round(y))) for x, y in wps]
        for a, b in zip(pts, pts[1:]):
            cv2.line(iz, a, b, 1, 3)
        kayit["kesisim_px"] = int(((iz > 0) & ust).sum())
    return kayit


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", type=Path, required=True)
    ap.add_argument("--ad", default=None)
    ap.add_argument("--adet", type=int, default=0, help="0 = tum kume")
    args = ap.parse_args()
    ad = args.ad or args.model.parent.parent.name
    kume = K65.kabul_kumesi_yolu()          # TEK KAYNAK (T125/D-226)
    yollar = sorted(kume.rglob("*.jpg"))
    if args.adet:
        yollar = yollar[:args.adet]

    from ultralytics import YOLO
    model = YOLO(str(args.model), task="segment")
    kayitlar = [k for k in (kare_olc(model, p) for p in yollar) if k]

    olculebilir = [k for k in kayitlar if k.get("kesisim_px") is not None]
    kesen = [k for k in olculebilir if k["kesisim_px"] > 0]
    ozet = {
        "model": str(args.model), "ad": ad, "kume": str(kume),
        "n": len(kayitlar),
        "bariyerli_kare": sum(1 for k in kayitlar if k["bariyer_kutu"]),
        "rota_uretilen": sum(1 for k in kayitlar if k["rota_var"]),
        "K5_OLCULEBILIR_kare": len(olculebilir),
        "kesen_kare": len(kesen),
        "kesisim_toplam_px": int(sum(k["kesisim_px"] for k in olculebilir)),
        "bariyere_ENGEL_ort": round(float(np.mean(
            [k["bariyere_ENGEL_orani"] for k in kayitlar
             if "bariyere_ENGEL_orani" in k])), 4) if any(
            "bariyere_ENGEL_orani" in k for k in kayitlar) else None,
        "kayitlar": kayitlar,
    }
    CIKTI.mkdir(parents=True, exist_ok=True)
    io.open(CIKTI / f"k5_zemin_{ad}.json", "w", encoding="utf-8").write(
        json.dumps(ozet, ensure_ascii=False, indent=1))
    print(json.dumps({k: v for k, v in ozet.items() if k != "kayitlar"},
                     ensure_ascii=False, indent=1))
    print("⚠ Bu bir KAPI DEGILDIR — K5'in neye bakacagi MIMARIN karari.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
