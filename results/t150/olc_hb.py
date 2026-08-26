# -*- coding: utf-8 -*-
"""T150 — hb_maskesi / hb_konumu OLCUMU (ON_KAYIT SS16). Uretime BAGLAMA YOK."""
import json, os, sys
import numpy as np
import cv2

KOK = r"O:\navitas"
sys.path.insert(0, os.path.join(KOK, "codes"))
from karar_sozlesmesi import (hb_maskesi, hb_konumu, ince_bariyer_maskesi,
                              mpp_hb_pedinden, HB_KENAR_M, HB_KARE_TOLERANSI,
                              HB_ASGARI_ALAN_ORANI, HB_KAPAMA_ORANI,
                              BARIYER_KROMA_ESIGI, BARIYER_EN_BOY_ORANI)

KUME = r"O:\navitas-local-train\calisma\sentetik_arena_kadraj_t66"
CIK  = os.path.join(KOK, "results", "t150")
BIND = os.path.join(CIK, "bindirme")
os.makedirs(BIND, exist_ok=True)

man = json.load(open(os.path.join(KUME, "manifest.json"), encoding="utf-8"))
ornekler = man["ornekler"]

def iou(a, b):
    ax, ay, aw, ah = a; bx, by, bw, bh = b
    x0, y0 = max(ax, bx), max(ay, by)
    x1, y1 = min(ax+aw, bx+bw), min(ay+ah, by+bh)
    if x1 <= x0 or y1 <= y0: return 0.0
    ke = (x1-x0)*(y1-y0)
    return ke / float(aw*ah + bw*bh - ke)

kayitlar = []
for o in ornekler:
    yol = os.path.join(KUME, o["cikti"].replace("/", os.sep))
    im = cv2.imread(yol, cv2.IMREAD_COLOR)
    if im is None:
        kayitlar.append({"kare": o["cikti"], "hata": "okunamadi"}); continue
    gk = [float(v) for v in o["arena"]["hedef_kutu"]]        # x,y,w,h (640 uzayi)
    gcx, gcy = gk[0]+gk[2]/2.0, gk[1]+gk[3]/2.0
    ped = hb_maskesi(im)
    hb  = hb_konumu(im)
    bar = ince_bariyer_maskesi(im)

    # bilesen bazli TP/FP: GT kutusuyla >= 0,10 IoU olan bilesen = TP adayi
    bilesenler = []
    if ped is not None and ped.any():
        n, lbl, st, mrk = cv2.connectedComponentsWithStats(ped.astype(np.uint8), 8)
        for i in range(1, n):
            x, y, bw_, bh_, alan = (int(v) for v in st[i][:5])
            bilesenler.append({"kutu": [x, y, bw_, bh_], "alan": alan,
                               "merkez": [float(mrk[i][0]), float(mrk[i][1])],
                               "iou": iou([x, y, bw_, bh_], gk)})
    fp_bilesen = [b for b in bilesenler if b["iou"] < 0.10]

    r = {"kare": o["cikti"], "bolum": o["bolum"],
         "gt_kutu": gk, "gt_merkez": [gcx, gcy],
         "gt_mpp": float(o["arena"]["mpp"]),
         "hedef_serit": o["arena"].get("hedef_serit"),
         "bulundu": hb is not None,
         "bilesen_sayisi": len(bilesenler),
         "fp_bilesen_sayisi": len(fp_bilesen),
         "bariyer_kesisim_px": int(np.count_nonzero(
             (ped > 0) & (bar > 0))) if (ped is not None and bar is not None) else None,
         "ped_px": int(ped.sum()) if ped is not None else None,
         "bariyer_px": int(bar.sum()) if bar is not None else None}
    if hb is not None:
        px, py = hb["merkez"]
        r.update({"tespit_kutu": list(hb["kutu"]),
                  "tespit_merkez": [px, py],
                  "kenar_px": hb["kenar_px"],
                  "aday_sayisi": hb["aday_sayisi"],
                  "merkez_hata_px": float(np.hypot(px-gcx, py-gcy)),
                  "iou": iou(list(hb["kutu"]), gk),
                  "merkez_gt_icinde": bool(gk[0] <= px <= gk[0]+gk[2]
                                           and gk[1] <= py <= gk[1]+gk[3]),
                  "mpp_tahmin": mpp_hb_pedinden(hb["kenar_px"])})
    kayitlar.append(r)

