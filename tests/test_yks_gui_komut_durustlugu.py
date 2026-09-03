"""NEDEN: Hakem ekranı yalnız gerçekten iletilen ARM, DISARM ve paraşüt
komutları için başarı durumu göstermeli; iletim yokluğu operatör onayı değildir.
"""

import sys
import time
import unittest
from pathlib import Path
from unittest import mock


KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "comms"))

import yks_gui  # noqa: E402
from protocol import decode  # noqa: E402


IHA_ADRESI = ("127.0.0.1", 5006)


class _SahteWidget:
    def __init__(self, **ayarlar):
        self.ayarlar = dict(ayarlar)

    def config(self, **ayarlar):
        self.ayarlar.update(ayarlar)

    def cget(self, ad):
        return self.ayarlar.get(ad)


class YksKomutDurustluguTests(unittest.TestCase):
    def _arayuz(self, arm_acik=False, adres_var=False):
        arayuz = object.__new__(yks_gui.YksArayuz)
        arayuz.arm_acik = arm_acik
        arayuz.arm_durum_zamani = time.monotonic()
        arayuz.arm_bekleyen_komut = None
        arayuz.arm_ack_zamani = None
        arayuz._kritik_teyit = {}
        arayuz.link = mock.Mock()
        arayuz.son_adr = {"iha": IHA_ADRESI} if adres_var else {}
        arayuz._logla = mock.Mock()
        arayuz.btn_arm = _SahteWidget(
            state="normal",
            text="DISARM (A)" if arm_acik else "ARM (A)",
            bg=yks_gui.KIRMIZI if arm_acik else "#232e3a",
        )
        arayuz.lbl_arm = _SahteWidget(
            text=("SİSTEM: ARM — uçuşa hazır" if arm_acik
                  else "SİSTEM: DISARM — güvenli"),
            fg=yks_gui.SARI if arm_acik else yks_gui.SOLUK,
        )
        arayuz.btn_firlat = _SahteWidget(
            state="normal" if arm_acik else "disabled",
            bg=yks_gui.SARI if arm_acik else "#232e3a",
        )
        arayuz.parasut_teyit = 99.0
        arayuz.btn_parasut = _SahteWidget(
            state="normal", bg=yks_gui.KIRMIZI,
            text="EMİN MİSİN? tekrar bas (3 sn)",
        )
        # P9a (D-393): parasut artik ACK'li tekrarla gider; ayni durustluk
        # sozlesmesi AckliTekrar.baslat -> _ham_gonder uzerinden korunur.
        arayuz.parasut_tekrar = yks_gui.AckliTekrar(
            arayuz._ham_gonder, yks_gui.PARASUT_TEKRAR_ARALIGI_S,
            yks_gui.PARASUT_TEKRAR_UST_SINIRI)
        arayuz.parasut_ack_zamani = None
        arayuz.kok = mock.Mock()
        arayuz.arm_tekrar = yks_gui.AckliTekrar(
            arayuz._ham_gonder, yks_gui.ARM_TEKRAR_ARALIGI_S,
            yks_gui.ARM_TEKRAR_UST_SINIRI)
        arayuz._ceza_ekle = mock.Mock()
        arayuz._ucus = mock.Mock()
        return arayuz

    @staticmethod
    def _arm_teyitli(arayuz):
        arayuz.arm_degistir()             # ilk tık: ağ çıktısı yok
        arayuz.link.send.assert_not_called()
        arayuz._logla.reset_mock()
        arayuz.arm_degistir()             # ikinci tık: gerçek istek

    def _komut_dogrula(self, arayuz, beklenen_komut):
        arayuz.link.send.assert_called_once()
        veri, hedef = arayuz.link.send.call_args.args
        mesaj = decode(veri)
        self.assertEqual("CMD", mesaj["type"])
        self.assertEqual(beklenen_komut, mesaj["cmd"])
        self.assertEqual("iha", mesaj["hedef"])
        self.assertRegex(mesaj.get("oturum", ""), r"^[A-Za-z0-9_-]{16,64}$")
        self.assertEqual(IHA_ADRESI, hedef)

    def _kirmizi_hata_dogrula(self, arayuz, komut):
        arayuz.link.send.assert_not_called()
        arayuz._logla.assert_called_once()
        metin, renk = arayuz._logla.call_args.args
        self.assertIn("GÖNDERİLEMEDİ", metin)
        self.assertIn(komut, metin)
        self.assertEqual("kirmizi", renk)

    def _kirmizi_hata_dogrula_gonderim(self, arayuz, komut):
        """Taşıyıcı çağrıldı ama PATLADI: yine tek kırmızı GÖNDERİLEMEDİ."""
        arayuz._logla.assert_called_once()
        metin, renk = arayuz._logla.call_args.args
        self.assertIn("GÖNDERİLEMEDİ", metin)
        self.assertIn(komut, metin)
        self.assertEqual("kirmizi", renk)

    def test_arm_adres_yokken_durum_ve_ekran_degismez(self):
        arayuz = self._arayuz()

        self._arm_teyitli(arayuz)

        self._kirmizi_hata_dogrula(arayuz, "ARM")
        self.assertFalse(arayuz.arm_acik)
        self.assertEqual("normal", arayuz.btn_arm.cget("state"))
        self.assertEqual("ARM (A)", arayuz.btn_arm.cget("text"))
        self.assertEqual("disabled", arayuz.btn_firlat.cget("state"))
        self.assertNotIn("uçuşa hazır", arayuz.lbl_arm.cget("text"))

    def test_arm_adres_varken_ack_ve_heartbeat_gelmeden_baslamis_sayilmaz(self):
        arayuz = self._arayuz(adres_var=True)

        self._arm_teyitli(arayuz)

        self._komut_dogrula(arayuz, "ARM")
        self.assertFalse(arayuz.arm_acik)
        self.assertEqual("ARM", arayuz.arm_bekleyen_komut)
        self.assertIn("BEKLENİYOR", arayuz.btn_arm.cget("text"))
        self.assertNotIn("uçuşa hazır", arayuz.lbl_arm.cget("text"))
        self.assertEqual("disabled", arayuz.btn_firlat.cget("state"))

    def test_disarm_adres_yokken_durum_ve_ekran_degismez(self):
        arayuz = self._arayuz(arm_acik=True)

        self._arm_teyitli(arayuz)

        self._kirmizi_hata_dogrula(arayuz, "DISARM")
        self.assertTrue(arayuz.arm_acik)
        self.assertEqual("normal", arayuz.btn_arm.cget("state"))
        self.assertEqual("DISARM (A)", arayuz.btn_arm.cget("text"))
        self.assertEqual("normal", arayuz.btn_firlat.cget("state"))
        self.assertNotIn("DISARM", arayuz.lbl_arm.cget("text"))
        self.assertNotIn("güvenli", arayuz.lbl_arm.cget("text"))

    def test_disarm_adres_varken_ack_ve_heartbeat_gelmeden_guvenli_sayilmaz(self):
        arayuz = self._arayuz(arm_acik=True, adres_var=True)

        self._arm_teyitli(arayuz)

        self._komut_dogrula(arayuz, "DISARM")
        self.assertTrue(arayuz.arm_acik)
        self.assertEqual("DISARM", arayuz.arm_bekleyen_komut)
        self.assertIn("BEKLENİYOR", arayuz.btn_arm.cget("text"))
        self.assertNotIn("güvenli", arayuz.lbl_arm.cget("text"))
        self.assertEqual("disabled", arayuz.btn_firlat.cget("state"))

    # ── Teyit penceresi ile EKRAN arasındaki bağ ────────────────────────────
    # NEDEN: iki-tık teyidinde ikinci tık anahtarı tüketir. Komut o tıkta
    # başarısız olursa (UDP adresi yok / gönderim hatası) BEKLEYEN TEYİT
    # KALMAZ; düğme "ARM? TEKRAR BAS" derse hakem, var olmayan bir bekleyen
    # onay görür — bu dosyanın sözleşmesiyle aynı sınıf yanıltma.
    def test_teyit_tuketilip_gonderim_dusunce_dugme_gercege_doner(self):
        arayuz = self._arayuz(adres_var=True)
        arayuz.link.send.side_effect = OSError("ağ yok")

        self._arm_teyitli(arayuz)         # 1. tık teyit, 2. tık başarısız gönderim

        self._kirmizi_hata_dogrula_gonderim(arayuz, "ARM")
        self.assertEqual({}, arayuz._kritik_teyit,
                         "gönderim düştü: bekleyen teyit KALMAMALI")
        self.assertIsNone(arayuz.arm_bekleyen_komut)
        self.assertFalse(arayuz.arm_acik)
        self.assertEqual("ARM (A)", arayuz.btn_arm.cget("text"))
        self.assertEqual("normal", arayuz.btn_arm.cget("state"))
        self.assertEqual("disabled", arayuz.btn_firlat.cget("state"))

    def test_gonderim_dustukten_sonraki_tik_YENI_teyit_turu_baslatir(self):
        arayuz = self._arayuz(adres_var=True)
        arayuz.link.send.side_effect = OSError("ağ yok")

        self._arm_teyitli(arayuz)
        self.assertEqual(1, arayuz.link.send.call_count)

        arayuz.arm_degistir()             # 3. tık: DOĞRUDAN ARM ETMEZ
        self.assertEqual(1, arayuz.link.send.call_count,
                         "3. tık yeni bir teyit turu başlatmalı, komut GÖNDERMEMELİ")
        self.assertEqual("ARM? TEKRAR BAS", arayuz.btn_arm.cget("text"))
        self.assertIsNone(arayuz.arm_bekleyen_komut)
        self.assertFalse(arayuz.arm_acik)

        arayuz.arm_degistir()             # 4. tık: teyit tamam, yeniden denenir
        self.assertEqual(2, arayuz.link.send.call_count)

    def test_disarm_teyidi_tuketilip_gonderim_dusunce_dugme_gercege_doner(self):
        arayuz = self._arayuz(arm_acik=True, adres_var=True)
        arayuz.link.send.side_effect = OSError("ağ yok")

        self._arm_teyitli(arayuz)

        self._kirmizi_hata_dogrula_gonderim(arayuz, "DISARM")
        self.assertEqual({}, arayuz._kritik_teyit)
        self.assertTrue(arayuz.arm_acik)
        self.assertEqual("DISARM (A)", arayuz.btn_arm.cget("text"))
        self.assertEqual("normal", arayuz.btn_arm.cget("state"))

    def test_bekleyen_teyit_varken_dugme_TEKRAR_BAS_der(self):
        """Pozitif kontrol: yukarıdaki 'gerçeğe dönüş' teyidi gizlemiyor."""
        arayuz = self._arayuz(adres_var=True)

        arayuz.arm_degistir()             # yalnız 1. tık

        arayuz.link.send.assert_not_called()
        self.assertEqual("ARM? TEKRAR BAS", arayuz.btn_arm.cget("text"))
        self.assertEqual(yks_gui.SARI, arayuz.btn_arm.cget("bg"))
        self.assertIn("ARM", arayuz._kritik_teyit)

    def _acil_arayuz(self):
        arayuz = self._arayuz(adres_var=True)
        arayuz.acil_bekleyen_komut = None
        arayuz.acil_ack_zamani = None
        arayuz.acil_tekrar = yks_gui.AckliTekrar(
            arayuz._ham_gonder, yks_gui.ARM_TEKRAR_ARALIGI_S,
            yks_gui.ARM_TEKRAR_UST_SINIRI)
        arayuz.btn_rtl = _SahteWidget(state="normal", bg=yks_gui.KIRMIZI,
                                      text="ACİL RTL")
        arayuz.btn_land = _SahteWidget(state="normal", bg=yks_gui.KIRMIZI,
                                       text="ACİL LAND")
        arayuz.lbl_acil = _SahteWidget(text="", fg=yks_gui.SOLUK)
        return arayuz

    def test_acil_RTL_teyidi_tuketilip_gonderim_dusunce_dugme_gercege_doner(self):
        """Aynı sızıntı RTL/LAND'de de olmamalı (aynı `_kritik_teyit` kapısı)."""
        arayuz = self._acil_arayuz()

        arayuz.acil_komut("RTL")          # 1. tık: teyit ister, ağ çıktısı YOK
        arayuz.link.send.assert_not_called()
        self.assertEqual("RTL? TEKRAR BAS", arayuz.btn_rtl.cget("text"))
        self.assertIn("RTL", arayuz._kritik_teyit)

        arayuz.link.send.side_effect = OSError("ağ yok")
        arayuz.acil_komut("RTL")          # 2. tık: teyit tüketilir, gönderim düşer

        self.assertEqual({}, arayuz._kritik_teyit,
                         "gönderim düştü: bekleyen teyit KALMAMALI")
        self.assertIsNone(arayuz.acil_bekleyen_komut)
        self.assertEqual("ACİL RTL", arayuz.btn_rtl.cget("text"))
        self.assertEqual(yks_gui.KIRMIZI, arayuz.btn_rtl.cget("bg"))

        arayuz.acil_komut("RTL")          # 3. tık: YENİ teyit turu, komut YOK
        self.assertEqual(1, arayuz.link.send.call_count)
        self.assertEqual("RTL? TEKRAR BAS", arayuz.btn_rtl.cget("text"))

    def test_parasut_teyit_zamanlayicisi_ucustaki_komut_metnini_EZMEZ(self):
        """`parasut()` içindeki geri alma zamanlayıcısı komut yolunu ezmemeli."""
        arayuz = self._arayuz(adres_var=True)
        arayuz.parasut_teyit = 0.0        # bekleyen teyit YOK

        with mock.patch.object(yks_gui.time, "time", return_value=100.0):
            arayuz.parasut()              # 1. tık: teyit (damga = 100.0)
            arayuz.parasut()              # 2. tık: PARACHUTE gider

        gonderim_metni = arayuz.btn_parasut.cget("text")
        self.assertEqual("PARAŞÜT GÖNDERİLDİ — İHA ACK bekleniyor", gonderim_metni)

        arayuz._parasut_teyit_sondur(100.0)   # zamanlayıcı 3,2 sn sonra ateşler

        self.assertEqual(gonderim_metni, arayuz.btn_parasut.cget("text"),
                         "uçuşta PARACHUTE varken düğme boşta görünemez")
        self.assertEqual("disabled", arayuz.btn_parasut.cget("state"))

    def test_parasut_teyidi_gonderim_olmadan_suresi_dolunca_silinir(self):
        """Karşı kontrol: komut çıkmadıysa teyit metni GERÇEKTEN temizlenir."""
        arayuz = self._arayuz(adres_var=True)
        arayuz.parasut_teyit = 0.0        # bekleyen teyit YOK

        with mock.patch.object(yks_gui.time, "time", return_value=100.0):
            arayuz.parasut()              # yalnız 1. tık

        self.assertEqual("EMİN MİSİN? tekrar bas (3 sn)",
                         arayuz.btn_parasut.cget("text"))

        arayuz._parasut_teyit_sondur(100.0)

        self.assertEqual("PARAŞÜT (manuel −50)", arayuz.btn_parasut.cget("text"))
        self.assertEqual(0.0, arayuz.parasut_teyit,
                         "pencere kapandı: bekleyen teyit damgası da SIFIRLANMALI")

    def test_parasut_adres_yokken_ceza_ve_basari_uydurmaz(self):
        arayuz = self._arayuz()

        with mock.patch.object(yks_gui.time, "time", return_value=100.0):
            arayuz.parasut()

        self._kirmizi_hata_dogrula(arayuz, "PARACHUTE")
        arayuz._ceza_ekle.assert_not_called()
        arayuz._ucus.assert_not_called()
        self.assertEqual(99.0, arayuz.parasut_teyit)
        self.assertEqual("normal", arayuz.btn_parasut.cget("state"))
        self.assertNotIn("AÇILDI", arayuz.btn_parasut.cget("text"))

    def test_parasut_adres_varken_eskisi_gibi_tetiklenir(self):
        arayuz = self._arayuz(adres_var=True)

        with mock.patch.object(yks_gui.time, "time", return_value=100.0):
            arayuz.parasut()

        self._komut_dogrula(arayuz, "PARACHUTE")
        arayuz._ceza_ekle.assert_called_once_with(
            50, "manuel paraşüt tetikleme (§2.2.4)")
        arayuz._ucus.assert_called_once_with(
            "PARAŞÜT İSTEĞİ GÖNDERİLDİ — ACK BEKLENİYOR (−50)",
            yks_gui.KIRMIZI)
        self.assertEqual("disabled", arayuz.btn_parasut.cget("state"))
        # D-403 (curutucu): dugme GONDERIMDE "ACILDI" diyemez — ACK yok daha.
        # "ACILDI ✓" yalniz IHA ACK'inde (o da Pixhawk COMMAND_ACK ACCEPTED).
        self.assertEqual("PARAŞÜT GÖNDERİLDİ — İHA ACK bekleniyor",
                         arayuz.btn_parasut.cget("text"))
        self.assertNotIn("AÇILDI", arayuz.btn_parasut.cget("text"))


if __name__ == "__main__":
    unittest.main()
