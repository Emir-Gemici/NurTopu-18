"""T220 NOBETCISI — Jetson oturumunun (9 Eylul, Halil) gelistiriciden istekleri.

Kaynak: JETSON_OTURUM_DURUMU_20260909.md SS5, results/jetson_20260906/K10_LISTE.md,
results/fdr_sprint_20260910/ON_KAYIT.md SS5.10 (cv2 GStreamer denetimi kusuru).

  K2   kabul kumeleri depoda (`data/kabul/`), registry yollari depo kokune GORELI (madde 16),
       parmak izi DEGISMEDI (bayt-es kopya), okuyucular goreli yolu cozer, .gitignore istisnasi,
       paket registry aynasi bayt-es.
  G4   `177_pc_referans_v36.py`: --help, referans JSON semasi + model sha == defter,
       `karsilastir` saf fonksiyonu (GECTI / DUSTU / OLCULEMEDI) + mutasyon.
  K10  tests/*.py icinde ciplak `O:/navitas` ya da `O:\\navitas` YOK (desen kilidi);
       `depo_yollari` yardimcisi turetir; ana depo adaylari worktree kalibini bulur.
  K1   JETSON_KILAVUZ.md basligi ve SS5 FPS satiri Orin NX bandi (~~cizili~~ + Orin Nano),
       iki kopyada da.
  cv2  Orin kurulum betikleri GStreamer denetimi: "GStreamer:" satiri YES mi — sahte cv2 ile
       YES -> True, NO -> False; naif eski ifade NO'da da True verirdi (kontrol);
       scripts/ <-> jetson_paket/ bayt-es.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from importlib import import_module
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
for _alt in ("tests", "codes", "scripts/olcum", "comms"):
    if str(KOK / _alt) not in sys.path:
        sys.path.insert(0, str(KOK / _alt))

from depo_yollari import ana_depo_adaylari  # noqa: E402

REGISTRY = KOK / "config" / "model_registry.json"
PAKET_REGISTRY = KOK / "jetson_paket" / "config" / "model_registry.json"
KABUL = KOK / "data" / "kabul"
BETIK_177 = KOK / "scripts" / "olcum" / "177_pc_referans_v36.py"
REFERANS = KOK / "results" / "fdr_sprint_20260910" / "H8" / "pc_referans_v36.json"
KILAVUZLAR = (KOK / "JETSON_KILAVUZ.md", KOK / "jetson_paket" / "JETSON_KILAVUZ.md")
ORIN_BETIKLER = ("orin_nano_root_kurulum.sh", "orin_nano_venv_kurulum.sh")
PY = sys.executable

CIPLAK_O_NAVITAS = re.compile(r"O:[\\/]{1,2}navitas")


def _defter():
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def _profil():
    d = _defter()
    return d["profiles"][d["default_profile"]]


def _m177():
    import importlib.util
    spec = importlib.util.spec_from_file_location("m177_t220", BETIK_177)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ═══════════════════════════════════════════════════════════════════════════
# K2 — kabul kumeleri depoda, registry yollari goreli
# ═══════════════════════════════════════════════════════════════════════════
class K2KabulKumeleriDepoda(unittest.TestCase):

    def test_registry_yollari_GORELI_ve_ciplak_degil(self):
        p = _profil()
        for alan in ("kabul_kumesi", "kabul_kumesi_acili"):
            with self.subTest(alan=alan):
                deger = p[alan]
                self.assertFalse(Path(deger).is_absolute(), f"{alan} mutlak yol: {deger}")
                self.assertIsNone(CIPLAK_O_NAVITAS.search(deger), f"{alan} ciplak O: yolu: {deger}")
                self.assertTrue(deger.startswith("data/kabul/"), deger)
                self.assertTrue((KOK / deger / "manifest.json").is_file(),
                                f"{alan} -> {KOK / deger} altinda manifest yok")

    def test_65_denetci_goreli_yolu_depo_kokune_cozer(self):
        K65 = import_module("65_kabul_denetcisi")
        p = _profil()
        self.assertEqual(K65.kabul_kumesi_yolu().resolve(), (KOK / p["kabul_kumesi"]).resolve())
        self.assertEqual(K65.kabul_kumesi_acili_yolu().resolve(),
                         (KOK / p["kabul_kumesi_acili"]).resolve())
        self.assertNotEqual(K65.kabul_kumesi_yolu().resolve(), K65.kabul_kumesi_acili_yolu().resolve())

    def test_65_denetci_goreli_yol_VERILEN_koke_gore_cozulur_ve_fail_closed(self):
        K65 = import_module("65_kabul_denetcisi")
        with tempfile.TemporaryDirectory() as td:
            kok = Path(td)
            (kok / "config").mkdir()
            (kok / "data" / "k").mkdir(parents=True)
            (kok / "config" / "model_registry.json").write_text(json.dumps(
                {"default_profile": "c", "profiles": {"c": {"kabul_kumesi": "data/k",
                                                            "kabul_kumesi_acili": "data/yok"}}}),
                encoding="utf-8")
            self.assertEqual(K65.kabul_kumesi_yolu(kok).resolve(), (kok / "data" / "k").resolve())
            with self.assertRaises(RuntimeError):      # goreli ama dizin yok -> fail-closed
                K65.kabul_kumesi_acili_yolu(kok)

    def test_65_denetci_MUTLAK_yolu_hala_kabul_eder(self):
        """Geriye uyum: gecici registry'li testler mutlak yol yazar (t125/t132)."""
        K65 = import_module("65_kabul_denetcisi")
        with tempfile.TemporaryDirectory() as td:
            kok = Path(td)
            (kok / "config").mkdir()
            hedef = kok / "mutlak_kume"
            hedef.mkdir()
            (kok / "config" / "model_registry.json").write_text(json.dumps(
                {"default_profile": "c", "profiles": {"c": {"kabul_kumesi": str(hedef)}}}),
                encoding="utf-8")
            self.assertEqual(K65.kabul_kumesi_yolu(kok), hedef)

    def test_parmak_izi_DEGISMEDI_bayt_es_kopya(self):
        """Kume tasindi ama DONDURULMUS kaldi: registry parmak izi = dizinden turetilen."""
        K65 = import_module("65_kabul_denetcisi")
        p = _profil()
        pi = K65.kume_parmak_izi(KOK / p["kabul_kumesi"])
        kayit = p["kabul_kumesi_parmak_izi"]
        self.assertEqual(pi["n"], kayit["n"], "kabul kumesi dosya sayisi registry ile uyusmuyor")
        self.assertEqual(pi["ozet"], kayit["ozet"], "kabul kumesi parmak izi registry ile uyusmuyor")
        self.assertEqual(pi["n"], 547)
        acili = K65.kume_parmak_izi(KOK / p["kabul_kumesi_acili"])
        self.assertEqual(acili["n"], 524)
        self.assertEqual(acili["ozet"], "sha256:735ecc812c09a88e8a939da72ad3b8e1e7cc0a80d15a8d2e46e5dbcb6bd6fb1d"[:7]
                         + acili["ozet"][7:], "acili kume parmak izi bicimi")

    def test_manifestler_260_ornek_ve_acili_90(self):
        p = _profil()
        yatay = json.loads((KOK / p["kabul_kumesi"] / "manifest.json").read_text(encoding="utf-8"))
        acili = json.loads((KOK / p["kabul_kumesi_acili"] / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(len(yatay["ornekler"]), 260)
        self.assertEqual(len(acili["ornekler"]), 260)
        self.assertEqual(acili["parametreler"].get("bariyer_acisi"), 90.0)
        self.assertIsNone(yatay["parametreler"].get("bariyer_acisi"))
        # kareler GERCEKTEN diskte (gitignore `images/` kalibi yutmamis)
        yazilan = [o for o in yatay["ornekler"] if o.get("durum") == "YAZILDI"]
        self.assertTrue(yazilan)
        self.assertTrue(all((KOK / p["kabul_kumesi"] / o["cikti"]).is_file() for o in yazilan),
                        "kabul kumesi kareleri diskte eksik")

    def test_170_s_kumesi_kabul_goreli_yolu_bulur(self):
        m = _m177.__globals__  # noqa: F841  (yalniz sys.path hazir)
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "m170_t220", KOK / "scripts" / "olcum" / "170_engine_karar_denkligi.py")
        m170 = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m170)
        yol = m170.s_kumesi("kabul")
        self.assertTrue(yol.is_absolute())
        self.assertEqual(yol.resolve(), (KOK / _profil()["kabul_kumesi"]).resolve())
        self.assertTrue((yol / "manifest.json").is_file(), "170 --s-kume kabul manifest bulamiyor")

    def test_yks_gui_kabul_kumesi_koku_mutlak_ve_mevcut(self):
        import yks_gui
        koku = yks_gui._kabul_kumesi_koku()
        self.assertTrue(koku.is_absolute())
        self.assertEqual(koku.resolve(), (KOK / _profil()["kabul_kumesi"]).resolve())
        self.assertTrue(koku.is_dir())

    def test_gitignore_istisnasi_kabul_images_izlenir(self):
        gi = KOK / ".gitignore"
        if not gi.is_file():
            self.skipTest(".gitignore yok (paket git degil)")
        satirlar = [s.strip() for s in gi.read_text(encoding="utf-8").splitlines()]
        self.assertIn("images/", satirlar, "genel images/ kalibi kalkmis — istisnanin anlami degisti")
        self.assertIn("!data/kabul/*/images/", satirlar)
        if not (KOK / ".git").exists():
            self.skipTest("git deposu degil — check-ignore olculemez")
        kare = "data/kabul/sentetik_arena_kadraj_t66/images/val/sa_000000.jpg"
        s = subprocess.run(["git", "check-ignore", "-q", kare], cwd=str(KOK),
                           capture_output=True, text=True, timeout=30)
        self.assertEqual(s.returncode, 1, f"kabul kumesi karesi hala ignore: {kare}")
        s2 = subprocess.run(["git", "check-ignore", "-q", "dataset/x/images/y.jpg"], cwd=str(KOK),
                            capture_output=True, text=True, timeout=30)
        self.assertEqual(s2.returncode, 0, "pozitif kontrol: genel images/ kalibi artik ignore etmiyor")

    def test_paket_registry_aynasi_bayt_es(self):
        self.assertEqual(REGISTRY.read_bytes(), PAKET_REGISTRY.read_bytes(),
                         "jetson_paket/config/model_registry.json kanonikle bayt-es degil "
                         "(scripts/jetson_paket_hazirla.py kosulmali)")

    def test_registry_yol_notu_var(self):
        self.assertIn("T220", _profil().get("_kabul_kumesi_yol_notu", ""))


