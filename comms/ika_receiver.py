"""NEDEN: İKA, geçerli rota alsa bile hem YKS operatörünün `IKA_GO` komutu
hem de İHA uçuş yazılımının doğruladığı iniş olayı gelmeden hareket edemez.

İKA tarafı — İHA'dan açık yol verisini alır, ACK döner, en güncel rotayı dışa açar.

İKA navigasyonu (ika_nav) bu sınıfı kullanarak "gelen veriye göre" hareket eder:
    rx = IkaReceiver(UDPLink(bind=("0.0.0.0", 5006)))
    rx.start()                      # arka planda dinler
    ...
    route = rx.latest               # {"road":2,"label":"orta",...} veya None
    if route: plan_path(route["road"])

Kullanım (dev/UDP):
  python3 ika_receiver.py --bind 0.0.0.0:5006
Saha (SiK telsiz):
  python3 ika_receiver.py --serial /dev/ttyUSB0
"""
import argparse
import threading
import time

from link import UDPLink, SerialLink
from protocol import encode, ack, FrameReader


class IkaReceiver:
    def __init__(self, link, node="ika", send_ack=True, hb_timeout=3.0,
                 yks_peer=None):
        self.link = link
        self.node = node
        self.send_ack = send_ack
        # K8 (şartname §2.2.3): hakem "İKA'ya aktarıldı" onayını ekranda KANIT
        # görmeden veremez. UDP'de OPEN_ROUTE ACK'ı yalnız gönderene (İHA)
        # gider; YKS adresi biliniyorsa ACK'ın kopyası YKS'ye de yansıtılır.
        # Seri (SiK) hatta ortam zaten yayındır, yansıtma gerekmez. Adres CLI
        # ile verilmemişse ilk geçerli IKA_GO'nun kaynağından öğrenilir.
        self.yks_addr = yks_peer
        self.hb_timeout = hb_timeout    # sn: bu süre mesaj gelmezse bağlantı KAYIP
        self.reader = FrameReader()
        # RLock: navigasyonun atomik karar+motor korumasında aynı thread'den
        # tanı amaçlı snapshot alınabilsin; alıcı thread'i ise karar güncellemesi
        # tamamlanana kadar motor komutuyla kesin bir sıra paylaşır.
        self._decision_lock = threading.RLock()
        self._decision_generation = 0
        self._decision_monotonic = None
        self._decision_deadline = None
        self._decision_deadline_snapshot = (None, None, 0, None)
        self.latest = None              # son OPEN_ROUTE mesajı (kayıpta KORUNUR)
        self.last_no_route = None       # son NO_ROUTE; latest'i asla ezmez
        self.last_rx = None             # son mesajın (HEARTBEAT dahil) zamanı
        self.link_lost = False
        self.ika_go = False             # YKS manuel intikal izni; görev boyunca latch
        self.iha_landed = False         # İHA üretim iniş kanıtı; görev boyunca latch
        self.ika_go_monotonic = None    # ilk geçerli IKA_GO'nun yerel alınma zamanı
        self.iha_landed_monotonic = None  # ilk geçerli IHA_LANDED alınma zamanı
        self._ika_go_event = threading.Event()
        self._iha_landed_event = threading.Event()
        self._surus_izni_event = threading.Event()
        self._stop = threading.Event()
        self._thr = None
        self.on_route = None            # callback(msg)
        self.on_no_route = None         # callback(msg) — rota yok, güvenli duruş
        self.on_ika_go = None           # callback(msg) — YKS manuel intikal izni
        self.on_iha_landed = None       # callback(msg) — İHA iniş kanıtı
        self.on_link_lost = None        # callback() — navigasyon GÜVENLİ DURMA tetiği
        self.on_link_back = None        # callback() — kaldığı wp'den devam tetiği

    @property
    def link_ok(self):
        """Navigasyon her adımda bunu kontrol eder; False ise araç DURUR."""
        with self._decision_lock:
            return self.last_rx is not None and not self.link_lost

    def decision_snapshot(self):
        """Karar kapısını nesil ve yerel alınma zamanıyla tutarlı döndür."""
        with self._decision_lock:
            return (self.latest, self.last_no_route, self._decision_generation,
                    self._decision_monotonic)

    def run_if_route_valid(self, action, validator=None):
        """Geçerli rota kontrolü ile eylemi karar güncellemesine göre atomikleştir.

        NO_ROUTE durumu kilit altında kurulup ACK ancak kilitli güncellemeden
        sonra gönderildiğinden, bu metodun ``True`` döndürerek yürüttüğü eylem
        kararın öncesinde; ``False`` sonucu ise kararın sonrasında kesin olarak
        sıralanır. ``validator`` rota geometrisi gibi alıcı katmanının bilmediği
        üst-katman koşullarını sınar.
        """
        with self._decision_lock:
            route = self.latest
            if (self.last_rx is None or self.link_lost
                    or not self._surus_izni_gecerli_unlocked(
                        self._decision_deadline)
                    or route is None
                    or self.last_no_route is not None):
                return False
            if validator is not None and not validator(route):
                return False
            action()
            return True

    def wait_ika_go(self, timeout=None):
        """YKS'nin manuel İKA intikal iznini bekle; izin görev boyunca kalıcıdır."""
        if timeout is not None:
            timeout = max(0.0, float(timeout))
        return self._ika_go_event.wait(timeout)

    def wait_iha_landed(self, timeout=None):
        """İHA uçuş yazılımının iniş kanıtını bekle."""
        if timeout is not None:
            timeout = max(0.0, float(timeout))
        return self._iha_landed_event.wait(timeout)

    def wait_surus_izni(self, timeout=None, deadline_monotonic=None):
        """İki latch'i bekle ve ikisinin de ortak deadline içinde geldiğini doğrula."""
        if timeout is not None:
            timeout = max(0.0, float(timeout))
        if deadline_monotonic is not None:
            deadline_monotonic = float(deadline_monotonic)
            kalan = max(0.0, deadline_monotonic - time.monotonic())
            timeout = kalan if timeout is None else min(timeout, kalan)
        if not self._surus_izni_event.wait(timeout):
            return False
        with self._decision_lock:
            return self._surus_izni_gecerli_unlocked(deadline_monotonic)

    def _surus_izni_gecerli_unlocked(self, deadline_monotonic=None):
        """Latch'lerin varlığını ve isteğe bağlı ilk-alınma son tarihini denetle."""
        if not self.ika_go or not self.iha_landed:
            return False
        if deadline_monotonic is None:
            return True
        return (
            self.ika_go_monotonic is not None
            and self.iha_landed_monotonic is not None
            and self.ika_go_monotonic <= deadline_monotonic
            and self.iha_landed_monotonic <= deadline_monotonic
        )

    def _surus_iznini_guncelle_unlocked(self):
        if self.ika_go and self.iha_landed:
            self._surus_izni_event.set()

    def iha_inisini_bildir(self, alindi_monotonic=None):
        """Doğrulanmış İHA iniş latch'ini ve gerekirse link saatini kur."""
        latch_zamani = (time.monotonic() if alindi_monotonic is None
                        else float(alindi_monotonic))
        with self._decision_lock:
            geri_geldi = False
            if alindi_monotonic is not None:
                geri_geldi = self._iha_canliligini_guncelle_unlocked(
                    latch_zamani)
            if not self.iha_landed:
                self.iha_landed = True
                self.iha_landed_monotonic = latch_zamani
            self._iha_landed_event.set()
            self._surus_iznini_guncelle_unlocked()
            return geri_geldi

    def _kontrol_mesaji_ack(self, ref_seq, addr, ref_tip=None):
        """Kontrol olayı ACK hatasının alıcı thread'ini öldürmesini engelle."""
        if not self.send_ack:
            return
        if addr is None and not isinstance(self.link, SerialLink):
            return
        try:
            data = encode(ack(ref_seq, self.node, ref_tip))
            if addr is None:
                self.link.send(data)
            else:
                self.link.send(data, addr)
        except (OSError, TypeError, ValueError):
            pass

    def _rota_ack(self, msg, addr):
        """OPEN_ROUTE/NO_ROUTE ACK'ı gönderene (İHA) + kopyası YKS'ye (K8)."""
        if not self.send_ack or addr is None:
            return
        data = encode(ack(msg["seq"], self.node, msg.get("type")))
        self.link.send(data, addr)
        if self.yks_addr is not None and tuple(self.yks_addr) != tuple(addr):
            try:
                self.link.send(data, self.yks_addr)
            except (OSError, TypeError, ValueError):
                pass                          # yansıtma hatası İHA ACK'ını bozmaz

    def set_decision_deadline(self, deadline_monotonic):
        """Deadline anındaki son kararı, sonraki mesajlardan bağımsız koru."""
        with self._decision_lock:
            self._decision_deadline = float(deadline_monotonic)
            self._capture_deadline_snapshot_unlocked()

    def decision_deadline_snapshot(self):
        """Son deadline-öncesi kararın sabitlenmiş snapshot'ını döndür."""
        with self._decision_lock:
            return self._decision_deadline_snapshot

    def _capture_deadline_snapshot_unlocked(self):
        if (self._decision_deadline is not None
                and self._decision_monotonic is not None
                and self._decision_monotonic <= self._decision_deadline):
            self._decision_deadline_snapshot = (
                self.latest,
                self.last_no_route,
                self._decision_generation,
                self._decision_monotonic,
            )

    def _iha_canliligini_guncelle_unlocked(self, alindi_monotonic):
        """Yalnız doğrulanmış İHA trafiği için link saatini ilerlet."""
        geri_geldi = self.link_lost
        self.last_rx = alindi_monotonic
        self.link_lost = False
        return geri_geldi

    def _link_geri_bildir(self, geri_geldi):
        """Link geri dönüş callback'ini karar kilidi dışında çağır."""
        if geri_geldi and self.on_link_back:
            self.on_link_back()

    def _handle(self, msg, addr):
        alindi_monotonic = time.monotonic()
        tip = msg.get("type")
        if tip == "OPEN_ROUTE":
            with self._decision_lock:
                geri_geldi = self._iha_canliligini_guncelle_unlocked(
                    alindi_monotonic)
                self.latest = msg
                self.last_no_route = None
                self._decision_generation += 1
                self._decision_monotonic = alindi_monotonic
                self._capture_deadline_snapshot_unlocked()
            self._link_geri_bildir(geri_geldi)
            self._rota_ack(msg, addr)
            if self.on_route:
                self.on_route(msg)
        elif tip == "NO_ROUTE":
            # Eski geçerli rota tanı/toparlanma için korunur. NO_ROUTE onu
            # ``None`` yapmaz; çağıran ayrı durumla güvenli duruş kararını görür.
            with self._decision_lock:
                geri_geldi = self._iha_canliligini_guncelle_unlocked(
                    alindi_monotonic)
                self.last_no_route = msg
                self._decision_generation += 1
                self._decision_monotonic = alindi_monotonic
                self._capture_deadline_snapshot_unlocked()
            self._link_geri_bildir(geri_geldi)
            self._rota_ack(msg, addr)
            if self.on_no_route:
                self.on_no_route(msg)
        elif tip == "HEARTBEAT" and msg.get("node") == "iha":
            with self._decision_lock:
                geri_geldi = self._iha_canliligini_guncelle_unlocked(
                    alindi_monotonic)
            self._link_geri_bildir(geri_geldi)
        elif tip == "IHA_LANDED" and msg.get("node") == "iha":
            ref_seq = msg.get("seq")
            if isinstance(ref_seq, bool) or not isinstance(ref_seq, int):
                return
            geri_geldi = self.iha_inisini_bildir(alindi_monotonic)
            self._link_geri_bildir(geri_geldi)
            self._kontrol_mesaji_ack(ref_seq, addr, "IHA_LANDED")
            if self.on_iha_landed:
                self.on_iha_landed(msg)
        elif (tip == "CMD"
              and msg.get("cmd") == "IKA_GO"
              and msg.get("hedef") == "ika"):
            ref_seq = msg.get("seq")
            if isinstance(ref_seq, bool) or not isinstance(ref_seq, int):
                return
            with self._decision_lock:
                if not self.ika_go:
                    self.ika_go = True
                    self.ika_go_monotonic = alindi_monotonic
                self._ika_go_event.set()
                self._surus_iznini_guncelle_unlocked()
                if self.yks_addr is None and addr is not None:
                    self.yks_addr = tuple(addr)   # K8: rota ACK kopyası buraya
            # Mükerrer IKA_GO idempotent: latch zaten kurulu, yalnız ACK tekrarlanır
            self._kontrol_mesaji_ack(ref_seq, addr, "CMD")
            if self.on_ika_go:
                self.on_ika_go(msg)

    def poll(self):
        """Bir kez al-işle (bloklamayan, link timeout'una bağlı)."""
        d, addr = self.link.recv()
        for m in self.reader.feed(d) if d else []:
            self._handle(m, addr)
        kayip = False
        with self._decision_lock:
            if (self.last_rx is not None and not self.link_lost
                    and time.monotonic() - self.last_rx > self.hb_timeout):
                self.link_lost = True   # rota önbelleği (latest) silinmez
                kayip = True
        if kayip and self.on_link_lost:
            self.on_link_lost()

    def _loop(self):
        while not self._stop.is_set():
            self.poll()

    def start(self):
        """Arka planda dinlemeye başla."""
        self._thr = threading.Thread(target=self._loop, daemon=True)
        self._thr.start()
        return self

    def stop(self):
        self._stop.set()
        if self._thr:
            self._thr.join(timeout=1)


