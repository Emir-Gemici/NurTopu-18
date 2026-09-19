"""TEST 4 (Jetson): GERCEK OPEN_ROUTE telsizle YKI'ye -> hakem 'TESPITI DOGRULA' -> ACK telsizle Jetson'a.
Uretim protokolu (comms/protocol.open_route) ve uretim hub'i (127.0.0.1:5100) kullanilir; rota GEOMETRISI SENTETIKTIR
(masada model olcek uretemez — tasima testi). Uretim rpi_inference bu sure DURAKLATILIR (cagiran kabuk STOP/CONT);
YKI 'baglanti kaybi' gostermesin diye bu betik 1 Hz iha HEARTBEAT de yollar. Arg: <rota_seq> <hb_seq_taban> <sure_s>"""
import json, os, socket, sys, time
sys.path.insert(0, os.path.expanduser("~/navitas/comms")); sys.path.insert(0, os.path.expanduser("~/navitas/codes"))
from protocol import open_route, heartbeat, encode, decode
try:
    from karar_sozlesmesi import YAYIN_REF_XY
except Exception:
    YAYIN_REF_XY = (0.0, 0.0)
seq = int(sys.argv[1]); hb_seq = int(sys.argv[2]); sure = float(sys.argv[3])
wp = [[0.0, 0.0]] + [[round(0.3 * ((i % 4) - 1.5), 2), round(0.8 * i, 2)] for i in range(1, 24)]   # ilk nokta ANKOR [0,0] (iha_sender kurali), 24 nokta ~18 m
cerceve = encode(open_route(2, 0.91, wp, list(YAYIN_REF_XY), seq=seq))
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.bind(("127.0.0.1", 5192)); s.settimeout(0.1)
bas = time.time(); son_rota = son_hb = 0; gonderim = 0; ack = None; diger_ack = 0
while time.time() - bas < sure and ack is None:
    t = time.time()
    if t - son_hb >= 1.0:
        s.sendto(encode(heartbeat("iha", seq=hb_seq, karar_yas=0.3)), ("127.0.0.1", 5100)); hb_seq += 1; son_hb = t
    if t - son_rota >= 1.0:                          # uretim gibi tekrar: ACK gelene dek saniyede bir
        s.sendto(cerceve, ("127.0.0.1", 5100)); gonderim += 1; son_rota = t
        if gonderim == 1: ilk = t
    try: veri, _ = s.recvfrom(4096)
    except socket.timeout: continue
    for satir in veri.split(b"\n"):
        try: m = decode(satir)
        except Exception: continue
        if m.get("type") == "ACK":
            if m.get("ref") == seq: ack = (time.time(), m)
            else: diger_ack += 1
f = lambda x: time.strftime("%H:%M:%S", time.localtime(x)) + f".{int(x*1000)%1000:03d}"
print(json.dumps({"rota_seq": seq, "waypoint": len(wp), "cerceve_B": len(cerceve), "tunel_parca": -(-len(cerceve) // 123),
                  "ilk_gonderim": f(ilk), "gonderim_sayisi": gonderim, "ack_geldi": ack is not None,
                  "ack_saati": f(ack[0]) if ack else None, "ilk_gonderimden_ack_s": round(ack[0] - ilk, 1) if ack else None,
                  "ack": ack[1] if ack else None, "son_hb_seq": hb_seq}, ensure_ascii=False))
