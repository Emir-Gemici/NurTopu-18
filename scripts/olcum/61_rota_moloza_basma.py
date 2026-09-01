"""T63b — SERIT TANIMINDAN BAGIMSIZ olcut: rota molozun USTUNDEN geciyor mu?

NEDEN. "Serit dogru mu" olcumu iki tanima birden bagli: uretecin serit indisi ve
`analyze_path`in `icerik` ucte biri. Bu ikisi kadraj kumesinde UYUSMUYOR (arena
kare icinde icerde duruyor, arena_x_araligi 122..518 / 640) ve olcum tanim
farkina duyarli cikiyor:

    icerik = tum kare   -> DOGRU %92,7 · TEHLIKELI %3,1
    icerik = arena      -> DOGRU %67,7 · TEHLIKELI %21,2

Iki sayi da AYNI kararlari tarif ediyor; degisen yalnizca kiyas tanimidir.
Dolayisiyla ikisi de tek basina "calisiyor mu" sorusunu yanitlamaz.

BU BETIK tanimdan kurtulur ve gorevin sordugu seyi olcer: URETILEN ROTA, YER
GERCEGI molozunun uzerinden geciyor mu? IKA govdesi noktasal degildir, bu yuzden
rota `r_gerekli_px` ile kalinlastirilir (C-uzayi ile ayni yaricap).

    basma_orani = (kalin rota ∩ GT engel) / (kalin rota)

Sifirdan buyuk her deger, IKA'nin molozla temas etmesi demektir.

Referans: REVIEW_LOG D-90. Olcut secimi mimarin `arena-olcum-araci` notuna
dayanir: "IoU gizli varsayim tasir; asil olcut moloza basma oranidir."
"""
import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

from ayarlar import REPO
# K6 (ON_KAYIT §12): "rota yol ustunde mi" — tanim 142 ile ORTAK (rota_yol_olcumu.py).
from rota_yol_olcumu import (KAPI_B_EK2, rota_yol_olc, uc_durum_maske,
                             yanlis_guzergah_mi)

sys.path.insert(0, str(REPO / "codes"))

from costmap_path_finder import R_GEREKLI_M  # noqa: E402
from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp,  # noqa: E402
                           _preprocess, analyze_path, get_masks)

CONF = 0.30


