"""YKİ İHA bağlantı satırı: kısa heartbeat boşluğu SARI "ZAYIF", KIRMIZI değil.

NEDEN (19 Eylül hakem kaydı): kayıplı tünelde 1 Hz heartbeat ile İHA düğümü
1-2 sn içinde TAZE/BAYAT arasında gidip geliyordu (19:15:16 BAYAT, 19:15:17
TAZE; 19:16:02, 19:16:39, 19:17:52 aynı örüntü). Kırmızı "BAĞLANTI KAYBI"
eşiği `_durum_tazele`'deki `canli = 0.0 <= yas < 3.0` idi: 1 Hz'de 2-3 kopya
düşünce aşılıyor.

Davranış (yalnız gösterim, yalnız İHA satırı):
  yas < 3 sn                          → TAZE (değişmedi)
  3 sn ≤ yas ≤ YKS_TESPIT_TAZELIK_S   → SARI nokta, "(bağlantı ZAYIF)", kayıt ZAYIF
  yas > YKS_TESPIT_TAZELIK_S          → KIRMIZI "(BAĞLANTI KAYBI!)", kayıt BAYAT
İKA satırı değişmedi (3 sn İKA failsafe eşiğidir).

Kilitler:
  Z1  1 sn → yeşil, TAZE (regresyon)
  Z2  3,5 sn → SARI + "(bağlantı ZAYIF)", KAYBI yok; kayıt iha=ZAYIF,
      `bayat` alanı eski anlamını korur (iha listede)
  Z3  sınır: 5,0 sn ZAYIF; 5,1 sn KIRMIZI "(BAĞLANTI KAYBI!)", kayıt iha=BAYAT
  Z4  19 Eyl örüntüsü (heartbeat 3,4 sn gecikir, sonra akar) hiç KIRMIZI olmaz
  Z5  İKA satırı 3,5 sn'de yine KIRMIZI (bant yalnız İHA)
  Z6  güvenlik/kapı eşikleri GEVŞEMEDİ: `_iha_havada_mi` 3,5 sn'de False,
      `_arm_durumu_taze_mi` 3,5 sn'de False

Tk açılmaz, port bağlanmaz. Saat: `time.monotonic` sahte saatle yamanır.

KOSUM:
  O:\\navitas-local-train\\venv\\Scripts\\python.exe -B -m unittest discover \\
      -s tests -p "test_yks_baglanti_zayif.py"
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
from karar_sozlesmesi import YKS_TESPIT_TAZELIK_S  # noqa: E402
from protocol import heartbeat  # noqa: E402
from test_yks_operator_guvenligi import _taban_arayuz  # noqa: E402


class _Saat:
    def __init__(self):
        self.t = 5000.0

    def __call__(self):
        return self.t


class IhaBaglantiSatiri(unittest.TestCase):

    def setUp(self):
        self.saat = _Saat()
        yama = mock.patch.object(yks_gui.time, "monotonic", self.saat)
        yama.start()
        self.addCleanup(yama.stop)
        self.g = _taban_arayuz()
        self.seq = 0

    def _hb(self, dugum="iha", t=None):
        if t is not None:
            self.saat.t = 5000.0 + t
        self.seq += 1
        self.g._mesaj_isle(heartbeat(dugum, seq=self.seq, pixhawk_canli=True,
                                     armed=False, mod="AUTO"), None)

    def _tazele(self, t):
        self.saat.t = 5000.0 + t
        self.g._durum_tazele()
        nokta, metin = self.g.lbl_dugum["iha"]
        kayit = self.g._kanit_durumu_yaz.call_args
        return nokta.ayar.get("fg"), metin.ayar.get("text", ""), kayit

    def test_Z1_taze_yesil(self):
        self._hb(t=0.0)
        fg, metin, kayit = self._tazele(1.0)
        self.assertEqual(yks_gui.YESIL, fg)
        self.assertNotIn("ZAYIF", metin)
        self.assertNotIn("KAYBI", metin)
        self.assertIn("iha=TAZE", kayit.args[1])

    def test_Z2_kisa_bosluk_sari_zayif(self):
        self._hb(t=0.0)
        fg, metin, kayit = self._tazele(3.5)
        self.assertEqual(yks_gui.SARI, fg)
        self.assertIn("(bağlantı ZAYIF)", metin)
        self.assertNotIn("BAĞLANTI KAYBI", metin)
        self.assertIn("iha=ZAYIF", kayit.args[1])
        self.assertIn("iha", kayit.kwargs["bayat"],
                      "`bayat` alanının anlamı (>= 3 sn) değişmemeli")
        self.assertEqual(3.5, kayit.kwargs["yas_s"]["iha"])

    def test_Z3_sinir_ve_gercek_kayip_kirmizi(self):
        self._hb(t=0.0)
        fg, metin, _ = self._tazele(YKS_TESPIT_TAZELIK_S)
        self.assertEqual(yks_gui.SARI, fg)
        self.assertIn("ZAYIF", metin)
        fg, metin, kayit = self._tazele(YKS_TESPIT_TAZELIK_S + 0.1)
        self.assertEqual(yks_gui.KIRMIZI, fg)
        self.assertIn("(BAĞLANTI KAYBI!)", metin)
        self.assertIn("iha=BAYAT", kayit.args[1])

    def test_Z4_ondokuz_eylul_oruntusu_hic_kirmizi_olmaz(self):
        metinler, renkler = [], []
        self._hb(t=0.0)
        for t in (0.5, 1.5, 2.5, 3.1, 3.4):          # 2-3 kopya düştü
            fg, metin, _ = self._tazele(t)
            renkler.append(fg)
            metinler.append(metin)
        self._hb(t=3.5)                                # hat geri geldi
        for t in (3.6, 4.5):
            fg, metin, _ = self._tazele(t)
            renkler.append(fg)
            metinler.append(metin)
        self.assertNotIn(yks_gui.KIRMIZI, renkler, metinler)
        self.assertFalse(any("KAYBI" in m for m in metinler), metinler)
        self.assertTrue(any("ZAYIF" in m for m in metinler), metinler)

    def test_Z5_ika_satiri_degismedi(self):
        self._hb("ika", t=0.0)
        self.saat.t = 5003.5
        self.g._durum_tazele()
        nokta, metin = self.g.lbl_dugum["ika"]
        self.assertEqual(yks_gui.KIRMIZI, nokta.ayar.get("fg"))
        self.assertIn("(BAĞLANTI KAYBI!)", metin.ayar.get("text", ""))
        self.assertIn("ika=BAYAT", self.g._kanit_durumu_yaz.call_args.args[1])

    def test_Z6_kapi_esikleri_gevsemedi(self):
        self._hb(t=0.0)
        self.saat.t = 5001.0
        self.assertTrue(self.g._iha_havada_mi())
        self.assertTrue(self.g._arm_durumu_taze_mi())
        self.saat.t = 5003.5                           # ekranda ZAYIF bandı
        self.g._durum_tazele()
        self.assertIn("ZAYIF", self.g.lbl_dugum["iha"][1].ayar.get("text", ""))
        self.assertFalse(self.g._iha_havada_mi(),
                         "havada kanıtı ekran bandıyla GEVŞEDİ")
        self.assertFalse(self.g._arm_durumu_taze_mi(),
                         "ARM tazelik kapısı ekran bandıyla GEVŞEDİ")


if __name__ == "__main__":
    unittest.main()
