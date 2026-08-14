"""T63c — HARITALAMA gorseli: goruntu -> maske -> C-uzayi -> rota.

Amac: karar zincirinin urettigi HARITAYI gosterebilir hale getirmek. Dort
katman, uretim fonksiyonlariyla:

    1 OZGUN          ham kare
    2 SEGMENTASYON   zemin / engel (model ciktisi)
    3 C-UZAYI        distanceTransform >= r_gerekli_px  ->  IKA govdesinin
                     MERKEZININ durabilecegi yerler. Haritanin kendisi budur.
    4 ROTA           dogrulanmis yol + waypoint'ler

C-uzayi neden harita: `costmap_path_finder` rotayi ham serbest alanda degil,
govde yaricapina gore ASINDIRILMIS alanda arar (R_GEREKLI_M = 1,10 m). Ekranda
yesil gorunen bir bosluk IKA icin gecilebilir olmayabilir; 3. panel bunu
gorunur kilar.

Kullanim:
  venv\\Scripts\\python.exe 62_haritalama_gorseli.py --model models/... \
      --kume calisma/sentetik_arena_kadraj_t60 --kare sa_000003.jpg
  venv\\Scripts\\python.exe 62_haritalama_gorseli.py --model ... --gercek-arena
"""
import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

from ayarlar import REPO

sys.path.insert(0, str(REPO / "codes"))

from costmap_path_finder import R_GEREKLI_M  # noqa: E402
from karar_sozlesmesi import (rota_olcek_reddi, zemin_kaplamasi,  # noqa: E402
                              zemin_kenar_dayanmasi, zemin_maskesi_reddi)
from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp,  # noqa: E402
                           _preprocess, analyze_path, get_masks)

CONF = 0.30
GERCEK_ARENA = REPO / "data" / "arena_referans" / "sartname_s9_arena.png"


def basliklandir(p, ad, alt=None):
    yuk = 30 if alt is None else 50
    cv2.rectangle(p, (0, 0), (p.shape[1], yuk), (0, 0, 0), -1)
    cv2.putText(p, ad, (8, 21), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                (255, 255, 255), 2)
    if alt:
        cv2.putText(p, alt, (8, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.45,
                    (170, 210, 255), 1)
    return p


def harita_uret(model, img, mpp, baslik):
    sq, small, icerik = _preprocess(img)
    h, w = sq.shape[:2]
    sonuc = model.predict(small, imgsz=INFER_SIZE, conf=CONF, verbose=False)
    mk = _maskeleri_icerige_kirp(get_masks(sonuc, h, w), icerik)
    trav, blok = mk[0], mk[1]

    kaplama = zemin_kaplamasi(trav, icerik)
    kenar = zemin_kenar_dayanmasi(trav, icerik)
    zemin_red = zemin_maskesi_reddi(trav, icerik)
    olcek_red = rota_olcek_reddi(mpp)
    yol, guven, wps, _k, karar_red, olcum = analyze_path(
        trav, icerik=icerik, engel_mask=blok, mpp=mpp,
        return_clean=True, return_reason=True, return_olcum=True)

    def kapla(taban, m, renk, a=0.55):
        kat = np.zeros_like(taban)
        kat[m > 0] = renk
        return cv2.addWeighted(taban, 1.0, kat, a, 0)

    p1 = sq.copy()
    p2 = kapla(kapla(sq.copy(), trav, (0, 190, 0)), blok, (0, 0, 220))

    # --- 3. panel: C-UZAYI ---
    serbest = trav.copy()
    serbest[blok > 0] = 0
    dt = cv2.distanceTransform((serbest > 0).astype(np.uint8), cv2.DIST_L2, 5)
    p3 = sq.copy()
    if mpp:
        r_px = R_GEREKLI_M / mpp
        gecilebilir = (dt >= r_px).astype(np.uint8)
        p3 = kapla(p3, (serbest > 0).astype(np.uint8), (60, 60, 60), 0.55)
        p3 = kapla(p3, gecilebilir, (255, 200, 0), 0.65)
        c_alt = (f"r_gerekli = {R_GEREKLI_M:.2f} m / {mpp:.5f} = {r_px:.1f} px"
                 f"  ·  gecilebilir %{100.0 * gecilebilir.mean():.1f}")
    else:
        p3 = kapla(p3, (serbest > 0).astype(np.uint8), (60, 60, 60), 0.55)
        c_alt = "OLCEK YOK -> C-uzayi HESAPLANAMAZ (govde acikligi dogrulanamaz)"

    # --- 4. panel: ROTA ---
    p4 = sq.copy()
    p4 = kapla(p4, (serbest > 0).astype(np.uint8), (70, 70, 70), 0.45)
    if wps:
        pts = [(int(round(x)), int(round(y))) for x, y in wps]
        for a, b in zip(pts, pts[1:]):
            cv2.line(p4, a, b, (0, 0, 255), 3)
        for q in pts:
            cv2.circle(p4, q, 6, (255, 255, 255), -1)
            cv2.circle(p4, q, 6, (0, 0, 255), 2)
    red = olcek_red or zemin_red or karar_red
    yayin = "YAYINLANIR" if red is None else f"YAYINLANMAZ · {red[0]}"
    r_alt = (f"serit={yol} guven={guven} · darbogaz="
             f"{(olcum or {}).get('darbogaz_px', 0):.1f} px · {yayin}")

    x0, y0, cw, ch = icerik
    for p in (p1, p2, p3, p4):
        cv2.rectangle(p, (x0, y0), (x0 + cw, y0 + ch), (255, 255, 255), 1)
    basliklandir(p1, f"1 OZGUN — {baslik}",
                 f"mpp={mpp if mpp else 'YOK'}")
    basliklandir(p2, "2 SEGMENTASYON  yesil=zemin  kirmizi=engel",
                 f"kaplama {kaplama:.3f} · kenar {kenar:.3f}"
                 f" · zemin kapisi: {'SUSUYOR' if zemin_red is None else zemin_red[0]}")
    basliklandir(p3, "3 C-UZAYI (HARITA)  sari = IKA MERKEZI durabilir", c_alt)
    basliklandir(p4, "4 ROTA", r_alt)
    return np.vstack([np.hstack([p1, p2]), np.hstack([p3, p4])])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", type=Path, required=True)
    ap.add_argument("--kume", type=Path, default=None)
    ap.add_argument("--kare", default=None)
    ap.add_argument("--gercek-arena", action="store_true")
    ap.add_argument("--cikti", type=Path, required=True)
    args = ap.parse_args()

    from ultralytics import YOLO
    model = YOLO(str(args.model), task="segment")

    if args.gercek_arena:
        img = cv2.imread(str(GERCEK_ARENA))
        panel = harita_uret(model, img, None, GERCEK_ARENA.name)
    else:
        man = json.loads((args.kume / "manifest.json").read_text(encoding="utf-8"))
        secili = None
        for o in man["ornekler"]:
            if o.get("arena") and Path(o["cikti"]).name == args.kare:
                secili = o
                break
        if secili is None:
            raise SystemExit(f"kare bulunamadi: {args.kare}")
        img = cv2.imread(str(args.kume / secili["cikti"]))
        panel = harita_uret(model, img, secili["arena"]["mpp"], args.kare)

    args.cikti.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(args.cikti), panel)
    print(f"panel -> {args.cikti}  {panel.shape[1]}x{panel.shape[0]}")


if __name__ == "__main__":
    main()
