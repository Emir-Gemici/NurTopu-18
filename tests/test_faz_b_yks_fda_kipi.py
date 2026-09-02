"""CONTRACTS §6.7 — YKS `--fda` görev kipi (şartname §5.3.2 · 21 Eylül Adıyaman).

NEDEN (D-407 ölçümü): `yks_gui` yarışma günü görevine (§2.2 mancınık + paraşüt +
İKA) göre yazıldı. 21 Eylül'deki görev test uçuşu **çoklu rotorlu drone**'la
yapılır: İKA yok, paraşüt yok, mancınık yok, bütçe tek 10 dakika.

🔴 Kapatılan tıkanma: hakem onayının 2/2 adımı `ika_aktarim_kaniti_var()` istiyordu.
O uçuşta İKA olmadığı için kanıt **hiç gelmez** → onay tamamlanamaz, İHA'ya ACK
gitmez. Şartname §5.3.2 hakem onayını zorunlu kıldığından uçuş **geçersiz** olurdu.

Kilitler (kart: `CODEX_GOREV_YKS_FDA.md`):
  1  FDA'da 2/2 onay İKA kanıtı OLMADAN tamamlanır; link'e `ref_tip`'li ACK gider
  2  Yarışma kipinde (varsayılan) aynı senaryo REDDEDİLİR — regresyon yok
  3  FDA'da `parasut()` link'e HİÇBİR ŞEY yazmaz (düğme durumu tek savunma değil)
  4  FDA'da `ika_baslat()` IKA_GO yazmaz
  5  FDA'da FIRLATMA etiketi KALKIŞ; ARM kilidi damgayı hâlâ reddeder
  6  Bütçe: FDA'da `SARTNAME_FDA_OPERASYON_SURESI_S`, aksi hâlde İHA görev süresi
"""

import json
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
from karar_sozlesmesi import (SARTNAME_FDA_OPERASYON_SURESI_S,  # noqa: E402
                              SARTNAME_IHA_GOREV_SURESI_S)
from komut_tekrar import BOS  # noqa: E402
from protocol import ack  # noqa: E402
from test_ika_go_ackli_tekrar import _SahteSaat, _SahteWidget, _arayuz  # noqa: E402
from test_p9abc_yks import _p9_arayuz  # noqa: E402

ROTA = {"v": 1, "type": "OPEN_ROUTE", "seq": 41, "road": 2, "conf": 0.91,
        "ref_xy": [0.0, 0.0], "wp": [[1.0, 2.0], [3.0, 4.0]]}


def _onay_arayuzu(*, fda, ika_kaniti):
    """Hakem onayı yolunun dokunduğu alanlar (Tk'siz)."""
    saat = _SahteSaat()
    link = mock.Mock()
    link.send = mock.Mock(return_value=None)
    g = _arayuz(link, ("127.0.0.1", 5006), saat)
    g.rota = dict(ROTA)
    g.rota_yok = None
    g.rota_adr = ("127.0.0.1", 5005)
    g.onaylandi = False
    g.tespit_onayli = False
    g.iha_landed_seq = None
    g.t_iha1 = None
    g.ika_rota_ack = {ROTA["seq"]: time.time()} if ika_kaniti else {}
    g._tespiti_yaslandir = mock.Mock(return_value=False)
    g._aktarim_onay_dugmesini_kur = mock.Mock()
    g.fda_kipi = False
    if fda:
        g.fda_kipini_uygula()
    return g, link


def _gonderilen(link):
    """link.send çağrılarındaki çerçeveleri sözlük olarak döndür."""
    cikan = []
    for cagri in link.send.call_args_list:
        ham = cagri.args[0] if cagri.args else cagri.kwargs.get("veri")
        if isinstance(ham, (bytes, bytearray)):
            for satir in bytes(ham).decode("utf-8").splitlines():
                if satir.strip():
                    cikan.append(json.loads(satir))
    return cikan


class HakemOnayiFdaKipi(unittest.TestCase):
    def test_1_FDA_ika_kaniti_OLMADAN_onay_tamamlanir_ve_ACK_gider(self):
        g, link = _onay_arayuzu(fda=True, ika_kaniti=False)
        g.onayla()                       # 1/2 — tespit doğrulandı
        self.assertTrue(g.tespit_onayli)
        self.assertFalse(g.onaylandi, "1/2 adımında ACK gitmemeli")
        g.onayla()                       # 2/2 — FDA'da İKA kanıtı aranmaz
        self.assertTrue(g.onaylandi, "FDA'da 2/2 onay TAMAMLANMALI (§5.3.2)")
        ackler = [m for m in _gonderilen(link) if m.get("type") == "ACK"]
        self.assertEqual(1, len(ackler), _gonderilen(link))
        self.assertEqual(ROTA["seq"], ackler[0]["ref"])
        self.assertEqual("yks", ackler[0].get("node"))
        self.assertEqual("OPEN_ROUTE", ackler[0].get("ref_tip"),
                         "ACK ref_tip taşımalı (§6.6 / T206)")

    def test_2_YARISMA_kipinde_ayni_senaryo_REDDEDILIR(self):
        g, link = _onay_arayuzu(fda=False, ika_kaniti=False)
        g.onayla()
        g.onayla()
        self.assertFalse(g.onaylandi,
                         "İKA kanıtı yokken yarışma kipinde onay VERİLMEZ (K8)")
        self.assertEqual([], [m for m in _gonderilen(link)
                              if m.get("type") == "ACK"])

    def test_2b_YARISMA_kipinde_ika_kaniti_varsa_onay_tamamlanir(self):
        """Pozitif kontrol: 2 numaralı testin reddi kanıt yokluğundandır."""
        g, link = _onay_arayuzu(fda=False, ika_kaniti=True)
        g.onayla()
        g.onayla()
        self.assertTrue(g.onaylandi)
        self.assertEqual(1, len([m for m in _gonderilen(link)
                                 if m.get("type") == "ACK"]))


