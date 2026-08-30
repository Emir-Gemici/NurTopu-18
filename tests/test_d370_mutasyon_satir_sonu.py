"""D-370 — MUTASYON DESENI SATIR SONUNA TAKILMAMALI, ve UYGULANMAYAN
mutasyon "gecti" SAYILMAMALI.

🔴 KUSUR (Codex bagimsiz denetiminde bulundu, kendim dogruladim):
`129_t141_mutasyon_olcumu.py`'nin M2' mutasyonu satir sonu ICEREN bir desen
ariyordu:

    (NAV, b"        current_no_route is None\\n", ...)

`simulation/scripts/ika_nav.py` TAMAMEN CRLF'tir: olculdu, 658 CRLF ve
**0 ciplak LF**. Desen dosyada **0 KEZ** eslesiyor, CRLF hâli 1 kez.
Yani M2' mutasyonu **HIC UYGULANMIYORDU** — ve betik yine **exit 0**
donuyordu. Cikis kodunu okuyan bir kapi bunu BASARI sanardi.

⚠ Betigin KENDI docstring'i bu tuzagi zaten uyariyordu (T123'te ayni sey
olmus). **Uyari yetmedi**; kod duzeyinde onlem gerekiyordu. Bu, bugunun
tekrar eden dersinin bir ornegi daha: OLCEN ARACIN KENDISI DE OLCULMELIDIR
(D-349, D-354, D-357, D-360).

DUZELTME SONRASI OLCULDU: M2' artik uygulaniyor ve
`T141 icra kilidi 1/7 · mevcut kod kilidi 0/3` veriyor — yani kaydin
iddiasi (M2' YAKALANIYOR) simdi GERCEKTEN olculdu.
"""
import ast
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
BETIK = KOK / "scripts" / "olcum" / "129_t141_mutasyon_olcumu.py"
NAV = KOK / "simulation" / "scripts" / "ika_nav.py"
KAYNAK = BETIK.read_text(encoding="utf-8")


def _kodu(metin: str) -> str:
    """Yorumlari at — mutasyon/denetim YORUM uzerinde yapilmaz (D-354)."""
    return "\n".join(s for s in metin.splitlines()
                     if not s.lstrip().startswith("#"))


KOD = _kodu(KAYNAK)


class SatirSonuUyarlamasi(unittest.TestCase):
    def test_capa_BETIK_AYRISTIRILIYOR(self):
        self.assertTrue(BETIK.is_file())
        ast.parse(KAYNAK)

    def test_UYARLAMA_ISLEVI_VAR(self):
        self.assertIn("_satir_sonuna_uyarla(", KOD,
                      "desen satir sonuna uyarlanmiyor — CRLF dosyada mutasyon "
                      "sessizce uygulanmaz (D-370)")

    def test_UYARLAMA_CRLF_DOSYADA_CALISIYOR(self):
        """Gercek dosya uzerinde: LF'li desen CRLF hâline cevrilebiliyor mu?"""
        import importlib.util as u
        sp = u.spec_from_file_location("m129", BETIK)
        m = u.module_from_spec(sp)
        sp.loader.exec_module(m)
        icerik = NAV.read_bytes()
        desen_lf = b"        current_no_route is None\n"
        self.assertNotIn(desen_lf, icerik,
                         "on kosul: dosya CRLF olmali, yoksa bu test bos")
        bulunan = m._satir_sonuna_uyarla(icerik, desen_lf)
        self.assertIn(bulunan, icerik,
                      "uyarlanan desen dosyada BULUNAMIYOR — M2' yine "
                      "uygulanmayacak")
        self.assertTrue(bulunan.endswith(b"\r\n"))

    def test_YERINE_YAZILAN_da_UYARLANIYOR(self):
        """CRLF dosyaya LF sokulmamali; dosya karisik satir sonlu olmamali."""
        import importlib.util as u
        sp = u.spec_from_file_location("m129b", BETIK)
        m = u.module_from_spec(sp)
        sp.loader.exec_module(m)
        yeni = m._es_satir_sonu(b"        True  # MUTASYON\n",
                                b"        current_no_route is None\r\n")
        self.assertTrue(yeni.endswith(b"\r\n"),
                        "yerine yazilan metin LF kaliyor — CRLF dosyaya LF "
                        "sokar, dosya KARISIK satir sonlu olur")


class UygulanmayanMutasyonGECTI_DEGIL(unittest.TestCase):
    def test_EXIT_KODU_UYGULANMAYANI_BILDIRIYOR(self):
        self.assertIn("uygulanmayan", KOD,
                      "uygulanmayan mutasyon izlenmiyor")
        self.assertIn("return 1", KOD,
                      "uygulanmayan mutasyon oldugunda exit 1 donmuyor — "
                      "cikis kodunu okuyan kapi BASARI sanar (D-370)")

    def test_MUTASYON_exit_bagi_kaldirilinca_DUSER(self):
        mutant = KOD.replace("uygulanmayan.append(", "_atlandi(", 1)
        self.assertNotEqual(KOD, mutant, "mutasyon uygulanamadi")
        self.assertNotIn("uygulanmayan.append(", mutant,
                         "izleme kaldirildigi hâlde kapi gormuyor — BOS KAPI")

    def test_UYARI_METNI_OLCULEMEDI_diyor(self):
        self.assertIn("OLCULMEDI", KAYNAK,
                      "uygulanmayan mutasyonun OLCULMEDIGI acikca yazilmali; "
                      "'dusmedi' ile karistirilmamali")


if __name__ == "__main__":
    unittest.main()
