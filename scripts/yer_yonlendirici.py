#!/usr/bin/env python3
"""Yer MAVLink bayt yonlendiricisi — RFD900A (COM) <-> Mission Planner (UDP) + YKI tunel ucu (UDP).

NEDEN (18 Eyl 2026, K8a): Mission Planner'in MAVLink aynasi (SerialOutput, Write access)
yer->hava yonunde ~%54 kayip ve 400 ms RTT verdi; TUNEL_SAHA_RUNBOOK §9 yedek plani
"yer yonlendiricisi" der. Bu betik COM portunun TEK sahibidir; gelen baytlari oldugu gibi
iki UDP hedefe kopyalar, iki hedeften gelen datagramlari oldugu gibi seri porta yazar.
Paket cozumu YAPMAZ (bayt boru); MP ve yks_gui akis ayristirma yapar.

YENIDEN BAGLANTI (19 Eyl 2026): USB kablosu cikip takilinca pyserial her cagrida
"ClearCommError/WriteFile failed (PermissionError 13)" atiyor ve eski tutamac bir daha
duzelmiyordu (olculdu: seri_hata 1793, seri->udp 0 B/s). Artik seri hata -> tutamac
kapatilir, ayni port/baud 1 s arayla yeniden acilir; bu sirada UDP'den gelen veri dusurulup
sayilir. UDP soketleri ASLA yeniden acilmaz: MP ve YKI akrani kaynak adresinden ogrenir.

  MP: baglanti turu UDP, port 14550 (dinler); YKI: yks_gui --tunel 127.0.0.1:14570
  python -B scripts/yer_yonlendirici.py --port COM7 --baud 57600
"""
import argparse
import socket
import sys
import threading
import time

import serial

# PortNotOpenError (eski adi portNotOpenError) SerialException alt sinifidir.
SERI_HATALARI = (serial.SerialException, OSError)
YENIDEN_DENEME_S = 1.0  # iki acma denemesi arasi (acilip hemen dusen port da dahil)
DENEME_LOG_S = 5.0  # basarisiz deneme logu en fazla bu aralikla


def _seri_ac(port, baud):
    return serial.Serial(port, baud, timeout=0.05, exclusive=True)


def _log(mesaj, hata=False):
    print(mesaj, file=sys.stderr if hata else sys.stdout, flush=True)


def udp_hedefler(mp, tunel):
    hedefler = []
    for ad, hp in (("mp", mp), ("tunel", tunel)):
        h, p = hp.rsplit(":", 1)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(("127.0.0.1", 0))
        s.settimeout(0.2)
        hedefler.append((ad, s, (h, int(p))))
    return hedefler


