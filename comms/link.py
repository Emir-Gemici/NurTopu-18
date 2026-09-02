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


def make_link(kind="udp", **kw):
    """Fabrika: kind='udp' | 'serial'."""
    if kind == "udp":
        return UDPLink(**kw)
    if kind == "serial":
        return SerialLink(**kw)
    raise ValueError(f"bilinmeyen link tipi: {kind}")
