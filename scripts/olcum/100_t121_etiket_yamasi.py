"""T121 adim 4 — ETIKET YAMASI: copy_paste_gercek -> copy_paste_t121.

MIMAR TASARIMI (D-211 §4 / T121 emri): catili karelerde cati bolgesi SINIF 1
etiketlenir ve tam-kare zemin poligonu O BOLGEDEN CIKARILIR. GORSELLER AYNEN
KOPYALANIR (yeni veri yok, yalniz etiket duzeldi). Diger etiket satirlari
(molozlar, DOTA araclari) OLDUGU GIBI korunur.

YONTEM:
  zemin_maskesi = tam_kare − cati_maskesi (results/t121/cati_maskeleri/,
  56 kaynak; D-80 ile iki turda gorsel dogrulanip kilitlendi).
  IC DELIK sorunu: YOLO poligonu delik desteklemez; kadraj icinde kalan cati
  bilesenleri icin zemin maskesine 2 px'lik dikey DIKIS acilir (bilesenin
  tepe noktasindan y=0'a) — delik dis sinira baglanir, kontur tek parca olur.
  Dikisin bedeli: kare basina ~2x400 px etiketsiz serit (~%0,07) — ihmal.
  Poligonlastirma: uretecin KENDI `poligon_satirlari`i, min_alan=16.0
  (uretec CLI varsayilani `--min-poligon-alan`).

DENETIM (her dosyada, yazmadan once):
  1. catinin zemin-talebi: raster(zemin) ∩ cati / cati  < 0.02
  2. zemin sadakati: IoU(raster(zemin), tam_kare−cati) > 0.97
  3. cati kapsami: raster(engel) ∩ cati / cati > 0.95
Ihlal varsa dosya YAZILMAZ ve rapora duser.

CIKTI: dataset/copy_paste_t121/ + dataset/karisim_t121.yaml +
       results/t121/etiket_yamasi_ozet.json
"""
from __future__ import annotations

import io
import json
import shutil
import sys
from pathlib import Path

import cv2
import numpy as np

KOK = Path(__file__).resolve().parents[2]
for p in (KOK / "scripts",):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from copy_paste_augmentation import poligon_satirlari, yolo_sinif_maskesi  # noqa: E402

ESKI = KOK / "dataset" / "copy_paste_gercek"
YENI = KOK / "dataset" / "copy_paste_t121"
MASKELER = KOK / "results" / "t121" / "cati_maskeleri"
OZET = KOK / "results" / "t121" / "etiket_yamasi_ozet.json"
MIN_ALAN = 16.0
TAM_KARE_ONEKI = "0 0.000000 0.000000 1.000000"
ZEMIN, ENGEL = 0, 1


