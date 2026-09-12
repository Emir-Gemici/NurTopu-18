"""T226-D3 (D-460 karar 3) — YENI denetimlerin CURUTUCUSU.

NEDEN: D-460 bagimsiz mimar denetimi olctu ki akis kapisi TABAN-AGAC kiyasindan
ibaretti; tabanda zaten var olan yanlis atfi goremiyor, hatta DOGRU atfi HATA
sayiyordu. T226-D3 iki sey ekledi:
  (a) TABANDAN BAGIMSIZ ALTGRAFIK denetimi (akis_kapsam_t226d.py),
  (b) ANA haritada OPEN_ROUTE kalinti kesisimini SAYIYLA kilitleyen H2f
      (tests/test_yks_mk15_hakem_ekrani.py).
Bu betik ikisinin de GERCEKTEN dustugunu olcer. Eklenen denetim dusmuyorsa
kapi degildir (D-354 sinifi).

MUTANTLAR
  M1  d71 yeniden 2182'ye cekilir (denetcinin olctugu asil vaka: taban-agac
      kiyasi bunu "AYNI" der; YALNIZ ALTGRAFIK yakalar)
  M2  d112 yeniden 3931'e cekilir (ayni sinif)
  M3  d113 dugumu sD9'dan (ika_baslat) sD8'e (firlatma) TASINIR — dosya:satir
      DEGISMEZ, yani taban kiyasi "AYNI" der; yalniz ALTGRAFIK yakalar
  M4  d100 dugumu sD8'den (firlatma) sD6'ya (onayla) TASINIR (ayni sinif)
  M5  d10 CAGRI dugumu silinir — d11'in CAGRI_GOVDESI bagisikligi dusmeli
      ("hemen once" kuralinin DAR oldugunun kaniti)
  M6  ANA haritada "ref" etiketi 60 px YUKARI alinir: road3 kalintisi KAYBOLUR
      -> H2f'in sayi kilidi dusmeli. (Olculdu: yatay `rx - 60` YETMEZ —
      kutular 209..215 x 395..399 araliginda hala kesisiyor ve mutant KACIYOR;
      esigi degil MUTANTI duzelttik, kapi oldugu gibi kaldi.)
  M7  ANA haritada "ref" IKA-KB'nin ustune konur: kalinti BUYUR -> H2f dusmeli

Yalniz bu worktree'de baska test/yazici yokken kosulur. Her denemeden sonra
asil baytlar finally ile geri yuklenir; once ve sonra temiz kosum zorunludur.

KOSUM (depo kokunden):
  O:/navitas-local-train/venv/Scripts/python.exe -X utf8 -B \
      results/fdr_sprint_20260910/H9_MK15/t226/mutasyon_t226d3.py
Cikis: 0 butun mutantlar yakalandi · 1 en az biri kacti · 2 on kosum kirmizi
"""
import hashlib
import re
import subprocess
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]
CIKTI = Path(__file__).with_name("mutasyon_t226d3_20260912.txt")
GUI = KOK / "comms/yks_gui.py"
MMD = KOK / "FDR/sekiller/akis_d.mmd"
TEST = ["-m", "unittest", "discover", "-s", "tests", "-p",
        "test_yks_mk15_hakem_ekrani.py", "-q"]
AKIS = ["results/fdr_sprint_20260910/H9_MK15/t226/akis_kapsam_t226d.py",
        "--taban", "76df4dcb"]
H2C = TEST + ["-k", "H2c"]
KALINTI = "KALINTI KESİŞİM SAYISI DEĞİŞTİ"


def kos(argv):
    p = subprocess.run([sys.executable, "-X", "utf8", "-B", *argv], cwd=KOK,
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=600)
    return p.returncode, p.stdout + p.stderr


def satir(metin, kimlik):
    """`.mmd` icinde `<kimlik>[` ya da `<kimlik>{` ile baslayan TEK satir."""
    bulunan = [s for s in metin.splitlines()
               if s.lstrip().startswith(kimlik + "[")
               or s.lstrip().startswith(kimlik + "{")]
    if len(bulunan) != 1:
        raise ValueError(f"{kimlik}: {len(bulunan)} satir")
    return bulunan[0]


def tasi(metin, kimlik, hedef_kimlik):
    """`kimlik` dugum satirini kendi yerinden alip `hedef_kimlik`in ARDINA koy."""
    kaynak = satir(metin, kimlik)
    hedef = satir(metin, hedef_kimlik)
    yeni = metin.replace(kaynak + "\n", "", 1)
    if yeni == metin:
        raise ValueError(f"{kimlik}: satir cikarilamadi")
    return yeni.replace(hedef, hedef + "\n" + kaynak, 1)


