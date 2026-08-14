"""T36 KAPISI: hakem ekrani URETIM yolunu mu kosuyor, kendi hattini mi?

Kusur (REVIEW_LOG D-48): `_algi_kos` kendi cikarim hattini CIPLAK SABITLERLE
yazmisti — imgsz 512, letterbox YOK, zemin esigi 0.30->0.05, engel esigi 0.10,
min_area_ratio 0.02. Uretim yolu bunlarin hicbirini boyle kullanmiyordu.
Anayasa madde 16 ihlali; T8'de `analyze_path`'in kopyasi icin verilen kararin
aynisi gecerli: OLCUM/GOSTERIM YOLU URETIM YOLUNDAN AYRI OLAMAZ.

HANGI URETIM YOLU? `CONTRACTS.md` SS11.2: Halka 3 (Cikarim) ve Halka 4 (Maske)
sahibi `codes/rpi_inference.py` ve ikisi de GECERLI. SS11.1/1 `simulation/`
altindaki hicbir dosyanin sahip olmasini YASAKLAR — bu yuzden hakem ekrani
`simulation/scripts/iha_perceive.py`'a degil, `codes/rpi_inference.py`'a
hizalanir. Jetson saha paketi de o dosyanin bayt-birebir kopyasidir.

Bu paket model AGIRLIGI GEREKTIRMEZ: model sahte, maskeler sabit. Boylece
sira/parametre/cerceve sozlesmesi kilitlenir; gercek agirlikla olculen
67-kare tablosu goreve yapistirilmistir.
"""

from __future__ import annotations

import ast
import json
import queue
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import cv2
import numpy as np

KOK = Path(__file__).resolve().parents[1]
for _alt in ("codes", "comms"):
    if str(KOK / _alt) not in sys.path:
        sys.path.insert(0, str(KOK / _alt))

import rpi_inference  # noqa: E402
import yks_gui  # noqa: E402
from karar_sozlesmesi import (OLCEK_YOK_SEBEBI,  # noqa: E402
                              olcek_gecerli_mi, rota_olcek_reddi)
from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp,  # noqa: E402
                           _preprocess, _rota_kararini_esikle, analyze_path,
                           get_masks)

H, W = 576, 1024
ARENA_KADRAJ_MPP = 0.078125


class _SahteModel:
    """predict() cagrilarini kaydeder; gercek agirlik yuklemez."""

    def __init__(self):
        self.cagrilar = []

    def predict(self, *args, **kwargs):
        self.cagrilar.append((args, kwargs))
        return ["sonuc"]


