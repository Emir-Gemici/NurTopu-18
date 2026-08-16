"""T86 KAPISI: olcek kahini URETIM karar yoluna gercekten bagli mi?

KUSUR SINIFI (D-98'in dersi): bir halkanin FONKSIYONUN VARLIGINI sinamasi
sahte GECTI uretir. T83 kahini yazdi ve `tests/test_olcek_kahini.py` onu
birim olarak dogruladi; ama D-126 ayni kayitta "uretim cagri yerlerine ve
EKRANA BAGLANMADI" diyordu ve D-136 sonucu olctu: 7 kaynagin 5'i OLCEK_YOK.

Bu paket kahinin DAVRANISINI uretim yolunda sinar:
  1. Telemetri/beyan varsa katman 1 kazanir ve carpan 1.00 kalir (GERIYE UYUM).
  2. Telemetri yoksa katman 3 devreye girer ve GUVEN CARPANI karara YANSIR.
  3. 🔴 KAPI GEVSEMEZ: hicbir katman uretemezse `rota_olcek_reddi` HALA reddeder.
  4. 🔴 SESSIZ DUSUS YOK: hangi katmanin neden dustugu metinde YAZILIDIR.
  5. Katman 2 senaryo BEYAN EDILMEDIKCE devreye girmez (2,5 kat olcek hatasi).
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

KOK = Path(__file__).resolve().parents[1]
for alt in ("codes", "comms"):
    if str(KOK / alt) not in sys.path:
        sys.path.insert(0, str(KOK / alt))

from karar_sozlesmesi import (OLCEK_GUVEN_CARPANI,  # noqa: E402
                              OLCEK_KAYNAK_ARAC,
                              OLCEK_KAYNAK_ARENA,
                              OLCEK_KAYNAK_ETIKETI,
                              OLCEK_KAYNAK_TELEMETRI,
                              olcek_guveni_uygula, rota_olcek_reddi,
                              olcek_kaynak_metni)
from arac_maskesi import ARAC_ASGARI_SAYI  # noqa: E402
from rpi_inference import kare_olcek_kahini  # noqa: E402

ICERIK = (0, 0, 1024, 576)
#: 1,80 m / 24 px = 0,075 m/px — D-124'un olctugu bandin ortasi.
ARAC_KISA_KENAR_PX = 24.0
#: T89/D-143: olcek katmani ARTIK asgari `ARAC_ASGARI_SAYI` arac ister.
#: Bu fiksturler katman SIRASINI ve GUVEN CARPANINI sinar, SAYIMI degil —
#: bu yuzden esigi saglayan ESIT kenarlar kullanilir. Medyan DEGISMEZ
#: (24,0), dolayisiyla bu testlerin mpp iddialari BIREBIR korunur.
ARAC_YETERLI = [ARAC_KISA_KENAR_PX] * ARAC_ASGARI_SAYI
#: Esik ALTI fikstur de sozlesmeden turer (denetim bulgusu 5): sabit `1`
#: yazilirsa esik 1'e cekildiginde testler YANLIS SEBEPLE duser.
ARAC_YETERSIZ = [ARAC_KISA_KENAR_PX] * max(0, ARAC_ASGARI_SAYI - 1)


class _SahteOBB:
    """Ultralytics OBB donusunun YALNIZ okunan alanlarini taklit eder."""

    def __init__(self, kisa_kenarlar, sinif_adi="small vehicle"):
        self.names = {0: sinif_adi}
        self._kisa = list(kisa_kenarlar)

    def predict(self, bgr, imgsz=None, conf=None, verbose=False):
        import types

        class _T:
            def __init__(self, dizi):
                self._d = np.asarray(dizi, dtype=np.float32)

            def cpu(self):
                return self

            def numpy(self):
                return self._d

        n = len(self._kisa)
        # xywhr: [x, y, genislik, yukseklik, aci] — kisa kenar min(w, h).
        # ⚠ Araclar AYRI konumlara yerlestirilir (T89 · denetim bulgusu 4).
        # Ilk surumde hepsi (10, 10) idi; mukerrer eleme gelince bu fikstur
        # "tek arac" anlamina gelirdi ve testler YANLIS SEBEPLE dusrerdi.
        xywhr = np.zeros((n, 5), dtype=np.float32)
        for i, k in enumerate(self._kisa):
            xywhr[i] = (60.0 + 200.0 * i, 60.0 + 120.0 * i, k * 2.5, k, 0.0)
        return [types.SimpleNamespace(
            obb=types.SimpleNamespace(cls=_T(np.zeros(n)), xywhr=_T(xywhr),
                                      xyxyxyxy=None))]


def _kare():
    return np.zeros((576, 1024, 3), np.uint8)


class KatmanSirasiTests(unittest.TestCase):
    """Hangi katman kazaniyor — ve KAYNAGINI beyan ediyor mu?"""

    def test_beyan_VARSA_katman1_kazanir_carpan_DEGISMEZ(self):
        """GERIYE UYUM: arena yolu telemetriyle koşar, T86 onu bozmamali."""
        k = kare_olcek_kahini(0.0781, None, ICERIK, bgr=_kare(),
                              arac_modeli=_SahteOBB(ARAC_YETERLI))
        self.assertEqual(OLCEK_KAYNAK_TELEMETRI, k["kaynak"])
        self.assertAlmostEqual(0.0781, k["mpp"])
        self.assertEqual(1.00, k["guven_carpani"])

    def test_beyan_YOKSA_katman3_devreye_girer(self):
        k = kare_olcek_kahini(None, None, ICERIK, bgr=_kare(),
                              arac_modeli=_SahteOBB(ARAC_YETERLI))
        self.assertEqual(OLCEK_KAYNAK_ARAC, k["kaynak"])
        self.assertAlmostEqual(1.80 / ARAC_KISA_KENAR_PX, k["mpp"], places=6)

    def test_katman3_MEDYAN_kullanir_tek_kotu_kutu_kaydirmaz(self):
        """Bir kamyon/golge kutusu olcegi tek basina bozamamali (D-124)."""
        k = kare_olcek_kahini(None, None, ICERIK, bgr=_kare(),
                              arac_modeli=_SahteOBB([24.0, 24.0, 24.0, 300.0]))
        self.assertEqual(OLCEK_KAYNAK_ARAC, k["kaynak"])
        self.assertAlmostEqual(1.80 / 24.0, k["mpp"], places=6)

    def test_arac_SINIFI_ad_ile_eslesir_yabanci_sinif_olcek_URETMEZ(self):
        """S1/K-6: id kayar, ad kaymaz. `ship` bir arac referansi DEGILDIR."""
        k = kare_olcek_kahini(None, None, ICERIK, bgr=_kare(),
                              arac_modeli=_SahteOBB([24.0] * ARAC_ASGARI_SAYI, sinif_adi="ship"))
        self.assertIsNone(k["kaynak"])
        self.assertIsNone(k["mpp"])


class KapiGevsemediTests(unittest.TestCase):
    """🔴 T86'nin DEGISTIRMEDIGI sey: olcek yoksa rota YAYINLANMAZ."""

    def test_hicbir_katman_uretmezse_OLCEK_KAPISI_HALA_REDDEDER(self):
        k = kare_olcek_kahini(None, None, ICERIK, bgr=_kare(), arac_modeli=None)
        self.assertIsNone(k["mpp"])
        self.assertIsNotNone(rota_olcek_reddi(k["mpp"]),
                             "olcek kahini bagliyken kapi GEVSEMIS — "
                             "olceksiz kare reddedilmiyor")

    def test_arac_YOKSA_olcek_uydurulmaz(self):
        k = kare_olcek_kahini(None, None, ICERIK, bgr=_kare(),
                              arac_modeli=_SahteOBB([]))
        self.assertIsNone(k["mpp"])
        self.assertIsNotNone(rota_olcek_reddi(k["mpp"]))

    def test_dedektor_PATLARSA_olcek_uydurulmaz(self):
        class _Patlak:
            names = {0: "small vehicle"}

            def predict(self, *a, **k):
                raise RuntimeError("cuda out of memory")

        k = kare_olcek_kahini(None, None, ICERIK, bgr=_kare(),
                              arac_modeli=_Patlak())
        self.assertIsNone(k["mpp"])
        self.assertIsNotNone(rota_olcek_reddi(k["mpp"]))
        self.assertIn("HATA", dict(k["denenen"])[OLCEK_KAYNAK_ARAC])

    def test_katman3_olcegi_GUVENI_DUSURUR(self):
        """Katman 3'ten gelen olcek telemetriyle AYNI guvende sunulamaz."""
        ham = 0.90
        k1 = kare_olcek_kahini(0.0781, None, ICERIK)
        k3 = kare_olcek_kahini(None, None, ICERIK, bgr=_kare(),
                               arac_modeli=_SahteOBB(ARAC_YETERLI))
        g1 = olcek_guveni_uygula(ham, k1["kaynak"])
        g3 = olcek_guveni_uygula(ham, k3["kaynak"])
        self.assertAlmostEqual(ham * 1.00, g1)
        self.assertAlmostEqual(ham * OLCEK_GUVEN_CARPANI[OLCEK_KAYNAK_ARAC], g3)
        self.assertLess(g3, g1, "katman 3 guveni DUSURMUYOR")


