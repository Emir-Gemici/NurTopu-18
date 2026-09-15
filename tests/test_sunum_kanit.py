"""T259 — SUNUM KANIT KAPISI: slayttaki her sayı kaynağına bağlıdır.

NEDEN (ölçülen risk): Sunum, FDR'nin ölçülmüş çekirdeğinden türetilir. Elle
yazılan bir slaytta iki şey sessizce olur: (1) rapordaki sayı yuvarlanır ya da
uydurulur, (2) `ÖLÇÜLEMEDİ` etiketi düşer ve ölçülmemiş bir şey ölçülmüş gibi
sunulur. Jüri önünde bunun bedeli rapordan büyüktür — söylenen söz geri alınmaz.

Bu kapı `results/sunum_20260913/icerik.json` ve üretilen
`FDR/sunum/sunum_metin.txt` üzerinden çalışır; `pptx` kütüphanesine bağlı
DEĞİLDİR (nöbetçi, üreteçten bağımsız koşmalıdır).

Kapılar:
  K1  şema geçerli (zorunlu alanlar, etiket/kaynak biçimi)
  K2  her `kaynak` gerçek dosya + o satır numarası dosyada var
  K3  madde metnindeki her sayı kaynak dosyada geçiyor  ← uydurma sayı kapısı
  K4  ÖLÇÜLEMEDİ sayısı icerik.json ile sunum_metin.txt'te AYNI (sessiz düşme kapısı)
  K5  [İNSAN DOLDURACAK] yer tutucuları sayılır (uyarı, hata değil)
  K6  mutasyon: (a) bozuk sayı K3'ü düşürür, (b) silinen ÖLÇÜLEMEDİ K4'ü düşürür

Gerçek sunum dosyaları henüz yoksa K1–K5 fixture (`ornek_icerik.json`) üzerinde
koşar; gerçek dosyalar gelince ikisi de denetlenir.

Kullanım:
  python tests/test_sunum_kanit.py
  python tests/test_sunum_kanit.py --icerik <yol> --metin <yol>
  python -m unittest tests.test_sunum_kanit
"""

import argparse
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
ICERIK = KOK / "results" / "sunum_20260913" / "icerik.json"
ORNEK = KOK / "results" / "sunum_20260913" / "ornek_icerik.json"
METIN = KOK / "FDR" / "sunum" / "sunum_metin.txt"

ETIKET_ADI = {"OLCULDU": "ÖLÇÜLDÜ", "OLCULEMEDI": "ÖLÇÜLEMEDİ", "BEYAN": "BEYAN"}
GECERLI_TIPLER = {"kapak", "takim", "icerik", "tesekkur"}
ZORUNLU_META = ["proje_adi", "konu_basligi", "takim_adi", "takim_id",
                "basvuru_id", "tarih", "sure_dk"]
YER_TUTUCU = "[İNSAN DOLDURACAK]"

# "1,35" · "0,61" · "4.5.7" · "57600" · "%93" (yüzde işareti sayıya dahil değil)
SAYI = re.compile(r"\d+(?:[.,]\d+)*")

_KAYNAK_ONBELLEK = {}


def _kaynak_metni(yol: Path) -> str:
    anahtar = str(yol)
    if anahtar not in _KAYNAK_ONBELLEK:
        _KAYNAK_ONBELLEK[anahtar] = yol.read_text(encoding="utf-8", errors="replace")
    return _KAYNAK_ONBELLEK[anahtar]


def yukle(yol: Path):
    return json.loads(Path(yol).read_text(encoding="utf-8"))


def _maddeler(veri):
    for s in veri.get("slaytlar", []):
        for m in s.get("maddeler", []):
            yield s, m


# ─────────────────────────── kapılar ───────────────────────────

def kapi1_sema(veri):
    """Şema denetimi. (hatalar) döndürür."""
    h = []
    meta = veri.get("meta")
    if not isinstance(meta, dict):
        h.append("meta yok ya da sözlük değil")
    else:
        for alan in ZORUNLU_META:
            if alan not in meta:
                h.append(f"meta.{alan} yok")
    slaytlar = veri.get("slaytlar")
    if not isinstance(slaytlar, list) or not slaytlar:
        h.append("slaytlar yok ya da boş")
        return h
    nolar = []
    for i, s in enumerate(slaytlar):
        if not isinstance(s, dict):
            h.append(f"slaytlar[{i}] sözlük değil")
            continue
        if not isinstance(s.get("no"), int):
            h.append(f"slaytlar[{i}].no tamsayı değil")
        else:
            nolar.append(s["no"])
        if s.get("tip") not in GECERLI_TIPLER:
            h.append(f"slaytlar[{i}].tip geçersiz: {s.get('tip')!r}")
        for j, m in enumerate(s.get("maddeler", [])):
            yer = f"slaytlar[{i}].maddeler[{j}]"
            if not isinstance(m, dict) or not str(m.get("metin", "")).strip():
                h.append(f"{yer}.metin boş")
                continue
            if m.get("etiket") is not None and m["etiket"] not in ETIKET_ADI:
                h.append(f"{yer}.etiket geçersiz: {m['etiket']!r}")
            k = m.get("kaynak")
            if k is not None and not re.match(r"^[^:]+:\d+$", str(k)):
                h.append(f"{yer}.kaynak 'dosya:satır' değil: {k!r}")
    if len(set(nolar)) != len(nolar):
        h.append("slayt no'ları yinelenmiş")
    return h


