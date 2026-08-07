#!/usr/bin/env python3
"""NEDEN: İKA artık senaryo adından üretilen sabit arena geometrisini sürmez.
Bu denetleyici İHA ve İKA'yı paralel başlatır; İKA, yalnızca İHA'nın gönderdiği
doğrulanmış dinamik OPEN_ROUTE mesajını alırsa hareket eder. Geçerli rota
gelmezse güvenli duruşta kalır.

Navitas — Ana Simülasyon Kontrolcüsü

Kullanım:
  python3 scripts/navitas_sim.py [kolay|orta|zor] [--speed 1.0] [--iha-only] [--ika-only]
  python3 scripts/navitas_sim.py kolay --speed 3.0   # 3x hızlı
  python3 scripts/navitas_sim.py zor   --iha-only    # sadece İHA
"""

import subprocess
import sys
import threading
import time
import argparse
from pathlib import Path

for _akim in (sys.stdout, sys.stderr):
    try:
        _akim.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

import ika_nav
import iha_flight

COMMS = Path(__file__).resolve().parents[2] / "comms"
if str(COMMS) not in sys.path:
    sys.path.insert(0, str(COMMS))
from iha_sender import IhaSender, _addr as udp_adres  # noqa: E402
from link import UDPLink  # noqa: E402


def check_topics():
    """Gazebo'nun İKA topic'ini bul ve doğrula."""
    print("[sim] Gazebo topic'leri kontrol ediliyor...")
    try:
        r = subprocess.run(
            ["gz", "topic", "-l"],
            capture_output=True, text=True, timeout=5
        )
        topics = r.stdout.splitlines()
        ika_topics = [t for t in topics if "ika" in t.lower()]
        if ika_topics:
            print(f"[sim] İKA topic'leri bulundu: {ika_topics}")
        else:
            print("[sim] UYARI: İKA topic'i bulunamadı. "
                  "Gazebo çalışıyor ve ika modeli yüklü olduğundan emin ol.")
        return bool(ika_topics)
    except Exception as e:
        print(f"[sim] Topic kontrolü başarısız: {e}")
        return False


def wait_for_gazebo(timeout=30):
    """gzserver hazır olana kadar bekle."""
    print("[sim] Gazebo hazır bekleniyor...")
    for i in range(timeout):
        try:
            r = subprocess.run(
                ["gz", "stats"], capture_output=True, text=True, timeout=3
            )
        except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
            print(f"[sim] Gazebo kontrolü yapılamadı: {exc}")
            return False
        if "Sim" in r.stdout or "Real" in r.stdout:
            print(f"[sim] Gazebo hazır! ({i+1}s)")
            return True
        print(f"[sim]   ... bekleniyor ({i+1}/{timeout}s)")
        time.sleep(1)
    print("[sim] HATA: Gazebo zaman aşımı!")
    return False


def _yerel_udp_hedef(bind):
    """Dinleme adresini aynı makinedeki gönderilebilir İKA hedefine dönüştür."""
    host, port = udp_adres(bind)
    if host in ("", "0.0.0.0"):
        host = "127.0.0.1"
    return host, port


def iha_inisini_yayinla(
        peers, heartbeat_until=None, repeat=8, interval=0.25):
    """IHA_LANDED olayını ACK'li yayınla, İKA bitene dek heartbeat sürdür."""
    if not peers:
        return True
    link = UDPLink(bind=("0.0.0.0", 0), timeout=min(0.05, interval))
    sender = IhaSender(link, peers=peers)
    try:
        seq, acked = sender.send_iha_landed(
            repeat=repeat, interval=interval, wait_ack=True)
        beklenen = set(peers)
        aktarim_tam = acked >= beklenen
        if not aktarim_tam:
            print(f"[sim] IHA_LANDED ACK eksik: seq={seq} "
                  f"beklenen={sorted(beklenen)} gelen={sorted(acked)}")
        else:
            print(f"[sim] IHA_LANDED yayınlandı: seq={seq} ACK={sorted(acked)}")
        # YKS gibi ikinci bir akranın ACK'i eksik olsa bile İKA landed latch'ini
        # açmış olabilir. İKA görevi bitene dek heartbeat'i kesmek, sürüşü link
        # timeout'unda sonsuz güvenli-duruşa kilitler. Görev sonucu yine False
        # kalır; yalnız yaşam döngüsü tamamlanana kadar canlılık korunur.
        while heartbeat_until is not None and not heartbeat_until.wait(0.5):
            sender.send_heartbeat("iha")
        return aktarim_tam
    finally:
        link.close()


