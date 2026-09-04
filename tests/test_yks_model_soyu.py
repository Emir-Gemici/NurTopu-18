"""YKİ yerel algı modeli yalnız doğrulanmış kayıt soyundan yüklenmelidir."""

import ast
import inspect
import sys
import textwrap
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


KOK = Path(__file__).resolve().parents[1]
if str(KOK / "comms") not in sys.path:
    sys.path.insert(0, str(KOK / "comms"))
if str(KOK / "codes") not in sys.path:
    sys.path.insert(0, str(KOK / "codes"))

import model_registry  # noqa: E402
import yks_gui  # noqa: E402


class YksModelSoyuTests(unittest.TestCase):
    MODEL_ADI = "navitas_seg_v36_best.pt"
    MODEL_YOLU = KOK / "models" / MODEL_ADI

    @staticmethod
    def _profil(imgsz=512):
        return {
            "model_id": "navitas-seg-v36-512",
            "imgsz": imgsz,
            "sha256": "a" * 64,
        }

    def test_sha_dogrulamasi_yolo_yuklemesinden_ONCE_kosar(self):
        olaylar = []

        def coz(*args, **kwargs):
            olaylar.append("resolve")
            return self.MODEL_YOLU, self._profil()

        def yolo(*args, **kwargs):
            olaylar.append("yolo")
            return object()

        sahte_ultralytics = SimpleNamespace(YOLO=yolo)
        with (mock.patch.object(model_registry, "resolve_model", side_effect=coz)
              as resolve,
              mock.patch.dict(sys.modules, {"ultralytics": sahte_ultralytics})):
            model, yol, profil = yks_gui._dogrulanmis_algi_modeli_yukle(
                calisan_imgsz=512, beklenen_dosya=self.MODEL_ADI)

        self.assertIsNotNone(model)
        self.assertEqual(self.MODEL_YOLU, yol)
        self.assertEqual("a" * 64, profil["sha256"])
        self.assertEqual(["resolve", "yolo"], olaylar)
        resolve.assert_called_once_with(
            registry_path=KOK / "config" / "model_registry.json",
            verify=True)

    def test_worker_dogrulanmis_yukleyiciyi_kullanir(self):
        agac = ast.parse(textwrap.dedent(
            inspect.getsource(yks_gui.YksArayuz._algi_kos)))
        cagrilar = [n.func for n in ast.walk(agac) if isinstance(n, ast.Call)]
        self.assertTrue(any(
            isinstance(f, ast.Name)
            and f.id == "_dogrulanmis_algi_modeli_yukle"
            for f in cagrilar),
            "mutasyon: worker kayıt doğrulamasını atlayarak model yüklüyor")
        self.assertFalse(any(
            isinstance(f, ast.Name) and f.id == "YOLO" for f in cagrilar),
            "worker doğrulanmış yükleyiciyi atlayıp YOLO'yu doğrudan kuruyor")

    def test_sha_dogrulamasi_duserse_yolo_HIC_yuklenmez(self):
        yolo = mock.Mock()
        sahte_ultralytics = SimpleNamespace(YOLO=yolo)
        with (mock.patch.object(
                  model_registry, "resolve_model",
                  side_effect=model_registry.ModelRegistryError("SHA uyuşmuyor")),
              mock.patch.dict(sys.modules, {"ultralytics": sahte_ultralytics}),
              self.assertRaisesRegex(model_registry.ModelRegistryError, "SHA")):
            yks_gui._dogrulanmis_algi_modeli_yukle(
                calisan_imgsz=512, beklenen_dosya=self.MODEL_ADI)
        yolo.assert_not_called()

    def test_imgsz_ayrismasi_yolo_yuklemesini_fail_closed_durdurur(self):
        yolo = mock.Mock()
        sahte_ultralytics = SimpleNamespace(YOLO=yolo)
        with (mock.patch.object(
                  model_registry, "resolve_model",
                  return_value=(self.MODEL_YOLU, self._profil(imgsz=640))),
              mock.patch.dict(sys.modules, {"ultralytics": sahte_ultralytics}),
              self.assertRaisesRegex(RuntimeError, "çıkarım boyuyla ayrıştı")):
            yks_gui._dogrulanmis_algi_modeli_yukle(
                calisan_imgsz=512, beklenen_dosya=self.MODEL_ADI)
        yolo.assert_not_called()

    def test_dosya_adi_ayrismasi_yolo_yuklemesini_fail_closed_durdurur(self):
        yolo = mock.Mock()
        sahte_ultralytics = SimpleNamespace(YOLO=yolo)
        baska_yol = self.MODEL_YOLU.with_name("baska_model.pt")
        with (mock.patch.object(
                  model_registry, "resolve_model",
                  return_value=(baska_yol, self._profil())),
              mock.patch.dict(sys.modules, {"ultralytics": sahte_ultralytics}),
              self.assertRaisesRegex(RuntimeError, "kayıt defterinden ayrıştı")):
            yks_gui._dogrulanmis_algi_modeli_yukle(
                calisan_imgsz=512, beklenen_dosya=self.MODEL_ADI)
        yolo.assert_not_called()


if __name__ == "__main__":
    unittest.main()