class FdaKapaliDugmeler(unittest.TestCase):
    def test_3_FDA_parasut_link_e_HICBIR_SEY_yazmaz(self):
        g, saat = _p9_arayuz()
        g.fda_kipini_uygula()
        g.link.send.reset_mock()
        g.parasut()
        g.parasut()                      # iki adımlı teyit denemesi de geçmez
        self.assertEqual([], _gonderilen(g.link))
        self.assertEqual(BOS, g.parasut_tekrar.durum,
                         "FDA'da paraşüt tekrarı başlatılmamalı")
        self.assertEqual("PARAŞÜT (FDA dışı)", g.btn_parasut.ayarlar.get("text"))
        self.assertEqual("disabled", g.btn_parasut.ayarlar.get("state"))

    def test_3b_YARISMA_kipinde_parasut_iki_adimla_GIDER(self):
        """Pozitif kontrol: 3 numaralı testteki sessizlik FDA kilididir."""
        g, saat = _p9_arayuz()
        g.link.send.reset_mock()
        g.parasut()                      # 1. tık: teyit ister, komut yok
        self.assertEqual([], _gonderilen(g.link))
        g.parasut()                      # 2. tık: komut gider
        cmdler = [m for m in _gonderilen(g.link) if m.get("type") == "CMD"]
        self.assertTrue(cmdler, "yarışma kipinde paraşüt komutu gitmeli")
        self.assertEqual("PARACHUTE", cmdler[0].get("cmd"))

    def test_4_FDA_ika_baslat_IKA_GO_yazmaz(self):
        saat = _SahteSaat()
        link = mock.Mock()
        link.send = mock.Mock(return_value=None)
        g = _arayuz(link, ("127.0.0.1", 5006), saat)
        g.iha_landed_seq = 7             # yarışma kipinde izin verecek durum
        g.onaylandi = True
        g.fda_kipi = False
        g.fda_kipini_uygula()
        link.send.reset_mock()
        g.ika_baslat()
        self.assertEqual([], [m for m in _gonderilen(link)
                              if m.get("type") == "CMD"])
        self.assertEqual("İKA (FDA dışı)", g.btn_ika_go.ayarlar.get("text"))
        self.assertEqual("disabled", g.btn_ika_go.ayarlar.get("state"))

    def test_5_FDA_firlatma_etiketi_KALKIS_ve_ARM_kilidi_SURUYOR(self):
        g, saat = _p9_arayuz()
        g.fda_kipini_uygula()
        self.assertEqual("KALKIŞ", g.btn_firlat.ayarlar.get("text"))
        g.arm_acik = False               # ARM doğrulanmadı
        g._arm_durumu_taze_mi = mock.Mock(return_value=True)
        g._arm_ui_uygula = mock.Mock()
        g.firlatma()
        self.assertIsNone(g.t_iha0, "ARM olmadan KALKIŞ damgası atılamaz (D-393)")


class FdaButcesi(unittest.TestCase):
    def test_6_iha_limiti_kipe_gore(self):
        self.assertEqual(SARTNAME_IHA_GOREV_SURESI_S,
                         yks_gui.YksArayuz.IHA_LIMIT,
                         "sınıf varsayılanı yarışma günü kipidir")
        g, _ = _p9_arayuz()
        g.fda_kipini_uygula()
        self.assertEqual(SARTNAME_FDA_OPERASYON_SURESI_S, g.IHA_LIMIT)
        self.assertTrue(g.fda_kipi)
        self.assertEqual(SARTNAME_IHA_GOREV_SURESI_S,
                         yks_gui.YksArayuz.IHA_LIMIT,
                         "örnek düzeyinde ezilir; SINIF varsayılanı DEĞİŞMEZ")

    def test_6b_cli_fda_bayragi_var_ve_varsayilan_kapali(self):
        kaynak = (KOK / "comms" / "yks_gui.py").read_text(encoding="utf-8")
        self.assertIn('"--fda", action="store_true"', kaynak)
        self.assertIn("app.fda_kipini_uygula()", kaynak,
                      "--fda kipi uygulayıcıyı çağırmalı (yalnız bütçe değil)")
        self.assertIs(False, yks_gui.YksArayuz.fda_kipi)


if __name__ == "__main__":
    unittest.main()
