"""T224 (D-441) — YKS K8 ERKEN ACK TAMPONU: İKA'nın OPEN_ROUTE ACK kopyası
YKS'ye OPEN_ROUTE'tan ÖNCE gelirse hakem kanıtı KAYBOLMAZ.

ÖLÇÜLEN KUSUR (T213-B, 10 Eylül 10:0x, `gt 1 orta 44`; README_T213B §6.2,
D-441): loopback'te İKA, İHA'nın YKS'ye ikinci datagramından hızlıydı; İKA'nın
ACK kopyası YKS'ye OPEN_ROUTE'tan önce ulaştı. `comms/yks_gui.py` `_ack_isle`:

    if (self.rota and ref == self.rota["seq"] and ref_tip in (None, OPEN_ROUTE)
            and ref not in self.ika_rota_ack):

`self.rota` boş (ya da başka seq) olduğu için kopya ATILIYORDU. İHA 'ika'
ACK'ını gördüğü için İKA'ya OPEN_ROUTE'u tekrar göndermez → İKA kopyayı BİR
DAHA üretmez → `ika_rota_ack` hiç dolmaz → hakem 2/2 fail-closed kilitli kalır
(sim'de çıkış 3, 45 koşumun 3'ü). Üretim YKS'de aynı sıra aynı sonucu verir.

Çözüm (`simulation/mujoco/sim_hakem.py` kalıbı): `ref_tip="OPEN_ROUTE"` taşıyan
erken kopya `ref` ile `IKA_ROTA_ACK_ERKEN_TAMPON_S` (5 s, monotonik) saklanır;
OPEN_ROUTE gelince eşlenir, `ika_rota_ack` + `IKA_AKTARIM_KANITI` (`erken=true`)
yazılır. Süresi dolan kopya kanıt SAYILMAZ (fail-closed). Anlık (OPEN_ROUTE →
ACK) davranış ve kayıt satırı DEĞİŞMEDİ.

Kapılar:
  E1  GERÇEK UDP loopback (gerçek `_dinle` iş parçacığı + gerçek `_tik`):
      ACK, OPEN_ROUTE'tan ÖNCE varır (kuyruk sırası ölçülür) → ika_rota_ack
      dolu, IKA_AKTARIM_KANITI (erken=true) diske ROTA_ALINDI'dan SONRA düşer.
  E2  Ters sıra (OPEN_ROUTE → ACK): aynı sonuç; kayıt satırında `erken` alanı
      YOK (anlık yol birebir), tampon boş.
  E3  Tampon süresi dolunca → kanıt YOK, tampon boşalır, 2/2 reddi sürer.
  E4  Süre sınırının içinde → eşlenir.
  E5  `ref_tip`siz erken ACK tamponlanmaz (eski davranış aynen: kanıt yok).
  E6  Başka seq eşlenmez; mevcut rota varken YENİ seq için erken ACK eşlenir.
  E7  İHA düğümünün ACK'ı tamponlanmaz.
  E8  Uçtan uca hakem: erken ACK → OPEN_ROUTE → 1/2 → 2/2 = HAKEM_ONAYI_2,
      ACK link'e yazılır (kanıt hakem ekranında kaybolmadı).
  E9  Sabit gerekçeli: 5 s ≥ 2 × İHA tekrar penceresi (8 × 0,25 s).
  E10 Yinelenen erken kopya ilk damgayı korur; bayat kayıtlar temizlenir.

Mutasyon (elle koşuldu, T224 raporu): tampon saklamayı kapat → E1/E6/E8 düşer;
süre denetimini kaldır → E3 düşer; `ref_tip`siz kopyayı da tamponla → E5 düşer;
`erken` alanını yazma → E1 düşer.

KOSUM:
  O:\\navitas-local-train\\venv\\Scripts\\python.exe -B -m unittest discover \\
      -s tests -p "test_yks_erken_ika_ack_tamponu.py"
"""

import inspect
import json
import queue
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