class SessizDususYokTests(unittest.TestCase):
    """🔴 Hangi katmanin NEDEN devreye girmedigi YAZILI olmali."""

    def test_dokum_UC_katmani_da_sayar(self):
        k = kare_olcek_kahini(None, None, ICERIK, bgr=_kare(), arac_modeli=None)
        kaynaklar = [x for x, _ in k["denenen"]]
        self.assertEqual([OLCEK_KAYNAK_TELEMETRI, OLCEK_KAYNAK_ARENA,
                          OLCEK_KAYNAK_ARAC], kaynaklar)

    def test_DEDEKTOR_yoklugu_ile_ARAC_yoklugu_AYRI_raporlanir(self):
        """Ikisi ayni sey degildir: biri yapilandirma, digeri sahne."""
        yok = dict(kare_olcek_kahini(None, None, ICERIK, bgr=_kare(),
                                     arac_modeli=None)["denenen"])
        bos = dict(kare_olcek_kahini(None, None, ICERIK, bgr=_kare(),
                                     arac_modeli=_SahteOBB([]))["denenen"])
        self.assertIn("dedektor", yok[OLCEK_KAYNAK_ARAC])
        self.assertIn("arac YOK", bos[OLCEK_KAYNAK_ARAC])
        self.assertNotEqual(yok[OLCEK_KAYNAK_ARAC], bos[OLCEK_KAYNAK_ARAC])

    def test_ekran_metni_KAYNAGI_ve_CARPANI_tasir(self):
        k = kare_olcek_kahini(None, None, ICERIK, bgr=_kare(),
                              arac_modeli=_SahteOBB(ARAC_YETERLI))
        metin = olcek_kaynak_metni(k)
        self.assertIn(OLCEK_KAYNAK_ETIKETI[OLCEK_KAYNAK_ARAC], metin)
        self.assertIn("0.86", metin)

    def test_olceksiz_metin_HER_katmanin_sebebini_yazar(self):
        metin = olcek_kaynak_metni(
            kare_olcek_kahini(None, None, ICERIK, bgr=_kare(), arac_modeli=None))
        for kaynak in (OLCEK_KAYNAK_TELEMETRI, OLCEK_KAYNAK_ARENA,
                       OLCEK_KAYNAK_ARAC):
            with self.subTest(kaynak=kaynak):
                self.assertIn(OLCEK_KAYNAK_ETIKETI[kaynak], metin)


