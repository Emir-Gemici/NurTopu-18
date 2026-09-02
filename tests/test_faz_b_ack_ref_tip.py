"""NEDEN (SAHA_HAZIRLIK_PLANI_20260903.md §1 madde 1.1 · D-405 kapanisi, T206):
ACK eslemesi yalniz `ref` ileyken hub fan-out'unda her tuketici HERKESIN
ACK'ini gorur ve seq sayaclari surec basinadir; OPEN_ROUTE seq=7 bekleyen
gonderici, IHA_LANDED seq=7 icin uretilmis IKA ACK'ini de "aktarildi" sayiyordu
(REVIEW_LOG D-405 §1 Q4, repro: results/faz_b_oncesi/curutucu_d405/r_q4_q6.py).
Sartname §2.2.3'te "aktarildi" kaniti bu ACK'tir — yanlis bekleyene baglanan
ACK, aktarim bitmemisken bitmis gosterir (fail-open).

Kilitlenen kurallar (CONTRACTS §6.6, AckliTekrar.ack_geldi ile AYNI):
  1. IhaSender._tekrarli_gonder: ACK `ref_tip` tasiyorsa bekleyen mesajin
     tipiyle de eslesmeli; eslesmeyen ACK o akrani ONAYLAMAZ.
  2. `ref_tip`siz ACK (eski uretici) yalniz `ref` ile kabul — geriye uyum.
  3. yks_gui'nin urettigi OPEN_ROUTE / NO_ROUTE / IHA_LANDED ACK'leri `ref_tip`
     tasir (UDP dali VE seri dali).
  4. Uctan uca: gercek YksArayuz (Tk'siz, D-320 `__new__` kalibi) + gercek
     IhaSender + gercek loopback UDP hub ikizi — YKS'nin IHA_LANDED ACK'i
     OPEN_ROUTE bekleyenine gitmez, IHA_LANDED bekleyenine gider.

Bilesenler GERCEKTIR: UDP loopback (`UDPLink` + ham soket), `loop://` seri hat
(pyserial), `yks_gui.YksArayuz` metodlari. Sahte soket yok. Mutasyon kontrolu:
iha_sender'daki `ref_tip` denetimi kaldirilinca Q4 testleri DUSER (notlarda
ham cikti).
"""
import socket
import sys
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
from iha_sender import IhaSender  # noqa: E402
from link import UDPLink, SerialLink  # noqa: E402
from protocol import (ack, decode, encode, iha_landed, open_route,  # noqa: E402
                      rota_yok, FrameReader)
from karar_sozlesmesi import YAYIN_REF_XY  # noqa: E402

YEREL = "127.0.0.1"
TEKRAR = 3
ARALIK_S = 0.3
BEKLEME_S = 8.0
# D-405 Q4 repro'sundaki capraz seq: iki farkli tipte mesaj AYNI sayiyi bekler.
CAPRAZ_SEQ = 7


class _SahteWidget:
    def __init__(self, **ayarlar):
        self.ayarlar = dict(ayarlar)

    def config(self, **ayarlar):
        self.ayarlar.update(ayarlar)

    def cget(self, ad):
        return self.ayarlar.get(ad)


class _AckVerici:
    """Ham UDP soket — hub/YKS ikizi. Gelen HER cerceve icin `yanit(m)`'in
    dondurdugu ACK'leri gonderene geri yazar; gorulen (tip, seq)'leri sayar."""

    def __init__(self, yanit, sock=None):
        self.yanit = yanit
        if sock is None:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind((YEREL, 0))
            sock.settimeout(0.05)
        self.sock = sock
        self.adr = (YEREL, self.sock.getsockname()[1])
        self.gorulen = []
        self._kilit = threading.Lock()
        self._dur = threading.Event()
        self._thr = threading.Thread(target=self._dongu, daemon=True)
        self._thr.start()

    def _dongu(self):
        okuyucu = FrameReader()
        while not self._dur.is_set():
            try:
                veri, kaynak = self.sock.recvfrom(4096)
            except (socket.timeout, ConnectionResetError, OSError):
                continue
            for m in okuyucu.feed(veri):
                with self._kilit:
                    self.gorulen.append((m.get("type"), m.get("seq")))
                for a in self.yanit(m):
                    self.sock.sendto(encode(a), kaynak)

    def gorulen_sayisi(self):
        with self._kilit:
            return len(self.gorulen)

    def kapat(self):
        self._dur.set()
        self._thr.join(2.0)
        self.sock.close()


