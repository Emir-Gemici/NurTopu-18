# SALT OKUMA HESAP — ANALIZ B. Girdi: T214-A k3_uretim_boru/kerteriz/*.json (dal worktree-wf_2c28e623-233-7), sabitler.
import json, math, glob, os, re, statistics as st
B = r"C:\Users\yunus\AppData\Local\Temp\claude\O--navitas\3e104177-9b44-4ec7-a18f-1f32ed2c3f72\scratchpad\rota_dunya"
f_mm, sw, sh = 6.0, 6.287, 4.712
HF = 2*math.degrees(math.atan(sw/2/f_mm)); VF = 2*math.degrees(math.atan(sh/2/f_mm))
kW, kH = sw/f_mm, sh/f_mm           # yer izi / irtifa
print(f"HQ 6mm: HFOV {HF:.2f} deg  VFOV {VF:.2f} deg  W/h {kW:.4f}  H/h {kH:.4f}")
sim_hfov = math.degrees(1.3); print(f"sim hfov {sim_hfov:.3f} deg, 30 m iz {2*30*math.tan(0.65):.2f} m (kare)")
# 1) T214-A kare verisi
out=[]
for p in sorted(glob.glob(os.path.join(B,"k3k","harita_*.json"))):
    d=json.load(open(p,encoding="utf-8"))
    kb, hb = d["kb_xy"], d["hb_xy"]; D=math.dist(kb,hb)
    K=d["kareler"]; tb=[k for k in K if k.get("tarama_bacagi")]
    both=sum(1 for k in tb if k["kb_karede"] and k["hb_karede"])
    kbn=sum(1 for k in tb if k["kb_karede"]); hbn=sum(1 for k in tb if k["hb_karede"])
    zs=sorted({k["z"] for k in tb})
    # varsayimsal: ayni x,y,yaw ile HQ 4:3 hangi irtifada KB(±0.5)+HB(±1.0) ikisini de kapsar
    def hreq(k, uzun_ileri):
        c,s=math.cos(math.radians(k["yaw_derece"])),math.sin(math.radians(k["yaw_derece"]))
        h=0
        for (px,py),m in ((kb,0.5),(hb,1.0)):
            dx,dy=px-k["x"],py-k["y"]; a= dx*c+dy*s; b=-dx*s+dy*c   # a: ileri, b: yan
            ka,kb_=(kW/2,kH/2) if uzun_ileri else (kH/2,kW/2)
            h=max(h,(abs(a)+m)/ka,(abs(b)+m)/kb_)
        return h
    hmin_tb=min(min(hreq(k,True),hreq(k,False)) for k in tb) if tb else None
    hmin_all=min(min(hreq(k,True),hreq(k,False)) for k in K if k["z"]>5)
    out.append((os.path.basename(p)[7:-5],D,len(K),len(tb),kbn,hbn,both,zs,hmin_tb,hmin_all))
print("\nharita | KB-HB m | kare | tarama_bacagi | KB | HB | ikisi | z | HQ h_min(tarama) | HQ h_min(z>5 tum)")
for r in out: print(f"{r[0]:8s} | {r[1]:.2f} | {r[2]} | {r[3]} | {r[4]} | {r[5]} | {r[6]} | {r[7]} | {r[8]:.1f} | {r[9]:.1f}")
Ds=[r[1] for r in out]; print(f"KB-HB: min {min(Ds):.2f} maks {max(Ds):.2f} medyan {st.median(Ds):.2f}; toplam tarama karesi {sum(r[3] for r in out)}, ikisi {sum(r[6] for r in out)}, KB {sum(r[4] for r in out)}, HB {sum(r[5] for r in out)}")
print(f"HQ h_min(tarama bacagi) min/medyan/maks: {min(r[8] for r in out):.1f} / {st.median([r[8] for r in out]):.1f} / {max(r[8] for r in out):.1f}")
# 2) Analitik: KB-HB tek karede (en iyi hizalama, pay: KB 0.5 + HB 1.0 = 1.5 m)
print("\nD senaryosu | h (KB-HB kisa eksende, uretim ALT->UST, yatay montaj) | h (uzun eksende) | h (uretim: KB alt %8 bantta + HB karede, kisa eksen) ust sinir")
for lab,D in (("sim min",min(Ds)),("sim maks",max(Ds)),("HTAB kenari 50",50.0),("HTAB kosegeni 70.7",50*math.sqrt(2)),("FDA 20x20 kenar",20.0),("FDA kosegen 28.3",20*math.sqrt(2))):
    Dm=D+1.5
    print(f"{lab:20s} D={D:5.1f} | h>={Dm/kH:6.1f} m | h>={Dm/kW:6.1f} m | KB bantta ise h<= ~{(Dm)/(0.92*kH):.1f} olmadan pencere: {'-'}")
# 3) Irtifa tablosu
print("\nh m | iz W x H m | GSD@512 cm/px | GSD@640 cm/px | IKA 0.70m px@512 | R_GEREKLI 1.10m px@512 | HB 2m px@512 | alt bant 8% m | on-kayit KB bant penceresi (V-D-1.5 ile min) D=45")
for h in (30,32,40,50,56,60,64,70,80,90,100,120):
    W,H=kW*h,kH*h; g5=W/512; g6=W/640
    win=min(0.08*H, H-45-1.5)
    print(f"{h:4d} | {W:5.1f} x {H:5.1f} | {g5*100:5.2f} | {g6*100:5.2f} | {0.70/g5:5.1f} | {1.10/g5:5.1f} | {2/g5:5.1f} | {0.08*H:4.1f} | {win:5.1f}")
# 4) Ornekleme araligi: kare basina ilerleme
for v,fps,lab in ((10,1.0,"sim tarama 10 m/s @1 Hz"),(10,1.35,"10 m/s @1.35 FPS (Jetson .pt olcumu)"),(18,1.35,"18 m/s (sim kalkis/tirmanis hizi) @1.35"),(3,1.35,"FDA WPNAV 3 m/s @1.35")):
    print(f"{lab}: kareler arasi {v/fps:.1f} m")
# 5) Referans olcekler
print("\nsim 30 m: GSD@512 =", round(2*30*math.tan(0.65)/512*100,2),"cm/px ; mpp kaynak 1280 =", round(2*30*math.tan(0.65)/1280,6))
print("DJI 20260822 medyan 4.389 cm/px@960 -> @512 =", round(4.389*960/512,2),"cm/px (3840 px kaynak)")
print("K-B cozunurluk koruyucusu esigi mpp > 1.10/(0.20*0.035*w): w=512 ->", round(1.10/(0.2*0.035*512),3), " w=1024 ->", round(1.10/(0.2*0.035*1024),3))
# 6) Sartname metninde hiz / tarama / irtifa ifadeleri
t=open(r"O:\navitas\results\sartname_bosluk\sartname_metin.txt",encoding="utf-8").read()
for pat in (r"m/s",r"km/s",r"tarama",r"irtifa",r"koordinat",r"GPS",r"geni[sş]li",r"\bsol\b",r"\bsa[gğ]\b",r"40.?-.?45",r"kuzey|g[uü]ney"):
    hits=[i+1 for i,l in enumerate(t.splitlines()) if re.search(pat,l,re.I)]
    print(f"sartname grep {pat!r}: satir {hits[:10]}")
