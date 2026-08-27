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
import threading
import time
from pathlib import Path

from link import UDPLink, SerialLink
from protocol import (open_route, rota_yok, heartbeat, iha_landed, encode,
                      FrameReader)

_KOK = Path(__file__).resolve().parents[1]
if str(_KOK / "codes") not in sys.path:
    sys.path.insert(0, str(_KOK / "codes"))
from karar_sozlesmesi import (rota_guven_reddi, olcek_gecerli_mi,
                              KARAR_YOK_SEBEBI, OLCEK_YOK_SEBEBI,
                              ROTA_GEOMETRI_SEBEBI,
                              IHA_HEARTBEAT_ARALIK_S, YAYIN_REF_XY)

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
            gonderilen_hedefler = []
            for name, peer in targets:
                if name in acked or peer in gonderilen_hedefler:
                    continue
                self.link.send(data, peer)
                gonderilen_hedefler.append(peer)
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
        """Geçerli dinamik rotayı gönder; düşük güvende ACK'li NO_ROUTE gönder.

        CONTRACTS.md §6.3/K-B son savunmasıdır: unutulmuş/yeni bir çağrı yeri
        eşik altı kararı bu katmandan OPEN_ROUTE olarak kaçıramaz.
        """
        guven_reddi = rota_guven_reddi(conf)
        if guven_reddi is not None:
            return self.send_no_route(
                *guven_reddi, repeat=repeat, interval=interval,
                wait_ack=wait_ack)
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

    def send_heartbeat(self, node="iha", **telemetri):
        """Bağlantı-failsafe için tüm alıcılara tek bir canlılık çerçevesi yayınla.

        T162: `x`/`y` (İHA-UB yerel metre) verilirse çerçeveye eklenir; YKS
        şartname §6.2/§6.4 ALAN İHLALİ denetimini o alanlarla yapar. Argümansız
        çağrı ALAN ALAN eskisiyle aynıdır.
        """
        msg = heartbeat(node, **telemetri)
        data = encode(msg)
        gonderilen_hedefler = []
        for _name, peer in (list(self.peers.items()) or [(None, None)]):
            if peer in gonderilen_hedefler:
                continue
            self.link.send(data, peer)
            gonderilen_hedefler.append(peer)
        return msg["seq"]

    def send_iha_landed(self, repeat=8, interval=0.25, wait_ack=True):
        """İHA iniş olayını tüm yapılandırılmış akranlara ACK'li gönder."""
        msg = iha_landed()
        return self._tekrarli_gonder(
            msg, repeat=repeat, interval=interval, wait_ack=wait_ack)


def piksel_rotayi_yerele_cevir(waypoints_px, mpp):
    """Tuval-piksel waypoint'lerini ref=ilk nokta olan YEREL metreye cevir.

    CONTRACTS SS6.5: x saga (+), y ILERIYE (+) — piksel y asagi buyudugu icin
    isaret ters cevrilir (iha_haritala.piksel_to_dunya ile ayni yon kurali).
    Ilk yerel nokta daima [0, 0]; ardisik segmentler MAX_SEGMENT_M'i asarsa
    dogrusal ara nokta eklenir (geometri EKLENMEZ, mevcut kenar bolunur).
    Sonuc `rota_geometrisini_dogrula` ile denetlenir; gecmezse ValueError.
    """
    if not olcek_gecerli_mi(mpp):
        raise ValueError("olcek (mpp) gecersiz; piksel rota metreye cevrilemez")
    if not isinstance(waypoints_px, (list, tuple)) or len(waypoints_px) < 2:
        raise ValueError("en az 2 piksel waypoint gerekli")
    m = float(mpp)
    px0, py0 = float(waypoints_px[0][0]), float(waypoints_px[0][1])
    ham = [((float(px) - px0) * m, (py0 - float(py)) * m)
           for px, py in waypoints_px]
    yerel = [ham[0]]
    for a, b in zip(ham, ham[1:]):
        uzunluk = math.dist(a, b)
        bolum = max(1, int(math.ceil(uzunluk / MAX_SEGMENT_M)))
        if bolum > MAX_WAYPOINTS:
            raise ValueError("segment yogunlastirma waypoint tavanini asiyor")
        for k in range(1, bolum + 1):
            t = k / bolum
            yerel.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    yerel = [[round(x, 2), round(y, 2)] for x, y in yerel]
    return rota_geometrisini_dogrula(list(YAYIN_REF_XY), yerel)


