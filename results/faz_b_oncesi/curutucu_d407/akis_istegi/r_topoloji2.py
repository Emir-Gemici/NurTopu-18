"""D-407 · T207 gercek Jetson topolojisi: MAVProxy ISTEMCI iter, yayinci SUNUCU dinler.
Olculen: SET_MESSAGE_INTERVAL geri gidiyor mu, ne kadar gecikmeyle, hangi id/aralik."""
import os, socket, sys, threading, time, traceback
from pathlib import Path
KOK = Path(r"O:\navitas")
for p in (KOK / "comms", KOK / "codes"):
    if str(p) not in sys.path: sys.path.insert(0, str(p))
os.environ.setdefault("MAVLINK20", "1")
from pymavlink import mavutil
import iha_inis_yayinci as Y
from karar_sozlesmesi import (MAVLINK_AKIS_ISTEK_ARALIGI_S,
                              MAVLINK_AKIS_SESSIZLIK_TAVANI_S)
M = mavutil.mavlink

def bos_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]; s.close(); return p

class Proxy(threading.Thread):
    def __init__(self, port, extended=False):
        super().__init__(daemon=True)
        self.port, self.extended = port, extended
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(0.1)
        self.dur = threading.Event()
        self.komutlar = []; self.ilk = None; self.t0 = None; self.hata = None
        self.gonderilen = 0
    def run(self):
        self.t0 = time.monotonic()
        mav = M.MAVLink(None, srcSystem=1, srcComponent=1)
        cozucu = mavutil.mavlink.MAVLink(None)
        son = 0.0
        try:
            while not self.dur.is_set():
                simdi = time.monotonic()
                if simdi - son >= 0.5:
                    son = simdi
                    self.sock.sendto(M.MAVLink_heartbeat_message(2, 3, 0, 0, 4, 3).pack(mav),
                                     ("127.0.0.1", self.port)); self.gonderilen += 1
                    if self.extended:
                        self.sock.sendto(
                            M.MAVLink_extended_sys_state_message(0, 2).pack(mav),
                            ("127.0.0.1", self.port)); self.gonderilen += 1
                try:
                    veri, _ = self.sock.recvfrom(4096)
                except socket.timeout:
                    continue
                for m in (cozucu.parse_buffer(veri) or []):
                    if m.get_type() == "COMMAND_LONG":
                        if self.ilk is None: self.ilk = time.monotonic() - self.t0
                        self.komutlar.append((int(m.command), int(m.param1), int(m.param2)))
        except Exception:
            self.hata = traceback.format_exc()
    def kapat(self):
        self.dur.set(); self.join(2); self.sock.close()

def senaryo(ad, extended, sure):
    port = bos_port()
    mav = mavutil.mavlink_connection("udp:127.0.0.1:%d" % port, source_system=250)
    pr = Proxy(port, extended); pr.start(); time.sleep(0.3)
    ist = Y.AkisIstekcisi(mav, beklenen_sysid=1)
    alinan = 0; t0 = time.monotonic()
    while time.monotonic() - t0 < sure:
        m = mav.recv_match(blocking=True, timeout=0.2)
        if m is not None:
            alinan += 1; ist.gozle(m)
        ist.bakim()
    sayac = dict(ist.sayac); pr.kapat(); mav.close()
    print("\n== %s (%.0f s)" % (ad, sure))
    print("   proxy gonderdi=%d | yayinci aldi=%d | proxy hata=%s"
          % (pr.gonderilen, alinan, "YOK" if pr.hata is None else pr.hata.splitlines()[-1]))
    print("   GERI GELEN KOMUT=%d ilk_gecikme=%s" % (len(pr.komutlar), pr.ilk))
    print("   komut/id/aralik_us: %s" % sorted(set(pr.komutlar)))
    print("   sayac: %s | sessiz=%s" % (sayac, ist.sessiz))

print("aralik=%ss tavan=%ss | beklenen komut=%d id=[%d,%d]"
      % (MAVLINK_AKIS_ISTEK_ARALIGI_S, MAVLINK_AKIS_SESSIZLIK_TAVANI_S,
         M.MAV_CMD_SET_MESSAGE_INTERVAL, M.MAVLINK_MSG_ID_GLOBAL_POSITION_INT,
         M.MAVLINK_MSG_ID_EXTENDED_SYS_STATE))
senaryo("A · EXTENDED AKMIYOR (ArduCopter varsayilani)", False, 13)
senaryo("B · EXTENDED akiyor", True, 13)
