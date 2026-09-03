"""NEDEN: YKİ'de GPS ve gerçek ARM durumu görünür değilse operatör bağlantıyı
canlı sansa bile aracın konum/fix/durum kanıtını göremez. Bu kapı, üç MAVLink
akışının tek okuyucudan atomik ve fail-closed HEARTBEAT alanlarına taşındığını
kanıtlar; bayat son değer hiçbir koşulda tekrar kullanılamaz.
"""

import sys
import threading
import unittest
import json
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


KOK = Path(__file__).resolve().parents[1]
for _dizin in (KOK / "comms", KOK / "codes"):
    if str(_dizin) not in sys.path:
        sys.path.insert(0, str(_dizin))

import iha_sender  # noqa: E402
import inis_kaniti as kanit  # noqa: E402
import rpi_inference as ri  # noqa: E402


SYSID = 1
COMPONENT = 1
ARM_BAYRAGI = 128


class SahteSaat:
    def __init__(self, simdi=0.0):
        self.simdi = float(simdi)

    def __call__(self):
        return self.simdi


class Mesaj:
    def __init__(self, tip, sysid=SYSID, component=COMPONENT, **alanlar):
        self._tip = tip
        self._sysid = sysid
        self._component = component
        for ad, deger in alanlar.items():
            setattr(self, ad, deger)

    def get_type(self):
        return self._tip

    def get_srcSystem(self):
        return self._sysid

    def get_srcComponent(self):
        return self._component


class Akis:
    def __init__(self, mesajlar=()):
        self.mesajlar = list(mesajlar)
        self.cagrilar = []
        self.target_system = SYSID
        self.target_component = COMPONENT

    def recv_match(self, **kwargs):
        self.cagrilar.append(kwargs)
        return self.mesajlar.pop(0) if self.mesajlar else None


def _konum(zaman=1, sysid=SYSID, *, lat=39.925533, lon=32.866287,
           alt=31.25):
    return Mesaj(
        kanit.MESAJ_GLOBAL_POSITION_INT, sysid,
        time_boot_ms=zaman, relative_alt=int(round(alt * 1000)),
        lat=int(round(lat * 1e7)), lon=int(round(lon * 1e7)))


def _gps(zaman=1, sysid=SYSID, *, fix=3, uydu=12):
    return Mesaj(kanit.MESAJ_GPS_RAW_INT, sysid, time_usec=zaman,
                 fix_type=fix, satellites_visible=uydu)


def _hb(sysid=SYSID, *, armed=True):
    return Mesaj(kanit.MESAJ_HEARTBEAT, sysid,
                 base_mode=ARM_BAYRAGI if armed else 0)


