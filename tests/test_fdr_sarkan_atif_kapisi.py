"""D-420 — SARKAN İÇ ATIF KAPISI: rapor kendi içinde var olmayan bölüme atıf yapmaz.

NEDEN (ölçülen kusur, 4 Eylül): FDR bölümleri resmî yönergenin iskeletine
taşınırken başlıklar **yeniden numaralandı** (eski §3.5.x → §3.3.4.2.x). Ama
metin içindeki çapraz atıflar eski numaraları göstermeye devam etti. Bir okur
— ya da **hakem** — "§3.5.2'deki üç sütunlu tabloda" cümlesini takip edip
hiçbir şey bulamazdı. Ölçüm: 32 sarkan atıf, 23'ü Bölüm 3'te.

Kusur içerik kaybı değildi (hiçbir `D-NNN` ve hiçbir dosya yolu kaybolmamıştı);
**yönlendirme** kaybıydı. Bu kapı onu ölçer.

AYIRT ETMEK ZORUNDA OLDUĞU ÜÇ ŞEY — kapının tamamı bu ayrımdadır:

  1. **Kendi bölümüne atıf** (§3.2.1 → Bölüm 3 içindeki bir başlık) → hedef
     başlık VAR OLMALI. Yoksa sarkan.
  2. **Başka belgeye atıf** (`şartname §5.3.2`, `REVIEW_LOG.md D-408 §3`,
     `CONTRACTS.md §7.4`) → bu kapının konusu DEĞİL. Aynı satırda belge adı
     ya da kayıt kimliği geçiyorsa atıf dışarıyadır.
  3. **Tarihsel etiket** — taşıma haritalarının "eski numara" sütunu. Orada
     `3.5.1` bir işaretçi değil, bir KAYITTIR. Bu yüzden o sütundan `§`
     işareti KALDIRILDI (4 Eylül): işaretsiz numara işaretçi gibi okunmaz.
     Kapı `§` arar; işaretsiz tarihsel numarayı görmez. Ayrım bilerek
     **biçimle** yapıldı, ad listesiyle değil — liste bakımsız kalır, biçim
     kalmaz.

  T1  hiçbir FDR bölümü kendi içinde var olmayan bir alt başlığa `§` ile
      atıf yapmıyor
  T2  taşıma haritalarının eski-numara sütununda `§` işareti YOK
      (aksi hâlde T1 sonsuza dek yanlış alarm üretir)
  T3  kural birim düzeyinde de sınanır: sentetik metinlerle hem sarkan atıf
      YAKALANIR hem de başka belgeye atıf YAKALANMAZ
"""

import re
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
FDR = KOK / "FDR"

BASLIK = re.compile(r"^#{2,6}\s+(?:Bölüm\s+)?(\d+(?:\.\d+)*)", re.M)
ATIF = re.compile(r"§(\d+(?:\.\d+)*)")

# Satırda bunlardan biri geçiyorsa atıf BAŞKA BELGEYE gider; bu kapının konusu
# değildir. Biçimsel ölçüt: bir belge adı, bir kayıt kimliği ya da şartname/
# yönerge sözcüğü.
DIS_BELGE = re.compile(
    r"D-\d{2,4}|REVIEW_LOG|CONTRACTS|AGENTS\.md|CLAUDE\.md|TASK_QUEUE|"
    r"şartname|Şartname|yönerge|Yönerge|SAHA_[A-Z_]+|JETSON_[A-Z_]+|"
    r"ddr_requirements|\.md\b|Bölüm [1-7]\b")


def sarkan_atiflar(metin: str, bolum_no: int):
    """Metnin KENDİ bölümüne ait, hedefi olmayan `§` atıfları.

    SAF fonksiyon — dosya sistemi yok — ki aynı kural hem sentetik birim
    testlerde hem gerçek belgelerde koşsun. İki kopya kural yazılmaz.
    """
    basliklar = set(BASLIK.findall(metin))
    sarkan = []
    for i, satir in enumerate(metin.splitlines(), 1):
        if DIS_BELGE.search(satir):
            continue
        for a in ATIF.findall(satir):
            if a.split(".")[0] != str(bolum_no):
                continue          # başka bölüme atıf — o bölümün kapısı bakar
            if a == str(bolum_no):
                continue          # bölümün kendisine atıf, alt başlık değil
            if a not in basliklar:
                sarkan.append((i, a, satir.strip()[:90]))
    return sarkan


