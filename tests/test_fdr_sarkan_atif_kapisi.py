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


# ── T214-B (10 Eylül) · KOD DOSYA:SATIR ATIF KAPISI ─────────────────────────
# NEDEN (ölçülen kusur): T213-B `ika_nav.py` ve `karar_sozlesmesi.py`'ye satır ekledi; FDR'deki T217
# tabloları (§3.3.1.3.3/§3.3.1.3.4) ve sabit tabloları eski satırları göstermeye devam etti
# (ör. `ika_nav.py:437 ika_gorevi` → tanım 477'de; `karar_sozlesmesi.py:2112` MAVLINK tavanı → 2126).
# Bir hakem `dosya:satır`ı açınca başka bir şey bulurdu. Kural: atıf bir TANIMLAYICI taşıyorsa
# (`dosya.py:N ad` ya da hemen önündeki `ad` + `dosya.py:N`) o ad kaynağın [N−3, M+3] satırlarında
# geçmelidir. ~~Üstü çizili~~ atıf tarihsel kayıttır (bakılmaz); tanımlayıcısız atıf ölçülemez (atlanır).
# Zorlanan dosyalar T214-B'de tazelenenlerdir; diğerleri (ör. `comms/yks_gui.py` — T224 dalında
# tazeleniyor) tazelendikçe `KOD_ATIF_DOSYALARI`'na eklenir.
KOD_ATIF_DOSYALARI = {
    "ika_nav.py": KOK / "simulation" / "scripts" / "ika_nav.py",
    "karar_sozlesmesi.py": KOK / "codes" / "karar_sozlesmesi.py",
}
KOD_ATIF_PAYI = 3
_TIK = re.compile(r"`([^`\n]+)`")
_CIZILI = re.compile(r"~~.*?~~")
_KOD_ATIF = re.compile(r"^(?:(?:[\w.-]+/)*([\w.-]+\.py))?:(\d+)(?:\s*[-–]\s*(\d+))?(?:\s+([A-Za-z_][\w.]*))?$")
_DOSYA_ADI = re.compile(r"(?:[\w.-]+/)*([\w.-]+\.py)\b")
_ONCEKI_AD = re.compile(r"^([A-Za-z_][\w.]*)(?:\s*=.*)?$")
_AYRAC = re.compile(r"^[\s,(;]*$")


def kod_atif_ihlalleri(metin: str, kaynaklar: dict, pay: int = KOD_ATIF_PAYI):
    """`dosya.py:N[-M] ad` (ya da `ad` hemen önde, arada yalnız `,` `(` `;` boşluk) atıflarında `ad`
    (noktalıysa son parçası) kaynağın [N−pay, M+pay] satırlarında geçmeli. Devam atıfı `:N` aynı
    hücredeki son dosyaya bağlanır. SAF: `kaynaklar` = {dosya_adı: satır listesi}. Döner: ihlaller."""
    ihlal = []
    for no, satir in enumerate(metin.splitlines(), 1):
        temiz = _CIZILI.sub(" ", satir)
        hucreler = temiz.split("|") if temiz.lstrip().startswith("|") else [temiz]
        for h in hucreler:
            son_dosya, onceki_ad, onceki_bitis = None, None, 0
            for mt in _TIK.finditer(h):
                ic = mt.group(1).strip()
                m = _KOD_ATIF.match(ic)
                if m and (m.group(1) or son_dosya):
                    dosya = m.group(1) or son_dosya
                    son_dosya = dosya
                    ad = m.group(4)
                    if ad is None and onceki_ad and _AYRAC.match(h[onceki_bitis:mt.start()]):
                        ad = onceki_ad
                    if ad and dosya in kaynaklar:
                        n1, n2 = int(m.group(2)), int(m.group(3) or m.group(2))
                        src = kaynaklar[dosya]
                        pencere = src[max(0, n1 - 1 - pay):min(len(src), n2 + pay)]
                        if not any(ad.split(".")[-1] in s for s in pencere):
                            ihlal.append((no, f"{dosya}:{m.group(2)}", ad, satir.strip()[:90]))
                    onceki_ad, onceki_bitis = None, mt.end()
                    continue
                md = _DOSYA_ADI.search(ic)
                if md:
                    son_dosya = md.group(1)
                ma = _ONCEKI_AD.match(ic)
                onceki_ad = ma.group(1) if ma else None
                onceki_bitis = mt.end()
    return ihlal


def _kod_kaynaklari():
    return {ad: p.read_text(encoding="utf-8").splitlines() for ad, p in KOD_ATIF_DOSYALARI.items()}


class KodSatirAtiflari(unittest.TestCase):
    def test_T4_fdr_kod_atiflari_tanimlayiciyla_es(self):
        kaynaklar = _kod_kaynaklari()
        hatali, sayilan = [], 0
        for p in sorted(FDR.glob("*.md")):
            metin = p.read_text(encoding="utf-8")
            sayilan += sum(metin.count(f"{d}:") for d in kaynaklar)
            for no, atif, ad, satir in kod_atif_ihlalleri(metin, kaynaklar):
                hatali.append(f"{p.name}:{no}  `{atif}` ±{KOD_ATIF_PAYI} satırda `{ad}` YOK  ->  {satir}")
        self.assertGreater(sayilan, 20, "atıf sayımı boş — kapı hiçbir şeye bakmıyor")
        self.assertEqual([], hatali, "FDR kod atfı bayat (kaynak satır kaydı):\n  " + "\n  ".join(hatali))

    def test_T4a_bayat_atif_YAKALANIR(self):
        kay = {"ornek.py": ["x = 1", "", "", "", "", "", "", "", "def hedef():", "    pass"]}
        self.assertEqual(1, len(kod_atif_ihlalleri("bkz. `ornek.py:1 hedef`", kay)))
        self.assertEqual(1, len(kod_atif_ihlalleri("(`hedef`, `ornek.py:1`)", kay)))       # önceki ad
        self.assertEqual(1, len(kod_atif_ihlalleri("`ornek.py:2 x` ve `:1 hedef`", kay)))   # devam atıfı

    def test_T4b_dogru_atif_ve_pay_YAKALANMAZ(self):
        kay = {"ornek.py": ["x = 1", "", "", "", "", "", "", "", "def hedef():", "    pass"]}
        for metin in ("`ornek.py:9 hedef`", "`ornek.py:6 hedef`", "`ornek.py:12 hedef`",
                      "(`hedef`, `ornek.py:9`)", "`x = 1` (`ornek.py:1`)", "`ornek.py:1-2 x`"):
            with self.subTest(metin=metin):
                self.assertEqual([], kod_atif_ihlalleri(metin, kay))

    def test_T4c_cizili_ve_tanimlayicisiz_atif_BAKILMAZ(self):
        kay = {"ornek.py": ["x = 1"] + [""] * 20 + ["def hedef():"]}
        self.assertEqual([], kod_atif_ihlalleri("~~`ornek.py:1 hedef`~~ `ornek.py:22 hedef`", kay))
        self.assertEqual([], kod_atif_ihlalleri("sürücü sağlığı (`ornek.py:1`)", kay))
        self.assertEqual([], kod_atif_ihlalleri("`baska.py:1 hedef`", kay))          # zorlanmayan dosya


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
