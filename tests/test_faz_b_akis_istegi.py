"""T207 (D-406 A, KRITIK) — URETIM SURECI MAVLink AKISINI KENDISI ISTER.

OLGU: ArduCopter EXTENDED_SYS_STATE'i hicbir `SR*` akisinda vermez; yalniz
MAV_CMD_SET_MESSAGE_INTERVAL ile akar, istek baglantiya ozeldir ve Pixhawk
reboot'unda (pil degisimi) silinir. Bugune dek isteyen YALNIZ on-ucus araci
(scripts/mavlink_dogrula.py) idi; uretim sureci comms/iha_inis_yayinci.py
istemiyordu -> reboot sonrasi inis kaniti SESSIZCE olurdu.

Kapilar (her biri neyi kilitledigini adiyla soyler):
  A1 baslangicta uc akis icin SET_MESSAGE_INTERVAL (id'ler pymavlink'ten,
     aralik_us = 1e6 / (asgari_hz x carpan), hedef/onay alanlari dogru)
  A2 main() istegi ILK okumadan once gonderir
  A3 GERCEK UDP: sahte Pixhawk `udpin` (sunucu) kipinde istek gelmeden akis
     BASLATAMAZ; yayinci `udpout` ile ister -> sahtenin alinan_komutlar'inda
     uc istek, akis akar, kanit olusur, IHA_LANDED gercek IkaReceiver'a gider
  A4 A3'un on kosulu: sunucu kipindeki sahte, hic paket gormedigi akrana
     hicbir sey gondermez (istek olmadan kanit YOK)
  B1 EXTENDED gelmezken saat ilerleyince: KIRMIZI log (bir kez) + aninda
     yeniden istek; tekrar turlarda spam yok; periyodik yenileme surer;
     akis donunce toparlanma logu; ikinci sessizlikte ikinci KIRMIZI
  B2 ayni davranis main() yolunda (enjekte saat, gercek yerde_mi + gozcu)
  C1 EXTENDED akarken periyodik yenileme (0/10/20 s) var, KIRMIZI yok
  C2 yabanci sysid'in EXTENDED'i sessizligi bozmaz (--sysid beyanliyken)
  D1 command_long_send OSError: sayac artar, KIRMIZI log, sonraki tur surer
  D2 main() yolunda OSError'a ragmen kanit olusur, exit 0, ozet hatayi soyler
  E1 pymavlink udp sunucusu akran gormeden yazamaz: istek ERTELENIR, akran
     gorulunce bakim() 10 s beklemeden gonderir
  F1 sozlesme: carpan mavlink_dogrula.ISTEK_HIZ_CARPANI ile ayni; aralik
     formulu ayni; tavan/aralik iliskileri
  G1 gozcu: dilimli bekleme toplam sureyi korur, mesajda hemen doner
  (e) MUTASYON: periyodik yenileme kaldirilinca B1/B2/C1 duser — scratchpad
      kopyasinda kosuldu, ham cikti commit mesajinda/raporda.
"""
import contextlib
import io
import socket
import sys
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

