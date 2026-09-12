"""CURUTUCU'nun KENDI mutasyonlari (worker'inkilerden bagimsiz).

C1  URUN: `_harita_ciz` olculu alan onbellegini ARTIK SILMIYOR (gercek onbellek
    sizintisi). Enjeksiyon YOK. Duzeltilmis testin `assertNotIn` kilidi bunu
    YAKALAMALI  -> beklenen KIRMIZI (1)
C2  URUN: kaynak kilidi IHA verisi icin IP'yi ARTIK DENETLEMIYOR. Enjeksiyon VAR.
    Fikstur yalitimi urunun KENDI kilidine dayaniyorsa test KIRMIZI olmali (1)
C3  TEST: adres yalitimi geri alinir, enjeksiyon YOK -> yesil beklenir (0)
    (yalitimin tek basina davranisi degistirmedigini, kusurun YABANCI CERCEVE
     gerektirdigini gosterir)
C4  URUN: ana haritada OPEN_ROUTE'ta da OLCULU yerlesim kullanilir (sizinti).
    Enjeksiyon YOK -> KIRMIZI beklenir (1)
"""
import hashlib, subprocess, sys
from pathlib import Path

KOK = Path(r"O:\navitas\.claude\worktrees\wf_56b658bb-aff-1")
CIK = Path(r"C:\Users\yunus\AppData\Local\Temp\claude\O--navitas\3e104177-9b44-4ec7-a18f-1f32ed2c3f72\scratchpad\curutucu")
TANI = KOK / "results/fdr_sprint_20260910/H9_MK15/t226/h2e_kararsizlik/h2e_tani.py"
DOSYA = {"test": KOK / "tests" / "test_yks_mk15_hakem_ekrani.py",
         "urun": KOK / "comms" / "yks_gui.py"}
PY = sys.executable

ONBELLEK_SIL = ("urun",
                "        else:\n            alanlar.pop(str(c), None)\n",
                "        else:\n            pass\n")
KILIT_KAPAT = ("urun",
               "        return ((adr[0] == iha_peer[0]),\n",
               "        return (True,\n")
ADRES_GERI = ("test",
              '    IHA_ADRESI = "127.0.0.2"\n    IKA_ADRESI = "127.0.0.3"',
              '    IHA_ADRESI = "127.0.0.1"\n    IKA_ADRESI = "127.0.0.1"')
OLCULU_HEP = ("urun",
              '        olcu = (self._harita_olculu_yerlesim(c, w, rota_yok_metni, inset_var)\n'
              '                if (not inset_var or rota_yok_metni) else None)\n',
              '        olcu = self._harita_olculu_yerlesim(c, w, rota_yok_metni, inset_var)\n')

MUTASYONLAR = [
    ("C0 mutasyon yok, enjeksiyon yok", [], 0, 0),
    ("C1 urun: olculu alan onbellegi silinmiyor", [ONBELLEK_SIL], 1, 0),
    ("C2 urun: kaynak kilidi IP denetimi kapali + enjeksiyon", [KILIT_KAPAT], 1, 40),
    ("C3 test: adres yalitimi geri, enjeksiyon YOK", [ADRES_GERI], 0, 0),
    ("C4 urun: ana harita hep olculu yerlesim", [OLCULU_HEP], 1, 0),
]


def main():
    ham = {a: y.read_bytes() for a, y in DOSYA.items()}
    ozet = {a: hashlib.sha256(b).hexdigest() for a, b in ham.items()}
    ss = {a: ("\r\n" if b"\r\n" in b else "\n") for a, b in ham.items()}
    sonuc = []
    for ad, degs, beklenen, periyot in MUTASYONLAR:
        metin = dict(ham)
        for hedef, eski, yeni in degs:
            e = eski.replace("\n", ss[hedef]).encode("utf-8")
            y2 = yeni.replace("\n", ss[hedef]).encode("utf-8")
            if e not in metin[hedef]:
                raise SystemExit(f"DESEN YOK ({ad}) [{hedef}]:\n{eski}")
            if metin[hedef].count(e) != 1:
                raise SystemExit(f"DESEN TEK DEGIL ({ad}) [{hedef}]: {metin[hedef].count(e)}")
            metin[hedef] = metin[hedef].replace(e, y2, 1)
        try:
            for h, y in DOSYA.items():
                if metin[h] != ham[h]:
                    y.write_bytes(metin[h])
            p = subprocess.run(
                [PY, "-X", "utf8", "-B", str(TANI), "--enjekte-ms", str(periyot),
                 "--kanca", "--cikti", str(CIK / f"{ad.split()[0]}.txt")],
                cwd=str(KOK), capture_output=True, text=True,
                encoding="utf-8", errors="replace")
            kod = p.returncode
        finally:
            for h, y in DOSYA.items():
                y.write_bytes(ham[h])
                if hashlib.sha256(y.read_bytes()).hexdigest() != ozet[h]:
                    raise SystemExit(f"GERI YAZILAMADI {y}")
        print(f"{ad}: beklenen={beklenen} gercek={kod}", flush=True)
        sonuc.append((ad, beklenen, kod))
    hepsi = all(b == k for _, b, k in sonuc)
    print("CURUTUCU_MUTASYON", "GECTI" if hepsi else "DUSTU")
    return 0 if hepsi else 1


if __name__ == "__main__":
    raise SystemExit(main())
