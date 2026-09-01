#!/usr/bin/env python3
"""
Navitas — İKA sürüş test scripti (ROS gerektirmez)
Gazebo'nun native DiffDrivePlugin'ini gz topic üzerinden kullanır.

Kullanım:
  python3 scripts/drive_ika.py ileri     # 3 saniye ileri git
  python3 scripts/drive_ika.py sag       # sağa dön
  python3 scripts/drive_ika.py sol       # sola dön
  python3 scripts/drive_ika.py dur       # dur
  python3 scripts/drive_ika.py demo      # demo rotayı çalıştır
  python3 scripts/drive_ika.py konum     # mevcut konum bilgisi
"""

import subprocess
import sys
import time


WORLD = "navitas_arena"
MODEL = "ika"
TOPIC = f"~/{WORLD}/{MODEL}/vel_cmd"


def _send(right_wheel_spd: float, left_wheel_spd: float, duration: float = 1.0):
    """
    DiffDrivePlugin native mesaj formatı:
      position.x = sağ tekerlek hızı (m/s)
      position.y = sol tekerlek hızı (m/s)
    """
    msg = f"position {{ x: {right_wheel_spd} y: {left_wheel_spd} z: 0 }}"
    proc = subprocess.Popen(
        ["gz", "topic", "-p", TOPIC, "-m", msg],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    time.sleep(duration)
    proc.terminate()


def ileri(hiz=1.5, sure=3.0):
    print(f"[drive] İleri — hız={hiz} m/s, süre={sure}s")
    _send(hiz, hiz, sure)


def geri(hiz=1.5, sure=3.0):
    print(f"[drive] Geri — hız={hiz} m/s, süre={sure}s")
    _send(-hiz, -hiz, sure)


def sag_don(sure=2.0):
    print(f"[drive] Sağa dön — {sure}s")
    _send(1.0, -1.0, sure)


def sol_don(sure=2.0):
    print(f"[drive] Sola dön — {sure}s")
    _send(-1.0, 1.0, sure)


def dur():
    print("[drive] Dur")
    _send(0.0, 0.0, 0.3)


def konum():
    result = subprocess.run(
        ["gz", "model", "-m", MODEL, "-p"],
        capture_output=True, text=True
    )
    print("[drive] İKA konumu:")
    print(result.stdout or result.stderr)


def demo():
    print("[drive] Demo rota başlatılıyor...")
    print("[drive] Adım 1: 3s ileri")
    ileri(1.5, 3.0)
    dur()
    time.sleep(0.5)

    print("[drive] Adım 2: Sola dön")
    sol_don(1.8)
    dur()
    time.sleep(0.5)

    print("[drive] Adım 3: 4s ileri")
    ileri(1.5, 4.0)
    dur()
    time.sleep(0.5)

    print("[drive] Adım 4: Sağa dön")
    sag_don(1.8)
    dur()
    time.sleep(0.5)

    print("[drive] Adım 5: 3s ileri")
    ileri(1.5, 3.0)
    dur()
    print("[drive] Demo tamamlandı.")


KOMUTLAR = {
    "ileri": ileri,
    "geri":  geri,
    "sag":   sag_don,
    "sol":   sol_don,
    "dur":   dur,
    "demo":  demo,
    "konum": konum,
}

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "demo"
    if cmd in ("--help", "-h"):                       # P8/D-392 duman kapisi
        print(__doc__ or "drive_ika — İKA el komutları (sim)")
        print(f"Geçerli komutlar: {', '.join(KOMUTLAR)}")
        sys.exit(0)
    if cmd not in KOMUTLAR:
        print(f"Bilinmeyen komut: {cmd}")
        print(f"Geçerli komutlar: {', '.join(KOMUTLAR)}")
        sys.exit(1)
    KOMUTLAR[cmd]()
