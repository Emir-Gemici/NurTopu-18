"""151 — K7 · YAYINLANAN SERIT DOGRULUGU (ON_KAYIT SS34 · REVIEW_LOG D-314).

Sartname SS2.1/SS5.3.2: "uc yoldan yalnizca biri acik" ve YANLIS GUZERGAH =
0 PUAN. Hakem ekranda NUMARAYI canli onaylar (SS2.2.3). Kabul zinciri bu ekseni
2026-08-27'ye kadar HIC olcmuyordu: K1 rota URETIMINI, K6 rotanin yol USTUNDE
olup olmadigini olcer; NUMARAYI hicbiri olcmez.

🔴 NEDEN DONDURULMUS ALT KUME: serit numarasi goruntunun UCTE BIRLERINDEN
hesaplanir (`karar_sozlesmesi.serit_no`). Koridor kapisi bir sinira denk
geldiginde etiket TANIM GEREGI belirsizlesir (T101). Olculdu (D-312): kabul
kumesinin %54'u boyle ve serit ayrismasinin %100'u oradan geliyor. Bu yuzden
kapi YALNIZ `config/k7_iyi_kosullu_kume.json` icindeki 88 karede olcer —
orada manifest ile koridor envanteri %100 uyusur, yani referans KESINDIR.
Kotu kosullu 105 ve beyansiz 49 kare DISLANIR; aksi halde kapi, tanim geregi
belirsiz olan bir seyi olcuyormus gibi yapar (D-15 sinifi vakum kapi).

Kullanim:
  python 151_k7_serit_dogrulugu.py --agirlik models/navitas_seg_v36_best.pt
  python 151_k7_serit_dogrulugu.py                 # uretim modeli (defterden)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[2]
for _y in (KOK / "codes", KOK / "comms"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

import cv2  # noqa: E402
import numpy as np  # noqa: E402
import rpi_inference as ri  # noqa: E402

KUME_DOSYASI = KOK / "config" / "k7_iyi_kosullu_kume.json"
# URETIM guven esigi — ciplak yazilmaz, uretimin CLI varsayilanindan gelir
# (61/65/126 ile ayni; kilit: tests/test_conf_esigi_supurmesi.py).
CONF = 0.30


def iyi_kosullu_kume(yol: Path = KUME_DOSYASI):
    """DONDURULMUS alt kume — kosum aninda YENIDEN TURETILMEZ."""
    veri = json.loads(yol.read_text(encoding="utf-8"))
    kareler = veri["kareler"]
    if len(kareler) != int(veri["n"]):
        raise ValueError(f"k7 kumesi tutarsiz: n={veri['n']} liste={len(kareler)}")
    return veri


def olc(agirlik: Path, veri: dict, kume_koku: Path):
    from ultralytics import YOLO

    mf = json.loads((kume_koku / "manifest.json").read_text(encoding="utf-8"))
    mpp = {Path(o["cikti"]).name: o["arena"].get("mpp") for o in mf["ornekler"]
           if isinstance(o.get("arena"), dict)}
    model = YOLO(str(agirlik))

    satirlar = []
    for kayit in veri["kareler"]:
        ad = kayit["kare"]
        gorsel = None
        for alt in ("val", "train"):
            aday = kume_koku / "images" / alt / ad
            if aday.is_file():
                gorsel = aday
                break
        if gorsel is None:
            satirlar.append({"kare": ad, "hata": "gorsel bulunamadi"})
            continue
        img = cv2.imread(str(gorsel))
        sq, small, icerik = ri._preprocess(img)
        yan = sq.shape[0]
        son = model.predict(small, imgsz=ri.INFER_SIZE, conf=CONF, verbose=False)
        mk = ri._maskeleri_icerige_kirp(ri.get_masks(son, yan, yan), icerik)
        hy, gv, hw, red = ri.analyze_path(mk[0], icerik=icerik,
                                          engel_mask=mk[1], mpp=mpp.get(ad),
                                          return_reason=True)
        yol_no, gv, wps, red = ri._rota_kararini_esikle(hy, gv, hw, red)
        satirlar.append({
            "kare": ad, "referans_serit": kayit["referans_serit"],
            "yayinlanan": yol_no,
            "ret": (red[0] if isinstance(red, (tuple, list)) else red),
            "dogru": bool(yol_no is not None and yol_no == kayit["referans_serit"]),
        })
    return satirlar


def ozetle(satirlar, n_kume):
    olculen = [s for s in satirlar if "hata" not in s]
    rota = [s for s in olculen if s["yayinlanan"] is not None]
    dogru = sum(1 for s in rota if s["dogru"])
    return {
        "kume_n": n_kume, "olculen": len(olculen),
        "rota_uretilen": len(rota), "dogru": dogru,
        "yanlis": len(rota) - dogru,
        "rota_uretilmeyen": len(olculen) - len(rota),
        "dogruluk": (dogru / len(rota)) if rota else None,
        "yanlis_kareler": [(s["kare"], s["referans_serit"], s["yayinlanan"])
                           for s in rota if not s["dogru"]],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agirlik", type=Path, default=None)
    ap.add_argument("--kume", type=Path, default=None,
                    help="kabul kumesi koku (varsayilan: defterden)")
    ap.add_argument("--cikti", type=Path, default=None)
    a = ap.parse_args()

    defter = json.loads((KOK / "config" / "model_registry.json")
                        .read_text(encoding="utf-8"))
    kume_koku = a.kume or Path(defter["profiles"]["competition"]["kabul_kumesi"])
    if not kume_koku.is_absolute():
        kume_koku = KOK / kume_koku      # T220: defter yolu depo kokune GORELI (madde 16)
    agirlik = a.agirlik
    if agirlik is None:
        from model_registry import resolve_model
        agirlik = Path(resolve_model()[0])
    elif not agirlik.is_absolute():
        agirlik = (KOK / agirlik).resolve()

    veri = iyi_kosullu_kume()
    print(f"K7 · dondurulmus alt kume {veri['n']} kare · model {agirlik.name} "
          f"· conf {CONF}", flush=True)
    satirlar = olc(agirlik, veri, kume_koku)
    ozet = ozetle(satirlar, veri["n"])
    ozet["model"] = agirlik.name
    ozet["conf"] = CONF
    print(json.dumps({k: v for k, v in ozet.items() if k != "yanlis_kareler"},
                     indent=1, ensure_ascii=False))
    if ozet["yanlis_kareler"]:
        print("yanlis (kare, referans, yayinlanan):", ozet["yanlis_kareler"])

    cikti = a.cikti or (KOK / "results" / "t165" / "k7_olcum.json")
    cikti.parent.mkdir(parents=True, exist_ok=True)
    cikti.write_text(json.dumps({"ozet": ozet, "kareler": satirlar}, indent=1,
                                ensure_ascii=False), encoding="utf-8")
    print("yazildi:", cikti)


if __name__ == "__main__":
    main()
