"""NEDEN: T226-D2'nin O5/D1/O6 ve ret-nedeni baglarini gercek dosyada sina.

Yalniz bu worktree'de baska test/yazici yokken kosulur. Her denemeden sonra
asil baytlar finally ile geri yuklenir; once ve sonra temiz test zorunludur.
Onceki mutasyon kanitlari korunur; bu kosum ayri dosyaya yazilir.
"""
import hashlib
import re
import subprocess
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]
CIKTI = Path(__file__).with_name("mutasyon_t226d2_20260911.txt")
GUI = KOK / "comms/yks_gui.py"
SOZLESME = KOK / "CONTRACTS.md"
MMD = KOK / "FDR/sekiller/akis_d.mmd"
TEST = ["-m", "unittest", "discover", "-s", "tests", "-p",
        "test_yks_mk15_hakem_ekrani.py", "-q"]
AKIS = ["results/fdr_sprint_20260910/H9_MK15/t226/akis_kapsam_t226d.py",
        "--taban", "76df4dcb"]


def kos(argv):
    p = subprocess.run([sys.executable, "-X", "utf8", "-B", *argv], cwd=KOK,
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=240)
    return p.returncode, p.stdout + p.stderr


def main():
    kaynaklar = {p: p.read_bytes() for p in (GUI, SOZLESME, MMD)}
    sha = {p: hashlib.sha256(b).hexdigest() for p, b in kaynaklar.items()}
    metinler = {p: b.decode("utf-8").replace("\r\n", "\n")
                for p, b in kaynaklar.items()}
    sozlesme_satiri = next(s for s in metinler[SOZLESME].splitlines()
                          if s.startswith("**`KAMERA_KANIT.kaynak`"))
    d78 = next(s for s in metinler[MMD].splitlines() if s.lstrip().startswith('d78["'))
    d83 = next(s for s in metinler[MMD].splitlines() if s.lstrip().startswith('d83["'))
    mutantlar = [
        ("N11 O5: NO_ROUTE onbellegi temizlenmez", GUI,
         "            alanlar.pop(str(c), None)", "            pass",
         TEST + ["-k", "H2e"], "test_H2e_olcek_1_5"),
        ("N12 D1: kaynak sozlesmesi cizilir", SOZLESME,
         sozlesme_satiri, "~~" + sozlesme_satiri + "~~",
         TEST + ["-k", "H4e"], "test_H4e_contracts_ornegi_kodla_ayni"),
        ("N13 O6: HB etiketi H kutusuna geri iner", GUI,
         '        hb_y, hb_capa = ((hy - 12 - S(2), {"anchor": "s"}) if kucuk\n'
         '                         else (hy - 20, {}))',
         '        hb_y, hb_capa = (hy - 20, {})',
         TEST + ["-k", "H2c"], "test_H2c_olcek_1_5_hakem_ekrani"),
        ("N14: d78 yanlis ret cagrisina kayar", MMD, d78,
         re.sub(r"\.py:\d+", ".py:2217", d78), AKIS, "HATA d78"),
        ("N15: d83 yanlis ret cagrisina kayar", MMD, d83,
         re.sub(r"\.py:\d+", ".py:2217", d83), AKIS, "HATA d83"),
        ("N16: d83 dugumu silinir", MMD, d83, "", AKIS, "HATA d83 [SILINEN]"),
        ("N17: d83 cagri ve kenari birlikte yanlis anlama kayar", MMD,
         metinler[MMD], metinler[MMD].replace(d83, d83.replace(":2226", ":2248"))
         .replace('d73 -->|"evet: BAYAT_TESPIT"| d83',
                  'd73 -->|"evet: IKA_ACK_KANITI_YOK"| d83'),
         AKIS, "HATA [KENAR_KUMESI]"),
    ]
    log, hatalar = [], 0

    def yaz(s):
        log.append(s)
        print(s, flush=True)

    try:
        for ad, argv in (("TEMIZ ONCE", TEST), ("AKIS ONCE", AKIS)):
            rc, out = kos(argv)
            yaz(f"{ad}: komut={argv!r} exit={rc}\n{out.strip()}")
            if rc:
                return 2
        for ad, yol, eski, yeni, argv, beklenen in mutantlar:
            metin = metinler[yol]
            if metin.count(eski) != 1:
                raise ValueError(f"{ad}: hedef tek degil")
            try:
                metin = metin.replace(eski, yeni)
                if b"\r\n" in kaynaklar[yol]:
                    metin = metin.replace("\n", "\r\n")
                yol.write_bytes(metin.encode("utf-8"))
                rc, out = kos(argv)
                yakalandi = rc == 1 and beklenen in out
                hatalar += not yakalandi
                yaz(f"{ad}: komut={argv!r} exit={rc} "
                    f"{'YAKALANDI' if yakalandi else 'KACTI'}\n{out.strip()}")
            finally:
                yol.write_bytes(kaynaklar[yol])
        esit = all(hashlib.sha256(p.read_bytes()).hexdigest() == h for p, h in sha.items())
        yaz(f"GERI YUKLEME SHA256 ESIT: {esit}")
        hatalar += not esit
        for ad, argv in (("TEMIZ SONRA", TEST), ("AKIS SONRA", AKIS)):
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
