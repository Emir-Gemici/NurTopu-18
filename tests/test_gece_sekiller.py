"""G5 (7 Eylül gecesi) — FDR ŞEKİL NÖBETÇİSİ: SVG'ler tabloyla birebir, şema isimsiz.

NEDEN: `Y-6-M06` genel uygunluk dağılımının **görsel** sunumunu, `Y-2.1-M01`
rol bazlı ve **isimsiz** organizasyon şemasını ister. Görsel bir kez çizilip
unutulursa tablo değişir, grafik eskir; şemaya bir isim sızarsa yönerge
ihlal edilir (Y-2.1-M02). Bu kapı üçünü de her koşuda ölçer.

Tablo ile karşılaştırma **bağımsızdır**: bu dosya §6.6.2/§6.6.3 tablolarını
kendi regex'iyle okur (`scripts/fdr_sekil_uret.py`'nin okuyucusunu ithal
ETMEZ) — üreteç yanlış okusa bile kapı ayrı gözle bakar.

  T1  üç SVG var, XML olarak ayrışıyor, kök <svg>, viewBox var, genişlik 900
  T2  pasta: dilim etiketleri/sayıları/oranları §6.6.2 tablosuyla BİREBİR
      (küme eşitliği — eksik ya da fazla dilim yok); dilim toplamı tablonun
      kendi 'toplam' hücresine eşit
  T3  pasta GEOMETRİSİ: her dilimin yay açısı 360·satır/toplam (±0,5°) —
      sayı etiketi doğru ama dilim yanlış çizilmiş olamaz
  T4  yöntem çubukları §6.6.3 ile birebir; çubuk genişliği = satır × px/satır
  T5  organizasyon.svg: R1…R8 sekizi de geçiyor; "Halil|Yunus|Emir" GEÇMİYOR
      (büyük/küçük harf duyarsız); R2/R5 uçuş anı eşzamanlılık notu var
  T6  SVG'lerde yönergenin yasakladığı isimler hiçbirinde yok (üçü birden)
"""

import math
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
FDR = KOK / "FDR"
SEKILLER = FDR / "sekiller"
BOLUM_6 = FDR / "BOLUM_6_GEREKSINIM_IZLENEBILIRLIGI.md"
SVG_NS = "{http://www.w3.org/2000/svg}"
SVGLER = ("uygunluk_pasta.svg", "uygunluk_yontem.svg", "organizasyon.svg")

# Yönergenin yasakladığı kişisel veri: takım üyesi adları (Y-2.1-M02).
YASAK_ISIM = re.compile(r"Halil|Yunus|Emir", re.I)


def _b6() -> str:
    return BOLUM_6.read_text(encoding="utf-8").replace("\r\n", "\n")


def _kesit(metin: str, bas: str, son: str) -> str:
    i = metin.index(bas)
    return metin[i:metin.index(son, i)]


def tablo_662():
    """§6.6.2 → ({durum: (satır, oran)}, toplam) — bu dosyanın KENDİ okuyucusu."""
    kesit = _kesit(_b6(), "### 6.6.2", "### 6.6.3")
    satirlar, toplam = {}, None
    for s in kesit.splitlines():
        m = re.match(r"^\|\s*\*\*([^*|]+?)\*\*\s*\|\s*(\*\*)?(\d+)(\*\*)?\s*\|\s*(\*\*)?(%[\d,]+)", s)
        if not m:
            continue
        ad, n, oran = m.group(1).strip(), int(m.group(3)), m.group(6)
        if ad == "toplam":
            toplam = n
        else:
            satirlar[ad] = (n, oran)
    return satirlar, toplam


