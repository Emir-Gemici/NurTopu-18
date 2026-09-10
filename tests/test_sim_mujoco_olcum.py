"""T214-A · ölçüm zinciri nöbetçileri (ON_KAYIT H1-K3/K5/K6 · REVIEW_LOG D-441 mimar kararları a–d).

Kapılar:
  A  `gorev_kosumu.basari_hesapla` — K5 başarısının TEK tanımı (saf). Her koşul tek başına
     düşürülünce False: temas=1, kod=4/2/3, süre 600,1, süre ölçülmedi, rota yok, HB dışı;
     sınır 600,0 dahil ve sözleşmeden (çıplak 600 yok). `kos()` başarıyı YALNIZ bu fonksiyonla
     kurar (AST). Diskteki her koşum JSON'unun `basari` alanı fonksiyonla yeniden hesaplanınca eş.
  B  Takip hatası — `nokta_polyline_uzakligi` geometrisi ve `arena.dist_to_path` ile eşliği;
     `TakipOlcer` ilk temastan sonra örneklemez, örnek yoksa None (ÖLÇÜLEMEDİ ≠ 0);
     `takip_ornekle` yalnız SÜRÜŞ sırasında örnekler; `kos().bekle` kancayı kullanır (AST).
     Disk: sürülmeyen koşumda None, sürülende temaslı ⇔ `takip_temasla_kesildi`.
  C  Çıkarım imgsz TEK KAYNAK (D-441 a) — `iha_haritala.INFER_SIZE` = kayıt defteri etkin
     profili = `rpi_inference.INFER_SIZE` (512); kopya defterde imgsz değişince iki okuyucu da
     yeni değeri okur; defter yoksa `ModelRegistryError` (fail-closed, sessiz yedek yok);
     `_infer` çağrısı `INFER_SIZE` ile (AST: MOZ_PX/sayı değil); `on_olcum_k3.teshis`
     varsayılanı üretim boyu. Disk: model koşumları ve K3 üretim JSON'ları imgsz 512.
  D  Karar toplayıcı — `harita_hukmu` (ön kayıtlı hüküm: yanlış yol yayını → False, OPEN_ROUTE
     yok → False); `ceyrek_tur`; `piksel_dunya` ↔ `dunya_piksel` gidiş-dönüş ve kuzey-yukarı;
     `karede_mi`; `dunya_yolu` arena yolunu tanır; `ozet_hesapla` YAZMAZ ve diskteki
     `ozet_k3_uretim.json` ile eş (elle düzenleme/bayatlık yakalanır); harita JSON şeması.
  E  Koşum özeti — `tel_tipi` (güven kapısı OPEN_ROUTE'u NO_ROUTE'a çevirince NO_ROUTE sayılır);
     yapay iki koşumda olay sayıları; `ozet_hesapla` YAZMAZ ve diskteki `ozet_kosum.json` ile
     eş (`tarih` hariç); diskte güven dönüşümü yalnız DUSUK_GUVEN sebebiyle.
  F  Grafik nöbetçisi (H1-K6) — `FDR/sekiller/sim_*.{svg,png}` 4×2 var; aynı JSON'dan geçici
     klasöre yeniden üretilince PNG BAYT-EŞ, SVG içerik-eş (yalnız satır sonu normalize — git
     autocrlf); alt yazı ve SVG açıklaması veri JSON yolunu taşır.
  G  `README_T214A.md` üreteç (`t214a_rapor.py`) çıktısıyla eş (elle düzenlenmedi).
Mutasyonlar: `results/fdr_sprint_20260910/H1/t214a/mutasyon_t214a.py` (çıktı `mutasyon_ciktisi.txt`).
GPU / MuJoCo render YOK (disk kanıtı + saf fonksiyonlar); ağ portu yok.
"""
from __future__ import annotations

import ast
import copy
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