def _yks_kur(link=None):
    """Tk acmadan YksArayuz (D-320 / r_q5.py kalibi): yalniz ACK ureten
    yollarin dokundugu alanlar. UI ciziciler mock; protokol metodlari GERCEK."""
    g = object.__new__(yks_gui.YksArayuz)
    g.link = link if link is not None else mock.Mock()
    g.son_adr = {}
    g.sabit_adr = {}
    g._logla = mock.Mock()
    g._zincir = mock.Mock()
    g._kutu_yaz = mock.Mock()
    g._harita_ciz = mock.Mock()
    g._rota_analiz = mock.Mock()
    g._irtifa_notunu_goster = mock.Mock()
    g.iha_indi = mock.Mock()
    g.kok = mock.Mock()
    g.otomatik_onay = False
    g.sayac = {"ACK_TX": 0, "OPEN_ROUTE": 0, "NO_ROUTE": 0, "IHA_LANDED": 0}
    g.rx_alim = {}
    g.rota = None
    g.rota_yok = None
    g.rota_adr = None
    g.rota_zaman = None
    g.tespit_bayat = False
    g.onaylandi = False
    g.tespit_onayli = False
    g.ika_rota_ack = {}
    g.iha_landed_seq = None
    g.t_iha1 = None
    g.btn_onay = _SahteWidget(state="disabled")
    g.lbl_onay = _SahteWidget(text="")
    return g


def _gecerli_rota(seq):
    return open_route(2, 0.9, [[0.0, 0.0], [0.0, 1.0]], list(YAYIN_REF_XY),
                      seq=seq)


# ── 1-2: IhaSender esleme kurali (gercek loopback UDP) ───────────────────────

