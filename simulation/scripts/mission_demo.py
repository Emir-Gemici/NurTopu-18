"""
Uçtan uca GÖREV AKIŞI demosu (Gazebo'suz) — şartname §2.2 akışını GERÇEK comms ile canlandırır.

  İHA mancınıkla fırlatılır → otonom uçar → HTAB'de açık yolu TESPİT eder
  → comms (UDP loopback) ile YKS + İKA'ya GÖNDERİR → YKS hakem onaylar
  → İKA yalnız gelen dinamik A* waypoint dizisini izler → HB'ye gider.

Tek kaynak: iha_haritala'nın doğrulanmış rota.json çıktısı.

Çalıştır:  python3 scripts/mission_demo.py --rota-json recordings/.../rota.json
"""
import argparse
import sys
import threading
import time
from pathlib import Path

# cp1254 konsolda '✓' / '═' UnicodeEncodeError ile betigi dusuruyordu (D-438 §2a
# sinifi); ika_nav.py ile ayni kalip.
for _akim in (sys.stdout, sys.stderr):
    try:
        _akim.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "comms"))
from link import UDPLink
from iha_sender import IhaSender, rota_json_oku
from ika_receiver import IkaReceiver
from protocol import encode, ack, FrameReader, MESAJ_OPEN_ROUTE
from ika_nav import route_to_world_waypoints


def _yks_acker(link, stop, box):
    reader = FrameReader()
    while not stop.is_set():
        d, addr = link.recv()
        for m in reader.feed(d) if d else []:
            if m.get("type") == MESAJ_OPEN_ROUTE:
                box["latest"] = m
                print(f"   [YKS] 📡 tespit alındı: {m['label'].upper()} ({m['road']}) "
                      f"conf={m['conf']} — HAKEM ONAYI ✓")
                if addr:
                    link.send(encode(ack(m["seq"], "yks")), addr)


def run(rota_json):
    road, conf, ref_xy, yerel_wps = rota_json_oku(rota_json)
    line = "═" * 56
    print(f"\n{line}\n  NAVITAS GÖREV DEMOSU — dinamik A* rota\n{line}")

    # Alıcılar (İKA + YKS) — gerçek UDP soketleri, EPHEMERAL port (T209/D-427
    # kalıbı, D-438 §2e). NEDEN: sabit 5005/5006 ÜRETİM YKS/İKA portlarıdır
    # (yalnız CONTRACTS.md'ye ait); demo saha PC'sinde YKS açıkken bunlara bind
    # edince `WinError 10013` ile düşüyordu. Gerçek port `UDPLink.port` ile
    # alınır ve gönderici akran sözlüğüne verilir. Kilit:
    # tests/test_sim_mission_demo_port.py (üretim portları tutuluyorken geçer).
    ika_link = UDPLink(bind=("127.0.0.1", 0), timeout=0.1)
    yks_link = UDPLink(bind=("127.0.0.1", 0), timeout=0.1)
    ika = IkaReceiver(ika_link).start()
    stop = threading.Event()
    yks_box = {"latest": None}
    yks_thread = threading.Thread(target=_yks_acker, args=(yks_link, stop, yks_box), daemon=True)
    yks_thread.start()

    # 1) İHA fırlatma + otonom uçuş (özet)
    print("\n[1] İHA mancınıkla fırlatıldı → tam otonom uçuş (İHA-UB)...")
    time.sleep(0.6)

    # 2) Tespit (iha_haritala çıktısındaki gerçek costmap kararı)
    print(f"[2] İHA HTAB'i taradı → açık yol TESPİT: yol={road}  [costmap A*]")

    # 3) Aktarım — İHA havadayken comms ile gönder, ACK bekle
    print("[3] İHA → YKS + İKA aktarımı (comms)...")
    iha_link = UDPLink(bind=("127.0.0.1", 0), timeout=0.1)
    sender = IhaSender(iha_link,
                       peers={"ika": ("127.0.0.1", ika_link.port),
                              "yks": ("127.0.0.1", yks_link.port)})
    seq, acked = sender.send_open_route(road, conf=conf,
                                        waypoints=yerel_wps, ref_xy=ref_xy)
    print(f"   [İHA] ✓ aktarım onaylandı — ACK: {sorted(acked)}")

    # 4) İKA gelen veriyle rota planlar (şartname: İHA inişini bekler; burada özet)
    time.sleep(0.2)
    assert ika.latest is not None, "İKA veri almadı!"
    road_rx = ika.latest["road"]
    wps = route_to_world_waypoints(ika.latest)
    print(f"[4] İKA açık yolu ALDI (yol {road_rx}) → "
          f"dinamik rota: {len(wps)} waypoint, HB={wps[-1]}")
    for i, (x, y) in enumerate(wps):
        print(f"       wp{i}: ({x:+.1f}, {y:+.1f})")

    stop.set(); ika.stop(); yks_thread.join(timeout=1)
    for l in (ika_link, yks_link, iha_link):
        l.close()

    # Tutarlılık: İHA'nın verdiği koordinatlar == YKS/İKA'nın aldığı koordinatlar
    ok = (road == ika.latest["road"] == yks_box["latest"]["road"]
          and ika.latest["ref_xy"] == ref_xy
          and ika.latest["waypoints"] == [list(p) for p in yerel_wps])
    print(f"\n{line}")
    print(f"  İHA gönderdi={road}  YKS aldı={yks_box['latest']['road']}  "
          f"İKA izleyecek={road_rx}")
    print(f"  {'✓ UÇTAN UCA AKIŞ TUTARLI — comms görevi sürüyor' if ok else '✗ TUTARSIZ!'}")
    print(line)
    return ok


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Navitas uçtan uca görev demosu")
    ap.add_argument("--rota-json", required=True,
                    help="iha_haritala'nin doğrulanmış rota.json çıktısı")
    args = ap.parse_args()
    sys.exit(0 if run(args.rota_json) else 1)
