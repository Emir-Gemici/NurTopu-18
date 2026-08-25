"""NEDEN (şartname §2.2.5 / §2.2.3 · boşluk K4+K8 · REVIEW_LOG D-02): IKA_GO tek
UDP paketiydi; tek paket kaybı görevi geri dönülmez bitiriyordu. YKS artık ACK
gelene dek AYNI seq ile tekrar gönderir, üst sınırda KIRMIZI hata verip düğmeyi
yeniden açar; İKA mükerrer IKA_GO'yu idempotent işler; hakem 'İKA'ya aktarıldı'
onayını İKA'nın OPEN_ROUTE ACK kanıtı ekranda görünmeden VEREMEZ (fail-closed).

Tk penceresi AÇILMAZ: durum makinesi `comms/komut_tekrar.py`'de, GUI sahte
widget'larla `object.__new__` üzerinden sürülür. Zamanlama sahte saatle
(time.sleep'e dayanan test yok); paket düşürme gerçek UDP loopback'te YKS
soketinin `send`'i sarılarak yapılır.
"""
import sys
import time
import unittest
from pathlib import Path
from unittest import mock

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "comms"))
sys.path.insert(0, str(KOK / "codes"))

import yks_gui  # noqa: E402
from ika_receiver import IkaReceiver  # noqa: E402
from komut_tekrar import (AckliTekrar, BEKLIYOR, BOS, ONAYLANDI,  # noqa: E402
                          VAZGECILDI)
from link import UDPLink  # noqa: E402
from protocol import ack, command, decode, encode, open_route  # noqa: E402
from karar_sozlesmesi import (IKA_GO_TEKRAR_ARALIGI_S,  # noqa: E402
                              IKA_GO_TEKRAR_UST_SINIRI)


class _SahteSaat:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t

    def ilerle(self, sn):
        self.t += sn


class _SahteWidget:
    def __init__(self, **ayarlar):
        self.ayarlar = dict(ayarlar)

    def config(self, **ayarlar):
        self.ayarlar.update(ayarlar)

    def cget(self, ad):
        return self.ayarlar.get(ad)


def _arayuz(link, ika_adr, saat):
    """Tk açmadan YksArayuz: yalnız K4/K8 yollarının dokunduğu alanlar."""
    g = object.__new__(yks_gui.YksArayuz)
    g.link = link
    g.son_adr = {"ika": ika_adr} if ika_adr else {}
    g.sabit_adr = {}
    g._logla = mock.Mock()
    g._zincir = mock.Mock()
    g.kok = mock.Mock()
    g.otomatik_onay = False
    g.ika_go_tekrar = AckliTekrar(g._ham_gonder, IKA_GO_TEKRAR_ARALIGI_S,
                                  IKA_GO_TEKRAR_UST_SINIRI, saat=saat)
    g.ika_go_ack_zamani = None
    g.ika_rota_ack = {}
    g.t_ika0 = g.t_ika1 = None
    g.t_iha1 = None
    g.iha_landed_seq = 7
    g.onaylandi = True
    g.tespit_onayli = False
    g.rota = None
    g.rota_yok = None
    g.rota_adr = None
    g.sayac = {"ACK_TX": 0}
    g.btn_ika_go = _SahteWidget(state="normal")
    g.btn_hb = _SahteWidget(state="disabled")
    g.lbl_ika_go = _SahteWidget(text="İKA_GO: —")
    g.btn_onay = _SahteWidget(state="disabled")
    g.lbl_onay = _SahteWidget(text="")
    return g