class TekOkuyucuSnapshotTests(unittest.TestCase):
    def setUp(self):
        mavlink = SimpleNamespace(
            MAV_MODE_FLAG_SAFETY_ARMED=ARM_BAYRAGI,
            MAV_COMP_ID_AUTOPILOT1=COMPONENT)
        self.yama = mock.patch.object(
            kanit, "_mavutil_al", return_value=SimpleNamespace(
                mavlink=mavlink,
                mode_string_v10=lambda mesaj: getattr(
                    mesaj, "mode_string", "UNKNOWN")))
        self.yama.start()

    def tearDown(self):
        self.yama.stop()

    def _okuyucu(self, mesajlar, saat, *, durum_tazelik=1.5):
        akis = Akis(mesajlar)
        okuyucu = kanit.BagilIrtifaOkuyucu(
            akis, 0.5, beklenen_sysid=SYSID,
            durum_tazelik_s=durum_tazelik, monotonic=saat)
        return okuyucu, akis

    def test_uc_akis_tek_atomik_snapshotta(self):
        saat = SahteSaat()
        okuyucu, akis = self._okuyucu(
            [_konum(), _gps(), _hb(armed=True)], saat)

        self.assertEqual({
            "lat": 39.925533,
            "lon": 32.866287,
            "alt": 31.25,
            "gps_fix": 3,
            "uydu": 12,
            "armed": True,
            "pixhawk_canli": True,
        }, okuyucu.telemetri_oku())
        self.assertTrue(all(
            c == {"type": kanit.MAVLINK_TELEMETRI_MESAJLARI,
                  "blocking": False}
            for c in akis.cagrilar))

    def test_irtifa_gps_ve_armed_kendi_tazelik_esiklerinde_omit(self):
        saat = SahteSaat()
        okuyucu, _akis = self._okuyucu(
            [_konum(), _gps(), _hb()], saat, durum_tazelik=1.5)
        okuyucu.telemetri_oku()

        saat.simdi = 0.5
        self.assertEqual({"armed": True, "pixhawk_canli": True},
                         okuyucu.telemetri_snapshot(),
                         "0,50 s esigindeki konum/GPS son degeri sizdi")
        saat.simdi = 1.5
        self.assertEqual({}, okuyucu.telemetri_snapshot(),
                         "bayat ARM son bilinen deger olarak sizdi")

    def test_durum_esigi_verilmezse_armed_yayinlanmaz(self):
        saat = SahteSaat()
        okuyucu, _akis = self._okuyucu(
            [_hb()], saat, durum_tazelik=None)
        self.assertEqual({}, okuyucu.telemetri_oku())

    def test_bozuk_gps_yalniz_gps_alanlarini_temizler(self):
        saat = SahteSaat()
        okuyucu, akis = self._okuyucu(
            [_konum(), _gps(), _hb()], saat)
        okuyucu.telemetri_oku()
        saat.simdi = 0.1
        akis.mesajlar.append(_gps(zaman=2, fix=True, uydu=19))

        sonuc = okuyucu.telemetri_oku()
        self.assertNotIn("gps_fix", sonuc)
        self.assertNotIn("uydu", sonuc)
        self.assertEqual(31.25, sonuc["alt"])
        self.assertTrue(sonuc["armed"])

    def test_yabanci_kaynak_hicbir_alani_degistirmez(self):
        saat = SahteSaat()
        okuyucu, akis = self._okuyucu(
            [_konum(), _gps(), _hb()], saat)
        beklenen = okuyucu.telemetri_oku()
        saat.simdi = 0.1
        akis.mesajlar.extend([
            _konum(2, 99, lat=1.0, lon=2.0, alt=99.0),
            _gps(2, 99, fix=1, uydu=1),
            _hb(99, armed=False),
        ])
        self.assertEqual(beklenen, okuyucu.telemetri_oku())

    def test_tekrar_gps_paketi_yasi_yenilemez(self):
        saat = SahteSaat()
        okuyucu, akis = self._okuyucu([_gps(zaman=10)], saat)
        self.assertEqual({"gps_fix": 3, "uydu": 12},
                         okuyucu.telemetri_oku())
        saat.simdi = 0.4
        akis.mesajlar.append(_gps(zaman=10, fix=4, uydu=20))
        okuyucu.telemetri_oku()
        saat.simdi = 0.5
        self.assertEqual({}, okuyucu.telemetri_snapshot())

    def test_MUTASYON_pixhawk_reboot_iki_ilerleyen_ornekle_yeni_cag_acar(self):
        """Eski kod iki reboot paketini de eski uptime aşılana dek reddederdi."""
        saat = SahteSaat()
        okuyucu, akis = self._okuyucu(
            [_konum(zaman=120_000, alt=31.0),
             _gps(zaman=120_000_000, fix=3, uydu=12)], saat)
        self.assertEqual(31.0, okuyucu.telemetri_oku()["alt"])

        # Büyük geri adımın ilk paketi yalnız aday: eski veri de fail-closed
        # temizlenir; tek gecikmiş paket reboot diye kabul edilmez.
        saat.simdi = 0.6
        akis.mesajlar.extend([
            _konum(zaman=100, alt=32.0),
            _gps(zaman=100_000, fix=4, uydu=18),
        ])
        self.assertEqual({}, okuyucu.telemetri_oku())

        # Aynı düşük çağda zaman ilerledi: reboot açıkça doğrulandı.
        saat.simdi = 0.7
        akis.mesajlar.extend([
            _konum(zaman=200, alt=32.5),
            _gps(zaman=200_000, fix=4, uydu=19),
        ])
        self.assertEqual({
            "lat": 39.925533, "lon": 32.866287, "alt": 32.5,
            "gps_fix": 4, "uydu": 19,
        }, okuyucu.telemetri_oku())

    def test_kucuk_out_of_order_reboot_sayilmaz_ve_yasi_yenilemez(self):
        saat = SahteSaat()
        okuyucu, akis = self._okuyucu(
            [_konum(zaman=10_000, alt=31.0),
             _gps(zaman=10_000_000, fix=3, uydu=12)], saat)
        okuyucu.telemetri_oku()
        saat.simdi = 0.4
        akis.mesajlar.extend([
            _konum(zaman=9_900, alt=99.0),
            _gps(zaman=9_900_000, fix=1, uydu=1),
        ])
        sonuc = okuyucu.telemetri_oku()
        self.assertEqual(31.0, sonuc["alt"])
        self.assertEqual(3, sonuc["gps_fix"])
        saat.simdi = 0.5
        self.assertEqual({}, okuyucu.telemetri_snapshot(),
                         "küçük sıra dışı paket eski örneğin yaşını yeniledi")

    def test_baglanti_yasam_dongusu_sira_damgalarini_da_sifirlar(self):
        saat = SahteSaat()
        okuyucu, akis = self._okuyucu(
            [_konum(zaman=120_000, alt=31.0),
             _gps(zaman=120_000_000, fix=3, uydu=12)], saat)
        okuyucu.telemetri_oku()
        akis.mesajlar.append(OSError("Pixhawk yeniden baglaniyor"))
        self.assertEqual({}, okuyucu.telemetri_oku())

        # Yeni bağlantı çağında ilk düşük damga bekletilmeden kabul edilir;
        # eski uptime'a erişmesi saatlerce beklenmez.
        saat.simdi = 0.1
        akis.mesajlar.extend([
            _konum(zaman=100, alt=32.0),
            _gps(zaman=100_000, fix=4, uydu=18),
        ])
        self.assertEqual(32.0, okuyucu.telemetri_oku()["alt"])

    def test_uydu_255_bilinmiyor_alanini_yazmaz(self):
        saat = SahteSaat()
        okuyucu, _akis = self._okuyucu(
            [_gps(uydu=kanit.GPS_UYDU_BILINMIYOR)], saat)
        self.assertEqual({"gps_fix": 3}, okuyucu.telemetri_oku())

    def test_yerde_alt_sifir_ve_gps_gorunur_ama_olcek_irtifasi_olmaz(self):
        saat = SahteSaat()
        okuyucu, _akis = self._okuyucu(
            [_konum(alt=0.0)], saat)
        self.assertEqual({"lat": 39.925533, "lon": 32.866287, "alt": 0.0},
                         okuyucu.telemetri_oku())
        self.assertIsNone(okuyucu.irtifa_m(),
                          "yerdeki 0 m olcek irtifasi olarak kullanildi")


