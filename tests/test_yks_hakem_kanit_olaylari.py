"""CONTRACTS §6.8 — YKS hakem kanıt kaydının OLAY KÜMESİ + KANIT KİLİDİ.

Bu dosya iki ÖLÇÜLEN kusurun kapısıdır. İkisi de aynı sınıftandır: hakem
ekranında GÖRÜNEN ile GERÇEK ayrışıyordu.

  A) KANIT KAYDI KİLİDİ FAIL-OPEN'DI (ölçüldü 2026-09-03).
     `_kanit_hatasini_goster` disk hatasında `kanit_kaydi_hatasi` bayrağını
     kurup KIRMIZI afiş basıyor, `btn_firlat` ile `btn_onay`u `disabled`
     yapıyordu. Ama bayrak kodda YALNIZ iki yerde okunuyordu (kendi tekrar
     koruması ve `_kanit_yaz`). Düğmeleri periyodik çizen üç yol —
     `_arm_ui_uygula`, `_onay_dugmesini_tazele`, `_aktarim_onay_dugmesini_kur`
     — bayrağa HİÇ bakmıyordu; bir tik sonra düğmeler geri açılıyor, afiş
     ekranda kalıyordu. Kilit artık düğmeleri çizen TEK yazardan
     (`_firlat_dugmesini_ciz` / `_onay_dugmesini_ciz`) okunur ve `firlatma()`
     ile `onayla()` eylemin kendisinde de reddeder.
     ⚠ NİYET KORUNUR: kilit yalnız uçuş/onay BAŞLATMA içindir. ARM/DISARM ve
     acil komutlar (RTL/LAND) kanıt kaydı bozukken de KULLANILABİLİR kalır —
     aracı indirebilmek emniyetin kendisidir.

  B) OLAY KÜMESİ SÖZLEŞMESİZDİ. Kayda yalnız `YKS_ARAYUZ_HAZIR`, `UI_OLAYI`
     ve iki döngüsel satır düşüyordu; §2.2.3 onay zincirinin ve §6.2/§5.3.2
     süre bütçesinin hiçbir olayı yoktu. Adlar koda gömülü serbest metindi
     (madde 16 ihlali). Artık tek küme `yks_gui.KANIT_OLAYLARI`'dır ve
     CONTRACTS §6.8 tablosu ↔ sabit ↔ koddan AST ile toplanan adlar ÜÇ YÖNLÜ
     birebir karşılaştırılır.

Kapılar:

  K1  UÇTAN UCA: GERÇEK `HakemKaydi` + GERÇEK geçici dosya ile üretim
      metotları koşulur; sözleşmedeki her olay (kurucununki hariç) DİSKE
      düşer, JSONL olarak geri okunur.
  K2  Zorunlu alanlar CONTRACTS §6.8 TABLOSUNDAN okunur; her satırda tam.
  K3  Ad kümesi ÜÇ YÖNLÜ birebir: CONTRACTS tablosu ↔ `yks_gui.KANIT_OLAYLARI`
      ↔ kodda `_kanit_yaz`/`_kanit_durumu_yaz`'a verilen sabit adlar.
  K4  Döngüsel olaylar (kamera/telemetri) KENAR + tekrar aralığı.
  K5  Atıl alanlar artık OKUNUYOR (kusurun kendisi).
  K6  Yazma hatası arayüzü ÖLDÜRMEZ ve 8 Hz'lik döngüde diske asılı kalmaz.
  K7  `main()` kanıt yolunu GERÇEKTEN geçirir; kurucu `YKS_ARAYUZ_HAZIR` yazar.
  A1  Kilit sonrası PERİYODİK TAZELEME düğmeleri geri AÇMAZ (fail-open kapısı).
  A2  Aynı durumda ARM ve acil komut düğmeleri KULLANILABİLİR kalır (niyet).
  A3  Kilit kendiliğinden TEMİZLENMEZ; tekrarlanan tazeleme onu açmaz.
  A4  Eylem düzeyi: `firlatma()` kronometre başlatmaz, `onayla()` link'e ACK
      YAZMAZ — düğme durumu tek savunma değildir (T180 sınıfı).
  A5  Yapısal: `btn_firlat`/`btn_onay`ın state'ini TEK yazar dışında yazan
      kod kalmadı (yeni bir yol eklenirse kapı düşer).

KOSUM:
  O:\\navitas-local-train\\venv\\Scripts\\python.exe -B -m unittest discover \\
      -s tests -p "test_yks_hakem_kanit_olaylari.py"
"""

import ast
import json
import re
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

