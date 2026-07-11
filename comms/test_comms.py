"""
Comms loopback testi — İHA → (YKS + İKA) açık yol aktarımı, localhost UDP üzerinden.
İHA gönderir, İKA ve YKS alır + ACK döner, İHA ACK'leri toplar.

Çalıştır:  python3 test_comms.py
"""
from link import UDPLink
from iha_sender import IhaSender
from ika_receiver import IkaReceiver
from yks_monitor import FrameReader  # noqa (paket içi tutarlılık)
from protocol import encode, ack, FrameReader as FR


def _make_acker(link, node):
    """Basit alıcı: OPEN_ROUTE'a ACK döner, son mesajı saklar (YKS taklidi)."""
    reader = FR()
    box = {"latest": None}

    def poll():
        d, addr = link.recv()
        for m in reader.feed(d) if d else []:
            if m.get("type") == "OPEN_ROUTE":
                box["latest"] = m
                link.send(encode(ack(m["seq"], node)), addr)
    return poll, box


def main():
    # İKA ve YKS alıcıları (sabit portlar, loopback)
    ika_link = UDPLink(bind=("127.0.0.1", 5006), timeout=0.1)
    yks_link = UDPLink(bind=("127.0.0.1", 5005), timeout=0.1)

    ika = IkaReceiver(ika_link)
    ika.on_route = lambda m: print(f"  [İKA] aldı: {m['label']} ({m['road']})")
    ika.start()

    yks_poll, yks_box = _make_acker(yks_link, "yks")
    import threading
    stop = threading.Event()

    def yks_loop():
        while not stop.is_set():
            yks_poll()
    threading.Thread(target=yks_loop, daemon=True).start()

    # İHA gönderici
    iha_link = UDPLink(bind=("127.0.0.1", 0), timeout=0.1)
    sender = IhaSender(iha_link, peers={
        "ika": ("127.0.0.1", 5006),
        "yks": ("127.0.0.1", 5005),
    })

    ref = [-20.0, -24.5]
    wps = [[0.0, 0.0], [1.2, 8.4], [-2.6, 17.1], [0.4, 49.0]]
    print("İHA → açık yol gönderiliyor (road=2 / orta, conf=0.91, "
          f"ref={ref}, {len(wps)} yerel wp)...")
    seq, acked = sender.send_open_route(road=2, conf=0.91,
                                        waypoints=wps, ref_xy=ref)

    import time
    time.sleep(0.2)  # alıcıların işlemesini bekle

    print("\n=== SONUÇ (aktarım) ===")
    print(f"İHA ACK aldı: {sorted(acked)}")
    assert acked == {"ika", "yks"}, f"Eksik ACK: {acked}"
    assert ika.latest and ika.latest["road"] == 2, "İKA açık yolu almadı"
    assert yks_box["latest"] and yks_box["latest"]["road"] == 2, "YKS açık yolu almadı"
    assert ika.latest["ref_xy"] == ref, f"referans noktası bozuk: {ika.latest['ref_xy']}"
    assert ika.latest["waypoints"] == wps, "yerel waypoint listesi bozuk"
    print(f"İKA.latest = {ika.latest['label']} ({ika.latest['road']}) "
          f"ref={ika.latest['ref_xy']} wp={len(ika.latest['waypoints'])}")
    print(f"YKS.latest = {yks_box['latest']['label']} ({yks_box['latest']['road']})")

    # ── Arıza emniyet: HEARTBEAT kesilince İKA güvenli durmaya geçmeli ──
    # NOT: hb_timeout, son mesajdan (OPEN_ROUTE, ~0,3 sn önce) beri geçen
    # süreden BÜYÜK seçilmeli; yoksa daha heartbeat gelmeden sahte KAYIP
    # tetiklenir (zamanlama yarışı). 0,8 sn bu marjı garanti eder.
    print("\n=== SONUÇ (bağlantı-kaybı failsafe) ===")
    ika.hb_timeout = 0.8
    olaylar = []
    ika.on_link_lost = lambda: olaylar.append("KAYIP")
    ika.on_link_back = lambda: olaylar.append("GERİ")

    from protocol import heartbeat
    iha_link.send(encode(heartbeat("iha")), ("127.0.0.1", 5006))
    time.sleep(0.2)
    assert ika.link_ok, "HEARTBEAT geldi ama link_ok değil"
    assert olaylar == [], f"heartbeat akarken sahte olay: {olaylar}"
    print("HEARTBEAT akarken: link_ok=True")

    time.sleep(1.3)  # heartbeat kes → timeout aşılsın
    assert not ika.link_ok and olaylar == ["KAYIP"], f"failsafe tetiklenmedi: {olaylar}"
    assert ika.latest is not None, "rota önbelleği kayıpta silinmemeli"
    print("HEARTBEAT kesilince: link_ok=False → GÜVENLİ DURMA tetiklendi, rota önbellekte")

    iha_link.send(encode(heartbeat("iha")), ("127.0.0.1", 5006))
    time.sleep(0.2)
    assert ika.link_ok and olaylar == ["KAYIP", "GERİ"], f"toparlanma olmadı: {olaylar}"
    print("HEARTBEAT dönünce: link_ok=True → kaldığı waypoint'ten devam")

    stop.set()
    ika.stop()
    print("\n✓ TEST GEÇTİ — aktarım (ref+wp) + ACK + bağlantı-kaybı failsafe çalışıyor")

    for l in (ika_link, yks_link, iha_link):
        l.close()


if __name__ == "__main__":
    main()
