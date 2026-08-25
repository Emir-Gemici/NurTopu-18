"""EKSIK BANT TANISI — hangi karede bant TAMAMLAMASI ISE YARAR?

🔴 NEDEN (D-281 §5): refuterlar olctu ki elle cizilen maskelerin medyan %38'i
ETIKETSIZ ve bant testi ETIKETSIZ'i sessizce "zemin degil" sayiyor. YAPISAL
grubunda etiketsiz orani p50 0,543, GECER'de 0,344 — yani "yapisal" hukmu
ETIKET SEYREKLIGIYLE BIRLIKTE ARTIYOR. Iki karede basarisiz bandin %100'u
etiketsizdi.

Bu betik, bant tamamlamanin NEREDE ISE YARAYACAGINI ONCEDEN ayirir:

  KURTARILABILIR : basarisiz bandin cogu ETIKETSIZ -> insan/amele oraya bakip
                   sinif verirse kare GECER'e donebilir
  ENGEL          : basarisiz bandin cogu SINIF1 -> orasi gercekten gecilemez,
                   etiketleme DEGISTIRMEZ
  ZATEN_YETER    : bant zaten yeterli temasa sahip (baska sebeple red)

⚠ "Kurtarilabilir" bir TAHMINDIR, garanti degil: amele oraya bakip SINIF1
  veya yine ETIKETSIZ diyebilir (D-210: emin degilsen isaretleme). Bu yuzden
  ayrica UST SINIR hesaplanir: bandin etiketsiz kismi TAMAMEN sinif 0 olsaydi
  kac kare gecerdi.

CIKTI: results/dji_kirsal/bant_bosluk.json + is listesi
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import numpy as np

KOK = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(KOK / "codes"))

from karar_sozlesmesi import bant_temasi_gereken_px  # noqa: E402
from rpi_inference import _preprocess, hedef_bant_yuksekligi  # noqa: E402

MASKE_KOK = KOK / "results" / "dji_20260822" / "f5_olcek"
KARE_KOK = KOK / "results" / "dji_20260822" / "kareler_1fps"
CIKTI = KOK / "results" / "dji_kirsal" / "bant_bosluk.json"

ETIKETSIZ, SINIF0, SINIF1 = 0, 1, 2


def bant_dilimi(m, icerik, taraf):
    x0, y0, w, h = icerik
    bh = hedef_bant_yuksekligi(h)
    if taraf == "ust":
        return m[y0:y0 + bh, x0:x0 + w]
    return m[y0 + h - bh:y0 + h, x0:x0 + w]


def temas(msk_ikili, icerik, taraf):
    b = bant_dilimi(msk_ikili, icerik, taraf)
    return 0 if b.size == 0 else int(b.any(axis=0).sum())


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    maskeler = {p.name[:-len("_uc.png")]: p
                for g in "ABCD" for p in (MASKE_KOK / g).glob("*_uc.png")}
    print("maske: %d" % len(maskeler))
    satirlar = []
    for govde, mp in sorted(maskeler.items()):
        kaynak_dizin, stem = govde.split("__", 1)
        kare = KARE_KOK / kaynak_dizin / (stem + ".jpg")
        if not kare.is_file():
            continue
        img = cv2.imread(str(kare))
        sq, _, icerik = _preprocess(img)
        H, W = sq.shape[:2]
        ix, iy, iw, ih = icerik
        m960 = cv2.imread(str(mp), cv2.IMREAD_GRAYSCALE)
        # etiket olceginden uretim tuvaline (letterbox icerigi)
        buyuk = cv2.resize(m960, (iw, ih), interpolation=cv2.INTER_NEAREST)
        tuval = np.zeros((H, W), np.uint8)
        tuval[iy:iy + ih, ix:ix + iw] = buyuk
        s0 = (tuval == SINIF0).astype(np.uint8)
        ger = bant_temasi_gereken_px(iw)
        kayit = {"kare": govde, "kaynak": kaynak_dizin, "gereken": ger,
                 "bantlar": {}}
        eksik_taraflar = []
        for taraf in ("alt", "ust"):
            t = temas(s0, icerik, taraf)
            dilim = bant_dilimi(tuval, icerik, taraf)
            n = max(dilim.size, 1)
            pay = {"etiketsiz": round(float((dilim == ETIKETSIZ).sum()) / n, 4),
                   "sinif0": round(float((dilim == SINIF0).sum()) / n, 4),
                   "sinif1": round(float((dilim == SINIF1).sum()) / n, 4)}
            # UST SINIR: bandin ETIKETSIZ kismi sinif 0 olsaydi temas ne olurdu
            iyimser = ((dilim == SINIF0) | (dilim == ETIKETSIZ)).astype(np.uint8)
            t_iyimser = 0 if iyimser.size == 0 else int(iyimser.any(axis=0).sum())
            kayit["bantlar"][taraf] = {"temas": t, "yeter": t >= ger,
                                       "temas_iyimser": t_iyimser,
                                       "iyimser_yeter": t_iyimser >= ger, **pay}
            if t < ger:
                eksik_taraflar.append(taraf)
        kayit["eksik_taraf"] = eksik_taraflar
        if not eksik_taraflar:
            kayit["hukum"] = "ZATEN_YETER"
        else:
            # her eksik taraf iyimser halde yetiyorsa KURTARILABILIR
            hepsi = all(kayit["bantlar"][t]["iyimser_yeter"] for t in eksik_taraflar)
            en_bos = max(kayit["bantlar"][t]["etiketsiz"] for t in eksik_taraflar)
            if hepsi and en_bos >= 0.10:
                kayit["hukum"] = "KURTARILABILIR"
            elif hepsi:
                kayit["hukum"] = "KURTARILABILIR_ZAYIF"
            else:
                kayit["hukum"] = "ENGEL"
        satirlar.append(kayit)

    say = {}
    for s in satirlar:
        say[s["hukum"]] = say.get(s["hukum"], 0) + 1
    print("\nHUKUM DAGILIMI (%d kare)" % len(satirlar))
    for k in ("ZATEN_YETER", "KURTARILABILIR", "KURTARILABILIR_ZAYIF", "ENGEL"):
        if k in say:
            print("  %-22s %3d" % (k, say[k]))

    kurt = [s for s in satirlar if s["hukum"].startswith("KURTARILABILIR")]
    print("\nIS LISTESI: %d kare · eksik bant sayisi %d"
          % (len(kurt), sum(len(s["eksik_taraf"]) for s in kurt)))
    if kurt:
        bos = sorted(max(s["bantlar"][t]["etiketsiz"] for t in s["eksik_taraf"])
                     for s in kurt)
        print("  eksik bantlardaki ETIKETSIZ payi: medyan %.2f · min %.2f · maks %.2f"
              % (bos[len(bos) // 2], bos[0], bos[-1]))
        kk = {}
        for s in kurt:
            kk[s["kaynak"][-8:]] = kk.get(s["kaynak"][-8:], 0) + 1
        print("  kaynak dagilimi: %s" % kk)

    CIKTI.parent.mkdir(parents=True, exist_ok=True)
    CIKTI.write_text(json.dumps(
        {"_ne": "Eksik bant tanisi — bant tamamlamasi NEREDE ise yarar",
         "_hukumler": {
             "ZATEN_YETER": "bant zaten yeterli temasa sahip",
             "KURTARILABILIR": "eksik bandin >=%10'u ETIKETSIZ ve iyimser halde yeterdi",
             "KURTARILABILIR_ZAYIF": "iyimser halde yeterdi ama etiketsiz payi dusuk",
             "ENGEL": "iyimser halde bile yetmiyor -> etiketleme DEGISTIRMEZ"},
         "_uyari": "KURTARILABILIR bir TAHMINDIR; amele oraya bakip SINIF1 ya da "
                   "yine ETIKETSIZ diyebilir (D-210).",
         "sayim": say, "kareler": satirlar},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print("\nyazildi: %s" % CIKTI)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
