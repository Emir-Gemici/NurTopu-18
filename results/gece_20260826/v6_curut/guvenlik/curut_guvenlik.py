"""LENS 3 GUVENLIK — v6 curutme olcumu. KOD/VERI/REGISTRY DEGISTIRMEZ; yalniz bu klasore yazar."""
import sys, json, time, io
from pathlib import Path
import numpy as np, cv2
KOK = Path(r"O:\navitas")
sys.path.insert(0, str(KOK / "codes"))
from rpi_inference import INFER_SIZE, _preprocess, _maskeleri_icerige_kirp, get_masks, analyze_path
import karar_sozlesmesi as ks
from ultralytics import YOLO
CIK = KOK / "results/gece_20260826/v6_curut/guvenlik"
BIND = CIK / "bindirme"; BIND.mkdir(parents=True, exist_ok=True)
MODELLER = {"v6": KOK / "codes/runs/segment/gece_v6_v35taban/weights/best.pt",
            "v35": KOK / "models/navitas_seg_v35_best.pt"}
TEST = KOK / "dataset/dji_kirsal_0038_bolum_v2/images/test"
LBL = KOK / "dataset/dji_kirsal_0038_bolum_v2/labels/test"
TAVAN = {s["kare"]: s["rota"] for s in json.load(io.open(KOK / "results/gece_20260826/test29_etiket_tavani_v2.json", encoding="utf-8"))["kareler"]}
ARENA = KOK / "data/arena_referans/sartname_s9_arena.png"
SENT = sorted(Path(r"O:\navitas-local-train\calisma\sentetik_arena_kadraj_t66\images").rglob("*.jpg"))
OTO = sorted((KOK / "data/raw_frames").rglob("*.jpg"))
assert INFER_SIZE == 512 and len(SENT) == 260 and len(OTO) == 67, (INFER_SIZE, len(SENT), len(OTO))


def cikar(model, img):
    sq, small, icerik = _preprocess(img)
    h, w = sq.shape[:2]
    r = model.predict(small, imgsz=INFER_SIZE, conf=0.30, verbose=False, device=0)
    mk = _maskeleri_icerige_kirp(get_masks(r, h, w), icerik)
    return sq, icerik, mk


def etiket_maske(p, icerik, h, w):
    """YOLO poligon etiketi -> letterbox tuvalde sinif0 / sinif1 maskeleri."""
    x0, y0, cw, ch = icerik
    m0 = np.zeros((h, w), np.uint8); m1 = np.zeros((h, w), np.uint8)
    t = LBL / (p.stem + ".txt")
    if not t.is_file():
        return m0, m1, False
    for sat in t.read_text().split("\n"):
        v = sat.split()
        if len(v) < 7: continue
        c = int(v[0]); pts = np.array(v[1:], float).reshape(-1, 2)
        pts[:, 0] = x0 + pts[:, 0] * cw; pts[:, 1] = y0 + pts[:, 1] * ch
        cv2.fillPoly(m0 if c == 0 else m1, [pts.astype(np.int32)], 1)
    return m0, m1, True


