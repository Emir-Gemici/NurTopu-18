"""19 Eyl onayli Pixhawk ayarlari (telsiz COM7): COMPASS_USE3 0 (yalniz slot3 = dahili ise), SERVO1-8_FUNCTION 0
(motorlar AUX1-4 = SERVO9-12 ise), RC_PROTOCOLS 4 (IBUS), BRD_SER1_RTSCTS 0. Once oku+dogrula, yaz, geri oku, disarm ise yeniden baslat, tekrar oku."""
import json, sys, time
from pymavlink import mavutil
D="results/telsiz_20260919/"; kayit={"t":time.time()}
def baglan():
    m=mavutil.mavlink_connection("COM7", baud=57600, source_system=255, source_component=190); m.wait_heartbeat(timeout=15); return m
def oku(m, ad):
    for _ in range(5):
        m.mav.param_request_read_send(m.target_system, m.target_component, ad.encode(), -1); t=time.time()
        while time.time()-t<1.5:
            x=m.recv_match(type="PARAM_VALUE", blocking=True, timeout=0.3)
            if x is not None and x.param_id.rstrip("\x00")==ad: return x.param_value
    return None
def yaz(m, ad, v, tip):
    for _ in range(5):
        m.mav.param_set_send(m.target_system, m.target_component, ad.encode(), float(v), tip); t=time.time()
        while time.time()-t<1.5:
            x=m.recv_match(type="PARAM_VALUE", blocking=True, timeout=0.3)
            if x is not None and x.param_id.rstrip("\x00")==ad and int(x.param_value)==int(v): return True
    return False
def dev(d):
    d=int(d or 0); return "YOK" if d==0 else f"tip{(d>>16)&0xFF} bus{(d>>3)&0x1F} adr0x{(d>>8)&0xFF:02X}"
I8=mavutil.mavlink.MAV_PARAM_TYPE_INT8; I16=mavutil.mavlink.MAV_PARAM_TYPE_INT16; I32=mavutil.mavlink.MAV_PARAM_TYPE_INT32
m=baglan()
ADLAR=["COMPASS_DEV_ID","COMPASS_DEV_ID2","COMPASS_DEV_ID3","COMPASS_EXTERN2","COMPASS_EXTERN3","COMPASS_USE","COMPASS_USE2","COMPASS_USE3","COMPASS_PRIO1_ID","RC_PROTOCOLS","BRD_SER1_RTSCTS"]+[f"SERVO{i}_FUNCTION" for i in range(1,13)]
once={a:oku(m,a) for a in ADLAR}; kayit["once"]=once
print("pusula: slot1", dev(once["COMPASS_DEV_ID"]), "| slot2", dev(once["COMPASS_DEV_ID2"]), "EXTERN2", once["COMPASS_EXTERN2"], "| slot3", dev(once["COMPASS_DEV_ID3"]), "EXTERN3", once["COMPASS_EXTERN3"], "USE3", once["COMPASS_USE3"], "| PRIO1", dev(once["COMPASS_PRIO1_ID"]))
print("SERVO1-8:", [int(once[f'SERVO{i}_FUNCTION']) for i in range(1,9)], "| SERVO9-12:", [int(once[f'SERVO{i}_FUNCTION']) for i in range(9,13)], "| RC_PROTOCOLS", once["RC_PROTOCOLS"], "| BRD_SER1_RTSCTS", once["BRD_SER1_RTSCTS"])
if any(v is None for v in once.values()): sys.exit("okunamayan parametre var — hicbir sey yazilmadi")
plan={}
if int(once["COMPASS_EXTERN3"])==0 and int(once["COMPASS_DEV_ID3"])!=0 and int(once["COMPASS_PRIO1_ID"])!=int(once["COMPASS_DEV_ID3"]) and int(once["COMPASS_EXTERN2"])==1:
    plan["COMPASS_USE3"]=(0,I8)
else: print("⚠ COMPASS_USE3 ATLANDI: slot3 dahili/ikincil kosulu saglanmadi")
motor={33,34,35,36}
if sorted(int(once[f'SERVO{i}_FUNCTION']) for i in range(9,13))==[33,34,35,36]:
    for i in range(1,9):
        if int(once[f'SERVO{i}_FUNCTION'])!=0: plan[f"SERVO{i}_FUNCTION"]=(0,I16)
else: print("⚠ SERVO1-8 ATLANDI: AUX1-4 motor 1-4 degil")
if int(once["RC_PROTOCOLS"])!=4: plan["RC_PROTOCOLS"]=(4,I32)
if int(once["BRD_SER1_RTSCTS"])!=0: plan["BRD_SER1_RTSCTS"]=(0,I8)
print("PLAN:", {k:v[0] for k,v in plan.items()})
sonuc={a:yaz(m,a,v,t) for a,(v,t) in plan.items()}; kayit["yazim"]=sonuc; print("yazim:", sonuc)
hb=m.recv_match(type="HEARTBEAT", blocking=True, timeout=5)
while hb is not None and hb.get_srcSystem()!=m.target_system: hb=m.recv_match(type="HEARTBEAT", blocking=True, timeout=5)
armli = bool(hb.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED) if hb else None; kayit["armli"]=armli; print("ARMLI mi:", armli)
if armli is False and all(sonuc.values()):
    m.mav.command_long_send(m.target_system, m.target_component, mavutil.mavlink.MAV_CMD_PREFLIGHT_REBOOT_SHUTDOWN, 0, 1,0,0,0,0,0,0)
    ack=m.recv_match(type="COMMAND_ACK", blocking=True, timeout=5); print("yeniden baslatma ACK:", getattr(ack,"result",None)); m.close()
    time.sleep(12); m=baglan(); time.sleep(3)
    son={a:oku(m,a) for a in ADLAR}; kayit["son"]=son
    fark={a:(once[a],son[a]) for a in ADLAR if once[a]!=son[a]}; print("ACILIS SONRASI degisenler:", fark)
    tutmayan=[a for a,(v,_) in plan.items() if son.get(a) is None or int(son[a])!=v]; print("plana UYMAYAN:", tutmayan or "yok"); kayit["uymayan"]=tutmayan
    t=time.time(); txt=[]
    while time.time()-t<12:
        x=m.recv_match(type="STATUSTEXT", blocking=True, timeout=0.5)
        if x: txt.append(x.text)
    print("STATUSTEXT (12 s):", txt); kayit["statustext"]=txt
else: print("yeniden baslatma YAPILMADI (armli ya da yazim eksik)")
m.close(); json.dump(kayit, open(D+"08_pixhawk_ayar_kayit.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
