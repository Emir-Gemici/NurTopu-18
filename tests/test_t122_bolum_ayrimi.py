"""T122 KAPISI: train/val ayrimi KAYNAK BAZINDA olmali (grup ayrimi).

KUSUR (D-233, olculdu): `bolum_sec()` anahtari `cesit`i de iceriyordu, yani
AYNI kaynak karenin varyantlari farkli bolumlere dusebiliyordu. Uretilmis
kumede olculdu:
    56 kaynagin 41'i HEM train HEM val'de
    val ornegi 55 · kaynagi egitimde de olan 55 (%100) · TEMIZ val: 0
Varyantlar ayni kareden uretilir (piksel farki %0,1-0,4 — olculdu), yani o
bilesenin dogrulama kumesi fiilen egitim verisinin ikiziydi ve val metrigi
GENELLEME degil EZBER olcuyordu.

Bu kapi iki seyi birden kilitler:
  1. FONKSIYON DEGISMEZI — bir kaynagin butun varyantlari ayni bolumde.
  2. URETILMIS KUMELERIN DURUMU — manifest tasiyan her kumede kaynak-bazinda
     sizinti sayilir ve BILINEN kirli kumeler ACIKCA isaretlidir. Boylece
     "duzeltildi" sanilan bir kume sessizce kirli kalamaz.

⚠ KIRLI KUMELER YENIDEN URETILMEDI: veri sozlesmesi degisikligi mimarin
karari (AGENTS SS9.2). Kapi bu durumu SAKLAMAZ, KAYDEDER.
"""

from __future__ import annotations

import json
import sys
import unittest
from collections import defaultdict
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
if str(KOK / "scripts") not in sys.path:
    sys.path.insert(0, str(KOK / "scripts"))

from copy_paste_augmentation import bolum_sec  # noqa: E402

# Duzeltmeden ONCE uretilmis, kaynak-bazinda sizintisi OLCULMUS kumeler.
# (Yeniden uretim mimarin karari; bu liste "biliniyor ve kayitli" demektir.)
BILINEN_KIRLI = {"copy_paste_gercek"}


def _kaynak_bolumleri(manifest: Path) -> dict[str, set[str]]:
    veri = json.loads(manifest.read_text(encoding="utf-8"))
    esleme: dict[str, set[str]] = defaultdict(set)
    for o in veri.get("ornekler", []):
        if o.get("cikti") and o.get("bolum"):
            esleme[o.get("kaynak")].add(o["bolum"])
    return esleme


class FonksiyonDegismeziTests(unittest.TestCase):
    def test_ayni_kaynagin_tum_cesitleri_ayni_bolumde(self):
        for i in range(60):
            kaynak = Path(f"video_{i:02d}/frame_{i:06d}.jpg")
            bolumler = {bolum_sec(kaynak, c, 20260802, 0.15) for c in range(8)}
            self.assertEqual(
                len(bolumler), 1,
                f"{kaynak}: cesitler bolunmus -> {bolumler} (grup ayrimi bozuk)")

    def test_ayrim_hala_iki_bolum_uretiyor(self):
        """VAKUM KONTROLU: her sey train'e duserse ayrim yok demektir."""
        bolumler = {bolum_sec(Path(f"v/f_{i:04d}.jpg"), 0, 20260802, 0.15)
                    for i in range(400)}
        self.assertEqual(bolumler, {"train", "val"},
                         "ayrim tek bolum uretiyor — val kumesi olusmuyor")

    def test_tohum_degisince_ayrim_degisebilir_kaynak_grubu_BOZULMAZ(self):
        kaynak = Path("v/f_0001.jpg")
        for tohum in (1, 42, 20260802):
            bolumler = {bolum_sec(kaynak, c, tohum, 0.15) for c in range(8)}
            self.assertEqual(len(bolumler), 1, f"tohum {tohum}: grup bozuldu")

    def test_val_orani_kabaca_saglaniyor(self):
        n = 2000
        val = sum(1 for i in range(n)
                  if bolum_sec(Path(f"v/f_{i:05d}.jpg"), 0, 7, 0.15) == "val")
        self.assertTrue(0.10 * n <= val <= 0.20 * n,
                        f"val orani beklenen bandin disinda: {val}/{n}")


class UretilmisKumelerTests(unittest.TestCase):
    def test_kirlilik_durumu_KAYITLI(self):
        """Her manifestli kume ya TEMIZ ya da BILINEN_KIRLI listesinde olmali.

        Yeni bir kume sessizce kirli uretilirse bu kapi duser; kirliligi
        bilinen ve mimar kararina birakilan kume ise ACIKCA isaretlidir.
        """
        surprizler = []
        for manifest in sorted((KOK / "dataset").glob("*/manifest.json")):
            ad = manifest.parent.name
            esleme = _kaynak_bolumleri(manifest)
            if not esleme:
                continue
            sizan = [k for k, b in esleme.items() if len(b) > 1]
            if sizan and ad not in BILINEN_KIRLI:
                surprizler.append(f"{ad}: {len(sizan)}/{len(esleme)} kaynak "
                                  "HEM train HEM val'de")
        self.assertEqual(surprizler, [], "kayitsiz sizinti: " + "; ".join(surprizler))

    def test_bilinen_kirli_kume_hala_kirli_ise_liste_dogru(self):
        """BILINEN_KIRLI listesi BAYATLAMASIN: temizlenen kume listede kalmaz."""
        for ad in sorted(BILINEN_KIRLI):
            manifest = KOK / "dataset" / ad / "manifest.json"
            if not manifest.is_file():
                continue
            esleme = _kaynak_bolumleri(manifest)
            sizan = [k for k, b in esleme.items() if len(b) > 1]
            self.assertTrue(
                sizan,
                f"{ad} artik TEMIZ — BILINEN_KIRLI listesinden cikarilmali "
                "(bayat muafiyet)")


if __name__ == "__main__":
    unittest.main(verbosity=2)
