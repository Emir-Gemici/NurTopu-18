"""T58 KAPISI: hakem ekrani ile SAHA PAKETI ayni modelde mi?

Kusur sinifi (D-58/D-60): iki uctan biri cevrilir, digeri unutulur; ekran ile
donanim SESSIZCE farkli modele duser ve hakemde gorulen karar sahada uretilmez.
Bu tam olarak `jetson_paket/models/jetson_derleme_manifest.json`'in basina geldi:
2026-08-05'ten 2026-08-13'e kadar `pc_modeli` **v17** diyordu, oysa pakette
**v21** ONNX vardi. Manifest paket icerigine BAKMIYORDU, kimse fark etmedi
(REVIEW_LOG D-83).

Bu paket dort ucu TEK KAYNAGA baglar ve kaymayi mekanik olarak yakalar:
  1. `comms/yks_gui.py` `ALGI_MODEL_DOSYA`      — hakem ekraninin yukledigi .pt
  2. `jetson_paket/models/`                      — sahaya giden dosyalar
  3. `jetson_paket/models/jetson_derleme_manifest.json` — paketin kunyesi
  4. HER IKI `JETSON_KILAVUZ.md`                 — "ASIL - bunu derle" satiri

Model AGIRLIGI YUKLENMEZ; yalniz bayt ve metin kimligi sinanir, boylece kapi
GPU'suz ve saniyeler icinde kosar.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
if str(KOK / "comms") not in sys.path:
    sys.path.insert(0, str(KOK / "comms"))

import yks_gui  # noqa: E402

PAKET = KOK / "jetson_paket" / "models"
MANIFEST = PAKET / "jetson_derleme_manifest.json"
KILAVUZLAR = (KOK / "JETSON_KILAVUZ.md", KOK / "jetson_paket" / "JETSON_KILAVUZ.md")

SURUM_DESENI = re.compile(r"navitas_seg_(v\d+)_best")

# Agirliklar `.gitignore:132` ile depo disinda tutulur (`*.pt`, `*.onnx`).
# Temiz bir klonda bayt kapilari dosya YOKLUGUNDAN duserdi — bu YANLIS sebeple
# kirmizi yanmaktir. Bayt kapilari agirlik varsa kosar; METIN kapilari
# (manifest alanlari, kilavuz `ASIL` satiri) her zaman kosar cunku o dosyalar
# depoda izlenir. Manifest `paket_icerigi` sayesinde temiz klonda bile paketin
# NE OLMASI GEREKTIGI git'te kayitlidir.
AGIRLIK_VAR = any((KOK / "models").glob("*.pt")) and any(PAKET.glob("*.pt"))
AGIRLIK_YOK_SEBEBI = ("model agirliklari diskte yok (.gitignore:132) — bayt "
                      "kapisi atlandi, metin kapilari yine kosuldu")


def _sha(yol: Path) -> str:
    ozet = hashlib.sha256()
    with open(yol, "rb") as fh:
        for blok in iter(lambda: fh.read(1 << 20), b""):
            ozet.update(blok)
    return ozet.hexdigest()


def _surum(ad: str):
    """`navitas_seg_v24_best.pt` -> `v24`. Eslesmezse None."""
    m = SURUM_DESENI.search(ad)
    return m.group(1) if m else None


def _asil_satirlari(metin: str):
    """Kilavuzda `ASIL` isaretli model satirlari."""
    return [s for s in metin.splitlines() if "ASIL" in s and "navitas_seg_" in s]


class UretimModeliKimligiTests(unittest.TestCase):
    """Ekranin yukledigi model gercekten var ve surumu okunabilir mi?"""

    @unittest.skipUnless(AGIRLIK_VAR, AGIRLIK_YOK_SEBEBI)
    def test_gui_modeli_depoda_VAR(self):
        yol = KOK / "models" / yks_gui.YksArayuz.ALGI_MODEL_DOSYA
        self.assertTrue(yol.is_file(),
                        f"hakem ekrani var olmayan modeli gosteriyor: {yol}")

    def test_gui_modelinin_surumu_OKUNABILIR(self):
        self.assertIsNotNone(
            _surum(yks_gui.YksArayuz.ALGI_MODEL_DOSYA),
            "model adi `navitas_seg_vNN_best` kalibina uymuyor; bu kapinin "
            "geri kalani surumu karsilastiramaz")


@unittest.skipUnless(AGIRLIK_VAR, AGIRLIK_YOK_SEBEBI)
class PaketHizasiTests(unittest.TestCase):
    """IRAKSAMA KAPISI — ekran ile sahaya giden dosya AYNI olmali."""

    def setUp(self):
        self.ad = yks_gui.YksArayuz.ALGI_MODEL_DOSYA
        self.surum = _surum(self.ad)

    def test_gui_modeli_PAKETTE_de_var_ve_BAYT_ESIT(self):
        depo = KOK / "models" / self.ad
        paket = PAKET / self.ad
        self.assertTrue(
            paket.is_file(),
            f"hakem ekrani {self.ad} yukluyor ama saha paketinde YOK — "
            f"ekran ile donanim farkli modele duser (D-58/D-60 sinifi)")
        self.assertEqual(_sha(depo), _sha(paket),
                         f"{self.ad} depo ve paket kopyalari FARKLI")

    def test_paketteki_ONNX_ayni_SURUMDEN(self):
        onnxler = [p for p in PAKET.glob("*.onnx")
                   if _surum(p.name) == self.surum]
        self.assertTrue(
            onnxler,
            f"pakette {self.surum} ONNX'i yok; Jetson eski surumu derler")

    def test_paketteki_ONNX_depodan_TURETILMIS(self):
        """Elle duzenlenmis/yeniden uretilmis ONNX yakalanir."""
        depo_ozetleri = {_sha(p) for p in (KOK / "models").glob("*.onnx")}
        for p in KOK.glob("results/onnx_export_*/**/*.onnx"):
            depo_ozetleri.add(_sha(p))
        for p in PAKET.glob("*.onnx"):
            if _surum(p.name) != self.surum:
                continue
            with self.subTest(onnx=p.name):
                self.assertIn(
                    _sha(p), depo_ozetleri,
                    f"{p.name} depodaki hicbir ONNX ile ayni degil")


class ManifestBayATLIGI_Tests(unittest.TestCase):
    """Manifest paketin KENDISINI tarif ediyor mu — yoksa eski kosuyu mu?"""

    def setUp(self):
        self.mf = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.surum = _surum(yks_gui.YksArayuz.ALGI_MODEL_DOSYA)

    def test_manifest_URETIM_surumunu_gosteriyor(self):
        for alan in ("pc_modeli", "asil_model", "asil_model_pt"):
            with self.subTest(alan=alan):
                self.assertEqual(
                    self.surum, _surum(str(self.mf.get(alan, ""))),
                    f"manifest `{alan}` uretim surumu {self.surum} degil — "
                    f"2026-08-05 bayatliginin tekrari")

    def test_manifest_paket_icerigini_TASIYOR(self):
        self.assertTrue(self.mf.get("paket_icerigi"),
                        "manifest paket icerigini listelemiyor; bayatlik "
                        "yeniden GORUNMEZ olur")

    @unittest.skipUnless(AGIRLIK_VAR, AGIRLIK_YOK_SEBEBI)
    def test_manifest_ozetleri_GERCEK_dosyalarla_ESLESIYOR(self):
        for kayit in self.mf["paket_icerigi"]:
            p = PAKET / kayit["dosya"]
            with self.subTest(dosya=kayit["dosya"]):
                self.assertTrue(p.is_file(), "manifestte var, pakette YOK")
                self.assertEqual(kayit["bayt"], p.stat().st_size)
                self.assertEqual(kayit["sha256"], _sha(p))

    @unittest.skipUnless(AGIRLIK_VAR, AGIRLIK_YOK_SEBEBI)
    def test_manifest_DISINDA_dosya_kalmamis(self):
        listelenen = {k["dosya"] for k in self.mf["paket_icerigi"]}
        artik = sorted(p.name for p in PAKET.iterdir()
                       if p.name != MANIFEST.name and p.name not in listelenen)
        self.assertEqual([], artik,
                         f"manifest bu dosyalari tarif etmiyor: {artik}")


class KilavuzHizasiTests(unittest.TestCase):
    """Sahadaki insan hangi dosyayi derleyecek — kilavuz ne diyor?"""

    def setUp(self):
        self.surum = _surum(yks_gui.YksArayuz.ALGI_MODEL_DOSYA)

    def test_IKI_kilavuz_da_ASIL_satiri_TASIYOR(self):
        for k in KILAVUZLAR:
            with self.subTest(kilavuz=k.name, yol=str(k.parent.name)):
                self.assertTrue(k.is_file())
                self.assertTrue(_asil_satirlari(k.read_text(encoding="utf-8")),
                                "kilavuzda `ASIL` isaretli model satiri yok")

    def test_ASIL_satiri_URETIM_surumunu_gosteriyor(self):
        for k in KILAVUZLAR:
            for satir in _asil_satirlari(k.read_text(encoding="utf-8")):
                with self.subTest(kilavuz=k.parent.name, satir=satir.strip()):
                    self.assertEqual(
                        self.surum, _surum(satir),
                        "kilavuz baska surumu ASIL gosteriyor; sahadaki kisi "
                        "hakem ekraninda gorulmeyen modeli derler")

    def test_derleme_komutu_URETIM_surumunu_kullaniyor(self):
        """`yolo export ... format=engine` satiri asil surumu gostermeli."""
        for k in KILAVUZLAR:
            satirlar = [s for s in k.read_text(encoding="utf-8").splitlines()
                        if "format=engine" in s and "navitas_seg_" in s]
            with self.subTest(kilavuz=k.parent.name):
                self.assertTrue(satirlar, "engine derleme komutu bulunamadi")
                self.assertIn(
                    self.surum, [_surum(s) for s in satirlar],
                    f"hicbir derleme komutu {self.surum} kullanmiyor")


if __name__ == "__main__":
    unittest.main(verbosity=2)
