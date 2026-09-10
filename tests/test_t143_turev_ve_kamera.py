"""T143 KAPISI (D-284, T18 curutucusu) — iki saha kusuru:

1. Kayit defteri ad kiyasi HER `.engine`'i "ESLESMIYOR" diye reddediyordu ->
   Jetson'da TensorRT yalniz `--kayit-dogrulamasiz` ile (fail-closed
   KAPATILARAK) yukleniyordu. Simdi `turevler` sozlugu ayni soyun .engine/.onnx
   turevlerini KENDI sha256'leriyle tanitir. Fail-closed KALIR:
   yabanci .engine RED · yer tutucu RED · sha uyusmazsa RED · yetim kaynak RED ·
   .pt davranisi DEGISMEDI.
2. Canli kamera dongusu ilk dusen karede SESSIZCE bitiyordu. Simdi dusen kare
   SAYILIR, ust sinirli yeniden denenir, bitis LOGLANIR.

Hicbir test "fonksiyon var mi" diye sormaz; her biri davranisi olcer (D-98).
Mutasyon kaniti raporda: sayac satiri kaldirilinca `dusen_toplam` testi duser.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

KOK = Path(__file__).resolve().parents[1]
if str(KOK / "codes") not in sys.path:
    sys.path.insert(0, str(KOK / "codes"))
if str(KOK / "tests") not in sys.path:
    sys.path.insert(0, str(KOK / "tests"))

from depo_yollari import ana_depo_adaylari, ilk_var_olan  # noqa: E402  (T220/K10)
import rpi_inference as R  # noqa: E402
from codes import model_registry as MR  # noqa: E402
from codes.karar_sozlesmesi import (  # noqa: E402
    KAMERA_BITIS_ACILAMADI, KAMERA_BITIS_DUSEN_KARE, KAMERA_DUSEN_KARE_BEKLEME_S,
    KAMERA_DUSEN_KARE_UST_SINIRI, MODEL_TUREV_SHA_YER_TUTUCU)

DEFTER = KOK / "config" / "model_registry.json"
PAKET_DEFTER = KOK / "jetson_paket" / "config" / "model_registry.json"
# ⚠ 2026-08-26: uretim v35 -> v36 (kural disi terfi, D-293 / ON_KAYIT SS15).
# Bu UC sabit ELLE cevrilir — defterden turetilseydi test totolojik olurdu ve
# kazara cevrilmis bir profili yakalayamazdi (test_model_registry ile ayni
# gerekce). v35 turev girdileri profilden CIKARILDI (kaynak artik v36; kalsalar
# `turev_dogrula` onlari YETIM sayip RED donerdi) — v35 DOSYALARI diskte duruyor.
URETIM_PT = "models/navitas_seg_v36_best.pt"
URETIM_SHA = "1d1caca6f6da19ea35e69186a048da960ca5188be6ee6d49d6106457cac46911"
# 2026-09-07 (REVIEW_LOG D-431, K3/K4): FP16 engine 6 Eylul'de Jetson Orin Nano'da
# DERLENDI ve urun defterindeki sha256'si artik GERCEK (bb9bd868...0300); FP32
# `navitas_seg_v36_best.engine` yer tutucu girdisi profilden CIKARILDI (derlenmedi,
# gerekmiyor; `surum_dondur --dondur` her tensorrt turevinin kayitli olmasini
# ister). Asagidaki sema testleri "derlenmemis = RED" halinden basladigi icin
# `_GeciciKok` urun defterini kopyalayip engine kaydini YER TUTUCUYA GERI CEKER;
# hicbir assert silinmedi.
ENGINE_ADI = "navitas_seg_v36_best_512_fp16.engine"
PT_VEKIL_ICERIK = b"URETIM-PT-VEKIL-ICERIGI"


def _sha(yol: Path) -> str:
    return hashlib.sha256(yol.read_bytes()).hexdigest()


def _diskteki_turev(ad: str):
    """Turev dosyasi bu makinede varsa yolu (worktree'de ana depo salt okunur kaynak).

    T220 / K10: ana depo adaylari `depo_yollari.ana_depo_adaylari()` ile TURETILIR
    (worktree kalibi / NAVITAS_ANA_DEPO); ciplak `O:/navitas` yazilmaz (madde 16).
    """
    for kok in ana_depo_adaylari():
        for dizin in (kok / "models", kok / "jetson_paket" / "models"):
            if (dizin / ad).is_file():
                return dizin / ad
    return None


class _GeciciKok:
    """Gecici bir depo koku: config/model_registry.json + sahte turev dosyasi."""

    def __init__(self):
        self.dizin = Path(tempfile.mkdtemp(prefix="t143_"))
        (self.dizin / "config").mkdir()
        (self.dizin / "models").mkdir()
        self.defter = self.dizin / "config" / "model_registry.json"
        shutil.copy(DEFTER, self.defter)
        # D-431: urun defterinde engine sha'si GERCEK; sahte engine icerigiyle
        # eslesmez. Sema testleri 'derlenmemis' halden basladigi icin gecici
        # kayit yer tutucuya cekilir (baslangic durumu, mutasyon degil).
        self.turev_sha_yaz(MODEL_TUREV_SHA_YER_TUTUCU)
        self.engine = self.dizin / "models" / ENGINE_ADI
        self.engine.write_bytes(b"TRT-ENGINE-SAHTE-ICERIK-" * 64)
        # T143 kalinti (1): --kaynak-pt ZORUNLU. Uretim .pt worktree'de yok;
        # vekil dosya + yalniz BU dosya/BU icerik icin sha vekili (asagida).
        self.pt = self.dizin / "models" / "navitas_seg_v36_best.pt"
        self.pt.write_bytes(PT_VEKIL_ICERIK)

    def sha_vekili(self):
        """`MR._sha256` yamasi: vekil .pt (ayni icerikle) -> URETIM_SHA; digerleri gercek."""
        gercek = MR._sha256

        def _sha256(yol):
            yol = Path(yol)
            if yol == self.pt and yol.read_bytes() == PT_VEKIL_ICERIK:
                return URETIM_SHA
            return gercek(yol)
        return mock.patch.object(MR, "_sha256", side_effect=_sha256)

    def veri(self) -> dict:
        return json.loads(self.defter.read_text(encoding="utf-8"))

    def yaz(self, veri: dict) -> None:
        self.defter.write_text(json.dumps(veri, indent=1, ensure_ascii=False), encoding="utf-8")

    def turev_sha_yaz(self, ozet: str, ad: str = ENGINE_ADI) -> None:
        veri = self.veri()
        veri["profiles"]["competition"]["turevler"][ad]["sha256"] = ozet
        self.yaz(veri)

    def kapat(self):
        shutil.rmtree(self.dizin, ignore_errors=True)


class UretimDefteriTests(unittest.TestCase):
    """Defterin kendisi: competition DEGISMEDI, turevler yer tutucuyla var."""

    def setUp(self):
        self.profil = json.loads(DEFTER.read_text(encoding="utf-8"))["profiles"]["competition"]

    def test_competition_path_ve_pt_sha_DEGISMEDI(self):
        self.assertEqual(URETIM_PT, self.profil["path"])
        self.assertEqual(URETIM_SHA, self.profil["sha256"])

    def _engine_kaydi_dogrula(self, ad: str, kayit: dict) -> None:
        """K3 (D-431): .engine kaydi YA yer tutucu (derlenmedi = RED, mesru) YA DA
        gercek bir ozet olmali. Gercek ozet: 64 hex ZORUNLU (dosya diskte yoksa
        test ATLANMAZ; kaynak_sha256 == .pt ozeti kosulu cagiran dongude sinanir),
        dosya bu makinede varsa ozet dosyanin sha256'si ile BIREBIR."""
        ozet = kayit["sha256"]
        if ozet == MODEL_TUREV_SHA_YER_TUTUCU:
            return
        self.assertTrue(MR.sha256_dogrulanmis_mi(ozet),
                        f"{ad}: ne yer tutucu ne 64 hex ozet: {ozet!r}")
        dosya = _diskteki_turev(ad)
        if dosya is None:
            return          # atlanmadi: bicim + (dongude) soy kosulu dogrulandi
        self.assertEqual(_sha(dosya), ozet,
                         f"{ad}: defterdeki ozet diskteki dosyayla BIREBIR degil ({dosya})")

    def test_turevler_engine_YER_TUTUCU_onnx_DOGRULANMIS_hepsi_kaynaga_BAGLI(self):
        """ONNX'ler diskte var; ozetleri `--turev-kaydet` ile GERCEKTEN yazildi
        (2026-08-26, --kaynak-pt ile .pt ozeti kiyaslanarak). FP16 .engine 6 Eylul
        2026'da Jetson Orin Nano'da derlendi ve ayni CLI ile yazildi (D-431); kayit
        yer tutucu YA DA diskteki dosyanin ozetiyle birebir olmali (K3). FP32
        `navitas_seg_v36_best.engine` girdisi CIKARILDI (K4) — kume esitligi
        geri gelmesini de yakalar."""
        turevler = self.profil["turevler"]
        self.assertEqual({ENGINE_ADI,
                          "navitas_seg_v36_best.onnx",
                          "navitas_seg_v36_best_512_fp16.onnx"}, set(turevler))
        for ad, kayit in turevler.items():
            with self.subTest(ad=ad):
                if ad.endswith(".engine"):
                    self._engine_kaydi_dogrula(ad, kayit)
                else:
                    self.assertTrue(MR.sha256_dogrulanmis_mi(kayit["sha256"]), ad)
                self.assertEqual(URETIM_PT, kayit["kaynak"])
                self.assertEqual(URETIM_SHA, kayit["kaynak_sha256"])
                self.assertEqual(self.profil["imgsz"], kayit["imgsz"])

    def test_diskteki_onnx_turevi_GERCEKTEN_GECER(self):
        """Gercek dosya, gercek ozet — sadece defter metni degil."""
        onnx = ilk_var_olan("models", "navitas_seg_v36_best.onnx")   # worktree: ana depo salt okunur kaynak
        if onnx is None:
            onnx = KOK / "models" / "navitas_seg_v36_best.onnx"
        if not onnx.is_file():
            self.skipTest(f"ONNX turevi bu makinede yok: {onnx}")
        u, d = R.model_kayit_dogrula(onnx, kok=KOK, calisan_imgsz=512)
        self.assertTrue(u, d)
        self.assertEqual("turev_eslesti", d["durum"])

    def test_diskteki_engine_turevi_GERCEKTEN_GECER(self):
        """D-431: Jetson'da derlenen FP16 engine bu makinede varsa defterle
        `turev_eslesti` vermeli (kayit CLI ciktisi: results/jetson_20260906/
        jetson_log_20260906/turev_kaydet.log). Dosya yoksa atlanir ve SOYLER;
        defter kaydinin bicimi yukaridaki testte atlanmadan sinanir."""
        engine = _diskteki_turev(ENGINE_ADI)
        if engine is None:
            self.skipTest(f"engine turevi bu makinede yok: {ENGINE_ADI} (Jetson'da derlenir)")
        u, d = R.model_kayit_dogrula(engine, kok=KOK, calisan_imgsz=512)
        self.assertTrue(u, d)
        self.assertEqual("turev_eslesti", d["durum"])

    def test_paket_aynasi_BAYT_ES(self):
        self.assertEqual(_sha(DEFTER), _sha(PAKET_DEFTER))

    def test_kilavuza_kayit_dogrulamasiz_YORDAM_olarak_yazilmadi(self):
        """Bayrak kilavuzda yalniz UYARI olarak gecebilir; komut satiri
        orneginde ('--camera ... --kayit-dogrulamasiz') GECMEZ."""
        for yol in (KOK / "JETSON_KILAVUZ.md", KOK / "jetson_paket" / "JETSON_KILAVUZ.md"):
            metin = yol.read_text(encoding="utf-8")
            for satir in metin.splitlines():
                if "--kayit-dogrulamasiz" in satir and "rpi_inference" in satir:
                    self.fail(f"{yol.name}: bayrak komut satirinda: {satir!r}")


class TurevDogrulamaTests(unittest.TestCase):
    """`rpi_inference.model_kayit_dogrula` VE `model_registry.turev_dogrula`
    AYNI girdide AYNI hukmu vermeli (paket standalone kopya)."""

    def setUp(self):
        self.k = _GeciciKok()
        self.addCleanup(self.k.kapat)

    def _iki_hukum(self, dosya, imgsz=512):
        u1, d1 = R.model_kayit_dogrula(dosya, kok=self.k.dizin, calisan_imgsz=imgsz)
        profil = self.k.veri()["profiles"]["competition"]
        u2, d2 = MR.turev_dogrula(profil, dosya, calisan_imgsz=imgsz)
        return (u1, d1["durum"]), (u2, d2["durum"])

    def test_YER_TUTUCU_turev_RED(self):
        """Derlenmemis = dogrulanmamis = RED. Urun defteri 6 Eylul 2026'ya kadar bu
        haldeydi; artik gecici kok bu hali yeniden kurar (D-431, _GeciciKok)."""
        (u1, s1), (u2, s2) = self._iki_hukum(self.k.engine)
        self.assertFalse(u1); self.assertFalse(u2)
        self.assertIn("YER TUTUCU", s1); self.assertEqual(s1, s2)

    def test_DOGRULANMIS_sha_ile_engine_GECER(self):
        self.k.turev_sha_yaz(_sha(self.k.engine))
        (u1, s1), (u2, s2) = self._iki_hukum(self.k.engine)
        self.assertTrue(u1, s1); self.assertTrue(u2, s2)
        self.assertEqual("turev_eslesti", s1); self.assertEqual(s1, s2)

    def test_sha_UYUSMAZSA_RED(self):
        self.k.turev_sha_yaz(_sha(self.k.engine))
        self.k.engine.write_bytes(b"DEGISTI")           # dosya defterden sonra degisti
        (u1, s1), (u2, s2) = self._iki_hukum(self.k.engine)
        self.assertFalse(u1); self.assertFalse(u2)
        self.assertEqual("TUREV SHA ESLESMIYOR", s1); self.assertEqual(s1, s2)

    def test_YABANCI_engine_RED(self):
        yabanci = self.k.dizin / "models" / "baska_model.engine"
        yabanci.write_bytes(b"x" * 100)
        self.k.turev_sha_yaz(_sha(self.k.engine))       # kayitli olan dogrulanmis olsa bile
        (u1, s1), (u2, s2) = self._iki_hukum(yabanci)
        self.assertFalse(u1); self.assertFalse(u2)
        self.assertEqual("ESLESMIYOR", s1); self.assertEqual(s1, s2)

    def test_YETIM_kaynak_RED(self):
        """Turev dogrulanmis olsa bile kaynak .pt ozeti profile uymuyorsa RED."""
        self.k.turev_sha_yaz(_sha(self.k.engine))
        veri = self.k.veri()
        veri["profiles"]["competition"]["turevler"][ENGINE_ADI]["kaynak_sha256"] = "0" * 64
        self.k.yaz(veri)
        (u1, s1), (u2, s2) = self._iki_hukum(self.k.engine)
        self.assertFalse(u1); self.assertFalse(u2)
        self.assertEqual("TUREV KAYNAGI ESLESMIYOR", s1); self.assertEqual(s1, s2)

    def test_turev_IMGSZ_uyusmazsa_RED(self):
        self.k.turev_sha_yaz(_sha(self.k.engine))
        (u1, s1), (u2, s2) = self._iki_hukum(self.k.engine, imgsz=640)
        self.assertFalse(u1); self.assertFalse(u2)
        self.assertEqual("IMGSZ ESLESMIYOR", s1); self.assertEqual(s1, s2)

    def test_PT_davranisi_DEGISMEDI(self):
        """.pt: ad + imgsz kiyasi, sha HESAPLANMAZ (dosya yok bile olsa eslesir)."""
        u, d = R.model_kayit_dogrula(self.k.dizin / URETIM_PT, kok=self.k.dizin, calisan_imgsz=512)
        self.assertTrue(u); self.assertEqual("eslesti", d["durum"])
        u, d = R.model_kayit_dogrula(self.k.dizin / URETIM_PT, kok=self.k.dizin, calisan_imgsz=640)
        self.assertFalse(u); self.assertEqual("IMGSZ ESLESMIYOR", d["durum"])
        u, d = R.model_kayit_dogrula("yabanci.pt", kok=self.k.dizin, calisan_imgsz=512)
        self.assertFalse(u); self.assertEqual("ESLESMIYOR", d["durum"])

    def test_yer_tutucu_sha_biciminde_DEGIL(self):
        self.assertFalse(R._sha256_dogrulanmis_mi(MODEL_TUREV_SHA_YER_TUTUCU))
        self.assertFalse(R._sha256_dogrulanmis_mi(""))
        self.assertFalse(R._sha256_dogrulanmis_mi("zz" * 32))
        self.assertTrue(R._sha256_dogrulanmis_mi("ab" * 32))

    def test_load_model_YER_TUTUCU_turevle_FAIL_CLOSED(self):
        with mock.patch.object(R, "YOLO") as yolo:
            with self.assertRaises(RuntimeError) as ctx:
                R.load_model(self.k.engine, kok=self.k.dizin, kayit_zorunlu=True)
            self.assertIn("YER TUTUCU", str(ctx.exception))
            yolo.assert_not_called()

    def test_load_model_DOGRULANMIS_turevle_YUKLER(self):
        self.k.turev_sha_yaz(_sha(self.k.engine))
        with mock.patch.object(R, "YOLO") as yolo:
            _m, yol, detay = R.load_model(self.k.engine, kok=self.k.dizin,
                                          kayit_zorunlu=True, ayrinti=True)
        self.assertEqual("turev_eslesti", detay["durum"])
        yolo.assert_called_once_with(str(self.k.engine), task="segment")

    def test_resolve_model_turev_ile(self):
        with self.assertRaises(MR.ModelRegistryError):
            MR.resolve_model(registry_path=self.k.defter, turev=self.k.engine)
        self.k.turev_sha_yaz(_sha(self.k.engine))
        yol, spec = MR.resolve_model(registry_path=self.k.defter, turev=self.k.engine)
        self.assertEqual(self.k.engine, yol)
        self.assertEqual(URETIM_PT, spec["path"])            # .pt yolu degismedi

    def test_resolve_model_turev_CALISAN_IMGSZ_iletir(self):
        """T143 kalinti (3): `calisan_imgsz` turev kaydinin imgsz'i ile kiyaslanir."""
        self.k.turev_sha_yaz(_sha(self.k.engine))
        with self.assertRaises(MR.ModelRegistryError) as ctx:
            MR.resolve_model(registry_path=self.k.defter, turev=self.k.engine, calisan_imgsz=640)
        self.assertIn("IMGSZ ESLESMIYOR", str(ctx.exception))
        yol, spec = MR.resolve_model(registry_path=self.k.defter, turev=self.k.engine,
                                     calisan_imgsz=512)
        self.assertEqual(self.k.engine, yol)
        self.assertEqual("turev_eslesti", spec["turev_detay"]["durum"])


class TurevKaydetCliTests(unittest.TestCase):
    def setUp(self):
        self.k = _GeciciKok()
        self.addCleanup(self.k.kapat)
        yama = self.k.sha_vekili()
        yama.start()
        self.addCleanup(yama.stop)

    def test_turev_kaydet_yer_tutucuyu_GERCEK_ozetle_degistirir_ve_aynayi_yazar(self):
        ayna = self.k.dizin / "ayna.json"
        sonuc = MR.turev_kaydet(self.k.engine, registry_path=self.k.defter, ayna_yollari=(ayna,),
                                kaynak_pt=self.k.pt)
        self.assertEqual(MODEL_TUREV_SHA_YER_TUTUCU, sonuc["eski_sha256"])
        self.assertEqual(_sha(self.k.engine), sonuc["yeni_sha256"])
        veri = self.k.veri()
        kayit = veri["profiles"]["competition"][ "turevler"][ENGINE_ADI]
        self.assertEqual(_sha(self.k.engine), kayit["sha256"])
        self.assertEqual(URETIM_SHA, veri["profiles"]["competition"]["sha256"])   # .pt sha DEGISMEDI
        self.assertEqual(URETIM_PT, veri["profiles"]["competition"]["path"])
        self.assertEqual(self.k.defter.read_bytes(), ayna.read_bytes())
        u, d = R.model_kayit_dogrula(self.k.engine, kok=self.k.dizin, calisan_imgsz=512)
        self.assertTrue(u, d)

    def test_turev_kaydet_YABANCI_dosyayi_soya_SOKMAZ(self):
        yabanci = self.k.dizin / "models" / "baska.engine"
        yabanci.write_bytes(b"y" * 10)
        with self.assertRaises(MR.ModelRegistryError):
            MR.turev_kaydet(yabanci, registry_path=self.k.defter, kaynak_pt=self.k.pt)
        with self.assertRaises(MR.ModelRegistryError):
            MR.turev_kaydet(self.k.dizin / "models" / "x.pt", registry_path=self.k.defter,
                            kaynak_pt=self.k.pt)

    def test_turev_kaydet_KAYNAK_PT_YOKSA_RED(self):
        """T143 kalinti (1): soy kaniti olmadan kayit yazilmaz (API + CLI)."""
        with self.assertRaises(MR.ModelRegistryError) as ctx:
            MR.turev_kaydet(self.k.engine, registry_path=self.k.defter)
        self.assertIn("--kaynak-pt ZORUNLU", str(ctx.exception))
        self.assertEqual(MODEL_TUREV_SHA_YER_TUTUCU,
                         self.k.veri()["profiles"]["competition"]["turevler"][ENGINE_ADI]["sha256"])
        with mock.patch("builtins.print") as p:
            kod = MR._cli(["--turev-kaydet", str(self.k.engine),
                           "--defter", str(self.k.defter), "--ayna-yok"])
        self.assertEqual(1, kod)
        basilan = " ".join(str(c.args[0]) for c in p.call_args_list if c.args)
        self.assertIn("RED", basilan); self.assertIn("--kaynak-pt", basilan)
        self.assertEqual(MODEL_TUREV_SHA_YER_TUTUCU,
                         self.k.veri()["profiles"]["competition"]["turevler"][ENGINE_ADI]["sha256"])

    def test_turev_kaydet_YANLIS_kaynak_pt_RED(self):
        sahte_pt = self.k.dizin / "models" / "navitas_seg_v36_best.pt"
        sahte_pt.write_bytes(b"bu uretim agirligi degil")
        with self.assertRaises(MR.ModelRegistryError):
            MR.turev_kaydet(self.k.engine, registry_path=self.k.defter, kaynak_pt=sahte_pt)
        self.assertEqual(MODEL_TUREV_SHA_YER_TUTUCU,
                         self.k.veri()["profiles"]["competition"]["turevler"][ENGINE_ADI]["sha256"])

    def test_cli_cikis_kodu(self):
        self.assertEqual(1, MR._cli(["--turev-kaydet", str(self.k.dizin / "yok.engine"),
                                     "--kaynak-pt", str(self.k.pt), "--defter", str(self.k.defter)]))
        self.assertEqual(0, MR._cli(["--turev-kaydet", str(self.k.engine), "--kaynak-pt", str(self.k.pt),
                                     "--defter", str(self.k.defter), "--ayna-yok"]))
        self.assertEqual(2, MR._cli([]))


class _SahteKamera:
    """`cap.read()` senaryosu: 'K' kare, '-' dusen kare; bitince hep dusen.

    T143 kalinti (2): bitince SONSUZA dek (False, None) donuyordu -> ust sinir
    mutasyonunda (M6) test ASILIYORDU. Cagri tavani: senaryo + 10 x ust_sinir
    asilinca RuntimeError — mutasyon artik DUSER, asmaz.
    """

    def __init__(self, senaryo: str, ust_sinir: int = KAMERA_DUSEN_KARE_UST_SINIRI):
        self.senaryo = list(senaryo)
        self.cagri = 0
        self.cagri_tavani = len(senaryo) + 10 * int(ust_sinir)

    def read(self):
        self.cagri += 1
        if self.cagri > self.cagri_tavani:
            raise RuntimeError(f"_SahteKamera: cagri tavani asildi ({self.cagri_tavani}) — "
                               "kamera dongusu ust sinirda BITMIYOR")
        if self.senaryo:
            s = self.senaryo.pop(0)
            if s == "K":
                return True, f"kare{self.cagri}"
        return False, None


class KameraDusenKareTests(unittest.TestCase):
    def _kos(self, senaryo, ust_sinir=5):
        ozet = {"bitis": None, "okunan": 0, "dusen_toplam": 0, "dusen_ardisik_maks": 0}
        loglar, beklemeler = [], []
        kareler = list(R.kamera_kareleri(_SahteKamera(senaryo, ust_sinir), ozet, ust_sinir=ust_sinir,
                                         bekleme_s=0.01, bekle=beklemeler.append,
                                         log=loglar.append))
        return kareler, ozet, loglar, beklemeler

    def test_sabitler_gerekceli_ve_makul(self):
        self.assertIsInstance(KAMERA_DUSEN_KARE_UST_SINIRI, int)
        self.assertGreater(KAMERA_DUSEN_KARE_UST_SINIRI, 1)     # tek dusen kare bitirmez
        self.assertGreaterEqual(KAMERA_DUSEN_KARE_BEKLEME_S, 0.0)
        self.assertLess(KAMERA_DUSEN_KARE_UST_SINIRI * KAMERA_DUSEN_KARE_BEKLEME_S, 5.0)

    def test_tek_dusen_kare_BITIRMEZ_sayilir_ve_loglanir(self):
        """Eski kusur: ilk `ret=False` -> break. Simdi sonraki kare okunur."""
        kareler, ozet, loglar, beklemeler = self._kos("K-KK")
        self.assertEqual(["kare1", "kare3", "kare4"], kareler)
        self.assertEqual(3, ozet["okunan"])
        self.assertEqual(KAMERA_BITIS_DUSEN_KARE, ozet["bitis"])  # senaryo bitince hat koptu
        self.assertEqual(1 + 5, ozet["dusen_toplam"])            # 1 gecici + 5 sonda
        self.assertEqual(5, ozet["dusen_ardisik_maks"])
        self.assertTrue(any("kare dusdu (1/5" in s for s in loglar), loglar)
        self.assertTrue(any("kontrollu bitiyor" in s for s in loglar), loglar)
        self.assertEqual([0.01] * 5, beklemeler)                # son (sinir) okumada beklenmez

    def test_N_dusen_kare_SAYAC(self):
        for n in (1, 2, 4):
            with self.subTest(n=n):
                _, ozet, loglar, _ = self._kos("K" + "-" * n + "K", ust_sinir=5)
                self.assertEqual(n + 5, ozet["dusen_toplam"])
                self.assertEqual(5, ozet["dusen_ardisik_maks"])
                self.assertEqual(2, ozet["okunan"])
                self.assertEqual(n + 5, sum("kare dusdu" in s or "kontrollu" in s for s in loglar))

    def test_basarili_okuma_ardisik_sayaci_SIFIRLAR(self):
        """4 dusen + kare + 4 dusen: ardisik maks 4 (<5), dongu bitmez."""
        kareler, ozet, _, _ = self._kos("----K----K", ust_sinir=5)
        self.assertEqual(["kare5", "kare10"], kareler)
        self.assertEqual(5, ozet["dusen_ardisik_maks"])         # sondaki koptu blogu
        self.assertEqual(8 + 5, ozet["dusen_toplam"])

    def test_ust_sinir_asilinca_KONTROLLU_bitis(self):
        kam = _SahteKamera("", ust_sinir=3)
        ozet = {}
        loglar = []
        list(R.kamera_kareleri(kam, ozet, ust_sinir=3, bekleme_s=0, bekle=lambda s: None,
                               log=loglar.append))
        self.assertEqual(3, kam.cagri)                           # sonsuz dongu YOK
        self.assertEqual(KAMERA_BITIS_DUSEN_KARE, ozet["bitis"])
        self.assertEqual(3, ozet["dusen_toplam"])
        self.assertIn("ust sinir 3", loglar[-1])
        rapor = R.kamera_bitis_raporu(ozet)
        self.assertIn("neden=DUSEN_KARE_UST_SINIRI", rapor)
        self.assertIn("dusen_toplam=3", rapor)

    def test_varsayilan_sinir_sozlesmeden_gelir(self):
        kam = _SahteKamera("")
        ozet = {}
        list(R.kamera_kareleri(kam, ozet, bekle=lambda s: None, log=lambda s: None))
        self.assertEqual(KAMERA_DUSEN_KARE_UST_SINIRI, kam.cagri)

    def test_run_camera_ACILAMAYAN_kaynakta_ozet_doner(self):
        sahte = mock.MagicMock()
        sahte.isOpened.return_value = False
        with mock.patch.object(R.cv2, "VideoCapture", return_value=sahte):
            ozet = R.run_camera(model=None, conf=0.3, kaynak=9)
        self.assertEqual(KAMERA_BITIS_ACILAMADI, ozet["bitis"])

    def test_run_camera_dusen_kareleri_RAPORLAR(self):
        """Uctan uca: mock kamera 2 kare + kopus; predict/imshow sahte."""
        import numpy as np
        kam = _SahteKamera("KK")
        kam.read = (lambda orj=kam.read: (lambda: (lambda r: (r[0], np.zeros((32, 32, 3), np.uint8)
                                                            if r[0] else None))(orj())))()
        kam.isOpened = lambda: True
        kam.release = lambda: None
        sonuc = mock.MagicMock()
        sonuc.masks = None
        model = mock.MagicMock()
        model.predict.return_value = [sonuc]
        with mock.patch.object(R.cv2, "VideoCapture", return_value=kam), \
                mock.patch.object(R.cv2, "imshow"), \
                mock.patch.object(R.cv2, "waitKey", return_value=0), \
                mock.patch.object(R.cv2, "destroyAllWindows"), \
                mock.patch.object(R, "KAMERA_DUSEN_KARE_UST_SINIRI", 2), \
                mock.patch.object(R, "KAMERA_DUSEN_KARE_BEKLEME_S", 0.0), \
                mock.patch("builtins.print") as p:
            ozet = R.run_camera(model, conf=0.3, kaynak=0)
        self.assertEqual(2, ozet["okunan"])
        self.assertEqual(2, ozet["dusen_toplam"])
        self.assertEqual(KAMERA_BITIS_DUSEN_KARE, ozet["bitis"])
        basilan = " ".join(str(c.args[0]) for c in p.call_args_list if c.args)
        self.assertIn("KAMERA BITIS: neden=DUSEN_KARE_UST_SINIRI", basilan)


if __name__ == "__main__":
    unittest.main()