KOK = Path(__file__).resolve().parents[1]
for _y in (KOK / "comms", KOK / "codes", KOK / "scripts"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

try:
    from pymavlink import mavutil
except ImportError:  # pragma: no cover - kurulum kapisi
    mavutil = None

import iha_inis_yayinci as yayinci  # noqa: E402
import inis_kaniti as kanit  # noqa: E402
from karar_sozlesmesi import (MAVLINK_AKIS_ISTEK_ARALIGI_S,  # noqa: E402
                              MAVLINK_AKIS_ISTEK_HIZ_CARPANI,
                              MAVLINK_AKIS_SESSIZLIK_TAVANI_S,
                              MAVLINK_DURUM_ASGARI_HZ,
                              MAVLINK_KONUM_ASGARI_HZ)

SYSID = 1
YABANCI = 99
KIRMIZI_METIN = "EXTENDED_SYS_STATE gelmiyor — akis yeniden isteniyor"


class SahteSaat:
    def __init__(self, t=0.0):
        self.t = float(t)

    def __call__(self):
        return self.t

    def ilerle(self, dt):
        self.t += float(dt)


class MavMesaj:
    def __init__(self, tip, kaynak=SYSID, **alanlar):
        self._tip = tip
        self._kaynak = kaynak
        for ad, deger in alanlar.items():
            setattr(self, ad, deger)

    def get_type(self):
        return self._tip

    def get_srcSystem(self):
        return self._kaynak


def _extended(kaynak=SYSID, yerde=True):
    return MavMesaj(kanit.MESAJ_EXTENDED_SYS_STATE, kaynak,
                    landed_state=1 if yerde else 2)


def _konum(kaynak=SYSID, bagil_mm=250):
    return MavMesaj(kanit.MESAJ_GLOBAL_POSITION_INT, kaynak,
                    relative_alt=bagil_mm)


class KayitMav:
    """pymavlink baglantisi taklidi: komutlari kaydeder, kuyruktan mesaj verir.

    `hata` verilirse command_long_send o istisnayi firlatir. `okuma_kancasi`
    her recv_match'te cagrilir (sahte saati ilerletmek icin).
    """

    def __init__(self, mesajlar=(), *, hata=None, okuma_kancasi=None,
                 target_system=SYSID, target_component=1):
        self.mesajlar = list(mesajlar)
        self.komutlar = []          # command_long_send argumanlari
        self.olaylar = []           # "komut" / "okuma" sirasi
        self.kapandi = False
        self.target_system = target_system
        self.target_component = target_component
        self._hata = hata
        self._kanca = okuma_kancasi
        self.mav = SimpleNamespace(command_long_send=self._command_long_send)

    def _command_long_send(self, *args):
        self.olaylar.append("komut")
        if self._hata is not None:
            raise self._hata
        self.komutlar.append(args)

    def recv_match(self, **kwargs):
        if not kwargs.get("blocking") or kwargs.get("timeout", 0) <= 0:
            raise ValueError("sinirli bloklayici okuma gerekli")
        self.olaylar.append("okuma")
        if self._kanca is not None:
            self._kanca()
        return self.mesajlar.pop(0) if self.mesajlar else None

    def close(self):
        self.kapandi = True


def _kanit_mesajlari(adet=3):
    m = []
    for _ in range(adet):
        m.extend([_extended(), _konum()])
    return m


def _sahte_mavutil():
    return SimpleNamespace(mavlink=SimpleNamespace(MAV_LANDED_STATE_ON_GROUND=1))


def _bos_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]
    finally:
        s.close()


