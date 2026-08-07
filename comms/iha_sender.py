"""NEDEN: Açık yol veya güvenli NO_ROUTE kararı, ancak açıkça seçilmiş bir
İKA/YKS UDP akranına ya da SiK seri hattına gönderilirse aktarılmış sayılabilir.

Görev kuralı: aktarım İHA HAVADAYKEN tamamlanmalı ve alan hakemi YKS'de canlı
onaylamalı. Bu yüzden mesaj ACK alınana kadar (veya N kez) tekrarlanır — RF
kaybına karşı dayanıklılık.

İHA tarafı — açık yol tespitini YKS'ye ve İKA'ya gönderir (şartname §2.2.3).

Kullanım (dev/UDP):
  python3 iha_sender.py --road 2 --conf 0.91 --ika 127.0.0.1:5006 --yks 127.0.0.1:5005
Saha (SiK telsiz):
  python3 iha_sender.py --road 2 --conf 0.91 --serial /dev/ttyUSB0
"""
import argparse
import json
import math
import sys
import time

from link import UDPLink, SerialLink
from protocol import (open_route, rota_yok, heartbeat, iha_landed, encode,
                      FrameReader)

for _akim in (sys.stdout, sys.stderr):
    try:
        _akim.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass


MAX_WAYPOINTS = 64
MAX_SEGMENT_M = 2.10
MAX_LOCAL_EXTENT_M = 60.0
SOURCE_TOLERANCE_M = 0.15


def _xy(value, field):
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ValueError(f"{field} [x, y] biçiminde olmalı")
    try:
        x, y = float(value[0]), float(value[1])
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} sayısal olmalı") from exc
    if not math.isfinite(x) or not math.isfinite(y):
        raise ValueError(f"{field} sonlu sayılar içermeli")
    return x, y


def rota_geometrisini_dogrula(ref_xy, waypoints):
    """İKA'ya gidecek dinamik A* geometri sözleşmesini denetle."""
    _xy(ref_xy, "ref_xy")
    if not isinstance(waypoints, (list, tuple)) or not 2 <= len(waypoints) <= MAX_WAYPOINTS:
        raise ValueError(f"waypoints 2..{MAX_WAYPOINTS} nokta içermeli")
    yerel = [_xy(wp, f"waypoints[{i}]") for i, wp in enumerate(waypoints)]
    if math.hypot(*yerel[0]) > SOURCE_TOLERANCE_M:
        raise ValueError("ilk yerel waypoint costmap başlangıç ankuru [0, 0] olmalı")
    if any(math.hypot(x, y) > MAX_LOCAL_EXTENT_M for x, y in yerel):
        raise ValueError("yerel waypoint HTAB sınırını aşıyor")
    for i, (a, b) in enumerate(zip(yerel, yerel[1:]), 1):
        if math.dist(a, b) > MAX_SEGMENT_M:
            raise ValueError(f"waypoint[{i - 1}]→waypoint[{i}] azami {MAX_SEGMENT_M:.2f} m olmalı")
    return yerel


