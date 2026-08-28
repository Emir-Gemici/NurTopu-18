"""157 — ARENA ZEMIN DOKUSU (ciplak sikistirilmis toprak) · T199 · D-341.

NEDEN VAR. Doku bankasinin `zemin/` sinifi RescueNet KASIRGA goruntulerinde
"hicbir poligonun ortmedigi" artik alanlardan cikariliyor: asfalt yollar,
catilar, mavi brandalar, dagink moloz. Sartname arenasinin zemini ise TEK
DUZE, ince taneli, acik kahve SIKISTIRILMIS TOPRAKTIR. Bankada bu aile HIC
YOK ve olculdu (D-341): model saf toprak yamasinda %0,0 zemin diyor.

YORDAMSAL uretiliyor, indirilmiyor:
  · lisans sorunu birakmaz,
  · ve daha onemlisi ISTATISTIGI BIZ KONTROL EDERIZ — figurden OLCTUGUMUZ
    hedefe gore ayarlanir, tahminle degil.

OLCULEN HEDEF — IKI KEZ OLCULDU, ILKI YANLISTI:
  ⚠ ILK olcumumu ELLE SECTIGIM yamalardan aldim ve o yamalar MOLOZ ICERIYORDU;
    cikan hedef (parlaklik 101-137, lap 34,7-50,9, b* 134,5) zemini degil
    zemin+moloz karisimini tarif ediyordu. Uretilen doku GRI cikti, oysa arena
    zemini SICAK KAHVE. Hata gorselle yakalandi (D-80: gorsel kazanir).
  ✅ IKINCI olcum kroma maskesiyle SAF zemin ayiklanarak yapildi
    (b* > 133 ∧ 126 < a* < 136 ∧ 90 < L < 190 -> figurun %58,9'u), sonra
    yalniz >%97 saf olan 39 adet 100x100 kutu uzerinden:
        gri parlaklik   ort 147,9   (%10: 144 · %90: 152)
        doku lap std    ort  21,8   (%10: 15,7 · %90: 38,2)
        LAB             L 152,8 · a 129,3 (±1,4) · b 138,7 (±2,2)
    Bankaninki lap 66-107 idi — arena zemini ondan UC KAT yumusaktir.

⚠ Bu doku MEVCUT BANKAYI DEGISTIRMEZ; yanina EKLENIR (ON_KAYIT D-340 §2:
"mevcut cesitlilik KALDIRILMAZ").

Kullanim:
  <venv> 157_arena_zemin_dokusu.py --adet 300 --cikti <banka>/zemin_arena
  <venv> 157_arena_zemin_dokusu.py --denetle          # istatistigi olc, yazma
"""
from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np

KOK = Path(__file__).resolve().parents[2]

# D-341'de OLCULEN hedef bantlar — burada TEK YERDE durur.
HEDEF_PARLAKLIK = (140.0, 158.0)
HEDEF_DOKU = (14.0, 40.0)          # Laplacian std (saf zemin olcumu)
BOYUT = 256


def _gurultu(rng, n, olcek):
    """Dusuk frekansli gurultu: kucuk uretip buyut (yumusak lekelenme)."""
    k = max(2, int(n / olcek))
    ham = rng.random((k, k)).astype(np.float32)
    return cv2.resize(ham, (n, n), interpolation=cv2.INTER_CUBIC)


