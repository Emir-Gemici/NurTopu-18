"""SiK saha yordamı tek-sahip hub mimarisinden sessizce ayrılamaz."""

import re
import unittest
from pathlib import Path


KOK = Path(__file__).resolve().parents[1]
KILAVUZLAR = (KOK / "JETSON_KILAVUZ.md",
              KOK / "jetson_paket" / "JETSON_KILAVUZ.md")


class YksSikYordamiTests(unittest.TestCase):
    def test_iki_kilavuz_da_hub_ve_ack_yolunu_anlatir(self):
        for yol in KILAVUZLAR:
            with self.subTest(kilavuz=str(yol)):
                metin = yol.read_text(encoding="utf-8")
                self.assertIn("KIP=sik", metin)
                self.assertIn("seri_hub", metin)
                self.assertIn("çift yönlü ACK", metin)
                self.assertIn("jetson_baslat.sh --kapi", metin)

    def test_dogrudan_rpi_telsiz_seri_calistiran_eski_komut_YOK(self):
        """Mutasyon: eski çok-sahipli komut geri gelirse kapı düşer."""
        eski_komut = re.compile(
            r"python3\s+[^\n]*rpi_inference\.py(?:(?!```)[\s\S])*?"
            r"--telsiz-seri\s+/dev/ttyUSB0")
        for yol in KILAVUZLAR:
            with self.subTest(kilavuz=str(yol)):
                metin = yol.read_text(encoding="utf-8")
                self.assertIsNone(eski_komut.search(metin),
                                  "eski doğrudan SiK komutu geri geldi")

    def test_iki_kilavuzun_sik_bloklari_AYNI(self):
        def blok(metin):
            bas = metin.index("SiK 433 MHz telsiz (saha")
            son = metin.index("\n---", bas)
            return metin[bas:son].strip()

        ana, paket = (blok(y.read_text(encoding="utf-8")) for y in KILAVUZLAR)
        self.assertEqual(ana, paket)


if __name__ == "__main__":
    unittest.main()
