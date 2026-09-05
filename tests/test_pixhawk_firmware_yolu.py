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


class SurumKilidiTests(unittest.TestCase):
    """D-425: parametre dosyası Copter-4.5'e bağlıdır; firmware sürümü SABİT olmalı.

    5 Eylül'de gerçek kartta ölçüldü: MP'nin önerdiği "en son kararlı" 4.7.1
    yüklendi, `.param` yüklendi, MP "Missing 9 params" dedi. Copter-4.7 SI
    birim reformu: `WPNAV_SPEED`(cm/s)→`WP_SPD`(m/s), `RTL_ALT`(cm)→`RTL_ALT_M`,
    `ARMING_CHECK`→`ARMING_SKIPCHK` (bit anlamı TERS), `SRx_*`→`MAVx_*`.
    """

    PARAM = KOK / "config" / "pixhawk" / "arducopter_fda.param"

    def test_indirici_stable_DEGIL_sabit_4_5_surumu_ceker(self):
        metin = _oku(BETIK)
        self.assertRegex(
            metin, r'SURUM\s*=\s*"stable-4\.5\.\d+"',
            "İndirici sürümü 4.5.x'e sabitlemiyor — 'stable' (= en son) çekerse "
            "4.7'nin SI reformu parametre dosyasını kırar (D-425)")
        self.assertNotRegex(
            metin, r'/Copter/stable/\{KART\}',
            "İndirici hâlâ /Copter/stable/ (= en son) yolunu kullanıyor")

    def test_param_dosyasi_kaynak_surumunu_beyan_ediyor(self):
        """Dosya hangi kaynaktan yazıldığını söylemeli; sabitleme ona dayanır."""
        metin = _oku(self.PARAM)
        self.assertIn("Copter-4.5", metin,
                      ".param başlığı kaynak sürümünü (Copter-4.5) beyan etmiyor")

    def test_iki_belge_de_4_5_7_diyor_ve_en_sona_karsi_uyariyor(self):
        for yol in (PARAM_README, PLAN):
            metin = _oku(yol)
            self.assertIn("4.5.7", metin,
                          f"{yol.name} uçuş sürümünü (4.5.7) yazmıyor")
            self.assertRegex(
                metin, r"4\.7",
                f"{yol.name} 4.7'nin NEDEN kullanılmayacağını söylemiyor — "
                "sahadaki insan MP'nin ikonuna tıklar ve 4.7 yükler")

    def test_indirilen_firmware_4_5_hattinda(self):
        sv = FIRMWARE / "firmware-version.txt"
        if not sv.is_file():
            self.skipTest("firmware/ indirilmemiş — ÖLÇÜLEMEDİ, geçti değil")
        metin = sv.read_text(encoding="utf-8", errors="replace").strip()
        self.assertTrue(
            metin.startswith("4.5."),
            f"Saha belleğine gidecek firmware {metin} — 4.5.x değil. "
            "Bu dosya sahada YÜKLENMEZ (D-425).")


if __name__ == "__main__":
    unittest.main()
