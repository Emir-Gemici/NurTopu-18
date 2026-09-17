"""TEZGAH: MAVLink TCP (SITL/MAVProxy) <-> UDP (Jetson) ham bayt koprusu (ONARIM-18).

Uretim kodu DEGIL. PC'de calisan ArduCopter SITL'i (tcp:127.0.0.1:5760) Jetson'daki
cogullayiciya (mavproxy --master=udpin:0.0.0.0:14560) tasir; Jetson cevaplari (komutlar)
geri SITL'e yazilir. Cerceve cozmez; baytlari oldugu gibi aktarir.

--kes S: calisirken S saniye veri aktarmayi durdurur (hat kopmasi dayaniklilik testi).
Kullanim: .venv/bin/python scripts/tezgah/mavlink_tcp_udp_kopru.py --jetson 10.21.8.7:14560
"""
import argparse
import select
import socket
import sys
import time


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--tcp", default="127.0.0.1:5760")
    ap.add_argument("--jetson", required=True)
    ap.add_argument("--sure", type=float, default=0.0, help="0 = surekli")
    ap.add_argument("--kes-bas", type=float, default=None, help="bu saniyede aktarimi kes")
    ap.add_argument("--kes-sure", type=float, default=0.0)
    a = ap.parse_args(argv)
    th, tp = a.tcp.rsplit(":", 1)
    jh, jp = a.jetson.rsplit(":", 1)
    jetson = (jh, int(jp))
    t = socket.create_connection((th, int(tp)), timeout=10)
    t.setblocking(False)
    u = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    u.bind(("0.0.0.0", 0))
    u.setblocking(False)
    bas = time.monotonic()
    sayac = {"tcp_to_udp": 0, "udp_to_tcp": 0, "kesilen": 0}
    son_rapor = bas
    print(f"kopru: tcp {a.tcp} <-> udp {a.jetson} (yerel udp {u.getsockname()[1]})", flush=True)
    while a.sure <= 0 or time.monotonic() - bas < a.sure:
        simdi = time.monotonic() - bas
        kesik = a.kes_bas is not None and a.kes_bas <= simdi < a.kes_bas + a.kes_sure
        r, _, _ = select.select([t, u], [], [], 0.2)
        if t in r:
            veri = t.recv(65536)
            if not veri:
                print("TCP kapandi", flush=True)
                return 1
            if kesik:
                sayac["kesilen"] += len(veri)
            else:
                u.sendto(veri, jetson)
                sayac["tcp_to_udp"] += len(veri)
        if u in r:
            veri, _ = u.recvfrom(65536)
            if not kesik:
                t.sendall(veri)
                sayac["udp_to_tcp"] += len(veri)
        if time.monotonic() - son_rapor >= 5:
            son_rapor = time.monotonic()
            print(f"t={simdi:.0f}s {sayac}{' KESIK' if kesik else ''}", flush=True)
    print(f"bitti {sayac}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
