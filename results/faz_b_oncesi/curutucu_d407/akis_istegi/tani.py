"""Ayirt et: mesaj alinmiyor mu, yoksa 'akran gorulmedi' hukmu mu yanlis?"""
import os, socket, sys, threading, time
from pathlib import Path
KOK = Path(r"O:\navitas")
for p in (KOK / "comms", KOK / "codes"):
    if str(p) not in sys.path: sys.path.insert(0, str(p))
os.environ.setdefault("MAVLINK20", "1")
from pymavlink import mavutil
from iha_komut_alici import mav_hedefi_biliniyor_mu
M = mavutil.mavlink

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.bind(("127.0.0.1", 0))
port = s.getsockname()[1]; s.close()

dur = threading.Event()
def proxy():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    mav = M.MAVLink(None, srcSystem=1, srcComponent=1)
    while not dur.is_set():
        hb = M.MAVLink_heartbeat_message(2, 3, 0, 0, 4, 3)
        sock.sendto(hb.pack(mav), ("127.0.0.1", port))
        time.sleep(0.5)
    sock.close()
threading.Thread(target=proxy, daemon=True).start()
time.sleep(0.3)

mav = mavutil.mavlink_connection("udp:127.0.0.1:%d" % port, source_system=250)
print("baglanti sinifi:", type(mav).__name__)
print("udp_server ozniteligi:", getattr(mav, "udp_server", "YOK"))
print("clients ozniteligi:", getattr(mav, "clients", "YOK"))
alinan = 0
t0 = time.monotonic()
while time.monotonic() - t0 < 4:
    m = mav.recv_match(blocking=True, timeout=0.3)
    if m is not None:
        alinan += 1
print("ALINAN mesaj:", alinan)
print("udp_server:", getattr(mav, "udp_server", "YOK"),
      "| clients:", getattr(mav, "clients", "YOK"),
      "| last_address:", getattr(mav, "last_address", "YOK"))
print("mav_hedefi_biliniyor_mu ->", mav_hedefi_biliniyor_mu(mav))
try:
    mav.mav.command_long_send(1, 1, 511, 0, 245, 500000, 0, 0, 0, 0, 0)
    print("command_long_send: istisna yok")
except Exception as e:
    print("command_long_send HATA:", e)
dur.set(); mav.close()
