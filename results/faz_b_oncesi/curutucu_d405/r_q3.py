"""Q3: encode(decode(x)) yeniden kodlama sadakati + bozuk/asiri girdi davranisi."""
import json
import traceback
from _hub_kur import *  # noqa

statik = tuketici()
k = Kur(tuketiciler=[(YEREL, statik.port)])

print("=== Q3a: bicim varyantlari (alan sirasi / bosluk / float / unicode / cift anahtar) ===")
varyantlar = [
    ("bosluklu JSON",
     b'{"v": 1, "type": "CMD", "cmd": "PARACHUTE", "hedef": "iha", "seq": 5, "t": 1.5}\n'),
    ("float 1.50 / 1E2 / 5.0",
     b'{"v":1,"type":"OPEN_ROUTE","road":2,"label":"orta","conf":0.910,"ref_xy":[0.0,0.0],"waypoints":[[0,0],[1E2,5.0]],"seq":6,"t":1E2}\n'),
    ("unicode \\u kacisi + ham UTF-8",
     '{"v":1,"type":"NO_ROUTE","sebep":"g\\u00fcven","detay":"şerit","seq":7,"t":1.0}\n'.encode("utf-8")),
    ("alan sirasi farkli",
     b'{"seq":8,"t":2,"hedef":"iha","cmd":"ARM","type":"CMD","v":1}\n'),
    ("cift anahtar seq:8,seq:9",
     b'{"v":1,"type":"CMD","cmd":"PARACHUTE","hedef":"iha","seq":8,"seq":9,"t":1}\n'),
    ("CRLF sonlu",
     b'{"v":1,"type":"CMD","cmd":"DISARM","hedef":"iha","seq":10,"t":1}\r\n'),
]
for ad, ham in varyantlar:
    k.yks.send(ham)
    dg = k.topla(statik, 1)
    if not dg:
        print(f"[{ad}] DATAGRAM YOK")
        continue
    cikan = dg[0]
    print(f"[{ad}]\n   giren : {ham!r}\n   cikan : {cikan!r}\n   bayt-es: {cikan == ham} | "
          f"decode-es: {decode(cikan) == decode(ham)} | kanonik(encode(decode(cikan))==cikan): "
          f"{encode(decode(cikan)) == cikan}")

print("\n=== Q3b: protokolde imza/kontrol toplami var mi? ===")
import protocol, inspect  # noqa: E402
src = inspect.getsource(protocol)
print("protocol.py icinde hmac/crc/checksum/imza gecen satir:",
      [l.strip() for l in src.splitlines() if any(w in l.lower() for w in ("hmac", "crc", "checksum", "imza"))])

print("\n=== Q3c: NaN / Infinity / 1e400 -> hub ne yapar? (dogrudan decode ne yapardi) ===")
for ad, ham in [("NaN", b'{"v":1,"type":"OPEN_ROUTE","conf":NaN,"seq":11}\n'),
                ("Infinity", b'{"v":1,"type":"OPEN_ROUTE","conf":Infinity,"seq":12}\n'),
                ("1e400", b'{"v":1,"type":"OPEN_ROUTE","conf":1e400,"seq":13}\n')]:
    onceki = dict(k.hub.sayac)
    k.yks.send(ham)
    dg = k.topla(statik, 1, tavan=0.6)
    print(f"[{ad}] dogrudan decode -> {decode(ham)} | hub datagram: {dg} | "
          f"bozuk {onceki['bozuk']}->{k.hub.sayac['bozuk']}")

print("\n=== Q3d: derin ic ice JSON satiri -> hub.poll ne yapar? ===")
for n in (500, 1000, 1500, 3000):
    try:
        json.loads("[" * n)
        print(f"json.loads('['*{n}): ValueError bekleniyordu?")
    except Exception as e:
        print(f"json.loads('['*{n}) -> {type(e).__name__}")
derin = b"[" * 3000 + b"\n"
k.yks.send(derin)
hata = None
bitis = time.monotonic() + 5.0
while time.monotonic() < bitis and hata is None:
    try:
        k.tur()
    except Exception as e:  # noqa: BLE001
        hata = e
        tb = traceback.format_exc().splitlines()
        break
print("hub.poll istisna:", type(hata).__name__ if hata else None, "|", str(hata)[:90] if hata else "")
if hata:
    print("traceback (son 6 satir):")
    for l in tb[-6:]:
        print("   ", l)
    print("hub.calistir() bu istisnayi yakalar mi? -> yalniz KeyboardInterrupt (seri_hub.py:375-381)")
print("hub sonrasi: seri_link acik mi:", k.hub.seri_link is not None,
      "| okuyucu tamponu bayt:", len(k.hub.okuyucu._buf), "| atilan_bayt:", k.hub.okuyucu.atilan_bayt)

# hub yasadiysa devam eder mi? (yasamiyorsa calistir() coktan cikmisti)
k.yks.send(encode(command("ARM", "iha", seq=99)))
dg = k.topla(statik, 1, tavan=1.0)
print("sonraki gecerli cerceve gecti mi (poll elle surdurulunce):", [decode(d)["seq"] for d in dg])
k.kapat()
statik.close()

print("\n=== Q3e: en uzun mesru OPEN_ROUTE boyutu vs hub UDP recv tamponu (4096) ===")
from iha_sender import MAX_WAYPOINTS  # noqa: E402
wps = [[-59.99 + 0.01 * i, -59.99 + 0.01 * i] for i in range(MAX_WAYPOINTS)]
m = open_route(3, 0.9999, wps, [-59.99, -59.99], seq=2**31)
print("MAX_WAYPOINTS", MAX_WAYPOINTS, "-> encode uzunlugu:", len(encode(m)), "bayt (tavan 4096)")
