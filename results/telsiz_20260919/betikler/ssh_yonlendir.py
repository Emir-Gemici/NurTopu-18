"""PC yerel portunu SSH uzerinden Jetson'daki 127.0.0.1:<port>'a yonlendir (paramiko direct-tcpip).
Kullanim: ssh_yonlendir.py <jetson> <yerel_port> <uzak_port> [<yerel_port> <uzak_port> ...]  (parola NAVITAS_SIFRE)"""
import os, sys, socket, threading, select, paramiko
host=sys.argv[1]; ciftler=[(int(sys.argv[i]),int(sys.argv[i+1])) for i in range(2,len(sys.argv),2)]
c=paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(host, username=os.environ.get("NAVITAS_KULLANICI","n4vitas"), password=os.environ["NAVITAS_SIFRE"], timeout=8, look_for_keys=False, allow_agent=False)
tr=c.get_transport(); tr.set_keepalive(10)
def _kopyala(kaynak_oku, hedef_yaz, kapat):
    try:
        while True:
            d=kaynak_oku(65536)
            if not d: break
            hedef_yaz(d)
    except Exception:
        pass
    finally:
        kapat()
def pompa(sock, uzak):
    # NEDEN iki is parcacigi: Windows'ta select() paramiko Channel ile guvenilir degil (olculdu, 10053).
    try: ch=tr.open_channel("direct-tcpip", ("127.0.0.1", uzak), sock.getpeername(), timeout=10)
    except Exception as e: print("kanal acilamadi:", e, flush=True); sock.close(); return
    def kapat():
        for x in (ch, sock):
            try: x.close()
            except Exception: pass
    threading.Thread(target=_kopyala, args=(sock.recv, ch.sendall, kapat), daemon=True).start()
    _kopyala(ch.recv, sock.sendall, kapat)
def dinle(yerel, uzak):
    s=socket.socket(); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1); s.bind(("127.0.0.1", yerel)); s.listen(8)
    print(f"yonlendirme: 127.0.0.1:{yerel} -> {host}:127.0.0.1:{uzak}", flush=True)
    while True:
        k,_=s.accept(); threading.Thread(target=pompa, args=(k,uzak), daemon=True).start()
for y,u in ciftler: threading.Thread(target=dinle, args=(y,u), daemon=True).start()
threading.Event().wait()