def rota_json_oku(path):
    """iha_haritala'nın atomik rota.json çıktısını protokol alanlarına çevir."""
    with open(path, encoding="utf-8") as f:
        rota = json.load(f)
    try:
        road = int(rota["yol_no"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("rota.json geçerli yol_no içermiyor") from exc
    conf = float(rota.get("guven", 0.0))
    ref_xy = rota.get("referans_xy")
    waypoints = rota.get("rota_yerel")
    return road, conf, ref_xy, rota_geometrisini_dogrula(ref_xy, waypoints)


class IhaSender:
    def __init__(self, link, peers=None):
        self.link = link
        self.peers = peers or {}          # {"ika": (host,port), "yks": (...)}
        self.reader = FrameReader()

    def _tekrarli_gonder(self, msg, repeat=8, interval=0.25, wait_ack=True):
        """Bir protokol mesajını tüm akranlardan ACK alana dek tekrarla."""
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
                d, _addr = self.link.recv()
                for m in self.reader.feed(d) if d else []:
                    if m.get("type") == "ACK" and m.get("ref") == msg["seq"]:
                        acked.add(m.get("node"))
            if self.peers and acked >= set(self.peers):
                break
        return msg["seq"], acked

    def send_open_route(self, road, conf, waypoints=None, ref_xy=None,
                        repeat=8, interval=0.25, wait_ack=True):
        """Açık dinamik rotayı gönder; ACK gelene dek tekrarla."""
        # İKA/broadcast hattında yol kimliği tek başına hareket komutu değildir.
        # Geometriyi burada da denetlemek eski statik üreticilerin sessizce
        # çalışmasını engeller.
        if "ika" in self.peers or "broadcast" in self.peers:
            waypoints = rota_geometrisini_dogrula(ref_xy, waypoints)
        msg = open_route(road, conf, waypoints, ref_xy)
        return self._tekrarli_gonder(msg, repeat=repeat, interval=interval,
                                     wait_ack=wait_ack)

    def send_no_route(self, sebep, detay=None, repeat=8, interval=0.25,
                      wait_ack=True):
        """Costmap rota üretemedi bilgisini ACK'li olarak tüm akranlara ilet."""
        msg = rota_yok(sebep, detay)
        return self._tekrarli_gonder(msg, repeat=repeat, interval=interval,
                                     wait_ack=wait_ack)

    def send_heartbeat(self, node="iha"):
        """Bağlantı-failsafe için tüm alıcılara tek bir canlılık çerçevesi yayınla."""
        msg = heartbeat(node)
        data = encode(msg)
        for _name, peer in (list(self.peers.items()) or [(None, None)]):
            self.link.send(data, peer)
        return msg["seq"]

    def send_iha_landed(self, repeat=8, interval=0.25, wait_ack=True):
        """İHA iniş olayını tüm yapılandırılmış akranlara ACK'li gönder."""
        msg = iha_landed()
        return self._tekrarli_gonder(
            msg, repeat=repeat, interval=interval, wait_ack=wait_ack)


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
    ap.add_argument("--no-route", metavar="SEBEP",
                    help="costmap rota üretemedi bildirimi (ör. KAPALI_DAR)")
    ap.add_argument("--detay", help="NO_ROUTE için insan-okunur ek açıklama")
    ap.add_argument("--ika", help="İKA adresi host:port (UDP)")
    ap.add_argument("--yks", help="YKS adresi host:port (UDP)")
    ap.add_argument("--serial", help="SiK telsiz seri portu (saha)")
    ap.add_argument("--baud", type=int, default=57600)
    ap.add_argument("--heartbeat-sure", type=float, default=0.0,
                    help="rota sonrası İHA heartbeat yayını süresi (sn; 0=kapalı)")
    ap.add_argument("--heartbeat-aralik", type=float, default=1.0,
                    help="heartbeat periyodu (sn)")
    args = ap.parse_args()

    no_route = args.no_route is not None
    road, conf, ref_xy, waypoints = args.road, args.conf, None, None
    if no_route:
        if args.road is not None or args.rota_json or args.ref:
            ap.error("--no-route, --road/--rota-json/--ref ile birlikte kullanılamaz")
    else:
        if args.rota_json:
            try:
                road, conf, ref_xy, waypoints = rota_json_oku(args.rota_json)
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                ap.error(f"rota.json okunamadı/geçersiz: {exc}")
        elif args.ref:
            ref_xy = [float(v) for v in args.ref.split(",")]
        if road is None:
            ap.error("--road, --rota-json veya --no-route gerekli")
        if (args.ika or args.serial) and not args.rota_json:
            ap.error("İKA/broadcast aktarımı için doğrulanmış --rota-json gerekli")
    if args.heartbeat_sure < 0 or args.heartbeat_aralik <= 0:
        ap.error("heartbeat süre/aralığı pozitif olmalı")
    if not (args.serial or args.ika or args.yks):
        ap.error("--serial, --ika veya --yks hedeflerinden biri gerekli")

    if args.serial:
        link = SerialLink(args.serial, args.baud)
        peers = {"broadcast": None}        # telsiz: tek hatta yayın
    else:
        link = UDPLink()
        peers = {}
        if args.ika:
            peers["ika"] = _addr(args.ika)
        if args.yks:
            peers["yks"] = _addr(args.yks)

    sender = IhaSender(link, peers)
    try:
        if no_route:
            print(f"[İHA] ROTA YOK gönderiliyor: {args.no_route}"
                  + (f" · {args.detay}" if args.detay else ""))
            seq, acked = sender.send_no_route(
                args.no_route, args.detay, wait_ack=not args.serial)
        else:
            print(f"[İHA] Açık yol gönderiliyor: road={road} conf={conf} "
                  f"ref={ref_xy} wp={len(waypoints or [])}")
            seq, acked = sender.send_open_route(road, conf, waypoints, ref_xy,
                                                wait_ack=not args.serial)
    except ValueError as exc:
        link.close()
        ap.error(f"protokol mesajı geçersiz: {exc}")
    if args.serial:
        print(f"[İHA] {'NO_ROUTE' if no_route else 'Rota'} gönderildi (seq={seq}) — telsiz yayın")
    elif acked:
        print(f"[İHA] ✓ Onaylandı (seq={seq}) — ACK: {sorted(acked)}")
    else:
        print(f"[İHA] ⚠ ACK alınamadı (seq={seq}) — RF/bağlantı kontrol et")
    if args.heartbeat_sure > 0:
        print(f"[İHA] heartbeat {args.heartbeat_sure:g}s boyunca yayında")
        bitis = time.monotonic() + args.heartbeat_sure
        while time.monotonic() < bitis:
            sender.send_heartbeat()
            time.sleep(args.heartbeat_aralik)
    link.close()


if __name__ == "__main__":
    main()
