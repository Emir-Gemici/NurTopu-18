#!/usr/bin/env python3
"""NEDEN: Yarım kalan kayıtların hakem özetinde başarıya dönüşmesini engeller."""

import sys
import tempfile
import unittest
from pathlib import Path


SIM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SIM / "scripts"))

import hakem_log


class _BellekLogu:
    def __init__(self):
        self.satirlar = []

    def __call__(self, tag, msg):
        self.satirlar.append(f"{tag} {msg}")

    def raw(self, msg):
        self.satirlar.append(msg)

    @property
    def metin(self):
        return "\n".join(self.satirlar)


class HakemDurustlukTest(unittest.TestCase):
    def test_duvar_siniri_basari_ve_ulasildi_yazmaz(self):
        with tempfile.TemporaryDirectory() as tmp:
            kok = Path(tmp)
            level_dir = kok / "iha_scan_kolay"
            level_dir.mkdir()
            (level_dir / "meta.txt").write_text(
                "LEVEL=kolay\n"
                "MAP=1\n"
                "SEBEP=DUVAR_SINIRI\n"
                "SON_DURUM=YOK\n"
                "SIM_T=64\n"
                "RECORD_SECONDS=144\n",
                encoding="utf-8",
            )
            durum = hakem_log._kayit_sonu_for_level(kok / "detections.json", "kolay")

        log = _BellekLogu()
        sonuc = hakem_log.run_level(
            "kolay",
            log,
            det={"road": 1, "conf": 0.99, "rota": [[0, 0], [1, 1]]},
            kayit_sonu=durum,
        )

        self.assertFalse(sonuc)
        self.assertIn(
            "SONUÇ: ✗ KAYIT YARIDA KESİLDİ (sim 64s / hedef 144s)",
            log.metin,
        )
        self.assertNotIn("HEDEF BÖLGE (HB) ULAŞILDI", log.metin)
        self.assertNotIn("SONUÇ: ✓ BAŞARILI", log.metin)

    def test_terminal_rota_yok_da_hb_varisi_sayilmaz(self):
        log = _BellekLogu()
        sonuc = hakem_log.run_level(
            "kolay",
            log,
            det={"road": 1, "conf": 0.99, "rota": [[0, 0], [1, 1]]},
            kayit_sonu={
                "sebep": "GOREV_TAMAMLANDI",
                "son_durum": "ROTA_YOK",
                "sim_t": "48",
                "record_seconds": "144",
            },
        )

        self.assertFalse(sonuc)
        self.assertIn("SONUÇ: ✗ GÖREV BAŞARISIZ", log.metin)
        self.assertNotIn("HEDEF BÖLGE (HB) ULAŞILDI", log.metin)
        self.assertNotIn("SONUÇ: ✓ BAŞARILI", log.metin)


if __name__ == "__main__":
    unittest.main()
