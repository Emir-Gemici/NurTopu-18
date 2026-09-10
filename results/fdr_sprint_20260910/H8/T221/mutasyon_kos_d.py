#!/usr/bin/env python3
"""T221-D · GERCEK DOSYADA mutasyon: A18'in yeni kilitleri (README SS6.6 kabul olcutu 1, beklenen-yok
listesi, sitl_yoklama.txt SS6.1 ek taramasi) bozuk depoda DUSUYOR mu?

Her mutant icin:
  1. calisma kopyasi git'in kayitli haliyle BAYT-ES mi: `git cat-file --filters <ref>:<yol>`
     (core.autocrlf=true -> checkout'un urettigi CRLF'in aynisi). Degilse mutant KOSULMAZ.
  2. mutant yazilir (satir sonu dosyanin kendi bicimiyle; yalniz desen degisir),
  3. kapi (tests/test_faz_b_arduplane_sablon.py) alt surecte TAM kosulur,
  4. dosya HER DURUMDA (finally) git'ten alinan baytlarla geri yazilir ve sha256'si ilk haliyle
     karsilastirilir.
Beklenen: her mutantta cikis != 0 ve test_a18 FAIL; geri yuklemeden sonra kapi OK.

REF: varsayilan "index" (git add'lenmis, commit'e girecek hal). Commit sonrasi: --ref HEAD.
KULLANIM: python -B results/fdr_sprint_20260910/H8/T221/mutasyon_kos_d.py [--ref HEAD] \\
              > results/fdr_sprint_20260910/H8/T221/mutasyon_cikti_d.txt
"""
import argparse
import hashlib
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

for _akim in (sys.stdout, sys.stderr):
    try:
        _akim.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

KOK = Path(__file__).resolve().parents[4]
PARAM = "config/pixhawk/arduplane_final.param"
README = "config/pixhawk/README.md"
YOKLAMA = "results/fdr_sprint_20260910/H8/T221/sitl_yoklama.txt"
A18 = "test_a18_sitl_olculemedi_yazili_gecti_yazilmaz"
SHA = "639a8381c1d8805a2e252a679f22d72473232ac813c810216d99aaba55e160e9"

# (ad, dosya, eski, yeni, beklenen eslesme adedi, FAIL beklenen testler)
MUTANTLAR = (
    ("R1 README beklenen-yok listesi bosaltildi", README,
     "listesi = {`BRD_SER2_RTSCTS`}", "listesi = {}", 1, (A18,)),
    ("R2 README olcut 1: SITL'de 61 yerine 62 (SITL'de tutamayan eski sayi)", README,
     "SITL'de **61**'i", "SITL'de **62**'si", 1, (A18,)),
    ("R3 .param'dan TKOFF_ACCEL_CNT satiri silindi (N .param'dan hesaplanir)", PARAM,
     "\nTKOFF_ACCEL_CNT,1\n", "\n", 1, (A18,)),
    ("R4 yoklama SS6.1: SER2_RTSCTS 0 -> 1 (beklenen-yok olcumle celisir)", YOKLAMA,
     f"  {'SER2_RTSCTS':22s} 0\n", f"  {'SER2_RTSCTS':22s} 1\n", 1, (A18,)),
    ("R5 README olcut 1 ikili sha'sinin son hanesi degisti", README,
     f"(sha256 `{SHA}`)", f"(sha256 `{SHA[:-1]}8`)", 1, (A18,)),
    ("R6 yoklama SS6.1: pozitif kontrol SAFETY_DEFLT 1 -> 0", YOKLAMA,
     f"  {'SAFETY_DEFLT':22s} 1\n", f"  {'SAFETY_DEFLT':22s} 0\n", 1, (A18,)),
    ("R7 README 'her eksik ad DUSER' kurali yumusatildi", README,
     "listenin dışındaki her eksik ad **DÜŞER**", "listenin dışındaki her eksik ad not edilir", 1,
     (A18,)),
    ("R8 README CHUTE_* on hukmunun kayit cumlesi kisaltildi", README,
     "SITL paraşütsüz derlenmiş — paraşüt zinciri ÖLÇÜLEMEDİ", "SITL paraşütsüz derlenmiş", 1,
     (A18,)),
    ("R9 README 'olcumden once, D-449' damgasi (2 yer) silindi", README,
     "ölçümden önce, D-449", "D-449", 2, (A18,)),
    ("R10 README SITL features.txt:139 -> :138", README,
     "SITL_x86_64_linux_gnu/features.txt:139", "SITL_x86_64_linux_gnu/features.txt:138", 1, (A18,)),
)


