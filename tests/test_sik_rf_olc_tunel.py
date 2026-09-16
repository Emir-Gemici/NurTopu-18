"""K7 — `scripts/sik_rf_olc.py` tunel kipi ve `--prob-dolgu` (CONTRACTS §7.6 · K8 araci).

NEDEN: K8a/K8b gercek donanim olcumu bu aracla yapilir (INSAN gorevi). Burada
arac tezgahta, ArduPilot yonlendirici TAKLIDI uzerinden uctan uca kosturulur:
  * tunel kipi prob -> ACK dongusunu tamamlar; esikler karar_sozlesmesi'nden
    IMPORT edilir (verdikt mantigi degismez);
  * `--prob-dolgu B` prob cercevesini TAM B bayt yapar (165 B -> 2 parca,
    473 B -> 4 parca); dolgu > 0 kosusu JSON'da `kapi_disi: true` tasir;
  * CLI fail-closed: tunel + --tunel-bind yok -> 2; ulasilamaz dolgu -> 2.
Bu testler taklidi kanitlar; gercek hat hukmu K8'dedir (olculene dek ÖLÇÜLEMEDİ).
"""
from __future__ import annotations

import contextlib
import io
import json
import socket
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
for _y in (KOK / "comms", KOK / "codes", KOK / "scripts"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

try:
    import pymavlink  # noqa: F401
except ImportError:  # pragma: no cover
    pymavlink = None

import sik_rf_olc  # noqa: E402
from karar_sozlesmesi import (IKA_GO_TEKRAR_ARALIGI_S,  # noqa: E402
                              PARASUT_TEKRAR_ARALIGI_S)
from mavlink_tunel import (KIMLIK_HAVA, KIMLIK_YER, TASIYICI_TUNEL,  # noqa: E402
                           TUNEL_PARCA_YUK_B)

YEREL = "127.0.0.1"


def _bos_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((YEREL, 0))
    port = s.getsockname()[1]
    s.close()
    return port


class ProbDolgusuTests(unittest.TestCase):
    def test_dolgu_cerceveyi_tam_boya_getirir_ve_parca_sayisi(self):
        for b, parca in ((165, 2), (473, 4)):
            with self.subTest(b=b):
                c = sik_rf_olc.prob_cercevesi(7, b)
                self.assertEqual(b, len(c))
                self.assertEqual(parca, sik_rf_olc.tunel_parca_sayisi(len(c)))
                self.assertEqual(parca, -(-len(c) // TUNEL_PARCA_YUK_B))
                m = json.loads(c)
                self.assertTrue(sik_rf_olc._prob_mu(m), "dolgulu prob yine prob sayilmali")
        self.assertEqual(sik_rf_olc.encode(sik_rf_olc.command(
            sik_rf_olc.PROB_KOMUTU, sik_rf_olc.PROB_HEDEF, seq=3))[:40],
            sik_rf_olc.prob_cercevesi(3, 0)[:40])
        self.assertEqual(1, sik_rf_olc.tunel_parca_sayisi(len(sik_rf_olc.prob_cercevesi(3))))
        with self.assertRaises(ValueError):
            sik_rf_olc.prob_cercevesi(1, 20)

    def test_tasiyici_secenegi_ve_cli_fail_closed(self):
        self.assertEqual("tunel", sik_rf_olc.TASIYICI_TUNEL)
        self.assertEqual(TASIYICI_TUNEL, sik_rf_olc.TASIYICI_TUNEL)
        for argv in (["--rol", "olc", "--tasiyici", "tunel"],
                     ["--rol", "olc", "--tasiyici", "tunel", "--tunel-bind", "bozuk"],
                     ["--rol", "olc", "--tasiyici", "udp", "--peer", "127.0.0.1:9",
                      "--prob-dolgu", "20"],
                     ["--rol", "olc", "--tasiyici", "udp", "--peer", "127.0.0.1:9",
                      "--prob-dolgu", "-1"]):
            with self.subTest(argv=argv), self.assertRaises(SystemExit) as cm, \
                    contextlib.redirect_stderr(io.StringIO()):
                sik_rf_olc.main(argv)
            self.assertEqual(2, cm.exception.code)


@unittest.skipIf(pymavlink is None, "pymavlink kurulu degil")
class TunelKipiTaklitUzerindenTests(unittest.TestCase):
    """yer olc (TunelUc 'yer') <-> MP taklidi <-> ArduPilot taklidi <-> MAVProxy
    taklidi <-> hava yanki (TunelUc 'hava')."""

    def _zincir(self, yer_port, hat_bps=None):
        from ardupilot_yonlendirici_taklit import (ArdupilotYonlendiriciTaklit,
                                                   MavproxyTaklit, MP_GCS_KIMLIGI)
        hava = sik_rf_olc.TunelUc((YEREL, 0), KIMLIK_HAVA, timeout=0.05)
        self.addCleanup(hava.close)
        r = ArdupilotYonlendiriciTaklit(2, hat_bps=hat_bps)
        mp = MavproxyTaklit(r.kanal_adresi(0), [(YEREL, yer_port)], heartbeat=MP_GCS_KIMLIGI)
        mv = MavproxyTaklit(r.kanal_adresi(1), [(YEREL, hava.port)])
        r.kanal_bagla(0, mp.master_adresi)
        r.kanal_bagla(1, mv.master_adresi)
        for x in (r, mp, mv):
            x.baslat()
            self.addCleanup(x.durdur)
        dur = threading.Event()
        sayac = {}
        t = threading.Thread(target=sik_rf_olc.yanki_kos, args=(hava,),
                             kwargs={"dur": dur, "sayac": sayac}, daemon=True)
        t.start()
        self.addCleanup(t.join, 2.0)
        self.addCleanup(dur.set)
        return hava, sayac

    def _akran_bekle(self, uc, tavan_s=4.0):
        bitis = time.monotonic() + tavan_s
        while uc.link.akran is None and time.monotonic() < bitis:
            uc.oku()
        return uc.link.akran is not None

    def test_olc_kos_tunel_kipinde_ack_alir_esikler_sozlesmeden(self):
        yer = sik_rf_olc.TunelUc((YEREL, 0), KIMLIK_YER, timeout=0.05)
        self.addCleanup(yer.close)
        hava, _ = self._zincir(yer.port)
        self.assertTrue(self._akran_bekle(yer))
        rapor = sik_rf_olc.olc_kos(yer, 10, 0.1, zaman_asimi=1.0)
        self.assertEqual(10, rapor["ack_alinan"], rapor)
        self.assertEqual({"IKA_GO_TEKRAR_ARALIGI_S": IKA_GO_TEKRAR_ARALIGI_S,
                          "PARASUT_TEKRAR_ARALIGI_S": PARASUT_TEKRAR_ARALIGI_S},
                         rapor["esik_s"])
        self.assertFalse(rapor["kapi_disi"])
        self.assertEqual(sik_rf_olc.CIKIS_UYUMLU if rapor["rtt_ms"]["p95"] / 1000.0
                         < min(IKA_GO_TEKRAR_ARALIGI_S, PARASUT_TEKRAR_ARALIGI_S)
                         else sik_rf_olc.CIKIS_UYARI, rapor["cikis_kodu"])
        rapor2 = sik_rf_olc.olc_kos(yer, 5, 0.1, zaman_asimi=1.0, prob_dolgu_b=473)
        self.assertEqual(5, rapor2["ack_alinan"], rapor2)
        self.assertTrue(rapor2["kapi_disi"])
        self.assertIn("SAYILMAZ", rapor2["kapi_disi_notu"])

    def test_cli_tunel_olc_json_kapi_disi_ve_tunel_sayac(self):
        yer_port = _bos_port()
        self._zincir(yer_port)
        time.sleep(1.5)                       # arac heartbeat'i MP taklidinden gelsin
        with tempfile.TemporaryDirectory() as d:
            cikti = Path(d) / "K8_cok_parca_165.json"
            with contextlib.redirect_stdout(io.StringIO()), \
                    contextlib.redirect_stderr(io.StringIO()):
                kod = sik_rf_olc.main(["--rol", "olc", "--tasiyici", "tunel",
                                       "--tunel-bind", f"{YEREL}:{yer_port}",
                                       "--n", "6", "--aralik", "0.25", "--prob-dolgu", "165",
                                       "--json", "--sessiz", "--cikti", str(cikti)])
            rapor = json.loads(cikti.read_text(encoding="utf-8"))
        self.assertIn(kod, (sik_rf_olc.CIKIS_UYUMLU, sik_rf_olc.CIKIS_UYARI,
                            sik_rf_olc.CIKIS_OLCULEMEDI))
        self.assertEqual("tunel", rapor["tasiyici"])
        self.assertEqual(KIMLIK_YER, rapor["tunel_kimlik"], "olc rolu varsayilani yer")
        self.assertTrue(rapor["kapi_disi"])
        self.assertEqual(165, rapor["prob_dolgu_b"])
        self.assertEqual(2, rapor["prob_tunel_parca"])
        self.assertIn("kimlik_boslugu", rapor["tunel_sayac"])
        self.assertGreaterEqual(rapor["ack_alinan"], 1, rapor)


if __name__ == "__main__":
    unittest.main()