def iha_ucus_ve_inis_gorevi(speed, landed_peers, heartbeat_until=None):
    """Uçuş başarı sınırından sonra iniş olayını yayınla; erken yayınlama."""
    if not iha_flight.fly(fps=20.0, speed_mult=speed):
        return False
    return iha_inisini_yayinla(
        landed_peers, heartbeat_until=heartbeat_until)


def dinamik_ika_gorevi(bind, timeout):
    """İKA'yı yalnız İHA'nın geçerli dinamik rota mesajıyla sür.

    Alıcı sürüş boyunca açık kalır; bağlantı kesilirse ``ika_nav.navigate``
    hız komutunu sıfırlar. Eski senaryo→arena rotasına geri dönüş yoktur.
    """
    timeout = max(0.0, float(timeout))
    deadline = time.monotonic() + timeout
    alindi = ika_nav.wait_open_route_from_comms(
        bind=bind,
        timeout=timeout,
        keep_receiver=True,
        deadline_monotonic=deadline,
    )
    if alindi is None:
        print("[sim] Geçerli dinamik rota gelmedi — İKA güvenli duruşta")
        return False
    if isinstance(alindi, dict) and alindi.get("type") == "NO_ROUTE":
        print(f"[sim] İHA rota yok bildirdi: {alindi.get('sebep', 'bilinmeyen neden')}")
        return False
    route, receiver = alindi
    try:
        kalan = max(0.0, deadline - time.monotonic())
        if not ika_nav.receiver_surus_izni_bekle(
                receiver, kalan, deadline_monotonic=deadline):
            return False
        return ika_nav.navigate_route(
            route,
            link_ok=lambda: receiver.link_ok,
            rota_gecerli=lambda: ika_nav.receiver_rota_gecerli(receiver),
            rota_korumali_gonder=lambda r, l: (
                ika_nav.receiver_korumali_hiz_gonder(receiver, r, l)
            ),
        )
    finally:
        try:
            ika_nav.send_vel(0, 0)
        finally:
            try:
                receiver.stop()
            finally:
                receiver.link.close()


