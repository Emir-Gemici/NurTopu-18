#!/usr/bin/env python3
"""Yer MAVLink bayt yonlendiricisi — RFD900A (COM) <-> Mission Planner (UDP) + YKI tunel ucu (UDP).

NEDEN (18 Eyl 2026, K8a): Mission Planner'in MAVLink aynasi (SerialOutput, Write access)
yer->hava yonunde ~%54 kayip ve 400 ms RTT verdi; TUNEL_SAHA_RUNBOOK §9 yedek plani
"yer yonlendiricisi" der. Bu betik COM portunun TEK sahibidir; gelen baytlari oldugu gibi
iki UDP hedefe kopyalar, iki hedeften gelen datagramlari oldugu gibi seri porta yazar.
Paket cozumu YAPMAZ (bayt boru); MP ve yks_gui akis ayristirma yapar.

  MP: baglanti turu UDP, port 14550 (dinler); YKI: yks_gui --tunel 127.0.0.1:14570
  python -B scripts/yer_yonlendirici.py --port COM7 --baud 57600
"""
import argparse
import socket
import sys
import threading
import time

import serial


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", required=True, help="RFD900A yer modulu COM portu")
    ap.add_argument("--baud", type=int, default=57600)
    ap.add_argument("--mp", default="127.0.0.1:14550", help="Mission Planner UDP dinleme ucu")
    ap.add_argument("--tunel", default="127.0.0.1:14570", help="YKI tunel ucu (yks_gui --tunel)")
    ap.add_argument("--istatistik", type=float, default=5.0, help="sayac satiri araligi (s)")
    a = ap.parse_args()

    hedefler = []
    for ad, hp in (("mp", a.mp), ("tunel", a.tunel)):
        h, p = hp.rsplit(":", 1)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(("127.0.0.1", 0))
        s.settimeout(0.2)
        hedefler.append((ad, s, (h, int(p))))
    ser = serial.Serial(a.port, a.baud, timeout=0.05, exclusive=True)
    kilit = threading.Lock()
    say = {"seri_udp": 0, "mp_seri": 0, "tunel_seri": 0, "seri_hata": 0}
    print(f"[YONLENDIRICI] {a.port}@{a.baud} <-> mp {a.mp} + tunel {a.tunel}", flush=True)

    def seri_oku():
        while True:
            try:
                n = ser.in_waiting
                veri = ser.read(n if n else 1)
            except serial.SerialException as e:
                say["seri_hata"] += 1
                print(f"[YONLENDIRICI] seri okuma hatasi: {e}", file=sys.stderr, flush=True)
                time.sleep(0.5)
                continue
            if not veri:
                continue
            say["seri_udp"] += len(veri)
            for _, s, hedef in hedefler:
                try:
                    s.sendto(veri, hedef)
                except OSError:
                    pass  # hedef dinlemiyor (MP/YKI kapali) — normal

    def udp_oku(ad, s):
        while True:
            try:
                veri, _ = s.recvfrom(4096)
            except socket.timeout:
                continue
            except OSError:
                continue
            with kilit:
                try:
                    ser.write(veri)
                except serial.SerialException as e:
                    say["seri_hata"] += 1
                    print(f"[YONLENDIRICI] seri yazma hatasi: {e}", file=sys.stderr, flush=True)
                    continue
            say[f"{ad}_seri"] += len(veri)

    threading.Thread(target=seri_oku, daemon=True).start()
    for ad, s, _ in hedefler:
        threading.Thread(target=udp_oku, args=(ad, s), daemon=True).start()
    onceki = dict(say)
    while True:
        time.sleep(a.istatistik)
        fark = {k: say[k] - onceki[k] for k in say}
        onceki = dict(say)
        print(f"[YONLENDIRICI] {time.strftime('%H:%M:%S')} seri->udp {fark['seri_udp']/a.istatistik:.0f} B/s · "
              f"mp->seri {fark['mp_seri']/a.istatistik:.0f} B/s · tunel->seri {fark['tunel_seri']/a.istatistik:.0f} B/s · "
              f"seri_hata {say['seri_hata']}", flush=True)


if __name__ == "__main__":
    main()
