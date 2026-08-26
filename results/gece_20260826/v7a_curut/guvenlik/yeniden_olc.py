"""GPU'suz yeniden üretim: 126 JSON'daki olceksiz_wps + t152_uzlasi/*_uc.png (960x540) ile
rota_yol (yol_payi/etiketsiz/engel/engel_wp) yeniden hesaplanır; bindirmeler çizilir.
Tuval: 3840x3840 letterbox, görüntü y0=840 -> 960x540: x/4, (y-840)/4."""
import json, sys, cv2, numpy as np
from pathlib import Path
KOK = Path("O:/navitas"); G = KOK/"results/gece_20260826"
UZ = G/"t152_uzlasi"; CIK = G/"v7a_curut/guvenlik"; (CIK/"bindirme").mkdir(exist_ok=True)
sys.path.insert(0, str(KOK/"scripts/olcum"))
import importlib.util
spec = importlib.util.spec_from_file_location("ryo", KOK/"scripts/olcum/rota_yol_olcumu.py"); ryo = importlib.util.module_from_spec(spec); spec.loader.exec_module(ryo)

def yukle(p):
    d = json.load(open(p)); m = d["modeller"]; return {s["kare"]: s for s in m[list(m)[0]]["kareler"]}
J = {
 "v7a_test29": yukle(G/"gece_v7a_test29.json"), "v7a_val82": yukle(G/"gece_v7a_val82_test29.json"),
 "v35_test29": yukle(G/"v35_ref3_test29.json"), "v35_val82": yukle(G/"sizinti/val82_v35_test29.json"),
}
def uc_oku(kare):
    m = cv2.imread(str(UZ/(Path(kare).stem+"_uc.png")), cv2.IMREAD_GRAYSCALE); return np.squeeze(m)
def wps_960(wps):
    return [[x/4.0, (y-840)/4.0] for x,y in wps]
def olc(kare, wps):
    uc = uc_oku(kare); return ryo.rota_yol_olc([[int(round(x)),int(round(y))] for x,y in wps_960(wps)], uc), uc

# 1) Etiket dizini (dataset v3 labels) == uzlaşı png mi? (tuval üzerinden, 3840 -> 960 örnekleme)
lbl = KOK/"dataset/dji_kirsal_0038_bolum_v3/labels"
fark = []
for bol, kum in (("test","v7a_test29"),("val","v7a_val82")):
    for kare in list(J[kum])[:200]:
        uc_l = ryo.uc_durum_maske(lbl/bol/(Path(kare).stem+".txt"), 2160, 3840)[840:3000, :]
        uc_l = cv2.resize(uc_l, (960,540), interpolation=cv2.INTER_NEAREST)
        uc_p = uc_oku(kare)
        fark.append((kare[-25:-4], float((uc_l!=uc_p).mean())))
print("etiket(v3 labels) vs uzlasi png farkli piksel payi: maks", max(f for _,f in fark), "ort", sum(f for _,f in fark)/len(fark), "n", len(fark))

# 2) Yeniden hesap + 111 kare çapraz tablo
sonuc = {"yeniden": {}, "capraz": []}
for model in ("v7a","v35"):
    for bol in ("test29","val82"):
        k = J[f"{model}_{bol}"]; satir=[]
        for kare, s in k.items():
            if s["olceksiz_sebep"] is not None: continue
            o,_ = olc(kare, s["olceksiz_wps"]); o["yanlis"] = ryo.yanlis_guzergah_mi(o); o["kare"]=kare[-25:-4]; satir.append(o)
        ny = sum(o["yanlis"] for o in satir)
        print(f"{model} {bol}: ROTA {len(satir)} YANLIS {ny} yanlis_kareler {[o["kare"][5:11] for o in satir if o["yanlis"]]} engel_wp_toplam {sum(o['engel_wp'] for o in satir)}")
        sonuc["yeniden"][f"{model}_{bol}"] = {"rota": len(satir), "yanlis": ny, "satirlar": satir}
# çapraz: her karede v35 sebep / v7a sebep / yanlış mı
for bol in ("test29","val82"):
    for kare in J[f"v35_{bol}"]:
        a = J[f"v35_{bol}"][kare]; b = J[f"v7a_{bol}"][kare]
        sonuc["capraz"].append({"kare": kare[-25:-4], "bol": bol, "v35": a["olceksiz_sebep"] or "ROTA", "v7a": b["olceksiz_sebep"] or "ROTA", "v35_zemin": a["zemin_orani"], "v7a_zemin": b["zemin_orani"]})
from collections import Counter
print("capraz (v35 sebep -> v7a sebep):", Counter((c["v35"], c["v7a"]) for c in sonuc["capraz"]))
json.dump(sonuc, open(CIK/"yeniden_olc.json","w"), indent=1)

