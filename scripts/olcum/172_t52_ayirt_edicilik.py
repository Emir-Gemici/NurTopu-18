"""T52 (D-398) — "her sey boyanmis" cokusu ile gercek acik arenayi ayiran olcut.

ON KAYIT: results/t52_ayirt_edicilik/ON_KAYIT.md (adaylar + karar kurali
sonuc gorulmeden). Imza URETIMIN KENDISI (T99 dersi): _preprocess ->
predict(INFER_SIZE, conf=0.30) -> get_masks -> _maskeleri_icerige_kirp;
buyuklukler ICERIK kutusunda.

Kumeler: mesru = kabul kumesi (registry, kendi mpp'si karar icin gereksiz —
buyuklukler maskeden) · cokus = data/raw_frames (otopark kareleri).
"""
import json
import sys
from importlib import import_module
from pathlib import Path

import cv2
import numpy as np

from ayarlar import REPO, uretim_pt

sys.path.insert(0, str(REPO / "codes"))

from karar_sozlesmesi import zemin_kenar_dayanmasi  # noqa: E402
from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp,  # noqa: E402
                           _preprocess, get_masks)

kabul_kumesi_yolu = import_module("65_kabul_denetcisi").kabul_kumesi_yolu
CONF = 0.30

# ON_KAYIT §2 — cokuste beklenen YON (+1: cokuste yuksek, -1: dusuk)
ADAY_YONLERI = {"A1_zemin_orani": +1, "A2_bilesen_sayisi": -1,
                "A3_en_buyuk_pay": +1, "A4_kenar_dayanma": +1,
                "A5_engel_orani": -1}


def buyuklukler(model, img):
    sq, small, icerik = _preprocess(img)
    r = model.predict(small, imgsz=INFER_SIZE, conf=CONF, verbose=False)
    mk = _maskeleri_icerige_kirp(get_masks(r, *sq.shape[:2]), icerik)
    zemin = np.asarray(mk.get(0))
    engel = mk.get(1)
    x0, y0, iw, ih = icerik
    icerik_alani = float(iw * ih)
    z = float(zemin.sum()) if zemin is not None and zemin.ndim == 2 else 0.0
    e = (float(np.asarray(engel).sum())
         if engel is not None and np.asarray(engel).ndim == 2 else 0.0)

    if zemin is not None and zemin.ndim == 2 and z > 0:
        n_bilesen, etiketler = cv2.connectedComponents(
            zemin.astype(np.uint8), connectivity=8)
        n_bilesen -= 1                                    # arka plan haric
        boyutlar = np.bincount(etiketler.ravel())[1:]
        en_buyuk_pay = float(boyutlar.max()) / z if len(boyutlar) else 0.0
        kenar = zemin_kenar_dayanmasi(zemin, icerik=icerik)
    else:
        n_bilesen, en_buyuk_pay, kenar = 0, 0.0, 0.0

    return {"A1_zemin_orani": z / (z + e) if (z + e) > 0 else 0.0,
            "A2_bilesen_sayisi": float(n_bilesen),
            "A3_en_buyuk_pay": en_buyuk_pay,
            "A4_kenar_dayanma": float(kenar),
            "A5_engel_orani": e / icerik_alani if icerik_alani else 0.0,
            "_bos_zemin": z == 0.0}


def kume_olc(model, kareler):
    kayitlar = []
    for p in kareler:
        img = cv2.imread(str(p))
        if img is None:
            continue
        b = buyuklukler(model, img)
        b["_kare"] = p.name
        kayitlar.append(b)
    return kayitlar


def main():
    from ultralytics import YOLO
    model_yolu = uretim_pt()
    model = YOLO(str(model_yolu), task="segment")

    kume = kabul_kumesi_yolu()
    man = json.loads((kume / "manifest.json").read_text(encoding="utf-8"))
    mesru_kareler = [kume / o["cikti"] for o in man["ornekler"]
                     if o.get("durum") == "YAZILDI" and o.get("arena")
                     and (kume / o["cikti"]).is_file()]
    cokus_kareler = sorted((REPO / "data" / "raw_frames").rglob("*.jpg"))

    print(f"mesru n={len(mesru_kareler)} · cokus n={len(cokus_kareler)}")
    mesru = kume_olc(model, mesru_kareler)
    cokus = kume_olc(model, cokus_kareler)

    # Bos-zemin kareler cokus tanimina girmez (K0 zaten ayri kapi): raporla
    bos_c = sum(1 for k in cokus if k["_bos_zemin"])
    bos_m = sum(1 for k in mesru if k["_bos_zemin"])
    print(f"bos-zemin: mesru {bos_m} · cokus {bos_c} (analiz disi degil, "
          "deger 0 olarak kalir)")

    analiz = {}
    for aday, yon in ADAY_YONLERI.items():
        md = np.array([k[aday] for k in mesru])
        cd = np.array([k[aday] for k in cokus])
        if yon == +1:      # cokuste yuksek: bosluk = cokus_min - mesru_maks
            bosluk = float(cd.min() - md.max())
            esik = float((cd.min() + md.max()) / 2)
        else:              # cokuste dusuk: bosluk = mesru_min - cokus_maks
            bosluk = float(md.min() - cd.max())
            esik = float((md.min() + cd.max()) / 2)
        aciklik = float(max(md.max(), cd.max()) - min(md.min(), cd.min()))
        gorece = bosluk / aciklik if aciklik > 0 else 0.0
        analiz[aday] = {
            "mesru": {"min": float(md.min()), "maks": float(md.max()),
                      "p50": float(np.median(md))},
            "cokus": {"min": float(cd.min()), "maks": float(cd.max()),
                      "p50": float(np.median(cd))},
            "bosluk": bosluk, "gorece_bosluk": gorece,
            "ayiriyor": bosluk > 0.0, "esik_onerisi": esik if bosluk > 0 else None}
        print(f"{aday:18s} mesru[{md.min():7.3f},{md.max():7.3f}] "
              f"cokus[{cd.min():7.3f},{cd.max():7.3f}] "
              f"bosluk={bosluk:+.4f} ({'AYIRIYOR' if bosluk > 0 else 'cakisik'})")

    ayiranlar = {a: v for a, v in analiz.items() if v["ayiriyor"]}
    if ayiranlar:
        secilen = max(ayiranlar, key=lambda a: ayiranlar[a]["gorece_bosluk"])
        verdikt = f"AYIRAN BULUNDU: {secilen}"
        # Yanlis-negatif raporu (ON_KAYIT §3.4)
        v = analiz[secilen]
        print(f"\nSECILEN: {secilen} · esik onerisi {v['esik_onerisi']:.4f} "
              f"(gorece bosluk {v['gorece_bosluk']:.2%})")
    else:
        secilen = None
        verdikt = "DOGRULANAMADI"
        print("\nDOGRULANAMADI — hicbir aday cakismasiz ayirmiyor; "
              "kopru tavan 0,55 OLDUGU GIBI kalir (ON_KAYIT §3.3)")

    cikti = {"_on_kayit": "results/t52_ayirt_edicilik/ON_KAYIT.md",
             "_model": str(model_yolu), "verdikt": verdikt,
             "secilen": secilen, "analiz": analiz,
             "n": {"mesru": len(mesru), "cokus": len(cokus),
                   "bos_zemin_mesru": bos_m, "bos_zemin_cokus": bos_c}}
    hedef = REPO / "results" / "t52_ayirt_edicilik" / "olcum_20260903.json"
    hedef.write_text(json.dumps(cikti, ensure_ascii=False, indent=1),
                     encoding="utf-8")
    print(f"json -> {hedef}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
