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

D-405 (curutucu turu; mercekler PROTOKOL/ACK, ARIZA/YENIDEN ACMA, TEST
VAKUMU) ile eklenen kilitler — her biri o turda KACAN bir mutanti dusurur:
  * hicbir cerceve hub'i oldurmez: derin ic ice satir (RecursionError) ve
    cozucuden sizan HER istisna `bozuk` + KIRMIZI, sonraki cerceve gecer;
  * tek sahiplik: `UDPLink(reuse=False)` ikinci bind OSError; ayni --bind ile
    ikinci hub `main` -> 3; `SerialLink` `exclusive=True` ile acar;
  * zamanlama: sabitler parasut tekrar araligina bagli tavanin altinda,
    kurulan hub soketleri o degere ceker; ON KAYITLI gecikme kapisi
    (test_16 dokstringi);
  * newline'siz datagram: newline eklenir, sayilir, ilkinde KIRMIZI;
  * tavan ustu datagram tam alinir; UDP okuma OSError hub'i oldurmez;
  * SIGTERM -> durdur() (systemd stop'ta son sayac satiri);
  * vakum: iki OGRENILEN tuketici, "kuyruklanmaz" TELDE, tavan tahliyesi
    (en az tazelenen + KIRMIZI), yeniden acmada okuyucu sifirlamasi,
    bos tur beklemesi, tek turda datagram patlamasi, seri_ac None,
    hedefsiz/yazilamayan fan-out sayaclari.

⚠ Windows zamanlayici tanecigi 15,6 ms (D-405 olcumu, olc_granul.py): 1 ms
UDP zaman asimi fiilen ~15,6 ms, 20 ms seri zaman asimi ~31 ms, bos
`hub.poll` ~47 ms (Linux/Jetson'da ~21 ms). 0,2 s'lik negatif pencereler
Windows'ta yalniz ~4 turdur; pozitif tavanlar (TAVAN_S) bunun ≥ 30 kati.
"""
import contextlib
import io
import random
import signal
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
from karar_sozlesmesi import PARASUT_TEKRAR_ARALIGI_S  # noqa: E402
from link import SerialLink, UDPLink  # noqa: E402
from protocol import (FrameReader, command, decode, encode,  # noqa: E402
                      heartbeat, open_route, rota_yok)
from test_p2_seri_hat import SikKoprusu  # noqa: E402
# Derin ic ice satir tek yerde tanimli (protokol dayaniklilik testi); hub
# testi ayni tetikleyiciyi kullanir ki iki dosya birbirinden sapmasin.
from test_faz_b_protocol_dayaniklilik import _derin_satir  # noqa: E402

YEREL = "127.0.0.1"
TAVAN_S = 3.0                       # gercek soketlerde bekleme tavani
UC_ZAMAN_ASIMI_S = 0.02             # test uclari: pompalama dongusu tikanmasin
TUKETICI_ZAMAN_ASIMI_S = 0.01

# ── D-405 zamanlama kilidi (madde 16: tavanlar sozlesmeden TURETILIR) ────────
# NEDEN: D-403'te 0,3 s'lik seri zaman asimi tek iplikli hubda UDP->seri
# yonunu her turda 300 ms bekletip ACK turunu 622 ms'e cikarmisti — parasut
# tekrar araliginin (0,20 s) ustu. D-405 olctu: o deger geri gelse 11/11
# yesil kaliyordu (M8/M9 mutantlari kacti). Tavanlar parasut araligina bagli:
# seri okuma zaman asimi araligin en cok 1/4'u (0,05 s; bir turda iki yon +
# Windows tanecigi sigsin), UDP zaman asimi 1/20'si (0,01 s; UDP tarafi
# fiilen non-blocking kalsin). CONTRACTS §7.5 "zamanlama" satiriyla aynidir.
SERI_ZAMAN_ASIMI_TAVANI_S = PARASUT_TEKRAR_ARALIGI_S / 4
UDP_ZAMAN_ASIMI_TAVANI_S = PARASUT_TEKRAR_ARALIGI_S / 20
#: D-403'un gerileme degeri (UDPLink varsayilani da bu): hub'a bilerek bu
#: gevsek zaman asimiyla soket verilir, hub'in kendi degerine cektigi kilitlenir.
GEVSEK_ZAMAN_ASIMI_S = 0.3
#: On kayitli gecikme kapisi ornek sayisi ve faz kirici bekleme tavani
#: (D-405 olc_granul.py: faz kilitli olcum p50'yi 0,3 ms gosterip yaniltti).
GECIKME_ORNEK_SAYISI = 30
FAZ_KIRICI_TAVAN_S = 0.1
#: D-405 oncesi `udp_link.recv()` varsayilan tamponu — Windows'ta bunun ustu
#: datagram WinError 10040 ile hub'i olduruyordu (r5_buyuk.py). Test datagrami
#: bu eski tavanin USTUNDE, yeni tavanin altinda olmak zorunda.
ESKI_UDP_RECV_TAVANI_B = 4096
BUYUK_DATAGRAM_HEDEF_B = 5000


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
            m, hepsi = _seri_cerceve_bekle(yks2, FrameReader(),
                                           lambda x: x.get("seq") == 4,
                                           pompa=k.hub.poll)
        self.assertEqual(cmd, m, "yeniden acma sonrasi UDP -> seri yok")
        # D-405 (mutant c2 kacti): "kuyruklanmaz" SAYACLA degil TELDE kilitli —
        # arizada dusurulen seq=3 yeni hatta ASLA gorunmez (bayat rota yok).
        self.assertEqual([4], [x.get("seq") for x in hepsi],
                         f"bayat (dusurulen) cerceve telde gorundu: {hepsi}")
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
        # D-405 (mutant M6 kacti): kapat() UDP soketini de birakir (port sizmaz)
        self.assertEqual(-1, hub.udp_link.sock.fileno(),
                         "kapat() UDP soketini kapatmadi")


# ── D-405: hicbir cerceve / datagram hub'i oldurmez ─────────────────────────

class _BirKezPatlayanOkuyucu:
    """Ilk feed'de cozucu istisnasi (RecursionError sinifinin genel hali),
    sonra gercek FrameReader'a devreder. Hub'in `_cerceveleri_isle` sarmalini
    protocol.py'den BAGIMSIZ kilitler (savunma derinligi)."""

    def __init__(self):
        self.gercek = FrameReader()
        self.patladi = False

    @property
    def atilan_bayt(self):
        return self.gercek.atilan_bayt

    @property
    def _buf(self):
        return self.gercek._buf

    def feed(self, veri):
        if not self.patladi:
            self.patladi = True
            raise RuntimeError("cozucu patladi (sahte)")
        return self.gercek.feed(veri)


@unittest.skipIf(serial is None, "pyserial kurulu degil")
class TestSeriHubDayaniklilik(unittest.TestCase):

    def test_11_derin_ic_ice_satir_hubu_oldurmez_bozuk_sayar_sonraki_gecer(self):
        """D-405 ONEMLI: YKS ucundan `[`*3000+newline (json RecursionError)
        GERCEK kopru uzerinden gelir: poll istisnasiz, seri acik kalir,
        `bozuk` 1 artar, cerceve yayinlanmaz; sonraki gecerli cerceve AYNI
        okuyucudan statik tuketiciye gecer. (Onceki kod: hub sureci exit 1.)"""
        statik = _tuketici()
        self.addCleanup(statik.close)
        k = _HubKurulum(self, tuketiciler=[(YEREL, statik.port)])
        k.yks.send(_derin_satir())
        bitis = time.monotonic() + TAVAN_S * 2      # 3 KiB, socket:// 2 B/okuma
        while time.monotonic() < bitis and k.hub.sayac["bozuk"] < 1:
            k.tur()                                  # ISTISNA SIZARSA BURADA PATLAR
        self.assertEqual(1, k.hub.sayac["bozuk"], "derin satir bozuk sayilmadi")
        self.assertIsNotNone(k.hub.seri_link, "derin satir seriyi kapattirdi")
        self.assertEqual(0, k.hub.sayac["seri_cerceve"])
        self.assertEqual(b"", k.hub.okuyucu._buf, "derin satir tamponda kaldi")
        self.assertEqual([], k.topla(statik, 1, tavan_s=0.2),
                         "derin satir datagram olarak sizdi")
        mesaj = command("PARACHUTE", "iha", seq=99)
        k.yks_yaz(mesaj)
        gelen = k.topla(statik, 1)
        self.assertEqual(1, len(gelen), "derin satir sonrasi gecerli cerceve gecmedi")
        _tek_cerceve_dogrula(self, gelen[0], mesaj)
        self.assertEqual(1, k.hub.sayac["bozuk"])
        self.assertEqual(1, k.hub.sayac["seri_cerceve"])

    def test_11b_cozucuden_sizan_her_istisna_hub_sarmalinda_yutulur_kirmizi(self):
        """Savunma derinligi: okuyucu `feed` RuntimeError firlatsa bile poll
        yasar, parca `bozuk` sayilir, KIRMIZI 'cozme ISTISNASI' logu; sonraki
        cerceve gecer. protocol.py'nin except listesinden BAGIMSIZ kilit."""
        statik = _tuketici()
        self.addCleanup(statik.close)
        k = _HubKurulum(self, tuketiciler=[(YEREL, statik.port)])
        k.hub.okuyucu = _BirKezPatlayanOkuyucu()
        m1 = heartbeat("yks", seq=1)
        m2 = command("IKA_GO", "ika", seq=2)
        k.hub_seri.recv = mock.Mock(side_effect=[(encode(m1), None), (None, None),
                                                 (encode(m2), None), (None, None)])
        k.tur()                                      # patlar -> yutulmali
        self.assertEqual(1, k.hub.sayac["bozuk"])
        self.assertEqual(0, k.hub.sayac["seri_cerceve"])
        self.assertIsNotNone(k.hub.seri_link)
        log = k.log.getvalue()
        self.assertIn("KIRMIZI", log)
        self.assertIn("cozme ISTISNASI", log)
        self.assertIn("RuntimeError", log)
        gelen = k.topla(statik, 1)
        self.assertEqual(1, len(gelen), "istisna sonrasi cerceve gecmedi")
        _tek_cerceve_dogrula(self, gelen[0], m2)
        self.assertEqual(1, k.hub.sayac["seri_cerceve"])

    def test_12_newline_siz_datagram_newline_eklenir_ikisi_de_yks_okur_sayac_kirmizi(self):
        """D-405 Q1: newline'siz datagram seride komsusuna yapisip IKISINI de
        oldururdu (olculdu: seri_yazilan=2, YKS 0 cerceve). Simdi hub newline
        EKLER: YKS iki cerceveyi de okur, `newline_eklenen` sayar, ilkinde
        KIRMIZI; ikincisi yalniz sayacta (log seli yok)."""
        tuketici = _tuketici()
        self.addCleanup(tuketici.close)
        k = _HubKurulum(self)
        m1 = command("PARACHUTE", "iha", seq=11)
        m2 = command("PARACHUTE", "iha", seq=12)
        tuketici.send(encode(m1)[:-1], k.hub_adr)          # newline YOK
        tuketici.send(encode(m2), k.hub_adr)                # newline VAR
        m, hepsi = k.yks_bekle(lambda x: x.get("seq") == 12)
        self.assertEqual(m2, m, f"gelenler={hepsi}")
        self.assertEqual([m1, m2], hepsi, "newline'siz datagram komsusuyla kayboldu")
        self.assertEqual(1, k.hub.sayac["newline_eklenen"])
        self.assertEqual(2, k.hub.sayac["seri_yazilan"])
        log = k.log.getvalue()
        self.assertIn("KIRMIZI", log)
        self.assertIn("newline'siz datagram", log)
        self.assertIn(f"{YEREL}:{tuketici.port}", log)
        # ikinci newline'siz: sayac artar, log tekrarlanmaz
        m3 = heartbeat("iha", seq=13)
        tuketici.send(encode(m3)[:-1], k.hub_adr)
        m, hepsi = k.yks_bekle(lambda x: x.get("seq") == 13)
        self.assertEqual(m3, m)
        self.assertEqual(2, k.hub.sayac["newline_eklenen"])
        self.assertEqual(1, k.log.getvalue().count("newline'siz datagram"))

    def test_13_eski_tavan_ustu_datagram_TAM_alinir_hub_yasar_bayt_es(self):
        """D-405: 4096 B ustu datagram Windows'ta OSError 10040 ile hub'i
        olduruyor, Linux'ta budanip newline'siz parca seriye gidiyordu. Simdi
        tam datagram alinir (UDP_DATAGRAM_TAVANI_B), YKS BAYT-ES okur,
        `udp_hata` 0."""
        tuketici = _tuketici()
        self.addCleanup(tuketici.close)
        k = _HubKurulum(self)
        # Mesru mesaj tipi (NO_ROUTE, serbest metin `detay`); en uzun mesru
        # OPEN_ROUTE 1407 B oldugundan (D-405 olcumu) buyuk cerceve boyle kurulur.
        bos = len(encode(rota_yok("test", detay="", seq=1)))
        mesaj = rota_yok("test", detay="x" * (BUYUK_DATAGRAM_HEDEF_B - bos), seq=1)
        ham = encode(mesaj)
        self.assertGreater(len(ham), ESKI_UDP_RECV_TAVANI_B, "on kosul: eski tavanin ustu")
        self.assertLess(len(ham), modul.UDP_DATAGRAM_TAVANI_B, "on kosul: yeni tavanin alti")
        tuketici.send(ham, k.hub_adr)
        with _Yakala(k.log):
            gelen = _seri_ham_bekle(k.yks, pompa=k.hub.poll, tavan_s=TAVAN_S * 2)
        self.assertEqual(ham, gelen, "buyuk datagram seride bayt-es degil (budandi?)")
        self.assertEqual(1, k.hub.sayac["udp_alinan"])
        self.assertEqual(1, k.hub.sayac["seri_yazilan"])
        self.assertEqual(0, k.hub.sayac["udp_hata"])
        self.assertEqual(0, k.hub.sayac["newline_eklenen"])
        self.assertIsNotNone(k.hub.seri_link)

    def test_13b_udp_okuma_oserror_hub_yasar_udp_hata_sayilir_ilkinde_kirmizi(self):
        """recv OSError (10040 sinifi): poll istisnasiz, `udp_hata` sayilir,
        ilkinde KIRMIZI, ikincisi yalniz sayacta; recv duzelince datagramlar
        yeniden seriye gider (ogrenilen kume korunur)."""
        tuketici = _tuketici()
        self.addCleanup(tuketici.close)
        k = _HubKurulum(self)
        k.udp.recv = mock.Mock(side_effect=OSError("[WinError 10040] tavan ustu"))
        k.tur()                                      # SIZARSA burada patlar
        k.tur()
        self.assertEqual(2, k.hub.sayac["udp_hata"])
        self.assertIsNotNone(k.hub.seri_link, "UDP hatasi seriyi kapattirdi")
        log = k.log.getvalue()
        self.assertIn("KIRMIZI", log)
        self.assertEqual(1, log.count("UDP okuma HATASI"), "log seli / log yok")
        del k.udp.recv                               # gercek recv geri
        mesaj = command("ARM", "iha", seq=5)
        tuketici.send(encode(mesaj), k.hub_adr)
        m, _ = k.yks_bekle(lambda x: x.get("seq") == 5)
        self.assertEqual(mesaj, m, "UDP hatasi sonrasi UDP -> seri yok")
        self.assertEqual(2, k.hub.sayac["udp_hata"])
        self.assertEqual(1, k.hub.sayac["seri_yazilan"])


# ── D-405: tek sahiplik ──────────────────────────────────────────────────────

@unittest.skipIf(serial is None, "pyserial kurulu degil")
class TestSeriHubTekSahiplik(unittest.TestCase):

    def test_14_udplink_reuse_false_ikinci_bind_oserror(self):
        """`UDPLink(reuse=False)`: ayni porta ikinci bind OSError (once
        SO_REUSEADDR ile sessizce basariliyor, ikinci soket hic datagram
        almiyordu — r_cift_bind.py). Varsayilan reuse=True eski davranis."""
        a = UDPLink(bind=(YEREL, 0), timeout=TUKETICI_ZAMAN_ASIMI_S, reuse=False)
        self.addCleanup(a.close)
        with self.assertRaises(OSError):
            b = UDPLink(bind=(YEREL, a.port), timeout=TUKETICI_ZAMAN_ASIMI_S,
                        reuse=False)
            b.close()
        # reuse=True olan bir soket de tek sahipli portu CALAMAZ
        with self.assertRaises(OSError):
            c = UDPLink(bind=(YEREL, a.port), timeout=TUKETICI_ZAMAN_ASIMI_S)
            c.close()
        # tek sahipli soket normal calisir
        g = _tuketici()
        self.addCleanup(g.close)
        g.send(b"dg", (YEREL, a.port))
        self.assertEqual([b"dg"], _datagramlari_topla(a, 1, tavan_s=1.0))

    def test_14b_ayni_bind_ile_ikinci_hub_main_cikis_3_kirmizi(self):
        """GERCEK ikinci hub: ilk `main` (loop://) iplikte calisirken ayni
        --bind ile ikinci `main` UDP ucunu acamaz -> 3, KIRMIZI, SeriHub
        kurulmaz (runbook manuel komut + systemd birimi senaryosu)."""
        kurulan = {}
        hublar = []
        bekciler = []
        hazir = threading.Event()
        orijinal = modul.SeriHub

        def yakala(*a, **kw):
            hub = orijinal(*a, **kw)
            hublar.append(hub)
            # Bekci: kurulan HER hub tavan icinde durdurulur — aksi halde bir
            # gerileme (ikinci hub porta baglanip calistir'a girerse) bu testi
            # SONSUZA dek asar (olculdu: mutant x9 kosucuyu kilitledi).
            bekci = threading.Timer(TAVAN_S, hub.durdur)
            bekci.daemon = True
            bekci.start()
            bekciler.append(bekci)
            hazir.set()
            return hub

        cikti = io.StringIO()
        with mock.patch.object(modul, "SeriHub", side_effect=yakala) as hub_sinifi, \
                contextlib.redirect_stdout(cikti), contextlib.redirect_stderr(cikti):
            ilk = threading.Thread(
                target=lambda: kurulan.setdefault("kod1", modul.main(
                    ["--port", "loop://", "--bind", f"{YEREL}:0", "--log-aralik", "0"])),
                daemon=True)
            ilk.start()
            try:
                self.assertTrue(hazir.wait(TAVAN_S), "ilk hub kurulmadi")
                port = hublar[0].udp_link.port
                kod2 = modul.main(["--port", "loop://", "--bind", f"{YEREL}:{port}",
                                   "--log-aralik", "0"])
            finally:
                for hub in hublar:
                    hub.durdur()
                ilk.join(timeout=TAVAN_S)
                for bekci in bekciler:
                    bekci.cancel()
        self.assertEqual(3, kod2, "ikinci hub ayni porta sessizce baglandi")
        self.assertEqual(1, hub_sinifi.call_count, "ikinci hub SeriHub kurdu")
        self.assertFalse(ilk.is_alive(), "ilk hub durdur() ile cikmadi")
        self.assertEqual(0, kurulan.get("kod1"))
        log = cikti.getvalue()
        self.assertIn("KIRMIZI HATA: UDP ucu acilamadi", log)
        self.assertIn("systemctl stop navitas-seri-hub", log)

    def test_14c_seriallink_exclusive_true_varsayilan_pyserial_e_gecer(self):
        """`SerialLink` `serial_for_url(..., exclusive=True)` ile acar (Linux'ta
        flock: ikinci surec SerialException). Windows'ta flock yok; kilit,
        parametrenin pyserial'e GERCEKTEN gectigidir. `loop://` ve `socket://`
        exclusive=True'yu kabul eder (bu dosyanin tum uclari boyle acilir)."""
        with mock.patch.object(serial, "serial_for_url") as sfu:
            SerialLink("loop://", modul.VARSAYILAN_BAUD, timeout=UC_ZAMAN_ASIMI_S)
        sfu.assert_called_once_with("loop://", modul.VARSAYILAN_BAUD,
                                    timeout=UC_ZAMAN_ASIMI_S, exclusive=True)
        with mock.patch.object(serial, "serial_for_url") as sfu:
            SerialLink("loop://", modul.VARSAYILAN_BAUD, timeout=UC_ZAMAN_ASIMI_S,
                       exclusive=False)
        sfu.assert_called_once_with("loop://", modul.VARSAYILAN_BAUD,
                                    timeout=UC_ZAMAN_ASIMI_S, exclusive=False)
        # gercek acilis: loop:// exclusive varsayilaniyla acilir ve calisir
        link = SerialLink("loop://", modul.VARSAYILAN_BAUD, timeout=UC_ZAMAN_ASIMI_S)
        self.addCleanup(link.close)
        link.send(b"abc")
        veri, _ = link.recv()
        self.assertEqual(b"abc", veri)
        # CLI seri_ac da ayni siniftan gecer (main -> SerialLink)
        self.assertIs(modul.SerialLink, SerialLink)


# ── D-405: zamanlama kilidi ──────────────────────────────────────────────────

def _yuzdelik(degerler, p):
    s = sorted(degerler)
    return s[min(len(s) - 1, int(round(p / 100.0 * (len(s) - 1))))]


@unittest.skipIf(serial is None, "pyserial kurulu degil")
class TestSeriHubZamanlama(unittest.TestCase):

    def test_15_zaman_asimi_sabitleri_parasut_araligina_bagli_hub_soketlere_uygular(self):
        """Sabit kilidi (M8/M9 kacmisti): seri okuma zaman asimi <= parasut
        araliginin 1/4'u, UDP <= 1/20'si, UDP > 0 (0 BlockingIOError sizdirir).
        Kurulan hub, kendisine GEVSEK (0,3 s) zaman asimiyla verilen seri ve
        UDP soketlerini kendi sabitlerine ceker (M5 kacmisti)."""
        self.assertLessEqual(modul.SERI_OKUMA_ZAMAN_ASIMI_S, SERI_ZAMAN_ASIMI_TAVANI_S,
                             "D-403 gerilemesi: seri zaman asimi parasut araligina gore uzun")
        self.assertLessEqual(modul.UDP_OKUMA_ZAMAN_ASIMI_S, UDP_ZAMAN_ASIMI_TAVANI_S)
        self.assertGreater(modul.UDP_OKUMA_ZAMAN_ASIMI_S, 0)
        self.assertGreater(modul.SERI_OKUMA_ZAMAN_ASIMI_S, 0)
        self.assertLessEqual(modul.BOS_TUR_BEKLEME_S, SERI_ZAMAN_ASIMI_TAVANI_S)
        kopru = SikKoprusu()
        self.addCleanup(kopru.kapat)
        hub_seri = _uc(kopru, timeout=GEVSEK_ZAMAN_ASIMI_S)
        udp = UDPLink(bind=(YEREL, 0), timeout=GEVSEK_ZAMAN_ASIMI_S)
        self.assertEqual(GEVSEK_ZAMAN_ASIMI_S, hub_seri.ser.timeout, "on kosul")
        self.assertEqual(GEVSEK_ZAMAN_ASIMI_S, udp.sock.gettimeout(), "on kosul")
        with _Yakala(io.StringIO()):
            hub = SeriHub(hub_seri, udp, [])
        self.addCleanup(hub.kapat)
        self.assertEqual(modul.SERI_OKUMA_ZAMAN_ASIMI_S, hub.seri_link.ser.timeout,
                         "hub seri zaman asimini kendi sabitine cekmedi")
        self.assertEqual(modul.UDP_OKUMA_ZAMAN_ASIMI_S, hub.udp_link.sock.gettimeout(),
                         "hub UDP zaman asimini kendi sabitine cekmedi")
        # yeniden acmada da ayni: seri_ac'in verdigi link de cekilir
        kopru2 = SikKoprusu()
        self.addCleanup(kopru2.kapat)
        yeni = _uc(kopru2, timeout=GEVSEK_ZAMAN_ASIMI_S)
        hub._seri_bagla(yeni)
        self.assertEqual(modul.SERI_OKUMA_ZAMAN_ASIMI_S, yeni.ser.timeout)

    def test_16_udp_seri_gecikme_p95_parasut_araliginin_altinda_ON_KAYIT(self):
        """ON KAYIT (sonuc gorulmeden yazildi, D-405 §2 madde 5):
          * duzenek: GERCEK hub `calistir()` ayri iplikte, SikKoprusu
            (socket:// pyserial uclari), tuketici UDPLink; her ornekte
            rastgele faz beklemesi (0..FAZ_KIRICI_TAVAN_S) sonra PARACHUTE
            datagrami -> hub -> seri -> YKS ucu cerceveyi okur;
          * GECIKME_ORNEK_SAYISI (30) ornek, kayip 0/30;
          * KAPI: p95 < PARASUT_TEKRAR_ARALIGI_S (karar_sozlesmesi, 0,20 s);
          * mutasyon kontrolu: SERI_OKUMA_ZAMAN_ASIMI_S = 0.3 (D-403 gerilemesi,
            mutant M8) bu kapiyi DUSURMELIDIR (bosta her tur 0,3 s bekler ->
            p95 ~0,28 s);
          * beklenen (D-405 olcumu r2_gecikme/olc_granul): Windows p50 ~10 ms
            p95 ~31 ms (20 ms seri zaman asimi 15,6 ms tanecigiyle yuvarlanir);
            Linux/Jetson p95 ~21 ms. Kapi bunun >= 6 kati: tanecik kirilganligi
            yok. Sonuc ham olarak iddia mesajina yazilir."""
        k = _HubKurulum(self, log_aralik_s=0)
        tuketici = _tuketici()
        self.addCleanup(tuketici.close)
        rastgele = random.Random(7)
        okuyucu = FrameReader()
        gecikmeler = []
        kayip = []
        with _Yakala(k.log):
            hub_thr = threading.Thread(target=k.hub.calistir, daemon=True)
            hub_thr.start()
            try:
                for i in range(GECIKME_ORNEK_SAYISI):
                    time.sleep(rastgele.uniform(0.0, FAZ_KIRICI_TAVAN_S))
                    t0 = time.perf_counter()
                    tuketici.send(encode(command("PARACHUTE", "iha", seq=i)), k.hub_adr)
                    bitis = t0 + TAVAN_S
                    geldi = False
                    while time.perf_counter() < bitis and not geldi:
                        veri, _ = k.yks.recv()
                        if veri:
                            for m in okuyucu.feed(veri):
                                if m.get("seq") == i:
                                    geldi = True
                    if geldi:
                        gecikmeler.append(time.perf_counter() - t0)
                    else:
                        kayip.append(i)
            finally:
                k.hub.durdur()
                hub_thr.join(timeout=TAVAN_S)
        self.assertFalse(hub_thr.is_alive())
        self.assertEqual([], kayip, f"kayip ornekler: {kayip}")
        p50 = _yuzdelik(gecikmeler, 50) * 1000.0
        p95 = _yuzdelik(gecikmeler, 95) * 1000.0
        ozet = (f"n={len(gecikmeler)} p50={p50:.1f} ms p95={p95:.1f} ms "
                f"max={max(gecikmeler) * 1000.0:.1f} ms kapi={PARASUT_TEKRAR_ARALIGI_S * 1000:.0f} ms")
        self.assertLess(p95 / 1000.0, PARASUT_TEKRAR_ARALIGI_S,
                        f"UDP->seri gecikme kapisi DUSTU: {ozet}")
        self.assertEqual(GECIKME_ORNEK_SAYISI, k.hub.sayac["seri_yazilan"], ozet)


# ── D-405: SIGTERM ───────────────────────────────────────────────────────────

class TestSeriHubSigterm(unittest.TestCase):

    def test_17_sigterm_isleyicisi_durdur_cagirir_ve_geri_alinir(self):
        """`_sigterm_kur`: SIGTERM isleyicisi hub.durdur() cagirir (Windows'ta
        isleyici dogrudan cagrilir); `_sigterm_geri_al` onceki isleyiciyi
        koyar (test hijyeni / ust surec)."""
        hub = mock.Mock()
        onceki = signal.getsignal(signal.SIGTERM)
        eski = modul._sigterm_kur(hub)
        self.addCleanup(modul._sigterm_geri_al, eski)
        self.assertIsNot(eski, modul._SIGTERM_KURULAMADI, "ana iplikte kurulamadi")
        isleyici = signal.getsignal(signal.SIGTERM)
        self.assertTrue(callable(isleyici), f"SIGTERM isleyicisi yok: {isleyici!r}")
        self.assertNotIn(isleyici, (signal.SIG_DFL, signal.SIG_IGN))
        hub.durdur.assert_not_called()
        isleyici(signal.SIGTERM, None)
        hub.durdur.assert_called_once_with()
        modul._sigterm_geri_al(eski)
        self.assertEqual(onceki, signal.getsignal(signal.SIGTERM),
                         "onceki SIGTERM isleyicisi geri konmadi")

    def test_17b_cli_sigterm_hub_temiz_cikar_0_son_sayac_logu_basilir(self):
        """`main()` hub kurulunca SIGTERM isleyicisi kurar; isleyici (systemd
        stop gibi) tetiklenince dongu cikar, son sayac satiri basilir, cikis 0,
        isleyici geri alinir. Isleyici Timer ipliginden DOGRUDAN cagrilir
        (Windows'ta gercek SIGTERM yollanamaz)."""
        if serial is None:
            self.skipTest("pyserial kurulu degil")
        onceki = signal.getsignal(signal.SIGTERM)
        kayit = {}
        bekciler = []
        orijinal = modul.SeriHub

        def yakala(*a, **kw):
            hub = orijinal(*a, **kw)
            # Bekci: isleyici HIC kurulmazsa (gerileme) hub'i kimse durdurmaz
            # ve main() sonsuza dek doner (olculdu: mutant x10 kosucuyu
            # kilitledi). Tavan + pay sonra durdurulur; iddia yine duser.
            bekci = threading.Timer(TAVAN_S + 1.0, hub.durdur)
            bekci.daemon = True
            bekci.start()
            bekciler.append(bekci)
            return hub

        def tetikle():
            bitis = time.monotonic() + TAVAN_S
            while time.monotonic() < bitis:
                isleyici = signal.getsignal(signal.SIGTERM)
                if callable(isleyici) and isleyici not in (signal.SIG_DFL, signal.SIG_IGN) \
                        and isleyici is not onceki:
                    kayit["isleyici"] = isleyici
                    isleyici(signal.SIGTERM, None)
                    return
                time.sleep(0.01)
            kayit["isleyici"] = None

        cikti = io.StringIO()
        thr = threading.Thread(target=tetikle, daemon=True)
        with mock.patch.object(modul, "SeriHub", side_effect=yakala), \
                contextlib.redirect_stdout(cikti), contextlib.redirect_stderr(cikti):
            thr.start()
            try:
                kod = modul.main(["--port", "loop://", "--bind", f"{YEREL}:0",
                                  "--log-aralik", "0"])
            finally:
                for bekci in bekciler:
                    bekci.cancel()
        thr.join(timeout=TAVAN_S)
        self.assertIsNotNone(kayit.get("isleyici"), "main SIGTERM isleyicisi kurmadi")
        self.assertEqual(0, kod)
        self.assertEqual(onceki, signal.getsignal(signal.SIGTERM), "isleyici geri alinmadi")
        log = cikti.getvalue()
        self.assertIn("sayac udp_alinan=", log, "son sayac satiri basilmadi")
        self.assertNotIn("SIGTERM isleyicisi kurulamadi", log)


# ── D-405: TEST VAKUMU — kacan mutantlar icin kilitler ───────────────────────

@unittest.skipIf(serial is None, "pyserial kurulu degil")
class TestSeriHubVakum(unittest.TestCase):

    def test_18_iki_ogrenilen_tuketici_IKISI_de_alir_yalniz_son_gonderen_degil(self):
        """Mutant b (yalniz EN SON gonderene fan-out) 11/11 kacmisti; uretim
        topolojisinde tam iki ogrenilen var (rpi_inference + iha_inis_yayinci).
        a ve b gonderir (b en son); YKS cercevesi IKISINE de gider."""
        a = _tuketici()
        b = _tuketici()
        self.addCleanup(a.close)
        self.addCleanup(b.close)
        k = _HubKurulum(self)
        a.send(encode(heartbeat("iha", seq=1)), k.hub_adr)
        k.tur(2)
        b.send(encode(heartbeat("iha", seq=2)), k.hub_adr)   # b EN SON gonderen
        k.tur(2)
        self.assertEqual({(YEREL, a.port), (YEREL, b.port)}, set(k.hub.ogrenilen))
        mesaj = command("IKA_GO", "ika", seq=5)
        k.yks_yaz(mesaj)
        a_gelen = k.topla(a, 1)
        b_gelen = k.topla(b, 1)
        self.assertEqual(1, len(a_gelen), "ILK ogrenilen (a) cerceve almadi")
        self.assertEqual(1, len(b_gelen), "son ogrenilen (b) cerceve almadi")
        _tek_cerceve_dogrula(self, a_gelen[0], mesaj)
        _tek_cerceve_dogrula(self, b_gelen[0], mesaj)
        self.assertEqual(2, k.hub.sayac["fanout_gonderim"])

    def test_19_yeniden_acmada_yarim_cerceve_atilir_yeni_hattin_ilk_cercevesi_bozuk_degil(self):
        """Mutant h (okuyucu sifirlanmaz) kacmisti: ariza aninda okuyucuda
        YARIM cerceve var; yeniden acilan hattaki ilk TAM cerceve bozulmadan
        fan-out edilir, bozuk=0, tampon bos."""
        saat = _SahteSaat(1000.0)
        statik = _tuketici()
        self.addCleanup(statik.close)
        kopru2 = SikKoprusu()
        self.addCleanup(kopru2.kapat)
        yeni_link = _uc(kopru2)
        yks2 = _uc(kopru2)
        self.addCleanup(yks2.close)
        k = _HubKurulum(self, tuketiciler=[(YEREL, statik.port)],
                        seri_ac=mock.Mock(return_value=yeni_link), saat=saat)
        yarim = encode(heartbeat("yks", seq=1))[:-10]          # newline yok
        k.yks.send(yarim)
        bitis = time.monotonic() + TAVAN_S
        while time.monotonic() < bitis and len(k.hub.okuyucu._buf) < len(yarim):
            k.tur()
        self.assertEqual(yarim, k.hub.okuyucu._buf, "on kosul: yarim cerceve tamponda")
        k.hub_seri.recv = mock.Mock(side_effect=OSError("USB koptu"))
        k.tur()
        self.assertIsNone(k.hub.seri_link)
        saat.t += modul.SERI_YENIDEN_ACMA_ARALIGI_S
        k.tur()
        self.assertIs(yeni_link, k.hub.seri_link)
        self.assertEqual(b"", k.hub.okuyucu._buf, "eski yarim cerceve yeni akisa tasindi")
        mesaj = command("IKA_GO", "ika", seq=8)
        yks2.send(encode(mesaj))
        gelen = k.topla(statik, 1)
        self.assertEqual(1, len(gelen), "yeniden acma sonrasi ilk cerceve gelmedi")
        _tek_cerceve_dogrula(self, gelen[0], mesaj)
        self.assertEqual(0, k.hub.sayac["bozuk"], "eski yarim cerceve yeni akisa bulasti")

    def test_20_ogrenilen_tavani_en_az_tazelenen_duser_uzun_omurlu_kalir_KIRMIZI(self):
        """Mutantlar i1 (en YENI duser), i2 (tavan yok), j (tazelik
        guncellenmez) kacmisti. Uzun omurlu tuketici L (arada tazelenir) tavan
        asilinca DUSMEZ ve hic tahliye edilmez (tek 'ogrenildi'); en eski kisa
        omurlu duser; kume tavanda kalir; tahliye KIRMIZI ve 'en az tazelenen'
        + STATIK --tuketici kuralini soyler (CONTRACTS §7.5); L fan-out alir."""
        L = _tuketici()
        self.addCleanup(L.close)
        k = _HubKurulum(self)
        L.send(encode(heartbeat("iha", seq=0)), k.hub_adr)
        k.tur(2)
        kisa = []
        for i in range(modul.OGRENILEN_TAVANI + 4):
            u = _tuketici()
            self.addCleanup(u.close)
            kisa.append(u)
            u.send(encode(heartbeat("iha", seq=i + 1)), k.hub_adr)
            k.tur(2)
            if i % 8 == 7:                       # L arada heartbeat atar (canli)
                L.send(encode(heartbeat("iha", seq=100 + i)), k.hub_adr)
                k.tur(2)
        L.send(encode(heartbeat("iha", seq=999)), k.hub_adr)
        k.tur(2)
        self.assertEqual(modul.OGRENILEN_TAVANI, len(k.hub.ogrenilen), "tavan uygulanmadi")
        self.assertIn((YEREL, L.port), k.hub.ogrenilen, "uzun omurlu tuketici dustu")
        self.assertNotIn((YEREL, kisa[0].port), k.hub.ogrenilen, "EN ESKI dusmedi")
        self.assertIn((YEREL, kisa[-1].port), k.hub.ogrenilen, "en yeni dustu")
        log = k.log.getvalue()
        self.assertIn(f"KIRMIZI ogrenilen tavani ({modul.OGRENILEN_TAVANI}) asildi", log)
        self.assertIn("en az tazelenen dusuruldu", log)
        self.assertIn("STATIK --tuketici", log)
        self.assertIn(f"dusuruldu: {YEREL}:{kisa[0].port}", log, "en eski tahliyesi loglanmadi")
        # L HICBIR ZAMAN tahliye edilmemis olmali (tahliye + yeniden ogrenme de
        # arada fan-out kaybidir): tahliye logunda L yok, L bir kez ogrenilmis.
        self.assertNotIn(f"dusuruldu: {YEREL}:{L.port}", log,
                         "uzun omurlu tuketici ARADA tahliye edildi")
        self.assertEqual(1, log.count(f"ogrenildi: {YEREL}:{L.port}"),
                         "L birden fazla kez ogrenildi (arada dusmus)")
        mesaj = command("IKA_GO", "ika", seq=5)
        k.yks_yaz(mesaj)
        self.assertEqual(1, len(k.topla(L, 1)), "L fan-out almadi")

    def test_21_seri_kapaliyken_bos_tur_bekler_sicak_dongu_yok(self):
        """Mutant k kacmisti: seri_link None iken her poll BOS_TUR_BEKLEME_S
        bekler (Linux'ta aksi ~1000 tur/s sicak dongu; Windows tanecigi
        gizler, o yuzden cagri sayisiyla kilitli)."""
        k = _HubKurulum(self)
        k.hub_seri.recv = mock.Mock(side_effect=OSError("koptu"))
        k.tur()
        self.assertIsNone(k.hub.seri_link)
        k.hub._dur = mock.Mock(wraps=k.hub._dur)
        k.tur(10)
        self.assertEqual(10, k.hub._dur.wait.call_count)
        k.hub._dur.wait.assert_called_with(modul.BOS_TUR_BEKLEME_S)

    def test_22_tek_turda_datagram_patlamasi_hepsi_seriye_sirali(self):
        """Mutant p (UDP tur tavani 1) kacmisti: 10 datagram tek poll'da
        bosaltilir, HEPSI seriye SIRAYLA yazilir."""
        tuketici = _tuketici()
        self.addCleanup(tuketici.close)
        k = _HubKurulum(self)
        for i in range(10):
            tuketici.send(encode(heartbeat("iha", seq=i)), k.hub_adr)
        time.sleep(0.05)
        k.tur(1)
        self.assertEqual(10, k.hub.sayac["seri_yazilan"], "tek turda hepsi yazilmadi")
        with _Yakala(k.log):
            m, hepsi = _seri_cerceve_bekle(k.yks, FrameReader(),
                                           lambda x: x.get("seq") == 9, pompa=None)
        self.assertEqual(list(range(10)), [x.get("seq") for x in hepsi])

    def test_23_seri_ac_None_donerse_baglanmaz_hata_sayilir_yalan_log_yok(self):
        """Mutant u kacmisti: seri_ac None dondurunce None BAGLANMAZ,
        yeniden_acma_hatasi sayilir, 'YENIDEN ACILDI' yalani yok, aralik
        dolmadan tekrar denenmez."""
        saat = _SahteSaat(1000.0)
        k = _HubKurulum(self, seri_ac=mock.Mock(return_value=None), saat=saat)
        k.hub_seri.recv = mock.Mock(side_effect=OSError("koptu"))
        k.tur()
        saat.t += modul.SERI_YENIDEN_ACMA_ARALIGI_S
        k.tur()
        self.assertIsNone(k.hub.seri_link)
        self.assertEqual(1, k.hub.sayac["yeniden_acma_hatasi"])
        self.assertEqual(0, k.hub.sayac["yeniden_acma"])
        self.assertNotIn("YENIDEN ACILDI", k.log.getvalue())
        self.assertIn("seri_ac None dondu", k.log.getvalue())
        k.tur()                                   # aralik dolmadan tekrar YOK
        self.assertEqual(1, k.hub.seri_ac.call_count)

    def test_24_hedefsiz_fanout_sayilir_ve_kirmizi_loglanir(self):
        """Mutant m kacmisti: tuketici yokken seriden gelen cerceve
        `hedefsiz` sayilir ve KIRMIZI loglanir (sessiz dusurme yok)."""
        k = _HubKurulum(self)
        k.yks_yaz(command("IKA_GO", "ika", seq=5))
        bitis = time.monotonic() + TAVAN_S
        while time.monotonic() < bitis and k.hub.sayac["seri_cerceve"] < 1:
            k.tur()
        self.assertEqual(1, k.hub.sayac["hedefsiz"])
        self.assertEqual(0, k.hub.sayac["fanout_gonderim"])
        log = k.log.getvalue()
        self.assertIn("KIRMIZI", log)
        self.assertIn("HICBIR tuketici", log)

    def test_25_fanout_oserror_hub_yasar_fanout_hata_sayilir_kirmizi(self):
        """Mutant n kacmisti: udp send OSError (ENOBUFS) poll'dan YUKSELMEZ;
        `fanout_hata` sayilir, KIRMIZI 'yazilamadi' logu."""
        statik = _tuketici()
        self.addCleanup(statik.close)
        k = _HubKurulum(self, tuketiciler=[(YEREL, statik.port)])
        k.udp.send = mock.Mock(side_effect=OSError("ENOBUFS"))
        k.yks_yaz(command("IKA_GO", "ika", seq=5))
        bitis = time.monotonic() + TAVAN_S
        while time.monotonic() < bitis and k.hub.sayac["seri_cerceve"] < 1:
            k.tur()                              # OSError yukselirse burada patlar
        self.assertEqual(1, k.hub.sayac["fanout_hata"])
        self.assertEqual(0, k.hub.sayac["fanout_gonderim"])
        log = k.log.getvalue()
        self.assertIn("KIRMIZI", log)
        self.assertIn("yazilamadi", log)


if __name__ == "__main__":
    unittest.main()
