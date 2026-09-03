"""D-416 — YARIŞMA ADI KAPISI: ad şartname kapağından okunur, ezberden yazılmaz.

NEDEN (ölçülen kusur): `FDR/TAKIM_PROMPT.md` takım üyelerine gidecek bir belgedir
ve yarışmanın adını **"TEKNOFEST 2026 Ulaşımda Üretken Yapay Zekâ"** diye yazıyordu.
Doğrusu şartnamenin kendi kapağındadır:

    İLERİ OTONOM SİSTEMLER TASARIM VE OPERASYON YARIŞMASI ŞARTNAMESİ 2026

Kusuru kullanıcı yakaladı, ölçüm yakalamadı — çünkü hiçbir kapı yarışmanın adına
bakmıyordu. Yanlış ad rapora ya da takım yazışmasına sızarsa hakem önünde
takımın şartnameyi okumadığı izlenimi doğar; ayrıca FDR kapağı bu adı taşır.

Kapı, adı **ezberlemez** — şartname metninden okur. Şartname değişirse kapı da
değişir; iddia ile kaynak aynı yerden gelir.

  T1  şartname kapağı gerçekten bu adı taşıyor (kapının kendi dayanağı)
  T2  hiçbir belge yanlış adı ("Üretken Yapay Zekâ" ailesi) taşımıyor
  T3  takım prompt'u ve FDR kapağı DOĞRU adı taşıyor (ad sessizce düşmedi)
"""

import re
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
SARTNAME = KOK / "results" / "sartname_bosluk" / "sartname_metin.txt"

# Sartname kapagi satirlari boluyor; bosluk/satir sonu farkina bakmadan aranir.
AD_PARCALARI = ("İLERİ OTONOM", "SİSTEMLER TASARIM VE", "OPERASYON YARIŞMASI")

# Yanlis ad ailesi. "Uretken yapay zeka" bu yarismanin adi DEGILDIR.
YANLIS = re.compile(r"[ÜU]retken\s+[Yy]apay\s+[Zz]ek", re.IGNORECASE)

# Yanlis adi BILEREK alintilayan satir bu isareti tasir (kusur anlatimi).
MUAF_ISARET = "<!-- ad-kapisi-muaf -->"

# Adin gecmesi BEKLENEN belgeler (ad sessizce silinmesin diye)
AD_TASIYANLAR = (
    KOK / "FDR" / "TAKIM_PROMPT.md",
    KOK / "FDR" / "README.md",
)

# Taranan belgeler: repo kokundeki ve FDR altindaki markdown'lar.
# Sartname metninin KENDISI ve ham cikarimlar haric (kaynak metin degismez).
def _belgeler():
    for p in sorted(KOK.glob("*.md")):
        yield p
    for p in sorted((KOK / "FDR").glob("*.md")):
        yield p


class SartnameDayanagi(unittest.TestCase):
    def test_T1_kapak_adi_sartnamede(self):
        metin = SARTNAME.read_text(encoding="utf-8", errors="replace")
        bas = metin[:4000]          # kapak ilk sayfadadir
        for parca in AD_PARCALARI:
            with self.subTest(parca=parca):
                self.assertIn(parca, bas,
                              "şartname kapağı değişmiş olabilir — adı yeniden oku")


class AdKapisi(unittest.TestCase):
    def test_T2_hicbir_belge_yanlis_adi_tasimiyor(self):
        hatali = []
        for p in _belgeler():
            for i, satir in enumerate(
                    p.read_text(encoding="utf-8").splitlines(), 1):
                # Kusuru ANLATAN satirlar muaf — ama muafiyet tesadufi
                # olmasin diye ACIK BIR ISARET ister. Isareti koyan, yanlis
                # adi bilerek alintiladigini beyan etmis olur.
                if MUAF_ISARET in satir:
                    continue
                if YANLIS.search(satir):
                    hatali.append(f"{p.name}:{i}  {satir.strip()[:110]}")
        self.assertEqual(
            [], hatali,
            "Yarışmanın adı 'İleri Otonom Sistemler Tasarım ve Operasyon "
            "Yarışması'dır (şartname kapağı); 'Üretken Yapay Zekâ' DEĞİLDİR")

    def test_T3_dogru_ad_belgelerde_duruyor(self):
        for p in AD_TASIYANLAR:
            with self.subTest(dosya=p.name):
                metin = p.read_text(encoding="utf-8")
                self.assertRegex(
                    metin,
                    r"İleri\s+Otonom\s+Sistemler\s+Tasarım\s+ve\s+Operasyon\s+Yarışması",
                    f"{p.name} yarışmanın doğru adını taşımıyor")


if __name__ == "__main__":
    unittest.main()
