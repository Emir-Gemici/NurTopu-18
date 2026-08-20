"""T121 adim 3d — KARISIM KUTLE TABLOSU: celiski kutlesi vs gercek-doku denetimi.

SORU (mimar emri, secenek d): karisim oranini degistirmek CELISKIYI mi azaltir
yoksa yalnizca GERCEK-DOKU denetimini mi? Cevap icin uc bilesenin piksel
kutleleri sayilir (karisim_t54_engelli.yaml uyeleri):

  rescuenet_2sinif_engelli : "cati/bina -> engel" dersinin kaynagi
  sentetik_arena           : arena geometrisi (yer gercegi kusursuz)
  copy_paste_gercek        : gercek doku + TAM-KARE zemin celiskisi (D-210)

Kutle = dosya_sayisi x ortalama sinif payi (256x144 rasterle, orneklem
n<=400/dosya kumesi; orneklem tohumu sabit — tekrarlanabilir).
CIKTI: results/t121/karisim_kutlesi.json
"""
from __future__ import annotations

import io
import json
import random
import sys
from pathlib import Path

import numpy as np

KOK = Path(__file__).resolve().parents[2]
for p in (KOK / "scripts",):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from copy_paste_augmentation import yolo_sinif_maskesi  # noqa: E402

W, H = 256, 144
ORNEKLEM = 400
TOHUM = 20260820
KUMELER = ["rescuenet_2sinif_engelli", "sentetik_arena", "copy_paste_gercek"]
CIKTI = KOK / "results" / "t121" / "karisim_kutlesi.json"


def kume_olc(ad: str) -> dict:
    etiketler = sorted((KOK / "dataset" / ad).glob("labels/*/*.txt"))
    n = len(etiketler)
    secim = etiketler
    if n > ORNEKLEM:
        secim = random.Random(TOHUM).sample(etiketler, ORNEKLEM)
    z_pay, e_pay = [], []
    for p in secim:
        metin = io.open(p, encoding="utf-8").read()
        z_pay.append(float(yolo_sinif_maskesi(metin, (H, W), 0).mean()))
        e_pay.append(float(yolo_sinif_maskesi(metin, (H, W), 1).mean()))
    z, e = float(np.mean(z_pay)), float(np.mean(e_pay))
    return {"dosya": n, "orneklem": len(secim),
            "ort_zemin_payi": round(z, 4), "ort_engel_payi": round(e, 4),
            "zemin_kutlesi": round(n * z, 1), "engel_kutlesi": round(n * e, 1)}


def main() -> int:
    sonuc = {"tohum": TOHUM, "raster": [W, H], "kumeler": {}}
    for ad in KUMELER:
        sonuc["kumeler"][ad] = kume_olc(ad)
        print(ad, json.dumps(sonuc["kumeler"][ad], ensure_ascii=False))
    r = sonuc["kumeler"]
    # Celiski kutlesi: copy_paste'in ZEMIN kutlesi icinde catinin payi bilinmiyor
    # (elle etiket adim 4'te); v30 vekili etiket_istatistigi.json'da. Burada
    # kaba sinir: copy_paste zemin kutlesi vs rescuenet engel kutlesi.
    sonuc["oran_notu"] = {
        "copy_paste_zemin_kutlesi": r["copy_paste_gercek"]["zemin_kutlesi"],
        "rescuenet_engel_kutlesi": r["rescuenet_2sinif_engelli"]["engel_kutlesi"],
        "yorum": "(d) karisim orani dususu copy_paste'in HEM celiskili zemin "
                 "kutlesini HEM gercek-doku denetimini AYNI carpanla azaltir "
                 "— secici degildir. Sayisal karsiligi bu iki kutledir.",
    }
    CIKTI.parent.mkdir(parents=True, exist_ok=True)
    io.open(CIKTI, "w", encoding="utf-8").write(
        json.dumps(sonuc, ensure_ascii=False, indent=1))
    print(f"yazildi: {CIKTI}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