KOK = Path(__file__).resolve().parents[1]
for _p in (str(KOK / "simulation" / "mujoco"), str(KOK / "simulation" / "scripts"),
           str(KOK / "codes"), str(KOK / "comms")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np                              # noqa: E402

import arena                                    # noqa: E402
import gorev_kosumu as gk                       # noqa: E402
import sim_karar_toplayici as skt               # noqa: E402
from karar_sozlesmesi import SARTNAME_IKA_GOREV_SURESI_S   # noqa: E402

H1 = KOK / "results" / "fdr_sprint_20260910" / "H1"
KOSUM = H1 / "kosum_tur3"
K3 = H1 / "k3_uretim_boru"
GK_KAYNAK = KOK / "simulation" / "mujoco" / "gorev_kosumu.py"


def _kosumlar() -> list[dict]:
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(KOSUM.glob("*_*_*_*.json"))]


def _fonksiyon(agac, ad):
    return next(n for n in agac.body if isinstance(n, ast.FunctionDef) and n.name == ad)


def _ad(r) -> str:
    return f"{r['rota_kaynak']}_{r['harita']}_{r['senaryo']}_{r['seed']}"


# ── A ───────────────────────────────────────────────────────────────────────
class A_BasariHesapla(unittest.TestCase):
    TAMAM = dict(kod=0, rota_bulundu=True, hb_icinde=True, temas_sayisi=0, sure_ika=71.3)

    def test_hepsi_saglaninca_basari(self):
        self.assertIs(gk.basari_hesapla(**self.TAMAM), True)

    def test_her_kosul_tek_basina_dusurur(self):
        for alan, deger in (("temas_sayisi", 1), ("temas_sayisi", 469), ("kod", 4), ("kod", 2), ("kod", 3),
                            ("sure_ika", 600.1), ("sure_ika", None), ("rota_bulundu", False),
                            ("hb_icinde", False)):
            with self.subTest(alan=alan, deger=deger):
                self.assertIs(gk.basari_hesapla(**{**self.TAMAM, alan: deger}), False)

    def test_sure_siniri_dahil_ve_sozlesmeden(self):
        self.assertEqual(SARTNAME_IKA_GOREV_SURESI_S, 600)          # şartname §6.2 (CONTRACTS)
        self.assertIs(gk.basari_hesapla(**{**self.TAMAM, "sure_ika": SARTNAME_IKA_GOREV_SURESI_S}), True)
        fn = _fonksiyon(ast.parse(GK_KAYNAK.read_text(encoding="utf-8")), "basari_hesapla")
        sayilar = [n.value for n in ast.walk(fn) if isinstance(n, ast.Constant)
                   and isinstance(n.value, (int, float)) and not isinstance(n.value, bool)]
        self.assertNotIn(600, sayilar, "basari_hesapla içinde çıplak 600 — sözleşme sabiti okunmalı")

    def test_kos_basariyi_yalniz_fonksiyonla_kurar(self):
        kos = _fonksiyon(ast.parse(GK_KAYNAK.read_text(encoding="utf-8")), "kos")
        atamalar = [n for n in ast.walk(kos) if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == "basari" for t in n.targets)]
        self.assertEqual(len(atamalar), 1)
        cagri = atamalar[0].value
        self.assertIsInstance(cagri, ast.Call)
        self.assertEqual(getattr(cagri.func, "id", None), "basari_hesapla")
        for n in ast.walk(kos):
            if isinstance(n, ast.Compare) and isinstance(n.left, ast.Attribute) and n.left.attr == "temas_sayisi":
                self.fail("kos() içinde temas karşılaştırması — başarı tanımı ikiye bölünmüş")

    def test_diskteki_kosumlar_tanimla_es(self):
        rs = _kosumlar()
        self.assertGreaterEqual(len(rs), 90)
        for r in rs:
            with self.subTest(k=_ad(r)):
                self.assertEqual(r["basari"], gk.basari_hesapla(r["cikis_kodu"], r["rota_bulundu"], r["hb_icinde"],
                                                                r["temas_sayisi"], r["sure_sim_ika"]))