class Katman2BeyanTests(unittest.TestCase):
    """🔴 Senaryo BEYAN EDILIR, tahmin edilmez (yanlis senaryo = 2,5 kat hata)."""

    def test_senaryo_BEYAN_EDILMEDIKCE_katman2_calismaz(self):
        k = kare_olcek_kahini(None, None, ICERIK, arena_sinir_px=900.0,
                              senaryo=None)
        self.assertIsNone(k["mpp"])
        self.assertIn("BEYAN EDILMEDI", dict(k["denenen"])[OLCEK_KAYNAK_ARENA])

    def test_senaryo_beyan_edilince_katman2_uretir_ve_carpani_070(self):
        k = kare_olcek_kahini(None, None, ICERIK, arena_sinir_px=900.0,
                              senaryo="HTAB")
        self.assertEqual(OLCEK_KAYNAK_ARENA, k["kaynak"])
        self.assertAlmostEqual(50.0 / 900.0, k["mpp"], places=6)
        self.assertEqual(0.70, k["guven_carpani"])

    def test_katman2_katman3ten_ONCE_denenir(self):
        """Siralama kullanicinin karari; olcum onu dogrulamasa da (D-126) UYULUR."""
        k = kare_olcek_kahini(None, None, ICERIK, bgr=_kare(),
                              arac_modeli=_SahteOBB(ARAC_YETERLI),
                              arena_sinir_px=900.0, senaryo="HTAB")
        self.assertEqual(OLCEK_KAYNAK_ARENA, k["kaynak"])



