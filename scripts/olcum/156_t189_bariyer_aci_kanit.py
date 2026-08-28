"""156 — T189 AYIRT EDICILIK KANITI · ON_KAYIT D-334 + D-336.

SORU: K5'in yer gercegi nufusu, T184'un duzelttigi DONME KORLUGUNU
yakalayabiliyor mu? Yakalayamiyorsa nufus VAKUM KAPIDIR (TEST_SPECS SS4.1).

YORDAM: `ince_bariyer_maskesi` T184 ONCESI haline (yalniz `ozgun` kolu)
MUTASYONLA dondurulur ve iki nufusta kac karede bariyer buldugu sayilir.
Model YUKLENMEZ — olculen sey DEDEKTOR, model degil.

⚠ Mutant, uretim kodunu DEGISTIRMEZ: calisma aninda kopya bir islev
kurulur. Depodaki `karar_sozlesmesi.py` dokunulmadan kalir.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

KOK = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(KOK / "codes"))

import karar_sozlesmesi as ks                                    # noqa: E402


def mutant_ince_bariyer_maskesi(bgr):
    """T184 ONCESI dedektor: YALNIZ `ozgun` kolu (yatay kapama + genislik).

    `karar_sozlesmesi.ince_bariyer_maskesi`nin (a) kolunun birebir kopyasi;
    (b) acidan bagimsiz kol KALDIRILMISTIR. Sabitler ve yardimci islev yine
    sozlesmeden gelir — ciplak sabit yazilmaz (madde 16).
    """
    im = np.asarray(bgr)
    if im.ndim != 3 or im.shape[2] != 3 or im.size == 0:
        return None
    h, w = im.shape[:2]
    if h < 3 or w < 3:
        return np.zeros((max(h, 0), max(w, 0)), np.uint8)
    lab = cv2.cvtColor(im.astype(np.uint8), cv2.COLOR_BGR2LAB)
    a = lab[:, :, 1].astype(np.int16) - 128
    kirmizi = (a > ks.BARIYER_KROMA_ESIGI).astype(np.uint8)
    kx0 = max(3, int(round(w * ks.BARIYER_KAPAMA_ORANI)) | 1)
    ky0 = max(3, int(round(kx0 / 12.0)) | 1)
    return ks._bariyer_kollari(
        cv2.morphologyEx(kirmizi, cv2.MORPH_CLOSE,
                         cv2.getStructuringElement(cv2.MORPH_RECT, (kx0, ky0))),
        w, h, uzun_eksen=False)


def _kol_var_mi(maske) -> bool:
    if maske is None:
        return False
    n, _l, _s, _c = cv2.connectedComponentsWithStats(maske, 8)
    return n > 1


def say(kume: Path, dedektor) -> dict:
    man = json.loads((kume / "manifest.json").read_text(encoding="utf-8"))
    tarandi = bulunan = okunamayan = 0
    for ornek in man["ornekler"]:
        p = kume / ornek["cikti"]
        img = cv2.imread(str(p))
        if img is None:
            okunamayan += 1
            continue
        tarandi += 1
        if _kol_var_mi(dedektor(img)):
            bulunan += 1
    return {"tarandi": tarandi, "bariyerli": bulunan,
            "okunamayan": okunamayan,
            "oran": round(bulunan / tarandi, 4) if tarandi else None}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--acili", type=Path, required=True)
    ap.add_argument("--yatay", type=Path, required=True)
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args()

    d = {}
    for ad, kume in (("acili", a.acili), ("yatay", a.yatay)):
        for sur, fn in (("saglam", ks.ince_bariyer_maskesi),
                        ("mutant", mutant_ince_bariyer_maskesi)):
            d[f"{ad}_{sur}"] = say(kume, fn)
            r = d[f"{ad}_{sur}"]
            print(f"  {ad:6s} · {sur:7s} bariyerli {r['bariyerli']:4d}/"
                  f"{r['tarandi']:4d} = %{100 * (r['oran'] or 0):.1f}", flush=True)

    # ON KAYIT SARTLARI (D-336) — sayilar gorulmeden yazildi
    dus = (d["acili_saglam"]["oran"] - d["acili_mutant"]["oran"]) * 100
    s1 = dus >= 40.0
    s3 = d["yatay_mutant"]["oran"] >= d["yatay_saglam"]["oran"]
    print("\n  ON KAYIT SARTLARI (D-336):")
    print(f"   1) acili dusus >= 40 puan : {dus:.1f} puan  -> "
          f"{'SAGLANDI' if s1 else 'SAGLANMADI'}")
    print(f"   3) yatayda mutant DUSMEZ  : mutant %{100*d['yatay_mutant']['oran']:.1f}"
          f" vs saglam %{100*d['yatay_saglam']['oran']:.1f}  -> "
          f"{'SAGLANDI' if s3 else 'SAGLANMADI'}")
    print(f"\n  AYIRT EDICI Mi: {'EVET' if (s1 and s3) else 'HAYIR'}")

    d["_on_kayit"] = {"sart1_acili_dusus_puan": round(dus, 1), "sart1": s1,
                      "sart3": s3, "ayirt_edici": bool(s1 and s3)}
    if a.json:
        a.json.parent.mkdir(parents=True, exist_ok=True)
        a.json.write_text(json.dumps(d, indent=1, ensure_ascii=False),
                          encoding="utf-8")
        print(f"json -> {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