# ── B ───────────────────────────────────────────────────────────────────────
class _SahteSurucu:
    temas_sayisi = 0

    def konum_al(self):
        return (5.0, 1.0, 0.0, 0.0)


class B_TakipHatasi(unittest.TestCase):
    HAT = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0)]

    def test_nokta_polyline_geometri(self):
        f = gk.nokta_polyline_uzakligi
        self.assertAlmostEqual(f(5.0, 3.0, self.HAT), 3.0)
        self.assertAlmostEqual(f(-4.0, 0.0, self.HAT), 4.0)
        self.assertAlmostEqual(f(12.0, 5.0, self.HAT), 2.0)
        self.assertAlmostEqual(f(13.0, 14.0, self.HAT), 5.0)            # (10,10) köşesinden 3-4-5
        self.assertAlmostEqual(f(1.0, 1.0, [(0.0, 0.0)]), math.sqrt(2.0))

    def test_arena_dist_to_path_ile_es(self):
        H = arena.harita(3, "zor")
        rng = np.random.RandomState(7)
        for r in (1, 2, 3):
            for x, y in rng.uniform(-25.0, 25.0, size=(15, 2)):
                self.assertAlmostEqual(gk.nokta_polyline_uzakligi(x, y, H["paths"][r]),
                                       arena.dist_to_path(x, y, H["paths"][r]), places=9)

    def test_ilk_temastan_sonra_orneklemez(self):
        o = gk.TakipOlcer(self.HAT)
        o.ornekle(5.0, 0.2, 0)
        o.ornekle(5.0, 0.5, 0)
        o.ornekle(5.0, 9.0, 1)             # temas: bu örnek de alınmaz, ölçüm kesilir
        o.ornekle(5.0, 20.0, 1)
        oz = o.ozet()
        self.assertEqual(oz["n"], 2)
        self.assertAlmostEqual(oz["maks"], 0.5)
        self.assertAlmostEqual(oz["ort"], 0.35)
        self.assertTrue(oz["temasla_kesildi"])

    def test_ornek_yoksa_none(self):
        oz = gk.TakipOlcer(self.HAT).ozet()
        self.assertIsNone(oz["maks"])
        self.assertIsNone(oz["ort"])
        self.assertEqual(oz["n"], 0)

    def test_yalniz_surus_sirasinda_ornekler(self):
        o, s = gk.TakipOlcer(self.HAT), _SahteSurucu()
        kayit = {"t_surus_bas": None, "t_surus_son": None}
        self.assertFalse(gk.takip_ornekle(kayit, s, o))                 # rota bekleme / IKA_GO öncesi
        kayit["t_surus_bas"] = 40.0
        self.assertTrue(gk.takip_ornekle(kayit, s, o, None))            # sürüş (plan ölçeri yok)
        kayit["t_surus_son"] = 110.0
        self.assertFalse(gk.takip_ornekle(kayit, s, o))                 # sürüş bitti
        self.assertEqual(o.ozet()["n"], 1)
        self.assertAlmostEqual(o.ozet()["maks"], 1.0)

    def test_kos_bekle_kancayi_kullanir(self):
        kos = _fonksiyon(ast.parse(GK_KAYNAK.read_text(encoding="utf-8")), "kos")
        bekle = next(n for n in ast.walk(kos) if isinstance(n, ast.FunctionDef) and n.name == "bekle")
        cagrilar = {getattr(n.func, "id", getattr(n.func, "attr", None))
                    for n in ast.walk(bekle) if isinstance(n, ast.Call)}
        self.assertIn("takip_ornekle", cagrilar)
        self.assertNotIn("ornekle", cagrilar, "bekle() ölçeri doğrudan örnekliyor — sürüş koşulu atlanır")

    def test_disk_takip_alanlari(self):
        for r in _kosumlar():
            with self.subTest(k=_ad(r)):
                if r["sure_sim_ika"] is None:
                    self.assertIsNone(r["takip_hatasi_maks_m"])
                    self.assertEqual(r["takip_ornek_n"], 0)
                    continue
                self.assertEqual(r["takip_ornek_n"] > 0, r["takip_hatasi_maks_m"] is not None)
                self.assertEqual(r["temas_sayisi"] > 0, bool(r["takip_temasla_kesildi"]))
                if r["takip_hatasi_maks_m"] is not None:
                    self.assertLessEqual(r["takip_hatasi_ort_m"], r["takip_hatasi_maks_m"])


