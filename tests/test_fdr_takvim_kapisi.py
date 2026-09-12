"""D-410 — RESMİ TAKVİM KAPISI: 21 Eylül uçuş günü DEĞİLDİR.

NEDEN (ölçülen kusur): FDR taslağı ve saha planı 21 Eylül'ü şartname §5.3.2'nin
"Drone ile Görev Test Uçuşu" günü sanıp öyle etiketledi. Şartname Tablo 1 başka
söylüyor:

    21.09.2026 – 17.00   →  **FDR Son Teslim Tarihi**
    30.09-03.10.2026     →  Final Değerlendirme Aşaması
                            (FDS sunumları + Drone ile Görev Test Uçuşu)

Hata bir çürütücü turunda bulundu; bu kapı **tekrarını** engeller. Belgeler
takvimi başka türlü yazamaz: kaynak `results/sartname_bosluk/sartname_metin.txt`
değişmedikçe iddia da değişemez.

Kilitler:
  T1  şartname metni gerçekten bu iki tarihi söylüyor (kapının kendi dayanağı)
  T2  hiçbir belge "§5.3.2 ... 21 Eylül" biçiminde eşleştirme yapmıyor
  T3  FDR/README ve saha planı resmî takvim tablosunu TAŞIYOR
  T4  30 Eylül–3 Ekim penceresi belgelerde geçiyor (tarih sessizce düşmedi)
"""

import re
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
SARTNAME = KOK / "results" / "sartname_bosluk" / "sartname_metin.txt"

# Takvim iddiası taşıyan belgeler (kanıt klasörleri ve ham çıkarımlar hariç).
BELGELER = [
    KOK / "FDR" / "README.md",
    KOK / "FDR" / "BOLUM_1_OZET.md",
    KOK / "FDR" / "BOLUM_3_SISTEM_SPESIFIKASYONLARI.md",
    KOK / "FDR" / "BOLUM_4_TEST_FAALIYETLERI.md",
    KOK / "FDR" / "BOLUM_6_GEREKSINIM_IZLENEBILIRLIGI.md",
    KOK / "SAHA_HAZIRLIK_PLANI_20260903.md",
    KOK / "SAHA_RUNBOOK.md",
    KOK / "CONTRACTS.md",
]

# "§5.3.2 ... 21 Eylül" ya da "21 Eylül ... §5.3.2" yakınlığı: 80 karakter
# içinde ikisi birden geçerse belge uçuşu yanlış güne bağlamış demektir.
YASAK = re.compile(
    r"(5\.3\.2[^\n]{0,80}21 Eylül)|(21 Eylül[^\n]{0,80}5\.3\.2)")
# "21 Eylül'deki görev test uçuşu" gibi doğrudan etiketler
YASAK2 = re.compile(r"21 Eylül[^\n]{0,20}(görev test uçuşu|zorunlu uçuş)")


class SartnameDayanagi(unittest.TestCase):
    def test_T1_sartname_iki_tarihi_soyluyor(self):
        metin = SARTNAME.read_text(encoding="utf-8", errors="replace")
        self.assertIn("21.09.2026", metin)
        self.assertIn("30.09-03.10.2026", metin)
        # FDR teslimi 21'inde, gorev test ucusu 30 Eylul penceresinde
        i21 = metin.index("21.09.2026")
        pencere = metin[max(0, i21 - 260):i21]
        self.assertIn("Final Değerlendirme Raporu", pencere,
                      "21.09.2026 FDR teslim satırında değil — şartname değişmiş olabilir")
        i30 = metin.index("30.09-03.10.2026")
        pencere30 = metin[max(0, i30 - 320):i30]
        self.assertIn("Görev Test Uçuşu", pencere30,
                      "30.09-03.10 görev test uçuşu satırında değil")


class BelgeKapisi(unittest.TestCase):
    def test_T2_hicbir_belge_ucusu_21_eylule_baglamiyor(self):
        hatali = []
        for p in BELGELER:
            if not p.is_file():
                continue
            for i, satir in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                # "prova" geçen satır bu kapıdan muaftır: takım provası 21'inde.
                if "prova" in satir.lower():
                    continue
                if YASAK.search(satir) or YASAK2.search(satir):
                    hatali.append(f"{p.name}:{i}  {satir.strip()[:120]}")
        self.assertEqual([], hatali,
                         "21 Eylül FDR TESLİM günüdür; §5.3.2 uçuşu 30.09-03.10'dadır")

    def test_T3_resmi_takvim_tablosu_belgelerde(self):
        for p in (KOK / "FDR" / "README.md", KOK / "SAHA_HAZIRLIK_PLANI_20260903.md"):
            metin = p.read_text(encoding="utf-8")
            with self.subTest(dosya=p.name):
                self.assertIn("21.09.2026", metin)
                self.assertRegex(metin, r"30\.09\s*[–-]\s*0?3\.10\.2026")
                self.assertIn("FDR", metin)

    def test_T5_guncel_teslim_tarihi_14_eylul_belgelerde(self):
        """D-476: teslim 14.09.2026 – 17.00'ye ÖNE ÇEKİLDİ (resmî yarışma sayfası).

        Şartname PDF'i hâlâ 21.09.2026 diyor (T1 onu kilitler ve DOĞRUDUR —
        şartname o tarihte öyle yazmıştı). Değişen şey organizasyonun sonraki
        duyurusudur. Bu kilit, güncel tarihin belgelerden **sessizce düşmesini**
        engeller; eski tarih üstü çizili KALIR (silinmez, madde 6)."""
        for p_ in (KOK / "FDR" / "README.md", KOK / "SAHA_HAZIRLIK_PLANI_20260903.md",
                   KOK / "FDR" / "BOLUM_2_ORGANIZASYON_VE_TAKVIM.md"):
            metin = p_.read_text(encoding="utf-8")
            with self.subTest(dosya=p_.name):
                self.assertIn("14.09.2026", metin,
                              "güncel FDR teslim tarihi belgeden düşmüş")
                self.assertIn("21.09.2026", metin,
                              "eski tarih silinmiş — üstü çizili KALMALI (madde 6)")
                self.assertRegex(metin, r"~~[^~]*21\.09\.2026[^~]*~~",
                                 "eski tarih üstü çizili değil")

    def test_T4_ucus_penceresi_kaybolmadi(self):
        gecen = [p.name for p in BELGELER if p.is_file()
                 and re.search(r"30 Eylül[^\n]{0,12}3 Ekim|30\.09", p.read_text(encoding="utf-8"))]
        self.assertGreaterEqual(len(gecen), 3,
                                f"uçuş penceresi yalnız {gecen} belgesinde geçiyor")


if __name__ == "__main__":
    unittest.main()
