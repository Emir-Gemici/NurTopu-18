"""NÖBETÇİ — İHA renk kodlu bağlantı şeması (Y-3.3.1-M01; gece ön kaydı G6).

Ön kayıt (results/gece_20260907/ON_KAYIT.md, G6 satırı): "her bağlantı D-kaydı
ya da param satırıyla KAYNAKLI; kaynaksız bağlantı çizilmez; ölçülmeyen
'DOĞRULANACAK' etiketiyle; İKA şeması çizilmez". Bu dosya o kapıyı ÖLÇER:

  T1  SVG geçerli XML, kök <svg>, genişlik 1100
  T2  legend'de altı zorunlu tür (güç, PWM, UART, I2C, CSI, RC) ayrı renkle var
  T3  çizilen her hat legend'deki bir rengi kullanır (legend dışı renk yok)
  T4  kaynaklar.md'de her hat satırında en az bir "D-4xx" / "param:" / "§" atfı
  T5  SVG'deki hat kümesi == md'deki hat kümesi (kaynaksız çizim / çizimsiz kaynak yok)
  T6  kesik çizgi <=> durum "DOĞRULANACAK" (ölçülmemiş hat düz çizilemez)
  T7  atıf yapılan her D-kaydı REVIEW_LOG.md'de VAR; her "param:AD,DEĞER"
      20260906 dökümünde BİREBİR satır
  T8  isim yok: commit yazarının adı geçmez; kişi anlatımı rol bazlıdır
  T9  drift kilidi: diskteki iki dosya üreticinin çıktısıyla bayt-eş
  T10 kural fonksiyonları sentetik girdide de yakalar (mutasyon: legend dışı
      renk, kaynaksız satır, kesik/düz uyumsuzluğu)

Bu dosya SVG'yi güzel bulmaz; yalnız sayılabilir olanı sayar. Okunurluk
mimarın gözüyle denetlenir.
"""

from __future__ import annotations

import importlib.util as _u
import re
import subprocess
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
SEKILLER = KOK / "FDR" / "sekiller"
SVG = SEKILLER / "iha_baglanti.svg"
MD = SEKILLER / "iha_baglanti_kaynaklar.md"
BETIK = KOK / "scripts" / "fdr_iha_baglanti_svg.py"
REVIEW_LOG = KOK / "REVIEW_LOG.md"
DOKUM = KOK / "config" / "pixhawk" / "arducopter_fda_20260906.param"
BOLUM_3 = KOK / "FDR" / "BOLUM_3_SISTEM_SPESIFIKASYONLARI.md"

SVG_NS = "{http://www.w3.org/2000/svg}"
ZORUNLU_TURLER = {"guc", "pwm", "uart", "i2c", "csi", "rc"}
ATIF = re.compile(r"D-4\d\d|param:|§")
D_KAYIT = re.compile(r"\bD-(\d{3})\b")
PARAM_ATIF = re.compile(r"param:([A-Z0-9_]+),(-?[0-9.]+)")
HAT_SATIRI = re.compile(r"^\|\s*(H\d{2})\s*\|")


def _oku(p: Path) -> str:
    return p.read_text(encoding="utf-8").replace("\r\n", "\n")


# ── Saf kural fonksiyonları (sentetik girdide de koşar) ──────────────────────
def legend_renkleri(kok: ET.Element) -> dict:
    """legend grubundaki data-hat -> stroke."""
    leg = None
    for g in kok.iter(SVG_NS + "g"):
        if g.get("id") == "legend":
            leg = g
            break
    if leg is None:
        return {}
    out = {}
    for el in leg.iter():
        if el.get("data-hat") and el.get("stroke"):
            out[el.get("data-hat")] = el.get("stroke")
    return out


def hatlar(kok: ET.Element) -> list:
    """class='hat' elemanları: (id, tür, stroke, kesik_mi)."""
    out = []
    for el in kok.iter():
        if "hat" in (el.get("class") or "").split():
            out.append((el.get("data-hat"), el.get("data-tur"), el.get("stroke"),
                        el.get("stroke-dasharray") is not None))
    return out


def legend_disi_renkler(kok: ET.Element) -> list:
    renkler = set(legend_renkleri(kok).values())
    return [(i, r) for i, _, r, _ in hatlar(kok) if r not in renkler]


def md_hat_satirlari(metin: str) -> dict:
    """md tablosundan hat id -> (durum, kaynak) hücreleri."""
    out = {}
    for satir in metin.splitlines():
        m = HAT_SATIRI.match(satir)
        if not m:
            continue
        hucreler = [h.strip() for h in satir.strip().strip("|").split("|")]
        # | hat | ad | nereden → nereye | tür | durum | kaynak |
        if len(hucreler) < 6:
            out[m.group(1)] = ("", "")
        else:
            out[m.group(1)] = (hucreler[4], hucreler[5])
    return out


