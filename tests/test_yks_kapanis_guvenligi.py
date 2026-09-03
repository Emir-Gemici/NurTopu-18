"""YKI kapanisi: bir kaynagin hatasi diger kaynaklari acik birakamaz.

Gercek Tk penceresi acilmaz. Uretim ``main()`` yolunun kullanmasi gereken saf
kapanis yardimcisi sahte kamera, kanit kaydi ve link ile sinanir.
"""

import ast
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


KOK = Path(__file__).resolve().parents[1]
GUI_YOLU = KOK / "comms" / "yks_gui.py"
sys.path.insert(0, str(KOK / "comms"))

import yks_gui  # noqa: E402


YARDIMCI_ADI = "kapanis_kaynaklarini_temizle"


def _yardimciyi_cagir(app, link):
    """Hata raporlama tercihini dayatmadan tum kaynak denemelerini olc."""
    yardimci = getattr(yks_gui, YARDIMCI_ADI)
    try:
        return yardimci(app, link)
    except Exception:
        # Yardimci, tum kaynaklari denedikten sonra toplu hata yukseltebilir.
        # Bu kapinin iddiasi hata sunum bicimi degil, kaynak sizdirmamasidir.
        return None


def _kaynaklar(*, kamera_hatasi=None, kayit_hatasi=None, link_hatasi=None):
    kamera = mock.Mock()
    kamera.durdur.side_effect = kamera_hatasi
    kayit = mock.Mock()
    kayit.kapat.side_effect = kayit_hatasi
    link = mock.Mock()
    link.close.side_effect = link_hatasi
    app = SimpleNamespace(kamera_istemci=kamera, hakem_kaydi=kayit)
    return app, link, kamera, kayit


class KapanisKaynakBagimsizligiTests(unittest.TestCase):
    def test_kamera_durdurma_hatasi_kayit_ve_linki_acik_birakamaz(self):
        app, link, kamera, kayit = _kaynaklar(
            kamera_hatasi=RuntimeError("kamera worker kapanmadi"))

        _yardimciyi_cagir(app, link)

        kamera.durdur.assert_called_once_with()
        kayit.kapat.assert_called_once_with()
        link.close.assert_called_once_with()

    def test_kayit_kapatma_hatasi_linki_acik_birakamaz(self):
        app, link, kamera, kayit = _kaynaklar(
            kayit_hatasi=OSError("fsync/kapatma hatasi"))

        _yardimciyi_cagir(app, link)

        kamera.durdur.assert_called_once_with()
        kayit.kapat.assert_called_once_with()
        link.close.assert_called_once_with()

    def test_saglikli_kapanista_her_kaynak_tam_bir_kez_kapanir(self):
        app, link, kamera, kayit = _kaynaklar()

        _yardimciyi_cagir(app, link)

        kamera.durdur.assert_called_once_with()
        kayit.kapat.assert_called_once_with()
        link.close.assert_called_once_with()


class MainBaglantisiTests(unittest.TestCase):
    def test_main_finally_saf_kapanis_yardimcisini_cagirir(self):
        agac = ast.parse(GUI_YOLU.read_text(encoding="utf-8"), filename=str(GUI_YOLU))
        main = next(
            (dugum for dugum in agac.body
             if isinstance(dugum, ast.FunctionDef) and dugum.name == "main"),
            None)
        self.assertIsNotNone(main, "yks_gui.main() bulunamadi")

        finally_cagrilari = []
        for dugum in ast.walk(main):
            if not isinstance(dugum, ast.Try):
                continue
            for alt in dugum.finalbody:
                for cagri in ast.walk(alt):
                    if isinstance(cagri, ast.Call):
                        finally_cagrilari.append(cagri)

        self.assertTrue(
            any(isinstance(c.func, ast.Name) and c.func.id == YARDIMCI_ADI
                for c in finally_cagrilari),
            f"main() finally, {YARDIMCI_ADI}() yardimcisini cagirmiyor")


if __name__ == "__main__":
    unittest.main()
