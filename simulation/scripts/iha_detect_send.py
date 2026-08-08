"""
NEDEN: İHA'nın güvenli rota üretemediği kararını da aynı telsiz hattından
iletmek gerekir. Sessizlik, alıcı tarafında bağlantı kaybı ile güvenli ret
kararını ayırt edilemez yapar.

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
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))                       # arena
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "comms"))
import arena
from link import UDPLink, SerialLink
from iha_sender import IhaSender, rota_json_oku


def detect_open_road(scenario=None, road=None):
    """Açık yolu döndür (1/2/3). GERÇEKTE: YOLO ile kameradan tespit.
    DEMO: arena ground-truth — vision modeli buraya bağlanacak."""
    if road:
        return road
    return arena.open_road(scenario or "kolay")


def _addr(s):
    h, p = s.split(":")
    return (h, int(p))


def rota_yok_kararini_oku(path):
    """iha_haritala'nın ``detection.json`` kararını NO_ROUTE'a çevir.

    ``rota_durum`` eski bir artefaktta yoksa da ``road=None`` güvenli ret
    sayılır. Böylece eksik karar alanı, yanlışlıkla eski/varsayılan bir rota
    yayınlamaya dönüşmez.
    """
    with open(path, encoding="utf-8") as f:
        karar = json.load(f)
    if not isinstance(karar, dict):
        raise ValueError("detection.json nesne kökü içermeli")

    durum = str(karar.get("rota_durum") or "").strip().upper()
    if durum == "ACIK" and karar.get("road") in (1, 2, 3):
        return None

    sebep = durum or "DOGRULAMA_BASARISIZ"
    detay = karar.get("rota_sebep")
    if not detay:
        detay = ("detection.json rota_durum alanı yok veya geçerli bir yol "
                 "numarası içermiyor.")
    return sebep, str(detay)


def main():
    ap = argparse.ArgumentParser(description="İHA açık yol tespit + gönderici")
    ap.add_argument("--scenario", choices=["kolay", "orta", "zor"], default="kolay")
    ap.add_argument("--road", type=int, choices=[1, 2, 3], help="tespiti elle ver (test)")
    ap.add_argument("--conf", type=float, default=0.92)
    ap.add_argument("--rota-json", help="iha_haritala'nin dogrulanmis dinamik rota.json cikisi")
    ap.add_argument("--detection-json",
                    help="iha_haritala detection.json karari; kapaliysa NO_ROUTE yayini yapar")
    ap.add_argument("--ika"); ap.add_argument("--yks")
    ap.add_argument("--serial"); ap.add_argument("--baud", type=int, default=57600)
    args = ap.parse_args()

    no_route = None
    if args.detection_json:
        try:
            no_route = rota_yok_kararini_oku(args.detection_json)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            ap.error(f"detection.json okunamadi/gecersiz: {exc}")
        # Başarılı planın rota dosyası aynı seviyededir. Başarısız durumda
        # iha_haritala bu dosyayı özellikle siler; o durumda NO_ROUTE gider.
        if no_route is None and not args.rota_json:
            aday = Path(args.detection_json).with_name("rota.json")
            if aday.is_file():
                args.rota_json = str(aday)
            else:
                no_route = (
                    "DOGRULAMA_BASARISIZ",
                    "detection.json ACIK bildiriyor ancak dogrulanmis rota.json yok.",
                )

    ref_xy = waypoints = None
    if no_route is not None:
        road = conf = None
    elif args.rota_json:
        try:
            road, conf, ref_xy, waypoints = rota_json_oku(args.rota_json)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            # detection.json varsa bir aktarım/artefakt hatası bile telden
            # bildirilir; İKA'nın sessiz timeout'a düşmesine izin verilmez.
            if args.detection_json:
                no_route = ("DOGRULAMA_BASARISIZ",
                            f"rota.json okunamadi/gecersiz: {exc}")
                road = conf = None
            else:
                ap.error(f"rota.json okunamadi/gecersiz: {exc}")
    else:
        road, conf = detect_open_road(args.scenario, args.road), args.conf
        if args.ika or args.serial:
            ap.error("IKA/broadcast aktarimi icin --rota-json ile dinamik A* rota gerekli")
    if no_route is None:
        print(f"[İHA] HTAB tarandı → AÇIK YOL tespiti: {arena.ROAD_LABEL[road].upper()} "
              f"({road})  conf={conf}")
    else:
        print(f"[İHA] HTAB tarandı → ROTA YOK: {no_route[0]} · {no_route[1]}")

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
    if no_route is None:
        seq, acked = sender.send_open_route(road, conf, waypoints, ref_xy,
                                            wait_ack=not args.serial)
    else:
        seq, acked = sender.send_no_route(*no_route, wait_ack=not args.serial)
    if args.serial:
        print(f"[İHA] {'NO_ROUTE' if no_route else 'rota'} telsiz yayını yapıldı (seq={seq})")
    elif acked:
        print(f"[İHA] ✓ aktarım onaylandı (seq={seq}) — ACK: {sorted(acked)}")
    else:
        print(f"[İHA] ⚠ ACK yok (seq={seq})")
    link.close()


if __name__ == "__main__":
    main()
