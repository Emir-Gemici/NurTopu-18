"""A1: hakem haritasindaki rota, yayin seridinin girisine ankrajlanir.

Tk penceresi acilmaz. Geometri saf fonksiyon dikişinden, gorunurluk ise kayit
tutan yalanci canvas ile sinanir. Mutasyon gercek kaynak AST'sindeki ankraj
fonksiyonunu ``(0, 0)`` dondurecek bicimde degistirir; yorum mutasyonu degildir.
"""

from __future__ import annotations

import ast
from collections import defaultdict
import inspect
import sys
import unittest
from pathlib import Path


KOK = Path(__file__).resolve().parents[1]
GUI_YOLU = KOK / "comms" / "yks_gui.py"
if str(KOK / "comms") not in sys.path:
    sys.path.insert(0, str(KOK / "comms"))

import yks_gui  # noqa: E402


def _fonksiyon_dugumu(agac: ast.AST, ad: str) -> ast.FunctionDef:
    for dugum in ast.walk(agac):
        if isinstance(dugum, ast.FunctionDef) and dugum.name == ad:
            return dugum
    raise AssertionError(f"fonksiyon bulunamadi: {ad}")


def _ref_xy_get_var_mi(dugum: ast.AST) -> bool:
    for alt in ast.walk(dugum):
        if not isinstance(alt, ast.Call) or not isinstance(alt.func, ast.Attribute):
            continue
        if alt.func.attr != "get" or not alt.args:
            continue
        if isinstance(alt.args[0], ast.Constant) and alt.args[0].value == "ref_xy":
            return True
    return False


class _KayitCanvas:
    """Yalniz `_harita_ciz`in kullandigi canvas yuzeyini kaydeder."""

    def __init__(self, genislik=480, yukseklik=420):
        self.genislik = genislik
        self.yukseklik = yukseklik
        self.cagrilar = []

    def winfo_width(self):
        return self.genislik

    def winfo_height(self):
        return self.yukseklik

    def delete(self, *args, **kwargs):
        self.cagrilar.append(("delete", args, kwargs))

    def _kaydet(self, ad, *args, **kwargs):
        self.cagrilar.append((ad, args, kwargs))

    def create_line(self, *args, **kwargs):
        self._kaydet("create_line", *args, **kwargs)

    def create_rectangle(self, *args, **kwargs):
        self._kaydet("create_rectangle", *args, **kwargs)

    def create_text(self, *args, **kwargs):
        self._kaydet("create_text", *args, **kwargs)

    def create_oval(self, *args, **kwargs):
        self._kaydet("create_oval", *args, **kwargs)


class _KayitWidget:

    def __init__(self):
        self.ayarlar = {}

    def config(self, **kwargs):
        self.ayarlar.update(kwargs)


class _KayitLink:

    def __init__(self):
        self.gonderilen = []

    def send(self, *args):
        self.gonderilen.append(args)


def _tk_siz_gui(rota):
    gui = yks_gui.YksArayuz.__new__(yks_gui.YksArayuz)
    gui.harita = _KayitCanvas()
    gui.f_kucuk = "kucuk"
    gui.f_orta = "orta"
    gui.rota = rota
    gui.rota_yok = None
    return gui


def _mesaj_gui():
    gui = _tk_siz_gui(None)
    gui.rota_adr = None
    gui.rota_zaman = None
    gui.tespit_bayat = False
    gui.rx_alim = {}
    gui.onaylandi = False
    gui.tespit_onayli = False
    gui.sayac = defaultdict(int)
    gui.t_iha1 = None
    gui.otomatik_onay = False
    gui.btn_onay = _KayitWidget()
    gui.lbl_onay = _KayitWidget()
    gui.link = _KayitLink()
    gui.iha_iz = []
    gui.gunluk = []
    gui.kutular = []
    gui._dugum_adresini_ogren = lambda *_args: None
    gui._logla = lambda satir, renk="soluk": gui.gunluk.append((renk, satir))
    gui._kutu_yaz = lambda kaynak, **alanlar: gui.kutular.append(
        (kaynak, alanlar))
    gui._rota_analiz = lambda _m: None
    gui._irtifa_notunu_goster = lambda: None
    gui._zincir = lambda _adimlar: None
    return gui


class HakemEkraniAnkoruTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.kaynak = GUI_YOLU.read_text(encoding="utf-8")
        cls.agac = ast.parse(cls.kaynak, filename=str(GUI_YOLU))

    def _rota_seritte_mi(self, geometri_fonksiyonu):
        for yol, serit in yks_gui.SERIT_CIZIM_TABLOSU.items():
            merkez_x, yari_genislik, giris_y, cikis_y = serit
            noktalar, uyari = geometri_fonksiyonu(
                yol, [0.0, 0.0], [(0.0, 0.0), (0.0, 21.0), (0.0, 42.0)])
            self.assertIsNone(uyari)
            self.assertGreaterEqual(len(noktalar), 2)
            for x_m, y_m in noktalar:
                self.assertGreaterEqual(x_m, merkez_x - yari_genislik)
                self.assertLessEqual(x_m, merkez_x + yari_genislik)
                self.assertGreaterEqual(y_m, giris_y)
                self.assertLessEqual(y_m, cikis_y)

    def test_yapi_ref_xy_icin_truthy_yedek_yok(self):
        """a) Cizim yolunda ``ref_xy get(...) or ...`` bulunamaz."""
        for ad in ("rota_gosterim_geometrisi", "_harita_ciz"):
            fonksiyon = _fonksiyon_dugumu(self.agac, ad)
            kusurlular = [
                dugum for dugum in ast.walk(fonksiyon)
                if isinstance(dugum, ast.BoolOp)
                and isinstance(dugum.op, ast.Or)
                and _ref_xy_get_var_mi(dugum)
            ]
            self.assertEqual([], kusurlular,
                             f"{ad}: ref_xy truthy-yedegi ankraj kusurunu gizliyor")

    def test_davranis_sifir_ref_uc_seridin_icinde(self):
        """b) [0,0] yerel ofsettir; her rota kendi serit girisinde baslar."""
        self._rota_seritte_mi(yks_gui.rota_gosterim_geometrisi)

    def test_fail_closed_none_ref_rota_cizmez_ankor_yok_gosterir(self):
        """c) None ankrajda yesil rota yoktur ve ANKOR YOK gorunur."""
        rota = {"road": 2, "ref_xy": None,
                "waypoints": [(0.0, 0.0), (0.0, 8.0)]}
        noktalar, uyari = yks_gui.rota_gosterim_geometrisi(
            rota["road"], rota["ref_xy"], rota["waypoints"])
        self.assertEqual((), noktalar)
        self.assertEqual(yks_gui.ANKOR_YOK_UYARISI, uyari)

        gui = _tk_siz_gui(rota)
        gui._harita_ciz()
        metinler = [kw.get("text") for ad, _args, kw in gui.harita.cagrilar
                    if ad == "create_text"]
        rota_cizgileri = [
            (args, kw) for ad, args, kw in gui.harita.cagrilar
            if ad == "create_line" and kw.get("fill") == yks_gui.YESIL
            and kw.get("arrow") == "last"
        ]
        self.assertEqual([], rota_cizgileri)
        self.assertIn(yks_gui.ANKOR_YOK_UYARISI, metinler)

    def test_fail_closed_none_ref_hakem_onayini_da_kapatir(self):
        """Eksik ankor, secili seridi yesil yapamaz ve programatik onaylanamaz."""
        gui = _mesaj_gui()
        mesaj = {
            "type": "OPEN_ROUTE", "road": 2, "label": "orta", "conf": 0.9,
            "seq": 101, "ref_xy": None,
            "waypoints": [(0.0, 0.0), (0.0, 8.0)],
        }
        gui._mesaj_isle(mesaj, None)

        self.assertEqual("disabled", gui.btn_onay.ayarlar.get("state"))
        self.assertIn("ANKOR YOK", gui.btn_onay.ayarlar.get("text", ""))
        self.assertIn("ANKOR YOK", gui.lbl_onay.ayarlar.get("text", ""))
        self.assertFalse(gui.tespit_onayli)
        yesil_seritler = [
            (args, kw) for ad, args, kw in gui.harita.cagrilar
            if ad == "create_rectangle" and kw.get("fill") == yks_gui.YESIL
        ]
        self.assertEqual([], yesil_seritler,
                         "ankorsuz OPEN_ROUTE seridi yesil/gidilebilir gosterildi")

        gui.onayla()  # dugme disindan/dogrudan cagri da fail-closed kalmali
        self.assertFalse(gui.tespit_onayli)
        self.assertFalse(gui.onaylandi)
        self.assertEqual([], gui.link.gonderilen, "ankorsuz rotaya ACK gonderildi")

    def test_demo_da_saha_gibi_sifir_yerel_ref_yayinlar(self):
        """Demo, eski dunya koordinatiyla kusuru gizleyen ozel yol kullanmaz."""
        for ad in ("yeni_tespit", "demo_besle"):
            fonksiyon = _fonksiyon_dugumu(self.agac, ad)
            open_route_cagrilari = [
                dugum for dugum in ast.walk(fonksiyon)
                if isinstance(dugum, ast.Call)
                and isinstance(dugum.func, ast.Name)
                and dugum.func.id == "open_route"
            ]
            self.assertTrue(open_route_cagrilari, f"{ad}: demo OPEN_ROUTE yok")
            for cagri in open_route_cagrilari:
                alanlar = {kw.arg: kw.value for kw in cagri.keywords if kw.arg}
                ref = alanlar.get("ref_xy")
                self.assertIsInstance(ref, ast.Call,
                                      f"{ad}: ref_xy sozlesmeden turetilmiyor")
                self.assertIsInstance(ref.func, ast.Name)
                self.assertEqual("list", ref.func.id)
                self.assertEqual(1, len(ref.args))
                self.assertIsInstance(ref.args[0], ast.Name)
                self.assertEqual("YAYIN_REF_XY", ref.args[0].id,
                                 f"{ad}: demo saha ref sozlesmesinden ayrildi")
        self.assertEqual((0.0, 0.0), yks_gui.YAYIN_REF_XY)

    def test_mutasyon_ankoru_sifira_sabitlemek_kapiyi_DUSURUR(self):
        """d) Gercek kod AST'sindeki ankraj `(0,0)` olursa davranis kapisi duser."""
        secilen = []
        gerekli_adlar = {
            "SERIT_CIZIM_TABLOSU", "ANKOR_YOK_UYARISI",
            "serit_giris_ankoru", "rota_gosterim_geometrisi",
        }
        for dugum in self.agac.body:
            if isinstance(dugum, ast.Assign):
                adlar = {h.id for h in dugum.targets if isinstance(h, ast.Name)}
                if adlar & gerekli_adlar:
                    secilen.append(dugum)
            elif isinstance(dugum, ast.FunctionDef) and dugum.name in gerekli_adlar:
                if dugum.name == "serit_giris_ankoru":
                    # KOD mutasyonu: fonksiyon govdesi yeniden yazilir; yorumlara
                    # veya kaynak metnindeki tesadufi bir eslesmeye dokunulmaz.
                    dugum = ast.FunctionDef(
                        name=dugum.name, args=dugum.args,
                        body=[ast.Return(value=ast.Tuple(
                            elts=[ast.Constant(0.0), ast.Constant(0.0)],
                            ctx=ast.Load()))],
                        decorator_list=[], returns=dugum.returns,
                        type_comment=dugum.type_comment)
                secilen.append(dugum)
        mutant_agac = ast.fix_missing_locations(ast.Module(body=secilen,
                                                            type_ignores=[]))
        mutant_alan = {}
        exec(compile(mutant_agac, "<a1_ankor_mutasyonu>", "exec"), mutant_alan)
        with self.assertRaises(AssertionError):
            self._rota_seritte_mi(mutant_alan["rota_gosterim_geometrisi"])

    def test_sematik_uyari_width_ile_gorunur(self):
        """e) GPS olmayan gosterim, tasma onleyen width ile acikca yazilir."""
        harita = _fonksiyon_dugumu(self.agac, "_harita_ciz")
        uyarilar = []
        for cagri in (n for n in ast.walk(harita) if isinstance(n, ast.Call)):
            if not isinstance(cagri.func, ast.Attribute) or cagri.func.attr != "create_text":
                continue
            alanlar = {kw.arg: kw.value for kw in cagri.keywords if kw.arg}
            metin = alanlar.get("text")
            if isinstance(metin, ast.Name) and metin.id == "SEMATIK_GOSTERIM_UYARISI":
                uyarilar.append(alanlar)
        self.assertEqual(1, len(uyarilar))
        self.assertIn("width", uyarilar[0])
        self.assertEqual(
            "SEMATIK GOSTERIM — serit tablosundan turetildi, GPS degil",
            yks_gui.SEMATIK_GOSTERIM_UYARISI)

    def test_sematik_uyari_ana_harita_katmanlarindan_sonra_cizilir(self):
        """Rota-yok bandi dahil ana katmanlar semantik uyariyi ortemez."""
        gui = _tk_siz_gui(None)
        gui.rota_yok = {"sebep": "TEST"}
        gui._harita_ciz()
        uyari_indisi = next(
            i for i, (ad, _args, kw) in enumerate(gui.harita.cagrilar)
            if ad == "create_text"
            and kw.get("text") == yks_gui.SEMATIK_GOSTERIM_UYARISI)
        self.assertEqual(len(gui.harita.cagrilar) - 1, uyari_indisi)

    def test_sematik_uyari_inset_bbox_ile_cakismaz_width_bir_dahil(self):
        """Uyari bbox'i, sonradan cizilen opak inset kutusundan ayridir."""
        for canvas_w in (1, 480, 800):
            with self.subTest(canvas_w=canvas_w):
                gui = _tk_siz_gui({
                    "road": 2, "ref_xy": [0.0, 0.0],
                    "waypoints": [(0.0, 0.0), (0.0, 8.0)],
                })
                gui.harita = _KayitCanvas(genislik=canvas_w)
                gui.iha_iz = []
                gui._harita_ciz()
                gui._inset_ciz()  # gercek cizim sirasi: opak inset daha sonra

                uyari = next(
                    (args, kw) for ad, args, kw in gui.harita.cagrilar
                    if ad == "create_text"
                    and kw.get("text") == yks_gui.SEMATIK_GOSTERIM_UYARISI)
                inset = next(
                    (args, kw) for ad, args, kw in gui.harita.cagrilar
                    if ad == "create_rectangle" and kw.get("tags") == "inset"
                    and kw.get("fill") == "#0d1318")
                uyari_args, uyari_kw = uyari
                inset_args, _inset_kw = inset
                uyari_sol = uyari_args[0]
                uyari_sag = uyari_sol + uyari_kw["width"]
                inset_sol = inset_args[0]
                self.assertGreater(uyari_kw["width"], 0,
                                   "ilk pack genisligi=1 uyarinin width'ini bozdu")
                self.assertGreaterEqual(uyari_sol, 0)
                self.assertLessEqual(
                    uyari_sag, inset_sol,
                    f"uyari bbox x={uyari_sol}..{uyari_sag}, "
                    f"opak inset x={inset_sol}..{inset_args[2]} ile cakisti")

    def test_capa_geometri_tk_penceresinden_ayri_saf_fonksiyon(self):
        """f) Geometriyi sinamak icin Tk/YksArayuz nesnesi gerekmez."""
        imza = inspect.signature(yks_gui.rota_gosterim_geometrisi)
        self.assertEqual(["road", "ref_xy", "waypoints"], list(imza.parameters))
        dugum = next((n for n in self.agac.body
                      if isinstance(n, ast.FunctionDef)
                      and n.name == "rota_gosterim_geometrisi"), None)
        self.assertIsNotNone(dugum, "geometri sinif metoduna gomulmus")
        noktalar, uyari = yks_gui.rota_gosterim_geometrisi(
            1, [0.0, 0.0], [(0.0, 0.0), (0.0, 1.0)])
        self.assertIsNone(uyari)
        self.assertTrue(noktalar)


if __name__ == "__main__":
    unittest.main(verbosity=2)
