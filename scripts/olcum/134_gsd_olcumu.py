"""GSD (yer ornekleme araligi) OLCUMU — tahmin degil, fotogrametrik.

🔴 NEDEN: sartnamedeki boyut esikleri PIKSELDE yaziliydi ve ayni yapi 960'ta
15 px, ham 3840'ta 60 px. Piksel esigi OLCEGE GORE ANLAM DEGISTIRIR;
santimetre degistirmez. Esikleri fiziksel birime cevirmek icin GSD gerekir.

Amele A, otomobil lastigi capindan ~5 cm/px @960 TAHMIN etmisti (FOV bilinmedigi
icin bagimsiz dogrulanamamisti). Bu betik onu OLCER.

YONTEM (yalniz elimizdeki veriyle, kamera parametresi GEREKTIRMEZ):
  ardisik kare cifti -> SRT'den GPS otelenmesi (metre)
                     -> faz korelasyonundan piksel kaymasi
                     -> GSD = metre / piksel
  ELEME: irtifa SABIT olmali (<0,5 m fark) · seyir irtifasi (>=25 m)
         otelenme 3-25 m · piksel kaymasi >=15 px · korelasyon guveni >=0,15
  Bu elemeler donus/irtifa degisimi olan ciftleri disarida birakir; kalanlarda
  hareket SAF OTELENMEDIR ve olcek dogrudan okunur.

⚠ SONUC MEDYANLA raporlanir: tek tek ciftler GPS gurultusune duyarlidir.
"""
from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

import cv2
import numpy as np

KOK = Path(__file__).resolve().parents[2]
KARE_KOK = KOK / "results" / "dji_20260822" / "kareler_1fps"
DJI = KOK / "dji"
CIKTI = KOK / "results" / "dji_20260822" / "gsd_olcumu.json"
M_DERECE = 111320.0


def srt_oku(p: Path) -> dict:
    tab = {}
    for b in p.read_text(encoding="utf-8", errors="replace").split("\n\n"):
        mf = re.search(r"FrameCnt:\s*(\d+)", b)
        la = re.search(r"latitude:\s*([\d.-]+)", b)
        lo = re.search(r"longitude:\s*([\d.-]+)", b)
        al = re.search(r"rel_alt:\s*([\d.-]+)", b)
        if mf and la and lo and al:
            tab[int(mf.group(1))] = (float(la.group(1)), float(lo.group(1)),
                                     float(al.group(1)))
    return tab


def medyan(v):
    v = sorted(v)
    n = len(v)
    return None if not n else (v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    man = json.loads((KARE_KOK / "manifest.json").read_text(encoding="utf-8"))
    pencere = cv2.createHanningWindow((960, 540), cv2.CV_32F)
    sonuc = []
    for srt_yolu in sorted(DJI.glob("DJI_2026*.SRT")):
        kaynak = srt_yolu.stem
        srt = srt_oku(srt_yolu)
        kareler = sorted((k for k in man["kareler"] if k["kaynak"].startswith(kaynak)),
                         key=lambda x: x["kare_no"])
        for a, b in zip(kareler, kareler[1:]):
            pa, pb = srt.get(a["kare_no"]), srt.get(b["kare_no"])
            if not pa or not pb:
                continue
            if abs(pa[2] - pb[2]) > 0.5 or pa[2] < 25.0:
                continue
            m_lat = (pb[0] - pa[0]) * M_DERECE
            m_lon = (pb[1] - pa[1]) * M_DERECE * math.cos(math.radians(pa[0]))
            mesafe = math.hypot(m_lat, m_lon)
            if not (3.0 < mesafe < 25.0):
                continue
            ia = cv2.imread(str(KARE_KOK / a["dosya"]), cv2.IMREAD_GRAYSCALE)
            ib = cv2.imread(str(KARE_KOK / b["dosya"]), cv2.IMREAD_GRAYSCALE)
            if ia is None or ib is None:
                continue
            ia = cv2.resize(ia, (960, 540)).astype(np.float32)
            ib = cv2.resize(ib, (960, 540)).astype(np.float32)
            (dx, dy), guven = cv2.phaseCorrelate(ia, ib, pencere)
            px = math.hypot(dx, dy)
            if px < 15.0 or guven < 0.15:
                continue
            sonuc.append({"kaynak": kaynak[-6:], "kare": a["kare_no"],
                          "metre": round(mesafe, 3), "piksel": round(px, 2),
                          "gsd_cm_px_960": round(100 * mesafe / px, 3),
                          "guven": round(guven, 3), "rel_alt": pa[2]})
    if not sonuc:
        print("🔴 GECERLI CIFT YOK — GSD OLCULEMEDI (hukum yok)")
        return 1
    g = [x["gsd_cm_px_960"] for x in sonuc]
    gs = sorted(g)
    med = medyan(g)
    ozet = {"n": len(g), "medyan": med, "p25": gs[len(gs) // 4],
            "p75": gs[3 * len(gs) // 4], "min": gs[0], "maks": gs[-1]}
    print(f"gecerli cift: {ozet['n']}")
    print(f"GSD @960 (cm/px): medyan {med:.2f} · p25 {ozet['p25']:.2f} · "
          f"p75 {ozet['p75']:.2f} · min {ozet['min']:.2f} · maks {ozet['maks']:.2f}")
    print(f"  ham 3840 : {med/4:.3f} cm/px")
    print(f"  model 512: {med*960/512:.2f} cm/px")
    print(f"  -> model girdisinde 3 px = {3*med*960/512:.1f} cm "
          f"(kod: MASKE_HATA_M = 25 cm)")
    CIKTI.write_text(json.dumps(
        {"_ne": "GSD olcumu — GPS otelenmesi / faz korelasyonu",
         "_yontem": "irtifa sabit <0,5 m · seyir >=25 m · otelenme 3-25 m · "
                    "piksel >=15 · guven >=0,15",
         "ozet_cm_px_960": ozet, "ornekler": sonuc[:60]},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"yazildi: {CIKTI}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
