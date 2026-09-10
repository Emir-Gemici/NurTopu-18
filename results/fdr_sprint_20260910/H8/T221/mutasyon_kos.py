#!/usr/bin/env python3
"""T221 · GERCEK DOSYADA mutasyon: kapi (tests/test_faz_b_arduplane_sablon.py) bozuk depoda DUSUYOR mu?

Testin icindeki mutasyonlar (M1-M11) denetleyici fonksiyonlari kopyada sinar; bu betik ise DEPODAKI
dosyayi bozar, kapiyi alt surecte TAM kosar, sonucu yazar ve dosyayi HER DURUMDA geri koyar (finally,
bayt-es geri yazim + sha256 dogrulamasi). Beklenen: her mutantta cikis != 0 ve beklenen kapi FAIL;
geri yuklemeden sonra kapi OK.

KULLANIM: python -B results/fdr_sprint_20260910/H8/T221/mutasyon_kos.py > .../mutasyon_cikti.txt
"""
import hashlib
import subprocess
import sys
from pathlib import Path

for _akim in (sys.stdout, sys.stderr):
    try:
        _akim.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

KOK = Path(__file__).resolve().parents[4]
PARAM = KOK / "config" / "pixhawk" / "arduplane_final.param"
README = KOK / "config" / "pixhawk" / "README.md"
GOREV = KOK / "config" / "pixhawk" / "arduplane_sitl_prova.waypoints"

# (ad, dosya, eski, yeni, FAIL beklenen testler)
MUTANTLAR = (
    ("G1 TKOFF_THR_MINSPD 0->4 (GPS hiz kapisi)", PARAM,
     "\nTKOFF_THR_MINSPD,0\n", "\nTKOFF_THR_MINSPD,4\n",
     ("test_a5_mancinik_kalkisi_tutarliligi", "test_a14_kaynak_kaniti_temiz_ve_guncel")),
    ("G2 SERVO7 parasut -> 0 (Chute has no channel)", PARAM,
     "\nSERVO7_FUNCTION,27\n", "\nSERVO7_FUNCTION,0\n",
     ("test_a3_servo_fonksiyonlari_ve_cakisma_yok", "test_a4_parasut_tutarliligi")),
    ("G3 README TEYIT listesinden CHUTE_ENABLED silindi", README,
     "- `CHUTE_ENABLED` — 1; arm öncesi", "- CHUTE_ENABLED — 1; arm öncesi",
     ("test_a16_readme_teyit_ve_beyan_listeleri_param_ile_ayni",)),
    ("G4 gorevden DO_PARACHUTE silindi", GOREV,
     "5\t0\t3\t208\t2\t0\t0\t0\t0\t0\t0\t1\n", "",
     ("test_a17_prova_gorevi_yapi_ve_parasut_tutarliligi",)),
)


def kapi():
    r = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests",
                        "-p", "test_faz_b_arduplane_sablon.py"],
                       cwd=KOK, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, r.stdout + r.stderr


def main():
    sonuc = 0
    for ad, dosya, eski, yeni, beklenen in MUTANTLAR:
        asil = dosya.read_bytes()
        ozet = hashlib.sha256(asil).hexdigest()
        # Windows checkout'ta dosya CRLF olabilir (core.autocrlf): desenler LF'le yazildi.
        # Mutant LF'le yazilir (ayristiricilar ikisini de okur); geri yukleme ASIL baytlarla.
        metin = asil.decode("utf-8").replace("\r\n", "\n")
        if metin.count(eski) != 1:
            print(f"[{ad}] UYGULANAMADI (eslesme {metin.count(eski)})")
            sonuc = 1
            continue
        try:
            dosya.write_bytes(metin.replace(eski, yeni).encode("utf-8"))
            kod, cikti = kapi()
        finally:
            dosya.write_bytes(asil)
        geri = hashlib.sha256(dosya.read_bytes()).hexdigest() == ozet
        dusenler = sorted({s.split(" ")[1] for s in cikti.splitlines()
                           if s.startswith(("FAIL: ", "ERROR: "))})
        yakalandi = kod != 0 and all(b in dusenler for b in beklenen)
        print(f"[{ad}] cikis={kod} dusen={dusenler} beklenen={list(beklenen)} "
              f"-> {'YAKALANDI' if yakalandi else 'KACTI'} · geri_yukleme_bayt_es={geri}")
        print("    son satir: " + (cikti.strip().splitlines() or [''])[-1])
        if not (yakalandi and geri):
            sonuc = 1
    kod, cikti = kapi()
    print(f"[geri yukleme sonrasi] cikis={kod} · son satir: {(cikti.strip().splitlines() or [''])[-1]}")
    return sonuc or (1 if kod else 0)


if __name__ == "__main__":
    sys.exit(main())
