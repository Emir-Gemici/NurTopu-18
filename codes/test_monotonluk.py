"""MONOTONLUK KAPISI — mimarinin tek degismezi (CLAUDE.md madde 15).

Sozlesme: "Serbest alan OTORITEDIR; nesne katmani yalniz CIKARIR."
Formel:   serbest(K1 ^ !K2)  alt kumesi  serbest(K1)

Yani Katman-2'ye eklenen HER yeni engel kaynagi sistemi ancak daha GUVENLI
yapabilir; serbest alani BUYUTEMEZ.

NEDEN bu test var: bu iddia bugune kadar hicbir testle sinanmadi (TASK_QUEUE S3).
`serbest_alan()` icinde cikarmadan SONRA bir `dilate` / `MORPH_CLOSE` /
`bitwise_or` eklense, kod calismaya devam eder, hicbir istisna atilmaz ve
serbest alan sessizce buyur. Boyle bir regresyon yalnizca DAVRANIS olcen bir
testle yakalanir.

S1/S2 dogrulamasinin bir parcasi olarak da kosulur: arac katmani eklemek
serbest alani kucultuyor mu, buyutuyor mu?
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

_BURASI = Path(__file__).resolve().parent
if str(_BURASI) not in sys.path:
    sys.path.insert(0, str(_BURASI))

from costmap_path_finder import serbest_alan
from sinif_semasi import (COSTMAP_ENGEL_KATMANLARI, COSTMAP_YOL_KATMANLARI,
                          KATMAN_ARAC, KATMAN_MOLOZ, KATMAN_ZEMIN)

GECTI: list[str] = []
DUSTU: list[str] = []


def kontrol(ad: str, kosul: bool, ayrinti: str = "") -> None:
    (GECTI if kosul else DUSTU).append(ad)
    print(f"  [{'OK  ' if kosul else 'DUSTU'}] {ad}" + (f"  -> {ayrinti}" if ayrinti else ""))


def sahne(tohum: int, yan: int = 240):
    """Tekrarlanabilir sentetik sahne: zemin + moloz + arac."""
    rng = np.random.default_rng(tohum)
    zemin = np.zeros((yan, yan), np.uint8)
    zemin[20:yan - 20, 20:yan - 20] = 1

    moloz = np.zeros((yan, yan), np.uint8)
    for _ in range(4):
        x, y = rng.integers(30, yan - 60, size=2)
        w, h = rng.integers(18, 45, size=2)
        moloz[y:y + h, x:x + w] = 1

    arac = np.zeros((yan, yan), np.uint8)
    for _ in range(3):
        x, y = rng.integers(30, yan - 50, size=2)
        w, h = rng.integers(12, 30, size=2)
        arac[y:y + h, x:x + w] = 1
    return zemin, moloz, arac


def alan(maskeler, engeller) -> np.ndarray:
    return serbest_alan(maskeler, mpp=None,
                        yol_sinif_idler=COSTMAP_YOL_KATMANLARI,
                        engel_sinif_idler=engeller)["serbest"].astype(bool)


def main() -> int:
    print("MONOTONLUK KAPISI — serbest(K1 ^ !K2) alt kumesi serbest(K1)\n")

    print("1) Arac katmani eklemek serbest alani BUYUTMUYOR (10 tohum)")
    ihlal = 0
    kucultme_var = 0
    for tohum in range(10):
        zemin, moloz, arac = sahne(tohum)
        # K1: yalniz moloz engel
        s1 = alan({KATMAN_ZEMIN: zemin, KATMAN_MOLOZ: moloz}, (KATMAN_MOLOZ,))
        # K1 ^ !K2: moloz + arac engel
        s2 = alan({KATMAN_ZEMIN: zemin, KATMAN_MOLOZ: moloz, KATMAN_ARAC: arac},
                  COSTMAP_ENGEL_KATMANLARI)
        # alt kume mi: s2 icinde olup s1 disinda kalan piksel OLMAMALI
        disari = int((s2 & ~s1).sum())
        if disari:
            ihlal += 1
            print(f"     tohum {tohum}: {disari} px s1 disinda — IHLAL")
        if int(s1.sum()) > int(s2.sum()):
            kucultme_var += 1
    kontrol("hicbir tohumda serbest alan buyumedi", ihlal == 0,
            f"{ihlal}/10 tohumda ihlal")
    kontrol("arac katmani gercekten CIKARIYOR (bos islem degil)", kucultme_var >= 8,
            f"{kucultme_var}/10 tohumda kuculme olctu")

    print("\n2) Bos arac katmani serbest alani DEGISTIRMIYOR")
    zemin, moloz, _ = sahne(42)
    bos = np.zeros_like(moloz)
    s_yok = alan({KATMAN_ZEMIN: zemin, KATMAN_MOLOZ: moloz}, (KATMAN_MOLOZ,))
    s_bos = alan({KATMAN_ZEMIN: zemin, KATMAN_MOLOZ: moloz, KATMAN_ARAC: bos},
                 COSTMAP_ENGEL_KATMANLARI)
    kontrol("bos katman serbest alani aynen birakiyor",
            int((s_yok ^ s_bos).sum()) == 0,
            f"{int((s_yok ^ s_bos).sum())} px fark")

    print("\n3) Eksik katman sessizce atlanip serbest alani BUYUTMUYOR")
    # Arac katmani sozlukte HIC yok ama engel listesinde adi geciyor.
    s_eksik = alan({KATMAN_ZEMIN: zemin, KATMAN_MOLOZ: moloz}, COSTMAP_ENGEL_KATMANLARI)
    kontrol("eksik katman = katmansiz hal (buyume yok)",
            int((s_eksik & ~s_yok).sum()) == 0,
            f"{int((s_eksik & ~s_yok).sum())} px fazladan serbest")

    print("\n4) Cikarma SON islem mi — sonrasinda genisletme var mi")
    # Davranis testi: engel alanina denk gelen hicbir piksel serbest olamaz.
    zemin, moloz, arac = sahne(7)
    s = alan({KATMAN_ZEMIN: zemin, KATMAN_MOLOZ: moloz, KATMAN_ARAC: arac},
             COSTMAP_ENGEL_KATMANLARI)
    engel_birlesim = (moloz | arac).astype(bool)
    sizinti = int((s & engel_birlesim).sum())
    kontrol("hicbir engel pikseli serbest degil", sizinti == 0,
            f"{sizinti} px engel uzerinde serbest")

    print("\n" + "=" * 64)
    print(f"GECTI: {len(GECTI)}   DUSTU: {len(DUSTU)}")
    if DUSTU:
        print("DUSEN: " + ", ".join(DUSTU))
        return 1
    print("[OK] MONOTONLUK KAPISI GECTI")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
