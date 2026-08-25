"""CURUTME 8 — dondurulmus kadrajda URETILEN rotayi GOZLE dogrula (D-80) ve
zeminin kenardan ne kadar UZAKTA bittigini piksel olarak olc.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import numpy as np

KOK = Path(r"O:\navitas")
sys.path.insert(0, str(KOK / "codes"))
import karar_sozlesmesi as ks  # noqa: E402
from rpi_inference import _preprocess, analyze_path  # noqa: E402

KARE_DIZIN = KOK / "dataset" / "dji_kirsal" / "images" / "val"
ETIKET_KOK = KOK / "results" / "dji_20260822" / "f5_olcek"
CIK = KOK / "results" / "dji_kirsal" / "curut_yapisal"


def etiket_bul(stem):
    for alt in ("A", "B", "C", "D"):
        p = ETIKET_KOK / alt / (stem + "_uc.png")
        if p.exists():
            return p
    return None


def rota_ciz(ad):
    img0 = cv2.imread(str(KARE_DIZIN / ad))
    lab0 = cv2.imread(str(etiket_bul(Path(ad).stem)), cv2.IMREAD_UNCHANGED)
    if lab0.ndim == 3:
        lab0 = lab0[:, :, 0]
    img = cv2.rotate(img0, cv2.ROTATE_90_CLOCKWISE)
    lab = cv2.rotate(lab0, cv2.ROTATE_90_CLOCKWISE)
    tuval, _, icerik = _preprocess(img)
    x0, y0, w, h = icerik
    big = cv2.resize(lab, (w, h), interpolation=cv2.INTER_NEAREST)
    zemin = np.zeros(tuval.shape[:2], np.uint8)
    engel = np.zeros(tuval.shape[:2], np.uint8)
    zemin[y0:y0 + h, x0:x0 + w] = (big == 1).astype(np.uint8)
    engel[y0:y0 + h, x0:x0 + w] = (big == 2).astype(np.uint8)
    s, g, wps, temiz, r = analyze_path(zemin, return_clean=True,
                                       return_reason=True, icerik=icerik,
                                       engel_mask=engel)
    vis = tuval.copy()
    renk = np.zeros_like(vis)
    renk[zemin > 0] = (0, 255, 0)
    renk[engel > 0] = (0, 0, 255)
    m = (zemin > 0) | (engel > 0)
    vis[m] = cv2.addWeighted(tuval, 0.55, renk, 0.45, 0)[m]
    bh = ks.hedef_bant_yuksekligi(h)
    cv2.rectangle(vis, (x0, y0), (x0 + w, y0 + h), (255, 255, 0), 6)
    cv2.line(vis, (x0, y0 + bh), (x0 + w, y0 + bh), (0, 255, 255), 6)
    cv2.line(vis, (x0, y0 + h - bh), (x0 + w, y0 + h - bh), (0, 255, 255), 6)
    for a, b in zip(wps, wps[1:]):
        cv2.line(vis, a, b, (255, 0, 255), 14)
    for p in wps:
        cv2.circle(vis, p, 18, (255, 0, 255), -1)
    cv2.putText(vis, "%s  serit=%s guven=%.3f" % (ad[-26:], s, g),
                (x0 + 20, y0 + 90), cv2.FONT_HERSHEY_SIMPLEX, 2.0,
                (255, 0, 255), 6)
    out = CIK / "bindirme" / ("%s_DONDURULMUS_ROTA.png" % Path(ad).stem[-19:])
    cv2.imwrite(str(out), cv2.resize(vis, (900, 900)))
    return out, s, g, len(wps)


def kenar_mesafesi():
    e = json.loads((KOK / "results" / "dji_kirsal" /
                    "bant_tanisi_etiket.json").read_text(encoding="utf-8"))
    hedefler = [r["kare"] for r in e["kareler"] if r["durum"] == "YAPISAL"]
    print("\nSINIF0 (elle) kadrajin UST/ALT kenarindan kac px UZAKTA bitiyor?")
    print("(bant esigi 172 px · '<172' = banda temas)")
    ust_l, alt_l = [], []
    for ad in hedefler:
        lab = cv2.imread(str(etiket_bul(Path(ad).stem)), cv2.IMREAD_UNCHANGED)
        if lab.ndim == 3:
            lab = lab[:, :, 0]
        big = cv2.resize(lab, (3840, 2160), interpolation=cv2.INTER_NEAREST)
        s0 = (big == 1)
        rows = np.nonzero(s0.any(axis=1))[0]
        if rows.size == 0:
            continue
        du, da = int(rows[0]), int(2160 - 1 - rows[-1])
        ust_l.append(du)
        alt_l.append(da)
        print("  %-26s ust_bosluk=%5d px  alt_bosluk=%5d px" % (ad[-24:], du, da))
    for ad, v in (("UST", ust_l), ("ALT", alt_l)):
        v = sorted(v)
        print("  %s bosluk: min %d · p50 %d · maks %d"
              % (ad, v[0], v[len(v) // 2], v[-1]))


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    (CIK / "bindirme").mkdir(parents=True, exist_ok=True)
    for ad in ("dji_20260822172613_0038_d__frame_000217_000007950.jpg",
               "dji_20260822172613_0038_d__frame_000207_000007620.jpg",
               "dji_20260822172613_0038_d__frame_000197_000007320.jpg"):
        out, s, g, n = rota_ciz(ad)
        print("%s -> serit=%s guven=%.3f wp=%d  %s" % (ad[-26:], s, g, n, out.name))
    kenar_mesafesi()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
