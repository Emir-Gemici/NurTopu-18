"""S9 KAPISI: hakem gunlugunun yazdigi kunye, IHA algisinin YUKLEDIGI modele mi ait?

Kusur (S9): `simulation/scripts/iha_perceive.py` varsayilan agirligi
`models/navitas_seg_v2_best.pt` diye CIPLAK yaziyordu (11 Temmuz, diskte VAR);
`simulation/scripts/hakem_log.py::_model_kunyesi` ise kunyeyi
`config/model_registry.json`'dan (v35) turetiyordu. Yani hakem, `detections.json`'i
URETMEYEN modelin adini ve sha'sini okuyordu — kod hatasi degil, KANIT BUTUNLUGU
hatasi (D-21 ailesi; D-58/D-60 iraksama sinifi: bir uc cevrilir, digeri unutulur).

Bu paket iki ucu TEK KAYNAGA baglar ve kaymayi mekanik olarak yakalar:
  1. `iha_perceive.DEFAULT_MODEL`   — algi betiginin yukledigi agirlik
  2. `hakem_log.MODEL_NAME`          — hakem gunlugune yazilan kunye
  3. `yks_gui.YksArayuz.ALGI_MODEL_DOSYA` — hakem ekraninin yukledigi agirlik (T58)
Ucunun de kaynagi `config/model_registry.json` etkin profilinin `path` alanidir.
Gecici defter kopyasinda `model_id`/`path` cevrilince 1 ve 2 BIRLIKTE donmelidir.

Model AGIRLIGI YUKLENMEZ (ultralytics/torch cagrilmaz); yalniz yol ve ad kimligi
sinanir, kapi GPU'suz ve saniyeler icinde kosar.

POZITIF KONTROL (madde 3, kosuldu): `DEFAULT_MODEL = ROOT/"models"/"navitas_seg_v2_best.pt"`
geri konunca `test_algi_ile_gunluk_AYNI_agirligi_soyluyor` ve
`test_varsayilan_CIPLAK_yazilmiyor` DUSER.
"""

from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
for _alt in ("codes", "comms", "simulation/scripts"):
    if str(KOK / _alt) not in sys.path:
        sys.path.insert(0, str(KOK / _alt))

import hakem_log  # noqa: E402
import iha_perceive  # noqa: E402
import yks_gui  # noqa: E402

DEFTER = KOK / "config" / "model_registry.json"
IHA_PERCEIVE_KAYNAK = KOK / "simulation" / "scripts" / "iha_perceive.py"
SINAMA_ADI = "navitas_seg_v999_sinama.pt"


def _etkin_profil_yolu(defter: Path) -> str:
    veri = json.loads(defter.read_text(encoding="utf-8"))
    return veri["profiles"][veri["default_profile"]]["path"]


def _gecici_defter(dizin: str, **profil_degisikligi) -> Path:
    """Gercek defterin kopyasi; etkin profilde verilen alanlar cevrilir."""
    veri = json.loads(DEFTER.read_text(encoding="utf-8"))
    veri["profiles"][veri["default_profile"]].update(profil_degisikligi)
    kopya = Path(dizin) / "model_registry.json"
    kopya.write_text(json.dumps(veri), encoding="utf-8")
    return kopya