def kapi2_kaynak_satiri(veri, kok=KOK):
    """Her kaynak: dosya var mı, satır numarası dosyada mevcut mu."""
    h = []
    for _s, m in _maddeler(veri):
        k = m.get("kaynak")
        if not k:
            continue
        dosya, _, satir = str(k).rpartition(":")
        p = kok / dosya
        if not p.is_file():
            h.append(f"kaynak dosyası yok: {k}")
            continue
        try:
            n = int(satir)
        except ValueError:
            h.append(f"kaynak satırı sayı değil: {k}")
            continue
        toplam = len(_kaynak_metni(p).splitlines())
        if not (1 <= n <= toplam):
            h.append(f"kaynak satırı dosyada yok: {k} (dosya {toplam} satır)")
    return h


def kapi3_sayilar(veri, kok=KOK):
    """Madde metnindeki her sayı kaynak dosyada geçmeli."""
    h = []
    for _s, m in _maddeler(veri):
        k = m.get("kaynak")
        if not k:
            continue
        dosya, _, _satir = str(k).rpartition(":")
        p = kok / dosya
        if not p.is_file():
            continue                       # K2 zaten düşürdü
        kaynak = _kaynak_metni(p)
        for sayi in SAYI.findall(m["metin"]):
            if sayi not in kaynak:
                h.append(f"{k} → '{sayi}' kaynakta YOK · madde: {m['metin'][:70]}")
    return h


def _metin_olculemedi_sayisi(metin: str) -> int:
    return sum(1 for satir in metin.splitlines()
               if satir.lstrip().startswith("-") and f"[{ETIKET_ADI['OLCULEMEDI']}]" in satir)


def kapi4_olculemedi_tutarlilik(veri, metin: str):
    """ÖLÇÜLEMEDİ sayısı iki dosyada aynı olmalı (sessiz düşme kapısı)."""
    json_sayi = sum(1 for _s, m in _maddeler(veri) if m.get("etiket") == "OLCULEMEDI")
    metin_sayi = _metin_olculemedi_sayisi(metin)
    beyan = veri.get("meta", {}).get("olculemedi_sayisi")
    h = []
    if json_sayi != metin_sayi:
        h.append(f"ÖLÇÜLEMEDİ sayısı uyuşmuyor: icerik.json={json_sayi} · metin={metin_sayi}")
    if beyan is not None and beyan != json_sayi:
        h.append(f"meta.olculemedi_sayisi={beyan} ama icerik.json'da {json_sayi} madde var")
    return h


def kapi5_yer_tutucular(veri):
    """[İNSAN DOLDURACAK] sayımı — hata değil, uyarı."""
    yerler = []
    for anahtar, d in veri.get("meta", {}).items():
        if isinstance(d, str) and YER_TUTUCU in d:
            yerler.append(f"meta.{anahtar}")
    for s, m in _maddeler(veri):
        if YER_TUTUCU in m.get("metin", ""):
            yerler.append(f"slayt {s.get('no')}: {m['metin'][:50]}")
    return yerler


# ─────────────────────────── testler ───────────────────────────

class FixtureKapilari(unittest.TestCase):
    """Kapılar fixture üzerinde her koşumda sınanır (gerçek içerik olmasa bile)."""

    @classmethod
    def setUpClass(cls):
        if not ORNEK.is_file():
            raise unittest.SkipTest(f"fixture yok: {ORNEK}")
        cls.veri = yukle(ORNEK)

    def test_K1_sema(self):
        self.assertEqual([], kapi1_sema(self.veri))

    def test_K2_kaynak_satiri(self):
        self.assertEqual([], kapi2_kaynak_satiri(self.veri))

    def test_K3_sayilar(self):
        self.assertEqual([], kapi3_sayilar(self.veri))


