"""NEDEN: Costmap gerçek-görsel kapısı boş veya fiziksel ölçeksiz bir ölçümü
temiz güvenlik sonucu ve başarılı süreç olarak sunmamalıdır."""

import unittest

import test_costmap_on_images as hedef


def _kayit(*, ham_ihlal=False, enjekte_karar=False, enjekte_ihlal=False,
           mpp=0.1):
    return hedef.KareSonucu(
        kaynak="sahte.jpg",
        tur="foto",
        kare_no=0,
        ham_karar_var=True,
        ham_ihlal=ham_ihlal,
        ham_min_aciklik_px=0.0 if ham_ihlal else 100.0,
        enjekte_karar_var=enjekte_karar,
        enjekte_ihlal=enjekte_ihlal,
        enjekte_min_aciklik_px=100.0 if enjekte_karar else None,
        r_gerekli_px=10.0 if mpp is not None else None,
        mpp=mpp,
    )


class OlcumYokKapisiTests(unittest.TestCase):
    def test_sifir_enjekte_rota_exit_1_olur(self):
        sonuclar = [
            _kayit(ham_ihlal=i < 2, enjekte_karar=False)
            for i in range(6)
        ]

        ozet = hedef.guvenlik_ozeti(sonuclar)

        self.assertEqual("OLCUM_YOK", ozet["durum"])
        self.assertEqual(0, ozet["enjekte_karar_var"])
        self.assertEqual(1.0, ozet["enjekte_cekimserlik_orani"])
        self.assertEqual(1, hedef.ozet_cikis_kodu(ozet))

    def test_gercek_enjekte_karari_varsa_diger_kapilar_gecebilir(self):
        sonuclar = [
            _kayit(ham_ihlal=i < 2, enjekte_karar=True)
            for i in range(6)
        ]

        ozet = hedef.guvenlik_ozeti(sonuclar)

        self.assertEqual("GECTI", ozet["durum"])
        self.assertEqual(0, hedef.ozet_cikis_kodu(ozet))

    def test_geometri_ihlali_en_yuksek_onceliktedir(self):
        sonuclar = [
            _kayit(ham_ihlal=i < 2, enjekte_karar=True,
                   enjekte_ihlal=i == 0)
            for i in range(6)
        ]

        ozet = hedef.guvenlik_ozeti(sonuclar)

        self.assertEqual("GEOMETRI_HATASI", ozet["durum"])
        self.assertEqual(1, hedef.ozet_cikis_kodu(ozet))

    def test_zayif_ham_olcum_gecti_olamaz(self):
        sonuclar = [
            _kayit(ham_ihlal=False, enjekte_karar=True)
            for _ in range(6)
        ]

        ozet = hedef.guvenlik_ozeti(sonuclar)

        self.assertEqual("GUCSUZ", ozet["durum"])
        self.assertEqual(1, hedef.ozet_cikis_kodu(ozet))

    def test_olceksiz_zehir_kaydi_ihlal_istatistigine_girmez(self):
        sonuclar = [
            _kayit(ham_ihlal=True, enjekte_karar=True),
            _kayit(ham_ihlal=False, enjekte_karar=True),
            _kayit(ham_ihlal=True, enjekte_karar=True,
                   enjekte_ihlal=True, mpp=None),
        ]

        ozet = hedef.guvenlik_ozeti(sonuclar)

        self.assertEqual(2, ozet["olcekli_kare"])
        self.assertEqual(1, ozet["olceksiz_kare"])
        self.assertEqual(1, ozet["ham_ihlal"])
        self.assertEqual(0.5, ozet["ham_ihlal_orani"])
        self.assertEqual(0, ozet["enjekte_ihlal"])
        self.assertEqual("KISMI_OLCUM", ozet["durum"])
        self.assertEqual(1, hedef.ozet_cikis_kodu(ozet))

    def test_yalniz_olceksiz_kareler_olcum_yok_ve_exit_1(self):
        ozet = hedef.guvenlik_ozeti([
            _kayit(ham_ihlal=True, enjekte_karar=True,
                   enjekte_ihlal=True, mpp=None),
        ])

        self.assertEqual("OLCUM_YOK", ozet["durum"])
        self.assertIsNone(ozet["ham_ihlal_orani"])
        self.assertIsNone(ozet["enjekte_cekimserlik_orani"])
        self.assertIsNone(
            ozet["enjekte_kesisim_dilate_arac_r_gerekli_tam_sifir"])
        self.assertEqual(1, hedef.ozet_cikis_kodu(ozet))

    def test_sonuc_donustur_null_ihlal_ve_esigi_korur(self):
        olceksiz = {
            "ham": {"karar_var": False, "ihlal": None,
                    "min_aciklik_px": None},
            "enj": {"karar_var": False, "ihlal": None,
                    "min_aciklik_px": None},
            "r_gerekli_px": None,
            "mpp": None,
        }

        kayit = hedef.sonuc_donustur("sahte.jpg", "foto", 0, olceksiz)

        self.assertIsNone(kayit.ham_ihlal)
        self.assertIsNone(kayit.enjekte_ihlal)
        self.assertIsNone(kayit.r_gerekli_px)
        self.assertIsNone(kayit.mpp)


if __name__ == "__main__":
    unittest.main()