# ── C ───────────────────────────────────────────────────────────────────────
class C_ImgszTekKaynak(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import iha_haritala
        import rpi_inference
        cls.ih, cls.ri = iha_haritala, rpi_inference
        cls.defter = json.loads((KOK / "config" / "model_registry.json").read_text(encoding="utf-8"))

    def test_uc_okuyucu_ayni_sayi(self):
        etkin = int(self.defter["profiles"][self.defter["default_profile"]]["imgsz"])
        self.assertEqual(etkin, 512)                                    # D-441 a: kayıt (512) esas
        self.assertEqual(self.ih.INFER_SIZE, etkin)
        self.assertEqual(self.ih.cikarim_boyu(), etkin)
        self.assertEqual(self.ri.INFER_SIZE, etkin)
        self.assertNotEqual(self.ih.INFER_SIZE, self.ih.MOZ_PX)         # 1024 tuval, çıkarım boyu değil

    def test_kopya_defter_degisince_ayni_degeri_okur(self):
        with tempfile.TemporaryDirectory() as td:
            veri = copy.deepcopy(self.defter)
            veri["profiles"][veri["default_profile"]]["imgsz"] = 640
            (Path(td) / "config").mkdir()
            (Path(td) / "config" / "model_registry.json").write_text(json.dumps(veri), encoding="utf-8")
            self.assertEqual(self.ih.cikarim_boyu(kok=td), 640)
            self.assertEqual(self.ri._kayittan_imgsz(td), 640)          # üretim okuyucusu da aynı alanı okur

    def test_defter_yoksa_fail_closed(self):
        from model_registry import ModelRegistryError
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ModelRegistryError):
                self.ih.cikarim_boyu(kok=td)

    def test_infer_cagrisi_kayit_boyuyla(self):
        agac = ast.parse((KOK / "simulation" / "scripts" / "iha_haritala.py").read_text(encoding="utf-8"))
        cagrilar = [n for n in ast.walk(agac) if isinstance(n, ast.Call)
                    and isinstance(n.func, ast.Name) and n.func.id == "_infer"]
        self.assertEqual(len(cagrilar), 1)
        arg = cagrilar[0].args[3]
        self.assertIsInstance(arg, ast.Name)
        self.assertEqual(arg.id, "INFER_SIZE")
        atama = [n for n in agac.body if isinstance(n, ast.Assign)
                 and any(getattr(t, "id", None) == "INFER_SIZE" for t in n.targets)]
        self.assertEqual(len(atama), 1)
        self.assertIsInstance(atama[0].value, ast.Call, "INFER_SIZE çıplak sayı — kayıt defterinden okunmalı")

    def test_on_olcum_k3_teshis_uretim_boyu(self):
        import on_olcum_k3 as oo

        class _Dur(Exception):
            pass

        yakalanan = []

        def sahte(_img, _model, _conf, imgsz, *a, **k):
            yakalanan.append(imgsz)
            raise _Dur

        with mock.patch.object(oo, "_infer", sahte):
            with self.assertRaises(_Dur):
                oo.teshis(np.zeros((8, 8, 3), np.uint8), None, 0.15, None, "kolay")
        self.assertEqual(yakalanan, [self.ih.INFER_SIZE])

    def test_disk_kosum_ve_k3_imgsz(self):
        ms = [r for r in _kosumlar() if r["rota_kaynak"] == "model"]
        self.assertEqual(len(ms), 45)
        for r in ms:
            with self.subTest(k=_ad(r)):
                self.assertEqual(r["model_teshis"]["imgsz"], 512)
                self.assertEqual(r["model_teshis"]["mozaik_px"], 1024)
        for p in sorted(K3.glob("*/harita_*_*.json")):
            with self.subTest(p=p.as_posix()):
                self.assertEqual(json.loads(p.read_text(encoding="utf-8"))["uretim"]["imgsz"], 512)


