# BEYAZ ZEMIN DENEYI 2 — yalniz ZEMIN beyazlatilir; engeller ve HB DOKUNULMAZ.
# Saha beyani (21 Eyl): zemin BEYAZ, engeller kaldirim tasi benzeri taslar.
# Yer gercegi poligonlari (sinif 0 = zemin) kullanilir, boylece deney "beyaz zemin +
# degismemis engel" durumunu tasilar. ONARIM-04 yordami: bilinen iyi kareyi kontrollu boz.
import sys, glob, os
sys.path.insert(0, r"O:\navitas")
sys.path.insert(0, r"O:\navitas\codes")
import cv2, numpy as np
import codes.rpi_inference as ri

MPP = 0.0755
model = ri.load_model()
KOK = r"O:\navitas\data\kabul\sentetik_arena_kadraj_t66"
kareler = sorted(glob.glob(os.path.join(KOK, "images", "val", "*.jpg")))[:6]


def zemin_maskesi_gt(etiket_yolu, h, w):
    m = np.zeros((h, w), np.uint8)
    if not os.path.exists(etiket_yolu):
        return None
    for satir in open(etiket_yolu):
        parca = satir.split()
        if not parca or parca[0] != "0":
            continue
        ks = np.array([float(x) for x in parca[1:]], np.float32).reshape(-1, 2)
        ks[:, 0] *= w; ks[:, 1] *= h
        cv2.fillPoly(m, [ks.astype(np.int32)], 1)
    return m


def zemini_beyazlat(bgr, gt, k, hb_kutu=None):
    if k <= 0:
        return bgr.copy()
    gt = gt.copy()
    if hb_kutu is not None:            # HB zemin poligonunun ICINDE; korunur
        x, y, w_, h_ = hb_kutu
        pay = 4
        gt[max(0, y-pay):y+h_+pay, max(0, x-pay):x+w_+pay] = 0
    f = bgr.astype(np.float32)
    beyaz = np.full_like(f, 255.0)
    karisim = np.clip(f * (1 - k) + beyaz * k, 0, 255)
    m3 = np.repeat(gt[:, :, None], 3, axis=2).astype(bool)
    return np.where(m3, karisim, f).astype(np.uint8)


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


print("yalniz ZEMIN beyazlatilir (yer gercegi sinif 0); engel ve HB aynen kalir\n")
print(f"{'beyaz':>6} {'ort zemin%':>11} {'ort engel%':>11} {'rota':>9}  sebepler")
for k in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0):
    zs, es, rota, sebepler = [], [], 0, {}
    for p in kareler:
        img = cv2.imread(p)
        gt = zemin_maskesi_gt(os.path.join(KOK, "labels", "val",
                                           os.path.basename(p).replace(".jpg", ".txt")),
                              *img.shape[:2])
        from karar_sozlesmesi import hb_konumu
        hb = hb_konumu(img, mpp=None, sekil_esigi=None)
        z, e, r, s = olc(zemini_beyazlat(img, gt, k, hb["kutu"] if hb else None))
        zs.append(z); es.append(e); rota += int(r)
        if s: sebepler[s] = sebepler.get(s, 0) + 1
    print(f"{k:>6.2f} {np.mean(zs):>11.2f} {np.mean(es):>11.2f} {rota:>5}/{len(kareler):<3}  {sebepler or '-'}")
