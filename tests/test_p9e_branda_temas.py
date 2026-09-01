"""P9e (D-391) — IKA VARISI: BRANDAYA TEMAS, SINIRDA DURMAK DEGIL.

Sartname SS7 Pgorev: "branda uzerine (H noktasi) fiziksel olarak temas" —
sinira girmek 0 puan. Zincirin iki yarisi:

  IHA yarisi (T150, olculdu): rotanin SON waypoint'i HB pedinin KUTUSUNDA
  biter (B_hedef_pedde 253/256; kadraj-disi HEDEF_YOK fail-closed).

  IKA yarisi (BU KILIT): `navigate` son waypoint'e FINAL_WP_RADIUS icinde
  yaklasinca varmis sayar. Temas garantisi GEOMETRIK esitsizlikten gelir:

      FINAL_WP_RADIUS < HB_KENAR_M / 2
      (0,3 m)           (1,0 m)

  Arac merkezi ped merkezine <= 0,3 m'deyken ped kenarina >= 0,7 m iceride
  kalir -> govde/teker pedin USTUNDEDIR (fiziksel temas). Sinirda durma
  ancak FINAL_WP_RADIUS ped yari-kenarini asarsa mumkun olur; bu test o
  gerilemeyi kilitler.

⚠ Gazebo'da fiziksel temas kosusu BU MAKINEDE OLCULEMEZ (gz/WSL yok);
Faz C provasinda (Gazebo'lu makine) kosulacak. OLCULEMEDI != GECTI —
buradaki kanit kinematik + geometrik katmandir.
"""
import sys
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
for _y in (KOK / "codes", KOK / "simulation" / "scripts"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

import ika_nav  # noqa: E402
import ika_surucu  # noqa: E402
from karar_sozlesmesi import HB_KENAR_M  # noqa: E402


class GeometrikSozlesme(unittest.TestCase):
    def test_varis_yaricapi_ped_yari_kenarinin_icinde(self):
        """FINAL_WP_RADIUS < HB_KENAR_M/2 — temasin geometrik garantisi."""
        self.assertLess(
            ika_nav.FINAL_WP_RADIUS, HB_KENAR_M / 2.0,
            "varis yaricapi ped yari-kenarini asiyor: IKA pede TEMAS ETMEDEN "
            "'vardim' diyebilir — SS7 Pgorev 0 puan riski")

    def test_varis_yaricapi_guvenli_pay_birakiyor(self):
        """Merkez sapmasi + yaricap toplami ped icinde kalmali (>= 0,5 m pay).

        T150 olcumu waypoint'i ped KUTUSUNDA garanti eder (merkezinde degil);
        kutu ici en kotu sapma yari-kenara yaklasabilir. Yaricapin kucuklugu
        bu sapmaya karsi tampondur; pay 0,5 m'nin altina dusurulecekse once
        ped-ici waypoint dagilimi OLCULMELIDIR (D-107).
        """
        pay = HB_KENAR_M / 2.0 - ika_nav.FINAL_WP_RADIUS
        self.assertGreaterEqual(
            pay, 0.5,
            f"varis payi {pay:.2f} m — gerileme: yaricap buyutulmus")

    def test_son_waypoint_dar_yaricap_kullaniyor(self):
        """navigate SON waypoint'te FINAL_WP_RADIUS, oncekilerde WP_RADIUS
        kullanmali — mutasyon kilidi (D-370 sinifi)."""
        kod = (KOK / "simulation" / "scripts" / "ika_nav.py").read_text(
            encoding="utf-8")
        govde = "\n".join(s for s in kod.splitlines()
                          if not s.lstrip().startswith("#"))
        kalip = ("hedef_yaricapi = FINAL_WP_RADIUS "
                 "if idx == len(wps) - 1 else WP_RADIUS")
        self.assertIn(kalip, govde, "son-waypoint dar yaricap secimi kayip")
        mutant = govde.replace(kalip, "hedef_yaricapi = WP_RADIUS", 1)
        self.assertNotEqual(govde, mutant, "MUTASYON UYGULANMADI")


class KinematikTemasKaniti(unittest.TestCase):
    """SahteSurucu ile: navigate ped merkezine surer, temas bolgesinde durur."""

    def tearDown(self):
        ika_nav.surucu_ayarla(None)

    def test_navigate_ped_icinde_durur(self):
        ped_merkez = (10.0, 5.0)
        # Yaklasan poz dizisi: son poz ped merkezine 0,2 m (< FINAL_WP_RADIUS)
        pozlar = [
            (7.0, 5.0, 0.0, 0.0), (8.0, 5.0, 0.0, 0.0),
            (9.0, 5.0, 0.0, 0.0), (9.5, 5.0, 0.0, 0.0),
            (9.8, 5.0, 0.0, 0.0),
        ]
        surucu = ika_surucu.SahteSurucu(pozlar=pozlar)
        ika_nav.surucu_ayarla(surucu)
        sonuc = ika_nav.navigate([(7.0, 5.0), ped_merkez], verbose=False)
        self.assertTrue(sonuc, "kisa rota tamamlanmali")
        # Son gorulen poz ped SINIRLARININ icinde mi (temas bolgesi)?
        son_x, son_y = 9.8, 5.0
        self.assertLess(abs(son_x - ped_merkez[0]), HB_KENAR_M / 2.0,
                        "arac ped disinda durdu — temas yok")
        self.assertLess(abs(son_y - ped_merkez[1]), HB_KENAR_M / 2.0)
        self.assertEqual(surucu.komutlar[-1], (0.0, 0.0),
                         "varista durdurma komutu olmali")

    def test_ped_disi_uzaklikta_varmis_saymaz(self):
        """0,5 m uzakta (yaricap disi) 'vardim' diyemez — ilerlemeye calisir."""
        ped_merkez = (10.0, 5.0)
        # Sabit poz: 9.5 → uzaklik 0,5 m > FINAL_WP_RADIUS(0,3) — varilmadi.
        surucu = ika_surucu.SahteSurucu(pozlar=[(9.5, 5.0, 0.0, 0.0)],
                                        arizali_cagrilar=set(range(4, 99)))
        ika_nav.surucu_ayarla(surucu)
        # Ariza enjeksiyonu donguyu sonlandirir (sonsuz kosmasin); onemli
        # olan varmis SAYMAMASI: False donmeli, True degil.
        sonuc = ika_nav.navigate([(9.0, 5.0), ped_merkez], verbose=False)
        self.assertFalse(sonuc,
                         "0,5 m uzakligi varis saydi — SS7 temas kaybi")


if __name__ == "__main__":
    unittest.main()
