"""T156 — GENEL KAPI URETIM YOLUNU DA ZORLUYOR MU?

NEDEN (REVIEW_LOG D-295 / D-296 · CONTRACTS SS11.2-EK · ON_KAYIT SS18-B).
Anayasa madde 14'un genel kapisi (`codes/test_rota_sentetik.py`) 2026-08-26'ya
kadar YALNIZ `costmap_path_finder.rota_bul`u zorluyordu. URETIM yolu ise
`rpi_inference.analyze_path`tir (D-295): Jetson/RPi cikarim hatti, `comms`
yayini ve YKS'de PUANLANAN etiket oradan gelir.

Delik OLCULDU, varsayilmadi: T155'te (D-296) uretim yolu ayni 15 yer gercekli
sahnenin 9'unda YANLIS serit numarasi yayinlarken genel kapi 15/15 YESIL
yaniyordu. Kapi, uretimin yayinladigi karari hic gormemisti.

BU DOSYA UC SEYI TUTAR:
  1. DEGER — kapinin URETIM kolu (`test_rota_sentetik.uretim_yolu_kolu`) ayni
     15 sahnede hem rota URETIYOR hem de yer gercegine uyan serit yayinliyor
     (ON_KAYIT SS18-B esigi >= 14/15; olculen taban 15/15).
  2. SOZLESME — kapinin CIKIS KODU (`kapi_karari`) iki kola da bagli: KOL 1
     tam puan sarti KORUNUR, KOL 2 esik altina dusunce kapi DUSER.
  3. MUTASYON MUHAFIZI — yayin hatti eski `darbogaz_serit`e cevrilirse KOL 2
     esigin ALTINA duser. Bu olmadan kapi vakum olurdu (D-15).

Sahneler kapinin KENDI ureticisinden gelir (`sahne_uret`), buraya kopyalanmaz;
kopya sahne, sahne degistiginde bu testi sessizce ALAKASIZ kilardi.

⚠ SINIR (raporda da aynen durur): sahneler SENTETIKtir ve maske KUSURSUZdur.
  Bu bir ALGI olcumu degil MANTIK olcumudur; gercek karelerde oran BU DEGILDIR.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
KAPI_YOLU = KOK / "codes" / "test_rota_sentetik.py"
for _alt in ("codes", "simulation/scripts"):
    _p = str(KOK / _alt)
    if _p not in sys.path:
        sys.path.insert(0, _p)

import arena  # noqa: E402


def _kapi_modulu():
    """Kapi betigini **acik dosya yolundan** yukle — `import` ile DEGIL.

    🔴 OLCULDU (bu gorevde): `discover` tam suiti kosarken bazi test modulleri
    `scripts/olcum/ayarlar.py` zincirinden `sys.path`'e ANA deponun (`O:\\navitas`)
    `codes` dizinini SIFIRINCI sirada ekliyor. Duz `import test_rota_sentetik`
    o zaman worktree'nin degil ANA deponun dosyasini yukluyordu
    (`MODUL: O:\\navitas\\codes\\test_rota_sentetik.py`) — yani kapi testi,
    degistirilen kodu DEGIL baska bir kopyayi olcuyordu. Sessiz yanlis olcum.
    Bu yuzden modul buradan, kesin yoldan yuklenir.
    """
    ad = "t156_kapi_modulu"
    spec = importlib.util.spec_from_file_location(ad, KAPI_YOLU)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


TRS = _kapi_modulu()


def _satirlar():
    """Kapinin URETIM kolu — bir kez kosulur, uc test sinifi paylasir."""
    global _ONBELLEK
    try:
        return _ONBELLEK
    except NameError:
        _ONBELLEK = TRS.uretim_yolu_kolu()
        return _ONBELLEK


class T156DegerKapisiTests(unittest.TestCase):
    """1. Kapinin URETIM kolu esigi geciyor mu?"""

    def test_sahne_sayisi_arenanin_kendi_sayisidir(self):
        """Kol 15 sahnenin TAMAMINI kosuyor (ciplak sayi degil, uretecten)."""
        beklenen = arena.HARITA_N * len(arena.SCENARIOS)
        self.assertEqual(beklenen, len(_satirlar()))
        self.assertEqual(15, beklenen, "arena kumesi degismis — esik gozden "
                                       "gecirilmeli (ON_KAYIT SS18-B)")

    def test_uretim_yolu_her_sahnede_ROTA_URETIYOR(self):
        """KAPI (a): karar uretilmeli — ret yok, yol var, >= 2 waypoint."""
        rota_dogru, _serit, toplam = TRS.uretim_kolu_sayimi(_satirlar())
        eksik = [f"{s['harita']}/{s['senaryo']}: ret={s['ret']} "
                 f"yol={s['yayinlanan_road']} wp={s['wp']}"
                 for s in _satirlar() if not s["rota_var"]]
        self.assertGreaterEqual(
            rota_dogru, TRS.URETIM_KAPI_ESIGI,
            f"ON_KAYIT SS18-B: rota uretimi {rota_dogru}/{toplam} "
            f"(>= {TRS.URETIM_KAPI_ESIGI} gerekli). Eksikler: {eksik}")

    def test_yayinlanan_serit_yer_gercegiyle_UYUSUYOR(self):
        """KAPI (b): yayinlanan `road` yer gercegi guzergahi olmali.

        Bagimsiz kahin: `arena.harita()` hangi guzergahi ACIK biraktigini kendi
        tohumundan bilir (`H["open"]`) ve bu bilgi karar yoluna HIC verilmez.
        """
        _rota, serit_dogru, toplam = TRS.uretim_kolu_sayimi(_satirlar())
        yanlislar = [f"{s['harita']}/{s['senaryo']}: yayin="
                     f"{s['yayinlanan_road']} gercek={s['yer_gercegi']}"
                     for s in _satirlar() if not s["serit_ok"]]
        self.assertGreaterEqual(
            serit_dogru, TRS.URETIM_KAPI_ESIGI,
            f"ON_KAYIT SS18-B: yayinlanan serit {serit_dogru}/{toplam} "
            f"(>= {TRS.URETIM_KAPI_ESIGI} gerekli). Yanlislar: {yanlislar}")


class T156CikisKoduSozlesmesiTests(unittest.TestCase):
    """2. Kapinin cikis kodu IKI kola da bagli (madde 14 sozlesmesi)."""

    def test_iki_kol_da_gecince_kapi_GECER(self):
        self.assertEqual(0, TRS.kapi_karari(15, 15, 15, 15, 15))

    def test_kol1_tam_puan_sarti_KORUNDU(self):
        """`rota_bul` kolunda TEK sahne dusse bile kapi duser (degismedi)."""
        self.assertEqual(1, TRS.kapi_karari(14, 15, 15, 15, 15))

    def test_uretim_kolu_serit_esigin_ALTINA_dusunce_kapi_DUSER(self):
        self.assertEqual(
            1, TRS.kapi_karari(15, 15, 15, TRS.URETIM_KAPI_ESIGI - 1, 15))

    def test_uretim_kolu_rota_esigin_ALTINA_dusunce_kapi_DUSER(self):
        self.assertEqual(
            1, TRS.kapi_karari(15, 15, TRS.URETIM_KAPI_ESIGI - 1, 15, 15))

    def test_esik_SINIRI_tam_esikte_gecer(self):
        """Esik >= olarak tanimli; 14/15 GECER, 13/15 DUSER (ON_KAYIT SS18-B)."""
        e = TRS.URETIM_KAPI_ESIGI
        self.assertEqual(0, TRS.kapi_karari(15, 15, e, e, 15))
        self.assertEqual(1, TRS.kapi_karari(15, 15, e, e - 1, 15))

    def test_bos_kume_kapiyi_GECIREMEZ(self):
        """Sahne uretimi cokerse kapi sessizce yesil yanmamali (fail-closed)."""
        self.assertEqual(1, TRS.kapi_karari(0, 0, 0, 0, 0))

    def test_olculen_kapi_BU_depodan_geliyor(self):
        """Vakum panzehiri: olculen dosya gercekten bu deponun kapisi mi?"""
        self.assertEqual(str(KAPI_YOLU), TRS.__file__)
        self.assertTrue(KAPI_YOLU.is_file(), f"kapi betigi yok: {KAPI_YOLU}")


class T156KapiBetigiUctanUcaTests(unittest.TestCase):
    """2b. Kapi betigi GERCEKTEN kosulur — cikti sozlesmesi + cikis kodu.

    Fonksiyonlari tek tek cagirmak, `main()`den cagri silinirse yakalamaz.
    Bu yuzden kapi ALT SUREC olarak kosulur: hem `main()` baglantisi, hem
    cikis kodu, hem de dis okuyucularin sozlesmesi (KOL 1 metni) kilitlenir.
    Alt surec ayrica `sys.path` kirlenmesinden BAGISIKTIR (bkz. `_kapi_modulu`).
    """

    @classmethod
    def setUpClass(cls):
        cls.p = subprocess.run(
            [sys.executable, str(KAPI_YOLU)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            cwd=str(KOK), timeout=600)
        cls.cikti = (cls.p.stdout or "") + (cls.p.stderr or "")

    def test_kapi_GECIYOR_ve_cikis_kodu_sifir(self):
        self.assertEqual(0, self.p.returncode,
                         f"genel kapi dustu:\n{self.cikti[-3000:]}")

    def test_KOL1_cikti_sozlesmesi_BOZULMADI(self):
        """Dis okuyucular bu iki satiri okuyor olabilir — aynen durmali."""
        self.assertIn("SONUC: 15/15 dogru", self.cikti)
        self.assertIn("[OK] TUM DETERMINISTIK SAHNELER GECTI", self.cikti)

    def test_KOL2_uretim_yolu_ciktida_var_ve_GECTI(self):
        self.assertIn("KOL 2 — URETIM YOLU (rpi_inference.analyze_path)",
                      self.cikti)
        self.assertIn("[OK] URETIM YOLU KOLU GECTI", self.cikti)
        self.assertIn(f"esik >= {TRS.URETIM_KAPI_ESIGI}/15", self.cikti)


class T156MutasyonMuhafiziTests(unittest.TestCase):
    """3. Kol vakum degil — yayin alani bozulunca esigin ALTINA duser."""

    def test_darbogaz_serit_yayinlansaydi_KOL_DUSERDI(self):
        """MUTASYON: `open_path = olcum["serit_karari"]` -> `darbogaz_serit`.

        O mutasyonla yayinlanan sayi kac sahnede dogru kalirdi? Olculdu: 6/15
        (T155 oncesi master ile ayni sayi, D-296). 6 < 14 oldugu icin KOL 2
        DUSER — yani kapi bu mutasyonu GERCEKTEN ayirt eder.
        """
        satirlar = _satirlar()
        mutant_dogru = sum(1 for s in satirlar
                           if s["rota_var"]
                           and s["tani_darbogaz_serit"] == s["yer_gercegi"])
        self.assertLess(
            mutant_dogru, TRS.URETIM_KAPI_ESIGI,
            f"`darbogaz_serit` yayinlansaydi kol {mutant_dogru}/"
            f"{len(satirlar)} ile GECERDI — kapi bu mutasyonu ayirt etmiyor, "
            "vakum kapi (D-15)")

    def test_mutant_ile_gercek_yayin_AYRISIYOR(self):
        """Mutasyonun ETKILI oldugunu ispatlar: iki alan ayni degil."""
        ayrisan = [s for s in _satirlar()
                   if s["tani_darbogaz_serit"] != s["yayinlanan_road"]]
        self.assertTrue(
            ayrisan,
            "`darbogaz_serit` ile yayinlanan `road` 15 sahnenin hicbirinde "
            "ayrismiyor — mutasyon testi ALAKASIZ hale gelmis")


if __name__ == "__main__":
    unittest.main()