class KararYayinci:
    """Uretim algi yolunun (rpi_inference) telsiz halkasi — K1 / SS2.2.3.

    Iki is parcacigi: (a) KARAR — son karar 'latest-wins' yuvasindan alinip
    ACK'li gonderilir (kamera dongusunu bloklamaz); (b) HEARTBEAT —
    IHA_HEARTBEAT_ARALIK_S ile surekli yayin. Guven kapisi BURADA
    COGALTILMAZ: OPEN_ROUTE her zaman IhaSender.send_open_route uzerinden
    gecer, esik alti orada NO_ROUTE'a doner. Fail-closed: karar None ise
    NO_ROUTE(KARAR_YOK); ret sebebi olan karar HICBIR KOSULDA OPEN_ROUTE
    olarak yayinlanmaz.
    """

    # 🔴 SINIF DUZEYI VARSAYILANLAR (T171 · D-320): bu sinif `__new__` ile de
    # kuruluyor (testler) ve eski cagiranlar bu alanlari bilmiyor. Eksik
    # oznitelik `_heartbeat_dongusu` icinde AttributeError'a, o da SESSIZ
    # HEARTBEAT KAYBINA yol aciyordu — dongu her turda patlayip hicbir
    # heartbeat gondermeden sonsuza kadar donuyordu (bir suit kosumu bu
    # yuzden 20 dakika kilitlendi ve kusur boyle yakalandi).
    konum_saglayici = None
    irtifa_saglayici = None

    def __init__(self, sender, heartbeat_aralik=IHA_HEARTBEAT_ARALIK_S,
                 repeat=4, interval=0.25, wait_ack=True, konum_saglayici=None,
                 irtifa_saglayici=None):
        if heartbeat_aralik <= 0:
            raise ValueError("heartbeat araligi pozitif olmali")
        self.sender = sender
        self.heartbeat_aralik = float(heartbeat_aralik)
        self.repeat, self.interval, self.wait_ack = repeat, interval, wait_ack
        # T162: cagrilabilir, `(x, y)` yerel metre ya da None dondurur.
        self.konum_saglayici = konum_saglayici
        # T171: cagrilabilir, irtifa (m) ya da None. Sartname SS5.3.2 tespiti
        # ASGARI 30 m'den ister; hakem ekrani bunu ancak yayinlanirsa gorur.
        self.irtifa_saglayici = irtifa_saglayici
        self._kilit = threading.Lock()
        self._bekleyen = None
        self._yeni = threading.Event()
        self._dur = threading.Event()
        self._karar_thr = threading.Thread(target=self._karar_dongusu,
                                           name="iha-karar", daemon=True)
        self._hb_thr = threading.Thread(target=self._heartbeat_dongusu,
                                        name="iha-heartbeat", daemon=True)
        self.gonderilen = []        # [(tip, sebep|road, seq, acked)] tani icin
        self.hata = []              # yakalanan istisnalar (str)
        self.heartbeat_sayisi = 0

    # ── uretim yolu API'si ────────────────────────────────────────────────
    def start(self):
        self._karar_thr.start()
        self._hb_thr.start()
        return self

    def stop(self, zaman_asimi=5.0):
        """Bekleyen son karari GONDERIP durur (son karar telde kalmaz)."""
        self._dur.set()
        self._yeni.set()
        self._karar_thr.join(zaman_asimi)
        self._hb_thr.join(zaman_asimi)
        return not (self._karar_thr.is_alive() or self._hb_thr.is_alive())

    def karar(self, open_path, conf, waypoints_px, mpp, karar_reddi=None):
        """Kare karari -> yuva. Ret sebebi varsa OPEN_ROUTE ASLA olusmaz."""
        with self._kilit:
            self._bekleyen = (open_path, conf, list(waypoints_px or []),
                              mpp, karar_reddi)
        self._yeni.set()

    # ── ic dongu ──────────────────────────────────────────────────────────
    def _yuvayi_al(self):
        with self._kilit:
            k, self._bekleyen = self._bekleyen, None
        return k

    def _yuva_bos_mu(self):
        with self._kilit:
            return self._bekleyen is None

    def _karar_dongusu(self):
        while True:
            self._yeni.wait()
            self._yeni.clear()
            k = self._yuvayi_al()
            if k is not None:
                self._karari_gonder(*k)
            # Durma kontrolu yuvayi BOSALTMADAN bakar: gonderim sirasinda
            # yazilip stop() ile yakalanan karar bir sonraki turda gider
            # (dalga 2 curutucusu: eski `_yuvayi_al() is None` onu pop edip atiyordu).
            if self._dur.is_set() and self._yuva_bos_mu():
                return

    def _karari_gonder(self, open_path, conf, waypoints_px, mpp, karar_reddi):
        try:
            if karar_reddi is not None:
                seq, acked = self.sender.send_no_route(
                    karar_reddi[0], karar_reddi[1] if len(karar_reddi) > 1 else None,
                    repeat=self.repeat, interval=self.interval,
                    wait_ack=self.wait_ack)
                self.gonderilen.append(("NO_ROUTE", karar_reddi[0], seq, acked))
                return
            if open_path is None:
                seq, acked = self.sender.send_no_route(
                    KARAR_YOK_SEBEBI, "analyze_path yol uretmedi; sessizlik yok.",
                    repeat=self.repeat, interval=self.interval,
                    wait_ack=self.wait_ack)
                self.gonderilen.append(("NO_ROUTE", KARAR_YOK_SEBEBI, seq, acked))
                return
            try:
                yerel = piksel_rotayi_yerele_cevir(waypoints_px, mpp)
            except ValueError as exc:
                sebep = OLCEK_YOK_SEBEBI if not olcek_gecerli_mi(mpp) else ROTA_GEOMETRI_SEBEBI
                seq, acked = self.sender.send_no_route(
                    sebep, f"rota telsiz sozlesmesine cevrilemedi: {exc}",
                    repeat=self.repeat, interval=self.interval,
                    wait_ack=self.wait_ack)
                self.gonderilen.append(("NO_ROUTE", sebep, seq, acked))
                return
            # Guven kapisi send_open_route icindedir (SS6.3/K-B son savunma).
            seq, acked = self.sender.send_open_route(
                int(open_path), conf, yerel, list(YAYIN_REF_XY),
                repeat=self.repeat, interval=self.interval,
                wait_ack=self.wait_ack)
            self.gonderilen.append(("OPEN_ROUTE", int(open_path), seq, acked))
        except Exception as exc:  # telsiz hatasi kamera dongusunu dusurmez
            self.hata.append(f"{type(exc).__name__}: {exc}")

    def _heartbeat_dongusu(self):
        while not self._dur.is_set():
            try:
                # 🔴 ALAN TOPLAMA KENDI TRY'INDE (T171/D-320): burada olusan
                # HERHANGI bir hata heartbeat'i DURDURMAMALI. Once boyle
                # degildi ve eksik bir oznitelik (AttributeError) `send_heartbeat`
                # cagrilmadan disari firliyordu; dongu sonsuza kadar donuyor,
                # TELSIZ SESSIZCE SUSUYORDU. Baglanti-failsafe icin heartbeat
                # HER TURDA denenir; telemetri alanlari YALNIZCA EK bilgidir.
                # T162: alan uretilemezse YAZILMAZ — "bilinmiyor" ile "0,0"
                # ayni sey degildir.
                alanlar = {}
                try:
                    xy = (self.konum_saglayici() if self.konum_saglayici
                          else None)
                    if xy is not None:
                        alanlar["x"] = round(float(xy[0]), 2)
                        alanlar["y"] = round(float(xy[1]), 2)
                except Exception as exc:
                    self.hata.append(f"konum {type(exc).__name__}: {exc}")
                try:
                    irtifa = (self.irtifa_saglayici() if self.irtifa_saglayici
                              else None)
                    if irtifa is not None:
                        alanlar["alt"] = round(float(irtifa), 1)
                except Exception as exc:
                    self.hata.append(f"irtifa {type(exc).__name__}: {exc}")
                self.sender.send_heartbeat(**alanlar)
                self.heartbeat_sayisi += 1
            except Exception as exc:
                self.hata.append(f"heartbeat {type(exc).__name__}: {exc}")
            self._dur.wait(self.heartbeat_aralik)


