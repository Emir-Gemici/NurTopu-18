"""ONNX KARAR DENKLIGI — sahaya giden artefakt, sertifikaladigimiz kararı veriyor mu?

NEDEN (REVIEW_LOG D-116/3, amele "DOGRULANAMADI" diye yazdi):
Kabul denetimi (D-115) `navitas_seg_v27_best.pt` uzerinde kosuldu. Jetson'da
kosacak olan ise `navitas_seg_v27_best_512_fp16.onnx` — FP16'ya indirilmis,
BASKA bir calisma zamaniyla kosan BASKA bir artefakt. Ikisinin AYNI KARARI
verdigi HIC olculmedi. Ayrisiyorlarsa elimizdeki butun kabul kaydi ucmayacak
bir dosyaya aittir.

OLCULEN SEY MASKE BENZERLIGI DEGIL, KARARDIR. Maskeler %99 ortusup karar
degisebilir (esik civarindaki tek piksel seridi koridoru kapatir); maskeler
ayrisip karar ayni kalabilir (fark arenanin disindadir). Gorevi belirleyen sey
`analyze_path`in dondurdugu SERIT ve RED sebebidir.

    1. KARAR UYUSMAZLIGI : serit veya red sebebi farkli mi?           <- ASIL
    2. ROTA SAPMASI      : ikisi de rota uretiyorsa, govde yaricapiyla
                           kalinlastirilmis izler ne kadar ortusuyor?
    3. MASKE AYRISMASI   : baglam icin — IoU ve kaplama farki.

Yer gercegi KULLANILMAZ. Sorulan "hangisi dogru" degil, "ikisi ayni mi".
"""
import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

from ayarlar import REPO, uretim_onnx, uretim_pt

BURASI = Path(__file__).parent
sys.path.insert(0, str(REPO / "codes"))

from costmap_path_finder import R_GEREKLI_M  # noqa: E402
from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp,  # noqa: E402
                           _preprocess, analyze_path, get_masks)

KUME = BURASI / "calisma" / "sentetik_arena_kadraj_t66"
# T85: surum adi CIPLAK SABIT degildir (madde 16) — kayit defteri ve paket
# kunyesi tek kaynaktir; `--pt` / `--onnx` ile ezilebilir.
PT = uretim_pt()
ONNX = uretim_onnx()
CONF = 0.30


def karar(model, img, mpp):
    """(serit, red_sebebi, waypointler, trav_maskesi, tuval_boyu) dondur."""
    sq, small, icerik = _preprocess(img)
    h, w = sq.shape[:2]
    r = model.predict(small, imgsz=INFER_SIZE, conf=CONF, verbose=False)
    mk = _maskeleri_icerige_kirp(get_masks(r, h, w), icerik)
    trav, blok = mk[0], mk[1]
    yol, guven, wps, _k, red, _o = analyze_path(
        trav, icerik=icerik, engel_mask=blok, mpp=mpp,
        return_clean=True, return_reason=True, return_olcum=True)
    sebep = red[0] if isinstance(red, tuple) else red
    return yol, sebep, guven, wps, trav, (h, w)


def kalin_iz(wps, hw, r_px):
    """Waypoint zincirini govde yaricapiyla kalinlastirilmis maskeye cevir."""
    iz = np.zeros(hw, np.uint8)
    pts = [(int(round(x)), int(round(y))) for x, y in wps]
    for a, b in zip(pts, pts[1:]):
        cv2.line(iz, a, b, 1, 2)
    return cv2.dilate(iz, cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (2 * r_px + 1, 2 * r_px + 1)))


