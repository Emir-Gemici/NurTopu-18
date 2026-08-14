"""T73 KAPISI: saha kodu ELLE DUZENLENMEDEN kosabilmeli.

Kusur (saha kuru kosusu): iki halka DUSUK ve ikisi de ayni sinif —
  kamera        : "uretim girisi kaynagi PARAMETRIK almiyor: VideoCapture(0) sabit"
  model_yukleme : "yuklenen agirlik kayit defterindeki profille eslesmiyor ve
                   --model argumani yok"

Sartname SS2.2.1 sistemlerin goreve MUHURLU KUTULAR icinde intikal etmesini sart
kosar; muhurler hakem nezaretinde acilir. Yarisma gunu kamera indeksi ya da model
dosyasi degisirse KAYNAK DOSYA DUZENLEMEK prosedure aykiridir.

⚠ D-98'IN DERSI BU PAKETIN OMURGASI: o kayitta `saha_kuru_kosu.py`nin "olcek"
halkasi FONKSIYONUN VARLIGINA bakip GECTI yaziyordu, oysa halka bostu. Bu yuzden
burada hicbir test "argparse'ta secenek var mi" diye SORMAZ; her test secenegin
GERCEKTEN BESLEDIGINI olcer.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

KOK = Path(__file__).resolve().parents[1]
if str(KOK / "codes") not in sys.path:
    sys.path.insert(0, str(KOK / "codes"))

import rpi_inference as R  # noqa: E402


class KameraKaynagiTests(unittest.TestCase):
    """Kaynak indeks / cihaz yolu / dosya kabul etmeli."""

    def test_INDEKS_int_olarak_cozulur(self):
        for girdi, beklenen in ((None, 0), (0, 0), (2, 2), ("0", 0), ("3", 3),
                                ("  4 ", 4), ("", 0)):
            with self.subTest(girdi=girdi):
                self.assertEqual(beklenen, R.kamera_kaynagi_coz(girdi))

    def test_CIHAZ_YOLU_ve_DOSYA_str_kalir(self):
        for girdi in ("/dev/video1", "rtsp://10.0.0.5/live", "kayit.mp4",
                      r"C:\kare\a.avi"):
            with self.subTest(girdi=girdi):
                self.assertEqual(girdi, R.kamera_kaynagi_coz(girdi))

    def test_bool_REDDEDILIR(self):
        """`True` sessizce 1 indeksine donusmemeli — bu gizli hatadir."""
        with self.assertRaises(ValueError):
            R.kamera_kaynagi_coz(True)


class KameraBeslemesiTests(unittest.TestCase):
    """SECENEGIN VARLIGI DEGIL, VideoCapture'a ULASMASI olculur (D-98)."""

    def _capture_ne_aldi(self, **kw):
        alinan = []

        class _Cap:
            def __init__(self, kaynak):
                alinan.append(kaynak)

            def isOpened(self):
                return False

        with mock.patch.object(R.cv2, "VideoCapture", _Cap):
            R.run_camera(object(), 0.30, **kw)
        return alinan

    def test_cihaz_yolu_VideoCapture_a_ULASIR(self):
        self.assertEqual(["/dev/video7"],
                         self._capture_ne_aldi(kaynak="/dev/video7"))

    def test_indeks_INT_olarak_ULASIR(self):
        self.assertEqual([3], self._capture_ne_aldi(kaynak="3"))

    def test_VARSAYILAN_DEGISMEDI(self):
        """Geriye uyum: kaynak verilmezse yine indeks 0."""
        self.assertEqual([0], self._capture_ne_aldi())

    def test_argparse_KAYNAGI_TASIYOR(self):
        ap = R._arguman_ayristirici()
        secenekler = {o for a in ap._actions for o in a.option_strings}
        self.assertIn("--kaynak", secenekler)
        self.assertIn("--model", secenekler)