def bindir(ad, p, sq, mk, clean, wps, m0, m1, sebep):
    g = sq.copy()
    ov = g.copy()
    ov[mk[0] > 0] = (0, 200, 0)
    ov[mk[1] > 0] = (0, 0, 200)
    g = cv2.addWeighted(g, 0.55, ov, 0.45, 0)
    cs, _ = cv2.findContours(m0.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(g, cs, -1, (255, 200, 0), 2)  # etiket sinif0: mavi kontur
    if clean is not None:
        cc, _ = cv2.findContours((np.asarray(clean) > 0).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(g, cc, -1, (255, 255, 255), 1)
    if wps:
        pts = np.array(wps, np.int32)
        cv2.polylines(g, [pts], False, (0, 255, 255), 3)
        for x, y in wps: cv2.circle(g, (int(x), int(y)), 6, (0, 255, 255), -1)
    cv2.putText(g, f"{ad} {p.name[-24:-4]} {sebep}", (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    return g


out = {"test29": {}, "arena": {}, "t142": {}}
for mad, myol in MODELLER.items():
    model = YOLO(str(myol), task="segment")
    # ---- (2) test29 bindirme + etiket uyumu
    satirlar = []
    for p in sorted(TEST.glob("*.jpg")):
        img = cv2.imread(str(p)); sq, icerik, mk = cikar(model, img); h, w = sq.shape[:2]
        y = analyze_path(mk[0], icerik=icerik, engel_mask=mk[1], mpp=None, return_clean=True, return_reason=True, return_olcum=True)
        yol, guven, wps, clean, red, olcum = y
        sebep = red[0] if isinstance(red, tuple) else red
        m0, m1, var = etiket_maske(p, icerik, h, w)
        s = {"kare": p.name, "sebep": sebep, "yol": yol, "wp": len(wps) if wps else 0, "tavan": TAVAN.get(p.name),
             "zemin_orani": round(float(ks.zemin_kaplamasi(mk[0] > 0, icerik)), 4),
             "kenar": round(float(ks.zemin_kenar_dayanmasi(mk[0] > 0, icerik)), 4), "etiket_var": var}
        tr = mk[0] > 0
        s["maske0_etiket0_icinde"] = round(float((tr & (m0 > 0)).sum() / max(1, tr.sum())), 4)   # v6 zemin maskesinin ne kadari etiketli yol
        s["maske0_etiket1_icinde"] = round(float((tr & (m1 > 0)).sum() / max(1, tr.sum())), 4)
        s["maske0_etiketsiz"] = round(float((tr & (m0 == 0) & (m1 == 0)).sum() / max(1, tr.sum())), 4)
        if wps:
            wp_ok = sum(1 for x, yy in wps if m0[int(min(max(yy, 0), h - 1)), int(min(max(x, 0), w - 1))] > 0)
            s["wp_etiket0_ustunde"] = f"{wp_ok}/{len(wps)}"
            # waypoint'ler arasi cizgi pikselleri
            cz = np.zeros((h, w), np.uint8); cv2.polylines(cz, [np.array(wps, np.int32)], False, 1, 1)
            s["rota_cizgi_etiket0_orani"] = round(float(((cz > 0) & (m0 > 0)).sum() / max(1, (cz > 0).sum())), 4)
            s["rota_cizgi_etiketsiz_orani"] = round(float(((cz > 0) & (m0 == 0) & (m1 == 0)).sum() / max(1, (cz > 0).sum())), 4)
            cl = np.asarray(clean) > 0
            s["temiz_koridor_etiket0_orani"] = round(float((cl & (m0 > 0)).sum() / max(1, cl.sum())), 4)
        if wps or sebep == "ZEMIN_MASKESI_SUPHELI" or mad == "v6":
            cv2.imwrite(str(BIND / f"{mad}_{p.stem[-24:]}.jpg"), bindir(mad, p, sq, mk, clean, wps, m0, m1, sebep), [cv2.IMWRITE_JPEG_QUALITY, 85])
        satirlar.append(s)
    out["test29"][mad] = satirlar
    # ---- (3) arena figuru
    img = cv2.imread(str(ARENA)); sq, icerik, mk = cikar(model, img); h, w = sq.shape[:2]
    y = analyze_path(mk[0], icerik=icerik, engel_mask=mk[1], mpp=None, return_clean=True, return_reason=True, return_olcum=True)
    yol, guven, wps, clean, red, olcum = y
    out["arena"][mad] = {"kaplama_icerik": round(float(ks.zemin_kaplamasi(mk[0] > 0, icerik)), 4),
                         "kaplama_tuval": round(float(ks.zemin_kaplamasi(mk[0] > 0, None)), 4),
                         "engel_icerik": round(float(ks.zemin_kaplamasi(mk[1] > 0, icerik)), 4),
                         "yol": yol, "wp": len(wps) if wps else 0, "sebep": (red[0] if isinstance(red, tuple) else red),
                         "detay": (red[1][:200] if isinstance(red, tuple) else None)}
    cv2.imwrite(str(BIND / f"{mad}_arena_s9.jpg"), bindir(mad, ARENA, sq, mk, clean, wps, np.zeros((h, w), np.uint8), None, out["arena"][mad]["sebep"]))
    # ---- (4) T142 dagilimi
    for kad, yollar in (("sentetik260", SENT), ("otopark67", OTO)):
        kap_b, ken_b, kap_n, ken_n = [], [], [], []
        for p in yollar:
            img = cv2.imread(str(p)); sq, icerik, mk = cikar(model, img); tr = mk[0]
            kap_b.append(ks.zemin_kaplamasi(tr, icerik)); ken_b.append(ks.zemin_kenar_dayanmasi(tr, icerik))
            kap_n.append(ks.zemin_kaplamasi(tr, None)); ken_n.append(ks.zemin_kenar_dayanmasi(tr, None))
        kb, eb, kn, en = map(np.array, (kap_b, ken_b, kap_n, ken_n))
        def d(a): return {"min": round(float(a.min()), 4), "p50": round(float(np.median(a)), 4), "p95": round(float(np.percentile(a, 95)), 4), "maks": round(float(a.max()), 4)}
        out["t142"][f"{mad}/{kad}"] = {"n": len(yollar), "kap_box": d(kb), "ken_box": d(eb), "kap_none": d(kn), "ken_none": d(en),
                                       "ret_AND_0.55_0.40_box": int(((kb > 0.55) & (eb > 0.40)).sum()),
                                       "kaplama_asan_box": int((kb > 0.55).sum()), "kenar_asan_box": int((eb > 0.40).sum()),
                                       "kenar_0.35_0.40_arasi_box": int(((eb > 0.35) & (eb <= 0.40)).sum()),
                                       "ret_AND_0.55_0.40_none": int(((kn > 0.55) & (en > 0.40)).sum())}
        print(mad, kad, out["t142"][f"{mad}/{kad}"], flush=True)
    del model
json.dump(out, io.open(CIK / "olcum.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("YAZILDI", CIK / "olcum.json")