def iou(a, b):
    a, b = a > 0, b > 0
    birlesim = float((a | b).sum())
    return float((a & b).sum()) / birlesim if birlesim else 1.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pt", type=Path, default=PT)
    ap.add_argument("--onnx", type=Path, default=ONNX)
    ap.add_argument("--kume", type=Path, default=KUME)
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    man = json.loads((args.kume / "manifest.json").read_text(encoding="utf-8"))
    from ultralytics import YOLO
    m_pt = YOLO(str(args.pt), task="segment")
    m_ox = YOLO(str(args.onnx), task="segment")

    n = 0
    karar_ayni = rota_ikisi = 0
    uyusmazlik = []
    maske_iou, kaplama_fark, rota_iou, sapma_px, sapma_m = [], [], [], [], []

    for ornek in man["ornekler"]:
        if ornek.get("durum") != "YAZILDI" or not ornek.get("arena"):
            continue
        p = args.kume / ornek["cikti"]
        if not p.is_file():
            continue
        mpp = ornek["arena"].get("mpp")
        if not mpp:
            continue
        img = cv2.imread(str(p))
        if img is None:
            continue
        n += 1

        y1, s1, g1, w1, t1, hw = karar(m_pt, img, mpp)
        y2, s2, g2, w2, t2, _ = karar(m_ox, img, mpp)

        maske_iou.append(iou(t1, t2))
        kaplama_fark.append(float((t2 > 0).mean()) - float((t1 > 0).mean()))

        if (y1, s1) == (y2, s2):
            karar_ayni += 1
        else:
            uyusmazlik.append({"kare": p.name,
                               "pt": {"serit": y1, "red": s1, "guven": g1},
                               "onnx": {"serit": y2, "red": s2, "guven": g2}})

        if w1 and w2:
            rota_ikisi += 1
            r_px = max(1, int(round(R_GEREKLI_M / mpp)))
            rota_iou.append(iou(kalin_iz(w1, hw, r_px), kalin_iz(w2, hw, r_px)))
            # Her .pt waypoint'inin ONNX izine en kisa uzakligi
            a = np.array(w1, np.float32)
            b = np.array(w2, np.float32)
            d = np.sqrt(((a[:, None, :] - b[None, :, :]) ** 2).sum(-1)).min(1)
            sapma_px.append(float(d.max()))
            sapma_m.append(float(d.max()) * mpp)

    print(f"\n{'=' * 66}\nONNX KARAR DENKLIGI")
    print(f"  .pt   : {args.pt.name}")
    print(f"  .onnx : {args.onnx.name}\n{'=' * 66}")
    print(f"  olculen kare              : {n}")
    print(f"  KARAR AYNI                : {karar_ayni}/{n}  "
          f"(%{100 * karar_ayni / max(1, n):.1f})")
    print(f"  ikisi de rota uretti      : {rota_ikisi}/{n}")
    print("-" * 66)
    if rota_iou:
        print(f"  rota ortusmesi (IoU)      : ort {np.mean(rota_iou):.4f} · "
              f"en dusuk {np.min(rota_iou):.4f}")
        print(f"  azami sapma               : ort {np.mean(sapma_px):.1f} px "
              f"({np.mean(sapma_m):.3f} m) · en kotu {np.max(sapma_px):.1f} px "
              f"({np.max(sapma_m):.3f} m)")
    print(f"  zemin maskesi IoU         : ort {np.mean(maske_iou):.4f} · "
          f"en dusuk {np.min(maske_iou):.4f}")
    print(f"  kaplama farki (onnx-pt)   : ort {np.mean(kaplama_fark):+.5f} · "
          f"azami |fark| {np.max(np.abs(kaplama_fark)):.5f}")
    print("=" * 66)
    if uyusmazlik:
        print(f"  🔴 KARAR UYUSMAZLIGI: {len(uyusmazlik)} kare")
        for u in uyusmazlik[:12]:
            print(f"    {u['kare']}  pt={u['pt']['serit']}/{u['pt']['red']}"
                  f"  onnx={u['onnx']['serit']}/{u['onnx']['red']}")
    else:
        print("  KARAR UYUSMAZLIGI YOK — sahaya giden artefakt, "
              "sertifikaladigimiz karari veriyor.")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(
            {"pt": str(args.pt), "onnx": str(args.onnx), "n": n,
             "karar_ayni": karar_ayni, "rota_ikisi": rota_ikisi,
             "rota_iou_ort": float(np.mean(rota_iou)) if rota_iou else None,
             "rota_iou_min": float(np.min(rota_iou)) if rota_iou else None,
             "sapma_px_maks": float(np.max(sapma_px)) if sapma_px else None,
             "sapma_m_maks": float(np.max(sapma_m)) if sapma_m else None,
             "maske_iou_ort": float(np.mean(maske_iou)),
             "maske_iou_min": float(np.min(maske_iou)),
             "uyusmazlik": uyusmazlik},
            ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\njson -> {args.json}")


if __name__ == "__main__":
    main()
