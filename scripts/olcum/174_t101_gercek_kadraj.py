"""T101 (D-400) — GERCEK kadrajda koridor sayisi ve `serit_no` sinir asimi.

ON KAYIT: results/t101_gercek_kadraj/ON_KAYIT.md (yontem + W1..W4 kapilari
sonuc gorulmeden yazildi).

SORU (gorevden): D-205 SENTETIK t66'da olctu — acik seridin kutusu 260
karenin 77'sinde (%29,6) iki `serit_no` ucte-birine yayiliyor, merkez-sinir
medyani 6,99 px. "Sentetik kadrajin mi gercegin mi sorunu BILINMIYOR."
Bu betik ayni olcuyu GERCEK kaynakli kumelerde yapar.

VEKIL: gercek karelerde serit kutusu etiketi YOK (T111 duvari). Koridorlar
URETIMIN KENDI `koridor_adaylari` ciktisindan alinir ve URETIMIN KENDI
`serit_yayilimi` alani okunur — D-205'in kullandigi ALANIN AYNISI, yani
sayilar birebir kiyaslanabilir. Yer gercegi degildir; rapor oyle anar.

⛔ `serit_no` DEGISMEZ (CONTRACTS §8) — bu tur yalniz olcer.
"""
import argparse
import json
import sys
from importlib import import_module
from pathlib import Path

import cv2
import numpy as np

from ayarlar import REPO, uretim_pt

sys.path.insert(0, str(REPO / "codes"))

from costmap_path_finder import (koridor_adaylari, olcek_px,  # noqa: E402
                                 serbest_alan)
from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp,  # noqa: E402
                           _preprocess, get_masks)

kabul_kumesi_yolu = import_module("65_kabul_denetcisi").kabul_kumesi_yolu

CONF = 0.30
GERCEK_KUMELER = ("arena_kompozit", "arena_kompozit_v2", "arena_kompozit_dji")


def kume_kareleri(kok):
    """(kare_yolu, arena) ciftleri — manifest sozlesmesi tek yerde."""
    man = json.loads((kok / "manifest.json").read_text(encoding="utf-8"))
    for o in man.get("ornekler", []):
        if o.get("durum") != "YAZILDI" or not o.get("arena"):
            continue
        p = kok / o["cikti"]
        if p.is_file():
            yield p, o["arena"]


def kare_olc(model, img, mpp, sayac):
    """Uretim zinciriyle kapi adaylarini cikar."""
    sq, small, icerik = _preprocess(img)
    son = model.predict(small, imgsz=INFER_SIZE, conf=CONF, verbose=False)
    sayac["segmentasyon"] += 1
    mk = _maskeleri_icerige_kirp(get_masks(son, *sq.shape[:2]), icerik)
    sa = serbest_alan(mk, mpp=mpp, icerik=icerik)
    r_gerekli = olcek_px(mpp)["r_gerekli_px"]
    adaylar, tani = koridor_adaylari(sa["dt_px"], r_gerekli, icerik=icerik)
    return adaylar, tani, icerik


def sinir_uzakligi(x, icerik_x0, icerik_w):
    """Kapi merkezinin en yakin ucte-bir sinirina piksel uzakligi."""
    s1 = icerik_x0 + icerik_w / 3.0
    s2 = icerik_x0 + 2.0 * icerik_w / 3.0
    return float(min(abs(x - s1), abs(x - s2)))


