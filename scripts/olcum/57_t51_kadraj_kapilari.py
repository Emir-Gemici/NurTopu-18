"""T51 KAPILARI 1-3 ve 5 — kadraj kipi karar yoluyla uyumlu mu?

KAPI 1  TAM KAREDE (kirpmasiz) rota orani >= 12/24
KAPI 2  yer gercegi serit ile sistemin verdigi serit: uyumsuzluk sayisi
KAPI 3  POZITIF KONTROL: acik serit KAPATILINCA karar ACIK KALMAMALI
KAPI 5  T48 kaplama tavani bu kumede yanlis ateslıyor mu (D-62 yan bulgusu)

Olcum YER GERCEGI etiketleriyle yapilir (model YOK) — bu gorev uretecin
GEOMETRISINI sinar, modelin arenadaki basarimini DEGIL.
"""
import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

from ayarlar import REPO

sys.path.insert(0, str(REPO / "codes"))
from karar_sozlesmesi import (ZEMIN_KAPLAMA_TAVANI,  # noqa: E402
                              ZEMIN_MASKESI_SUPHELI_SEBEBI, serit_no,
                              zemin_kaplamasi)
from rpi_inference import _rota_kararini_esikle, analyze_path  # noqa: E402

KUME = Path(__file__).parent / "calisma" / "sentetik_arena_kadraj"


def maskeler(p, lbl):
    """Etiket poligonlarindan zemin/engel maskesi (YER GERCEGI)."""
    im = cv2.imread(str(p))
    h, w = im.shape[:2]
    z = np.zeros((h, w), np.uint8)
    e = np.zeros((h, w), np.uint8)
    t = lbl / f"{p.stem}.txt"
    if t.exists():
        for s in t.read_text().splitlines():
            pr = s.split()
            if len(pr) < 7:
                continue
            k = np.array([float(x) for x in pr[1:]], np.float32).reshape(-1, 2)
            k[:, 0] *= w
            k[:, 1] *= h
            cv2.fillPoly(z if pr[0] == "0" else e, [k.astype(np.int32)], 1)
    return im, z, e


def gercek_serit(z, e, w, h):
    """Yer gercegi: alt VE ust bantla temas eden zemin bileseninin seridi.

    Karar yolundan BAGIMSIZ turetilir — `analyze_path` cagrilmaz.
    """
    serbest = z.copy()
    serbest[e > 0] = 0
    n, lab, st, _ = cv2.connectedComponentsWithStats(serbest, 8)
    bant = max(1, int(h * 0.08))
    adaylar = []
    for i in range(1, n):
        bil = (lab == i)
        if not (bil[:bant, :].any() and bil[h - bant:, :].any()):
            continue
        xs = np.nonzero(bil)[1]
        adaylar.append((int(bil.sum()), serit_no(float(xs.mean()), 0, w)))
    if not adaylar:
        return None
    return max(adaylar)[1]


def kos(n_kare):
    dosyalar = []
    for bol in ("val", "train"):
        d = KUME / "images" / bol
        if d.is_dir():
            dosyalar += [(p, KUME / "labels" / bol) for p in sorted(d.iterdir())]
    dosyalar = dosyalar[:n_kare]

    karar = uyumsuz = cekimser = 0
    kaplama_reddi = 0
    sebepler = {}
    poz_kontrol_ok = poz_kontrol_n = 0
    kaplamalar = []
    print(f"{'kare':<16}{'GT serit':>9}{'sistem':>8}{'guven':>8}{'kaplama':>9}"
          f"  sebep")
    for p, lbl in dosyalar:
        im, z, e = maskeler(p, lbl)
        h, w = im.shape[:2]
        icerik = (0, 0, w, h)
        kap = zemin_kaplamasi(z, icerik)
        kaplamalar.append(kap)
        gt = gercek_serit(z, e, w, h)
        y, g, wp, r = analyze_path(z, icerik=icerik, engel_mask=e,
                                   return_reason=True)
        y, g, wp, r = _rota_kararini_esikle(y, g, wp, r)
        sebep = r[0] if r else None
        if sebep:
            sebepler[sebep] = sebepler.get(sebep, 0) + 1
            if sebep == ZEMIN_MASKESI_SUPHELI_SEBEBI:
                kaplama_reddi += 1
        if y is None:
            cekimser += 1
        else:
            karar += 1
            if gt is not None and y != gt:
                uyumsuz += 1
        print(f"{p.stem:<16}{str(gt):>9}{str(y):>8}{g:>8.3f}{100*kap:>8.1f}%"
              f"  {sebep or '-'}")

        # KAPI 3 — POZITIF KONTROL: sistemin actigi seridi KAPAT
        if y is not None:
            z2 = z.copy()
            e2 = e.copy()
            lo = int((y - 1) * w / 3.0)
            hi = int(y * w / 3.0)
            orta = (lo + hi) // 2
            kal = max(6, h // 40)
            e2[h // 2 - kal:h // 2 + kal, lo:hi] = 1
            z2[h // 2 - kal:h // 2 + kal, lo:hi] = 0
            del orta
            y2, g2, wp2, r2 = analyze_path(z2, icerik=icerik, engel_mask=e2,
                                           return_reason=True)
            y2, g2, wp2, r2 = _rota_kararini_esikle(y2, g2, wp2, r2)
            poz_kontrol_n += 1
            if y2 != y:
                poz_kontrol_ok += 1

    n = len(dosyalar)
    print()
    print("=" * 78)
    print(f"KAPI 1  TAM KAREDE rota: {karar}/{n}   "
          f"{'GECTI' if karar >= 12 * n / 24 else 'DUSTU'} (esik >= {12*n/24:.0f})")
    print(f"KAPI 2  GT serit ile UYUMSUZLUK: {uyumsuz}/{karar}")
    print(f"KAPI 3  POZITIF KONTROL: acik serit kapatilinca karar DEGISTI "
          f"{poz_kontrol_ok}/{poz_kontrol_n}   "
          f"{'GECTI' if poz_kontrol_n and poz_kontrol_ok == poz_kontrol_n else 'DUSTU'}")
    print(f"KAPI 5  T48 kaplama: ort %{100*np.mean(kaplamalar):.1f} · "
          f"maks %{100*max(kaplamalar):.1f} · tavan %{100*ZEMIN_KAPLAMA_TAVANI:.0f} · "
          f"tavan reddi {kaplama_reddi}/{n}")
    print(f"        cekimser {cekimser}/{n} · ret sebepleri: {sebepler}")
    print("=" * 78)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=24)
    kos(ap.parse_args().n)
