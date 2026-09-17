"""
Navitas haberleşme taşıyıcıları (link katmanı).

İki arka uç, aynı arayüz:
  UDPLink     — geliştirme / simülasyon (loopback veya LAN).
  SerialLink  — saha: SiK Radio V3 433 MHz (transparan seri, MAVLink/UDP BTK uyumlu).

Üst katman (protocol.FrameReader) byte akışını mesajlara çevirir; bu yüzden link
sadece ham byte gönderir/alır. Böylece UDP↔seri geçişi kodu değiştirmez.
"""
import socket


class UDPLink:
    """Dev/sim taşıyıcı: UDP datagram. peer = (host, port)."""

    def __init__(self, bind=("0.0.0.0", 0), peer=None, timeout=0.3, reuse=True):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # NEDEN `reuse` (D-405 · "Hub'in 'portu TEK BASINA acar' garantisi
        # kodda zorlanmiyor"): SO_REUSEADDR ile ikinci bir surec AYNI porta
        # sessizce baglanir ve datagramlarin hepsini ilk soket alir (olculdu:
        # r_cift_bind.py — ikinci soket [] aldi, hata gormedi). Tek sahipli
        # uclar (seri hub) `reuse=False` ile acilir: ikinci bind OSError
        # (EADDRINUSE / WinError 10048) -> gorunur cikis. Windows'ta ayrica
        # SO_EXCLUSIVEADDRUSE kurulur; yoksa SO_REUSEADDR'li bir ikinci soket
        # portu yine calabilir (Windows'a ozgu yari-acik semantik).
        # Varsayilan True: dev/test uclarinin eski davranisi (hizli yeniden
        # acilis, ayni porta cok dinleyici) degismez.
        if reuse:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        elif hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        try:
            self.sock.bind(bind)
        except OSError:
            # bind basarisiz (port dolu: tek sahiplik reddi) -> hata AYNEN
            # yukselir ama olusturulan soket kapatilir; aksi halde cagiran
            # (hub main -> cikis 3) acik bir fd birakir (ResourceWarning).
            self.sock.close()
            raise
        self.sock.settimeout(timeout)
        self.peer = peer

    @property
    def port(self):
        return self.sock.getsockname()[1]

    def send(self, data: bytes, peer=None):
        self.sock.sendto(data, peer or self.peer)

    def recv(self, bufsize=4096):
        """(data, addr) döndürür; zaman aşımında (None, None).

        ConnectionResetError de zaman aşımı gibi yutulur. NEDEN: bağlantısız bir
        UDP soketinde bu hata KARŞI TARAFIN sorunudur — dinlemeyen bir akrana
        gönderim yapılınca Windows bir sonraki `recvfrom`'da WinError 10054
        üretir. Yutulmazsa iki gerçek kusur doğuyordu:
          · YKS dinleyici thread'i tek bir ölü akran yüzünden KALICI ölüyor,
            hakem ekranı donmadan sessizce sağırlaşıyordu;
          · `iha_sender` dinlemeyen bir hedefe gönderimde ham traceback ile
            çöküyor, rota aktarımı yarıda kalıyordu.
        Her ikisi de ölçüldü; kayıt: REVIEW_LOG D-06 ve 2026-08-07 taraması.
        """
        try:
            return self.sock.recvfrom(bufsize)
        except (socket.timeout, ConnectionResetError, ConnectionRefusedError):
            return None, None

    def close(self):
        self.sock.close()


class SerialLink:
    """Saha taşıyıcı: SiK Radio (transparan seri). pyserial gerekir.

    SiK telsiz şeffaf seri köprü gibi davranır: bir uçtan yazdığın byte'lar
    diğer uçtan çıkar. Varsayılan SiK air-rate ile 57600 baud yaygındır.
    """

    def __init__(self, port="/dev/ttyUSB0", baud=57600, timeout=0.3,
                 exclusive=True):
        import serial  # tembel import (dev makinesinde pyserial olmayabilir)
        # P2 (D-388): `serial_for_url` cihaz yolu icin `Serial` ile AYNI sonucu
        # verir (ust kume) — ek olarak `loop://`, `socket://` ve `spy://` acar.
        # Bunsuz bu sinif gercek bir bayt akisiyla HIC sinanamiyordu: saha
        # tasiyicisi yalniz sahte nesneyle "gecmis" sayiliyordu (D-383 §1).
        #
        # NEDEN `exclusive=True` varsayilan (D-405 · "Hub'in 'portu TEK BASINA
        # acar' garantisi kodda zorlanmiyor"): pyserial >= 3.3 POSIX'te
        # flock(LOCK_EX|LOCK_NB) kurar -> ayni /dev/ttyUSB0'i acan IKINCI
        # surec SerialException "Could not exclusively lock port" alir (sessiz
        # bayt calmak yerine gorunur hata; hub main -> cikis 4). Windows zaten
        # tekil acar (win32 yalniz True kabul eder, False ValueError).
        # `loop://` ve `socket://` kwarg'i kabul eder, kilit kurmaz (olculdu,
        # pyserial 3.5 / Py 3.13: her iki URL exclusive=True ile acilip
        # okudu-yazdi; test suitlerinin tum socket:// uclari boyle acilir).
        # Kilit: tests/test_faz_b_seri_hub.py test_14c (kwarg pyserial'e
        # GERCEKTEN gecer). Seri acan HER surec bu siniftan gecer; hepsi tek
        # sahipli olur.
        self.ser = serial.serial_for_url(port, baud, timeout=timeout,
                                         exclusive=exclusive)

    def send(self, data: bytes, peer=None):
        self.ser.write(data)

    def recv(self, bufsize=256):
        # D-403 (olculdu, gercek iki uclu seri kopru): `ser.read(256)` 256 bayt
        # gelene YA DA zaman asimi (0,3 s) dolana dek bloklar; ~70 baytlik ACK
        # icin her bekleme zaman asimina yuvarlaniyordu -> uretim IhaSender
        # ACK turu p50 622,6 ms (iki ucta iki zaman asimi), parasut tekrar
        # araligi 0,20 s'nin UC KATI. D-383'un UDP'de kaldirdigi artefaktin
        # seri ikizi. Simdi: ilk bayta kadar bekle (zaman asimi korunur),
        # sonra birikeni tek seferde bosalt -> ayni koprude 0,8 ms.
        ilk = self.ser.read(1)
        if not ilk:
            return None, None
        bekleyen = getattr(self.ser, "in_waiting", 0) or 0
        if bekleyen:
            ilk += self.ser.read(min(int(bekleyen), max(0, bufsize - 1)))
        return ilk, None

    def close(self):
        self.ser.close()


