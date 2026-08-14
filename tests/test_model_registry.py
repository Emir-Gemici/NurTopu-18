import unittest

from codes.model_registry import ModelRegistryError, load_registry, resolve_model


class ModelRegistryTests(unittest.TestCase):
    def test_default_is_verified_v27_competition_model(self):
        """T76: etkin profil v4 -> v27, imgsz 640 -> 512.

        v4 kaydi 2026-07-15'ten kalmaydi ve uretim manifestiyle CELISIYORDU;
        `load_model` fail-closed oldugu icin saha kuru kosusunda
        `model_yukleme` halkasi bu yuzden dusuyordu (REVIEW_LOG D-106).
        Surum dayanagi D-115 (kabul), boyut dayanagi D-112.

        `resolve_model` SHA-256'yi GERCEKTEN dogrular (verify=True): bu test
        defterdeki ozetin diskteki agirligin ozeti oldugunu da kanitlar.
        """
        path, spec = resolve_model()
        self.assertEqual(path.name, "navitas_seg_v27_best.pt")
        self.assertEqual(spec["imgsz"], 512)
        self.assertEqual(spec["status"], "competition")
        self.assertEqual(spec["model_id"], "navitas-seg-v27-512")

    def test_profiles_are_explicit_not_alias_directories(self):
        registry = load_registry()
        self.assertEqual(set(registry["profiles"]), {"competition", "rpi_ncnn"})
        self.assertIn("not metric-equivalent", registry["profiles"]["rpi_ncnn"]["warning"])

    def test_unknown_profile_fails_closed(self):
        with self.assertRaises(ModelRegistryError):
            resolve_model("latest-maybe")


if __name__ == "__main__":
    unittest.main()