json.dump({"sabitler": {"HB_KENAR_M": HB_KENAR_M,
                        "HB_KARE_TOLERANSI": HB_KARE_TOLERANSI,
                        "HB_ASGARI_ALAN_ORANI": HB_ASGARI_ALAN_ORANI,
                        "HB_KAPAMA_ORANI": HB_KAPAMA_ORANI,
                        "BARIYER_KROMA_ESIGI": BARIYER_KROMA_ESIGI,
                        "BARIYER_EN_BOY_ORANI": BARIYER_EN_BOY_ORANI},
           "kume": KUME, "n": len(kayitlar), "kareler": kayitlar},
          open(os.path.join(CIK, "ham_kareler.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

# ── ozet ────────────────────────────────────────────────────────────────────
n = len(kayitlar)
bul = [k for k in kayitlar if k.get("bulundu")]
yok = [k for k in kayitlar if not k.get("bulundu")]
ici = [k for k in bul if k["merkez_gt_icinde"]]
hata = np.array([k["merkez_hata_px"] for k in bul]) if bul else np.array([])
ious = np.array([k["iou"] for k in bul]) if bul else np.array([])
fp_kare = [k for k in kayitlar if k.get("fp_bilesen_sayisi", 0) > 0]
cak = [k for k in kayitlar if (k.get("bariyer_kesisim_px") or 0) > 0]
mppt = np.array([k["mpp_tahmin"] for k in bul if k.get("mpp_tahmin")])
mppg = np.array([k["gt_mpp"] for k in bul if k.get("mpp_tahmin")])

ozet = {
 "n": n,
 "bulundu": len(bul), "bulunamadi": len(yok),
 "bulunamayan_kareler": [k["kare"] for k in yok],
 "merkez_gt_kutusu_icinde": len(ici),
 "merkez_hata_px": {"medyan": float(np.median(hata)) if hata.size else None,
                    "ort": float(hata.mean()) if hata.size else None,
                    "p90": float(np.percentile(hata, 90)) if hata.size else None,
                    "maks": float(hata.max()) if hata.size else None},
 "iou": {"medyan": float(np.median(ious)) if ious.size else None,
         "min": float(ious.min()) if ious.size else None,
         "iou>=0,5 kare": int((ious >= 0.5).sum()) if ious.size else 0},
 "yanlis_pozitif": {"kare": len(fp_kare),
                    "toplam_bilesen": int(sum(k["fp_bilesen_sayisi"] for k in kayitlar)),
                    "kareler": [k["kare"] for k in fp_kare][:40]},
 "T67_cakismasi": {"kare": len(cak),
                   "toplam_px": int(sum(k.get("bariyer_kesisim_px") or 0 for k in kayitlar)),
                   "kareler": [k["kare"] for k in cak][:40]},
 "mpp": {"gt_medyan": float(np.median(mppg)) if mppg.size else None,
         "tahmin_medyan": float(np.median(mppt)) if mppt.size else None,
         "bagil_hata_medyan": float(np.median(np.abs(mppt-mppg)/mppg)) if mppt.size else None,
         "bagil_hata_maks": float(np.abs(mppt-mppg).max()/mppg.max()) if mppt.size else None},
 "URETIME_BAGLAMA_MALIYETI": {
   "HB_bulunamayan_kare": len(yok),
   "HEDEF_YOK_ile_rota_kaybedecek_kare": len(yok),
   "oran": round(len(yok)/float(n), 4)},
}
json.dump(ozet, open(os.path.join(CIK, "olcum.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(json.dumps(ozet, ensure_ascii=False, indent=1))

# ── bindirme: en kotu 10 + bulunamayan hepsi + ilk 6 iyi ────────────────────
def bindir(k, ad):
    im = cv2.imread(os.path.join(KUME, k["kare"].replace("/", os.sep)))
    if im is None: return
    g = [int(round(v)) for v in k["gt_kutu"]]
    cv2.rectangle(im, (g[0], g[1]), (g[0]+g[2], g[1]+g[3]), (0, 255, 0), 2)
    if k.get("tespit_kutu"):
        t = k["tespit_kutu"]
        cv2.rectangle(im, (t[0], t[1]), (t[0]+t[2], t[1]+t[3]), (255, 0, 255), 2)
    ped = hb_maskesi(im)
    if ped is not None and ped.any():
        im[ped > 0] = (0.45*im[ped > 0] + 0.55*np.array([255, 0, 255])).astype(np.uint8)
    cv2.putText(im, ad, (6, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 3)
    cv2.putText(im, ad, (6, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.imwrite(os.path.join(BIND, ad.replace(" ", "_").replace("=", "")
                             .replace(",", "") + ".jpg"), im)

kotu = sorted(bul, key=lambda k: -k["merkez_hata_px"])[:10]
for k in kotu: bindir(k, "kotu %s h%.1f" % (os.path.basename(k["kare"]), k["merkez_hata_px"]))
for k in yok[:20]: bindir(k, "bulunamadi %s" % os.path.basename(k["kare"]))
for k in fp_kare[:10]: bindir(k, "fp %s" % os.path.basename(k["kare"]))
for k in sorted(bul, key=lambda x: x["merkez_hata_px"])[:6]:
    bindir(k, "iyi %s h%.1f" % (os.path.basename(k["kare"]), k["merkez_hata_px"]))
print("bindirme:", len(os.listdir(BIND)))
