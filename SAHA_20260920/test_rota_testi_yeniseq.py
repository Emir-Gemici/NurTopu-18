"""rota_testi_yeniseq.py'nin KENDI KANITI — sahte hub + sahte YKI ile cevrimdisi.

NEDEN: bir olcum araci, olcmesi gereken hatayi YAKALAYABILDIGINI kanitlamadan
sahaya goturulmez. 19 Eyl'de tam bu atlandi: eldeki rota_testi.py hep ayni seq'i
yolladigi icin D-516 hatasini goremedi ve "Test 4 GECTI" denildi.

Burada dort senaryo kosuluyor: bir SAGLAM YKI (a2e69b9b + db692109 davranisi) ve
UC MUTANT. Arac saglamda GECTI, uc mutantin hepsinde DUSTU demek ZORUNDADIR.
Mutant yakalanmazsa bu arac saha kaniti uretemez.

Kosum: python3 test_rota_testi_yeniseq.py   (~55 s, ag/donanim gerekmez)
"""
import json, os, socket, sys, threading, time, unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "comms"))
from protocol import ack, decode, encode                      # noqa: E402
import rota_testi_yeniseq as arac                              # noqa: E402

SURE = 13.0
NO_ROUTE_HER = 6
PENCERE = 3.0          # kisa kosu icin; saha on kaydi 10 s (arac uyari basar)


class SahteYKI(threading.Thread):
    """Hub + YKI yerine tek surec. Hakem 3. ve 4. OPEN_ROUTE'ta iki adima BIRER KEZ basar.

    kip:
      saglam       — yeni seq onayi silmez; NO_ROUTE askiya alir, ayni serit donunce geri gelir
      yeni_seq     — MUTANT: her yeni seq iki adimi da sifirlar (D-516'daki hata)
      no_route     — MUTANT: tek NO_ROUTE onayi kalici siler (db692109 oncesi)
      hayalet      — MUTANT: ACK'i gonderilmemis bir seq'e yazar
    """

    def __init__(self, port, kip):
        super().__init__(daemon=True)
        self.kip, self.dur = kip, threading.Event()
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.bind(("127.0.0.1", port))
        self.s.settimeout(0.1)
        self.adim, self.onayli_serit, self.ackli = 0, None, set()
        self.open_sayaci = 0

    def run(self):
        while not self.dur.is_set():
            try:
                veri, adr = self.s.recvfrom(4096)
            except socket.timeout:
                continue
            for satir in veri.split(b"\n"):
                try:
                    m = decode(satir)
                except Exception:
                    continue
                self._isle(m, adr)
        self.s.close()

    def _gonder(self, adr, seq, tip):
        self.s.sendto(encode(ack(seq, "yks", ref_tip=tip)), adr)

    def _isle(self, m, adr):
        tip = m.get("type")
        if tip == "NO_ROUTE":
            self._gonder(adr, m["seq"], "NO_ROUTE")      # sartname: otomatik ACK
            if self.kip == "no_route":
                self.adim, self.onayli_serit = 0, None   # MUTANT: kalici siler
            return
        if tip != "OPEN_ROUTE":
            return
        self.open_sayaci += 1
        if self.kip == "yeni_seq":
            self.adim, self.onayli_serit = 0, None       # MUTANT: her yeni seq sifirlar
        # hakem iki adima birer kez basar
        if self.open_sayaci == 3 and self.adim == 0:
            self.adim = 1
        elif self.open_sayaci == 4 and self.adim == 1:
            self.adim, self.onayli_serit = 2, m["road"]
        if self.adim == 2 and m["road"] == self.onayli_serit and m["seq"] not in self.ackli:
            self.ackli.add(m["seq"])
            self._gonder(adr, m["seq"] + 500000 if self.kip == "hayalet" else m["seq"],
                         "OPEN_ROUTE")


def senaryo(kip, hub_port, dinle_port):
    yki = SahteYKI(hub_port, kip)
    yki.start()
    try:
        g, a, bitis = arac.kosu(SURE, 2, 9000, NO_ROUTE_HER,
                                f"127.0.0.1:{hub_port}", dinle_port, (0.0, 0.0))
    finally:
        yki.dur.set()
        yki.join(timeout=2)
    return arac.hukum(g, a, bitis, PENCERE)


class AracKendiniKanitliyor(unittest.TestCase):

    def test_1_saglam_yki_GECTI_der(self):
        h = senaryo("saglam", 5601, 5701)
        print("\nSAGLAM:", json.dumps(h, ensure_ascii=False))
        self.assertEqual(h["sonuc"], "GECTI", h["gerekce"])
        self.assertGreaterEqual(h["yeni_seq_ack_sayisi"], 5)
        self.assertEqual(h["hayalet_ack_seq"], [])

    def test_2_mutant_yeni_seq_onayi_siliyor_YAKALANIR(self):
        h = senaryo("yeni_seq", 5602, 5702)
        print("\nMUTANT yeni_seq:", json.dumps(h, ensure_ascii=False))
        self.assertEqual(h["sonuc"], "DUSTU")
        self.assertTrue(any("OLCUT 1" in x for x in h["gerekce"]), h["gerekce"])
        self.assertEqual(h["open_route_ack"], 0)

    def test_3_mutant_no_route_onayi_siliyor_YAKALANIR(self):
        h = senaryo("no_route", 5603, 5703)
        print("\nMUTANT no_route:", json.dumps(h, ensure_ascii=False))
        self.assertEqual(h["sonuc"], "DUSTU")
        self.assertTrue(any("OLCUT 2" in x for x in h["gerekce"]), h["gerekce"])

    def test_4_mutant_hayalet_ack_YAKALANIR(self):
        h = senaryo("hayalet", 5604, 5704)
        print("\nMUTANT hayalet:", json.dumps(h, ensure_ascii=False))
        self.assertEqual(h["sonuc"], "DUSTU")
        self.assertTrue(any("OLCUT 3" in x for x in h["gerekce"]), h["gerekce"])
        self.assertTrue(h["hayalet_ack_seq"])

    def test_5_no_route_otomatik_ack_saglamda_geliyor(self):
        """NO_ROUTE'un otomatik ACK'i sayiliyor mu (sartname davranisi kaybolmasin)."""
        h = senaryo("saglam", 5605, 5705)
        self.assertGreaterEqual(h["no_route_gonderim"], 2)
        self.assertGreaterEqual(h["no_route_ack"], 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
