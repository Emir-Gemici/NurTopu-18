"""
İKA tarafı — İHA'dan açık yol verisini alır, ACK döner, en güncel rotayı dışa açar.

İKA navigasyonu (ika_nav) bu sınıfı kullanarak "gelen veriye göre" hareket eder:
    rx = IkaReceiver(UDPLink(bind=("0.0.0.0", 5006)))
    rx.start()                      # arka planda dinler
    ...
    route = rx.latest               # {"road":2,"label":"orta",...} veya None
    if route: plan_path(route["road"])

Kullanım (dev/UDP):
  python3 ika_receiver.py --bind 0.0.0.0:5006
Saha (SiK telsiz):
  python3 ika_receiver.py --serial /dev/ttyUSB0
"""
import argparse
import threading
import time

from link import UDPLink, SerialLink
from protocol import encode, ack, FrameReader


class IkaReceiver:
    def __init__(self, link, node="ika", send_ack=True, hb_timeout=3.0):
        self.link = link
        self.node = node
        self.send_ack = send_ack
        self.hb_timeout = hb_timeout    # sn: bu süre mesaj gelmezse bağlantı KAYIP
        self.reader = FrameReader()
        self.latest = None              # son OPEN_ROUTE mesajı (kayıpta KORUNUR)
        self.last_rx = None             # son mesajın (HEARTBEAT dahil) zamanı
        self.link_lost = False
        self._stop = threading.Event()
        self._thr = None
        self.on_route = None            # callback(msg)
        self.on_link_lost = None        # callback() — navigasyon GÜVENLİ DURMA tetiği
        self.on_link_back = None        # callback() — kaldığı wp'den devam tetiği

    @property
    def link_ok(self):
        """Navigasyon her adımda bunu kontrol eder; False ise araç DURUR."""
        return self.last_rx is not None and not self.link_lost

    def _handle(self, msg, addr):
        self.last_rx = time.time()
        if self.link_lost:              # bağlantı geri geldi
            self.link_lost = False
            if self.on_link_back:
                self.on_link_back()
        if msg.get("type") == "OPEN_ROUTE":
            self.latest = msg
            if self.send_ack and addr is not None:
                self.link.send(encode(ack(msg["seq"], self.node)), addr)
            if self.on_route:
                self.on_route(msg)

    def poll(self):
        """Bir kez al-işle (bloklamayan, link timeout'una bağlı)."""
        d, addr = self.link.recv()
        for m in self.reader.feed(d) if d else []:
            self._handle(m, addr)
        if (self.last_rx is not None and not self.link_lost
                and time.time() - self.last_rx > self.hb_timeout):
            self.link_lost = True       # rota önbelleği (latest) silinmez
            if self.on_link_lost:
                self.on_link_lost()

    def _loop(self):
        while not self._stop.is_set():
            self.poll()

    def start(self):
        """Arka planda dinlemeye başla."""
        self._thr = threading.Thread(target=self._loop, daemon=True)
        self._thr.start()
        return self

    def stop(self):
        self._stop.set()
        if self._thr:
            self._thr.join(timeout=1)


def main():
    ap = argparse.ArgumentParser(description="İKA → açık yol alıcı")
    ap.add_argument("--bind", default="0.0.0.0:5006", help="UDP bind host:port")
    ap.add_argument("--serial", help="SiK telsiz seri portu (saha)")
    ap.add_argument("--baud", type=int, default=57600)
    args = ap.parse_args()

    if args.serial:
        link = SerialLink(args.serial, args.baud)
    else:
        h, p = args.bind.split(":")
        link = UDPLink(bind=(h, int(p)))
        print(f"[İKA] Dinleniyor: {args.bind}")

    rx = IkaReceiver(link)
    rx.on_route = lambda m: print(
        f"[İKA] ✓ Açık yol alındı: {m['label'].upper()} ({m['road']}) "
        f"conf={m['conf']} seq={m['seq']} ref={m.get('ref_xy')} "
        f"wp={len(m.get('waypoints') or [])} → rota planlanıyor")
    rx.on_link_lost = lambda: print(
        f"[İKA] ⚠ BAĞLANTI KAYIP ({rx.hb_timeout:.0f} sn sessizlik) → GÜVENLİ DURMA")
    rx.on_link_back = lambda: print(
        "[İKA] ✓ Bağlantı geri geldi → kaldığı waypoint'ten devam")
    try:
        while True:
            rx.poll()
    except KeyboardInterrupt:
        print("\n[İKA] kapatılıyor")
    finally:
        link.close()


if __name__ == "__main__":
    main()
