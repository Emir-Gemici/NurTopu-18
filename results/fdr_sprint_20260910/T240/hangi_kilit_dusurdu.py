# -*- coding: utf-8 -*-
"""T240-B / T240-C — her yeni mutanti HANGI kilidin dusurdugunu OLCER (iddia degil, olcum).

KANIT.md'deki "kapali hukum cumlesi kumesi (tek yakalayan)" gibi hukumler ancak
hata METNIYLE dogrulanabilir: mutant uygulanir, ilgili tek test METODU kosulur ve
AssertionError metni kaydedilir; dosya sha256 ile BAYT-ES geri yuklenir.

Kullanim (depo kokunden):
  O:\\navitas-local-train\\venv\\Scripts\\python.exe -X utf8 -B \\
      results/fdr_sprint_20260910/T240/hangi_kilit_dusurdu.py
Cikis 0 = her mutant dustu ve her dosya bayt-es geri yuklendi.
"""

import hashlib
import io
import re
import subprocess
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[3]
CIKTI = Path(__file__).resolve().parent
PY = sys.executable

sys.path.insert(0, str(CIKTI))
from mutasyon_t240 import (  # noqa: E402
    SOZLESME, KURULUM, README, ON_KAYIT_T235,
    C_Y4_CAPA, C_Y4, C_Y4B, C_Y7, SOZLESME_KAYNAK_BASI_C, C_ILKELER, C_SON_PARAGRAF,
    K_CAPA, K_A4, K_X16_CAPA, K_Y5, K_Y10_ESKI, K_Y10_YENI, R_CAPA, O_CAPA, O_D461)

#: (ad, dosya, eski, yeni, test yolu)
VAKALAR = (
    ("Y4  &#822; harf harf", SOZLESME, C_Y4_CAPA, C_Y4,
     "test_yks_mk15_hakem_ekrani.H4_KameraKanitKaynagi.test_H4e_contracts_ornegi_kodla_ayni"),
    ("Y4b &#x336; onaltilik", SOZLESME, C_Y4_CAPA, C_Y4B,
     "test_yks_mk15_hakem_ekrani.H4_KameraKanitKaynagi.test_H4e_contracts_ornegi_kodla_ayni"),
    ("Y7a baslıksiz paragraf (kaynak onu)", SOZLESME, SOZLESME_KAYNAK_BASI_C,
     C_Y7 + "\n\n" + SOZLESME_KAYNAK_BASI_C,
     "test_yks_mk15_hakem_ekrani.H4_KameraKanitKaynagi.test_H4e_contracts_ornegi_kodla_ayni"),
    ("Y7b baslıksiz paragraf (ilkeler onu)", SOZLESME, C_ILKELER, C_Y7 + "\n\n" + C_ILKELER,
     "test_yks_mk15_hakem_ekrani.H4_KameraKanitKaynagi.test_H4e_contracts_ornegi_kodla_ayni"),
    ("Y7c baslıksiz paragraf (son paragraf onu)", SOZLESME, C_SON_PARAGRAF,
     C_Y7 + "\n\n" + C_SON_PARAGRAF,
     "test_yks_mk15_hakem_ekrani.H4_KameraKanitKaynagi.test_H4e_contracts_ornegi_kodla_ayni"),
    ("Y5  aile disi es anlamli", KURULUM, K_CAPA, K_Y5 + K_CAPA,
     "test_isaretli_gosterici.GostericiDosyalari.test_G8_D453_D454_olculmemis_hukum_celiski_eski_komut"),
    ("Y10 esik birimi s -> ms", KURULUM, K_Y10_ESKI, K_Y10_YENI,
     "test_isaretli_gosterici.GostericiDosyalari.test_G8_D453_D454_olculmemis_hukum_celiski_eski_komut"),
    ("Y11 anahtarsiz README celiskisi", README, R_CAPA,
     R_CAPA + " Zincir yerinde; kapılar sorun çıkarmadı.",
     "test_faz_b_arduplane_sablon"),
    ("D461 ikinci gevsetilmis olcut", ON_KAYIT_T235, O_CAPA, O_CAPA + O_D461,
     "test_t235_alan_etiketi.OnKayitKilitleri.test_SS4_T236_kabul_olcutu_TEKLIGI"),
    # ── T240-C (D-465): `&#96;` sarmali SAHTE KOD ARALIGI ────────────────────
    ("X15 &#96; sarmali ~~cizik~~", KURULUM, K_A4, "- &#96;~~" + K_A4[2:] + "~~&#96;",
     "test_isaretli_gosterici.GostericiDosyalari.test_G8_D465_on_kayitli_metin_esitligi_dort_bolum"),
    ("X16 &#96; sarmali nabiz maddesi", KURULUM, K_X16_CAPA,
     "- &#96;~~" + K_X16_CAPA[2:] + "~~&#96;",
     "test_isaretli_gosterici.GostericiDosyalari.test_G8_D465_on_kayitli_metin_esitligi_dort_bolum"),
    ("X17 &#96; sarmali <s>cizik</s>", KURULUM, K_A4, "- &#96;<s>" + K_A4[2:] + "</s>&#96;",
     "test_isaretli_gosterici.GostericiDosyalari.test_G8_D465_on_kayitli_metin_esitligi_dort_bolum"),
    # ... ve ayni uc mutant, ESKI (ayiklamali) kilidi de dusurmeli: K1 duzeltmesinden
    # sonra `&#96;` COZULMEDIGI icin `beyaz_liste_disi_cizik` onlari DOGRUDAN gorur.
    ("X15b eski cizik kilidi de dusurur", KURULUM, K_A4, "- &#96;~~" + K_A4[2:] + "~~&#96;",
     "test_isaretli_gosterici.GostericiDosyalari."
     "test_G8_D453_D454_olculmemis_hukum_celiski_eski_komut"),
    ("X17b eski cizik kilidi de dusurur", KURULUM, K_A4, "- &#96;<s>" + K_A4[2:] + "</s>&#96;",
     "test_isaretli_gosterici.GostericiDosyalari."
     "test_G8_D453_D454_olculmemis_hukum_celiski_eski_komut"),
)


