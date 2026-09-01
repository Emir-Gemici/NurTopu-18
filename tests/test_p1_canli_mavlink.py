"""P1 (plan v2) — URETIM MAVLink YOLU GERCEK CERCEVELERLE KOSTU.

ON KAYIT: results/p1_mavlink/ON_KAYIT.md (G1..G8 sonuc gorulmeden yazildi).

NEDEN: `test_inis_kaniti.py` sozlesmeyi SAHTE nesnelerle kilitler; pymavlink
2026-09-02'ye kadar venv'de kurulu bile degildi. Bu nobetci ayni uretim
siniflarini GERCEK pymavlink akisina baglar: gercek serilestirme, gercek CRC,
gercek `recv_match`, UDP soketi. `KOD_VAR != KOSUYOR` sinifi kapanir.

Kapsam (ON_KAYIT §2):
  G1 ucus akisi: irtifa + konum okunuyor
  G2 irtifa -> mpp: CanliOlcekSaglayici canli akistan olcek uretiyor
  G3 inis kaniti: gercek alcalma + ON_GROUND -> yerde_mi True
  G4 havadayken: IN_AIR -> yerde_mi False (fail-closed)
  G5 yabanci kaynak: sysid 99'un irtifasi ASLA donmez
  G6 donuk saat: ilerlemeyen time_boot_ms yasi yenilemez
  G7 bayatlik: yayin durunca tazelik penceresi sonrasi None

⚠ Sahte Pixhawk gercek ucus kontrolcusu DEGILDIR (ON_KAYIT §4); Faz B'de
gercek Pixhawk'la olculecek.
"""
import sys
import time
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
for _y in (KOK / "comms", KOK / "codes", KOK / "scripts"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

try:
    from pymavlink import mavutil
except ImportError:  # pragma: no cover - kurulum kapisi
    mavutil = None

import inis_kaniti as kanit  # noqa: E402
from karar_sozlesmesi import (TELEMETRI_IRTIFA_TAZELIK_S,  # noqa: E402
                              mpp_irtifadan)
from sahte_pixhawk import (VARSAYILAN_LAT, VARSAYILAN_LON,  # noqa: E402
                           YABANCI_SYSID, SahtePixhawk)

SYSID = 1
BEKLEME_TAVANI_S = 8.0
ICERIK_GENISLIGI_PX = 640
YATAY_FOV = 66.0


def _dinleyici():
    """Efemeral portta gercek MAVLink UDP dinleyicisi ac."""
    mav = mavutil.mavlink_connection("udpin:127.0.0.1:0")
    return mav, mav.port.getsockname()[1]


def _bekle(kosul, tavan_s=BEKLEME_TAVANI_S, adim_s=0.02):
    """Kosul saglanana dek bekle; saglanirsa True."""
    bitis = time.monotonic() + tavan_s
    while time.monotonic() < bitis:
        if kosul():
            return True
        time.sleep(adim_s)
    return False


@unittest.skipIf(mavutil is None, "pymavlink kurulu degil")
class CanliMavlinkAkisi(unittest.TestCase):
    """Uretim siniflari gercek MAVLink cerceveleriyle kosar."""

    def setUp(self):
        self.mav, self.port = _dinleyici()
        self.addCleanup(self.mav.close)
        self.okuyucular = []

    def _okuyucu(self, tazelik_s=TELEMETRI_IRTIFA_TAZELIK_S, sysid=SYSID):
        okuyucu = kanit.BagilIrtifaOkuyucu(self.mav, tazelik_s,
                                           beklenen_sysid=sysid)
        self.assertTrue(okuyucu.baslat(), "poller baslamadi")
        self.addCleanup(okuyucu.durdur)
        return okuyucu

    def _sahte(self, **kw):
        sp = SahtePixhawk(f"udpout:127.0.0.1:{self.port}", **kw)
        self.addCleanup(sp.dur)
        return sp

    # --- G1 ---
    def test_G1_ucus_akisi_irtifa_ve_konum(self):
        okuyucu = self._okuyucu()
        with self._sahte(senaryo="ucus", irtifa_m=30.0):
            self.assertTrue(_bekle(lambda: okuyucu.irtifa_m() is not None),
                            "gercek akistan hic irtifa okunamadi")
            irtifa = okuyucu.irtifa_m()
            konum = okuyucu.konum_derece()
        self.assertAlmostEqual(irtifa, 30.0, delta=0.05,
                               msg="ON_KAYIT G1: 30,0 ± 0,05 m")
        self.assertIsNotNone(konum, "ON_KAYIT G1: konum okunmali (T162 yolu)")
        self.assertAlmostEqual(konum[0], VARSAYILAN_LAT, delta=1e-6)
        self.assertAlmostEqual(konum[1], VARSAYILAN_LON, delta=1e-6)

    # --- G2 ---
    def test_G2_canli_akistan_mpp(self):
        from rpi_inference import CanliOlcekSaglayici
        okuyucu = self._okuyucu()
        saglayici = CanliOlcekSaglayici(okuyucu, yatay_fov_derece=YATAY_FOV)
        with self._sahte(senaryo="ucus", irtifa_m=30.0):
            self.assertTrue(
                _bekle(lambda: saglayici.kare_mpp(ICERIK_GENISLIGI_PX)
                       is not None),
                "canli akistan mpp uretilemedi")
            mpp = saglayici.kare_mpp(ICERIK_GENISLIGI_PX)
            irtifa = okuyucu.irtifa_m()
        self.assertIsNotNone(mpp)
        self.assertGreater(mpp, 0.0, "ON_KAYIT G2: mpp pozitif olmali")
        self.assertTrue(mpp == mpp and mpp not in (float("inf"),),
                        "mpp sonlu olmali")
        beklenen = mpp_irtifadan(irtifa, ICERIK_GENISLIGI_PX,
                                 yatay_fov_derece=YATAY_FOV)
        # Ayni irtifa penceresi icinde iki okuma; sozlesme ayni fonksiyonu verir
        self.assertAlmostEqual(mpp, beklenen, delta=beklenen * 0.02,
                               msg="ON_KAYIT G2: mpp_irtifadan ile ayni olmali")

    # --- G3 (pozitif yol: temas etmis arac) ---
    def test_G3_ON_GROUND_akisinda_inis_kaniti(self):
        """Gercek cerceveler gercek kaniti uretiyor mu (pozitif yol)."""
        self.mav.inis_kaniti_deadline_monotonic = time.monotonic() + 5.0
        with self._sahte(senaryo="yerde", irtifa_m=30.0):
            yerde = kanit.yerde_mi(self.mav, ardisik=3, tavan_m=1.0)
        self.assertTrue(yerde, "ON_KAYIT G3: ON_GROUND + dusuk irtifa "
                               "akisinda gercek cerceveden kanit olusmadi")

    # --- G4 ---
    def test_G4_havadayken_inis_kaniti_yok(self):
        self.mav.inis_kaniti_deadline_monotonic = time.monotonic() + 2.0
        with self._sahte(senaryo="ucus", irtifa_m=30.0):
            yerde = kanit.yerde_mi(self.mav, ardisik=3, tavan_m=1.0)
        self.assertFalse(yerde, "ON_KAYIT G4: IN_AIR akisinda yerde_mi True "
                                "dondu — fail-closed bozuldu")

    # --- G5a (KAPI: sizinti yok) ---
    def test_G5a_yabanci_sysid_degeri_asla_donmez(self):
        """Yabancinin irtifasi kasten +100 m: sizarsa deger ele verir."""
        okuyucu = self._okuyucu()
        gorulen = []
        with self._sahte(senaryo="yabanci", irtifa_m=30.0) as sp:
            bitis = time.monotonic() + 2.0
            while time.monotonic() < bitis:
                deger = okuyucu.irtifa_m()
                if deger is not None:
                    gorulen.append(deger)
                time.sleep(0.02)
            self.assertGreater(sp.gonderilen["yabanci_konum"], 0,
                               "on kosul: yabanci paket hic gonderilmedi")
        if gorulen:
            self.assertLess(
                max(gorulen), 40.0,
                f"ON_KAYIT G5: yabanci sysid {YABANCI_SYSID} irtifasi (130 m) "
                f"sizdi: max={max(gorulen)}")

    # --- G6 ---
    def test_G6_donuk_saat_yasi_yenilemez(self):
        """time_boot_ms ilerlemezse tekrar paketleri ornegi tazeleyemez."""
        okuyucu = self._okuyucu()
        with self._sahte(senaryo="donuk-saat", irtifa_m=30.0):
            self.assertTrue(_bekle(lambda: okuyucu.irtifa_m() is not None),
                            "ilk paket de kabul edilmedi (on kosul)")
            # Yayin SURUYOR; ama boot zamani ilerlemedigi icin yas donmuyor.
            bayatladi = _bekle(lambda: okuyucu.irtifa_m() is None,
                               tavan_s=TELEMETRI_IRTIFA_TAZELIK_S * 6)
        self.assertTrue(bayatladi,
                        "ON_KAYIT G6: donuk saatli tekrar paketleri ornegin "
                        "yasini yeniledi — replay korumasi calismiyor")

    # --- G7 ---
    def test_G7_yayin_durunca_bayatlar(self):
        okuyucu = self._okuyucu()
        sp = self._sahte(senaryo="ucus", irtifa_m=30.0)
        sp.baslat()
        self.assertTrue(_bekle(lambda: okuyucu.irtifa_m() is not None))
        self.assertIsNotNone(okuyucu.irtifa_m(), "pencere icinde deger VAR")
        sp.dur()
        self.assertTrue(_bekle(lambda: okuyucu.irtifa_m() is None,
                               tavan_s=TELEMETRI_IRTIFA_TAZELIK_S * 6),
                        "ON_KAYIT G7: yayin durdu ama deger bayatlamadi")


@unittest.skipIf(mavutil is None, "pymavlink kurulu degil")
class D389Kapilari(unittest.TestCase):
    """D-389 karari uygulandi: D-387'nin iki bulgusu kapandi.

    Bu sinif onceki `AcikBulgular` karakterizasyon testlerinin BILEREK
    guncellenmis halidir (D-387 §4'te ilan edildigi gibi). Olcutler
    `results/d389_karar/ON_KAYIT.md` §2'de uygulamadan ONCE yazildi.
    P1 on kaydinin ozgun G3 ve G5(2) olcutleri artik GEVSETILMEDEN gecer.
    """

    def setUp(self):
        self.mav, self.port = _dinleyici()
        self.addCleanup(self.mav.close)

    def _sahte(self, **kw):
        sp = SahtePixhawk(f"udpout:127.0.0.1:{self.port}", **kw)
        self.addCleanup(sp.dur)
        return sp

    def test_K1_alcalma_sirasinda_baslatilan_dogrulama_TEMASI_bekliyor(self):
        """D-387/G3 OZGUN olcut: alcalan profil + son tarih -> True."""
        self.mav.inis_kaniti_deadline_monotonic = time.monotonic() + 10.0
        with self._sahte(senaryo="inis", irtifa_m=3.0, inis_suresi_s=1.0):
            sonuc = kanit.yerde_mi(self.mav, ardisik=3, tavan_m=1.0)
        self.assertTrue(sonuc, "ON_KAYIT K1: alcalma sirasinda baslatilan "
                               "dogrulama temasi bekleyip kanit uretmeli (A2)")

    def test_K2_soket_birikintisi_kaniti_dusuremez(self):
        """Temas SONRASI cagri, birikmis eski IN_AIR'lere ragmen True."""
        with self._sahte(senaryo="inis", irtifa_m=3.0, inis_suresi_s=1.0):
            time.sleep(1.6)          # arac indi; sokette eski IN_AIR birikti
            self.mav.inis_kaniti_deadline_monotonic = time.monotonic() + 5.0
            sonuc = kanit.yerde_mi(self.mav, ardisik=3, tavan_m=1.0)
        self.assertTrue(sonuc, "ON_KAYIT K2: soket birikintisindeki eski "
                               "IN_AIR paketleri kaniti dusurdu")

    def test_K3_havada_asla_yerde_denmez(self):
        """Fail-closed korunmus: bastan sona IN_AIR -> sure dolar, False."""
        self.mav.inis_kaniti_deadline_monotonic = time.monotonic() + 1.5
        with self._sahte(senaryo="ucus", irtifa_m=30.0):
            t0 = time.monotonic()
            sonuc = kanit.yerde_mi(self.mav, ardisik=3, tavan_m=1.0)
            gecen = time.monotonic() - t0
        self.assertFalse(sonuc, "ON_KAYIT K3: IN_AIR akisinda True dondu — "
                                "fail-closed BOZULDU")
        self.assertGreaterEqual(gecen, 1.0,
                                "sure dolmadan False dondu — A2 beklemiyor")

    def test_K4_yabanci_trafik_altinda_erisilebilirlik(self):
        """D-387/G5(2) OZGUN olcut: erisilebilirlik >= %90, sizinti 0."""
        okuyucu = kanit.BagilIrtifaOkuyucu(self.mav, TELEMETRI_IRTIFA_TAZELIK_S,
                                           beklenen_sysid=SYSID)
        self.assertTrue(okuyucu.baslat())
        self.addCleanup(okuyucu.durdur)
        with self._sahte(senaryo="yabanci", irtifa_m=30.0) as sp:
            time.sleep(0.6)
            okumalar = []
            bitis = time.monotonic() + 1.5
            while time.monotonic() < bitis:
                okumalar.append(okuyucu.irtifa_m())
                time.sleep(0.01)
            self.assertGreater(sp.gonderilen["yabanci_konum"], 0)
        dolu = [d for d in okumalar if d is not None]
        oran = len(dolu) / len(okumalar)
        self.assertGreaterEqual(
            oran, 0.90,
            f"ON_KAYIT K4: yabanci trafik altinda erisilebilirlik "
            f"{oran:.1%} (< %90) — B1 uygulanmamis")
        self.assertTrue(all(d < 40.0 for d in dolu),
                        "ON_KAYIT K4: yabanci deger SIZDI — G5a bozuldu")

    def test_K5_yabanci_EXTENDED_inis_kanitini_dusuremez(self):
        """Beklenen sysid beyanliyken yabanci EXTENDED akisi kaniti bozamaz."""
        self.mav.inis_kaniti_deadline_monotonic = time.monotonic() + 6.0
        yerdeki = self._sahte(senaryo="yerde", sysid=SYSID)
        yerdeki.baslat()
        # Ayni porta YABANCI bir arac HAVADA oldugunu soyluyor:
        yabanci = self._sahte(senaryo="ucus", sysid=YABANCI_SYSID,
                              irtifa_m=130.0)
        yabanci.baslat()
        sonuc = kanit.yerde_mi(self.mav, ardisik=3, tavan_m=1.0,
                               beklenen_sysid=SYSID)
        self.assertTrue(sonuc, "ON_KAYIT K5: yabanci EXTENDED_SYS_STATE "
                               "inis kanitini dusurdu — B1 kardesi eksik")


@unittest.skipIf(mavutil is None, "pymavlink kurulu degil")
class SahteUretecSozlesmesi(unittest.TestCase):
    """Uretecin kendisi olcum araci: profili yanlissa kapi da yanlis olur."""

    def test_inis_profili_gercekten_alcaliyor(self):
        sp = SahtePixhawk("udpout:127.0.0.1:1", senaryo="inis", irtifa_m=3.0,
                          inis_suresi_s=1.0)
        sp._baslangic = time.monotonic()
        self.assertGreater(sp.anlik_irtifa_m(), 1.0, "baslangicta yuksek olmali")
        sp._baslangic = time.monotonic() - 2.0
        self.assertLess(sp.anlik_irtifa_m(), sp.inis_tavani_m,
                        "sure dolunca inis tavaninin altina inmeli")
        self.assertTrue(sp._yerde_mi(), "alcaldiktan sonra ON_GROUND olmali")

    def test_yerde_profili_temas_etmis_araci_taklit_ediyor(self):
        sp = SahtePixhawk("udpout:127.0.0.1:1", senaryo="yerde")
        sp._baslangic = time.monotonic()
        self.assertLess(sp.anlik_irtifa_m(), sp.inis_tavani_m,
                        "yerde senaryosu inis tavaninin altinda olmali")
        self.assertTrue(sp._yerde_mi())

    def test_ucus_profili_asla_yerde_demez(self):
        sp = SahtePixhawk("udpout:127.0.0.1:1", senaryo="ucus", irtifa_m=30.0)
        sp._baslangic = time.monotonic() - 60.0
        self.assertEqual(sp.anlik_irtifa_m(), 30.0)
        self.assertFalse(sp._yerde_mi(), "ucus senaryosu yerde diyemez")

    def test_donuk_saat_gercekten_donuk(self):
        sp = SahtePixhawk("udpout:127.0.0.1:1", senaryo="donuk-saat")
        sp._baslangic = time.monotonic() - 1.0
        ilk = sp._time_boot_ms()
        sp._baslangic = time.monotonic() - 5.0
        self.assertEqual(sp._time_boot_ms(), ilk,
                         "donuk-saat senaryosunda boot zamani ilerlememeli")

    def test_gecersiz_senaryo_reddedilir(self):
        with self.assertRaises(ValueError):
            SahtePixhawk("udpout:127.0.0.1:1", senaryo="yok")
        with self.assertRaises(ValueError):
            SahtePixhawk("udpout:127.0.0.1:1", sysid=0)


if __name__ == "__main__":
    unittest.main()