def yayinci_kur(yks=None, ika=None, seri=None, baud=57600, **kw):
    """--yks-hedef/--ika-hedef/--telsiz-seri'den KararYayinci uret; hicbiri
    yoksa None (davranis bayt-es: telsiz halkasi HIC kurulmaz)."""
    if not (yks or ika or seri):
        return None
    if seri:
        link = SerialLink(seri, baud)
        peers = {"broadcast": None}
        kw.setdefault("wait_ack", False)
    else:
        link = UDPLink()
        peers = {}
        if ika:
            peers["ika"] = _addr(ika)
        if yks:
            peers["yks"] = _addr(yks)
    return KararYayinci(IhaSender(link, peers), **kw)


def _addr(s):
    h, p = s.rsplit(":", 1)
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
    yayin_no_route = ((args.no_route, args.detay) if no_route
                      else rota_guven_reddi(conf))
    try:
        if yayin_no_route is not None:
            print(f"[İHA] ROTA YOK gönderiliyor: {yayin_no_route[0]}"
                  + (f" · {yayin_no_route[1]}" if yayin_no_route[1] else ""))
            seq, acked = sender.send_no_route(
                *yayin_no_route, wait_ack=not args.serial)
        else:
            print(f"[İHA] Açık yol gönderiliyor: road={road} conf={conf} "
                  f"ref={ref_xy} wp={len(waypoints or [])}")
            seq, acked = sender.send_open_route(road, conf, waypoints, ref_xy,
                                                wait_ack=not args.serial)
    except ValueError as exc:
        link.close()
        ap.error(f"protokol mesajı geçersiz: {exc}")
    if args.serial:
        print(f"[İHA] {'NO_ROUTE' if yayin_no_route is not None else 'Rota'} "
              f"gönderildi (seq={seq}) — telsiz yayın")
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