# ═══════════════════════════════════════════════════════════════════════════
# G4 — v36 PC referans kararlari
# ═══════════════════════════════════════════════════════════════════════════
class G4PcReferans(unittest.TestCase):

    def test_help_exit0(self):
        s = subprocess.run([PY, str(BETIK_177), "--help"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=180)
        self.assertEqual(s.returncode, 0, s.stderr[-500:])
        self.assertIn("--karsilastir", s.stdout)

    def test_referans_json_semasi_ve_model_defterle_es(self):
        self.assertTrue(REFERANS.is_file(), f"PC referansi yok: {REFERANS}")
        r = json.loads(REFERANS.read_text(encoding="utf-8"))
        p = _profil()
        self.assertEqual(r["_model"]["sha256"], p["sha256"], "referans uretim modeliyle (v36) uretilmemis")
        self.assertEqual(r["_model"]["yol"], p["path"])
        self.assertEqual(r["_model"]["defter_durum"], "eslesti")
        self.assertEqual(r["_model"]["dtype"], "torch.float32")
        self.assertIsNone(r["_sinir"], "referans --sinir ile (kismi) uretilmis")
        self.assertEqual(r["_conf"], 0.30)
        self.assertEqual(r["_infer_size"], p["imgsz"])
        self.assertEqual(sorted(r["kumeler"]), ["drone_kareleri", "sentetik_arena"])
        self.assertEqual(len(r["kumeler"]["sentetik_arena"]), 30)
        self.assertEqual(len(r["kumeler"]["drone_kareleri"]), 19)
        gerekli = {"kare", "sha256", "boyut", "mpp", "mpp_kaynagi", "uretim_yol", "uretim_red",
                   "katman_a_durum", "katman_a_yol_no", "gecilebilir_orani", "engel_orani"}
        for kume, kayitlar in r["kumeler"].items():
            for k in kayitlar:
                self.assertTrue(gerekli <= set(k), f"{kume}/{k.get('kare')}: eksik alan {gerekli - set(k)}")
                self.assertRegex(k["sha256"], r"^[0-9a-f]{64}$")
        # olcek kurali docstring'de ONCEDEN yazildi: sentetik 50/640, drone None
        for k in r["kumeler"]["sentetik_arena"]:
            self.assertAlmostEqual(k["mpp"], 50.0 / 640.0, places=9)
        for k in r["kumeler"]["drone_kareleri"]:
            self.assertIsNone(k["mpp"])
            self.assertEqual(k["uretim_yol"], None)
            self.assertEqual(k["uretim_red"], "OLCEK_YOK")

    def test_referans_kare_shalari_diskteki_karelerle_es(self):
        """Referans hangi karelere aitse Jetson da onlari kosmali: sha listesi gercek dosyalarla es."""
        r = json.loads(REFERANS.read_text(encoding="utf-8"))
        kok = None
        for aday in ana_depo_adaylari():
            if (aday / "jetson_paket" / "test_goruntuleri" / "sentetik_arena").is_dir():
                kok = aday / "jetson_paket" / "test_goruntuleri"
                break
        if kok is None:
            self.skipTest("jetson_paket/test_goruntuleri bu makinede yok (gitignore'lu)")
        import hashlib
        for kume in ("sentetik_arena", "drone_kareleri"):
            diskteki = sorted(p.name for p in (kok / kume).iterdir() if p.suffix.lower() == ".jpg")
            self.assertEqual([k["kare"] for k in r["kumeler"][kume]], diskteki, f"{kume} kare listesi farkli")
            for k in r["kumeler"][kume][:5]:
                self.assertEqual(k["sha256"], hashlib.sha256((kok / kume / k["kare"]).read_bytes()).hexdigest())

    def test_karsilastir_saf_fonksiyon_GECTI_DUSTU_OLCULEMEDI(self):
        m = _m177()
        ref = {"kumeler": {"sentetik_arena": [
            {"kare": "a.jpg", "sha256": "1", "uretim_yol": 2, "uretim_red": None, "katman_a_durum": "ACIK", "katman_a_yol_no": 2},
            {"kare": "b.jpg", "sha256": "2", "uretim_yol": None, "uretim_red": "KAPALI_DAR", "katman_a_durum": "KAPALI_DAR", "katman_a_yol_no": None}],
            "drone_kareleri": [
            {"kare": "c.jpg", "sha256": "3", "uretim_yol": None, "uretim_red": "OLCEK_YOK", "katman_a_durum": "MASKE_YOK", "katman_a_yol_no": None}]}}
        ayni = json.loads(json.dumps(ref))
        h = m.karsilastir(ref, ayni)["hukum"]
        self.assertEqual(h["durum"], "GECTI")
        self.assertEqual((h["uyusmazlik"], h["n"]), (0, 3))
        # MUTASYON 1: tek serit karari cevrildi -> DUSTU (esik 0)
        mut = json.loads(json.dumps(ref))
        mut["kumeler"]["sentetik_arena"][0]["uretim_yol"] = 3
        f = m.karsilastir(ref, mut)
        self.assertEqual(f["hukum"]["durum"], "DUSTU")
        self.assertEqual(f["hukum"]["uyusmazlik"], 1)
        self.assertEqual(f["kumeler"]["sentetik_arena"]["farklar"][0]["tur"], "URETIM_KARARI")
        # MUTASYON 2: yalniz katman-A degisti -> hukum GECTI, bilgi sayaci 1
        mut2 = json.loads(json.dumps(ref))
        mut2["kumeler"]["drone_kareleri"][0]["katman_a_durum"] = "ACIK"
        f2 = m.karsilastir(ref, mut2)
        self.assertEqual(f2["hukum"]["durum"], "GECTI")
        self.assertEqual(f2["kumeler"]["drone_kareleri"]["katman_a_farki_bilgi"], 1)
        # MUTASYON 3: kare sha farkli -> OLCULEMEDI (baska kareyle "gecti" satilamaz)
        mut3 = json.loads(json.dumps(ref))
        mut3["kumeler"]["sentetik_arena"][1]["sha256"] = "farkli"
        self.assertEqual(m.karsilastir(ref, mut3)["hukum"]["durum"], "OLCULEMEDI")
        # MUTASYON 4: kare eksik -> OLCULEMEDI
        mut4 = json.loads(json.dumps(ref))
        del mut4["kumeler"]["drone_kareleri"][0]
        self.assertEqual(m.karsilastir(ref, mut4)["hukum"]["durum"], "OLCULEMEDI")
        # bos kume -> OLCULEMEDI (bos uzerinden GECTI yok)
        self.assertEqual(m.karsilastir({"kumeler": {}}, {"kumeler": {}})["hukum"]["durum"], "OLCULEMEDI")

    def test_referans_kendisiyle_kiyaslaninca_GECTI(self):
        m = _m177()
        r = json.loads(REFERANS.read_text(encoding="utf-8"))
        h = m.karsilastir(r, r)["hukum"]
        self.assertEqual(h["durum"], "GECTI")
        self.assertEqual(h["n"], 49)

    def test_mpp_kurali_onceden_yazildi(self):
        m = _m177()
        self.assertAlmostEqual(m.mpp_kurali("sentetik_arena", 640)[0], 0.078125)
        self.assertIsNone(m.mpp_kurali("drone_kareleri", 1024)[0])


# ═══════════════════════════════════════════════════════════════════════════
# K10 — suitte ciplak O:\ yolu YOK
# ═══════════════════════════════════════════════════════════════════════════
class K10CiplakYolYasagi(unittest.TestCase):

    def test_tests_altinda_ciplak_O_navitas_yok(self):
        ihlal = []
        for p in sorted((KOK / "tests").glob("*.py")):
            for i, satir in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if CIPLAK_O_NAVITAS.search(satir):
                    ihlal.append(f"{p.name}:{i}: {satir.strip()[:90]}")
        self.assertEqual([], ihlal, "tests/ altinda ciplak O:/navitas yolu (K10, madde 16):\n" + "\n".join(ihlal))

    def test_p4_p8_yorumlayici_sys_executable(self):
        for ad in ("test_p4_runbook.py", "test_p8_sim_katmani.py"):
            with self.subTest(dosya=ad):
                s = (KOK / "tests" / ad).read_text(encoding="utf-8")
                self.assertIn("VENV = sys.executable", s)
                self.assertNotIn("navitas-local-train/venv", s)

    def test_depo_koku_testi_anchor_kullanmiyor(self):
        s = (KOK / "tests" / "test_depo_koku_turetilir.py").read_text(encoding="utf-8")
        self.assertNotIn("dir=str(surucu)", s)
        self.assertNotIn("Path(KOK.anchor)", s)
        self.assertIn("kardes_koku = KOK.parent", s)

    def test_ana_depo_adaylari_ilk_eleman_KOK_ve_worktree_kalibi(self):
        adaylar = ana_depo_adaylari()
        self.assertEqual(adaylar[0], KOK.resolve())
        self.assertEqual(len(adaylar), len(set(adaylar)))
        with tempfile.TemporaryDirectory() as td:
            ana = Path(td) / "ana"
            (ana / "codes").mkdir(parents=True)
            (ana / "CLAUDE.md").write_text("#", encoding="utf-8")
            wt = ana / ".claude" / "worktrees" / "wf_x"
            (wt / "codes").mkdir(parents=True)
            (wt / "CLAUDE.md").write_text("#", encoding="utf-8")
            self.assertEqual(ana_depo_adaylari(wt), [wt.resolve(), ana.resolve()])
            # isaretcisiz "ana" -> yalniz kok
            (ana / "CLAUDE.md").unlink()
            self.assertEqual(ana_depo_adaylari(wt), [wt.resolve()])

    def test_ortam_degiskeni_isaretci_ister(self):
        with tempfile.TemporaryDirectory() as td:
            eski = os.environ.get("NAVITAS_ANA_DEPO")
            try:
                os.environ["NAVITAS_ANA_DEPO"] = td            # isaretci yok -> yok sayilir
                self.assertNotIn(Path(td).resolve(), ana_depo_adaylari())
                (Path(td) / "codes").mkdir()
                (Path(td) / "CLAUDE.md").write_text("#", encoding="utf-8")
                self.assertIn(Path(td).resolve(), ana_depo_adaylari())
            finally:
                if eski is None:
                    os.environ.pop("NAVITAS_ANA_DEPO", None)
                else:
                    os.environ["NAVITAS_ANA_DEPO"] = eski


# ═══════════════════════════════════════════════════════════════════════════
# K1 — JETSON_KILAVUZ.md Orin NX bandi
# ═══════════════════════════════════════════════════════════════════════════
class K1KilavuzOrinNxBandi(unittest.TestCase):

    def test_baslik_ve_fps_satiri_bantli_iki_kopyada(self):
        for k in KILAVUZLAR:
            with self.subTest(dosya=k.name if k.parent == KOK else "jetson_paket/" + k.name):
                s = k.read_text(encoding="utf-8")
                ilk = s.splitlines()[0]
                self.assertTrue(ilk.startswith("# JETSON ~~ORIN NX~~"), ilk)
                self.assertIn("ORIN NANO", ilk)
                self.assertIn("KART DÜZELTMESİ (2026-09-10, T220", s)
                self.assertIn("~~Jetson Orin NX bunun belirgin altında çıkacaktır", s)
                # eski metin SILINMEDI (D-431 kalibi): cizili hali duruyor, sayilar kaynakla es
                self.assertIn("1,35 FPS", s)
                self.assertIn("1,58 FPS", s)
                self.assertIn("jetson_fps_20260906_orin_nano/ozet.json", s)
                self.assertNotRegex(s, r"^# JETSON ORIN NX", "bantsiz eski baslik geri geldi")

    def test_bant_sayilari_olcum_dosyasiyla_es(self):
        ozet = KOK / "results" / "jetson_20260906" / "jetson_fps_20260906_orin_nano" / "ozet.json"
        d = json.loads(ozet.read_text(encoding="utf-8"))
        v = {x["ad"]: x for x in d["vakalar"] if x.get("durum") == "OK"}
        self.assertAlmostEqual(1000.0 / v["pt"]["metrikler_ms"]["toplam_ms"]["p50"], 1.35, places=2)
        self.assertAlmostEqual(1000.0 / v["tensorrt_fp16"]["metrikler_ms"]["toplam_ms"]["p50"], 1.58, places=2)
        self.assertAlmostEqual(1000.0 / v["pt"]["metrikler_ms"]["toplam_ms"]["p95"], 1.06, places=2)
        self.assertAlmostEqual(1000.0 / v["tensorrt_fp16"]["metrikler_ms"]["toplam_ms"]["p95"], 1.33, places=2)
        self.assertTrue(str(d["parametreler"]["girdi"]).endswith("raw_frames"),
                        "bant 'girdi data/raw_frames' der; olcum dosyasi baska sey diyor")


# ═══════════════════════════════════════════════════════════════════════════
# cv2 — Orin kurulum betikleri GStreamer denetimi
# ═══════════════════════════════════════════════════════════════════════════
class Cv2GstreamerDenetimi(unittest.TestCase):
    NAIF = "'GStreamer' in cv2.getBuildInformation()"

    @staticmethod
    def _stub(dizin: Path, deger: str):
        (dizin / "cv2.py").write_text(
            '__version__ = "4.6.0-stub"\n'
            'def getBuildInformation():\n'
            f'    return "  Video I/O:\\n    GStreamer:                   {deger}\\n  Parallel framework: TBB\\n"\n',
            encoding="utf-8")

    def _kos(self, snippet: str, stub_dizin: Path) -> str:
        ortam = dict(os.environ, PYTHONPATH=str(stub_dizin))
        s = subprocess.run([PY, "-c", snippet], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=120, env=ortam)
        self.assertEqual(s.returncode, 0, s.stderr[-400:])
        return s.stdout.strip()

    @staticmethod
    def _root_snippet():
        s = (KOK / "scripts" / "orin_nano_root_kurulum.sh").read_text(encoding="utf-8")
        m = re.search(r'python3 -c "(import cv2[^"\n]*GStreamer[^"\n]*)"', s)
        assert m, "root betiginde cv2 GStreamer -c satiri bulunamadi"
        return m.group(1)

    @staticmethod
    def _venv_snippet():
        s = (KOK / "scripts" / "orin_nano_venv_kurulum.sh").read_text(encoding="utf-8")
        satir = [l for l in s.splitlines() if l.startswith("import") and "GStreamer" in l and "cv2" in l]
        assert len(satir) == 1, f"venv heredoc'unda cv2 GStreamer satiri tek olmali: {satir}"
        return satir[0]

    def test_naif_ifade_betiklerde_YOK(self):
        for ad in ORIN_BETIKLER:
            s = (KOK / "scripts" / ad).read_text(encoding="utf-8")
            kod = "\n".join(l for l in s.splitlines() if not l.lstrip().startswith("#"))
            self.assertNotIn("in cv2.getBuildInformation()", kod, f"{ad}: naif denetim geri geldi")
            self.assertIn("GStreamer:", kod, f"{ad}: 'GStreamer:' satir denetimi yok")

    def test_YES_True_NO_False_iki_betikte(self):
        with tempfile.TemporaryDirectory() as td:
            evet, hayir = Path(td) / "evet", Path(td) / "hayir"
            evet.mkdir()
            hayir.mkdir()
            self._stub(evet, "YES (1.20.3)")
            self._stub(hayir, "NO")
            for ad, snip in (("root", self._root_snippet()), ("venv", self._venv_snippet())):
                with self.subTest(betik=ad):
                    self.assertIn("True", self._kos(snip, evet), "YES derlemede True demiyor")
                    self.assertIn("False", self._kos(snip, hayir), "NO derlemede False demiyor")
                    self.assertNotIn("True", self._kos(snip, hayir))
            # KONTROL: eski naif ifade NO stub'inda da True verir -> stub ayirt edicidir, test bos degil
            naif = f"import cv2; print({self.NAIF})"
            self.assertEqual("True", self._kos(naif, hayir),
                             "kontrol: naif ifade NO'da False dedi — stub eski kusuru yeniden uretmiyor")

    def test_bilgi_satiri_yoksa_BILINMIYOR(self):
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "cv2.py").write_text('__version__="x"\ndef getBuildInformation():\n    return "hic"\n',
                                             encoding="utf-8")
            for snip in (self._root_snippet(), self._venv_snippet()):
                self.assertIn("BILINMIYOR", self._kos(snip, Path(td)))

    def test_scripts_ve_paket_kopyalari_bayt_es(self):
        for ad in ORIN_BETIKLER:
            with self.subTest(betik=ad):
                self.assertEqual((KOK / "scripts" / ad).read_bytes(),
                                 (KOK / "jetson_paket" / ad).read_bytes(),
                                 f"{ad}: paket kopyasi kanonikle bayt-es degil (jetson_paket_hazirla.py)")


if __name__ == "__main__":
    unittest.main()
