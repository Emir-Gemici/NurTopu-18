"""T104 KAPISI: iki `JETSON_KILAVUZ.md`in KURULUM YORDAMI ayni ve EKSIKSIZ.

KARAR (REVIEW_LOG D-193, mimar). T112'de olcum aynasi icin BAYT KIMLIGI
kullanildi (`scripts/olcum/` <-> canli). Burada AYNI degismez UYGULANAMAZ:
iki kilavuz FARKLI BAGLAM anlatir ve farklari MESRUDUR —

  kok kopya   : depo baglami ("Depo kopyasinda ayni manifest
                `jetson_paket/models/` altindan bulunur")
  paket kopya : saha baglami + ek bir SS0-A bolumu (G1..G4)

Bayt kimligi dayatmak bu icerigi SILERDI. Yuk tasiyan degismez BASKA:

    KURULUM YORDAMI (dizin agaci + kopyalanan dosya kumesi) AYNI olmali,
    ve paketin GERCEKTEN tasidigi dosyalari EKSIKSIZ kapsamali.

🔴 NEDEN BU KAPI VAR — IKI KEZ KIRILDI:
  · T103 (D-177): iki kilavuzda da `config` dizini YOKTU -> defter
    kopyalanmiyordu -> `load_model` FAIL-CLOSED duserdi.
  · T104 (D-193): kok kopyada `comms` dizini ve `karar_sozlesmesi.py` YOKTU.
    `costmap_path_finder.py` `karar_sozlesmesi`i IMPORT EDER; bu kilavuzu
    izleyen saha kurulumu `ImportError` alirdi.

⚠ BEKLENEN DOSYA LISTESI ELLE YAZILMAZ. `scripts/jetson_paket_hazirla.py`
icindeki `KOPYALAR` sozlugunden TURETILIR — elle liste bu projede tekrar
tekrar bayatladi (D-146 · D-157 · D-159 · D-163). Paketleyiciye yeni bir
dosya eklenirse bu kapi kendiliginden onu da arar.
"""

import re
import sys
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
KILAVUZLAR = (KOK / "JETSON_KILAVUZ.md",
              KOK / "jetson_paket" / "JETSON_KILAVUZ.md")

sys.path.insert(0, str(KOK / "scripts"))
from jetson_paket_hazirla import KOPYALAR  # noqa: E402


def _paketin_tasidigi_dosyalar():
    """Paketleyicinin `kod/` altina koydugu dosya adlari (KOPYALAR'dan turer)."""
    return {h.name for h in KOPYALAR.values() if h.parent.name == "kod"}


def _kurulum_blogu(metin):
    """Kilavuzdaki `mkdir -p ~/navitas/...` ve ardindaki `cp` satirlari."""
    satirlar = metin.splitlines()
    for i, s in enumerate(satirlar):
        if "mkdir -p ~/navitas/" in s:
            blok = [s]
            for t in satirlar[i + 1:]:
                if t.startswith("cp ") or t.startswith("python3 ") or not t.strip():
                    blok.append(t)
                    if t.strip() and not t.startswith("cp "):
                        break
                else:
                    break
            return blok
    return []


def _mkdir_dizinleri(blok):
    for s in blok:
        m = re.search(r"mkdir -p ~/navitas/\{([^}]*)\}", s)
        if m:
            return {a.strip() for a in m.group(1).split(",") if a.strip()}
    return set()


def _kopyalanan_adlar(blok):
    adlar = set()
    for s in blok:
        if s.startswith("cp "):
            for parca in s.split()[1:-1]:
                adlar.add(Path(parca).name)
    return adlar


class KilavuzKurulumYordami(unittest.TestCase):
    def test_IKI_kilavuz_da_kurulum_blogu_TASIYOR(self):
        """Pozitif kontrol: blok bulunamazsa asagidaki testler BOS gecerdi."""
        for k in KILAVUZLAR:
            with self.subTest(kilavuz=k.parent.name):
                self.assertTrue(k.is_file(), f"kilavuz yok: {k}")
                blok = _kurulum_blogu(k.read_text(encoding="utf-8"))
                self.assertTrue(blok, "kurulum blogu (`mkdir -p ~/navitas/`) yok")
                self.assertTrue(_mkdir_dizinleri(blok), "mkdir dizinleri okunamadi")

    def test_dizin_agaci_IKI_kilavuzda_AYNI(self):
        kumeler = {}
        for k in KILAVUZLAR:
            blok = _kurulum_blogu(k.read_text(encoding="utf-8"))
            kumeler[k.parent.name] = _mkdir_dizinleri(blok)
        adlar = list(kumeler)
        self.assertEqual(
            kumeler[adlar[0]], kumeler[adlar[1]],
            "iki kilavuz FARKLI dizin agaci soyluyor; sahadaki kisi hangisini "
            "okudugusa gore FARKLI kurulum yapar (T104 · D-193)")

    def test_config_dizini_ZORUNLU(self):
        """T103/D-177: `config` yoksa defter kopyalanmaz -> load_model DUSER."""
        for k in KILAVUZLAR:
            with self.subTest(kilavuz=k.parent.name):
                blok = _kurulum_blogu(k.read_text(encoding="utf-8"))
                self.assertIn("config", _mkdir_dizinleri(blok))
                self.assertTrue(
                    any("model_registry.json" in s for s in blok),
                    "kayit defteri kopyalanmiyor — `load_model` fail-closed duser")

    def test_PAKETIN_TASIDIGI_her_dosya_kilavuzda_KOPYALANIYOR(self):
        """Liste ELLE degil `KOPYALAR`dan turer — bayatlamasin diye."""
        beklenen = _paketin_tasidigi_dosyalar()
        self.assertGreaterEqual(len(beklenen), 9, "KOPYALAR beklenmedik sekilde kucuk")
        for k in KILAVUZLAR:
            blok = _kurulum_blogu(k.read_text(encoding="utf-8"))
            kopyalanan = _kopyalanan_adlar(blok)
            eksik = sorted(beklenen - kopyalanan)
            with self.subTest(kilavuz=k.parent.name):
                self.assertEqual(
                    [], eksik,
                    f"paket bu dosyalari tasiyor ama kilavuz KOPYALAMIYOR: {eksik}")

    def test_karar_sozlesmesi_EKSIK_KALAMAZ(self):
        """D-193: `costmap_path_finder` onu IMPORT eder; eksikse ImportError."""
        kaynak = (KOK / "codes" / "costmap_path_finder.py").read_text(encoding="utf-8")
        self.assertIn("karar_sozlesmesi", kaynak,
                      "bu testin dayanagi kalkmis: costmap artik onu import etmiyor")
        for k in KILAVUZLAR:
            with self.subTest(kilavuz=k.parent.name):
                blok = _kurulum_blogu(k.read_text(encoding="utf-8"))
                self.assertIn("karar_sozlesmesi.py", _kopyalanan_adlar(blok))

    def test_POZITIF_KONTROL_ayristirici_gercekten_okuyor(self):
        """Yardimcilar bos kume dondurup testleri BOS gecirmesin."""
        ornek = ("mkdir -p ~/navitas/{codes,comms,config}\n"
                 "cp kod/a.py kod/b.py ~/navitas/codes/\n")
        blok = _kurulum_blogu(ornek)
        self.assertEqual({"codes", "comms", "config"}, _mkdir_dizinleri(blok))
        self.assertEqual({"a.py", "b.py"}, _kopyalanan_adlar(blok))
        self.assertEqual(set(), _mkdir_dizinleri([]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