@unittest.skipIf(mavutil is None, "pymavlink kurulu degil")
class A_BaslangicIstegi(unittest.TestCase):

    def _komut_sozlugu(self, args):
        return {"sys": args[0], "comp": args[1], "cmd": args[2],
                "onay": args[3], "p1": args[4], "p2": args[5],
                "kalan": args[6:]}

    def test_A1_baslangicta_uc_akis_icin_SET_MESSAGE_INTERVAL(self):
        mav = KayitMav()
        saat = SahteSaat()
        istekci = yayinci.AkisIstekcisi(mav, beklenen_sysid=SYSID, saat=saat)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertTrue(istekci.iste())
        self.assertEqual(3, len(mav.komutlar))
        m = mavutil.mavlink
        gelen = {int(k[4]): self._komut_sozlugu(k) for k in mav.komutlar}
        self.assertEqual({m.MAVLINK_MSG_ID_EXTENDED_SYS_STATE,
                          m.MAVLINK_MSG_ID_GLOBAL_POSITION_INT,
                          m.MAVLINK_MSG_ID_GPS_RAW_INT}, set(gelen))
        ext = gelen[m.MAVLINK_MSG_ID_EXTENDED_SYS_STATE]
        kon = gelen[m.MAVLINK_MSG_ID_GLOBAL_POSITION_INT]
        gps = gelen[m.MAVLINK_MSG_ID_GPS_RAW_INT]
        for k in (ext, kon, gps):
            self.assertEqual(m.MAV_CMD_SET_MESSAGE_INTERVAL, k["cmd"])
            self.assertEqual(SYSID, k["sys"])
            self.assertEqual(1, k["comp"])
            self.assertEqual(0, k["onay"], "ilk gonderim: confirmation 0")
            self.assertEqual((0.0,) * 5, tuple(k["kalan"]))
            self.assertIsInstance(k["p1"], float)
            self.assertIsInstance(k["p2"], float)
        self.assertEqual(
            1e6 / (MAVLINK_DURUM_ASGARI_HZ * MAVLINK_AKIS_ISTEK_HIZ_CARPANI),
            ext["p2"])
        self.assertEqual(
            1e6 / (MAVLINK_KONUM_ASGARI_HZ * MAVLINK_AKIS_ISTEK_HIZ_CARPANI),
            kon["p2"])
        self.assertEqual(kon["p2"], gps["p2"],
                         "GPS_RAW_INT konumla ayni sozlesme hizini kullanir")
        self.assertEqual(500000.0, ext["p2"], "1 Hz x 2 -> 500 ms")
        self.assertEqual(125000.0, kon["p2"], "4 Hz x 2 -> 125 ms")
        s = istekci.sayac
        self.assertEqual((1, 3, 0, 0, 0),
                         (s["tur"], s["gonderilen"], s["gonderim_hatasi"],
                          s["ertelenen"], s["sessizlik_uyarisi"]))

    def test_A1b_sysid_beyani_yoksa_baglantinin_hedefi_yoksa_0(self):
        mav = KayitMav(target_system=7, target_component=1)
        with contextlib.redirect_stdout(io.StringIO()):
            yayinci.AkisIstekcisi(mav, saat=SahteSaat()).iste()
        self.assertEqual({7}, {k[0] for k in mav.komutlar})
        mav = KayitMav(target_system=0, target_component=0)
        with contextlib.redirect_stdout(io.StringIO()):
            yayinci.AkisIstekcisi(mav, saat=SahteSaat()).iste()
        self.assertEqual({(0, 0)}, {(k[0], k[1]) for k in mav.komutlar},
                         "hedef bilinmiyorsa 0/0 (tum sistemler/bilesenler)")

    def test_A2_main_istegi_ilk_okumadan_once_gonderir(self):
        mav = KayitMav(_kanit_mesajlari())
        with mock.patch.object(yayinci, "mavlink_baglantisi_ac",
                               return_value=mav), \
             mock.patch.object(kanit, "_mavutil_al",
                               return_value=_sahte_mavutil()), \
             mock.patch.object(yayinci, "iha_inisini_yayinla",
                               return_value=True) as yayin, \
             contextlib.redirect_stdout(io.StringIO()) as out, \
             contextlib.redirect_stderr(io.StringIO()) as err:
            kod = yayinci.main([
                "--mavlink", "mock:pixhawk", "--kanit-timeout", "3",
                "--sysid", str(SYSID), "--heartbeat-sure", "0",
                "--ika", "127.0.0.1:5006"])
        self.assertEqual(0, kod, err.getvalue())
        yayin.assert_called_once()
        self.assertEqual(["komut", "komut", "komut"], mav.olaylar[:3],
                         "istek ilk okumadan ONCE gitmeli")
        self.assertIn("okuma", mav.olaylar)
        self.assertEqual(3, len(mav.komutlar), "kisa kosuda tek tur")
        self.assertIn("akış isteği özeti: tur=1 gönderilen=3", out.getvalue())
        self.assertNotIn("KIRMIZI", err.getvalue())
        self.assertTrue(mav.kapandi)

    def test_A3_gercek_udp_sahte_pixhawk_istegi_alir_akis_baslar_kanit_olusur(self):
        from ika_receiver import IkaReceiver
        from link import UDPLink
        from sahte_pixhawk import SahtePixhawk
        port = _bos_port()
        # Sahte Pixhawk SUNUCU kipinde: akrani gormeden hicbir sey gondermez
        # (A4). Yayincinin gonderdigi TEK sey SET_MESSAGE_INTERVAL'dir; akis
        # ancak onunla baslar -> istek olmadan kanit yok, mekanik olculur.
        sp = SahtePixhawk(f"udpin:127.0.0.1:{port}", senaryo="yerde")
        self.addCleanup(sp.dur)
        sp.baslat()
        alici_link = UDPLink(bind=("127.0.0.1", 0), timeout=0.05)
        receiver = IkaReceiver(alici_link, hb_timeout=2.0).start()
        self.addCleanup(alici_link.close)
        self.addCleanup(receiver.stop)
        t0 = time.monotonic()
        with contextlib.redirect_stdout(io.StringIO()) as out, \
             contextlib.redirect_stderr(io.StringIO()) as err:
            kod = yayinci.main([
                "--mavlink", f"udpout:127.0.0.1:{port}",
                "--sysid", str(SYSID), "--kanit-timeout", "8",
                "--heartbeat-sure", "0",
                "--ika", f"127.0.0.1:{alici_link.port}"])
        gecen = time.monotonic() - t0
        self.assertEqual(0, kod, f"stdout={out.getvalue()}\nstderr="
                                 f"{err.getvalue()}")
        self.assertTrue(receiver.wait_iha_landed(1.0))
        self.assertTrue(receiver.iha_landed)
        m = mavutil.mavlink
        komutlar = set(sp.alinan_komutlar)
        self.assertIn((m.MAV_CMD_SET_MESSAGE_INTERVAL,
                       float(m.MAVLINK_MSG_ID_EXTENDED_SYS_STATE)), komutlar)
        self.assertIn((m.MAV_CMD_SET_MESSAGE_INTERVAL,
                       float(m.MAVLINK_MSG_ID_GLOBAL_POSITION_INT)), komutlar)
        self.assertIn((m.MAV_CMD_SET_MESSAGE_INTERVAL,
                       float(m.MAVLINK_MSG_ID_GPS_RAW_INT)), komutlar)
        self.assertEqual({m.MAV_CMD_SET_MESSAGE_INTERVAL},
                         {c for c, _p in sp.alinan_komutlar},
                         "yayinci baska komut gondermez")
        self.assertGreater(sp.gonderilen["durum"], 0)
        self.assertLess(gecen, MAVLINK_AKIS_SESSIZLIK_TAVANI_S,
                        "kanit sessizlik tavanindan once olusmali")
        self.assertNotIn("KIRMIZI", err.getvalue())
        self.assertIn("gönderilen=3", out.getvalue())
        print(f"[T207_A3] exit={kod} alinan_komutlar={sp.alinan_komutlar} "
              f"sure={gecen:.2f}s")

    def test_A4_on_kosul_sunucu_kipindeki_sahte_akrani_gormeden_gondermez(self):
        from sahte_pixhawk import SahtePixhawk
        port = _bos_port()
        sp = SahtePixhawk(f"udpin:127.0.0.1:{port}", senaryo="yerde")
        self.addCleanup(sp.dur)
        sp.baslat()
        dinleyici = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.addCleanup(dinleyici.close)
        dinleyici.bind(("127.0.0.1", 0))
        dinleyici.settimeout(1.5)
        with self.assertRaises(socket.timeout):
            dinleyici.recvfrom(2048)
        self.assertGreater(sp.gonderilen["durum"], 0,
                           "sahte uretiyor ama akransiz yazamiyor")
        # Ilk paket (icerigi ne olursa olsun) akrani ogretir; akis o zaman gelir.
        dinleyici.sendto(b"\x00", ("127.0.0.1", port))
        dinleyici.settimeout(3.0)
        veri, _adr = dinleyici.recvfrom(2048)
        self.assertTrue(veri)