def _bolumler():
    for p in sorted(FDR.glob("BOLUM_[1-7]_*.md")):
        m = re.match(r"BOLUM_(\d)_", p.name)
        if m:
            yield p, int(m.group(1))


class GercekBelgeler(unittest.TestCase):
    def test_T1_hicbir_bolum_var_olmayan_alt_basliga_atif_yapmiyor(self):
        hatali = []
        for p, n in _bolumler():
            for i, a, satir in sarkan_atiflar(
                    p.read_text(encoding="utf-8"), n):
                hatali.append(f"{p.name}:{i}  §{a} hedefi YOK  ->  {satir}")
        self.assertEqual(
            [], hatali,
            "FDR içinde var olmayan bölüme atıf var — yeniden numaralandırma "
            "sonrası çapraz atıflar güncellenmemiş:\n  " + "\n  ".join(hatali))

    def test_T2_tasima_haritalarinda_eski_numara_isaretsiz(self):
        """Harita sol sütunu TARİHSEL KAYITTIR; `§` onu işaretçi gibi gösterir."""
        hatali = []
        for p, _ in _bolumler():
            satirlar = p.read_text(encoding="utf-8").splitlines()
            for i, l in enumerate(satirlar, 1):
                duz = l.lstrip().lstrip(">").strip()
                if not duz.startswith("|"):
                    continue
                parcalar = duz.split("|")
                if len(parcalar) < 3:
                    continue
                ilk = parcalar[1]
                # Harita satırı: ilk hücre yalnız numara(lar) taşıyor ve
                # ikinci hücre de numara taşıyor (eski -> yeni eşlemesi).
                if (re.fullmatch(r"[\s§\d.…·/a-z,-]+", ilk)
                        and "§" in ilk and ATIF.search(parcalar[2] or "")):
                    hatali.append(f"{p.name}:{i}  {duz[:90]}")
        self.assertEqual(
            [], hatali,
            "taşıma haritasının eski-numara sütununda `§` var — tarihsel "
            "etiket işaretçi gibi okunuyor:\n  " + "\n  ".join(hatali))


class KuralBirimTestleri(unittest.TestCase):
    """Kural sentetik metinlerle iki yönde de sınanır (boş kapı olmasın)."""

    def test_T3a_sarkan_atif_YAKALANIR(self):
        metin = ("## 3.1 Var olan\n\nBurada §3.9.2 diye bir yere atıf var.\n")
        s = sarkan_atiflar(metin, 3)
        self.assertEqual(1, len(s), s)
        self.assertEqual("3.9.2", s[0][1])

    def test_T3b_var_olan_hedef_YAKALANMAZ(self):
        metin = ("## 3.1 Var olan\n### 3.1.2 Alt\n\nBkz. §3.1.2.\n")
        self.assertEqual([], sarkan_atiflar(metin, 3))

    def test_T3c_baska_belgeye_atif_YAKALANMAZ(self):
        for satir in ("şartname §5.3.2 der ki",
                      "`REVIEW_LOG.md` D-408 §3 kaydı",
                      "`CONTRACTS.md` §7.4 sözleşmesi",
                      "yönerge §3.9.9 böyle diyor"):
            with self.subTest(satir=satir):
                self.assertEqual([], sarkan_atiflar("## 3.1 X\n" + satir, 3))

    def test_T3d_isaretsiz_tarihsel_numara_YAKALANMAZ(self):
        """Harita sütunundaki `3.5.1` (işaretsiz) atıf sayılmaz."""
        metin = "## 3.1 X\n\n| 3.5.1 … 3.5.5 | §3.1 | kapı tablosu |\n"
        self.assertEqual([], sarkan_atiflar(metin, 3))

    def test_T3e_bolumun_KENDISINE_atif_YAKALANMAZ(self):
        self.assertEqual([], sarkan_atiflar("## 3.1 X\n\nBu §3 içinde.\n", 3))


if __name__ == "__main__":
    unittest.main()
