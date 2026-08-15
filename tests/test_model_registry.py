import unittest

from codes.model_registry import ModelRegistryError, load_registry, resolve_model


class ModelRegistryTests(unittest.TestCase):
    def test_default_is_verified_v30_competition_model(self):
        """T85: etkin profil v27 -> v30 (imgsz 512, DEGISMEDI).

        Tarihce: v4 kaydi 2026-07-15'ten kalmaydi ve uretim manifestiyle
        CELISIYORDU; `load_model` fail-closed oldugu icin saha kuru kosusunda
        `model_yukleme` halkasi bu yuzden dusuyordu (REVIEW_LOG D-106). T76'da
        v27'ye gecildi (D-115), T85'te v30'a (D-132 kabul kurali + D-133 kabul,
        kullanici karari). Boyut dayanagi D-112.

        `resolve_model` SHA-256'yi GERCEKTEN dogrular (verify=True): bu test
        defterdeki ozetin diskteki agirligin ozeti oldugunu da kanitlar — yani
        `path` alani cevrilip `sha256` unutulursa kapi KIRMIZI yanar.
        """
        path, spec = resolve_model()
        self.assertEqual(path.name, "navitas_seg_v30_best.pt")
        self.assertEqual(spec["imgsz"], 512)
        self.assertEqual(spec["status"], "competition")
        self.assertEqual(spec["model_id"], "navitas-seg-v30-512")

    def test_profiles_are_explicit_not_alias_directories(self):
        registry = load_registry()
        self.assertEqual(set(registry["profiles"]),
                         {"competition", "rpi_ncnn", "arac_referansi"})
        self.assertIn("not metric-equivalent", registry["profiles"]["rpi_ncnn"]["warning"])

    def test_olcek_katman3_profili_KARAR_modeli_olarak_secilemez(self):
        """T86: `arac_referansi` bir OLCEK referansidir, algi karari vermez.

        Ayri profil olmasinin sebebi madde 16 (yol/ozet ciplak yazilmasin);
        ama etkin profil ASLA o olamaz — olursa hakem ekrani zemin maskesi
        uretmeyen bir agirligi karar modeli diye yukler.
        """
        registry = load_registry()
        self.assertNotEqual("arac_referansi", registry["default_profile"])
        katman3 = registry["profiles"]["arac_referansi"]
        self.assertEqual("olcek-katman-3", katman3["status"])
        self.assertIn("`default_profile` OLAMAZ", katman3["warning"])

    def test_unknown_profile_fails_closed(self):
        with self.assertRaises(ModelRegistryError):
            resolve_model("latest-maybe")


if __name__ == "__main__":
    unittest.main()
