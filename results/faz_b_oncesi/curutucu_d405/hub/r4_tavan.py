"""R4: ogrenilen kume 32 tavani — 33. adres gelince EN ESKI dusuyor; uzun
omurlu (ama o an sessiz) tuketici sessizce KOPAR mi? Iki senaryo:
  S1: A bir kez gonderir, sonra 32 efemer kaynak birer datagram -> A duser mi,
      seriden gelen cerceve A'ya ulasir mi?
  S2: A her 1 s'de heartbeat gonderir (rpi_inference kalibi) -> tazelik onu
      korur mu?"""
import contextlib
import io
import time

from ortak import SahteSaat, YEREL, hub_modulu_yukle

modul = hub_modulu_yukle(None)
from link import SerialLink, UDPLink  # noqa: E402
from protocol import command, encode, heartbeat  # noqa: E402
from test_p2_seri_hat import SikKoprusu  # noqa: E402


def uc(kopru):
    return SerialLink(f"socket://{YEREL}:{kopru.port}", 57600, timeout=0.02)


def topla(link, adet, pompa, tavan_s=1.0):
    gelen = []
    bitis = time.monotonic() + tavan_s
    while len(gelen) < adet and time.monotonic() < bitis:
        pompa()
        veri, _ = link.recv()
        if veri:
            gelen.append(veri)
    return gelen


def senaryo(ad, a_tazeler):
    log = io.StringIO()
    saat = SahteSaat(1000.0)
    k = SikKoprusu()
    hub_seri, yks = uc(k), uc(k)
    udp = UDPLink(bind=(YEREL, 0), timeout=modul.UDP_OKUMA_ZAMAN_ASIMI_S)
    statik = UDPLink(bind=(YEREL, 0), timeout=0.01)
    A = UDPLink(bind=(YEREL, 0), timeout=0.01)          # uzun omurlu tuketici
    with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        hub = modul.SeriHub(hub_seri, udp, [(YEREL, statik.port)], saat=saat,
                            log_aralik_s=0)
        hub_adr = (YEREL, udp.port)
        A.send(encode(heartbeat("iha", seq=1)), hub_adr)
        time.sleep(0.02)
        hub.poll()
        a_ogrenildi = (YEREL, A.port) in hub.ogrenilen
        efemerler = []
        for i in range(modul.OGRENILEN_TAVANI):
            e = UDPLink(bind=(YEREL, 0), timeout=0.01)
            efemerler.append(e)
            e.send(encode(heartbeat("sahte", seq=i)), hub_adr)
            saat.t += 0.03
            if a_tazeler and i == modul.OGRENILEN_TAVANI // 2:
                A.send(encode(heartbeat("iha", seq=2)), hub_adr)   # 1 s'lik HB
            time.sleep(0.005)
            hub.poll()
            hub.poll()
        a_hala = (YEREL, A.port) in hub.ogrenilen
        # seriden bir cerceve (YKS ACK gibi) -> fan-out
        mesaj = command("IKA_GO", "ika", seq=9)
        yks.send(encode(mesaj))
        s_gelen = topla(statik, 1, hub.poll)
        a_gelen = topla(A, 1, hub.poll, tavan_s=0.5)
    metin = log.getvalue()
    kirmizi = [s for s in metin.splitlines() if "tavani" in s]
    print(f"R4 {ad}: A ogrenildi={a_ogrenildi} | {modul.OGRENILEN_TAVANI} efemer "
          f"sonra A kumede={a_hala} kume={len(hub.ogrenilen)} | seri cerceve -> "
          f"statik {len(s_gelen)} datagram, A {len(a_gelen)} datagram | "
          f"fanout_gonderim={hub.sayac['fanout_gonderim']}")
    print(f"   ilk tavan logu: {kirmizi[0] if kirmizi else 'YOK'} (toplam {len(kirmizi)})")
    hub.kapat()
    for e in efemerler:
        e.close()
    statik.close()
    A.close()
    yks.close()
    k.kapat()


senaryo("S1 A sessiz (bir kez gonderdi)", a_tazeler=False)
senaryo("S2 A ortada bir kez daha gonderdi (HB)", a_tazeler=True)
