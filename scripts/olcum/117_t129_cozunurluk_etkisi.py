"""T129 — CATI KORLUGU COZUNURLUGE BAGLI MI? (kendi bulgum, olcuye ceviriliyor)

GOZLEM (2026-08-21, gorsel): depo kokundeki 6 HAM 1600x900 fotografta
(2026-07-30, videolarla AYNI oturum) DORT MODEL DE — v34 dahil — cati
bolgesini ENGEL boyuyor. Oysa ayni sahnenin 1024x576 VIDEO karelerinde v34
catinin %96'sini ZEMIN sayiyor (D-232/D-237).
Dogruysa "v34 cati kordur" hukmu KOSULLUDUR: kusur buyuk olcude VIDEO
kaynagina (sikistirma/keskinlik) bagli olabilir ve saha kamerasinda
gorunmeyebilir. Bu, bekleyen terfi kararini DOGRUDAN etkiler.

YONTEM (goz degil olcum):
  · Her fotograf icin EN YAKIN video karesi pHash ile bulunur.
  · O karenin T121 dogrulanmis cati maskesi ORB+RANSAC homografisiyle
    fotografa tasinir (99'un fonksiyonlari ITHAL edilir).
  · Tasinan maske GORSEL olarak dogrulanir (D-80) ve dort modelin o bolgede
    ne dedigi olculur.
⚠ SINIR: fotograflar da ayni sahadan ve ayni oturumdandir; olculen sey
"alan-disi genelleme" DEGIL, YALNIZCA "kaynak kalitesi/cozunurluk etkisi".

CIKTI: results/t129/olcum.json · dogrulama.png
"""
from __future__ import annotations

import glob
import importlib.util
import io
import json
import sys
from pathlib import Path

import cv2
import numpy as np

KOK = Path(__file__).resolve().parents[2]
OLCUM = KOK / "scripts" / "olcum"
for p in (KOK / "scripts", KOK / "codes", OLCUM):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from copy_paste_augmentation import zemin_ve_mevcut_engel  # noqa: E402
from ultralytics import YOLO  # noqa: E402

spec = importlib.util.spec_from_file_location(
    "yayilim99", OLCUM / "99_t121_cati_yayilimi.py")
Y99 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(Y99)

KARE_KOK = KOK / "data" / "raw_frames"
CATI_KOK = KOK / "results" / "t121" / "cati_maskeleri"
CIKTI = KOK / "results" / "t129"
CONF = 0.30
RUNS = KOK / "codes" / "runs" / "segment"
MODELLER = [
    ("v30", KOK / "models" / "navitas_seg_v30_best.pt"),
    ("v34_URETIM", KOK / "models" / "navitas_seg_v34_best.pt"),
    ("t121_ft", RUNS / "t121_etiket_ft" / "weights" / "best.pt"),
    ("t122ac", RUNS / "t122ac_daralt_cati" / "weights" / "best.pt"),
]


def phash(gri: np.ndarray) -> np.ndarray:
    g = cv2.resize(gri, (32, 32)).astype(np.float32)
    d = cv2.dct(g)[:8, :8]
    return (d > np.median(d)).flatten()


