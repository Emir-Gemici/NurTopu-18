"""İHA karar yayıncısının ACK kaynak/tip/saat güvenlik kapıları.

Mutasyonların tehlike yönü fail-open'dır: başka bir süreçten gelen ya da bozuk
ACK aktarımı tamamlanmış gösteremez; bozuk bir UDP datagramı da ardından gelen
sağlam ACK'i yutamaz. Testler gerçek dosyalara/duvar saatine müdahale etmez.
"""

from __future__ import annotations

import json
import sys
import time
import unittest
from pathlib import Path
from unittest import mock


KOK = Path(__file__).resolve().parents[1]
for _yol in (KOK / "comms", KOK / "codes"):
    if str(_yol) not in sys.path:
        sys.path.insert(0, str(_yol))

import iha_sender  # noqa: E402
from iha_sender import IhaSender, KararYayinci  # noqa: E402
from protocol import PROTOCOL_VERSION, ack, encode, rota_yok  # noqa: E402


AKRAN = ("127.0.0.1", 55001)
YABANCI = ("127.0.0.1", 55002)


class _AdimliSaat:
    def __init__(self, adim=0.01):
        self.deger = 0.0
        self.adim = adim

    def __call__(self):
        sonuc = self.deger
        self.deger += self.adim
        return sonuc


class _KuyrukLink:
    def __init__(self, alinan=()):
        self.alinan = list(alinan)
        self.gonderilen = []

    def send(self, data, peer=None):
        self.gonderilen.append((data, peer))

    def recv(self, _bufsize=4096):
        if self.alinan:
            return self.alinan.pop(0)
        return None, None


def _ham(nesne):
    return (json.dumps(nesne, separators=(",", ":")) + "\n").encode("utf-8")


class AckDogrulamaTests(unittest.TestCase):
    def _gonder(self, alinan, *, peers=None, interval=0.06):
        link = _KuyrukLink(alinan)
        sender = IhaSender(
            link, peers or {"ika": AKRAN}, monotonic=_AdimliSaat())
        mesaj = rota_yok("TEST", seq=71)
        return sender._tekrarli_gonder(
            mesaj, repeat=1, interval=interval, wait_ack=True)

    def test_dogru_ack_beklenen_kaynaktan_kabul_edilir(self):
        _, acked = self._gonder([
            (encode(ack(71, "ika", "NO_ROUTE")), AKRAN),
        ])
        self.assertEqual({"ika"}, acked)

    def test_yabanci_udp_kaynagi_dogru_icerikle_bile_reddedilir(self):
        _, acked = self._gonder([
            (encode(ack(71, "ika", "NO_ROUTE")), YABANCI),
        ])
        self.assertEqual(set(), acked)

    def test_bool_ref_yabanci_node_ve_bozuk_ref_tip_reddedilir(self):
        bozuklar = [
            ["ACK"],
            {"v": PROTOCOL_VERSION, "type": "ACK", "ref": True,
             "node": "ika", "ref_tip": "NO_ROUTE"},
            {"v": PROTOCOL_VERSION, "type": "ACK", "ref": 71,
             "node": "yks", "ref_tip": "NO_ROUTE"},
            {"v": PROTOCOL_VERSION, "type": "ACK", "ref": 71,
             "node": "ika", "ref_tip": None},
            {"v": PROTOCOL_VERSION, "type": "ACK", "ref": 71,
             "node": "ika", "ref_tip": 123},
            {"v": True, "type": "ACK", "ref": 71,
             "node": "ika", "ref_tip": "NO_ROUTE"},
        ]
        alinan = [(_ham(m), AKRAN) for m in bozuklar]
        _, acked = self._gonder(alinan, interval=0.2)
        self.assertEqual(set(), acked)

    def test_bozuk_udp_datagrami_sonraki_saglam_acki_zehirlemez(self):
        _, acked = self._gonder([
            (b'{"v":1,"type":"ACK"', AKRAN),  # newline yok, eksik JSON
            (encode(ack(71, "ika", "NO_ROUTE")), AKRAN),
        ], interval=0.2)
        self.assertEqual({"ika"}, acked)

    def test_ref_tipsiz_eski_ack_kaynak_sabitlemeyle_kabul_edilir(self):
        _, acked = self._gonder([(encode(ack(71, "ika")), AKRAN)])
        self.assertEqual({"ika"}, acked)

    def test_ack_penceresi_duvar_saatine_bakmaz(self):
        link = _KuyrukLink()
        sender = IhaSender(
            link, {"ika": AKRAN}, monotonic=_AdimliSaat(adim=0.02))
        mesaj = rota_yok("TEST", seq=72)
        with mock.patch.object(
                iha_sender.time, "time",
                side_effect=AssertionError("ACK penceresi wall-clock kullandi")):
            _, acked = sender._tekrarli_gonder(
                mesaj, repeat=1, interval=0.05,
                wait_ack=True)
        self.assertEqual(set(), acked)

    def test_gonderilecek_bool_seq_fail_closed_reddedilir(self):
        sender = IhaSender(_KuyrukLink(), {"ika": AKRAN},
                           monotonic=_AdimliSaat())
        with self.assertRaisesRegex(ValueError, "tamsayi seq"):
            sender._tekrarli_gonder(
                {"v": PROTOCOL_VERSION, "type": "NO_ROUTE", "seq": True},
                repeat=1, interval=0.0, wait_ack=False)


class KararThreadDayaniklilikTests(unittest.TestCase):
    class _Sender:
        def __init__(self):
            self.cagrilar = []

        def send_no_route(self, *args, **kwargs):
            self.cagrilar.append((args, kwargs))
            return 901, set()

        def send_heartbeat(self, **_kwargs):
            return 1

    def test_beklenmedik_dongu_hatasi_kaydedilir_thread_sessiz_olmez(self):
        sender = self._Sender()
        yayinci = KararYayinci(
            sender, heartbeat_aralik=0.02, repeat=1, interval=0.0,
            wait_ack=False)
        asil_yuvayi_al = yayinci._yuvayi_al
        ilk = True

        def bir_kez_patla():
            nonlocal ilk
            if ilk:
                ilk = False
                raise RuntimeError("mutasyon")
            return asil_yuvayi_al()

        yayinci._yuvayi_al = bir_kez_patla
        yayinci.start()
        self.addCleanup(lambda: yayinci.stop(1.0))
        yayinci.karar(None, 0.0, None, None)

        son = time.monotonic() + 1.0
        while time.monotonic() < son and not yayinci.hata:
            time.sleep(0.005)
        self.assertTrue(any("karar_dongusu RuntimeError: mutasyon" in h
                            for h in yayinci.hata), yayinci.hata)
        self.assertTrue(yayinci._karar_thr.is_alive())

        # Yeni olay thread'i yeniden uyandırır; kusurlu ilk tur sessiz bir
        # OPEN_ROUTE üretmez, ikinci karar fail-closed NO_ROUTE olarak gider.
        yayinci.karar(None, 0.0, None, None)
        son = time.monotonic() + 1.0
        while time.monotonic() < son and not sender.cagrilar:
            time.sleep(0.005)
        self.assertEqual(1, len(sender.cagrilar))


if __name__ == "__main__":
    unittest.main()