# ── D ───────────────────────────────────────────────────────────────────────
class D_KararToplayici(unittest.TestCase):
    @staticmethod
    def _k(acik, *yayin):
        return {"acik_yol": acik, "ika_yayin": [
            {"tip": "NO_ROUTE", "sebep": "MASKE_YOK"} if y is None else {"tip": "OPEN_ROUTE", "yol": y}
            for y in yayin]}

    def test_harita_hukmu(self):
        h = skt.harita_hukmu
        self.assertFalse(h(self._k(1))["open_route_var"])
        self.assertFalse(h(self._k(1))["dogru"])
        self.assertFalse(h(self._k(1, None, None))["dogru"])
        self.assertTrue(h(self._k(1, 1))["dogru"])
        k = h(self._k(1, 2, 1))
        self.assertFalse(k["dogru"])
        self.assertEqual(k["yanlis_yol_yayini_n"], 1)
        self.assertFalse(k["ilk_open_route_dogru"])
        self.assertTrue(k["son_open_route_dogru"])
        k = h(self._k(3, 3, None))
        self.assertTrue(k["dogru"])
        self.assertEqual(k["son_yayin_tipi"], "NO_ROUTE")

    def test_ceyrek_tur(self):
        for yaw, k in ((0.0, 0), (math.pi / 2, 1), (-math.pi / 2, 3), (math.pi, 2), (0.3, 0),
                       (math.radians(136.0), 2)):
            with self.subTest(yaw=yaw):
                self.assertEqual(skt.ceyrek_tur(yaw), k)

    def test_piksel_dunya_gidis_donus(self):
        rng = np.random.RandomState(3)
        for _ in range(40):
            x, y = rng.uniform(-20.0, 20.0, 2)
            poz = (0, 0.0, float(x), float(y), 30.0, float(rng.uniform(-math.pi, math.pi)))
            teta = skt.ceyrek_tur(poz[5]) * math.pi / 2
            px, py = rng.uniform(0.0, 1280.0, 2)
            wx, wy = skt.piksel_dunya(px, py, poz, 1280, 1280, 0.0356, teta)
            qx, qy = skt.dunya_piksel(wx, wy, poz, 1280, 1280, 0.0356, teta)
            self.assertAlmostEqual(qx, px, places=6)
            self.assertAlmostEqual(qy, py, places=6)
        wx, wy = skt.piksel_dunya(640, 640, (0, 0.0, 3.0, -4.0, 30.0, 1.0), 1280, 1280, 0.05, 0.3)
        self.assertAlmostEqual(wx, 3.0)
        self.assertAlmostEqual(wy, -4.0)

    def test_kerteriz_kuzey_yukari(self):
        for yaw in (math.pi / 2, -math.pi / 2, 0.0, math.pi):
            with self.subTest(yaw=yaw):
                poz = (0, 0.0, 1.0, 2.0, 30.0, yaw)
                teta = skt.ceyrek_tur(yaw) * math.pi / 2
                wx, wy = skt.piksel_dunya(640, 540, poz, 1280, 1280, 0.05, teta)     # 100 px YUKARI → kuzey
                self.assertAlmostEqual(wx, 1.0, places=6)
                self.assertAlmostEqual(wy, 7.0, places=6)
                wx, wy = skt.piksel_dunya(740, 640, poz, 1280, 1280, 0.05, teta)     # 100 px SAĞA → doğu
                self.assertAlmostEqual(wx, 6.0, places=6)
                self.assertAlmostEqual(wy, 2.0, places=6)

    def test_karede_mi(self):
        poz = (0, 0.0, 0.0, 0.0, 30.0, math.pi / 2)            # 1280 px × 0,0356 = 45,6 m kare
        self.assertTrue(skt.karede_mi(10.0, 10.0, poz, 1280, 1280, 0.0356, math.pi / 2))
        self.assertFalse(skt.karede_mi(0.0, -23.0, poz, 1280, 1280, 0.0356, math.pi / 2))

    def test_dunya_yolu_arena_yolunu_tanir(self):
        for h, lv in ((2, "orta"), (5, "zor")):
            H = arena.harita(h, lv)
            for r in (1, 2, 3):
                yol = H["paths"][r]
                n = len(yol)
                govde = [tuple(p) for p in yol[n // 5: 4 * n // 5: 5]]     # KB/HB ortak uçları hariç gövde
                with self.subTest(h=h, lv=lv, r=r):
                    self.assertEqual(skt.dunya_yolu(govde, H)["yol"], r)

    def test_ozet_hesapla_yazmaz_ve_disk_es(self):
        disk = json.loads((K3 / skt.OZET_ADI).read_text(encoding="utf-8"))
        with mock.patch.object(Path, "write_text", side_effect=AssertionError("ozet_hesapla YAZDI")):
            yeni = skt.ozet_hesapla(K3)
        self.assertEqual(disk, yeni, "ozet_k3_uretim.json elle düzenlenmiş / bayat — sim_karar_toplayici ile üret")

    def test_harita_json_semasi(self):
        import rpi_inference as ri
        dosyalar = sorted(K3.glob("kerteriz/harita_*_*.json")) + sorted(K3.glob("ham/harita_*_*.json"))
        self.assertEqual(len(dosyalar), 30)
        for p in dosyalar:
            r = json.loads(p.read_text(encoding="utf-8"))
            with self.subTest(p=p.parent.name + "/" + p.name):
                self.assertTrue(r["hizali"])
                self.assertEqual(r["okunan"], r["kare_n"])
                self.assertEqual(r["uretim"]["imgsz"], ri.INFER_SIZE)
                self.assertTrue(r["model"]["eslesti"])
                self.assertEqual(r["hukum"], skt.harita_hukmu(r))
                self.assertEqual(r["teshis"], skt.harita_teshisi(r))
                self.assertTrue(r["teshis"]["kare_ika_or_tutarli"])
                for s in r["kareler"]:
                    if s.get("karar") == "OPEN_ROUTE":
                        self.assertIn(s["rota_dunya_yolu"], (1, 2, 3))
                        self.assertEqual(len(s["rota_dunya"]), s["wp_n"])


# ── E ───────────────────────────────────────────────────────────────────────
class E_KosumOzeti(unittest.TestCase):
    def test_tel_tipi(self):
        g = {"tip": "OPEN_ROUTE", "seq": 7, "acked": ["ika", "yks"]}
        self.assertEqual(gk.tel_tipi({"iha_gonderim": g, "hakem": {
            "rota_seq": None, "no_route": {"seq": 7, "sebep": "DUSUK_GUVEN"}}}), "NO_ROUTE")
        self.assertEqual(gk.tel_tipi({"iha_gonderim": g, "hakem": {"rota_seq": 7, "no_route": None}}), "OPEN_ROUTE")
        self.assertEqual(gk.tel_tipi({"iha_gonderim": {**g, "tel_tipi": "NO_ROUTE"}, "hakem": {"rota_seq": 7}}),
                         "NO_ROUTE")
        self.assertIsNone(gk.tel_tipi({"iha_gonderim": {"tip": "HATA"}, "hakem": {}}))
        self.assertIsNone(gk.tel_tipi({"iha_gonderim": g, "hakem": {"rota_seq": 8, "no_route": {"seq": 9}}}))

    @staticmethod
    def _satir(h, lv, *, tel, basari):
        return {"rota_kaynak": "model", "harita": h, "senaryo": lv, "seed": 42,
                "rota_bulundu": True, "rota_dogru": True, "basari": basari, "hb_icinde": basari,
                "temas_sayisi": 0, "cikis_kodu": 0 if basari else 2, "sure_sim_ika": 70.0 if basari else None,
                "sure_sim_gorev": 107.0 if basari else 40.0, "varis_mesafesi_m": 0.2 if basari else 44.0,
                "duvar_saati_s": 5.0, "open_route_ack": ["ika", "yks"], "t_ika_go_ack": 40.0 if basari else None,
                "rota_insaat_geregi_gecilemez": False,
                "takip_hatasi_maks_m": 0.4 if basari else None, "takip_hatasi_ort_m": 0.2 if basari else None,
                "plan_takip_hatasi_maks_m": 0.3 if basari else None,
                "iha_gonderim": {"tip": "OPEN_ROUTE", "seq": 11, "acked": ["ika", "yks"]},
                "hakem": {"rota_seq": 11 if tel == "OPEN_ROUTE" else None,
                          "no_route": ({"seq": 11, "sebep": "DUSUK_GUVEN"} if tel == "NO_ROUTE" else None)},
                "link_olaylari": {"kayip": 0, "geri": 0}}

    def test_olaylar_tel_tipinden(self):
        with tempfile.TemporaryDirectory() as td:
            for ad, r in (("model_1_kolay_42", self._satir(1, "kolay", tel="OPEN_ROUTE", basari=True)),
                          ("model_2_zor_42", self._satir(2, "zor", tel="NO_ROUTE", basari=False))):
                (Path(td) / f"{ad}.json").write_text(json.dumps(r), encoding="utf-8")
            ol = gk.ozet_hesapla(Path(td))["kaynaklar"]["model"]["olaylar"]
        self.assertEqual(ol["open_route_yayini"], 1)
        self.assertEqual(ol["no_route_yayini"], 1)
        self.assertEqual(ol["guven_kapisi_reddi"], 1)
        self.assertEqual(ol["open_route_ack_ika_yks"], 1)
        self.assertEqual(ol["no_route_ack_ika_yks"], 1)

    def test_open_route_ack_alani_k4_anlaminda(self):
        """T214-B · çürütücü RED-2: `open_route_ack_ika_yks_n` H1-K4 kapısının adını taşır → yalnız TEL'de
        OPEN_ROUTE ∧ ACK [ika,yks] sayar (= olaylar.open_route_ack_ika_yks). Eski tanım NO_ROUTE ACK'larını
        da sayıyordu (model 45 ↔ OPEN_ROUTE 9); o sayım `karar_ack_ika_yks_n` adıyla ayrı durur."""
        with tempfile.TemporaryDirectory() as td:
            for ad, r in (("model_1_kolay_42", self._satir(1, "kolay", tel="OPEN_ROUTE", basari=True)),
                          ("model_2_zor_42", self._satir(2, "zor", tel="NO_ROUTE", basari=False))):
                (Path(td) / f"{ad}.json").write_text(json.dumps(r), encoding="utf-8")
            o = gk.ozet_hesapla(Path(td))["kaynaklar"]["model"]
        self.assertEqual(o["open_route_ack_ika_yks_n"], 1)
        self.assertEqual(o["karar_ack_ika_yks_n"], 2)
        disk = json.loads((KOSUM / "ozet_kosum.json").read_text(encoding="utf-8"))
        for k, o in disk["kaynaklar"].items():
            with self.subTest(kaynak=k):
                ol = o["olaylar"]
                self.assertEqual(o["open_route_ack_ika_yks_n"], ol["open_route_ack_ika_yks"])
                self.assertEqual(o["karar_ack_ika_yks_n"], ol["open_route_ack_ika_yks"] + ol["no_route_ack_ika_yks"])
                self.assertLessEqual(o["open_route_ack_ika_yks_n"], ol["open_route_yayini"])

    def test_ozet_hesapla_yazmaz_ve_disk_es(self):
        disk = json.loads((KOSUM / "ozet_kosum.json").read_text(encoding="utf-8"))
        with mock.patch.object(Path, "write_text", side_effect=AssertionError("ozet_hesapla YAZDI")):
            yeni = gk.ozet_hesapla(KOSUM)
        disk.pop("tarih")
        yeni.pop("tarih")
        self.assertEqual(disk, yeni, "ozet_kosum.json elle düzenlenmiş / bayat — gorev_kosumu.ozet_kur ile üret")

    def test_disk_guven_donusumu_yalniz_dusuk_guven(self):
        for r in _kosumlar():
            if r["rota_bulundu"] and gk.tel_tipi(r) == "NO_ROUTE":
                with self.subTest(k=_ad(r)):
                    self.assertEqual(((r.get("hakem") or {}).get("no_route") or {}).get("sebep"), "DUSUK_GUVEN")
                    self.assertFalse(r["basari"])


# ── F ───────────────────────────────────────────────────────────────────────
class F_GrafikNobetcisi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import sim_grafik
        cls.sg = sim_grafik
        cls.tmp = tempfile.TemporaryDirectory()
        cls.alt = sim_grafik.hepsini_ciz(sim_grafik.veri_yukle(), Path(cls.tmp.name))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_dort_grafik_svg_png_var(self):
        self.assertEqual(len(self.sg.GRAFIKLER), 4)
        for ad in self.sg.GRAFIKLER:
            for uz in ("svg", "png"):
                p = self.sg.SEKIL_DIR / f"{ad}.{uz}"
                with self.subTest(p=p.name):
                    self.assertTrue(p.is_file())
                    self.assertGreater(p.stat().st_size, 5000)

    def test_jsondan_yeniden_uretim_es(self):
        for ad in self.sg.GRAFIKLER:
            disk_png = (self.sg.SEKIL_DIR / f"{ad}.png").read_bytes()
            yeni_png = (Path(self.tmp.name) / f"{ad}.png").read_bytes()
            disk_svg = (self.sg.SEKIL_DIR / f"{ad}.svg").read_bytes().replace(b"\r\n", b"\n")
            yeni_svg = (Path(self.tmp.name) / f"{ad}.svg").read_bytes().replace(b"\r\n", b"\n")
            with self.subTest(dosya=ad):
                self.assertEqual(disk_png, yeni_png, "PNG bayat / elle düzenlenmiş — sim_grafik.py ile üret")
                self.assertEqual(disk_svg, yeni_svg, "SVG bayat / elle düzenlenmiş — sim_grafik.py ile üret")

    def test_alt_yazi_veri_kaynagi(self):
        self.assertEqual(set(self.alt), set(self.sg.GRAFIKLER))
        for ad, metin in self.alt.items():
            with self.subTest(ad=ad):
                self.assertIn("results/fdr_sprint_20260910/H1/kosum_tur3", metin)
                svg = (self.sg.SEKIL_DIR / f"{ad}.svg").read_text(encoding="utf-8")
                self.assertIn("results/fdr_sprint_20260910/H1/kosum_tur3", svg)      # dc:description


# ── G ───────────────────────────────────────────────────────────────────────
class G_Readme(unittest.TestCase):
    def test_readme_uretecle_es(self):
        import t214a_rapor
        disk = t214a_rapor.README_YOL.read_text(encoding="utf-8")
        self.assertEqual(disk, t214a_rapor.uret(), "README_T214A.md elle düzenlenmiş / bayat — t214a_rapor.py ile üret")


if __name__ == "__main__":
    unittest.main()
