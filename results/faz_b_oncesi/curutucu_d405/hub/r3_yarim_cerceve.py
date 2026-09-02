"""R3: yeniden acma sirasinda FrameReader'daki yarim bayt yeni baglantinin
ilk cercevesine yapisiyor mu? Kullanim: r3_yarim_cerceve.py [mutant_hub.py]"""
import contextlib
import io
import sys
import time
from unittest import mock

from ortak import SahteSaat, YEREL, hub_modulu_yukle

modul = hub_modulu_yukle(sys.argv[1] if len(sys.argv) > 1 else None)
from link import SerialLink, UDPLink  # noqa: E402
from protocol import command, decode, encode  # noqa: E402
from test_p2_seri_hat import SikKoprusu  # noqa: E402


def uc(kopru):
    return SerialLink(f"socket://{YEREL}:{kopru.port}", 57600, timeout=0.02)


def topla(link, adet, pompa, tavan_s=2.0):
    gelen = []
    bitis = time.monotonic() + tavan_s
    while len(gelen) < adet and time.monotonic() < bitis:
        pompa()
        veri, _ = link.recv()
        if veri:
            gelen.append(veri)
    return gelen


log = io.StringIO()
saat = SahteSaat(1000.0)
k1, k2 = SikKoprusu(), SikKoprusu()
hub_seri, yks1 = uc(k1), uc(k1)
yeni, yks2 = uc(k2), uc(k2)
udp = UDPLink(bind=(YEREL, 0), timeout=modul.UDP_OKUMA_ZAMAN_ASIMI_S)
tuketici = UDPLink(bind=(YEREL, 0), timeout=0.01)
seri_ac = mock.Mock(return_value=yeni)
with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
    hub = modul.SeriHub(hub_seri, udp, [(YEREL, tuketici.port)], seri_ac=seri_ac,
                        saat=saat, log_aralik_s=0)

    # 1) YKS yarim cerceve yazar (newline YOK) — RF kopmasi tam ortada
    yks1.send(b'{"v":1,"type":"CMD","cmd":"PARA')
    time.sleep(0.05)
    for _ in range(5):
        hub.poll()
    tampon_once = bytes(hub.okuyucu._buf)

    # 2) ARIZA: okuma OSError
    hub_seri.recv = mock.Mock(side_effect=OSError("USB koptu"))
    hub.poll()
    ariza_sonrasi_seri = hub.seri_link
    # 3) 1 s sonra yeniden acma -> yeni kopru
    saat.t += modul.SERI_YENIDEN_ACMA_ARALIGI_S
    hub.poll()
    tampon_sonra = bytes(hub.okuyucu._buf)
    # 4) yeni hatta ILK gecerli cerceve
    mesaj = command("PARACHUTE", "iha", seq=77)
    yks2.send(encode(mesaj))
    gelen = topla(tuketici, 1, hub.poll)

print(f"R3 hub={sys.argv[1] if len(sys.argv) > 1 else 'REPO'}")
print(f"  yarim tampon (ariza oncesi)      : {tampon_once!r}")
print(f"  ariza sonrasi seri_link          : {ariza_sonrasi_seri}")
print(f"  yeniden acma sonrasi seri_link   : {'yeni' if hub.seri_link is yeni else hub.seri_link}")
print(f"  yeniden acma sonrasi tampon      : {tampon_sonra!r}")
print(f"  yeni hattaki ILK cerceve tuketiciye: {len(gelen)} datagram -> "
      f"{[decode(g) == mesaj for g in gelen]}")
print(f"  sayac bozuk={hub.sayac['bozuk']} seri_cerceve={hub.sayac['seri_cerceve']} "
      f"yeniden_acma={hub.sayac['yeniden_acma']}")
hub.kapat()
tuketici.close()
yks1.close()
yks2.close()
k1.kapat()
k2.kapat()