def main():
    kaynaklar = {p: p.read_bytes() for p in (GUI, MMD)}
    sha = {p: hashlib.sha256(b).hexdigest() for p, b in kaynaklar.items()}
    metinler = {p: b.decode("utf-8").replace("\r\n", "\n")
                for p, b in kaynaklar.items()}
    mmd = metinler[MMD]
    d71, d112 = satir(mmd, "d71"), satir(mmd, "d112")
    ref_asil = ('                            else ((rx - 16, ry, "e"),))')
    mutantlar = [
        ("M1: d71 yeniden _ankor_yok_onayini_kapat'in 2182'sine cekilir", MMD,
         d71, re.sub(r"\.py:\d+", ".py:2182", d71), AKIS,
         "HATA d71 [ALTGRAFIK]"),
        ("M2: d112 yeniden iha_indi'nin 3931'ine cekilir", MMD,
         d112, re.sub(r"\.py:\d+", ".py:3931", d112), AKIS,
         "HATA d112 [ALTGRAFIK]"),
        ("M3: d113 dugumu sD9'dan sD8'e tasinir (dosya:satir DEGISMEZ)", MMD,
         mmd, tasi(mmd, "d113", "d103"), AKIS, "HATA d113 [ALTGRAFIK]"),
        ("M4: d100 dugumu sD8'den sD6'ya tasinir (dosya:satir DEGISMEZ)", MMD,
         mmd, tasi(mmd, "d100", "d83"), AKIS, "HATA d100 [ALTGRAFIK]"),
        ("M5: d10 CAGRI dugumu silinir (d11 bagisikligi dusmeli)", MMD,
         satir(mmd, "d10") + "\n", "", AKIS, "HATA d11 [ALTGRAFIK]"),
        ("M6: ANA haritada 'ref' 60 px yukari alinir — road3 kalintisi KAYBOLUR",
         GUI, ref_asil,
         '                            else ((rx - 16, ry - 60, "e"),))',
         H2C, KALINTI),
        ("M7: ANA haritada 'ref' IKA-KB'nin ustune konur — kalinti BUYUR", GUI,
         ref_asil,
         '                            else ((self._mxy(*KB_KONUM_M, c)[0] + 16,\n'
         '                                   self._mxy(*KB_KONUM_M, c)[1], "w"),))',
         H2C, KALINTI),
    ]
    log, hatalar = [], 0

    def yaz(s):
        log.append(s)
        print(s, flush=True)

    try:
        for ad, argv in (("AKIS ONCE", AKIS), ("H2C ONCE", H2C)):
            rc, out = kos(argv)
            yaz(f"{ad}: komut={argv!r} exit={rc}\n{out.strip()}")
            if rc:
                return 2
        for ad, yol, eski, yeni, argv, beklenen in mutantlar:
            metin = metinler[yol]
            if metin.count(eski) != 1:
                raise ValueError(f"{ad}: hedef tek degil ({metin.count(eski)})")
            try:
                metin = metin.replace(eski, yeni)
                if b"\r\n" in kaynaklar[yol]:
                    metin = metin.replace("\n", "\r\n")
                yol.write_bytes(metin.encode("utf-8"))
                rc, out = kos(argv)
                yakalandi = rc == 1 and beklenen in out
                hatalar += not yakalandi
                yaz(f"{ad}: komut={argv!r} exit={rc} beklenen={beklenen!r} "
                    f"{'YAKALANDI' if yakalandi else 'KACTI'}\n{out.strip()}")
            finally:
                yol.write_bytes(kaynaklar[yol])
        esit = all(hashlib.sha256(p.read_bytes()).hexdigest() == h
                   for p, h in sha.items())
        yaz(f"GERI YUKLEME SHA256 ESIT: {esit}")
        hatalar += not esit
        for ad, argv in (("AKIS SONRA", AKIS), ("H2C SONRA", H2C)):
            rc, out = kos(argv)
            yaz(f"{ad}: komut={argv!r} exit={rc}\n{out.strip()}")
            hatalar += rc != 0
        yaz(f"SONUC: {len(mutantlar)} mutasyon; hata={hatalar}")
        return 1 if hatalar else 0
    finally:
        for p, b in kaynaklar.items():
            if p.read_bytes() != b:
                p.write_bytes(b)
        CIKTI.write_text("\n\n".join(log) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
