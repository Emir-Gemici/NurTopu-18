"""NEDEN: Dalga 2 çürütücüleri (results/gece_20260826/dalga2_ozet.txt) birleşik
K1/K4+K8/K5+K6 kodunda beş kusur ölçtü; bu dosya her birini kilitler.

K8-UDP  : navitas_sim/ika_nav zinciri IkaReceiver'ı yks_peer'siz kuruyordu;
          OPEN_ROUTE IKA_GO'dan ÖNCE geldiği için YKS'ye ACK kopyası hiç gitmiyordu
          → hakem 2. onayı kalıcı pasif. Şimdi --yks / --landed-yks bağlanır.
K8-seri : ika_receiver._rota_ack `addr is None → return` — SerialLink'te addr daima
          None olduğundan İKA sahada rota ACK'ı HİÇ üretmiyordu (yalnız CMD).
K1      : KararYayinci._karar_dongusu durma kontrolü yuvayı pop edip ATIYORDU;
          stop() sırasında yazılan karar kayboluyordu.
K5      : ika_gorevi 'sürüş süresi doldu → 4' ve navitas_sim 'yalnız 0 başarı'
          eşlemesi testle kilitli değildi (M7 hayatta kalmıştı).
K4      : yks_gui VAZGECILDI'de t_ika1 sıfırlanmıyordu; btn_hb ACK'tan önce açılıyordu.

Gerçek UDP loopback kullanılan testte adres 127.0.0.1'dir; zamanlama iddiası
Event'lerle kurulur, time.sleep'e dayanan süre iddiası yoktur.
"""
import contextlib
import io
import socket
import sys
import threading
import unittest
from pathlib import Path
from unittest import mock

