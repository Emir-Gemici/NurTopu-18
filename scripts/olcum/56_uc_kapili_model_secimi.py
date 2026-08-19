"""T50 FAZ 1 — 11 modeli MIMARININ olcutuyle sirala. mAP KULLANILMAZ.

NEDEN (REVIEW_LOG D-61, D-62): mimari degismez "Serbest alan OTORITEDIR;
zemin degil -> engel". Uretim modeli bunun TERSINI yapiyor: her seye zemin
diyor, fail-safe kural hic ateslenmiyor. Model secimi bugune kadar mAP ile
yapildi; K-3 zaten "mAP arena siralamasini TERSINE ceviriyor" diyordu.

UC KAPI
  1. ALAN ICI DOGRULUK  — rescuenet_1024 val: zemin IoU + KESINLIK.
     KESINLIK ONCELIKLI: yanlis-pozitif zemin, kacirilan zeminden TEHLIKELI.
  2. ALAN DISI TEMKIN   — data/raw_frames (OTOPARK): zemin kaplamasi.
     Model burayi arena zemini SANMAMALI. %73,7 = cokus · %0-20 = kabul.
  3. KARAR DOGRULUGU    — data/arena_kompozit: manifest `acik_serit` ile
     sistemin verdigi serit kac karede ayni.

GURULTU TABANI: 0,04'ten kucuk farklar GURULTUDUR. Esitse daha TEMKINLI olan
(kapi 2) secilir.

Kullanim:
  venv\\Scripts\\python.exe 56_uc_kapili_model_secimi.py [--val N] [--gorsel]
"""
import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

from ayarlar import REPO

sys.path.insert(0, str(REPO / "codes"))
from karar_sozlesmesi import zemin_kaplamasi          # noqa: E402
from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp,  # noqa: E402
                           _preprocess, _rota_kararini_esikle, analyze_path,
                           get_masks)

CIK = Path(__file__).parent / "results" / "t50_uc_kapi"
CONF = 0.30                    # uretim `run_image` varsayilani

MODELLER = [
    "navitas_seg_v2_best.pt", "navitas_seg_v3_best.pt", "navitas_seg_v4_best.pt",
    "navitas_seg_v5_best.pt", "aday_v5a_s640.pt", "aday_v5b_s640ft.pt",
    "aday_v5c_m640.pt", "aday_v9_mixup_m640.pt", "navitas_seg_v17_best.pt",
    "navitas_seg_v20_best.pt", "navitas_seg_v21_best.pt",
]


# ── ortak: uretim zinciriyle maske uret ─────────────────────────────────────
def uretim_maskeleri(model, img):
    sq, small, icerik = _preprocess(img)
    h, w = sq.shape[:2]
    r = model.predict(small, imgsz=INFER_SIZE, conf=CONF, verbose=False)
    m = _maskeleri_icerige_kirp(get_masks(r, h, w), icerik)
    return sq, m, icerik


def _gt_maske(etiket_yolu, h, w, sinif="0"):
    m = np.zeros((h, w), np.uint8)
    if not etiket_yolu.exists():
        return m
    for satir in etiket_yolu.read_text().splitlines():
        pr = satir.split()
        if len(pr) < 7 or pr[0] != sinif:
            continue
        k = np.array([float(x) for x in pr[1:]], np.float32).reshape(-1, 2)
        k[:, 0] *= w
        k[:, 1] *= h
        cv2.fillPoly(m, [k.astype(np.int32)], 1)
    return m


# ── KAPI 1 ───────────────────────────────────────────────────────────────────
def kapi1_alan_ici(model, n):
    """Mikro-ortalama zemin IoU + KESINLIK (rescuenet_1024 val)."""
    kok = REPO / "dataset" / "rescuenet_1024"
    gorseller = sorted((kok / "images" / "val").iterdir())[:n]
    kesisim = birlesim = tp = tahmin = gercek = 0
    for p in gorseller:
        img = cv2.imread(str(p))
        if img is None:
            continue
        h, w = img.shape[:2]
        gt = _gt_maske(kok / "labels" / "val" / f"{p.stem}.txt", h, w)
        sq, m, icerik = uretim_maskeleri(model, img)
        x0, y0, iw, ih = icerik
        pred = m[0][y0:y0 + ih, x0:x0 + iw]
        if pred.shape != gt.shape:
            pred = cv2.resize(pred, (gt.shape[1], gt.shape[0]),
                              interpolation=cv2.INTER_NEAREST)
        p_b, g_b = pred > 0, gt > 0
        kesisim += int(np.count_nonzero(p_b & g_b))
        birlesim += int(np.count_nonzero(p_b | g_b))
        tp += int(np.count_nonzero(p_b & g_b))
        tahmin += int(np.count_nonzero(p_b))
        gercek += int(np.count_nonzero(g_b))
    return {
        "n": len(gorseller),
        "iou": kesisim / birlesim if birlesim else 0.0,
        "kesinlik": tp / tahmin if tahmin else 0.0,
        "duyarlilik": tp / gercek if gercek else 0.0,
        "tahmin_kaplama": tahmin / max(1, len(gorseller)),
    }


# ── KAPI 2 ───────────────────────────────────────────────────────────────────
def kapi2_alan_disi(model):
    """OTOPARK karelerinde zemin kaplamasi — DUSUK olan IYI."""
    kareler = sorted((REPO / "data" / "raw_frames").rglob("*.jpg"))
    oranlar = []
    for p in kareler:
        img = cv2.imread(str(p))
        if img is None:
            continue
        _sq, m, icerik = uretim_maskeleri(model, img)
        oranlar.append(zemin_kaplamasi(m[0], icerik))
    o = sorted(oranlar)
    q = lambda t: o[min(len(o) - 1, max(0, int(round(t * (len(o) - 1)))))]  # noqa: E731
    return {"n": len(o), "ort": float(np.mean(o)) if o else 0.0,
            "p50": q(.5) if o else 0.0, "maks": o[-1] if o else 0.0}


