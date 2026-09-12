r"""T249 mutasyon kapısı — H2f kilidinin GERÇEKTEN neye dayandığını ölçer.

Her mutasyon GERÇEK kaynak dosyayı bayt düzeyinde bozar ve `finally` içinde
sha256 doğrulayarak aynen geri yazar (satır sonu dâhil).

Koşum yüzeyi `kos_dpi.py`dir: süreç DPI farkındalığı AÇIK (tam süitte
`test_sim_mujoco_arena` MuJoCo GL bağlamının süreç genelinde yaptığı şey;
ölçüm `dpi_izi_cikti.txt`). Beklenen 1 = KIRMIZI, 0 = YEŞİL.

Kullanım:
  O:\navitas-local-train\venv\Scripts\python.exe -X utf8 -B \
      results/fdr_sprint_20260910/H9_MK15/t249/mutasyon_t249.py
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]
CIK = Path(__file__).resolve().parent
TEST = KOK / "tests" / "test_yks_mk15_hakem_ekrani.py"
KOSUCU = CIK / "kos_dpi.py"
PY = sys.executable

# T250: `_ana_denetle` artik ONCE dogal, SONRA civilenmis tuvalde kosuyor; bu
# yuzden 'civileme geri alinir' mutasyonu artik YALNIZ civileme cagrisini
# hedefler (dogal kapsam noktasi yerinde kalir). Geri alinan hal = H2f'in
# ekrandan TUREYEN tuvalde olculmesi, yani RED oncesi master davranisi.
CIVILEME_GERI = (
    "        # ÇİVİLENMİŞ tuval: H2f kalıntı sayısı buradan hüküm verir.\n"
    "        self._ana_tuvali_civile(olcek)\n",
    "        self.assertTrue(self._pompala(self.app.harita.winfo_ismapped, 3.0))\n",
)

SABIT_UYKU_GERI = (
    "                self.assertTrue(\n"
    "                    self._pompala(lambda: c.winfo_ismapped()\n"
    "                                  and (c.winfo_width(), c.winfo_height())\n"
    "                                  == self.ANA_TUVAL[olcek], 5.0),\n"
    '                    f"ana tuval ölçüm anında {c.winfo_width()}×"\n'
    '                    f"{c.winfo_height()}, çivilenen "\n'
    '                    f"{self.ANA_TUVAL[olcek]} değil")\n',
    "                self._pompala(lambda: False, 0.2)\n",
)

MUTASYONLAR = [
    ("M0 mutasyon yok (DPI ACIK)", [], 1, 0),
    ("M1 TAM GERI ALMA: civileme yok + sabit uyku geri", 
     [CIVILEME_GERI, SABIT_UYKU_GERI], 1, 1),
    ("M2 yalniz CIVILEME geri alinir (gercek hazir kosulu kalir)",
     [CIVILEME_GERI], 1, 1),
    ("M3 yalniz SABIT UYKU geri gelir (civileme kalir)",
     [SABIT_UYKU_GERI], 1, 0),
    ("M4 mutasyon yok (DPI KAPALI, denetim)", [], 0, 0),
]


def main():
    ham = TEST.read_bytes()
    ozet = hashlib.sha256(ham).hexdigest()
    ss = "\r\n" if b"\r\n" in ham else "\n"
    sonuc = []
    for ad, degs, dpi, beklenen in MUTASYONLAR:
        metin = ham
        for eski, yeni in degs:
            e = eski.replace("\n", ss).encode("utf-8")
            y = yeni.replace("\n", ss).encode("utf-8")
            if metin.count(e) != 1:
                raise SystemExit(f"DESEN TEK DEGIL ({ad}): {metin.count(e)}\n{eski}")
            metin = metin.replace(e, y, 1)
        try:
            if metin != ham:
                TEST.write_bytes(metin)
            komut = [PY, "-X", "utf8", "-B", str(KOSUCU),
                     "--sinif", "H2c_EtiketCakismasi"]
            if not dpi:
                komut.append("--dpisiz")
            p = subprocess.run(komut, cwd=str(KOK), capture_output=True,
                               text=True, encoding="utf-8", errors="replace")
            kod = p.returncode
            (CIK / f"mutasyon_{ad.split()[0]}.txt").write_text(
                p.stdout + p.stderr, encoding="utf-8")
        finally:
            TEST.write_bytes(ham)
            if hashlib.sha256(TEST.read_bytes()).hexdigest() != ozet:
                raise SystemExit(f"GERI YAZILAMADI {TEST}")
        print(f"{ad}: beklenen={beklenen} gercek={kod}", flush=True)
        sonuc.append((ad, beklenen, kod))
    hepsi = all(b == k for _, b, k in sonuc)
    print("MUTASYON_SONUC", "GECTI" if hepsi else "DUSTU")
    return 0 if hepsi else 1


if __name__ == "__main__":
    raise SystemExit(main())
