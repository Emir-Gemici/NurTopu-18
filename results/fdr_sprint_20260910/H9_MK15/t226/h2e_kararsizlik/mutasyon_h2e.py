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
DOSYA = {"test": KOK / "tests" / "test_yks_mk15_hakem_ekrani.py",
         "urun": KOK / "comms" / "yks_gui.py"}
TANI = BURASI / "h2e_tani.py"
PY = sys.executable

ESKI_UYKU = """            f"kaynak reddi={getattr(self.app, 'kaynak_ret_sayaci', 0)}")"""

ADRES_GERI = ("test",
              '    IHA_ADRESI = "127.0.0.2"\n    IKA_ADRESI = "127.0.0.3"',
              '    IHA_ADRESI = "127.0.0.1"\n    IKA_ADRESI = "127.0.0.1"')
HAZIR_GEVSET = ("test", """            if acik:
                return ((app.rota or {}).get("seq") == mesaj["seq"]
                        and app.rota_yok is None)""",
                """            if acik:
                return (app.rota or {}).get("seq") == mesaj["seq"]""")
UYKU_GERI = ("test", ESKI_UYKU,
             ESKI_UYKU + "\n        self._pompala(lambda: False, 0.15)")
ONKOSUL_SIL = ("test",
               "                    self._yalniz_bizim_cerceveler("
               "app, acik_sayisi, yok_sayisi)\n", "")
# URUN mutasyonu: OPEN_ROUTE artik `rota_yok`u TEMIZLEMIYOR — yani T226'nin
# koruduğu gercek kusur geri getiriliyor. Duzeltilmis test bunu YAKALAMALI.
URUN_SIZINTI = ("urun",
                "            self.tespit_bayat = False\n"
                "            self.rota_yok = None\n",
                "            self.tespit_bayat = False\n")

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
    # M5: URUN kusuru, enjeksiyon YOK. Kapinin gevsemedigi burada olculur:
    # `rota_yok` OPEN_ROUTE'ta temizlenmezse test KIRMIZI olmalidir.
    ("M5 urun: OPEN_ROUTE rota_yok'u temizlemiyor", [URUN_SIZINTI], 1, 0),
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
    # BAYT duzeyinde oku/yaz: metin kipinde okuyup geri yazmak dosyanin satir
    # sonlarini CRLF'ten LF'e cevirir ve kaynak agaci "degismis" gosterirdi.
    # Mutasyon kaynak dosyayi AYNEN birakmak zorundadir.
    ham = {ad: y.read_bytes() for ad, y in DOSYA.items()}
    ozet = {ad: hashlib.sha256(b).hexdigest() for ad, b in ham.items()}
    ss = {ad: ("\r\n" if b"\r\n" in b else "\n") for ad, b in ham.items()}
    sonuc = []
    for ad, degisiklikler, beklenen, periyot_ms in MUTASYONLAR:
        metin = dict(ham)
        for hedef, eski, yeni in degisiklikler:
            e = eski.replace("\n", ss[hedef]).encode("utf-8")
            y2 = yeni.replace("\n", ss[hedef]).encode("utf-8")
            if e not in metin[hedef]:
                raise SystemExit(f"MUTASYON UYGULANAMADI ({ad}): desen yok "
                                 f"[{hedef}]:\n{eski}")
            metin[hedef] = metin[hedef].replace(e, y2, 1)
        try:
            for h, y in DOSYA.items():
                if metin[h] != ham[h]:
                    y.write_bytes(metin[h])
            print(ad)
            kod = kos(ad, BURASI / f"mutasyon_{ad.split()[0]}.txt", periyot_ms)
        finally:
            for h, y in DOSYA.items():
                y.write_bytes(ham[h])
                if hashlib.sha256(y.read_bytes()).hexdigest() != ozet[h]:
                    raise SystemExit(f"DOSYA GERI YAZILAMADI ({y}) — elle onar!")
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