class Yonlendirici:
    """Seri portu yalniz oku ipligi acar/kapatir; yazma hatasi yalniz isaretler (_bozuk)."""

    def __init__(self, port, baud, hedefler, ac=_seri_ac, saat=time.monotonic, uyku=time.sleep, log=_log):
        self.port, self.baud, self.hedefler = port, baud, hedefler
        self._ac, self._saat, self._uyku, self._log = ac, saat, uyku, log
        self.kilit = threading.Lock()
        self.dur = threading.Event()
        self.say = {"seri_udp": 0, "mp_seri": 0, "tunel_seri": 0, "seri_hata": 0,
                    "yeniden_baglanti": 0, "dusen_udp": 0}
        self.ser = ac(port, baud)  # ilk acilis eskisi gibi: port yoksa betik baslamaz
        self._bozuk = False
        self._kopus_t = self._son_log = None
        self._deneme = 0

    def bagli(self):
        return self.ser is not None and not self._bozuk

    def _hata(self, e, yon):
        self.say["seri_hata"] += 1
        if not self._bozuk:
            self._log(f"[YONLENDIRICI] seri {yon} hatasi: {e} -> port kapatilip yeniden acilacak", True)
        self._bozuk = True

    def _kapat(self):
        with self.kilit:
            ser, self.ser, self._bozuk = self.ser, None, False
        try:
            ser.close()
        except Exception:  # olu tutamac kapanirken de atabilir; kapanmis sayilir
            pass
        self._kopus_t, self._son_log, self._deneme = self._saat(), None, 0

    def _yeniden_dene(self):
        self._uyku(YENIDEN_DENEME_S)
        self._deneme += 1
        simdi = self._saat()
        try:
            ser = self._ac(self.port, self.baud)
        except SERI_HATALARI as e:
            if self._son_log is None or simdi - self._son_log >= DENEME_LOG_S:
                self._son_log = simdi
                self._log(f"[YONLENDIRICI] seri yeniden acilamadi {self.port} (deneme {self._deneme}, "
                          f"kopukluk {simdi - self._kopus_t:.1f} s): {e}", True)
            return
        with self.kilit:
            self.ser = ser
        self.say["yeniden_baglanti"] += 1
        self._log(f"[YONLENDIRICI] SERI YENIDEN BAGLANDI {self.port} "
                  f"(kopukluk {simdi - self._kopus_t:.1f} s, deneme {self._deneme})")

    def seri_adim(self):
        """Oku ipliginin bir turu: bagliysa oku ve iki hedefe kopyala; kopuksa kapat/yeniden ac."""
        if self.ser is not None and self._bozuk:
            self._kapat()
        if self.ser is None:
            self._yeniden_dene()
            return
        try:
            n = self.ser.in_waiting
            veri = self.ser.read(n if n else 1)
        except SERI_HATALARI as e:
            self._hata(e, "okuma")
            self._kapat()
            return
        if not veri:
            return
        self.say["seri_udp"] += len(veri)
        for _, s, hedef in self.hedefler:
            try:
                s.sendto(veri, hedef)
            except OSError:
                pass  # hedef dinlemiyor (MP/YKI kapali) — normal

    def udp_adim(self, ad, s):
        try:
            veri, _ = s.recvfrom(4096)
        except OSError:  # zaman asimi veya Windows ICMP sifirlamasi — normal
            return
        with self.kilit:
            if not self.bagli():
                self.say["dusen_udp"] += 1  # seri kopuk: datagram dusurulur, sayilir
                return
            try:
                self.ser.write(veri)
            except SERI_HATALARI as e:
                self._hata(e, "yazma")
                return
        self.say[f"{ad}_seri"] += len(veri)

    def baslat(self):
        def dongu(adim, *arg):
            while not self.dur.is_set():
                adim(*arg)
        threading.Thread(target=dongu, args=(self.seri_adim,), daemon=True).start()
        for ad, s, _ in self.hedefler:
            threading.Thread(target=dongu, args=(self.udp_adim, ad, s), daemon=True).start()

    def istatistik_satiri(self, fark, aralik):
        return (f"[YONLENDIRICI] {time.strftime('%H:%M:%S')} seri->udp {fark['seri_udp']/aralik:.0f} B/s · "
                f"mp->seri {fark['mp_seri']/aralik:.0f} B/s · tunel->seri {fark['tunel_seri']/aralik:.0f} B/s · "
                f"seri_hata {self.say['seri_hata']} · seri_bagli={int(self.bagli())} · "
                f"yeniden_baglanti={self.say['yeniden_baglanti']} · dusen_udp={self.say['dusen_udp']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", required=True, help="RFD900A yer modulu COM portu")
    ap.add_argument("--baud", type=int, default=57600)
    ap.add_argument("--mp", default="127.0.0.1:14550", help="Mission Planner UDP dinleme ucu")
    ap.add_argument("--tunel", default="127.0.0.1:14570", help="YKI tunel ucu (yks_gui --tunel)")
    ap.add_argument("--istatistik", type=float, default=5.0, help="sayac satiri araligi (s)")
    a = ap.parse_args()

    y = Yonlendirici(a.port, a.baud, udp_hedefler(a.mp, a.tunel))
    print(f"[YONLENDIRICI] {a.port}@{a.baud} <-> mp {a.mp} + tunel {a.tunel}", flush=True)
    y.baslat()
    onceki = dict(y.say)
    while True:
        time.sleep(a.istatistik)
        fark = {k: y.say[k] - onceki[k] for k in y.say}
        onceki = dict(y.say)
        print(y.istatistik_satiri(fark, a.istatistik), flush=True)


if __name__ == "__main__":
    main()
