"""Uzak RFD900A'ya MAX_WINDOW yaz — her adim dogrulanir (D-507 yordami). Kullanim: <port> <deger>"""
import sys, time, re, json, serial
PORT, DEGER = sys.argv[1], int(sys.argv[2])
SATIR=re.compile(r"^S(\d+):\s*([A-Z_0-9]+)=(-?\d+)\s*$")
def oku(s, toplam_s):
    bas=time.monotonic(); t=b""
    while time.monotonic()-bas<toplam_s:
        v=s.read(4096)
        if v: t+=v
    return t.decode("utf-8","replace")
def at(s, k, bekle): s.reset_input_buffer(); s.write((k+"\r\n").encode()); s.flush(); return oku(s,bekle)
def coz(m): return {x.group(2):(int(x.group(1)),int(x.group(3))) for x in (SATIR.match(l.strip()) for l in m.splitlines()) if x}
kayit={"t":time.time(),"deger":DEGER,"adimlar":[]}
s=serial.Serial(PORT,57600,timeout=0.2)
def komut_modu():
    s.reset_input_buffer(); time.sleep(1.2); s.write(b"+++"); s.flush(); time.sleep(1.2); c=oku(s,0.8); return "OK" in c.upper()
print("komut modu:", komut_modu())
uzak=coz(at(s,"RTI5",8.0)); print("uzak once:", {k:v[1] for k,v in uzak.items()} if uzak else "CEVAP YOK")
if not uzak: at(s,"ATO",0.3); s.close(); sys.exit("uzak okunamadi, hicbir sey yazilmadi")
no, eski = uzak["MAX_WINDOW"]; kayit["uzak_once"]=eski
if eski==DEGER: print("uzak MAX_WINDOW zaten", DEGER)
else:
    c=at(s,f"RTS{no}={DEGER}",3.0); print(f"RTS{no}={DEGER} ->", repr(c.strip()[-20:])); kayit["adimlar"].append(("RTS",c))
    c=at(s,"RT&W",3.0); print("RT&W ->", repr(c.strip()[-20:])); kayit["adimlar"].append(("RT&W",c))
    tekrar=coz(at(s,"RTI5",8.0)); v=tekrar.get("MAX_WINDOW",(None,None))[1]; print("uzak geri okuma MAX_WINDOW =", v); kayit["uzak_geri_okuma"]=v
    if v!=DEGER:
        print("DOGRULANAMADI -> yeniden baslatma YAPILMADI; geri alma:", f"RTS{no}={eski}", "RT&W"); at(s,"ATO",0.3); s.close()
        json.dump(kayit,open(f"results/telsiz_20260919/03_uzak_yazim_{DEGER}.json","w",encoding="utf-8"),ensure_ascii=False,indent=1); sys.exit(3)
    c=at(s,"RTZ",2.0); print("RTZ ->", repr(c.strip()[-20:])); kayit["adimlar"].append(("RTZ",c))
at(s,"ATO",0.3); s.close()
print("uzak yeniden basliyor, 6 s bekleniyor..."); time.sleep(6)
s=serial.Serial(PORT,57600,timeout=0.2); veri=oku(s,3.0); print("hat: 3 s'de", len(veri), "bayt veri", "(Pixhawk akisi var)" if len(veri)>100 else "(VERI YOK!)"); kayit["yeniden_baslatma_sonrasi_bayt_3s"]=len(veri)
print("komut modu:", komut_modu()); yerel=coz(at(s,"ATI5",3.0)); uzak2=coz(at(s,"RTI5",8.0)); at(s,"ATO",0.3); s.close()
kayit["yerel_son"]={k:v[1] for k,v in yerel.items()}; kayit["uzak_son"]={k:v[1] for k,v in uzak2.items()}
print("SON: yerel MAX_WINDOW", yerel.get("MAX_WINDOW",(0,None))[1], "| uzak MAX_WINDOW", uzak2.get("MAX_WINDOW",(0,None))[1] if uzak2 else "CEVAP YOK")
fark=[k for k in yerel if k in uzak2 and yerel[k][1]!=uzak2[k][1]]; print("yerel/uzak fark:", fark or "yok"); kayit["fark"]=fark
json.dump(kayit,open(f"results/telsiz_20260919/03_uzak_yazim_{DEGER}.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