def tablo_663():
    """§6.6.3 → ({yöntem: (satır, oran)}, payda)."""
    kesit = _kesit(_b6(), "### 6.6.3", "### 6.6.4")
    satirlar = {}
    for s in kesit.splitlines():
        m = re.match(r"^\|\s*([^*|]+?)\s*\|\s*(\d+)\s*\|\s*(%[\d,]+)\s*\|", s)
        if m and m.group(1).strip() != "yöntem":
            satirlar[m.group(1).strip()] = (int(m.group(2)), m.group(3))
    mp = re.search(r"\|\s*(\d+)\s+satırın oranı\s*\|", kesit)
    return satirlar, (int(mp.group(1)) if mp else None)


def _svg(ad: str) -> ET.Element:
    return ET.parse(SEKILLER / ad).getroot()


def _metinler(kok: ET.Element) -> str:
    return "\n".join((t.text or "") for t in kok.iter(SVG_NS + "text"))


def _aci(cx: float, cy: float, x: float, y: float) -> float:
    return math.degrees(math.atan2(y - cy, x - cx)) % 360.0


class T1_UcSvgVarVeGecerli(unittest.TestCase):
    def test_uc_svg_var_xml_gecerli_900px(self):
        for ad in SVGLER:
            with self.subTest(svg=ad):
                yol = SEKILLER / ad
                self.assertTrue(yol.is_file(), f"yok: {yol}")
                kok = ET.parse(yol).getroot()          # XML geçersizse burada patlar
                self.assertEqual(SVG_NS + "svg", kok.tag)
                self.assertIn("viewBox", kok.attrib)
                self.assertEqual("900", kok.get("width"))
                self.assertTrue(kok.get("viewBox", "").startswith("0 0 900 "))


class T2_PastaTabloylaBirebir(unittest.TestCase):
    def setUp(self):
        self.tablo, self.toplam = tablo_662()
        self.assertGreaterEqual(len(self.tablo), 2, "§6.6.2 tablosu okunamadı")
        self.assertIsNotNone(self.toplam, "§6.6.2 'toplam' hücresi okunamadı")
        self.kok = _svg("uygunluk_pasta.svg")
        self.grup = self.kok.find(f".//{SVG_NS}g[@id='dilimler']")
        self.assertIsNotNone(self.grup, "id='dilimler' grubu yok")
        self.dilimler = list(self.grup.iter(SVG_NS + "path"))

    def test_dilim_kumesi_tabloya_esit(self):
        svg = {d.get("data-durum"): (int(d.get("data-satir")), d.get("data-oran")) for d in self.dilimler}
        self.assertEqual(self.tablo, svg)      # eksik/fazla dilim, yanlış sayı, yanlış oran → düşer

    def test_dilim_toplami_tablonun_toplam_hucresi(self):
        self.assertEqual(self.toplam, sum(int(d.get("data-satir")) for d in self.dilimler))
        self.assertEqual(str(self.toplam), self.grup.get("data-toplam"))

    def test_gorunur_metin_sayilari_tasiyor(self):
        """data-* doğru ama gözle görünen etiket başka olamaz: sayı ve oran <text> içinde."""
        metin = _metinler(self.kok)
        for ad, (n, oran) in self.tablo.items():
            with self.subTest(durum=ad):
                self.assertIn(ad, metin)
                self.assertRegex(metin, rf"\b{n} \({re.escape(oran)}\)")
        self.assertIn("§6.6.2", metin)          # kaynak alt yazısı


