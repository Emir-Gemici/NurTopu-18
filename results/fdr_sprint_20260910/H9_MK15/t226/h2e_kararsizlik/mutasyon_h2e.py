"""H2e fikstur duzeltmesinin MUTASYONLA sinanmasi (12 Eylul olcumu).

Her mutasyon GERCEK dosyayi (tests/test_yks_mk15_hakem_ekrani.py) kisa sureligine
bozar, `h2e_tani.py --enjekte-ms` ile YABANCI bir 127.0.0.1 ucundan NO_ROUTE
serperek kosar ve dosyayi `finally` icinde AYNEN geri yazar (sha256 dogrulanir).

Beklenti:
  M0  mutasyon YOK, enjeksiyon VAR              -> 0  (duzeltme tutuyor)
  M1  ayri geri dongu adresi geri alinir        -> 1  (eski kararsizlik doner)
  M2  hazir kosulundan `rota_yok is None` cikar
      + eski 0,15 s sabit uyku geri gelir       -> 1  (eski kararsizlik doner)
  M3  yabanci cerceve onkosulu (sayac) silinir  -> 0  (yalniz tani kaybolur;
                                                  adres yalitimi hala tutuyor)
  M4  duzeltme ONCESI fikstur + seyrek enjeksiyon -> 1 (mimarin 12 Eylul 01:17
                                                  imzasinin AYNISI)
Kosum:
  O:\\navitas-local-train\\venv\\Scripts\\python.exe -X utf8 -B mutasyon_h2e.py
"""

import hashlib
import subprocess
import sys
from pathlib import Path

BURASI = Path(__file__).resolve().parent
KOK = BURASI.parents[4]
HEDEF = KOK / "tests" / "test_yks_mk15_hakem_ekrani.py"
TANI = BURASI / "h2e_tani.py"
PY = sys.executable

ESKI_UYKU = """        self.assertTrue(self._pompala(islendi), mesaj)"""

ADRES_GERI = ('    IHA_ADRESI = "127.0.0.2"\n    IKA_ADRESI = "127.0.0.3"',
              '    IHA_ADRESI = "127.0.0.1"\n    IKA_ADRESI = "127.0.0.1"')
HAZIR_GEVSET = ("""            if acik:
                return ((app.rota or {}).get("seq") == mesaj["seq"]
                        and app.rota_yok is None)""",
                """            if acik:
                return (app.rota or {}).get("seq") == mesaj["seq"]""")
UYKU_GERI = (ESKI_UYKU,
             ESKI_UYKU + "\n        self._pompala(lambda: False, 0.15)")
ONKOSUL_SIL = ("                    self._yalniz_bizim_cerceveler("
               "app, acik_sayisi, yok_sayisi)\n", "")

# (ad, degisiklikler, beklenen cikis, enjeksiyon periyodu ms)
MUTASYONLAR = [
    ("M0 mutasyon yok", [], 0, 40),
    ("M1 ayri geri dongu adresi geri alindi", [ADRES_GERI], 1, 40),
    ("M2 hazir kosulu gevsetildi + sabit uyku geri geldi",
     [HAZIR_GEVSET, ADRES_GERI, UYKU_GERI], 1, 40),
    ("M3 yabanci cerceve onkosulu silindi", [ONKOSUL_SIL], 0, 40),
    # M4: duzeltme ONCESI fikstur + SEYREK enjeksiyon — mimarin 12 Eylul
    # 01:17 kosumundaki imzanin AYNISI beklenir (":726 sizinti" ve ":728
    # onbellek" alt testleri; olculu alan 1,0'da (34,189,227)).
    ("M4 duzeltme oncesi fikstur + seyrek enjeksiyon",
     [HAZIR_GEVSET, ADRES_GERI, UYKU_GERI, ONKOSUL_SIL], 1, 300),
]


def kos(ad, cikti, periyot_ms):
    p = subprocess.run(
        [PY, "-X", "utf8", "-B", str(TANI), "--enjekte-ms", str(periyot_ms),
         "--cikti", str(cikti)],
        cwd=str(KOK), capture_output=True, text=True,
        encoding="utf-8", errors="replace")
    print(f"    {ad}: cikis={p.returncode}")
    return p.returncode


def main():
    ham = HEDEF.read_text(encoding="utf-8")
    ozet = hashlib.sha256(ham.encode("utf-8")).hexdigest()
    sonuc = []
    for ad, degisiklikler, beklenen, periyot_ms in MUTASYONLAR:
        metin = ham
        for eski, yeni in degisiklikler:
            if eski not in metin:
                raise SystemExit(f"MUTASYON UYGULANAMADI ({ad}): desen yok:\n{eski}")
            metin = metin.replace(eski, yeni, 1)
        try:
            HEDEF.write_text(metin, encoding="utf-8", newline="")
            print(ad)
            kod = kos(ad, BURASI / f"mutasyon_{ad.split()[0]}.txt", periyot_ms)
        finally:
            HEDEF.write_text(ham, encoding="utf-8", newline="")
            simdi = hashlib.sha256(
                HEDEF.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
            if simdi != ozet:
                raise SystemExit("DOSYA GERI YAZILAMADI — elle onar!")
        sonuc.append((ad, beklenen, kod))

    print("\n--- OZET ---")
    hepsi = True
    for ad, beklenen, kod in sonuc:
        tamam = beklenen == kod
        hepsi &= tamam
        print(f"{'OK ' if tamam else 'RED'} {ad}: beklenen={beklenen} gercek={kod}")
    print("MUTASYON_SONUC", "GECTI" if hepsi else "DUSTU")
    return 0 if hepsi else 1


if __name__ == "__main__":
    raise SystemExit(main())