def main() -> int:
    maskeli = {}
    for mp in sorted(CATI_KOK.glob("*.png")):
        ham = cv2.imread(str(mp), 0)
        m = ((ham[:, :, 0] if ham.ndim == 3 else ham) > 127)
        if m.any():
            video, kare = mp.stem.split("__")
            maskeli[f"{video}/{kare}.jpg"] = m
    kare_hash = {ad: phash(cv2.imread(str(KARE_KOK / ad), cv2.IMREAD_GRAYSCALE))
                 for ad in maskeli}

    fotolar = [f for f in sorted(glob.glob(str(KOK / "*.jpeg")))
               if "2026-07-30" in Path(f).name]
    eslesme, hucreler = [], []
    for f in fotolar:
        img = cv2.imread(f)
        gri = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        h1 = phash(gri)
        mesafe, en_yakin = min((float((h1 != v).mean()), ad)
                               for ad, v in kare_hash.items())
        a_bgr = cv2.imread(str(KARE_KOK / en_yakin))
        H, inlier = Y99.homografi(cv2.cvtColor(a_bgr, cv2.COLOR_BGR2GRAY), gri)
        if H is None or inlier < 40:
            eslesme.append({"foto": Path(f).name, "durum": "HOMOGRAFI_YOK",
                            "en_yakin": en_yakin, "pHash": round(mesafe, 3),
                            "inlier": inlier})
            continue
        cati = cv2.warpPerspective(maskeli[en_yakin].astype(np.uint8), H,
                                   (img.shape[1], img.shape[0]),
                                   flags=cv2.INTER_NEAREST) > 0
        if not cati.any():
            eslesme.append({"foto": Path(f).name, "durum": "MASKE_BOS",
                            "en_yakin": en_yakin, "pHash": round(mesafe, 3)})
            continue
        eslesme.append({"foto": Path(f).name, "durum": "TAMAM",
                        "en_yakin": en_yakin, "pHash": round(mesafe, 3),
                        "inlier": inlier, "cati_pay": round(float(cati.mean()), 4),
                        "_maske": cati, "_img": img})

    gecerli = [e for e in eslesme if e["durum"] == "TAMAM"]
    print(f"foto: {len(fotolar)} · maske tasinabilen: {len(gecerli)}", flush=True)

    sonuc = {}
    for etiket, yol in MODELLER:
        if not yol.is_file():
            continue
        model = YOLO(str(yol), task="segment")
        kacak = []
        for e in gecerli:
            z, _ = zemin_ve_mevcut_engel(model, e["_img"], CONF)
            kacak.append(float((z.astype(bool) & e["_maske"]).sum()
                               / max(1, e["_maske"].sum())))
            if etiket == "v34_URETIM" and len(hucreler) < 4:
                g = e["_img"].copy()
                g[z > 0] = (g[z > 0] * 0.55
                            + np.array([0, 255, 0]) * 0.45).astype(np.uint8)
                g[e["_maske"]] = (g[e["_maske"]] * 0.5
                                  + np.array([255, 0, 255]) * 0.5).astype(np.uint8)
                cv2.putText(g, f"v34 · cati kacak={kacak[-1]:.2f}", (12, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 3)
                hucreler.append(cv2.resize(g, (760, 428)))
        del model
        sonuc[etiket] = {"foto_cati_kacak_ort": round(float(np.mean(kacak)), 4),
                          "foto_cati_kacak_medyan": round(float(np.median(kacak)), 4),
                          "n": len(gecerli)}
        print(etiket, json.dumps(sonuc[etiket], ensure_ascii=False), flush=True)

    CIKTI.mkdir(parents=True, exist_ok=True)
    io.open(CIKTI / "olcum.json", "w", encoding="utf-8").write(json.dumps(
        {"kume": "6 ham 1600x900 foto (2026-07-30, videolarla AYNI oturum)",
         "yer_gercegi": "T121 cati maskeleri, en yakin video karesinden homografi",
         "kiyas_video_kareleri": {"v34": 0.961, "t121_ft": 0.131, "t122ac": 0.020,
                                   "v30": 0.305, "_kaynak": "D-232/D-237, 55 kare"},
         "eslesme": [{k: v for k, v in e.items() if not k.startswith("_")}
                      for e in eslesme],
         "modeller": sonuc}, ensure_ascii=False, indent=1))
    if hucreler:
        while len(hucreler) % 2:
            hucreler.append(np.zeros_like(hucreler[0]))
        satir = [np.hstack(hucreler[i:i + 2]) for i in range(0, len(hucreler), 2)]
        cv2.imwrite(str(CIKTI / "dogrulama.png"), np.vstack(satir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
