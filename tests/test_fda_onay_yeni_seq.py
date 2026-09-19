"""FDA hakem onayı: aynı şeritten YENİ seq'li OPEN_ROUTE onayı SIFIRLAMAZ.

NEDEN (mimar ölçümü, 19 Eylül): İHA (`comms/iha_sender.py` →
`protocol.open_route`, seq `itertools.count`) şeridi gördükçe ~1 Hz YENİ
seq'li OPEN_ROUTE yollar. `_mesaj_isle`'nin OPEN_ROUTE dalı her yeni seq'te
`tespit_onayli` ve `onaylandi`yı sıfırlıyordu: hakemin 1/2'si ~1 s içinde
siliniyor, 2/2'ye pratikte ulaşılamıyor, tamamlanmış onay bir sonraki karede
geri alınıyordu (§5.3.2 FDA uçuşu hakem onaysız kalırdı).

Kilitler:
  a  FDA · 1/2 → aynı şerit yeni seq → 1/2 KORUNUR → 2/2 → tek ACK, ref=yeni seq
  b  FDA · 2/2 tamam → aynı şerit yeni seq → onay korunur + ACK ref=yeni seq;
     aynı seq tekrarı ve eski seq'in geç kopyası İKİNCİ ACK üretmez
  c  FDA · şerit değişti → iki aşama sıfırlanır, ACK yok
  d  Yarışma kipi (fda_kipi False) → bugünkü sıfırlama birebir (regresyon kilidi)
  e  FDA · ankorsuz yeni seq → onay taşınmaz, ACK yok (e3/e4: geometri
     kapısı olmadan da — ankor kapısı tek başına yeter)
  f  FDA · bayat tespit → onay taşınmaz, ACK yok
  g  FDA · İHA indi → onay taşınmaz, ACK yok
  h  FDA · kanıt kaydı kilidi → onay taşınmaz, ACK yok
  i  FDA · taşınan 2/2'de asgari irtifa altı notu onay etiketini EZMEZ
  j  FDA · arada eşik altı güvenli OPEN_ROUTE → onay ASKIYA alınır, pencere
     içinde aynı şerit dönünce taşınır (askı: `test_fda_onay_askida.py`)
  k  FDA · arada NO_ROUTE → aynı askı davranışı; NO_ROUTE ACK'i ayrıca gider

Tk açılmaz, port bağlanmaz: `test_a1_hakem_ekrani_ankoru._mesaj_gui` fikstürü
+ kayıt tutan sahte link/widget'lar.

KOSUM:
  O:\\navitas-local-train\\venv\\Scripts\\python.exe -B -m unittest discover \\
      -s tests -p "test_fda_onay_yeni_seq.py"
"""