def main():
    ap = argparse.ArgumentParser(description="İKA → açık yol alıcı")
    ap.add_argument("--bind", default="0.0.0.0:5006", help="UDP bind host:port")
    ap.add_argument("--serial", help="SiK telsiz seri portu (saha)")
    ap.add_argument("--baud", type=int, default=57600)
    ap.add_argument("--yks", help="YKS adresi host:port — OPEN_ROUTE ACK "
                    "kopyası hakem ekranına yansıtılır (K8, UDP)")
    args = ap.parse_args()

    if args.serial:
        link = SerialLink(args.serial, args.baud)
    else:
        h, p = args.bind.split(":")
        link = UDPLink(bind=(h, int(p)))
        print(f"[İKA] Dinleniyor: {args.bind}")

    yks_peer = None
    if args.yks:
        h, p = args.yks.split(":")
        yks_peer = (h, int(p))
    rx = IkaReceiver(link, yks_peer=yks_peer)
    rx.on_route = lambda m: print(
        f"[İKA] ✓ Açık yol alındı: {m['label'].upper()} ({m['road']}) "
        f"conf={m['conf']} seq={m['seq']} ref={m.get('ref_xy')} "
        f"wp={len(m.get('waypoints') or [])} → rota planlanıyor")
    rx.on_ika_go = lambda m: print(
        f"[İKA] ✓ YKS IKA_GO alındı (seq={m['seq']}) → manuel intikal izni açık")
    rx.on_iha_landed = lambda m: print(
        f"[İKA] ✓ İHA iniş kanıtı alındı (seq={m['seq']}) → iniş kapısı açık")
    rx.on_link_lost = lambda: print(
        f"[İKA] ⚠ BAĞLANTI KAYIP ({rx.hb_timeout:.0f} sn sessizlik) → GÜVENLİ DURMA")
    rx.on_link_back = lambda: print(
        "[İKA] ✓ Bağlantı geri geldi → kaldığı waypoint'ten devam")
    try:
        while True:
            rx.poll()
    except KeyboardInterrupt:
        print("\n[İKA] kapatılıyor")
    finally:
        link.close()


if __name__ == "__main__":
    main()