def _koridor_maskeleri(serit=2, genislik=200):
    """Tuval boyutunda (kare) zemin/engel maskesi uret."""
    yan = max(H, W)
    trav = np.zeros((yan, yan), np.uint8)
    x0 = (yan - W) // 2
    merkez = x0 + {1: W // 6, 2: W // 2, 3: 5 * W // 6}[serit]
    y0 = (yan - H) // 2
    trav[y0:y0 + H, merkez - genislik // 2:merkez + genislik // 2] = 1
    return {0: trav, 1: np.zeros((yan, yan), np.uint8)}


def _gui(kaynak="drone", model=None):
    g = yks_gui.YksArayuz.__new__(yks_gui.YksArayuz)
    g.algi_model = model or _SahteModel()
    g.algi_kuyruk = queue.Queue()
    g.algi_mesgul = True
    g.algi_kaynak = kaynak
    return g


def _paketler(g):
    return list(g.algi_kuyruk.queue)


def _sonuc_bilgisi(g):
    paket = next((p for p in _paketler(g) if p[0] == "sonuc"), None)
    hata = [p for p in _paketler(g) if p[0] == "hata"]
    if paket is None:
        raise AssertionError(f"sonuc paketi yok; hatalar={hata}")
    return paket[2]


def _karar_metni(bilgi):
    return bilgi.split("karar: ", 1)[1].split(" · güven", 1)[0].strip()


def _kos(g, ad="kare.jpg", maskeler=None, goruntu=None):
    img = goruntu if goruntu is not None else np.zeros((H, W, 3), np.uint8)
    mask = maskeler if maskeler is not None else _koridor_maskeleri()

    def _get_masks(_sonuc, h, w, **_kw):
        return {k: v.copy() for k, v in mask.items()}

    with mock.patch.object(cv2, "imread", return_value=img), \
         mock.patch.object(rpi_inference, "get_masks", side_effect=_get_masks):
        g._algi_kos(Path(ad))
    return g


class UretimHizasiTests(unittest.TestCase):
    """GUI, uretim fonksiyonlarini uretim sirasiyla mi cagiriyor?"""

    def test_predict_uretim_imgsz_ve_esigiyle_cagriliyor(self):
        model = _SahteModel()
        g = _kos(_gui(model=model))
        self.assertEqual(1, len(model.cagrilar), "tek atis bekleniyordu")
        _args, kwargs = model.cagrilar[0]
        self.assertEqual(INFER_SIZE, kwargs["imgsz"])
        self.assertEqual(yks_gui.YksArayuz.ALGI_PREDICT_CONF, kwargs["conf"])
        del g

    def test_letterbox_ve_icerik_kutusu_uretimden_geliyor(self):
        """`_preprocess` kosacak ve `analyze_path` `icerik` ALACAK (T35)."""
        gercek_ap = rpi_inference.analyze_path
        cagri = {}

        def sarmal(*args, **kwargs):
            cagri.update(kwargs)
            return gercek_ap(*args, **kwargs)

        with mock.patch.object(rpi_inference, "_preprocess",
                               side_effect=_preprocess) as on_islem, \
             mock.patch.object(rpi_inference, "analyze_path",
                               side_effect=sarmal):
            _kos(_gui())
        self.assertEqual(1, on_islem.call_count, "letterbox kosmadi")
        self.assertIn("icerik", cagri, "analyze_path'e icerik GECIRILMEDI")
        self.assertIsNotNone(cagri["icerik"])
        self.assertEqual(4, len(cagri["icerik"]))

    def test_dolgu_kirpma_ve_esikleme_uretim_fonksiyonlariyla(self):
        with mock.patch.object(rpi_inference, "_maskeleri_icerige_kirp",
                               side_effect=_maskeleri_icerige_kirp) as kirp, \
             mock.patch.object(rpi_inference, "_rota_kararini_esikle",
                               side_effect=_rota_kararini_esikle) as esik:
            _kos(_gui())
        self.assertEqual(1, kirp.call_count,
                         "dolgu kirpma uretim fonksiyonuyla yapilmiyor")
        self.assertEqual(1, esik.call_count,
                         "K-B uretimin esikleyicisiyle uygulanmiyor")

    def test_gui_karari_uretim_yolunun_karariyla_AYNI(self):
        """Cikti denkligi: ayni maskede GUI ile `run_image` govdesi ayni der.

        T44: uretim govdesi ARTIK olcek kapisini de tasiyor
        (`rota_olcek_reddi`). Referans tarafi da onu icermelidir; yoksa test
        GUI'yi olcegi YOK SAYAN bir uretime hizalamis olur.

        Iki kip birden sinanir:
          · olceksiz (`mpp=None`)  -> iki taraf da OLCEK_YOK demeli
          · olcekli  (`mpp` VAR)   -> iki taraf da AYNI seridi vermeli
        """
        kaynaklar = (("arena_kadraj", ARENA_KADRAJ_MPP),
                     ("arena_gercek", None))
        for kaynak, mpp in kaynaklar:
            for serit in (1, 2, 3):
                for genislik in (60, 200, 340):
                    with self.subTest(kaynak=kaynak, mpp=mpp, serit=serit,
                                      genislik=genislik):
                        maskeler = _koridor_maskeleri(serit, genislik)
                        g = _gui(kaynak)
                        with mock.patch.object(
                                yks_gui.YksArayuz, "_kaynak_olcegi",
                                return_value=(mpp, "test")):
                            _kos(g, maskeler=maskeler)
                        ekran = _karar_metni(_sonuc_bilgisi(g))

                        # URETIM (codes/rpi_inference.py::run_image govdesi)
                        img = np.zeros((H, W, 3), np.uint8)
                        sq, _small, icerik = _preprocess(img)
                        m = {k: v.copy() for k, v in maskeler.items()}
                        m = _maskeleri_icerige_kirp(m, icerik)
                        olcek_reddi = rota_olcek_reddi(mpp)
                        yol, guv, wps, ret = analyze_path(
                            m[0], icerik=icerik, engel_mask=m.get(1), mpp=mpp,
                            return_reason=True)
                        if olcek_reddi is not None and ret is None:
                            yol, guv, wps, ret = None, 0.0, [], olcek_reddi
                        yol, guv, wps, ret = _rota_kararini_esikle(
                            yol, guv, wps, ret)
                        beklenen = (f"{yol}·{yks_gui.ROAD_LABEL[yol].upper()}"
                                    if yol else
                                    (f"ROTA YOK · {ret[0]}" if ret
                                     else "TESPİT YOK"))
                        self.assertEqual(beklenen, ekran)

    def test_predict_conf_uretim_varsayilanindan_KOPYALANMIS(self):
        """Ciplak sabit kilidi: deger `run_image`'in `--conf` varsayilanidir.

        Uretim varsayilani degisirse bu test duser; ekran sessizce ayrisamaz.
        """
        agac = ast.parse((KOK / "codes" / "rpi_inference.py").read_text(
            encoding="utf-8"))
        bulunan = None
        for dugum in ast.walk(agac):
            if (isinstance(dugum, ast.Call)
                    and isinstance(dugum.func, ast.Attribute)
                    and dugum.func.attr == "add_argument"
                    and dugum.args
                    and isinstance(dugum.args[0], ast.Constant)
                    and dugum.args[0].value == "--conf"):
                for kw in dugum.keywords:
                    if kw.arg == "default":
                        bulunan = ast.literal_eval(kw.value)
        self.assertIsNotNone(
            bulunan, "codes/rpi_inference.py'de --conf varsayilani bulunamadi")
        self.assertEqual(
            bulunan, yks_gui.YksArayuz.ALGI_PREDICT_CONF,
            "GUI predict esigi uretim varsayilanindan AYRISTI")

    def test_gui_kendi_cikarim_hattini_KURMUYOR(self):
        """Karolu/ciplak-esikli eski hattin izleri kalmamali."""
        kaynak = (KOK / "comms" / "yks_gui.py").read_text(encoding="utf-8")
        govde = kaynak.split("def _algi_kos", 1)[1].split(
            "def _algi_sonucu_goster", 1)[0]
        for yasak in ("min_conf=0.25", "min_conf=0.10", "min_conf=0.30",
                      "imgsz=512", "conf=0.05", "KARO"):
            self.assertNotIn(
                yasak, govde,
                f"_algi_kos hala kendi cikarim sabitini tasiyor: {yasak}")

    def test_serit_cizgileri_ICERIK_kutusundan(self):
        """Letterbox'ta tuvalin w//3'u gercek seritten kayar."""
        govde = (KOK / "comms" / "yks_gui.py").read_text(
            encoding="utf-8").split("def _algi_kos", 1)[1].split(
                "def _algi_sonucu_goster", 1)[0]
        self.assertNotIn("for x in (w // 3, 2 * w // 3):", govde)
        self.assertIn("_ix0 + _k * _iw / 3.0", govde)


class KompozitKaynakTests(unittest.TestCase):
    """Arena kompoziti hakem ekraninda gorunuyor mu, ve YER GERCEGI sizmiyor mu?"""

    def test_kompozit_ilk_ve_acilis_kaynagi(self):
        self.assertEqual("kompozit", yks_gui.YksArayuz.ALGI_KAYNAKLAR[0])

    def test_eski_dort_kaynak_hala_secilebilir(self):
        for ad in ("drone", "gemini", "test", "val"):
            self.assertIn(ad, yks_gui.YksArayuz.ALGI_KAYNAKLAR)

    def test_kompozit_dizini_listeleniyor(self):
        g = _gui("kompozit")
        dosyalar = g._algi_gorseller()
        self.assertTrue(dosyalar, "kompozit kume bos listelendi")
        self.assertTrue(all(p.suffix.lower() == ".jpg" for p in dosyalar))

    def test_yer_gercegi_manifestten_okunuyor(self):
        gercek = _gui("kompozit")._kompozit_yer_gercegi()
        self.assertTrue(gercek)
        for ad, serit in gercek.items():
            self.assertIn(serit, (1, 2, 3), ad)

    def test_beklenen_serit_bilgi_satirinda_gosteriliyor(self):
        gercek = _gui("kompozit")._kompozit_yer_gercegi()
        ad = sorted(gercek)[0]
        g = _kos(_gui("kompozit"), ad=ad)
        bilgi = _sonuc_bilgisi(g)
        self.assertIn(f"beklenen şerit {gercek[ad]}", bilgi)

    def test_beklenen_serit_KARARA_SIZMIYOR(self):
        """Yer gercegi degisirse KARAR degismemeli — yoksa test kendini dogrular."""
        gercek = _gui("kompozit")._kompozit_yer_gercegi()
        ad = sorted(gercek)[0]
        kararlar = set()
        for sahte_serit in (1, 2, 3):
            g = _gui("kompozit")
            with mock.patch.object(
                    yks_gui.YksArayuz, "_kompozit_yer_gercegi",
                    return_value={ad: sahte_serit}):
                _kos(g, ad=ad)
            kararlar.add(_karar_metni(_sonuc_bilgisi(g)))
        self.assertEqual(
            1, len(kararlar),
            f"beklenen serit karari degistirdi: {kararlar}")

    def test_manifest_okunamazsa_FAIL_CLOSED(self):
        """Sessiz bos gosterme yok: hata gunluge ve bilgi satirina yazilir."""
        g = _gui("kompozit")
        with mock.patch.object(yks_gui.YksArayuz, "_kompozit_yer_gercegi",
                               side_effect=FileNotFoundError("manifest yok")):
            _kos(g, ad="olmayan.jpg")
        bilgi = _sonuc_bilgisi(g)
        self.assertIn("beklenen şerit: OKUNAMADI", bilgi)
        gunlukler = [p[1] for p in _paketler(g) if p[0] == "log"]
        self.assertTrue(
            any("YER GERÇEĞİ OKUNAMADI" in x for x in gunlukler),
            f"fail-closed gunluk satiri yok: {gunlukler}")

    def test_manifest_bozuksa_sessizce_bos_donmez(self):
        with mock.patch.object(
                Path, "read_text",
                return_value=json.dumps({"ornekler": []})):
            with self.assertRaises(ValueError):
                _gui("kompozit")._kompozit_yer_gercegi()

    def test_kompozit_disinda_beklenen_serit_gosterilmez(self):
        g = _kos(_gui("drone"))
        self.assertNotIn("beklenen şerit", _sonuc_bilgisi(g))


class OlcekKapisiTests(unittest.TestCase):
    """T44 · Halka 5 hakem ekraninda: olcek kaynagindan mi geliyor?"""

    def test_olceksiz_kaynakta_OLCEK_YOK_gosterilir(self):
        """`drone`/`gemini`/`val`/`test`: telemetri yok -> olcek yok.

        Ekran "sahnede koridor yok" DEMEZ; sistem kisitini oldugu gibi yazar.
        """
        for kaynak in ("drone", "gemini", "val", "test"):
            with self.subTest(kaynak=kaynak):
                g = _kos(_gui(kaynak))
                bilgi = _sonuc_bilgisi(g)
                self.assertIn(OLCEK_YOK_SEBEBI, bilgi)
                self.assertIn("ölçek YOK", bilgi)
                self.assertIn("C-uzayı UYGULANAMADI", bilgi)

    def test_kompozit_kaynakta_manifest_olcegi_kullanilir(self):
        olcekler = _gui("kompozit")._kompozit_olcekleri()
        self.assertTrue(olcekler)
        ad = sorted(olcekler)[0]
        g = _gui("kompozit")
        mpp, not_ = g._kaynak_olcegi(Path(ad))
        self.assertTrue(olcek_gecerli_mi(mpp))
        self.assertEqual(olcekler[ad], mpp)
        self.assertIn("manifest", not_)

    def test_olcek_analyze_path_e_GERCEKTEN_geciriliyor(self):
        gercek_ap = rpi_inference.analyze_path
        cagri = {}

        def sarmal(*args, **kwargs):
            cagri.update(kwargs)
            return gercek_ap(*args, **kwargs)

        g = _gui()
        with mock.patch.object(yks_gui.YksArayuz, "_kaynak_olcegi",
                               return_value=(0.05, "test")),              mock.patch.object(rpi_inference, "analyze_path",
                               side_effect=sarmal):
            _kos(g)
        self.assertIn("mpp", cagri, "analyze_path'e mpp GECIRILMEDI")
        self.assertEqual(0.05, cagri["mpp"])

    def test_olcek_varken_C_UZAYI_kaniti_ekranda(self):
        g = _gui()
        with mock.patch.object(yks_gui.YksArayuz, "_kaynak_olcegi",
                               return_value=(0.05, "test")):
            _kos(g, maskeler=_koridor_maskeleri(1, 340))
        bilgi = _sonuc_bilgisi(g)
        self.assertIn("C-uzayı UYGULANDI", bilgi)
        self.assertIn("gövde açıklığı", bilgi)
        self.assertIn("ölçek 0.0500 m/px", bilgi)

    def test_uretimin_olcek_kapisi_KOPYALANMADI(self):
        """GUI kendi esigini yazmaz; sozlesmenin fonksiyonunu cagirir."""
        govde = (KOK / "comms" / "yks_gui.py").read_text(
            encoding="utf-8").split("def _algi_kos", 1)[1].split(
                "def _algi_sonucu_goster", 1)[0]
        self.assertIn("rota_olcek_reddi(mpp)", govde)
        for yasak in ('"OLCEK_YOK"', "olcek_gecerli_mi(mpp)",
                      "R_GEREKLI_M", "r_gerekli_piksel("):
            self.assertNotIn(
                yasak, govde,
                f"GUI uretimin olcek kapisini KOPYALIYOR: {yasak}")

    def test_manifest_bozuksa_FAIL_CLOSED_olceksiz_sayilir(self):
        g = _gui("kompozit")
        with mock.patch.object(yks_gui.YksArayuz, "_kaynak_olcegi",
                               side_effect=FileNotFoundError("manifest yok")):
            _kos(g, ad="olmayan.jpg")
        bilgi = _sonuc_bilgisi(g)
        self.assertIn(OLCEK_YOK_SEBEBI, bilgi)
        gunlukler = [x[1] for x in _paketler(g) if x[0] == "log"]
        self.assertTrue(
            any("ÖLÇEK OKUNAMADI" in x for x in gunlukler),
            f"fail-closed gunluk satiri yok: {gunlukler}")

    def test_olcek_yoksa_rota_YAYINLANMAZ(self):
        """Fail-closed: karar None, waypoint yok — 'sadece uyari' degil."""
        g = _gui("drone")
        with mock.patch.object(yks_gui.YksArayuz, "_kaynak_olcegi",
                               return_value=(None, "telemetri yok")):
            _kos(g, maskeler=_koridor_maskeleri(2, 340))
        self.assertEqual(f"ROTA YOK · {OLCEK_YOK_SEBEBI}",
                         _karar_metni(_sonuc_bilgisi(g)))


class ArenaKaynakTests(unittest.TestCase):
    """T64: arena kaynakları, manifest ölçeği ve fail-closed ekran kanıtı."""

    @staticmethod
    def _kadraj_fiksturu(kok: Path, mpp=ARENA_KADRAJ_MPP):
        """Gerçek T60 dizilimini küçük ve hermetik olarak kur."""
        veri = kok / "images" / "train" / "sa_000001.jpg"
        veri.parent.mkdir(parents=True)
        veri.write_bytes(b"gorsel")
        onizleme = kok / "_onizleme" / veri.name
        onizleme.parent.mkdir(parents=True)
        onizleme.write_bytes(b"onizleme")
        manifest = {
            "ornekler": [{
                "cikti": "images/train/sa_000001.jpg",
                "arena": {"mpp": mpp},
            }],
        }
        (kok / "manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8")
        return veri, onizleme

    def test_arena_kaynaklari_listede_ve_yollari_sabit(self):
        self.assertIn("arena_kadraj", yks_gui.YksArayuz.ALGI_KAYNAKLAR)
        self.assertIn("arena_gercek", yks_gui.YksArayuz.ALGI_KAYNAKLAR)
        self.assertEqual(
            Path(r"O:\navitas-local-train\calisma\sentetik_arena_kadraj_t60"),
            yks_gui.YksArayuz.ALGI_ARENA_KADRAJ_KOKU)
        self.assertEqual(
            KOK / "data" / "arena_referans" / "sartname_s9_arena.png",
            yks_gui.YksArayuz.ALGI_ARENA_GERCEK_DOSYA)

    def test_arena_kadraj_yalniz_images_altini_listeler(self):
        with tempfile.TemporaryDirectory() as gecici:
            kok = Path(gecici)
            veri, onizleme = self._kadraj_fiksturu(kok)
            with mock.patch.object(
                    yks_gui.YksArayuz, "ALGI_ARENA_KADRAJ_KOKU", kok):
                bulunan = _gui("arena_kadraj")._algi_gorseller()
        self.assertEqual([veri], bulunan)
        self.assertNotIn(onizleme, bulunan)

    def test_arena_gercek_tek_dosya_olarak_listelenir(self):
        with tempfile.TemporaryDirectory() as gecici:
            gercek = Path(gecici) / "arena.png"
            gercek.write_bytes(b"gorsel")
            with mock.patch.object(
                    yks_gui.YksArayuz, "ALGI_ARENA_GERCEK_DOSYA", gercek):
                bulunan = _gui("arena_gercek")._algi_gorseller()
        self.assertEqual([gercek], bulunan)

    def test_arena_kadraj_manifest_olcegi_tam_yolla_baglanir(self):
        with tempfile.TemporaryDirectory() as gecici:
            kok = Path(gecici)
            veri, onizleme = self._kadraj_fiksturu(kok)
            with mock.patch.object(
                    yks_gui.YksArayuz, "ALGI_ARENA_KADRAJ_KOKU", kok):
                g = _gui("arena_kadraj")
                mpp, not_ = g._kaynak_olcegi(veri)
                yanlis, _ = g._kaynak_olcegi(onizleme)
        self.assertEqual(ARENA_KADRAJ_MPP, mpp)
        self.assertIn("T60 manifesti", not_)
        self.assertIsNone(yanlis, "aynı basename'li önizlemeye mpp sızdı")

    def test_arena_kadraj_mpp_None_mutasyonu_fail_closed(self):
        with tempfile.TemporaryDirectory() as gecici:
            kok = Path(gecici)
            veri, _ = self._kadraj_fiksturu(kok, mpp=None)
            with mock.patch.object(
                    yks_gui.YksArayuz, "ALGI_ARENA_KADRAJ_KOKU", kok):
                mpp, not_ = _gui("arena_kadraj")._kaynak_olcegi(veri)
        self.assertIsNone(mpp)
        self.assertIn("mpp yok/geçersiz", not_)
        self.assertIn("ölçek uydurulmadı", not_)

    def test_arena_kadraj_gecersiz_mpp_degerlerini_uydurmaz(self):
        gecersizler = (True, 0, -1, float("nan"), float("inf"),
                       "0.078125", [])
        for mpp in gecersizler:
            with self.subTest(mpp=repr(mpp)):
                with tempfile.TemporaryDirectory() as gecici:
                    kok = Path(gecici)
                    veri, _ = self._kadraj_fiksturu(kok, mpp=mpp)
                    with mock.patch.object(
                            yks_gui.YksArayuz,
                            "ALGI_ARENA_KADRAJ_KOKU", kok):
                        bulunan, not_ = _gui(
                            "arena_kadraj")._kaynak_olcegi(veri)
                self.assertIsNone(bulunan)
                self.assertIn("ölçek uydurulmadı", not_)

    def test_arena_kadraj_bozuk_manifest_olcek_uydurmaz(self):
        with tempfile.TemporaryDirectory() as gecici:
            kok = Path(gecici)
            veri = kok / "images" / "train" / "sa_000001.jpg"
            veri.parent.mkdir(parents=True)
            veri.write_bytes(b"gorsel")
            (kok / "manifest.json").write_text("{bozuk", encoding="utf-8")
            with mock.patch.object(
                    yks_gui.YksArayuz, "ALGI_ARENA_KADRAJ_KOKU", kok):
                bulunan, not_ = _gui("arena_kadraj")._kaynak_olcegi(veri)
        self.assertIsNone(bulunan)
        self.assertIn("manifesti okunamadı/geçersiz", not_)
        self.assertIn("ölçek uydurulmadı", not_)

    def test_arena_kadraj_kok_disina_tasan_manifest_reddedilir(self):
        with tempfile.TemporaryDirectory() as gecici:
            kok = Path(gecici)
            (kok / "images").mkdir()
            (kok / "manifest.json").write_text(json.dumps({
                "ornekler": [{"cikti": "../disari.jpg",
                              "arena": {"mpp": ARENA_KADRAJ_MPP}}],
            }), encoding="utf-8")
            with mock.patch.object(
                    yks_gui.YksArayuz, "ALGI_ARENA_KADRAJ_KOKU", kok):
                with self.assertRaisesRegex(ValueError, "üst dizine"):
                    _gui("arena_kadraj")._arena_kadraj_olcekleri()

    def test_arena_kadraj_ekranda_rota_cizer_ve_loglar(self):
        g = _gui("arena_kadraj")
        with mock.patch.object(
                yks_gui.YksArayuz, "_kaynak_olcegi",
                return_value=(ARENA_KADRAJ_MPP, "T60 manifesti")):
            _kos(g, maskeler=_koridor_maskeleri(2, 340))
        paket = next(p for p in _paketler(g) if p[0] == "sonuc")
        self.assertEqual("2·ORTA", _karar_metni(paket[2]))
        self.assertIn("gösterim: sürüş koridoru", paket[2])
        self.assertIn("arena_kadraj", paket[3])
        sari = np.all(paket[1] == np.asarray((0, 220, 255), np.uint8), axis=2)
        self.assertGreater(np.count_nonzero(sari), 0, "ekranda sarı rota yok")

    def test_arena_gercek_maske_var_rota_yok_ve_sebep_acik(self):
        g = _kos(_gui("arena_gercek"),
                 maskeler=_koridor_maskeleri(2, 340))
        paket = next(p for p in _paketler(g) if p[0] == "sonuc")
        bilgi = paket[2]
        self.assertEqual(f"ROTA YOK · {OLCEK_YOK_SEBEBI}",
                         _karar_metni(bilgi))
        self.assertIn("eğik arena bakışında", bilgi)
        self.assertIn("72 px", bilgi)
        self.assertIn("38 px", bilgi)
        self.assertIn("tek skaler mpp geçersiz", bilgi)
        self.assertIn("gösterim: segmentasyon maskesi (rota değil)", bilgi)
        self.assertIn(OLCEK_YOK_SEBEBI, paket[3])
        sari = np.all(paket[1] == np.asarray((0, 220, 255), np.uint8), axis=2)
        self.assertEqual(0, np.count_nonzero(sari), "ölçeksiz karede rota çizildi")
        # Siyah girdi üzerinde, uyarı bandının altındaki serbest maske mavi
        # tonla görünür olmalı; bu rota/waypoint iddiası değildir.
        self.assertTrue(np.any(paket[1][H // 2, W // 2] != 0))

    def test_bos_maske_varmis_gibi_gosterilmez_ve_yapisal_ret_korunur(self):
        yan = max(H, W)
        bos = np.zeros((yan, yan), np.uint8)
        g = _kos(_gui("arena_gercek"), maskeler={0: bos, 1: bos})
        paket = next(p for p in _paketler(g) if p[0] == "sonuc")
        self.assertIn("ROTA YOK · MASKE_YOK", paket[2])
        self.assertIn("gösterim: maske yok", paket[2])
        self.assertNotIn("gösterim: segmentasyon maskesi", paket[2])
        sari = np.all(paket[1] == np.asarray((0, 220, 255), np.uint8), axis=2)
        self.assertEqual(0, np.count_nonzero(sari))

    def test_arena_kadraj_mpp_None_olursa_rota_cizilmez(self):
        g = _gui("arena_kadraj")
        with mock.patch.object(
                yks_gui.YksArayuz, "_kaynak_olcegi",
                return_value=(None, "MUTASYON: manifest mpp=None")):
            _kos(g, maskeler=_koridor_maskeleri(2, 340))
        paket = next(p for p in _paketler(g) if p[0] == "sonuc")
        self.assertEqual(f"ROTA YOK · {OLCEK_YOK_SEBEBI}",
                         _karar_metni(paket[2]))
        sari = np.all(paket[1] == np.asarray((0, 220, 255), np.uint8), axis=2)
        self.assertEqual(0, np.count_nonzero(sari))


if __name__ == "__main__":
    unittest.main(verbosity=2)