class IhaSenderRefTipTests(unittest.TestCase):
    """Hub topolojisi: iki akran ("ika", "yks") AYNI adrese (hub) gider;
    hub HERKESIN ACK'ini geri yazar (D-405 Q4)."""

    def _gonderici(self, hedef_adr):
        link = UDPLink(bind=(YEREL, 0), timeout=0.05)
        self.addCleanup(link.close)
        return IhaSender(link, {"ika": hedef_adr, "yks": hedef_adr})

    def _verici(self, yanit):
        v = _AckVerici(yanit)
        self.addCleanup(v.kapat)
        return v

    def test_q4_yanlis_tipli_ika_acki_open_route_bekleyenini_onaylamaz(self):
        """D-405 Q4 birebir: OPEN_ROUTE seq=7 beklerken YKS'den ref_tip'li
        OPEN_ROUTE ACK'i + IKA'dan IHA_LANDED tipli ACK(ref=7) gelir.
        Beklenen: acked == {'yks'} — IKA ACK'i baska bir mesaja aittir."""
        verici = self._verici(lambda m: [
            ack(CAPRAZ_SEQ, "yks", "OPEN_ROUTE"),
            ack(CAPRAZ_SEQ, "ika", "IHA_LANDED"),
        ])
        s = self._gonderici(verici.adr)
        seq, acked = s._tekrarli_gonder(_gecerli_rota(CAPRAZ_SEQ),
                                        repeat=TEKRAR, interval=ARALIK_S,
                                        wait_ack=True)
        self.assertEqual(CAPRAZ_SEQ, seq)
        self.assertEqual({"yks"}, acked,
                         "IHA_LANDED tipli IKA ACK'i OPEN_ROUTE bekleyenine "
                         "baglandi (D-405 Q4 fail-open)")
        # IKA onayi eksik kaldigi icin tekrar SURMELIDIR (erken cikis yok).
        self.assertEqual(TEKRAR, verici.gorulen_sayisi(),
                         "eksik ACK'te tekrar tavanina kadar gonderilmeli")

    def test_q4_simetrik_iha_landed_bekleyeni_open_route_ackini_almaz(self):
        """Q4'un B tarafi: IHA_LANDED seq=7 bekleyen, OPEN_ROUTE tipli IKA
        ACK'ini reddeder; dogru tipli YKS ACK'ini alir."""
        verici = self._verici(lambda m: [
            ack(CAPRAZ_SEQ, "ika", "OPEN_ROUTE"),
            ack(CAPRAZ_SEQ, "yks", "IHA_LANDED"),
        ])
        s = self._gonderici(verici.adr)
        _seq, acked = s._tekrarli_gonder(iha_landed(seq=CAPRAZ_SEQ),
                                         repeat=TEKRAR, interval=ARALIK_S,
                                         wait_ack=True)
        self.assertEqual({"yks"}, acked)

    def test_dogru_ref_tip_her_iki_akrani_onaylar_ve_erken_cikar(self):
        verici = self._verici(lambda m: [
            ack(CAPRAZ_SEQ, "yks", "OPEN_ROUTE"),
            ack(CAPRAZ_SEQ, "ika", "OPEN_ROUTE"),
        ])
        s = self._gonderici(verici.adr)
        t0 = time.monotonic()
        _seq, acked = s._tekrarli_gonder(_gecerli_rota(CAPRAZ_SEQ),
                                         repeat=TEKRAR, interval=ARALIK_S,
                                         wait_ack=True)
        gecen = time.monotonic() - t0
        self.assertEqual({"ika", "yks"}, acked)
        # D-383 erken cikis KORUNDU: tam ACK'te pencere terk edilir.
        self.assertEqual(1, verici.gorulen_sayisi(),
                         "tam ACK sonrasi tekrar gonderim olmamali")
        self.assertLess(gecen, ARALIK_S * TEKRAR,
                        "tam ACK'te tekrar penceresi terk edilmeli (D-383)")

    def test_ref_tipsiz_eski_ack_geriye_uyumlu_kabul(self):
        """CONTRACTS §6.6: alan yoksa yalniz `ref` ile eslenir — eski IKA/YKS
        ACK'leri reddedilmez."""
        verici = self._verici(lambda m: [
            ack(CAPRAZ_SEQ, "yks"),
            ack(CAPRAZ_SEQ, "ika"),
        ])
        s = self._gonderici(verici.adr)
        _seq, acked = s._tekrarli_gonder(_gecerli_rota(CAPRAZ_SEQ),
                                         repeat=TEKRAR, interval=ARALIK_S,
                                         wait_ack=True)
        self.assertEqual({"ika", "yks"}, acked)

    def test_yanlis_ref_hala_reddedilir(self):
        """`ref` denetimi ref_tip eklenince GEVSEMEDI: dogru tip, yanlis seq
        yine kabul edilmez."""
        verici = self._verici(lambda m: [
            ack(CAPRAZ_SEQ + 1, "yks", "OPEN_ROUTE"),
            ack(CAPRAZ_SEQ + 1, "ika", "OPEN_ROUTE"),
        ])
        s = self._gonderici(verici.adr)
        _seq, acked = s._tekrarli_gonder(_gecerli_rota(CAPRAZ_SEQ),
                                         repeat=TEKRAR, interval=ARALIK_S,
                                         wait_ack=True)
        self.assertEqual(set(), acked)

    def test_no_route_bekleyeni_de_ayni_kurala_tabi(self):
        """Kural mesaj tipinden bagimsizdir: NO_ROUTE bekleyen, OPEN_ROUTE
        tipli ACK'i almaz, NO_ROUTE tiplisini alir."""
        verici = self._verici(lambda m: [
            ack(CAPRAZ_SEQ, "ika", "OPEN_ROUTE"),
            ack(CAPRAZ_SEQ, "yks", "NO_ROUTE"),
        ])
        s = self._gonderici(verici.adr)
        _seq, acked = s._tekrarli_gonder(rota_yok("KAPALI_DAR", seq=CAPRAZ_SEQ),
                                         repeat=TEKRAR, interval=ARALIK_S,
                                         wait_ack=True)
        self.assertEqual({"yks"}, acked)


# ── 3: yks_gui ACK uretimi `ref_tip` tasir (UDP + seri dallari) ──────────────