def etiket_maskesi(txt, h, w):
    """YOLO-seg poligon etiketi -> {sinif: maske}. Yer gercegi budur."""
    m = {0: np.zeros((h, w), np.uint8), 1: np.zeros((h, w), np.uint8)}
    if not txt.is_file():
        return m
    for satir in txt.read_text(encoding="utf-8").splitlines():
        p = satir.split()
        if len(p) < 7:
            continue
        c = int(float(p[0]))
        if c not in m:
            continue
        xy = np.array([float(v) for v in p[1:]], np.float32).reshape(-1, 2)
        xy[:, 0] *= w
        xy[:, 1] *= h
        cv2.fillPoly(m[c], [xy.astype(np.int32)], 1)
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", type=Path, required=True)
    ap.add_argument("--kume", type=Path, required=True)
    ap.add_argument("--json", type=Path, default=None)
    # T150/D-386: uretim artik analyze_path'e goruntu=sq gecirir
    # (varis HB'den). Kabul zinciri uretimi YANSITMALI (D-351);
    # bayrak 65'ten gecilir. Bayraksiz davranis BAYT-ES eskisidir.
    ap.add_argument("--hb-hedefli", action="store_true")
    args = ap.parse_args()

    kok, model_yolu = args.kume, args.model
    man = json.loads((kok / "manifest.json").read_text(encoding="utf-8"))

    from ultralytics import YOLO
    model = YOLO(str(model_yolu), task="segment")

    kayitlar = []
    for ornek in man["ornekler"]:
        if ornek.get("durum") != "YAZILDI" or not ornek.get("arena"):
            continue
        p = kok / ornek["cikti"]
        if not p.is_file():
            continue
        arena = ornek["arena"]
        img = cv2.imread(str(p))
        h0, w0 = img.shape[:2]
        txt = (kok / "labels" / Path(ornek["cikti"]).parent.name
               / (p.stem + ".txt"))
        gt = etiket_maskesi(txt, h0, w0)

        sq, small, icerik = _preprocess(img)
        h, w = sq.shape[:2]
        sonuc = model.predict(small, imgsz=INFER_SIZE, conf=CONF, verbose=False)
        mk = _maskeleri_icerige_kirp(get_masks(sonuc, h, w), icerik)
        trav, blok = mk[0], mk[1]
        mpp = arena.get("mpp")
        yol, guven, wps, _k, red, olcum = analyze_path(
            trav, icerik=icerik, engel_mask=blok, mpp=mpp,
            return_clean=True, return_reason=True, return_olcum=True,
            goruntu=sq if args.hb_hedefli else None)

        kayit = {"kare": p.name, "serit": yol, "guven": guven,
                 "red": (red[0] if isinstance(red, tuple) else red),
                 "basma_orani": None, "arena_disi_orani": None,
                 "yol_payi": None, "engel_wp": None, "yanlis_guzergah": None}
        if red is None and wps:
            # K6 (ON_KAYIT §12) — rota YOL USTUNDE mi: waypoint'ler TUVAL
            # koordinatinda (analyze_path, `sq` = _preprocess letterbox'u,
            # yan = max(h0, w0)); yer gercegi poligonlari AYNI tuvale
            # `uc_durum_maske` ile tasinir (ayni (x0, y0) yerlesimi). Tanim 142
            # ile ortak: 1 px polylines, yol_payi >= 0,90 ve engel_wp == 0.
            uc = uc_durum_maske(txt, h0, w0, yan=h)
            assert uc.shape == (h, w), (uc.shape, (h, w))
            ry = rota_yol_olc(wps, uc)
            kayit["yol_payi"] = ry["yol_payi"]
            kayit["etiketsiz_payi"] = ry["etiketsiz_payi"]
            kayit["engel_wp"] = ry["engel_wp"]
            kayit["wp"] = ry["wp"]
            kayit["yanlis_guzergah"] = yanlis_guzergah_mi(ry)
            r_px = max(1, int(round(R_GEREKLI_M / mpp)))
            # Rota, TUVAL koordinatinda cizilir; sonra icerikten kirpilip
            # ozgun kare boyutuna goturulur (GT ile ayni cerceve).
            iz = np.zeros((h, w), np.uint8)
            pts = [(int(round(x)), int(round(y))) for x, y in wps]
            for a, b in zip(pts, pts[1:]):
                cv2.line(iz, a, b, 1, 2)
            iz = cv2.dilate(iz, cv2.getStructuringElement(
                cv2.MORPH_ELLIPSE, (2 * r_px + 1, 2 * r_px + 1)))
            x0, y0, cw, ch = icerik
            iz = cv2.resize(iz[y0:y0 + ch, x0:x0 + cw], (w0, h0),
                            interpolation=cv2.INTER_NEAREST)
            alan = float(iz.sum())
            if alan > 0:
                kayit["basma_orani"] = float(((iz > 0) & (gt[1] > 0)).sum()) / alan
                ax = arena.get("arena_x_araligi")
                if ax:
                    dis = np.ones((h0, w0), np.uint8)
                    dis[:, max(0, int(ax[0])):min(w0, int(ax[1]))] = 0
                    kayit["arena_disi_orani"] = float(
                        ((iz > 0) & (dis > 0)).sum()) / alan
        kayitlar.append(kayit)

    rotali = [k for k in kayitlar if k["basma_orani"] is not None]
    basan = [k for k in rotali if k["basma_orani"] > 0.0]
    agir = [k for k in rotali if k["basma_orani"] > 0.05]
    disari = [k for k in rotali if (k["arena_disi_orani"] or 0) > 0.10]
    # K6: payda ROTA URETILEN kare (yanlis_guzergah hesaplanmis olanlar).
    yol_olculen = [k for k in kayitlar if k["yanlis_guzergah"] is not None]
    yanlis = [k for k in yol_olculen if k["yanlis_guzergah"]]
    n = len(kayitlar)
    print(f"\nmodel : {model_yolu.name}")
    print(f"kume  : {kok.name}   n = {n}   rota uretilen = {len(rotali)}")
    print("-" * 66)
    print(f"  ROTA URETILDI          {len(rotali):>4} / {n}")
    print(f"  MOLOZA BASIYOR (>0)    {len(basan):>4} / {len(rotali)}"
          f"   %{100 * len(basan) / max(1, len(rotali)):5.1f}   <-- SIFIR OLMALI")
    print(f"  AGIR BASMA   (>%5)     {len(agir):>4} / {len(rotali)}"
          f"   %{100 * len(agir) / max(1, len(rotali)):5.1f}")
    print(f"  ARENA DISINDA (>%10)   {len(disari):>4} / {len(rotali)}"
          f"   %{100 * len(disari) / max(1, len(rotali)):5.1f}")
    print(f"  YANLIS GUZERGAH (K6)   {len(yanlis):>4} / {len(yol_olculen)}"
          f"   %{100 * len(yanlis) / max(1, len(yol_olculen)):5.1f}"
          f"   (yol_payi < {KAPI_B_EK2['yol_payi_min']:.2f} veya engel_wp > "
          f"{KAPI_B_EK2['engel_wp_maks']})")
    if rotali:
        o = np.array([k["basma_orani"] for k in rotali])
        d = np.array([k["arena_disi_orani"] or 0.0 for k in rotali])
        print(f"\n  basma orani   ort %{100 * o.mean():.2f} · "
              f"medyan %{100 * float(np.median(o)):.2f} · maks %{100 * o.max():.2f}")
        print(f"  arena disi    ort %{100 * d.mean():.2f} · "
              f"medyan %{100 * float(np.median(d)):.2f} · maks %{100 * d.max():.2f}")
    print("-" * 66)

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps({
            "model": str(model_yolu), "kume": str(kok), "n": n,
            "rota_uretilen": len(rotali), "basan": len(basan),
            "agir": len(agir), "arena_disi": len(disari),
            "yol_olculen": len(yol_olculen), "yanlis_guzergah": len(yanlis),
            "yanlis_kareler": [k["kare"] for k in yanlis],
            "kapi_rota_yol": dict(KAPI_B_EK2),
            "kayitlar": kayitlar,
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"json -> {args.json}")


if __name__ == "__main__":
    main()
