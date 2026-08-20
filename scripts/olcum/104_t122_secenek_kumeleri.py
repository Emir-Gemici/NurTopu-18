"""T122 — SECENEK (a) ve (a)+(c) icin ETIKET KUMELERI uret.

ON KAYIT: results/t122_on_kayit.md (D-107; egitimlerden ONCE yazildi).

(a) DARALT     : zemin = aday_v5c(conf 0,05) zemin maskesi. Uretecin KENDI
                 kahini ve KENDI conf'u (dataset/copy_paste_gercek/
                 manifest.json: zemin_model, zemin_conf) — yeni bir kahin
                 SECILMEDI, mevcut olan KULLANILDI (D-218: v5c catiyi zaten
                 zemin saymiyor, 0,115).
(a)+(c) DARALT+CATI : zemin = v5c zemin MINUS cati · engel += cati
                 (cati maskeleri T121'in elle+homografi urunu, uc gorsel
                 dogrulama turundan gecti: results/t121/cati_maskeleri/).

ORTAK: gorseller AYNEN kopyalanir (yeni veri YOK), engel/hedef satirlari
KORUNUR, tam-kare zemin satiri KALDIRILIR. 100_t121_etiket_yamasi.py'nin
denetim kalibi aynen uygulanir (dosya basina oran denetimi; ihlal -> YAZILMAZ).

CIKTI: dataset/copy_paste_t122a/ · dataset/copy_paste_t122ac/
       dataset/karisim_t122a.yaml · dataset/karisim_t122ac.yaml
       results/t122/kume_ozeti_<kip>.json
"""
from __future__ import annotations

import argparse
import io
import json
import shutil
import sys
from pathlib import Path

import cv2
import numpy as np