class AckliTekrarDurumMakinesiTests(unittest.TestCase):
    def test_ilk_uc_kayip_dorduncu_ulasir_ack_tekrari_durdurur(self):
        saat = _SahteSaat()
        giden = []
        tekrar = AckliTekrar(lambda m: giden.append(m) or True,
                             0.25, 20, saat=saat)
        msg = command("IKA_GO", "ika", seq=41)
        self.assertTrue(tekrar.baslat(msg))
        self.assertEqual(BEKLIYOR, tekrar.durum)
        # aralık dolmadan tik → gönderim YOK
        saat.ilerle(0.1)
        tekrar.tik()
        self.assertEqual(1, len(giden))
        # 3 paket "kaybolur" (ACK gelmez), her aralıkta bir tekrar
        for _ in range(3):
            saat.ilerle(0.25)
            self.assertEqual(BEKLIYOR, tekrar.tik())
        self.assertEqual(4, len(giden))
        self.assertTrue(all(m["seq"] == 41 for m in giden), "seq değişti")
        # 4. paket ulaştı → ACK
        self.assertTrue(tekrar.ack_geldi(ack(41, "ika", "CMD")))
        self.assertEqual(ONAYLANDI, tekrar.durum)
        for _ in range(5):
            saat.ilerle(0.25)
            self.assertEqual(ONAYLANDI, tekrar.tik())
        self.assertEqual(4, len(giden), "ACK sonrası tekrar sürdü")

    def test_ack_hic_gelmezse_ust_sinirda_vazgecer(self):
        saat = _SahteSaat()
        giden = []
        tekrar = AckliTekrar(lambda m: giden.append(m) or True,
                             0.25, 5, saat=saat)
        tekrar.baslat(command("IKA_GO", "ika", seq=42))
        for _ in range(4):
            saat.ilerle(0.25)
            self.assertEqual(BEKLIYOR, tekrar.tik())
        saat.ilerle(0.25)
        self.assertEqual(VAZGECILDI, tekrar.tik())
        self.assertEqual(5, len(giden), "üst sınır = toplam gönderim")
        saat.ilerle(0.25)
        self.assertEqual(VAZGECILDI, tekrar.tik())
        self.assertEqual(5, len(giden))
        self.assertFalse(tekrar.ack_geldi(ack(42, "ika")), "vazgeçtikten sonra ACK")

    def test_yanlis_ref_veya_ref_tip_tekrari_durdurmaz(self):
        tekrar = AckliTekrar(lambda m: True, 0.25, 3, saat=_SahteSaat())
        tekrar.baslat(command("IKA_GO", "ika", seq=43))
        self.assertFalse(tekrar.ack_geldi(ack(44, "ika", "CMD")))
        self.assertFalse(tekrar.ack_geldi(ack(43, "ika", "OPEN_ROUTE")))
        self.assertFalse(tekrar.ack_geldi({"type": "HEARTBEAT", "ref": 43}))
        self.assertEqual(BEKLIYOR, tekrar.durum)
        self.assertTrue(tekrar.ack_geldi(ack(43, "ika")))   # ref_tip yok: uyumlu

    def test_tasiyici_reddederse_bos_kalir(self):
        tekrar = AckliTekrar(lambda m: False, 0.25, 3, saat=_SahteSaat())
        self.assertFalse(tekrar.baslat(command("IKA_GO", "ika", seq=45)))
        self.assertEqual(BOS, tekrar.durum)