class CokluLink:
    """ONARIM-09 (2026-09-17): YKS'de LAN (UDP) ve SiK (seri) AYNI ANDA.

    NEDEN: tek taşıyıcı seçilince o hat koptuğunda (Wi-Fi/DHCP değişimi, telsiz
    menzili) hakem ekranı sağırlaşıyor ve komut İHA'ya ulaşmıyordu. İki hat
    birlikte dinlenir, komut ikisinden de gider. Tekrar güvenli: alıcı
    (iha_komut_alici) ``(oturum, seq, cmd)`` ile eylemi bir kez uygular; YKS
    aynı seq'li heartbeat'i düşürür, OPEN_ROUTE tekrarını zaten tekrar gönderim
    gibi işler.

    Arayüz ``UDPLink``/``SerialLink`` ile aynı: ``recv() -> (data, adr)``;
    ``adr is None`` = SiK hattından geldi (seri tamponu korunur).
      send(data, peer)   : peer verilirse YALNIZ UDP (ACK geldiği hatta döner),
                           peer None ise YALNIZ seri.
      send_hepsi(data, peer): komut — iki hat (UDP yalnız peer biliniyorsa).
      hat_yaslari()      : {"lan": s|None, "sik": s|None} son alımdan beri geçen.
    """

    HATLAR = ("lan", "sik")

    def __init__(self, udp, seri, *, saat=None, kuyruk_tavani=4096):
        import queue
        import threading
        import time
        self.udp = udp
        self.seri = seri
        self._saat = saat or time.monotonic
        self._kuyruk = queue.Queue(maxsize=kuyruk_tavani)
        self._kilit = threading.Lock()
        self._son_rx = {"lan": None, "sik": None}
        self.dusen = 0
        self._dur = threading.Event()
        self._okuyucular = [
            threading.Thread(target=self._oku, args=(udp, "lan"), daemon=True,
                             name="coklu-lan"),
            threading.Thread(target=self._oku, args=(seri, "sik"), daemon=True,
                             name="coklu-sik"),
        ]
        for t in self._okuyucular:
            t.start()

    @property
    def port(self):
        return self.udp.port

    @property
    def sock(self):
        return self.udp.sock

    def _oku(self, link, hat):
        import queue
        while not self._dur.is_set():
            try:
                veri, adr = link.recv()
            except Exception:
                if self._dur.is_set():
                    return
                continue
            if not veri:
                continue
            with self._kilit:
                self._son_rx[hat] = self._saat()
            try:
                self._kuyruk.put_nowait((veri, adr if hat == "lan" else None))
            except queue.Full:
                self.dusen += 1

    def recv(self, bufsize=4096):
        import queue
        try:
            return self._kuyruk.get(timeout=0.3)
        except queue.Empty:
            if self._dur.is_set():
                raise OSError("CokluLink kapali")
            return None, None

    def send(self, data: bytes, peer=None):
        if peer is not None:
            self.udp.send(data, peer)
        else:
            self.seri.send(data)

    def send_hepsi(self, data: bytes, peer=None):
        """İki hatta da gönder; en az biri başarılıysa gönderilen hat listesi.
        Hiçbiri gönderemediyse son hatayı yükseltir."""
        giden, son_hata = [], None
        if peer is not None:
            try:
                self.udp.send(data, peer)
                giden.append("lan")
            except OSError as exc:
                son_hata = exc
        try:
            self.seri.send(data)
            giden.append("sik")
        except OSError as exc:
            son_hata = exc
        if not giden:
            raise son_hata if son_hata is not None else OSError("hat yok")
        return giden

    def hat_yaslari(self):
        simdi = self._saat()
        with self._kilit:
            return {h: (None if t is None else simdi - t) for h, t in self._son_rx.items()}

    def close(self):
        self._dur.set()
        for link in (self.udp, self.seri):
            try:
                link.close()
            except Exception:
                pass


def make_link(kind="udp", **kw):
    """Fabrika: kind='udp' | 'serial'."""
    if kind == "udp":
        return UDPLink(**kw)
    if kind == "serial":
        return SerialLink(**kw)
    raise ValueError(f"bilinmeyen link tipi: {kind}")
