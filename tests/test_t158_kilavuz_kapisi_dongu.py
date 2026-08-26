"""T158 KAPISI (ON_KAYIT SS27 · REVIEW_LOG D-304): kilavuz kapisi KABUK
DONGUSUYLE kurulan model adlarini goruyor mu?

KUSUR (D-296 SS4, curutucu olctu): `JETSON_KILAVUZ.md` SS5 "Karar kiyasi" blogu
model adini `for M in v21 v17 v20` + `navitas_seg_${M}_best.pt` diye kuruyor.
  1. Dosya adi deseni `${M}` bicimine takilmiyordu -> dongu listesindeki
     surumler kapiya GORUNMEZDI.
  2. `--imgsz` istisnasinin kancasi "blokta URETIM adi gecerse duser" diyordu;
     uretim adi bu blokta HICBIR ZAMAN tam dosya adi olarak gecmez -> kanca
     ates alamiyordu, istisna fiilen KOSULSUZDU (bos kanca).

BOS KAPI YASAGI (TEST_SPECS SS4.1): kapinin bugun GECMESI yetmez. Uc mutasyon
ayri ayri kosulur ve UCU DE kapiyi DUSURMELIDIR.
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
KILAVUZ = KOK / "JETSON_KILAVUZ.md"


def _kapi_modulu():
    spec = importlib.util.spec_from_file_location(
        "_t158_kapi", KOK / "tests" / "test_uretim_modeli_hizasi.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class DonguTaramasi(unittest.TestCase):

    def setUp(self):
        self.m = _kapi_modulu()
        self.metin = KILAVUZ.read_text(encoding="utf-8")

    def test_dongu_gorunur(self):
        dongular = self.m._dongu_surumleri(self.metin)
        self.assertTrue(dongular, "kabuk dongusu hic gorulmedi (T158/1)")
        surumler = {s for _n, _s, _b, sur in dongular for s in sur}
        self.assertIn("v21", surumler)
        self.assertIn("v17", surumler)

    def test_model_adinda_kullanilmayan_dongu_SAYILMAZ(self):
        """Rastgele bir kabuk dongusu surum denetimine girmemeli."""
        sahte = "```bash\nfor X in v98 v99; do\n  echo ${X}\ndone\n```\n"
        self.assertEqual([], self.m._dongu_surumleri(sahte))


class Mutasyonlar(unittest.TestCase):
    """Kilavuz KOPYASI bozulur; kapi DUSMELI."""

    def setUp(self):
        self.m = _kapi_modulu()

    def _sapma_sayisi(self, metin: str, uretim: str):
        with tempfile.TemporaryDirectory() as td:
            yol = Path(td) / "JETSON_KILAVUZ.md"
            yol.write_text(metin, encoding="utf-8")
            return [x for x in self.m._sapmalar(yol, uretim) if x[3] is None]

    def _uretim_surumu(self):
        sys.path.insert(0, str(KOK / "comms"))
        try:
            import yks_gui
            return self.m._surum(yks_gui.YksArayuz.ALGI_MODEL_DOSYA)
        finally:
            sys.path.pop(0)

    def test_TABAN_bugunku_kilavuz_temiz(self):
        uretim = self._uretim_surumu()
        self.assertEqual([], self._sapma_sayisi(
            KILAVUZ.read_text(encoding="utf-8"), uretim),
            "bugunku kilavuz zaten kirmizi — mutasyon kaniti anlamsiz olur")

    def test_MUTASYON_A_uretim_surumu_donguye_girerse_DUSER(self):
        uretim = self._uretim_surumu()
        metin = KILAVUZ.read_text(encoding="utf-8").replace(
            "for M in v21 v17 v20; do", f"for M in v21 v17 v20 {uretim}; do", 1)
        self.assertNotIn("for M in v21 v17 v20; do", metin)
        sapmalar = self._sapma_sayisi(metin, uretim)
        self.assertTrue(sapmalar,
                        "URETIM surumu dongu listesine girdi ama kapi YESIL "
                        "kaldi — istisna hâlâ bos kanca (T158/2)")

    def test_MUTASYON_B_defterde_olmayan_surum_DUSER(self):
        uretim = self._uretim_surumu()
        metin = KILAVUZ.read_text(encoding="utf-8").replace(
            "for M in v21 v17 v20; do", "for M in v21 v17 v99; do", 1)
        sapmalar = self._sapma_sayisi(metin, uretim)
        self.assertTrue(any(x[2] == "v99" for x in sapmalar),
                        "dongu listesindeki BILINMEYEN surum yakalanmadi")

    def test_MUTASYON_C_imgsz_512_yapilirsa_DUSER(self):
        """Tarihsel kiyas kendi doneminin 640'inda kosar; 512 celiskidir."""
        uretim = self._uretim_surumu()
        uretim_ad = f"navitas_seg_{uretim}"
        metin = KILAVUZ.read_text(encoding="utf-8").replace(
            "--imgsz 640 --isinma 5 --tekrar 40 --conf 0.25 --cihaz 0",
            "--imgsz 512 --isinma 5 --tekrar 40 --conf 0.25 --cihaz 0", 1)
        bulundu = False
        for _no, komut, baslik in self.m._mantiksal_komutlar(metin):
            if "Karar kıyası" not in baslik or "--imgsz 512" not in komut:
                continue
            bulundu = True
            ist = self.m._imgsz_istisna_bul(
                baslik, komut, 512, uretim_ad,
                self.m._bolumun_dongu_surumleri(metin, baslik), uretim)
            self.assertIsNone(
                ist, "640 yerine 512 yazildi ama istisna hâlâ oruyor — "
                     "tarihsel kiyas kendi kaydiyla celisir")
        self.assertTrue(bulundu, "mutasyon uygulanamadi (desen bulunamadi)")


if __name__ == "__main__":
    unittest.main()