class IkaGoGercekUdpPaketDusurmeTests(unittest.TestCase):
    def test_ilk_uc_ika_go_dusurulur_dorduncu_ack_alir_tekrar_durur(self):
        yks_link = UDPLink(bind=("127.0.0.1", 0), timeout=0.05)
        ika_link = UDPLink(bind=("127.0.0.1", 0), timeout=0.05)
        try:
            ika_adr = ("127.0.0.1", ika_link.port)
            gercek_send = yks_link.send
            dusurulen = []

            def sahte_send(data, peer=None):
                if len(dusurulen) < 3 and b'"IKA_GO"' in data:
                    dusurulen.append(data)      # ilk 3 IKA_GO KAYBOLUR
                    return
                gercek_send(data, peer)

            yks_link.send = sahte_send
            saat = _SahteSaat()
            g = _arayuz(yks_link, ika_adr, saat)
            alici = IkaReceiver(ika_link)

            g.ika_baslat()
            self.assertIsNotNone(g.t_ika0)
            self.assertEqual("disabled", g.btn_ika_go.cget("state"))
            self.assertIn("ACK bekleniyor", g.lbl_ika_go.cget("text"))
            g.kok.after.assert_called()       # tik zamanlandı

            def yks_al():
                d, adr = yks_link.recv()
                for m in g_reader.feed(d) if d else []:
                    g._mesaj_isle(m, adr)

            from protocol import FrameReader
            g_reader = FrameReader()
            # ilk gönderim (ika_baslat) + 2 tekrar = ilk 3 IKA_GO KAYIP
            for _ in range(2):
                saat.ilerle(IKA_GO_TEKRAR_ARALIGI_S)
                g._ika_go_tik()
                alici.poll()
                yks_al()
            self.assertEqual(3, len(dusurulen))
            self.assertEqual(3, g.ika_go_tekrar.deneme)
            self.assertFalse(alici.ika_go, "düşürülen paket İKA'ya ulaştı")
            self.assertIsNone(g.ika_go_ack_zamani)

            saat.ilerle(IKA_GO_TEKRAR_ARALIGI_S)
            g._ika_go_tik()                   # 4. IKA_GO ulaşır → ACK
            alici.poll()
            yks_al()
            self.assertTrue(alici.ika_go)
            self.assertEqual(ONAYLANDI, g.ika_go_tekrar.durum)
            self.assertEqual(4, g.ika_go_tekrar.deneme)
            self.assertIsNotNone(g.ika_go_ack_zamani)
            self.assertIn("İKA ALDI ✓", g.lbl_ika_go.cget("text"))
            self.assertEqual(yks_gui.YESIL, g.lbl_ika_go.cget("fg"))
            self.assertEqual(g.ika_go_tekrar.ack_mesaji["ref_tip"], "CMD")

            # ACK sonrası tik'ler artık paket üretmez
            giden_once = g.ika_go_tekrar.deneme
            for _ in range(3):
                saat.ilerle(IKA_GO_TEKRAR_ARALIGI_S)
                g._ika_go_tik()
            alici.poll()
            self.assertEqual(giden_once, g.ika_go_tekrar.deneme)
            print(f"[K4_UDP] dusurulen=3 ulasan_deneme={g.ika_go_tekrar.deneme} "
                  f"ika_go={alici.ika_go} tekrar_durdu=1")
        finally:
            yks_link.close()
            ika_link.close()

    def test_ack_hic_gelmez_ust_sinir_kirmizi_hata_dugme_yeniden_aktif(self):
        link = mock.Mock(spec=UDPLink)
        saat = _SahteSaat()
        g = _arayuz(link, ("127.0.0.1", 5006), saat)
        g.ika_baslat()
        self.assertEqual(1, link.send.call_count)
        for _ in range(IKA_GO_TEKRAR_UST_SINIRI - 1):
            saat.ilerle(IKA_GO_TEKRAR_ARALIGI_S)
            g._ika_go_tik()
        self.assertEqual(IKA_GO_TEKRAR_UST_SINIRI, link.send.call_count)
        self.assertEqual(BEKLIYOR, g.ika_go_tekrar.durum)
        saat.ilerle(IKA_GO_TEKRAR_ARALIGI_S)
        g._ika_go_tik()
        self.assertEqual(VAZGECILDI, g.ika_go_tekrar.durum)
        self.assertEqual(IKA_GO_TEKRAR_UST_SINIRI, link.send.call_count)
        self.assertEqual("İKA ONAY VERMEDİ ✗", g.lbl_ika_go.cget("text"))
        self.assertEqual(yks_gui.KIRMIZI, g.lbl_ika_go.cget("fg"))
        self.assertEqual("normal", g.btn_ika_go.cget("state"))
        self.assertEqual("disabled", g.btn_hb.cget("state"))
        self.assertIsNone(g.t_ika0, "kronometre başlamış sayıldı")
        metin, renk = g._logla.call_args.args
        self.assertIn("İKA ONAY VERMEDİ", metin)
        self.assertEqual("kirmizi", renk)
        # tüm gönderimler AYNI seq
        seqler = {decode(c.args[0])["seq"] for c in link.send.call_args_list}
        self.assertEqual(1, len(seqler))
        # görev kaybedilmedi: operatör yeniden tetikleyebilir
        g.ika_baslat()
        self.assertEqual(IKA_GO_TEKRAR_UST_SINIRI + 1, link.send.call_count)
        self.assertEqual(BEKLIYOR, g.ika_go_tekrar.durum)


