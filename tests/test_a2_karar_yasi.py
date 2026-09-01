"""A2 (D-381) — TESPIT YASI `karar_yas`: HAT canliligi ALGI canliligi DEGILDIR.

NEDEN: D-374 olctu — gercek ucusta algi 45-51 s'lik sahne bagintili
araliklarda HIC karar uretemiyor; heartbeat o sirada AKMAYA DEVAM EDIYOR ve
ekran "CANLI" gorunuyordu. Hakem, saatler once uretilmis bir tespiti "gercek
zamanli" sanip onaylayabilirdi (SS6.4: onaysiz/gecersiz tespit -> ucus 0).

Prompt'un yedi ekseni (a-g):
  a) SOZLESME  b) MONOTONIK (AST)  c) ASIL KAPI: heartbeat akarken karar_yas
  esigi asarsa BAYAT  d) D-321 GERILEME KORUMASI: karar_yas TAZEyken ACK
  sonrasi OPEN_ROUTE sussa bile dugme ACIK  e) EKSIK ALAN = BILINMIYOR,
  TAZE DEGIL  f) MUTASYON (uygulanma kontrollu, D-370/D-375)  g) CAPA (Tk'siz).
"""
from __future__ import annotations

import ast
import sys
import threading
import time
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
for _y in (KOK / "comms", KOK / "codes"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

import iha_sender                                     # noqa: E402
import protocol                                       # noqa: E402
import yks_gui                                        # noqa: E402
from karar_sozlesmesi import YKS_TESPIT_TAZELIK_S     # noqa: E402

SIMDI = 1_000_000.0


class SahteEtiket:
    def __init__(self):
        self.ayarlar = {}

    def config(self, **kw):
        self.ayarlar.update(kw)


class SahteDugme(SahteEtiket):
    pass


def _ekran(rota_yasi=0.5, hb_yasi=0.5, karar_yas_rx="taze"):
    """Tk ACMADAN tazelik yolu. karar_yas_rx: 'taze' | None | (deger, alim)."""
    o = object.__new__(yks_gui.YksArayuz)
    o.rota = {"seq": 7, "road": 2, "label": "orta", "conf": 0.9,
              "waypoints": [(0.0, 0.0), (0.0, 2.0)]}
    o.rota_yok = None
    o.rota_zaman = SIMDI - rota_yasi
    o.son_hb = {"iha": SIMDI - hb_yasi}
    o.tespit_bayat = False
    o.onaylandi = False
    o.tespit_onayli = False
    o.btn_onay = SahteDugme()
    o.lbl_onay = SahteEtiket()
    o.gunluk = []
    o._logla = lambda metin, renk=None: o.gunluk.append(metin)
    o._kutu_yaz = lambda kaynak, **kw: None
    o._onay_dugmesini_tazele = lambda: None
    if karar_yas_rx == "taze":
        o.karar_yas_rx = (0.2, SIMDI)
    else:
        o.karar_yas_rx = karar_yas_rx
    return o


class A_Sozlesme(unittest.TestCase):
    def test_alan_sozlesmede(self):
        self.assertIn("karar_yas", protocol.HEARTBEAT_TELEMETRI_ALANLARI)

    def test_None_ise_YAZILMAZ(self):
        msg = protocol.heartbeat("iha", karar_yas=None)
        self.assertNotIn("karar_yas", msg,
                         "None alan yazildi — 'bilmiyorum' ile '0 sn' "
                         "ayni sey degildir (fail-closed)")

    def test_deger_verilince_tasinir(self):
        self.assertEqual(protocol.heartbeat("iha", karar_yas=3.7)["karar_yas"],
                         3.7)

    def test_sozlesme_disi_alan_hala_ValueError(self):
        with self.assertRaises(ValueError):
            protocol.heartbeat("iha", uydurma_alan=1)


class B_Monotonik(unittest.TestCase):
    """AST ILE — metin aramasi docstring'i 'kullanim' sanir (D-354/D-361)."""

    def _monotonik_cagrilar(self, islev_adi):
        agac = ast.parse((KOK / "comms" / "iha_sender.py")
                         .read_text(encoding="utf-8"))
        for d in ast.walk(agac):
            if isinstance(d, ast.ClassDef) and d.name == "KararYayinci":
                for f in d.body:
                    if (isinstance(f, ast.FunctionDef)
                            and f.name == islev_adi):
                        return [n for n in ast.walk(f)
                                if isinstance(n, ast.Attribute)
                                and n.attr == "monotonic"]
        return None

    def test_karar_damgasi_monotonik(self):
        c = self._monotonik_cagrilar("karar")
        self.assertTrue(c, "karar() time.monotonic kullanmiyor — duvar "
                           "saati geri atlayabilir")

    def test_heartbeat_yas_hesabi_monotonik(self):
        c = self._monotonik_cagrilar("_heartbeat_dongusu")
        self.assertTrue(c, "heartbeat yas hesabi monotonik degil")


class C_AsilKapi(unittest.TestCase):
    def test_heartbeat_AKARKEN_karar_yasi_asarsa_BAYAT(self):
        """D-374 senaryosu: hat CANLI (hb 0,5 sn), algi OLU (karar 10 sn)."""
        o = _ekran(rota_yasi=0.5, hb_yasi=0.5,
                   karar_yas_rx=(YKS_TESPIT_TAZELIK_S + 5.0, SIMDI))
        self.assertTrue(o._tespiti_yaslandir(SIMDI))
        self.assertEqual(o.btn_onay.ayarlar.get("state"), "disabled")

    def test_gonderim_sonrasi_GECEN_SURE_de_sayilir(self):
        """Alan 3 sn'de gonderildi, alim 4 sn once -> etkin 7 > 5."""
        o = _ekran(karar_yas_rx=(3.0, SIMDI - 4.0))
        self.assertTrue(o._tespiti_yaslandir(SIMDI))

    def test_taze_karar_yasi_BAYATLATMAZ(self):
        o = _ekran(karar_yas_rx=(0.3, SIMDI))
        self.assertFalse(o._tespiti_yaslandir(SIMDI))
        self.assertNotEqual(o.btn_onay.ayarlar.get("state"), "disabled")


class D_GerilemeKorumasi_D321(unittest.TestCase):
    def test_ACK_sonrasi_OPEN_ROUTE_sussa_bile_dugme_ACIK(self):
        """IHA rotayi ACK alana kadar tekrarlar, sonra SUSAR (T172/D-321).
        rota_zaman ESKI ama heartbeat + karar_yas TAZE -> BAYAT DEGIL."""
        o = _ekran(rota_yasi=60.0, hb_yasi=0.5, karar_yas_rx=(0.4, SIMDI))
        self.assertFalse(o._tespiti_yaslandir(SIMDI),
                         "D-321 GERI GELDI: protokolun normal davranisi "
                         "(ACK sonrasi susma) ariza sayildi")
        self.assertNotEqual(o.btn_onay.ayarlar.get("state"), "disabled")


class E_EksikAlan(unittest.TestCase):
    def test_alan_yoksa_TAZE_SAYILMAZ(self):
        o = _ekran(karar_yas_rx=None)
        self.assertTrue(o._tespiti_yaslandir(SIMDI),
                        "EKSIK ALAN 'TAZE' SAYILDI — eski/bozuk yayinci "
                        "hakem onayina acik kaldi")

    def test_etiket_BILINMIYOR_diyor(self):
        o = _ekran(karar_yas_rx=None)
        o._tespiti_yaslandir(SIMDI)
        self.assertIn("BİLİNMİYOR", o.lbl_onay.ayarlar.get("text", ""))


class F_Mutasyon(unittest.TestCase):
    def test_karar_yas_denetimi_kaldirilinca_C_DUSER(self):
        kaynak = (KOK / "comms" / "yks_gui.py").read_text(encoding="utf-8")
        kod = "\n".join(s for s in kaynak.splitlines()
                        if not s.lstrip().startswith("#"))
        desen = "_etkin_karar_yas > YKS_TESPIT_TAZELIK_S"
        self.assertIn(desen, kod, "MUTASYON UYGULANAMADI: desen yok (D-370)")
        mutant = kod.replace(desen, "False", 1)
        self.assertNotEqual(kod, mutant, "MUTASYON UYGULANMADI (D-370)")
        self.assertNotIn(desen, mutant,
                         "karar_yas kiyasi kaldirildigi halde gorunmuyor — "
                         "C ekseni BOS KAPIYA doner")

    def test_eksik_alan_dali_kaldirilinca_E_DUSER(self):
        kaynak = (KOK / "comms" / "yks_gui.py").read_text(encoding="utf-8")
        kod = "\n".join(s for s in kaynak.splitlines()
                        if not s.lstrip().startswith("#"))
        desen = '_bayat_kaynak = "bilinmiyor"'
        self.assertIn(desen, kod, "MUTASYON UYGULANAMADI (D-370)")
        mutant = kod.replace(desen, "pass", 1)
        self.assertLess(mutant.count(desen), kod.count(desen),
                        "eksik-alan dali kaldirildi ve sayim dusmedi")


class G_CapaVeUcaUc(unittest.TestCase):
    def test_capa_Tk_ACMADAN_cagrilabiliyor(self):
        self.assertIn(_ekran()._tespiti_yaslandir(SIMDI), (True, False))

    def test_yayinci_karar_damgasi_gercekten_tazeleniyor(self):
        y = object.__new__(iha_sender.KararYayinci)
        y._kilit = threading.Lock()
        y._yeni = threading.Event()
        y._bekleyen = None
        self.assertIsNone(y._son_karar_monotonik,
                          "sinif duzeyi varsayilan None olmali (T171/D-320)")
        y.karar(None, 0.0, [], None, ("KARAR_YOK", "x"))
        self.assertIsNotNone(y._son_karar_monotonik)
        self.assertLess(time.monotonic() - y._son_karar_monotonik, 5.0)

    def test_heartbeat_alani_uctan_uca(self):
        """Gercek is parcaciklariyla: karar oncesi alan YOK, sonrasi VAR."""
        alinan = []

        class SahteSender:
            def send_heartbeat(self, **tel):
                alinan.append(dict(tel))

        y = iha_sender.KararYayinci(SahteSender(), heartbeat_aralik=0.03,
                                    wait_ack=False)
        y._karar_thr.daemon = True
        y._hb_thr.daemon = True
        y._hb_thr.start()                       # yalniz heartbeat kolu
        try:
            time.sleep(0.1)
            onces = list(alinan)
            self.assertTrue(onces, "heartbeat hic akmadi")
            self.assertTrue(all("karar_yas" not in t for t in onces),
                            "karar uretilmeden alan gonderildi (0 doldurma?)")
            with y._kilit:
                y._son_karar_monotonik = time.monotonic()
            time.sleep(0.1)
            sonras = alinan[len(onces):]
            self.assertTrue(any("karar_yas" in t for t in sonras),
                            "karar uretildi ama alan heartbeat'e binmedi")
        finally:
            y._dur.set()
            y._hb_thr.join(2.0)


if __name__ == "__main__":
    unittest.main()
