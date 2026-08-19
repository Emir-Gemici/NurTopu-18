"""T103 KAPISI: saha paketi KAYIT DEFTERINI tasir ve depoyla AYNIDIR.

KUSUR (REVIEW_LOG D-177 §2 · olculdu). `scripts/jetson_paket_hazirla.py`
dokuz `.py` tasiyordu ama `config/model_registry.json` TASIMIYORDU. Sonuc:
kilavuza gore kurulan bir Jetson MODEL YUKLEYEMIYORDU —

    model_kayit_dogrula -> False | durum "kayit_defteri_yok"
    load_model -> RuntimeError: MODEL KAYIT DOGRULAMASI BASARISIZ — fail-closed

Tek calistirma yolu `--kayit-dogrulamasiz` idi ve o bayrak T73'te BILEREK
kurulan yanlis-model korumasini kapatir. Yani saha ya HIC kosuyordu ya da
KORUMASIZ kosuyordu.

⚠ Bu, S5'in URETTIGI bir kusur DEGILDIR: zorunluluk T73'te geldi, kilavuza ve
paketleyiciye yansitilmadi; S5 yalnizca GORUNUR kildi.

BU DOSYANIN ISI: bir daha senkronsuz kalmasini engellemek. Paket defteri
tasiyor mu, ve depodakiyle BIREBIR ayni mi.
"""

import hashlib
import json
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
DEPO_DEFTERI = KOK / "config" / "model_registry.json"
PAKET_DEFTERI = KOK / "jetson_paket" / "config" / "model_registry.json"


def _sha(yol: Path) -> str:
    return hashlib.sha256(yol.read_bytes()).hexdigest()


class JetsonPaketDefteri(unittest.TestCase):

    def test_paket_kayit_defterini_TASIYOR(self):
        self.assertTrue(
            PAKET_DEFTERI.is_file(),
            f"{PAKET_DEFTERI} YOK — kilavuza gore kurulan Jetson `load_model` "
            "asamasinda fail-closed duser (T103 · D-177). "
            "`scripts/jetson_paket_hazirla.py` kosulmali.")

    def test_paket_defteri_depo_defteriyle_BIREBIR_AYNI(self):
        self.assertTrue(DEPO_DEFTERI.is_file(), f"{DEPO_DEFTERI} yok")
        self.assertTrue(PAKET_DEFTERI.is_file(), f"{PAKET_DEFTERI} yok")
        self.assertEqual(
            _sha(DEPO_DEFTERI), _sha(PAKET_DEFTERI),
            "paket defteri depo defterinden AYRISTI — `jetson_paket_hazirla.py` "
            "yeniden kosulmali. Ayrisma sahada BASKA bir modelin beklenmesi "
            "demektir (D-58/D-60/D-116 sapma sinifi).")

    def test_paket_defteri_URETIM_PROFILINI_iceriyor(self):
        """Dosyanin VAR olmasi yetmez; ise yarar icerikte olmali."""
        veri = json.loads(PAKET_DEFTERI.read_text(encoding="utf-8"))
        profil = veri["profiles"][veri["default_profile"]]
        self.assertIn("path", profil)
        self.assertIn("imgsz", profil)

    def test_paketlenmis_duzende_DEFTER_BULUNUYOR(self):
        """`rpi_inference` defteri `_here.parent / "config"` diye arar.

        Paket duzeninde `_here` = `jetson_paket/kod`, dolayisiyla aranan yer
        `jetson_paket/config`tir. Hedef dizinin `kod/` OLMAMASI bu testin
        asil konusudur — yanlis dizine kopyalamak sessizce ise yaramaz.
        """
        paket_kod = KOK / "jetson_paket" / "kod"
        self.assertTrue(paket_kod.is_dir())
        aranan = paket_kod.parent / "config" / "model_registry.json"
        self.assertEqual(PAKET_DEFTERI, aranan)
        self.assertTrue(aranan.is_file())

    def test_paketleyici_defteri_KOPYALAR_LISTESINDE_tutuyor(self):
        """Dosya elle konmus olabilir; paketleyici onu YENILEMELI de.

        Aksi halde depo defteri degisince paket sessizce bayatlar — testin
        (2) maddesi bunu yakalar ama SEBEBI burada kilitlenir.
        """
        import importlib.util
        yol = KOK / "scripts" / "jetson_paket_hazirla.py"
        spec = importlib.util.spec_from_file_location("_jph", yol)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        hedefler = set(mod.KOPYALAR.values())
        self.assertIn(PAKET_DEFTERI, hedefler,
                      "kayit defteri KOPYALAR sozlugunde YOK — paket "
                      "yenilendiginde defter guncellenmez")

    # ── POZITIF KONTROL ───────────────────────────────────────────────────
    def test_POZITIF_KONTROL_dosya_yoksa_kapi_DUSER(self):
        """Yukaridaki kapilar "dosya var" diye bos yere yesil yanmiyor.

        Var olmayan bir yol icin AYNI kontroller uygulanir ve DUSMELIDIR;
        yani kontrol gercekten dosyanin varligina bakiyor (D-15/K-04).
        """
        yok = KOK / "jetson_paket" / "config" / "boyle_bir_defter_yok.json"
        self.assertFalse(yok.is_file())
        with self.assertRaises(FileNotFoundError):
            _sha(yok)


if __name__ == "__main__":
    unittest.main()