class ModelVarsayilaniTests(unittest.TestCase):
    """Madde 16: varsayilan CIPLAK YAZILMAZ, manifestten turetilir."""

    def test_varsayilan_MANIFESTTEN_gelir(self):
        yol = R.varsayilan_model_yolu()
        self.assertTrue(yol.is_file())
        self.assertEqual(".pt", yol.suffix)

    def test_kaynakta_CIPLAK_model_adi_YOK(self):
        """`navitas_seg_vNN_best.pt` kaynak dosyaya yazilmamis olmali."""
        import re
        kaynak = (KOK / "codes" / "rpi_inference.py").read_text(encoding="utf-8")
        self.assertIsNone(
            re.search(r"navitas_seg_v\d+_best\.pt", kaynak),
            "uretim kodunda CIPLAK model adi var — manifest tek kaynak olmali")

    def test_manifest_alani_GUVENSIZ_ise_reddedilir(self):
        for kotu in ("../gizli.pt", "alt/dizin.pt", "model.onnx", "", None, 5):
            with self.subTest(deger=kotu):
                with mock.patch.object(
                        R, "_uretim_manifesti",
                        lambda kok=None: ({"asil_model_pt": kotu}, Path("m.json"))):
                    with self.assertRaises(RuntimeError):
                        R.varsayilan_model_yolu()

    def test_manifest_YOKSA_sessiz_varsayilan_URETILMEZ(self):
        with mock.patch.object(
                R, "_uretim_manifesti",
                mock.Mock(side_effect=RuntimeError("manifest yok"))):
            with self.assertRaises(RuntimeError):
                R.varsayilan_model_yolu()


class FailClosedTests(unittest.TestCase):
    """🔴 Sessiz devam = sahada YANLIS MODELLE ucmak (D-89 sinifi)."""

    def _sahte_yolo(self):
        istenen = []

        class _Y:
            def __init__(self, yol, task=None):
                istenen.append(str(yol))
        return _Y, istenen

    def test_UYUSMAZLIKTA_yukselir(self):
        Y, _ = self._sahte_yolo()
        with mock.patch.object(R, "YOLO", Y), \
             mock.patch.object(R, "model_kayit_dogrula",
                               lambda *a, **k: (False, {"durum": "SINAMA"})):
            with self.assertRaises(RuntimeError) as ctx:
                R.load_model(R.varsayilan_model_yolu())
        self.assertIn("fail-closed", str(ctx.exception))

    def test_UYUM_varsa_yuklenir(self):
        Y, istenen = self._sahte_yolo()
        hedef = R.varsayilan_model_yolu()
        with mock.patch.object(R, "YOLO", Y), \
             mock.patch.object(R, "model_kayit_dogrula",
                               lambda *a, **k: (True, {"durum": "eslesti"})):
            _m, yol, detay = R.load_model(hedef, ayrinti=True)
        self.assertEqual(hedef.name, yol.name)
        self.assertEqual([str(hedef)], istenen, "--model yuklemeyi BESLEMIYOR")
        self.assertEqual("eslesti", detay["durum"])

    def test_GEVSETME_ACIKCA_istenmeli(self):
        """`kayit_zorunlu=False` verilmeden gevseme OLMAZ."""
        Y, _ = self._sahte_yolo()
        with mock.patch.object(R, "YOLO", Y), \
             mock.patch.object(R, "model_kayit_dogrula",
                               lambda *a, **k: (False, {"durum": "SINAMA"})):
            _m, yol, _d = R.load_model(R.varsayilan_model_yolu(),
                                       kayit_zorunlu=False, ayrinti=True)
        self.assertTrue(yol.is_file())
        self.assertTrue(R.MODEL_KAYIT_ZORUNLU,
                        "varsayilan gevsek olmamali (fail-closed esas)")

    def test_VAR_OLMAYAN_yol_ACIK_hata(self):
        with self.assertRaises(RuntimeError) as ctx:
            R.load_model(KOK / "models" / "boyle_bir_model_yok.pt")
        self.assertIn("bulunamadi", str(ctx.exception))

    def test_kayit_defteri_YOKSA_uyum_SAYILMAZ(self):
        """Yokluk "sorun yok" demek DEGILDIR — fail-closed tarafinda kalir."""
        uyumlu, detay = R.model_kayit_dogrula(
            R.varsayilan_model_yolu(), kok=KOK / "boyle_bir_dizin_yok")
        self.assertFalse(uyumlu)
        self.assertEqual("kayit_defteri_yok", detay["durum"])


