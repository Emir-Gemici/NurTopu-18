#!/usr/bin/env python3
"""
Navitas — Ana Simülasyon Kontrolcüsü
İHA ve İKA'yı paralel olarak çalıştırır.

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

import ika_nav
import iha_flight


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
        r = subprocess.run(
            ["gz", "stats"], capture_output=True, text=True, timeout=3
        )
        if "Sim" in r.stdout or "Real" in r.stdout:
            print(f"[sim] Gazebo hazır! ({i+1}s)")
            return True
        print(f"[sim]   ... bekleniyor ({i+1}/{timeout}s)")
        time.sleep(1)
    print("[sim] HATA: Gazebo zaman aşımı!")
    return False


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
    args = parser.parse_args()

    print("\n" + "═"*50)
    print("  Navitas TEKNOFEST 2026 — Simülasyon Kontrolcüsü")
    print(f"  Senaryo : {args.scenario}")
    print(f"  Hız     : {args.speed}x")
    print("═"*50 + "\n")

    if not args.no_wait:
        if not wait_for_gazebo():
            print("[sim] Gazebo başlatılmamış. Önce launch.sh'ı çalıştır.")
            sys.exit(1)

    time.sleep(2)  # modellerin yüklenmesi için kısa bekleme
    check_topics()
    time.sleep(1)

    threads = []
    results = {}

    # İHA thread
    if not args.ika_only:
        def run_iha():
            print("\n[sim] İHA uçuşu başlıyor...")
            results["iha"] = iha_flight.fly(fps=20.0, speed_mult=args.speed)
        t_iha = threading.Thread(target=run_iha, name="iha-flight", daemon=True)
        threads.append(t_iha)

    # İKA thread
    if not args.iha_only:
        def run_ika():
            print("\n[sim] İKA navigasyonu başlıyor...")
            results["ika"] = ika_nav.navigate(args.scenario)
        t_ika = threading.Thread(target=run_ika, name="ika-nav", daemon=True)
        threads.append(t_ika)

    # Paralel başlat
    for t in threads:
        t.start()

    # Her ikisi de bitene kadar bekle
    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        print("\n[sim] Kullanıcı durdurdu (Ctrl+C)")
        ika_nav.send_vel(0, 0)

    # Sonuç raporu
    print("\n" + "═"*50)
    print("  GÖREV SONUCU")
    print("═"*50)
    if "iha" in results:
        print(f"  İHA uçuşu : {'✓ TAMAMLANDI' if results.get('iha') else '✗ BAŞARISIZ'}")
    if "ika" in results:
        print(f"  İKA görevi: {'✓ TAMAMLANDI' if results.get('ika') else '✗ BAŞARISIZ'}")
    print("═"*50)


if __name__ == "__main__":
    # scripts/ klasöründen çalıştır ki import'lar çalışsın
    import os
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main()