def kume_isle(ad, kok, model, sinir=0):
    sayac = {"segmentasyon": 0}
    kareler, kapilar = [], []
    ilk_mpp, ilk_boyut = None, None
    n = 0
    for p, a in kume_kareleri(kok):
        if sinir and n >= sinir:
            break
        mpp = a.get("mpp")
        if not mpp:
            continue
        img = cv2.imread(str(p))
        if img is None:
            continue
        n += 1
        if ilk_mpp is None:
            ilk_mpp, ilk_boyut = mpp, (img.shape[1], img.shape[0])
        adaylar, tani, icerik = kare_olc(model, img, mpp, sayac)
        ix, _iy, iw, _ih = icerik
        kare = {"kare": p.name, "acik_serit": a.get("acik_serit"),
                "n_kapi": tani.get("n_kapi", 0),
                "belirsiz": bool(tani.get("belirsiz")), "kapilar": []}
        for c in adaylar:
            yay = c.get("serit_yayilimi") or (0, 0)
            merkez = c.get("kapi_merkez_x")
            k = {"etiket": c.get("etiket"),
                 "gecilebilir": bool(c.get("gecilebilir")),
                 "merkez_x": merkez,
                 "genislik_px": c.get("kapi_genislik_px"),
                 "yayilim": list(yay),
                 "yayilan": bool(yay[0] != yay[1]),
                 "sinir_px": (sinir_uzakligi(merkez, ix, iw)
                              if merkez is not None else None)}
            k["sinir_m"] = (k["sinir_px"] * mpp
                            if k["sinir_px"] is not None else None)
            kare["kapilar"].append(k)
            kapilar.append(k)
        kareler.append(kare)

    kapili_kare = sum(1 for k in kareler if k["n_kapi"] > 0)
    yayilan = [k for k in kapilar if k["yayilan"]]
    acik_kapilar = [k for k in kapilar if k["gecilebilir"]]
    acik_yayilan = [k for k in acik_kapilar if k["yayilan"]]
    sinirlar = [k["sinir_px"] for k in kapilar if k["sinir_px"] is not None]
    sinirlar_m = [k["sinir_m"] for k in kapilar if k["sinir_m"] is not None]
    n_kapi_dagilim = {}
    for k in kareler:
        n_kapi_dagilim[k["n_kapi"]] = n_kapi_dagilim.get(k["n_kapi"], 0) + 1

    ozet = {
        "kume": ad, "n_kare": len(kareler), "mpp": ilk_mpp,
        "kare_boyutu": ilk_boyut,
        "kapili_kare": kapili_kare,
        "kapili_kare_orani": kapili_kare / max(1, len(kareler)),
        "n_kapi_dagilim": n_kapi_dagilim,
        "kapi_toplam": len(kapilar),
        "yayilan_kapi": len(yayilan),
        "yayilan_orani": len(yayilan) / max(1, len(kapilar)),
        "acik_kapi": len(acik_kapilar),
        "acik_yayilan": len(acik_yayilan),
        "acik_yayilan_orani": len(acik_yayilan) / max(1, len(acik_kapilar)),
        "sinir_px_medyan": float(np.median(sinirlar)) if sinirlar else None,
        "sinir_px_p05": float(np.percentile(sinirlar, 5)) if sinirlar else None,
        "sinir_m_medyan": float(np.median(sinirlar_m)) if sinirlar_m else None,
        "W3_tek_cikarim": sayac["segmentasyon"] == len(kareler),
    }
    return ozet, kareler


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", type=Path, default=uretim_pt())
    ap.add_argument("--sinir", type=int, default=0)
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    from ultralytics import YOLO
    model = YOLO(str(args.model), task="segment")

    kumeler = [(ad, REPO / "data" / ad) for ad in GERCEK_KUMELER]
    kumeler.append(("SENTETIK_t66_taban", kabul_kumesi_yolu()))

    ozetler, detay = [], {}
    for ad, kok in kumeler:
        if not (kok / "manifest.json").is_file():
            print(f"{ad}: manifest YOK — atlandi")
            continue
        ozet, kareler = kume_isle(ad, kok, model, sinir=args.sinir)
        ozetler.append(ozet)
        detay[ad] = kareler
        print(f"\n{ad}  (mpp={ozet['mpp']} · {ozet['kare_boyutu']})")
        print(f"  kare {ozet['n_kare']} · kapili kare "
              f"{ozet['kapili_kare']} (%{100*ozet['kapili_kare_orani']:.1f}) "
              f"· n_kapi dagilim {ozet['n_kapi_dagilim']}")
        print(f"  kapi {ozet['kapi_toplam']} · YAYILAN "
              f"{ozet['yayilan_kapi']} (%{100*ozet['yayilan_orani']:.1f}) "
              f"· acik kapilarda yayilan {ozet['acik_yayilan']}/"
              f"{ozet['acik_kapi']} (%{100*ozet['acik_yayilan_orani']:.1f})")
        print(f"  merkez-sinir: medyan {ozet['sinir_px_medyan']} px "
              f"({ozet['sinir_m_medyan']} m) · p05 {ozet['sinir_px_p05']} px")

    # W1 / W2 kapilari
    w1 = {o["kume"]: o["kapili_kare_orani"] >= 0.50 for o in ozetler}
    taban = next((o for o in ozetler if o["kume"] == "SENTETIK_t66_taban"), None)
    w2 = None
    if taban:
        w2 = abs(taban["acik_yayilan_orani"] - 0.296) <= 0.10
    print("\nW1 (her kumede kapili kare >= %50):",
          {k: ("GECTI" if v else "🔴 OLCULEMEDI") for k, v in w1.items()})
    print(f"W2 (sentetik taban D-205'in %29,6'sina ±10 puan): "
          f"{'GECTI' if w2 else '🔴 KAYMA VAR'}"
          + (f" — bugun %{100*taban['acik_yayilan_orani']:.1f}" if taban else ""))
    print("W3 (tek cikarim):",
          {o["kume"]: o["W3_tek_cikarim"] for o in ozetler})

    cikti = {"_on_kayit": "results/t101_gercek_kadraj/ON_KAYIT.md",
             "_model": str(args.model),
             "_vekil_notu": ("koridorlar uretimin koridor_adaylari ciktisindan; "
                             "yer gercegi DEGIL (T111 duvari)"),
             "W1": w1, "W2_sentetik_taban": w2,
             "ozetler": ozetler, "kareler": detay}
    hedef = args.json or (REPO / "results" / "t101_gercek_kadraj"
                          / "olcum_20260903.json")
    hedef.parent.mkdir(parents=True, exist_ok=True)
    hedef.write_text(json.dumps(cikti, ensure_ascii=False, indent=1),
                     encoding="utf-8")
    print(f"json -> {hedef}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
