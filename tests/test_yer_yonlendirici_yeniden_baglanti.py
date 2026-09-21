"""yer_yonlendirici: USB kopup geri takilinca seri port yeniden acilir (19 Eyl 2026 saha hatasi).

Olculen hata: kablo cikip takilinca pyserial her cagrida
"ClearCommError failed (PermissionError(13, ...))" / "WriteFile failed (PermissionError(13, ...))"
atti; betik ~900 kez logladi, hic toparlanmadi (seri_hata 1793, seri->udp 0 B/s).

Gercek seri port ASLA acilmaz: acici sahte (Dunya.ac) enjekte edilir ve serial.Serial
cagrisi test boyunca AssertionError atar. Saat/uyku sahte; UDP akranlari gercek localhost
soketleri (gecici portlar, 14550/14590 degil).
"""
import socket
import sys
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

import serial

KOK = Path(__file__).resolve().parents[1]
if str(KOK / "scripts") not in sys.path:
    sys.path.insert(0, str(KOK / "scripts"))
import yer_yonlendirici as yy  # noqa: E402

PORT, BAUD = "COM_SAHTE", 57600


class Saat:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t

    def uyku(self, dt):
        self.t += dt


class SahteSeri:
    def __init__(self, bekle=0.0):
        self.acik, self.bekle = True, bekle
        self.gelen, self.yazilan = bytearray(), bytearray()
        self.okuma_hatasi = self.yazma_hatasi = None

    def _denetle(self, hata):
        if not self.acik:
            raise serial.PortNotOpenError()
        if hata is not None:
            raise hata

    @property
    def in_waiting(self):
        self._denetle(self.okuma_hatasi)
        return len(self.gelen)

    def read(self, n):
        self._denetle(self.okuma_hatasi)
        if not self.gelen and self.bekle:
            time.sleep(self.bekle)
        v = bytes(self.gelen[:n])
        del self.gelen[:n]
        return v

    def write(self, b):
        self._denetle(self.yazma_hatasi)
        self.yazilan += b
        return len(b)

    def close(self):
        self.acik = False


class Dunya:
    """Sahte USB: var=False iken acma, Windows'taki gibi 'could not open port' atar."""

    def __init__(self, saat, bekle=0.0):
        self.saat, self.bekle, self.var = saat, bekle, True
        self.acilanlar, self.denemeler = [], []

    def ac(self, port, baud):
        self.denemeler.append((self.saat(), port, baud))
        if not self.var:
            raise serial.SerialException(f"could not open port '{port}': FileNotFoundError(2, 'sahte')")
        s = SahteSeri(self.bekle)
        self.acilanlar.append(s)
        return s


def okuma_hatalari():
    return [PermissionError(13, "Erisim engellendi.", None, 5),
            serial.SerialException("ClearCommError failed (PermissionError(13, 'Erisim engellendi.', None, 5))"),
            serial.PortNotOpenError()]


def yazma_hatalari():
    return [serial.SerialException("WriteFile failed (PermissionError(13, 'Aygit komutu algilayamiyor.', None, 22))"),
            PermissionError(13, "Aygit komutu algilayamiyor.", None, 22),
            serial.PortNotOpenError()]


class Tezgah:
    def __init__(self, tc, saat=None, uyku=None, bekle=0.0):
        p = mock.patch.object(yy.serial, "Serial", side_effect=AssertionError("gercek seri port acilmamali"))
        p.start()
        tc.addCleanup(p.stop)
        self.saat = saat or Saat()
        self.dunya = Dunya(self.saat, bekle)
        self.akran = {}
        for ad in ("mp", "tunel"):
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.bind(("127.0.0.1", 0))
            s.settimeout(1.0)
            tc.addCleanup(s.close)
            self.akran[ad] = s
        hedefler = yy.udp_hedefler("127.0.0.1:%d" % self.akran["mp"].getsockname()[1],
                                   "127.0.0.1:%d" % self.akran["tunel"].getsockname()[1])
        for _, s, _ in hedefler:
            tc.addCleanup(s.close)
        self.loglar = []
        self.y = yy.Yonlendirici(PORT, BAUD, hedefler, ac=self.dunya.ac, saat=self.saat,
                                 uyku=uyku or self.saat.uyku,
                                 log=lambda m, hata=False: self.loglar.append((self.saat(), hata, m)))
        self.soket = {ad: s for ad, s, _ in hedefler}

    def seri_udp(self, tc, veri):
        """Seri -> iki akran; akranlarin gordugu kaynak adresleri doner."""
        self.y.ser.gelen += veri
        self.y.seri_adim()
        kaynak = {}
        for ad, s in self.akran.items():
            gelen, kaynak[ad] = s.recvfrom(4096)
            tc.assertEqual(gelen, veri, ad)
        return kaynak

    def udp_gonder(self, ad, veri):
        self.akran[ad].sendto(veri, self.soket[ad].getsockname())
        self.y.udp_adim(ad, self.soket[ad])

    def logda(self, parca):
        return [m for _, _, m in self.loglar if parca in m]


