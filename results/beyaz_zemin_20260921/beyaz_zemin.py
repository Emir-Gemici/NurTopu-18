# BEYAZ ZEMIN DENEYI — ONARIM-04 yordami (bilinen iyi kareyi kontrollu boz, olc).
# Saha beyani (21 Eyl): zemin BEYAZ, engeller kaldirim tasina benzer taslar.
# Kabul kumesinin zemini gri beton; zemini kademeli olarak BEYAZLATIP modelin
# zemin maskesini kaybedip kaybetmedigini olcuyoruz.
import sys, glob, os
sys.path.insert(0, r"O:\navitas")
sys.path.insert(0, r"O:\navitas\codes")
import cv2, numpy as np
import codes.rpi_inference as ri

MPP = 0.0755  # kabul kumesinin gercek olcegi (D-524 ek 1)
model = ri.load_model()
kareler = sorted(glob.glob(r"O:\navitas\data\kabul\sentetik_arena_kadraj_t66\images\val\*.jpg"))[:6]


def beyazlat(bgr, k):
    """k=0 degismez; k=1 tam beyaz. Parlakligi beyaza dogru cek + doygunlugu dusur."""
    if k <= 0:
        return bgr.copy()
    f = bgr.astype(np.float32)
    beyaz = np.full_like(f, 255.0)
    return np.clip(f * (1 - k) + beyaz * k, 0, 255).astype(np.uint8)


def olc(bgr):
    sq, small, icerik = ri._preprocess(bgr)
    res = model.predict(small, imgsz=ri.INFER_SIZE, conf=0.30, verbose=False)
    h, w = sq.shape[:2]
    masks = ri.get_masks(res, h, w)
    ri._maskeleri_icerige_kirp(masks, icerik)
    zemin, engel = masks[0], masks[1]
    ic = icerik[2] * icerik[3]
    yol, guven, wps, ret, _ = ri.analyze_path(
        zemin, icerik=icerik, engel_mask=engel, mpp=MPP,
        return_reason=True, return_olcum=True, goruntu=sq)
    sebep = ret[0] if isinstance(ret, tuple) else ret
    return (100.0 * np.count_nonzero(zemin) / ic,
            100.0 * np.count_nonzero(engel) / ic,
            (ret is None and yol is not None and len(wps) >= 2), sebep)


SEVIYELER = [0.0, 0.15, 0.30, 0.45, 0.60]
print(f"{len(kareler)} kabul karesi · beyazlatma seviyeleri {SEVIYELER}")
print(f"{'beyaz':>6} {'ort zemin%':>11} {'ort engel%':>11} {'rota uretilen':>14}  {'sebepler'}")
for k in SEVIYELER:
    zs, es, rota, sebepler = [], [], 0, {}
    for p in kareler:
        img = beyazlat(cv2.imread(p), k)
        z, e, r, s = olc(img)
        zs.append(z); es.append(e); rota += int(r)
        if s: sebepler[s] = sebepler.get(s, 0) + 1
    print(f"{k:>6.2f} {np.mean(zs):>11.2f} {np.mean(es):>11.2f} {rota:>8}/{len(kareler):<5}  {sebepler or '-'}")
