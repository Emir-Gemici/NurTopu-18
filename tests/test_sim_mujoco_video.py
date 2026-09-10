"""T214-B · ON_KAYIT H1-K7 — MuJoCo görev simülasyonu VİDEOSU nöbetçileri (H1-K8 "video varlığı").

Kapılar:
  A  Saf yardımcılar (`simulation/mujoco/sim_video.py`): `faz_belirle` (uçuş profili → FIRLATMA/TARAMA;
     sürüş bayrakları → AKTARIM/IKA_GO/SURUS/VARIS), `kare_plani` (2× yarıya, 3× üçte bire seyreltir,
     0,25× dörder tekrarlar; her fazın ilk karesi yayınlanır), `ascii_katla` (HUD Türkçe → ASCII),
     HUD/kart çizimi 1280×720 verir.
  B  Kaydedici FİZİK DEĞİŞMEZLİĞİ (GPU'suz: çizim saplanır, `mj_forward` + İHA mocap GERÇEK):
     `_KareKaydedici.surus_adimla` ile `MuJoCoSurucu.adimla` aynı okunan poz dizisini, aynı qpos'u ve aynı
     temas sayısını verir (bit-eş); kareler 0,04 s katlarında. ÖLÇÜLMÜŞ KUSUR (T214-B ilk koşum): kare
     `bekle` sonunda çizilince `mj_forward` xpos'u tazeliyor, denetleyici 2 ms taze poz okuyordu
     (model_1_kolay_44 varış 0,286 ↔ 0,273 m) — mutasyon M1 bu kusuru geri koyar, B düşer.
  C  `iha_ucus.tara` kancası `kanca_aralik_s` olmadan reddedilir; tara ve kaydedici aynı mocap kuralını
     (`mocap_uygula`) kullanır.
  D  `video_ozeti.json` — ON_KAYIT H1-K7 eşikleri (bu testte yazılı, koddan okunmaz): süre ≥ 90 s,
     ≥ 24 FPS, 1280×720, üç kamera, HUD alanları; 3 koşum başarılı; boyut < 60 MB (görev tanımı);
     koşum JSON'u / durum.jsonl sha256'ları diskle eş; giriş kartı sayıları bugünkü ölçümle eş;
     değişmezlik koşumu (GT, rota render'dan bağımsız) tüm alanlarda kosum_tur3 ile eş.
  E  `OKUBENI.md` üreteç çıktısıyla eş (elle düzenlenmedi); mp4 yerelde varsa sha256 + kare sayısı özetle
     eş — mp4 git dışıdır (`*.mp4`): yoksa ATLANIR (ÖLÇÜLEMEDİ ≠ GEÇTİ; özet sha256'yı taşır).
Mutasyonlar: `results/fdr_sprint_20260910/H1/t214b/mutasyon_t214b.py` → `mutasyon_ciktisi.txt`.
"""
from __future__ import annotations

