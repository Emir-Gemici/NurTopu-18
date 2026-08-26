"""GERCEK ARENA: uretilen rota BARIYER KOLUNU kesiyor mu?

Bariyer, sartname figurunde kapali guzergahi kapatan tek yapidir. Ince ve
yukseltilmis oldugu icin altindaki zemin gorunur; segmentasyon onu engel
saymazsa rota UZERINDEN gecer ve IKA carpar.

Bariyer, sahnedeki TEK yuksek-kromali kirmizi yapidir (D-87: sahnenin geri
kalaninin tamaminda |a| < 1). Bu yuzden LAB a* ile guvenle bulunur — model
kullanilmaz, olcum modelden bagimsizdir.
"""
import sys
from pathlib import Path

import cv2
import numpy as np

# T161: kok `ayarlar`dan gelir — ciplak yol yazilmaz; kopya
# agacta (worktree) KENDI deposunu gosterir (ON_KAYIT SS22).
from ayarlar import REPO  # noqa: E402
sys.path.insert(0, str(REPO / "codes"))

from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp, _preprocess,
                           analyze_path, get_masks)

ARENA = REPO / "data" / "arena_referans" / "sartname_s9_arena.png"
import argparse
MODEL = REPO / "models" / "navitas_seg_v24_best.pt"
CIKTI = REPO.parent / "navitas-local-train" / "results" / "t63"


def bariyer_maskesi(img):
    """Yuksek kromali KIRMIZI seritler -> bariyer kollari."""
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    a = lab[:, :, 1].astype(np.int16) - 128
    kirmizi = (a > 25).astype(np.uint8)
    # Serit araliklarini (beyaz) kapatarak kolu tek parca yap
    kirmizi = cv2.morphologyEx(kirmizi, cv2.MORPH_CLOSE,
                               cv2.getStructuringElement(cv2.MORPH_RECT, (61, 5)))
    n, lbl, st, _ = cv2.connectedComponentsWithStats(kirmizi, 8)
    kol = np.zeros_like(kirmizi)
    kutular = []
    for i in range(1, n):
        x, y, w, h, alan = st[i]
        if alan < 300:
            continue
        if w > 4 * max(1, h) and w > 60:          # uzun, ince, YATAY
            kol[lbl == i] = 1
            kutular.append((x, y, w, h, int(alan)))
    return kol, kutular


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", type=Path, default=MODEL)
    args = ap.parse_args()
    from ultralytics import YOLO
    img = cv2.imread(str(ARENA))
    kol, kutular = bariyer_maskesi(img)
    print(f"kare: {img.shape[1]}x{img.shape[0]}")
    print(f"BARIYER KOLU bulundu: {len(kutular)}")
    for x, y, w, h, a in kutular:
        print(f"  kutu x={x} y={y} w={w} h={h} alan={a}")
    if not kutular:
        print("  bariyer bulunamadi — olcum yapilamaz")
        return

    model = YOLO(str(args.model), task="segment")
    sq, small, icerik = _preprocess(img)
    h, w = sq.shape[:2]
    sonuc = model.predict(small, imgsz=INFER_SIZE, conf=0.30, verbose=False)
    mk = _maskeleri_icerige_kirp(get_masks(sonuc, h, w), icerik)
    trav, blok = mk[0], mk[1]
    yol, guven, wps, _k, red, olcum = analyze_path(
        trav, icerik=icerik, engel_mask=blok, mpp=None,
        return_clean=True, return_reason=True, return_olcum=True)
    print(f"\nkarar: serit={yol} guven={guven} red={red}")

    # Bariyeri TUVAL cercevesine tasi (rota orada cizili)
    x0, y0, cw, ch = icerik
    kol_tuval = np.zeros((h, w), np.uint8)
    kol_tuval[y0:y0 + ch, x0:x0 + cw] = cv2.resize(
        kol, (cw, ch), interpolation=cv2.INTER_NEAREST)

    # 1) Model bariyeri ENGEL sayiyor mu?
    ust = kol_tuval > 0
    print(f"\nBARIYER PIKSELLERI (n={int(ust.sum())}):")
    print(f"  model ENGEL diyor : %{100.0 * float((blok[ust] > 0).mean()):.1f}")
    print(f"  model ZEMIN diyor : %{100.0 * float((trav[ust] > 0).mean()):.1f}")

    # 2) Rota bariyeri KESIYOR mu?
    if not wps:
        print("  rota yok — kesisim olculemez")
        return
    iz = np.zeros((h, w), np.uint8)
    pts = [(int(round(x)), int(round(y))) for x, y in wps]
    for p, q in zip(pts, pts[1:]):
        cv2.line(iz, p, q, 1, 3)
    kesisim = int(((iz > 0) & ust).sum())
    print(f"\n  ROTA x BARIYER kesisimi: {kesisim} px  ->  "
          f"{'KESIYOR — IKA CARPAR' if kesisim else 'kesmiyor'}")

    gor = sq.copy()
    gor[ust] = (0, 255, 255)
    for p, q in zip(pts, pts[1:]):
        cv2.line(gor, p, q, (0, 0, 255), 3)
    cv2.imwrite(str(CIKTI / "bariyer_kesisim.png"), gor)
    print(f"  gorsel -> {CIKTI / 'bariyer_kesisim.png'}")


if __name__ == "__main__":
    main()