class UretimSaglayiciTests(unittest.TestCase):
    def test_tek_snapshot_ham_gnss_ve_ayni_ornekten_yerel_xy_uretir(self):
        ham = {"lat": 39.925633, "lon": 32.866387, "alt": 30.0,
               "hiz": 12.4, "yon": 178.2, "gps_fix": 3, "uydu": 14,
               "bat": 15.7, "bat_yuzde": 68, "armed": False, "mod": "AUTO",
               "pixhawk_canli": True}

        class Okuyucu:
            adet = 0

            def telemetri_snapshot(self):
                self.adet += 1
                return dict(ham)

        okuyucu = Okuyucu()
        saglayici = ri._telemetri_saglayici(
            SimpleNamespace(okuyucu=okuyucu), (39.925533, 32.866287))
        sonuc = saglayici()
        x, y = ri.yerel_konum_m(
            39.925533, 32.866287, ham["lat"], ham["lon"])

        self.assertEqual(1, okuyucu.adet, "snapshot bir turda iki kez okundu")
        self.assertEqual((x, y), (sonuc["x"], sonuc["y"]))
        for ad in ham:
            self.assertEqual(ham[ad], sonuc[ad])

    def test_referans_yokken_ham_gnss_kalir_xy_uydurulmaz(self):
        okuyucu = SimpleNamespace(
            telemetri_snapshot=lambda: {"lat": 39.0, "lon": 32.0,
                                        "gps_fix": 2})
        sonuc = ri._telemetri_saglayici(
            SimpleNamespace(okuyucu=okuyucu), None)()
        self.assertEqual({"lat": 39.0, "lon": 32.0, "gps_fix": 2}, sonuc)
        self.assertNotIn("x", sonuc)
        self.assertNotIn("y", sonuc)

    def test_okuyucu_yoksa_ikinci_telemetri_yolu_acilmaz(self):
        self.assertIsNone(ri._telemetri_saglayici(None))
        self.assertIsNone(ri._telemetri_saglayici(
            SimpleNamespace(okuyucu=object())))


