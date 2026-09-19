"""YKİ akla yatkın olmayan İHA telemetrisini GÖSTERMEZ (yalnız gösterim).

NEDEN (19 Eylül telsiz kanıtı): Pixhawk yeniden başlayınca heartbeat
lat/lon ≈ 0/0 taşıdı ve ekran aracı ~4500 km öteye koydu; başka bir anda
alt = 890,6 m geldi ve §5.3.2 uyum satırı "asgari 30 m sağlanıyor" dedi.
Jetson tarafı ayrıca düzeltiliyor; yer istasyonu da buna güvenmemeli.

Ölçülen önceki davranış (bu dosyadan önce, aynı çağrılar):
  alt 0.0 / -10.0 / 890.6 → "irtifa … m — §5.3.2 asgari 30 m sağlanıyor"
  {lat 0, lon 0, fix 3}   → "HAM GNSS: 0.0000000, 0.0000000 · … · 3B FIX ✓"
  {fix 1}                 → koordinat yine basılıyordu

Kilitler:
  G1  0/0 (ikisi de < 1e-6°) GNSS geçersiz; tek eksen 0 (ekvator/meridyen) geçerli
  G2  0/0 ve fix<3'te HAM GNSS satırı koordinat BASMAZ → "konum BİLİNMİYOR"
  G3  geçerli 3B fix'te koordinat basılır (regresyon)
  G4  uçtan uca heartbeat → `_durum_tazele`: GNSS etiketi KIRMIZI + BİLİNMİYOR;
      kayda giden ham telemetri (TELEMETRI_KANIT dugumler) DEĞİŞMEZ
  F1  `gps_fix` alanı YOK (mimar ölçümü: 19 Eyl oturumlarının çoğunda yok) +
      akla yatkın lat/lon → SAYILAR gösterilir + "fix BİLİNMİYOR", durum
      "FIX YETERSİZ" (yeşil değil); katı doğrulayıcı yine False (etiket KIRMIZI)
  F2  `gps_fix` = 2 → gizli (regresyon)
  F3  `gps_fix` yok + 0/0 → gizli
  F4  `gps_fix` = 3 → değişmedi (yeşil, 3B FIX ✓)
  F5  uçtan uca: fix'siz heartbeat → `_durum_tazele` etiketi sayıları gösterir,
      KIRMIZI kalır
  A1  bant dışı irtifa (890,6 / 250 / -60 / NaN / bool) → "İRTİFA GEÇERSİZ",
      "sağlanıyor" YOK, onay etiketi kirlenmez
  A2  bant sınırı: 200 m (IRTIFA_MAKUL_UST_M) geçerli
  A3  0 m ve -10 m (bant içi, asgari altı) → ASGARİ İRTİFA ALTI uyarısı
      (eski yol "sağlanıyor" diyordu)
  A4  35 m → sağlanıyor (regresyon)

Tk açılmaz, port bağlanmaz.

KOSUM:
  O:\\navitas-local-train\\venv\\Scripts\\python.exe -B -m unittest discover \\
      -s tests -p "test_yks_telemetri_akla_yatkinlik.py"
"""

import sys
import unittest
from pathlib import Path
from unittest import mock

