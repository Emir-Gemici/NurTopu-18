# T142/T135 olcum — kod DEGISTIRMEZ. 65_kabul_denetcisi.kaplama() yolu birebir.
import sys, json, time
from pathlib import Path
import numpy as np, cv2
REPO = Path(r"O:\navitas")
sys.path.insert(0, str(REPO / "codes"))
from rpi_inference import INFER_SIZE, _maskeleri_icerige_kirp, _preprocess, get_masks
import karar_sozlesmesi as ks
from ultralytics import YOLO
CONF = 0.30
assert INFER_SIZE == 512, INFER_SIZE
KUMELER = {
 "a_sentetik_kadraj_t66": sorted(Path(r"O:\navitas-local-train\calisma\sentetik_arena_kadraj_t66\images").rglob("*.jpg")),
 "b_otopark_raw_frames": sorted(Path(r"O:\navitas\data\raw_frames").rglob("*.jpg")),
 "c_dji_0038_val": sorted(Path(r"O:\navitas\dataset\dji_kirsal\images\val").glob("*.jpg")),
 "d_arena_s9": [REPO / "data/arena_referans/sartname_s9_arena.png"],
}
MODELLER = {"v35": REPO/"models/navitas_seg_v35_best.pt", "v24": REPO/"models/navitas_seg_v24_best.pt"}
CIFTLER = [(0.67,0.50),(0.60,0.45),(0.55,0.40),(0.50,0.35)]

def olc(model, p):
    img = cv2.imread(str(p))
    sq, small, icerik = _preprocess(img)
    h, w = sq.shape[:2]
    sonuc = model.predict(small, imgsz=INFER_SIZE, conf=CONF, verbose=False, device=0)
    mk = _maskeleri_icerige_kirp(get_masks(sonuc, h, w), icerik)
    tr = mk[0]
    return {"kare": p.name, "sekil": [int(img.shape[0]), int(img.shape[1])], "icerik": [int(v) for v in icerik],
            "icerik_orani": round(icerik[2]*icerik[3]/(h*w), 4),
            "kap_none": ks.zemin_kaplamasi(tr, None), "ken_none": ks.zemin_kenar_dayanmasi(tr, None),
            "kap_box": ks.zemin_kaplamasi(tr, icerik), "ken_box": ks.zemin_kenar_dayanmasi(tr, icerik)}

def dag(v):
    a = np.array(v, float)
    if a.size == 0: return None
    return {"n": int(a.size), "min": round(a.min(),4), "p05": round(float(np.percentile(a,5)),4),
            "p50": round(float(np.percentile(a,50)),4), "p95": round(float(np.percentile(a,95)),4), "maks": round(a.max(),4)}

out = {"parametreler": {"imgsz": INFER_SIZE, "conf": CONF, "yol": "scripts/olcum/65_kabul_denetcisi.kaplama() (_preprocess->predict->get_masks->_maskeleri_icerige_kirp), sinif 0", "tarih": time.strftime("%Y-%m-%d %H:%M"), "ciftler": CIFTLER}, "kareler": {}, "dagilim": {}, "esik_tablosu": {}}
for mad, myol in MODELLER.items():
    model = YOLO(str(myol))
    for kad, yollar in KUMELER.items():
        t0 = time.time()
        k = [olc(model, p) for p in yollar]
        out["kareler"][f"{mad}/{kad}"] = k
        d = {}
        for alan in ("kap_none","ken_none","kap_box","ken_box"):
            d[alan] = dag([x[alan] for x in k])
        d["icerik_orani"] = dag([x["icerik_orani"] for x in k])
        out["dagilim"][f"{mad}/{kad}"] = d
        tb = {}
        for K,E in CIFTLER:
            for payda in ("none","box"):
                ret = sum(1 for x in k if x[f"kap_{payda}"] > K and x[f"ken_{payda}"] > E)
                sk = sum(1 for x in k if x[f"kap_{payda}"] > K)
                se = sum(1 for x in k if x[f"ken_{payda}"] > E)
                tb[f"{K:.2f}/{E:.2f}/{payda}"] = {"ret_AND": ret, "kaplama_asan": sk, "kenar_asan": se, "n": len(k)}
        out["esik_tablosu"][f"{mad}/{kad}"] = tb
        print(f"{mad} {kad} n={len(k)} {time.time()-t0:.1f}s", flush=True)
        for alan in ("kap_none","ken_none","kap_box","ken_box"):
            print("   ", alan, d[alan], flush=True)
        for c,v in tb.items(): print("   ", c, v, flush=True)
    del model
json.dump(out, open(REPO/"results/t142/olcum.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("YAZILDI results/t142/olcum.json")
