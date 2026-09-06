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
    """Basit alıcı: rota/rota-yok bildirimini ACK'ler (YKS taklidi)."""
    reader = FR()
    box = {"latest": None, "no_route": None}

    def poll():
        d, addr = link.recv()
        for m in reader.feed(d) if d else []:
            if m.get("type") == "OPEN_ROUTE":
                box["latest"] = m
            elif m.get("type") == "NO_ROUTE":
                box["no_route"] = m
            else:
                continue
            if m.get("seq") is not None:
                link.send(encode(ack(m["seq"], node)), addr)
    return poll, box


def main():
    # İKA ve YKS alıcıları — EPHEMERAL port (T209 / D-427). NEDEN: sabit
    # 5005/5006 ÜRETİM YKS/İKA portlarıdır (yalnız CONTRACTS.md'ye ait);
    # loopback burada bunlara bind edince saha PC'sinde YKS açıkken test
    # `WinError 10013` ile KESİN düşüyordu (5 Eylül, üç koşu). Gerçek port
    # aşağıda `getsockname()` ile alınır ve gönderici akran sözlüğüne verilir
    # (iha_link zaten böyle). Kilit: tests/test_p8_sim_katmani.py
    # (5005+5006 tutuluyorken geçer; kaynakta sabit port yok).
    ika_link = UDPLink(bind=("127.0.0.1", 0), timeout=0.1)
    yks_link = UDPLink(bind=("127.0.0.1", 0), timeout=0.1)
    ika_port = ika_link.sock.getsockname()[1]
    yks_port = yks_link.sock.getsockname()[1]

    ika = IkaReceiver(ika_link)
    ika.on_route = lambda m: print(f"  [İKA] aldı: {m['label']} ({m['road']})")
    ika.start()

    yks_poll, yks_box = _make_acker(yks_link, "yks")
    import threading
    stop = threading.Event()

    def yks_loop():
        while not stop.is_set():
            yks_poll()
    yks_thread = threading.Thread(target=yks_loop, daemon=True)
    yks_thread.start()

    # İHA gönderici
    iha_link = UDPLink(bind=("127.0.0.1", 0), timeout=0.1)
    sender = IhaSender(iha_link, peers={
        "ika": ("127.0.0.1", ika_port),
        "yks": ("127.0.0.1", yks_port),
    })

    ref = [-20.0, -24.5]
    # Costmap transport contract: first point is the source anchor and every
    # segment is at most 2.1 m, so the rover cannot skip a distant corner.
    wps = [[0.0, 0.0], [0.3, 1.8], [-0.4, 3.5], [0.4, 5.0]]
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

    sender.send_heartbeat()
    time.sleep(0.2)
    assert ika.link_ok, "HEARTBEAT geldi ama link_ok değil"
    assert olaylar == [], f"heartbeat akarken sahte olay: {olaylar}"
    print("HEARTBEAT akarken: link_ok=True")

    time.sleep(1.3)  # heartbeat kes → timeout aşılsın
    assert not ika.link_ok and olaylar == ["KAYIP"], f"failsafe tetiklenmedi: {olaylar}"
    assert ika.latest is not None, "rota önbelleği kayıpta silinmemeli"
    print("HEARTBEAT kesilince: link_ok=False → GÜVENLİ DURMA tetiklendi, rota önbellekte")

    sender.send_heartbeat()
    time.sleep(0.2)
    assert ika.link_ok and olaylar == ["KAYIP", "GERİ"], f"toparlanma olmadı: {olaylar}"
    print("HEARTBEAT dönünce: link_ok=True → kaldığı waypoint'ten devam")

    # ── NO_ROUTE: sessizlik değil, ACK'li güvenli ret kararı ────────────────
    print("\n=== SONUÇ (ROTA YOK bildirimi) ===")
    onceki_rota = ika.latest
    no_seq, no_acked = sender.send_no_route(
        "KAPALI_DAR", "araç/moloz sonrası gerekli açıklık yok")
    time.sleep(0.2)
    assert no_acked == {"ika", "yks"}, f"NO_ROUTE eksik ACK: {no_acked}"
    assert ika.latest is onceki_rota, "NO_ROUTE son OPEN_ROUTE önbelleğini ezmemeli"
    assert ika.last_no_route and ika.last_no_route["seq"] == no_seq, "İKA NO_ROUTE almadı"
    assert yks_box["no_route"] and yks_box["no_route"]["sebep"] == "KAPALI_DAR", \
        "YKS NO_ROUTE almadı"
    print(f"NO_ROUTE ACK: {sorted(no_acked)} · İKA rota önbelleği korundu · "
          f"sebep={ika.last_no_route['sebep']}")

    stop.set()
    ika.stop()
    # Let the YKS polling loop leave its socket timeout before closing the link.
    # Closing first can race with recv() and emit a spurious OSError traceback.
    yks_thread.join(timeout=1)
    print("\n✓ TEST GEÇTİ — aktarım + NO_ROUTE ACK + bağlantı-kaybı failsafe çalışıyor")

    for l in (ika_link, yks_link, iha_link):
        l.close()


if __name__ == "__main__":
    main()