class T3_PastaGeometrisi(unittest.TestCase):
    """Yay açısı sayıyla tutmalı; sadece etiketin doğru olması yetmez."""

    def test_yay_acilari_satir_oraniyla_tutuyor(self):
        tablo, toplam = tablo_662()
        kok = _svg("uygunluk_pasta.svg")
        grup = kok.find(f".//{SVG_NS}g[@id='dilimler']")
        cx, cy = float(grup.get("data-cx")), float(grup.get("data-cy"))
        yay = re.compile(r"M\s+([-\d.]+)\s+([-\d.]+)\s+A\s+[-\d.]+\s+[-\d.]+\s+0\s+([01])\s+1\s+([-\d.]+)\s+([-\d.]+)")
        bas_beklenen = 270.0                    # 12 yönü; dilimler saat yönünde birbirini izler
        for d in grup.iter(SVG_NS + "path"):
            ad, n = d.get("data-durum"), int(d.get("data-satir"))
            m = yay.match(d.get("d"))
            self.assertIsNotNone(m, f"{ad}: dış yay okunamadı")
            x0, y0, buyuk, x1, y1 = (float(m.group(1)), float(m.group(2)), int(m.group(3)),
                                     float(m.group(4)), float(m.group(5)))
            a0, a1 = _aci(cx, cy, x0, y0), _aci(cx, cy, x1, y1)
            span = (a1 - a0) % 360.0
            beklenen = 360.0 * n / toplam
            with self.subTest(durum=ad):
                self.assertAlmostEqual(beklenen, span, delta=0.5)
                self.assertEqual(1 if beklenen > 180 else 0, buyuk, "large-arc bayrağı")
                self.assertAlmostEqual(bas_beklenen, a0, delta=0.5, msg="dilimler ardışık değil")
            bas_beklenen = (bas_beklenen + beklenen) % 360.0
        self.assertEqual(set(tablo), {d.get("data-durum") for d in grup.iter(SVG_NS + "path")})


class T4_YontemCubuklari(unittest.TestCase):
    def test_cubuklar_tabloyla_birebir_ve_genislik_orantili(self):
        tablo, payda = tablo_663()
        self.assertGreaterEqual(len(tablo), 2, "§6.6.3 tablosu okunamadı")
        self.assertIsNotNone(payda)
        kok = _svg("uygunluk_yontem.svg")
        grup = kok.find(f".//{SVG_NS}g[@id='cubuklar']")
        self.assertIsNotNone(grup)
        self.assertEqual(str(payda), grup.get("data-satir-toplam"))
        px = float(grup.get("data-px-per-satir"))
        cubuklar = list(grup.iter(SVG_NS + "rect"))
        svg = {c.get("data-yontem"): (int(c.get("data-satir")), c.get("data-oran")) for c in cubuklar}
        self.assertEqual(tablo, svg)
        for c in cubuklar:
            with self.subTest(yontem=c.get("data-yontem")):
                self.assertAlmostEqual(px * int(c.get("data-satir")), float(c.get("width")), places=2)
        metin = _metinler(kok)
        for ad, (n, oran) in tablo.items():
            self.assertIn(f"{n} satır · {oran}", metin)
        self.assertIn("§6.6.3", metin)


class T5_OrganizasyonSemasi(unittest.TestCase):
    def setUp(self):
        self.metin = _metinler(_svg("organizasyon.svg"))

    def test_sekiz_rol_kodu_geciyor(self):
        roller = set(re.findall(r"\bR([1-8])\b", self.metin))
        self.assertEqual({str(i) for i in range(1, 9)}, roller)

    def test_isim_gecmiyor(self):
        self.assertIsNone(YASAK_ISIM.search(self.metin), "şemada isim var")

    def test_r2_r5_ucus_ani_eszamanlilik_notu_var(self):
        satirlar = [s for s in self.metin.splitlines() if re.search(r"e[şs]zamanl", s, re.I)]
        self.assertTrue(any("R2" in s and "R5" in s for s in satirlar),
                        "R2 ve R5'i birlikte anan eşzamanlılık notu yok")

    def test_rol_bazli_notu_ve_kaynak_var(self):
        self.assertIn("isim içermez", self.metin)
        self.assertIn("§2.1", self.metin)


class T6_HicbirSvgdeIsimYok(unittest.TestCase):
    def test_ham_dosyada_da_isim_yok(self):
        """<text> dışına (yorum, title, attribute) sızan isim de yakalanır."""
        for ad in SVGLER:
            with self.subTest(svg=ad):
                ham = (SEKILLER / ad).read_text(encoding="utf-8")
                self.assertIsNone(YASAK_ISIM.search(ham))


if __name__ == "__main__":
    unittest.main()
