"""T212 · SIM-1 nöbetçileri — MuJoCo arena üreteci, araç modelleri, tarama sözleşmesi.

Kapılar (ON_KAYIT H1-K1/K2/K8): determinizm (aynı girdi → bayt-eş), 15 harita MJCF
üretilir + `mujoco.MjModel.from_xml_path` ile yüklenir, yönerge geometrisi (İHA-İB
30×30 mavi, HB kırmızı H 2×2, tek açık yol), tarama çıktı sözleşmesi (poses.csv
n,t,x,y,z,yaw; kare sayısı > 0; kare boyu), kamera yön sözleşmesi (görüntü sağı =
burun, mozaik kuzey-yukarı), 3 mutasyon (H rengi, İB kenarı, seed).
GPU gerekmez; küçük çözünürlük; hedef < 60 s.
"""
import hashlib
import json
import math
import sys
import tempfile
import time
import unittest
from pathlib import Path

import numpy as np

KOK = Path(__file__).resolve().parents[1]
for _p in (str(KOK), str(KOK / "simulation" / "mujoco"), str(KOK / "simulation" / "scripts"),
           str(KOK / "codes")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import mujoco                                   # noqa: E402
import arena                                    # noqa: E402
import arena_mjcf                               # noqa: E402
import araclar                                  # noqa: E402
import iha_ucus                                 # noqa: E402
import iha_haritala                             # noqa: E402

HARITALAR = [(h, lv) for h in range(1, arena.HARITA_N + 1) for lv in arena.SCENARIOS]


class Determinizm(unittest.TestCase):
    def test_ayni_girdi_bayt_es_xml(self):
        a = arena_mjcf.uret(2, "orta", 42)
        b = arena_mjcf.uret(2, "orta", 42)
        self.assertEqual(a, b)
        self.assertEqual(hashlib.sha256(a.encode()).hexdigest(),
                         arena_mjcf.kanonik_sha256(2, "orta", 42))

    def test_mutasyon_seed_degisince_xml_degisir(self):
        self.assertNotEqual(arena_mjcf.uret(2, "orta", 42), arena_mjcf.uret(2, "orta", 43))

    def test_htab_dokusu_deterministik(self):
        H = arena.harita(3, "zor")
        a = arena_mjcf.htab_dokusu(H, 4.0)
        b = arena_mjcf.htab_dokusu(H, 4.0)
        self.assertTrue(np.array_equal(a, b))
        self.assertEqual(a.shape, (arena_mjcf.HTAB_DOKU_PX, arena_mjcf.HTAB_DOKU_PX, 3))

    def test_kanonik_xml_goreli_dizin(self):
        xml = arena_mjcf.uret(1, "kolay")
        self.assertIn('meshdir="mesh" texturedir="dokular"', xml)
        self.assertNotIn(str(arena_mjcf.BURASI), xml)


class OnBesHarita(unittest.TestCase):
    """15 MJCF üretilir, dosyaya yazılır ve from_xml_path ile yüklenir; yönerge kontrolü."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.modeller = {}
        t0 = time.perf_counter()
        for h, lv in HARITALAR:
            p = arena_mjcf.yaz(h, lv, Path(cls.tmp.name) / f"arena_{h}_{lv}.xml")
            cls.modeller[(h, lv)] = mujoco.MjModel.from_xml_path(str(p))
        cls.sure = time.perf_counter() - t0

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_15_harita_yuklendi(self):
        self.assertEqual(len(self.modeller), 15)
        for m in self.modeller.values():
            self.assertGreater(m.ngeom, 100)

    def test_yonerge_geometrisi_15_15(self):
        dusen = []
        for (h, lv), m in self.modeller.items():
            k = arena_mjcf.yonerge_kontrol(m, h, lv)
            for ad, v in k.items():
                if not v["ok"]:
                    dusen.append((h, lv, ad, v["deger"]))
        self.assertEqual(dusen, [], f"yönerge maddeleri düştü: {dusen}")

    def test_acik_yol_bariyersiz_ve_gizli(self):
        """Açık yolun bariyeri yok; XML'de yolu ele veren renk/geom yok (yalnız yorum satırı)."""
        for (h, lv), m in self.modeller.items():
            acik = arena.harita(h, lv)["open"]
            self.assertLess(mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, f"bariyer_{acik}"), 0)
            for r in (1, 2, 3):
                if r != acik:
                    self.assertGreaterEqual(mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, f"bariyer_{r}"), 0)

    def test_ika_ddr_olculeri(self):
        m = self.modeller[(1, "kolay")]
        ika = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "ika")
        self.assertAlmostEqual(float(m.body_subtreemass[ika]), araclar.IKA_KUTLE_KG, delta=0.05)
        sol = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "teker_on_sol")
        sag = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "teker_on_sag")
        self.assertAlmostEqual(float(m.body_pos[sol][1] - m.body_pos[sag][1]), araclar.IKA_IZ_M, places=6)
        g = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, "g_teker_on_sol")
        self.assertAlmostEqual(float(m.geom_size[g][0]), araclar.IKA_TEKER_R, places=6)
        self.assertEqual(m.nu, 4)
        self.assertAlmostEqual(float(m.actuator_ctrlrange[0][1]), araclar.IKA_VMAX_MS / araclar.IKA_TEKER_R, places=2)

    def test_ika_fizikte_devrilmeden_durur(self):
        m = self.modeller[(1, "kolay")]
        d = mujoco.MjData(m)
        for _ in range(1500):
            mujoco.mj_step(m, d)
        ika = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "ika")
        z = float(d.xpos[ika][2])
        self.assertGreater(z, araclar.IKA_TEKER_R - 0.01)
        self.assertLess(z, araclar.IKA_TEKER_R + 0.05)
        self.assertGreater(float(d.xmat[ika].reshape(3, 3)[2, 2]), 0.99, "İKA devrildi")

    def test_uretim_hizi(self):
        self.assertLess(self.sure, 45.0, f"15 harita üret+yaz+yükle {self.sure:.1f} s")