def kaynaksiz_satirlar(metin: str) -> list:
    return [hid for hid, (_, kaynak) in md_hat_satirlari(metin).items() if not ATIF.search(kaynak)]


def kesik_durum_uyumsuz(kok: ET.Element, metin: str) -> list:
    """Kesik çizilen hat DOĞRULANACAK olmalı; DOĞRULANACAK hat kesik olmalı."""
    durumlar = {hid: d for hid, (d, _) in md_hat_satirlari(metin).items()}
    kotu = []
    for hid, _, _, kesik in hatlar(kok):
        d = durumlar.get(hid, "")
        if kesik != d.startswith("DOĞRULANACAK"):
            kotu.append((hid, kesik, d[:40]))
    return kotu


def _modul():
    sp = _u.spec_from_file_location("fdr_iha_baglanti_svg", BETIK)
    m = _u.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


class Sema(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.svg_metin = _oku(SVG)
        cls.md_metin = _oku(MD)
        cls.kok = ET.fromstring(cls.svg_metin)

    def test_T1_svg_xml_gecerli_1100px(self):
        self.assertEqual(self.kok.tag, SVG_NS + "svg")
        self.assertEqual(self.kok.get("width"), "1100")
        self.assertTrue((self.kok.get("viewBox") or "").startswith("0 0 1100 "))
        self.assertIsNotNone(self.kok.find(SVG_NS + "title"))

    def test_T2_legend_alti_zorunlu_tur_ayri_renk(self):
        leg = legend_renkleri(self.kok)
        eksik = ZORUNLU_TURLER - set(leg)
        self.assertFalse(eksik, f"legend'de eksik tür: {sorted(eksik)}")
        zorunlu_renkler = [leg[t] for t in sorted(ZORUNLU_TURLER)]
        self.assertEqual(len(set(zorunlu_renkler)), len(ZORUNLU_TURLER),
                         f"zorunlu türler ayrı renk olmalı: {leg}")
        self.assertGreaterEqual(len(leg), 6)

    def test_T3_her_hat_legend_renginde(self):
        self.assertGreater(len(hatlar(self.kok)), 0, "hiç hat çizilmemiş")
        self.assertEqual(legend_disi_renkler(self.kok), [])
        leg = legend_renkleri(self.kok)
        for hid, tur, renk, _ in hatlar(self.kok):
            self.assertEqual(leg.get(tur), renk, f"{hid}: data-tur={tur} rengi legend ile uyuşmuyor")

    def test_T4_md_her_hatta_atif(self):
        satirlar = md_hat_satirlari(self.md_metin)
        self.assertGreater(len(satirlar), 0)
        self.assertEqual(kaynaksiz_satirlar(self.md_metin), [])

    def test_T5_svg_md_hat_kumeleri_esit(self):
        svg_ids = {hid for hid, _, _, _ in hatlar(self.kok)}
        md_ids = set(md_hat_satirlari(self.md_metin))
        self.assertEqual(svg_ids, md_ids,
                         f"yalnız SVG'de: {sorted(svg_ids - md_ids)} · yalnız md'de: {sorted(md_ids - svg_ids)}")

    def test_T6_kesik_cizgi_dogrulanacak(self):
        self.assertEqual(kesik_durum_uyumsuz(self.kok, self.md_metin), [])
        # En az bir DOĞRULANACAK hat olmalı: Jetson güç ve TELEM2 sahada ölçülmedi (D-426 §4)
        self.assertTrue(any(k for _, _, _, k in hatlar(self.kok)), "hiç kesik hat yok — ölçülmeyen hatlar düz çizilmiş")

    def test_T7_atiflar_gercek(self):
        mevcut = set(re.findall(r"^### D-(\d{3})\b", _oku(REVIEW_LOG), flags=re.M))
        atifli = set(D_KAYIT.findall(self.md_metin)) | set(D_KAYIT.findall(self.svg_metin))
        self.assertTrue(atifli, "hiç D-kaydı atfı yok")
        yok = sorted(a for a in atifli if a not in mevcut)
        self.assertEqual(yok, [], f"REVIEW_LOG'da olmayan D-kaydına atıf: {yok}")

        dokum = set(s.strip() for s in _oku(DOKUM).splitlines())
        param_atiflari = PARAM_ATIF.findall(self.md_metin)
        self.assertGreater(len(param_atiflari), 0)
        yanlis = [f"{a},{v}" for a, v in param_atiflari if f"{a},{v}" not in dokum]
        self.assertEqual(yanlis, [], f"dökümde birebir olmayan param atfı: {yanlis}")

    def test_T8_isim_yok(self):
        metin = self.md_metin + "\n" + self.svg_metin
        # Kişi anlatımı rol bazlıdır: "Operatör (Ad)" / "pilot: Ad" biçimi yasak.
        self.assertIsNone(re.search(r"(?i)(operat[öo]r|pilot|kaptan)\s*[:(]\s*[A-ZÇĞİÖŞÜ][a-zçğıöşü]+", metin))
        try:
            q = subprocess.run(["git", "log", "-1", "--format=%an"], cwd=KOK,
                               capture_output=True, text=True, timeout=30)
            yazar = q.stdout.strip()
        except OSError:
            yazar = ""
        if not yazar:
            self.skipTest("git yazarı okunamadı")
        for parca in re.split(r"[\s\-_.]+", yazar):
            if len(parca) >= 3:
                self.assertNotRegex(metin, rf"\b{re.escape(parca)}\b", f"isim geçiyor: {parca}")

    def test_T9_drift_kilidi_uretici_ile_ayni(self):
        m = _modul()
        svg, md = m.uret()
        self.assertEqual(svg, self.svg_metin, "iha_baglanti.svg üreticiden sapmış — betiği koş ve commit'le")
        self.assertEqual(md, self.md_metin, "iha_baglanti_kaynaklar.md üreticiden sapmış")

    def test_T9b_bolum3_atif_hedefi_var(self):
        b3 = _oku(BOLUM_3)
        if "sekiller/iha_baglanti.svg" in b3:
            self.assertTrue(SVG.is_file())
            self.assertIn("DOĞRULANACAK", b3[b3.index("sekiller/iha_baglanti.svg"):][:400],
                          "BOLUM_3 şema satırı kesik çizgi anlamını söylemeli")
        self.assertIn("iha_baglanti_kaynaklar.md", self.svg_metin, "SVG kaynak dosyasına atıf yapmalı")


class SentetikMutasyon(unittest.TestCase):
    """Kural fonksiyonları gerçek dosyaya değil kurala bağlıdır (D-370 sınıfı)."""

    SVG = ('<svg xmlns="http://www.w3.org/2000/svg" width="1100" viewBox="0 0 1100 10">'
           '<g id="legend"><line data-hat="guc" stroke="#c62828"/><line data-hat="uart" stroke="#1565c0"/></g>'
           '<polyline class="hat" data-hat="H01" data-tur="guc" stroke="#c62828" points="0,0 1,1"/>'
           '<polyline class="hat" data-hat="H02" data-tur="uart" stroke="#1565c0" points="0,0 1,1" stroke-dasharray="8,5"/>'
           '{ek}</svg>')
    MD = ("| hat | ad | nereden → nereye | tür | durum | kaynak |\n|---|---|---|---|---|---|\n"
          "| H01 | a | b → c | `guc` | ÖLÇÜLDÜ | D-426 §1 |\n"
          "| H02 | a | b → c | `uart` | DOĞRULANACAK — x | param:SERIAL2_BAUD,57 |\n{ek}")

    def test_temiz_gecer(self):
        kok = ET.fromstring(self.SVG.format(ek=""))
        md = self.MD.format(ek="")
        self.assertEqual(legend_disi_renkler(kok), [])
        self.assertEqual(kaynaksiz_satirlar(md), [])
        self.assertEqual(kesik_durum_uyumsuz(kok, md), [])

    def test_legend_disi_renk_yakalanir(self):
        kok = ET.fromstring(self.SVG.format(
            ek='<polyline class="hat" data-hat="H03" data-tur="pwm" stroke="#ff00ff" points="0,0 1,1"/>'))
        self.assertEqual(legend_disi_renkler(kok), [("H03", "#ff00ff")])

    def test_kaynaksiz_satir_yakalanir(self):
        md = self.MD.format(ek="| H03 | a | b → c | `pwm` | ÖLÇÜLDÜ | sahada görüldü |\n")
        self.assertEqual(kaynaksiz_satirlar(md), ["H03"])

    def test_kesik_duz_uyumsuzlugu_yakalanir(self):
        # DOĞRULANACAK hat düz çizilmiş → yakalanır
        svg = self.SVG.format(ek="").replace(' stroke-dasharray="8,5"', "")
        kotu = kesik_durum_uyumsuz(ET.fromstring(svg), self.MD.format(ek=""))
        self.assertEqual([k[0] for k in kotu], ["H02"])
        # Ölçülmüş hat kesik çizilmiş → yakalanır
        svg2 = self.SVG.format(ek="").replace('data-tur="guc" stroke="#c62828" points="0,0 1,1"/>',
                                              'data-tur="guc" stroke="#c62828" points="0,0 1,1" stroke-dasharray="8,5"/>')
        kotu2 = kesik_durum_uyumsuz(ET.fromstring(svg2), self.MD.format(ek=""))
        self.assertIn("H01", [k[0] for k in kotu2])


if __name__ == "__main__":
    unittest.main()
