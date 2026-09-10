import json,sys,math,collections
S=sys.argv[1]
for f in ["uretim_2_kolay_42","uretim_5_zor_42","uretim_1_kolay_42"]:
    d=json.load(open(f"{S}/{f}.json",encoding="utf-8"))
    print("==",f, "ust anahtarlar:", sorted(d.keys())[:40])
    kr=d.get("kareler",[])
    print(" kare sayisi",len(kr))
    for s in kr:
        if s.get("karar")=="OPEN_ROUTE":
            print("  n=%s x=%s y=%s z=%s yaw=%s teta=%s yol=%s dunya_yolu=%s ilk=%s son=%s ankorKB=%s sonHB=%s ort=%s kb_karede=%s hb_karede=%s mpp=%s"%(
              s["n"],s["x"],s["y"],s["z"],s["yaw_derece"],s.get("teta_derece"),s["yol"],s.get("rota_dunya_yolu"),s.get("rota_ilk_dunya"),s.get("rota_son_dunya"),s.get("ankor_kb_uzakligi_m"),s.get("rota_sonu_hb_uzakligi_m"),s.get("rota_dunya_ort_uzaklik_m"),s.get("kb_karede"),s.get("hb_karede"),s.get("mpp")))
    tb=[s for s in kr if s.get("tarama_bacagi")]
    print(" tarama bacagi kare",len(tb),"kb_karede",sum(bool(s.get("kb_karede")) for s in tb),"hb_karede",sum(bool(s.get("hb_karede")) for s in tb),"ikisi",sum(bool(s.get("kb_karede")) and bool(s.get("hb_karede")) for s in tb))
    print(" bacak x degerleri", sorted(collections.Counter(round(s["x"]) for s in tb).items()))
    for k in ("H","arena","kb","hb","open"):
        if k in d: print(" ",k,str(d[k])[:300])
o=json.load(open(f"{S}/ozet_k3_uretim.json",encoding="utf-8"))
def walk(x,p=""):
    if isinstance(x,dict):
        for k,v in x.items():
            if any(t in k for t in ("teshis","dunya","kb_","hb_","etiket")):
                print(p+k,":",json.dumps(v,ensure_ascii=False)[:400])
            elif isinstance(v,(dict)): walk(v,p+k+".")
walk(o)