class Mutasyonlar(unittest.TestCase):
    """Yönerge kontrolü gerçekten ayırt ediyor mu: bozulmuş XML'de İLGİLİ madde düşmeli."""

    def _yukle(self, xml):
        return mujoco.MjModel.from_xml_string(xml)

    def test_mutasyon_H_beyaz_olunca_duser(self):
        xml = arena_mjcf.uret(1, "kolay", asset_kok=arena_mjcf.BURASI)
        arena_mjcf.hazirla(1, "kolay")
        bozuk = xml.replace('rgba="0.85 0.08 0.08 1.00"', 'rgba="1.00 1.00 1.00 1.00"')
        self.assertNotEqual(xml, bozuk)
        k = arena_mjcf.yonerge_kontrol(self._yukle(bozuk), 1, "kolay")
        self.assertFalse(k["hb_kirmizi_H_2x2"]["ok"])
        self.assertTrue(arena_mjcf.yonerge_kontrol(self._yukle(xml), 1, "kolay")["hb_kirmizi_H_2x2"]["ok"])

    def test_mutasyon_ib_8x8_olunca_duser(self):
        xml = arena_mjcf.uret(1, "kolay", asset_kok=arena_mjcf.BURASI)
        bozuk = xml.replace('size="15.000 15.000 0.010"', 'size="4.000 4.000 0.010"')
        self.assertNotEqual(xml, bozuk)
        k = arena_mjcf.yonerge_kontrol(self._yukle(bozuk), 1, "kolay")
        self.assertFalse(k["iha_ib_30x30_mavi"]["ok"])

    def test_mutasyon_acik_yola_bariyer_konunca_duser(self):
        xml = arena_mjcf.uret(1, "kolay", asset_kok=arena_mjcf.BURASI)
        acik = arena.harita(1, "kolay")["open"]
        kapali = next(r for r in (1, 2, 3) if r != acik)
        bozuk = xml.replace(f'name="bariyer_{kapali}"', f'name="bariyer_{acik}"')
        k = arena_mjcf.yonerge_kontrol(self._yukle(bozuk), 1, "kolay")
        self.assertFalse(k["acik_yol_tek_bariyersiz"]["ok"])


