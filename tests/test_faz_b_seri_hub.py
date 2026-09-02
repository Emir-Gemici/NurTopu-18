"""NEDEN (Faz B · CONTRACTS §7.4 · D-403): SiK kipinde uc IHA sureci ayni
/dev/ttyUSB0'i acamaz; `comms/seri_hub.py` portu TEK BASINA acar ve NAVITAS
cercevelerini UDP loopback uzerinden cogullar. Burada kilitlenen sey:
  * UDP -> seri birebir aktarim, seri -> UDP fan-out (statik ∪ ogrenilen);
  * her datagram TAM BIR cerceve (iha_komut_alici datagram basina taze
    FrameReader kullanir — parca gelirse cerceve kaybolur, D-403 KUCUK-4);
  * seri arizasinda hub COKMEZ, UDP cerceveleri KUYRUKLANMAZ (dusurulur ve
    sayilir), 1 s sonra yeniden acilir;
  * bozuk cerceve yayinlanmaz ama hat kilitlenmez;
  * UCTAN UCA: YKS seri ucundan PARACHUTE -> hub -> gercek IhaKomutAlici (UDP)
    -> sahte Pixhawk -> ACK -> hub -> seri -> YKS ACK'i okur.

Bilesenler GERCEKTIR: `SikKoprusu` (tests/test_p2_seri_hat.py — iki gercek
pyserial `socket://` ucunu pompalayan transparan TCP role = SiK'in seffaf
davranisi), `SerialLink`, `UDPLink` loopback, `FrameReader`/`protocol`,
uretim `IhaKomutAlici`. Mock yalniz donanim ucunda (command_long_send) ve
ariza enjeksiyonunda (seri_link.recv/send).

⚠ pyserial `socket://` ucunda `in_waiting` 0/1 doner -> `SerialLink.recv` en
cok 2 bayt verir; hub bunu tur ici tekrar okumayla (SERI_TUR_TAVANI) tasir.
Gercek seri portta `in_waiting` gercek bayt sayisidir.
"""
import contextlib
import io
import sys
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