# 3) Bindirmeler
KARE = KOK/"dataset/dji_kirsal_0038_bolum_v3/images"
def bindir(kare, bol, ad):
    kum = "test29" if bol=="test" else "val82"
    img = cv2.imread(str(KARE/bol/kare)); img = cv2.resize(img, (960,540), interpolation=cv2.INTER_AREA)
    uc = uc_oku(kare); ov = img.copy()
    ov[uc==1] = (0.45*ov[uc==1] + 0.55*np.array([0,200,0])).astype(np.uint8)   # yol yeşil
    ov[uc==2] = (0.45*ov[uc==2] + 0.55*np.array([0,0,220])).astype(np.uint8)   # engel kırmızı
    paneller = [img, ov]
    for model in ("v35","v7a"):
        s = J[f"{model}_{kum}"][kare]; p = ov.copy()
        if s["olceksiz_sebep"] is None:
            pts = np.array([[int(round(x)),int(round(y))] for x,y in wps_960(s["olceksiz_wps"])], np.int32)
            cv2.polylines(p, [pts], False, (255,255,0), 3)
            o,_ = olc(kare, s["olceksiz_wps"])
            for (x,y) in pts:
                renk = (0,0,255) if uc[min(max(y,0),539), min(max(x,0),959)]==2 else ((255,255,255) if uc[min(max(y,0),539), min(max(x,0),959)]==1 else (0,255,255))
                cv2.circle(p, (int(x),int(y)), 7, renk, -1)
            txt = f"{model} ROTA yol {o['yol_payi']:.2f} etiketsiz {o['etiketsiz_payi']:.2f} engel {o['engel_payi']:.2f} engel_wp {o['engel_wp']}"
        else:
            txt = f"{model} {s['olceksiz_sebep']} zemin_orani {s['zemin_orani']:.3f}"
        cv2.putText(p, txt, (8,28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,0), 4); cv2.putText(p, txt, (8,28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
        paneller.append(p)
    ust = np.hstack(paneller[:2]); alt = np.hstack(paneller[2:]); out = np.vstack([ust, alt])
    cv2.putText(out, f"{kare[-25:-4]} | ust-sol kare, ust-sag uzlasi (yesil yol, kirmizi engel, renksiz etiketsiz) | wp: beyaz yol, sari etiketsiz, kirmizi engel", (8, 1075), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255,255,255), 1)
    cv2.imwrite(str(CIK/"bindirme"/f"{ad}_{kare[-25:-4]}.jpg"), out, [cv2.IMWRITE_JPEG_QUALITY, 80])
v7a_yanlis = ["000064","000129","000140","000168","000208","000210","000223"]
v35_yanlis = ["000130","000153","000156","000157","000158","000159","000201","000203","000208","000230"]
for kare in J["v7a_val82"]:
    f = kare[-20:-14]
    if f in v7a_yanlis: bindir(kare, "val", "v7a_yanlis")
    elif f in v35_yanlis: bindir(kare, "val", "v35_yanlis")
for kare in J["v7a_test29"]:
    f = kare[-20:-14]
    if f in ("000218","000124","000135","000152","000196","000202"): bindir(kare, "test", "test29")
print("bindirmeler:", len(list((CIK/"bindirme").glob("*.jpg"))))

# 4) v35 ROTA olan karelerde v7a ne yaptı (rota kaybı = v35 TP iken v7a MASKE_YOK/UC_BANT?)
tavan_t = json.load(open(G/"test29_etiket_tavani_v3.json")); tavan_v = json.load(open(G/"sizinti/val82_etiket_tavani.json"))
def tavan_rota(tv):
    m = tv.get("kareler", tv); 
    return {s["kare"]: (s.get("sebep") is None or s.get("sebep")=="ROTA" or s.get("rota") is True) for s in m} if isinstance(m,list) else None
print("tavan keys", list(tavan_t)[:8])
ry = {k: {o["kare"]: o for o in v["satirlar"]} for k,v in sonuc["yeniden"].items()}
for bol in ("test29","val82"):
    print(f"--- {bol}: v35 ROTA karelerinde v7a")
    for kare in J[f"v35_{bol}"]:
        a = J[f"v35_{bol}"][kare]; b = J[f"v7a_{bol}"][kare]
        if a["olceksiz_sebep"] is None:
            kk = kare[-25:-4]; av = ry[f"v35_{bol}"][kk]; bv = ry[f"v7a_{bol}"].get(kk)
            print(f"  {kk[5:11]} v35 yol {av['yol_payi']:.2f} engel_wp {av['engel_wp']} yanlis {av['yanlis']} | v7a {b['olceksiz_sebep'] or 'ROTA'}", (f"yol {bv['yol_payi']:.2f} engel_wp {bv['engel_wp']} yanlis {bv['yanlis']}" if bv else f"zemin_orani {b['zemin_orani']:.3f}"))
