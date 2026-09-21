# Tam karar zinciri olcumu: kare -> v36 -> maske -> analyze_path -> waypoint
# Uretim cagri bicimi codes/rpi_inference.py:2003 ile ayni; kapi bicimi
# codes/test_rota_sentetik.py:161 ile ayni (mpp=0.10).
import sys, glob, os, json
sys.path.insert(0, r"O:\navitas")
sys.path.insert(0, r"O:\navitas\codes")
import cv2, numpy as np
import codes.rpi_inference as ri

model = ri.load_model()
KARELER = sys.argv[1:]

print(f"INFER_SIZE={ri.INFER_SIZE}  |  kapi mpp=0.10\n")
for p in KARELER:
    img = cv2.imread(p)
    if img is None:
        print(f"{os.path.basename(p)}: OKUNAMADI"); continue
    tuval, small, icerik = ri._preprocess(img)
    res = model.predict(small, imgsz=ri.INFER_SIZE, conf=0.30, verbose=False)
    h, w = tuval.shape[:2]
    masks = ri.get_masks(res, h, w, min_conf=None)
    ri._maskeleri_icerige_kirp(masks, icerik)
    zemin, engel = masks.get(0), masks.get(1)
    zp, ep = int(np.count_nonzero(zemin)), int(np.count_nonzero(engel))
    ic_px = icerik[2] * icerik[3]
    print(f"=== {os.path.basename(p)}")
    print(f"    maske: zemin {zp} px (%{100*zp/ic_px:.2f}) · engel {ep} px (%{100*ep/ic_px:.2f})")
    for etiket, mpp, goruntu in (("mpp=0.10 (kapi degeri)", 0.10, None),
                                 ("mpp=None (sahada gorulen)", None, None),
                                 ("mpp=0.0755 + goruntu (uretim)", 0.0755, tuval)):
        kw = dict(icerik=icerik, engel_mask=engel, mpp=mpp,
                  return_reason=True, return_olcum=True)
        if goruntu is not None:
            kw["goruntu"] = goruntu
        try:
            yol, guven, wps, ret, olcum = ri.analyze_path(zemin, **kw)
            sebep = ret[0] if isinstance(ret, tuple) else ret
            aciklama = (ret[1][:90] if isinstance(ret, tuple) and len(ret) > 1 else "")
            rota_var = ret is None and yol is not None and len(wps) >= 2
            print(f"    [{etiket:28s}] rota_var={rota_var}  serit={yol}  guven={guven:.3f}  "
                  f"wp={len(wps)}  ret={sebep}")
            if aciklama:
                print(f"        -> {aciklama}")
        except Exception as e:
            print(f"    [{etiket:28s}] ISTISNA: {type(e).__name__}: {e}")
    print()
