"""Q6: iha_komut_alici ACK'i nereye yollar (hub'a doner mu)?
Q4: hub fan-out ile yanlis tuketici yanlis ACK'i kendi seq'iyle esler mi (IhaSender)?"""
import contextlib
import io
import threading
from _hub_kur import *  # noqa
from iha_komut_alici import IhaKomutAlici
from iha_sender import IhaSender

print("=== Q6: alici 0.0.0.0:P'ye bagli (uretimdeki gibi), hub statik 127.0.0.1:P ===")
al_link = UDPLink(bind=("0.0.0.0", 0), timeout=0.05)
P = al_link.port
mav = T._SahteMav(kaynak_sysid=1)
al = IhaKomutAlici(al_link, mav, target_system=1)
gorulen = []
_orj = al.isle
def _isle(m, adr):
    gorulen.append((m.get("type"), m.get("seq"), adr))
    return _orj(m, adr)
al.isle = _isle
k = Kur(tuketiciler=[(YEREL, P)])
cmd = command("PARACHUTE", "iha", seq=41)
k.yks.send(encode(cmd))
ack_m = None
bitis = time.monotonic() + 4.0
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    while ack_m is None and time.monotonic() < bitis:
        k.tur()
        al.poll()
        for m in k.yks_okuyucu.feed(T._seri_bosalt(k.yks)):
            if m.get("type") == "ACK" and m.get("ref") == 41:
                ack_m = m
print("hub UDP adresi        :", k.hub_adr)
print("alici.isle'nin gordugu:", gorulen, " -> adr == hub_adr:", all(a == k.hub_adr for *_, a in gorulen))
print("YKS seride okudugu ACK:", ack_m)
print("hub.ogrenilen         :", list(k.hub.ogrenilen), "| hedefler (tekil?):", k.hub.hedefler())
print("hub sayac             :", {a: b for a, b in k.hub.sayac.items() if b})
k.kapat()
al_link.close()

print("\n=== Q4: iki IhaSender tuketici (rpi_inference & iha_inis_yayinci ikizi), AYNI seq bekliyor ===")
k = Kur()
A_link = UDPLink(bind=(YEREL, 0), timeout=0.05)
B_link = UDPLink(bind=(YEREL, 0), timeout=0.05)
A = IhaSender(A_link, {"ika": k.hub_adr, "yks": k.hub_adr})   # rpi_inference (OPEN_ROUTE)
B = IhaSender(B_link, {"ika": k.hub_adr, "yks": k.hub_adr})   # iha_inis_yayinci (IHA_LANDED)
mA = open_route(2, 0.9, [[0, 0], [0.5, 1.0]], [0, 0], seq=7)
mB = iha_landed(seq=7)
sonuc = {}
def kos(ad, s, m):
    sonuc[ad] = s._tekrarli_gonder(m, repeat=3, interval=0.6, wait_ack=True)
tA = threading.Thread(target=kos, args=("A(OPEN_ROUTE seq7)", A, mA))
tB = threading.Thread(target=kos, args=("B(IHA_LANDED seq7)", B, mB))
tA.start(); tB.start()
# YKS: seride ilk cerceveyi gorunce TEK ACK seti gonderir: YKS-tarzi (ref_tip YOK) + IKA-tarzi (ref_tip=IHA_LANDED)
gonderildi = False
seride = []
bitis = time.monotonic() + 3.0
while time.monotonic() < bitis and (tA.is_alive() or tB.is_alive()):
    k.tur()
    for m in k.yks_okuyucu.feed(T._seri_bosalt(k.yks)):
        seride.append((m["type"], m["seq"]))
        if not gonderildi:
            gonderildi = True
            k.yks.send(encode(ack(7, "yks")))                    # yks_gui:1077/1108 tarzi: ref_tip yok
            k.yks.send(encode(ack(7, "ika", "IHA_LANDED")))      # ika_receiver tarzi: ref_tip var
tA.join(3); tB.join(3)
print("seride gorulen (type, seq):", seride)
print("YKS'nin gonderdigi ACK'ler : ack(7,'yks') [ref_tip yok], ack(7,'ika','IHA_LANDED')")
for ad, (seq, acked) in sonuc.items():
    print(f"  {ad}: seq={seq} acked={sorted(acked)}")
print("-> A (OPEN_ROUTE) IHA_LANDED tipli IKA ACK'ini de kabul etti mi:",
      "ika" in sonuc.get("A(OPEN_ROUTE seq7)", (0, set()))[1])
print("hub.ogrenilen:", list(k.hub.ogrenilen))
k.kapat()
A_link.close(); B_link.close()

print("\n=== Q4 kanit: IhaSender eslesme kosulu (iha_sender.py) ===")
import inspect  # noqa: E402
src = inspect.getsource(IhaSender._tekrarli_gonder).splitlines()
for l in src:
    if '"ACK"' in l or "acked.add" in l:
        print("   ", l.strip())
