"""K5+K6 — şartname §6.2 süre limitleri (2026-08-26).

K5: ika_nav iki AYRI deadline kullanır — bekleme (rota+iniş+IKA_GO, İHA görev
    süresi 15 dk) ve sürüş (izin anından HB'ye, İKA görev süresi 10 dk).
    Eski tek 60 s deadline sahada İKA'yı görevden düşürüyordu.
K6: iha_inis_yayinci CLI iniş sonrası heartbeat sürdürür; alıcı link_lost
    ancak heartbeat gerçekten kesilince oluşur.

Sahte saat kullanılır; time.sleep'e dayanan süre iddiası yoktur.
"""

from __future__ import annotations

import contextlib
import io
import sys
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

KOK = Path(__file__).resolve().parents[1]
for _p in (KOK / "comms", KOK / "codes", KOK / "simulation" / "scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import ika_nav  # noqa: E402
import iha_inis_yayinci as yayinci  # noqa: E402
import inis_kaniti as kanit  # noqa: E402
import karar_sozlesmesi as ks  # noqa: E402
from ika_receiver import IkaReceiver  # noqa: E402
from link import UDPLink  # noqa: E402


class SahteSaat:
    def __init__(self, t0=1000.0):
        self.t = float(t0)

    def __call__(self):
        return self.t

    def ilerle(self, s):
        self.t += float(s)


class SahteReceiver:
    def __init__(self):
        self.link_ok = True
        self.link = SimpleNamespace(close=lambda: None)
        self.durduruldu = False

    def stop(self):
        self.durduruldu = True


ROTA = {"type": "OPEN_ROUTE", "road": 1, "seq": 1}


class K5BeklemeVeSurusDeadlineTests(unittest.TestCase):
    def test_sozlesme_sabitleri_sartname_degerleri(self):
        # §6.2: İHA 15 dk, İKA 10 dk (PDF sayfa 23-24, fitz ile okundu)
        self.assertEqual(900.0, ks.SARTNAME_IHA_GOREV_SURESI_S)
        self.assertEqual(600.0, ks.SARTNAME_IKA_GOREV_SURESI_S)
        self.assertEqual(ks.SARTNAME_IHA_GOREV_SURESI_S, ks.IKA_BEKLEME_SURESI_S)
        self.assertEqual(ks.SARTNAME_IKA_GOREV_SURESI_S, ks.IKA_SURUS_SURESI_S)
        self.assertGreater(ks.IKA_BEKLEME_SURESI_S, 60.0)
        self.assertEqual(ks.IKA_BEKLEME_SURESI_S, ika_nav.IKA_BEKLEME_SURESI_S)

    def test_bekleme_60s_de_dusmez_ve_surus_deadline_i_ayri_isler(self):
        saat = SahteSaat(1000.0)
        rx = SahteReceiver()
        kayit = {}

        def rota_bekle(bind, timeout, keep_receiver, deadline_monotonic):
            kayit["bekleme_timeout"] = timeout
            kayit["bekleme_deadline"] = deadline_monotonic
            saat.ilerle(61.0)          # rota 61 s sonra geldi (eski limit 60)
            return ROTA, rx

        def izin_bekle(receiver, kalan, deadline_monotonic):
            kayit["izin_kalan"] = kalan
            kayit["izin_deadline"] = deadline_monotonic
            saat.ilerle(240.0)         # iniş + IKA_GO 4 dk daha sürdü
            # eski tek deadline (60 s) çoktan geçmiş olmalı
            self.assertGreater(saat(), 1000.0 + 60.0)
            return saat() < deadline_monotonic

        def sur(route, **kw):
            kayit["surus_deadline"] = kw["surus_deadline_monotonic"]
            kayit["surus_baslangic"] = saat()
            return True

        with mock.patch.object(ika_nav, "send_vel",
                               lambda r, l, topic=None: None), \
             contextlib.redirect_stdout(io.StringIO()):
            kod = ika_nav.ika_gorevi(
                "127.0.0.1:0", saat=saat,
                rota_bekle=rota_bekle, izin_bekle=izin_bekle, sur=sur)
        self.assertEqual(0, kod)
        self.assertEqual(1000.0 + ks.IKA_BEKLEME_SURESI_S,
                         kayit["bekleme_deadline"])
        self.assertEqual(kayit["bekleme_deadline"], kayit["izin_deadline"])
        self.assertAlmostEqual(ks.IKA_BEKLEME_SURESI_S - 61.0,
                               kayit["izin_kalan"])
        # Sürüş deadline'ı izin ANINDA başlar; beklemeden bağımsızdır.
        self.assertEqual(1000.0 + 61.0 + 240.0, kayit["surus_baslangic"])
        self.assertEqual(kayit["surus_baslangic"] + ks.IKA_SURUS_SURESI_S,
                         kayit["surus_deadline"])
        self.assertNotEqual(kayit["bekleme_deadline"], kayit["surus_deadline"])
        self.assertTrue(rx.durduruldu)
        print(f"[K5] bekleme_deadline=+{ks.IKA_BEKLEME_SURESI_S:.0f}s "
              f"surus_deadline=izin+{ks.IKA_SURUS_SURESI_S:.0f}s "
              f"rota=61s izin=+240s exit={kod}")

    def test_bekleme_suresi_dolunca_1_doner_surus_baslamaz(self):
        saat = SahteSaat()
        surdu = []
        with contextlib.redirect_stdout(io.StringIO()):
            kod = ika_nav.ika_gorevi(
                "127.0.0.1:0", bekleme_suresi=5.0, saat=saat,
                rota_bekle=lambda *a, **k: None,
                izin_bekle=lambda *a, **k: True,
                sur=lambda *a, **k: surdu.append(1) or True)
        self.assertEqual(1, kod)
        self.assertEqual([], surdu)

    def test_navigate_surus_deadline_dolunca_durur_false_doner(self):
        saat = SahteSaat(0.0)
        gonderilen = []
        adim = {"n": 0}

        def sahte_pose(model="ika"):
            # her adımda hedefe 1 m yaklaş; 20 adımda ulaşır
            adim["n"] += 1
            return (min(20.0, float(adim["n"])), 0.0, 0.0, 0.0)

        def sahte_sleep(s):
            saat.ilerle(1.0)      # her kontrol turu 1 s ilerlesin

        wps = [(0.0, 0.0), (20.0, 0.0)]
        with mock.patch.object(ika_nav, "get_pose", sahte_pose), \
             mock.patch.object(ika_nav, "send_vel",
                               lambda r, l, topic=None: gonderilen.append((r, l))), \
             mock.patch.object(ika_nav.time, "sleep", sahte_sleep), \
             contextlib.redirect_stdout(io.StringIO()):
            sonuc = ika_nav.navigate(
                wps, "test", verbose=False,
                surus_deadline_monotonic=5.0, saat=saat)
        self.assertFalse(sonuc)
        self.assertEqual((0, 0), gonderilen[-1])
        self.assertLess(adim["n"], 20)   # HB'ye ulaşmadan durdu
        self.assertGreaterEqual(saat(), 5.0)
        print(f"[K5] surus deadline=5s -> durdu adim={adim['n']} son_vel="
              f"{gonderilen[-1]} sonuc={sonuc}")

    def test_navigate_deadline_yoksa_hedefe_ulasir(self):
        saat = SahteSaat(0.0)
        adim = {"n": 0}

        def sahte_pose(model="ika"):
            adim["n"] += 1
            return (min(20.0, float(adim["n"])), 0.0, 0.0, 0.0)

        with mock.patch.object(ika_nav, "get_pose", sahte_pose), \
             mock.patch.object(ika_nav, "send_vel",
                               lambda r, l, topic=None: None), \
             mock.patch.object(ika_nav.time, "sleep",
                               lambda s: saat.ilerle(1.0)), \
             contextlib.redirect_stdout(io.StringIO()):
            sonuc = ika_nav.navigate(
                [(0.0, 0.0), (20.0, 0.0)], "test", verbose=False,
                surus_deadline_monotonic=1000.0, saat=saat)
        self.assertTrue(sonuc)


# ── K6 ──────────────────────────────────────────────────────────────────────

from test_iha_inis_yayinci import KanitMav  # noqa: E402


class K6InisSonrasiHeartbeatTests(unittest.TestCase):
    def test_sozlesme_heartbeat_suresi_ika_gorev_suresi(self):
        self.assertEqual(ks.SARTNAME_IKA_GOREV_SURESI_S,
                         ks.IHA_INIS_HEARTBEAT_SURESI_S)
        self.assertLess(ks.IHA_INIS_HEARTBEAT_ARALIGI_S,
                        IkaReceiver(link=SimpleNamespace()).hb_timeout)

    def test_cli_varsayilani_sozlesmeden_gelir(self):
        args = yayinci._arg_parser().parse_args(
            ["--mavlink", "x", "--kanit-timeout", "1", "--ika", "127.0.0.1:1"])
        self.assertEqual(ks.IHA_INIS_HEARTBEAT_SURESI_S, args.heartbeat_sure)
        self.assertEqual(ks.IHA_INIS_HEARTBEAT_ARALIGI_S, args.heartbeat_aralik)

    def test_heartbeat_suresi_sahte_saatle_adet_ve_durus(self):
        """Sahte saat: 600 s süre / 0.5 s aralık → heartbeat sayısı 1200,
        süre 0 → hiç heartbeat; link.send çağrıları sayılır."""
        from protocol import decode
        for sure, beklenen in ((600.0, 1200), (0.0, 0)):
            saat = SahteSaat(0.0)
            durdur = threading.Event()

            class Tasiyici:
                def __init__(self):
                    self.hb = 0
                    self.kapandi = False

                def send(self, data, peer=None):
                    m = decode(data)
                    if m and m.get("type") == "HEARTBEAT":
                        self.hb += 1

                def recv(self):
                    return (None, None)

                def close(self):
                    self.kapandi = True

            tasiyici = Tasiyici()
            with mock.patch.object(threading.Event, "wait",
                                   lambda self, t=None: (saat.ilerle(t or 0.0)
                                                         or False)), \
                 contextlib.redirect_stdout(io.StringIO()):
                yayinci.iha_inisini_yayinla(
                    {"ika": None}, repeat=1, interval=0.01,
                    tasiyici=tasiyici, heartbeat_suresi=sure,
                    heartbeat_araligi=0.5, saat=saat)
            with self.subTest(sure=sure):
                self.assertEqual(beklenen, tasiyici.hb)
                self.assertTrue(tasiyici.kapandi)
            print(f"[K6] heartbeat_suresi={sure:.0f}s aralik=0.5s -> "
                  f"heartbeat={tasiyici.hb}")

    def test_gercek_udp_inis_sonrasi_heartbeat_surer_link_lost_olmaz(self):
        """Gerçek UDP loopback: hb_timeout=0.4 s alıcı, 1.2 s heartbeat.
        Yayıncı bittiğinde geçen süre > hb_timeout; link_lost hiç oluşmadı."""
        mav = KanitMav()
        mavutil = SimpleNamespace(mavlink=SimpleNamespace(
            MAV_LANDED_STATE_ON_GROUND=1))
        alici_link = UDPLink(bind=("127.0.0.1", 0), timeout=0.05)
        receiver = IkaReceiver(alici_link, hb_timeout=0.4)
        kayip = []
        receiver.on_link_lost = lambda: kayip.append(True)
        sonuc = {}

        def yayinci_kos():
            with mock.patch.object(
                    yayinci, "mavlink_baglantisi_ac", return_value=mav), \
                 mock.patch.object(
                    kanit, "_mavutil_al", return_value=mavutil), \
                 contextlib.redirect_stdout(io.StringIO()):
                sonuc["kod"] = yayinci.main([
                    "--mavlink", "mock:pixhawk",
                    "--kanit-timeout", "2",
                    "--heartbeat-sure", "1.2",
                    "--heartbeat-aralik", "0.05",
                    "--ika", f"127.0.0.1:{alici_link.port}",
                ])
        t = threading.Thread(target=yayinci_kos, daemon=True)
        t.start()
        try:
            import time
            t0 = time.monotonic()
            landed_t = None
            hb_gorulen = 0
            son_rx = None
            # Yayıncı canlıyken alıcıyı elle poll et; link_lost asla oluşmamalı.
            while t.is_alive():
                receiver.poll()
                if receiver.iha_landed and landed_t is None:
                    landed_t = time.monotonic()
                if receiver.last_rx != son_rx and receiver.iha_landed:
                    hb_gorulen += 1
                    son_rx = receiver.last_rx
                self.assertFalse(receiver.link_lost, "iniş sonrası link_lost!")
            t.join(5.0)
            receiver.poll()
            bitis = time.monotonic()
        finally:
            alici_link.close()
        self.assertEqual(0, sonuc.get("kod"))
        self.assertIsNotNone(landed_t)
        self.assertGreater(bitis - landed_t, receiver.hb_timeout,
                           "test anlamsız: yayıncı hb_timeout'tan kısa yaşadı")
        self.assertEqual([], kayip)
        self.assertFalse(receiver.link_lost)
        self.assertGreater(hb_gorulen, 5)
        print(f"[K6] gercek UDP: landed→bitis={bitis - landed_t:.2f}s "
              f"> hb_timeout={receiver.hb_timeout}s, heartbeat_gorulen="
              f"{hb_gorulen}, link_lost={receiver.link_lost}, exit="
              f"{sonuc['kod']}")


if __name__ == "__main__":
    unittest.main()
