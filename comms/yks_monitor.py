"""
⛔ EMEKLİ — SAHADA KULLANILMAZ (P8 · D-392 · 2026-09-02).

Bu eski monitör gelen OPEN_ROUTE'a **"HAKEM ONAYI: ✓ (otomatik)"** basar ve
ACK'i KENDİSİ döner. Üretim akışında hakem onayı İKİ AŞAMALIDIR ve `yks_gui`
içindedir; bu betik sahada yanlışlıkla açılırsa onay kapısını DELER (rota,
hakem görmeden "onaylanmış" olur). Ölçüm: hiçbir test bu dosyayı zorlamıyor,
tek meşru kullanıcı eski simülasyon tatbikatlarıdır.

Madde 18 gereği SİLİNMEDİ. Bilerek (ör. eski bir sim tatbikatını yeniden
üretmek için) koşturmak gerekiyorsa: `--legacy-bilerek` bayrağı zorunludur.

Kullanım (yalnız legacy):
  python3 yks_monitor.py --legacy-bilerek --bind 0.0.0.0:5005
"""
import argparse
import sys
import time

from link import UDPLink, SerialLink
from protocol import encode, ack, FrameReader, MESAJ_OPEN_ROUTE


def main():
    ap = argparse.ArgumentParser(description="YKS açık yol monitörü (hakem)")
    ap.add_argument("--bind", default="0.0.0.0:5005")
    ap.add_argument("--serial", help="SiK telsiz seri portu")
    ap.add_argument("--baud", type=int, default=57600)
    ap.add_argument("--legacy-bilerek", action="store_true",
                    help="Emekli betiği BILEREK koştur (sahada yasak; "
                         "hakem onayını otomatik basar — D-392)")
    args = ap.parse_args()

    if not args.legacy_bilerek:
        print("[YKS_MONITOR] ⛔ EMEKLİ BETİK (D-392): OPEN_ROUTE'a otomatik "
              "'hakem onayı' basar ve iki aşamalı onay kapısını DELER.\n"
              "Sahada `yks_gui` kullanılır. Bilerek koşturmak için: "
              "--legacy-bilerek", file=sys.stderr)
        return 2

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
                if m.get("type") == MESAJ_OPEN_ROUTE:
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
    return 0


if __name__ == "__main__":
    sys.exit(main())