class KararYayinciSnapshotTests(unittest.TestCase):
    @staticmethod
    def _bir_tur(saglayici, eski_kanca=None):
        y = iha_sender.KararYayinci.__new__(iha_sender.KararYayinci)
        y._dur = threading.Event()
        y.hata = []
        y.heartbeat_sayisi = 0
        y.heartbeat_aralik = 0.001
        y.telemetri_saglayici = saglayici
        y.konum_saglayici = eski_kanca
        y.irtifa_saglayici = eski_kanca
        y._son_karar_monotonik = None
        cagrilar = []

        class Sender:
            def send_heartbeat(_self, node="iha", **alanlar):
                cagrilar.append(dict(alanlar))
                y._dur.set()

        y.sender = Sender()
        y._heartbeat_dongusu()
        return cagrilar, y

    def test_atomik_saglayici_varken_eski_kancalar_cagrilmaz(self):
        adet = {"yeni": 0, "eski": 0}

        def yeni():
            adet["yeni"] += 1
            return {"lat": 39.9, "lon": 32.8, "alt": 31.2,
                    "hiz": 13.1, "yon": 92.0, "gps_fix": 3, "uydu": 16,
                    "bat": 15.4, "bat_yuzde": 64, "armed": True, "mod": "AUTO",
                    "pixhawk_canli": True}

        def eski():
            adet["eski"] += 1
            raise AssertionError("atomik snapshot varken eski kanca cagrildi")

        cagrilar, y = self._bir_tur(yeni, eski)
        self.assertEqual(1, adet["yeni"])
        self.assertEqual(0, adet["eski"])
        self.assertEqual({"lat": 39.9, "lon": 32.8, "alt": 31.2,
                          "hiz": 13.1, "yon": 92.0, "gps_fix": 3,
                          "uydu": 16, "bat": 15.4, "bat_yuzde": 64,
                          "armed": True,
                          "mod": "AUTO", "pixhawk_canli": True},
                         cagrilar[0])
        self.assertEqual(1, y.heartbeat_sayisi)
        self.assertEqual([], y.hata)

    def test_bos_ve_hatalı_snapshot_son_deger_uydurmaz_heartbeat_surer(self):
        for saglayici in (lambda: {}, lambda: (_ for _ in ()).throw(
                RuntimeError("MAVLink koptu"))):
            with self.subTest(saglayici=saglayici):
                cagrilar, y = self._bir_tur(saglayici)
                self.assertEqual([{}], cagrilar)
                self.assertEqual(1, y.heartbeat_sayisi)
                if y.hata:
                    self.assertIn("MAVLink koptu", y.hata[0])

    def test_snapshot_gercek_protokol_heartbeat_cercevesine_girer(self):
        class Link:
            def __init__(self):
                self.gonderilen = []

            def send(self, veri, hedef):
                self.gonderilen.append((veri, hedef))

        link = Link()
        asil_sender = iha_sender.IhaSender(
            link, {"yks": ("127.0.0.1", 5005)})
        y = iha_sender.KararYayinci.__new__(iha_sender.KararYayinci)
        y._dur = threading.Event()
        y.hata = []
        y.heartbeat_sayisi = 0
        y.heartbeat_aralik = 0.001
        y.telemetri_saglayici = lambda: {
            "lat": 39.925533, "lon": 32.866287, "alt": 31.2,
            "hiz": 11.0, "yon": 270.0, "gps_fix": 3, "uydu": 15,
            "bat": 15.8, "bat_yuzde": 66, "armed": True, "mod": "AUTO",
            "pixhawk_canli": True,
        }
        y.konum_saglayici = None
        y.irtifa_saglayici = None
        y._son_karar_monotonik = None

        class BirTurSender:
            def send_heartbeat(_self, node="iha", **alanlar):
                sonuc = asil_sender.send_heartbeat(node, **alanlar)
                y._dur.set()
                return sonuc

        y.sender = BirTurSender()
        y._heartbeat_dongusu()

        self.assertEqual(1, len(link.gonderilen))
        mesaj = json.loads(link.gonderilen[0][0].decode("utf-8"))
        self.assertEqual("HEARTBEAT", mesaj["type"])
        self.assertEqual("iha", mesaj["node"])
        for ad, deger in y.telemetri_saglayici().items():
            self.assertEqual(deger, mesaj[ad])


if __name__ == "__main__":
    unittest.main()
