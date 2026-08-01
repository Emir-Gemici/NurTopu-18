"""
İHA tarafı — açık yol tespitini YKS'ye ve İKA'ya gönderir (şartname §2.2.3).

Görev kuralı: aktarım İHA HAVADAYKEN tamamlanmalı ve alan hakemi YKS'de canlı
onaylamalı. Bu yüzden mesaj ACK alınana kadar (veya N kez) tekrarlanır — RF
kaybına karşı dayanıklılık.

Kullanım (dev/UDP):
  python3 iha_sender.py --road 2 --conf 0.91 --ika 127.0.0.1:5006 --yks 127.0.0.1:5005
Saha (SiK telsiz):
  python3 iha_sender.py --road 2 --conf 0.91 --serial /dev/ttyUSB0
"""
import argparse
import time

try:
    from .link import UDPLink, SerialLink
    from .protocol import open_route, encode, FrameReader
except ImportError:
    from link import UDPLink, SerialLink
    from protocol import open_route, encode, FrameReader


class IhaSender:
    def __init__(self, link, peers=None):
        self.link = link
        self.peers = peers or {}          # {"ika": (host,port), "yks": (...)}
        self.reader = FrameReader()

    def send_open_route(self, road, conf, waypoints=None, ref_xy=None,
                        repeat=8, interval=0.25, wait_ack=True):
        """Açık yolu gönder; ACK gelene dek tekrarla. (seq, acked_set) döner."""
        msg = open_route(road, conf, waypoints, ref_xy)
        data = encode(msg)
        acked = set()
        targets = list(self.peers.items()) or [(None, None)]
        for _ in range(repeat):
            for name, peer in targets:
                if name not in acked:
                    self.link.send(data, peer)
            if not wait_ack:
                time.sleep(interval)
                continue
            t0 = time.time()
            while time.time() - t0 < interval:
                d, addr = self.link.recv()
                for m in self.reader.feed(d) if d else []:
                    node = m.get("node")
                    expected_peer = self.peers.get(node)
                    valid_source = expected_peer is None or addr == expected_peer
                    if (m.get("type") == "ACK" and m.get("ref") == msg["seq"]
                            and m.get("ref_session") in (None, msg.get("session"))
                            and node in self.peers and valid_source):
                        acked.add(node)
            if self.peers and acked >= set(self.peers):
                break
        return msg["seq"], acked


def _addr(s):
    h, p = s.split(":")
    return (h, int(p))


def main():
    ap = argparse.ArgumentParser(description="İHA → açık yol gönderici")
    ap.add_argument("--road", type=int, choices=[1, 2, 3],
                    help="Açık yol: 1=sol 2=orta 3=sag")
    ap.add_argument("--conf", type=float, default=0.9)
    ap.add_argument("--ref", help="referans noktası 'x,y' (metre)")
    ap.add_argument("--rota-json",
                    help="iha_haritala çıktısı rota.json — road/conf/referans/"
                         "waypoint'leri dosyadan yükler")
    ap.add_argument("--ika", help="İKA adresi host:port (UDP)")
    ap.add_argument("--yks", help="YKS adresi host:port (UDP)")
    ap.add_argument("--serial", help="SiK telsiz seri portu (saha)")
    ap.add_argument("--baud", type=int, default=57600)
    args = ap.parse_args()

    road, conf, ref_xy, waypoints = args.road, args.conf, None, None
    if args.rota_json:
        import json
        with open(args.rota_json, encoding="utf-8") as f:
            rota = json.load(f)
        road = int(rota["yol_no"])
        conf = float(rota.get("guven", conf))
        ref_xy = rota.get("referans_xy")
        waypoints = rota.get("rota_yerel")
    elif args.ref:
        ref_xy = [float(v) for v in args.ref.split(",")]
    if road is None:
        ap.error("--road veya --rota-json gerekli")

    if args.serial:
        link = SerialLink(args.serial, args.baud)
        peers = {"ika": None}              # İKA ACK'i aynı seri hattan döner
    else:
        link = UDPLink()
        peers = {}
        if args.ika:
            peers["ika"] = _addr(args.ika)
        if args.yks:
            peers["yks"] = _addr(args.yks)

    sender = IhaSender(link, peers)
    print(f"[İHA] Açık yol gönderiliyor: road={road} conf={conf} "
          f"ref={ref_xy} wp={len(waypoints or [])}")
    seq, acked = sender.send_open_route(road, conf, waypoints, ref_xy)
    if args.serial:
        print(f"[İHA] {'✓ İKA tarafından onaylandı' if 'ika' in acked else '⚠ ACK alınamadı'} "
              f"(seq={seq}) — telsiz")
    elif acked:
        print(f"[İHA] ✓ Onaylandı (seq={seq}) — ACK: {sorted(acked)}")
    else:
        print(f"[İHA] ⚠ ACK alınamadı (seq={seq}) — RF/bağlantı kontrol et")
    link.close()


if __name__ == "__main__":
    main()