def kos(hedef):
    p = subprocess.run([PY, "-X", "utf8", "-B", "-m", "unittest", hedef, "-v"],
                       cwd=str(KOK / "tests"), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def main():
    kayit = io.StringIO()

    def yaz(s=""):
        print(s)
        kayit.write(s + "\n")

    yaz("# T240-B / T240-C — yeni mutantlari HANGI kilit dusurdu (hata metniyle)")
    yaz("# yorumlayici: {}".format(PY))
    yaz("# depo koku : {}".format(KOK))
    yaz()
    tamam = True
    for ad, goreli, eski, yeni, hedef in VAKALAR:
        yol = KOK / goreli
        ham = yol.read_bytes()
        once = hashlib.sha256(ham).hexdigest()
        metin = ham.decode("utf-8")
        if metin.count(eski) != 1:
            yaz("{:<42} CAPA HATASI ({} kez)".format(ad, metin.count(eski)))
            tamam = False
            continue
        yol.write_bytes(metin.replace(eski, yeni, 1).encode("utf-8"))
        try:
            rc, cikti = kos(hedef)
        finally:
            yol.write_bytes(ham)
        sonra = hashlib.sha256(yol.read_bytes()).hexdigest()
        satirlar = [s for s in cikti.splitlines()
                    if "AssertionError" in s or s.startswith("FAIL:") or s.startswith("ERROR:")]
        yaz("## {}".format(ad))
        yaz("   dosya={} cikis={} geri_bayt_es={}".format(
            goreli.split("/")[-1], rc, once == sonra))
        for s in satirlar[:3]:
            yaz("   {}".format(re.sub(r"\s+", " ", s.strip())[:300]))
        yaz()
        tamam &= (rc != 0 and once == sonra)
    yaz("HUKUM: {}".format("HEPSI DUSTU, geri yukleme bayt-es" if tamam else "BOZUK"))
    (CIKTI / "hangi_kilit_dusurdu.txt").write_text(kayit.getvalue(), encoding="utf-8")
    return 0 if tamam else 1


if __name__ == "__main__":
    sys.exit(main())