class YksGuiAckRefTipTests(unittest.TestCase):
    ADR = (YEREL, 6000)

    def _son_ack(self, g):
        veri, hedef = g.link.send.call_args.args
        m = decode(veri)
        self.assertEqual("ACK", m["type"])
        self.assertEqual("yks", m["node"])
        return m, hedef

    def test_no_route_acki_ref_tip_tasir(self):
        g = _yks_kur()
        g._mesaj_isle(rota_yok("KAPALI_DAR", seq=31), self.ADR)
        m, hedef = self._son_ack(g)
        self.assertEqual((31, "NO_ROUTE", self.ADR),
                         (m["ref"], m.get("ref_tip"), hedef))
        self.assertEqual(1, g.sayac["ACK_TX"])

    def test_iha_landed_acki_ref_tip_tasir(self):
        g = _yks_kur()
        g._mesaj_isle(iha_landed(seq=44), self.ADR)
        m, hedef = self._son_ack(g)
        self.assertEqual((44, "IHA_LANDED", self.ADR),
                         (m["ref"], m.get("ref_tip"), hedef))
        g.iha_indi.assert_called_once()

    def _onaya_hazir(self, rota, link=None, rota_adr=ADR):
        g = _yks_kur(link)
        g.rota = rota
        g.rota_adr = rota_adr
        g.tespit_onayli = True                 # 1/2 verildi
        g.ika_rota_ack = {rota["seq"]: time.time()}   # K8 kaniti hazir
        return g

    def test_open_route_hakem_acki_ref_tip_tasir(self):
        g = self._onaya_hazir(_gecerli_rota(8801))
        g.onayla()                              # 2/2 -> ACK
        self.assertTrue(g.onaylandi)
        m, hedef = self._son_ack(g)
        self.assertEqual((8801, "OPEN_ROUTE", self.ADR),
                         (m["ref"], m.get("ref_tip"), hedef))

    def test_open_route_tipsiz_fiksturde_bile_ref_tip_open_route(self):
        """`onayla` tanim geregi OPEN_ROUTE onayidir: `rota`da `type` alani
        yoksa (Tk'siz eski fiksturler) ref_tip'siz ZAYIF ACK uretilmez."""
        rota = {"seq": 8802, "road": 2, "ref_xy": list(YAYIN_REF_XY),
                "waypoints": [[0.0, 0.0], [0.0, 1.0]]}
        g = self._onaya_hazir(rota)
        g.onayla()
        m, _hedef = self._son_ack(g)
        self.assertEqual("OPEN_ROUTE", m.get("ref_tip"))

    # seri dal (SiK): adres yok, ACK ortam yayini — alan yine tasinmali
    def _seri(self):
        link = SerialLink("loop://", 57600, timeout=0.1)
        self.addCleanup(link.close)
        return link

    def _seriden_oku(self, link):
        okuyucu = FrameReader()
        bitis = time.monotonic() + 2.0
        while time.monotonic() < bitis:
            veri, _ = link.recv()
            for m in okuyucu.feed(veri or b""):
                return m
        self.fail("seri hatta ACK cercevesi okunamadi")

    def test_seri_no_route_acki_ref_tip_tasir(self):
        link = self._seri()
        g = _yks_kur(link)
        g._mesaj_isle(rota_yok("KAPALI_DAR", seq=32), None)
        m = self._seriden_oku(link)
        self.assertEqual(("ACK", 32, "NO_ROUTE"),
                         (m["type"], m["ref"], m.get("ref_tip")))

    def test_seri_iha_landed_acki_ref_tip_tasir(self):
        link = self._seri()
        g = _yks_kur(link)
        g._mesaj_isle(iha_landed(seq=45), None)
        m = self._seriden_oku(link)
        self.assertEqual(("ACK", 45, "IHA_LANDED"),
                         (m["type"], m["ref"], m.get("ref_tip")))

    def test_seri_open_route_hakem_acki_ref_tip_tasir(self):
        link = self._seri()
        g = self._onaya_hazir(_gecerli_rota(8803), link=link, rota_adr=None)
        g.onayla()
        self.assertTrue(g.onaylandi)
        m = self._seriden_oku(link)
        self.assertEqual(("ACK", 8803, "OPEN_ROUTE"),
                         (m["type"], m["ref"], m.get("ref_tip")))


