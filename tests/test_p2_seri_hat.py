"""P2 (plan v2) — SAHA TASIYICISI GERCEK BAYT AKISINDA KOSTU.

ON KAYIT: results/p2_seri/ON_KAYIT.md (S1..S7 sonuc gorulmeden yazildi).

NEDEN: `SerialLink` saha tasiyicisidir (SiK 433 MHz) ama bugune dek YALNIZ
sahte seri nesnesiyle sinandi; `pyserial` venv'de kurulu bile degildi.
D-383 §1 bunu uyarmisti: "B2-G2 GECTI yalniz UDP-loopback icindi".

UDP ile serinin farki SINIFSALDIR: UDP datagram, mesaj sinirini korur; seri
BAYT AKISIDIR, sinir yoktur. Cerceveleme (`FrameReader`, newline) bu farki
kapatmak zorunda ve gercek bir bayt akisinda hic kosmadi.

Yontem: TCP role iki `serial_for_url("socket://...")` ucunu karsilikli
pompalar — SiK'in transparan davranisinin birebir karsiligi (ON_KAYIT §3).

⚠ GERCEK RF YOKTUR (ON_KAYIT §4): menzil, paket kaybi, SiK'in kendi ECC'si ve
baud uyusmazligi burada yoktur. 433 MHz olcumu Faz B'de.
"""
import socket
import sys
import threading
import time
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
for _y in (KOK / "comms",):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

try:
    import serial
except ImportError:  # pragma: no cover - kurulum kapisi
    serial = None

from iha_sender import IhaSender  # noqa: E402
from link import SerialLink  # noqa: E402
from protocol import (CERCEVE_TAMPON_TAVANI, FrameReader, ack,  # noqa: E402
                      encode)

BAUD = 57600
ZAMAN_ASIMI_S = 0.3
COP_BOYUTU = 1024 * 1024          # ON_KAYIT S5: 1 MiB newline'siz cop
# Madde 16: tavan sozlesmeden okunur, testte yeniden yazilmaz.
TAMPON_TAVANI = CERCEVE_TAMPON_TAVANI


class SikKoprusu:
    """Iki `socket://` ucunu karsilikli pompalayan transparan seri kopru.

    SiK telsiz seffaf koprudur: bir uctan yazilan baytlar digerinden cikar.
    `boz` verilirse A->B yonune kasten cop enjekte edilir (RF gurultusu).
    """

    def __init__(self, bozucu=None):
        self._srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._srv.bind(("127.0.0.1", 0))
        self._srv.listen(2)
        self.port = self._srv.getsockname()[1]
        self._bozucu = bozucu
        self._uclar = []
        self._pompalar = []
        self._dur = threading.Event()
        self._kabul = threading.Thread(target=self._kabul_et, daemon=True)
        self._kabul.start()

    def _kabul_et(self):
        try:
            while len(self._uclar) < 2 and not self._dur.is_set():
                baglanti, _ = self._srv.accept()
                baglanti.settimeout(0.2)
                self._uclar.append(baglanti)
            if len(self._uclar) == 2:
                a, b = self._uclar
                self._pompa_baslat(a, b, bozucu=self._bozucu)
                self._pompa_baslat(b, a, bozucu=None)
        except OSError:
            pass

    def _pompa_baslat(self, kaynak, hedef, bozucu):
        def calis():
            while not self._dur.is_set():
                try:
                    veri = kaynak.recv(4096)
                except socket.timeout:
                    continue
                except OSError:
                    return
                if not veri:
                    return
                if bozucu is not None:
                    veri = bozucu(veri)
                try:
                    hedef.sendall(veri)
                except OSError:
                    return
        t = threading.Thread(target=calis, daemon=True)
        t.start()
        self._pompalar.append(t)

    def uc_ac(self):
        """Kopruye bagli GERCEK pyserial ucu (SerialLink uzerinden)."""
        return SerialLink(f"socket://127.0.0.1:{self.port}", BAUD,
                          timeout=ZAMAN_ASIMI_S)

    def kapat(self):
        self._dur.set()
        for u in self._uclar:
            try:
                u.close()
            except OSError:
                pass
        try:
            self._srv.close()
        except OSError:
            pass


def _cerceve_bekle(link, okuyucu, kosul, tavan_s=3.0):
    """Kosulu saglayan mesaj gelene dek gercek akistan oku."""
    bitis = time.monotonic() + tavan_s
    toplanan = []
    while time.monotonic() < bitis:
        veri, _ = link.recv()
        for mesaj in (okuyucu.feed(veri) if veri else []):
            toplanan.append(mesaj)
            if kosul(mesaj):
                return mesaj, toplanan
    return None, toplanan


