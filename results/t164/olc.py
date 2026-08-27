"""T164 olcumu (ON_KAYIT SS30): kabul kumesinde YAYINLANAN SERIT dogru mu?

AYIRT EDICI OLCUM: ayni karelerde IKI karar yolu ayri ayri manifestteki
`acik_serit` ile kiyaslanir.
  URETIM  : rpi_inference.analyze_path  -> yayinlanan `road` (T155 duzeltmesi)
  TANISAL : costmap_path_finder.rota_bul -> `yol_no` (T155'te 15/15 olculmustu)

Amac, "uretim yanlis serit yayinliyor" demeden once kusurun OLCUM ARACINDA mi
(manifest sozlesmesi farkli) yoksa URETIMDE mi oldugunu ayirmaktir.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[2]
for _y in (KOK / "codes", KOK / "comms"):
    sys.path.insert(0, str(_y))

import cv2  # noqa: E402
import numpy as np  # noqa: E402
import rpi_inference as ri  # noqa: E402
from costmap_path_finder import rota_bul  # noqa: E402

CONF = 0.30


def main():
    from ultralytics import YOLO

    defter = json.loads((KOK / "config" / "model_registry.json")
                        .read_text(encoding="utf-8"))
    kume = Path(defter["profiles"]["competition"]["kabul_kumesi"])
    mf = json.loads((kume / "manifest.json").read_text(encoding="utf-8"))
    bilgi = {}
    for o in mf["ornekler"]:
        a = o.get("arena")
        if isinstance(a, dict) and a.get("acik_serit") is not None:
            bilgi[Path(o["cikti"]).name] = {
                "acik_serit": a["acik_serit"],
                "kapali": a.get("kapali_seritler"),
                "adaylar": a.get("acik_serit_adaylari"),
                "belirsiz": a.get("belirsiz"),
                "mpp": a.get("mpp"),
            }

    val = sorted((kume / "images" / "val").glob("*.jpg"))
    train = sorted((kume / "images" / "train").glob("*.jpg"))
    adim = max(1, len(train) // 40)
    secilen = val + train[::adim][:40]
    secilen = [p for p in secilen if p.name in bilgi]
    assert secilen, "kabul kumesinde manifestli kare yok"

    model = YOLO(str(KOK / "models" / "navitas_seg_v36_best.pt"))
    print(f"kare {len(secilen)} (val {len(val)}) · v36 · conf {CONF}", flush=True)

    satirlar = []
    for i, yol in enumerate(secilen, 1):
        img = cv2.imread(str(yol))
        sq, small, icerik = ri._preprocess(img)
        yan = sq.shape[0]
        son = model.predict(small, imgsz=ri.INFER_SIZE, conf=CONF, verbose=False)
        mk = ri._maskeleri_icerige_kirp(ri.get_masks(son, yan, yan), icerik)
        mpp = bilgi[yol.name]["mpp"]

        hy, gv, hw, red = ri.analyze_path(mk[0], icerik=icerik,
                                          engel_mask=mk[1], mpp=mpp,
                                          return_reason=True)
        uretim_yol, _gv, _wps, _red = ri._rota_kararini_esikle(hy, gv, hw, red)

        try:
            tanisal = rota_bul(mk, mpp=mpp, icerik=icerik)
            tanisal_yol = tanisal.get("yol_no")
            tanisal_durum = tanisal.get("durum")
        except Exception as exc:
            tanisal_yol, tanisal_durum = None, f"HATA:{type(exc).__name__}"

        beklenen = bilgi[yol.name]["acik_serit"]
        satirlar.append({
            "kare": yol.name, "beklenen": beklenen,
            "uretim": uretim_yol, "tanisal": tanisal_yol,
            "tanisal_durum": tanisal_durum,
            "uretim_dogru": bool(uretim_yol is not None and uretim_yol == beklenen),
            "tanisal_dogru": bool(tanisal_yol is not None and tanisal_yol == beklenen),
            "belirsiz": bilgi[yol.name]["belirsiz"],
        })
        if i % 20 == 0:
            print(f"  {i}/{len(secilen)}", flush=True)

    n = len(satirlar)
    u_rota = sum(1 for s in satirlar if s["uretim"] is not None)
    t_rota = sum(1 for s in satirlar if s["tanisal"] is not None)
    u_dogru = sum(1 for s in satirlar if s["uretim_dogru"])
    t_dogru = sum(1 for s in satirlar if s["tanisal_dogru"])
    # Yalniz IKISININ DE rota urettigi kareler — esli kiyas
    esli = [s for s in satirlar if s["uretim"] is not None and s["tanisal"] is not None]
    e_u = sum(1 for s in esli if s["uretim_dogru"])
    e_t = sum(1 for s in esli if s["tanisal_dogru"])
    ayni = sum(1 for s in esli if s["uretim"] == s["tanisal"])

    ozet = {
        "n": n, "uretim_rota": u_rota, "tanisal_rota": t_rota,
        "uretim_dogru": u_dogru, "tanisal_dogru": t_dogru,
        "esli_n": len(esli), "esli_uretim_dogru": e_u, "esli_tanisal_dogru": e_t,
        "esli_iki_yol_ayni": ayni,
    }
    print(json.dumps(ozet, indent=1, ensure_ascii=False))
    print(f"URETIM  dogru serit {u_dogru}/{n} (rota {u_rota})")
    print(f"TANISAL dogru serit {t_dogru}/{n} (rota {t_rota})")
    print(f"ESLI ({len(esli)} kare): uretim {e_u} · tanisal {e_t} · "
          f"iki yol ayni {ayni}")

    p = KOK / "results" / "t164" / "olcum.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"ozet": ozet, "kareler": satirlar}, indent=1,
                            ensure_ascii=False), encoding="utf-8")
    print("yazildi:", p)


if __name__ == "__main__":
    main()
