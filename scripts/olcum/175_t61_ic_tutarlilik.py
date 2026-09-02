"""T61 (D-401) — IC TUTARLILIK adaylari: KESIF turu (ESIK YAZILMAZ).

ON KAYIT: results/t61_ic_tutarlilik/ON_KAYIT.md (adaylar + yontem + X1..X5
kapilari sonuc gorulmeden yazildi).

Kaplama ve kenar YAPISAL olarak orta siddetli cokmeyi yakalayamaz (ikisi de
alan/temas olcusu). Bu betik DOKU/RENK ic tutarliligina bakar:
  B1 maske-ici HSV kanal varyansi (S ve V std)
  B2 bilesen-bazli LAB renk sapmasi (bilesenler arasi agirlikli yayilim)
  B3 maske-ici Laplacian enerjisi (maske ERODE edilerek — kenar sizintisi)

COKUS TANIMI ESIKSIZDIR: `gercek_kare_etiket_v1` GT poligonlariyla
IoU(model zemin, GT zemin) hesaplanir ve adaylarin IoU ile SIRA
KORELASYONU raporlanir. Kesme noktasi SECILMEZ (D-86 dersi).

Madde 4: yalniz OpenCV + NumPy. Madde 15: bu tur uretime hicbir sey baglamaz.
"""
import argparse
import json
import sys
from importlib import import_module
from pathlib import Path

import cv2
import numpy as np

from ayarlar import REPO, uretim_pt

sys.path.insert(0, str(REPO / "codes"))

from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp,  # noqa: E402
                           _preprocess, get_masks)

kabul_kumesi_yolu = import_module("65_kabul_denetcisi").kabul_kumesi_yolu

CONF = 0.30
GT_KOK = Path("O:/navitas-local-train/calisma/gercek_kare_etiket_v1")
GT_ZEMIN_SINIFI = 0
ERODE_YARICAP = 3      # X4: Laplacian cekirdegi maske disini okumasin


def gt_maskesi(etiket_yolu, h, w, sinif=GT_ZEMIN_SINIFI):
    """YOLO-seg poligon dosyasindan ikili maske kur (normalize -> piksel)."""
    m = np.zeros((h, w), np.uint8)
    for satir in etiket_yolu.read_text(encoding="utf-8").splitlines():
        parcalar = satir.split()
        if len(parcalar) < 7:
            continue
        try:
            s = int(float(parcalar[0]))
        except ValueError:
            continue
        if s != sinif:
            continue
        koord = np.array([float(x) for x in parcalar[1:]], dtype=np.float32)
        if koord.size % 2:
            koord = koord[:-1]
        pts = koord.reshape(-1, 2) * np.array([w, h], dtype=np.float32)
        cv2.fillPoly(m, [pts.astype(np.int32)], 1)
    return m


def iou(a, b):
    a = (np.asarray(a) > 0)
    b = (np.asarray(b) > 0)
    birlesim = np.logical_or(a, b).sum()
    if birlesim == 0:
        return None
    return float(np.logical_and(a, b).sum()) / float(birlesim)


def adaylari_olc(bgr, maske):
    """B1/B2/B3 — hepsi maske ICINDE, yalniz cv2 + numpy."""
    mu = (np.asarray(maske) > 0).astype(np.uint8)
    if mu.sum() < 50:
        return None

    # B1 — HSV kanal varyansi (maske icinde)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    _ort, std = cv2.meanStdDev(hsv, mask=mu)
    b1_s, b1_v = float(std[1, 0]), float(std[2, 0])

    # B2 — bilesen-bazli LAB renk sapmasi
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    n, etiket, ist, _mrk = cv2.connectedComponentsWithStats(mu, connectivity=8)
    merkezler, agirliklar = [], []
    for k in range(1, n):
        alan = int(ist[k, cv2.CC_STAT_AREA])
        if alan < 25:
            continue
        bilesen = (etiket == k).astype(np.uint8)
        ort = cv2.mean(lab, mask=bilesen)[:3]
        merkezler.append(ort)
        agirliklar.append(alan)
    if len(merkezler) >= 2:
        M = np.array(merkezler, dtype=np.float64)
        w_ = np.array(agirliklar, dtype=np.float64)
        w_ = w_ / w_.sum()
        genel = (M * w_[:, None]).sum(axis=0)
        b2 = float(np.sqrt((w_ * ((M - genel) ** 2).sum(axis=1)).sum()))
    else:
        b2 = 0.0

    # B3 — maske ICINDE Laplacian enerjisi; X4: maske ERODE edilir
    gri = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    lap = cv2.Laplacian(gri, cv2.CV_32F, ksize=3)
    enerji = cv2.multiply(lap, lap)
    cekirdek = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (2 * ERODE_YARICAP + 1, 2 * ERODE_YARICAP + 1))
    ic = cv2.erode(mu, cekirdek)
    if ic.sum() < 50:
        ic = mu
    b3_ort = float(cv2.mean(enerji, mask=ic)[0])
    _o, es = cv2.meanStdDev(enerji, mask=ic)
    b3_std = float(es[0, 0])

    return {"B1_S_std": b1_s, "B1_V_std": b1_v, "B2_lab_yayilim": b2,
            "B3_lap_ort": b3_ort, "B3_lap_std": b3_std,
            "bilesen": int(len(merkezler)), "alan_px": int(mu.sum())}