import hashlib
import inspect
import json
import sys
import tempfile
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
for _p in (str(KOK / "simulation" / "mujoco"), str(KOK / "simulation" / "scripts"),
           str(KOK / "codes"), str(KOK / "comms")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np                              # noqa: E402

import gorev_kosumu as gk                       # noqa: E402
import iha_ucus                                 # noqa: E402
import sim_video as sv                          # noqa: E402

ESIK_SURE_S = 90.0          # ON_KAYIT H1-K7 (önceden yazılı)
ESIK_FPS = 24.0             # ON_KAYIT H1-K7
BOYUT_SINIRI_MB = 60.0      # T214-B görev tanımı
OZET = sv.VIDEO_DIR / sv.OZET_ADI


def _sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# ── A ───────────────────────────────────────────────────────────────────────
class A_SafYardimcilar(unittest.TestCase):
    def test_faz_belirle(self):
        for faz, bek in (("rampa", "FIRLATMA"), ("kalkis", "FIRLATMA"), ("tirmanis", "FIRLATMA"),
                         ("tarama", "TARAMA"), ("donus", "TARAMA")):
            self.assertEqual(sv.faz_belirle({"kaynak": "ucus", "faz_profil": faz}), bek)
        s = {"kaynak": "surus"}
        self.assertEqual(sv.faz_belirle(s), "AKTARIM")
        self.assertEqual(sv.faz_belirle({**s, "ika_go": True}), "IKA_GO")
        self.assertEqual(sv.faz_belirle({**s, "ika_go": True, "surus": True}), "SURUS")
        self.assertEqual(sv.faz_belirle({**s, "ika_go": True, "surus": True, "surus_bitti": True}), "VARIS")
        self.assertEqual(set(sv.ANA_KAMERA) | {"ROTA"}, set(sv.FAZLAR))

    def test_kare_plani_hizlar(self):
        self.assertEqual(sv.kare_plani(["TARAMA"] * 10), [0, 2, 4, 6, 8])                 # 2×
        self.assertEqual(sv.kare_plani(["SURUS"] * 9), [0, 3, 6])                         # 3×
        self.assertEqual(sv.kare_plani(["AKTARIM"] * 4), [0, 1, 2, 3])                    # 1×
        self.assertEqual(sv.kare_plani(["IKA_GO"] * 2), [0, 0, 0, 0, 1, 1, 1, 1])         # 0,25×
        p = sv.kare_plani(["TARAMA"] * 3 + ["AKTARIM"] * 2 + ["SURUS"] * 4)
        self.assertEqual(p, [0, 2, 3, 4, 5, 8])                                           # her faz ilk karesi
        self.assertEqual(sv.FPS, int(gk.KARE_HZ_VIDEO))       # kayıt 25 Hz = video 25 FPS → 1× gerçek zaman
        self.assertGreaterEqual(sv.FPS, ESIK_FPS)

    def test_ascii_katla_ve_cizim(self):
        self.assertEqual(sv.ascii_katla("ÜRETİM MODELİ · YER GERÇEĞİ → ≥ ✓"), "URETIM MODELI | YER GERCEGI -> >= OK")
        self.assertTrue(all(ord(c) < 128 for c in sv.ascii_katla("İHA-İB ÇĞŞÖÜıçğşöü")))
        kart = sv.kart_ciz(["satır", ("büyük", 0.8, (255, 255, 255))], "başlık")
        self.assertEqual(kart.shape, (sv.YUK, sv.GEN, 3))
        t = np.zeros((sv.YUK, sv.GEN, 3), np.uint8)
        sv.hud_ciz(t, faz="SURUS", t=40.0, hiz=3.0, kaynak="model", kosum_ad="x", sira=1, toplam=3,
                   model_guven=0.9, satir={"kaynak": "surus", "acked": ["ika", "yks"], "hb_m": 3.2, "temas": 0})
        self.assertGreater(int(t[sv.ANA_H:].sum()), 0)                  # alt şerit çizildi
        self.assertGreater(int(t[2 * sv.KUC_H:sv.ANA_H, sv.ANA_W:].sum()), 0)   # bilgi kutusu
        self.assertEqual(sv.hiz_metni(None), "sim saati DONDURULDU (kart)")
        self.assertIn("3x", sv.hiz_metni(3.0))


# ── B ───────────────────────────────────────────────────────────────────────
class B_KaydediciFizikDegismezligi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import mujoco  # noqa: F401
        except ImportError:                       # pragma: no cover
            raise unittest.SkipTest("mujoco yok — ÖLÇÜLEMEDİ")

    @staticmethod
    def _kos(kayitli: bool):
        import mujoco
        import arena_mjcf
        from ika_surucu_mujoco import MuJoCoSurucu
        m = arena_mjcf.yukle(1, "kolay", 42)
        d = mujoco.MjData(m)
        s = MuJoCoSurucu(m, d)
        cizilen, pozlar = [], []
        with tempfile.TemporaryDirectory() as td:
            k = None
            if kayitli:
                k = gk._KareKaydedici(Path(td) / "kv")
                ids = tuple(int(m.body_mocapid[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, a)])
                            for a in ("iha", "parasut"))
                k._cizici = lambda mm: (mm, None, ids)                    # GL yok; mj_forward + mocap gerçek
                k.kare = lambda mm, dd, t, durum: cizilen.append(round(float(dd.time), 6))
            try:
                for i in range(30):
                    s.hiz_ver(0.9, 0.6 if i % 5 else 0.9)
                    pozlar.append(s.konum_al())
                    dt = 0.05 if i % 7 == 0 else 0.1
                    if k is None:
                        s.adimla(dt)
                    else:
                        k.surus_adimla(s, m, d, dt, lambda: 31.98 + float(d.time), lambda: {})
                pozlar.append(s.konum_al())
            finally:
                if k is not None:
                    k.kapat()
        return pozlar, d.qpos.copy(), float(d.time), int(s.temas_sayisi), cizilen

    def test_kaydedici_trajektoriyi_degistirmez(self):
        p0, q0, t0, c0, _ = self._kos(False)
        p1, q1, t1, c1, ciz = self._kos(True)
        self.assertEqual(t0, t1)
        self.assertEqual(p0, p1, "kaydedici denetleyicinin okuduğu pozu değiştirdi (bekle sonunda mj_forward?)")
        self.assertTrue(np.array_equal(q0, q1), "kaydedici fizik trajektorisini değiştirdi")
        self.assertEqual(c0, c1)
        self.assertGreater(abs(p0[-1][0] - p0[0][0]) + abs(p0[-1][1] - p0[0][1]), 0.5)   # İKA gerçekten sürüldü
        adim = 1.0 / gk.KARE_HZ_VIDEO
        self.assertEqual(len(ciz), int(np.ceil(t1 / adim - 1e-9)))
        self.assertTrue(all(abs(t / adim - round(t / adim)) < 1e-6 for t in ciz))

    def test_alt_adim_sayisi_adimla_ile_es(self):
        class Sayac:
            def __init__(self, d, ts):
                self.d, self.ts, self.n = d, ts, 0

            def adimla(self, dt):
                k = max(1, int(round(dt / self.ts))) if dt > 0 else 0
                self.n += k
                self.d.time += k * self.ts

        class M:
            class opt:
                timestep = 0.002

        class D:
            time = 0.0

        for dt in (0.0, 0.002, 0.013, 0.05, 0.1, 0.5, 1.0):
            with self.subTest(dt=dt), tempfile.TemporaryDirectory() as td:
                k = gk._KareKaydedici(Path(td))
                cizilen = []
                k.surus_karesi = lambda m, d, t, durum: cizilen.append(d.time)
                d = D()
                s = Sayac(d, 0.002)
                k.surus_adimla(s, M, d, dt, lambda: d.time, lambda: {})
                k.kapat()
                self.assertEqual(s.n, max(1, int(round(dt / 0.002))) if dt > 0 else 0)
                self.assertTrue(all(t < d.time - 1e-12 or dt == 0 for t in cizilen), "bekle SONUNDA kare çizildi")


