import unittest

from codes.model_registry import ModelRegistryError, load_registry, resolve_model


class ModelRegistryTests(unittest.TestCase):
    def test_default_is_verified_v36_competition_model(self):
        """v36 terfisi: etkin profil v35 -> v36 (imgsz 512, DEGISMEDI).

        Tarihce: v4 kaydi 2026-07-15'ten kalmaydi ve uretim manifestiyle
        CELISIYORDU; `load_model` fail-closed oldugu icin saha kuru kosusunda
        `model_yukleme` halkasi bu yuzden dusuyordu (REVIEW_LOG D-106). T76'da
        v27'ye gecildi (D-115), T85'te v30'a (D-132 kabul kurali + D-133 kabul,
        kullanici karari), 2026-08-19'da v34'e (T54 kosumu `v23_t54_engelli`;
        on kayit `scripts/olcum/v22_v23_on_kayit.md` olcumlerden ONCE yazildi,
        hukum D-181, sevk karari KULLANICININ). 2026-08-21'de v35'e gecildi
        (kosum `t127_temiz`: T122 secenegi (a)+(c) + T127 TEMIZ bolum; on kayit
        `results/t127_on_kayit.md` olcumlerden ONCE yazildi, sonuc D-249,
        mimar denetimi D-255, sevk karari YINE KULLANICININ — T130).
        2026-08-26'da v36'ya gecildi (kosum `gece_v7a_v35taban`, taban v35;
        on kayit `results/gece_20260826/ON_KAYIT.md` SS12/SS14 olcumlerden
        ONCE yazildi, sonuc D-293, sevk karari YINE KULLANICININ).
        🔴 v36 TERFISI KURAL DISIDIR: on kayitli gercek-kare esikleri
        ROTA >= 10 (olculen 8) ve MASKE_YOK <= 10 (olculen 16) GECILMEDI;
        kullanici "izin veriyorum kurala ragmen" dedi (ON_KAYIT SS15).
        Esikler DEGISTIRILMEDI ve sonraki terfileri baglar (CONTRACTS SS12).
        ⚠ v34 ve v35 SILINMEDI: v35 bugunun YEDEK adayidir ve FARKLI HATA
        YAPAR (arena K3/K4/K6'da daha iyi; ama gercek karelerde rotayi beton
        kanal ustunden gecirir). Boyut dayanagi D-112.

        ⚠ Bu testteki surum adi ELLE guncellenir ve bu BILEREK boyledir:
        defterden turetilseydi test totolojik olur, kazara degisen bir profili
        YAKALAYAMAZDI. Surum bumpi terfinin BILINCLI bir adimidir.

        `resolve_model` SHA-256'yi GERCEKTEN dogrular (verify=True): bu test
        defterdeki ozetin diskteki agirligin ozeti oldugunu da kanitlar — yani
        `path` alani cevrilip `sha256` unutulursa kapi KIRMIZI yanar.
        """
        path, spec = resolve_model()
        self.assertEqual(path.name, "navitas_seg_v36_best.pt")
        self.assertEqual(spec["imgsz"], 512)
        self.assertEqual(spec["status"], "competition")
        self.assertEqual(spec["model_id"], "navitas-seg-v36-512")

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
