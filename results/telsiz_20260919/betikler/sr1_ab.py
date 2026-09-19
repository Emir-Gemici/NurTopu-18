"""SR1 A/B/A: telsiz yolu RTT (param yanki) — SR1 mevcut / SR1 sifir / SR1 mevcut. Sonda eski degerler geri yazilir ve dogrulanir."""
import json, subprocess, sys, time
from pymavlink import mavutil
PORT="COM7"; PY=sys.executable; D="results/telsiz_20260919/"
AD=["SR1_RAW_SENS","SR1_EXT_STAT","SR1_RC_CHAN","SR1_RAW_CTRL","SR1_POSITION","SR1_EXTRA1","SR1_EXTRA2","SR1_EXTRA3","SR1_PARAMS","SR1_ADSB"]
def baglan():
    m=mavutil.mavlink_connection(PORT, baud=57600, source_system=255, source_component=190); m.wait_heartbeat(timeout=10); return m
def oku(m, ad, dene=4):
    for _ in range(dene):
        m.mav.param_request_read_send(m.target_system, m.target_component, ad.encode(), -1)
        t=time.time()
        while time.time()-t<1.5:
            x=m.recv_match(type="PARAM_VALUE", blocking=True, timeout=0.3)
            if x is not None and x.param_id.rstrip("\x00")==ad: return x.param_value
    return None
def yaz(m, ad, deger):
    for _ in range(4):
        m.mav.param_set_send(m.target_system, m.target_component, ad.encode(), float(deger), mavutil.mavlink.MAV_PARAM_TYPE_INT16)
        t=time.time()
        while time.time()-t<1.5:
            x=m.recv_match(type="PARAM_VALUE", blocking=True, timeout=0.3)
            if x is not None and x.param_id.rstrip("\x00")==ad and int(x.param_value)==int(deger): return True
    return False
def yuk(m, s=8.0):
    t=time.time(); n=0; tip={}
    while time.time()-t<s:
        x=m.recv_match(blocking=True, timeout=0.3)
        if x is None: continue
        n+=len(x.get_msgbuf()); tip[x.get_type()]=tip.get(x.get_type(),0)+1
    return round(n/s), {k:v for k,v in sorted(tip.items(), key=lambda kv:-kv[1])[:8]}
def rtt(etiket, dosya):
    r=subprocess.run([PY,"scripts/tezgah/telsiz_rtt_param.py","--port",PORT,"--n","120","--etiket",etiket,"--json","--sessiz","--cikti",D+dosya],capture_output=True,text=True,encoding="utf-8",errors="replace")
    son=[l for l in r.stdout.splitlines() if l.startswith("p50=")]; print(f"  {etiket}: {son[-1] if son else r.stdout[-300:]+r.stderr[-300:]}", flush=True)
kayit={"t":time.time()}
m=baglan(); once={a:oku(m,a) for a in AD}; kayit["once"]=once; print("SR1 once:", once, flush=True)
if any(v is None for v in once.values()): print("OKUNAMAYAN VAR, durdu"); sys.exit(2)
kayit["yuk_A"]=yuk(m); print("A yuk (B/s, tipler):", kayit["yuk_A"], flush=True); m.close()
print("A  — SR1 mevcut", flush=True); rtt("A_sr1_mevcut","05_A_sr1_mevcut.json")
m=baglan(); sonuc={a:yaz(m,a,0) for a,v in once.items() if int(v)!=0}; kayit["sifirla"]=sonuc; print("sifirlandi:", sonuc, flush=True)
time.sleep(3); kayit["yuk_B"]=yuk(m); print("B yuk (B/s, tipler):", kayit["yuk_B"], flush=True); m.close()
print("B  — SR1 sifir", flush=True); rtt("B_sr1_sifir","06_B_sr1_sifir.json")
m=baglan(); geri={a:yaz(m,a,int(v)) for a,v in once.items() if int(v)!=0}; kayit["geri_yaz"]=geri
son={a:oku(m,a) for a in AD}; kayit["son"]=son; print("geri yazildi:", geri, "| dogrulama esit:", son==once, flush=True)
time.sleep(3); kayit["yuk_A2"]=yuk(m); print("A' yuk:", kayit["yuk_A2"], flush=True); m.close()
print("A' — SR1 mevcut (tekrar)", flush=True); rtt("A2_sr1_mevcut","07_A2_sr1_mevcut.json")
json.dump(kayit, open(D+"05_sr1_ab_kayit.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
