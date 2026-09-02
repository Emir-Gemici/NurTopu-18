"""Q1: newline'siz datagram seride yapisir mi?  Q2: bir datagramda birden cok cerceve."""
from _hub_kur import *  # noqa

print("=== Q1: newline'siz datagram + ardindan gecerli cerceve ===")
k = Kur()
tuk = tuketici()
m1 = command("PARACHUTE", "iha", seq=11)
m2 = command("PARACHUTE", "iha", seq=12)
tuk.send(encode(m1)[:-1], k.hub_adr)      # newline YOK
tuk.send(encode(m2), k.hub_adr)           # newline VAR
ham = k.yks_ham_bekle(n_newline=1)
cerceveler = list(FrameReader().feed(ham))
print("seride cikan ham   :", ham)
print("YKS FrameReader    :", cerceveler)
print("hub sayac          :", {a: b for a, b in k.hub.sayac.items() if b})
print("SONUC Q1:", "IKI CERCEVE DE KAYIP (sessiz)" if not cerceveler else "cerceve okundu")
k.kapat()
tuk.close()

print("\n=== Q2a: UDP->seri, TEK datagramda IKI cerceve ===")
k = Kur()
tuk = tuketici()
m1 = command("ARM", "iha", seq=21)
m2 = heartbeat("iha", seq=22)
tuk.send(encode(m1) + encode(m2), k.hub_adr)
gelen = k.yks_cerceveler(2)
print("YKS okudu:", [(m["type"], m["seq"]) for m in gelen], "| esit:", gelen == [m1, m2])
print("hub sayac:", {a: b for a, b in k.hub.sayac.items() if b})
k.kapat()
tuk.close()

print("\n=== Q2b: seri->UDP, TEK seri parcasinda IKI cerceve -> tuketiciye kac datagram? ===")
statik = tuketici()
k = Kur(tuketiciler=[(YEREL, statik.port)])
m1 = command("IKA_GO", "ika", seq=31)
m2 = ack(31, "yks")
k.yks.send(encode(m1) + encode(m2))
dg = k.topla(statik, 2)
print("datagram sayisi:", len(dg))
for d in dg:
    print("  datagram:", d, "| newline sayisi:", d.count(b"\n"))
print("hub sayac:", {a: b for a, b in k.hub.sayac.items() if b})
k.kapat()
statik.close()

print("\n=== Q2c: iha_komut_alici datagram-basina FrameReader, datagramda IKI CMD ===")
from iha_komut_alici import IhaKomutAlici  # noqa: E402
al_link = UDPLink(bind=(YEREL, 0), timeout=0.05)
al = IhaKomutAlici(al_link, None)         # mav None: aktarim yok, ACK yok ama CMD sayilir
g = UDPLink()
import io, contextlib  # noqa: E402
g.send(encode(command("PARACHUTE", "iha", seq=1)) + encode(command("ARM", "iha", seq=2)),
       (YEREL, al_link.port))
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    sonuc = al.poll()
print("poll donusu:", sonuc, "| sayac:", al.sayac)
al_link.close()
g.close()
