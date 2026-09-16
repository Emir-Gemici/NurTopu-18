"""K4 — MAVLink TUNNEL uctan uca benzetim (results/tunel_20260916/ON_KAYIT.md §4).

⚠ BU KAPILAR YALNIZ TAKLIT MODELINI KANITLAR. `scripts/ardupilot_yonlendirici_taklit.py`
GERCEK ArduPilot DEGILDIR; yonlendirme kurallari, TX tampon boyu ve oncelik depoda
dogrulanmadi. Gercek hat hukmu K8a/K8b'dedir (INSAN gorevi, gercek donanim);
olculene dek ÖLÇÜLEMEDİ. Benzetim GECTI'si onun yerine GECMEZ.

Duzenek (her vaka kendi efemer portlariyla):
  yer TunelLink('yer','akis') <-UDP-> MP aynasi taklidi (MavproxyTaklit, GCS 255/190)
    <-UDP "TELEM1" kanal 0-> ArdupilotYonlendiriciTaklit (sysid 1, hat + tampon modeli)
    <-UDP "TELEM2" kanal 1-> MAVProxy taklidi (GCS 255/230, mavfwd)
    <-UDP-> GERCEK SeriHub(TunelLink('hava','datagram')) -UDP-> GERCEK IhaKomutAlici
    (+ sahte Pixhawk COMMAND_ACK) ve GERCEK IhaSender.
Hat: 57600 bit/s (UART 10 bit/bayt = 5760 B/s); arka plan TELEM1 1943 B/s (06 Eyl
tlog OLCUMU, SR1 oranlariyla), TELEM2 1500 B/s (HESAP, streamrate -1 + SR2).
"""
from __future__ import annotations

import contextlib
import math
import queue
import socket
import sys
import threading
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
    from pymavlink.dialects.v20 import ardupilotmega as M
except ImportError:  # pragma: no cover
    M = None

import mavlink_tunel as mt  # noqa: E402
import seri_hub  # noqa: E402
from karar_sozlesmesi import PARASUT_TEKRAR_ARALIGI_S  # noqa: E402
from link import UDPLink  # noqa: E402
from protocol import (FrameReader, ack, command, encode, heartbeat,  # noqa: E402
                      open_route, MESAJ_ACK, MESAJ_HEARTBEAT, MESAJ_OPEN_ROUTE)

if M is not None:
    import ardupilot_yonlendirici_taklit as taklit  # noqa: E402
    from ardupilot_yonlendirici_taklit import (ArdupilotYonlendiriciTaklit,  # noqa: E402
                                               Kova, MavproxyTaklit, MP_GCS_KIMLIGI,
                                               MAVPROXY_GCS_KIMLIGI, cerceve_icerik_anahtari,
                                               kayip_ozeti, kopya_kayip_ozeti)

YEREL = "127.0.0.1"
HAT_BPS = 57600
TELEM1_ARKA_PLAN_B_S = 1943      # 06 Eyl tlog olcumu (SR1 oranlari)
TELEM2_ARKA_PLAN_B_S = 1500      # HESAP (streamrate -1, SR2_POSITION=8, EXTRA3=2)
ARKA_PLAN = {0: TELEM1_ARKA_PLAN_B_S, 1: TELEM2_ARKA_PLAN_B_S}
TOHUM = 20260916
HAVA_ILK_KIMLIK = 1000
YER_ILK_KIMLIK = 30000
URETIM_TEKRAR = 4                # IhaSender/KararYayinci uretim butcesi (iha_sender.py:328)
URETIM_ARALIK_S = 0.25
AKRAN_BEKLEME_S = 4.0
TAVAN_S = 5.0


def _wp(n, a, b):
    return [[round(a * i + 0.37, 2), round(b * i + 0.91, 2)] for i in range(n)]


#: Parca sayisi test icinde assert edilir (12 wp -> 3, 30 wp -> 4, 64 wp -> 10).
ROTA_12 = _wp(12, 1.37, 0.73)
ROTA_30 = [[round(0.5 * i, 1), round(0.3 * i, 1)] for i in range(30)]
ROTA_64 = _wp(64, 11.37, 10.73)
REF_XY = [12.34, 56.78]


def _parca_sayisi(mesaj):
    return math.ceil(len(encode(mesaj)) / mt.TUNEL_PARCA_YUK_B)


class _SahteMav:
    """Donanim ucu (kalip: tests/test_faz_b_seri_hub.py): command_long_send
    kaydeder, Pixhawk gibi COMMAND_ACK ACCEPTED doner."""

    def __init__(self, kaynak_sysid):
        from pymavlink import mavutil
        self._m = mavutil.mavlink
        self.kaynak_sysid = kaynak_sysid
        self._bekleyen = []
        self._kilit = threading.Lock()

        def kaydet(sys_id, comp, mav_cmd, *_):
            with self._kilit:
                self._bekleyen.append(int(mav_cmd))

        self.mav = mock.Mock(name="mav")
        self.mav.command_long_send = mock.Mock(side_effect=kaydet)

    def recv_match(self, type=None, blocking=False, timeout=None, **_):
        with self._kilit:
            if type == "COMMAND_ACK" and self._bekleyen:
                cmd = self._bekleyen.pop(0)
                return SimpleNamespace(command=cmd, result=self._m.MAV_RESULT_ACCEPTED,
                                       get_srcSystem=lambda: self.kaynak_sysid)
        if blocking and timeout:
            time.sleep(min(float(timeout), 0.05))
        return None


def _sessiz_log(*_a, **_k):
    return None


