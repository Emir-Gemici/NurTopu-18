# -*- coding: utf-8 -*-
"""T243-C: kilitli blogun DISINA konan celiskili hukum — hangisi yakalanir?

Curutucunun uc probunu (S1/S2/S3) GERCEK dosyada yeniden kurar. Amac kapatmak
degil, SINIRI OLCMEKTIR: hangi bicim dusuruyor, hangisi kaciyor?
Her denemeden sonra sha256 ile bayt-es geri yukleme dogrulanir.
"""
import hashlib
import subprocess
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]
PY_EXE = r"O:\navitas-local-train\venv\Scripts\python.exe"
FDR = KOK / "FDR" / "BOLUM_3_SISTEM_SPESIFIKASYONLARI.md"
CAPA = "**Bu alt bölümdeki hiçbir sayı RF ölçümü değildir:**"

PROBLAR = [
    ("S1 FARKLI basla celiskili ikinci hukum (curutucunun probu)",
     "Gözden geçirilmiş duyarlılık (13 Eylül): gerçekçi değer 3715,4 B/s; "
     "ECC açıkken bile ham bütçe aşılmaz."),
    ("S2 FARKLI basla 'yayin tavani KAPATILDI' celiskisi (curutucunun probu)",
     "Yayın tavanı sorunu 13 Eylül'de KAPATILDI; besleme hızlanınca yayın da "
     "hızlanıyor."),
    ("S3 AYNI basla ikinci (ikiz) blok — T243-C bunu kapatti",
     "⚠ **Duyarlılık (HESAP, ölçüm değil):** gözden geçirilmiş değer "
     "**3715,4 B/s**; ECC açıkken bile ham bütçe aşılmaz."),
]


def kos():
    r = subprocess.run(
        [PY_EXE, "-X", "utf8", "-B", "-m", "unittest", "discover",
         "-s", "tests", "-p", "test_t243_paket_boyutu.py"],
        cwd=str(KOK), capture_output=True, text=True, encoding="utf-8",
        errors="replace")
    son = [s for s in (r.stdout + r.stderr).splitlines() if s.strip()]
    dusen = [s for s in son if s.startswith(("FAIL:", "ERROR:"))]
    return r.returncode, (son[-1] if son else "?"), dusen


def main():
    rc, ozet, _ = kos()
    print(f"TABAN: rc={rc} · {ozet}")
    if rc != 0:
        return 2
    for ad, cumle in PROBLAR:
        ham = FDR.read_bytes()
        sha = hashlib.sha256(ham).hexdigest()
        metin = ham.decode("utf-8")
        assert metin.count(CAPA) == 1, "capa tek degil"
        FDR.write_bytes(metin.replace(CAPA, cumle + "\n\n" + CAPA, 1)
                        .encode("utf-8"))
        try:
            rc2, ozet2, dusen = kos()
        finally:
            FDR.write_bytes(ham)
            assert hashlib.sha256(FDR.read_bytes()).hexdigest() == sha
        durum = "YAKALANDI" if rc2 != 0 else "KACTI (kapatilmadi)"
        print(f"  [{durum}] {ad} · {ozet2} · "
              + "; ".join(d.split("(")[0].strip() for d in dusen[:3]))
    rc3, ozet3, _ = kos()
    print(f"GERI YUKLEME SONRASI: rc={rc3} · {ozet3}")
    return 0
if __name__ == "__main__":
    sys.exit(main())
