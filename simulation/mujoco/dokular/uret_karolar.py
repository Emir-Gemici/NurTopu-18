"""Doku kaynakları — GERÇEK eğitim karelerinden kırpılmış PNG'ler.

Amaç: MuJoCo arenasında zemin / yol / moloz yüzeyleri, üretim segmentasyon
modelinin (v36) eğitimde gördüğü türden GERÇEK fotoğraf dokusu taşısın; düz
renkli kutu (world_generator.py'nin SDF'i) değil.

İki tür çıktı:
  *_kaynak.png : kaynak kareden kesilmiş GENİŞ bölge (zemin/yol). `arena_mjcf`
                 bu bölgeden rastgele (deterministik) yamalar alıp yumuşak geçişle
                 birleştirerek tekrarsız HTAB dokusu kurar (ayna/kaleydoskop yok).
  moloz_*.png  : kare karo, 2×2 aynalı döşenmiş (MuJoCo cube dokusu kare ister).
  bariyer.png  : kırmızı-beyaz şerit — PROSEDÜREL (fotoğraf değil).

Kaynaklar ve piksel kutuları `KAYNAK.md`'de; bu betik o tabloyu yeniden üretir
(kaynak diskte varsa). Çıktılar depoya işlenmiştir.

Kullanım:
  O:/navitas-local-train/venv/Scripts/python.exe simulation/mujoco/dokular/uret_karolar.py
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import cv2
import numpy as np

for _akim in (sys.stdout, sys.stderr):
    try:
        _akim.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

BURASI = Path(__file__).resolve().parent
KARO_PX = 256   # moloz karosu: kırpma bu kenara ölçeklenir, 2×2 aynalı → 512² (depo boyutu)

# ad → (kaynak dosya, (x0, y0, x1, y1), tür, açıklama)
# Kaynak yolları eğitim ağacındaki GERÇEK karelerdir (dataset/ git dışı; O:/navitas altında).
KAYNAKLAR = {
    "toprak_kaynak": (
        "dataset/dji_kirsal/images/train/dji_20260822170832_0037_d__frame_000170_000006630.jpg",
        (2900, 100, 3800, 1900), "bolge",
        "kumlu toprak/stabilize zemin (tekerlek izli), DJI 0037 kırsal eğitim karesi, nadir"),
    "stabilize_kaynak": (
        "dataset/dji_kirsal/images/train/dji_20260822170832_0037_d__frame_000003_000000090.jpg",
        (60, 250, 560, 1150), "bolge",
        "gri çakıl/stabilize yol yüzeyi, DJI 0037 kırsal eğitim karesi, nadir"),
    "asfalt_kaynak": (
        "data/raw_frames/whatsapp_video_2026_07_30_at_11_44_03/frame_000000_000000000.jpg",
        (700, 240, 1000, 330), "bolge",
        "asfalt otopark zemini, gerçek nadir drone karesi (gercek_otopark eğitim kaynağı) — TEŞHİS varyantı"),
    "moloz_a": (
        "dataset/rescuenet_11sinif/images/train/12275.jpg",
        (430, 150, 730, 400), "karo",
        "yoğun kırık enkaz (gri-kahve), RescueNet eğitim karesi"),
    "moloz_b": (
        "dataset/rescuenet_11sinif/images/train/11237.jpg",
        (10, 370, 310, 670), "karo",
        "ahşap/beton kırık enkaz, RescueNet eğitim karesi"),
}


def _aynali_dose(karo: np.ndarray) -> np.ndarray:
    ust = np.hstack([karo, karo[:, ::-1]])
    return np.vstack([ust, ust[::-1, :]])


def _kaynak_yolu(kaynak: str, depo_kok: Path) -> Path | None:
    for kok in (depo_kok, Path("O:/navitas")):
        p = kok / kaynak
        if p.is_file():
            return p
    return None


def uret(ad: str, depo_kok: Path) -> Path | None:
    kaynak, (x0, y0, x1, y1), tur, _ = KAYNAKLAR[ad]
    yol = _kaynak_yolu(kaynak, depo_kok)
    if yol is None:
        print(f"[karo] {ad}: kaynak yok: {kaynak}")
        return None
    im = cv2.imread(str(yol))
    kes = im[y0:y1, x0:x1]
    dosya = BURASI / f"{ad}.png"
    if tur == "karo":
        kes = cv2.resize(kes, (KARO_PX, KARO_PX), interpolation=cv2.INTER_AREA)
        cv2.imwrite(str(dosya), _aynali_dose(kes))
    else:
        cv2.imwrite(str(dosya), kes)
    return dosya


def bariyer_uret() -> Path:
    im = np.full((256, 256, 3), 235, np.uint8)     # kare: MuJoCo cube dokusu şartı
    for k in range(0, 256, 64):
        im[:, k:k + 32] = (30, 30, 210)     # BGR kırmızı
    dosya = BURASI / "bariyer.png"
    cv2.imwrite(str(dosya), im)
    return dosya


def main():
    depo = BURASI.parents[2]
    print(f"[karo] depo kökü: {depo}")
    for ad in KAYNAKLAR:
        d = uret(ad, depo)
        if d is not None:
            sha = hashlib.sha256(d.read_bytes()).hexdigest()[:12]
            h, w = cv2.imread(str(d)).shape[:2]
            print(f"[karo] {ad}: {d.name} {w}×{h} sha256={sha}")
    b = bariyer_uret()
    print(f"[karo] bariyer: {b.name} (prosedürel)")


if __name__ == "__main__":
    main()