@unittest.skipIf(serial is None, "pyserial kurulu degil")
class GercekSeriAkis(unittest.TestCase):
    """Uretim mesaj katmani GERCEK pyserial bayt akisinda."""

    def _kopru(self, bozucu=None):
        k = SikKoprusu(bozucu=bozucu)
        self.addCleanup(k.kapat)
        return k

    def _uc(self, kopru):
        link = kopru.uc_ac()
        self.addCleanup(link.close)
        return link

    # --- S1 ---
    def test_S1_mutlu_yol_turu_ACK_geliyor(self):
        """IHA OPEN_ROUTE -> IKA ACK -> gonderici ACK'i GORUYOR."""
        kopru = self._kopru()
        iha_link = self._uc(kopru)
        ika_link = self._uc(kopru)

        durduruldu = threading.Event()

        def ika_tarafi():
            """Gercek protokol: cerceveyi ayristir, gercek ACK dondur."""
            okuyucu = FrameReader()
            while not durduruldu.is_set():
                veri, _ = ika_link.recv()
                for mesaj in (okuyucu.feed(veri) if veri else []):
                    if mesaj.get("type") == "OPEN_ROUTE":
                        ika_link.send(encode(ack(mesaj["seq"], node="ika")))

        t = threading.Thread(target=ika_tarafi, daemon=True)
        t.start()
        self.addCleanup(lambda: (durduruldu.set(), t.join(timeout=1.0)))

        gonderici = IhaSender(iha_link, peers={"ika": None})
        mesaj = {"type": "OPEN_ROUTE", "seq": 1, "road": 2, "conf": 0.91}
        sonuc = gonderici._tekrarli_gonder(mesaj, repeat=8, interval=0.25)
        self.assertTrue(sonuc, "ON_KAYIT S1: gercek seri akista ACK turu "
                               "tamamlanmadi")

    # --- S2 ---
    def test_S2_bayt_bayt_parcalanma(self):
        """Mesaj 1 baytlik parcalara bolunse de tam ve birebir cikar."""
        kopru = self._kopru(bozucu=None)
        yazan = self._uc(kopru)
        okuyan = self._uc(kopru)
        mesaj = {"type": "OPEN_ROUTE", "seq": 7, "road": 1, "conf": 0.5}
        ham = encode(mesaj)
        for bayt in ham:                       # tek tek: en kotu parcalanma
            yazan.send(bytes([bayt]))
            time.sleep(0.001)
        okuyucu = FrameReader()
        gelen, _ = _cerceve_bekle(okuyan, okuyucu,
                                  lambda m: m.get("seq") == 7)
        self.assertIsNotNone(gelen, "ON_KAYIT S2: parcali mesaj toparlanmadi")
        self.assertEqual(gelen, mesaj, "ON_KAYIT S2: mesaj birebir degil")

    # --- S3 ---
    def test_S3_tek_okumada_uc_mesaj(self):
        kopru = self._kopru()
        yazan = self._uc(kopru)
        okuyan = self._uc(kopru)
        mesajlar = [{"type": "HEARTBEAT", "seq": i, "x": i} for i in (1, 2, 3)]
        yazan.send(b"".join(encode(m) for m in mesajlar))
        okuyucu = FrameReader()
        _, toplanan = _cerceve_bekle(okuyan, okuyucu,
                                     lambda m: m.get("seq") == 3)
        self.assertEqual([m.get("seq") for m in toplanan], [1, 2, 3],
                         "ON_KAYIT S3: birlesik cerceveler ayrismadi/sira bozuldu")

    # --- S4 ---
    def test_S4_bozuk_bayt_sonrasi_kurtarma(self):
        """RF gurultusu: bozuk cerceve atilir, SONRAKI gecerli cerceve okunur."""
        kopru = self._kopru()
        yazan = self._uc(kopru)
        okuyan = self._uc(kopru)
        # Bozuk cerceve (JSON degil) + hemen ardindan gecerli cerceve
        yazan.send(b"\xff\xfe bozuk cop {yanlis json\n")
        yazan.send(encode({"type": "OPEN_ROUTE", "seq": 42, "road": 3}))
        okuyucu = FrameReader()
        gelen, toplanan = _cerceve_bekle(okuyan, okuyucu,
                                         lambda m: m.get("seq") == 42)
        self.assertIsNotNone(gelen, "ON_KAYIT S4: bozuk bayttan sonra hat "
                                    "kurtarilamadi — cerceveleme kilitlendi")
        self.assertEqual(len(toplanan), 1,
                         "ON_KAYIT S4: bozuk cerceve mesaj olarak sizdi")

    # --- S6 ---
    def test_S6_serial_link_api_gercek_nesneyle(self):
        kopru = self._kopru()
        yazan = self._uc(kopru)
        okuyan = self._uc(kopru)
        self.assertIsInstance(okuyan.ser, serial.SerialBase,
                              "gercek pyserial nesnesi olmali")
        bos, adres = okuyan.recv()
        self.assertIsNone(bos, "ON_KAYIT S6: veri yokken recv None donmeli")
        self.assertIsNone(adres)
        yazan.send(b"selam\n")
        veri, _ = _bekle_veri(okuyan)
        self.assertEqual(veri, b"selam\n")

    def test_S6b_cihaz_yolu_davranisi_degismedi(self):
        """`serial_for_url` degisikligi cihaz yolu sozlesmesini bozmamali."""
        with self.assertRaises(serial.SerialException):
            SerialLink("COM_YOK_BOYLE_BIR_PORT", BAUD, timeout=0.1)


