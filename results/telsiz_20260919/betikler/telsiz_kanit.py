"""TELSIZ KANITI (Jetson'da kosar): tek seferlik isaretli ROTA_YOK cercevesini hub'a (127.0.0.1:5100) verir; cerceve
Jetson -> TELEM2 -> Pixhawk -> RFD900A -> yer telsizi -> YKI yolunu izler. YKI'nin otomatik ACK'i ayni yoldan geri
gelir; hub onu ogrenilmis tuketicilere dagitir, bu betik yakalar. Cikti: gidis saati, ACK saati, gidis-donus."""
import json, os, socket, sys, time
sys.path.insert(0, os.path.expanduser("~/navitas/comms"))
from protocol import rota_yok, encode, decode
isaret = sys.argv[1]; seq = int(sys.argv[2])
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.bind(("127.0.0.1", 5191)); s.settimeout(0.2)
cerceve = encode(rota_yok("MASKE_YOK", detay=isaret, seq=seq))
gonder = []; ack = None; bas = time.time()
for deneme in range(8):                      # uretim gibi: ACK gelene dek 0,25 s aralikla tekrar (en cok 8)
    s.sendto(cerceve, ("127.0.0.1", 5100)); gonder.append(time.time())
    son = time.time()
    while time.time() - son < 0.25 and ack is None:
        try: veri, _ = s.recvfrom(4096)
        except socket.timeout: continue
        for satir in veri.split(b"\n"):
            if not satir.strip(): continue
            try: m = decode(satir)
            except Exception: continue
            if m.get("type") == "ACK" and m.get("ref") == seq:
                ack = (time.time(), m)
    if ack: break
while ack is None and time.time() - bas < 6:  # son tekrardan sonra 4 s daha bekle
    try: veri, _ = s.recvfrom(4096)
    except socket.timeout: continue
    for satir in veri.split(b"\n"):
        try: m = decode(satir)
        except Exception: continue
        if m.get("type") == "ACK" and m.get("ref") == seq: ack = (time.time(), m)
print(json.dumps({"isaret": isaret, "seq": seq, "cerceve_B": len(cerceve), "gonderim_sayisi": len(gonder),
                  "ilk_gonderim": time.strftime("%H:%M:%S", time.localtime(gonder[0])) + f".{int(gonder[0]*1000)%1000:03d}",
                  "ack_geldi": ack is not None,
                  "ack_saati": (time.strftime("%H:%M:%S", time.localtime(ack[0])) + f".{int(ack[0]*1000)%1000:03d}") if ack else None,
                  "gidis_donus_ms": round((ack[0] - gonder[0]) * 1000) if ack else None,
                  "ack_icerik": ack[1] if ack else None}, ensure_ascii=False))
