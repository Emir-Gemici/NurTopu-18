#!/usr/bin/env python3
"""NEDEN: Jetson paketindeki haberlesme dosyalari elle kopyalanirsa depo
uygulamasindan sessizce ayrisabilir. Bu betik saha paketini kanonik codes/comms
kaynaklarindan mekanik olarak yeniler ve kopyalanan her dosyayi raporlar.
"""

from __future__ import annotations

import shutil
from pathlib import Path


KOK = Path(__file__).resolve().parents[1]
PAKET_KOD = KOK / "jetson_paket" / "kod"
KOPYALAR = {
    KOK / "codes" / "karar_sozlesmesi.py": PAKET_KOD / "karar_sozlesmesi.py",
    KOK / "comms" / "protocol.py": PAKET_KOD / "protocol.py",
    KOK / "comms" / "link.py": PAKET_KOD / "link.py",
    KOK / "comms" / "iha_sender.py": PAKET_KOD / "iha_sender.py",
    KOK / "comms" / "inis_kaniti.py": PAKET_KOD / "inis_kaniti.py",
    KOK / "comms" / "iha_inis_yayinci.py": PAKET_KOD / "iha_inis_yayinci.py",
}


def paketi_hazirla():
    """Kanonik saha modullerini Jetson paketine birebir kopyala."""
    PAKET_KOD.mkdir(parents=True, exist_ok=True)
    for kaynak, hedef in KOPYALAR.items():
        if not kaynak.is_file():
            raise FileNotFoundError(f"kanonik paket kaynagi yok: {kaynak}")
        shutil.copy2(kaynak, hedef)
        print(f"[JETSON_PAKET] {kaynak.relative_to(KOK)} -> "
              f"{hedef.relative_to(KOK)}")


def main():
    paketi_hazirla()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