def _bekle_veri(link, tavan_s=3.0):
    bitis = time.monotonic() + tavan_s
    while time.monotonic() < bitis:
        veri, adres = link.recv()
        if veri:
            return veri, adres
    return None, None


class TamponDisiplini(unittest.TestCase):
    """S5 — cerceveleyici newline'siz akista belleği sinirsiz buyutmemeli."""

    def test_S5_newline_siz_cop_tamponu_sisirmiyor(self):
        okuyucu = FrameReader()
        kalan = COP_BOYUTU
        parca = b"A" * 4096              # newline YOK: cerceve hic tamamlanmaz
        while kalan > 0:
            list(okuyucu.feed(parca[:min(len(parca), kalan)]))
            kalan -= len(parca)
        tampon = len(okuyucu._buf)
        self.assertLessEqual(
            tampon, TAMPON_TAVANI,
            f"ON_KAYIT S5: {COP_BOYUTU} bayt newline'siz cop sonrasi ic tampon "
            f"{tampon} bayt (tavan {TAMPON_TAVANI}) — sinirsiz buyuyor")

    def test_S5c_atma_sonrasi_hat_kurtariliyor(self):
        """Cop atildiktan SONRA gelen gecerli cerceve yine okunmali."""
        okuyucu = FrameReader()
        list(okuyucu.feed(b"B" * (TAMPON_TAVANI + 1)))
        self.assertGreater(okuyucu.atilan_bayt, 0, "atma sayaci islemedi")
        self.assertEqual(len(okuyucu._buf), 0, "tampon temizlenmedi")
        cikan = list(okuyucu.feed(encode({"type": "ACK", "seq": 5})))
        self.assertEqual([m.get("seq") for m in cikan], [5],
                         "atma sonrasi hat toparlanmadi")

    def test_S5d_mesru_cerceve_pesindeki_cop_cerceveyi_yemiyor(self):
        """Newline'li gecerli cerceve + arkasindan dev cop: cerceve KAYBOLMAZ."""
        okuyucu = FrameReader()
        veri = encode({"type": "ACK", "seq": 9}) + b"C" * (TAMPON_TAVANI + 1)
        cikan = list(okuyucu.feed(veri))
        self.assertEqual([m.get("seq") for m in cikan], [9],
                         "cop, onundeki mesru cerceveyi yuttu")
        self.assertEqual(len(okuyucu._buf), 0, "arkadaki cop atilmadi")

    def test_S5b_tavan_mesru_cerceveyi_kesmiyor(self):
        """Tavan, en uzun mesru cerceveden cok buyuk olmali (on kayit gerekcesi)."""
        buyuk_rota = {"type": "OPEN_ROUTE", "seq": 1, "road": 2,
                      "waypoints": [[i, i] for i in range(200)]}
        ham = encode(buyuk_rota)
        self.assertLess(len(ham), TAMPON_TAVANI // 4,
                        "mesru cerceve tavana yaklasti — tavan yeniden "
                        "degerlendirilmeli")
        okuyucu = FrameReader()
        cikan = list(okuyucu.feed(ham))
        self.assertEqual(len(cikan), 1, "buyuk mesru cerceve ayrismali")
        self.assertEqual(cikan[0]["waypoints"][-1], [199, 199])


if __name__ == "__main__":
    unittest.main()
