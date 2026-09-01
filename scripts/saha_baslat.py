"""P9d (D-394) — SAHA TEK-KOMUT ACILIS (thazirlik, sartname §6.2).

NEDEN: §6.2 kurulum icin 15 dk verir; 900 s'den tasarruf edilen her 30 s
+1 puandir ve hands-off sonrasi fiziksel mudahale -100'dur. Sahada bayrak
hatirlamaya calismak hem sure yakar hem hata uretir. Bu betik istasyon
basina TEK komuttur: dogru bayraklarla bileseni kaldirir, acilis suresini
olcup yazar.

Kullanim (saha):
  <venv> scripts/saha_baslat.py yks --ika 10.0.0.2:5006
  <venv> scripts/saha_baslat.py yks --serial COM5          # SiK ile
  <venv> scripts/saha_baslat.py ika --yks 10.0.0.1:5005
  <venv> scripts/saha_baslat.py --komutlar                 # karti yazdir
  <venv> scripts/saha_baslat.py --reset                    # tekrar-firlatma yordami

Jetson tarafi bu betikle ACILMAZ — cihazda `jetson_paket/` kilavuzu gecerli
(SAHA_RUNBOOK.md §3'te tek satiri var).
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

# cp1254 konsollarda ⚠ gibi isaretler patlamasin (repo kalibi)
for _akim in (sys.stdout, sys.stderr):
    try:
        _akim.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

KOK = Path(__file__).resolve().parents[1]
VENV = sys.executable

#: Ilk cikti satiri icin bekleme tavani; GUI'ler stdout'a gec yazabilir.
ACILIS_ISARET_TAVANI_S = 30.0

RESET_YORDAMI = """\
TEKRAR FIRLATMA / RESET YORDAMI (sartname §6.2 — sure 15 dk'dan yer)
  1. YKS: R tusu (onay_sifirla) — tespit/onay durumu sifirlanir.
  2. YKS: ARM durumunu kontrol et; gerekiyorsa A ile yeniden ARM.
  3. IKA: ika_nav zaten NO_ROUTE/izin-yok durumunda guvenli durusta bekler;
     surec OLDURULMEZ (bekleme son tarihi §6.2 icinde islemeye devam eder).
  4. Jetson: rpi_inference kosmaya devam eder — yeniden baslatma GEREKMEZ;
     yeni ucusun kararlari ayni hatta akar.
  5. Kronometreler: FIRLATMA damgasi yeni atista yeniden atilir.
  ⚠ Hicbir adimda arac donanimina fiziksel mudahale yoktur (-100 ceza)."""


def komut_uret(kip, ika=None, yks=None, serial=None, baud=None):
    """Istasyon komutunu TEK yerden uret (runbook bu ciktiyi kopyalar)."""
    if kip == "yks":
        komut = [VENV, str(KOK / "comms" / "yks_gui.py")]
        if serial:
            komut += ["--serial", serial]
            if baud:
                komut += ["--baud", str(baud)]
        if ika:
            komut += ["--ika", ika]
        return komut
    if kip == "ika":
        komut = [VENV, str(KOK / "simulation" / "scripts" / "ika_nav.py"),
                 "comms"]
        if yks:
            komut += ["--yks", yks]
        if serial:
            komut += ["--serial", serial]
            if baud:
                komut += ["--baud", str(baud)]
        return komut
    raise ValueError(f"bilinmeyen kip: {kip!r}")


def acilis_olc(komut, cikti=sys.stdout, tavan_s=ACILIS_ISARET_TAVANI_S):
    """Komutu baslat, ilk cikti satirina kadar gecen sureyi olc, akisi aktar."""
    t0 = time.monotonic()
    print(f"[saha_baslat] {' '.join(komut)}", file=cikti, flush=True)
    cocuk = subprocess.Popen(komut, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, text=True,
                             encoding="utf-8", errors="replace")
    ilk = cocuk.stdout.readline()
    gecen = time.monotonic() - t0
    if ilk:
        print(f"[saha_baslat] AÇILIŞ {gecen:.1f} s (ilk işaret: {ilk.strip()!r})",
              file=cikti, flush=True)
    else:
        print(f"[saha_baslat] ⚠ {gecen:.1f} s içinde çıktı işareti yok — "
              "süreç çalışıyor olabilir (GUI sessiz); kronometreyle doğrula",
              file=cikti, flush=True)
    try:
        for satir in cocuk.stdout:
            print(satir, end="", file=cikti, flush=True)
    except KeyboardInterrupt:
        pass
    return cocuk


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("kip", nargs="?", choices=("yks", "ika"))
    ap.add_argument("--ika", help="IKA adresi host:port (yks kipinde)")
    ap.add_argument("--yks", help="YKS adresi host:port (ika kipinde)")
    ap.add_argument("--serial", help="SiK seri portu (orn. COM5, /dev/ttyUSB0)")
    ap.add_argument("--baud", type=int, default=None)
    ap.add_argument("--komutlar", action="store_true",
                    help="thazirlik kartini yazdir ve cik")
    ap.add_argument("--reset", action="store_true",
                    help="tekrar-firlatma yordamini yazdir ve cik")
    args = ap.parse_args(argv)

    if args.reset:
        print(RESET_YORDAMI)
        return 0
    if args.komutlar or not args.kip:
        print("SAHA AÇILIŞ KARTI (thazırlık — istasyon başına TEK komut):")
        print("  YKS :", " ".join(komut_uret("yks", ika="<IKA_IP>:5006")))
        print("  İKA :", " ".join(komut_uret("ika", yks="<YKS_IP>:5005")))
        print("  SiK :", " ".join(komut_uret("yks", serial="COM5", baud=57600)))
        print("  Jetson: bkz. SAHA_RUNBOOK.md §3 (cihazda jetson_paket/)")
        return 0

    komut = komut_uret(args.kip, ika=args.ika, yks=args.yks,
                       serial=args.serial, baud=args.baud)
    cocuk = acilis_olc(komut)
    return cocuk.wait()


if __name__ == "__main__":
    sys.exit(main())
