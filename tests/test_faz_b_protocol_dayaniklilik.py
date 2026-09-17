"""NEDEN (Faz B · D-405 · curutucu bulgusu "Hub sureci derin ic ice JSON
satirinda RecursionError ile OLUR"): `json.loads` derin ic ice tek satirda
(`b"["*3000 + b"\\n"`) ValueError degil RecursionError uretir; FrameReader
yalniz ValueError/UnicodeDecodeError yutuyordu. Tek satir SiK hattinin tek
erisim noktasi olan hub'i (calistir yalniz KeyboardInterrupt yakalar) ve ayni
FrameReader'i kullanan her tuketiciyi (`IhaKomutAlici.poll`) olduruyordu —
olculdu: hub sureci cikis kodu 1, stderr RecursionError.

Burada kilitlenen sey (protocol.py duzeltmesi, tuketiciler dahil):
  * ON KOSUL: bu Python'da json.loads derin satirda GERCEKTEN RecursionError
    uretir (test vakum degil);
  * FrameReader.feed derin satiri istisnasiz yutar, sonraki gecerli cerceve
    AYNI okuyucudan gecer;
  * uretim `IhaKomutAlici.poll` (UDP, mav=None) ayni datagramda yasar ve
    sonraki gecerli CMD'yi isler.

Mutasyon kontrolu (scratchpad, repoya dokunmadan): protocol.py'de
`RecursionError` except listesinden cikarilinca test_1 ve test_2 duser
(kos_protocol_mutant.py).
"""
import contextlib
import io
import inspect
import json
import sys
import unittest
from unittest.mock import patch
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
for _y in (KOK / "comms", KOK / "codes"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

from link import UDPLink  # noqa: E402
from protocol import FrameReader, command, encode  # noqa: E402

YEREL = "127.0.0.1"
# Tam, gecerli JSON: eksik kapatma parantezinin JSONDecodeError vermesine
# baglanmaz. 2002 bayt tampon tavanindan ve UDP datagram tavanindan kucuk.
DERIN_IC_ICE_DERINLIK = 1000


def _derin_satir():
    return b"[" * DERIN_IC_ICE_DERINLIK + b"0" + b"]" * DERIN_IC_ICE_DERINLIK + b"\n"


class _RecursionSiniri(unittest.TestCase):
    def setUp(self):
        onceki = sys.getrecursionlimit()
        self.addCleanup(sys.setrecursionlimit, onceki)
        sys.setrecursionlimit(500)
        # CPython 3.12 C tarayicisinin siniri sys recursion limitinden bagimsiz.
        # Gercek saf Python JSON tarayicisi ayni gecerli JSON'u deterministik
        # sinirda ayrisir; 2002 bayt UDPLink.recv(4096) icinde TAM gelir.
        decoder = json.JSONDecoder()
        decoder.scan_once = json.scanner.py_make_scanner(decoder)
        self.enterContext(patch.object(json, "_default_decoder", decoder))
        # Her davranis testi kendi on kosulunu dogrular; yalniz secilince de bos gecmez.
        with self.assertRaises(RecursionError):
            json.loads(_derin_satir())
        from protocol import CERCEVE_TAMPON_TAVANI
        self.assertLess(len(_derin_satir()), CERCEVE_TAMPON_TAVANI)


class TestVarsayilanJSON(unittest.TestCase):
    def test_eski_eksik_json_varsayilan_decoder_ile_reddedilir(self):
        # Tarihsel saldiri eksik JSON'dur: C tarayicisi/Python surumune gore
        # hata sinifi degisir; deterministik Recursion kilidi asagida ayridir.
        with self.assertRaises((json.JSONDecodeError, RecursionError)):
            json.loads(b"[" * 3000 + b"\n")


class TestFrameReaderRecursion(_RecursionSiniri):

    def test_0_on_kosul_json_loads_derin_satirda_recursion_error(self):
        """Vakum korumasi: duzeltmenin hedefi olan istisna bu Python'da
        gercekten RecursionError'dur (ValueError degil)."""
        with self.assertRaises(RecursionError):
            json.loads(_derin_satir().decode("ascii"))

    def test_1_feed_derin_satiri_yutar_sonraki_gecerli_ayni_okuyucudan_gecer(self):
        okuyucu = FrameReader()
        # istisna SIZMAZ, cerceve uretilmez
        self.assertEqual([], list(okuyucu.feed(_derin_satir())))
        self.assertEqual(b"", okuyucu._buf, "derin satir tamponda kaldi")
        mesaj = command("PARACHUTE", "iha", seq=99)
        self.assertEqual([mesaj], list(okuyucu.feed(encode(mesaj))),
                         "derin satir sonrasi gecerli cerceve gecmedi")

    def test_1b_feed_derin_satir_parcali_gelse_de_yutulur(self):
        """Seri akista satir bayt bayt gelir; istisna yalniz newline'da
        dogar — orada da yutulur, tampon temizlenir."""
        okuyucu = FrameReader()
        ham = _derin_satir()
        cikan = []
        for i in range(0, len(ham), 7):
            cikan += list(okuyucu.feed(ham[i:i + 7]))
        self.assertEqual([], cikan)
        self.assertEqual(b"", okuyucu._buf)
        mesaj = command("ARM", "iha", seq=3)
        self.assertEqual([mesaj], list(okuyucu.feed(encode(mesaj))))


class TestIhaKomutAliciDerinSatir(_RecursionSiniri):

    def test_2_iha_komut_alici_poll_derin_datagramda_yasar_sonraki_cmd_islenir(self):
        """Uretim `IhaKomutAlici` (UDP, mav=None: aktarim yok ama CMD sayilir)
        derin datagramda istisnasiz doner; sonraki PARACHUTE `cmd` sayacini
        artirir. protocol.py duzeltmesi tuketiciyi de kurtarir — alici
        kodunda degisiklik YOK."""
        from iha_komut_alici import IhaKomutAlici
        gecerli = encode(command("PARACHUTE", "iha", seq=41))
        recv_tavani = inspect.signature(UDPLink.recv).parameters["bufsize"].default
        self.assertLess(len(_derin_satir()) + len(gecerli), recv_tavani,
                        "UDP datagrami kirpilirsa Recursion savunmasi sinanmaz")
        alici_link = UDPLink(bind=(YEREL, 0), timeout=0.05)
        yks = UDPLink(bind=(YEREL, 0), timeout=0.05)
        self.addCleanup(alici_link.close)
        self.addCleanup(yks.close)
        sessiz = io.StringIO()
        with contextlib.redirect_stdout(sessiz), contextlib.redirect_stderr(sessiz):
            alici = IhaKomutAlici(alici_link, None)
            yks.send(_derin_satir(), (YEREL, alici_link.port))
            sonuc = alici.poll()                    # ISTISNA SIZMAMALI
            self.assertEqual([], sonuc)
            self.assertEqual(0, alici.sayac["cmd"])
            yks.send(gecerli, (YEREL, alici_link.port))
            sonuc = alici.poll()
        self.assertEqual(1, len(sonuc), "derin datagram sonrasi CMD islenmedi")
        self.assertEqual(1, alici.sayac["cmd"])
        self.assertEqual(0, alici.sayac["ack"], "mav=None iken ACK olmamali")


if __name__ == "__main__":
    unittest.main()