class Duzenek:
    """Uctan uca tezgah. Bilesenler gercek; Pixhawk ve MAVProxy/MP taklit."""

    def __init__(self, test, *, kayip=0.0, tohum=TOHUM, hat_bps=HAT_BPS,
                 tx_tampon_b=1024, arka_plan=None, mavfwd=True,
                 mp_heartbeat=None if M is None else MP_GCS_KIMLIGI,
                 otomatik_rota_ack=True):
        import iha_komut_alici as alici_modul
        from iha_komut_alici import IhaKomutAlici
        self.test = test
        self.otomatik_rota_ack = otomatik_rota_ack
        self.router = ArdupilotYonlendiriciTaklit(
            2, kayip=kayip, tohum=tohum, hat_bps=hat_bps, tx_tampon_b=tx_tampon_b,
            arka_plan=ARKA_PLAN if arka_plan is None else arka_plan)
        self.yer = mt.TunelLink((YEREL, 0), mt.KIMLIK_YER, timeout=0.05,
                                ilk_kimlik=YER_ILK_KIMLIK, log=_sessiz_log)
        self.hava = mt.TunelLink((YEREL, 0), mt.KIMLIK_HAVA, timeout=0.02,
                                 ilk_kimlik=HAVA_ILK_KIMLIK, log=_sessiz_log)
        self.mp = MavproxyTaklit(self.router.kanal_adresi(0),
                                 [(YEREL, self.yer.port)], heartbeat=mp_heartbeat)
        self.mavproxy = MavproxyTaklit(self.router.kanal_adresi(1),
                                       [(YEREL, self.hava.port)], mavfwd=mavfwd,
                                       heartbeat=MAVPROXY_GCS_KIMLIGI)
        self.router.kanal_bagla(0, self.mp.master_adresi)
        self.router.kanal_bagla(1, self.mavproxy.master_adresi)
        self.sysid = alici_modul.VARSAYILAN_HEDEF_SYSID
        self.mav = _SahteMav(self.sysid)
        self.alici_link = UDPLink(bind=(YEREL, 0), timeout=0.05)
        self.alici = IhaKomutAlici(self.alici_link, self.mav, target_system=self.sysid)
        self.dinleyici = UDPLink(bind=(YEREL, 0), timeout=0.02)
        self.hub_udp = UDPLink(bind=(YEREL, 0), timeout=0.001, reuse=False)
        self.hub_log = []
        self._yamalar = [mock.patch.object(seri_hub.SeriHub, "_logla",
                                           lambda s, m, kirmizi=False: self.hub_log.append((m, kirmizi))),
                         mock.patch.object(IhaKomutAlici, "_logla",
                                           lambda s, m, kirmizi=False: None)]
        for y in self._yamalar:
            y.start()
        self.hub = seri_hub.SeriHub(self.hava, self.hub_udp,
                                    [(YEREL, self.alici_link.port), (YEREL, self.dinleyici.port)],
                                    log_aralik_s=0)
        self.hub_adr = self.hub_udp.sock.getsockname()
        self.yer_gelen = queue.Queue()
        self.hava_dinleyici_gelen = queue.Queue()
        self.yer_bozuk = 0
        self._dur = threading.Event()
        self.iplikler = []
        self.router.baslat()
        self.mp.baslat()
        self.mavproxy.baslat()
        for hedef in (self.hub.calistir, self.alici.calistir, self._yer_dongu,
                      self._dinleyici_dongu):
            t = threading.Thread(target=hedef, daemon=True)
            t.start()
            self.iplikler.append(t)
        test.addCleanup(self.kapat)

    # ── dongular ─────────────────────────────────────────────────────────
    def _yer_dongu(self):
        okuyucu = FrameReader()
        while not self._dur.is_set():
            try:
                veri, _ = self.yer.recv()
            except OSError:
                return
            if veri is None:
                continue
            t = time.monotonic()
            mesajlar = list(okuyucu.feed(veri))
            self.yer_bozuk += veri.count(b"\n") - len(mesajlar)
            for m in mesajlar:
                self.yer_gelen.put((t, m))
                if (self.otomatik_rota_ack and isinstance(m, dict)
                        and m.get("type") == MESAJ_OPEN_ROUTE):
                    self.yer.send(encode(ack(m["seq"], "yks", MESAJ_OPEN_ROUTE)))

    def _dinleyici_dongu(self):
        while not self._dur.is_set():
            try:
                veri, _ = self.dinleyici.recv(65535)
            except OSError:
                return
            if veri:
                t = time.monotonic()
                for m in FrameReader().feed(veri):
                    self.hava_dinleyici_gelen.put((t, m))

    # ── yardimcilar ──────────────────────────────────────────────────────
    def akran_bekle(self):
        bitis = time.monotonic() + AKRAN_BEKLEME_S
        while time.monotonic() < bitis:
            if self.hava.akran is not None and self.yer.akran is not None:
                return True
            time.sleep(0.02)
        return False

    def yer_bekle(self, kosul, tavan_s=TAVAN_S):
        bitis = time.monotonic() + tavan_s
        while time.monotonic() < bitis:
            try:
                t, m = self.yer_gelen.get(timeout=0.05)
            except queue.Empty:
                continue
            if isinstance(m, dict) and kosul(m):
                return t, m
        return None, None

    def yks_komut_ack(self, seq, tavan_s=TAVAN_S, aralik_s=PARASUT_TEKRAR_ARALIGI_S):
        """YKS gibi: ACK gelene dek PARACHUTE'u tekrar et; ACK ani (s) ya da None."""
        t0 = time.monotonic()
        cerceve = encode(command("PARACHUTE", "iha", seq=seq))
        while time.monotonic() - t0 < tavan_s:
            self.yer.send(cerceve)
            t, m = self.yer_bekle(lambda m: m.get("type") == MESAJ_ACK and m.get("ref") == seq
                                  and m.get("node") == "iha", tavan_s=aralik_s)
            if m is not None:
                return t - t0, m
        return None, None

    def rota_denemeleri(self, rota, adet, repeat=URETIM_TEKRAR, interval=URETIM_ARALIK_S,
                        once=None):
        from iha_sender import IhaSender
        link = UDPLink(bind=(YEREL, 0), timeout=0.05)
        try:
            gonderen = IhaSender(link, peers={"yks": self.hub_adr})
            sonuc = []
            for _ in range(adet):
                if once is not None:
                    once(link)
                _seq, acked = gonderen.send_open_route(2, 0.9, rota, REF_XY,
                                                       repeat=repeat, interval=interval)
                sonuc.append("yks" in acked)
            return sonuc
        finally:
            link.close()

    def kapat(self):
        self._dur.set()
        self.hub.durdur()
        self.alici.durdur()
        for t in self.iplikler:
            t.join(timeout=2.0)
        self.mp.durdur()
        self.mavproxy.durdur()
        self.router.durdur()
        for ln in (self.yer, self.hava, self.alici_link, self.dinleyici, self.hub_udp):
            try:
                ln.close()
            except OSError:
                pass
        for y in self._yamalar:
            y.stop()


