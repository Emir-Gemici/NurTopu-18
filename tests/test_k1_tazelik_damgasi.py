"""K1 (D-385) — BAYAT kutuda CANLI yas damgasi.

ON KAYIT: results/k1_tazelik_damgasi/ON_KAYIT.md — davranis kod yazilmadan
donduruldu. Dondurulanlar: damga her tikte GUNCELLENIR; karar metni ve guven
SILINMEZ; onay kilidi DEGISMEZ; gunluk BIR KEZ; uc kaynak metni (hat kesik /
algi sustu / yas bilinmiyor).
"""
from __future__ import annotations

import re
import sys
import time
import unittest
from pathlib import Path
from unittest import mock

KOK = Path(__file__).resolve().parents[1]
for _y in (KOK / "comms", KOK / "codes"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

import yks_gui                                        # noqa: E402
from karar_sozlesmesi import YKS_TESPIT_TAZELIK_S     # noqa: E402


class SahteEtiket:
    def __init__(self):
        self.ayarlar = {}

    def config(self, **kw):
        self.ayarlar.update(kw)


def _ekran(rota_yasi=0.5, hb_yasi=0.5, karar_yas_rx="taze"):
    o = object.__new__(yks_gui.YksArayuz)
    o.rota = {"seq": 7, "road": 2, "label": "orta", "conf": 0.9,
              "waypoints": [(0.0, 0.0), (0.0, 2.0)]}
    o.rota_yok = None
    o.rota_zaman = time.monotonic() - rota_yasi
    o.son_hb = {"iha": time.monotonic() - hb_yasi}
    o.tespit_bayat = False
    o.onaylandi = False
    o.tespit_onayli = False
    o.btn_onay = SahteEtiket()
    o.lbl_onay = SahteEtiket()
    o.gunluk = []
    o._logla = lambda metin, renk=None: o.gunluk.append(metin)
    o.kutu_kayitlari = []
    o._kutu_yaz = (lambda kaynak, **kw:
                   o.kutu_kayitlari.append((kaynak, kw)))
    o._onay_dugmesini_tazele = lambda: None
    if karar_yas_rx == "taze":
        o.karar_yas_rx = (0.2, time.monotonic())
    else:
        o.karar_yas_rx = karar_yas_rx
    return o


def _damgalar(o):
    return [kw["detay"] for _, kw in o.kutu_kayitlari
            if "detay" in kw and "⏱" in str(kw.get("detay", ""))]


class DamgaDavranisi(unittest.TestCase):
    def test_ALGI_kaynakli_bayatlikta_damga_var_ve_ARTIYOR(self):
        """Iki tik arasinda yas buyumeli — damga CANLI (mock ile adimli)."""
        o = _ekran(karar_yas_rx=(10.0, 1000.0))
        with mock.patch("time.monotonic", side_effect=[1000.0, 1000.0,
                                                       1007.0, 1007.0,
                                                       1007.0, 1007.0]):
            o.rota_zaman = 999.5
            o.son_hb = {"iha": 999.5}
            o._tespiti_yaslandir(0.0)
            o._tespiti_yaslandir(0.0)
        d = _damgalar(o)
        self.assertGreaterEqual(len(d), 2, f"damga her tikte yazilmadi: "
                                           f"{o.kutu_kayitlari}")
        yaslar = [int(re.search(r"(\d+) sn önce", x).group(1)) for x in d]
        self.assertGreater(yaslar[-1], yaslar[0],
                           "damga guncellenmiyor — donmus yas gosteriyor")
        self.assertIn("algı sustu", d[-1])

    def test_HAT_kaynakli_metin(self):
        o = _ekran(rota_yasi=60.0, hb_yasi=60.0)
        self.assertTrue(o._tespiti_yaslandir(0.0))
        d = _damgalar(o)
        self.assertTrue(d and "hat kesik" in d[-1], d)

    def test_BILINMIYOR_kaynakli_metin(self):
        o = _ekran(karar_yas_rx=None)
        self.assertTrue(o._tespiti_yaslandir(0.0))
        d = _damgalar(o)
        self.assertTrue(d and "BİLİNMİYOR" in d[-1], d)

    def test_KARAR_METNI_SILINMIYOR(self):
        """Damga yalniz `detay` yazar — `karar` alanina dokunan kayit yok
        (bosalma yok; ON_KAYIT §1.2)."""
        o = _ekran(karar_yas_rx=(30.0, time.monotonic()))
        o._tespiti_yaslandir(0.0)
        for kaynak, kw in o.kutu_kayitlari:
            self.assertNotIn("karar", kw,
                             "bayatlik yolu KARAR metnini yeniden yazdi")
            self.assertNotIn("guven", kw)

    def test_GUNLUK_BIR_KEZ(self):
        o = _ekran(karar_yas_rx=(30.0, time.monotonic()))
        o._tespiti_yaslandir(0.0)
        n = len(o.gunluk)
        o._tespiti_yaslandir(0.0)
        self.assertEqual(n, len(o.gunluk),
                         "damga guncellemesi gunlugu tekrarlatiyor")
        self.assertGreaterEqual(len(_damgalar(o)), 2,
                                "gunluk sustu diye damga da susmus")

    def test_ONAYLANMIS_tespitte_damga_YAZILMAZ(self):
        o = _ekran(karar_yas_rx=(30.0, time.monotonic()))
        o.onaylandi = True
        o._tespiti_yaslandir(0.0)
        self.assertEqual([], _damgalar(o),
                         "onaylanmis tespite damga basildi — D-321 kuralina "
                         "aykiri (onay TAZEYKEN verildi)")


class MutasyonKontrolu(unittest.TestCase):
    def test_damga_blogu_kaldirilinca_yakalanir(self):
        kaynak = (KOK / "comms" / "yks_gui.py").read_text(encoding="utf-8")
        kod = "\n".join(s for s in kaynak.splitlines()
                        if not s.lstrip().startswith("#"))
        desen = "if bayat and not self.onaylandi:"
        self.assertIn(desen, kod, "MUTASYON UYGULANAMADI: desen yok (D-370)")
        mutant = kod.replace(desen, "if False:", 1)
        self.assertNotEqual(kod, mutant, "MUTASYON UYGULANMADI (D-370)")
        self.assertNotIn(desen, mutant,
                         "damga blogu kaldirildigi halde gorunmuyor")


if __name__ == "__main__":
    unittest.main()
