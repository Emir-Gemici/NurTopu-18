"""ON_KAYIT §12 — engel->zemin SIZINTI olcumu (kapi DEGIL). Uretim cikarim yolu 126 ile ayni:
_preprocess -> predict(imgsz INFER_SIZE, conf 0.30) -> get_masks -> _maskeleri_icerige_kirp.
Maske tuvalden icerik kutusuyla kesilir, 960x540'a INTER_NEAREST kucultulur ve
t152_uzlasi/<govde>_uc.png (0 etiketsiz / 1 sinif0 / 2 sinif1) ile kesistirilir.
Yalniz results/gece_20260826/sizinti/ altina yazar. Esik yok, hukum yok.
"""
from __future__ import annotations
import io, json, sys, time
from pathlib import Path
import numpy as np, cv2

KOK = Path(r"O:\navitas")
sys.path.insert(0, str(KOK / "codes"))
from rpi_inference import _preprocess, _maskeleri_icerige_kirp, get_masks, INFER_SIZE  # noqa
from ultralytics import YOLO  # noqa

R = KOK / "results" / "gece_20260826"
UZ = R / "t152_uzlasi"
KARE = KOK / "results" / "dji_20260822" / "kareler_1fps"
V3 = KOK / "dataset" / "dji_kirsal_0038_bolum_v3" / "images"
CIK = R / "sizinti"
MODELLER = {
    # D-305: URETIM modeli v36 bu tabloda YOKTU; terfi (D-294) sizintiyi hic
    # olcmemisti. Beton kanal <-> toprak yol karisikligi tam bu olcumun konusu.
    "v36": KOK / "models" / "navitas_seg_v36_best.pt",
    "v35": KOK / "models" / "navitas_seg_v35_best.pt",
    "v3": KOK / "codes" / "runs" / "segment" / "gece_v3_v35taban" / "weights" / "best.pt",
    "v6": KOK / "codes" / "runs" / "segment" / "gece_v6_v35taban" / "weights" / "best.pt",
}
W, H = 960, 540


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    bolum = {p.stem: "test29" for p in (V3 / "test").glob("*.jpg")}
    bolum.update({p.stem: "val82" for p in (V3 / "val").glob("*.jpg")})
    govdeler = sorted(p.name[:-7] for p in UZ.glob("*_uc.png"))
    assert len(govdeler) == 111, len(govdeler)
    gt = {}
    for g in govdeler:
        m = np.squeeze(cv2.imread(str(UZ / (g + "_uc.png")), cv2.IMREAD_GRAYSCALE))
        assert m.shape == (H, W) and set(np.unique(m).tolist()) <= {0, 1, 2}, g
        gt[g] = m
    print(f"kare {len(govdeler)} · test29 {sum(bolum[g]=='test29' for g in govdeler)} · val82 {sum(bolum[g]=='val82' for g in govdeler)} · imgsz {INFER_SIZE}")
    cikti = {"_ne": "ON_KAYIT §12 sizinti olcumu (kapi degil)", "_referans": str(UZ), "_kareler": str(KARE),
             "_cikarim": f"_preprocess -> predict(imgsz={INFER_SIZE}, conf=0.30) -> get_masks -> _maskeleri_icerige_kirp; icerik kesme + INTER_NEAREST 960x540",
             "_tanim": {"sizinti": "|GT sinif1 & model zemin| / |GT sinif1|",
                        "geri_cagirma": "|GT sinif0 & model zemin| / |GT sinif0|",
                        "etiketsiz_payi": "|GT etiketsiz & model zemin| / |model zemin|"},
             "modeller": {}}
    # D-305: yalniz belirli modelleri kosmak icin (eski olcum EZILMESIN diye
    # cikti adi da secilen kumeye gore ayrisir).
    secim = [a for a in sys.argv[1:] if not a.startswith("-")]
    modeller = ({a: MODELLER[a] for a in secim} if secim else MODELLER)
    for ad, yol in modeller.items():
        model = YOLO(str(yol), task="segment")
        t0 = time.perf_counter()
        satirlar = []
        for g in govdeler:
            kaynak, frame = g.split("__")
            img = cv2.imread(str(KARE / kaynak / (frame + ".jpg")))
            assert img is not None, g
            sq, small, icerik = _preprocess(img)
            h, w = sq.shape[:2]
            son = model.predict(small, imgsz=INFER_SIZE, conf=0.30, verbose=False)
            mk = _maskeleri_icerige_kirp(get_masks(son, h, w), icerik)
            x0, y0, cw, ch = icerik
            zem = (mk[0][y0:y0 + ch, x0:x0 + cw] > 0).astype(np.uint8)
            zem = cv2.resize(zem, (W, H), interpolation=cv2.INTER_NEAREST) > 0
            u = gt[g]
            g1, g0, ge = u == 2, u == 1, u == 0
            n1, n0, nz = int(g1.sum()), int(g0.sum()), int(zem.sum())
            s1, s0, se = int((g1 & zem).sum()), int((g0 & zem).sum()), int((ge & zem).sum())
            satirlar.append({"govde": g, "bolum": bolum[g],
                             "gt1": n1, "gt0": n0, "gt_etiketsiz": int(ge.sum()), "model_zemin": nz,
                             "gt1_zemin": s1, "gt0_zemin": s0, "etiketsiz_zemin": se,
                             "sizinti": round(s1 / n1, 4) if n1 else None,
                             "geri_cagirma": round(s0 / n0, 4) if n0 else None,
                             "etiketsiz_payi": round(se / nz, 4) if nz else None})
        sure = time.perf_counter() - t0
        ozet = {}
        for b in ("hepsi", "test29", "val82"):
            S = [s for s in satirlar if b == "hepsi" or s["bolum"] == b]
            def top(a, p):
                pa = sum(s[p] for s in S); return round(sum(s[a] for s in S) / pa, 4) if pa else None
            def med(k):
                v = [s[k] for s in S if s[k] is not None]; return round(float(np.median(v)), 4) if v else None
            def ort(k):
                v = [s[k] for s in S if s[k] is not None]; return round(float(np.mean(v)), 4) if v else None
            ozet[b] = {"n": len(S),
                       "sizinti_toplam_px": top("gt1_zemin", "gt1"), "sizinti_kare_medyan": med("sizinti"), "sizinti_kare_ort": ort("sizinti"),
                       "sizinti_kare_n": sum(1 for s in S if s["sizinti"] is not None),
                       "geri_cagirma_toplam_px": top("gt0_zemin", "gt0"), "geri_cagirma_kare_medyan": med("geri_cagirma"), "geri_cagirma_kare_ort": ort("geri_cagirma"),
                       "geri_cagirma_kare_n": sum(1 for s in S if s["geri_cagirma"] is not None),
                       "etiketsiz_payi_toplam_px": top("etiketsiz_zemin", "model_zemin"), "etiketsiz_payi_kare_medyan": med("etiketsiz_payi"), "etiketsiz_payi_kare_ort": ort("etiketsiz_payi"),
                       "model_zemin_bos_kare": sum(1 for s in S if s["model_zemin"] == 0)}
        # en kotu 5 sizinti (kare basina pay; esitlikte piksel sayisi)
        kotu = sorted([s for s in satirlar if s["sizinti"] is not None], key=lambda s: (-s["sizinti"], -s["gt1_zemin"]))[:5]
        (CIK / f"kotu5_{ad}").mkdir(parents=True, exist_ok=True)
        for i, s in enumerate(kotu, 1):
            g = s["govde"]; kaynak, frame = g.split("__")
            img = cv2.imread(str(KARE / kaynak / (frame + ".jpg")))
            sq, small, icerik = _preprocess(img); h, w = sq.shape[:2]
            son = model.predict(small, imgsz=INFER_SIZE, conf=0.30, verbose=False)
            mk = _maskeleri_icerige_kirp(get_masks(son, h, w), icerik)
            x0, y0, cw, ch = icerik
            zem = cv2.resize((mk[0][y0:y0 + ch, x0:x0 + cw] > 0).astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST) > 0
            kucuk = cv2.resize(img, (W, H), interpolation=cv2.INTER_AREA)
            g1 = gt[g] == 2
            ov = kucuk.copy()
            ov[g1 & ~zem] = (0, 0, 255); ov[zem & ~g1] = (0, 255, 0); ov[g1 & zem] = (0, 255, 255)
            bind = cv2.addWeighted(kucuk, 0.5, ov, 0.5, 0)
            cv2.putText(bind, f"{ad} #{i} {g} sizinti {s['sizinti']:.2f} ({s['gt1_zemin']}/{s['gt1']} px) {s['bolum']}", (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
            cv2.imwrite(str(CIK / f"kotu5_{ad}" / f"{i}_{g}.jpg"), np.vstack([kucuk, bind]))
        cikti["modeller"][ad] = {"agirlik": str(yol), "sure_sn": round(sure, 1), "ozet": ozet,
                                 "kotu5": [{k: s[k] for k in ("govde", "bolum", "sizinti", "gt1_zemin", "gt1")} for s in kotu],
                                 "kareler": satirlar}
        print(f"== {ad} ({sure:.0f} sn)")
        for b, o in ozet.items():
            print(f"  {b:7s} n={o['n']:3d} sizinti px {o['sizinti_toplam_px']} med {o['sizinti_kare_medyan']} | geri px {o['geri_cagirma_toplam_px']} med {o['geri_cagirma_kare_medyan']} | etiketsiz px {o['etiketsiz_payi_toplam_px']} med {o['etiketsiz_payi_kare_medyan']} | zemin bos {o['model_zemin_bos_kare']}")
        print("  kotu5:", [(s["govde"][-16:], s["sizinti"]) for s in kotu])
    ad_dosya = ("olcum_sizinti.json" if not secim
                else "olcum_sizinti_" + "_".join(secim) + ".json")
    (CIK / ad_dosya).write_text(json.dumps(cikti, indent=1, ensure_ascii=False), encoding="utf-8")
    print("yazildi:", CIK / ad_dosya)


if __name__ == "__main__":
    main()
