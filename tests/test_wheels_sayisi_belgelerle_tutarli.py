"""Çevrimdışı `wheels/` sayıları belgelerde ELLE yazılmaz, DOĞRULANIR (D-423).

NEDEN: 4 Eylül'de `JETSON_NANO_KURULUM.md` §3.4'e şu saha kapısı yazılmıştı:

    ls ~/wheels | wc -l   ->  **48** beklenir

`wheels/` 48 `.whl` + 3 metin dosyası = **51** dosya içerir. `ls` süzgeçsizdir,
yani komut 51 basar, kapı 48 bekler: **doğru bir kopyada bile düşer.** Sahadaki
insan kurulumu durdurup USB'yi suçlardı.

Bu kapı iki şeyi birden tutar:
  1. Belgedeki komut, beklediği sayıyı GERÇEKTEN basan komut olmalı.
  2. Sayı değişirse (bir `.whl` eklenir/çıkarılır) belge sessizce bayatlayamaz.
"""

import re
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
WHEELS = KOK / "wheels"
KILAVUZ = KOK / "jetson_paket" / "JETSON_NANO_KURULUM.md"
KART = KOK / "results" / "faz_b_oncesi" / "CUMA_KONTROL_KARTI.md"


def _oku(yol):
    return yol.read_text(encoding="utf-8")


def _sayilar():
    """Dosya sistemini say — belgeden değil, diskten."""
    dosyalar = [p for p in WHEELS.iterdir() if p.is_file()]
    whl = [p for p in dosyalar if p.suffix == ".whl"]
    return len(whl), len(dosyalar)


class WheelsSayisiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not WHEELS.is_dir():
            raise unittest.SkipTest("wheels/ yok — çevrimdışı paketler indirilmemiş")
        cls.n_whl, cls.n_tum = _sayilar()

    def test_kilavuzdaki_saha_kapisi_gercek_whl_sayisini_bekler(self):
        """§3.4'teki kapı `*.whl` süzgeçli olmalı ve gerçek sayıyı beklemeli."""
        metin = _oku(KILAVUZ)
        kalip = re.compile(
            r"`ls ~/wheels/\*\.whl \| wc -l`\s*\*\*(\d+)\*\*")
        eslesme = kalip.search(metin)
        self.assertIsNotNone(
            eslesme,
            "JETSON_NANO_KURULUM.md §3.4'te `ls ~/wheels/*.whl | wc -l` kapısı yok. "
            "Süzgeçsiz `ls ~/wheels` kullanılıyorsa metin dosyaları da sayılır (D-423).")
        self.assertEqual(
            int(eslesme.group(1)), self.n_whl,
            f"Kılavuz {eslesme.group(1)} bekliyor ama diskte {self.n_whl} adet .whl var. "
            "Paket eklendi/çıkarıldıysa belgeyi güncelle.")

    def test_suzgecsiz_ls_kapisi_belgede_KALMAMIS_olmali(self):
        """Eski hatalı biçim geri gelirse kapı düşer."""
        metin = _oku(KILAVUZ)
        self.assertNotRegex(
            metin, r"`ls ~/wheels \| wc -l`\s*\*\*\d+\*\*",
            "Süzgeçsiz `ls ~/wheels | wc -l` kapısı geri gelmiş. Bu komut "
            f"{self.n_tum} basar ({self.n_whl} .whl + metin dosyaları), yani doğru "
            "bir kopyada bile düşer (D-423).")

    def test_cuma_kartinda_HER_IKI_sayi_da_dogru(self):
        """Kart hem toplamı hem .whl sayısını taşımalı — ikisi karıştırılmasın."""
        metin = _oku(KART)
        satirlar = [s for s in metin.splitlines() if "wheels/" in s and "Çevrimdışı" in s]
        self.assertEqual(len(satirlar), 1,
                         f"Kartta tam bir 'Çevrimdışı tekerlekler' satırı olmalı, "
                         f"{len(satirlar)} bulundu")
        satir = satirlar[0]
        self.assertIn(str(self.n_tum), satir,
                      f"Kart toplam dosya sayısını ({self.n_tum}) yazmıyor")
        self.assertIn(str(self.n_whl), satir,
                      f"Kart .whl sayısını ({self.n_whl}) yazmıyor")

    def test_VAKUMLULUK_iki_sayi_farkli_olmali(self):
        """.whl sayısı == toplam ise bu testin ayırt edici gücü yoktur.

        O durumda metin dosyaları silinmiş demektir; testi yeşil bırakmak
        yerine bunu söylemek doğrudur — kapının kendisi de ölçülür.
        """
        self.assertNotEqual(
            self.n_whl, self.n_tum,
            "wheels/ içinde .whl dışı dosya kalmamış. Bu test iki sayıyı ayırt "
            "etmek için var; eşitlerse anlamsızdır. INDIRME_RAPORU.txt / "
            "kaynak_paketler.txt / requirements_nano.txt silinmiş olabilir.")


if __name__ == "__main__":
    unittest.main()