# ── 4: uctan uca — gercek YKS ACK'i, gercek IhaSender, gercek UDP hub ikizi ──

class _HubLink:
    """YksArayuz'un `link`'i: YKS'nin yazdigi her cerceveyi hub gibi TUM
    tuketicilere dagitir (seri_hub fan-out semantigi, CONTRACTS §7.5)."""

    def __init__(self, sock, tuketiciler):
        self.sock = sock
        self.tuketiciler = list(tuketiciler)
        self.yazilan = []

    def send(self, data, peer=None):
        self.yazilan.append(decode(data))
        for adr in self.tuketiciler:
            self.sock.sendto(data, adr)


class UctanUcaQ4Tests(unittest.TestCase):
    def test_yks_iha_landed_acki_open_route_bekleyenine_gitmez(self):
        """r_q4_q6.py Q4 topolojisi, ACK'i bu kez GERCEK yks_gui uretir:
        A = rpi_inference ikizi (OPEN_ROUTE seq=7), B = iha_inis_yayinci ikizi
        (IHA_LANDED seq=7). YKS, IHA_LANDED'i hemen ACK'ler (ref_tip'li);
        OPEN_ROUTE hakem onayi bekler (ACK yok). Beklenen: B acked={'yks'},
        A acked=set() — YKS'nin ACK'i A'ya "aktarildi" dedirtmez."""
        a_link = UDPLink(bind=(YEREL, 0), timeout=0.05)
        b_link = UDPLink(bind=(YEREL, 0), timeout=0.05)
        self.addCleanup(a_link.close)
        self.addCleanup(b_link.close)
        tuketiciler = [(YEREL, a_link.port), (YEREL, b_link.port)]

        hub_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        hub_sock.bind((YEREL, 0))
        hub_sock.settimeout(0.05)
        hub_adr = (YEREL, hub_sock.getsockname()[1])
        yks = _yks_kur(_HubLink(hub_sock, tuketiciler))
        yks_kilit = threading.Lock()

        def _yanit(m):
            # Gelen cerceveyi GERCEK YksArayuz isler; ACK'ler _HubLink ile
            # zaten fan-out edildi, verici ayrica bir sey yazmaz.
            with yks_kilit:
                yks._mesaj_isle(m, hub_adr)
            return []

        verici = _AckVerici(_yanit, sock=hub_sock)
        self.addCleanup(verici.kapat)

        A = IhaSender(a_link, {"yks": hub_adr})
        B = IhaSender(b_link, {"yks": hub_adr})
        sonuc = {}

        def kos(ad, s, m):
            sonuc[ad] = s._tekrarli_gonder(m, repeat=TEKRAR,
                                           interval=ARALIK_S, wait_ack=True)

        tA = threading.Thread(target=kos, args=("A", A, _gecerli_rota(CAPRAZ_SEQ)))
        tB = threading.Thread(target=kos, args=("B", B, iha_landed(seq=CAPRAZ_SEQ)))
        tA.start(); tB.start()
        tA.join(BEKLEME_S); tB.join(BEKLEME_S)
        self.assertFalse(tA.is_alive() or tB.is_alive(), "gonderim bitmedi")

        yks_ackleri = [m for m in yks.link.yazilan if m["type"] == "ACK"]
        self.assertTrue(yks_ackleri, "YKS hic ACK uretmedi")
        self.assertTrue(all(m.get("ref_tip") == "IHA_LANDED" and m["ref"] == CAPRAZ_SEQ
                            for m in yks_ackleri),
                        f"YKS ACK'leri beklenmedik: {yks_ackleri}")
        self.assertEqual((CAPRAZ_SEQ, {"yks"}), sonuc["B"],
                         "IHA_LANDED bekleyeni YKS ACK'ini almali")
        self.assertEqual((CAPRAZ_SEQ, set()), sonuc["A"],
                         "OPEN_ROUTE bekleyeni IHA_LANDED ACK'ini SAHIPLENDI "
                         "(D-405 Q4 fail-open)")


if __name__ == "__main__":
    unittest.main()