# ── KAPI 3 ───────────────────────────────────────────────────────────────────
def _kompozit_kayitlari():
    mf = json.loads((REPO / "data" / "arena_kompozit" / "manifest.json")
                    .read_text(encoding="utf-8"))
    kok = REPO / "data" / "arena_kompozit"
    for o in mf.get("ornekler", []):
        if o.get("durum") != "YAZILDI" or not o.get("arena"):
            continue
        yield kok / o["cikti"], o["arena"]


def kapi3_karar(model):
    """Manifest `acik_serit` ile sistemin verdigi serit kac karede ayni."""
    dogru = yanlis = ret = 0
    sebepler = {}
    for yol, arena in _kompozit_kayitlari():
        img = cv2.imread(str(yol))
        if img is None:
            continue
        _sq, m, ic_lb = uretim_maskeleri(model, img)
        ax, ay, aw, ah = arena["icerik"]           # arena ROI, tuval koordinatina
        icerik = (ic_lb[0] + ax, ic_lb[1] + ay, aw, ah)
        y, g, w, r = analyze_path(m[0], icerik=icerik, engel_mask=m.get(1),
                                  mpp=arena.get("mpp"), return_reason=True)
        y, g, w, r = _rota_kararini_esikle(y, g, w, r)
        if y is None:
            ret += 1
            s = r[0] if r else "-"
            sebepler[s] = sebepler.get(s, 0) + 1
        elif y == arena["acik_serit"]:
            dogru += 1
        else:
            yanlis += 1
    return {"n": dogru + yanlis + ret, "dogru": dogru, "yanlis": yanlis,
            "ret": ret, "sebepler": sebepler}


# ── GORSEL ───────────────────────────────────────────────────────────────────
def bindirme(model, img, baslik):
    """Yesil = zemin, Kirmizi = engel."""
    sq, m, icerik = uretim_maskeleri(model, img)
    vis = sq.copy()
    ust = vis.copy()
    ust[m[0] > 0] = (0, 200, 0)
    ust[m[1] > 0] = (0, 0, 200)
    vis = cv2.addWeighted(vis, 0.45, ust, 0.55, 0)
    x0, y0, iw, ih = icerik
    cv2.rectangle(vis, (x0, y0), (x0 + iw, y0 + ih), (255, 255, 255), 2)
    kap = 100.0 * zemin_kaplamasi(m[0], icerik)
    cv2.putText(vis, f"{baslik}  zemin %{kap:.1f}", (16, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
    return vis


def gorseller_uret(ad, model):
    CIK.mkdir(parents=True, exist_ok=True)
    otopark = sorted((REPO / "data" / "raw_frames").rglob("*.jpg"))[0]
    val = sorted((REPO / "dataset" / "rescuenet_1024" / "images" / "val")
                 .iterdir())[0]
    for etiket, p in (("otopark", otopark), ("rescuenet_val", val)):
        img = cv2.imread(str(p))
        if img is None:
            continue
        cv2.imwrite(str(CIK / f"{ad}__{etiket}.jpg"),
                    bindirme(model, img, f"{ad} / {etiket}"))
    print(f"    gorsel yazildi -> {CIK}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--val", type=int, default=120)
    ap.add_argument("--gorsel", action="store_true")
    ap.add_argument("--modeller", nargs="*", default=None)
    a = ap.parse_args()

    from ultralytics import YOLO
    secili = a.modeller or MODELLER
    CIK.mkdir(parents=True, exist_ok=True)
    satirlar = []
    print(f"UC KAPILI MODEL SECIMI · conf={CONF} · val n={a.val} · "
          f"otopark n=67 · kompozit n=9")
    print("=" * 118)
    print(f"{'model':<26}{'K1 IoU':>8}{'K1 kesinlik':>13}{'K1 duyar':>10}"
          f"{'K2 otopark ort':>16}{'K2 maks':>9}"
          f"{'K3 dogru':>10}{'K3 yanlis':>11}{'K3 ret':>8}")
    for ad in secili:
        yol = REPO / "models" / ad
        if not yol.exists():
            print(f"{ad:<26}  (dosya yok)")
            continue
        mdl = YOLO(str(yol), task="segment")
        k1 = kapi1_alan_ici(mdl, a.val)
        k2 = kapi2_alan_disi(mdl)
        k3 = kapi3_karar(mdl)
        satirlar.append({"model": ad, "k1": k1, "k2": k2, "k3": k3})
        print(f"{ad:<26}{k1['iou']:>8.3f}{k1['kesinlik']:>13.3f}"
              f"{k1['duyarlilik']:>10.3f}{100*k2['ort']:>15.1f}%"
              f"{100*k2['maks']:>8.1f}%{k3['dogru']:>10}{k3['yanlis']:>11}"
              f"{k3['ret']:>8}")
        if a.gorsel:
            gorseller_uret(ad.replace(".pt", ""), mdl)
        del mdl
    (CIK / "t50_uc_kapi.json").write_text(
        json.dumps(satirlar, ensure_ascii=False, indent=1), encoding="utf-8")
    print("=" * 118)
    print(f"JSON -> {CIK / 't50_uc_kapi.json'}")


if __name__ == "__main__":
    main()
