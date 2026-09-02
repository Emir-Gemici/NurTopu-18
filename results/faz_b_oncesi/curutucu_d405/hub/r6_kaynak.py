"""R6: durdur()/kapat() sonrasi soketler kapaniyor mu? (ResourceWarning avi)
  S1 main() loop:// + durdur -> finally kapat -> gc: uyari var mi?
  S2 ariza yolu (recv OSError -> link.close) + kapat -> gc
  S3 yalniz durdur() (kapat YOK) -> del hub -> gc: soketler acik kalir mi?"""
import contextlib
import gc
import io
import threading
import warnings
from unittest import mock

from ortak import YEREL, hub_modulu_yukle

modul = hub_modulu_yukle(None)
from link import SerialLink, UDPLink  # noqa: E402
from test_p2_seri_hat import SikKoprusu  # noqa: E402


def uyarilar(fn):
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        fn()
        gc.collect()
        gc.collect()
    return [f"{x.category.__name__}: {x.message}" for x in w
            if issubclass(x.category, ResourceWarning)]


def s1():
    orij = modul.SeriHub
    kurulan = {}

    def yakala(*a, **kw):
        hub = orij(*a, **kw)
        kurulan["hub"] = hub
        threading.Timer(0.2, hub.durdur).start()
        return hub
    with mock.patch.object(modul, "SeriHub", side_effect=yakala), \
            contextlib.redirect_stdout(io.StringIO()), \
            contextlib.redirect_stderr(io.StringIO()):
        kod = modul.main(["--port", "loop://", "--bind", f"{YEREL}:0",
                          "--tuketici", f"{YEREL}:5007", "--log-aralik", "0"])
    hub = kurulan["hub"]
    print(f"  S1 main() cikis kodu={kod} udp fileno={hub.udp_link.sock.fileno()} "
          f"seri_link={hub.seri_link}")


def s2():
    k = SikKoprusu()
    hub_seri = SerialLink(f"socket://{YEREL}:{k.port}", 57600, timeout=0.02)
    yks = SerialLink(f"socket://{YEREL}:{k.port}", 57600, timeout=0.02)
    udp = UDPLink(bind=(YEREL, 0), timeout=0.001)
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        hub = modul.SeriHub(hub_seri, udp, [(YEREL, 5007)], log_aralik_s=0)
        hub_seri.recv = mock.Mock(side_effect=OSError("USB koptu"))
        hub.poll()
        acik = hub_seri.ser.is_open
        hub.kapat()
    print(f"  S2 ariza sonrasi hub_seri.ser.is_open={acik} udp fileno={udp.sock.fileno()}")
    yks.close()
    k.kapat()


s3_kalinti = {}


def s3():
    udp = UDPLink(bind=(YEREL, 0), timeout=0.001)
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        hub = modul.SeriHub(None, udp, [(YEREL, 5007)], log_aralik_s=0)
        hub.durdur()
    s3_kalinti["fileno_durdur_sonrasi"] = udp.sock.fileno()
    del hub, udp


for ad, fn in (("S1 main()+durdur (finally kapat)", s1),
               ("S2 ariza yolu + kapat", s2),
               ("S3 yalniz durdur(), kapat YOK", s3)):
    u = uyarilar(fn)
    print(f"R6 {ad}: ResourceWarning {len(u)} adet {u[:3]}")
    if ad.startswith("S3"):
        print(f"  S3 durdur() sonrasi udp fileno={s3_kalinti['fileno_durdur_sonrasi']} "
              f"(-1 degil => durdur() soketi KAPATMAZ; kapat() gerekir)")