def _yuzdelik(degerler, p):
    s = sorted(degerler)
    return s[max(0, min(len(s) - 1, math.ceil(p / 100.0 * len(s)) - 1))]


@unittest.skipIf(M is None, "pymavlink kurulu degil")
class K4_01_YonlendiriciKurallari(unittest.TestCase):
    def _router(self, **kw):
        r = ArdupilotYonlendiriciTaklit(3, **kw)
        self.addCleanup(r.durdur)
        socks = []
        for k in range(3):
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.bind((YEREL, 0))
            s.settimeout(0.3)
            self.addCleanup(s.close)
            r.kanal_bagla(k, s.getsockname())
            socks.append(s)
        return r, socks

    @staticmethod
    def _topla(s, sure_s=0.4):
        bitis = time.monotonic() + sure_s
        tipler = []
        s.settimeout(0.05)
        a = M.MAVLink(None)
        a.robust_parsing = True
        while time.monotonic() < bitis:
            try:
                veri, _ = s.recvfrom(65535)
            except socket.timeout:
                continue
            tipler += [(m.get_type(), m.get_srcSystem()) for m in (a.parse_buffer(veri) or [])]
        return tipler

    def test_K4_01a_kurallar_heartbeat_yayin_hedefli_yerel(self):
        r, (a, b, c) = self._router(heartbeat_aralik_s=3600)
        r.baslat()
        time.sleep(0.1)
        for s in (a, b, c):
            self._topla(s, 0.1)                       # router'in kendi heartbeat'i
        gcs = M.MAVLink(None, srcSystem=255, srcComponent=190)
        a.sendto(gcs.heartbeat_encode(M.MAV_TYPE_GCS, 8, 0, 0, 0).pack(gcs), r.kanal_adresi(0))
        ta, tb, tc = (self._topla(s) for s in (a, b, c))
        self.assertIn(("HEARTBEAT", 255), tb)
        self.assertIn(("HEARTBEAT", 255), tc)
        self.assertNotIn(("HEARTBEAT", 255), ta, "gelen kanala geri GONDERILMEZ")
        tun = M.MAVLink(None, srcSystem=mt.TUNEL_SYSID, srcComponent=mt.TUNEL_HAVA_COMPID)
        p = mt.parcalara_bol(1, b"x\n")[0]
        b.sendto(tun.tunnel_encode(0, 0, mt.TUNEL_PAYLOAD_TYPE, len(p),
                                   p + bytes(128 - len(p))).pack(tun), r.kanal_adresi(1))
        ta, tb, tc = (self._topla(s) for s in (a, b, c))
        self.assertIn(("TUNNEL", mt.TUNEL_SYSID), ta, "rotasi olan kanala (A: 255) yayin")
        self.assertNotIn(("TUNNEL", mt.TUNEL_SYSID), tc, "rotasiz kanala (C) yayin YOK")
        self.assertNotIn(("TUNNEL", mt.TUNEL_SYSID), tb)
        cmd = M.MAVLink(None, srcSystem=42, srcComponent=1)
        c.sendto(cmd.command_long_encode(255, 190, 400, 0, 0, 0, 0, 0, 0, 0, 0).pack(cmd),
                 r.kanal_adresi(2))
        ta, tb, tc = (self._topla(s) for s in (a, b, c))
        self.assertIn(("COMMAND_LONG", 42), ta, "hedefli: yalniz 255'in kanali")
        self.assertNotIn(("COMMAND_LONG", 42), tb)
        yerel0 = r.sayac["yerel"]
        c.sendto(cmd.command_long_encode(1, 1, 400, 0, 0, 0, 0, 0, 0, 0, 0).pack(cmd),
                 r.kanal_adresi(2))
        ta, tb = self._topla(a), self._topla(b)
        self.assertEqual(yerel0 + 1, r.sayac["yerel"])
        self.assertNotIn(("COMMAND_LONG", 42), ta + tb, "kendi sysid'ine hedefli iletilmez")
        r.sifirla()
        self.assertEqual({}, r.rotalar)

    def test_K4_01b_kova_hiz_ve_tampon_saf(self):
        k = Kova(bps_b=100, tampon_b=150)
        self.assertTrue(k.ekle(0.0, b"x" * 50))
        self.assertTrue(k.ekle(0.0, b"y" * 50))
        self.assertFalse(k.ekle(0.0, b"z" * 60), "txspace < len -> dusmeli")
        self.assertEqual([], k.hazirlar(0.49))
        self.assertEqual([b"x" * 50], k.hazirlar(0.5))
        self.assertEqual([b"y" * 50], k.hazirlar(1.0))
        self.assertEqual(150, k.txspace(1.0))
        # bayt duzeyi: dokulmekte olan paketin gonderilen kismi tampondan cikar
        k2 = Kova(bps_b=100, tampon_b=100)
        self.assertTrue(k2.ekle(0.0, b"a" * 100))
        self.assertAlmostEqual(50.0, k2.txspace(0.5))
        self.assertTrue(k2.ekle(0.5, b"b" * 50))
        self.assertFalse(k2.ekle(0.5, b"c" * 1))

    def test_K4_01c_hat_ve_arka_plan_hizi_gercek_zamanda_yuzde_10(self):
        hedef = 1000.0
        r, (a, _b, _c) = self._router(hat_bps=HAT_BPS, arka_plan={0: hedef},
                                      heartbeat_aralik_s=3600)
        r.baslat()
        time.sleep(0.3)
        a.settimeout(0.0)
        with contextlib.suppress(OSError):
            while True:                       # uyku sirasinda biriken backlog olcume girmesin
                a.recvfrom(65535)
        a.settimeout(0.05)
        bayt = 0
        t0 = time.monotonic()
        while time.monotonic() - t0 < 2.0:
            try:
                veri, _ = a.recvfrom(65535)
            except socket.timeout:
                continue
            bayt += len(veri)
        hiz = bayt / (time.monotonic() - t0)
        self.assertLess(abs(hiz - hedef) / hedef, 0.10, f"arka plan {hiz:.0f} B/s")
        # kova hat hizinda bosalir: 57600 bit/s -> 5760 B/s, 2 s'lik doldurma
        k = Kova(bps_b=HAT_BPS / taklit.UART_BIT_PER_BAYT)
        paket = b"p" * 144
        for _ in range(80):
            k.ekle(0.0, paket)
        son = k.kuyruk[-1][0]
        self.assertLess(abs(80 * 144 / son - 5760) / 5760, 0.10)
        r2 = ArdupilotYonlendiriciTaklit(2, hat_bps=HAT_BPS, tx_tampon_b=100)
        self.addCleanup(r2.durdur)
        r2.kanal_bagla(0, ("127.0.0.1", 9))
        r2.rotalar[255] = {0}
        tun = M.MAVLink(None, srcSystem=mt.TUNEL_SYSID, srcComponent=mt.TUNEL_HAVA_COMPID)
        p = mt.parcalara_bol(1, b"x" * 123)[0]
        r2._yonlendir(1, tun.tunnel_encode(0, 0, mt.TUNEL_PAYLOAD_TYPE, len(p), p).pack(tun),
                      time.monotonic())
        self.assertEqual(1, r2.sayac["txspace_dusen"])

    def test_K4_01d_kayip_ozetleri_saf_belirlenimci(self):
        basliklar = [mt.parcalara_bol(k, b"x" * 300)[i] for k in range(400) for i in range(3)]
        r1 = ArdupilotYonlendiriciTaklit(2, kayip=0.05, tohum=TOHUM)
        r2 = ArdupilotYonlendiriciTaklit(2, kayip=0.05, tohum=TOHUM)
        r3 = ArdupilotYonlendiriciTaklit(2, kayip=0.05, tohum=TOHUM + 1)
        for r in (r1, r2, r3):
            self.addCleanup(r.durdur)
        # Kayitsiz parca -> YEDEK baslik ozeti; gorunur sayilir.
        k1 = [r1.kayip_mi(0, 1, b) for b in basliklar]
        self.assertEqual(len(basliklar), r1.sayac["kayip_anahtari_eksik"])
        self.assertEqual(k1, [r2.kayip_mi(0, 1, b) for b in basliklar], "ayni payload ayni karar")
        self.assertNotEqual(k1, [r3.kayip_mi(0, 1, b) for b in basliklar])
        self.assertNotEqual(k1, [r1.kayip_mi(1, 0, b) for b in basliklar], "yon ozete girer")
        oran = sum(k1) / len(k1)
        self.assertLess(abs(oran - 0.05), 0.02, oran)
        self.assertEqual(kayip_ozeti(1, 0, 1, basliklar[0][:5] + b"a"),
                         kayip_ozeti(1, 0, 1, basliklar[0][:5] + b"b"))
        # Kopya ozeti: her anahtar alani karara girer, oran ~kayip.
        taban = kopya_kayip_ozeti(TOHUM, 0, 1, 3, 1, 0, 4)
        for degisik in ((TOHUM + 1, 0, 1, 3, 1, 0, 4), (TOHUM, 1, 0, 3, 1, 0, 4),
                        (TOHUM, 0, 1, 4, 1, 0, 4), (TOHUM, 0, 1, 3, 2, 0, 4),
                        (TOHUM, 0, 1, 3, 1, 1, 4)):
            self.assertNotEqual(taban, kopya_kayip_ozeti(*degisik), degisik)
        degerler = [kopya_kayip_ozeti(TOHUM, 0, 1, n, c, i, 4)
                    for n in range(100) for c in range(1, 5) for i in range(4)]
        self.assertLess(abs(sum(d < 0.05 for d in degerler) / len(degerler) - 0.05), 0.02)
        # zaman damgasi normallestirilir; seq/ref KORUNUR
        a = encode(open_route(2, 0.9, ROTA_12, REF_XY, seq=7))
        b = a.replace(b'"t":', b'"t":1', 1)
        self.assertNotEqual(a, b)
        self.assertEqual(cerceve_icerik_anahtari(a), cerceve_icerik_anahtari(b))
        self.assertNotEqual(cerceve_icerik_anahtari(a),
                            cerceve_icerik_anahtari(encode(open_route(2, 0.9, ROTA_12, REF_XY, seq=8))))

    def test_K4_01e_kayip_karari_kimlikten_ve_kopya_sayisindan_BAGIMSIZ(self):
        """DUZELTME TURU 1 (curutucu olcumu: 1024 B alt vakasi 4 kosuda 3 DUSTU).
        Iki 'kosu': farkli baslangic kimligi, farkli seq tabani, farkli `t` ve
        denemeler arasinda FARKLI kopya sayisi (ACK zamanlamasi). Var olan her
        (deneme, kopya, parca) icin kayip karari AYNI olmali. Eski baslik ozeti
        (kimlik dahil) bu kosulda farkli karar verir (pozitif kontrol)."""
        kayip = 0.3

        def kosu(ilk_kimlik, seq_tabani, t_eki, kopya_sayisi):
            r = ArdupilotYonlendiriciTaklit(2, kayip=kayip, tohum=TOHUM)
            self.addCleanup(r.durdur)
            kimlik = ilk_kimlik
            kararlar, eski_kararlar = {}, {}
            for deneme in range(12):
                cerceve = encode(open_route(2, 0.9, ROTA_30, REF_XY, seq=seq_tabani + deneme))
                cerceve = cerceve.replace(b'"t":', b'"t":' + t_eki, 1)
                for kopya in range(1, kopya_sayisi(deneme) + 1):
                    parcalar = [p + bytes(mt.TUNEL_MAVLINK_YUK_B - len(p))
                                for p in mt.parcalara_bol(kimlik, cerceve)]
                    kimlik += 1
                    for p in parcalar:
                        r.parca_kaydet(0, p)
                    for indis, p in enumerate(parcalar):
                        kararlar[(deneme, kopya, indis)] = r.kayip_mi(0, 1, p)
                        eski_kararlar[(deneme, kopya, indis)] = (
                            kayip_ozeti(TOHUM, 0, 1, p) < kayip)
            self.assertEqual(0, r.sayac["kayip_anahtari_eksik"])
            return kararlar, eski_kararlar
        k1, e1 = kosu(HAVA_ILK_KIMLIK, 100, b"1", lambda d: 1 + d % 4)
        k2, e2 = kosu(51234, 9000, b"7", lambda d: 4)
        ortak = sorted(set(k1) & set(k2))
        self.assertGreater(len(ortak), 60)
        self.assertEqual({a: k1[a] for a in ortak}, {a: k2[a] for a in ortak})
        self.assertGreater(sum(k1.values()), 0, "kayip hic yok: test ayirt edemez")
        self.assertNotEqual({a: e1[a] for a in ortak}, {a: e2[a] for a in ortak},
                            "pozitif kontrol: kimlige bagli eski ozet farkli karar vermeli")
        # eksik parca -> yedek ozet, GORUNUR sayac
        r = ArdupilotYonlendiriciTaklit(2, kayip=kayip, tohum=TOHUM)
        self.addCleanup(r.durdur)
        parcalar = mt.parcalara_bol(5, encode(open_route(2, 0.9, ROTA_30, REF_XY, seq=1)))
        r.parca_kaydet(0, parcalar[0])
        r.kayip_mi(0, 1, parcalar[0])
        self.assertEqual(1, r.sayac["kayip_anahtari_eksik"])


