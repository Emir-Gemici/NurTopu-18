"""rota_yol_olcumu — "ROTA YOL USTUNDE MI" olcumunun TEK tanimi (T152 · ON_KAYIT §11(2) / K6 · §12).

Bu modul 142_gece_olcum.py'den (gercek kare, b-ek2) TASINDI; artik iki tuketici de
AYNI fonksiyonlari cagirir — tanim iki yerde ayri ayri yasamaz (D-90 "tanim farki" dersi):
  * 142_gece_olcum.py  : 29 test karesi, uzlasi/elle etiket, kapi YANLIS GUZERGAH == 0
  * 61_rota_moloza_basma.py -> 65_kabul_denetcisi.py K6 : sentetik kabul kumesi (t66, YOLO
    yer gercegi), kapi yanlis guzergah orani <= %5

Tanim (degismez, sonuc gorulmeden yazildi):
  rota cizgisi  = ardisik waypoint'leri birlestiren 1 px polylines, TUVAL koordinati
  yol_payi      = cizgi ∩ sinif 0  /  cizgi
  engel_wp      = sinif 1 ustundeki (ya da tuval DISINDAKI, fail-closed) waypoint sayisi
  YANLIS GUZERGAH <=> yol_payi < 0,90  VEYA  engel_wp > 0

TUVAL: `rpi_inference._preprocess` letterbox'u — yan = max(h, w), gorüntü (x0, y0) =
((yan-w)//2, (yan-h)//2) ile ortalanir. `uc_durum_maske` etiketi AYNI yerlesimle tuvale
tasir; boylece `analyze_path`in urettigi waypoint'ler (tuval koordinati) etiketle ayni
cercevede kesistirilir. Kabul kumesinde kareler 640x640 oldugundan yerlesim birebirdir
(x0 = y0 = 0); genel kareler icin dolgu bandi ETIKETSIZ kalir.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import cv2
import numpy as np

OLCUM = Path(__file__).resolve().parent

# ON_KAYIT §11(2) — T152 "rota yol ustunde mi" (b-ek2); sonuc gorulmeden yazildi (2026-08-27).
KAPI_B_EK2 = {"yol_payi_min": 0.90, "engel_wp_maks": 0}
ETIKETSIZ, SINIF0, SINIF1 = 0, 1, 2   # uc durumlu etiket maskesi degerleri


def _modul(ad: str):
    spec = importlib.util.spec_from_file_location(ad, OLCUM / f"{ad}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def uc_durum_maske(lbl: Path, h: int, w: int, yan: int | None = None):
    """YOLO etiketi -> tuval (letterbox, 143 ile ayni yerlesim) uzerinde uc durumlu maske:
    0 ETIKETSIZ · 1 sinif 0 (yol) · 2 sinif 1 (engel). Cakismada engel kazanir (guvenli yon)."""
    m143 = _modul("143_etiket_tavani")
    t, e = m143.etiket_maskeleri(lbl, h, w)
    yan = max(h, w) if yan is None else yan
    x0, y0 = (yan - w) // 2, (yan - h) // 2
    uc = np.zeros((yan, yan), np.uint8)
    uc[y0:y0 + h, x0:x0 + w][t > 0] = SINIF0
    uc[y0:y0 + h, x0:x0 + w][e > 0] = SINIF1
    return uc


def rota_yol_olc(wps, uc) -> dict:
    """Rota cizgisi (ardisik waypoint'ler, 1 px polylines) ile uc durumlu etiket kesisimi.
    wps: [[x, y], ...] tuval koordinati. uc: (yan, yan) uint8, degerler ETIKETSIZ/SINIF0/SINIF1.
    Doner: yol_payi (cizgi px'inin sinif 0 payi), etiketsiz_payi, engel_payi, engel_wp
    (sinif 1 ustundeki — ya da tuval DISINDAKI, fail-closed — waypoint sayisi), cizgi_px, wp."""
    h, w = uc.shape[:2]
    cz = np.zeros((h, w), np.uint8)
    pts = np.array([[int(x), int(y)] for x, y in wps], np.int32).reshape(-1, 2)
    if len(pts) >= 2:
        cv2.polylines(cz, [pts], False, 1, 1)
    elif len(pts) == 1 and 0 <= pts[0, 0] < w and 0 <= pts[0, 1] < h:
        cz[pts[0, 1], pts[0, 0]] = 1
    n = int((cz > 0).sum())
    payda = max(1, n)
    engel_wp = 0
    for x, y in pts:
        if not (0 <= x < w and 0 <= y < h) or uc[y, x] == SINIF1:
            engel_wp += 1
    return {"yol_payi": round(float(((cz > 0) & (uc == SINIF0)).sum() / payda), 4),
            "etiketsiz_payi": round(float(((cz > 0) & (uc == ETIKETSIZ)).sum() / payda), 4),
            "engel_payi": round(float(((cz > 0) & (uc == SINIF1)).sum() / payda), 4),
            "engel_wp": int(engel_wp), "cizgi_px": n, "wp": int(len(pts))}


def yanlis_guzergah_mi(olcum: dict, kapi: dict = KAPI_B_EK2) -> bool:
    """ON_KAYIT §11(2): YANLIS GUZERGAH <=> yol_payi < 0,90 VEYA engel_wp > 0."""
    if olcum["yol_payi"] < kapi["yol_payi_min"]:
        return True
    if olcum["engel_wp"] > kapi["engel_wp_maks"]:
        return True
    return False
