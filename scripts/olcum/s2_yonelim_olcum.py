"""S2 — YONELIM OLCUMU: K-A uc-bant kapisi rota eksenine gore.

ON KAYIT: results/gece_20260826/ON_KAYIT.md SS5 (bu betik yazilmadan once).

UC OLCUM:
  A) dji_kirsal val (0038, 59 kare) · v35 (imgsz kayit defteri, conf 0,30)
     · cikarim yolu 126_t138_gece_kumesi.py ile BIREBIR (_preprocess ->
     predict -> get_masks -> _maskeleri_icerige_kirp) · analyze_path
     eksen ∈ {None, 0, 90} · olceksiz (uretim) ve olcek BEDAVA (mpp 0,01).
     "en iyi eksen" tavani = 0 VEYA 90'da rota uretilen kare sayisi
     (yalniz OLCUM; uretime GIRMEZ).
  B) Ayni 59 kare · ELLE etiket (YOLO poligon -> letterbox tuvalinde maske;
     sinif 0 -> trav, sinif 1 -> engel) · ayni eksenler.
  C) Sentetik kabul kumesi sentetik_arena_kadraj_t66 (n=260) · v35 ·
     61_rota_moloza_basma.py'nin cagrisiyla BIREBIR (mpp manifestten) ·
     eksen None ve 0 · K1 rota sayisi AYNI mi (bayt-es beklenir: karar,
     guven, waypoint, temiz maske).

REGISTRY'YE YAZMAZ, ESIK DEGISTIRMEZ, dataset/ altina YAZMAZ.
"""
from __future__ import annotations

import collections
import io
import json
import sys
import time
from pathlib import Path