@unittest.skipIf(M is None, "pymavlink kurulu degil")
class K4UctanUca(unittest.TestCase):
    def test_K4_02_parachute_ack_zinciri_hat_ve_arka_plan_acik(self):
        d = Duzenek(self)
        self.assertTrue(d.akran_bekle(), "akranlar arac heartbeat'iyle ogrenilmedi")
        sure, m = d.yks_komut_ack(41)
        self.assertIsNotNone(m, f"ACK gelmedi; router={d.router.sayac} hava={d.hava.sayac} "
                                f"yer={d.yer.sayac} hub={d.hub.sayac}")
        self.assertEqual("CMD", m.get("ref_tip"))
        self.assertEqual("PARACHUTE", m.get("ref_cmd"))
        d.mav.mav.command_long_send.assert_called()
        self.assertEqual(M.MAV_CMD_DO_PARACHUTE, d.mav.mav.command_long_send.call_args[0][2])
        self.assertEqual(0, d.hub.sayac["dusurulen"])
        self.assertEqual(0, d.hub.sayac["bozuk"])
        self.assertEqual(0, d.yer_bozuk)
        print(f"\n[K4_02] ACK {sure * 1000:.0f} ms · router={d.router.sayac}")

    def _rota_alt_vakasi(self, kayip, tampon):
        d = Duzenek(self, kayip=kayip, tx_tampon_b=tampon)
        self.assertTrue(d.akran_bekle())
        self.assertEqual(3, _parca_sayisi(open_route(2, 0.9, ROTA_12, REF_XY, seq=100)))
        self.assertEqual(4, _parca_sayisi(open_route(2, 0.9, ROTA_30, REF_XY, seq=100)))
        s12 = d.rota_denemeleri(ROTA_12, 20)
        s30 = d.rota_denemeleri(ROTA_30, 20)
        ozet = (f"kayip={kayip} tampon={tampon}: 12wp {sum(s12)}/20 · 30wp {sum(s30)}/20 · "
                f"router={d.router.sayac} yer={{zaman_asimi_dusen: {d.yer.sayac['zaman_asimi_dusen']}, "
                f"kimlik_boslugu: {d.yer.sayac['kimlik_boslugu']}}} hava={{kimlik_boslugu: "
                f"{d.hava.sayac['kimlik_boslugu']}, zaman_asimi_dusen: {d.hava.sayac['zaman_asimi_dusen']}}}")
        print(f"\n[K4_03/04] {ozet}")
        return s12 + s30, ozet

    def _k4_03_04(self, tampon):
        for kayip in (0.0, 0.05):
            with self.subTest(kayip=kayip, tampon=tampon):
                sonuc, ozet = self._rota_alt_vakasi(kayip, tampon)
                self.assertEqual(40, sum(sonuc), f"K4 DUSTU: {ozet}")

    def test_K4_03_K4_04_tampon_256_ZORUNLU(self):
        """On kayit: `_K4_03_K4_04_ON_KAYIT` dokstringi (alt vaka: TX tampon 256 B)."""
        self._k4_03_04(256)

    def test_K4_03_K4_04_tampon_1024_ZORUNLU(self):
        """On kayit: `_K4_03_K4_04_ON_KAYIT` dokstringi (alt vaka: TX tampon 1024 B)."""
        self._k4_03_04(1024)

    def _K4_03_K4_04_ON_KAYIT(self):
        """ON KAYIT (sonuc gorulmeden yazildi, 16 Eylul):
          * tohum 20260916; hava ilk_kimlik 1000, yer ilk_kimlik 30000 (enjekte);
            kayip karari icerik ozetiyle (NAVITAS 5 B basligi) — belirlenimci;
          * 20 deneme 12 wp (3 parca) + 20 deneme 30 wp (4 parca); uretim butcesi
            IhaSender repeat=4, interval=0,25 s; hat modeli ACIK (57600, arka plan
            TELEM1 1943 / TELEM2 1500 B/s);
          * alt vakalar: tampon 256 B ve 1024 B, her biri %0 ve %5 kayipla;
          * KAPI: her alt vakada 40/40 ACK (ON_KAYIT K4 "alinir (zorunlu)"; gevsetilmez);
          * analitik (bagimsizlik varsayimi, zamanlama etkisi yok): %5'te kopya basari
            q = 0,95^(p+1) -> p=3: 0,8145, p=4: 0,7738; 4 kopyanin hepsi duser
            (1-q)^4 = 0,00119 / 0,00263; 20+20 denemenin hepsi gecer
            ≈ 0,9765 x 0,9487 ≈ %92,6 (alt vaka); iki tampon alt vakasi birlikte
            ≈ %85,8. Son kopyanin 0,25 s penceresi uzun rotada ACK'e yetmeyebilir;
            gercek olasilik biraz daha dusuktur;
          * DUSERSE: DUSTU yazilir; tohum ve deneme sayisi DEGISTIRILMEZ.
        (Iki alt vaka ayri test yontemlerine bolundu — hangi tamponun dustugu
        adiyla gorunsun; kapi ve parametreler AYNI.)

        SAPMA — DUZELTME TURU 1 (16 Eylul; yukaridaki metin DEGISTIRILMEDI):
          * curutucu olcumu: "kayip karari icerik ozetiyle (5 B baslik) —
            belirlenimci" iddiasi YANLISTI. Baslik kimligi icerir; kimlik her
            gonderilen kopyada artar ve kopya sayisi ACK zamanlamasina baglidir.
            Degismemis kodda 1024 B alt vakasi 4 kosuda 3 DUSTU, 1 GECTI
            (kayip_dusen 12/12/11/6).
          * duzeltme: kayip anahtari (ileti_no, kopya_no, indis, toplam); kayip
            TX'ten hatta cikista uygulanir (scripts/ardupilot_yonlendirici_taklit.py
            dokstringi). Kilit: K4_01e.
          * DEGISMEYEN: kapi 40/40, tohum 20260916, 20+20 deneme, uretim butcesi
            (repeat=4, interval=0,25 s), hat modeli, iki tampon alt vakasi.
          * belirlenimci OLMAYAN kalan bilesen: hat/kuyruk gercek saatle isler
            (txspace_dusen, son kopyanin ACK penceresi). Bu yuzden alt vaka N kez
            kosulur ve dagilim raporlanir (results/tunel_20260916/duzeltme_t1.txt).
          * analitik %92,6 olasiligi artik tek kosunun degil, TOHUMUN kaderidir:
            ayni tohumla sonuc (zamanlama disinda) sabittir."""

    def test_K4_05_yuzde_20_kayip_RAPOR(self):
        d = Duzenek(self, kayip=0.20, tx_tampon_b=1024)
        self.assertTrue(d.akran_bekle())
        s12 = d.rota_denemeleri(ROTA_12, 10)
        s30 = d.rota_denemeleri(ROTA_30, 10)
        print(f"\n[K4_05 RAPOR] %20 kayip: 12wp {sum(s12)}/10 · 30wp {sum(s30)}/10 · "
              f"txspace_dusen={d.router.sayac['txspace_dusen']} kayip_dusen="
              f"{d.router.sayac['kayip_dusen']} yer_kimlik_boslugu={d.yer.sayac['kimlik_boslugu']} "
              f"yer_zaman_asimi={d.yer.sayac['zaman_asimi_dusen']} hava_kimlik_boslugu="
              f"{d.hava.sayac['kimlik_boslugu']} hava_zaman_asimi={d.hava.sayac['zaman_asimi_dusen']}")

    def test_K4_06_gecikme_p95_iki_yonde_hat_modeli_acik(self):
        """ON KAYIT: Bu kapi yalniz taklit modelinde (hat hizi + tampon + loopback)
        gecikme butcesini sinar; gercek hat gecikmesi hakkinda hukum K8a/K8b'dedir.
        n=30 her yon; tek parcali HEARTBEAT; kapi p95 < PARASUT_TEKRAR_ARALIGI_S.
        HESAP karsilastirmasi (arayuz tablosu): 1 parca tel ~106 B -> UART sekmesi
        ~18 ms; taklitte yon basina 2 hiz sinirli sekme (RX + TX) + arka plan."""
        d = Duzenek(self)
        self.assertTrue(d.akran_bekle())
        kaynak = UDPLink(bind=(YEREL, 0), timeout=0.02)
        self.addCleanup(kaynak.close)
        hava_yer, yer_hava = [], []
        for i in range(30):
            t0 = time.monotonic()
            kaynak.send(encode(heartbeat("iha", seq=5000 + i)), d.hub_adr)
            t, m = d.yer_bekle(lambda m, i=i: m.get("type") == MESAJ_HEARTBEAT
                               and m.get("seq") == 5000 + i, tavan_s=2.0)
            self.assertIsNotNone(m, f"hava->yer {i} kayboldu")
            hava_yer.append(t - t0)
            t0 = time.monotonic()
            d.yer.send(encode(heartbeat("ika", seq=6000 + i)))
            bitis = t0 + 2.0
            geldi = None
            while time.monotonic() < bitis and geldi is None:
                try:
                    t, m = d.hava_dinleyici_gelen.get(timeout=0.05)
                except queue.Empty:
                    continue
                if m.get("seq") == 6000 + i:
                    geldi = t
            self.assertIsNotNone(geldi, f"yer->hava {i} kayboldu")
            yer_hava.append(geldi - t0)
        ozet = (f"hava->yer p50={_yuzdelik(hava_yer, 50) * 1000:.0f} p95={_yuzdelik(hava_yer, 95) * 1000:.0f} ms · "
                f"yer->hava p50={_yuzdelik(yer_hava, 50) * 1000:.0f} p95={_yuzdelik(yer_hava, 95) * 1000:.0f} ms · "
                f"HESAP 2x18 ms UART + arka plan · kapi {PARASUT_TEKRAR_ARALIGI_S * 1000:.0f} ms")
        print(f"\n[K4_06] {ozet}")
        self.assertLess(_yuzdelik(hava_yer, 95), PARASUT_TEKRAR_ARALIGI_S, ozet)
        self.assertLess(_yuzdelik(yer_hava, 95), PARASUT_TEKRAR_ARALIGI_S, ozet)

    def test_K4_07_pixhawk_reboot_rota_silinir_toparlanir_kayip_gorunur(self):
        d = Duzenek(self)
        self.assertTrue(d.akran_bekle())
        # 1) reboot; hava trafigi YOK — yayin (0/0) MAVProxy GCS heartbeat'iyle
        #    ogrenilen rotadan gecer. Hedefli adres (M9) burada kilitlenirdi.
        d.router.sifirla(kesinti_s=0.3)
        sure, m = d.yks_komut_ack(77, tavan_s=3.0)
        self.assertIsNotNone(m, f"reboot sonrasi 3 s icinde ACK yok: router={d.router.sayac}")
        # 2) surekli hava trafigi varken reboot: yer tarafi kaybi GORUR
        kaynak = UDPLink(bind=(YEREL, 0), timeout=0.02)
        self.addCleanup(kaynak.close)
        dur = threading.Event()

        def hava_akisi():
            i = 0
            while not dur.is_set():
                kaynak.send(encode(heartbeat("iha", seq=7000 + i)), d.hub_adr)
                i += 1
                time.sleep(0.1)
        t = threading.Thread(target=hava_akisi, daemon=True)
        t.start()
        time.sleep(0.5)
        d.router.sifirla(kesinti_s=0.5)
        time.sleep(2.5)
        dur.set()
        t.join(2.0)
        time.sleep(0.8)
        s = d.yer.sayac
        print(f"\n[K4_07] ACK {sure * 1000:.0f} ms · yer kimlik_boslugu={s['kimlik_boslugu']} "
              f"zaman_asimi_dusen={s['zaman_asimi_dusen']} · router={d.router.sayac}")
        self.assertGreater(s["kimlik_boslugu"] + s["zaman_asimi_dusen"], 0)

    def test_K4_08_mavproxy_yeniden_baslar_akran_yalniz_arac_heartbeatiyle(self):
        d = Duzenek(self)
        self.assertTrue(d.akran_bekle())
        eski = d.hava.akran
        self.assertEqual(eski, (YEREL, d.mavproxy.cikis_adresi(0)[1]))
        d.mavproxy.yeniden_baslat()
        d.router.kanal_bagla(1, d.mavproxy.master_adresi)
        sure, m = d.yks_komut_ack(88, tavan_s=4.0)
        self.assertIsNotNone(m, f"MAVProxy yeniden basladiktan sonra ACK yok: hava={d.hava.sayac}")
        self.assertEqual(1, d.hava.sayac["akran_degisti"])
        self.assertEqual((YEREL, d.mavproxy.cikis_adresi(0)[1]), d.hava.akran)
        self.assertEqual(0, d.hub.sayac["seri_ariza"])
        print(f"\n[K4_08] ACK {sure * 1000:.0f} ms · hava={d.hava.sayac}")

    def test_K4_09_mp_heartbeati_yokken_yayin_ulasmaz_rota_ogrenilince_ulasir(self):
        d = Duzenek(self, mp_heartbeat=None)
        bitis = time.monotonic() + AKRAN_BEKLEME_S
        while d.hava.akran is None and time.monotonic() < bitis:
            time.sleep(0.02)
        self.assertIsNotNone(d.hava.akran)
        kaynak = UDPLink(bind=(YEREL, 0), timeout=0.02)
        self.addCleanup(kaynak.close)
        for i in range(8):
            kaynak.send(encode(heartbeat("iha", seq=9000 + i)), d.hub_adr)
            time.sleep(0.15)
        _, m = d.yer_bekle(lambda m: m.get("type") == MESAJ_HEARTBEAT, tavan_s=0.5)
        self.assertIsNone(m, "kanal 0'da rota yokken yayin ULASMAMALI")
        self.assertGreater(d.router.sayac["hedefsiz"], 0)
        d.mp.heartbeat_ayarla(MP_GCS_KIMLIGI)
        geldi = None
        bitis = time.monotonic() + 3.0
        i = 100
        while geldi is None and time.monotonic() < bitis:
            kaynak.send(encode(heartbeat("iha", seq=9000 + i)), d.hub_adr)
            i += 1
            _, geldi = d.yer_bekle(lambda m: m.get("type") == MESAJ_HEARTBEAT, tavan_s=0.2)
        self.assertIsNotNone(geldi, "MP heartbeat'iyle rota ogrenilince yayin ULASMALI")

    def test_K4_10_PATLAMA_rapor_ve_zorunlu_asgari(self):
        """ON KAYIT: TELEM1 arka plan 1943 B/s, tampon 256 B; 1172 B'a yakin
        OPEN_ROUTE (64 wp, 10 parca) ile ayni anda HEARTBEAT (3 parca), 20 deneme,
        uretim tekrar butcesi. RAPOR: ACK orani, txspace_dusen, kimlik_boslugu.
        ZORUNLU ASGARI: surecler canli, bozuk teslim 0, dusen her cerceve sayaclarin
        en az birinde gorunur (sum dusen <= zaman_asimi_dusen + kimlik_boslugu).
        Basari orani kapi DEGILDIR."""
        d = Duzenek(self, tx_tampon_b=256)
        self.assertTrue(d.akran_bekle())
        self.assertEqual(10, _parca_sayisi(open_route(2, 0.9, ROTA_64, REF_XY, seq=100)))
        hb = heartbeat("iha", seq=1, x=12.345, y=67.891, alt=31.25, hiz=4.56, yon=123.4,
                       bat=15.87, bat_yuzde=87, uydu=14, karar_yas=0.35, lat=37.7651234,
                       lon=38.2771234, gps_fix=3, armed=True, mod="GUIDED", pixhawk_canli=True)
        self.assertEqual(3, _parca_sayisi(hb))
        gonderilen0 = d.hava.sayac["gonderilen_cerceve"]
        teslim0 = d.yer.sayac["teslim_cerceve"]
        sayac = {"i": 0}

        def once(link):
            sayac["i"] += 1
            hb["seq"] = 20000 + sayac["i"]
            link.send(encode(hb), d.hub_adr)
        sonuc = d.rota_denemeleri(ROTA_64, 20, once=once)
        kaynak = UDPLink(bind=(YEREL, 0), timeout=0.02)
        self.addCleanup(kaynak.close)
        time.sleep(1.0)
        kaynak.send(encode(heartbeat("iha", seq=29999)), d.hub_adr)   # son kimligi gorunur kil
        d.yer_bekle(lambda m: m.get("seq") == 29999, tavan_s=3.0)
        time.sleep(mt.TUNEL_BIRLESTIRME_ZAMAN_ASIMI_S + 0.3)
        gonderilen = d.hava.sayac["gonderilen_cerceve"] - gonderilen0
        teslim = d.yer.sayac["teslim_cerceve"] - teslim0
        s = d.yer.sayac
        dusen = gonderilen - teslim
        print(f"\n[K4_10 RAPOR] ACK {sum(sonuc)}/20 · hava gonderilen={gonderilen} yer teslim={teslim} "
              f"dusen={dusen} · yer zaman_asimi_dusen={s['zaman_asimi_dusen']} "
              f"kimlik_boslugu={s['kimlik_boslugu']} eszamanli_tavan={s['eszamanli_tavan_dusen']} · "
              f"txspace_dusen={d.router.sayac['txspace_dusen']} · yer->hava hava.kimlik_boslugu="
              f"{d.hava.sayac['kimlik_boslugu']}")
        self.assertTrue(all(t.is_alive() for t in d.iplikler), "surecler canli olmali")
        self.assertTrue(d.router._iplik.is_alive() and d.mp._iplik.is_alive()
                        and d.mavproxy._iplik.is_alive())
        self.assertEqual(0, d.yer_bozuk, "bozuk teslim olmamali")
        self.assertEqual(0, d.hub.sayac["bozuk"])
        self.assertLessEqual(dusen, s["zaman_asimi_dusen"] + s["kimlik_boslugu"],
                             "dusen cerceve sayaclarda GORUNMUYOR")

    def test_K4_11_mavfwd_kapaliysa_hava_yer_kesilir_yer_hava_suruyor(self):
        """SAPMA (sartname K4_11 yonu TERS yazmisti; olculdu): hub'in TunelLink'i
        MAVProxy'nin `--out` ucundadir. `mavfwd` MAVProxy'de CIKISTAN gelenin
        master'a yazilmasini yonetir (mavproxy.py:898-903) — bu HAVA->YER
        yonudur (ACK, OPEN_ROUTE, HEARTBEAT). Master'dan (Pixhawk) gelen her sey
        cikislara mavfwd'den BAGIMSIZ yazilir: YER->HAVA PARACHUTE hava
        tuketicisine ULASIR, ama ACK'i yere DONMEZ. Ilk kosuda sartname yonuyle
        yazilan vaka DUSTU (alici cmd=6)."""
        d = Duzenek(self, mavfwd=False)
        bitis = time.monotonic() + AKRAN_BEKLEME_S
        while (d.hava.akran is None or d.yer.akran is None) and time.monotonic() < bitis:
            time.sleep(0.02)
        self.assertIsNotNone(d.hava.akran)
        self.assertIsNotNone(d.yer.akran, "arac heartbeat'i master->cikis yonunde gelir")
        _sure, m = d.yks_komut_ack(99, tavan_s=1.5)
        self.assertIsNone(m, "ACK (hava->yer) mavfwd kapaliyken DONMEMELI")
        self.assertGreater(d.alici.sayac["cmd"], 0, "yer->hava PARACHUTE hava tuketicisine ULASIR")
        self.assertGreater(d.mavproxy.sayac["mavfwd_atilan"], 0)
        kaynak = UDPLink(bind=(YEREL, 0), timeout=0.02)
        self.addCleanup(kaynak.close)
        kaynak.send(encode(heartbeat("iha", seq=4242)), d.hub_adr)
        _, hb = d.yer_bekle(lambda m: m.get("seq") == 4242, tavan_s=1.5)
        self.assertIsNone(hb, "hava->yer HEARTBEAT mavfwd kapaliyken ULASMAMALI")


if __name__ == "__main__":
    unittest.main()
