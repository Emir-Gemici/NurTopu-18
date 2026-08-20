"""T122 adim 0 — K0 TAKASININ TANISI: figurun zemini NEREYE gitti?

SORU (D-225: T121 sonucu TAKAS): t121_ft figur zemin kaplamasini %0,49'dan
%0,15'e dusurdu (oran 0,30 < 0,5 on kayit bandi). Iki AYRI aciklama var ve
ikisi FARKLI secenek onerir:
  (i) ASIRI GENELLEME — cati dersi figurun duz/parlak zeminine tasindi:
      kaybolan pikseller artik ENGEL (sinif 1) sayiliyor.
  (ii) GUVEN COKMESI — pikseller hicbir sinifa atanmiyor (maske YOK):
      model kararsizlasti, ders degil GUVEN kaybi var.
Ayrimi olcmek icin figurde v34 zemin maskesinden DUSEN pikseller alinir ve
ft'nin o piksellerde NE dedigi sayilir.

CIKTI: results/t122/k0_tanisi.json + gorsel (v34 / ft / fark haritasi).
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import cv2
import numpy as np

KOK = Path(__file__).resolve().parents[2]
for p in (KOK / "scripts", KOK / "codes"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from copy_paste_augmentation import zemin_ve_mevcut_engel  # noqa: E402
from ultralytics import YOLO  # noqa: E402

FIGUR = KOK / "data" / "arena_referans" / "sartname_s9_arena.png"
CIKTI = KOK / "results" / "t122"
CONF = 0.30                     # uretim zinciri (65 denetcisi ile AYNI)
MODELLER = {
    "v34": KOK / "models" / "navitas_seg_v34_best.pt",
    "t121_ft": KOK / "codes" / "runs" / "segment" / "t121_etiket_ft" / "weights" / "best.pt",
}


def main() -> int:
    bgr = cv2.imread(str(FIGUR))
    if bgr is None:
        print(f"figur okunamadi: {FIGUR}", file=sys.stderr)
        return 2
    maskeler = {}
    for ad, yol in MODELLER.items():
        model = YOLO(str(yol), task="segment")
        zemin, engel = zemin_ve_mevcut_engel(model, bgr, CONF)
        maskeler[ad] = (zemin.astype(bool), engel.astype(bool))
        del model

    z34, e34 = maskeler["v34"]
    zft, eft = maskeler["t121_ft"]
    kaybolan = z34 & ~zft                     # v34 zemin dedi, ft demedi
    toplam = z34.size

    sonuc = {
        "figur": str(FIGUR), "conf": CONF,
        "v34": {"zemin_pay": round(float(z34.mean()), 5),
                "engel_pay": round(float(e34.mean()), 5)},
        "t121_ft": {"zemin_pay": round(float(zft.mean()), 5),
                    "engel_pay": round(float(eft.mean()), 5)},
        "kaybolan_zemin_pay": round(float(kaybolan.mean()), 5),
        "kaybolan_piksel": int(kaybolan.sum()),
        "kaybolan_nereye": {
            "ENGEL_oldu": round(float((kaybolan & eft).sum() / max(1, kaybolan.sum())), 4),
            "HICBIR_SINIF": round(float((kaybolan & ~eft).sum() / max(1, kaybolan.sum())), 4),
        },
        "ft_engel_artisi_pay": round(float(eft.mean() - e34.mean()), 5),
        "yorum_kurali": ("ENGEL_oldu >= 0,5 -> (i) ASIRI GENELLEME; "
                         "HICBIR_SINIF >= 0,5 -> (ii) GUVEN COKMESI"),
        "kare_px": int(toplam),
    }
    sonuc["tani"] = ("ASIRI_GENELLEME"
                     if sonuc["kaybolan_nereye"]["ENGEL_oldu"] >= 0.5
                     else "GUVEN_COKMESI")

    CIKTI.mkdir(parents=True, exist_ok=True)
    io.open(CIKTI / "k0_tanisi.json", "w", encoding="utf-8").write(
        json.dumps(sonuc, ensure_ascii=False, indent=1))

    # Gorsel: v34 zemin (yesil) · ft zemin (yesil) · kaybolan (sari=hicbiri,
    # kirmizi=engel oldu)
    hucreler = []
    for ad, (z, e) in maskeler.items():
        g = bgr.copy()
        g[z] = (g[z] * 0.5 + np.array([0, 255, 0]) * 0.5).astype(np.uint8)
        g[e] = (g[e] * 0.5 + np.array([0, 0, 255]) * 0.5).astype(np.uint8)
        cv2.putText(g, ad, (10, 34), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 0), 2)
        hucreler.append(cv2.resize(g, (640, 360)))
    fark = bgr.copy()
    fark[kaybolan & ~eft] = (0, 255, 255)      # sari: hicbir sinif
    fark[kaybolan & eft] = (0, 0, 255)         # kirmizi: engel oldu
    cv2.putText(fark, "kaybolan zemin", (10, 34), cv2.FONT_HERSHEY_SIMPLEX,
                1.1, (255, 255, 0), 2)
    hucreler.append(cv2.resize(fark, (640, 360)))
    while len(hucreler) % 2:
        hucreler.append(np.zeros_like(hucreler[0]))
    satir = [np.hstack(hucreler[i:i + 2]) for i in range(0, len(hucreler), 2)]
    cv2.imwrite(str(CIKTI / "k0_tanisi.png"), np.vstack(satir))

    print(json.dumps(sonuc, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