def dikisli_zemin(cati: np.ndarray) -> np.ndarray:
    """tam_kare − cati; ic bilesenler icin y=0'a 2px dikis ac."""
    h, w = cati.shape
    zemin = (cati == 0).astype(np.uint8)
    konturlar, _ = cv2.findContours((cati > 0).astype(np.uint8),
                                    cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for k in konturlar:
        x0, y0, kw, kh = cv2.boundingRect(k)
        kenara_deger = x0 == 0 or y0 == 0 or x0 + kw >= w or y0 + kh >= h
        if not kenara_deger:
            tepe = k[k[:, 0, 1].argmin(), 0]
            x = int(np.clip(tepe[0], 1, w - 2))
            zemin[0:int(tepe[1]) + 1, x - 1:x + 1] = 0
    return zemin


def main() -> int:
    manifest = json.load(io.open(ESKI / "manifest.json", encoding="utf-8"))
    esleme = {o["cikti"]: o["kaynak"] for o in manifest["ornekler"] if o.get("cikti")}

    if YENI.exists():
        shutil.rmtree(YENI)
    for bolum in ("train", "val"):
        (YENI / "images" / bolum).mkdir(parents=True)
        (YENI / "labels" / bolum).mkdir(parents=True)

    kayitlar, ihlaller = [], []
    for cikti, kaynak in sorted(esleme.items()):
        img_eski = ESKI / cikti
        etiket_eski = ESKI / cikti.replace("images/", "labels/").replace(".jpg", ".txt")
        maske_yolu = MASKELER / (kaynak.replace("/", "__").replace(".jpg", "") + ".png")
        ham = cv2.imread(str(maske_yolu), 0)
        if ham is None:
            print(f"MASKE OKUNAMADI: {maske_yolu}", file=sys.stderr)
            return 5
        if ham.ndim == 3:
            # ultralytics import edilince cv2.imread yamali (H,W,1) donduruyor
            ham = ham[:, :, 0]
        cati = (ham > 127).astype(np.uint8)
        h, w = cati.shape

        metin = io.open(etiket_eski, encoding="utf-8").read()
        satirlar = metin.splitlines()
        if not satirlar[0].startswith(TAM_KARE_ONEKI):
            ihlaller.append({"cikti": cikti, "sebep": "ilk satir tam-kare degil"})
            continue
        kalan = satirlar[1:]

        if int(cati.sum()) == 0:
            yeni_metin = metin                      # cati kadraj disi: degisiklik yok
            kontrol = {"cati_pay": 0.0}
        else:
            # Zemin, GENISLETILMIS catidan cikarilir (5x5): poligon sadelesmesi
            # (approxPolyDP) sinirda ~%2 bindirme uretiyordu — tampon bunu sifira
            # ceker; cati poligonu ORIJINAL maskeden yazilir, 2 px'lik etiketsiz
            # halka (~kare paydasinin <%2'si) kabul edilen bedeldir.
            genis = cv2.dilate(cati, np.ones((5, 5), np.uint8))
            zemin = dikisli_zemin(genis)
            z_satir = poligon_satirlari(ZEMIN, zemin, MIN_ALAN)
            c_satir = poligon_satirlari(ENGEL, cati, MIN_ALAN)
            yeni_metin = "\n".join(z_satir + kalan + c_satir) + "\n"

            z_r = yolo_sinif_maskesi(yeni_metin, (h, w), ZEMIN)
            e_r = yolo_sinif_maskesi(yeni_metin, (h, w), ENGEL)
            c = cati.astype(bool)
            talep = float((z_r.astype(bool) & c).sum() / max(1, c.sum()))
            hedef_zemin = (~c)
            iou = float((z_r.astype(bool) & hedef_zemin).sum()
                        / max(1, (z_r.astype(bool) | hedef_zemin).sum()))
            kapsam = float((e_r.astype(bool) & c).sum() / max(1, c.sum()))
            kontrol = {"cati_pay": round(float(cati.mean()), 4),
                       "cati_zemin_talebi": round(talep, 4),
                       "zemin_iou": round(iou, 4),
                       "cati_engel_kapsami": round(kapsam, 4)}
            if talep >= 0.02 or iou <= 0.97 or kapsam <= 0.95:
                ihlaller.append({"cikti": cikti, **kontrol})
                continue

        shutil.copy2(img_eski, YENI / cikti)
        hedef_txt = YENI / cikti.replace("images/", "labels/").replace(".jpg", ".txt")
        io.open(hedef_txt, "w", encoding="utf-8", newline="\n").write(yeni_metin)
        kayitlar.append({"cikti": cikti, "kaynak": kaynak, **kontrol})

    shutil.copy2(ESKI / "data.yaml", YENI / "data.yaml")

    # karisim: copy_paste_gercek -> copy_paste_t121 (diger bilesenler AYNEN)
    kaynak_yaml = io.open(KOK / "dataset" / "karisim_t54_engelli.yaml",
                          encoding="utf-8").read()
    io.open(KOK / "dataset" / "karisim_t121.yaml", "w", encoding="utf-8",
            newline="\n").write(
        "# T121 belirleyici kosum: copy_paste_gercek yerine ETIKETI YAMALI\n"
        "# copy_paste_t121 (cati -> sinif 1; tam-kare zemin catidan cikarildi).\n"
        "# Kaynak: karisim_t54_engelli.yaml — diger iki bilesen AYNEN.\n"
        + kaynak_yaml.replace("copy_paste_gercek", "copy_paste_t121"))

    n_degisen = sum(1 for k in kayitlar if k.get("cati_pay", 0) > 0)
    ozet = {
        "yazilan": len(kayitlar), "ihlal": len(ihlaller),
        "etiketi_degisen": n_degisen,
        "degismeyen_cati_disi": len(kayitlar) - n_degisen,
        "ort_cati_pay": round(float(np.mean([k["cati_pay"] for k in kayitlar])), 4),
        "en_kotu_zemin_iou": min((k.get("zemin_iou", 1.0) for k in kayitlar), default=None),
        "en_kotu_kapsam": min((k.get("cati_engel_kapsami", 1.0) for k in kayitlar), default=None),
        "ihlaller": ihlaller, "kayitlar": kayitlar,
    }
    OZET.parent.mkdir(parents=True, exist_ok=True)
    io.open(OZET, "w", encoding="utf-8").write(json.dumps(ozet, ensure_ascii=False, indent=1))
    print(json.dumps({k: v for k, v in ozet.items()
                      if k not in ("kayitlar", "ihlaller")}, ensure_ascii=False, indent=1))
    print("ihlal ornekleri:", json.dumps(ihlaller[:3], ensure_ascii=False))
    return 0 if not ihlaller else 4


if __name__ == "__main__":
    raise SystemExit(main())