class B_SessizlikBekcisi(unittest.TestCase):

    def _kur(self, **kw):
        mav = KayitMav()
        saat = SahteSaat()
        out, err = io.StringIO(), io.StringIO()
        istekci = yayinci.AkisIstekcisi(mav, beklenen_sysid=SYSID, saat=saat,
                                        **kw)
        return mav, saat, istekci, out, err

    def test_B1_EXTENDED_gelmezken_KIRMIZI_bir_kez_ve_yeniden_istek(self):
        mav, saat, istekci, out, err = self._kur()
        tavan = MAVLINK_AKIS_SESSIZLIK_TAVANI_S
        aralik = MAVLINK_AKIS_ISTEK_ARALIGI_S
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            istekci.iste()
            self.assertEqual(3, len(mav.komutlar))
            # Yalniz konum akiyor; EXTENDED yok.
            for _ in range(int(tavan)):
                saat.ilerle(1.0)
                istekci.gozle(_konum())
                istekci.bakim()
            self.assertEqual(3, len(mav.komutlar),
                             "tavan ASILMADAN yeniden istek yok (strict >)")
            self.assertEqual("", err.getvalue())
            saat.ilerle(0.1)                       # tavan + 0,1
            self.assertTrue(istekci.bakim())
            self.assertEqual(6, len(mav.komutlar), "aninda yeniden istek")
            self.assertTrue(istekci.sessiz)
            self.assertEqual(1, istekci.sayac["sessizlik_uyarisi"])
            self.assertEqual(1, err.getvalue().count("KIRMIZI"))
            self.assertIn(KIRMIZI_METIN, err.getvalue())
            # Sessizlik surerken her tur spam yok, istek de yok.
            for _ in range(5):
                saat.ilerle(0.5)
                self.assertFalse(istekci.bakim())
            self.assertEqual(6, len(mav.komutlar))
            self.assertEqual(1, err.getvalue().count("KIRMIZI"))
            # Periyodik yenileme sessizlikte de surer (son istekten aralik).
            saat.t = tavan + 0.1 + aralik
            self.assertTrue(istekci.bakim())
            self.assertEqual(9, len(mav.komutlar))
            self.assertEqual(1, err.getvalue().count("KIRMIZI"),
                             "periyodik yenileme KIRMIZI basmaz")
            # Akis donuyor: toparlanma logu, alarm kapanir.
            saat.ilerle(0.5)
            self.assertTrue(istekci.gozle(_extended()))
            self.assertFalse(istekci.sessiz)
            self.assertEqual(saat.t, istekci.son_extended_monotonic)
            self.assertIn("yeniden akıyor", out.getvalue())
            # Ikinci sessizlik: ikinci KIRMIZI (durum degisti).
            saat.ilerle(tavan + 0.1)
            self.assertTrue(istekci.bakim())
            self.assertEqual(12, len(mav.komutlar))
            self.assertEqual(2, err.getvalue().count("KIRMIZI"))
            self.assertEqual(2, istekci.sayac["sessizlik_uyarisi"])
        print(f"[T207_B1] komut={len(mav.komutlar)} kirmizi="
              f"{err.getvalue().count('KIRMIZI')} sayac={istekci.sayac}")

    def test_B2_main_yolunda_sessizlik_yeniden_istek_KIRMIZI_bir_kez(self):
        saat = SahteSaat()

        def kanca():
            saat.ilerle(1.0)            # her okuma 1 sahte saniye
            time.sleep(0.002)

        mav = KayitMav([], okuma_kancasi=kanca)   # hic mesaj yok
        with mock.patch.object(yayinci, "mavlink_baglantisi_ac",
                               return_value=mav), \
             mock.patch.object(kanit, "_mavutil_al",
                               return_value=_sahte_mavutil()), \
             mock.patch.object(yayinci, "iha_inisini_yayinla") as yayin, \
             contextlib.redirect_stdout(io.StringIO()) as out, \
             contextlib.redirect_stderr(io.StringIO()) as err:
            kod = yayinci.main([
                "--mavlink", "mock:pixhawk", "--kanit-timeout", "1",
                "--sysid", str(SYSID), "--heartbeat-sure", "0",
                "--ika", "127.0.0.1:5006"], saat=saat)
        self.assertEqual(3, kod, "kanit yok -> 3")
        yayin.assert_not_called()
        turlar = len(mav.komutlar) // 3
        self.assertGreaterEqual(turlar, 3,
                                f"baslangic + sessizlik + periyodik >= 3 tur; "
                                f"gelen {turlar} (sahte t={saat.t:.0f} s)")
        self.assertEqual(1, err.getvalue().count(KIRMIZI_METIN),
                         "sessizlik KIRMIZI'si durum degisince BIR kez")
        self.assertIn("son_EXTENDED=hiç gelmedi", err.getvalue())
        beklenen_tur = 2 + int((saat.t - MAVLINK_AKIS_SESSIZLIK_TAVANI_S)
                               // MAVLINK_AKIS_ISTEK_ARALIGI_S)
        self.assertLessEqual(abs(turlar - beklenen_tur), 1,
                             f"tur={turlar} beklenen~{beklenen_tur} "
                             f"(t={saat.t:.0f})")
        print(f"[T207_B2] exit={kod} tur={turlar} sahte_t={saat.t:.0f}s "
              f"kirmizi={err.getvalue().count('KIRMIZI')}")

    def test_C1_EXTENDED_akarken_periyodik_yenileme_var_KIRMIZI_yok(self):
        mav, saat, istekci, out, err = self._kur()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            istekci.iste()
            son = None
            while saat.t < 2.5 * MAVLINK_AKIS_ISTEK_ARALIGI_S:
                saat.ilerle(0.5)
                istekci.gozle(_extended())
                istekci.gozle(_konum())
                istekci.bakim()
                son = saat.t
        self.assertEqual(3 * 3, len(mav.komutlar),
                         "t=0, 10, 20 -> 3 tur x 3 mesaj")
        self.assertEqual(3, istekci.sayac["tur"])
        self.assertEqual("", err.getvalue(), "akis akarken KIRMIZI yok")
        self.assertFalse(istekci.sessiz)
        self.assertEqual(0, istekci.sayac["sessizlik_uyarisi"])
        self.assertEqual(son, istekci.son_extended_monotonic)
        print(f"[T207_C1] komut={len(mav.komutlar)} kirmizi=0 "
              f"sahte_t={saat.t:.1f}s")

    def test_C2_yabanci_sysid_EXTENDED_sessizligi_bozmaz(self):
        mav, saat, istekci, out, err = self._kur()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            istekci.iste()
            saat.ilerle(MAVLINK_AKIS_SESSIZLIK_TAVANI_S + 0.1)
            self.assertFalse(istekci.gozle(_extended(kaynak=YABANCI)))
            self.assertIsNone(istekci.son_extended_monotonic)
            self.assertTrue(istekci.bakim())
        self.assertIn(KIRMIZI_METIN, err.getvalue())
        # Beyan yoksa her pozitif kaynak sayilir (kalinti risk, belgelendi).
        mav2 = KayitMav()
        i2 = yayinci.AkisIstekcisi(mav2, saat=SahteSaat())
        self.assertTrue(i2.gozle(_extended(kaynak=YABANCI)))
        self.assertFalse(i2.gozle(MavMesaj(kanit.MESAJ_EXTENDED_SYS_STATE, 0)),
                         "adsiz kaynak (0) sayilmaz")
        self.assertFalse(i2.gozle(None))


class D_GonderimHatasi(unittest.TestCase):

    def test_D1_OSError_yutulmaz_sayac_artar_dongu_surer(self):
        mav = KayitMav(hata=OSError("kablo koptu"))
        saat = SahteSaat()
        istekci = yayinci.AkisIstekcisi(mav, beklenen_sysid=SYSID, saat=saat)
        with contextlib.redirect_stdout(io.StringIO()), \
             contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertFalse(istekci.iste())
            self.assertEqual(3, istekci.sayac["gonderim_hatasi"])
            self.assertEqual(0, istekci.sayac["gonderilen"])
            self.assertEqual(3, err.getvalue().count("KIRMIZI"))
            self.assertIn("kablo koptu", err.getvalue())
            self.assertIn("döngü sürüyor", err.getvalue())
            # Sonraki periyodik tur yine denenir (sayac 6), istisna cikmaz.
            saat.ilerle(MAVLINK_AKIS_ISTEK_ARALIGI_S)
            self.assertFalse(istekci.bakim())
            self.assertEqual(6, istekci.sayac["gonderim_hatasi"])
            self.assertEqual(2, istekci.sayac["tur"])
        # OSError disindaki istisna gizlenmez (fail-visible).
        mav2 = KayitMav(hata=RuntimeError("beklenmeyen"))
        i2 = yayinci.AkisIstekcisi(mav2, saat=SahteSaat())
        with self.assertRaises(RuntimeError):
            i2.iste()

    def test_D2_main_OSError_ile_kanit_yine_olusur_exit_0(self):
        mav = KayitMav(_kanit_mesajlari(), hata=OSError("port kapali"))
        with mock.patch.object(yayinci, "mavlink_baglantisi_ac",
                               return_value=mav), \
             mock.patch.object(kanit, "_mavutil_al",
                               return_value=_sahte_mavutil()), \
             mock.patch.object(yayinci, "iha_inisini_yayinla",
                               return_value=True), \
             contextlib.redirect_stdout(io.StringIO()) as out, \
             contextlib.redirect_stderr(io.StringIO()) as err:
            kod = yayinci.main([
                "--mavlink", "mock:pixhawk", "--kanit-timeout", "3",
                "--sysid", str(SYSID), "--heartbeat-sure", "0",
                "--ika", "127.0.0.1:5006"])
        self.assertEqual(0, kod)
        self.assertIn("gonderim_hatasi=3", out.getvalue())
        self.assertIn("port kapali", err.getvalue())
        self.assertGreaterEqual(err.getvalue().count("KIRMIZI"), 2)


class E_AkranErtelemesi(unittest.TestCase):

    def test_E1_udp_sunucu_akran_gorulmeden_ertelenir_gorulunce_hemen(self):
        mav = KayitMav()
        mav.udp_server = True
        mav.clients = set()
        saat = SahteSaat()
        istekci = yayinci.AkisIstekcisi(mav, beklenen_sysid=SYSID, saat=saat)
        with contextlib.redirect_stdout(io.StringIO()) as out, \
             contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertFalse(istekci.iste())
            self.assertEqual([], mav.komutlar, "yazilmadi: sessiz dusurme yok")
            self.assertEqual(1, istekci.sayac["ertelenen"])
            self.assertIn("ertelendi", out.getvalue())
            saat.ilerle(0.5)
            self.assertFalse(istekci.bakim(), "akran hala yok")
            mav.clients.add(("127.0.0.1", 14550))     # ilk paket geldi
            saat.ilerle(0.5)
            self.assertTrue(istekci.bakim(), "10 s beklemeden gonderilmeli")
            self.assertEqual(3, len(mav.komutlar))
            self.assertEqual(0, istekci.sayac["gonderim_hatasi"])
        self.assertEqual("", err.getvalue())


class F_Sozlesme(unittest.TestCase):

    def test_F1_carpan_ve_aralik_mavlink_dogrula_ile_ayni(self):
        import mavlink_dogrula as md
        self.assertEqual(md.ISTEK_HIZ_CARPANI, MAVLINK_AKIS_ISTEK_HIZ_CARPANI,
                         "on-ucus araci ile uretim ayni hizi istemeli")
        for hz in (MAVLINK_DURUM_ASGARI_HZ, MAVLINK_KONUM_ASGARI_HZ):
            self.assertEqual(int(round(md.MIKROSANIYE / (hz * md.ISTEK_HIZ_CARPANI))),
                             yayinci.istek_araligi_us(hz))
        self.assertGreater(MAVLINK_AKIS_ISTEK_ARALIGI_S,
                           MAVLINK_AKIS_SESSIZLIK_TAVANI_S,
                           "yenileme araligi sessizlik tavanindan uzun olmali; "
                           "aksi halde sessizlik alarmi hic tetiklenmez")
        self.assertGreaterEqual(
            MAVLINK_AKIS_SESSIZLIK_TAVANI_S * MAVLINK_DURUM_ASGARI_HZ, 3,
            "tavan en az 3 kayip mesaj olmali (tek paket kaybi alarm degil)")
        self.assertEqual(MAVLINK_AKIS_SESSIZLIK_TAVANI_S / 10.0,
                         yayinci.AKIS_BAKIM_DILIMI_S)

    @unittest.skipIf(mavutil is None, "pymavlink kurulu degil")
    def test_F2_tanimlar_pymavlink_sabitlerinden_ve_inis_kaniti_mesajlari(self):
        m = mavutil.mavlink
        t = {x["ad"]: x for x in yayinci.akis_istek_tanimlari()}
        self.assertEqual(set(kanit.MAVLINK_INIS_MESAJLARI)
                         | {kanit.MESAJ_GPS_RAW_INT}, set(t))
        self.assertEqual(m.MAVLINK_MSG_ID_EXTENDED_SYS_STATE,
                         t[kanit.MESAJ_EXTENDED_SYS_STATE]["id"])
        self.assertEqual(m.MAVLINK_MSG_ID_GLOBAL_POSITION_INT,
                         t[kanit.MESAJ_GLOBAL_POSITION_INT]["id"])
        self.assertEqual(m.MAVLINK_MSG_ID_GPS_RAW_INT,
                         t[kanit.MESAJ_GPS_RAW_INT]["id"])

    def test_F3_gecersiz_parametreler_reddedilir(self):
        mav = KayitMav()
        with self.assertRaises(TypeError):
            yayinci.AkisIstekcisi(mav, saat=None)
        for kotu in (0, 256, True):
            with self.assertRaises(ValueError):
                yayinci.AkisIstekcisi(mav, beklenen_sysid=kotu)
        for ad in ("istek_araligi_s", "sessizlik_tavani_s", "hiz_carpani"):
            for kotu in (0, -1.0, float("nan"), float("inf"), True):
                with self.assertRaises(ValueError):
                    yayinci.AkisIstekcisi(mav, **{ad: kotu})


class G_Gozcu(unittest.TestCase):

    def test_G1_dilimli_bekleme_toplam_sureyi_korur_mesajda_hemen_doner(self):
        bakimlar = []

        class Istekci:
            def gozle(self, m):
                return False

            def bakim(self):
                bakimlar.append(time.monotonic())
                return False

        mav = KayitMav()                         # kuyruk bos: hep None
        gozcu = yayinci.AkisGozcusu(mav, Istekci(), dilim_s=0.05)
        t0 = time.monotonic()
        self.assertIsNone(gozcu.recv_match(type=["X"], blocking=True,
                                           timeout=0.3))
        gecen = time.monotonic() - t0
        self.assertGreaterEqual(gecen, 0.3 * 0.9, "sure erken bitmemeli")
        self.assertGreaterEqual(len(bakimlar), 2, "bakim dilim basina kosar")
        # Mesaj varsa hemen doner (5 s tavani beklemez) ve ayni nesnedir.
        mesaj = _extended()
        mav.mesajlar = [mesaj]
        t0 = time.monotonic()
        self.assertIs(mesaj, gozcu.recv_match(type=["X"], blocking=True,
                                              timeout=5.0))
        self.assertLess(time.monotonic() - t0, 1.0)
        # Oznitelikler gercek baglantiya devredilir.
        mav.inis_kaniti_deadline_monotonic = 123.0
        self.assertEqual(123.0, gozcu.inis_kaniti_deadline_monotonic)
        self.assertEqual(SYSID, gozcu.target_system)

    def test_G2_gozcu_yerde_mi_ile_ayni_karari_verir(self):
        """Sargi karar mantigini degistirmez: ayni mesaj dizisi ayni sonuc."""
        mavutil_sahte = _sahte_mavutil()
        for dizi, beklenen in (
                (_kanit_mesajlari(3), True),
                (_kanit_mesajlari(2), False),
                ([_extended(yerde=False)] + _kanit_mesajlari(3), True),
                ([_extended(), _konum(bagil_mm=5000)] + _kanit_mesajlari(3),
                 True)):
            for sargi in (False, True):
                mav = KayitMav(list(dizi))
                mav.inis_kaniti_deadline_monotonic = time.monotonic() + 0.4
                hedef = mav
                if sargi:
                    istekci = yayinci.AkisIstekcisi(mav, beklenen_sysid=SYSID,
                                                    saat=SahteSaat())
                    hedef = yayinci.AkisGozcusu(mav, istekci, dilim_s=0.05)
                with mock.patch.object(kanit, "_mavutil_al",
                                       return_value=mavutil_sahte), \
                     contextlib.redirect_stdout(io.StringIO()):
                    sonuc = kanit.yerde_mi(hedef, beklenen_sysid=SYSID)
                with self.subTest(sargi=sargi, n=len(dizi)):
                    self.assertEqual(beklenen, sonuc)


if __name__ == "__main__":
    unittest.main()
