"""
YKS (Yer Kontrol İstasyonu) — alan hakeminin açık yol tespitini canlı izlediği monitör.

Şartname §2.2.3: tespit edilen güzergâh YKS'de canlı görünmeli, hakem onaylamalı.
Bu düğüm gelen OPEN_ROUTE'u ekrana basar, ACK döner (hakem onayı simülasyonu).

Kullanım:
  python3 yks_monitor.py --bind 0.0.0.0:5005
"""
import argparse
import time

from link import UDPLink, SerialLink
from protocol import encode, ack, FrameReader


def main():
    ap = argparse.ArgumentParser(description="YKS açık yol monitörü (hakem)")
    ap.add_argument("--bind", default="0.0.0.0:5005")
    ap.add_argument("--serial", help="SiK telsiz seri portu")
    ap.add_argument("--baud", type=int, default=57600)
    args = ap.parse_args()

    if args.serial:
        link = SerialLink(args.serial, args.baud)
    else:
        h, p = args.bind.split(":")
        link = UDPLink(bind=(h, int(p)))
        print(f"[YKS] Hakem monitörü dinleniyor: {args.bind}")

    reader = FrameReader()
    try:
        while True:
            d, addr = link.recv()
            for m in reader.feed(d) if d else []:
                if m.get("type") == "OPEN_ROUTE":
                    print("─" * 44)
                    print(f"[YKS] AÇIK YOL TESPİTİ → {m['label'].upper()} (yol {m['road']})")
                    print(f"      güven={m['conf']}  seq={m['seq']}  t={m['t']}")
                    print(f"      HAKEM ONAYI: ✓ (otomatik)  →  İKA'ya aktarım onaylandı")
                    if addr is not None:
                        link.send(encode(ack(m["seq"], "yks")), addr)
    except KeyboardInterrupt:
        print("\n[YKS] kapatılıyor")
    finally:
        link.close()


if __name__ == "__main__":
    main()
