"""k3b/ornekler/: varyant başına harita 1 (kolay/orta/zor) mozaik + algı JPG'leri (800 px, %85).
Kaynak: k3b/<varyant>/harita_1_<lv>/iha_scan/{ortomozaik,algi}.jpg (ölçüm çıktısı, elle düzenlenmez)."""
import sys
from pathlib import Path

import cv2

for _akim in (sys.stdout, sys.stderr):
    try:
        _akim.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

K3B = Path(__file__).resolve().parent
OUT = K3B / "ornekler"
OUT.mkdir(exist_ok=True)
n = 0
for v in ("taban", "v1", "v2", "v3", "v1_nadir", "v1_asfalt", "v1_zemin_toprak", "v1_yerlesim_d441"):
    for lv in ("kolay", "orta", "zor"):
        for ad, kisa in (("ortomozaik.jpg", "mozaik"), ("algi.jpg", "algi")):
            p = K3B / v / f"harita_1_{lv}" / "iha_scan" / ad
            if not p.is_file():
                continue
            im = cv2.imread(str(p))
            cv2.imwrite(str(OUT / f"{v}_1_{lv}_{kisa}.jpg"), cv2.resize(im, (800, 800), interpolation=cv2.INTER_AREA),
                        [cv2.IMWRITE_JPEG_QUALITY, 85])
            n += 1
print(f"[ornekler] {n} dosya → {OUT}")
