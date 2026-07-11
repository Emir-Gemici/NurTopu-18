"""
İHA tarafı — HTAB'de açık yolu TESPİT eder ve comms ile YKS + İKA'ya gönderir.

Tespit (detect_open_road): gerçekte İHA kamerasından YOLOv8-seg ile 3 yoldan açık
olanı bulur. Bu demoda 'arena' ground-truth (veya --road) kullanılır — vision çıktısı
buraya bağlanacak yer burası.

Kullanım (dev/UDP):
  python3 iha_detect_send.py --scenario kolay --ika 127.0.0.1:5006 --yks 127.0.0.1:5005
Saha (SiK telsiz):
  python3 iha_detect_send.py --scenario kolay --serial /dev/ttyUSB0
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))                       # arena
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "comms"))
import arena
from link import UDPLink, SerialLink
from iha_sender import IhaSender


def detect_open_road(scenario=None, road=None):
    """Açık yolu döndür (1/2/3). GERÇEKTE: YOLO ile kameradan tespit.
    DEMO: arena ground-truth — vision modeli buraya bağlanacak."""
    if road:
        return road
    return arena.open_road(scenario or "kolay")


def _addr(s):
    h, p = s.split(":")
    return (h, int(p))


def main():
    ap = argparse.ArgumentParser(description="İHA açık yol tespit + gönderici")
    ap.add_argument("--scenario", choices=["kolay", "orta", "zor"], default="kolay")
    ap.add_argument("--road", type=int, choices=[1, 2, 3], help="tespiti elle ver (test)")
    ap.add_argument("--conf", type=float, default=0.92)
    ap.add_argument("--ika"); ap.add_argument("--yks")
    ap.add_argument("--serial"); ap.add_argument("--baud", type=int, default=57600)
    args = ap.parse_args()

    road = detect_open_road(args.scenario, args.road)
    print(f"[İHA] HTAB tarandı → AÇIK YOL tespiti: {arena.ROAD_LABEL[road].upper()} "
          f"({road})  conf={args.conf}")

    if args.serial:
        link = SerialLink(args.serial, args.baud)
        peers = {"broadcast": None}
    else:
        link = UDPLink()
        peers = {}
        if args.ika:
            peers["ika"] = _addr(args.ika)
        if args.yks:
            peers["yks"] = _addr(args.yks)

    sender = IhaSender(link, peers)
    seq, acked = sender.send_open_route(road, args.conf, wait_ack=not args.serial)
    if args.serial:
        print(f"[İHA] telsiz yayın yapıldı (seq={seq})")
    elif acked:
        print(f"[İHA] ✓ aktarım onaylandı (seq={seq}) — ACK: {sorted(acked)}")
    else:
        print(f"[İHA] ⚠ ACK yok (seq={seq})")
    link.close()


if __name__ == "__main__":
    main()
