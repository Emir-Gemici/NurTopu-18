"""K11 / K10 mutasyonlari — scratch kopyada (mut/) kosar; repo DOKUNULMAZ.

Her mutant: dosya yedeklenir, metin degisimi uygulanir (degismezse HATA), secili test
siniflari kosulur, sonuc (FAIL/ERROR sayisi) yazilir, dosya geri alinir.
"""
import re
import subprocess
import sys
from pathlib import Path

MUT = Path(__file__).resolve().parent / "mut"
PY = r"O:\navitas-local-train\venv\Scripts\python.exe"
BETIK = MUT / "jetson_paket" / "jetson_baslat.sh"
KOPRU_BIRIM = MUT / "jetson_paket" / "systemd" / "navitas-kamera-koprusu.service"
RPI_BIRIM = MUT / "jetson_paket" / "systemd" / "navitas-rpi-inference.service"
TEST = MUT / "tests" / "test_faz_b_jetson_baslat.py"

SINIFLAR = ["KameraKoprusuBirimi", "SystemdBirimleri", "JetsonBaslatKurKapiShim",
            "JetsonBaslatKuruUdp"]

MUTANTLAR = [
    ("M1 birimler(): kopru satiri kaldirildi", BETIK,
     '  if [ "$KAMERA_KOPRU" = 1 ]; then echo navitas-kamera-koprusu; fi   # rpi_inference\'tan ONCE\n', ""),
    ("M2 RPI_EK_ARGS --kaynak kaldirildi", BETIK,
     'if [ -n "$KAMERA" ]; then RPI_EK_ARGS="$RPI_EK_ARGS --kaynak $KAMERA"; fi\n', ""),
    ("M3 kopru birimi After= kaldirildi", KOPRU_BIRIM,
     "After=network.target\n", ""),
    ("M4 birimler(): kopru rpi'den SONRA (liste sirasi)", BETIK,
     '  if [ "$KAMERA_KOPRU" = 1 ]; then echo navitas-kamera-koprusu; fi   # rpi_inference\'tan ONCE\n  echo navitas-rpi-inference\n',
     '  echo navitas-rpi-inference\n  if [ "$KAMERA_KOPRU" = 1 ]; then echo navitas-kamera-koprusu; fi\n'),
    ("M5 kapi(): kopru enable+restart kaldirildi", BETIK,
     '  if [ "$KAMERA_KOPRU" = 1 ]; then\n    etkinlestir_ve_yeniden_baslat navitas-kamera-koprusu.service\n  fi\n', ""),
    ("M6 birimleri_kur(): koprusuz kipte kopru disable kaldirildi", BETIK,
     '  if [ "$KAMERA_KOPRU" != 1 ]; then systemctl disable --now navitas-kamera-koprusu.service >/dev/null 2>&1 || true; fi\n', ""),
    ("M7 kapi(): kopru restart'i dogrulamadan SONRAYA alindi (sleep 3 sonrasi)", BETIK,
     '  if [ "$KAMERA_KOPRU" = 1 ]; then\n    etkinlestir_ve_yeniden_baslat navitas-kamera-koprusu.service\n  fi\n  sleep 3\n',
     '  sleep 3\n  if [ "$KAMERA_KOPRU" = 1 ]; then\n    etkinlestir_ve_yeniden_baslat navitas-kamera-koprusu.service\n  fi\n'),
    ("M8 rpi birimi After= icine kopru EKLENDI (tersine mutant: test fark eder mi?)", RPI_BIRIM,
     "After=network.target navitas-cogullayici.service navitas-seri-hub.service\n",
     "After=network.target navitas-cogullayici.service navitas-seri-hub.service navitas-kamera-koprusu.service\n"),
    ("M9 sozlesme_denetle: rpi --kaynak denetimi kaldirildi", BETIK,
     '    k="$(exec_start navitas-rpi-inference)"\n    case " $k " in *" --kaynak $KAMERA "*) ;; *) hata "navitas-rpi-inference: \'--kaynak $KAMERA\' yok — kopru kalkar ama tuketici okumaz" ;; esac\n',
     ""),
]


def kos_testler():
    p = subprocess.run([PY, str(TEST)] + SINIFLAR, cwd=str(MUT), capture_output=True,
                       text=True, encoding="utf-8", errors="replace", timeout=900)
    son = p.stderr.strip().splitlines()
    ozet = [s for s in son if s.startswith(("Ran ", "OK", "FAILED"))]
    dusen = [s for s in son if s.startswith(("FAIL:", "ERROR:"))]
    return p.returncode, ozet, dusen


def main():
    secim = sys.argv[1:]
    print("BASELINE (mut kopyasi, mutantsiz):")
    rc, ozet, dusen = kos_testler()
    print("  rc", rc, ozet, dusen)
    for ad, dosya, eski, yeni in MUTANTLAR:
        if secim and not any(ad.startswith(s) for s in secim):
            continue
        ham = dosya.read_bytes()
        metin = ham.decode("utf-8")
        eol = "\r\n" if "\r\n" in metin else "\n"
        e = eski.replace("\n", eol)
        y = yeni.replace("\n", eol)
        if e not in metin:
            print(f"\n{ad}: HATA — hedef metin bulunamadi ({dosya.name})")
            continue
        try:
            dosya.write_bytes(metin.replace(e, y, 1).encode("utf-8"))
            rc, ozet, dusen = kos_testler()
            print(f"\n{ad}\n  rc {rc} {ozet}")
            for d in dusen:
                print("   ", d)
            if rc == 0:
                print("  >>> MUTANT YASIYOR (hicbir test dusmedi)")
        finally:
            dosya.write_bytes(ham)


if __name__ == "__main__":
    main()
