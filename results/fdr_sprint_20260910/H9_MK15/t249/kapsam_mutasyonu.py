r"""T250 (çürütücü KUSUR 2) — geri kazanılan kapsam noktası GERÇEKTEN ÖLÇÜYOR mu?

Kapsam noktası "sağlam üründe yeşil koşar"; yeşil koşması tek başına onun bir
şey ölçtüğünü KANITLAMAZ. Bu betik, YALNIZ GENİŞ TUVALDE görünen sentetik bir
ürün kusuru enjekte eder (ana haritada tuval >= 1000 px genişse ikinci, sahte
bir "ROTA YOK — ..." metni çizilir) ve iki test kurgusunu karşılaştırır:

  YENI  = HEAD'in `_h2c`i — `_ana_denetle` ÖNCE doğal tuvalde, SONRA çivilenmiş
          tuvalde koşar.                                   → beklenen KIRMIZI
  ESKI  = RED edilen hâl — çivileme `_ana_denetle`den ÖNCE; ölçüm YALNIZ
          çivilenmiş 945x630'da.                           → beklenen YESIL

ESKI'nin yeşil kalması, daralan kapsamın gerçek bir kör nokta olduğunun
ölçümüdür; YENI'nin kırmızıya dönmesi o noktanın geri kazanıldığının ölçümüdür.

Ürün kaynağı DEĞİŞTİRİLMEZ: enjeksiyon süreç içinde, yalnız bu betiğin
koşumunda, `yks_gui.YksArayuz._harita_ciz` sarmalanarak yapılır.

Kullanım (süreç DPI farkındalığı AÇIK = tam süitin durumu):
  O:\navitas-local-train\venv\Scripts\python.exe -X utf8 -B \
      results/fdr_sprint_20260910/H9_MK15/t249/kapsam_mutasyonu.py
"""
from __future__ import annotations

import ctypes
import sys
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(KOK))
sys.path.insert(0, str(KOK / "tests"))

GENIS_ESIK = 1000


def enjekte(yks_gui):
    """Ana haritada tuval >= GENIS_ESIK ise SAHTE ikinci ROTA YOK metni çiz."""
    gercek = yks_gui.YksArayuz._harita_ciz

    def sarmal(self, tuval=None):
        sonuc = gercek(self, tuval)
        c = tuval if tuval is not None else getattr(self, "harita", None)
        if c is None or c is not getattr(self, "harita", None):
            return sonuc
        if c.winfo_width() < GENIS_ESIK or not getattr(self, "rota_yok", None):
            return sonuc
        c.create_text(8, 8, anchor="nw", fill=yks_gui.METIN,
                      text="ROTA YOK — SENTETIK KUSUR (kapsam mutasyonu)")
        return sonuc

    yks_gui.YksArayuz._harita_ciz = sarmal


def main():
    print("[dpi] SetProcessDpiAwareness(1) ->",
          ctypes.windll.shcore.SetProcessDpiAwareness(1), flush=True)
    import test_yks_mk15_hakem_ekrani as T
    enjekte(T.yks_gui)

    class YENI(T.H2c_EtiketCakismasi):
        def test_H2c_olcek_1_5_hakem_ekrani(self):
            self._h2c(1.5)

    class ESKI(T.H2c_EtiketCakismasi):
        """RED edilen hâl: çivileme `_ana_denetle`den ÖNCE, tek yüzey."""

        def _h2c(self, olcek):
            self._olcekli_kur(olcek)
            seq = T.SEQ + 100
            for yol in (1, 2, 3):
                seq += 1
                self._mesaj_ver(dict(T.ROTA, seq=seq, road=yol,
                                     label=T.yks_gui.ROAD_LABEL[yol]))
            self._mesaj_ver(dict(T.YOK_ROTA, seq=seq + 2, detay=T.UZUN_DETAY))
            self.app.gorunum("harita")
            self._ana_tuvali_civile(olcek)
            self._ana_denetle("no_route_uzun")
            self._mesaj_ver(dict(T.YOK_ROTA, seq=seq + 3))
            self._ana_denetle("no_route")

        def test_H2c_olcek_1_5_hakem_ekrani(self):
            self._h2c(1.5)

    beklenen = {"YENI": False, "ESKI": True}
    gercek = {}
    for ad, sinif in (("YENI", YENI), ("ESKI", ESKI)):
        print(f"\n===== {ad} =====", flush=True)
        takim = unittest.TestLoader().loadTestsFromName(
            "test_H2c_olcek_1_5_hakem_ekrani", sinif)
        sonuc = unittest.TextTestRunner(verbosity=2).run(takim)
        gercek[ad] = sonuc.wasSuccessful()
        print(f"[{ad}] wasSuccessful={sonuc.wasSuccessful()} "
              f"(beklenen {beklenen[ad]})", flush=True)

    print("\n== KAPSAM MUTASYONU OZETI ==", flush=True)
    for ad in ("YENI", "ESKI"):
        d = "YESIL" if gercek[ad] else "KIRMIZI"
        b = "YESIL" if beklenen[ad] else "KIRMIZI"
        print(f"  {ad}: gercek={d} beklenen={b} "
              f"{'TUTTU' if gercek[ad] == beklenen[ad] else 'TUTMADI'}",
          flush=True)
    tamam = gercek == beklenen
    print(f"KAPSAM_MUTASYON_SONUC {'GECTI' if tamam else 'DUSTU'}", flush=True)
    return 0 if tamam else 1


if __name__ == "__main__":
    raise SystemExit(main())
