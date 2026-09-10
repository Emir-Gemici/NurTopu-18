"""Faz B — SiK RF olcum araci (`scripts/sik_rf_olc.py`) GERCEK bayt akisinda.

NEDEN: Cumartesi iki SiK telsizle ACK gidis-donusu olculecek (RTT p50/p95,
kayip). Arac o gun ILK KEZ kosmamali; bugun D-388'in TCP koprusuyle
(`tests/test_p2_seri_hat.py::SikKoprusu`, iki gercek `socket://` pyserial ucu)
sinanir. Kilitlenen sey: arac gercek `protocol` cerceveleriyle CMD -> ACK
turunu kapatir, RTT'yi ilk-bayt okumasiyla olcer (okuma zaman asimina
yuvarlamaz), kayip/gecikme durumunda fail-closed hukum verir ve COKMEZ.

⚠ GERCEK RF YOKTUR: menzil, SiK ECC, baud uyusmazligi burada yok. Bu test
aracin YORDAMINI kilitler; 433 MHz sayilari Cumartesi olculur.
"""
import contextlib
import io
import json
import sys
import threading
import time
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
for _y in (KOK / "scripts", KOK / "tests", KOK / "comms", KOK / "codes"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

try:
    import serial
except ImportError:  # pragma: no cover - kurulum kapisi
    serial = None

import sik_rf_olc  # noqa: E402
from karar_sozlesmesi import (IKA_GO_TEKRAR_ARALIGI_S,  # noqa: E402
                              PARASUT_TEKRAR_ARALIGI_S)
from protocol import FrameReader, ack, command, encode  # noqa: E402
from test_p2_seri_hat import SikKoprusu  # noqa: E402

BAUD = sik_rf_olc.VARSAYILAN_BAUD
N_PROB = 20
ARALIK_S = 0.05
ENJEKTE_GECIKME_S = 0.30          # gorev tanimi: kopruye 300 ms gecikme
ESIK_S = min(IKA_GO_TEKRAR_ARALIGI_S, PARASUT_TEKRAR_ARALIGI_S)
#: Cerceve uzunlugu `t` (3 ondalik) ve `seq` basamagiyla birkac bayt oynar;
#: sayac kilidi bu payla kurulur (ornek: 1757500000.1 vs 1757500000.123).
CERCEVE_PAYI_BAYT = 4


def _gecikmeli(veri):
    """SikKoprusu bozucusu: A->B yonunu 300 ms geciktirir (RF gecikmesi)."""
    time.sleep(ENJEKTE_GECIKME_S)
    return veri


def _main_kos(argv):
    """CLI'yi cagir; (cikis_kodu, stdout_metni) dondur. Ilerleme stderr'de bastirilir."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        kod = sik_rf_olc.main(argv)
    return kod, out.getvalue()


@unittest.skipIf(serial is None, "pyserial kurulu degil")
class SikRfOlcKoprude(unittest.TestCase):
    """Arac, iki gercek pyserial ucu arasindaki TCP koprusunde kosar."""

    def _kopru(self, bozucu=None):
        k = SikKoprusu(bozucu=bozucu)
        self.addCleanup(k.kapat)
        return k

    def _url(self, kopru):
        return f"socket://127.0.0.1:{kopru.port}"

    def _yanki_baslat(self, kopru):
        """Yanki rolu ayri thread'de, aracin kendi `uc_ac`/`yanki_kos` yoluyla."""
        link = sik_rf_olc.uc_ac(self._url(kopru), BAUD, timeout=0.1)
        dur = threading.Event()
        sonuc = {"sayac": {}}

        def calis():
            sonuc["cevaplanan"] = sik_rf_olc.yanki_kos(link, dur=dur,
                                                       sayac=sonuc["sayac"])

        t = threading.Thread(target=calis, daemon=True)
        t.start()

        def temizle():
            dur.set()
            t.join(timeout=2.0)
            link.close()

        self.addCleanup(temizle)
        return sonuc, dur, t

    # --- (1) ---
    def test_1_mutlu_yol_20_20_ACK_kayip_0_p95_esik_altinda_cikis_0(self):
        """Yanki varken 20/20 ACK, kayip 0, p95 < tekrar araligi -> cikis 0."""
        kopru = self._kopru()
        sonuc, dur, t = self._yanki_baslat(kopru)
        kod, cikti = _main_kos([
            "--rol", "olc", "--port", self._url(kopru), "--n", str(N_PROB),
            "--aralik", str(ARALIK_S), "--zaman-asimi", "0.25",
            "--json", "--sessiz"])
        rapor = json.loads(cikti)
        self.assertEqual(rapor["gonderilen"], N_PROB)
        self.assertEqual(rapor["ack_alinan"], N_PROB,
                         f"ACK {rapor['ack_alinan']}/{N_PROB}: {rapor}")
        self.assertEqual(rapor["kayip"], 0)
        self.assertEqual(rapor["kayip_yuzde"], 0.0)
        p95_s = rapor["rtt_ms"]["p95"] / 1000.0
        self.assertLess(p95_s, IKA_GO_TEKRAR_ARALIGI_S,
                        f"p95 {p95_s:.4f} s IKA_GO araligini asiyor")
        self.assertLess(p95_s, PARASUT_TEKRAR_ARALIGI_S,
                        f"p95 {p95_s:.4f} s PARASUT araligini asiyor")
        self.assertEqual(rapor["verdikt"], sik_rf_olc.VERDIKT_UYUMLU)
        self.assertEqual(kod, sik_rf_olc.CIKIS_UYUMLU)
        self.assertEqual(rapor["cikis_kodu"], kod)
        # RTT okuma zaman asimina YUVARLANMIYOR: pyserial read(256) zaman asimina
        # kadar bloklasaydi p50 ~= OLC_OKUMA_ZAMAN_ASIMI_S (50 ms) cikardi;
        # loopback'te gercek RTT ~1 ms (olculdu: p50 0,85 ms, p95 1,09 ms).
        self.assertLess(rapor["rtt_ms"]["p50"],
                        sik_rf_olc.OLC_OKUMA_ZAMAN_ASIMI_S * 1000 / 2,
                        "RTT okuma zaman asimina yuvarlaniyor (read(256) bloklamasi)")
        dur.set()
        t.join(timeout=2.0)
        self.assertEqual(sonuc.get("cevaplanan"), N_PROB,
                         "yanki her probu tam bir kez cevaplamali")

    # --- (2) ---
    def test_2_300ms_gecikme_p95_esigi_asar_cikis_1_UYARI(self):
        """Kopruye 300 ms gecikme -> RTT p95 >= 300 ms > esik -> UYARI, cikis 1."""
        kopru = self._kopru(bozucu=_gecikmeli)
        # Gecikme A->B yonundedir; ilk baglanan uc A'dir. RTT icin yon fark etmez.
        olc_url = self._url(kopru)
        sonuc, dur, t = self._yanki_baslat(kopru)
        kod, cikti = _main_kos([
            "--rol", "olc", "--port", olc_url, "--n", str(N_PROB),
            "--aralik", str(ARALIK_S), "--zaman-asimi", "0.6",
            "--json", "--sessiz"])
        rapor = json.loads(cikti)
        self.assertEqual(rapor["ack_alinan"], N_PROB,
                         f"gecikmeli ACK'ler zaman asimi icinde gelmeli: {rapor}")
        p95_s = rapor["rtt_ms"]["p95"] / 1000.0
        self.assertGreaterEqual(p95_s, ENJEKTE_GECIKME_S,
                                "enjekte edilen gecikme RTT'de gorunmuyor")
        self.assertGreater(p95_s, ESIK_S)
        self.assertEqual(rapor["verdikt"], sik_rf_olc.VERDIKT_UYARI)
        self.assertEqual(kod, sik_rf_olc.CIKIS_UYARI)
        self.assertEqual(rapor["cikis_kodu"], sik_rf_olc.CIKIS_UYARI)

    # --- (3) ---
    def test_3_yanki_yokken_kayip_yuzde_100_cokmez_UYUMLU_demez(self):
        """Karsi uc yok: 20 prob, 0 ACK, kayip %100; arac cokmez, UYUMLU demez."""
        kopru = self._kopru()                     # ikinci uc HIC baglanmaz
        kod, cikti = _main_kos([
            "--rol", "olc", "--port", self._url(kopru), "--n", str(N_PROB),
            "--aralik", str(ARALIK_S), "--json", "--sessiz"])
        rapor = json.loads(cikti)
        self.assertEqual(rapor["gonderilen"], N_PROB)
        self.assertEqual(rapor["ack_alinan"], 0)
        self.assertEqual(rapor["kayip"], N_PROB)
        self.assertEqual(rapor["kayip_yuzde"], 100.0)
        self.assertIsNone(rapor["rtt_ms"]["p95"])
        self.assertEqual(rapor["verdikt"], sik_rf_olc.VERDIKT_OLCULEMEDI)
        self.assertNotEqual(kod, sik_rf_olc.CIKIS_UYUMLU,
                            "ACK'siz olcum UYUMLU sayilamaz (fail-closed)")
        self.assertEqual(kod, sik_rf_olc.CIKIS_OLCULEMEDI)
        # Varsayilan zaman asimi = 2 * aralik (gorev tanimi)
        self.assertAlmostEqual(rapor["zaman_asimi_s"], 2 * ARALIK_S, places=9)
        # Sayac: ACK yokken alinan 0, gonderilen N (kayip sayaci bozmaz)
        v = rapor["veri_hizi"]
        self.assertEqual((v["gonderilen_paket"], v["alinan_paket"], v["alinan_bayt"]),
                         (N_PROB, 0, 0))
        self.assertEqual(v["alinan_bayt_s"], 0.0)

    # --- (4) T216: veri hizi sayaclari — gercek bayt akisinda, iki uc tutarli ---
    def test_4_veri_hizi_sayaclari_koprude_iki_uc_tutarli(self):
        """olc'un gonderdigi bayt == yanki'nin aldigi; yanki'nin gonderdigi ==
        olc'un aldigi (bayt bayt). Hizlar sayac/sure ile birebir; sure en az
        (N-1)*aralik. RTT/kayip alanlari degismedi (test_1 ile ayni hukum)."""
        kopru = self._kopru()
        sonuc, dur, t = self._yanki_baslat(kopru)
        kod, cikti = _main_kos([
            "--rol", "olc", "--port", self._url(kopru), "--n", str(N_PROB),
            "--aralik", str(ARALIK_S), "--zaman-asimi", "0.25",
            "--json", "--sessiz"])
        rapor = json.loads(cikti)
        self.assertEqual(kod, sik_rf_olc.CIKIS_UYUMLU, rapor)
        self.assertEqual(rapor["ack_alinan"], N_PROB, rapor)
        v = rapor["veri_hizi"]
        cmd_b = len(encode(command(sik_rf_olc.PROB_KOMUTU, sik_rf_olc.PROB_HEDEF, seq=1)))
        ack_b = len(encode(ack(1, sik_rf_olc.YANKI_DUGUMU, ref_tip=sik_rf_olc.ACK_REF_TIPI)))
        self.assertEqual(v["gonderilen_paket"], N_PROB)
        self.assertEqual(v["alinan_paket"], N_PROB, "hatta yalniz ACK var: cozulen = ACK")
        self.assertTrue(N_PROB * (cmd_b - CERCEVE_PAYI_BAYT) <= v["gonderilen_bayt"]
                        <= N_PROB * (cmd_b + CERCEVE_PAYI_BAYT), (v, cmd_b))
        self.assertTrue(N_PROB * (ack_b - CERCEVE_PAYI_BAYT) <= v["alinan_bayt"]
                        <= N_PROB * (ack_b + CERCEVE_PAYI_BAYT), (v, ack_b))
        self.assertGreaterEqual(v["sure_s"], (N_PROB - 1) * ARALIK_S)
        self.assertAlmostEqual(v["gonderilen_bayt_s"] * v["sure_s"], v["gonderilen_bayt"], places=6)
        self.assertAlmostEqual(v["alinan_bayt_s"] * v["sure_s"], v["alinan_bayt"], places=6)
        self.assertAlmostEqual(v["gonderilen_bit_s"], 8 * v["gonderilen_bayt_s"], places=6)
        self.assertAlmostEqual(v["gonderilen_paket_s"] * v["sure_s"], N_PROB, places=6)
        self.assertAlmostEqual(v["alinan_paket_s"] * v["sure_s"], N_PROB, places=6)
        # Kadans yuku (kapasite degil): pencere (N-1)*aralik + son RTT oldugundan
        # paket/s en fazla N/((N-1)*aralik) olabilir; 1/aralik'i hafif asar.
        self.assertLessEqual(v["gonderilen_paket_s"],
                             N_PROB / ((N_PROB - 1) * ARALIK_S) + 1e-9)
        self.assertGreater(v["gonderilen_paket_s"], 0.5 / ARALIK_S,
                           "kadans yukunun yarisindan az paket/s: sure sayaci bozuk")
        dur.set()
        t.join(timeout=2.0)
        y = sonuc["sayac"]
        self.assertEqual(sonuc.get("cevaplanan"), N_PROB)
        self.assertEqual(y["alinan_bayt"], v["gonderilen_bayt"], "yanki aldigi != olc gonderdigi")
        self.assertEqual(y["gonderilen_bayt"], v["alinan_bayt"], "yanki gonderdigi != olc aldigi")
        self.assertEqual((y["gonderilen_paket"], y["alinan_paket"]), (N_PROB, N_PROB))
        self.assertGreater(y["sure_s"], 0.0)
        self.assertIn("veri hizi", sik_rf_olc.rapor_metni(rapor))

    # --- (5) T216: UDP tasiyici — ayni yordam loopback'te ---
    def test_5_udp_loopback_tasiyici_ayni_yordam_cikis_0(self):
        """`--tasiyici udp`: yanki ephemeral portta, olc `--peer` ile; 20/20 ACK,
        kayip 0, cikis 0, veri_hizi dolu, RTT loopback duzeyinde (< 25 ms)."""
        yanki = sik_rf_olc.udp_uc_ac("127.0.0.1:0", timeout=0.1)
        dur = threading.Event()
        sonuc = {"sayac": {}}

        def calis():
            sonuc["cevaplanan"] = sik_rf_olc.yanki_kos(yanki, dur=dur,
                                                       sayac=sonuc["sayac"])

        t = threading.Thread(target=calis, daemon=True)
        t.start()

        def temizle():
            dur.set()
            t.join(timeout=2.0)
            yanki.close()

        self.addCleanup(temizle)
        kod, cikti = _main_kos([
            "--rol", "olc", "--tasiyici", "udp", "--peer", f"127.0.0.1:{yanki.port}",
            "--n", str(N_PROB), "--aralik", str(ARALIK_S), "--zaman-asimi", "0.25",
            "--json", "--sessiz"])
        rapor = json.loads(cikti)
        self.assertEqual(rapor["tasiyici"], sik_rf_olc.TASIYICI_UDP)
        self.assertTrue(rapor["peer"].endswith(f":{yanki.port}"), rapor["peer"])
        self.assertEqual(rapor["ack_alinan"], N_PROB, rapor)
        self.assertEqual(rapor["kayip"], 0)
        self.assertEqual(kod, sik_rf_olc.CIKIS_UYUMLU)
        self.assertLess(rapor["rtt_ms"]["p50"], 25.0, "UDP loopback RTT beklenenden buyuk")
        v = rapor["veri_hizi"]
        self.assertEqual((v["gonderilen_paket"], v["alinan_paket"]), (N_PROB, N_PROB))
        self.assertGreater(v["gonderilen_bayt_s"], 0.0)
        dur.set()
        t.join(timeout=2.0)
        self.assertEqual(sonuc.get("cevaplanan"), N_PROB)
        self.assertEqual(sonuc["sayac"]["alinan_bayt"], v["gonderilen_bayt"])


class SikRfOlcVeriHiziSayaci(unittest.TestCase):
    """T216 sayac kilidi — DETERMINISTIK sahte uc (kopru yok, zamanlama yok).

    Mutasyon (elle, kayit: T216 kapi ciktisi): `olc_kos` icindeki
    `gonderilen_bayt += len(cerceve)` satiri kaldirilinca bu sinif DUSER.
    """

    class _SahteSeri:
        def __init__(self):
            self.tampon = b""

        def read(self, n):
            parca, self.tampon = self.tampon[:n], self.tampon[n:]
            return parca

        @property
        def in_waiting(self):
            return len(self.tampon)

    class _SahteLink:
        """Her CMD cercevesine aninda ACK yazan sahte pyserial ucu (link.ser)."""

        def __init__(self, cevapla=True):
            self.ser = SikRfOlcVeriHiziSayaci._SahteSeri()
            self.yazilan, self.acklar = [], []
            self._okuyucu = FrameReader()
            self._cevapla = cevapla

        def send(self, data, peer=None):
            self.yazilan.append(data)
            for m in self._okuyucu.feed(data):
                if self._cevapla:
                    a = encode(ack(m["seq"], "ika", ref_tip="CMD"))
                    self.acklar.append(a)
                    self.ser.tampon += a

        def close(self):
            pass

    def test_sayaclar_gonderilen_ve_alinan_baytla_birebir(self):
        link = self._SahteLink()
        rapor = sik_rf_olc.olc_kos(link, 5, 0.01, zaman_asimi=0.5)
        v = rapor["veri_hizi"]
        self.assertEqual(rapor["ack_alinan"], 5)
        self.assertEqual(v["gonderilen_bayt"], sum(len(b) for b in link.yazilan))
        self.assertEqual(v["alinan_bayt"], sum(len(a) for a in link.acklar))
        self.assertEqual((v["gonderilen_paket"], v["alinan_paket"]), (5, 5))
        self.assertGreater(v["sure_s"], 0.0)
        self.assertAlmostEqual(v["gonderilen_bayt_s"], v["gonderilen_bayt"] / v["sure_s"])
        self.assertAlmostEqual(v["alinan_paket_s"], 5 / v["sure_s"])
        self.assertEqual(v["not"], sik_rf_olc.VERI_HIZI_NOTU)

    def test_ack_yokken_alinan_sifir_gonderilen_sayilir(self):
        link = self._SahteLink(cevapla=False)
        rapor = sik_rf_olc.olc_kos(link, 3, 0.01, zaman_asimi=0.02)
        v = rapor["veri_hizi"]
        self.assertEqual(rapor["kayip"], 3)
        self.assertEqual((v["gonderilen_paket"], v["alinan_paket"], v["alinan_bayt"]), (3, 0, 0))
        self.assertEqual(v["gonderilen_bayt"], sum(len(b) for b in link.yazilan))

    def test_veri_hizi_hesapla_saf_fonksiyon(self):
        v = sik_rf_olc.veri_hizi_hesapla(2.0, 200, 100, 8, 4)
        self.assertEqual(v["gonderilen_bayt_s"], 100.0)
        self.assertEqual(v["alinan_bayt_s"], 50.0)
        self.assertEqual(v["gonderilen_bit_s"], 800.0)
        self.assertEqual(v["alinan_bit_s"], 400.0)
        self.assertEqual(v["gonderilen_paket_s"], 4.0)
        self.assertEqual(v["alinan_paket_s"], 2.0)
        sifir = sik_rf_olc.veri_hizi_hesapla(0.0, 10, 10, 1, 1)
        for ad in ("gonderilen_bayt_s", "alinan_bayt_s", "gonderilen_bit_s",
                   "alinan_bit_s", "gonderilen_paket_s", "alinan_paket_s"):
            self.assertIsNone(sifir[ad], ad)      # 0'a bolme yok, sessiz sonsuz yok
        self.assertEqual(sifir["gonderilen_bayt"], 10)

    def test_cli_arguman_kapilari(self):
        """seri icin --port, udp+olc icin --peer zorunlu (argparse cikis 2)."""
        for argv in (["--rol", "olc", "--n", "1", "--sessiz"],
                     ["--rol", "olc", "--tasiyici", "udp", "--n", "1", "--sessiz"],
                     ["--rol", "olc", "--tasiyici", "udp", "--peer", "bozuk", "--n", "1"]):
            with self.subTest(argv=argv), self.assertRaises(SystemExit) as cm:
                _main_kos(argv)
            self.assertEqual(cm.exception.code, 2, argv)


class SikRfOlcYardimcilar(unittest.TestCase):
    """Sozlesme/yordam kilitleri — kopru gerektirmez."""

    def test_esikler_sozlesmeden_okunuyor(self):
        """Madde 16: esik ciplak sayi degil, karar_sozlesmesi'nden gelir."""
        kaynak = (KOK / "scripts" / "sik_rf_olc.py").read_text(encoding="utf-8")
        self.assertIn("from karar_sozlesmesi import", kaynak)
        self.assertEqual(sik_rf_olc.VARSAYILAN_ARALIK_S, IKA_GO_TEKRAR_ARALIGI_S)
        rapor = sik_rf_olc.olc_kos.__globals__  # esik kaynagi modul globali
        self.assertIs(rapor["IKA_GO_TEKRAR_ARALIGI_S"], IKA_GO_TEKRAR_ARALIGI_S)
        self.assertIs(rapor["PARASUT_TEKRAR_ARALIGI_S"], PARASUT_TEKRAR_ARALIGI_S)

    def test_yuzdelik_en_yakin_sira(self):
        """p50/p95 nearest-rank: 20 ornekte 10. ve 19. deger; bos liste None."""
        degerler = list(range(20, 0, -1))          # 20..1 karisik sira
        self.assertEqual(sik_rf_olc.yuzdelik(degerler, 50), 10)
        self.assertEqual(sik_rf_olc.yuzdelik(degerler, 95), 19)
        self.assertEqual(sik_rf_olc.yuzdelik([7], 95), 7)
        self.assertIsNone(sik_rf_olc.yuzdelik([], 95))

    @unittest.skipIf(serial is None, "pyserial kurulu degil")
    def test_loop_url_kendi_CMD_sini_ACK_sanmaz_cokmez(self):
        """loop:// ile olc rolu kendi CMD cercevesini geri okur; ACK sayilmaz."""
        kod, cikti = _main_kos([
            "--rol", "olc", "--port", "loop://", "--n", "2",
            "--aralik", str(ARALIK_S), "--json", "--sessiz"])
        rapor = json.loads(cikti)
        self.assertEqual(rapor["gonderilen"], 2)
        self.assertEqual(rapor["ack_alinan"], 0)
        self.assertEqual(rapor["kayip_yuzde"], 100.0)
        self.assertEqual(kod, sik_rf_olc.CIKIS_OLCULEMEDI)

    def test_port_acilamazsa_OLCULEMEDI_cikis_2(self):
        """Olmayan port: arac cokmez, OLCULEMEDI koduyla doner (her iki rol)."""
        for rol in ("olc", "yanki"):
            kod, _ = _main_kos(["--rol", rol, "--port", "COM_YOK_BOYLE_BIR_PORT",
                                "--n", "1", "--sessiz"])
            self.assertEqual(kod, sik_rf_olc.CIKIS_OLCULEMEDI, rol)


if __name__ == "__main__":
    unittest.main()
