"""Pixhawk 6C flash yolu belgeli ve çevrimdışı olmalı (D-424).

NEDEN: 5 Eylül'de sahada ölçüldü — yeni Pixhawk 6C USB'ye takıldı, Mission
Planner `Messages` sekmesi **boştu**. Sebep: kart fabrikadan **PX4 yüklü**
çıkar; bizim yığınımızın tamamı ArduCopter'dir. O gün depoda firmware dosyası
YOKTU, saha belleğinde YOKTU, flash yordamı **hiçbir belgede** YOKTU — plan
§2.4 yalnızca "ArduCopter kararlı sürüm" diyordu, sanki kartta zaten varmış
gibi. Atölyede internet vardı ve kurtardı; 21 Eylül Adıyaman'da internet
VARSAYILMAZ ve uçuş **tek atıştır**.

Bu kapı üç şeyi birden tutar:
  1. İndirici betik var ve doğru kartı hedefliyor (board_id 56 = Pixhawk6C).
  2. Flash yordamı **iki** belgede yazılı ve "önce firmware, sonra param"
     sırasını söylüyor — ters sıra bütün parametreleri siler.
  3. Saha belleği firmware'i taşıyor (indirilmişse) — internetsiz flash.

VAKUMLULUK: `firmware/` indirilmemişse 3. test atlanır ve bunu **söyler**;
sessizce yeşile dönmez ("ÖLÇÜLEMEDİ ≠ GEÇTİ").
"""

import json
import re
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
BETIK = KOK / "scripts" / "pixhawk_firmware_indir.py"
PLAN = KOK / "SAHA_HAZIRLIK_PLANI_20260903.md"
PARAM_README = KOK / "config" / "pixhawk" / "README.md"
BELLEK_BETIK = KOK / "scripts" / "bellek_hazirla.py"
FIRMWARE = KOK / "firmware"

# ArduPilot hwdef: Pixhawk6C board_id. Yanlış kartın .apj'si sahada zaman kaybıdır.
PIXHAWK6C_BOARD_ID = 56


def _oku(yol):
    return yol.read_text(encoding="utf-8")


class FirmwareIndiriciTests(unittest.TestCase):
    def test_indirici_betik_var_ve_dogru_karti_hedefler(self):
        self.assertTrue(BETIK.is_file(), f"{BETIK.name} yok — çevrimdışı flash yolu kapalı")
        metin = _oku(BETIK)
        self.assertIn(f"BOARD_ID = {PIXHAWK6C_BOARD_ID}", metin,
                      "Betik Pixhawk6C board_id'sini (56) doğrulamıyor")
        self.assertIn("Pixhawk6C", metin, "Betik kart adını taşımıyor")
        self.assertIn("stable", metin, "Betik kararlı (stable) sürümü çekmiyor")

    def test_bellek_betigi_firmware_klasorunu_kopyaliyor(self):
        metin = _oku(BELLEK_BETIK)
        self.assertRegex(
            metin, r'\(\s*"firmware"\s*,\s*"firmware"\s*,',
            "bellek_hazirla.py firmware/ için kopya kuralı taşımıyor — "
            "indirilen firmware saha belleğine GİTMEZ")


class FlashYordamiBelgeliTests(unittest.TestCase):
    def test_plan_2_4_flash_adimini_ve_teshisi_icerir(self):
        metin = _oku(PLAN)
        self.assertIn("PX4", metin,
                      "SAHA_HAZIRLIK_PLANI kartın PX4 ile geldiğini yazmıyor (D-424)")
        self.assertIn("arducopter.apj", metin,
                      "Plan hangi dosyanın yükleneceğini yazmıyor")

    def test_param_readme_ONCE_FIRMWARE_sirasini_soyluyor(self):
        """Ters sıra (önce param, sonra flash) bütün parametreleri siler."""
        metin = _oku(PARAM_README)
        self.assertIn("PX4", metin, "README kartın PX4 ile geldiğini yazmıyor")
        # Sıra kuralı açıkça yazılmış olmalı: firmware önce, param sonra.
        self.assertRegex(
            metin, r"firmware\s*→\s*param",
            "README 'firmware → param' sırasını açıkça yazmıyor — ters sıra "
            "yüklenen parametrelerin tamamını siler")
        self.assertRegex(
            metin, r"[Ff]lash.{0,40}(sıfırlar|siler)",
            "README flash'ın parametreleri sıfırladığını söylemiyor")

    def test_teshis_adimi_PX4_parametre_adlarini_veriyor(self):
        """Sahadaki insan PX4'ü ArduCopter'dan ayırt edebilmeli."""
        metin = _oku(PARAM_README)
        for ad in ("FRAME_CLASS", "MC_"):
            self.assertIn(ad, metin,
                          f"README teşhis için '{ad}' ayracını vermiyor")


class FirmwareCevrimdisiTests(unittest.TestCase):
    def test_indirilen_apj_pixhawk6c_icin(self):
        apj = FIRMWARE / "arducopter.apj"
        if not apj.is_file():
            self.skipTest(
                "firmware/arducopter.apj indirilmemiş — ÖLÇÜLEMEDİ, geçti değil. "
                "İndir: python scripts/pixhawk_firmware_indir.py")
        d = json.loads(apj.read_text(encoding="utf-8"))
        self.assertEqual(
            d.get("board_id"), PIXHAWK6C_BOARD_ID,
            f"İndirilen .apj board_id={d.get('board_id')} — Pixhawk6C değil "
            f"({PIXHAWK6C_BOARD_ID} beklenir). Bu dosya sahada YÜKLENMEZ.")
        self.assertEqual(d.get("summary"), "Pixhawk6C")


if __name__ == "__main__":
    unittest.main()