KOK = Path(__file__).resolve().parents[1]
for _y in (KOK / "comms", KOK / "codes", KOK / "tests"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

try:
    import serial
except ImportError:  # pragma: no cover - kurulum kapisi
    serial = None

import seri_hub as modul  # noqa: E402
from seri_hub import SeriHub  # noqa: E402
from link import SerialLink, UDPLink  # noqa: E402
from protocol import (FrameReader, command, decode, encode,  # noqa: E402
                      heartbeat, open_route)
from test_p2_seri_hat import SikKoprusu  # noqa: E402

YEREL = "127.0.0.1"
TAVAN_S = 3.0                       # gercek soketlerde bekleme tavani
UC_ZAMAN_ASIMI_S = 0.02             # test uclari: pompalama dongusu tikanmasin
TUKETICI_ZAMAN_ASIMI_S = 0.01


class _SahteSaat:
    def __init__(self, t=1000.0):
        self.t = t

    def __call__(self):
        return self.t


def _uc(kopru, timeout=UC_ZAMAN_ASIMI_S):
    """Kopruye bagli GERCEK pyserial ucu (SerialLink uzerinden)."""
    return SerialLink(f"socket://{YEREL}:{kopru.port}", modul.VARSAYILAN_BAUD,
                      timeout=timeout)


def _tuketici():
    return UDPLink(bind=(YEREL, 0), timeout=TUKETICI_ZAMAN_ASIMI_S)


def _datagramlari_topla(link, adet, pompa=None, tavan_s=TAVAN_S):
    """UDP ucundan `adet` datagram gelene dek (pompa=hub.poll ile) topla."""
    gelen = []
    bitis = time.monotonic() + tavan_s
    while len(gelen) < adet and time.monotonic() < bitis:
        if pompa is not None:
            pompa()
        veri, _ = link.recv()
        if veri:
            gelen.append(veri)
    return gelen


#: socket:// ucunda `SerialLink.recv` en cok 2 bayt verir (dokstring); test
#: ucu her turda birikeni bosaltir ki olcum hub'i degil artefakti saymasin.
UC_BOSALTMA_TAVANI = 512


def _seri_bosalt(link):
    """Uctaki birikeni tek turda topla (ilk okuma zaman asimina kadar bekler)."""
    toplanan = b""
    for _ in range(UC_BOSALTMA_TAVANI):
        veri, _ = link.recv()
        if not veri:
            break
        toplanan += veri
    return toplanan


def _seri_cerceve_bekle(link, okuyucu, kosul, pompa=None, tavan_s=TAVAN_S):
    """Seri uctan kosulu saglayan cerceve gelene dek oku; (mesaj, hepsi)."""
    bitis = time.monotonic() + tavan_s
    toplanan = []
    while time.monotonic() < bitis:
        if pompa is not None:
            pompa()
        for mesaj in okuyucu.feed(_seri_bosalt(link)):
            toplanan.append(mesaj)
            if kosul(mesaj):
                return mesaj, toplanan
    return None, toplanan


def _seri_ham_bekle(link, tavan_s=TAVAN_S, pompa=None):
    """Seri uctan newline gelene dek HAM bayt topla (birebir karsilastirma)."""
    toplanan = b""
    bitis = time.monotonic() + tavan_s
    while b"\n" not in toplanan and time.monotonic() < bitis:
        if pompa is not None:
            pompa()
        toplanan += _seri_bosalt(link)
    return toplanan


class _HubKurulum:
    """Hub bir ucta (socket:// SerialLink), sahte YKS diger ucta."""

    def __init__(self, test, tuketiciler=(), **kw):
        self.test = test
        self.kopru = SikKoprusu()
        test.addCleanup(self.kopru.kapat)
        self.hub_seri = _uc(self.kopru)
        self.yks = _uc(self.kopru)
        test.addCleanup(self.yks.close)
        self.udp = UDPLink(bind=(YEREL, 0), timeout=modul.UDP_OKUMA_ZAMAN_ASIMI_S)
        self.log = io.StringIO()
        with _Yakala(self.log):
            self.hub = SeriHub(self.hub_seri, self.udp, list(tuketiciler), **kw)
        test.addCleanup(self.hub.kapat)
        self.hub_adr = (YEREL, self.udp.port)
        self.yks_okuyucu = FrameReader()

    def tur(self, n=1):
        with _Yakala(self.log):
            for _ in range(n):
                self.hub.poll()

    def pompa(self):
        self.tur()

    def yks_yaz(self, mesaj):
        self.yks.send(encode(mesaj))

    def yks_bekle(self, kosul, tavan_s=TAVAN_S):
        with _Yakala(self.log):
            return _seri_cerceve_bekle(self.yks, self.yks_okuyucu, kosul,
                                       pompa=self.hub.poll, tavan_s=tavan_s)

    def topla(self, link, adet, tavan_s=TAVAN_S):
        with _Yakala(self.log):
            return _datagramlari_topla(link, adet, pompa=self.hub.poll,
                                       tavan_s=tavan_s)


class _Yakala:
    """stdout+stderr'i tek tampona yonlendir (hub loglari test ciktisini
    kirletmesin; KIRMIZI satirlar iddia edilebilsin)."""

    def __init__(self, tampon):
        self.tampon = tampon
        self._yigin = None

    def __enter__(self):
        self._yigin = contextlib.ExitStack()
        self._yigin.enter_context(contextlib.redirect_stdout(self.tampon))
        self._yigin.enter_context(contextlib.redirect_stderr(self.tampon))
        return self

    def __exit__(self, *exc):
        self._yigin.__exit__(*exc)
        return False


def _tek_cerceve_dogrula(test, datagram, beklenen):
    """Datagram TAM OLARAK BIR cerceve: tek newline, sonda; icerik birebir."""
    test.assertTrue(datagram.endswith(b"\n"), datagram)
    test.assertEqual(1, datagram.count(b"\n"), datagram)
    test.assertEqual(beklenen, decode(datagram))
    test.assertEqual(encode(decode(datagram)), datagram, "yeniden kodlama farkli")


@unittest.skipIf(serial is None, "pyserial kurulu degil")
class TestSeriHubAktarim(unittest.TestCase):

    def test_1_tuketici_udp_hub_seri_yks_cerceveyi_birebir_alir(self):
        """UDP -> hub -> seri: YKS ucu datagramdaki baytlari BIREBIR okur."""
        k = _HubKurulum(self)
        tuketici = _tuketici()
        self.addCleanup(tuketici.close)
        mesaj = open_route(2, 0.91, [[0, 0], [0.5, 1.0]], [0.0, 0.0], seq=17)
        ham = encode(mesaj)
        tuketici.send(ham, k.hub_adr)
        with _Yakala(k.log):
            gelen = _seri_ham_bekle(k.yks, pompa=k.hub.poll)
        self.assertEqual(ham, gelen, "seri hatta cikan bayt dizisi birebir degil")
        self.assertEqual(mesaj, decode(gelen))
        self.assertEqual(1, k.hub.sayac["udp_alinan"])
        self.assertEqual(1, k.hub.sayac["seri_yazilan"])
        self.assertEqual(0, k.hub.sayac["dusurulen"])
        self.assertIn((YEREL, tuketici.port), k.hub.ogrenilen,
                      "gonderen adresi ogrenilmedi")

    def test_2_seri_cerceve_statik_ve_ogrenilen_tuketicilere_TAM_gider(self):
        """YKS seri -> hub -> hem statik (5007 benzeri) hem gondererek
        ogrenilmis tuketici, ikisi de TAM cerceve alir; datagram = 1 cerceve."""
        statik = _tuketici()
        ogrenen = _tuketici()
        self.addCleanup(statik.close)
        self.addCleanup(ogrenen.close)
        k = _HubKurulum(self, tuketiciler=[(YEREL, statik.port)])
        # ogrenen once bir sey gonderir (rpi_inference heartbeat gibi)
        ogrenen.send(encode(heartbeat("iha", seq=1)), k.hub_adr)
        k.tur(3)
        self.assertIn((YEREL, ogrenen.port), k.hub.ogrenilen)
        self.assertEqual([(YEREL, statik.port), (YEREL, ogrenen.port)],
                         k.hub.hedefler())
        mesaj = command("IKA_GO", "ika", seq=5)
        k.yks_yaz(mesaj)
        s_gelen = k.topla(statik, 1)
        o_gelen = k.topla(ogrenen, 1)
        self.assertEqual(1, len(s_gelen), "statik tuketici cerceve almadi")
        self.assertEqual(1, len(o_gelen), "ogrenilen tuketici cerceve almadi")
        _tek_cerceve_dogrula(self, s_gelen[0], mesaj)
        _tek_cerceve_dogrula(self, o_gelen[0], mesaj)
        self.assertEqual(1, k.hub.sayac["seri_cerceve"])
        self.assertEqual(2, k.hub.sayac["fanout_gonderim"])
        self.assertEqual(0, k.hub.sayac["bozuk"])

    def test_3_yks_bayt_bayt_yazar_tuketiciye_BUTUN_cerceve_gelir(self):
        """1 baytlik parcalar (her parca arasinda hub turu): tuketiciye TEK
        datagram, o da butun cerceve. Parca datagram YOK."""
        statik = _tuketici()
        self.addCleanup(statik.close)
        k = _HubKurulum(self, tuketiciler=[(YEREL, statik.port)])
        mesaj = open_route(1, 0.5, [[0, 0], [1.0, 1.0]], [0.0, 0.0], seq=7)
        ham = encode(mesaj)
        erken = []
        for bayt in ham[:-1]:
            k.yks.send(bytes([bayt]))
            time.sleep(0.001)
            k.tur()
            veri, _ = statik.recv()
            if veri:
                erken.append(veri)
        self.assertEqual([], erken, "newline gelmeden parca datagram cikti")
        k.yks.send(ham[-1:])                       # son bayt: newline
        gelen = k.topla(statik, 1)
        self.assertEqual(1, len(gelen), "butun cerceve gelmedi")
        _tek_cerceve_dogrula(self, gelen[0], mesaj)
        # fazladan (parca) datagram yok
        self.assertEqual([], k.topla(statik, 1, tavan_s=0.2))
        self.assertEqual(1, k.hub.sayac["seri_cerceve"])

    def test_6_bozuk_cerceve_yayinlanmaz_sonraki_gecerli_gecer(self):
        """JSON olmayan satir, dict olmayan JSON: fan-out YOK, bozuk sayaci;
        ardindan gecerli cerceve GECER (hat kilitlenmez)."""
        statik = _tuketici()
        self.addCleanup(statik.close)
        k = _HubKurulum(self, tuketiciler=[(YEREL, statik.port)])
        mesaj = open_route(3, 0.8, [[0, 0], [0.0, 1.0]], [0.0, 0.0], seq=42)
        k.yks.send(b"\xff\xfe bozuk cop {yanlis json\n")
        k.yks.send(b"42\n")                        # gecerli JSON ama dict degil
        k.yks.send(encode(mesaj))
        gelen = k.topla(statik, 1)
        self.assertEqual(1, len(gelen), "bozuk sonrasi gecerli cerceve gecmedi")
        _tek_cerceve_dogrula(self, gelen[0], mesaj)
        self.assertEqual([], k.topla(statik, 1, tavan_s=0.2),
                         "bozuk cerceve datagram olarak sizdi")
        self.assertEqual(2, k.hub.sayac["bozuk"])
        self.assertEqual(1, k.hub.sayac["seri_cerceve"])
        self.assertEqual(1, k.hub.sayac["fanout_gonderim"])

    def test_7_statik_ve_ogrenilen_ayni_adres_TEK_datagram_alir(self):
        """iha_komut_alici hem statik (5007) hem ACK gonderdigi icin ogrenilen
        olur; fan-out tekildir — cerceve IKI KEZ gitmez."""
        statik = _tuketici()
        self.addCleanup(statik.close)
        k = _HubKurulum(self, tuketiciler=[(YEREL, statik.port)])
        statik.send(encode(heartbeat("iha", seq=2)), k.hub_adr)
        k.tur(3)
        self.assertIn((YEREL, statik.port), k.hub.ogrenilen)
        self.assertEqual([(YEREL, statik.port)], k.hub.hedefler())
        mesaj = command("PARACHUTE", "iha", seq=9)
        k.yks_yaz(mesaj)
        gelen = k.topla(statik, 2, tavan_s=1.0)
        self.assertEqual(1, len(gelen), f"cerceve {len(gelen)} kez geldi")
        _tek_cerceve_dogrula(self, gelen[0], mesaj)


@unittest.skipIf(serial is None, "pyserial kurulu degil")
class TestSeriHubAriza(unittest.TestCase):

    def test_4_seri_okuma_arizasi_hub_cokmez_dusurur_yeniden_acar(self):
        """recv OSError -> seri kapatilir (KIRMIZI), UDP cerceveleri
        DUSURULUR (kuyruk yok), 1 s dolmadan deneme yok, ilk yeniden acma
        denemesi patlarsa sayilir, ikinci link verince fan-out yeniden calisir."""
        saat = _SahteSaat(1000.0)
        statik = _tuketici()
        tuketici = _tuketici()
        self.addCleanup(statik.close)
        self.addCleanup(tuketici.close)
        kopru2 = SikKoprusu()
        self.addCleanup(kopru2.kapat)
        yeni_link = _uc(kopru2)
        yks2 = _uc(kopru2)
        self.addCleanup(yks2.close)
        seri_ac = mock.Mock(side_effect=[serial.SerialException("port yok"),
                                         yeni_link])
        k = _HubKurulum(self, tuketiciler=[(YEREL, statik.port)],
                        seri_ac=seri_ac, saat=saat)
        # saglikli on kosul: seri -> statik calisiyor
        k.yks_yaz(heartbeat("yks", seq=1))
        self.assertEqual(1, len(k.topla(statik, 1)))

        # ARIZA: okuma OSError
        k.hub_seri.recv = mock.Mock(side_effect=OSError("USB koptu"))
        k.tur()
        self.assertIsNone(k.hub.seri_link, "arizada seri kapatilmadi")
        self.assertEqual(1, k.hub.sayac["seri_ariza"])
        self.assertIn("KIRMIZI", k.log.getvalue())
        self.assertIn("okuma ARIZASI", k.log.getvalue())
        self.assertFalse(k.hub_seri.ser.is_open, "arizali port gercekten kapanmali")

        # arizada UDP'den gelen cerceve DUSURULUR, kuyruklanmaz
        tuketici.send(encode(command("PARACHUTE", "iha", seq=3)), k.hub_adr)
        k.tur(3)
        self.assertEqual(1, k.hub.sayac["dusurulen"])
        self.assertEqual(0, k.hub.sayac["seri_yazilan"])
        self.assertEqual(0, seri_ac.call_count, "1 s dolmadan yeniden acma denendi")

        # 1 s dolmadan: deneme yok
        saat.t += modul.SERI_YENIDEN_ACMA_ARALIGI_S / 2
        k.tur()
        self.assertEqual(0, seri_ac.call_count)
        # 1 s doldu: ilk deneme PATLAR -> sayilir, hub yasar
        saat.t += modul.SERI_YENIDEN_ACMA_ARALIGI_S
        k.tur()
        self.assertEqual(1, seri_ac.call_count)
        self.assertEqual(1, k.hub.sayac["yeniden_acma_hatasi"])
        self.assertEqual(0, k.hub.sayac["yeniden_acma"])
        self.assertIsNone(k.hub.seri_link)
        self.assertIn("yeniden acma BASARISIZ", k.log.getvalue())
        # ikinci deneme (yine 1 s sonra) YENI link verir
        k.tur()
        self.assertEqual(1, seri_ac.call_count, "aralik dolmadan tekrar denedi")
        saat.t += modul.SERI_YENIDEN_ACMA_ARALIGI_S
        k.tur()
        self.assertEqual(2, seri_ac.call_count)
        self.assertEqual(1, k.hub.sayac["yeniden_acma"])
        self.assertIs(yeni_link, k.hub.seri_link)
        self.assertIn("YENIDEN ACILDI", k.log.getvalue())

        # fan-out yeniden calisiyor (yeni kopru uzerinden)
        mesaj = command("IKA_GO", "ika", seq=8)
        yks2.send(encode(mesaj))
        gelen = k.topla(statik, 1)
        self.assertEqual(1, len(gelen), "yeniden acma sonrasi fan-out yok")
        _tek_cerceve_dogrula(self, gelen[0], mesaj)
        # UDP -> seri de yeniden calisiyor; dusurulen artmaz
        cmd = command("PARACHUTE", "iha", seq=4)
        tuketici.send(encode(cmd), k.hub_adr)
        with _Yakala(k.log):
            m, _ = _seri_cerceve_bekle(yks2, FrameReader(),
                                       lambda x: x.get("seq") == 4,
                                       pompa=k.hub.poll)
        self.assertEqual(cmd, m, "yeniden acma sonrasi UDP -> seri yok")
        self.assertEqual(1, k.hub.sayac["dusurulen"])
        self.assertEqual(1, k.hub.sayac["seri_yazilan"])

    def test_4b_seri_yazma_arizasi_da_kapatir_ve_dusurur(self):
        """send SerialException -> ayni ariza yolu: seri kapali, datagram
        dusurulen sayilir, seri_ac yoksa KIRMIZI 'yeniden acici yok' logu."""
        tuketici = _tuketici()
        self.addCleanup(tuketici.close)
        k = _HubKurulum(self)
        k.hub_seri.send = mock.Mock(side_effect=serial.SerialException("yazma"))
        tuketici.send(encode(heartbeat("iha", seq=1)), k.hub_adr)
        k.tur(3)
        self.assertIsNone(k.hub.seri_link)
        self.assertEqual(1, k.hub.sayac["seri_ariza"])
        self.assertEqual(1, k.hub.sayac["dusurulen"])
        self.assertEqual(0, k.hub.sayac["seri_yazilan"])
        log = k.log.getvalue()
        self.assertIn("yazma ARIZASI", log)
        self.assertIn("yeniden acici yok", log)
        # hub yasamaya devam eder, ikinci datagram da dusurulur
        tuketici.send(encode(heartbeat("iha", seq=2)), k.hub_adr)
        k.tur(3)
        self.assertEqual(2, k.hub.sayac["dusurulen"])


class _SahteMav:
    """Donanim ucu mock'u (kalip: tests/test_faz_b_iha_komut_alici.py):
    command_long_send kaydeder, ardindan Pixhawk gibi COMMAND_ACK ACCEPTED doner."""

    def __init__(self, kaynak_sysid):
        from pymavlink import mavutil
        self._m = mavutil.mavlink
        self.kaynak_sysid = kaynak_sysid
        self._bekleyen = []

        def kaydet(sys_id, comp, mav_cmd, *_):
            self._bekleyen.append(int(mav_cmd))

        self.mav = mock.Mock(name="mav")
        self.mav.command_long_send = mock.Mock(name="command_long_send",
                                               side_effect=kaydet)

    def recv_match(self, type=None, blocking=False, timeout=None, **_):
        if type == "COMMAND_ACK" and self._bekleyen:
            cmd = self._bekleyen.pop(0)
            return SimpleNamespace(command=cmd, result=self._m.MAV_RESULT_ACCEPTED,
                                   get_srcSystem=lambda: self.kaynak_sysid)
        if blocking and timeout:
            time.sleep(min(float(timeout), 0.6))
        return None


@unittest.skipIf(serial is None, "pyserial kurulu degil")
class TestSeriHubUctanUca(unittest.TestCase):

    def test_5_yks_seri_parachute_gercek_komut_alici_ack_seriye_doner(self):
        """YKS (seri) CMD PARACHUTE -> hub -> GERCEK IhaKomutAlici (UDP, statik
        tuketici) -> sahte Pixhawk COMMAND_ACK -> ACK -> hub -> seri -> YKS
        ACK(ref=seq, node=iha, ref_tip=CMD) OKUR. Hub ve alici kendi
        `calistir` dongulerinde (ayri iplikler)."""
        try:
            from pymavlink import mavutil
        except ImportError:  # pragma: no cover
            self.skipTest("pymavlink kurulu degil")
        import iha_komut_alici as alici_modul
        from iha_komut_alici import IhaKomutAlici

        sysid = alici_modul.VARSAYILAN_HEDEF_SYSID
        mav = _SahteMav(kaynak_sysid=sysid)
        alici_link = UDPLink(bind=(YEREL, 0), timeout=0.05)
        self.addCleanup(alici_link.close)
        alici = IhaKomutAlici(alici_link, mav, target_system=sysid)
        k = _HubKurulum(self, tuketiciler=[(YEREL, alici_link.port)])

        cmd = command("PARACHUTE", "iha", seq=41)
        with _Yakala(k.log):
            hub_thr = threading.Thread(target=k.hub.calistir, daemon=True)
            alici_thr = threading.Thread(target=alici.calistir, daemon=True)
            hub_thr.start()
            alici_thr.start()
            try:
                k.yks.send(encode(cmd))
                gelen, hepsi = _seri_cerceve_bekle(
                    k.yks, FrameReader(),
                    lambda m: m.get("type") == "ACK" and m.get("ref") == 41)
            finally:
                alici.durdur()
                k.hub.durdur()
                alici_thr.join(timeout=2.0)
                hub_thr.join(timeout=2.0)
        self.assertFalse(hub_thr.is_alive(), "hub durdur() ile cikmadi")
        self.assertFalse(alici_thr.is_alive())
        self.assertIsNotNone(gelen, f"YKS ACK okumadi; gelenler={hepsi} "
                                    f"log={k.log.getvalue()[-1500:]}")
        self.assertEqual("ACK", gelen["type"])
        self.assertEqual(41, gelen["ref"])
        self.assertEqual("iha", gelen["node"])
        self.assertEqual("CMD", gelen["ref_tip"])
        mav.mav.command_long_send.assert_called_once()
        self.assertEqual(mavutil.mavlink.MAV_CMD_DO_PARACHUTE,
                         mav.mav.command_long_send.call_args[0][2])
        self.assertEqual(1, alici.sayac["ack"])
        self.assertEqual(1, alici.sayac["aktarilan"])
        self.assertGreaterEqual(k.hub.sayac["seri_cerceve"], 1)   # CMD
        self.assertGreaterEqual(k.hub.sayac["udp_alinan"], 1)     # ACK
        self.assertGreaterEqual(k.hub.sayac["seri_yazilan"], 1)
        self.assertEqual(0, k.hub.sayac["dusurulen"])
        self.assertEqual(0, k.hub.sayac["bozuk"])
        # alici hem statik hem (ACK ile) ogrenilen: hedef listesi TEKIL
        self.assertEqual([(YEREL, alici_link.port)], k.hub.hedefler())


class TestSeriHubCli(unittest.TestCase):

    def test_8_adres_cozumleme_ve_tekillik(self):
        self.assertEqual((YEREL, 5007), modul._adres("127.0.0.1:5007"))
        self.assertEqual((YEREL, 5007), modul._adres("localhost:5007"))
        for kotu in ("5007", "127.0.0.1:0", "127.0.0.1:70000", "127.0.0.1:x"):
            with self.assertRaises(ValueError, msg=kotu):
                modul._adres(kotu)
        with self.assertRaises(SystemExit) as cm, \
                contextlib.redirect_stderr(io.StringIO()):
            modul.main(["--port", "loop://", "--tuketici", "kotu"])
        self.assertEqual(2, cm.exception.code)

    def test_9_cli_seri_acilamazsa_cikis_4_kirmizi_hub_kurulmaz(self):
        """Yanlis --port: sessiz bekleme yok; KIRMIZI + cikis 4; UDP ucu
        kapatilir (port sizintisi yok)."""
        hata = io.StringIO()
        with mock.patch.object(modul, "SeriHub") as hub_sinifi, \
                contextlib.redirect_stderr(hata), \
                contextlib.redirect_stdout(io.StringIO()):
            kod = modul.main(["--port", "COM_YOK_BOYLE_BIR_PORT",
                              "--bind", f"{YEREL}:0"])
        self.assertEqual(4, kod)
        self.assertIn("KIRMIZI", hata.getvalue())
        self.assertIn("seri port acilamadi", hata.getvalue())
        hub_sinifi.assert_not_called()

    def test_10_cli_loop_portu_ile_hub_kurulur_ve_durur(self):
        """`loop://` ile gercek pyserial ucu; hub calistir()'a girer, durdur()
        ile cikar (CLI yolunun butunu: parse -> UDP -> seri -> SeriHub)."""
        if serial is None:
            self.skipTest("pyserial kurulu degil")
        kurulan = {}
        orijinal = modul.SeriHub

        def yakala(*a, **kw):
            hub = orijinal(*a, **kw)
            kurulan["hub"] = hub
            threading.Timer(0.2, hub.durdur).start()
            return hub

        with mock.patch.object(modul, "SeriHub", side_effect=yakala), \
                contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()):
            kod = modul.main(["--port", "loop://", "--bind", f"{YEREL}:0",
                              "--tuketici", f"{YEREL}:5007",
                              "--tuketici", f"localhost:5007",
                              "--log-aralik", "0"])
        self.assertEqual(0, kod)
        hub = kurulan["hub"]
        self.assertEqual([(YEREL, 5007)], hub.tuketiciler, "statik tekillesmedi")
        self.assertIsNone(hub.seri_link, "kapat() seriyi birakmadi")


if __name__ == "__main__":
    unittest.main()
