#!/usr/bin/env python3
"""NEDEN: Saha görevinde IHA_LANDED mesajı ancak Pixhawk iniş kanıtı
doğrulandıktan sonra, İKA/YKS haberleşme protokolünün ACK'li yayın yoluyla
üretilmelidir. Simülasyon pozu ve operatör düğmesi saha kanıtı sayılmaz.

Örnekler:
  python3 iha_inis_yayinci.py --mavlink udp:127.0.0.1:14550 --kanit-timeout 5 --ika 10.0.0.2:5006
  python3 iha_inis_yayinci.py --mavlink /dev/ttyACM0 --kanit-timeout 5 --serial /dev/ttyUSB0
"""

import argparse
import math
import sys
import threading
import time
from pathlib import Path


_BU_DIZIN = Path(__file__).resolve().parent
if str(_BU_DIZIN) not in sys.path:
    sys.path.insert(0, str(_BU_DIZIN))

from iha_sender import IhaSender, _addr as udp_adres  # noqa: E402
from inis_kaniti import mavlink_baglantisi_ac, yerde_mi  # noqa: E402
from link import SerialLink, UDPLink  # noqa: E402

_KOK = _BU_DIZIN.parent
for _aday in (_BU_DIZIN, _KOK / "codes"):
    if str(_aday) not in sys.path:
        sys.path.insert(0, str(_aday))
from karar_sozlesmesi import (  # noqa: E402
    IHA_INIS_HEARTBEAT_ARALIGI_S, IHA_INIS_HEARTBEAT_SURESI_S)


def iha_inisini_yayinla(
        peers, heartbeat_until=None, repeat=8, interval=0.25, *, tasiyici=None,
        heartbeat_suresi=None, heartbeat_araligi=IHA_INIS_HEARTBEAT_ARALIGI_S,
        saat=time.monotonic):
    """IHA_LANDED olayını ACK'li yayınla, görev bitene dek heartbeat sürdür.

    Heartbeat iki koşuldan biri sağlanana dek sürer (K6):
      * ``heartbeat_until`` (Event) set edilene dek — simülasyon İKA bitti der;
      * ``heartbeat_suresi`` saniye dolana dek — saha CLI, sözleşmeden.
    İkisi de None ise heartbeat gönderilmez (eski davranış, yalnız test/araç).
    Alıcıdaki ``link_lost`` ancak heartbeat GERÇEKTEN kesilince oluşur.

    ``tasiyici`` verilirse de bu fonksiyon onun yaşam döngüsünü sahiplenir ve
    çıkışta kapatır. Bu, UDP ve saha SerialLink yolunun aynı kanonik gövdeyi
    kullanmasını sağlar.
    """
    if not peers:
        if tasiyici is not None:
            tasiyici.close()
        return True
    link = tasiyici
    if link is None:
        link = UDPLink(bind=("0.0.0.0", 0), timeout=min(0.05, interval))
    sender = IhaSender(link, peers=peers)
    try:
        seq, acked = sender.send_iha_landed(
            repeat=repeat, interval=interval, wait_ack=True)
        beklenen = set(peers)
        aktarim_tam = acked >= beklenen
        if not aktarim_tam:
            print(f"[İHA] IHA_LANDED ACK eksik: seq={seq} "
                  f"beklenen={sorted(beklenen)} gelen={sorted(acked)}")
        else:
            print(f"[İHA] IHA_LANDED yayınlandı: seq={seq} ACK={sorted(acked)}")
        # İKA landed latch'ini açmış olsa bile ikinci bir akran ACK'i kayıp
        # olabilir. Görev sonucunu False tutarken İKA bitene dek canlılığı
        # kesmemek, alıcının link-timeout ile kilitlenmesini önler.
        hb_deadline = None
        if heartbeat_suresi is not None:
            hb_deadline = saat() + max(0.0, float(heartbeat_suresi))
        if heartbeat_until is None and hb_deadline is None:
            return aktarim_tam
        durdur = (heartbeat_until if heartbeat_until is not None
                  else threading.Event())
        araligi = max(0.0, float(heartbeat_araligi))
        while True:
            if hb_deadline is not None:
                kalan = hb_deadline - saat()
                if kalan <= 0.0:
                    break
                bekle = min(araligi, kalan)
            else:
                bekle = araligi
            if durdur.wait(bekle):
                break
            sender.send_heartbeat("iha")
        return aktarim_tam
    finally:
        link.close()