KOK = Path(__file__).resolve().parents[1]
for _y in (KOK / "comms", KOK / "codes", KOK / "tests"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

import yks_gui  # noqa: E402
from link import UDPLink  # noqa: E402
from protocol import FrameReader, ack, encode  # noqa: E402
from test_yks_hakem_kanit_olaylari import ADR, ROTA, _arayuz  # noqa: E402

SEQ = ROTA["seq"]
IKA_ADR = ("127.0.0.1", 5006)


def _satirlar(yol):
    return [json.loads(s) for s in
            Path(yol).read_text(encoding="utf-8").strip().splitlines()]


def _olaylar(yol, ad):
    return [k for k in _satirlar(yol) if k["olay"] == ad]


def _olay_sirasi(yol):
    return [k["olay"] for k in _satirlar(yol)]


class _Taban(unittest.TestCase):
    def setUp(self):
        self._gecici = tempfile.TemporaryDirectory()
        self.yol = Path(self._gecici.name) / "hakem_log.jsonl"
        self.g = _arayuz(self.yol)

    def tearDown(self):
        try:
            self.g.hakem_kaydi.kapat()
        finally:
            self._gecici.cleanup()

    def _erken_ack(self, seq=SEQ, node="ika", ref_tip="OPEN_ROUTE"):
        self.g._ack_isle(ack(seq, node, ref_tip), IKA_ADR)

    def _rota(self, seq=SEQ):
        self.g._mesaj_isle(dict(ROTA, seq=seq), ADR)


class E1_GercekLoopbackErkenAck(_Taban):
    """Gerçek UDP loopback: ACK datagramı OPEN_ROUTE datagramından ÖNCE varır."""

    def _bekle(self, kosul, sure=3.0):
        bitis = time.monotonic() + sure
        while time.monotonic() < bitis:
            if kosul():
                return True
            time.sleep(0.005)
        return False

    def test_E1_ack_rotadan_once_gelince_kanit_kaybolmaz(self):
        g = self.g
        g.link = UDPLink(bind=("127.0.0.1", 0), timeout=0.2)
        g.gelen = queue.Queue()
        g.algi_kuyruk = queue.Queue()
        g.reader = FrameReader()
        dinleyici = threading.Thread(target=g._dinle, daemon=True)
        dinleyici.start()
        gonderici = UDPLink(bind=("127.0.0.1", 0), timeout=0.2)
        hedef = ("127.0.0.1", g.link.port)
        try:
            # 1) İKA'nın kopyası ÖNCE gelir — kuyrukta görülene dek beklenir.
            gonderici.send(encode(ack(SEQ, "ika", "OPEN_ROUTE")), hedef)
            self.assertTrue(self._bekle(lambda: g.gelen.qsize() >= 1),
                            "ACK datagramı dinleyiciye ulaşmadı")
            # 2) OPEN_ROUTE SONRA gelir.
            gonderici.send(encode(dict(ROTA)), hedef)
            self.assertTrue(self._bekle(lambda: g.gelen.qsize() >= 2),
                            "OPEN_ROUTE datagramı dinleyiciye ulaşmadı")
            # Sıra kanıtı: kuyruğun başı ACK, sonu OPEN_ROUTE.
            sira = [m["type"] for m, _ in list(g.gelen.queue)]
            self.assertEqual(["ACK", "OPEN_ROUTE"], sira)
            # 3) Üretim tiki kuyruğu bu sırayla işler.
            g._tik()
        finally:
            gonderici.close()
            g.link.sock.close()
            dinleyici.join(timeout=2.0)
        self.assertIn(SEQ, g.ika_rota_ack, "erken ACK kanıtı kayboldu (T224)")
        self.assertTrue(g.ika_aktarim_kaniti_var())
        self.assertEqual({}, g._erken_ika_rota_ack, "eşlenen kayıt tamponda kaldı")
        g.hakem_kaydi.kapat()
        kanit = _olaylar(self.yol, "IKA_AKTARIM_KANITI")
        self.assertEqual(1, len(kanit))
        self.assertEqual(SEQ, kanit[0]["seq"])
        self.assertIs(True, kanit[0]["erken"])
        self.assertIn("iha_havada", kanit[0])
        sira = _olay_sirasi(self.yol)
        self.assertLess(sira.index("ACK_ALINDI"), sira.index("ROTA_ALINDI"),
                        "ACK_ALINDI rotadan önce yazılmalıydı (gerçek sıra)")
        self.assertLess(sira.index("ROTA_ALINDI"),
                        sira.index("IKA_AKTARIM_KANITI"),
                        "kanıt olayı ROTA_ALINDI'dan SONRA düşmeli")
        # Ekran günlüğü: erken geliş ve tampondan eşleme görünür.
        gunluk = "\n".join(s[1] for s in g.gunluk.satirlar)
        self.assertIn("rotadan ÖNCE geldi", gunluk)
        self.assertIn("tampondan eşlendi", gunluk)


class E2_TersSiraDegismedi(_Taban):
    def test_E2_rota_sonra_ack_ayni_sonuc_kayit_satiri_ayni(self):
        self._rota()
        self.assertNotIn(SEQ, self.g.ika_rota_ack)
        self._erken_ack()
        self.assertIn(SEQ, self.g.ika_rota_ack)
        self.assertTrue(self.g.ika_aktarim_kaniti_var())
        self.assertEqual({}, self.g._erken_ika_rota_ack)
        self.g.hakem_kaydi.kapat()
        kanit = _olaylar(self.yol, "IKA_AKTARIM_KANITI")
        self.assertEqual(1, len(kanit))
        self.assertNotIn("erken", kanit[0],
                         "anlık yolun kayıt satırı DEĞİŞMEMELİ")
        self.assertEqual({"seq", "iha_havada"},
                         {a for a in kanit[0] if a not in
                          ("v", "ts", "monotonic_s", "oturum", "olay")})

    def test_E2b_ayni_seq_tekrar_ack_ikinci_kanit_yazmaz(self):
        self._rota()
        self._erken_ack()
        self._erken_ack()
        self.g.hakem_kaydi.kapat()
        self.assertEqual(1, len(_olaylar(self.yol, "IKA_AKTARIM_KANITI")))


class E3_E4_TamponSuresi(_Taban):
    def _yaslandir(self, saniye):
        """Monotonik saati `saniye` ileri kaydırarak OPEN_ROUTE'u işle."""
        gercek = time.monotonic
        with mock.patch.object(yks_gui.time, "monotonic",
                               lambda: gercek() + saniye):
            self._rota()

    def test_E3_sure_dolunca_kanit_yok_tampon_bosalir(self):
        self._erken_ack()
        self.assertIn(SEQ, self.g._erken_ika_rota_ack)
        self._yaslandir(yks_gui.IKA_ROTA_ACK_ERKEN_TAMPON_S + 0.05)
        self.assertNotIn(SEQ, self.g.ika_rota_ack, "bayat kopya kanıt sayıldı")
        self.assertFalse(self.g.ika_aktarim_kaniti_var())
        self.assertEqual({}, self.g._erken_ika_rota_ack, "bayat kayıt atılmadı")
        # Hakem 2/2 fail-closed ret sürer (kanıtsız onay yok).
        self.g.onayla()                      # 1/2
        self.g.onayla()                      # 2/2 → ret
        self.assertFalse(self.g.onaylandi)
        self.g.hakem_kaydi.kapat()
        self.assertEqual([], _olaylar(self.yol, "IKA_AKTARIM_KANITI"))
        redler = _olaylar(self.yol, "HAKEM_ONAYI_REDDI")
        self.assertEqual(["IKA_ACK_KANITI_YOK"], [r["sebep"] for r in redler])
        gunluk = "\n".join(s[1] for s in self.g.gunluk.satirlar)
        self.assertIn("BAYATLADI", gunluk)

    def test_E4_sure_icinde_eslenir(self):
        self._erken_ack()
        self._yaslandir(yks_gui.IKA_ROTA_ACK_ERKEN_TAMPON_S - 0.05)
        self.assertIn(SEQ, self.g.ika_rota_ack)
        self.assertTrue(self.g.ika_aktarim_kaniti_var())
        self.g.hakem_kaydi.kapat()
        kanit = _olaylar(self.yol, "IKA_AKTARIM_KANITI")
        self.assertEqual(1, len(kanit))
        self.assertIs(True, kanit[0]["erken"])


class E5_E6_E7_Eslesme(_Taban):
    def test_E5_ref_tipsiz_erken_ack_tamponlanmaz(self):
        self._erken_ack(ref_tip=None)
        self.assertEqual({}, self.g._erken_ika_rota_ack)
        self._rota()
        self.assertNotIn(SEQ, self.g.ika_rota_ack,
                         "ref_tip'siz erken ACK eski davranışta kanıt olmaz")
        self.g.hakem_kaydi.kapat()
        self.assertEqual([], _olaylar(self.yol, "IKA_AKTARIM_KANITI"))
        # Anlık yol için ref_tip'siz eşleme (geriye uyumluluk) DEĞİŞMEDİ.
        self._erken_ack(ref_tip=None)
        self.assertIn(SEQ, self.g.ika_rota_ack)

    def test_E5b_baska_tip_ack_tamponlanmaz(self):
        self._erken_ack(ref_tip="CMD")
        self._erken_ack(ref_tip="IHA_LANDED")
        self.assertEqual({}, self.g._erken_ika_rota_ack)

    def test_E6_baska_seq_eslenmez(self):
        self._erken_ack(seq=SEQ + 1)
        self._rota(SEQ)
        self.assertNotIn(SEQ, self.g.ika_rota_ack)
        self.assertFalse(self.g.ika_aktarim_kaniti_var())
        self.assertIn(SEQ + 1, self.g._erken_ika_rota_ack,
                      "eşleşmeyen kayıt süresi dolana dek tamponda kalmalı")

    def test_E6b_mevcut_rota_varken_yeni_seq_erken_ack_eslenir(self):
        self._rota(SEQ)                      # eski rota ekranda
        self._erken_ack(seq=SEQ + 1)         # yeni rotanın kopyası önce gelir
        self.assertNotIn(SEQ + 1, self.g.ika_rota_ack)
        self.assertIn(SEQ + 1, self.g._erken_ika_rota_ack)
        self._rota(SEQ + 1)                  # yeni OPEN_ROUTE
        self.assertIn(SEQ + 1, self.g.ika_rota_ack)
        self.assertTrue(self.g.ika_aktarim_kaniti_var())
        self.g.hakem_kaydi.kapat()
        kanit = _olaylar(self.yol, "IKA_AKTARIM_KANITI")
        self.assertEqual([SEQ + 1], [k["seq"] for k in kanit])
        self.assertIs(True, kanit[0]["erken"])

    def test_E7_iha_dugumunun_ack_i_tamponlanmaz(self):
        self._erken_ack(node="iha")
        self.assertEqual({}, self.g._erken_ika_rota_ack)
        self._rota()
        self.assertNotIn(SEQ, self.g.ika_rota_ack)


class E8_UctanUcaHakem(unittest.TestCase):
    """Erken ACK → OPEN_ROUTE → 1/2 → 2/2: kanıt hakem ekranında kaybolmadı."""

    def setUp(self):
        self._gecici = tempfile.TemporaryDirectory()
        self.yol = Path(self._gecici.name) / "hakem_log.jsonl"
        self.g = _arayuz(self.yol, gercek_ui=True)

    def tearDown(self):
        try:
            self.g.hakem_kaydi.kapat()
        finally:
            self._gecici.cleanup()

    def test_E8_erken_kanitla_2_2_onay_verilir_ack_linke_yazilir(self):
        g = self.g
        g._ack_isle(ack(SEQ, "ika", "OPEN_ROUTE"), IKA_ADR)
        g._mesaj_isle(dict(ROTA), ADR)
        g.onayla()                           # 1/2
        self.assertTrue(g.tespit_onayli)
        self.assertEqual("normal", g.btn_onay.cget("state"))
        self.assertIn("İKA ALDI ✓", g.lbl_onay.cget("text"))
        g.onayla()                           # 2/2
        self.assertTrue(g.onaylandi)
        self.assertEqual(1, g.sayac["ACK_TX"])
        gonderilen = [json.loads(c.args[0].decode("utf-8").strip())
                      for c in g.link.send.call_args_list]
        self.assertEqual([("ACK", SEQ, "yks", "OPEN_ROUTE")],
                         [(m["type"], m["ref"], m["node"], m.get("ref_tip"))
                          for m in gonderilen])
        g.hakem_kaydi.kapat()
        sira = _olay_sirasi(self.yol)
        for olay in ("ACK_ALINDI", "ROTA_ALINDI", "IKA_AKTARIM_KANITI",
                     "HAKEM_ONAYI_1", "HAKEM_ONAYI_2"):
            self.assertIn(olay, sira)
        self.assertEqual([], _olaylar(self.yol, "HAKEM_ONAYI_REDDI"))
        onay2 = _olaylar(self.yol, "HAKEM_ONAYI_2")[0]
        self.assertTrue(onay2["dayanak"].startswith("İKA ACK kanıtı "))


class E9_E10_SabitVeTamponDisiplini(_Taban):
    def test_E9_tampon_suresi_iha_tekrar_penceresinin_en_az_iki_kati(self):
        from iha_sender import IhaSender
        imza = inspect.signature(IhaSender._tekrarli_gonder).parameters
        pencere = imza["repeat"].default * imza["interval"].default
        self.assertEqual(2.0, pencere)
        self.assertEqual(5.0, yks_gui.IKA_ROTA_ACK_ERKEN_TAMPON_S)
        self.assertGreaterEqual(yks_gui.IKA_ROTA_ACK_ERKEN_TAMPON_S, 2 * pencere)

    def test_E10_yinelenen_kopya_ilk_damgayi_korur_bayat_temizlenir(self):
        self._erken_ack(seq=SEQ)
        ilk = self.g._erken_ika_rota_ack[SEQ]
        self._erken_ack(seq=SEQ)
        self.assertEqual(ilk, self.g._erken_ika_rota_ack[SEQ])
        # Süresi dolmuş bir kayıt, yeni bir erken kopya gelince temizlenir.
        gercek = time.monotonic
        with mock.patch.object(yks_gui.time, "monotonic",
                               lambda: gercek()
                               + yks_gui.IKA_ROTA_ACK_ERKEN_TAMPON_S + 0.05):
            self._erken_ack(seq=SEQ + 5)
        self.assertNotIn(SEQ, self.g._erken_ika_rota_ack)
        self.assertIn(SEQ + 5, self.g._erken_ika_rota_ack)

    def test_E10b_kurucu_alani_tanimlar(self):
        kaynak = (KOK / "comms" / "yks_gui.py").read_text(encoding="utf-8")
        self.assertIn("self._erken_ika_rota_ack = {}", kaynak)


if __name__ == "__main__":
    unittest.main()
