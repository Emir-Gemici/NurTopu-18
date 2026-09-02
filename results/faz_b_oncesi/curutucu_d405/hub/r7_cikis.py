"""R7: (a) modul SIGTERM/SIGINT icin isleyici kuruyor mu? (b) poll() icinden
beklenmeyen istisna (R5a: >4096 B datagram, Windows) sizarsa main() ne yapar —
kapat() kosar mi, cikis kodu ne olur (systemd Restart=always icin)."""
import contextlib
import io
import signal
import socket
import threading
from unittest import mock

from ortak import YEREL, hub_modulu_yukle

modul = hub_modulu_yukle(None)

print(f"R7a SIGTERM isleyici = {signal.getsignal(signal.SIGTERM)} ; "
      f"SIGINT isleyici = {signal.getsignal(signal.SIGINT).__name__ if callable(signal.getsignal(signal.SIGINT)) else signal.getsignal(signal.SIGINT)}")

# bos port sec
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind((YEREL, 0))
port = s.getsockname()[1]
s.close()

orij = modul.SeriHub
kurulan = {}


def yakala(*a, **kw):
    hub = orij(*a, **kw)
    kurulan["hub"] = hub

    def buyuk_gonder():
        g = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        g.sendto(b"B" * 5000, (YEREL, port))
        g.close()
    threading.Timer(0.3, buyuk_gonder).start()
    threading.Timer(3.0, hub.durdur).start()      # emniyet: asilmazsa dur
    return hub


hata = io.StringIO()
cikti = io.StringIO()
sonuc = "donmedi"
try:
    with mock.patch.object(modul, "SeriHub", side_effect=yakala), \
            contextlib.redirect_stdout(cikti), contextlib.redirect_stderr(hata):
        sonuc = f"main() dondu kod={modul.main(['--port', 'loop://', '--bind', f'{YEREL}:{port}', '--log-aralik', '0'])}"
except BaseException as exc:
    sonuc = f"main() ISTISNA SIZDIRDI: {type(exc).__name__}: {str(exc)[:60]}"
hub = kurulan["hub"]
print(f"R7b 5000 B datagram -> {sonuc}")
print(f"    kapat() kostu mu: udp fileno={hub.udp_link.sock.fileno()} seri_link={hub.seri_link} "
      f"udp_alinan={hub.sayac['udp_alinan']}")
print(f"    son stdout satiri: {cikti.getvalue().strip().splitlines()[-1] if cikti.getvalue().strip() else '-'}")
print(f"    stderr: {hata.getvalue().strip()[-200:] or '-'}")
print("    (ana betik: `raise SystemExit(main())` -> yakalanmayan istisna = cikis kodu 1 + traceback; "
      "systemd Restart=always 2 s sonra yeniden baslatir)")
