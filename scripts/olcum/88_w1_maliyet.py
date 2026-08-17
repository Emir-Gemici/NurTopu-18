"""T94 / W1 · MALIYET: waypoint sayisi · rota uzunlugu · sure (model yolu).

NEDEN (REVIEW_LOG D-157 madde 4.1). W1'in kararlilik ve K5 kazanci olculdu ama
BEDELI olculmedi. V1 icin bunlar "AYNI" cikmisti; W1 FARKLI bir kuraldir ve
varsayimla gecilemez. Sartname sureye bakar; mesaj boyutu ve IKA planlamasi
waypoint sayisina bakar.

Ayni kareler, ayni model, TEK fark W1 kuralinin acik/kapali olmasi.
On kayit: `calisma/olcum/w1_on_kayit.md` (olcum kosulmadan once yazildi).
"""
import argparse
import json
import sys
import time
from importlib import import_module
from pathlib import Path

import cv2
import numpy as np

from ayarlar import REPO, uretim_pt

BURASI = Path(__file__).parent
sys.path.insert(0, str(REPO / "codes"))
sys.path.insert(0, str(BURASI))

from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp,   # noqa: E402
                           _preprocess, get_masks)
import rpi_inference as RI                                        # noqa: E402

yumusak = import_module("87_t94_yumusak_kiris")

KUME = BURASI / "calisma" / "sentetik_arena_kadraj_t66"
CONF = 0.30


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", type=Path, default=uretim_pt())
    ap.add_argument("--kume", type=Path, default=KUME)
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    man = json.loads((args.kume / "manifest.json").read_text(encoding="utf-8"))
    from ultralytics import YOLO
    model = YOLO(str(args.model), task="segment")

    kareler = []
    for o in man["ornekler"]:
        if o.get("durum") != "YAZILDI" or not o.get("arena"):
            continue
        p = args.kume / o["cikti"]
        mpp = o["arena"].get("mpp")
        if not p.is_file() or not mpp:
            continue
        img = cv2.imread(str(p))
        if img is None:
            continue
        kareler.append((p.name, img, mpp))
    print(f"olculecek kare: {len(kareler)}", flush=True)

    # Cikarimi BIR KEZ yap, maskeleri iki kosumda da KULLAN (D-139 dersi:
    # iki ayri cikarim yapilirsa fark kuraldan mi cekilisten mi gelir belli olmaz).
    onbellek = []
    for kare, img, mpp in kareler:
        sq, small, icerik = _preprocess(img)
        r = model.predict(small, imgsz=INFER_SIZE, conf=CONF, verbose=False)
        mk = _maskeleri_icerige_kirp(get_masks(r, *sq.shape[:2]), icerik)
        onbellek.append((kare, mk, icerik, mpp))

    sonuc = {}
    for ad, kural in (("TABAN (W1 kapali)", None), ("W1 acik", "W1")):
        if kural:
            yumusak.ac([b for b in yumusak.BICIMLER if b.startswith(kural)][0])
        satir = []
        try:
            for kare, mk, icerik, mpp in onbellek:
                t0 = time.perf_counter()
                yol, guven, wps, _t, red, ol = RI.analyze_path(
                    mk[0], icerik=icerik, engel_mask=mk[1], mpp=mpp,
                    return_clean=True, return_reason=True, return_olcum=True)
                sure = (time.perf_counter() - t0) * 1000.0
                if red is not None or not wps:
                    satir.append({"kare": kare, "rota": False, "sure_ms": sure})
                    continue
                p_ = np.asarray(wps, dtype=float)
                uz = float(np.sum(np.hypot(*(p_[1:] - p_[:-1]).T)))
                satir.append({"kare": kare, "rota": True, "wp": len(wps),
                              "uzunluk": uz, "sure_ms": sure,
                              "darbogaz": float((ol or {}).get("darbogaz_px") or 0.0)})
        finally:
            if kural:
                yumusak.kapat()
        sonuc[ad] = satir

    c = "=" * 78
    print(f"\n{c}\nT94 / W1 · MALIYET (model {args.model.name})\n"
          f"  kume {args.kume.name} · kare {len(kareler)}\n{c}")
    print(f"{'kosum':<22}{'rota':>7}{'wp med':>9}{'wp maks':>9}"
          f"{'uzunluk med':>13}{'sure med ms':>13}")
    ozet = {}
    taban = None
    for ad in sonuc:
        r = [k for k in sonuc[ad] if k["rota"]]
        if not r:
            continue
        g = lambda a: np.array([k[a] for k in r], dtype=float)
        wp, uz, sr = g("wp"), g("uzunluk"), g("sure_ms")
        ozet[ad] = {"rota": len(r), "wp_med": float(np.median(wp)),
                    "wp_maks": float(wp.max()),
                    "uzunluk_med": float(np.median(uz)),
                    "sure_med": float(np.median(sr))}
        print(f"{ad:<22}{len(r):>7}{np.median(wp):>9.0f}{wp.max():>9.0f}"
              f"{np.median(uz):>13.1f}{np.median(sr):>13.1f}")
        if taban is None:
            taban = ozet[ad]
    if len(ozet) == 2:
        a, b = list(ozet.values())
        print(f"\n  UZUNLUK ARTISI : %{100*(b['uzunluk_med']/max(1e-9,a['uzunluk_med'])-1):+.2f}"
              f"   (esik: <= %5)")
        print(f"  SURE ARTISI    : {b['sure_med']/max(1e-9,a['sure_med']):.2f} kat"
              f"   (esik: <= 2 kat)")
        print(f"  WAYPOINT medyan: {a['wp_med']:.0f} -> {b['wp_med']:.0f}"
              f"   (esik: <= 16)")
    print(c)

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps({"ozet": ozet, "kayitlar": sonuc},
                                        ensure_ascii=False, indent=1),
                             encoding="utf-8")
        print(f"json -> {args.json}")


if __name__ == "__main__":
    main()
