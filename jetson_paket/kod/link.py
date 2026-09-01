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

    def __init__(self, bind=("0.0.0.0", 0), peer=None, timeout=0.3):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(bind)
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

    def __init__(self, port="/dev/ttyUSB0", baud=57600, timeout=0.3):
        import serial  # tembel import (dev makinesinde pyserial olmayabilir)
        # P2 (D-388): `serial_for_url` cihaz yolu icin `Serial` ile AYNI sonucu
        # verir (ust kume) — ek olarak `loop://`, `socket://` ve `spy://` acar.
        # Bunsuz bu sinif gercek bir bayt akisiyla HIC sinanamiyordu: saha
        # tasiyicisi yalniz sahte nesneyle "gecmis" sayiliyordu (D-383 §1).
        self.ser = serial.serial_for_url(port, baud, timeout=timeout)

    def send(self, data: bytes, peer=None):
        self.ser.write(data)

    def recv(self, bufsize=256):
        data = self.ser.read(bufsize)
        return (data or None), None

    def close(self):
        self.ser.close()


def make_link(kind="udp", **kw):
    """Fabrika: kind='udp' | 'serial'."""
    if kind == "udp":
        return UDPLink(**kw)
    if kind == "serial":
        return SerialLink(**kw)
    raise ValueError(f"bilinmeyen link tipi: {kind}")