def uret(rng, n: int = BOYUT) -> np.ndarray:
    """Bir ciplak sikistirilmis toprak yamasi (BGR uint8)."""
    # 1) TEK DUZE taban ton: acik kahve. Sahneden sahneye hafif kayar.
    taban_l = rng.uniform(138.0, 168.0)      # LAB L; olculen ort 152,8
    sicak = rng.uniform(0.9, 1.35)              # b* yonu (sari-kahve)

    # 2) Genis olcekli sikismalar / tekerlek izleri — YUMUSAK, dusuk genlik.
    genis = _gurultu(rng, n, rng.uniform(6.0, 14.0)) - 0.5
    orta = _gurultu(rng, n, rng.uniform(2.5, 5.0)) - 0.5
    taban = (taban_l
             + genis * rng.uniform(14.0, 26.0)
             + orta * rng.uniform(5.0, 11.0))

    # 3) Seyrek kucuk cakil — DUSUK kontrast (arena zemini temizdir).
    #    ⚠ TANEDEN ONCE cizilir: yoksa kalibrasyondan SONRA doku eklenir ve
    #    olculen istatistik hedefi asar.
    for _ in range(rng.randint(6, 26)):
        cx, cy = rng.randrange(n), rng.randrange(n)
        r = rng.randint(1, 4)
        cv2.circle(taban, (cx, cy), r,
                   float(taban.mean() + rng.uniform(-22.0, 26.0)), -1, cv2.LINE_AA)

    # 4) INCE TANE — genlik TAHMINLE DEGIL, KAPALI FORMLA cozulur.
    # 🔴 Iki basarisiz deneme kayda gecsin: sigma 0,6-1,1 + genlik 3,0-6,5 ->
    # Laplacian std 2,5 (hedef 28-55: cok yumusak); sigma 0,35-0,55 + genlik
    # 30-52 -> 115,2 (cok sert). Ucuncu kez TAHMIN etmek yerine sunu kullandik:
    # Laplacian DOGRUSAL bir islectir ve tane tabandan bagimsizdir, dolayisiyla
    #     std(lap(taban + a·tane))^2 ≈ std(lap(taban))^2 + a^2 · std(lap(tane))^2
    # Hedefe goturen `a` buradan DOGRUDAN cozulur. Boylece dokunun istatistigi
    # D-341'de OLCULEN banda KURGU GEREGI oturur — "deneyip tutturmak" degil.
    tane = rng.normal(0.0, 1.0, (n, n)).astype(np.float32)
    tane = cv2.GaussianBlur(tane, (0, 0), rng.uniform(0.35, 0.55))
    s_taban = float(cv2.Laplacian(taban, cv2.CV_32F).std())
    s_tane = float(cv2.Laplacian(tane, cv2.CV_32F).std())
    hedef = rng.uniform(*HEDEF_DOKU)
    a_kat = ((max(0.0, hedef ** 2 - s_taban ** 2) ** 0.5 / s_tane)
             if s_tane > 1e-6 else 0.0)
    l = np.clip(taban + tane * a_kat, 0, 255)   # SON BULANIKLASTIRMA YOK

    # 5) LAB -> BGR. a/b figurden OLCULEN degerlere yakin tutulur.
    lab = np.zeros((n, n, 3), np.float32)
    lab[:, :, 0] = l
    # a*/b* OLCULEN degerlere oturtulur: a 129,3 (±1,4) · b 138,7 (±2,2).
    # 🔴 Ilk surumde b* ~133,5 idi ve uretilen doku GRI cikiyordu; arena
    # zemininin SICAKLIGI buradan gelir, atlanirsa renk tutmaz.
    lab[:, :, 1] = 129.3 + rng.uniform(-1.4, 1.4) + (l - l.mean()) * 0.010
    lab[:, :, 2] = 138.7 + rng.uniform(-2.2, 2.2) * sicak + (l - l.mean()) * 0.030
    return cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR)


def imza(im) -> tuple[float, float]:
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(np.float32)
    return float(g.mean()), float(cv2.Laplacian(g, cv2.CV_32F).std())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--adet", type=int, default=300)
    ap.add_argument("--tohum", type=int, default=7)
    ap.add_argument("--cikti", type=Path, default=None)
    ap.add_argument("--denetle", action="store_true",
                    help="yalniz istatistigi olc, DOSYA YAZMA")
    a = ap.parse_args()

    rng = np.random.default_rng(a.tohum)
    class _R:                                  # okunur kisa sarmalayici
        random = staticmethod(lambda *s: rng.random(*s))
        uniform = staticmethod(lambda lo, hi: float(rng.uniform(lo, hi)))
        normal = staticmethod(lambda m, s, sh: rng.normal(m, s, sh))
        randint = staticmethod(lambda lo, hi: int(rng.integers(lo, hi)))
        randrange = staticmethod(lambda n: int(rng.integers(0, n)))
    r = _R()

    par, dok, yazildi = [], [], 0
    if a.cikti and not a.denetle:
        a.cikti.mkdir(parents=True, exist_ok=True)
    for i in range(a.adet):
        im = uret(r)
        p, d = imza(im)
        par.append(p); dok.append(d)
        if a.cikti and not a.denetle:
            cv2.imwrite(str(a.cikti / f"arena_zemin_{i:04d}.png"), im)
            yazildi += 1

    par, dok = np.array(par), np.array(dok)
    print(f"uretilen: {len(par)}")
    print(f"  parlaklik  ort {par.mean():6.1f}  bant [{par.min():.1f}, {par.max():.1f}]"
          f"  · hedef {HEDEF_PARLAKLIK}")
    print(f"  doku(lap)  ort {dok.mean():6.1f}  bant [{dok.min():.1f}, {dok.max():.1f}]"
          f"  · hedef {HEDEF_DOKU}")
    p_ok = HEDEF_PARLAKLIK[0] <= par.mean() <= HEDEF_PARLAKLIK[1]
    d_ok = HEDEF_DOKU[0] <= dok.mean() <= HEDEF_DOKU[1]
    icinde = float(((dok >= HEDEF_DOKU[0]) & (dok <= HEDEF_DOKU[1])).mean())
    print(f"  doku bandinda kalan yama: %{100*icinde:.1f}")
    print(f"\n  PARLAKLIK {'UYDU' if p_ok else 'UYMADI'} · DOKU {'UYDU' if d_ok else 'UYMADI'}")
    if yazildi:
        print(f"  yazildi -> {a.cikti} ({yazildi} dosya)")
    return 0 if (p_ok and d_ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