# ── C ───────────────────────────────────────────────────────────────────────
class C_TaraKancasi(unittest.TestCase):
    def test_kanca_araliksiz_reddedilir(self):
        with tempfile.TemporaryDirectory() as td, self.assertRaises(ValueError):
            iha_ucus.tara(1, "kolay", 42, out=Path(td), kare_kancasi=lambda *a: None)

    def test_tek_mocap_kurali(self):
        kaynak = inspect.getsource(iha_ucus.tara)
        self.assertIn("return mocap_uygula(d, prof, t, iha, par)", kaynak)
        self.assertIn("iha_ucus.mocap_uygula(", inspect.getsource(gk._KareKaydedici.surus_karesi))


# ── D ───────────────────────────────────────────────────────────────────────
class D_VideoOzeti(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.oz = json.loads(OZET.read_text(encoding="utf-8"))

    def test_h1_k7_esikleri(self):
        oz = self.oz
        self.assertGreaterEqual(oz["sure_s"], ESIK_SURE_S)
        self.assertGreaterEqual(oz["okunan"]["fps"], ESIK_FPS)
        self.assertEqual((oz["okunan"]["genislik"], oz["okunan"]["yukseklik"]), (1280, 720))
        self.assertTrue(oz["okunan"]["ilk_kare_okundu"])
        self.assertAlmostEqual(oz["sure_s"], oz["okunan"]["kare_n"] / oz["okunan"]["fps"], places=1)
        self.assertEqual(oz["okunan"]["kare_n"], oz["yazilan_kare_n"])
        self.assertEqual(set(oz["kameralar"]), {"iha_nadir", "ucuncu_sahis", "ika_takip"})
        for alan in ("sim saati", "faz", "rota kaynağı", "OPEN_ROUTE ACK", "SENTETİK"):
            self.assertTrue(any(alan in h for h in oz["hud_alanlari"]), alan)
        self.assertLess(oz["boyut_mb"], BOYUT_SINIRI_MB)
        self.assertIn("SENTETİK", oz["etiket"])
        self.assertIn("BEYAN GEREKLİ", oz["link"])

    def test_kosumlar_ve_kanit_butunlugu(self):
        ks = self.oz["kosumlar"]
        self.assertEqual([k["senaryo"] for k in ks], ["kolay", "orta", "zor"])
        for k in ks:
            with self.subTest(k=k["json"]):
                self.assertTrue(k["basari"])
                p = sv.VIDEO_DIR / k["json"]
                self.assertEqual(sv.sha256_metin(p), k["json_sha256"])      # CRLF/LF bağımsız (autocrlf)
                r = json.loads(p.read_text(encoding="utf-8"))
                self.assertTrue(r["kare_kaydet"])
                self.assertEqual(r["kare_hz_video"], gk.KARE_HZ_VIDEO)
                durum = p.with_suffix("") / "kareler_video" / "durum.jsonl"
                self.assertEqual(sv.sha256_metin(durum), k["durum_sha256"])
                crlf = durum.read_bytes().replace(b"\n", b"\r\n")                  # checkout'u taklit et
                self.assertEqual(hashlib.sha256(crlf.replace(b"\r\n", b"\n")).hexdigest(), k["durum_sha256"])
                satir_n = sum(1 for s in durum.read_text(encoding="utf-8").splitlines() if s.strip())
                self.assertEqual(satir_n, r["kare_n_video"])
                self.assertEqual(gk.basari_hesapla(r["cikis_kodu"], r["rota_bulundu"], r["hb_icinde"],
                                                   r["temas_sayisi"], r["sure_sim_ika"]), r["basari"])

    def test_giris_karti_sayilari_guncel(self):
        self.assertEqual(self.oz["genel_sayilar"], sv._genel_sayilar())

    def test_degismezlik_kosumu_tur3_ile_es(self):
        dz = json.loads((sv.KOSUM_DIR / "degismezlik.json").read_text(encoding="utf-8"))
        self.assertTrue(dz["hepsi_es"], {a: v for a, v in dz["alanlar"].items() if not v["es"]})
        self.assertGreater(dz["kare_n_video"], 1000)
        self.assertEqual(self.oz.get("degismezlik", {}).get("hepsi_es"), True)


# ── E ───────────────────────────────────────────────────────────────────────
class E_OkubeniVeMp4(unittest.TestCase):
    def test_okubeni_uretecle_es(self):
        oz = json.loads(OZET.read_text(encoding="utf-8"))
        disk = (sv.VIDEO_DIR / sv.OKUBENI_ADI).read_text(encoding="utf-8")
        self.assertEqual(disk, sv.okubeni_uret(oz), "OKUBENI.md elle düzenlenmiş / bayat — sim_video.py ile üret")
        self.assertIn(oz["sha256"], disk)

    def test_mp4_yerelde_varsa_ozetle_es(self):
        oz = json.loads(OZET.read_text(encoding="utf-8"))
        mp4 = KOK / oz["dosya"]
        if not mp4.is_file():
            self.skipTest("mp4 git dışı ve bu ağaçta yok — ÖLÇÜLEMEDİ (sha256 özette)")
        self.assertEqual(sv.sha256_dosya(mp4), oz["sha256"])
        import cv2
        cap = cv2.VideoCapture(str(mp4))
        try:
            self.assertEqual(int(cap.get(cv2.CAP_PROP_FRAME_COUNT)), oz["okunan"]["kare_n"])
            self.assertGreaterEqual(cap.get(cv2.CAP_PROP_FPS), ESIK_FPS)
        finally:
            cap.release()


if __name__ == "__main__":
    unittest.main()