KOK = Path(__file__).resolve().parents[1]
for _y in (KOK / "comms", KOK / "codes", KOK / "tests"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

import yks_gui  # noqa: E402
from hakem_kaydi import HakemKaydi  # noqa: E402
from protocol import ack  # noqa: E402

YKS_KAYNAK = KOK / "comms" / "yks_gui.py"
SOZLESME = KOK / "CONTRACTS.md"

# Hakem kaydının KENDİ satırları (HakemKaydi üretir; §6.8 olay kümesine dâhil
# değildir ama dosyada bulunur).
OTURUM_SATIRLARI = ("OTURUM_BASLADI", "OTURUM_BITTI")

ROTA = {"v": 1, "type": "OPEN_ROUTE", "seq": 41, "road": 2, "label": "orta",
        "conf": 0.91, "ref_xy": [0.0, 0.0],
        "waypoints": [[0.5, 4.0], [1.0, 9.0], [1.5, 14.0]]}
DUSUK_GUVEN = dict(ROTA, seq=39, conf=0.10)
YOK_ROTA = {"v": 1, "type": "NO_ROUTE", "seq": 40, "sebep": "KORIDOR_DEGIL",
            "detay": "koridor genişlik tavanı aşıldı"}
ADR = ("127.0.0.1", 5005)


# ── CONTRACTS §6.8 tablosunun okunması ───────────────────────────────────────
def _sozlesme_tablosu():
    """CONTRACTS §6.8 olay tablosunu `{olay: (zorunlu alanlar)}` olarak oku."""
    metin = SOZLESME.read_text(encoding="utf-8")
    bas = metin.index("### 6.8 Hakem kanıt kaydının OLAY KÜMESİ")
    son = metin.index("### 6.2 `road` sözleşmesi", bas)
    tablo = {}
    for satir in metin[bas:son].splitlines():
        satir = satir.strip()
        if not satir.startswith("|"):
            continue
        hucre = [h.strip() for h in satir.strip("|").split("|")]
        if len(hucre) != 3:
            continue
        olay = re.fullmatch(r"`([A-Z0-9_]+)`", hucre[0])
        if olay is None:                      # başlık ve ayraç satırları
            continue
        tablo[olay.group(1)] = tuple(re.findall(r"`([a-z0-9_]+)`", hucre[2]))
    return tablo


def _agac():
    return ast.parse(YKS_KAYNAK.read_text(encoding="utf-8"),
                     filename=str(YKS_KAYNAK))


def _koddaki_olay_adlari():
    """`_kanit_yaz` / `_kanit_durumu_yaz` çağrılarındaki SABİT olay adları."""
    adlar = set()
    for dugum in ast.walk(_agac()):
        if (isinstance(dugum, ast.Call)
                and isinstance(dugum.func, ast.Attribute)
                and dugum.func.attr in ("_kanit_yaz", "_kanit_durumu_yaz")
                and dugum.args
                and isinstance(dugum.args[0], ast.Constant)
                and isinstance(dugum.args[0].value, str)):
            adlar.add(dugum.args[0].value)
    return adlar


# ── Tk'siz üretim fikstürü ───────────────────────────────────────────────────
class _SahteWidget:
    """`config`/`cget` sözleşmesinin en küçük taklidi (Tk açılmaz)."""

    def __init__(self, **ayarlar):
        self.ayarlar = dict(ayarlar)
        self.satirlar = []

    def config(self, **ayarlar):
        self.ayarlar.update(ayarlar)

    def cget(self, ad):
        return self.ayarlar.get(ad)

    def insert(self, *args):
        self.satirlar.append(args)

    def see(self, *_args):
        pass


class _SahteKamera:
    """`KameraIstemci.snapshot()` sözleşmesinin küçük, JPEG'siz taklidi."""

    def __init__(self, durum, hata=None, yas=0.4):
        self.durum, self.hata, self.yas = durum, hata, yas

    def snapshot(self):
        return {"surum": 1, "jpeg": None, "durum": self.durum,
                "hata": self.hata, "kare_yasi_s": self.yas, "kare_sira": 7,
                "calisiyor": True,
                "kaynak": "http://127.0.0.1:8080/kare.jpg"}


DUGMELER = ("btn_onay", "lbl_onay", "btn_firlat", "btn_iha_indi", "btn_ika_go",
            "lbl_ika_go", "btn_hb", "btn_alan", "btn_hazir", "btn_mudahale",
            "btn_arm", "lbl_arm", "btn_rtl", "btn_land", "lbl_acil",
            "lbl_ceza", "lbl_saat", "lbl_sayac", "lbl_kron_iha",
            "lbl_kron_ika", "lbl_kron_haz", "lbl_gps", "lbl_kamera_img",
            "lbl_kamera_bilgi")

# Ekran/karar yolları bu kapının konusu değil: mock'lanır. `_logla` BİLEREK
# gerçek bırakılır — `UI_OLAYI` (Codex'in çalışan bağlantısı) da §6.8
# kümesinin parçasıdır ve uçtan uca ölçülmelidir.
MOCKLANAN = ("_zincir", "_ucus", "_ucus_normal", "_harita_ciz", "_rota_analiz",
             "_kutu_yaz", "_irtifa_notunu_goster", "_algi_iste", "_inset_ciz",
             "_kutu_ciz")


def _arayuz(yol, *, kamera_url=None, gercek_ui=False):
    """Kurucuyu (Tk ister) atlayarak kanıt yollarının dokunduğu alanları kur.

    `gercek_ui=True` iken düğme çizen yollar (`_arm_ui_uygula`,
    `_acil_ui_uygula`, `_onay_dugmesini_tazele`, `_aktarim_onay_dugmesini_kur`)
    GERÇEK koşar — kanıt kilidi kapıları tam olarak orayı ölçer.
    """
    g = object.__new__(yks_gui.YksArayuz)
    g.hakem_kaydi = HakemKaydi(yol) if yol is not None else None
    g.kanit_kaydi_hatasi = None
    g._kanit_kilidi_metni = None
    g._kamera_kanit_durumu = None
    g._son_kamera_kanit_monotonic = None
    g._telemetri_kanit_durumu = None
    g._son_telemetri_kanit_monotonic = None

    g.link = mock.Mock()
    g.link.send = mock.Mock(return_value=None)
    g.kok = mock.Mock()
    g.demo = True
    g.otomatik_onay = False
    g.fda_kipi = False
    g.son_adr = {}
    g.sabit_adr = {}
    g.demo_durum = {"iha_hb": True, "ika_hb": True, "iha_bat": True,
                    "iha_gnss": True, "iha_algi": True}

    g.rota = None
    g.rota_yok = None
    g.rota_adr = None
    g.rota_zaman = None
    g.tespit_bayat = False
    g.onaylandi = False
    g.tespit_onayli = False
    g.iha_landed_seq = None
    g.ika_rota_ack = {}
    g.rx_alim = {}
    g.karar_yas_rx = None
    g.son_hb = {}
    g.tel = {}
    g.mod = {}
    g.iha_iz = []
    g._detay_base = ""
    g.sayac = {k: 0 for k in ("OPEN_ROUTE", "OPEN_ROUTE_RED", "NO_ROUTE",
                              "IHA_LANDED", "HEARTBEAT", "ACK_TX")}
    g.t_iha0 = g.t_iha1 = g.t_ika0 = g.t_ika1 = None
    g.t_haz0 = g.t_haz1 = None
    g.ceza_toplam = 0
    g.arm_acik = True
    g.arm_bekleyen_komut = None
    g.acil_bekleyen_komut = None
    g._kritik_teyit = {}
    g.gorunum_adi = "algi"          # `_inset_ciz` yolunu açma

    g.kamera_url = kamera_url
    g.kamera_istemci = None
    g._kamera_surum = -1
    g._kamera_foto = None

    for ad in MOCKLANAN:
        setattr(g, ad, mock.Mock())
    if not gercek_ui:
        for ad in ("_aktarim_onay_dugmesini_kur", "_arm_ui_uygula",
                   "_acil_ui_uygula"):
            setattr(g, ad, mock.Mock())
    g._tespiti_yaslandir = mock.Mock(return_value=False)
    g._iha_havada_mi = mock.Mock(return_value=True)
    g._arm_durumu_taze_mi = mock.Mock(return_value=True)
    g.ika_go_tekrar = mock.Mock()
    g.ika_go_tekrar.ack_geldi.return_value = False
    g.ika_go_tekrar.baslat.return_value = True
    g.parasut_tekrar = mock.Mock()
    g.parasut_tekrar.mesaj = None

    g.gunluk = _SahteWidget(state="disabled")
    for ad in DUGMELER:
        setattr(g, ad, _SahteWidget(text="", state="normal"))
    g.lbl_dugum = {"iha": (_SahteWidget(), _SahteWidget()),
                   "ika": (_SahteWidget(), _SahteWidget())}
    return g


def _satirlar(yol):
    return [json.loads(s) for s in
            Path(yol).read_text(encoding="utf-8").strip().splitlines()]


def _tam_akis(g):
    """Üretim metotlarını GERÇEKTEN koş: her §6.8 olayı bir kez üretilsin."""
    # 1) eşik altı OPEN_ROUTE → ROTA_REDDEDILDI (ACK üretilmez)
    g._mesaj_isle(dict(DUSUK_GUVEN), ADR)
    g.rota_yok = None
    # 2) NO_ROUTE → ROTA_YOK
    g._mesaj_isle(dict(YOK_ROTA), ADR)
    g.rota_yok = None
    # 3) geçerli OPEN_ROUTE → ROTA_ALINDI
    g._mesaj_isle(dict(ROTA), ADR)
    # 4) hakem 1/2 → HAKEM_ONAYI_1
    g.onayla()
    # 5) 2/2 kanıtsız → HAKEM_ONAYI_REDDI (fail-closed)
    g.onayla()
    # 6) İKA ACK → ACK_ALINDI + IKA_AKTARIM_KANITI
    g._ack_isle(ack(ROTA["seq"], "ika", "OPEN_ROUTE"), ("127.0.0.1", 5006))
    # 7) 2/2 onay → HAKEM_ONAYI_2 (ACK link'e yazıldıktan SONRA)
    g.onayla()
    # 8) hazırlık kronometresi + müdahale (devam=True)
    g.alan_girisi()
    g.takim_hazir()
    g.mudahale()
    # 9) İHA kronometresi: fırlatma → gerçek IHA_LANDED çerçevesi iniş yazar
    g.firlatma()
    g._mesaj_isle({"v": 1, "type": "IHA_LANDED", "node": "iha", "seq": 25}, ADR)
    # 10) İKA kronometresi
    g.ika_baslat()
    g.hb_temas()
    # 11) acil durum tatbikatı
    g.senaryo("rc")
    # 12) kamera kanıt durumu (URL yok → YAPILANDIRILMADI)
    g._kamera_tazele()
    # 13) telemetri tazelik özeti
    g.son_hb["iha"] = time.monotonic()
    g.tel["iha"] = {"alt": 31.0, "lat": 37.7, "lon": 38.2, "gps_fix": 3}
    g._durum_tazele()
    # 14) ONARIM-09: coklu tasiyicida LAN hattinin TAZE -> KOPUK gecisi -> HAT_DURUMU
    yaslar = iter([{"lan": 0.4, "sik": None}, {"lan": 9.0, "sik": None}])
    g.link = mock.Mock()
    g.link.hat_yaslari.side_effect = lambda: next(yaslar)
    g.lbl_hatlar = _SahteWidget()
    g._hat_durum_onceki = {}
    g._hatlari_tazele()
    g._hatlari_tazele()


class UctanUcaDiskeYazar(unittest.TestCase):
    """K1/K2/K5 — gerçek dosya, gerçek metotlar."""

    def setUp(self):
        self._gecici = tempfile.TemporaryDirectory()
        self.yol = Path(self._gecici.name) / "hakem_log.jsonl"
        self.g = _arayuz(self.yol)
        _tam_akis(self.g)
        self.g.hakem_kaydi.kapat()
        self.kayitlar = _satirlar(self.yol)

    def tearDown(self):
        self._gecici.cleanup()

    def test_K1_sozlesmedeki_her_olay_diske_dustu(self):
        uretilen = {k["olay"] for k in self.kayitlar} - set(OTURUM_SATIRLARI)
        beklenen = set(yks_gui.KANIT_OLAYLARI) - {"YKS_ARAYUZ_HAZIR"}
        self.assertEqual(beklenen, uretilen,
                         f"eksik: {sorted(beklenen - uretilen)} · "
                         f"fazla: {sorted(uretilen - beklenen)}")
        self.assertIsNone(self.g.kanit_kaydi_hatasi)
        # Dosya GERÇEKTEN diskte ve oturum kapanışı yazılı (yarım kayıt değil)
        self.assertTrue(self.yol.is_file())
        self.assertEqual("OTURUM_BASLADI", self.kayitlar[0]["olay"])
        self.assertEqual("OTURUM_BITTI", self.kayitlar[-1]["olay"])

    def test_K2_zorunlu_alanlar_sozlesme_tablosundan_tam(self):
        tablo = _sozlesme_tablosu()
        self.assertEqual(set(yks_gui.KANIT_OLAYLARI), set(tablo),
                         "CONTRACTS §6.8 tablosu ile KANIT_OLAYLARI ayrıştı")
        for kayit in self.kayitlar:
            olay = kayit["olay"]
            if olay in OTURUM_SATIRLARI:
                continue
            with self.subTest(olay=olay):
                eksik = [a for a in tablo[olay] if a not in kayit]
                self.assertEqual([], eksik, f"{olay} satırında eksik: {eksik}")
                for ortak in ("v", "ts", "monotonic_s", "oturum"):
                    self.assertIn(ortak, kayit)

    def test_K2b_onay_zinciri_alanlari_gercek_degerleri_tasir(self):
        olaylar = {k["olay"]: k for k in self.kayitlar}
        self.assertEqual(ROTA["seq"], olaylar["ROTA_ALINDI"]["seq"])
        self.assertEqual(ROTA["road"], olaylar["ROTA_ALINDI"]["road"])
        self.assertEqual(3, olaylar["ROTA_ALINDI"]["waypoint"])
        self.assertIs(True, olaylar["ROTA_ALINDI"]["ankor"])
        self.assertEqual("IKA_ACK_KANITI_YOK",
                         olaylar["HAKEM_ONAYI_REDDI"]["sebep"])
        self.assertEqual("OPEN_ROUTE", olaylar["ACK_ALINDI"]["ref_tip"])
        self.assertEqual(ROTA["seq"], olaylar["IKA_AKTARIM_KANITI"]["seq"])
        self.assertEqual("OPEN_ROUTE", olaylar["HAKEM_ONAYI_2"]["ref_tip"])
        self.assertIs(False, olaylar["HAKEM_ONAYI_2"]["fda_kipi"])
        self.assertEqual(25, olaylar["IHA_INIS_KANITI"]["seq"])
        self.assertIs(True, olaylar["IHA_INIS_KANITI"]["ika_rota_ack_var"])
        self.assertEqual("rc", olaylar["ACIL_SENARYO"]["kod"])
        self.assertEqual("YAPILANDIRILMADI", olaylar["KAMERA_KANIT"]["durum"])
        self.assertEqual("iha=TAZE·ika=YOK",
                         olaylar["TELEMETRI_KANIT"]["durum"])
        self.assertEqual(["ika"], olaylar["TELEMETRI_KANIT"]["bayat"])
        # Codex'in ayrıntılı örneği KORUNDU: özet satırı ham telemetriyi de taşır
        self.assertIn("telemetri", olaylar["TELEMETRI_KANIT"]["dugumler"]["iha"])
        self.assertEqual(
            31.0,
            olaylar["TELEMETRI_KANIT"]["dugumler"]["iha"]["telemetri"]["alt"])
        # Kronometrelerin ÜÇÜ de kayıtta; müdahale `devam=True` ile ayrışır
        baslangic = [k for k in self.kayitlar
                     if k["olay"] == "KRONOMETRE_BASLADI"]
        self.assertEqual(["hazirlik", "hazirlik", "iha", "ika"],
                         sorted(k["kron"] for k in baslangic))
        self.assertEqual(
            [True], [k["devam"] for k in baslangic if k["devam"]])
        bitis = [k for k in self.kayitlar if k["olay"] == "KRONOMETRE_BITTI"]
        self.assertEqual(["hazirlik", "iha", "ika"],
                         sorted(k["kron"] for k in bitis))

    def test_K2c_UI_OLAYI_gunluk_satirlarini_kayda_bagliyor(self):
        """Codex'in çalışan bağlantısı korundu: ekrandaki her satır kayıtta."""
        ui = [k for k in self.kayitlar if k["olay"] == "UI_OLAYI"]
        self.assertTrue(ui, "günlük satırları kayda hiç düşmedi")
        self.assertTrue(any("HAKEM 1/2" in k["mesaj"] for k in ui))
        self.assertTrue(all("seviye" in k for k in ui))

    def test_K5_atil_alanlar_artik_okunuyor(self):
        # Kusurun kendisi: dört alan kuruluyor ama hiç okunmuyordu.
        self.assertEqual("YAPILANDIRILMADI", self.g._kamera_kanit_durumu)
        self.assertIsNotNone(self.g._son_kamera_kanit_monotonic)
        self.assertEqual("iha=TAZE·ika=YOK", self.g._telemetri_kanit_durumu)
        self.assertIsNotNone(self.g._son_telemetri_kanit_monotonic)


class AdKumesiUcYonluKilit(unittest.TestCase):
    """K3 — sözleşme ↔ sabit ↔ kod aynı kümeyi taşımalı."""

    def test_K3_sozlesme_sabit_ve_kod_birebir(self):
        tablo = set(_sozlesme_tablosu())
        sabit = set(yks_gui.KANIT_OLAYLARI)
        kod = _koddaki_olay_adlari()
        self.assertEqual(tablo, sabit,
                         f"CONTRACTS↔sabit farkı: {tablo ^ sabit}")
        self.assertEqual(sabit, kod, f"sabit↔kod farkı: {sabit ^ kod}")
        self.assertEqual(len(yks_gui.KANIT_OLAYLARI), len(sabit),
                         "KANIT_OLAYLARI'nda yinelenen ad var")

    def test_K3b_kurucu_YKS_ARAYUZ_HAZIR_yazar(self):
        """Tk'siz de ölçülebilen kısım: çağrı `__init__` gövdesinde duruyor."""
        kurucu = next(
            d for s in ast.walk(_agac()) if isinstance(s, ast.ClassDef)
            and s.name == "YksArayuz"
            for d in s.body
            if isinstance(d, ast.FunctionDef) and d.name == "__init__")
        adlar = {c.args[0].value for c in ast.walk(kurucu)
                 if isinstance(c, ast.Call)
                 and isinstance(c.func, ast.Attribute)
                 and c.func.attr == "_kanit_yaz" and c.args
                 and isinstance(c.args[0], ast.Constant)}
        self.assertEqual({"YKS_ARAYUZ_HAZIR"}, adlar)

    def test_K3c_tek_kanit_yazma_yolu_var(self):
        """Birleştirme artığı kapısı: iki `_kanit_yaz` tanımı bırakılamaz."""
        sinif = next(s for s in ast.walk(_agac())
                     if isinstance(s, ast.ClassDef) and s.name == "YksArayuz")
        sayim = {}
        for d in sinif.body:
            if isinstance(d, ast.FunctionDef):
                sayim[d.name] = sayim.get(d.name, 0) + 1
        for ad in ("_kanit_yaz", "_kanit_durumu_yaz", "_kanit_hatasini_goster",
                   "_firlat_dugmesini_ciz", "_onay_dugmesini_ciz"):
            self.assertEqual(1, sayim.get(ad, 0), f"{ad} tanımı 1 değil")


class DongusselOlaylarKenarVeTekrar(unittest.TestCase):
    """K4/K6 — `_tik` 8 Hz koşar; her tikte fsync Tk'yı diske bağlar."""

    def setUp(self):
        self._gecici = tempfile.TemporaryDirectory()
        self.yol = Path(self._gecici.name) / "hakem_log.jsonl"
        self.g = _arayuz(self.yol)

    def tearDown(self):
        try:
            self.g.hakem_kaydi.kapat()
        except Exception:
            pass
        self._gecici.cleanup()

    def _kamera_olaylari(self):
        return [k for k in _satirlar(self.yol) if k["olay"] == "KAMERA_KANIT"]

    def test_K4_ayni_durum_araliktan_once_IKINCI_satiri_yazmaz(self):
        self.g._kamera_tazele()
        self.assertEqual(1, len(self._kamera_olaylari()))
        self.assertIs(True, self._kamera_olaylari()[0]["degisim"])
        for _ in range(40):                    # 5 saniyelik `_tik` yükü
            self.g._kamera_tazele()
        self.assertEqual(1, len(self._kamera_olaylari()),
                         "aralık dolmadan tekrar yazıldı — 8 Hz fsync")

    def test_K4b_aralik_dolunca_degisim_false_ile_bir_kez_daha(self):
        self.g._kamera_tazele()
        # Damgayı GERİYE al: tekrar aralığı dolmuş sayılır (monotonik saat).
        self.g._son_kamera_kanit_monotonic -= (
            yks_gui.KANIT_TEKRAR_ARALIGI_S + 1.0)
        self.g._kamera_tazele()
        olaylar = self._kamera_olaylari()
        self.assertEqual(2, len(olaylar))
        self.assertIs(False, olaylar[1]["degisim"],
                      "süreklilik satırı geçiş gibi görünüyor")
        self.assertEqual(olaylar[0]["durum"], olaylar[1]["durum"])

    def test_K4c_durum_degisince_ARALIK_BEKLENMEDEN_yazilir(self):
        self.g._kamera_tazele()                       # YAPILANDIRILMADI
        self.g.kamera_istemci = _SahteKamera("BAGLANAMADI", hata="timeout")
        self.g._kamera_tazele()                       # kenar: hemen
        olaylar = self._kamera_olaylari()
        self.assertEqual(2, len(olaylar))
        self.assertEqual("YAPILANDIRILMADI", olaylar[0]["durum"])
        self.assertEqual("BAGLANAMADI·KARE_YOK", olaylar[1]["durum"])
        self.assertIs(True, olaylar[1]["degisim"])
        self.assertIn("timeout", olaylar[1]["hata"])
        self.assertEqual(7, olaylar[1]["kare_sira"])

    def test_K6_yazma_hatasi_oldurmez_ve_damga_ILERLER(self):
        bozuk = mock.Mock()
        bozuk.yaz.side_effect = OSError("disk dolu")
        self.g.hakem_kaydi.kapat()             # gerçek tutamacı sızdırma
        self.g.hakem_kaydi = bozuk
        with mock.patch("builtins.print"):
            self.g._kamera_tazele()            # yükseltmemeli
            damga = self.g._son_kamera_kanit_monotonic
            self.assertIsNotNone(damga)
            self.assertIn("disk dolu", self.g.kanit_kaydi_hatasi)
            self.g._kamera_tazele()
        # Damga ilerlediği için hata hâlinde 8 Hz yeniden denenmez.
        self.assertEqual(damga, self.g._son_kamera_kanit_monotonic)
        self.assertEqual(1, bozuk.yaz.call_count)


class KanitKaydiKilidi(unittest.TestCase):
    """A1–A4 — ölçülen fail-open: kilit bir tik sonra kalkıyordu."""

    def setUp(self):
        self.g = _arayuz(None, gercek_ui=True)
        bozuk = mock.Mock()
        bozuk.yaz.side_effect = OSError("disk dolu")
        self.g.hakem_kaydi = bozuk
        # Kilidi GERÇEK yoldan kur: bir kanıt yazma denemesi diske düşemiyor.
        with mock.patch("builtins.print"):
            self.g._logla("kilit tetikleyici", "mavi")
        self.assertIn("disk dolu", self.g.kanit_kaydi_hatasi)

    def _tazele(self, kere=3):
        """Periyodik çizim yollarını GERÇEKTEN koş (eski fail-open kapısı)."""
        self.g.rota = dict(ROTA)
        self.g.rota_yok = None
        self.g.onaylandi = False
        for _ in range(kere):
            self.g._arm_ui_uygula()            # btn_firlat'ı çizer
            self.g._onay_dugmesini_tazele()    # btn_onay 1. aşama
            self.g.tespit_onayli = True
            self.g.ika_rota_ack[ROTA["seq"]] = time.time()
            self.g._aktarim_onay_dugmesini_kur()   # btn_onay 2. aşama
            self.g.tespit_onayli = False
            self.g._acil_ui_uygula()

    def test_A1_periyodik_tazeleme_dugmeleri_GERI_ACMAZ(self):
        self.assertEqual("disabled", self.g.btn_firlat.cget("state"))
        self.assertEqual("disabled", self.g.btn_onay.cget("state"))
        self._tazele()
        self.assertEqual("disabled", self.g.btn_firlat.cget("state"),
                         "FIRLATMA tazelemeden sonra geri açıldı (fail-open)")
        self.assertEqual("disabled", self.g.btn_onay.cget("state"),
                         "ONAY tazelemeden sonra geri açıldı (fail-open)")
        # Ekranla gerçek AYRIŞMASIN: düğme metni ve afiş kilidi söylüyor.
        self.assertEqual(yks_gui.KANIT_KILIDI_FIRLAT_METNI,
                         self.g.btn_firlat.cget("text"))
        self.assertEqual(yks_gui.KANIT_KILIDI_ONAY_METNI,
                         self.g.btn_onay.cget("text"))
        self.assertIn("KANIT KAYDI HATASI", self.g.lbl_onay.cget("text"))
        self.assertEqual(yks_gui.KIRMIZI, self.g.lbl_onay.cget("fg"))

    def test_A2_ARM_ve_ACIL_dugmeleri_KULLANILABILIR_kalir(self):
        """NİYET KORUNUR: kanıt kaydı bozukken de araç indirilebilmeli."""
        self._tazele()
        self.assertEqual("normal", self.g.btn_arm.cget("state"),
                         "kilit ARM'a taştı — araç ARM/DISARM edilemez oldu")
        self.assertEqual("normal", self.g.btn_rtl.cget("state"),
                         "kilit acil RTL'e taştı")
        self.assertEqual("normal", self.g.btn_land.cget("state"),
                         "kilit acil LAND'e taştı")

    def test_A3_kilit_kendiliginden_TEMIZLENMEZ(self):
        self._tazele(kere=25)                  # ~3 saniyelik `_tik` yükü
        self.assertIsNotNone(self.g.kanit_kaydi_hatasi)
        self.assertTrue(self.g._kanit_kilidi_var())
        self.assertEqual("disabled", self.g.btn_firlat.cget("state"))
        self.assertEqual("disabled", self.g.btn_onay.cget("state"))

    def test_A4a_firlatma_KRONOMETRE_BASLATMAZ(self):
        """Düğme durumu tek savunma değildir: doğrudan çağrı da reddedilir."""
        self.g.firlatma()
        self.assertIsNone(self.g.t_iha0,
                          "kanıtsız uçuş kronometresi başladı")
        self.assertEqual("disabled", self.g.btn_firlat.cget("state"))

    def test_A4b_onayla_LINKE_ACK_YAZMAZ(self):
        self.g.rota = dict(ROTA)
        self.g.rota_adr = ADR
        self.g.tespit_onayli = True            # 2/2 aşamasına kurulu
        self.g.ika_rota_ack[ROTA["seq"]] = time.time()
        self.g.onayla()
        self.assertFalse(self.g.onaylandi, "kanıtsız hakem onayı verildi")
        self.g.link.send.assert_not_called()

    def test_A4c_kilit_YOKKEN_ayni_akis_CALISIR(self):
        """Mutasyonun ters yönü: kilit her şeyi kapatan bir taş değil."""
        with tempfile.TemporaryDirectory() as d:
            g = _arayuz(Path(d) / "h.jsonl", gercek_ui=True)
            g.rota = dict(ROTA)
            g.rota_adr = ADR
            g.tespit_onayli = True
            g.ika_rota_ack[ROTA["seq"]] = time.time()
            g.onayla()
            g.firlatma()
            g.hakem_kaydi.kapat()
            self.assertTrue(g.onaylandi)
            g.link.send.assert_called()
            self.assertIsNotNone(g.t_iha0)


class DugmeTekYazarKilidi(unittest.TestCase):
    """A5 — kilit ancak TEK yazar varsa tutar; yeni bir yol kapıyı düşürür."""

    YAZARLAR = {"_firlat_dugmesini_ciz", "_onay_dugmesini_ciz"}

    def _state_yazan_metotlar(self, dugme):
        """`<dugme>.config(state=...)` çağrısını içeren metot adlarını bul."""
        bulunan = set()
        sinif = next(s for s in ast.walk(_agac())
                     if isinstance(s, ast.ClassDef) and s.name == "YksArayuz")
        for metot in sinif.body:
            if not isinstance(metot, ast.FunctionDef):
                continue
            for c in ast.walk(metot):
                if not (isinstance(c, ast.Call)
                        and isinstance(c.func, ast.Attribute)
                        and c.func.attr == "config"):
                    continue
                if not any(k.arg == "state" for k in c.keywords):
                    continue
                hedef = c.func.value
                # `self.btn_x.config(...)` ve yerel `btn = self.btn_x` sonrası
                # `btn.config(...)` — ikisini de yakala.
                ad = None
                if (isinstance(hedef, ast.Attribute)
                        and isinstance(hedef.value, ast.Name)
                        and hedef.value.id == "self"):
                    ad = hedef.attr
                elif isinstance(hedef, ast.Name):
                    ad = _yerel_kaynak(metot, hedef.id)
                if ad == dugme:
                    bulunan.add(metot.name)
        return bulunan

    def test_A5_btn_firlat_state_yazari_TEK(self):
        self.assertEqual({"_firlat_dugmesini_ciz"},
                         self._state_yazan_metotlar("btn_firlat"))

    def test_A5b_btn_onay_state_yazari_TEK(self):
        self.assertEqual({"_onay_dugmesini_ciz"},
                         self._state_yazan_metotlar("btn_onay"))


def _yerel_kaynak(metot, ad):
    """`ad = self.btn_x` / `ad = getattr(self, "btn_x", ...)` kaynağını çöz."""
    for d in ast.walk(metot):
        if not (isinstance(d, ast.Assign) and len(d.targets) == 1
                and isinstance(d.targets[0], ast.Name)
                and d.targets[0].id == ad):
            continue
        kaynak = d.value
        if (isinstance(kaynak, ast.Attribute)
                and isinstance(kaynak.value, ast.Name)
                and kaynak.value.id == "self"):
            return kaynak.attr
        if (isinstance(kaynak, ast.Call)
                and isinstance(kaynak.func, ast.Name)
                and kaynak.func.id == "getattr"
                and len(kaynak.args) >= 2
                and isinstance(kaynak.args[0], ast.Name)
                and kaynak.args[0].id == "self"
                and isinstance(kaynak.args[1], ast.Constant)):
            return kaynak.args[1].value
    return None


class MainKanitYolunuGecirir(unittest.TestCase):
    """K7 — `main()` kanıt yolunu GERÇEKTEN geçirmeli."""

    def test_K7_main_kurucuya_hakem_log_yolu_verir(self):
        ana = next(d for d in ast.walk(_agac())
                   if isinstance(d, ast.FunctionDef) and d.name == "main")
        cagrilar = [c for c in ast.walk(ana) if isinstance(c, ast.Call)
                    and isinstance(c.func, ast.Name)
                    and c.func.id == "YksArayuz"]
        self.assertEqual(1, len(cagrilar), "main() YksArayuz'u bir kez kurar")
        anahtarlar = {k.arg for k in cagrilar[0].keywords}
        self.assertIn("hakem_log_yolu", anahtarlar,
                      "main() kanıt yolunu geçirmiyor: saha koşumunda hakem "
                      "kanıt dosyası HİÇ açılmaz")
        # Varsayılan yol üreticisi gerçekten çağrılıyor (içe aktarılıp atıl
        # durmuyor — kusurun asıl biçimi buydu).
        self.assertTrue(
            any(isinstance(c.func, ast.Name)
                and c.func.id == "varsayilan_hakem_log_yolu"
                for c in ast.walk(ana) if isinstance(c, ast.Call)),
            "varsayilan_hakem_log_yolu main()'de çağrılmıyor")

    def test_K7b_gercek_kurucu_diske_YKS_ARAYUZ_HAZIR_yazar(self):
        """Tk GERÇEKTEN açılabiliyorsa uçtan uca kurucu yolu da ölçülür."""
        import tkinter as tk
        from link import UDPLink
        try:
            kok = tk.Tk()
        except Exception as exc:               # başsız oturum / ekran yok
            self.skipTest(f"YAPILAMADI: tkinter ekran açamadı: {exc!r}")
        kok.withdraw()
        link = UDPLink(bind=("127.0.0.1", 0), timeout=0.05)
        with tempfile.TemporaryDirectory() as d:
            yol = Path(d) / "hakem_log.jsonl"
            try:
                app = yks_gui.YksArayuz(
                    kok, link, demo=False, ika_peer=("127.0.0.1", 5006),
                    iha_peer=("127.0.0.1", 5007), hakem_log_yolu=yol)
                app.hakem_kaydi.kapat()
            finally:
                link.close()
                kok.destroy()
            olaylar = [k["olay"] for k in _satirlar(yol)]
            self.assertIn("YKS_ARAYUZ_HAZIR", olaylar)
            hazir = next(k for k in _satirlar(yol)
                         if k["olay"] == "YKS_ARAYUZ_HAZIR")
            for alan in _sozlesme_tablosu()["YKS_ARAYUZ_HAZIR"]:
                self.assertIn(alan, hazir)
            self.assertEqual("udp", hazir["tasiyici"])


if __name__ == "__main__":
    unittest.main()
