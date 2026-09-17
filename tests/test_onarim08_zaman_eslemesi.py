"""ONARIM-08: gorev kaydini Pixhawk boot zamanina saatten bagimsiz hizalama.

Kilitler:
  1) `inis_kaniti.zaman_eslemesi(okuyucu)` son KABUL edilen GLOBAL_POSITION_INT'in
     (time_boot_ms, yerel monotonic gelis) ciftini dondurur; veri yokken None;
     yabanci sysid ve sira-disi (eski) paket eslemeyi DEGISTIRMEZ.
  2) Gorev kaydi KARE satiri `pixhawk_ms`, `pixhawk_gelis_mono`, `irtifa_m`, `armed`,
     `mod` tasir; canli saglayici yoksa hepsi None; okuyucu patlasa kosum surer.
  3) jetson_paket/kod/inis_kaniti.py kanonik kopyayla ayni.
"""
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

KOK = Path(__file__).resolve().parents[1]
for _p in (KOK / "codes", KOK / "comms", KOK / "tests"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import inis_kaniti as kanit  # noqa: E402
from test_inis_kaniti import CanliAkis, SahteSaat, _p  # noqa: E402


class ZamanEslemesi(unittest.TestCase):
    def test_veri_yokken_none_sonra_son_kabul(self):
        saat = SahteSaat(50.0)
        mav = CanliAkis([])
        ok = kanit.BagilIrtifaOkuyucu(mav, 1.0, beklenen_sysid=1, monotonic=saat)
        self.assertIsNone(kanit.zaman_eslemesi(ok))
        mav.mesajlar.append(_p(30_000, time_boot_ms=202_400))
        self.assertEqual(30.0, ok.oku())
        self.assertEqual(kanit.zaman_eslemesi(ok), (202_400, 50.0))

    def test_yabanci_ve_eski_paket_eslemeyi_degistirmez(self):
        saat = SahteSaat(10.0)
        mav = CanliAkis([_p(30_000, time_boot_ms=500)])
        ok = kanit.BagilIrtifaOkuyucu(mav, 1.0, beklenen_sysid=1, monotonic=saat)
        ok.oku()
        saat.simdi = 10.2
        mav.mesajlar.extend([_p(40_000, sysid=9, time_boot_ms=900),
                             _p(41_000, time_boot_ms=499)])
        ok.oku()
        self.assertEqual(kanit.zaman_eslemesi(ok), (500, 10.0))

    def test_paket_kopyasi_kanonikle_ayni(self):
        self.assertEqual((KOK / "comms" / "inis_kaniti.py").read_bytes(),
                         (KOK / "jetson_paket" / "kod" / "inis_kaniti.py").read_bytes())


class GorevKaydiTelemetri(unittest.TestCase):
    def test_alanlar_saglayicidan(self):
        import rpi_inference as ri
        saat = SahteSaat(77.5)
        okuyucu = kanit.BagilIrtifaOkuyucu(CanliAkis([_p(12_300, time_boot_ms=123_456)]), 1.0,
                                           beklenen_sysid=1, monotonic=saat)
        okuyucu.oku()
        okuyucu.telemetri_snapshot = lambda: {"alt": 12.3, "armed": True, "mod": "AUTO"}
        a = ri._gorev_telemetri_alanlari(SimpleNamespace(okuyucu=okuyucu))
        self.assertEqual(a, {"pixhawk_ms": 123_456, "pixhawk_gelis_mono": 77.5,
                             "irtifa_m": 12.3, "armed": True, "mod": "AUTO"})

    def test_saglayici_yok_ya_da_patlarsa_none(self):
        import rpi_inference as ri
        bos = {"pixhawk_ms": None, "pixhawk_gelis_mono": None,
               "irtifa_m": None, "armed": None, "mod": None}
        self.assertEqual(ri._gorev_telemetri_alanlari(None), bos)
        self.assertEqual(ri._gorev_telemetri_alanlari(lambda _w: 0.05), bos)

        def patla():
            raise RuntimeError("baglanti koptu")
        okuyucu = SimpleNamespace(telemetri_snapshot=patla)   # _snapshot_kilidi yok -> patlar
        self.assertEqual(ri._gorev_telemetri_alanlari(SimpleNamespace(okuyucu=okuyucu)), bos)

    def test_kare_satirinda_alanlar(self):
        import rpi_inference as ri
        from test_onarim03_gorev_kaydi import _kos, _satirlar
        with tempfile.TemporaryDirectory() as d:
            with contextlib.redirect_stdout(io.StringIO()):
                kayit = ri.gorev_kaydi_ac(Path(d) / "g")
            _kos(2, kayit)   # sahte canli_olcek = lambda (okuyucu yok)
            ri.gorev_kaydi_kapat(kayit)
            kareler = [r for r in _satirlar(kayit.yol) if r["olay"] == "KARE"]
        self.assertEqual(len(kareler), 2)
        for r in kareler:
            for alan in ("pixhawk_ms", "pixhawk_gelis_mono", "irtifa_m", "armed", "mod"):
                self.assertIn(alan, r)
                self.assertIsNone(r[alan])


if __name__ == "__main__":
    unittest.main()