class YenidenBaglanti(unittest.TestCase):
    def test_a_okuma_hatasi_kapat_yeniden_ac_iki_yon_akar(self):
        for hata in okuma_hatalari():
            with self.subTest(hata=repr(hata)):
                t = Tezgah(self)
                eski = t.y.ser
                t.seri_udp(self, b"\xfe\x09once")
                t.udp_gonder("mp", b"MP1")
                t.udp_gonder("tunel", b"TN1")
                self.assertEqual(bytes(eski.yazilan), b"MP1TN1")

                eski.okuma_hatasi, t.dunya.var = hata, False
                t.y.seri_adim()
                self.assertFalse(eski.acik, "olu tutamac kapatilmadi")
                self.assertIsNone(t.y.ser)
                self.assertFalse(t.y.bagli())
                self.assertEqual(t.y.say["seri_hata"], 1)
                self.assertEqual(len(t.logda("okuma hatasi")), 1)

                t.y.seri_adim()
                t.y.seri_adim()
                self.assertEqual(len(t.dunya.denemeler), 1 + 2, "yeniden acma denenmedi")
                self.assertIsNone(t.y.ser)

                t.dunya.var = True
                t.y.seri_adim()
                yeni = t.dunya.acilanlar[-1]
                self.assertIsNot(yeni, eski)
                self.assertIs(t.y.ser, yeni)
                self.assertTrue(t.y.bagli())
                self.assertEqual({(p, b) for _, p, b in t.dunya.denemeler}, {(PORT, BAUD)})
                self.assertEqual(t.y.say["yeniden_baglanti"], 1)
                self.assertEqual(t.logda("SERI YENIDEN BAGLANDI"),
                                 [f"[YONLENDIRICI] SERI YENIDEN BAGLANDI {PORT} (kopukluk 3.0 s, deneme 3)"])

                t.seri_udp(self, b"\xfe\x09sonra")
                t.udp_gonder("mp", b"MP2")
                t.udp_gonder("tunel", b"TN2")
                self.assertEqual(bytes(yeni.yazilan), b"MP2TN2")
                self.assertEqual(t.y.say["mp_seri"], 6)
                self.assertEqual(t.y.say["tunel_seri"], 6)

    def test_b_surekli_basarisiz_deneme_cokmez_log_5s_de_bir(self):
        t = Tezgah(self)
        t.y.ser.okuma_hatasi, t.dunya.var = PermissionError(13, "Erisim engellendi."), False
        t.y.seri_adim()
        t0 = t.saat()
        for _ in range(60):
            t.y.seri_adim()
        self.assertEqual(t.saat() - t0, 60.0)
        zamanlar = [z for z, _, _ in t.dunya.denemeler[1:]]
        self.assertEqual(len(zamanlar), 60)
        self.assertTrue(all(b - a >= 1.0 for a, b in zip(zamanlar, zamanlar[1:])), "1 s araligi yok")
        loglu = [z for z, _, m in t.loglar if "yeniden acilamadi" in m]
        self.assertGreaterEqual(len(loglu), 2, "basarisiz denemeler hic loglanmiyor")
        self.assertLessEqual(len(loglu), 1 + 60 // 5, loglu)
        self.assertTrue(all(b - a >= 5.0 for a, b in zip(loglu, loglu[1:])), loglu)
        self.assertLessEqual(len(t.loglar), 2 + 60 // 5, "log seli")
        satir = t.y.istatistik_satiri(dict.fromkeys(t.y.say, 0), 5.0)
        self.assertIn("seri_bagli=0", satir)
        self.assertIn("yeniden_baglanti=0", satir)

        t.dunya.var = True
        t.y.seri_adim()
        self.assertTrue(t.y.bagli())
        self.assertEqual(t.logda("SERI YENIDEN BAGLANDI"),
                         [f"[YONLENDIRICI] SERI YENIDEN BAGLANDI {PORT} (kopukluk 61.0 s, deneme 61)"])
        satir = t.y.istatistik_satiri(dict.fromkeys(t.y.say, 0), 5.0)
        self.assertIn("seri_bagli=1", satir)
        self.assertIn("yeniden_baglanti=1", satir)

    def test_c_kopukken_udp_dusurulur_ve_sayilir(self):
        t = Tezgah(self)
        eski = t.y.ser
        eski.okuma_hatasi, t.dunya.var = serial.SerialException("ClearCommError failed"), False
        t.y.seri_adim()
        for i in range(3):
            t.udp_gonder("mp", b"MP%d" % i)
        for i in range(2):
            t.udp_gonder("tunel", b"TN%d" % i)
        self.assertEqual(t.y.say["dusen_udp"], 5)
        self.assertEqual((t.y.say["mp_seri"], t.y.say["tunel_seri"]), (0, 0))
        self.assertEqual(t.y.say["seri_hata"], 1, "kapali tutamaca yazma denendi")
        self.assertEqual(bytes(eski.yazilan), b"")
        self.assertIn("dusen_udp=5", t.y.istatistik_satiri(dict.fromkeys(t.y.say, 0), 5.0))

    def test_d_ayni_udp_soketi_ve_kaynak_adres(self):
        t = Tezgah(self)
        soketler = [s for _, s, _ in t.y.hedefler]
        adresler = [s.getsockname() for s in soketler]
        once = t.seri_udp(self, b"once")
        t.y.ser.okuma_hatasi = PermissionError(13, "Erisim engellendi.")
        t.y.seri_adim()
        t.y.seri_adim()
        self.assertTrue(t.y.bagli())
        self.assertEqual(len(t.dunya.acilanlar), 2)
        sonra = t.seri_udp(self, b"sonra")
        self.assertEqual([s for _, s, _ in t.y.hedefler], soketler)
        self.assertTrue(all(a is b for a, b in zip((s for _, s, _ in t.y.hedefler), soketler)))
        self.assertEqual([s.getsockname() for _, s, _ in t.y.hedefler], adresler)
        self.assertEqual(sonra, once, "akranlar farkli kaynak adresten aliyor")
        self.assertTrue(all(s.fileno() != -1 for s in soketler), "UDP soketi kapatildi")

    def test_e_yazma_hatasi_da_yeniden_baglar(self):
        for hata in yazma_hatalari():
            with self.subTest(hata=repr(hata)):
                t = Tezgah(self)
                eski = t.y.ser
                eski.yazma_hatasi = hata
                t.udp_gonder("mp", b"MP1")
                self.assertEqual(t.y.say["seri_hata"], 1)
                self.assertFalse(t.y.bagli())
                self.assertEqual(t.y.say["mp_seri"], 0)
                self.assertEqual(len(t.logda("yazma hatasi")), 1)
                t.udp_gonder("tunel", b"TN1")  # oku ipligi kapatmadan once: dusurulur
                self.assertEqual(t.y.say["dusen_udp"], 1)
                self.assertEqual(t.y.say["seri_hata"], 1)

                t.y.seri_adim()
                self.assertFalse(eski.acik, "olu tutamac kapatilmadi")
                yeni = t.dunya.acilanlar[-1]
                self.assertIsNot(yeni, eski)
                self.assertIs(t.y.ser, yeni)
                self.assertEqual(len(t.logda("SERI YENIDEN BAGLANDI")), 1)
                t.udp_gonder("mp", b"MP2")
                t.udp_gonder("tunel", b"TN2")
                self.assertEqual(bytes(yeni.yazilan), b"MP2TN2")
                t.seri_udp(self, b"sonra")

    def test_f_gercek_ipliklerle_uctan_uca(self):
        t = Tezgah(self, saat=time.monotonic, uyku=lambda dt: time.sleep(0.02), bekle=0.005)
        self.addCleanup(t.y.dur.set)
        t.y.baslat()

        def bekle(kosul, sure=2.0):
            son = time.monotonic() + sure
            while time.monotonic() < son:
                if kosul():
                    return True
                time.sleep(0.005)
            return False

        def iki_yon(ser, veri):
            ser.gelen += veri
            for ad, s in t.akran.items():  # bayt borusu parcali iletebilir (gercek seri gibi)
                gelen = b""
                while len(gelen) < len(veri):
                    gelen += s.recvfrom(4096)[0]
                self.assertEqual(gelen, veri, ad)
            n = len(ser.yazilan)
            t.akran["mp"].sendto(b"M" + veri, t.soket["mp"].getsockname())
            t.akran["tunel"].sendto(b"T" + veri, t.soket["tunel"].getsockname())
            self.assertTrue(bekle(lambda: len(ser.yazilan) >= n + 2 * (len(veri) + 1)), bytes(ser.yazilan))

        eski = t.y.ser
        iki_yon(eski, b"once")
        eski.okuma_hatasi, t.dunya.var = PermissionError(13, "Erisim engellendi."), False
        self.assertTrue(bekle(lambda: not eski.acik and len(t.dunya.denemeler) >= 3))
        t.dunya.var = True
        self.assertTrue(bekle(lambda: t.y.bagli() and t.y.ser is not eski))
        iki_yon(t.y.ser, b"sonra")
        self.assertEqual(len(t.logda("SERI YENIDEN BAGLANDI")), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