class AsgariAracSayisiTests(unittest.TestCase):
    """T89 · D-143 — olcek katmani ALAN DISINDA susmali.

    KUSUR: T86 katman 3'u uretime bagladiginda `gemini` (yer seviyesinden
    cekilmis yol fotograflari) 3 karede olcek turetti ve 1 karede ROTA URETTI
    (D-142). Yandan/egik bakista yonlu kutunun kisa kenari govde genisligi
    DEGILDIR; uydurma olcek -> uydurma r_gerekli -> gecilemeyecek koridor
    gecilebilir sayilir. EMNIYETSIZ yon.

    OLCULMUS ESIK (D-143, kaynak basina 20 kare):
        >= 3 arac bulunan kare
          drone 20/20 · kompozit 9/9 · gemini 1/20 · val 0/20 · test 0/20
    Once denenen "sacilim" olcutu CURUDU: gemini'nin nitelikli tek karesi
    IQR/medyan 0,101 verdi ve drone'un bandinin (0,084-0,117) TAM ICINDEYDI.
    """

    def test_esik_ALTINDA_olcek_URETILMEZ(self):
        # Denetim bulgusu 5: esik 1'e cekilirse dongu BOS doner ve test
        # BOSA gecerdi. Bos gecisi acikca reddet.
        if ARAC_ASGARI_SAYI <= 1:
            self.skipTest("esik 1; 'esik alti' diye bir durum yok")
        for n in range(1, ARAC_ASGARI_SAYI):
            with self.subTest(arac=n):
                k = kare_olcek_kahini(None, None, ICERIK, bgr=_kare(),
                                      arac_modeli=_SahteOBB(
                                          [ARAC_KISA_KENAR_PX] * n))
                self.assertIsNone(k["mpp"], f"{n} aracla olcek URETILMEMELI")
                self.assertNotEqual(k["kaynak"], OLCEK_KAYNAK_ARAC)

    def test_esikTE_olcek_URETILIR(self):
        k = kare_olcek_kahini(None, None, ICERIK, bgr=_kare(),
                              arac_modeli=_SahteOBB(ARAC_YETERLI))
        self.assertEqual(k["kaynak"], OLCEK_KAYNAK_ARAC)
        self.assertAlmostEqual(k["mpp"], 1.80 / ARAC_KISA_KENAR_PX, places=6)

    def test_esik_ALTINDA_kapi_HALA_REDDEDER(self):
        """Sessiz gecis yok: olcek uretilmeyince rota kapisi da reddetmeli."""
        k = kare_olcek_kahini(None, None, ICERIK, bgr=_kare(),
                              arac_modeli=_SahteOBB(ARAC_YETERSIZ))
        self.assertIsNotNone(rota_olcek_reddi(k["mpp"]))

    def test_SEBEP_sayiyi_yazar_arac_YOKLUGUNDAN_ayirt_edilir(self):
        """Hakem "arac yok" ile "arac az"i AYIRT edebilmeli (sessiz dusus yok)."""
        az = dict(kare_olcek_kahini(None, None, ICERIK, bgr=_kare(),
                                    arac_modeli=_SahteOBB(
                                        [ARAC_KISA_KENAR_PX]))["denenen"])
        yok = dict(kare_olcek_kahini(None, None, ICERIK, bgr=_kare(),
                                     arac_modeli=_SahteOBB([]))["denenen"])
        self.assertIn("asgari", az[OLCEK_KAYNAK_ARAC])
        self.assertIn("arac YOK", yok[OLCEK_KAYNAK_ARAC])
        self.assertNotEqual(az[OLCEK_KAYNAK_ARAC], yok[OLCEK_KAYNAK_ARAC])

    def test_esik_SOZLESMEDEN_gelir_testte_ikinci_kez_TANIMLANMAZ(self):
        """Madde 16: esik tek kaynakta. Kod 3'ten baskasina cekilirse bu test
        de onunla birlikte hareket eder; sabit sayi CIVILENMEZ."""
        from arac_maskesi import arac_kisa_kenar_medyani
        kare = _kare()
        alti = _SahteOBB([ARAC_KISA_KENAR_PX] * (ARAC_ASGARI_SAYI - 1))
        tam = _SahteOBB([ARAC_KISA_KENAR_PX] * ARAC_ASGARI_SAYI)
        self.assertIsNone(arac_kisa_kenar_medyani(kare, alti))
        self.assertIsNotNone(arac_kisa_kenar_medyani(kare, tam))