KOK = Path(__file__).resolve().parents[1]
for _y in (KOK / "comms", KOK / "codes", KOK / "tests"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

import yks_gui  # noqa: E402
from protocol import heartbeat  # noqa: E402
from test_yks_operator_guvenligi import _taban_arayuz  # noqa: E402

GERCEK = {"lat": 37.7648123, "lon": 38.2786456, "gps_fix": 3, "uydu": 14}


class GnssGosterimi(unittest.TestCase):

    def test_G1_sifir_sifir_gecersiz_tek_eksen_sifir_gecerli(self):
        gecerli, sebep = yks_gui.gps_telemetrisi_dogrula(
            {"lat": 0.0, "lon": 0.0, "gps_fix": 3})
        self.assertFalse(gecerli)
        self.assertIn("0/0", sebep)
        self.assertFalse(yks_gui.gps_telemetrisi_dogrula(
            {"lat": 5e-7, "lon": -5e-7, "gps_fix": 3})[0])
        self.assertTrue(yks_gui.gps_telemetrisi_dogrula(
            {"lat": 0.0, "lon": 38.27, "gps_fix": 3})[0])
        self.assertTrue(yks_gui.gps_telemetrisi_dogrula(
            {"lat": 37.76, "lon": 0.0, "gps_fix": 3})[0])

    def test_G2_sifir_sifir_ve_fixsiz_koordinat_basilmaz(self):
        metin = yks_gui.gps_gosterim_metni(
            {"lat": 0.0, "lon": 0.0, "gps_fix": 3, "uydu": 0})
        self.assertIn("konum BİLİNMİYOR", metin)
        self.assertNotIn("0.0000000", metin)
        self.assertNotIn("3B FIX ✓", metin)
        for fix in (0, 1, 2):
            with self.subTest(fix=fix):
                metin = yks_gui.gps_gosterim_metni(dict(GERCEK, gps_fix=fix))
                self.assertIn("konum BİLİNMİYOR", metin)
                self.assertNotIn("37.7648123", metin)
                self.assertIn(f"fix {fix}", metin)

    def test_G3_gecerli_3B_fix_koordinati_basar(self):
        metin = yks_gui.gps_gosterim_metni(GERCEK)
        self.assertIn("37.7648123, 38.2786456", metin)
        self.assertIn("3B FIX ✓", metin)
        self.assertIn("konum YOK",
                      yks_gui.gps_gosterim_metni({"gps_fix": 3}))

    def test_G4_uctan_uca_etiket_kirmizi_kayit_ham_kalir(self):
        g = _taban_arayuz()
        g._mesaj_isle(heartbeat("iha", seq=1, lat=0.0, lon=0.0, gps_fix=3,
                                uydu=0, alt=890.6, pixhawk_canli=True,
                                armed=False, mod="AUTO"), None)
        g._durum_tazele()
        self.assertIn("konum BİLİNMİYOR", g.lbl_gps.ayar["text"])
        self.assertEqual(yks_gui.KIRMIZI, g.lbl_gps.ayar["fg"])
        # Kayıt: ham telemetri aynen (yalnız gösterim değişti).
        self.assertEqual(0.0, g.tel["iha"]["lat"])
        self.assertEqual(890.6, g.tel["iha"]["alt"])
        kayit = g._kanit_durumu_yaz.call_args.kwargs["dugumler"]["iha"]
        self.assertEqual(0.0, kayit["telemetri"]["lat"])
        self.assertEqual(0.0, kayit["telemetri"]["lon"])
        self.assertEqual(890.6, kayit["telemetri"]["alt"])


class FixAlaniYok(unittest.TestCase):
    """Mimar ölçümü (19 Eyl): prova3/4/5 ve yki_uctan_uca oturumlarında
    lat/lon taşıyan heartbeat'lerin HİÇBİRİNDE `gps_fix` yoktu (prova2:
    59/118). 21ae2f5f bu durumda konumu gizliyordu (gerileme)."""

    FIXSIZ = {"lat": 40.9594863, "lon": 29.1337822}

    def test_F1_fix_alani_yok_sayilar_gosterilir_isaretli(self):
        metin = yks_gui.gps_gosterim_metni(dict(self.FIXSIZ))
        self.assertIn("40.9594863, 29.1337822", metin)
        self.assertIn("fix BİLİNMİYOR", metin)
        self.assertIn("FIX YETERSİZ", metin)
        self.assertNotIn("3B FIX ✓", metin)
        self.assertNotIn("konum BİLİNMİYOR", metin)
        # Katı doğrulayıcı GEVŞEMEDİ (etiket rengi ondan okunur).
        self.assertEqual((False, "3B fix yok"),
                         yks_gui.gps_telemetrisi_dogrula(dict(self.FIXSIZ)))
        metin = yks_gui.gps_gosterim_metni(dict(self.FIXSIZ, gps_fix=None))
        self.assertIn("40.9594863", metin)

    def test_F2_fix_iki_gizler(self):
        metin = yks_gui.gps_gosterim_metni(dict(self.FIXSIZ, gps_fix=2))
        self.assertIn("konum BİLİNMİYOR", metin)
        self.assertNotIn("40.9594863", metin)
        self.assertIn("fix 2", metin)

    def test_F3_fixsiz_sifir_sifir_gizlenir(self):
        metin = yks_gui.gps_gosterim_metni({"lat": 0.0, "lon": 0.0})
        self.assertIn("konum BİLİNMİYOR", metin)
        self.assertNotIn("0.0000000", metin)
        self.assertIn("0/0", metin)
        for bozuk in ({"lat": 95.0, "lon": 29.1},
                      {"lat": float("nan"), "lon": 29.1}):
            with self.subTest(bozuk=bozuk):
                self.assertIn("konum BİLİNMİYOR",
                              yks_gui.gps_gosterim_metni(bozuk))

    def test_F4_fix_uc_degismedi(self):
        metin = yks_gui.gps_gosterim_metni(dict(self.FIXSIZ, gps_fix=3, uydu=11))
        self.assertIn("40.9594863, 29.1337822", metin)
        self.assertIn("fix 3", metin)
        self.assertIn("3B FIX ✓", metin)
        self.assertEqual((True, "3B fix"), yks_gui.gps_telemetrisi_dogrula(
            dict(self.FIXSIZ, gps_fix=3)))

    def test_F5_uctan_uca_fixsiz_heartbeat_sayilari_gosterir_kirmizi(self):
        g = _taban_arayuz()
        g._mesaj_isle(heartbeat("iha", seq=1, lat=40.9594863, lon=29.1337822,
                                pixhawk_canli=True, armed=False, mod="AUTO"),
                      None)
        self.assertNotIn("gps_fix", g.tel["iha"])
        g._durum_tazele()
        self.assertIn("40.9594863, 29.1337822", g.lbl_gps.ayar["text"])
        self.assertIn("fix BİLİNMİYOR", g.lbl_gps.ayar["text"])
        self.assertEqual(yks_gui.KIRMIZI, g.lbl_gps.ayar["fg"])


class IrtifaUyumSatiri(unittest.TestCase):

    @staticmethod
    def _ekran(alt):
        o = object.__new__(yks_gui.YksArayuz)
        o.tel = {"iha": {"alt": alt}}
        o.gunluk = []
        o._logla = lambda metin, renk=None: o.gunluk.append(metin)
        o.lbl_onay = mock.MagicMock()
        return o

    def test_A1_bant_disi_irtifa_GECERSIZ_saglaniyor_demez(self):
        for alt in (890.6, 250.0, -60.0, float("nan"), float("inf"), True):
            with self.subTest(alt=alt):
                o = self._ekran(alt)
                self.assertIsNone(o._irtifa_notunu_goster())
                self.assertTrue(any("İRTİFA GEÇERSİZ" in s for s in o.gunluk),
                                o.gunluk)
                self.assertFalse(any("sağlanıyor" in s for s in o.gunluk),
                                 o.gunluk)
                o.lbl_onay.config.assert_not_called()

    def test_A2_ust_sinir_sozlesmedeki_makul_ust(self):
        self.assertEqual(200.0, yks_gui.IRTIFA_MAKUL_UST_M)
        o = self._ekran(yks_gui.IRTIFA_MAKUL_UST_M)
        o._irtifa_notunu_goster()
        self.assertTrue(any("sağlanıyor" in s for s in o.gunluk), o.gunluk)
        self.assertTrue(yks_gui.irtifa_gosterimde_gecerli_mi(-49.9))
        self.assertFalse(yks_gui.irtifa_gosterimde_gecerli_mi(-50.0))
        self.assertFalse(yks_gui.irtifa_gosterimde_gecerli_mi(200.1))

    def test_A3_yerdeki_arac_saglaniyor_DEMEZ_uyari_verir(self):
        for alt in (0.0, -10.0):
            with self.subTest(alt=alt):
                o = self._ekran(alt)
                self.assertIsNotNone(o._irtifa_notunu_goster())
                self.assertFalse(any("sağlanıyor" in s for s in o.gunluk),
                                 o.gunluk)
                metin = o.lbl_onay.config.call_args.kwargs["text"]
                self.assertIn("ASGARİ İRTİFA ALTI", metin)

    def test_A4_gecerli_irtifa_regresyon(self):
        o = self._ekran(35.0)
        self.assertIsNone(o._irtifa_notunu_goster())
        self.assertTrue(any("sağlanıyor" in s for s in o.gunluk), o.gunluk)
        o = self._ekran(12.0)
        self.assertIsNotNone(o._irtifa_notunu_goster())
        self.assertIn("12.0 m", o.lbl_onay.config.call_args.kwargs["text"])


if __name__ == "__main__":
    unittest.main()
