"""T210 — SÜİT SONU SÜREÇ NÖBETÇİSİ: süit başı ve sonunda nöbet portlarını dinleyen
süreç kümesi AYNI olmalı; yeni dinleyici = sızıntı → DÜŞ.

NEDEN: 7 Eylül gecesi tam süit her koşulduğunda `yks_gui.py --fda --ika
10.0.0.2:5006 …` ve `ika_nav.py comms --yks 10.0.0.1:5005` süreçleri canlı
kalıyor, UDP 5005/5006'yı tutuyor ve bir SONRAKİ süitte
`test_p8_sim_katmani.test_comms_loopback_gecer` `WinError 10013` ile düşüyordu
(kanıt: `results/gece_20260907/sizinti_surecleri_0207.txt`; kök:
`tests/test_runbook_komutlari_kosuyor.py`nin zaman aşımında yalnız doğrudan
çocuğu öldürmesi — D-427/D-430'da "ortam kusuru" sanıldı). Kökü kapatan
düzeltme `surec_nobetcisi.kos_agac_kapat`; bu dosya ise süit DÜZEYİNDE
nöbet tutar: hangi test sızdırırsa sızdırsın burada görünür.

NASIL "süit başı" ölçülür: `unittest` keşfi (`TestLoader.discover`) TÜM test
modüllerini koşumdan ÖNCE içe alır; bu modülün yüklenme anı = süit başı.
NASIL "süit sonu": keşif dosyaları `sorted()` ile sıralar; bu dosyanın adı
`tests/` altındaki `test_*.py`lerin SONUNCUSUDUR (aşağıda kilitlenir), yani
testleri en son koşar.

  N1  süit sonunda nöbet portlarında süit başında olmayan (adres, PID) YOK
  N2  nöbet portları istasyon kartından türetildi (3 uç; çıplak sabit yok)
  N3  bu dosya keşif sırasında SON — aksi hâlde "süit sonu" ölçümü yalan olur
  N4  pozitif kontrol: gerçekten açılan bir UDP soketi ölçüm aleti GÖRÜYOR
      (netstat ayrıştırıcı boş küme döndürüp sessiz geçemez)
"""

import socket
import sys
import time
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))
import surec_nobetcisi  # noqa: E402

#: Süit başı anlık görüntüsü — modül yüklenirken alınır (keşif = koşumdan önce).
SUIT_BASI = surec_nobetcisi.udp_dinleyenler()
SUIT_BASI_SAATI = time.strftime("%Y-%m-%d %H:%M:%S")

#: Kapanış gecikmesini sızıntıdan ayıran azami bekleme (s); sızıntı kalıcıdır.
PORT_SERBEST_BEKLEME_S = 5.0


class SuitSonuNobetcisi(unittest.TestCase):
    def test_N1_suit_sonunda_nobet_portlarinda_YENI_dinleyici_YOK(self):
        if SUIT_BASI is None:
            self.skipTest("netstat -ano yalnız Windows'ta ölçülür — ÖLÇÜLEMEDİ")
        son = time.monotonic() + PORT_SERBEST_BEKLEME_S
        while True:
            yeni = surec_nobetcisi.udp_dinleyenler() - SUIT_BASI
            if not yeni or time.monotonic() >= son:
                break
            time.sleep(0.25)
        rapor = [f"{adr} PID {pid}: {surec_nobetcisi.surec_komutu(pid)[:160]}"
                 for adr, pid in sorted(yeni)]
        self.assertEqual(
            [], rapor,
            f"SÜİT SÜREÇ SIZDIRDI (başı {SUIT_BASI_SAATI}, taban "
            f"{len(SUIT_BASI)} dinleyici): süit sonunda nöbet portlarında yeni "
            "UDP dinleyici var — bir sonraki süit WinError 10013 ile düşer "
            "(D-427/D-430 kökü):\n  " + "\n  ".join(rapor))

    def test_N2_nobet_portlari_istasyon_kartindan_turetildi(self):
        portlar = surec_nobetcisi.nobet_portlari()
        self.assertEqual(3, len(portlar),
                         f"YKS/İKA/İHA uçlarından 3 port beklenir: {portlar}")
        for p in portlar:
            self.assertTrue(p.isdigit() and 0 < int(p) < 65536, p)

    def test_N3_bu_dosya_kesif_sirasinda_SON(self):
        """"Süit sonu" iddiası ada dayanır; ad kilitlenmezse iddia yalan olur."""
        sonuncu = sorted(p.name for p in TESTS.glob("test_*.py"))[-1]
        self.assertEqual(Path(__file__).name, sonuncu,
                         f"nöbetçi artık en son koşmuyor; {sonuncu} ondan "
                         "sonra — nöbetçi adı ya da o dosya yeniden adlanmalı")

    def test_N4_olcum_aleti_acik_soketi_GORUYOR(self):
        """Pozitif kontrol: kendi açtığımız UDP soketi netstat'ta görünmeli."""
        if SUIT_BASI is None:
            self.skipTest("netstat -ano yalnız Windows'ta ölçülür — ÖLÇÜLEMEDİ")
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.addCleanup(s.close)
        s.bind(("127.0.0.1", 0))
        port = str(s.getsockname()[1])
        gorulen = surec_nobetcisi.udp_dinleyenler(portlar={port})
        self.assertTrue(
            any(adr.endswith(":" + port) for adr, _pid in gorulen),
            f"netstat ayrıştırıcı açık 127.0.0.1:{port} soketini GÖRMEDİ — "
            "nöbetçi kör; sızıntıyı da göremez")


if __name__ == "__main__":
    unittest.main(verbosity=2)
