"""K3 — MAVLink TUNNEL tasiyicisi birim kapilari (results/tunel_20260916/ON_KAYIT.md §4).

NEDEN: `comms/mavlink_tunel.py` NAVITAS cercevelerini Pixhawk yonlendirmesi
uzerinden tasir; parcalama, birlestirme, suzgecler, akran ogrenme, son tarih
ve ariza semantigi burada GERCEK pymavlink paketleri ve GERCEK UDP soketleriyle
(efemer port) kilitlenir. Saat gereken yerde enjekte edilir.

Vaka adlari nihai sartnamenin test planiyla birebirdir (K3_01 .. K3_24); her
mutant (K5, M1..M20) en az bir vakayi dusurmelidir.
"""
from __future__ import annotations

import inspect
import socket
import struct
import sys
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

KOK = Path(__file__).resolve().parents[1]
for _y in (KOK / "comms", KOK / "codes"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

try:
    from pymavlink.dialects.v20 import ardupilotmega as M
except ImportError:  # pragma: no cover - kurulum kapisi
    M = None

import mavlink_tunel as mt  # noqa: E402
import seri_hub  # noqa: E402
from iha_komut_alici import VARSAYILAN_HEDEF_SYSID  # noqa: E402
from link import SerialLink  # noqa: E402

YEREL = "127.0.0.1"
SINIRLAR = [0, 1, 122, 123, 124, 245, 246, 247, 248, 256, 473, 4096, 7872]
#: Windows zamanlayici tanecigi ~15,6 ms (D-405 olc_granul): son tarih payi.
TANECIK_PAYI_S = 0.035
BEKLEME_TAVANI_S = 3.0


class _Saat:
    def __init__(self, t=1000.0):
        self.t = float(t)

    def __call__(self):
        return self.t


class _Log:
    def __init__(self):
        self.satirlar = []

    def __call__(self, metin, kirmizi=False):
        self.satirlar.append((str(metin), bool(kirmizi)))

    def kirmizi(self):
        return [m for m, k in self.satirlar if k]


def _veri(n):
    """Sifir bayti olmayan (MAVLink2 sondaki sifirlari kirpar) belirlenimci veri."""
    return bytes((i % 251) + 1 for i in range(n))


def _kodlayici(sysid=mt.TUNEL_SYSID, compid=mt.TUNEL_YER_COMPID):
    return M.MAVLink(None, srcSystem=sysid, srcComponent=compid)


def _tunnel_paketi(yuk, sysid=mt.TUNEL_SYSID, compid=mt.TUNEL_YER_COMPID,
                   payload_type=mt.TUNEL_PAYLOAD_TYPE, kod=None):
    kod = kod or _kodlayici(sysid, compid)
    return kod.tunnel_encode(0, 0, payload_type, len(yuk),
                             bytes(yuk) + bytes(mt.TUNEL_MAVLINK_YUK_B - len(yuk))).pack(kod)


def _parca_paketleri(kimlik, veri, **kw):
    kod = _kodlayici(kw.pop("sysid", mt.TUNEL_SYSID), kw.pop("compid", mt.TUNEL_YER_COMPID))
    return [_tunnel_paketi(p, kod=kod, **kw) for p in mt.parcalara_bol(kimlik, veri)]


def _heartbeat(sysid=VARSAYILAN_HEDEF_SYSID, compid=1, tip=None):
    kod = _kodlayici(sysid, compid)
    tip = M.MAV_TYPE_QUADROTOR if tip is None else tip
    return kod.heartbeat_encode(tip, M.MAV_AUTOPILOT_ARDUPILOTMEGA, 0, 0, 0).pack(kod)


def _udp():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((YEREL, 0))
    s.settimeout(1.0)
    return s


class _SahteSoket:
    """`socket.sendto` salt okunurdur; yalniz sendto'yu hataya ceviren vekil."""

    def __init__(self, gercek, hata):
        self._gercek = gercek
        self._hata = hata

    def sendto(self, *_a, **_k):
        raise self._hata

    def __getattr__(self, ad):
        return getattr(self._gercek, ad)


def _cozumle(datagram):
    a = M.MAVLink(None)
    a.robust_parsing = True
    return [m for m in (a.parse_buffer(datagram) or []) if m.get_type() != "BAD_DATA"]


@unittest.skipIf(M is None, "pymavlink kurulu degil")
class _Temel(unittest.TestCase):
    def link(self, kimlik=mt.KIMLIK_YER, **kw):
        kw.setdefault("timeout", 0.2)
        kw.setdefault("log", _Log())
        ln = mt.TunelLink((YEREL, 0), kimlik, **kw)
        self.addCleanup(ln.close)
        return ln

    def soket(self):
        s = _udp()
        self.addCleanup(s.close)
        return s

    def cift(self, **kw):
        """hava -> yer dogrudan (akranlar peer ile verilir)."""
        hava = self.link(mt.KIMLIK_HAVA, ilk_kimlik=kw.pop("hava_kimlik", 100), **kw)
        yer = self.link(mt.KIMLIK_YER, ilk_kimlik=kw.pop("yer_kimlik", 200), **kw)
        hava.akran = (YEREL, yer.port)
        yer.akran = (YEREL, hava.port)
        hava._son_akran_t = hava.saat()
        yer._son_akran_t = yer.saat()
        return hava, yer

    def bekle_cerceve(self, ln, tavan_s=BEKLEME_TAVANI_S):
        bitis = time.monotonic() + tavan_s
        while time.monotonic() < bitis:
            veri, adr = ln.recv()
            self.assertIsNone(adr)
            if veri is not None:
                return veri
        return None


class K3Parcalama(_Temel):
    def test_K3_01_parca_sinirlari_saf_ve_soket_birebir(self):
        for n in SINIRLAR:
            with self.subTest(yol="saf", n=n):
                veri = _veri(n)
                b = mt.Birlestirici(saat=_Saat())
                parcalar = mt.parcalara_bol(7, veri)
                cikan = [b.ekle(p) for p in parcalar]
                if n == 0:
                    self.assertEqual([], parcalar)
                    continue
                self.assertEqual([None] * (len(parcalar) - 1), cikan[:-1])
                self.assertEqual(veri, cikan[-1])
        hava, yer = self.cift(timeout=0.5)
        for n in SINIRLAR:
            with self.subTest(yol="soket", n=n):
                veri = _veri(n)
                hava.send(veri)
                if n == 0:
                    self.assertEqual((None, None), yer.recv())
                    continue
                self.assertEqual(veri, self.bekle_cerceve(yer))
        self.assertEqual(len(SINIRLAR) - 1, yer.sayac["teslim_cerceve"])

    def test_K3_02_parca_sayisi_baslik_tel_boyu_hedef_magic(self):
        hava = self.link(mt.KIMLIK_HAVA, ilk_kimlik=4242)
        s = self.soket()
        hava.akran = s.getsockname()
        for n in (1, 123, 124, 473, 7872):
            with self.subTest(n=n):
                hava.send(_veri(n))
                beklenen = -(-n // mt.TUNEL_PARCA_YUK_B)
                datagramlar = [s.recvfrom(65535)[0] for _ in range(beklenen)]
                s.settimeout(0.05)
                with self.assertRaises(socket.timeout):
                    s.recvfrom(65535)
                s.settimeout(1.0)
                for i, dg in enumerate(datagramlar):
                    self.assertEqual(0xFD, dg[0], "MAVLink2 magic")
                    (msg,) = _cozumle(dg)
                    self.assertEqual(mt.TUNEL_MAVLINK_MSG_ID, msg.get_msgId())
                    self.assertEqual(M.MAVLINK_MSG_ID_TUNNEL, msg.get_msgId())
                    self.assertEqual((0, 0), (msg.target_system, msg.target_component))
                    self.assertEqual((mt.TUNEL_SYSID, mt.TUNEL_HAVA_COMPID),
                                     (msg.get_srcSystem(), msg.get_srcComponent()))
                    self.assertEqual(mt.TUNEL_PAYLOAD_TYPE, msg.payload_type)
                    self.assertEqual(17 + msg.payload_length, len(dg), "tel = 17 + payload_length")
                    surum, kimlik, indis, toplam = struct.unpack_from(
                        mt.TUNEL_BASLIK_BICIMI, bytes(msg.payload))
                    self.assertEqual((mt.TUNEL_SURUM, i, beklenen), (surum, indis, toplam))
                    son = i == beklenen - 1
                    if not son:
                        self.assertEqual(mt.TUNEL_MAVLINK_YUK_B, msg.payload_length)
        # kimlik cerceve basina +1 (5 cerceve gonderildi)
        self.assertEqual((4242 + 5) % 65536, hava._sonraki_kimlik)

    def test_K3_03_tavan_ustu_ve_akran_yok_gorunur_ret_kimlik_TUKETILMEZ(self):
        log = _Log()
        hava = self.link(mt.KIMLIK_HAVA, ilk_kimlik=500, log=log)
        s = self.soket()
        # akran yok
        hava.send(_veri(10))
        hava.send(_veri(10))
        self.assertEqual(2, hava.sayac["akran_yok"])
        self.assertEqual(1, sum("akran YOK" in m for m in log.kirmizi()), "ilk seferde tek KIRMIZI")
        hava.akran = s.getsockname()
        hava._son_akran_t = hava.saat()
        # tavan ustu
        hava.send(_veri(mt.TUNEL_AZAMI_CERCEVE_B + 1))
        hava.send(_veri(mt.TUNEL_AZAMI_CERCEVE_B + 1))
        self.assertEqual(2, hava.sayac["tavan_ustu"])
        self.assertEqual(2, sum("tavan" in m for m in log.kirmizi()), "her olayda KIRMIZI")
        s.settimeout(0.1)
        with self.assertRaises(socket.timeout):
            s.recvfrom(65535)
        s.settimeout(1.0)
        hava.send(_veri(5))
        (msg,) = _cozumle(s.recvfrom(65535)[0])
        _, kimlik, _, _ = struct.unpack_from(mt.TUNEL_BASLIK_BICIMI, bytes(msg.payload))
        self.assertEqual(500, kimlik, "tavan ustu / akran yok kimlik TUKETMEMELI")
        self.assertEqual(1, hava.sayac["gonderilen_cerceve"])


class K3Suzgecler(_Temel):
    def _gonder(self, ln, *datagramlar, kaynak=None):
        s = kaynak or self.soket()
        for dg in datagramlar:
            s.sendto(dg, (YEREL, ln.port))
        return s

    def test_K3_04_yabanci_payload_type_yok_sayilir(self):
        yer = self.link()
        self._gonder(yer, _tunnel_paketi(mt.parcalara_bol(1, b"x\n")[0], payload_type=0x1234,
                                         compid=mt.TUNEL_HAVA_COMPID),
                     *_parca_paketleri(2, b"gecerli\n", compid=mt.TUNEL_HAVA_COMPID))
        self.assertEqual(b"gecerli\n", self.bekle_cerceve(yer))
        self.assertEqual(1, yer.sayac["yabanci_payload_type"])
        self.assertEqual(1, yer.sayac["teslim_cerceve"])

    def test_K3_05_yabanci_mesaj_tipi_yok_sayilir(self):
        yer = self.link()
        kod = _kodlayici(mt.TUNEL_SYSID, mt.TUNEL_HAVA_COMPID)
        att = kod.attitude_encode(1, 0.1, 0.2, 0.3, 0, 0, 0).pack(kod)
        self._gonder(yer, att, *_parca_paketleri(3, b"ok\n", compid=mt.TUNEL_HAVA_COMPID))
        self.assertEqual(b"ok\n", self.bekle_cerceve(yer))
        self.assertEqual(1, yer.sayac["yabanci_mesaj"])

    def test_K3_06_kendi_yankisi_yok_sayilir(self):
        yer = self.link()
        self._gonder(yer, *_parca_paketleri(4, b"yanki\n", compid=mt.TUNEL_YER_COMPID),
                     *_parca_paketleri(5, b"karsi\n", compid=mt.TUNEL_HAVA_COMPID))
        self.assertEqual(b"karsi\n", self.bekle_cerceve(yer))
        self.assertEqual((None, None), yer.recv())
        self.assertEqual(1, yer.sayac["kendi_yanki"])

    def test_K3_06b_yabanci_kaynak_yok_sayilir(self):
        yer = self.link()
        self._gonder(yer,
                     *_parca_paketleri(6, b"a\n", sysid=mt.TUNEL_SYSID, compid=27),
                     *_parca_paketleri(7, b"b\n", sysid=VARSAYILAN_HEDEF_SYSID,
                                       compid=mt.TUNEL_HAVA_COMPID),
                     *_parca_paketleri(8, b"c\n", compid=mt.TUNEL_HAVA_COMPID))
        self.assertEqual(b"c\n", self.bekle_cerceve(yer))
        self.assertEqual((None, None), yer.recv())
        self.assertEqual(2, yer.sayac["yabanci_kaynak"])

    def test_K3_07_hareketsizlik_zaman_asimi_eksik_cerceve_duser_sayilir(self):
        saat = _Saat()
        yer = self.link(saat=saat)
        paketler = _parca_paketleri(9, _veri(300), compid=mt.TUNEL_HAVA_COMPID)
        self._gonder(yer, paketler[0], paketler[1])
        self.assertEqual((None, None), yer.recv())
        self.assertEqual(0, yer.sayac["zaman_asimi_dusen"])
        saat.t += mt.TUNEL_BIRLESTIRME_ZAMAN_ASIMI_S + 0.01
        self.assertEqual((None, None), yer.recv())
        self.assertEqual(1, yer.sayac["zaman_asimi_dusen"])
        self._gonder(yer, paketler[2])           # gec gelen son parca tek basina teslim YOK
        self.assertEqual((None, None), yer.recv())
        self.assertEqual(0, yer.sayac["teslim_cerceve"])

    def test_K3_07b_hareket_suruyorsa_toplam_sure_asilsa_da_teslim(self):
        saat = _Saat()
        b = mt.Birlestirici(saat=saat)
        parcalar = mt.parcalara_bol(10, _veri(500))
        adim = mt.TUNEL_BIRLESTIRME_ZAMAN_ASIMI_S * 0.8
        for p in parcalar[:-1]:
            self.assertIsNone(b.ekle(p))
            saat.t += adim
        self.assertEqual(_veri(500), b.ekle(parcalar[-1]))
        self.assertEqual(0, b.sayac["zaman_asimi_dusen"])

    def test_K3_08_bozuk_baslik_ve_tutarsiz_parca(self):
        b = mt.Birlestirici(saat=_Saat())
        dogru = mt.parcalara_bol(11, _veri(300))
        bozuklar = [
            b"\x01\x00",                                                # kisa
            struct.pack(mt.TUNEL_BASLIK_BICIMI, 2, 11, 0, 3) + b"x",  # surum
            struct.pack(mt.TUNEL_BASLIK_BICIMI, 1, 11, 0, 0) + b"x",  # toplam 0
            struct.pack(mt.TUNEL_BASLIK_BICIMI, 1, 11, 0, 65) + b"x",  # toplam > 64
            struct.pack(mt.TUNEL_BASLIK_BICIMI, 1, 11, 3, 3) + b"x",  # indis >= toplam
            struct.pack(mt.TUNEL_BASLIK_BICIMI, 1, 11, 0, 3) + b"x" * 122,  # son olmayan kisa
            struct.pack(mt.TUNEL_BASLIK_BICIMI, 1, 11, 2, 3),          # bos yuk
        ]
        for p in bozuklar:
            self.assertIsNone(b.ekle(p))
        self.assertEqual(len(bozuklar), b.sayac["bozuk_parca"])
        self.assertEqual(0, b.sayac["alinan_parca"])
        # tutarsiz: ayni kimlik farkli toplam -> kismi cerceve TAMAMEN atilir
        self.assertIsNone(b.ekle(dogru[0]))
        tutarsiz = struct.pack(mt.TUNEL_BASLIK_BICIMI, 1, 11, 1, 4) + _veri(123)
        self.assertIsNone(b.ekle(tutarsiz))
        self.assertEqual(1, b.sayac["tutarsiz_parca"])
        self.assertIsNone(b.ekle(dogru[1]))
        self.assertIsNone(b.ekle(dogru[2]), "atilan kismi cerceve eski parcalarla TAMAMLANMAMALI")
        # tutarsiz: ayni indis farkli icerik
        b2 = mt.Birlestirici(saat=_Saat())
        self.assertIsNone(b2.ekle(dogru[0]))
        degisik = dogru[0][:mt.TUNEL_BASLIK_B] + _veri(124)[1:]
        self.assertIsNone(b2.ekle(degisik))
        self.assertEqual(1, b2.sayac["tutarsiz_parca"])
        self.assertIsNone(b2.ekle(dogru[1]))
        self.assertIsNone(b2.ekle(dogru[2]))
        self.assertEqual(0, b2.sayac["tamamlanan_cerceve"])

    def test_K3_09_yinelenen_parca_tek_teslim_hafiza_sonrasi_yeni_cerceve(self):
        saat = _Saat()
        b = mt.Birlestirici(saat=saat)
        uc = mt.parcalara_bol(12, _veri(300))
        self.assertIsNone(b.ekle(uc[0]))
        self.assertIsNone(b.ekle(uc[1]))
        self.assertIsNone(b.ekle(uc[1]))                    # orta parca kopyasi
        self.assertEqual(1, b.sayac["yinelenen_parca"])
        self.assertEqual(_veri(300), b.ekle(uc[2]))
        tek = mt.parcalara_bol(13, b"tek\n")
        self.assertEqual(b"tek\n", b.ekle(tek[0]))
        saat.t += mt.TUNEL_TAMAMLANAN_HAFIZA_S * 0.5
        self.assertIsNone(b.ekle(tek[0]), "tek parcali kopya ikinci kez teslim edilmemeli")
        self.assertEqual(2, b.sayac["yinelenen_parca"])
        saat.t += mt.TUNEL_TAMAMLANAN_HAFIZA_S + 0.01
        self.assertEqual(b"tek\n", b.ekle(tek[0]), "hafiza sonrasi ayni kimlik YENI cercevedir")

    def test_K3_10_sira_disi_parca_kabul(self):
        b = mt.Birlestirici(saat=_Saat())
        p = mt.parcalara_bol(14, _veri(473))
        for i in (3, 1, 0):
            self.assertIsNone(b.ekle(p[i]))
        self.assertEqual(_veri(473), b.ekle(p[2]))

    def test_K3_11_araya_giren_iki_cerceve(self):
        yer = self.link()
        a = _parca_paketleri(15, _veri(300), compid=mt.TUNEL_HAVA_COMPID)
        c = _parca_paketleri(16, bytes(reversed(_veri(250))), compid=mt.TUNEL_HAVA_COMPID)
        self._gonder(yer, a[0], c[0], a[1], c[1], a[2], c[2])
        gelen = {self.bekle_cerceve(yer), self.bekle_cerceve(yer)}
        self.assertEqual({_veri(300), bytes(reversed(_veri(250)))}, gelen)


class K3ZamanlamaVeAriza(_Temel):
    def test_K3_12_recv_son_tarihi_cagri_basina_yabanci_sel_altinda(self):
        varsayilan = inspect.signature(mt.TunelLink.__init__).parameters["timeout"].default
        seri_varsayilan = inspect.signature(SerialLink.__init__).parameters["timeout"].default
        self.assertLessEqual(varsayilan, seri_varsayilan)
        yer = self.link(timeout=0.05)
        dur = threading.Event()
        kod = _kodlayici(VARSAYILAN_HEDEF_SYSID, 1)
        att = kod.attitude_encode(1, 0.1, 0.2, 0.3, 0, 0, 0).pack(kod)
        s = self.soket()

        def sel():
            bitis = time.monotonic() + 4.0
            while not dur.is_set() and time.monotonic() < bitis:
                s.sendto(att, (YEREL, yer.port))
                time.sleep(0.001)
        t = threading.Thread(target=sel, daemon=True)
        t.start()
        self.addCleanup(t.join, 5.0)
        self.addCleanup(dur.set)
        time.sleep(0.05)
        sureler = []
        for _ in range(20):
            t0 = time.monotonic()
            self.assertEqual((None, None), yer.recv())
            sureler.append(time.monotonic() - t0)
        dur.set()
        self.assertGreater(yer.sayac["yabanci_mesaj"], 20, "sel gercekten geldi mi")
        self.assertLessEqual(max(sureler), 0.05 + TANECIK_PAYI_S,
                             f"son tarih cagri basina olmali: {sureler}")

    def test_K3_13_close_idempotent_sonra_OSError(self):
        ln = mt.TunelLink((YEREL, 0), mt.KIMLIK_HAVA, log=_Log())
        ln.close()
        ln.close()
        self.assertEqual(-1, ln.sock.fileno())
        with self.assertRaises(OSError):
            ln.send(b"x\n")
        with self.assertRaises(OSError):
            ln.recv()

    def test_K3_14_akran_yok_surec_olmez(self):
        ln = self.link(mt.KIMLIK_HAVA)
        for _ in range(3):
            ln.send(b"x\n")
        self.assertEqual(3, ln.sayac["akran_yok"])
        self.assertEqual(0, ln.sayac["gonderilen_parca"])
        self.assertEqual(1, len(ln.log.kirmizi()))

    def test_K3_15_olu_akran_ve_yerel_soket_hatasi(self):
        ln = self.link(mt.KIMLIK_HAVA, ilk_kimlik=30)
        olu = _udp()
        adr = olu.getsockname()
        olu.close()
        ln.akran = adr
        ln._son_akran_t = ln.saat()
        for _ in range(3):
            ln.send(b"olu akran\n")
            self.assertEqual((None, None), ln.recv())   # Windows: WinError 10054 yutulur
        with mock.patch.object(ln, "sock", _SahteSoket(ln.sock, ConnectionResetError())):
            ln.send(_veri(300))
        self.assertEqual(1, ln.sayac["gonderim_hatasi"])
        self.assertEqual((30 + 4) % 65536, ln._sonraki_kimlik)
        with mock.patch.object(ln, "sock", _SahteSoket(ln.sock, OSError(9, "EBADF"))):
            with self.assertRaises(OSError):
                ln.send(b"x\n")

    def test_K3_17_akran_sessizligi_bolum_basina_tek_KIRMIZI(self):
        saat = _Saat()
        ln = self.link(mt.KIMLIK_HAVA, saat=saat)
        s = self.soket()
        ln.akran = s.getsockname()
        ln._son_akran_t = saat()
        ln.send(b"a\n")
        self.assertEqual(0, ln.sayac["akran_sessizken_gonderilen"])
        saat.t += mt.TUNEL_AKRAN_SESSIZLIK_S + 0.5
        ln.send(b"b\n")
        ln.send(b"c\n")
        self.assertEqual(2, ln.sayac["akran_sessizken_gonderilen"])
        self.assertEqual(1, sum("SESSIZ" in m for m in ln.log.kirmizi()))
        s.sendto(_heartbeat(), (YEREL, ln.port))     # akran konustu: bolum biter
        ln.recv()
        ln.send(b"d\n")
        self.assertEqual(2, ln.sayac["akran_sessizken_gonderilen"])
        saat.t += mt.TUNEL_AKRAN_SESSIZLIK_S + 0.5
        ln.send(b"e\n")
        self.assertEqual(2, sum("SESSIZ" in m for m in ln.log.kirmizi()))

    def test_K3_18_bufsize_cerceveyi_bolmez(self):
        hava, yer = self.cift()
        hava.send(_veri(473))
        bitis = time.monotonic() + BEKLEME_TAVANI_S
        veri = None
        while veri is None and time.monotonic() < bitis:
            veri, _ = yer.recv(10)
        self.assertEqual(_veri(473), veri)

    def test_K3_19_eszamanli_kismi_tavani(self):
        saat = _Saat()
        b = mt.Birlestirici(saat=saat)
        for k in range(mt.TUNEL_ESZAMANLI_KISMI_TAVANI + 1):
            self.assertIsNone(b.ekle(mt.parcalara_bol(k, _veri(200))[0]))
            saat.t += 0.001
        self.assertEqual(1, b.sayac["eszamanli_tavan_dusen"])
        self.assertLessEqual(len(b._kismi), mt.TUNEL_ESZAMANLI_KISMI_TAVANI)
        self.assertNotIn(0, b._kismi, "EN ESKI kismi dusmeli")


class K3AkranOgrenme(_Temel):
    def test_K3_16a_arac_heartbeat_akrani_degistirir_KIRMIZI(self):
        ln = self.link(mt.KIMLIK_HAVA)
        eski = self.soket()
        yeni = self.soket()
        ln.akran = eski.getsockname()
        ln._son_akran_t = ln.saat()
        yeni.sendto(_heartbeat(VARSAYILAN_HEDEF_SYSID, 1, M.MAV_TYPE_QUADROTOR), (YEREL, ln.port))
        ln.recv()
        self.assertEqual(1, ln.sayac["akran_degisti"])
        self.assertEqual(yeni.getsockname(), ln.akran)
        self.assertTrue(any("DEGISTI" in m for m in ln.log.kirmizi()))
        ln.send(b"yeni\n")
        (msg,) = _cozumle(yeni.recvfrom(65535)[0])
        self.assertEqual(mt.TUNEL_MAVLINK_MSG_ID, msg.get_msgId())

    def test_K3_16b_heartbeat_olmayan_ya_da_yanlis_heartbeat_akrani_DEGISTIRMEZ(self):
        ln = self.link(mt.KIMLIK_HAVA)
        asil = self.soket()
        ln.akran = asil.getsockname()
        ln._son_akran_t = ln.saat()
        saldirgan = self.soket()
        kod = _kodlayici(VARSAYILAN_HEDEF_SYSID, 1)
        att = kod.attitude_encode(1, 0, 0, 0, 0, 0, 0).pack(kod)
        datagramlar = (_parca_paketleri(40, b"tunel\n", compid=mt.TUNEL_YER_COMPID)
                       + [att, _heartbeat(255, 190, M.MAV_TYPE_GCS),
                          _heartbeat(VARSAYILAN_HEDEF_SYSID, 1, M.MAV_TYPE_GCS),
                          _heartbeat(2, 1, M.MAV_TYPE_QUADROTOR)])
        for dg in datagramlar:
            saldirgan.sendto(dg, (YEREL, ln.port))
        self.assertEqual(b"tunel\n", self.bekle_cerceve(ln), "TUNNEL parcasi yine islenir")
        for _ in range(5):
            ln.recv()
        self.assertEqual(asil.getsockname(), ln.akran)
        self.assertEqual(0, ln.sayac["akran_degisti"])
        self.assertEqual(len(datagramlar), ln.sayac["akrandisi_datagram"])

    def test_K3_16c_akran_yokken_gcs_heartbeati_akran_kurmaz(self):
        ln = self.link(mt.KIMLIK_YER)
        s = self.soket()
        s.sendto(_heartbeat(255, 190, M.MAV_TYPE_GCS), (YEREL, ln.port))
        s.sendto(_heartbeat(VARSAYILAN_HEDEF_SYSID, 1, M.MAV_TYPE_GCS), (YEREL, ln.port))
        ln.recv()
        ln.recv()
        self.assertIsNone(ln.akran)
        s.sendto(_heartbeat(), (YEREL, ln.port))
        ln.recv()
        self.assertEqual(s.getsockname(), ln.akran)
        self.assertEqual(0, ln.sayac["akran_degisti"], "ilk ogrenme degisim sayilmaz")


class K3Ayristirma(_Temel):
    def _cop_sonrasi_gecerli(self, cop):
        ln = self.link(mt.KIMLIK_HAVA)
        s = self.soket()
        s.sendto(cop, (YEREL, ln.port))
        (ilk,) = _parca_paketleri(50, b"ilk gecerli\n", compid=mt.TUNEL_YER_COMPID)
        s.sendto(ilk, (YEREL, ln.port))
        return ln, self.bekle_cerceve(ln)

    def test_K3_21a_hava_datagram_kipi_coptan_sonra_ILK_gecerli_teslim(self):
        (tam,) = _parca_paketleri(51, _veri(60), compid=mt.TUNEL_YER_COMPID)
        bozuk_crc = bytearray(tam)
        bozuk_crc[-1] ^= 0xFF
        coplar = {
            "00 fd 80 + 5x00": b"\x00\xfd\x80" + bytes(5),
            "yarim MAVLink2": tam[:10],
            "bozuk CRC": bytes(bozuk_crc),
            "65507 B": bytes(65507),
        }
        for ad, cop in coplar.items():
            with self.subTest(cop=ad):
                ln, veri = self._cop_sonrasi_gecerli(cop)
                self.assertEqual(mt.AYRISTIRMA_DATAGRAM, ln.ayristirma)
                self.assertEqual(b"ilk gecerli\n", veri)

    def test_K3_21b_yer_akis_kipi_bolunmus_obek_ikisi_de_teslim(self):
        a = _parca_paketleri(52, b"A" * 122 + b"\n", compid=mt.TUNEL_HAVA_COMPID)[0]
        b = _parca_paketleri(53, b"B" * 122 + b"\n", compid=mt.TUNEL_HAVA_COMPID)[0]
        obek = a + b
        yer = self.link(mt.KIMLIK_YER)
        self.assertEqual(mt.AYRISTIRMA_AKIS, yer.ayristirma)
        s = self.soket()
        s.sendto(obek[:100], (YEREL, yer.port))
        s.sendto(obek[100:], (YEREL, yer.port))
        self.assertEqual(b"A" * 122 + b"\n", self.bekle_cerceve(yer))
        self.assertEqual(b"B" * 122 + b"\n", self.bekle_cerceve(yer))
        # Ayni obek 'datagram' kipinde: bolunen ilk paket KAYBOLUR, cozum hatasi
        # sayilir (olculdu: yalniz ikinci paket cozuldu). Kipler arasi farkin belgesi.
        yer_d = self.link(mt.KIMLIK_YER, ayristirma=mt.AYRISTIRMA_DATAGRAM)
        s.sendto(obek[:100], (YEREL, yer_d.port))
        s.sendto(obek[100:], (YEREL, yer_d.port))
        gelen = [self.bekle_cerceve(yer_d, tavan_s=0.5) for _ in range(2)]
        self.assertNotIn(b"A" * 122 + b"\n", gelen)
        self.assertGreaterEqual(yer_d.sayac["cozum_hatasi"], 1)
        self.assertLess(yer_d.sayac["teslim_cerceve"], 2)

    def test_K3_21c_gecersiz_kip_ve_kimlik_ValueError(self):
        with self.assertRaises(ValueError):
            mt.TunelLink((YEREL, 0), mt.KIMLIK_HAVA, ayristirma="satir")
        with self.assertRaises(ValueError):
            mt.TunelLink((YEREL, 0), "iha")


class K3KimlikBoslugu(_Temel):
    def test_K3_22_bosluk_geri_sarma_sicrama_zaman_asimi_cift_sayilmaz(self):
        saat = _Saat()
        log = _Log()
        b = mt.Birlestirici(saat=saat, log=log)
        for k in (10, 11, 14):
            self.assertIsNotNone(b.ekle(mt.parcalara_bol(k, b"x\n")[0]))
        self.assertEqual(2, b.sayac["kimlik_boslugu"])
        b.ekle(mt.parcalara_bol(13, b"x\n")[0])
        self.assertEqual(1, b.sayac["kimlik_geri"])
        self.assertEqual(2, b.sayac["kimlik_boslugu"])
        s = mt.Birlestirici(saat=_Saat(), log=_Log())
        s.ekle(mt.parcalara_bol(65535, b"x\n")[0])
        s.ekle(mt.parcalara_bol(0, b"x\n")[0])
        self.assertEqual(0, s.sayac["kimlik_boslugu"], "65535 -> 0 sarmasi bosluk degil")
        b.ekle(mt.parcalara_bol(14 + 300, b"x\n")[0])
        self.assertEqual(1, b.sayac["kimlik_sicramasi"])
        self.assertEqual(1, len(log.kirmizi()))
        b.ekle(mt.parcalara_bol(14 + 900, b"x\n")[0])
        self.assertEqual(2, b.sayac["kimlik_sicramasi"])
        self.assertEqual(1, len(log.kirmizi()), "yalniz ilk sicrama KIRMIZI")
        z = mt.Birlestirici(saat=saat, log=_Log())
        z.ekle(mt.parcalara_bol(20, b"y\n")[0])
        z.ekle(mt.parcalara_bol(21, _veri(300))[0])     # yalniz ilk parca
        saat.t += mt.TUNEL_BIRLESTIRME_ZAMAN_ASIMI_S + 0.01
        z.ekle(mt.parcalara_bol(22, b"y\n")[0])
        self.assertEqual(1, z.sayac["zaman_asimi_dusen"])
        self.assertEqual(0, z.sayac["kimlik_boslugu"], "zaman asimi bosluga CIFT sayilmaz")

    def test_K3_23_soket_ortanca_tek_parcali_dusurulur_bosluk_1(self):
        hava = self.link(mt.KIMLIK_HAVA, ilk_kimlik=100)
        yer = self.link(mt.KIMLIK_YER)
        aktarici = self.soket()
        hava.akran = aktarici.getsockname()
        hava._son_akran_t = hava.saat()
        for i in range(3):
            hava.send(f"cerceve {i}\n".encode())
        dgs = [aktarici.recvfrom(65535)[0] for _ in range(3)]
        for i, dg in enumerate(dgs):
            if i != 1:
                aktarici.sendto(dg, (YEREL, yer.port))
        self.assertEqual(b"cerceve 0\n", self.bekle_cerceve(yer))
        self.assertEqual(b"cerceve 2\n", self.bekle_cerceve(yer))
        self.assertEqual(1, yer.sayac["kimlik_boslugu"])


class K3SabitIliskileri(unittest.TestCase):
    def test_K3_24_zaman_asimi_hafiza_yeniden_acma_sirasi(self):
        self.assertLess(mt.TUNEL_BIRLESTIRME_ZAMAN_ASIMI_S, mt.TUNEL_TAMAMLANAN_HAFIZA_S)
        self.assertLess(mt.TUNEL_TAMAMLANAN_HAFIZA_S, seri_hub.SERI_YENIDEN_ACMA_ARALIGI_S)
        self.assertEqual(mt.TUNEL_PARCA_YUK_B * mt.TUNEL_AZAMI_PARCA, mt.TUNEL_AZAMI_CERCEVE_B)
        self.assertGreaterEqual(mt.TUNEL_AZAMI_CERCEVE_B, 4096, "protocol.py '< 4 KiB' beyani")
        self.assertEqual(struct.calcsize(mt.TUNEL_BASLIK_BICIMI), mt.TUNEL_BASLIK_B)
        self.assertEqual(mt.TUNEL_MAVLINK_YUK_B, mt.TUNEL_PARCA_YUK_B + mt.TUNEL_BASLIK_B)

    def test_modul_pymavlinki_import_aninda_yuklemez(self):
        import subprocess
        kod = ("import sys; sys.path.insert(0, %r); import mavlink_tunel; "
               "assert not any(m.startswith('pymavlink') for m in sys.modules), "
               "[m for m in sys.modules if m.startswith('pymavlink')]; print('OK')"
               % str(KOK / "comms"))
        r = subprocess.run([sys.executable, "-B", "-c", kod], capture_output=True,
                           text=True, timeout=60)
        self.assertEqual(0, r.returncode, r.stderr)


if __name__ == "__main__":
    unittest.main()
