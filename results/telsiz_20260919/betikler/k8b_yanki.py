"""K8b yanki (Jetson): hub'a (127.0.0.1:5100) 5190'dan tek bayt gonderip kendini tuketici olarak ogretir,
sonra sik_rf_olc --rol yanki --tasiyici udp --bind 127.0.0.1:5190 calistirir. Hub servisi DURDURULMAZ (uretim yolu)."""
import os, socket, runpy, sys
os.chdir(os.path.expanduser("~/navitas"))
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(("127.0.0.1", 5190)); s.sendto(b"\x00", ("127.0.0.1", 5100)); s.close()
print("hub'a 5190'dan hazirlik baytı gonderildi", flush=True)
sys.argv = ["scripts/sik_rf_olc.py", "--rol", "yanki", "--tasiyici", "udp", "--bind", "127.0.0.1:5190"]
runpy.run_path("scripts/sik_rf_olc.py", run_name="__main__")