class AlgiIleGunlukTekKaynakTests(unittest.TestCase):

    def test_algi_ile_gunluk_AYNI_agirligi_soyluyor(self):
        """Gunlukteki ad == algi betiginin yukledigi dosya == defterin etkin `path`i."""
        defter_adi = Path(_etkin_profil_yolu(DEFTER)).name
        self.assertEqual(iha_perceive.DEFAULT_MODEL.name, defter_adi,
                         "iha_perceive varsayilani kayit defterinden GELMIYOR")
        self.assertEqual(hakem_log.MODEL_NAME, iha_perceive.DEFAULT_MODEL.name,
                         "hakem gunlugu, algi betiginin yuklemedigi bir modeli yaziyor (S9)")
        # T58 ucu: hakem EKRANI da ayni defteri okur — uc uc tek ad.
        self.assertEqual(yks_gui.YksArayuz.ALGI_MODEL_DOSYA, hakem_log.MODEL_NAME)

    def test_defter_cevrilince_IKISI_BIRLIKTE_doner(self):
        """Gecici kopyada model_id+path cevrilir; algi yolu ve gunluk kunyesi birlikte degisir."""
        with tempfile.TemporaryDirectory() as dizin:
            kopya = _gecici_defter(dizin, model_id="navitas-seg-v999-sinama",
                                   path=f"models/{SINAMA_ADI}")
            algi_yolu = iha_perceive.varsayilan_model_yolu(kopya)
            ad, _imgsz, sha8 = hakem_log._model_kunyesi(kopya)
        self.assertEqual(algi_yolu.name, SINAMA_ADI)
        self.assertEqual(ad, algi_yolu.name, "gunluk kunyesi algi yolunu izlemiyor")
        self.assertEqual(algi_yolu, KOK / "models" / SINAMA_ADI,
                         "yol depo kokune goreli cozulmeli (model_registry.resolve_model deseni)")
        # Sinama agirligi diskte YOK: sha UYDURULMAZ, '?' yazilir.
        self.assertFalse(algi_yolu.exists())
        self.assertEqual(sha8, "?")

    def test_gercek_defterde_kunye_sha_defterle_UYUSUYOR(self):
        """Agirlik diskteyse gunlugun sha8'i defterin sha256 on ekidir; yoksa '?' (uydurma yok)."""
        veri = json.loads(DEFTER.read_text(encoding="utf-8"))
        profil = veri["profiles"][veri["default_profile"]]
        if not iha_perceive.DEFAULT_MODEL.exists():
            self.assertEqual(hakem_log.MODEL_SHA8, "?")
            self.skipTest(f"agirlik diskte yok ({iha_perceive.DEFAULT_MODEL.name}); sha kiyasi OLCULEMEDI")
        self.assertEqual(hakem_log.MODEL_SHA8, profil["sha256"][:8])

    def test_varsayilan_CIPLAK_yazilmiyor(self):
        """Kaynakta `DEFAULT_MODEL = ...navitas_seg_vN_best.pt` gibi ciplak ad OLMAMALI (madde 16)."""
        kaynak = IHA_PERCEIVE_KAYNAK.read_text(encoding="utf-8")
        atama = re.search(r"^DEFAULT_MODEL\s*=\s*(.+)$", kaynak, re.M)
        self.assertIsNotNone(atama, "DEFAULT_MODEL atamasi bulunamadi")
        self.assertTrue(atama.group(1).startswith("varsayilan_model_yolu("),
                        f"DEFAULT_MODEL kayit defterinden turetilmiyor: {atama.group(0)!r}")
        # Kod satirlarinda (docstring/yorum disinda) surumlu agirlik adi gecmez.
        kod_satirlari = [s for s in kaynak.splitlines()
                         if s.strip() and not s.lstrip().startswith("#")]
        ciplak = [s for s in kod_satirlari
                  if re.search(r"[\"']navitas_seg_v\d+[^\"']*\.pt[\"']", s)]
        self.assertEqual(ciplak, [], f"ciplak agirlik adi: {ciplak}")

    def test_defter_okunamazsa_FAIL_CLOSED(self):
        """Bozuk/eksik defter: ad UYDURULMAZ, iki uc da yukselir (eski gunluk 'BILINMIYOR' yutuyordu)."""
        with tempfile.TemporaryDirectory() as dizin:
            bozuk = Path(dizin) / "model_registry.json"
            bozuk.write_text("{bozuk", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                iha_perceive.varsayilan_model_yolu(bozuk)
            with self.assertRaises(RuntimeError):
                hakem_log._model_kunyesi(bozuk)
            with self.assertRaises(RuntimeError):
                iha_perceive.varsayilan_model_yolu(Path(dizin) / "yok.json")
            # Etkin profil `.pt` gostermiyorsa da uydurulmaz.
            kopya = _gecici_defter(dizin, path="models/bir_dizin_ncnn_model")
            with self.assertRaises(RuntimeError):
                iha_perceive.varsayilan_model_yolu(kopya)


if __name__ == "__main__":
    unittest.main()
