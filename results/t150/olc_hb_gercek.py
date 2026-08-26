# -*- coding: utf-8 -*-
"""T150 (b) — HB'nin BULUNMADIGI gercek karelerde YANLIS-POZITIF olcumu.
Gercek karelerde kirmizi H pedi YOKTUR (kullanici dogruladi: 'gercek kirmizi H
karesi YOK'). Bu yuzden hb_konumu'nun HERHANGI bir tespiti YANLIS-POZITIFTIR.
Uretime baglanirsa: tespit YOK -> HEDEF_YOK (rota kesilir);
                   tespit VAR  -> rota YANLIS varis noktasina gider."""
import glob, json, os, sys
import numpy as np, cv2
KOK = r"O:\navitas"
sys.path.insert(0, os.path.join(KOK, "codes"))
from karar_sozlesmesi import hb_maskesi, hb_konumu, ince_bariyer_maskesi, mpp_hb_pedinden

KUMELER = {
 "gercek_67_otopark": sorted(glob.glob(os.path.join(KOK, "data", "raw_frames", "**", "*.jpg"), recursive=True)),
 "dji_kirsal_0038_111": sorted(glob.glob(os.path.join(KOK, "dataset", "dji_kirsal_0038_bolum_v3", "images", "**", "*.jpg"), recursive=True)),
 "arena_figuru_s9": [os.path.join(KOK, "data", "arena_referans", "sartname_s9_arena.png")],
}
CIK = os.path.join(KOK, "results", "t150"); BIND = os.path.join(CIK, "bindirme")
os.makedirs(BIND, exist_ok=True)
sonuc, ham = {}, {}
for ad, yollar in KUMELER.items():
    kayit = []
    for p in yollar:
        im = cv2.imread(p, cv2.IMREAD_COLOR)
        if im is None: continue
        hb = hb_konumu(im); ped = hb_maskesi(im); bar = ince_bariyer_maskesi(im)
        r = {"kare": os.path.basename(p), "boyut": list(im.shape[:2]),
             "tespit": hb is not None,
             "ped_px": int(ped.sum()) if ped is not None else None,
             "bariyer_kesisim_px": int(np.count_nonzero((ped > 0) & (bar > 0)))
                 if (ped is not None and bar is not None) else None}
        if hb is not None:
            r.update({"kutu": list(hb["kutu"]), "merkez": list(hb["merkez"]),
                      "kenar_px": hb["kenar_px"], "alan_px": hb["alan_px"],
                      "aday_sayisi": hb["aday_sayisi"],
                      "mpp_ima": mpp_hb_pedinden(hb["kenar_px"])})
        kayit.append(r)
    tespitli = [k for k in kayit if k["tespit"]]
    cak = [k for k in kayit if (k.get("bariyer_kesisim_px") or 0) > 0]
    sonuc[ad] = {"n": len(kayit), "tespit_kare": len(tespitli),
                 "yanlis_pozitif_orani": round(len(tespitli)/max(1.0, len(kayit)), 4),
                 "tespitli_kareler": [k["kare"] for k in tespitli][:40],
                 "T67_cakisan_kare": len(cak)}
    ham[ad] = kayit
    # bindirme
    for k in (tespitli[:12] if tespitli else kayit[:3]):
        p = [q for q in yollar if os.path.basename(q) == k["kare"]][0]
        im = cv2.imread(p)
        ped = hb_maskesi(im)
        if ped is not None and ped.any():
            im[ped > 0] = (0.45*im[ped > 0] + 0.55*np.array([255, 0, 255])).astype(np.uint8)
        if k.get("kutu"):
            x, y, w, h = k["kutu"]; cv2.rectangle(im, (x, y), (x+w, y+h), (255, 0, 255), 3)
        et = "%s %s %s" % (ad, k["kare"], "TESPIT" if k["tespit"] else "tespit-yok")
        cv2.putText(im, et, (6, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 4)
        cv2.putText(im, et, (6, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.imwrite(os.path.join(BIND, "gercek_%s_%s.jpg" % (ad, os.path.splitext(k["kare"])[0])), im)
json.dump(ham, open(os.path.join(CIK, "ham_gercek.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
json.dump(sonuc, open(os.path.join(CIK, "olcum_gercek.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(json.dumps(sonuc, ensure_ascii=False, indent=1))
