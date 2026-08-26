"""surucu logunda N adet 'bitti' gorunene kadar bekle (GPU isleri sirali; yoklama 20 sn)."""
import sys
import time
from pathlib import Path

log = Path(sys.argv[1])
n = int(sys.argv[2])
while True:
    s = log.read_text(encoding="utf-8", errors="replace") if log.is_file() else ""
    if s.count("bitti") >= n or "Traceback" in s or "TUMU BITTI" in s:
        print(s)
        break
    time.sleep(20)
