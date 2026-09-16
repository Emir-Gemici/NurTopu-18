"""K7 — `scripts/sik_rf_olc.py` tunel kipi ve `--prob-dolgu` (CONTRACTS §7.6 · K8 araci).

NEDEN: K8a/K8b gercek donanim olcumu bu aracla yapilir (INSAN gorevi). Burada
arac tezgahta, ArduPilot yonlendirici TAKLIDI uzerinden uctan uca kosturulur:
  * tunel kipi prob -> ACK dongusunu tamamlar; esikler karar_sozlesmesi'nden
    IMPORT edilir (verdikt mantigi degismez);
  * `--prob-dolgu B` prob cercevesini TAM B bayt yapar (165 B -> 2 parca,
    473 B -> 4 parca); dolgu > 0 kosusu JSON'da `kapi_disi: true` tasir;
  * CLI fail-closed: tunel + --tunel-bind yok -> 2; ulasilamaz dolgu -> 2.
Duzeltme turu 1:
  * `--ack-dolgu B` (yanki) hava->yer yonunu cok parcali yapar; olc raporu
    dolgulu ACK'i sayar ve `kapi_disi: true` yazar;
  * `datagram_siniri`: MP aynasinin sinirini AYIRT EDER — paket ortasindan
    baslayan datagramlar 'akis' kipinde cozulse de `hizasiz` sayilir
    (curutucu k80i.py deneyi: eski olcut `mavlink_paket/alinan_datagram ~ 1`
    ve `cozum_hatasi = 0` ile GECIYORDU, 'datagram' kipi %100 kaybederdi);
  * yanki Ctrl+C'de sayaclari yazar.
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
from mavlink_tunel import (AYRISTIRMA_AKIS, AYRISTIRMA_DATAGRAM,  # noqa: E402
                           KIMLIK_HAVA, KIMLIK_YER, TASIYICI_TUNEL,
                           TUNEL_PARCA_YUK_B)
from unittest import mock  # noqa: E402

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

    def test_ack_dolgusu_tam_boy_ve_ack_olarak_eslesir(self):
        for b, parca in ((165, 2), (473, 4)):
            with self.subTest(b=b):
                c = sik_rf_olc.ack_cercevesi(9, b)
                self.assertEqual(b, len(c))
                self.assertEqual(parca, sik_rf_olc.tunel_parca_sayisi(len(c)))
                self.assertTrue(sik_rf_olc._ack_eslesir(json.loads(c), 9))
        self.assertEqual(json.loads(sik_rf_olc.encode(sik_rf_olc.ack(
            9, sik_rf_olc.YANKI_DUGUMU, ref_tip=sik_rf_olc.ACK_REF_TIPI))).keys(),
            json.loads(sik_rf_olc.ack_cercevesi(9, 0)).keys(), "dolgusuz ACK eskisiyle ayni")
        with self.assertRaises(ValueError):
            sik_rf_olc.ack_cercevesi(1, 20)

    def test_yanki_ctrl_c_sayaclari_yazar_cevaplanani_dondurur(self):
        gelen = [sik_rf_olc.prob_cercevesi(1), sik_rf_olc.prob_cercevesi(2)]
        gonderilen = []

        class _Uc:
            def oku(self):
                if gelen:
                    return gelen.pop(0)
                raise KeyboardInterrupt

            def send(self, data, peer=None):
                gonderilen.append(data)
        sayac = {}
        try:
            cevaplanan = sik_rf_olc.yanki_kos(_Uc(), sayac=sayac, ack_dolgu_b=165)
        except KeyboardInterrupt:
            self.fail("Ctrl+C yanki_kos'tan tasti: sayac yazilmaz, cevaplanan kaybolur")
        self.assertEqual(2, cevaplanan)
        self.assertEqual(2, sayac["gonderilen_paket"])
        self.assertEqual([165, 165], [len(g) for g in gonderilen])

    def test_olc_dolgulu_ack_kapi_disi_yazar(self):
        class _Uc:
            def __init__(self):
                self.bekleyen = []

            def send(self, data, peer=None):
                seq = json.loads(data)["seq"]
                self.bekleyen.append(sik_rf_olc.ack_cercevesi(seq, 473))

            def oku(self):
                return self.bekleyen.pop(0) if self.bekleyen else b""
        rapor = sik_rf_olc.olc_kos(_Uc(), 3, 0.01, zaman_asimi=0.5)
        self.assertEqual(3, rapor["ack_alinan"])
        self.assertEqual(3, rapor["ack_dolgulu"])
        self.assertTrue(rapor["kapi_disi"])
        self.assertIn("SAYILMAZ", rapor["kapi_disi_notu"])

    def test_tasiyici_secenegi_ve_cli_fail_closed(self):
        self.assertEqual("tunel", sik_rf_olc.TASIYICI_TUNEL)
        self.assertEqual(TASIYICI_TUNEL, sik_rf_olc.TASIYICI_TUNEL)
        for argv in (["--rol", "olc", "--tasiyici", "tunel"],
                     ["--rol", "olc", "--tasiyici", "tunel", "--tunel-bind", "bozuk"],
                     ["--rol", "olc", "--tasiyici", "udp", "--peer", "127.0.0.1:9",
                      "--prob-dolgu", "20"],
                     ["--rol", "olc", "--tasiyici", "udp", "--peer", "127.0.0.1:9",
                      "--prob-dolgu", "-1"],
                     ["--rol", "olc", "--tasiyici", "udp", "--peer", "127.0.0.1:9",
                      "--ack-dolgu", "473"],
                     ["--rol", "yanki", "--tasiyici", "udp", "--ack-dolgu", "20"],
                     ["--rol", "yanki", "--tasiyici", "udp", "--tunel-ayristirma", "datagram"]):
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

    def test_datagram_siniri_hizasiz_akisi_ayirt_eder_K8_0_i(self):
        """Curutucu k80i.py deneyinin yeniden kurulumu: 200 gecerli MAVLink paketi
        paket boyunda ama paket ORTASINDAN baslayan datagramlarla. Eski olcut
        (`mavlink_paket/alinan_datagram ~ 1`, `cozum_hatasi = 0`) 'akis' kipinde
        GECER; `datagram_siniri.hizasiz` bunu yakalar. Hizali akista hizasiz 0."""
        from pymavlink.dialects.v20 import ardupilotmega as m
        kod = m.MAVLink(None, srcSystem=1, srcComponent=1)
        paketler = [kod.attitude_encode(i, 0.1, 0.2, 0.3, 0.01, 0.02, 0.03).pack(kod)
                    for i in range(200)]
        boy = len(paketler[0])
        akis = b"".join(paketler)
        kaydir = boy // 2
        hizasiz = [akis[:kaydir]] + [akis[kaydir + i * boy:kaydir + (i + 1) * boy]
                                     for i in range(200)]
        hizasiz = [d for d in hizasiz if d]
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.addCleanup(s.close)
        for ad, datagramlar, kip in (("hizasiz", hizasiz, AYRISTIRMA_AKIS),
                                     ("hizali", paketler, AYRISTIRMA_AKIS),
                                     ("hizasiz_datagram_kipi", hizasiz, AYRISTIRMA_DATAGRAM)):
            with self.subTest(ad=ad):
                uc = sik_rf_olc.TunelUc((YEREL, 0), KIMLIK_YER, timeout=0.05, ayristirma=kip)
                self.addCleanup(uc.close)
                self.assertEqual(kip, uc.link.ayristirma)
                for d in datagramlar:
                    s.sendto(d, (YEREL, uc.port))
                bitis = time.monotonic() + 3.0
                while (sum(uc.datagram_siniri.values()) < len(datagramlar)
                       and time.monotonic() < bitis):
                    uc.oku()
                c = uc.link.sayac
                self.assertEqual(len(datagramlar), c["alinan_datagram"])
                if ad == "hizasiz":
                    # eski olcut burada YANLIS GECER (belge): oran ~1, cozum_hatasi 0
                    self.assertGreater(c["mavlink_paket"] / c["alinan_datagram"], 0.99)
                    self.assertEqual(0, c["cozum_hatasi"])
                    self.assertEqual(len(datagramlar), uc.datagram_siniri["hizasiz"])
                    self.assertEqual(0, uc.datagram_siniri["hizali"])
                elif ad == "hizali":
                    self.assertEqual({"hizali": 200, "hizasiz": 0}, uc.datagram_siniri)
                    self.assertEqual(200, c["mavlink_paket"])
                else:
                    self.assertEqual(0, c["mavlink_paket"], "datagram kipi hizasizda paket KAYBEDER")
                    self.assertEqual(len(datagramlar), uc.datagram_siniri["hizasiz"])
        self.assertFalse(sik_rf_olc.datagram_siniri_hizali_mi(paketler[0] + paketler[1][:5], m))
        self.assertFalse(sik_rf_olc.datagram_siniri_hizali_mi(b"", m))
        self.assertTrue(sik_rf_olc.datagram_siniri_hizali_mi(paketler[0] + paketler[1], m))

    def test_cli_yanki_ack_dolgu_hava_yer_cok_parca_uctan_uca(self):
        """Hava yanki --ack-dolgu 473 (4 parca, hava->yer) taklit zinciri uzerinden
        olc ucuna ulasir; olc raporu kapi_disi + ack_dolgulu yazar."""
        yer = sik_rf_olc.TunelUc((YEREL, 0), KIMLIK_YER, timeout=0.05)
        self.addCleanup(yer.close)
        from ardupilot_yonlendirici_taklit import (ArdupilotYonlendiriciTaklit,
                                                   MavproxyTaklit, MP_GCS_KIMLIGI)
        hava_port = _bos_port()
        r = ArdupilotYonlendiriciTaklit(2)
        mp = MavproxyTaklit(r.kanal_adresi(0), [(YEREL, yer.port)], heartbeat=MP_GCS_KIMLIGI)
        mv = MavproxyTaklit(r.kanal_adresi(1), [(YEREL, hava_port)])
        r.kanal_bagla(0, mp.master_adresi)
        r.kanal_bagla(1, mv.master_adresi)
        for x in (r, mp, mv):
            x.baslat()
            self.addCleanup(x.durdur)
        with tempfile.TemporaryDirectory() as d:
            cikti = Path(d) / "K8_hava_yanki_ack473.json"
            sonuc = {}

            def yanki():
                with contextlib.redirect_stdout(io.StringIO()), \
                        contextlib.redirect_stderr(io.StringIO()):
                    sonuc["kod"] = sik_rf_olc.main(
                        ["--rol", "yanki", "--tasiyici", "tunel", "--tunel-bind",
                         f"{YEREL}:{hava_port}", "--ack-dolgu", "473", "--json", "--sessiz",
                         "--cikti", str(cikti)])
            gercek_yanki = sik_rf_olc.yanki_kos
            dur = threading.Event()

            def durdurulabilir(link, **kw):
                return gercek_yanki(link, dur=dur, **kw)
            with mock.patch.object(sik_rf_olc, "yanki_kos", side_effect=durdurulabilir):
                t = threading.Thread(target=yanki, daemon=True)
                t.start()
                self.assertTrue(self._akran_bekle(yer))
                time.sleep(1.5)       # hava yanki ucu da arac heartbeat'ini (1 Hz) gorsun
                rapor = sik_rf_olc.olc_kos(yer, 5, 0.25, zaman_asimi=1.0)
                dur.set()
                t.join(5.0)
            hava_json = json.loads(cikti.read_text(encoding="utf-8"))
        self.assertEqual(5, rapor["ack_alinan"], rapor)
        self.assertEqual(5, rapor["ack_dolgulu"])
        self.assertTrue(rapor["kapi_disi"])
        self.assertEqual(sik_rf_olc.CIKIS_UYUMLU, sonuc["kod"])
        self.assertTrue(hava_json["kapi_disi"])
        self.assertEqual(473, hava_json["ack_dolgu_b"])
        self.assertEqual(4, hava_json["ack_tunel_parca"])
        self.assertEqual(5, hava_json["cevaplanan"])
        self.assertIn("tunel_sayac", hava_json)
        self.assertEqual(0, hava_json["datagram_siniri"]["hizasiz"])
        self.assertGreater(yer.link.sayac["teslim_cerceve"], 0)

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
        self.assertEqual(AYRISTIRMA_AKIS, rapor["tunel_ayristirma"], "yer varsayilani")
        self.assertEqual(0, rapor["datagram_siniri"]["hizasiz"])
        self.assertGreater(rapor["datagram_siniri"]["hizali"], 0)


if __name__ == "__main__":
    unittest.main()
