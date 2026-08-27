"""T165 teshisi (ON_KAYIT SS31): serit kaymasi ATFETME hatasi mi, ROTA SECIMI mi?

Her kare icin:
  - manifestten her seridin x PENCERESI (bariyerler[].pencere / kutu)
  - uretim rotasinin piksel medyan x'i ve `serit_no` (ucte bir) atamasi
  - rotanin ACIK seridin KENDI penceresi icinde kalip kalmadigi

Kod DEGISMEZ; yalniz olculur.
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
from karar_sozlesmesi import serit_no  # noqa: E402

CONF = 0.30


def _serit_pencereleri(arena):
    """{serit: (x0, x1)} — manifestteki `pencere` (yoksa `kutu`)."""
    cikti = {}
    for b in arena.get("bariyerler", []) or []:
        s = b.get("serit")
        kutu = b.get("pencere") or b.get("kutu")
        if s is None or not kutu:
            continue
        x, _y, w, _h = kutu[:4]
        eski = cikti.get(s)
        yeni = (float(x), float(x) + float(w))
        cikti[s] = yeni if eski is None else (min(eski[0], yeni[0]),
                                              max(eski[1], yeni[1]))
    return cikti


def main():
    from ultralytics import YOLO

    defter = json.loads((KOK / "config" / "model_registry.json")
                        .read_text(encoding="utf-8"))
    kume = Path(defter["profiles"]["competition"]["kabul_kumesi"])
    mf = json.loads((kume / "manifest.json").read_text(encoding="utf-8"))
    arena_bilgi = {Path(o["cikti"]).name: o["arena"] for o in mf["ornekler"]
                   if isinstance(o.get("arena"), dict)}

    onceki = json.loads((KOK / "results" / "t164" / "olcum.json")
                        .read_text(encoding="utf-8"))
    ilgi = [s["kare"] for s in onceki["kareler"]
            if s["uretim"] is not None and not s["uretim_dogru"]]
    dogrular = [s["kare"] for s in onceki["kareler"] if s["uretim_dogru"]][:10]
    print(f"YANLIS {len(ilgi)} · kontrol grubu {len(dogrular)} dogru kare",
          flush=True)

    model = YOLO(str(KOK / "models" / "navitas_seg_v36_best.pt"))
    satirlar = []
    for ad in ilgi + dogrular:
        yol = None
        for alt in ("val", "train"):
            aday = kume / "images" / alt / ad
            if aday.is_file():
                yol = aday
                break
        if yol is None:
            continue
        arena = arena_bilgi[ad]
        img = cv2.imread(str(yol))
        sq, small, icerik = ri._preprocess(img)
        yan = sq.shape[0]
        x0, y0, w, h = icerik
        son = model.predict(small, imgsz=ri.INFER_SIZE, conf=CONF, verbose=False)
        mk = ri._maskeleri_icerige_kirp(ri.get_masks(son, yan, yan), icerik)
        hy, gv, hw, red, olc = ri.analyze_path(
            mk[0], icerik=icerik, engel_mask=mk[1], mpp=arena.get("mpp"),
            return_reason=True, return_olcum=True)
        yol_no, gv, wps, red = ri._rota_kararini_esikle(hy, gv, hw, red)
        if yol_no is None:
            continue

        # Rota piksellerinin x dagilimi — `rota_serit_karari` govdeyi kullanir.
        rota_px = (olc or {}).get("rota_pikselleri")
        if rota_px is not None and len(rota_px):
            xs = np.asarray([p[0] for p in rota_px], dtype=float)
        else:
            xs = np.asarray([p[0] for p in (wps or [])], dtype=float)
        if xs.size == 0:
            continue
        medyan_x = float(np.median(xs))

        pencere = _serit_pencereleri(arena)
        beklenen = arena.get("acik_serit")
        acik_pencere = pencere.get(beklenen)
        ucte_bir = [x0 + w / 3.0, x0 + 2.0 * w / 3.0]
        satirlar.append({
            "kare": ad,
            "beklenen_serit": beklenen,
            "yayinlanan": yol_no,
            "dogru": bool(yol_no == beklenen),
            "rota_medyan_x": round(medyan_x, 1),
            "serit_no_medyandan": serit_no(medyan_x, x0, w),
            "ucte_bir_sinirlari": [round(u, 1) for u in ucte_bir],
            "acik_serit_penceresi": (None if acik_pencere is None else
                                     [round(acik_pencere[0], 1),
                                      round(acik_pencere[1], 1)]),
            "pencere_icinde": (None if acik_pencere is None else
                               bool(acik_pencere[0] <= medyan_x <= acik_pencere[1])),
            "tum_pencereler": {str(k): [round(v[0], 1), round(v[1], 1)]
                               for k, v in sorted(pencere.items())},
            "icerik": [x0, y0, w, h],
        })
        d = satirlar[-1]
        print(f"  {ad} beklenen {beklenen} yayin {yol_no} | medyan x "
              f"{d['rota_medyan_x']} | ucte bir {d['ucte_bir_sinirlari']} | "
              f"acik pencere {d['acik_serit_penceresi']} | pencere icinde "
              f"{d['pencere_icinde']}", flush=True)

    yanlislar = [s for s in satirlar if not s["dogru"]]
    dogrular_s = [s for s in satirlar if s["dogru"]]
    icinde = sum(1 for s in yanlislar if s["pencere_icinde"])

    # ALET DOGRULAMASI (bos kapi yasagi): "acik seridin penceresi" olcutu ancak
    # DOGRU karelerde TUTUYORSA anlamlidir. Tutmuyorsa olcut, manifestin
    # `bariyerler[].pencere` alanini yanlis yorumluyor demektir ve HUKUM
    # VERILEMEZ. Bu kontrol olmadan yanlis bir kok ilan edilebilirdi (ilk
    # kosumda tam bunun esigine gelindi — REVIEW_LOG D-310).
    olculebilir = [s for s in dogrular_s if s["pencere_icinde"] is not None]
    kontrol_ic = sum(1 for s in olculebilir if s["pencere_icinde"])
    alet_gecerli = bool(olculebilir) and kontrol_ic >= max(1, int(0.8 * len(olculebilir)))

    if not alet_gecerli:
        hukum = ("HUKUM VERILEMEDI - ALET GECERSIZ: kontrol grubundaki DOGRU "
                 f"karelerin {kontrol_ic}/{len(olculebilir)}'i 'acik serit "
                 "penceresi icinde' cikti; olcut DOGRU kareleri bile "
                 "aciklamiyor. Kok ayrimi bu aletle YAPILAMAZ.")
    else:
        hukum = ("ATFETME (numara hesabi)" if icinde >= 4 else
                 ("ROTA SECIMI (planlayici)" if icinde <= 1 else "TEK KOK YOK"))

    def _sinir_uzakligi(s):
        return round(min(abs(s["rota_medyan_x"] - u)
                         for u in s["ucte_bir_sinirlari"]), 1)

    for s in satirlar:
        s["ucte_bir_sinirina_uzaklik"] = _sinir_uzakligi(s)
    y_uz = sorted(_sinir_uzakligi(s) for s in yanlislar)
    d_uz = sorted(_sinir_uzakligi(s) for s in dogrular_s)

    print("")
    print(f"KONTROL GRUBU: dogru karelerin {kontrol_ic}/{len(olculebilir)}'i "
          f"pencere icinde · ALET GECERLI: {alet_gecerli}")
    print(f"YANLIS {len(yanlislar)} kareden {icinde}'i pencere icinde")
    print(f"HUKUM: {hukum}")
    print(f"ucte bir sinirina uzaklik (px) · YANLIS {y_uz} · DOGRU {d_uz}")

    p = KOK / "results" / "t165" / "olcum.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"hukum": hukum, "alet_gecerli": alet_gecerli,
                             "kontrol_ic": kontrol_ic,
                             "kontrol_n": len(olculebilir),
                             "yanlis_n": len(yanlislar),
                             "pencere_icinde": icinde,
                             "sinir_uzakligi_yanlis": y_uz,
                             "sinir_uzakligi_dogru": d_uz,
                             "kareler": satirlar},
                            indent=1, ensure_ascii=False), encoding="utf-8")
    print("yazildi:", p)


if __name__ == "__main__":
    main()