class TaramaSozlesmesi(unittest.TestCase):
    """Küçük çözünürlükte kısa uçuş: poses.csv sütunları, kare sayısı/boyu, kabul edilen kareler."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name) / "harita_1_kolay" / "iha_scan"
        cls.ozet = iha_ucus.tara(1, "kolay", out=cls.out, res=96, fizik=False, onizleme=False)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_poses_csv_sozlesmesi(self):
        satirlar = (self.out / "poses.csv").read_text().strip().splitlines()
        self.assertEqual(len(satirlar), self.ozet["kare_n"])
        for i, s in enumerate(satirlar):
            parca = s.split(",")
            self.assertEqual(len(parca), 6, "n,t,x,y,z,yaw")
            self.assertEqual(int(parca[0]), i)
        pozlar = iha_haritala.poz_oku(self.out / "poses.csv")
        self.assertEqual(len(pozlar), self.ozet["kare_n"])
        for n in range(self.ozet["kare_n"]):
            self.assertTrue((self.out / "kareler" / f"scan_{n:05d}.jpg").is_file())

    def test_kare_sayisi_ve_boyu(self):
        import cv2
        self.assertGreater(self.ozet["kare_n"], 0)
        im = cv2.imread(str(self.out / "kareler" / "scan_00000.jpg"))
        self.assertEqual(im.shape[:2], (96, 96))

    def test_tarama_bacaklari_iha_haritala_suzgecinden_gecer(self):
        pozlar = iha_haritala.poz_oku(self.out / "poses.csv")
        kabul = [k for k, p in pozlar.items() if iha_ucus.kare_kabul(*p)]
        self.assertGreaterEqual(len(kabul), 12, "en az 4 bacak × 3 kare")
        self.assertEqual(len(kabul), self.ozet["kabul_edilen_kare"])
        self.assertGreaterEqual(self.ozet["htab_kapsama_orani"], 0.99)
        for k in kabul:
            x, y, z, yaw = pozlar[k]
            self.assertAlmostEqual(z, iha_haritala.SCAN_Z, delta=iha_haritala.Z_TOL)
            self.assertAlmostEqual(abs(yaw), math.pi / 2, delta=iha_haritala.YAW_TOL)

    def test_meta_txt_anahtarlari(self):
        meta = iha_haritala._meta_oku(self.out)
        self.assertEqual(iha_haritala._htab_merkez(meta, None), (0.0, 0.0))
        self.assertIsNotNone(iha_haritala._meta_xy(meta, "KB_XY"))
        self.assertIsNotNone(iha_haritala._meta_xy(meta, "HB_XY"))
        self.assertEqual(meta["SIM"], "mujoco-kinematik")

    def test_mozaik_kurulur(self):
        pozlar = iha_haritala.poz_oku(self.out / "poses.csv")
        moz, n = iha_haritala.mozaik_kur(self.out / "kareler", pozlar, 0.0, 0.0)
        self.assertEqual(n, self.ozet["kabul_edilen_kare"])
        self.assertEqual(moz.shape, (iha_haritala.MOZ_PX, iha_haritala.MOZ_PX, 3))
        # HTAB penceresinin büyük kısmı arka plan grisi değil
        c, k = iha_haritala.MOZ_PX // 2, int(round(arena.HTAB_HALF / iha_haritala.MPP))
        pen = moz[c - k:c + k, c - k:c + k]
        bg = np.all(pen == iha_haritala.BG_GRI, axis=2).mean()
        self.assertLess(bg, 0.02)

    def test_mozaik_yer_kaydi_ib_bati_kenari(self):
        """T213-A KUSUR KAPISI: mozaikteki İHA-İB batı kenarı (x = 27 m) dünya→piksel dönüşümünün
        dediği sütunda olmalı. T212 profili düz tarama bacağına ±26,2° yatış sızdırıyordu →
        nadir 14,8 m kayıyor, İB kenarı ~710. sütunda çıkıyordu (beklenen ~1006)."""
        pozlar = iha_haritala.poz_oku(self.out / "poses.csv")
        for birlestirme in iha_haritala.BIRLESTIRMELER:
            moz, _ = iha_haritala.mozaik_kur(self.out / "kareler", pozlar, 0.0, 0.0, birlestirme=birlestirme)
            mavi = (moz[..., 0] > 150) & (moz[..., 2] < 100)
            sutun = np.nonzero(mavi.sum(0) > 20)[0]
            self.assertGreater(len(sutun), 0, f"{birlestirme}: mozaikte İB mavisi yok")
            beklenen = iha_haritala.dunya_to_piksel((arena_mjcf.IHA_IB_MERKEZ_X - arena_mjcf.IHA_IB_KENAR_M / 2, 0.0),
                                                    0.0, 0.0)[0]
            self.assertLess(abs(int(sutun.min()) - beklenen), 20,
                            f"{birlestirme}: İB batı kenarı {sutun.min()} px, beklenen {beklenen} px (yer kaydı bozuk)")

    def test_tarama_bacaginda_yatis_sifir(self):
        """Kabul edilen (düz bacak) karelerde roll = 0; dönüş yaylarında ≠ 0 (profil hâlâ yatıyor)."""
        p = iha_ucus.UcusProfili()
        kabul, donus = [], []
        for t in range(0, int(p.t_inis) + 1):
            pos, yaw, _pitch, roll, faz = p.durum(float(t))
            if iha_ucus.kare_kabul(pos[0], pos[1], pos[2], yaw):
                kabul.append(roll)
            elif faz == "donus" and abs(pos[2] - iha_haritala.SCAN_Z) < 0.1:
                donus.append(roll)
        self.assertGreaterEqual(len(kabul), 12)
        self.assertTrue(all(abs(r) < 1e-9 for r in kabul), f"düz bacakta yatış var: {kabul}")
        self.assertTrue(donus and all(abs(r) > math.radians(5) for r in donus), "dönüşte yatış yok")

    def test_ucus_profili_dunya_disina_cikmaz_ve_ib_ye_iner(self):
        p = iha_ucus.UcusProfili()
        self.assertTrue(np.all(np.abs(p.xyz[:, :2]) < arena.UB_HALF))
        self.assertAlmostEqual(float(p.xyz[-1][0]), arena_mjcf.IHA_IB_MERKEZ_X)
        self.assertLess(float(p.xyz[-1][2]), 0.5)
        self.assertLess(p.t_tarama0, p.t_parasut)
        self.assertLess(p.t_parasut, p.t_inis)


class KameraYonSozlesmesi(unittest.TestCase):
    """Nadir kamera: görüntü sağı = burun (+X gövde), yukarısı = sol kanat. Kuzeye bakan İHA'da
    doğu (İHA-İB mavisi) görüntünün ALT yarısında, kuzey (H) SAĞ yarısında olmalı."""

    def test_kuzeye_bakan_karede_ib_altta(self):
        import cv2
        m = arena_mjcf.yukle(1, "kolay", kam_res=160)
        d = mujoco.MjData(m)
        iha = m.body_mocapid[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "iha")]
        d.mocap_pos[iha] = [arena_mjcf.IHA_IB_MERKEZ_X - 14.0, 0.0, 30.0]      # İB'nin batı kenarı
        d.mocap_quat[iha] = iha_ucus.quat_ypr(math.pi / 2, 0.0, 0.0)           # burun kuzey
        mujoco.mj_forward(m, d)
        r = mujoco.Renderer(m, 160, 160)
        r.update_scene(d, camera="scan_camera")
        img = r.render(); r.close()
        mavi = (img[..., 2] > 150) & (img[..., 0] < 100)
        ust, alt = mavi[:80].mean(), mavi[80:].mean()
        self.assertGreater(alt, 0.3, f"İB altta olmalı: üst {ust:.2f} alt {alt:.2f}")
        self.assertLess(ust, 0.05)

    def test_hfov_sozlesmesi(self):
        self.assertEqual(arena_mjcf.HFOV_RAD, iha_haritala.HFOV)
        self.assertEqual(iha_ucus.SCAN_Z, iha_haritala.SCAN_Z)


class Varyantlar(unittest.TestCase):
    """T213-A (K3-b) render varyantları: taban bayt-eş, v1 yalnız doku, v2 ışık, v3 moloz mesh."""

    def test_varsayilan_v1_ve_taban_t212_sha_es(self):
        """Karar (RAPOR_K3B §5): varsayılan v1; taban varyantı T212 XML'iyle bayt-eş kalır."""
        self.assertEqual(arena_mjcf.VARYANT_VARSAYILAN, "v1")
        self.assertEqual(arena_mjcf.uret(1, "kolay"), arena_mjcf.uret(1, "kolay", varyant="v1"))
        self.assertNotEqual(arena_mjcf.uret(1, "kolay"), arena_mjcf.uret(1, "kolay", varyant="taban"))
        ozet = KOK / "results" / "fdr_sprint_20260910" / "H1" / "arena_ozeti_15.json"
        if ozet.is_file():   # T212 kanıtı: taban varyantı o günkü XML'le bayt-eş kalmalı
            sha = json.loads(ozet.read_text(encoding="utf-8"))["sha256"]["1_kolay"]
            self.assertEqual(hashlib.sha256(arena_mjcf.uret(1, "kolay", varyant="taban").encode()).hexdigest(), sha)

    def test_v1_yalniz_doku_dosyalari_degisir(self):
        import difflib
        a = arena_mjcf.uret(2, "orta", varyant="taban").splitlines()
        b = arena_mjcf.uret(2, "orta", varyant="v1").splitlines()
        fark = [l for l in difflib.unified_diff(a, b, lineterm="", n=0)
                if l[:1] in "+-" and not l.startswith(("+++", "---"))]
        self.assertEqual(len(fark), 4, fark)
        self.assertTrue(all("uretilen/" in l for l in fark), fark)

    def test_v2_isik_golge(self):
        x1 = arena_mjcf.uret(1, "kolay", varyant="v1")
        x2 = arena_mjcf.uret(1, "kolay", varyant="v2")
        self.assertIn('castshadow="true"', x2)
        self.assertNotEqual(x1, x2)
        amb = lambda x: float(x.split('<headlight ambient="')[1].split()[0])
        self.assertLess(amb(x2), amb(x1))
        dir2 = [float(v) for v in x2.split('<light name="gunes"')[1].split('dir="')[1].split('"')[0].split()]
        self.assertLess(abs(dir2[2]), 0.75, "v2 güneşi alçak olmalı (uzun gölge)")

    def test_v3_moloz_mesh(self):
        m = arena_mjcf.yukle(1, "kolay", varyant="v3", kam_res=64)
        adlar = [mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, i) or "" for i in range(m.ngeom)]
        moloz = [i for i, a in enumerate(adlar) if a.startswith(("moloz_", "tikama_", "chicane_"))]
        self.assertGreater(len(moloz), 50)
        self.assertTrue(all(m.geom_type[i] == mujoco.mjtGeom.mjGEOM_MESH for i in moloz))
        self.assertGreaterEqual(m.nmesh, len(moloz) + len(araclar.MESH_ADLARI))
        k = arena_mjcf.yonerge_kontrol(m, 1, "kolay")
        self.assertTrue(all(v["ok"] for v in k.values()), k)

    def test_v1_doku_deterministik(self):
        H = arena.harita(4, "zor")
        a = arena_mjcf.htab_dokusu(H, 4.0, varyant="v1")
        b = arena_mjcf.htab_dokusu(H, 4.0, varyant="v1")
        self.assertTrue(np.array_equal(a, b))
        self.assertEqual(a.shape, (arena_mjcf.HTAB_DOKU_PX, arena_mjcf.HTAB_DOKU_PX, 3))

    def test_yol_koridor_uv_geometrisi(self):
        """Merkez hattında |d| ≈ 0, normal boyunca 1 m'de |d| ≈ 1, s artan; uçlar uzatma kadar."""
        H = arena.harita(1, "kolay")
        N, mpp = arena_mjcf.HTAB_DOKU_PX, arena.HTAB / arena_mjcf.HTAB_DOKU_PX
        p = H["paths"][H["open"]]
        ys, xs, s, d = arena_mjcf.yol_koridor_uv(p, N, mpp, 3.0)
        d_map = np.full((N, N), np.nan, np.float32); d_map[ys, xs] = d
        s_map = np.full((N, N), np.nan, np.float32); s_map[ys, xs] = s
        onceki_s = -1.0
        for i in range(2, len(p) - 2, 5):
            x, y = p[i]
            px, py = int(round((x + 25) / mpp)), int(round((25 - y) / mpp))
            self.assertLess(abs(d_map[py, px]), 2.5 * mpp, f"nokta {i}: d={d_map[py, px]}")
            self.assertGreater(s_map[py, px], onceki_s); onceki_s = s_map[py, px]
            (x1, y1), (x2, y2) = p[i - 1], p[i + 1]
            L = math.hypot(x2 - x1, y2 - y1)
            nx, ny = -(y2 - y1) / L, (x2 - x1) / L
            qx, qy = int(round((x + nx + 25) / mpp)), int(round((25 - (y + ny)) / mpp))
            self.assertAlmostEqual(abs(float(d_map[qy, qx])), 1.0, delta=0.12)
        # uzatma: KB'nin 2 m ötesi (yol yönünün tersi) uzatmasız koridor DIŞI, 3 m uzatmayla İÇİ
        (x0, y0), (x1, y1) = p[0], p[1]
        L = math.hypot(x1 - x0, y1 - y0)
        ox, oy = x0 - (x1 - x0) / L * 2.0, y0 - (y1 - y0) / L * 2.0
        px, py = int(round((ox + 25) / mpp)), int(round((25 - oy) / mpp))
        self.assertTrue(np.isnan(d_map[py, px]) or not np.isfinite(d_map[py, px]))
        ys2, xs2, s2, d2 = arena_mjcf.yol_koridor_uv(p, N, mpp, 3.0, uzatma_m=3.0)
        d_map2 = np.full((N, N), np.nan, np.float32); d_map2[ys2, xs2] = d2
        self.assertTrue(np.isfinite(d_map2[py, px]) and abs(d_map2[py, px]) < 2.5 * mpp)

    def test_kaynak_olcekleri_gercek(self):
        """Yol şeridi kırpması fiziksel olarak ~4 m; V1 zemin yaması gerçek ölçekte (büyütme yok)."""
        yol = arena_mjcf._kaynak_oku("yol_serit_kaynak")
        self.assertAlmostEqual(yol.shape[1] * arena_mjcf.KAYNAK_MPP["yol_serit_kaynak"], 4.0, delta=0.15)
        self.assertTrue(3.5 <= arena_mjcf.YOL_GENISLIK_M <= 4.0)
        mpp = arena.HTAB / arena_mjcf.HTAB_DOKU_PX
        for z in arena_mjcf.ZEMIN_DOKULARI:
            olcek = arena_mjcf.KAYNAK_MPP[f"{z}_kaynak"] / mpp
            k = int(round(arena_mjcf.YAMA_PX_V1 / olcek))          # kaynaktan alınan kenar (px)
            src = arena_mjcf._kaynak_oku(f"{z}_kaynak")
            self.assertLess(olcek, 1.0, "kaynak dokudan KÜÇÜLTÜLEREK döşenmeli (büyütme yok)")
            self.assertLessEqual(k, min(src.shape[:2]), f"{z}: yama {k} px kaynağa sığmıyor")

    def test_mutasyon_bilinmeyen_varyant_reddedilir(self):
        with self.assertRaises(ValueError):
            arena_mjcf.uret(1, "kolay", varyant="v9")
        with self.assertRaises(ValueError):
            arena_mjcf.htab_dokusu(arena.harita(1, "kolay"), 6.0, varyant="v1", zemin_dokusu="cim")


class MeshVarliklari(unittest.TestCase):
    def test_mesh_dosyalari_var_ve_yuklenir(self):
        yollar = araclar.mesh_uret()
        for ad, p in yollar.items():
            self.assertTrue(p.is_file(), ad)
            self.assertGreater(p.stat().st_size, 500)

    def test_iha_kanat_acikligi(self):
        import trimesh
        k = trimesh.load(str(araclar.MESH_DIR / "iha_kanat.stl"))
        self.assertAlmostEqual(float(k.extents[1]), araclar.IHA_ACIKLIK, delta=0.05)


if __name__ == "__main__":
    unittest.main()
