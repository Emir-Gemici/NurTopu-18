# -*- coding: utf-8 -*-
"""T150 (4) — URETIME BAGLAMA MALIYETI. GPU YOK: analyze_path YER GERCEGI
maskesiyle kosulur (segmentasyon modeli devre disi). Iki kip kare kare
karsilastirilir:  goruntu=None (BUGUNKU URETIM)  vs  goruntu=im (T72 baglanmis).
Yer gercegi maskesi = MUKEMMEL ALGI ust siniri; gercek modelle sayilar ancak
DAHA KOTU olur."""
import glob, json, os, sys
import numpy as np, cv2
KOK = r"O:\navitas"
sys.path.insert(0, os.path.join(KOK, "codes"))
from rpi_inference import analyze_path
from karar_sozlesmesi import hb_konumu

KUME = r"O:\navitas-local-train\calisma\sentetik_arena_kadraj_t66"
CIK = os.path.join(KOK, "results", "t150")
man = json.load(open(os.path.join(KUME, "manifest.json"), encoding="utf-8"))

def maskeler(etiket_yolu, h, w):
    z = np.zeros((h, w), np.uint8); e = np.zeros((h, w), np.uint8)
    if not os.path.exists(etiket_yolu): return None, None
    for satir in open(etiket_yolu, encoding="utf-8"):
        p = satir.split()
        if len(p) < 7: continue
        c = int(float(p[0])); v = np.array([float(x) for x in p[1:]], np.float32)
        if v.size % 2: v = v[:-1]
        pts = (v.reshape(-1, 2) * np.array([w, h], np.float32)).astype(np.int32)
        cv2.fillPoly(z if c == 0 else e, [pts], 1)
    z[e > 0] = 0                    # MADDE 15: engel zemini asla buyutmez
    return z, e

kayit = []
for o in man["ornekler"]:
    ip = os.path.join(KUME, o["cikti"].replace("/", os.sep))
    lp = os.path.join(KUME, o["cikti"].replace("/", os.sep)
                      .replace("images", "labels").rsplit(".", 1)[0] + ".txt")
    im = cv2.imread(ip, cv2.IMREAD_COLOR)
    if im is None: continue
    h, w = im.shape[:2]
    z, e = maskeler(lp, h, w)
    if z is None or not z.any(): continue
    mpp = float(o["arena"]["mpp"]); ic = tuple(o["arena"]["icerik"])
    r = {"kare": o["cikti"]}
    for ad, gor in (("bugun", None), ("hb_bagli", im)):
        yol, guven, wps, red = analyze_path(
            z, icerik=ic, engel_mask=e, mpp=mpp, return_reason=True, goruntu=gor)
        r[ad] = {"rota": yol is not None, "n_wp": len(wps or []),
                 "sebep": (red[0] if red else None)}
        if yol is not None and wps:
            r[ad]["son_wp"] = [float(wps[-1][0]), float(wps[-1][1])]
    hb = hb_konumu(im)
    r["hb_bulundu"] = hb is not None
    if hb is not None: r["hb_kutu"] = list(hb["kutu"])
    r["gt_hedef_kutu"] = [float(v) for v in o["arena"]["hedef_kutu"]]
    kayit.append(r)

n = len(kayit)
bug = [k for k in kayit if k["bugun"]["rota"]]
hbk = [k for k in kayit if k["hb_bagli"]["rota"]]
kayip = [k for k in kayit if k["bugun"]["rota"] and not k["hb_bagli"]["rota"]]
from collections import Counter
sb = Counter(k["hb_bagli"]["sebep"] for k in kayit if not k["hb_bagli"]["rota"])
# HB'ye gercekten varildi mi: son waypoint GT HB kutusunda mi
def icinde(p, kb):
    return p and kb[0] <= p[0] <= kb[0]+kb[2] and kb[1] <= p[1] <= kb[1]+kb[3]
vardi_b = sum(1 for k in bug if icinde(k["bugun"].get("son_wp"), k["gt_hedef_kutu"]))
vardi_h = sum(1 for k in hbk if icinde(k["hb_bagli"].get("son_wp"), k["gt_hedef_kutu"]))
ozet = {"n": n, "not": "YER GERCEGI maskesi (mukemmel algi ust siniri), GPU yok",
        "bugun_rota": len(bug), "hb_bagli_rota": len(hbk),
        "hb_bagli_kaybedilen_kare": len(kayip),
        "hb_bagli_ret_sebepleri": dict(sb),
        "son_wp_GT_HB_kutusunda__bugun": vardi_b,
        "son_wp_GT_HB_kutusunda__hb_bagli": vardi_h,
        "kaybedilen_kareler": [k["kare"] for k in kayip][:40]}
json.dump({"ozet": ozet, "kareler": kayit},
          open(os.path.join(CIK, "olcum_maliyet.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(json.dumps(ozet, ensure_ascii=False, indent=1))
