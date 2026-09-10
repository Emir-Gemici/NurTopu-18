"""T232 mutasyon kontrolu — kapi (tests/test_atolye_test_gunu.py) bozulmayi GERCEKTEN yakaliyor mu.

Her mutant bir dosyayi gecici bozar, kapiyi kosar (DUSMELI), dosyayi bayt-es geri yazar ve
sha256 ile dogrular. Sonda temiz kosu (OK olmali). Cikti: ayni klasorde mutasyon_ciktisi.txt.

Kosum (depo kokunden):
  O:\\navitas-local-train\\venv\\Scripts\\python.exe -B results/fdr_sprint_20260910/T232/mutasyon_t232.py
"""
from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[3]
KAGIT = KOK / "ATOLYE_TEST_GUNU_20260912.md"
SABLON = KOK / "results" / "atolye_20260912" / "SONUC_SABLONU.md"
UCUS = KOK / "scripts" / "ucus_logu_devrilme.py"
CIKTI = Path(__file__).with_name("mutasyon_ciktisi.txt")
KOMUT = [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests",
         "-p", "test_atolye_test_gunu.py"]


def _sil_satir(baslangic):
    def f(m):
        satirlar = m.split("\n")
        kalan = [s for s in satirlar if not s.startswith(baslangic)]
        assert len(kalan) == len(satirlar) - 1, f"mutant satiri tek degil: {baslangic!r}"
        return "\n".join(kalan)
    return f


def _degistir(eski, yeni):
    def f(m):
        # Depo dosyalari karisik satir sonlu (CRLF checkout); kalip dosyanin satir sonuna uyar.
        e, y = eski, yeni
        if "\r\n" in m:
            e, y = e.replace("\n", "\r\n"), y.replace("\n", "\r\n")
        assert m.count(e) == 1, f"mutant metni tek degil: {eski!r}"
        return m.replace(e, y)
    return f


MUTANTLAR = [
    ("M1 A5 bolumunden Kabul satiri silindi", KAGIT,
     _sil_satir("- **Kabul (bu kâğıtta ön kayıt; eşik koddaki 3 s")),
    ("M2 A3 GERI AL adimi silindi", KAGIT, _sil_satir("- **Adım 3 — GERİ AL (zorunlu")),
    ("M3 'GEÇTİ' kelimesi eklendi (A6 kabul)", KAGIT,
     _degistir("= 200 ms, çıkış 0;", "= 200 ms, çıkış 0 → GEÇTİ;")),
    ("M4 dokum atfi degeri degisti (FS_THR_ENABLE 3 -> 1)", KAGIT,
     _degistir("`FS_THR_ENABLE=3` (döküm :411)", "`FS_THR_ENABLE=1` (döküm :411)")),
    ("M5 olu betik atfi (sik_rf_olc -> sik_rf_olcum)", KAGIT,
     _degistir("scripts/sik_rf_olc.py --rol yanki --port COMy",
               "scripts/sik_rf_olcum.py --rol yanki --port COMy")),
    ("M6 FOV hesabi sonucu degisti (55,3 -> 57,3)", KAGIT,
     _degistir("2 · atan(0,5239) = 55,3°", "2 · atan(0,5239) = 57,3°")),
    ("M7 A9 basligi 15 dk -> 20 dk (tablo dilimiyle celisik)", KAGIT,
     _degistir("### A9 — Kamera yatay FOV · 15 dk", "### A9 — Kamera yatay FOV · 20 dk")),
    ("M8 A10 model yolu eski hataya dondu (models/)", KAGIT,
     _degistir("--model jetson_paket/models/navitas_seg_v36_best.pt",
               "--model models/navitas_seg_v36_best.pt")),
    ("M9 SONUC_SABLONU A7 satiri silindi", SABLON, _sil_satir("| A7 |")),
    ("M10 ucus_logu_devrilme --help dali kaldirildi", UCUS,
     _degistir('    if any(a in ("-h", "--help") for a in argv[1:]):\n        print(__doc__)\n'
               '        return 0\n', "")),
]


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _kos():
    ortam = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    r = subprocess.run(KOMUT, cwd=str(KOK), env=ortam, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=900)
    son = [s for s in (r.stdout + r.stderr).strip().splitlines() if s.strip()]
    ozet = son[-1] if son else "(cikti yok)"
    dusenler = sorted({s.split("(")[1].split(")")[0].split(".")[-1]
                       for s in (r.stdout + r.stderr).splitlines()
                       if s.startswith(("FAIL:", "ERROR:")) and "(" in s})
    return r.returncode, ozet, dusenler


def main():
    satirlar = [f"T232 mutasyon kontrolu · {sys.executable}", ""]
    yakalanan = 0
    for ad, dosya, mutasyon in MUTANTLAR:
        asil_bayt = dosya.read_bytes()
        asil_sha = _sha(dosya)
        metin = asil_bayt.decode("utf-8")
        try:
            dosya.write_bytes(mutasyon(metin).encode("utf-8"))
            kod, ozet, dusenler = _kos()
        finally:
            dosya.write_bytes(asil_bayt)
        assert _sha(dosya) == asil_sha, f"{dosya} geri yazilamadi"
        yakaladi = kod != 0
        yakalanan += yakaladi
        satirlar.append(f"{ad}: cikis={kod} · {ozet} · {'YAKALANDI' if yakaladi else 'KACTI'}")
        satirlar.append(f"    dusen testler: {', '.join(dusenler) or '-'}")
    kod, ozet, _ = _kos()
    satirlar += ["", f"TEMIZ KOSU (geri alindiktan sonra): cikis={kod} · {ozet}",
                 f"SONUC: {yakalanan}/{len(MUTANTLAR)} mutant yakalandi; dosyalar sha256 ile geri dogrulandi"]
    metin = "\n".join(satirlar) + "\n"
    CIKTI.write_text(metin, encoding="utf-8")
    print(metin)
    return 0 if yakalanan == len(MUTANTLAR) and kod == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
