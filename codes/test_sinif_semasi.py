"""S2 kapisi: sinif-id cakismasinin GERCEKTEN bittigini kanitla.

NEDEN bu test var: kusur sessizdi. Kod calisiyordu, rota uretiliyordu, hicbir
istisna atilmiyordu -- yalnizca hedef ENGEL sayiliyordu ve IKA hedefe hicbir
zaman ulasamiyordu. Yani "kod kosuyor" bu kusuru yakalamaz; yalnizca DAVRANISI
olcen bir test yakalar.

Kapi olcutu: 3 sinifli bir model ciktisi costmap yoluna verildiginde HEDEF
bolgesi serbest alanda 1 olmali (yani gecilebilir kalmali).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

_BURASI = Path(__file__).resolve().parent
if str(_BURASI) not in sys.path:
    sys.path.insert(0, str(_BURASI))

from costmap_path_finder import serbest_alan
from sinif_semasi import (ALGI_SINIF_IDLERI, COSTMAP_ENGEL_KATMANLARI,
                          COSTMAP_YOL_KATMANLARI, EGITIM_SINIF_ADLARI, ENGEL,
                          HEDEF, KATMAN_ARAC, KATMAN_MOLOZ, KATMAN_ZEMIN,
                          ZEMIN, costmap_katmanlari, dogrula)

GECTI: list[str] = []
DUSTU: list[str] = []


def kontrol(ad: str, kosul: bool, ayrinti: str = "") -> None:
    (GECTI if kosul else DUSTU).append(ad)
    isaret = "OK  " if kosul else "DUSTU"
    print(f"  [{isaret}] {ad}" + (f"  -> {ayrinti}" if ayrinti and not kosul else ""))


def main() -> int:
    print("S2 KAPISI — sinif-id sozlesmesi\n")

    print("1) Ad alanlari ayri mi")
    dogrula()  # cakisirsa AssertionError
    kontrol("HEDEF costmap engel katmanlarinda DEGIL",
            HEDEF not in COSTMAP_ENGEL_KATMANLARI,
            f"HEDEF={HEDEF}, engeller={COSTMAP_ENGEL_KATMANLARI}")
    kontrol("KATMAN_ARAC egitim sinif uzayiyla cakismiyor",
            KATMAN_ARAC not in EGITIM_SINIF_ADLARI,
            f"KATMAN_ARAC={KATMAN_ARAC}, egitim={sorted(EGITIM_SINIF_ADLARI)}")
    kontrol("ENGEL hem egitim sinifi hem costmap moloz katmani (kasitli)",
            ENGEL == KATMAN_MOLOZ)
    kontrol("ZEMIN hem egitim sinifi hem costmap zemin katmani (kasitli)",
            ZEMIN == KATMAN_ZEMIN)

    print("\n2) DAVRANIS: 3 sinifli model ciktisinda hedef gecilebilir kaliyor mu")
    yan = 200
    zemin = np.ones((yan, yan), np.uint8)
    moloz = np.zeros((yan, yan), np.uint8)
    moloz[0:40, :] = 1                       # ust bantta moloz
    hedef_maskesi = np.zeros((yan, yan), np.uint8)
    hedef_maskesi[150:180, 80:120] = 1       # H brandasi
    arac = np.zeros((yan, yan), np.uint8)
    arac[60:80, 20:60] = 1                   # bir arac

    # 3 sinifli model ciktisini taklit et: {0: zemin, 1: moloz, 2: HEDEF}
    model_ciktisi = {ZEMIN: zemin, ENGEL: moloz, HEDEF: hedef_maskesi}

    katmanlar = costmap_katmanlari(model_ciktisi[ZEMIN], model_ciktisi[ENGEL], arac)
    sonuc = serbest_alan(katmanlar, mpp=None,
                         yol_sinif_idler=COSTMAP_YOL_KATMANLARI,
                         engel_sinif_idler=COSTMAP_ENGEL_KATMANLARI)
    serbest = sonuc["serbest"]
    hedefte_serbest = int((serbest & hedef_maskesi).sum())
    hedef_px = int(hedef_maskesi.sum())
    kontrol("hedef bolgesi serbest alanda duruyor",
            hedefte_serbest > 0.5 * hedef_px,
            f"{hedefte_serbest}/{hedef_px} px serbest")
    kontrol("arac engel sayiliyor",
            int((serbest & arac).sum()) == 0,
            f"{int((serbest & arac).sum())} px arac serbest gorunuyor")

    print("\n3) ESKI DAVRANIS gercekten kusurluymus mu (pozitif kontrol)")
    # Eski kod: costmap_maskeleri = {0:.., 1:.., 2: arac} ve engel=(1,2)
    # 3 sinifli model ciktisi verilince 2 = HEDEF olur ve engel sayilir.
    eski_katmanlar = {0: zemin, 1: moloz, 2: model_ciktisi[HEDEF]}
    eski = serbest_alan(eski_katmanlar, mpp=None,
                        yol_sinif_idler=(0,), engel_sinif_idler=(1, 2))
    eski_hedefte = int((eski["serbest"] & hedef_maskesi).sum())
    kontrol("eski semada hedef ENGEL sayiliyordu (kusur dogrulandi)",
            eski_hedefte == 0,
            f"eski semada hedefte {eski_hedefte} px serbest cikti — "
            f"kusur yeniden uretilemedi, test gecersiz")

    print("\n4) Ciplak sayi kalmadi mi (sozlesme kaynagi tek)")
    kontrol("ALGI_SINIF_IDLERI = (ZEMIN, ENGEL)", ALGI_SINIF_IDLERI == (ZEMIN, ENGEL))

    print("\n" + "=" * 62)
    print(f"GECTI: {len(GECTI)}   DUSTU: {len(DUSTU)}")
    if DUSTU:
        print("DUSEN: " + ", ".join(DUSTU))
        return 1
    print("[OK] S2 KAPISI GECTI")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