class OlcekCozunurluguTests(unittest.TestCase):
    """T89 · bagimsiz denetim bulgusu 3 — olcek yolunun cikarim cozunurlugu.

    KUSUR: kalibrasyonlarin tamami (D-124/D-126/D-143) Ultralytics'in
    VARSAYILAN imgsz=640'iyla kosuldu; uretim ise DOGAL uzun kenari
    kullaniyordu. Olculdu (drone n=20, 1024x576):
        imgsz=640  mpp 0,07037 -> r_gerekli 15,6 px
        DOGAL      mpp 0,07392 -> r_gerekli 14,9 px   (%5,1 · EMNIYETSIZ yon)
    Cozunurluk artik `ARAC_OLCEK_IMGSZ` ile SABITTIR.
    """

    def test_olcek_yolu_cozunurlugu_SABIT(self):
        from arac_maskesi import ARAC_OLCEK_IMGSZ, arac_olcek_kenari
        gorulen = []

        class _Kaydeden(_SahteOBB):
            def predict(self, bgr, imgsz=None, conf=None, verbose=False):
                gorulen.append(imgsz)
                return super().predict(bgr, imgsz=imgsz, conf=conf,
                                       verbose=verbose)

        arac_olcek_kenari(_kare(), _Kaydeden(ARAC_YETERLI))   # 1024x576
        self.assertEqual(gorulen, [ARAC_OLCEK_IMGSZ],
                         "uzun kenari tavandan BUYUK kare tavanda kosmali")

    def test_KUCUK_kare_BUYUTULMEZ(self):
        """Tavan hedef degil SINIRDIR: 512'lik kare 640'a cikarilmaz.

        Olculdu: 640'a sabitlenince `test/road_233.jpg` (512x512) buyutulup
        3 arac bulundu ve ALAN DISI bir karede ROTA uretildi (0 -> 1)."""
        from arac_maskesi import ARAC_OLCEK_IMGSZ, arac_olcek_kenari
        gorulen = []

        class _Kaydeden(_SahteOBB):
            def predict(self, bgr, imgsz=None, conf=None, verbose=False):
                gorulen.append(imgsz)
                return super().predict(bgr, imgsz=imgsz, conf=conf,
                                       verbose=verbose)

        kucuk = np.zeros((512, 512, 3), np.uint8)
        arac_olcek_kenari(kucuk, _Kaydeden(ARAC_YETERLI))
        self.assertEqual(gorulen, [512])
        self.assertLess(gorulen[0], ARAC_OLCEK_IMGSZ)

    def test_uretim_yolu_da_ayni_cozunurlugu_kullanir(self):
        """Sozlesme fonksiyonu degil, URETIMIN cagirdigi yol sinanir."""
        from arac_maskesi import ARAC_OLCEK_IMGSZ
        gorulen = []

        class _Kaydeden(_SahteOBB):
            def predict(self, bgr, imgsz=None, conf=None, verbose=False):
                gorulen.append(imgsz)
                return super().predict(bgr, imgsz=imgsz, conf=conf,
                                       verbose=verbose)

        kare_olcek_kahini(None, None, ICERIK, bgr=_kare(),
                          arac_modeli=_Kaydeden(ARAC_YETERLI))
        self.assertEqual(gorulen, [ARAC_OLCEK_IMGSZ])