def main():
    parser = argparse.ArgumentParser(description="Navitas simülasyon kontrolcüsü")
    parser.add_argument("scenario", nargs="?", default="kolay",
                        choices=["kolay", "orta", "zor"],
                        help="Senaryo (varsayılan: kolay)")
    parser.add_argument("--speed", type=float, default=1.0,
                        help="Zaman hızlandırma katsayısı (varsayılan: 1.0)")
    parser.add_argument("--iha-only", action="store_true",
                        help="Sadece İHA uçuşunu çalıştır")
    parser.add_argument("--ika-only", action="store_true",
                        help="Sadece İKA navigasyonunu çalıştır")
    parser.add_argument("--no-wait", action="store_true",
                        help="Gazebo hazırlık beklemesini atla")
    parser.add_argument("--bind", default="0.0.0.0:5006",
                        help="İHA dinamik rota dinleme adresi")
    parser.add_argument("--route-timeout", type=float, default=60.0,
                        help="geçerli dinamik rota için azami bekleme (sn)")
    parser.add_argument("--landed-ika", type=udp_adres,
                        help="harici İKA IHA_LANDED hedefi host:port")
    parser.add_argument("--landed-yks", type=udp_adres,
                        help="YKS IHA_LANDED hedefi host:port")
    args = parser.parse_args()
    if args.iha_only and args.ika_only:
        parser.error("--iha-only ve --ika-only aynı anda kullanılamaz")

    print("\n" + "═"*50)
    print("  Navitas TEKNOFEST 2026 — Simülasyon Kontrolcüsü")
    print(f"  Senaryo : {args.scenario}")
    print(f"  Hız     : {args.speed}x")
    print("═"*50 + "\n")

    if not args.no_wait:
        if not wait_for_gazebo():
            print("[sim] Gazebo başlatılmamış. Önce launch.sh'ı çalıştır.")
            return 1

    time.sleep(2)  # modellerin yüklenmesi için kısa bekleme
    check_topics()
    time.sleep(1)

    threads = []
    results = {}
    beklenen = []
    thread_hatalari = {}
    ika_bitti = threading.Event()
    landed_peers = {}
    if not args.ika_only:
        if not args.iha_only:
            landed_peers["ika"] = args.landed_ika or _yerel_udp_hedef(args.bind)
        elif args.landed_ika:
            landed_peers["ika"] = args.landed_ika
        if args.landed_yks:
            landed_peers["yks"] = args.landed_yks

    def gorev_kos(ad, islev):
        """Worker istisnasını görünür başarısız sonuca dönüştür."""
        try:
            results[ad] = islev()
        except BaseException as exc:
            results[ad] = False
            thread_hatalari[ad] = exc
            print(f"\n[sim] {ad.upper()} thread hatası: "
                  f"{type(exc).__name__}: {exc}")

    # İHA thread
    if not args.ika_only:
        beklenen.append("iha")
        results["iha"] = False

        def run_iha():
            print("\n[sim] İHA uçuşu başlıyor...")
            gorev_kos(
                "iha", lambda: iha_ucus_ve_inis_gorevi(
                    args.speed,
                    landed_peers,
                    heartbeat_until=(ika_bitti if not args.iha_only else None),
                ))
        t_iha = threading.Thread(target=run_iha, name="iha-flight", daemon=True)
        threads.append(t_iha)

    # İKA thread
    if not args.iha_only:
        beklenen.append("ika")
        results["ika"] = False

        def run_ika():
            print("\n[sim] İKA dinamik rota bekliyor...")
            try:
                gorev_kos(
                    "ika", lambda: dinamik_ika_gorevi(
                        args.bind, args.route_timeout))
            finally:
                ika_bitti.set()
        t_ika = threading.Thread(target=run_ika, name="ika-nav", daemon=True)
        threads.append(t_ika)

    # İKA alıcısını İHA'dan önce bind et; çok yüksek speed katsayısında bile
    # landing yayıncısı ilk paketini boş porta göndermesin.
    baslatma_sirasi = sorted(
        threads, key=lambda t: 0 if t.name == "ika-nav" else 1)
    for t in baslatma_sirasi:
        t.start()

    # Her ikisi de bitene kadar bekle
    kullanici_durdurdu = False
    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        kullanici_durdurdu = True
        ika_bitti.set()
        print("\n[sim] Kullanıcı durdurdu (Ctrl+C)")
        try:
            ika_nav.send_vel(0, 0)
        except Exception as exc:
            print(f"[sim] İKA durdurma komutu gönderilemedi: {exc}")

    # Sonuç raporu
    print("\n" + "═"*50)
    print("  GÖREV SONUCU")
    print("═"*50)
    etiketler = {"iha": "İHA uçuşu ", "ika": "İKA görevi"}
    for ad in beklenen:
        basarili = bool(results.get(ad, False))
        print(f"  {etiketler[ad]}: "
              f"{'✓ TAMAMLANDI' if basarili else '✗ BAŞARISIZ'}")
        if ad in thread_hatalari:
            exc = thread_hatalari[ad]
            print(f"    Hata: {type(exc).__name__}: {exc}")
    print("═"*50)
    tumu_basarili = (
        not kullanici_durdurdu
        and bool(beklenen)
        and all(results.get(ad, False) for ad in beklenen)
    )
    return 0 if tumu_basarili else 1


if __name__ == "__main__":
    # scripts/ klasöründen çalıştır ki import'lar çalışsın
    import os
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    sys.exit(main())
