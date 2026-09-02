"""R1: seri_ac callback SUREKLI exception atarken hub CPU'yu yiyor mu?
Kullanim: r1_cpu.py [mutant_hub.py]"""
import sys
import threading
import time

from ortak import YEREL, hub_modulu_yukle

modul = hub_modulu_yukle(sys.argv[1] if len(sys.argv) > 1 else None)
from link import UDPLink  # noqa: E402
import serial  # noqa: E402

SURE_S = 3.0
sayac = {"seri_ac": 0, "poll": 0}


def patlat():
    sayac["seri_ac"] += 1
    raise serial.SerialException("could not open port /dev/ttyUSB0: No such file")


udp = UDPLink(bind=(YEREL, 0), timeout=modul.UDP_OKUMA_ZAMAN_ASIMI_S)
hub = modul.SeriHub(None, udp, [(YEREL, 5007)], seri_ac=patlat, log_aralik_s=0)
orijinal_poll = hub.poll


def sayan_poll():
    sayac["poll"] += 1
    orijinal_poll()


hub.poll = sayan_poll
thr = threading.Thread(target=hub.calistir, daemon=True)
cpu0 = time.process_time()
t0 = time.perf_counter()
thr.start()
time.sleep(SURE_S)
hub.durdur()
thr.join(timeout=2.0)
cpu = time.process_time() - cpu0
duvar = time.perf_counter() - t0
hub.kapat()
print(f"R1 hub={sys.argv[1] if len(sys.argv) > 1 else 'REPO'} sure={duvar:.2f}s "
      f"cpu={cpu:.3f}s cpu_orani={100 * cpu / duvar:.1f}% poll_tur={sayac['poll']} "
      f"tur_hizi={sayac['poll'] / duvar:.0f}/s seri_ac_cagri={sayac['seri_ac']} "
      f"yeniden_acma_hatasi={hub.sayac['yeniden_acma_hatasi']} "
      f"saat_tipi={type(hub.saat).__name__}")
