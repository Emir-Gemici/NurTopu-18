import unittest

from codes.model_registry import ModelRegistryError, load_registry, resolve_model


class ModelRegistryTests(unittest.TestCase):
    def test_default_is_verified_v4_competition_model(self):
        path, spec = resolve_model()
        self.assertEqual(path.name, "navitas_seg_v4_best.pt")
        self.assertEqual(spec["imgsz"], 640)
        self.assertEqual(spec["status"], "competition")

    def test_profiles_are_explicit_not_alias_directories(self):
        registry = load_registry()
        self.assertEqual(set(registry["profiles"]), {"competition", "rpi_ncnn"})
        self.assertIn("not metric-equivalent", registry["profiles"]["rpi_ncnn"]["warning"])

    def test_unknown_profile_fails_closed(self):
        with self.assertRaises(ModelRegistryError):
            resolve_model("latest-maybe")


if __name__ == "__main__":
    unittest.main()