def _arg_parser():
    parser = argparse.ArgumentParser(
        description="Pixhawk kanıtlı saha IHA_LANDED yayıncısı")
    parser.add_argument(
        "--mavlink", required=True,
        help="Pixhawk MAVLink bağlantısı (ör. udp:127.0.0.1:14550)")
    parser.add_argument(
        "--kanit-timeout", required=True, type=float,
        help="İniş kanıtı için toplam çalışma süresi (saniye)")
    parser.add_argument("--serial", help="SiK telsiz seri portu")
    parser.add_argument("--baud", type=int,
                        help="SiK seri baud değeri (verilmezse link varsayılanı)")
    parser.add_argument("--ika", help="IKA adresi host:port (UDP)")
    parser.add_argument("--yks", help="YKS adresi host:port (UDP)")
    parser.add_argument(
        "--heartbeat-sure", type=float, default=IHA_INIS_HEARTBEAT_SURESI_S,
        help="iniş sonrası heartbeat süresi (sn); İKA sürüşü boyunca link "
             "canlı kalır (K6). Varsayılan şartname §6.2 İKA görev süresi "
             f"({IHA_INIS_HEARTBEAT_SURESI_S:.0f})")
    parser.add_argument(
        "--heartbeat-aralik", type=float, default=IHA_INIS_HEARTBEAT_ARALIGI_S,
        help="heartbeat aralığı (sn); ika_receiver hb_timeout'undan küçük "
             f"olmalı (varsayılan {IHA_INIS_HEARTBEAT_ARALIGI_S})")
    return parser


def _mavlink_kapat(mav):
    kapat = getattr(mav, "close", None)
    if callable(kapat):
        try:
            kapat()
        except (OSError, RuntimeError):
            pass


def main(argv=None):
    parser = _arg_parser()
    args = parser.parse_args(argv)
    if args.serial and (args.ika or args.yks):
        parser.error("--serial ile --ika/--yks birlikte kullanılamaz")
    if not args.serial and not (args.ika or args.yks):
        parser.error("--serial veya --ika/--yks hedeflerinden biri gerekli")
    if args.baud is not None and not args.serial:
        parser.error("--baud yalnız --serial ile kullanılabilir")
    if args.baud is not None and args.baud <= 0:
        parser.error("--baud pozitif olmalı")
    if not math.isfinite(args.kanit_timeout) or args.kanit_timeout <= 0:
        parser.error("--kanit-timeout sonlu ve pozitif olmalı")
    if not math.isfinite(args.heartbeat_sure) or args.heartbeat_sure < 0:
        parser.error("--heartbeat-sure sonlu ve negatif olmayan olmalı")
    if (not math.isfinite(args.heartbeat_aralik)
            or args.heartbeat_aralik <= 0):
        parser.error("--heartbeat-aralik sonlu ve pozitif olmalı")

    peers = None
    if not args.serial:
        try:
            peers = {}
            if args.ika:
                peers["ika"] = udp_adres(args.ika)
            if args.yks:
                peers["yks"] = udp_adres(args.yks)
        except (TypeError, ValueError) as exc:
            print(f"[İHA] HATA: UDP hedefi geçersiz: {exc}", file=sys.stderr)
            return 4

    try:
        mav = mavlink_baglantisi_ac(args.mavlink)
    except (ImportError, ConnectionError) as exc:
        print(f"[İHA] HATA: {exc}", file=sys.stderr)
        return 2

    try:
        try:
            mav.inis_kaniti_deadline_monotonic = (
                time.monotonic() + args.kanit_timeout)
        except (AttributeError, TypeError, ValueError) as exc:
            print(f"[İHA] HATA: MAVLink son tarihi kurulamadı: {exc}",
                  file=sys.stderr)
            return 2
        if not yerde_mi(mav):
            print("[İHA] İniş kanıtı doğrulanmadı; IHA_LANDED yayınlanmadı.",
                  file=sys.stderr)
            return 3

        if args.serial:
            try:
                link = (SerialLink(args.serial, args.baud)
                        if args.baud is not None else SerialLink(args.serial))
            except (ImportError, OSError, ValueError) as exc:
                print(f"[İHA] HATA: SiK hattı açılamadı: {exc}", file=sys.stderr)
                return 4
            peers = {"ika": None}
            basarili = iha_inisini_yayinla(
                peers, tasiyici=link,
                heartbeat_suresi=args.heartbeat_sure,
                heartbeat_araligi=args.heartbeat_aralik)
        else:
            basarili = iha_inisini_yayinla(
                peers,
                heartbeat_suresi=args.heartbeat_sure,
                heartbeat_araligi=args.heartbeat_aralik)
        return 0 if basarili else 5
    finally:
        _mavlink_kapat(mav)


if __name__ == "__main__":
    raise SystemExit(main())