class MukerrerKutuTests(unittest.TestCase):
    """T89 · bagimsiz denetim bulgusu 4 — ayni arac IKI SINIFTA sayilmasin.

    Ultralytics NMS'i SINIF FARKINDADIR; bir arac `small vehicle` ve
    `large vehicle` olarak IKI kutu birden birakabilir. Olculdu: drone 1137
    kutuda 3 cift, kompozit 685'te 2 cift — BESI DE farkli sinifta, mekanizma
    dogrulandi. Oran kucuk ama TEHLIKELI DURUM esik civaridir:
    2 gercek arac + 1 mukerrer = 3 ile esik HAKSIZ gecilir.
    """

    def test_ustuste_kutular_TEK_sayilir_ve_esik_HAKSIZ_gecilmez(self):
        from arac_maskesi import arac_olcek_kenari

        class _Ustuste(_SahteOBB):
            """Ayni konumda ust uste kutular: fiziksel olarak TEK arac."""

            def predict(self, bgr, imgsz=None, conf=None, verbose=False):
                import types
                n = len(self._kisa)

                class _T:
                    def __init__(self, d):
                        self._d = np.asarray(d, dtype=np.float32)

                    def cpu(self):
                        return self

                    def numpy(self):
                        return self._d

                xywhr = np.zeros((n, 5), dtype=np.float32)
                for i, k in enumerate(self._kisa):
                    # AYNI merkez, ayni boyut -> IoU = 1
                    xywhr[i] = (100.0, 100.0, k * 2.5, k, 0.0)
                return [types.SimpleNamespace(obb=types.SimpleNamespace(
                    cls=_T(np.zeros(n)), xywhr=_T(xywhr), xyxyxyxy=None))]

        kenar, n, sebep = arac_olcek_kenari(
            _kare(), _Ustuste([ARAC_KISA_KENAR_PX] * (ARAC_ASGARI_SAYI + 2)))
        self.assertEqual(n, 1, f"ust uste kutular TEK sayilmali (sebep: {sebep})")
        self.assertIsNone(kenar, "tek aracla olcek URETILMEMELI")

    def test_AYRI_konumdaki_araclar_ELENMEZ(self):
        """Eleme yalnizca ORTUSEN kutulari kaldirmali; gercek araclari DEGIL."""
        from arac_maskesi import arac_olcek_kenari
        kenar, n, _s = arac_olcek_kenari(_kare(), _SahteOBB(ARAC_YETERLI))
        self.assertEqual(n, ARAC_ASGARI_SAYI)
        self.assertIsNotNone(kenar)


if __name__ == "__main__":
    unittest.main(verbosity=2)