def git(*arg):
    return subprocess.run(["git", *arg], cwd=KOK, capture_output=True, check=True).stdout


def git_bayt(ref, yol):
    """Dosyanin git'teki kayitli hali, checkout filtreleriyle (autocrlf) = beklenen calisma baytlari."""
    nesne = f":{yol}" if ref == "index" else f"{ref}:{yol}"
    return git("cat-file", "--filters", nesne)


def kapi():
    r = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests",
                        "-p", "test_faz_b_arduplane_sablon.py"],
                       cwd=KOK, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, r.stdout + r.stderr


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ref", default="index", help="'index' (varsayilan) ya da bir rev (HEAD)")
    a = ap.parse_args(argv)
    head = git("rev-parse", "HEAD").decode().strip()
    print(f"# T221-D gercek dosya mutasyonu · {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    print(f"ref={a.ref} · HEAD={head} · core.autocrlf="
          f"{git('config', 'core.autocrlf').decode().strip()}")
    sonuc = 0
    for ad, goreli, eski, yeni, adet, beklenen in MUTANTLAR:
        dosya = KOK / goreli
        asil = dosya.read_bytes()
        ozet = hashlib.sha256(asil).hexdigest()
        kayitli = git_bayt(a.ref, goreli)
        if kayitli != asil:
            print(f"[{ad}] KOSULMADI: calisma kopyasi git {a.ref} ile bayt-es DEGIL ({goreli})")
            sonuc = 1
            continue
        crlf = b"\r\n" in asil
        metin = asil.decode("utf-8").replace("\r\n", "\n")
        if metin.count(eski) != adet:
            print(f"[{ad}] UYGULANAMADI (eslesme {metin.count(eski)} != {adet})")
            sonuc = 1
            continue
        mutant = metin.replace(eski, yeni)
        try:
            dosya.write_bytes((mutant.replace("\n", "\r\n") if crlf else mutant).encode("utf-8"))
            kod, cikti = kapi()
        finally:
            dosya.write_bytes(kayitli)
        geri = hashlib.sha256(dosya.read_bytes()).hexdigest() == ozet
        dusenler = sorted({s.split(" ")[1] for s in cikti.splitlines()
                           if s.startswith(("FAIL: ", "ERROR: "))})
        yakalandi = kod != 0 and all(b in dusenler for b in beklenen)
        print(f"[{ad}] {goreli} · cikis={kod} dusen={dusenler} beklenen={list(beklenen)} "
              f"-> {'YAKALANDI' if yakalandi else 'KACTI'} · geri_yukleme(git cat-file --filters "
              f"{a.ref}) bayt_es={geri} sha256={ozet[:12]}")
        a18 = [s for s in cikti.splitlines() if s.startswith("AssertionError") ]
        print("    ilk AssertionError: " + (a18[0][:220] if a18 else "-"))
        print("    son satir: " + (cikti.strip().splitlines() or [''])[-1])
        if not (yakalandi and geri):
            sonuc = 1
    kod, cikti = kapi()
    temiz = all(git_bayt(a.ref, y) == (KOK / y).read_bytes() for y in (PARAM, README, YOKLAMA))
    print(f"[geri yukleme sonrasi] cikis={kod} · 3 dosya git {a.ref} ile bayt-es={temiz} · "
          f"son satir: {(cikti.strip().splitlines() or [''])[-1]}")
    return sonuc or (0 if kod == 0 and temiz else 1)


if __name__ == "__main__":
    sys.exit(main())
