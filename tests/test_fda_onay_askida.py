"""FDA hakem onayı ASKISI: NO_ROUTE / düşük güven karesi onayı hemen SİLMEZ.

NEDEN (mimar, 19 Eylül): Jetson'un karar yumuşatıcısı NO_ROUTE'u beklemeden
geçirir; hakemin iki tıklaması birkaç saniye sürer. a2e69b9b'den sonra bile
tek bir NO_ROUTE / eşik altı OPEN_ROUTE karesi FDA onayını siliyordu.

Davranış (yalnız `fda_kipi`): onay ASKIYA alınır — askıdayken bayraklar
sıfırdır, ACK yok, düğme kapalı, etiket "ONAY ASKIDA — tespit N sn kayıp".
Aynı şerit, tüm kapılardan geçerek, SON KABUL EDİLEN rotanın monotonik
damgasından `YKS_TESPIT_TAZELIK_S` içinde dönerse onay geri gelir (2/2 ise
yeni seq'e ACK). Süre dolarsa ya da şerit değişirse onay düşer (bir kez log).

Kilitler:
  1   NO_ROUTE 1 sn → aynı şerit: 2/2 geri gelir + yeni seq'e ACK
  1b  NO_ROUTE 1 sn → aynı şerit: 1/2 geri gelir, ACK yok, 2. düğme açık
  2   6 sn boşluk → onay düşer, ACK yok, "ONAY DÜŞTÜ" bir kez
  2b  tik (`_durum_tazele` yolu) süre dolunca düşürür, bir kez loglar
  3   arada düşük güven karesi → taşınır
  3b  NO_ROUTE + düşük güven + NO_ROUTE karışık, pencere içinde → taşınır
  4   NO_ROUTE sonrası farklı şerit → düşer, ACK yok
  5   yarışma kipi → bugünkü sıfırlama, askı yok
  6   askıdayken `onayla()` (aynı seq tekrarı rota_yok'u temizlese bile)
      onay/ACK vermez; periyodik tazeleme düğmeyi AÇMAZ
  7   askıdan dönen rota kapılardan geçmeli: ankorsuz / bayat / İHA indi
  8   pencere NO_ROUTE anından değil SON KABUL EDİLEN rotadan ölçülür

Tk açılmaz, port bağlanmaz. Saat: `time.monotonic` sahte saatle yamanır.

KOSUM:
  O:\\navitas-local-train\\venv\\Scripts\\python.exe -B -m unittest discover \\
      -s tests -p "test_fda_onay_askida.py"
"""

import sys
import time
import unittest
from pathlib import Path
from unittest import mock

