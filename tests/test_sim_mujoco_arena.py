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
