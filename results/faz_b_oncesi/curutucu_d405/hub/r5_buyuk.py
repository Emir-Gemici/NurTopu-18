"""R5: (a) UDP soketine cok buyuk datagram (64 KB ve 4097 B): hub ne yapar?
(b) seride sonsuz newline'siz akis: bellek/CPU tavani (FrameReader tavani
hub'da da var mi?)."""
import contextlib
import io
import socket
import time
import tracemalloc

from ortak import YEREL, hub_modulu_yukle

modul = hub_modulu_yukle(None)
from link import SerialLink, UDPLink  # noqa: E402
from protocol import CERCEVE_TAMPON_TAVANI, command, encode  # noqa: E402
from test_p2_seri_hat import SikKoprusu  # noqa: E402


def uc(kopru):
    return SerialLink(f"socket://{YEREL}:{kopru.port}", 57600, timeout=0.02)


log = io.StringIO()
k = SikKoprusu()
hub_seri, yks = uc(k), uc(k)
udp = UDPLink(bind=(YEREL, 0), timeout=modul.UDP_OKUMA_ZAMAN_ASIMI_S)
tuketici = UDPLink(bind=(YEREL, 0), timeout=0.01)
with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
    hub = modul.SeriHub(hub_seri, udp, [(YEREL, tuketici.port)], log_aralik_s=0)
hub_adr = (YEREL, udp.port)
g = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print("R5a — buyuk UDP datagram (hub.udp_link.recv() bufsize=4096 varsayilan)")
for boyut in (4096, 4097, 65000):
    veri = b"A" * boyut
    try:
        g.sendto(veri, hub_adr)
    except OSError as exc:
        print(f"  {boyut} B: GONDERIM hatasi {type(exc).__name__}: {exc}")
        continue
    time.sleep(0.02)
    try:
        with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
            hub.poll()
        print(f"  {boyut} B: poll() sessiz; udp_alinan={hub.sayac['udp_alinan']} "
              f"seri_yazilan={hub.sayac['seri_yazilan']} dusurulen={hub.sayac['dusurulen']}")
    except Exception as exc:
        print(f"  {boyut} B: poll() ISTISNA SIZDIRDI -> {type(exc).__name__}: {exc} "
              f"(calistir() dongusu bunu YAKALAMAZ; hub cikar)")
# hub sonraki turda hala calisiyor mu?
try:
    with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        hub.poll()
    print(f"  sonraki poll(): sessiz; seri_link={'acik' if hub.seri_link else 'KAPALI'}")
except Exception as exc:
    print(f"  sonraki poll(): {type(exc).__name__}: {exc}")

print("R5b — seride newline'siz sonsuz akis (hub._cerceveleri_isle, 1 MiB)")
for parca_boyu in (2, 115):
    with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        hub2 = modul.SeriHub(None, UDPLink(bind=(YEREL, 0), timeout=0.001), [],
                             log_aralik_s=0)
    cop = b"\xff" * parca_boyu
    kalan = 1024 * 1024
    tracemalloc.start()
    t0 = time.perf_counter()
    azami_tampon = 0
    while kalan > 0:
        hub2._cerceveleri_isle(cop[:min(parca_boyu, kalan)])
        kalan -= parca_boyu
        if len(hub2.okuyucu._buf) > azami_tampon:
            azami_tampon = len(hub2.okuyucu._buf)
    sure = time.perf_counter() - t0
    _, tepe = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"  parca={parca_boyu} B: 1 MiB islendi {sure:.2f} s, azami tampon="
          f"{azami_tampon} B (tavan {CERCEVE_TAMPON_TAVANI}), tepe bellek={tepe / 1024:.0f} KiB, "
          f"atilan_bayt={hub2.okuyucu.atilan_bayt} bozuk={hub2.sayac['bozuk']}")
    hub2.kapat()

print("R5c — cop sonrasi gecerli cerceve gecer mi? (hat toparlanir mi)")
mesaj = command("PARACHUTE", "iha", seq=5)
with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
    hub3 = modul.SeriHub(hub_seri if hub.seri_link else None, udp,
                         [(YEREL, tuketici.port)], log_aralik_s=0) if False else hub
yks.send(b"\xff" * 3000)        # newline yok
time.sleep(0.05)
with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
    for _ in range(40):
        hub.poll()
yks.send(encode(mesaj))
gelen = []
bitis = time.monotonic() + 2.0
with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
    while not gelen and time.monotonic() < bitis:
        hub.poll()
        v, _ = tuketici.recv()
        if v:
            gelen.append(v)
print(f"  3000 B cop + gecerli cerceve: tuketiciye {len(gelen)} datagram "
      f"(cop cerceveye yapisik -> ilk gecerli KAYIP beklenir); bozuk={hub.sayac['bozuk']}")
yks.send(encode(mesaj))
gelen = []
bitis = time.monotonic() + 2.0
with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
    while not gelen and time.monotonic() < bitis:
        hub.poll()
        v, _ = tuketici.recv()
        if v:
            gelen.append(v)
print(f"  ikinci gecerli cerceve: tuketiciye {len(gelen)} datagram")
hub.kapat()
tuketici.close()
yks.close()
g.close()
k.kapat()
