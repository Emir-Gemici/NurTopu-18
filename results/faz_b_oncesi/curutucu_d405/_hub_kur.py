"""Ortak kurulum: GERCEK SeriHub + SikKoprusu (socket:// pyserial uclari) + UDPLink."""
import io
import sys
import time
from pathlib import Path

KOK = Path(r"O:\navitas")
for _y in (KOK / "comms", KOK / "codes", KOK / "tests"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

import seri_hub as modul  # noqa: E402
from seri_hub import SeriHub  # noqa: E402
from link import SerialLink, UDPLink  # noqa: E402
from protocol import (FrameReader, encode, decode, open_route, heartbeat,  # noqa: E402
                      command, ack, iha_landed, rota_yok)
from test_p2_seri_hat import SikKoprusu  # noqa: E402
import test_faz_b_seri_hub as T  # noqa: E402

YEREL = "127.0.0.1"


class Kur:
    def __init__(self, tuketiciler=(), **kw):
        self.kopru = SikKoprusu()
        self.hub_seri = T._uc(self.kopru)
        self.yks = T._uc(self.kopru)
        self.udp = UDPLink(bind=(YEREL, 0), timeout=modul.UDP_OKUMA_ZAMAN_ASIMI_S)
        self.log = io.StringIO()
        with T._Yakala(self.log):
            self.hub = SeriHub(self.hub_seri, self.udp, list(tuketiciler),
                               log_aralik_s=0, **kw)
        self.hub_adr = (YEREL, self.udp.port)
        self.yks_okuyucu = FrameReader()

    def tur(self, n=1):
        with T._Yakala(self.log):
            for _ in range(n):
                self.hub.poll()

    def yks_ham_bekle(self, n_newline=1, tavan=3.0):
        toplanan = b""
        bitis = time.monotonic() + tavan
        while toplanan.count(b"\n") < n_newline and time.monotonic() < bitis:
            self.tur()
            toplanan += T._seri_bosalt(self.yks)
        return toplanan

    def yks_cerceveler(self, adet, tavan=3.0):
        gelen = []
        bitis = time.monotonic() + tavan
        while len(gelen) < adet and time.monotonic() < bitis:
            self.tur()
            gelen += list(self.yks_okuyucu.feed(T._seri_bosalt(self.yks)))
        return gelen

    def topla(self, link, adet, tavan=3.0):
        with T._Yakala(self.log):
            return T._datagramlari_topla(link, adet, pompa=self.hub.poll,
                                         tavan_s=tavan)

    def kapat(self):
        try:
            self.hub.kapat()
        finally:
            self.yks.close()
            self.kopru.kapat()


def tuketici(bind_host=YEREL, port=0, timeout=0.01):
    return UDPLink(bind=(bind_host, port), timeout=timeout)