BURASI = Path(__file__).resolve()
KOK = BURASI.parents[2]                       # worktree koku (cikti buraya)
ANA = Path(r"O:\navitas")                     # modeller/veri SALT OKUNUR
CIKTI = KOK / "results" / "s2_yonelim"
MODEL = ANA / "models" / "navitas_seg_v35_best.pt"
DJI_IMG = ANA / "dataset" / "dji_kirsal" / "images" / "val"
DJI_LBL = ANA / "dataset" / "dji_kirsal" / "labels" / "val"
SENTETIK = Path(r"O:\navitas-local-train\calisma\sentetik_arena_kadraj_t66")
CONF = 0.30
MPP_BEDAVA = 0.01
EKSENLER = (None, 0, 90)


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError, OSError):
        pass
    sys.path.insert(0, str(KOK / "codes"))
    import numpy as np                                        # noqa: E402
    import cv2                                                # noqa: E402
    from rpi_inference import (_preprocess, _maskeleri_icerige_kirp,  # noqa: E402
                               get_masks, analyze_path, INFER_SIZE)
    from ultralytics import YOLO                              # noqa: E402

    def karar(trav, engel, icerik, mpp, eksen):
        y = analyze_path(trav, icerik=icerik, engel_mask=engel, mpp=mpp,
                         return_clean=True, return_reason=True,
                         return_olcum=True, rota_ekseni_derece=eksen)
        yol, guven, wps, clean, red, olcum = y
        sebep = red[0] if isinstance(red, tuple) else red
        return {"yol": yol, "guven": round(float(guven), 4), "wp": len(wps),
                "sebep": sebep, "_wps": wps, "_clean": clean}

    def etiket_maskesi(txt, h0, w0, icerik):
        """YOLO poligon -> letterbox tuvali (kare) maskesi, iki sinif."""
        x0, y0, _, _ = icerik
        yan = max(h0, w0)
        mk = {0: np.zeros((yan, yan), np.uint8), 1: np.zeros((yan, yan), np.uint8)}
        if not txt.is_file():
            return mk
        for satir in txt.read_text(encoding="utf-8").splitlines():
            par = satir.split()
            if len(par) < 7:
                continue
            sinif = int(par[0])
            if sinif not in mk:
                continue
            xy = np.array(par[1:], dtype=np.float64).reshape(-1, 2)
            pts = np.stack([xy[:, 0] * w0 + x0, xy[:, 1] * h0 + y0], 1)
            cv2.fillPoly(mk[sinif], [np.round(pts).astype(np.int32)], 1)
        return mk

    print(f"model {MODEL.name} · imgsz {INFER_SIZE} · conf {CONF}")
    model = YOLO(str(MODEL), task="segment")

    # ── A + B: DJI 0038 ────────────────────────────────────────────────────
    kareler = sorted(DJI_IMG.glob("*.jpg"))
    print(f"\nA/B) dji_kirsal val: {len(kareler)} kare")
    # KISMI KAYIT (kare basina ~60 sn; surec kesilirse kaldigi yerden surer,
    # sonuc DEGISMEZ: her kare bagimsiz hesaplanir)
    CIKTI.mkdir(parents=True, exist_ok=True)
    kismi = CIKTI / "kareler_kismi.jsonl"
    satirlar = []
    if kismi.is_file():
        satirlar = [json.loads(x) for x in
                    kismi.read_text(encoding="utf-8").splitlines() if x.strip()]
    hazir = {s["kare"] for s in satirlar}
    t0 = time.perf_counter()
    for p in kareler:
        if p.name in hazir:
            continue
        img = cv2.imread(str(p))
        sq, small, icerik = _preprocess(img)
        h, w = sq.shape[:2]
        sonuc = model.predict(small, imgsz=INFER_SIZE, conf=CONF, verbose=False)
        mk = _maskeleri_icerige_kirp(get_masks(sonuc, h, w), icerik)
        gt = etiket_maskesi(DJI_LBL / (p.stem + ".txt"), *img.shape[:2], icerik)
        satir = {"kare": p.name}
        for kaynak, m in (("v35", mk), ("etiket", gt)):
            for kip, mpp in (("olceksiz", None), ("olcekli", MPP_BEDAVA)):
                for eksen in EKSENLER:
                    k = karar(m[0], m[1], icerik, mpp, eksen)
                    # madde 15 denetimi: geri cevrilen waypoint'ler orijinal
                    # ham serbest maskede mi (eksen None/0'da da ayni sinama)
                    wps = k.pop("_wps"); clean = k.pop("_clean")
                    k["wp_serbest_disi"] = int(sum(
                        1 for x, y in wps if not m[0][y, x] > 0))
                    k["wp_clean_disi"] = int(sum(
                        1 for x, y in wps if not clean[y, x] > 0))
                    satir[f"{kaynak}/{kip}/{eksen}"] = k
        satirlar.append(satir)
        with io.open(kismi, "a", encoding="utf-8") as f:
            f.write(json.dumps(satir, ensure_ascii=False) + "\n")
        print(f"  {p.name} · {len(satirlar)}/{len(kareler)} · "
              f"{time.perf_counter() - t0:.0f} sn", flush=True)
    satirlar.sort(key=lambda s: s["kare"])
    sure_ab = time.perf_counter() - t0

    ozet_ab = {}
    for kaynak in ("v35", "etiket"):
        for kip in ("olceksiz", "olcekli"):
            o = {}
            for eksen in EKSENLER:
                anahtar = f"{kaynak}/{kip}/{eksen}"
                rota = [s["kare"] for s in satirlar if s[anahtar]["yol"] is not None]
                sebepler = collections.Counter(s[anahtar]["sebep"] for s in satirlar)
                o[str(eksen)] = {"rota": len(rota), "sebep": dict(sebepler),
                                 "wp_serbest_disi_toplam": sum(
                                     s[anahtar]["wp_serbest_disi"] for s in satirlar),
                                 "wp_clean_disi_toplam": sum(
                                     s[anahtar]["wp_clean_disi"] for s in satirlar)}
            r0 = {s["kare"] for s in satirlar if s[f"{kaynak}/{kip}/0"]["yol"] is not None}
            r90 = {s["kare"] for s in satirlar if s[f"{kaynak}/{kip}/90"]["yol"] is not None}
            rn = {s["kare"] for s in satirlar if s[f"{kaynak}/{kip}/None"]["yol"] is not None}
            o["None_eq_0"] = (rn == r0) and all(
                s[f"{kaynak}/{kip}/None"] == s[f"{kaynak}/{kip}/0"] for s in satirlar)
            o["en_iyi_eksen_tavani"] = len(r0 | r90)
            o["yalniz_0"] = len(r0 - r90)
            o["yalniz_90"] = len(r90 - r0)
            o["ikisi_de"] = len(r0 & r90)
            ozet_ab[f"{kaynak}/{kip}"] = o
            print(f"  {kaynak:7s} {kip:9s}: rota None={o['None']['rota']} 0={o['0']['rota']} "
                  f"90={o['90']['rota']} · tavan(0∪90)={o['en_iyi_eksen_tavani']} "
                  f"(yalniz0 {o['yalniz_0']} · yalniz90 {o['yalniz_90']} · "
                  f"ikisi {o['ikisi_de']}) · None==0: {o['None_eq_0']}")
            print(f"           sebep@0  {o['0']['sebep']}")
            print(f"           sebep@90 {o['90']['sebep']}")
    print(f"  sure {sure_ab:.0f} sn")

    # ── C: sentetik kabul kumesi, K1 ───────────────────────────────────────
    man = json.loads((SENTETIK / "manifest.json").read_text(encoding="utf-8"))
    print(f"\nC) sentetik kabul kumesi: {len(man['ornekler'])} ornek")
    t0 = time.perf_counter()
    k1 = {"None": 0, "0": 0}
    n = 0
    bayt_es = True
    farklar = []
    for ornek in man["ornekler"]:
        if ornek.get("durum") != "YAZILDI" or not ornek.get("arena"):
            continue
        p = SENTETIK / ornek["cikti"]
        if not p.is_file():
            continue
        n += 1
        img = cv2.imread(str(p))
        sq, small, icerik = _preprocess(img)
        h, w = sq.shape[:2]
        sonuc = model.predict(small, imgsz=INFER_SIZE, conf=CONF, verbose=False)
        mk = _maskeleri_icerige_kirp(get_masks(sonuc, h, w), icerik)
        mpp = ornek["arena"].get("mpp")
        ya = analyze_path(mk[0], icerik=icerik, engel_mask=mk[1], mpp=mpp,
                          return_clean=True, return_reason=True, return_olcum=True)
        yb = analyze_path(mk[0], icerik=icerik, engel_mask=mk[1], mpp=mpp,
                          return_clean=True, return_reason=True, return_olcum=True,
                          rota_ekseni_derece=0)
        if ya[4] is None:
            k1["None"] += 1
        if yb[4] is None:
            k1["0"] += 1
        ayni = (ya[0] == yb[0] and ya[1] == yb[1] and ya[2] == yb[2]
                and np.array_equal(ya[3], yb[3])
                and (ya[4] == yb[4] if ya[4] is None else ya[4][0] == yb[4][0]))
        if not ayni:
            bayt_es = False
            farklar.append({"kare": p.name, "None": [ya[0], ya[1], len(ya[2]),
                                                     ya[4] and ya[4][0]],
                            "0": [yb[0], yb[1], len(yb[2]), yb[4] and yb[4][0]]})
    sure_c = time.perf_counter() - t0
    print(f"  n={n} · K1 rota None={k1['None']} 0={k1['0']} · karar/guven/wp/clean "
          f"bayt-es: {bayt_es} ({len(farklar)} fark) · sure {sure_c:.0f} sn")

    CIKTI.mkdir(parents=True, exist_ok=True)
    io.open(CIKTI / "olcum.json", "w", encoding="utf-8").write(json.dumps({
        "_ne": "S2 yonelim: K-A uc-bant kapisi rota eksenine gore",
        "_on_kayit": "results/gece_20260826/ON_KAYIT.md SS5",
        "_model": str(MODEL), "_imgsz": INFER_SIZE, "_conf": CONF,
        "_mpp_bedava": MPP_BEDAVA, "_eksenler": [str(e) for e in EKSENLER],
        "dji_0038": {"n": len(satirlar), "sure_sn": round(sure_ab, 1),
                     "ozet": ozet_ab, "kareler": satirlar},
        "sentetik_t66": {"n": n, "K1": k1, "bayt_es": bayt_es,
                         "farklar": farklar, "sure_sn": round(sure_c, 1)},
    }, ensure_ascii=False, indent=1))
    print(f"yazildi: {CIKTI / 'olcum.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