KOK = Path(__file__).resolve().parents[2]
for p in (KOK / "scripts", KOK / "codes"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from copy_paste_augmentation import (poligon_satirlari,  # noqa: E402
                                     yolo_sinif_maskesi,
                                     zemin_ve_mevcut_engel)
from ultralytics import YOLO  # noqa: E402

ESKI = KOK / "dataset" / "copy_paste_gercek"
CATI_MASKELERI = KOK / "results" / "t121" / "cati_maskeleri"
KARE_KOKU = KOK / "data" / "raw_frames"
CIKTI_KOK = KOK / "results" / "t122"
MIN_ALAN = 16.0                 # uretec CLI varsayilani (--min-poligon-alan)
TAM_KARE_ONEKI = "0 0.000000 0.000000 1.000000"
ZEMIN, ENGEL = 0, 1
MORF = 5                        # T121'deki tampon (poligon sadelesmesi payi)


def gri_oku(yol: Path) -> np.ndarray:
    """ultralytics import edilince cv2.imread gri okumada (H,W,1) donuyor."""
    ham = cv2.imread(str(yol), 0)
    if ham is None:
        raise OSError(f"maske okunamadi: {yol}")
    return ham[:, :, 0] if ham.ndim == 3 else ham


def dikisli(maske: np.ndarray, delikler: np.ndarray) -> np.ndarray:
    """`maske` icindeki KAPALI delikleri 2px dikisle disa bagla (YOLO deliksiz)."""
    h, w = maske.shape
    sonuc = maske.copy()
    konturlar, _ = cv2.findContours((delikler > 0).astype(np.uint8),
                                    cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for k in konturlar:
        x0, y0, kw, kh = cv2.boundingRect(k)
        if x0 == 0 or y0 == 0 or x0 + kw >= w or y0 + kh >= h:
            continue
        tepe = k[k[:, 0, 1].argmin(), 0]
        x = int(np.clip(tepe[0], 1, w - 2))
        sonuc[0:int(tepe[1]) + 1, x - 1:x + 1] = 0
    return sonuc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kip", choices=("a", "ac"), required=True)
    args = ap.parse_args()
    kip = args.kip
    yeni = KOK / "dataset" / f"copy_paste_t122{kip}"

    manifest = json.load(io.open(ESKI / "manifest.json", encoding="utf-8"))
    par = manifest["parametreler"]
    zemin_model_yolu = KOK / par["zemin_model"]
    zemin_conf = float(par["zemin_conf"])
    print(f"[{kip}] kahin: {zemin_model_yolu.name} conf={zemin_conf} "
          "(manifest'ten, secilmedi)", flush=True)
    esleme = {o["cikti"]: o["kaynak"] for o in manifest["ornekler"] if o.get("cikti")}

    model = YOLO(str(zemin_model_yolu), task="segment")
    kaynak_zemin: dict[str, np.ndarray] = {}
    for kaynak in sorted(set(esleme.values())):
        bgr = cv2.imread(str(KARE_KOKU / kaynak))
        z, _ = zemin_ve_mevcut_engel(model, bgr, zemin_conf)
        kaynak_zemin[kaynak] = (z > 0).astype(np.uint8)
    del model

    if yeni.exists():
        shutil.rmtree(yeni)
    for bolum in ("train", "val"):
        (yeni / "images" / bolum).mkdir(parents=True)
        (yeni / "labels" / bolum).mkdir(parents=True)

    kayitlar, ihlaller = [], []
    for cikti, kaynak in sorted(esleme.items()):
        etiket_eski = ESKI / cikti.replace("images/", "labels/").replace(".jpg", ".txt")
        metin = io.open(etiket_eski, encoding="utf-8").read()
        satirlar = metin.splitlines()
        if not satirlar[0].startswith(TAM_KARE_ONEKI):
            ihlaller.append({"cikti": cikti, "sebep": "ilk satir tam-kare degil"})
            continue
        kalan = satirlar[1:]

        z5c = kaynak_zemin[kaynak]
        h, w = z5c.shape
        cati = (gri_oku(CATI_MASKELERI /
                        (kaynak.replace("/", "__").replace(".jpg", "") + ".png")) > 127
                ).astype(np.uint8)

        if kip == "a":
            zemin = z5c.copy()
            cati_satir = []
        else:
            genis = cv2.dilate(cati, np.ones((MORF, MORF), np.uint8))
            zemin = (z5c.astype(bool) & ~genis.astype(bool)).astype(np.uint8)
            cati_satir = poligon_satirlari(ENGEL, cati, MIN_ALAN)
        zemin = dikisli(zemin, (1 - zemin))
        z_satir = poligon_satirlari(ZEMIN, zemin, MIN_ALAN)
        if not z_satir:
            ihlaller.append({"cikti": cikti, "sebep": "zemin poligonu URETILEMEDI"})
            continue
        yeni_metin = "\n".join(z_satir + kalan + cati_satir) + "\n"

        # Denetim: rasterize edilen zemin, hedeflenen zemine sadik mi; ve
        # (ac) kipinde cati zemin TALEP ETMIYOR mu?
        z_r = yolo_sinif_maskesi(yeni_metin, (h, w), ZEMIN).astype(bool)
        hedef = zemin.astype(bool)
        iou = float((z_r & hedef).sum() / max(1, (z_r | hedef).sum()))
        talep = (float((z_r & cati.astype(bool)).sum() / max(1, cati.sum()))
                 if cati.sum() else 0.0)
        kontrol = {"zemin_pay": round(float(zemin.mean()), 4),
                   "zemin_iou": round(iou, 4),
                   "cati_zemin_talebi": round(talep, 4)}
        if iou <= 0.90 or (kip == "ac" and talep >= 0.02):
            ihlaller.append({"cikti": cikti, **kontrol})
            continue

        shutil.copy2(ESKI / cikti, yeni / cikti)
        io.open(yeni / cikti.replace("images/", "labels/").replace(".jpg", ".txt"),
                "w", encoding="utf-8", newline="\n").write(yeni_metin)
        kayitlar.append({"cikti": cikti, "kaynak": kaynak, **kontrol})

    shutil.copy2(ESKI / "data.yaml", yeni / "data.yaml")
    kaynak_yaml = io.open(KOK / "dataset" / "karisim_t54_engelli.yaml",
                          encoding="utf-8").read()
    io.open(KOK / "dataset" / f"karisim_t122{kip}.yaml", "w", encoding="utf-8",
            newline="\n").write(
        f"# T122 secenek {'(a) DARALT' if kip == 'a' else '(a)+(c) DARALT+CATI'}\n"
        "# copy_paste_gercek -> copy_paste_t122" + kip + " (yalniz ETIKET degisti).\n"
        "# Kaynak: karisim_t54_engelli.yaml — diger iki bilesen AYNEN.\n"
        + kaynak_yaml.replace("copy_paste_gercek", f"copy_paste_t122{kip}"))

    ozet = {"kip": kip, "kahin": str(zemin_model_yolu), "zemin_conf": zemin_conf,
            "yazilan": len(kayitlar), "ihlal": len(ihlaller),
            "ort_zemin_pay": round(float(np.mean([k["zemin_pay"] for k in kayitlar])), 4)
            if kayitlar else None,
            "en_kotu_zemin_iou": min((k["zemin_iou"] for k in kayitlar), default=None),
            "ihlaller": ihlaller[:20], "kayitlar": kayitlar}
    CIKTI_KOK.mkdir(parents=True, exist_ok=True)
    io.open(CIKTI_KOK / f"kume_ozeti_{kip}.json", "w", encoding="utf-8").write(
        json.dumps(ozet, ensure_ascii=False, indent=1))
    print(json.dumps({k: v for k, v in ozet.items()
                      if k not in ("kayitlar", "ihlaller")}, ensure_ascii=False,
                     indent=1))
    return 0 if not ihlaller else 4


if __name__ == "__main__":
    raise SystemExit(main())