import json
import sys
import time
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
for _y in (KOK / "comms", KOK / "codes", KOK / "tests"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

import yks_gui  # noqa: E402
from karar_sozlesmesi import YKS_TESPIT_TAZELIK_S  # noqa: E402
from test_a1_hakem_ekrani_ankoru import _mesaj_gui  # noqa: E402

# Yalnız adres demeti — hiçbir yere bind EDİLMEZ (sahte link kaydeder).
IHA_ADR = ("10.0.0.7", 45001)
WAYPOINTS = [[0.0, 0.0], [0.0, 0.8], [0.0, 1.6], [0.0, 2.4]]


def _rota(seq, road=2, ref_xy=(0.0, 0.0), conf=0.9):
    return {"v": 1, "type": "OPEN_ROUTE", "seq": seq, "road": road,
            "label": {1: "sol", 2: "orta", 3: "sag"}[road], "conf": conf,
            "ref_xy": None if ref_xy is None else list(ref_xy),
            "waypoints": [list(w) for w in WAYPOINTS], "t": 0.0}


def _gui(*, fda=True, tek_rota=None):
    """`_mesaj_gui` + onay yolunun (onayla, bayatlık, kanıt) dokunduğu alanlar."""
    g = _mesaj_gui()
    g.fda_kipi = bool(fda)
    g.tek_rota = bool(fda) if tek_rota is None else bool(tek_rota)
    g.kanit_kaydi_hatasi = None
    g._kanit_kilidi_metni = None
    g.kanitlar = []
    g._kanit_yaz = lambda olay, **alanlar: g.kanitlar.append((olay, alanlar))
    g._harita_ciz = lambda: None
    g.ika_rota_ack = {}
    g._erken_ika_rota_ack = {}
    g.iha_landed_seq = None
    g.son_hb = {}
    g.tel = {"iha": {"alt": 45.0}}
    # Taze algı: GERÇEK `_tespiti_yaslandir` taze der (karar_yas < eşik).
    g.karar_yas_rx = (0.2, time.monotonic())
    return g


def _ackler(g):
    """Sahte link'e yazılan ACK çerçeveleri: [(mesaj, adres), ...]."""
    cikan = []
    for args in g.link.gonderilen:
        adr = args[1] if len(args) > 1 else None
        for satir in bytes(args[0]).decode("utf-8").splitlines():
            if satir.strip():
                m = json.loads(satir)
                if m.get("type") == "ACK":
                    cikan.append((m, adr))
    return cikan


def _bayatlat(g):
    """Algı karar yaşı eşiği aşsın → GERÇEK `_tespiti_yaslandir` BAYAT der."""
    g.karar_yas_rx = (YKS_TESPIT_TAZELIK_S + 5.0, time.monotonic())


class FdaAyniSeritYeniSeq(unittest.TestCase):

    def test_a_birinci_asama_yeni_seqte_korunur_ikinci_asama_tek_ACK(self):
        g = _gui()
        g._mesaj_isle(_rota(101), IHA_ADR)
        g.onayla()                                            # 1/2
        self.assertTrue(g.tespit_onayli)
        g._mesaj_isle(_rota(102), IHA_ADR)                    # aynı şerit
        self.assertTrue(g.tespit_onayli,
                        "aynı şeridin yeni seq'i 1/2'yi SİLDİ (saha kusuru)")
        self.assertFalse(g.onaylandi)
        self.assertEqual([], _ackler(g), "1/2 taşınırken ACK gitmemeli")
        # Düğme 2. aşamada kalmalı (gerçek `_aktarim_onay_dugmesini_kur`).
        self.assertEqual("normal", g.btn_onay.ayarlar.get("state"))
        self.assertIn("2) YKS'DE GÖRÜLDÜ", g.btn_onay.ayarlar.get("text", ""))
        self.assertTrue(any("ONAY KORUNDU" in s and "seq=102" in s
                            and "onceki 101" in s for _r, s in g.gunluk),
                        g.gunluk)
        g.onayla()                                            # 2/2
        self.assertTrue(g.onaylandi)
        ackler = _ackler(g)
        self.assertEqual(1, len(ackler), ackler)
        self.assertEqual(102, ackler[0][0]["ref"])
        self.assertEqual("OPEN_ROUTE", ackler[0][0].get("ref_tip"))
        self.assertEqual("yks", ackler[0][0].get("node"))
        self.assertEqual(IHA_ADR, ackler[0][1])

    def test_b_tamamlanmis_onay_korunur_yeni_seqe_tek_ACK(self):
        g = _gui()
        g._mesaj_isle(_rota(201), IHA_ADR)
        g.onayla()
        g.onayla()
        self.assertTrue(g.onaylandi)
        self.assertEqual([201], [m["ref"] for m, _ in _ackler(g)])
        g._mesaj_isle(_rota(202), IHA_ADR)
        self.assertTrue(g.onaylandi, "tamamlanmış onay yeni seq'te GERİ ALINDI")
        self.assertTrue(g.tespit_onayli)
        ackler = _ackler(g)
        self.assertEqual([201, 202], [m["ref"] for m, _ in ackler], ackler)
        self.assertEqual("OPEN_ROUTE", ackler[1][0].get("ref_tip"))
        self.assertEqual("yks", ackler[1][0].get("node"))
        self.assertEqual(IHA_ADR, ackler[1][1])
        self.assertEqual("disabled", g.btn_onay.ayarlar.get("state"))
        self.assertIn("ONAYLANDI", g.btn_onay.ayarlar.get("text", ""))
        self.assertIn("seq=202", g.lbl_onay.ayarlar.get("text", ""))
        self.assertTrue(any("ONAY KORUNDU" in s and "seq=202" in s
                            and "onceki 201" in s for _r, s in g.gunluk))
        # Aynı seq tekrarı (İHA tekrar penceresi) ikinci ACK üretmez.
        g._mesaj_isle(_rota(202), IHA_ADR)
        self.assertEqual(2, len(_ackler(g)), _ackler(g))
        # Eski seq'in geç kopyası da (zaten ACK'lendi) ikinci ACK üretmez.
        g._mesaj_isle(_rota(201), IHA_ADR)
        self.assertEqual(2, len(_ackler(g)), _ackler(g))
        self.assertTrue(g.onaylandi)
        # Kanıt: yeni seq'in ROTA_ALINDI satırı düşer.
        self.assertIn(202, [a.get("seq") for o, a in g.kanitlar
                            if o == "ROTA_ALINDI"])

    def test_c_serit_degisince_iki_asama_sifirlanir_ACK_yok(self):
        g = _gui()
        g._mesaj_isle(_rota(301, road=2), IHA_ADR)
        g.onayla()
        self.assertTrue(g.tespit_onayli)
        g._mesaj_isle(_rota(302, road=1), IHA_ADR)
        self.assertFalse(g.tespit_onayli)
        self.assertFalse(g.onaylandi)
        self.assertEqual([], _ackler(g))
        self.assertIn("1) TESPİTİ DOĞRULA", g.btn_onay.ayarlar.get("text", ""))
        self.assertTrue(any("SERIT DEGISTI" in s for _r, s in g.gunluk),
                        g.gunluk)

    def test_c2_tamamlanmis_onayda_serit_degisirse_ACK_yok(self):
        g = _gui()
        g._mesaj_isle(_rota(311, road=2), IHA_ADR)
        g.onayla()
        g.onayla()
        g._mesaj_isle(_rota(312, road=3), IHA_ADR)
        self.assertFalse(g.onaylandi)
        self.assertFalse(g.tespit_onayli)
        self.assertEqual([311], [m["ref"] for m, _ in _ackler(g)])

    def test_e_ankorsuz_yeni_seq_onayi_tasimaz_ACK_yok(self):
        g = _gui()
        g._mesaj_isle(_rota(501), IHA_ADR)
        g.onayla()
        g._mesaj_isle(_rota(502, ref_xy=None), IHA_ADR)
        self.assertFalse(g.tespit_onayli)
        self.assertFalse(g.onaylandi)
        self.assertEqual([], _ackler(g))
        self.assertIn("ANKOR YOK", g.btn_onay.ayarlar.get("text", ""))
        self.assertEqual("disabled", g.btn_onay.ayarlar.get("state"))

    def test_e2_tamamlanmis_onayda_ankorsuz_yeni_seq_ACK_yok(self):
        g = _gui()
        g._mesaj_isle(_rota(511), IHA_ADR)
        g.onayla()
        g.onayla()
        g._mesaj_isle(_rota(512, ref_xy=None), IHA_ADR)
        self.assertFalse(g.onaylandi)
        self.assertEqual([511], [m["ref"] for m, _ in _ackler(g)])

    def test_e3_tek_rotasiz_FDA_ankorsuz_yeni_seq_onayi_tasimaz(self):
        """`tek_rota` geometri kapısı yokken de (Tk'siz FDA fikstürü) ankor
        kapısı TEK BAŞINA taşımayı engeller — geometri kapısı ankoru gizlemez."""
        g = _gui(fda=True, tek_rota=False)
        g._mesaj_isle(_rota(521), IHA_ADR)
        g.onayla()
        self.assertTrue(g.tespit_onayli)
        g._mesaj_isle(_rota(522, ref_xy=None), IHA_ADR)
        self.assertFalse(g.tespit_onayli)
        self.assertEqual([], _ackler(g))

    def test_e4_tek_rotasiz_FDA_tam_onayda_ankorsuz_yeni_seq_ACK_yok(self):
        g = _gui(fda=True, tek_rota=False)
        g._mesaj_isle(_rota(531), IHA_ADR)
        g.onayla()
        g.onayla()
        g._mesaj_isle(_rota(532, ref_xy=None), IHA_ADR)
        self.assertFalse(g.onaylandi)
        self.assertEqual([531], [m["ref"] for m, _ in _ackler(g)])

    def test_f_bayat_tespit_yeni_seqe_ACK_gondermez(self):
        """Görev metni: `_tespiti_yaslandir` True dönerse yeni seq'e ACK yok."""
        g = _gui()
        g._mesaj_isle(_rota(601), IHA_ADR)
        g.onayla()
        g.onayla()
        self.assertEqual([601], [m["ref"] for m, _ in _ackler(g)])
        g._tespiti_yaslandir = lambda simdi=None: True
        g._mesaj_isle(_rota(602), IHA_ADR)
        self.assertEqual([601], [m["ref"] for m, _ in _ackler(g)],
                         "BAYAT tespite taşınan onayla ACK gitti")
        self.assertFalse(g.onaylandi)

    def test_f2_gercek_bayatlik_birinci_asamayi_tasimaz_dugme_kapali(self):
        g = _gui()
        g._mesaj_isle(_rota(611), IHA_ADR)
        g.onayla()
        self.assertTrue(g.tespit_onayli)
        _bayatlat(g)
        g._mesaj_isle(_rota(612), IHA_ADR)
        self.assertFalse(g.tespit_onayli)
        self.assertEqual([], _ackler(g))
        self.assertIn("BAYAT", g.btn_onay.ayarlar.get("text", ""))
        self.assertEqual("disabled", g.btn_onay.ayarlar.get("state"))
        self.assertTrue(g.tespit_bayat)

    def test_f3_gercek_bayatlik_tamamlanmis_onayi_tasimaz_ACK_yok(self):
        g = _gui()
        g._mesaj_isle(_rota(621), IHA_ADR)
        g.onayla()
        g.onayla()
        _bayatlat(g)
        g._mesaj_isle(_rota(622), IHA_ADR)
        self.assertFalse(g.onaylandi)
        self.assertEqual([621], [m["ref"] for m, _ in _ackler(g)])
        self.assertIn("BAYAT", g.btn_onay.ayarlar.get("text", ""))

    def test_g_iha_indiyse_onay_tasinmaz_ACK_yok(self):
        g = _gui()
        g._mesaj_isle(_rota(701), IHA_ADR)
        g.onayla()
        g.onayla()
        g.iha_landed_seq = 9
        g._mesaj_isle(_rota(702), IHA_ADR)
        self.assertFalse(g.onaylandi)
        self.assertEqual([701], [m["ref"] for m, _ in _ackler(g)])

    def test_h_kanit_kilidi_varken_onay_tasinmaz_ACK_yok(self):
        g = _gui()
        g._mesaj_isle(_rota(801), IHA_ADR)
        g.onayla()
        g.onayla()
        g.kanit_kaydi_hatasi = "OSError: disk dolu"
        g._mesaj_isle(_rota(802), IHA_ADR)
        self.assertFalse(g.onaylandi)
        self.assertEqual([801], [m["ref"] for m, _ in _ackler(g)])
        self.assertEqual(yks_gui.KANIT_KILIDI_ONAY_METNI,
                         g.btn_onay.ayarlar.get("text"))

    def test_j_dusuk_guven_arada_ise_onay_askidan_doner(self):
        # NEDEN: ilk sürümde (a2e69b9b) arada kayıp kare onayı SİLİYORDU;
        # mimar kararıyla FDA'da askı penceresi eklendi — beklenti değişti.
        g = _gui()
        g._mesaj_isle(_rota(1001), IHA_ADR)
        g.onayla()
        g.onayla()
        g._mesaj_isle(_rota(1002, conf=0.01), IHA_ADR)      # eşik altı
        self.assertFalse(g.onaylandi, "askıdayken bayrak açık kalmamalı")
        g._mesaj_isle(_rota(1003), IHA_ADR)                 # aynı şerit
        self.assertTrue(g.onaylandi)
        self.assertEqual([1001, 1003], [m["ref"] for m, _ in _ackler(g)
                                        if m.get("ref_tip") == "OPEN_ROUTE"])

    def test_k_NO_ROUTE_arada_ise_onay_askidan_doner(self):
        g = _gui()
        g._mesaj_isle(_rota(1101), IHA_ADR)
        g.onayla()
        g.onayla()
        g._mesaj_isle({"v": 1, "type": "NO_ROUTE", "seq": 1102,
                       "sebep": "KORIDOR_DEGIL", "detay": "test"}, IHA_ADR)
        self.assertFalse(g.onaylandi, "askıdayken bayrak açık kalmamalı")
        self.assertEqual([1102], [m["ref"] for m, _ in _ackler(g)
                                  if m.get("ref_tip") == "NO_ROUTE"])
        g._mesaj_isle(_rota(1103), IHA_ADR)
        self.assertTrue(g.onaylandi)
        self.assertEqual([1101, 1103], [m["ref"] for m, _ in _ackler(g)
                                        if m.get("ref_tip") == "OPEN_ROUTE"])

    def test_i_tasinan_tam_onayda_irtifa_notu_etiketi_ezmez(self):
        g = _gui()
        del g._irtifa_notunu_goster            # sınıftaki GERÇEK yöntem
        g._mesaj_isle(_rota(901), IHA_ADR)
        g.onayla()
        g.onayla()
        g.tel = {"iha": {"alt": 12.0}}         # §5.3.2 asgari irtifa altı
        g._mesaj_isle(_rota(902), IHA_ADR)
        self.assertTrue(g.onaylandi)
        etiket = g.lbl_onay.ayarlar.get("text", "")
        self.assertIn("seq=902", etiket)
        self.assertNotIn("BEKLENİYOR", etiket,
                         "tam onay ekranda 'onay bekleniyor' ile çelişiyor")
        self.assertTrue(any("12.0 m" in s for _r, s in g.gunluk),
                        "irtifa uyarısı günlükten de kayboldu")


class YarismaKipiRegresyonKilidi(unittest.TestCase):

    def test_d_yarisma_kipinde_yeni_seq_bugunku_gibi_sifirlar(self):
        g = _gui(fda=False)
        g._mesaj_isle(_rota(401), IHA_ADR)
        g.onayla()                                            # 1/2
        self.assertTrue(g.tespit_onayli)
        g._mesaj_isle(_rota(402), IHA_ADR)
        self.assertFalse(g.tespit_onayli)
        self.assertFalse(g.onaylandi)
        self.assertIn("1) TESPİTİ DOĞRULA", g.btn_onay.ayarlar.get("text", ""))
        self.assertFalse(any("ONAY KORUNDU" in s for _r, s in g.gunluk))

    def test_d2_yarisma_kipinde_tam_onay_yeni_seqte_sifirlanir_ACK_yok(self):
        g = _gui(fda=False)
        g._mesaj_isle(_rota(411), IHA_ADR)
        g.ika_rota_ack[411] = time.time()                    # K8 kanıtı
        g.onayla()
        g.onayla()
        self.assertTrue(g.onaylandi)
        g._mesaj_isle(_rota(412), IHA_ADR)
        self.assertFalse(g.onaylandi)
        self.assertFalse(g.tespit_onayli)
        self.assertEqual([411], [m["ref"] for m, _ in _ackler(g)])

    def test_d3_tek_rota_ama_FDA_degil_sifirlar(self):
        """`--tek-rota` (FDA'sız) yarışma kipidir: K8 kanıtı olmadan yeni
        seq'e ACK verilemez, onay taşınmaz."""
        g = _gui(fda=False, tek_rota=True)
        g._mesaj_isle(_rota(421), IHA_ADR)
        g.onayla()
        self.assertTrue(g.tespit_onayli)
        g._mesaj_isle(_rota(422), IHA_ADR)
        self.assertFalse(g.tespit_onayli)
        self.assertEqual([], _ackler(g))


if __name__ == "__main__":
    unittest.main()