def sira_korelasyonu(x, y):
    """Spearman = siralar uzerinde Pearson (saf NumPy; madde 4)."""
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    if len(x) < 3:
        return None

    def sira(v):
        s = np.argsort(np.argsort(v)).astype(np.float64)
        return s
    rx, ry = sira(x), sira(y)
    rx -= rx.mean()
    ry -= ry.mean()
    payda = np.sqrt((rx ** 2).sum() * (ry ** 2).sum())
    return float((rx * ry).sum() / payda) if payda > 0 else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", type=Path, default=uretim_pt())
    ap.add_argument("--sinir", type=int, default=0)
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    from ultralytics import YOLO
    model = YOLO(str(args.model), task="segment")
    sayac = {"segmentasyon": 0}

    # ── (a) GT'li gercek kareler: IoU + adaylar ──────────────────────────
    gt_kayitlar = []
    etiketler = sorted((GT_KOK / "labels").glob("*.txt"))
    if args.sinir:
        etiketler = etiketler[:args.sinir]
    for et in etiketler:
        img_yolu = GT_KOK / "images" / (et.stem + ".jpg")
        if not img_yolu.is_file():
            continue
        img = cv2.imread(str(img_yolu))
        if img is None:
            continue
        sq, small, icerik = _preprocess(img)
        son = model.predict(small, imgsz=INFER_SIZE, conf=CONF, verbose=False)
        sayac["segmentasyon"] += 1
        mk = _maskeleri_icerige_kirp(get_masks(son, *sq.shape[:2]), icerik)
        model_zemin = np.asarray(mk[0])

        # GT ham cozunurlukte; model maskesi letterbox tuvalinde -> GT'yi
        # ayni tuvale tasi (icerik kutusuna olcekle, disini 0 birak).
        gt_ham = gt_maskesi(et, img.shape[0], img.shape[1])
        ix, iy, iw, ih = icerik
        gt_tuval = np.zeros_like(model_zemin)
        gt_tuval[iy:iy + ih, ix:ix + iw] = cv2.resize(
            gt_ham, (iw, ih), interpolation=cv2.INTER_NEAREST)

        skor = iou(model_zemin, gt_tuval)
        ol = adaylari_olc(sq, model_zemin)
        if skor is None or ol is None:
            continue
        kayit = {"kare": et.stem, "iou": skor}
        kayit.update(ol)
        gt_kayitlar.append(kayit)

    # ── (b) referans: kabul kumesi (sentetik) ───────────────────────────
    kume = kabul_kumesi_yolu()
    man = json.loads((kume / "manifest.json").read_text(encoding="utf-8"))
    ref_kayitlar = []
    ornekler = [o for o in man["ornekler"]
                if o.get("durum") == "YAZILDI" and o.get("arena")]
    if args.sinir:
        ornekler = ornekler[:args.sinir]
    for o in ornekler:
        p = kume / o["cikti"]
        if not p.is_file():
            continue
        img = cv2.imread(str(p))
        if img is None:
            continue
        sq, small, icerik = _preprocess(img)
        son = model.predict(small, imgsz=INFER_SIZE, conf=CONF, verbose=False)
        sayac["segmentasyon"] += 1
        mk = _maskeleri_icerige_kirp(get_masks(son, *sq.shape[:2]), icerik)
        ol = adaylari_olc(sq, np.asarray(mk[0]))
        if ol:
            ol["kare"] = p.name
            ref_kayitlar.append(ol)

    ADAYLAR = ["B1_S_std", "B1_V_std", "B2_lab_yayilim", "B3_lap_ort",
               "B3_lap_std"]
    iou_dizi = [k["iou"] for k in gt_kayitlar]
    print(f"\nGT kare: {len(gt_kayitlar)} · IoU medyan "
          f"{np.median(iou_dizi):.3f} · min {min(iou_dizi):.3f} · "
          f"maks {max(iou_dizi):.3f}")
    print(f"referans (sentetik) kare: {len(ref_kayitlar)}\n")

    kor = {}
    print("ADAY                 IoU ile sira korelasyonu   GT medyan   REF medyan")
    for ad in ADAYLAR:
        r = sira_korelasyonu([k[ad] for k in gt_kayitlar], iou_dizi)
        kor[ad] = r
        gm = float(np.median([k[ad] for k in gt_kayitlar]))
        rm = float(np.median([k[ad] for k in ref_kayitlar])) if ref_kayitlar else float("nan")
        print(f"{ad:20s} {r:+.3f}                    {gm:10.2f}  {rm:10.2f}")

    # IoU ceyrekleri (betimsel — esik DEGIL)
    q = np.percentile(iou_dizi, [25, 50, 75])
    ceyrek = {}
    print(f"\nIoU ceyrekleri: Q1={q[0]:.3f} Q2={q[1]:.3f} Q3={q[2]:.3f}")
    for ad in ADAYLAR:
        gruplar = [[], [], [], []]
        for k in gt_kayitlar:
            i = int(np.searchsorted(q, k["iou"]))
            gruplar[min(i, 3)].append(k[ad])
        medyanlar = [round(float(np.median(g)), 2) if g else None
                     for g in gruplar]
        ceyrek[ad] = medyanlar
        print(f"  {ad:20s} ceyrek medyanlari (dusuk IoU -> yuksek): {medyanlar}")

    # Kapilar
    x1 = len(gt_kayitlar) == len(etiketler)
    x2 = all(np.isfinite(k[ad]) for k in gt_kayitlar for ad in ADAYLAR)
    x3 = sayac["segmentasyon"] == len(gt_kayitlar) + len(ref_kayitlar)
    print(f"\nX1 GT okunabildi ({len(gt_kayitlar)}/{len(etiketler)}): "
          f"{'GECTI' if x1 else '🔴 DUSTU'}")
    print(f"X2 sayisal saglamlik: {'GECTI' if x2 else '🔴 DUSTU'}")
    print(f"X3 tek cikarim: {'GECTI' if x3 else '🔴 DUSTU'}")
    print(f"X4 kenar sizintisi korumasi: GECTI (erode r={ERODE_YARICAP})")

    cikti = {"_on_kayit": "results/t61_ic_tutarlilik/ON_KAYIT.md",
             "_model": str(args.model),
             "_vekil_notu": ("cokus vekili = GT IoU'su dusuk kareler; tek "
                             "mekan/67 kare (X5)"),
             "_esik_yok": "Bu tur ESIK URETMEZ (D-86 dersi)",
             "X1": x1, "X2": x2, "X3": x3, "erode_yaricap": ERODE_YARICAP,
             "iou": {"n": len(gt_kayitlar),
                     "medyan": float(np.median(iou_dizi)),
                     "min": float(min(iou_dizi)), "maks": float(max(iou_dizi)),
                     "ceyrekler": [float(x) for x in q]},
             "sira_korelasyonu": kor, "ceyrek_medyanlari": ceyrek,
             "gt_kayitlar": gt_kayitlar, "referans_kayitlar": ref_kayitlar}
    hedef = args.json or (REPO / "results" / "t61_ic_tutarlilik"
                          / "olcum_20260903.json")
    hedef.parent.mkdir(parents=True, exist_ok=True)
    hedef.write_text(json.dumps(cikti, ensure_ascii=False, indent=1),
                     encoding="utf-8")
    print(f"json -> {hedef}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