class IkaMukerrerIkaGoIdempotentTests(unittest.TestCase):
    def test_ayni_ika_go_uc_kez_gelir_latch_bir_kez_kurulur_her_seferinde_ack(self):
        link = mock.Mock()
        alici = IkaReceiver(link)
        cagri = []
        alici.on_ika_go = cagri.append
        msg = command("IKA_GO", "ika", seq=9001)
        adr = ("127.0.0.1", 40000)
        alici._handle(msg, adr)
        ilk_t = alici.ika_go_monotonic
        alici._handle(msg, adr)
        alici._handle(msg, adr)
        self.assertTrue(alici.ika_go)
        self.assertEqual(ilk_t, alici.ika_go_monotonic, "latch zamanı yeniden yazıldı")
        self.assertEqual(3, link.send.call_count, "her alım ACK'lanmalı")
        for c in link.send.call_args_list:
            a = decode(c.args[0])
            self.assertEqual(("ACK", 9001, "ika", "CMD"),
                             (a["type"], a["ref"], a["node"], a["ref_tip"]))
            self.assertEqual(adr, c.args[1])
        self.assertEqual(adr, alici.yks_addr, "YKS adresi IKA_GO'dan öğrenilmeli")

    def test_open_route_ack_yks_akranina_yansitilir(self):
        link = mock.Mock()
        yks = ("127.0.0.1", 5005)
        alici = IkaReceiver(link, yks_peer=yks)
        iha = ("127.0.0.1", 6000)
        rota = open_route(2, 0.9, waypoints=[[0, 0], [1, 0]], ref_xy=[0, 0], seq=77)
        alici._handle(rota, iha)
        hedefler = [c.args[1] for c in link.send.call_args_list]
        self.assertEqual([iha, yks], hedefler)
        a = decode(link.send.call_args_list[1].args[0])
        self.assertEqual(("ACK", 77, "OPEN_ROUTE"), (a["type"], a["ref"], a["ref_tip"]))


class HakemAktarimOnayiKanitsizPasifTests(unittest.TestCase):
    def _rota_gui(self):
        g = _arayuz(mock.Mock(), ("127.0.0.1", 5006), _SahteSaat())
        g.onaylandi = False
        g.rota = {"seq": 8801, "road": 2}
        g.rota_adr = ("127.0.0.1", 6000)
        return g

    def test_kanit_yokken_ikinci_onay_verilmez_dugme_pasif_gerekce_gorunur(self):
        g = self._rota_gui()
        g.onayla()                                   # 1/2 tespit
        self.assertTrue(g.tespit_onayli)
        self.assertEqual("disabled", g.btn_onay.cget("state"))
        self.assertEqual("2) İKA ACK KANITI BEKLENİYOR", g.btn_onay.cget("text"))
        self.assertEqual(yks_gui.KIRMIZI, g.lbl_onay.cget("fg"))
        self.assertIn("kanıtı GÖRÜNMEDİ", g.lbl_onay.cget("text"))
        g.onayla()                                   # 2/2 denenir → RET
        self.assertFalse(g.onaylandi)
        g.link.send.assert_not_called()
        self.assertEqual(0, g.sayac["ACK_TX"])
        self.assertIn("kanıtsız onay verilmez", g._logla.call_args.args[0])

    def test_ika_open_route_ack_gelince_dugme_acilir_ve_onay_verilir(self):
        g = self._rota_gui()
        g.onayla()
        # başka rota / başka tip ACK kanıt SAYILMAZ
        g._mesaj_isle(ack(8802, "ika", "OPEN_ROUTE"), ("127.0.0.1", 5006))
        g._mesaj_isle(ack(8801, "iha", "OPEN_ROUTE"), ("127.0.0.1", 6000))
        g._mesaj_isle(ack(8801, "ika", "CMD"), ("127.0.0.1", 5006))
        self.assertEqual("disabled", g.btn_onay.cget("state"))
        self.assertFalse(g.ika_aktarim_kaniti_var())
        # gerçek kanıt
        g._mesaj_isle(ack(8801, "ika", "OPEN_ROUTE"), ("127.0.0.1", 5006))
        self.assertTrue(g.ika_aktarim_kaniti_var())
        self.assertEqual("normal", g.btn_onay.cget("state"))
        self.assertIn("İKA ALDI ✓", g.lbl_onay.cget("text"))
        g.onayla()
        self.assertTrue(g.onaylandi)
        self.assertEqual(1, g.sayac["ACK_TX"])
        veri, hedef = g.link.send.call_args.args
        self.assertEqual(8801, decode(veri)["ref"])
        self.assertEqual(("127.0.0.1", 6000), hedef)
        self.assertIn("İKA ACK kanıtı", g.lbl_onay.cget("text"))

    def test_sabit_degerler_sozlesmeden(self):
        self.assertGreater(IKA_GO_TEKRAR_ARALIGI_S, 0)
        self.assertGreaterEqual(IKA_GO_TEKRAR_UST_SINIRI, 2)
        self.assertLessEqual(IKA_GO_TEKRAR_ARALIGI_S * IKA_GO_TEKRAR_UST_SINIRI, 30,
                             "üst sınır operatörü dakikalarca bekletmemeli")


if __name__ == "__main__":
    unittest.main(verbosity=2)
