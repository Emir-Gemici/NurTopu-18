"""
Uçtan uca GÖREV AKIŞI demosu (Gazebo'suz) — şartname §2.2 akışını GERÇEK comms ile canlandırır.

  İHA mancınıkla fırlatılır → otonom uçar → HTAB'de açık yolu TESPİT eder
  → comms (UDP loopback) ile YKS + İKA'ya GÖNDERİR → YKS hakem onaylar
  → İKA gelen veriyle rotasını PLANLAR (arena) → HB'ye gider.

Tek kaynak: arena.py. İHA'nın gönderdiği yol == İKA'nın planladığı yol == dünyadaki açık şerit.

Çalıştır:  python3 scripts/mission_demo.py --scenario kolay
"""
import argparse
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "comms"))
import arena
from link import UDPLink
from iha_sender import IhaSender
from ika_receiver import IkaReceiver
from protocol import encode, ack, FrameReader


def _yks_acker(link, stop, box):
    reader = FrameReader()
    while not stop.is_set():
        d, addr = link.recv()
        for m in reader.feed(d) if d else []:
            if m.get("type") == "OPEN_ROUTE":
                box["latest"] = m
                print(f"   [YKS] 📡 tespit alındı: {m['label'].upper()} ({m['road']}) "
                      f"conf={m['conf']} — HAKEM ONAYI ✓")
                if addr:
                    link.send(encode(ack(m["seq"], "yks", m.get("session"))), addr)


def run(scenario="kolay"):
    truth = arena.open_road(scenario)
    line = "═" * 56
    print(f"\n{line}\n  NAVITAS GÖREV DEMOSU — senaryo: {scenario.upper()}\n{line}")

    # Alıcılar (İKA + YKS) — gerçek UDP soketleri
    ika_link = UDPLink(bind=("127.0.0.1", 5006), timeout=0.1)
    yks_link = UDPLink(bind=("127.0.0.1", 5005), timeout=0.1)
    ika = IkaReceiver(ika_link).start()
    stop = threading.Event()
    yks_box = {"latest": None}
    threading.Thread(target=_yks_acker, args=(yks_link, stop, yks_box), daemon=True).start()

    # 1) İHA fırlatma + otonom uçuş (özet)
    print("\n[1] İHA mancınıkla fırlatıldı → tam otonom uçuş (İHA-UB)...")
    time.sleep(0.6)

    # 2) Tespit (gerçekte YOLOv8-seg; demoda arena ground-truth)
    print(f"[2] İHA HTAB'i taradı → açık yol TESPİT: "
          f"{arena.ROAD_LABEL[truth].upper()} ({truth})  [vision]")

    # 3) Aktarım — İHA havadayken comms ile gönder, ACK bekle
    print("[3] İHA → YKS + İKA aktarımı (comms)...")
    sender = IhaSender(UDPLink(bind=("127.0.0.1", 0), timeout=0.1),
                       peers={"ika": ("127.0.0.1", 5006), "yks": ("127.0.0.1", 5005)})
    seq, acked = sender.send_open_route(truth, conf=0.92)
    print(f"   [İHA] ✓ aktarım onaylandı — ACK: {sorted(acked)}")

    # 4) İKA gelen veriyle rota planlar (şartname: İHA inişini bekler; burada özet)
    time.sleep(0.2)
    assert ika.latest is not None, "İKA veri almadı!"
    road = ika.latest["road"]
    wps = arena.route_waypoints(road)
    print(f"[4] İKA açık yolu ALDI ({arena.ROAD_LABEL[road].upper()}) → "
          f"rota planlandı: {len(wps)} waypoint, HB={arena.hb_yeri(scenario)}")
    for i, (x, y) in enumerate(wps):
        print(f"       wp{i}: ({x:+.1f}, {y:+.1f})")

    stop.set(); ika.stop()
    for l in (ika_link, yks_link):
        l.close()

    # Tutarlılık: İHA gönderdi == İKA aldı == dünya açık şeridi
    ok = (road == truth == ika.latest["road"] == yks_box["latest"]["road"])
    print(f"\n{line}")
    print(f"  İHA gönderdi={truth}  YKS aldı={yks_box['latest']['road']}  "
          f"İKA izleyecek={road}")
    print(f"  {'✓ UÇTAN UCA AKIŞ TUTARLI — comms görevi sürüyor' if ok else '✗ TUTARSIZ!'}")
    print(line)
    return ok


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Navitas uçtan uca görev demosu")
    ap.add_argument("--scenario", choices=["kolay", "orta", "zor"], default="kolay")
    args = ap.parse_args()
    sys.exit(0 if run(args.scenario) else 1)
