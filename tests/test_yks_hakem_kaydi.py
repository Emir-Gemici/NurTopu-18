import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock


KOK = Path(__file__).resolve().parents[1]
if str(KOK / "comms") not in sys.path:
    sys.path.insert(0, str(KOK / "comms"))

import hakem_kaydi  # noqa: E402
import yks_gui  # noqa: E402


class SahteWidget:
    def __init__(self):
        self.ayar = {}
        self.satirlar = []

    def config(self, **kwargs):
        self.ayar.update(kwargs)

    def insert(self, *args):
        self.satirlar.append(args)

    def see(self, *_args):
        pass


class KaliciKayitTesti(unittest.TestCase):
    def test_jsonl_oturum_olay_ve_fsync(self):
        with tempfile.TemporaryDirectory() as gecici:
            yol = Path(gecici) / "kanıt" / "hakem_log.jsonl"
            fsync = mock.Mock()
            saat = mock.Mock(return_value=1_725_000_000.125)
            mono = mock.Mock(side_effect=[10.0, 10.5, 11.0])
            kayit = hakem_kaydi.HakemKaydi(
                yol, saat=saat, monotonic=mono, fsync=fsync,
                oturum_id="oturum-test")
            kayit.yaz("ARM_ISTEGI", komut="ARM", deneme=1)
            self.assertTrue(kayit.kapat())
            satirlar = [json.loads(s) for s in
                        yol.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(
                ["OTURUM_BASLADI", "ARM_ISTEGI", "OTURUM_BITTI"],
                [s["olay"] for s in satirlar])
            self.assertTrue(all(s["oturum"] == "oturum-test" for s in satirlar))
            self.assertEqual("ARM", satirlar[1]["komut"])
            self.assertEqual(3, fsync.call_count,
                             "mutasyon: flush tek başına dayanıklı kanıt değildir")

    def test_varsayilan_yol_oturumlari_ayirir(self):
        an = datetime(2026, 9, 21, 8, 9, 10, tzinfo=timezone.utc)
        yol = hakem_kaydi.varsayilan_hakem_log_yolu(
            "O:/navitas", simdi=an, pid=4321)
        self.assertEqual("hakem_log.jsonl", yol.name)
        self.assertEqual("20260921_080910_4321", yol.parent.name)
        self.assertEqual("prova", yol.parent.parent.name)

    def test_nan_ve_kapali_dosyaya_yazma_reddedilir(self):
        with tempfile.TemporaryDirectory() as gecici:
            kayit = hakem_kaydi.HakemKaydi(Path(gecici) / "h.jsonl")
            with self.assertRaises(ValueError):
                kayit.yaz("TELEMETRI", bat=float("nan"))
            kayit.kapat()
            with self.assertRaises(RuntimeError):
                kayit.yaz("GECIKMIS")


class YksKayitBaglantisiTesti(unittest.TestCase):
    def _gui(self, kayit):
        g = object.__new__(yks_gui.YksArayuz)
        g.gunluk = SahteWidget()
        g.hakem_kaydi = kayit
        g.kanit_kaydi_hatasi = None
        g.btn_firlat = SahteWidget()
        g.btn_onay = SahteWidget()
        g.lbl_onay = SahteWidget()
        return g

    def test_ui_logu_ayni_anda_jsonlye_gider(self):
        with tempfile.TemporaryDirectory() as gecici:
            yol = Path(gecici) / "hakem.jsonl"
            kayit = hakem_kaydi.HakemKaydi(yol)
            g = self._gui(kayit)
            g._logla("Pixhawk ARM doğrulandı", "yesil")
            kayit.kapat()
            olaylar = [json.loads(s) for s in
                       yol.read_text(encoding="utf-8").splitlines()]
            ui = next(s for s in olaylar if s["olay"] == "UI_OLAYI")
            self.assertEqual("Pixhawk ARM doğrulandı", ui["mesaj"])
            self.assertEqual("yesil", ui["seviye"])

    def test_yazma_hatasi_gorunur_ve_kalkis_onayi_kapatir(self):
        bozuk = mock.Mock()
        bozuk.yaz.side_effect = OSError("disk dolu")
        g = self._gui(bozuk)
        with mock.patch("builtins.print"):
            self.assertIsNone(g._kanit_yaz("OLAY"))
        self.assertIn("disk dolu", g.kanit_kaydi_hatasi)
        self.assertEqual("disabled", g.btn_firlat.ayar.get("state"))
        self.assertEqual("disabled", g.btn_onay.ayar.get("state"))
        self.assertIn("KANIT KAYDI HATASI", g.lbl_onay.ayar.get("text", ""))


class KameraSunumBaglantisiTesti(unittest.TestCase):
    def _gui(self, istemci):
        g = object.__new__(yks_gui.YksArayuz)
        g.kamera_istemci = istemci
        g.kamera_url = "http://jetson:8080"
        g.lbl_kamera_img = SahteWidget()
        g.lbl_kamera_bilgi = SahteWidget()
        g._kamera_surum = -1
        g._kamera_foto = None
        g.hakem_kaydi = None
        return g

    @staticmethod
    def _jpeg():
        import cv2
        import numpy as np
        ok, veri = cv2.imencode(".jpg", np.zeros((12, 16, 3), dtype=np.uint8))
        if not ok:
            raise AssertionError("JPEG fikstürü üretilemedi")
        return veri.tobytes()

    def test_canli_kare_guiye_baglanir_sonra_bayat_kare_temizlenir(self):
        istemci = mock.Mock()
        istemci.snapshot.return_value = {
            "surum": 1, "jpeg": self._jpeg(), "durum": "CANLI",
            "hata": None, "kare_yasi_s": 0.1, "kare_sira": 7,
            "kaynak": "http://jetson:8080/kare.jpg", "calisiyor": True,
        }
        g = self._gui(istemci)
        with mock.patch("PIL.ImageTk.PhotoImage", return_value="foto"):
            g._kamera_tazele()
        self.assertEqual("foto", g.lbl_kamera_img.ayar.get("image"))
        self.assertEqual(yks_gui.YESIL, g.lbl_kamera_bilgi.ayar.get("fg"))

        istemci.snapshot.return_value = {
            "surum": 1, "jpeg": None, "durum": "KARE_BAYAT",
            "hata": "kamera karesi bayat", "kare_yasi_s": 3.0,
            "kare_sira": 7, "kaynak": "http://jetson:8080/kare.jpg",
            "calisiyor": True,
        }
        g._kamera_tazele()
        self.assertEqual("", g.lbl_kamera_img.ayar.get("image"))
        self.assertIsNone(g._kamera_foto,
                          "mutasyon: eski foto bayat durumda ekranda kalamaz")
        self.assertEqual(yks_gui.KIRMIZI, g.lbl_kamera_bilgi.ayar.get("fg"))

    def test_snapshot_istisnasi_gui_tikini_dusurmez(self):
        istemci = mock.Mock()
        istemci.snapshot.side_effect = OSError("wifi koptu")
        g = self._gui(istemci)
        g._kamera_tazele()
        self.assertEqual("", g.lbl_kamera_img.ayar.get("image"))
        self.assertIn("wifi koptu", g.lbl_kamera_bilgi.ayar.get("text", ""))
        self.assertEqual(yks_gui.KIRMIZI, g.lbl_kamera_bilgi.ayar.get("fg"))


if __name__ == "__main__":
    unittest.main()