KOK = Path(__file__).resolve().parents[1]
for _p in (KOK / "comms", KOK / "codes", KOK / "simulation" / "scripts",
           KOK / "tests"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import ika_nav  # noqa: E402
import navitas_sim  # noqa: E402
import iha_sender  # noqa: E402
import yks_gui  # noqa: E402
from ika_receiver import IkaReceiver  # noqa: E402
from komut_tekrar import VAZGECILDI  # noqa: E402
from link import SerialLink, UDPLink  # noqa: E402
from protocol import ack, decode, encode, open_route, rota_yok  # noqa: E402
from karar_sozlesmesi import (IKA_GO_TEKRAR_ARALIGI_S,  # noqa: E402
                              IKA_GO_TEKRAR_UST_SINIRI)
from test_ika_go_ackli_tekrar import _SahteSaat, _arayuz  # noqa: E402


def _bos_udp_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


ROTA = {"type": "OPEN_ROUTE", "road": 1, "seq": 1}


# ── K8 (UDP): ika_nav zinciri yks_peer bağlar ───────────────────────────────
class K8UdpYksAkraniTests(unittest.TestCase):
    def test_open_route_ika_go_dan_ONCE_gelince_yks_ack_kopyasi_alir(self):
        """Gerçek loopback: IKA_GO HİÇ gönderilmez; yalnız --yks ile kopya gider."""
        port = _bos_udp_port()
        yks = UDPLink(bind=("127.0.0.1", 0), timeout=0.5)
        iha = UDPLink(bind=("127.0.0.1", 0), timeout=0.2)
        sonuc = {}

        def bekle():
            with contextlib.redirect_stdout(io.StringIO()):
                sonuc["r"] = ika_nav.wait_open_route_from_comms(
                    f"127.0.0.1:{port}", timeout=10.0, keep_receiver=True,
                    yks_peer=("127.0.0.1", yks.port))

        t = threading.Thread(target=bekle, daemon=True)
        t.start()
        rota = open_route(2, 0.9, waypoints=[[0, 0], [1, 0]], ref_xy=[0, 0], seq=41)
        iha_ack = None
        for _ in range(50):                       # alıcı bind olana dek yinele
            iha.send(encode(rota), ("127.0.0.1", port))
            d, _a = iha.recv()
            if d:
                iha_ack = decode(d)
                break
        t.join(5.0)
        rx = None
        try:
            self.assertIsNotNone(iha_ack, "İHA'ya ACK dönmedi")
            self.assertEqual(("ACK", 41, "ika", "OPEN_ROUTE"),
                             (iha_ack["type"], iha_ack["ref"], iha_ack["node"],
                              iha_ack["ref_tip"]))
            self.assertIn("r", sonuc, "wait_open_route_from_comms dönmedi")
            route, rx = sonuc["r"]
            self.assertEqual(41, route["seq"])
            yks_ack = None
            for _ in range(10):
                d, _a = yks.recv()
                if d:
                    m = decode(d)
                    if m.get("type") == "ACK" and m.get("ref") == 41:
                        yks_ack = m
                        break
            self.assertIsNotNone(
                yks_ack, "YKS OPEN_ROUTE ACK kopyasını almadı (IKA_GO yokken)")
            self.assertEqual("OPEN_ROUTE", yks_ack["ref_tip"])
            self.assertEqual("ika", yks_ack["node"])
            print(f"[K8-UDP] IKA_GO gonderilmedi; YKS'ye OPEN_ROUTE ACK gitti mi: "
                  f"{yks_ack is not None}")
        finally:
            if rx is not None:
                rx.stop()
                rx.link.close()
            yks.close()
            iha.close()

    def test_ika_gorevi_yks_peer_i_rota_bekle_ye_gecirir(self):
        kayit = {}

        def rota_bekle(bind, timeout, keep_receiver, deadline_monotonic, yks_peer=None):
            kayit["yks_peer"] = yks_peer
            return None

        with contextlib.redirect_stdout(io.StringIO()):
            kod = ika_nav.ika_gorevi("127.0.0.1:0", 1.0, rota_bekle=rota_bekle,
                                     yks_peer=("10.0.0.5", 5005))
        self.assertEqual(1, kod)
        self.assertEqual(("10.0.0.5", 5005), kayit["yks_peer"])

    def test_navitas_sim_dinamik_gorev_yks_peer_i_ika_gorevi_ye_gecirir(self):
        with mock.patch.object(ika_nav, "ika_gorevi", return_value=0) as g, \
                contextlib.redirect_stdout(io.StringIO()):
            ok = navitas_sim.dinamik_ika_gorevi("0.0.0.0:5006", 900.0, 600.0,
                                                yks_peer=("10.0.0.5", 5005))
        self.assertTrue(ok)
        self.assertEqual(("10.0.0.5", 5005), g.call_args.kwargs["yks_peer"])

    def test_navitas_sim_main_landed_yks_adresini_ika_gorevine_baglar(self):
        ika_cagrisi = mock.Mock(return_value=True)
        with mock.patch.object(sys, "argv", ["navitas_sim.py", "--no-wait",
                                             "--ika-only",
                                             "--landed-yks", "10.0.0.5:5005"]), \
             mock.patch.object(navitas_sim.time, "sleep"), \
             mock.patch.object(navitas_sim, "check_topics", return_value=True), \
             mock.patch.object(navitas_sim, "dinamik_ika_gorevi", ika_cagrisi), \
             contextlib.redirect_stdout(io.StringIO()):
            try:
                navitas_sim.main()
            except SystemExit:
                pass
        ika_cagrisi.assert_called_once()
        self.assertEqual(("10.0.0.5", 5005), ika_cagrisi.call_args.kwargs["yks_peer"])

    def test_ika_nav_cli_yks_bayragi_parse_edilir(self):
        kayit = {}

        def sahte_gorev(bind, bekleme, surus, yks_peer=None):
            kayit["yks_peer"] = yks_peer
            return 0
        kaynak = (KOK / "simulation" / "scripts" / "ika_nav.py").read_text(encoding="utf-8")
        self.assertIn('"--yks"', kaynak)
        with mock.patch.object(ika_nav, "ika_gorevi", sahte_gorev), \
                mock.patch.object(sys, "argv", ["ika_nav.py", "comms", "--yks", "10.0.0.5:5005"]), \
                mock.patch.object(sys, "exit") as cikis:
            main_govdesi = kaynak.split('if __name__ == "__main__":', 1)[1]
            exec(compile("if True:" + main_govdesi, "ika_nav.__main__", "exec"),
                 vars(ika_nav))
        cikis.assert_called_once_with(0)
        self.assertEqual(("10.0.0.5", 5005), kayit["yks_peer"])


# ── K8 (seri): SerialLink'te rota ACK üretilir ──────────────────────────────
class KayitSerial(SerialLink):
    def __init__(self):
        self.gonderilen = []

    def send(self, data, peer=None):
        self.gonderilen.append((data, peer))


class K8SeriRotaAckTests(unittest.TestCase):
    def test_serial_open_route_ve_no_route_ack_uretir(self):
        link = KayitSerial()
        rx = IkaReceiver(link)
        rota = open_route(2, 0.9, waypoints=[[0, 0], [1, 0]], ref_xy=[0, 0], seq=51)
        rx._handle(rota, None)                       # seri: addr daima None
        rx._handle(rota_yok("KAPALI_DAR", "test", seq=52), None)
        tipler = [(decode(d)["type"], decode(d)["ref"], decode(d)["ref_tip"], p)
                  for d, p in link.gonderilen]
        self.assertEqual([("ACK", 51, "OPEN_ROUTE", None),
                          ("ACK", 52, "NO_ROUTE", None)], tipler)
        print(f"[K8-seri] SerialLink rota ACK'lari: {[t[2] for t in tipler]}")

    def test_udp_de_addr_yoksa_ack_yine_gonderilmez(self):
        link = mock.Mock(spec=UDPLink)
        rx = IkaReceiver(link)
        rx._handle(open_route(2, 0.9, waypoints=[[0, 0], [1, 0]], ref_xy=[0, 0], seq=53), None)
        link.send.assert_not_called()


# ── K1: stop() sırasında yazılan karar atılmaz ──────────────────────────────
class K1StopYarisiTests(unittest.TestCase):
    def test_gonderim_sirasinda_yazilan_karar_stop_ile_kaybolmaz(self):
        icerde = threading.Event()
        devam = threading.Event()
        sender = mock.Mock()

        def send_no_route(*a, **k):
            if not icerde.is_set():
                icerde.set()
                self.assertTrue(devam.wait(5.0))
            return (1, True)
        sender.send_no_route.side_effect = send_no_route
        y = iha_sender.KararYayinci(sender, wait_ack=False)
        y.karar(None, 0.0, [], 0.05, ("KAPALI_DAR", "1. karar"))
        y.start()
        self.assertTrue(icerde.wait(5.0))            # 1. karar gönderimde
        y.karar(None, 0.0, [], 0.05, ("KAPALI_DAR", "2. karar"))
        durduran = threading.Thread(target=y.stop, daemon=True)
        durduran.start()
        for _ in range(500):                          # stop() _dur'u kurana dek
            if y._dur.is_set():
                break
            threading.Event().wait(0.01)
        self.assertTrue(y._dur.is_set())
        devam.set()
        durduran.join(5.0)
        self.assertFalse(y._karar_thr.is_alive())
        detaylar = [c.args[1] for c in sender.send_no_route.call_args_list]
        self.assertEqual(["1. karar", "2. karar"], detaylar)
        self.assertEqual([], y.hata)
        print(f"[K1] 2 karar beklenirken stop(): send_no_route {len(detaylar)} kez")


# ── K5: sürüş süresi dolan görev 4 döner, navitas_sim BAŞARISIZ sayar ───────
class K5CikisKoduTests(unittest.TestCase):
    def _gorev(self, sur_sonucu):
        with mock.patch.object(ika_nav, "send_vel", lambda r, l, topic=None: None), \
                contextlib.redirect_stdout(io.StringIO()):
            return ika_nav.ika_gorevi(
                "127.0.0.1:0",
                rota_bekle=lambda *a, **k: (ROTA, mock.Mock(link_ok=True)),
                izin_bekle=lambda *a, **k: True,
                sur=lambda *a, **k: sur_sonucu)

    def test_surus_suresi_dolunca_4_doner_basarida_0(self):
        self.assertEqual(4, self._gorev(False))
        self.assertEqual(0, self._gorev(True))

    def test_navitas_sim_yalniz_0_i_basari_sayar(self):
        for kod, beklenen in ((0, True), (1, False), (2, False), (3, False), (4, False)):
            with mock.patch.object(ika_nav, "ika_gorevi", return_value=kod), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(beklenen,
                                 navitas_sim.dinamik_ika_gorevi("0.0.0.0:5006", 1.0),
                                 f"kod={kod}")

    def test_surus_dolan_gorev_zincirde_BASARISIZ(self):
        with mock.patch.object(ika_nav, "send_vel", lambda r, l, topic=None: None), \
                mock.patch.object(ika_nav, "wait_open_route_from_comms",
                                  lambda *a, **k: (ROTA, mock.Mock(link_ok=True))), \
                mock.patch.object(ika_nav, "receiver_surus_izni_bekle",
                                  lambda *a, **k: True), \
                mock.patch.object(ika_nav, "navigate_route", lambda *a, **k: False), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertFalse(navitas_sim.dinamik_ika_gorevi("0.0.0.0:5006", 1.0))


# ── K4 küçük: VAZGECILDI tam sıfırlar, HB TEMAS ancak ACK ile açılır ─────────
class K4KronometreVeHbTemasTests(unittest.TestCase):
    def _vazgecir(self, g, saat):
        for _ in range(IKA_GO_TEKRAR_UST_SINIRI):
            saat.ilerle(IKA_GO_TEKRAR_ARALIGI_S)
            g._ika_go_tik()
        self.assertEqual(VAZGECILDI, g.ika_go_tekrar.durum)

    def test_btn_hb_ack_gelmeden_acilmaz_ack_gelince_acilir(self):
        link = mock.Mock(spec=UDPLink)
        saat = _SahteSaat()
        g = _arayuz(link, ("127.0.0.1", 5006), saat)
        g.ika_baslat()
        self.assertIsNotNone(g.t_ika0)                # kronometre komutla başlar
        self.assertEqual("disabled", g.btn_hb.cget("state"))
        seq = g.ika_go_tekrar.mesaj["seq"]
        g._ack_isle(ack(seq, "ika", "CMD"), ("127.0.0.1", 5006))
        self.assertEqual("normal", g.btn_hb.cget("state"))
        g.hb_temas()
        self.assertIsNotNone(g.t_ika1)

    def test_vazgecildi_t_ika1_i_de_sifirlar_yeniden_ika_go_sonrasi_hb_temas_calisir(self):
        link = mock.Mock(spec=UDPLink)
        saat = _SahteSaat()
        g = _arayuz(link, ("127.0.0.1", 5006), saat)
        g.ika_baslat()
        g.t_ika1 = 1234.0            # bayat HB damgası (çürütücü senaryosu)
        self._vazgecir(g, saat)
        self.assertIsNone(g.t_ika0)
        self.assertIsNone(g.t_ika1, "VAZGECILDI t_ika1'i sıfırlamadı")
        self.assertEqual("disabled", g.btn_hb.cget("state"))
        g.ika_baslat()               # operatör yeniden tetikler
        self.assertIsNotNone(g.t_ika0)
        self.assertIsNone(g.t_ika1)
        g._ack_isle(ack(g.ika_go_tekrar.mesaj["seq"], "ika", "CMD"), ("127.0.0.1", 5006))
        g.hb_temas()
        self.assertIsNotNone(g.t_ika1, "hb_temas kalıcı kilitli kaldı")


if __name__ == "__main__":
    unittest.main()