class Mutasyonlar(unittest.TestCase):
    """K6 — kapılar gerçekten yakalıyor mu? Bozulmuş kopya DÜŞMELİ."""

    @classmethod
    def setUpClass(cls):
        if not ORNEK.is_file():
            raise unittest.SkipTest(f"fixture yok: {ORNEK}")
        cls.veri = yukle(ORNEK)

    def test_M1_bozuk_sayi_K3u_dusurur(self):
        bozuk = json.loads(json.dumps(self.veri))          # derin kopya
        degisti = False
        for s in bozuk["slaytlar"]:
            for m in s.get("maddeler", []):
                if m.get("kaynak") and SAYI.search(m["metin"]):
                    m["metin"] = SAYI.sub("999999", m["metin"], count=1)
                    degisti = True
                    break
            if degisti:
                break
        self.assertTrue(degisti, "fixture'da kaynaklı ve sayılı madde yok — mutasyon kurulamadı")
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "bozuk.json"
            p.write_text(json.dumps(bozuk, ensure_ascii=False), encoding="utf-8")
            self.assertNotEqual([], kapi3_sayilar(yukle(p)),
                                "K3 uydurma sayıyı YAKALAMADI — kapı işe yaramıyor")

    def test_M2_silinen_olculemedi_K4u_dusurur(self):
        metin_satirlari = []
        for s in self.veri["slaytlar"]:
            for m in s.get("maddeler", []):
                sat = f"- {m['metin']}"
                if m.get("etiket"):
                    sat += f" [{ETIKET_ADI[m['etiket']]}]"
                metin_satirlari.append(sat)
        saglam = "\n".join(metin_satirlari)
        self.assertEqual([], kapi4_olculemedi_tutarlilik(self.veri, saglam),
                         "sağlam metin K4'ü düşürmemeli")
        bozuk = saglam.replace(f" [{ETIKET_ADI['OLCULEMEDI']}]", "", 1)
        self.assertNotEqual(saglam, bozuk, "fixture'da ÖLÇÜLEMEDİ etiketi yok")
        self.assertNotEqual([], kapi4_olculemedi_tutarlilik(self.veri, bozuk),
                            "K4 silinen ÖLÇÜLEMEDİ etiketini YAKALAMADI")


class GercekSunum(unittest.TestCase):
    """Gerçek sunum dosyaları varsa aynı kapılar onlara da uygulanır."""

    @classmethod
    def setUpClass(cls):
        if not ICERIK.is_file():
            raise unittest.SkipTest(f"gerçek içerik henüz yok: {ICERIK}")
        cls.veri = yukle(ICERIK)

    def test_K1_sema(self):
        self.assertEqual([], kapi1_sema(self.veri))

    def test_K2_kaynak_satiri(self):
        self.assertEqual([], kapi2_kaynak_satiri(self.veri))

    def test_K3_sayilar(self):
        self.assertEqual([], kapi3_sayilar(self.veri))

    def test_K4_olculemedi(self):
        if not METIN.is_file():
            self.skipTest(f"metin dökümü yok: {METIN}")
        self.assertEqual([], kapi4_olculemedi_tutarlilik(
            self.veri, METIN.read_text(encoding="utf-8")))


# ─────────────────────────── elle koşum raporu ───────────────────────────

def rapor(icerik_yolu: Path, metin_yolu: Path) -> int:
    if not Path(icerik_yolu).is_file():
        print(f"ATLANDI: içerik yok: {icerik_yolu}")
        return 0
    veri = yukle(icerik_yolu)
    gecti = 0
    toplam = 0

    def yaz(ad, hatalar):
        nonlocal gecti, toplam
        toplam += 1
        if hatalar:
            print(f"{ad}: DUSTU ({len(hatalar)})")
            for h in hatalar[:10]:
                print(f"    - {h}")
        else:
            print(f"{ad}: OK")
            gecti += 1

    yaz("K1 şema", kapi1_sema(veri))
    yaz("K2 kaynak satırı", kapi2_kaynak_satiri(veri))
    yaz("K3 sayılar kaynakta", kapi3_sayilar(veri))

    toplam += 1
    if Path(metin_yolu).is_file():
        h4 = kapi4_olculemedi_tutarlilik(veri, Path(metin_yolu).read_text(encoding="utf-8"))
        if h4:
            print(f"K4 ÖLÇÜLEMEDİ tutarlılığı: DUSTU ({len(h4)})")
            for h in h4:
                print(f"    - {h}")
        else:
            print("K4 ÖLÇÜLEMEDİ tutarlılığı: OK")
            gecti += 1
    else:
        print(f"K4 ÖLÇÜLEMEDİ tutarlılığı: DUSTU (metin dökümü yok: {metin_yolu})")

    yer = kapi5_yer_tutucular(veri)
    print(f"K5 yer tutucu: UYARI ({len(yer)} adet [İNSAN DOLDURACAK])")
    for y in yer:
        print(f"    - {y}")

    sonuc = unittest.TextTestRunner(verbosity=0, stream=open("/dev/null", "w")).run(
        unittest.TestLoader().loadTestsFromTestCase(Mutasyonlar))
    if sonuc.wasSuccessful():
        print(f"K6 mutasyon: OK ({sonuc.testsRun} mutasyon yakalandı)")
        gecti += 1
    else:
        print(f"K6 mutasyon: DUSTU ({len(sonuc.failures) + len(sonuc.errors)})")
    toplam += 1

    print(f"SONUC: {gecti}/{toplam} OK")
    return 0 if gecti == toplam else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="T259 sunum kanıt kapısı")
    ap.add_argument("--icerik", type=Path, default=ICERIK)
    ap.add_argument("--metin", type=Path, default=METIN)
    a = ap.parse_args()
    sys.exit(rapor(a.icerik, a.metin))