class KayitDefteriDurumuTests(unittest.TestCase):
    """T76'da TERS CEVRILDI: iki bildirim artik ESLESMEK ZORUNDA.

    T73 bu testi "celiski VAR" diye yazmisti; amaci celiskiyi bugunku haliyle
    kaydetmek ve duzeltildigi an DUSEREK haber vermekti. T76'da kayit defteri
    v4'ten v27'ye cevrildi ve test gorevini yapip dustu — simdi ayni yerde
    ESITLIGI kilitliyor. Bir daha ayrisirlarsa BURADA yakalanir.
    """

    def test_manifest_ile_kayit_defteri_ESLESIYOR(self):
        uyumlu, detay = R.model_kayit_dogrula(R.varsayilan_model_yolu())
        self.assertTrue(
            uyumlu,
            f"uretim manifesti ile kayit defteri AYRISTI: {detay} — saha "
            "kuru kosusunda `model_yukleme` halkasi duser (D-106 tekrari)")
        self.assertEqual("eslesti", detay["durum"])

    def test_UC_UC_ayni_agirligi_gosteriyor(self):
        """Kayit defteri · uretim manifesti · hakem ekrani — tek ad.

        T58'in kusur sinifi (D-58/D-60/D-83): uclardan biri cevrilir, digeri
        unutulur; ekran ile saha SESSIZCE farkli modele duser.
        """
        import json
        sys.path.insert(0, str(KOK / "comms"))
        import yks_gui

        defter = json.loads(
            (KOK / "config" / "model_registry.json").read_text(encoding="utf-8"))
        defter_adi = Path(
            defter["profiles"][defter["default_profile"]]["path"]).name
        manifest_adi = R.varsayilan_model_yolu().name
        ekran_adi = yks_gui.YksArayuz.ALGI_MODEL_DOSYA

        self.assertEqual(defter_adi, manifest_adi, "manifest defterden AYRISTI")
        self.assertEqual(defter_adi, ekran_adi, "hakem ekrani defterden AYRISTI")

    def test_hakem_ekraninda_CIPLAK_model_adi_YOK(self):
        """Madde 16 / T76-5: surum adi ikinci kez ciplak yazilmaz."""
        import re
        kaynak = (KOK / "comms" / "yks_gui.py").read_text(encoding="utf-8")
        self.assertIsNone(
            re.search(r"navitas_seg_v\d+_best\.pt", kaynak),
            "hakem ekraninda CIPLAK model adi var — tek kaynak kayit "
            "defteri olmali (T58'de zincirin dort ucu bu yuzden elle "
            "hizalanmak zorundaydi)")

    def test_defter_okunamazsa_ekran_ad_UYDURMAZ(self):
        """Fail-closed: sessiz varsayilan = ekranin sahadan farkli model
        gostermesi. Yokluk 'sorun yok' DEGILDIR."""
        sys.path.insert(0, str(KOK / "comms"))
        import yks_gui

        for bozuk in ("{bozuk", "{}", '{"default_profile": "yok", "profiles": {}}',
                      '{"default_profile": "c", "profiles": {"c": {}}}',
                      '{"default_profile": "c", "profiles": {"c": {"path": "m.onnx"}}}'):
            with self.subTest(defter=bozuk[:40]):
                with mock.patch.object(Path, "read_text", return_value=bozuk):
                    with self.assertRaises(RuntimeError):
                        yks_gui._uretim_modeli_adi()


if __name__ == "__main__":
    unittest.main(verbosity=2)
