"""ZİNCİR — GPU boşalınca bir sonraki işi otomatik başlat.

Şu an alt küme kararlılık testi (v9 vs v5c) koşuyor. Bitince GPU'yu bekletmeden
çok sınıflı ön eğitim deneyi (42_cok_sinifli_onegitim.py) başlasın diye bu zincir
kuruldu — kullanıcı başında olmasa da ilerler.

Kullanım:
  venv\\Scripts\\python.exe 43_zincir.py
"""
import subprocess
import sys
import time
from pathlib import Path

PYTHON = Path(sys.executable)
BURASI = Path(__file__).parent
LOG = BURASI / "calisma" / "zincir.log"


def logla(s):
    m = f"{time.strftime('%H:%M:%S')}  {s}"
    print(m, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(m + "\n")


def gpu_mesgul():
    """Kendi süreçlerimiz dışında python koşuyor mu (bu betik hariç)."""
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
             "Where-Object { $_.CommandLine -notlike '*43_zincir*' }).Count"],
            capture_output=True, text=True, timeout=30)
        return int((r.stdout or "0").strip() or 0) > 0
    except Exception:
        return False


def main():
    logla("ZİNCİR başladı — GPU'nun boşalması bekleniyor")
    bos_sayac = 0
    while True:
        if gpu_mesgul():
            bos_sayac = 0
        else:
            bos_sayac += 1
            # üst üste 2 kontrolde boş → gerçekten bitti
            if bos_sayac >= 2:
                break
        time.sleep(60)

    logla("GPU serbest → çok sınıflı ön eğitim deneyi başlatılıyor")
    kod = subprocess.run(
        [str(PYTHON), str(BURASI / "42_cok_sinifli_onegitim.py")],
        cwd=str(BURASI)).returncode
    logla(f"42_cok_sinifli_onegitim bitti (çıkış {kod})")


if __name__ == "__main__":
    main()