KOK = Path(__file__).resolve().parents[1]
for _y in (KOK / "comms", KOK / "codes", KOK / "tests"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

import yks_gui  # noqa: E402
from karar_sozlesmesi import YKS_TESPIT_TAZELIK_S  # noqa: E402
from test_fda_onay_yeni_seq import IHA_ADR, _ackler, _gui, _rota  # noqa: E402


class _Saat:
    def __init__(self, t=1000.0):
        self.t = float(t)

    def __call__(self):
        return self.t


def _no_route(seq):
    return {"v": 1, "type": "NO_ROUTE", "seq": seq, "sebep": "KORIDOR_DEGIL",
            "detay": "test"}


def _rota_ackleri(g):
    return [m["ref"] for m, _ in _ackler(g) if m.get("ref_tip") == "OPEN_ROUTE"]


def _satirlar(g, parca):
    return [s for _r, s in g.gunluk if parca in s]


class _SaatliTest(unittest.TestCase):
    def setUp(self):
        self.saat = _Saat()
        yama = mock.patch.object(yks_gui.time, "monotonic", self.saat)
        yama.start()
        self.addCleanup(yama.stop)

    def _git(self, t):
        """Sahte saati `t` sn'ye getir; İHA heartbeat'i taze `karar_yas` taşır."""
        self.saat.t = 1000.0 + t
        self.g.karar_yas_rx = (0.2, self.saat.t)

    def _kur(self, *, fda=True, tam=True, seq=201, road=2):
        self.g = _gui(fda=fda)
        self._git(0.0)
        self.g._mesaj_isle(_rota(seq, road=road), IHA_ADR)
        if not fda:
            self.g.ika_rota_ack[seq] = time.time()           # K8 kanıtı
        self.g.onayla()
        if tam:
            self.g.onayla()
        return self.g


class FdaOnayAskisi(_SaatliTest):

    def test_1_NO_ROUTE_1sn_sonra_ayni_serit_tam_onay_geri_gelir_ACK(self):
        g = self._kur()
        self.assertEqual([201], _rota_ackleri(g))
        self._git(0.5)
        g._mesaj_isle(_no_route(202), IHA_ADR)
        self.assertFalse(g.onaylandi, "askıdayken onay bayrağı açık kalmamalı")
        self.assertIn("ONAY ASKIDA", g.lbl_onay.ayarlar.get("text", ""))
        self.assertEqual("disabled", g.btn_onay.ayarlar.get("state"))
        g.onayla()
        self.assertEqual([201], _rota_ackleri(g), "askıdayken ACK gitti")
        self._git(1.0)
        g._mesaj_isle(_rota(203), IHA_ADR)
        self.assertTrue(g.onaylandi, "tek NO_ROUTE karesi tam onayı SİLDİ")
        self.assertEqual([201, 203], _rota_ackleri(g))
        self.assertIn("ONAYLANDI", g.btn_onay.ayarlar.get("text", ""))
        self.assertTrue(_satirlar(g, "askıdan döndü"), g.gunluk)

    def test_1b_birinci_asama_askidan_doner_ACK_yok(self):
        g = self._kur(tam=False)
        self._git(0.5)
        g._mesaj_isle(_no_route(202), IHA_ADR)
        self.assertFalse(g.tespit_onayli)
        self._git(1.0)
        g._mesaj_isle(_rota(203), IHA_ADR)
        self.assertTrue(g.tespit_onayli)
        self.assertFalse(g.onaylandi)
        self.assertEqual([], _rota_ackleri(g))
        self.assertEqual("normal", g.btn_onay.ayarlar.get("state"))
        self.assertIn("2) YKS'DE GÖRÜLDÜ", g.btn_onay.ayarlar.get("text", ""))
        g.onayla()
        self.assertEqual([203], _rota_ackleri(g))

    def test_2_6sn_bosluk_onay_duser_ACK_yok(self):
        g = self._kur()
        self._git(0.5)
        g._mesaj_isle(_no_route(202), IHA_ADR)
        self._git(6.0)
        g._mesaj_isle(_rota(203), IHA_ADR)
        self.assertFalse(g.onaylandi)
        self.assertFalse(g.tespit_onayli)
        self.assertEqual([201], _rota_ackleri(g))
        self.assertEqual(1, len(_satirlar(g, "ONAY DÜŞTÜ")), g.gunluk)
        self.assertIn("1) TESPİTİ DOĞRULA", g.btn_onay.ayarlar.get("text", ""))

    def test_2b_tik_suresi_dolunca_duser_bir_kez_loglar(self):
        g = self._kur()
        self._git(0.5)
        g._mesaj_isle(_no_route(202), IHA_ADR)
        self._git(3.0)
        g._onay_askisini_tazele()
        self.assertIn("ONAY ASKIDA — tespit 3 sn", g.lbl_onay.ayarlar["text"])
        self._git(YKS_TESPIT_TAZELIK_S + 0.5)
        g._onay_askisini_tazele()
        self.assertIn("ONAY DÜŞTÜ", g.lbl_onay.ayarlar["text"])
        self.assertEqual("disabled", g.btn_onay.ayarlar.get("state"))
        self._git(YKS_TESPIT_TAZELIK_S + 1.0)
        g._onay_askisini_tazele()
        g._mesaj_isle(_rota(203), IHA_ADR)
        self.assertFalse(g.onaylandi)
        self.assertEqual([201], _rota_ackleri(g))
        self.assertEqual(1, len(_satirlar(g, "ONAY DÜŞTÜ")), g.gunluk)

    def test_3_dusuk_guven_arada_tasir(self):
        g = self._kur()
        self._git(0.5)
        g._mesaj_isle(_rota(202, conf=0.01), IHA_ADR)
        self.assertFalse(g.onaylandi)
        self.assertIn("ONAY ASKIDA", g.lbl_onay.ayarlar.get("text", ""))
        self._git(1.0)
        g._mesaj_isle(_rota(203), IHA_ADR)
        self.assertTrue(g.onaylandi)
        self.assertEqual([201, 203], _rota_ackleri(g))

    def test_3b_karisik_kayip_kareler_pencere_icinde_tasir(self):
        g = self._kur()
        self._git(0.5)
        g._mesaj_isle(_no_route(202), IHA_ADR)
        self._git(1.0)
        g._mesaj_isle(_rota(203, conf=0.01), IHA_ADR)
        self._git(2.0)
        g._mesaj_isle(_no_route(204), IHA_ADR)
        self._git(3.0)
        g._mesaj_isle(_rota(205), IHA_ADR)
        self.assertTrue(g.onaylandi)
        self.assertEqual([201, 205], _rota_ackleri(g))

    def test_4_NO_ROUTE_sonrasi_farkli_serit_duser(self):
        g = self._kur(road=2)
        self._git(0.5)
        g._mesaj_isle(_no_route(202), IHA_ADR)
        self._git(1.0)
        g._mesaj_isle(_rota(203, road=1), IHA_ADR)
        self.assertFalse(g.onaylandi)
        self.assertFalse(g.tespit_onayli)
        self.assertEqual([201], _rota_ackleri(g))
        self.assertTrue(_satirlar(g, "SERIT DEGISTI"), g.gunluk)
        # Aynı şerit sonradan dönse de düşen onay GERİ GELMEZ.
        self._git(1.5)
        g._mesaj_isle(_rota(204, road=2), IHA_ADR)
        self.assertFalse(g.onaylandi)
        self.assertEqual([201], _rota_ackleri(g))

    def test_6_askidayken_onayla_ACK_uretmez_tazeleme_dugmeyi_acmaz(self):
        g = self._kur(tam=False)
        self._git(0.5)
        g._mesaj_isle(_no_route(202), IHA_ADR)
        self._git(0.7)
        g._mesaj_isle(_rota(201), IHA_ADR)       # eski seq'in geç tekrarı
        self.assertIsNone(g.rota_yok, "tekrar rota_yok'u temizlemeliydi")
        g._onay_dugmesini_tazele()
        self.assertEqual("disabled", g.btn_onay.ayarlar.get("state"),
                         "askıdayken periyodik tazeleme düğmeyi AÇTI")
        g.onayla()
        g.onayla()
        self.assertFalse(g.tespit_onayli)
        self.assertFalse(g.onaylandi)
        self.assertEqual([], _rota_ackleri(g), "askıdayken hakem ACK'i gitti")

    def test_7_ankorsuz_donus_tasinmaz(self):
        g = self._kur()
        self._git(0.5)
        g._mesaj_isle(_no_route(202), IHA_ADR)
        self._git(1.0)
        g._mesaj_isle(_rota(203, ref_xy=None), IHA_ADR)
        self.assertFalse(g.onaylandi)
        self.assertEqual([201], _rota_ackleri(g))

    def test_7b_bayat_donus_tasinmaz(self):
        g = self._kur()
        self._git(0.5)
        g._mesaj_isle(_no_route(202), IHA_ADR)
        self._git(1.0)
        g.karar_yas_rx = (YKS_TESPIT_TAZELIK_S + 5.0, self.saat.t)
        g._mesaj_isle(_rota(203), IHA_ADR)
        self.assertFalse(g.onaylandi)
        self.assertEqual([201], _rota_ackleri(g))

    def test_7c_iha_indiyse_donus_tasinmaz(self):
        g = self._kur()
        self._git(0.5)
        g._mesaj_isle(_no_route(202), IHA_ADR)
        g.iha_landed_seq = 3
        self._git(1.0)
        g._mesaj_isle(_rota(203), IHA_ADR)
        self.assertFalse(g.onaylandi)
        self.assertEqual([201], _rota_ackleri(g))

    def test_8_pencere_son_kabul_edilen_rotadan_olculur(self):
        g = self._kur()
        self._git(3.0)
        g._mesaj_isle(_rota(202), IHA_ADR)                 # taşındı, ACK 202
        self.assertEqual([201, 202], _rota_ackleri(g))
        self._git(3.0 + YKS_TESPIT_TAZELIK_S - 0.1)
        g._mesaj_isle(_no_route(203), IHA_ADR)
        self._git(3.0 + YKS_TESPIT_TAZELIK_S + 0.5)        # NO_ROUTE'tan 0,6 sn
        g._mesaj_isle(_rota(204), IHA_ADR)
        self.assertFalse(g.onaylandi,
                         "pencere NO_ROUTE anından ölçüldü (son rotadan değil)")
        self.assertEqual([201, 202], _rota_ackleri(g))


class YarismaKipiAskisiz(_SaatliTest):

    def test_5_yarisma_kipinde_NO_ROUTE_bugunku_gibi_sifirlar(self):
        g = self._kur(fda=False)
        self.assertTrue(g.onaylandi)
        self._git(0.5)
        g._mesaj_isle(_no_route(202), IHA_ADR)
        self.assertNotIn("ASKIDA", g.lbl_onay.ayarlar.get("text", ""))
        self._git(1.0)
        g._mesaj_isle(_rota(203), IHA_ADR)
        self.assertFalse(g.onaylandi)
        self.assertFalse(g.tespit_onayli)
        self.assertEqual([201], _rota_ackleri(g))
        self.assertEqual([], _satirlar(g, "ASKIDA"))

    def test_5b_yarisma_kipinde_dusuk_guven_bugunku_gibi_sifirlar(self):
        g = self._kur(fda=False, tam=False)
        self._git(0.5)
        g._mesaj_isle(_rota(202, conf=0.01), IHA_ADR)
        self._git(1.0)
        g._mesaj_isle(_rota(203), IHA_ADR)
        self.assertFalse(g.tespit_onayli)
        self.assertEqual([], _satirlar(g, "ASKIDA"))


if __name__ == "__main__":
    unittest.main()
