"""T201 — SAHA KAMERA YOLU KAREYI AYNALAMAZ. Kanit: REVIEW_LOG D-349.

🔴 NEDEN VAR. `run_camera` icinde aciklamasiz bir `cv2.flip(frame, 1)` vardi
(projenin ILK commit'inden). Bu SAHA YOLUDUR: `jetson_paket/kod/` icinde de
var ve CONTRACTS izlenebilirlik tablosu satir 1 onu uretim kamera yolu ilan
ediyor. Kareyi aynalamak SOL ile SAGI takas eder; OLCULDU: acik yol 1 ya da
3 olan 16 karenin 15'i (%93,8) takas oluyordu. Sartname SS2.1 uyarinca
yanlis guzergah = 0 PUAN.

Hicbir kapi bunu yakalamamisti cunku kabul zincirinin TAMAMI `analyze_path`i
DOGRUDAN cagiriyor; hicbiri `run_camera` dongusunden gecmiyor.

BU DOSYA IKI SEYI AYRI AYRI SINAR:
  1. YAPI  — `run_camera` govdesinde kare aynalamasi YOK (mutasyonla sinanir).
  2. ETKI  — aynalama ONEMLIDIR: asimetrik bir zemin maskesi aynalandiginda
             uretim karar yolu BASKA serit yayinlar. Bu, 1. testin bos kapi
             olmadigini kanitlar. Model YUKLENMEZ (maske dogrudan kurulur).
"""
import re
import sys
import unittest
from pathlib import Path

import numpy as np

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "codes"))

from rpi_inference import analyze_path  # noqa: E402

KAYNAK = (KOK / "codes" / "rpi_inference.py").read_text(encoding="utf-8")
PAKET = KOK / "jetson_paket" / "kod" / "rpi_inference.py"


def _run_camera_govdesi(metin: str) -> str:
    i = metin.index("def run_camera(")
    j = metin.find("\ndef ", i + 10)
    return metin[i:j if j > 0 else len(metin)]


class RunCameraAynalamaz(unittest.TestCase):
    def test_govde_AYRISTIRILABILIYOR(self):
        """Capa: govde bulunamazsa asagidaki testler BOSA doner."""
        self.assertIn("def run_camera(", KAYNAK)
        self.assertGreater(len(_run_camera_govdesi(KAYNAK)), 400)

    def test_KARE_AYNALANMIYOR(self):
        g = _run_camera_govdesi(KAYNAK)
        kod = "\n".join(s for s in g.splitlines()
                        if not s.lstrip().startswith("#"))
        self.assertNotRegex(
            kod, r"cv2\.flip\s*\(\s*frame",
            "run_camera kareyi AYNALIYOR — D-349: sol/sag takas olur, "
            "SS2.1 uyarinca yanlis guzergah = 0 PUAN")

    def test_MUTASYON_flip_geri_gelirse_DUSER(self):
        g = _run_camera_govdesi(KAYNAK)
        mutant = g.replace("        sq, small, icerik = _preprocess(frame)",
                           "        frame = cv2.flip(frame, 1)\n"
                           "        sq, small, icerik = _preprocess(frame)", 1)
        self.assertNotEqual(g, mutant, "mutasyon uygulanamadi")
        kod = "\n".join(s for s in mutant.splitlines()
                        if not s.lstrip().startswith("#"))
        self.assertRegex(kod, r"cv2\.flip\s*\(\s*frame",
                         "flip geri konuldugu hâlde kapi gormuyor — BOS KAPI")

    def test_JETSON_PAKETI_de_aynalamaz(self):
        """Saha paketi ayni kusuru tasiyamaz (D-304 kalibi)."""
        if not PAKET.is_file():
            self.skipTest("jetson_paket/kod/rpi_inference.py yok")
        g = _run_camera_govdesi(PAKET.read_text(encoding="utf-8"))
        kod = "\n".join(s for s in g.splitlines()
                        if not s.lstrip().startswith("#"))
        self.assertNotRegex(kod, r"cv2\.flip\s*\(\s*frame",
                            "JETSON PAKETI kareyi aynaliyor (D-349)")


class AynalamaOnemlidir(unittest.TestCase):
    """1. sinifin BOS KAPI olmadigini kanitlar: model YUKLENMEZ."""

    @staticmethod
    def _asimetrik_zemin(n=512):
        """Yalniz SOL koridoru acik, sag koridoru KAPALI bir zemin maskesi."""
        z = np.zeros((n, n), np.uint8)
        # ust ve alt bant boyunca uc dusey koridor; yalniz SOLDAKI ustten alta
        # kesintisiz gider.
        for x0, x1, acik in ((int(n*0.10), int(n*0.30), True),
                             (int(n*0.40), int(n*0.60), False),
                             (int(n*0.70), int(n*0.90), False)):
            z[int(n*0.05):int(n*0.95), x0:x1] = 1
            if not acik:                      # ortadan kesilir -> gecilemez
                z[int(n*0.45):int(n*0.55), x0:x1] = 0
        z[int(n*0.05):int(n*0.12), int(n*0.10):int(n*0.90)] = 1   # ust bant
        z[int(n*0.88):int(n*0.95), int(n*0.10):int(n*0.90)] = 1   # alt bant
        return z

    def test_aynalanan_maske_BASKA_serit_yayinlar(self):
        z = self._asimetrik_zemin()
        ic = (0, 0, z.shape[1], z.shape[0])
        mpp = 50.0 / z.shape[1]
        a = analyze_path(z, icerik=ic, mpp=mpp)[0]
        b = analyze_path(np.ascontiguousarray(z[:, ::-1]), icerik=ic, mpp=mpp)[0]
        self.assertIsNotNone(a, "on kosul: ozgun maskede rota URETILMELI")
        self.assertIsNotNone(b, "on kosul: aynalanmis maskede rota URETILMELI")
        self.assertNotEqual(
            a, b,
            "aynalama seridi DEGISTIRMIYOR — bu test ayirt etmiyor demektir; "
            "maske yeterince asimetrik degil, duzeltilmeli (bos kapi yasagi)")


if __name__ == "__main__":
    unittest.main()
